"""WP1 instance list: the authors' OPT-AP rows (results_release.csv.gz) for Regions 4-7 x samples 0-0.9 -> jobs.json.
Same row selection as phase-1 explore/common/src/make_jobs.py ('OPT AP', 'OPT-Range on OPT-Ep-Start', Target DWPD 7.5,
366.47 GB, SampleRatio 0.1): EA = the OPT's converged eviction age (train cmd), author threshold / WR / P100 (sim cmd).
Run with the Baleen env (pandas)."""
import json
import os
import shlex

HERE = os.path.dirname(os.path.abspath(__file__))
WP1 = os.path.dirname(HERE)
CSV = "/home/sxing/project/OS_final_project/changes/1_literature_review/explore/common/data/results_release.csv.gz"
TRACES = {"Region4": "202110/Region4", "Region5": "20230325/Region5", "Region6": "20230325/Region6",
          "Region7": "20230325/Region7"}
SAMPLES = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]


def margs(cmd, module):
    t = shlex.split(cmd)
    return t[t.index(module) + 1:]


def get(a, f):
    return a[a.index(f) + 1] if f in a else None


def main():
    import pandas as pd
    df = pd.read_csv(CSV, low_memory=False)
    jobs, missing = {}, []
    for region, trace in TRACES.items():
        for s in SAMPLES:
            d = df[(df.Trace == trace) & (df.SampleRatio == 0.1) & (df.SampleStart == s)
                   & (df.Prefetching == "OPT-Range on OPT-Ep-Start") & (df["Target DWPD"] == 7.5)
                   & (df["Target Cache Size"].round(2) == 366.47) & (df.AdmissionPolicyLabel == "OPT AP")]
            key = f"{region}_s{s:g}"
            if len(d) != 1:
                missing.append((key, len(d)))
                continue
            r = d.iloc[0]
            tr = margs(r["TrainCommand"], "BCacheSim.episodic_analysis.train")
            sim = margs(r["ReproduceCommand"], "BCacheSim.cachesim.simulate_ap")
            assert get(sim, "--prefetch-when") == "at_start" and get(sim, "--prefetch-range") == "acctime-episode"
            assert get(tr, "--rl-init-kwargs") == "filter_=prefetch" and get(tr, "--trace-group") == trace.split("/")[0]
            jobs[key] = dict(region=region, sample=s, group=trace.split("/")[0], ea=float(get(tr, "--eviction-age")),
                             author_th=float(get(sim, "--ap-threshold")), author_wr=float(r["Write Rate (MB/s)"]),
                             author_p100=float(r["P100ServiceTimeUtil@10m"]), experiment=r["ExperimentName"],
                             author_train_cmd=r["TrainCommand"], author_sim_cmd=r["ReproduceCommand"])
    json.dump(dict(jobs=jobs, missing=missing), open(os.path.join(WP1, "jobs.json"), "w"), indent=1)
    print(len(jobs), "instances; missing:", missing)


if __name__ == "__main__":
    main()
