"""Build the held-out plan from the dev tuning (Optuna DB): config per budget = best trial of the budget's study
(10 s -> b10 study; 60 s and 300 s -> b60 study, falling back to b10). Seeds: stochastic methods 3, deterministic 1.

  python q2plan.py --form '{"name":"F2b","tau_rel":0.6}' --ising eim --out plan_F2b.json
"""
import argparse
import json
import os

import optuna

SRC = os.path.dirname(os.path.abspath(__file__))
Q2 = os.path.dirname(SRC)
X = os.path.dirname(Q2)
DB = "sqlite:///" + os.path.join(Q2, "optuna.db")
HELDOUT = [os.path.join(X, "common", "inst", f"full_{r}_s{s}.npz") for r in ("Region7", "Region6")
           for s in ("0.1", "0.2", "0.3")]
STOCHASTIC = {"ls", "cpsat", "eim", "pt", "hlns", "sb", "mq"}
CLASSICAL = ["greedy", "pgreedy", "lp", "milp", "cpsat", "scip", "ls"]


def best_cfg(fname, solver, b):
    try:
        st = optuna.load_study(study_name=f"{fname}__{solver}__b{b}", storage=DB)
        return json.loads(st.best_trial.user_attrs["cfg"]), st.best_trial.value, len(st.trials)
    except KeyError:
        return None, None, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--ising", required=True, nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--budgets", default="10,60,300")
    ap.add_argument("--no-scip", action="store_true")
    o = ap.parse_args()
    form = json.loads(o.form)
    fname = form["name"] + "".join(f"_{k}{v}" for k, v in sorted(form.items()) if k != "name")
    budgets = [int(b) for b in o.budgets.split(",")]
    methods = []
    for solver in CLASSICAL + list(o.ising):
        if solver == "scip" and o.no_scip:
            continue
        cfgs = {}
        src = {}
        for b in budgets:
            if solver in ("greedy", "pgreedy"):
                cfgs[str(b)], src[str(b)] = {}, "none (no hyperparameters)"
                continue
            c60, v60, n60 = best_cfg(fname, solver, 60)
            c10, v10, n10 = best_cfg(fname, solver, 10)
            if b == 10 or c60 is None:
                cfgs[str(b)], src[str(b)] = c10, f"b10 best ({n10} trials, value {v10})"
            else:
                cfgs[str(b)], src[str(b)] = c60, f"b60 best ({n60} trials, value {v60})"
            assert cfgs[str(b)] is not None, (solver, b)
        methods.append(dict(solver=solver, cfg_by_budget=cfgs, cfg_source=src,
                            seeds=[0, 1, 2] if solver in STOCHASTIC else [0]))
    plan = dict(form=form, instances=HELDOUT, budgets=budgets, methods=methods)
    json.dump(plan, open(o.out, "w"), indent=1)
    for m in methods:
        print(m["solver"], m["seeds"], m["cfg_source"])


if __name__ == "__main__":
    main()
