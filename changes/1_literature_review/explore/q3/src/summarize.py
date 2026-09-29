"""Summaries of q3/trials.csv (all rows, no filtering except the matched flag, which is reported)."""
import json
import os
import sys

import numpy as np
import pandas as pd

X = os.environ.get("X_ROOT", os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
# dev references: 0_reproduce Baleen online (9 retrains), static baselines (bit-exact replays)
DEV_REF = {"Region7_s0": dict(baleen=(40.10, 0.18, 9), rejectx=42.455, coinflip=48.961),
           "Region6_s0": dict(baleen=(43.25, 0.04, 9), rejectx=42.321, coinflip=43.445)}


def load():
    p = os.path.join(X, "q3", "trials.csv")
    return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame()


def table(df, stage=None):
    if stage:
        df = df[df.stage == stage]
    rows = []
    for (cfg, inst), d in df.groupby(["config", "instance"], sort=False):
        ref = DEV_REF.get(inst, {})
        r = dict(config=cfg, instance=inst, n=len(d), n_matched=int(d.matched.sum()), p100_mean=d.p100.mean(),
                 p100_sd=d.p100.std(ddof=1) if len(d) > 1 else np.nan, per_rep=", ".join(f"{v:.2f}" for v in d.p100),
                 top5=d.top5.mean(), mean_dt=d.mean_dt.mean(), wr=", ".join(f"{v:.2f}" for v in d.wr),
                 J=d.jaccard_vs_baleen.mean(), label_peak=d.label_peak_day1.mean(), argmax=",".join(map(str, d.argmax)))
        if ref:
            r["vs_baleen_ref"] = r["p100_mean"] - ref["baleen"][0]
            r["vs_rejectx"] = r["p100_mean"] - ref["rejectx"]
        rows.append(r)
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load()
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_colwidth", 40)
    t = table(df, sys.argv[1] if len(sys.argv) > 1 else None)
    print(t.round(3).to_string(index=False))
