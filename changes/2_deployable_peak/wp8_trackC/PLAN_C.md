# Track C plan: Stage 2 (dev screen with full simulations) and Stage 3 (fresh test)

**Status:** written 2026-10-16 at the end of Stage 1, BEFORE any Stage-2 simulation or artifact training. The
finalist rule (§3) and the fresh-test design (§4) are fixed here; they may only be changed by a dated addendum
written before the first Stage-2 / Stage-3 run they affect.

Stage-1 evidence: `results/stage1_table.md`, `results/proxy_validation.md`, `PROGRESS.md`.

## 1. What Stage 1 established (DEV only; numbers in `results/stage1_table.md`)
- **The cheap proxy is NOT valid** by its pre-registered criterion (PL median per-instance Spearman 0.49 < 0.5;
  C2 and C3 pass; WP2's real models with the calibrated threshold do no better, median 0.37). Stage 2 therefore
  screens every short-listed configuration with **full simulations**; PL numbers are diagnostics only and are never
  used to drop or rank a configuration.
- The proxy's first-access-admission estimate IS reliable (Pearson 0.98 vs WP2's model-based k0 over 128 cells), so
  it is used to verify the mechanism a design is meant to change (Region7 first-access admission).
- **C-anchor** keeps most of F1's day-1 peak reduction with a small edit of Baleen's labels and restores Baleen-level
  first-access admission in the emulator (the Region7 failure mode of X1).

## 2. Stage-2 dev screen (full simulations)
**Short-list** (the exact configs and the reasons are in §5, filled from the Stage-1 table):
each config = Track C label design (PT, 10 s, 4 numba threads, seed = retrain k) + `meta+block+chunk+load` +
load-adaptive threshold α = −1 (arm-E form, as X1). The same retrain's models are also simulated with α = none
(sim-only variant, arm-D form) for the 2×2 with WP2 — reported, not eligible.

