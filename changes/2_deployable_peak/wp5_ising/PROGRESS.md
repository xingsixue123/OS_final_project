# WP5 (Ising track) progress log -- Phase-2 Track B

## 2026-10-01 14:33 setup
- Area `P2/wp5_ising` (sandbox `env.sh`: HOME/XDG/TMPDIR/pip/conda/numba/torch caches inside the area,
  `CONDA_REGISTER_ENVS=false`, `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`); `.leak_marker` touched 14:33 before
  anything else. Solver env = phase-1 `explore/env` (read-only use; no new packages installed). Baleen env read-only.
- Code: phase-1 solver modules copied unchanged into `src/` (q2core, q2anneal, q2lp, q2cpsat, q2sb, q2mq, q2hybrid,
  q2run, q2tune, q2policy, q2launch_train; full phase-1 src snapshot in `src/phase1_copy/`). New: `p2run.py` (multi-
  instance runner, cores lock), `p2tune.py`, `p2deval.py`, `p2roll.py`, `p2scale.py`, `core_audit.py`.
- Dev instances `inst/full_Region{7,6}_s{0,0.1,0.2,0.3}.npz` = symlinks to phase-1 `explore/common/inst` (read-only;
  WP1 rebuilt Region7 s0.1 through its own pipeline: identical up to episode permutation / ties in Baleen's order, and
  R0 P100 identical, 33.676).
- Timing hygiene: every timing process (WP5 tuning/eval/rolling/scaling AND the WP1 solves) holds an exclusive flock on
  `wp5_ising/.cores07.lock` for its whole life and asserts CPU affinity == cores 0-7 (8 threads) -> no two timing runs
  ever overlap. `src/core_audit.py` (pinned to 8-23) logs any foreign thread using > 5% of a core on cores 0-7
  (`logs/core_audit.log`).
- Smoke (1 s budget, 8 nested levels): process overhead ~0.5 s; nested driver alone (greedy) 0.03 s, pgreedy 0.1 s,
  LP start ~0.4-0.5 s for all 8 levels -> 1 s budgets are feasible for every method.

## 14:44 tuning started (`src/chain_tune.sh`): budgets 1 -> 3 -> 10 s, 12 trials per solver per budget
- Ising: pt, eim, sb (matrix-free; ballistic/discrete/heated is a tuned parameter), mq (MindQuantum bSB/dSB/CAC).
  Classical: lp (+repair), milp (HiGHS), cpsat, ls (true-objective SA). Both families choose warm start in {lp, pgreedy}.
- Trial 0 of each study = that solver's phase-1 best 10-s configuration. Value = mean over the 8 dev instances of
  obj / pgreedy - 1 (pgreedy refs in `results/ref_pgreedy.json`); failed / over-budget (> 1.05 T + 0.5 s) -> +1.
- Phase-1 nested split kept (w = 2,1,...,1).

## 14:55 PRE-REGISTERED (before any dev-evaluation run, before tuning finished): dev evaluation + finalist rule
1. Dev evaluation (`p2deval.py`): config per (solver, budget) = best tuning trial of its study (same rule for every
   solver). Fresh seeds 101-103 (lp/greedy/pgreedy deterministic: one run), 8 dev instances, phase-1 split
   (`deval`) and the allocate-to-hard-level split w = (6,1,...,1) (`deval_hl`).
