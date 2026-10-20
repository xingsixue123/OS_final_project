"""Independent recomputation of headline numbers from raw ledgers (read-only; used by STORY.md Appendix D).

  python3 changes/4_story/code/recompute.py > changes/4_story/result/recompute_out.txt

Only matched rows (WR within 35.599 MB/s +-1%, column `matched`) count, as in every protocol.
SE_retrain = sqrt(sum_i s2_X,i/n_X,i + s2_R,i/n_R,i)/n  (PROTOCOL_v2_H3 section 5); SE_inst = sd(d_i)/sqrt(n).
"""
import collections
import csv
import json
import math
import os
import re
import statistics as st

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P2 = os.path.join(REPO, "changes", "2_deployable_peak")
AR = os.path.join(REPO, "changes", "3_autoresearch", "work")


def cells(path):
    d = collections.defaultdict(list)
    for r in csv.DictReader(open(path)):
        if r["matched"] != "True":
            continue
        arm = r["arm"]
        if r.get("design") not in (None, "", "baleen"):
            arm += ":" + r["design"]
        d[(arm, r["inst"])].append(float(r["p100"]))
    out = collections.defaultdict(dict)
    for (a, i), v in d.items():
        out[a][i] = v
    return out


def compare(c, x, ref):
    insts = sorted(c[ref])
    n = len(insts)
    d = [st.mean(c[ref][i]) - st.mean(c[x][i]) for i in insts]
    var = sum(st.variance(c[x][i]) / len(c[x][i]) + st.variance(c[ref][i]) / len(c[ref][i]) for i in insts)
    se_r = math.sqrt(var) / n
    se_i = st.stdev(d) / math.sqrt(n)
    wins = sum(v > 0 for v in d)
    return (f"{x} vs {ref}: wins {wins}/{n}, mean(ref-X) {st.mean(d):+.3f}, SE_retrain {se_r:.3f}, SE_inst {se_i:.3f}, "
            f"worst {min(d):+.3f}; |mean|/SE_retrain {abs(st.mean(d)) / se_r:.3f}, |mean|/SE_inst {abs(st.mean(d)) / se_i:.3f}")


def arm_means(label, c):
    for a in sorted(c):
        m = st.mean(st.mean(v) for v in c[a].values())
        print(f"{label}: {a} mean P100 {m:.2f} over {len(c[a])} instances; matched retrains per cell {sorted(len(v) for v in c[a].values())}")


def mech_by_region(path, label):
    d = collections.defaultdict(list)
    for r in csv.DictReader(open(path)):
        if r["matched"] != "True":
            continue
        arm = r["arm"] + (":" + r["design"] if r.get("design") not in (None, "", "baleen") else "")
        d[(r["region"], arm)].append((float(r["k0_adm"]), float(r["peak_adm"])))
    for (reg, arm), v in sorted(d.items()):
        print(f"{label} {reg} {arm}: first-access adm {st.mean(x for x, _ in v) * 100:.1f}%, "
              f"peak-window adm {st.mean(y for _, y in v):.2f} (n={len(v)})")


def wp2_wide_theta():
    rows = [r for r in csv.DictReader(open(os.path.join(P2, "wp2_deployed", "trials.csv")))
            if r["arm"].startswith(("Ax", "Bx", "Ex")) and r["matched"] == "True"]
    th = [float(r["threshold"]) for r in rows]
    cnt = collections.Counter(r["arm"] for r in rows)
    print(f"WP2 widened-search re-runs (Ax/Bx/Ex): {len(rows)} matched rows {dict(cnt)}; theta min {min(th):.4f} max {max(th):.4f}")


def concentration(c, ref, x, label):
    insts = sorted(c[ref])
    d = {i: st.mean(c[ref][i]) - st.mean(c[x][i]) for i in insts}
    tot = sum(d.values())
    top = max(d, key=d.get)
    rest = [v for i, v in d.items() if i != top]
    se_i = st.stdev(list(d.values())) / math.sqrt(len(d))
    print(f"{label}: per-instance {ref} - {x}: " + ", ".join(f"{i} {v:+.3f}" for i, v in d.items())
          + f"; sum {tot:.3f}; largest {top} {d[top]:+.3f} = {100 * d[top] / tot:.0f}% of the sum; "
          f"mean of the other {len(rest)} {st.mean(rest):+.3f} ({100 * st.mean(rest) / st.mean(st.mean(v) for v in c[ref].values()):.1f}% of {ref}'s mean); "
          f"mean/SE_inst = {st.mean(d.values()) / se_i:.2f}")


