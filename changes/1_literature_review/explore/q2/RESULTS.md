# Track B (Q2): QUBO/Ising vs classical solvers on the PeakBaleen selection problem

**Answers (held-out, matched write rate 35.599 MB/s +-1%, judged per PROTOCOL.md): Q1 = YES, Q2 = NO.**

## 0. Verdicts

Two Ising configurations went to the held-out set (both on F1 = the true min-max peak, the Q1 formulation):
**F1 + PT** (replica exchange on the LSE-smoothed peak with a QUBO budget penalty) and **F1 + EIM** (replica exchange
with a native hinge budget and an augmented-Lagrangian multiplier). Classical side, equally tuned: greedy, peak-aware
greedy, LP + round + repair, HiGHS MILP, CP-SAT, true-objective local search.

| question | criterion | F1 + PT | F1 + EIM |
|---|---|---|---|
| Q1 | simulated P100 below Baleen peak-blind OPT on >= 5/6 | **yes, 6/6** | **yes, 6/6** |
| Q1 | lower on average | **yes**: 27.06 vs 32.28 (-5.21) | **yes**: 26.95 vs 32.28 (-5.33) |
| Q2 | objective <= best classical on >= 5/6 at >= 2 of 3 budgets | **no**: 5/6 at 10 s, 2/6 at 60 s, 1/6 at 300 s | **no**: 4/6, 1/6, 1/6 |
| Q2 | strictly better on average | **no**: yes at 10 s (22.524 vs 22.569), no at 60 s (22.508 vs 22.415) and 300 s (22.503 vs 22.313); all 18 pairs 22.511 vs 22.432 | **no**: 10 s 22.553 vs 22.569; 60 s 22.502 vs 22.415; 300 s 22.463 vs 22.313; all 22.506 vs 22.432 |
| Q2 | simulated P100 <= classical's on average | **no**: 27.063 vs 26.954 | yes, by 0.003 (26.951 vs 26.954; far inside the seed spread) |
| Q2 | formulation used by the final Q1/Q3 config | yes (F1 is the Q1 configurations' formulation) | yes |
| | **answer** | **Q1 yes, Q2 no** | **Q1 yes, Q2 no** |

Why (details in sections 8 and 10):
- Q1 is a formulation effect, not a solver effect: every peak-aware selection (Ising or classical) simulates 4-7 P100
  points below Baleen's peak-blind OPT; the best classical selections simulate at 26.95 on average, i.e. the same.
- Q2: the Ising samplers are the best solvers **only at the 10 s budget** (PT: <= best classical on 5/6 instances,
  one of them a tie; strictly better on average). At 60 s CP-SAT is better on the four budget-limited instances
  (Region7 s0.3 and the three Region6 samples; PT +0.4 to +0.8%); PT wins only Region7 s0.1 (-0.04% vs HiGHS) and ties
  the floored Region7 s0.2. At 300 s CP-SAT is better everywhere except that tie (PT +0.04% on Region7 s0.1, where
  CP-SAT proves the optimum, and +1.1 to +1.5% on the budget-limited instances). The nested F1 problem has one hard level (level 1); with enough time
  an exact LP-guided search reaches better integral solutions there, while the samplers plateau (PT's mean improves by only
  0.005 from 60 s to 300 s, CP-SAT's by 0.105). Dev tuning predicted exactly this (Ising ahead at 10 s, CP-SAT ahead at 60 s).

## 1. Environment (B0)

- `explore/env`: `conda create -y -p explore/env --override-channels -c conda-forge python=3.11` inside the q2 sandbox
  (`q2/env.sh`: HOME, XDG dirs, TMPDIR, pip/conda/MPL/numba/torch caches under `explore/`, `CONDA_REGISTER_ENVS=false`,
  `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`). Not registered in `~/.conda/environments.txt`.
- pip (all succeeded, none skipped; `env/env.lock.txt`, `env/install_outcomes.tsv`): numpy 2.4.6, scipy 1.17.1,
  numba 0.67.0, highspy 1.15.1, PySCIPOpt 6.2.1, ortools 9.15.6755, optuna 5.0.0, torch 2.14.0+cpu (CPU wheel index),
  simulated-bifurcation 2.0.0, dwave-samplers 1.8.0, dimod 0.12.22, openjij 0.12.2, mindquantum 0.12.0, pandas 3.0.6.
- Known issue: `ortools` and `highspy` cannot be imported into one process (ortools bundles its own HiGHS; the second
  import fails with an undefined symbol). CP-SAT therefore runs in processes that never import highspy; its optional LP
  warm start uses scipy's bundled HiGHS (`scipy.optimize.linprog(method="highs-ds")`), which coexists with ortools.
- Baleen harness: `0_reproduce/env` (read-only use), frozen artifact `0_reproduce/baleen_code`, every Baleen process
  under `bwrap --dev-bind / / --bind q2/work/systmp /tmp --`, `python -B`.
- Machine: 24-thread AMD Ryzen 9 9900X, 123 GB, no GPU. **Every solver timing run (both families) is pinned to cores
  0-7 (`taskset -c 0-7`) with 8 threads** (HiGHS `threads=8`, CP-SAT `num_workers=8`, numba 8 threads, torch 8 threads;
  SCIP is single-threaded in the PyPI build). Timing runs are strictly sequential. Baleen sims run on cores 8-23
  (`taskset -c 8-23`, `OMP_NUM_THREADS=2`, <= 6 concurrent), trains under `flock explore/.train.lock` (shared with
  Track A).

## 2. Problem, formulations, and what is compared

Instances (harness format, built by the unmodified training driver through a Policy dump): episodes e with
d(e,w) = DT saved in 10-min window w if e is admitted, C_w = no-cache DT, s_e = chunks written, B = the harness's
chunk budget at 35.599 MB/s. Loads L_w(x) = C_w - sum_e d(e,w) x_e over the objective windows (after day 1).
Dev = `q2/inst/dev_Region{7,6}.npz` (copies of harness_eval's dumps; n = 87,828 / 61,903 episodes, 853 windows).
Held-out = `common/inst/full_Region{7,6}_s{0.1,0.2,0.3}.npz` (Track A; OPT EAs from the release CSV).

| id | objective of a set x (smaller is better) | structure | MILP needs |
|---|---|---|---|
| F1 | max_w L_w (true min-max) | linear epigraph | exact |
| F2a | mean of the top-4 L_w (CVaR_4) | linear | exact (CVaR LP) |
| F2b | (1/853) sum_w ((L_w - tau)_+)^2, tau = 0.6 x (peak of Baleen's greedy set at W) | convex quadratic (squared hinge) | tangent cuts (J = 6-24 per window) |
| F3 | capacity/eviction-coupled QKP | quadratic/bilinear | McCormick |
| F4 | Track A's learnability-regularized formulation | - | - |

All formulations use the same nested-prefix output as harness_eval (the simulator's converged OPT cutoff admits only a
prefix of the selection): K = 8 levels f = 0.65, 0.70, ..., 1.00 of B solved bottom-up with S_k forced into S_{k+1};
emitted order = S_1, then each increment in Baleen order, then the harness strict-prefix fill in Baleen order.
**Q2 objective of a run = mean over the 8 levels of the formulation objective of the prefix of the emitted order
within f_k B** (exactly the sets the simulator admits at cutoff f_k W), computed after the shared repair.
Time: one wall-clock budget T for the whole nested solve (10, 60, 300 s); level k gets
remaining x w_k / sum_{j>=k} w_j with w = (2,1,...,1) (level 1 is the only large sub-problem; unused time carries over).
The clock starts after instance load and a numba warm-up (same for every solver) and includes every repair.

F3 and F4: see section 9 (F3 not implemented; F4 was finalized by Track A at 21:50, after the F1 held-out runs had started at 18:25).

## 3. Solvers

Shared by every solver of a formulation: the level sub-problem, the **shared repair** (1: drop over-budget episodes by
smallest weighted saving per chunk, weights = the objective's window marginals -- for F1 exactly harness_eval's
argmax-window rule; 2: improving adds, most negative d(objective)/s_e first -- for F2b an exact lazy greedy; 3:
Baleen-order fill that never worsens the objective), the classical starting points, and the nested driver.

Classical family:
- `greedy`: Baleen's own prefix (peak-blind) + shared repair.
- `pgreedy`: peak-aware greedy = shared repair from the empty set.
- `lp`: formulation LP (HiGHS) [+ optional lexicographic max-DT stage], round down, shared repair.
- `milp`: HiGHS MILP (8 threads) warm-started from `lp` or `pgreedy`, remaining level time; presolve on/off,
  heuristic effort, tangent count tuned; a solution returned after its level deadline is discarded.
- `cpsat`: OR-Tools CP-SAT (8 workers), integer-scaled model (F2b squares exact via AddMultiplicationEquality),
  hint = `lp` (scipy HiGHS) or `pgreedy`.
- `scip`: PySCIPOpt (single-threaded wheel), MILP for F1/F2a, exact convex MIQCP (t_w >= u_w^2) for F2b.
- `ls`: true-objective local search, **hard budget**, the formulation's objective on the true loads (F1 acceptance on
  LSE_g(L), the harness R3 design), 8/16 independent SA chains (one numba thread each), geometric cooling over the
  level time, optional restarts from the incumbent.

Ising family (energy-based samplers; the same numba move/energy kernel as `ls`, so speed is not a confound):
- `eim`: Extended-Ising-Machine style: energy = formulation energy + native hinge budget term lam*h + rho/2*h^2
  (h = (s.x - B)_+, no slack spins), ALM update of lam, replica exchange over R replicas (parallel tempering, numba
  prange over replicas), optional annealing of the ladder; best feasible replica state kept.
- `pt`: the same replica-exchange sampler on a plain QUBO penalty rho*(s.x - B)^2 (SA/PT on a QUBO energy).
- `hlns`: LNS whose moves come from the `eim` sampler restricted to neighbourhoods of the objective-relevant windows
  (+ optional HiGHS sub-MILP branch; accepted-move shares reported).
- `sb`: matrix-free simulated bifurcation (ballistic / discrete / heated; batched agents; torch, 8 threads) on the
  formulation's QUBO surrogate sum_w alpha_w (C_w - tau - (D^T x)_w)^2 + mu s.x (F2b: exact on the active set),
  with ALM/subgradient budget price and window reweighting.
- `mq`: contested-subset QUBO LNS: explicit sub-QUBO on a neighbourhood, solved by MindQuantum bSB/dSB/CAC (sparse J +
  h), dwave-samplers SA or OpenJij SA (choice tuned), samples repaired, accepted if the true objective improves.

## 4. Tuning procedure (dev only; identical for both families)

- Optuna TPE (seed 0, 4 random start-up trials), one study per (formulation, solver, budget), stored in `q2/optuna.db`;
  every trial runs the sampled config on BOTH dev instances (two sequential processes on cores 0-7) and is logged in
  `q2/trials.csv` (phase `tune`, tag = study + trial). Trial seed = trial number. Value = mean over the two dev
  instances of objective / (peak-aware greedy objective of that instance) - 1. Failed or over-budget (> 1.05 T + 0.5 s)
  runs score +1. Trial 0 of every 10-s study is the solver's default configuration.
- **10 s stage: 10 trials per tunable solver** (greedy and pgreedy have no hyperparameters).
- **60 s stage (successive halving): the 3 best distinct 10-s configurations of every solver are re-run at 60 s**
  (3 trials per solver); the best is used at 60 s and 300 s. No tuning at 300 s for any solver.
- Search spaces (q2tune.py `space`): classical LS 9-10 parameters (start, T0, T1, moves/round, add/swap mix,
  hot-window count, restarts, chains, [LSE g]); EIM/PT 11-13 (start, replicas, Tmin, Tmax, moves/round, move mix,
  hot windows, rho, hinge scale, ladder annealing, [ALM step], [LSE g]); MILP 4-5 (start, presolve, heuristic
  effort, tie-break, [tangents]); CP-SAT 4-5; SCIP 2; LP 1-2; HLNS 11; SB 9-11; MQ 10.

## 5. Dev results (tuning; dev instances only)

Values = mean over the two dev instances of (objective / peak-aware-greedy objective - 1), in %, for the best trial of
each study (lower is better); per-instance columns in `results/dev_summary.csv` / `results/dev_summary.md`.
F1 (true min-max; 853 windows; 8 nested levels):

| solver | family | 10 s (10 trials) | 60 s (3 trials) |
|---|---|---|---|
| pt | Ising | **-15.010** | -15.167 |
| eim | Ising | -14.973 | -15.110 |
| hlns | Ising | -14.066 | -14.796 |
| mq | Ising | -13.891 | -14.036 |
| sb | Ising | -13.217 | -13.236 |
| ls | classical | -14.901 | -15.229 |
| cpsat | classical | -14.566 | **-15.530** |
| milp | classical | -14.760 | -14.798 |
| lp | classical | -13.172 | -13.149 |

F2b (squared-hinge soft peak), 10 s only (10 trials each): classical ls **-0.143**, lp -0.020, milp -0.019,
cpsat -0.010, scip 0.000; Ising pt -0.134, eim -0.104, hlns -0.059, mq -0.019, sb 0.000 (SB and SCIP never improved on
their greedy start within 10 s; HiGHS/CP-SAT need tangents / integer products for the square).

Dev reading:
- F1, 10 s: both Ising samplers lead (PT and EIM ahead of every classical solver on both dev instances).
- F1, 60 s: the order flips -- CP-SAT (exact search, LP-hinted) and LS overtake PT/EIM. Per level (60 s, Region7):
  PT sits on the 24.088 floor at all 8 levels while CP-SAT/LS miss it only at level 1; Region6: CP-SAT is better on
  every level and PT's deficit grows on the small later increments (each adds 5% of B to a forced set).
- F2b, 10 s: the classical LS leads; PT is close (-0.134 vs -0.143) and EIM behind; the exact lazy greedy is already
  within ~0.2% of everything anybody finds.
- Dev simulations (OPT mode, matched WR +-1%): F2b greedy 28.53/28.26, F2b ls 28.47/28.28, F2b pt 28.53/28.24;
  F1 10-s pt 28.96/27.65, F1 10-s ls 27.85/27.76; F1 60-s cpsat 27.85/27.91, ls 27.95/27.59, pt 27.88/27.86
  (Region7/Region6). harness_eval's Baleen peak-blind OPT on the same dev instances: 34.52/35.56. Analytically
  near-identical selections differ by up to ~1 P100 point in simulation (peak migration), without a family pattern.

## 6. Finalists (chosen on dev only, before any held-out run)

Formulation F1 (Ising ahead on dev at 10 s; F2b favoured the classical LS at 10 s and its 60 s stage was not run).
Final Ising configurations (2 of the allowed 3):
1. **F1 + PT** (replica exchange on LSE_g(L) + QUBO budget penalty; 16 replicas, LP start; 10 s config = best of
   10 trials, 60/300 s config = best of the 60 s stage).
2. **F1 + EIM** (replica exchange on LSE_g(L) + native hinge budget + ALM; 16 replicas, LP start).
Classical side on held-out: greedy, pgreedy, lp, milp (deterministic, 1 run per budget), cpsat and ls (3 seeds),
each with its own tuned configuration per budget (same procedure). SCIP omitted for F1 (linear; the protocol requires
SCIP for quadratic formulations; HiGHS and CP-SAT cover the MIP side). Plan: `q2/plan_F1.json`.

## 7. Held-out evaluation protocol (as run)

- Instances: `common/inst/full_Region{7,6}_s{0.1,0.2,0.3}.npz` (Track A; offline full-trace instances at the OPT EA
  of each sample from the release CSV; 57.5k-88.5k episodes, 852-853 objective windows). Never used before this phase.
- Runs: `q2heldout.py --plan plan_F1.json`: for every instance, the 300 s block, then 60 s, then 10 s; inside a block
  the (method, seed) runs in a fixed pseudo-random order; strictly sequential on cores 0-7, 8 threads each. 288 runs:
  greedy, pgreedy, lp, milp (1 run per budget; deterministic), cpsat, ls, pt, eim (seeds 0, 1, 2). Every run is in
  `trials.csv` (phase `heldout`) with its solution file in `sols/`.
- Q2 unit: per (instance, budget), the Ising configuration's mean objective over its 3 seeds vs the best classical
  method's mean (lowest mean among greedy, pgreedy, lp, milp, cpsat, ls). Objective criterion: Ising <= best classical
  on >= 5/6 instances at >= 2 of 3 budgets. Average criterion: Ising mean < classical mean (reported per budget and
  over all 18 instance-budget pairs). Simulation criterion: mean over instances of the simulated P100 of the Ising
  300 s selections (3 seeds) <= that of the per-instance best classical method's 300 s selections (all its seeds).
- Simulation (Q1 and the Q2 clause): `q2simloop.py` replays each 300 s selection through `PolicyQ2` (replay mode,
  identity-mapped, instance consistency and prefix rule asserted) inside the unmodified `train.main()`
  (authors' OPT-AP train args, OPT EA of the sample, no GBMs, split end 1e9), then `simulate_ap --offline-ap --ap opt`
  (authors' "OPT-Range on OPT-Ep-Start" sim args + `--eviction-policy LRU`) with `--ap-threshold` converged to
  35.599 MB/s +-1% (converge.py rules). Unmatched results are excluded and reported.
- Q1 comparator: Baleen's peak-blind OPT. (a) `R0` = Baleen's own order through the identical q2 pipeline
  (`q2r0.py`, same train/sim args, only the order differs); (b) Track A's `common/baselines.csv` when its
  `BASELINES_READY` flag exists.

## 8. Held-out results

All 288 runs finished with status ok (none failed); walls <= 300.06 s at 300 s, <= 60.07 s at 60 s; one run over the
1.05 T + 0.5 s limit: HiGHS MILP on Region7 s0.3 at 10 s (11.03 s; objective 22.616, not the best classical there, so
no verdict depends on it; kept as is). Objective = mean over the 8 nested levels of the peak (util %) of the prefix sets.

### 8.1 Mean objective per method over the 6 held-out instances (lower is better)

| method | family | 10 s | 60 s | 300 s |
|---|---|---|---|---|
| pt (3 seeds) | Ising | **22.524** | 22.508 | 22.503 |
| eim (3 seeds) | Ising | 22.553 | 22.502 | 22.463 |
| ls (3 seeds) | classical | 22.569 | 22.462 | 22.434 |
| cpsat (3 seeds) | classical | 22.689 | **22.418** | **22.313** |
| milp (1 run) | classical | 22.958 | 23.582 | 22.763 |
| lp (1 run) | classical | 23.039 | 23.039 | 23.001 |
| pgreedy | classical | 26.693 | 26.693 | 26.693 |
| greedy (Baleen order + repair) | classical | 31.816 | 31.816 | 31.816 |

(The "best classical" of the Q2 comparison is chosen per instance and budget, so its averages, 22.569 / 22.415 /
22.313, are <= every single classical row.) HiGHS MILP note: with 8 threads HiGHS still overshoots its time limit
occasionally (presolve off); the guard discarded 5 of its 144 held-out level solutions that came back after the
level deadline (3 at 60 s on the Region6 samples, 1 at 300 s on Region7 s0.1 level 1, 1 at 10 s), so those levels
fell back to their greedy/LP start. This is why its 60 s mean (23.58) is worse than its 10 s mean. HiGHS was never the
best classical method in those cells, so no verdict depends on it; CP-SAT never overran.

### 8.2 Q2, F1 + PT vs the best classical method per instance and budget (mean +- sd over seeds; gap = Ising/classical - 1)

| instance | budget | PT | best classical | classical | gap % | PT <= ? |
|---|---|---|---|---|---|---|
| Region6_s0.1 | 10 | 20.6606 +- 0.0111 | ls | 20.6732 +- 0.0071 | -0.061 | yes |
| Region6_s0.2 | 10 | 22.3456 +- 0.0035 | ls | 22.3536 +- 0.0118 | -0.036 | yes |
| Region6_s0.3 | 10 | 21.5559 +- 0.0085 | ls | 21.5503 +- 0.0102 | +0.026 | no |
| Region7_s0.1 | 10 | 23.1407 +- 0.0014 | ls | 23.2084 +- 0.0081 | -0.292 | yes |
| Region7_s0.2 | 10 | 25.4120 +- 0 | cpsat | 25.4120 +- 0 | 0 | tie |
| Region7_s0.3 | 10 | 22.0264 +- 0.0092 | ls | 22.2138 +- 0.0150 | -0.844 | yes |
| Region6_s0.1 | 60 | 20.6479 +- 0.0186 | cpsat | 20.4875 +- 0.0689 | +0.783 | no |
| Region6_s0.2 | 60 | 22.3118 +- 0.0169 | cpsat | 22.1599 +- 0.0326 | +0.686 | no |
| Region6_s0.3 | 60 | 21.5343 +- 0.0102 | cpsat | 21.3746 +- 0.0353 | +0.747 | no |
| Region7_s0.1 | 60 | 23.1360 +- 0.0059 | milp | 23.1448 (1 run) | -0.038 | yes |
| Region7_s0.2 | 60 | 25.4120 +- 0 | milp | 25.4120 (1 run) | 0 | tie |
| Region7_s0.3 | 60 | 22.0047 +- 0.0036 | cpsat | 21.9110 +- 0.0152 | +0.428 | no |
| Region6_s0.1 | 300 | 20.6255 +- 0.0207 | cpsat | 20.3847 +- 0.0274 | +1.181 | no |
| Region6_s0.2 | 300 | 22.3202 +- 0.0069 | cpsat | 21.9801 +- 0.0075 | +1.547 | no |
| Region6_s0.3 | 300 | 21.5244 +- 0.0136 | cpsat | 21.2057 +- 0.0085 | +1.503 | no |
| Region7_s0.1 | 300 | 23.1260 +- 0.0080 | cpsat | 23.1166 +- 0 (optimal) | +0.040 | no |
| Region7_s0.2 | 300 | 25.4120 +- 0 | milp | 25.4120 (1 run) | 0 | tie |
| Region7_s0.3 | 300 | 22.0091 +- 0.0065 | cpsat | 21.7771 +- 0.0200 | +1.065 | no |

Per budget: 10 s 5/6 (1 tie), mean 22.524 vs 22.569 (strictly better); 60 s 2/6 (1 tie), 22.508 vs 22.415;
300 s 1/6 (tie), 22.503 vs 22.313. Objective criterion met at 1 budget (needs 2): **fail**. Average over all 18
instance-budget pairs 22.511 vs 22.432: **fail**.

F1 + EIM (full table in `results/q2_final.md`, `results/heldout_F1_eim_objective.csv`): <= best classical on 4/6
at 10 s (better on Region6 s0.1, Region7 s0.1, s0.3; tie on Region7 s0.2; worse on Region6 s0.2, s0.3), 1/6 (the tie)
at 60 s and 300 s; means 22.553 / 22.502 / 22.463 vs 22.569 / 22.415 / 22.313. **Fail** on both criteria.

Ties: Region7 s0.2 is floored at 25.412 on every level; cpsat, ls, pt, eim reach it at every budget (MILP at 60/300 s).
Objectives within 1e-9 relative are treated as ties (they count as "<=" and never as "strictly better").

Accepted-move shares (hybrid attribution, all held-out runs): the replica-exchange sampler made 99.40% (PT, 10 s) to
99.9994% (EIM, 300 s) of all accepted moves; the rest are shared-repair operations after the LP-rounding start
(start 196k-224k, final repair < 1k per 18 runs). Relative to that classical start (LP + round + repair, `lp` row:
23.04), the samplers contribute the whole improvement to 22.50-22.55.

### 8.3 Q1 and the Q2 simulation clause (300 s selections; OPT mode; all 52 simulations matched, WR 35.26-35.95)

| instance | PT P100 (3 seeds) | EIM P100 (3 seeds) | best classical at 300 s: P100 | Baleen peak-blind OPT (Track A = our R0) | PT - OPT |
|---|---|---|---|---|---|
| Region7_s0.1 | 27.61 +- 0.16 | 27.34 +- 0.22 | cpsat 27.38 (3) | 33.68 | -6.07 |
| Region7_s0.2 | 27.90 +- 0.54 | 28.02 +- 0.18 | milp 28.21 (1) | 35.28 | -7.38 |
| Region7_s0.3 | 26.76 +- 0.21 | 26.49 +- 0.31 | cpsat 26.64 (3) | 31.23 | -4.47 |
| Region6_s0.1 | 26.41 +- 0.20 | 25.94 +- 0.39 | cpsat 26.11 (3) | 30.90 | -4.49 |
| Region6_s0.2 | 26.38 +- 0.11 | 26.54 +- 0.24 | cpsat 26.23 (3) | 30.62 | -4.23 |
| Region6_s0.3 | 27.32 +- 0.17 | 27.38 +- 0.08 | cpsat 27.15 (3) | 31.96 | -4.64 |
| **mean** | **27.063** | **26.951** | **26.954** | **32.277** | **-5.21** (EIM -5.33) |

- Q1: both Ising configurations are below Baleen's peak-blind OPT on 6/6 instances and by 5.2-5.3 points on average
  -> **Q1 = yes**. The comparator is Track A's `common/baselines.csv` OPT row (1 run each, converged); our own R0
  through the identical q2 pipeline reproduces it exactly on all six (33.676, 35.277, 31.228, 30.901, 30.616, 31.964).
  The classical selections are just as far below OPT (26.95), so the Q1 gain is a formulation effect.
- Q2 simulation clause: PT 27.063 > 26.954 (**fail**); EIM 26.951 <= 26.954 (pass by 0.003 P100, well inside the
  seed-to-seed spread of 0.1-0.5). Selections with near-identical analytic objectives differ by up to ~1 P100 in
  simulation (peak migration), without a family pattern (dev showed the same).

## 9. F3 and F4 (not run on held-out) -- why

- **F3 (capacity / eviction-age-coupled QKP)** was not implemented. Reasons, in order: (i) the protocol requires Q2 on
  a formulation used by the final Q1 or Q3 configuration, and dev evidence pointed to F1/F2; (ii) harness_eval's own
  capacity-coupled arms (C3L/C3 at kappa = 1.5) simulated WORSE than the plain peak arms (P100 28.9-29.6 vs 27.6-28.3),
  so F3 was the least likely Q1 formulation; (iii) the timing cores are exclusive and a Q2 campaign on one formulation
  already takes ~8 h (288 runs). An eviction-coupled F3 would be the natural place for an Ising edge (bilinear
  savings x occupancy terms that MILP must McCormick-linearise), but a true-objective classical local search evaluates
  such terms just as cheaply as an Ising sampler (same O(row) incremental update), so the family question would again
  reduce to replica exchange / soft constraints vs hard-constraint SA -- the comparison F1/F2b already make.
- **F4 (Track A's day-1 energy, `common/Q3_FORMULATION.md`)** appeared at ~17:30 as a DRAFT and was finalized at
  21:50 (finalists P0 = pure day-1 soft peak LSE_2 under the hard budget; T2 = + DT blend + trust region), i.e. after
  the F1 held-out campaign had started (18:25) on the exclusive cores 0-7. A second held-out Q2 campaign (6 day-1
  instances x 3 budgets x every method x 3 seeds, ~6-8 h) did not fit within the ~16 h cap. Q2 is therefore shown on
  F1, the formulation of the Q1 configurations (which satisfies the protocol's "which formulation" rule); nothing is
  claimed about F4. Track A's own note is relevant: their deployed gain comes mostly from zero-value episodes that the
  stochastic PT leaves selected, so an energy-level Q2 comparison on F4 would measure something different from Q3.

## 10. Why the Ising samplers win at 10 s and lose at 60/300 s (mechanism)

- **The nested F1 problem has one hard level.** Level 1 (65% of B, nothing forced) carries almost all of the
  difference between methods; levels 2-8 add 5% of B each on top of a forced set and are small. Several instances are
  floored (a window whose load cannot be shaved further, `results/floors.txt`): dev Region7 (24.088), held-out
  Region7 s0.1 (23.117, reached on levels 2-8 by every good method) and Region7 s0.2 (25.412, reached on EVERY level by
  cpsat, ls, pt, eim at every budget -> exact ties).
- **Short budgets favour the samplers.** Level 1 gets 2/9 of T (2.2 s at 10 s). The replica-exchange samplers start
  from the LP rounding and descend to near-optimal loads within ~1-2 s; CP-SAT and HiGHS spend most of that slice on
  the LP start, model build and root processing (and HiGHS's presolve cannot be interrupted), so they return early with
  weaker incumbents.
- **Longer budgets favour exact search.** With 13 s (60 s budget) or 67 s (300 s) for level 1, CP-SAT's LP-guided
  search proves level-1 optimality on the floored instances (Region7 s0.1 in ~20 s) and finds better integral points
  on the budget-limited ones (Region7 s0.3, Region6), where the samplers plateau (60 s -> 300 s gains per instance:
  PT -0.01 to +0.02 util-points, EIM 0.00-0.07, CP-SAT 0.05-0.18).
- **Driver caveat.** Exact solvers finish the small later levels early and the pre-registered nested split only lets
  unused time flow forward, so on the held-out set CP-SAT used 4-10 s of the 10 s budget and 4-59 s of the 60 s budget
  (HiGHS 2-11 s and 11-60 s; the short walls are the floored/easy instances). The post-hoc dev check in section 11
  shows that giving level 1 more time does not change the ordering at either budget.

## 11. Post-hoc sensitivity to the nested time split (dev only; NOT part of any verdict)

Question: are the 10 s Ising win and the 60 s CP-SAT win artifacts of the pre-registered level-time split
(w = 2,1,...,1)? Dev instances, the held-out configurations of PT and CP-SAT, seeds 0-2, run sequentially on cores 0-7
after the held-out phase (`trials.csv` phases `sens_default` and `sens_w6`; 48 runs, all ok, none over budget).
Mean objective over the two dev instances (3 seeds each):

| split | budget | PT | CP-SAT | better |
|---|---|---|---|---|
| default w1 = 2 | 10 s | **23.183** | 23.321 | PT |
| default w1 = 2 | 60 s | 23.160 | **23.080** | CP-SAT |
| level-1 weight w1 = 6 (46% of T) | 10 s | **23.174** | 23.355 | PT |
| level-1 weight w1 = 6 | 60 s | 23.163 | **23.048** | CP-SAT (now also on the Region7 floor, 24.0875) |

The ordering does not depend on the split: more level-1 time helps CP-SAT a little at 60 s (23.080 -> 23.048), hurts
it at 10 s (23.321 -> 23.355), and leaves PT unchanged (+-0.01). CP-SAT still returns before its budget (mean wall
7.8-8.8 s at 10 s, ~37 s at 60 s) because it proves the small later levels quickly. The held-out verdict is therefore
not an artifact of the time allocation.

## 12. Integrity

- Scope: only the offline selection Policy (`q2/src/q2policy.py`, a copy of harness_eval's with a replay mode) and the
  solvers behind it were added; the unmodified `train.main()` is called through `q2/src/q2launch_train.py`. Nothing
  under `0_reproduce/`, `harness_eval/`, `ising_followup/` was modified (harness code was COPIED to
  `q2/src/orig_harness/`). No git commits.
- `bash 0_reproduce/check_frozen.sh`: **`frozen OK (94 files)`** (run at 18:58 and again at the end, 01:55).
- Leak check (prescribed command, marker `q2/.leak_marker` touched at 15:55 before any install), run at 01:55:
  `find /home/sxing /tmp -xdev -newer X/q2/.leak_marker -type f 2>/dev/null | grep -v "^X/" | grep -vE "<prescribed
  exclusions>"` -> **empty output** (also empty at 20:30 and right after the B0 install). No file under
  `harness_eval/`, `ising_followup/` or `0_reproduce/` is newer than the marker; `~/.conda/environments.txt` is
  unchanged (2026-09-26), i.e. the env was not registered.
- Sandbox: every Baleen process ran under `bwrap --dev-bind / / --bind q2/work/systmp /tmp --` with `python -B`;
  every train (74 in total: 68 replay trains, each logging "prefix rule reproduces |S| exactly" and the instance-consistency
  check, plus 6 R0 Baleen-order trains) under `flock explore/.train.lock` shared with Track A; sims pinned to
  cores 8-23, `OMP_NUM_THREADS=2`, <= 6 concurrent (own flock slot pool).
- Timing cleanliness: all timing runs sequential on cores 0-7. `src/core_audit.py` sampled per-thread CPU every 10 s
  during the held-out phase (18:31-01:31): other processes used 94.5 CPU-s on cores 0-7 in total (0.05% of the 8-core
  capacity; 90.8 s the user's VS Code Pylance server, not touched), max one core for one 10-s interval.
- Incident (16:53, dev tuning): a chained launcher's pgrep pattern containing '{' failed (regex error read as "not
  running") and started F1 tuning concurrently with the F2b tuner on cores 0-7 for ~25 s. Killed within 30 s; the 8
  overlapping trials.csv rows are kept and flagged `contaminated_overlap`; the affected F2b `lp` study was deleted and
  re-run cleanly; the F1 study was deleted and started again later (after the F2b tuner, PID-based chaining).
- Equal tuning: every tunable solver got 10 trials at 10 s and 3 at 60 s per formulation (F2b: 10 s only); all
  trials are in `trials.csv` (phase `tune`, 455 ok + 8 flagged) and `optuna.db`.
- No cherry-picking: all 288 held-out runs and all 52 held-out simulations are reported (means over all seeds);
  the finalists were fixed on dev before the first held-out run.
- Pre-registration: the simulation plan (300 s selections, all seeds, per-instance best classical) and the nested
  time split / level grid were fixed before any held-out run (PROGRESS.md 17:00 and B1 notes).

## 13. Files (all under `explore/q2/`)

| path | content |
|---|---|
| `RESULTS.md`, `PROGRESS.md` | this report; milestone log |
| `trials.csv` | every trial (tune, heldout, devconfirm/sensitivity, flagged rows), one row per run |
| `optuna.db` | all tuning studies |
| `plan_F1.json` | held-out plan (configs per budget and their provenance) |
| `results/q2_final.md`, `results/heldout_F1_{pt,eim}_{objective,sims}.csv` | held-out Q2 / Q1 tables |
| `results/sims.jsonl` | every simulation (dev and held-out, incl. R0), with all thresholds tried |
| `results/dev_summary.{csv,md}`, `results/floors.txt` | dev tuning summary; per-instance F1 floors |
| `sols/` | every solution (nested order by episode identity) + per-level JSON |
| `src/` | q2core, q2lp, q2cpsat, q2scip, q2anneal, q2sb, q2mq, q2hybrid, q2run, q2tune, q2plan, q2heldout, q2confirm, q2policy, q2launch_train, q2sim, q2simloop, q2r0, q2final, q2analyze, q2devsummary, q2floor, core_audit |
| `work/` | Baleen runs (train/sim outputs, logs with the full commands on the first line) |
| `logs/` | tuning, held-out, simulation, audit logs |
| `../env/` | the shared solver env (ENV_READY, env.lock.txt, install_outcomes.tsv, env.sh) |
