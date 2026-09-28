"""Baleen retrain-to-retrain distribution at matched write rate.

Retraining is not deterministic (LightGBM num_threads=20 + 8-worker episode generation give
different models from identical commands), so the authors' single Baleen number is one draw.
For each Baleen job: K fresh retrains with the authors' exact TrainCommand, each with its AP
threshold re-converged to the target write rate (converge.converge_loop). Replicate 0 is the
original fig9 run's converged result. Every replicate is reported (no selection).

  python repro/retrain_dist.py fig9 --only Region7_s0_baleen --only Region6_s0_baleen -k 8
-> work/results/retrain_dist.csv
"""
import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

import common as C
import converge as V
import run as R


def replicate(set_name, job, k, th_start, pool):
    jid = job["job_id"]
    tag = f"{jid}/rep{k}"
    logd = os.path.join(C.LOGS_DIR, set_name, jid, f"rep{k}")
    targs = C.set_flag(list(job["train_args"]), "--exp", f"{jid}_rep{k}")
    targs = C.set_flag(targs, "--output-base-dir", f"runs/repro/{jid}/rep{k}/train")
    with R.TRAIN_LOCK:
        rc, _ = R.run_logged([C.PY, "-B", "-m", C.TRAIN_MOD] + targs, os.path.join(logd, "train.log"))
    out = R.parse_train_outputs(os.path.join(logd, "train.log"))
    if rc != 0 or out is None or any(sz == "NoExists" for _, sz in out.values()):
        return {"job": jid, "rep": k, "error": f"train rc={rc}"}
    base = R.fill_sim_args(list(job["sim_args"]), out)
    base = C.set_flag(base, "--ap-threshold", f"{th_start:.6f}")
    seed = list(pool.map(lambda t: V.sim(tag, base, t, set_name), [th_start - 0.02, th_start, th_start + 0.02]))
    tried, best = V.converge_loop(tag, base, seed, pool, set_name, step=0.02)
    return {"job": jid, "rep": k, "threshold": best["threshold"], "wr": best["wr"], "peak": best["peak"],
            "n_sims": len(tried), "matched": abs(best["wr"] - C.TARGET_WR) / C.TARGET_WR <= V.TOL}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set")
    ap.add_argument("--only", action="append", required=True)
    ap.add_argument("-k", type=int, default=8)
    ap.add_argument("-j", "--jobs", type=int, default=12)
    a = ap.parse_args()
    R.THREADS = 2
    R.check_frozen()
    jobs = [j for j in C.load_jobs(a.set) if any(o in j["job_id"] for o in a.only)]
    rows = []
    for j in jobs:  # replicate 0 = original run, converged by converge.py
        cv = pd.read_csv(os.path.join(C.WORK, "results", f"converge_{j['job_id']}.csv"))
        b = cv.iloc[(cv.wr - C.TARGET_WR).abs().argmin()]
        rows.append({"job": j["job_id"], "rep": 0, "threshold": b.threshold, "wr": b.wr, "peak": b.peak,
                     "matched": abs(b.wr - C.TARGET_WR) / C.TARGET_WR <= V.TOL})
    with ThreadPoolExecutor(max_workers=a.jobs) as pool, ThreadPoolExecutor(max_workers=len(jobs) * a.k) as outer:
        futs = []
        for j in jobs:
            th0 = [r for r in rows if r["job"] == j["job_id"]][0]["threshold"]
            futs += [outer.submit(replicate, a.set, j, k, th0, pool) for k in range(1, a.k + 1)]
        for f in futs:
            r = f.result()
            rows.append(r)
            print("REP", json.dumps(r), flush=True)
    df = pd.DataFrame(rows).sort_values(["job", "rep"])
    df.to_csv(os.path.join(C.WORK, "results", "retrain_dist.csv"), index=False)
    for jid, d in df.groupby("job"):
        m = d[d.matched == True]
        print(f"\n== {jid}: {len(m)}/{len(d)} replicates at matched WR")
        print(m[["rep", "threshold", "wr", "peak"]].to_string(index=False))
        print(f"   peak mean={m.peak.mean():.2f} sd={m.peak.std():.2f} min={m.peak.min():.2f} max={m.peak.max():.2f}")
    R.check_frozen()


if __name__ == "__main__":
    main()
