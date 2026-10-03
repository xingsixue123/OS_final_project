"""Phase-2 Track B offline (OPT-mode) simulation of a selection (Baleen env, read-only use of the frozen artifact).
Copied from phase-1 q2/src/q2sim.py; changes: P2 paths, the shared P2/.train.lock, the trace group per region
(Region4 = 202110), a dump mode (instance + R0 decisions in ONE train), top-5 windows in the metrics, a work dir per
caller (WP1: wp1_offline/work, WP5: wp5_ising/work) and ONE sim-slot pool for the whole track (<= 6 concurrent).

1. train (flock P2/.train.lock, bwrap private /tmp, taskset -c 8-23): the authors' OPT-AP train args ("OPT-Range on
   OPT-Ep-Start": filter_=prefetch, the OPT's converged EA from the release CSV, no GBMs, split end 1e9) with
   --policy PolicyQ2 in mode
     'dump'   : Baleen's own order (= R0, the peak-blind OPT) + instance dump (harness format)
     'replay' : a solver selection (prefix rule asserted; instance re-dumped and checked against the solved one)
2. simulate_ap --offline-ap --ap opt (unmodified OfflineAP; authors' sim flags) with --ap-threshold converged to
   35.599 MB/s +-1% (converge.py rules as in phase 1: 3 seeds h-1, h, h+1, then bracket -> secant + 3-point grid,
   else secant/step outward); sims pinned to cores 8-23, OMP_NUM_THREADS=2, <= 6 concurrent for the whole track.
3. metrics (P100 = PeakServiceTimeUtil1, P99, top-5 mean, mean DT, argmax window, top-5 windows) -> results jsonl.
"""
import fcntl
import glob
import json
import os
import shlex
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

SRC = os.path.dirname(os.path.abspath(__file__))
P2 = "/home/sxing/project/OS_final_project/changes/2_deployable_peak"
REPRO = "/home/sxing/project/OS_final_project/changes/0_reproduce"
BALEEN_PY = os.path.join(REPRO, "env", "bin", "python")
TRAIN_LOCK = os.path.join(P2, ".train.lock")
SLOTS_DIR = os.path.join(P2, "wp1_offline", ".sim_slots.d")      # shared by WP1 and WP5 sims
PIN = ["taskset", "-c", "8-11,20-23"]   # physical cores 8-11 only: never the SMT siblings (12-19) of the timing cores 0-7
TRAIN_MOD = "q2launch_train"
SIM_MOD = "BCacheSim.cachesim.simulate_ap"
TARGET_WR = 35.599
TOL = 0.01
SKIP_WINDOWS = 144
MAX_SIMS = min(int(os.environ.get("P2_MAX_SIMS", "6")), 6)
GROUP = {"Region4": "202110", "Region5": "20230325", "Region6": "20230325", "Region7": "20230325"}

WORK = os.environ.get("P2_SIM_WORK", os.path.join(P2, "wp1_offline", "work"))
RESULTS = os.environ.get("P2_SIM_RESULTS", os.path.join(P2, "wp1_offline", "results", "sims.jsonl"))


def sandbox():
    return ["bwrap", "--dev-bind", "/", "/", "--bind", os.path.join(WORK, "systmp"), "/tmp", "--"]


def base_env(extra=None, threads=2):
    e = dict(os.environ)
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"]:
        e[k] = str(threads)
    e["PYTHONPATH"] = SRC + ":" + WORK
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e["OMP_WAIT_POLICY"] = "PASSIVE"
    if extra:
        e.update(extra)
    return e


def run_logged(args, log_path, env=None, cwd=None):
    cwd = cwd or WORK
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    t0 = time.time()
    full = PIN + sandbox() + args
    with open(log_path, "w") as log:
        log.write("$ cd " + cwd + " && " + " ".join(shlex.quote(a) for a in full) + "\n\n")
        log.flush()
        rc = subprocess.call(full, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, env=env or base_env())
    return rc, time.time() - t0


class SimSlot:
    def __enter__(self):
        os.makedirs(SLOTS_DIR, exist_ok=True)
        while True:
            for i in range(MAX_SIMS):
                f = open(os.path.join(SLOTS_DIR, f"slot_{i}"), "w")
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.f = f
                    return self
                except OSError:
                    f.close()
            time.sleep(2)

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()


class TrainLock:
    """shared with Track A: P2/.train.lock (exclusive flock around every Baleen train)."""
    _t = threading.Lock()

    def __enter__(self):
        self._t.acquire()
        self.f = open(TRAIN_LOCK, "a")
        t = time.time()
        fcntl.flock(self.f, fcntl.LOCK_EX)
        self.waited = time.time() - t
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()
        self._t.release()


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


