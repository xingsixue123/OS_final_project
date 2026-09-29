"""Solver CLI (solver env). Called by PolicyPeakBaleen via subprocess.

  solve.py --inst inst.npz --out sol.npz --cand R1 --args '{"levels":[...], ...}'
Writes sol.npz (order_sel = selected episode indices in nested order, incl. the strict-prefix fill) and
sol.json (analytic stats: peak, z_LP, gap, per-level, solve time).
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pbcore as PC          # noqa: E402
import pbsolvers as PS       # noqa: E402


def greedy_sub(P):
    xs = np.zeros(P.n)
    use = 0.0
    for e in np.argsort(P.rank, kind="stable"):
        if use + P.s[e] > P.B + 1e-9:
            break
        xs[e] = 1
        use += P.s[e]
    return xs


def make_level_solver(cand, a):
    threads = int(a.get("threads", 1))

    def r1(P, k):
        x, info, _ = PS.solve_lp(P, lexi=True, threads=threads)
        xr = (x >= 1 - 1e-6).astype(float)
        xr, st = PC.repair(P, xr, fill=True)
        info.update(st)
        return xr, info

    if cand in ("IDENT", "R0"):
        return lambda P, k: (greedy_sub(P), {})
    if cand == "R1":
        return r1
    if cand == "R2":
        def r2(P, k):
            x1, info = r1(P, k)
            p1 = P.peak(x1)
            xm, mi = PS.solve_milp(P, a.get("milp_secs", 60), x0=x1, threads=threads, seed=a.get("seed", 0))
            info.update(mi)
            info["peak_r1"] = p1
            if xm is not None and P.peak(xm) < p1 - 1e-12:
                xm, _, _, nf = PC.peak_preserving_fill(P, xm)
                info["milp_improved"] = 1
                return xm, info
            info["milp_improved"] = 0
            return x1, info
        return r2
    if cand == "R3":
        def r3(P, k):
            x1, info = r1(P, k)
            p1 = P.peak(x1)
            xl, li = PS.local_search(P, x1, secs=a.get("ls_secs", 30), n_moves=a.get("ls_moves", 300000),
                                     seed=a.get("seed", 0), topk_obj=int(a.get("ls_topk", 0)))
            info.update(li)
            info["peak_r1"] = p1
            if P.peak(xl) < p1 - 1e-12:
                xl, _, _, _ = PC.peak_preserving_fill(P, xl)
                return xl, info
            return x1, info
        return r3
    if cand in ("C3", "C3L"):
        import pbcap
        return pbcap.make_level_solver(cand, a)
    import pbising as PI
    return PI.make_level_solver(cand, a, r1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inst", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--args", default="{}")
    o = ap.parse_args()
    a = json.loads(o.args)
    t = time.time()
    I = PC.Instance(o.inst)
    levels = a.get("levels", [1.0])
    assert abs(levels[-1] - 1.0) < 1e-12
    print(f"[solve] cand={o.cand} n={I.n} m={I.m} active={I.ma} nnz={I.Da.nnz} B={I.B:.0f} levels={levels}",
          flush=True)
    # references at the full budget: Baleen greedy prefix and the LP bound
    xg = PC.greedy_prefix(I, I.B, np.zeros(I.n, bool))
    Pfull = PC.Sub(I, I.B, np.zeros(I.n, bool))
    _, lpinfo, _ = PS.solve_lp(Pfull, lexi=False)
    z_lp = lpinfo["z_lp"]
    solver = make_level_solver(o.cand, a)
    ts = time.time()
    x, lvl_of, per = PC.nested_solve(I, solver, levels)
    solve_secs = time.time() - ts
    order_sel, xf, nfill = PC.final_order(I, x, lvl_of)
    ev = I.evaluate(xf)
    evg = I.evaluate(xg)
    stats = dict(cand=o.cand, args=a, n=I.n, ma=I.ma, B=I.B, levels=levels, solve_secs=solve_secs,
                 total_secs=time.time() - t, z_lp=z_lp, z_lp_util=z_lp * I.US,
                 peak=ev["peak"], peak_util=ev["peak_util"], top5_util=ev["top5"], mean_util=ev["mean"],
                 argmax=ev["argmax"], n_sel=ev["n_sel"], sts=ev["sts"], use=ev["use"], n_fill=nfill,
                 gap_to_zlp=(ev["peak"] - z_lp) / z_lp,
                 baleen_peak_util=evg["peak_util"], baleen_sts=evg["sts"], baleen_argmax=evg["argmax"],
                 headroom_recovered=(evg["peak"] - ev["peak"]) / max(evg["peak"] - z_lp, 1e-12),
                 per_level=per)
    # nested prefix: analytic peak of each prefix of order_sel at the level budgets
    np.savez(o.out, order_sel=order_sel, x=xf)
    with open(o.out.replace(".npz", ".json"), "w") as f:
        json.dump(stats, f, indent=1, default=float)
    print(f"[solve] {o.cand}: peak={ev['peak_util']:.3f}% (Baleen {evg['peak_util']:.3f}%, z_LP "
          f"{z_lp * I.US:.3f}%) gap={stats['gap_to_zlp']:.4f} headroom_rec={stats['headroom_recovered']:.3f} "
          f"sts={ev['sts']:.1f} (Baleen {evg['sts']:.1f}) solve={solve_secs:.1f}s", flush=True)


if __name__ == "__main__":
    main()
