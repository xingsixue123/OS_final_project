"""Analytic headroom of feature-cell (learnable) admission policies on the dev traces (dev only).

A cell policy admits an episode at its FIRST access iff the cell of that access's simulator-style features is
selected (what a GBM that learned cell-consistent labels would do). Evaluated on the full trace (EA_ml episodes):
analytic loads L = C - D^T x, write rate from s, P100 over windows >= 144, the number of selected cells chosen so
the full-trace write rate matches 35.599 MB/s.
Policies:  baleen_cell  cells ranked by day-1 aggregate DT-saved / chunks-written (a smoothed Baleen)
           peak_cell    day-1 min-max LP over cells (nested budgets), rounded + DT fill
           oracle_cell  the same LP solved on the TEST days' own cell aggregates (upper bound, cheating)
References: episode-level Baleen OPT (hindsight) and episode-level peak LP (hindsight), both analytic.
Run in the solver env (numpy/scipy/highspy).  cellan.py <Region> [cellspec ...]
"""
import json
import os
import sys

import numpy as np
import scipy.sparse as sp
import highspy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3lib as QL  # noqa: E402

X = os.environ["X_ROOT"]
INF = highspy.kHighsInf


def cells_of(F, spec):
    """Cell id per row of F (n x 18) for a spec string."""
    cols = []
    op, ns, user, off, end, size = [F[:, i] for i in range(6)]
    b = F[:, 6:12]
    c = F[:, 12:18]
    if "meta" in spec:
        cols += [op, ns, user]
    if "op" in spec and "meta" not in spec:
        cols += [op]
    if "sz" in spec:
        cols += [np.floor(np.log2(np.maximum(size, 1))).astype(np.int64)]
    if "off" in spec:
        cols += [(off > 0).astype(np.int64) + (off >= 4 << 20).astype(np.int64)]
    if "h0" in spec:
        cols += [np.digitize(b[:, 0], [1, 2, 5, 20])]
    if "hany" in spec:
        cols += [(b[:, 1:].sum(1) > 0).astype(np.int64)]
    if "c0" in spec:
        cols += [np.digitize(c[:, 0], [1, 3, 10, 40])]
    M = np.stack(cols, 1)
    _, cid = np.unique(M, axis=0, return_inverse=True)
    return cid.ravel()


def lp_minmax(Dc, Cw, s, B, dts=None, eps=1e-6):
    """min z  s.t. Dc^T x + z >= Cw, s.x <= B, 0<=x<=1 ; then round (x>=0.5) and fill by DT/size within B."""
    n, m = Dc.shape
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    lp = highspy.HighsLp()
    A = sp.vstack([Dc.T.tocsr(), sp.csr_matrix(s[None, :])]).tocsc()
    zc = sp.csc_matrix((np.ones(m), (np.arange(m), np.zeros(m, int))), shape=(m + 1, 1))
    A = sp.hstack([A, zc]).tocsc()
    lp.num_col_ = n + 1
    lp.num_row_ = m + 1
    cost = np.r_[np.zeros(n), 1.0]
    if dts is not None:
        cost[:n] = -eps * dts / max(dts.sum(), 1e-12) * max(Cw.max(), 1e-12)
    lp.col_cost_ = cost
    lp.col_lower_ = np.r_[np.zeros(n), -INF]
    lp.col_upper_ = np.r_[np.ones(n), INF]
    lp.row_lower_ = np.r_[Cw, -INF]
    lp.row_upper_ = np.r_[np.full(m, INF), B]
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = A.indptr.astype(np.int32)
    lp.a_matrix_.index_ = A.indices.astype(np.int32)
    lp.a_matrix_.value_ = A.data.astype(float)
    h.passModel(lp)
    h.run()
    x = np.array(h.getSolution().col_value)[:n]
    xr = (x >= 0.5).astype(float)
    use = float(s @ xr)
    while use > B + 1e-9:      # drop the lowest-fraction selected cell
        sel = np.flatnonzero(xr > 0)
        j = sel[np.argmin(x[sel])]
        xr[j] = 0
        use -= s[j]
    return xr, x


