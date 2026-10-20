"""E2 step 2 (solver env, numba): choose the threshold-multiplier table on a TRAINING-WINDOW pack (e2_pack.py).

Spin encoding: x[b, v] in {0, 1}, one-hot per load bucket b (K = 6) over the grid G = (0.25, 0.35, 0.5, 0.7, 1, 1.4, 2,
2.8, 4); table m_b = G[v(b)]. Hamiltonian (pre-registered in PROGRESS.md, E2 section):
  H(x) = peak_day1(m) + 0.1 * top5_day1(m)                      replayed day-1 load (util %), higher-order spin term
       + LAM * sum_b |log2 m_b|                                  local fields h[b, v] = LAM * |log2 G[v]|
       + PMONO * sum_b sum_{v < v'} x[b, v] x[b+1, v']           couplings: penalise m increasing with load
The write budget is a HARD repair: for every spin state the base theta is set exactly so that the day-1 written chunks
are <= W1 (largest admitted set by episode maxima of score / m), so every evaluated state is budget-feasible.
One-hot is kept by one-hot-preserving moves (a bucket's 1 moves to another grid value), standard for Potts-encoded
Ising samplers.

Solvers (same energy function, same evaluation kernel):
  pt   Ising-family: parallel tempering (replica exchange, the q2 PT ladder scheme: geometric temperatures,
       neighbour swaps with Metropolis acceptance), 16 replicas, 10 s wall budget, seed = retrain k
  cd   classical: greedy coordinate descent (exact best value per bucket, random bucket order) + perturbation
       restarts from the incumbent, 10 s wall budget, seed = retrain k
  ex   classical exact reference: exhaustive enumeration of all C(14, 6) = 3003 monotone (non-increasing) tables

  source env.sh && PY=$SOLVER_PY src/sbx.sh src/e2_solve.py --mode dev --solvers pt cd ex
-> tables/<mode>/<solver>_<inst>_<arm>_r<k>.json (the simulator's --ap-load-adapt-table format) and the ledger
   results/solves_<mode>.csv (one row per solve).
"""
import argparse
import csv
import fcntl
import itertools
import json
import math
import os
import time

import numba as nb
import numpy as np

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID = np.array([0.25, 0.35, 0.5, 0.7, 1.0, 1.4, 2.0, 2.8, 4.0])
K = 6
LAM = 0.02          # util-pts per octave away from 1 (prior towards the neutral table)
PMONO = 50.0        # per increasing adjacent pair (practically hard)
TOP5W = 0.1
BUDGET_S = 10.0
DEV = [f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]


# ------------------------------------------------------------------ kernels
@nb.njit(cache=True)
def replay(score, bucket, mult, admissible, starts, acc_w, stc, st_full, nch, C0, W1, US):
    n_ep = starts.shape[0] - 1
    n = score.shape[0]
    r = np.empty(n)
    for i in range(n):
        r[i] = score[i] / mult[bucket[i]] if admissible[i] else -1e300
    M = np.empty(n_ep)
    for e in range(n_ep):
        m = -1e300
        for i in range(starts[e], starts[e + 1]):
            if r[i] > m:
                m = r[i]
        M[e] = m
    order = np.argsort(-M, kind="mergesort")
    cs = 0.0
    j = 0
    while j < n_ep and cs + nch[order[j]] <= W1:
        cs += nch[order[j]]
        j += 1
    theta = M[order[j]] if j < n_ep else -1e299
    L = C0.copy()
    mw = C0.shape[0]
    wch = 0.0
    for e in range(n_ep):
        if M[e] <= theta:
            continue
        wch += nch[e]
        k = starts[e]
        while k < starts[e + 1] and r[k] <= theta:
            k += 1
        w = acc_w[k]
        if w < mw:
            L[w] -= stc[k] - st_full[e]
        for q in range(k + 1, starts[e + 1]):
            w = acc_w[q]
            if w < mw:
                L[w] -= stc[q]
    Lu = L * US
    s = np.sort(Lu)[::-1]
    return s[0], (s[0] + s[1] + s[2] + s[3] + s[4]) / 5.0, theta, wch


@nb.njit(cache=True)
def penalty(v, lam, pmono, logg):
    f = 0.0
    for b in range(v.shape[0]):
        f += lam * abs(logg[v[b]])
    viol = 0
    for b in range(v.shape[0] - 1):
        if v[b + 1] > v[b]:
            viol += 1
    return f, viol, f + pmono * viol


