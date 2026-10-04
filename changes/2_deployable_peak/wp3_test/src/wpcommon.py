"""Track A WP3 (test) shared infrastructure -- copied from wp2_deployed/src/wpcommon.py and adapted: configurable
jobs/instance/label sources (test by default; dev only for the plumbing dry run), a frozen work dir for the
RejectX/CoinFlip replays and instance dumps, the test instance list.

Original WP2 docstring:

Work dir wp2_deployed/work: BCacheSim -> ../../wp0_overlay/overlay/BCacheSim (the reviewed overlay), data -> explore
common/data (read-only). Every Baleen process: taskset -c <cpus> bwrap --dev-bind / / --bind <private job tmp> /tmp --
$BALEEN_PY -B ...   CPU policy (coordinator, 2026-10-01 16:22): while Track B's timing runs hold cores 0-7, Track A
uses logical CPUs 8-11,20-23 only and <= 6 concurrent sims; when 2_deployable_peak/TIMING_IDLE exists, CPUs 0-23 and up
to IDLE_SIMS sims (checked at every launch; running jobs are left to finish if the flag disappears).
Every train holds flock(2_deployable_peak/.train.lock) (shared with Track B).
"""
import fcntl
import glob
import json
import os
import shlex
import shutil
import subprocess
import threading
import time

import numpy as np

