"""Offline (OPT) mode: full-trace episodes -> PolicyPeakBaleen selection -> decisions file ->
`simulate_ap --ap opt` (unmodified OfflineAP) with --ap-threshold re-converged to 35.599 MB/s +-1%.

  offline.py --region Region7 --name R1 --cand R1 --args '{"levels": [...]}'  [--th-hint 29.4]
Train: authors' OPT-AP train args (filter_=prefetch, OPT's own converged EA), no GBMs, and
--train-split-secs-end 1e9 so the decisions cover the whole trace. Sim: authors' "OPT-Range on
OPT-Ep-Start" ReproduceCommand (prefetch-when at_start, prefetch-range acctime-episode) + --eviction-policy LRU.
"""
import argparse
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

import hecommon as HC

SIM_POOL = ThreadPoolExecutor(max_workers=int(os.environ.get("HE_SIM_WORKERS", "14")))
_CSV_LOCK = threading.Lock()


def train_args(region, exp, ea):
    return ["--exp", exp, "--policy", "PolicyPeakBaleen", "--region", region, "--sample-ratio", "0.1",
            "--sample-start", "0.0", "--trace-group", "20230325", "--supplied-ea", "physical",
            "--target-wrs", "34", "50", "100", "75", "20", "10", "60", "90", "30",
            "--target-csizes", "366.47461", "--output-base-dir", f"runs/off/{exp}/train",
            "--eviction-age", f"{ea}", "--rl-init-kwargs", "filter_=prefetch",
            "--train-split-secs-start", "0", "--train-split-secs-end", "1000000000"]


def policy_cfg(name, exp, cand, solver_args, skip_windows):
    mode = "baleen" if cand in ("R0",) else "solver"
    return {"mode": mode, "name": f"pb_{name}", "candidate": cand, "solver_args": solver_args,
            "target_wr": HC.TARGET_WR, "skip_windows": skip_windows,
            "solver_py": HC.SOLVER_PY, "solver_cli": os.path.join(HC.SRC, "solve.py"),
            "inst_path": os.path.join(HC.WORK, "inst", f"{exp}.npz"),
            "sol_path": os.path.join(HC.WORK, "inst", f"{exp}_sol.npz")}


def run_train(region, name, cand, solver_args, ea=None, prefix="off", skip_windows=HC.SKIP_WINDOWS, lock=False,
              extra_args=None):
    ea = ea or HC.TRACES[region]["ea_opt"]
    exp = f"{prefix}_{region}_{name}"
    cfg = policy_cfg(name, exp, cand, solver_args, skip_windows)
    cfgp = os.path.join(HC.WORK, "cfg", f"{exp}.json")
    os.makedirs(os.path.dirname(cfgp), exist_ok=True)
    json.dump(cfg, open(cfgp, "w"), indent=1)
    env = HC.base_env(extra={"HE_POLICY_CONFIG": cfgp}, threads=int(solver_args.get("threads", 2)))
    log = os.path.join(HC.LOGS, prefix, exp, "train.log")
    targs = extra_args if extra_args is not None else train_args(region, exp, ea)
    args = [HC.BALEEN_PY, "-B", "-m", "launch_train"] + targs
    out = HC.parse_train_outputs(log) if os.path.exists(log) else None
    if out is None or any(sz == "NoExists" for _, sz in out.values()):
        if lock:
            with HC.TRAIN_LOCK:
                rc, dt = HC.run_logged(args, log, env=env)
        else:
            rc, dt = HC.run_logged(args, log, env=env)
        out = HC.parse_train_outputs(log)
        if rc != 0 or out is None:
            raise RuntimeError(f"train failed rc={rc}: {log}")
    sol_json = cfg["sol_path"].replace(".npz", ".json")
    return dict(exp=exp, out=out, cfg=cfg, log=log,
                sol=json.load(open(sol_json)) if os.path.exists(sol_json) else None)


