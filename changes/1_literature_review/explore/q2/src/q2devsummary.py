"""Dev summary: per (formulation, solver, budget) study -> #trials, best value, per-instance objectives of the best
trial; plus counts of every logged dev trial. Writes results/dev_summary.csv and prints markdown."""
import json
import os

import optuna
import pandas as pd

SRC = os.path.dirname(os.path.abspath(__file__))
Q2 = os.path.dirname(SRC)
DB = "sqlite:///" + os.path.join(Q2, "optuna.db")
FAM = {"greedy": "classical", "pgreedy": "classical", "lp": "classical", "milp": "classical", "ls": "classical",
       "cpsat": "classical", "scip": "classical", "eim": "ising", "pt": "ising", "hlns": "ising", "sb": "ising",
       "mq": "ising"}

optuna.logging.set_verbosity(optuna.logging.WARNING)
rows = []
for s in optuna.get_all_study_summaries(storage=DB):
    name = s.study_name
    form, solver, b = name.split("__")
    st = optuna.load_study(study_name=name, storage=DB)
    comp = [t for t in st.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if not comp:
        continue
    bt = min(comp, key=lambda t: t.value)
    per = bt.user_attrs.get("per_inst", [None, None])
    rows.append(dict(form=form, solver=solver, family=FAM[solver], budget=int(b[1:]), n_trials=len(comp),
                     best_value_pct=100 * bt.value, R7_pct=100 * per[0], R6_pct=100 * per[1], best_trial=bt.number,
                     cfg=bt.user_attrs.get("cfg")))
df = pd.DataFrame(rows).sort_values(["form", "budget", "best_value_pct"])
os.makedirs(os.path.join(Q2, "results"), exist_ok=True)
df.to_csv(os.path.join(Q2, "results", "dev_summary.csv"), index=False)
for (f, b), g in df.groupby(["form", "budget"]):
    print(f"\n### {f}, {b} s (value = mean over dev of objective / peak-aware greedy - 1, in %)\n")
    print("| solver | family | trials | value % | Region7 % | Region6 % |\n|---|---|---|---|---|---|")
    for _, r in g.iterrows():
        print(f"| {r.solver} | {r.family} | {r.n_trials} | {r.best_value_pct:+.3f} | {r.R7_pct:+.3f} | {r.R6_pct:+.3f} |")
tr = pd.read_csv(os.path.join(Q2, "trials.csv"))
print("\ntrials.csv rows by phase/status:\n", tr.groupby(["phase", "status"]).size().to_string())
