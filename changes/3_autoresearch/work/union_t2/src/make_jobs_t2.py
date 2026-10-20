"""AR: the authors' per-sample commands for test pool T2 = Region4 (202110, 0.1%) samples 0.2-0.6 -> jobs_test.json.
Copied from src/make_jobs_t1.py (same rc_common.make_job path rewrite). Second-spend rule (result/LAB_NOTEBOOK.md,
2026-10-20 04:56): Fig 9 Baleen rows + the authors' RejectX/CoinFlip rows of experiment 20230412_XX_rerun2 (the only
static rows Region4 has). Reads command rows only; no authors' outcome is carried into the jobs.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rc_common as RC  # noqa: E402

W = os.path.dirname(HERE)
RC.RESULTS_CSV = os.path.join(W, "work", "data", "results_release.csv.gz")
OUTF = os.path.join(W, "jobs_test.json")
POOL = [0.2, 0.3, 0.4, 0.5, 0.6]
TRACE = "202110/Region4"
REGION = "Region4"
STATIC_EXP = "20230412_XX_rerun2"


def main():
    df = RC.load_csv()
    dfc = RC.canonical(df)
    pf = RC.best_baleen_prefetch(dfc, TRACE)
    assert pf == "All on Partial Hit", pf
    jobs = {}
    for s in POOL:
        key = f"{REGION}_s{s:g}"
        J = {}
        b = RC.select_rows(dfc, TRACE, "Baleen")
        b = b[b.SampleStart == s]
        assert len(b) == 1, (key, len(b))
        J["baleen"] = RC.make_job(b.iloc[0])
        J["baleen"]["constructed_from"] = None
        J["baleen"]["author"] = {}
        for pol in ["RejectX", "CoinFlip"]:
            rows = RC.select_rows(dfc, TRACE, pol)
            rows = rows[(rows.ExperimentName == STATIC_EXP) & (rows.SampleStart == s)]
            assert len(rows) == 1, (key, pol, len(rows))
            j = RC.make_job(rows.iloc[0])
            j["constructed_from"] = None
            j["author_probability"] = float(RC.get_flag(j["sim_args"], "--ap-probability"))
            j["author"] = {}
            J[f"{pol.lower()}_static"] = j
        J["region"] = REGION
        J["sample"] = s
        J["ea_ml"] = float(RC.get_flag(J["baleen"]["train_args"], "--eviction-age"))
        jobs[key] = J
        print(key, J["baleen"]["job_id"], "EA", J["ea_ml"], "| rejectx", J["rejectx_static"]["job_id"],
              J["rejectx_static"]["author_probability"], "| coinflip", J["coinflip_static"]["author_probability"], flush=True)
    json.dump(jobs, open(OUTF, "w"), indent=1, default=float)
    print("-> jobs_test.json:", len(jobs), "instances (T2 = Region4 s0.2-0.6)")


if __name__ == "__main__":
    main()
