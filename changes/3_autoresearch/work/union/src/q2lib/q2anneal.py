"""Annealing kernels (numba) shared by the classical local search and the Ising-family EIM sampler.

The low-level move/energy kernel is IDENTICAL for both families so that speed is not a confound. The families differ
exactly in what the protocol says distinguishes them:
  LS  (classical, "true-objective local search, no QUBO"): hard budget (moves that break s.x <= B are rejected),
       objective = the formulation's objective on the true loads (F1 acceptance on LSE_g(L) with large g, i.e. max
       with a tie-count bonus, the harness R3 design); nch independent chains (one per thread), geometric cooling over
       the level's time, optional restarts from the incumbent (iterated SA).
  EIM (Ising family, Extended-Ising-Machine style): energy = formulation energy + native hinge budget term
       lam*h + rho/2*h^2 (h = (s.x - B)_+, i.e. an inequality handled natively, not by slack/QUBO penalty), ALM update
       of lam, replica exchange (parallel tempering) over a temperature ladder; best feasible replica state kept.
       penalty mode 'quad' = plain QUBO penalty P*(s.x - B)^2 (SA/PT on a QUBO energy).
Objective types: 0 = F1 (LSE_g), 1 = F2a (top-k mean), 2 = F2b (sum of squared hinge (L - tau)_+^2 / ma).
"""
import math
import time

import numpy as np
import numba as nb

from q2core import obj_nb, topk_sum


@nb.njit(cache=True)
def _lse_init(L, g):
    M = L.max()
    S = 0.0
    for w in range(L.shape[0]):
        S += math.exp(g * (L[w] - M))
    return M, S


@nb.njit(cache=True)
def _sq_init(L, tau):
    Q = 0.0
    for w in range(L.shape[0]):
        v = L[w] - tau
        if v > 0:
            Q += v * v
    return Q


@nb.njit(cache=True)
def _hot(L, topw, hot, typ, tau):
    """indices of the topw largest loads (typ 2: restricted to loads above tau when possible)"""
    m = L.shape[0]
    Ls = L.copy()
    cnt = 0
    for j in range(topw):
        a = np.argmax(Ls)
        if typ == 2 and Ls[a] <= tau and cnt > 0:
            break
        hot[j] = a
        Ls[a] = -1e300
        cnt += 1
    return cnt


@nb.njit(cache=True)
def _move_apply(L, ip, ix, iv, j, i, ridx, rold):
    """apply add j / drop i to L; record (window, old value) for up to 64 touched entries.
    returns (nt, big) where big = more than 64 entries touched (then undo re-applies the rows)."""
    nt = 0
    big = False
    if j >= 0:
        for q in range(ip[j], ip[j + 1]):
            w = ix[q]
            if nt < 64:
                ridx[nt] = w
                rold[nt] = L[w]
                nt += 1
            else:
                big = True
            L[w] -= iv[q]
    if i >= 0:
        for q in range(ip[i], ip[i + 1]):
            w = ix[q]
            if nt < 64:
                ridx[nt] = w
                rold[nt] = L[w]
                nt += 1
            else:
                big = True
            L[w] += iv[q]
    return nt, big


@nb.njit(cache=True)
def _move_undo(L, ip, ix, iv, j, i, ridx, rold, nt, big):
    if big:
        if j >= 0:
            for q in range(ip[j], ip[j + 1]):
                L[ix[q]] += iv[q]
        if i >= 0:
            for q in range(ip[i], ip[i + 1]):
                L[ix[q]] -= iv[q]
    else:
        for t in range(nt - 1, -1, -1):
            L[ridx[t]] = rold[t]


@nb.njit(cache=True)
def _is_first(ridx, t):
    w = ridx[t]
    for u in range(t):
        if ridx[u] == w:
            return False
    return True


