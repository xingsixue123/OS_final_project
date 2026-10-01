"""Gate G1 (default equivalence), dev Region7 + Region6 sample 0, defaults only, OVERLAY vs FROZEN.

  source wp0_overlay/env.sh && cd wp0_overlay && taskset -c 8-23 $BALEEN_PY -B src/g1.py [--regions ...]

1. RejectX + CoinFlip (authors' 20230410_static_pf commands, as 0_reproduce): frozen sim vs overlay sim -> full result
   JSON + per-window stats must be bit-identical (and equal to 0_reproduce's published frozen runs).
2. Baleen (authors' Fig 9 TrainCommand): one frozen and one overlay training, each dumping train_ap's df_X/df_Y
   (+ per-row keys) and the prefetch trainers' X/Y right after prep (ta_launch_train hooks) -> labels and feature
   matrices must be identical. Model files are compared too (training is not deterministic run-to-run, so they
   may differ; see --frozen-repeat).
3. The SAME model files (from each training) are simulated with the frozen and the overlay simulator at 0_reproduce's
   converged threshold -> PeakServiceTimeUtil1, FlashWriteRate (and every other result) must be bit-identical.
Outputs: results/g1/*.json, results/g1_summary.json.
"""
import argparse
import glob
import hashlib
import json
import os
import pickle
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tacommon as T  # noqa: E402

OUT = os.path.join(T.RESULTS, "g1")
LOGS = os.path.join(T.A, "logs", "g1")
SKIP_RESULT_KEYS = {"SimWallClockTime", "SimRAMUsage"}


# ------------------------------------------------------------------ runs
def train_baleen(code, region, tag, dump=True):
    rec = os.path.join(OUT, f"train_{tag}.json")
    if os.path.exists(rec):
        return json.load(open(rec))
    job = T.load_fig9_job(T.BALEEN_JOB[region])
    targs = T.set_flag(list(job["train_args"]), "--exp", tag)
    targs = T.set_flag(targs, "--output-base-dir", f"runs/g1/{tag}/train")
    out, dt = T.run_train(code, targs, os.path.join(LOGS, tag, "train.log"),
                          dump_dir=os.path.join(OUT, "dumps", tag) if dump else None)
    r = dict(code=code, region=region, tag=tag, out=out, secs=dt)
    json.dump(r, open(rec, "w"), indent=1)
    return r


def sim_baleen(code, region, train_rec, tag):
    job = T.load_fig9_job(T.BALEEN_JOB[region])
    base = T.fill_sim_args(list(job["sim_args"]), train_rec["out"])
    base = T.set_flag(base, "--ap-threshold", f"{T.BALEEN_TH[region]:.6f}")
    base = T.set_flag(base, "--job-id", tag)
    return T.run_sim(code, base, f"runs/g1/{tag}/sim", os.path.join(LOGS, tag, "sim.log"))


def sim_static(code, region, pol, tag):
    job = T.load_fig9_job(T.STATIC_JOBS[(region, pol)])
    # --ep-analysis is parsed but never read by cachesim/ (grep): keep phase 1's value (a string only)
    ana = {"Region7": {"rejectx": "6972.29", "coinflip": "7158.64"},
           "Region6": {"rejectx": "6260.56", "coinflip": "6401.12"}}[region][pol]
    jid = job["job_id"]
    path = f"runs/repro/{jid}/train/{jid}/20230325_{region}_0_0.1/offline_analysis_ea_{ana}.csv"
    base = T.fill_sim_args(list(job["sim_args"]), {"analysis": (path, "")})
    base = T.set_flag(base, "--job-id", jid)
    return T.run_sim(code, base, f"runs/g1/{tag}/sim", os.path.join(LOGS, tag, "sim.log"))


