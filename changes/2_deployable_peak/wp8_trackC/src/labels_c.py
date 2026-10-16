"""Track C deployment-aware Ising label designs (solver env explore/env, read-only), solved by the q2 PT solver family
(q8anneal = q2anneal + local field; pmode 'quad' = PT on the QUBO-penalised energy, the frozen F1PT 10 s configuration
of explore/q2/plan_F1.json, replica exchange, 16 replicas) on the DEV day-1 instance common/inst/day1_<inst>.npz.

Designs (name -> energy; all with the native budget s.x <= B as the QUBO penalty of the PT configuration):
  F1PT4            F1 = LSE_g(L(x)) (true min-max day-1 peak), LP start -- WP2's F1PT through this driver, 4 threads
  ANC<lam>         F1 + field h_e = (lam/US)/|S_B| * (1 - 2 b_e)  == lam util-pts per 100% of Baleen's labels flipped
                   (b = Baleen's label set; Hamming anchor), start = Baleen's set, field move p_fadd
  TK<k>            F2a = mean of the top-k day-1 window loads (CVaR_k), LP start
  ANC<lam>TK<k>    F2a + Hamming anchor
  STU<lam>R<r>     student-field alternation round r >= 1: F1 + h_e = (lam/US)/|S_prev| * (1 - 2 p_e), p_e = out-of-fold
                   GBM(+load) probability of the round r-1 labels (file from student.py), start = round r-1 core
Output (same format as wp2_deployed/src/labels.py, so pb4_policy applies it by episode identity):
  labels/<inst>_<design>_s<seed>.npz (core_keys, core_ts0, B, x_core, x_full) + .json (statistics, energy parts)
The repair (q2core shared repair: drop-to-budget, improving adds, Baleen-order non-worsening fill) is applied as in
the q2 driver; for field designs the improving-add step is disabled (max_adds = 0) so the repair cannot undo the field.
  src/run.sh solver ../src/labels_c.py --inst Region7_s0 --design ANC10 --seed 1
"""
import argparse
import json
import os
import re
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, "q2lib")]
W = os.path.dirname(HERE)
EXPLORE = os.path.normpath(os.path.join(W, "..", "..", "1_literature_review", "explore"))
INST = os.path.join(EXPLORE, "common", "inst")
LABELS = os.path.join(W, "labels")
WP2_LABELS = os.path.normpath(os.path.join(W, "..", "wp2_deployed", "labels"))
PLAN_F1 = os.path.join(EXPLORE, "q2", "plan_F1.json")
DEV = [f"{r}_s{s}" for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]
BUDGET = 10.0
THREADS = 4
US = 1.0 / 36 * (100.0 / 0.1) / 600 * 100


def pt_cfg():
    plan = json.load(open(PLAN_F1))
    for m in plan["methods"]:
        if m["solver"] == "pt":
            return dict(m["cfg_by_budget"]["10"])
    raise KeyError("pt")


def parse(design):
    d = dict(form="F1", anchor=None, k=None, student=None, rnd=None)
    if design == "F1PT4":
        return d
    m = re.fullmatch(r"ANC([\d.]+)(?:TK(\d+))?(CP)?", design)
    if m:
        d["anchor"] = float(m.group(1))
        if m.group(2):
            d.update(form="F2a", k=int(m.group(2)))
        d["cpsat"] = bool(m.group(3))
        assert not (d["cpsat"] and m.group(2)), "CP-SAT control only for the F1 anchor"
        return d
    m = re.fullmatch(r"TK(\d+)", design)
    if m:
        d.update(form="F2a", k=int(m.group(1)))
        return d
    m = re.fullmatch(r"STU([\d.]+)R(\d+)", design)
    if m:
        d.update(student=float(m.group(1)), rnd=int(m.group(2)))
        return d
    raise ValueError(design)


def baleen_x(I):
    xb = np.zeros(I.n)
    cs = np.cumsum(I.s[I.base_order])
    xb[I.base_order[cs <= I.B]] = 1.0
    return xb


