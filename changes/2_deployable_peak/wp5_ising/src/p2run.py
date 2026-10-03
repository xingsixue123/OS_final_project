"""Phase-2 Track B: run ONE solver configuration on one or more instances (nested F1 solve, phase-1 semantics), log
every run to a trials CSV.  Solver code = phase-1 q2 modules copied unchanged into this directory.

  taskset -c 0-7 python p2run.py --insts a.npz b.npz ... --solver pt --budget 3 --seed 0 --cfg '{...}' \
      --phase tune --tag F1__pt__b3_t4 --trials ../trials.csv --sols ../sols

Differences to phase-1 q2run.py (semantics of a single run are identical):
  * several instances per process (each one: load, formulation, numba warm-up -- untimed -- then the timed nested solve);
  * every process holds an exclusive flock on P2/wp5_ising/.cores07.lock for its whole life (no two timing runs ever
    overlap: WP1 solves, WP5 tuning/evaluation/rolling/scaling all take this lock) and refuses to run unless its CPU
    affinity is exactly cores 0-7;
  * unique row key (phase|instance|solver|cfg_hash|budget|seed|tag) + the run's cpu affinity in the CSV.
Timing (unchanged): the clock starts after instance load + formulation + warm-up and covers the whole nested solve incl.
every repair. Objective = mean over the 8 nested levels of max_w L_w of the PREFIX sets of the emitted order.
"""
import argparse
import csv
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
from q2run import FAMILY, cfg_hash, make_level_solver, warmup  # noqa: E402

AREA = os.path.dirname(SRC)
CORES_LOCK = os.path.join(AREA, ".cores07.lock")
COLS = ["key", "ts", "phase", "instance", "form", "form_params", "solver", "family", "cfg_hash", "cfg", "budget", "seed",
        "wall", "over_budget", "objective", "obj_levels", "peak_W_util", "sts_W", "n_sel", "feasible", "moves",
        "status", "sol", "tag", "affinity", "level_secs"]


def row_key(phase, inst, solver, h, budget, seed, tag):
    return hashlib.sha1(f"{phase}|{inst}|{solver}|{h}|{float(budget):g}|{int(seed)}|{tag}".encode()).hexdigest()[:16]


def append_rows(rows, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        new = not os.path.exists(path) or os.path.getsize(path) == 0
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=COLS)
            if new:
                w.writeheader()
            for row in rows:
                w.writerow({k: row.get(k, "") for k in COLS})
        fcntl.flock(lk, fcntl.LOCK_UN)


def done_keys(path):
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        return {r["key"] for r in csv.DictReader(f) if r.get("status") == "ok"}


class CoresLock:
    """Exclusive flock on wp5_ising/.cores07.lock + a simple priority queue: a process of priority P (env P2_PRIO,
    1 = WP5 critical path, 2 = WP1 solves, 3 = other) only tries the lock while no LIVE process of a strictly higher
    priority (lower number) is registered as waiting in wp5_ising/.cores07.wait/. Scheduling only: the timed work
    of a run is identical whatever its priority."""
    def __enter__(self):
        aff = sorted(os.sched_getaffinity(0))
        assert aff == list(range(8)), f"timing run must be pinned to cores 0-7 (taskset -c 0-7), got {aff}"
        prio = int(os.environ.get("P2_PRIO", "1"))
        wd = CORES_LOCK.replace(".lock", ".wait")
        os.makedirs(wd, exist_ok=True)
        me = os.path.join(wd, f"{prio}_{os.getpid()}")
        open(me, "w").close()
        self.f = open(CORES_LOCK, "a")
        t = time.time()
        try:
            while True:
                higher = False
                for fn in os.listdir(wd):
                    try:
                        p, pid = fn.split("_")
                        if int(p) < prio:
                            os.kill(int(pid), 0)
                            higher = True
                            break
                    except (ValueError, ProcessLookupError):
                        try:
                            os.remove(os.path.join(wd, fn))
                        except OSError:
                            pass
                    except PermissionError:
                        higher = True
                if not higher:
                    try:
                        fcntl.flock(self.f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        break
                    except OSError:
                        pass
                time.sleep(0.2 if prio == 1 else 0.5)
        finally:
            try:
                os.remove(me)
            except OSError:
                pass
        self.waited = time.time() - t
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


def run_one(inst, form_spec, solver, budget, seed, cfg, phase, tag, sols_dir, levels=None):
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
    h = cfg_hash(cfg)
    row = dict(key=row_key(phase, I.name, solver, h, budget, seed, tag), ts=time.strftime("%Y-%m-%dT%H:%M:%S"),
               phase=phase, instance=I.name, form=form.name, form_params=json.dumps(form.to_json(), sort_keys=True),
               solver=solver, family=FAMILY[solver], cfg_hash=h, cfg=json.dumps(cfg, sort_keys=True), budget=budget,
               seed=seed, wall=round(wall, 3), over_budget=int(wall > 1.05 * budget + 0.5), status=status, tag=tag,
               affinity="0-7", level_secs=json.dumps([round(p.get("secs", 0.0), 3) for p in per]))
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
        if sols_dir:
            os.makedirs(sols_dir, exist_ok=True)
            sp = os.path.join(sols_dir, f"{phase}_{I.name}_{form.name}_{solver}_{h}_b{budget:g}_s{seed}"
                              f"{('_' + tag) if tag else ''}.npz")
            np.savez_compressed(sp, order=order, lvl_of=lvl_of, keys=I.z["keys"][order], ts0=I.z["ts0"][order],
                                levels=np.asarray(levels))
            with open(sp.replace(".npz", ".json"), "w") as fh:
                json.dump(dict(row, per_level=per), fh, default=float, indent=1)
            row["sol"] = os.path.relpath(sp, AREA) if sp.startswith(AREA) else sp
    else:
        row.update(feasible=0)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insts", required=True, nargs="+")
    ap.add_argument("--form", default='{"name": "F1"}')
    ap.add_argument("--solver", required=True)
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--cfg", default="{}")
    ap.add_argument("--phase", default="dev")
    ap.add_argument("--tag", default="")
    ap.add_argument("--trials", default=os.path.join(AREA, "trials.csv"))
    ap.add_argument("--sols", default=os.path.join(AREA, "sols"))
    ap.add_argument("--nosave", action="store_true")
    ap.add_argument("--skip-done", action="store_true")
    o = ap.parse_args()
    cfg = json.loads(o.cfg)
    import numba
    numba.set_num_threads(int(cfg.get("threads", 8)))
    have = done_keys(o.trials) if o.skip_done else set()
    with CoresLock() as L:
        for inst in o.insts:
            name = os.path.basename(inst).replace(".npz", "")
            k = row_key(o.phase, name, o.solver, cfg_hash(cfg), o.budget, o.seed, o.tag)
            if k in have:
                print("SKIP", name, flush=True)
                continue
            row = run_one(inst, json.loads(o.form), o.solver, o.budget, o.seed, cfg, o.phase, o.tag,
                          None if o.nosave else o.sols)
            append_rows([row], o.trials)
            print("RESULT", json.dumps({k: row.get(k) for k in ["instance", "solver", "budget", "seed", "wall",
                                                              "objective", "peak_W_util", "status", "over_budget"]}),
                  flush=True)


if __name__ == "__main__":
    main()
