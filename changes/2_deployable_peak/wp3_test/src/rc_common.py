"""Shared paths, target selection and command rewriting for the Baleen reproduction.

Target selection mirrors notebooks/includes/common-20230414.ipynb::get_data/add_pfbest
(the code behind Fig 9): canonical experiments, Target DWPD 7.5, 366.47 GB cache,
PracticalAP; baselines = ShortLabel RejectX/CoinFlip (no prefetch); Baleen = the prefetch
option with the lowest mean peak load on that trace.
"""
import json
import os
import re
import shlex

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, "work")
CODE = os.path.join(ROOT, "baleen_code")
PY = os.path.join(ROOT, "env", "bin", "python")
RESULTS_CSV = os.path.join(WORK, "data", "results_release.csv.gz")
JOBS_DIR = os.path.join(WORK, "jobs")
LOGS_DIR = os.path.join(WORK, "logs")

Y = "P100ServiceTimeUtil@10m"          # Fig 9 metric: peak backend load (%), 10-min windows
TARGET_WR = 35.599                     # MB/s, == "Target DWPD 7.5" in the release CSV
FIG9_TRACES = ['201910/Region1', '201910/Region3', '201910/Region2', '202110/Region4',
               '20230325/Region7', '20230325/Region6', '20230325/Region5']
DEFAULT_TRACES = ['20230325/Region7', '20230325/Region6']
POLICIES = ['Baleen', 'RejectX', 'CoinFlip']

# BCacheSim/cachesim/utils.py:29 hard-codes a trace-stats cache at /tmp/cache-sim-accesses-*.
# Every job runs in a bubblewrap mount namespace where /tmp is work/systmp, so nothing is
# written to the real /tmp and the frozen code stays untouched.
SYSTMP = os.path.join(WORK, "systmp")
SANDBOX = ["bwrap", "--dev-bind", "/", "/", "--bind", SYSTMP, "/tmp", "--"]

TRAIN_MOD = "BCacheSim.episodic_analysis.train"
SIM_MOD = "BCacheSim.cachesim.simulate_ap"


def load_csv():
    import pandas as pd
    df = pd.read_csv(RESULTS_CSV, low_memory=False)
    df["TraceGroup"] = df["TraceGroup"].astype(str)
    return df


def canonical(df, sample_ratio=0.1):
    """Rows eligible for Fig 9 at the default operating point."""
    return df[(df["CanonExp"] == True) & (df["DWPDNotFar"] == True)
              & (df["Target Cache Size"].round(2) == 366.47)
              & (df["Target DWPD"] == 7.5) & (df["PracticalAP"] == True)
              & (df["SampleRatio"] == sample_ratio) & (df["Trace"].isin(FIG9_TRACES))]


def best_baleen_prefetch(dfc, trace):
    """add_pfbest(): Baleen prefetch option with min mean peak load over all rows of the trace."""
    d = dfc[(dfc["Trace"] == trace) & (dfc["AdmissionPolicyLabel"] == "Baleen")]
    return d.groupby("Prefetching")[Y].mean().idxmin()


def select_rows(dfc, trace, policy):
    """All CSV rows making up one Fig 9 bar (trace, policy), any sample."""
    d = dfc[dfc["Trace"] == trace]
    if policy == "Baleen":
        return d[(d["AdmissionPolicyLabel"] == "Baleen")
                 & (d["Prefetching"] == best_baleen_prefetch(dfc, trace))]
    return d[d["ShortLabel"] == policy]


# ---------------------------------------------------------------- command rewriting
def _module_args(cmd, module):
    toks = shlex.split(cmd)
    i = toks.index(module)
    return toks[i + 1:]


def set_flag(args, flag, value):
    """Replace the value of every occurrence of `flag` (commands repeat some flags)."""
    out, i, seen = [], 0, False
    while i < len(args):
        if args[i] == flag:
            out += [flag, value]
            i += 2
            seen = True
        else:
            out.append(args[i])
            i += 1
    if not seen:
        out += [flag, value]
    return out


def remove_flag(args, flag):
    """Drop every `flag value` pair."""
    out, i = [], 0
    while i < len(args):
        if args[i] == flag:
            i += 2
        else:
            out.append(args[i])
            i += 1
    return out


