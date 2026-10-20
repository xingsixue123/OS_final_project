"""AR step 2 (solver env, numba): fit the load x access-class threshold-multiplier table on a TRAINING-WINDOW pack
(cls_pack.py). Copied from wp10_schedule/src/e2_solve.py (same replay kernel, hard budget repair, PT and CD solvers);
AR changes: J access classes x K load buckets (cells c = j*K + b), a Potts coupling between the classes of one
load bucket, and no exhaustive reference (9^12 states; C(14,6)^2 ~ 9e6 monotone tables).

Spin encoding: x[c, v] in {0, 1}, one-hot per cell c over the grid G = (0.25, 0.35, 0.5, 0.7, 1, 1.4, 2, 2.8, 4);
m_c = G[v(c)]. Hamiltonian:
  H(x) = peak_day1(m) + 0.1 * top5_day1(m)                       replayed day-1 load (util %), higher-order spin term
       + LAM * sum_c |log2 m_c|                                   local fields (prior towards the neutral table)
       + MU * sum_b sum_{j>0} |log2 m_{j,b} - log2 m_{0,b}|       Potts couplings: class j follows class 0 unless the
                                                                  day-1 replay pays for the difference
       + PMONO * sum_j sum_b [m_{j,b+1} > m_{j,b}]                couplings: non-increasing in load within a class
Write budget: HARD repair (theta set so the day-1 written chunks are <= W1), as WP10.

'm' variants (ptm / cdm, AR 01:12, before any screen result): + PMONO * sum_b [m_{j,b} > m_{0,b}] for j >= 1, i.e. the
big-offset class is never less admissive than the small class at the same load (WP3/WP9: not admitting scans is the
catastrophic failure mode).

Solvers (same energy, same kernel, same wall budget):
  pt   Ising family: parallel tempering, 16 replicas, geometric T in [0.005, 1] util-pts, one-hot-preserving single-cell
       moves, neighbour replica swaps; seed = retrain k
  cd   classical: greedy coordinate descent over cells (exact best value per cell) + perturbation restarts; seed = k

  source env.sh && PY=$SOLVER_PY src/sbx.sh src/cls_fit.py --mode dev --keys <inst>_<arm>_r<k> ...
-> tables/<mode>/<solver>_<inst>_<arm>_r<k>.json (overlay v4 class-table JSON) + ledger results/solves_<mode>.csv
"""
import argparse
import csv
import fcntl
import json
import math
import os
import time

import numba as nb
import numpy as np

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRID = np.array([0.25, 0.35, 0.5, 0.7, 1.0, 1.4, 2.0, 2.8, 4.0])
NEUTRAL = 4
K = 6
LAM = 0.02
MU = 0.02
PMONO = 50.0
TOP5W = 0.1
BUDGET_S = 20.0


@nb.njit(cache=True)
def replay(score, cell, mult, admissible, starts, acc_w, stc, st_full, nch, C0, W1, US):
    n_ep = starts.shape[0] - 1
    n = score.shape[0]
    r = np.empty(n)
    for i in range(n):
        r[i] = score[i] / mult[cell[i]] if admissible[i] else -1e300
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
def penalty(v, J, K, lam, mu, pmono, logg, cmono):
    f = 0.0
    for c in range(J * K):
        f += lam * abs(logg[v[c]])
    for j in range(1, J):
        for b in range(K):
            f += mu * abs(logg[v[j * K + b]] - logg[v[b]])
    viol = 0
    for j in range(J):
        for b in range(K - 1):
            if v[j * K + b + 1] > v[j * K + b]:
                viol += 1
    if cmono:                                  # AR 'm' solvers: class j >= 1 never less admissive than class 0
        for j in range(1, J):
            for b in range(K):
                if v[j * K + b] > v[b]:
                    viol += 1
    return f, viol, f + pmono * viol


class Problem:
    def __init__(self, pack_path, cmono=False):
        self.cmono = bool(cmono)
        z = np.load(pack_path)
        self.z = z
        self.class_dims = json.loads(str(z["class_dims"]))
        self.J = int(np.prod([len(c["edges"]) + 1 for c in self.class_dims]))
        cell = z["cls"].astype(np.int64) * K + z["bucket"].astype(np.int64)
        self.args = (z["score"].astype(np.float64), cell, None, z["admissible"].astype(np.bool_),
                     z["starts"].astype(np.int64), z["acc_w"].astype(np.int64), z["stc"].astype(np.float64),
                     z["st_full"].astype(np.float64), z["nch"].astype(np.float64), z["C0"].astype(np.float64),
                     float(z["W1"]), float(z["US"]))
        self.edges = z["edges"].tolist()
        self.n_cells = self.J * K
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
        f, viol, pen = penalty(np.asarray(v, np.int64), self.J, K, LAM, MU, PMONO, self.logg, self.cmono)
        self.n_eval += 1
        out = dict(E=pk + TOP5W * t5 + pen, peak=pk, top5=t5, field=f, viol=viol, theta=th, wch=wch)
        self.cache[key] = out
        return out

    def E(self, v):
        return self.parts(v)["E"]


