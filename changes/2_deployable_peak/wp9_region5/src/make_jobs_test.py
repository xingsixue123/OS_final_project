"""WP9 (Track D) jobs: the authors' per-sample commands from results_release.csv.gz for Region5 (20230325, 0.1%)
x samples 0 (pipeline dry run only) and 0.1-0.6 (H4 test) -> wp9_region5/jobs.json. The reserve samples 0.7-0.9 are
NEVER built (assert below). Copied from wp3_test/src/make_jobs_test.py; WP9 changes: region/samples/Fig 9 variant.
 Logic copied from explore/common/src/make_jobs.py (phase 1), using a
COPY of 0_reproduce/repro/common.py (src/rc_common.py, unmodified; only RESULTS_CSV is pointed at the read-only data
symlink) for the canonical Fig 9 row selection and the path rewrite (--exp/--output-base-dir/-o/--job-id; trace path
-> data/tectonic/...; + --eviction-policy LRU; - --offline-ap-decisions; train-output flags -> {TRAIN:<key>}).
Per instance: baleen (Fig 9 prefetch variant: Region5 ML-Range on Partial Hit, experiment 20230421_alltraces_pfalways), rejectx/coinflip
(static_pf = primary, tracedrop = secondary), opt (OPT AP row: EA etc., recorded for reference only).
  cd wp9_region5 && $BALEEN_PY -B src/make_jobs_test.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rc_common as RC  # noqa: E402

W = os.path.dirname(HERE)
RC.RESULTS_CSV = os.path.join(W, "work", "data", "results_release.csv.gz")
SAMPLES = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]     # s0 = dry run; 0.1-0.6 = test; 0.7-0.9 = reserve, never built
assert all(s < 0.65 for s in SAMPLES)
TRACES = {"Region5": "20230325/Region5"}
FIG9_PF = {"Region5": "ML-Range on Partial Hit"}
FIG9_EXP = "20230421_alltraces_pfalways"


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
            assert J["baleen"]["experiment"] == FIG9_EXP, (key, J["baleen"]["experiment"])
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
                  J["baleen"]["author"]["AP Threshold"], "| opt EA", J["opt"]["ea"], "|",
                  sorted(k for k in J if k.startswith(("rejectx", "coinflip"))), flush=True)
    json.dump(jobs, open(os.path.join(W, "jobs.json"), "w"), indent=1, default=float)
    # cross-check against WP1's independent OPT-row extraction (same CSV)
    wp1 = json.load(open(os.path.join(W, "..", "wp1_offline", "jobs.json")))["jobs"]
    for k, J in jobs.items():
        assert abs(wp1[k]["ea"] - J["opt"]["ea"]) < 1e-6, (k, wp1[k]["ea"], J["opt"]["ea"])
    print("-> jobs.json; OPT EAs equal WP1's for all", len(jobs), "instances")


if __name__ == "__main__":
    main()
