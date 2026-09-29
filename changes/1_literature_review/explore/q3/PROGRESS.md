# Track A (q3 + common) progress log

## A0.1 data (DONE 15:58)
- storage_0.1_10.tar.gz downloaded to common/raw (HOME sandboxed), extracted, assembled at common/data/tectonic/<group>/<region>/
  (all 7 traces x samples 0..0.9); sample 0 = read-only relative symlinks to 0_reproduce/work/data; results_release.csv.gz
  symlinked. sha1: 70/70 trace files OK against each region's checksums.sha1. -> common/DATA_READY
- Integrity note: at 15:54 (before the sandbox env was sourced) an interactive CSV inspection with 0_reproduce's python
  created 0_reproduce/repro/__pycache__/common.cpython-311.pyc (no -B). Removed at 16:06, directory mtime restored;
  check_frozen.sh OK. All later processes run with env.sh (PYTHONDONTWRITEBYTECODE=1) and -B.

## Infrastructure (DONE 16:10)
- common/src/xc.py (paths, taskset 8-23 + bwrap runner, flock X/.train.lock, sim slot pool <=14, metrics, convergence),
  common/src/make_jobs.py -> common/jobs.json (authors' per-sample commands via 0_reproduce/repro/common.py, read-only),
  common/src/a0.py (dumps + baselines), q3/src/pb3_policy.py (Policy; harness_eval semantics + per-access GBM features),
  q3/src/launch_train.py.
- Feature check (q3/results/verify_features_Region7_s0.json): the dumped per-access features equal the frozen trainer's
  df_X on all 31,105 rows (18 columns, max abs diff 0) and the dumped Baleen labels equal its threshold_binary labels.
- Dev instances: harness_eval copies (common/inst/hx_*) == our own dumps up to episode permutation (C, D, s, B identical).

## A0.2/A0.3 (RUNNING, started 16:10): held-out dumps, then OPT / Baleen online x3 / RejectX+CoinFlip (static_pf rows).

## A0.2 instances (DONE 16:27) -> common/INSTANCES.md, common/INSTANCES_READY
- day1_* (authors' Baleen TrainCommand args per sample, no GBMs) and full_* (OPT EA, skip 144) for dev + held-out;
  pbcore.Instance loads all; dev copies of harness_eval instances in common/inst/hx_*.

## A1 diagnosis on dev (16:15-16:40)
- Deployed peaks come from a few windows (R6: 712 = 43.3 vs next ~40; R7: 646/660/613). Most load there is from episodes
  that START in the window.
- Cheap proxy (score all accesses with simulator-style features, emulate admission analytically): tracks simulated WR
  along each model's threshold curve (r=0.975/0.995 on 37 harness_eval models) but does NOT rank models at matched WR
  (r~0). Used only to seed the WR-matching threshold search (log-space map), not to screen P100.
- First-access feature-cell policies are far worse than the GBM (history counts carry most signal); day-1-optimal cells
  do not generalize (q3/results/cellan_Region7.json).
- Diagnostic sims (existing flags only): Baleen's peak-blind OPT decisions under the DEPLOYED prefetcher give R6 P100
  37.8 with window 712 at 25.7 (online: 43.3) -> the R6 peak is an online-admission failure.
- Mechanism: at R6 window 712 a long sequential scan (447 accesses, 174 chunks = 21.7 MB block) is admitted while its
  offsets are < ~10 MB, then the GBM score collapses (0.97 -> 0.04-0.09) at larger offsets: all 282 accesses in 712 are
  rejected (online misses 491 IOs there vs 197 under OPT). Big-offset accesses (end > 8 MB, ~5-6% of accesses) are
  rejected 92-99.5% of the time vs 64-68% for others and carry 20 util-points of R6's 712 load (5-7.5 at R7's top).
  Day-1 scans of this type ARE Baleen-positive, but the trainer uses only each episode's first 15 accesses (small
  offsets, block count <= 14), so the big-offset/high-count region is learned only from other, mostly negative rows;
  flipping those rows positive would cost 55-86% of the day-1 write budget.

## A1 screening (RUNNING): trust-region PT (T5/T2), pure peak (P0), Baleen control (R0), peak-weighted DT (PW4),
   top-k (TK10), kNN consistency (L5), cells (C2); 1 retrain per dev trace; results -> q3/trials.csv.

## A1 early screen signal (17:30, partial, not yet WR-matched)
- Region7 dev: trust-region PT labels (T5: mu=5, beta=1, LSE peak; TK10: top-10 peak) reach P100 ~38.9-39.1 at WR 34.5-36.7
  vs the Baleen control 40.14 at WR 34.5 (0_reproduce Baleen ref 40.10 +- 0.18); mean post-day-1 load also drops
  (21.61 -> 21.27-21.32). Region6: T5 ~43.0 at WR 36.0 (Baleen 43.25).
