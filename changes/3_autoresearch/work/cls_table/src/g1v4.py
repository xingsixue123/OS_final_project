"""G1_v4: default equivalence of the 3_autoresearch overlay v4 (PATCH_v3.diff + PATCH_v4_delta.diff, SCOPE_AMENDMENT.md
item 1.2c) vs the FROZEN artifact, plus v4 == v3 checks. Copied from wp10_schedule/src/g1v3.py (comparison code
unchanged); Region7 s0 only (dev).

  source env.sh && setsid nohup src/sbx.sh src/g1v4.py > logs/g1v4.out 2>&1 &

1. RejectX + CoinFlip (authors' 20230410_static_pf commands, authors' probability): frozen sim vs v4 sim.
2. Baleen, pinned training (CP1's G1-det): frozen train vs v4 train -> dumps and model files identical; frozen train ->
   frozen sim vs v4 train -> v4 sim (0_reproduce threshold) identical.
3. Baleen, the same model files (WP2 retrain A_baleen_Region7_s0_r1) through the frozen and the v4 simulator.
4. v4 == v3 on the adaptive paths (same WP2 model files, its WP2 A+alpha threshold):
   (a) --ap-load-adapt-alpha -1: v3 sim vs v4 sim;
   (b) --ap-load-adapt-table <exact power-law table> (G1_v3's construction): v3 sim vs v4 sim;
   (c) CLASS TABLE == TABLE: v4 sim with a class table (class_dims endoff > 8 MiB, both class rows = the exact
       power-law table) vs the v3 sim of (b) -> bit-identical; and (b) == (a) repeats G1_v3's table == power law.
Outputs: results/g1v4/*.json, results/g1v4_summary.json
"""
import glob
import hashlib
import json
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402
sys.path.insert(0, C.WORK)

OUT = os.path.join(C.W, "results", "g1v4")
LOGS = os.path.join(C.W, "logs", "g1v4")
WORK_V3 = os.path.join(C.W, "work_v3")       # overlay v3 copy (BCacheSim -> ../overlay_v3/BCacheSim)
FROZEN = C.WORK_FROZEN
INST = "Region7_s0"
BALEEN_TH = 0.62094                     # 0_reproduce's converged threshold (CP1)
SKIP_RESULT_KEYS = {"SimWallClockTime", "SimRAMUsage"}
DET_ENV = {"TA_DETERMINISTIC": "1", "PYTHONHASHSEED": "0"}
WP0 = os.path.join(C.P2, "wp0_overlay")


def work_of(code):
    return {"frozen": FROZEN, "v3": WORK_V3}.get(code, C.WORK)


# ------------------------------------------------------------------ runners
_TL = {}
_TLL = __import__("threading").Lock()


def train(code, tag, args, dump_dir=None, extra=None, mod="ta_launch_train"):
    with _TLL:
        lk = _TL.setdefault(tag, __import__("threading").Lock())
    with lk:
        return _train(code, tag, args, dump_dir, extra, mod)


def _train(code, tag, args, dump_dir=None, extra=None, mod="ta_launch_train"):
    rec = os.path.join(OUT, f"train_{tag}.json")
    if os.path.exists(rec):
        return json.load(open(rec))
    W_ = work_of(code)
    env = C.base_env(threads=2, extra=extra, work=W_)
    if dump_dir:
        os.makedirs(dump_dir, exist_ok=True)
        env["TA_DUMP_DIR"] = dump_dir
    lp = os.path.join(LOGS, tag, "train.log")
    with C.TrainLock():
        rc, dt = C.run_logged(["-m", mod] + list(args), lp, env=env, work=W_, cpuset=C.cpus())
    out = C.parse_train_outputs(lp, work=W_)
    if rc != 0 or out is None or any(v[1] == "NoExists" for v in out.values()):
        raise RuntimeError(f"train failed rc={rc}: {lp}")
    r = dict(code=code, tag=tag, out=out, secs=dt)
    json.dump(r, open(rec, "w"), indent=1)
    return r


def sim(code, tag, args):
    W_ = work_of(code)
    out = f"runs/g1v4/{tag}/sim"
    args = C.set_flag(list(args), "-o", out)
    args = C.set_flag(args, "--job-id", tag)
    done = C.result_files(out, work=W_)
    lp = os.path.join(LOGS, tag, "sim.log")
    if not done:
        with C.SimSlot() as S:
            rc, _ = C.run_logged(["-m", "BCacheSim.cachesim.simulate_ap"] + args, lp,
                                 env=C.base_env(threads=2, work=W_), work=W_, cpuset=S.cpuset)
        log = open(lp).read()
        for p in ["Failed to load", "Bad file", "Traceback (most recent call last)"]:
            if p in log:
                raise RuntimeError(f"sim soft-fail '{p}': {lp}")
        done = C.result_files(out, work=W_)
        if rc != 0 or not done:
            raise RuntimeError(f"sim failed rc={rc}: {lp}")
    return done[0]


