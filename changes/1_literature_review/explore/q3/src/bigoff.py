import sys, os, json
import numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3lib as QL
X = os.environ["X_ROOT"]; H = os.path.normpath(os.path.join(X, "..", "harness_eval"))
MB = 1 << 20
dep = pd.read_csv(f"{H}/results/deployed.csv")
for region in ["Region7", "Region6"]:
    I = QL.Inst(f"{X}/common/inst/fullml_{region}_s0.npz")
    F = QL.sim_features(I, cache=f"{X}/q3/work/cache/simfeat_fullml_{region}_s0.npz").astype(float)
    log = open(f"{H}/work/logs/dep/dep_{region}_R0_rep1/train.log").read().splitlines()
    mp = [l.split(" ")[1] for l in log if l.startswith("model_admit_threshold_binary ") and l.endswith("M")][0]
    g = lgb.Booster(model_file=f"{H}/work/{mp}").predict(F)
    th = float(dep[(dep.region == region) & (dep.name == "R0")].threshold.iloc[0])
    end = F[:, 4]
    big = end > 8 * MB
    stc = QL.st(1, I.acc_nch) * QL.US
    print(f"\n{region}: accesses with end offset > 8MB: {big.mean():.4f} of all; rejected frac (g<th) big {np.mean(g[big] < th):.3f} vs small {np.mean(g[~big] < th):.3f}")
    # per test window: rejected load from big-offset accesses
    rej = g < th
    Lbig = np.bincount(I.acc_w, weights=stc * (big & rej), minlength=I.m)
    Lall_rej = np.bincount(I.acc_w, weights=stc * rej, minlength=I.m)
    order = np.argsort(-I.C[144:])[:0]
    for w in ([712, 152, 816] if region == "Region6" else [646, 660, 613, 282, 636]):
        print(f"  win {w}: C={I.C[w]*QL.US:.2f}  rejected-load all={Lall_rej[w]:.2f}  big-offset rejected={Lbig[w]:.2f}")
    # day-1 instance: episodes touching > 8MB, their Baleen labels and scores
    I1 = QL.Inst(f"{X}/common/inst/day1_{region}_s0.npz")
    xb = I1.baleen_x()
    endmax = np.maximum.reduceat(I1.acc_meta[:, 4], I1.acc_start[:-1])
    bige = endmax > 8 * MB
    sc = I1.sts / np.maximum(I1.s, 1e-9)
    rows1 = I1.acc_row == 1
    bigrow = (I1.acc_meta[:, 4] > 8 * MB) & rows1
    print(f"  day1: episodes with end>8MB: {bige.sum()} of {I1.n}; Baleen-positive {int(xb[bige].sum())}; their DT share {I1.sts[bige].sum()/I1.sts.sum():.3f}, "
          f"s share {I1.s[bige].sum()/I1.s.sum():.3f}; training rows with end>8MB: {bigrow.sum()} of {rows1.sum()}, positive under Baleen: {int(xb[I1.acc_ep[bigrow]].sum())}")
    print("  day1 big episodes: median DT/size", np.median(sc[bige]) if bige.any() else None, " Baleen cutoff score", sc[xb > 0].min())
    # full trace: same stats per day
    endmax_f = np.maximum.reduceat(I.acc_meta[:, 4], I.acc_start[:-1])
    bigf = endmax_f > 8 * MB
    day = ((I.ts0 - I.t0) // 86400).astype(int)
    print("  full trace big episodes per day:", np.bincount(day[bigf], minlength=7), " DT share per day:",
          np.round([I.sts[bigf & (day == d)].sum() / max(I.sts[day == d].sum(), 1e-9) for d in range(7)], 3))
