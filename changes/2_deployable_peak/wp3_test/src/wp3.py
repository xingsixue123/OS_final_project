"""WP3 TEST driver for PROTOCOL_v2_H3 (copied from wp2_deployed/src/wp2.py; changes marked "WP3").
  * arms = PROTOCOL §3: X1 = Ea-1.0:F1PT, X2 = Ea-0.5:F1PT, A, B, A+alpha = Aa-1.0, B+alpha = Ba-1.0, Dc+alpha = Ea-1.0:F1CPSAT;
    the alpha arms re-use retrain k of their base arm (D:F1PT, D:F1CPSAT, A, B), trained on demand (base trainings
    without simulations for D/Dc unless the optional 2x2 plan is requested)
  * threshold search (0, 4] for every alpha arm, (0, 1) otherwise (PROTOCOL §3)
  * extra retrains with seeds 4, 5, 6 for (arm, instance) cells with < 3 matched retrains (PROTOCOL §4)
  * sources: --mode test (wp3_test/jobs.json, inst/, labels/, trials.csv) or --mode dev_dryrun (WP2 dev jobs/instances/
    labels; outputs in dryrun/) -- the dry run is the ONLY use of this driver before G3 is signed.
  * a test run refuses to start unless wp3_test/G3_SIGNED exists (created by the coordinator after the G3 review).

Original WP2 docstring:
WP2 deployed 2x2 study on DEV (Region7/Region6 x samples 0, 0.1, 0.2, 0.3), everything through the OVERLAY.

One evaluation = one retrain (new episode generation through the artifact's own train driver, new label-solver seed,
new GBMs) + --ap-threshold re-converged to 35.599 MB/s +-1% (sequential sims, seeded/steered by the emulator) +
metrics. Arms (PLAN.md WP2):
  A   Baleen labels (authors' policy),     original features (meta+block+chunk)
  B   Baleen labels,                       + load
  C   peak-aware labels (design, Ising),   original features
  D   peak-aware labels (design, Ising),   + load            (design F1CPSAT = arm Dc)
  D2  peak-aware labels,                   + load + tod
  Ea<alpha>   D's trained models (same retrain) + load-adaptive threshold alpha (simulation-only option)
  Epf         peak-aware labels + load, prefetch models with meta+load (Region7 only: Region6's Fig 9 variant has no
              ML prefetch model)
The authors' per-sample TrainCommand / ReproduceCommand (explore/common/jobs.json) are used unchanged apart from the
documented overlay options, --exp/-o/--job-id, --policy PolicyPeakBaleen4 (label arms) and --ap-threshold.
Every evaluation (also failures and unmatched ones) is one row of trials.csv (unique trial_key).

  source wp2_deployed/env.sh && cd wp2_deployed && taskset -c 8-11,20-23 $BALEEN_PY -B src/wp2.py --plan base
"""
import argparse
import json
import os
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "q3lib"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "work"))
import wpcommon as C  # noqa: E402

# WP3: trials / pairs / logs / runs follow C.configure() (test or dev dry run)
def TRIALS():
    return C.TRIALS


def PAIRS_():
    return os.path.join(C.RESULTS, "wrmap_pairs.jsonl")


_TRAIN_LOCKS = {}
_TL = threading.Lock()
ORIG = "meta+block+chunk"
LOAD = "meta+block+chunk+load"
LOADTOD = "meta+block+chunk+load+tod"
# log(sim WR) = a + b log(emu WR), seeding only. Initial maps from phase 1 (explore/q3/src/deployed3.py): the
# harness_eval fit for Baleen-label models, the q3 refit for PT-label models; refit online from this WP's own sims.
WRMAP0 = {("Region7", "baleen"): (-1.288, 1.177), ("Region6", "baleen"): (-0.770, 1.146),
          ("Region7", "peak"): (-0.138, 0.860), ("Region6", "peak"): (0.520, 0.801)}
_LOCK = threading.Lock()
_EMU_LOCK = threading.Lock()


# ------------------------------------------------------------------ specs
def spec(arm, design, inst, rep, stage, ap=ORIG, pf=None, alpha=None, reuse=None):
    key = f"{arm}_{design}_{inst}_r{rep}"
    return dict(trial_key=key, arm=arm, design=design, inst=inst, rep=rep, stage=stage, ap_subset=ap,
                pf_subset=pf, alpha=alpha, reuse=reuse)


