"""Solve the test label sets (PROTOCOL_v2_H3 §7.4): designs F1PT and F1CPSAT, seeds 1-6, on wp3_test/inst/day1_<key>.npz
(frozen configurations: explore/q2/plan_F1.json cfg_by_budget["10"] for pt / cpsat, single level f = 1.0, 10 s,
8 numba threads -- exactly as WP2 dev). Waits for each day-1 instance to exist. 4 concurrent solver processes.
  cd wp3_test && $BALEEN_PY -B src/run_labels.py"""
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402


def one(job):
    inst, design, seed = job
    out = os.path.join(C.W, "labels", f"{inst}_{design}_s{seed}.npz")
    while not os.path.exists(os.path.join(C.W, "inst", f"day1_{inst}.npz")):
        time.sleep(15)
    if os.path.exists(out):
        return
    rc, dt = C.run_logged(["../src/labels.py", "--inst", inst, "--design", design, "--seed", str(seed)],
                          os.path.join(C.W, "logs", "labels", f"{inst}_{design}_s{seed}.log"),
                          env=C.base_env(threads=8), py=C.SOLVER_PY, cpuset=C.cpus())
    print(f"{inst} {design} s{seed} rc={rc} {dt:.0f}s", flush=True)


if __name__ == "__main__":
    jobs = [(i, d, s) for s in (1, 2, 3, 4, 5, 6) for d in ("F1PT", "F1CPSAT") for i in C.TEST]
    with ThreadPoolExecutor(4) as ex:
        list(ex.map(one, jobs))