@nb.njit(cache=True)
def chain(x, L, use, sel, pos, ns, T, B, s, sts, ip, ix, iv, wp, wi, wv, cand, typ, k, tau, g,
          soft, pmode, lam, rho, hscale, moves, p_add, p_swap, topw, refresh, seed, bx, bstate):
    """One Metropolis chain at temperature T for `moves` proposals. State (x, L, use, sel/pos/ns) updated in place.
    bstate = [best_val, best_sts, has_best]; bx = best feasible x. Returns (use, ns, E, n_acc, n_prop)."""
    np.random.seed(seed)
    m = L.shape[0]
    hot = np.empty(max(topw, 1), np.int64)
    nh = _hot(L, topw, hot, typ, tau)
    M = 0.0
    S = 1.0
    Q = 0.0
    if typ == 0:
        M, S = _lse_init(L, g)
        Eo = M + math.log(S) / g
    elif typ == 1:
        Eo = topk_sum(L, k) / k
    else:
        Q = _sq_init(L, tau)
        Eo = Q / m
    if soft:
        if pmode == 0:
            h = max(0.0, use - B) * hscale
            Epen = lam * h + 0.5 * rho * h * h
        else:
            hh = (use - B) * hscale
            Epen = rho * hh * hh
    else:
        Epen = 0.0
    E = Eo + Epen
    sv = 0.0
    for q in range(ns):
        sv += sts[sel[q]]
    n_acc = 0
    n_prop = 0
    last_copy = -1000000
    ridx = np.empty(64, np.int64)
    rold = np.empty(64)
    for it in range(moves):
        if it % refresh == 0 and it > 0:
            nh = _hot(L, topw, hot, typ, tau)
            if typ == 0:
                M, S = _lse_init(L, g)
            elif typ == 2:
                Q = _sq_init(L, tau)
        r = np.random.random()
        i = -1
        j = -1
        if r < p_add + p_swap:
            w = hot[np.random.randint(nh)]
            cnt = wp[w + 1] - wp[w]
            if cnt == 0:
                continue
            qq = wp[w] + np.random.randint(cnt)
            j = wi[qq]
            if x[j] > 0.5 or not cand[j] or wv[qq] <= 0:
                continue
            if r >= p_add:
                if ns == 0:
                    continue
                i = sel[np.random.randint(ns)]
        else:
            if ns == 0:
                continue
            i = sel[np.random.randint(ns)]
        nuse = use + (s[j] if j >= 0 else 0.0) - (s[i] if i >= 0 else 0.0)
        if (not soft) and nuse > B + 1e-9:
            continue
        n_prop += 1
        nt, big = _move_apply(L, ip, ix, iv, j, i, ridx, rold)
        M2 = M
        S2 = S
        Q2 = Q
        if typ == 0:
            if big:
                M2, S2 = _lse_init(L, g)
            else:
                ovf = False
                for t in range(nt):
                    if not _is_first(ridx, t):
                        continue
                    w = ridx[t]
                    b = g * (L[w] - M2)
                    if b > 600.0:
                        ovf = True
                        break
                    S2 += math.exp(b) - math.exp(g * (rold[t] - M2))
                if ovf or S2 <= 1e-300:
                    M2, S2 = _lse_init(L, g)
            Eo2 = M2 + math.log(S2) / g
        elif typ == 1:
            Eo2 = topk_sum(L, k) / k
        else:
            if big:
                Q2 = _sq_init(L, tau)
            else:
                for t in range(nt):
                    if not _is_first(ridx, t):
                        continue
                    w = ridx[t]
                    a = rold[t] - tau
                    b = L[w] - tau
                    Q2 += (b * b if b > 0 else 0.0) - (a * a if a > 0 else 0.0)
            Eo2 = Q2 / m
        if soft:
            if pmode == 0:
                h2 = max(0.0, nuse - B) * hscale
                Epen2 = lam * h2 + 0.5 * rho * h2 * h2
            else:
                hh = (nuse - B) * hscale
                Epen2 = rho * hh * hh
        else:
            Epen2 = 0.0
        E2 = Eo2 + Epen2
        dE = E2 - E
        if dE <= 0.0 or np.random.random() < math.exp(-dE / T):
            n_acc += 1
            E = E2
            M = M2
            S = S2
            Q = Q2
            use = nuse
            if j >= 0:
                x[j] = 1.0
                sv += sts[j]
            if i >= 0:
                x[i] = 0.0
                sv -= sts[i]
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
            if use <= B + 1e-9:
                if typ == 0:
                    val = L.max()
                else:
                    val = Eo2
                better = bstate[2] < 0.5 or val < bstate[0] - 1e-12 or (val <= bstate[0] + 1e-12 and sv > bstate[1] + 1e-9)
                if better and (it - last_copy >= 256 or bstate[2] < 0.5 or val < bstate[0] - 1e-6 * abs(bstate[0])):
                    bstate[0] = val
                    bstate[1] = sv
                    bstate[2] = 1.0
                    bx[:] = x
                    last_copy = it
        else:
            _move_undo(L, ip, ix, iv, j, i, ridx, rold, nt, big)
    # end-of-round check of the current state
    if use <= B + 1e-9:
        if typ == 0:
            val = L.max()
        elif typ == 1:
            val = topk_sum(L, k) / k
        else:
            val = _sq_init(L, tau) / m
        if bstate[2] < 0.5 or val < bstate[0] - 1e-12 or (val <= bstate[0] + 1e-12 and sv > bstate[1] + 1e-9):
            bstate[0] = val
            bstate[1] = sv
            bstate[2] = 1.0
            bx[:] = x
    return use, ns, E, n_acc, n_prop