TEST_ARMS = {   # WP3 (PROTOCOL §3): name -> (arm code, design, admission features, alpha, base retrain arm)
    "X1": ("Ea-1.0", "F1PT", LOAD, -1.0, "D"),
    "X2": ("Ea-0.5", "F1PT", LOAD, -0.5, "D"),
    "A": ("A", "baleen", ORIG, None, None),
    "B": ("B", "baleen", LOAD, None, None),
    "Aa": ("Aa-1.0", "baleen", ORIG, -1.0, "A"),
    "Ba": ("Ba-1.0", "baleen", LOAD, -1.0, "B"),
    "Dca": ("Ea-1.0", "F1CPSAT", LOAD, -1.0, "D"),
    # optional (2x2 / plain D), not part of the verdict
    "C": ("C", "F1PT", ORIG, None, None),
    "D": ("D", "F1PT", LOAD, None, None),
}


def test_spec(name, inst, rep):
    arm, design, ap, alpha, base = TEST_ARMS[name]
    reuse = None
    if base == "D":
        reuse = f"D_{design}_{inst}_r{rep}"
    elif base in ("A", "B"):
        reuse = f"{base}_baleen_{inst}_r{rep}"
    return spec(arm, design, inst, rep, "test" if C.RUNTAG == "" else "dryrun", ap=ap, alpha=alpha, reuse=reuse)


def plan(name, designs=None, insts=None, reps=None):
    insts = insts or C.DEV
    out = []
    if name in TEST_ARMS:                    # WP3
        return [test_spec(name, i, r) for r in (reps or (1, 2, 3)) for i in insts]
    if name == "base":                       # arms A and B, 3 retrains, rep-major order
        for r in reps or (1, 2, 3):
            for i in insts:
                out += [spec("A", "baleen", i, r, "base"), spec("B", "baleen", i, r, "base", ap=LOAD)]
    elif name in ("C", "D", "D2"):
        ap = {"C": ORIG, "D": LOAD, "D2": LOADTOD}[name]
        for r in reps or (1,):
            for i in insts:                  # instance-major: every design covered early
                for d in designs:
                    out.append(spec(name, d, i, r, "screen" if r == 1 else "confirm", ap=ap))
    elif name.startswith("Ea"):              # simulation-only variant of D's retrains
        alpha = float(name[2:])
        for r in reps or (1,):
            for d in designs:
                for i in insts:
                    out.append(spec(name, d, i, r, "screen" if r == 1 else "confirm", ap=LOAD, alpha=alpha,
                                    reuse=f"D_{d}_{i}_r{r}"))
    elif name.startswith(("Ax", "Bx")):      # the same controls with the theta search widened to (0, 4]
        alpha = float(name[2:])
        base_arm = name[0]
        for r in reps or (1,):
            for i in insts:
                out.append(spec(name, "baleen", i, r, "control", ap=ORIG if base_arm == "A" else LOAD, alpha=alpha,
                                reuse=f"{base_arm}_baleen_{i}_r{r}"))
    elif name.startswith("Ex"):              # Ea with the theta search widened to (0, 4]
        alpha = float(name[2:])
        for r in reps or (1,):
            for d in designs:
                for i in insts:
                    out.append(spec(name, d, i, r, "screen" if r == 1 else "confirm", ap=LOAD, alpha=alpha,
                                    reuse=f"D_{d}_{i}_r{r}"))
    elif name.startswith(("Aa", "Ba")):      # CONTROL: Baleen's own models (arm A or B retrain) + the same adaptive alpha
        alpha = float(name[2:])
        base_arm = name[0]
        for r in reps or (1,):
            for i in insts:
                out.append(spec(name, "baleen", i, r, "control", ap=ORIG if base_arm == "A" else LOAD, alpha=alpha,
                                reuse=f"{base_arm}_baleen_{i}_r{r}"))
    elif name == "Epf":
        for r in reps or (1,):
            for d in designs:
                for i in [x for x in insts if x.startswith("Region7")]:
                    out.append(spec("Epf", d, i, r, "screen" if r == 1 else "confirm", ap=LOAD, pf="meta+load"))
    else:
        raise ValueError(name)
    return out


