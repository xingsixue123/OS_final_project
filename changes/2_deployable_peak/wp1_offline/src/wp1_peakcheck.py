"""Model-vs-simulator check at the simulated peak (Baleen env): for every instance's R0 simulation, compare at the
simulated argmax window the simulator's no-cache DT (service_time_nocache) and used DT with the instance's analytic
C_w (no-cache DT of the episodes' GET accesses) and the analytic floor (C_w - every positive saving), util %.
-> results/peakcheck.csv"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); WP1 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import p2sim as S
import scipy.sparse as sp
US = 1.0 / 36 * (100.0 / 0.1) / 600 * 100
rows = [json.loads(l) for l in open(os.path.join(WP1, "results", "sims.jsonl")) if l.strip()]
out = ["instance,method,p100,argmax,sim_used_util,sim_nocache_util,inst_C_util,inst_floor_util,scale"]
import compress_json
for r in rows:
    if r.get("method") not in ("R0", "pt") or not r.get("matched"):
        continue
    k = r["instance"]
    z = np.load(os.path.join(WP1, "inst", f"full_{k}.npz"))
    res = compress_json.load(r["result_file"])["results"]
    st_f = r["result_file"].replace("_cache_perf.txt.lzma", "_cache_perf.txt.stats.lzma")
    st = compress_json.load(st_f)
    b = st["batches"] if "batches" in st else st["stats"]["batches"]
    used = np.diff(np.asarray(b["service_time_used_stats"], float), prepend=0)
    noc = np.diff(np.asarray(b["service_time_nocache_stats"], float), prepend=0)
    w = int(r["argmax"])
    scale = res["PeakServiceTimeUtil1"] / used[144:].max()
    D = sp.csr_matrix((z["D_data"], z["D_indices"], z["D_indptr"]), shape=tuple(z["D_shape"]))
    Dp = D.copy(); Dp.data = np.maximum(Dp.data, 0)
    fl = z["C"] - np.asarray(Dp.sum(0)).ravel()
    out.append(f"{k},{r['method']},{r['p100']:.3f},{w},{used[w]*scale:.3f},{noc[w]*scale:.3f},{z['C'][w]*US:.3f},"
               f"{fl[w]*US:.3f},{scale:.5f}")
open(os.path.join(WP1, "results", "peakcheck.csv"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
