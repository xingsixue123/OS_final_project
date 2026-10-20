# T2 results: union finalist XA-F1PT on Region4 s0.2–0.6 (PROTOCOL.md, commit `1cda6af`)

**Verdict: T2 FAILED the contract §4 rule.**
- Y = XA-F1PT beats Baleen A and B by a wide margin.
- It does **not** beat the best α arm (A+α): 1/5 wins, mean −0.30. Its gain over Baleen on Region4 is the load-adaptive threshold's.
- With T1 failed (unevaluable), **the test budget (2 of 2) is exhausted.**

**Run:**
- TEST_GO at 07:05:04 (written by `work/union_t2/src/chain_test_t2u.sh` after `ADDENDUM_T1_UNEVALUABLE.md`, `3fdba1b`); CHAIN_DONE at 10:00:33.
- 98 ledger rows: 90 evaluations, plus 8 `__FAILED_` rows from the 07:05–07:07 operational incident (missing emulator cache dir; pre-simulation; same retrains re-run; `result/LAB_NOTEBOOK.md`).
- Every cell has 3/3 matched retrains, so no extra seed was needed.
- Code: overlay v5, G1_v5 PASS (`work/union/G1_v5.md`). Evaluator: `work/union_t2/src/eval_test.py` → `results_test/evaluation.json`.

## 1. Pass rule (pre-registered; n = 5; wins ≥ 4; margin > 2.5 SE_retrain; tail ≥ −2.0)
| Y vs R | wins | mean(R − Y) | SE_retrain | 2.5 SE | worst | rule |
|---|---|---|---|---|---|---|
| A | 4/5 | +7.547 | 1.028 | 2.569 | −0.078 | ok |
| B | 5/5 | +13.541 | 1.691 | 4.227 | +1.121 | ok |
| **best α = A+α** (42.87 < B+α 43.87) | **1/5** | **−0.300** | 1.117 | 2.791 | −0.909 | **FAIL** (wins, margin) |

Static baselines: Y (43.17) is below RejectX (65.84) and CoinFlip (68.84). All 10 static replays are matched at the authors' probability (RejectX factors 0.16–0.32, where the knob works). **good_result = false.**

## 2. P100 per instance (mean of 3 matched retrains; lower is better)
| instance | A | B | A+α | B+α | **Y = XA-F1PT** | control XA-F1CPSAT | RejectX | CoinFlip |
|---|---|---|---|---|---|---|---|---|
| s0.2 | 59.07 | 58.88 | 49.58 | 50.85 | 49.61 | 55.05 | 58.31 | 64.52 |
| s0.3 | 76.14 | 75.99 | 48.95 | 51.38 | 49.37 | 51.23 | 77.09 | 83.26 |
| s0.4 | 51.72 | 59.60 | 51.60 | 51.15 | 51.22 | 50.96 | 73.35 | 74.19 |
| s0.5 | 32.85 | 55.25 | 32.41 | 33.45 | 32.93 | 32.60 | 55.84 | 56.74 |
| s0.6 | 33.81 | 33.84 | 31.81 | 32.49 | 32.72 | 32.00 | 64.59 | 65.48 |
| **mean** | 50.72 | 56.71 | **42.87** | 43.87 | **43.17** | 44.37 | 65.84 | 68.84 |

**Per retrain (r1 / r2 / r3):**
- Y: s0.2 46.67 / 42.87 / 59.28 (sd 8.59); s0.3 50.60 / 50.46 / 47.05; s0.4 50.98 / 50.84 / 51.85; s0.5 32.64 / 33.05 / 33.10; s0.6 32.83 / 31.88 / 33.46.
- A+α: s0.2 46.29 / 52.68 / 49.77; s0.3 50.04 / 46.59 / 50.23; s0.4 51.52 / 51.69 / 51.57; s0.5 32.56 / 32.37 / 32.31; s0.6 31.43 / 32.20 / 31.81.
- B: s0.4 has one collapsed retrain (73.03), and s0.5 is 55.1–55.3 on every retrain (vs A 32.9). B's models are poor on Region4.

**Y − A+α per instance:** s0.2 +0.03, s0.3 +0.42, s0.4 −0.37 (Y better), s0.5 +0.52, s0.6 +0.91.

## 3. Mechanism (matched means)
| arm | P99 | top-5 | mean DT | first-access adm | peak-window adm | peak big-offset share |
|---|---|---|---|---|---|---|
| A | 38.97 | 46.98 | 21.31 | 0.2% | 0.25 | 0.032 |
| B | 41.05 | 51.07 | 21.41 | 0.3% | 0.21 | 0.023 |
| A+α | 36.05 | 40.33 | 21.90 | 2.4% | 0.41 | 0.029 |
| B+α | 36.09 | 40.79 | 21.90 | 2.9% | 0.32 | 0.032 |
| Y | 36.34 | 40.83 | 22.08 | 2.7% | 0.31 | 0.034 |
| control | 36.10 | 41.37 | 22.07 | 2.8% | 0.35 | 0.031 |

- Region4's peaks are high-load bursts, not big-offset scans: the peak window's big-offset share is 0.02–0.04 for every arm, against 0.33 for A+α on dev Region6.
- The load-adaptive threshold does almost all the work: A 50.72 → A+α 42.87, −15%, which confirms H4 on a fresh region, not pre-registered as H4 here.
- The union's second model (F1 peak labels) targets scan admission at peaks, so it has nothing to add. Y lands at A+α's level, with slightly lower peak-window admission (0.31 vs 0.41).

## 4. Ising vs classical
- The F1 objective (`label_peak_util`) is **identical for PT and CP-SAT on all 30 Region4 label solves** (5 instances × 6 seeds). The label sets differ only among co-optimal solutions (Jaccard with Baleen's labels: PT 0.22–0.73, CP-SAT 0.61–0.74).
- Y vs control: 2/5 wins, mean +1.20, carried by s0.2, where Y's r3 = 59.28 against the control's ≈ 54–56 on all retrains. Not significant, and not attributable to better optimization.

## 5. Integrity
- **Base-model race audit (validator N2):** all 15 `work/union_t2/logs/test/A_baleen_Region4_*/train.log` used `--ap-feat-subset meta+block+chunk`.
- **Convergence:** 4–10 sims per cell over 3 retrains; 0 repeated-θ rounds; 0 unmatched rows.
- `check_frozen`: `frozen OK (94 files)` (`results_test/integrity.txt`, 10:00:33). PATCH_v5.diff sha256 `3cadbdf4a638`.
- **No row dropped:** 98 rows in `trials_test.csv`, including the 8 incident rows.
- **Protocol:** PROTOCOL.md is unchanged since `1cda6af`. The only post-commit change is the chain's T1 condition (`ADDENDUM_T1_UNEVALUABLE.md`), committed before TEST_GO.
