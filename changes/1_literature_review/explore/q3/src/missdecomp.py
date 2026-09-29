import sys, os
import numpy as np, pandas as pd, lightgbm as lgb
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import q3lib as QL
X = os.environ["X_ROOT"]; H = os.path.normpath(os.path.join(X, "..", "harness_eval")); MB = 1 << 20
dep = pd.read_csv(f"{H}/results/deployed.csv")
for region, wins in [("Region7", [646, 660, 613, 282, 636, 674]), ("Region6", [712, 152, 816, 806, 807, 817])]:
    I = QL.Inst(f"{X}/common/inst/fullml_{region}_s0.npz")
    F = QL.sim_features(I, cache=f"{X}/q3/work/cache/simfeat_fullml_{region}_s0.npz").astype(float)
    log = open(f"{H}/work/logs/dep/dep_{region}_R0_rep1/train.log").read().splitlines()
    mp = [l.split(" ")[1] for l in log if l.startswith("model_admit_threshold_binary ") and l.endswith("M")][0]
    g = lgb.Booster(model_file=f"{H}/work/{mp}").predict(F)
    th = float(dep[(dep.region == region) & (dep.name == "R0")].threshold.iloc[0])
    rej = g <= th
    load = QL.st(1, I.acc_nch) * QL.US
    cat = np.full(I.n_acc, "other", object)
    cat[I.acc_meta[:, 0] == 5] = "op5"
    cat[(F[:, 4] > 8 * MB)] = "bigoff"
    cat[(I.acc_k <= 1)] = "k<=1"
    # later accesses of episodes that never pass the threshold
    kst = QL.first_admit(I, g > th)
    never = kst[I.acc_ep] < 0
    rows = []
    for w in wins:
        a = I.acc_w == w
        r = dict(win=w, C=load[a].sum())
        for c in ["k<=1", "bigoff", "op5", "other"]:
            r["rej_" + c] = load[a & rej & (cat == c)].sum()
        r["rej_never_admitted_ep"] = load[a & rej & never].sum()
        r["acc_rej_frac"] = (a & rej).sum() / max(a.sum(), 1)
        rows.append(r)
    print(region, "threshold", th); print(pd.DataFrame(rows).round(2).to_string(index=False))
