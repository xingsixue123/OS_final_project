# WP5 (Ising track) -- dev results at CP2: tight-budget tuning, rolling re-solve, finalists, label solver, scaling

All numbers on the **dev instances only** (Region7 / Region6, samples 0, 0.1, 0.2, 0.3; full-trace OPT-mode F1
instances = phase-1 `explore/common/inst/full_*.npz`). Nothing was run on samples 0.4-0.6 for H2'.

## 0. Summary
- **Tight-budget tuning (12 Optuna trials per solver per budget, both families, 2,304 tuning runs):** the ranking flips
  with the budget. **1 s: the classical true-objective SA (`ls`) is best** (dev-eval mean 23.03 vs PT 23.25,
  EIM 23.54; LP/MILP/CP-SAT/SB/MQ stay at their LP-rounding start, ~24.7). **3 s: the Ising replica-exchange
  samplers are best** (PT 22.73, EIM 22.77 vs LS 22.87; PT <= best classical on 7/8 dev instances, EIM 8/8).
  **10 s: a near tie** (PT 22.685, LS 22.703, EIM 22.702, CP-SAT 22.81; PT <= on 5/8, EIM 3/8).
- **Dev reading of H2' (criteria applied to the 8 dev instances, ">= 5/6" read as ">= 7/8"):** PT meets the count
  criterion at 1 of 3 budgets (3 s) and is **not** strictly better on average over the 24 instance-budget pairs
  (22.888 vs 22.864); EIM likewise (1 budget; 23.005 vs 22.864). **Dev therefore predicts that H2' will FAIL on test**,
  driven by 1 s (LS) and by the 10-s tie. The allocate-to-hard-level split (w1 = 6) changes no conclusion.
- **Finalists (pre-registered rule, 14:55 Oct 1, applied mechanically): PT and EIM** (V = -14.58% and -14.14%;
  MQ -12.50%, SB -11.64%).
- **Rolling re-solve (6-h windows, 3-h step, commit first half, cumulative write-rate cap; 49 timed window solves per
  trace):** on the small window instances (median 2.6k episodes) the **exact classical solvers win at both 1 s and 3 s**
  (CP-SAT / MILP 26.45-26.47 at 1 s and 26.42 / 26.44 at 3 s vs PT 26.87 / 26.51, EIM 26.89 / 26.54; PT <= best
  classical on 1/8 instances at each budget), i.e. the Ising 3-s edge does not carry over to the periodic
  re-labeling regime. Rolling costs 3.2-4.4 util points vs the one-shot full-trace solve, but stays far below rolling
  greedy (32.65) and rolling peak-aware greedy (30.22).
- **Label solver for WP2 (Ising family): EIM, WP5-tuned 10-s configuration, T = 10 s, F1 nested (phase-1 split)** --
  best Ising day-1 objective at 1 s and 10 s, dev simulated P100 equal to PT's within noise (27.32 vs 27.33; R0 32.97),
  phase-1 300-s held-out sims EIM 26.95 vs PT 27.06. CP-SAT 10 s (arm Dc) is slightly better on day-1 (22.26 vs 22.33).
- **Scaling (real instances, CPU):** matrix-free SB takes 0.3-1.9 ms per step (32 agents) and +12-86 MB on every
  day-1 and full-trace instance (up to 88.5k episodes / 32k QUBO variables) and 4.5-12.7 ms, +111-214 MB on real
  0.2-0.4% unions (174k-348k episodes, 62k-126k variables). The dense SB package needs 1.5-3.6 s per step and 12-22 GB
  on the full traces (~1,400-3,600x slower) and runs **out of memory on all three unions** (64 GB cap; projected need
  88-355 GB, i.e. beyond the 123-GB machine from ~70k variables). PT (sparse) runs at 5-31 M proposals/s with <= 165 MB.

## 1. Setup (as run)
- Instances (dev): `inst/full_Region{7,6}_s{0,0.1,0.2,0.3}.npz` (symlinks to phase-1 common/inst; n = 57.5k-88.5k
  episodes, 853 objective windows). Formulation F1 (min-max peak), 8 nested levels f = 0.65..1.00, phase-1 nested time
  split w = (2,1,...,1), objective = mean over the levels of the peak (util %) of the prefix sets of the emitted order,
  after the shared repair -- all phase-1 code copied unchanged (`src/q2*.py`).
- Budgets 1, 3, 10 s of wall clock for the whole nested solve (clock after load + numba warm-up, includes repairs);
  over budget = wall > 1.05 T + 0.5 s. Every timing run: `taskset -c 0-7`, 8 threads, exclusive flock on
  `.cores07.lock` (asserts affinity == 0-7; also used by the WP1 solves), so no two timing runs ever overlapped.
- Solvers. Ising: `pt` (replica exchange on LSE(L) + QUBO budget penalty), `eim` (replica exchange + native hinge
  budget + ALM), `sb` (matrix-free simulated bifurcation; ballistic / discrete / heated tuned), `mq` (MindQuantum
  bSB / dSB / CAC on contested-subset sub-QUBOs). Classical: `lp` (LP + round + repair), `milp` (HiGHS),
  `cpsat` (OR-Tools CP-SAT, LP hint), `ls` (true-objective SA, hard budget); references `greedy` (Baleen order +
  repair), `pgreedy` (peak-aware greedy). Warm start in {LP rounding, pgreedy} for every tunable solver (tuned).
- Tuning (`src/p2tune.py`): Optuna TPE (seed 0, 4 start-up trials), one study per (solver, budget), **12 trials per
  solver per budget**, trial 0 = the solver's phase-1 best 10-s configuration; each trial runs on all 8 dev instances
  (one process, sequential); value = mean of obj / pgreedy - 1; failed or over-budget instance -> +1.
- Dev evaluation (`src/p2deval.py`, pre-registered 14:55): best tuning trial per (solver, budget), fresh seeds
  101-103 (lp / greedy / pgreedy deterministic: 1 run), phase-1 split (`deval`) and the allocate-to-hard-level split
  w = (6,1,...,1) (`deval_hl`, level 1 gets 46% of T).