- Mechanism (trained admission GBMs scored on all accesses): T5/TK10 models admit an episode's FIRST access 3.4x more
  often (17% vs 5%), admit 50% more episodes, and earlier (mean first-admit index 0.8 vs 1.3) at the same WR. The PT
  leaves zero-value single-access episodes (no effect on day-1 loads, small trust cost) in the labels (256 of 412
  additions on Region7), i.e. extra positive first-access rows. Ablations queued: T5c (same config, zero-value
  additions removed -> Baleen fill) and JUNK10 (NOT an Ising candidate: Baleen labels with 10% of the budget swapped
  for random zero-value episodes).
- Sim-slot pool made FIFO (a run's last simulation had been starved for 33 min under random polling).

## A1 screen status (18:25)
- Matched so far: T5 R7 39.26 / R6 43.07; PW4 R6 42.81 (dev Baleen refs 40.10 +- 0.18 / 43.25 +- 0.04).
- Admission profiles of all trained screen GBMs (q3/src inline analysis): on Region7 every PT variant (T5, TK10, T2, L5,
  SAT12, C2) raises first-access admission from 6% (control) to 13-22% and reaches P100 ~39.1-39.4 (closest-to-target
  thresholds); PW4 (no first-access shift) shows no gain (40.26). The non-Ising JUNK10 control (random one-hit wonders
  as positives) raises it to 9.5% and reaches 39.57 at WR 32.3 -> the Region7 gain is mainly "more first-access
  positives", not peak-awareness. Region6: first-access admission stays ~0-3% for all; P100 42.7-43.3 (the window-712
  big-offset scan dominates).
- Queued: reps 2-3 of T5, TK10, T2, L5 on both dev traces (confirmation, >=3 retrains); T5c / JUNK10 / SATB10 rep1.
- Baselines: OPT done (6/6); RejectX 6/6; CoinFlip 4/6; Baleen online 12/18 retrains.

## A0.3 baselines (DONE 19:30) -> common/baselines.csv, common/BASELINES_READY
- Held-out Baleen online 3 retrains each (matched), RejectX/CoinFlip bit-exact vs the authors at their ap-probability
  (all within +-1% WR, no bisection), peak-blind OPT converged. Dev rows reused (0_reproduce, harness_eval).

## A1 dev status (19:30)
- Matched: R7 control (R0 via solver path) 40.18 (ref 40.10+-0.18); T5 39.26; T2 39.23; SAT12 39.37; PW4 40.26.
  R6: T5 43.07, 42.91; TK10 43.27; PW4 42.81; P0 42.94; C2 43.21; SAT12 43.32; JUNK10 43.39 (ref 43.25+-0.04).
- SATB10 abandoned after training (logged in trials.csv) to free simulation throughput.

## PRE-REGISTERED finalist rule (19:35, before the confirmation retrains are complete)
- Eligible: Ising-family configs (PT) with >= 3 matched retrains on BOTH dev traces (candidates: T5, TK10, T2, L5;
  controls R0/JUNK10 and cleanup ablation T5c are not eligible as finalists unless they meet the same bar; JUNK10 never
  (not an Ising solver)).
- Score = mean over the two dev traces of (dev Baleen reference mean - config mean P100) (references: 0_reproduce 9
  retrains, 40.10 / 43.25). Finalists = the (up to) 3 highest scores with score > 0; ties (< 0.05) broken by lower
  pooled retrain SD. Each finalist then runs 3 retrains on all 6 held-out instances and is reported however it turns out.

## A1 ablations (20:12)
- Region7: control R0 40.18; T5 39.26; T5c (T5 with zero-value additions removed) 39.90; JUNK10 (non-Ising: Baleen +
  random zero-value positives) 39.51 -> most of the Region7 gain comes from zero-value one-hit-wonder positives
  (first-access admission shift), a smaller part from the peak-aware reshuffle.
- Region6: T5c 43.06, T5 43.07/42.91, JUNK10 43.39, T2 42.33 (rep1), L5 43.28 (ref 43.25).
- TK10 Region7 rep1 is UNMATCHABLE: 242 accesses share one GBM score (0.4771624) -> WR jumps 36.21 -> 34.60 at that
  threshold (P100 39.08 on both sides); will be logged unmatched.
- 20:42: queued P0 reps 2-3 (both dev traces; P0 rep1 heading to ~38.7 on R7) and TK10 rep4 on Region7 (rep1
  unmatchable) so that both can meet the pre-registered >=3-matched-retrains eligibility bar.
- 20:58: queued C2 reps 2-3 (both dev traces; C2 rep1 R7 38.89) for the same eligibility bar.

