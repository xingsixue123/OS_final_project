"""G1_v3: default equivalence of the WP10 overlay v3 (PATCH_v3.diff) vs the FROZEN artifact, plus the table check.
Region7 s0 only (dev), as CP1 (wp0_overlay/src/g1.py, g1det.py; comparison code copied below).

  source wp10_schedule/env.sh && cd wp10_schedule && setsid nohup $BALEEN_PY -B src/g1v3.py > logs/g1v3.out 2>&1 &
  (the driver itself only orchestrates; every Baleen process runs under taskset + bwrap with a private /tmp)

1. RejectX + CoinFlip (authors' 20230410_static_pf commands, authors' probability): frozen sim vs v3 sim -> every result
   key, counter, per-window series and histogram identical; also equal to phase 1's published frozen runs.
2. Baleen, pinned training (CP1's G1-det: Pool.imap_unordered -> imap, PYTHONHASHSEED=0, identical for both code bases):
   frozen train vs v3 train -> dumps (df_X, df_Y, split, prefetch X/Y) and all model files identical (and equal to
   CP1's pinned frozen model files); frozen train -> frozen sim vs v3 train -> v3 sim (0_reproduce threshold) identical.
3. Baleen, the same model files (WP2 retrain A_baleen_Region7_s0_r1, copied) through the frozen and the v3 simulator.
4. TABLE == POWER LAW: v3 sim with --ap-load-adapt-alpha -1 vs v3 sim with --ap-load-adapt-table <exact table>, where the
   table has one bucket per distinct load_10m value occurring at any request timestamp of the trace and multiplier
   g_pow(v) computed with the overlay's own power-law expression -> every result/series must be bit-identical.
Outputs: results/g1v3/*.json, results/g1v3_summary.json
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

OUT = os.path.join(C.W, "results", "g1v3")
LOGS = os.path.join(C.W, "logs", "g1v3")
FROZEN = C.WORK_FROZEN
INST = "Region7_s0"
BALEEN_TH = 0.62094                     # 0_reproduce's converged threshold (CP1)
SKIP_RESULT_KEYS = {"SimWallClockTime", "SimRAMUsage"}
DET_ENV = {"TA_DETERMINISTIC": "1", "PYTHONHASHSEED": "0"}
WP0 = os.path.join(C.P2, "wp0_overlay")


def work_of(code):
    return FROZEN if code == "frozen" else C.WORK


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
    out = f"runs/g1v3/{tag}/sim"
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
    t = C.set_flag(t, "--output-base-dir", f"runs/g1v3/{tag}/train")
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
    t = C.set_flag(t, "--output-base-dir", f"runs/g1v3/{tag}/train")
    tr = train(code, tag, t, dump_dir=os.path.join(OUT, "dumps", tag), extra=DET_ENV)
    base = C.fill_sim_args(list(J["sim_args"]), tr["out"])
    base = C.set_flag(base, "--ap-threshold", f"{BALEEN_TH:.6f}")
    return tr, sim(code, f"{tag}_sim", base)


def wp2_model_out(key):
    """Copy a WP2 retrain's trained files into wp10 work/models/<key>/ (read-only use of WP2) -> train 'out' dict."""
    rec = json.load(open(os.path.join(C.WP2, "results", "train", f"{key}.json")))
    out = {}
    for k, (p, szs) in rec["out"].items():
        dst = os.path.join(C.WORK, "models", key, os.path.basename(p))
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


def part_table(model_key, theta):
    J = C.JOBS[INST]["baleen"]
    out = wp2_model_out(model_key)
    base = C.fill_sim_args(list(J["sim_args"]), out)
    base = C.set_flag(base, "--ap-threshold", f"{theta:.6f}")
    tpath = os.path.join(C.WORK, "tables", "g1v3_exact_powerlaw_Region7_s0.json")
    os.makedirs(os.path.dirname(tpath), exist_ok=True)
    meta = exact_table(tpath)
    a = sim("overlay", "table_alpha", C.set_flag(list(base), "--ap-load-adapt-alpha", "-1.0"))
    b = sim("overlay", "table_exact", C.set_flag(list(base), "--ap-load-adapt-table", os.path.relpath(tpath, C.WORK)))
    return meta, a, b, base