@nb.njit(cache=True, parallel=True)
def run_round(X, Ls, uses, SEL, POS, NS, temps, B, s, sts, ip, ix, iv, wp, wi, wv, cand, typ, k, tau, g,
              soft, pmode, lam, rho, hscale, moves, p_add, p_swap, topw, refresh, seed, BX, BST, Es, ACC):
    R = X.shape[0]
    for r in nb.prange(R):
        u, nsr, E, na, npr = chain(X[r], Ls[r], uses[r], SEL[r], POS[r], NS[r], temps[r], B, s, sts, ip, ix, iv, wp,
                                   wi, wv, cand, typ, k, tau, g, soft, pmode, lam, rho, hscale, moves, p_add, p_swap,
                                   topw, refresh, seed * 7919 + r * 104729 + 1, BX[r], BST[r])
        uses[r] = u
        NS[r] = nsr
        Es[r] = E
        ACC[r, 0] += na
        ACC[r, 1] += npr


def _init_states(P, x0, R, cand):
    n = P.n
    X = np.tile((np.asarray(x0) > 0.5).astype(np.float64), (R, 1))
    L0 = P.loads(X[0]).astype(np.float64)
    Ls = np.tile(L0, (R, 1))
    uses = np.full(R, float(P.s @ X[0]))
    SEL = np.zeros((R, n), np.int64)
    POS = -np.ones((R, n), np.int64)
    idx = np.flatnonzero((X[0] > 0.5) & cand)
    SEL[:, :len(idx)] = idx
    POS[:, idx] = np.arange(len(idx))
    NS = np.full(R, len(idx), np.int64)
    return X, Ls, uses, SEL, POS, NS


def _typ(P):
    return P.form.typ if P.form.typ < 3 else 2


def _scale(P, x0):
    """reference objective scale (for temperatures) and g for F1."""
    L = P.loads(x0)
    pk = float(L.max())
    typ = _typ(P)
    if typ == 2:
        ref = max(P.obj(x0), 1e-12)
    else:
        ref = pk
    return pk, ref


def local_search(P, x0, deadline, cfg, seed=0, cand=None):
    """Classical true-objective SA with a hard budget: nch independent chains, geometric cooling over the time budget,
    restart from the incumbent every `restart_every` rounds (0 = never)."""
    t0 = time.time()
    nch = int(cfg.get("ls_chains", 8))
    moves = int(cfg.get("ls_moves", 20000))
    T0f, T1f = float(cfg.get("ls_T0", 2e-3)), float(cfg.get("ls_T1", 1e-6))
    cm = np.ones(P.n, np.bool_) if cand is None else np.asarray(cand, np.bool_)
    x0 = (np.asarray(x0) > 0.5).astype(np.float64)
    if float(P.s @ x0) > P.B + 1e-9:
        x0, _ = P.repair(x0, fill=False)
    pk, ref = _scale(P, x0)
    g = float(cfg.get("g_scale", 3000.0)) / max(pk, 1e-12)
    typ = _typ(P)
    X, Ls, uses, SEL, POS, NS = _init_states(P, x0, nch, cm)
    BX = X.copy()
    BST = np.zeros((nch, 3))
    Es = np.zeros(nch)
    ACC = np.zeros((nch, 2), np.int64)
    rounds = 0
    restart = int(cfg.get("ls_restart_every", 0))
    p_add, p_swap = float(cfg.get("p_add", 0.2)), float(cfg.get("p_swap", 0.6))
    topw = int(cfg.get("topw", 8))
    refresh = int(cfg.get("refresh", 64))
    T_total = max(deadline - t0, 1e-3)
    while True:
        frac = min((time.time() - t0) / T_total, 1.0)
        T = T0f * ref * (T1f / T0f) ** frac
        temps = np.full(nch, T)
        run_round(X, Ls, uses, SEL, POS, NS, temps, P.B, P.s, P.sts, P.ip, P.ix, P.iv, P.wp, P.wi, P.wv, cm, typ,
                  P.form.k, P.form.tau, g, False, 0, 0.0, 0.0, 0.0, moves, p_add, p_swap, topw, refresh,
                  seed * 1000003 + rounds, BX, BST, Es, ACC)
        rounds += 1
        if time.time() >= deadline:
            break
        if restart > 0 and rounds % restart == 0:
            b = int(np.argmin(np.where(BST[:, 2] > 0.5, BST[:, 0], np.inf)))
            if BST[b, 2] > 0.5:
                xb = BX[b].copy()
                X[:], Ls[:], uses[:], SEL[:], POS[:], NS[:] = _init_states(P, xb, nch, cm)
    ok = BST[:, 2] > 0.5
    if not ok.any():
        return x0, dict(ls_rounds=rounds, ls_acc=int(ACC[:, 0].sum()), ls_prop=int(ACC[:, 1].sum()))
    vals = np.where(ok, BST[:, 0], np.inf)
    b = int(np.argmin(vals))
    xb = BX[b].copy()
    if P.obj(xb) > P.obj(x0) + 1e-15:
        xb = x0
    return xb, dict(ls_rounds=rounds, ls_acc=int(ACC[:, 0].sum()), ls_prop=int(ACC[:, 1].sum()),
                    ls_time=time.time() - t0)


