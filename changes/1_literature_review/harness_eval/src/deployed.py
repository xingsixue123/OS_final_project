"""Deployed (ML) mode: day-1 selection by PolicyPeakBaleen -> labels (threshold < 35.599) -> the authors'
unchanged GBMs (train_ap / train_prefetcher via the authors' Fig 9 Baleen TrainCommand) -> `simulate_ap --ap
mlnew` with the authors' ReproduceCommand for that trace (Region7: ML-Range on ML-When; Region6: All on Partial
Hit) + --eviction-policy LRU, minus --offline-ap-decisions; --ap-threshold re-converged to 35.599 +-1%.

  deployed.py --region Region7 --name C2 --cand C2 --args '{...}' --reps 3
Training (incl. the day-1 solve) runs under the H/work train lock (LightGBM num_threads=20 is hard-coded).
"""
import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

import hecommon as HC
import offline as OF

SIM_POOL = ThreadPoolExecutor(max_workers=int(os.environ.get("HE_SIM_WORKERS", "6")))
BALEEN_TH = {"Region7": 0.62094, "Region6": 0.806378}   # 0_reproduce converged Baleen thresholds (rep 0)


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


def one_rep(region, name, cand, solver_args, rep, th0):
    job = HC.load_fig9_job(HC.TRACES[region]["ml_job"])
    exp = f"dep_{region}_{name}_rep{rep}"
    targs = list(job["train_args"])
    targs = HC.set_flag(targs, "--exp", exp)
    targs = HC.set_flag(targs, "--output-base-dir", f"runs/dep/{exp}/train")
    targs = HC.set_flag(targs, "--policy", "PolicyPeakBaleen")
    tr = OF.run_train(region, f"{name}_rep{rep}", cand, solver_args, prefix="dep", skip_windows=0, lock=True,
                      extra_args=targs)
    base = fill_sim_args(list(job["sim_args"]), tr["out"])
    base = HC.set_flag(base, "-o", f"runs/dep/{exp}/sim")
    base = HC.set_flag(base, "--job-id", exp)
    assert "--offline-ap-decisions" not in base and "--eviction-policy" in base
    seeds = [round(th0 - 0.02, 6), round(th0, 6), round(th0 + 0.02, 6)]
    tried, best = HC.converge_loop(exp, base, seeds, SIM_POOL, os.path.join(HC.LOGS, "dep", exp, "converge"),
                                   f"runs/dep/{exp}/converge", 0.02, increasing=False, lo_bound=0.0, hi_bound=1.0,
                                   max_rounds=8)
    df = pd.DataFrame(tried).sort_values("threshold")
    os.makedirs(os.path.join(HC.RESULTS, "converge"), exist_ok=True)
    df.to_csv(os.path.join(HC.RESULTS, "converge", f"{exp}.csv"), index=False)
    m = HC.metrics(best["result_file"])
    row = dict(region=region, name=name, cand=cand, rep=rep, args=json.dumps(solver_args), exp=exp,
               threshold=best["threshold"], matched=abs(best["wr"] - HC.TARGET_WR) / HC.TARGET_WR <= HC.TOL,
               n_sims=len(df), **{k: v for k, v in m.items() if k != "top5_windows"},
               top5_windows=json.dumps(m["top5_windows"]), result_file=os.path.relpath(best["result_file"], HC.WORK))
    s = tr["sol"]
    if s:
        for k in ["peak_util", "z_lp_util", "gap_to_zlp", "baleen_peak_util", "solve_secs", "n_sel", "sts",
                  "baleen_sts"]:
            row["an1_" + k] = s.get(k)
    OF.append_row(row, "deployed")
    print(f"== DEP {region} {name} rep{rep}: P100={m['p100']:.3f} WR={m['wr']:.3f} th={best['threshold']:.5f} "
          f"matched={row['matched']} P99={m['p99']:.3f} top5={m['top5']:.3f} meanDT={m['mean_dt']:.3f}", flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--args", default="{}")
    ap.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--th0", type=float)
    o = ap.parse_args()
    th0 = o.th0 or BALEEN_TH[o.region]
    with ThreadPoolExecutor(max_workers=len(o.reps)) as ex:
        list(ex.map(lambda r: one_rep(o.region, o.name, o.cand, json.loads(o.args), r, th0), o.reps))


if __name__ == "__main__":
    main()
