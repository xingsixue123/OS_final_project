"""Q3 formulation builder (Track A -> Track B): the exact energy used by q3/src/q3solve.py (PT candidate), rebuilt
from an instance .npz + a config dict, with an energy evaluator, a feasibility check and a MILP-ready export.

  from q3form import build, energy
  F = build("common/inst/day1_Region7_s0.npz", cfg)       # cfg = the final Q3 config's solver args (Q3_FORMULATION.md)
  E, parts = energy(F, x_units)                           # x_units: 0/1 over F["units"]

Problem (binary units u = episodes, or feature cells if cfg["cells"] != "ep"; all terms in utilisation-% points):
  min_x  E(x) = A * F_peak(L(x)) + sum_u lin_u x_u + lam_c * sum_{(u,v) in G} |x_u - x_v| + const
  s.t.   sum_u s_u x_u <= Bc          (Bc = f * B, B = harness label budget in chunks)
  L_w(x) = C_w - sum_u D_uw x_u       (w over the instance's active windows, optional temporal aggregation)
  F_peak = LSE_gamma(L) = max L + log(sum_w exp(gamma (L_w - max L))) / gamma   (peak = "lse")
         | mean of the top-k L_w                                                  (peak = "topk")
  lin_u = -beta * sts_u * US / m  +  mu / |S_B| * (n_u - 2 b_u)  -  beta_pw * sum_w D_uw phi_w / m
  (b_u = #episodes of u in Baleen's selection S_B, n_u = #episodes of u, phi_w = normalized (C_w/mean C)^pw)
MILP form (classical solvers): with peak = "max" the problem is linear: min A z + lin.x + lam_c sum_e t_e
  s.t. z >= C_w - (D^T x)_w, t_e >= x_u - x_v, t_e >= x_v - x_u, s.x <= Bc, x binary. (LSE/top-k: see Q3_FORMULATION.md)
Units -> labels: episode e is selected iff its unit is; labels = selection + harness strict-prefix fill in Baleen order.
"""
import math
import os
import sys

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "q3", "src"))
import q3lib as QL  # noqa: E402
from q3solve import episode_cells, knn_graph  # noqa: E402

US = QL.US


def build(inst_path, a):
    I = QL.Inst(inst_path)
    I.active = np.ones(I.m, bool) if a.get("all_windows", True) else I.active
    spec = a.get("cells", "ep")
    cid = episode_cells(I, spec)
    K = int(cid.max()) + 1
    E = sp.csr_matrix((np.ones(I.n), (cid, np.arange(I.n))), shape=(K, I.n))
    Dw = I.D[:, I.active]
    Cw = I.C[I.active]
    agg = int(a.get("win_agg", 1))
    if agg > 1:
        m0 = Dw.shape[1]
        grp = np.arange(m0) // agg
        G = sp.csr_matrix((np.ones(m0) / agg, (np.arange(m0), grp)), shape=(m0, grp.max() + 1))
        Dw = (Dw @ G).tocsr()
        Cw = np.asarray(G.T @ Cw).ravel()
    Du = (E @ Dw).tocsr() * US
    Cu = Cw * US
    m = Du.shape[1]
    su = np.asarray(E @ I.s).ravel()
    stsu = np.asarray(E @ I.sts).ravel()
    xb = I.baleen_x()
    bu = np.asarray(E @ xb).ravel()
    nu = np.asarray(E @ np.ones(I.n)).ravel()
    SB = max(float(xb.sum()), 1.0)
    beta, mu, lam = float(a.get("beta", 0.0)), float(a.get("mu", 0.0)), float(a.get("lam", 0.0))
    lin = -beta * stsu * US / m + mu / SB * ((nu - bu) - bu)
    bpw = float(a.get("beta_pw", 0.0))
    if bpw > 0:
        phi = (Cu / max(float(Cu.mean()), 1e-12)) ** float(a.get("pw", 2.0))
        phi = phi / max(float(phi.mean()), 1e-12)
        lin = lin - bpw * np.asarray(Du @ phi).ravel() / m
    const = mu / SB * bu.sum()
    edges = np.zeros((0, 2), np.int64)
    lam_c = 0.0
    if lam > 0 and spec == "ep":
        Gk = sp.triu(knn_graph(I, k=int(a.get("knn", 5))), k=1).tocoo()
        edges = np.c_[Gk.row, Gk.col].astype(np.int64)
        lam_c = lam / max(len(edges), 1)
    return dict(inst=inst_path, cfg=dict(a), units=K, cell_of_episode=cid, D=Du, C=Cu, s=su, Bc=float(a.get("f", 1.0)) * I.B,
                B=I.B, lin=lin, const=const, edges=edges, lam_c=lam_c, A=float(a.get("A", 1.0)),
                peak=a.get("peak", "lse"), gamma=float(a.get("gamma", 2.0)), topk=int(a.get("topk", 5)),
                baleen_units=(bu >= 0.5 * nu).astype(float) if spec != "ep" else xb, m=m)


def peak_term(F, L):
    if F["peak"] == "lse":
        g = F["gamma"]
        mx = L.max()
        return mx + math.log(np.exp(g * (L - mx)).sum()) / g
    if F["peak"] == "topk":
        return float(np.sort(L)[::-1][:F["topk"]].mean())
    return float(L.max())


def energy(F, x):
    x = np.asarray(x, float)
    L = F["C"] - F["D"].T @ x
    pk = F["A"] * peak_term(F, L)
    ln = float(F["lin"] @ x)
    cons = F["lam_c"] * float(np.abs(x[F["edges"][:, 0]] - x[F["edges"][:, 1]]).sum()) if len(F["edges"]) else 0.0
    feas = float(F["s"] @ x) <= F["Bc"] + 1e-6
    return pk + ln + cons + F["const"], dict(peak_term=pk, linear=ln, consistency=cons, const=F["const"],
                                             peak_util=float(L.max()), feasible=feas, use=float(F["s"] @ x))


def save(F, path):
    D = F["D"].tocsr()
    np.savez_compressed(path, D_data=D.data, D_indices=D.indices, D_indptr=D.indptr, D_shape=np.asarray(D.shape),
                        C=F["C"], s=F["s"], Bc=F["Bc"], B=F["B"], lin=F["lin"], const=F["const"], edges=F["edges"],
                        lam_c=F["lam_c"], A=F["A"], peak=F["peak"], gamma=F["gamma"], topk=F["topk"],
                        cell_of_episode=F["cell_of_episode"], baleen_units=F["baleen_units"])


if __name__ == "__main__":
    import json
    inst, cfg, out = sys.argv[1], json.loads(sys.argv[2]), sys.argv[3]
    F = build(inst, cfg)
    save(F, out)
    E0, parts = energy(F, F["baleen_units"])
    print(f"units={F['units']} windows={F['m']} Bc={F['Bc']:.0f} edges={len(F['edges'])} E(Baleen)={E0:.4f} {parts}")
