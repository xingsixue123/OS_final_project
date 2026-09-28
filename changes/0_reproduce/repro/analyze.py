"""Score finished jobs against the authors' rows and the pass criteria in REPRODUCE_PLAN.md.

  python repro/analyze.py fig9      -> work/results/fig9_jobs.csv, work/results/fig9_summary.md
  python repro/analyze.py smoke     -> README example check (expected 16.1% saving on Region1)

Peak load = the simulator's own PeakServiceTimeUtil1 result field, which is exactly what the
release CSV stores as P100ServiceTimeUtil@10m (checked bit-exact on replayed baseline runs).
Median/write rate come from the artifact's loader (episodic_analysis.exps.results.SimResult).
"""
import argparse
import json
import os
import sys

import common as C

PEAK_TOL_PP = 2.0      # |ours - authors| on peak load, percentage points
WR_TOL = 0.05          # achieved write rate within 5% of target
SAVING_TOL_PP = 3.0    # Baleen saving over RejectX within 3 pp of authors'


def load_metrics(result_file, region):
    sys.path.insert(0, C.WORK)
    os.chdir(C.WORK)
    from BCacheSim.episodic_analysis.exps import results
    r = results.get({"Region": region, "Filename": result_file})
    r.load_progress()
    ps = r._pstats["GET"]
    s = r.summary.iloc[0] if hasattr(r.summary, "iloc") and not hasattr(r.summary, "index") else r.summary
    if hasattr(s, "iloc") and getattr(s, "ndim", 1) == 2:
        s = s.iloc[0]
    import compress_json
    sim = compress_json.load(result_file)["results"]
    return {
        # The release CSV's P100ServiceTimeUtil@10m is the simulator's own PeakServiceTimeUtil1
        # (verified bit-exact: Region7 RejectX 42.455387 vs 42.455387). The loader's re-windowed
        # pstats P100 differs slightly and is kept only as a cross-check.
        C.Y: sim["PeakServiceTimeUtil1"],
        "loader_P100@10m": ps["P100ServiceTimeUtil@10m"],
        "P50ServiceTimeUtil@10m": ps["P50ServiceTimeUtil@10m"],
        "P100ServiceTimePercent@10m": ps.get("P100ServiceTimePercent@10m"),
        "Write Rate (MB/s)": float(s["Write Rate (MB/s)"]),
        "IOPSMissRatio": float(s["IOPSMissRatio"]) if "IOPSMissRatio" in s else None,
        "PeakServiceTimeSavedRatio1": float(s["PeakServiceTimeSavedRatio1"]) if "PeakServiceTimeSavedRatio1" in s else None,
    }


def statuses(set_name):
    d = os.path.join(C.JOBS_DIR, set_name)
    return {f[:-5]: json.load(open(os.path.join(d, f))) for f in sorted(os.listdir(d)) if f.endswith(".json")}


def analyze_smoke():
    st = statuses("smoke")
    m = {}
    for jid, s in st.items():
        if s["status"] == "done":
            m[s["job"]["policy"]] = load_metrics(s["result_file"], "Region1")
    for pol, v in m.items():
        print(f"{pol:8s} peak={v[C.Y]:.2f}%  WR={v['Write Rate (MB/s)']:.2f} MB/s  "
              f"PeakServiceTimeSavedRatio1={v['PeakServiceTimeSavedRatio1']:.4f}")
    if {"Baleen", "RejectX"} <= set(m):
        used = {p: 1 - m[p]["PeakServiceTimeSavedRatio1"] for p in m}
        saving = (1 - used["Baleen"] / used["RejectX"]) * 100
        print(f"\nREADME example (example.ipynb): Baleen peak saving over RejectX = {saving:.2f}%  "
              f"(authors: 16.11%)  -> {'PASS' if abs(saving - 16.11) <= SAVING_TOL_PP else 'CHECK'}")