def main():
    os.makedirs(OUT, exist_ok=True)
    pool = ThreadPoolExecutor(max_workers=12)
    f = {}
    for pol in ("rejectx", "coinflip"):
        for code in ("frozen", "overlay"):
            f[("static", pol, code)] = pool.submit(part_static, code, pol)
    for code in ("frozen", "overlay"):
        f[("det", code)] = pool.submit(part_pinned, code)
    # same WP2 model files through both simulators; its WP2 A+alpha converged threshold for the table check
    t2 = pd.read_csv(os.path.join(C.WP2, "trials.csv"))
    key = "A_baleen_Region7_s0_r1"
    th_A = float(t2[t2.trial_key == key].threshold.iloc[0])
    ra = t2[(t2.arm.isin(["Aa-1.0", "Ax-1.0"])) & (t2.inst == INST) & (t2.rep == 1) & (t2.matched.astype(str) == "True")]
    th_Aa = float(ra.threshold.iloc[0])
    out = wp2_model_out(key)
    J = C.JOBS[INST]["baleen"]
    base = C.set_flag(C.fill_sim_args(list(J["sim_args"]), out), "--ap-threshold", f"{th_A:.6f}")
    for code in ("frozen", "overlay"):
        f[("same", code)] = pool.submit(sim, code, f"samemodel_{code}", base)
    f["table"] = pool.submit(part_table, key, th_Aa)
    res = {k: v.result() for k, v in f.items()}
    S = {}
    for pol in ("rejectx", "coinflip"):
        c = compare_results(res[("static", pol, "frozen")], res[("static", pol, "overlay")])
        jid = C.JOBS[INST][f"{pol}_static"]["job_id"]
        pub = glob.glob(os.path.join(C.REPRO, "work", "runs", "repro", jid, "sim", "*", "*_cache_perf.txt.lzma"))
        rp = C.load_result(pub[0])["results"]
        c["phase1_published_p100"], c["phase1_published_wr"] = rp["PeakServiceTimeUtil1"], rp["FlashWriteRate"]
        c["v3_equals_phase1_published"] = rp["PeakServiceTimeUtil1"] == c["p100_b"] and rp["FlashWriteRate"] == c["wr_b"]
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
    S["same_models_simF_vs_simV3"] = compare_results(res[("same", "frozen")], res[("same", "overlay")])
    meta, a, b, _ = res["table"]
    S["table_vs_alpha"] = dict(compare_results(a, b), table=meta, theta=th_Aa, model=key)
    v = dict(
        rejectx_identical=S["rejectx"]["all_results_and_series_identical"],
        coinflip_identical=S["coinflip"]["all_results_and_series_identical"],
        static_equal_phase1_published=S["rejectx"]["v3_equals_phase1_published"] and S["coinflip"]["v3_equals_phase1_published"],
        pinned_dumps_identical=S["pinned_admit_dumps"]["df_X_identical"] and S["pinned_admit_dumps"]["df_Y_identical"]
        and S["pinned_admit_dumps"]["same_row_order"] and all(x["X_identical"] and x["Y_identical"] for x in S["pinned_prefetch_dumps"].values()),
        pinned_models_identical=all(x["identical"] for x in S["pinned_models"].values()),
        pinned_models_equal_CP1=all(x["identical"] for x in S.get("pinned_models_vs_CP1_frozen1", {"_": {"identical": False}}).values()),
        pinned_pipeline_identical=S["pinned_pipeline"]["all_results_and_series_identical"],
        same_models_identical=S["same_models_simF_vs_simV3"]["all_results_and_series_identical"],
        table_equals_alpha=S["table_vs_alpha"]["all_results_and_series_identical"],
        p100=dict(rejectx=S["rejectx"]["p100_b"], coinflip=S["coinflip"]["p100_b"], pinned=S["pinned_pipeline"]["p100_b"],
                  same_model=S["same_models_simF_vs_simV3"]["p100_b"], alpha=S["table_vs_alpha"]["p100_a"],
                  table=S["table_vs_alpha"]["p100_b"]))
    v["G1_v3_pass"] = all(v[k] for k in ("rejectx_identical", "coinflip_identical", "pinned_dumps_identical",
                                         "pinned_models_identical", "pinned_pipeline_identical", "same_models_identical"))
    v["table_check_pass"] = v["table_equals_alpha"]
    json.dump(dict(verdict=v, summary=S), open(os.path.join(C.W, "results", "g1v3_summary.json"), "w"), indent=1, default=str)
    print(json.dumps(v, indent=1, default=str))


if __name__ == "__main__":
    main()
