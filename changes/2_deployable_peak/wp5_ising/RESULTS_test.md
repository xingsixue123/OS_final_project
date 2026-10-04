# WP5 -- H2' test result (Ising at tight re-solve budgets), run exactly as pre-registered

Protocol: `PROTOCOL_v2_H2.md` + `results/plan_H2test.json`, committed and pushed as fd54e76 (phase2-deployable-peak,
Oct 3 ~01:15) before any test run. Test runs: Oct 3 01:24:38-01:45:3x, 324/324 runs, cores 0-7, strictly sequential.
Nothing in the configuration, seeds, instances, order or criteria was changed.

## 1. Verdict: **H2' is NOT supported** -- for either finalist, both criteria fail


| finalist | <= best classical: 1 s | 3 s | 10 s | budgets with >= 5/6 | (i) count | mean finalist (18 pairs) | mean best classical (18 pairs) | (ii) average | H2' |
|---|---|---|---|---|---|---|---|---|---|
| pt | 1/6 (strict 0) | 6/6 (strict 5) | 4/6 (strict 2) | 1 | FAIL | 22.7336 | 22.7166 | FAIL | **NOT supported** |
| eim | 0/6 (strict 0) | 5/6 (strict 4) | 3/6 (strict 1) | 1 | FAIL | 22.8413 | 22.7166 | FAIL | **NOT supported** |

- **PT** is <= the best classical method on 1/6 instances at 1 s (the floored Region7 s0.4, a tie), **6/6 at 3 s** and
  4/6 at 10 s -> the count criterion
  (>= 5/6 at >= 2 budgets) holds at only one budget: **(i) FAIL**. Over the 18 (instance, budget) pairs PT averages
  22.7336 vs 22.7166 for the per-cell best classical: **(ii) FAIL** (PT is 0.017 worse; the 1-s cells cost it +0.17 on
  average while it gains 0.11 at 3 s and ties at 10 s).
- **EIM**: 0/6, 5/6, 3/6 -> one budget: **(i) FAIL**; 22.8413 vs 22.7166: **(ii) FAIL**.
- Multiple comparison: irrelevant here (neither finalist passes).
- The outcome is exactly what the dev evaluation predicted (dev: PT 3/8, 7/8, 5/8; mean 22.888 vs 22.864; EIM
  0/8, 8/8, 3/8): the classical true-objective local search (`ls`, hard budget) is the best method at 1 s on every
  test instance; the replica-exchange samplers are best at 3 s; at 10 s PT, LS and CP-SAT are within +-0.3%.

## 2. Per-budget means over the 6 test instances (method mean over its seeds; util %, lower is better)


| method | family | 1 s | 3 s | 10 s |
|---|---|---|---|---|
| pt | Ising finalist | 22.9996 | 22.6008 | 22.6004 |
| eim | Ising finalist | 23.2044 | 22.7158 | 22.6036 |
| lp | classical | 24.6935 | 23.0888 | 23.0888 |
| milp | classical | 24.6690 | 22.8303 | 22.7991 |
| cpsat | classical | 24.6759 | 22.9688 | 22.6382 |
| ls | classical | 22.8335 | 22.7589 | 22.6222 |
| greedy | classical | 32.6532 | 32.6532 | 32.6532 |
| pgreedy | classical | 26.7305 | 26.7305 | 26.7305 |
| best classical per cell | - | 22.8335 | 22.7157 | 22.6006 |

Best classical per cell: 1 s -- LS on 6/6; 3 s -- LS 3, CP-SAT 2, MILP 1; 10 s -- CP-SAT 3, LS 3. Two instances are
floored (Region7 s0.4 at 23.8766 and Region6 s0.5 at 23.6721: PT, EIM, LS and, on Region7 s0.4, CP-SAT reach the same
value), so they count as ties (<=) for whoever reaches the floor.

## 3. Per-cell comparison (protocol section 7; finalist mean over seeds 0-2 vs best classical mean; gap = finalist / classical - 1; "<=" = counts for criterion (i))


