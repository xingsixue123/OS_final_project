"""Held-out Q2 runs: every method x every budget x seeds on the held-out instances, strictly sequential on cores 0-7.

  python q2heldout.py --plan plan.json
plan.json = {"form": {...}, "instances": [paths], "budgets": [10, 60, 300],
             "methods": [{"solver": "ls", "cfg_by_budget": {"10": {...}, "60": {...}, "300": {...}}, "seeds": [0,1,2]}, ...]}
Resumable: a (instance, solver, cfg_hash, budget, seed) already present in trials.csv with phase=heldout is skipped.
Within each (instance, budget) block the (method, seed) runs are executed in a fixed pseudo-random order.
"""
import argparse
import csv
import json
import os
import random
import zlib
import subprocess
import sys
import time

SRC = os.path.dirname(os.path.abspath(__file__))
Q2 = os.path.dirname(SRC)
sys.path.insert(0, SRC)
from q2run import cfg_hash, TRIALS  # noqa: E402

PY = sys.executable


def done_keys():
    keys = set()
    if not os.path.exists(TRIALS):
        return keys
    with open(TRIALS) as f:
        for r in csv.DictReader(f):
            if r["phase"] == "heldout" and r["status"] == "ok":
                keys.add((r["instance"], r["solver"], r["cfg_hash"], float(r["budget"]), int(r["seed"])))
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--dry", action="store_true")
    o = ap.parse_args()
    plan = json.load(open(o.plan))
    form = plan["form"]
    have = done_keys()
    jobs = []
    for inst in plan["instances"]:
        iname = os.path.basename(inst).replace(".npz", "")
        for b in plan["budgets"]:
            block = []
            for mth in plan["methods"]:
                cfg = mth["cfg_by_budget"][str(int(b))]
                for sd in mth["seeds"]:
                    key = (iname, mth["solver"], cfg_hash(cfg), float(b), int(sd))
                    if key in have:
                        continue
                    block.append((inst, mth["solver"], cfg, b, sd))
            random.Random(zlib.crc32(f"{iname}|{b}".encode())).shuffle(block)
            jobs += block
    total = sum(j[3] for j in jobs)
    print(f"{len(jobs)} runs to do, {total / 3600:.2f} h of budget", flush=True)
    if o.dry:
        return
    env = dict(os.environ, OMP_NUM_THREADS="8", NUMBA_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", MKL_NUM_THREADS="8")
    for i, (inst, solver, cfg, b, sd) in enumerate(jobs):
        cmd = ["taskset", "-c", "0-7", PY, os.path.join(SRC, "q2run.py"), "--inst", inst, "--form", json.dumps(form),
               "--solver", solver, "--budget", str(b), "--seed", str(sd), "--cfg", json.dumps(cfg),
               "--phase", "heldout"]
        t = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=b * 4 + 600)
        res = [ln for ln in p.stdout.splitlines() if ln.startswith("RESULT ")]
        print(f"[{i + 1}/{len(jobs)}] {os.path.basename(inst)} {solver} b={b} s={sd} ({time.time() - t:.0f}s) "
              f"{res[-1][7:] if res else 'NO RESULT: ' + (p.stderr[-300:])}", flush=True)


if __name__ == "__main__":
    main()
