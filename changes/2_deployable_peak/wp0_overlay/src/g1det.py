"""G1-det: strict bit-exact form of gate G1 for Baleen training. The frozen artifact's training is not deterministic
run-to-run only because episode generation uses Pool.imap_unordered (episode order -> row order, score-tie order at
the label boundary, block-level train/test split). Our launcher (ta_launch_train, TA_DETERMINISTIC=1) pins that to the
ordered Pool.imap and PYTHONHASHSEED=0, identically for both code bases. Then, per dev trace:
  frozen train x2, overlay train x2 (authors' Fig 9 TrainCommand, defaults)  -> dumps + model files must be identical
  frozen train -> frozen sim  vs  overlay train -> overlay sim (0_reproduce threshold) -> full results identical.
  -> results/g1det_summary.json

  source wp0_overlay/env.sh && cd wp0_overlay && taskset -c 8-23 $BALEEN_PY -B src/g1det.py
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tacommon as T  # noqa: E402
import g1 as G  # noqa: E402

OUT = os.path.join(T.RESULTS, "g1det")
LOGS = os.path.join(T.A, "logs", "g1det")
DET_ENV = {"TA_DETERMINISTIC": "1", "PYTHONHASHSEED": "0"}


def train_det(code, region, tag):
    rec = os.path.join(OUT, f"train_{tag}.json")
    if os.path.exists(rec):
        return json.load(open(rec))
    job = T.load_fig9_job(T.BALEEN_JOB[region])
    targs = T.set_flag(list(job["train_args"]), "--exp", tag)
    targs = T.set_flag(targs, "--output-base-dir", f"runs/g1det/{tag}/train")
    out, dt = T.run_train(code, targs, os.path.join(LOGS, tag, "train.log"),
                          dump_dir=os.path.join(OUT, "dumps", tag), extra_env=DET_ENV)
    r = dict(code=code, region=region, tag=tag, out=out, secs=dt)
    json.dump(r, open(rec, "w"), indent=1)
    return r


def sim_det(code, region, train_rec, tag):
    job = T.load_fig9_job(T.BALEEN_JOB[region])
    base = T.fill_sim_args(list(job["sim_args"]), train_rec["out"])
    base = T.set_flag(base, "--ap-threshold", f"{T.BALEEN_TH[region]:.6f}")
    base = T.set_flag(base, "--job-id", tag)
    return T.run_sim(code, base, f"runs/g1det/{tag}/sim", os.path.join(LOGS, tag, "sim.log"))


def main():
    os.makedirs(OUT, exist_ok=True)
    pool = ThreadPoolExecutor(max_workers=4)
    summary, futs, trains = {}, {}, {}
    for region in ("Region7", "Region6"):
        for code, k in (("frozen", 1), ("overlay", 1), ("frozen", 2), ("overlay", 2)):
            trains[(region, code, k)] = train_det(code, region, f"g1det_{region}_{code}{k}")
            if k == 1:
                futs[(region, code)] = pool.submit(sim_det, code, region, trains[(region, code, 1)],
                                                   f"g1det_{region}_{code}1_sim{code[0].upper()}")
    for region in ("Region7", "Region6"):
        d = lambda c, k: os.path.join(OUT, "dumps", f"g1det_{region}_{c}{k}")  # noqa: E731
        s = {}
        for a, b in ((("frozen", 1), ("frozen", 2)), (("frozen", 1), ("overlay", 1)), (("frozen", 1), ("overlay", 2))):
            name = f"{a[0]}{a[1]}_vs_{b[0]}{b[1]}"
            ad = G.compare_admit_dumps(d(*a), d(*b))
            ad.pop("feat_cols")
            s[name] = dict(admit=ad, prefetch=G.compare_prefetch_dumps(d(*a), d(*b)),
                           models=G.compare_models(trains[(region,) + a], trains[(region,) + b]))
        s["pipeline_frozen_vs_overlay"] = G.compare_results(futs[(region, "frozen")].result(),
                                                            futs[(region, "overlay")].result())
        summary[region] = s
    verdict = {}
    for region, s in summary.items():
        v = {}
        for name in ("frozen1_vs_frozen2", "frozen1_vs_overlay1", "frozen1_vs_overlay2"):
            ad, pf, md = s[name]["admit"], s[name]["prefetch"], s[name]["models"]
            v[name] = dict(rows_same_order=ad["same_row_order"],
                           df_X_identical=ad["df_X_all_columns_identical"] and ad["df_X_columns_same_order"],
                           df_Y_identical=ad["df_Y_identical"], labels_identical=ad["labels_threshold_binary_identical"],
                           split_identical=ad["train_split_same_rows"],
                           prefetch_XY_identical=all(x["X_identical_in_order"] and x["Y_identical_in_order"]
                                                     for x in pf.values()),
                           model_files_identical=all(m["identical"] for m in md.values()))
        p = s["pipeline_frozen_vs_overlay"]
        v["pipeline_metrics_bit_identical"] = p["metrics_bit_identical"]
        v["pipeline_all_results_and_series_identical"] = p["all_results_and_series_identical"]
        v["p100"], v["wr"] = p["p100_a"], p["wr_a"]
        verdict[region] = v
    json.dump(dict(verdict=verdict, summary=summary), open(os.path.join(T.RESULTS, "g1det_summary.json"), "w"),
              indent=1, default=str)
    print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
    main()