| instance | budget | pt (sd) | gap pt | eim (sd) | gap eim | best classical (sd) | method |
|---|---|---|---|---|---|---|---|
| R7_s0.4 | 10 | 23.8766 (0.0000) | +0.000% <= | 23.8766 (0.0000) | +0.000% <= | 23.8766 (0.0000) | cpsat |
| R7_s0.4 | 3 | 23.8766 (0.0000) | +0.000% <= | 23.8766 (0.0000) | +0.000% <= | 23.8766 (0.0000) | cpsat |
| R7_s0.4 | 1 | 23.8766 (0.0000) | +0.000% <= | 23.9321 (0.0308) | +0.233% | 23.8766 (0.0000) | ls |
| R7_s0.5 | 10 | 22.9194 (0.0094) | -0.251% <= | 22.9551 (0.0469) | -0.096% <= | 22.9771 (0.0234) | cpsat |
| R7_s0.5 | 3 | 22.9169 (0.0021) | -0.890% <= | 23.0148 (0.0036) | -0.466% <= | 23.1227 (0.0053) | milp |
| R7_s0.5 | 1 | 23.3735 (0.0371) | +0.731% | 23.6203 (0.0220) | +1.795% | 23.2038 (0.0055) | ls |
| R7_s0.6 | 10 | 22.5940 (0.0055) | -0.078% <= | 22.6294 (0.0095) | +0.079% | 22.6117 (0.0125) | cpsat |
| R7_s0.6 | 3 | 22.5778 (0.0037) | -0.924% <= | 22.6317 (0.0061) | -0.688% <= | 22.7885 (0.0152) | cpsat |
| R7_s0.6 | 1 | 23.2055 (0.0535) | +0.711% | 23.5371 (0.0621) | +2.150% | 23.0417 (0.0028) | ls |
| R6_s0.4 | 10 | 21.8499 (0.0333) | +0.305% | 21.7906 (0.0187) | +0.033% | 21.7835 (0.0063) | ls |
| R6_s0.4 | 3 | 21.8599 (0.0329) | -0.665% <= | 22.3097 (0.2502) | +1.379% | 22.0062 (0.0082) | ls |
| R6_s0.4 | 1 | 22.5431 (0.0432) | +1.830% | 22.8117 (0.1655) | +3.043% | 22.1380 (0.0334) | ls |
| R6_s0.5 | 10 | 23.6721 (0.0000) | +0.000% <= | 23.6721 (0.0000) | +0.000% <= | 23.6721 (0.0000) | ls |
| R6_s0.5 | 3 | 23.6721 (0.0000) | -0.000% <= | 23.6721 (0.0000) | -0.000% <= | 23.6722 (0.0000) | ls |
| R6_s0.5 | 1 | 23.6722 (0.0000) | +0.000% | 23.7000 (0.0433) | +0.118% | 23.6721 (0.0000) | ls |
| R6_s0.6 | 10 | 20.6906 (0.0047) | +0.039% | 20.6976 (0.0209) | +0.072% | 20.6826 (0.0886) | ls |
| R6_s0.6 | 3 | 20.7016 (0.0037) | -0.606% <= | 20.7901 (0.0408) | -0.182% <= | 20.8279 (0.0078) | ls |
| R6_s0.6 | 1 | 21.3268 (0.0536) | +1.223% | 21.6253 (0.1161) | +2.640% | 21.0691 (0.0161) | ls |

## 4. Per-level objectives (mean over the 6 instances and seeds)


