"""Track B core (solver env): instance, formulations, shared repair, nested driver, evaluation.

NEVER imports highspy or ortools (they cannot share a process); solver modules import those themselves.

Instance = harness npz dumped by PolicyPeakBaleen (harness_eval/src/peakbaleen_policy.py, copied semantics):
  D (n x m) d(e,w) = DT saved in window w if episode e admitted; C (m) no-cache DT per window; active (m) objective
  windows (offline full trace: after day 1); s = rl.chunks_written; B = harness chunk budget at 35.599 MB/s;
  base_order = Baleen order. L_w(x) = C_w - sum_e d(e,w) x_e.

Formulations (objective on the active-window loads of a prefix set; smaller is better):
  F1   max_w L_w                                   (true min-max, current harness objective)
  F2a  mean of the top-k L_w (CVaR_k)               (linear soft peak)
  F2b  sum_w ((L_w - tau)_+ * US)^2 / ma            (quadratic soft peak, squared hinge; tau fixed per instance)
  F3   F2b on eviction-coupled loads (see q2f3.py)  (quadratic / bilinear)
Nested objective (what Q2 compares): mean over the levels f_k of obj(prefix of the final order within f_k B).
"""
import json
import math
import os
import time

import numpy as np
import scipy.sparse as sp
import numba as nb

US = 1.0 / 36 * (100.0 / 0.1) / 600 * 100          # util % per DT-second in a 600 s window (== sim scale)
LEVELS = [0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]
CAP_CHUNKS = 366.475 * 1024 * (0.1 / 100) / 0.125    # 128 KiB chunks at the 0.1% sample

FORM_TYP = {"F1": 0, "F2a": 1, "F2b": 2, "F3": 3}


class Instance:
    def __init__(self, path):
        self.path = path
        z = np.load(path, allow_pickle=False)
        self.z = z
        self.D = sp.csr_matrix((z["D_data"], z["D_indices"], z["D_indptr"]), shape=tuple(z["D_shape"]))
        self.n, self.m = self.D.shape
        self.C = z["C"].astype(float)
        self.active = z["active"].astype(bool)
        self.s = z["s"].astype(float)
        self.B = float(z["B"])
        self.base_order = z["base_order"].astype(np.int64)
        self.sts = np.asarray(self.D.sum(1)).ravel()
        self.act_idx = np.flatnonzero(self.active)
        Da = self.D[:, self.act_idx].tocsr()
        Da.eliminate_zeros()
        Da.sort_indices()
        self.Da = Da
        self.Ca = self.C[self.act_idx]
        self.ma = len(self.act_idx)
        self.rank = np.empty(self.n, np.int64)
        self.rank[self.base_order] = np.arange(self.n)
        self.name = os.path.basename(path).replace(".npz", "")

    def loads(self, x):
        return self.Ca - self.Da.T @ x

    def greedy_prefix(self, Bk):
        x = np.zeros(self.n)
        cs = np.cumsum(self.s[self.base_order])
        k = int(np.searchsorted(cs, Bk, side="right"))
        x[self.base_order[:k]] = 1.0
        return x


# ------------------------------------------------------------------ formulation spec
class Form:
    """name in F1/F2a/F2b(/F3); k for F2a; tau for F2b (absolute DT units, fixed per instance)."""
    def __init__(self, name, k=4, tau=0.0, extra=None):
        self.name = name
        self.typ = FORM_TYP[name]
        self.k = int(k)
        self.tau = float(tau)
        self.extra = extra or {}

    def obj(self, L):
        return float(obj_nb(np.ascontiguousarray(L, dtype=np.float64), self.typ if self.typ < 3 else 2, self.k,
                            self.tau))

    def report(self, v):
        """objective in reporting units: F1/F2a util %, F2b util%^2 per window."""
        if self.typ in (0, 1):
            return v * US
        return v * US * US

    def to_json(self):
        return dict(name=self.name, k=self.k, tau=self.tau, **self.extra)


