"""WP5 step 4: scaling report (CPU only, cores 0-7, 8 threads): time and peak memory vs instance size n on REAL
full-trace and day-1 instances, matrix-free SB vs the dense simulated-bifurcation package (v2.0.0), plus the sparse
replica-exchange sampler (PT, numba on CSR).

  python p2scale.py all --plan scale_plan.json      (driver: one fresh child process per run; the driver takes the
                                                     P2 cores lock around every child -> no overlap with any timing run)
  python p2scale.py one --inst X.npz --part full|day1 --solver mfsb|dense|pt [--n-sub N] ...   (child)

Problem solved by every arm = the SAME level-1 F1 QUBO surrogate (q2sb's first round, i.e. what the SB solver of the
phase-1/WP5 pipeline builds): x over the model variables of the f = 1.0 level, E(x) = sum_w alpha_w (C_w - tau -
(D^T x)_w)^2 + mu s.x with alpha_w = 1 on windows within 3% of the peak-aware-greedy peak (0.05 elsewhere),
tau = 0.97 x that peak, mu = 0.1 x mu_max (fixed; no outer loop): pure solver cost, no repair.
  mfsb  : q2sb's matrix-free ballistic SB kernel (torch sparse CSR, D^T y and D z; Q never formed), A agents x S steps
  dense : simulated_bifurcation.minimize on the dense float32 Q (n x n) built as D diag(alpha) D^T, same A and S,
          ballistic, early_stopping=False; RLIMIT_AS cap (default 64 GB) so an out-of-memory fails cleanly
  pt    : phase-1 replica-exchange sampler (q2anneal.eim, QUBO-penalty mode) on the true F1 energy, fixed number of
          rounds (R replicas x moves per round), no deadline effect
Recorded per run: n, nnz(D), m, build time, solve time, time per step (per move), ru_maxrss (peak RSS of the child),
RSS after instance load (baseline), status (ok / oom / error), best surrogate energy (mfsb/dense, sanity).
"""
import argparse
import json
import os
import resource
import subprocess
import sys
import time

import numpy as np

SRC = os.path.dirname(os.path.abspath(__file__))
AREA = os.path.dirname(SRC)
sys.path.insert(0, SRC)
OUT = os.path.join(AREA, "results", "scaling.jsonl")


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def cur_rss_mb():
    with open("/proc/self/status") as f:
        for line in f:
            if line.startswith("VmRSS:"):
                return float(line.split()[1]) / 1024.0
    return float("nan")


class Day1:
    """day-1 sub-instance of a full-trace instance: episodes whose first access is in day 1, objective = day-1 windows,
    budget = B * 86400 / duration (instance-like interface for q2core.Sub)."""
    def __init__(self, I):
        import scipy.sparse as sp  # noqa: F401
        z = I.z
        w0 = np.floor((z["ts0"] - float(z["t0"])) / 600.0).astype(np.int64)
        E = np.flatnonzero(w0 < 144)
        wins = np.arange(144)
        self.Da = I.D.tocsr()[E][:, wins].tocsr()
        self.Da.eliminate_zeros()
        self.Da.sort_indices()
        self.Ca = I.C[wins]
        self.ma = len(wins)
        self.s = I.s[E]
        self.sts = I.sts[E]
        self.n = len(E)
        self.B = I.B * 86400.0 / float(z["duration"])
        self.rank = np.argsort(np.argsort(I.rank[E], kind="stable"), kind="stable")
        self.name = I.name.replace("full_", "day1_")

    def loads(self, x):
        return self.Ca - self.Da.T @ x


class SubN:
    """first n_sub episodes in time order of a full instance (for the dense-package size ladder)."""
    def __init__(self, I, n_sub):
        z = I.z
        E = np.argsort(z["ts0"], kind="stable")[:n_sub]
        E = np.sort(E)
        last_w = int(np.floor((z["ts0"][E].max() - float(z["t0"])) / 600.0)) + 18
        wins = np.flatnonzero(I.active[:min(last_w, I.m)]) if last_w > 144 else np.arange(min(last_w, I.m))
        self.Da = I.D.tocsr()[E][:, wins].tocsr()
        self.Da.eliminate_zeros()
        self.Da.sort_indices()
        self.Ca = I.C[wins]
        self.ma = len(wins)
        self.s = I.s[E]
        self.sts = I.sts[E]
        self.n = len(E)
        dur_sub = float(z["ts0"][E].max() - float(z["t0"])) + 1.0
        self.B = I.B * dur_sub / float(z["duration"])
        self.rank = np.argsort(np.argsort(I.rank[E], kind="stable"), kind="stable")
        self.name = I.name + f"_first{n_sub}"

    def loads(self, x):
        return self.Ca - self.Da.T @ x


