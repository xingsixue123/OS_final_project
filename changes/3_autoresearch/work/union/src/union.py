"""3_autoresearch union driver (overlay v5, SCOPE_AMENDMENT.md item 1.2d): admit iff Baleen's model admits OR a second
model trained on min-max peak labels (F1, phase-1/WP2 formulation) admits, both under the load-adaptive threshold
(alpha = -1): score_A > theta*g(load)  OR  score_X > kappa*theta*g(load) [AND load_10m >= gate].
Re-uses cls.py (WP10/WP9/WP3/WP2 lineage) for training, threshold convergence (full sims, (0, 4]), metrics and ledger.

Arms (dev: WP2's retrains reused read-only; model A = A_baleen_<inst>_r<k>, model X = D_<labels>_<inst>_r<k>):
  XA:<labels>  union, no gate          labels F1PT (Ising, parallel tempering) | F1CPSAT (classical control, CP-SAT)
  XG:<labels>  union, second model only where load_10m >= the instance's day-1 access-level q75 of load_10m
kappa = theta_X* / theta_A*, the two models' own training-day thresholds at the same day-1 write budget (SchedEmu,
pooled seeding target), i.e. both models equally strict relative to their own budgets. Training day only.

  source env.sh && setsid nohup src/sbx.sh src/union.py --mode dev --arms XA:F1PT XG:F1PT --reps 1 -j 14 &
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
import wpcommon as C  # noqa: E402
sys.path.insert(0, C.WORK)
import cls as B  # noqa: E402  (base driver: train, converge, ledger)

ORIG, LOAD = B.ORIG, B.LOAD
LABELS = ("F1PT", "F1CPSAT")


def arm_def(name):
    if name in ("A", "B", "Aa", "Ba"):
        return B.arm_def_base(name)
    kind, lab = name.split(":")
    assert kind in ("XA", "XG") and lab in LABELS, name
    return dict(arm=f"{kind}-{lab}", ap=LOAD, alpha=-1.0, solver=lab, base="A")


B.arm_def_base = B.arm_def
B.arm_def = arm_def            # cls.spec() resolves arm_def at call time


def x_model(sp):
    """the second model's training record: DEV8 = WP2's D_<labels> retrain (copied read-only); otherwise trained here
    exactly as WP9/WP3 arm D (labels.py F1 solve with seed = retrain k on day1_<inst>.npz, then the overlay trainer with
    --policy PolicyPeakBaleen4 and --ap-feat-subset meta+block+chunk+load)."""
    key = f"D_{sp['solver']}_{sp['inst']}_r{sp['rep']}"
    if C.MODE == "dev" and sp["inst"] in C.DEV8:
        return B.wp2_model_out(key)
    with B._TL:
        lk = B._TRAIN_LOCKS.setdefault(key, threading.Lock())
    with lk:
        return _train_x(sp, key)


def _train_x(sp, key):
    rec = os.path.join(C.RESULTS, "train", f"{key}.json")
    if os.path.exists(rec):
        return json.load(open(rec))
    lab = os.path.join(C.LABELS, f"{sp['inst']}_{sp['solver']}_s{sp['rep']}.npz")
    if not os.path.exists(lab):
        rc, _ = C.run_logged([os.path.join(C.SRC, "labels.py"), "--inst", sp["inst"], "--design", sp["solver"], "--seed",
                              str(sp["rep"]), "--inst-dir", C.INST_DIR],
                             os.path.join(C.LOGS, C.MODE, "labels", f"{sp['inst']}_{sp['solver']}_s{sp['rep']}.log"),
                             env=C.base_env(threads=8), py=C.SOLVER_PY)
        if rc != 0 or not os.path.exists(lab):
            raise RuntimeError(f"label solve failed: {lab}")
    lp = os.path.join(C.LOGS, C.MODE, key, "train.log")
    J = C.JOBS[sp["inst"]]["baleen"]
    t = list(J["train_args"])
    t = C.set_flag(t, "--exp", key)
    t = C.set_flag(t, "--output-base-dir", f"runs/{C.MODE}/{key}/train")
    t = C.set_flag(t, "--ap-feat-subset", LOAD)
    t = C.set_flag(t, "--suffix", C.get_flag(t, "--suffix").replace(f"fs_{ORIG}/", f"fs_{LOAD}/"))
    t = C.set_flag(t, "--policy", "PolicyPeakBaleen4")
    cfgp = os.path.join(C.RESULTS, "cfg", f"{key}.json")
    os.makedirs(os.path.dirname(cfgp), exist_ok=True)
    json.dump({"labels": lab, "name": f"pb4_{sp['solver']}_r{sp['rep']}", "target_wr": C.TARGET_WR}, open(cfgp, "w"), indent=1)
    env = C.base_env(threads=2, extra={"HE_POLICY_CONFIG": cfgp})
    with C.TrainLock() as L:
        rc, dt = C.run_logged(["-m", "wp2_launch_train"] + t, lp, env=env, cpuset=C.cpus())
        waited = L.waited
    out = C.parse_train_outputs(lp)
    if rc != 0 or out is None or any(v[1] == "NoExists" for v in out.values()):
        raise RuntimeError(f"train failed rc={rc}: {lp}")
    assert "[PB4] call" in open(lp).read(), lp
    r = dict(key=key, out=out, secs=dt, wait=waited, label_file=lab)
    os.makedirs(os.path.dirname(rec), exist_ok=True)
    json.dump(r, open(rec, "w"), indent=1)
    return r


def union_params(sp, trA, trX):
    """kappa and gate from the training day only (cached per (inst, labels, retrain))."""
    p = os.path.join(C.W, "params", C.MODE, f"{sp['inst']}_{sp['solver']}_r{sp['rep']}.json")
    if os.path.exists(p):
        return json.load(open(p))
    import schedemu as SE
    E = B.get_emu(sp["inst"])
    S = SE.SchedEmu(E, "day1")
    region = sp["inst"].split("_")[0]
    a, b = (-1.288, 1.177) if region == "Region7" else (-0.770, 1.146) if region == "Region6" else (-1.029, 1.1615)
    tgt = float(np.exp((np.log(C.TARGET_WR) - a) / b))
    sA = E.scores(trA["out"]["model_admit_threshold_binary"][0], ORIG)[S.idx]
    sX = E.scores(trX["out"]["model_admit_threshold_binary"][0], LOAD)[S.idx]
    tA = S.budget_at_emu_wr(sA, tgt)["theta"]
    tX = S.budget_at_emu_wr(sX, tgt)["theta"]
    q75 = float(np.quantile(S.load_sub[S.admissible], 0.75))
    out = dict(kappa=float(tX / tA), theta_A_day1=float(tA), theta_X_day1=float(tX), gate_q75=q75, emu_target=tgt)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w"), indent=1)
    return out


def run_eval(sp):
    if os.path.exists(os.path.join(C.W, "STOP")):
        return None
    if sp["arm"][:2] not in ("XA", "XG"):
        return B.run_eval(sp)
    t0 = time.time()
    key = sp["trial_key"]
    base_row = {k: sp[k] for k in ("trial_key", "stage", "arm", "design", "inst", "rep", "ap_subset", "alpha", "solver")}
    base_row.update(region=sp["inst"].split("_")[0], sample=float(sp["inst"].split("_s")[1]))
    try:
        trA = B.train(sp)
        trX = x_model(sp)
        prm = union_params(sp, trA, trX)
        gate = prm["gate_q75"] if sp["arm"].startswith("XG") else None
        J = C.JOBS[sp["inst"]]["baleen"]
        base = C.fill_sim_args(list(J["sim_args"]), trA["out"])
        base = C.set_flag(base, "--ap-feat-subset", LOAD)                 # collected vector = the longer subset
        base = C.set_flag(base, "--ap-main-feat-subset", ORIG)
        base = C.set_flag(base, "--ap-union-model", trX["out"]["model_admit_threshold_binary"][0])
        base = C.set_flag(base, "--ap-union-feat-subset", LOAD)
        base = C.set_flag(base, "--ap-union-kappa", f"{prm['kappa']:.9g}")
        if gate is not None:
            base = C.set_flag(base, "--ap-union-gate-load", f"{gate:.9g}")
        base = C.set_flag(base, "--ap-load-adapt-alpha", "-1.0")
        assert "--offline-ap-decisions" not in base and "--eviction-policy" in base
        E = B.get_emu(sp["inst"])
        g = dict(a=E.scores(trA["out"]["model_admit_threshold_binary"][0], ORIG),
                 x=E.scores(trX["out"]["model_admit_threshold_binary"][0], LOAD), kappa=prm["kappa"],
                 gate=None if gate is None else (E.load[:, 0] >= gate))
        tried, best, th_pred = B.converge(sp, base, E, g, -1.0)
        df = pd.DataFrame(tried).sort_values("threshold")
        os.makedirs(os.path.join(C.RESULTS, "converge"), exist_ok=True)
        df.to_csv(os.path.join(C.RESULTS, "converge", f"{key}.csv"), index=False)
        m = C.metrics(best["result_file"])
        mech = E.mechanism(g, best["threshold"], -1.0, m["argmax"])
        row = dict(base_row, train_key=trA["key"], x_model=trX["key"], kappa=prm["kappa"], gate=gate if gate else "",
                   threshold=best["threshold"], threshold_pred=th_pred, n_sims=len(df),
                   matched=bool(abs(best["wr"] - C.TARGET_WR) / C.TARGET_WR <= C.TOL), wr=m["wr"], p100=m["p100"],
                   p99=m["p99"], top5=m["top5"], mean_dt=m["mean_dt"], argmax=m["argmax"],
                   top5_windows=json.dumps(m["top5_windows"]), **mech, wall_secs=time.time() - t0,
                   result_file=os.path.relpath(best["result_file"], C.W), error="", reused_from="",
                   ts=time.strftime("%Y-%m-%dT%H:%M:%S"))
        C.append_csv(C.TRIALS, row)
        print(f"== {key}: P100={m['p100']:.3f} WR={m['wr']:.3f} th={best['threshold']:.5f} (pred {th_pred:.4f}) "
              f"kappa={prm['kappa']:.3f} matched={row['matched']} n_sims={len(df)}", flush=True)
        return row
    except Exception as ex:
        traceback.print_exc()
        C.append_csv(C.TRIALS, dict(base_row, trial_key=f"{key}__FAILED_{int(time.time())}", matched=False,
                                    error=repr(ex)[:300], wall_secs=time.time() - t0,
                                    ts=time.strftime("%Y-%m-%dT%H:%M:%S")))
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["dev", "test"], default="dev")
    ap.add_argument("--arms", nargs="+", default=[])
    ap.add_argument("--insts", nargs="+", default=None)
    ap.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3])
    ap.add_argument("-j", type=int, default=14)
    ap.add_argument("--queue")
    o = ap.parse_args()
    C.configure(o.mode)
    C.LOGS = os.path.join(C.W, "logs")
    insts = o.insts or {"dev": C.DEV8, "test": C.TEST}[o.mode]
    assert not any(C.is_reserve(i) for i in insts)
    if o.mode == "dev":
        assert all(i in C.DEV and i not in C.FORBIDDEN_DEV for i in insts)
    else:
        assert os.path.exists(os.path.join(C.TEST_DIR, "TEST_GO")), "PROTOCOL.md not committed (no TEST_GO)"
        assert all(i in C.TEST for i in insts)
    os.makedirs(C.RESULTS, exist_ok=True)
    specs = [B.spec(n, i, r) for r in o.reps for n in o.arms for i in insts]
    if o.queue:
        specs = [B.spec(n, i, int(r)) for n, i, r in (ln.split() for ln in open(o.queue) if ln.strip() and not ln.startswith("#"))]
        assert all((sp["inst"] in C.DEV and sp["inst"] not in C.FORBIDDEN_DEV) if o.mode == "dev" else sp["inst"] in C.TEST
                   for sp in specs)
    d = B.done_rows()
    done = set(d.trial_key.astype(str)) if len(d) else set()
    todo = [s for s in specs if s["trial_key"] not in done]
    print(f"{len(specs)} evaluations planned, {len(todo)} to run", flush=True)
    with ThreadPoolExecutor(max_workers=o.j) as ex:
        list(ex.map(run_eval, todo))
    if o.mode == "test":                  # cells with < 3 matched retrains get seeds 4, 5, 6 (as WP9/WP10)
        for _ in range(3):
            d = B.done_rows()
            done = set(d.trial_key.astype(str))
            extra = [s_ for s_ in B.extra_retrain_specs(o.arms, insts) if s_["trial_key"] not in done]
            if not extra:
                break
            print(f"[extra retrains] {[s_['trial_key'] for s_ in extra]}", flush=True)
            with ThreadPoolExecutor(max_workers=o.j) as ex:
                list(ex.map(run_eval, extra))


if __name__ == "__main__":
    main()
