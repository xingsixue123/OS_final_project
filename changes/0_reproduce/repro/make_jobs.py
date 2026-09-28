"""Build job lists from the authors' own commands in results_release.csv.gz.

  python repro/make_jobs.py                          # fig9 set: Region7+Region6, sample 0
  python repro/make_jobs.py --samples 0 0.1 ... 0.9   # multi-sample (needs setup/02_data.sh --samples10)
  python repro/make_jobs.py --traces 20230325/Region5

Writes work/jobs/<set>.jsonl. Every CSV row that makes up a Fig 9 bar for the chosen
(trace, sample) cells becomes one job, so each run is replicated 1:1 against the authors' row.
Also writes work/jobs/smoke.jsonl: the README "simple experiment" (Region1, RejectX + Baleen).
"""
import argparse
import json
import os

import common as C

# README "Do a simple experiment" commands, verbatim (paths are relative to work/).
README_SMOKE = [
    {"job_id": "readme_rejectx", "policy": "RejectX", "train_args": None,
     "sim_args": ["--config", "../baleen_code/runs/example/rejectx/config.json"]},
    {"job_id": "readme_baleen", "policy": "Baleen",
     "train_args": ("--exp example --policy PolicyUtilityServiceTimeSize2 --region Region1 --sample-ratio 0.1 "
                    "--sample-start 0 --trace-group 201910 --supplied-ea physical --target-wrs 34 50 100 75 20 10 60 90 30 "
                    "--target-csizes 366.475 --output-base-dir runs/example/baleen --eviction-age 5892.856 "
                    "--rl-init-kwargs filter_=prefetch --train-target-wr 35.599 --train-models admit prefetch "
                    "--train-split-secs-start 0 --train-split-secs-end 86400 --ap-acc-cutoff 15 "
                    "--ap-feat-subset meta+block+chunk").split(),
     "sim_args": ["--config", "../baleen_code/runs/example/baleen/prefetch_ml-on-partial-hit/config.json"]},
]


def check_fig9(dfc):
    """Our row selection must reproduce the Fig 9 bars (sampleright: mean per sample, then mean)."""
    print("Fig 9 check (0.1% traces; notebook values: R4 54.88/66.07/67.83, R5 33.37/36.48/41.46, "
          "R6 38.87/40.84/46.46, R7 37.21/39.08/46.12)")
    for trace in ['202110/Region4', '20230325/Region5', '20230325/Region6', '20230325/Region7']:
        vals = [C.select_rows(dfc, trace, p).groupby("SampleStart")[C.Y].mean().mean() for p in C.POLICIES]
        print(f"  {trace:18s} Baleen[{C.best_baleen_prefetch(dfc, trace)}]={vals[0]:.2f} "
              f"RejectX={vals[1]:.2f} CoinFlip={vals[2]:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traces", nargs="+", default=C.DEFAULT_TRACES)
    ap.add_argument("--samples", nargs="+", type=float, default=[0.0])
    ap.add_argument("--set", default="fig9")
    args = ap.parse_args()

    dfc = C.canonical(C.load_csv())
    check_fig9(dfc)

    jobs = []
    for trace in args.traces:
        for pol in C.POLICIES:
            rows = C.select_rows(dfc, trace, pol)
            rows = rows[rows["SampleStart"].isin(args.samples)]
            if rows.empty:
                print(f"  WARNING: no author rows for {trace} {pol} samples={args.samples}")
            for _, row in rows.iterrows():
                jobs.append(C.make_job(row))

    ids = [j["job_id"] for j in jobs]
    assert len(ids) == len(set(ids)), "duplicate job ids"
    os.makedirs(C.JOBS_DIR, exist_ok=True)
    with open(os.path.join(C.JOBS_DIR, f"{args.set}.jsonl"), "w") as f:
        for j in jobs:
            f.write(json.dumps(j) + "\n")
    with open(os.path.join(C.JOBS_DIR, "smoke.jsonl"), "w") as f:
        for j in README_SMOKE:
            f.write(json.dumps(j) + "\n")

    print(f"\n{len(jobs)} jobs -> work/jobs/{args.set}.jsonl")
    for j in jobs:
        print(f"  {j['job_id']:70s} author peak={j['author'][C.Y]:.2f}")
    print(f"{len(README_SMOKE)} jobs -> work/jobs/smoke.jsonl")


if __name__ == "__main__":
    main()
