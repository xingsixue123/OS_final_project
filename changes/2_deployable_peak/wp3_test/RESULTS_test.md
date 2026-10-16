# WP3 results: H3′ test (PROTOCOL_v2_H3, committed `cba9970`)

**Test instances:** Region7/Region6 (20230325, 0.1%) × samples 0.4, 0.5, 0.6, touched once.
**Run:** launched 2026-10-05 after G3 was waived by the captain (`SCOPE_v2.md` §1a); 126 evaluations, **126 matched, 0 unmatched, 0 failed**, so no extra-retrain pass was needed. Evaluation: `src/evaluate_test.py` (written before any test data existed) → `results/evaluation.json`.

## 0. Verdict

| judgement (PROTOCOL §5) | result |
|---|---|
| **H3′** (X1 vs A and vs B) | **NO.** X1 wins 5/6 against both, but its mean is worse: A − X1 = −1.27, B − X1 = −1.36 |
| X1 below RejectX / CoinFlip | yes, barely: 40.53 vs 40.73 / 48.64 |
| **H3′-labels** (X1 vs A+α, B+α) | **NO.** 3/6 wins each; mean −2.23 / −2.15 |
| X2 (secondary) | NO. 4/6 wins; mean −1.61 / −1.70; not below RejectX (40.88) |
| Dc+α vs X1 (no pass/fail) | CP-SAT labels better by 0.89 (3/6; instance SE 0.84) |

**The pre-registered deployability claim for Ising peak-aware labels fails on the test set.** The dev result (X1 37.20 vs A 38.50) did not transfer.

## 1. P100 per instance (mean of 3 matched retrains; lower is better)

| instance | A | B | A+α | B+α | X1 = Ea-1.0:F1PT | X2 = Ea-0.5:F1PT | Dc+α = Ea-1.0:F1CPSAT | RejectX | CoinFlip |
|---|---|---|---|---|---|---|---|---|---|
| Region6 s0.4 | 37.58 | 37.43 | 36.12 | 36.57 | 36.93 | 37.36 | 37.36 | 38.56 | 45.07 |
| Region6 s0.5 | 38.75 | 38.95 | 37.50 | 38.17 | 37.24 | 38.00 | 37.61 | 37.96 | 44.68 |
| Region6 s0.6 | 43.04 | 42.94 | 43.79 | 42.72 | 42.02 | 42.01 | 41.91 | 47.21 | 58.04 |
| Region7 s0.4 | 39.51 | 39.86 | 38.66 | 38.71 | 37.20 | 37.78 | 37.57 | 39.29 | 49.24 |
| Region7 s0.5 | 39.07 | 38.31 | 36.95 | 37.05 | **52.30** | **52.15** | 47.49 | 42.05 | 51.60 |
| Region7 s0.6 | 37.65 | 37.55 | 36.80 | 37.05 | 37.51 | 37.96 | 35.91 | 39.31 | 43.19 |
| **mean** | 39.27 | 39.17 | **38.30** | 38.38 | 40.53 | 40.88 | 39.64 | 40.73 | 48.64 |

**Comparisons** (improvement = ref − X; SE as PROTOCOL §5, retrain-level / instance-level):

| X vs ref | wins | mean | SE retrain / instance |
|---|---|---|---|
| X1 vs A | 5/6 | −1.27 | 0.15 / 2.41 |
| X1 vs B | 5/6 | −1.36 | 0.17 / 2.55 |
| X1 vs A+α | 3/6 | −2.23 | 0.21 / 2.66 |
| X1 vs B+α | 3/6 | −2.15 | 0.27 / 2.64 |
| X1 vs Dc+α | 3/6 | −0.89 | 0.36 / 0.84 |
| X2 vs A | 4/6 | −1.61 | 0.21 / 2.31 |
| X2 vs B | 4/6 | −1.70 | 0.22 / 2.45 |

## 2. What went wrong: one catastrophic instance (diagnosis, not a re-analysis)