def lp_start_share():
    q2 = os.path.join(REPO, "changes", "1_literature_review", "explore", "q2", "RESULTS.md")
    rows = {}
    for ln in open(q2):
        m = re.match(r"\| (pt|lp|greedy)[^|]*\| [^|]*\| \**([\d.]+)\**", ln)
        if m and m.group(1) not in rows:
            rows[m.group(1)] = float(m.group(2))
    g, lp, pt = rows["greedy"], rows["lp"], rows["pt"]
    print(f"Q2 held-out, 10 s analytic objective (q2 RESULTS 8.1): greedy {g}, LP+round+repair {lp}, PT {pt}; "
          f"share of the greedy->PT reduction already reached by the LP start = {100 * (g - lp) / (g - pt):.1f}%; "
          f"PT's own improvement over its LP start = {lp - pt:.3f}")


def k0_by_arm(path, region, label):
    d = collections.defaultdict(list)
    for r in csv.DictReader(open(path)):
        if r["matched"] == "True" and r["region"] == region and r.get("k0_adm"):
            arm = r["arm"] + (":" + r["design"] if r.get("design") not in (None, "", "baleen") else "")
            d[arm].append(float(r["k0_adm"]))
    print(f"{label} {region} first-access admission by arm (mean / max over matched rows): " + "; ".join(
        f"{a} {100 * st.mean(v):.2f}%/{100 * max(v):.2f}% (n={len(v)})" for a, v in sorted(d.items())))


def wp1_region_means():
    rows = list(csv.DictReader(open(os.path.join(P2, "wp1_offline", "results", "wp1_table.csv"))))
    for m in ("lp", "cpsat", "pt"):
        per = collections.defaultdict(list)
        for r in rows:
            per[r["region"]].append((float(r["R0"]) - float(r[m])) / float(r["R0"]) * 100)
        rm = {k: st.mean(v) for k, v in per.items()}
        print(f"WP1 {m}: per-region mean reduction " + ", ".join(f"{k} {v:.2f}%" for k, v in sorted(rm.items()))
              + f"; mean of the 4 per-region means {st.mean(rm.values()):.2f}%")


def cells_merged(path, merge, keyfn):
    """Like cells(), with an arm-name merge map (e.g. WP2's widened-search re-runs Ax/Bx/Ex merged into Aa/Ba/Ea,
    as wp2_deployed/RESULTS_dev.md section 8 does) and a custom configuration key."""
    d = collections.defaultdict(list)
    for r in csv.DictReader(open(path)):
        if r["matched"] != "True":
            continue
        r = dict(r)
        r["arm"] = merge.get(r["arm"], r["arm"])
        d[(keyfn(r), r["inst"])].append(float(r["p100"]))
    out = collections.defaultdict(dict)
    for (a, i), v in d.items():
        out[a][i] = v
    return out


def wp10_tables():
    rows = list(csv.DictReader(open(os.path.join(P2, "wp10_schedule", "results", "solves_test.csv"))))
    by = collections.defaultdict(dict)
    for r in rows:
        by[(r["inst"], r["arm"], r["rep"])][r["solver"]] = [round(float(x), 6) for x in json.loads(r["mult"])]
    pt = {k: v["pt"] for k, v in by.items() if "pt" in v}
    neutral = sorted(k for k, m in pt.items() if all(x == 1.0 for x in m))
    same_ex = sum(1 for k in pt if by[k].get("ex") == pt[k])
    same_cd = sum(1 for k in pt if by[k].get("cd") == pt[k])
    print(f"WP10 test table fits (solves_test.csv): {len(pt)} PT fits; neutral (all multipliers 1.0) on {len(neutral)}: "
          + ", ".join(f"{i} {a} r{r}" for i, a, r in neutral)
          + f"; PT table == exhaustive (ex) table on {same_ex}/{len(pt)}; == CD table on {same_cd}/{len(pt)}")