# ------------------------------------------------------------------ write-rate map (seeding only)
def wrmap(region, kind):
    a, b = WRMAP0[(region, kind)]
    if os.path.exists(PAIRS_()):
        rows = [json.loads(x) for x in open(PAIRS_())]
        rows = [r for r in rows if r["region"] == region and r["kind"] == kind and r["emu_wr"] > 0 and r["sim_wr"] > 0]
        if len(rows) >= 4:
            x = np.log([r["emu_wr"] for r in rows][-40:])
            y = np.log([r["sim_wr"] for r in rows][-40:])
            if np.ptp(x) > 0.05:
                b_ = float(np.clip(np.polyfit(x, y, 1)[0], 0.5, 1.5))
            else:
                b_ = b
            a, b = float(np.mean(y - b_ * x)), b_
    return a, b


def _inst_of(key):
    p = key.split("_")
    return f"{p[2]}_{p[3]}"


def emu_target(region, kind, inst=None, arm=None, design=None):
    """Emulated WR that maps to the target: regional log-linear map + the mean residual of earlier sims of the same
    instance and configuration (arm, design), else of the same instance and label kind (seeding only)."""
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


# ------------------------------------------------------------------ train
def train(sp):
    key = sp["reuse"] or sp["trial_key"]
    rec = os.path.join(C.RESULTS, "train", f"{key}.json")
    lp = os.path.join(C.LOGS, key, "train.log")
    if sp["reuse"]:                           # WP3: train the base retrain on demand (one thread per key)
        p_ = sp["reuse"].split("_")
        b_arm, b_design, b_inst, b_rep = p_[0], p_[1], f"{p_[2]}_{p_[3]}", int(p_[4][1:])
        b_ap = ORIG if b_arm == "A" else LOAD
        base_sp = spec(b_arm, b_design, b_inst, b_rep, "base", ap=b_ap)
        assert base_sp["trial_key"] == sp["reuse"], (base_sp["trial_key"], sp["reuse"])
        return train(base_sp)
    with _TL:
        lk = _TRAIN_LOCKS.setdefault(key, threading.Lock())
    with lk:
        return _train(sp, key, rec, lp)


def _train(sp, key, rec, lp):
    if os.path.exists(rec):
        return json.load(open(rec))
    # resume: a training finished (or still running, e.g. orphaned by a driver restart) without its record
    while os.path.exists(lp) and "Filenames generated:" not in open(lp).read() and time.time() - os.path.getmtime(lp) < 900:
        time.sleep(30)
    if os.path.exists(lp):
        out = C.parse_train_outputs(lp)
        if out is not None and all(v[1] != "NoExists" for v in out.values()):
            lab = os.path.join(C.LABELS, f"{sp['inst']}_{sp['design']}_s{sp['rep']}.npz") if sp["design"] != "baleen" else None
            r = dict(key=key, out=out, secs=float("nan"), wait=float("nan"), label_file=lab, resumed=True)
            os.makedirs(os.path.dirname(rec), exist_ok=True)
            json.dump(r, open(rec, "w"), indent=1)
            return r
    J = C.JOBS[sp["inst"]]["baleen"]
    t = list(J["train_args"])
    t = C.set_flag(t, "--exp", key)
    t = C.set_flag(t, "--output-base-dir", f"runs/{key}/train")
    t = C.set_flag(t, "--ap-feat-subset", sp["ap_subset"])
    suf = C.get_flag(t, "--suffix").replace(f"fs_{ORIG}/", f"fs_{sp['ap_subset']}/")
    if sp["pf_subset"]:
        t = C.set_flag(t, "--pf-feat-subset", sp["pf_subset"])
        suf = suf.replace("/accs_15", f"_pf_{sp['pf_subset']}/accs_15")
    t = C.set_flag(t, "--suffix", suf)
    extra = {}
    lab = None
    if sp["design"] != "baleen":
        lab = os.path.join(C.LABELS, f"{sp['inst']}_{sp['design']}_s{sp['rep']}.npz")
        assert os.path.exists(lab), f"label file missing: {lab}"
        cfgp = os.path.join(C.RESULTS, "cfg", f"{key}.json")
        os.makedirs(os.path.dirname(cfgp), exist_ok=True)
        json.dump({"labels": lab, "name": f"pb4_{sp['design']}_r{sp['rep']}", "target_wr": C.TARGET_WR},
                  open(cfgp, "w"), indent=1)
        extra["HE_POLICY_CONFIG"] = cfgp
        t = C.set_flag(t, "--policy", "PolicyPeakBaleen4")
    env = C.base_env(threads=2, extra=extra)
    with C.TrainLock() as L:
        rc, dt = C.run_logged(["-m", "wp2_launch_train"] + t, lp, env=env, cpuset=C.cpus())
        waited = L.waited
    out = C.parse_train_outputs(lp)
    if rc != 0 or out is None or any(v[1] == "NoExists" for v in out.values()):
        raise RuntimeError(f"train failed rc={rc}: {lp}")
    txt = open(lp).read()
    if lab:
        assert "[PB4] call" in txt, lp
    r = dict(key=key, out=out, secs=dt, wait=waited, label_file=lab)
    os.makedirs(os.path.dirname(rec), exist_ok=True)
    json.dump(r, open(rec, "w"), indent=1)
    return r


