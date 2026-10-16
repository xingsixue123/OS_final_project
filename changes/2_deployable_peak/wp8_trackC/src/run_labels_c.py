"""Batch driver (resumable): Track C label solves (labels_c.py, solver env) and student fits (student.py, Baleen env),
in dependency phases. Every finished solve is appended to results/ledger_labels.csv (one row per (inst, design, seed)).
  source env.sh && python3 src/run_labels_c.py --phase A [-j 1]
Phases: A = F1PT4 ANC3 ANC10 ANC30 TK10 TK72 ANC10TK10 | B = student(F1PT4) | C = STU10R1 STU30R1 |
        D = student(STU10R1) | E = STU10R2
"""
import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(HERE)
LABELS = os.path.join(W, "labels")
LEDGER = os.path.join(W, "results", "ledger_labels.csv")
DEV = [f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]
PHASES = {"A": ("solve", ["F1PT4", "ANC3", "ANC10", "ANC30", "TK10", "TK72", "ANC10TK10"]),
          "B": ("student", ["F1PT4"]),
          "C": ("solve", ["STU10R1", "STU30R1"]),
          "D": ("student", ["STU10R1"]),
          "E": ("solve", ["STU10R2"]),
          "F": ("solve", ["ANC10CP"])}         # classical control: anchored energy by CP-SAT
sys.path.insert(0, HERE)


def ledger_row(inst, design, seed, stage):
    import csv
    import fcntl
    st = json.load(open(os.path.join(LABELS, f"{inst}_{design}_s{seed}.json")))
    row = dict(key=f"{inst}_{design}_s{seed}", stage=stage, inst=inst, design=design, seed=seed,
               n_label=st["n_label"], n_baleen=st["n_baleen"], jaccard_vs_baleen=round(st["jaccard_vs_baleen"], 4),
               hamming_vs_baleen=st["hamming_vs_baleen"], label_peak_util=round(st["label_peak_util"], 4),
               baleen_peak_util=round(st["baleen_peak_util"], 4), label_top3=round(st["label_top3"], 4),
               label_top10=round(st["label_top10"], 4), label_mean_util=round(st["label_mean_util"], 4),
               zero_value_labels=st["zero_value_labels"], single_access_labels=st.get("single_access_labels", ""),
               wall=round(st["info"]["wall"], 2), wall_pt=round(st["info"]["wall_pt"], 2),
               ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
    with open(LEDGER + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        keys = set()
        if os.path.exists(LEDGER):
            keys = {r["key"] for r in csv.DictReader(open(LEDGER))}
        if row["key"] not in keys:
            new = not os.path.exists(LEDGER)
            with open(LEDGER, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(row))
                if new:
                    w.writeheader()
                w.writerow(row)
        fcntl.flock(lk, fcntl.LOCK_UN)


def one(job):
    kind, inst, design, seed = job
    if kind == "solve":
        out = os.path.join(LABELS, f"{inst}_{design}_s{seed}.npz")
        if not os.path.exists(out):
            log = os.path.join(W, "logs", "labels", f"{inst}_{design}_s{seed}.log")
            os.makedirs(os.path.dirname(log), exist_ok=True)
            with open(log, "w") as f:
                rc = subprocess.call([os.path.join(HERE, "run.sh"), "solver", "../src/labels_c.py", "--inst", inst,
                                      "--design", design, "--seed", str(seed)], stdout=f, stderr=subprocess.STDOUT)
            print(f"{inst} {design} s{seed} rc={rc}", flush=True)
            if rc != 0:
                return
        ledger_row(inst, design, seed, "table")
    else:
        out = os.path.join(LABELS, f"student_{inst}_{design}_s{seed}.npz")
        if os.path.exists(out):
            return
        log = os.path.join(W, "logs", "labels", f"student_{inst}_{design}_s{seed}.log")
        with open(log, "w") as f:
            rc = subprocess.call([os.path.join(HERE, "run.sh"), "baleen", "../src/student.py", "--inst", inst,
                                  "--design", design, "--seed", str(seed)], stdout=f, stderr=subprocess.STDOUT)
        print(f"student {inst} {design} s{seed} rc={rc}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", nargs="+", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("-j", type=int, default=1)
    o = ap.parse_args()
    assert o.j <= 2
    for ph in o.phase:
        kind, designs = PHASES[ph]
        jobs = [(kind, i, d, s) for d in designs for s in o.seeds for i in DEV]
        with ThreadPoolExecutor(o.j) as ex:
            list(ex.map(one, jobs))
        print(f"phase {ph} done", flush=True)


if __name__ == "__main__":
    main()
