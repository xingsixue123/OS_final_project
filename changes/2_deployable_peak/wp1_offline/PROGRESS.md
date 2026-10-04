# WP1 (H1' breadth, offline) progress log -- Phase-2 Track B

## 2026-10-01 14:33 setup
- Area `P2/wp1_offline` (sandbox `env.sh`, same layout as wp5_ising; `.leak_marker` 14:33). Baleen env and the
  frozen artifact are used read-only; work dir `work/` with `BCacheSim` -> `0_reproduce/baleen_code/BCacheSim` and
  `data` -> phase-1 `explore/common/data` (read-only symlinks; traces sha1-verified in phase 1); every Baleen process
  runs as `taskset -c 8-23 bwrap --dev-bind / / --bind work/systmp /tmp --`, `OMP_NUM_THREADS=2`, `python -B`;
  every train under `flock P2/.train.lock` (shared with Track A); <= 6 concurrent sims for the whole track (flock slot
  pool `wp1_offline/.sim_slots.d`).
- Instance list `jobs.json` (`src/wp1_jobs.py`): the authors' OPT-AP rows of results_release.csv.gz for Regions 4-7 x
  samples 0-0.9 (same row filter as phase-1 make_jobs.py). 39 instances: **Region4 sample 0.1 has no OPT-AP row in the
  release CSV** (and its trace is 0.87 MB vs ~17 MB for the other Region4 samples) -> excluded, documented. EAs of
  Region7/6 s0-0.3 identical to phase-1 jobs.json.
- Pipeline (copied from phase-1 q2sim with P2 paths; `src/p2sim.py`, `src/wp1.py`):
  * `r0`: ONE train in PolicyQ2 'dump' mode = instance dump (harness format) + Baleen's own order (R0, peak-blind OPT);
    OPT-mode sim with --ap-threshold converged to 35.599 MB/s +-1% (phase-1 converge rules, seeds = author OPT
    threshold +-1).
  * `solve`: LP+repair, CP-SAT 300 s, PT 300 s = phase-1 frozen 300-s configurations (`q2/plan_F1.json`), seed 0,
    nested 8-level output (phase-1 pipeline), on cores 0-7 under the P2 cores lock (no overlap with WP5 timing).
    Phase-1 held-out 300-s seed-0 solutions of lp/cpsat/pt for Region7/6 s0.1-0.3 are REUSED (same frozen configs,
    same instances, same machine) -> 18 rows copied into trials.csv (phase `wp1_reused_phase1_heldout`).
  * `sim`: every solution replayed through the identical train (PolicyQ2 replay; prefix rule + instance identity
    asserted) and OPT-mode sim converged to 35.599 +-1%, seeds = R0's converged threshold +-1.
- Check: rebuilt Region7 s0.1 == phase-1 `common/inst/full_Region7_s0.1.npz` up to episode permutation (D, C, s, B,
  identities, scores identical; Baleen order identical up to ties); R0 P100 = 33.676 (phase-1: 33.676). Region7 s0
  R0 = 34.522 (harness_eval: 34.52).
- Priority order: samples 0-0.3 of all four regions first, then 0.4-0.9.

## 14:40 r0 (instances + R0 sims) running; 14:42 solve loop running (alternates with WP5 tuning on the cores lock)

## 15:00 incident (see wp5_ising/PROGRESS.md): Region4 s0 lp/cpsat/pt solves overlapped an unpinned script of mine on
  cores 0-2 (14:44:30-14:47:40) -> rows flagged `contaminated_overlap`, re-run with tag `_rerun` (their sims get the
  exp suffix `_rerun`; the analysis uses only sims of `ok` rows). Since 15:05 the WP1 Baleen sims/trains run on
  `taskset -c 8-11,20-23` (physical cores 8-11, never the SMT siblings 12-19 of the timing cores); the r0/sim loops
  were restarted (resumable; finished sims reused) after the orphaned old-pinning sims completed.
- 15:20 WP1 solve gate opened (WP1 solves alternate with WP5 tuning on the cores lock; scheduling only).
- 19:36 all 117 solves done (39 instances x lp/cpsat/pt; 0 over budget). 19:55 all 156 sims matched (816 sim runs).
- 20:15 RESULTS.md written: H1' PASS for LP (36/39, 13.0%), CP-SAT (36/39, 13.2%), PT (37/39, 13.7%); Region4 weak
  (3-5%), Regions 5-7 30/30.
- See wp5_ising/RESULTS_dev.md section 9 for the final leak check / check_frozen of the whole Track B (Oct 3 01:12).
