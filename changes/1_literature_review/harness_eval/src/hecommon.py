"""Shared paths, sandboxed runners, train lock, result parsing and WR convergence for harness_eval.

Everything writes under H = harness_eval/. The frozen artifact (0_reproduce/baleen_code) and
0_reproduce/env are only read / executed. Runs happen with cwd = H/work, where
  H/work/BCacheSim -> ../../../0_reproduce/baleen_code/BCacheSim   (frozen, read-only)
  H/work/data      -> ../../../0_reproduce/work/data               (read-only)
and every Baleen process runs under bwrap with /tmp bound to H/work/systmp.
"""
import fcntl
import glob
import json
import lzma
import os
import pickle
import shlex
import subprocess
import threading
import time

import numpy as np

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(H, "work")
SRC = os.path.join(H, "src")
RESULTS = os.path.join(H, "results")
LOGS = os.path.join(WORK, "logs")
REPRO = os.path.normpath(os.path.join(H, "..", "..", "0_reproduce"))
BALEEN_PY = os.path.join(REPRO, "env", "bin", "python")
SOLVER_PY = os.path.normpath(os.path.join(H, "..", "ising_followup", "audit", "env", "bin", "python"))
SYSTMP = os.path.join(WORK, "systmp")
SANDBOX = ["bwrap", "--dev-bind", "/", "/", "--bind", SYSTMP, "/tmp", "--"]
TRAIN_MOD = "BCacheSim.episodic_analysis.train"
SIM_MOD = "BCacheSim.cachesim.simulate_ap"
TARGET_WR = 35.599
TOL = 0.01
LOG_INTERVAL = 600
SKIP_WINDOWS = 86400 // LOG_INTERVAL

# Authors' settings (sample 0). Offline (OPT) mode = the authors' "OPT-Range on OPT-Ep-Start" OPT AP
# rows (20230327_tracedrop_*), which use filter_=prefetch episodes at the OPT's own converged eviction
# age; deployed mode = the Fig 9 Baleen jobs (0_reproduce/work/jobs/fig9.jsonl).
TRACES = {
    "Region7": dict(ea_opt=4442.942, ea_ml=5653.153, ml_job="20230325_Region7_s0_baleen_20230327_tracedrop_XX",
                    opt_author_th=29.3777),
    "Region6": dict(ea_opt=3848.741, ea_ml=4669.873, ml_job="20230325_Region6_s0_baleen_20230327_tracedrop_old",
                    opt_author_th=27.4728),
}


def trace_path(region):
    return f"data/tectonic/20230325/{region}/full_0_0.1.trace"


def base_env(extra=None, threads=2):
    e = dict(os.environ)
    assert e.get("HE_ROOT") == H, "source harness_eval/env.sh first"
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"]:
        e[k] = str(threads)
    e["PYTHONPATH"] = SRC + ":" + WORK
    # LightGBM's hard-coded num_threads=20 + OpenMP busy-waiting stalls under CPU sharing; passive waiting
    # changes only the OpenMP runtime's idle behaviour (no model / parameter change).
    e["OMP_WAIT_POLICY"] = "PASSIVE"
    if extra:
        e.update(extra)
    return e


def run_logged(args, log_path, env=None, cwd=WORK):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    t0 = time.time()
    with open(log_path, "w") as log:
        log.write("$ cd " + cwd + " && " + " ".join(shlex.quote(a) for a in SANDBOX + args) + "\n\n")
        log.flush()
        rc = subprocess.call(SANDBOX + args, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                             env=env or base_env())
    return rc, time.time() - t0


_TLOCK = threading.Lock()


class SimSlot:
    """Cross-process cap on concurrent simulations: one of K flock'ed slot files, K read from
    H/work/.sim_slots at every acquisition (default 16) so it can be changed while runs are in flight."""
    def __enter__(self):
        d = os.path.join(WORK, ".sim_slots.d")
        os.makedirs(d, exist_ok=True)
        while True:
            try:
                k = int(open(os.path.join(WORK, ".sim_slots")).read().strip())
            except Exception:
                k = 16
            for i in range(k):
                f = open(os.path.join(d, f"slot_{i}"), "w")
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.f = f
                    return self
                except OSError:
                    f.close()
            time.sleep(5)

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


