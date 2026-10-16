"""Stage-1 table: offline + stability + learnability + proxy for every Track C design and the references.
Offline statistics are recomputed uniformly from the label files (x_full) on the day-1 instances.
Outputs results/stage1_table.md, results/stage1_offline.csv, results/stage1_proxy_cells.csv.
  src/run.sh baleen ../src/table.py
"""
import itertools
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "q3lib")]
import wpcommon as C  # noqa: E402
import proxy as PX  # noqa: E402
import q3lib as QL  # noqa: E402

DESIGNS_C = ["F1PT4", "ANC3", "ANC10", "ANC30", "TK10", "TK72", "ANC10TK10", "STU10R1", "STU10R2", "STU30R1", "ANC10CP"]
REFS = {"Baleen": None, "F1PT": "wp2", "F1CPSAT": "wp2"}


def label_file(inst, d, k):
    if REFS.get(d) == "wp2":
        return os.path.join(PX.WP2, "labels", f"{inst}_{d}_s{k}.npz")
    return os.path.join(C.LABELS, f"{inst}_{d}_s{k}.npz")


def offline():
    rows = []
    for inst in C.DEV:
        I = QL.Inst(os.path.join(C.COMMON, "inst", f"day1_{inst}.npz"))
        xb = I.baleen_x()
        dmax = np.asarray(I.D.max(1).todense()).ravel()
        nacc = I.z["num_accesses"]
        for d in ["Baleen"] + list(REFS)[1:] + DESIGNS_C:
            xs = {}
            for k in (1, 2, 3):
                if d == "Baleen":
                    xs[k] = xb
                else:
                    f = label_file(inst, d, k)
                    if os.path.exists(f):
                        xs[k] = np.load(f)["x_full"].astype(float)
            if not xs:
                continue
            for k, x in xs.items():
                L = I.loads(x) * QL.US
                srt = np.sort(L)[::-1]
                rows.append(dict(inst=inst, design=d, seed=k, n_label=int(x.sum()), peak=srt[0], top10=srt[:10].mean(),
                                 mean_load=L.mean(), jacc_baleen=(x * xb).sum() / max(((x + xb) > 0).sum(), 1),
                                 hamming_baleen=int(np.abs(x - xb).sum()),
                                 zero_value=int(((x > 0.5) & (dmax <= 1e-12)).sum()),
                                 single_acc_share=float(((x > 0.5) & (nacc <= 1)).sum() / max(x.sum(), 1)),
                                 small_share=float(((x > 0.5) & (I.nchunks <= 2)).sum() / max(x.sum(), 1))))
            js = [(xs[a] * xs[b]).sum() / max(((xs[a] + xs[b]) > 0).sum(), 1) for a, b in itertools.combinations(sorted(xs), 2)]
            rows.append(dict(inst=inst, design=d, seed=0, stab_jaccard=float(np.mean(js)) if js else np.nan))
    return pd.DataFrame(rows)


def fmt(m, s=None, p=2):
    if pd.isna(m):
        return "–"
    return f"{m:.{p}f}" + (f" ± {s:.{p}f}" if s is not None and not pd.isna(s) else "")


