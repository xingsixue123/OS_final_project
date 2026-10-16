"""Write-rate calibration for the proxy (pre-registered in PROGRESS.md): uses ONLY WP2's (theta, simulated WR) pairs
(results/pm_points.csv, real models' emulated measures at each simulated theta), never a simulated P100.
Per instance: log(sim WR) ~ a + b log(emu wr_ep) | a + b log(emu wr_acc) | a + b log(ep) + c log(acc) ("mix").
Selection: smallest leave-one-configuration-out RMSE of log sim WR on the matched sims, pooled over the 8 instances.
Output: results/wr_calibration.json ({inst: {variant, coef}} for the selected variant, fitted on all sims of the
instance) + results/wr_calibration_loco.csv.
  src/run.sh baleen ../src/calib.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE]
import wpcommon as C  # noqa: E402


def cfg_name(arm, design):
    a = arm
    for x, y in (("Ax", "Aa"), ("Bx", "Ba"), ("Ex", "Ea")):
        if a.startswith(x):
            a = y + a[2:]
    return f"{a}:{design}"


def design_matrix(d, v):
    if v == "ep":
        return np.c_[np.ones(len(d)), np.log(d.emu_wr_ep)]
    if v == "acc":
        return np.c_[np.ones(len(d)), np.log(d.emu_wr_acc)]
    return np.c_[np.ones(len(d)), np.log(d.emu_wr_ep), np.log(d.emu_wr_acc)]


def main():
    p = pd.read_csv(os.path.join(C.RESULTS, "pm_points.csv"))
    p = p[(p.sim_wr > 0) & (p.emu_wr_ep > 0) & (p.emu_wr_acc > 0)].copy()
    p["cfg"] = [cfg_name(a, d) for a, d in zip(p.arm, p.design)]
    p["matched_sim"] = (p.sim_wr - C.TARGET_WR).abs() / C.TARGET_WR <= C.TOL
    rows = []
    for v in ("ep", "acc", "mix"):
        for inst, d in p.groupby("inst"):
            for cfg in sorted(d.cfg.unique()):
                tr = d[d.cfg != cfg]
                te = d[(d.cfg == cfg) & d.matched_sim]
                if len(te) == 0:
                    continue
                coef, *_ = np.linalg.lstsq(design_matrix(tr, v), np.log(tr.sim_wr), rcond=None)
                err = np.log(te.sim_wr) - design_matrix(te, v) @ coef
                for e in err:
                    rows.append(dict(variant=v, inst=inst, cfg=cfg, err=float(e)))
    L = pd.DataFrame(rows)
    L.to_csv(os.path.join(C.RESULTS, "wr_calibration_loco.csv"), index=False)
    summ = L.groupby("variant").err.agg(rmse=lambda e: float(np.sqrt(np.mean(e ** 2))), bias="mean", n="size")
    per_inst = L.groupby(["variant", "inst"]).err.agg(lambda e: float(np.sqrt(np.mean(e ** 2)))).unstack(0)
    print(summ.to_string())
    print(per_inst.round(4).to_string())
    best = summ.rmse.idxmin()
    out = {"_selected": best, "_loco_rmse": summ.rmse.to_dict()}
    for inst, d in p.groupby("inst"):
        coef, *_ = np.linalg.lstsq(design_matrix(d, best), np.log(d.sim_wr), rcond=None)
        resid = np.log(d.sim_wr) - design_matrix(d, best) @ coef
        out[inst] = dict(variant=best, coef=[float(c) for c in coef], n=int(len(d)),
                         rmse_in=float(np.sqrt(np.mean(resid ** 2))))
    json.dump(out, open(os.path.join(C.RESULTS, "wr_calibration.json"), "w"), indent=1)
    print("selected", best, json.dumps({k: v for k, v in out.items() if not k.startswith("_")}, indent=None)[:600])


if __name__ == "__main__":
    main()
