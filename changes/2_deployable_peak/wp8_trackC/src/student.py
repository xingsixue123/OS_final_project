"""C-student: fit the student (Baleen's admission GBM with the artifact's parameters, features 18 + load = arm D) on a
label set's day-1 training rows and write the per-episode out-of-fold probability p_e (mean over the episode's
training rows, 3 block-grouped folds, inner early-stopping split) for the next Ising round's local field.
  src/run.sh baleen ../src/student.py --inst Region7_s0 --design F1PT4 --seed 1
Output: labels/student_<inst>_<design>_s<seed>.npz (p_ep, oof logloss/AUC) -- read by labels_c.py (STU<lam>R<r>).
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "q3lib")]
import wpcommon as C  # noqa: E402
import proxy as PX  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", required=True)
    ap.add_argument("--design", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--ap", default=PX.LOAD)
    o = ap.parse_args()
    from sklearn.metrics import log_loss, roc_auc_score
    D1 = PX.Day1(o.inst)
    lf = os.path.join(C.LABELS, f"{o.inst}_{o.design}_s{o.seed}.npz")
    y_ep = np.load(lf)["x_full"].astype(float)
    p_row = D1.oof(y_ep, o.ap, o.seed)
    y = y_ep[D1.ep]
    s = np.bincount(D1.ep, weights=p_row, minlength=D1.I.n)
    n = np.bincount(D1.ep, minlength=D1.I.n)
    p_ep = np.where(n > 0, s / np.maximum(n, 1), 0.5)
    k0 = D1.k == 0
    st = dict(inst=o.inst, design=o.design, seed=o.seed, ap=o.ap,
              oof_logloss=float(log_loss(y, np.clip(p_row, 1e-6, 1 - 1e-6), labels=[0, 1])),
              oof_auc=float(roc_auc_score(y, p_row)) if 0 < y.mean() < 1 else float("nan"),
              ep_disagree=float(((p_ep > 0.5) != (y_ep > 0.5)).mean()),
              pos_ep_p_mean=float(p_ep[y_ep > 0.5].mean()), neg_ep_p_mean=float(p_ep[y_ep < 0.5].mean()),
              k0_pos_rows_pred=float((p_row[k0] > 0.5).mean()), n_rows=int(len(y)))
    out = os.path.join(C.LABELS, f"student_{o.inst}_{o.design}_s{o.seed}.npz")
    np.savez_compressed(out + ".part.npz", p_ep=p_ep.astype(np.float32), stats=json.dumps(st))
    os.replace(out + ".part.npz", out)
    print("[student]", json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in st.items()}), flush=True)


if __name__ == "__main__":
    main()
