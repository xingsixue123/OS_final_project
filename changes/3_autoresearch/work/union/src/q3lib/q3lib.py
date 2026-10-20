"""Track A analysis library (numpy/scipy only; lightgbm optional): instances, simulator-style features, analytic
online-admission emulation (the cheap deployed proxy), cell definitions.

Instance npz = pb3_policy dump (harness_eval format + per-access arrays; see common/INSTANCES.md).
"""
import os

import numpy as np
import scipy.sparse as sp

US = 1.0 / 36 * (100.0 / 0.1) / 600 * 100          # DT seconds per 600 s window -> utilisation %
SKIP = 144
TARGET_WR = 35.599
FEAT_NAMES = (["feat_metadata|op", "feat_metadata|ns", "feat_metadata|user", "feat_metadata_size|start",
               "feat_metadata_size|end", "feat_metadata_size|size"] + [f"feat_dynamic_b|{i}" for i in range(6)]
              + [f"feat_dynamic_c_combined|{i}" for i in range(6)])


def st(ios, chunks):
    """episodes.service_time (constants_public): ios * 11.5 ms + chunks * 128 KiB / 143 MB/s."""
    return ios * 11.5e-3 + chunks * 131072 / 1048576 / 143


class Inst:
    def __init__(self, path):
        self.path = path
        z = np.load(path, allow_pickle=False)
        self.z = z
        self.D = sp.csr_matrix((z["D_data"], z["D_indices"], z["D_indptr"]), shape=tuple(z["D_shape"]))
        self.n, self.m = self.D.shape
        self.C = z["C"].astype(float)
        self.s = z["s"].astype(float)
        self.B = float(z["B"])
        self.active = z["active"].astype(bool)
        self.base_order = z["base_order"].astype(np.int64)
        self.base_score = z["base_score"].astype(float)
        self.keys = z["keys"]
        self.ts0 = z["ts0"].astype(float)
        self.ts_end = z["ts_end"].astype(float)
        self.nchunks = z["nchunks"].astype(float)
        self.t0 = float(z["t0"])
        self.ea = float(z["ea"])
        self.sts = np.asarray(self.D.sum(1)).ravel()
        self.rank = np.empty(self.n, np.int64)
        self.rank[self.base_order] = np.arange(self.n)
        if "acc_ep" in z.files:
            for k in ["acc_ep", "acc_k", "acc_ts", "acc_w", "acc_nch", "acc_c0", "acc_meta", "acc_dyn", "acc_row",
                      "acc_start"]:
                setattr(self, k, z[k])
            self.n_acc = len(self.acc_ep)
            self.block_of_ep = None

    # ---------------------------------------------------------------- selections
    def baleen_x(self, B=None):
        B = self.B if B is None else B
        cs = np.cumsum(self.s[self.base_order])
        x = np.zeros(self.n)
        x[self.base_order[cs <= B]] = 1
        return x

    def loads(self, x):
        return self.C - self.D.T @ x

    def peak(self, x, skip=None):
        L = self.loads(x)
        a = self.active if skip is None else (np.arange(self.m) >= skip)
        return float(L[a].max() * US)

    def wr(self, x):
        return TARGET_WR * float(self.s @ x) / self.B

    def block_ids(self):
        if self.block_of_ep is None:
            u, inv = np.unique(self.keys, return_inverse=True)
            self.block_of_ep = inv.astype(np.int64)
            self.n_blocks = len(u)
        return self.block_of_ep


# -------------------------------------------------------------------- simulator-style features
def sim_features(I, cache=None):
    """18 features per access exactly as the simulator computes them for `mlnew` (sim_features.collect_features with
    a global DynamicFeatures(6, granularity='both'), counts read BEFORE the access updates them), for all GET
    accesses in the instance, processed in time order (ties: episode order). Returns (n_acc x 18) int64 in the
    flat access order of the instance."""
    if cache and os.path.exists(cache):
        return np.load(cache)["F"]
    blk = I.block_ids()[I.acc_ep]
    order = np.lexsort((np.arange(I.n_acc), I.acc_ts))
    F = np.zeros((I.n_acc, 18), np.int64)
    F[:, :6] = I.acc_meta
    hist = []      # newest first: dicts
    tss = []
    HR = 3600.0
    for p in order:
        ts = I.acc_ts[p]
        b = int(blk[p])
        c0 = int(I.acc_c0[p])
        nch = int(I.acc_nch[p])
        # features before update
        bf = [h.get(b, 0) for h in hist]
        F[p, 6:6 + len(bf)] = bf
        comb = np.zeros(6, np.int64)
        for c in range(c0, c0 + nch):
            key = b * 4096 + c
            for i, h in enumerate(hist):
                comb[i] += h.get(-key - 1, 0)
        F[p, 12:18] = comb
        # updates (block key then each chunk key), same bucket rule as DynamicFeatures.updateFeatures
        for key in [b] + [-(b * 4096 + c) - 1 for c in range(c0, c0 + nch)]:
            if len(hist) == 0 or ts > tss[0] + HR:
                hist.insert(0, {})
                tss.insert(0, ts)
            if len(hist) > 6:
                hist.pop()
                tss.pop()
            hist[0][key] = hist[0].get(key, 0) + 1
    if cache:
        np.savez_compressed(cache, F=F)
    return F


