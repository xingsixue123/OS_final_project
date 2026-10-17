"""WP9: authors-vs-ours check of the frozen RejectX/CoinFlip replays. For every test instance and policy, the replay AT
THE AUTHORS' OWN --ap-probability (first sim of prep.py static) is compared with the authors' CSV P100 and write rate;
the row actually used as the baseline (results/static_baselines.csv: authors' p if matched, else the closest-WR point of
the bisection) is listed next to it. -> results/static_author_check.csv"""
import json
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wpcommon as C  # noqa: E402

rows = []
st = pd.read_csv(os.path.join(C.W, "results", "static_baselines.csv"))
for _, b in st.iterrows():
    jkey = ("rejectx" if b["method"] == "RejectX" else "coinflip") + "_static"
    J = C.JOBS[b["instance"]][jkey]
    p0 = float(C.get_flag(J["sim_args"], "--ap-probability"))
    out = f"runs/prep/prep_{jkey}_{b['instance']}/sim/p_{p0:.6f}"
    rf = C.result_files(out, work=C.WORK_FROZEN)[0]
    r = C.load_result(rf)["results"]
    rows.append(dict(instance=b["instance"], method=b["method"], author_p=p0,
                     author_p100=J["author"]["P100ServiceTimeUtil@10m"], ours_p100_at_author_p=r["PeakServiceTimeUtil1"],
                     abs_diff=abs(r["PeakServiceTimeUtil1"] - J["author"]["P100ServiceTimeUtil@10m"]),
                     author_wr=J["author"]["Write Rate (MB/s)"], ours_wr_at_author_p=r["FlashWriteRate"],
                     baseline_p=b["ap_probability"], baseline_p100=b["p100"], baseline_wr=b["wr"],
                     baseline_matched=b["matched"], n_sims=b["n_sims"]))
df = pd.DataFrame(rows).sort_values(["method", "instance"])
df.to_csv(os.path.join(C.W, "results", "static_author_check.csv"), index=False)
print(df.round(4).to_string(index=False))
print("max |ours - authors| P100 at the authors' p:", df["abs_diff"].max())
for m in ("RejectX", "CoinFlip"):
    print(m, "baseline mean P100", round(df[df.method == m]["baseline_p100"].mean(), 4),
          "| authors' mean", round(df[df.method == m]["author_p100"].mean(), 4))


# RejectX write-rate step (Region5): the replays closest to the target from BELOW and from ABOVE (any instance whose
# baseline is unmatched). -> results/static_rejectx_bracket.csv; evaluate_test.py requires an arm to be below RejectX
# with BOTH the baseline values (authors' bit-exact replays) and the below-step values (conservative; PROTOCOL_v2_H4 §3).
import glob  # noqa: E402

br = []
for _, b in st[st.method == "RejectX"].iterrows():
    pts = []
    for d in sorted(glob.glob(os.path.join(C.WORK_FROZEN, "runs", "prep", f"prep_rejectx_static_{b['instance']}", "sim", "p_*"))):
        rf = C.result_files(os.path.relpath(d, C.WORK_FROZEN), work=C.WORK_FROZEN)
        if rf:
            r = C.load_result(rf[0])["results"]
            pts.append(dict(p=float(os.path.basename(d)[2:]), wr=r["FlashWriteRate"], p100=r["PeakServiceTimeUtil1"]))
    lo = [x for x in pts if x["wr"] <= C.TARGET_WR * (1 + C.TOL)]
    lo = max(lo, key=lambda x: (x["wr"], x["p"])) if lo else None
    hi = [x for x in pts if x["wr"] > C.TARGET_WR * (1 + C.TOL)]
    hi = min(hi, key=lambda x: (x["wr"], x["p"])) if hi else None
    br.append(dict(instance=b["instance"], baseline_p100=b["p100"], baseline_wr=b["wr"], baseline_matched=b["matched"],
                   below_p=lo["p"] if lo else None, below_wr=lo["wr"] if lo else None,
                   below_p100=lo["p100"] if lo else None,
                   above_p=hi["p"] if hi else None, above_wr=hi["wr"] if hi else None, above_p100=hi["p100"] if hi else None,
                   step_dp=(hi["p"] - lo["p"]) if (lo and hi) else None))
br = pd.DataFrame(br)
br["rejectx_low_side_p100"] = [r.baseline_p100 if r.baseline_matched else r.below_p100 for r in br.itertuples()]
br.to_csv(os.path.join(C.W, "results", "static_rejectx_bracket.csv"), index=False)
print(br.round(4).to_string(index=False))
print("RejectX mean: baseline (authors' replays)", round(br.baseline_p100.mean(), 4), "| low-side (below the WR step)",
      round(br.rejectx_low_side_p100.mean(), 4))
