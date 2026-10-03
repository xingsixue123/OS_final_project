"""OR-Tools CP-SAT level solver (classical). NEVER imports highspy (symbol clash); the optional LP warm start uses
scipy's bundled HiGHS (q2core.lp_start_scipy), the same LP model as q2lp.

Integer scaling: loads/savings multiplied by SC and rounded (F1/F2a SC=1e6 DT-units -> rounding error <= 5e-7 DT per
coefficient; F2b SC=1e3 so that u^2 stays small; u_w^2 is exact via AddMultiplicationEquality). The solution is always
re-evaluated on the exact float objective by the shared repair / nested evaluation.
"""
import time

import numpy as np
from ortools.sat.python import cp_model

import q2core as C


def cpsat_level(P, k, dl, cfg, seed):
    t0 = time.time()
    info = {}
    start = cfg.get("start", "lp")
    x0 = None
    if start == "lp":
        xl = C.lp_start_scipy(P, dl, J=int(cfg.get("J", 12)))
        if xl is not None:
            x0, st = P.repair((xl >= 1 - 1e-6).astype(float), fill=True)
    if x0 is None:
        x0, st = C.pgreedy(P)
    rem = dl - time.time()
    if rem < 0.3:
        return x0, dict(info, cp_status="no_time")
    var = C.model_vars(P)
    if len(var) == 0:
        return x0, info
    typ = P.form.typ if P.form.typ < 3 else 2
    SC = float(cfg.get("scale", 1e6 if typ < 2 else 1e3))
    Da = P.Da[var].tocsc()          # columns = windows
    nv = len(var)
    m = cp_model.CpModel()
    xs = [m.NewBoolVar(f"x{i}") for i in range(nv)]
    dsc = np.rint(Da.data * SC).astype(np.int64)
    Csc = np.rint(P.C * SC).astype(np.int64)
    s_int = np.rint(P.s[var]).astype(np.int64)
    m.Add(cp_model.LinearExpr.WeightedSum(xs, [int(v) for v in s_int]) <= int(np.floor(P.B + 1e-9)))
    maxsave = np.zeros(P.ma, np.int64)
    np.add.at(maxsave, Da.indices if False else np.repeat(np.arange(P.ma), np.diff(Da.indptr)), np.maximum(dsc, 0))
    minsave = np.zeros(P.ma, np.int64)
    np.add.at(minsave, np.repeat(np.arange(P.ma), np.diff(Da.indptr)), np.minimum(dsc, 0))
    lo_load = Csc - maxsave
    hi_load = Csc - minsave
    cols = [(Da.indices[Da.indptr[w]:Da.indptr[w + 1]], dsc[Da.indptr[w]:Da.indptr[w + 1]]) for w in range(P.ma)]

    def load_expr(w):
        idx, val = cols[w]
        return cp_model.LinearExpr.WeightedSum([xs[i] for i in idx], [int(v) for v in val])

    if typ == 0:
        z = m.NewIntVar(int(lo_load.max()), int(hi_load.max()), "z")
        for w in range(P.ma):
            idx, _ = cols[w]
            if len(idx) == 0:
                m.Add(z >= int(Csc[w]))
            else:
                m.Add(z + load_expr(w) >= int(Csc[w]))
        m.Minimize(z)
    elif typ == 1:
        kk = int(P.form.k)
        t = m.NewIntVar(int(lo_load.min()), int(hi_load.max()), "t")
        us = []
        for w in range(P.ma):
            u = m.NewIntVar(0, int(max(hi_load[w] - lo_load.min(), 0)), f"u{w}")
            us.append(u)
            idx, _ = cols[w]
            if len(idx) == 0:
                m.Add(u + t >= int(Csc[w]))
            else:
                m.Add(u + t + load_expr(w) >= int(Csc[w]))
        m.Minimize(kk * t + sum(us))
    else:
        tau = int(np.rint(P.form.tau * SC))
        rw = C.relevant_windows(P)
        ts = []
        for w in rw:
            ub = int(max(hi_load[w] - tau, 0))
            u = m.NewIntVar(0, ub, f"u{w}")
            tt = m.NewIntVar(0, ub * ub, f"t{w}")
            idx, _ = cols[w]
            if len(idx) == 0:
                m.Add(u >= int(Csc[w]) - tau)
            else:
                m.Add(u + load_expr(w) >= int(Csc[w]) - tau)
            m.AddMultiplicationEquality(tt, [u, u])
            ts.append(tt)
        m.Minimize(sum(ts))
    if cfg.get("hint", True):
        for i, e in enumerate(var):
            m.AddHint(xs[i], bool(x0[e] > 0.5))
    rem = dl - time.time()
    if rem < 0.2:
        return x0, dict(info, cp_status="no_time_after_build")
    sv = cp_model.CpSolver()
    sv.parameters.num_workers = int(cfg.get("threads", 8))
    sv.parameters.max_time_in_seconds = max(0.9 * rem - 0.05, 0.05)
    sv.parameters.random_seed = int(seed * 1000 + k)
    for key in ("linearization_level", "symmetry_level", "cp_model_presolve", "use_lns_only", "repair_hint",
                "fix_variables_to_their_hinted_value", "hint_conflict_limit"):
        if key in cfg:
            setattr(sv.parameters, key, cfg[key])
    st = sv.Solve(m)
    info.update(cp_status=sv.StatusName(st), cp_time=time.time() - t0, cp_build=None)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) and time.time() <= dl + 0.05:
        x = np.zeros(P.n)
        vals = np.array([sv.BooleanValue(v) for v in xs], dtype=float)
        x[var] = vals
        xr, _ = P.repair(x, fill=False)
        if P.obj(xr) < P.obj(x0) - 1e-15:
            info["cp_improved"] = 1
            return xr, info
    info["cp_improved"] = 0
    return x0, info
