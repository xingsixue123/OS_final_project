"""Track A (phase 2) shared infrastructure: paths, sandboxed runners, train lock, sim slots, result loading.
Adapted (copied) from 1_literature_review/harness_eval/src/hecommon.py.

Two work dirs with the same relative layout, so the same command line runs either code base:
  wp0_overlay/work/BCacheSim        -> ../overlay/BCacheSim                         (the overlay, our patch)
  wp0_overlay/work_frozen/BCacheSim -> ../../../0_reproduce/baleen_code/BCacheSim   (frozen, read-only)
  */data -> ../../../1_literature_review/explore/common/data                        (read-only, 70 traces)
Every Baleen process: `taskset -c 8-23 bwrap --dev-bind / / --bind <private job tmp> /tmp -- python -B ...`
(private /tmp per job: no shared /tmp/cache-sim-accesses-* pickle between concurrent jobs or code bases).
Every train holds flock(2_deployable_peak/.train.lock) (shared with Track B); <= 12 concurrent sims.
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

A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # wp0_overlay
P2 = os.path.dirname(A)
SRC = os.path.join(A, "src")
RESULTS = os.path.join(A, "results")
WORKS = {"overlay": os.path.join(A, "work"), "frozen": os.path.join(A, "work_frozen")}
REPRO = os.path.normpath(os.path.join(P2, "..", "0_reproduce"))
BALEEN_PY = os.path.join(REPRO, "env", "bin", "python")
TRAIN_LOCK_FILE = os.path.join(P2, ".train.lock")
CORES = "8-23"
MAX_SIMS = 12
TRAIN_MOD = "ta_launch_train"
SIM_MOD = "ta_launch_sim"
TARGET_WR = 35.599
LOG_INTERVAL = 600
SKIP_WINDOWS = 86400 // LOG_INTERVAL
# Fig 9 Baleen jobs (0_reproduce/work/jobs/fig9.jsonl, read-only) and 0_reproduce's converged thresholds (rep 0).
BALEEN_JOB = {"Region7": "20230325_Region7_s0_baleen_20230327_tracedrop_XX",
              "Region6": "20230325_Region6_s0_baleen_20230327_tracedrop_old"}
BALEEN_TH = {"Region7": 0.62094, "Region6": 0.806378}
STATIC_JOBS = {(r, p): f"20230325_{r}_s0_{p}_20230410_static_pf"
               for r in ("Region7", "Region6") for p in ("rejectx", "coinflip")}


def base_env(threads=2, extra=None):
    e = dict(os.environ)
    assert e.get("TA_ROOT") == A, "source wp0_overlay/env.sh first"
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"]:
        e[k] = str(threads)
    e["OMP_WAIT_POLICY"] = "PASSIVE"
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    if extra:
        e.update(extra)
    return e


def run_logged(args, log_path, code="overlay", env=None, tag=None):
    """Run `python -B ...` (args without the interpreter) in WORKS[code] under taskset + bwrap with a private /tmp."""
    cwd = WORKS[code]
    tag = tag or os.path.basename(log_path).replace(".log", "")
    jtmp = os.path.join(cwd, "systmp", f"{tag}_{os.getpid()}_{threading.get_ident()}_{time.time_ns()}")
    os.makedirs(jtmp)
    cmd = ["taskset", "-c", CORES, "bwrap", "--dev-bind", "/", "/", "--bind", jtmp, "/tmp", "--",
           BALEEN_PY, "-B"] + list(args)
    env = env or base_env()
    env["PYTHONPATH"] = SRC + ":" + cwd
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    t0 = time.time()
    with open(log_path, "w") as log:
        log.write("$ cd " + cwd + " && " + " ".join(shlex.quote(a) for a in cmd) + "\n\n")
        log.flush()
        rc = subprocess.call(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, env=env)
    shutil.rmtree(jtmp, ignore_errors=True)
    return rc, time.time() - t0


_TLOCK = threading.Lock()


class TrainLock:
    """Serialize every Baleen `train` (LightGBM num_threads=20 is hard-coded); shared with Track B."""
    def __enter__(self):
        _TLOCK.acquire()
        self.f = open(TRAIN_LOCK_FILE, "a")
        fcntl.flock(self.f, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()
        _TLOCK.release()


class SimSlot:
    """Cross-process cap on concurrent simulations (MAX_SIMS flock'ed slot files)."""
    def __enter__(self):
        d = os.path.join(A, ".sim_slots.d")
        os.makedirs(d, exist_ok=True)
        while True:
            for i in range(MAX_SIMS):
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


def parse_train_outputs(log_path, code):
    """'Filenames generated:' block of a train log -> {name: (absolute path, size)}."""
    lines = open(log_path).read().splitlines()
    if "Filenames generated:" not in lines:
        return None
    out = {}
    for line in lines[lines.index("Filenames generated:") + 1:]:
        parts = line.split(" ")
        if len(parts) == 3 and not parts[0].startswith("+"):
            out[parts[0]] = (os.path.join(WORKS[code], parts[1]), parts[2])
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


def load_fig9_job(job_id):
    with open(os.path.join(REPRO, "work", "jobs", "fig9.jsonl")) as f:
        for line in f:
            j = json.loads(line)
            if j["job_id"] == job_id:
                return j
    raise KeyError(job_id)


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


def result_files(code, out_dir):
    return sorted(glob.glob(os.path.join(WORKS[code], out_dir, "**", "*_cache_perf.txt.lzma"), recursive=True))


def run_train(code, args, log_path, dump_dir=None, extra_env=None):
    env = base_env(threads=2, extra=extra_env)
    if dump_dir:
        os.makedirs(dump_dir, exist_ok=True)
        env["TA_DUMP_DIR"] = dump_dir
    with TrainLock():
        rc, dt = run_logged(["-m", TRAIN_MOD] + list(args), log_path, code=code, env=env)
    out = parse_train_outputs(log_path, code)
    if rc != 0 or out is None or any(sz == "NoExists" for _, sz in out.values()):
        raise RuntimeError(f"train failed rc={rc}: {log_path}")
    return out, dt


def run_sim(code, args, out_dir, log_path, record=None):
    """Simulate (args must not contain -o); returns the result file (absolute)."""
    args = set_flag(list(args), "-o", out_dir)
    env = base_env(threads=2)
    if record:
        env["TA_RECORD"] = record
    done = result_files(code, out_dir)
    if not done:
        with SimSlot():
            rc, dt = run_logged(["-m", SIM_MOD] + args, log_path, code=code, env=env)
        log = open(log_path).read()
        for p in ["Failed to load", "Bad file", "Traceback (most recent call last)"]:
            if p in log:
                raise RuntimeError(f"sim soft-fail '{p}': {log_path}")
        done = result_files(code, out_dir)
        if rc != 0 or not done:
            raise RuntimeError(f"sim failed rc={rc}: {log_path}")
    return done[0]


def load_result(path):
    import compress_json  # Baleen env only
    return compress_json.load(path)


def stats_file(result_file):
    return result_file.replace("_cache_perf.txt.lzma", "_cache_perf.txt.stats.lzma")
