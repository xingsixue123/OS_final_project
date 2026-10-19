"""E3 evaluation: the FINALIST RULE of PROGRESS.md (FINALIST RULE), applied unchanged.
References = WP2 dev trials (reused, matched rows): A+alpha = Aa-1.0 U Ax-1.0, B+alpha = Ba-1.0 U Bx-1.0; also A, B.
  src/sbx.sh src/e3_eval.py  -> results/e3_screen.csv, results/e3_finalist.json, results/e3_tables.md
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402

REF = {"A": ["A"], "B": ["B"], "A+a": ["Aa-1.0", "Ax-1.0"], "B+a": ["Ba-1.0", "Bx-1.0"]}
CANDS = ["TA-pt", "TB-pt"]
CTRLS = ["TA-cd", "TB-cd"]


def load():
    t2 = pd.read_csv(os.path.join(C.WP2, "trials.csv"))
    t2 = t2[~t2.trial_key.astype(str).str.contains("FAILED") & (t2.matched.astype(str) == "True")]
    ref = {n: t2[t2.arm.isin(a) & (t2.design == "baleen")][["inst", "rep", "p100", "wr", "threshold"]] for n, a in REF.items()}
    t = pd.read_csv(os.path.join(C.W, "trials_dev.csv"))
    t = t[~t.trial_key.astype(str).str.contains("FAILED")]
    unmatched = t[t.matched.astype(str) != "True"]
    t = t[t.matched.astype(str) == "True"]
    return ref, t, unmatched


def per_inst(df, reps=None):
    d = df if reps is None else df[df.rep.isin(reps)]
    g = d.groupby("inst").p100
    return g.mean().reindex(C.DEV), g.count().reindex(C.DEV), g.var(ddof=1).reindex(C.DEV)


def score(X, Aa, Ba):
    dA, dB = Aa - X, Ba - X
    S = float(np.minimum(dA, dB).mean())
    reg = {r: float((X - Ba)[[i for i in C.DEV if i.startswith(r)]].mean()) for r in ("Region6", "Region7")}
    return dict(S=S, dA_mean=float(dA.mean()), dB_mean=float(dB.mean()), winsA=int((dA > 0).sum()),
                winsB=int((dB > 0).sum()), region_minus_Ba=reg, mean=float(X.mean()))


def main():
    ref, t, unmatched = load()
    out = {"unmatched": unmatched.trial_key.tolist()}
    # ---- screen: rep 1 vs rep 1 (paired by retrain)
    r1 = {n: per_inst(d, [1])[0] for n, d in ref.items()}
    rows = []
    for arm in CANDS + CTRLS:
        x = t[(t.arm == arm) & (t.rep == 1)]
        X, n, _ = per_inst(x)
        if n.isna().any() or (n < 1).any():
            rows.append(dict(config=arm, complete=False))
            continue
        s = score(X, r1["A+a"], r1["B+a"])
        rows.append(dict(config=arm, complete=True, mean=s["mean"], S1=s["S"], vs_Aa=s["dA_mean"], vs_Ba=s["dB_mean"],
                         winsA=s["winsA"], winsB=s["winsB"], R6_minus_Ba=s["region_minus_Ba"]["Region6"],
                         R7_minus_Ba=s["region_minus_Ba"]["Region7"], **{i: X[i] for i in C.DEV}))
    scr = pd.DataFrame(rows)
    scr.to_csv(os.path.join(C.W, "results", "e3_screen.csv"), index=False)
    passing = scr[(scr.config.isin(CANDS)) & scr.complete & (scr.S1 > 0)].sort_values("S1", ascending=False)
    out["screen"] = scr.drop(columns=[c for c in C.DEV if c in scr.columns]).to_dict("records")
    out["screen_pass"] = passing.config.tolist()[:2]
    # ---- finalist: 3 matched retrains
    m3 = {n: per_inst(d) for n, d in ref.items()}
    fin = []
    for arm in out["screen_pass"]:
        x = t[t.arm == arm]
        X, n, v = per_inst(x)
        if n.isna().any() or (n < 3).any():
            fin.append(dict(config=arm, eligible=False, n=n.fillna(0).astype(int).tolist()))
            continue
        s = score(X, m3["A+a"][0], m3["B+a"][0])
        q = (s["S"] > 0 and s["winsA"] >= 5 and s["winsB"] >= 5
             and all(v_ <= 0.5 for v_ in s["region_minus_Ba"].values()))
        # SEs (reported, not in the rule): retrain-level and instance-level vs each reference
        se = {}
        for rn in ("A+a", "B+a", "A", "B"):
            Rm, Rn, Rv = m3[rn]
            d = Rm - X
            se[rn] = dict(mean=float(d.mean()), wins=int((d > 0).sum()),
                          se_retrain=float(np.sqrt((v / n + Rv / Rn).sum()) / len(C.DEV)),
                          se_instance=float(d.std(ddof=1) / np.sqrt(len(C.DEV))))
        fin.append(dict(config=arm, eligible=True, qualifies=bool(q), **s, vs=se, per_inst=X.to_dict()))
    out["finalist_eval"] = fin
    q = [f for f in fin if f.get("qualifies")]
    # deterministic tie-break (PROTOCOL_v2_H5 §1): larger S3, then more total wins (A+a and B+a), then name order
    q = sorted(q, key=lambda f: (-round(f["S"], 9), -(f["winsA"] + f["winsB"]), f["config"]))
    out["FINALIST"] = q[0]["config"] if q else None
    out["CONTROL"] = q[0]["config"].replace("-pt", "-cd") if q else None
    out["complete_confirmation"] = bool(fin) and all(f.get("eligible") for f in fin)
    json.dump(out, open(os.path.join(C.W, "results", "e3_finalist.json"), "w"), indent=1, default=float)
    json.dump({k: out.get(k) for k in ("FINALIST", "CONTROL", "screen_pass", "complete_confirmation", "unmatched")},
              open(os.path.join(C.W, "results", "finalist.json"), "w"), indent=1, default=float)
    # ---- tables for RESULTS_dev.md
    lines = ["| config | n | " + " | ".join(i.replace("Region", "R") for i in C.DEV) + " | mean |", "|---" * (len(C.DEV) + 3) + "|"]
    for nme, d in [("A", ref["A"]), ("B", ref["B"]), ("A+α", ref["A+a"]), ("B+α", ref["B+a"])] + \
                   [(a, t[t.arm == a]) for a in CANDS + CTRLS]:
        for reps, tag in (([1], "r1"), (None, "all")):
            X, n, _ = per_inst(d, reps)
            if n.isna().all():
                continue
            lines.append(f"| {nme} ({tag}) | {int(n.min()) if not n.isna().any() else 'part'}–{int(n.max())} | "
                         + " | ".join("—" if np.isnan(v) else f"{v:.2f}" for v in X) + f" | {X.mean():.2f} |")
    open(os.path.join(C.W, "results", "e3_tables.md"), "w").write("\n".join(lines) + "\n")
    print(json.dumps({k: out[k] for k in ("screen_pass", "FINALIST")}, indent=1))
    print(scr.drop(columns=[c for c in C.DEV if c in scr.columns]).to_string())
    print("\n".join(lines))


if __name__ == "__main__":
    main()
