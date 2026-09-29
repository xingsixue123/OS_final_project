"""Markdown tables for RESULTS.md from q3/trials.csv (every row; unmatched rows counted and excluded from means)."""
import json
import os
import sys

import numpy as np
import pandas as pd

X = os.environ.get("X_ROOT", os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
REF = {"Region7_s0": (40.097, 0.176, 9), "Region6_s0": (43.248, 0.041, 9)}
DESC = {
    "R0": "control: Baleen's own labels through the solver path (identity)",
    "T5": "PT, LSE peak (gamma 2) + DT blend beta=1 + trust region mu=5",
    "T2": "PT, LSE peak + beta=0.5 + trust mu=2",
    "P0": "PT, pure LSE peak (no DT blend, no trust region)",
    "PW4": "PT, peak-weighted DT knapsack (phi=(C/mean C)^4), no peak term",
    "TK10": "PT, top-10-window mean peak + beta=1 + trust mu=5",
    "L5": "PT, LSE peak + beta=0.5 + mu=2 + kNN feature-consistency couplings lam=5",
    "C2": "PT on feature CELLS (op/ns/user, log size, history bins, #rows bin) + beta=0.5 + mu=2",
    "SAT12": "PT T5 + forced coverage of episodes with block count>=12 at offsets>8MB",
    "SATB10": "coverage (b0>=10, >8MB) forced + DT/trust only (no peak term)",
    "T5c": "T5 with zero-value additions removed (Baleen-order fill)",
    "JUNK10": "CONTROL (not Ising): Baleen labels, lowest 10% of budget swapped for random zero-value episodes",
}


def main(stage=None):
    df = pd.read_csv(os.path.join(X, "q3", "trials.csv"))
    if stage:
        df = df[df.stage == stage]
    df["matched"] = df["matched"].astype(bool)
    lines = ["| config | description | instance | retrains (matched/all) | P100 mean +- sd (matched) | per retrain | "
             "vs Baleen ref | mean DT | J vs Baleen labels | day-1 label peak |", "|" + "---|" * 10]
    order = list(dict.fromkeys(df.config))
    for cfg in order:
        for inst in ["Region7_s0", "Region6_s0"] if stage in (None, "screen", "control") else sorted(df.instance.unique()):
            d = df[(df.config == cfg) & (df.instance == inst)]
            if d.empty:
                continue
            m = d[d.matched]
            per = ", ".join(f"{v:.2f}" + ("" if ok else "*") for v, ok in zip(d.p100, d.matched) if v == v)
            mu = m.p100.mean() if len(m) else np.nan
            sd = m.p100.std(ddof=1) if len(m) > 1 else np.nan
            ref = REF.get(inst)
            vs = f"{mu - ref[0]:+.2f}" if ref and mu == mu else ""
            lines.append(f"| {cfg} | {DESC.get(cfg, '')} | {inst} | {len(m)}/{len(d)} | "
                         f"{'' if mu != mu else f'{mu:.2f}'}{'' if sd != sd else f' +- {sd:.2f}'} | {per} | {vs} | "
                         f"{'' if not len(m) else f'{m.mean_dt.mean():.2f}'} | "
                         f"{'' if d.jaccard_vs_baleen.isna().all() else f'{d.jaccard_vs_baleen.mean():.2f}'} | "
                         f"{'' if d.label_peak_day1.isna().all() else f'{d.label_peak_day1.mean():.2f}'} |")
    print("\n".join(lines))
    print("\n(* = not within +-1% WR; excluded from the mean)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
