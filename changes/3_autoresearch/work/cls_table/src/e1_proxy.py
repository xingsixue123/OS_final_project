"""E1: validate schedule-replay proxies on WP2's threshold variants (criterion pre-registered in PROGRESS.md
before any value was computed). DEV only.

  source env.sh && src/sbx.sh src/e1_proxy.py            -> results/e1_cells.csv, results/proxy_validation_e1.md
"""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402
sys.path.insert(0, C.WORK)
import emu  # noqa: E402
import schedemu as SE  # noqa: E402

WRMAP0 = {("Region7", "baleen"): (-1.288, 1.177), ("Region6", "baleen"): (-0.770, 1.146),
          ("Region7", "peak"): (-0.138, 0.860), ("Region6", "peak"): (0.520, 0.801)}   # WP2 seeding constants
VARIANTS = {   # (base arm, design) -> {variant name: (arms in WP2 trials, alpha)}
    ("A", "baleen"): {"none": (["A"], None), "a-1": (["Aa-1.0", "Ax-1.0"], -1.0)},
    ("B", "baleen"): {"none": (["B"], None), "a-1": (["Ba-1.0", "Bx-1.0"], -1.0), "a-0.5": (["Ba-0.5", "Bx-0.5"], -0.5)},
    ("D", "F1PT"): {"none": (["D"], None), "a-1": (["Ea-1.0"], -1.0), "a-0.5": (["Ea-0.5"], -0.5)},
    ("D", "F1CPSAT"): {"none": (["D"], None), "a-1": (["Ea-1.0", "Ex-1.0"], -1.0)},
    ("D", "F1EIM"): {"none": (["D"], None), "a-1": (["Ea-1.0"], -1.0)},
}


def emu_target(region, kind):
    a, b = WRMAP0[(region, kind)]
    return float(np.exp((np.log(C.TARGET_WR) - a) / b))


def main():
    C.configure("dev")
    t = pd.read_csv(os.path.join(C.WP2, "trials.csv"))
    t = t[~t.trial_key.astype(str).str.contains("FAILED") & (t.matched.astype(str) == "True")]
    rows = []
    for inst in C.DEV:
        E = emu.get(inst)
        S1, S2 = SE.SchedEmu(E, "day1"), SE.SchedEmu(E, "full")
        region = inst.split("_")[0]
        for (arm, design), V in VARIANTS.items():
            base = t[(t.arm == arm) & (t.design == design) & (t.inst == inst)]
            for _, br in base.iterrows():
                tk = br.trial_key
                rec = json.load(open(os.path.join(C.WP2, "results", "train", f"{tk}.json")))
                score = E.scores(rec["out"]["model_admit_threshold_binary"][0], br.ap_subset)
                kind = "baleen" if design == "baleen" else "peak"
                tgt = emu_target(region, kind)
                # sim day-1 series of the plain variant (P3 anchor)
                ws = C.window_series(os.path.join(C.WP2, br.result_file))
                used = ws["used"]
                scale = br.p100 / used[C.SKIP:].max()
                Sw = used[:SE.DAY1_W] * scale
                base1 = S1.budget_at_emu_wr(score[S1.idx], tgt)
                base2 = S2.budget_at_emu_wr(score[S2.idx], tgt)
                L1none = None
                for vname, (arms, alpha) in V.items():
                    sv = t[(t.arm.isin(arms)) & (t.design == design) & (t.inst == inst) & (t.train_key == tk)]
                    if len(sv) == 0:
                        continue
                    assert len(sv) == 1, (tk, vname, len(sv))
                    sv = sv.iloc[0]
                    r1 = S1.run(score[S1.idx], SE.powerlaw_g(S1.load_sub, alpha), W=base1["wch"])
                    r2 = S2.run(score[S2.idx], SE.powerlaw_g(S2.load_sub, alpha), W=base2["wch"])
                    if vname == "none":
                        L1none = r1["L"]
                    rows.append(dict(inst=inst, region=region, base=f"{arm}:{design}", retrain=tk, variant=vname,
                                     alpha=alpha, sim_p100=sv.p100, sim_wr=sv.wr, sim_theta=sv.threshold,
                                     P1=r1["peak"], P1_top5=r1["top5"], P1_theta=r1["theta"], P1_wch=r1["wch"],
                                     P2=r2["peak"], P2_theta=r2["theta"], _L1=r1["L"], _Sw=Sw, emu_target=tgt,
                                     W1=base1["wch"], plain_theta1=base1["theta"]))
                for r in rows:
                    if r["retrain"] == tk and "P3" not in r:
                        r["P3"] = float(np.max(r["_Sw"] + (r["_L1"] - L1none) * SE.US))
                print(inst, tk, {r["variant"]: (round(r["P1"], 2), round(r["P3"], 2), round(r["sim_p100"], 2))
                                 for r in rows if r["retrain"] == tk}, flush=True)
    df = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in rows])
    df.to_csv(os.path.join(C.RESULTS, "e1_cells.csv"), index=False)
    evaluate(df)


