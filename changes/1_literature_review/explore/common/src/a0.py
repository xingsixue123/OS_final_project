"""A0: shared instances + held-out baselines (Track A owns explore/common).

  a0.py dumps    [--keys Region7_s0.1 ...]   day-1 (deployed) + full-trace (offline) instance dumps
  a0.py opt      [--keys ...]                Baleen peak-blind OPT offline (full-trace decisions, cutoff converged)
  a0.py baleen   [--keys ...] --reps 1 2 3   Baleen online: authors' Fig 9 TrainCommand (stock policy) + converge
  a0.py static   [--keys ...]                RejectX + CoinFlip (authors' static_pf rows; ap-probability converged
                                              by bisection only if the authors' value misses 35.599 +-1%)
All Baleen processes: cwd common/work, taskset -c 8-23, bwrap private /tmp, flock X/.train.lock around every train.
Results: common/results/a0.jsonl (one row per run; every threshold tried in common/results/converge/<exp>.csv).
"""
import argparse
import json
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xc  # noqa: E402

W = os.path.join(xc.COMMON, "work")
LOGS = os.path.join(W, "logs")
RES = os.path.join(xc.COMMON, "results")
INST = os.path.join(xc.COMMON, "inst")
Q3SRC = os.path.join(xc.Q3, "src")
JOBS = json.load(open(os.path.join(xc.COMMON, "jobs.json")))
HELDOUT = [f"{r}_s{s}" for r in ["Region7", "Region6"] for s in ["0.1", "0.2", "0.3"]]
DEV = ["Region7_s0", "Region6_s0"]
POOL = ThreadPoolExecutor(max_workers=int(os.environ.get("A0_SIM_WORKERS", "10")))
_LOCK = threading.Lock()


def log(*a):
    with _LOCK:
        print(*a, flush=True)


