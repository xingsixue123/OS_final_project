"""QUBO / Ising candidates (C1, C2, C4, C5, RB) on a pbcore.Sub problem (one nested level).

C1  hybrid LP + peak-window LNS: start from repaired LP (R1); neighbourhoods = episodes touching the top-k
    analytic peak windows | LP fractional core + top windows | a block of 6-24 windows around a top window;
    racing sub-solvers: HiGHS sub-MILP, true-objective SA restricted to the neighbourhood, dwave-samplers SA
    on the sum-of-squares sub-QUBO; accept only if the TRUE peak improves (tie: more DT saved).
C2  open EIM-style constrained Ising on the true objective: numba replica exchange (24 replicas),
    energy LSE_g(L) + lambda*h + rho/2*h^2 with h = hinge budget violation (native inequality), ALM on lambda,
    started from the repaired LP.
C4  sum-of-squares peak QUBO  sum_w alpha_w (C_w - tau - (D^T x)_w)^2 + mu s^T x  solved by matrix-free
    ballistic SB (PyTorch CPU) with window-dual (SAIM/ALM-style) reweighting of alpha and mu; then repair.
C5  contested-subset QUBO after LP pegging (reduced costs): explicit sub-QUBO solved by dwave-samplers SA,
    Tabu and MindQuantum bSB/dSB, vs HiGHS MILP on the same subset.
RB  robustness: minimize mean of the top-k windows (CVaR LP, k in 3..5) + round + repair + top-k SA.
"""
import math
import time

import numpy as np
import scipy.sparse as sp
import numba as nb

import pbcore as PC
import pbsolvers as PS


class View:
    """Sub-problem over a subset N of a Sub P's free vars, the rest fixed at xbase."""
    def __init__(self, P, N, xbase):
        N = np.asarray(N, np.int64)
        self.N = N
        mask = np.zeros(P.n, bool)
        mask[N] = True
        xo = np.where(mask, 0.0, xbase)
        self.C = P.C - P.Da.T @ xo
        self.B = P.B - float(P.s @ xo)
        self.Da = P.Da[N].tocsr()
        self.s = P.s[N]
        self.sts = P.sts[N]
        self.rank = P.rank[N]
        self.n = len(N)
        self.ma = P.ma

    def loads(self, xs):
        return self.C - self.Da.T @ xs

    def peak(self, xs):
        return float(self.loads(xs).max())


def _better(P, x, bpk, bsts):
    pk = P.peak(x)
    sv = float(P.sts @ x)
    return (pk < bpk - 1e-12) or (pk <= bpk + 1e-12 and sv > bsts + 1e-12), pk, sv


# ------------------------------------------------------------------ sub-QUBO construction
def subqubo(V, xs0, tau, pen=1.0, wmask=None, alpha=None):
    """Explicit QUBO on V's vars: sum_w a_w (C_w - tau - (D^T x)_w)^2 + pen_s (s.x - B)^2 (equality-with-offset
    budget penalty, scaled) restricted to windows touched by V. Returns (Q dense upper incl diag, c, const, cols)."""
    Da = V.Da.tocsc()
    touched = np.flatnonzero(np.diff(Da.indptr) > 0)
    Dt = V.Da[:, touched].toarray()          # n x t
    r = V.C[touched] - tau
    a = np.ones(len(touched)) if alpha is None else alpha[touched]
    Q = (Dt * a[None, :]) @ Dt.T
    c = -2.0 * Dt @ (a * r)
    const = float((a * r * r).sum())
    scale = float(np.mean(np.diag(Q))) / max(float(np.mean(V.s ** 2)), 1e-12)
    ps = pen * scale
    Q = Q + ps * np.outer(V.s, V.s)
    c = c - 2.0 * ps * V.B * V.s
    const += ps * V.B ** 2
    return Q, c, const


def _bqm(Q, c, const):
    import dimod
    n = Q.shape[0]
    lin = c + np.diag(Q)
    iu = np.triu_indices(n, k=1)
    q = 2.0 * Q[iu]
    nz = q != 0
    return dimod.BinaryQuadraticModel.from_numpy_vectors(lin, (iu[0][nz], iu[1][nz], q[nz]), const, dimod.BINARY)