def make_form(I, spec):
    """spec: dict(name=..., k=..., tau_rel=...). tau (F2b) = tau_rel * (Baleen-greedy peak at B), fixed per instance
    by a deterministic rule computed from the instance only."""
    name = spec["name"]
    if name == "F1":
        return Form("F1")
    if name == "F2a":
        return Form("F2a", k=int(spec.get("k", 4)))
    if name in ("F2b", "F3"):
        xg = I.greedy_prefix(I.B)
        pg = float(I.loads(xg).max())
        tau = float(spec.get("tau_rel", 0.8)) * pg
        return Form(name, tau=tau, extra={kk: v for kk, v in spec.items() if kk not in ("name",)})
    raise ValueError(name)


# ------------------------------------------------------------------ numba objective kernels
@nb.njit(cache=True)
def topk_sum(L, k):
    # partial selection of the k largest (k small): simple insertion buffer
    buf = np.full(k, -1e300)
    for w in range(L.shape[0]):
        v = L[w]
        if v > buf[k - 1]:
            j = k - 1
            while j > 0 and buf[j - 1] < v:
                buf[j] = buf[j - 1]
                j -= 1
            buf[j] = v
    s = 0.0
    for j in range(k):
        s += buf[j]
    return s


@nb.njit(cache=True)
def obj_nb(L, typ, k, tau):
    if typ == 0:
        return L.max()
    elif typ == 1:
        return topk_sum(L, k) / k
    else:
        s = 0.0
        for w in range(L.shape[0]):
            v = L[w] - tau
            if v > 0:
                s += v * v
        return s / L.shape[0]


@nb.njit(cache=True)
def _apply(L, ip, ix, iv, e, sign):
    for q in range(ip[e], ip[e + 1]):
        L[ix[q]] -= sign * iv[q]


@nb.njit(cache=True)
def delta_add(L, ip, ix, iv, e, typ, k, tau, cur):
    """objective change if e is added (sign=+1)"""
    if typ == 2:
        d = 0.0
        for q in range(ip[e], ip[e + 1]):
            w = ix[q]
            a = L[w] - tau
            b = L[w] - iv[q] - tau
            d += (b * b if b > 0 else 0.0) - (a * a if a > 0 else 0.0)
        return d / L.shape[0]
    _apply(L, ip, ix, iv, e, 1.0)
    v = obj_nb(L, typ, k, tau)
    _apply(L, ip, ix, iv, e, -1.0)
    return v - cur


@nb.njit(cache=True)
def window_weights(L, typ, k, tau, out):
    """marginal objective weight per window (for the budget-drop rule)"""
    m = L.shape[0]
    for w in range(m):
        out[w] = 0.0
    if typ == 0:
        out[np.argmax(L)] = 1.0
    elif typ == 1:
        Ls = L.copy()
        for j in range(k):
            a = np.argmax(Ls)
            out[a] = 1.0 / k
            Ls[a] = -1e300
    else:
        for w in range(m):
            v = L[w] - tau
            if v > 0:
                out[w] = 2.0 * v / m




@nb.njit(cache=True)
def _heap_push(hk, hv, size, key, val):
    i = size
    hk[i] = key
    hv[i] = val
    while i > 0:
        p = (i - 1) // 2
        if hk[p] <= hk[i]:
            break
        hk[p], hk[i] = hk[i], hk[p]
        hv[p], hv[i] = hv[i], hv[p]
        i = p
    return size + 1


@nb.njit(cache=True)
def _heap_pop(hk, hv, size):
    key = hk[0]
    val = hv[0]
    size -= 1
    hk[0] = hk[size]
    hv[0] = hv[size]
    i = 0
    while True:
        l = 2 * i + 1
        r = l + 1
        sm = i
        if l < size and hk[l] < hk[sm]:
            sm = l
        if r < size and hk[r] < hk[sm]:
            sm = r
        if sm == i:
            break
        hk[sm], hk[i] = hk[i], hk[sm]
        hv[sm], hv[i] = hv[i], hv[sm]
        i = sm
    return key, val, size


