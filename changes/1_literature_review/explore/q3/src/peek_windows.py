import json, sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.environ["X_ROOT"], "common", "src"))
import xc
H = xc.HARNESS
US = 1.0 / 36 * (100.0 / 0.1) / 600 * 100
off = pd.read_csv(f"{H}/results/offline.csv"); dep = pd.read_csv(f"{H}/results/deployed.csv")
for region in ["Region7", "Region6"]:
    S = {}
    for nm, df in [("optR0", off[(off.region == region) & (off.name == "R0")]), ("optR2", off[(off.region == region) & (off.name == "R2")]),
                   ("depR0", dep[(dep.region == region) & (dep.name == "R0")]), ("depR2", dep[(dep.region == region) & (dep.name == "R2")].iloc[:1])]:
        rf = os.path.join(H, "work", df.iloc[-1].result_file)
        ws = xc.window_series(rf)
        S[nm] = ws["used"] * US
        S["noc"] = ws["nocache"] * US
    m = min(len(v) for v in S.values())
    d = pd.DataFrame({k: v[:m] for k, v in S.items()})
    d = d.iloc[144:]
    print(region, "windows", len(d), "means:", d.mean().round(2).to_dict())
    print(" top-12 windows by depR0 (Baleen online):")
    print(d.sort_values("depR0", ascending=False).head(12).round(2).to_string())
    print(" top-8 by nocache:"); print(d.sort_values("noc", ascending=False).head(8).round(2).to_string())
    print(" corr(noc, depR0)=%.3f  corr(noc, optR0)=%.3f  saved fraction at top-10 depR0 windows: %.3f vs mean %.3f" % (
        np.corrcoef(d.noc, d.depR0)[0, 1], np.corrcoef(d.noc, d.optR0)[0, 1],
        (1 - d.sort_values("depR0", ascending=False).head(10).eval("depR0/noc")).mean(), (1 - d.depR0 / d.noc).mean()))
