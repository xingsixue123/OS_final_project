"""Core of the PeakBaleen solvers (solver env): instance, evaluation, repair, nested driver, fill.

Instance (from the Policy's npz, harness units):
  D (n x m CSR): d(e,w) DT saved in window w if episode e admitted;  C (m): no-cache DT per window
  active (m): windows in the objective (offline full trace: w >= 144, i.e. after day 1; day-1 instance: all)
  s (n): rl.chunks_written (harness write units);  B: largest chunk budget with WR < target (label rule)
  base_order: Baleen's order (score = service_time_saved / chunks_written, argsort desc)
Objective: min_x max_{w active} L_w,  L = C - D^T x,  s^T x <= B, x binary.
"""
import json
import time

import numpy as np
import scipy.sparse as sp


def util_scale(sample_ratio=0.1, disks=36, dur=600):
    """DT seconds per window -> utilisation % (episodes.st_to_util(.)*100)."""
    return 1.0 / disks * (100.0 / sample_ratio) / dur * 100   # upsample x1000 (0.1% sample), in %


class Instance:
    def __init__(self, path):
        self.path = path
        z = np.load(path, allow_pickle=False)
        self.D = sp.csr_matrix((z["D_data"], z["D_indices"], z["D_indptr"]), shape=tuple(z["D_shape"]))
        self.n, self.m = self.D.shape
        self.C = z["C"].astype(float)
        self.active = z["active"].astype(bool)
        self.s = z["s"].astype(float)
        self.B = float(z["B"])
        self.base_order = z["base_order"].astype(np.int64)
        self.base_score = z["base_score"].astype(float)
        self.keys = z["keys"]
        self.ts0 = z["ts0"]
        self.t0 = float(z["t0"])
        self.sts = np.asarray(self.D.sum(1)).ravel()          # total DT saved (all windows) = harness sts
        self.act_idx = np.flatnonzero(self.active)
        self.Da = self.D[:, self.act_idx].tocsr()              # objective windows only
        self.Da.eliminate_zeros()
        self.Ca = self.C[self.act_idx]
        self.ma = len(self.act_idx)
        self.rank = np.empty(self.n, np.int64)
        self.rank[self.base_order] = np.arange(self.n)
        self.US = util_scale()

    # ---------------- evaluation
    def loads(self, x):
        return self.Ca - self.Da.T @ x

    def peak(self, x):
        return float(self.loads(x).max())

    def all_loads(self, x):
        return self.C - self.D.T @ x

    def evaluate(self, x):
        L = self.loads(x)
        top = np.sort(L)[::-1]
        return dict(peak=float(top[0]), peak_util=float(top[0] * self.US), top5=float(top[:5].mean() * self.US),
                    p99=float(np.percentile(L, 99) * self.US), mean=float(L.mean() * self.US),
                    argmax=int(self.act_idx[int(np.argmax(L))]), use=float(self.s @ x), B=self.B,
                    n_sel=int((x > 0.5).sum()), sts=float(self.sts @ x))


class Sub:
    """Reduced problem after forcing `forced` episodes in, with budget Bk. Free vars = `free` indices."""
    def __init__(self, I, Bk, forced, free=None):
        self.I = I
        self.forced = forced.astype(bool)
        if free is None:
            free = np.flatnonzero(~self.forced)
        self.free = np.asarray(free, np.int64)
        xf = self.forced.astype(float)
        self.C = I.Ca - I.Da.T @ xf
        self.B = Bk - float(I.s @ xf)
        self.Da = I.Da[self.free].tocsr()
        self.D = I.D[self.free].tocsr()
        self.s = I.s[self.free]
        self.sts = I.sts[self.free]
        self.rank = I.rank[self.free]
        self.n = len(self.free)
        self.ma = I.ma

    def full(self, xs):
        x = self.forced.astype(float)
        x[self.free] = np.asarray(xs) > 0.5
        return x

    def loads(self, xs):
        return self.C - self.Da.T @ xs

    def peak(self, xs):
        return float(self.loads(xs).max())


# ------------------------------------------------------------------ greedy / repair / fill
def greedy_prefix(I, Bk, forced):
    """Baleen strict prefix of base_order (forced first) within Bk -- the harness prefix rule."""
    x = forced.astype(float).copy()
    use = float(I.s @ x)
    for e in I.base_order:
        if x[e] > 0.5:
            continue
        if use + I.s[e] > Bk:
            break
        x[e] = 1.0
        use += I.s[e]
    return x