@nb.njit(cache=True)
def _lazy_adds(x, L, B, use, s, ip, ix, iv, wp, wi, wv, tau, max_adds):
    """exact lazy greedy for the squared hinge: add the fitting episode with the most negative d(obj)/s while < 0.
    Valid because an episode's gain can only shrink after other adds (loads fall, (L-tau)_+^2 convex)."""
    n = x.shape[0]
    hk = np.empty(n + 1)
    hv = np.empty(n + 1, np.int64)
    size = 0
    rem = B - use
    for e in range(n):
        if x[e] > 0.5 or s[e] > rem + 1e-9:
            continue
        d = delta_add(L, ip, ix, iv, e, 2, 1, tau, 0.0)
        if d < -1e-15:
            size = _heap_push(hk, hv, size, d / max(s[e], 1e-12), e)
    n_add = 0
    while size > 0 and n_add < max_adds:
        key, e, size = _heap_pop(hk, hv, size)
        if x[e] > 0.5 or s[e] > rem + 1e-9:
            continue
        d = delta_add(L, ip, ix, iv, e, 2, 1, tau, 0.0)
        if d >= -1e-15:
            continue
        kk = d / max(s[e], 1e-12)
        if size > 0 and kk > hk[0] + 1e-18:
            size = _heap_push(hk, hv, size, kk, e)
            continue
        x[e] = 1.0
        rem -= s[e]
        _apply(L, ip, ix, iv, e, 1.0)
        n_add += 1
    return n_add

@nb.njit(cache=True)
def repair_nb(x, L, B, s, sts, ip, ix, iv, wp, wi, wv, rank_order, typ, k, tau, do_fill, max_adds):
    """Shared repair (same for every solver of a formulation). In place on x (0/1 float64) and L.
    1) drop while over budget: selected episode with min (weighted saving)/s_e, weights = marginal objective weight
       per window (F1: argmax window only == harness rule; ties -> larger s_e);
    2) greedy improving adds: repeatedly add the budget-fitting episode with the most negative d(obj)/s_e among
       episodes touching the objective-relevant windows (F1: argmax; F2a: top-k; F2b: windows above tau);
    3) (do_fill) lexicographic tie-break: Baleen order, add every fitting episode with sts > 0 that does not
       worsen the objective.  Returns (use, n_drop, n_add, n_fill)."""
    n = x.shape[0]
    m = L.shape[0]
    use = 0.0
    for e in range(n):
        if x[e] > 0.5:
            use += s[e]
    wts = np.zeros(m)
    n_drop = 0
    while use > B + 1e-9:
        window_weights(L, typ, k, tau, wts)
        best = 1e300
        bj = -1
        for e in range(n):
            if x[e] < 0.5:
                continue
            v = 0.0
            for q in range(ip[e], ip[e + 1]):
                v += wts[ix[q]] * iv[q]
            key = v / max(s[e], 1e-12)
            if key < best - 1e-15 or (abs(key - best) <= 1e-15 and bj >= 0 and s[e] > s[bj]):
                best = key
                bj = e
        if bj < 0:
            break
        x[bj] = 0.0
        use -= s[bj]
        _apply(L, ip, ix, iv, bj, -1.0)
        n_drop += 1
    # phase 2: improving adds
    n_add = 0
    if typ == 2:
        n_add = _lazy_adds(x, L, B, use, s, ip, ix, iv, wp, wi, wv, tau, max_adds)
        use = 0.0
        for e in range(n):
            if x[e] > 0.5:
                use += s[e]
    else:
        mark = np.zeros(n, np.int64)
        stamp = 0
        cur = obj_nb(L, typ, k, tau)
        while n_add < max_adds:
            stamp += 1
            rem = B - use
            best = -1e-12
            bj = -1
            nrel = 1 if typ == 0 else k
            Ls = L.copy()
            for r in range(nrel):
                w = np.argmax(Ls)
                Ls[w] = -1e300
                for q in range(wp[w], wp[w + 1]):
                    e = wi[q]
                    if mark[e] == stamp:
                        continue
                    mark[e] = stamp
                    if x[e] > 0.5 or s[e] > rem + 1e-9 or wv[q] <= 0:
                        continue
                    dlt = delta_add(L, ip, ix, iv, e, typ, k, tau, cur)
                    sc = dlt / max(s[e], 1e-12)
                    if dlt < -1e-12 and sc < best:
                        best = sc
                        bj = e
            if bj < 0:
                break
            x[bj] = 1.0
            use += s[bj]
            _apply(L, ip, ix, iv, bj, 1.0)
            cur = obj_nb(L, typ, k, tau)
            n_add += 1
    n_fill = 0
    if do_fill:
        cur = obj_nb(L, typ, k, tau)
        pk = L.max()
        for t in range(rank_order.shape[0]):
            e = rank_order[t]
            if x[e] > 0.5 or s[e] > B - use + 1e-9:
                continue
            if sts[e] <= 0 and s[e] > 0:
                continue
            ok = True
            if typ == 0:
                for q in range(ip[e], ip[e + 1]):
                    if L[ix[q]] - iv[q] > pk + 1e-12:
                        ok = False
                        break
            elif typ == 2:
                if delta_add(L, ip, ix, iv, e, typ, k, tau, cur) > 1e-15:
                    ok = False
            else:
                # top-k mean can only get worse if some window rises (negative d)
                anyneg = False
                for q in range(ip[e], ip[e + 1]):
                    if iv[q] < 0:
                        anyneg = True
                        break
                if anyneg:
                    if delta_add(L, ip, ix, iv, e, typ, k, tau, cur) > 1e-12:
                        ok = False
            if not ok:
                continue
            x[e] = 1.0
            use += s[e]
            _apply(L, ip, ix, iv, e, 1.0)
            if typ != 0:
                cur = obj_nb(L, typ, k, tau)
            n_fill += 1
    return use, n_drop, n_add, n_fill


