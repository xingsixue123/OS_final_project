"""HiGHS epigraph LP / MILP: min z s.t. C_w - (D^T x)_w <= z, s^T x <= W, 0<=x<=1."""
import time
import numpy as np
import highspy


def _build(inst, integer):
    D, s, W, C = inst["D"], inst["s"], inst["W"], inst["C"]
    n, m = D.shape
    Dc = D.tocsr()  # rows of D = columns of the LP matrix
    lp = highspy.HighsLp()
    lp.num_col_ = n + 1
    lp.num_row_ = m + 1
    lp.col_cost_ = np.r_[np.zeros(n), 1.0]
    lp.col_lower_ = np.r_[np.zeros(n), -highspy.kHighsInf]
    lp.col_upper_ = np.r_[np.ones(n), highspy.kHighsInf]
    lp.row_lower_ = np.r_[C, -highspy.kHighsInf]
    lp.row_upper_ = np.r_[np.full(m, highspy.kHighsInf), W]
    # column-wise: column e = D[e,:] rows 0..m-1 plus s_e at row m ; column z = ones rows 0..m-1
    cnt = np.diff(Dc.indptr) + 1
    start = np.r_[0, np.cumsum(cnt)]
    idx = np.empty(start[-1], dtype=np.int32)
    val = np.empty(start[-1])
    pos = start[:-1]
    # fill: for each column the D entries then the budget row
    rowptr = Dc.indptr
    lens = np.diff(rowptr)
    rep = np.repeat(pos, lens) + (np.arange(Dc.nnz) - np.repeat(rowptr[:-1], lens))
    idx[rep] = Dc.indices
    val[rep] = Dc.data
    idx[pos + lens] = m
    val[pos + lens] = s
    start = np.r_[start, start[-1] + m]
    idx = np.r_[idx, np.arange(m, dtype=np.int32)]
    val = np.r_[val, np.ones(m)]
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = start.astype(np.int32)
    lp.a_matrix_.index_ = idx
    lp.a_matrix_.value_ = val
    if integer:
        lp.integrality_ = [highspy.HighsVarType.kInteger] * n + [highspy.HighsVarType.kContinuous]
    return lp


def solve_lp(inst, threads=1):
    t = time.time()
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.setOptionValue("threads", threads)
    h.passModel(_build(inst, False))
    h.run()
    sol = np.array(h.getSolution().col_value)
    n = inst["n"]
    x = sol[:n]
    z = float(sol[n])
    nfrac = int(((x > 1e-7) & (x < 1 - 1e-7)).sum())
    xr = (x >= 1 - 1e-7).astype(float)  # round down
    return dict(x_raw=xr, z_lp=z, n_frac=nfrac, status=h.modelStatusToString(h.getModelStatus()),
                lp_time=time.time() - t, n_ones=int(xr.sum()))


def solve_milp(inst, time_limit, threads=1):
    t = time.time()
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.setOptionValue("threads", threads)
    h.setOptionValue("time_limit", float(time_limit))
    h.setOptionValue("random_seed", int(inst["seed"]))
    h.passModel(_build(inst, True))
    h.run()
    info = h.getInfo()
    n = inst["n"]
    status = h.modelStatusToString(h.getModelStatus())
    has = info.primal_solution_status == 2  # kSolutionStatusFeasible
    if has:
        sol = np.array(h.getSolution().col_value)
        x = (sol[:n] > 0.5).astype(float)
    else:
        x = None
    return dict(x_raw=x, status=status, mip_obj=float(info.objective_function_value) if has else float("nan"),
                mip_bound=float(info.mip_dual_bound), mip_gap=float(info.mip_gap),
                milp_time=time.time() - t, nodes=int(info.mip_node_count))