def solve(inst, design, seed, student_file=None, prev_file=None, p_fadd=0.1):
    import numba
    import q2core as C
    import q2run as R
    import q8anneal as A8
    numba.set_num_threads(THREADS)
    spec = parse(design)
    cfg = pt_cfg()
    cfg["eim_pmode"] = "quad"                 # PT = q2 'pt' (QUBO penalty)
    I = C.Instance(os.path.join(INST, f"day1_{inst}.npz"))
    form = C.make_form(I, {"name": spec["form"], "k": spec["k"] or 4})
    R.warmup(I, form, "pt", cfg)
    # warm up the field kernel (not timed)
    P0 = C.Sub(I, 0.02 * I.B, np.zeros(I.n, bool), form)
    A8.eim(P0, np.zeros(P0.n), time.time() + 0.01, dict(eim_moves=200, eim_R=2, eim_pmode="quad", p_fadd=0.1),
           field=np.zeros(P0.n) - 1e-9)
    P = C.Sub(I, I.B, np.zeros(I.n, bool), form)
    xb = baleen_x(I)
    field = None
    info = dict(spec)
    if spec["anchor"] is not None:
        field = (spec["anchor"] / US) / max(xb.sum(), 1.0) * (1.0 - 2.0 * xb)
        info["field_per_flip_util"] = spec["anchor"] / max(xb.sum(), 1.0)
    if spec["student"] is not None:
        z = np.load(student_file)
        p = z["p_ep"].astype(float)
        assert len(p) == I.n
        nprev = float(np.load(prev_file)["x_core"].sum()) if prev_file else xb.sum()
        field = (spec["student"] / US) / max(nprev, 1.0) * (1.0 - 2.0 * p)
        info.update(student_file=os.path.relpath(student_file, W), field_per_flip_util=spec["student"] / max(nprev, 1.0))
    t0 = time.time()
    dl = t0 + BUDGET
    if spec.get("cpsat"):
        # CLASSICAL CONTROL: the same anchored energy (exact max + field) solved by OR-Tools CP-SAT, Baleen hint
        xs, li = cpsat_anchor(C, P, xb, field, dl, seed)
        wall_pt = time.time() - t0
        xr, st = P.repair(xs, fill=True, max_adds=0)
        x = P.full(xr)
        assert I.s @ x <= I.B + 1e-6
        order, nfill = C.final_order(I, x, np.zeros(I.n, np.int64))
        xf = np.zeros(I.n)
        xf[order] = 1.0
        info.update(start="baleen_hint", wall=time.time() - t0, wall_pt=wall_pt, threads=THREADS, budget=BUDGET,
                    solver="cpsat", **li, **{"rep_" + k: v for k, v in st.items()}, n_fill=int(nfill))
        return I, x, xf, xb, field, info
    if spec["anchor"] is not None:
        x0 = xb.copy()
        start = "baleen"
    elif spec["student"] is not None:
        x0 = np.load(prev_file)["x_core"].astype(float)
        start = "prev_round"
    else:
        import q2lp
        q2lp._THREADS[0] = THREADS
        x0, sinfo = R.start_solution(P, "lp", dl, cfg, seed)
        info.update({k: v for k, v in sinfo.items() if np.isscalar(v)})
        start = "lp"
    c2 = dict(cfg, p_fadd=p_fadd)
    xs, li = A8.eim(P, x0, dl, c2, seed=seed * 100, field=field)
    wall_pt = time.time() - t0
    xr, st = P.repair(xs, fill=True, max_adds=0 if field is not None else 1_000_000)
    x = P.full(xr)
    assert I.s @ x <= I.B + 1e-6
    order, nfill = C.final_order(I, x, np.zeros(I.n, np.int64))
    xf = np.zeros(I.n)
    xf[order] = 1.0
    info.update(start=start, wall=time.time() - t0, wall_pt=wall_pt, threads=THREADS, budget=BUDGET, cfg=c2,
                **{k: v for k, v in li.items() if np.isscalar(v)}, **{"rep_" + k: v for k, v in st.items()},
                n_fill=int(nfill))
    return I, x, xf, xb, field, info