# ------------------------------------------------------------------ level sub-problem
class Sub:
    """Level problem: episodes `forced` are in; free vars = the rest; budget Bk (chunks)."""
    def __init__(self, I, Bk, forced, form):
        self.I = I
        self.form = form
        self.forced = forced.astype(bool)
        self.free = np.flatnonzero(~self.forced)
        xf = self.forced.astype(float)
        self.C = I.Ca - I.Da.T @ xf
        self.B = Bk - float(I.s @ xf)
        Da = I.Da[self.free].tocsr()
        Da.sort_indices()
        self.Da = Da
        self.s = I.s[self.free]
        self.sts = I.sts[self.free]
        self.rank = I.rank[self.free]
        self.n = len(self.free)
        self.ma = I.ma
        Dc = Da.tocsc()
        Dc.sort_indices()
        self.Dc = Dc
        self.ip = Da.indptr.astype(np.int64)
        self.ix = Da.indices.astype(np.int64)
        self.iv = Da.data.astype(np.float64)
        self.wp = Dc.indptr.astype(np.int64)
        self.wi = Dc.indices.astype(np.int64)
        self.wv = Dc.data.astype(np.float64)
        self.rank_order = np.argsort(self.rank, kind="stable").astype(np.int64)

    def loads(self, xs):
        return self.C - self.Da.T @ xs

    def obj(self, xs):
        return self.form.obj(self.loads(xs))

    def repair(self, xs, fill=True, max_adds=1_000_000):
        x = (np.asarray(xs) > 0.5).astype(np.float64)
        L = self.loads(x).astype(np.float64)
        f = self.form
        typ = f.typ if f.typ < 3 else 2
        use, nd, na, nf = repair_nb(x, L, self.B, self.s, self.sts, self.ip, self.ix, self.iv, self.wp, self.wi,
                                    self.wv, self.rank_order, typ, f.k, f.tau, fill, max_adds)
        return x, dict(n_drop=int(nd), n_add=int(na), n_fill=int(nf))

    def useful(self):
        pos = np.zeros(self.n, bool)
        rows = np.repeat(np.arange(self.n), np.diff(self.Da.indptr))
        pos[rows[self.Da.data > 0]] = True
        return np.flatnonzero(pos & (self.s <= self.B + 1e-9))

    def full(self, xs):
        x = self.forced.astype(float)
        x[self.free] = (np.asarray(xs) > 0.5)
        return x


