"""Gate 0: fidelity of the analytic per-window load L_w = C_w - sum_e d(e,w) x_e vs the simulated DT.

For an offline run (region, name) from results/offline.csv:
  x_e = 1 iff the episode's threshold in the decisions file <= the converged --ap-threshold (exactly the
        set OfflineAP admits), mapped to the dumped instance by episode identity (block key, first ts).
  C_w validated against the simulator's service_time_nocache_stats (per 600 s window).
Reports Pearson r / R^2 / Spearman over windows after day 1, peak (util %) and argmax windows, top-10 overlap.
Run in the Baleen env (compress_pickle / compress_json).
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
import scipy.sparse as sp
import compress_pickle

import hecommon as HC

US = 1.0 / 36 * (100.0 / 0.1) / 600 * 100   # == sim scale PeakServiceTimeUtil1 / max(used)


def load_inst(p):
    z = np.load(p)
    D = sp.csr_matrix((z["D_data"], z["D_indices"], z["D_indptr"]), shape=tuple(z["D_shape"]))
    ids = list(zip([str(k) for k in z["keys"]], [float(t) for t in z["ts0"]]))
    return D, z["C"], z["active"], ids, z


def thresholds(dec_path):
    d = compress_pickle.load(dec_path)
    out = {}
    for k, eps in d.items():
        for (key, tsl, tsp, off), kw in eps:
            out[(str(key), float(tsp[0]))] = kw["threshold"]
    return out


def spearman(a, b):
    ra = pd.Series(a).rank().values
    rb = pd.Series(b).rank().values
    return float(np.corrcoef(ra, rb)[0, 1])


def gate(region, name, store="offline"):
    df = pd.DataFrame([json.loads(l) for l in open(os.path.join(HC.RESULTS, f"{store}.jsonl")) if l.strip()])
    row = df[(df.region == region) & (df.name == name)].iloc[-1].to_dict()
    row = pd.Series(row)
    exp = row.exp
    inst = os.path.join(HC.WORK, "inst", f"{exp}.npz")
    D, C, active, ids, z = load_inst(inst)
    log = os.path.join(HC.LOGS, row.get("prefix", "off") if isinstance(row.get("prefix", "off"), str) else "off", exp, "train.log")
    out = HC.parse_train_outputs(log)
    th = thresholds(os.path.join(HC.WORK, out["thresholds"][0]))
    tvec = np.array([th[i] for i in ids])
    cut = float(row.threshold)
    x = (tvec <= cut).astype(float)
    xW = (tvec < HC.TARGET_WR).astype(float)
    rf = os.path.join(HC.WORK, row.result_file)
    ws = HC.window_series(rf)
    m = min(len(C), len(ws["used"]))
    act = np.arange(m) >= HC.SKIP_WINDOWS
    L = (C - D.T @ x)[:m]
    LW = (C - D.T @ xW)[:m]
    sim = ws["used"][:m]
    noc = ws["nocache"][:m]
    a, b = L[act], sim[act]
    r = float(np.corrcoef(a, b)[0, 1])
    top10a = set(np.argsort(-a)[:10])
    top10b = set(np.argsort(-b)[:10])
    res = dict(region=region, name=name, cutoff=cut, n_admit=int(x.sum()), n_sel_W=int(xW.sum()),
               n_windows=int(act.sum()), len_inst=len(C), len_sim=len(ws["used"]),
               C_vs_nocache_maxabs=float(np.abs(C[:m] - noc).max()), C_vs_nocache_r=float(np.corrcoef(C[:m], noc)[0, 1]),
               pearson_r=r, r2=r * r, spearman=spearman(a, b),
               resid_mean_util=float((b - a).mean() * US), resid_sd_util=float((b - a).std() * US),
               analytic_peak_util=float(a.max() * US), sim_peak_util=float(b.max() * US),
               analytic_argmax=int(np.argmax(a)) + HC.SKIP_WINDOWS, sim_argmax=int(np.argmax(b)) + HC.SKIP_WINDOWS,
               sim_rank_of_analytic_argmax=int((b > b[np.argmax(a)]).sum()) + 1,
               analytic_rank_of_sim_argmax=int((a > a[np.argmax(b)]).sum()) + 1,
               top10_overlap=len(top10a & top10b),
               analytic_peak_util_atW=float(LW[act].max() * US),
               analytic_mean_util=float(a.mean() * US), sim_mean_util=float(b.mean() * US),
               nocache_peak_util=float(noc[act].max() * US))
    return res, dict(L=L, sim=sim, noc=noc, C=C[:m])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", nargs="+", required=True, help="Region:name")
    ap.add_argument("--out", default="gate0.csv")
    o = ap.parse_args()
    rows = []
    for p in o.pairs:
        region, name = p.split(":")
        res, ser = gate(region, name)
        rows.append(res)
        np.savez(os.path.join(HC.RESULTS, f"gate0_series_{region}_{name}.npz"), **ser)
        print(json.dumps(res))
    pd.DataFrame(rows).to_csv(os.path.join(HC.RESULTS, o.out), index=False)


if __name__ == "__main__":
    main()
