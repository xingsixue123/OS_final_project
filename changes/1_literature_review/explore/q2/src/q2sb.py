"""Matrix-free simulated bifurcation (Ising family) on the formulation's QUBO surrogate (PyTorch CPU, 8 threads).

QUBO per round (over the model vars of the level, x in {0,1}^n):
   E(x) = sum_w alpha_w (C_w - tau_s - (D^T x)_w)^2 + mu s.x
   F2b : alpha_w = 1 on the current active set {w: L_w > tau} (IRLS on the squared hinge), tau_s = tau  -> exact on A
   F1/F2a: alpha from window duals (SAIM/ALM-style, as harness C4), tau_s = tau_frac * current objective peak
J x = D (alpha * (D^T x)) is applied matrix-free (sparse CSR matmuls); Q is never formed.
Variants: ballistic (bSB), discrete (dSB: sign(x) in the coupling), heated (HbSB/HdSB: momentum += dt*heat*y_prev).
Budget: Lagrangian price mu with ALM/subgradient update from the decoded agents; every decoded agent is repaired and
the best TRUE objective kept (the incumbent starts at the level's classical start, which SB must beat to change it).
"""
import math
import time

import numpy as np
import torch

import q2core as C


def sb_level(P, k, dl, cfg, seed, start_solution):
    torch.set_num_threads(int(cfg.get("threads", 8)))
    t0 = time.time()
    x1, info = start_solution(P, cfg.get("start", "lp"), dl, cfg, seed)
    best, bobj = x1.copy(), P.obj(x1)
    bsts = float(P.sts @ x1)
    info["sb_start_obj"] = bobj
    var = C.model_vars(P)
    if len(var) < 2 or time.time() > dl - 0.1:
        return best, info
    D = P.Da[var].tocsr()
    n, ma = D.shape
    s = P.s[var].astype(np.float64)
    ip = torch.from_numpy(D.indptr.astype(np.int64))
    Dt = torch.sparse_csr_tensor(ip, torch.from_numpy(D.indices.astype(np.int64)),
                                 torch.from_numpy(D.data.astype(np.float32)), size=(n, ma))
    DT = D.T.tocsr()
    DTt = torch.sparse_csr_tensor(torch.from_numpy(DT.indptr.astype(np.int64)),
                                  torch.from_numpy(DT.indices.astype(np.int64)),
                                  torch.from_numpy(DT.data.astype(np.float32)), size=(ma, n))
    M = (D.T @ D).toarray()
    D2 = D.multiply(D).tocsr()
    colsum = np.asarray(D.sum(0)).ravel()
    typ = P.form.typ if P.form.typ < 3 else 2
    L1 = P.loads(x1)
    pk1 = float(L1.max())
    if typ == 2:
        tau_s = P.form.tau
        alpha = (L1 > tau_s).astype(float) + float(cfg.get("sb_alpha_floor", 0.0))
    else:
        tau_s = pk1 * float(cfg.get("sb_tau_frac", 0.97))
        alpha = np.where(L1 >= tau_s, 1.0, float(cfg.get("sb_alpha_floor", 0.05)))
    mu = float(cfg.get("sb_mu0", 0.0))
    agents = int(cfg.get("sb_agents", 32))
    steps = int(cfg.get("sb_steps", 400))
    dt = float(cfg.get("sb_dt", 1.0))
    variant = cfg.get("sb_variant", "ballistic")
    heat = float(cfg.get("sb_heat", 0.06))
    xi_scale = float(cfg.get("sb_xi", 0.7))
    warm = float(cfg.get("sb_warm", 0.0))           # agents start at warm*(2x1-1) + noise
    eta = float(cfg.get("sb_eta", 0.5))
    eta_mu = float(cfg.get("sb_eta_mu", 1.0))
    g = torch.Generator().manual_seed(int(seed) * 1000 + k)
    x1v = torch.as_tensor(2.0 * x1[var] - 1.0, dtype=torch.float32)[:, None]
    rounds = 0
    improved = 0
    decoded = 0
    while time.time() < dl - 0.05:
        rounds += 1
        r = P.C - tau_s
        c = -2.0 * (D @ (alpha * r)) + mu * s
        dQ = np.asarray(D2 @ alpha).ravel()
        Q1 = D @ (alpha * colsum)
        AM = alpha[:, None] * M
        JF2 = max(0.25 * (float(np.trace(AM @ AM)) - float((dQ ** 2).sum())), 1e-30)
        h = torch.as_tensor(-0.5 * (Q1 + c), dtype=torch.float32)[:, None]
        dQt = torch.as_tensor(dQ, dtype=torch.float32)[:, None]
        al = torch.as_tensor(alpha, dtype=torch.float32)[:, None]
        hF2 = float((h.double() ** 2).sum())
        xi0 = xi_scale * math.sqrt(n) / math.sqrt(JF2 + 2 * hF2)
        Xs = (torch.rand(n, agents, generator=g) - 0.5) * 0.2 + warm * x1v
        Ys = (torch.rand(n, agents, generator=g) - 0.5) * 0.2
        a0 = 1.0
        for st in range(steps):
            if st % 32 == 0 and time.time() > dl - 0.05:
                break
            at = a0 * st / steps
            Z = torch.sign(Xs) if variant == "discrete" else Xs
            F = Dt @ (al * (DTt @ Z))
            F = -0.5 * (F - dQt * Z) + h
            if variant == "heated":
                Yprev = Ys.clone()
            Ys.add_(F, alpha=xi0 * dt).add_(Xs, alpha=-(a0 - at) * dt)
            if variant == "heated":
                Ys.add_(Yprev, alpha=dt * heat)
            Xs.add_(Ys, alpha=a0 * dt)
            wall = Xs.abs() > 1
            Xs.clamp_(-1.0, 1.0)
            Ys.masked_fill_(wall, 0.0)
        S = (Xs >= 0).double().numpy()
        objs = []
        for j in range(agents):
            if time.time() > dl - 0.02:
                break
            xf = np.zeros(P.n)
            xf[var] = S[:, j]
            xr, _ = P.repair(xf, fill=False)
            decoded += 1
            ob = P.obj(xr)
            sv = float(P.sts @ xr)
            objs.append((ob, j))
            if ob < bobj - 1e-15 or (ob <= bobj + 1e-15 and sv > bsts + 1e-9):
                best, bobj, bsts = xr, ob, sv
                improved += 1
        if not objs:
            break
        # dual updates from the median agent (raw, before repair)
        jm = sorted(objs)[len(objs) // 2][1]
        xm = np.zeros(P.n)
        xm[var] = S[:, jm]
        Lm = P.loads(xm)
        if typ == 2:
            Lb = P.loads(best)
            alpha = (Lb > tau_s).astype(float) + float(cfg.get("sb_alpha_floor", 0.0))
        else:
            alpha = np.maximum(alpha + eta * (Lm - tau_s) / max(pk1, 1e-12) * 10, 0.0)
            alpha = alpha / max(alpha.max(), 1e-12)
            alpha = np.maximum(alpha, 1e-3)
        viol = (float(P.s @ xm) - P.B) / max(P.B, 1.0)
        mu = max(0.0, mu + eta_mu * viol * float(np.abs(c).mean()) / max(float(s.mean()), 1e-12))
    info.update(sb_rounds=rounds, sb_improved=improved, sb_decoded=decoded, sb_time=time.time() - t0)
    return best, info