class TrainLock:
    """Serialize every `train` invocation (LightGBM num_threads=20 is hard-coded)."""
    def __enter__(self):
        _TLOCK.acquire()
        self.f = open(os.path.join(WORK, ".train.lock"), "w")
        fcntl.flock(self.f, fcntl.LOCK_EX)

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()
        _TLOCK.release()


TRAIN_LOCK = TrainLock()


def parse_train_outputs(log_path):
    lines = open(log_path).read().splitlines()
    if "Filenames generated:" not in lines:
        return None
    out = {}
    for line in lines[lines.index("Filenames generated:") + 1:]:
        parts = line.split(" ")
        if len(parts) == 3 and not parts[0].startswith("+"):
            out[parts[0]] = (parts[1], parts[2])
    return out


def set_flag(args, flag, value):
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


def load_fig9_job(job_id):
    with open(os.path.join(REPRO, "work", "jobs", "fig9.jsonl")) as f:
        for line in f:
            j = json.loads(line)
            if j["job_id"] == job_id:
                return j
    raise KeyError(job_id)


# ------------------------------------------------------------------ results
def load_result(result_file):
    import compress_json  # Baleen env only
    return compress_json.load(result_file)


def result_file_in(out_dir):
    res = sorted(glob.glob(os.path.join(WORK, out_dir, "**", "*_cache_perf.txt.lzma"), recursive=True))
    return res


def window_series(result_file):
    """Per-window simulated DT (GET, used) and no-cache DT from the .stats.lzma next to the result.
    Returns dict with arrays over ALL windows (index 0 = first 10-min window of the trace)."""
    stats_f = result_file.replace("_cache_perf.txt.lzma", "_cache_perf.txt.stats.lzma")
    if not os.path.exists(stats_f):
        cands = glob.glob(os.path.join(os.path.dirname(result_file), "*.stats*lzma"))
        stats_f = cands[0]
    import compress_json
    st = compress_json.load(stats_f)
    b = st["batches"] if "batches" in st else st["stats"]["batches"]
    used = np.diff(np.asarray(b["service_time_used_stats"], float), prepend=0)
    noc = np.diff(np.asarray(b["service_time_nocache_stats"], float), prepend=0)
    tphy = np.asarray(b["time_phy"], float)
    return dict(used=used, nocache=noc, time_phy=tphy)


def metrics(result_file):
    """P100 (== PeakServiceTimeUtil1), P99, top-5 mean, mean DT (utilisation %, windows after day 1)."""
    r = load_result(result_file)["results"]
    ws = window_series(result_file)
    used = ws["used"][SKIP_WINDOWS:]
    scale = r["PeakServiceTimeUtil1"] / used.max()   # st_to_util(.)*100 for 600 s windows
    top5 = np.sort(used)[::-1][:5]
    return dict(wr=r["FlashWriteRate"], p100=r["PeakServiceTimeUtil1"], p99=float(np.percentile(used, 99) * scale),
                top5=float(top5.mean() * scale), mean_dt=float(used.mean() * scale),
                argmax=int(np.argmax(used)) + SKIP_WINDOWS, scale=float(scale),
                top5_windows=[int(x) + SKIP_WINDOWS for x in np.argsort(used)[::-1][:5]])


# ------------------------------------------------------------------ convergence (copied logic of
# 0_reproduce/repro/converge.py::converge_loop, with outputs under H/work)
def sim_at(tag, base_args, th, log_dir, out_root, threads=2):
    ttag = f"th_{th:.6f}"
    out = f"{out_root}/{ttag}"
    args = set_flag(list(base_args), "--ap-threshold", f"{th:.6f}")
    args = set_flag(args, "-o", out)
    args = set_flag(args, "--job-id", f"{tag}__{ttag}".replace("/", "__"))
    done = result_file_in(out)
    if not done:
        with SimSlot():
            done = result_file_in(out)
            if not done:
                rc, dt = run_logged(        [BALEEN_PY, "-B", "-m", SIM_MOD] + args, os.path.join(log_dir, f"{ttag}.log"),
                                    env=base_env(threads=threads))
                if rc != 0:
                    return {"threshold": th, "error": f"rc={rc}", "log": os.path.join(log_dir, f"{ttag}.log")}
                done = result_file_in(out)
                log = open(os.path.join(log_dir, f"{ttag}.log")).read()
                for p in ["Failed to load", "Bad file", "Traceback (most recent call last)"]:
                    if p in log:
                        return {"threshold": th, "error": f"soft-fail {p}", "log": os.path.join(log_dir, f"{ttag}.log")}
    r = load_result(done[0])["results"]
    return {"threshold": th, "wr": r["FlashWriteRate"], "peak": r["PeakServiceTimeUtil1"],
            "result_file": done[0]}


