"""Validate the cheap deployed proxy against real simulations (dev only).

Data: harness_eval's deployed runs (37 trained admission GBMs; for each, the simulated WR and P100 at every
--ap-threshold tried: harness_eval/results/converge/dep_*.csv) -- read-only.
For each model: score every GET access of the dev trace with simulator-style features (q3lib.sim_features), emulate
online admission analytically (q3lib.emulate_at), and compare
  (a) emulated WR vs simulated WR at the same thresholds,
  (b) proxy P100 at the emulated-WR-matched threshold vs the simulated P100 at the converged threshold.
Run in the Baleen env (lightgbm 3.3.5, the version the models were trained with).
"""
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3lib as QL  # noqa: E402

X = os.environ["X_ROOT"]
H = os.path.normpath(os.path.join(X, "..", "harness_eval"))
CACHE = os.path.join(X, "q3", "work", "cache")
os.makedirs(CACHE, exist_ok=True)


def model_path(exp):
    log = os.path.join(H, "work", "logs", "dep", exp, "train.log")
    for line in open(log).read().splitlines():
        if line.startswith("model_admit_threshold_binary ") and line.split(" ")[-1] != "NoExists" \
                and line.endswith("M"):
            return os.path.join(H, "work", line.split(" ")[1])
    raise KeyError(exp)


def main():
    import lightgbm as lgb
    dep = pd.read_csv(os.path.join(H, "results", "deployed.csv"))
    rows = []
    for region in ["Region7", "Region6"]:
        I = QL.Inst(os.path.join(X, "common", "inst", f"fullml_{region}_s0.npz"))
        F = QL.sim_features(I, cache=os.path.join(CACHE, f"simfeat_fullml_{region}_s0.npz")).astype(float)
        d = dep[dep.region == region]
        for _, r in d.iterrows():
            bst = lgb.Booster(model_file=model_path(r.exp))
            score = bst.predict(F)
            conv = pd.read_csv(os.path.join(H, "results", "converge", f"{r.exp}.csv"))
            for _, c in conv.iterrows():
                if np.isnan(c.wr):
                    continue
                L, wr, kst = QL.emulate_at(I, score, c.threshold)
                rows.append(dict(kind="curve", region=region, name=r["name"], rep=r.rep, threshold=c.threshold,
                                 sim_wr=c.wr, sim_p100=c.peak, emu_wr=wr, emu_p100=QL.peak_util(L),
                                 emu_top5=QL.topk_util(L)))
            th, L, wr, kst = QL.match_wr(I, score)
            rows.append(dict(kind="matched", region=region, name=r["name"], rep=r.rep, threshold=th,
                             sim_threshold=r.threshold, sim_wr=r.wr, sim_p100=r.p100, emu_wr=wr,
                             emu_p100=QL.peak_util(L), emu_top5=QL.topk_util(L), sim_top5=r.top5,
                             n_adm=int((kst >= 0).sum()), emu_argmax=int(np.argmax(L[QL.SKIP:]) + QL.SKIP),
                             sim_argmax=int(r["argmax"])))
            print(json.dumps(rows[-1]), flush=True)
    df = pd.DataFrame(rows)
    out = os.path.join(X, "q3", "results", "proxy_validate.csv")
    df.to_csv(out, index=False)
    m = df[df.kind == "matched"]
    for region in ["Region7", "Region6"]:
        a = m[m.region == region]
        print(region, "matched: corr(emu_p100, sim_p100)=%.3f  spearman=%.3f  n=%d" % (
            np.corrcoef(a.emu_p100, a.sim_p100)[0, 1], a[["emu_p100", "sim_p100"]].rank().corr().iloc[0, 1], len(a)))
        c = df[(df.kind == "curve") & (df.region == region)]
        print(region, "curve: corr(emu_wr, sim_wr)=%.3f  corr(emu_p100, sim_p100)=%.3f" % (
            np.corrcoef(c.emu_wr, c.sim_wr)[0, 1], np.corrcoef(c.emu_p100, c.sim_p100)[0, 1]))


if __name__ == "__main__":
    main()
