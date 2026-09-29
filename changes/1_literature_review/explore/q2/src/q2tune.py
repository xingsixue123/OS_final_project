"""Equal-budget hyperparameter tuning on the DEV instances only (Optuna TPE, same number of trials per solver).

  python q2tune.py --form '{"name":"F2b","tau_rel":0.6}' --solvers lp,milp,... --budget 10 --trials 10 [--seed-from 10]

Each trial = one sampled config run on BOTH dev instances (separate processes, taskset -c 0-7, 8 threads), logged by
q2run into trials.csv (phase=tune). Optuna value = mean over the two dev instances of obj/ref - 1, where ref = the
peak-aware greedy objective of that instance (deterministic, budget-independent). The first trial of every study is
the solver's default config; with --seed-from B the best config of the budget-B study is enqueued first instead.
Failed / over-budget runs score +1.0. Studies persist in q2/optuna.db.
"""
import argparse
import json
import os
import subprocess
import sys
import time

import optuna

SRC = os.path.dirname(os.path.abspath(__file__))
Q2 = os.path.dirname(SRC)
PY = sys.executable
DEV = [os.path.join(Q2, "inst", "dev_Region7.npz"), os.path.join(Q2, "inst", "dev_Region6.npz")]
DB = "sqlite:///" + os.path.join(Q2, "optuna.db")


DEFAULTS = {
    "lp": {"lexi": False, "J": 12},
    "milp": {"start": "lp", "presolve": "on", "mip_heuristic_effort": 0.05, "eps_tie": 0.0, "J": 12},
    "cpsat": {"start": "lp", "linearization_level": 1, "repair_hint": False, "cp_model_presolve": True, "scale": 1000.0},
    "scip": {"start": "lp", "emphasis": "default"},
    "ls": {"start": "lp", "ls_T0": 2e-3, "ls_T1_ratio": 5e-4, "ls_moves": 20000, "p_add": 0.2, "p_swap": 0.6,
           "topw": 8, "ls_restart_every": 0, "ls_chains": 8, "g_scale": 3000.0},
    "eim": {"start": "lp", "eim_R": 16, "eim_Tmin": 1e-6, "eim_Tratio": 3000.0, "eim_moves": 20000, "p_add": 0.2,
            "p_swap": 0.6, "topw": 8, "eim_rho": 50.0, "eim_hscale": 10.0, "eim_anneal": 0.0, "eim_eta": 1.0,
            "g_scale": 3000.0},
    "hlns": {"start": "lp", "hl_nmax": 3000, "hl_slice": 0.25, "hl_q": 8, "hl_p_block": 0.3, "hl_frac_sel": 0.5,
             "hl_p_milp": 0.0, "eim_R": 8, "eim_Tmin": 1e-6, "eim_Tratio": 3000.0, "eim_moves": 20000},
    "sb": {"start": "lp", "sb_agents": 32, "sb_steps": 400, "sb_dt": 1.0, "sb_variant": "ballistic", "sb_heat": 0.06,
           "sb_xi": 0.7, "sb_warm": 0.0, "sb_eta_mu": 1.0, "sb_alpha_floor": 0.0, "sb_tau_frac": 0.97, "sb_eta": 0.5},
    "mq": {"start": "lp", "mq_solver": "mq_dsb", "mq_nmax": 800, "mq_reads": 16, "mq_iters": 300, "mq_dt": 1.0,
           "mq_xi": 0.5, "mq_pen": 0.05, "mq_q": 6, "mq_ksamp": 4},
}
DEFAULTS["pt"] = {k: v for k, v in DEFAULTS["eim"].items() if k != "eim_eta"}


