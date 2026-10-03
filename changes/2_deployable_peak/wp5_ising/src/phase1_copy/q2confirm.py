"""Dev confirmation with fresh seeds (removes the seed-selection bias of the tuning 'best trial') -- DEV ONLY.

  python q2confirm.py --form '{"name":"F1"}' --solvers ls,milp,cpsat,pt,eim --budgets 10,60 --seeds 101,102
Configs: 10 s -> best of the b10 study, 60 s -> best of the b60 study. Runs are sequential on cores 0-7 and logged in
trials.csv with phase=devconfirm.
"""
import argparse
import json
import os
import subprocess
import sys

SRC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SRC)
from q2plan import best_cfg  # noqa: E402
from q2tune import DEV  # noqa: E402

PY = sys.executable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", required=True)
    ap.add_argument("--solvers", required=True)
    ap.add_argument("--budgets", default="10,60")
    ap.add_argument("--seeds", default="101,102")
    ap.add_argument("--extra-cfg", default="{}", help="json merged into every config (e.g. level_weights)")
    ap.add_argument("--phase", default="devconfirm")
    o = ap.parse_args()
    form = json.loads(o.form)
    fname = form["name"] + "".join(f"_{k}{v}" for k, v in sorted(form.items()) if k != "name")
    env = dict(os.environ, OMP_NUM_THREADS="8", NUMBA_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", MKL_NUM_THREADS="8")
    for b in [int(x) for x in o.budgets.split(",")]:
        for sd in [int(x) for x in o.seeds.split(",")]:
            for solver in o.solvers.split(","):
                cfg, _, _ = best_cfg(fname, solver, b)
                if cfg is None:
                    cfg, _, _ = best_cfg(fname, solver, 10)
                cfg = dict(cfg, **json.loads(o.extra_cfg))
                for inst in DEV:
                    cmd = ["taskset", "-c", "0-7", PY, os.path.join(SRC, "q2run.py"), "--inst", inst, "--form",
                           json.dumps(form), "--solver", solver, "--budget", str(b), "--seed", str(sd), "--cfg",
                           json.dumps(cfg), "--phase", o.phase]
                    p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=b * 4 + 300)
                    res = [ln for ln in p.stdout.splitlines() if ln.startswith("RESULT ")]
                    print(f"{solver} b={b} s={sd} {os.path.basename(inst)}: {res[-1][7:220] if res else p.stderr[-300:]}",
                          flush=True)


if __name__ == "__main__":
    main()