## 2. Tuning (best trial value = mean over 8 dev instances of obj / pgreedy - 1, %; "phase-1 cfg" = trial 0)
| solver | family | 1 s best (trial) | 1 s phase-1 cfg (t0) | 3 s best (trial) | 3 s phase-1 cfg (t0) | 10 s best (trial) | 10 s phase-1 cfg (t0) |
|---|---|---|---|---|---|---|---|
| pt | Ising | -13.009 (t9, n=12) | -8.571 | -15.282 (t9, n=12) | -14.731 | -15.343 (t9, n=12) | -15.341 |
| eim | Ising | -12.303 (t7, n=12, fail 3) | -8.496 | -15.038 (t0, n=12, fail 1) | -15.038 | -15.326 (t2, n=12) | -15.298 |
| sb | Ising | -7.690 (t0, n=12, fail 4) | -7.690 | -13.454 (t7, n=12, fail 1) | -13.342 | -13.798 (t9, n=12) | -13.395 |
| mq | Ising | -7.979 (t10, n=12, fail 1) | -7.908 | -14.749 (t11, n=12) | -13.869 | -15.039 (t11, n=12) | -14.297 |
| lp | classical | -7.798 (t5, n=12, fail 4) | -7.690 | -13.482 (t5, n=12, fail 4) | -13.375 | -13.482 (t5, n=12) | -13.375 |
| milp | classical | -7.779 (t11, n=12, fail 1) | -3.682 | -14.080 (t11, n=12, fail 3) | -11.160 | -14.570 (t6, n=12, fail 3) | -13.938 |
| cpsat | classical | -7.737 (t11, n=12, fail 2) | -7.696 | -12.674 (t4, n=12, fail 2) | -11.388 | -15.076 (t9, n=12, fail 4) | -14.968 |
| ls | classical | -14.059 (t5, n=12) | -12.908 | -14.665 (t1, n=12) | -14.632 | -15.261 (t9, n=12) | -15.215 |

"fail k" = trials in which at least one instance failed or ran over budget (scored +1). LP has only 2 configurations
(lexi on/off), so its 12 trials repeat them. At 1 s the phase-1 10-s configurations of PT/EIM are poor (-8.6 / -8.5%)
and tuning gains 4.4 / 3.8 points; LS gains 1.2. Every Ising and classical study got exactly 12 completed trials.

## 3. Dev evaluation (fresh seeds 101-103; mean over the 8 instances of the per-instance mean; in parentheses obj / pgreedy - 1)
| solver | family | 1 s | 3 s | 10 s |
|---|---|---|---|---|
| pt | Ising | 23.2509 (-13.21%) | 22.7269 (-15.19%) | 22.6854 (-15.34%) |
| eim | Ising | 23.5394 (-12.12%) | 22.7738 (-15.01%) | 22.7018 (-15.28%) |
| sb | Ising | 24.7186 (-7.65%) | 23.1923 (-13.44%) | 23.0935 (-13.82%) |
| mq | Ising | 24.6605 (-7.87%) | 22.8729 (-14.64%) | 22.7814 (-14.98%) |
| lp | classical | 24.7337 (-7.60%) | 23.2332 (-13.29%) | 23.2332 (-13.29%) |
| milp | classical | 24.7084 (-7.69%) | 23.0449 (-13.99%) | 22.9193 (-14.47%) |
| cpsat | classical | 24.6964 (-7.73%) | 23.5984 (-11.86%) | 22.8144 (-14.86%) |
| ls | classical | 23.0308 (-14.04%) | 22.8714 (-14.65%) | 22.7033 (-15.28%) |
| greedy | reference | 32.0870 (+19.82%) | 32.0870 (+19.82%) | 32.0870 (+19.82%) |
| pgreedy | reference | 26.7782 (+0.00%) | 26.7782 (+0.00%) | 26.7782 (+0.00%) |

Per instance, 1 s (mean over seeds):

| solver | R7_s0 | R7_s0.1 | R7_s0.2 | R7_s0.3 | R6_s0 | R6_s0.1 | R6_s0.2 | R6_s0.3 |
|---|---|---|---|---|---|---|---|---|
| pt | 24.240 | 23.391 | 25.412 | 22.793 | 23.188 | 21.366 | 23.207 | 22.409 |
| eim | 24.402 | 23.629 | 25.417 | 23.152 | 23.565 | 21.771 | 23.582 | 22.797 |
| sb | 24.340 | 23.608 | 25.736 | 25.160 | 25.428 | 23.736 | 25.070 | 24.671 |
| mq | 24.330 | 23.567 | 25.729 | 25.080 | 25.277 | 23.686 | 24.982 | 24.633 |
| lp | 24.308 | 23.768 | 25.728 | 25.160 | 25.428 | 23.736 | 25.070 | 24.671 |
| milp | 24.336 | 23.589 | 25.736 | 25.147 | 25.417 | 23.723 | 25.069 | 24.649 |
| cpsat | 24.381 | 23.439 | 25.777 | 25.147 | 25.373 | 23.735 | 25.053 | 24.665 |
| ls | 24.265 | 23.424 | 25.412 | 22.528 | 22.719 | 20.982 | 22.815 | 22.102 |
| greedy | 32.489 | 33.023 | 34.536 | 30.526 | 33.308 | 31.006 | 29.896 | 31.910 |
| pgreedy | 27.414 | 27.503 | 27.461 | 26.941 | 26.654 | 25.585 | 26.522 | 26.145 |

Per instance, 3 s (mean over seeds):

| solver | R7_s0 | R7_s0.1 | R7_s0.2 | R7_s0.3 | R6_s0 | R6_s0.1 | R6_s0.2 | R6_s0.3 |
|---|---|---|---|---|---|---|---|---|
| pt | 24.137 | 23.177 | 25.446 | 22.055 | 22.327 | 20.693 | 22.392 | 21.589 |
| eim | 24.134 | 23.214 | 25.412 | 22.182 | 22.430 | 20.720 | 22.481 | 21.618 |
| sb | 24.326 | 23.584 | 25.736 | 22.672 | 22.956 | 21.169 | 22.968 | 22.127 |
| mq | 24.246 | 23.275 | 25.416 | 22.270 | 22.562 | 20.869 | 22.606 | 21.739 |
| lp | 24.308 | 23.768 | 25.728 | 22.682 | 23.065 | 21.223 | 22.961 | 22.130 |
| milp | 24.231 | 23.454 | 25.672 | 22.480 | 22.583 | 21.080 | 22.865 | 21.995 |
| cpsat | 24.255 | 23.340 | 25.412 | 22.562 | 22.864 | 22.795 | 22.924 | 24.635 |
| ls | 24.198 | 23.298 | 25.513 | 22.376 | 22.459 | 20.833 | 22.561 | 21.734 |
| greedy | 32.489 | 33.023 | 34.536 | 30.526 | 33.308 | 31.006 | 29.896 | 31.910 |
| pgreedy | 27.414 | 27.503 | 27.461 | 26.941 | 26.654 | 25.585 | 26.522 | 26.145 |

Per instance, 10 s (mean over seeds):

