"""WP9 preparation summaries (no test outcomes): results/labels_summary.csv from labels/*.json and the instance table
(episodes, GET accesses, active windows, B, EA, bytes, sha256) printed as Markdown for INSTANCES.md.
  cd wp9_region5 && $BALEEN_PY -B src/summarize_prep.py"""
import glob
import json
import os

import numpy as np
import pandas as pd

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def labels_summary():
    rows = []
    for f in sorted(glob.glob(os.path.join(W, "labels", "*.json"))):
        s = json.load(open(f))
        info = s.get("info", {})
        rows.append(dict(inst=s["inst"], design=s["design"], seed=s["seed"], n_core=s["n_core"], n_label=s["n_label"],
                         n_baleen=s["n_baleen"], jaccard_vs_baleen=s["jaccard_vs_baleen"], use_frac=s["use_frac"],
                         label_peak_util=s["label_peak_util"], baleen_peak_util=s["baleen_peak_util"],
                         zero_value_labels=s["zero_value_labels"], secs=s["secs"], solver=info.get("solver"),
                         budget=info.get("budget"), cfg=json.dumps(info.get("cfg"))))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(W, "results", "labels_summary.csv"), index=False)
    print(df.groupby("inst")[["n_label", "n_baleen", "jaccard_vs_baleen", "label_peak_util", "baleen_peak_util",
                              "zero_value_labels", "secs"]].mean().round(3).to_string())
    print(len(df), "label sets")


def instances():
    sha = pd.read_csv(os.path.join(W, "results", "instances_sha256.csv")).set_index("file")
    print("| file | episodes | GET accesses | active windows | B (chunks) | EA (s) | bytes | sha256 |")
    print("|---|---|---|---|---|---|---|---|")
    for f in sha.index:
        z = np.load(os.path.join(W, "inst", f))
        print(f"| `{f}` | {len(z['s'])} | {len(z['acc_ts'])} | {int(z['active'].sum())}/{len(z['active'])} | "
              f"{int(z['B'])} | {float(z['ea']):.3f} | {sha.loc[f, 'bytes']} | `{sha.loc[f, 'sha256']}` |")


if __name__ == "__main__":
    labels_summary()
    instances()
