"""AR union: day-1 instance dumps (day1_<key>.npz) for the F1-label solver, FROZEN code only, exactly as
wp9_region5/src/prep.py do_dumps (day-1 branch: the authors' Baleen TrainCommand for that sample, --policy
PolicyPeakBaleen3 via launch_train, --train-models removed, skip_windows 0). Copied functions; no outcome is read.

  source env.sh && src/sbx.sh src/prep_day1.py --mode dev --keys Region1_s0
  (test mode: the pool's jobs_test.json / inst_test, allowed before TEST_GO as an instance-dump prerequisite)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402

FROZEN = C.WORK_FROZEN


def remove_flag_nargs(args, flag):
    out, i = [], 0
    while i < len(args):
        if args[i] == flag:
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                i += 1
        else:
            out.append(args[i])
            i += 1
    return out


def dump_day1(key):
    J = C.JOBS[key]
    exp = f"prep_day1_{key}"
    inst = os.path.join(C.INST_DIR, f"day1_{key}.npz")
    if os.path.exists(inst):
        return inst
    a = list(J["baleen"]["train_args"])
    a = C.set_flag(a, "--exp", exp)
    a = C.set_flag(a, "--output-base-dir", f"runs/prep/{exp}/train")
    a = C.set_flag(a, "--policy", "PolicyPeakBaleen3")
    a = remove_flag_nargs(a, "--train-models")
    cfg = {"mode": "dump", "name": f"pb3_day1_{key}", "target_wr": C.TARGET_WR, "skip_windows": 0, "inst_path": inst,
           "dump_access": True}
    p = os.path.join(C.W, "results", "cfg_prep", f"{exp}.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(cfg, open(p, "w"), indent=1)
    env = C.base_env(threads=2, work=FROZEN)
    env["HE_POLICY_CONFIG"] = p
    lp = os.path.join(C.W, "logs", "prep", exp, "train.log")
    with C.TrainLock():
        rc, dt = C.run_logged(["-m", "launch_train"] + a, lp, env=env, work=FROZEN, cpuset=C.cpus())
    if rc != 0 or not os.path.exists(inst):
        raise RuntimeError(f"day-1 dump failed rc={rc}: {lp}")
    print(f"[dump] {inst} {os.path.getsize(inst) / 1e6:.1f} MB ({dt:.0f}s)", flush=True)
    return inst


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dev", "test"], required=True)
    ap.add_argument("--keys", nargs="+", required=True)
    o = ap.parse_args()
    C.configure(o.mode)
    for k in o.keys:
        assert not C.is_reserve(k)
        assert (k in C.DEV and k not in C.FORBIDDEN_DEV) if o.mode == "dev" else k in C.TEST
        dump_day1(k)