def get_flag(args, flag):
    return args[args.index(flag) + 1] if flag in args else None


def trace_path(trace_group, region, sample_start, sample_ratio=0.1):
    """local_cluster.tracefilename() layout #3, relative to work/."""
    return f"data/tectonic/{trace_group}/{region}/full_{sample_start:g}_{sample_ratio:g}.trace"


# Sim flags whose values are files produced by the train step (key in train's `filenames`).
TRAIN_OUTPUT_FLAGS = {
    "--ep-analysis": "analysis",
    "--learned-ap-model-path": "model_admit_threshold_binary",
    "--prefetcher-model-path": "model_prefetch_offset_start",   # -> *_prefetch_{k}.model
}


def make_job(row):
    """Turn one authors' CSV row into a self-contained job spec (paths relative to work/)."""
    region, tg, start = row["Region"], str(row["TraceGroup"]), float(row["SampleStart"])
    short = {"Baleen": "baleen", "RejectX": "rejectx", "CoinFlip": "coinflip"}[row["AdmissionPolicyLabel"]]
    job_id = f"{tg}_{region}_s{start:g}_{short}_{row['ExperimentName']}"
    job_id = re.sub(r"[^A-Za-z0-9_.+-]", "_", job_id)
    base = f"runs/repro/{job_id}"

    train = _module_args(row["TrainCommand"], TRAIN_MOD)
    train = set_flag(train, "--exp", job_id)                 # isolate tmp/<exp>/... per job
    train = set_flag(train, "--output-base-dir", f"{base}/train")

    sim = _module_args(row["ReproduceCommand"], SIM_MOD)
    sim = set_flag(sim, "--trace", trace_path(tg, region, start, float(row["SampleRatio"])))
    sim = set_flag(sim, "-o", f"{base}/sim")
    sim = set_flag(sim, "--job-id", job_id)
    # The authors' commands predate --eviction-policy; in the frozen simulator its default is
    # None, which crashes (eviction_policies.py:682). Use the row's recorded policy (LRU, as in
    # the paper and the README configs).
    deviations = []
    if "--eviction-policy" not in sim:
        sim = set_flag(sim, "--eviction-policy", row["EvictionPolicy"])
        deviations.append(f"added --eviction-policy {row['EvictionPolicy']} (flag absent in authors' "
                          "command; frozen simulator default None crashes)")
    # The authors' --offline-ap-decisions pointed at a full-trace decisions file from a separate
    # analysis pass; train.py (split 0-86400s) only covers day-1 blocks, so the per-access
    # lookup (ep_helpers.py:66) raises KeyError on test days. For rejectx/coinflip/mlnew with
    # size_opt=access, LRU and acctime-* prefetch, loaded episodes only feed diagnostic counters,
    # never admission/eviction/prefetch -- the README example configs omit the flag too.
    if "--offline-ap-decisions" in sim:
        sim = remove_flag(sim, "--offline-ap-decisions")
        deviations.append("dropped --offline-ap-decisions (diagnostic-only here; as in README configs)")
    for flag, key in TRAIN_OUTPUT_FLAGS.items():
        if flag in sim:
            sim = set_flag(sim, flag, "{TRAIN:" + key + "}")

    return {
        "job_id": job_id,
        "trace": row["Trace"], "region": region, "trace_group": tg,
        "sample_ratio": float(row["SampleRatio"]), "sample_start": start,
        "policy": row["AdmissionPolicyLabel"], "prefetching": row["Prefetching"],
        "experiment": row["ExperimentName"],
        "author": {Y: row[Y], "P50ServiceTimeUtil@10m": row["P50ServiceTimeUtil@10m"],
                   "Write Rate (MB/s)": row["Write Rate (MB/s)"],
                   "IOPSMissRatio": row["IOPSMissRatio"], "BandwidthMissRatio": row["BandwidthMissRatio"],
                   "AP Threshold": row.get("AP Threshold"), "AP Probability": row.get("AP Probability")},
        "author_train_cmd": row["TrainCommand"],
        "author_sim_cmd": row["ReproduceCommand"],
        "train_args": train,
        "sim_args": sim,
        "base": base,
        "deviations": deviations,
    }


def load_jobs(set_name):
    path = os.path.join(JOBS_DIR, f"{set_name}.jsonl")
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]
