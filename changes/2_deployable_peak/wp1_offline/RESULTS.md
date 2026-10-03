# WP1 -- H1' breadth (offline): peak-aware selection vs Baleen's peak-blind oracle on Regions 4-7 x samples 0-0.9

**Verdict: H1' = PASS for every peak-aware method (phase-1 frozen configurations, no tuning).**

| method (phase-1 frozen config, seed 0) | instances | wins vs R0 | win rate | mean P100 reduction vs R0 | mean P100 (R0 33.00) | H1' (>= 80% and mean >= 10%) |
|---|---|---|---|---|---|---|
| LP + round + repair | 39 | 36 | 92% | **13.03%** (sd 6.60, min -1.60, max 23.43) | 28.74 | **pass** |
| CP-SAT 300 s | 39 | 36 | 92% | **13.15%** (sd 7.21, min -6.88, max 23.64) | 28.78 | **pass** |
| PT 300 s (phase-1 Ising finalist) | 39 | 37 | 95% | **13.69%** (sd 6.43, min -4.06, max 23.46) | 28.59 | **pass** |

Per region (wins / mean reduction): **Region4 is the exception** -- LP 6/9, 4.6%; CP-SAT 6/9, 3.0%; PT 7/9, 5.4%.
Region5: 10/10 for all three (13.0 / 14.5 / 14.6%); Region6: 10/10 (16.3 / 16.4 / 16.6%); Region7: 10/10
(17.4 / 17.7 / 17.3%). Without Region4: 30/30 wins for all three methods, mean reduction 15.6 / 16.2 / 16.2%.
**Headroom gate (PLAN section 5, offline mean reduction >= 10% on Regions 4-7): met overall (13.0-13.7%) and on
Regions 5, 6, 7 separately; NOT met on Region4 alone (3-5%)** -> claims about Region4 should be narrowed.

