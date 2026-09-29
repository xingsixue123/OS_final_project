"""Contested-subset QUBO LNS (Ising family): explicit sub-QUBO on a neighbourhood N of the objective-relevant windows,
solved by MindQuantum QAIA (bSB / dSB / CAC, sparse J + h, CPU) or dwave-samplers SA or OpenJij SA; the k lowest-
energy samples are repaired on the view and the best TRUE objective is accepted if it improves the incumbent.

Sub-QUBO:  E(x) = sum_{w in T} alpha_w (C'_w - tau_s - (D_N^T x)_w)^2 + pen*scale*(s.x - B')^2   (x in {0,1}^N)
  F2b: alpha_w = 1 on windows above tau at the incumbent, tau_s = tau (exact squared hinge on the active set)
  F1/F2a: alpha_w = 1 on windows within delta of the incumbent's peak, tau_s = (1 - tau_gap) * peak
"""
import math
import time

import numpy as np
import scipy.sparse as sp

import q2core as C
from q2hybrid import View


def subqubo(V, xs0, typ, tau, alpha_mode_delta, tau_gap, pen):
    Da = V.Da.tocsc()
    L0 = V.loads(xs0)
    touched = np.flatnonzero(np.diff(Da.indptr) > 0)
    if typ == 2:
        act = touched[L0[touched] > tau]
        tau_s = tau
    else:
        pk = float(L0.max())
        act = touched[L0[touched] >= pk * (1 - alpha_mode_delta)]
        tau_s = pk * (1 - tau_gap)
    if len(act) == 0:
        act = touched[np.argsort(-L0[touched])[:4]]
    Dt = V.Da[:, act].toarray()
    r = V.C[act] - tau_s
    Q = Dt @ Dt.T
    c = -2.0 * Dt @ r
    const = float((r * r).sum())
    scale = float(np.mean(np.diag(Q))) / max(float(np.mean(V.s ** 2)), 1e-12)
    ps = pen * scale
    Q = Q + ps * np.outer(V.s, V.s)
    c = c - 2.0 * ps * V.B * V.s
    const += ps * V.B ** 2
    return Q, c, const


def qubo_samples(Q, c, const, solver, seed, reads, iters, dt, xi_scale, x0=None):
    n = Q.shape[0]
    if solver in ("mq_bsb", "mq_dsb", "mq_cac"):
        from mindquantum.algorithm.qaia import BSB, DSB, CAC
        np.random.seed(seed)
        dQ = np.diag(Q).copy()
        Q1 = Q.sum(1)
        J = -0.5 * (Q - np.diag(dQ))
        h = -0.5 * (Q1 + c)
        Js = sp.csr_matrix(J.astype(np.float32))
        if solver == "mq_cac":
            sol = CAC(Js, h.astype(np.float32), batch_size=reads, n_iter=iters, dt=dt)
        else:
            JF2 = float((J ** 2).sum())
            xi = xi_scale * math.sqrt(max(n - 1, 1)) / math.sqrt(JF2 + 2 * ((h / 2) ** 2).sum() + 1e-30)
            cls = BSB if solver == "mq_bsb" else DSB
            sol = cls(Js, h.astype(np.float32), batch_size=reads, n_iter=iters, dt=dt, xi=float(xi))
        sol.update()
        S = np.sign(np.asarray(sol.x, float))
        S[~np.isfinite(S)] = -1
        S[S == 0] = 1
        X = ((S + 1) / 2).T
    elif solver == "dwave_sa":
        import dimod
        from dwave.samplers import SimulatedAnnealingSampler
        lin = c + np.diag(Q)
        iu = np.triu_indices(n, k=1)
        q = 2.0 * Q[iu]
        nz = q != 0
        bqm = dimod.BinaryQuadraticModel.from_numpy_vectors(lin, (iu[0][nz], iu[1][nz], q[nz]), const, dimod.BINARY)
        kw = {}
        if x0 is not None:
            kw = dict(initial_states=np.tile(np.asarray(x0, np.int8), (reads, 1)), initial_states_generator="none")
        ss = SimulatedAnnealingSampler().sample(bqm, num_reads=reads, num_sweeps=iters, seed=seed, **kw)
        rec = ss.record.sample
        var = np.asarray(list(ss.variables))
        X = np.zeros((rec.shape[0], n))
        X[:, var] = rec
    elif solver == "openjij_sa":
        import openjij as oj
        Qd = {}
        iu = np.triu_indices(n, k=1)
        for i in range(n):
            Qd[(i, i)] = float(Q[i, i] + c[i])
        qv = 2.0 * Q[iu]
        for a, b, v in zip(iu[0], iu[1], qv):
            if v != 0:
                Qd[(int(a), int(b))] = float(v)
        res = oj.SASampler().sample_qubo(Qd, num_reads=reads, num_sweeps=iters, seed=seed)
        X = np.zeros((len(res.record), n))
        for r_, smp in enumerate(res.record.sample):
            X[r_, :len(smp)] = smp
    else:
        raise ValueError(solver)
    E = np.einsum("ki,ij,kj->k", X, Q, X) + X @ c + const
    o = np.argsort(E)
    return X[o], E[o]


