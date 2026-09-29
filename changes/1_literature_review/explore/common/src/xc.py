"""Shared infrastructure for Track A (explore/common + explore/q3).

Copied/adapted from harness_eval/src/hecommon.py (never imported from there; harness_eval stays untouched).
Everything writes under X = explore/. The frozen artifact (0_reproduce/baleen_code) and 0_reproduce/env are only
read / executed.  A "work" dir W (X/common/work or X/q3/work) is the cwd of every Baleen process:
  W/BCacheSim -> <rel>/0_reproduce/baleen_code/BCacheSim   (frozen, read-only)
  W/data      -> <rel>/common/data                          (traces, sha1-verified)
Every Baleen process runs as  taskset -c 8-23 bwrap --dev-bind / / --bind W/systmp /tmp -- ...
Every `train` invocation holds an exclusive flock on X/.train.lock (shared with Track B).
Concurrent simulations are capped by a flock slot pool X/common/.sim_slots.d (K from X/common/.sim_slots, default 14).
"""
import fcntl
import glob
import json
import os
import shlex
import subprocess
import threading
import time

import numpy as np

X = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
COMMON = os.path.join(X, "common")
Q3 = os.path.join(X, "q3")
REPRO = os.path.normpath(os.path.join(X, "..", "..", "0_reproduce"))
HARNESS = os.path.normpath(os.path.join(X, "..", "harness_eval"))
BALEEN_PY = os.path.join(REPRO, "env", "bin", "python")
AUDIT_SOLVER_PY = os.path.normpath(os.path.join(X, "..", "ising_followup", "audit", "env", "bin", "python"))
XENV_PY = os.path.join(X, "env", "bin", "python")
TRAIN_LOCK_FILE = os.path.join(X, ".train.lock")
CORES = "8-23"
TRAIN_MOD = "BCacheSim.episodic_analysis.train"
SIM_MOD = "BCacheSim.cachesim.simulate_ap"
TARGET_WR = 35.599
TOL = 0.01
LOG_INTERVAL = 600
SKIP_WINDOWS = 86400 // LOG_INTERVAL


def solver_py():
    """Solver env: X/env once Track B wrote X/env/ENV_READY, else harness_eval's audit env (read-only)."""
    if os.path.exists(os.path.join(X, "env", "ENV_READY")) and os.path.exists(XENV_PY):
        return XENV_PY
    return AUDIT_SOLVER_PY


def sandbox(work):
    return ["taskset", "-c", CORES, "bwrap", "--dev-bind", "/", "/", "--bind", os.path.join(work, "systmp"), "/tmp", "--"]


def base_env(src_dirs, work, extra=None, threads=2):
    e = dict(os.environ)
    assert e.get("X_ROOT") == X, "source explore/q3/env.sh first"
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"]:
        e[k] = str(threads)
    e["PYTHONPATH"] = ":".join(list(src_dirs) + [work])
    e["OMP_WAIT_POLICY"] = "PASSIVE"   # OpenMP idle behaviour only (no model/parameter change)
    if extra:
        e.update(extra)
    return e


def run_logged(args, log_path, env, work):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    t0 = time.time()
    with open(log_path, "w") as log:
        log.write("$ cd " + work + " && " + " ".join(shlex.quote(a) for a in sandbox(work) + args) + "\n\n")
        log.flush()
        rc = subprocess.call(sandbox(work) + args, cwd=work, stdout=log, stderr=subprocess.STDOUT, env=env)
    return rc, time.time() - t0


_TLOCK = threading.Lock()


class TrainLock:
    """Serialize every Baleen `train` invocation across BOTH tracks (flock on X/.train.lock)."""
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


TRAIN_LOCK = TrainLock()


