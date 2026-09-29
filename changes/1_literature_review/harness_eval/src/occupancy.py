"""Diagnostic: analytic cache occupancy (chunks resident, EA model) per window for an offline run's admitted
set, vs the cache capacity (366.475 GB at 0.1% sampling), and its relation to the sim-vs-analytic residual."""
import json, os, sys
import numpy as np
import pandas as pd
import hecommon as HC
import gate0 as G

def occ(region, name):
    df = pd.DataFrame([json.loads(l) for l in open(os.path.join(HC.RESULTS, "offline.jsonl"))])
    row = df[(df.region == region) & (df.name == name)].iloc[-1]
    D, C, active, ids, z = G.load_inst(os.path.join(HC.WORK, "inst", f"{row.exp}.npz"))
    out = HC.parse_train_outputs(os.path.join(HC.LOGS, row.get("prefix", "off"), row.exp, "train.log"))
    th = G.thresholds(os.path.join(HC.WORK, out["thresholds"][0]))
    x = np.array([th[i] <= float(row.threshold) for i in ids])
    ea = HC.TRACES[region]["ea_opt"]
    t0 = float(z["t0"]); m = len(C)
    s = z["s"]; ts0 = z["ts0"]; te = z["ts_end"]
    o = np.zeros(m + 1)
    a = ((ts0 - t0) // 600).astype(int); b = np.minimum(((te + ea - t0) // 600).astype(int) + 1, m)
    np.add.at(o, a[x], s[x]); np.add.at(o, b[x], -s[x])
    o = np.cumsum(o)[:m]
    ser = np.load(os.path.join(HC.RESULTS, f"gate0_series_{region}_{name}.npz"))
    resid = (ser["sim"] - ser["L"]) * G.US
    return o, resid

cap = 366.475 * 1024 * 0.001 / 0.125   # chunks of 128 KiB at 0.1% sampling
print("cap chunks", cap)
for region in ["Region7", "Region6"]:
    for name in ["R0", "R1_L6"]:
        try:
            o, r = occ(region, name)
        except Exception as ex:
            print(region, name, ex); continue
        act = slice(144, None)
        print(region, name, "occ mean %.0f max %.0f  frac windows > cap %.2f  corr(occ, resid) %.3f" % (
            o[act].mean(), o[act].max(), (o[act] > cap).mean(), np.corrcoef(o[act], r[act])[0, 1]))
