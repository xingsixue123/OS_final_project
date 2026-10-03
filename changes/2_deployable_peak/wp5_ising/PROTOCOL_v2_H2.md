# PROTOCOL_v2 -- H2' (Ising at tight re-solve budgets): proposed pre-registration

**Status: PROPOSED by Track B at CP2 (2026-10-03), for the coordinator to review and commit to git BEFORE any WP5 run
on samples 0.4-0.6.** Nothing below has been run on the test instances. Every choice was fixed from dev evidence only
(Region7 / Region6 samples 0, 0.1, 0.2, 0.3; `RESULTS_dev.md`). WP1's frozen-configuration runs on samples >= 0.4
(H1' breadth) were not used for any choice here.

## 1. Hypothesis (verbatim, PLAN.md section 2)
At budgets of 1, 3 and 10 s, on the same pinned cores with equal tuning trials, the tuned Ising solver is at least as
good as the best classical solver on >= 5/6 test instances at >= 2 of the 3 budgets, and strictly better on average.

## 2. Test instances (never used for tuning or selection)
Full-trace OPT-mode F1 instances of **Region7 and Region6, samples 0.4, 0.5, 0.6** (6 instances), built by the WP1
pipeline (unmodified `train.main()` + PolicyQ2 dump; the authors' OPT-AP eviction age of each sample from
results_release.csv.gz; filter_=prefetch; objective windows after day 1; B = the harness chunk budget at 35.599 MB/s):

| file (`P2/wp1_offline/inst/`) | sha256 |
|---|---|
| full_Region7_s0.4.npz | 42eb1113e0d50d5c52ef81117d89404bab9931af9fae55c61b44763ecbef9239 |
| full_Region7_s0.5.npz | 791b4e8296c3b3bd04b2583a8dc5c9eec31f2ea2724a76b22857350611bcb9ee |
| full_Region7_s0.6.npz | 271c98db1fe41c65558710d2572858626c35ffb596fd8608208705197d04d6b5 |
| full_Region6_s0.4.npz | 942375907df7a04fdbec509f0aa6280af258205156ab006e1e44241a594dc5ca |
| full_Region6_s0.5.npz | f39046c3e51cada0be9f24d46b50768ad8049a40c85e5e2c7f8b14cc1c940b84 |
| full_Region6_s0.6.npz | 9f6fe5a096f2e2f9de27400c23975657221c54335068171da1d9f2cbcf511ab8 |

## 3. Formulation, output, objective (identical to phase 1 and WP5 dev)
F1: minimise max_w L_w(x), L_w = C_w - sum_e d(e,w) x_e, s.x <= B. Nested-prefix output: 8 levels f = 0.65, 0.70, ...,
1.00 of B solved bottom-up (S_k forced into S_{k+1}); emitted order = S_1, increments in Baleen order, then the harness
strict-prefix fill. **Objective of a run = mean over the 8 levels of max_w L_w (util %) of the prefix of the emitted
order within f_k B**, after the shared repair (phase-1 `q2core`, copied unchanged into `wp5_ising/src`).

## 4. Budgets, timing, hardware
- T = 1, 3, 10 s wall clock for the whole nested solve. The clock starts after instance load, formulation set-up and
  the numba warm-up (identical for every method) and includes every repair. Level time split = **phase-1 split**
  w = (2,1,...,1) (level k gets remaining x w_k / sum_{j>=k} w_j; unused time carries forward).
- A run with wall > 1.05 T + 0.5 s is **over budget** and counts as failed: its (instance, budget) cell gets objective
  +inf for that method (a classical method with a failed run in a cell cannot be that cell's best classical; an Ising
  finalist with a failed run in a cell is "not <=" there). Crashes: logged; re-run once with the same seed only if the
  cause is infrastructure (both rows kept and reported).
- Runner `wp5_ising/src/p2run.py`: `taskset -c 0-7`, 8 threads (numba / torch / HiGHS / CP-SAT workers), exclusive
  flock on `wp5_ising/.cores07.lock` (the runner refuses to start unless its affinity is exactly 0-7), strictly
  sequential. **Logical CPUs 12-19 (the SMT siblings of 0-7 on this Ryzen 9 9900X) must be idle during the test**
  (Track A pinned to 8-11,20-23; `P2/TIMING_IDLE` deleted >= 10 min before the first test run). `core_audit.py` logs
  foreign threads on 0-7 (DIRECT) and 12-19 (SIBLING); the per-run foreign load (`src/audit_load.py`) is reported
  for every test run; a run with mean DIRECT foreign load > 0.5 logical CPUs is flagged in the report (not dropped).

## 5. Methods (configurations frozen from dev: `wp5_ising/results/plan_H2test.json`)
Ising finalists, chosen by the rule pre-registered in `wp5_ising/PROGRESS.md` (Oct 1, 14:55, before any
dev-evaluation run) -- lowest mean dev-evaluation ratio V over the 3 budgets:
1. **PT** (replica exchange on LSE(L) + QUBO budget penalty; V = -14.58%): best tuning trial of F1__pt__b{1,3,10}
   (trial 9 in each study).
2. **EIM** (replica exchange + native hinge budget + augmented Lagrangian; V = -14.14%): trial 7 at 1 s; the phase-1
   10-s configuration at 3 s and 10 s.

Classical set (each with its best tuning trial per budget; 12 trials per solver per budget, exactly as every Ising
solver): **LP + round + repair** (`lp`), **HiGHS MILP** (`milp`), **OR-Tools CP-SAT** (`cpsat`), **true-objective
local search** (`ls`), plus `greedy` (Baleen order + repair) and `pgreedy` (peak-aware greedy), no hyperparameters.
Warm starts: both families choose from {LP rounding + repair, peak-aware greedy} (the tuned choice is part of each
configuration). No re-tuning, no other configuration may be added after this file is committed.

## 6. Seeds and order
- pt, eim, ls, cpsat, milp: seeds 0, 1, 2. lp, greedy, pgreedy: seed 0.
- Instance-major (Region7 s0.4, s0.5, s0.6, Region6 s0.4, s0.5, s0.6); per instance the budgets 10, 3, 1 s; inside an
  (instance, budget) block the (method, seed) runs in a fixed pseudo-random order
  `random.Random(zlib.crc32(f"{instance}|{budget}".encode())).shuffle(block)` (as phase-1 `q2heldout.py`).
- Every run is a row of `wp5_ising/trials.csv` (phase `h2test`); solutions in `wp5_ising/sols/`.
- Expected cost: 6 instances x (5 methods x 3 seeds + 3 x 1) x 14 s ~ 25 min of core time (+ process overhead).

## 7. Unit and pass criteria (judged separately for each finalist)
- Unit: per (instance, budget), the finalist's mean objective over its 3 seeds vs the **best classical method's mean**
  (lowest mean over lp, milp, cpsat, ls, greedy, pgreedy). Objectives within 1e-9 relative count as "<=" but never as
  "strictly better".
- (i) **Count criterion:** finalist <= best classical on >= 5 of the 6 instances at >= 2 of the 3 budgets.
- (ii) **Average criterion:** mean over all 18 (instance, budget) pairs of the finalist's mean objective < mean of the 18
  best-classical means (strict).
- **H2' is supported for a finalist iff (i) and (ii) hold.** Both finalists are reported whatever the outcome; "H2'
  passes" may be claimed only for a finalist that meets both. (Two finalists = a mild multiple comparison; stated next
  to the verdict.)
