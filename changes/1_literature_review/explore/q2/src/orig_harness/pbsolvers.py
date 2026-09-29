"""Classical arms on a Sub problem: epigraph LP (+ lexicographic stage), MILP polish, true-objective SA."""
import time

import numpy as np
import scipy.sparse as sp
import highspy
import numba as nb

INF = highspy.kHighsInf


def _useful(P):
    """Free vars with any positive saving in an objective window (only these can lower the peak)."""
    Da = P.Da
    pos = np.zeros(P.n, bool)
    rows = np.repeat(np.arange(P.n), np.diff(Da.indptr))
    pos[rows[Da.data > 0]] = True
    return np.flatnonzero(pos & (P.s <= P.B + 1e-9))


def _highs(threads=1, time_limit=None, seed=0, verbose=False):
    h = highspy.Highs()
    h.setOptionValue("output_flag", bool(verbose))
    h.setOptionValue("threads", 1)   # HiGHS: thread count must stay constant per process
    h.setOptionValue("random_seed", int(seed))
    if time_limit is not None:
        h.setOptionValue("time_limit", float(time_limit))
    return h


def build_epigraph(P, var, integer=False, obj_sts=0.0, z_ub=None, zcost=1.0, topk=None):
    """min zcost*z - obj_sts * sts.x   s.t. (Da^T x)_w + z >= C_w (w active), s.x <= B, 0<=x<=1.
    topk: if set, objective = mean of top-k loads via CVaR form: min t + (1/k) sum u_w, u_w >= L_w - t."""
    Da = P.Da[var]
    nv = len(var)
    ma = P.ma
    lp = highspy.HighsLp()
    A_x = sp.vstack([Da.T.tocsr(), sp.csr_matrix(P.s[var][None, :])]).tocsc()
    if topk is None:
        ncol = nv + 1
        cost = np.r_[-obj_sts * P.sts[var], zcost]
        lower = np.r_[np.zeros(nv), -INF]
        upper = np.r_[np.ones(nv), INF if z_ub is None else z_ub]
        zcol = sp.csc_matrix((np.ones(ma), (np.arange(ma), np.zeros(ma, int))), shape=(ma + 1, 1))
        A = sp.hstack([A_x, zcol]).tocsc()
        row_lo = np.r_[P.C, -INF]
        row_hi = np.r_[np.full(ma, INF), P.B]
    else:
        # vars: x (nv), t (1), u (ma);  rows: Da^T x + t + u_w >= C_w ; s.x <= B
        k = float(topk)
        ncol = nv + 1 + ma
        cost = np.r_[-obj_sts * P.sts[var], zcost, np.full(ma, zcost / k)]
        lower = np.r_[np.zeros(nv), -INF, np.zeros(ma)]
        upper = np.r_[np.ones(nv), INF, np.full(ma, INF)]
        tcol = sp.csc_matrix((np.ones(ma), (np.arange(ma), np.zeros(ma, int))), shape=(ma + 1, 1))
        ucol = sp.vstack([sp.identity(ma, format="csc"), sp.csc_matrix((1, ma))]).tocsc()
        A = sp.hstack([A_x, tcol, ucol]).tocsc()
        row_lo = np.r_[P.C, -INF]
        row_hi = np.r_[np.full(ma, INF), P.B]
    lp.num_col_ = ncol
    lp.num_row_ = ma + 1
    lp.col_cost_ = cost
    lp.col_lower_ = lower
    lp.col_upper_ = upper
    lp.row_lower_ = row_lo
    lp.row_upper_ = row_hi
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = A.indptr.astype(np.int32)
    lp.a_matrix_.index_ = A.indices.astype(np.int32)
    lp.a_matrix_.value_ = A.data.astype(float)
    if integer:
        lp.integrality_ = [highspy.HighsVarType.kInteger] * nv + [highspy.HighsVarType.kContinuous] * (ncol - nv)
    return lp