def converge_loop(tag, base, seeds, pool, log_dir, out_root, step, increasing, lo_bound=0.0, hi_bound=1.0,
                  max_rounds=6, target=TARGET_WR):
    """Inner loop on --ap-threshold until WR within TOL of target. Same rules as
    0_reproduce/repro/converge.py (bracket -> secant + 3-point grid of +-d/4; else step outward),
    generalized to both directions: `increasing`=True for --ap opt (cutoff in MB/s; higher -> more
    admits), False for --ap mlnew (probability; higher -> fewer admits)."""
    tried = list(pool.map(lambda t: sim_at(tag, base, t, log_dir, out_root), seeds))
    best = None
    grid = []
    for rnd in range(max_rounds):
        grid = [t for t in grid if lo_bound < t < hi_bound and all(abs(t - x["threshold"]) > 1e-6 for x in tried)]
        tried += list(pool.map(lambda t: sim_at(tag, base, t, log_dir, out_root), grid))
        ok = [x for x in tried if x.get("wr") is not None]
        if not ok:
            raise RuntimeError(f"{tag}: all sims failed: {tried}")
        best = min(ok, key=lambda x: abs(x["wr"] - target))
        print(f"[{tag}] round {rnd}: best th={best['threshold']:.5f} WR={best['wr']:.3f} peak={best['peak']:.3f}",
              flush=True)
        if abs(best["wr"] - target) / target <= TOL:
            break
        above = [x for x in ok if x["wr"] > target]
        below = [x for x in ok if x["wr"] < target]
        if above and below:
            a = min(above, key=lambda x: x["wr"])     # closest from above
            b = max(below, key=lambda x: x["wr"])     # closest from below
            t = a["threshold"] + (a["wr"] - target) * (b["threshold"] - a["threshold"]) / (a["wr"] - b["wr"])
            d = abs(b["threshold"] - a["threshold"]) / 4
            grid = [round(t - d, 6), round(t, 6), round(t + d, 6)]
        else:
            # No bracket yet. converge.py steps outward by a fixed +-step; when the WR is far from the
            # target (e.g. a GBM trained on different labels) that needs many rounds, so extrapolate with the
            # secant through the two points closest to the target when its slope has the expected sign,
            # else step outward with doubling steps.
            up = (best["wr"] < target) == increasing
            st = abs(step) if up else -abs(step)
            edge = max(ok, key=lambda x: x["threshold"]) if st > 0 else min(ok, key=lambda x: x["threshold"])
            two = sorted(ok, key=lambda x: abs(x["wr"] - target))
            two = [two[0]] + [x for x in two[1:] if abs(x["threshold"] - two[0]["threshold"]) > 1e-9][:1]
            slope = None
            if len(two) == 2:
                slope = (two[1]["wr"] - two[0]["wr"]) / (two[1]["threshold"] - two[0]["threshold"])
                if (slope > 0) != increasing or abs(slope) < 1e-9:
                    slope = None
            if slope is not None:
                t = two[0]["threshold"] + (target - two[0]["wr"]) / slope
                t = min(max(t, edge["threshold"] + st), edge["threshold"] + 12 * st) if st > 0 else \
                    max(min(t, edge["threshold"] + st), edge["threshold"] + 12 * st)
                d = max(abs(step) / 2, abs(t - two[0]["threshold"]) * 0.15)
                grid = [round(t - d, 6), round(t, 6), round(t + d, 6)]
            else:
                grid = [round(edge["threshold"] + st * k, 6) for k in (1, 2, 4)]
    return tried, best


def remove_flag_nargs(args, flag):
    """Drop `flag v1 v2 ...` (all values up to the next --option)."""
    out, i = [], 0
    while i < len(args):
        if args[i] == flag:
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                i += 1
        else:
            out.append(args[i])
            i += 1
    return out