| solver | R7_s0 | R7_s0.1 | R7_s0.2 | R7_s0.3 | R6_s0 | R6_s0.1 | R6_s0.2 | R6_s0.3 |
|---|---|---|---|---|---|---|---|---|
| pt | 24.095 | 23.160 | 25.412 | 22.060 | 22.243 | 20.673 | 22.313 | 21.528 |
| eim | 24.132 | 23.179 | 25.412 | 22.078 | 22.245 | 20.650 | 22.376 | 21.542 |
| sb | 24.303 | 23.522 | 25.667 | 22.554 | 22.953 | 20.967 | 22.739 | 22.043 |
| mq | 24.163 | 23.216 | 25.412 | 22.155 | 22.431 | 20.748 | 22.486 | 21.641 |
| lp | 24.308 | 23.768 | 25.728 | 22.682 | 23.065 | 21.223 | 22.961 | 22.130 |
| milp | 24.194 | 23.307 | 25.672 | 22.380 | 22.400 | 20.824 | 22.705 | 21.873 |
| cpsat | 24.169 | 23.331 | 25.412 | 22.173 | 22.354 | 20.763 | 22.616 | 21.697 |
| ls | 24.122 | 23.246 | 25.412 | 22.150 | 22.237 | 20.633 | 22.323 | 21.504 |
| greedy | 32.489 | 33.023 | 34.536 | 30.526 | 33.308 | 31.006 | 29.896 | 31.910 |
| pgreedy | 27.414 | 27.503 | 27.461 | 26.941 | 26.654 | 25.585 | 26.522 | 26.145 |

H2'-style dev check (Ising mean over seeds vs the best classical method's mean per (instance, budget); classical set = lp, milp, cpsat, ls, greedy, pgreedy):

| Ising solver | 1 s: <= best classical | 1 s mean Ising vs classical | 3 s: <= best classical | 3 s mean Ising vs classical | 10 s: <= best classical | 10 s mean Ising vs classical | all pairs mean | budgets with >= 7/8 (<=) |
|---|---|---|---|---|---|---|---|---|
| pt | 3/8 (strict 2) | 23.2509 vs 23.0308 | 7/8 (strict 7) | 22.7269 vs 22.8588 | 5/8 (strict 4) | 22.6854 vs 22.7033 | 22.8877 vs 22.8643 | 1 |
| eim | 0/8 (strict 0) | 23.5394 vs 23.0308 | 8/8 (strict 7) | 22.7738 vs 22.8588 | 3/8 (strict 2) | 22.7018 vs 22.7033 | 23.0050 vs 22.8643 | 1 |
| sb | 0/8 (strict 0) | 24.7186 vs 23.0308 | 0/8 (strict 0) | 23.1923 vs 22.8588 | 0/8 (strict 0) | 23.0935 vs 22.7033 | 23.6681 vs 22.8643 | 0 |
| mq | 0/8 (strict 0) | 24.6605 vs 23.0308 | 2/8 (strict 2) | 22.8729 vs 22.8588 | 2/8 (strict 1) | 22.7814 vs 22.7033 | 23.4383 vs 22.8643 | 0 |

Per-cell details (gap, best classical per cell): `results/h2dev_deval_{pt,eim,sb,mq}.csv`. At 1 s PT is better than
LS on Region7 s0 and s0.1, ties the floored Region7 s0.2, and loses on Region7 s0.3 (+1.2%) and on all four Region6
instances (+1.4 to +2.1%); at 3 s PT beats the best classical (LS) by 0.25-1.43% on 7/8 (it loses only the floored
Region7 s0.2, by 0.13%); at 10 s all gaps are within +-0.41% (PT better on Region7 s0, s0.1, s0.3, tie on s0.2, worse
on Region6 s0, s0.1, s0.3 by 0.03-0.19%).

Mechanism (per-level objectives, mean over 8 instances x 3 seeds; level 1 = 65% of B with 2/9 of T):

| budget | metric | PT | EIM | LS | CP-SAT | MILP | MQ | SB |
|---|---|---|---|---|---|---|---|---|
| 1 s | level-1 peak | 23.97 | 24.23 | **23.84** | 29.53 | 29.62 | 29.61 | 29.62 |
| 1 s | peak at f = 1.0 | 22.91 | 23.25 | **22.48** | 23.21 | 23.26 | 23.10 | 23.31 |
| 3 s | level-1 peak | **23.22** | 23.83 | 23.71 | 25.94 | 23.74 | 23.73 | 24.11 |
| 3 s | peak at f = 1.0 | 22.37 | 22.33 | **22.32** | 22.75 | 22.60 | 22.38 | 22.76 |
| 10 s | level-1 peak | **23.09** | 23.32 | 23.38 | 23.49 | 23.60 | 23.44 | 23.82 |
| 10 s | peak at f = 1.0 | 22.32 | 22.31 | **22.27** | 22.38 | 22.50 | 22.33 | 22.64 |

At 1 s (level 1 gets ~0.2-0.3 s) MILP, CP-SAT, SB and MQ cannot improve on their LP-rounding start at level 1 (29.5 =
the rounded LP), and only the two move-based samplers do; LS (hard budget: every move feasible) beats PT (QUBO penalty:
part of a very short budget is spent in infeasible states) on every level. From 3 s on, PT's replica exchange finds the
best level-1 sets (the one hard level), which dominates the nested mean; LS stays best on the full-budget level. The
exact solvers return early on the later levels (CP-SAT mean wall 7.4 s of 10 s; MILP 7.4 s) because the phase-1 split
only carries unused time forward -- the hl split (section 4) tests whether that matters.

## 4. Allocate-to-hard-level split (w1 = 6; same configurations and seeds)
| solver | family | 1 s | 3 s | 10 s |
|---|---|---|---|---|
| pt | Ising | 23.2364 (-13.26%) | 22.7425 (-15.13%) | 22.6876 (-15.34%) |
| eim | Ising | 23.6230 (-11.80%) | 22.7401 (-15.14%) | 22.6931 (-15.32%) |
| sb | Ising | 24.3067 (-9.22%) [over 3] | 23.2058 (-13.39%) | 23.0704 (-13.90%) |
| mq | Ising | 24.3418 (-9.08%) | 22.8619 (-14.68%) | 22.7776 (-15.00%) |
| lp | classical | 24.4239 (-8.75%) | 23.2332 (-13.29%) | 23.2332 (-13.29%) |
| milp | classical | 24.3617 (-9.01%) | 23.0844 (-13.84%) | 22.9493 (-14.36%) |
| cpsat | classical | 24.6834 (-7.78%) | 23.0521 (-13.96%) | 22.8206 (-14.84%) |
| ls | classical | 22.9921 (-14.19%) | 22.8021 (-14.91%) | 22.6827 (-15.36%) |
| greedy | reference | 32.0870 (+19.82%) | 32.0870 (+19.82%) | 32.0870 (+19.82%) |
| pgreedy | reference | 26.7782 (+0.00%) | 26.7782 (+0.00%) | 26.7782 (+0.00%) |