def _samples(ss, n):
    rec = ss.record.sample
    var = np.asarray(list(ss.variables))
    X = np.zeros((rec.shape[0], n))
    X[:, var] = rec
    return X, ss.record.energy


def qubo_solve(Q, c, const, solver, seed=0, reads=16, sweeps=1000, secs=5.0, x0=None):
    """Returns (k, n) candidate binary samples, lowest surrogate energy first. x0: optional warm start
    (dwave SA: initial state with a low starting temperature; Tabu: initial state)."""
    n = Q.shape[0]
    if solver == "dwave_sa":
        from dwave.samplers import SimulatedAnnealingSampler
        kw = {}
        if x0 is not None:
            kw = dict(initial_states=np.tile(np.asarray(x0, np.int8), (reads, 1)), initial_states_generator="none")
        ss = SimulatedAnnealingSampler().sample(_bqm(Q, c, const), num_reads=reads, num_sweeps=sweeps, seed=seed,
                                                **kw)
        X, E = _samples(ss, n)
    elif solver == "dwave_tabu":
        from dwave.samplers import TabuSampler
        kw = {}
        if x0 is not None:
            r = max(2, reads // 4)
            kw = dict(initial_states=np.tile(np.asarray(x0, np.int8), (r, 1)), initial_states_generator="none")
        ss = TabuSampler().sample(_bqm(Q, c, const), num_reads=max(2, reads // 4), timeout=int(secs * 1000 / 4),
                                  seed=seed, **kw)
        X, E = _samples(ss, n)
    elif solver in ("mq_bsb", "mq_dsb"):
        from mindquantum.algorithm.qaia import BSB, DSB
        np.random.seed(seed)
        dQ = np.diag(Q).copy()
        Q1 = Q.sum(1)
        J = -0.5 * (Q - np.diag(dQ))
        h = -0.5 * (Q1 + c)
        JF2 = float((J ** 2).sum())
        xi = 0.5 * math.sqrt(max(n - 1, 1)) / math.sqrt(JF2 + 2 * ((h / 2) ** 2).sum() + 1e-30)
        cls = BSB if solver == "mq_bsb" else DSB
        sol = cls(sp.csr_matrix(J.astype(np.float32)), h.astype(np.float32), batch_size=reads, n_iter=sweeps,
                  xi=float(xi))
        sol.update()
        S = np.sign(np.asarray(sol.x, float))
        S[~np.isfinite(S)] = -1
        S[S == 0] = 1
        X = ((S + 1) / 2).T
        E = np.einsum("ki,ij,kj->k", X, Q, X) + X @ c + const
    else:
        raise ValueError(solver)
    o = np.argsort(E)
    return X[o], E[o]


def best_of_samples(V, X, k=4):
    """Repair each of the k lowest-energy samples on the view; return the best by true peak (tie: DT saved)."""
    best, bpk, bsv = None, np.inf, -np.inf
    for x in X[:k]:
        xr, _ = PC.repair(V, x, fill=False)
        pk, sv = V.peak(xr), float(V.sts @ xr)
        if pk < bpk - 1e-12 or (pk <= bpk + 1e-12 and sv > bsv):
            best, bpk, bsv = xr, pk, sv
    return best


# ------------------------------------------------------------------ C1: LP + peak-window LNS
def lns(P, k, a, r1, log=print):
    t0 = time.time()
    budget = float(a.get("lns_secs", 20.0))
    nmax = int(a.get("lns_nmax", 1500))
    rng = np.random.default_rng(int(a.get("seed", 0)) * 100 + k)
    x, info = r1(P, k)
    xlp, _, _ = PS.solve_lp(P, lexi=False)
    frac = np.flatnonzero((xlp > 1e-6) & (xlp < 1 - 1e-6))
    bpk, bsv = P.peak(x), float(P.sts @ x)
    info["peak_r1"] = bpk
    Dc = P.Da.tocsc()
    wins = {"milp": 0, "sa": 0, "qubo": 0}
    tries = 0
    it = 0
    while time.time() - t0 < budget:
        it += 1
        L = P.loads(x)
        top = np.argsort(-L)
        ntype = it % 3
        if ntype == 0:
            W = top[:int(rng.choice([3, 5, 8]))]
        elif ntype == 1:
            W = top[:3]
        else:
            c = int(top[int(rng.integers(5))])
            half = int(rng.integers(3, 12))
            W = np.arange(max(0, c - half), min(P.ma, c + half + 1))
        N = np.unique(np.concatenate([Dc.indices[Dc.indptr[w]:Dc.indptr[w + 1]] for w in W] + [np.zeros(0, int)]))
        if ntype == 1:
            N = np.union1d(N, frac)
        N = N[(P.s[N] <= P.B + 1e-9)]
        if len(N) > nmax:
            sel = N[x[N] > 0.5]
            uns = N[x[N] <= 0.5]
            keep_u = rng.choice(uns, size=max(0, min(len(uns), nmax - len(sel))), replace=False) if len(uns) else uns
            N = np.union1d(sel if len(sel) <= nmax // 2 else rng.choice(sel, nmax // 2, replace=False), keep_u)
        if len(N) < 2:
            continue
        V = View(P, N, x)
        xs0 = x[N]
        cands = {}
        # (i) HiGHS sub-MILP
        xm, _ = PS.solve_milp(V, float(a.get("lns_milp_secs", 3.0)), x0=xs0, seed=it)
        if xm is not None:
            xf = x.copy()
            xf[N] = xm
            cands["milp"] = xf
        # (ii) true-objective SA restricted to N
        cm = np.zeros(P.n, bool)
        cm[N] = True
        xl, _ = PS.local_search(P, x, n_moves=int(a.get("lns_sa_moves", 30000)), seed=it, cand=cm)
        cands["sa"] = xl
        # (iii) SA on the sum-of-squares sub-QUBO (target tau = current peak - 2%)
        if len(N) <= nmax:
            Q, cq, const = subqubo(V, xs0, tau=bpk * 0.98, pen=float(a.get("qubo_pen", 0.05)))
            X, _ = qubo_solve(Q, cq, const, "dwave_sa", seed=it, reads=8, sweeps=500)
            xq = best_of_samples(V, X, k=4)
            xf = x.copy()
            xf[N] = xq
            cands["qubo"] = xf
        tries += 1
        best_name, best_x, best_key = None, None, (bpk, -bsv)
        for nm, xc in cands.items():
            if float(P.s @ xc) > P.B + 1e-6:
                continue
            key = (P.peak(xc), -float(P.sts @ xc))
            if key[0] < best_key[0] - 1e-12 or (key[0] <= best_key[0] + 1e-12 and key[1] < best_key[1] - 1e-12):
                best_name, best_x, best_key = nm, xc, key
        if best_name is not None:
            wins[best_name] += 1
            x = best_x
            bpk, bsv = best_key[0], -best_key[1]
    x, _, _, nf = PC.peak_preserving_fill(P, x)
    info.update(lns_iters=tries, lns_wins_milp=wins["milp"], lns_wins_sa=wins["sa"], lns_wins_qubo=wins["qubo"],
                lns_secs=time.time() - t0)
    return x, info


# ------------------------------------------------------------------ C2: EIM-style replica exchange
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


@nb.njit(cache=True, parallel=True)
def _pt_round(X, Ls, uses, temps, B, s, sts, ip, ix, iv, wp, wi, lam, rho, hscale, g, moves, seed,
              best_feas_pk, best_feas_x):
    R, n = X.shape
    Es = np.empty(R)
    for r in nb.prange(R):
        np.random.seed(seed * 1000 + r)
        x = X[r]
        L = Ls[r]
        use = uses[r]
        T = temps[r]
        h = max(0.0, use - B) * hscale
        E = _lse(L, g) + lam * h + 0.5 * rho * h * h
        bpk = best_feas_pk[r]
        for it in range(moves):
            # pick a top window (argmax with prob .5, else random among 3 argmax passes)
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
                    i = -1
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
            if j >= 0:
                _app(L, ip, ix, iv, j, 1.0)
            if i >= 0:
                _app(L, ip, ix, iv, i, -1.0)
            nuse = use + (s[j] if j >= 0 else 0.0) - (s[i] if i >= 0 else 0.0)
            nh = max(0.0, nuse - B) * hscale
            En = _lse(L, g) + lam * nh + 0.5 * rho * nh * nh
            dE = En - E
            if dE <= 0 or np.random.random() < np.exp(-dE / T):
                E = En
                use = nuse
                if j >= 0:
                    x[j] = 1.0
                if i >= 0:
                    x[i] = 0.0
                if use <= B:
                    pk = L.max()
                    if pk < bpk - 1e-12:
                        bpk = pk
                        best_feas_x[r, :] = x
            else:
                if j >= 0:
                    _app(L, ip, ix, iv, j, -1.0)
                if i >= 0:
                    _app(L, ip, ix, iv, i, 1.0)
        uses[r] = use
        Es[r] = E
        best_feas_pk[r] = bpk
    return Es


def eim(P, k, a, r1, log=print):
    t0 = time.time()
    x, info = r1(P, k)
    info["peak_r1"] = P.peak(x)
    Da = P.Da
    Dc = Da.tocsc()
    R = int(a.get("eim_replicas", 24))
    budget = float(a.get("eim_secs", 30.0))
    pk0 = P.peak(x)
    g = float(a.get("g_scale", 3000.0)) / pk0
    Tmin, Tmax = 1e-6 * pk0, 3e-3 * pk0
    temps = np.geomspace(Tmin, Tmax, R)
    X = np.tile(x, (R, 1)).astype(np.float64)
    Ls = np.tile(P.loads(x), (R, 1))
    uses = np.full(R, float(P.s @ x))
    hscale = pk0 / max(P.B, 1.0) * 10     # h in peak units (10x budget fraction)
    lam, rho = 0.0, float(a.get("eim_rho", 50.0))
    bfp = np.full(R, pk0)
    bfx = X.copy()
    args = (P.B, P.s.astype(np.float64), P.sts.astype(np.float64), Da.indptr.astype(np.int64),
            Da.indices.astype(np.int64), Da.data.astype(np.float64), Dc.indptr.astype(np.int64),
            Dc.indices.astype(np.int64))
    rnd = 0
    swaps = 0
    while time.time() - t0 < budget:
        rnd += 1
        Es = _pt_round(X, Ls, uses, temps, *args, lam, rho, hscale, g, int(a.get("eim_moves", 4000)), rnd, bfp, bfx)
        # replica exchange between neighbours
        for r in range((rnd % 2), R - 1, 2):
            d = (1 / temps[r] - 1 / temps[r + 1]) * (Es[r] - Es[r + 1])
            if d >= 0 or np.random.random() < math.exp(d):
                X[[r, r + 1]] = X[[r + 1, r]]
                Ls[[r, r + 1]] = Ls[[r + 1, r]]
                uses[[r, r + 1]] = uses[[r + 1, r]]
                swaps += 1
        # ALM multiplier update on the coldest replica's hinge violation
        h0 = max(0.0, uses[0] - P.B) * hscale
        lam += rho * h0
    r = int(np.argmin(bfp))
    xb = bfx[r].copy()
    if P.peak(xb) >= P.peak(x) - 1e-12:
        xb = x
    xb, _ = PC.repair(P, xb, fill=True)
    info.update(eim_rounds=rnd, eim_swaps=swaps, eim_lambda=lam, eim_secs=time.time() - t0)
    return xb, info


# ------------------------------------------------------------------ C4: matrix-free SB on SoS QUBO + duals
def sb_mf(P, k, a, r1, log=print):
    import torch
    torch.set_num_threads(int(a.get("threads", 2)))
    t0 = time.time()
    x1, info = r1(P, k)
    info["peak_r1"] = P.peak(x1)
    var = PS._useful(P)
    D = P.Da[var].tocsr()
    n, ma = D.shape
    s = P.s[var]
    Dt = torch.sparse_csr_tensor(torch.from_numpy(D.indptr.astype(np.int64)), torch.from_numpy(D.indices.astype(np.int64)),
                                 torch.from_numpy(D.data.astype(np.float32)), size=(n, ma))
    DT = D.T.tocsr()
    DTt = torch.sparse_csr_tensor(torch.from_numpy(DT.indptr.astype(np.int64)), torch.from_numpy(DT.indices.astype(np.int64)),
                                  torch.from_numpy(DT.data.astype(np.float32)), size=(ma, n))
    M = (D.T @ D).toarray()
    D2 = D.multiply(D).tocsr()
    pk1 = P.peak(x1)
    tau = pk1 * float(a.get("sb_tau_frac", 0.97))
    L1 = P.loads(x1)
    alpha = np.where(L1 >= tau, 1.0, 0.05)
    mu = 0.0
    best, bpk, bsv = x1.copy(), pk1, float(P.sts @ x1)
    rounds = int(a.get("sb_rounds", 8))
    agents = int(a.get("sb_agents", 32))
    steps = int(a.get("sb_steps", 800))
    budget = float(a.get("sb_secs", 60.0))
    g = torch.Generator().manual_seed(int(a.get("seed", 0)) * 100 + k)
    rr = 0
    for rr in range(rounds):
        if time.time() - t0 > budget:
            break
        r = P.C - tau
        c = -2.0 * (D @ (alpha * r)) + mu * s
        dQ = np.asarray(D2 @ alpha).ravel()
        Q1 = D @ (alpha * np.asarray(D.sum(0)).ravel())
        AM = alpha[:, None] * M
        JF2 = max(0.25 * (float(np.trace(AM @ AM)) - float((dQ ** 2).sum())), 1e-30)
        h = torch.as_tensor(-0.5 * (Q1 + c), dtype=torch.float32)[:, None]
        dQt = torch.as_tensor(dQ, dtype=torch.float32)[:, None]
        al = torch.as_tensor(alpha, dtype=torch.float32)[:, None]
        hF2 = float((h.double() ** 2).sum())
        xi0 = 0.7 * math.sqrt(n) / math.sqrt(JF2 + 2 * hF2)
        Xs = (torch.rand(n, agents, generator=g) - 0.5) * 0.2
        Ys = (torch.rand(n, agents, generator=g) - 0.5) * 0.2
        dt, a0 = 1.25, 1.0
        for st in range(steps):
            at = a0 * st / steps
            F = Dt @ (al * (DTt @ Xs))
            F = -0.5 * (F - dQt * Xs) + h
            Ys.add_(F, alpha=xi0 * dt).add_(Xs, alpha=-(a0 - at) * dt)
            Xs.add_(Ys, alpha=a0 * dt)
            wall = Xs.abs() > 1
            Xs.clamp_(-1.0, 1.0)
            Ys.masked_fill_(wall, 0.0)
        S = (Xs >= 0).double().numpy()
        # decode: repair each agent and keep the best by true peak
        pks = []
        for j in range(agents):
            xf = np.zeros(P.n)
            xf[var] = S[:, j]
            xr, _ = PC.repair(P, xf, fill=False)
            ok, pk, sv = _better(P, xr, bpk, bsv)
            pks.append(pk)
            if ok:
                best, bpk, bsv = xr, pk, sv
        # window duals / budget price update from the median agent (raw, before repair)
        xm = np.zeros(P.n)
        xm[var] = S[:, int(np.argsort(pks)[len(pks) // 2])]
        Lm = P.loads(xm)
        eta = float(a.get("sb_eta", 0.5))
        alpha = np.maximum(alpha + eta * (Lm - tau) / max(pk1, 1e-12) * 10, 0.0)
        alpha = alpha / max(alpha.max(), 1e-12)
        alpha = np.maximum(alpha, 1e-3)
        viol = (float(P.s @ xm) - P.B) / max(P.B, 1.0)
        mu = max(0.0, mu + float(a.get("sb_eta_mu", 1.0)) * viol * float(np.abs(c).mean()) / max(float(s.mean()), 1e-12))
    best, _, _, _ = PC.peak_preserving_fill(P, best)
    info.update(sb_rounds=rr + 1, sb_secs=time.time() - t0, sb_improved=int(bpk < pk1 - 1e-12))
    return best, info


# ------------------------------------------------------------------ C5: contested-subset QUBO
def contested(P, k, a, r1, log=print):
    t0 = time.time()
    x1, info = r1(P, k)
    info["peak_r1"] = P.peak(x1)
    xlp, lpi, rc = PS.solve_lp(P, lexi=False)
    z = lpi["z_lp"]
    tol = 1e-9
    frac = (xlp > 1e-6) & (xlp < 1 - 1e-6)
    peg1 = (xlp >= 1 - 1e-6) & (rc < -tol)
    peg0 = (xlp <= 1e-6) & (rc > tol)
    Llp = P.loads(xlp)
    delta = float(a.get("c5_delta", 0.03)) * z
    hot = np.flatnonzero(Llp >= z - delta)
    Dc = P.Da.tocsc()
    touch = np.unique(np.concatenate([Dc.indices[Dc.indptr[w]:Dc.indptr[w + 1]] for w in hot] + [np.zeros(0, int)]))
    cont = np.union1d(np.flatnonzero(frac), touch[~peg0[touch] & ~peg1[touch]])
    cont = cont[P.s[cont] <= P.B + 1e-9]
    nmax = int(a.get("c5_nmax", 1500))
    if len(cont) > nmax:   # keep fractional first, then smallest |reduced cost|
        pri = np.where(frac[cont], -1.0, np.abs(rc[cont]))
        cont = cont[np.argsort(pri, kind="stable")[:nmax]]
    base = x1.copy()
    V = View(P, cont, base)
    res = {}
    Q, c, const = subqubo(V, base[cont], tau=z, pen=float(a.get("qubo_pen", 0.05)))
    for solver in a.get("c5_solvers", ["dwave_sa", "dwave_tabu", "mq_bsb", "mq_dsb"]):
        ts = time.time()
        try:
            X, E = qubo_solve(Q, c, const, solver, seed=k, reads=16, sweeps=int(a.get("c5_sweeps", 1000)),
                              secs=float(a.get("c5_tabu_secs", 8)),
                              x0=base[cont] if a.get("c5_warm", True) else None)
            xq = best_of_samples(V, X, k=8)
            xf = base.copy()
            xf[cont] = xq
            xf, _ = PC.repair(P, xf, fill=True)
            res[solver] = (xf, P.peak(xf), time.time() - ts)
        except Exception as ex:
            print(f"[C5] {solver} failed: {ex}", flush=True)
    ts = time.time()
    xm, mi = PS.solve_milp(V, float(a.get("c5_milp_secs", 30)), x0=base[cont])
    if xm is not None:
        xf = base.copy()
        xf[cont] = xm
        xf, _ = PC.repair(P, xf, fill=True)
        res["highs_submilp"] = (xf, P.peak(xf), time.time() - ts)
    for nm, (_, pk, sec) in res.items():
        info[f"c5_peak_{nm}"] = pk * PC.util_scale()
        info[f"c5_secs_{nm}"] = sec
    qs = {nm: v for nm, v in res.items() if nm != "highs_submilp"}
    info["c5_n_cont"] = len(cont)
    info["c5_peak_r1"] = P.peak(x1) * PC.util_scale()
    if not qs:
        return x1, info
    nm = min(qs, key=lambda q: (qs[q][1], -float(P.sts @ qs[q][0])))
    info["c5_best_qubo"] = nm
    xb = qs[nm][0]
    if P.peak(xb) > P.peak(x1) + 1e-12 and not a.get("c5_raw", False):
        info["c5_used_r1_fallback"] = 1
    info["c5_secs"] = time.time() - t0
    return xb, info


# ------------------------------------------------------------------ RB: top-k robust
def robust(P, k, a, r1, log=print):
    kk = int(a.get("topk", 4))
    x, info, _ = PS.solve_lp(P, lexi=True, topk=kk)
    xr = (x >= 1 - 1e-6).astype(float)
    xr, st = PC.repair(P, xr, fill=True)
    info.update(st)
    xl, li = PS.local_search(P, xr, secs=a.get("ls_secs", 10), n_moves=a.get("ls_moves", 200000),
                             seed=a.get("seed", 0), topk_obj=kk)
    info.update(li)

    def tk(z):
        return float(np.sort(P.loads(z))[::-1][:kk].mean())
    if tk(xl) < tk(xr) - 1e-12:
        xr, _, _, _ = PC.peak_preserving_fill(P, xl)
    return xr, info


def make_level_solver(cand, a, r1):
    fn = {"C1": lns, "C2": eim, "C4": sb_mf, "C5": contested, "RB": robust}[cand]
    return lambda P, k: fn(P, k, a, r1)
