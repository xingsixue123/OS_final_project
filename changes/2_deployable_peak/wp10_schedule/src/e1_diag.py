"""E1 diagnostic (POST-HOC, not pre-registered, not a usable proxy): P4 = the simulator's OWN day-1 peak, i.e. the max
over windows 0-143 of each WP2 variant sim's per-window used load (same run, same theta as its P100). If even P4 does
not rank variants like P100 (windows >= 144), no training-window replay can. Same C1/C2 code as e1_proxy.evaluate."""
import os, sys
import numpy as np
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402
import e1_proxy as E1  # noqa: E402

t = pd.read_csv(os.path.join(C.WP2, "trials.csv"))
t = t[~t.trial_key.astype(str).str.contains("FAILED") & (t.matched.astype(str) == "True")]
df = pd.read_csv(os.path.join(C.RESULTS, "e1_cells.csv"))
p4 = []
for r in df.itertuples():
    arms = E1.VARIANTS[tuple(r.base.split(":"))][r.variant][0]
    design = r.base.split(":")[1]
    sv = t[(t.arm.isin(arms)) & (t.design == design) & (t.inst == r.inst) & (t.train_key == r.retrain)].iloc[0]
    used = C.window_series(os.path.join(C.WP2, sv.result_file))["used"] * E1.SE.US
    p4.append(float(used[:144].max()))
df["P1"] = p4          # evaluate() scores the column named P1..P3; reuse it for P4 under a separate output
out = df[["inst", "region", "base", "retrain", "variant", "alpha", "sim_p100", "P1"]].rename(columns={"P1": "P4"})
out.to_csv(os.path.join(C.RESULTS, "e1_diag_P4.csv"), index=False)
df["P2"] = df["P1"]; df["P3"] = df["P1"]
import json
E1.C.RESULTS = os.path.join(C.RESULTS, "e1_diag")
os.makedirs(E1.C.RESULTS, exist_ok=True)
E1.evaluate(df)
