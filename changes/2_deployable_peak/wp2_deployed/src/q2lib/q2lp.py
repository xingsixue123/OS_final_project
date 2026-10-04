"""Classical LP / MILP (HiGHS) models for the level problems (solver env; imports highspy -> never with ortools).

F1  : min z                 s.t. D_w.x + z >= C_w (w active), s.x <= B
F2a : min t + 1/k sum u_w   s.t. D_w.x + t + u_w >= C_w, u >= 0, s.x <= B          (CVaR_k of the loads)
F2b : min 1/ma sum t_w      s.t. D_w.x + u_w >= C_w - tau, u >= 0, t_w >= 2 a_j u_w - a_j^2 (tangents), s.x <= B
      (the squared hinge (L_w - tau)_+^2 as a convex piecewise-linear outer approximation; only windows that can
       exceed tau get rows; the MILP solution is always re-evaluated on the exact objective)
Optional lexicographic stage: max sts.x s.t. objective <= z*(1+eps).
"""
import time

import numpy as np
import scipy.sparse as sp
import highspy

import q2core as C

INF = highspy.kHighsInf
_THREADS = [None]


def highs(time_limit=None, seed=0, threads=8, opts=None):
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    if _THREADS[0] is None:
        _THREADS[0] = int(threads)
    h.setOptionValue("threads", int(_THREADS[0]))      # must stay constant within a process
    h.setOptionValue("random_seed", int(seed))
    if time_limit is not None:
        h.setOptionValue("time_limit", max(float(time_limit), 0.01))
    for k, v in (opts or {}).items():
        h.setOptionValue(k, v)
    return h


def relevant_windows(P, form):
    return C.relevant_windows(P)


def model_vars(P, form):
    return C.model_vars(P)


def tangents(umax, J):
    a = np.linspace(0.0, umax, int(J))
    return a


