"""Authors' per-sample commands (results_release.csv.gz) for the dev + held-out instances -> common/jobs.json.

Uses 0_reproduce/repro/common.py (imported read-only) for the canonical Fig 9 row selection and the path rewrite
(--exp/--output-base-dir/-o/--job-id; trace path -> data/tectonic/...; + --eviction-policy LRU; - --offline-ap-decisions;
train-output flags -> {TRAIN:<key>} placeholders), exactly as 0_reproduce and harness_eval did.

Per (region, sample):
  baleen   : Fig 9 prefetch variant (Region7 ML-Range on ML-When, Region6 All on Partial Hit; authors' tracedrop rows)
  rejectx / coinflip : ShortLabel rows (20230410_static_pf = primary, 20230327_tracedrop_* = secondary)
  opt      : 'OPT AP', Prefetching 'OPT-Range on OPT-Ep-Start', Target DWPD 7.5, 366.47 GB (authors' tracedrop rows):
             EA (the OPT's converged eviction age) + AP threshold hint + the authors' sim command
"""
import json
import os
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import xc  # noqa: E402

sys.path.insert(0, os.path.join(xc.REPRO, "repro"))
import common as RC  # noqa: E402  (0_reproduce/repro/common.py, read-only)

RC.RESULTS_CSV = os.path.join(xc.COMMON, "data", "results_release.csv.gz")
SAMPLES = [0.0, 0.1, 0.2, 0.3]
TRACES = {"Region7": "20230325/Region7", "Region6": "20230325/Region6"}
FIG9_PF = {"Region7": "ML-Range on ML-When", "Region6": "All on Partial Hit"}


def main():
    df = RC.load_csv()
    dfc = RC.canonical(df)
    jobs = {}
    for region, trace in TRACES.items():
        assert RC.best_baleen_prefetch(dfc, trace) == FIG9_PF[region]
        for s in SAMPLES:
            key = f"{region}_s{s:g}"
            J = {}
            rows = RC.select_rows(dfc, trace, "Baleen")
            rows = rows[rows.SampleStart == s]
            assert len(rows) == 1, (key, len(rows))
            J["baleen"] = RC.make_job(rows.iloc[0])
            for pol in ["RejectX", "CoinFlip"]:
                rows = RC.select_rows(dfc, trace, pol)
                rows = rows[rows.SampleStart == s]
                for _, r in rows.iterrows():
                    tag = "static" if r["ExperimentName"] == "20230410_static_pf" else "tracedrop"
                    J[f"{pol.lower()}_{tag}"] = RC.make_job(r)
            d = df[(df.Trace == trace) & (df.SampleRatio == 0.1) & (df.SampleStart == s)
                   & (df.Prefetching == "OPT-Range on OPT-Ep-Start") & (df["Target DWPD"] == 7.5)
                   & (df["Target Cache Size"].round(2) == 366.47) & (df.AdmissionPolicyLabel == "OPT AP")]
            assert len(d) == 1, (key, len(d))
            r = d.iloc[0]
            sim = RC._module_args(r["ReproduceCommand"], RC.SIM_MOD)
            tr = RC._module_args(r["TrainCommand"], RC.TRAIN_MOD)
            J["opt"] = dict(ea=float(RC.get_flag(tr, "--eviction-age")), author_th=float(RC.get_flag(sim, "--ap-threshold")),
                            author_wr=float(r["Write Rate (MB/s)"]), author_p100=float(r[RC.Y]),
                            experiment=r["ExperimentName"], author_train_cmd=r["TrainCommand"],
                            author_sim_cmd=r["ReproduceCommand"],
                            prefetch_when=RC.get_flag(sim, "--prefetch-when"),
                            prefetch_range=RC.get_flag(sim, "--prefetch-range"))
            J["region"] = region
            J["sample"] = s
            J["ea_ml"] = float(RC.get_flag(J["baleen"]["train_args"], "--eviction-age"))
            jobs[key] = J
            print(key, "baleen", J["baleen"]["job_id"], "EA_ml", J["ea_ml"], "author th",
                  J["baleen"]["author"]["AP Threshold"], "| opt EA", J["opt"]["ea"], "th", J["opt"]["author_th"],
                  "|", sorted(k for k in J if k.startswith(("rejectx", "coinflip"))))
    out = os.path.join(xc.COMMON, "jobs.json")
    json.dump(jobs, open(out, "w"), indent=1, default=float)
    print("->", out)


if __name__ == "__main__":
    main()