def cpsat_anchor(C, P, xb, field, dl, seed, SC=1e6):
    """min SC*max_w L_w + sum_e round(SC*h_e) x_e  s.t. s.x <= B (exact max, no LSE); variables = episodes with a
    positive saving in some window or in Baleen's set (others stay 0: their field is positive and they change no load).
    q2 classical-finalist CP-SAT parameters (no presolve, linearization 1), Baleen solution as hint, 4 workers."""
    from ortools.sat.python import cp_model
    pos = np.zeros(P.n, bool)
    rows = np.repeat(np.arange(P.n), np.diff(P.Da.indptr))
    pos[rows[P.Da.data > 0]] = True
    var = np.flatnonzero((pos | (xb > 0.5)) & (P.s <= P.B + 1e-9))
    Da = P.Da[var].tocsc()
    dsc = np.rint(Da.data * SC).astype(np.int64)
    Csc = np.rint(P.C * SC).astype(np.int64)
    hsc = np.rint(field[var] * SC).astype(np.int64)
    m = cp_model.CpModel()
    xs = [m.NewBoolVar(f"x{i}") for i in range(len(var))]
    m.Add(cp_model.LinearExpr.WeightedSum(xs, [int(v) for v in np.rint(P.s[var]).astype(np.int64)]) <= int(np.floor(P.B + 1e-9)))
    wi = np.repeat(np.arange(P.ma), np.diff(Da.indptr))
    maxsave = np.zeros(P.ma, np.int64)
    np.add.at(maxsave, wi, np.maximum(dsc, 0))
    minsave = np.zeros(P.ma, np.int64)
    np.add.at(minsave, wi, np.minimum(dsc, 0))
    z = m.NewIntVar(int((Csc - maxsave).max()), int((Csc - minsave).max()), "z")
    for w in range(P.ma):
        idx = Da.indices[Da.indptr[w]:Da.indptr[w + 1]]
        val = dsc[Da.indptr[w]:Da.indptr[w + 1]]
        if len(idx) == 0:
            m.Add(z >= int(Csc[w]))
        else:
            m.Add(z + cp_model.LinearExpr.WeightedSum([xs[i] for i in idx], [int(v) for v in val]) >= int(Csc[w]))
    m.Minimize(z + cp_model.LinearExpr.WeightedSum(xs, [int(v) for v in hsc]))
    for i, e in enumerate(var):
        m.AddHint(xs[i], int(xb[e] > 0.5))
    sv = cp_model.CpSolver()
    sv.parameters.max_time_in_seconds = max(dl - time.time(), 0.1)
    sv.parameters.num_workers = THREADS
    sv.parameters.random_seed = int(seed)
    sv.parameters.cp_model_presolve = False
    sv.parameters.linearization_level = 1
    st = sv.Solve(m)
    x = np.zeros(P.n)
    info = dict(cp_status=sv.StatusName(st), cp_nvar=int(len(var)))
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        x[var] = [sv.Value(v) for v in xs]
        info.update(cp_obj=float(sv.ObjectiveValue()) / SC, cp_bound=float(sv.BestObjectiveBound()) / SC)
    else:
        x = xb.copy()
    return x, info


