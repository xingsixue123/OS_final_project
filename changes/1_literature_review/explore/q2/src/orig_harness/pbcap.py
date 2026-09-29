"""C3: capacity / eviction-age-coupled selection (computed in-module from the harness's episode data).

Occupancy model (the harness's own eviction-age assumption): an admitted episode e keeps its chunk range
(num_chunks, what the simulator's at_start prefetch writes) resident from its first access until
last access + EA (EA = rl.eviction_age_physical). occ_w(x) = sum_e O[e,w] x_e. The simulated LRU cache holds at
most Cap = 366.475 GB x 0.1% sample = 3002 chunks, so windows with occ_w > Cap evict early and lose planned hits
(Gate 0: corr(occ_w, sim - analytic residual) = 0.64 / 0.78 on Region7 / Region6 for Baleen's own selection).

C3L (classical reference, "LP/MILP with the occupancy rows"): epigraph LP + rows occ_w <= kappa*Cap, lexicographic
    max-DT stage, round down, occupancy-aware repair + fill.
C3  (capacity-coupled Ising): EIM-style replica exchange on LSE(L) + ALM budget hinge + occupancy hinge
    mu_o * sum_w max(0, occ_w - kappa*Cap) (native inequality terms), seeded by C3L; best feasible kept.
"""
import math
import time

import numpy as np
import scipy.sparse as sp
import highspy
import numba as nb

import pbcore as PC
import pbsolvers as PS

INF = highspy.kHighsInf
CAP_CHUNKS = 366.475 * 1024 * (0.1 / 100) / 0.125   # 128 KiB chunks at the 0.1% sample


