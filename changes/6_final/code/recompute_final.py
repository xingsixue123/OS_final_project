"""Recompute every number the final deck draws or states, from raw result files in the repo (read-only).

  changes/0_reproduce/env/bin/python -B changes/6_final/code/recompute_final.py > changes/6_final/result/recompute_final_out.txt

Writes changes/6_final/result/numbers.json, which build_deck.py reads for its charts.
Deployed means follow the RESULTS files: matched rows only; per-instance mean over retrains, then mean over instances.
Offline reductions follow wp1_offline/RESULTS.md: mean over samples of the per-sample % reduction against R0.
"""
import json
import os

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = lambda *a: os.path.join(REPO, "changes", *a)  # noqa: E731
OUT = {}

# ---------------- offline (WP1: 39 samples, Regions 4-7) ----------------
w = pd.read_csv(P("2_deployable_peak", "wp1_offline", "results", "wp1_table.csv"))
red = lambda col: 100.0 * (w.R0 - w[col]) / w.R0  # noqa: E731
print("== Slide 8-9: offline, ours vs Baleen's OPT (R0); per-sample % reduction, mean")
off = {}
for col in ("lp", "cpsat", "pt"):
    off[col] = dict(reduction=round(red(col).mean(), 2), wins=int((w[col] < w.R0).sum()), n=len(w))
    print(f"{col}: mean reduction {red(col).mean():.2f}%, wins {int((w[col] < w.R0).sum())}/{len(w)}")
print(f"pt lower than cpsat on {int((w.pt < w.cpsat).sum())}/{len(w)}; lower than lp on {int((w.pt < w.lp).sum())}/{len(w)}")
print(f"mean P100: R0 {w.R0.mean():.2f}, pt {w.pt.mean():.2f}")
regions = []
for reg, g in w.groupby("region"):
    r = 100.0 * (g.R0 - g.pt) / g.R0
    regions.append(dict(region=reg, n=len(g), opt=round(g.R0.mean(), 2), ours=round(g.pt.mean(), 2),
                        reduction=round(r.mean(), 1), wins=int((g.pt < g.R0).sum())))
    print(f"{reg}: n={len(g)} OPT {g.R0.mean():.2f} ours {g.pt.mean():.2f} reduction {r.mean():.1f}% wins {int((g.pt < g.R0).sum())}/{len(g)}")
g = w[w.region != "Region4"]
print(f"Regions 5-7: wins {int((g.pt < g.R0).sum())}/{len(g)}, mean reduction {(100.0 * (g.R0 - g.pt) / g.R0).mean():.1f}%")
OUT["offline"] = dict(solvers=off, regions=regions, pt_below_cpsat=int((w.pt < w.cpsat).sum()), pt_below_lp=int((w.pt < w.lp).sum()))

# ---------------- deployed ----------------
POOLS = {"Region6+7": P("2_deployable_peak", "wp3_test", "trials.csv"),
         "Region5": P("2_deployable_peak", "wp9_region5", "trials.csv"),
         "Region4": P("3_autoresearch", "work", "t2u_region4", "trials_test.csv"),
         "Region1": P("2_deployable_peak", "wp10_schedule", "trials_test.csv")}
ARMS = [("load", "B", "baleen"), ("bar", "Aa-1.0", "baleen"), ("load_bar", "Ba-1.0", "baleen"), ("full", "Ea-1.0", "F1PT")]


def per_inst(path, arm, design, col="p100"):
    t = pd.read_csv(path)
    t = t[(t.matched == True) & (t.arm == arm) & (t.design == design)]  # noqa: E712
    return t.groupby("inst")[col].mean()


print("\n== Slide 10-11: deployed, each configuration vs Baleen (mean P100, % change, samples below Baleen)")
abl = {}
for pool, path in POOLS.items():
    a = per_inst(path, "A", "baleen")
    abl[pool] = {"baleen": round(a.mean(), 2), "n": len(a)}
    print(f"{pool}: Baleen {a.mean():.2f} (n={len(a)})")
    for key, arm, design in ARMS:
        x = per_inst(path, arm, design)
        if x.empty:
            print(f"  {key}: not run")
            continue
        pct = 100 * (x.mean() - a.mean()) / a.mean()
        abl[pool][key] = dict(p100=round(x.mean(), 2), pct=round(pct, 1), wins=int((x < a).sum()))
        print(f"  {key}: {x.mean():.2f}, {pct:+.1f}%, wins {int((x < a).sum())}/{len(a)}")
OUT["ablation"] = abl

print("\n== Slide 10: change vs Baleen per test sample (points of P100)")
samples = []
for pool in ("Region6+7", "Region5"):
    a = per_inst(POOLS[pool], "A", "baleen")
    full = per_inst(POOLS[pool], "Ea-1.0", "F1PT")
    bar = per_inst(POOLS[pool], "Aa-1.0", "baleen")
    for inst in a.index:
        samples.append(dict(inst=inst, d_full=round(full[inst] - a[inst], 2), d_bar=round(bar[inst] - a[inst], 2)))
        print(f"{inst}: full {full[inst] - a[inst]:+.2f}, bar {bar[inst] - a[inst]:+.2f}")
OUT["samples"] = samples

print("\n== Slide 12: the two collapses, peak-window admission and big-offset share (mean over matched retrains)")
col = {}
for pool, inst in (("Region6+7", "Region7_s0.5"), ("Region5", "Region5_s0.5")):
    col[inst] = {}
    for key, arm, design in (("baleen", "A", "baleen"), ("bar", "Aa-1.0", "baleen"), ("full", "Ea-1.0", "F1PT")):
        adm = per_inst(POOLS[pool], arm, design, "peak_adm")[inst]
        big = per_inst(POOLS[pool], arm, design, "peak_bigoff_share")[inst]
        col[inst][key] = dict(adm=round(adm, 2), big=round(big, 2))
        print(f"{inst} {key}: peak-window admission {adm:.2f}, big-offset share {big:.2f}")
OUT["collapse"] = col

print("\n== Backup: Region5 per sample (A, A+alpha, B+alpha)")
r5 = []
for key, arm in (("A", "A"), ("Aa", "Aa-1.0"), ("Ba", "Ba-1.0")):
    x = per_inst(POOLS["Region5"], arm, "baleen")
    r5.append((key, x))
tab = pd.DataFrame({k: v for k, v in r5}).round(2)
tab["gain_Aa"] = (tab.A - tab.Aa).round(2)
print(tab.to_string())
share = tab.loc["Region5_s0.5", "gain_Aa"] / tab.gain_Aa.sum()
print(f"share of the A+alpha gain from s0.5: {100 * share:.0f}%")
OUT["region5"] = dict(rows=tab.reset_index().to_dict(orient="records"), s05_share=round(100 * share))

json.dump(OUT, open(P("6_final", "result", "numbers.json"), "w"), indent=1)
