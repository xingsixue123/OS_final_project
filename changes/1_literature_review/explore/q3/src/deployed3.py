"""Q3 deployed (ML) mode, copied from harness_eval/src/deployed.py and adapted (Track A):
day-1 labels by PolicyPeakBaleen3 (solver = q3solve.py in the solver env) inside the authors' Baleen TrainCommand for
that sample (GBMs trained on our labels) -> authors' ReproduceCommand for that sample (`--ap mlnew`, Region7 ML-Range
on ML-When, Region6 All on Partial Hit, + --eviction-policy LRU, - --offline-ap-decisions) -> --ap-threshold
re-converged to 35.599 +-1% (seeds predicted by the analytic emulation of the trained GBM on the full trace).

  deployed3.py --inst Region7_s0 --name T5 --cand PT --args '{"mu":5,"beta":1}' --reps 1 2 3
Every retrain appends one row to q3/trials.csv (unique key = exp) and q3/results/trials.jsonl.
Run in the Baleen env (lightgbm/compress_json); training holds X/.train.lock.
"""
import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.environ["X_ROOT"], "common", "src"))
import xc  # noqa: E402
import q3lib as QL  # noqa: E402

W = os.path.join(xc.Q3, "work")
LOGS = os.path.join(W, "logs")
RES = os.path.join(xc.Q3, "results")
JOBS = json.load(open(os.path.join(xc.COMMON, "jobs.json")))
SIM_POOL = ThreadPoolExecutor(max_workers=int(os.environ.get("Q3_SIM_WORKERS", "12")))
# log-space emulated->simulated write-rate map fitted on harness_eval's 37 deployed models (results/proxy_validate.csv)
WRMAP = {"Region7": (-1.288, 1.177), "Region6": (-0.770, 1.146)}
# refit (18:40) on this track's own dev simulations of PT-label models (q3/results/wrmap_refit.json): the old Region7
# map over-predicted the simulated WR by ~18% for these models. Seeding only (no effect on results).
WRMAP = {"Region7": (-0.138, 0.860), "Region6": (0.520, 0.801)}
TRIALS_CSV = os.path.join(xc.Q3, "trials.csv")


def fill_sim_args(sim_args, train_out):
    filled = []
    for a in sim_args:
        m = re.fullmatch(r"\{TRAIN:(\w+)\}", a)
        if m:
            path = train_out[m.group(1)][0]
            if m.group(1).startswith("model_prefetch_"):
                path = path.replace("_prefetch_offset_start.model", "_prefetch_{k}.model")
            a = path
        filled.append(a)
    return filled


def run_train(exp, targs, cfg):
    cfgp = os.path.join(W, "cfg", f"{exp}.json")
    os.makedirs(os.path.dirname(cfgp), exist_ok=True)
    json.dump(cfg, open(cfgp, "w"), indent=1)
    env = xc.base_env([HERE], W, extra={"HE_POLICY_CONFIG": cfgp}, threads=2)
    lp = os.path.join(LOGS, "q3", exp, "train.log")
    out = xc.parse_train_outputs(lp) if os.path.exists(lp) else None
    if out is not None and all(v[1] != "NoExists" for v in out.values()):
        return out, 0.0, 0.0
    with xc.TRAIN_LOCK as L:
        rc, dt = xc.run_logged([xc.BALEEN_PY, "-B", "-m", "launch_train"] + targs, lp, env, W)
        waited = L.waited
    out = xc.parse_train_outputs(lp)
    if rc != 0 or out is None or any(v[1] == "NoExists" for v in out.values()):
        raise RuntimeError(f"train failed rc={rc}: {lp}")
    txt = open(lp).read()
    assert "prefix rule reproduces" in txt, lp
    return out, dt, waited


_FEAT = {}


def predict_threshold(key, model_path):
    """Emulated WR curve of the trained admission GBM on the full trace (fullml dump of this instance), mapped to the
    simulator's WR scale; returns the threshold predicted to give 35.599 MB/s."""
    import lightgbm as lgb
    region = JOBS[key]["region"]
    if key not in _FEAT:
        I = QL.Inst(os.path.join(xc.COMMON, "inst", f"fullml_{key}.npz"))
        F = QL.sim_features(I, cache=os.path.join(W, "cache", f"simfeat_fullml_{key}.npz")).astype(float)
        _FEAT[key] = (I, F)
    I, F = _FEAT[key]
    g = lgb.Booster(model_file=os.path.join(W, model_path)).predict(F)
    a, b = WRMAP[region]
    target_emu = np.exp((np.log(xc.TARGET_WR) - a) / b)
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        _, wr, _ = QL.emulate_at(I, g, mid)
        if wr > target_emu:
            lo = mid
        else:
            hi = mid
    return float(hi)


def append_trial(row):
    xc.append_jsonl(os.path.join(RES, "trials.jsonl"), row)
    rows = xc.read_jsonl(os.path.join(RES, "trials.jsonl"))
    df = pd.DataFrame(rows)
    assert not df["trial_key"].duplicated().any(), "duplicate trial key"
    df.to_csv(TRIALS_CSV, index=False)


