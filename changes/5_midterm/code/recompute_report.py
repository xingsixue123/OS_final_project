"""Recompute the numbers used only in the mid-term report (read-only). Slide numbers: see recompute.py.

  changes/0_reproduce/env/bin/python -B changes/5_midterm/code/recompute_report.py > changes/5_midterm/result/recompute_report_out.txt

Same rule as recompute.py: matched rows only; per-instance mean over retrains, then mean over instances.
Also writes changes/5_midterm/report/figures/fig2_data.csv, which the per-sample figure reads.
"""
import os

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = lambda *a: os.path.join(REPO, "changes", *a)

POOLS = {"Region6+7": P("2_deployable_peak", "wp3_test", "trials.csv"),
         "Region5": P("2_deployable_peak", "wp9_region5", "trials.csv"),
         "Region4": P("3_autoresearch", "work", "t2u_region4", "trials_test.csv"),
         "Region1": P("2_deployable_peak", "wp10_schedule", "trials_test.csv")}
ARMS = [("Baleen + load feature", "B", "baleen"),
        ("Baleen + adaptive bar", "Aa-1.0", "baleen"),
        ("Baleen + load feature + adaptive bar", "Ba-1.0", "baleen"),
        ("Full PeakBaleen", "Ea-1.0", "F1PT")]


def per_inst(path, arm, design, col="p100"):
    t = pd.read_csv(path)
    t = t[(t.matched == True) & (t.arm == arm) & (t.design == design)]  # noqa: E712
    return t.groupby("inst")[col].mean()


print("== Report Table 3: each arm vs Baleen (mean P100, % change, instances below Baleen)")
for pool, path in POOLS.items():
    a = per_inst(path, "A", "baleen")
    print(f"{pool}: Baleen {a.mean():.2f} (n={len(a)})")
    for name, arm, design in ARMS:
        x = per_inst(path, arm, design)
        if x.empty:
            print(f"  {name}: not run")
            continue
        wins = int((x < a).sum())
        print(f"  {name}: {x.mean():.2f}, {100 * (x.mean() - a.mean()) / a.mean():+.1f}%, wins {wins}/{len(a)}")

print("\n== Report Figure 2: change vs Baleen per test sample (points of P100)")
rows = []
for pool in ("Region6+7", "Region5"):
    a = per_inst(POOLS[pool], "A", "baleen")
    full = per_inst(POOLS[pool], "Ea-1.0", "F1PT")
    bar = per_inst(POOLS[pool], "Aa-1.0", "baleen")
    for inst in a.index:
        rows.append(dict(inst=inst, baleen=a[inst], full=full[inst], bar=bar[inst],
                         d_full=full[inst] - a[inst], d_bar=bar[inst] - a[inst]))
fig = pd.DataFrame(rows)
print(fig.round(2).to_string(index=False))
fig.round(4).to_csv(P("5_midterm", "report", "figures", "fig2_data.csv"), index=False)

print("\n== Report 5.4: the two collapses, peak-window behaviour (mean over matched retrains)")
for pool, inst in (("Region6+7", "Region7_s0.5"), ("Region5", "Region5_s0.5")):
    for label, arm, design in (("Baleen", "A", "baleen"), ("Baleen + adaptive bar", "Aa-1.0", "baleen"),
                               ("Full PeakBaleen", "Ea-1.0", "F1PT")):
        adm = per_inst(POOLS[pool], arm, design, "peak_adm")[inst]
        big = per_inst(POOLS[pool], arm, design, "peak_bigoff_share")[inst]
        print(f"{inst} {label}: peak-window admission {adm:.2f}, big-offset share {big:.2f}")
