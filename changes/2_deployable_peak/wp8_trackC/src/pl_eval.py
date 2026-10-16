"""Proxy evaluations (Baleen env; resumable; every evaluation = one row of results/proxy_ledger.csv).
  --what wp2   PL for WP2's dev configurations (validation set, PROGRESS.md pre-registration)
  --what pm    PM: WP2's actual trained models of the matched retrains, theta from the same calibration
  --what c     PL for Track C designs (labels/<inst>_<design>_s<k>.npz), alpha in {none, -1}
  src/run.sh baleen ../src/pl_eval.py --what wp2 [--insts ...]
"""
import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "q3lib")]
import wpcommon as C  # noqa: E402
import proxy as PX  # noqa: E402

LEDGER = os.path.join(C.RESULTS, "proxy_ledger.csv")
ORIG, LOAD = PX.ORIG, PX.LOAD
WP2_CFGS = {"A": ("baleen", ORIG, None), "B": ("baleen", LOAD, None), "A+a": ("baleen", ORIG, -1.0),
            "B+a": ("baleen", LOAD, -1.0), "B+a0.5": ("baleen", LOAD, -0.5),
            "C:F1PT": ("wp2:F1PT", ORIG, None), "C:F1EIM": ("wp2:F1EIM", ORIG, None),
            "D:F1PT": ("wp2:F1PT", LOAD, None), "D:F1EIM": ("wp2:F1EIM", LOAD, None),
            "Dc": ("wp2:F1CPSAT", LOAD, None), "X1": ("wp2:F1PT", LOAD, -1.0), "X2": ("wp2:F1PT", LOAD, -0.5),
            "Ec": ("wp2:F1CPSAT", LOAD, -1.0)}
WP2_SCREENS = {"D:P0": ("wp2:P0", LOAD, None), "D:T2": ("wp2:T2", LOAD, None),
               "E:F1EIM": ("wp2:F1EIM", LOAD, -1.0)}
# WP2 trials.csv arm/design -> validation configuration name
WP2_MAP = {("A", "baleen"): "A", ("B", "baleen"): "B", ("Aa-1.0", "baleen"): "A+a", ("Ax-1.0", "baleen"): "A+a",
           ("Ba-1.0", "baleen"): "B+a", ("Bx-1.0", "baleen"): "B+a", ("Ba-0.5", "baleen"): "B+a0.5",
           ("Bx-0.5", "baleen"): "B+a0.5", ("C", "F1PT"): "C:F1PT", ("C", "F1EIM"): "C:F1EIM",
           ("D", "F1PT"): "D:F1PT", ("D", "F1EIM"): "D:F1EIM", ("D", "F1CPSAT"): "Dc", ("Ea-1.0", "F1PT"): "X1",
           ("Ea-0.5", "F1PT"): "X2", ("Ea-1.0", "F1CPSAT"): "Ec", ("Ex-1.0", "F1CPSAT"): "Ec",
           ("D", "P0"): "D:P0", ("D", "T2"): "D:T2", ("Ea-1.0", "F1EIM"): "E:F1EIM"}


def done_keys():
    return set(pd.read_csv(LEDGER).key) if os.path.exists(LEDGER) else set()


def append(row):
    C.append_csv(LEDGER, row)


def labels_of(D1, src, seed):
    if src == "baleen":
        return D1.I.baleen_x()
    kind, d = src.split(":")
    root = os.path.join(PX.WP2, "labels") if kind == "wp2" else C.LABELS
    f = os.path.join(root, f"{D1.inst}_{d}_s{seed}.npz")
    if not os.path.exists(f):
        return None
    return np.load(f)["x_full"].astype(float)


