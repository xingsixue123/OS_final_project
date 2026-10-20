# T1 results: union finalist XA-F1PT on Region2 s0.1–0.6 (PROTOCOL.md, commit `76cf5c8d`)

**Verdict: T1 is SPENT and FAILED: unevaluable as pre-registered.**
- **Why unevaluable:**
  - Region2_s0.2 cannot reach the target write rate for any arm;
  - reference arm A is short of 3 matched retrains on s0.1 and s0.5 after the pre-registered seeds 4–6.
  - So the contract §4 rule cannot be computed: `code/validate.py:check_claim` stops at "< 3 matched retrains", and `eval_test.py` wrote `results_test/evaluation.json` with `missing` and no `good_result`.
- **Fail-closed decision** (`result/LAB_NOTEBOOK.md`, 07:05 entry, committed `539f39e` before `evaluation.json` was opened):
  - s0.2 stays in the pool and `matched` is not relaxed;
  - no seed beyond 6 is run;
  - T1 is not re-registered or re-spent;
  - no subset reading is a pass.
- **The descriptive numbers below do not favour Y either.**

**Run:** TEST_GO 06:26:50 → CHAIN_DONE 07:03:10 (`work/union/src/chain_test_t1u.sh`).
- 132 evaluations (seeds 1–6 where needed), 0 `__FAILED_` rows, every row kept: `trials_test.csv`.
- Code: overlay v5, G1_v5 PASS (`work/union/G1_v5.md`).

## 1. Matched / total retrains per (arm, instance) (matched = WR within 35.599 ± 1%)
| arm | s0.1 | s0.2 | s0.3 | s0.4 | s0.5 | s0.6 |
|---|---|---|---|---|---|---|
| Y = XA-F1PT | 3/3 | **0/6** | 3/3 | 3/3 | 3/3 | 3/3 |
| control = XA-F1CPSAT | 3/3 | **0/6** | 3/3 | 3/3 | 3/3 | 3/3 |
| A | **0/6** | **0/6** | 3/3 | 3/3 | **2/6** | 3/3 |
| B | 3/3 | **0/6** | 3/3 | 3/3 | 3/3 | 3/3 |
| A+α (`Aa-1.0`) | 3/3 | **0/6** | 3/3 | 3/3 | 3/3 | 3/3 |
| B+α (`Ba-1.0`) | 3/3 | **0/6** | 3/3 | 3/3 | 3/3 | 3/3 |

