"""H2' secondary analysis (pre-declared in PROTOCOL_v2_H2.md section 8, no verdict): rolling re-solve variant at 1 s on
the 6 test instances for PT, EIM, LS, MILP, CP-SAT, LP, pgreedy, greedy, seed 0; configurations from
results/plan_H2test.json (budget "1"). One p2roll process per method (cores 0-7 lock). Rows -> results/rolling_test.csv
(phase roll_test)."""
import json
import os
import subprocess
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
AREA = os.path.dirname(SRC)
P2 = os.path.dirname(AREA)


def main():
    plan = json.load(open(os.path.join(AREA, "results", "plan_H2test.json")))
    cfgs = {m["solver"]: m["cfg_by_budget"]["1"] for m in plan["methods"]}
    insts = [os.path.join(P2, rel) for rel in plan["instances"]]
    env = dict(os.environ, OMP_NUM_THREADS="8", NUMBA_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", MKL_NUM_THREADS="8")
    for sv in ["pt", "eim", "ls", "milp", "cpsat", "lp", "pgreedy", "greedy"]:
        cmd = ["taskset", "-c", "0-7", sys.executable, os.path.join(SRC, "p2roll.py"), "--insts", *insts,
               "--solver", sv, "--budget", "1", "--seed", "0", "--cfg", json.dumps(cfgs[sv]), "--phase", "roll_test",
               "--tag", f"roll_test_{sv}_b1", "--out", os.path.join(AREA, "results", "rolling_test.csv"),
               "--sols", os.path.join(AREA, "sols_roll")]
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        for line in p.stdout.splitlines():
            if line.startswith("RESULT "):
                print(line, flush=True)
        if p.returncode != 0:
            print("FAILED", sv, p.stderr[-1500:], flush=True)


if __name__ == "__main__":
    main()