def pgreedy(P):
    """peak-aware greedy: repair from the empty set (improving adds by d(obj)/s, then Baleen fill)."""
    return P.repair(np.zeros(P.n), fill=True)


# ------------------------------------------------------------------ nested driver with a global deadline
def nested_solve(I, form, level_solver, T_total, levels=LEVELS, t_start=None, weights=None, log=None):
    """Bottom-up nested prefix S_1 c S_2 c ... c S_K (S_k solved at f_k B with S_{k-1} forced).
    Level k gets deadline = now + remaining * w_k / sum_{j>=k} w_j. level_solver(P, k, deadline) -> (xs, info).
    Every level output goes through the shared repair (P.repair) before being frozen."""
    t_start = time.time() if t_start is None else t_start
    K = len(levels)
    weights = np.ones(K) if weights is None else np.asarray(weights, float)
    forced = np.zeros(I.n, bool)
    lvl_of = np.full(I.n, -1)
    per = []
    for k, f in enumerate(levels):
        now = time.time()
        rem = T_total - (now - t_start)
        dl = now + max(rem, 0.0) * weights[k] / weights[k:].sum()
        P = Sub(I, f * I.B, forced, form)
        t0 = time.time()
        xs, info = level_solver(P, k, dl)
        xr, st = P.repair(xs, fill=True)
        info = dict(info)
        info.update({"rep_" + a: b for a, b in st.items()})
        x = P.full(xr)
        assert I.s @ x <= f * I.B + 1e-6
        new = (x > 0.5) & ~forced
        lvl_of[new] = k
        forced = x > 0.5
        info.update(level=f, secs=time.time() - t0, obj=form.report(P.obj(xr)), n_sel=int(forced.sum()))
        per.append(info)
        if log:
            log(f"  L{k} f={f:.2f} obj={info['obj']:.4f} sel={info['n_sel']} {time.time() - t0:.2f}s")
    return forced.astype(float), lvl_of, per


def final_order(I, x, lvl_of):
    """Selected set in nested order (level, then Baleen rank), then the harness strict-prefix fill in Baleen order."""
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
    return np.r_[sel, np.asarray(fill, np.int64)].astype(np.int64), len(fill)


def nested_objective(I, form, order, levels=LEVELS):
    """obj of the prefix of `order` within f B for each level (what the simulator admits at cutoff f W)."""
    cs = np.cumsum(I.s[order])
    vals = []
    for f in levels:
        kk = int(np.searchsorted(cs, f * I.B + 1e-9, side="right"))
        x = np.zeros(I.n)
        x[order[:kk]] = 1.0
        vals.append(form.report(form.obj(I.loads(x))))
    return float(np.mean(vals)), vals


def peak_util(I, order, f=1.0):
    cs = np.cumsum(I.s[order])
    kk = int(np.searchsorted(cs, f * I.B + 1e-9, side="right"))
    x = np.zeros(I.n)
    x[order[:kk]] = 1.0
    L = I.loads(x)
    return float(L.max() * US), float(I.sts @ x)


# ------------------------------------------------------------------ model helpers shared by LP/MILP/CP-SAT/SCIP
def relevant_windows(P):
    """F2b: windows whose load can exceed tau (C_w plus all negative savings)."""
    neg = np.zeros(P.ma)
    np.add.at(neg, P.Da.indices[P.Da.data < 0], -P.Da.data[P.Da.data < 0])
    return np.flatnonzero(P.C + neg > P.form.tau)