def solve_pt(P, seed, budget=BUDGET_S, R=16, Tmin=0.005, Tmax=1.0):
    rng = np.random.default_rng(seed)
    t0 = time.time()
    n = P.n_cells
    temps = np.geomspace(Tmin, Tmax, R)
    X = np.full((R, n), NEUTRAL, np.int64)
    En = np.array([P.E(x) for x in X])
    best_v, best_E = X[0].copy(), En[0]
    sweeps = swaps = acc = prop = 0
    order = np.arange(R)
    while time.time() - t0 < budget:
        for slot in range(R):
            rr = order[slot]
            T = temps[slot]
            for _ in range(n):
                c = rng.integers(n)
                nv = rng.integers(len(GRID) - 1)
                nv = nv + 1 if nv >= X[rr, c] else nv
                y = X[rr].copy()
                y[c] = nv
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
    n = P.n_cells
    x = np.full(n, NEUTRAL, np.int64)
    Ex = P.E(x)
    best_v, best_E = x.copy(), Ex
    restarts = passes = 0
    while time.time() - t0 < budget:
        improved = True
        while improved and time.time() - t0 < budget:
            improved = False
            passes += 1
            for c in rng.permutation(n):
                cand = []
                for v in range(len(GRID)):
                    y = x.copy()
                    y[c] = v
                    cand.append((P.E(y), v))
                e_, v_ = min(cand)
                if e_ < Ex - 1e-12:
                    x[c], Ex, improved = v_, e_, True
        if Ex < best_E:
            best_v, best_E = x.copy(), Ex
        restarts += 1
        x = best_v.copy()
        for c in rng.choice(n, 3, replace=False):
            x[c] = rng.integers(len(GRID))
        Ex = P.E(x)
    return best_v, dict(passes=passes, restarts=restarts, wall=time.time() - t0)


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dev", "test"], default="dev")
    ap.add_argument("--solvers", nargs="+", default=["pt", "cd", "ptm", "cdm"])
    ap.add_argument("--keys", nargs="+", required=True, help="pack names <inst>_<arm>_r<k>")
    o = ap.parse_args()
    pdir = os.path.join(W, "work", "packs", o.mode)
    ledger = os.path.join(W, "results", f"solves_{o.mode}.csv")
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    done = set()
    if os.path.exists(ledger):
        with open(ledger) as f:
            done = {r["solve_key"] for r in csv.DictReader(f)}
    for key in o.keys:
        inst, arm, rk = key.rsplit("_", 2)
        seed = int(rk[1:])
        for s in o.solvers:
            skey = f"{s}_{key}"
            if skey in done:
                continue
            P = Problem(os.path.join(pdir, key + ".npz"), cmono=s.endswith("m"))
            ones = P.parts(np.full(P.n_cells, NEUTRAL, np.int64))
            assert abs(ones["peak"] - float(P.z["plain_peak"])) < 1e-9, (key, ones["peak"], float(P.z["plain_peak"]))
            n0 = P.n_eval
            P.cache = {}
            v, info = {"pt": solve_pt, "cd": solve_cd, "ptm": solve_pt, "cdm": solve_cd}[s](P, seed)
            pr = P.parts(v)
            mult = GRID[v].reshape(P.J, K).tolist()
            tdir = os.path.join(W, "tables", o.mode)
            os.makedirs(tdir, exist_ok=True)
            json.dump(dict(name=f"{s}_{key}", window_min=10, edges=P.edges, class_dims=P.class_dims, mult=mult,
                           fit=dict(solver=s, E=pr["E"], peak_day1=pr["peak"], top5_day1=pr["top5"], viol=pr["viol"],
                                    W1=float(P.z["W1"]), theta_fit=pr["theta"], grid=GRID.tolist(), lam=LAM, mu=MU,
                                    pmono=PMONO, top5w=TOP5W, budget_s=BUDGET_S, class_monotone=P.cmono)),
                      open(os.path.join(tdir, f"{s}_{key}.json"), "w"), indent=1)
            row = dict(solve_key=skey, mode=o.mode, inst=inst, arm=arm, rep=seed, solver=s, budget_s=BUDGET_S,
                       E=pr["E"], peak=pr["peak"], top5=pr["top5"], field=pr["field"], viol=pr["viol"],
                       mult=json.dumps(mult), edges=json.dumps([round(e, 4) for e in P.edges]),
                       n_evals=P.n_eval - n0, wall_s=info["wall"],
                       info=json.dumps({k: v_ for k, v_ in info.items() if k != "wall"}),
                       E_ones=ones["E"], peak_ones=ones["peak"], ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
            append(ledger, row)
            print(f"{skey}: E={pr['E']:.4f} peak={pr['peak']:.3f} (ones {ones['peak']:.3f}) mult={mult} "
                  f"evals={row['n_evals']} {info}", flush=True)


if __name__ == "__main__":
    main()
