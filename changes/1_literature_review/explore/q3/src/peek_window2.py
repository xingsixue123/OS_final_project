import sys, os, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3lib as QL
import lightgbm as lgb
X = os.environ["X_ROOT"]; H = os.path.normpath(os.path.join(X, "..", "harness_eval"))
region, wins = sys.argv[1], [int(w) for w in sys.argv[2].split(",")]
I = QL.Inst(f"{X}/common/inst/fullml_{region}_s0.npz")
F = QL.sim_features(I, cache=f"{X}/q3/work/cache/simfeat_fullml_{region}_s0.npz").astype(float)
exp = f"dep_{region}_R0_rep1"
log = open(f"{H}/work/logs/dep/{exp}/train.log").read().splitlines()
mp = [l.split(" ")[1] for l in log if l.startswith("model_admit_threshold_binary ") and l.endswith("M")][0]
bst = lgb.Booster(model_file=f"{H}/work/{mp}")
g = bst.predict(F)
dep = pd.read_csv(f"{H}/results/deployed.csv"); th = float(dep[(dep.region == region) & (dep.name == "R0")].threshold.iloc[0])
xb = I.baleen_x()      # Baleen OPT selection at W on the full trace (EA_ml episodes)
kst = QL.first_admit(I, g > th)
print(region, "online threshold", th, "episodes admitted (emu)", (kst >= 0).sum(), "OPT-selected", int(xb.sum()))
blk = I.block_ids()
for w in wins:
    a = np.flatnonzero(I.acc_w == w)
    eps = np.unique(I.acc_ep[a])
    stc = QL.st(1, I.acc_nch[a])
    print(f"\n== window {w}: accesses {len(a)}, episodes {len(eps)}, C_w util {I.C[w]*QL.US:.2f}")
    # per-episode contribution to C_w and status
    rows = []
    for e in eps:
        m = a[I.acc_ep[a] == e]
        k0 = I.acc_k[m].min()
        rows.append(dict(ep=e, n_in_w=len(m), C_util=float(QL.st(1, I.acc_nch[m]).sum() * QL.US), k_first_in_w=int(k0),
                         ep_start_w=int((I.ts0[e] - I.t0) // 600), n_acc=int(I.z["num_accesses"][e]), nch=int(I.nchunks[e]),
                         opt=int(xb[e]), emu_kstar=int(kst[e]), gmax_before=float(g[I.acc_start[e]:I.acc_start[e] + k0 + 1].max()),
                         g_first=float(g[I.acc_start[e]]), op=int(I.acc_meta[m[0], 0]), ns=int(I.acc_meta[m[0], 1]), user=int(I.acc_meta[m[0], 2]),
                         d_w_util=float(I.D[e, w] * QL.US)))
    d = pd.DataFrame(rows).sort_values("C_util", ascending=False)
    print("episodes started in this window: %d, contributing %.2f util; started earlier: %.2f util" % (
        (d.ep_start_w == w).sum(), d[d.ep_start_w == w].C_util.sum(), d[d.ep_start_w < w].C_util.sum()))
    print("savable (sum d(e,w) over all eps):  %.2f util; OPT-selected saves %.2f; emulated online saves ~%.2f" % (
        d.d_w_util.sum(), d[d.opt == 1].d_w_util.sum(),
        d[(d.emu_kstar >= 0) & (d.emu_kstar <= d.k_first_in_w)].d_w_util.sum()))
    print(d.head(15).round(3).to_string())
    print("by (op,ns,user):"); print(d.groupby(["op", "ns", "user"]).agg(C=("C_util", "sum"), n=("ep", "size"), opt=("opt", "sum"), dsum=("d_w_util", "sum")).sort_values("C", ascending=False).head(8).round(2).to_string())