| budget | method | L1 | L2 | L3 | L4 | L5 | L6 | L7 | L8 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | pt | 23.548 | 23.304 | 23.133 | 22.967 | 22.827 | 22.774 | 22.740 | 22.706 |
| 1 | eim | 23.809 | 23.433 | 23.227 | 23.157 | 23.116 | 23.040 | 22.958 | 22.894 |
| 1 | lp | 30.776 | 25.161 | 24.359 | 23.930 | 23.601 | 23.364 | 23.253 | 23.104 |
| 1 | milp | 30.770 | 25.155 | 24.349 | 23.911 | 23.618 | 23.362 | 23.232 | 22.955 |
| 1 | cpsat | 30.776 | 25.161 | 24.359 | 23.930 | 23.601 | 23.364 | 23.253 | 22.963 |
| 1 | ls | 23.381 | 23.194 | 23.015 | 22.839 | 22.686 | 22.590 | 22.516 | 22.448 |
| 1 | greedy | 34.046 | 33.731 | 33.385 | 32.979 | 32.427 | 32.012 | 31.678 | 30.968 |
| 1 | pgreedy | 33.825 | 27.067 | 26.582 | 26.357 | 25.494 | 25.106 | 24.813 | 24.602 |
| 3 | pt | 22.967 | 22.785 | 22.667 | 22.592 | 22.534 | 22.465 | 22.410 | 22.387 |
| 3 | eim | 23.644 | 22.865 | 22.721 | 22.622 | 22.552 | 22.482 | 22.433 | 22.408 |
| 3 | lp | 24.604 | 23.233 | 23.172 | 22.903 | 22.827 | 22.744 | 22.623 | 22.605 |
| 3 | milp | 23.330 | 23.162 | 22.925 | 22.829 | 22.712 | 22.621 | 22.556 | 22.508 |
| 3 | cpsat | 24.337 | 23.167 | 22.969 | 22.840 | 22.722 | 22.647 | 22.559 | 22.509 |
| 3 | ls | 23.441 | 23.130 | 22.921 | 22.740 | 22.588 | 22.478 | 22.407 | 22.366 |
| 3 | greedy | 34.046 | 33.731 | 33.385 | 32.979 | 32.427 | 32.012 | 31.678 | 30.968 |
| 3 | pgreedy | 33.825 | 27.067 | 26.582 | 26.357 | 25.494 | 25.106 | 24.813 | 24.602 |
| 10 | pt | 22.861 | 22.776 | 22.692 | 22.610 | 22.561 | 22.498 | 22.425 | 22.380 |
| 10 | eim | 23.091 | 22.814 | 22.657 | 22.562 | 22.493 | 22.434 | 22.396 | 22.382 |
| 10 | lp | 24.604 | 23.233 | 23.172 | 22.903 | 22.827 | 22.744 | 22.623 | 22.605 |
| 10 | milp | 23.669 | 23.054 | 22.846 | 22.750 | 22.635 | 22.525 | 22.481 | 22.433 |
| 10 | cpsat | 23.183 | 22.838 | 22.705 | 22.594 | 22.523 | 22.466 | 22.409 | 22.388 |
| 10 | ls | 23.128 | 22.888 | 22.705 | 22.567 | 22.483 | 22.427 | 22.390 | 22.390 |
| 10 | greedy | 34.046 | 33.731 | 33.385 | 32.979 | 32.427 | 32.012 | 31.678 | 30.968 |
| 10 | pgreedy | 33.825 | 27.067 | 26.582 | 26.357 | 25.494 | 25.106 | 24.813 | 24.602 |

At 1 s, level 1 (65% of B, 2/9 of T) decides the result: LP, MILP and CP-SAT cannot get past the LP rounding there
(30.8), PT and EIM reach 23.5-23.8 and LS 23.4; LS is also best on every later level. At 3 s and 10 s PT's level-1 sets (22.97 / 22.86)
are the best of any method; at the full-budget level LS is best at 3 s (22.37 vs PT 22.39) and PT, EIM, CP-SAT and LS are
within 0.01 at 10 s.

## 5. Wall time, failures, over-budget runs
**324 runs, 324 ok, 0 failed, 0 over budget** (limit 1.05 T + 0.5 s). No re-run was needed.


