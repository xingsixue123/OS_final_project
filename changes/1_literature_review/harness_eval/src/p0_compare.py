"""Compare per-episode thresholds/labels across the P0 decision files."""
import json, os, sys
import numpy as np
import compress_pickle
import hecommon as HC

runs = json.load(open(os.path.join(HC.WORK, "p0", "decisions.json")))
def load(p):
    d = compress_pickle.load(p)
    out = {}
    for k, eps in d.items():
        for (key, tsl, tsp, off), kw in eps:
            out[(str(key), float(tsp[0]))] = (kw["threshold"], kw["score"])
    return out
D = {k: load(v) for k, v in runs.items()}
ref = D["A1"]
rows = []
for k, d in D.items():
    assert set(d) == set(ref), k
    th = np.array([d[e][0] for e in ref]); th0 = np.array([ref[e][0] for e in ref])
    sc = np.array([d[e][1] for e in ref]); sc0 = np.array([ref[e][1] for e in ref])
    lab = th < HC.TARGET_WR; lab0 = th0 < HC.TARGET_WR
    rows.append(dict(run=k, n=len(ref), identical_thresholds=int((th == th0).sum()),
                     max_abs_th_diff=float(np.abs(th - th0).max()), label_diff=int((lab != lab0).sum()),
                     n_pos=int(lab.sum()), scores_identical=bool((sc == sc0).all())))
    # episodes whose thresholds differ: are they all score-tied with another episode?
    diff = np.flatnonzero(th != th0)
    if len(diff):
        vals, cnt = np.unique(sc0, return_counts=True)
        tied = set(vals[cnt > 1])
        rows[-1]["diff_all_in_score_ties"] = bool(all(sc0[i] in tied for i in diff))
for r in rows: print(json.dumps(r))
import pandas as pd
pd.DataFrame(rows).to_csv(os.path.join(HC.RESULTS, "p0_skeleton_verify.csv"), index=False)

# Stronger check: per score-tie group, the group's threshold range (min, max) is identical
# (i.e. runs differ only by the order of episodes inside a tie group, as stock-vs-stock does).
def group_ranges(d):
    g = {}
    for e, (th, sc) in d.items():
        lo, hi = g.get(sc, (np.inf, -np.inf))
        g[sc] = (min(lo, th), max(hi, th))
    return g
g0 = group_ranges(ref)
for k, d in D.items():
    g = group_ranges(d)
    bad = [s for s in g0 if not (np.isclose(g[s][0], g0[s][0], rtol=0, atol=1e-6 * 0 + 0.2) and np.isclose(g[s][1], g0[s][1], rtol=1e-9))]
    print(k, "score groups:", len(g0), "groups with different max-threshold:", len(bad))