class SimSlot:
    """Cross-process cap on concurrent simulations of Track A (one of K flock'ed slot files), FIFO: a waiter may try
    the slots only while it holds the oldest live ticket in .sim_queue.d (tickets of dead processes are removed)."""
    def __enter__(self):
        d = os.path.join(COMMON, ".sim_slots.d")
        q = os.path.join(COMMON, ".sim_queue.d")
        os.makedirs(d, exist_ok=True)
        os.makedirs(q, exist_ok=True)
        ticket = os.path.join(q, f"{time.time_ns():020d}_{os.getpid()}_{threading.get_ident()}")
        open(ticket, "w").close()
        try:
            while True:
                tickets = sorted(os.listdir(q))
                live = []
                for t in tickets:
                    pid = int(t.split("_")[1])
                    try:
                        os.kill(pid, 0)
                        live.append(t)
                    except OSError:
                        try:
                            os.remove(os.path.join(q, t))
                        except OSError:
                            pass
                if live and live[0] == os.path.basename(ticket):
                    try:
                        k = int(open(os.path.join(COMMON, ".sim_slots")).read().strip())
                    except Exception:
                        k = 14
                    k = min(k, 14)
                    for i in range(k):
                        f = open(os.path.join(d, f"slot_{i}"), "w")
                        try:
                            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            self.f = f
                            return self
                        except OSError:
                            f.close()
                    time.sleep(0.3)    # head of the queue polls fast (older random-polling drivers still compete)
                else:
                    time.sleep(1)
        finally:
            try:
                os.remove(ticket)
            except OSError:
                pass

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


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


def remove_flag_nargs(args, flag):
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


def get_flag(args, flag):
    return args[args.index(flag) + 1] if flag in args else None


def trace_path(region, start, group="20230325"):
    return f"data/tectonic/{group}/{region}/full_{start:g}_0.1.trace"


# ------------------------------------------------------------------ results (Baleen env only: compress_json)
def load_result(result_file):
    import compress_json
    return compress_json.load(result_file)


def result_file_in(work, out_dir):
    return sorted(glob.glob(os.path.join(work, out_dir, "**", "*_cache_perf.txt.lzma"), recursive=True))


def window_series(result_file):
    stats_f = result_file.replace("_cache_perf.txt.lzma", "_cache_perf.txt.stats.lzma")
    if not os.path.exists(stats_f):
        stats_f = glob.glob(os.path.join(os.path.dirname(result_file), "*.stats*lzma"))[0]
    import compress_json
    st = compress_json.load(stats_f)
    b = st["batches"] if "batches" in st else st["stats"]["batches"]
    used = np.diff(np.asarray(b["service_time_used_stats"], float), prepend=0)
    noc = np.diff(np.asarray(b["service_time_nocache_stats"], float), prepend=0)
    return dict(used=used, nocache=noc, time_phy=np.asarray(b["time_phy"], float))


def metrics(result_file):
    """P100 (== PeakServiceTimeUtil1), P99, top-5 mean, mean DT (util %, windows after day 1)."""
    r = load_result(result_file)["results"]
    ws = window_series(result_file)
    used = ws["used"][SKIP_WINDOWS:]
    scale = r["PeakServiceTimeUtil1"] / used.max()
    top5 = np.sort(used)[::-1][:5]
    return dict(wr=r["FlashWriteRate"], p100=r["PeakServiceTimeUtil1"], p99=float(np.percentile(used, 99) * scale),
                top5=float(top5.mean() * scale), mean_dt=float(used.mean() * scale),
                argmax=int(np.argmax(used)) + SKIP_WINDOWS, scale=float(scale),
                top5_windows=[int(x) + SKIP_WINDOWS for x in np.argsort(used)[::-1][:5]])


# ------------------------------------------------------------------ simulation + threshold convergence
def sim_at(work, tag, base_args, th, log_dir, out_root, flag="--ap-threshold", threads=2, fmt="{:.6f}"):
    ttag = f"th_{fmt.format(th)}"
    out = f"{out_root}/{ttag}"
    args = set_flag(list(base_args), flag, fmt.format(th))
    args = set_flag(args, "-o", out)
    args = set_flag(args, "--job-id", f"{tag}__{ttag}".replace("/", "__"))
    done = result_file_in(work, out)
    t = time.time()
    if not done:
        with SimSlot():
            done = result_file_in(work, out)
            if not done:
                env = base_env([], work, threads=threads)
                log = os.path.join(log_dir, f"{ttag}.log")
                rc, dt = run_logged([BALEEN_PY, "-B", "-m", SIM_MOD] + args, log, env, work)
                if rc != 0:
                    return {"threshold": th, "error": f"rc={rc}", "log": log}
                done = result_file_in(work, out)
                txt = open(log).read()
                for p in ["Failed to load", "Bad file", "Traceback (most recent call last)"]:
                    if p in txt:
                        return {"threshold": th, "error": f"soft-fail {p}", "log": log}
                if not done:
                    return {"threshold": th, "error": "no result file", "log": log}
    r = load_result(done[0])["results"]
    return {"threshold": th, "wr": r["FlashWriteRate"], "peak": r["PeakServiceTimeUtil1"], "result_file": done[0],
            "secs": time.time() - t}


