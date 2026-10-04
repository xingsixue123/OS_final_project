"""PROTOCOL_v2_H3 §5 evaluation, written BEFORE any test data exist (2026-10-04, WP3 preparation).

P100 = PeakServiceTimeUtil1, mean over MATCHED retrains per instance, over the instances.
  H3' = YES iff X1 (Ea-1.0:F1PT) meets, against A AND against B:
          wins >= 4/6 (mean P100 below the reference's) and mean improvement > 2 SE,
          SE = sqrt(sum_i s_X,i^2/n_X,i + s_R,i^2/n_R,i) / N (retrain-level; instance-level SE also reported),
        and its mean P100 is below RejectX's and CoinFlip's means (results/static_baselines.csv).
  H3'-labels = YES iff X1 meets the two conditions against A+alpha (Aa-1.0) AND B+alpha (Ba-1.0).
  X2 (Ea-0.5:F1PT): same rule, secondary (no claim). Dc+alpha (Ea-1.0:F1CPSAT): paired X1 - Dc+alpha, no pass/fail.
  Reported: P99, top-5, mean DT, WR, first-access admission, retention R = (A - X)/(OPT_peakblind - OPT_peakaware)
  with WP1's R0 and PT offline P100 (results/retention_inputs_wp1.csv), peak-window big-offset share.
  python src/evaluate_test.py [--trials trials.csv] [--insts ...]   (--trials/--insts let it be checked on WP2 dev data)
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(HERE)
TEST = [f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0.4", "0.5", "0.6")]
CFG = {"X1": ("Ea-1.0", "F1PT"), "X2": ("Ea-0.5", "F1PT"), "A": ("A", "baleen"), "B": ("B", "baleen"),
       "A+alpha": ("Aa-1.0", "baleen"), "B+alpha": ("Ba-1.0", "baleen"), "Dc+alpha": ("Ea-1.0", "F1CPSAT")}


def table(t, insts):
    t = t[(t["matched"].astype(str) == "True") & ~t["trial_key"].astype(str).str.contains("__FAILED_")]
    out = {}
    for name, (arm, design) in CFG.items():
        d = t[(t["arm"] == arm) & (t["design"] == design) & (t["inst"].isin(insts))]
        if len(d):
            out[name] = d.groupby("inst")["p100"].agg(["mean", "std", "count"]).reindex(insts)
    return out, t


def versus(T, x, ref, insts):
    X, R = T[x], T[ref]
    diff = (R["mean"] - X["mean"]).to_numpy()
    se = float(np.sqrt(np.nansum((X["std"] ** 2 / X["count"]).to_numpy() + (R["std"] ** 2 / R["count"]).to_numpy())) / len(insts))
    se_i = float(np.nanstd(diff, ddof=1) / np.sqrt(np.sum(~np.isnan(diff))))
    wins = int(np.nansum(diff > 0))
    return dict(X=x, ref=ref, wins=wins, n_inst=int(np.sum(~np.isnan(diff))), mean_improvement=float(np.nanmean(diff)),
                se_retrain=se, se_instance=se_i, min_matched=int(np.nanmin(X["count"])),
                ok=bool(wins >= 4 and np.nanmean(diff) > 2 * se), per_inst=" ".join(f"{v:+.2f}" for v in diff))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", default=os.path.join(W, "trials.csv"))
    ap.add_argument("--insts", nargs="+", default=TEST)
    ap.add_argument("--static", default=os.path.join(W, "results", "static_baselines.csv"))
    ap.add_argument("--out", default=os.path.join(W, "results", "evaluation.json"))
    o = ap.parse_args()
    T, t = table(pd.read_csv(o.trials), o.insts)
    res = {"instances": o.insts, "n_rows": int(len(t))}
    rows = []
    for x, refs in (("X1", ("A", "B", "A+alpha", "B+alpha", "Dc+alpha")), ("X2", ("A", "B"))):
        for r in refs:
            if x in T and r in T:
                rows.append(versus(T, x, r, o.insts))
    res["comparisons"] = rows
    st = pd.read_csv(o.static) if os.path.exists(o.static) else None
    if st is not None and "X1" in T:
        st = st[st["instance"].isin(o.insts)]
        rx = st[st.method == "RejectX"].set_index("instance")["p100"].reindex(o.insts).mean()
        cf = st[st.method == "CoinFlip"].set_index("instance")["p100"].reindex(o.insts).mean()
        res["baselines"] = dict(RejectX=float(rx), CoinFlip=float(cf))
        for x in ("X1", "X2"):
            if x in T:
                res[f"{x}_mean_p100"] = float(T[x]["mean"].mean())
                res[f"{x}_below_baselines"] = bool(T[x]["mean"].mean() < rx and T[x]["mean"].mean() < cf)
    get = {(r["X"], r["ref"]): r["ok"] for r in rows}
    if all(k in get for k in [("X1", "A"), ("X1", "B")]) and "X1_below_baselines" in res:
        res["H3prime"] = bool(get[("X1", "A")] and get[("X1", "B")] and res["X1_below_baselines"])
    if all(k in get for k in [("X1", "A+alpha"), ("X1", "B+alpha")]):
        res["H3prime_labels"] = bool(get[("X1", "A+alpha")] and get[("X1", "B+alpha")])
    if all(k in get for k in [("X2", "A"), ("X2", "B")]) and "X2_below_baselines" in res:
        res["X2_rule"] = bool(get[("X2", "A")] and get[("X2", "B")] and res["X2_below_baselines"])
    ret = os.path.join(W, "results", "retention_inputs_wp1.csv")
    if os.path.exists(ret) and "A" in T:
        rr = pd.read_csv(ret).set_index("instance").reindex(o.insts)
        den = (rr["R0"] - rr["pt"]).to_numpy()
        res["retention"] = {x: float(np.nanmean((T["A"]["mean"].to_numpy() - T[x]["mean"].to_numpy()) / den))
                            for x in T if x != "A"}
    sec = t[t["inst"].isin(o.insts)].copy()
    sec["cfg"] = sec["arm"] + ":" + sec["design"]
    res["secondary"] = sec.groupby("cfg")[["p100", "p99", "top5", "mean_dt", "wr", "k0_adm", "peak_adm",
                                            "peak_bigoff_share"]].mean().round(4).to_dict(orient="index")
    json.dump(res, open(o.out, "w"), indent=1, default=float)
    print(pd.DataFrame(rows).drop(columns=["per_inst"]).round(3).to_string(index=False))
    print({k: v for k, v in res.items() if k in ("baselines", "X1_mean_p100", "X1_below_baselines", "H3prime",
                                                  "H3prime_labels", "X2_rule", "retention")})


if __name__ == "__main__":
    main()
