"""E2 step 1 (Baleen env, numpy): one TRAINING-WINDOW replay pack per (instance, base arm A/B, retrain k).
Only day-1 data enter a pack: the retrain's admission-GBM scores on day-1 accesses (episodes with >= 1 day-1 access,
admission allowed only in windows 0-143), causal load_10m at those accesses, the day-1 no-cache window loads, the
budget W1 (P1 definition, PROGRESS.md E1 PRE-REGISTRATION) and the K = 6 load-bucket edges = day-1 access-level quantiles of load_10m
at (0.25, 0.5, 0.75, 0.9, 0.97). -> work/packs/<mode>/<inst>_<arm>_r<k>.npz

  source env.sh && src/sbx.sh src/e2_pack.py --mode dev [--reps 1 2 3]
  (test mode reads the E4 instances; it is used only after PROTOCOL_v2_H5 is committed)
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
WRMAP_POOLED = (-1.029, 1.1615)                    # mean of the two dev baleen maps (E4 region has no map)
ORIG, LOAD = "meta+block+chunk", "meta+block+chunk+load"


def emu_target(region):
    a, b = WRMAP0.get((region, "baleen"), WRMAP_POOLED)
    return float(np.exp((np.log(C.TARGET_WR) - a) / b))


def train_record(mode, arm, inst, rep):
    key = f"{arm}_baleen_{inst}_r{rep}"
    if mode == "dev":
        return json.load(open(os.path.join(C.WP2, "results", "train", f"{key}.json")))
    return json.load(open(os.path.join(C.RESULTS, "train", f"{key}.json")))


def make_pack(mode, inst, arm, rep):
    out = os.path.join(C.WORK, "packs", mode, f"{inst}_{arm}_r{rep}.npz")
    if os.path.exists(out):
        return out
    E = emu.get(inst)
    S = SE.SchedEmu(E, "day1")
    rec = train_record(mode, arm, inst, rep)
    score = E.scores(rec["out"]["model_admit_threshold_binary"][0], ORIG if arm == "A" else LOAD)
    sc = score[S.idx]
    region = inst.split("_")[0]
    base = S.budget_at_emu_wr(sc, emu_target(region))
    lo = S.load_sub[S.admissible]
    edges = np.quantile(lo, QUANTILES)
    assert np.all(np.diff(edges) > 0), edges
    bucket = np.searchsorted(edges, S.load_sub, side="right").astype(np.int64)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, score=sc, load=S.load_sub, bucket=bucket, edges=edges, starts=S.starts,
                        acc_w=S.acc_w, stc=S.stc, st_full=S.st_full, nch=S.nch, C0=S.C0, admissible=S.admissible,
                        W1=base["wch"], plain_theta=base["theta"], plain_peak=base["peak"], emu_target=emu_target(region),
                        US=SE.US, model=os.path.basename(rec["out"]["model_admit_threshold_binary"][0]))
    # self-check: the pack's plain replay equals SchedEmu's
    r = S.run(sc, np.ones(len(sc)), W=base["wch"])
    assert abs(r["peak"] - base["peak"]) < 1e-9
    print(f"[pack] {inst} {arm} r{rep}: W1={base['wch']:.0f} plain peak {base['peak']:.3f} edges {np.round(edges, 2)}", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dev", "test", "dryrun"], default="dev")
    ap.add_argument("--insts", nargs="+", default=None)
    ap.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("--arms", nargs="+", default=["A", "B"])
    o = ap.parse_args()
    C.configure(o.mode)
    insts = o.insts or {"dev": C.DEV, "test": C.TEST, "dryrun": C.DRY}[o.mode]
    assert all(i in {"dev": C.DEV, "test": C.TEST, "dryrun": C.DRY}[o.mode] for i in insts)
    if o.mode == "test":
        assert os.path.exists(os.path.join(C.W, "TEST_GO")), "E4 test data only after PROTOCOL_v2_H5 is committed"
    for inst in insts:
        assert not C.is_reserve(inst) and inst not in C.FORBIDDEN_DEV
        for arm in o.arms:
            for k in o.reps:
                make_pack(o.mode, inst, arm, k)


if __name__ == "__main__":
    main()
