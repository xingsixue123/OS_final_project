"""Which day-1 episodes do candidate selections label positive? Focus: big-offset rows (end > 8 MB)."""
import sys, os, json, subprocess
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3lib as QL
X = os.environ["X_ROOT"]; MB = 1 << 20
region = sys.argv[1]
I = QL.Inst(f"{X}/common/inst/day1_{region}_s0.npz")
rows = I.acc_row == 1
bigrow = rows & (I.acc_meta[:, 4] > 8 * MB)
nbig = np.bincount(I.acc_ep[bigrow], minlength=I.n)          # big-offset training rows per episode
hotbig = np.zeros(I.n, bool)
# episode has a big-offset row with block count b0 >= 4
hb = bigrow & (I.acc_dyn[:, 0] >= 4)
hotbig[np.unique(I.acc_ep[hb])] = True
xb = I.baleen_x()
print(region, "episodes with big rows:", int((nbig > 0).sum()), "hot-big (big row with b0>=4):", int(hotbig.sum()),
      "Baleen-positive hot-big:", int(xb[hotbig].sum()), " big rows total", int(bigrow.sum()), "hot big rows", int(hb.sum()))
print("  hot-big episodes: DT sum %.1f (%.3f of all), s sum %.0f (%.3f of B), DT/size median %.4f, cutoff %.4f" % (
    I.sts[hotbig].sum(), I.sts[hotbig].sum() / I.sts.sum(), I.s[hotbig].sum(), I.s[hotbig].sum() / I.B,
    np.median(I.sts[hotbig] / np.maximum(I.s[hotbig], 1e-9)) if hotbig.any() else 0, (I.sts / np.maximum(I.s, 1e-9))[xb > 0].min()))
L = I.loads(xb) * QL.US
top = np.argsort(-L)[:5]
print("  day-1 top windows (Baleen labels):", [(int(w), round(float(L[w]), 2)) for w in top])
hbw = np.bincount(I.acc_w[hb], weights=QL.st(1, I.acc_nch[hb]) * QL.US, minlength=I.m)
print("  hot-big row load in those windows:", [round(float(hbw[w]), 2) for w in top])
for sol in sys.argv[2:]:
    z = np.load(sol)
    x = z["x"]
    print(f"  {os.path.basename(sol)}: n_pos={int(x.sum())} hot-big pos={int(x[hotbig].sum())} big-row pos rows={int(x[I.acc_ep[bigrow]].sum())}/{int(bigrow.sum())} "
          f"J={float((x*xb).sum()/((x+xb)>0).sum()):.3f}")
