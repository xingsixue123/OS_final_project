"""WP1 (H1' breadth, offline) driver. Phase-1 FROZEN configurations only (no tuning): pure evaluation.

  wp1.py r0     [--keys ...]   train in PolicyQ2 'dump' mode (instance + Baleen peak-blind OPT order = R0 in ONE
                               train) + OPT-mode sim with --ap-threshold converged to 35.599 MB/s +-1%   (Baleen env)
  wp1.py solve  [--keys ...]   LP+repair / CP-SAT 300 s / PT 300 s (phase-1 300-s configs, seed 0) on cores 0-7, one
                               process per (instance, method), strictly sequential via the P2 cores lock (solver env)
  wp1.py sim    [--keys ...]   replay every solution through the identical train/sim pipeline (Baleen env)
  wp1.py verify               compare rebuilt instances with phase-1 common/inst (Region7/6 s0-0.3)

Priority order of the instance list: samples 0-0.3 of all four regions first, then 0.4-0.9.
Phase-1 300-s held-out solutions (seed 0) of lp / cpsat / pt on Region7/6 s0.1-0.3 are REUSED (identical frozen
configs, same instances, same machine; solved in phase 1 on explore/common/inst) instead of re-solving them.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
WP1 = os.path.dirname(HERE)
P2 = os.path.dirname(WP1)
WP5SRC = os.path.join(P2, "wp5_ising", "src")
INST = os.path.join(WP1, "inst")
SOLS = os.path.join(WP1, "sols")
TRIALS = os.path.join(WP1, "trials.csv")
SIMS = os.path.join(WP1, "results", "sims.jsonl")
PH1 = "/home/sxing/project/OS_final_project/changes/1_literature_review/explore"
SOLVER_PY = os.path.join(PH1, "env", "bin", "python")
JOBS = json.load(open(os.path.join(WP1, "jobs.json")))["jobs"]
PLAN1 = json.load(open(os.path.join(PH1, "q2", "plan_F1.json")))
METHODS = ["lp", "cpsat", "pt"]
REUSE = {f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0.1", "0.2", "0.3")}


def ordered_keys():
    ks = list(JOBS)
    return sorted(ks, key=lambda k: (JOBS[k]["sample"] >= 0.35, JOBS[k]["sample"],
                                     ["Region4", "Region5", "Region7", "Region6"].index(JOBS[k]["region"])))


def frozen_cfg(solver, budget="300"):
    for m in PLAN1["methods"]:
        if m["solver"] == solver:
            return m["cfg_by_budget"][budget]
    raise KeyError(solver)


def inst_path(key):
    return os.path.join(INST, f"full_{key}.npz")


def read_sims():
    if not os.path.exists(SIMS):
        return []
    return [json.loads(l) for l in open(SIMS) if l.strip()]


# ------------------------------------------------------------------ r0 (+ instance dump)
def do_r0(keys, workers):
    sys.path.insert(0, HERE)
    import p2sim as S
    done = {r["exp"] for r in read_sims() if r.get("matched")}
    os.makedirs(INST, exist_ok=True)

    def one(k):
        J = JOBS[k]
        exp = f"wp1_{k}_R0"
        if exp in done and os.path.exists(inst_path(k)):
            return
        try:
            S.evaluate(None, None, J["region"], J["sample"], J["ea"], J["author_th"], exp,
                       extra=dict(instance=k, method="R0", seed=0), mode="dump", inst_out=inst_path(k))
        except Exception as e:  # report failures too
            print(f"FAILED {exp}: {e!r}", flush=True)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, keys))


# ------------------------------------------------------------------ solves (cores 0-7)
def reused_rows():
    """phase-1 held-out 300-s seed-0 rows of lp/cpsat/pt (copied into WP1 trials.csv once, marked reused)."""
    import csv
    rows = []
    with open(os.path.join(PH1, "q2", "trials.csv")) as f:
        for r in csv.DictReader(f):
            if r["phase"] == "heldout" and r["form"] == "F1" and r["solver"] in METHODS and r["status"] == "ok" \
                    and float(r["budget"]) == 300 and int(r["seed"]) == 0:
                rows.append(r)
    return rows


def do_solve(keys, wait):
    sys.path.insert(0, WP5SRC)
    import p2run as R
    import csv
    have, contaminated = set(), set()
    if os.path.exists(TRIALS):
        with open(TRIALS) as f:
            for r in csv.DictReader(f):
                if r["status"] == "ok":
                    have.add((r["instance"], r["solver"]))
                elif r["status"] == "contaminated_overlap":
                    contaminated.add((r["instance"], r["solver"]))
    # reused phase-1 solutions
    add = []
    for r in reused_rows():
        k = r["instance"].replace("full_", "")
        if k in REUSE and (r["instance"], r["solver"]) not in have:
            row = {c: r.get(c, "") for c in R.COLS}
            row.update(phase="wp1_reused_phase1_heldout", affinity="0-7",
                       sol=os.path.join(PH1, "q2", r["sol"]), tag="reused:" + r["instance"],
                       key=R.row_key("wp1_reused", r["instance"], r["solver"], r["cfg_hash"], 300, 0, "reused"))
            add.append(row)
            have.add((r["instance"], r["solver"]))
    if add:
        R.append_rows(add, TRIALS)
        print(f"reused {len(add)} phase-1 rows", flush=True)
    env = dict(os.environ, OMP_NUM_THREADS="8", NUMBA_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", MKL_NUM_THREADS="8")
    pending = [(k, m) for k in keys for m in METHODS if (f"full_{k}", m) not in have]
    gate = os.path.join(WP1, ".solve_gate")      # scheduling gate (exists = may take the cores lock); no effect on runs
    while pending:
        progressed = False
        for (k, m) in list(pending):
            if not os.path.exists(inst_path(k)):
                continue
            while not os.path.exists(gate):
                time.sleep(15)
            cfg = frozen_cfg(m, "300")
            cmd = ["taskset", "-c", "0-7", SOLVER_PY, os.path.join(WP5SRC, "p2run.py"), "--insts", inst_path(k),
                   "--solver", m, "--budget", "300", "--seed", "0", "--cfg", json.dumps(cfg), "--phase", "wp1",
                   "--tag", f"wp1_{k}_{m}" + ("_rerun" if (f"full_{k}", m) in contaminated else ""), "--trials", TRIALS,
                   "--sols", SOLS, "--skip-done"]
            t = time.time()
            p = subprocess.run(cmd, capture_output=True, text=True, env=env)
            res = [ln for ln in p.stdout.splitlines() if ln.startswith("RESULT ")]
            print(f"[solve] {k} {m} ({time.time() - t:.0f}s) {res[-1][7:] if res else 'NO RESULT ' + p.stderr[-400:]}",
                  flush=True)
            pending.remove((k, m))
            progressed = True
        if pending and not progressed:
            if not wait:
                break
            time.sleep(30)


# ------------------------------------------------------------------ sims of the solutions
def do_sim(keys, wait, workers):
    sys.path.insert(0, HERE)
    import p2sim as S
    import csv
    inflight = set()
    ex = ThreadPoolExecutor(max_workers=workers)
    futs = []
    keys = set(keys)
    while True:
        sims = read_sims()
        done = {r["exp"] for r in sims}
        r0 = {r["instance"]: r for r in sims if r.get("method") == "R0" and r.get("matched")}
        rows = []
        if os.path.exists(TRIALS):
            with open(TRIALS) as f:
                rows = [r for r in csv.DictReader(f) if r["status"] == "ok"]
        todo = 0
        for r in rows:
            k = r["instance"].replace("full_", "")
            if k not in keys:
                continue
            exp = f"wp1_{k}_{r['solver']}_{r['cfg_hash']}_s{r['seed']}" + ("_rerun" if "rerun" in str(r["tag"]) else "")
            if exp in done or exp in inflight:
                continue
            todo += 1
            if k not in r0:
                continue
            J = JOBS[k]
            solved = os.path.join(PH1, "common", "inst", f"full_{k}.npz") if r["phase"].startswith("wp1_reused") \
                else inst_path(k)
            sol = r["sol"] if os.path.isabs(r["sol"]) else os.path.join(WP1, r["sol"])
            inflight.add(exp)
            futs.append(ex.submit(S.evaluate, sol, solved, J["region"], J["sample"], J["ea"],
                                  round(float(r0[k]["threshold"]), 3), exp,
                                  dict(instance=k, method=r["solver"], seed=int(r["seed"]), cfg_hash=r["cfg_hash"],
                                       objective=float(r["objective"]), wall=float(r["wall"]),
                                       trial_phase=r["phase"]), "replay"))
            print(f"submitted {exp}", flush=True)
        for f in [f for f in futs if f.done()]:
            try:
                f.result()
            except Exception as e:  # report failures too
                print("FAILED:", repr(e), flush=True)
            futs.remove(f)
        if not wait and not futs:
            break
        if wait and not futs and todo == 0 and all(
                sum(1 for r in rows if r["instance"] == f"full_{k}") >= len(METHODS) for k in keys):
            break
        time.sleep(30)


def do_verify():
    import numpy as np
    out = {}
    for r in ("Region7", "Region6"):
        for s in ("0", "0.1", "0.2", "0.3"):
            k = f"{r}_s{s}"
            a, b = inst_path(k), os.path.join(PH1, "common", "inst", f"full_{k}.npz")
            if not os.path.exists(a):
                out[k] = "missing"
                continue
            za, zb = np.load(a), np.load(b)
            ok = {}
            for kk in ("D_data", "D_indices", "D_indptr", "D_shape", "C", "s", "B", "active", "base_order", "keys",
                       "ts0", "ea"):
                ok[kk] = bool(np.array_equal(za[kk], zb[kk]))
            out[k] = ok
            print(k, "IDENTICAL" if all(ok.values()) else ok, flush=True)
    json.dump(out, open(os.path.join(WP1, "results", "verify_instances.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["r0", "solve", "sim", "verify", "list"])
    ap.add_argument("--keys", nargs="+", default=None)
    ap.add_argument("--wait", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    o = ap.parse_args()
    keys = o.keys or ordered_keys()
    if o.what == "list":
        print(" ".join(keys))
    elif o.what == "r0":
        do_r0(keys, o.workers)
    elif o.what == "solve":
        do_solve(keys, o.wait)
    elif o.what == "sim":
        do_sim(keys, o.wait, o.workers)
    elif o.what == "verify":
        do_verify()


if __name__ == "__main__":
    main()
