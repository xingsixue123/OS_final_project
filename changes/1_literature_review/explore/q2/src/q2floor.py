"""Per-instance F1 floor: max_w (C_w - sum of positive d(e,w)) over objective windows = a lower bound on the peak of
ANY selection (budget ignored). A level whose optimum equals it is 'floored' (all good solvers tie there)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import q2core as C
Q2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
paths = [os.path.join(Q2, "inst", f"dev_{r}.npz") for r in ("Region7", "Region6")] + \
        [os.path.join(Q2, "..", "common", "inst", f"full_{r}_s{s}.npz") for r in ("Region7", "Region6") for s in ("0.1", "0.2", "0.3")]
for p in paths:
    I = C.Instance(p)
    Dp = I.Da.copy(); Dp.data = np.maximum(Dp.data, 0)
    low = I.Ca - np.asarray(Dp.sum(0)).ravel()
    xg = I.greedy_prefix(I.B)
    print(f"{I.name:22s} floor={low.max() * C.US:8.4f}  argmax_w={I.act_idx[int(np.argmax(low))]}  "
          f"Baleen-greedy peak@W={I.loads(xg).max() * C.US:8.4f}")