def trackc_anc_times():
    """When Track C's anchored-energy solves finished (ledger `ts` = completion time), PT (ANC10) vs CP-SAT (ANC10CP)."""
    rows = list(csv.DictReader(open(os.path.join(P2, "wp8_trackC", "results", "ledger_labels.csv"))))
    for d in ("ANC10", "ANC10CP"):
        ts = sorted(r["ts"] for r in rows if r["design"] == d)
        print(f"Track C {d} solves: {len(ts)} ledger rows, finished {ts[0]} .. {ts[-1]}")


def patch_counts():
    """Added/removed lines in wp0_overlay/PATCH.diff: all '+'/'-' lines (as git numstat counts) and non-blank '+' lines."""
    lines = open(os.path.join(P2, "wp0_overlay", "PATCH.diff"), encoding="utf-8").read().split("\n")
    add = [x for x in lines if x.startswith("+") and not x.startswith("+++")]
    rem = [x for x in lines if x.startswith("-") and not x.startswith("---")]
    print(f"wp0 PATCH.diff: +{len(add)}/-{len(rem)} lines; non-blank added lines {sum(1 for x in add if x[1:].strip())}; "
          f"files {sum(1 for x in lines if x.startswith('diff '))}")


def quoted_arithmetic():
    """Differences between values quoted in reports (the inputs are copied from the cited lines)."""
    # harness_eval/RESULTS.md: C4 sim P100 Region7 27.97 (L137), Region6 27.87 (L156); q2/PROGRESS.md L50-51: F2b dev sims
    c4 = {"Region7": 27.97, "Region6": 27.87}
    f2b = {"pgreedy": {"Region7": 28.53, "Region6": 28.26}, "ls": {"Region7": 28.47, "Region6": 28.28},
           "pt": {"Region7": 28.53, "Region6": 28.24}}
    r0 = {"Region7": 34.52, "Region6": 35.56}
    print("harness C4 below F2b dev pgreedy: " + ", ".join(
        f"{r} {(f2b['pgreedy'][r] - c4[r]) / f2b['pgreedy'][r] * 100:.2f}%" for r in c4))
    print("Baleen peak-blind OPT minus F2b dev sims (points): " + ", ".join(
        f"{m} {r} {r0[r] - f2b[m][r]:.2f}" for m in f2b for r in r0))


def wp1_r0_vs_author():
    rows = list(csv.DictReader(open(os.path.join(P2, "wp1_offline", "results", "wp1_table.csv"))))
    d = {r["instance"]: float(r["R0"]) - float(r["author_opt_p100"]) for r in rows}
    worst = max(d, key=lambda k: abs(d[k]))
    print(f"WP1 R0 - authors' OPT-AP P100 over {len(d)} instances: mean {st.mean(d.values()):+.3f}, "
          f"mean |d| {st.mean(abs(v) for v in d.values()):.3f}, largest |d| {abs(d[worst]):.3f} on {worst}; "
          f"Region4_s0.3 {d['Region4_s0.3']:+.3f} (|d| {abs(d['Region4_s0.3']):.3f})")