def build_O(I):
    if hasattr(I, "O"):
        return I.O
    z = np.load(I.path)
    assert "nchunks" in z.files, "instance lacks nchunks/ea (re-dump with the current policy)"
    nch, ea = z["nchunks"].astype(float), float(z["ea"])
    ts0, te = z["ts0"], z["ts_end"]
    a = np.clip(((ts0 - I.t0) // 600).astype(np.int64), 0, I.m - 1)
    b = np.clip(((te + ea - I.t0) // 600).astype(np.int64), 0, I.m - 1)
    ln = b - a + 1
    rows = np.repeat(np.arange(I.n), ln)
    cols = np.concatenate([np.arange(x, y + 1) for x, y in zip(a, b)])
    vals = np.repeat(nch, ln)
    I.O = sp.csr_matrix((vals, (rows, cols)), shape=(I.n, I.m))
    return I.O


class CapView:
    def __init__(self, P, kappa):
        I = P.I
        O = build_O(I)
        self.O = O[P.free].tocsr()
        self.cap = kappa * CAP_CHUNKS - O.T @ P.forced.astype(float)


def lp_occ(P, cv, lexi=True, eps_rel=1e-6):
    t = time.time()
    var = PS._useful(P)
    info = {}

    def build(var, obj_sts, z_ub, zcost):
        lp = PS.build_epigraph(P, var, obj_sts=obj_sts, z_ub=z_ub, zcost=zcost)
        return lp

    def add_occ_rows(h, var):
        Ov = cv.O[var].tocsc().T.tocsr()     # m x nv
        m = Ov.shape[0]
        keep = np.flatnonzero(np.diff(Ov.indptr) > 0)
        for w in keep:
            r0, r1 = Ov.indptr[w], Ov.indptr[w + 1]
            h.addRow(-INF, float(cv.cap[w]), int(r1 - r0), Ov.indices[r0:r1].astype(np.int32), Ov.data[r0:r1])
        return len(keep)

    h = PS._highs()
    h.passModel(build(var, 0.0, None, 1.0))
    nrows = add_occ_rows(h, var)
    h.run()
    sol = np.array(h.getSolution().col_value)
    z = float(h.getInfo().objective_function_value)
    info.update(z_lp_occ=z, lp_occ_status=h.modelStatusToString(h.getModelStatus()), occ_rows=nrows)
    x = np.zeros(P.n)
    x[var] = sol[:len(var)]
    if lexi:
        var2 = np.union1d(np.flatnonzero((P.sts > 0) & (P.s <= P.B + 1e-9)), var)
        h2 = PS._highs()
        h2.passModel(build(var2, 1.0, z * (1 + eps_rel) + 1e-12, 0.0))
        add_occ_rows(h2, var2)
        h2.run()
        sol2 = np.array(h2.getSolution().col_value)
        x = np.zeros(P.n)
        x[var2] = sol2[:len(var2)]
        info["lp2_occ_status"] = h2.modelStatusToString(h2.getModelStatus())
    info["lp_occ_time"] = time.time() - t
    return x, info


def repair_occ(P, cv, xs, fill=True):
    """Round-down start assumed feasible. Peak-reducing adds + Baleen-order peak-preserving fill, each only if
    the budget AND every occupancy row stay satisfied."""
    Da, Dc = P.Da, P.Da.tocsc()
    O = cv.O
    x = (np.asarray(xs) > 0.5).astype(float)
    L = P.loads(x)
    occ = O.T @ x
    use = float(P.s @ x)
    s = P.s
    assert use <= P.B + 1e-6

    def occ_ok(e):
        r0, r1 = O.indptr[e], O.indptr[e + 1]
        return np.all(occ[O.indices[r0:r1]] + O.data[r0:r1] <= cv.cap[O.indices[r0:r1]] + 1e-9)

    def add(e):
        nonlocal use
        x[e] = 1.0
        use += s[e]
        r0, r1 = Da.indptr[e], Da.indptr[e + 1]
        L[Da.indices[r0:r1]] -= Da.data[r0:r1]
        r0, r1 = O.indptr[e], O.indptr[e + 1]
        occ[O.indices[r0:r1]] += O.data[r0:r1]

    # drop to satisfy occupancy if the start violates it (should not after round-down)
    n_add = 0
    for _ in range(100000):
        top = np.argsort(-L)[:8]
        pk = L[top[0]]
        if L[top[1]] >= pk - 1e-12:
            break
        w = top[0]
        col = Dc.indices[Dc.indptr[w]:Dc.indptr[w + 1]]
        val = Dc.data[Dc.indptr[w]:Dc.indptr[w + 1]]
        col = col[(x[col] < 0.5) & (s[col] <= P.B - use + 1e-9) & (val > 0)]
        best, bj = 0.0, -1
        for e in col:
            if not occ_ok(e):
                continue
            r0, r1 = Da.indptr[e], Da.indptr[e + 1]
            idx = Da.indices[r0:r1]
            newin = (L[idx] - Da.data[r0:r1]).max()
            out = -np.inf
            for t in top:
                if not np.any(idx == t):
                    out = L[t]
                    break
            red = pk - max(newin, out)
            if red > 1e-12 and red / max(s[e], 1e-12) > best:
                best, bj = red / max(s[e], 1e-12), e
        if bj < 0:
            break
        add(bj)
        n_add += 1
    n_fill = 0
    if fill:
        pk = L.max()
        for e in np.argsort(P.rank, kind="stable"):
            if x[e] > 0.5 or s[e] > P.B - use + 1e-9 or (P.sts[e] <= 0 and s[e] > 0):
                continue
            r0, r1 = Da.indptr[e], Da.indptr[e + 1]
            if r1 > r0 and (L[Da.indices[r0:r1]] - Da.data[r0:r1]).max() > pk + 1e-12:
                continue
            if not occ_ok(e):
                continue
            add(e)
            n_fill += 1
    return x, dict(n_add=n_add, n_fill=n_fill, occ_max=float((occ - cv.cap).max()))


# ------------------------------------------------------------------ Ising with occupancy hinge
@nb.njit(cache=True)
def _lse(L, g):
    mx = L.max()
    s = 0.0
    for w in range(L.shape[0]):
        s += np.exp(g * (L[w] - mx))
    return mx + np.log(s) / g


@nb.njit(cache=True)
def _flip(L, occ, cap, ip, ix, iv, op, ox, ov, e, sign):
    """Apply +/- episode e; return change of total occupancy excess."""
    for k in range(ip[e], ip[e + 1]):
        L[ix[k]] -= sign * iv[k]
    dH = 0.0
    for k in range(op[e], op[e + 1]):
        w = ox[k]
        before = max(0.0, occ[w] - cap[w])
        occ[w] += sign * ov[k]
        dH += max(0.0, occ[w] - cap[w]) - before
    return dH


@nb.njit(cache=True, parallel=True)
def _pt_occ(X, Ls, Os, Hs, uses, temps, B, s, cap, ip, ix, iv, op, ox, ov, wp, wi, lam, rho, hscale, mu_o,
            oscale, g, moves, seed, bfp, bfx):
    R, n = X.shape
    Es = np.empty(R)
    for r in nb.prange(R):
        np.random.seed(seed * 1000 + r)
        x = X[r]
        L = Ls[r]
        occ = Os[r]
        H = Hs[r]
        use = uses[r]
        T = temps[r]
        hb = max(0.0, use - B) * hscale
        E = _lse(L, g) + lam * hb + 0.5 * rho * hb * hb + mu_o * H * oscale
        bpk = bfp[r]
        for it in range(moves):
            w = np.argmax(L)
            rr = np.random.random()
            i = -1
            j = -1
            if rr < 0.45:
                cnt = wp[w + 1] - wp[w]
                if cnt == 0:
                    continue
                j = wi[wp[w] + np.random.randint(cnt)]
                if x[j] > 0.5:
                    continue
            elif rr < 0.9:
                i = np.random.randint(n)
                if x[i] < 0.5:
                    continue
                cnt = wp[w + 1] - wp[w]
                if cnt > 0 and np.random.random() < 0.7:
                    j = wi[wp[w] + np.random.randint(cnt)]
                    if x[j] > 0.5:
                        j = -1
            else:
                i = np.random.randint(n)
                if x[i] < 0.5:
                    continue
            dH = 0.0
            if j >= 0:
                dH += _flip(L, occ, cap, ip, ix, iv, op, ox, ov, j, 1.0)
            if i >= 0:
                dH += _flip(L, occ, cap, ip, ix, iv, op, ox, ov, i, -1.0)
            nuse = use + (s[j] if j >= 0 else 0.0) - (s[i] if i >= 0 else 0.0)
            nhb = max(0.0, nuse - B) * hscale
            En = _lse(L, g) + lam * nhb + 0.5 * rho * nhb * nhb + mu_o * (H + dH) * oscale
            dE = En - E
            if dE <= 0 or np.random.random() < np.exp(-dE / T):
                E = En
                use = nuse
                H += dH
                if j >= 0:
                    x[j] = 1.0
                if i >= 0:
                    x[i] = 0.0
                if use <= B and H <= 1e-9:
                    pk = L.max()
                    if pk < bpk - 1e-12:
                        bpk = pk
                        bfx[r, :] = x
            else:
                if j >= 0:
                    _flip(L, occ, cap, ip, ix, iv, op, ox, ov, j, -1.0)
                if i >= 0:
                    _flip(L, occ, cap, ip, ix, iv, op, ox, ov, i, 1.0)
        uses[r] = use
        Hs[r] = H
        Es[r] = E
        bfp[r] = bpk
    return Es


def c3l(P, k, a):
    cv = CapView(P, float(a.get("kappa", 1.0)))
    x, info = lp_occ(P, cv)
    xr = (x >= 1 - 1e-6).astype(float)
    xr, st = repair_occ(P, cv, xr, fill=True)
    info.update(st)
    return xr, info, cv


def c3(P, k, a):
    t0 = time.time()
    x, info, cv = c3l(P, k, a)
    info["peak_c3l"] = P.peak(x)
    Da, Dc, O = P.Da, P.Da.tocsc(), cv.O
    R = int(a.get("eim_replicas", 24))
    pk0 = P.peak(x)
    g = float(a.get("g_scale", 3000.0)) / pk0
    temps = np.geomspace(1e-6 * pk0, 3e-3 * pk0, R)
    X = np.tile(x, (R, 1)).astype(np.float64)
    Ls = np.tile(P.loads(x), (R, 1))
    occ0 = O.T @ x
    Os = np.tile(occ0, (R, 1))
    H0 = float(np.maximum(occ0 - cv.cap, 0).sum())
    Hs = np.full(R, H0)
    uses = np.full(R, float(P.s @ x))
    hscale = pk0 / max(P.B, 1.0) * 10
    oscale = pk0 / CAP_CHUNKS * float(a.get("occ_weight", 1.0))
    lam, rho, mu_o = 0.0, float(a.get("eim_rho", 50.0)), float(a.get("mu_o", 1.0))
    bfp = np.full(R, pk0 if H0 <= 1e-9 else np.inf)
    bfx = X.copy()
    args = (P.B, P.s.astype(np.float64), np.asarray(cv.cap, np.float64), Da.indptr.astype(np.int64),
            Da.indices.astype(np.int64), Da.data.astype(np.float64), O.indptr.astype(np.int64),
            O.indices.astype(np.int64), O.data.astype(np.float64), Dc.indptr.astype(np.int64),
            Dc.indices.astype(np.int64))
    rnd = swaps = 0
    while time.time() - t0 < float(a.get("eim_secs", 20.0)):
        rnd += 1
        Es = _pt_occ(X, Ls, Os, Hs, uses, temps, *args, lam, rho, hscale, mu_o, oscale, g,
                     int(a.get("eim_moves", 4000)), rnd, bfp, bfx)
        for r in range(rnd % 2, R - 1, 2):
            d = (1 / temps[r] - 1 / temps[r + 1]) * (Es[r] - Es[r + 1])
            if d >= 0 or np.random.random() < math.exp(d):
                for arr in (X, Ls, Os):
                    arr[[r, r + 1]] = arr[[r + 1, r]]
                uses[[r, r + 1]] = uses[[r + 1, r]]
                Hs[[r, r + 1]] = Hs[[r + 1, r]]
                swaps += 1
        lam += rho * max(0.0, uses[0] - P.B) * hscale
        mu_o *= 1.0 + 0.5 * float(Hs[0] > 1e-9)       # ALM-like escalation while the cold replica violates
    r = int(np.argmin(bfp))
    xb = bfx[r].copy() if np.isfinite(bfp[r]) and bfp[r] < P.peak(x) - 1e-12 else x
    xb, st = repair_occ(P, cv, xb, fill=True)
    info.update(eim_rounds=rnd, eim_swaps=swaps, eim_lambda=lam, eim_mu_o=mu_o, eim_secs=time.time() - t0,
                c3_improved=int(P.peak(xb) < info["peak_c3l"] - 1e-12))
    return xb, info


def make_level_solver(cand, a):
    if cand == "C3L":
        def f(P, k):
            x, info, _ = c3l(P, k, a)
            return x, info
        return f
    return lambda P, k: c3(P, k, a)
