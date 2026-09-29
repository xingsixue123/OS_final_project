"""Held-out simulation loop (Baleen env): simulate the 300 s held-out solutions of the Ising finalists and of the
per-instance best classical method (by mean objective over its seeds, among the classical methods whose 300 s runs are
all complete for that instance), all seeds, once available. Pre-registered in PROGRESS.md (17:00).

  python q2simloop.py --form F1 --ising pt eim --classical greedy pgreedy lp milp cpsat ls [--seeds 0 1 2] [--once]
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
import q2sim as S  # noqa: E402

Q2 = S.Q2
X = S.X


def instance_meta(iname):
    # iname like full_Region7_s0.1
    _, region, ss = iname.split("_")
    start = float(ss[1:])
    z = np.load(os.path.join(X, "common", "inst", f"{iname}.npz"), allow_pickle=False)
    return region, start, float(z["ea"]), os.path.join(X, "common", "inst", f"{iname}.npz")


def simulated():
    p = os.path.join(Q2, "results", "sims.jsonl")
    if not os.path.exists(p):
        return set()
    return {json.loads(l)["sol"] for l in open(p) if l.strip()}


def pending(form, ising, classical, n_seeds_expected, seeds):
    df = pd.read_csv(os.path.join(Q2, "trials.csv"))
    df = df[(df.phase == "heldout") & (df.form == form) & (df.budget == 300) & (df.status == "ok")]
    todo = []
    done = simulated()
    for inst, g in df.groupby("instance"):
        rows = []
        for s in ising:
            rows += [r for _, r in g[g.solver == s].iterrows()]
        cl = g[g.solver.isin(classical)]
        complete = all(len(cl[cl.solver == c]) >= n_seeds_expected.get(c, 1) for c in classical)
        if complete and len(cl):
            best = cl.groupby("solver").objective.mean().idxmin()
            rows += [r for _, r in cl[cl.solver == best].iterrows()]
        for r in rows:
            if int(r.seed) not in seeds or r.sol in done or not isinstance(r.sol, str):
                continue
            todo.append((inst, r.solver, int(r.seed), r.sol, r.cfg_hash))
    return todo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--ising", nargs="+", required=True)
    ap.add_argument("--classical", nargs="+", required=True)
    ap.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    ap.add_argument("--stochastic", nargs="+", default=["ls", "cpsat", "eim", "pt", "hlns", "sb", "mq"])
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--th-hint", type=float, default=28.5)
    o = ap.parse_args()
    nexp = {c: (3 if c in o.stochastic else 1) for c in o.classical}
    inflight = set()
    ex = ThreadPoolExecutor(max_workers=4)
    futs = []
    while True:
        for (inst, solver, seed, sol, h) in pending(o.form, o.ising, o.classical, nexp, set(o.seeds)):
            if sol in inflight:
                continue
            region, start, ea, solved = instance_meta(inst)
            exp = f"ho_{inst}_{o.form}_{solver}_{h}_s{seed}"
            inflight.add(sol)
            futs.append(ex.submit(S.evaluate, os.path.join(Q2, sol), solved, region, start, ea, o.th_hint, exp,
                                  dict(instance=inst, solver=solver, seed=seed, form=o.form, budget=300,
                                       cfg_hash=h)))
            print(f"submitted {exp}", flush=True)
        for f in [f for f in futs if f.done()]:
            try:
                f.result()
            except Exception as e:  # report failures too
                print("FAILED:", repr(e), flush=True)
            futs.remove(f)
        if o.once and not futs:
            break
        time.sleep(60)


if __name__ == "__main__":
    main()
