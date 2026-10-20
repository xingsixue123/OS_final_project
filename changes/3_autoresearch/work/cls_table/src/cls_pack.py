"""AR step 1 (Baleen env, numpy): one TRAINING-WINDOW replay pack per (instance, base arm A/B, retrain k) for the load x
access-class table. Copied from wp10_schedule/src/e2_pack.py (same day-1 replay, budget W1 and K = 6 load buckets at
the day-1 access-level quantiles (0.25, 0.5, 0.75, 0.9, 0.97) of load_10m); AR adds the access class of every pack
access (CLASS_DIMS, the overlay v4 CLASS_FEATURES on the simulator's own features). Only day-1 data enter a pack.
-> work/packs/<mode>/<inst>_<arm>_r<k>.npz

  source env.sh && src/sbx.sh src/cls_pack.py --mode dev --insts ... --arms B --reps 1
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402
sys.path.insert(0, C.WORK)
import emu  # noqa: E402
import schedemu as SE  # noqa: E402

QUANTILES = (0.25, 0.5, 0.75, 0.9, 0.97)
WRMAP0 = {("Region7", "baleen"): (-1.288, 1.177), ("Region6", "baleen"): (-0.770, 1.146)}
WRMAP_POOLED = (-1.029, 1.1615)                    # mean of the two dev baleen maps (as WP10 for other regions)
ORIG, LOAD = "meta+block+chunk", "meta+block+chunk+load"
CLASS_DIMS = [dict(feat="endoff", edges=[float(8 * (1 << 20))])]     # J = 2: end offset <= / > 8 MiB (WP2 big-offset)


def emu_target(region):
    a, b = WRMAP0.get((region, "baleen"), WRMAP_POOLED)
    return float(np.exp((np.log(C.TARGET_WR) - a) / b))


def train_record(mode, arm, inst, rep):
    key = f"{arm}_baleen_{inst}_r{rep}"
    if mode == "dev" and inst in C.DEV8:
        return json.load(open(os.path.join(C.WP2, "results", "train", f"{key}.json")))
    return json.load(open(os.path.join(C.RESULTS, "train", f"{key}.json")))


def model_path(rec):
    """the copied model file (cls.py copies WP2 models into work/models/<key>/; own trains already live in WORK)."""
    p = rec["out"]["model_admit_threshold_binary"][0]
    cp = os.path.join(C.WORK, "models", rec["key"], os.path.basename(p))
    return cp if os.path.exists(cp) else p


def make_pack(mode, inst, arm, rep):
    out = os.path.join(C.WORK, "packs", mode, f"{inst}_{arm}_r{rep}.npz")
    if os.path.exists(out):
        return out
    E = emu.get(inst)
    S = SE.SchedEmu(E, "day1")
    rec = train_record(mode, arm, inst, rep)
    score = E.scores(model_path(rec), ORIG if arm == "A" else LOAD)
    sc = score[S.idx]
    region = inst.split("_")[0]
    base = S.budget_at_emu_wr(sc, emu_target(region))
    lo = S.load_sub[S.admissible]
    edges = np.quantile(lo, QUANTILES)
    assert np.all(np.diff(edges) > 0), edges
    bucket = np.searchsorted(edges, S.load_sub, side="right").astype(np.int64)
    cls = E.class_index(CLASS_DIMS)[S.idx].astype(np.int64)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, score=sc, load=S.load_sub, bucket=bucket, cls=cls, edges=edges, starts=S.starts,
                        acc_w=S.acc_w, stc=S.stc, st_full=S.st_full, nch=S.nch, C0=S.C0, admissible=S.admissible,
                        W1=base["wch"], plain_theta=base["theta"], plain_peak=base["peak"], emu_target=emu_target(region),
                        US=SE.US, model=os.path.basename(model_path(rec)), class_dims=json.dumps(CLASS_DIMS))
    r = S.run(sc, np.ones(len(sc)), W=base["wch"])
    assert abs(r["peak"] - base["peak"]) < 1e-9
    print(f"[pack] {inst} {arm} r{rep}: W1={base['wch']:.0f} plain peak {base['peak']:.3f} edges {np.round(edges, 2)} "
          f"class shares {np.bincount(cls, minlength=2) / len(cls)}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dev", "test"], default="dev")
    ap.add_argument("--insts", nargs="+", required=True)
    ap.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--arms", nargs="+", default=["A", "B"])
    o = ap.parse_args()
    C.configure(o.mode)
    for inst in o.insts:
        assert not C.is_reserve(inst)
        if o.mode == "dev":
            assert inst in C.DEV and inst not in C.FORBIDDEN_DEV
        else:
            assert os.path.exists(os.path.join(C.TEST_DIR, "TEST_GO")) and inst in C.TEST
        for arm in o.arms:
            for k in o.reps:
                make_pack(o.mode, inst, arm, k)


if __name__ == "__main__":
    main()