class Problem:
    def __init__(self, pack_path):
        z = np.load(pack_path)
        self.z = z
        self.args = (z["score"].astype(np.float64), z["bucket"].astype(np.int64), None, z["admissible"].astype(np.bool_),
                     z["starts"].astype(np.int64), z["acc_w"].astype(np.int64), z["stc"].astype(np.float64),
                     z["st_full"].astype(np.float64), z["nch"].astype(np.float64), z["C0"].astype(np.float64),
                     float(z["W1"]), float(z["US"]))
        self.edges = z["edges"].tolist()
        self.logg = np.log2(GRID)
        self.n_eval = 0
        self.cache = {}

    def parts(self, v):
        key = tuple(int(x) for x in v)
        if key in self.cache:
            return self.cache[key]
        a = list(self.args)
        a[2] = GRID[np.asarray(v, np.int64)]
        pk, t5, th, wch = replay(*a)
        f, viol, pen = penalty(np.asarray(v, np.int64), LAM, PMONO, self.logg)
        self.n_eval += 1
        out = dict(E=pk + TOP5W * t5 + pen, peak=pk, top5=t5, field=f, viol=viol, theta=th, wch=wch)
        self.cache[key] = out
        return out

    def E(self, v):
        return self.parts(v)["E"]


# ------------------------------------------------------------------ solvers
def solve_pt(P, seed, budget=BUDGET_S, R=16, Tmin=0.005, Tmax=1.0):
    rng = np.random.default_rng(seed)
    t0 = time.time()
    temps = np.geomspace(Tmin, Tmax, R)
    X = np.full((R, K), 4, np.int64)                  # all replicas start at the neutral table (m = 1)
    En = np.array([P.E(x) for x in X])
    best_v, best_E = X[0].copy(), En[0]
    sweeps = swaps = acc = prop = 0
    order = np.arange(R)                              # order[slot] = replica at temperature slot
    while time.time() - t0 < budget:
        for slot in range(R):
            rr = order[slot]
            T = temps[slot]
            for _ in range(K):
                b = rng.integers(K)
                nv = rng.integers(len(GRID) - 1)
                nv = nv + 1 if nv >= X[rr, b] else nv
                y = X[rr].copy()
                y[b] = nv
                Ey = P.E(y)
                prop += 1
                if Ey <= En[rr] or rng.random() < math.exp(-(Ey - En[rr]) / T):
                    X[rr], En[rr] = y, Ey
                    acc += 1
                    if Ey < best_E:
                        best_v, best_E = y.copy(), Ey
        for a in range(sweeps % 2, R - 1, 2):
            ra, rb = order[a], order[a + 1]
            d = (1.0 / temps[a] - 1.0 / temps[a + 1]) * (En[ra] - En[rb])
            if d >= 0 or rng.random() < math.exp(d):
                order[a], order[a + 1] = rb, ra
                swaps += 1
        sweeps += 1
    return best_v, dict(sweeps=sweeps, swaps=swaps, acc=acc, prop=prop, wall=time.time() - t0)


def solve_cd(P, seed, budget=BUDGET_S):
    rng = np.random.default_rng(seed)
    t0 = time.time()
    x = np.full(K, 4, np.int64)
    Ex = P.E(x)
    best_v, best_E = x.copy(), Ex
    restarts = passes = 0
    while time.time() - t0 < budget:
        improved = True
        while improved and time.time() - t0 < budget:
            improved = False
            passes += 1
            for b in rng.permutation(K):
                cand = []
                for v in range(len(GRID)):
                    y = x.copy()
                    y[b] = v
                    cand.append((P.E(y), v))
                e_, v_ = min(cand)
                if e_ < Ex - 1e-12:
                    x[b], Ex, improved = v_, e_, True
        if Ex < best_E:
            best_v, best_E = x.copy(), Ex
        restarts += 1                                    # perturb the incumbent: 2 random buckets, random values
        x = best_v.copy()
        for b in rng.choice(K, 2, replace=False):
            x[b] = rng.integers(len(GRID))
        Ex = P.E(x)
    return best_v, dict(passes=passes, restarts=restarts, wall=time.time() - t0)


def monotone_tables():
    for c in itertools.combinations_with_replacement(range(len(GRID)), K):
        yield np.array(sorted(c, reverse=True), np.int64)          # non-increasing in load


