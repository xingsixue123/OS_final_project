"""Run reproduction jobs (train -> simulate) exactly as the artifact does, from work/.

  python repro/run.py smoke            # README example (Region1): RejectX + Baleen
  python repro/run.py fig9 -j 10       # jobs from make_jobs.py
  python repro/run.py fig9 --only Region7_s0_rejectx --force

Each job = `python -B -m BCacheSim.episodic_analysis.train ...` then
`python -B -m BCacheSim.cachesim.simulate_ap ...`, cwd=work/ (as BCacheSim/run_py.sh does
from the repo root). Train output paths are read from train's own "Filenames generated:"
block and substituted into the sim command. Status: work/jobs/<set>/<job_id>.json.
"""
import argparse
import datetime
import fcntl
import glob
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import common as C

# Soft failures the simulator prints and then continues past (sim_cache.py:1467 etc.).
SOFT_FAIL_PATTERNS = ["Failed to load", "Bad file", "Traceback (most recent call last)"]


THREADS = None  # OpenMP threads per job (set in main)
# The artifact hard-codes LightGBM num_threads=20 for training (train_ap.py:293,
# train_prefetcher.py:57), which overrides OMP_NUM_THREADS. Training steps therefore run one
# at a time (as on the authors' one-job-per-node cluster); simulations run in parallel.
_TRAIN_TLOCK = threading.Lock()


class _TrainLock:
    """Thread lock + flock on work/.train.lock, so it also holds across run.py processes."""
    def __enter__(self):
        _TRAIN_TLOCK.acquire()
        self.f = open(os.path.join(C.WORK, ".train.lock"), "w")
        fcntl.flock(self.f, fcntl.LOCK_EX)

    def __exit__(self, *exc):
        fcntl.flock(self.f, fcntl.LOCK_UN)
        self.f.close()
        _TRAIN_TLOCK.release()


TRAIN_LOCK = _TrainLock()


def env():
    e = dict(os.environ)
    if "REPRO_ROOT" not in e:
        sys.exit("source changes/0_reproduce/env.sh first")
    # LightGBM defaults to one OpenMP thread per core; N parallel jobs would oversubscribe the
    # CPU N-fold and OpenMP spin-waiting then stalls training. Cap threads per job instead
    # (the authors ran one job per 16-core node). Model and parameters are unchanged.
    for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]:
        e[k] = str(THREADS)
    return e