def pl_group(inst, src, ap, seed, items, cal, done):
    """one refit (labels src, features ap, seed) -> several (config, alpha) evaluations."""
    todo = [(cfg, a) for cfg, a in items if f"pl|{inst}|{cfg}|s{seed}" not in done]
    if not todo:
        return
    D1 = PX.Day1(inst)
    y = labels_of(D1, src, seed)
    if y is None:
        print("missing labels", inst, src, seed, flush=True)
        return
    E = PX.get_emu(inst)
    t0 = time.time()
    bst, te = D1.fit(y, ap, seed, return_val=True)
    from sklearn.metrics import log_loss
    yv = y[D1.ep][te]
    vll = float(log_loss(yv, np.clip(bst.predict(D1.X(ap)[te]), 1e-6, 1 - 1e-6), labels=[0, 1]))
    g = PX.booster_scores(E, bst, ap)
    for cfg, alpha in todo:
        ev = PX.theta_matched(E, g, alpha, cal[inst])
        row = dict(key=f"pl|{inst}|{cfg}|s{seed}", kind="pl", inst=inst, config=cfg, labels=src, ap_subset=ap,
                   alpha=alpha, seed=seed, n_label=int(y.sum()), gbm_rounds=int(bst.best_iteration or bst.current_iteration()),
                   val_logloss=vll, secs=time.time() - t0, ts=time.strftime("%Y-%m-%dT%H:%M:%S"),
                   **{k: v for k, v in ev.items() if k not in ("L",)})
        append(row)
        print(f"PL {inst} {cfg} s{seed}: p100={ev['p100']:.2f} th={ev['theta']:.4f} predWR={ev['pred_sim_wr']:.2f} "
              f"k0={ev['k0_adm']:.3f}", flush=True)


def run_pl(insts, cfgs, seeds_of, cal):
    done = done_keys()
    for inst in insts:
        groups = {}
        for cfg, (src, ap, alpha) in cfgs.items():
            for k in seeds_of(cfg):
                groups.setdefault((src, ap, k), []).append((cfg, alpha))
        for (src, ap, k), items in groups.items():
            pl_group(inst, src, ap, k, items, cal, done)


def run_pm(insts, cal):
    done = done_keys()
    t = pd.read_csv(os.path.join(PX.WP2, "trials.csv"))
    t = t[~t.trial_key.str.contains("FAILED") & (t.matched == True)]  # noqa: E712
    for inst in insts:
        E = PX.get_emu(inst)
        for _, r in t[t.inst == inst].iterrows():
            cfg = WP2_MAP.get((r.arm, r.design))
            if cfg is None:
                continue
            key = f"pm|{inst}|{cfg}|{r.trial_key}"
            if key in done:
                continue
            rec = json.load(open(os.path.join(PX.WP2, "results", "train", f"{r.train_key}.json")))
            g = PX.scores_cached(E, "wp2_" + r.train_key, rec["out"]["model_admit_threshold_binary"][0], r.ap_subset)
            alpha = None if pd.isna(r.alpha) else float(r.alpha)
            ev = PX.theta_matched(E, g, alpha, cal[inst])
            ev_sim = PX.emu_eval(E, g, float(r.threshold), alpha)       # at the simulation's converged theta
            row = dict(key=key, kind="pm", inst=inst, config=cfg, labels=r.design, ap_subset=r.ap_subset, alpha=alpha,
                       seed=int(r.rep), trial_key=r.trial_key, sim_p100=float(r.p100), sim_threshold=float(r.threshold),
                       sim_k0_adm=float(r.k0_adm), emu_p100_at_sim_theta=ev_sim["p100"],
                       emu_k0_at_sim_theta=ev_sim["k0_adm"], ts=time.strftime("%Y-%m-%dT%H:%M:%S"),
                       **{k: v for k, v in ev.items() if k not in ("L",)})
            append(row)
            print(f"PM {r.trial_key}: emu p100={ev['p100']:.2f} (at sim theta {ev_sim['p100']:.2f}) sim {r.p100:.2f}",
                  flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", required=True, choices=["wp2", "pm", "c"])
    ap.add_argument("--insts", nargs="+", default=C.DEV)
    ap.add_argument("--designs", nargs="+", default=[])
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    o = ap.parse_args()
    assert set(o.insts) <= set(C.DEV)
    cal = PX.load_calib()
    assert cal is not None, "run calib.py first"
    if o.what == "wp2":
        cfgs = dict(WP2_CFGS, **WP2_SCREENS)
        run_pl(o.insts, cfgs, lambda c: [1] if c in WP2_SCREENS else o.seeds, cal)
    elif o.what == "pm":
        run_pm(o.insts, cal)
    else:
        cfgs = {}
        for d in o.designs:
            cfgs[f"D:{d}"] = (f"c:{d}", LOAD, None)
            cfgs[f"E:{d}"] = (f"c:{d}", LOAD, -1.0)
        run_pl(o.insts, cfgs, lambda c: o.seeds, cal)


if __name__ == "__main__":
    main()
