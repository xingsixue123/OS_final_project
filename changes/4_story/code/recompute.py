"""Independent recomputation of headline numbers from raw ledgers (read-only; used by STORY.md Appendix D).

  python3 changes/4_story/code/recompute.py > changes/4_story/result/recompute_out.txt

Only matched rows (WR within 35.599 MB/s +-1%, column `matched`) count, as in every protocol.
SE_retrain = sqrt(sum_i s2_X,i/n_X,i + s2_R,i/n_R,i)/n  (PROTOCOL_v2_H3 section 5); SE_inst = sd(d_i)/sqrt(n).
"""
import collections
import csv
import math
import os
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
    return f"{x} vs {ref}: wins {wins}/{n}, mean(ref-X) {st.mean(d):+.3f}, SE_retrain {se_r:.3f}, SE_inst {se_i:.3f}, worst {min(d):+.3f}"


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


if __name__ == "__main__":
    main()
