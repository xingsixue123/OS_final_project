"""WP3 preparation (PROTOCOL_v2_H3 §7), adapted from explore/common/src/a0.py (phase 1). FROZEN code only
(work_frozen/BCacheSim -> 0_reproduce/baleen_code); nothing here touches the overlay or any test arm.

  prep.py dumps   [--keys ...]  day1_<key>.npz (deployed day-1 instance: the authors' Baleen TrainCommand for that sample,
                                --train-models removed, skip_windows 0) and fullml_<key>.npz (full trace at the deployed
                                EA; threshold seeding / mechanism statistics only) through the UNMODIFIED train.main()
                                with phase-1's dump Policy (src/pb3_policy.py via src/launch_train.py, copied unchanged)
  prep.py static  [--keys ...]  RejectX + CoinFlip replays (the authors' 20230410_static_pf commands; ap-probability
                                bisected only if the authors' value misses 35.599 MB/s +-1%, as a0.do_static)
  prep.py sha                   sha256 of every instance -> results/instances_sha256.csv
"""
import argparse
import hashlib
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wpcommon as C  # noqa: E402

FROZEN = C.WORK_FROZEN
LOGS = os.path.join(C.W, "logs", "prep")
RES = os.path.join(C.W, "results")
SKIP_WINDOWS = 144


def remove_flag_nargs(args, flag):
    out, i = [], 0
    while i < len(args):
        if args[i] == flag:
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                i += 1
        else:
            out.append(args[i])
            i += 1
    return out