# ------------------------------------------------------------------ comparisons
def compare_results(fa, fb):
    ra, rb = T.load_result(fa), T.load_result(fb)
    res_a, res_b = ra["results"], rb["results"]
    keys = sorted(set(res_a) | set(res_b))
    diff = [k for k in keys if k not in SKIP_RESULT_KEYS and res_a.get(k, "MISSING") != res_b.get(k, "MISSING")]
    top = sorted(k for k in set(ra) | set(rb) if k not in ("results", "options", "command", "stats"))
    top_diff = [k for k in top if ra.get(k) != rb.get(k)]
    st_a = {k: v for k, v in ra.get("stats", {}).items()}
    st_b = {k: v for k, v in rb.get("stats", {}).items()}
    counters_diff = [k for k in sorted(set(st_a) | set(st_b))
                     if "realtime" not in k and k != "time_phy" and st_a.get(k) != st_b.get(k)]
    sa, sb = T.load_result(T.stats_file(fa)), T.load_result(T.stats_file(fb))
    ba, bb = sa["batches"], sb["batches"]
    batch_diff = [k for k in sorted(set(ba) | set(bb)) if "realtime" not in k and ba.get(k) != bb.get(k)]
    fa_, fb_ = sa["freq"], sb["freq"]
    freq_diff = [k for k in sorted(set(fa_) | set(fb_)) if fa_.get(k) != fb_.get(k)]
    oa, ob = ra["options"], rb["options"]
    return dict(a=fa, b=fb, p100_a=res_a["PeakServiceTimeUtil1"], p100_b=res_b["PeakServiceTimeUtil1"],
                wr_a=res_a["FlashWriteRate"], wr_b=res_b["FlashWriteRate"],
                p100_equal=res_a["PeakServiceTimeUtil1"] == res_b["PeakServiceTimeUtil1"],
                wr_equal=res_a["FlashWriteRate"] == res_b["FlashWriteRate"],
                n_result_keys=len(keys), result_keys_differing=diff, toplevel_differing=top_diff,
                counters_differing=counters_diff, n_batches=len(set(ba) | set(bb)), batches_differing=batch_diff,
                n_freq=len(set(fa_) | set(fb_)), freq_differing=freq_diff,
                options_only_in_b=sorted(set(ob) - set(oa)), options_only_in_a=sorted(set(oa) - set(ob)),
                options_differing=sorted(k for k in set(oa) & set(ob) if oa[k] != ob[k]),
                metrics_bit_identical=(res_a["PeakServiceTimeUtil1"] == res_b["PeakServiceTimeUtil1"]
                                       and res_a["FlashWriteRate"] == res_b["FlashWriteRate"]),
                all_results_and_series_identical=not diff and not batch_diff and not counters_diff)


def _frame_equal(a, b):
    """Exact equality of two DataFrames with identical index/columns (NaN == NaN)."""
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        return False, ["<shape/columns>"]
    bad = []
    for c in a.columns:
        x, y = a[c].to_numpy(), b[c].to_numpy()
        try:
            eq = (x == y) | (pd.isna(x) & pd.isna(y))
        except TypeError:
            eq = np.array([u == v or (pd.isna(u) and pd.isna(v)) for u, v in zip(x, y)])
        if not bool(np.all(eq)):
            bad.append(c)
    return not bad, bad