def run_logged(args, log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    t0 = time.time()
    with open(log_path, "w") as log:
        log.write("$ cd work && " + " ".join(C.SANDBOX + args) + "\n\n")
        log.flush()
        rc = subprocess.call(C.SANDBOX + args, cwd=C.WORK, stdout=log, stderr=subprocess.STDOUT, env=env())
    return rc, time.time() - t0


def parse_train_outputs(log_path):
    """Parse the `Filenames generated:` block printed at the end of train.py."""
    lines = open(log_path).read().splitlines()
    if "Filenames generated:" not in lines:
        return None
    out = {}
    for line in lines[lines.index("Filenames generated:") + 1:]:
        parts = line.split(" ")
        if len(parts) == 3 and not parts[0].startswith("+"):
            out[parts[0]] = (parts[1], parts[2])
    return out


def fill_sim_args(sim_args, train_out):
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


def required_inputs(sim_args):
    files = [C.get_flag(sim_args, "--trace")]
    for flag in ["--ep-analysis", "--offline-ap-decisions", "--learned-ap-model-path", "--config"]:
        if flag in sim_args:
            files.append(sim_args[sim_args.index(flag) + 1])
    if "--prefetcher-model-path" in sim_args:
        pat = C.get_flag(sim_args, "--prefetcher-model-path")
        files += [pat.format(k=k) for k in ["offset_start", "offset_end", "pred_net_pf_st_binary"]]
    return [f for f in files if f]


def run_job(job, set_name, force=False):
    jid = job["job_id"]
    status_path = os.path.join(C.JOBS_DIR, set_name, f"{jid}.json")
    if os.path.exists(status_path) and not force:
        st = json.load(open(status_path))
        if st.get("status") == "done":
            return st
    logd = os.path.join(C.LOGS_DIR, set_name, jid)
    st = {"job_id": jid, "status": "running", "started": datetime.datetime.now().isoformat(),
          "omp_threads": THREADS, "job": job}

    def save(**kw):
        st.update(kw)
        os.makedirs(os.path.dirname(status_path), exist_ok=True)
        json.dump(st, open(status_path, "w"), indent=1)
        return st

    save()
    sim_args = list(job["sim_args"])
    if job.get("train_args"):
        targs = [C.PY, "-B", "-m", C.TRAIN_MOD] + job["train_args"]
        with TRAIN_LOCK:
            rc, dt = run_logged(targs, os.path.join(logd, "train.log"))
        st["train_secs"] = round(dt, 1)
        if rc != 0:
            return save(status="failed", error=f"train rc={rc}")
        train_out = parse_train_outputs(os.path.join(logd, "train.log"))
        if train_out is None:
            return save(status="failed", error="train: no 'Filenames generated' block")
        missing = [k for k, (p, size) in train_out.items() if size == "NoExists"]
        if missing:
            return save(status="failed", error=f"train did not produce: {missing}")
        st["train_outputs"] = {k: p for k, (p, _) in train_out.items()}
        sim_args = fill_sim_args(sim_args, train_out)

    missing = [f for f in required_inputs(sim_args) if not os.path.exists(os.path.join(C.WORK, f))]
    if missing:
        return save(status="failed", error=f"missing sim inputs: {missing}")

    sargs = [C.PY, "-B", "-m", C.SIM_MOD] + sim_args
    st["sim_cmd"] = " ".join(sargs)
    rc, dt = run_logged(sargs, os.path.join(logd, "sim.log"))
    st["sim_secs"] = round(dt, 1)
    log = open(os.path.join(logd, "sim.log")).read()
    soft = [p for p in SOFT_FAIL_PATTERNS if p in log]
    if rc != 0 or soft:
        return save(status="failed", error=f"sim rc={rc} soft={soft}")

    if "--config" in sim_args:
        out_dir = json.load(open(os.path.join(C.WORK, C.get_flag(sim_args, "--config"))))["output_dir"]
    else:
        out_dir = C.get_flag(sim_args, "-o")
    res = sorted(glob.glob(os.path.join(C.WORK, out_dir, "**", "*_cache_perf.txt.lzma"), recursive=True))
    if len(res) != 1:
        return save(status="failed", error=f"expected 1 result file under {out_dir}, found {len(res)}")
    return save(status="done", result_file=os.path.relpath(res[0], C.WORK),
                finished=datetime.datetime.now().isoformat())


def check_frozen():
    subprocess.check_call(["bash", os.path.join(C.ROOT, "check_frozen.sh")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set", help="job set name: smoke | fig9 | ...")
    ap.add_argument("-j", "--jobs", type=int, default=6, help="parallel jobs (train uses 8 workers each)")
    ap.add_argument("--only", help="substring filter on job_id")
    ap.add_argument("--force", action="store_true", help="rerun jobs already done")
    ap.add_argument("--threads", type=int, help="OpenMP threads per job (default: cores // jobs)")
    args = ap.parse_args()
    global THREADS
    THREADS = args.threads or max(1, (os.cpu_count() or 1) // args.jobs)

    check_frozen()
    jobs = C.load_jobs(args.set)
    if args.only:
        jobs = [j for j in jobs if args.only in j["job_id"]]
    print(f"{len(jobs)} jobs, -j {args.jobs}, OMP threads/job {THREADS}")
    with ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(run_job, j, args.set, args.force): j["job_id"] for j in jobs}
        for f in as_completed(futs):
            st = f.result()
            print(f"[{st['status']:6s}] {futs[f]}  train={st.get('train_secs', '-')}s "
                  f"sim={st.get('sim_secs', '-')}s  {st.get('error', '')}", flush=True)
    check_frozen()


if __name__ == "__main__":
    main()
