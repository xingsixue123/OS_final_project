"""Median-over-seeds tables (markdown) from results.csv."""
import json
import pandas as pd

d = pd.read_csv("results.csv")
d = d[d.status == "ok"]
ORDER = ["greedy", "repair_only", "lp", "milp", "ls_greedy", "ls_lp", "mfsb", "sb_ballistic", "sb_discrete", "dwave_sa",
         "dwave_tabu", "openjij_sa", "cim_extahc", "mq_bsb", "mq_dsb", "mq_cac", "mq_bsb_mf", "mq_dsb_mf",
         "mq_cac_mf", "mfsb_penalty_k0.1", "mfsb_penalty_k1.0", "mfsb_penalty_k10.0"]


def calls(e):
    try:
        return json.loads(e).get("calls", "")
    except Exception:
        return ""


d["calls"] = d.extra.map(calls)
out = []
for n, g in d.groupby("n"):
    ref = g.groupby("seed").first()[["z_lp", "greedy_peak", "headroom"]].median()
    out.append(f"\n### n = {n:,}  (median over seeds: z_LP = {ref.z_lp:.5f}, greedy peak = {ref.greedy_peak:.5f}, "
               f"headroom greedy - z_LP = {ref.headroom:.5f} = {100*ref.headroom/ref.greedy_peak:.2f}% of greedy peak)\n")
    out.append("| method | seeds | peak raw | peak repaired | use raw | use rep | gap abs | gap % of headroom | wall s | peak RSS MB | inner calls |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    ms = [m for m in ORDER if m in set(g.method)] + sorted(set(g.method) - set(ORDER))
    for m in ms:
        h = g[g.method == m]
        med = h[["peak_raw", "peak_rep", "use_raw", "use_rep", "gap_abs", "gap_pct", "wall_time", "peak_mem_mb"]].median()
        cc = "/".join(str(int(x)) for x in h.calls if x != "")
        out.append(f"| {m} | {len(h)} | {med.peak_raw:.5f} | {med.peak_rep:.5f} | {med.use_raw:.3f} | {med.use_rep:.3f} | "
                   f"{med.gap_abs:.5f} | {med.gap_pct:.1f} | {med.wall_time:.1f} | {med.peak_mem_mb:.0f} | {cc} |")
print("\n".join(out))
