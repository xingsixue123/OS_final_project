"""Read-only planning aid for the Stage-3 fresh test: which authors' Fig 9 rows exist for Region5 (20230325).
Imports 0_reproduce/repro/common.py read-only (python -B: no bytecode is written). Prints availability only."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
REPRO = os.path.normpath(os.path.join(HERE, "..", "..", "..", "0_reproduce"))
sys.path.insert(0, os.path.join(REPRO, "repro"))
import common as RC  # noqa: E402
df = RC.load_csv()
dfc = RC.canonical(df)
tr = "20230325/Region5"
print("best Baleen prefetch (Fig 9) for", tr, ":", RC.best_baleen_prefetch(dfc, tr))
for pol in ["Baleen", "RejectX", "CoinFlip"]:
    rows = RC.select_rows(dfc, tr, pol)
    g = rows.groupby("SampleStart")
    print(pol, {round(float(k), 2): (len(v), sorted(set(v.ExperimentName))) for k, v in g})
d = df[(df.Trace == tr) & (df.SampleRatio == 0.1) & (df.Prefetching == "OPT-Range on OPT-Ep-Start") &
       (df["Target DWPD"] == 7.5) & (df["Target Cache Size"].round(2) == 366.47) & (df.AdmissionPolicyLabel == "OPT AP")]
print("OPT AP rows per sample", d.groupby("SampleStart").size().to_dict())
data = os.path.join(HERE, "..", "work", "data", "tectonic", "20230325", "Region5")
print("local Region5 trace files:", sorted(f for f in os.listdir(data) if f.endswith(".trace")))