W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))           # wp3_test
P2 = os.path.dirname(W)
SRC = os.path.join(W, "src")
WORK = os.path.join(W, "work")                     # overlay (BCacheSim -> wp0_overlay/overlay)
WORK_FROZEN = os.path.join(W, "work_frozen")       # frozen artifact (BCacheSim -> 0_reproduce/baleen_code)
RESULTS = os.path.join(W, "results")
LOGS = os.path.join(W, "logs")
LABELS = os.path.join(W, "labels")
EXPLORE = os.path.normpath(os.path.join(P2, "..", "1_literature_review", "explore"))
COMMON = os.path.join(EXPLORE, "common")
REPRO = os.path.normpath(os.path.join(P2, "..", "0_reproduce"))
BALEEN_PY = os.path.join(REPRO, "env", "bin", "python")
SOLVER_PY = os.path.join(EXPLORE, "env", "bin", "python")
TRAIN_LOCK_FILE = os.path.join(P2, ".train.lock")
IDLE_FLAG = os.path.join(P2, "TIMING_IDLE")
BUSY_CPUS, IDLE_CPUS = "8-11,20-23", "0-23"
BUSY_SIMS, IDLE_SIMS = 6, 14
TARGET_WR = 35.599
TOL = 0.01
SKIP = 144
US = 1.0 / 36 * (100.0 / 0.1) / 600 * 100          # DT seconds per 600 s window -> utilisation %
DEV = [f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]
TEST = [f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0.4", "0.5", "0.6")]
TEST_JOBS = os.path.join(W, "jobs.json")
# configurable sources (configure()): test by default; the dev configuration exists ONLY for the plumbing dry run
JOBS = json.load(open(TEST_JOBS)) if os.path.exists(TEST_JOBS) else {}
INST_DIR = os.path.join(W, "inst")
TRIALS = os.path.join(W, "trials.csv")
RUNTAG = ""


def configure(mode):
    """mode 'test' (default) or 'dev_dryrun' (dev jobs/instances/labels of WP2, outputs under wp3_test/dryrun)."""
    global JOBS, INST_DIR, LABELS, TRIALS, RUNTAG, RESULTS
    if mode == "test":
        JOBS = json.load(open(TEST_JOBS))
        INST_DIR, LABELS, TRIALS, RUNTAG = os.path.join(W, "inst"), os.path.join(W, "labels"), os.path.join(W, "trials.csv"), ""
        RESULTS = os.path.join(W, "results")
    elif mode == "dev_dryrun":
        JOBS = json.load(open(os.path.join(COMMON, "jobs.json")))
        INST_DIR = os.path.join(COMMON, "inst")
        LABELS = os.path.join(P2, "wp2_deployed", "labels")
        TRIALS = os.path.join(W, "dryrun", "trials_dryrun.csv")
        RESULTS = os.path.join(W, "dryrun", "results")
        RUNTAG = "dryrun_"
    else:
        raise ValueError(mode)


def cpus():
    return IDLE_CPUS if os.path.exists(IDLE_FLAG) else BUSY_CPUS


def base_env(threads=2, extra=None, work=None):
    e = dict(os.environ)
    assert e.get("WP3_ROOT") == W, "source wp3_test/env.sh first"
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"]:
        e[k] = str(threads)
    e["OMP_WAIT_POLICY"] = "PASSIVE"
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e["PYTHONPATH"] = ":".join([SRC, os.path.join(SRC, "q3lib"), os.path.join(SRC, "q2lib"), work or WORK])
    if extra:
        e.update(extra)
    return e


def run_logged(args, log_path, env=None, py=BALEEN_PY, cpuset=None, tag=None, work=None):
    """Run `py -B args...` in `work` (default WORK = overlay) under taskset + bwrap with a private /tmp."""
    WORK_ = work or WORK
    cpuset = cpuset or cpus()
    tag = tag or os.path.basename(os.path.dirname(log_path)) + "_" + os.path.basename(log_path).replace(".log", "")
    jtmp = os.path.join(WORK_, "systmp", f"{tag}_{os.getpid()}_{threading.get_ident()}_{time.time_ns()}")
    os.makedirs(jtmp)
    cmd = ["taskset", "-c", cpuset, "bwrap", "--dev-bind", "/", "/", "--bind", jtmp, "/tmp", "--", py, "-B"] + list(args)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    t0 = time.time()
    with open(log_path, "w") as log:
        log.write("$ cd " + WORK_ + " && " + " ".join(shlex.quote(a) for a in cmd) + "\n\n")
        log.flush()
        rc = subprocess.call(cmd, cwd=WORK_, stdout=log, stderr=subprocess.STDOUT, env=env or base_env(work=WORK_))
    shutil.rmtree(jtmp, ignore_errors=True)
    return rc, time.time() - t0


_TLOCK = threading.Lock()


class TrainLock:
    """Serialize every Baleen `train` / GBM-heavy job (LightGBM num_threads=20 hard-coded); shared with Track B."""
    def __enter__(self):
        _TLOCK.acquire()
        self.f = open(TRAIN_LOCK_FILE, "a")
        t = time.time()
        fcntl.flock(self.f, fcntl.LOCK_EX)
        self.waited = time.time() - t
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()
        _TLOCK.release()


class SimSlot:
    """Cross-process cap on concurrent simulations with a cap that follows TIMING_IDLE (6 busy / 14 idle).
    Acquisition is atomic under a mutex file: count held slots, take a free one only if held < cap."""
    def __enter__(self):
        d = os.path.join(W, ".sim_slots.d")
        os.makedirs(d, exist_ok=True)
        while True:
            with open(os.path.join(d, "mutex"), "w") as mx:
                fcntl.flock(mx, fcntl.LOCK_EX)
                cap = IDLE_SIMS if os.path.exists(IDLE_FLAG) else BUSY_SIMS
                free, held = [], 0
                fs = []
                for i in range(IDLE_SIMS):
                    f = open(os.path.join(d, f"slot_{i}"), "w")
                    try:
                        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                        free.append((i, f))
                    except OSError:
                        held += 1
                        f.close()
                got = None
                if held < cap and free:
                    got = free[0][1]
                    for _, f in free[1:]:
                        fcntl.flock(f, fcntl.LOCK_UN)
                        f.close()
                else:
                    for _, f in free:
                        fcntl.flock(f, fcntl.LOCK_UN)
                        f.close()
                fcntl.flock(mx, fcntl.LOCK_UN)
            if got is not None:
                self.f = got
                self.cpuset = cpus()
                return self
            time.sleep(10)

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


def parse_train_outputs(log_path, work=None):
    lines = open(log_path).read().splitlines()
    if "Filenames generated:" not in lines:
        return None
    out = {}
    for line in lines[lines.index("Filenames generated:") + 1:]:
        parts = line.split(" ")
        if len(parts) == 3 and not parts[0].startswith("+"):
            out[parts[0]] = (os.path.join(work or WORK, parts[1]), parts[2])
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


def fill_sim_args(sim_args, train_out):
    import re
    filled = []
    for a in sim_args:
        m = re.fullmatch(r"\{TRAIN:(\w+)\}", a)
        if m:
            path = train_out[m.group(1)][0]
            if m.group(1).startswith("model_prefetch_"):
                path = path.replace("_prefetch_offset_start.model", "_prefetch_{k}.model")
            a = path
        filled.append(a)
    return filled


def result_files(out_dir, work=None):
    return sorted(glob.glob(os.path.join(work or WORK, out_dir, "**", "*_cache_perf.txt.lzma"), recursive=True))


def load_result(path):
    import compress_json
    return compress_json.load(path)


def window_series(result_file):
    import compress_json
    st = compress_json.load(result_file.replace("_cache_perf.txt.lzma", "_cache_perf.txt.stats.lzma"))
    b = st["batches"]
    used = np.diff(np.asarray(b["service_time_used_stats"], float), prepend=0)
    noc = np.diff(np.asarray(b["service_time_nocache_stats"], float), prepend=0)
    return dict(used=used, nocache=noc)


def metrics(result_file):
    """P100 (== PeakServiceTimeUtil1), P99, top-5 mean, mean DT (util %, windows after day 1) -- as xc.metrics."""
    r = load_result(result_file)["results"]
    ws = window_series(result_file)
    used = ws["used"][SKIP:]
    scale = r["PeakServiceTimeUtil1"] / used.max()
    top5 = np.sort(used)[::-1][:5]
    return dict(wr=r["FlashWriteRate"], p100=r["PeakServiceTimeUtil1"], p99=float(np.percentile(used, 99) * scale),
                top5=float(top5.mean() * scale), mean_dt=float(used.mean() * scale),
                argmax=int(np.argmax(used)) + SKIP, top5_windows=[int(x) + SKIP for x in np.argsort(used)[::-1][:5]])


def append_csv(path, row, cols=None):
    import csv
    with open(path + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        exist = os.path.exists(path) and os.path.getsize(path) > 0
        if exist:
            with open(path) as f:
                hdr = next(csv.reader(f))
            keys = [r[0] for r in csv.reader(open(path))][1:]
            assert row.get("trial_key") not in keys, f"duplicate trial key {row.get('trial_key')}"
        else:
            hdr = cols or list(row)
        extra = [k for k in row if k not in hdr]
        if extra:  # rewrite with the extended header
            import pandas as pd
            df = pd.read_csv(path) if exist else pd.DataFrame(columns=hdr)
            hdr = hdr + extra
            df = df.reindex(columns=hdr)
            df.to_csv(path, index=False)
        with open(path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=hdr)
            if not exist and not extra:
                w.writeheader()
            w.writerow({k: row.get(k, "") for k in hdr})
        fcntl.flock(lk, fcntl.LOCK_UN)


def get_flag(args, flag):
    return args[args.index(flag) + 1] if flag in args else None
