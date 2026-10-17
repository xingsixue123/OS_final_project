"""Analytic emulation of a trained admission GBM on the full trace (phase-1 q3 'cheap proxy', copied/extended):
simulator-style features of every GET access of the fullml instance (q3lib.sim_features, cached), plus the overlay's
`load`/`tod` columns (cachesim/load_features: same function the simulator uses), GBM scores, first-admission
emulation -> emulated write rate as a function of the threshold. Used ONLY to seed / steer the threshold search and
for mechanism statistics (first-access admission, peak-window admission); every reported P100/WR is a full simulation.
"""
import os

import numpy as np

import q3lib as QL
import wpcommon as C

_INST = {}


class InstEmu:
    def __init__(self, key):
        self.key = key
        self.I = QL.Inst(os.path.join(C.INST_DIR, f"fullml_{key}.npz"))     # WP3: configured source (test or dev)
        self.F18 = QL.sim_features(self.I, cache=os.path.join(C.WORK, "cache", f"simfeat_fullml_{key}.npz")).astype(float)
        trace = C.get_flag(C.JOBS[key]["baleen"]["sim_args"], "--trace")
        from BCacheSim.cachesim import load_features as LF
        self.LF = LF
        self.demand = LF.DemandLoad.from_trace(os.path.join(C.WORK, trace), 0.1)
        ts = self.I.acc_ts
        self.load = np.array([self.demand.load(t) for t in ts])
        self.tod = np.array([LF.tod(t) for t in ts])
        self.k0 = self.I.acc_k == 0

    def features(self, ap_subset):
        parts = (ap_subset or "meta+block+chunk").split("+")
        assert parts[:3] == ["meta", "block", "chunk"], ap_subset
        cols = [self.F18]
        for g in parts[3:]:
            cols.append(self.load if g == "load" else self.tod)
        return np.hstack(cols)

    def scores(self, model_path, ap_subset):
        import lightgbm as lgb
        return lgb.Booster(model_file=model_path).predict(self.features(ap_subset))

    def gmult(self, alpha, ref=20.0, window_min=10):
        if alpha is None:
            return np.ones(len(self.I.acc_ts))
        idx = self.LF.LOAD_WINDOWS_S.index(window_min * 60)
        x = np.maximum(self.load[:, idx], 1e-6)
        lo, hi = self.LF.LOAD_ADAPT_CLIP
        return np.clip((x / ref) ** float(alpha), lo, hi)

    def admit(self, g, theta, alpha=None):
        return g > theta * self.gmult(alpha)

    def wr(self, g, theta, alpha=None):
        kst = QL.first_admit(self.I, self.admit(g, theta, alpha))
        _, wch = QL.emulate_loads(self.I, kst)
        return C.TARGET_WR * wch / self.I.B

    def theta_for(self, g, emu_target, alpha=None, lo=0.0, hi=1.0, iters=30):
        """Emulated WR is non-increasing in theta: bisection for emu WR == emu_target."""
        for _ in range(iters):
            mid = 0.5 * (lo + hi)
            if self.wr(g, mid, alpha) > emu_target:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    def mechanism(self, g, theta, alpha, peak_window):
        a = self.admit(g, theta, alpha)
        m = self.I.acc_w == peak_window
        return dict(k0_adm=float(a[self.k0].mean()), all_adm=float(a.mean()),
                    peak_bigoff_share=float((self.F18[m, 4] > 8 * (1 << 20)).mean()) if m.any() else float("nan"),
                    peak_adm=float(a[m].mean()) if m.any() else float("nan"))


def get(key):
    if key not in _INST:
        _INST[key] = InstEmu(key)
    return _INST[key]