def one_rep(key, name, cand, solver_args, rep, stage):
    J = JOBS[key]
    exp = f"q3_{key}_{name}_rep{rep}"
    done = {r["trial_key"] for r in xc.read_jsonl(os.path.join(RES, "trials.jsonl"))}
    if exp in done:
        print(f"[skip] {exp} already logged", flush=True)
        return None
    t_start = time.time()
    targs = list(J["baleen"]["train_args"])
    targs = xc.set_flag(targs, "--exp", exp)
    targs = xc.set_flag(targs, "--output-base-dir", f"runs/q3/{exp}/train")
    targs = xc.set_flag(targs, "--policy", "PolicyPeakBaleen3")
    cfg = {"mode": "solver", "name": f"pb3_{name}_rep{rep}", "candidate": cand,
           "solver_args": dict(solver_args, seed=rep), "target_wr": xc.TARGET_WR, "skip_windows": 0,
           "solver_py": xc.solver_py(), "solver_cli": os.path.join(HERE, "q3solve.py"),
           "inst_path": os.path.join(W, "inst", f"{exp}.npz"), "sol_path": os.path.join(W, "inst", f"{exp}_sol.npz"),
           "dump_access": True}
    out, tdt, twait = run_train(exp, targs, cfg)
    sol = json.load(open(cfg["sol_path"].replace(".npz", ".json")))
    base = fill_sim_args(list(J["baleen"]["sim_args"]), out)
    base = xc.set_flag(base, "-o", f"runs/q3/{exp}/sim")
    base = xc.set_flag(base, "--job-id", exp)
    assert "--offline-ap-decisions" not in base and "--eviction-policy" in base
    try:
        thp = predict_threshold(key, out["model_admit_threshold_binary"][0])
    except Exception as ex:  # fall back to the authors' threshold
        print("[warn] threshold prediction failed:", ex, flush=True)
        thp = float(J["baleen"]["author"]["AP Threshold"])
    seeds = [round(thp - 0.012, 6), round(thp, 6), round(thp + 0.012, 6)]
    tried, best = xc.converge_loop(W, exp, base, seeds, SIM_POOL, os.path.join(LOGS, "q3", exp, "converge"),
                                   f"runs/q3/{exp}/converge", 0.02, increasing=False, lo_bound=0.0, hi_bound=1.0,
                                   max_rounds=8)
    df = pd.DataFrame(tried).sort_values("threshold")
    os.makedirs(os.path.join(RES, "converge"), exist_ok=True)
    df.to_csv(os.path.join(RES, "converge", f"{exp}.csv"), index=False)
    m = xc.metrics(best["result_file"])
    row = dict(trial_key=exp, stage=stage, instance=key, region=J["region"], sample=J["sample"], config=name,
               cand=cand, args=json.dumps(solver_args, sort_keys=True), rep=rep, seed=rep, threshold=best["threshold"],
               threshold_pred=thp, n_sims=int(df["wr"].notna().sum()),
               matched=bool(abs(best["wr"] - xc.TARGET_WR) / xc.TARGET_WR <= xc.TOL),
               wr=m["wr"], p100=m["p100"], p99=m["p99"], top5=m["top5"], mean_dt=m["mean_dt"], argmax=m["argmax"],
               top5_windows=json.dumps(m["top5_windows"]), train_secs=tdt, train_lock_wait=twait,
               wall_secs=time.time() - t_start, solve_secs=sol.get("total_secs"),
               label_peak_day1=sol.get("label_peak_util"), baleen_peak_day1=sol.get("baleen_peak_util"),
               label_top5_day1=sol.get("label_top5"), jaccard_vs_baleen=sol.get("jaccard_vs_baleen"),
               dt_ratio_day1=sol.get("dt_ratio"), n_label=sol.get("n_label"), n_fill=sol.get("n_fill"),
               solver_energy=(sol.get("solver") or {}).get("E"), move_share_pt=(sol.get("solver") or {}).get("move_share_pt"),
               result_file=os.path.relpath(best["result_file"], W))
    append_trial(row)
    print(f"== Q3 {key} {name} rep{rep}: P100={m['p100']:.3f} WR={m['wr']:.3f} th={best['threshold']:.5f} "
          f"(pred {thp:.4f}) matched={row['matched']} n_sims={row['n_sims']} top5={m['top5']:.2f} "
          f"meanDT={m['mean_dt']:.2f} J={row['jaccard_vs_baleen']}", flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", nargs="+", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--args", default="{}")
    ap.add_argument("--reps", type=int, nargs="+", default=[1])
    ap.add_argument("--stage", default="screen")
    o = ap.parse_args()
    tasks = [(k, r) for r in o.reps for k in o.inst]

    def safe(t):
        try:
            return one_rep(t[0], o.name, o.cand, json.loads(o.args), t[1], o.stage)
        except Exception as ex:   # log failures too (PROTOCOL rule 3)
            import traceback
            traceback.print_exc()
            key = f"q3_{t[0]}_{o.name}_rep{t[1]}__FAILED_{int(time.time())}"
            J = JOBS[t[0]]
            append_trial(dict(trial_key=key, stage=o.stage, instance=t[0], region=J["region"], sample=J["sample"],
                              config=o.name, cand=o.cand, args=json.dumps(json.loads(o.args), sort_keys=True),
                              rep=t[1], seed=t[1], matched=False, error=repr(ex)[:300]))
            return None
    with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
        list(ex.map(safe, tasks))


if __name__ == "__main__":
    main()