def main():
    off = offline()
    off.to_csv(os.path.join(C.RESULTS, "stage1_offline.csv"), index=False)
    o = off[off.seed > 0].groupby("design").agg(peak=("peak", "mean"), top10=("top10", "mean"), n_label=("n_label", "mean"),
                                                 jacc=("jacc_baleen", "mean"), ham=("hamming_baleen", "mean"),
                                                 zv=("zero_value", "mean"), small=("small_share", "mean"))
    o["stab"] = off[off.seed == 0].groupby("design").stab_jaccard.mean()
    # learnability (learn.py protocol, seed 1): net = ll(shuf) - ll(load), block split
    lr = []
    for f in (os.path.join(C.RESULTS, "learnability.csv"), os.path.join(PX.WP2, "results", "learnability.csv")):
        if os.path.exists(f):
            x = pd.read_csv(f)
            x = x[x.split == "block"]
            pv = x.pivot_table(index=["inst", "labels"], columns="feat", values="val_logloss").reset_index()
            pv["net"] = pv["shuf"] - pv["load"]
            pv["src"] = "wp2" if "wp2_deployed" in f else "c"
            lr.append(pv[["inst", "labels", "net", "src"]])
    lr = pd.concat(lr) if lr else pd.DataFrame(columns=["inst", "labels", "net", "src"])
    lr["labels"] = lr["labels"].replace({"baleen": "Baleen"})
    lr = lr.drop_duplicates(["inst", "labels"], keep="first")
    lg = lr.groupby("labels").net.agg(["mean", "std", "size"])
    # proxy
    P = pd.read_csv(os.path.join(C.RESULTS, "proxy_ledger.csv"))
    P = P[P.kind == "pl"]
    cmap = {"Baleen": ("B", "B+a", "A", "A+a"), "F1PT": ("D:F1PT", "X1"), "F1CPSAT": ("Dc", "Ec")}
    cells = []
    for d in list(REFS) + DESIGNS_C:
        names = {"Baleen": [("B", "none"), ("B+a", "-1"), ("A", "none (orig feats)"), ("A+a", "-1 (orig feats)")],
                 "F1PT": [("D:F1PT", "none"), ("X1", "-1")], "F1CPSAT": [("Dc", "none"), ("Ec", "-1")]}.get(
            d, [(f"D:{d}", "none"), (f"E:{d}", "-1")])
        for cfg, al in names:
            q = P[P.config == cfg]
            if len(q) == 0:
                continue
            per = q.groupby("inst").agg(m=("p100", "mean"), sd=("p100", "std"), k0=("k0_adm", "mean"), n=("p100", "size"))
            cells.append(per.assign(design=d, config=cfg, alpha=al).reset_index())
    cells = pd.concat(cells)
    cells.to_csv(os.path.join(C.RESULTS, "stage1_proxy_cells.csv"), index=False)
    piv = cells.pivot_table(index="inst", columns="config", values="m")
    lines = ["# Stage-1 table (DEV: Region7/Region6 x samples 0-0.3; 8 instances; label seeds 1-3)", "",
             "Offline = day-1 instance (all 145 windows), util %. Stability = mean pairwise Jaccard of the label sets of",
             "seeds 1-3. Learnability = learn.py protocol (seed-1 labels, block split): net logloss gain from `load`",
             "= ll(+shuffled load) - ll(+load), mean ± sd over 8 instances. PL = label-level proxy (emulated deployed",
             "P100, refit GBM + calibrated threshold; mean over instances of the per-instance mean over seeds 1-3;",
             "± = mean per-instance sd over seeds). dX1 / dAa = paired proxy difference vs X1 / vs A+α (negative =",
             "design better), mean over instances (wins/8). **The proxy failed its pre-registered validation (see",
             "proxy_validation.md) unless stated otherwise; PL columns are diagnostics, not evidence.**", "",
             "| design | day-1 peak | top-10 | #labels | J vs Baleen | stability J | zero-value | small (≤2 ch) share | learnability net | PL α none | PL α=−1 | k0 adm (α=−1) | dX1 (α=−1) | dAa (α=−1) |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for d in list(REFS) + DESIGNS_C:
        if d not in o.index:
            continue
        r = o.loc[d]
        lg_ = lg.loc[d] if d in lg.index else None
        c = cells[cells.design == d]
        def cfgval(alpha_key):
            q = c[c.alpha == alpha_key]
            if len(q) == 0:
                return "–", None
            return f"{q.m.mean():.2f} ± {q.sd.mean():.2f}", q
        s_none, _ = cfgval("none")
        s_a, qa = cfgval("-1")
        k0 = f"{qa.k0.mean():.3f}" if qa is not None else "–"
        if qa is not None and "X1" in piv and "A+a" in piv:
            cf = qa.config.iloc[0]
            dx = piv[cf] - piv["X1"]
            da = piv[cf] - piv["A+a"]
            sdx = f"{dx.mean():+.2f} ({(dx < 0).sum()}/8)"
            sda = f"{da.mean():+.2f} ({(da < 0).sum()}/8)"
        else:
            sdx = sda = "–"
        lines.append(f"| {d} | {r.peak:.2f} | {r.top10:.2f} | {r.n_label:.0f} | {r.jacc:.3f} | {fmt(r.stab, p=3)} | "
                     f"{r.zv:.1f} | {r.small:.3f} | "
                     f"{fmt(lg_['mean'], lg_['std'], 3) if lg_ is not None else '–'} | {s_none} | {s_a} | {k0} | {sdx} | {sda} |")
    if "A" in piv:
        lines.append("")
        lines.append(f"Baleen-label rows with original features: PL A = {piv['A'].mean():.2f}, A+α = {piv['A+a'].mean():.2f}.")
    # per-region proxy means for alpha -1
    lines.append("\n### PL α = −1 by region (mean over 4 instances)\n")
    lines.append("| config | Region7 | Region6 |")
    lines.append("|---|---|---|")
    for cf in ["A+a", "B+a", "X1", "Ec"] + [f"E:{d}" for d in DESIGNS_C]:
        if cf in piv:
            r7 = piv.loc[[i for i in piv.index if i.startswith("Region7")], cf].mean()
            r6 = piv.loc[[i for i in piv.index if i.startswith("Region6")], cf].mean()
            lines.append(f"| {cf} | {r7:.2f} | {r6:.2f} |")
    open(os.path.join(C.RESULTS, "stage1_table.md"), "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
