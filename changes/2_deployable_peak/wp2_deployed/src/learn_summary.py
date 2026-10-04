"""Learnability gate summary (criterion fixed before reading the results, PROGRESS.md 2026-10-01):
for label set L and instance i (block split, validation part):
  gain_load  = val_logloss(orig) - val_logloss(+load)          (> 0: load helps the GBM fit L)
  gain_shuf  = val_logloss(orig) - val_logloss(+shuffled load)  (control: extra granularity without alignment)
  net        = gain_load - gain_shuf
Gate PASS for a peak-aware design if mean_i(net) > 0 and > 2 SE (SE = sd_i/sqrt(n)). Reported alongside: the same for
Baleen labels and the difference design - Baleen (does load help the peak-aware labels MORE), AUC gains, the time
split (train on the first 70% of day 1, validate on the last 30%), and +load+tod.
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402


def main():
    d = pd.read_csv(os.path.join(C.RESULTS, "learnability.csv"))
    piv = d.pivot_table(index=["labels", "inst", "split"], columns="feat", values=["val_logloss", "val_auc", "train_logloss"])
    rows = []
    for (lab, inst, split), r in piv.iterrows():
        x = dict(labels=lab, inst=inst, split=split)
        ll = r["val_logloss"]
        au = r["val_auc"]
        x["gain_load"] = ll["orig"] - ll["load"]
        x["auc_gain_load"] = au["load"] - au["orig"]
        x["train_gain_load"] = r["train_logloss"]["orig"] - r["train_logloss"]["load"]
        if split == "block":
            x["gain_shuf"] = ll["orig"] - ll["shuf"]
            x["net"] = x["gain_load"] - x["gain_shuf"]
            x["gain_loadtod"] = ll["orig"] - ll["load+tod"]
            x["auc_gain_shuf"] = au["shuf"] - au["orig"]
        x["val_logloss_orig"] = ll["orig"]
        x["val_auc_orig"] = au["orig"]
        rows.append(x)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(C.RESULTS, "learnability_gains.csv"), index=False)
    out = []
    bal = t[t.labels == "baleen"].set_index(["inst", "split"])
    for (lab, split), g in t.groupby(["labels", "split"]):
        n = len(g)
        s = dict(labels=lab, split=split, n_inst=n)
        for c in ["gain_load", "net", "gain_shuf", "gain_loadtod", "auc_gain_load", "train_gain_load", "val_logloss_orig", "val_auc_orig"]:
            if c in g and g[c].notna().any():
                s[c] = g[c].mean()
                s[c + "_se"] = g[c].std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
        if lab != "baleen":
            b = bal.loc[[(i, split) for i in g["inst"]]]
            dd = g["gain_load"].to_numpy() - b["gain_load"].to_numpy()
            s["vs_baleen_gain_load"] = dd.mean()
            s["vs_baleen_gain_load_se"] = dd.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
        if split == "block":
            s["gate_pass"] = bool(s["net"] > 0 and s["net"] > 2 * s["net_se"])
        out.append(s)
    o = pd.DataFrame(out)
    o.to_csv(os.path.join(C.RESULTS, "learnability_summary.csv"), index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    print(o.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