# ------------------------------------------------------------------ comparisons (copied from wp0_overlay/src/g1.py)
def stats_file(result_file):
    return result_file.replace("_cache_perf.txt.lzma", "_cache_perf.txt.stats.lzma")


def compare_results(fa, fb):
    ra, rb = C.load_result(fa), C.load_result(fb)
    res_a, res_b = ra["results"], rb["results"]
    keys = sorted(set(res_a) | set(res_b))
    diff = [k for k in keys if k not in SKIP_RESULT_KEYS and res_a.get(k, "MISSING") != res_b.get(k, "MISSING")]
    st_a = {k: v for k, v in ra.get("stats", {}).items()}
    st_b = {k: v for k, v in rb.get("stats", {}).items()}
    counters_diff = [k for k in sorted(set(st_a) | set(st_b))
                     if "realtime" not in k and k != "time_phy" and st_a.get(k) != st_b.get(k)]
    sa, sb = C.load_result(stats_file(fa)), C.load_result(stats_file(fb))
    ba, bb = sa["batches"], sb["batches"]
    batch_diff = [k for k in sorted(set(ba) | set(bb)) if "realtime" not in k and ba.get(k) != bb.get(k)]
    fa_, fb_ = sa["freq"], sb["freq"]
    freq_diff = [k for k in sorted(set(fa_) | set(fb_)) if fa_.get(k) != fb_.get(k)]
    oa, ob = ra["options"], rb["options"]
    return dict(a=os.path.relpath(fa, C.W), b=os.path.relpath(fb, C.W),
                p100_a=res_a["PeakServiceTimeUtil1"], p100_b=res_b["PeakServiceTimeUtil1"],
                wr_a=res_a["FlashWriteRate"], wr_b=res_b["FlashWriteRate"],
                n_result_keys=len(keys), result_keys_differing=diff,
                counters_differing=counters_diff, n_batches=len(set(ba) | set(bb)), batches_differing=batch_diff,
                n_freq=len(set(fa_) | set(fb_)), freq_differing=freq_diff,
                options_only_in_b=sorted(set(ob) - set(oa)), options_only_in_a=sorted(set(oa) - set(ob)),
                options_differing=sorted(k for k in set(oa) & set(ob) if oa[k] != ob[k]),
                metrics_bit_identical=(res_a["PeakServiceTimeUtil1"] == res_b["PeakServiceTimeUtil1"]
                                       and res_a["FlashWriteRate"] == res_b["FlashWriteRate"]),
                all_results_and_series_identical=not diff and not batch_diff and not counters_diff and not freq_diff)


def _frame_equal(a, b):
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
    import pickle
    A_ = pickle.load(open(os.path.join(da, "admit_prep.pkl"), "rb"))
    B_ = pickle.load(open(os.path.join(db, "admit_prep.pkl"), "rb"))
    out = dict(n_rows_a=len(A_["keys"]), n_rows_b=len(B_["keys"]), same_row_order=A_["keys"] == B_["keys"],
               feat_cols_equal=A_["feat_cols"] == B_["feat_cols"])
    okx, badx = _frame_equal(A_["df_X"].reset_index(drop=True), B_["df_X"].reset_index(drop=True))
    oky, bady = _frame_equal(A_["df_Y"].reset_index(drop=True), B_["df_Y"].reset_index(drop=True))
    out.update(df_X_identical=okx, df_X_differing=badx, df_Y_identical=oky, df_Y_differing=bady,
               split_identical=A_["split_idxes"]["train"] == B_["split_idxes"]["train"] if hasattr(A_["split_idxes"]["train"], "__eq__") else None)
    try:
        out["split_identical"] = bool(np.array_equal(np.asarray(A_["split_idxes"]["train"]), np.asarray(B_["split_idxes"]["train"])))
    except Exception:
        pass
    return out