| Ising solver | 1 s: <= best classical | 1 s mean Ising vs classical | 3 s: <= best classical | 3 s mean Ising vs classical | 10 s: <= best classical | 10 s mean Ising vs classical | all pairs mean | budgets with >= 7/8 (<=) |
|---|---|---|---|---|---|---|---|---|
| pt | 2/8 (strict 1) | 23.2364 vs 22.9921 | 7/8 (strict 6) | 22.7425 vs 22.8021 | 4/8 (strict 3) | 22.6876 vs 22.6827 | 22.8888 vs 22.8256 | 1 |
| eim | 1/8 (strict 0) | 23.6230 vs 22.9921 | 8/8 (strict 7) | 22.7401 vs 22.8021 | 4/8 (strict 3) | 22.6931 vs 22.6827 | 23.0187 vs 22.8256 | 1 |
| sb | 0/8 (strict 0) | inf vs 22.9921 | 0/8 (strict 0) | 23.2058 vs 22.8021 | 0/8 (strict 0) | 23.0704 vs 22.6827 | inf vs 22.8256 | 0 |
| mq | 0/8 (strict 0) | 24.3418 vs 22.9921 | 4/8 (strict 3) | 22.8619 vs 22.8021 | 3/8 (strict 2) | 22.7776 vs 22.6827 | 23.3271 vs 22.8256 | 0 |

Conclusions unchanged at every budget: LS best at 1 s (22.99 vs PT 23.24), PT/EIM best at 3 s (7/8 and 8/8 <= best
classical), near tie at 10 s (PT 22.688 vs LS 22.683). The extra level-1 time mostly helps the exact solvers at 1-3 s
(MILP 24.71 -> 24.36 at 1 s, CP-SAT 23.60 -> 23.05 at 3 s), not enough to change the ranking. SB ran over budget on 3
runs at 1 s with this split. **Per the pre-declared rule, the hl split is therefore not part of the H2' test.**

## 5. Ising finalists (rule pre-registered in PROGRESS.md at 14:55 Oct 1, before any dev-evaluation run)
Rule: V(s) = mean over the 3 budgets x 8 dev instances x 3 seeds of (objective / pgreedy - 1) in `deval`
(phase-1 split); the two lowest V are the finalists, each with its per-budget best-trial configuration.

| Ising solver | V (all) | V 1 s | V 3 s | V 10 s | over-budget dev runs |
|---|---|---|---|---|---|
| **pt** | **-14.58%** | -13.21% | -15.19% | -15.34% | 0 |
| **eim** | **-14.14%** | -12.12% | -15.01% | -15.28% | 0 |
| mq | -12.50% | -7.87% | -14.64% | -14.98% | 0 |
| sb | -11.64% | -7.65% | -13.44% | -13.82% | 0 |

**Finalists: PT and EIM** (`results/finalists.json`; the ranking is the same if over-budget runs were scored as
failures). Their configurations and those of the classical set are in `results/plan_H2test.json` (PT: trial 9 at
every budget; EIM: trial 7 at 1 s, the phase-1 10-s configuration at 3 s and 10 s).

## 6. Label-solver recommendation for WP2 (arms C/D/D2/E need an Ising-family solver on the day-1 F1 instance)
Evidence 1 -- offline (OPT-mode) simulated P100 of full-trace selections on the 8 dev instances (matched WR 35.599
+-1%, same pipeline as WP1; WP5 rows = the dev-evaluation seed-101 selections, sims `results/sims_label.jsonl`):

| configuration | R7_s0 | R7_s0.1 | R7_s0.2 | R7_s0.3 | R6_s0 | R6_s0.1 | R6_s0.2 | R6_s0.3 | mean | reduction vs R0 | matched |
|---|---|---|---|---|---|---|---|---|---|---|---|
| eim 300 s (phase-1 held-out sims, mean of 3 seeds; s0.1-0.3 only) | - | 27.34 | 28.02 | 26.49 | - | 25.94 | 26.54 | 27.38 | 26.951 (n=6) | 16.4% | 6 |
| pt 300 s (phase-1 held-out sims, mean of 3 seeds; s0.1-0.3 only) | - | 27.61 | 27.90 | 26.76 | - | 26.41 | 26.38 | 27.32 | 27.063 (n=6) | 16.0% | 6 |
| ls 10 s (WP5 tuned, deval seed 101) | 28.28 | 26.82 | 27.89 | 26.09 | 27.51 | 26.28 | 26.57 | 27.10 | 27.067 (n=8) | 17.7% | 8 |
| cpsat 300 s (phase-1 frozen, WP1 run) | 27.85 | 27.42 | 27.98 | 26.68 | 27.76 | 26.03 | 26.15 | 27.12 | 27.123 (n=8) | 17.6% | 8 |
| pt 300 s (phase-1 frozen, WP1 run) | 28.27 | 27.53 | 27.59 | 26.53 | 27.77 | 26.18 | 26.49 | 27.14 | 27.187 (n=8) | 17.4% | 8 |
| eim 10 s (WP5 tuned, deval seed 101) | 27.85 | 27.20 | 27.88 | 26.89 | 28.13 | 26.44 | 26.83 | 27.31 | 27.316 (n=8) | 17.0% | 8 |
| pt 10 s (WP5 tuned, deval seed 101) | 28.32 | 27.99 | 28.68 | 26.37 | 27.56 | 26.51 | 26.19 | 26.98 | 27.325 (n=8) | 17.0% | 8 |
| lp 300 s (phase-1 frozen, WP1 run) | 28.14 | 27.63 | 28.41 | 26.88 | 27.97 | 26.54 | 26.62 | 26.92 | 27.386 (n=8) | 16.8% | 8 |
| ls 1 s (WP5 tuned, deval seed 101) | 28.16 | 27.45 | 27.85 | 26.69 | 28.10 | 26.84 | 26.97 | 28.31 | 27.547 (n=8) | 16.2% | 8 |
| pt 1 s (WP5 tuned, deval seed 101) | 28.28 | 27.66 | 28.17 | 26.81 | 28.66 | 26.71 | 26.56 | 28.76 | 27.703 (n=8) | 15.8% | 8 |
| R0 (Baleen peak-blind OPT) | 34.52 | 33.68 | 35.28 | 31.23 | 35.56 | 30.90 | 30.62 | 31.96 | 32.968 (n=8) | 0.0% | 8 |

Day-1 (label-size) instances, dev Region7/6 s0-0.3 (n = 8.3k-12.3k episodes):

