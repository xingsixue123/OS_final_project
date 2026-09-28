"""Re-converge Baleen's admission threshold to the target flash write rate (paper Sec 4.1,
"Converging on Eviction Age, Policy Threshold": inner loop on the AP threshold).

Only --ap-threshold changes; the trained models, eviction age and every other flag are the
job's own (taken from its finished status file). Target = write rate, never peak load.

  python repro/converge.py fig9 --only Region7_s0_baleen --only Region6_s0_baleen
Results: work/results/converge_<job_id>.csv (one row per threshold tried).
"""
import argparse
import json
import os
import shlex
from concurrent.futures import ThreadPoolExecutor

import common as C
import run as R

TOL = 0.01  # |WR - target| / target


def sim(job_id, base_args, th, set_name):
    tag = f"th_{th:.6f}"
    out = f"runs/repro/{job_id}/converge/{tag}"
    args = C.set_flag(list(base_args), "--ap-threshold", f"{th:.6f}")
    args = C.set_flag(args, "-o", out)
    args = C.set_flag(args, "--job-id", f"{job_id}__{tag}".replace("/", "__"))
    log = os.path.join(C.LOGS_DIR, set_name, job_id, "converge", f"{tag}.log")
    res_glob = os.path.join(C.WORK, out)
    import glob
    done = glob.glob(os.path.join(res_glob, "**", "*_cache_perf.txt.lzma"), recursive=True)
    if not done:
        rc, dt = R.run_logged([C.PY, "-B", "-m", C.SIM_MOD] + args, log)
        if rc != 0:
            return {"threshold": th, "error": f"rc={rc}", "log": log}
        done = glob.glob(os.path.join(res_glob, "**", "*_cache_perf.txt.lzma"), recursive=True)
    import compress_json
    r = compress_json.load(done[0])["results"]
    return {"threshold": th, "wr": r["FlashWriteRate"], "peak": r["PeakServiceTimeUtil1"],
            "result_file": os.path.relpath(done[0], C.WORK)}


def converge_loop(tag, base, tried, pool, set_name, step, max_rounds=4):
    """Inner loop on --ap-threshold until WR is within TOL of target. `tried` = seed results."""
    th0 = float(C.get_flag(base, "--ap-threshold"))
    grid = [round(th0 + step * k, 6) for k in range(1, 7)] if len(tried) == 1 else []
    best = None
    for rnd in range(max_rounds):
        grid = [t for t in grid if 0 < t < 1 and all(abs(t - x["threshold"]) > 1e-6 for x in tried)]
        tried += [x for x in pool.map(lambda t: sim(tag, base, t, set_name), grid)]
        ok = [x for x in tried if x.get("wr") is not None]
        best = min(ok, key=lambda x: abs(x["wr"] - C.TARGET_WR))
        print(f"[{tag}] round {rnd}: best th={best['threshold']:.5f} WR={best['wr']:.3f} "
              f"peak={best['peak']:.2f}", flush=True)
        if abs(best["wr"] - C.TARGET_WR) / C.TARGET_WR <= TOL:
            break
        lo = [x for x in ok if x["wr"] > C.TARGET_WR]   # thresholds too low
        hi = [x for x in ok if x["wr"] < C.TARGET_WR]   # thresholds too high
        if lo and hi:
            a = max(lo, key=lambda x: x["threshold"])
            b = min(hi, key=lambda x: x["threshold"])
            t = a["threshold"] + (a["wr"] - C.TARGET_WR) * (b["threshold"] - a["threshold"]) / (a["wr"] - b["wr"])
            d = abs(b["threshold"] - a["threshold"]) / 4
            grid = [round(t - d, 6), round(t, 6), round(t + d, 6)]
        else:
            step = 0.02 if best["wr"] > C.TARGET_WR else -0.02
            edge = max(ok, key=lambda x: x["threshold"]) if step > 0 else min(ok, key=lambda x: x["threshold"])
            grid = [round(edge["threshold"] + step * k, 6) for k in range(1, 7)]
    return tried, best


def converge(set_name, job_id, pool, max_rounds=4):
    st = json.load(open(os.path.join(C.JOBS_DIR, set_name, f"{job_id}.json")))
    base = shlex.split(st["sim_cmd"])
    base = base[base.index(C.SIM_MOD) + 1:]
    import compress_json
    rr = compress_json.load(os.path.join(C.WORK, st["result_file"]))["results"]
    r0 = {"threshold": float(C.get_flag(base, "--ap-threshold")), "wr": rr["FlashWriteRate"],
          "peak": rr["PeakServiceTimeUtil1"], "result_file": st["result_file"]}
    step = 0.02 if r0["wr"] > C.TARGET_WR else -0.02
    tried, best = converge_loop(job_id, base, [r0], pool, set_name, step, max_rounds)
    import pandas as pd
    df = pd.DataFrame(tried).sort_values("threshold")
    df["wr_err_pct"] = 100 * (df["wr"] - C.TARGET_WR) / C.TARGET_WR
    df.to_csv(os.path.join(C.WORK, "results", f"converge_{job_id}.csv"), index=False)
    return df, best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set")
    ap.add_argument("--only", action="append", required=True)
    ap.add_argument("-j", "--jobs", type=int, default=12)
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    R.THREADS = a.threads
    R.check_frozen()
    ids = [f[:-5] for f in os.listdir(os.path.join(C.JOBS_DIR, a.set))
           if f.endswith(".json") and any(o in f for o in a.only)]
    with ThreadPoolExecutor(max_workers=a.jobs) as pool, ThreadPoolExecutor(max_workers=len(ids)) as outer:
        outs = list(outer.map(lambda j: (j, converge(a.set, j, pool)), ids))
    for j, (df, best) in outs:
        print(f"\n== {j}\n{df.to_string(index=False)}\n-> matched-WR threshold {best['threshold']:.5f}: "
              f"WR={best['wr']:.3f} peak={best['peak']:.2f}")
    R.check_frozen()


if __name__ == "__main__":
    main()