def space(trial, solver, form):
    t = trial
    c = {}
    typ = form["name"]
    if solver != "cpsat":
        c["start"] = t.suggest_categorical("start", ["lp", "pgreedy"])
    if solver == "lp":
        c = {"lexi": t.suggest_categorical("lexi", [False, True])}
        if typ in ("F2b", "F3"):
            c["J"] = t.suggest_categorical("J", [6, 12, 24])
    elif solver == "milp":
        c["presolve"] = t.suggest_categorical("presolve", ["on", "off"])
        c["mip_heuristic_effort"] = t.suggest_float("mip_heuristic_effort", 0.02, 1.0, log=True)
        c["eps_tie"] = t.suggest_categorical("eps_tie", [0.0, 1e-4])
        if typ in ("F2b", "F3"):
            c["J"] = t.suggest_categorical("J", [6, 12, 24])
    elif solver == "cpsat":
        c["start"] = t.suggest_categorical("start", ["lp", "pgreedy"])
        c["linearization_level"] = t.suggest_int("linearization_level", 0, 2)
        c["repair_hint"] = t.suggest_categorical("repair_hint", [False, True])
        c["cp_model_presolve"] = t.suggest_categorical("cp_model_presolve", [True, False])
        if typ in ("F2b", "F3"):
            c["scale"] = t.suggest_categorical("scale", [300.0, 1000.0, 3000.0])
    elif solver == "scip":
        c["emphasis"] = t.suggest_categorical("emphasis", ["default", "aggressive", "fast"])
    elif solver == "ls":
        c["ls_T0"] = t.suggest_float("ls_T0", 1e-5, 1e-1, log=True)
        c["ls_T1"] = c["ls_T0"] * t.suggest_float("ls_T1_ratio", 1e-5, 1e-1, log=True)
        c["ls_moves"] = t.suggest_int("ls_moves", 5000, 200000, log=True)
        c["p_add"] = t.suggest_float("p_add", 0.0, 0.5)
        c["p_swap"] = t.suggest_float("p_swap", 0.2, 0.95 - c["p_add"])
        c["topw"] = t.suggest_int("topw", 2, 64, log=True)
        c["ls_restart_every"] = t.suggest_categorical("ls_restart_every", [0, 2, 5, 20])
        c["ls_chains"] = t.suggest_categorical("ls_chains", [8, 16])
        if typ == "F1":
            c["g_scale"] = t.suggest_float("g_scale", 100, 1e4, log=True)
    elif solver in ("eim", "pt"):
        c["eim_R"] = t.suggest_categorical("eim_R", [8, 16, 32, 64])
        c["eim_Tmin"] = t.suggest_float("eim_Tmin", 1e-7, 1e-3, log=True)
        c["eim_Tmax"] = c["eim_Tmin"] * t.suggest_float("eim_Tratio", 2.0, 1e4, log=True)
        c["eim_moves"] = t.suggest_int("eim_moves", 5000, 200000, log=True)
        c["p_add"] = t.suggest_float("p_add", 0.0, 0.5)
        c["p_swap"] = t.suggest_float("p_swap", 0.2, 0.95 - c["p_add"])
        c["topw"] = t.suggest_int("topw", 2, 64, log=True)
        c["eim_rho"] = t.suggest_float("eim_rho", 0.1, 1e3, log=True)
        c["eim_hscale"] = t.suggest_float("eim_hscale", 0.1, 100.0, log=True)
        c["eim_anneal"] = t.suggest_float("eim_anneal", 0.0, 0.99)
        if solver == "eim":
            c["eim_eta"] = t.suggest_float("eim_eta", 0.01, 10.0, log=True)
        if typ == "F1":
            c["g_scale"] = t.suggest_float("g_scale", 100, 1e4, log=True)
    elif solver == "hlns":
        c["hl_nmax"] = t.suggest_int("hl_nmax", 300, 8000, log=True)
        c["hl_slice"] = t.suggest_float("hl_slice", 0.05, 2.0, log=True)
        c["hl_q"] = t.suggest_int("hl_q", 2, 32, log=True)
        c["hl_p_block"] = t.suggest_float("hl_p_block", 0.0, 0.8)
        c["hl_frac_sel"] = t.suggest_float("hl_frac_sel", 0.05, 2.0, log=True)
        c["hl_p_milp"] = t.suggest_float("hl_p_milp", 0.0, 0.3)
        c["eim_R"] = t.suggest_categorical("eim_R", [4, 8, 16])
        c["eim_Tmin"] = t.suggest_float("eim_Tmin", 1e-7, 1e-3, log=True)
        c["eim_Tmax"] = c["eim_Tmin"] * t.suggest_float("eim_Tratio", 2.0, 1e4, log=True)
        c["eim_moves"] = t.suggest_int("eim_moves", 2000, 100000, log=True)
    elif solver == "sb":
        c["sb_agents"] = t.suggest_categorical("sb_agents", [8, 16, 32, 64])
        c["sb_steps"] = t.suggest_int("sb_steps", 50, 2000, log=True)
        c["sb_dt"] = t.suggest_float("sb_dt", 0.2, 1.5)
        c["sb_variant"] = t.suggest_categorical("sb_variant", ["ballistic", "discrete", "heated"])
        c["sb_heat"] = t.suggest_float("sb_heat", 0.01, 0.3, log=True)
        c["sb_xi"] = t.suggest_float("sb_xi", 0.05, 3.0, log=True)
        c["sb_warm"] = t.suggest_float("sb_warm", 0.0, 0.95)
        c["sb_eta_mu"] = t.suggest_float("sb_eta_mu", 0.01, 10.0, log=True)
        c["sb_alpha_floor"] = t.suggest_float("sb_alpha_floor", 0.0, 0.2)
        if typ != "F2b":
            c["sb_tau_frac"] = t.suggest_float("sb_tau_frac", 0.9, 1.0)
            c["sb_eta"] = t.suggest_float("sb_eta", 0.05, 5.0, log=True)
    elif solver == "mq":
        c["mq_solver"] = t.suggest_categorical("mq_solver", ["mq_bsb", "mq_dsb", "mq_cac", "dwave_sa", "openjij_sa"])
        c["mq_nmax"] = t.suggest_int("mq_nmax", 100, 1500, log=True)
        c["mq_reads"] = t.suggest_categorical("mq_reads", [4, 8, 16, 32])
        c["mq_iters"] = t.suggest_int("mq_iters", 50, 2000, log=True)
        c["mq_dt"] = t.suggest_float("mq_dt", 0.05, 1.5, log=True)
        c["mq_xi"] = t.suggest_float("mq_xi", 0.05, 3.0, log=True)
        c["mq_pen"] = t.suggest_float("mq_pen", 1e-3, 1.0, log=True)
        c["mq_q"] = t.suggest_int("mq_q", 2, 32, log=True)
        c["mq_ksamp"] = t.suggest_int("mq_ksamp", 1, 8)
    return c


