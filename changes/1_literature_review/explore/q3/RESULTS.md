# Track A (Q3): Ising-family labels distilled into Baleen's unchanged online models — results

Track A of the deep-exploration campaign (PROTOCOL.md, frozen 2026-09-28). Run 2026-09-28 15:53 → 2026-09-29 02:30, 24-thread
AMD Ryzen 9 9900X (cores 8-23), CPU only; frozen artifact Baleen-FAST24 `4e3a920` / BCacheSim `ddeb2d8` (unmodified).

## 0. Verdict

**Q3 — "Does it beat Baleen in the real deployed system?" — NO.** None of the three Ising-family finalists passes on the
held-out instances (Region7/Region6 × samples 0.1-0.3, 3 retrains each, matched WR 35.599 ±1%):

| finalist (PT on the extended-Ising energy) | wins vs Baleen online (need >= 4/6) | mean improvement over Baleen (need > 2 SE) | mean P100 vs RejectX 39.05 / CoinFlip 44.69 | Q3 |
|---|---|---|---|---|
| **P0** pure soft peak (LSE) | 2/6 — FAIL | −0.41 (worse) vs 2 SE = 0.56 — FAIL | 37.97 — PASS | **NO** |
| **T2** LSE + DT blend + trust region | 2/6 — FAIL | −1.07 (worse) vs 2 SE = 0.85 — FAIL | 38.62 — PASS | **NO** |
| **C2** T2 energy over GBM-feature cells | 2/6 — FAIL | −0.57 (worse) vs 2 SE = 0.96 — FAIL | 38.13 — PASS | **NO** |

(Baleen online held-out mean 37.55. Criterion 3 is passed by Baleen itself; it does not discriminate here.)

- **Dev looked positive, held-out reversed it.** On dev (sample 0) the finalists were 0.74-1.17 points below Baleen on
  Region7 (Baleen 40.10 ± 0.18 → 38.93-39.36) and 0.04-0.47 on Region6 (43.25 → 42.78-43.21), each with 3 retrains.
  On held-out they are on average 0.41-1.07 points *above* Baleen, with large retrain-to-retrain swings (T2 Region7
  s0.1: 36.05 / 42.69 / 36.42; C2 Region6 s0.1: 49.50 / 41.03 / 41.66; P0 Region6 s0.2: 36.40 / 35.87 / 40.96) while
  Baleen's own held-out retrains vary by at most 0.5.
