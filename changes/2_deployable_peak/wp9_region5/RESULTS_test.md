# WP9 results: Region5 fresh deployed test (PROTOCOL_v2_H4, committed `c8f655a`)

**Test instances:** Region5 (20230325, 0.1%), samples 0.1–0.6, touched once. Reserve 0.7–0.9 untouched.
**Run:** 2026-10-16 to 2026-10-17 05:31; 90 evaluations, **90 matched, 0 unmatched, 0 failed**.
**Evaluation:** `src/evaluate_test.py`, written and checked on WP3's trials before the test, run automatically when the driver exited (`logs/post_eval.out`) → `results/evaluation.json`.

## 0. Verdict

| judgement | result |
|---|---|
| **H4: A+α beats A and B** | **YES.** vs A: 5/6, +1.16 (retrain SE 0.09, instance SE 0.75). vs B: 5/6, +1.35 (0.08 / 0.94). Mean 35.02, below RejectX (39.35; low side 39.28) and CoinFlip (44.47) |
| B+α vs A and B (secondary) | rule met. 6/6, +1.70 (0.22 / 1.19) and 6/6, +1.89 (0.22 / 1.40); mean 34.48 |
| X1 (Ising record, no pass/fail) | fails the rule. vs A 3/6, −1.92; vs B 2/6, −1.73; vs A+α 2/6, −3.07 |

**The load-adaptive admission threshold (scope v2 §1.2) lowers deployed peak load on a fresh region**, on Baleen's own models: −3.2% (A+α) and −4.7% (B+α) vs Baleen.
- Its first appearance (WP3) was post-hoc. This is its pre-registered confirmation.
- **Caveat: the gain is concentrated.** On Region5 s0.5, A+α is 4.76 below A. On the other five instances the differences are −0.24 to +1.19. The instance-level SE (0.75) is much larger than the retrain-level SE that the rule uses. B+α is more uniform (6/6).

**The Ising-label configuration X1 fails again**, by the same mechanism as in WP3: one catastrophic instance (s0.5: 51.46 vs A 42.72).

## 1. P100 per instance (mean of 3 matched retrains; lower is better)

| instance | A | B | A+α | B+α | X1 | RejectX* | CoinFlip |
|---|---|---|---|---|---|---|---|
| s0.1 | 39.92 | 40.36 | 39.32 | 39.55 | 40.89 | 46.69 | 46.96 |
| s0.2 | 33.92 | 33.79 | 34.16 | 33.51 | 33.22 | 36.08 | 37.87 |
| s0.3 | 37.72 | 37.94 | 37.47 | 37.28 | 36.00 | 39.68 | 46.75 |
| s0.4 | 26.39 | 26.18 | 26.02 | 25.95 | 26.22 | 28.12 | 29.21 |
| s0.5 | 42.72 | 43.91 | 37.96 | **35.07** | **51.46** | 46.05 | 61.36 |
| s0.6 | 36.38 | 36.02 | 35.19 | 35.51 | 40.78 | 39.50 | 44.67 |
| **mean** | 36.17 | 36.37 | **35.02** | **34.48** | 38.09 | 39.35 | 44.47 |

\* RejectX: the authors' probabilities, replayed by the frozen code (equal to the authors' P100). Only s0.4 is matched to ±1% WR; on the others, WR jumps across the target between adjacent probabilities. PROTOCOL §5 therefore compares against both the authors' replays and the replays just below the jump (mean 39.28).

## 2. Secondary metrics (means over matched retrains)

| config | P99 | top-5 | mean DT | WR | first-access adm. | peak-window adm. | peak big-offset share |
|---|---|---|---|---|---|---|---|
| A | 29.09 | 32.46 | 18.80 | 35.52 | 3.8% | 0.37 | 0.27 |
| B | 29.20 | 32.43 | 18.78 | 35.53 | 3.0% | 0.36 | 0.28 |
| A+α | 28.79 | 31.81 | 18.85 | 35.55 | 4.1% | 0.47 | 0.24 |
| B+α | 28.91 | 31.74 | 18.83 | 35.57 | 3.6% | 0.43 | 0.28 |
| X1 | 29.00 | 32.79 | 19.61 | 35.57 | 2.2% | 0.42 | 0.29 |

- The threshold arms raise peak-window admission (0.43–0.47 vs 0.36–0.37) at almost unchanged mean DT (+0.05).
- That is the intended mechanism: spend the write budget when demand is high.
- X1's labels again cut first-access admission and raise mean DT by 0.8.

**Retention** (WP1 offline OPT): A+α 0.31, B+α 0.46, B −0.05, X1 −0.54.

## 3. Integrity (2026-10-19)
- `check_frozen.sh`: `frozen OK (94 files)`. `PATCH.diff` sha256 `2a914eb589bb`, unchanged.
- Under `0_reproduce/` and `1_literature_review/`, nothing is newer than `.leak_marker` except the known foreign cpython-312/313 `.pyc` files dated 2026-10-10 (not from this project; left in place).
- **Sandbox as in WP3:** `env.sh`, bwrap with a private `/tmp`, and the train lock.
- A foreign job of `<another project>` shared the CPUs. It made sims slower but cannot change results.
- All 90 rows are in `trials.csv`; none excluded.
