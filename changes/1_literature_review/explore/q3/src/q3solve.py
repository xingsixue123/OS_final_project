"""Track A label solver (solver env X/env). Called by PolicyPeakBaleen3 via subprocess on the day-1 instance.

  q3solve.py --inst inst.npz --out sol.npz --cand PT --args '{...}'

Formulation (extended Ising / EIM-style, binary units u = episodes or feature cells):
  E(x) = A * F_peak(L(x)) + beta * (DT_B - DT(x)) * US / m + mu * sum_u t_u |x_u - b_u| / |S_B|
         + lam * sum_(u,v) w_uv |x_u - x_v| / |G|                 (all terms in utilisation-% points)
  s.t.   s . x <= f * B          (native hard budget: infeasible moves are never proposed)
  L_w(x) = C_w - sum_u D_uw x_u  (util %), F_peak = LSE_gamma(L) (mode 0) or mean of the top-k windows (mode 1)
  b = Baleen's own selection at B (trust region), t_u = #episodes of unit u in/out of b.
Solver: parallel tempering (Metropolis flips/swaps biased to the current peak window's units, numba prange over
replicas, replica exchange) -- an Ising-family sampler on the energy above; 100% of the accepted moves come from it.
Labels = selected episodes (Baleen rank inside), then the harness strict-prefix fill in Baleen order up to B
(SCOPE §1: the tail stays in Baleen order), as harness_eval/pbcore.final_order.
Candidates: PT (this solver), BALEEN (identity: Baleen's own prefix through the solver path).
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
import numba as nb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3lib as QL  # noqa: E402

US = QL.US


# ------------------------------------------------------------------ units (episodes or cells)
def episode_cells(I, spec):
    """Cell id per episode from its first training row (what the GBM sees first).
    spec: 'ep' (no cells) or '+'-joined parts: meta (op,ns,user) | op | sz (log2 IO size) | h (history bins of b0 and
    any-older-history) | nacc (#accesses bin, capped at 15 = #rows) | c (chunk-count bin)."""
    if spec in (None, "", "ep"):
        return np.arange(I.n, dtype=np.int64)
    p0 = I.acc_start[:-1]
    meta = I.acc_meta[p0]
    dyn = I.acc_dyn[p0]
    cols = []
    parts = spec.split("+")
    if "meta" in parts:
        cols += [meta[:, 0], meta[:, 1], meta[:, 2]]
    if "op" in parts:
        cols += [meta[:, 0]]
    if "sz" in parts:
        cols += [np.floor(np.log2(np.maximum(meta[:, 5], 1))).astype(np.int64)]
    if "h" in parts:
        cols += [np.digitize(dyn[:, 0], [1, 2, 5, 20]), (dyn[:, 1:6].sum(1) > 0).astype(np.int64)]
    if "nacc" in parts:
        na = np.minimum(np.asarray(I.z["num_accesses"]), 15)
        cols += [np.digitize(na, [2, 3, 5, 9, 15])]
    if "c" in parts:
        cols += [np.digitize(dyn[:, 6], [1, 3, 10, 40])]
    M = np.stack(cols, 1)
    _, cid = np.unique(M, axis=0, return_inverse=True)
    return cid.ravel().astype(np.int64)


def knn_graph(I, k=5):
    """Consistency graph over episodes: k nearest neighbours within the same (op, ns, user) group, in the
    standardized space of the first training row's numeric features + log #rows. Returns symmetric 0/1 csr."""
    p0 = I.acc_start[:-1]
    meta = I.acc_meta[p0].astype(float)
    dyn = I.acc_dyn[p0].astype(float)
    Z = np.c_[np.log2(np.maximum(meta[:, 5], 1)), np.log2(np.maximum(meta[:, 3], 1)), np.log1p(np.maximum(dyn, 0)),
              np.log1p(np.minimum(np.asarray(I.z["num_accesses"], float), 15))]
    Z = (Z - Z.mean(0)) / np.maximum(Z.std(0), 1e-9)
    g = np.unique(meta[:, :3], axis=0, return_inverse=True)[1].ravel()
    rows, cols = [], []
    for gid in np.unique(g):
        idx = np.flatnonzero(g == gid)
        if len(idx) < 2:
            continue
        Zi = Z[idx]
        kk = min(k + 1, len(idx))
        for a0 in range(0, len(idx), 256):
            q = idx[a0:a0 + 256]
            d = ((Z[q][:, None, :] - Zi[None, :, :]) ** 2).sum(-1)
            nn = np.argpartition(d, kk - 1, axis=1)[:, :kk]
            rows.append(np.repeat(q, kk))
            cols.append(idx[nn].ravel())
    rows = np.concatenate(rows)
    cols = np.concatenate(cols)
    keep = rows != cols
    E = sp.coo_matrix((np.ones(keep.sum()), (rows[keep], cols[keep])), shape=(I.n, I.n)).tocsr()
    E = ((E + E.T) > 0).astype(float).tocsr()
    return E


# ------------------------------------------------------------------ PT kernel
@nb.njit(cache=True)
def _peak(L, mode, g, k):
    if mode == 0:
        mx = L.max()
        s = 0.0
        for w in range(L.shape[0]):
            s += math.exp(g * (L[w] - mx))
        return mx + math.log(s) / g
    Ls = np.sort(L)
    s = 0.0
    for i in range(k):
        s += Ls[L.shape[0] - 1 - i]
    return s / k


@nb.njit(cache=True)
def _app(L, ip, ix, iv, u, sign):
    for q in range(ip[u], ip[u + 1]):
        L[ix[q]] -= sign * iv[q]


@nb.njit(cache=True)
def _cons_delta(x, u, gp, gi, gw):
    """Change of sum_v w_uv |x_u - x_v| when x_u flips (x_u = current value before the flip)."""
    d = 0.0
    xu = x[u]
    for q in range(gp[u], gp[u + 1]):
        if x[gi[q]] == xu:
            d += gw[q]
        else:
            d -= gw[q]
    return d


@nb.njit(cache=True, parallel=True)
def pt_round(X, Ls, uses, P, Q, temps, Bc, s, lin, ip, ix, iv, wp, wi, gp, gi, gw, A, mode, g, k, lam_c,
             moves, seed, bestE, bestX, acc):
    """lin[u] = linear energy change for x_u 0->1 (DT blend + trust region); P = A*peak, Q = linear + consistency."""
    R, n = X.shape
    for r in nb.prange(R):
        np.random.seed(seed * 7919 + r)
        x = X[r]
        L = Ls[r]
        use = uses[r]
        T = temps[r]
        p_cur = P[r]
        q_cur = Q[r]
        na = 0
        for it in range(moves):
            w = np.argmax(L)
            rr = np.random.random()
            i = -1
            j = -1
            if rr < 0.4:
                cnt = wp[w + 1] - wp[w]
                if cnt == 0:
                    continue
                j = wi[wp[w] + np.random.randint(cnt)]
                if x[j] > 0.5 or use + s[j] > Bc:
                    continue
            elif rr < 0.8:
                cnt = wp[w + 1] - wp[w]
                if cnt == 0:
                    continue
                j = wi[wp[w] + np.random.randint(cnt)]
                if x[j] > 0.5:
                    continue
                i = np.random.randint(n)
                if x[i] < 0.5 or use - s[i] + s[j] > Bc:
                    continue
            elif rr < 0.9:
                i = np.random.randint(n)
                if x[i] < 0.5:
                    continue
            else:
                j = np.random.randint(n)
                if x[j] > 0.5 or use + s[j] > Bc:
                    continue
            dq = 0.0
            if j >= 0:
                dq += lin[j]
                if lam_c > 0:
                    dq += lam_c * _cons_delta(x, j, gp, gi, gw)
                x[j] = 1.0
                _app(L, ip, ix, iv, j, 1.0)
            if i >= 0:
                dq -= lin[i]
                if lam_c > 0:
                    dq += lam_c * _cons_delta(x, i, gp, gi, gw)
                x[i] = 0.0
                _app(L, ip, ix, iv, i, -1.0)
            p_new = A * _peak(L, mode, g, k)
            dE = p_new - p_cur + dq
            if dE <= 0 or np.random.random() < math.exp(-dE / T):
                p_cur = p_new
                q_cur += dq
                use += (s[j] if j >= 0 else 0.0) - (s[i] if i >= 0 else 0.0)
                na += 1
                if p_cur + q_cur < bestE[r] - 1e-12:
                    bestE[r] = p_cur + q_cur
                    bestX[r, :] = x
            else:
                if j >= 0:
                    x[j] = 0.0
                    _app(L, ip, ix, iv, j, -1.0)
                if i >= 0:
                    x[i] = 1.0
                    _app(L, ip, ix, iv, i, 1.0)
        uses[r] = use
        P[r] = p_cur
        Q[r] = q_cur
        acc[r] += na


def solve_pt(I, a, log=print):
    """Returns the episode selection x (0/1) and stats."""
    t0 = time.time()
    spec = a.get("cells", "ep")
    cid = episode_cells(I, spec)
    K = int(cid.max()) + 1
    E = sp.csr_matrix((np.ones(I.n), (cid, np.arange(I.n))), shape=(K, I.n))
    active = I.active.copy()
    # temporal smoothing of the loads (window aggregation), optional
    agg = int(a.get("win_agg", 1))
    Dw = I.D[:, active]
    Cw = I.C[active]
    if agg > 1:
        m0 = Dw.shape[1]
        grp = np.arange(m0) // agg
        G = sp.csr_matrix((np.ones(m0) / agg, (np.arange(m0), grp)), shape=(m0, grp.max() + 1))
        Dw = (Dw @ G).tocsr()
        Cw = np.asarray(G.T @ Cw).ravel()
    Du = (E @ Dw).tocsr() * US
    Cu = Cw * US
    m = Du.shape[1]
    su = np.asarray(E @ I.s).ravel()
    stsu = np.asarray(E @ I.sts).ravel()
    xb_ep = I.baleen_x()
    bu_in = np.asarray(E @ xb_ep).ravel()            # #Baleen-selected episodes in the unit
    nu = np.asarray(E @ np.ones(I.n)).ravel()
    SB = max(float(xb_ep.sum()), 1.0)
    DTB = float(I.sts @ xb_ep)
    beta = float(a.get("beta", 0.0))
    mu = float(a.get("mu", 0.0))
    lam = float(a.get("lam", 0.0))
    A = float(a.get("A", 1.0))
    f = float(a.get("f", 1.0))
    mode = 0 if a.get("peak", "lse") == "lse" else 1
    gam = float(a.get("gamma", 2.0))
    topk = int(a.get("topk", 5))
    # linear energy: selecting unit u changes DT blend by -beta*sts_u*US/m and the trust term by
    # mu/SB * (#non-Baleen eps in u - #Baleen eps in u)
    lin = -beta * stsu * US / m + mu / SB * ((nu - bu_in) - bu_in)
    # peak-weighted DT (window weights phi_w = (C_w / mean C)^p): rewards savings in busy windows smoothly
    bpw = float(a.get("beta_pw", 0.0))
    if bpw > 0:
        phi = (Cu / max(float(Cu.mean()), 1e-12)) ** float(a.get("pw", 2.0))
        phi = phi / max(float(phi.mean()), 1e-12)
        lin = lin - bpw * np.asarray(Du @ phi).ravel() / m
    const_trust = mu / SB * bu_in.sum()
    # consistency graph (only for episode units)
    if lam > 0 and spec == "ep":
        G = knn_graph(I, k=int(a.get("knn", 5)))
        GW = float(G.nnz) / 2
        gp, gi, gw = G.indptr.astype(np.int64), G.indices.astype(np.int64), G.data.astype(np.float64)
        lam_c = lam / max(GW, 1.0)
    else:
        gp, gi, gw = np.zeros(K + 1, np.int64), np.zeros(0, np.int64), np.zeros(0)
        lam_c = 0.0
    Bc = f * I.B
    # coverage of saturated rows (robustness of the distilled policy to count extrapolation): episodes having a
    # training row with block count b0 >= sat_b0 at an end offset > sat_end_mb MB are force-labeled (x_u = 1);
    # PT optimizes the remaining units with the remaining budget.
    forced = np.zeros(K, bool)
    assert not (a.get("sat_b0") is not None and lam > 0), "sat_b0 + lam not supported"
    if a.get("sat_b0") is not None:
        rows = (I.acc_row == 1) & (I.acc_dyn[:, 0] >= int(a["sat_b0"])) & \
               (I.acc_meta[:, 4] > float(a.get("sat_end_mb", 8)) * (1 << 20))
        fe = np.unique(I.acc_ep[rows])
        forced[np.unique(cid[fe])] = True
        if a.get("sat_max_frac") is not None:      # cap the forced cost (cheapest first)
            fu = np.flatnonzero(forced)
            fu = fu[np.argsort(su[fu], kind="stable")]
            keep = fu[np.cumsum(su[fu]) <= float(a["sat_max_frac"]) * I.B]
            forced[:] = False
            forced[keep] = True
    # start: Baleen's selection mapped to units (units fully inside Baleen's set), repaired to the budget
    if spec == "ep":
        x0 = xb_ep.copy()
    else:
        x0 = (bu_in >= 0.5 * nu).astype(float)
    x0[forced] = 1.0
    order = np.argsort(-np.where(su > 0, stsu / np.maximum(su, 1e-12), -1e9))
    use = float(su @ x0)
    for u in order[::-1]:
        if use <= Bc:
            break
        if x0[u] > 0.5 and not forced[u]:
            x0[u] = 0
            use -= su[u]
    # forced units are removed from the PT's move set by giving them an infinite cost of removal:
    # implemented by excluding them from the unit arrays (fixed at 1) -> fold their loads into C.
    if forced.any():
        Cu = Cu - np.asarray(Du[forced].sum(0)).ravel()
        Bc = Bc - float(su[forced].sum())
        keep_u = np.flatnonzero(~forced)
        remap = -np.ones(K, np.int64)
        remap[keep_u] = np.arange(len(keep_u))
        Du, su, stsu, lin, bu_in, nu = Du[keep_u], su[keep_u], stsu[keep_u], lin[keep_u], bu_in[keep_u], nu[keep_u]
        x0 = x0[keep_u]
        full_K, K = K, len(keep_u)
    else:
        keep_u = np.arange(K)
        full_K = K
    Dc = Du.tocsc()
    R = int(a.get("replicas", 16))
    L0 = Cu - Du.T @ x0
    Lscale = float(L0.max())
    temps = np.geomspace(float(a.get("Tmin", 1e-3)), float(a.get("Tmax", 0.3)), R)
    X = np.tile(x0, (R, 1)).astype(np.float64)
    Ls = np.tile(L0, (R, 1))
    uses = np.full(R, use)

    def energy(x):
        L = Cu - Du.T @ x
        pk = _peak(L, mode, gam, topk)
        q = float(lin @ x)
        if lam_c > 0:
            xx = x[gi]
            rr = np.repeat(np.arange(K), np.diff(gp))
            q += lam_c * float((gw * np.abs(x[rr] - xx)).sum()) / 2.0
        return A * pk, q
    p0, q0 = energy(x0)
    P = np.full(R, p0)
    Q = np.full(R, q0)
    bestE = np.full(R, p0 + q0)
    bestX = X.copy()
    acc = np.zeros(R, np.int64)
    budget = float(a.get("secs", 20.0))
    moves = int(a.get("moves", 3000))
    rnd = swaps = 0
    rng = np.random.default_rng(int(a.get("seed", 0)))
    ts = time.time()
    while time.time() - ts < budget:
        rnd += 1
        pt_round(X, Ls, uses, P, Q, temps, Bc, su.astype(np.float64), lin.astype(np.float64),
                 Du.indptr.astype(np.int64), Du.indices.astype(np.int64), Du.data.astype(np.float64),
                 Dc.indptr.astype(np.int64), Dc.indices.astype(np.int64), gp, gi, gw, A, mode, gam, topk, lam_c,
                 moves, int(a.get("seed", 0)) * 100000 + rnd, bestE, bestX, acc)
        Et = P + Q
        for r in range(rnd % 2, R - 1, 2):
            d = (1 / temps[r] - 1 / temps[r + 1]) * (Et[r] - Et[r + 1])
            if d >= 0 or rng.random() < math.exp(d):
                for arr in (X, Ls):
                    arr[[r, r + 1]] = arr[[r + 1, r]]
                for arr in (uses, P, Q):
                    arr[[r, r + 1]] = arr[[r + 1, r]]
                swaps += 1
    rb = int(np.argmin(bestE))
    xu_k = bestX[rb].copy()
    n_clean = 0
    if a.get("clean", False):
        # drop selected units that are not in Baleen's selection and save nothing in any window (zero-value
        # additions that do not change the loads); the freed budget goes to the Baleen-order fill
        dmax = np.asarray(Du.max(1).todense()).ravel()
        junk = (xu_k > 0.5) & (bu_in < 0.5) & (dmax <= 1e-12)
        n_clean = int(junk.sum())
        xu_k[junk] = 0.0
    xu = np.ones(full_K)
    xu[keep_u] = xu_k
    x = xu[cid]
    # exact energies / stats
    pb, qb = energy(xu_k)
    Lb = Cu - Du.T @ xu_k
    st = dict(units=K, cells=spec, m=m, rounds=rnd, swaps=swaps, accepted=int(acc.sum()), secs=time.time() - t0,
              E0=p0 + q0 + const_trust, E=pb + qb + const_trust, peak_term0=p0, peak_term=pb,
              peak_util=float(Lb.max()), top5_util=float(np.sort(Lb)[::-1][:5].mean()),
              baleen_peak_util=float((Cu - Du.T @ x0).max()) if spec == "ep" else None, n_forced=int(forced.sum()),
              forced_frac_B=float(np.asarray(E @ I.s).ravel()[forced].sum() / I.B),
              flips_vs_baleen=int(np.abs(x - xb_ep).sum()), n_baleen=int(xb_ep.sum()), n_sel=int(x.sum()),
              use_frac=float(I.s @ x / I.B), dt_ratio=float(I.sts @ x / max(DTB, 1e-12)),
              move_share_pt=1.0, n_clean=n_clean)
    log(f"[PT] {json.dumps({k: v for k, v in st.items()}, default=float)}")
    return x, st


# ------------------------------------------------------------------ final order (harness_eval/pbcore.final_order)
def final_order(I, x):
    sel = np.flatnonzero(x > 0.5)
    sel = sel[np.argsort(I.rank[sel], kind="stable")]
    use = float(I.s[sel].sum())
    assert use <= I.B + 1e-6, (use, I.B)
    in_sel = np.zeros(I.n, bool)
    in_sel[sel] = True
    fill = []
    for e in I.base_order:
        if in_sel[e]:
            continue
        if use + I.s[e] > I.B:
            break
        fill.append(e)
        use += I.s[e]
    order_sel = np.r_[sel, np.asarray(fill, np.int64)].astype(np.int64)
    xf = np.zeros(I.n)
    xf[order_sel] = 1
    return order_sel, xf, len(fill)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--args", default="{}")
    o = ap.parse_args()
    a = json.loads(o.args)
    t = time.time()
    I = QL.Inst(o.inst)
    I.active = np.ones(I.m, bool) if a.get("all_windows", True) else I.active
    xb = I.baleen_x()
    if o.cand == "BALEEN":
        x, st = xb.copy(), {"cand": "BALEEN"}
    elif o.cand == "PT":
        x, st = solve_pt(I, a)
    elif o.cand == "JUNK":
        # mechanism CONTROL (not an Ising candidate): Baleen's selection with its lowest-ranked episodes worth
        # junk_frac*B replaced by random zero-value episodes (no positive saving in any window) of similar cost
        rng = np.random.default_rng(int(a.get("seed", 0)))
        x = xb.copy()
        sel = I.base_order[x[I.base_order] > 0.5]
        drop, cost = [], 0.0
        for e in sel[::-1]:
            if cost >= float(a.get("junk_frac", 0.1)) * I.B:
                break
            drop.append(e)
            cost += I.s[e]
        x[drop] = 0
        dmax = np.asarray(I.D.max(1).todense()).ravel()
        pool = np.flatnonzero((x < 0.5) & (dmax <= 1e-12) & (I.s > 0))
        rng.shuffle(pool)
        use = float(I.s @ x)
        added = 0
        for e in pool:
            if use + I.s[e] > I.B:
                continue
            x[e] = 1
            use += I.s[e]
            added += 1
            if use >= float(I.s @ xb) - 1e-9:
                break
        st = {"cand": "JUNK", "dropped": len(drop), "added": added}
    else:
        raise ValueError(o.cand)
    order_sel, xf, nfill = final_order(I, x)
    L = I.loads(xf)
    Lb = I.loads(xb)
    stats = dict(cand=o.cand, args=a, n=I.n, B=I.B, n_sel_core=int(x.sum()), n_fill=nfill, n_label=int(xf.sum()),
                 label_peak_util=float(L.max() * US), baleen_peak_util=float(Lb.max() * US),
                 label_top5=float(np.sort(L)[::-1][:5].mean() * US), baleen_top5=float(np.sort(Lb)[::-1][:5].mean() * US),
                 label_mean=float(L.mean() * US), baleen_mean=float(Lb.mean() * US),
                 jaccard_vs_baleen=float((xf * xb).sum() / max(((xf + xb) > 0).sum(), 1)),
                 dt_ratio=float(I.sts @ xf / max(I.sts @ xb, 1e-12)), use_frac=float(I.s @ xf / I.B),
                 total_secs=time.time() - t, solver=st)
    np.savez(o.out, order_sel=order_sel, x=xf, x_core=x)
    with open(o.out.replace(".npz", ".json"), "w") as f:
        json.dump(stats, f, indent=1, default=float)
    print(f"[q3solve] {o.cand}: label peak {stats['label_peak_util']:.3f} (Baleen {stats['baleen_peak_util']:.3f}) "
          f"top5 {stats['label_top5']:.2f}/{stats['baleen_top5']:.2f} mean {stats['label_mean']:.2f}/{stats['baleen_mean']:.2f} "
          f"J={stats['jaccard_vs_baleen']:.3f} dt={stats['dt_ratio']:.3f} n={stats['n_label']} (fill {nfill}) "
          f"{stats['total_secs']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
