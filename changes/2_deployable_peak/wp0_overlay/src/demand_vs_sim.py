"""Cross-check: the overlay's demand series (load_features.DemandLoad, GET-only, artifact service_time) summed over
each 10-minute log window equals the simulator's own per-window no-cache GET service time (`service_time_nocache`,
from a FROZEN simulation's stats file). -> results/demand_vs_sim.json

  cd work && taskset ... bwrap ... $BALEEN_PY -B ../src/demand_vs_sim.py
"""
import glob
import json
import os

import compress_json
import numpy as np

from BCacheSim.cachesim import load_features as LF

A = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    out = {}
    for region in ("Region7", "Region6"):
        rf = glob.glob(os.path.join(A, "work_frozen", "runs", "g1", f"g1_{region}_rejectx_frozen", "sim", "*",
                                    "*_cache_perf.txt.stats.lzma"))[0]
        st = compress_json.load(rf)
        b = st["batches"]
        noc = np.diff(np.asarray(b["service_time_nocache_stats"], float), prepend=0)
        tphy = np.asarray(b["time_phy"], float)
        dl = LF.demand_for_trace(f"data/tectonic/20230325/{region}/full_0_0.1.trace", 0.1)
        # sim window k = [t_start + 600 k, t_start + 600 (k+1)); time_phy[k] = time of the first access after it
        res = compress_json.load(rf.replace(".stats.lzma", ".lzma"))
        t0 = float(res["stats"]["start_ts_phy"])
        n = len(noc)
        ours = np.array([dl.window_st(t0 + 600 * (k + 1), 600) for k in range(n)])
        # the last entry is the final partial checkpoint at the last access (inclusive) -> compare all but last
        d = np.abs(ours[:-1] - noc[:-1])
        rel = d / np.maximum(noc[:-1], 1e-12)
        out[region] = dict(n_windows=int(n - 1), max_abs_diff_s=float(d.max()), max_rel_diff=float(rel.max()),
                           total_ours=float(ours[:-1].sum()), total_sim=float(noc[:-1].sum()),
                           peak_window_ours=int(ours[144:-1].argmax()) + 144, peak_window_sim=int(noc[144:-1].argmax()) + 144)
        print(region, out[region], flush=True)
    json.dump(out, open(os.path.join(A, "results", "demand_vs_sim.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
