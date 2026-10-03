"""WP1 analysis: per-instance P100 table, reduction vs R0, win rate, peak-window migration, H1' verdict.

H1' (PLAN.md section 2): peak-aware offline selection beats Baleen's peak-blind oracle (R0) on >= 80% of the instances
across Regions 4-7 x samples 0-0.9, with a mean reduction >= 10%.  Evaluated separately for each peak-aware method
(LP+repair, CP-SAT 300 s, PT 300 s; phase-1 frozen configs, seed 0) on the instances where both R0 and the method
have a matched simulation (WR within 35.599 +-1%). Reduction = (P100_R0 - P100_M) / P100_R0. Win = P100_M < P100_R0.
Peak-window migration: simulated argmax window (10-min, after day 1) of R0 vs the method; the method's planned
(analytic) argmax window of the prefix the simulator admits (within f B, f = converged threshold / 35.599) vs its
simulated one.
Run with the solver env (numpy/scipy/pandas).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
WP1 = os.path.dirname(HERE)
P2 = os.path.dirname(WP1)
sys.path.insert(0, os.path.join(P2, "wp5_ising", "src"))
JOBS = json.load(open(os.path.join(WP1, "jobs.json")))["jobs"]
PH1 = "/home/sxing/project/OS_final_project/changes/1_literature_review/explore"
METHODS = ["lp", "cpsat", "pt"]
NAMES = {"R0": "Baleen peak-blind OPT (R0)", "lp": "LP+repair", "cpsat": "CP-SAT 300 s", "pt": "PT 300 s"}


def hhmm(w):
    """10-min window index (from trace start) -> 'd<day> hh:mm' (relative to the trace start)."""
    m = int(w) * 10
    return f"d{m // 1440} {(m % 1440) // 60:02d}:{m % 60:02d}"


def planned_argmax(inst_path, sol_path, f=1.0):
    import q2core as C
    I = C.Instance(inst_path)
    z = np.load(sol_path, allow_pickle=False)
    pos = {(str(k), float(t)): i for i, (k, t) in enumerate(zip(I.z["keys"], I.z["ts0"]))}
    order = np.array([pos[(str(k), float(t))] for k, t in zip(z["keys"], z["ts0"])], np.int64)
    cs = np.cumsum(I.s[order])
    kk = int(np.searchsorted(cs, min(f, 1.0) * I.B + 1e-9, side="right"))
    x = np.zeros(I.n)
    x[order[:kk]] = 1.0
    L = I.loads(x)
    return int(I.act_idx[int(np.argmax(L))]), float(L.max() * C.US)


def floor_util(inst_path):
    """analytic peak floor: max over objective windows of C_w - sum_e max(d(e,w), 0) (every saving admitted, budget
    ignored), util % -- a window whose floor equals the peak cannot be shaved by ANY admission choice."""
    import q2core as C
    I = C.Instance(inst_path)
    Dp = I.Da.copy()
    Dp.data = np.maximum(Dp.data, 0)
    L = I.Ca - np.asarray(Dp.sum(0)).ravel()
    return float(L.max() * C.US), int(I.act_idx[int(np.argmax(L))])


def load():
    sims = [json.loads(l) for l in open(os.path.join(WP1, "results", "sims.jsonl")) if l.strip()]
    df = pd.DataFrame(sims)
    df = df.sort_values("exp").drop_duplicates("exp", keep="last")
    return df


def main():
    df = load()
    tr = pd.read_csv(os.path.join(WP1, "trials.csv"))
    rows = []
    for k, J in JOBS.items():
        r = dict(instance=k, region=J["region"], sample=J["sample"], author_opt_p100=J["author_p100"])
        ipath = os.path.join(WP1, "inst", f"full_{k}.npz")
        if os.path.exists(ipath):
            r["floor"], r["floor_argmax"] = floor_util(ipath)
        d = df[df.instance == k]
        r0 = d[(d.method == "R0")]
        if len(r0):
            x = r0.iloc[-1]
            r.update(R0=x.p100, R0_wr=x.wr, R0_matched=bool(x.matched), R0_argmax=int(x["argmax"]),
                     R0_p99=x.p99, R0_top5=x.top5)
        for m in METHODS:
            t = tr[(tr.instance == f"full_{k}") & (tr.solver == m) & (tr.status == "ok")]
            if not len(t):
                continue
            tt = t.iloc[-1]
            exp = f"wp1_{k}_{m}_{tt.cfg_hash}_s{tt.seed}" + ("_rerun" if "rerun" in str(tt.tag) else "")
            dm = d[d.exp == exp]          # only the sim of the valid (status ok) solve
            if len(dm):
                x = dm.iloc[-1]
                r.update({m: x.p100, f"{m}_wr": x.wr, f"{m}_matched": bool(x.matched), f"{m}_argmax": int(x["argmax"]),
                          f"{m}_p99": x.p99, f"{m}_top5": x.top5, f"{m}_obj": float(tt.objective),
                          f"{m}_wall": float(tt.wall)})
                if True:
                    sol = t.iloc[-1].sol
                    sol = sol if os.path.isabs(sol) else os.path.join(WP1, sol)
                    ip = os.path.join(PH1, "common", "inst", f"full_{k}.npz") if \
                        t.iloc[-1].phase.startswith("wp1_reused") else os.path.join(WP1, "inst", f"full_{k}.npz")
                    try:
                        # the simulator's OPT AP admits the prefix whose harness-estimated cumulative write rate is
                        # <= the converged --ap-threshold, i.e. the prefix within f B, f = threshold / 35.599
                        pa, pv = planned_argmax(ip, sol, float(x.threshold) / 35.599)
                        r.update({f"{m}_plan_argmax": pa, f"{m}_plan_peak": pv})
                    except Exception as e:  # report, do not hide
                        r[f"{m}_plan_err"] = repr(e)[:80]
        rows.append(r)
    T = pd.DataFrame(rows).sort_values(["region", "sample"])
    T.to_csv(os.path.join(WP1, "results", "wp1_table.csv"), index=False)
    out = []
    out.append("| instance | author OPT | R0 | LP+repair | CP-SAT 300 s | PT 300 s | analytic floor (window) | R0 peak window | LP / CP-SAT / PT sim peak window | PT planned window |")
    out.append("|---|---|---|---|---|---|---|---|---|---|")
    for _, r in T.iterrows():
        def f(m):
            if m not in r or pd.isna(r.get(m)):
                return "-"
            s = f"{r[m]:.2f}"
            if not r.get(f"{m}_matched", True):
                s += " (unmatched)"
            return s
        aw = " / ".join(hhmm(r[f"{m}_argmax"]) if not pd.isna(r.get(f"{m}_argmax", np.nan)) else "-" for m in METHODS)
        fl = f"{r.floor:.2f} ({hhmm(r.floor_argmax)})" if not pd.isna(r.get("floor", np.nan)) else "-"
        out.append(f"| {r.instance} | {r.author_opt_p100:.2f} | {f('R0')} | {f('lp')} | {f('cpsat')} | {f('pt')} | {fl} | "
                   f"{hhmm(r.R0_argmax) if not pd.isna(r.get('R0_argmax', np.nan)) else '-'} | {aw} | "
                   f"{hhmm(r.pt_plan_argmax) if not pd.isna(r.get('pt_plan_argmax', np.nan)) else '-'} |")
    summ = []
    verdict = {}
    for m in METHODS:
        ok = T[(T.get("R0_matched") == True) & (T.get(f"{m}_matched") == True)]   # noqa: E712
        if not len(ok):
            continue
        red = (ok.R0 - ok[m]) / ok.R0 * 100
        wins = int((ok[m] < ok.R0).sum())
        n = len(ok)
        moved = int((ok[f"{m}_argmax"] != ok.R0_argmax).sum())
        plan_hit = int(((ok.get(f"{m}_plan_argmax") - ok[f"{m}_argmax"]).abs() <= 1).sum()) if f"{m}_plan_argmax" in ok else 0
        p = dict(method=m, n=n, wins=wins, win_rate=wins / n, mean_red_pct=float(red.mean()),
                 sd_red=float(red.std(ddof=1)) if n > 1 else float("nan"), min_red=float(red.min()),
                 max_red=float(red.max()), mean_R0=float(ok.R0.mean()), mean_M=float(ok[m].mean()),
                 moved=moved, plan_hit=plan_hit, pass_win=wins / n >= 0.8, pass_mean=float(red.mean()) >= 10.0)
        p["H1prime"] = bool(p["pass_win"] and p["pass_mean"])
        summ.append(p)
        verdict[m] = p
        per_reg = []
        for reg, g in ok.groupby("region"):
            rr = (g.R0 - g[m]) / g.R0 * 100
            per_reg.append(f"{reg}: {int((g[m] < g.R0).sum())}/{len(g)} wins, mean red {rr.mean():.1f}%")
        p["per_region"] = per_reg
    json.dump(dict(summary=summ, n_instances=len(T)), open(os.path.join(WP1, "results", "wp1_summary.json"), "w"),
              indent=1, default=float)
    print("\n".join(out))
    print()
    for p in summ:
        print(f"{NAMES[p['method']]}: n={p['n']} wins {p['wins']}/{p['n']} ({100 * p['win_rate']:.0f}%), mean reduction "
              f"{p['mean_red_pct']:.2f}% (sd {p['sd_red']:.2f}, min {p['min_red']:.2f}, max {p['max_red']:.2f}); "
              f"mean P100 {p['mean_M']:.2f} vs R0 {p['mean_R0']:.2f}; sim peak window moved vs R0 on {p['moved']}/{p['n']}; "
              f"planned peak window within +-1 window (10 min) of the simulated one on {p['plan_hit']}/{p['n']}; H1' {'PASS' if p['H1prime'] else 'FAIL'}")
        print("   ", "; ".join(p["per_region"]))
    with open(os.path.join(WP1, "results", "wp1_table.md"), "w") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
