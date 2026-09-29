"""Compare two deployed trials (dev): per-window simulated load at the top windows, and the admission-GBM scores
on the full trace by access category (Baleen env).

  compare_runs.py <trial_key_A> <trial_key_B>
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import lightgbm as lgb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.environ["X_ROOT"], "common", "src"))
import q3lib as QL  # noqa: E402
import xc  # noqa: E402

W = os.path.join(xc.Q3, "work")
MB = 1 << 20


def trial(key):
    rows = [r for r in xc.read_jsonl(os.path.join(xc.Q3, "results", "trials.jsonl")) if r["trial_key"] == key]
    return rows[-1]


def model(key):
    out = xc.parse_train_outputs(os.path.join(W, "logs", "q3", key, "train.log"))
    return lgb.Booster(model_file=os.path.join(W, out["model_admit_threshold_binary"][0]))


def main():
    ka, kb = sys.argv[1], sys.argv[2]
    ta, tb = trial(ka), trial(kb)
    inst = ta["instance"]
    sa = xc.window_series(os.path.join(W, ta["result_file"]))
    sb = xc.window_series(os.path.join(W, tb["result_file"]))
    US = QL.US
    ua, ub = sa["used"] * US, sb["used"] * US
    noc = sa["nocache"] * US
    top = sorted(set(np.argsort(-ua[144:])[:8] + 144) | set(np.argsort(-ub[144:])[:8] + 144))
    print(f"{inst}: A={ka} P100={ta['p100']:.2f} WR={ta['wr']:.2f} th={ta['threshold']:.4f} | "
          f"B={kb} P100={tb['p100']:.2f} WR={tb['wr']:.2f} th={tb['threshold']:.4f}")
    print(pd.DataFrame({"win": top, "nocache": noc[top], "A": ua[top], "B": ub[top], "B-A": ub[top] - ua[top]}).round(2).to_string(index=False))
    I = QL.Inst(os.path.join(xc.COMMON, "inst", f"fullml_{inst}.npz"))
    F = QL.sim_features(I, cache=os.path.join(W, "cache", f"simfeat_fullml_{inst}.npz")).astype(float)
    ga, gb = model(ka).predict(F), model(kb).predict(F)
    adm_a, adm_b = ga > ta["threshold"], gb > tb["threshold"]
    cat = np.full(I.n_acc, "other", object)
    cat[I.acc_meta[:, 0] == 5] = "op5"
    cat[I.acc_meta[:, 0] == 1] = "op1"
    cat[F[:, 4] > 8 * MB] = "bigoff"
    cat[I.acc_k == 0] = "k0"
    load = QL.st(1, I.acc_nch) * US
    rows = []
    for c in ["k0", "bigoff", "op1", "op5", "other"]:
        m = cat == c
        rows.append(dict(cat=c, n=int(m.sum()), adm_A=adm_a[m].mean(), adm_B=adm_b[m].mean(),
                         load_adm_A=load[m & adm_a].sum(), load_adm_B=load[m & adm_b].sum()))
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    for w in top[:6]:
        m = I.acc_w == w
        print(f"  win {w}: accesses {m.sum()}, admitted A {adm_a[m].mean():.3f} B {adm_b[m].mean():.3f}; "
              f"admitted-load A {load[m & adm_a].sum():.2f} B {load[m & adm_b].sum():.2f}")


if __name__ == "__main__":
    main()
