"""3_autoresearch cls_table driver: Baleen's own models + a threshold-multiplier table over load buckets x access
classes (overlay v4, SCOPE_AMENDMENT.md item 1.2c), deployed through this dir's overlay. Copied from
2_deployable_peak/wp10_schedule/src/wp10.py (WP9/WP3/WP2 lineage); training, threshold convergence (sequential full
sims seeded by the emulator, at most 7, (0, 4] for every adaptive arm), metrics and the ledger are WP10's code,
unchanged apart from what is marked "AR".

Arms (name -> admission features, schedule, base retrain):
  A, B            Baleen labels, meta+block+chunk / +load, no schedule
  Aa, Ba          + --ap-load-adapt-alpha -1.0 (A's / B's retrain)
  TA:<s>, TB:<s>  A's / B's retrain + WP10 load-bucket table (dev: WP10's own dev tables, copied read-only)
  PB<c>           AR probe: TB:pt's table for every access class, x c for big-offset accesses (end > 8 MiB) in the
                  load buckets b >= 3 (day-1 load quantile >= 0.75); dev only (mechanism check, no candidate)
  CA:<s>, CB:<s>  AR: A's / B's retrain + a load x class table fitted on the TRAINING day by solver <s> (cls_fit.py)
Modes: dev (8 Region6/7 instances: retrain k = WP2's A/B retrain k, model files copied read-only; Region5_s0 and
       Region1_s0: trained here, retrains 1-3), test (one pre-registered pool; refuses to start without TEST_GO).

  source env.sh && setsid nohup src/sbx.sh src/cls.py --mode dev --arms PB0.5 PB0.25 --reps 1 -j 16 &
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402
sys.path.insert(0, C.WORK)

ORIG = "meta+block+chunk"
LOAD = "meta+block+chunk+load"
WRMAP0 = {("Region7", "baleen"): (-1.288, 1.177), ("Region6", "baleen"): (-0.770, 1.146),
          # WP10: the E4 region has no earlier deployed sims; seed with Region6's map (as WP9; seeding only)
          ("Region1", "baleen"): (-0.770, 1.146),
          # AR: Region5 / test regions have no map of their own here; Region6's map (seeding only, as WP9)
          ("Region5", "baleen"): (-0.770, 1.146), ("Region2", "baleen"): (-0.770, 1.146),
          ("Region3", "baleen"): (-0.770, 1.146), ("Region4", "baleen"): (-0.770, 1.146)}
_LOCK = threading.Lock()
_EMU_LOCK = threading.Lock()
_TRAIN_LOCKS = {}
_TL = threading.Lock()


def PAIRS_():
    return os.path.join(C.RESULTS, "wrmap_pairs.jsonl")


# ------------------------------------------------------------------ specs
def arm_def(name):
    if name in ("A", "B"):
        return dict(arm=name, ap=ORIG if name == "A" else LOAD, alpha=None, solver=None, base=name)
    if name in ("Aa", "Ba"):
        return dict(arm=f"{name}-1.0", ap=ORIG if name[0] == "A" else LOAD, alpha=-1.0, solver=None, base=name[0])
    if name[:3] in ("TA:", "TB:", "CA:", "CB:"):
        b = name[1]
        return dict(arm=f"{name[0]}{b}-{name[3:]}", ap=ORIG if b == "A" else LOAD, alpha=None, solver=name[3:], base=b)
    if name[:3] in ("UA:", "UB:"):                              # AR plan B: pooled (universal) class table
        b = name[1]
        return dict(arm=f"U{b}-{name[3:]}", ap=ORIG if b == "A" else LOAD, alpha=None, solver="U" + name[3:], base=b)
    if name.startswith("PB"):                                   # AR probe (dev only)
        return dict(arm=f"PB-{name[2:]}", ap=LOAD, alpha=None, solver=f"probe{name[2:]}", base="B")
    raise ValueError(name)


def spec(name, inst, rep):
    d = arm_def(name)
    key = f"{d['arm']}_baleen_{inst}_r{rep}"
    base_key = f"{d['base']}_baleen_{inst}_r{rep}"
    return dict(trial_key=key, name=name, arm=d["arm"], design="baleen", inst=inst, rep=rep, stage=C.MODE,
                ap_subset=d["ap"], pf_subset=None, alpha=d["alpha"], solver=d["solver"], base=d["base"],
                base_key=base_key)


def table_path(sp):
    return os.path.join(C.W, "tables", C.MODE if C.MODE != "dryrun" else "dryrun",
                        f"{sp['solver']}_{sp['inst']}_{sp['base']}_r{sp['rep']}.json")


# ------------------------------------------------------------------ write-rate map (seeding only; WP9 code)
def wrmap(region, kind):
    a, b = WRMAP0[(region, kind)]
    if os.path.exists(PAIRS_()):
        rows = [json.loads(x) for x in open(PAIRS_())]
        rows = [r for r in rows if r["region"] == region and r["kind"] == kind and r["emu_wr"] > 0 and r["sim_wr"] > 0]
        if len(rows) >= 4:
            x = np.log([r["emu_wr"] for r in rows][-40:])
            y = np.log([r["sim_wr"] for r in rows][-40:])
            b_ = float(np.clip(np.polyfit(x, y, 1)[0], 0.5, 1.5)) if np.ptp(x) > 0.05 else b
            a, b = float(np.mean(y - b_ * x)), b_
    return a, b


def _inst_of(key):
    p = key.split("_")
    return f"{p[2]}_{p[3]}"


def emu_target(region, kind, inst=None, arm=None, design=None):
    a, b = wrmap(region, kind)
    bias = 0.0
    if inst and os.path.exists(PAIRS_()):
        rows = [r for r in map(json.loads, open(PAIRS_())) if r["emu_wr"] > 0 and r["sim_wr"] > 0 and _inst_of(r["key"]) == inst]
        same = [r for r in rows if r["key"].split("_")[0] == arm and r["key"].split("_")[1] == design]
        pick = same or [r for r in rows if r["kind"] == kind]
        res = [np.log(r["sim_wr"]) - (a + b * np.log(r["emu_wr"])) for r in pick]
        if res:
            bias = float(np.mean(res[-6:]))
    return float(np.exp((np.log(C.TARGET_WR) - a - bias) / b))


def get_emu(inst):
    import emu
    with _EMU_LOCK:
        return emu.get(inst)


# ------------------------------------------------------------------ train (dev: WP2 retrain copies; test: overlay train)
def wp2_model_out(key):
    rec = json.load(open(os.path.join(C.WP2, "results", "train", f"{key}.json")))
    out = {}
    for k, (p, szs) in rec["out"].items():
        dst = os.path.join(C.WORK, "models", key, os.path.basename(p))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst) and os.path.exists(p):
            shutil.copy2(p, dst)
        out[k] = (dst, szs)
    return dict(key=key, out=out, secs=rec.get("secs"), wait=rec.get("wait"), label_file=None, source="wp2")


def train(sp):
    key = sp["base_key"]
    if C.MODE == "dev" and sp["inst"] in C.DEV8 and sp["rep"] <= 3:   # AR: DEV8 retrains 1-3 re-use WP2's retrains
        return wp2_model_out(key)                                       # (extra seeds 4-6 are trained here, DEV_RULES R4)
    with _TL:
        lk = _TRAIN_LOCKS.setdefault(key, threading.Lock())
    with lk:
        return _train(sp, key)


def _train(sp, key):
    rec = os.path.join(C.RESULTS, "train", f"{key}.json")
    lp = os.path.join(C.LOGS, C.MODE, key, "train.log")
    if os.path.exists(rec):
        return json.load(open(rec))
    while os.path.exists(lp) and "Filenames generated:" not in open(lp).read() and time.time() - os.path.getmtime(lp) < 900:
        time.sleep(30)
    if os.path.exists(lp):
        out = C.parse_train_outputs(lp)
        if out is not None and all(v[1] != "NoExists" for v in out.values()):
            r = dict(key=key, out=out, secs=float("nan"), wait=float("nan"), label_file=None, resumed=True)
            os.makedirs(os.path.dirname(rec), exist_ok=True)
            json.dump(r, open(rec, "w"), indent=1)
            return r
    J = C.JOBS[sp["inst"]]["baleen"]
    t = list(J["train_args"])
    t = C.set_flag(t, "--exp", key)
    t = C.set_flag(t, "--output-base-dir", f"runs/{C.MODE}/{key}/train")
    t = C.set_flag(t, "--ap-feat-subset", sp["ap_subset"])
    t = C.set_flag(t, "--suffix", C.get_flag(t, "--suffix").replace(f"fs_{ORIG}/", f"fs_{sp['ap_subset']}/"))
    env = C.base_env(threads=2)
    with C.TrainLock() as L:
        rc, dt = C.run_logged(["-m", "BCacheSim.episodic_analysis.train"] + t, lp, env=env, cpuset=C.cpus())
        waited = L.waited
    out = C.parse_train_outputs(lp)
    if rc != 0 or out is None or any(v[1] == "NoExists" for v in out.values()):
        raise RuntimeError(f"train failed rc={rc}: {lp}")
    r = dict(key=key, out=out, secs=dt, wait=waited, label_file=None)
    os.makedirs(os.path.dirname(rec), exist_ok=True)
    json.dump(r, open(rec, "w"), indent=1)
    return r


# ------------------------------------------------------------------ WP10: table for this retrain (test: fit after training)
_FIT_LOCKS = {}


BIG = 8 * (1 << 20)                                   # AR: big-offset access class (end offset > 8 MiB), as WP2 §7
WP10_TABLES = os.path.join(C.P2, "wp10_schedule", "tables")


def probe_table(sp):
    """AR probe PB<c>: the same retrain's WP10 TB:pt table for small accesses; x c for big-offset accesses in load
    buckets b >= 3 (dev mechanism check only)."""
    c = float(sp["solver"][len("probe"):])
    src = os.path.join(WP10_TABLES, "dev", f"pt_{sp['inst']}_B_r{sp['rep']}.json")
    t = json.load(open(src))
    m = list(map(float, t["mult"]))
    big = [x * c if b >= 3 else x for b, x in enumerate(m)]
    return dict(name=f"{sp['solver']}_{sp['inst']}_B_r{sp['rep']}", window_min=10, edges=t["edges"],
                class_dims=[dict(feat="endoff", edges=[float(BIG)])], mult=[m, big],
                fit=dict(source=os.path.relpath(src, C.P2), probe_c=c))


def ensure_table(sp):
    tp = table_path(sp)
    if os.path.exists(tp):
        return tp
    os.makedirs(os.path.dirname(tp), exist_ok=True)
    if sp["solver"].startswith("probe"):
        assert C.MODE == "dev" and sp["inst"] in C.DEV8
        json.dump(probe_table(sp), open(tp, "w"), indent=1)
        return tp
    if sp["solver"].startswith("U"):                 # pooled table (cls_pool.py) + this instance's own day-1 edges
        hold = sp["inst"] if (C.MODE == "dev" and sp["inst"] in C.DEV8) else "all"   # DEV8: leave-one-out; else the all-DEV8 fit
        src = os.path.join(C.W, "tables", "dev", f"pool_loo_{hold}_{sp['base']}_{sp['solver'][1:]}.json")
        pk = os.path.join(C.WORK, "packs", C.MODE, f"{sp['inst']}_{sp['base']}_r{sp['rep']}.npz")
        if not os.path.exists(pk):
            rc, _ = C.run_logged([os.path.join(C.SRC, "cls_pack.py"), "--mode", C.MODE, "--insts", sp["inst"], "--arms",
                                  sp["base"], "--reps", str(sp["rep"])],
                                 os.path.join(C.LOGS, C.MODE, "fit", f"{sp['inst']}_{sp['base']}_r{sp['rep']}_pack.log"),
                                 env=C.base_env(threads=4))
            if rc != 0:
                raise RuntimeError(f"pack failed for {pk}")
        u = json.load(open(src))
        z = np.load(pk)
        t = dict(name=f"{sp['solver']}_{sp['inst']}_{sp['base']}_r{sp['rep']}", window_min=10, edges=z["edges"].tolist(),
                 class_dims=json.loads(str(z["class_dims"])), mult=u["mult"],
                 fit=dict(source=os.path.relpath(src, C.W), pooled_packs=u["packs"], solver=u["fit"]["solver"]))
        assert not any(k.rsplit("_", 2)[0] == sp["inst"] for k in u["packs"]), "held-out instance must not be in the pooled fit"
        json.dump(t, open(tp, "w"), indent=1)
        return tp
    if sp["name"][0] == "T" and C.MODE == "dev" and sp["inst"] in C.DEV8:       # WP10's own dev tables (read-only copy)
        shutil.copy2(os.path.join(WP10_TABLES, "dev", os.path.basename(tp)), tp)
        return tp
    pk = f"{sp['inst']}_{sp['base']}_r{sp['rep']}"
    lp = os.path.join(C.LOGS, C.MODE, "fit", f"{pk}.log")
    with _TL:
        plk = _FIT_LOCKS.setdefault("pack_" + pk, threading.Lock())
        lk = _FIT_LOCKS.setdefault(pk + ("m" if sp["solver"].endswith("m") else ""), threading.Lock())
    with plk:                                      # one pack per (inst, base, retrain), shared by every solver
        if not os.path.exists(os.path.join(C.WORK, "packs", C.MODE, f"{pk}.npz")):
            rc, _ = C.run_logged([os.path.join(C.SRC, "cls_pack.py"), "--mode", C.MODE, "--insts", sp["inst"], "--arms",
                                  sp["base"], "--reps", str(sp["rep"])], lp.replace(".log", "_pack.log"), env=C.base_env(threads=4))
            if rc != 0:
                raise RuntimeError(f"pack failed: {lp}")
    with lk:
        if os.path.exists(tp):
            return tp
        env = C.base_env(threads=1, extra={"NUMBA_NUM_THREADS": "1"})
        sol = ["ptm", "cdm"] if sp["solver"] in ("ptm", "cdm") else ["pt", "cd"]
        rc, _ = C.run_logged([os.path.join(C.SRC, "cls_fit.py"), "--mode", C.MODE, "--keys", pk, "--solvers"] + sol,
                             lp.replace(".log", f"_{sol[0]}.log"), env=env, py=C.SOLVER_PY)
        if rc != 0 or not os.path.exists(tp):
            raise RuntimeError(f"solve failed: {lp}")
    return tp


def same_table(p1, p2):
    a, b = json.load(open(p1)), json.load(open(p2))
    if a["edges"] != b["edges"] or a.get("class_dims") != b.get("class_dims"):
        return False
    ra, rb = np.ravel(a["mult"]), np.ravel(b["mult"])
    return bool(np.allclose(ra / ra[0], rb / rb[0], rtol=1e-9, atol=0))


# ------------------------------------------------------------------ simulate + converge (WP9 code, WP10 table option)
def sim_at(sp, base, th):
    key = sp["trial_key"]
    ttag = f"th_{th:.6f}"
    out = f"runs/{C.MODE}/{key}/converge/{ttag}"
    args = C.set_flag(list(base), "--ap-threshold", f"{th:.6f}")
    args = C.set_flag(args, "-o", out)
    args = C.set_flag(args, "--job-id", f"{key}__{ttag}")
    done = C.result_files(out)
    lp = os.path.join(C.LOGS, C.MODE, key, "converge", f"{ttag}.log")
    if not done:
        with C.SimSlot() as S:
            rc, dt = C.run_logged(["-m", "BCacheSim.cachesim.simulate_ap"] + args, lp, env=C.base_env(threads=2),
                                  cpuset=S.cpuset)
        log = open(lp).read()
        for p in ["Failed to load", "Bad file", "Traceback (most recent call last)"]:
            if p in log:
                raise RuntimeError(f"sim soft-fail '{p}': {lp}")
        done = C.result_files(out)
        if rc != 0 or not done:
            raise RuntimeError(f"sim failed rc={rc}: {lp}")
    r = C.load_result(done[0])["results"]
    return dict(threshold=th, wr=r["FlashWriteRate"], peak=r["PeakServiceTimeUtil1"], result_file=done[0])


def existing_points(sp):
    import glob
    root = os.path.join(C.WORK, "runs", C.MODE, sp["trial_key"], "converge")
    done, running = [], []
    for d in sorted(glob.glob(os.path.join(root, "th_*"))):
        th = float(os.path.basename(d)[3:])
        rf = C.result_files(os.path.relpath(d, C.WORK))
        if rf:
            r = C.load_result(rf[0])["results"]
            done.append(dict(threshold=th, wr=r["FlashWriteRate"], peak=r["PeakServiceTimeUtil1"], result_file=rf[0]))
        else:
            files = [x for x in glob.glob(os.path.join(d, "**", "*"), recursive=True) if os.path.isfile(x)]
            if files and time.time() - max(os.path.getmtime(x) for x in files) < 420:
                running.append(th)
    return done, running


def next_theta(tried, E, g, sched, T, hi=1.0):
    best = min(tried, key=lambda x: abs(x["wr"] - T))
    above = [x for x in tried if x["wr"] > T]
    below = [x for x in tried if x["wr"] < T]
    if above and below:
        a = min(above, key=lambda x: x["wr"])
        b = max(below, key=lambda x: x["wr"])
        if abs(b["threshold"] - a["threshold"]) < 3e-6:
            return None
        t = a["threshold"] + (a["wr"] - T) * (b["threshold"] - a["threshold"]) / (a["wr"] - b["wr"])
        lo, hi_ = sorted([a["threshold"], b["threshold"]])
        if not (lo < t < hi_):
            t = 0.5 * (lo + hi_)
        return t
    x = best
    goal = E.wr(g, x["threshold"], sched) * T / x["wr"]
    t = E.theta_for(g, goal, sched, hi=max(hi, 1.0))
    step = t - x["threshold"]
    need_up = x["wr"] > T
    if need_up and step <= 0.002:
        t = x["threshold"] + max(0.01, abs(step))
    if not need_up and step >= -0.002:
        t = x["threshold"] - max(0.01, abs(step))
    return t


def converge(sp, base, E, g, sched, kind="baleen", max_rounds=7):
    region = sp["inst"].split("_")[0]
    T = C.TARGET_WR
    th_hi = 4.0 if sched is not None else 0.9999      # (0, 4] for every adaptive arm (alpha or table), (0, 1) otherwise
    th_pred = E.theta_for(g, emu_target(region, kind, sp["inst"], sp["arm"], sp["design"]), sched, hi=th_hi)
    while True:
        tried, running = existing_points(sp)
        if not running:
            break
        time.sleep(60)
    best = min(tried, key=lambda x: abs(x["wr"] - T)) if tried else None
    th = th_pred
    for _ in range(max_rounds):
        if best is not None and abs(best["wr"] - T) / T <= C.TOL:
            break
        if len(tried) >= max_rounds:
            break
        if tried:
            th = next_theta(tried, E, g, sched, T, hi=th_hi)
            if th is None:
                break
        th = float(min(max(round(th, 6), 1e-4), th_hi))
        if any(abs(th - x["threshold"]) < 1e-6 for x in tried):
            if th >= th_hi - 1e-9 and th_hi > 1.0:
                break
            th = round(th + 2e-4, 6)
        r = sim_at(sp, base, th)
        r["emu_wr"] = E.wr(g, th, sched)
        with _LOCK:
            with open(PAIRS_(), "a") as f:
                f.write(json.dumps(dict(region=region, kind=kind, emu_wr=r["emu_wr"], sim_wr=r["wr"], key=sp["trial_key"])) + "\n")
        tried.append(r)
        best = min(tried, key=lambda x: abs(x["wr"] - T))
        print(f"[{sp['trial_key']}] round {len(tried) - 1}: th={th:.6f} WR={r['wr']:.3f} P100={r['peak']:.3f} "
              f"(best WR {best['wr']:.3f})", flush=True)
    return tried, best, th_pred


# ------------------------------------------------------------------ one evaluation
def done_rows():
    if not os.path.exists(C.TRIALS):
        return pd.DataFrame()
    return pd.read_csv(C.TRIALS)


def run_eval(sp):
    if os.path.exists(os.path.join(C.W, "STOP")):
        print(f"[stop] {sp['trial_key']} not started (STOP file)", flush=True)
        return None
    t0 = time.time()
    key = sp["trial_key"]
    base_row = {k: sp[k] for k in ("trial_key", "stage", "arm", "design", "inst", "rep", "ap_subset", "alpha", "solver")}
    base_row.update(region=sp["inst"].split("_")[0], sample=float(sp["inst"].split("_s")[1]))
    try:
        tr = train(sp)
        J = C.JOBS[sp["inst"]]["baleen"]
        base = C.fill_sim_args(list(J["sim_args"]), tr["out"])
        base = C.set_flag(base, "--ap-feat-subset", sp["ap_subset"])
        sched, tp = None, None
        if sp["alpha"] is not None:
            base = C.set_flag(base, "--ap-load-adapt-alpha", str(sp["alpha"]))
            sched = sp["alpha"]
        if sp["solver"]:
            tp = ensure_table(sp)
            base = C.set_flag(base, "--ap-load-adapt-table", os.path.relpath(tp, C.WORK))
            sched = json.load(open(tp))
            twin = {"cd": "pt", "cdm": "ptm", "Ucdm": "Uptm"}.get(sp["solver"])   # classical control -> its Ising twin
            if twin is not None and ":" in sp["name"]:  # WP10: scale-equivalent to the Ising table -> same policy family
                pt_sp = spec(sp["name"].split(":")[0] + ":" + twin.lstrip("U"), sp["inst"], sp["rep"])
                if same_table(tp, ensure_table(pt_sp)):     # AR: build the twin's table first (race fix)
                    while True:
                        d = done_rows()
                        hit = d[d.trial_key.astype(str) == pt_sp["trial_key"]] if len(d) else d
                        if len(hit):
                            break
                        time.sleep(60)
                    row = dict(hit.iloc[0])
                    row.update(base_row, reused_from=pt_sp["trial_key"], table=os.path.relpath(tp, C.W),
                               wall_secs=time.time() - t0, ts=time.strftime("%Y-%m-%dT%H:%M:%S"), error="")
                    C.append_csv(C.TRIALS, row)
                    print(f"== {key}: table scale-equivalent to {pt_sp['trial_key']} -> reused (P100 {row['p100']:.3f})", flush=True)
                    return row
        assert "--offline-ap-decisions" not in base and "--eviction-policy" in base
        E = get_emu(sp["inst"])
        g = E.scores(tr["out"]["model_admit_threshold_binary"][0], sp["ap_subset"])
        tried, best, th_pred = converge(sp, base, E, g, sched)
        df = pd.DataFrame(tried).sort_values("threshold")
        os.makedirs(os.path.join(C.RESULTS, "converge"), exist_ok=True)
        df.to_csv(os.path.join(C.RESULTS, "converge", f"{key}.csv"), index=False)
        m = C.metrics(best["result_file"])
        mech = E.mechanism(g, best["threshold"], sched, m["argmax"])
        fit = json.load(open(tp))["fit"] if tp else {}
        row = dict(base_row, train_key=tr["key"], table=os.path.relpath(tp, C.W) if tp else "",
                   table_mult=json.dumps(json.load(open(tp))["mult"]) if tp else "",
                   fit_peak_day1=fit.get("peak_day1", ""), threshold=best["threshold"], threshold_pred=th_pred,
                   n_sims=len(df), matched=bool(abs(best["wr"] - C.TARGET_WR) / C.TARGET_WR <= C.TOL),
                   wr=m["wr"], p100=m["p100"], p99=m["p99"], top5=m["top5"], mean_dt=m["mean_dt"], argmax=m["argmax"],
                   top5_windows=json.dumps(m["top5_windows"]), **mech, train_secs=tr.get("secs"),
                   wall_secs=time.time() - t0, result_file=os.path.relpath(best["result_file"], C.W), error="",
                   reused_from="", ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
        C.append_csv(C.TRIALS, row)
        print(f"== {key}: P100={m['p100']:.3f} WR={m['wr']:.3f} th={best['threshold']:.5f} (pred {th_pred:.4f}) "
              f"matched={row['matched']} n_sims={len(df)}", flush=True)
        return row
    except Exception as ex:
        traceback.print_exc()
        row = dict(base_row, trial_key=f"{key}__FAILED_{int(time.time())}", matched=False, error=repr(ex)[:300],
                   wall_secs=time.time() - t0, ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
        C.append_csv(C.TRIALS, row)
        return None


def extra_retrain_specs(names, insts):
    """(test, as PROTOCOL_v2_H4 §4) cells with < 3 matched retrains get the next seed (4, 5, 6) until 3 are matched."""
    d = done_rows()
    if not len(d):
        return []
    d = d[~d["trial_key"].astype(str).str.contains("__FAILED_")]
    out = []
    for n in names:
        arm = arm_def(n)["arm"]
        for i in insts:
            x = d[(d["arm"] == arm) & (d["inst"] == i)]
            n_ok = int((x["matched"].astype(str) == "True").sum())
            reps = set(x["rep"].astype(int))
            if n_ok < 3 and len(reps) > 0 and max(reps) < 6:
                out.append(spec(n, i, max(reps) + 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dev", "test"], default="dev")
    ap.add_argument("--arms", nargs="+", default=[])
    ap.add_argument("--insts", nargs="+", default=None)
    ap.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("-j", type=int, default=16)
    ap.add_argument("--queue", help="AR: file of 'arm inst rep' lines, run in this priority order (overrides --arms/--insts/--reps)")
    o = ap.parse_args()
    C.configure(o.mode)
    C.LOGS = os.path.join(C.W, "logs")
    insts = o.insts or {"dev": C.DEV8, "test": C.TEST}[o.mode]
    assert not any(C.is_reserve(i) for i in insts), "reserve samples are never touched"
    if o.mode == "dev":
        assert all(i in C.DEV and i not in C.FORBIDDEN_DEV for i in insts)
    else:
        assert os.path.exists(os.path.join(C.TEST_DIR, "TEST_GO")), "PROTOCOL.md not committed (no TEST_GO)"
        assert all(i in C.TEST for i in insts)
    os.makedirs(C.RESULTS, exist_ok=True)
    specs = [spec(n, i, r) for r in o.reps for n in o.arms for i in insts]
    if o.queue:
        q = [ln.split() for ln in open(o.queue) if ln.strip() and not ln.startswith("#")]
        specs = [spec(n, i, int(r)) for n, i, r in q]
        assert all(sp["inst"] in (C.DEV if o.mode == "dev" else C.TEST) for sp in specs)
        assert not any(C.is_reserve(sp["inst"]) or (o.mode == "dev" and sp["inst"] in C.FORBIDDEN_DEV) for sp in specs)
    d = done_rows()
    done = set(d.trial_key.astype(str)) if len(d) else set()
    todo = [s for s in specs if s["trial_key"] not in done]
    print(f"{len(specs)} evaluations planned, {len(todo)} to run", flush=True)
    with ThreadPoolExecutor(max_workers=o.j) as ex:
        list(ex.map(run_eval, todo))
    if o.mode == "test":
        for _ in range(3):
            d = done_rows()
            done = set(d.trial_key.astype(str))
            extra = [s for s in extra_retrain_specs(o.arms, insts) if s["trial_key"] not in done]
            if not extra:
                break
            print(f"[extra retrains] {[s['trial_key'] for s in extra]}", flush=True)
            with ThreadPoolExecutor(max_workers=o.j) as ex:
                list(ex.map(run_eval, extra))


if __name__ == "__main__":
    main()
