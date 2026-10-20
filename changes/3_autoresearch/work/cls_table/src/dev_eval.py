"""Dev evaluation for DEV_RULES.md (R0/R1): screen gate (retrain 1) and finalist rule (>= 3 matched retrains).
References: DEV8 = WP2 trials (A, B, A+alpha = Aa-1.0 U Ax-1.0, B+alpha = Ba-1.0 U Bx-1.0), DEV_EXTRA = this dir's
trials_dev.csv (A, B, Aa-1.0, Ba-1.0). Also reports WP10's TB-pt / TA-pt dev trials (same WP2 models) for context.

  python3 src/dev_eval.py screen [--arms ...]        # rep-1 screen table + gate
  python3 src/dev_eval.py final  [--arms ...]        # finalist rule (contract §4 on dev)
"""
import argparse
import math
import os

import numpy as np
import pandas as pd

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.normpath(os.path.join(H, "..", "..", ".."))
WP2 = os.path.join(CH, "2_deployable_peak", "wp2_deployed", "trials.csv")
WP10 = os.path.join(CH, "2_deployable_peak", "wp10_schedule", "trials_dev.csv")
DEV8 = [f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]
EXTRA = ["Region5_s0", "Region1_s0"]
REFMAP = {"A": ["A"], "B": ["B"], "A+a": ["Aa-1.0", "Ax-1.0"], "B+a": ["Ba-1.0", "Bx-1.0"]}


def matched(d):
    d = d[~d.trial_key.astype(str).str.contains("__FAILED_")]
    return d[d.matched.astype(str) == "True"]


def load():
    w2 = matched(pd.read_csv(WP2))
    own = matched(pd.read_csv(os.path.join(H, "trials_dev.csv"))) if os.path.exists(os.path.join(H, "trials_dev.csv")) else pd.DataFrame(columns=w2.columns)
    w10 = matched(pd.read_csv(WP10))
    rows = []
    for ref, arms in REFMAP.items():
        x = w2[w2.arm.isin(arms) & w2.inst.isin(DEV8)]
        rows.append(x.assign(cfg=ref))
        y = own[own.arm.isin(arms) & own.inst.isin(EXTRA)]
        rows.append(y.assign(cfg=ref))
    for a in ("TB-pt", "TA-pt"):
        rows.append(w10[w10.arm == a].assign(cfg="wp10:" + a))
    rows.append(own[~own.arm.isin(sum(REFMAP.values(), []))].assign(cfg=lambda z: z.arm))
    t = pd.concat(rows, ignore_index=True)
    t["rep"] = t.rep.astype(int)
    return t[["cfg", "inst", "rep", "p100", "wr", "threshold", "n_sims", "peak_adm", "peak_bigoff_share", "k0_adm"]]


def screen(t, arms):
    r1 = t[t.rep == 1]
    P = r1.pivot_table(index="inst", columns="cfg", values="p100", aggfunc="mean")
    insts = [i for i in DEV8 + EXTRA if i in P.index and not P.loc[i, ["A+a", "B+a"]].isna().any()]
    P = P.loc[insts]
    out = []
    for a in arms:
        if a not in P.columns:
            continue
        ok = P[a].notna()
        d = np.minimum(P["A+a"], P["B+a"]) - P[a]
        dd = d[ok]
        out.append(dict(cfg=a, n=int(ok.sum()), mean_d=dd.mean(), min_d=dd.min(), wins=int((dd > 0).sum()),
                        mean_p100=P.loc[ok, a].mean(), ref_minalpha=np.minimum(P["A+a"], P["B+a"])[ok].mean(),
                        gate=bool(dd.mean() > 0 and dd.min() >= -2.0 and ok.sum() == len(insts))))
    pd.set_option("display.width", 250)
    print("rep-1 P100 per instance:")
    cols = ["A", "B", "A+a", "B+a"] + [c for c in ("wp10:TB-pt", "wp10:TA-pt") if c in P.columns] + [a for a in arms if a in P.columns]
    print(P[cols].round(2).to_string())
    print(P[cols].mean().round(3).to_string())
    print("\nscreen gate (R0): d_i = min(A+a, B+a)_i - X_i (rep 1)")
    print(pd.DataFrame(out).round(3).to_string())
    return out


def final(t, arms):
    G = t.groupby(["cfg", "inst"]).p100
    M, S, N = G.mean().unstack(0), G.var(ddof=1).unstack(0), G.count().unstack(0)
    insts = [i for i in DEV8 + EXTRA if i in M.index and all(N.loc[i].get(r, 0) >= 3 for r in REFMAP)]
    best = "A+a" if M.loc[insts, "A+a"].mean() <= M.loc[insts, "B+a"].mean() else "B+a"
    n = len(insts)
    need = math.ceil(2 * n / 3)
    res = []
    for a in arms:
        if a not in M.columns or any(N.loc[i].get(a, 0) < 3 for i in insts):
            res.append(dict(cfg=a, eligible=False))
            continue
        row = dict(cfg=a, eligible=True, n=n, mean=M.loc[insts, a].mean())
        ok = True
        for ref in ("A", "B", best):
            d = M.loc[insts, ref] - M.loc[insts, a]
            se = math.sqrt(sum(S.loc[i, a] / N.loc[i, a] + S.loc[i, ref] / N.loc[i, ref] for i in insts)) / n
            w = int((d > 0).sum())
            c = w >= need and d.mean() > 2.5 * se and d.min() >= -2.0
            ok &= c
            row.update({f"{ref}_wins": w, f"{ref}_mean": d.mean(), f"{ref}_se": se, f"{ref}_worst": d.min(), f"{ref}_ok": c})
        row["qualifies"] = ok
        res.append(row)
    pd.set_option("display.width", 250)
    print(f"finalist rule on n={n} dev instances {insts}; best alpha = {best}; need wins >= {need}")
    print(M.loc[insts].round(2).to_string())
    print(pd.DataFrame(res).round(3).T.to_string())
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["screen", "final"])
    ap.add_argument("--arms", nargs="+", default=["CB-pt", "CA-pt", "CB-ptm", "CA-ptm", "CB-cd", "CA-cd", "CB-cdm", "CA-cdm",
                                                    "PB-0.5", "PB-0.25"])
    o = ap.parse_args()
    t = load()
    screen(t, o.arms) if o.what == "screen" else final(t, o.arms)