def build(P, form, var, integer=False, obj_sts=0.0, zcap=None, J=12):
    """Returns (HighsLp, layout) for formulation `form` over free vars `var`."""
    nv = len(var)
    Da = P.Da[var]
    s = P.s[var]
    typ = form.typ if form.typ < 3 else 2
    blocks_cols = []
    if typ == 0:
        ma = P.ma
        # cols: x, z ; rows: ma (loads) + 1 (budget)
        A_x = sp.vstack([Da.T.tocsr(), sp.csr_matrix(s[None, :])]).tocsc()
        zcol = sp.csc_matrix((np.ones(ma), (np.arange(ma), np.zeros(ma, int))), shape=(ma + 1, 1))
        A = sp.hstack([A_x, zcol]).tocsc()
        cost = np.r_[-obj_sts * P.sts[var], 1.0 if zcap is None else 0.0]
        lower = np.r_[np.zeros(nv), -INF]
        upper = np.r_[np.ones(nv), INF if zcap is None else zcap]
        rlo = np.r_[P.C, -INF]
        rhi = np.r_[np.full(ma, INF), P.B]
        layout = dict(typ=0, nv=nv)
    elif typ == 1:
        ma = P.ma
        k = float(form.k)
        A_x = sp.vstack([Da.T.tocsr(), sp.csr_matrix(s[None, :])]).tocsc()
        tcol = sp.csc_matrix((np.ones(ma), (np.arange(ma), np.zeros(ma, int))), shape=(ma + 1, 1))
        ucol = sp.vstack([sp.identity(ma, format="csc"), sp.csc_matrix((1, ma))]).tocsc()
        A = sp.hstack([A_x, tcol, ucol]).tocsc()
        zc = 1.0 if zcap is None else 0.0
        cost = np.r_[-obj_sts * P.sts[var], zc, np.full(ma, zc / k)]
        lower = np.r_[np.zeros(nv), -INF, np.zeros(ma)]
        upper = np.r_[np.ones(nv), INF, np.full(ma, INF)]
        rlo = np.r_[P.C, -INF]
        rhi = np.r_[np.full(ma, INF), P.B]
        layout = dict(typ=1, nv=nv, k=k)
    else:
        rw = relevant_windows(P, form)
        mr = len(rw)
        umax = max(float((P.C[rw] - form.tau).max()), 1e-9) * 1.05
        a = tangents(umax, J)
        Jn = len(a)
        # cols: x (nv), u (mr), t (mr); rows: mr (u >= C - tau - Dx), mr*Jn tangents, 1 budget
        Dr = Da[:, rw].T.tocsr()                    # mr x nv
        rows_load = sp.hstack([Dr, sp.identity(mr, format="csr"), sp.csr_matrix((mr, mr))])
        # tangent rows: t_w - 2 a_j u_w >= -a_j^2
        I_ = sp.identity(mr, format="csr")
        tan_u = sp.vstack([-2.0 * aj * I_ for aj in a]).tocsr()
        tan_t = sp.vstack([I_ for _ in a]).tocsr()
        rows_tan = sp.hstack([sp.csr_matrix((mr * Jn, nv)), tan_u, tan_t])
        rows_b = sp.hstack([sp.csr_matrix(s[None, :]), sp.csr_matrix((1, 2 * mr))])
        A = sp.vstack([rows_load, rows_tan, rows_b]).tocsc()
        zc = 1.0 if zcap is None else 0.0
        cost = np.r_[-obj_sts * P.sts[var], np.zeros(mr), np.full(mr, zc / P.ma)]
        lower = np.r_[np.zeros(nv), np.zeros(mr), np.zeros(mr)]
        upper = np.r_[np.ones(nv), np.full(mr, INF), np.full(mr, INF)]
        rlo = np.r_[P.C[rw] - form.tau, -np.repeat(a ** 2, mr), -INF]
        rhi = np.r_[np.full(mr, INF), np.full(mr * Jn, INF), P.B]
        layout = dict(typ=2, nv=nv, rw=rw, a=a, mr=mr)
    lp = highspy.HighsLp()
    lp.num_col_ = len(cost)
    lp.num_row_ = len(rlo)
    lp.col_cost_ = cost
    lp.col_lower_ = lower
    lp.col_upper_ = upper
    lp.row_lower_ = rlo
    lp.row_upper_ = rhi
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = A.indptr.astype(np.int32)
    lp.a_matrix_.index_ = A.indices.astype(np.int32)
    lp.a_matrix_.value_ = A.data.astype(float)
    if integer:
        lp.integrality_ = [highspy.HighsVarType.kInteger] * nv + [highspy.HighsVarType.kContinuous] * (len(cost) - nv)
    return lp, layout


def objective_row(layout, ncol, P):
    """(indices, values) of the objective expression as a row (for the lexicographic cap)."""
    nv = layout["nv"]
    if layout["typ"] == 0:
        return np.array([nv], np.int32), np.array([1.0])
    if layout["typ"] == 1:
        ma = P.ma
        return np.r_[nv, nv + 1 + np.arange(ma)].astype(np.int32), np.r_[1.0, np.full(ma, 1.0 / layout["k"])]
    mr = layout["mr"]
    return (nv + mr + np.arange(mr)).astype(np.int32), np.full(mr, 1.0 / P.ma)


def full_start(P, layout, var, xv):
    """column values for a warm start from a binary x over var."""
    L = P.C - P.Da[var].T @ xv
    if layout["typ"] == 0:
        return np.r_[xv, L.max()]
    if layout["typ"] == 1:
        k = int(layout["k"])
        t = float(np.sort(L)[::-1][k - 1])
        return np.r_[xv, t, np.maximum(L - t, 0.0)]
    rw, a = layout["rw"], layout["a"]
    tau = P.form.tau
    u = np.maximum(L[rw] - tau, 0.0)
    t = np.max(2.0 * a[None, :] * u[:, None] - a[None, :] ** 2, axis=1)
    t = np.maximum(t, 0.0)
    return np.r_[xv, u, t]