def repair(P, xs, fill=True, max_iter=100000):
    """Generic repair on a Sub problem (free vars):
    1) drop while over budget: selected episode with min d(e,w*)/s_e at the peak window w* (ties -> larger s)
    2) add while it strictly reduces the peak: best (peak reduction)/s_e among episodes covering w*
    3) (fill=True) lexicographic tie-break: in Baleen order, add every episode that fits and does not raise the
       peak (maximizes DT saved at the reached peak, approximately)."""
    Da = P.Da
    Dc = Da.tocsc()
    x = (np.asarray(xs) > 0.5).astype(float)
    L = P.loads(x)
    use = float(P.s @ x)
    s = P.s
    stats = dict(n_drop=0, n_add=0, n_fill=0)
    it = 0
    while use > P.B + 1e-9 and it < max_iter:
        it += 1
        w = int(np.argmax(L))
        sel = np.flatnonzero(x > 0.5)
        dw = np.asarray(Dc[:, w].todense()).ravel()[sel]
        key = dw / np.maximum(s[sel], 1e-12)
        cand = np.flatnonzero(key == key.min())
        e = sel[cand[np.argmax(s[sel[cand]])]]
        x[e] = 0.0
        use -= s[e]
        r0, r1 = Da.indptr[e], Da.indptr[e + 1]
        L[Da.indices[r0:r1]] += Da.data[r0:r1]
        stats["n_drop"] += 1
    # phase 2
    while it < max_iter:
        it += 1
        rem = P.B - use
        top = np.argsort(-L)[:8]
        pk = L[top[0]]
        if L[top[1]] >= pk - 1e-12:
            break
        w = top[0]
        c0, c1 = Dc.indptr[w], Dc.indptr[w + 1]
        col = Dc.indices[c0:c1]
        val = Dc.data[c0:c1]
        ok = (x[col] < 0.5) & (s[col] <= rem + 1e-9) & (val > 0)
        col = col[ok]
        if len(col) == 0:
            break
        best, bestj, bestred = -1.0, -1, 0.0
        for e in col:
            r0, r1 = Da.indptr[e], Da.indptr[e + 1]
            idx = Da.indices[r0:r1]
            newin = (L[idx] - Da.data[r0:r1]).max()
            out = -np.inf
            for t in top:
                if not np.any(idx == t):
                    out = L[t]
                    break
            if out == -np.inf:
                out = np.max(np.delete(L, idx)) if len(idx) < len(L) else -np.inf
            red = pk - max(newin, out)
            sc = red / max(s[e], 1e-12)
            if red > 1e-12 and sc > best:
                best, bestj, bestred = sc, e, red
        if bestj < 0:
            break
        e = bestj
        x[e] = 1.0
        use += s[e]
        r0, r1 = Da.indptr[e], Da.indptr[e + 1]
        L[Da.indices[r0:r1]] -= Da.data[r0:r1]
        stats["n_add"] += 1
    if fill:
        x, L, use, nf = peak_preserving_fill(P, x, L, use)
        stats["n_fill"] = nf
    return x, stats


def peak_preserving_fill(P, x, L=None, use=None, pk=None):
    """Walk free vars in Baleen order; add each that fits the budget and does not raise max(L)."""
    Da = P.Da
    if L is None:
        L = P.loads(x)
    if use is None:
        use = float(P.s @ x)
    if pk is None:
        pk = L.max()
    nf = 0
    order = np.argsort(P.rank, kind="stable")
    for e in order:
        if x[e] > 0.5 or P.s[e] > P.B - use + 1e-9:
            continue
        if P.sts[e] <= 0 and P.s[e] > 0:
            continue    # never admit an episode with non-positive total saving just to fill
        r0, r1 = Da.indptr[e], Da.indptr[e + 1]
        if r1 > r0:
            idx = Da.indices[r0:r1]
            if (L[idx] - Da.data[r0:r1]).max() > pk + 1e-12:
                continue
            L[idx] -= Da.data[r0:r1]
        x[e] = 1.0
        use += P.s[e]
        nf += 1
    return x, L, use, nf


# ------------------------------------------------------------------ nested driver
def nested_solve(I, solve_level, levels, log=print):
    """Bottom-up nested prefix: S_1 at f_1 B, S_2 ⊇ S_1 at f_2 B, ..., S_K at B (f_K = 1).
    Returns x (top level), nested order of S_K and per-level stats."""
    forced = np.zeros(I.n, bool)
    lvl_of = np.full(I.n, -1)
    per = []
    for k, f in enumerate(levels):
        Bk = f * I.B
        t = time.time()
        P = Sub(I, Bk, forced)
        xs, st = solve_level(P, k)
        x = P.full(xs)
        assert I.s @ x <= Bk + 1e-6, (I.s @ x, Bk)
        new = (x > 0.5) & ~forced
        lvl_of[new] = k
        forced = x > 0.5
        ev = I.evaluate(x)
        ev.update(level=f, secs=time.time() - t, **{k_: v for k_, v in st.items() if np.isscalar(v)})
        per.append(ev)
        log(f"  level {f:.3f}: peak={ev['peak_util']:.3f}% use={ev['use'] / I.B:.4f}B n_sel={ev['n_sel']} "
            f"({ev['secs']:.1f}s) {json.dumps({k_: v for k_, v in st.items() if np.isscalar(v)})}")
    x = forced.astype(float)
    return x, lvl_of, per


def final_order(I, x, lvl_of):
    """Selected set in nested order (by level, then Baleen rank), then harness strict-prefix fill in Baleen
    order at B (so the prefix rule at W reproduces the final set exactly)."""
    sel = np.flatnonzero(x > 0.5)
    sel = sel[np.lexsort((I.rank[sel], lvl_of[sel]))]
    use = float(I.s[sel].sum())
    fill = []
    in_sel = np.zeros(I.n, bool)
    in_sel[sel] = True
    for e in I.base_order:
        if in_sel[e]:
            continue
        if use + I.s[e] > I.B:
            break
        fill.append(e)
        use += I.s[e]
    order_sel = np.r_[sel, np.asarray(fill, np.int64)].astype(np.int64)
    xf = np.zeros(I.n)
    xf[order_sel] = 1
    return order_sel, xf, len(fill)
