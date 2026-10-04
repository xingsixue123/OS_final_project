"""Solve every (instance, design, seed) label set (labels.py) that is missing; 2 concurrent solver processes.
  source wp2_deployed/env.sh && cd wp2_deployed && $BALEEN_PY -B src/run_labels.py [--seeds 1 2 3] [--designs ...]"""
import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402

DESIGNS = ["P0", "T2", "C2", "F1PT", "F1EIM", "F1CPSAT"]


def one(job):
    inst, design, seed = job
    out = os.path.join(C.LABELS, f"{inst}_{design}_s{seed}.npz")
    if os.path.exists(out):
        return
    env = C.base_env(threads=8)
    rc, dt = C.run_logged(["../src/labels.py", "--inst", inst, "--design", design, "--seed", str(seed)],
                          os.path.join(C.LOGS, "labels", f"{inst}_{design}_s{seed}.log"), env=env, py=C.SOLVER_PY,
                          cpuset=C.BUSY_CPUS)
    print(f"{inst} {design} s{seed} rc={rc} {dt:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--designs", nargs="+", default=DESIGNS)
    ap.add_argument("-j", type=int, default=2)
    o = ap.parse_args()
    jobs = [(i, d, s) for s in o.seeds for d in o.designs for i in C.DEV]
    with ThreadPoolExecutor(o.j) as ex:
        list(ex.map(one, jobs))


if __name__ == "__main__":
    main()
