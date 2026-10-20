"""Run ONE trial: nested solve of (instance, formulation, solver, config, budget, seed) and log it to trials.csv.

  taskset -c 0-7 python q2run.py --inst inst/dev_Region7.npz --form '{"name":"F2a","k":4}' --solver eim \
      --budget 10 --seed 0 --cfg '{...}' --phase dev [--tag ...]

Timing: the clock starts after imports, instance load, formulation setup and a numba warm-up (identical for all
solvers) and covers the whole nested solve incl. every repair. The final objective is the TRUE formulation objective
of the prefix sets of the emitted order (after the shared repair), mean over the levels.
Solvers: classical {greedy, pgreedy, lp, milp, ls, cpsat*, scip*}; Ising {eim, pt (QUBO penalty), hlns, sb, mq}.
(* in their own modules; cpsat never imports highspy.)
"""
import argparse
import fcntl
import hashlib
import json
import os
import sys
import time

import numpy as np

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
import q2core as C  # noqa: E402

Q2 = os.path.dirname(SRC)
TRIALS = os.path.join(Q2, "trials.csv")
COLS = ["ts", "phase", "instance", "form", "form_params", "solver", "family", "cfg_hash", "cfg", "budget", "seed",
        "wall", "over_budget", "objective", "obj_levels", "peak_W_util", "sts_W", "n_sel", "feasible", "moves",
        "status", "sol", "tag", "sim_p100", "sim_wr", "sim_matched", "sim_threshold"]
FAMILY = {"greedy": "classical", "pgreedy": "classical", "lp": "classical", "milp": "classical", "ls": "classical",
          "cpsat": "classical", "scip": "classical", "eim": "ising", "pt": "ising", "hlns": "ising", "sb": "ising",
          "mq": "ising"}


def cfg_hash(d):
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()[:10]