def mq_level(P, k, dl, cfg, seed, start_solution):
    t0 = time.time()
    x, info = start_solution(P, cfg.get("start", "lp"), dl, cfg, seed)
    rng = np.random.default_rng(int(seed) * 1000 + k)
    bobj, bsts = P.obj(x), float(P.sts @ x)
    solver = cfg.get("mq_solver", "mq_dsb")
    nmax = int(cfg.get("mq_nmax", 800))
    reads = int(cfg.get("mq_reads", 16))
    iters = int(cfg.get("mq_iters", 300))
    dtv = float(cfg.get("mq_dt", 1.0 if solver != "mq_cac" else 0.075))
    xi_scale = float(cfg.get("mq_xi", 0.5))
    pen = float(cfg.get("mq_pen", 0.05))
    q = int(cfg.get("mq_q", 6))
    delta = float(cfg.get("mq_delta", 0.03))
    tau_gap = float(cfg.get("mq_tau_gap", 0.02))
    ksamp = int(cfg.get("mq_ksamp", 4))
    typ = P.form.typ if P.form.typ < 3 else 2
    Dc = P.Dc
    wins = tries = 0
    while time.time() < dl - 0.1:
        L = P.loads(x)
        order = np.argsort(-L)
        W = order[:int(rng.integers(2, max(q, 2) + 1))]
        if typ == 2:
            above = np.flatnonzero(L > P.form.tau)
            if len(above):
                W = np.union1d(W, rng.choice(above, size=min(len(above), q), replace=False))
        N = np.unique(np.concatenate([Dc.indices[Dc.indptr[w]:Dc.indptr[w + 1]] for w in W]))
        sel = np.flatnonzero(x > 0.5)
        if len(sel):
            N = np.union1d(N, rng.choice(sel, size=min(len(sel), max(nmax // 4, 1)), replace=False))
        N = N[P.s[N] <= P.B + 1e-9]
        if len(N) > nmax:
            N = rng.choice(N, size=nmax, replace=False)
        if len(N) < 2:
            break
        V = View(P, N, x)
        Q, c, const = subqubo(V, x[N], typ, P.form.tau, delta, tau_gap, pen)
        tries += 1
        try:
            X, E = qubo_samples(Q, c, const, solver, int(rng.integers(1 << 30)), reads, iters, dtv, xi_scale, x0=x[N])
        except Exception as ex:
            info["mq_error"] = str(ex)[:80]
            break
        for xs in X[:ksamp]:
            xn = x.copy()
            xn[N] = xs
            xn, _ = P.repair(xn, fill=False)
            ob, sv = P.obj(xn), float(P.sts @ xn)
            if ob < bobj - 1e-15 or (ob <= bobj + 1e-15 and sv > bsts + 1e-9):
                x, bobj, bsts = xn, ob, sv
                wins += 1
        if time.time() > dl:
            break
    info.update(mq_tries=tries, mq_wins=wins, mq_time=time.time() - t0)
    return x, info
