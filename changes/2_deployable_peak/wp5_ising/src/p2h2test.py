"""H2' TEST driver -- runs PROTOCOL_v2_H2.md (committed fd54e76) exactly; no configuration, seed, instance or criterion
is read from anywhere but results/plan_H2test.json (committed with the protocol).

  python p2h2test.py [--dry]
Order (protocol section 6): instance-major (Region7 s0.4, s0.5, s0.6, Region6 s0.4, s0.5, s0.6); per instance the budgets
10, 3, 1 s; inside an (instance, budget) block the (method, seed) runs in the order
random.Random(zlib.crc32(f"{instance}|{budget}".encode())).shuffle(block), instance = file stem (e.g. full_Region7_s0.4),
budget formatted with :g (as phase-1 q2heldout.py), block built in plan method order x seed order. One p2run process per
run (cores 0-7 lock, affinity asserted, 8 threads), rows to trials.csv with phase h2test. Resumable: a run whose row key
is already present with status ok is skipped (a crash would leave no ok row and is re-run once, logged).
The instance files' sha256 are checked against the protocol before the first run.
"""
import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import zlib

SRC = os.path.dirname(os.path.abspath(__file__))
AREA = os.path.dirname(SRC)
P2 = os.path.dirname(AREA)
sys.path.insert(0, SRC)
from p2run import done_keys, row_key  # noqa: E402
from q2run import cfg_hash  # noqa: E402

SHA = {"full_Region7_s0.4": "42eb1113e0d50d5c52ef81117d89404bab9931af9fae55c61b44763ecbef9239",
       "full_Region7_s0.5": "791b4e8296c3b3bd04b2583a8dc5c9eec31f2ea2724a76b22857350611bcb9ee",
       "full_Region7_s0.6": "271c98db1fe41c65558710d2572858626c35ffb596fd8608208705197d04d6b5",
       "full_Region6_s0.4": "942375907df7a04fdbec509f0aa6280af258205156ab006e1e44241a594dc5ca",
       "full_Region6_s0.5": "f39046c3e51cada0be9f24d46b50768ad8049a40c85e5e2c7f8b14cc1c940b84",
       "full_Region6_s0.6": "9f6fe5a096f2e2f9de27400c23975657221c54335068171da1d9f2cbcf511ab8"}
TRIALS = os.path.join(AREA, "trials.csv")


def jobs():
    plan = json.load(open(os.path.join(AREA, "results", "plan_H2test.json")))
    out = []
    for rel in plan["instances"]:
        path = os.path.join(P2, rel)
        iname = os.path.basename(path).replace(".npz", "")
        for b in plan["budgets"]:                     # [10, 3, 1]
            block = []
            for m in plan["methods"]:
                cfg = m["cfg_by_budget"][f"{b:g}"]
                for sd in m["seeds"]:
                    block.append((path, iname, m["solver"], cfg, b, sd))
            random.Random(zlib.crc32(f"{iname}|{b:g}".encode())).shuffle(block)
            out += block
    return plan, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    o = ap.parse_args()
    plan, js = jobs()
    for iname, h in SHA.items():
        p = os.path.join(P2, "wp1_offline", "inst", f"{iname}.npz")
        assert hashlib.sha256(open(p, "rb").read()).hexdigest() == h, f"sha256 mismatch {p}"
    print(f"sha256 of the 6 test instances verified; {len(js)} runs planned", flush=True)
    have = done_keys(TRIALS)
    env = dict(os.environ, OMP_NUM_THREADS="8", NUMBA_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", MKL_NUM_THREADS="8")
    for i, (path, iname, sv, cfg, b, sd) in enumerate(js):
        tag = f"h2test_{sv}_b{b:g}_s{sd}"
        key = row_key("h2test", iname, sv, cfg_hash(cfg), float(b), sd, tag)
        if o.dry:
            print(i, iname, b, sv, sd, key, flush=True)
            continue
        if key in have:
            print(f"[{i + 1}/{len(js)}] SKIP done {iname} {sv} b={b} s={sd}", flush=True)
            continue
        cmd = ["taskset", "-c", "0-7", sys.executable, os.path.join(SRC, "p2run.py"), "--insts", path,
               "--form", json.dumps(plan["form"]), "--solver", sv, "--budget", str(b), "--seed", str(sd),
               "--cfg", json.dumps(cfg), "--phase", "h2test", "--tag", tag, "--trials", TRIALS,
               "--sols", os.path.join(AREA, "sols")]
        t = time.time()
        p = subprocess.run(cmd, capture_output=True, text=True, env=env)
        res = [ln for ln in p.stdout.splitlines() if ln.startswith("RESULT ")]
        print(f"[{i + 1}/{len(js)}] {iname} b={b} {sv} s={sd} ({time.time() - t:.0f}s) "
              f"{res[-1][7:] if res else 'NO RESULT rc=%d %s' % (p.returncode, p.stderr[-400:])}", flush=True)


if __name__ == "__main__":
    main()