def compare_prefetch_dumps(da, db):
    import pickle
    out = {}
    for fa in sorted(glob.glob(os.path.join(da, "prefetch_prep_*.pkl"))):
        name = os.path.basename(fa).split("_", 3)[-1]
        fb = glob.glob(os.path.join(db, f"prefetch_prep_*_{name}"))
        assert len(fb) == 1, (fa, fb)
        A_, B_ = pickle.load(open(fa, "rb")), pickle.load(open(fb[0], "rb"))
        Xa, Xb = np.asarray(A_["X"], float), np.asarray(B_["X"], float)
        Ya, Yb = np.asarray(A_["Y"], float), np.asarray(B_["Y"], float)
        out[name] = dict(same_row_order=A_["keys"] == B_["keys"],
                         X_identical=Xa.shape == Xb.shape and bool(np.array_equal(Xa, Xb)),
                         Y_identical=Ya.shape == Yb.shape and bool(np.array_equal(Ya, Yb, equal_nan=True)))
    return out


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def compare_models(oa, ob):
    return {k: dict(identical=sha(pa) == sha(ob[k][0])) for k, (pa, _) in oa.items() if k.startswith("model_")}


# ------------------------------------------------------------------ parts
def part_static(code, pol):
    J = C.JOBS[INST][f"{pol}_static"]
    tag = f"static_{pol}"
    t = C.set_flag(list(J["train_args"]), "--exp", tag)
    t = C.set_flag(t, "--output-base-dir", f"runs/g1v4/{tag}/train")
    tr = train("frozen", tag, t, mod="BCacheSim.episodic_analysis.train")
    # the same (frozen-built) analysis file for both simulators; --ep-analysis is parsed but not read by cachesim
    out = dict(tr["out"])
    if code == "overlay":
        rel = os.path.relpath(out["analysis"][0], FROZEN)
        dst = os.path.join(C.WORK, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst):
            shutil.copy2(out["analysis"][0], dst)
        out["analysis"] = (dst, out["analysis"][1])
    base = C.fill_sim_args(list(J["sim_args"]), out)
    return sim(code, f"{tag}_{code}", base)


def part_pinned(code):
    J = C.JOBS[INST]["baleen"]
    tag = f"det_{code}"
    t = C.set_flag(list(J["train_args"]), "--exp", tag)
    t = C.set_flag(t, "--output-base-dir", f"runs/g1v4/{tag}/train")
    tr = train(code, tag, t, dump_dir=os.path.join(OUT, "dumps", tag), extra=DET_ENV)
    base = C.fill_sim_args(list(J["sim_args"]), tr["out"])
    base = C.set_flag(base, "--ap-threshold", f"{BALEEN_TH:.6f}")
    return tr, sim(code, f"{tag}_sim", base)


def wp2_model_out(key, work=None):
    """Copy a WP2 retrain's trained files into <work>/models/<key>/ (read-only use of WP2) -> train 'out' dict."""
    rec = json.load(open(os.path.join(C.WP2, "results", "train", f"{key}.json")))
    out = {}
    for k, (p, szs) in rec["out"].items():
        dst = os.path.join(work or C.WORK, "models", key, os.path.basename(p))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst) and os.path.exists(p):
            shutil.copy2(p, dst)
        out[k] = (dst, szs)
    return out


def exact_table(path):
    """One bucket per distinct load_10m value at any request timestamp of the Region7 s0 trace."""
    if os.path.exists(path):
        return json.load(open(path))["meta"]
    from BCacheSim.cachesim import legacy_utils
    from BCacheSim.cachesim import load_features as LF
    tracef = os.path.join(C.WORK, C.get_flag(C.JOBS[INST]["baleen"]["sim_args"], "--trace"))
    demand = LF.DemandLoad.from_trace(tracef, 0.1)
    k_acc, _, _ = legacy_utils.read_processed_file(tracef, get_features=True, only_gets=False)
    ts = sorted({float(a.ts) for k in k_acc.values() for a in k.accesses})
    ref, alpha = 20.0, -1.0
    lt = LF.LoadAdaptiveThreshold(demand, alpha, ref=ref, window_min=10)
    vals = sorted({demand.load(t)[0] for t in ts})
    mult = []
    for x in vals:          # LoadAdaptiveThreshold.g's expression, verbatim
        x_ = max(x, 1e-6)
        mult.append(min(max((x_ / lt.ref) ** lt.alpha, LF.LOAD_ADAPT_CLIP[0]), LF.LOAD_ADAPT_CLIP[1]))
    meta = dict(n_timestamps=len(ts), n_buckets=len(vals), min_load=vals[0], max_load=vals[-1])
    json.dump(dict(name="exact_powerlaw_alpha-1_ref20_Region7_s0", window_min=10, edges=vals[1:], mult=mult, meta=meta),
              open(path, "w"))
    return meta