| solver | budget | day-1 nested objective (mean of 8) | day-1 peak at f=1 | max wall s | over budget |
|---|---|---|---|---|---|
| cpsat | 1 | 23.0674 | 22.1508 | 0.92 | 0 |
| cpsat | 3 | 22.4531 | 21.9922 | 2.91 | 0 |
| cpsat | 10 | 22.2579 | 21.8159 | 9.81 | 0 |
| eim | 1 | 22.6881 | 22.0753 | 1.06 | 0 |
| eim | 3 | 22.3864 | 21.9426 | 3.02 | 0 |
| eim | 10 | 22.3257 | 21.8671 | 10.02 | 0 |
| ls | 1 | 22.6661 | 22.1227 | 1.03 | 0 |
| ls | 3 | 22.3359 | 21.7848 | 3.02 | 0 |
| ls | 10 | 22.2677 | 21.7430 | 10.01 | 0 |
| pt | 1 | 22.8104 | 22.2171 | 1.06 | 0 |
| pt | 3 | 22.4066 | 21.9498 | 3.08 | 0 |
| pt | 10 | 22.6071 | 22.1714 | 10.02 | 0 |

Evidence 2 is the day-1 table above (label-size instances `inst_day1/`, seed 101, cores 0-7): EIM reaches the best
Ising day-1 objective at 1 s (22.69 vs PT 22.81) and 10 s (22.33 vs PT 22.61; PT's 10-s configuration, tuned on the
7x larger full traces, is worse on day 1 than its 3-s one), and is within 0.07 of its 10-s value already at 3 s.

**Recommendation:** produce WP2's Ising labels with **EIM, the WP5-tuned 10-s configuration
(`plan_H2test.json` -> eim / "10"), T = 10 s per day-1 solve, F1 nested 8 levels, phase-1 split, cores 0-7**.
Reasons: (i) best Ising day-1 objective at the label budget; (ii) its full-trace selections simulate as well as PT's
(27.32 vs 27.33 on dev, both 17.0% below R0 = 32.97) and, in phase 1's 300-s held-out sims, slightly better (26.95 vs
27.06); (iii) 10 s is negligible for a once-per-retrain label solve. Caveats: all peak-aware selections simulate within
~0.4 P100 of each other (27.07-27.39 at >= 10 s; differences are inside the seed-to-seed spread, cf. WP1 section 3) --
the solver choice matters far less than the formulation; for the Dc arm ("does the Ising solver matter?") use CP-SAT
with its 10-s tuned configuration at the same 10 s (day-1 22.26, i.e. marginally better than EIM).

## 7. Rolling re-solve variant (WP5 step 2; `src/p2roll.py`, `results/rolling.csv`)
**Design (chosen before any rolling result was used):** receding horizon with **6-h windows and a 3-h step**: window k
covers the 10-min slots [s_k, s_k + 36); its variables are the episodes whose first access (= admission decision) falls
in the window, its objective is max_w L_w over the window's objective slots, with the savings of every previously
committed episode already subtracted (spill-over); only the decisions of the **first 3 h are committed**, the second
half is look-ahead re-decided by the next window (step 6 h without look-ahead was tried first in a smoke test and
rejected because a window cannot see the savings its episodes produce after its end -- 3% of episodes cross a 6-h
boundary, and the result became an artefact of incidental spill-over); the last window commits everything. Budget =
**cumulative write-rate cap**: window k may use B x end_k / duration minus everything already committed (the target
write rate holds for every prefix of time; total = B). Day-1 windows (no objective slots) commit Baleen's order,
identically for all methods. Each window is ONE single-level F1 solve under the wall-clock budget (tuned configuration
of the method at that budget, clock after the window sub-instance is built), then the shared repair. No solver state
is carried across windows (episodes are disjoint; the warm start is the committed load/budget, identical for all).
49 timed window solves per trace (median 2.6k episodes per window, p10 2.0k, max 4.0k); every stitched selection uses
>= 99.996% of B; no window ran over budget (max window wall 1.12 s at 1 s, 3.07 s at 3 s). Seed 0, 8 dev instances.
Methods: all 10 at 1 s; at 3 s PT, EIM, LS, pgreedy (chain) and MILP, CP-SAT, LP (added Oct 3, see PROGRESS.md,
because MILP/CP-SAT were the best methods at 1 s).

| solver | budget | rolling full-trace peak (mean over instances) | one-shot nested solve: peak at f=1 (same budget, seed 101) | windows over budget | max window wall (s) |
|---|---|---|---|---|---|
| milp | 1 | 26.449 (n=8) | 23.240 | 0 | 0.77 |
| cpsat | 1 | 26.468 (n=8) | 23.205 | 0 | 1.05 |
| mq | 1 | 26.587 (n=8) | 23.078 | 0 | 1.06 |
| lp | 1 | 26.735 (n=8) | 23.313 | 0 | 0.03 |
| sb | 1 | 26.735 (n=8) | 23.313 | 0 | 0.98 |
| ls | 1 | 26.863 (n=8) | 22.483 | 0 | 1.02 |
| pt | 1 | 26.865 (n=8) | 22.935 | 0 | 1.05 |
| eim | 1 | 26.890 (n=8) | 23.269 | 0 | 1.12 |
| pgreedy | 1 | 30.215 (n=8) | 24.808 | 0 | 0.00 |
| greedy | 1 | 32.650 (n=8) | 30.451 | 0 | 0.01 |
| cpsat | 3 | 26.415 (n=8) | 22.690 | 0 | 2.82 |
| milp | 3 | 26.442 (n=8) | 22.656 | 0 | 2.48 |
| pt | 3 | 26.505 (n=8) | 22.362 | 0 | 3.07 |
| eim | 3 | 26.537 (n=8) | 22.321 | 0 | 3.02 |
| ls | 3 | 26.542 (n=8) | 22.309 | 0 | 3.01 |
| lp | 3 | 26.735 (n=8) | 22.750 | 0 | 0.03 |
| pgreedy | 3 | 30.215 (n=8) | 24.808 | 0 | 0.00 |

Per instance (full-trace peak of the stitched selection, util %):