def label_objectives(d, label, insts=None, seeds=None):
    """Day-1 F1 objective (label_peak_util) of seed-matched PT vs CP-SAT label sets in one labels/ directory."""
    obj = {}
    for f in sorted(os.listdir(d)):
        m = re.match(r"(.+)_(F1PT|F1CPSAT)_s(\d+)\.json$", f)
        if m and (insts is None or m.group(1) in insts) and (seeds is None or m.group(3) in seeds):
            obj[(m.group(1), m.group(3), m.group(2))] = json.load(open(os.path.join(d, f)))["label_peak_util"]
    pairs = sorted({(i, k) for i, k, _ in obj if (i, k, "F1PT") in obj and (i, k, "F1CPSAT") in obj})
    diff = [obj[(i, k, "F1PT")] - obj[(i, k, "F1CPSAT")] for i, k in pairs]
    rel = [100 * x / obj[(i, k, "F1CPSAT")] for x, (i, k) in zip(diff, pairs)]
    print(f"{label} day-1 F1 objective, {len(pairs)} seed-matched pairs: CP-SAT lower {sum(x > 0 for x in diff)}, "
          f"PT lower {sum(x < 0 for x in diff)}, equal {sum(x == 0 for x in diff)}; PT - CP-SAT {min(diff):+.3f} .. "
          f"{max(diff):+.3f} ({min(rel):+.2f}% .. {max(rel):+.2f}%); means PT {st.mean(obj[(i, k, 'F1PT')] for i, k in pairs):.3f}"
          f" CP-SAT {st.mean(obj[(i, k, 'F1CPSAT')] for i, k in pairs):.3f}")


def per_retrain(path, inst, arms):
    rows = [r for r in csv.DictReader(open(path)) if r["matched"] == "True" and r["inst"] == inst and r["arm"] in arms]
    return {a: [round(float(r["p100"]), 2) for r in sorted(rows, key=lambda r: r["rep"]) if r["arm"] == a] for a in arms}


def ledger_window(path, flt=lambda r: True):
    """Earliest start (ts - wall_secs) and last completion (ts) of the rows that pass flt."""
    import datetime as dt
    rows = [r for r in csv.DictReader(open(path)) if flt(r) and r.get("ts")]
    t = [dt.datetime.fromisoformat(r["ts"]) for r in rows]
    s = [dt.datetime.fromisoformat(r["ts"]) - dt.timedelta(seconds=float(r["wall_secs"] or 0)) for r in rows]
    return f"{len(rows)} rows, earliest start {min(s):%Y-%m-%d %H:%M:%S}, first row {min(t):%H:%M:%S}, last row {max(t):%Y-%m-%d %H:%M:%S}"


