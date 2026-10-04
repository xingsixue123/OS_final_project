"""Day-1 label sets for WP2 (solver env explore/env, read-only). One file per (instance, design, seed):
labels/<inst>_<design>_s<seed>.npz (+ .json stats). Phase-1 Ising configurations, reused by COPYING the phase-1 code:
  P0, T2, C2   explore/q3 label designs, solved by q3solve.solve_pt (parallel tempering on the extended-Ising energy,
               common/Q3_FORMULATION.md; secs=15, NUMBA 2 threads as in phase 1), labels = selection + Baleen fill
  F1PT, F1EIM  explore/q2 F1 finalists (true min-max day-1 peak), solver 'pt' / 'eim' with the frozen 10 s configs
               of q2/plan_F1.json, nested driver with the single level f = 1.0 (deployed labels depend only on the set
               at W), 10 s budget, 8 numba threads; shared q2 repair + Baleen-order fill
  F1CPSAT      the same F1 formulation solved by OR-Tools CP-SAT (q2 classical finalist cfg, 10 s) -> arm Dc
The core selection (before the harness strict-prefix fill) is stored by episode identity (block key, first ts); the
train-time policy (pb4_policy) re-applies the fill in each run's own Baleen order.

  cd wp2_deployed/work && taskset ... bwrap ... $SOLVER_PY -B ../src/labels.py --inst Region7_s0 --design P0 --seed 1
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "q3lib"))
sys.path.insert(0, os.path.join(HERE, "q2lib"))
W = os.path.dirname(HERE)
EXPLORE = os.path.normpath(os.path.join(W, "..", "..", "1_literature_review", "explore"))
INST = os.path.join(EXPLORE, "common", "inst")
LABELS = os.path.join(W, "labels")
PLAN_F1 = os.path.join(EXPLORE, "q2", "plan_F1.json")

Q3_DESIGNS = {"P0": {"mu": 0, "beta": 0, "secs": 15},
              "T2": {"mu": 2, "beta": 0.5, "secs": 15},
              "C2": {"mu": 2, "beta": 0.5, "cells": "meta+sz+h+nacc", "secs": 15}}
Q2_DESIGNS = {"F1PT": "pt", "F1EIM": "eim", "F1CPSAT": "cpsat"}
BUDGET_Q2 = 10.0


def q2_cfg(solver):
    plan = json.load(open(PLAN_F1))
    for m in plan["methods"]:
        if m["solver"] == solver:
            return dict(m["cfg_by_budget"]["10"])
    raise KeyError(solver)


def solve_q3(path, design, seed):
    import numba
    numba.set_num_threads(2)
    import q3lib as QL
    import q3solve as QS
    I = QL.Inst(path)
    I.active = np.ones(I.m, bool)                      # q3solve default all_windows=True
    a = dict(Q3_DESIGNS[design], seed=seed)
    x, st = QS.solve_pt(I, a, log=lambda *_: None)
    order_sel, xf, nfill = QS.final_order(I, x)
    return I, x, xf, dict(solver=st, args=a, n_fill=int(nfill))


def solve_q2(path, design, seed):
    import numba
    import q2core as C
    import q2run as R
    solver = Q2_DESIGNS[design]
    cfg = q2_cfg(solver)
    numba.set_num_threads(int(cfg.get("threads", 8)))
    I = C.Instance(path)
    form = C.make_form(I, {"name": "F1"})
    R.warmup(I, form, solver, cfg)
    ls = R.make_level_solver(solver, cfg, seed)
    t0 = time.time()
    x, lvl_of, per = C.nested_solve(I, form, ls, BUDGET_Q2, levels=[1.0], t_start=t0, weights=[1.0])
    wall = time.time() - t0
    order, nfill = C.final_order(I, x, lvl_of)
    xf = np.zeros(I.n)
    xf[order] = 1.0
    return I, x, xf, dict(solver=solver, cfg=cfg, budget=BUDGET_Q2, wall=wall, per_level=per, n_fill=int(nfill))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", required=True)
    ap.add_argument("--design", required=True)
    ap.add_argument("--seed", type=int, required=True)
    o = ap.parse_args()
    path = os.path.join(INST, f"day1_{o.inst}.npz")
    out = os.path.join(LABELS, f"{o.inst}_{o.design}_s{o.seed}.npz")
    t = time.time()
    if o.design in Q3_DESIGNS:
        I, x, xf, info = solve_q3(path, o.design, o.seed)
    else:
        I, x, xf, info = solve_q2(path, o.design, o.seed)
    z = np.load(path)
    # common statistics on the day-1 instance (util %; all 145 day-1 windows)
    import scipy.sparse as sp
    D = sp.csr_matrix((z["D_data"], z["D_indices"], z["D_indptr"]), shape=tuple(z["D_shape"]))
    C_ = z["C"].astype(float)
    s = z["s"].astype(float)
    B = float(z["B"])
    order = z["base_order"]
    xb = np.zeros(len(s))
    xb[order[np.cumsum(s[order]) <= B]] = 1.0
    US = 1.0 / 36 * (100.0 / 0.1) / 600 * 100
    L = C_ - D.T @ xf
    Lb = C_ - D.T @ xb
    dmax = np.asarray(D.max(1).todense()).ravel()
    sel = x > 0.5
    assert float(s @ xf) <= B + 1e-6
    st = dict(inst=o.inst, design=o.design, seed=o.seed, n=int(len(s)), B=B, n_core=int(sel.sum()),
              n_label=int(xf.sum()), n_baleen=int(xb.sum()), jaccard_vs_baleen=float((xf * xb).sum() / max(((xf + xb) > 0).sum(), 1)),
              use_frac=float(s @ xf / B), dt_ratio=float((D.sum(1).A1 @ xf) / max(D.sum(1).A1 @ xb, 1e-12)),
              label_peak_util=float(L.max() * US), baleen_peak_util=float(Lb.max() * US),
              label_top5=float(np.sort(L)[::-1][:5].mean() * US), baleen_top5=float(np.sort(Lb)[::-1][:5].mean() * US),
              zero_value_labels=int(((xf > 0.5) & (dmax <= 1e-12)).sum()),
              zero_value_labels_baleen=int(((xb > 0.5) & (dmax <= 1e-12)).sum()),
              secs=time.time() - t, info=info)
    os.makedirs(LABELS, exist_ok=True)
    np.savez_compressed(out + ".part.npz", core_keys=z["keys"][sel], core_ts0=z["ts0"][sel], B=int(B),
                        x_core=x.astype(np.int8), x_full=xf.astype(np.int8))
    os.replace(out + ".part.npz", out)
    json.dump(st, open(out.replace(".npz", ".json"), "w"), indent=1, default=float)
    print(f"[labels] {o.inst} {o.design} s{o.seed}: core {st['n_core']} label {st['n_label']} (Baleen {st['n_baleen']}) "
          f"J={st['jaccard_vs_baleen']:.3f} day-1 peak {st['label_peak_util']:.2f} (Baleen {st['baleen_peak_util']:.2f}) "
          f"zero-value {st['zero_value_labels']} {st['secs']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