| budget | solver | R7_s0 | R7_s0.1 | R7_s0.2 | R7_s0.3 | R6_s0 | R6_s0.1 | R6_s0.2 | R6_s0.3 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | cpsat | 27.810 | 27.058 | 27.237 | 26.073 | 26.648 | 25.001 | 25.744 | 26.170 |
| 1 | eim | 28.377 | 27.620 | 27.836 | 26.891 | 26.817 | 25.096 | 26.043 | 26.438 |
| 1 | greedy | 34.543 | 33.921 | 34.771 | 32.830 | 33.310 | 30.752 | 29.775 | 31.302 |
| 1 | lp | 28.104 | 27.135 | 28.182 | 26.157 | 26.856 | 25.157 | 25.959 | 26.331 |
| 1 | ls | 28.913 | 27.337 | 27.588 | 26.271 | 26.785 | 25.393 | 26.037 | 26.582 |
| 1 | milp | 27.866 | 26.931 | 27.121 | 26.083 | 26.642 | 25.008 | 25.750 | 26.190 |
| 1 | mq | 28.104 | 27.135 | 28.182 | 26.157 | 26.861 | 24.006 | 25.919 | 26.331 |
| 1 | pgreedy | 31.535 | 33.979 | 29.803 | 30.308 | 29.138 | 28.115 | 28.370 | 30.468 |
| 1 | pt | 29.185 | 27.572 | 27.988 | 26.593 | 26.898 | 24.046 | 26.071 | 26.571 |
| 1 | sb | 28.104 | 27.135 | 28.182 | 26.157 | 26.856 | 25.157 | 25.959 | 26.331 |
| 3 | cpsat | 27.741 | 27.045 | 27.139 | 25.959 | 26.641 | 24.987 | 25.691 | 26.120 |
| 3 | eim | 27.973 | 27.103 | 27.489 | 26.147 | 26.648 | 24.868 | 25.840 | 26.224 |
| 3 | lp | 28.104 | 27.135 | 28.182 | 26.157 | 26.856 | 25.157 | 25.959 | 26.331 |
| 3 | ls | 27.976 | 27.422 | 27.568 | 26.466 | 26.740 | 23.990 | 25.873 | 26.302 |
| 3 | milp | 27.834 | 26.988 | 27.198 | 26.032 | 26.616 | 24.969 | 25.763 | 26.137 |
| 3 | pgreedy | 31.535 | 33.979 | 29.803 | 30.308 | 29.138 | 28.115 | 28.370 | 30.468 |
| 3 | pt | 27.913 | 26.988 | 27.394 | 26.083 | 26.678 | 25.008 | 25.763 | 26.214 |

Ising vs the best classical method per (instance, budget) on the stitched full-trace peak:

| Ising | budget | <= best classical | mean Ising | mean best classical | best classical per instance |
|---|---|---|---|---|---|
| PT | 1 s | 1/8 | 26.865 | 26.436 | CP-SAT 5, MILP 3 |
| EIM | 1 s | 0/8 | 26.890 | 26.436 | |
| MQ | 1 s | 1/8 | 26.587 | 26.436 | |
| SB | 1 s | 0/8 | 26.735 | 26.436 | |
| PT | 3 s | 1/8 | 26.505 | 26.281 | CP-SAT 5, MILP 2, LS 1 |
| EIM | 3 s | 0/8 | 26.537 | 26.281 | |

Findings:
1. **Rolling reverses the 3-s full-trace result.** On 6-h window instances (~2.6k episodes, 36 slots) the exact solvers
   finish (or nearly prove) each window within 1 s, and CP-SAT / MILP give the best stitched peaks at both budgets
   (26.42-26.47); PT/EIM/LS are 0.1-0.5 points worse. The Ising samplers' 3-s edge exists only on the large one-shot
   full-trace problem, i.e. exactly not in the periodic-re-labeling regime that motivates H2'.
2. **The cost of rolling is large:** every rolling method ends 3.2-4.4 util points above its own one-shot full-trace
   solve at the same budget (e.g. CP-SAT 26.42 vs 22.69 at 3 s), because a window cannot shift write budget to later
   peaks and decides with at most 3 h of look-ahead. It still keeps most of the peak-aware benefit relative to the
   rolling peak-blind greedy (32.65) and rolling peak-aware greedy (30.22).
3. Per-window objectives (mean of the 6-h window peaks at solve time, 1 s): CP-SAT 21.13, MILP 21.14, MQ 21.29,
   EIM 21.41, LS 21.42, PT 21.46 -- the same ordering as the stitched peaks.

## 8. Scaling report (WP5 step 4; CPU only, cores 0-7, 8 threads; `src/p2scale.py`, `results/scaling.jsonl`)
Problem for every arm: the level-1 (f = 1.0) F1 QUBO surrogate the SB solver builds (sum_w alpha_w (C_w - tau -
(D^T x)_w)^2 + mu s.x over the model variables; alpha = 1 within 3% of the peak-aware-greedy peak, 0.05 elsewhere,
tau = 0.97 x that peak, mu = 0.1 mu_max), i.e. pure solver cost, no repair loop. Arms: **matrix-free SB** (q2sb kernel:
D^T y and D z as sparse CSR products, Q never formed; 32 agents x 500 steps), the **dense simulated-bifurcation
package** (v2.0.0, `minimize` on the dense float32 Q = D diag(alpha) D^T built directly in float32; 32 agents, 100
steps on day-1 parts and 50 on larger ones, early stopping off; `RLIMIT_AS` = 64 GB so an out-of-memory fails
cleanly instead of endangering Track A), and the sparse **PT** sampler (16 replicas, 5 s, proposals per second).
Instances: real day-1 parts and full traces of Regions 4-7 samples 0-0.3 (WP1 builds), plus unions of 2 or 4 disjoint
0.1% samples of the same trace (= real 0.2% / 0.4% samples; windows aligned by time) to go beyond the largest 0.1%
instance. Memory = peak RSS of the run minus the RSS after instance load (~355-410 MB of Python + data).