def analyze_set(set_name):
    import pandas as pd
    rows = []
    for jid, s in statuses(set_name).items():
        j = s["job"]
        row = {"job_id": jid, "trace": j["trace"], "policy": j["policy"], "prefetching": j["prefetching"],
               "sample": j["sample_start"], "experiment": j["experiment"], "status": s["status"],
               "author_peak": j["author"][C.Y], "author_wr": j["author"]["Write Rate (MB/s)"],
               "author_iomiss": j["author"]["IOPSMissRatio"],
               "train_s": s.get("train_secs"), "sim_s": s.get("sim_secs"), "error": s.get("error", "")}
        if s["status"] == "done":
            m = load_metrics(s["result_file"], j["region"])
            row.update(ours_peak=m[C.Y], ours_wr=m["Write Rate (MB/s)"], ours_iomiss=m["IOPSMissRatio"],
                       ours_median=m["P50ServiceTimeUtil@10m"])
            row["d_peak"] = row["ours_peak"] - row["author_peak"]
            row["exact"] = abs(row["d_peak"]) < 1e-3 and abs(row["ours_wr"] - row["author_wr"]) < 1e-2
        rows.append(row)
    df = pd.DataFrame(rows)
    os.makedirs(os.path.join(C.WORK, "results"), exist_ok=True)
    df.to_csv(os.path.join(C.WORK, "results", f"{set_name}_jobs.csv"), index=False)

    done = df[df.status == "done"]
    lines = [f"# Reproduction: {set_name}", "",
             f"{len(done)}/{len(df)} jobs done. Metric: {C.Y} (peak backend load, %).", "",
             "## Per job (1:1 vs the authors' row)", "",
             "| job | author peak | ours | Δ | author WR | ours WR | bit-exact |", "|---|---|---|---|---|---|---|"]
    for _, r in df.iterrows():
        if r.status == "done":
            lines.append(f"| {r.job_id} | {r.author_peak:.2f} | {r.ours_peak:.2f} | {r.d_peak:+.2f} | "
                         f"{r.author_wr:.3f} | {r.ours_wr:.3f} | {'yes' if r.exact else ''} |")
        else:
            lines.append(f"| {r.job_id} | {r.author_peak:.2f} | {r.status} | | | {r.error} |")

    # Per Fig 9 bar: mean over replicate runs within a sample, then over samples (sampleright).
    def cell(d, col):
        return d.groupby("sample")[col].mean().mean()

    lines += ["", "## Per Fig 9 bar", "",
              "| trace | policy | prefetch | author | ours | Δ | spread of authors' runs | pass |",
              "|---|---|---|---|---|---|---|---|"]
    verdict, cells = [], {}
    for (trace, pol), d in df.groupby(["trace", "policy"], sort=False):
        dd = d[d.status == "done"]
        a = cell(d, "author_peak")
        o = cell(dd, "ours_peak") if len(dd) == len(d) else float("nan")
        cells[(trace, pol)] = (a, o)
        spread = d.author_peak.max() - d.author_peak.min()
        ok = abs(o - a) <= PEAK_TOL_PP
        verdict.append(ok)
        lines.append(f"| {trace} | {pol} | {d.prefetching.iloc[0]} | {a:.2f} | {o:.2f} | {o - a:+.2f} | "
                     f"{spread:.2f} | {'PASS' if ok else 'FAIL'} |")

    lines += ["", "## Per trace: ordering and Baleen saving over RejectX", ""]
    for trace in df.trace.unique():
        g = {p: cells.get((trace, p)) for p in C.POLICIES}
        if any(v is None for v in g.values()):
            continue
        a_sav = 100 * (1 - g["Baleen"][0] / g["RejectX"][0])
        o_sav = 100 * (1 - g["Baleen"][1] / g["RejectX"][1])
        order = g["Baleen"][1] < g["RejectX"][1] < g["CoinFlip"][1]
        ok = order and abs(o_sav - a_sav) <= SAVING_TOL_PP
        verdict.append(ok)
        lines.append(f"- **{trace}**: saving vs RejectX authors {a_sav:.1f}% / ours {o_sav:.1f}%; "
                     f"order Baleen<RejectX<CoinFlip: {order} -> {'PASS' if ok else 'FAIL'}")

    wr_bad = done[(done.ours_wr - C.TARGET_WR).abs() > WR_TOL * C.TARGET_WR]
    verdict.append(wr_bad.empty)
    lines += ["", f"- Write rate within ±{WR_TOL:.0%} of {C.TARGET_WR} MB/s for all jobs: "
              f"{'PASS' if wr_bad.empty else 'FAIL ' + ', '.join(wr_bad.job_id)}"]
    lines += ["", f"**Overall: {'PASS' if all(verdict) and len(done) == len(df) else 'NOT PASSED'}**"]
    devs = sorted({d for s in statuses(set_name).values() for d in s["job"].get("deviations", [])})
    lines += ["", "## Deviations from the authors' commands (applied to every job)", ""]
    lines += [f"- {d}" for d in devs] or ["- none"]
    lines += ["- training steps serialized (artifact hard-codes LightGBM num_threads=20); simulations "
              "run in parallel with OMP_NUM_THREADS capped per job"]
    out = os.path.join(C.WORK, "results", f"{set_name}_summary.md")
    open(out, "w").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\n-> {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("set")
    a = ap.parse_args()
    analyze_smoke() if a.set == "smoke" else analyze_set(a.set)
