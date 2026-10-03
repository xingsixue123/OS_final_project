"""Baleen peak-blind OPT (R0) on the held-out instances through the identical Track-B train/sim pipeline."""
import os, sys
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import q2sim as S

jobs = []
for r in ("Region7", "Region6"):
    for s in ("0.1", "0.2", "0.3"):
        inst = f"full_{r}_s{s}"
        ea = float(np.load(os.path.join(S.X, "common", "inst", f"{inst}.npz"))["ea"])
        jobs.append((None, None, r, float(s), ea, 30.0 if r == "Region7" else 27.8, f"ho_{inst}_R0",
                     dict(instance=inst, solver="R0_baleen", seed=0, form="none", budget=0), "baleen"))
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = [ex.submit(S.evaluate, *j) for j in jobs]
    for f in futs:
        try:
            f.result()
        except Exception as e:
            print("FAILED:", repr(e), flush=True)
