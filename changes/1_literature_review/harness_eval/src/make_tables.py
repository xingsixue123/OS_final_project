"""Build markdown tables for RESULTS.md from results/offline.jsonl, gate0_all.csv, deployed.jsonl."""
import json
import os

import numpy as np
import pandas as pd

import hecommon as HC

ONLINE = {"Region7": (40.10, 0.18), "Region6": (43.25, 0.04)}
REJECTX = {"Region7": 42.455, "Region6": 42.321}
COINFLIP = {"Region7": 48.961, "Region6": 43.445}


def load(store):
    p = os.path.join(HC.RESULTS, f"{store}.jsonl")
    if not os.path.exists(p):
        return pd.DataFrame()
    df = pd.DataFrame([json.loads(l) for l in open(p) if l.strip()])
    for c in df.columns:
        if c not in ("region", "name", "cand", "args", "exp", "prefix", "result_file", "top5_windows", "matched"):
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def jacc(a, b):
    a, b = set(json.loads(a)), set(json.loads(b))
    return len(a & b) / len(a | b)


def offline_table():
    df = load("offline").drop_duplicates(["region", "name"], keep="last")
    g = pd.read_csv(os.path.join(HC.RESULTS, "gate0_all.csv")) if os.path.exists(
        os.path.join(HC.RESULTS, "gate0_all.csv")) else pd.DataFrame(columns=["region", "name"])
    out = []
    for region in ["Region7", "Region6"]:
        d = df[df.region == region]
        r0 = d[d.name == "R0"].iloc[0]
        lines = [f"\n**{region}** (R0 = Baleen peak-blind OPT: P100 {r0.p100:.2f}; Baleen online "
                 f"{ONLINE[region][0]:.2f} +- {ONLINE[region][1]:.2f})\n",
                 "| arm | analytic peak @W (%) | gap to z_LP @W | solve (s) | analytic peak @cutoff | R^2 (an. vs sim) | "
                 "sim P100 | P99 | top-5 mean | mean DT | WR (MB/s) | cutoff (MB/s) | sim argmax | analytic argmax "
                 "@cutoff | top-5 Jaccard vs R0 | dP100 vs R0 | dP100 vs online |",
                 "|" + "---|" * 17]
        for _, r in d.iterrows():
            gg = g[(g.region == region) & (g.name == r["name"])]
            aam = int(gg.analytic_argmax.iloc[0]) if len(gg) else ""
            anc = f"{gg.analytic_peak_util.iloc[0]:.2f}" if len(gg) else ""
            r2 = f"{gg.r2.iloc[0]:.3f}" if len(gg) else ""
            an = r.get("an_peak_util")
            if pd.isna(an) and len(gg):
                an = gg.analytic_peak_util_atW.iloc[0]
            zl = r.get("an_z_lp_util")
            lines.append(
                f"| {r['name']} | {an:.2f} | "
                f"{'' if pd.isna(r.get('an_gap_to_zlp')) else f'{100 * r.an_gap_to_zlp:.1f}% (z_LP {zl:.2f})'} | "
                f"{'' if pd.isna(r.get('an_solve_secs')) else f'{r.an_solve_secs:.0f}'} | {anc} | {r2} | **{r.p100:.2f}** | "
                f"{r.p99:.2f} | {r.top5:.2f} | {r.mean_dt:.2f} | {r.wr:.2f} | {r.threshold:.3f} | {int(r['argmax'])} | "
                f"{aam} | {jacc(r.top5_windows, r0.top5_windows):.2f} | {r.p100 - r0.p100:+.2f} | "
                f"{r.p100 - ONLINE[region][0]:+.2f} |")
        out += lines
    return "\n".join(out)


def deployed_table():
    df = load("deployed")
    if df.empty:
        return "(no deployed runs)"
    df = df.drop_duplicates(["region", "name", "rep"], keep="last")
    lines = ["| trace | arm | reps | P100 mean +- sd | per-rep P100 | P99 mean | top-5 mean | mean DT | WR range | "
             "vs Baleen online | vs RejectX | vs CoinFlip |", "|" + "---|" * 12]
    for (region, name), d in df.groupby(["region", "name"], sort=False):
        mu, sd = ONLINE[region]
        lines.append(f"| {region} | {name} | {len(d)} | **{d.p100.mean():.2f} +- {d.p100.std(ddof=1) if len(d) > 1 else 0:.2f}** | "
                     f"{', '.join(f'{x:.2f}' for x in d.p100)} | {d.p99.mean():.2f} | {d.top5.mean():.2f} | "
                     f"{d.mean_dt.mean():.2f} | {d.wr.min():.2f}-{d.wr.max():.2f} | {d.p100.mean() - mu:+.2f} | "
                     f"{d.p100.mean() - REJECTX[region]:+.2f} | {d.p100.mean() - COINFLIP[region]:+.2f} |")
    return "\n".join(lines)


if __name__ == "__main__":
    print(offline_table())
    print()
    print(deployed_table())
