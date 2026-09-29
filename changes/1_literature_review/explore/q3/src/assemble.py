"""Insert generated tables/outputs into q3/RESULTS.md placeholders (run after A2 completes).

  assemble.py   (expects q3/results/q3eval_heldout.md, heldout_mech.csv, final_checks.txt)
Placeholders: HELDOUT_TABLES, HELDOUT_MECHANISM, FINAL_CHECKS (each replaced once; re-running is a no-op).
"""
import os

import pandas as pd

X = os.environ.get("X_ROOT", os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
R = os.path.join(X, "q3", "results")
p = os.path.join(X, "q3", "RESULTS.md")
s = open(p).read()

if "HELDOUT_TABLES" in s:
    s = s.replace("HELDOUT_TABLES", open(os.path.join(R, "q3eval_heldout.md")).read())

if "HELDOUT_MECHANISM" in s:
    d = pd.read_csv(os.path.join(R, "heldout_mech.csv"))
    g = d.groupby(["instance", "config"]).agg(n=("p100", "size"), p100=("p100", "mean"), k0_adm=("k0_adm", "mean"),
                                              mean_load=("mean_used", "mean"), peak_win=("peak_win", lambda v: ",".join(map(str, sorted(set(v))))),
                                              bigoff_share_at_peak=("peak_bigoff_share", "mean"),
                                              admitted_at_peak=("peak_adm", "mean")).reset_index()
    lines = ["*Held-out, post hoc (analysis only; the configurations were frozen before A2): per instance and label set, "
             "mean over matched retrains of the trained admission GBM's first-access admission rate on the whole trace, "
             "the mean post-day-1 load, the simulated peak window(s), the share of big-offset (end > 8 MB) accesses in "
             "that window and the fraction of its accesses the GBM admits (`q3/results/heldout_mech.csv`).*", "",
             "| instance | labels | retrains | P100 | first-access admission | mean load | peak window(s) | "
             "big-offset share there | admitted there |", "|" + "---|" * 9]
    for _, r in g.iterrows():
        lines.append(f"| {r.instance} | {r.config} | {r.n} | {r.p100:.2f} | {r.k0_adm:.3f} | {r.mean_load:.2f} | "
                     f"{r.peak_win} | {r.bigoff_share_at_peak:.2f} | {r.admitted_at_peak:.2f} |")
    s = s.replace("HELDOUT_MECHANISM", "\n".join(lines))

if "FINAL_CHECKS" in s:
    s = s.replace("- FINAL_CHECKS", open(os.path.join(R, "final_checks.txt")).read())

open(p, "w").write(s)
print("assembled; remaining placeholders:", [k for k in ["HELDOUT_TABLES", "HELDOUT_MECHANISM", "FINAL_CHECKS", "TODO"]
                                              if k in s])
