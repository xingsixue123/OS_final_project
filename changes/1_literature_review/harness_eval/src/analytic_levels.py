"""Per-level analytic results (solver JSONs of the offline o11 runs) -> results/analytic_levels.csv and a
summary (mean analytic peak over levels, C1 sub-solver wins, C5 per-QUBO-solver peaks)."""
import glob, json, os
import numpy as np
import pandas as pd
import hecommon as HC

rows = []
for p in sorted(glob.glob(os.path.join(HC.WORK, "inst", "o11_*_sol.json"))):
    s = json.load(open(p))
    exp = os.path.basename(p)[:-9]
    _, region, name = exp.split("_", 2)
    for lv in s["per_level"]:
        r = dict(region=region, name=name, cand=s["cand"], level=lv["level"], peak_util=lv["peak_util"],
                 top5=lv["top5"], sts=lv["sts"], secs=lv["secs"])
        for k, v in lv.items():
            if k.startswith(("lns_", "c5_", "eim_", "sb_", "milp_", "z_lp", "peak_r1", "ls_")) and np.isscalar(v):
                r[k] = v
        rows.append(r)
df = pd.DataFrame(rows)
df.to_csv(os.path.join(HC.RESULTS, "analytic_levels.csv"), index=False)
US = 4.62962962962963
df["peak_r1_util"] = df.get("peak_r1") * US
summ = df.groupby(["region", "name"]).agg(mean_peak=("peak_util", "mean"), peak_075=("peak_util", lambda x: float(x.iloc[5])),
                                         peak_085=("peak_util", lambda x: float(x.iloc[7])), secs=("secs", "sum"),
                                         mean_sts=("sts", "mean")).round(3)
print(summ.to_string())
c1 = df[df.cand == "C1"].groupby("region")[["lns_wins_milp", "lns_wins_sa", "lns_wins_qubo", "lns_iters"]].sum()
print("\nC1 accepted-move wins by sub-solver:\n", c1.to_string())
c5 = df[df.cand == "C5"]
cols = [c for c in c5.columns if c.startswith("c5_peak_")]
print("\nC5 per-solver analytic peak (mean over levels, util %):\n", c5.groupby("region")[cols].mean().round(3).T.to_string())
imp = df[df.cand.isin(["R2", "R3", "C2", "C4"])].copy()
imp["improved_over_r1"] = imp["peak_util"] < imp["peak_r1_util"] - 1e-9
print("\nlevels where the arm improved on its repaired-LP start:\n", imp.groupby(["region", "name"]).improved_over_r1.sum().to_string())
