"""AR: tables for a test report (all rows; descriptive parts are labelled non-confirmatory).
  python3 src/report_tables.py --test-dir ../t2u_region4 --labels-dir labels --logs-dir logs/test
"""
import argparse
import glob
import json
import os
import re

import pandas as pd

ARMS = ["A", "B", "Aa-1.0", "Ba-1.0", "XA-F1PT", "XA-F1CPSAT"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-dir", required=True)
    ap.add_argument("--labels-dir", default="labels")
    ap.add_argument("--logs-dir", default="logs/test")
    o = ap.parse_args()
    pd.set_option("display.width", 220)
    t = pd.read_csv(os.path.join(o.test_dir, "trials_test.csv"))
    fail = t.trial_key.astype(str).str.contains("__FAILED_")
    print(f"rows {len(t)}, __FAILED_ {int(fail.sum())}")
    if fail.any():
        print(t[fail][["trial_key", "error", "ts"]].to_string())
    t = t[~fail].copy()
    t["m"] = t.matched.astype(str) == "True"
    g = t.groupby(["arm", "inst"]).agg(n=("m", "size"), ok=("m", "sum"))
    print("\nmatched/total:\n", g.apply(lambda r: f"{int(r.ok)}/{int(r.n)}", axis=1).unstack(1).reindex(ARMS).to_string())
    m = t[t.m]
    P = m.pivot_table(index="inst", columns="arm", values="p100", aggfunc="mean").reindex(columns=ARMS)
    S = m.pivot_table(index="inst", columns="arm", values="p100", aggfunc="std").reindex(columns=ARMS)
    print("\nmean P100 over matched retrains:\n", P.round(3).to_string())
    print("\nsd:\n", S.round(3).to_string())
    u = t[~t.m]
    if len(u):
        print("\nunmatched rows:\n", u[["trial_key", "wr", "p100", "threshold", "n_sims"]].to_string())
    print("\nsecondary (matched means):\n", m.groupby("arm")[["p99", "top5", "mean_dt", "wr", "k0_adm", "peak_adm",
                                                            "peak_bigoff_share"]].mean().reindex(ARMS).round(3).to_string())
    rows = []
    for _, r in t.iterrows():
        f = os.path.join(o.test_dir, "results_test", "converge", f"{r.trial_key}.csv")
        rep = 0
        if os.path.exists(f):
            c = pd.read_csv(f)
            rep = len(c) - c.threshold.round(6).nunique()
        rows.append(dict(arm=r.arm, inst=r.inst, n_sims=r.n_sims, rep_theta=rep))
    d = pd.DataFrame(rows)
    print("\nconvergence (sims, repeated-theta rounds):\n",
          d.groupby(["arm", "inst"]).agg(sims=("n_sims", "sum"), rep=("rep_theta", "sum")).unstack(1).to_string())
    sb = os.path.join(o.test_dir, "results_test", "static_baselines.csv")
    if os.path.exists(sb):
        print("\nstatic:\n", pd.read_csv(sb)[["instance", "method", "p100", "wr", "matched", "ap_probability", "author_prob",
                                               "n_sims"]].to_string())
    insts = sorted(set(t.inst))
    lab = []
    for i in insts:
        for f in sorted(glob.glob(os.path.join(o.labels_dir, f"{i}_F1PT_s*.json"))):
            s = f.split("_s")[-1].split(".json")[0]
            c = f.replace("_F1PT_", "_F1CPSAT_")
            if os.path.exists(c):
                a, b = json.load(open(f)), json.load(open(c))
                lab.append(dict(inst=i, seed=s, pt=a["label_peak_util"], cp=b["label_peak_util"], j_pt=a["jaccard_vs_baleen"],
                                j_cp=b["jaccard_vs_baleen"]))
    if lab:
        L = pd.DataFrame(lab)
        print(f"\nF1 objective PT == CP-SAT on {int((L.pt.round(9) == L.cp.round(9)).sum())} of {len(L)} solves; "
              f"PT < CP-SAT on {int((L.pt < L.cp - 1e-9).sum())}; CP-SAT < PT on {int((L.cp < L.pt - 1e-9).sum())}")
        print(L.groupby("inst")[["j_pt", "j_cp"]].agg(["min", "max"]).round(3).to_string())
    bad, n = [], 0
    for f in glob.glob(os.path.join(o.logs_dir, "A_baleen_*", "train.log")):
        n += 1
        mm = re.search(r"--ap-feat-subset (\S+)", open(f).read(6000))
        if not mm or mm.group(1) != "meta+block+chunk":
            bad.append((f, mm.group(1) if mm else None))
    print(f"\nrace audit: {n} A_baleen train logs, {len(bad)} with another subset: {bad}")
    ev = os.path.join(o.test_dir, "results_test", "evaluation.json")
    if os.path.exists(ev):
        e = json.load(open(ev))
        print("\nevaluation.json:", json.dumps({k: e.get(k) for k in ("means", "best_alpha", "static", "good_result", "missing")}, indent=1))
        for c in e.get("comparisons", []) + [e.get("Y_vs_control")] if e.get("comparisons") else []:
            if c:
                print(f"{c['x']} vs {c['ref']}: wins {c['wins']}/{len(e['insts'])} (need {c['need']}), mean {c['mean']:+.3f}, "
                      f"SE {c['se']:.3f} (2.5SE {2.5 * c['se']:.3f}), worst {c['worst']:+.3f}, ok={c['ok']}")


if __name__ == "__main__":
    main()
