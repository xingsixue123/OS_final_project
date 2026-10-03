"""Timing-cleanliness summary: foreign CPU load on the timing cores (DIRECT, logical 0-7) and on their SMT siblings
(SIBLING, logical 12-19) during every timing run, from logs/core_audit.log (10-s samples of threads using > 5% of a
core; Track-B timing processes excluded).  Load of a run = foreign CPU-seconds overlapping [end - wall, end] divided
by the run's wall time = average number of foreign busy logical CPUs (0..8) during the run.

  python audit_load.py [trials.csv ...]
"""
import os
import re
import sys
from datetime import datetime

import numpy as np
import pandas as pd

AREA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LINE = re.compile(r"^(\d\d:\d\d:\d\d) (DIRECT|SIBLING) pid=\d+ tid=\d+ cpu=(\d+) used=([\d.]+)s/10s (.*)$")


def parse(path, day="2026-10-01"):
    rows = []
    prev = None
    d = datetime.fromisoformat(day)
    for l in open(path):
        m = LINE.match(l.strip())
        if not m:
            continue
        t = datetime.fromisoformat(f"{d.date()}T{m.group(1)}")
        if prev is not None and t < prev and (prev - t).total_seconds() > 3600:      # past midnight
            d = d.replace(day=d.day + 1)
            t = datetime.fromisoformat(f"{d.date()}T{m.group(1)}")
        prev = t
        rows.append(dict(t=t.timestamp(), kind=m.group(2), used=float(m.group(4)), cmd=m.group(5)[:80]))
    return pd.DataFrame(rows)


def load_for(A, start, end):
    """foreign CPU-seconds (DIRECT, SIBLING) overlapping [start, end]; each sample covers (t - 10, t]."""
    if not len(A):
        return 0.0, 0.0
    lo, hi = A.t.values - 10.0, A.t.values
    ov = np.clip(np.minimum(hi, end) - np.maximum(lo, start), 0, None) / 10.0
    sec = A.used.values * ov
    return float(sec[A.kind.values == "DIRECT"].sum()), float(sec[A.kind.values == "SIBLING"].sum())


def main():
    A = parse(os.environ.get("AUDIT_LOG", os.path.join(AREA, "logs", "core_audit.log")),
              day=os.environ.get("AUDIT_DAY", "2026-10-01"))
    paths = sys.argv[1:] or [os.path.join(AREA, "trials.csv")]
    for p in paths:
        T = pd.read_csv(p)
        T = T[T.status == "ok"].copy()
        end = np.array([datetime.fromisoformat(x).timestamp() for x in T.ts])
        dl, sl = [], []
        for e, w in zip(end, T.wall.values):
            a, b = load_for(A, e - w - 0.5, e)
            dl.append(a / max(w, 1e-9))
            sl.append(b / max(w, 1e-9))
        T["direct_load"] = dl
        T["sibling_load"] = sl
        T = T[pd.to_datetime(T.ts) >= pd.Timestamp(os.environ.get("AUDIT_FROM", "2026-10-01 15:00:00"))]
        g = T.groupby(["phase", "family"]).agg(n=("wall", "size"), direct=("direct_load", "mean"),
                                               sibling=("sibling_load", "mean"),
                                               sib_p90=("sibling_load", lambda x: np.percentile(x, 90)),
                                               frac_any_direct=("direct_load", lambda x: float((x > 0.05).mean())))
        print(p)
        print(g.round(3).to_string())
        T[["key", "phase", "instance", "solver", "family", "budget", "seed", "wall", "direct_load",
           "sibling_load"]].to_csv(p.replace(".csv", os.environ.get("AUDIT_SUFFIX", "_audit_load.csv")), index=False)


if __name__ == "__main__":
    main()
