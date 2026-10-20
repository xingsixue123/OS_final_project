"""Write G1_v5.md from results/g1v5_summary.json (src/g1v5.py)."""
import json
import os

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(H, "results", "g1v5_summary.json")))
v, s = S["verdict"], S["summary"]


def yes(b):
    return "**bit-identical**" if b else "**DIFFERENT**"


def cmp_line(name, c):
    return (f"| {name} | {yes(c['all_results_and_series_identical'])}: {c['n_result_keys']} result keys "
            f"(differing: {len(c['result_keys_differing'])}), {c['n_batches']} per-window series (differing: "
            f"{len(c['batches_differing'])}), {c['n_freq']} histograms (differing: {len(c['freq_differing'])}), "
            f"counters differing: {len(c['counters_differing'])}. P100 {c['p100_a']!r} vs {c['p100_b']!r}, "
            f"WR {c['wr_a']:.6f} vs {c['wr_b']:.6f} |")


L = ["# G1_v5: default equivalence of overlay v5 + the union checks (Region7 s0, dev)", "",
     "Driver `src/g1v5.py` (copied from `work/cls_table/src/g1v4.py`; comparison code unchanged). Overlay v5 = "
     "`overlay/BCacheSim` = `PATCH_v5.diff` (9 files) = `work/cls_table/PATCH_v4.diff` + `PATCH_v5_delta.diff` (2 files: "
     "`cachesim/admission_policies.py`, `cachesim/simulate_ap.py`). The frozen code is `0_reproduce/baleen_code`; overlay "
     "v4 (`overlay_v4/`, rebuilt from PATCH_v4.diff) for the v5 == v4 and union checks (the summary keys call it 'v3' "
     "in places: the driver's slot name, inherited). Every process ran as `taskset -c 0-23 bwrap ... --bind <private "
     "tmp> /tmp`; trains under the shared train lock. Full numbers: `results/g1v5_summary.json`.", "",
     f"## Verdict: **G1_v5 {'PASS' if v['G1_v5_pass'] else 'FAIL'}; v5 paths (alpha, class table, union "
     f"degenerate) {'PASS' if v['v5_paths_pass'] else 'FAIL'}**", "",
     "| check | result |", "|---|---|",
     cmp_line("RejectX (authors' static_pf command), frozen sim vs v5 sim", s["rejectx"]),
     cmp_line("CoinFlip (same), frozen vs v5", s["coinflip"]),
     f"| RejectX / CoinFlip v5 equal to phase 1's published frozen runs | {v['static_equal_phase1_published']} |",
     f"| Baleen pinned training (CP1 G1-det: imap_unordered -> imap, PYTHONHASHSEED=0), frozen vs v5: admission dumps "
     f"(rows {s['pinned_admit_dumps']['n_rows_a']} / {s['pinned_admit_dumps']['n_rows_b']}, same order "
     f"{s['pinned_admit_dumps']['same_row_order']}, df_X {s['pinned_admit_dumps']['df_X_identical']}, df_Y "
     f"{s['pinned_admit_dumps']['df_Y_identical']}), prefetch dumps, model files | dumps identical: "
     f"{v['pinned_dumps_identical']}; all model files byte-identical: {v['pinned_models_identical']}; equal to CP1's "
     f"pinned frozen models: {v['pinned_models_equal_CP1']} |",
     cmp_line("Baleen pipeline: frozen train -> frozen sim vs v5 train -> v5 sim (0_reproduce theta)", s["pinned_pipeline"]),
     cmp_line("Baleen, the same model files (WP2 A r1) through the frozen and the v5 simulator", s["same_models_simF_vs_simV4"]),
     cmp_line("alpha = -1: v4 sim vs v5 sim (WP2 A r1 models, its A+alpha threshold)", s["alpha_v4_vs_v5"]),
     cmp_line("class table (1.2c, identical rows): v4 sim vs v5 sim", s["classtable_v4_vs_v5"]),
     cmp_line("UNION, second model can never admit (D_F1PT r1, kappa = 1e9) on v5 vs alpha on v4", s["union_never_v5_vs_alpha_v4"]),
     cmp_line("UNION of A with itself (kappa = 1, both meta+block+chunk) on v5 vs alpha on v4", s["union_self_v5_vs_alpha_v4"]),
     "", "The only differences are in the echoed `options`, as at CP1/G1_v3 (checked per comparison, "
     "`results/g1v4_summary.json`): values of " + ", ".join(sorted({x for c in s.values() if isinstance(c, dict)
                                                                 for x in c.get("options_differing", [])})) +
     "; flags present only in the overlay: " + ", ".join(sorted({x for c in s.values() if isinstance(c, dict)
                                                                 for x in c.get("options_only_in_b", [])})) + ".",
     "", "## What this shows",
     "- With default flags the v5 simulator and trainer are the frozen artifact (bit-identical results, series, "
     "histograms, counters; byte-identical models under pinned training).",
     "- The v5 edits leave the alpha and class-table paths bit-identical to v4.",
     "- The union path (`NewMLAP._union_accept`) is the single-model mechanism when the second clause cannot fire "
     "(kappa = 1e9, with the longer collected feature vector) and when both clauses are the same model: both reproduce "
     "the A+alpha run bit-for-bit. Union runs differ from single-model runs only through the second model's admissions."]
open(os.path.join(H, "G1_v5.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L[:12]))
