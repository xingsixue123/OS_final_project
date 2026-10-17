"""PROTOCOL_v2_H4 §5 evaluation (WP9, Region5), written BEFORE any test data exist (2026-10-16); adapted from
wp3_test/src/evaluate_test.py (functions table/versus unchanged).

P100 = PeakServiceTimeUtil1, mean over MATCHED retrains per instance, over the 6 test instances (Region5 s0.1-0.6).
Rule (X vs ref): wins >= 4/6 (mean P100 below the reference's) and mean improvement (ref - X) > 2 SE,
  SE = sqrt(sum_i s_X,i^2/n_X,i + s_R,i^2/n_R,i) / N (retrain-level); instance-level SE reported too.
  H4 (primary)  = YES iff A+alpha (Aa-1.0) meets the rule vs A AND vs B, and its mean P100 is below RejectX's and
                  CoinFlip's means (results/static_baselines.csv; RejectX also with the below-WR-step replays,
                  results/static_rejectx_bracket.csv, since no RejectX probability matches +-1% on 5/6 instances).
  B+alpha (secondary) = the same rule vs A and B (reported; no claim).
  X1 (Ea-1.0:F1PT) vs A, B, A+alpha: the rule is reported (Ising record), no pass/fail beyond that.
  Reported: P99, top-5, mean DT, WR, first-access admission, peak-window admission / big-offset share, retention
  R = (A - X)/(OPT_peakblind - OPT_peakaware) with WP1's R0 and PT offline P100 (results/retention_inputs_wp1.csv).
  python src/evaluate_test.py [--trials trials.csv] [--insts ...]
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(HERE)
TEST = [f"Region5_s{s}" for s in ("0.1", "0.2", "0.3", "0.4", "0.5", "0.6")]
CFG = {"A": ("A", "baleen"), "B": ("B", "baleen"), "A+alpha": ("Aa-1.0", "baleen"), "B+alpha": ("Ba-1.0", "baleen"),
       "X1": ("Ea-1.0", "F1PT")}


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
    for x, refs in (("A+alpha", ("A", "B")), ("B+alpha", ("A", "B")), ("X1", ("A", "B", "A+alpha"))):
        for r in refs:
            if x in T and r in T:
                rows.append(versus(T, x, r, o.insts))
    res["comparisons"] = rows
    res["mean_p100"] = {k: float(v["mean"].mean()) for k, v in T.items()}
    res["n_matched"] = {k: int(v["count"].sum()) for k, v in T.items()}
    st = pd.read_csv(o.static) if os.path.exists(o.static) else None
    if st is not None:
        st = st[st["instance"].isin(o.insts)]
        rx = st[st.method == "RejectX"].set_index("instance")["p100"].reindex(o.insts).mean()
        cf = st[st.method == "CoinFlip"].set_index("instance")["p100"].reindex(o.insts).mean()
        # WP9 (PROTOCOL_v2_H4 §3): RejectX's WR steps over the target on Region5 (no probability matches +-1%); an arm
        # must be below RejectX's mean with the authors' bit-exact replays AND with the below-step replays.
        br = os.path.join(W, "results", "static_rejectx_bracket.csv")
        rx_low = rx
        if os.path.exists(br):
            v = pd.read_csv(br).set_index("instance")["rejectx_low_side_p100"].reindex(o.insts)
            assert v.notna().all() or v.isna().all(), "bracket file covers only some instances"
            rx_low = v.mean() if v.notna().all() else rx      # (bracket absent for these instances: WP3 check)
        res["baselines"] = dict(RejectX=float(rx), RejectX_low_side=float(rx_low), CoinFlip=float(cf))
        for x in ("A+alpha", "B+alpha", "X1"):
            if x in T:
                m_ = T[x]["mean"].mean()
                res[f"{x}_below_baselines"] = bool(m_ < rx and m_ < rx_low and m_ < cf)
    get = {(r["X"], r["ref"]): r["ok"] for r in rows}
    for x, key in (("A+alpha", "H4"), ("B+alpha", "Balpha_rule"), ("X1", "X1_rule_vs_A_B")):
        if all(k in get for k in [(x, "A"), (x, "B")]) and f"{x}_below_baselines" in res:
            res[key] = bool(get[(x, "A")] and get[(x, "B")] and res[f"{x}_below_baselines"])
    if ("X1", "A+alpha") in get:
        res["X1_rule_vs_Aalpha"] = bool(get[("X1", "A+alpha")])
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
    print({k: v for k, v in res.items() if k in ("baselines", "mean_p100", "n_matched", "H4", "Balpha_rule",
                                                  "X1_rule_vs_A_B", "X1_rule_vs_Aalpha", "retention")})


if __name__ == "__main__":
    main()
