"""WP5 step 1: equal-trial tight-budget tuning on the DEV instances only (Region7/Region6 samples 0, 0.1, 0.2, 0.3).

  python p2tune.py --budget 1 --solvers pt,eim,sb,mq,lp,milp,cpsat,ls --trials 12

Same procedure as phase-1 q2tune.py (Optuna TPE seed 0, 4 random start-up trials, one study per (solver, budget),
value = mean over the dev instances of obj/ref - 1 with ref = the peak-aware greedy objective of that instance,
failed / over-budget (> 1.05 T + 0.5 s) runs score +1), with these phase-2 choices (fixed before any trial):
  * dev = 8 instances; every trial runs its config on all 8 (one process, sequential, cores 0-7, 8 threads);
  * trial 0 of every study = the solver's phase-1 best 10-s configuration (phase-1 optuna.db, read-only), so both
    families start from their phase-1 tuned point;
  * the same number of trials for every solver at a budget (12);
  * search spaces = phase-1 q2tune.space, except MindQuantum: mq_solver in {mq_bsb, mq_dsb, mq_cac} (the MindQuantum
    QAIA Ising-machine emulators; SA-on-QUBO is already covered by PT);
  * both families choose their warm start from the same options {lp, pgreedy} (phase-1 spaces already do this).
Studies persist in wp5_ising/optuna.db; every run is a row of wp5_ising/trials.csv (phase tune).
"""
import argparse
import json
import os
import subprocess
import sys

import optuna

SRC = os.path.dirname(os.path.abspath(__file__))
AREA = os.path.dirname(SRC)
sys.path.insert(0, SRC)
import q2tune as T1  # noqa: E402  (phase-1 search spaces, copied unchanged)

PY = sys.executable
DEV = [os.path.join(AREA, "inst", f"full_{r}_s{s}.npz") for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]
DB = "sqlite:///" + os.path.join(AREA, "optuna.db")
TRIALS = os.path.join(AREA, "trials.csv")
PH1 = json.load(open(os.path.join(AREA, "phase1_best_F1_b10.json")))
FORM = {"name": "F1"}
ISING = ["pt", "eim", "sb", "mq"]
CLASSICAL = ["lp", "milp", "cpsat", "ls"]


def space(trial, solver):
    if solver == "mq":
        c = {"start": trial.suggest_categorical("start", ["lp", "pgreedy"])}
        c["mq_solver"] = trial.suggest_categorical("mq_solver", ["mq_bsb", "mq_dsb", "mq_cac"])
        c["mq_nmax"] = trial.suggest_int("mq_nmax", 100, 1500, log=True)
        c["mq_reads"] = trial.suggest_categorical("mq_reads", [4, 8, 16, 32])
        c["mq_iters"] = trial.suggest_int("mq_iters", 50, 2000, log=True)
        c["mq_dt"] = trial.suggest_float("mq_dt", 0.05, 1.5, log=True)
        c["mq_xi"] = trial.suggest_float("mq_xi", 0.05, 3.0, log=True)
        c["mq_pen"] = trial.suggest_float("mq_pen", 1e-3, 1.0, log=True)
        c["mq_q"] = trial.suggest_int("mq_q", 2, 32, log=True)
        c["mq_ksamp"] = trial.suggest_int("mq_ksamp", 1, 8)
        return c
    return T1.space(trial, solver, FORM)


def run_cfg(insts, solver, budget, cfg, seed, phase, tag, trials=TRIALS, sols=None):
    """one process, all instances; returns {instance: RESULT dict}."""
    cmd = ["taskset", "-c", "0-7", PY, os.path.join(SRC, "p2run.py"), "--insts", *insts, "--form", json.dumps(FORM),
           "--solver", solver, "--budget", str(budget), "--seed", str(seed), "--cfg", json.dumps(cfg),
           "--phase", phase, "--tag", tag, "--trials", trials]
    cmd += ["--sols", sols] if sols else ["--nosave"]
    env = dict(os.environ, OMP_NUM_THREADS="8", NUMBA_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", MKL_NUM_THREADS="8")
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    out = {}
    for line in p.stdout.splitlines():
        if line.startswith("RESULT "):
            r = json.loads(line[7:])
            out[r["instance"]] = r
    if len(out) < len(insts):
        sys.stderr.write(p.stdout[-2000:] + p.stderr[-3000:])
    return out


_REF = {}


def ref_objs():
    """peak-aware greedy objective per dev instance (deterministic, budget-independent)."""
    p = os.path.join(AREA, "results", "ref_pgreedy.json")
    if os.path.exists(p):
        return json.load(open(p))
    out = run_cfg(DEV, "pgreedy", 1, {}, 0, "ref", "ref_pgreedy")
    ref = {k: float(v["objective"]) for k, v in out.items()}
    assert len(ref) == len(DEV)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(ref, open(p, "w"), indent=1)
    return ref


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--solvers", required=True)
    ap.add_argument("--trials", type=int, default=12)
    o = ap.parse_args()
    ref = ref_objs()
    names = [os.path.basename(p).replace(".npz", "") for p in DEV]
    for solver in o.solvers.split(","):
        sname = f"F1__{solver}__b{o.budget:g}"
        st = optuna.create_study(study_name=sname, storage=DB, load_if_exists=True, direction="minimize",
                                 sampler=optuna.samplers.TPESampler(seed=0, n_startup_trials=4))
        if len(st.trials) == 0:
            st.enqueue_trial(PH1[solver]["params"])          # trial 0 = phase-1 best 10-s config

        def objective(trial):
            cfg = space(trial, solver)
            res = run_cfg(DEV, solver, o.budget, cfg, trial.number, "tune", f"{sname}_t{trial.number}")
            vals = []
            for nm in names:
                r = res.get(nm)
                if r is None or r.get("status") != "ok" or r.get("objective") is None or \
                        float(r.get("wall", 0)) > 1.05 * o.budget + 0.5:
                    vals.append(1.0)
                else:
                    vals.append(float(r["objective"]) / ref[nm] - 1.0)
            trial.set_user_attr("cfg", json.dumps(cfg, sort_keys=True))
            trial.set_user_attr("per_inst", vals)
            trial.set_user_attr("walls", [res.get(nm, {}).get("wall") for nm in names])
            v = float(sum(vals) / len(vals))
            print(f"[{sname}] trial {trial.number}: {v:+.5f} {[round(x, 4) for x in vals]} "
                  f"{json.dumps(cfg, sort_keys=True)[:160]}", flush=True)
            return v

        done = len([t for t in st.trials if t.state == optuna.trial.TrialState.COMPLETE])
        if o.trials - done > 0:
            st.optimize(objective, n_trials=o.trials - done)
        b = st.best_trial
        print(f"[{sname}] BEST t{b.number} {b.value:+.5f} cfg={b.user_attrs.get('cfg')}", flush=True)


if __name__ == "__main__":
    main()
