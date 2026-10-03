"""Hybrid LNS (Ising family): start from the level's classical start, repeatedly pick a neighbourhood around the
objective-relevant windows and re-optimize it with the EIM sub-sampler (native hinge budget + replica exchange on the
formulation energy, moves restricted to the neighbourhood). Optionally (hl_p_milp > 0) a HiGHS sub-MILP races on some
neighbourhoods; accepted-move shares per sub-solver are reported (the arm counts as Ising only if the EIM branch
contributes most accepted moves)."""
import time

import numpy as np

import q2core as C
import q2anneal as A


class View:
    """sub-problem over a subset N of P's free vars, the rest fixed at xbase (interface of q2core.Sub for q2lp)."""
    def __init__(self, P, N, xbase):
        N = np.asarray(N, np.int64)
        self.N = N
        mask = np.zeros(P.n, bool)
        mask[N] = True
        xo = np.where(mask, 0.0, xbase)
        self.form = P.form
        self.C = P.C - P.Da.T @ xo
        self.B = P.B - float(P.s @ xo)
        self.Da = P.Da[N].tocsr()
        self.Dc = self.Da.tocsc()
        self.s = P.s[N]
        self.sts = P.sts[N]
        self.n = len(N)
        self.ma = P.ma

    def loads(self, xs):
        return self.C - self.Da.T @ xs

    def obj(self, xs):
        return self.form.obj(self.loads(xs))

    def useful(self):
        pos = np.zeros(self.n, bool)
        rows = np.repeat(np.arange(self.n), np.diff(self.Da.indptr))
        pos[rows[self.Da.data > 0]] = True
        return np.flatnonzero(pos & (self.s <= self.B + 1e-9))


def hlns(P, k, dl, cfg, seed, start_solution):
    t0 = time.time()
    x, info = start_solution(P, cfg.get("start", "lp"), dl, cfg, seed)
    rng = np.random.default_rng(int(seed) * 1000 + k)
    bobj, bsts = P.obj(x), float(P.sts @ x)
    wins = {"ising": 0, "milp": 0}
    tries = {"ising": 0, "milp": 0}
    flips = {"ising": 0, "milp": 0}
    nmax = int(cfg.get("hl_nmax", 3000))
    slice_s = float(cfg.get("hl_slice", 0.25))
    p_milp = float(cfg.get("hl_p_milp", 0.0))
    qmax = int(cfg.get("hl_q", 8))
    p_block = float(cfg.get("hl_p_block", 0.3))
    frac_sel = float(cfg.get("hl_frac_sel", 0.5))
    sub_cfg = dict(cfg)
    sub_cfg.setdefault("eim_R", 8)
    Dc = P.Dc
    typ = P.form.typ if P.form.typ < 3 else 2
    while time.time() < dl - 0.05:
        L = P.loads(x)
        order = np.argsort(-L)
        q = int(rng.integers(2, max(qmax, 2) + 1))
        W = list(order[:q])
        if rng.random() < p_block:
            c = int(order[int(rng.integers(min(5, len(order))))])
            half = int(rng.integers(2, 10))
            W += list(range(max(0, c - half), min(P.ma, c + half + 1)))
        if typ == 2 and rng.random() < 0.5:
            above = np.flatnonzero(L > P.form.tau)
            if len(above):
                W += list(rng.choice(above, size=min(len(above), q), replace=False))
        W = np.unique(np.asarray(W, np.int64))
        N = np.unique(np.concatenate([Dc.indices[Dc.indptr[w]:Dc.indptr[w + 1]] for w in W] + [np.zeros(0, np.int64)]))
        # add some selected episodes from elsewhere so that budget can be moved (swaps)
        sel = np.flatnonzero(x > 0.5)
        if len(sel):
            extra = rng.choice(sel, size=min(len(sel), int(frac_sel * max(len(N), 100))), replace=False)
            N = np.union1d(N, extra)
        if len(N) > nmax:
            N = rng.choice(N, size=nmax, replace=False)
        if len(N) < 2:
            continue
        sub = "milp" if rng.random() < p_milp else "ising"
        tries[sub] += 1
        dls = min(dl, time.time() + slice_s)
        if sub == "ising":
            cm = np.zeros(P.n, bool)
            cm[N] = True
            xn, _ = A.eim(P, x, dls, sub_cfg, seed=int(rng.integers(1 << 30)), cand=cm)
        else:
            import q2lp
            V = View(P, N, x)
            xm, _ = q2lp.solve_milp(V, dls, x0=x[N], seed=int(rng.integers(1 << 30)))
            if xm is None:
                continue
            xn = x.copy()
            xn[N] = xm
        if float(P.s @ xn) > P.B + 1e-6:
            xn, _ = P.repair(xn, fill=False)
        ob, sv = P.obj(xn), float(P.sts @ xn)
        if ob < bobj - 1e-15 or (ob <= bobj + 1e-15 and sv > bsts + 1e-9):
            flips[sub] += int(np.sum(np.abs(xn - x) > 0.5))
            x, bobj, bsts = xn, ob, sv
            wins[sub] += 1
    info.update(hl_wins_ising=wins["ising"], hl_wins_milp=wins["milp"], hl_tries_ising=tries["ising"],
                hl_tries_milp=tries["milp"], hl_flips_ising=flips["ising"], hl_flips_milp=flips["milp"],
                hl_time=time.time() - t0)
    return x, info