# -------------------------------------------------------------------- analytic online admission emulation
def first_admit(I, adm):
    """kstar[e] = first access index k with adm True (acc order within episode), -1 if none."""
    kst = np.full(I.n, -1, np.int64)
    idx = np.flatnonzero(adm)
    if len(idx):
        ep = I.acc_ep[idx]
        # first occurrence per episode (flat order is episode-major, k ascending)
        u, first = np.unique(ep, return_index=True)
        kst[u] = I.acc_k[idx[first]]
    return kst


def emulate_loads(I, kst, prefetch="episode"):
    """Per-window loads when episode e is admitted at its access kst[e] (>=0): accesses after kst hit; at kst the
    whole episode range is fetched (the harness's filter_=prefetch model generalised to late admission).
    Returns (loads, chunks_written)."""
    k_of = kst[I.acc_ep]
    after = (k_of >= 0) & (I.acc_k > k_of)
    at = (k_of >= 0) & (I.acc_k == k_of)
    stc = st(1, I.acc_nch)
    contrib = np.where(after, stc, 0.0)
    contrib = contrib + np.where(at, stc - st(1, I.nchunks[I.acc_ep]), 0.0)
    L = I.C - np.bincount(I.acc_w, weights=contrib, minlength=I.m)[:I.m]
    written = float(I.nchunks[kst >= 0].sum()) if prefetch == "episode" else float(I.s[kst >= 0].sum())
    return L, written


def emulate_at(I, score, theta):
    kst = first_admit(I, score > theta)
    L, wch = emulate_loads(I, kst)
    wr = TARGET_WR * wch / I.B
    return L, wr, kst


def match_wr(I, score, target=TARGET_WR, lo=0.0, hi=1.0, iters=40):
    """Bisection on the probability threshold so the emulated write rate matches the target."""
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        _, wr, _ = emulate_at(I, score, mid)
        if wr > target:
            lo = mid
        else:
            hi = mid
    L, wr, kst = emulate_at(I, score, hi)
    return hi, L, wr, kst


def peak_util(L, skip=SKIP):
    return float(L[skip:].max() * US)


def topk_util(L, k=5, skip=SKIP):
    return float(np.sort(L[skip:])[::-1][:k].mean() * US)


# -------------------------------------------------------------------- GBM (proxy only; same params as train_ap)
GBM_PARAMS = {"boosting_type": "gbdt", "objective": "binary", "metric": "binary_logloss", "num_leaves": 63,
              "learning_rate": 0.005, "max_bin": 255, "feature_fraction": 0.9, "bagging_fraction": 0.9,
              "bagging_freq": 5, "min_data_in_leaf": 50, "min_sum_hessian_in_leaf": 5.0, "num_threads": 2,
              "verbosity": -1}


def train_rows(I):
    """Training rows exactly as the frozen trainer builds them (k < 15): (X (rows x 18), episode index)."""
    r = np.flatnonzero(I.acc_row == 1)
    X = np.c_[I.acc_meta[r], I.acc_dyn[r]]
    return X, I.acc_ep[r]


def train_gbm(I, y_ep, seed=42, threads=2, rounds=2000, test_size=0.3):
    """Proxy GBM: same features/params as train_ap.GBAdmissionTrainer; 70/30 split by block (seeded)."""
    import lightgbm as lgb
    X, ep = train_rows(I)
    y = y_ep[ep].astype(float)
    blocks = I.block_ids()[ep]
    ub = np.unique(blocks)
    rng = np.random.RandomState(seed)
    test_b = set(rng.choice(ub, size=int(round(test_size * len(ub))), replace=False).tolist())
    te = np.array([b in test_b for b in blocks])
    p = dict(GBM_PARAMS, num_threads=threads, seed=seed)
    dtr = lgb.Dataset(X[~te], y[~te], feature_name=[f.replace("|", "_") for f in FEAT_NAMES])
    dte = lgb.Dataset(X[te], y[te], reference=dtr)
    bst = lgb.train(p, dtr, num_boost_round=rounds, valid_sets=[dte],
                    callbacks=[lgb.early_stopping(25, verbose=False)])
    return bst