def eim(P, x0, deadline, cfg, seed=0, cand=None):
    """Ising-family EIM-style sampler: native hinge budget (or QUBO penalty), ALM multiplier, replica exchange."""
    t0 = time.time()
    R = int(cfg.get("eim_R", 16))
    moves = int(cfg.get("eim_moves", 20000))
    Tmin_f, Tmax_f = float(cfg.get("eim_Tmin", 1e-6)), float(cfg.get("eim_Tmax", 3e-3))
    pmode = 0 if cfg.get("eim_pmode", "hinge") == "hinge" else 1
    cm = np.ones(P.n, np.bool_) if cand is None else np.asarray(cand, np.bool_)
    x0 = (np.asarray(x0) > 0.5).astype(np.float64)
    pk, ref = _scale(P, x0)
    g = float(cfg.get("g_scale", 3000.0)) / max(pk, 1e-12)
    typ = _typ(P)
    anneal = float(cfg.get("eim_anneal", 0.0))     # ladder shrink factor over time (0 = fixed ladder)
    base_temps = np.geomspace(Tmin_f * ref, Tmax_f * ref, R)
    X, Ls, uses, SEL, POS, NS = _init_states(P, x0, R, cm)
    BX = X.copy()
    BST = np.zeros((R, 3))
    Es = np.zeros(R)
    ACC = np.zeros((R, 2), np.int64)
    hscale = ref / max(P.B, 1.0) * float(cfg.get("eim_hscale", 10.0))
    lam, rho = float(cfg.get("eim_lam0", 0.0)), float(cfg.get("eim_rho", 50.0))
    eta = float(cfg.get("eim_eta", 1.0))
    p_add, p_swap = float(cfg.get("p_add", 0.2)), float(cfg.get("p_swap", 0.6))
    topw = int(cfg.get("topw", 8))
    refresh = int(cfg.get("refresh", 64))
    rng = np.random.default_rng(seed)
    rounds = swaps = 0
    T_total = max(deadline - t0, 1e-3)
    order = np.arange(R)          # order[slot] = replica index at temperature slot
    while True:
        frac = min((time.time() - t0) / T_total, 1.0)
        temps_slot = base_temps * (1.0 - anneal * frac)
        temps = np.empty(R)
        temps[order] = temps_slot
        run_round(X, Ls, uses, SEL, POS, NS, temps, P.B, P.s, P.sts, P.ip, P.ix, P.iv, P.wp, P.wi, P.wv, cm, typ,
                  P.form.k, P.form.tau, g, True, pmode, lam, rho, hscale, moves, p_add, p_swap, topw, refresh,
                  seed * 1000003 + rounds, BX, BST, Es, ACC)
        rounds += 1
        # replica exchange between neighbouring temperature slots
        for a in range(rounds % 2, R - 1, 2):
            ra, rb = order[a], order[a + 1]
            d = (1.0 / temps_slot[a] - 1.0 / temps_slot[a + 1]) * (Es[ra] - Es[rb])
            if d >= 0 or rng.random() < math.exp(d):
                order[a], order[a + 1] = rb, ra
                swaps += 1
        # ALM multiplier update from the coldest replica's hinge violation
        cold = order[0]
        h0 = max(0.0, uses[cold] - P.B) * hscale
        if pmode == 0:
            lam += eta * rho * h0
        if time.time() >= deadline:
            break
    ok = BST[:, 2] > 0.5
    info = dict(eim_rounds=rounds, eim_swaps=swaps, eim_lambda=lam, eim_acc=int(ACC[:, 0].sum()),
                eim_prop=int(ACC[:, 1].sum()), eim_time=time.time() - t0)
    if not ok.any():
        # no feasible state visited: return the coldest replica (the shared repair fixes the budget)
        return X[order[0]].copy(), dict(info, eim_feasible=0)
    b = int(np.argmin(np.where(ok, BST[:, 0], np.inf)))
    return BX[b].copy(), dict(info, eim_feasible=1)