def stats(inst, design, seed, I, x, xf, xb, field, info, secs):
    import scipy.sparse as sp
    z = np.load(os.path.join(INST, f"day1_{inst}.npz"))
    D = sp.csr_matrix((z["D_data"], z["D_indices"], z["D_indptr"]), shape=tuple(z["D_shape"]))
    C_ = z["C"].astype(float)
    s = z["s"].astype(float)
    L = C_ - D.T @ xf
    Lb = C_ - D.T @ xb
    dmax = np.asarray(D.max(1).todense()).ravel()
    nacc = z["num_accesses"] if "num_accesses" in z.files else None
    sel = x > 0.5
    srt = np.sort(L)[::-1] * US
    out = dict(inst=inst, design=design, seed=seed, n=int(len(s)), B=float(I.B), n_core=int(sel.sum()),
               n_label=int(xf.sum()), n_baleen=int(xb.sum()),
               jaccard_vs_baleen=float((xf * xb).sum() / max(((xf + xb) > 0).sum(), 1)),
               hamming_vs_baleen=int(np.abs(xf - xb).sum()), use_frac=float(s @ xf / I.B),
               dt_ratio=float((D.sum(1).A1 @ xf) / max(D.sum(1).A1 @ xb, 1e-12)),
               label_peak_util=float(srt[0]), baleen_peak_util=float(Lb.max() * US),
               label_top3=float(srt[:3].mean()), label_top5=float(srt[:5].mean()), label_top10=float(srt[:10].mean()),
               baleen_top3=float(np.sort(Lb)[::-1][:3].mean() * US), baleen_top10=float(np.sort(Lb)[::-1][:10].mean() * US),
               label_mean_util=float(L.mean() * US), baleen_mean_util=float(Lb.mean() * US),
               zero_value_labels=int(((xf > 0.5) & (dmax <= 1e-12)).sum()),
               zero_value_labels_baleen=int(((xb > 0.5) & (dmax <= 1e-12)).sum()),
               field_energy_util=float(field @ xf * US) if field is not None else 0.0,
               secs=secs, info=info)
    if nacc is not None:
        out["single_access_labels"] = int(((xf > 0.5) & (nacc <= 1)).sum())
        out["single_access_labels_baleen"] = int(((xb > 0.5) & (nacc <= 1)).sum())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", required=True)
    ap.add_argument("--design", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--p-fadd", type=float, default=0.1)
    o = ap.parse_args()
    assert o.inst in DEV, o.inst
    out = os.path.join(LABELS, f"{o.inst}_{o.design}_s{o.seed}.npz")
    spec = parse(o.design)
    student_file = prev_file = None
    if spec["student"] is not None:
        r = spec["rnd"]
        lam_s = re.fullmatch(r"STU([\d.]+)R\d+", o.design).group(1)
        prev = "F1PT4" if r == 1 else f"STU{lam_s}R{r - 1}"
        prev_file = os.path.join(LABELS, f"{o.inst}_{prev}_s{o.seed}.npz")
        student_file = os.path.join(LABELS, f"student_{o.inst}_{prev}_s{o.seed}.npz")
        assert os.path.exists(prev_file) and os.path.exists(student_file), (prev_file, student_file)
    t = time.time()
    I, x, xf, xb, field, info = solve(o.inst, o.design, o.seed, student_file, prev_file, o.p_fadd)
    z = np.load(os.path.join(INST, f"day1_{o.inst}.npz"))
    st = stats(o.inst, o.design, o.seed, I, x, xf, xb, field, info, time.time() - t)
    os.makedirs(LABELS, exist_ok=True)
    sel = x > 0.5
    np.savez_compressed(out + ".part.npz", core_keys=z["keys"][sel], core_ts0=z["ts0"][sel], B=int(I.B),
                        x_core=x.astype(np.int8), x_full=xf.astype(np.int8))
    os.replace(out + ".part.npz", out)
    json.dump(st, open(out.replace(".npz", ".json"), "w"), indent=1, default=float)
    print(f"[labels_c] {o.inst} {o.design} s{o.seed}: core {st['n_core']} label {st['n_label']} (Baleen {st['n_baleen']}) "
          f"J={st['jaccard_vs_baleen']:.3f} H={st['hamming_vs_baleen']} day-1 peak {st['label_peak_util']:.2f} "
          f"top3 {st['label_top3']:.2f} top10 {st['label_top10']:.2f} (Baleen {st['baleen_peak_util']:.2f}) "
          f"zero-value {st['zero_value_labels']} {st['secs']:.1f}s", flush=True)


if __name__ == "__main__":
    main()
