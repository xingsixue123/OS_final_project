"""AR test evaluation (written before any test data exist): the contract §4 pass rule, computed exactly as
code/validate.py:check_claim does, on <test dir>/trials_test.csv and <test dir>/results_test/static_baselines.csv.
Also reports, without pass/fail: the classical control with the same rule, Y vs control (Ising vs classical), the alpha
arms vs A/B, and secondary metrics.

  python3 src/eval_test.py --test-dir <work/test dir> --pool T1 --Y UB-ptm --control UB-cdm
-> <test dir>/results_test/evaluation.json (+ printed report)
"""
import argparse
import csv
import json
import math
import os
from collections import defaultdict

POOLS = {"T1": [f"Region2_s0.{k}" for k in range(1, 7)],
         "T2": [f"Region4_s0.{k}" for k in range(2, 7)],
         "T3": [f"Region3_s0.{k}" for k in range(1, 4)]}


def mean(x):
    return sum(x) / len(x)


def var(x):
    return sum((v - mean(x)) ** 2 for v in x) / (len(x) - 1) if len(x) > 1 else 0.0


def rule(P, insts, x, ref):
    n = len(insts)
    d = [mean(P[(ref, i)]) - mean(P[(x, i)]) for i in insts]
    se = math.sqrt(sum(var(P[(x, i)]) / len(P[(x, i)]) + var(P[(ref, i)]) / len(P[(ref, i)]) for i in insts)) / n
    wins = sum(v > 0 for v in d)
    need = math.ceil(2 * n / 3)
    c = dict(x=x, ref=ref, wins=wins, need=need, mean=mean(d), se=se, worst=min(d), per_inst=dict(zip(insts, d)),
             win_ok=wins >= need, margin_ok=mean(d) > 2.5 * se, tail_ok=min(d) >= -2.0)
    c["ok"] = c["win_ok"] and c["margin_ok"] and c["tail_ok"]
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-dir", required=True)
    ap.add_argument("--pool", required=True, choices=list(POOLS))
    ap.add_argument("--Y", required=True)
    ap.add_argument("--control", required=True)
    o = ap.parse_args()
    insts = POOLS[o.pool]
    arms = {"Y": o.Y, "A": "A", "B": "B", "A+alpha": "Aa-1.0", "B+alpha": "Ba-1.0", "control": o.control}
    rows = list(csv.DictReader(open(os.path.join(o.test_dir, "trials_test.csv"))))
    P = defaultdict(list)
    allrows = defaultdict(int)
    for r in rows:
        allrows[(r["arm"], r["inst"])] += 1
        if str(r["matched"]).strip().lower() in ("true", "1") and r["inst"] in insts:
            P[(r["arm"], r["inst"])].append(float(r["p100"]))
    missing = [(k, i, len(P[(a, i)])) for k, a in arms.items() for i in insts if len(P[(a, i)]) < 3]
    out = dict(pool=o.pool, insts=insts, arms=arms, missing=missing, n_rows=len(rows))
    if missing:
        print("incomplete:", missing)
        json.dump(out, open(os.path.join(o.test_dir, "results_test", "evaluation.json"), "w"), indent=1)
        return
    m = {k: mean([mean(P[(a, i)]) for i in insts]) for k, a in arms.items()}
    per = {k: {i: mean(P[(a, i)]) for i in insts} for k, a in arms.items()}
    best = "A+alpha" if m["A+alpha"] <= m["B+alpha"] else "B+alpha"
    comps = [rule(P, insts, arms["Y"], arms[r]) for r in ("A", "B", best)]
    ok = all(c["ok"] for c in comps)
    st = list(csv.DictReader(open(os.path.join(o.test_dir, "results_test", "static_baselines.csv"))))
    stat = {}
    for meth in ("RejectX", "CoinFlip"):
        v = [float(r["p100"]) for r in st if r["method"] == meth and r["instance"] in insts]
        stat[meth] = mean(v) if len(v) >= len(insts) else None
        ok &= stat[meth] is not None and m["Y"] < stat[meth]
    ctl = [rule(P, insts, arms["control"], arms[r]) for r in ("A", "B", best)]
    y_vs_ctl = rule(P, insts, arms["Y"], arms["control"])
    alpha = [rule(P, insts, arms[a], arms[r]) for a in ("A+alpha", "B+alpha") for r in ("A", "B")]
    out.update(means=m, per_instance=per, best_alpha=best, comparisons=comps, static=stat, good_result=ok,
               control_comparisons=ctl, Y_vs_control=y_vs_ctl, alpha_vs_baselines=alpha,
               n_matched={f"{a}|{i}": len(P[(a, i)]) for a in arms.values() for i in insts},
               n_rows_per_cell={f"{a}|{i}": allrows[(a, i)] for a in arms.values() for i in insts})
    json.dump(out, open(os.path.join(o.test_dir, "results_test", "evaluation.json"), "w"), indent=1)
    print(json.dumps(dict(means=m, best_alpha=best, static=stat, good_result=ok), indent=1))
    for c in comps + [y_vs_ctl]:
        print(f"{c['x']} vs {c['ref']}: wins {c['wins']}/{len(insts)} (need {c['need']}), mean {c['mean']:+.3f}, "
              f"SE {c['se']:.3f} (2.5SE {2.5 * c['se']:.3f}), worst {c['worst']:+.3f} -> ok={c['ok']}")


if __name__ == "__main__":
    main()