def solve_ex(P, seed=0):
    t0 = time.time()
    best_v, best_E, n = None, np.inf, 0
    for v in monotone_tables():
        e = P.E(v)
        n += 1
        if e < best_E:
            best_v, best_E = v, e
    return best_v, dict(n_tables=n, wall=time.time() - t0)


# ------------------------------------------------------------------ ledger
def append(path, row):
    with open(path + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        new = not os.path.exists(path)
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if new:
                w.writeheader()
            w.writerow(row)
        fcntl.flock(lk, fcntl.LOCK_UN)


def powerlaw_proj(edges, alpha=-1.0, ref=20.0):
    """grid index closest (log scale) to the power law at each bucket's midpoint (diagnostic reference only)."""
    e = [max(edges[0] / 2, 1e-6)] + [0.5 * (a + b) for a, b in zip(edges, edges[1:])] + [edges[-1] * 1.1]
    g = np.clip((np.array(e) / ref) ** alpha, 0.25, 4)
    return np.array([int(np.argmin(np.abs(np.log2(GRID) - np.log2(x)))) for x in g], np.int64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dev", "test", "dryrun"], default="dev")
    ap.add_argument("--solvers", nargs="+", default=["pt", "cd", "ex"])
    ap.add_argument("--keys", nargs="*", help="pack names <inst>_<arm>_r<k> (default: all packs of the mode)")
    o = ap.parse_args()
    pdir = os.path.join(W, "work", "packs", o.mode)
    keys = o.keys or sorted(f[:-4] for f in os.listdir(pdir) if f.endswith(".npz"))
    ledger = os.path.join(W, "results", f"solves_{o.mode}.csv")
    done = set()
    if os.path.exists(ledger):
        with open(ledger) as f:
            done = {r["solve_key"] for r in csv.DictReader(f)}
    for key in keys:
        inst, arm, rk = key.rsplit("_", 2)
        if o.mode == "dev":
            assert inst in DEV, inst
        seed = int(rk[1:])
        P = Problem(os.path.join(pdir, key + ".npz"))
        ref = {"ones": np.full(K, 4, np.int64), "powerlaw": powerlaw_proj(P.edges)}
        refE = {n: P.parts(v) for n, v in ref.items()}
        assert abs(refE["ones"]["peak"] - float(P.z["plain_peak"])) < 1e-9, (key, refE["ones"]["peak"], float(P.z["plain_peak"]))
        for s in o.solvers:
            skey = f"{s}_{key}"
            if skey in done:
                continue
            n0 = P.n_eval
            P.cache = {}                                   # no cross-solver memo: every solver pays its own evaluations
            v, info = {"pt": solve_pt, "cd": solve_cd, "ex": solve_ex}[s](P, seed)
            pr = P.parts(v)
            mult = GRID[v].tolist()
            tdir = os.path.join(W, "tables", o.mode)
            os.makedirs(tdir, exist_ok=True)
            json.dump(dict(name=f"{s}_{key}", window_min=10, edges=P.edges, mult=mult,
                           fit=dict(solver=s, E=pr["E"], peak_day1=pr["peak"], top5_day1=pr["top5"], viol=pr["viol"],
                                    W1=float(P.z["W1"]), theta_fit=pr["theta"], grid=GRID.tolist(), lam=LAM,
                                    pmono=PMONO, top5w=TOP5W)),
                      open(os.path.join(tdir, f"{s}_{key}.json"), "w"), indent=1)
            row = dict(solve_key=skey, mode=o.mode, inst=inst, arm=arm, rep=seed, solver=s,
                       budget_s=BUDGET_S if s != "ex" else "", E=pr["E"], peak=pr["peak"], top5=pr["top5"],
                       field=pr["field"], viol=pr["viol"], mult=json.dumps(mult), edges=json.dumps([round(e, 4) for e in P.edges]),
                       n_evals=P.n_eval - n0, wall_s=info["wall"], info=json.dumps({k: v_ for k, v_ in info.items() if k != "wall"}),
                       E_ones=refE["ones"]["E"], peak_ones=refE["ones"]["peak"], E_powerlaw=refE["powerlaw"]["E"],
                       peak_powerlaw=refE["powerlaw"]["peak"], ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
            append(ledger, row)
            print(f"{skey}: E={pr['E']:.4f} peak={pr['peak']:.3f} (ones {refE['ones']['peak']:.3f}, powerlaw "
                  f"{refE['powerlaw']['peak']:.3f}) mult={mult} evals={row['n_evals']} {info}", flush=True)


if __name__ == "__main__":
    main()