def sign_test_p(k, n):
    from scipy.stats import binomtest
    return float(binomtest(k, n, 0.5, alternative="greater").pvalue) if n else 1.0


def evaluate(df):
    out = ["# E1 proxy validation (criterion pre-registered in PROGRESS.md, E1 PRE-REGISTRATION)", "",
           f"Retrains: {df.retrain.nunique()}; variant rows: {len(df)}. Sim = WP2 matched P100.", ""]
    verdict = {}
    for P in ("P1", "P2", "P3"):
        # C1 pairwise concordance within retrain
        agree = n = 0
        for _, g in df.groupby("retrain"):
            g = g.reset_index(drop=True)
            for i in range(len(g)):
                for j in range(i + 1, len(g)):
                    ds = g.sim_p100[i] - g.sim_p100[j]
                    if abs(ds) < 0.25:
                        continue
                    n += 1
                    agree += int(np.sign(g[P][i] - g[P][j]) == np.sign(ds))
        conc = agree / n if n else float("nan")
        p = sign_test_p(agree, n)
        c1 = n > 0 and conc >= 0.70 and p < 0.05
        # C2 cells {A,B} x inst: alpha=-1 minus none
        cells = []
        for (b, inst), g in df[df.base.isin(["A:baleen", "B:baleen"])].groupby(["base", "inst"]):
            d = []
            for tk, h in g.groupby("retrain"):
                if {"none", "a-1"} <= set(h.variant):
                    hn, ha = h[h.variant == "none"].iloc[0], h[h.variant == "a-1"].iloc[0]
                    d.append((ha.sim_p100 - hn.sim_p100, ha[P] - hn[P]))
            if d:
                d = np.array(d)
                cells.append(dict(base=b, inst=inst, n=len(d), sim=d[:, 0].mean(), proxy=d[:, 1].mean()))
        cdf = pd.DataFrame(cells)
        same_mean_sign = np.sign(cdf.sim.mean()) == np.sign(cdf.proxy.mean())
        big = cdf[cdf.sim.abs() >= 0.25]
        agree2 = int((np.sign(big.sim) == np.sign(big.proxy)).sum())
        c2 = bool(same_mean_sign) and len(big) > 0 and agree2 / len(big) >= 0.70
        valid = bool(c1 and c2)
        verdict[P] = dict(C1_concordance=conc, C1_pairs=n, C1_p=p, C1=bool(c1), C2_mean_sim=float(cdf.sim.mean()),
                          C2_mean_proxy=float(cdf.proxy.mean()), C2_cells_agree=agree2, C2_cells=len(big), C2=bool(c2),
                          VALID=valid)
        out += [f"## {P}", "",
                f"- **C1** within-retrain pairs with |sim Δ| ≥ 0.25: {n}; concordant {agree} ({conc:.2f}); sign-test p = {p:.3g} → {'PASS' if c1 else 'FAIL'}",
                f"- **C2** α=−1 minus none, cells {{A,B}}×8: mean sim Δ {cdf.sim.mean():+.3f} vs proxy Δ {cdf.proxy.mean():+.3f} "
                f"(same sign: {bool(same_mean_sign)}); sign agreement on |sim Δ| ≥ 0.25 cells: {agree2}/{len(big)} → {'PASS' if c2 else 'FAIL'}",
                f"- **verdict: {'VALID' if valid else 'NOT VALID'}**", "",
                "| cell | n | sim Δ | proxy Δ |", "|---|---|---|---|"]
        out += [f"| {r.base} {r.inst} | {r.n} | {r.sim:+.2f} | {r.proxy:+.3f} |" for r in cdf.itertuples()]
        # diagnostics: per-instance spearman across all rows of the instance
        from scipy.stats import spearmanr, pearsonr
        sp = {i: spearmanr(g.sim_p100, g[P]).correlation for i, g in df.groupby("inst")}
        out += ["", "Per-instance Spearman (all variants of all retrains): " + ", ".join(f"{k} {v:+.2f}" for k, v in sp.items()),
                f"Pooled Pearson: {pearsonr(df.sim_p100, df[P])[0]:+.2f}", ""]
    json.dump(verdict, open(os.path.join(C.RESULTS, "e1_verdict.json"), "w"), indent=1)
    open(os.path.join(C.RESULTS, "proxy_validation_e1.md"), "w").write("\n".join(out) + "\n")
    print(json.dumps(verdict, indent=1))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--eval-only":
        evaluate(pd.read_csv(os.path.join(C.RESULTS, "e1_cells.csv")))
    else:
        main()
