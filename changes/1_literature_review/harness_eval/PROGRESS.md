# harness_eval progress log

## P0 infra (done 2026-09-28)
- H = this dir. `env.sh` sandboxes HOME/XDG/TMPDIR/pip/conda/MPL/numba/torch caches under H; every Baleen
  process runs under `bwrap --dev-bind / / --bind H/work/systmp /tmp --`; `.leak_marker` touched at start.
- `work/BCacheSim -> ../../../0_reproduce/baleen_code/BCacheSim`, `work/data -> ../../../0_reproduce/work/data`
  (relative symlinks, verified to resolve).
- `src/launch_train.py`: registers `PolicyPeakBaleen` into `policies.__dict__`, calls unmodified `train.main()`.
- `src/peakbaleen_policy.py`: the one Policy subclass (modes: `baleen` = Baleen's own order, `solver` =
  instance -> npz -> solver-env subprocess (`src/solve.py`) -> nested selected set first, then Baleen order).
  Asserts sum_w d(e,w) == rl.service_time_saved and that the label rule `threshold < 35.599` reproduces the
  selected set exactly (checked on every one of train.py's 3 sort calls).
- Skeleton verification, Region7 day 1 (EA 5653.153, authors' train args minus GBMs), `results/p0_skeleton_verify.csv`:
  stock `PolicyUtilityServiceTimeSize2` run twice (A1, A2), skeleton (B1), solver plumbing with the identity
  candidate (C1). All 12,320 episodes: identical scores, identical labels (2,361 positives, 0 label diffs).
  Per-episode thresholds differ only inside score-tie groups (1,445 groups; every group's threshold range is
  identical in all runs) -- exactly the stock run-to-run behaviour (A1 vs A2), caused by train.py's
  imap_unordered episode order + numpy's unstable argsort on tied scores.

## P1 Gate 0 fidelity (done)
- Offline pipeline: full-trace episodes via `launch_train` with `--train-split-secs-end 1e9`, no GBMs, no
  `--train-target-wr` (policy gets target 35.599 from its config); authors' OPT-AP settings for
  "OPT-Range on OPT-Ep-Start" (filter_=prefetch, OPT converged EA: R7 4442.942 s, R6 3848.741 s);
  sim `--offline-ap --ap opt --prefetch-when at_start --prefetch-range acctime-episode --eviction-policy LRU`
  with `--offline-ap-decisions` = our full-trace decisions; `--ap-threshold` (MB/s cutoff) converged to
  35.599 +-1% (converge.py logic copied into src/hecommon.py, direction-aware).
- R0 (Baleen peak-blind OPT, our skeleton): R7 P100 34.522 @ WR 35.55 (cutoff 30.378);
  R6 P100 35.556 @ WR 35.68 (cutoff 27.790). Authors' OPT AP (same prefetch variant, tracedrop = older DT
  metric): R7 34.480 @ 34.68, R6 36.813 @ 34.76. At the authors' own cutoff (27.4728) our R6 WR is 34.70
  (theirs 34.76); the R6 peak gap (-1.26) is of the size RESULTS.md attributes to the tracedrop metric version.
- d(e,w)/C_w: C_w equals the simulator's per-window service_time_nocache to 6e-11 (all 997 windows, both traces).
- Analytic vs simulated per-window DT (windows after day 1), admitted set = threshold <= converged cutoff:
  R0: r=0.994 (R7) / 0.985 (R6), same argmax window, top-10 overlap 9/10; residual sd 0.40 / 0.66 util-pts.
  R1 (LP, 6 nested levels): r=0.987 / 0.947 but PEAK MIGRATION: analytic argmax 189 -> sim argmax 660 (R7),
  371 -> 154 (R6); sim peak exceeds analytic peak by 3.3 / 4.6 pts; residual concentrated in the heavily
  shaved high-no-cache windows (R7 646/647/660/662, R6 152/154/807/816).
- Mechanism evidence (src/occupancy.py): analytic cache occupancy (EA model) of Baleen's own admitted set
  exceeds the 3,002-chunk cache in ~40% of windows (max 1.5x R7, 2.0x R6), and corr(occupancy, sim-analytic
  residual) = 0.64 (R7) / 0.78 (R6) -> motivates C3 (capacity-coupled).
- results: results/gate0.csv, results/gate0_series_*.npz, results/offline.csv (R0, R1_L6).

## P2 offline candidates (done; results/offline.csv, results/analytic_levels.csv, results/gate0_all.csv)
- Nested prefix: 11 levels f = 0.50..1.00 (step .05) of the harness budget B (bottom-up, S_k forced into
  S_{k+1}); within an increment Baleen order; then the harness strict-prefix fill in Baleen order.
  (Needed: the converged OPT cutoff lands at 0.72-0.89 W, so the simulator admits only a prefix of S.)
- Simulated P100 at matched WR (R7 / R6): R0 34.52 / 35.56; R1 28.10 / 27.77; R2 27.77 / 27.60;
  R3 28.31 / 27.60; C1 28.22 / 27.92; C2 28.34 / 28.18; C4 27.97 / 27.87; C5 28.20 / 27.69;
  RB4 27.74 / 27.88; C3L(k=1.5) 28.89 / 29.58; C3(k=1.5) 29.00 / 29.28.
  Every arm beats R0 by 5.5-8.0 pts on both traces -> criterion (a) satisfied by all of them.
- Spread among the LP-family/Ising arms (27.6-28.3) is small compared to the migration residual (+3-5 pts at
  the heavily-shaved windows). Analytic ranking (mean over levels): R2 best on R6, C2 best on R7.
- H2: C1 accepted moves won by HiGHS sub-MILP 243, true-objective SA 118, sub-QUBO SA 2. C5: HiGHS sub-MILP
  <= MQ bSB <= warm-start LP < MQ dSB < dwave SA = Tabu (analytic).

## P3 deployed (done; results/deployed.csv)
- Day-1 solve at W only (levels=[1.0]) inside the authors' Fig 9 TrainCommand (GBMs trained on our labels),
  authors' ReproduceCommand (`--ap mlnew`), threshold re-converged to 35.599 +-1%.
- Control: Baleen via our skeleton R7 40.05 / R6 43.34 (ref 40.10+-0.18 / 43.25+-0.04).
- R2 (5 retrains): R7 40.35+-0.14, R6 42.38+-0.95; C4: 40.07+-0.03 / 43.20+-0.10; C5: 40.06+-0.07 / 43.19+-0.31;
  C2: 40.85+-0.34 / 43.09+-0.16; RB4: 40.19+-0.40 / 42.97+-0.25. None satisfies (b).
- Ops notes: GBM labels from peak-aware selections need a much lower mlnew threshold (0.40-0.54), so the
  converge loop got a secant extrapolation when unbracketed; OMP_WAIT_POLICY=PASSIVE fixed LightGBM stalls under
  CPU sharing; a cross-process sim slot pool (work/.sim_slots) capped concurrent sims. C2 Region7 rep2's train
  was re-invoked after an interrupted run and returned early ("files already exist") -> replaced by rep4.

## P4 report: RESULTS.md written; check_frozen OK; leak check: only non-harness files (IDE/Copilot/user shell/agent).