def run_train(exp, args, cfg=None, lock=True, prefix="a0"):
    """Run one `train` (launcher if cfg is given, else the stock module) under the global train lock."""
    env = xc.base_env([Q3SRC], W, threads=2)
    if cfg is not None:
        p = os.path.join(W, "cfg", f"{exp}.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(cfg, open(p, "w"), indent=1)
        env["HE_POLICY_CONFIG"] = p
        mod = ["-m", "launch_train"]
    else:
        mod = ["-m", xc.TRAIN_MOD]
    lp = os.path.join(LOGS, prefix, exp, "train.log")
    out = xc.parse_train_outputs(lp) if os.path.exists(lp) else None
    need = [k for k in ("analysis", "thresholds") if k in (out or {})]
    if out is not None and all(out[k][1] != "NoExists" for k in need) and \
            (cfg is None or cfg.get("mode") not in ("dump",) or os.path.exists(cfg["inst_path"])):
        return out, lp, 0.0, 0.0
    with xc.TRAIN_LOCK as L:
        rc, dt = xc.run_logged([xc.BALEEN_PY, "-B"] + mod + args, lp, env, W)
        waited = L.waited
    out = xc.parse_train_outputs(lp)
    if rc != 0 or out is None:
        raise RuntimeError(f"train failed rc={rc}: {lp}")
    log(f"[train] {exp}: {dt:.0f}s (waited {waited:.0f}s for the lock)")
    return out, lp, dt, waited


# ------------------------------------------------------------------ instances
def day1_args(key, exp):
    J = JOBS[key]
    a = list(J["baleen"]["train_args"])
    a = xc.set_flag(a, "--exp", exp)
    a = xc.set_flag(a, "--output-base-dir", f"runs/a0/{exp}/train")
    a = xc.set_flag(a, "--policy", "PolicyPeakBaleen3")
    a = xc.remove_flag_nargs(a, "--train-models")      # instance only: no GBMs
    return a


def full_args(key, exp, ea):
    J = JOBS[key]
    return ["--exp", exp, "--policy", "PolicyPeakBaleen3", "--region", J["region"], "--sample-ratio", "0.1",
            "--sample-start", f"{J['sample']:g}" if J["sample"] else "0.0", "--trace-group", "20230325",
            "--supplied-ea", "physical", "--target-wrs", "34", "50", "100", "75", "20", "10", "60", "90", "30",
            "--target-csizes", "366.47461", "--output-base-dir", f"runs/a0/{exp}/train", "--eviction-age", f"{ea}",
            "--rl-init-kwargs", "filter_=prefetch", "--train-split-secs-start", "0",
            "--train-split-secs-end", "1000000000"]


def dump_cfg(name, inst, mode, skip):
    return {"mode": mode, "name": name, "target_wr": xc.TARGET_WR, "skip_windows": skip, "inst_path": inst,
            "dump_access": True}


def do_dumps(keys, which=("day1", "full")):
    for key in keys:
        J = JOBS[key]
        if "day1" in which:
            exp = f"a0_day1_{key}"
            inst = os.path.join(INST, f"day1_{key}.npz")
            run_train(exp, day1_args(key, exp), dump_cfg(f"pb3_day1_{key}", inst, "dump", 0))
            log(f"[dump] {inst} {os.path.getsize(inst) / 1e6:.1f} MB")
        if "full" in which:
            exp = f"a0_full_{key}"
            inst = os.path.join(INST, f"full_{key}.npz")
            run_train(exp, full_args(key, exp, J["opt"]["ea"]), dump_cfg(f"pb3_full_{key}", inst, "baleen",
                                                                          xc.SKIP_WINDOWS))
            log(f"[dump] {inst} {os.path.getsize(inst) / 1e6:.1f} MB")
        if "fullml" in which:   # dev analysis only: full trace at the deployed (ML) eviction age
            exp = f"a0_fullml_{key}"
            inst = os.path.join(INST, f"fullml_{key}.npz")
            run_train(exp, full_args(key, exp, J["ea_ml"]), dump_cfg(f"pb3_fullml_{key}", inst, "baleen",
                                                                      xc.SKIP_WINDOWS))
            log(f"[dump] {inst} {os.path.getsize(inst) / 1e6:.1f} MB")


# ------------------------------------------------------------------ convergence + rows
def finish(key, method, variant, rep, exp, tried, best, knob, extra=None):
    df = pd.DataFrame(tried).sort_values("threshold")
    os.makedirs(os.path.join(RES, "converge"), exist_ok=True)
    df.to_csv(os.path.join(RES, "converge", f"{exp}.csv"), index=False)
    m = xc.metrics(best["result_file"])
    J = JOBS[key]
    row = dict(instance=key, region=J["region"], sample=J["sample"], method=method, variant=variant, rep=rep,
               exp=exp, knob=knob, value=best["threshold"], n_sims=int(df["wr"].notna().sum()),
               matched=bool(abs(best["wr"] - xc.TARGET_WR) / xc.TARGET_WR <= xc.TOL),
               **{k: v for k, v in m.items() if k != "top5_windows"}, top5_windows=json.dumps(m["top5_windows"]),
               result_file=os.path.relpath(best["result_file"], W))
    if extra:
        row.update(extra)
    xc.append_jsonl(os.path.join(RES, "a0.jsonl"), row)
    log(f"== {key} {method}/{variant} rep{rep}: P100={m['p100']:.3f} WR={m['wr']:.3f} {knob}={best['threshold']:.6g} "
        f"matched={row['matched']} P99={m['p99']:.2f} top5={m['top5']:.2f} meanDT={m['mean_dt']:.2f} n={row['n_sims']}")
    return row


def fill_sim_args(sim_args, train_out):
    import re
    filled = []
    for a in sim_args:
        mm = re.fullmatch(r"\{TRAIN:(\w+)\}", a)
        if mm:
            path = train_out[mm.group(1)][0]
            if mm.group(1).startswith("model_prefetch_"):
                path = path.replace("_prefetch_offset_start.model", "_prefetch_{k}.model")
            a = path
        filled.append(a)
    return filled


def do_opt(key):
    J = JOBS[key]
    exp = f"a0_full_{key}"
    out, _, _, _ = run_train(exp, full_args(key, exp, J["opt"]["ea"]),
                             dump_cfg(f"pb3_full_{key}", os.path.join(INST, f"full_{key}.npz"), "baleen",
                                      xc.SKIP_WINDOWS))
    base = ["--trace", xc.trace_path(J["region"], J["sample"]), "--offline-ap", "--ap", "opt", "--ap-threshold", "30",
            "--size_gb", "366.475", "-o", f"runs/a0/{exp}/sim", "--prefetch-when", J["opt"]["prefetch_when"],
            "--prefetch-range", J["opt"]["prefetch_range"], "--batch-size", "16", "--log-interval", "600",
            "--ep-analysis", out["analysis"][0], "--offline-ap-decisions", out["thresholds"][0],
            "--job-id", exp, "--eviction-policy", "LRU"]
    th = J["opt"]["author_th"]
    tried, best = xc.converge_loop(W, exp, base, [round(th - 1, 6), round(th, 6), round(th + 1, 6)], POOL,
                                   os.path.join(LOGS, "a0", exp, "converge"), f"runs/a0/{exp}/converge", 2.0,
                                   increasing=True, lo_bound=0.0, hi_bound=1e6, max_rounds=6)
    return finish(key, "OPT", "peak-blind (Baleen order, OPT-Range on OPT-Ep-Start)", 0, exp, tried, best,
                  "ap-threshold(MB/s)", dict(author_th=th, author_p100=J["opt"]["author_p100"],
                                             author_wr=J["opt"]["author_wr"], ea=J["opt"]["ea"]))


def do_baleen(key, rep):
    J = JOBS[key]
    job = J["baleen"]
    exp = f"a0_baleen_{key}_rep{rep}"
    targs = list(job["train_args"])
    targs = xc.set_flag(targs, "--exp", exp)
    targs = xc.set_flag(targs, "--output-base-dir", f"runs/a0/{exp}/train")
    assert xc.get_flag(targs, "--policy") == "PolicyUtilityServiceTimeSize2"
    out, _, _, _ = run_train(exp, targs, None)
    base = fill_sim_args(list(job["sim_args"]), out)
    base = xc.set_flag(base, "-o", f"runs/a0/{exp}/sim")
    base = xc.set_flag(base, "--job-id", exp)
    assert "--offline-ap-decisions" not in base and "--eviction-policy" in base
    th = float(job["author"]["AP Threshold"])
    tried, best = xc.converge_loop(W, exp, base, [round(th - 0.02, 6), round(th, 6), round(th + 0.02, 6)], POOL,
                                   os.path.join(LOGS, "a0", exp, "converge"), f"runs/a0/{exp}/converge", 0.02,
                                   increasing=False, lo_bound=0.0, hi_bound=1.0, max_rounds=8)
    return finish(key, "Baleen", job["prefetching"], rep, exp, tried, best, "ap-threshold(prob)",
                  dict(author_th=th, author_p100=job["author"][RCY], author_wr=job["author"]["Write Rate (MB/s)"],
                       ea=float(xc.get_flag(targs, "--eviction-age"))))


RCY = "P100ServiceTimeUtil@10m"


def do_static(key, jkey):
    J = JOBS[key]
    job = J[jkey]
    exp = f"a0_{jkey}_{key}"
    targs = list(job["train_args"])
    targs = xc.set_flag(targs, "--exp", exp)
    targs = xc.set_flag(targs, "--output-base-dir", f"runs/a0/{exp}/train")
    out, _, _, _ = run_train(exp, targs, None)
    base = fill_sim_args(list(job["sim_args"]), out)
    base = xc.set_flag(base, "-o", f"runs/a0/{exp}/sim")
    base = xc.set_flag(base, "--job-id", exp)
    p0 = float(xc.get_flag(base, "--ap-probability"))
    r0 = xc.sim_at(W, exp, base, p0, os.path.join(LOGS, "a0", exp, "converge"), f"runs/a0/{exp}/converge",
                   flag="--ap-probability", fmt="{:.6f}")
    tried = [r0]
    best = r0
    converged = False
    if r0.get("wr") is None:
        raise RuntimeError(f"{exp}: {r0}")
    if abs(r0["wr"] - xc.TARGET_WR) / xc.TARGET_WR > xc.TOL:
        # bisection on the probability knob (WR increases with it)
        lo, hi = (p0, None) if r0["wr"] < xc.TARGET_WR else (None, p0)
        f = 1.25 if r0["wr"] < xc.TARGET_WR else 0.8
        p = p0
        for it in range(14):
            if lo is not None and hi is not None:
                p = round((lo + hi) / 2, 6)
            else:
                p = round(p * f, 6)
            r = xc.sim_at(W, exp, base, p, os.path.join(LOGS, "a0", exp, "converge"), f"runs/a0/{exp}/converge",
                          flag="--ap-probability", fmt="{:.6f}")
            tried.append(r)
            if r.get("wr") is None:
                raise RuntimeError(f"{exp}: {r}")
            if abs(r["wr"] - xc.TARGET_WR) / xc.TARGET_WR <= xc.TOL:
                best = r
                converged = True
                break
            if r["wr"] < xc.TARGET_WR:
                lo = p
            else:
                hi = p
        if not converged:
            best = min([x for x in tried if x.get("wr") is not None], key=lambda x: abs(x["wr"] - xc.TARGET_WR))
    pol = "RejectX" if jkey.startswith("rejectx") else "CoinFlip"
    return finish(key, pol, job["experiment"], 0, exp, tried, best, "ap-probability",
                  dict(author_prob=p0, author_p100=job["author"][RCY], author_wr=job["author"]["Write Rate (MB/s)"],
                       converged_by_bisection=bool(converged), ea=float(xc.get_flag(targs, "--eviction-age"))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["dumps", "dumps_dev", "dumps_fullml", "opt", "baleen", "static", "all"])
    ap.add_argument("--keys", nargs="+", default=HELDOUT)
    ap.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--static-variants", nargs="+", default=["rejectx_static", "coinflip_static"])
    o = ap.parse_args()
    if o.what == "dumps":
        do_dumps(o.keys)
    elif o.what == "dumps_fullml":   # threshold-seeding only (no tuning): full trace at the deployed EA
        do_dumps(o.keys, which=("fullml",))
    elif o.what == "dumps_dev":
        do_dumps(o.keys, which=("day1", "fullml", "full"))
    elif o.what == "opt":
        with ThreadPoolExecutor(max_workers=len(o.keys)) as ex:
            list(ex.map(do_opt, o.keys))
    elif o.what == "baleen":
        tasks = [(k, r) for r in o.reps for k in o.keys]
        with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
            list(ex.map(lambda t: do_baleen(*t), tasks))
    elif o.what == "static":
        tasks = [(k, v) for v in o.static_variants for k in o.keys]
        with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
            list(ex.map(lambda t: do_static(*t), tasks))


if __name__ == "__main__":
    main()
