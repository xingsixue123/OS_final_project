"""Unit check of cachesim/load_features.DemandLoad against a naive per-request summation (sim's own
service_time_nocache accounting: sum of service_time(1, #chunks) over GET requests with t-L <= ts < t).

  cd wp0_overlay/work && bwrap ... $BALEEN_PY -B ../src/unit_load.py <Region> [n_samples]
"""
import json
import random
import sys

import numpy as np

from BCacheSim.cachesim import load_features as LF
from BCacheSim.cachesim import legacy_utils
from BCacheSim.episodic_analysis.episodes import service_time, st_to_util


def main():
    region = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
    f = f"data/tectonic/20230325/{region}/full_0_0.1.trace"
    dl = LF.demand_for_trace(f, 0.1)
    acc, s, e = legacy_utils.read_processed_file(f, get_features=True, only_gets=True)
    reqs = sorted([(a.ts, a.num_chunks()) for v in acc.values() for a in v.accesses])
    ts = np.array([r[0] for r in reqs])
    st1 = np.array([service_time(1, r[1]) for r in reqs])
    rng = random.Random(0)
    worst_rel, worst_abs, n_exact = 0.0, 0.0, 0
    probes = [rng.uniform(s - 100, e + 100) for _ in range(n // 2)] + [rng.choice(ts.tolist()) for _ in range(n // 2)]
    for t in probes:
        got = dl.load(t)
        want = []
        for w in LF.LOAD_WINDOWS_S:
            m = (ts >= t - w) & (ts < t)
            want.append(st_to_util(float(st1[m].sum()), sample_ratio=0.1, duration_s=w) * 100)
        for g, w_ in zip(got, want):
            d = abs(g - w_)
            worst_abs = max(worst_abs, d)
            if w_ != 0:
                worst_rel = max(worst_rel, d / abs(w_))
            n_exact += (g == w_)
    # windowed sum at 10-min boundaries == per-window no-cache DT (what the simulator logs as service_time_nocache)
    t0 = s
    k = np.arange(1, int((e - s) // 600) + 2)
    win = [dl.window_st(t0 + 600 * i, 600) for i in k]
    naive = [float(st1[(ts >= t0 + 600 * (i - 1)) & (ts < t0 + 600 * i)].sum()) for i in k]
    wdiff = max(abs(a - b) / max(abs(b), 1e-12) for a, b in zip(win, naive))
    # strict causality: a request exactly at t is not counted
    tq = float(ts[len(ts) // 2])
    cnt_lt = int(np.searchsorted(dl.ts, tq, side='left'))
    assert cnt_lt == int((ts < tq).sum())
    res = dict(region=region, n_gets=len(ts), n_probes=len(probes), n_values=3 * len(probes), n_exact=n_exact,
               max_abs_diff=worst_abs, max_rel_diff=worst_rel, window_sum_max_rel_diff=wdiff,
               tod_example=LF.tod(s), load_at_start=dl.load(s), load_example=dl.load(tq))
    print(json.dumps(res, indent=1))
    assert worst_rel <= 1e-9, worst_rel


if __name__ == "__main__":
    main()