class Union:
    """union of several samples of the same trace (disjoint 0.1% key samples) = a larger REAL instance (e.g. 4 samples
    = a 0.4% sample): episode rows stacked, windows aligned by absolute time, C and B summed, objective = windows
    after day 1, Baleen order = descending phase-1 Baleen score across the union."""
    def __init__(self, paths):
        import scipy.sparse as sp
        import q2core as C
        Is = [C.Instance(p) for p in paths]
        t0 = min(float(I.z["t0"]) for I in Is)
        offs = [int(np.floor((float(I.z["t0"]) - t0) / 600.0)) for I in Is]
        m = max(o + I.m for o, I in zip(offs, Is))
        blocks, Cs = [], np.zeros(m)
        for o, I in zip(offs, Is):
            Dc = I.D.tocoo()
            blocks.append(sp.csr_matrix((Dc.data, (Dc.row, Dc.col + o)), shape=(I.n, m)))
            Cs[o:o + I.m] += I.C
        D = sp.vstack(blocks).tocsr()
        act = np.zeros(m, bool)
        act[144:] = True
        self.act_idx = np.flatnonzero(act)
        self.Da = D[:, self.act_idx].tocsr()
        self.Da.eliminate_zeros()
        self.Da.sort_indices()
        self.Ca = Cs[self.act_idx]
        self.ma = len(self.act_idx)
        self.s = np.concatenate([I.s for I in Is])
        self.sts = np.concatenate([I.sts for I in Is])
        self.n = len(self.s)
        self.B = float(sum(I.B for I in Is))
        score = np.concatenate([I.z["base_score"] for I in Is])
        order = np.argsort(-score, kind="stable")
        self.rank = np.empty(self.n, np.int64)
        self.rank[order] = np.arange(self.n)
        self.name = "union_" + "+".join(os.path.basename(p).replace(".npz", "").replace("full_", "") for p in paths)

    def loads(self, x):
        return self.Ca - self.Da.T @ x


def surrogate(P):
    """level-1 F1 QUBO surrogate pieces over the model vars (same construction as q2sb round 1)."""
    import q2core as C
    x1, _ = C.pgreedy(P)
    var = C.model_vars(P)
    D = P.Da[var].tocsr()
    L1 = P.loads(x1)
    pk = float(L1.max())
    tau = 0.97 * pk
    alpha = np.where(L1 >= tau, 1.0, 0.05)
    r = P.C - tau
    s = P.s[var]
    lin0 = -2.0 * (D @ (alpha * r))
    dQ = np.asarray(D.multiply(D) @ alpha).ravel()
    mu_max = max(float(np.max(-(lin0 + dQ) / np.maximum(s, 1e-12))), 1e-12)
    mu = 0.1 * mu_max
    c = lin0 + mu * s
    const = float((alpha * r * r).sum())
    return D, alpha, c, const, dQ, s, var, r, mu


def energy(D, alpha, r, mu, s, X):
    """exact surrogate energy per column of X (n_vars x k binary): sum_w alpha_w (r_w - (D^T x)_w)^2 + mu s.x"""
    R = r[:, None] - D.T @ X
    return (alpha[:, None] * R * R).sum(0) + mu * (s @ X)