def solve_lp(P, var=None, lexi=True, eps_rel=1e-6, threads=1, topk=None):
    """Stage 1: z_LP = min peak (or top-k mean).  Stage 2 (lexi): max DT saved s.t. objective <= z_LP (1+eps)."""
    t = time.time()
    if var is None:
        var = _useful(P)
    h = _highs(threads)
    h.passModel(build_epigraph(P, var, topk=topk))
    h.run()
    sol = np.array(h.getSolution().col_value)
    x = np.zeros(P.n)
    x[var] = sol[:len(var)]
    z = float(h.getInfo().objective_function_value)
    info = dict(z_lp=z, lp_status=h.modelStatusToString(h.getModelStatus()), n_var=len(var),
                n_frac=int(((sol[:len(var)] > 1e-6) & (sol[:len(var)] < 1 - 1e-6)).sum()))
    # reduced costs of x (for pegging in C5)
    rc = np.zeros(P.n)
    rc[var] = np.array(h.getSolution().col_dual)[:len(var)]
    if lexi:
        var2 = np.flatnonzero((P.sts > 0) & (P.s <= P.B + 1e-9))
        var2 = np.union1d(var2, var)
        if topk is None:
            lp2 = build_epigraph(P, var2, obj_sts=1.0, z_ub=z * (1 + eps_rel) + 1e-12, zcost=0.0)
        else:
            # keep the top-k objective bounded via an extra row: t + (1/k) sum u <= z(1+eps)
            lp2 = build_epigraph(P, var2, obj_sts=1.0, zcost=0.0, topk=topk)
        h2 = _highs(threads)
        h2.passModel(lp2)
        if topk is not None:
            nv2 = len(var2)
            ma = P.ma
            idx = np.r_[nv2, nv2 + 1 + np.arange(ma)].astype(np.int32)
            val = np.r_[1.0, np.full(ma, 1.0 / topk)]
            h2.addRow(-INF, z * (1 + eps_rel) + 1e-12, len(idx), idx, val)
        h2.run()
        sol2 = np.array(h2.getSolution().col_value)
        x = np.zeros(P.n)
        x[var2] = sol2[:len(var2)]
        info["lp2_status"] = h2.modelStatusToString(h2.getModelStatus())
    info["lp_time"] = time.time() - t
    return x, info, rc


def solve_milp(P, time_limit, x0=None, var=None, threads=1, seed=0, eps_tie=1e-4):
    """MILP polish: min z - eps * sts.x/sum(sts)*z0 over useful vars, warm start x0."""
    t = time.time()
    if var is None:
        var = _useful(P)
    z0 = P.peak(x0) if x0 is not None else float(P.C.max())
    denom = max(float(P.sts[var].clip(min=0).sum()), 1e-12)
    h = _highs(threads, time_limit=time_limit, seed=seed)
    h.passModel(build_epigraph(P, var, integer=True, obj_sts=eps_tie * z0 / denom))
    if x0 is not None:
        s0 = highspy.HighsSolution()
        xv = (np.asarray(x0)[var] > 0.5).astype(float)
        L = P.C - P.Da[var].T @ xv
        s0.col_value = list(np.r_[xv, L.max()])
        s0.value_valid = True
        try:
            h.setSolution(s0)
        except Exception as ex:  # pragma: no cover
            print("setSolution failed:", ex)
    h.run()
    info = h.getInfo()
    status = h.modelStatusToString(h.getModelStatus())
    x = None
    if info.primal_solution_status == 2:
        sol = np.array(h.getSolution().col_value)
        x = np.zeros(P.n)
        x[var] = (sol[:len(var)] > 0.5)
    return x, dict(milp_status=status, mip_bound=float(info.mip_dual_bound), mip_gap=float(info.mip_gap),
                   milp_time=time.time() - t, nodes=int(info.mip_node_count))


# ------------------------------------------------------------------ true-objective SA (numba)
@nb.njit(cache=True)
def _lse(L, g):
    mx = L.max()
    s = 0.0
    for w in range(L.shape[0]):
        s += np.exp(g * (L[w] - mx))
    return mx + np.log(s) / g


@nb.njit(cache=True)
def _app(L, ip, ix, iv, e, sign):
    for k in range(ip[e], ip[e + 1]):
        L[ix[k]] -= sign * iv[k]


@nb.njit(cache=True)
def _topk(L, K, out):
    Ls = L.copy()
    for k in range(K):
        j = np.argmax(Ls)
        out[k] = j
        Ls[j] = -1e300