# ------------------------------------------------------------------ simulate + converge
def sim_at(sp, base, th):
    key = sp["trial_key"]
    ttag = f"th_{th:.6f}"
    out = f"runs/{key}/converge/{ttag}"
    args = C.set_flag(list(base), "--ap-threshold", f"{th:.6f}")
    args = C.set_flag(args, "-o", out)
    args = C.set_flag(args, "--job-id", f"{key}__{ttag}")
    done = C.result_files(out)
    lp = os.path.join(C.LOGS, key, "converge", f"{ttag}.log")
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
    """Completed sims of this evaluation (re-used on resume) and sims still running (artifact lock touched < 7 min)."""
    import glob
    root = os.path.join(C.WORK, "runs", sp["trial_key"], "converge")
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
                running.append(th)                      # lock / logs / partial dumps touched recently
    return done, running


def next_theta(tried, E, g, alpha, T, hi=1.0):
    best = min(tried, key=lambda x: abs(x["wr"] - T))
    above = [x for x in tried if x["wr"] > T]
    below = [x for x in tried if x["wr"] < T]
    if above and below:
        a = min(above, key=lambda x: x["wr"])
        b = max(below, key=lambda x: x["wr"])
        if abs(b["threshold"] - a["threshold"]) < 3e-6:
            return None                                 # WR step between adjacent thresholds: cannot match
        t = a["threshold"] + (a["wr"] - T) * (b["threshold"] - a["threshold"]) / (a["wr"] - b["wr"])
        lo, hi = sorted([a["threshold"], b["threshold"]])
        if not (lo < t < hi):
            t = 0.5 * (lo + hi)
        return t
    x = best
    goal = E.wr(g, x["threshold"], alpha) * T / x["wr"]
    t = E.theta_for(g, goal, alpha, hi=max(hi, 1.0))
    step = t - x["threshold"]
    need_up = x["wr"] > T                               # too many writes -> higher threshold
    if need_up and step <= 0.002:
        t = x["threshold"] + max(0.01, abs(step))
    if not need_up and step >= -0.002:
        t = x["threshold"] - max(0.01, abs(step))
    return t


