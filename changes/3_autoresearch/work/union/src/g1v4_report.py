"""Write G1_v4.md from results/g1v4_summary.json (src/g1v4.py)."""
import json
import os

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(H, "results", "g1v4_summary.json")))
v, s = S["verdict"], S["summary"]


def yes(b):
    return "**bit-identical**" if b else "**DIFFERENT**"


def cmp_line(name, c):
    return (f"| {name} | {yes(c['all_results_and_series_identical'])}: {c['n_result_keys']} result keys "
            f"(differing: {len(c['result_keys_differing'])}), {c['n_batches']} per-window series (differing: "
            f"{len(c['batches_differing'])}), {c['n_freq']} histograms (differing: {len(c['freq_differing'])}), "
            f"counters differing: {len(c['counters_differing'])}. P100 {c['p100_a']!r} vs {c['p100_b']!r}, "
            f"WR {c['wr_a']:.6f} vs {c['wr_b']:.6f} |")


L = ["# G1_v4: default equivalence of overlay v4 + the class-table checks (Region7 s0, dev)", "",
     "Driver `src/g1v4.py` (copied from `wp10_schedule/src/g1v3.py`; comparison code unchanged). Overlay v4 = "
     "`overlay/BCacheSim` rebuilt by `rebuild_overlay_v4.sh` from `PATCH_v4.diff` (9 files) = WP10 `PATCH_v3.diff` "
     "+ `PATCH_v4_delta.diff` (2 files: `cachesim/load_features.py`, `cachesim/admission_policies.py`). The frozen code "
     "is `0_reproduce/baleen_code`; overlay v3 (`overlay_v3/`, rebuilt from PATCH_v3.diff, identical to WP10's) for "
     "the v4 == v3 checks. Every process ran as `taskset -c 0-23 bwrap ... --bind <private tmp> /tmp`; trains under "
     "the shared train lock. Full numbers: `results/g1v4_summary.json`.", "",
     f"## Verdict: **G1_v4 {'PASS' if v['G1_v4_pass'] else 'FAIL'}; v4 adaptive paths "
     f"{'PASS' if v['v4_adaptive_paths_pass'] else 'FAIL'}**", "",
     "| check | result |", "|---|---|",
     cmp_line("RejectX (authors' static_pf command), frozen sim vs v4 sim", s["rejectx"]),
     cmp_line("CoinFlip (same), frozen vs v4", s["coinflip"]),
     f"| RejectX / CoinFlip v4 equal to phase 1's published frozen runs | {v['static_equal_phase1_published']} |",
     f"| Baleen pinned training (CP1 G1-det: imap_unordered -> imap, PYTHONHASHSEED=0), frozen vs v4: admission dumps "
     f"(rows {s['pinned_admit_dumps']['n_rows_a']} / {s['pinned_admit_dumps']['n_rows_b']}, same order "
     f"{s['pinned_admit_dumps']['same_row_order']}, df_X {s['pinned_admit_dumps']['df_X_identical']}, df_Y "
     f"{s['pinned_admit_dumps']['df_Y_identical']}), prefetch dumps, model files | dumps identical: "
     f"{v['pinned_dumps_identical']}; all model files byte-identical: {v['pinned_models_identical']}; equal to CP1's "
     f"pinned frozen models: {v['pinned_models_equal_CP1']} |",
     cmp_line("Baleen pipeline: frozen train -> frozen sim vs v4 train -> v4 sim (0_reproduce theta)", s["pinned_pipeline"]),
     cmp_line("Baleen, the same model files (WP2 A r1) through the frozen and the v4 simulator", s["same_models_simF_vs_simV4"]),
     cmp_line("alpha = -1: v3 sim vs v4 sim (WP2 A r1 models, its A+alpha threshold)", s["alpha_v3_vs_v4"]),
     cmp_line("exact power-law TABLE (1.2b): v3 sim vs v4 sim", s["table_v3_vs_v4"]),
     cmp_line("CLASS TABLE with identical class rows (1.2c) on v4 vs the 1.2b table on v3", s["classtable_v4_vs_table_v3"]),
     cmp_line("1.2b exact table vs alpha = -1 (both v3; repeats G1_v3's table == power law)", s["table_v3_vs_alpha_v3"]),
     "", "The only differences are in the echoed `options`, as at CP1/G1_v3 (checked per comparison, "
     "`results/g1v4_summary.json`): values of " + ", ".join(sorted({x for c in s.values() if isinstance(c, dict)
                                                                 for x in c.get("options_differing", [])})) +
     "; flags present only in the overlay: " + ", ".join(sorted({x for c in s.values() if isinstance(c, dict)
                                                                 for x in c.get("options_only_in_b", [])})) + ".",
     "", "## What this shows",
     "- With default flags the v4 simulator and trainer are the frozen artifact (bit-identical results, series, "
     "histograms, counters; byte-identical models under pinned training).",
     "- The v4 edit of `NewMLAP.batchAccept` leaves the alpha and 1.2b-table paths bit-identical to v3.",
     "- The class-table code path (`LoadClassTableThreshold.g_item`, class index from the access's own feature "
     "vector) is the same mechanism as the 1.2b table: equal class rows reproduce the table run bit-for-bit. Class "
     "tables differ from 1.2b tables only in their values."]
open(os.path.join(H, "G1_v4.md"), "w").write("\n".join(L) + "\n")
print("\n".join(L[:12]))
