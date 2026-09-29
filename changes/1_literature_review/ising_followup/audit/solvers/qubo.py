"""QUBO surrogate + shared Lagrangian outer loop.

E(x) = sum_w alpha_w (r_w - (D^T x)_w)^2 + mu s^T x  [+ P (s^T x - W)^2 in penalty mode],  r_w = C_w - tau
     = x^T Q x + c^T x + const,   Q = D diag(alpha) D^T (+ P s s^T)   (n x n, incl. diagonal)
       c = -2 D (alpha*r) + mu s (- 2 P W s),  const = sum alpha r^2 (+ P W^2)
The inner solver only changes; outer loop, repair and evaluation are identical for all.
"""
import time
import numpy as np
import scipy.sparse as sp
from .common import greedy, repair, evaluate


class QP:
    def __init__(self, inst, alpha, tau, mu, P=0.0):
        self.inst = inst
        self.D = inst["D"]
        self.s = inst["s"]
        self.W = inst["W"]
        self.alpha = np.asarray(alpha, float)
        self.tau = float(tau)
        self.r = inst["C"] - tau
        self.mu = float(mu)
        self.P = float(P)
        self.n = inst["n"]
        self._Qs = None

    # ---- explicit pieces ----
    def linear(self):
        c = -2.0 * (self.D @ (self.alpha * self.r)) + self.mu * self.s
        if self.P:
            c = c - 2.0 * self.P * self.W * self.s
        return c

    def const(self):
        return float((self.alpha * self.r ** 2).sum() + self.P * self.W ** 2)

    def diagQ(self):
        return np.asarray(self.D.multiply(self.D) @ self.alpha).ravel() + self.P * self.s ** 2

    def sparse_Q(self):
        """Q (without P term) as scipy CSR, symmetric incl. diagonal."""
        if self._Qs is None:
            Da = self.D.multiply(np.sqrt(self.alpha)[None, :]).tocsr()
            self._Qs = (Da @ Da.T).tocsr()
        return self._Qs

    def dense_Q(self, dtype=np.float32):
        Q = self.sparse_Q().toarray().astype(dtype, copy=False)
        if self.P:
            Q += (self.P * np.outer(self.s, self.s)).astype(dtype)
        return Q

    # ---- energies (matrix-free, exact) ----
    def energy(self, X):
        """X: (n,) or (n,k) binary. Returns E per column."""
        X = np.asarray(X, float)
        one = X.ndim == 1
        if one:
            X = X[:, None]
        R = self.r[:, None] - self.D.T @ X
        E = (self.alpha[:, None] * R ** 2).sum(0) + self.mu * (self.s @ X)
        if self.P:
            E = E + self.P * (self.s @ X - self.W) ** 2
        return E[0] if one else E

    def best_of(self, X):
        """X (n,k) binary -> best column by surrogate energy."""
        E = self.energy(X)
        j = int(np.argmin(E))
        return X[:, j].astype(float), float(E[j])


def mu_max(inst, alpha, tau):
    """mu above which no single episode has negative marginal energy."""
    qp = QP(inst, alpha, tau, 0.0)
    benefit = -(qp.linear() + qp.diagQ())
    return max(float(np.max(benefit / inst["s"])), 1e-12)


def outer_loop(inst, inner, max_outer=10, beta=8.0, delta_frac=0.003, time_cap=900.0,
               bisect_first=8, bisect_later=4, max_calls=40, tol=(0.95, 1.0), log=None, penalty_P=None):
    """Lagrangian outer loop (identical for every inner solver).
    inner(qp, call_idx) -> binary x (n,) (best-energy sample of the inner solver)."""
    t0 = time.time()
    xg = greedy(inst)
    xg_r, _ = repair(inst, xg)
    greedy_peak = evaluate(inst, xg_r)["peak"]
    best = dict(peak=np.inf, x_raw=None, x_rep=None, it=-1)   # best SOLVER iterate (greedy only seeds alpha/tau)
    L = inst["C"] - inst["D"].T @ xg_r
    alpha = np.clip(np.exp(beta * (L / L.max() - 1.0)), 1e-3, 1.0)
    delta = delta_frac * greedy_peak
    tau = greedy_peak - delta
    calls = 0
    hist = []
    mu_prev = None
    inner_time = 0.0
    P_abs = None
    for it in range(max_outer):
        if time.time() - t0 > time_cap or calls >= max_calls:
            break
        mmax = mu_max(inst, alpha, tau)
        if penalty_P is not None:
            # penalty_P is a multiplier k: P = k * mu_max(first iter) / W, so the penalty's
            # gradient at x=0 (-2 P W s) is 2k x the Lagrangian scale mu_max * s
            if P_abs is None:
                P_abs = penalty_P * mmax / inst["W"]
            lo = hi = 0.0
            nb = 1
        elif mu_prev is None:
            lo, hi, nb = mmax * 1e-4, mmax, bisect_first
        else:
            lo, hi, nb = mu_prev / 4, mu_prev * 4, bisect_later
        cands = []
        for k in range(nb):
            if time.time() - t0 > time_cap or calls >= max_calls:
                break
            mu = np.sqrt(lo * hi)
            qp = QP(inst, alpha, tau, mu, P=(P_abs or 0.0))
            ti = time.time()
            x = np.nan_to_num(np.asarray(inner(qp, calls), float), nan=0.0)
            inner_time += time.time() - ti
            calls += 1
            u = float(inst["s"] @ x / inst["W"])
            cands.append((mu, u, x))
            if u > 1.0:
                lo = mu
            else:
                hi = mu
            if tol[0] <= u <= tol[1]:
                break
        if not cands:
            break
        # evaluate all candidates of this outer iteration through the shared repair
        it_best = None
        for mu, u, x in cands:
            xr, rinfo = repair(inst, x)
            pk = evaluate(inst, xr)["peak"]
            if it_best is None or pk < it_best[0]:
                it_best = (pk, mu, u, x, xr)
        pk, mu, u, x, xr = it_best
        mu_prev = mu
        hist.append(dict(it=it, mu=mu, use_raw=u, peak_rep=pk, tau=tau, calls=calls,
                         t=time.time() - t0))
        if log:
            log(f"it={it} mu={mu:.4g} use_raw={u:.3f} peak_rep={pk:.5f} best={min(pk, best['peak']):.5f} greedy={greedy_peak:.5f} tau={tau:.5f} calls={calls} t={time.time()-t0:.1f}")
        if pk < best["peak"]:
            best = dict(peak=pk, x_raw=x, x_rep=xr, it=it, mu=mu)
        Lc = inst["C"] - inst["D"].T @ xr
        alpha = np.clip(np.exp(beta * (Lc / Lc.max() - 1.0)), 1e-3, 1.0)
        tau = min(best["peak"], greedy_peak) - delta
    return best, hist, dict(calls=calls, inner_time=inner_time, total_time=time.time() - t0,
                            P_abs=P_abs, outer_iters=len(hist), greedy_peak=greedy_peak)
