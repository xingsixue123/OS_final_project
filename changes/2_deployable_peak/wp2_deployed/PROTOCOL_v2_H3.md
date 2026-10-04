# PROTOCOL v2: H3′ (deployability), test-set protocol

**Status: FINAL as written by Track A at CP2 (2026-10-04), from the dev results in `RESULTS_dev.md`.** It replaces the 2026-10-01 17:23 draft. The coordinator must commit this file before any run on samples ≥ 0.4. Nothing in it was chosen by looking at test data: no test sample has been touched.

## 1. Hypotheses

**H3′ (PLAN.md §2, primary).** Peak-aware labels **produced by an Ising-family solver**, together with the causal demand-load signal, beat **both**:
- arm A: Baleen's own labels, original features;
- arm B: Baleen's labels + the `load` feature;

on the test set, at matched write rate, with ≥ 3 retrains each.

On dev, the only configurations that met the finalist rule are of PLAN arm type E: they use the demand-load signal both as a GBM feature and through the load-adaptive admission threshold (SCOPE_v2 §1.2). The primary configuration X1 therefore includes that threshold (§3).

**H3′-labels (secondary, pre-registered here).** Does X1's gain come from the Ising labels, or from the load-adaptive threshold alone? On dev the same threshold applied to Baleen's own models gives part of the gain (`RESULTS_dev.md` §6). So X1 is also compared, with the same rule, to:
- A+α (arm A's retrains + the same threshold);
- B+α (arm B's retrains + the same threshold).

H3′-labels is reported separately. It does not change the H3′ verdict.

**Solver question (comparison only, no pass/fail).** X1 vs the same configuration with the labels solved by OR-Tools CP-SAT ("Dc+α").

## 2. Instances

**Test, touched once, after this file is committed:**
- Region7 and Region6 (trace group 20230325, 0.1% sampling), samples 0.4, 0.5 and 0.6: 6 instances.
- None of them has been used for any tuning, selection or inspection.

**Reserve, untouched:** samples 0.7–0.9 (final paper).

**Dev, where all tuning and selection happened:** samples 0, 0.1, 0.2 and 0.3 of the same two traces.

## 3. Configurations (all through the reviewed overlay `wp0_overlay/overlay`, PATCH.diff at commit f79808f)

### Common to every arm

**Commands.**
- Base: the authors' per-sample Fig 9 Baleen TrainCommand / ReproduceCommand from `results_release.csv.gz`:
  - Region7: ML-Range on ML-When;
  - Region6: All on Partial Hit.
- Path rewrite, `+ --eviction-policy LRU` and `- --offline-ap-decisions`, exactly as `explore/common/src/make_jobs.py`.
- On top of that, only the arm's options below, plus `--exp`/`-o`/`--job-id` and `--ap-threshold`.

**Retrains.**
- Retrain k = a new episode generation (the artifact's own nondeterminism is kept, SCOPE_v2 §1a), label-solver seed k, and new GBMs.
- The adaptive-threshold variants (X1, X2, A+α, B+α, Dc+α) re-use retrain k of their base arm (D, A, B, Dc). The threshold is a simulation-only option, so comparisons are paired.

**Matched write rate.**
- Target 35.599 MB/s ± 1%. `--ap-threshold` is converged by simulation: sequential, seeded by the emulator, at most 7 sims; code in `wp2_deployed/src/wp2.py` (copy to wp3).
- **Threshold search range:**
  - (0, 1) for arms without α;
  - **(0, 4] for every arm with α.** With g ∈ [0.25, 4] the base threshold may legitimately exceed 1. On dev the Baleen-model controls needed 1.01–1.29 on Region6 (`RESULTS_dev.md` §8).

### Arms

| Arm | Labels (day 1) | Admission features | Options | Role |
|---|---|---|---|---|
| **X1** (primary) | F1PT | `meta+block+chunk+load` | `--ap-load-adapt-alpha -1.0` | H3′ |
| X2 (secondary finalist) | F1PT | `meta+block+chunk+load` | `--ap-load-adapt-alpha -0.5` | reported with the same rule; no claim |
| A | Baleen (authors' policy `PolicyUtilityServiceTimeSize2`) | `meta+block+chunk` | none | baseline |
| B | Baleen | `meta+block+chunk+load` | none | control: the signal alone |
| A+α | Baleen | `meta+block+chunk` | α = −1.0 (A's retrains) | H3′-labels control |
| B+α | Baleen | `meta+block+chunk+load` | α = −1.0 (B's retrains) | H3′-labels control |
| Dc+α | F1CPSAT | `meta+block+chunk+load` | α = −1.0 | solver comparison |
| RejectX, CoinFlip | none | none | the authors' `20230410_static_pf` commands (bit-exact replays) | baselines |

**Label designs.**
- **F1PT:**
  - Formulation: the true min–max day-1 peak (q2 F1) on `day1_<inst>.npz`, all 145 day-1 windows, the harness budget B. Built through the unmodified driver as `explore/common/src/a0.py`.
  - Solver: the q2 parallel-tempering finalist with its frozen 10 s configuration (`explore/q2/plan_F1.json`, `pt`, `cfg_by_budget["10"]`, LP start, 8 numba threads), single level f = 1.0, 10 s budget, seed = retrain k.
  - Labels: core selection + the harness's strict-prefix Baleen-order fill, re-applied in each run by `PolicyPeakBaleen4` (`wp2_deployed/src/labels.py`, `src/pb4_policy.py`).
- **F1CPSAT:** the same, solved by CP-SAT with q2's classical finalist configuration (10 s).

**Load-adaptive threshold (overlay defaults):** θ_t = θ · clip((load_10m / 20)^α, 0.25, 4), where load_10m is the trailing 10-minute GET demand in utilisation % at the access time; `--ap-load-adapt-ref 20 --ap-load-adapt-window 10`.

**Label solver.** Track B's WP5 work is finished and the H2′ test failed (coordinator note, 2026-10-04). The label solver is therefore fixed to the phase-1 PT configuration above, which is exactly what dev used.

## 4. Retrains, unmatched runs, logging

- 3 retrains per (arm, instance), seeds 1, 2, 3.
- A retrain whose threshold search ends unmatched is excluded and reported. If an (arm, instance) has fewer than 3 matched retrains, more retrains with seeds 4, 5, 6 are run until 3 are matched (at most 6 retrains).
- Every retrain, including failures, is one row of `wp3_test/trials.csv` with a unique key.

## 5. Pass criteria (phase-1 Q3 rule, PLAN.md §2)

P100 is `PeakServiceTimeUtil1`: the mean over matched retrains per instance, over the 6 test instances.

**H3′ = YES iff X1 meets all of:**
1. **vs A:**
   - mean P100 below A's on ≥ 4/6 instances; and
   - mean improvement (A − X1) > 2 SE, with SE = sqrt(Σ_i s²_X1,i/n_X1,i + s²_A,i/n_A,i) / 6 (retrain-level, as in phase 1; the instance-level SE is reported too).
2. **vs B:** the same two conditions.
3. **Baselines:** mean P100 below RejectX's and CoinFlip's means.

**Other judgements.**
- **X2:** judged by the same rule and reported as secondary. No claim rests on it.
- **H3′-labels = YES iff** X1 meets conditions 1 and 2 against A+α and against B+α. If H3′ is YES but H3′-labels is NO, the gain is attributed to the load-adaptive threshold, not to the Ising labels.
- **Dc+α:** paired difference per instance with its SE; no pass/fail.

**Also reported (no pass/fail):**
- P99, top-5 mean, mean DT, write rate;
- first-access admission;
- retention R = (A − X)/(OPT_peak-blind − OPT_peak-aware), with offline OPT runs on the test instances;
- the peak window's big-offset share;
- the 2×2 (A, B, C = F1PT labels without load, D = F1PT + load without α) only if the budget allows. C and D are not required for the verdict.

## 6. Dev evidence for the finalists (from `RESULTS_dev.md`; selection by the rule in `PROGRESS.md`, written 2026-10-03 00:20)

| | dev mean P100 (8 instances) | vs A | vs B | S = mean_i min(A_i − X_i, B_i − X_i) |
|---|---|---|---|---|
| X1 Ea-1.0:F1PT | 37.20 | +1.30 ± 0.25 (6/8) | +1.24 ± 0.26 (6/8) | +1.03 |
| X2 Ea-0.5:F1PT | 37.84 | +0.66 ± 0.29 (5/8) | +0.60 ± 0.30 (5/8) | +0.39 |
| A / B | 38.50 / 38.44 | | | |
| A+α / B+α (controls) | 37.88 / 38.43 | | | |

X1 vs A+α: +0.68 (5/8; instance-level SE 0.63). X1 vs B+α: +1.23 (5/8).

**Caveats known before the test:**
- Dev selection effect: two screens, the α tuning and the finalist choice all used dev data.
- X1's retrain spread is large on Region7 s0.3 (sd 1.81) and Region6 s0.1 (sd 2.56).
- The dev gain is concentrated on Region6.

## 7. Prerequisites before the first test run (none of them looks at test outcomes)

1. Teammate review of `PATCH.diff` recorded (G3, SCOPE_v2 §1a).
2. Test jobs (samples 0.4–0.6) built from `results_release.csv.gz` with the make_jobs logic.
3. Day-1 and fullml instances built through the unmodified driver (Policy dump, as `explore/common/src/a0.py`).
4. Label sets solved with `labels.py` (designs F1PT and F1CPSAT, seeds 1–3).
5. RejectX/CoinFlip replays.
6. This file committed (CP2).