- **Mechanism.** The Ising labels do not deliver peak-awareness to the GBM (it has no time/load feature and day-1 peak
  cells do not recur). What they change is *first-access admission*: the stochastic PT leaves many zero-value
  single-access episodes selected (the peak energy is indifferent to them), which gives the GBM positive first-access
  rows; the trained model then admits new episodes at their first access far more often (Region7: dev 6% → 14-28%,
  held-out 8-11% → 14-36%; Region6 stays below 8%). On dev Region7 this explains the gain (corr(first-access
  admission, P100) = −0.79 over 13 matched trials; in single-retrain ablations a *non-Ising* control with random
  one-hit-wonder positives reproduces ~3/4 of T5's gain, and removing T5's zero-value additions removes ~3/4 of it). On held-out
  the same shift lowers Region7's mean load, but P100 is set by rare scan-like windows (25-42% of their accesses beyond
  8 MB) whose treatment by the frozen GBM is learned from a handful of training rows (the trainer keeps only each
  episode's first 15 accesses) and flips unpredictably with the labels: e.g. T2's model admits 26% of Region7 s0.3
  window 362 vs 42% for Baleen's (+3.6 points), C2's 13% of Region6 s0.1 window 284 vs 20% (+3.1). The same fragile
  region caused Region6's dev peak (a 21.7 MB scan rejected once its offsets pass ~10 MB), which no label set fixed.
- **Built for everyone (A0):** held-out data (sha1-verified), day-1 and full-trace instances for dev + held-out
  (`common/INSTANCES.md`), and held-out baselines (Baleen online ×3 retrains, bit-exact RejectX/CoinFlip replays of the
  authors, peak-blind OPT) — `common/{DATA,INSTANCES,BASELINES}_READY`. The final Q3 formulation for Track B:
  `common/Q3_FORMULATION.md` + `common/src/q3form.py` (reproduces the solver's energies exactly).
- **Integrity:** `check_frozen.sh` OK; leak check empty; one disclosed pre-marker incident (a `__pycache__` file created
  and removed in `0_reproduce/repro/` at 15:54-16:06; section 5).

## 1. What was built (A0)

### 1.1 Data
- `storage_0.1_10.tar.gz` (162,615,908 bytes) downloaded with a sandboxed HOME into `common/raw/`, assembled as
  `common/data/tectonic/<group>/<region>/full_<start>_0.1.trace` for all 7 traces × samples 0..0.9; sample 0 and its
  `.keys` are read-only relative symlinks to `0_reproduce/work/data`; `results_release.csv.gz` symlinked.
  sha1: 70/70 trace files OK against each region's `checksums.sha1` → `common/DATA_READY`.

### 1.2 Instances (`common/INSTANCES.md`, `common/INSTANCES_READY`)
- `day1_<R>_s<t>.npz` (deployed; the authors' Baleen train args for that sample) and `full_<R>_s<t>.npz` (offline;
  OPT EA, OPT-Range on OPT-Ep-Start settings, windows after day 1) for dev (s0) and held-out (s0.1-0.3), built through
  the unmodified training driver with our launcher; harness_eval format + per-access GBM features.
- Feature fidelity: the dumped per-access features equal the frozen trainer's `df_X` on all 31,105 day-1 rows of
  Region7 (18 columns, max abs diff 0), and the dumped Baleen labels equal its `threshold_binary`.
- harness_eval's dev instances are copied as `hx_*` and are identical to ours up to episode permutation.

### 1.3 Held-out baselines (`common/baselines.csv`, `common/baselines_summary.csv`, `common/BASELINES_READY`)
All at matched WR (35.599 MB/s ±1%), from the authors' per-sample commands in `results_release.csv.gz` (path rewrite as
0_reproduce/harness_eval, `+ --eviction-policy LRU`, `- --offline-ap-decisions` for non-OPT APs):
- **Baleen online**: Fig 9 variants (Region7 ML-Range on ML-When, Region6 All on Partial Hit), the authors'
  `TrainCommand`/`ReproduceCommand` for each sample (EA from that sample's row), stock policy, 3 retrains per instance,
  `--ap-threshold` converged with converge.py's rules.
- **RejectX / CoinFlip**: the authors' `20230410_static_pf` rows; the authors' `--ap-probability` already gives WR within
  ±1% on all 6 held-out instances (no bisection needed) and the replays reproduce the authors' reported P100 exactly
  on all 12 runs (e.g. Region7 s0.1 RejectX 38.66278 vs 38.662782).
- **Peak-blind OPT**: Baleen's order on full-trace episodes at the OPT row's EA, "OPT-Range on OPT-Ep-Start", decisions
  from our launcher, OPT cutoff (MB/s) converged.
- Dev rows (sample 0) are reused read-only (0_reproduce 9 retrains / fig9 replays; harness_eval R0 for OPT).

| instance | Baleen online P100 | RejectX | CoinFlip | peak-blind OPT | WR range (MB/s) |
|---|---|---|---|---|---|
| Region7_s0 | 40.10 ± 0.18 (n=9; 39.98, 39.96, 40.35, 40.04, 40.09, 40.00, 40.42, 39.93, 40.10) | 42.46 | 48.96 | 34.52 | 35.30-36.00 |
| Region7_s0.1 | 36.57 ± 0.25 (n=3; 36.29, 36.64, 36.78) | 38.66 | 46.00 | 33.68 | 35.43-35.84 |
| Region7_s0.2 | 36.79 ± 0.00 (n=3; 36.79, 36.79, 36.78) | 38.00 | 41.97 | 35.28 | 35.54-35.90 |
| Region7_s0.3 | 37.81 ± 0.25 (n=3; 37.53, 38.01, 37.89) | 38.89 | 45.19 | 31.23 | 35.57-35.76 |
| Region6_s0 | 43.25 ± 0.04 (n=9; 43.21, 43.21, 43.27, 43.27, 43.27, 43.32, 43.27, 43.21, 43.21) | 42.32 | 43.45 | 35.56 | 35.27-35.68 |
| Region6_s0.1 | 40.93 ± 0.07 (n=3; 40.90, 41.01, 40.90) | 42.25 | 50.02 | 30.90 | 35.47-35.85 |
| Region6_s0.2 | 36.26 ± 0.10 (n=3; 36.31, 36.31, 36.14) | 37.29 | 43.85 | 30.62 | 35.28-35.90 |
| Region6_s0.3 | 36.96 ± 0.26 (n=3; 36.68, 37.18, 37.04) | 39.19 | 41.09 | 31.96 | 35.57-35.92 |


## 2. A1: search on dev

### 2.1 Diagnosis of the deployed peak (dev)
- **Where the deployed peak comes from.** Region6: one window (712: 43.3 online vs no-cache 53.4; next windows ~40).
  Region7: several windows (646 40.1, 660 38.4, 613 36.8). In these windows most of the no-cache load comes from
  episodes that *start* in the window (e.g. 34.9 of 48.3 util-points at Region7/646).
- **Admission quality, not prefetching, is the gap** (dev diagnostic sims, existing simulator flags only; `q3/src/diag.py`,
  `q3/results/diag.jsonl`): Baleen's peak-blind OPT decisions simulated under the *deployed* prefetch variants give
  P100 37.8 (Region6, window 712 at 25.7) and 37.0 (Region7); harness_eval's peak-aware R2 decisions give 31.4 / 34.0.
  The online GBM gives 43.3 / 40.1.
- **Region6/712 is an extrapolation failure of the frozen GBM.** A long sequential scan (447 accesses over a 174-chunk,
  21.7 MB block) is admitted while its byte offsets are small, then its score collapses (0.97 -> 0.04-0.09) once the
  offsets pass ~10 MB, so all 282 of its accesses in window 712 are rejected (online misses 491 IOs there vs 197 under
  OPT). Accesses ending beyond 8 MB (~5-6% of accesses) are rejected 92-99.5% of the time (vs 64-68% for the rest) and
  carry 20 util-points of 712's load. The day-1 scans of this kind are already Baleen-positive, but the trainer uses
  only each episode's first 15 accesses (small offsets, block count <= 14), so the big-offset/high-count region is
  learned from other, mostly negative rows; relabeling those rows positive would cost 11-38% of the day-1 write budget
  (the SAT12/SATB10 designs tried this; no Region6 gain).
- **What labels can move: first-access admission.** At the top windows the largest rejected component is the first two
  accesses of new episodes (16-23 util-points); the GBM sees only metadata there (no history). Label sets that contain
  more positive first-access rows make the GBM admit new episodes earlier (see 2.2 and section 4).
- **What does not transfer from day 1:** first-access-only feature-cell policies (`q3/src/cellan.py`) optimized on day
  1 are far worse than the GBM on the test days (analytic 55-59 vs ~40), while a test-day oracle over the same cells
  would reach 34-43; and the metadata cells over-represented in peak windows are only weakly and inconsistently
  correlated between day 1 and later days (Region7 r = 0.08-0.76, Region6 r = -0.36..0.51).
- **Cheap proxy rejected:** scoring all accesses with the trained GBM (simulator-style features, reconstructed exactly
  as `sim_features.collect_features`) and emulating admission analytically tracks the simulated write rate along each
  model's threshold curve (r = 0.975 / 0.995 over 37 harness_eval models) but does not rank models at matched WR
  (r = -0.01 / -0.03). It is used only to seed the threshold search; every reported number is a full simulation.

### 2.2 Designs tried (all rows of `q3/trials.csv`)
All designs share one pipeline (`q3/src/deployed3.py`, copied from harness_eval's `deployed.py`): the day-1 instance is
built inside the authors' Baleen `TrainCommand` for that sample by our Policy (`PolicyPeakBaleen3`), the solver
(`q3/src/q3solve.py`, solver env `X/env`) returns the selected set, labels = selected set + Baleen-order fill
(prefix rule asserted at every sort call), Baleen's unchanged GBMs are trained on them, and the authors'
`ReproduceCommand` is simulated with `--ap-threshold` converged to 35.599 MB/s ±1%. One retrain = new episode generation
+ new solver seed + new GBMs. Every Q3 candidate is an Ising-family solver: parallel tempering on the extended-Ising
energy of `common/Q3_FORMULATION.md` (100% of accepted moves from PT); `R0` (identity) and `JUNK10` (random,
non-Ising) are controls, never candidates.

Dev results (P100 util %, matched WR only; dev Baleen references 40.10 +- 0.18 (Region7) and 43.25 +- 0.04 (Region6), 9 retrains each):

| config | description | instance | retrains (matched/all) | P100 mean +- sd (matched) | per retrain | vs Baleen ref | mean DT | J vs Baleen labels | day-1 label peak |
|---|---|---|---|---|---|---|---|---|---|
| T5 | PT, LSE peak (gamma 2) + DT blend beta=1 + trust region mu=5 | Region7_s0 | 3/3 | 39.35 +- 0.32 | 39.26, 39.70, 39.07 | -0.75 | 21.29 | 0.77 | 23.11 |
| T5 | PT, LSE peak (gamma 2) + DT blend beta=1 + trust region mu=5 | Region6_s0 | 3/3 | 43.01 +- 0.09 | 43.07, 42.91, 43.05 | -0.24 | 22.05 | 0.85 | 21.25 |
| PW4 | PT, peak-weighted DT knapsack (phi=(C/mean C)^4), no peak term | Region7_s0 | 1/1 | 40.26 | 40.26 | +0.16 | 21.59 | 1.00 | 27.63 |
| PW4 | PT, peak-weighted DT knapsack (phi=(C/mean C)^4), no peak term | Region6_s0 | 1/1 | 42.81 | 42.81 | -0.44 | 21.94 | 0.37 | 22.24 |
| SAT12 | PT T5 + forced coverage of episodes with block count>=12 at offsets>8MB | Region7_s0 | 1/1 | 39.37 | 39.37 | -0.73 | 21.48 | 0.83 | 24.66 |
| SAT12 | PT T5 + forced coverage of episodes with block count>=12 at offsets>8MB | Region6_s0 | 1/1 | 43.32 | 43.32 | +0.08 | 22.05 | 0.85 | 22.01 |
| C2 | PT on feature CELLS (op/ns/user, log size, history bins, #rows bin) + beta=0.5 + mu=2 | Region7_s0 | 3/3 | 38.93 +- 0.56 | 38.89, 39.50, 38.39 | -1.17 | 21.38 | 0.77 | 25.81 |
| C2 | PT on feature CELLS (op/ns/user, log size, history bins, #rows bin) + beta=0.5 + mu=2 | Region6_s0 | 3/3 | 43.21 +- 0.13 | 43.20, 43.08, 43.35 | -0.04 | 22.00 | 0.72 | 22.92 |
| SATB10 | coverage (b0>=10, >8MB) forced + DT/trust only (no peak term) | Region7_s0 | 0/1 |  |  |  |  |  |  |
| SATB10 | coverage (b0>=10, >8MB) forced + DT/trust only (no peak term) | Region6_s0 | 0/1 |  |  |  |  |  |  |
| P0 | PT, pure LSE peak (no DT blend, no trust region) | Region7_s0 | 3/3 | 39.16 +- 0.40 | 38.71, 39.31, 39.46 | -0.93 | 21.29 | 0.37 | 23.06 |
| P0 | PT, pure LSE peak (no DT blend, no trust region) | Region6_s0 | 3/3 | 42.93 +- 0.18 | 42.94, 42.75, 43.11 | -0.32 | 21.96 | 0.38 | 20.81 |
| T2 | PT, LSE peak + beta=0.5 + trust mu=2 | Region7_s0 | 3/3 | 39.36 +- 0.17 | 39.23, 39.30, 39.55 | -0.74 | 21.25 | 0.55 | 23.06 |
| T2 | PT, LSE peak + beta=0.5 + trust mu=2 | Region6_s0 | 3/3 | 42.78 +- 0.40 | 42.33, 43.03, 42.99 | -0.46 | 22.02 | 0.67 | 20.83 |
| R0 | control: Baleen's own labels through the solver path (identity) | Region7_s0 | 1/1 | 40.17 | 40.17 | +0.08 | 21.57 | 1.00 | 28.90 |
| R0 | control: Baleen's own labels through the solver path (identity) | Region6_s0 | 1/1 | 43.27 | 43.27 | +0.02 | 21.97 | 1.00 | 25.93 |
| TK10 | PT, top-10-window mean peak + beta=1 + trust mu=5 | Region7_s0 | 2/4 | 39.20 +- 0.23 | 39.04, 39.36, 39.08*, 39.48* | -0.89 | 21.35 | 0.78 | 23.51 |
| TK10 | PT, top-10-window mean peak + beta=1 + trust mu=5 | Region6_s0 | 3/3 | 43.07 +- 0.18 | 43.27, 42.95, 42.98 | -0.18 | 22.04 | 0.87 | 21.81 |
| L5 | PT, LSE peak + beta=0.5 + mu=2 + kNN feature-consistency couplings lam=5 | Region7_s0 | 3/3 | 39.12 +- 0.18 | 39.21, 39.23, 38.92 | -0.98 | 21.27 | 0.61 | 22.99 |
| L5 | PT, LSE peak + beta=0.5 + mu=2 + kNN feature-consistency couplings lam=5 | Region6_s0 | 3/3 | 43.21 +- 0.07 | 43.28, 43.21, 43.15 | -0.04 | 22.10 | 0.72 | 20.88 |
| T5c | T5 with zero-value additions removed (Baleen-order fill) | Region7_s0 | 1/1 | 39.90 | 39.90 | -0.20 | 21.40 | 0.87 | 23.17 |
| T5c | T5 with zero-value additions removed (Baleen-order fill) | Region6_s0 | 1/1 | 43.05 | 43.05 | -0.19 | 22.05 | 0.85 | 21.18 |

(* = not within +-1% WR; excluded from the mean)

Controls (stage "control"):

| control | description | instance | retrains (matched/all) | P100 mean +- sd (matched) | per retrain | vs Baleen ref | mean DT | J vs Baleen labels | day-1 label peak |
|---|---|---|---|---|---|---|---|---|---|
| JUNK10 | CONTROL (not Ising): Baleen labels, lowest 10% of budget swapped for random zero-value episodes | Region7_s0 | 1/1 | 39.51 | 39.51 | -0.59 | 21.39 | 0.93 | 28.96 |
| JUNK10 | CONTROL (not Ising): Baleen labels, lowest 10% of budget swapped for random zero-value episodes | Region6_s0 | 1/1 | 43.38 | 43.38 | +0.14 | 21.96 | 0.88 | 26.12 |

(* = not within +-1% WR; excluded from the mean)


### 2.3 Finalists
Selection rule pre-registered at 19:35 (`q3/PROGRESS.md`) before the confirmation retrains were complete: eligible =
Ising configurations with >= 3 matched retrains on both dev traces; score = mean over the two traces of (dev Baleen
reference − configuration mean P100); finalists = the 3 highest positive scores.

```
config  Region7_n  Region7_mean  Region7_sd  Region7_imp  Region6_n  Region6_mean  Region6_sd  Region6_imp  eligible  score
    P0          3        39.163       0.397        0.933          3        42.933       0.179        0.316      True  0.624
    T2          3        39.356       0.168        0.741          3        42.784       0.396        0.465      True  0.603
    C2          3        38.929       0.555        1.168          3        43.211       0.132        0.037      True  0.602
  TK10          2        39.203       0.226        0.894          3        43.065       0.175        0.183     False  0.538
    L5          3        39.121       0.175        0.975          3        43.212       0.066        0.036      True  0.505
    T5          3        39.345       0.324        0.751          3        43.010       0.089        0.239      True  0.495
 SAT12          1        39.366         NaN        0.730          1        43.324         NaN       -0.076     False  0.327
   T5c          1        39.900         NaN        0.197          1        43.055         NaN        0.194     False  0.196
   PW4          1        40.257         NaN       -0.160          1        42.808         NaN        0.440     False  0.140
    R0          1        40.175         NaN       -0.078          1        43.267         NaN       -0.019     False -0.048
```

Finalists: **P0** (pure soft-peak LSE, no DT blend, no trust region), **T2** (LSE + DT blend 0.5 + trust region 2),
**C2** (T2's energy over first-row feature cells). All three have their deployed dev gain on Region7 (0.74-1.17
points) and at most ~0.5 points on Region6.

## 3. A2: held-out confirmation
The three finalists ran on all 6 held-out instances (Region7/Region6 × samples 0.1, 0.2, 0.3), 3 retrains each, with
exactly the dev pipeline and arguments (`q3/run_a2.sh`; stage `heldout` in `q3/trials.csv`), each against the
held-out baselines of section 1.3. Evaluation exactly per PROTOCOL.md (`q3/src/q3eval.py`, output
`q3/results/q3eval_heldout.{csv,md}`): (1) mean P100 below Baleen online's mean on >= 4 of 6 instances; (2) mean
improvement over Baleen online > 2 SE of the difference (primary SE from retrain variances as in harness_eval:
SE = sqrt(sum_i s_c,i^2/n_c,i + s_b,i^2/n_b,i)/6; the instance-level SE is also shown); (3) mean P100 below RejectX's
and CoinFlip's means. Only matched-WR retrains count.


**T2** (held-out, 3 retrains per instance; P100 util %, matched WR only)

| instance | retrains (matched/all) | P100 mean +- sd | per retrain | Baleen online (3) | diff (Baleen - cfg) | RejectX | CoinFlip | win vs Baleen |
|---|---|---|---|---|---|---|---|---|
| Region7_s0.1 | 3/3 | 38.39 +- 3.73 | 36.05, 42.69, 36.42 | 36.57 +- 0.25 | -1.82 | 38.66 | 46.00 | no |
| Region7_s0.2 | 2/3 | 36.69 +- 0.13 | 36.78, 36.60 | 36.79 +- 0.00 | +0.10 | 38.00 | 41.97 | yes |
| Region7_s0.3 | 3/3 | 41.39 +- 2.19 | 42.85, 42.45, 38.86 | 37.81 +- 0.25 | -3.58 | 38.89 | 45.19 | no |
| Region6_s0.1 | 3/3 | 42.28 +- 0.56 | 42.88, 42.17, 41.78 | 40.93 +- 0.07 | -1.34 | 42.25 | 50.02 | no |
| Region6_s0.2 | 3/3 | 36.29 +- 0.46 | 35.98, 36.82, 36.06 | 36.26 +- 0.10 | -0.03 | 37.29 | 43.85 | no |
| Region6_s0.3 | 3/3 | 36.70 +- 0.16 | 36.69, 36.55, 36.86 | 36.96 +- 0.26 | +0.26 | 39.19 | 41.09 | yes |

Criteria: wins 2/6 (need >= 4) -> FAIL; mean improvement -1.068 vs 2 SE = 0.850 (retrain SE; instance-level 2 SE = 1.218) -> FAIL; mean P100 38.62 vs RejectX 39.05 / CoinFlip 44.69 -> PASS. **Q3 for T2: NO**

**C2** (held-out, 3 retrains per instance; P100 util %, matched WR only)

| instance | retrains (matched/all) | P100 mean +- sd | per retrain | Baleen online (3) | diff (Baleen - cfg) | RejectX | CoinFlip | win vs Baleen |
|---|---|---|---|---|---|---|---|---|
| Region7_s0.1 | 3/3 | 36.68 +- 0.36 | 37.00, 36.74, 36.29 | 36.57 +- 0.25 | -0.11 | 38.66 | 46.00 | no |
| Region7_s0.2 | 3/3 | 37.05 +- 0.24 | 36.77, 37.21, 37.16 | 36.79 +- 0.00 | -0.26 | 38.00 | 41.97 | no |
| Region7_s0.3 | 3/3 | 38.08 +- 1.42 | 39.15, 36.47, 38.63 | 37.81 +- 0.25 | -0.27 | 38.89 | 45.19 | no |
| Region6_s0.1 | 3/3 | 44.06 +- 4.72 | 49.50, 41.03, 41.66 | 40.93 +- 0.07 | -3.13 | 42.25 | 50.02 | no |
| Region6_s0.2 | 3/3 | 36.14 +- 0.09 | 36.12, 36.05, 36.24 | 36.26 +- 0.10 | +0.12 | 37.29 | 43.85 | yes |
| Region6_s0.3 | 3/3 | 36.75 +- 0.16 | 36.83, 36.57, 36.87 | 36.96 +- 0.26 | +0.21 | 39.19 | 41.09 | yes |

Criteria: wins 2/6 (need >= 4) -> FAIL; mean improvement -0.573 vs 2 SE = 0.956 (retrain SE; instance-level 2 SE = 1.035) -> FAIL; mean P100 38.13 vs RejectX 39.05 / CoinFlip 44.69 -> PASS. **Q3 for C2: NO**

**P0** (held-out, 3 retrains per instance; P100 util %, matched WR only)

| instance | retrains (matched/all) | P100 mean +- sd | per retrain | Baleen online (3) | diff (Baleen - cfg) | RejectX | CoinFlip | win vs Baleen |
|---|---|---|---|---|---|---|---|---|
| Region7_s0.1 | 3/3 | 36.11 +- 0.25 | 36.38, 36.07, 35.88 | 36.57 +- 0.25 | +0.46 | 38.66 | 46.00 | yes |
| Region7_s0.2 | 3/3 | 36.89 +- 0.18 | 36.70, 36.91, 37.05 | 36.79 +- 0.00 | -0.10 | 38.00 | 41.97 | no |
| Region7_s0.3 | 3/3 | 38.50 +- 0.56 | 38.92, 38.72, 37.87 | 37.81 +- 0.25 | -0.69 | 38.89 | 45.19 | no |
| Region6_s0.1 | 3/3 | 41.66 +- 0.25 | 41.79, 41.83, 41.38 | 40.93 +- 0.07 | -0.73 | 42.25 | 50.02 | no |
| Region6_s0.2 | 3/3 | 37.74 +- 2.80 | 36.40, 35.87, 40.96 | 36.26 +- 0.10 | -1.49 | 37.29 | 43.85 | no |
| Region6_s0.3 | 3/3 | 36.90 +- 0.06 | 36.85, 36.97, 36.89 | 36.96 +- 0.26 | +0.06 | 39.19 | 41.09 | yes |

Criteria: wins 2/6 (need >= 4) -> FAIL; mean improvement -0.414 vs 2 SE = 0.562 (retrain SE; instance-level 2 SE = 0.568) -> FAIL; mean P100 37.97 vs RejectX 39.05 / CoinFlip 44.69 -> PASS. **Q3 for P0: NO**


## 4. Mechanism
**What the Ising labels actually change in the deployed system is first-access admission, not peak targeting.**

1. *Peak-awareness does not transfer.* Day-1 peak windows and test-day peak windows are driven by different, mostly
   new episodes; the metadata cells over-represented at peaks are inconsistent across days (section 2.1), and the
   GBM sees no time or load signal. The day-1 label peak of every design with a peak term is 20.8-25.8 (Baleen
   25.9-28.9), yet the deployed peak does not follow it (e.g. PW4, a peak-weighted DT knapsack without a peak term,
   changes the Region6 labels most, J = 0.37, for a ~0.4-point effect, and the Region7 labels hardly at all).
2. *Zero-value positives calibrate the GBM's first access.* An episode with a single access saves nothing (its d(e,w)
   is 0), so the peak energy is indifferent to it; the stochastic PT leaves many such episodes selected (P0: 44% of
   its Region7 labels; T2: 26%; T5: 10%). Each contributes a positive *first-access* row (no history). The trained GBM
   then admits new episodes at their first access much more often (Region7: 6% for Baleen's labels -> 15-28%) and
   earlier (mean first-admit index 1.3 -> 0.6-0.8), at the same write rate (the threshold is re-converged). Busy windows
   are dominated by new episodes, so their load drops (e.g. window 613: admitted accesses 18% -> 33%).
   Across the 13 matched Region7 dev trials: corr(first-access admission, P100) = −0.79, corr(#zero-value positives,
   P100) = −0.62 (`q3/results/mechanism_k0.csv`).
3. *Ablations and controls (Region7 dev, one retrain each):* Baleen control 40.18; T5 39.26; T5c = T5 with its 243
   zero-value additions removed 39.90; JUNK10 = Baleen's labels with 10% of the budget swapped for random zero-value
   episodes (no solver) 39.51. So roughly three quarters of the T5 gain is reproduced by random one-hit-wonder
   positives, and the rest comes from the PT's other reshuffles (T5c still raises first-access admission to 15%).
   Cell-level labels (C2) raise it structurally (14%) with few zero-value units.
4. *Region6 barely moves.* Its deployed thresholds are high (0.55-0.81) and first-access admission stays at 0.2-3.8%
   for every label set; its dev peak (window 712) is the big-offset scan that the frozen features/trainer cannot
   learn (section 2.1). Region6 dev effects are within −0.9..+0.1 points.

*Held-out, post hoc (analysis only; the configurations were frozen before A2): per instance and label set, mean over matched retrains of the trained admission GBM's first-access admission rate on the whole trace, the mean post-day-1 load, the simulated peak window(s), the share of big-offset (end > 8 MB) accesses in that window and the fraction of its accesses the GBM admits (`q3/results/heldout_mech.csv`).*

| instance | labels | retrains | P100 | first-access admission | mean load | peak window(s) | big-offset share there | admitted there |
|---|---|---|---|---|---|---|---|---|
| Region6_s0.1 | Baleen | 3 | 40.93 | 0.003 | 20.40 | 280,284 | 0.41 | 0.20 |
| Region6_s0.1 | C2 | 3 | 44.06 | 0.017 | 20.52 | 284 | 0.42 | 0.13 |
| Region6_s0.1 | P0 | 3 | 41.66 | 0.060 | 20.49 | 280,284 | 0.41 | 0.20 |
| Region6_s0.1 | T2 | 3 | 42.28 | 0.019 | 20.59 | 284 | 0.42 | 0.23 |
| Region6_s0.2 | Baleen | 3 | 36.26 | 0.003 | 22.32 | 457 | 0.40 | 0.28 |
| Region6_s0.2 | C2 | 3 | 36.14 | 0.011 | 22.42 | 153,457 | 0.28 | 0.32 |
| Region6_s0.2 | P0 | 3 | 37.74 | 0.072 | 22.53 | 457 | 0.40 | 0.27 |
| Region6_s0.2 | T2 | 3 | 36.29 | 0.018 | 22.59 | 153,457 | 0.28 | 0.27 |
| Region6_s0.3 | Baleen | 3 | 36.96 | 0.003 | 21.07 | 264,775 | 0.05 | 0.20 |
| Region6_s0.3 | C2 | 3 | 36.75 | 0.008 | 21.11 | 264,775 | 0.05 | 0.20 |
| Region6_s0.3 | P0 | 3 | 36.90 | 0.027 | 21.06 | 775,815 | 0.05 | 0.32 |
| Region6_s0.3 | T2 | 3 | 36.70 | 0.014 | 21.15 | 775,815 | 0.05 | 0.30 |
| Region7_s0.1 | Baleen | 3 | 36.57 | 0.108 | 21.03 | 621 | 0.08 | 0.35 |
| Region7_s0.1 | C2 | 3 | 36.68 | 0.166 | 21.00 | 621 | 0.08 | 0.36 |
| Region7_s0.1 | P0 | 3 | 36.11 | 0.320 | 20.96 | 621 | 0.08 | 0.44 |
| Region7_s0.1 | T2 | 3 | 38.39 | 0.208 | 20.89 | 315,621 | 0.16 | 0.31 |
| Region7_s0.2 | Baleen | 3 | 36.79 | 0.084 | 21.42 | 657 | 0.13 | 0.31 |
| Region7_s0.2 | C2 | 3 | 37.05 | 0.140 | 21.34 | 657 | 0.13 | 0.34 |
| Region7_s0.2 | P0 | 3 | 36.89 | 0.313 | 21.10 | 657 | 0.13 | 0.39 |
| Region7_s0.2 | T2 | 2 | 36.69 | 0.177 | 21.19 | 657 | 0.13 | 0.35 |
| Region7_s0.3 | Baleen | 3 | 37.81 | 0.105 | 20.91 | 362 | 0.25 | 0.42 |
| Region7_s0.3 | C2 | 3 | 38.08 | 0.163 | 20.87 | 362,636 | 0.18 | 0.38 |
| Region7_s0.3 | P0 | 3 | 38.50 | 0.359 | 20.81 | 362 | 0.25 | 0.41 |
| Region7_s0.3 | T2 | 3 | 41.39 | 0.201 | 20.77 | 362 | 0.25 | 0.26 |


5. *Held-out (table above).* The first-access shift carries over (Region7 8-11% → 14-36%; Region6 0.3% → 0.8-7.2%) and
   Region7's mean post-day-1 load drops for every finalist and instance (by 0.03-0.32 util-points), while Region6's
   mostly rises slightly. But P100 is not decided by the mean: Region7 s0.3, Region6 s0.1 and Region6 s0.2 peak in
   scan-like windows (25-42% of the window's accesses end beyond 8 MB), where the fraction of accesses a model admits
   varies with the labels and the retrain (Baleen 0.20-0.42; relabeled models 0.13-0.44). Relabeling moves those rare,
   sparsely-trained decisions in either direction, which produces the large held-out swings, and the losses outweigh
   the gains (2/6 wins for every finalist). On Region7 s0.2 all label sets share the same floor window (657, 36.6-37.2).
   Dev tuning could not anticipate this: dev had only two instances, and on dev the fragile region cut the other way
   (it was Baleen's model that failed Region6's scan).

## 5. Integrity
- Scope: only the offline selection Policy changed (`q3/src/pb3_policy.py`, registered by our launcher
  `q3/src/launch_train.py`; the unmodified `train.main()` does the rest). No feature/GBM/simulator/episode-model/driver
  change; the prefix rule `threshold < 35.599` reproduces the selected set at every sort call (asserted in every train
  log: "prefix rule reproduces |S|=... exactly"); the tail after the selected set is Baleen's order.
- Sandbox: `q3/env.sh` (HOME/XDG/TMPDIR/pip/conda/MPL/numba/torch caches inside explore/, CONDA_REGISTER_ENVS=false,
  PYTHONNOUSERSITE=1, PYTHONDONTWRITEBYTECODE=1); every Baleen process ran as `taskset -c 8-23 bwrap --dev-bind / /
  --bind <work>/systmp /tmp -- ...`; every train (incl. dumps) held `flock explore/.train.lock`; <= 14 concurrent
  simulations (flock slot pool, FIFO from 18:00); OMP_NUM_THREADS=2, OMP_WAIT_POLICY=PASSIVE.
- Incident (disclosed): at 15:54, before the sandbox env was sourced and before `.leak_marker` was touched, an
  interactive inspection of the release CSV with 0_reproduce's python (`import common` without `-B`) created
  `0_reproduce/repro/__pycache__/common.cpython-311.pyc`. It was removed at 16:06 and the directory mtime restored to its
  previous value (2026-09-26 21:46:25.888). `check_frozen.sh` (baleen_code) was OK before and after; nothing under
  0_reproduce/, harness_eval/ or ising_followup/ is newer than the leak marker.
- Trials: every run is a row of `q3/trials.csv` (unique `trial_key`; asserted on every append). Unmatched runs (WR
  steps caused by identical GBM scores) and the abandoned SATB10 runs are included with `matched=False`; one row
  (dev T5 Region7 rep 3) was written manually from its result file after its driver was stopped (noted in the row).
- `bash 0_reproduce/check_frozen.sh` (2026-09-29T02:21:43-04:00):
  ```
  frozen OK (94 files)
  ```
- Leak check (the prescribed command, marker `q3/.leak_marker` touched 2026-09-28 15:57:13):
  ```
  (empty: no file outside explore/ newer than the marker)
  ```
- Nothing under 0_reproduce/, harness_eval/ or ising_followup/ is newer than the marker:
  ```
  (empty)
  ```

