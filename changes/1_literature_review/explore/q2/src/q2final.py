"""Final held-out analysis: Q2 (objective, average, simulation) and Q1 for every Ising finalist.

  python q2final.py --form F1 --ising pt eim [--baselines ../common/baselines.csv]
Writes results/heldout_<form>_objective.csv, results/heldout_<form>_sims.csv and prints markdown tables.
All held-out runs with status ok are used (no seed picking); over-budget flags are reported.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

SRC = os.path.dirname(os.path.abspath(__file__))
Q2 = os.path.dirname(SRC)
X = os.path.dirname(Q2)
FAM = {"greedy": "classical", "pgreedy": "classical", "lp": "classical", "milp": "classical", "ls": "classical",
       "cpsat": "classical", "scip": "classical", "eim": "ising", "pt": "ising", "hlns": "ising", "sb": "ising",
       "mq": "ising"}
INST = [f"full_{r}_s{s}" for r in ("Region7", "Region6") for s in ("0.1", "0.2", "0.3")]


def heldout(form):
    df = pd.read_csv(os.path.join(Q2, "trials.csv"))
    return df[(df.phase == "heldout") & (df.form == form)]


def method_stats(df):
    ok = df[df.status == "ok"]
    g = ok.groupby(["instance", "budget", "solver"])
    st = g.objective.agg(["mean", "std", "count"]).reset_index()
    ob = df.groupby(["instance", "budget", "solver"]).over_budget.sum().reset_index()
    return st.merge(ob, on=["instance", "budget", "solver"], how="left")


def q2(form, ising):
    df = heldout(form)
    st = method_stats(df)
    rows = []
    for (inst, b), g in st.groupby(["instance", "budget"]):
        cl = g[g.solver.map(FAM) == "classical"]
        isi = g[g.solver == ising]
        if cl.empty or isi.empty:
            continue
        best = cl.loc[cl["mean"].idxmin()]
        rows.append(dict(instance=inst, budget=b, ising=isi["mean"].iloc[0],
                         ising_sd=isi["std"].iloc[0] if isi["count"].iloc[0] > 1 else 0.0,
                         ising_n=int(isi["count"].iloc[0]), best_classical=best.solver, classical=best["mean"],
                         classical_sd=best["std"] if best["count"] > 1 else 0.0, classical_n=int(best["count"]),
                         ising_le=bool(isi["mean"].iloc[0] <= best["mean"] * (1 + 1e-9)),   # ties within 1e-9 rel.
                         tie=bool(abs(isi["mean"].iloc[0] - best["mean"]) <= 1e-9 * abs(best["mean"])),
                         gap_pct=100 * (isi["mean"].iloc[0] / best["mean"] - 1),
                         over_budget_runs=int(g.over_budget.sum())))
    return pd.DataFrame(rows), st


def sims(form):
    p = os.path.join(Q2, "results", "sims.jsonl")
    s = pd.DataFrame([json.loads(l) for l in open(p) if l.strip()]) if os.path.exists(p) else pd.DataFrame()
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--ising", nargs="+", required=True)
    ap.add_argument("--baselines", default=None)
    o = ap.parse_args()
    os.makedirs(os.path.join(Q2, "results"), exist_ok=True)
    S = sims(o.form)
    r0 = {}
    if not S.empty and "mode" in S:
        for _, r in S[(S["mode"] == "baleen") & S.matched].iterrows():
            r0[r["instance"]] = r["p100"]
    tb = {}
    bpath = o.baselines or os.path.join(X, "common", "baselines_summary.csv")
    if os.path.exists(bpath):
        b = pd.read_csv(bpath)
        for _, r in b[b.method == "OPT"].iterrows():
            tb["full_" + r.instance] = float(r.p100_mean)
    for ising in o.ising:
        t, st = q2(o.form, ising)
        if t.empty:
            print("no held-out data yet for", ising)
            continue
        t.to_csv(os.path.join(Q2, "results", f"heldout_{o.form}_{ising}_objective.csv"), index=False)
        print(f"\n## Q2 objective: {o.form}, Ising = {ising}\n")
        print("| instance | budget | Ising mean +- sd (n) | best classical | classical mean +- sd (n) | gap % | Ising <= ? |")
        print("|---|---|---|---|---|---|---|")
        for _, r in t.sort_values(["budget", "instance"]).iterrows():
            print(f"| {r.instance} | {int(r.budget)} | {r.ising:.4f} +- {r.ising_sd:.4f} ({r.ising_n}) | {r.best_classical} | "
                  f"{r.classical:.4f} +- {r.classical_sd:.4f} ({r.classical_n}) | {r.gap_pct:+.3f} | "
                  f"{('tie' if r['tie'] else 'yes') if r['ising_le'] else 'no'} |")
        pb = t.groupby("budget").agg(n_le=("ising_le", "sum"), n_tie=("tie", "sum"), n=("ising_le", "size"),
                                     ising=("ising", "mean"), classical=("classical", "mean"))
        pb["obj_ok"] = pb.n_le >= 5
        pb["avg_strict"] = pb.ising < pb.classical * (1 - 1e-9)     # strictly better beyond the tie tolerance
        print("\n", pb.to_string())
        n_ok = int(pb.obj_ok.sum())
        print(f"Objective criterion: budgets with >=5/6 = {n_ok} (need >= 2) -> {'PASS' if n_ok >= 2 else 'FAIL'}")
        print(f"Average criterion (all instance-budgets): Ising {t.ising.mean():.4f} vs classical {t.classical.mean():.4f}"
              f" -> {'PASS' if t.ising.mean() < t.classical.mean() * (1 - 1e-9) else 'FAIL'}")
        # simulation clause and Q1
        if not S.empty and "instance" in S:
            s3 = S[(S.get("form") == o.form) & (S.budget == 300)]
            rows = []
            for inst in INST:
                g = s3[s3.instance == inst]
                gi = g[(g.solver == ising)]
                bc = t[(t.instance == inst) & (t.budget == 300)]
                c = bc.best_classical.iloc[0] if len(bc) else None
                gc = g[g.solver == c] if c else g.iloc[0:0]
                rows.append(dict(instance=inst, ising_p100=gi[gi.matched].p100.mean(), ising_sd=gi[gi.matched].p100.std(),
                                 ising_n=int(gi.matched.sum()), ising_unmatched=int((~gi.matched).sum()),
                                 ising_wr=gi.wr.mean(), classical=c, classical_p100=gc[gc.matched].p100.mean(),
                                 classical_n=int(gc.matched.sum()) if len(gc) else 0,
                                 r0_p100=r0.get(inst, np.nan), trackA_opt_p100=tb.get(inst, np.nan)))
            q = pd.DataFrame(rows)
            q.to_csv(os.path.join(Q2, "results", f"heldout_{o.form}_{ising}_sims.csv"), index=False)
            print(f"\n## Simulated offline P100 (300 s solutions), Ising = {ising}\n")
            print(q.to_string(index=False))
            qq = q.dropna(subset=["ising_p100", "classical_p100"])
            if len(qq):
                print(f"Simulation clause (mean over {len(qq)} instances): Ising {qq.ising_p100.mean():.3f} vs classical "
                      f"{qq.classical_p100.mean():.3f} -> {'PASS' if qq.ising_p100.mean() <= qq.classical_p100.mean() else 'FAIL'}")
            for col, lab in (("trackA_opt_p100", "Track A baselines.csv OPT"), ("r0_p100", "our R0 (same pipeline)")):
                q1 = q.dropna(subset=["ising_p100", col])
                if len(q1):
                    nb = int((q1.ising_p100 < q1[col]).sum())
                    print(f"Q1 vs {lab}: below on {nb}/{len(q1)}; mean {q1.ising_p100.mean():.3f} vs {q1[col].mean():.3f}"
                          f" -> {'PASS' if nb >= 5 and q1.ising_p100.mean() < q1[col].mean() and len(q1) == 6 else 'pending/FAIL'}")
    print("\nTrack A OPT (baselines_summary.csv):", {k: round(v, 3) for k, v in tb.items()})


if __name__ == "__main__":
    main()