## 1. Setup (as run)
- Instances: the authors' OPT-AP rows of `results_release.csv.gz` (OPT AP, "OPT-Range on OPT-Ep-Start", Target DWPD 7.5,
  366.47 GB, 0.1% samples) for Region4 (trace group 202110) and Regions 5/6/7 (20230325), samples 0-0.9 -> **39
  instances: Region4 sample 0.1 has no OPT-AP row in the release CSV** (its trace is also only 0.87 MB vs ~17 MB for
  the other Region4 samples) and is excluded. EA = the OPT's converged eviction age of the row (identical to phase-1
  jobs.json for Region7/6 s0-0.3). Instances built by the unmodified `train.main()` with `PolicyQ2` in dump mode
  (one train = instance + R0 decisions), n = 32k-89k episodes, 997-1009 windows, objective windows after day 1.
  Rebuilt Region7 s0.1 is identical to phase-1 `common/inst` up to episode permutation (ties in Baleen's order only).
- Methods: **R0** = Baleen's own peak-blind order (the "OPT AP" oracle of the paper) through the identical pipeline;
  **LP+repair**, **CP-SAT 300 s**, **PT 300 s** = phase-1 frozen 300-s configurations (`q2/plan_F1.json`: lp lexi=true;
  cpsat LP-hinted, presolve off; PT 16 replicas, LP start, QUBO budget penalty), F1 (min-max peak), 8 nested levels,
  seed 0, timed on cores 0-7 (8 threads) under the exclusive cores lock. All 117 solves ok, none over budget (PT walls
  300.005-300.025 s; CP-SAT 1.0-295.7 s, i.e. it proved optimality early on many instances; LP 2-15 s).
  Phase-1 300-s held-out solutions (seed 0) of lp/cpsat/pt on Region7/6 s0.1-0.3 were reused (identical configs and
  instances); everything else was solved here.
- Simulation: every selection replayed through the unmodified train (PolicyQ2 replay; prefix rule and instance identity
  asserted) and `simulate_ap --offline-ap --ap opt` with the authors' sim flags (+ `--eviction-policy LRU`), the
  OPT cutoff `--ap-threshold` converged to **35.599 MB/s +-1%** (phase-1 converge rules). **156/156 simulations
  matched** (WR 35.25-35.95), 816 simulator runs in total, none failed. Sims on cores 8-11,20-23 (<= 6 concurrent),
  every train under `flock P2/.train.lock`, every Baleen process in bwrap with a private /tmp.
- R0 reproduces the authors' OPT-AP P100 closely (mean R0 - author = -0.55, mean |diff| 1.02, max 4.81 on Region4 s0.3;
  our R0 is converged to 35.599 +-1% while the authors' rows sit at 34.0-35.8 MB/s).

## 2. Per-instance table (P100 = PeakServiceTimeUtil1, util %, matched WR; windows as day:hh:mm from trace start)
"analytic floor" = max over objective windows of C_w minus every positive saving (budget ignored): no admission policy
can push the instance's analytic peak below it. "PT planned window" = argmax window of PT's planned loads for exactly
the prefix the simulator admits (within f B, f = converged threshold / 35.599).

| instance | author OPT | R0 | LP+repair | CP-SAT 300 s | PT 300 s | analytic floor (window) | R0 peak window | LP / CP-SAT / PT sim peak window | PT planned window |
|---|---|---|---|---|---|---|---|---|---|
| Region4_s0 | 26.74 | 26.80 | 26.80 | 26.80 | 26.37 | 17.67 (d2 01:50) | d2 00:30 | d2 00:30 / d2 00:30 / d2 00:30 | d2 00:30 |
| Region4_s0.2 | 41.20 | 41.44 | 41.44 | 41.34 | 41.44 | 27.84 (d2 00:30) | d2 00:30 | d2 00:30 / d2 00:30 / d2 00:30 | d2 00:30 |
| Region4_s0.3 | 46.35 | 42.34 | 39.24 | 39.31 | 39.40 | 27.08 (d4 02:00) | d5 14:10 | d6 01:10 / d6 01:10 / d6 01:10 | d6 17:40 |
| Region4_s0.4 | 45.26 | 45.36 | 43.93 | 43.73 | 43.69 | 29.06 (d6 00:50) | d6 00:50 | d6 01:10 / d6 01:10 / d6 01:10 | d6 00:50 |
| Region4_s0.5 | 30.82 | 30.80 | 30.79 | 26.49 | 26.92 | 23.83 (d2 00:30) | d2 00:30 | d2 00:30 / d3 02:10 / d3 02:10 | d2 00:30 |
| Region4_s0.6 | 30.72 | 30.72 | 26.40 | 27.18 | 27.33 | 18.79 (d2 00:30) | d3 03:20 | d6 01:00 / d3 03:50 / d6 01:00 | d3 03:20 |
| Region4_s0.7 | 47.21 | 46.55 | 43.00 | 45.36 | 43.47 | 32.30 (d4 02:00) | d5 14:10 | d6 01:10 / d3 03:40 / d6 01:10 | d4 02:00 |
| Region4_s0.8 | 39.22 | 38.30 | 38.91 | 40.15 | 39.85 | 27.65 (d3 03:40) | d3 03:30 | d3 03:40 / d3 03:50 / d3 03:50 | d3 03:40 |
| Region4_s0.9 | 34.86 | 34.86 | 31.12 | 37.26 | 31.37 | 24.13 (d6 01:00) | d3 03:30 | d3 03:50 / d3 03:50 / d6 01:10 | d6 01:00 |
| Region5_s0 | 30.91 | 29.91 | 25.83 | 25.68 | 25.56 | 21.87 (d4 12:40) | d4 12:40 | d4 14:10 / d4 12:00 / d4 14:10 | d4 12:40 |
| Region5_s0.1 | 32.50 | 31.32 | 25.44 | 25.30 | 25.48 | 22.57 (d4 12:50) | d2 08:40 | d6 04:00 / d2 14:10 / d2 10:10 | d4 12:50 |
| Region5_s0.2 | 33.11 | 31.76 | 27.10 | 27.76 | 27.57 | 24.12 (d2 14:40) | d4 12:50 | d4 13:00 / d4 13:00 / d4 13:00 | d2 14:40 |
| Region5_s0.3 | 32.07 | 31.58 | 26.97 | 27.13 | 27.77 | 22.40 (d4 13:00) | d4 13:00 | d6 01:00 / d2 10:50 / d2 13:50 | d4 13:00 |
| Region5_s0.4 | 26.37 | 24.77 | 20.01 | 19.95 | 20.37 | 18.41 (d6 01:30) | d6 01:30 | d6 03:30 / d4 08:50 / d6 03:30 | d6 01:30 |
| Region5_s0.5 | 32.26 | 30.19 | 26.71 | 26.50 | 26.54 | 21.63 (d6 02:30) | d2 07:50 | d4 13:50 / d4 13:50 / d4 13:50 | d6 02:30 |
| Region5_s0.6 | 30.34 | 31.01 | 26.04 | 26.72 | 27.72 | 23.22 (d2 09:50) | d2 09:50 | d2 09:00 / d2 09:10 / d2 09:10 | d2 09:50 |
| Region5_s0.7 | 24.59 | 25.57 | 24.58 | 21.77 | 20.94 | 16.16 (d1 02:20) | d2 14:00 | d2 14:00 / d4 14:20 / d4 14:30 | d1 02:20 |
| Region5_s0.8 | 22.22 | 21.88 | 20.31 | 19.06 | 17.71 | 14.50 (d2 09:50) | d2 09:50 | d2 09:50 / d6 02:40 / d6 02:40 | d2 09:50 |
| Region5_s0.9 | 31.75 | 29.38 | 26.32 | 26.07 | 26.36 | 21.47 (d2 15:40) | d2 13:40 | d2 15:50 / d2 15:50 / d2 13:50 | d2 15:40 |
| Region6_s0 | 36.81 | 35.56 | 27.97 | 27.76 | 27.77 | 20.88 (d5 14:20) | d5 16:00 | d5 16:00 / d3 17:50 / d1 01:40 | d5 04:40 |
| Region6_s0.1 | 31.56 | 30.90 | 26.54 | 26.03 | 26.18 | 20.06 (d5 16:10) | d5 16:10 | d5 15:00 / d5 15:00 / d5 15:00 | d5 16:10 |
| Region6_s0.2 | 31.29 | 30.62 | 26.62 | 26.15 | 26.49 | 21.09 (d5 01:20) | d5 13:10 | d5 14:10 / d5 14:10 / d5 15:30 | d4 08:10 |
| Region6_s0.3 | 34.48 | 31.96 | 26.92 | 27.12 | 27.14 | 20.36 (d5 14:40) | d5 15:50 | d5 15:10 / d5 14:40 / d5 14:40 | d3 01:50 |
| Region6_s0.4 | 35.16 | 34.25 | 28.12 | 28.09 | 27.72 | 21.22 (d5 10:20) | d5 09:50 | d5 14:20 / d5 14:20 / d5 14:20 | d1 01:20 |
| Region6_s0.5 | 35.92 | 34.55 | 29.31 | 29.72 | 29.21 | 23.67 (d5 14:10) | d5 12:30 | d5 14:10 / d5 12:30 / d5 12:30 | d5 14:10 |
| Region6_s0.6 | 32.57 | 32.64 | 26.66 | 27.30 | 26.79 | 20.08 (d5 14:50) | d5 14:50 | d2 05:20 / d2 05:20 / d2 05:20 | d5 14:20 |
| Region6_s0.7 | 32.90 | 32.90 | 27.90 | 27.90 | 27.89 | 21.26 (d5 09:10) | d5 14:10 | d5 14:10 / d5 14:10 / d5 14:10 | d5 16:10 |
| Region6_s0.8 | 33.50 | 35.71 | 28.42 | 28.41 | 28.31 | 22.88 (d5 15:50) | d5 15:50 | d5 15:50 / d5 15:50 / d5 15:50 | d5 15:50 |
| Region6_s0.9 | 38.44 | 33.62 | 29.67 | 29.27 | 29.64 | 21.84 (d5 09:20) | d5 09:20 | d1 20:50 / d1 20:50 / d1 20:50 | d5 12:10 |
| Region7_s0 | 34.48 | 34.52 | 28.14 | 27.85 | 28.27 | 24.09 (d4 11:50) | d4 14:00 | d4 14:00 / d4 11:50 / d4 14:00 | d4 11:50 |
| Region7_s0.1 | 33.07 | 33.68 | 27.63 | 27.42 | 27.53 | 23.12 (d2 01:50) | d4 07:30 | d2 02:00 / d2 02:00 / d2 02:00 | d2 01:50 |
| Region7_s0.2 | 36.29 | 35.28 | 28.41 | 27.98 | 27.59 | 25.41 (d4 13:30) | d4 13:30 | d2 01:30 / d2 01:30 / d2 01:30 | d4 13:30 |
| Region7_s0.3 | 31.49 | 31.23 | 26.88 | 26.68 | 26.53 | 21.45 (d1 06:50) | d1 18:00 | d4 10:00 / d4 10:00 / d4 10:00 | d1 21:20 |
| Region7_s0.4 | 32.43 | 33.83 | 27.23 | 27.51 | 27.18 | 23.88 (d2 02:30) | d4 13:50 | d4 14:00 / d4 09:30 / d4 09:30 | d2 02:30 |
| Region7_s0.5 | 32.62 | 31.52 | 26.80 | 26.44 | 26.40 | 22.77 (d6 02:10) | d4 13:30 | d4 07:40 / d4 09:10 / d4 09:10 | d6 02:10 |
| Region7_s0.6 | 34.18 | 34.91 | 26.73 | 26.66 | 26.72 | 22.39 (d4 14:00) | d4 14:00 | d4 14:40 / d4 14:10 / d4 14:40 | d5 15:40 |
| Region7_s0.7 | 27.86 | 28.69 | 24.02 | 24.86 | 24.96 | 21.17 (d4 02:20) | d4 14:00 | d4 10:20 / d4 10:20 / d4 00:30 | d4 02:20 |
| Region7_s0.8 | 32.92 | 34.01 | 26.61 | 26.12 | 26.25 | 23.50 (d4 10:20) | d4 10:20 | d4 12:00 / d4 12:00 / d4 12:00 | d4 10:20 |
| Region7_s0.9 | 32.16 | 32.17 | 29.53 | 29.41 | 30.64 | 22.78 (d4 10:10) | d2 01:30 | d4 11:20 / d4 11:20 / d4 11:20 | d4 14:00 |

Secondary metrics (mean reduction vs R0): P99 -- LP 8.6%, CP-SAT 9.2%, PT 9.2%; top-5 window mean -- 10.8 / 11.2 / 11.3%.
Samples 0-0.3 (the prioritised block): LP 13/15 wins, 13.5%; CP-SAT 14/15, 13.9%; PT 14/15, 13.7%. Samples 0.4-0.9:
LP 23/24, 12.7%; CP-SAT 22/24, 12.7%; PT 23/24, 13.7% (the gain is stable across the sample blocks).

## 3. Findings
1. **H1' holds broadly**: on Regions 5-7 every peak-aware method beats the peak-blind oracle on every instance (30/30),
   by 13-18% on average per region. The gain is a formulation effect, as in phase 1: the Ising PT and the classical
   LP/CP-SAT selections simulate within ~0.2 P100 of each other on average (PT - CP-SAT = -0.18, PT lower on 18/39;
   PT - LP = -0.15, PT lower on 22/39); best-of-the-three would give 14.6%.
2. **Region4 has little headroom.** Its peaks are short bursts (window 291 = d2 00:30 on samples 0, 0.2, 0.5 with
   no-cache load C_w = 84-182% util; d5-d6 night windows on others) that Baleen's oracle already absorbs as far as the
   write budget allows; the peak-aware solvers either tie R0 (s0, s0.2: same window, budget-bound) or win a few points.
   Losses: CP-SAT -6.9% on s0.9 and -4.8% on s0.8, PT -4.1% on s0.8, LP -1.6% on s0.8 -- the simulated peak migrated
   to a window the plan did not protect (see 3).
3. **Peak migration is the rule, not the exception.** The simulated peak window differs from R0's on 30/39 (LP), 34/39
   (CP-SAT), 33/39 (PT) instances, and the planned (analytic) peak window of the admitted prefix coincides (+-10 min)
   with the simulated one on only 6/39 (LP), 9/39 (CP-SAT), 6/39 (PT). The min-max plan flattens the analytic loads
   so far that the simulated maximum is set by model-simulator differences (prefetch-range effects, eviction /
   residency differences of the converged cutoff) in some other window; the simulated peak hour also moves (R0 peaks
   cluster at 13-14 h; PT's peaks spread over 0-3 h and 13-15 h). Planned peaks are below the simulated
   ones by 4.4-5.2 points on average (median 4.3-4.6, range -2.5 to +14.7), so the analytic objective is an optimistic
   proxy for P100.
4. No method / instance was unmatched or failed; no result was excluded.

## 4. Integrity
- Pure evaluation: phase-1 frozen configurations only; nothing tuned on any WP1 instance; WP1 results on samples >= 0.4
  were not used by WP5 (WP5 tuning / selection used the dev instances Region7/6 s0-0.3 only).
- Incident (14:44:30-14:47:40): an unpinned ad-hoc script of mine ran on cores 0-2 while the Region4 s0 solves ran;
  those three rows are kept as `contaminated_overlap` and were re-run (tag `_rerun`); only the re-runs are used.
  From 15:00 all Track-B Baleen work is pinned to 8-11,20-23 (never the SMT siblings 12-19 of the timing cores).
- Files: `jobs.json` (instance list), `trials.csv` (every solve incl. reused and flagged rows), `results/sims.jsonl`
  (every simulation with all thresholds tried), `results/wp1_table.{csv,md}`, `results/wp1_summary.json`,
  `results/peakcheck.csv` (sim vs model load at the simulated peak), `src/` (wp1_jobs, wp1, p2sim, wp1_analyze,
  wp1_peakcheck, q2policy, q2launch_train), `work/` (Baleen runs, logs with full commands).
- Leak check and check_frozen: see `wp5_ising/RESULTS_dev.md` section 9 (one marker for the whole Track B).
