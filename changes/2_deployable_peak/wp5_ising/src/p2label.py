"""Label-solver evidence table (dev only): OPT-mode simulated P100 of the dev full-trace selections (8 dev instances)
for the candidate configurations + the day-1 (label-size) solve quality vs budget.  Solver env.
Sources: results/sims_label.jsonl (WP5 deval seed-101 selections), wp1_offline/results/sims.jsonl (R0 and the phase-1
frozen PT/CP-SAT/LP 300-s selections on the same dev instances), trials.csv phase label_day1."""
import json
import os

import numpy as np
import pandas as pd

AREA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P2 = os.path.dirname(AREA)
DEV = [f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]


def main():
    lab = pd.DataFrame([json.loads(l) for l in open(os.path.join(AREA, "results", "sims_label.jsonl")) if l.strip()]) \
        if os.path.exists(os.path.join(AREA, "results", "sims_label.jsonl")) else pd.DataFrame()
    w1 = pd.DataFrame([json.loads(l) for l in open(os.path.join(P2, "wp1_offline", "results", "sims.jsonl"))])
    w1 = w1[w1.instance.isin(DEV)]
    rows = []
    r0 = w1[w1.method == "R0"].set_index("instance").p100
    for m in ("pt", "cpsat", "lp"):
        x = w1[(w1.method == m) & ~w1.exp.str.contains("_s0_rerun") | (w1.method == m)]
        x = x.drop_duplicates("instance", keep="last").set_index("instance")
        rows.append(dict(config=f"{m} 300 s (phase-1 frozen, WP1 run)", **{k: x.p100.get(k, np.nan) for k in DEV},
                         matched=int(x.matched.sum())))
    ph1 = "/home/sxing/project/OS_final_project/changes/1_literature_review/explore/q2/results/sims.jsonl"
    P1 = pd.DataFrame([json.loads(l) for l in open(ph1) if l.strip()])
    P1 = P1[P1.get("budget", pd.Series(dtype=float)).eq(300) & P1.solver.isin(["eim", "pt"]) & P1.matched]
    for m, g in P1.groupby("solver"):
        g = g.assign(inst=g.instance.str.replace("full_", "")).groupby("inst").p100.mean()
        rows.append(dict(config=f"{m} 300 s (phase-1 held-out sims, mean of 3 seeds; s0.1-0.3 only)",
                         **{k: g.get(k, np.nan) for k in DEV}, matched=int(len(g))))
    if len(lab):
        for (m, b), g in lab.groupby(["method", "budget"]):
            g = g.drop_duplicates("instance", keep="last").set_index("instance")
            rows.append(dict(config=f"{m} {b:g} s (WP5 tuned, deval seed 101)", **{k: g.p100.get(k, np.nan) for k in DEV},
                             matched=int(g.matched.sum())))
    rows.append(dict(config="R0 (Baleen peak-blind OPT)", **{k: r0.get(k, np.nan) for k in DEV}, matched=len(r0)))
    T = pd.DataFrame(rows)
    T["mean"] = T[DEV].mean(axis=1)
    T["n"] = T[DEV].notna().sum(axis=1)
    T["red_vs_R0_%"] = [(100 * (1 - np.nanmean(r[DEV].values.astype(float) / r0[DEV].values))) for _, r in T.iterrows()]
    T = T.sort_values("mean")
    out = ["| configuration | " + " | ".join(k.replace("Region", "R") for k in DEV) + " | mean | reduction vs R0 | matched |",
           "|---|" + "---|" * (len(DEV) + 3)]
    for _, r in T.iterrows():
        out.append(f"| {r.config} | " + " | ".join("-" if pd.isna(r[k]) else f"{r[k]:.2f}" for k in DEV) +
                   f" | {r['mean']:.3f} (n={r.n}) | {r['red_vs_R0_%']:.1f}% | {r.matched} |")
    tr = pd.read_csv(os.path.join(AREA, "trials.csv"))
    d = tr[(tr.phase == "label_day1") & (tr.status == "ok")]
    out2 = []
    if len(d):
        g = d.groupby(["solver", "budget"]).agg(obj=("objective", "mean"), peak=("peak_W_util", "mean"),
                                                wall=("wall", "max"), over=("over_budget", "sum"), n=("objective", "size"))
        out2 = ["| solver | budget | day-1 nested objective (mean of 8) | day-1 peak at f=1 | max wall s | over budget |",
                "|---|---|---|---|---|---|"]
        for (sv, b), x in g.iterrows():
            out2.append(f"| {sv} | {b:g} | {x.obj:.4f} | {x.peak:.4f} | {x.wall:.2f} | {int(x.over)} |")
    md = "\n".join(out) + "\n\nDay-1 (label-size) instances, dev Region7/6 s0-0.3 (n = 8.3k-12.3k episodes):\n\n" + "\n".join(out2)
    open(os.path.join(AREA, "results", "label_evidence.md"), "w").write(md + "\n")
    print(md)


if __name__ == "__main__":
    main()
