"""Synthetic peak-aware admission instance, shaped like the Baleen admission problem.

m = 144 ten-minute windows (one trace-day). n episodes; episode e spans len_e in {1,2,3}
consecutive windows starting at start_e. d[e,w] > 0 = backend-load saving in window w if
admitted; s_e = bytes written (flash-write cost). Baseline load C_w (diurnal, peak/mean ~= 2,
C_w >= 1.5 * sum_e d[e,w]). Budget W = bytes of the greedy savings/byte prefix that admits
6% of episodes. Loads after admission: L = C - D^T x; objective min max_w L_w, s^T x <= W.
"""
import numpy as np
import scipy.sparse as sp

M = 144


def diurnal_shape(m=M, target_p2m=2.0):
    t = np.arange(m)
    bump = np.exp(-0.5 * ((t - 84) / 16.0) ** 2) + 0.45 * np.exp(-0.5 * ((t - 56) / 9.0) ** 2) \
        + 0.15 * np.exp(-0.5 * ((t - 126) / 8.0) ** 2)
    lo, hi = 1e-3, 10.0  # bisect a constant base so that max/mean == target
    for _ in range(100):
        b = 0.5 * (lo + hi)
        sh = b + bump
        if sh.max() / sh.mean() > target_p2m:
            lo = b
        else:
            hi = b
    sh = b + bump
    return sh / sh.max()


def make_instance(n, seed, m=M, admit_frac=0.06, busy_bias=0.8):
    rng = np.random.default_rng(seed)
    shape = diurnal_shape(m)
    # episode lengths / starts: mixture of uniform and busy-hour-biased starts
    length = rng.choice([1, 2, 3], size=n, p=[0.4, 0.35, 0.25])
    p_start = (1 - busy_bias) / m + busy_bias * shape / shape.sum()
    start = rng.choice(m, size=n, p=p_start)
    start = np.minimum(start, m - length)
    # heavy-tailed savings: episode-level factor x per-window factor
    ep_scale = rng.lognormal(0.0, 1.2, size=n)
    vals = np.zeros((n, 3))
    for k in range(3):
        vals[:, k] = np.where(k < length, ep_scale * rng.lognormal(0.0, 0.5, size=n), 0.0)
    total = vals.sum(1)
    # write cost positively correlated with total savings (corr in log space ~0.7)
    s = total ** 0.8 * rng.lognormal(0.0, 0.7, size=n)
    s = s / s.mean()
    rows = np.repeat(np.arange(n), length)
    cols = np.concatenate([np.arange(st, st + L) for st, L in zip(start, length)]) if n else np.array([])
    data = vals[vals > 0]  # row-major order matches rows/cols construction
    D = sp.csr_matrix((data, (rows, cols)), shape=(n, m))
    S_w = np.asarray(D.sum(0)).ravel()
    K = 1.5 * np.max(S_w / shape)
    C = K * shape
    # normalize so that max C == 1
    D = D / C.max()
    D = D.tocsr()
    vals = vals / C.max()
    C = C / C.max()
    # budget: greedy savings/byte prefix admitting admit_frac of episodes
    ratio = np.asarray(D.sum(1)).ravel() / s
    order = np.argsort(-ratio, kind="stable")
    k = int(round(admit_frac * n))
    W = float(s[order[:k]].sum())
    return dict(n=n, m=m, seed=seed, D=D, Dcsc=D.tocsc(), start=start.astype(np.int64),
                length=length.astype(np.int64), vals=vals, s=s, C=C, W=W, shape=shape)


def loads(inst, x):
    return inst["C"] - inst["D"].T @ x


def peak(inst, x):
    return float(loads(inst, x).max())


def usage(inst, x):
    return float(inst["s"] @ x / inst["W"])


if __name__ == "__main__":
    for n in [1000, 10000, 50000, 200000]:
        inst = make_instance(n, 0)
        D = inst["D"]
        S_w = np.asarray(D.sum(0)).ravel()
        tot = np.asarray(D.sum(1)).ravel()
        print(n, "nnz", D.nnz, "p2m", inst["C"].max() / inst["C"].mean(),
              "min C/S", (inst["C"] / S_w).min(), "corr(log s, log T)",
              np.corrcoef(np.log(inst["s"]), np.log(tot))[0, 1], "W", inst["W"],
              "W/sum s", inst["W"] / inst["s"].sum())
        # Q nnz estimate: sum over windows of count^2
        cnt = np.asarray((D > 0).sum(0)).ravel()
        print("   est Q nnz (upper bound)", int((cnt.astype(float) ** 2).sum()))