def run_trial(inst, form, solver, budget, cfg, seed, tag):
    cmd = ["taskset", "-c", "0-7", PY, os.path.join(SRC, "q2run.py"), "--inst", inst, "--form", json.dumps(form),
           "--solver", solver, "--budget", str(budget), "--seed", str(seed), "--cfg", json.dumps(cfg),
           "--phase", "tune", "--tag", tag]
    env = dict(os.environ, OMP_NUM_THREADS="8", NUMBA_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8",
               MKL_NUM_THREADS="8")
    p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=budget * 4 + 300)
    for line in p.stdout.splitlines():
        if line.startswith("RESULT "):
            return json.loads(line[7:])
    sys.stderr.write(p.stdout[-2000:] + p.stderr[-3000:])
    return None


_REF = {}


def ref_obj(inst, form):
    key = (inst, json.dumps(form, sort_keys=True))
    if key not in _REF:
        r = run_trial(inst, form, "pgreedy", 10, {}, 0, "ref")
        _REF[key] = float(r["objective"])
    return _REF[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--solvers", required=True)
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--trials", type=int, required=True)
    ap.add_argument("--seed-from", type=float, default=None)
    ap.add_argument("--topk", type=int, default=1, help="with --seed-from: enqueue the top-k distinct configs")
    ap.add_argument("--with-default", action="store_true",
                    help="with --seed-from: top-(k-1) distinct configs + the solver's default config (trial 0)")
    o = ap.parse_args()
    form = json.loads(o.form)
    fname = form["name"] + "".join(f"_{k}{v}" for k, v in sorted(form.items()) if k != "name")
    for solver in o.solvers.split(","):
        sname = f"{fname}__{solver}__b{int(o.budget)}"
        st = optuna.create_study(study_name=sname, storage=DB, load_if_exists=True, direction="minimize",
                                 sampler=optuna.samplers.TPESampler(seed=0, n_startup_trials=4))
        done = len([t for t in st.trials if t.state == optuna.trial.TrialState.COMPLETE])
        if done == 0:
            if o.seed_from is not None:
                prev = optuna.load_study(study_name=f"{fname}__{solver}__b{int(o.seed_from)}", storage=DB)
                done_tr = sorted([t for t in prev.trials if t.state == optuna.trial.TrialState.COMPLETE],
                                 key=lambda t: t.value)
                seen = []
                dflt = [t for t in prev.trials if t.number == 0]
                dcfg = dflt[0].user_attrs.get("cfg") if dflt else None
                kk = o.topk - (1 if o.with_default else 0)
                for t in done_tr:
                    c = t.user_attrs.get("cfg")
                    if c in seen:
                        continue
                    if len(seen) >= kk and not (o.with_default and c == dcfg):
                        continue
                    seen.append(c)
                    st.enqueue_trial(t.params)
                    if len(seen) >= o.topk:
                        break
                if o.with_default and dcfg not in seen and dflt:
                    st.enqueue_trial(dflt[0].params)
                    seen.append(dcfg)
            else:
                st.enqueue_trial(DEFAULTS[solver])          # trial 0 = the solver's default config

        def objective(trial):
            cfg = space(trial, solver, form)
            vals = []
            for inst in DEV:
                r = run_trial(inst, form, solver, o.budget, cfg, trial.number, f"{sname}_t{trial.number}")
                if r is None or r.get("status") != "ok" or r.get("objective") is None or \
                        float(r.get("wall", 0)) > 1.05 * o.budget + 0.5:
                    vals.append(1.0)
                else:
                    vals.append(float(r["objective"]) / ref_obj(inst, form) - 1.0)
            trial.set_user_attr("cfg", json.dumps(cfg, sort_keys=True))
            trial.set_user_attr("per_inst", vals)
            v = float(sum(vals) / len(vals))
            print(f"[{sname}] trial {trial.number}: {v:+.5f} {vals} {json.dumps(cfg, sort_keys=True)[:200]}", flush=True)
            return v

        need = o.trials - done
        if need > 0:
            st.optimize(objective, n_trials=need)
        b = st.best_trial
        print(f"[{sname}] BEST {b.value:+.5f} cfg={b.user_attrs.get('cfg')}", flush=True)


if __name__ == "__main__":
    main()
