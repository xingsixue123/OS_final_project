"""Aggregate baselines -> common/baselines.csv (+ per-instance summary common/baselines_summary.csv).

Held-out rows: common/results/a0.jsonl (this track's runs). Dev rows (sample 0) reused, read-only:
  Baleen online: 0_reproduce/work/results/retrain_dist.csv (9 retrains per trace, matched WR)
  RejectX/CoinFlip: 0_reproduce fig9 replays (20230410_static_pf; bit-exact vs the authors)
  OPT peak-blind: harness_eval/results/offline.csv (R0)
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xc  # noqa: E402


def dev_rows():
    rows = []
    rd = pd.read_csv(os.path.join(xc.REPRO, "work", "results", "retrain_dist.csv"))
    for _, r in rd.iterrows():
        region = "Region7" if "Region7" in r.job else "Region6"
        rows.append(dict(instance=f"{region}_s0", region=region, sample=0.0, method="Baleen",
                         variant="Fig 9 (0_reproduce retrain_dist)", rep=int(r.rep), knob="ap-threshold(prob)",
                         value=r.threshold, wr=r.wr, p100=r.peak, matched=bool(r.matched),
                         source="0_reproduce/work/results/retrain_dist.csv"))
    js = json.load(open(os.path.join(xc.COMMON, "jobs.json")))
    ref = {("Region7", "RejectX"): 42.455387, ("Region7", "CoinFlip"): 48.960956,
           ("Region6", "RejectX"): 42.321079, ("Region6", "CoinFlip"): 43.445335}
    for region in ["Region7", "Region6"]:
        for pol in ["RejectX", "CoinFlip"]:
            j = js[f"{region}_s0"][f"{pol.lower()}_static"]
            rows.append(dict(instance=f"{region}_s0", region=region, sample=0.0, method=pol,
                             variant="20230410_static_pf (0_reproduce fig9 replay, bit-exact)", rep=0,
                             knob="ap-probability", value=float(xc.get_flag(j["sim_args"], "--ap-probability")),
                             wr=j["author"]["Write Rate (MB/s)"], p100=ref[(region, pol)], matched=True,
                             source="0_reproduce/RESULTS.md section 2"))
    off = pd.read_csv(os.path.join(xc.HARNESS, "results", "offline.csv"))
    for region in ["Region7", "Region6"]:
        r = off[(off.region == region) & (off.name == "R0")].iloc[-1]
        rows.append(dict(instance=f"{region}_s0", region=region, sample=0.0, method="OPT",
                         variant="peak-blind (harness_eval R0)", rep=0, knob="ap-threshold(MB/s)", value=r.threshold,
                         wr=r.wr, p100=r.p100, p99=r.p99, top5=r.top5, mean_dt=r.mean_dt, matched=bool(r.matched),
                         source="harness_eval/results/offline.csv"))
    return rows


def main():
    a0 = xc.read_jsonl(os.path.join(xc.COMMON, "results", "a0.jsonl"))
    for r in a0:
        r["source"] = "common/results/a0.jsonl"
    df = pd.DataFrame(dev_rows() + a0)
    df = df.drop_duplicates(subset=["instance", "method", "variant", "rep"], keep="last")
    df.to_csv(os.path.join(xc.COMMON, "baselines.csv"), index=False)
    g = df.groupby(["instance", "method"]).agg(n=("p100", "size"), p100_mean=("p100", "mean"),
                                                p100_sd=("p100", lambda v: v.std(ddof=1) if len(v) > 1 else np.nan),
                                                wr_min=("wr", "min"), wr_max=("wr", "max"),
                                                all_matched=("matched", "all")).reset_index()
    g.to_csv(os.path.join(xc.COMMON, "baselines_summary.csv"), index=False)
    pd.set_option("display.width", 200)
    print(g.round(3).to_string(index=False))
    return g


if __name__ == "__main__":
    main()
