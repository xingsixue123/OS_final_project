"""Dev-only mechanism look (no sims): for WP2 retrain r1 of A and B on the 8 Region6/7 dev instances, at the converged
alpha=-1 threshold of the matched WP2 A+alpha / B+alpha run: admission rate and no-cache DT share by access class
(big-offset = end offset > 8 MiB; new block = all 6 block-count features 0) at high load and in the simulated peak window."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
import wpcommon as C  # noqa: E402
sys.path.insert(0, C.WORK)
import emu  # noqa: E402
import q3lib as QL  # noqa: E402

C.configure("dev")
t2 = pd.read_csv(os.path.join(C.WP2, "trials.csv"))
t2 = t2[t2.matched.astype(str) == "True"]
rows = []
for inst in C.DEV8:
    E = emu.get(inst)
    big = E.F18[:, 4] > 8 * (1 << 20)
    new = (E.F18[:, 6:12].sum(1) == 0)
    stc = QL.st(1, E.I.acc_nch)
    for base, arms, sub in (("A", ("Aa-1.0", "Ax-1.0"), "meta+block+chunk"), ("B", ("Ba-1.0", "Bx-1.0"), "meta+block+chunk+load")):
        r = t2[(t2.arm.isin(arms)) & (t2.inst == inst) & (t2.rep == 1)]
        if not len(r):
            continue
        r = r.iloc[0]
        rec = json.load(open(os.path.join(C.WP2, "results", "train", f"{base}_baleen_{inst}_r1.json")))
        g = E.scores(rec["out"]["model_admit_threshold_binary"][0], sub)
        th = float(r.threshold)
        gm = E.gmult(-1.0)
        adm = g > th * gm
        ld = E.load[:, 0]
        hi = ld > np.quantile(ld, 0.9)
        pw = E.I.acc_w == int(r["argmax"])
        for cname, cm in (("big", big), ("small", ~big), ("new", new), ("seen", ~new)):
            rows.append(dict(inst=inst, base=base, cls=cname, p100=r.p100, share_acc=cm.mean(),
                             adm_all=adm[cm].mean(), adm_hi=adm[cm & hi].mean() if (cm & hi).any() else np.nan,
                             peak_dt_share=stc[pw & cm].sum() / max(stc[pw].sum(), 1e-9),
                             peak_adm=adm[pw & cm].mean() if (pw & cm).any() else np.nan,
                             score_med_hi=np.median(g[cm & hi]) if (cm & hi).any() else np.nan,
                             thr_hi=np.median(th * gm[cm & hi]) if (cm & hi).any() else np.nan))
        print(inst, base, "done", flush=True)
df = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(df.round(3).to_string())
df.to_csv(os.path.join(C.W, "analysis", "mech0.csv"), index=False)