def sim_base(region, exp, out):
    return ["--trace", HC.trace_path(region), "--offline-ap", "--ap", "opt", "--ap-threshold", "30",
            "--size_gb", "366.475", "-o", f"runs/off/{exp}/sim", "--prefetch-when", "at_start",
            "--prefetch-range", "acctime-episode", "--batch-size", "16", "--log-interval", "600",
            "--ep-analysis", out["analysis"][0], "--offline-ap-decisions", out["thresholds"][0],
            "--job-id", exp, "--eviction-policy", "LRU"]


def converge(region, exp, out, th_hint, step=2.0):
    base = sim_base(region, exp, out)
    seeds = [round(th_hint - 1.0, 6), round(th_hint, 6), round(th_hint + 1.0, 6)]
    tried, best = HC.converge_loop(exp, base, seeds, SIM_POOL, os.path.join(HC.LOGS, "off", exp, "converge"),
                                   f"runs/off/{exp}/converge", step, increasing=True, lo_bound=0.0,
                                   hi_bound=1e6, max_rounds=6)
    df = pd.DataFrame(tried).sort_values("threshold")
    df["wr_err_pct"] = 100 * (df["wr"] - HC.TARGET_WR) / HC.TARGET_WR
    os.makedirs(os.path.join(HC.RESULTS, "converge"), exist_ok=True)
    df.to_csv(os.path.join(HC.RESULTS, "converge", f"{exp}.csv"), index=False)
    return df, best


def append_row(row, store="offline"):
    """Append to results/<store>.jsonl and rewrite results/<store>.csv from all rows."""
    with _CSV_LOCK:
        p = os.path.join(HC.RESULTS, f"{store}.jsonl")
        with open(p, "a") as f:
            f.write(json.dumps(row, default=float) + "\n")
        rows = [json.loads(l) for l in open(p) if l.strip()]
        pd.DataFrame(rows).to_csv(os.path.join(HC.RESULTS, f"{store}.csv"), index=False)


def load_rows(store="offline"):
    p = os.path.join(HC.RESULTS, f"{store}.jsonl")
    return pd.DataFrame([json.loads(l) for l in open(p) if l.strip()])


def evaluate(region, name, cand, solver_args, th_hint=None, csv="offline", prefix="off"):
    tr = run_train(region, name, cand, solver_args, prefix=prefix)
    th_hint = th_hint or HC.TRACES[region]["opt_author_th"]
    df, best = converge(region, tr["exp"], tr["out"], th_hint)
    matched = abs(best["wr"] - HC.TARGET_WR) / HC.TARGET_WR <= HC.TOL
    m = HC.metrics(best["result_file"])
    row = dict(region=region, name=name, prefix=prefix, cand=cand, args=json.dumps(solver_args), exp=tr["exp"],
               threshold=best["threshold"], matched=matched, n_sims=len(df), **{k: v for k, v in m.items()
                                                                               if k != "top5_windows"},
               top5_windows=json.dumps(m["top5_windows"]), result_file=os.path.relpath(best["result_file"], HC.WORK))
    s = tr["sol"]
    if s:
        for k in ["peak_util", "z_lp_util", "gap_to_zlp", "headroom_recovered", "baleen_peak_util", "solve_secs",
                  "argmax", "n_sel", "sts", "baleen_sts", "n_fill", "top5_util", "mean_util"]:
            row["an_" + k] = s.get(k)
    append_row(row, csv)
    print(f"== {region} {name}: P100={m['p100']:.3f} WR={m['wr']:.3f} th={best['threshold']:.4f} "
          f"matched={matched} P99={m['p99']:.3f} top5={m['top5']:.3f} meanDT={m['mean_dt']:.3f} "
          f"argmax={m['argmax']}", flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--args", default="{}")
    ap.add_argument("--th-hint", type=float)
    ap.add_argument("--csv", default="offline")
    ap.add_argument("--prefix", default="off")
    o = ap.parse_args()
    evaluate(o.region, o.name, o.cand, json.loads(o.args), o.th_hint, o.csv, o.prefix)


if __name__ == "__main__":
    main()
