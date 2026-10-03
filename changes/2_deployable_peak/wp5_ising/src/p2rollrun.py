"""Rolling-variant driver: for each solver, its tuned configuration at the budget (results/plan_dev.json), one p2roll
process over the 8 dev instances (seed 0, phase roll), cores 0-7 lock."""
import argparse
import json
import os
import subprocess
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
AREA = os.path.dirname(SRC)
DEV = [os.path.join(AREA, "inst", f"full_{r}_s{s}.npz") for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--solvers", required=True)
    ap.add_argument("--insts", nargs="+", default=DEV)
    ap.add_argument("--seed", type=int, default=0)
    o = ap.parse_args()
    plan = json.load(open(os.path.join(AREA, "results", "plan_dev.json")))["solvers"]
    env = dict(os.environ, OMP_NUM_THREADS="8", NUMBA_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", MKL_NUM_THREADS="8")
    for sv in o.solvers.split(","):
        cfg = plan[sv][f"{o.budget:g}"]["cfg"]
        cmd = ["taskset", "-c", "0-7", sys.executable, os.path.join(SRC, "p2roll.py"), "--insts", *o.insts,
               "--solver", sv, "--budget", str(o.budget), "--seed", str(o.seed), "--cfg", json.dumps(cfg),
               "--phase", "roll", "--tag", f"roll_{sv}_b{o.budget:g}"]
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        for line in p.stdout.splitlines():
            if line.startswith("RESULT "):
                print(line, flush=True)
        if p.returncode != 0:
            print("FAILED", sv, p.stderr[-1500:], flush=True)


if __name__ == "__main__":
    main()
