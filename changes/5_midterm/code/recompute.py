"""Recompute every derived number on the mid-term slides from raw CSVs in the repo (read-only).

  changes/0_reproduce/env/bin/python -B changes/5_midterm/code/recompute.py > changes/5_midterm/result/recompute_out.txt

Sources: wp1_offline/results/wp1_table.csv (offline OPT), wp3_test/trials.csv (Region6/7 test),
wp9_region5/trials.csv (Region5), wp10_schedule/trials_test.csv (Region1), 3_autoresearch/work/t2u_region4/trials_test.csv
(Region4). Matched rows only; per-instance mean over retrains, then mean over instances (as each RESULTS file does).
"""
import os

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = lambda *a: os.path.join(REPO, "changes", *a)


def arm_mean(path, arm, design="baleen"):
    t = pd.read_csv(path)
    t = t[(t.matched == True) & (t.arm == arm) & (t.design == design)]  # noqa: E712
    return t.groupby("inst").p100.mean().mean()


def pct(new, old):
    return 100.0 * (new - old) / old


wp1 = pd.read_csv(P("2_deployable_peak", "wp1_offline", "results", "wp1_table.csv"))
wp1["sample"] = wp1["sample"].round(1)


def opt(regions, samples, col="R0"):
    x = wp1[wp1.region.isin(regions) & wp1["sample"].isin(samples)]
    return x[col].mean(), len(x)


print("== Slide 3: Baleen's OPT (offline, peak-blind oracle = WP1 column R0)")
for name, (r, s) in {"Region7 s0": (["Region7"], [0.0]), "Region6 s0": (["Region6"], [0.0]),
                     "Region6+7 s0.4-0.6": (["Region6", "Region7"], [0.4, 0.5, 0.6]),
                     "Region5 s0.1-0.6": (["Region5"], [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]),
                     "Region4 s0.2-0.6": (["Region4"], [0.2, 0.3, 0.4, 0.5, 0.6])}.items():
    v, n = opt(r, s)
    print(f"OPT {name}: {v:.2f} (n={n})")

print("\n== Baleen (arm A) deployed means, matched retrains")
A = {"Region6+7 test": arm_mean(P("2_deployable_peak", "wp3_test", "trials.csv"), "A"),
     "Region5": arm_mean(P("2_deployable_peak", "wp9_region5", "trials.csv"), "A"),
     "Region1": arm_mean(P("2_deployable_peak", "wp10_schedule", "trials_test.csv"), "A"),
     "Region4": arm_mean(P("3_autoresearch", "work", "t2u_region4", "trials_test.csv"), "A")}
for k, v in A.items():
    print(f"A {k}: {v:.2f}")

print("\n== Slide 3: gap of Baleen online above its own offline OPT, held-out sets")
for k, (r, s) in {"Region6+7 test": (["Region6", "Region7"], [0.4, 0.5, 0.6]),
                  "Region5": (["Region5"], [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]),
                  "Region4": (["Region4"], [0.2, 0.3, 0.4, 0.5, 0.6])}.items():
    o, _ = opt(r, s)
    print(f"gap {k}: Baleen {A[k]:.2f} vs OPT {o:.2f} -> {100 * (A[k] - o) / A[k]:.1f}%")

print("\n== Slide 6: changes vs Baleen (arm A)")
rows = [("Full design X1 = Ea-1.0:F1PT, Region6+7", P("2_deployable_peak", "wp3_test", "trials.csv"), "Ea-1.0", "F1PT", "Region6+7 test"),
        ("Gate only A+alpha, Region6+7", P("2_deployable_peak", "wp3_test", "trials.csv"), "Aa-1.0", "baleen", "Region6+7 test"),
        ("Gate only A+alpha, Region5", P("2_deployable_peak", "wp9_region5", "trials.csv"), "Aa-1.0", "baleen", "Region5"),
        ("Gate only A+alpha, Region4", P("3_autoresearch", "work", "t2u_region4", "trials_test.csv"), "Aa-1.0", "baleen", "Region4"),
        ("Gate only A+alpha, Region1", P("2_deployable_peak", "wp10_schedule", "trials_test.csv"), "Aa-1.0", "baleen", "Region1")]
for name, path, arm, design, key in rows:
    v = arm_mean(path, arm, design)
    print(f"{name}: {v:.2f} vs Baleen {A[key]:.2f} -> {pct(v, A[key]):+.1f}%")

print("\n== Slide 6: offline teacher, 39 instances (WP1)")
print(f"Baleen OPT mean {wp1.R0.mean():.2f}; min-max PT mean {wp1.pt.mean():.2f}; n={len(wp1)}")