def main():
    region = sys.argv[1]
    specs = sys.argv[2:] or ["meta", "meta_sz", "meta_sz_off", "meta_sz_h0_hany", "meta_sz_off_h0_hany_c0"]
    I = QL.Inst(os.path.join(X, "common", "inst", f"fullml_{region}_s0.npz"))
    F = np.load(os.path.join(X, "q3", "work", "cache", f"simfeat_fullml_{region}_s0.npz"))["F"]
    I1 = QL.Inst(os.path.join(X, "common", "inst", f"day1_{region}_s0.npz"))
    B1 = I1.B
    first = I.acc_start[:-1]
    Fe = F[first]                                  # first-access features per episode
    day1 = I.ts0 < I.t0 + 86400
    w1 = np.arange(I.m) < 144
    wt = ~w1
    Dcsc = I.D.tocsc()
    D1 = I.D[:, w1]
    Dt = I.D[:, wt]
    out = []
    xb = I.baleen_x()
    ref = dict(policy="baleen_opt_episode", peak=I.peak(xb), wr=I.wr(xb))
    out.append(ref)
    print(region, json.dumps(ref))
    for spec in specs:
        cid = cells_of(Fe, spec)
        K = cid.max() + 1
        E = sp.csr_matrix((np.ones(I.n), (cid, np.arange(I.n))), shape=(K, I.n))
        E1 = E.multiply(day1[None, :]).tocsr()
        Et = E.multiply(~day1[None, :]).tocsr()
        d1 = (E1 @ D1).tocsr()                     # day-1 episodes' savings in day-1 windows
        s1 = np.asarray(E1 @ I.s).ravel()
        st1 = np.asarray(E1 @ I.sts).ravel()
        dt = (Et @ Dt).tocsr()
        stt = np.asarray(Et @ I.s).ravel()
        C1 = I.C[w1]
        Ct = I.C[wt]
        n_cells_d1 = int((s1 > 0).sum())
        # evaluate a cell selection on the full trace
        def ev(xc):
            x = xc[cid]
            return I.peak(x), I.wr(x), float(np.sort(I.loads(x)[I.active])[::-1][:5].mean() * QL.US)
        # (a) Baleen-cell: rank by day-1 DT/size; choose prefix so full-trace WR ~ 35.599
        sc = np.where(s1 > 0, st1 / np.maximum(s1, 1e-9), -np.inf)
        order = np.argsort(-sc)
        order = order[np.isfinite(sc[order])]
        s_full = np.asarray(E @ I.s).ravel()
        cs = np.cumsum(s_full[order])
        kk = int(np.searchsorted(cs, I.B))
        xc = np.zeros(K)
        xc[order[:kk]] = 1
        pk, wr, t5 = ev(xc)
        r = dict(policy="baleen_cell", spec=spec, cells=int(K), cells_day1=n_cells_d1, sel=int(xc.sum()), peak=pk, wr=wr, top5=t5)
        out.append(r)
        print(json.dumps(r, default=float), flush=True)
        # (b) peak-cell on day 1 and (c) oracle on test days: nested budgets, pick WR-matched level
        for pol, Dm, Cw, ss, stsv, Bref in [("peak_cell", d1, C1, s1, st1, B1),
                                            ("oracle_cell", dt, Ct, stt, np.asarray(Et @ I.sts).ravel(), I.B - B1)]:
            best = None
            for f in [0.6, 0.8, 1.0, 1.2, 1.4, 1.7, 2.0]:
                xs, xl = lp_minmax(Dm, Cw, ss, f * Bref, dts=stsv)
                pk, wr, t5 = ev(xs)
                rr = dict(policy=pol, spec=spec, f=f, sel=int(xs.sum()), peak=pk, wr=wr, top5=t5,
                          lp_obj=float((Cw - Dm.T @ xl).max() * QL.US))
                if best is None or abs(wr - QL.TARGET_WR) < abs(best["wr"] - QL.TARGET_WR):
                    best = rr
                if wr > 1.3 * QL.TARGET_WR:
                    break
            out.append(best)
            print(json.dumps(best, default=float), flush=True)
    json.dump(out, open(os.path.join(X, "q3", "results", f"cellan_{region}.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