def solve_lp(P, deadline, lexi=False, lexi_eps=1e-6, J=12, seed=0, var=None, opts=None):
    t = time.time()
    form = P.form
    if var is None:
        var = model_vars(P, form)
    info = dict(lp_nvar=len(var))
    x = np.zeros(P.n)
    if len(var) == 0:
        return x, dict(info, lp_status="empty")
    lp, lay = build(P, form, var, J=J)
    h = highs(time_limit=max(0.9 * (deadline - time.time()), 0.05), seed=seed, opts=opts)
    h.passModel(lp)
    h.run()
    st = h.modelStatusToString(h.getModelStatus())
    info["lp_status"] = st
    if st != "Optimal":
        info["lp_time"] = time.time() - t
        return None, info
    sol = np.array(h.getSolution().col_value)
    x[var] = sol[:len(var)]
    z = float(h.getInfo().objective_function_value)
    info["z_lp"] = z
    info["n_frac"] = int(((sol[:len(var)] > 1e-6) & (sol[:len(var)] < 1 - 1e-6)).sum())
    if lexi and time.time() < deadline:
        var2 = np.union1d(np.flatnonzero((P.sts > 0) & (P.s <= P.B + 1e-9)), var)
        lp2, lay2 = build(P, form, var2, obj_sts=1.0, zcap=None if lay["typ"] != 0 else z * (1 + lexi_eps) + 1e-12,
                          J=J)
        if lay["typ"] != 0:
            # zero the objective weight of the peak part; cap it by a row
            lp2.col_cost_ = np.r_[-P.sts[var2], np.zeros(lp2.num_col_ - len(var2))]
        h2 = highs(time_limit=deadline - time.time(), seed=seed, opts=opts)
        h2.passModel(lp2)
        if lay["typ"] != 0:
            idx, val = objective_row(lay2, lp2.num_col_, P)
            h2.addRow(-INF, z * (1 + lexi_eps) + 1e-12, len(idx), idx, val)
        h2.run()
        st2 = h2.modelStatusToString(h2.getModelStatus())
        info["lp2_status"] = st2
        if st2 == "Optimal":
            sol2 = np.array(h2.getSolution().col_value)
            x = np.zeros(P.n)
            x[var2] = sol2[:len(var2)]
    info["lp_time"] = time.time() - t
    return x, info


def solve_milp(P, deadline, x0=None, var=None, J=12, seed=0, opts=None, eps_tie=0.0):
    """HiGHS MILP on the formulation model, warm-started from binary x0 (free-var vector)."""
    t = time.time()
    form = P.form
    if var is None:
        var = model_vars(P, form)
    if len(var) == 0 or deadline - time.time() < 0.05:
        return None, dict(milp_status="no_time")
    obj_sts = 0.0
    if eps_tie > 0 and x0 is not None:
        z0 = abs(P.obj(x0)) + 1e-12
        obj_sts = eps_tie * z0 / max(float(P.sts[var].clip(min=0).sum()), 1e-12)
    lp, lay = build(P, form, var, integer=True, obj_sts=obj_sts, J=J)
    tl = 0.85 * (deadline - time.time()) - 0.1          # margin: HiGHS overshoots its limit + repair afterwards
    if tl < 0.05:
        return None, dict(milp_status="no_time")
    h = highs(time_limit=tl, seed=seed, opts=opts)
    h.passModel(lp)
    if x0 is not None:
        xv = (np.asarray(x0)[var] > 0.5).astype(float)
        s0 = highspy.HighsSolution()
        s0.col_value = list(full_start(P, lay, var, xv))
        s0.value_valid = True
        try:
            h.setSolution(s0)
        except Exception as ex:  # pragma: no cover
            print("setSolution failed:", ex)
    h.run()
    info = h.getInfo()
    status = h.modelStatusToString(h.getModelStatus())
    x = None
    if time.time() > deadline + 0.05:       # overran its level deadline (e.g. non-interruptible presolve):
        return None, dict(milp_status=status, milp_overrun=1, milp_time=time.time() - t)   # result discarded
    if info.primal_solution_status == 2:
        sol = np.array(h.getSolution().col_value)
        x = np.zeros(P.n)
        x[var] = (sol[:len(var)] > 0.5)
    return x, dict(milp_status=status, mip_gap=float(info.mip_gap), milp_time=time.time() - t,
                   nodes=int(info.mip_node_count))