def sstr(sample_start):
    return "0" if float(sample_start) == 0 else f"{float(sample_start):g}"


def trace_path(region, sample_start):
    return f"data/tectonic/{GROUP[region]}/{region}/full_{sstr(sample_start)}_0.1.trace"


def train_args(region, sample_start, exp, ea):
    ss = "0.0" if float(sample_start) == 0 else f"{float(sample_start):g}"
    return ["--exp", exp, "--policy", "PolicyQ2", "--region", region, "--sample-ratio", "0.1",
            "--sample-start", ss, "--trace-group", GROUP[region], "--supplied-ea", "physical",
            "--target-wrs", "34", "50", "100", "75", "20", "10", "60", "90", "30",
            "--target-csizes", "366.47461", "--output-base-dir", f"runs/off/{exp}/train",
            "--eviction-age", f"{ea}", "--rl-init-kwargs", "filter_=prefetch",
            "--train-split-secs-start", "0", "--train-split-secs-end", "1000000000"]


def run_train(exp, region, sample_start, ea, pcfg):
    cfgp = os.path.join(WORK, "cfg", f"{exp}.json")
    os.makedirs(os.path.dirname(cfgp), exist_ok=True)
    json.dump(pcfg, open(cfgp, "w"), indent=1)
    log = os.path.join(WORK, "logs", "off", exp, "train.log")
    out = parse_train_outputs(log) if os.path.exists(log) else None
    info = dict(train_secs=0.0, train_waited=0.0)
    need_inst = pcfg.get("mode") == "dump" and not os.path.exists(pcfg["inst_path"])
    if out is None or any(sz == "NoExists" for _, sz in out.values()) or need_inst:
        env = base_env(extra={"Q2_POLICY_CONFIG": cfgp}, threads=2)
        with TrainLock() as L:
            rc, dt = run_logged([BALEEN_PY, "-B", "-m", TRAIN_MOD] + train_args(region, sample_start, exp, ea), log,
                                env=env)
            info = dict(train_secs=dt, train_waited=L.waited)
        out = parse_train_outputs(log)
        if rc != 0 or out is None:
            raise RuntimeError(f"train failed rc={rc}: {log}")
        print(f"[train] {exp}: {info['train_secs']:.0f}s (waited {info['train_waited']:.0f}s)", flush=True)
    return out, log, info


def result_file_in(out_dir):
    return sorted(glob.glob(os.path.join(WORK, out_dir, "**", "*_cache_perf.txt.lzma"), recursive=True))


def load_result(result_file):
    import compress_json
    return compress_json.load(result_file)


def sim_at(tag, base_args, th, log_dir, out_root):
    ttag = f"th_{th:.6f}"
    out = f"{out_root}/{ttag}"
    args = set_flag(list(base_args), "--ap-threshold", f"{th:.6f}")
    args = set_flag(args, "-o", out)
    args = set_flag(args, "--job-id", f"{tag}__{ttag}".replace("/", "__"))
    done = result_file_in(out)
    t = time.time()
    if not done:
        with SimSlot():
            done = result_file_in(out)
            if not done:
                lp = os.path.join(log_dir, f"{ttag}.log")
                rc, dt = run_logged([BALEEN_PY, "-B", "-m", SIM_MOD] + args, lp, env=base_env(threads=2))
                if rc != 0:
                    return {"threshold": th, "error": f"rc={rc}", "log": lp}
                done = result_file_in(out)
                txt = open(lp).read()
                for p in ["Failed to load", "Bad file", "Traceback (most recent call last)"]:
                    if p in txt:
                        return {"threshold": th, "error": f"soft-fail {p}", "log": lp}
                if not done:
                    return {"threshold": th, "error": "no result file", "log": lp}
    r = load_result(done[0])["results"]
    return {"threshold": th, "wr": r["FlashWriteRate"], "peak": r["PeakServiceTimeUtil1"], "result_file": done[0],
            "secs": time.time() - t}


def converge_loop(tag, base, seeds, pool, log_dir, out_root, step, increasing=True, lo_bound=0.0, hi_bound=1e6,
                  max_rounds=6, target=TARGET_WR):
    """copied from phase-1 q2sim.converge_loop (converge.py rules, direction-aware)."""
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
            a = min(above, key=lambda x: x["wr"])
            b = max(below, key=lambda x: x["wr"])
            t = a["threshold"] + (a["wr"] - target) * (b["threshold"] - a["threshold"]) / (a["wr"] - b["wr"])
            d = abs(b["threshold"] - a["threshold"]) / 4
            grid = [round(t - d, 6), round(t, 6), round(t + d, 6)]
        else:
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
            grid = [g for g in grid if g > lo_bound]
    return tried, best


