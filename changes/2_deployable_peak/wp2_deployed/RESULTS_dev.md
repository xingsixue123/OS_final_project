# WP2 results on DEV: the deployed 2×2 study, ablations and finalists (Track A, CP2)

**Dev instances:** Region7 and Region6 (20230325, 0.1%) × samples 0, 0.1, 0.2 and 0.3 (8 instances). Nothing was run on samples ≥ 0.4.

**Code base:** everything ran through the reviewed overlay (`wp0_overlay/overlay`, PATCH.diff 9 files, +217/−6, sha256 `2a914eb5…`, unchanged during WP2).

**Runs:** 2026-10-01 16:25 to 2026-10-04 09:12, interrupted twice by session ends; every run was resumed without loss.
- **CPUs:** 8-11,20-23 with ≤ 6 sims, or 0-23 with ≤ 14 sims while `TIMING_IDLE` existed.
- **Totals:** 388 evaluations (one per retrain) and 1,075 full simulations. 348 matched, 40 unmatched (all reported, §8), 0 failed.
- **Files:** `trials.csv` (every row), `results/` (summaries), `PROGRESS.md` (log, finalist rule, RESUME).

## 0. Verdict at CP2

**The learnability gate passes (§2).** With `load`, the GBM fits Ising/F1 peak-aware day-1 labels much better than without, net of a shuffled-load control. Validation logloss improves by 0.041 ± 0.006 (F1PT); for Baleen's own labels the gain is 0.001 ± 0.001.

**The plain 2×2 hypothesis (arm D: Ising labels + `load`) does not survive confirmation.**
- Screened with 1 retrain, D:F1PT looked best (S = +0.24).
- With 3 retrains its finalist score is S = −0.14: P100 38.37 vs A 38.50 and B 38.44, 4/8 wins each, within noise.
- D:F1EIM: S = −0.24. P0 and T2 (phase-1 designs): −1.2 / −1.4 at screening.

**The 2×2 interaction is positive but not significant (§4).**
- `load` helps peak-aware labels more than Baleen's labels: +0.44 (F1PT) and +0.63 (F1EIM) vs +0.06.
- The interaction is +0.38 ± 0.61 and +0.57 ± 0.49 (about 1 SE).

**Finalists by the pre-registered rule (§3): X1 = Ea-1.0:F1PT, X2 = Ea-0.5:F1PT.** Both are PLAN arm E: F1PT labels from the q2 parallel-tempering finalist, the `load` feature, and the load-adaptive admission threshold with α = −1.0 / −0.5.

| | dev mean P100 | vs A | vs B | S |
|---|---|---|---|---|
| X1 | 37.20 | +1.30 ± 0.25 (6/8) | +1.24 ± 0.26 (6/8) | **+1.03** |
| X2 | 37.84 | +0.66 ± 0.29 (5/8) | +0.60 ± 0.30 (5/8) | +0.39 |

On dev X1 also meets the test pass rule: ≥ 4/6-type wins, > 2 SE against both A and B, and below RejectX (39.88) and CoinFlip (45.07). Dev is not evidence for H3′, though: the configurations were selected on it. → `PROTOCOL_v2_H3.md` is finalized with X1 (primary) and X2.

**Attribution (§6).** About half of X1's gain is reproduced by the same adaptive threshold on Baleen's own models.
- A+α: 37.88, i.e. +0.62 vs A.
- X1 vs A+α: +0.68 (5/8; instance-level SE 0.63). X1 vs B+α: +1.23 (5/8).
- The threshold helps the F1PT labels most: α = −1 gains +1.17 ± 0.29 (8/8) on D:F1PT, vs +0.62 (A), +0.02 (B) and +0.28 (CP-SAT labels).

The protocol therefore pre-registers a secondary test, **H3′-labels**: X1 vs A+α and B+α with the same rule.

**Ising vs classical labels (same F1 formulation):**
- Without α: D:F1PT vs Dc (CP-SAT) +0.37 (3/8; SE 0.54).
- With α = −1: X1 vs Ea-1.0:F1CPSAT +1.26 (5/8; SE 0.61).
- Not significant. The CP-SAT label sets give worse and more volatile deployed models on Region7 s0.3 and Region6 s0.1.