| budget | method | runs ok | failed | over budget (> 1.05 T + 0.5) | wall min | median | max |
|---|---|---|---|---|---|---|---|
| 1 | pt | 18 | 0 | 0 | 0.993 | 1.087 | 1.148 |
| 1 | eim | 18 | 0 | 0 | 0.998 | 1.131 | 1.239 |
| 1 | lp | 6 | 0 | 0 | 0.366 | 0.468 | 0.599 |
| 1 | milp | 18 | 0 | 0 | 0.333 | 0.853 | 0.874 |
| 1 | cpsat | 18 | 0 | 0 | 0.583 | 0.937 | 0.947 |
| 1 | ls | 18 | 0 | 0 | 0.987 | 1.032 | 1.063 |
| 1 | greedy | 6 | 0 | 0 | 0.050 | 0.123 | 0.144 |
| 1 | pgreedy | 6 | 0 | 0 | 0.054 | 0.112 | 0.154 |
| 3 | pt | 18 | 0 | 0 | 2.981 | 3.080 | 3.160 |
| 3 | eim | 18 | 0 | 0 | 3.004 | 3.028 | 3.065 |
| 3 | lp | 6 | 0 | 0 | 0.303 | 0.664 | 0.773 |
| 3 | milp | 18 | 0 | 0 | 0.908 | 2.266 | 3.543 |
| 3 | cpsat | 18 | 0 | 0 | 1.974 | 2.325 | 2.942 |
| 3 | ls | 18 | 0 | 0 | 3.002 | 3.024 | 3.046 |
| 3 | greedy | 6 | 0 | 0 | 0.072 | 0.119 | 0.145 |
| 3 | pgreedy | 6 | 0 | 0 | 0.066 | 0.143 | 0.192 |
| 10 | pt | 18 | 0 | 0 | 10.004 | 10.014 | 10.024 |
| 10 | eim | 18 | 0 | 0 | 10.003 | 10.034 | 10.078 |
| 10 | lp | 6 | 0 | 0 | 0.303 | 0.668 | 0.791 |
| 10 | milp | 18 | 0 | 0 | 2.615 | 7.645 | 10.443 |
| 10 | cpsat | 18 | 0 | 0 | 1.875 | 5.298 | 9.848 |
| 10 | ls | 18 | 0 | 0 | 10.006 | 10.011 | 10.016 |
| 10 | greedy | 6 | 0 | 0 | 0.044 | 0.097 | 0.124 |
| 10 | pgreedy | 6 | 0 | 0 | 0.073 | 0.103 | 0.174 |

MILP and CP-SAT return before the budget (exact solves of the small later levels; the phase-1 split only carries unused
time forward), as on dev.

## 6. Secondary (pre-declared, no verdict): rolling re-solve at 1 s on the 6 test instances
`src/p2h2roll.py` -> `src/p2roll.py` (6-h windows, 3-h step, commit first half, cumulative write-rate cap; design in
RESULTS_dev.md section 7), seed 0, configurations = plan_H2test.json budget "1"; 48 runs, all ok, 0 windows over
budget (max window wall 1.12 s). Stitched full-trace peak (util %):

| method | R7_s0.4 | R7_s0.5 | R7_s0.6 | R6_s0.4 | R6_s0.5 | R6_s0.6 | mean |
|---|---|---|---|---|---|---|---|
| pt | 26.762 | 27.828 | 27.452 | 26.105 | 27.731 | 25.537 | 26.903 |
| eim | 27.036 | 27.534 | 27.225 | 26.147 | 27.685 | 25.535 | 26.860 |
| ls | 26.904 | 27.462 | 27.139 | 26.011 | 27.490 | 25.435 | 26.740 |
| milp | 26.547 | 26.962 | 26.663 | 25.822 | 27.398 | 25.278 | 26.445 |
| cpsat | 26.508 | 27.026 | 26.660 | 25.821 | 27.417 | 25.207 | 26.440 |
| lp | 26.749 | 27.036 | 27.388 | 25.855 | 27.754 | 25.465 | 26.708 |
| pgreedy | 28.638 | 30.198 | 30.441 | 29.267 | 32.063 | 27.746 | 29.726 |
| greedy | 34.217 | 32.799 | 34.876 | 34.724 | 33.628 | 32.505 | 33.791 |
| best classical | 26.508 (cpsat) | 26.962 (milp) | 26.660 (cpsat) | 25.821 (cpsat) | 27.398 (milp) | 25.207 (cpsat) | 26.426 |

pt: <= best classical on 0/6; mean 26.903 vs 26.426

eim: <= best classical on 0/6; mean 26.860 vs 26.426