- Reported alongside, no verdict: per-budget counts, means and per-cell gaps (%), per-level objectives, wall-time
  distributions, over-budget counts, the foreign-load audit of every run.

## 8. Secondary analyses (pre-declared; not part of the verdict)
- The allocate-to-hard-level split (w = 6,1,...,1) changed no dev conclusion at any budget -> **not run on test**.
- Rolling re-solve variant (`src/p2roll.py`: 6-h windows, 3-h step, commit first half, cumulative write-rate cap,
  seed 0) on the 6 test instances at 1 s for PT, EIM, LS, MILP, CP-SAT, LP, pgreedy, greedy; reported as the stitched
  full-trace peak and per-window peaks; no criterion.

## 9. Dev evidence behind this protocol (details: RESULTS_dev.md sections 2-5)
Dev-evaluation means (8 dev instances x 3 fresh seeds; util %, lower is better):

| budget | PT | EIM | best classical per cell (LS in 22 of 24 cells, CP-SAT on the floored Region7 s0.2 at 3 and 10 s) | PT <= best classical | EIM <= best classical |
|---|---|---|---|---|---|
| 1 s | 23.251 | 23.539 | 23.031 | 3/8 | 0/8 |
| 3 s | 22.727 | 22.774 | 22.859 | 7/8 | 8/8 |
| 10 s | 22.685 | 22.702 | 22.703 | 5/8 | 3/8 |
| all 24 pairs | 22.888 | 23.005 | 22.864 | -- | -- |

Read with the test criteria (>= 5/6 ~ >= 7/8 on 8 instances): both finalists meet the count criterion at one budget
(3 s) and miss the average criterion -> **dev predicts H2' = FAIL**, mainly because the classical true-objective SA
wins at 1 s and ties at 10 s. The test is still worth running as pre-registered (a required WP5 deliverable; the
3-s Ising advantage and the 1-s classical advantage are both large relative to the seed spread).

## 10. Integrity
Leak check against `wp5_ising/.leak_marker` and `bash 0_reproduce/check_frozen.sh` before and after the test; no
change to any configuration, seed list, instance or criterion after this file is committed; nothing under
`0_reproduce/` or `1_literature_review/` is modified; no git commit by Track B.
