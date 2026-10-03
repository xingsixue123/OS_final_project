"""Q2 / Q1 verdicts from trials.csv (phase=heldout) and results/sims.jsonl.

Q2 per PROTOCOL.md: for the Ising configuration (solver+cfg per budget) vs the best classical method per (instance,
budget) (best = lowest mean objective over its seeds; deterministic methods have one run):
  Objective: Ising mean <= best classical mean on >= 5 of 6 instances, at >= 2 of 3 budgets.
  Average  : strictly better on average (mean over instances; reported per budget and over all 18 instance-budgets).
  Simulation: mean simulated P100 of the Ising solutions <= that of the classical solutions (mean over instances).
Every run is included (no seed picking); over-budget runs are flagged and counted as they are (their result is the one
available at the level deadlines -- q2lp discards MILP solutions returned after a deadline).
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

SRC = os.path.dirname(os.path.abspath(__file__))
Q2 = os.path.dirname(SRC)


def load(phase="heldout", form=None):
    df = pd.read_csv(os.path.join(Q2, "trials.csv"))
    df = df[df.phase == phase]
    if form:
        df = df[df.form == form]
    return df


def q2_table(df, ising_solver, ising_hashes=None):
    """per (instance, budget): Ising mean/sd, best classical method + mean, all method means."""
    rows = []
    for (inst, b), g in df.groupby(["instance", "budget"]):
        means = g[g.status == "ok"].groupby(["solver", "cfg_hash"]).objective.agg(["mean", "std", "count"])
        cls = means[[FAM.get(s, "?") == "classical" for s, _ in means.index]]
        isi = means.loc[[i for i in means.index if i[0] == ising_solver and
                         (ising_hashes is None or i[1] in ising_hashes)]]
        if len(isi) == 0 or len(cls) == 0:
            continue
        bc = cls["mean"].idxmin()
        r = dict(instance=inst, budget=b, ising=float(isi["mean"].iloc[0]), ising_sd=float(isi["std"].iloc[0] or 0),
                 ising_n=int(isi["count"].iloc[0]), best_classical=bc[0], classical=float(cls.loc[bc, "mean"]),
                 classical_sd=float(cls.loc[bc, "std"]) if not np.isnan(cls.loc[bc, "std"]) else 0.0,
                 over_budget=int(g.over_budget.sum()))
        for (s, h), v in means["mean"].items():
            r[f"m_{s}"] = float(v)
        r["ising_le"] = r["ising"] <= r["classical"] + 1e-12
        r["rel_gap"] = r["ising"] / r["classical"] - 1
        rows.append(r)
    return pd.DataFrame(rows)


FAM = {"greedy": "classical", "pgreedy": "classical", "lp": "classical", "milp": "classical", "ls": "classical",
       "cpsat": "classical", "scip": "classical", "eim": "ising", "pt": "ising", "hlns": "ising", "sb": "ising",
       "mq": "ising"}


def q2_verdict(t):
    per_b = t.groupby("budget").agg(n_le=("ising_le", "sum"), n=("ising_le", "size"), ising=("ising", "mean"),
                                    classical=("classical", "mean"))
    per_b["objective_ok"] = per_b.n_le >= 5
    per_b["avg_better"] = per_b.ising < per_b.classical
    n_budgets_ok = int(per_b.objective_ok.sum())
    overall_avg = bool(t.ising.mean() < t.classical.mean())
    return per_b, n_budgets_ok >= 2, overall_avg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--ising", required=True, nargs="+")
    o = ap.parse_args()
    df = load(form=o.form)
    for isolver in o.ising:
        t = q2_table(df, isolver)
        if t.empty:
            print("no data for", isolver)
            continue
        pd.set_option("display.width", 250)
        print(f"\n=== Q2 table: Ising={isolver} vs best classical ({o.form}) ===")
        cols = ["instance", "budget", "ising", "ising_sd", "ising_n", "best_classical", "classical", "classical_sd",
                "rel_gap", "ising_le", "over_budget"]
        print(t[cols].sort_values(["budget", "instance"]).to_string(index=False))
        per_b, obj_ok, avg_ok = q2_verdict(t)
        print(per_b.to_string())
        print(f"Objective criterion (>=5/6 at >=2 budgets): {obj_ok};  overall average strictly better: {avg_ok}")


if __name__ == "__main__":
    main()


# ------------------------------------------------------------------ simulations (Q1 and the Q2 simulation clause)
def load_sims():
    p = os.path.join(Q2, "results", "sims.jsonl")
    rows = [json.loads(l) for l in open(p) if l.strip()] if os.path.exists(p) else []
    return pd.DataFrame(rows)


def sim_tables(form, ising, q2t, baselines=None):
    """q2t: q2_table output (to know the best classical method per instance at 300 s)."""
    s = load_sims()
    if s.empty or "instance" not in s:
        return None
    s = s[(s.get("form") == form) & (s.budget == 300)]
    out = []
    for inst, g in s.groupby("instance"):
        r = dict(instance=inst)
        gi = g[(g.solver == ising) & g.matched]
        r["ising_p100"] = gi.p100.mean() if len(gi) else np.nan
        r["ising_p100_sd"] = gi.p100.std() if len(gi) > 1 else 0.0
        r["ising_n"] = len(gi)
        r["ising_unmatched"] = int(((g.solver == ising) & ~g.matched).sum())
        bc = q2t[(q2t.instance == inst) & (q2t.budget == 300)]
        if len(bc):
            c = bc.best_classical.iloc[0]
            gc = g[(g.solver == c) & g.matched]
            r.update(best_classical=c, classical_p100=gc.p100.mean() if len(gc) else np.nan, classical_n=len(gc))
        if baselines is not None and inst in baselines:
            r["baleen_opt_p100"] = baselines[inst]
        out.append(r)
    return pd.DataFrame(out)
