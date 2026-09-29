"""SCIP (PySCIPOpt) level solver (classical): MILP for F1/F2a, convex MIQCP for F2b (t_w >= u_w^2 exact).
SCIP is single-threaded in this build (PyPI wheel; no concurrent solve), documented in RESULTS."""
import time

import numpy as np
import pyscipopt as ps

import q2core as C


def scip_level(P, k, dl, cfg, seed, start_solution):
    t0 = time.time()
    x0, info = start_solution(P, cfg.get("start", "lp"), dl, cfg, seed)
    rem = dl - time.time()
    if rem < 0.3:
        return x0, dict(info, scip_status="no_time")
    var = C.model_vars(P)
    if len(var) == 0:
        return x0, info
    typ = P.form.typ if P.form.typ < 3 else 2
    Da = P.Da[var].tocsc()
    nv = len(var)
    m = ps.Model()
    m.hideOutput()
    m.setParam("randomization/randomseedshift", int(seed * 1000 + k))
    for key, val in cfg.get("scip_params", {}).items():
        m.setParam(key, val)
    if cfg.get("emphasis"):
        m.setHeuristics({"aggressive": ps.SCIP_PARAMSETTING.AGGRESSIVE, "fast": ps.SCIP_PARAMSETTING.FAST,
                         "off": ps.SCIP_PARAMSETTING.OFF, "default": ps.SCIP_PARAMSETTING.DEFAULT}[cfg["emphasis"]])
    xs = [m.addVar(vtype="B") for _ in range(nv)]
    m.addCons(ps.quicksum(float(P.s[var][i]) * xs[i] for i in range(nv)) <= float(P.B))
    cols = [(Da.indices[Da.indptr[w]:Da.indptr[w + 1]], Da.data[Da.indptr[w]:Da.indptr[w + 1]]) for w in range(P.ma)]
    extra = {}
    if typ == 0:
        z = m.addVar(lb=None, ub=None)
        for w in range(P.ma):
            idx, val = cols[w]
            m.addCons(z + ps.quicksum(float(v) * xs[i] for i, v in zip(idx, val)) >= float(P.C[w]))
        m.setObjective(z, "minimize")
        extra["z"] = z
    elif typ == 1:
        kk = float(P.form.k)
        t = m.addVar(lb=None, ub=None)
        us = [m.addVar(lb=0.0) for _ in range(P.ma)]
        for w in range(P.ma):
            idx, val = cols[w]
            m.addCons(us[w] + t + ps.quicksum(float(v) * xs[i] for i, v in zip(idx, val)) >= float(P.C[w]))
        m.setObjective(t + ps.quicksum(us) / kk, "minimize")
        extra.update(t=t, us=us)
    else:
        tau = P.form.tau
        rw = C.relevant_windows(P)
        us, ts = [], []
        for w in rw:
            u = m.addVar(lb=0.0)
            tt = m.addVar(lb=0.0)
            idx, val = cols[w]
            m.addCons(u + ps.quicksum(float(v) * xs[i] for i, v in zip(idx, val)) >= float(P.C[w] - tau))
            m.addCons(tt >= u * u)
            us.append(u)
            ts.append(tt)
        m.setObjective(ps.quicksum(ts) / float(P.ma), "minimize")
        extra.update(rw=rw, us=us, ts=ts)
    # warm start
    try:
        sol = m.createSol()
        xv = (np.asarray(x0)[var] > 0.5).astype(float)
        for i in range(nv):
            m.setSolVal(sol, xs[i], float(xv[i]))
        L = P.C - P.Da[var].T @ xv
        if typ == 0:
            m.setSolVal(sol, extra["z"], float(L.max()))
        elif typ == 1:
            kk = int(P.form.k)
            tv = float(np.sort(L)[::-1][kk - 1])
            m.setSolVal(sol, extra["t"], tv)
            for w in range(P.ma):
                m.setSolVal(sol, extra["us"][w], float(max(L[w] - tv, 0.0)))
        else:
            for q, w in enumerate(extra["rw"]):
                u = float(max(L[w] - P.form.tau, 0.0))
                m.setSolVal(sol, extra["us"][q], u)
                m.setSolVal(sol, extra["ts"][q], u * u)
        m.addSol(sol, free=True)
    except Exception as ex:  # pragma: no cover
        info["scip_warm_fail"] = str(ex)[:80]
    rem = dl - time.time()
    if rem < 0.2:
        return x0, dict(info, scip_status="no_time_after_build")
    m.setParam("limits/time", max(0.9 * rem - 0.05, 0.05))
    m.optimize()
    info.update(scip_status=m.getStatus(), scip_time=time.time() - t0)
    if m.getNSols() > 0 and time.time() <= dl + 0.1:
        best = m.getBestSol()
        x = np.zeros(P.n)
        x[var] = np.array([m.getSolVal(best, v) for v in xs]) > 0.5
        xr, _ = P.repair(x, fill=False)
        if P.obj(xr) < P.obj(x0) - 1e-15:
            info["scip_improved"] = 1
            return xr, info
    info["scip_improved"] = 0
    return x0, info