def round4():
    print("\n## Round-4 additions")
    label_objectives(os.path.join(P2, "wp3_test", "labels"), "WP3 H3' test labels")
    label_objectives(os.path.join(P2, "wp2_deployed", "labels"), "WP2 dev labels")
    tests = [("WP2 dev", os.path.join(P2, "wp2_deployed", "trials.csv")),
             ("WP3 H3'", os.path.join(P2, "wp3_test", "trials.csv")),
             ("WP9 H4", os.path.join(P2, "wp9_region5", "trials.csv")),
             ("WP10 H5", os.path.join(P2, "wp10_schedule", "trials_test.csv")),
             ("T2 Region4", os.path.join(AR, "t2u_region4", "trials_test.csv")),
             ("T1 Region2 (descriptive)", os.path.join(AR, "t1u_region2", "trials_test.csv"))]
    for name, path in tests:
        c = cells(path)
        ma, mb = (st.mean(st.mean(v) for v in c[a].values()) for a in ("A", "B"))
        both = sorted(set(c["A"]) & set(c["B"]))
        paired = st.mean(st.mean(c["B"][i]) - st.mean(c["A"][i]) for i in both)
        print(f"arm B vs A, {name}: A {ma:.3f} (n={len(c['A'])}), B {mb:.3f} (n={len(c['B'])}), "
              f"paired B - A {paired:+.3f} over {len(both)} instances;", compare(c, "B", "A"))
    t2 = os.path.join(AR, "t2u_region4", "trials_test.csv")
    for inst in ("Region4_s0.4", "Region4_s0.5"):
        print(f"T2 {inst} per retrain: {per_retrain(t2, inst, ('A', 'B'))}")
    c = cells(t2)
    d = {i: st.mean(c["A"][i]) - st.mean(c["Aa-1.0"][i]) for i in c["A"]}
    two = d["Region4_s0.2"] + d["Region4_s0.3"]
    print(f"T2 A - A+alpha: s0.2 + s0.3 = {two:.3f} of {sum(d.values()):.3f} ({100 * two / sum(d.values()):.1f}%)")
    for f in ("solves_dev.csv", "solves_test.csv"):
        w = [float(r["wall_s"]) for r in csv.DictReader(open(os.path.join(P2, "wp10_schedule", "results", f)))
             if r["solver"] == "ex"]
        print(f"WP10 {f} exhaustive (ex) wall_s: n={len(w)}, {min(w):.2f} .. {max(w):.2f} s, above 2.35 s: {sum(x > 2.35 for x in w)}")
    rows = list(csv.DictReader(open(os.path.join(P2, "wp10_schedule", "trials_test.csv"))))
    p = {(r["inst"], r["arm"], r["rep"]): float(r["p100"]) for r in rows if r["matched"] == "True"}
    neutral = [(r["inst"], r["rep"]) for r in rows if r["arm"] == "TB-pt" and r["matched"] == "True"
               and all(float(x) == 1.0 for x in json.loads(r["table_mult"] or "[]") or [0])]
    same = [k for k in neutral if (k[0], "B", k[1]) in p and abs(p[(k[0], "TB-pt", k[1])] - p[(k[0], "B", k[1])]) < 1e-9]
    print(f"WP10 TB-pt neutral-table retrains: {len(neutral)}; P100 equal to arm B's same retrain on {len(same)}; others: "
          + ", ".join(f"{i} r{k} TB-pt {p[(i, 'TB-pt', k)]:.3f} vs B {p[(i, 'B', k)]:.3f}" for i, k in neutral if (i, k) not in same))
    tc = os.path.join(P2, "wp8_trackC", "results")
    for f in ("ledger_labels.csv", "proxy_ledger.csv"):
        ts = sorted(r["ts"] for r in csv.DictReader(open(os.path.join(tc, f))) if r["ts"].startswith("2026-10-05"))
        print(f"Track C {f} rows on 2026-10-05: {len(ts)}, {ts[0]} .. {ts[-1]}; after 15:06: {sum(t > '2026-10-05T15:06' for t in ts)}")
    for name, path, flt in (("H3' test", os.path.join(P2, "wp3_test", "trials.csv"), lambda r: True),
                            ("H4 test", os.path.join(P2, "wp9_region5", "trials.csv"), lambda r: r["stage"] != "dry"),
                            ("H5 test", os.path.join(P2, "wp10_schedule", "trials_test.csv"), lambda r: True)):
        print(f"{name} ledger: {ledger_window(path, flt)}")
    for r in csv.DictReader(open(os.path.join(P2, "wp1_offline", "results", "wp1_table.csv"))):
        if r["region"] == "Region4":
            print(f"WP1 {r['instance']} reduction vs R0 % (simulated argmax / planned argmax): " + ", ".join(
                f"{m} {(float(r['R0']) - float(r[m])) / float(r['R0']) * 100:+.1f} ({r[m + '_argmax']}/{r[m + '_plan_argmax']})"
                for m in ("lp", "cpsat", "pt")))
    w1 = [r for r in csv.DictReader(open(os.path.join(P2, "wp1_offline", "trials.csv"))) if r["phase"] == "wp1_reused_phase1_heldout"]
    print(f"WP1 reused phase-1 held-out rows: {len(w1)} rows, {len({r['instance'] for r in w1})} instances, ts {min(r['ts'] for r in w1)} .. {max(r['ts'] for r in w1)}")


def h1_without_reused():
    rows = list(csv.DictReader(open(os.path.join(P2, "wp1_offline", "results", "wp1_table.csv"))))
    reused = {r["instance"].replace("full_", "") for r in csv.DictReader(open(os.path.join(P2, "wp1_offline", "trials.csv")))
              if r["phase"] == "wp1_reused_phase1_heldout"}
    for name, sel in (("without the reused", [r for r in rows if r["instance"] not in reused]),
                      ("reused only", [r for r in rows if r["instance"] in reused])):
        print(f"WP1 H1' {name} instances (n={len(sel)}; reused = {sorted(reused)}): " + ", ".join(
            f"{m} wins {sum(float(r[m]) < float(r['R0']) for r in sel)}/{len(sel)} mean reduction "
            f"{st.mean((float(r['R0']) - float(r[m])) / float(r['R0']) * 100 for r in sel):.2f}%" for m in ("lp", "cpsat", "pt")))


