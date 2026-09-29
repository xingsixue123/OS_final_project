"""Custom single-flip / swap simulated annealing on the TRUE objective (no QUBO).

State: x, per-window loads L_w, budget use. Moves touch only an episode's 1-3 windows.
Objective for acceptance: smooth max F(L) = (1/g) log sum_w exp(g L_w) (g large, -> max L),
budget is HARD (infeasible adds/swaps rejected). Tracks best TRUE peak max_w L_w.
Moves: (a) swap: add an unselected episode covering one of the top-3 load windows, drop a
random selected one; (b) add (if it fits); (c) drop a random selected episode.
"""
import time
import numpy as np
import numba as nb


@nb.njit(cache=True)
def _lse(L, g):
    mx = L.max()
    s = 0.0
    for w in range(L.shape[0]):
        s += np.exp(g * (L[w] - mx))
    return mx + np.log(s) / g


@nb.njit(cache=True)
def _apply(L, st, ln, V, e, sign):
    for k in range(ln[e]):
        L[st[e] + k] -= sign * V[e, k]


@nb.njit(cache=True)
def _sa(x, L, use, W, s, st, ln, V, wptr, wind, n_moves, T0, T1, g, seed):
    np.random.seed(seed)
    n = x.shape[0]
    m = L.shape[0]
    sel = np.empty(n, np.int64)
    pos = -np.ones(n, np.int64)
    ns = 0
    for e in range(n):
        if x[e] > 0.5:
            sel[ns] = e
            pos[e] = ns
            ns += 1
    F = _lse(L, g)
    best_pk = L.max()
    best_x = x.copy()
    top = np.empty(3, np.int64)
    for it in range(n_moves):
        T = T0 * (T1 / T0) ** (it / n_moves)
        # top-3 windows
        Ls = L.copy()
        for k in range(3):
            j = np.argmax(Ls)
            top[k] = j
            Ls[j] = -1e300
        r = np.random.random()
        if r < 0.7 and ns > 0:
            w = top[np.random.randint(3)]
            cnt = wptr[w + 1] - wptr[w]
            if cnt == 0:
                continue
            j = wind[wptr[w] + np.random.randint(cnt)]
            if x[j] > 0.5:
                continue
            i = sel[np.random.randint(ns)]
            if use - s[i] + s[j] > W:
                continue
            _apply(L, st, ln, V, j, 1.0)
            _apply(L, st, ln, V, i, -1.0)
            Fn = _lse(L, g)
            dF = Fn - F
            if dF <= 0 or np.random.random() < np.exp(-dF / T):
                F = Fn
                use += s[j] - s[i]
                x[j] = 1.0
                x[i] = 0.0
                p = pos[i]
                sel[p] = j
                pos[j] = p
                pos[i] = -1
            else:
                _apply(L, st, ln, V, i, 1.0)
                _apply(L, st, ln, V, j, -1.0)
        elif r < 0.85:
            w = top[np.random.randint(3)]
            cnt = wptr[w + 1] - wptr[w]
            if cnt == 0:
                continue
            j = wind[wptr[w] + np.random.randint(cnt)]
            if x[j] > 0.5 or use + s[j] > W:
                continue
            _apply(L, st, ln, V, j, 1.0)
            Fn = _lse(L, g)
            dF = Fn - F
            if dF <= 0 or np.random.random() < np.exp(-dF / T):
                F = Fn
                use += s[j]
                x[j] = 1.0
                sel[ns] = j
                pos[j] = ns
                ns += 1
            else:
                _apply(L, st, ln, V, j, -1.0)
        else:
            if ns == 0:
                continue
            p = np.random.randint(ns)
            i = sel[p]
            _apply(L, st, ln, V, i, -1.0)
            Fn = _lse(L, g)
            dF = Fn - F
            if dF <= 0 or np.random.random() < np.exp(-dF / T):
                F = Fn
                use -= s[i]
                x[i] = 0.0
                last = sel[ns - 1]
                sel[p] = last
                pos[last] = p
                pos[i] = -1
                ns -= 1
            else:
                _apply(L, st, ln, V, i, 1.0)
        if (it & 255) == 0:
            F = _lse(L, g)  # limit drift
        pk = L.max()
        if pk < best_pk - 1e-15:
            best_pk = pk
            best_x[:] = x
    return best_x, best_pk


def local_search(inst, x0, n_moves=None, seed=0, g_scale=2000.0, T0_frac=2e-3, T1_frac=1e-6):
    t = time.time()
    n, m = inst["n"], inst["m"]
    if n_moves is None:
        n_moves = int(min(3e7, max(2e6, 300 * n)))
    Dc = inst["Dcsc"]
    wptr = Dc.indptr.astype(np.int64)
    wind = Dc.indices.astype(np.int64)
    x = (np.asarray(x0) > 0.5).astype(np.float64)
    L = inst["C"] - inst["D"].T @ x
    use = float(inst["s"] @ x)
    assert use <= inst["W"] * (1 + 1e-9), "warm start must be feasible"
    pk0 = float(L.max())
    g = g_scale / pk0
    T0, T1 = T0_frac * pk0, T1_frac * pk0
    bx, bpk = _sa(x, L.copy(), use, inst["W"], inst["s"].astype(np.float64), inst["start"], inst["length"],
                  inst["vals"].astype(np.float64), wptr, wind, int(n_moves), T0, T1, g, int(seed))
    return bx, dict(ls_moves=int(n_moves), ls_time=time.time() - t, ls_g=g, ls_T0=T0, ls_T1=T1)