2. Ising finalist rule (<= 2 configurations for H2'): for each Ising solver s in {pt, eim, sb, mq} compute
   V(s) = mean over the 3 budgets and the 8 dev instances and the 3 seeds of (objective / pgreedy objective - 1) in the
   `deval` phase (phase-1 split). The two Ising solvers with the lowest V are the finalists; each finalist carries its
   per-budget configuration from (1). Tie (|dV| < 1e-5): lower V at 1 s wins. The rule is applied mechanically; the
   finalists are not changed afterwards by any other dev number.
3. Classical set for H2' = every tuned classical solver (lp, milp, cpsat, ls) with its per-budget configuration from
   (1), plus greedy and pgreedy (no hyperparameters). The H2' comparator per (instance, budget) is the best classical
   method's mean.
4. The hard-level split is a secondary analysis: the H2' verdict will use the phase-1 split; the hl split is reported
   (dev now, and on test as a non-verdict secondary if it changes any dev conclusion).

## 15:00 INCIDENT + topology finding -> tuning restarted from scratch (15:00)
- INCIDENT (detected by core_audit): an ad-hoc verification script of mine (an instance-identity check, `python -`)
  was launched WITHOUT `taskset` and ran on cores 0-2 at 100% from ~14:44:30 to ~14:47:40, i.e. during timing runs:
  WP5 tuning F1__pt__b1 trials 0-7 and the WP1 solves of Region4 s0 (lp, cpsat, pt). Actions: every WP5 tuning row
  so far (pt b1 x12, lp b1 x12, eim b1 x1 trials; 193 rows) is kept in trials.csv with status `superseded_restart`,
  the three Optuna studies were deleted, and tuning restarted from trial 0 at 15:00 (old log in
  `logs/superseded/`). WP1 Region4 s0 rows -> `contaminated_overlap`, re-run (tag `_rerun`). Rule since then: every
  ad-hoc command is pinned to `taskset -c 8-11,20-23`.
- TOPOLOGY: on this Ryzen 9 9900X logical CPU k and k+12 are the two SMT threads of ONE physical core (`lscpu -e`).
  "timing on 0-7, Baleen sims on 8-23" (the phase-1 rule, also this task's rule) therefore lets sims run on 12-19 =
  the SMT siblings of the timing cores (phase-1 timings had the same exposure). From 15:05 all Track-B Baleen sims are
  pinned to `8-11,20-23` (physical cores 8-11; a subset of the prescribed 8-23) and `core_audit.py` also logs foreign
  threads on 12-19 (`SIBLING`) so the background load on the timing cores' siblings (e.g. Track A's processes, which
  are not under my control) is documented per timing run. Recommendation for the H2' test: keep logical 12-19 idle.

## 16:22 coordinator: new coordination rule (Track A restarting for WP2)
- Track A is pinned to logical 8-11,20-23 while Track B timing runs are active -> 12-19 idle. When ALL Track-B timing
  runs on cores 0-7 are finished (WP5 tuning / eval / rolling / scaling and WP1 solves), Track B creates
  `P2/TIMING_IDLE`; if timing is needed again later: delete TIMING_IDLE, wait ~10 min for Track A's sims to drain.
- Track-B sims stay <= 6 concurrent on 8-11,20-23 (shared slot pool `wp1_offline/.sim_slots.d`, cap 6).
- Status at 16:21: tuning 3 s at eim (pt, lp done); deval 1 s done, deval_hl 1 s running; WP1 solves 15/39 instances
  (incl. 6 reused), R0 38/39, WP1 sims 32 done; `chain_rest.sh` (deval 3/10 s, finalists, label evidence, rolling,
  scaling) waiting on the tuning.
- Dev finding so far (1 s, deval, fresh seeds): the classical true-objective SA (ls) is the best method at 1 s
  (mean 23.013 vs PT 23.261, EIM 23.475; LP / MILP / CP-SAT / SB / MQ ~24.7 = essentially their LP or pgreedy start).
- 16:47 the 1-s `deval` runs (15:18-15:58) were NOT equally exposed to foreign load on the SMT siblings 12-19
  (`src/audit_load.py`: Ising runs 15:18-15:30 avg 1.7 foreign busy sibling threads while Track A was still running
  there; classical runs after 15:24: 0). To keep the comparison fair, all 1-s `deval` rows (both families)
  are kept with status `superseded_sibling_load` (192 rows) and the 1-s dev evaluation is re-run for every solver now that 12-19
  are idle (coordinator rule). Tuning trials were exposed about equally (Ising 4.1, classical 3.9 avg sibling threads)
  -> kept. The finalist rule has not been applied yet.

## Oct 1 21:20 - Oct 2 00:03 (detached chain, coordinator session gone): everything in chain_rest.sh completed
- 10-s tuning done 21:20; deval 3/10 s, hl 3/10 s, finalists (21:47: rule -> **PT, EIM**; V = -14.58 / -14.14 / mq
  -12.50 / sb -11.64; ranking unchanged if over-budget runs were counted as failures; no over-budget deval run),
  label day-1 timing (96 runs), label sims (40/40 matched), rolling 1 s (10 methods x 8) and 3 s (pt, eim, ls,
  pgreedy x 8) all finished.
- The scaling driver FAILED immediately (the driver process itself takes the cores lock, whose affinity assertion
  requires taskset 0-7; I had launched the driver unpinned). No scaling run happened (log kept in logs/superseded/).
## Oct 3 00:10 resumed (coordinator): all Track-B processes had died except core_audit.py (kept; still logging)
- 00:13 scaling relaunched with the driver pinned to cores 0-7 (`taskset -c 0-7 python p2scale.py all`).
- 00:20 rolling 3 s extended to milp, cpsat, lp: the 1-s rolling showed that on the small 6-h window instances the
  exact solvers (MILP 26.45, CP-SAT 26.47) are the best methods, so the 3-s rolling comparison (pt/eim/ls only) would
  otherwise miss the strongest classical methods. (Fill-in analysis, not part of any verdict.)
- Oct 3 01:11 all Track-B timing runs finished (WP5 tuning/eval/hl/label/rolling/scaling, WP1 solves) -> created P2/TIMING_IDLE; core_audit.py stopped.
- Oct 3 00:38 scaling done (88 runs: 85 ok, the dense SB package OOM on all 3 unions at the 64 GB cap). 01:11 3-s
  rolling for milp/cpsat/lp done (CP-SAT/MILP best at 3 s too). 01:11 TIMING_IDLE created (no Track-B timing left).
- 01:12 check_frozen: frozen OK (94 files); leak check: 378 hits, all attributable to non-Track-B activity
  (server_fix project, coordinator git objects / SCOPE_v2.md, HF cache of the server_fix job, desktop session files).
- 01:20 RESULTS_dev.md and PROTOCOL_v2_H2.md written (finalists PT + EIM; dev predicts H2' FAIL; label solver EIM
  10-s config at 10 s). STOP at CP2: no WP5 run on samples 0.4-0.6.