def drop_inst(c, inst):
    return {a: {i: v for i, v in d.items() if i != inst} for a, d in c.items()}


def round5():
    print("\n## Round-5 additions")
    tests = [("WP3 H3'", os.path.join(P2, "wp3_test", "trials.csv")),
             ("WP9 H4", os.path.join(P2, "wp9_region5", "trials.csv")),
             ("WP10 H5", os.path.join(P2, "wp10_schedule", "trials_test.csv")),
             ("T2 Region4", os.path.join(AR, "t2u_region4", "trials_test.csv")),
             ("T1 Region2 (descriptive)", os.path.join(AR, "t1u_region2", "trials_test.csv"))]
    for name, path in tests:
        c = cells(path)
        if name.startswith("T1"):  # the report's evaluable instances: those where arm A is matched (s0.3-0.6)
            c = {a: {i: v for i, v in d.items() if i in c["A"]} for a, d in c.items()}
        both = sorted(set(c["Aa-1.0"]) & set(c["Ba-1.0"]))
        ma, mb = (st.mean(st.mean(c[a][i]) for i in both) for a in ("Aa-1.0", "Ba-1.0"))
        print(f"B+alpha vs A+alpha, {name}: A+alpha {ma:.3f}, B+alpha {mb:.3f} over {len(both)} instances;",
              compare(c, "Ba-1.0", "Aa-1.0"))
    merge = {"Ax-1.0": "Aa-1.0", "Bx-1.0": "Ba-1.0", "Bx-0.5": "Ba-0.5", "Ex-1.0": "Ea-1.0"}
    w2 = cells_merged(os.path.join(P2, "wp2_deployed", "trials.csv"), merge,
                      lambda r: r["arm"] + (":" + r["design"] if r["design"] not in ("", "baleen") else ""))
    print("B+alpha vs A+alpha, WP2 dev (Ax/Bx merged):", compare(w2, "Ba-1.0", "Aa-1.0"))
    c9 = cells(os.path.join(P2, "wp9_region5", "trials.csv"))
    concentration(c9, "Aa-1.0", "Ba-1.0", "WP9 H4 A+alpha - B+alpha")
    concentration(cells(os.path.join(P2, "wp10_schedule", "trials_test.csv")), "Aa-1.0", "Ba-1.0", "WP10 H5 A+alpha - B+alpha")
    concentration(c9, "A", "Ba-1.0", "WP9 H4 A - B+alpha")
    concentration(c9, "B", "Ba-1.0", "WP9 H4 B - B+alpha")
    label_objectives(os.path.join(AR, "union", "labels"), "Union dev Region5_s0 labels", insts={"Region5_s0"})
    label_objectives(os.path.join(AR, "union", "labels"), "Union dev Region1_s0 labels", insts={"Region1_s0"})
    label_objectives(os.path.join(P2, "wp3_test", "labels"), "WP3 H3' test labels, deployed seeds 1-3", seeds={"1", "2", "3"})
    un = cells(os.path.join(AR, "union", "trials_dev.csv"))
    print("Union dev matched retrains on Region5_s0/Region1_s0: " + ", ".join(
        f"{a} {len(un[a].get('Region5_s0', []))}/{len(un[a].get('Region1_s0', []))}"
        for a in ("XA-F1PT", "XA-F1CPSAT", "XG-F1PT", "XG-F1CPSAT")))
    h1_without_reused()
    c3 = cells(os.path.join(P2, "wp3_test", "trials.csv"))
    for x, r in (("Ea-1.0:F1PT", "A"), ("Ea-1.0:F1PT", "Aa-1.0")):
        print("WP3 without Region7_s0.5:", compare(drop_inst(c3, "Region7_s0.5"), x, r))
    for x, r in (("Ea-1.0:F1PT", "A"), ("Ea-1.0:F1PT", "Aa-1.0")):
        print("WP9 without Region5_s0.5:", compare(drop_inst(c9, "Region5_s0.5"), x, r))
    for name, path in (("WP3 H3'", os.path.join(P2, "wp3_test", "trials.csv")), ("WP2 dev", os.path.join(P2, "wp2_deployed", "trials.csv"))):
        c = cells(path)
        d = {i: st.mean(c["A"][i]) - st.mean(c["B"][i]) for i in set(c["A"]) & set(c["B"])}
        best = max(d, key=d.get)
        print(f"{name} per-instance A - B (positive = B better): largest {d[best]:+.3f} on {best}")


