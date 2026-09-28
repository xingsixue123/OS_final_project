"""Stage A: execute the authors' own notebooks (copies in work/notebooks) with nbconvert.

  python repro/stage_a.py            # fig-09 from results_release.csv.gz -> must print 28.11/31.95/34.63
  python repro/stage_a.py --example  # example.ipynb on our README smoke runs -> expect ~16.1%

Executed notebooks are saved to work/results/notebooks/.
"""
import argparse
import json
import os
import re
import subprocess

import common as C

EXPECTED_FIG9_AVG = {"Baleen": 28.11, "Baleen (No Prefetch)": 31.61, "CoinFlip": 34.63, "RejectX": 31.95}


def execute(nb_rel):
    out_dir = os.path.join(C.WORK, "results", "notebooks")
    os.makedirs(out_dir, exist_ok=True)
    nb_dir = os.path.join(C.WORK, "notebooks", os.path.dirname(nb_rel))
    subprocess.check_call(C.SANDBOX + [os.path.join(C.ROOT, "env", "bin", "jupyter"), "nbconvert", "--to", "notebook",
                           "--execute", "--ExecutePreprocessor.timeout=1800",
                           "--output-dir", out_dir, os.path.basename(nb_rel)], cwd=nb_dir)
    return os.path.join(out_dir, os.path.basename(nb_rel))


def outputs(nb_path):
    nb = json.load(open(nb_path))
    for c in nb["cells"]:
        for o in c.get("outputs", []):
            t = o.get("text") or o.get("data", {}).get("text/plain")
            if t:
                yield "".join(t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--example", action="store_true")
    a = ap.parse_args()
    if a.example:
        path = execute("example/example.ipynb")
        txt = "\n".join(outputs(path))
        m = re.search(r"Savings in Peak Load from Baleen on Region1, Sample 0\s+([\d.]+)", txt)
        print(f"example.ipynb saving: {m.group(1) if m else 'NOT FOUND'} (authors: 16.114)")
        return
    path = execute("paper-figs/fig-09-202309.ipynb")
    txt = "\n".join(outputs(path))
    ok = True
    for label, exp in EXPECTED_FIG9_AVG.items():
        m = re.search(rf"^{re.escape(label)}\s+(?:[\d.]+\s+){{7}}([\d.]+)\s*$", txt, re.M)
        got = float(m.group(1)) if m else None
        ok &= got == exp
        print(f"Fig 9 avg peak load {label:22s} notebook={got}  paper={exp}  {'OK' if got == exp else 'MISMATCH'}")
    macros = re.findall(r"\\newcommand\{\\(PeakSavings\w+)\}\{([\d.]+)", txt)
    for k, v in macros:
        print(f"  {k} = {v}%")
    print("Stage A:", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
