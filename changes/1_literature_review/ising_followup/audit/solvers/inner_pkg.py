"""Inner QUBO solvers from packages; each returns the best-surrogate-energy binary sample."""
import numpy as np
import scipy.sparse as sp


# ---------- 4a: simulated-bifurcation package on the DENSE Q ----------
def make_sb(mode="ballistic", agents=64, steps=2000, seed=0, dtype="float32"):
    import torch
    import simulated_bifurcation as sb

    def inner(qp, call_idx):
        torch.manual_seed(seed * 1000 + call_idx)
        dt = torch.float32 if dtype == "float32" else torch.float64
        Q = torch.from_numpy(qp.dense_Q(np.float32 if dtype == "float32" else np.float64))
        c = torch.as_tensor(qp.linear(), dtype=dt)
        vecs, vals = sb.minimize(Q, c, qp.const(), domain="binary", dtype=dt, agents=agents,
                                 max_steps=steps, mode=mode, best_only=False, verbose=False,
                                 early_stopping=True)
        del Q
        X = vecs.double().numpy().T  # sb returns (agents, n)
        if X.shape[0] != qp.n:
            X = X.T
        x, _ = qp.best_of(X)
        return x
    return inner


# ---------- dimod BQM from the sparse Q ----------
def to_bqm(qp):
    import dimod
    Qs = qp.sparse_Q()
    lin = qp.linear() + Qs.diagonal()
    U = sp.triu(Qs, k=1).tocoo()
    return dimod.BinaryQuadraticModel.from_numpy_vectors(lin, (U.row, U.col, 2.0 * U.data),
                                                         qp.const(), dimod.BINARY)


def _samples_to_X(ss, n):
    rec = ss.record.sample  # (k, nv) ordered like ss.variables
    var = np.asarray(list(ss.variables))
    X = np.zeros((n, rec.shape[0]))
    X[var, :] = rec.T
    return X


# ---------- 4b: dwave-samplers SA / Tabu ----------
def make_dwave_sa(num_reads=16, num_sweeps=1000, seed=0):
    from dwave.samplers import SimulatedAnnealingSampler

    def inner(qp, call_idx):
        bqm = to_bqm(qp)
        ss = SimulatedAnnealingSampler().sample(bqm, num_reads=num_reads, num_sweeps=num_sweeps,
                                                seed=seed * 1000 + call_idx)
        x, _ = qp.best_of(_samples_to_X(ss, qp.n))
        return x
    return inner


def make_dwave_tabu(num_reads=4, timeout_ms=2000, seed=0):
    from dwave.samplers import TabuSampler

    def inner(qp, call_idx):
        bqm = to_bqm(qp)
        ss = TabuSampler().sample(bqm, num_reads=num_reads, timeout=timeout_ms, seed=seed * 1000 + call_idx)
        x, _ = qp.best_of(_samples_to_X(ss, qp.n))
        return x
    return inner


# ---------- 4c: openjij SA ----------
def make_openjij(num_reads=16, num_sweeps=1000, seed=0):
    import openjij as oj

    def inner(qp, call_idx):
        bqm = to_bqm(qp)
        ss = oj.SASampler().sample(bqm, num_reads=num_reads, num_sweeps=num_sweeps,
                                   seed=seed * 1000 + call_idx)
        x, _ = qp.best_of(_samples_to_X(ss, qp.n))
        return x
    return inner


# ---------- 4d: cim-optimizer (extAHC because h != 0) ----------
def make_cim(num_runs=8, timesteps=2000, seed=0, scheme="extAHC"):
    from cim_optimizer.solve_Ising import Ising

    def inner(qp, call_idx):
        np.random.seed(seed * 1000 + call_idx)
        import torch
        torch.manual_seed(seed * 1000 + call_idx)
        Q = qp.dense_Q(np.float64)
        dQ = np.diag(Q).copy()
        Q1 = Q.sum(1)
        c = qp.linear()
        np.fill_diagonal(Q, 0.0)
        J = -0.5 * Q  # zero diag, symmetric; cim minimizes -sum_{i<j} J s s - h s = -1/2 s^T J s - h s
        del Q
        h = -0.5 * (Q1 + c)
        scale = max(np.abs(J).max(), np.abs(h).max(), 1e-30)
        kw = dict(num_runs=num_runs, num_timesteps_per_run=timesteps, hyperparameters_randomtune=False,
                  suppress_statements=True, use_GPU=False, return_spin_trajectories_all_runs=False,
                  return_lowest_energies_found_spin_configuration=True, return_number_of_solutions=num_runs,
                  chosen_device=torch.device("cpu"))
        kw["num_parallel_runs"] = num_runs
        res = Ising(J / scale, h / scale).solve(**kw)
        S = np.asarray(res.result["spin_config_all_runs"], float).reshape(-1, qp.n).T  # (n, runs)
        X = (np.sign(S) + 1) / 2
        X[S == 0] = 0
        x, _ = qp.best_of(X)
        return x
    return inner