**Unmatched rows (means over the cell's rows):**

| arm | instance | WR | P100 | θ |
|---|---|---|---|---|
| every arm | s0.2 | 11.510 | 189.068 | 1e-4 (the search floor: admit everything) |
| A | s0.1 | 35.538 (each row off the band) | 9.702 | 0.549 |
| A | s0.5 | 35.906 | 8.738 | 0.619 |

- **s0.2:** at admit-all the write rate does not depend on the model, so no seed can match it. The constructed s0.2 job equals s0.1's except for the trace. The authors' release has no s0.2 row at the operating point (DWPD 7.5, 366.47 GB) for any policy, and its day-1 instance has 164 episodes, against 1285–1984 for the other instances (label statistics `n`). The F1 solvers can use only 31% of the day-1 budget (`use_frac` 0.31) and return Baleen's own labels. This was foreseeable before the protocol commit and was not checked (disclosed in LAB_NOTEBOOK 07:05).
- **A on s0.1 and s0.5:** write-rate cliffs, e.g. s0.1 r2 37.21 → 34.28 MB/s between θ 0.553273 and 0.553671. The pre-registered WP9/WP10 search (false position, at most 7 sims) approaches from one side.

**Convergence ledger** (`results_test/converge/*.csv`):
- Sims per cell: A s0.1 42 (6 rows), A s0.5 35 (6 rows); every s0.2 cell 42 (6 rows); the other cells 3–14.
- Repeated-θ rounds (the stall in `next_theta`, validator N1): 30 per arm on s0.2 (harmless there); 2 in A s0.5; 0 elsewhere.
- The search code is the pre-registered one and was not changed.

## 2. Descriptive only (NOT the pre-registered rule; non-confirmatory; never a pass)
Mean P100 over matched retrains (lower is better; util %):

| instance | A | B | A+α | B+α | Y = XA-F1PT | control XA-F1CPSAT |
|---|---|---|---|---|---|---|
| s0.1 | n/a (0 matched) | 9.659 | 10.195 | 10.007 | 9.637 | 9.853 |
| s0.2 | n/a | n/a | n/a | n/a | n/a | n/a |
| s0.3 | 11.052 | 11.035 | 11.115 | 10.977 | 11.331 | 11.295 |
| s0.4 | 11.626 | 11.626 | 11.359 | 11.378 | 11.378 | 11.359 |
| s0.5 | 8.709 (2 matched) | 8.658 | 8.800 | 8.710 | 8.800 | 8.853 |
| s0.6 | 9.632 | 9.483 | 9.477 | 9.474 | 9.476 | 9.477 |

On s0.3–s0.6, the only instances where every arm has at least one matched row:
- Y 10.246 vs A 10.255, B 10.201, A+α 10.188, B+α 10.135, control 10.246.
- Y wins 2/4 vs A (mean R − Y +0.009), 2/4 vs B (−0.045), 1/4 vs A+α (−0.058), 0/4 vs B+α (−0.111), 2/4 vs control (−0.000).

**No reading of T1 favours Y. The T1 failure is not an artefact of s0.2.**

**Region2 is very low-load.**
- Baleen's peak is ≈ 10 util-% (vs 36–43 on Regions 5–7) and mean DT ≈ 3.8–4.0.
- Peaks are not big-offset scans: their big-offset share is 0.006–0.009, vs 0.33 for A+α on Region6.
- The union's mechanism (admitting scans at peak) has nothing to act on, and the α arms do not help either. This matches WP10's Region1 finding.

**Secondary metrics** (matched rows):

| arm | P99 | top-5 | mean DT | first-access adm | peak-window adm |
|---|---|---|---|---|---|
| A | 8.97 | 9.53 | 4.05 | 15.4% | 0.69 |
| B | 8.51 | 9.07 | 3.77 | 18.9% | 0.73 |
| A+α | 8.37 | 8.98 | 3.84 | 20.6% | 0.81 |
| B+α | 8.50 | 9.00 | 3.81 | 20.4% | 0.80 |
| Y | 8.49 | 9.09 | 3.92 | 21.3% | 0.82 |
| control | 8.39 | 9.01 | 3.89 | 21.1% | 0.79 |

## 3. Static baselines (`results_test/static_baselines.csv`, frozen code): uninformative on T1
| instance | RejectX P100 | RejectX WR | matched | CoinFlip P100 | CoinFlip WR | matched |
|---|---|---|---|---|---|---|
| s0.1 | 15.01 | 21.18 | no | 17.63 | 35.61 | yes |
| s0.2 | 240.64 | 2.00 | no | 223.72 | 11.13 (probability pushed to 1.18; `prep.py` does not clamp it) | no |
| s0.3 | 16.35 | 36.47 | no | 18.28 | 35.58 | yes |
| s0.4 | 15.83 | 31.68 | no | 17.98 | 35.60 | yes |
| s0.5 | 12.71 | 25.36 | no | 16.13 | 35.60 | yes |
| s0.6 | 21.38 | 29.32 | no | 26.26 | 35.61 | yes |

- **RejectX cannot be matched on Region2.**
  - The authors' `20230410_static_pf` RejectX rows use a window factor ≈ 1e5, so the window is effectively unbounded, and the protocol's knob (`--ap-probability` = the window factor) does not move the write rate.
  - With X = 1, the write rate is capped below the target on 5 of 6 instances.
  - The supplementary, non-protocol replay (`results_test/supp_rejectx.csv`: the window factor bisected in log space) matches only s0.3 (WR 35.78, P100 16.35). It is reported only and never substituted.
- `validate.py` and `eval_test.py` average static P100 regardless of `matched`, so the condition "below RejectX/CoinFlip" would be trivially met through s0.2. It carries no information on T1.

## 4. Ising vs classical labels on the test pool (training-day data; validator N4)
- The F1 objective (`label_peak_util`) is **identical for PT and CP-SAT on all 36 Region2 label solves** (6 instances × 6 seeds).
- The label sets differ only among co-optimal solutions:
  - Jaccard with Baleen's labels: PT 0.41–0.88; CP-SAT 0.80–0.92 (s0.2: 1.00 for both, i.e. Baleen's own labels);
  - PT's sets vary by seed; CP-SAT's barely do.
- Y and its control are tied on T1 (descriptive, s0.3–s0.6: 10.246 vs 10.246). **No difference is attributed to better Ising optimization.**

## 5. Integrity
- **Base-model race audit (validator N2):** all 27 `logs/test/A_baleen_Region2_*/train.log` (seeds 1–6) used `--ap-feat-subset meta+block+chunk`. The race did not fire.
- **No row dropped.** Every evaluation, including all unmatched rows and seeds 4–6, is in `trials_test.csv` (132 rows; snapshot committed in `f27cdc2`).
- `check_frozen`: `frozen OK (94 files)` (`results_test/integrity.txt`, 07:03:10). PATCH_v5.diff sha256 `3cadbdf4a638`.