def main():
    print("## Test-set arm means (matched retrains; mean of per-instance means)")
    tests = {
        "WP3 H3' (Region6/7 s0.4-0.6)": os.path.join(P2, "wp3_test", "trials.csv"),
        "WP9 H4 (Region5 s0.1-0.6)": os.path.join(P2, "wp9_region5", "trials.csv"),
        "WP10 H5 (Region1 s0.1-0.6)": os.path.join(P2, "wp10_schedule", "trials_test.csv"),
        "3_autoresearch T2 (Region4 s0.2-0.6)": os.path.join(AR, "t2u_region4", "trials_test.csv"),
    }
    cs = {k: cells(v) for k, v in tests.items()}
    for k, c in cs.items():
        arm_means(k, c)
    print("\n## Paired comparisons (pass rule quantities)")
    c = cs["WP3 H3' (Region6/7 s0.4-0.6)"]
    for x, r in [("Ea-1.0:F1PT", "A"), ("Ea-1.0:F1PT", "B"), ("Ea-1.0:F1PT", "Aa-1.0"), ("Ea-1.0:F1PT", "Ba-1.0"),
                 ("Aa-1.0", "A"), ("Aa-1.0", "B"), ("Ba-1.0", "B")]:
        print("WP3", compare(c, x, r))
    c = cs["WP9 H4 (Region5 s0.1-0.6)"]
    for x, r in [("Aa-1.0", "A"), ("Aa-1.0", "B"), ("Ba-1.0", "A"), ("Ba-1.0", "B"), ("Ea-1.0:F1PT", "A"),
                 ("Ea-1.0:F1PT", "Aa-1.0")]:
        print("WP9", compare(c, x, r))
    c = cs["WP10 H5 (Region1 s0.1-0.6)"]
    for x, r in [("TB-pt", "A"), ("TB-pt", "B"), ("TB-pt", "Ba-1.0"), ("Aa-1.0", "A"), ("Aa-1.0", "B"),
                 ("Ba-1.0", "A"), ("Ba-1.0", "B")]:
        print("WP10", compare(c, x, r))
    c = cs["3_autoresearch T2 (Region4 s0.2-0.6)"]
    for x, r in [("XA-F1PT", "A"), ("XA-F1PT", "B"), ("XA-F1PT", "Aa-1.0"), ("XA-F1CPSAT", "XA-F1PT"),
                 ("Aa-1.0", "A"), ("Aa-1.0", "B")]:
        print("T2", compare(c, x, r))

    print("\n## WP1 H1' (offline, matched OPT sims): wins vs R0 and mean P100 reduction")
    rows = list(csv.DictReader(open(os.path.join(P2, "wp1_offline", "results", "wp1_table.csv"))))
    for m in ("lp", "cpsat", "pt"):
        for name, sel in (("all", rows), ("Region4", [r for r in rows if r["region"] == "Region4"]),
                          ("Regions5-7", [r for r in rows if r["region"] != "Region4"])):
            red = [(float(r["R0"]) - float(r[m])) / float(r["R0"]) * 100 for r in sel]
            wins = sum(float(r[m]) < float(r["R0"]) for r in sel)
            print(f"{m:5s} {name:10s} n={len(sel)} wins={wins} mean reduction {st.mean(red):.2f}%")

    print("\n## Mechanism statistics by region (matched retrains; k0_adm = first-access admission)")
    mech_by_region(os.path.join(P2, "wp3_test", "trials.csv"), "WP3")
    c = cells(os.path.join(P2, "wp9_region5", "trials.csv"))
    print("\nWP9 per-instance A - A+alpha: " + ", ".join(
        f"{i} {st.mean(c['A'][i]) - st.mean(c['Aa-1.0'][i]):+.3f}" for i in sorted(c["A"])))
    print("\n## WP2 dev bookkeeping")
    wp2_wide_theta()

    print("\n## Round-2 additions")
    lp_start_share()
    concentration(cells(os.path.join(P2, "wp9_region5", "trials.csv")), "A", "Aa-1.0", "WP9 H4")
    concentration(cells(os.path.join(AR, "t2u_region4", "trials_test.csv")), "A", "Aa-1.0", "T2 Region4")
    c3 = cells(os.path.join(P2, "wp3_test", "trials.csv"))
    print("WP3 per-instance X1 - Dc+alpha (positive = CP-SAT labels lower): " + ", ".join(
        f"{i} {st.mean(c3['Ea-1.0:F1PT'][i]) - st.mean(c3['Ea-1.0:F1CPSAT'][i]):+.3f}" for i in sorted(c3["A"])))
    concentration(c3, "Ea-1.0:F1PT", "Ea-1.0:F1CPSAT", "WP3 X1 - Dc+alpha")
    print("WP3", compare(c3, "Ea-1.0:F1CPSAT", "Ea-1.0:F1PT"))
    merge = {"Ax-1.0": "Aa-1.0", "Bx-1.0": "Ba-1.0", "Bx-0.5": "Ba-0.5", "Ex-1.0": "Ea-1.0"}
    w2 = cells_merged(os.path.join(P2, "wp2_deployed", "trials.csv"), merge,
                      lambda r: r["arm"] + (":" + r["design"] if r["design"] not in ("", "baleen") else ""))
    n378 = [(r["arm"], r["rep"], r["argmax"]) for r in csv.DictReader(open(os.path.join(P2, "wp3_test", "trials.csv")))
            if r["matched"] == "True" and r["inst"] == "Region7_s0.5"]
    print(f"WP3 Region7_s0.5: {sum(a == '378' for _, _, a in n378)} of {len(n378)} matched retrains peak in window 378; "
          f"others: {[x for x in n378 if x[2] != '378']}")
    k0_by_arm(os.path.join(P2, "wp2_deployed", "trials.csv"), "Region6", "WP2 dev")
    k0_by_arm(os.path.join(P2, "wp8_trackC", "trials.csv"), "Region6", "Track C dev")
    cc = cells(os.path.join(AR, "cls_table", "trials_dev.csv"))
    print("3_autoresearch dev Region1_s0 (cls_table ledger): " + ", ".join(
        f"{a} {st.mean(cc[a]['Region1_s0']):.2f} (n={len(cc[a]['Region1_s0'])})" for a in ("A", "Aa-1.0", "B", "Ba-1.0")))
    wp1_region_means()
    rows = [r for r in csv.DictReader(open(os.path.join(P2, "wp9_region5", "trials.csv")))
            if r["matched"] == "True" and r["inst"] == "Region5_s0.6" and r["arm"] in ("A", "Ea-1.0")]
    for arm in ("A", "Ea-1.0"):
        rr = [r for r in rows if r["arm"] == arm]
        print(f"WP9 Region5_s0.6 {arm}: P100 per retrain {[round(float(r['p100']), 2) for r in rr]}, peak windows "
              f"{[r['argmax'] for r in rr]}, big-offset share {[round(float(r['peak_bigoff_share']), 2) for r in rr]}")

    print("\n## Round-3 additions")
    print("WP2 dev (Ax/Bx/Ex merged into Aa/Ba/Ea):", compare(w2, "Ea-1.0:F1CPSAT", "Ea-1.0:F1PT"))
    print("WP2 dev:", compare(w2, "D:F1CPSAT", "D:F1PT"))
    un = cells_merged(os.path.join(AR, "union", "trials_dev.csv"), {}, lambda r: r["arm"])
    print("Union dev:", compare(un, "XA-F1CPSAT", "XA-F1PT"))
    print("Union dev:", compare(un, "XG-F1CPSAT", "XG-F1PT"))
    wp10_tables()
    wp1_r0_vs_author()
    trackc_anc_times()
    patch_counts()
    quoted_arithmetic()
    round4()
    round5()


if __name__ == "__main__":
    main()