def compare_admit_dumps(da, db):
    A_ = pickle.load(open(os.path.join(da, "admit_prep.pkl"), "rb"))
    B_ = pickle.load(open(os.path.join(db, "admit_prep.pkl"), "rb"))
    ka, kb = A_["keys"], B_["keys"]
    assert len(set(ka)) == len(ka) and len(set(kb)) == len(kb), "row keys not unique"
    out = dict(n_rows_a=len(ka), n_rows_b=len(kb), same_key_set=set(ka) == set(kb), same_row_order=ka == kb,
               feat_subset=A_["feat_subset"], feat_cols_equal=A_["feat_cols"] == B_["feat_cols"],
               feat_cols=A_["feat_cols"])
    pos_b = {k: i for i, k in enumerate(kb)}
    perm = [pos_b[k] for k in ka]
    Xa = A_["df_X"].reset_index(drop=True)
    Xb = B_["df_X"].iloc[perm].reset_index(drop=True)
    Ya = A_["df_Y"].reset_index(drop=True)
    Yb = B_["df_Y"].iloc[perm].reset_index(drop=True)
    out["df_X_columns_same_order"] = list(Xa.columns) == list(B_["df_X"].columns)
    out["df_X_same_column_set"] = set(Xa.columns) == set(Xb.columns)
    ok_used, bad_used = _frame_equal(Xa[A_["feat_cols"]], Xb[A_["feat_cols"]])
    out["df_X_used_features_identical"] = ok_used
    out["df_X_used_features_differing_cols"] = bad_used
    if out["df_X_same_column_set"]:
        ok_all, bad_all = _frame_equal(Xa, Xb[list(Xa.columns)])
        out["df_X_all_columns_identical"] = ok_all
        out["df_X_differing_cols"] = bad_all
    ok_y, bad_y = _frame_equal(Ya, Yb[list(Ya.columns)]) if set(Ya.columns) == set(Yb.columns) else (False, ["<cols>"])
    out["df_Y_identical"] = ok_y
    out["df_Y_differing_cols"] = bad_y
    out["labels_threshold_binary_identical"] = bool((Ya["threshold_binary"].to_numpy()
                                                     == Yb["threshold_binary"].to_numpy()).all())
    out["n_pos"] = int(Ya["threshold_binary"].sum())
    for c in bad_y:
        x, y = Ya[c].to_numpy(), Yb[c].to_numpy()
        try:
            m = ~((x == y) | (pd.isna(x) & pd.isna(y)))
            out[f"df_Y_{c}_n_rows_differing"] = int(m.sum())
            if c == "threshold":
                xa, ya = x[m].astype(float), y[m].astype(float)
                out["threshold_rows_differing_with_label_flip"] = int(((xa < T.TARGET_WR) != (ya < T.TARGET_WR)).sum())
                out["threshold_max_abs_diff"] = float(np.max(np.abs(xa - ya))) if m.any() else 0.0
        except TypeError:
            pass
    # the train/test split assigns rows by block; compare the train-row key sets
    sa = {ka[i] for i in A_["split_idxes"]["train"]}
    sb = {kb[i] for i in B_["split_idxes"]["train"]}
    out["train_split_same_rows"] = sa == sb
    return out


