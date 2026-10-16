"""Track C cheap deployed proxy ("emulated deployed P100"), Baleen env (lightgbm), run through src/run.sh baleen.

PL (label-level): labels -> LightGBM refit with the artifact's GBAdmissionTrainer params on the trainer's day-1 rows
(k < 15) of common/inst/day1_<inst>.npz (18 features, + the overlay's `load` for +load arms) -> scores of every GET
access of fullml_<inst>.npz (emu.InstEmu: simulator-style features + load) -> base threshold from the write-rate
calibration (alpha in the emulated admission rule) -> q3lib.emulate_loads -> emulated P100 (windows >= 144).
PM (model-level, diagnostic): the same with WP2's actual trained admission model.

Write-rate measures of an emulated admission (first admitted access k* per episode):
  ep   whole-episode chunk span written at k* (the existing emulator, I.nchunks)
  acc  chunk span accessed from k* on (min c0 .. max c0+nch over accesses k >= k*)
Both are reported as an emulated WR = 35.599 * chunks / B (B = the fullml instance's label budget).
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "q3lib")]
import wpcommon as C  # noqa: E402
import q3lib as QL  # noqa: E402

PARAMS = {"boosting_type": "gbdt", "objective": "binary", "metric": "binary_logloss", "num_leaves": 63,
          "learning_rate": 0.005, "max_bin": 255, "feature_fraction": 0.9, "bagging_fraction": 0.9,
          "bagging_freq": 5, "min_data_in_leaf": 50, "min_sum_hessian_in_leaf": 5.0, "num_threads": 4,
          "verbosity": -1}
ORIG = "meta+block+chunk"
LOAD = "meta+block+chunk+load"
CACHE = os.path.join(C.RESULTS, "proxy_cache")
WP2 = os.path.join(C.P2, "wp2_deployed")


# ------------------------------------------------------------------ day-1 training rows
class Day1:
    def __init__(self, inst):
        from BCacheSim.cachesim import load_features as LF
        assert inst in C.DEV, inst
        self.inst = inst
        self.I = QL.Inst(os.path.join(C.COMMON, "inst", f"day1_{inst}.npz"))
        I = self.I
        r = np.flatnonzero(I.acc_row == 1)
        self.r = r
        self.X18 = np.c_[I.acc_meta[r], I.acc_dyn[r]].astype(float)
        self.ts = I.acc_ts[r]
        self.k = I.acc_k[r]
        cache = os.path.join(CACHE, f"day1load_{inst}.npy")
        if os.path.exists(cache):
            self.load = np.load(cache)
        else:
            trace = C.get_flag(C.JOBS[inst]["baleen"]["sim_args"], "--trace")
            dl = LF.DemandLoad.from_trace(os.path.join(C.WORK, trace), 0.1)
            self.load = np.array([dl.load(t) for t in self.ts])
            os.makedirs(CACHE, exist_ok=True)
            np.save(cache, self.load)
        self.ep = I.acc_ep[r]
        self.blocks = I.block_ids()[self.ep]
        self.ub = np.unique(self.blocks)

    def X(self, ap):
        return self.X18 if ap == ORIG else np.c_[self.X18, self.load]

    def split(self, seed):
        rs = np.random.RandomState(seed)
        test_b = rs.choice(self.ub, size=int(round(0.3 * len(self.ub))), replace=False)
        return np.isin(self.blocks, test_b)

    def fit(self, y_ep, ap, seed, return_val=False):
        import lightgbm as lgb
        X = self.X(ap)
        y = np.asarray(y_ep, float)[self.ep]
        te = self.split(seed)
        p = dict(PARAMS, seed=seed)
        dtr = lgb.Dataset(X[~te], y[~te])
        dva = lgb.Dataset(X[te], y[te], reference=dtr)
        bst = lgb.train(p, dtr, num_boost_round=2000, valid_sets=[dva],
                        callbacks=[lgb.early_stopping(25, verbose=False)])
        if return_val:
            return bst, te
        return bst

    def oof(self, y_ep, ap, seed, folds=3):
        """Out-of-fold (block-grouped) predicted probability per training row (student field, C-student)."""
        import lightgbm as lgb
        X = self.X(ap)
        y = np.asarray(y_ep, float)[self.ep]
        rs = np.random.RandomState(1000 + seed)
        perm = rs.permutation(self.ub)
        fold_of_block = {b: i % folds for i, b in enumerate(perm)}
        f = np.array([fold_of_block[b] for b in self.blocks])
        out = np.zeros(len(y))
        for q in range(folds):
            tr = f != q
            # inner early-stopping split inside the training folds (by block, seeded)
            tb = np.unique(self.blocks[tr])
            es_b = np.random.RandomState(seed + 17 * q).choice(tb, size=max(1, int(round(0.2 * len(tb)))), replace=False)
            es = tr & np.isin(self.blocks, es_b)
            fit_ = tr & ~es
            p = dict(PARAMS, seed=seed)
            dtr = lgb.Dataset(X[fit_], y[fit_])
            dva = lgb.Dataset(X[es], y[es], reference=dtr)
            bst = lgb.train(p, dtr, num_boost_round=2000, valid_sets=[dva],
                            callbacks=[lgb.early_stopping(25, verbose=False)])
            out[f == q] = bst.predict(X[f == q])
        return out


# ------------------------------------------------------------------ emulation on the fullml instance
_EMU = {}


def get_emu(inst):
    import emu
    assert inst in C.DEV, inst
    if inst not in _EMU:
        _EMU[inst] = emu.InstEmu(inst)
        E = _EMU[inst]
        I = E.I
        # per-access helpers for the `acc` write measure
        E.acc_end = (I.acc_c0 + I.acc_nch).astype(np.int64)
        E.acc_c0i = I.acc_c0.astype(np.int64)
        st = I.acc_start.astype(np.int64)
        assert np.all(np.diff(st) > 0) and st[0] == 0 and len(st) >= I.n and np.all(I.acc_ep[st[:I.n]] == np.arange(I.n))
        E.seg = st[:I.n]
    return _EMU[inst]


def measures(E, adm):
    """emulated loads / writes for the admission vector adm (per access)."""
    I = E.I
    kst = QL.first_admit(I, adm)
    L, wch = QL.emulate_loads(I, kst)
    k_of = kst[I.acc_ep]
    m = (k_of >= 0) & (I.acc_k >= k_of)
    # accesses are episode-major (acc_start[e]:acc_start[e+1]) -> segment reductions (same result as ufunc.at)
    BIG = np.iinfo(np.int64).max
    lo = np.minimum.reduceat(np.where(m, E.acc_c0i, BIG), E.seg)
    hi = np.maximum.reduceat(np.where(m, E.acc_end, -1), E.seg)
    span = float(np.where(hi >= 0, hi - lo, 0).sum())
    return dict(L=L, wr_ep=C.TARGET_WR * wch / I.B, wr_acc=C.TARGET_WR * span / I.B, kst=kst)


def emu_eval(E, g, theta, alpha):
    adm = E.admit(g, theta, alpha)
    M = measures(E, adm)
    L = M["L"]
    used = L[QL.SKIP:]
    out = dict(theta=float(theta), wr_ep=M["wr_ep"], wr_acc=M["wr_acc"], p100=float(used.max() * QL.US),
               top5=float(np.sort(used)[::-1][:5].mean() * QL.US), mean_dt=float(used.mean() * QL.US),
               argmax=int(np.argmax(used)) + QL.SKIP, k0_adm=float(adm[E.k0].mean()), all_adm=float(adm.mean()))
    return out


# ------------------------------------------------------------------ write-rate calibration
def load_calib():
    p = os.path.join(C.RESULTS, "wr_calibration.json")
    return json.load(open(p)) if os.path.exists(p) else None


def pred_sim_wr(cal_i, ev):
    """calibrated simulated WR from the emulated measures (per-instance log-linear map)."""
    v = cal_i["variant"]
    c = cal_i["coef"]
    if v == "ep":
        return float(np.exp(c[0] + c[1] * np.log(max(ev["wr_ep"], 1e-9))))
    if v == "acc":
        return float(np.exp(c[0] + c[1] * np.log(max(ev["wr_acc"], 1e-9))))
    return float(np.exp(c[0] + c[1] * np.log(max(ev["wr_ep"], 1e-9)) + c[2] * np.log(max(ev["wr_acc"], 1e-9))))


def theta_matched(E, g, alpha, cal_i, iters=26):
    """bisection on the base threshold so that the calibrated WR equals 35.599 (WR non-increasing in theta)."""
    hi0 = 4.0 if alpha is not None else 0.9999
    lo, hi = 0.0, hi0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        ev = emu_eval(E, g, mid, alpha)
        if pred_sim_wr(cal_i, ev) > C.TARGET_WR:
            lo = mid
        else:
            hi = mid
    th = 0.5 * (lo + hi)
    ev = emu_eval(E, g, th, alpha)
    ev["pred_sim_wr"] = pred_sim_wr(cal_i, ev)
    ev["bound"] = bool(th > hi0 - 1e-3)
    return ev


def scores_cached(E, key, model_path, ap):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"g_{key}.npy")
    if os.path.exists(p):
        return np.load(p).astype(float)
    g = E.scores(model_path, ap)
    np.save(p, g.astype(np.float32))
    return g


def booster_scores(E, bst, ap):
    return bst.predict(E.features(ap))
