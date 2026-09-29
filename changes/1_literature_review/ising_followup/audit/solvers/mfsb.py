"""Matrix-free ballistic Simulated Bifurcation (Goto et al., Sci. Adv. 2021, bSB) in PyTorch.

QUBO  E(x) = x^T Q x + c^T x + k,  Q = D A D^T + P s s^T  (never materialized; A = diag(alpha)).
x = (1 + sigma)/2  =>
  x^T Q x = 1/4 [ 1^T Q 1 + 2 (Q 1)^T sigma + sigma^T Q_off sigma + tr Q ]      (sigma_i^2 = 1)
  c^T x   = 1/2 c^T 1 + 1/2 c^T sigma
Ising form  E(sigma) = -1/2 sigma^T J sigma - h^T sigma + e0  with
  J  = -1/2 Q_off            (zero diagonal)
  h  = -1/2 (Q 1 + c)
  e0 = 1/4 1^T Q 1 + 1/4 tr Q + 1/2 c^T 1 + k
Local field  J y + h = -1/2 (Q y - diag(Q) * y) + h,  Q y = D (alpha * (D^T y)) + P s (s^T y).
"""
import math
import numpy as np
import torch


class MFIsing:
    def __init__(self, qp, dtype=torch.float32):
        D = qp.D.tocsr()
        self.n = qp.n
        self.dtype = dtype
        self.Dt = torch.sparse_csr_tensor(torch.from_numpy(D.indptr.astype(np.int64)),
                                          torch.from_numpy(D.indices.astype(np.int64)),
                                          torch.from_numpy(D.data.astype(np.float64)).to(dtype),
                                          size=D.shape)
        DT = D.T.tocsr()
        self.DTt = torch.sparse_csr_tensor(torch.from_numpy(DT.indptr.astype(np.int64)),
                                           torch.from_numpy(DT.indices.astype(np.int64)),
                                           torch.from_numpy(DT.data.astype(np.float64)).to(dtype),
                                           size=DT.shape)
        t = lambda a: torch.as_tensor(np.asarray(a, float), dtype=dtype)
        # banded structure: episode e covers windows start_e .. start_e+len_e-1 -> gather form of D @ Z
        inst = qp.inst
        self.m = inst["m"]
        self.gidx = [torch.as_tensor(np.minimum(inst["start"] + k, self.m - 1)) for k in range(3)]
        self.gval = [torch.as_tensor(np.where(k < inst["length"], inst["vals"][:, k], 0.0), dtype=dtype)[:, None]
                     for k in range(3)]
        self.alpha = t(qp.alpha)
        self.s = t(qp.s)
        self.P = float(qp.P)
        c = qp.linear()
        dQ = qp.diagQ()
        one = np.ones(qp.n)
        Q1 = qp.D @ (qp.alpha * (qp.D.T @ one)) + qp.P * qp.s * qp.s.sum()
        self.diagQ = t(dQ)
        self.h = t(-0.5 * (Q1 + c))
        self.e0 = 0.25 * float(one @ Q1) + 0.25 * float(dQ.sum()) + 0.5 * float(c.sum()) + qp.const()
        # ||J||_F^2 = 1/4 (||Q||_F^2 - sum diag^2), ||Q||_F^2 = tr(A M A M) + 2P u^T A u + P^2 (s.s)^2
        Mm = (qp.D.T @ qp.D).toarray()
        AM = qp.alpha[:, None] * Mm
        u = qp.D.T @ qp.s
        QF2 = float(np.trace(AM @ AM)) + 2 * qp.P * float(u @ (qp.alpha * u)) + qp.P ** 2 * float(qp.s @ qp.s) ** 2
        self.JF2 = max(0.25 * (QF2 - float((dQ ** 2).sum())), 1e-30)
        self.hF2 = float((self.h.double() ** 2).sum())

    def Qmul(self, Y):
        Z = self.DTt @ Y                      # (m, k)  sparse
        Z = self.alpha[:, None] * Z
        out = self.gval[0] * Z[self.gidx[0]]  # (n, k) = D @ Z via 3 banded gathers
        out.addcmul_(self.gval[1], Z[self.gidx[1]])
        out.addcmul_(self.gval[2], Z[self.gidx[2]])
        if self.P:
            out = out + self.P * self.s[:, None] * (self.s @ Y)[None, :]
        return out

    def field(self, Y):
        F = self.Qmul(Y)
        F.addcmul_(self.diagQ[:, None], Y, value=-1.0)
        F.mul_(-0.5).add_(self.h[:, None])
        return F

    def energy(self, S):
        """Ising energy of spins S (n,k)."""
        return -0.5 * (S * (-0.5 * (self.Qmul(S) - self.diagQ[:, None] * S))).sum(0) - self.h @ S + self.e0


def bsb(ising, agents=64, steps=2000, dt=1.25, a0=1.0, xi_scale=0.7, seed=0, heated=False):
    """Ballistic SB. Returns spins (n, agents) in {-1,+1}."""
    g = torch.Generator().manual_seed(int(seed))
    n = ising.n
    X = (torch.rand(n, agents, generator=g, dtype=ising.dtype) - 0.5) * 0.2
    Y = (torch.rand(n, agents, generator=g, dtype=ising.dtype) - 0.5) * 0.2
    # xi0 = 0.7 sqrt(N-1)/||J||_F (Goto 2021), with h folded in as an extra spin
    xi0 = xi_scale * math.sqrt(max(n, 1)) / math.sqrt(ising.JF2 + 2 * ising.hF2)
    for k in range(steps):
        at = a0 * k / steps
        F = ising.field(X)
        Y.add_(F, alpha=xi0 * dt).add_(X, alpha=-(a0 - at) * dt)
        X.add_(Y, alpha=a0 * dt)
        wall = X.abs() > 1
        X.clamp_(-1.0, 1.0)
        Y.masked_fill_(wall, 0.0)
    S = torch.where(X >= 0, 1.0, -1.0).to(ising.dtype)
    return S


def make_inner(agents=64, steps=2000, dt=1.25, xi_scale=0.7, seed=0, dtype=torch.float32):
    def inner(qp, call_idx):
        ising = MFIsing(qp, dtype=dtype)
        S = bsb(ising, agents=agents, steps=steps, dt=dt, xi_scale=xi_scale, seed=seed * 1000 + call_idx)
        X = ((S.double().numpy() + 1) / 2)
        x, _ = qp.best_of(X)
        return x
    return inner


def verify(qp, trials=8, seed=0):
    """Check Ising(sigma) == explicit QUBO(x) on random x; returns max relative error."""
    rng = np.random.default_rng(seed)
    Q = qp.dense_Q(np.float64)
    c, k = qp.linear(), qp.const()
    ising = MFIsing(qp, dtype=torch.float64)
    errs = []
    for tr in range(trials):
        x = (rng.random(qp.n) < rng.uniform(0.02, 0.6)).astype(float)
        Eq = x @ Q @ x + c @ x + k
        S = torch.from_numpy(2 * x - 1)[:, None]
        Ei = float(ising.energy(S)[0])
        Ef = float(qp.energy(x))
        errs.append(max(abs(Ei - Eq), abs(Ef - Eq)) / max(abs(Eq), 1e-12))
    return max(errs)