One-shot full-trace 1-s solve, peak at f = 1.0 (seed 0, mean of 6): pt 22.738, eim 22.855, ls 22.463, milp 23.012, cpsat 22.951, lp 23.104, pgreedy 24.602, greedy 30.968

windows per run 49-49, episodes per window median 2524 (p10 1951, max 3856); use/B min 0.99996

As on dev, on the small window instances the exact solvers are best (CP-SAT 26.44, MILP 26.45); PT (26.90) and EIM
(26.86) are <= the best classical method on 0/6 instances, and LS (26.74) is also behind the exact solvers. Rolling
costs ~4 util points against the one-shot full-trace solve at the same 1-s budget.

## 7. Foreign-load audit (protocol section 4)
- `core_audit.py` restarted 01:15:47 (`logs/core_audit_h2test.log`, threads using > 5% of a core on logical 0-7
  "DIRECT" or 12-19 "SIBLING", Track-B timing processes excluded). Pre-check at 01:24: no entry since 01:16:37 (Track
  A's sims had drained; every running Track-A sim was pinned to 8-11,20-23).
- **Test runs (01:24:38-01:45:3x): zero audit entries.** Per-run foreign load (`src/audit_load.py`,
  `trials_audit_load_h2test.csv`): mean DIRECT 0.000 and SIBLING 0.000 logical CPUs for all 324 runs (Ising 108,
  classical 216); no run exceeds the 0.5-CPU flag threshold.
- Rolling secondary (01:45:40-02:08:50): one short burst of the unpinned VS Code Pylance server at 01:45:50-01:46:10
  (<= 1 CPU on 0-7 and ~1 CPU-s on 12-19 per 10 s), overlapping the first windows of the first method (PT on Region7
  s0.4); nothing else. Secondary analysis only.

## 8. Integrity
- Pre-registration: PROTOCOL_v2_H2.md and plan_H2test.json committed and pushed (fd54e76) before the first test run;
  the driver (`src/p2h2test.py`) reads instances, budgets, configurations and seeds only from plan_H2test.json, verifies
  the six sha256 values from the protocol, and executes the protocol's order (instance-major; budgets 10, 3, 1;
  per-block `random.Random(zlib.crc32(f"{instance}|{budget:g}"))` shuffle of the plan-ordered (method, seed) list).
  The analysis (`src/p2h2analyze.py`) implements section 7 (over-budget / failed runs would have made a cell +inf;
  none occurred). Two small fixes were made to the analysis script after the runs (a pandas column-access bug and an
  f-string quoting error; no change to any rule) before its first output.
- Hardware: every test run `taskset -c 0-7`, 8 threads, under the exclusive cores lock; logical 12-19 idle (audit).
  TIMING_IDLE was absent during the test (deleted by the coordinator 01:13:42) and re-created at 02:08:54 after the
  last timing run.
- `bash 0_reproduce/check_frozen.sh`: before (01:15:40) **`frozen OK (94 files)`**; after (02:09:12) **`frozen OK
  (94 files)`** (`results/check_frozen_{before,after}_h2test.txt`).
- Leak check (prescribed command, marker `wp5_ising/.leak_marker`): before (01:15) 595 files, after (02:09) 595 files,
  **identical lists -- the test wrote nothing outside P2**. The 595 hits are the same non-Track-B categories as at CP2
  (RESULTS_dev.md section 9): `OS_final_project/.git` objects (318, the coordinator's commits incl. fd54e76),
  `<another project>` (224, an unrelated user project), `<home cache>` (33, that project's
  model), `changes/SCOPE_v2.md` (coordinator), desktop/login files. Lists: `results/leak_check_{before,after}_h2test.txt`.
- No commit by Track B.

## 9. Files
`trials.csv` (phase `h2test`, 324 rows), `sols/h2test_*` (every solution), `results/h2test_cells.csv`,
`results/h2test_comparisons.csv`, `results/h2test_summary.md`, `results/h2test_verdict.json`,
`trials_audit_load_h2test.csv`, `logs/core_audit_h2test.log`, `logs/h2test.log`, `results/rolling_test.csv`,
`results/rolling_test_summary.md`, `src/p2h2test.py`, `src/p2h2roll.py`, `src/p2h2analyze.py`.