def run_train(exp, args, cfg=None):
    env = C.base_env(threads=2, work=FROZEN)
    if cfg is not None:
        p = os.path.join(RES, "cfg_prep", f"{exp}.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(cfg, open(p, "w"), indent=1)
        env["HE_POLICY_CONFIG"] = p
        mod = ["-m", "launch_train"]
    else:
        mod = ["-m", "BCacheSim.episodic_analysis.train"]
    lp = os.path.join(LOGS, exp, "train.log")
    out = C.parse_train_outputs(lp, work=FROZEN) if os.path.exists(lp) else None
    if out is not None and (cfg is None or os.path.exists(cfg["inst_path"])):
        return out
    with C.TrainLock():
        rc, dt = C.run_logged(mod + args, lp, env=env, work=FROZEN, cpuset=C.cpus())
    out = C.parse_train_outputs(lp, work=FROZEN)
    if rc != 0 or out is None:
        raise RuntimeError(f"train failed rc={rc}: {lp}")
    print(f"[train] {exp}: {dt:.0f}s", flush=True)
    return out


def dump_cfg(name, inst, mode, skip):
    return {"mode": mode, "name": name, "target_wr": C.TARGET_WR, "skip_windows": skip, "inst_path": inst,
            "dump_access": True}


def full_args(key, exp, ea):
    J = C.JOBS[key]
    return ["--exp", exp, "--policy", "PolicyPeakBaleen3", "--region", J["region"], "--sample-ratio", "0.1",
            "--sample-start", f"{J['sample']:g}", "--trace-group", "20230325",
            "--supplied-ea", "physical", "--target-wrs", "34", "50", "100", "75", "20", "10", "60", "90", "30",
            "--target-csizes", "366.47461", "--output-base-dir", f"runs/prep/{exp}/train", "--eviction-age", f"{ea}",
            "--rl-init-kwargs", "filter_=prefetch", "--train-split-secs-start", "0",
            "--train-split-secs-end", "1000000000"]


def do_dumps(key):
    J = C.JOBS[key]
    exp = f"prep_day1_{key}"
    inst = os.path.join(C.W, "inst", f"day1_{key}.npz")
    a = list(J["baleen"]["train_args"])
    a = C.set_flag(a, "--exp", exp)
    a = C.set_flag(a, "--output-base-dir", f"runs/prep/{exp}/train")
    a = C.set_flag(a, "--policy", "PolicyPeakBaleen3")
    a = remove_flag_nargs(a, "--train-models")        # instance only: no GBMs
    run_train(exp, a, dump_cfg(f"pb3_day1_{key}", inst, "dump", 0))
    print(f"[dump] {inst} {os.path.getsize(inst) / 1e6:.1f} MB", flush=True)
    exp = f"prep_fullml_{key}"
    inst = os.path.join(C.W, "inst", f"fullml_{key}.npz")
    run_train(exp, full_args(key, exp, J["ea_ml"]), dump_cfg(f"pb3_fullml_{key}", inst, "baleen", SKIP_WINDOWS))
    print(f"[dump] {inst} {os.path.getsize(inst) / 1e6:.1f} MB", flush=True)


def sim_at(exp, base, p):
    tag = f"p_{p:.6f}"
    out = f"runs/prep/{exp}/sim/{tag}"
    args = C.set_flag(list(base), "--ap-probability", f"{p:.6f}")
    args = C.set_flag(args, "-o", out)
    args = C.set_flag(args, "--job-id", f"{exp}__{tag}")
    done = C.result_files(out, work=FROZEN)
    lp = os.path.join(LOGS, exp, f"{tag}.log")
    if not done:
        with C.SimSlot() as S:
            rc, _ = C.run_logged(["-m", "BCacheSim.cachesim.simulate_ap"] + args, lp,
                                 env=C.base_env(threads=2, work=FROZEN), work=FROZEN, cpuset=S.cpuset)
        if "Traceback (most recent call last)" in open(lp).read():
            raise RuntimeError(f"sim failed: {lp}")
        done = C.result_files(out, work=FROZEN)
        if rc != 0 or not done:
            raise RuntimeError(f"sim failed rc={rc}: {lp}")
    r = C.load_result(done[0])["results"]
    return dict(p=p, wr=r["FlashWriteRate"], p100=r["PeakServiceTimeUtil1"], result_file=done[0])


def do_static(key, jkey):
    J = C.JOBS[key]
    job = J[jkey]
    exp = f"prep_{jkey}_{key}"
    t = list(job["train_args"])
    t = C.set_flag(t, "--exp", exp)
    t = C.set_flag(t, "--output-base-dir", f"runs/prep/{exp}/train")
    out = run_train(exp, t, None)
    base = C.fill_sim_args(list(job["sim_args"]), out)
    p0 = float(C.get_flag(base, "--ap-probability"))
    tried = [sim_at(exp, base, p0)]
    T = C.TARGET_WR
    ok = lambda r: abs(r["wr"] - T) / T <= C.TOL  # noqa: E731
    converged = ok(tried[0])
    if not converged:                     # bisection on the probability knob (WR increases with it), as a0.do_static
        lo, hi = (p0, None) if tried[0]["wr"] < T else (None, p0)
        f = 1.25 if tried[0]["wr"] < T else 0.8
        p = p0
        for _ in range(14):
            p = round((lo + hi) / 2, 6) if (lo is not None and hi is not None) else round(p * f, 6)
            r = sim_at(exp, base, p)
            tried.append(r)
            if ok(r):
                converged = True
                break
            if r["wr"] < T:
                lo = p
            else:
                hi = p
    best = min(tried, key=lambda r: abs(r["wr"] - T))
    m = C.metrics(best["result_file"])
    pol = "RejectX" if jkey.startswith("rejectx") else "CoinFlip"
    row = dict(instance=key, method=pol, experiment=job["experiment"], code="frozen 0_reproduce/baleen_code",
               ap_probability=best["p"], author_prob=p0, n_sims=len(tried), bisected=len(tried) > 1,
               matched=ok(best), wr=m["wr"], p100=m["p100"], p99=m["p99"], top5=m["top5"], mean_dt=m["mean_dt"],
               argmax=m["argmax"], author_p100=job["author"]["P100ServiceTimeUtil@10m"],
               author_wr=job["author"]["Write Rate (MB/s)"], result_file=os.path.relpath(best["result_file"], C.W))
    print(f"== {key} {pol}: P100={m['p100']:.4f} WR={m['wr']:.3f} p={best['p']} (author p={p0}, author P100 "
          f"{row['author_p100']:.4f}) matched={row['matched']} sims={len(tried)}", flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["dumps", "static", "sha"])
    ap.add_argument("--keys", nargs="+", default=C.TEST)
    o = ap.parse_args()
    os.makedirs(RES, exist_ok=True)
    if o.what == "dumps":
        with ThreadPoolExecutor(max_workers=3) as ex:
            list(ex.map(do_dumps, o.keys))
    elif o.what == "static":
        tasks = [(k, v) for v in ("rejectx_static", "coinflip_static") for k in o.keys]
        with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
            rows = list(ex.map(lambda t: do_static(*t), tasks))
        pd.DataFrame(rows).to_csv(os.path.join(RES, "static_baselines.csv"), index=False)
        print(pd.DataFrame(rows)[["instance", "method", "p100", "wr", "matched", "author_p100", "ap_probability", "author_prob"]].to_string())
    elif o.what == "sha":
        rows = []
        for f in sorted(os.listdir(os.path.join(C.W, "inst"))):
            if f.endswith(".npz"):
                pth = os.path.join(C.W, "inst", f)
                rows.append(dict(file=f, bytes=os.path.getsize(pth), sha256=hashlib.sha256(open(pth, "rb").read()).hexdigest()))
        pd.DataFrame(rows).to_csv(os.path.join(RES, "instances_sha256.csv"), index=False)
        print(pd.DataFrame(rows).to_string())


if __name__ == "__main__":
    main()