| instance | part | episodes n | QUBO vars | nnz(D) | matrix-free SB (32 agents) | dense SB package (32 agents) | PT (16 replicas) |
|---|---|---|---|---|---|---|---|
| R4_s0 | day1 | 5007 | 2617 | 4071 | 0.29 ms/step (0.15 s), 12 MB | 2.57 ms/step (0.26 s), 255 MB | 27.6 M/s, 6 MB |
| R4_s0.2 | day1 | 7062 | 3597 | 5545 | 0.39 ms/step (0.20 s), 15 MB | 6.56 ms/step (0.66 s), 339 MB | 31.5 M/s, 7 MB |
| R6_s0.1 | day1 | 8451 | 3962 | 8092 | 0.27 ms/step (0.14 s), 14 MB | 10.14 ms/step (1.01 s), 402 MB | 22.4 M/s, 7 MB |
| R4_s0.3 | day1 | 7053 | 3981 | 6772 | 0.34 ms/step (0.17 s), 15 MB | 8.43 ms/step (0.84 s), 405 MB | 31.2 M/s, 6 MB |
| R6_s0.3 | day1 | 8722 | 4077 | 8690 | 0.30 ms/step (0.15 s), 14 MB | 11.46 ms/step (1.15 s), 423 MB | 17.8 M/s, 7 MB |
| R6_s0 | day1 | 8843 | 4214 | 8298 | 0.38 ms/step (0.19 s), 16 MB | 11.32 ms/step (1.13 s), 449 MB | 24.1 M/s, 7 MB |
| R5_s0.2 | day1 | 10609 | 4217 | 7705 | 0.30 ms/step (0.15 s), 15 MB | 10.31 ms/step (1.03 s), 448 MB | 25.5 M/s, 8 MB |
| R5_s0 | day1 | 10796 | 4318 | 8107 | 0.36 ms/step (0.18 s), 16 MB | 12.02 ms/step (1.20 s), 467 MB | 26.2 M/s, 8 MB |
| R5_s0.3 | day1 | 11219 | 4336 | 7644 | 0.30 ms/step (0.15 s), 16 MB | 11.26 ms/step (1.13 s), 470 MB | 25.8 M/s, 9 MB |
| R6_s0.2 | day1 | 9040 | 4372 | 8467 | 0.28 ms/step (0.14 s), 14 MB | 13.33 ms/step (1.33 s), 479 MB | 23.0 M/s, 8 MB |
| R5_s0.1 | day1 | 11414 | 4526 | 7876 | 0.30 ms/step (0.15 s), 14 MB | 13.03 ms/step (1.30 s), 508 MB | 21.9 M/s, 8 MB |
| R7_s0.3 | day1 | 12434 | 5357 | 8883 | 0.36 ms/step (0.18 s), 16 MB | 23.62 ms/step (2.36 s), 693 MB | 21.6 M/s, 9 MB |
| R7_s0 | day1 | 12987 | 5412 | 8935 | 0.31 ms/step (0.15 s), 18 MB | 24.50 ms/step (2.45 s), 705 MB | 23.4 M/s, 9 MB |
| R7_s0.1 | day1 | 13008 | 5530 | 9365 | 0.33 ms/step (0.17 s), 17 MB | 24.52 ms/step (2.45 s), 733 MB | 21.2 M/s, 9 MB |
| R7_s0.2 | day1 | 13010 | 5544 | 9086 | 0.33 ms/step (0.16 s), 19 MB | 24.92 ms/step (2.49 s), 737 MB | 20.4 M/s, 9 MB |
| R4_s0 | full | 32311 | 17045 | 35755 | 0.50 ms/step (0.25 s), 51 MB | (not run) | 12.8 M/s, 18 MB |
| R5_s0.2 | full | 69504 | 23606 | 46719 | 0.62 ms/step (0.31 s), 50 MB | (not run) | 11.5 M/s, 37 MB |
| R5_s0 | full | 70408 | 23808 | 48107 | 1.05 ms/step (0.53 s), 58 MB | 1512.94 ms/step (75.65 s), 12308 MB | 9.9 M/s, 37 MB |
| R6_s0.1 | full | 57517 | 24227 | 49338 | 1.18 ms/step (0.59 s), 59 MB | (not run) | 11.7 M/s, 34 MB |
| R5_s0.1 | full | 73041 | 24928 | 47793 | 1.09 ms/step (0.54 s), 59 MB | (not run) | 11.1 M/s, 39 MB |
| R5_s0.3 | full | 73474 | 25030 | 47682 | 0.66 ms/step (0.33 s), 51 MB | (not run) | 11.4 M/s, 39 MB |
| R6_s0.3 | full | 60119 | 25053 | 52630 | 0.97 ms/step (0.49 s), 59 MB | (not run) | 11.1 M/s, 35 MB |
| R4_s0.2 | full | 49615 | 25669 | 51091 | 1.04 ms/step (0.52 s), 54 MB | (not run) | 13.4 M/s, 28 MB |
| R6_s0 | full | 61903 | 26338 | 53393 | 0.76 ms/step (0.38 s), 67 MB | 2159.45 ms/step (107.97 s), 15037 MB | 11.9 M/s, 30 MB |
| R6_s0.2 | full | 63012 | 26874 | 54148 | 1.05 ms/step (0.52 s), 62 MB | (not run) | 11.3 M/s, 34 MB |
| R7_s0.3 | full | 84790 | 30826 | 50885 | 1.31 ms/step (0.66 s), 67 MB | (not run) | 11.4 M/s, 43 MB |
| R7_s0.1 | full | 86569 | 31028 | 51734 | 1.40 ms/step (0.70 s), 86 MB | (not run) | 11.0 M/s, 46 MB |
| R4_s0.3 | full | 61662 | 31161 | 52417 | 1.55 ms/step (0.77 s), 68 MB | 3549.96 ms/step (177.50 s), 20541 MB | 17.8 M/s, 33 MB |
| R7_s0 | full | 87828 | 31487 | 53488 | 0.99 ms/step (0.49 s), 66 MB | 3551.49 ms/step (177.57 s), 21577 MB | 11.0 M/s, 46 MB |
| R7_s0.2 | full | 88507 | 32200 | 52607 | 1.86 ms/step (0.93 s), 69 MB | (not run) | 11.4 M/s, 46 MB |
| R7_s0+R7_s0.1 | union | 174397 | 62515 | 105222 | 4.53 ms/step (2.26 s), 111 MB | **OOM** at RLIMIT_AS 64 GB (RSS 53.8 GB when it failed) | 9.2 M/s, 89 MB |
| R5_s0+R5_s0.1+R5_s0.2+R5_s0.3 | union | 286427 | 97372 | 190301 | 8.23 ms/step (4.11 s), 171 MB | **OOM** at RLIMIT_AS 64 GB (RSS 23.9 GB when it failed) | 5.1 M/s, 144 MB |
| R7_s0+R7_s0.1+R7_s0.2+R7_s0.3 | union | 347694 | 125541 | 208714 | 12.71 ms/step (6.35 s), 214 MB | **OOM** at RLIMIT_AS 64 GB (RSS 39.7 GB when it failed) | 5.2 M/s, 165 MB |

- **Matrix-free SB:** 0.3-1.9 ms per step on every real day-1 and full-trace instance (up to 32k QUBO variables),
  4.5-12.7 ms on the 0.2-0.4% unions (62k-126k variables); time per step grows ~n^0.8 over this range; extra memory
  12-86 MB (<= 214 MB on the largest union).
- **Dense package:** 2.6-25 ms per step on day-1 parts (2.6k-5.5k variables) but **1.5-3.6 s per step on full traces
  (24k-31k variables; ~1,400-3,600x slower per step than matrix-free) with 12-22 GB of RSS**; time per step ~n^2.9, memory
  ~22-27 bytes per variable^2. It **fails (out of memory at the 64 GB cap) on every union**: the 0.2% Region7 union
  (62.5k variables) died at 53.8 GB RSS while allocating another 15.6 GB (extrapolated need ~88 GB); the 0.4% Region5
  (97k) and Region7 (126k) unions need ~210 GB and ~355 GB -- more than the whole 123-GB machine (their first dense
  Q allocation alone is 38 GB / 63 GB). At the project's 0.1% sampling the full traces still fit (<= 22 GB), so the
  dense package is "only" three orders of magnitude slower there; it stops being usable between 32k and 62k variables
  on this machine (and at any size above ~70k variables on 123 GB).
- **PT (sparse, numba):** 5-31 M proposals/s, extra memory 6-165 MB at every size.

