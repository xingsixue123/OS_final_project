"""Benchmark driver.
  python run_bench.py --worker METHOD N SEED   -> runs one job, writes results/raw/METHOD__N__SEED.json
  python run_bench.py --run [--only substr]     -> schedules all jobs (CPU-slot + memory aware)
  python run_bench.py --collect                 -> results.csv from results/raw/*.json
"""
import json
import os
import resource
import subprocess
import sys
import time

A = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(A, "results", "raw")
LOGS = os.path.join(A, "results", "logs")
SIZES = [1000, 10000, 50000, 200000]


def qcap(n):
    if os.environ.get("BENCH_QCAP"):
        return float(os.environ["BENCH_QCAP"])
    return {1000: 300, 10000: 900, 50000: 2400, 200000: 2400}[n]


# method -> dict(sizes -> seeds, threads, mem_gb, params(n))
def registry():
    R = {}
    S3 = [0, 1, 2]
    R["greedy"] = dict(seeds={n: S3 for n in SIZES}, threads=1, mem=lambda n: 2)
    R["repair_only"] = dict(seeds={n: S3 for n in SIZES}, threads=1, mem=lambda n: 2)  # x_raw = 0 -> shared repair
    R["lp"] = dict(seeds={n: S3 for n in SIZES}, threads=1, mem=lambda n: 3)
    R["milp"] = dict(seeds={n: S3 for n in SIZES}, threads=1, mem=lambda n: 6)
    R["ls_greedy"] = dict(seeds={n: S3 for n in SIZES}, threads=1, mem=lambda n: 3)
    R["ls_lp"] = dict(seeds={n: S3 for n in SIZES}, threads=1, mem=lambda n: 3)
    R["mfsb"] = dict(seeds={n: S3 for n in SIZES}, threads=4, mem=lambda n: 2 + n * 64 * 4 * 8 / 1e9,
                     params=lambda n: dict(agents=64 if n <= 50000 else 16, steps=1000, dt=1.25, xi_scale=0.7,
                                          dtype="float32"))
    dense_seeds = {1000: S3, 10000: S3, 50000: [0]}
    for mode in ["ballistic", "discrete"]:
        R[f"sb_{mode}"] = dict(seeds=dense_seeds, threads=4, mem=lambda n: 2 + 6 * n * n * 4 / 1e9,
                               params=lambda n: dict(agents=64 if n <= 10000 else 16,
                                                     steps=1000 if n <= 10000 else 500, dtype="float32"))
    R["dwave_sa"] = dict(seeds={1000: S3, 10000: S3, 50000: [0]}, threads=1,
                         mem=lambda n: 2 + (0 if n <= 10000 else 25),
                         params=lambda n: dict(num_reads=16 if n <= 10000 else 4,
                                               num_sweeps=1000 if n <= 10000 else 200))
    R["dwave_tabu"] = dict(seeds={1000: S3, 10000: [0]}, threads=1, mem=lambda n: 3,
                           params=lambda n: dict(num_reads=4, timeout_ms=2000))
    R["openjij_sa"] = dict(seeds={1000: S3, 10000: S3, 50000: [0]}, threads=1,
                           mem=lambda n: 2 + (0 if n <= 10000 else 25),
                           params=lambda n: dict(num_reads=16 if n <= 10000 else 4,
                                                 num_sweeps=1000 if n <= 10000 else 200))
    R["cim_extahc"] = dict(seeds={1000: S3, 10000: [0]}, threads=2, mem=lambda n: 2 + 3 * n * n * 8 / 1e9,
                           params=lambda n: dict(num_runs=4, timesteps=1000))
    for algo in ["BSB", "DSB", "CAC"]:
        R[f"mq_{algo.lower()}"] = dict(seeds={1000: S3, 10000: S3}, threads=1, mem=lambda n: 4,
                                       params=lambda n: dict(batch=32, n_iter=1000))
        R[f"mq_{algo.lower()}_mf"] = dict(seeds={1000: S3, 10000: S3, 50000: [0], 200000: [0]}, threads=1,
                                          mem=lambda n: 2 + n * 32 * 8 * 10 / 1e9,
                                          params=lambda n: dict(batch=32, n_iter=1000))
    for k in [0.1, 1.0, 10.0]:
        R[f"mfsb_penalty_k{k}"] = dict(seeds={1000: S3}, threads=4, mem=lambda n: 2,
                                       params=lambda n, k=k: dict(agents=64, steps=1000, dt=1.25, xi_scale=0.7,
                                                                  dtype="float32", penalty_k=k))
    return R


def set_threads(t):
    for v in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"]:
        os.environ[v] = str(t)


