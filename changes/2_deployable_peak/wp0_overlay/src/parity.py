"""Train/serve parity of the `load` (and `tod`) features + end-to-end smoke tests of the overlay options.

  source wp0_overlay/env.sh && cd wp0_overlay && taskset -c 8-23 $BALEEN_PY -B src/parity.py

S1 (required smoke + parity): overlay training on Region7 s0 with --ap-feat-subset meta+block+chunk+load (authors'
   Fig 9 TrainCommand otherwise), dumping train_ap's df_X + per-row keys (ta_launch_train); then the authors'
   ReproduceCommand with the same subset, recording every feature vector the simulator's collect_features builds
   for day-1 accesses (ta_launch_sim). Parity: for every training row whose access (block, ts) the simulator also
   featurised, the 3 load values must be equal (exact; tolerance <= 1e-9 relative is the documented fallback).
S2 (optional options): training with --ap-feat-subset meta+block+chunk+load+tod --pf-feat-subset meta+load+tod,
   simulated with the same subsets and --ap-load-adapt-alpha -0.5: end-to-end run + parity of the admission
   load/tod values and of the prefetch models' load/tod inputs (train_prefetcher X vs the rows the simulator feeds
   ML-Range/ML-When).
S3 (neutrality of the adaptive-threshold code path): G1's frozen-trained default models simulated by the overlay with
   --ap-load-adapt-alpha 0 (g == 1) must give bit-identical metrics to the frozen simulator.
No evaluation claims: thresholds are not converged.
"""
import json
import os
import pickle
import random
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tacommon as T  # noqa: E402
import g1 as G  # noqa: E402

OUT = os.path.join(T.RESULTS, "parity")
LOGS = os.path.join(T.A, "logs", "parity")
REGION = "Region7"
PF_FEAT_NAMES = {"load": ["load_10m", "load_30m", "load_60m"], "tod": ["tod_sin", "tod_cos"]}  # = load_features.PF_FEAT_NAMES (asserted vs the dumps)


def train(tag, ap_subset, pf_subset=None):
    rec = os.path.join(OUT, f"train_{tag}.json")
    if os.path.exists(rec):
        return json.load(open(rec))
    job = T.load_fig9_job(T.BALEEN_JOB[REGION])
    targs = T.set_flag(list(job["train_args"]), "--exp", tag)
    targs = T.set_flag(targs, "--output-base-dir", f"runs/parity/{tag}/train")
    targs = T.set_flag(targs, "--ap-feat-subset", ap_subset)
    targs = T.set_flag(targs, "--suffix", f"/ws.20230325_{REGION}_0_0.1/fs_{ap_subset}/accs_15")
    if pf_subset:
        targs = T.set_flag(targs, "--pf-feat-subset", pf_subset)
    out, dt = T.run_train("overlay", targs, os.path.join(LOGS, tag, "train.log"),
                          dump_dir=os.path.join(OUT, "dumps", tag))
    r = dict(tag=tag, out=out, secs=dt, ap_subset=ap_subset, pf_subset=pf_subset)
    json.dump(r, open(rec, "w"), indent=1)
    return r


def sim(tag, train_rec, extra=(), record=True):
    job = T.load_fig9_job(T.BALEEN_JOB[REGION])
    base = T.fill_sim_args(list(job["sim_args"]), train_rec["out"])
    base = T.set_flag(base, "--ap-threshold", f"{T.BALEEN_TH[REGION]:.6f}")
    base = T.set_flag(base, "--ap-feat-subset", train_rec["ap_subset"])
    base = T.set_flag(base, "--job-id", tag)
    for i in range(0, len(extra), 2):
        base = T.set_flag(base, extra[i], extra[i + 1])
    rec_path = os.path.join(OUT, f"record_{tag}.pkl") if record else None
    rf = T.run_sim("overlay", base, f"runs/parity/{tag}/sim", os.path.join(LOGS, tag, "sim.log"), record=rec_path)
    return rf, rec_path