- **On five of six instances** X1 is below A, by 0.1–2.3. **On Region7 s0.5** all three X1 retrains land at 51.7–52.8, above even RejectX (42.05). That single cell turns the mean.
- **Mechanism.** The simulated peak window (378) of Region7 s0.5 is a **big-offset sequential scan**: 48% of its accesses end beyond 8 MB, for every arm.
  - Baleen-label models admit 56–69% of that window's accesses (A, A+α).
  - The F1-label models admit only 4–14% (X1, X2) and 10–34% (CP-SAT labels).
  - The scan stays uncached, and the peak rises by about 13 points.
- **Why the F1 labels miss it.** Day-1 F1 labels are selected for Region7's day-1 peak windows, which are not scans. The GBM therefore learns that big-offset episodes are not worth admitting. On dev, F1 labels helped exactly on scan peaks (Region6, `RESULTS_dev.md` §7), because those scans were present on day 1.
- **The known Region7 failure mode persists:** first-access admission 1.8–1.9% for the F1 arms vs 4.1–4.8% for Baleen's; mean DT 21.5–21.6 vs 20.9–21.1.
- **Diagnosis:** min-max labels fitted to one day's peak are brittle when the peak *type* changes. Track C (`wp8_trackC`, Baleen-anchored and top-k/robust objectives) targets exactly this; it is dev-only and does not read these results.

## 3. Post-hoc observations (NOT pre-registered; no claim; hypotheses for a new pre-registration)

- **The load-adaptive threshold on Baleen's own models helps consistently:**
  - A+α vs A: 5/6, +0.96 (retrain SE 0.16; instance SE 0.39);
  - B+α vs B: 6/6, +0.79 (0.24 / 0.16);
  - A+α vs B: 5/6, +0.87.

  It is the best test configuration (38.30, −2.5% vs Baleen), and it was a positive control on dev as well (A+α +0.62 vs A). Because it was a control here and not the hypothesis, it needs its own pre-registered test (fresh region or reserve) before any claim.
- **Excluding Region7 s0.5** (for description only), the means are A 39.31, A+α 38.57, X1 38.18, Dc+α 38.07. The F1 arms' gain on the other five instances is real but small, and cannot be separated from the tail risk.

## 4. Secondary metrics (means over all matched retrains)

| config | P100 | P99 | top-5 | mean DT | WR | first-access adm. | peak-window adm. |
|---|---|---|---|---|---|---|---|
| A | 39.27 | 31.96 | 36.02 | 21.01 | 35.60 | 4.1% | 0.39 |
| B | 39.17 | 31.84 | 35.85 | 20.93 | 35.50 | 4.8% | 0.35 |
| A+α | 38.30 | 31.70 | 35.55 | 21.14 | 35.59 | 4.3% | 0.45 |
| B+α | 38.38 | 31.46 | 35.47 | 21.09 | 35.62 | 4.4% | 0.41 |
| X1 | 40.53 | 31.82 | 36.02 | 21.57 | 35.53 | 1.9% | 0.35 |
| X2 | 40.88 | 31.86 | 36.13 | 21.46 | 35.55 | 1.8% | 0.33 |
| Dc+α | 39.64 | 31.84 | 35.51 | 21.54 | 35.64 | 1.8% | 0.34 |

**Retention** R = (A − X)/(OPT_peak-blind − OPT_peak-aware), with the WP1 offline OPT values: X1 −0.28, X2 −0.33, B +0.02, A+α +0.16, B+α +0.15, Dc+α −0.12.

## 5. Integrity (2026-10-16)
- `check_frozen.sh`: `frozen OK (94 files)`.
- Nothing under `0_reproduce/` or `1_literature_review/` (envs excluded) is newer than `G3_SIGNED`.
- No `__pycache__` in the overlay or the work tree. `PATCH.diff` sha256 `2a914eb589bb`, unchanged.
- Every process ran under the WP3 sandbox (`env.sh`, bwrap private `/tmp`, train lock); the test configuration was not changed after launch.
- All 126 rows are in `trials.csv`; none is excluded.
