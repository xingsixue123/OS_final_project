"""Label-solver evidence (WP5 step 3): OPT-mode simulated P100 of dev full-trace selections (Baleen env).

  python p2labsim.py --phase deval --solvers pt eim cpsat --budgets 10 --seed 101
Uses the WP1 sim pipeline (wp1_offline/src/p2sim.py: identical train/sim, PolicyQ2 replay, converge to 35.599 +-1%,
pinned 8-11,20-23, shared <= 6 sim slots) with work dir wp5_ising/work; threshold hint = WP1's converged R0 threshold
of the instance. Results -> wp5_ising/results/sims_label.jsonl.
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

AREA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P2 = os.path.dirname(AREA)
os.environ["P2_SIM_WORK"] = os.path.join(AREA, "work")
os.environ["P2_SIM_RESULTS"] = os.path.join(AREA, "results", "sims_label.jsonl")
sys.path.insert(0, os.path.join(P2, "wp1_offline", "src"))
import p2sim as S  # noqa: E402
import pandas as pd  # noqa: E402

JOBS = json.load(open(os.path.join(P2, "wp1_offline", "jobs.json")))["jobs"]


def r0_thresholds():
    rows = [json.loads(l) for l in open(os.path.join(P2, "wp1_offline", "results", "sims.jsonl")) if l.strip()]
    return {r["instance"]: r["threshold"] for r in rows if r.get("method") == "R0" and r.get("matched")}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", default="deval")
    ap.add_argument("--solvers", nargs="+", required=True)
    ap.add_argument("--budgets", nargs="+", type=float, required=True)
    ap.add_argument("--seed", type=int, default=101)
    ap.add_argument("--workers", type=int, default=6)
    o = ap.parse_args()
    tr = pd.read_csv(os.path.join(AREA, "trials.csv"))
    d = tr[(tr.phase == o.phase) & (tr.status == "ok") & (tr.solver.isin(o.solvers)) & (tr.budget.isin(o.budgets))
           & (tr.seed == o.seed)]
    th = r0_thresholds()
    done = set()
    p = os.environ["P2_SIM_RESULTS"]
    if os.path.exists(p):
        done = {json.loads(l)["exp"] for l in open(p) if l.strip()}
    jobs = []
    for _, r in d.iterrows():
        k = r.instance.replace("full_", "")
        exp = f"lab_{k}_{r.solver}_{r.cfg_hash}_b{r.budget:g}_s{r.seed}_{o.phase}"
        if exp in done or k not in th:
            continue
        J = JOBS[k]
        jobs.append((os.path.join(AREA, r.sol), os.path.join(AREA, "inst", f"full_{k}.npz"), J["region"], J["sample"],
                     J["ea"], round(th[k], 3), exp, dict(instance=k, method=r.solver, budget=float(r.budget),
                                                         seed=int(r.seed), cfg_hash=r.cfg_hash, phase=o.phase,
                                                         objective=float(r.objective))))
    print(len(jobs), "jobs", flush=True)
    with ThreadPoolExecutor(max_workers=o.workers) as ex:
        futs = [ex.submit(S.evaluate, *j) for j in jobs]
        for f in futs:
            try:
                f.result()
            except Exception as e:  # report failures too
                print("FAILED:", repr(e), flush=True)


if __name__ == "__main__":
    main()