def _cmp(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = np.abs(a - b)
    rel = d / np.maximum(np.abs(b), 1e-300)
    rel[(a == b)] = 0.0
    return dict(n_values=int(a.size), n_exact=int((a == b).sum()), max_abs_diff=float(d.max()) if d.size else 0.0,
                max_rel_diff=float(rel.max()) if rel.size else 0.0)


def admission_parity(dump_dir, rec_path, groups):
    D = pickle.load(open(os.path.join(dump_dir, "admit_prep.pkl"), "rb"))
    R = pickle.load(open(rec_path, "rb"))
    cols = [c for g in groups for c in D["df_X"].columns if c.split("|")[0] == f"feat_{g}"]
    assert cols == [c for c in D["feat_cols"] if c.split("|")[0] in [f"feat_{g}" for g in groups]], (cols, D["feat_cols"])
    Xl = D["df_X"][cols].to_numpy(float)
    meta_cols = D["feat_cols"][:6]
    Xm = D["df_X"][meta_cols].to_numpy()
    n_extra = len(cols)
    tr, sv, meta_eq, idx = [], [], [], []
    for r, (blk, _ts0, _k, ts) in enumerate(D["keys"]):
        fv = R["admit"].get((blk, ts))
        if fv is None:
            continue
        idx.append(r)
        tr.append(Xl[r])
        sv.append(fv[18:18 + n_extra])
        meta_eq.append(list(Xm[r]) == list(fv[:6]))
    tr, sv = np.array(tr), np.array(sv)
    res = dict(groups=groups, cols=cols, n_train_rows=len(D["keys"]), n_rows_matched=len(idx),
               n_sim_accesses_recorded=len(R["admit"]), sim_collect_features_calls=R["admit_calls"],
               sim_same_access_load_mismatches=R["admit_mismatch"], meta_equal_frac=float(np.mean(meta_eq)),
               all=_cmp(tr, sv))
    rng = random.Random(0)
    samp = rng.sample(range(len(idx)), min(10000, len(idx)))
    res["sample10k"] = _cmp(tr[samp], sv[samp])
    for j, c in enumerate(cols):
        res[f"col_{c}"] = _cmp(tr[:, j], sv[:, j])
    res["nonzero_frac"] = float(np.mean(tr != 0))
    res["train_value_range"] = [float(tr.min()), float(tr.max())]
    res["pass"] = len(idx) >= 10000 and res["all"]["max_rel_diff"] <= 1e-9
    res["exact"] = res["all"]["n_exact"] == res["all"]["n_values"]
    return res


def prefetch_parity(dump_dir, rec_path, groups):
    R = pickle.load(open(rec_path, "rb"))
    names = [n for g in groups for n in PF_FEAT_NAMES[g]]
    out = {}
    for f in sorted(os.listdir(dump_dir)):
        if not f.startswith("prefetch_prep_"):
            continue
        D = pickle.load(open(os.path.join(dump_dir, f), "rb"))
        assert D["feat_names"][6:6 + len(names)] == names, D["feat_names"]
        X = np.asarray(D["X"], float)
        tr, sv = [], []
        for r, (blk, ts) in enumerate(D["keys"]):
            row = R["pf"].get((blk, ts))
            if row is None:
                continue
            tr.append(X[r, 6:6 + len(names)])
            sv.append(row[6:6 + len(names)])
        res = dict(n_train_rows=len(X), n_rows_matched=len(tr), n_sim_rows_recorded=len(R["pf"]),
                   sim_prefetch_feature_rows=R["pf_calls"], feat_names=D["feat_names"])
        if tr:
            res["all"] = _cmp(np.array(tr), np.array(sv))
            res["exact"] = res["all"]["n_exact"] == res["all"]["n_values"]
        out[f.replace(".pkl", "")] = res
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    pool = ThreadPoolExecutor(max_workers=4)
    summary = {}
    # S3 needs G1's frozen-trained models (written by g1.py)
    futs3 = {}
    for region in ("Region7", "Region6"):
        rec = os.path.join(G.OUT, f"train_g1_{region}_trainF.json")
        if os.path.exists(rec):
            tr = json.load(open(rec))
            job = T.load_fig9_job(T.BALEEN_JOB[region])
            base = T.fill_sim_args(list(job["sim_args"]), tr["out"])
            base = T.set_flag(base, "--ap-threshold", f"{T.BALEEN_TH[region]:.6f}")
            base = T.set_flag(base, "--ap-load-adapt-alpha", "0")
            tag = f"s3_{region}_modelF_alpha0"
            base = T.set_flag(base, "--job-id", tag)
            futs3[region] = pool.submit(T.run_sim, "overlay", base, f"runs/parity/{tag}/sim",
                                        os.path.join(LOGS, tag, "sim.log"))
    # S1
    t1 = train("smoke_R7_load", "meta+block+chunk+load")
    f1 = pool.submit(sim, "smoke_R7_load", t1)
    # S2
    t2 = train("smoke_R7_loadtod_pf", "meta+block+chunk+load+tod", "meta+load+tod")
    f2 = pool.submit(sim, "smoke_R7_loadtod_pf_adapt", t2,
                     ("--pf-feat-subset", "meta+load+tod", "--ap-load-adapt-alpha", "-0.5"))
    rf1, rec1 = f1.result()
    r1 = T.load_result(rf1)["results"]
    summary["S1"] = dict(train=t1, result_file=rf1, sim_P100=r1["PeakServiceTimeUtil1"], sim_WR=r1["FlashWriteRate"],
                         parity_load=admission_parity(os.path.join(OUT, "dumps", "smoke_R7_load"), rec1, ["load"]))
    rf2, rec2 = f2.result()
    r2 = T.load_result(rf2)["results"]
    summary["S2"] = dict(train=t2, result_file=rf2, sim_P100=r2["PeakServiceTimeUtil1"], sim_WR=r2["FlashWriteRate"],
                         parity_admit_load_tod=admission_parity(os.path.join(OUT, "dumps", "smoke_R7_loadtod_pf"), rec2,
                                                                ["load", "tod"]),
                         parity_prefetch_load_tod=prefetch_parity(os.path.join(OUT, "dumps", "smoke_R7_loadtod_pf"),
                                                                  rec2, ["load", "tod"]))
    s3 = {}
    for region, f in futs3.items():
        rf = f.result()
        ref = os.path.join(T.WORKS["frozen"], "runs", "g1", f"g1_{region}_modelF_simF", "sim")
        ref = T.result_files("frozen", os.path.relpath(ref, T.WORKS["frozen"]))[0]
        s3[region] = G.compare_results(ref, rf)
    summary["S3"] = s3
    json.dump(summary, open(os.path.join(T.RESULTS, "parity_summary.json"), "w"), indent=1, default=str)
    print(json.dumps({"S1_parity": summary["S1"]["parity_load"]["pass"], "S1_exact": summary["S1"]["parity_load"]["exact"],
                      "S1_rows": summary["S1"]["parity_load"]["n_rows_matched"],
                      "S2_admit_exact": summary["S2"]["parity_admit_load_tod"]["exact"],
                      "S2_pf": {k: v.get("exact") for k, v in summary["S2"]["parity_prefetch_load_tod"].items()},
                      "S3": {k: v["metrics_bit_identical"] for k, v in s3.items()}}, indent=1))


if __name__ == "__main__":
    main()
