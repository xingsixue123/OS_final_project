"""AR plan B (solver env, numba): ONE load x access-class multiplier table shared by all instances ("universal"),
fitted by an Ising solver on the pooled TRAINING-WINDOW packs of several instances (cls_pack.py packs; buckets are
each instance's own day-1 load quantiles, so the table is defined in quantile space and deploys causally on any
instance: edges from that instance's day-1, multipliers from the pooled fit).

Energy = mean over packs p of [peak_day1_p(m) + 0.1 * top5_day1_p(m)] + the cls_fit.py penalties (LAM field, MU class
coupling, PMONO load-monotone, and class-monotone for the 'm' solvers). Hard budget repair per pack (W1_p), as WP10.
Solvers: ptm (parallel tempering, Ising family) and cdm (coordinate descent, classical), same energy, same wall budget.

Leave-one-instance-out (honest dev estimate): --holdout <inst> fits on every listed pack except that instance's;
the table is then deployed on the held-out instance only.

  PY=$SOLVER_PY src/sbx.sh src/cls_pool.py --mode dev --base B --insts <DEV8...> --reps 1 2 3 --holdout Region7_s0 \
      --solvers ptm cdm --budget 240 --tag loo
-> tables/<mode>/pool_<tag>_<holdout|all>_<base>_<solver>.json (mult only; edges are per instance) + ledger
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cls_fit as F  # noqa: E402

W = F.W


class Pooled:
    def __init__(self, paths, cmono):
        self.P = [F.Problem(p, cmono=cmono) for p in paths]
        self.J, self.n_cells = self.P[0].J, self.P[0].n_cells
        assert all(p.n_cells == self.n_cells for p in self.P)
        self.cmono = cmono
        self.logg = np.log2(F.GRID)
        self.cache = {}
        self.n_eval = 0

    def parts(self, v):
        key = tuple(int(x) for x in v)
        if key in self.cache:
            return self.cache[key]
        pk, t5 = [], []
        for P in self.P:
            a = list(P.args)
            a[2] = F.GRID[np.asarray(v, np.int64)]
            p_, t_, _, _ = F.replay(*a)
            pk.append(p_)
            t5.append(t_)
        f, viol, pen = F.penalty(np.asarray(v, np.int64), self.J, F.K, F.LAM, F.MU, F.PMONO, self.logg, self.cmono)
        self.n_eval += 1
        out = dict(E=float(np.mean(pk)) + F.TOP5W * float(np.mean(t5)) + pen, peak=float(np.mean(pk)),
                   top5=float(np.mean(t5)), field=f, viol=viol, peaks=pk)
        self.cache[key] = out
        return out

    def E(self, v):
        return self.parts(v)["E"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dev"], default="dev")
    ap.add_argument("--base", choices=["A", "B"], required=True)
    ap.add_argument("--insts", nargs="+", required=True)
    ap.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--holdout", default="all")
    ap.add_argument("--solvers", nargs="+", default=["ptm", "cdm"])
    ap.add_argument("--budget", type=float, default=240.0)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--tag", default="loo")
    o = ap.parse_args()
    pdir = os.path.join(W, "work", "packs", o.mode)
    keys = [f"{i}_{o.base}_r{k}" for i in o.insts if i != o.holdout for k in o.reps]
    ledger = os.path.join(W, "results", f"pool_solves_{o.mode}.csv")
    for s in o.solvers:
        name = f"pool_{o.tag}_{o.holdout}_{o.base}_{s}"
        out = os.path.join(W, "tables", o.mode, name + ".json")
        if os.path.exists(out):
            continue
        Q = Pooled([os.path.join(pdir, k + ".npz") for k in keys], cmono=s.endswith("m"))
        ones = Q.parts(np.full(Q.n_cells, F.NEUTRAL, np.int64))
        solver = {"pt": F.solve_pt, "ptm": F.solve_pt, "cd": F.solve_cd, "cdm": F.solve_cd}[s]
        v, info = solver(Q, o.seed, budget=o.budget)
        pr = Q.parts(v)
        mult = F.GRID[v].reshape(Q.J, F.K).tolist()
        json.dump(dict(name=name, window_min=10, class_dims=Q.P[0].class_dims, mult=mult, packs=keys,
                       fit=dict(solver=s, E=pr["E"], mean_peak_day1=pr["peak"], mean_top5_day1=pr["top5"],
                                viol=pr["viol"], E_ones=ones["E"], mean_peak_ones=ones["peak"], budget_s=o.budget,
                                n_evals=Q.n_eval, info={k: v_ for k, v_ in info.items() if k != "wall"},
                                grid=F.GRID.tolist(), lam=F.LAM, mu=F.MU, pmono=F.PMONO, top5w=F.TOP5W,
                                class_monotone=Q.cmono)),
                  open(out, "w"), indent=1)
        F.append(ledger, dict(name=name, base=o.base, holdout=o.holdout, solver=s, n_packs=len(keys), E=pr["E"],
                              mean_peak=pr["peak"], E_ones=ones["E"], mean_peak_ones=ones["peak"], mult=json.dumps(mult),
                              n_evals=Q.n_eval, wall_s=info["wall"], ts=time.strftime("%Y-%m-%dT%H:%M:%S")))
        print(f"{name}: E={pr['E']:.4f} (ones {ones['E']:.4f}) mean day-1 peak {pr['peak']:.3f} (ones {ones['peak']:.3f}) "
              f"mult={mult} evals={Q.n_eval}", flush=True)


if __name__ == "__main__":
    main()