## 9. Integrity, incidents, sandbox
- **Equal tuning:** every one of the 8 tunable solvers got exactly 12 completed Optuna trials per budget (288 trials,
  2,304 instance runs; `optuna.db`, `trials.csv` phase `tune`). Seed reuse artefact (symmetric): because trial 0 is the
  phase-1 best configuration and the TPE sampler is seeded as in phase 1, the phase-1 random start-up draw that had
  produced that configuration is drawn again -- LS repeats it as trial 1 and EIM as trial 2 at every budget (11 distinct
  configurations each); CP-SAT has 10-11 distinct (small discrete space) and LP only 2 (lexi on/off). PT, MILP, SB and MQ
  have 12 distinct.
- **Timing hygiene:** all timing runs (tuning, dev evaluation, hl split, day-1 label timing, rolling, scaling, and the
  WP1 solves) ran under the exclusive cores-0-7 lock with asserted affinity 0-7; none overlapped another Track-B timing
  run. Foreign load per run from `core_audit.py` (`src/audit_load.py`, `trials_audit_load.csv`): mean DIRECT load
  (foreign threads on 0-7) <= 0.03 logical CPUs per phase; SIBLING load (12-19) 0 for every dev-evaluation, hl and
  label run (Track A kept off 12-19 from 16:22 Oct 1), ~2 threads on average during tuning (Ising 2.1, classical 1.8:
  Track A before the rule, plus one unrelated user process, see below).
- **Incident 1 (Oct 1 14:44:30-14:47:40):** an unpinned ad-hoc script of mine ran on cores 0-2 during timing runs ->
  all WP5 tuning so far superseded (193 rows kept as `superseded_restart`, studies deleted, restart from trial 0 at
  15:00); WP1 Region4 s0 solves flagged `contaminated_overlap` and re-run.
- **Incident 2 (sibling exposure):** the first 1-s dev evaluation (15:18-15:58) ran with Track A on the SMT siblings
  for the Ising but not the classical runs -> all 192 rows superseded (`superseded_sibling_load`) and the 1-s dev
  evaluation re-run at 16:47-17:41 with 12-19 idle (conclusions unchanged: LS 23.03 vs PT 23.25).
- **Incident 3 (foreign processes on 0-7, not Track A/B):** editor helpers (VS Code / extension node processes) caused
  short DIRECT bursts, and an unrelated user job (`python3 <foreign process>`, Oct 1 18:33-20:34, ~1,190 CPU-s in
  total, mostly on 12-19, 1 min at ~3 cores on 0-7 at 20:33) overlapped tuning. 63 timing runs had a mean DIRECT
  foreign load > 0.2 logical CPUs (`results/flagged_foreign_direct_load.csv`: 55 tuning instance-runs -- SB 1 s
  trials 8-11 (26), LP 1 s trials 2-3 (10), SB 10 s trials 7-8 (8), EIM 3 s trial 11 (5), MILP 10 s trials 8/10 (4),
  MILP 3 s trial 1 (2) --, 6 hl-split LP runs at 1 s, 2 WP1 solves); the worst are SB 10-s trials 7/8 (0.8-2.8
  CPUs). None of them is a selected (best) trial or a dev-evaluation run of a finalist; they are kept and reported
  (an affected trial can only look worse).
- **Scaling driver failure (Oct 2 ~00:03):** the scaling driver was launched unpinned and stopped at the affinity
  assertion before any run; relaunched pinned on Oct 3 00:13 (no partial results existed).
- **Process loss:** the coordinator session ended on the evening of Oct 1; the detached `chain_rest.sh` had already
  finished everything except scaling (Oct 2 00:03). On Oct 3 only `core_audit.py` was alive; scaling and the extra 3-s
  rolling runs were (re)started from the resumable drivers; no run was lost or duplicated.
- **Sandbox:** env.sh in each area (HOME, XDG, TMPDIR, pip/conda/numba/torch caches inside the area,
  CONDA_REGISTER_ENVS=false, PYTHONNOUSERSITE=1); solver env and Baleen env used read-only (no package installed);
  every Baleen process under bwrap with a private /tmp, sims on 8-11,20-23 (<= 6 concurrent), every train under
  `flock P2/.train.lock`; no git commit.
- `bash 0_reproduce/check_frozen.sh`: **`frozen OK (94 files)`** (Oct 1 14:58, Oct 3 00:20 and Oct 3 01:12, after
  all runs).
- Leak check (prescribed command, marker `wp5_ising/.leak_marker` touched Oct 1 14:33 before anything else; run Oct 3
  01:12; full output `results/leak_check_output.txt`): **378 files, none written by a Track-B process** -- 224 under
  `<another project>` (an unrelated concurrent user project: scholar/OpenAlex matching scripts and CSVs,
  incl. the `<foreign process>` job seen by the core audit), 101 under `OS_final_project/.git/objects` (the
  coordinator's commits; Track B made none), 33 under `<home cache>` (Oct 1 18:11, the
  sentence-transformers model used by that same <another project> job), `changes/SCOPE_v2.md` (edited by the coordinator,
  Oct 1 16:20), and desktop/session files (`<home desktop/config>`, `<home desktop/config>`,
  `<tmp file>`, `<home file>`, `<home cache>`, all at login times; `<home file>`
  Oct 1 15:11 -- Track B never ran wget). Every Track-B process ran with HOME/XDG/TMPDIR/caches inside its area and
  every Baleen process inside bwrap with a private /tmp; `<home file>` is unchanged.

## 10. Files (all under `P2/wp5_ising/`)
| path | content |
|---|---|
| `RESULTS_dev.md`, `PROGRESS.md`, `PROTOCOL_v2_H2.md` | this report; milestone log (incl. the 14:55 pre-registration); proposed H2' pre-registration |
| `trials.csv`, `trials_audit_load.csv` | every timing run (tune / ref / deval / deval_hl / label_day1, incl. superseded rows) and its foreign load |
| `optuna.db`, `phase1_best_F1_b10.json` | all 24 tuning studies; the phase-1 configurations used as trial 0 |
| `results/plan_dev.json`, `results/finalists.json`, `results/plan_H2test.json` | tuned configurations; finalist rule output; proposed test plan |
| `results/{tuning,deval,deval_hl,rolling,scaling}_summary.md`, `results/h2dev_*.csv`, `results/deval*_per_instance.csv` | tables of this report |
| `results/rolling.csv`, `sols_roll/` | rolling runs (per-window peaks / walls / sizes / budgets) and stitched selections |
| `results/scaling.jsonl`, `scale_plan.json` | scaling runs |
| `results/sims_label.jsonl`, `results/label_evidence.md`, `work/` | label-evidence simulations (Baleen runs, logs) |
| `results/flagged_foreign_direct_load.csv`, `logs/core_audit*.log` | foreign-load audit |
| `src/` | p2run, p2tune, p2deval, p2roll, p2rollrun, p2scale, make_scale_plan, p2labsim, p2label, p2analyze, audit_load, core_audit, best_classical, chain scripts; phase-1 q2 modules (unchanged copies) |
