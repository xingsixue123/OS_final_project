"""PM data collection (model-level, diagnostic + WR calibration data): for every WP2 dev evaluation (trials.csv,
read-only) and every simulated threshold of its convergence (results/converge/<trial_key>.csv): WP2's actual trained
admission model (results/train/<train_key>.json) -> emulated measures at that theta with the trial's alpha.
Output: results/pm_points.csv (one row per WP2 simulation). Resumable (skips trial keys already present).
  src/run.sh baleen ../src/pm_points.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "q3lib")]
import wpcommon as C  # noqa: E402
import proxy as PX  # noqa: E402

OUT = os.path.join(C.RESULTS, "pm_points.csv")


def main():
    t = pd.read_csv(os.path.join(PX.WP2, "trials.csv"))
    t = t[~t.trial_key.str.contains("FAILED")]
    assert set(t.inst) <= set(C.DEV)
    done = set(pd.read_csv(OUT).trial_key) if os.path.exists(OUT) else set()
    t = t.sort_values(["inst", "train_key"])
    for inst, ti in t.groupby("inst"):
        E = PX.get_emu(inst)
        for _, r in ti.iterrows():
            if r.trial_key in done:
                continue
            rec = json.load(open(os.path.join(PX.WP2, "results", "train", f"{r.train_key}.json")))
            mp = rec["out"]["model_admit_threshold_binary"][0]
            ap = r.ap_subset
            g = PX.scores_cached(E, "wp2_" + r.train_key, mp, ap)
            alpha = None if pd.isna(r.alpha) else float(r.alpha)
            cv = pd.read_csv(os.path.join(PX.WP2, "results", "converge", f"{r.trial_key}.csv"))
            rows = []
            for _, s in cv.iterrows():
                ev = PX.emu_eval(E, g, float(s.threshold), alpha)
                rows.append(dict(trial_key=r.trial_key, train_key=r.train_key, inst=inst, arm=r.arm, design=r.design,
                                 rep=int(r.rep), ap_subset=ap, alpha=alpha, trial_matched=bool(r.matched),
                                 trial_threshold=float(r.threshold), threshold=float(s.threshold), sim_wr=float(s.wr),
                                 sim_p100=float(s.peak), wp2_emu_wr=float(s.emu_wr) if "emu_wr" in s else np.nan,
                                 **{f"emu_{k}": v for k, v in ev.items() if k != "theta"}))
            pd.DataFrame(rows).to_csv(OUT, mode="a", header=not os.path.exists(OUT), index=False)
            print(f"{r.trial_key}: {len(rows)} sims, emu p100 at trial theta "
                  f"{[round(x['emu_p100'], 2) for x in rows if abs(x['threshold'] - x['trial_threshold']) < 1e-9]}",
                  flush=True)


if __name__ == "__main__":
    main()