**Mechanism (§7).**
- **Region6:** the dev gain is concentrated here, where peaks are long big-offset scans. X1 admits 41% of the peak window's accesses (A: 22%). In 10/12 retrains the peak moves away from a scan window (A: 3/12).
- **Region7:** the F1 labels lower first-access admission (2.8% vs 8.7%) and raise mean DT; X1 ≈ A there, and Baleen + α is as good or better.

## 1. Setup

**Arms (PLAN WP2; all at matched write rate 35.599 MB/s ± 1%, threshold converged by full simulation):**

| arm | labels | admission features | other | retrains |
|---|---|---|---|---|
| A | Baleen (authors' `PolicyUtilityServiceTimeSize2`) | `meta+block+chunk` | none | 3 × 8 |
| B | Baleen | `+load` | none | 3 × 8 |
| C:<d> | design d | `meta+block+chunk` | none | 3 × 8 (F1PT, F1EIM) |
| D:<d> | design d | `+load` | none | screen 1 × 8 (5 designs), confirm 3 × 8 (F1PT, F1EIM) |
| Dc | F1CPSAT (CP-SAT) | `+load` | none | 3 × 8 |
| D2:F1PT | F1PT | `+load+tod` | none | screen 1 × 8 |
| Ea<α>:<d> | design d | `+load` | load-adaptive threshold α (D's retrains) | F1PT α=−1, −0.5: 3 × 8; α=−2: screen; F1EIM α=−1: screen; F1CPSAT α=−1: 3 × 8 |
| Epf:F1PT | F1PT | `+load` | prefetch models `meta+load` (Region7 only) | screen 1 × 4 |
| Aa-1.0, Ba-1.0, Ba-0.5 | Baleen | as A / B | same threshold on A's / B's retrains (controls) | 3 × 8 |

**Label designs.** One label set per (instance, design, seed = retrain k), solved on `explore/common/inst/day1_<inst>.npz` by `src/labels.py` with the phase-1 code copied unchanged. Each set is applied in-run by `PolicyPeakBaleen4` by episode identity; the strict-prefix Baleen fill is re-applied in each run, and the in-run labels equal the offline sets.
- **P0, T2, C2:** q3 PT designs (`explore/common/Q3_FORMULATION.md`), 15 s.
- **F1PT, F1EIM:** q2 F1 finalists (true min–max day-1 peak), frozen 10 s configurations, single level f = 1.
- **F1CPSAT:** the same F1 by CP-SAT (q2 classical config), 10 s.

**Seed-1 label sets, mean of 8 instances:**

| design | day-1 label peak (util %) | other properties |
|---|---|---|
| F1PT / F1CPSAT | 21.5 | fewer, larger episodes than Baleen (563–1,724 labels vs 1,124–2,500); no zero-value labels |
| F1EIM | 21.6 | as F1PT |
| P0 | 22.4 | 37–44% zero-value labels |
| T2 | 22.5 | |
| C2 | 24.9 | |
| Baleen | 28.2 | |

Stability across seeds (Jaccard): C2 0.86, F1PT 0.76, F1EIM 0.70, P0 0.42.

**Threshold convergence.** Sequential sims, seeded by the phase-1 emulator (`src/emu.py`, extended with `load`/`tod`/α), at most 7 sims. 2.2 sims per evaluation for A/B, 3.3 for new label designs.

**Other metrics:**
- P99, top-5 and mean DT come from the per-window series.
- First-access admission and peak-window admission come from the trained GBM scored on every trace access at the converged threshold (emulator features, as phase 1).
- Big-offset share = share of the simulated peak window's accesses ending beyond 8 MB.

**Arm A agrees with phase 1** (frozen artifact; `results/summary_A_vs_phase1.csv`).
- Per-instance |diff| ≤ 0.59 and mean |diff| 0.16.
- z is within ±1.4 on 6/8 instances.
- The two large |z| (Region7 s0.2 −0.06 and Region6 s0 +0.08 points) come from near-zero retrain spreads (identical P100 values).

## 2. Learnability gate (PLAN §5; `src/learn.py`, `results/learnability_summary.csv`)

- **Setup:** the trainer's day-1 rows (k < 15) and its exact 18 features (+ the overlay's `load`/`tod`), the artifact's GBM parameters, a 70/30 block split.
- **Criterion** (fixed before reading, PROGRESS.md 16:35): net = [val logloss(orig) − val logloss(+load)] − [the same with shuffled load] > 0 and > 2 SE over the 8 instances.

| labels | net gain (block split) | positive instances | AUC gain | time-split gain (first 70% → last 30% of day 1) | gate |
|---|---|---|---|---|---|
| F1CPSAT | 0.042 ± 0.006 | 8/8 | +0.034 | 0.034 ± 0.014 | PASS |
| F1PT | 0.041 ± 0.006 | 8/8 | +0.034 | 0.031 ± 0.015 | PASS |
| F1EIM | 0.038 ± 0.006 | 8/8 | +0.033 | 0.024 ± 0.012 | PASS |
| P0 | 0.026 ± 0.005 | 8/8 | +0.019 | 0.017 ± 0.009 | PASS |
| T2 | 0.019 ± 0.003 | 8/8 | +0.013 | 0.011 ± 0.006 | PASS |
| C2 | 0.003 ± 0.002 | | +0.001 | −0.001 | fail (D:C2 not run) |
| Baleen | 0.001 ± 0.001 | | +0.000 | −0.004 | (no gain) |

- `+load+tod` adds a further 0.005–0.016 on the block split.
- The time split is positive on all Region7 instances and Region6 s0.2, and negative on Region6 s0.1 and s0.3. Load-conditional labels learned early on day 1 transfer less well to later hours there.

## 3. Screen, confirmation and finalist rule

**Rule** (PROGRESS.md "FINALIST RULE", written 2026-10-03 00:20 before any confirmation retrain; applied unchanged):
- **Candidates:** Ising-family label designs in arms D/D2/E.
- **Eligible:** ≥ 3 matched retrains on all 8 instances.
- **Score:** S = mean_i min(A_i − X_i, B_i − X_i).
- **Finalists:** up to 3 eligible configurations with S > 0.
- **Variant confirmation:** a D2/E variant is confirmed only if its rep-1 screen beats D:F1PT's rep 1, paired on the same instances.

| config | retrains | mean P100 | S | eligible / decision |
|---|---|---|---|---|
| **Ea-1.0:F1PT** | 3 × 8 | **37.20** | **+1.027** | eligible → **X1** |
| **Ea-0.5:F1PT** | 3 × 8 | **37.84** | **+0.386** | eligible → **X2** |
| D:F1PT | 3 × 8 | 38.37 | −0.142 | eligible, S < 0 |
| D:F1EIM | 3 × 8 | 38.46 | −0.238 | eligible, S < 0 |
| Ea-1.0:F1EIM | 1 × 8 | 38.02 | screen 0.206 vs D:F1PT r1 0.237 | not confirmed |
| Ea-2.0:F1PT | 1 × 8 | — | unmatched on 8/8 (threshold bound, §8) | no valid screen, not confirmed, not re-screened |
| D2:F1PT (+tod) | 1 × 8 | 40.26 | screen −2.04 | not confirmed (Region6 s0.3 47.4) |
| Epf:F1PT (pf load) | 1 × 4 | 39.11 | screen −1.62 vs −0.92 | not confirmed |
| D:P0 / D:T2 | 1 × 8 | 39.42 / 39.65 | −1.20 / −1.42 | screen only |
| Dc (CP-SAT), C arms, controls | | see below | | not eligible (by rule) |

**P100 per instance** (mean ± sd over matched retrains, n):

| config | R7 s0 | R7 s0.1 | R7 s0.2 | R7 s0.3 | R6 s0 | R6 s0.1 | R6 s0.2 | R6 s0.3 | mean |
|---|---|---|---|---|---|---|---|---|---|
| A | 40.00 ± 0.14 | 36.81 ± 0.41 | 36.73 ± 0.01 | 37.22 ± 0.77 | 43.33 ± 0.01 | 40.86 ± 0.06 | 36.23 ± 0.14 | 36.83 ± 0.10 | 38.50 |
| B | 39.50 ± 0.20 | 36.51 ± 1.03 | 37.08 ± 0.06 | 38.60 ± 0.38 | 42.79 ± 0.16 | 40.36 ± 0.39 | 36.23 ± 0.06 | 36.47 ± 0.28 | 38.44 |
| C:F1PT | 40.76 ± 0.27 | 37.68 ± 1.22 | 37.42 ± 0.19 | 41.53 ± 0.45 | 43.13 ± 0.08 | 37.06 ± 0.89 | 36.33 ± 0.43 | 36.58 ± 0.32 | 38.81 |
| D:F1PT | 40.25 ± 0.03 | 36.01 ± 0.81 | 37.42 ± 0.20 | 39.33 ± 3.04 | 41.88 ± 1.25 | 39.05 ± 2.24 | 35.95 ± 0.71 | 37.05 ± 0.57 | 38.37 |
| C:F1EIM | 40.68 ± 0.21 | 37.59 ± 0.36 | 37.13 ± 0.15 | 42.97 ± 1.00 | 43.36 ± 0.18 | 37.61 ± 2.29 | 36.16 ± 0.06 | 37.25 ± 0.58 | 39.09 |
| D:F1EIM | 40.37 ± 0.28 | 35.19 ± 0.07 | 37.19 ± 0.06 | 42.57 ± 3.77 | 40.58 ± 1.08 | 36.84 ± 2.16 | 37.99 ± 3.15 | 36.99 ± 0.59 | 38.46 |
| Dc:F1CPSAT | 39.84 ± 0.13 | 35.44 ± 1.07 | 37.20 ± 0.17 | 43.14 ± 0.41 | 41.68 ± 1.31 | 40.26 ± 3.67 | 36.14 ± 0.60 | 36.20 ± 0.05 | 38.74 |
| **X1 Ea-1.0:F1PT** | 39.90 ± 0.11 | 35.10 ± 1.08 | 37.42 ± 0.30 | 38.26 ± 1.81 | 39.29 ± 0.23 | 37.56 ± 2.56 | 34.23 ± 0.14 | 35.83 ± 0.19 | **37.20** |
| X2 Ea-0.5:F1PT | 40.08 ± 0.09 | 35.90 ± 0.91 | 37.40 ± 0.20 | 38.86 ± 2.68 | 40.07 ± 0.80 | 38.07 ± 2.56 | 36.19 ± 0.41 | 36.16 ± 0.33 | 37.84 |
| Ea-1.0:F1CPSAT | 39.85 ± 0.20 | 35.05 ± 1.46 | 37.15 ± 0.13 | 42.53 ± 1.27 | 40.48 ± 1.73 | 41.12 ± 4.87 | 35.17 ± 0.88 | 36.34 ± 0.46 | 38.46 |
| Aa-1.0 (A + α) | 39.65 ± 0.12 | 35.89 ± 0.38 | 36.87 ± 0.03 | 36.01 ± 0.33 | 42.90 ± 0.09 | 38.96 ± 0.04 | 36.30 ± 0.30 | 36.43 ± 0.19 | 37.88 |
| Ba-1.0 (B + α) | 39.61 ± 0.26 | 35.19 ± 0.26 | 37.11 ± 0.10 | 37.61 ± 1.01 | 42.69 ± 0.22 | 42.73 ± 0.23 | 36.07 ± 0.06 | 36.41 ± 0.37 | 38.43 |
| Ba-0.5 (B + α) | 39.49 ± 0.32 | 35.62 ± 0.53 | 37.10 ± 0.06 | 38.29 ± 0.42 | 43.04 ± 0.06 | 39.03 ± 0.35 | 35.74 ± 0.27 | 36.11 ± 0.35 | 38.05 |
| RejectX / CoinFlip | 42.46 / 48.96 | 38.66 / 46.00 | 38.00 / 41.97 | 38.89 / 45.19 | 42.32 / 43.45 | 42.25 / 50.02 | 37.29 / 43.85 | 39.19 / 41.09 | 39.88 / 45.07 |

All configurations with 3 retrains have n = 3 per cell; C:F1PT Region7 s0/s0.1 and C:F1EIM Region6 s0.3 needed extra seeds (§8). The full table with every configuration and n is in `results/summary.md`.

## 4. The 2×2: does `load` help peak-aware labels more than Baleen's labels? (mean over 8 instances ± instance-level SE)

| design | load gain, Baleen labels (A − B) | load gain, peak-aware labels (C − D) | interaction (C − D) − (A − B) | label gain without load (A − C) | label gain with load (B − D) |
|---|---|---|---|---|---|
| F1PT | +0.06 ± 0.23 | +0.44 ± 0.47 | **+0.38 ± 0.61** | −0.31 ± 0.78 | +0.08 ± 0.28 |
| F1EIM | +0.06 ± 0.23 | +0.63 ± 0.51 | **+0.57 ± 0.49** | −0.59 ± 0.87 | −0.02 ± 0.83 |

- Without `load`, the peak-aware labels are worse than Baleen's.
- With `load`, they reach Baleen's level, but not significantly beyond it.
- The direction agrees with the learnability gate. The size is about 1 SE.
- **Second 2×2, the threshold policy (α = −1):**
  - Baleen labels: +0.62 ± 0.24 (A − A+α), +0.02 ± 0.39 (B − B+α).
  - F1PT labels + load: **+1.17 ± 0.29, positive on 8/8** (D − X1).
  - CP-SAT labels + load: +0.28 ± 0.23.

## 5. Ising vs classical labels (same F1 formulation and budget)

Paired per instance; positive = Ising better (`results/attribution.txt`):

| comparison | wins | mean | SE (retrain / instance) |
|---|---|---|---|
| D:F1PT vs Dc:F1CPSAT | 3/8 | +0.37 | 0.42 / 0.54 |
| D:F1EIM vs Dc:F1CPSAT | 5/8 | +0.27 | / 0.55 |
| X1 vs Ea-1.0:F1CPSAT | 5/8 | +1.26 | 0.47 / 0.61 |

- CP-SAT finds day-1 label sets as good (offline day-1 peak 21.5) and about as stable (Jaccard 0.74).
- Its deployed models are worse on Region7 s0.3 (43.1) and volatile on Region6 s0.1 (40.3 ± 3.7).
- This is suggestive at best; no claim.

## 6. Attribution of the finalists' gain

| X1 = Ea-1.0:F1PT vs | wins | mean improvement | SE retrain / instance |
|---|---|---|---|
| A | 6/8 | +1.30 | 0.25 / 0.64 |
| B | 6/8 | +1.24 | 0.26 / 0.51 |
| A+α (Baleen labels, orig. features, same α) | 5/8 | +0.68 | 0.25 / 0.63 |
| B+α (Baleen labels + load, same α) | 5/8 | +1.23 | 0.26 / 0.74 |
| D:F1PT (same labels, no α) | 8/8 | +1.17 | 0.39 / 0.29 |

- **Per instance vs A+α:** Region7 −0.26, +0.80, −0.55, −2.25; Region6 +3.61, +1.40, +2.06, +0.60.
- **Where the gain is:** the labels × threshold combination wins on Region6. On Region7, Baleen + the same threshold is as good or better.
- **What the test will decide:** H3′ (vs A, B), and H3′-labels (vs A+α, B+α), which says whether the Ising labels matter beyond the threshold policy.

## 7. Mechanism

Per region; means over matched retrains × 4 instances; `results/mechanism_by_region.txt`.
- k0 = first-access admission.
- peak adm = admitted share of the peak window's accesses.
- scan peak = share of retrains whose peak window has > 25% of its accesses ending beyond 8 MB.

**Region6:**

| config | P100 | P99 | top-5 | mean DT | k0 | peak adm | scan peak |
|---|---|---|---|---|---|---|---|
| A | 39.31 | 33.11 | 37.09 | 21.44 | 0.2% | 0.22 | 9/12 |
| B | 38.96 | 33.08 | 36.74 | 21.38 | 0.2% | 0.23 | 6/12 |
| A+α | 38.65 | 32.68 | 36.06 | 21.55 | 0.7% | 0.29 | 9/12 |
| D:F1PT | 38.48 | 33.17 | 36.32 | 21.61 | 0.3% | 0.30 | 8/12 |
| **X1** | **36.73** | 32.63 | 35.28 | 21.72 | 0.4% | **0.41** | **2/12** |

**Region7:**

| config | P100 | P99 | top-5 | mean DT | k0 | peak adm | scan peak |
|---|---|---|---|---|---|---|---|
| A | 37.69 | 32.62 | 35.81 | 21.24 | 8.7% | 0.36 | 0/12 |
| B | 37.92 | 32.41 | 35.81 | 21.16 | 9.6% | 0.36 | 1/12 |
| A+α | 37.11 | 32.08 | 35.21 | 21.29 | 8.4% | 0.38 | 0/12 |
| B+α | 37.38 | 31.86 | 35.16 | 21.26 | 8.0% | 0.41 | 0/12 |
| D:F1PT | 38.25 | 32.10 | 35.64 | 21.86 | 2.4% | 0.31 | 2/12 |
| X1 | 37.67 | 31.92 | 35.28 | 22.02 | 2.8% | 0.38 | 2/12 |

1. **Region6 peaks are big-offset scans.** These are long sequential reads, the phase-1 Region6 s0 window 712 kind. The F1 labels select large episodes that save time in the day-1 peak windows; with `load`, the GBM learns to admit them when demand is high. The adaptive threshold lowers the bar further in exactly those windows. Together they admit 41% of the peak window (A: 22%), and the peak moves off the scan window in 10/12 retrains. The same threshold on Baleen's models (A+α, B+α) neither removes the scan peaks (9/12) nor reaches the same P100.
2. **Region7 peaks are bursts of new episodes.** First-access admission matters there (phase-1 finding). The F1 labels have no zero-value positives and fewer, larger episodes, so their models admit at first access 2–3% of the time vs 8–10% for Baleen's. That raises mean DT by about 0.7 and costs P100 on Region7 s0.3. The adaptive threshold recovers most of it, but not more than it gives Baleen's models.
3. **P0/T2 (phase-1 designs) restore first-access admission** (16–30%) but are unstable (Region7 s0.1 41.7 for T2, Region6 s0.2 42.1 for P0). The phase-1 held-out failure mode reappears.
4. **Retention** of the offline peak-aware gain, R = (A − X)/(OPT_peak-blind − OPT_peak-aware):
   - per-instance mean: X1 0.24 (range −0.23 to +0.74); X2 0.11; A+α 0.13; D:F1PT 0.02; B 0.00 (`results/summary.md`);
   - offline values: peak-blind OPT from `explore/common/baselines.csv`; peak-aware OPT from the q2 F1-PT held-out sims for s0.1–0.3 and harness_eval EIM arm C2 for s0.

## 8. Unmatched runs, limitations and deviations (all reported; nothing was deleted)

**40 unmatched rows**, excluded from every mean:
- **Write-rate steps** (tied GBM scores make WR jump across the ±1% window): 4 C-arm rows. One extra seed each kept 3 matched retrains per cell (seed 4; C:F1PT Region7 s0.1 needed seed 5).
- **Threshold-search bound (tool limitation):** 36 rows. My `converge` searched θ < 1. With the adaptive threshold (g ∈ [0.25, 4]) the base threshold may need to exceed 1.
  - Affected: the controls Aa-1.0/Ba-1.0 on all Region6 cells (WR 46–55 MB/s at θ = 1), Ba-0.5 (3 cells), Ea-1.0:F1CPSAT (1 cell) and Ea-2.0 (8/8).
  - The affected control/comparison cells were re-run with the search widened to (0, 4] under distinct names (Ax/Bx/Ex). They are merged as the same configuration; all 28 matched, at θ 1.01–1.29.
  - Both finalists matched inside the original bound on every cell.
  - Ea-2.0 was not re-screened (conservative; no further α tuning).
  - The test protocol fixes the (0, 4] range for all α arms.

**Other limitations and deviations:**
- **Dev selection.** The finalists come from screening 5 label designs plus 5 variants and 2 α values on the same 8 instances. The dev scores of X1/X2 are optimistic, and the test (PROTOCOL_v2_H3) is the only valid evidence.
- **Arm E's prefetch variant (Epf)** carries the known train/serve skew of SCOPE_v2 §1a: first access in training, triggering access in serving. It was screened on Region7 only.
- **D2 (+tod)** has one training day, hence one example per hour (PLAN §6 risk). Its screen is the worst configuration (Region6 s0.3 47.4).
- **Session interruptions.** The coordinator session ended twice (Oct 1 evening, Oct 3 ~02:15). All queues had completed or were resumed, and no orphaned partial simulation was used. Two in-session driver restarts (Oct 1 17:27, Oct 3 02:15) re-used finished sims of orphaned runs and held their sim slots until they exited.
- **Compute.** 1,075 sims. Threshold seeding used the emulator only; every reported number is a full simulation.

## 9. Integrity

**Sandbox:**
- `env.sh` puts HOME/XDG/TMPDIR/pip/conda/MPL/numba/torch inside `wp2_deployed/`, with `CONDA_REGISTER_ENVS=false`, `PYTHONNOUSERSITE=1` and `PYTHONDONTWRITEBYTECODE=1`.
- Every Baleen and solver process ran as `taskset -c <8-11,20-23 | 0-23 only while TIMING_IDLE> bwrap --dev-bind / / --bind <private job tmp> /tmp -- <env python> -B`.
- Every train held `2_deployable_peak/.train.lock`.
- ≤ 6 own sims while `TIMING_IDLE` was absent and ≤ 14 while it existed, through a slot pool in `SimSlot`.
- The Baleen and solver envs were used read-only. Data comes through the read-only symlink to `explore/common/data`. The phase-1 code was copied unchanged into `src/q2lib` and `src/q3lib`.
- No run on samples ≥ 0.4. No git commits.

**Checks:**
- `bash 0_reproduce/check_frozen.sh`: **`frozen OK (94 files)`** (2026-10-04 09:12).
- Nothing under `0_reproduce/` or `1_literature_review/` is newer than `wp2_deployed/.leak_marker` (2026-10-01 16:25).
- No `__pycache__` in the overlay, the frozen tree or `src/`.
- PATCH.diff is unchanged.

**Leak check** (the prescribed command, 2026-10-04 09:12; raw list in `results/integrity.txt`). It lists 562 files, none written by this work:

| count | location | owner |
|---|---|---|
| 371 | `OS_final_project/.git/` | the coordinator's commits (`COMMIT_EDITMSG`, `index`, objects) |
| 1 | `OS_final_project/RESEARCH.md` | another agent |
| 139 | `~/project/server_fix/diagnose/` | an unrelated project |
| 33 | `~/.cache/huggingface/` | a sentence-transformers model download, unrelated |
| 14 | `~/snap/snapd-desktop-integration/` | desktop |
| 1 each | `~/.config/dconf/user`, `~/.cache/update-manager-core`, `/tmp/krb5cc_*` | desktop / system |
| 1 | `~/.conda/aau_token_host` | conda outside this work |

This work never ran conda, git writes or HuggingFace, and all its processes had HOME = `wp2_deployed/.home` and a private `/tmp`.

```
# check_frozen.sh
frozen OK (94 files)
# leak check after removing the categories above
(empty)
```

## 10. Files (`wp2_deployed/`)

| path | contents |
|---|---|
| `trials.csv` | one row per evaluation (388), every column above |
| `PROGRESS.md` | log, finalist rule (as written), RESUME commands, queues |
| `PROTOCOL_v2_H3.md` | final test protocol (commit at CP2 before any test run) |
| `results/summary.md` (`summary_*.csv`, `finalist_scores.csv`) | all tables |
| `results/attribution.txt` | paired attribution |
| `results/mechanism_by_region.txt` | mechanism by region |
| `results/learnability*.csv` | learnability gate |
| `results/integrity.txt` | leak check and frozen check |
| `src/` | `wp2.py` (driver), `labels.py`, `pb4_policy.py`, `emu.py`, `learn.py`, `summarize.py`, `wpcommon.py`, copied phase-1 code |
| `labels/*.json` | label statistics (the `.npz` sets are git-ignored) |
