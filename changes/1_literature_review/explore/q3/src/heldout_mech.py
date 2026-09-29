"""Post-hoc mechanism analysis of the held-out runs (configurations are frozen; analysis only).

For every matched held-out trial of the finalists and every Baleen online held-out retrain: the trained admission
GBM's first-access admission rate on the full trace (simulator-style features), the simulated peak window, the share
of big-offset accesses (end > 8 MB) in that window, and the admitted fraction of that window's accesses.
Output: q3/results/heldout_mech.csv (+ printed summary). Baleen env.
"""
import os
import sys

import numpy as np
import pandas as pd
import lightgbm as lgb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.environ["X_ROOT"], "common", "src"))
import q3lib as QL  # noqa: E402
import xc  # noqa: E402

MB = 1 << 20
HELD = [f"{r}_s{s}" for r in ["Region7", "Region6"] for s in ["0.1", "0.2", "0.3"]]


def analyse(I, F, model_path, th, result_file):
    g = lgb.Booster(model_file=model_path).predict(F)
    a = g > th
    ws = xc.window_series(result_file)
    used = ws["used"] * QL.US
    w = int(np.argmax(used[144:]) + 144)
    m = I.acc_w == w
    return dict(k0_adm=float(a[I.acc_k == 0].mean()), all_adm=float(a.mean()), peak_win=w, peak=float(used[w]),
                peak_bigoff_share=float((F[m, 4] > 8 * MB).mean()) if m.any() else np.nan,
                peak_adm=float(a[m].mean()) if m.any() else np.nan, mean_used=float(used[144:].mean()))


def main():
    rows = []
    trials = pd.DataFrame(xc.read_jsonl(os.path.join(xc.Q3, "results", "trials.jsonl")))
    trials = trials[(trials.stage == "heldout") & trials.matched.astype(bool)]
    a0 = [r for r in xc.read_jsonl(os.path.join(xc.COMMON, "results", "a0.jsonl")) if r["method"] == "Baleen"]
    for key in HELD:
        I = QL.Inst(os.path.join(xc.COMMON, "inst", f"fullml_{key}.npz"))
        F = QL.sim_features(I, cache=os.path.join(xc.Q3, "work", "cache", f"simfeat_fullml_{key}.npz")).astype(float)
        for r in a0:
            if r["instance"] != key:
                continue
            out = xc.parse_train_outputs(os.path.join(xc.COMMON, "work", "logs", "a0", r["exp"], "train.log"))
            res = analyse(I, F, os.path.join(xc.COMMON, "work", out["model_admit_threshold_binary"][0]), r["value"],
                          os.path.join(xc.COMMON, "work", r["result_file"]))
            rows.append(dict(instance=key, config="Baleen", rep=r["rep"], p100=r["p100"], **res))
        for _, t in trials[trials.instance == key].iterrows():
            out = xc.parse_train_outputs(os.path.join(xc.Q3, "work", "logs", "q3", t.trial_key, "train.log"))
            res = analyse(I, F, os.path.join(xc.Q3, "work", out["model_admit_threshold_binary"][0]), t.threshold,
                          os.path.join(xc.Q3, "work", t.result_file))
            rows.append(dict(instance=key, config=t.config, rep=t.rep, p100=t.p100, **res))
        print(key, "done", flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(os.path.join(xc.Q3, "results", "heldout_mech.csv"), index=False)
    pd.set_option("display.width", 200)
    print(d.round(3).to_string(index=False))
    print(d.groupby(["instance", "config"])[["p100", "k0_adm", "peak_bigoff_share", "peak_adm", "mean_used"]].mean().round(3))


if __name__ == "__main__":
    main()