## Mechanism table (21:05, q3/results/mechanism_k0.csv)
- Across the 13 matched Region7 dev trials: corr(first-access admission of the trained GBM, P100) = -0.79;
  corr(#zero-value positives in the labels, P100) = -0.62. P0 labels are 44% zero-value one-hit wonders -> first-access
  admission 28% -> 38.71. T5c (no zero-value additions) 14.8% -> 39.90; C2 (cells) 14.3% -> 38.89; control 6% -> 40.18.
- Region6: first-access admission 0.2-3.8% for every label set (GBM threshold 0.55-0.81); P100 42.3-43.4.
- Controls through the pipeline reproduce Baleen: R0 Region7 40.18, Region6 43.27 (refs 40.10 / 43.25).

## FINALISTS (21:50, by the pre-registered rule)
- Complete scores (mean dev improvement over the two traces): P0 0.63 (R7 39.16+-0.40, R6 42.93+-0.18), T2 0.60
  (R7 39.36+-0.17, R6 42.78+-0.40), L5 0.51 (R7 39.12+-0.18, R6 43.21+-0.07). Pending candidates bounded from their
  simulated points: T5 ~0.49, C2 ~0.52, TK10 ~0.50 and ineligible (two unmatchable Region7 retrains, WR steps).
  -> P0 and T2 are certain finalists: A2 started for both (6 held-out x 3 retrains). Third finalist = C2 or L5 when
  C2 completes.
- 22:00: dev complete for the ranking (q3/results/finalist_scores.txt): P0 0.624, T2 0.603, C2 0.603 (R7 38.93+-0.56,
  R6 43.21+-0.13), L5 0.506; T5/TK10 cannot reach C2 (TK10 ineligible). FINALISTS = P0, T2, C2. A2 started for C2.

## A2 (held-out) running since 21:50 (P0, T2) / 22:00 (C2); early results
- T2 R7 s0.2 rep1 36.78 (Baleen 36.79+-0.00); T2 R7 s0.3 rep1 42.85 (Baleen 37.81+-0.25): post-hoc, window 362 (25% of
  its 649 accesses beyond 8 MB, a scan event) goes 37.5 -> 42.9 because T2's GBM admits 21% of that window's accesses vs
  42% for Baleen's, although T2 lowers the mean load (20.93 -> 20.74) and most other top windows (first-access admission
  11% -> 22%). The fragile big-offset/high-count region decides P100 on rare scan events.
- TK10 dev Region7 rep1 and rep3 logged unmatched (WR steps from identical GBM scores; no threshold within +-1%).
- 22:55: held-out rep1 so far: R7 s0.1 T2 36.05 / C2 37.00 / P0 36.38 (Baleen 36.57+-0.25); R7 s0.2 T2 36.78 / C2 36.77
  (Baleen 36.79); R7 s0.3 T2 42.85 / C2 39.15 (Baleen 37.81); R6 s0.1 C2 49.50 (Baleen 40.93). 41/54 held-out trains
  done; ~200 simulations remain (ETA ~01:15).
- Dev T5 Region7 rep3 row corrected (its driver was stopped after its matched point, WR 35.35, had been simulated):
  T5 dev = R7 39.35+-0.32, R6 43.01+-0.09 (score 0.495; finalists unchanged).
- 23:55 post-hoc held-out mechanism (partial, q3/src/heldout_mech.py): relabeled GBMs raise first-access admission on
  held-out too (R7 8-11% -> 15-33%; R6 0.3% -> 1.4-6.6%) and often lower the mean load, but P100 is set by scan-like
  windows with large big-offset shares (R7 s0.3 w362: 25%; R6 s0.1 w284: 42%) where the admitted fraction can collapse
  (T2 R7 s0.3 42% -> 21%: +4.6..5.0; C2 R6 s0.1 20% -> 8%: +8.6). 20/54 held-out runs done.
- 00:50 preliminary held-out evaluation (partial, 27/54 runs): T2 1/5 wins, mean change -1.93 (catastrophic R7 s0.3
  +4.8 and one R7 s0.1 retrain 42.69); C2 2/6 wins, -0.72 (R6 s0.1 49.50 / 41.03); P0 1/4 wins, -0.17. Q3 is heading to NO.

## A2 DONE (02:21) -> q3/results/q3eval_heldout.{csv,md}, q3/results/heldout_mech.csv; RESULTS.md written (02:30)
- Q3 = NO for all finalists (held-out, 3 retrains each, matched WR): P0 2/6 wins, mean change -0.41 (2SE 0.56);
  T2 2/6, -1.07 (2SE 0.85); C2 2/6, -0.57 (2SE 0.96); all below RejectX (39.05) / CoinFlip (44.69) on average, as is
  Baleen (37.55). One held-out retrain unmatched (T2 R7 s0.2 rep3: WR step 36.49 -> 35.03), excluded.
- Mechanism: first-access admission shift from zero-value positives (dev gain on Region7) carries over and lowers
  Region7's mean load, but held-out P100 is set by scan-like windows whose treatment flips with the labels.
- Integrity: check_frozen OK (94 files); leak check empty; nothing under 0_reproduce/harness_eval/ising_followup newer
  than the marker.
