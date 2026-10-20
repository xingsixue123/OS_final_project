"""AR: the authors' per-sample commands for test pool T1 = Region2 (201910, 0.1%) samples 0.1-0.6 -> jobs_test.json.
Copied from wp10_schedule/src/make_jobs_test.py (same rc_common.make_job path rewrite, + --eviction-policy LRU,
- --offline-ap-decisions, train outputs -> {TRAIN:<key>}). Reads command rows only (no metric column is used).

Missing release rows (pool-choice rule, result/LAB_NOTEBOOK.md 2026-10-20 01:08: constructed mechanically by
sample-start substitution in the same region's commands): the template is the row of the nearest sample of the same
(policy, prefetch variant, experiment) with a row (ties -> lower sample); every occurrence of the template's sample
start in the TrainCommand / ReproduceCommand (--sample-start, --suffix, trace path, output dirs) is replaced by the
target's. The template's --eviction-age and authors' threshold/probability are kept (the threshold/probability is
re-converged anyway). Constructed rows are flagged constructed_from.
Region2 lacks: Baleen Fig 9 s0.2; RejectX 20230410_static_pf s0.1, s0.2.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rc_common as RC  # noqa: E402

W = os.path.dirname(HERE)
RC.RESULTS_CSV = os.path.join(W, "work", "data", "results_release.csv.gz")
OUTF = os.path.join(W, "jobs_test.json")
POOL = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
TEMPLATE_SAMPLES = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6]   # rows usable as templates (never above 0.6)
TRACE = "201910/Region2"
REGION = "Region2"


def substitute(row, s_from, s_to):
    r = row.copy()
    a, b = f"{s_from:g}", f"{s_to:g}"
    for col in ("TrainCommand", "ReproduceCommand"):
        c = r[col]
        c = re.sub(r"--sample-start\s+\S+", f"--sample-start {b}", c)
        c = c.replace(f"{REGION}_{a}_0.1", f"{REGION}_{b}_0.1")
        c = c.replace(f"full_{a}_0.1", f"full_{b}_0.1")
        r[col] = c
    r["SampleStart"] = s_to
    return r


def pick(rows, s, key):
    have = {float(x): rows[rows.SampleStart == x].iloc[0] for x in TEMPLATE_SAMPLES if (rows.SampleStart == x).sum() == 1}
    if s in have:
        return have[s], None
    t = min(have, key=lambda x: (round(abs(x - s), 6), x))       # ties -> lower sample (rounded: float noise)
    r = substitute(have[t], t, s)
    assert f"--sample-start {s:g}" in r["TrainCommand"] and f"full_{s:g}_0.1" in r["ReproduceCommand"], (key, s)
    return r, t


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
        r, t = pick(b, s, key)
        J["baleen"] = RC.make_job(r)
        J["baleen"]["constructed_from"] = t
        J["baleen"]["author"] = {}                      # no authors' outcome is carried into the test jobs
        for pol in ["RejectX", "CoinFlip"]:
            rows = RC.select_rows(dfc, TRACE, pol)
            rows = rows[rows.ExperimentName == "20230410_static_pf"]
            r, t = pick(rows, s, key)
            j = RC.make_job(r)
            j["constructed_from"] = t
            j["author_probability"] = float(RC.get_flag(j["sim_args"], "--ap-probability"))
            j["author"] = {}
            J[f"{pol.lower()}_static"] = j
        J["region"] = REGION
        J["sample"] = s
        J["ea_ml"] = float(RC.get_flag(J["baleen"]["train_args"], "--eviction-age"))
        jobs[key] = J
        print(key, "baleen", J["baleen"]["job_id"], "from", J["baleen"]["constructed_from"], "EA", J["ea_ml"],
              "| rejectx from", J["rejectx_static"]["constructed_from"], "| coinflip from",
              J["coinflip_static"]["constructed_from"], flush=True)
    json.dump(jobs, open(OUTF, "w"), indent=1, default=float)
    print("-> jobs_test.json:", len(jobs), "instances (T1 = Region2 s0.1-0.6)")


if __name__ == "__main__":
    main()