def part_v4(model_key, theta):
    """v4 == v3 on the adaptive paths: (a) alpha, (b) exact power-law table, (c) class table with identical rows."""
    J = C.JOBS[INST]["baleen"]
    res = {}
    tpath = os.path.join(C.WORK, "tables", "g1v4_exact_powerlaw_Region7_s0.json")
    os.makedirs(os.path.dirname(tpath), exist_ok=True)
    meta = exact_table(tpath)
    t = json.load(open(tpath))
    cpath = os.path.join(C.WORK, "tables", "g1v4_class_identical_rows_Region7_s0.json")
    if not os.path.exists(cpath):
        json.dump(dict(name="class_identical_rows_exact_powerlaw_Region7_s0", window_min=10, edges=t["edges"],
                       class_dims=[dict(feat="endoff", edges=[float(8 * (1 << 20))])], mult=[t["mult"], t["mult"]]),
                  open(cpath, "w"))
    for code in ("v3", "overlay"):
        W_ = work_of(code)
        out = wp2_model_out(model_key, work=W_)
        base = C.set_flag(C.fill_sim_args(list(J["sim_args"]), out), "--ap-threshold", f"{theta:.6f}")
        tp = os.path.join(W_, "tables", os.path.basename(tpath))
        if code == "v3" and not os.path.exists(tp):
            os.makedirs(os.path.dirname(tp), exist_ok=True)
            shutil.copy2(tpath, tp)
        res[("alpha", code)] = sim(code, f"alpha_{code}", C.set_flag(list(base), "--ap-load-adapt-alpha", "-1.0"))
        res[("table", code)] = sim(code, f"table_{code}", C.set_flag(list(base), "--ap-load-adapt-table", os.path.relpath(tp, W_)))
        if code == "overlay":
            res[("class", code)] = sim(code, f"classtable_{code}",
                                       C.set_flag(list(base), "--ap-load-adapt-table", os.path.relpath(cpath, W_)))
    return meta, res


