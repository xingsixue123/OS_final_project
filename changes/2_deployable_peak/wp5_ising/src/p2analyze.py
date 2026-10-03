"""WP5 dev analysis: tuning tables, dev evaluation (fresh seeds), H2'-style dev check, hard-level split, finalist rule,
rolling variant, scaling, label-solver evidence.  Writes results/*.md / *.csv / *.json.  Solver env.

  python p2analyze.py tuning | deval | finalists | rolling | scaling | label | all
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

SRC = os.path.dirname(os.path.abspath(__file__))
AREA = os.path.dirname(SRC)
RES = os.path.join(AREA, "results")
ISING = ["pt", "eim", "sb", "mq"]
CLASSICAL = ["lp", "milp", "cpsat", "ls"]
REFS = ["greedy", "pgreedy"]
BUDGETS = [1, 3, 10]
DEV = [f"full_{r}_s{s}" for r in ("Region7", "Region6") for s in ("0", "0.1", "0.2", "0.3")]
TIE = 1e-9


def short(i):
    return i.replace("full_", "").replace("Region", "R")


def trials():
    return pd.read_csv(os.path.join(AREA, "trials.csv"))


def ref():
    return json.load(open(os.path.join(RES, "ref_pgreedy.json")))


# ------------------------------------------------------------------ tuning
def tuning():
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    db = "sqlite:///" + os.path.join(AREA, "optuna.db")
    rows = []
    for sv in ISING + CLASSICAL:
        for b in BUDGETS:
            try:
                st = optuna.load_study(study_name=f"F1__{sv}__b{b:g}", storage=db)
            except Exception:
                continue
            comp = [t for t in st.trials if t.state == optuna.trial.TrialState.COMPLETE]
            if not comp:
                continue
            vals = np.array([t.value for t in comp])
            bt = min(comp, key=lambda t: t.value)
            t0 = [t for t in comp if t.number == 0]
            nfail = int(sum(any(v >= 0.999 for v in t.user_attrs.get("per_inst", [])) for t in comp))
            rows.append(dict(solver=sv, family="Ising" if sv in ISING else "classical", budget=b, n_trials=len(comp),
                             best=100 * bt.value, best_trial=bt.number,
                             trial0_phase1cfg=100 * t0[0].value if t0 else np.nan,
                             median=100 * float(np.median(vals)), n_failed_trials=nfail,
                             best_cfg=bt.user_attrs.get("cfg")))
    T = pd.DataFrame(rows)
    T.to_csv(os.path.join(RES, "tuning_summary.csv"), index=False)
    out = ["| solver | family | " + " | ".join(f"{b} s best (trial) | {b} s phase-1 cfg (t0)" for b in BUDGETS) + " |",
           "|---|---|" + "---|---|" * len(BUDGETS)]
    for sv in ISING + CLASSICAL:
        d = T[T.solver == sv]
        if not len(d):
            continue
        cells = []
        for b in BUDGETS:
            x = d[d.budget == b]
            if len(x):
                x = x.iloc[0]
                cells.append(f"{x.best:+.3f} (t{x.best_trial}, n={x.n_trials}{', fail ' + str(x.n_failed_trials) if x.n_failed_trials else ''})")
                cells.append(f"{x.trial0_phase1cfg:+.3f}")
            else:
                cells += ["-", "-"]
        out.append(f"| {sv} | {'Ising' if sv in ISING else 'classical'} | " + " | ".join(cells) + " |")
    md = "\n".join(out)
    open(os.path.join(RES, "tuning_summary.md"), "w").write(md + "\n")
    print(md)
    return T


# ------------------------------------------------------------------ dev evaluation
def deval_table(phase="deval"):
    tr = trials()
    d = tr[(tr.phase == phase) & (tr.status == "ok")].copy()
    if not len(d):
        return None
    R = ref()
    d["ratio"] = d.apply(lambda r: 100 * (r.objective / R[r.instance] - 1), axis=1)
    g = d.groupby(["solver", "budget", "instance"]).agg(obj=("objective", "mean"), sd=("objective", "std"),
                                                       n=("objective", "size"), ratio=("ratio", "mean"),
                                                       wall=("wall", "max"), over=("over_budget", "sum")).reset_index()
    return d, g


def h2_check(g, ising_solver, budgets=BUDGETS, classical=CLASSICAL + REFS):
    """per (instance, budget): Ising mean vs best classical mean; returns rows + summary."""
    rows = []
    for b in budgets:
        for inst in sorted(g.instance.unique()):
            gi = g[(g.budget == b) & (g.instance == inst)]
            iv = gi[gi.solver == ising_solver]
            cl = gi[gi.solver.isin(classical) & (gi.over == 0)]      # over-budget runs invalidate a cell
            if not len(iv) or not len(cl):
                continue
            best = cl.loc[cl.obj.idxmin()]
            ivv = float(iv.obj.iloc[0]) if int(iv.over.iloc[0]) == 0 else float("inf")
            le = ivv <= best.obj * (1 + TIE)
            strict = ivv < best.obj * (1 - TIE)
            rows.append(dict(instance=inst, budget=b, ising=ivv, ising_over=int(iv.over.iloc[0]),
                             ising_sd=float(iv.sd.iloc[0]) if iv.n.iloc[0] > 1 else 0,
                             best_classical=best.solver, classical=float(best.obj), gap_pct=100 * (ivv / best.obj - 1),
                             le=bool(le), strict=bool(strict)))
    return pd.DataFrame(rows)


def deval(phase="deval", write=True):
    r = deval_table(phase)
    if r is None:
        print("no", phase, "rows")
        return None
    d, g = r
    sv_all = [s for s in ISING + CLASSICAL + REFS if s in set(g.solver)]
    out = [f"Dev evaluation ({phase}): mean over the 8 dev instances of the per-instance mean objective over seeds "
           "(util %, mean of the 8 nested-level peaks); in parentheses (objective / pgreedy - 1) in %.", "",
           "| solver | family | " + " | ".join(f"{b} s" for b in BUDGETS) + " |", "|---|---|" + "---|" * len(BUDGETS)]
    for sv in sv_all:
        cells = []
        for b in BUDGETS:
            x = g[(g.solver == sv) & (g.budget == b)]
            if len(x) == len(DEV):
                cells.append(f"{x.obj.mean():.4f} ({x.ratio.mean():+.2f}%){' [over ' + str(int(x.over.sum())) + ']' if x.over.sum() else ''}")
            elif len(x):
                cells.append(f"{x.obj.mean():.4f} (partial {len(x)}/8)")
            else:
                cells.append("-")
        fam = "Ising" if sv in ISING else ("classical" if sv in CLASSICAL else "reference")
        out.append(f"| {sv} | {fam} | " + " | ".join(cells) + " |")
    out.append("")
    # per-instance table for each budget
    for b in BUDGETS:
        out.append(f"Per instance, {b} s (mean over seeds):")
        out.append("")
        insts = [i for i in DEV if i in set(g.instance)]
        out.append("| solver | " + " | ".join(short(i) for i in insts) + " |")
        out.append("|---|" + "---|" * len(insts))
        for sv in sv_all:
            cells = []
            for i in insts:
                x = g[(g.solver == sv) & (g.budget == b) & (g.instance == i)]
                cells.append(f"{x.obj.iloc[0]:.3f}" if len(x) else "-")
            out.append(f"| {sv} | " + " | ".join(cells) + " |")
        out.append("")
    # H2'-style check on dev for every Ising solver
    out.append("H2'-style dev check (Ising mean over seeds vs the best classical method's mean per (instance, budget); "
               "classical set = lp, milp, cpsat, ls, greedy, pgreedy):")
    out.append("")
    out.append("| Ising solver | " + " | ".join(f"{b} s: <= best classical | {b} s mean Ising vs classical" for b in BUDGETS)
               + " | all pairs mean | budgets with >= 7/8 (<=) |")
    out.append("|---|" + "---|---|" * len(BUDGETS) + "---|---|")
    summ = {}
    for sv in ISING:
        h = h2_check(g, sv)
        if not len(h):
            continue
        cells = []
        nb = 0
        for b in BUDGETS:
            hb = h[h.budget == b]
            if not len(hb):
                cells += ["-", "-"]
                continue
            k = int(hb["le"].sum())
            cells.append(f"{k}/{len(hb)} (strict {int(hb['strict'].sum())})")
            cells.append(f"{hb.ising.mean():.4f} vs {hb.classical.mean():.4f}")
            nb += int(k >= 7)
        cells.append(f"{h.ising.mean():.4f} vs {h.classical.mean():.4f}")
        cells.append(str(nb))
        out.append(f"| {sv} | " + " | ".join(cells) + " |")
        summ[sv] = h
        h.to_csv(os.path.join(RES, f"h2dev_{phase}_{sv}.csv"), index=False)
    md = "\n".join(out)
    if write:
        open(os.path.join(RES, f"{phase}_summary.md"), "w").write(md + "\n")
        g.to_csv(os.path.join(RES, f"{phase}_per_instance.csv"), index=False)
    print(md)
    return g, summ


def finalists():
    r = deval_table("deval")
    d, g = r
    V = {}
    for sv in ISING:
        x = d[d.solver == sv]
        complete = all(len(g[(g.solver == sv) & (g.budget == b)]) == len(DEV) for b in BUDGETS)
        V[sv] = dict(V=float(x.ratio.mean()), V1=float(x[x.budget == 1].ratio.mean()), complete=complete,
                     n=int(len(x)), n_over=int(x.over_budget.sum()),
                     V_overbudget_as_fail=float(np.where(x.over_budget > 0, 100.0, x.ratio).mean()),
                     V_per_budget={f"{b:g}": float(x[x.budget == b].ratio.mean()) for b in BUDGETS})
    ranked = sorted([s for s in V if V[s]["complete"]], key=lambda s: (round(V[s]["V"], 5), V[s]["V1"]))
    fin = ranked[:2]
    plan = json.load(open(os.path.join(RES, "plan_dev.json")))["solvers"]
    alt = sorted([s for s in V if V[s]["complete"]], key=lambda s: (round(V[s]["V_overbudget_as_fail"], 5), V[s]["V1"]))
    out = dict(rule="lowest V = mean over budgets x dev instances x seeds of (obj/pgreedy - 1) in deval; tie -> lower V@1s",
               V=V, ranking=ranked, finalists=fin, ranking_if_overbudget_counted_as_fail=alt,
               ranking_changes_if_overbudget_fail=bool(alt[:2] != fin), configs={s: plan[s] for s in fin})
    json.dump(out, open(os.path.join(RES, "finalists.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "configs"}, indent=1))
    return out


# ------------------------------------------------------------------ rolling
def rolling():
    p = os.path.join(RES, "rolling.csv")
    if not os.path.exists(p):
        print("no rolling results")
        return
    R = pd.read_csv(p)
    R = R[R.status == "ok"]
    g = R.groupby(["solver", "budget"]).agg(full=("full_peak_util", "mean"), n=("full_peak_util", "size"),
                                            over=("n_over_budget", "sum"), maxwall=("max_block_wall", "max")).reset_index()
    tr = trials()
    one = tr[(tr.phase == "deval") & (tr.status == "ok") & (tr.seed.isin([101]))]
    out = ["| solver | budget | rolling full-trace peak (mean over instances) | one-shot nested solve: peak at f=1 (same budget, seed 101) | windows over budget | max window wall (s) |",
           "|---|---|---|---|---|---|"]
    for _, x in g.sort_values(["budget", "full"]).iterrows():
        o = one[(one.solver == x.solver) & (one.budget == x.budget)]
        o = o[o.instance.isin(set(R[(R.solver == x.solver) & (R.budget == x.budget)].instance))]
        out.append(f"| {x.solver} | {x.budget:g} | {x.full:.3f} (n={x.n}) | "
                   f"{o.peak_W_util.mean():.3f} | {int(x.over)} | {x.maxwall:.2f} |" if len(o) else
                   f"| {x.solver} | {x.budget:g} | {x.full:.3f} (n={x.n}) | - | {int(x.over)} | {x.maxwall:.2f} |")
    out.append("")
    out.append("Per instance (full-trace peak of the stitched selection, util %):")
    out.append("")
    piv = R.pivot_table(index=["budget", "solver"], columns="instance", values="full_peak_util")
    insts = [i for i in DEV if i in piv.columns]
    out.append("| budget | solver | " + " | ".join(short(i) for i in insts) + " |")
    out.append("|---|---|" + "---|" * len(insts))
    for (b, sv), row in piv.iterrows():
        out.append(f"| {b:g} | {sv} | " + " | ".join(f"{row[i]:.3f}" if not pd.isna(row[i]) else "-" for i in insts) + " |")
    # rolling H2-style: per (instance, budget) Ising vs best classical
    out.append("")
    rows = []
    for b in sorted(R.budget.unique()):
        for i in sorted(R.instance.unique()):
            x = R[(R.budget == b) & (R.instance == i)]
            cl = x[x.solver.isin(CLASSICAL + REFS)]
            for sv in ISING:
                iv = x[x.solver == sv]
                if len(iv) and len(cl):
                    rows.append(dict(budget=b, instance=i, solver=sv, ising=float(iv.full_peak_util.mean()),
                                     classical=float(cl.full_peak_util.min()),
                                     best=cl.loc[cl.full_peak_util.idxmin()].solver))
    H = pd.DataFrame(rows)
    if len(H):
        out.append("Rolling, Ising vs best classical (stitched full-trace peak) per (instance, budget):")
        out.append("")
        out.append("| Ising | budget | <= best classical | mean Ising | mean best classical |")
        out.append("|---|---|---|---|---|")
        for (sv, b), h in H.groupby(["solver", "budget"]):
            out.append(f"| {sv} | {b:g} | {int((h.ising <= h.classical * (1 + TIE)).sum())}/{len(h)} | {h.ising.mean():.3f} | "
                       f"{h.classical.mean():.3f} |")
    md = "\n".join(out)
    open(os.path.join(RES, "rolling_summary.md"), "w").write(md + "\n")
    print(md)


# ------------------------------------------------------------------ scaling
def scaling():
    p = os.path.join(RES, "scaling.jsonl")
    if not os.path.exists(p):
        print("no scaling results")
        return
    S = pd.DataFrame([json.loads(l) for l in open(p) if l.strip()])
    S = S.sort_values(["solver", "n"])
    out = ["| solver | instance | part | n (episodes) | n vars | nnz(D) | status | build s | solve s | s/step or s/Mprop | peak RSS MB | RSS after load MB |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in S.iterrows():
        per = r.get("secs_per_step") if r.solver != "pt" else r.get("secs_per_Mprop")
        out.append(f"| {r.solver} | {r.inst}{'' if not r.get('n_sub') else ' first ' + str(int(r.n_sub))} | {r.part} | "
                   f"{int(r.n) if not pd.isna(r.get('n')) else '-'} | {int(r.n_vars) if not pd.isna(r.get('n_vars', np.nan)) else '-'} | "
                   f"{int(r.nnz_vars) if not pd.isna(r.get('nnz_vars', np.nan)) else '-'} | {str(r.status)[:40]} | "
                   f"{r.get('build_secs', np.nan):.2f} | {r.get('solve_secs', np.nan):.2f} | "
                   f"{per if per is None or pd.isna(per) else round(per, 4)} | {r.get('maxrss_mb', np.nan):.0f} | "
                   f"{r.get('rss_base_mb', np.nan):.0f} |")
    md = "\n".join(out)
    open(os.path.join(RES, "scaling_summary.md"), "w").write(md + "\n")
    print(md)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["tuning", "deval", "deval_hl", "finalists", "rolling", "scaling", "all"])
    o = ap.parse_args()
    if o.what in ("tuning", "all"):
        tuning()
    if o.what in ("deval", "all"):
        deval("deval")
    if o.what in ("deval_hl", "all"):
        deval("deval_hl")
    if o.what == "finalists":
        finalists()
    if o.what in ("rolling", "all"):
        rolling()
    if o.what in ("scaling", "all"):
        scaling()


if __name__ == "__main__":
    main()
