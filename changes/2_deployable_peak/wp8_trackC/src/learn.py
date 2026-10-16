"""Learnability gate (PLAN.md §5): on day 1, can Baleen's GBM fit the peak-aware labels better WITH `load` than without?

Rows = the admission trainer's day-1 rows (k < 15) of common/inst/day1_<inst>.npz with exactly its 18 features
(acc_meta + acc_dyn, verified equal to the frozen trainer's df_X in phase 1), label = the episode's label:
Baleen (prefix of Baleen's order within B) or a WP2 label file (seed 1). Extra columns = the overlay's `load`
(load_features.DemandLoad, the same function train_ap uses) and `tod`.
Feature sets: orig (18) | +load | +shuf (load rows permuted across rows: same marginal, no alignment -- a control for
added granularity) | +load+tod.
Fits: the artifact's GBM (train_ap.GBAdmissionTrainer params: binary, 63 leaves, lr 0.005, <= 2000 rounds, early stop
25 on the held-out part), 70/30 split by block (seeded, identical for all label/feature sets). Reported: train/val
logloss, AUC, accuracy; cell-purity ceiling (share of rows a deterministic function of the features can get right:
cells = exact 18-feature tuples, + load decile bin for +load/+shuf). Secondary: time split (first 70% of day-1 rows by
time -> last 30%), orig vs +load.
  cd wp2_deployed/work && taskset ... bwrap ... $BALEEN_PY -B ../src/learn.py [--insts ...] [--labels ...]
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "q3lib"), os.path.join(os.path.dirname(HERE), "work")]
import wpcommon as C  # noqa: E402

PARAMS = {"boosting_type": "gbdt", "objective": "binary", "metric": "binary_logloss", "num_leaves": 63,
          "learning_rate": 0.005, "max_bin": 255, "feature_fraction": 0.9, "bagging_fraction": 0.9,
          "bagging_freq": 5, "min_data_in_leaf": 50, "min_sum_hessian_in_leaf": 5.0, "num_threads": 4,
          "verbosity": -1, "seed": 42}
LABEL_SETS = ["baleen", "P0", "T2", "C2", "F1PT", "F1EIM", "F1CPSAT"]


def fit(Xtr, ytr, Xva, yva):
    import lightgbm as lgb
    from sklearn.metrics import log_loss, roc_auc_score
    dtr = lgb.Dataset(Xtr, ytr)
    dva = lgb.Dataset(Xva, yva, reference=dtr)
    bst = lgb.train(PARAMS, dtr, num_boost_round=2000, valid_sets=[dva],
                    callbacks=[lgb.early_stopping(25, verbose=False)])
    ptr, pva = bst.predict(Xtr), bst.predict(Xva)
    eps = 1e-6
    out = dict(rounds=bst.best_iteration or bst.current_iteration(),
               train_logloss=log_loss(ytr, np.clip(ptr, eps, 1 - eps), labels=[0, 1]),
               val_logloss=log_loss(yva, np.clip(pva, eps, 1 - eps), labels=[0, 1]),
               train_acc=float(((ptr > 0.5) == ytr).mean()), val_acc=float(((pva > 0.5) == yva).mean()))
    out["train_auc"] = roc_auc_score(ytr, ptr) if 0 < ytr.mean() < 1 else np.nan
    out["val_auc"] = roc_auc_score(yva, pva) if 0 < yva.mean() < 1 else np.nan
    # base rate logloss (constant predictor) for reference
    p0 = float(np.clip(ytr.mean(), eps, 1 - eps))
    out["val_logloss_const"] = log_loss(yva, np.full(len(yva), p0), labels=[0, 1])
    return out


def purity(X, y):
    _, cid = np.unique(X, axis=0, return_inverse=True)
    cid = cid.ravel()
    pos = np.bincount(cid, weights=y)
    n = np.bincount(cid)
    return float(np.maximum(pos, n - pos).sum() / len(y)), int(len(n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insts", nargs="+", default=C.DEV)
    ap.add_argument("--labels", nargs="+", default=LABEL_SETS)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(C.RESULTS, "learnability.csv"))
    o = ap.parse_args()
    from BCacheSim.cachesim import load_features as LF
    import q3lib as QL
    done = set()
    if os.path.exists(o.out):
        d0 = pd.read_csv(o.out)
        done = set(zip(d0["inst"], d0["labels"], d0["split"], d0["feat"]))
    for inst in o.insts:
        I = QL.Inst(os.path.join(C.COMMON, "inst", f"day1_{inst}.npz"))
        trace = C.get_flag(C.JOBS[inst]["baleen"]["sim_args"], "--trace")
        dl = LF.DemandLoad.from_trace(os.path.join(C.WORK, trace), 0.1)
        r = np.flatnonzero(I.acc_row == 1)
        X18 = np.c_[I.acc_meta[r], I.acc_dyn[r]].astype(float)
        ts = I.acc_ts[r]
        load = np.array([dl.load(t) for t in ts])
        tod = np.array([LF.tod(t) for t in ts])
        rng = np.random.RandomState(7)
        shuf = load[rng.permutation(len(load))]
        ep = I.acc_ep[r]
        blocks = I.block_ids()[ep]
        ub = np.unique(blocks)
        rs = np.random.RandomState(42)
        test_b = set(rs.choice(ub, size=int(round(0.3 * len(ub))), replace=False).tolist())
        te_block = np.array([b in test_b for b in blocks])
        te_time = ts >= np.quantile(ts, 0.7)
        feats = {"orig": X18, "load": np.c_[X18, load], "shuf": np.c_[X18, shuf], "load+tod": np.c_[X18, load, tod]}
        dec = lambda v: np.digitize(v, np.quantile(v, np.linspace(0.1, 0.9, 9)))  # noqa: E731
        cellX = {"orig": X18, "load": np.c_[X18, dec(load[:, 0])], "shuf": np.c_[X18, dec(shuf[:, 0])],
                 "load+tod": np.c_[X18, dec(load[:, 0]), np.floor((ts % 86400) / 3600)]}
        for lab in o.labels:
            if lab == "baleen":
                y_ep = I.baleen_x()
            else:
                f = os.path.join(C.LABELS, f"{inst}_{lab}_s{o.seed}.npz")
                if not os.path.exists(f):
                    print("missing", f, flush=True)
                    continue
                y_ep = np.load(f)["x_full"].astype(float)
            y = y_ep[ep]
            for split, te in (("block", te_block), ("time", te_time)):
                for fs, X in feats.items():
                    if split == "time" and fs not in ("orig", "load"):
                        continue
                    if (inst, lab, split, fs) in done:
                        continue
                    res = fit(X[~te], y[~te], X[te], y[te])
                    pur, ncell = purity(cellX[fs], y)
                    row = dict(inst=inst, labels=lab, seed=o.seed, split=split, feat=fs, n_rows=len(y), pos_rate=float(y.mean()),
                               purity=pur, n_cells=ncell, **res)
                    pd.DataFrame([row]).to_csv(o.out, mode="a", header=not os.path.exists(o.out), index=False)
                    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}), flush=True)


if __name__ == "__main__":
    main()
