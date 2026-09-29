"""MindQuantum QAIA inner solvers (BSB / DSB / CAC), CPU backend.
Same Ising form as mfsb.py:  E = -1/2 s^T J s - h^T s + e0, J = -1/2 Q_off, h = -1/2 (Q 1 + c).
explicit: J passed as scipy CSR (nnz = nnz(Q_off));  matrix-free: after construction the solver's
J is swapped for an operator whose .dot / @ computes -1/2 (D (alpha * (D^T y)) - diag(Q) * y)."""
import numpy as np
import scipy.sparse as sp


class MFJ:
    def __init__(self, qp):
        self.D = qp.D.tocsr().astype(np.float32)
        self.DT = qp.D.T.tocsr().astype(np.float32)
        self.alpha = qp.alpha.astype(np.float32)[:, None]
        self.dQ = qp.diagQ().astype(np.float32)[:, None]
        self.shape = (qp.n, qp.n)

    def dot(self, Y):
        Y = np.asarray(Y)
        if Y.ndim == 1:
            return self.dot(Y[:, None])[:, 0]
        return -0.5 * (self.D @ (self.alpha * (self.DT @ Y)) - self.dQ * Y)

    __matmul__ = dot


def ising_terms(qp, matrix_free=False):
    if matrix_free:  # never build Q: diag(Q) and Q 1 via D
        Qs = None
        dQ = qp.diagQ()
        Q1 = qp.D @ (qp.alpha * (qp.D.T @ np.ones(qp.n)))
    else:
        Qs = qp.sparse_Q()
        dQ = Qs.diagonal()
        Q1 = np.asarray(Qs.sum(1)).ravel()
    h = -0.5 * (Q1 + qp.linear())
    return Qs, dQ, h


def make_mq(algo="BSB", matrix_free=False, batch=32, n_iter=1000, seed=0):
    from mindquantum.algorithm.qaia import BSB, DSB, CAC

    def inner(qp, call_idx):
        np.random.seed(seed * 1000 + call_idx)
        Qs, dQ, h = ising_terms(qp, matrix_free)
        n = qp.n
        if matrix_free:
            op = MFJ(qp)
            # ||J||_F^2 from the explicit Q is only used for the step constant; compute it
            # matrix-free via the m x m Gram: ||Q||_F^2 = tr(A M A M)
            M = (qp.D.T @ qp.D).toarray()
            AM = qp.alpha[:, None] * M
            JF2 = 0.25 * (np.trace(AM @ AM) - (dQ ** 2).sum())
            J0 = sp.csr_matrix((n, n))
        else:
            J = (-0.5 * (Qs - sp.diags(dQ))).tocsr()
            J.eliminate_zeros()
            J = J.astype(np.float32)
            JF2 = float(J.power(2).sum())
            J0 = J
        hh = h.astype(np.float32)
        if algo in ("BSB", "DSB"):
            xi = 0.5 * np.sqrt(n - 1) / np.sqrt(JF2 + 2 * ((hh / 2) ** 2).sum())  # MQ default formula
            cls = BSB if algo == "BSB" else DSB
            solver = cls(J0, hh, batch_size=batch, n_iter=n_iter, xi=float(xi))
        else:
            if matrix_free:
                # CAC's __init__ computes xi from J; build with a 1-entry dummy then overwrite
                Jd = sp.csr_matrix(([1e-30, 1e-30], ([0, 1], [1, 0])), shape=(n, n))
                solver = CAC(Jd, hh, batch_size=batch, n_iter=n_iter)
                # replicate MQ's CPU formula exactly: np.sum(J**2) on a scipy matrix is sum(J @ J)
                # = ||J 1||^2 (J symmetric)
                v = op.dot(np.ones(n, np.float32))
                solver.xi = np.sqrt(2 * n / float(v @ v))
            else:
                solver = CAC(J0, hh, batch_size=batch, n_iter=n_iter)
        if matrix_free:
            solver.J = op
        solver.update()
        S = np.sign(np.asarray(solver.x, float))
        S[~np.isfinite(S)] = -1  # diverged (NaN/inf) amplitudes -> not admitted
        S[S == 0] = 1
        X = (S + 1) / 2
        x, _ = qp.best_of(X)
        return x
    return inner