def main():
    os.makedirs(OUT, exist_ok=True)
    pool = ThreadPoolExecutor(max_workers=12)
    f = {}
    for pol in ("rejectx", "coinflip"):
        for code in ("frozen", "overlay"):
            f[("static", pol, code)] = pool.submit(part_static, code, pol)
    for code in ("frozen", "overlay"):
        f[("det", code)] = pool.submit(part_pinned, code)
    t2 = pd.read_csv(os.path.join(C.WP2, "trials.csv"))
    key = "A_baleen_Region7_s0_r1"
    th_A = float(t2[t2.trial_key == key].threshold.iloc[0])
    ra = t2[(t2.arm.isin(["Aa-1.0", "Ax-1.0"])) & (t2.inst == INST) & (t2.rep == 1) & (t2.matched.astype(str) == "True")]
    th_Aa = float(ra.threshold.iloc[0])
    out = wp2_model_out(key)
    J = C.JOBS[INST]["baleen"]
    base = C.set_flag(C.fill_sim_args(list(J["sim_args"]), out), "--ap-threshold", f"{th_A:.6f}")
    for code in ("frozen", "overlay"):
        b_ = base
        if code == "frozen":
            outF = wp2_model_out(key, work=FROZEN)
            b_ = C.set_flag(C.fill_sim_args(list(J["sim_args"]), outF), "--ap-threshold", f"{th_A:.6f}")
        f[("same", code)] = pool.submit(sim, code, f"samemodel_{code}", b_)
    f["v4"] = pool.submit(part_v4, key, th_Aa)
    res = {k: v.result() for k, v in f.items()}
    S = {}
    for pol in ("rejectx", "coinflip"):
        c = compare_results(res[("static", pol, "frozen")], res[("static", pol, "overlay")])
        jid = C.JOBS[INST][f"{pol}_static"]["job_id"]
        pub = glob.glob(os.path.join(C.REPRO, "work", "runs", "repro", jid, "sim", "*", "*_cache_perf.txt.lzma"))
        rp = C.load_result(pub[0])["results"]
        c["phase1_published_p100"], c["phase1_published_wr"] = rp["PeakServiceTimeUtil1"], rp["FlashWriteRate"]
        c["v4_equals_phase1_published"] = rp["PeakServiceTimeUtil1"] == c["p100_b"] and rp["FlashWriteRate"] == c["wr_b"]
        S[pol] = c
    (trF, sF), (trO, sO) = res[("det", "frozen")], res[("det", "overlay")]
    S["pinned_admit_dumps"] = compare_admit_dumps(os.path.join(OUT, "dumps", "det_frozen"), os.path.join(OUT, "dumps", "det_overlay"))
    S["pinned_prefetch_dumps"] = compare_prefetch_dumps(os.path.join(OUT, "dumps", "det_frozen"), os.path.join(OUT, "dumps", "det_overlay"))
    S["pinned_models"] = compare_models(trF["out"], trO["out"])
    cp1 = os.path.join(WP0, "results", "g1det", "train_g1det_Region7_frozen1.json")
    if os.path.exists(cp1):
        o1 = json.load(open(cp1))["out"]
        if all(os.path.exists(p) for k, (p, _) in o1.items() if k.startswith("model_")):
            S["pinned_models_vs_CP1_frozen1"] = compare_models(o1, trO["out"])
    S["pinned_pipeline"] = compare_results(sF, sO)
    S["same_models_simF_vs_simV4"] = compare_results(res[("same", "frozen")], res[("same", "overlay")])
    meta, r4 = res["v4"]
    S["alpha_v3_vs_v4"] = compare_results(r4[("alpha", "v3")], r4[("alpha", "overlay")])
    S["table_v3_vs_v4"] = compare_results(r4[("table", "v3")], r4[("table", "overlay")])
    S["classtable_v4_vs_table_v3"] = dict(compare_results(r4[("table", "v3")], r4[("class", "overlay")]), table=meta, theta=th_Aa, model=key)
    S["table_v3_vs_alpha_v3"] = compare_results(r4[("alpha", "v3")], r4[("table", "v3")])
    v = dict(
        rejectx_identical=S["rejectx"]["all_results_and_series_identical"],
        coinflip_identical=S["coinflip"]["all_results_and_series_identical"],
        static_equal_phase1_published=S["rejectx"]["v4_equals_phase1_published"] and S["coinflip"]["v4_equals_phase1_published"],
        pinned_dumps_identical=S["pinned_admit_dumps"]["df_X_identical"] and S["pinned_admit_dumps"]["df_Y_identical"]
        and S["pinned_admit_dumps"]["same_row_order"] and all(x["X_identical"] and x["Y_identical"] for x in S["pinned_prefetch_dumps"].values()),
        pinned_models_identical=all(x["identical"] for x in S["pinned_models"].values()),
        pinned_models_equal_CP1=all(x["identical"] for x in S.get("pinned_models_vs_CP1_frozen1", {"_": {"identical": False}}).values()),
        pinned_pipeline_identical=S["pinned_pipeline"]["all_results_and_series_identical"],
        same_models_identical=S["same_models_simF_vs_simV4"]["all_results_and_series_identical"],
        alpha_v4_equals_v3=S["alpha_v3_vs_v4"]["all_results_and_series_identical"],
        table_v4_equals_v3=S["table_v3_vs_v4"]["all_results_and_series_identical"],
        classtable_equals_table=S["classtable_v4_vs_table_v3"]["all_results_and_series_identical"],
        table_equals_alpha=S["table_v3_vs_alpha_v3"]["all_results_and_series_identical"],
        p100=dict(rejectx=S["rejectx"]["p100_b"], coinflip=S["coinflip"]["p100_b"], pinned=S["pinned_pipeline"]["p100_b"],
                  same_model=S["same_models_simF_vs_simV4"]["p100_b"], alpha_v3=S["alpha_v3_vs_v4"]["p100_a"],
                  alpha_v4=S["alpha_v3_vs_v4"]["p100_b"], table_v4=S["table_v3_vs_v4"]["p100_b"],
                  classtable_v4=S["classtable_v4_vs_table_v3"]["p100_b"]))
    v["G1_v4_pass"] = all(v[k] for k in ("rejectx_identical", "coinflip_identical", "pinned_dumps_identical",
                                         "pinned_models_identical", "pinned_pipeline_identical", "same_models_identical"))
    v["v4_adaptive_paths_pass"] = all(v[k] for k in ("alpha_v4_equals_v3", "table_v4_equals_v3", "classtable_equals_table",
                                                     "table_equals_alpha"))
    json.dump(dict(verdict=v, summary=S), open(os.path.join(C.W, "results", "g1v4_summary.json"), "w"), indent=1, default=str)
    print(json.dumps(v, indent=1, default=str))


if __name__ == "__main__":
    main()
