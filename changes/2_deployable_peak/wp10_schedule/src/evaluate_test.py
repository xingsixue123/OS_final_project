"""PROTOCOL_v2_H5 §5 evaluation (WP10, E4 region Region1 s0.1-0.6). Written BEFORE any test data exist; adapted from
wp9_region5/src/evaluate_test.py (functions table/versus unchanged) + its RejectX bracket (check_static.py).

P100 = PeakServiceTimeUtil1, mean over MATCHED retrains per instance, then over the 6 test instances.
Rule (X vs ref): wins >= 4/6 (mean P100 below the reference's) AND mean improvement (ref - X) > 2 SE,
  SE = sqrt(sum_i s_X,i^2/n_X,i + s_R,i^2/n_R,i) / N (retrain-level); the instance-level SE is reported too.
H5 = YES iff the finalist F meets the rule vs A, vs B AND vs the BEST alpha arm (the one of A+alpha, B+alpha with the
     lower mean test P100), and F's mean P100 is below RejectX's (authors'-probability/closest replays AND, where a
     replay is unmatched, the below-WR-step replays) and below CoinFlip's.
Reported, no pass/fail: F vs the other alpha arm; the classical control Fc with the same rule; F vs Fc (Ising vs
classical); A+alpha / B+alpha vs A, B (H4 re-check on a new region); secondary metrics.
  python src/evaluate_test.py --finalist TB-pt [--trials trials_test.csv]
"""
import argparse
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(HERE)
sys.path.insert(0, HERE)
TEST = [f"Region1_s{s}" for s in ("0.1", "0.2", "0.3", "0.4", "0.5", "0.6")]
TARGET_WR, TOL = 35.599, 0.01


def cfgs(fin):
    ctl = fin.replace("-pt", "-cd")
    return {"A": "A", "B": "B", "A+alpha": "Aa-1.0", "B+alpha": "Ba-1.0", "F": fin, "Fc": ctl}


def table(t, insts, CFG):
    t = t[(t["matched"].astype(str) == "True") & ~t["trial_key"].astype(str).str.contains("__FAILED_")]
    out = {}
    for name, arm in CFG.items():
        d = t[(t["arm"] == arm) & (t["inst"].isin(insts))]
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


def static_values(insts):
    """RejectX / CoinFlip from prep.py static (frozen code): baseline = authors' p if matched else closest-WR replay;
    for unmatched instances also the closest replay with WR <= target*(1+TOL) (low side), as WP9."""
    import wpcommon as C
    st = pd.read_csv(os.path.join(W, "results_test", "static_baselines.csv"))
    st = st[st.instance.isin(insts)]
    out = {}
    for m, jk in (("RejectX", "rejectx_static"), ("CoinFlip", "coinflip_static")):
        s = st[st.method == m].set_index("instance").reindex(insts)
        low = []
        for i, b in s.iterrows():
            if str(b["matched"]) == "True":
                low.append(b["p100"])
                continue
            pts = []
            for d in sorted(glob.glob(os.path.join(W, "work_frozen", "runs", "prep", f"prep_{jk}_{i}", "sim", "p_*"))):
                rf = sorted(glob.glob(os.path.join(d, "**", "*_cache_perf.txt.lzma"), recursive=True))
                if rf:
                    r = C.load_result(rf[0])["results"]
                    pts.append(dict(wr=r["FlashWriteRate"], p100=r["PeakServiceTimeUtil1"]))
            lo = [x for x in pts if x["wr"] <= TARGET_WR * (1 + TOL)]
            low.append(max(lo, key=lambda x: x["wr"])["p100"] if lo else b["p100"])
        out[m] = dict(mean=float(s["p100"].mean()), low_side_mean=float(np.mean(low)), n_matched=int((s["matched"].astype(str) == "True").sum()),
                      per_inst=s["p100"].round(4).tolist(), low_side=[round(float(v), 4) for v in low])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finalist", required=True, choices=["TA-pt", "TB-pt"])
    ap.add_argument("--trials", default=os.path.join(W, "trials_test.csv"))
    ap.add_argument("--insts", nargs="+", default=TEST)
    ap.add_argument("--out", default=os.path.join(W, "results_test", "evaluation.json"))
    ap.add_argument("--no-static", action="store_true")
    o = ap.parse_args()
    CFG = cfgs(o.finalist)
    T, t = table(pd.read_csv(o.trials), o.insts, CFG)
    res = {"instances": o.insts, "finalist": o.finalist, "control": CFG["Fc"], "n_rows": int(len(t))}
    res["mean_p100"] = {k: float(v["mean"].mean()) for k, v in T.items()}
    res["n_matched"] = {k: int(v["count"].sum()) for k, v in T.items()}
    best_alpha = min(("A+alpha", "B+alpha"), key=lambda k: res["mean_p100"].get(k, np.inf))
    res["best_alpha_arm"] = best_alpha
    rows = []
    for x, refs in (("F", ("A", "B", "A+alpha", "B+alpha", "Fc")), ("Fc", ("A", "B", "A+alpha", "B+alpha")),
                    ("A+alpha", ("A", "B")), ("B+alpha", ("A", "B"))):
        for r in refs:
            if x in T and r in T:
                rows.append(versus(T, x, r, o.insts))
    res["comparisons"] = rows
    get = {(r["X"], r["ref"]): r["ok"] for r in rows}
    if not o.no_static:
        sv = static_values(o.insts)
        res["baselines"] = sv
        for x in ("F", "Fc", "A+alpha", "B+alpha"):
            if x in T:
                m_ = T[x]["mean"].mean()
                res[f"{x}_below_baselines"] = bool(m_ < sv["RejectX"]["mean"] and m_ < sv["RejectX"]["low_side_mean"]
                                                   and m_ < sv["CoinFlip"]["mean"] and m_ < sv["CoinFlip"]["low_side_mean"])
    need = [("F", "A"), ("F", "B"), ("F", best_alpha)]
    if all(k in get for k in need) and "F_below_baselines" in res:
        res["H5"] = bool(all(get[k] for k in need) and res["F_below_baselines"])
    need_c = [("Fc", "A"), ("Fc", "B"), ("Fc", best_alpha)]
    if all(k in get for k in need_c) and "Fc_below_baselines" in res:
        res["Fc_rule"] = bool(all(get[k] for k in need_c) and res["Fc_below_baselines"])
    sec = t[t["inst"].isin(o.insts)].copy()
    cols = [c for c in ["p100", "p99", "top5", "mean_dt", "wr", "threshold", "k0_adm", "peak_adm", "peak_bigoff_share"] if c in sec]
    res["secondary"] = sec.groupby("arm")[cols].mean().round(4).to_dict(orient="index")
    res["per_instance"] = {k: v["mean"].round(4).tolist() for k, v in T.items()}
    json.dump(res, open(o.out, "w"), indent=1, default=float)
    print(pd.DataFrame(rows).round(3).to_string(index=False))
    print({k: v for k, v in res.items() if k in ("mean_p100", "n_matched", "best_alpha_arm", "H5", "Fc_rule", "F_below_baselines")})


if __name__ == "__main__":
    main()