def append_trial(row, path=TRIALS):
    new = not os.path.exists(path)
    with open(path + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        import csv
        new = not os.path.exists(path) or os.path.getsize(path) == 0
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            if new:
                w.writeheader()
            w.writerow({k: row.get(k, "") for k in COLS})
        fcntl.flock(lk, fcntl.LOCK_UN)


# ------------------------------------------------------------------ level solvers
def start_solution(P, how, deadline, cfg, seed):
    """classical starting points shared by LS / EIM / MILP (a config choice for every family)."""
    if how == "zero":
        return np.zeros(P.n), {}
    if how == "pgreedy":
        x, st = C.pgreedy(P)
        return x, {"start_" + k: v for k, v in st.items()}
    if how == "lp":
        import q2lp
        x, info = q2lp.solve_lp(P, deadline, lexi=bool(cfg.get("lexi", False)), J=int(cfg.get("J", 12)), seed=seed)
        if x is None:
            xs, st = C.pgreedy(P)
            return xs, dict(info, start_fallback=1)
        xr = (x >= 1 - 1e-6).astype(float)
        xr, st = P.repair(xr, fill=True)
        info.update({"start_" + k: v for k, v in st.items()})
        return xr, info
    raise ValueError(how)


def make_level_solver(solver, cfg, seed):
    if solver == "greedy":
        def f(P, k, dl):
            xs = np.zeros(P.n)
            cs = np.cumsum(P.s[P.rank_order])
            kk = int(np.searchsorted(cs, P.B + 1e-9, side="right"))
            xs[P.rank_order[:kk]] = 1.0
            return xs, {}
        return f
    if solver == "pgreedy":
        return lambda P, k, dl: (np.zeros(P.n), {})       # the shared repair from x = 0 is the peak-aware greedy
    if solver == "lp":
        def f(P, k, dl):
            return start_solution(P, "lp", dl, cfg, seed)
        return f
    if solver == "milp":
        import q2lp

        def f(P, k, dl):
            x0, info = start_solution(P, cfg.get("start", "lp"), dl, cfg, seed)
            opts = {}
            if "mip_heuristic_effort" in cfg:
                opts["mip_heuristic_effort"] = float(cfg["mip_heuristic_effort"])
            if "presolve" in cfg:
                opts["presolve"] = str(cfg["presolve"])
            if "mip_rel_gap" in cfg:
                opts["mip_rel_gap"] = float(cfg["mip_rel_gap"])
            xm, mi = q2lp.solve_milp(P, dl, x0=x0, J=int(cfg.get("J", 12)), seed=seed, opts=opts,
                                     eps_tie=float(cfg.get("eps_tie", 0.0)))
            info.update(mi)
            if xm is not None:
                xm2, _ = P.repair(xm, fill=False)
                if P.obj(xm2) < P.obj(x0) - 1e-15:
                    info["milp_improved"] = 1
                    return xm2, info
            info["milp_improved"] = 0
            return x0, info
        return f
    if solver in ("ls", "eim", "pt"):
        import q2anneal as A

        def f(P, k, dl):
            x0, info = start_solution(P, cfg.get("start", "lp"), dl, cfg, seed)
            if time.time() >= dl - 0.02:
                return x0, info
            if solver == "ls":
                xb, li = A.local_search(P, x0, dl, cfg, seed=seed * 100 + k)
            else:
                c2 = dict(cfg)
                if solver == "pt":
                    c2["eim_pmode"] = "quad"
                xb, li = A.eim(P, x0, dl, c2, seed=seed * 100 + k)
            info.update(li)
            return xb, info
        return f
    if solver == "hlns":
        import q2hybrid as HY
        return lambda P, k, dl: HY.hlns(P, k, dl, cfg, seed, start_solution)
    if solver == "sb":
        import q2sb as SB
        return lambda P, k, dl: SB.sb_level(P, k, dl, cfg, seed, start_solution)
    if solver == "mq":
        import q2mq as MQ
        return lambda P, k, dl: MQ.mq_level(P, k, dl, cfg, seed, start_solution)
    if solver == "scip":
        import q2scip as SC
        return lambda P, k, dl: SC.scip_level(P, k, dl, cfg, seed, start_solution)
    if solver == "cpsat":
        import q2cpsat as CP
        return lambda P, k, dl: CP.cpsat_level(P, k, dl, cfg, seed)
    raise ValueError(solver)


def warmup(I, form, solver, cfg):
    """compile / load numba kernels on a tiny sub-problem (not timed; identical for all solvers)."""
    forced = np.zeros(I.n, bool)
    P = C.Sub(I, 0.02 * I.B, forced, form)
    P.repair(np.zeros(P.n), fill=True)
    if solver in ("ls", "eim", "pt", "hlns"):
        import q2anneal as A
        x0 = np.zeros(P.n)
        A.local_search(P, x0, time.time() + 0.01, dict(ls_moves=200, ls_chains=2))
        A.eim(P, x0, time.time() + 0.01, dict(eim_moves=200, eim_R=2))
        A.eim(P, x0, time.time() + 0.01, dict(eim_moves=200, eim_R=2, eim_pmode="quad"))


def run(inst, form_spec, solver, budget, seed, cfg, phase="dev", tag="", levels=None, write=True, save=True):
    import numba
    numba.set_num_threads(int(cfg.get("threads", 8)))
    levels = levels or C.LEVELS
    I = C.Instance(inst)
    form = C.make_form(I, form_spec)
    warmup(I, form, solver, cfg)
    lsolver = make_level_solver(solver, cfg, seed)
    weights = cfg.get("level_weights", [2.0] + [1.0] * (len(levels) - 1))
    t0 = time.time()
    status = "ok"
    try:
        x, lvl_of, per = C.nested_solve(I, form, lsolver, float(budget), levels=levels, t_start=t0, weights=weights)
    except Exception as ex:  # report failures too
        import traceback
        traceback.print_exc()
        status = f"error: {ex!r}"[:200]
        x, lvl_of, per = None, None, []
    wall = time.time() - t0
    row = dict(ts=time.strftime("%Y-%m-%dT%H:%M:%S"), phase=phase, instance=I.name, form=form.name,
               form_params=json.dumps(form.to_json(), sort_keys=True), solver=solver, family=FAMILY[solver],
               cfg_hash=cfg_hash(cfg), cfg=json.dumps(cfg, sort_keys=True), budget=budget, seed=seed, wall=round(wall, 3),
               over_budget=int(wall > 1.05 * budget + 0.5), status=status, tag=tag)
    if x is not None:
        order, nfill = C.final_order(I, x, lvl_of)
        obj, vals = C.nested_objective(I, form, order, levels)
        pk, sts = C.peak_util(I, order, 1.0)
        mv = {}
        for p in per:
            for kk, v in p.items():
                if kk.startswith(("rep_", "start_n_", "ls_acc", "eim_acc", "hl_", "sb_", "mq_", "milp_improved",
                                  "cp_", "scip_")) and np.isscalar(v) and not isinstance(v, str):
                    mv[kk] = mv.get(kk, 0) + v
        row.update(objective=obj, obj_levels=json.dumps([round(v, 6) for v in vals]), peak_W_util=pk, sts_W=sts,
                   n_sel=int((x > 0.5).sum()), feasible=1, moves=json.dumps(mv, sort_keys=True))
        if save:
            os.makedirs(os.path.join(Q2, "sols"), exist_ok=True)
            sp = os.path.join(Q2, "sols", f"{phase}_{I.name}_{form.name}_{solver}_{row['cfg_hash']}_b{budget}_s{seed}"
                              f"{('_' + tag) if tag else ''}.npz")
            ids_key = I.z["keys"][order]
            ids_ts = I.z["ts0"][order]
            np.savez_compressed(sp, order=order, lvl_of=lvl_of, keys=ids_key, ts0=ids_ts, levels=np.asarray(levels))
            with open(sp.replace(".npz", ".json"), "w") as fh:
                json.dump(dict(row, per_level=per), fh, default=float, indent=1)
            row["sol"] = os.path.relpath(sp, Q2)
    else:
        row.update(feasible=0)
    if write:
        append_trial(row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", required=True)
    ap.add_argument("--form", required=True)
    ap.add_argument("--solver", required=True)
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cfg", default="{}")
    ap.add_argument("--phase", default="dev")
    ap.add_argument("--tag", default="")
    ap.add_argument("--nowrite", action="store_true")
    o = ap.parse_args()
    row = run(o.inst, json.loads(o.form), o.solver, o.budget, o.seed, json.loads(o.cfg), o.phase, o.tag,
              write=not o.nowrite)
    print("RESULT", json.dumps({k: row.get(k) for k in ["instance", "form", "solver", "budget", "seed", "wall",
                                                          "objective", "peak_W_util", "status", "moves"]}), flush=True)


if __name__ == "__main__":
    main()
