"""WP5 dev evaluation of the tuned configurations (fresh seeds; dev instances only).

  python p2deval.py plan                 -> results/plan_dev.json (best tuning trial per (solver, budget))
  python p2deval.py run [--split default|hl] [--solvers ...] [--budgets ...]

* config per (solver, budget) = the best trial of its tuning study (the same rule for every solver);
* seeds 101, 102, 103 for every stochastic / time-limited solver (pt, eim, sb, mq, ls, cpsat, milp); lp, greedy and
  pgreedy are deterministic (seed 101 only);
* split 'default' = phase-1 nested time split w = (2,1,...,1);
  split 'hl' ("allocate-to-hard-level") = level-1 weight 6, w = (6,1,...,1) -> level 1 gets 6/13 = 46% of T
  (the phase-1 post-hoc sensitivity variant), everything else identical;
* every run on the 8 dev instances in one process (cores 0-7 lock), rows in trials.csv (phase deval / deval_hl).
"""
import argparse
import json
import os
import sys

import optuna

SRC = os.path.dirname(os.path.abspath(__file__))
AREA = os.path.dirname(SRC)
sys.path.insert(0, SRC)
import p2tune as T  # noqa: E402

PLAN = os.path.join(AREA, "results", "plan_dev.json")
SOLVERS = T.ISING + T.CLASSICAL
BUDGETS = [1, 3, 10]
SEEDS = [101, 102, 103]
DETERMINISTIC = {"lp", "greedy", "pgreedy"}
HL = [6.0] + [1.0] * 7


def make_plan():
    plan = {"solvers": {}, "note": "best tuning trial per (solver, budget); built by p2deval.py plan"}
    for sv in SOLVERS:
        plan["solvers"][sv] = {}
        for b in BUDGETS:
            try:
                st = optuna.load_study(study_name=f"F1__{sv}__b{b:g}", storage=T.DB)
            except KeyError:
                continue
            comp = [t for t in st.trials if t.state == optuna.trial.TrialState.COMPLETE]
            if len(comp) < 12:                       # study not finished: no plan entry yet
                continue
            bt = min(comp, key=lambda t: t.value)
            plan["solvers"][sv][str(b)] = dict(cfg=json.loads(bt.user_attrs["cfg"]), trial=bt.number,
                                               value=bt.value, n_trials=len(comp),
                                               per_inst=bt.user_attrs.get("per_inst"))
    plan["solvers"]["greedy"] = {str(b): dict(cfg={}, trial=None, value=None, n_trials=0) for b in BUDGETS}
    plan["solvers"]["pgreedy"] = {str(b): dict(cfg={}, trial=None, value=None, n_trials=0) for b in BUDGETS}
    json.dump(plan, open(PLAN, "w"), indent=1)
    for sv, d in plan["solvers"].items():
        print(sv, {b: (x["trial"], None if x["value"] is None else round(x["value"], 5)) for b, x in d.items()})


def run(split, solvers, budgets, seeds):
    plan = json.load(open(PLAN))["solvers"]
    phase = "deval" if split == "default" else "deval_hl"
    for b in budgets:
        for sv in solvers:
            cfg = dict(plan[sv][f"{b:g}"]["cfg"])
            if split == "hl":
                cfg["level_weights"] = HL
            for sd in (seeds[:1] if sv in DETERMINISTIC else seeds):
                res = T.run_cfg(T.DEV, sv, b, cfg, sd, phase, f"{phase}_{sv}_b{b:g}_s{sd}",
                                sols=os.path.join(AREA, "sols"))
                vals = {k: round(v["objective"], 4) for k, v in res.items()}
                print(f"[{phase}] {sv} b={b} s={sd}: {vals}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["plan", "run"])
    ap.add_argument("--split", default="default", choices=["default", "hl"])
    ap.add_argument("--solvers", default=",".join(SOLVERS + ["greedy", "pgreedy"]))
    ap.add_argument("--budgets", default="1,3,10")
    o = ap.parse_args()
    if o.what == "plan":
        make_plan()
    else:
        run(o.split, o.solvers.split(","), [float(x) for x in o.budgets.split(",")], SEEDS)


if __name__ == "__main__":
    main()