def window_series(result_file):
    stats_f = result_file.replace("_cache_perf.txt.lzma", "_cache_perf.txt.stats.lzma")
    if not os.path.exists(stats_f):
        stats_f = glob.glob(os.path.join(os.path.dirname(result_file), "*.stats*lzma"))[0]
    import compress_json
    st = compress_json.load(stats_f)
    b = st["batches"] if "batches" in st else st["stats"]["batches"]
    used = np.diff(np.asarray(b["service_time_used_stats"], float), prepend=0)
    return used


def metrics(result_file):
    r = load_result(result_file)["results"]
    used = window_series(result_file)[SKIP_WINDOWS:]
    scale = r["PeakServiceTimeUtil1"] / used.max()
    top5 = np.sort(used)[::-1][:5]
    return dict(wr=r["FlashWriteRate"], p100=r["PeakServiceTimeUtil1"], p99=float(np.percentile(used, 99) * scale),
                top5=float(top5.mean() * scale), mean_dt=float(used.mean() * scale),
                argmax=int(np.argmax(used)) + SKIP_WINDOWS,
                top5_windows=[int(x) + SKIP_WINDOWS for x in np.argsort(used)[::-1][:5]])


_POOL = ThreadPoolExecutor(max_workers=MAX_SIMS)
_LOCK = threading.Lock()


def evaluate(sol, solved_inst, region, sample_start, ea, th_hint, exp, extra=None, mode="replay", inst_out=None):
    """mode 'replay' = simulate a solver's selection (sol = solution npz, solved_inst = the instance it was solved on);
    mode 'dump' = Baleen's own peak-blind order (R0) + dump of the instance to inst_out, in the same train."""
    if mode == "dump":
        ip = inst_out
    else:
        ip = os.path.join(WORK, "inst", f"{exp}.npz")
    pcfg = {"mode": mode, "name": f"q2_{exp}"[:60], "target_wr": TARGET_WR, "skip_windows": SKIP_WINDOWS,
            "sol_path": os.path.abspath(sol) if sol else None,
            "solved_inst": os.path.abspath(solved_inst) if solved_inst else None, "inst_path": ip}
    out, tlog, tinfo = run_train(exp, region, sample_start, ea, pcfg)
    if mode == "replay":
        txt = open(tlog).read()
        assert "prefix rule reproduces" in txt and "matched the solved instance" in txt, f"replay check missing: {tlog}"
    base = ["--trace", trace_path(region, sample_start), "--offline-ap", "--ap", "opt", "--ap-threshold", "30",
            "--size_gb", "366.475", "-o", f"runs/off/{exp}/sim", "--prefetch-when", "at_start",
            "--prefetch-range", "acctime-episode", "--batch-size", "16", "--log-interval", "600",
            "--ep-analysis", out["analysis"][0], "--offline-ap-decisions", out["thresholds"][0],
            "--job-id", exp, "--eviction-policy", "LRU"]
    seeds = [round(th_hint - 1.0, 6), round(th_hint, 6), round(th_hint + 1.0, 6)]
    seeds = [s for s in seeds if s > 0]
    tried, best = converge_loop(exp, base, seeds, _POOL, os.path.join(WORK, "logs", "off", exp, "converge"),
                                f"runs/off/{exp}/converge", 2.0, increasing=True)
    matched = abs(best["wr"] - TARGET_WR) / TARGET_WR <= TOL
    m = metrics(best["result_file"])
    row = dict(exp=exp, sol=os.path.abspath(sol) if sol else f"R0:{exp}", region=region,
               sample_start=float(sample_start), mode=mode, ea=ea, threshold=best["threshold"], matched=matched,
               n_sims=len(tried), train_log=tlog, result_file=best["result_file"], **m, **tinfo,
               tried=[{k: v for k, v in t.items() if k != "result_file"} for t in tried])
    if extra:
        row.update(extra)
    with _LOCK:
        os.makedirs(os.path.dirname(RESULTS), exist_ok=True)
        with open(RESULTS, "a") as f:
            f.write(json.dumps(row, default=float) + "\n")
    print(f"== {exp}: P100={m['p100']:.3f} WR={m['wr']:.3f} th={best['threshold']:.4f} matched={matched} "
          f"n_sims={len(tried)}", flush=True)
    return row