@nb.njit(cache=True)
def sa_true(x, L, use, B, s, sts, ip, ix, iv, wp, wi, cand_mask, n_moves, T0, T1, g, lam_sts, seed, topk_obj):
    """Budget-hard SA on F = LSE_g(L) (topk_obj=0) or mean-of-top-k (topk_obj=k) minus lam_sts*sts.x.
    cand_mask: vars allowed to change. Returns best x by (true objective, then -sts)."""
    np.random.seed(seed)
    n = x.shape[0]
    sel = np.empty(n, np.int64)
    pos = -np.ones(n, np.int64)
    ns = 0
    for e in range(n):
        if x[e] > 0.5 and cand_mask[e]:
            sel[ns] = e
            pos[e] = ns
            ns += 1
    top = np.empty(5, np.int64)
    tmp = np.empty(max(topk_obj, 1), np.int64)

    sv = 0.0
    for e in range(n):
        if x[e] > 0.5:
            sv += sts[e]
    if topk_obj > 0:
        _topk(L, topk_obj, tmp)
        F = 0.0
        for k in range(topk_obj):
            F += L[tmp[k]]
        F = F / topk_obj - lam_sts * sv
    else:
        F = _lse(L, g) - lam_sts * sv
    if topk_obj > 0:
        best_t = F + lam_sts * sv
    else:
        best_t = L.max()
    best_sv = sv
    best_x = x.copy()
    for it in range(n_moves):
        T = T0 * (T1 / T0) ** (it / n_moves)
        _topk(L, 5, top)
        r = np.random.random()
        i = -1
        j = -1
        if r < 0.6 and ns > 0:
            w = top[np.random.randint(5)]
            cnt = wp[w + 1] - wp[w]
            if cnt == 0:
                continue
            j = wi[wp[w] + np.random.randint(cnt)]
            if x[j] > 0.5 or not cand_mask[j]:
                continue
            i = sel[np.random.randint(ns)]
            if use - s[i] + s[j] > B:
                continue
        elif r < 0.8:
            w = top[np.random.randint(5)]
            cnt = wp[w + 1] - wp[w]
            if cnt == 0:
                continue
            j = wi[wp[w] + np.random.randint(cnt)]
            if x[j] > 0.5 or not cand_mask[j] or use + s[j] > B:
                continue
        else:
            if ns == 0:
                continue
            i = sel[np.random.randint(ns)]
        if j >= 0:
            _app(L, ip, ix, iv, j, 1.0)
        if i >= 0:
            _app(L, ip, ix, iv, i, -1.0)
        nsv = sv + (sts[j] if j >= 0 else 0.0) - (sts[i] if i >= 0 else 0.0)
        if topk_obj > 0:
            _topk(L, topk_obj, tmp)
            Fn = 0.0
            for k in range(topk_obj):
                Fn += L[tmp[k]]
            Fn = Fn / topk_obj - lam_sts * nsv
        else:
            Fn = _lse(L, g) - lam_sts * nsv
        dF = Fn - F
        if dF <= 0 or np.random.random() < np.exp(-dF / T):
            F = Fn
            sv = nsv
            if j >= 0:
                x[j] = 1.0
                use += s[j]
            if i >= 0:
                x[i] = 0.0
                use -= s[i]
            if i >= 0 and j >= 0:
                p = pos[i]
                sel[p] = j
                pos[j] = p
                pos[i] = -1
            elif j >= 0:
                sel[ns] = j
                pos[j] = ns
                ns += 1
            else:
                p = pos[i]
                last = sel[ns - 1]
                sel[p] = last
                pos[last] = p
                pos[i] = -1
                ns -= 1
            if topk_obj > 0:
                tv = F + lam_sts * sv
            else:
                tv = L.max()
            if tv < best_t - 1e-12 or (tv <= best_t + 1e-12 and sv > best_sv):
                best_t = tv
                best_sv = sv
                best_x[:] = x
        else:
            if j >= 0:
                _app(L, ip, ix, iv, j, -1.0)
            if i >= 0:
                _app(L, ip, ix, iv, i, 1.0)
    return best_x, best_t


def local_search(P, x0, secs=None, n_moves=None, seed=0, g_scale=3000.0, T0_frac=2e-3, T1_frac=1e-6,
                 cand=None, topk_obj=0, lam_rel=1e-4):
    """True-objective SA from a feasible start (hard budget). cand = mask of vars allowed to move."""
    t = time.time()
    Da = P.Da
    Dc = Da.tocsc()
    x = (np.asarray(x0) > 0.5).astype(np.float64)
    L = P.loads(x)
    use = float(P.s @ x)
    assert use <= P.B + 1e-6
    pk0 = float(L.max())
    g = g_scale / max(pk0, 1e-12)
    T0, T1 = T0_frac * pk0, T1_frac * pk0
    lam = lam_rel * pk0 / max(float(P.sts.clip(min=0).sum()), 1e-12)
    cm = np.ones(P.n, np.bool_) if cand is None else np.asarray(cand, np.bool_)
    if n_moves is None:
        n_moves = 200000
    args = (P.B, P.s.astype(np.float64), P.sts.astype(np.float64), Da.indptr.astype(np.int64),
            Da.indices.astype(np.int64), Da.data.astype(np.float64), Dc.indptr.astype(np.int64),
            Dc.indices.astype(np.int64), cm)
    best_x, best_pk = x.copy(), None
    total = 0
    k = 0
    while True:
        bx, bpk = sa_true(x.copy(), L.copy(), use, *args, int(n_moves), T0, T1, g, lam, int(seed * 1000 + k),
                          int(topk_obj))
        total += n_moves
        k += 1
        val = P.peak(bx) if topk_obj == 0 else float(np.sort(P.loads(bx))[::-1][:topk_obj].mean())
        if best_pk is None or val < best_pk - 1e-12:
            best_pk, best_x = val, bx
            x, L, use = bx.copy(), P.loads(bx), float(P.s @ bx)
        if secs is None or time.time() - t > secs:
            break
    return best_x, dict(ls_moves=total, ls_time=time.time() - t, ls_restarts=k)