def converge(sp, base, E, g, kind, max_rounds=7):
    region = sp["inst"].split("_")[0]
    T = C.TARGET_WR
    alpha = sp["alpha"]
    th_hi = 4.0 if alpha is not None else 0.9999      # WP3 / PROTOCOL §3: (0, 4] for every alpha arm, (0, 1) otherwise
    th_pred = E.theta_for(g, emu_target(region, kind, sp["inst"], sp["arm"], sp["design"]), alpha, hi=th_hi)
    while True:
        tried, running = existing_points(sp)
        if not running:
            break
        time.sleep(60)
    for r in tried:
        r["emu_wr"] = E.wr(g, r["threshold"], alpha)
    best = min(tried, key=lambda x: abs(x["wr"] - T)) if tried else None
    th = th_pred
    for rnd in range(max_rounds):
        if best is not None and abs(best["wr"] - T) / T <= C.TOL:
            break
        if len(tried) >= max_rounds:
            break
        if tried:
            th = next_theta(tried, E, g, alpha, T, hi=th_hi)
            if th is None:
                break
        th = float(min(max(round(th, 6), 1e-4), th_hi))
        if any(abs(th - x["threshold"]) < 1e-6 for x in tried):
            if th >= th_hi - 1e-9 and th_hi > 1.0:
                break                                   # already at the widened bound
            th = round(th + 2e-4, 6)
        r = sim_at(sp, base, th)
        r["emu_wr"] = E.wr(g, th, alpha)
        with _LOCK:
            with open(PAIRS_(), "a") as f:
                f.write(json.dumps(dict(region=region, kind=kind, emu_wr=r["emu_wr"], sim_wr=r["wr"], key=sp["trial_key"])) + "\n")
        tried.append(r)
        best = min(tried, key=lambda x: abs(x["wr"] - T))
        print(f"[{sp['trial_key']}] round {len(tried) - 1}: th={th:.6f} WR={r['wr']:.3f} P100={r['peak']:.3f} "
              f"(best WR {best['wr']:.3f})", flush=True)
    return tried, best, th_pred


# ------------------------------------------------------------------ one evaluation
def done_keys():
    if not os.path.exists(TRIALS()):
        return set()
    return set(pd.read_csv(TRIALS())["trial_key"].astype(str))


def label_stats(path):
    if not path:
        return {}
    s = json.load(open(path.replace(".npz", ".json")))
    return dict(n_label=s["n_label"], n_core=s["n_core"], jaccard_vs_baleen=s["jaccard_vs_baleen"],
                label_peak_day1=s["label_peak_util"], baleen_peak_day1=s["baleen_peak_util"],
                zero_value_labels=s["zero_value_labels"], label_dt_ratio=s["dt_ratio"])


