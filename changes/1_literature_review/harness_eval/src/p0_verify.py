"""P0: verify the PeakBaleen skeleton (mode=baleen) reproduces Baleen's PolicyUtilityServiceTimeSize2
ordering exactly on Region7 day 1 (same thresholds/labels per episode), via our launcher.

Runs (serialized under the train lock):
  A1, A2: stock policy PolicyUtilityServiceTimeSize2 through launch_train (two runs: run-to-run baseline)
  B1:     PolicyPeakBaleen mode=baleen
  C1:     PolicyPeakBaleen mode=solver, candidate=identity (solver returns Baleen's own greedy prefix
          through the full npz->subprocess->nested-order plumbing)
Compares per-episode thresholds (decisions file) and label sets (threshold < 35.599).
"""
import json
import os
import sys

import hecommon as HC

REGION = "Region7"


def train_args(exp, policy, ea):
    job = HC.load_fig9_job(HC.TRACES[REGION]["ml_job"])
    a = list(job["train_args"])
    a = HC.set_flag(a, "--exp", exp)
    a = HC.set_flag(a, "--output-base-dir", f"runs/p0/{exp}/train")
    a = HC.set_flag(a, "--policy", policy)
    a = HC.set_flag(a, "--eviction-age", f"{ea}")
    a = HC.remove_flag_nargs(a, "--train-models")   # no GBMs needed to compare labels
    return a


def run(exp, policy, cfg=None):
    env = HC.base_env()
    if cfg is not None:
        p = os.path.join(HC.WORK, "p0", f"{exp}.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(cfg, open(p, "w"), indent=1)
        env["HE_POLICY_CONFIG"] = p
    log = os.path.join(HC.LOGS, "p0", f"{exp}.log")
    args = [HC.BALEEN_PY, "-B", "-m", "launch_train"] + train_args(exp, policy, HC.TRACES[REGION]["ea_ml"])
    with HC.TRAIN_LOCK:
        rc, dt = HC.run_logged(args, log, env=env)
    out = HC.parse_train_outputs(log)
    print(exp, "rc", rc, f"{dt:.0f}s", out and out.get("thresholds"), flush=True)
    assert rc == 0, log
    return os.path.join(HC.WORK, out["thresholds"][0])


def main():
    runs = {}
    runs["A1"] = run("p0_stock_a", "PolicyUtilityServiceTimeSize2")
    runs["A2"] = run("p0_stock_b", "PolicyUtilityServiceTimeSize2")
    runs["B1"] = run("p0_skel", "PolicyPeakBaleen", {"mode": "baleen", "name": "peakbaleen_skel"})
    runs["C1"] = run("p0_ident", "PolicyPeakBaleen",
                     {"mode": "solver", "name": "peakbaleen_ident", "candidate": "IDENT",
                      "solver_py": HC.SOLVER_PY, "solver_cli": os.path.join(HC.SRC, "solve.py"),
                      "inst_path": os.path.join(HC.WORK, "p0", "ident_inst.npz"),
                      "sol_path": os.path.join(HC.WORK, "p0", "ident_sol.npz"), "skip_windows": 0})
    json.dump(runs, open(os.path.join(HC.WORK, "p0", "decisions.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