def worker(method, n, seed):
    R = registry()[method]
    th = int(os.environ.get("BENCH_THREADS", R["threads"]))
    set_threads(th)
    import numpy as np
    import torch
    torch.set_num_threads(th)
    sys.path.insert(0, A)
    from instance import make_instance
    from solvers.common import greedy, repair, evaluate
    from solvers.lp_milp import solve_lp, solve_milp
    t_inst = time.time()
    inst = make_instance(n, seed)
    rss_inst = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    # references (not timed as part of the method)
    xg = greedy(inst)
    greedy_peak = evaluate(inst, repair(inst, xg)[0])["peak"]
    lp = solve_lp(inst)
    z_lp = lp["z_lp"]
    params = R.get("params", lambda n: {})(n)
    extra = {}
    t0 = time.time()
    x_raw = None
    x_rep = None
    if method == "greedy":
        x_raw = greedy(inst)  # re-run inside the timed region
    elif method == "repair_only":
        x_raw = np.zeros(n)  # attribution baseline: the shared repair alone (peak-aware greedy add)
    elif method == "lp":
        lp2 = solve_lp(inst)  # re-run inside the timed region
        x_raw = lp2["x_raw"]
        extra = dict(n_frac=lp2["n_frac"], lp_status=lp2["status"], lp_time=lp2["lp_time"])
    elif method == "milp":
        tl = 60 if n <= 10000 else 300
        params = dict(time_limit=tl, threads=1)
        r = solve_milp(inst, tl, threads=1)
        x_raw = r["x_raw"]
        extra = {k: v for k, v in r.items() if k != "x_raw"}
    elif method.startswith("ls_"):
        from solvers.local_search import local_search
        x0 = xg if method == "ls_greedy" else lp["x_raw"]
        x_raw, info = local_search(inst, x0, seed=seed)
        params = dict(n_moves=info["ls_moves"], g=info["ls_g"], T0=info["ls_T0"], T1=info["ls_T1"],
                      moves="70% swap(top-3 window add, random drop)/15% add/15% drop, hard budget")
        extra = dict(ls_time=info["ls_time"])
    else:
        from solvers.qubo import outer_loop
        p = dict(params)
        penalty_k = p.pop("penalty_k", None)
        if method.startswith("mfsb"):
            from solvers import mfsb
            dt = torch.float32 if p.pop("dtype") == "float32" else torch.float64
            inner = mfsb.make_inner(seed=seed, dtype=dt, **p)
        elif method.startswith("sb_"):
            from solvers.inner_pkg import make_sb
            inner = make_sb(mode=method[3:], seed=seed, **p)
        elif method == "dwave_sa":
            from solvers.inner_pkg import make_dwave_sa
            inner = make_dwave_sa(seed=seed, **p)
        elif method == "dwave_tabu":
            from solvers.inner_pkg import make_dwave_tabu
            inner = make_dwave_tabu(seed=seed, **p)
        elif method == "openjij_sa":
            from solvers.inner_pkg import make_openjij
            inner = make_openjij(seed=seed, **p)
        elif method == "cim_extahc":
            from solvers.inner_pkg import make_cim
            inner = make_cim(seed=seed, **p)
        elif method.startswith("mq_"):
            from solvers.inner_mq import make_mq
            parts = method.split("_")
            inner = make_mq(algo=parts[1].upper(), matrix_free=(len(parts) > 2 and parts[2] == "mf"), seed=seed, **p)
        else:
            raise ValueError(method)
        logf = open(os.path.join(LOGS, f"{method}__{n}__{seed}.log"), "a")
        lg = lambda s: (logf.write(s + "\n"), logf.flush())
        best, hist, info = outer_loop(inst, inner, time_cap=qcap(n), log=lg, penalty_P=penalty_k)
        params.update(dict(outer_max=10, beta=8.0, delta_frac=0.003, bisect_first=8, bisect_later=4,
                           max_calls=40, time_cap=qcap(n), torch_threads=th))
        extra = dict(info)
        extra["best_iter"] = best["it"]
        extra["best_mu"] = best.get("mu")
        x_raw = best["x_raw"]
        x_rep = best["x_rep"]
    wall = time.time() - t0
    row = dict(method=method, n=n, seed=seed, z_lp=z_lp, greedy_peak=greedy_peak, headroom=greedy_peak - z_lp,
               wall_time=wall, rss_after_instance_mb=rss_inst, threads=th, params=json.dumps(params))
    if x_raw is None:
        row.update(status="no_solution")
    else:
        if x_rep is None:
            x_rep, rinfo = repair(inst, x_raw)
            extra.update(rinfo)
        er, ep = evaluate(inst, x_raw), evaluate(inst, x_rep)
        row.update(status="ok", peak_raw=er["peak"], use_raw=er["use"], nsel_raw=er["n_sel"],
                   peak_rep=ep["peak"], use_rep=ep["use"], nsel_rep=ep["n_sel"],
                   gap_abs=ep["peak"] - z_lp,
                   gap_pct=100 * (ep["peak"] - z_lp) / (greedy_peak - z_lp))
    row["repair_time_incl"] = time.time() - t0 - wall
    row["peak_mem_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    row["extra"] = json.dumps(extra, default=float)
    with open(os.path.join(RAW, f"{method}__{n}__{seed}.json"), "w") as f:
        json.dump(row, f, default=float)
    print(json.dumps(row, default=float))


def run(only=None, max_cores=24, max_mem=100):
    R = registry()
    # jobs already running (e.g. from another scheduler): skip them and count their cores/mem as busy
    ps = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout.splitlines()
    busy = set()
    for line in ps:
        t = line.split()
        if len(t) >= 6 and t[1].endswith("run_bench.py") and t[2] == "--worker":
            busy.add((t[3], int(t[4]), int(t[5])))
    busy_c = sum(R[b[0]]["threads"] for b in busy if b[0] in R)
    busy_m = sum(R[b[0]]["mem"](b[1]) for b in busy if b[0] in R)
    print(f"{len(busy)} jobs already running elsewhere ({busy_c} cores, {busy_m:.0f} GB)", flush=True)
    jobs = []
    for m, r in R.items():
        if only and not any(o in m for o in only.split(",")):
            continue
        for n, seeds in r["seeds"].items():
            if os.environ.get("BENCH_SIZES") and str(n) not in os.environ["BENCH_SIZES"].split(","):
                continue
            for s in seeds:
                if os.path.exists(os.path.join(RAW, f"{m}__{n}__{s}.json")) or (m, n, s) in busy:
                    continue
                jobs.append((m, n, s, r["threads"], r["mem"](n)))
    # long first: big n, dense solvers
    jobs.sort(key=lambda j: (-j[1], -j[4], j[0], j[2]))
    print(f"{len(jobs)} jobs", flush=True)
    running = []
    free_c, free_m = max_cores - busy_c, max_mem - busy_m
    ext = set(busy)
    while jobs or running:
        started = True
        while started:
            started = False
            for j in list(jobs):
                if j[3] <= free_c and j[4] <= free_m:
                    m, n, s, th, mem = j
                    lf = open(os.path.join(LOGS, f"{m}__{n}__{s}.out"), "w")
                    env = dict(os.environ)
                    p = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--worker", m, str(n), str(s)],
                                         stdout=lf, stderr=subprocess.STDOUT, env=env, cwd=A)
                    running.append((p, j, time.time(), lf))
                    free_c -= th
                    free_m -= mem
                    jobs.remove(j)
                    print(f"[{time.strftime('%H:%M:%S')}] start {m} n={n} s={s} (free cores {free_c}, mem {free_m:.0f}GB, queued {len(jobs)})", flush=True)
                    started = True
                    break
        time.sleep(2)
        if ext:
            ps = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
            for b in list(ext):
                if f"--worker {b[0]} {b[1]} {b[2]}" not in ps:
                    ext.discard(b)
                    free_c += R[b[0]]["threads"]
                    free_m += R[b[0]]["mem"](b[1])
        for r in list(running):
            p, j, ts, lf = r
            if p.poll() is not None:
                running.remove(r)
                lf.close()
                free_c += j[3]
                free_m += j[4]
                print(f"[{time.strftime('%H:%M:%S')}] done  {j[0]} n={j[1]} s={j[2]} rc={p.returncode} {time.time()-ts:.0f}s", flush=True)


def collect():
    import csv
    import glob
    rows = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(RAW, "*.json")))]
    keys = ["method", "n", "seed", "status", "peak_raw", "peak_rep", "use_raw", "use_rep", "nsel_raw", "nsel_rep",
            "z_lp", "greedy_peak", "headroom", "gap_abs", "gap_pct", "wall_time", "repair_time_incl",
            "peak_mem_mb", "rss_after_instance_mb", "threads", "params", "extra"]
    rows.sort(key=lambda r: (r["n"], r["method"], r["seed"]))
    with open(os.path.join(A, "results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"{len(rows)} rows -> results.csv")


if __name__ == "__main__":
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(LOGS, exist_ok=True)
    if sys.argv[1] == "--worker":
        worker(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    elif sys.argv[1] == "--run":
        only = sys.argv[3] if len(sys.argv) > 3 and sys.argv[2] == "--only" else None
        run(only)
    elif sys.argv[1] == "--collect":
        collect()