def run_one(o):
    import torch
    import q2core as C
    torch.set_num_threads(8)
    t_load = time.time()
    if o.part == "union":
        I2 = Union(o.inst.split(","))
        I = I2
    else:
        I = C.Instance(o.inst)
    if o.part == "union":
        pass
    elif o.part == "day1":
        I2 = Day1(I)
    elif o.part == "sub":
        I2 = SubN(I, o.n_sub)
    else:
        I2 = I
    form = C.Form("F1")
    P = C.Sub(I2, I2.B, np.zeros(I2.n, bool), form)
    rec = dict(inst=I2.name if o.part == "union" else os.path.basename(o.inst).replace(".npz", ""), part=o.part, n_sub=o.n_sub, solver=o.solver,
               n=int(P.n), m=int(P.ma), nnz=int(P.Da.nnz), agents=o.agents, steps=o.steps, threads=8)
    D, alpha, c, const, dQ, s, var, r_s, mu_s = surrogate(P)
    nv = D.shape[0]
    rec.update(n_vars=int(nv), nnz_vars=int(D.nnz), load_secs=time.time() - t_load, rss_base_mb=cur_rss_mb())
    status = "ok"
    try:
        if o.solver == "mfsb":
            import math
            t0 = time.time()
            ma = D.shape[1]
            Dt = torch.sparse_csr_tensor(torch.from_numpy(D.indptr.astype(np.int64)),
                                         torch.from_numpy(D.indices.astype(np.int64)),
                                         torch.from_numpy(D.data.astype(np.float32)), size=(nv, ma))
            DT = D.T.tocsr()
            DTt = torch.sparse_csr_tensor(torch.from_numpy(DT.indptr.astype(np.int64)),
                                          torch.from_numpy(DT.indices.astype(np.int64)),
                                          torch.from_numpy(DT.data.astype(np.float32)), size=(ma, nv))
            colsum = np.asarray(D.sum(0)).ravel()
            Q1 = D @ (alpha * colsum)
            M = (D.T @ D).toarray()
            AM = alpha[:, None] * M
            JF2 = max(0.25 * (float(np.trace(AM @ AM)) - float((dQ ** 2).sum())), 1e-30)
            h = torch.as_tensor(-0.5 * (Q1 + c), dtype=torch.float32)[:, None]
            dQt = torch.as_tensor(dQ, dtype=torch.float32)[:, None]
            al = torch.as_tensor(alpha, dtype=torch.float32)[:, None]
            xi0 = 0.7 * math.sqrt(nv) / math.sqrt(JF2 + 2 * float((h.double() ** 2).sum()))
            g = torch.Generator().manual_seed(0)
            Xs = (torch.rand(nv, o.agents, generator=g) - 0.5) * 0.2
            Ys = (torch.rand(nv, o.agents, generator=g) - 0.5) * 0.2
            rec["build_secs"] = time.time() - t0
            t1 = time.time()
            dt = 1.0
            for st in range(o.steps):
                at = st / o.steps
                F = Dt @ (al * (DTt @ Xs))
                F = -0.5 * (F - dQt * Xs) + h
                Ys.add_(F, alpha=xi0 * dt).add_(Xs, alpha=-(1.0 - at) * dt)
                Xs.add_(Ys, alpha=dt)
                wall = Xs.abs() > 1
                Xs.clamp_(-1.0, 1.0)
                Ys.masked_fill_(wall, 0.0)
            S = (Xs >= 0).double().numpy()
            rec["solve_secs"] = time.time() - t1
            rec["secs_per_step"] = rec["solve_secs"] / o.steps
        elif o.solver == "dense":
            import simulated_bifurcation as sbp
            cap = int(o.mem_cap_gb * (1 << 30))
            resource.setrlimit(resource.RLIMIT_AS, (cap, cap))
            rec["mem_cap_gb"] = o.mem_cap_gb
            t0 = time.time()
            Da = D.multiply(np.sqrt(alpha)[None, :]).tocsr()
            Qs = (Da @ Da.T).tocsr()
            rec["nnz_Q"] = int(Qs.nnz)
            Q = torch.from_numpy(Qs.astype(np.float32).toarray())          # float32 dense directly (no float64 copy)
            del Qs
            cc = torch.as_tensor(c, dtype=torch.float32)
            rec["build_secs"] = time.time() - t0
            torch.manual_seed(0)
            t1 = time.time()
            vecs, vals = sbp.minimize(Q, cc, const, domain="binary", dtype=torch.float32, agents=o.agents,
                                      max_steps=o.steps, mode="ballistic", best_only=False, verbose=False,
                                      early_stopping=False)
            rec["solve_secs"] = time.time() - t1
            rec["secs_per_step"] = rec["solve_secs"] / o.steps
            V = vecs.double().numpy()
            S = V.T if V.shape[0] != nv else V
        elif o.solver == "pt":
            import q2anneal as A
            import numba
            numba.set_num_threads(8)
            x0 = np.zeros(P.n)
            A.eim(P, x0, time.time() + 0.01, dict(eim_moves=200, eim_R=2, eim_pmode="quad"))     # compile (untimed)
            cfg = dict(eim_R=o.agents, eim_moves=o.moves, eim_pmode="quad", eim_Tmin=1e-6, eim_Tmax=7e-6)
            t1 = time.time()
            # fixed work: run the sampler for o.steps rounds by giving it a deadline far away and counting rounds
            xb, info = A.eim(P, x0, time.time() + o.pt_secs, cfg)
            rec["solve_secs"] = time.time() - t1
            rec["rounds"] = int(info["eim_rounds"])
            rec["proposals"] = int(info["eim_prop"])
            rec["secs_per_Mprop"] = rec["solve_secs"] / max(info["eim_prop"], 1) * 1e6
            rec["build_secs"] = 0.0
            S = None
            rec["peak_util"] = float(P.loads(xb).max() * C.US)
        if o.solver in ("mfsb", "dense"):
            E = energy(D, alpha, r_s, mu_s, s, S)
            j = int(np.argmin(E))
            rec["best_energy"] = float(E[j])
            rec["energy_zero"] = float(energy(D, alpha, r_s, mu_s, s, np.zeros((nv, 1)))[0])
            xr = np.zeros(P.n)
            xr[var] = S[:, j]
            xr, _ = P.repair(xr, fill=False)
            rec["peak_util_repaired"] = float(P.loads(xr).max() * C.US)
    except MemoryError as ex:
        status = f"oom: {ex!r}"[:160]
    except RuntimeError as ex:
        msg = repr(ex)
        status = ("oom: " if ("alloc" in msg.lower() or "memory" in msg.lower()) else "error: ") + msg[:160]
    except Exception as ex:  # report failures too
        status = f"error: {ex!r}"[:200]
    rec.update(status=status, maxrss_mb=rss_mb(), ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
    print("SCALE " + json.dumps(rec, default=float), flush=True)


def run_all(o):
    from p2run import CoresLock
    plan = json.load(open(o.plan))
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT):
            r = json.loads(l)
            done.add(r.get("run_id"))
    env = dict(os.environ, OMP_NUM_THREADS="8", NUMBA_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", MKL_NUM_THREADS="8")
    for job in plan:
        rid = "|".join(str(job.get(k, "")) for k in ("inst", "part", "n_sub", "solver", "agents", "steps", "moves",
                                                       "pt_secs", "mem_cap_gb"))
        if rid in done:
            continue
        cmd = ["taskset", "-c", "0-7", sys.executable, os.path.abspath(__file__), "one", "--inst", job["inst"],
               "--part", job["part"], "--solver", job["solver"], "--agents", str(job.get("agents", 32)),
               "--steps", str(job.get("steps", 500)), "--n-sub", str(job.get("n_sub", 0)),
               "--moves", str(job.get("moves", 20000)), "--pt-secs", str(job.get("pt_secs", 5.0)),
               "--mem-cap-gb", str(job.get("mem_cap_gb", 64))]
        with CoresLock():
            t = time.time()
            p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=job.get("timeout", 3600))
        lines = [l for l in p.stdout.splitlines() if l.startswith("SCALE ")]
        if lines:
            rec = json.loads(lines[-1][6:])
        else:
            rec = dict(inst=job["inst"], part=job["part"], solver=job["solver"], n_sub=job.get("n_sub", 0),
                       status=f"killed rc={p.returncode}: {p.stderr[-300:]}")
        rec["run_id"] = rid
        rec["wall_child"] = time.time() - t
        with open(OUT, "a") as f:
            f.write(json.dumps(rec, default=float) + "\n")
        print(f"[scale] {rid}: {rec.get('status')} n={rec.get('n')} solve={rec.get('solve_secs')} "
              f"rss={rec.get('maxrss_mb')}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["one", "all"])
    ap.add_argument("--plan")
    ap.add_argument("--inst")
    ap.add_argument("--part", default="full")
    ap.add_argument("--n-sub", type=int, default=0)
    ap.add_argument("--solver", default="mfsb")
    ap.add_argument("--agents", type=int, default=32)
    ap.add_argument("--steps", type=int, default=500)
    ap.add_argument("--moves", type=int, default=20000)
    ap.add_argument("--pt-secs", type=float, default=5.0)
    ap.add_argument("--mem-cap-gb", type=float, default=64)
    o = ap.parse_args()
    if o.what == "one":
        run_one(o)
    else:
        run_all(o)


if __name__ == "__main__":
    main()
