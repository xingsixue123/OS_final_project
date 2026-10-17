"""Stage-2 summary: screen gate and finalist rule exactly as PLAN_C.md §3, plus mechanism by region.
Track C rows: wp8_trackC/trials.csv; references (NOT re-run): wp2_deployed/trials.csv (read-only).
  source env.sh && $BALEEN_PY -B src/stage2.py      -> results/stage2_summary.md
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(HERE)
WP2 = os.path.join(os.path.dirname(W), "wp2_deployed")
DEV = [f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]
CANDS = ["E8:ANC3", "E8:ANC10", "E8:STU10R1"]
REFMAP = {("Ea-1.0", "F1PT"): "X1", ("Aa-1.0", "baleen"): "A+a", ("Ax-1.0", "baleen"): "A+a", ("A", "baleen"): "A",
          ("B", "baleen"): "B", ("Ba-1.0", "baleen"): "B+a", ("Bx-1.0", "baleen"): "B+a", ("D", "F1PT"): "D:F1PT"}


def load():
    t2 = pd.read_csv(os.path.join(WP2, "trials.csv"))
    t2 = t2[~t2.trial_key.str.contains("FAILED")]
    t2["config"] = [REFMAP.get((a, d)) for a, d in zip(t2.arm, t2.design)]
    t2 = t2[t2.config.notna()]
    t8 = pd.read_csv(os.path.join(W, "trials.csv"))
    t8["failed"] = t8.trial_key.str.contains("FAILED")
    t8f = t8[~t8.failed].copy()
    t8f["config"] = t8f.arm + ":" + t8f.design
    t = pd.concat([t2.assign(src="wp2"), t8f.assign(src="wp8")], ignore_index=True)
    t = t[t.inst.isin(DEV)]
    return t, t8


def per_inst(m, cfg, rep=None):
    d = m[m.config == cfg]
    if rep is not None:
        d = d[d.rep == rep]
    return d.groupby("inst").p100.mean().reindex(DEV)


def main():
    t, t8 = load()
    m = t[t.matched == True]  # noqa: E712
    L = ["# Track C Stage 2 summary (dev; P100 util %, matched WR only)", "",
         f"Track C ledger: {len(t8)} rows ({int(t8.failed.sum())} failed, "
         f"{int((~t8.failed & (t8.matched != True)).sum())} unmatched).", ""]
    cfgs = sorted(set(m[m.src == "wp8"].config))
    # ---- screen (rep 1)
    L += ["## Screen (rep 1, paired with WP2's rep 1 of X1 and A+α)", "",
          "| config | " + " | ".join(DEV) + " | mean | S1 | d_i>0 |", "|---" * (len(DEV) + 4) + "|"]
    x1, aa = per_inst(m, "X1", 1), per_inst(m, "A+a", 1)
    for name, s in [("X1 (r1)", x1), ("A+α (r1)", aa)]:
        L.append(f"| {name} | " + " | ".join(f"{v:.2f}" for v in s) + f" | {s.mean():.2f} | | |")
    s1 = {}
    for c in cfgs:
        y = per_inst(m, c, 1)
        d = np.minimum(x1 - y, aa - y)
        s1[c] = (d.mean(), int((d > 0).sum()), y.notna().sum())
        L.append(f"| {c} | " + " | ".join("–" if np.isnan(v) else f"{v:.2f}" for v in y) +
                 f" | {y.mean():.2f} | {d.mean():+.3f} | {int((d > 0).sum())}/{y.notna().sum()} |")
    gate = sorted([c for c in CANDS if c in s1 and s1[c][2] == 8 and s1[c][0] > 0],
                  key=lambda c: (-s1[c][0], -s1[c][1]))[:2]
    L += ["", f"Screen gate (S1 > 0, candidates only, at most 2): **{', '.join(gate) if gate else 'none'}**", ""]
    # ---- full (all matched retrains)
    L += ["## All matched retrains (finalist rule)", "",
          "| config | n | " + " | ".join(DEV) + " | mean | S | wins vs X1 | wins vs A+α | R7 − A+α | R6 − A+α |",
          "|---" * (len(DEV) + 8) + "|"]
    X1, AA = per_inst(m, "X1"), per_inst(m, "A+a")
    r7 = [i for i in DEV if i.startswith("Region7")]
    r6 = [i for i in DEV if i.startswith("Region6")]
    fin = []
    for c in ["A", "B", "A+a", "B+a", "D:F1PT", "X1"] + cfgs:
        y = per_inst(m, c)
        n = m[m.config == c].groupby("inst").size().reindex(DEV).fillna(0).astype(int)
        d = np.minimum(X1 - y, AA - y)
        wx, wa = int((y < X1).sum()), int((y < AA).sum())
        g7, g6 = (y[r7] - AA[r7]).mean(), (y[r6] - AA[r6]).mean()
        L.append(f"| {c} | {n.min()}-{n.max()} | " + " | ".join("–" if np.isnan(v) else f"{v:.2f}" for v in y) +
                 f" | {y.mean():.2f} | {d.mean():+.3f} | {wx}/8 | {wa}/8 | {g7:+.2f} | {g6:+.2f} |")
        if c in CANDS and n.min() >= 3 and d.mean() > 0 and wx >= 5 and wa >= 5 and g7 <= 0.5 and g6 <= 0.5:
            fin.append((d.mean(), int((d > 0).sum()), c))
    fin.sort(reverse=True)
    L += ["", f"Finalist (PLAN_C §3: n >= 3 everywhere, S > 0, >= 5/8 wins vs X1 and vs A+α, no region worse than A+α "
              f"by > 0.5, max 1): **{fin[0][2] if fin else 'NONE'}**", ""]
    # ---- mechanism by region
    L += ["## Mechanism by region (means over matched retrains x 4 instances)", "",
          "| region | config | P100 | P99 | top-5 | mean DT | first-access adm | peak-window adm | big-offset share | scan peak |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for reg in ("Region7", "Region6"):
        for c in ["A", "A+a", "X1"] + cfgs:
            d = m[(m.config == c) & m.inst.str.startswith(reg)]
            if len(d) == 0:
                continue
            L.append(f"| {reg} | {c} | {d.p100.mean():.2f} | {d.p99.mean():.2f} | {d.top5.mean():.2f} | "
                     f"{d.mean_dt.mean():.2f} | {d.k0_adm.mean():.3f} | {d.peak_adm.mean():.3f} | "
                     f"{d.peak_bigoff_share.mean():.3f} | {int((d.peak_bigoff_share > 0.25).sum())}/{len(d)} |")
    out = os.path.join(W, "results", "stage2_summary.md")
    open(out, "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