def model_vars(P):
    """free vars that can improve the objective (positive saving in an objective-relevant window) and fit."""
    Da = P.Da
    rows = np.repeat(np.arange(P.n), np.diff(Da.indptr))
    pos = np.zeros(P.n, bool)
    if P.form.typ in (2, 3):
        mask = np.zeros(P.ma, bool)
        mask[relevant_windows(P)] = True
        pos[rows[(Da.data > 0) & mask[Da.indices]]] = True
    else:
        pos[rows[Da.data > 0]] = True
    return np.flatnonzero(pos & (P.s <= P.B + 1e-9))


def lp_start_scipy(P, deadline, J=12):
    """LP relaxation (same model as q2lp, no lexicographic stage) solved with scipy's bundled HiGHS (usable in
    processes that import ortools), rounded down and repaired -- the 'lp' start for CP-SAT / SCIP."""
    import scipy.optimize as so
    var = model_vars(P)
    if len(var) == 0:
        return None
    Da = P.Da[var]
    nv = len(var)
    s = P.s[var]
    typ = P.form.typ if P.form.typ < 3 else 2
    if typ == 0:
        ma = P.ma
        A = sp.hstack([-Da.T.tocsr(), -sp.csr_matrix(np.ones((ma, 1)))])     # -(D x) - z <= -C
        A = sp.vstack([A, sp.hstack([sp.csr_matrix(s[None, :]), sp.csr_matrix((1, 1))])]).tocsr()
        b = np.r_[-P.C, P.B]
        c = np.r_[np.zeros(nv), 1.0]
        bounds = [(0, 1)] * nv + [(None, None)]
    elif typ == 1:
        ma = P.ma
        k = float(P.form.k)
        A = sp.hstack([-Da.T.tocsr(), -sp.csr_matrix(np.ones((ma, 1))), -sp.identity(ma, format="csr")])
        A = sp.vstack([A, sp.hstack([sp.csr_matrix(s[None, :]), sp.csr_matrix((1, 1 + ma))])]).tocsr()
        b = np.r_[-P.C, P.B]
        c = np.r_[np.zeros(nv), 1.0, np.full(ma, 1.0 / k)]
        bounds = [(0, 1)] * nv + [(None, None)] + [(0, None)] * ma
    else:
        rw = relevant_windows(P)
        mr = len(rw)
        umax = max(float((P.C[rw] - P.form.tau).max()), 1e-9) * 1.05
        a = np.linspace(0.0, umax, int(J))
        Dr = Da[:, rw].T.tocsr()
        I_ = sp.identity(mr, format="csr")
        rows_load = sp.hstack([-Dr, -I_, sp.csr_matrix((mr, mr))])            # -(Dx) - u <= -(C - tau)
        rows_tan = sp.hstack([sp.csr_matrix((mr * len(a), nv)), sp.vstack([2.0 * aj * I_ for aj in a]),
                              sp.vstack([-I_ for _ in a])])                  # 2 a u - t <= a^2
        rows_b = sp.hstack([sp.csr_matrix(s[None, :]), sp.csr_matrix((1, 2 * mr))])
        A = sp.vstack([rows_load, rows_tan, rows_b]).tocsr()
        b = np.r_[-(P.C[rw] - P.form.tau), np.repeat(a ** 2, mr), P.B]
        c = np.r_[np.zeros(nv), np.zeros(mr), np.full(mr, 1.0 / P.ma)]
        bounds = [(0, 1)] * nv + [(0, None)] * (2 * mr)
    tl = max(0.9 * (deadline - time.time()), 0.05)
    r = so.linprog(c, A_ub=A, b_ub=b, bounds=bounds, method="highs-ds", options=dict(time_limit=tl))
    if r.status != 0 or r.x is None:
        return None
    x = np.zeros(P.n)
    x[var] = r.x[:nv]
    return x