def run_eval(sp):
    if os.path.exists(os.path.join(C.W, "STOP")):
        print(f"[stop] {sp['trial_key']} not started (STOP file)", flush=True)
        return None
    t0 = time.time()
    key = sp["trial_key"]
    base_row = {k: sp[k] for k in ("trial_key", "stage", "arm", "design", "inst", "rep", "ap_subset", "pf_subset", "alpha")}
    base_row.update(region=sp["inst"].split("_")[0], sample=float(sp["inst"].split("_s")[1]))
    try:
        tr = train(sp)
        J = C.JOBS[sp["inst"]]["baleen"]
        base = C.fill_sim_args(list(J["sim_args"]), tr["out"])
        base = C.set_flag(base, "--ap-feat-subset", sp["ap_subset"])
        if sp["pf_subset"]:
            base = C.set_flag(base, "--pf-feat-subset", sp["pf_subset"])
        if sp["alpha"] is not None:
            base = C.set_flag(base, "--ap-load-adapt-alpha", str(sp["alpha"]))
        assert "--offline-ap-decisions" not in base and "--eviction-policy" in base
        E = get_emu(sp["inst"])
        g = E.scores(tr["out"]["model_admit_threshold_binary"][0], sp["ap_subset"])
        kind = "baleen" if sp["design"] == "baleen" else "peak"
        tried, best, th_pred = converge(sp, base, E, g, kind)
        df = pd.DataFrame(tried).sort_values("threshold")
        os.makedirs(os.path.join(C.RESULTS, "converge"), exist_ok=True)
        df.to_csv(os.path.join(C.RESULTS, "converge", f"{key}.csv"), index=False)
        m = C.metrics(best["result_file"])
        mech = E.mechanism(g, best["threshold"], sp["alpha"], m["argmax"])
        row = dict(base_row, train_key=tr["key"], label_file=os.path.relpath(tr["label_file"], C.W) if tr.get("label_file") else "",
                   threshold=best["threshold"], threshold_pred=th_pred, n_sims=len(df),
                   matched=bool(abs(best["wr"] - C.TARGET_WR) / C.TARGET_WR <= C.TOL),
                   wr=m["wr"], p100=m["p100"], p99=m["p99"], top5=m["top5"], mean_dt=m["mean_dt"], argmax=m["argmax"],
                   top5_windows=json.dumps(m["top5_windows"]), **mech, **label_stats(tr.get("label_file")),
                   train_secs=tr["secs"], train_wait=tr["wait"], wall_secs=time.time() - t0,
                   result_file=os.path.relpath(best["result_file"], C.W), error="", ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
        C.append_csv(TRIALS(), row)
        print(f"== {key}: P100={m['p100']:.3f} WR={m['wr']:.3f} th={best['threshold']:.5f} (pred {th_pred:.4f}) "
              f"matched={row['matched']} n_sims={len(df)} k0_adm={mech['k0_adm']:.3f}", flush=True)
        return row
    except Exception as ex:
        traceback.print_exc()
        row = dict(base_row, trial_key=f"{key}__FAILED_{int(time.time())}", matched=False, error=repr(ex)[:300],
                   wall_secs=time.time() - t0, ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
        C.append_csv(TRIALS(), row)
        return None


def extra_retrain_specs(names, insts):
    """PROTOCOL §4: cells with < 3 matched retrains get the next seed (4, 5, 6) until 3 are matched."""
    if not os.path.exists(TRIALS()):
        return []
    t = pd.read_csv(TRIALS())
    t = t[~t["trial_key"].astype(str).str.contains("__FAILED_")]
    out = []
    for n in names:
        arm, design = TEST_ARMS[n][0], TEST_ARMS[n][1]
        for i in insts:
            d = t[(t["arm"] == arm) & (t["design"] == design) & (t["inst"] == i)]
            n_ok = int((d["matched"].astype(str) == "True").sum())
            reps = set(d["rep"].astype(int))
            if n_ok < 3 and len(reps) > 0 and max(reps) < 6:
                out.append(test_spec(n, i, max(reps) + 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["test", "dev_dryrun"], default="test")
    ap.add_argument("--arms", nargs="*", default=[], help="WP3 test arms: X1 X2 A B Aa Ba Dca (+ optional C D)")
    ap.add_argument("--plan", nargs="*", default=[], help="base | C | D | D2 | Ea<alpha> | Epf")
    ap.add_argument("--designs", nargs="+", default=["P0", "T2", "C2", "F1PT", "F1EIM"])
    ap.add_argument("--insts", nargs="+", default=None)
    ap.add_argument("--reps", type=int, nargs="+", default=None)
    ap.add_argument("-j", type=int, default=12, help="concurrent evaluations (sims are capped by SimSlot)")
    ap.add_argument("--queue", help='JSON list of [plan, designs, reps] run in this order (priority)')
    o = ap.parse_args()
    C.configure(o.mode)
    if o.mode == "test":
        assert os.path.exists(os.path.join(C.W, "G3_SIGNED")), "G3 not signed: refusing to run any test arm"
        assert not o.queue and not o.plan, "test mode runs only --arms"
        assert all(i in C.TEST for i in (o.insts or C.TEST))
    else:
        assert o.insts and all(i in C.DEV for i in o.insts), "dry run: dev instances only"
    os.makedirs(C.RESULTS, exist_ok=True)
    specs = []
    for n in o.arms:
        specs += [test_spec(n, i, r) for r in (tuple(o.reps) if o.reps else (1, 2, 3)) for i in (o.insts or C.TEST)]
    if o.queue:
        for item in json.loads(o.queue):
            p, ds, rs = item[:3]
            specs += plan(p, ds, item[3] if len(item) > 3 else o.insts, tuple(rs))
    for p in o.plan:
        specs += plan(p, o.designs, o.insts, tuple(o.reps) if o.reps else None)
    done = done_keys()
    todo = [s for s in specs if s["trial_key"] not in done]
    print(f"{len(specs)} evaluations planned, {len(todo)} to run", flush=True)
    with ThreadPoolExecutor(max_workers=o.j) as ex:
        list(ex.map(run_eval, todo))
    if o.mode == "test" and o.arms:            # PROTOCOL §4: extra retrains until 3 matched (max seed 6)
        for _ in range(3):
            extra = [s for s in extra_retrain_specs(o.arms, o.insts or C.TEST) if s["trial_key"] not in done_keys()]
            if not extra:
                break
            print(f"[extra retrains] {[s['trial_key'] for s in extra]}", flush=True)
            with ThreadPoolExecutor(max_workers=o.j) as ex:
                list(ex.map(run_eval, extra))


if __name__ == "__main__":
    main()
