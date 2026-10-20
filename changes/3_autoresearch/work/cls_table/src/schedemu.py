"""WP10 schedule emulator: fast replay of "trained admission GBM + threshold schedule -> per-window load" on the
day-1 (training) window or the full trace. Built on the WP2/WP3 emulator (src/emu.py: simulator-style features of every
GET access of the fullml instance, the overlay's causal load_10m, GBM scores; q3lib.first_admit/emulate_loads
semantics: episode e is admitted at its first access k with score > theta * g_k; later accesses hit, the admission
access fetches the whole episode range).

Exact hard repair of the write budget: with r_k = score_k / g_k, episode e is admitted iff M_e = max_k r_k > theta, so
the theta that spends at most W chunks is read off the sorted episode maxima (no bisection). Then the admitted
episode's first access with r > theta gives its load contributions.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "q3lib"))

try:                                   # solver env (PT); the Baleen env has no numba -> numpy path (same semantics)
    import numba as nb
    HAVE_NB = True
except ImportError:
    HAVE_NB = False

import q3lib as QL
try:
    import wpcommon as C
    TARGET_WR = C.TARGET_WR
except Exception:                      # solver env: wpcommon needs nothing env-specific, but keep this standalone-safe
    C = None
    TARGET_WR = 35.599

US = QL.US
DAY1_W = 144


def _ep_max_np(r, starts):
    return np.maximum.reduceat(r, starts[:-1])


def _loads_np(r, starts, theta, M, acc_w, stc, st_full, C0, m, ep_of):
    adm = r > theta
    idx = np.flatnonzero(adm)
    L = C0.copy()
    if len(idx) == 0:
        return L
    e = ep_of[idx]
    first = idx[np.r_[True, e[1:] != e[:-1]]]               # first admitted access per admitted episode
    kfirst = np.full(len(starts) - 1, np.iinfo(np.int64).max)
    kfirst[ep_of[first]] = first
    kf = kfirst[ep_of]
    pos = np.arange(len(r))
    after = pos > kf
    at = pos == kf
    contrib = np.where(after, stc, 0.0) + np.where(at, stc - st_full[ep_of], 0.0)
    ok = acc_w < m
    L -= np.bincount(acc_w[ok], weights=contrib[ok], minlength=m)[:m]
    return L


def _ep_max(r, starts):
    if HAVE_NB:
        return _ep_max_nb(r, starts)
    return _ep_max_np(r, starts)


def _loads(r, starts, theta, M, acc_w, stc, st_full, C0, m, ep_of=None):
    if HAVE_NB:
        return _loads_nb(r, starts, theta, M, acc_w, stc, st_full, C0, m)
    return _loads_np(r, starts, theta, M, acc_w, stc, st_full, C0, m, ep_of)


def _njit(f):
    return nb.njit(cache=True)(f) if HAVE_NB else f


@_njit
def _ep_max_nb(r, starts):
    n = starts.shape[0] - 1
    M = np.empty(n)
    for e in range(n):
        m = -1e300
        for i in range(starts[e], starts[e + 1]):
            if r[i] > m:
                m = r[i]
        M[e] = m
    return M


@_njit
def _loads_nb(r, starts, theta, M, acc_w, stc, st_full, C0, m):
    """Per-window loads (DT seconds) with admission r > theta; returns (L, written chunks are computed outside)."""
    L = C0.copy()
    n = starts.shape[0] - 1
    for e in range(n):
        if M[e] <= theta:
            continue
        a, b = starts[e], starts[e + 1]
        k = a
        while k < b and r[k] <= theta:
            k += 1
        if k >= b:
            continue
        w = acc_w[k]
        if w < m:
            L[w] -= stc[k] - st_full[e]
        for j in range(k + 1, b):
            w = acc_w[j]
            if w < m:
                L[w] -= stc[j]
    return L


class SchedEmu:
    """Replay on a subset of episodes/accesses. scope='day1': only accesses in windows < 144 may admit (and only
    day-1 windows are scored); scope='full': every access may admit, windows >= 144 are scored."""

    def __init__(self, E, scope="day1"):
        I = E.I
        self.E, self.I, self.scope = E, I, scope
        self.load10 = E.load[:, 0].astype(float)          # causal trailing 10-min GET demand (util %)
        acc_ok = I.acc_w < DAY1_W if scope == "day1" else np.ones(I.n_acc, bool)
        # keep episodes with >= 1 admissible access; accesses of kept episodes in episode-major order
        ep_has = np.zeros(I.n, bool)
        ep_has[I.acc_ep[acc_ok]] = True
        keep_acc = ep_has[I.acc_ep]
        self.idx = np.flatnonzero(keep_acc)                # flat (episode-major) access indices
        ep = I.acc_ep[self.idx]
        self.eps = np.flatnonzero(ep_has)
        new_id = -np.ones(I.n, np.int64)
        new_id[self.eps] = np.arange(len(self.eps))
        e2 = new_id[ep]
        assert np.all(np.diff(e2) >= 0)
        self.starts = np.searchsorted(e2, np.arange(len(self.eps) + 1)).astype(np.int64)
        self.ep_of = e2.astype(np.int64)
        self.admissible = acc_ok[self.idx]
        self.acc_w = I.acc_w[self.idx].astype(np.int64)
        self.stc = QL.st(1, I.acc_nch[self.idx].astype(float))
        self.st_full = QL.st(1, I.nchunks[self.eps].astype(float))
        self.nch = I.nchunks[self.eps].astype(float)
        self.m = DAY1_W if scope == "day1" else I.m
        self.C0 = I.C[:self.m].astype(float).copy()
        self.win = np.arange(self.m) < DAY1_W if scope == "day1" else np.arange(self.m) >= DAY1_W
        self.load_sub = self.load10[self.idx]
        dur = float(I.z["duration"])
        self.frac = (DAY1_W * 600.0) / dur if scope == "day1" else 1.0
        self.B = float(I.B)

    # ---------------------------------------------------------------- core
    def r_of(self, score_sub, g_sub):
        r = score_sub / g_sub
        return np.where(self.admissible, r, -1e300)

    def theta_for_budget(self, M, W):
        """largest admitted set (by episode maxima) with written chunks <= W -> theta (admit iff M > theta)."""
        order = np.argsort(-M, kind="stable")
        cs = np.cumsum(self.nch[order])
        j = int(np.searchsorted(cs, W, side="right"))      # first j episodes fit
        if j >= len(order):
            return -1e299
        th = M[order[j]]
        return th

    def run(self, score_sub, g_sub, W=None, theta=None):
        r = self.r_of(score_sub, g_sub)
        M = _ep_max(r, self.starts)
        if theta is None:
            theta = self.theta_for_budget(M, W)
        L = _loads(r, self.starts, float(theta), M, self.acc_w, self.stc, self.st_full, self.C0, self.m, self.ep_of)
        wch = float(self.nch[M > theta].sum())
        Lu = L[self.win] * US
        return dict(theta=float(theta), wch=wch, peak=float(Lu.max()), top5=float(np.sort(Lu)[::-1][:5].mean()),
                    L=L)

    def wr_emu(self, wch):
        return TARGET_WR * wch / (self.B * self.frac)

    def budget_at_emu_wr(self, score_sub, emu_wr_target, g_sub=None):
        """Written chunks of the schedule g (default plain) at the theta whose emulated WR equals the target."""
        g_sub = np.ones(len(self.idx)) if g_sub is None else g_sub
        W = emu_wr_target * self.B * self.frac / TARGET_WR
        return self.run(score_sub, g_sub, W=W)


def powerlaw_g(load, alpha, ref=20.0):
    if alpha is None:
        return np.ones_like(load)
    return np.clip((np.maximum(load, 1e-6) / ref) ** float(alpha), 0.25, 4.0)


def table_g(load, edges, mult):
    return np.asarray(mult, float)[np.searchsorted(np.asarray(edges, float), load, side="right")]