def converge_loop(work, tag, base, seeds, pool, log_dir, out_root, step, increasing, lo_bound=0.0, hi_bound=1.0,
                  max_rounds=8, target=TARGET_WR, flag="--ap-threshold", fmt="{:.6f}", ndigits=6):
    """Inner loop on a threshold-like knob until WR within TOL of target. Same rules as
    0_reproduce/repro/converge.py (bracket -> secant + 3-point grid of +-d/4; else step outward), generalized to
    both directions (`increasing`: higher knob -> more admits), with harness_eval's secant extrapolation when the
    target is not yet bracketed."""
    def run(ths):
        return list(pool.map(lambda t: sim_at(work, tag, base, t, log_dir, out_root, flag=flag, fmt=fmt), ths))
    tried = run(seeds)
    best = None
    grid = []
    for rnd in range(max_rounds):
        grid = [t for t in grid if lo_bound < t < hi_bound and all(abs(t - x["threshold"]) > 10 ** -ndigits
                                                                  for x in tried)]
        tried += run(grid)
        ok = [x for x in tried if x.get("wr") is not None]
        if not ok:
            raise RuntimeError(f"{tag}: all sims failed: {tried}")
        best = min(ok, key=lambda x: abs(x["wr"] - target))
        print(f"[{tag}] round {rnd}: best {flag}={best['threshold']:.6g} WR={best['wr']:.3f} peak={best['peak']:.3f}",
              flush=True)
        if abs(best["wr"] - target) / target <= TOL:
            break
        above = [x for x in ok if x["wr"] > target]
        below = [x for x in ok if x["wr"] < target]
        if above and below:
            a = min(above, key=lambda x: x["wr"])
            b = max(below, key=lambda x: x["wr"])
            t = a["threshold"] + (a["wr"] - target) * (b["threshold"] - a["threshold"]) / (a["wr"] - b["wr"])
            d = abs(b["threshold"] - a["threshold"]) / 4
            grid = [round(t - d, ndigits), round(t, ndigits), round(t + d, ndigits)]
        else:
            up = (best["wr"] < target) == increasing
            st = abs(step) if up else -abs(step)
            edge = max(ok, key=lambda x: x["threshold"]) if st > 0 else min(ok, key=lambda x: x["threshold"])
            two = sorted(ok, key=lambda x: abs(x["wr"] - target))
            two = [two[0]] + [x for x in two[1:] if abs(x["threshold"] - two[0]["threshold"]) > 1e-12][:1]
            slope = None
            if len(two) == 2:
                slope = (two[1]["wr"] - two[0]["wr"]) / (two[1]["threshold"] - two[0]["threshold"])
                if (slope > 0) != increasing or abs(slope) < 1e-12:
                    slope = None
            if slope is not None:
                t = two[0]["threshold"] + (target - two[0]["wr"]) / slope
                t = min(max(t, edge["threshold"] + st), edge["threshold"] + 12 * st) if st > 0 else \
                    max(min(t, edge["threshold"] + st), edge["threshold"] + 12 * st)
                d = max(abs(step) / 2, abs(t - two[0]["threshold"]) * 0.15)
                grid = [round(t - d, ndigits), round(t, ndigits), round(t + d, ndigits)]
            else:
                grid = [round(edge["threshold"] + st * k, ndigits) for k in (1, 2, 4)]
            grid = [min(max(g, lo_bound * 1.0000001 + 1e-12), hi_bound * 0.9999999) for g in grid]
    return tried, best


_CSV_LOCK = threading.Lock()


def append_jsonl(path, row):
    with _CSV_LOCK:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(row, default=float) + "\n")


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]
