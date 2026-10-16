"""Proxy validation against WP2's full-simulation dev P100s, exactly the pre-registered criterion (PROGRESS.md).
Reads results/proxy_ledger.csv (PL + PM rows) and wp2_deployed/trials.csv (read-only). Writes
results/proxy_validation.md and results/proxy_validation_cells.csv.
  src/run.sh baleen ../src/validate.py
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "q3lib")]
import wpcommon as C  # noqa: E402
import proxy as PX  # noqa: E402
from pl_eval import WP2_CFGS, WP2_MAP, WP2_SCREENS  # noqa: E402

CFG13 = list(WP2_CFGS)


def sim_means():
    t = pd.read_csv(os.path.join(PX.WP2, "trials.csv"))
    t = t[~t.trial_key.str.contains("FAILED") & (t.matched == True)]  # noqa: E712
    t["config"] = [WP2_MAP.get((a, d)) for a, d in zip(t.arm, t.design)]
    t = t[t.config.notna()]
    g = t.groupby(["inst", "config"])
    return g.p100.mean().rename("sim"), g.p100.std().rename("sim_sd"), g.size().rename("sim_n"), g.k0_adm.mean().rename("sim_k0")


def criterion(cells, col, label, lines):
    """cells: DataFrame inst x config with columns sim, <col>."""
    out = {}
    rhos = {}
    for inst, d in cells[cells.config.isin(CFG13)].groupby("inst"):
        d = d.dropna(subset=[col, "sim"])
        rhos[inst] = spearmanr(d[col], d["sim"]).correlation if len(d) >= 4 else np.nan
    r = pd.Series(rhos)
    c1 = bool(np.nanmedian(r) >= 0.5 and (r > 0).sum() >= 6)
    piv = cells.pivot(index="inst", columns="config", values=col)
    sp = cells.pivot(index="inst", columns="config", values="sim")
    con = {}
    for name, (a, b) in {"X1-A": ("X1", "A"), "X1-(A+a)": ("X1", "A+a"), "D:F1PT-A": ("D:F1PT", "A")}.items():
        con[name] = (float((piv[a] - piv[b]).mean()), float((sp[a] - sp[b]).mean()))
    c2 = all(np.sign(p) == np.sign(s) for p, s in con.values())
    dx = (piv["X1"] - piv["A+a"])
    ds = (sp["X1"] - sp["A+a"])
    big = ds.abs() >= 0.5
    agree = int((np.sign(dx[big]) == np.sign(ds[big])).sum())
    c3 = agree >= 5
    dm = cells[cells.config.isin(CFG13)].dropna(subset=[col, "sim"]).copy()
    dm["p_dm"] = dm[col] - dm.groupby("inst")[col].transform("mean")
    dm["s_dm"] = dm["sim"] - dm.groupby("inst")["sim"].transform("mean")
    pr = pearsonr(dm.p_dm, dm.s_dm)[0]
    sr = spearmanr(dm.p_dm, dm.s_dm).correlation
    lines.append(f"\n### {label} (`{col}`)\n")
    lines.append("| instance | " + " | ".join(r.index) + " | median |")
    lines.append("|---" * (len(r) + 2) + "|")
    lines.append("| Spearman rho_i | " + " | ".join(f"{v:+.2f}" for v in r.values) + f" | {np.nanmedian(r):+.2f} |")
    lines.append(f"\n- **C1** median rho = {np.nanmedian(r):+.2f}, rho > 0 on {(r > 0).sum()}/8 -> {'PASS' if c1 else 'FAIL'}")
    lines.append("- **C2** dev-mean contrasts (proxy vs sim): " + "; ".join(
        f"{k}: {p:+.2f} vs {s:+.2f}" for k, (p, s) in con.items()) + f" -> {'PASS' if c2 else 'FAIL'}")
    lines.append(f"- **C3** X1-(A+a) sign agreement on instances with |sim| >= 0.5: {agree}/{int(big.sum())} "
                 f"(proxy {', '.join(f'{v:+.2f}' for v in dx[big].values)}; sim {', '.join(f'{v:+.2f}' for v in ds[big].values)})"
                 f" -> {'PASS' if c3 else 'FAIL'}")
    lines.append(f"- pooled within-instance correlation over {len(dm)} cells: Pearson {pr:+.2f}, Spearman {sr:+.2f}")
    verdict = c1 and c2 and c3
    lines.append(f"- **verdict: {'PROXY VALID' if verdict else 'PROXY NOT VALID'}**")
    out.update(c1=c1, c2=c2, c3=c3, median_rho=float(np.nanmedian(r)), pos=int((r > 0).sum()), pooled_pearson=pr,
               pooled_spearman=sr, verdict=verdict)
    return out


def main():
    L = pd.read_csv(os.path.join(C.RESULTS, "proxy_ledger.csv"))
    s, ssd, sn, sk0 = sim_means()
    cfgs = CFG13 + list(WP2_SCREENS)
    pl = L[(L.kind == "pl") & L.config.isin(cfgs)].groupby(["inst", "config"]).agg(
        pl=("p100", "mean"), pl_sd=("p100", "std"), pl_n=("p100", "size"), pl_k0=("k0_adm", "mean"),
        pl_bound=("bound", "sum"))
    pm = L[L.kind == "pm"].groupby(["inst", "config"]).agg(pm=("p100", "mean"), pm_simtheta=("emu_p100_at_sim_theta", "mean"),
                                                            pm_k0=("k0_adm", "mean"), pm_bound=("bound", "sum"))
    cells = pd.concat([s, ssd, sn, sk0, pl, pm], axis=1).reset_index()
    cells = cells[cells.config.isin(cfgs)]
    cells.to_csv(os.path.join(C.RESULTS, "proxy_validation_cells.csv"), index=False)
    lines = ["# Proxy validation (pre-registered criterion, PROGRESS.md 2026-10-05 14:25)", "",
             f"Cells: {len(cells)} (instance x configuration); 13 criterion configurations; sim = WP2 mean matched P100.",
             f"Calibration: `results/wr_calibration.json` (selected variant: see calib output)."]
    res = {}
    for col, label in (("pl", "PL: label-level proxy (refit GBM) -- PRIMARY"),
                       ("pm", "PM: WP2's actual models, calibrated theta -- diagnostic"),
                       ("pm_simtheta", "PM at the simulation's converged theta (oracle threshold) -- diagnostic")):
        if col in cells and cells[col].notna().any():
            res[col] = criterion(cells, col, label, lines)
    # mean table
    lines.append("\n### Dev means over 8 instances (util %)\n")
    lines.append("| config | sim | PL | PM | PM@sim-theta | sim k0 | PL k0 |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in cfgs:
        d = cells[cells.config == c]
        if len(d) == 0:
            continue
        f = lambda col: f"{d[col].mean():.2f}" if col in d and d[col].notna().all() else "–"  # noqa: E731
        k = lambda col: f"{d[col].mean():.3f}" if col in d and d[col].notna().all() else "–"  # noqa: E731
        lines.append(f"| {c} | {f('sim')} | {f('pl')} | {f('pm')} | {f('pm_simtheta')} | {k('sim_k0')} | {k('pl_k0')} |")
    if "pl_k0" in cells:
        d = cells.dropna(subset=["pl_k0", "sim_k0"])
        lines.append(f"\nk0 (first-access admission): PL vs WP2 sim-model k0 Pearson over {len(d)} cells: "
                     f"{pearsonr(d.pl_k0, d.sim_k0)[0]:+.2f}")
    open(os.path.join(C.RESULTS, "proxy_validation.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
