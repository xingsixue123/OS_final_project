"""AR T1 SUPPLEMENTARY (non-protocol; reported separately, never in the pass rule): RejectX replays of the authors'
Region2 static_pf commands with the window factor (--ap-probability; window = factor x cache elements) bisected in
log space within its effective range so the write rate matches 35.599 MB/s +-1% (X = --ap-threshold 1 unchanged).
Frozen code. -> <test dir>/results_test/supp_rejectx.csv

  source env.sh && AR_TEST_DIR=<abs t1u_region2> src/sbx.sh src/supp_rejectx.py
"""
import math
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prep as P  # noqa: E402  (configures test mode; frozen-code train + sim helpers)
C = P.C


def one(key):
    job = C.JOBS[key]["rejectx_static"]
    exp = f"prep_rejectx_static_{key}"                     # re-uses the protocol replay's frozen training (same command)
    t = list(job["train_args"])
    t = C.set_flag(t, "--exp", exp)
    t = C.set_flag(t, "--output-base-dir", f"runs/prep/{exp}/train")
    out = P.run_train(exp, t, None)
    base = C.fill_sim_args(list(job["sim_args"]), out)
    T = C.TARGET_WR
    lo, hi = math.log(0.01), math.log(1e5)
    tried = []
    for _ in range(14):
        f = round(math.exp(0.5 * (lo + hi)), 6)
        r = P.sim_at(exp + "_supp", base, f)
        tried.append(r)
        if abs(r["wr"] - T) / T <= C.TOL:
            break
        if r["wr"] < T:
            lo = math.log(f)
        else:
            hi = math.log(f)
    best = min(tried, key=lambda r: abs(r["wr"] - T))
    m = C.metrics(best["result_file"])
    return dict(instance=key, method="RejectX_supp", window_factor=best["p"], n_sims=len(tried),
                matched=abs(best["wr"] - T) / T <= C.TOL, wr=m["wr"], p100=m["p100"],
                result_file=os.path.relpath(best["result_file"], C.W))


if __name__ == "__main__":
    assert os.path.exists(os.path.join(C.TEST_DIR, "TEST_GO"))
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(one, C.TEST))
    pd.DataFrame(rows).to_csv(os.path.join(C.RESULTS, "supp_rejectx.csv"), index=False)
    print(pd.DataFrame(rows).to_string())
