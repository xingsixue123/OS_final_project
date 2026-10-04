"""Summaries of trials.csv (matched retrains only, every row counted; no selection):
results/summary_configs.csv  per (config, instance): n, mean/sd of P100, P99, top5, mean DT, WR, first-access admission,
                             peak-window big-offset share
results/summary_vs.csv       per config: wins / mean improvement / SE vs arm A and vs arm B (q3eval's SE:
                             sqrt(sum_i s_c,i^2/n_c,i + s_ref,i^2/n_ref,i)/N; plus instance-level SE), retention R
results/summary_2x2.csv      per design: (A - B) vs (C - D): does load help peak-aware labels more than Baleen labels?
results/summary.md           the same as markdown
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402

# offline (OPT-mode) P100 used by the retention ratio R = (A - X) / (OPT_baleen - OPT_peak)
OPT_BALEEN = {"Region7_s0": 34.52, "Region7_s0.1": 33.68, "Region7_s0.2": 35.28, "Region7_s0.3": 31.23,
              "Region6_s0": 35.56, "Region6_s0.1": 30.90, "Region6_s0.2": 30.62, "Region6_s0.3": 31.96}
OPT_PEAK = {"Region7_s0": 28.34, "Region7_s0.1": 27.61, "Region7_s0.2": 27.90, "Region7_s0.3": 26.76,
            "Region6_s0": 28.18, "Region6_s0.1": 26.41, "Region6_s0.2": 26.38, "Region6_s0.3": 27.32}
RX = {"Region7_s0": 42.46, "Region6_s0": 42.32}
CF = {"Region7_s0": 48.96, "Region6_s0": 43.45}
MET = ["p100", "p99", "top5", "mean_dt", "wr", "k0_adm", "peak_bigoff_share", "peak_adm"]


def config_name(r):
    if r["arm"] in ("A", "B"):
        return r["arm"]
    arm = "Dc" if (r["arm"] == "D" and r["design"] == "F1CPSAT") else r["arm"]
    # Ax/Bx/Ex = the same configuration as Aa/Ba/Ea, re-run with the threshold search widened to (0, 4]
    arm = {"Ax": "Aa", "Bx": "Ba", "Ex": "Ea"}.get(arm[:2], arm[:2]) + arm[2:] if arm[:2] in ("Ax", "Bx", "Ex") else arm
    return f"{arm}:{r['design']}"


def load_trials():
    t = pd.read_csv(os.path.join(C.W, "trials.csv"))
    t = t[~t["trial_key"].astype(str).str.contains("__FAILED_")].copy()
    t["config"] = t.apply(config_name, axis=1)
    t["matched"] = t["matched"].astype(str) == "True"
    return t


def baselines():
    """RejectX / CoinFlip per dev instance (explore/common/baselines.csv: authors' static_pf replays, bit-exact)."""
    b = pd.read_csv(os.path.join(C.COMMON, "baselines.csv"))
    out = {}
    for m in ("RejectX", "CoinFlip"):
        x = b[b["method"] == m].groupby("instance")["p100"].mean().to_dict()
        out[m] = {**x, **(RX if m == "RejectX" else CF)}
    return out


def per_instance(t):
    m = t[t["matched"]]
    g = m.groupby(["config", "inst"])
    agg = g[MET].mean().add_suffix("_mean")
    agg["p100_sd"] = g["p100"].std(ddof=1)
    agg["n"] = g.size()
    agg["n_all"] = t.groupby(["config", "inst"]).size()
    return agg.reset_index()


def versus(pi, ref):
    rows = []
    R = pi[pi["config"] == ref].set_index("inst")
    for cfg, d in pi.groupby("config"):
        if cfg == ref:
            continue
        d = d.set_index("inst")
        common = [i for i in C.DEV if i in d.index and i in R.index]
        if not common:
            continue
        diff = np.array([R.loc[i, "p100_mean"] - d.loc[i, "p100_mean"] for i in common])   # >0: config better
        var = [(d.loc[i, "p100_sd"] ** 2 / d.loc[i, "n"] if d.loc[i, "n"] > 1 else np.nan)
               + (R.loc[i, "p100_sd"] ** 2 / R.loc[i, "n"] if R.loc[i, "n"] > 1 else np.nan) for i in common]
        se = float(np.sqrt(np.nansum(var)) / len(common))
        se_inst = float(np.std(diff, ddof=1) / np.sqrt(len(common))) if len(common) > 1 else np.nan
        rows.append(dict(config=cfg, ref=ref, n_inst=len(common), wins=int((diff > 0).sum()), mean_improvement=float(diff.mean()),
                         se_retrain=se, se_instance=se_inst, pass_2se=bool(diff.mean() > 2 * se),
                         min_reps=int(d.loc[common, "n"].min()), per_inst=";".join(f"{i}:{x:+.2f}" for i, x in zip(common, diff))))
    return pd.DataFrame(rows)


def retention(pi):
    A = pi[pi["config"] == "A"].set_index("inst")
    rows = []
    for cfg, d in pi.groupby("config"):
        d = d.set_index("inst")
        for i in C.DEV:
            if i in d.index and i in A.index:
                rows.append(dict(config=cfg, inst=i, R=(A.loc[i, "p100_mean"] - d.loc[i, "p100_mean"]) / (OPT_BALEEN[i] - OPT_PEAK[i])))
    r = pd.DataFrame(rows)
    return r.groupby("config")["R"].agg(["mean", "min", "max", "count"]).reset_index() if len(r) else r


def two_by_two(pi):
    P = pi.set_index(["config", "inst"])["p100_mean"]
    rows = []
    designs = sorted({c.split(":")[1] for c in pi["config"] if c.startswith(("C:", "D:"))})
    for dsg in designs:
        for i in C.DEV:
            keys = [("A", i), ("B", i), (f"C:{dsg}", i), (f"D:{dsg}", i)]
            if all(k in P.index for k in keys):
                a, b, c, d = (P[k] for k in keys)
                rows.append(dict(design=dsg, inst=i, A=a, B=b, C=c, D=d, load_gain_baleen=a - b, load_gain_peak=c - d,
                                 interaction=(c - d) - (a - b), label_gain_noload=a - c, label_gain_load=b - d))
    return pd.DataFrame(rows)


def a_vs_phase1(t):
    """Arm A through the overlay vs phase-1 Baleen online retrains (explore/common/baselines.csv; frozen artifact)."""
    b = pd.read_csv(os.path.join(C.COMMON, "baselines.csv"))
    b = b[(b["method"] == "Baleen") & b["matched"].astype(bool)].drop_duplicates(subset=["instance", "rep", "p100"])
    a = t[(t["config"] == "A") & t["matched"]]
    rows = []
    for i in C.DEV:
        x = a[a["inst"] == i]["p100"].to_numpy()
        y = b[b["instance"] == i]["p100"].to_numpy()
        if len(x) == 0 or len(y) == 0:
            continue
        # pooled retrain sd (phase-1 and overlay retrains of the same instance); z of the difference of means
        dev = np.r_[x - x.mean(), y - y.mean()]
        sp_ = np.sqrt((dev ** 2).sum() / max(len(dev) - 2, 1)) if len(dev) > 2 else np.nan
        se = sp_ * np.sqrt(1 / len(x) + 1 / len(y))
        rows.append(dict(inst=i, A_n=len(x), A_mean=x.mean(), A_sd=x.std(ddof=1) if len(x) > 1 else np.nan,
                         phase1_n=len(y), phase1_mean=y.mean(), phase1_sd=y.std(ddof=1) if len(y) > 1 else np.nan,
                         diff=x.mean() - y.mean(), se=se, z=(x.mean() - y.mean()) / se if se > 0 else np.nan))
    return pd.DataFrame(rows)


def main():
    t = load_trials()
    pi = per_instance(t)
    pi.to_csv(os.path.join(C.RESULTS, "summary_configs.csv"), index=False)
    vs = pd.concat([versus(pi, "A"), versus(pi, "B")], ignore_index=True) if len(pi) else pd.DataFrame()
    bl = baselines()
    if len(vs):
        mean_p = pi.groupby("config")["p100_mean"].mean()
        vs["mean_p100"] = vs["config"].map(mean_p)
        vs["below_rejectx_coinflip"] = vs["config"].map(
            lambda c: bool(mean_p[c] < np.mean([bl["RejectX"][i] for i in C.DEV]) and mean_p[c] < np.mean([bl["CoinFlip"][i] for i in C.DEV])))
    vs.to_csv(os.path.join(C.RESULTS, "summary_vs.csv"), index=False)
    ret = retention(pi)
    ret.to_csv(os.path.join(C.RESULTS, "summary_retention.csv"), index=False)
    tt = two_by_two(pi)
    tt.to_csv(os.path.join(C.RESULTS, "summary_2x2.csv"), index=False)
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    wide = pi.pivot(index="config", columns="inst", values="p100_mean")[[i for i in C.DEV if i in pi["inst"].unique()]]
    wide["mean"] = wide.mean(axis=1)
    nrep = pi.pivot(index="config", columns="inst", values="n")
    print("P100 (matched mean) per config x instance\n", wide.round(2).to_string())
    print("\nmatched retrains\n", nrep.to_string())
    if len(vs):
        print("\nvs A / vs B\n", vs.drop(columns=["per_inst"]).round(3).to_string())
    if len(ret):
        print("\nretention R\n", ret.round(3).to_string())
    if len(tt):
        print("\n2x2 interaction (mean over instances)\n", tt.groupby("design")[["load_gain_baleen", "load_gain_peak", "interaction",
                                                                                 "label_gain_noload", "label_gain_load"]].agg(["mean", "count"]).round(3).to_string())
    av = a_vs_phase1(t)
    av.to_csv(os.path.join(C.RESULTS, "summary_A_vs_phase1.csv"), index=False)
    if len(av):
        print("\narm A (overlay) vs phase-1 Baleen online (frozen)\n", av.round(3).to_string(index=False))
    print("\nunmatched / failed rows:", int((~t["matched"]).sum()), "/",
          int(pd.read_csv(os.path.join(C.W, "trials.csv"))["trial_key"].astype(str).str.contains("__FAILED_").sum()))


if __name__ == "__main__" and len(sys.argv) == 1:
    main()


# ---------------------------------------------------------------- report tables (markdown) for RESULTS_dev.md
def finalist_scores(pi):
    """S(X) = mean_i min(A_i - X_i, B_i - X_i) (PROGRESS.md finalist rule); eligibility = >= 3 matched retrains on all
    8 dev instances; Ising-family arms D/D2/E only (Dc and C reported, not eligible)."""
    P = pi.set_index(["config", "inst"])
    rows = []
    for cfg in sorted(pi["config"].unique()):
        if cfg in ("A", "B"):
            continue
        d = [i for i in C.DEV if (cfg, i) in P.index]
        if not d:
            continue
        mins = [min(P.loc[("A", i), "p100_mean"], P.loc[("B", i), "p100_mean"]) - P.loc[(cfg, i), "p100_mean"] for i in d]
        both = sum(P.loc[(cfg, i), "p100_mean"] < min(P.loc[("A", i), "p100_mean"], P.loc[("B", i), "p100_mean"]) for i in d)
        nmin = int(min(P.loc[(cfg, i), "n"] for i in d))
        arm = cfg.split(":")[0]
        design = cfg.split(":")[1] if ":" in cfg else ""
        ising = design in ("F1PT", "F1EIM", "P0", "T2")
        eligible = ising and arm in ("D", "D2") or (ising and arm.startswith("E"))
        rows.append(dict(config=cfg, n_inst=len(d), min_matched_retrains=nmin, S=float(np.mean(mins)),
                         S_full8=bool(len(d) == 8), wins_both=int(both), ising_family=ising,
                         eligible=bool(eligible and len(d) == 8 and nmin >= 3)))
    s = pd.DataFrame(rows).sort_values("S", ascending=False)
    return s


def md_table(df, floatfmt=2):
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        vals = []
        for c in cols:
            v = r[c]
            if isinstance(v, (float, np.floating)):
                vals.append("" if np.isnan(v) else f"{v:.{floatfmt}f}")
            else:
                vals.append(str(v))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def report():
    t = load_trials()
    pi = per_instance(t)
    out = []
    # P100 mean +- sd (n) per config x instance
    cells = pi.assign(cell=pi.apply(lambda r: f"{r.p100_mean:.2f}" + (f" ± {r.p100_sd:.2f}" if r.n > 1 else "") + f" ({int(r.n)})", axis=1))
    wide = cells.pivot(index="config", columns="inst", values="cell")[[i for i in C.DEV if i in pi["inst"].unique()]]
    wide["mean P100"] = pi.groupby("config")["p100_mean"].mean().map(lambda v: f"{v:.2f}")
    out.append("### P100 per configuration and instance (mean ± sd over matched retrains, (n))\n\n" + md_table(wide.reset_index()))
    vs = pd.concat([versus(pi, "A"), versus(pi, "B")], ignore_index=True)
    vs = vs[["config", "ref", "n_inst", "min_reps", "wins", "mean_improvement", "se_retrain", "se_instance", "pass_2se"]]
    out.append("### Against arm A and arm B (improvement = ref - config, >0 better)\n\n" + md_table(vs, 3))
    fs = finalist_scores(pi)
    out.append("### Finalist score S(X) = mean_i min(A_i - X_i, B_i - X_i)\n\n" + md_table(fs, 3))
    m = t[t["matched"]].groupby("config")[["p100", "p99", "top5", "mean_dt", "wr", "k0_adm", "all_adm", "peak_bigoff_share",
                                           "peak_adm"]].mean()
    m["n"] = t[t["matched"]].groupby("config").size()
    out.append("### Secondary metrics (mean over matched retrains and instances)\n\n" + md_table(m.reset_index(), 3))
    ret = retention(pi)
    out.append("### Retention R = (A - X)/(OPT_peakblind - OPT_peakaware), per-instance mean\n\n" + md_table(ret, 3))
    tt = two_by_two(pi)
    if len(tt):
        g = tt.groupby("design")[["load_gain_baleen", "load_gain_peak", "interaction", "label_gain_noload", "label_gain_load"]]
        mm = g.mean()
        se = g.std(ddof=1) / np.sqrt(g.count())
        tab = mm.round(3).astype(str) + " ± " + se.round(3).astype(str)
        tab["n_inst"] = g.count()["interaction"]
        out.append("### 2x2: load gain for Baleen labels (A-B) vs for peak-aware labels (C-D); interaction = (C-D)-(A-B)\n\n"
                   + md_table(tab.reset_index()) + "\n\nPer instance:\n\n" + md_table(tt.round(2)))
    # Ising vs CP-SAT (D:F1PT, D:F1EIM vs Dc:F1CPSAT), paired per instance
    P = pi.set_index(["config", "inst"])["p100_mean"]
    rows = []
    for x in ("D:F1PT", "D:F1EIM"):
        d = [P[("Dc:F1CPSAT", i)] - P[(x, i)] for i in C.DEV if (x, i) in P.index and ("Dc:F1CPSAT", i) in P.index]
        if d:
            rows.append(dict(config=x, vs="Dc:F1CPSAT", n_inst=len(d), wins=int(sum(v > 0 for v in d)), mean_diff=float(np.mean(d)),
                             se_instance=float(np.std(d, ddof=1) / np.sqrt(len(d))) if len(d) > 1 else np.nan))
    if rows:
        out.append("### Ising labels vs CP-SAT labels (same F1 formulation; Dc - X, >0: Ising better)\n\n" + md_table(pd.DataFrame(rows), 3))
    av = a_vs_phase1(t)
    out.append("### Arm A (overlay) vs phase-1 Baleen online (frozen artifact)\n\n" + md_table(av, 3))
    open(os.path.join(C.RESULTS, "summary.md"), "w").write("\n\n".join(out) + "\n")
    fs.to_csv(os.path.join(C.RESULTS, "finalist_scores.csv"), index=False)
    print("\n\n".join(out))


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "report":
    report()