**Pipeline:** copy WP2's driver logic (`wp2_deployed/src/wp2.py`, `wpcommon.py`, `pb4_policy.py`,
`wp2_launch_train.py`) into `wp8_trackC/src/` (already copied; Stage 2 adds a plan entry `E8:<design>` that reads
labels from `wp8_trackC/labels/`). Labels are applied by `PolicyPeakBaleen4` by episode identity (files already
solved for seeds 1–3, same format as WP2).
- Every train holds `flock 2_deployable_peak/.train.lock`; every sim takes a slot of the shared `SimSlot`
  (WP2's cross-process slot pool, cap 6 while other tracks run). CPUs per the coordinator at launch time.
- Every Baleen process: taskset + `bwrap --dev-bind / / --bind <private job tmp> /tmp -- $BALEEN_PY -B`.
- Matched write rate 35.599 MB/s ± 1%, threshold converged by full sims (≤ 7), search range (0, 4] for α arms
  (PROTOCOL_v2_H3 §3). Emulator only seeds the search.
- Ledger: `wp8_trackC/trials.csv`, one row per evaluation (also failures/unmatched), WP2's columns.

**Screen:** 1 retrain (seed 1) × 8 dev instances per short-listed config.
**Confirmation:** retrains 2–3 for the configs that pass the screen gate (§3), at most 2 configs.
**References are NOT re-run:** WP2's dev trials (`wp2_deployed/trials.csv`) for A, B, A+α (Aa-1.0 ∪ Ax-1.0),
B+α, X1 (Ea-1.0:F1PT) are used as they are, paired by instance (and by retrain index for the rep-1 screen).
**Cost:** screen ≈ 3–4 configs × 8 = 24–32 evaluations (≈ 1 train + 3 sims each) ≈ 2–3 h at 6 sims;
confirmation ≈ 2 × 8 × 2 = 32 evaluations ≈ 3 h.

## 3. FINALIST RULE (fixed 2026-10-16, before any Stage-2 simulation)
- **Candidates:** Track C configurations whose labels come from the Ising solver (PT, `labels_c.py`), with `load`
  and α = −1. CP-SAT-labelled controls (e.g. ANC10CP) are comparison arms, never candidates.
- **Bar:** X1 and A+α on dev, paired per instance. For configuration Y and instance i (P100 = mean over matched
  retrains): d_i = min(X1_i − Y_i, Aa_i − Y_i) (positive = Y better than both).
- **Screen gate (rep 1):** S1(Y) = mean_i of d_i computed with rep 1 of Y against rep 1 of X1 and of A+α. Confirm
  (reps 2–3) the configurations with S1 > 0, at most 2, ranked by S1 (tie-break: #instances with d_i > 0).
- **Eligible:** ≥ 3 matched retrains on all 8 dev instances (extra seeds 4–6 if a retrain is unmatched, as WP2).
- **Finalist:** S(Y) = mean_i d_i (all matched retrains) > 0, AND Y beats X1 on ≥ 5/8 instances, AND Y beats A+α
  on ≥ 5/8 instances, AND on neither region (Region7: 4 instances; Region6: 4 instances) is Y's mean P100 worse than
  A+α's by more than 0.5 util-pts. At most 1 finalist (highest S; tie-break: #instances with d_i > 0).
- If no configuration qualifies, Track C reports a negative dev result (with mechanism) and Stage 3 is not run.
- Dev scores of the finalist are selection-biased; only Stage 3 is evidence.

## 4. Proposed fresh test (Stage 3): Region5, deployed — never run deployed by this project
**Why Region5:** it has not been used for any deployed run, tuning or selection (WP1 used Region5 only OFFLINE for
H1′ breadth, OPT on full traces, which says nothing about a deployed model); its offline peak-aware headroom is of
the Region6/7 size (≈ −16%, WP1), unlike Region4 (−3 to −5%). It is a different region, so it also tests
transfer of every dev choice (λ, α).

**Authors' rows (checked read-only in `results_release.csv.gz`, Stage 1):** trace group 20230325, 0.1% sampling;
Fig 9 Baleen variant for Region5 = **"ML-Range on Partial Hit"** (experiment `20230421_alltraces_pfalways`), one
row per sample 0, 0.1, …, 0.9; RejectX/CoinFlip `20230410_static_pf` rows for every sample; one `OPT AP` row per
sample. All Region5 trace samples are present locally (`explore/common/data`, sha1-checked in phase 1).

**Design:**
- **Pipeline dry run:** Region5 **s0**, arm A only (1 retrain), to check job construction (make_jobs logic for the
  "ML-Range on Partial Hit" variant), the day-1/fullml instance dump and threshold convergence. Not part of any
  verdict.
- **Test instances:** Region5 **s0.1–s0.6** (6 instances), touched once, after a test protocol (copy of
  PROTOCOL_v2_H3 with the Track C finalist) is committed. **Reserve s0.7–s0.9 untouched** (as for every region).
- **Arms (3 retrains each, matched WR ± 1%):** Y (Track C finalist), X1, A, B, A+α, B+α; RejectX/CoinFlip as the
  authors' bit-exact replays. Optional comparison: Y's CP-SAT-labelled control.
- **Pass rule (phase-1 Q3 / H3′ rule):** Y beats each of A, B, X1 and A+α on ≥ 4/6 instances with mean
  improvement > 2 SE (retrain-level SE as PROTOCOL_v2_H3 §5; instance-level SE also reported), and is below
  RejectX's and CoinFlip's means. The claim "Ising labels carry deployed gain beyond the threshold" requires the
  A+α and X1 comparisons.
- **Prerequisites before the first test run:** jobs for Region5 s0.1–0.6 built from the release CSV; day-1 and
  fullml instances dumped through the unmodified driver; label sets for Y (and X1's F1PT) solved for seeds 1–3;
  RejectX/CoinFlip replays; protocol committed.
- **Cost:** ≈ 6 arms × 6 instances × 3 retrains ≈ 108 evaluations (+ dry run) ≈ 6–8 h at 6 sims.

## 5. Short-list for Stage 2 and reasons (fixed 2026-10-16, before any Stage-2 run)
The proxy is not valid, so the short-list rests on offline + mechanism + learnability; the PL columns are quoted
only as diagnostics. All with `load` and α = −1 (arm-E form, as X1).

| config | why short-listed | known risk |
|---|---|---|
| **E8:ANC3** | Baleen-anchored F1: 96% of F1's day-1 peak cut (21.78 vs 21.51; Baleen 28.14) with only ~300 label flips (J 0.84); stability J 0.92 (F1PT 0.76); restores emulated first-access admission (0.056 vs X1 0.020) -> targets X1's Region7 failure; learnability net 0.025 | proxy (diagnostic) loses Region6 vs X1 (35.90 vs 34.18) |
| **E8:ANC10** | tighter anchor: 82% of the peak cut with ~150 flips (J 0.92, stability 0.95); the most Baleen-like Ising labels that still carry a peak edit | same, stronger (Region6 PL 36.26) |
| **E8:STU10R1** | student-field round 1: same offline peak as F1 (21.67), highest learnability (0.052) and best diagnostic PL mean (34.89; both regions) | introduces ~34 zero-value positives per set (phase-1 instability mechanism); stability 0.75 |

Comparison only (not eligible): **E8:ANC10CP** (same anchored energy by CP-SAT, 10 s) on the instances where ANC10
is run, if the budget allows (8 evaluations).

Dropped, with reasons: TK10 (CVaR_10 = max on day 1: the min-max optimum is a plateau of ≥ 30 windows, labels ≈ F1);
TK72 (half-day CVaR raises the day-1 peak to 26.0, little left of the peak edit); ANC10TK10 (≈ ANC10); ANC30 (only
58% of the peak cut, worst diagnostic PL); STU10R2 / STU30R1 (≈ STU10R1 with 2× more zero-value positives);
C-potts-load (not implemented: phase-1 C2 cell couplings failed held-out; an episode's rows span many load buckets,
so a per-episode label cannot be coupled by load cell; the student field is the learned, load-aware version of the
same idea).