def compare_prefetch_dumps(da, db):
    out = {}
    for fa in sorted(glob.glob(os.path.join(da, "prefetch_prep_*.pkl"))):
        name = os.path.basename(fa).split("_", 3)[-1]
        fb = glob.glob(os.path.join(db, f"prefetch_prep_*_{name}"))
        assert len(fb) == 1, (fa, fb)
        A_, B_ = pickle.load(open(fa, "rb")), pickle.load(open(fb[0], "rb"))
        r = dict(n_a=len(A_["X"]), n_b=len(B_["X"]), feat_names_equal=A_["feat_names"] == B_["feat_names"],
                 same_row_order=A_["keys"] == B_["keys"], same_key_set=set(A_["keys"]) == set(B_["keys"]))
        Xa, Xb = np.asarray(A_["X"], float), np.asarray(B_["X"], float)
        r["X_identical_in_order"] = Xa.shape == Xb.shape and bool(np.array_equal(Xa, Xb))
        sa = Xa[np.lexsort(Xa.T[::-1])] if len(Xa) else Xa
        sb = Xb[np.lexsort(Xb.T[::-1])] if len(Xb) else Xb
        r["X_identical_as_multiset"] = sa.shape == sb.shape and bool(np.array_equal(sa, sb))
        rank = A_["label_names"].index("rank")
        Ya = np.delete(np.asarray(A_["Y"], float), rank, axis=1)
        Yb = np.delete(np.asarray(B_["Y"], float), rank, axis=1)
        r["Y_identical_in_order"] = Ya.shape == Yb.shape and bool(np.array_equal(Ya, Yb, equal_nan=True))
        XYa = np.hstack([Xa, Ya])
        XYb = np.hstack([Xb, Yb])
        XYa = XYa[np.lexsort(XYa.T[::-1])] if len(XYa) else XYa
        XYb = XYb[np.lexsort(XYb.T[::-1])] if len(XYb) else XYb
        r["XY_identical_as_multiset_excl_rank"] = XYa.shape == XYb.shape and bool(np.array_equal(XYa, XYb, equal_nan=True))
        out[name.replace(".pkl", "")] = r
    return out


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def compare_models(ra, rb):
    out = {}
    for k, (pa, _) in ra["out"].items():
        if k.startswith("model_"):
            pb = rb["out"][k][0]
            out[k] = dict(identical=sha(pa) == sha(pb), size_a=os.path.getsize(pa), size_b=os.path.getsize(pb))
    return out


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", nargs="+", default=["Region7", "Region6"])
    ap.add_argument("--frozen-repeat", action="store_true",
                    help="also a 2nd frozen training (characterises run-to-run model nondeterminism)")
    o = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    pool = ThreadPoolExecutor(max_workers=T.MAX_SIMS)
    futs = {}
    # 1. static baselines: start right away
    for region in o.regions:
        for pol in ("rejectx", "coinflip"):
            for code in ("frozen", "overlay"):
                tag = f"g1_{region}_{pol}_{code}"
                futs[(region, pol, code)] = pool.submit(sim_static, code, region, pol, tag)
    # 2. trainings (serialised by the shared train lock), then 3. cross-simulations of the same model files
    trains = {}
    for region in o.regions:
        for code in ("frozen", "overlay"):
            trains[(region, code)] = train_baleen(code, region, f"g1_{region}_train{code[0].upper()}")
            for sim_code in ("frozen", "overlay"):
                tag = f"g1_{region}_model{code[0].upper()}_sim{sim_code[0].upper()}"
                futs[(region, f"model{code[0].upper()}", sim_code)] = pool.submit(
                    sim_baleen, sim_code, region, trains[(region, code)], tag)
        if o.frozen_repeat:
            trains[(region, "frozen2")] = train_baleen("frozen", region, f"g1_{region}_trainF2")
    res = {k: f.result() for k, f in futs.items()}
    summary = {}
    for region in o.regions:
        s = {}
        for pol in ("rejectx", "coinflip"):
            c = compare_results(res[(region, pol, "frozen")], res[(region, pol, "overlay")])
            jid = T.STATIC_JOBS[(region, pol)]
            pub = glob.glob(os.path.join(T.REPRO, "work", "runs", "repro", jid, "sim", "*", "*_cache_perf.txt.lzma"))
            rp = T.load_result(pub[0])["results"]
            c["phase1_published_p100"] = rp["PeakServiceTimeUtil1"]
            c["phase1_published_wr"] = rp["FlashWriteRate"]
            c["overlay_equals_phase1_published"] = (rp["PeakServiceTimeUtil1"] == c["p100_b"]
                                                    and rp["FlashWriteRate"] == c["wr_b"])
            s[pol] = c
        for m in ("modelF", "modelO"):
            s[f"baleen_{m}_simF_vs_simO"] = compare_results(res[(region, m, "frozen")], res[(region, m, "overlay")])
        dF = os.path.join(OUT, "dumps", f"g1_{region}_trainF")
        dO = os.path.join(OUT, "dumps", f"g1_{region}_trainO")
        s["train_admit_frozen_vs_overlay"] = compare_admit_dumps(dF, dO)
        s["train_prefetch_frozen_vs_overlay"] = compare_prefetch_dumps(dF, dO)
        s["model_files_frozen_vs_overlay"] = compare_models(trains[(region, "frozen")], trains[(region, "overlay")])
        if (region, "frozen2") in trains:
            dF2 = os.path.join(OUT, "dumps", f"g1_{region}_trainF2")
            s["train_admit_frozen_vs_frozen2"] = compare_admit_dumps(dF, dF2)
            s["train_prefetch_frozen_vs_frozen2"] = compare_prefetch_dumps(dF, dF2)
            s["model_files_frozen_vs_frozen2"] = compare_models(trains[(region, "frozen")], trains[(region, "frozen2")])
        s["train_secs"] = {k[1]: v["secs"] for k, v in trains.items() if k[0] == region}
        summary[region] = s
        json.dump(s, open(os.path.join(OUT, f"g1_{region}.json"), "w"), indent=1, default=str)
    # verdict. Unpinned training is not deterministic run-to-run in the frozen artifact itself (episode order from
    # Pool.imap_unordered -> row order, block-level split, score-tie order at the label boundary), so here the
    # training criterion is: model-input features identical (as a keyed set of rows), and every frozen-vs-overlay
    # difference is of a kind that also occurs frozen-vs-frozen2. The strict bit-exact form is g1det.py.
    def diff_kinds(ad, pf, md):
        k = set()
        if not ad["same_row_order"]:
            k.add("row_order")
        if not ad["train_split_same_rows"]:
            k.add("train_test_split")
        k |= {f"df_X:{c}" for c in ad.get("df_X_differing_cols", [])}
        k |= {f"df_Y:{c}" for c in ad["df_Y_differing_cols"]}
        k |= {f"prefetch_order:{n}" for n, v in pf.items() if not (v["X_identical_in_order"] and v["Y_identical_in_order"])}
        k |= {f"prefetch_rows:{n}" for n, v in pf.items() if not v["XY_identical_as_multiset_excl_rank"]}
        k |= {f"model:{n}" for n, v in md.items() if not v["identical"]}
        return k

    verdict = {}
    for region, s in summary.items():
        ad = s["train_admit_frozen_vs_overlay"]
        ko = diff_kinds(ad, s["train_prefetch_frozen_vs_overlay"], s["model_files_frozen_vs_overlay"])
        v = dict(
            rejectx_bit_identical=s["rejectx"]["metrics_bit_identical"],
            coinflip_bit_identical=s["coinflip"]["metrics_bit_identical"],
            rejectx_all_results_and_series_identical=s["rejectx"]["all_results_and_series_identical"],
            coinflip_all_results_and_series_identical=s["coinflip"]["all_results_and_series_identical"],
            static_equal_phase1_published=s["rejectx"]["overlay_equals_phase1_published"]
            and s["coinflip"]["overlay_equals_phase1_published"],
            train_same_row_keys=ad["same_key_set"],
            train_model_input_features_identical=ad["df_X_used_features_identical"] and ad["feat_cols_equal"],
            train_labels_identical=ad["labels_threshold_binary_identical"],
            train_label_flips_frozen_vs_overlay=ad.get("df_Y_threshold_binary_n_rows_differing", 0),
            prefetch_rows_identical_as_multiset=all(x["XY_identical_as_multiset_excl_rank"]
                                                    for x in s["train_prefetch_frozen_vs_overlay"].values()),
            frozen_vs_overlay_difference_kinds=sorted(ko),
            baleen_same_models_bit_identical=all(s[f"baleen_{m}_simF_vs_simO"]["metrics_bit_identical"]
                                                 for m in ("modelF", "modelO")),
            baleen_same_models_all_results_and_series_identical=all(
                s[f"baleen_{m}_simF_vs_simO"]["all_results_and_series_identical"] for m in ("modelF", "modelO")),
        )
        if "train_admit_frozen_vs_frozen2" in s:
            ad2 = s["train_admit_frozen_vs_frozen2"]
            kf = diff_kinds(ad2, s["train_prefetch_frozen_vs_frozen2"], s["model_files_frozen_vs_frozen2"])
            v["frozen_vs_frozen2_difference_kinds"] = sorted(kf)
            v["train_label_flips_frozen_vs_frozen2"] = ad2.get("df_Y_threshold_binary_n_rows_differing", 0)
            v["overlay_differences_within_frozen_run_to_run_differences"] = ko <= kf
        v["G1_pass"] = all(v.get(k, False) for k in (
            "rejectx_bit_identical", "coinflip_bit_identical", "train_same_row_keys",
            "train_model_input_features_identical", "prefetch_rows_identical_as_multiset",
            "overlay_differences_within_frozen_run_to_run_differences", "baleen_same_models_bit_identical"))
        verdict[region] = v
    json.dump(dict(verdict=verdict, summary=summary), open(os.path.join(T.RESULTS, "g1_summary.json"), "w"),
              indent=1, default=str)
    print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
    main()
