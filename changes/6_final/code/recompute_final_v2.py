"""Recompute the numbers of the v2 final deck (online results with Ising labels), from raw ledgers in the repo (read-only).

  changes/0_reproduce/env/bin/python -B changes/6_final/code/recompute_final_v2.py > changes/6_final/result/recompute_final_v2_out.txt

Writes changes/6_final/result/numbers_v2.json (read by build_deck_v2.py). Offline numbers come from numbers.json
(recompute_final.py). Means: matched rows only; per-instance mean over retrains, then mean over instances.
"""
import json
import os

import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = lambda *a: os.path.join(REPO, "changes", *a)  # noqa: E731
OUT = {}


def per_inst(df, arms, design, col="p100"):
    t = df[(df.matched == True) & (df.arm.isin(arms)) & (df.design == design)]  # noqa: E712
    return t.groupby("inst")[col].mean()


def pct(x, a):
    return 100.0 * (x - a) / a


# ---------------- dev: Ising labels + load + adaptive bar (WP2, Region6/7 s0-0.3) ----------------
w2 = pd.read_csv(P("2_deployable_peak", "wp2_deployed", "trials.csv"))
A = per_inst(w2, ["A"], "baleen")
X1 = per_inst(w2, ["Ea-1.0"], "F1PT")
Aa = per_inst(w2, ["Aa-1.0", "Ax-1.0"], "baleen")
D = per_inst(w2, ["D"], "F1PT")
print("== Slide 10: dev, Ising labels + load feature + adaptive bar (X1) vs Baleen (A)")
dev = {}
for name, idx in (("all", A.index), ("Region6", [i for i in A.index if i.startswith("Region6")]),
                  ("Region7", [i for i in A.index if i.startswith("Region7")])):
    a, x = A[idx], X1[idx]
    dev[name] = dict(baleen=round(a.mean(), 2), ising=round(x.mean(), 2), pct=round(pct(x.mean(), a.mean()), 1),
                     wins=int((x < a).sum()), n=len(idx))
    print(f"{name}: Baleen {a.mean():.2f}, Ising labels {x.mean():.2f} ({pct(x.mean(), a.mean()):+.1f}%), wins {int((x < a).sum())}/{len(idx)}")
r6 = w2[(w2.matched == True) & w2.inst.str.startswith("Region6")]  # noqa: E712
mech = {}
for key, arms, design in (("baleen", ["A"], "baleen"), ("ising", ["Ea-1.0"], "F1PT")):
    t = r6[r6.arm.isin(arms) & (r6.design == design)]
    mech[key] = dict(peak_adm=round(t.peak_adm.mean(), 2), scan_peaks=int((t.peak_bigoff_share > 0.25).sum()), n=len(t))
    print(f"Region6 {key}: peak-window admission {t.peak_adm.mean():.2f}; peak on a scan in {int((t.peak_bigoff_share > 0.25).sum())}/{len(t)} retrains")
gi, ga = X1 - D, Aa - A
print(f"adaptive bar gain on Ising labels: {-gi.mean():+.2f} ({int((gi < 0).sum())}/{len(gi)}); on Baleen labels: {-ga.mean():+.2f} ({int((ga < 0).sum())}/{len(ga)})")
OUT["dev_x1"] = dict(dev=dev, mech=mech, bar_on_ising=round(-gi.mean(), 2), bar_on_ising_wins=int((gi < 0).sum()),
                     bar_on_baleen=round(-ga.mean(), 2))

# ---------------- dev: PeakBaleen (Baleen model OR Ising peak model, + adaptive bar) ----------------
un = pd.read_csv(P("3_autoresearch", "work", "union", "trials_dev.csv"))
fin = json.load(open(P("3_autoresearch", "work", "union", "results", "dev_finalist.json")))
row = [r for r in fin["rule"] if r["cfg"] == "XA-F1PT"][0]
XA = per_inst(un, ["XA-F1PT"], "baleen")
XC = per_inst(un, ["XA-F1CPSAT"], "baleen")
print("\n== Slide 11: dev, PeakBaleen (union) on 10 dev samples")
u = dict(peak=round(XA.mean(), 2), n=len(XA), cpsat=round(XC.mean(), 2), cpsat_wins=int((XA < XC).sum()),
         baleen=round(XA.mean() + row["A_mean"], 2), baleen_wins=row["A_wins"],
         bar=round(XA.mean() + row["A+a_mean"], 2), bar_wins=row["A+a_wins"],
         load=round(XA.mean() + row["B_mean"], 2), load_wins=row["B_wins"])
u["pct_baleen"] = round(pct(u["peak"], u["baleen"]), 1)
print(f"PeakBaleen {XA.mean():.2f} (n={len(XA)}); Baleen {u['baleen']:.2f} ({u['pct_baleen']:+.1f}%), wins {u['baleen_wins']}/10; "
      f"Baleen + adaptive bar {u['bar']:.2f}, wins {u['bar_wins']}/10; Baleen + load {u['load']:.2f}, wins {u['load_wins']}/10")
print(f"same design with CP-SAT labels {XC.mean():.2f}; Ising-label version lower on {u['cpsat_wins']}/10")
OUT["dev_union"] = u

# ---------------- fresh cluster tests ----------------
t2 = pd.read_csv(P("3_autoresearch", "work", "t2u_region4", "trials_test.csv"))
a4, b4 = per_inst(t2, ["A"], "baleen"), per_inst(t2, ["B"], "baleen")
y4, c4 = per_inst(t2, ["XA-F1PT"], "baleen"), per_inst(t2, ["XA-F1CPSAT"], "baleen")
r4 = dict(baleen=round(a4.mean(), 2), load=round(b4.mean(), 2), peak=round(y4.mean(), 2), cpsat=round(c4.mean(), 2),
          pct_baleen=round(pct(y4.mean(), a4.mean()), 1), pct_load=round(pct(y4.mean(), b4.mean()), 1),
          wins_baleen=int((y4 < a4).sum()), wins_load=int((y4 < b4).sum()), n=len(a4))
print("\n== Slide 12: Region4 (never run before)")
print(f"Baleen {a4.mean():.2f}, Baleen + load {b4.mean():.2f}, PeakBaleen {y4.mean():.2f} ({r4['pct_baleen']:+.1f}% vs Baleen, "
      f"wins {r4['wins_baleen']}/{len(a4)}; {r4['pct_load']:+.1f}% vs Baleen + load, wins {r4['wins_load']}/{len(a4)}); CP-SAT labels {c4.mean():.2f}")
w9 = pd.read_csv(P("2_deployable_peak", "wp9_region5", "trials.csv"))
a5 = per_inst(w9, ["A"], "baleen")
r5 = {"baleen": round(a5.mean(), 2), "n": len(a5)}
for key, arm in (("bar", "Aa-1.0"), ("load_bar", "Ba-1.0")):
    x = per_inst(w9, [arm], "baleen")
    r5[key] = dict(p100=round(x.mean(), 2), pct=round(pct(x.mean(), a5.mean()), 1), wins=int((x < a5).sum()))
print(f"Region5 (pre-registered): Baleen {a5.mean():.2f}; load-aware bar {r5['bar']}; + load feature {r5['load_bar']}")
OUT["region4"], OUT["region5"] = r4, r5

json.dump(OUT, open(P("6_final", "result", "numbers_v2.json"), "w"), indent=1)
