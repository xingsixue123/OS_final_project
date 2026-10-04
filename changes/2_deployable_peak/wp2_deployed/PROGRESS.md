# Track A WP2 progress: 2x2 deployed study on DEV (Region7/Region6 x samples 0, 0.1, 0.2, 0.3)

Rules: everything through the reviewed overlay (`wp0_overlay/overlay`, CP1 approved, commit f79808f); no run on samples
>= 0.4; CPUs 8-11,20-23 and <= 6 own sims while Track B timing runs are active (0-23 / <= 14 sims when
`2_deployable_peak/TIMING_IDLE` exists, checked at every launch); every train under `2_deployable_peak/.train.lock`;
sandbox `env.sh`, bwrap with a private /tmp per job; no git commits.

- 2026-10-01 16:25 `.leak_marker`; area set up: `work/BCacheSim -> ../../wp0_overlay/overlay/BCacheSim`, `work/data ->
  explore/common/data` (read-only); phase-1 code COPIED (unmodified) into `src/q3lib` (q3solve, q3lib, pb3_policy) and
  `src/q2lib` (q2core, q2anneal, q2lp, q2cpsat, q2run); phase-1 sim-feature caches copied to `work/cache`.
- Design decisions (before any WP2 result):
  - Labels are solved once per (instance, design, seed) on `explore/common/inst/day1_<inst>.npz` (`src/labels.py`,
    solver env) -- the day-1 instance every deployed train builds (identical up to episode order) -- and applied in the
    train by `PolicyPeakBaleen4` (`src/pb4_policy.py`) by episode identity; the harness strict-prefix Baleen fill is
    re-applied in each run's own Baleen order (asserted at every sort call). Retrain k uses solver seed k.
  - Designs (phase-1 Ising configurations, unchanged): P0, T2, C2 (q3 PT, 15 s, 2 threads), F1PT and F1EIM (q2 F1
    finalists' frozen 10 s configs, single level f = 1.0, 10 s, 8 threads); F1CPSAT = same F1 formulation, OR-Tools
    CP-SAT (q2's classical finalist cfg, 10 s) for arm Dc.
  - Threshold convergence: sequential sims (+-1% of 35.599 MB/s), seeded/steered by the phase-1 emulator
    (`src/emu.py`), secant once bracketed; every reported number is a full simulation.
- 16:27 label solves started (`src/run_labels.py`, 144 = 6 designs x 8 instances x seeds 1-3).
- 16:31 arms A and B launched (`src/wp2.py --plan base`, 48 evaluations).
- 16:35-16:50 learnability gate running (`src/learn.py`, 8 instances x 7 label sets (Baleen, P0, T2, C2, F1PT, F1EIM,
  F1CPSAT; seed 1) x {orig, +load, +shuffled load, +load+tod} block split + {orig, +load} time split). Gate criterion
  fixed before reading (`src/learn_summary.py`): net = [val_logloss(orig) - val_logloss(+load)] - [val_logloss(orig) -
  val_logloss(+shuffled load)] > 0 and > 2 SE over instances.
- 16:52 partial gate (2-3 instances): Baleen and C2 labels: no load gain; F1PT/F1EIM/F1CPSAT +0.04-0.05 val logloss
  (AUC +0.035), P0 +0.03, T2 +0.018; shuffled control ~0. -> D screen launched (1 retrain x 8 instances) for F1PT,
  F1EIM, P0, T2 and F1CPSAT (= arm Dc); C2 deferred to the final gate verdict.
- 17:19 LEARNABILITY GATE (final, 8 instances, block split; `results/learnability_summary.csv`): net val-logloss gain
  of `load` over the shuffled-load control: F1PT 0.041+-0.006, F1EIM 0.038+-0.006, F1CPSAT 0.042+-0.006, P0 0.026+-0.005,
  T2 0.019+-0.003 -> PASS (positive on 8/8 instances each); C2 0.003+-0.002 and Baleen 0.001+-0.001 -> no gain (FAIL).
  Load helps the peak-aware labels more than Baleen's (+0.026..+0.042 over Baleen's gain). Time split (later day-1
  hours): positive on all Region7 instances and Region6 s0.2, negative on Region6 s0.1/s0.3. +load+tod adds
  0.005-0.016 on the block split. -> D screen continues for F1PT/F1EIM/P0/T2 (+F1CPSAT = Dc); D:C2 not run (gate).
- 17:27 drivers restarted with resumable convergence + per-(instance, arm) seeding bias (in-flight sims/trainings continued as orphans and are re-used).
- 17:55 all 144 label sets solved (`labels/`). Seed-1 day-1 label peaks (util %, mean of 8 instances): F1PT/F1CPSAT
  21.5, F1EIM 21.6, P0 22.4, T2 22.5, C2 24.9 vs Baleen 28.2 (25.2-31.7). F1 designs use the whole budget with fewer,
  larger episodes (563-1724 labels vs Baleen 1124-2500) and no zero-value labels; P0 keeps 37-44% zero-value labels
  (the phase-1 mechanism). Label stability across seeds (pairwise Jaccard): C2 0.86, F1PT 0.76, F1CPSAT 0.74,
  F1EIM 0.70, T2 0.56, P0 0.42. In-run label sets reproduce the offline ones exactly (core + strict-prefix fill).
- 2026-10-01 23:21 (logged on resume) arms A/B (3 retrains x 8 instances, 48 evaluations) and the D screen (F1PT,
  F1EIM, P0, T2, F1CPSAT=Dc; 1 retrain x 8 instances, 40 evaluations) all completed, all matched (0 failed). Then the
  coordinator session ended (all processes died); nothing was in flight. Resumed 2026-10-03 00:10.
- Screen result (P100, mean of 8 dev instances; A 38.50, B 38.44 with 3 retrains each): D:F1PT 37.99 (vs A +0.51,
  4/8 wins; vs B +0.45, 2/8), D:F1EIM 38.29 (+0.21 / +0.15; very volatile: Region6 s0/s0.1 -4..-5, Region7 s0.3 +7.7),
  Dc:F1CPSAT 39.38, D:P0 39.42, D:T2 39.65. B vs A: +0.06 +- 0.11 (5/8). Arm A (overlay) vs phase-1 Baleen online
  (frozen): per-instance |diff| <= 0.59, mean |diff| 0.16 (`results/summary_A_vs_phase1.csv`).

## RESUME (exact commands; the drivers are resumable: completed evaluations are skipped via trials.csv, completed sims
## of an unfinished evaluation are re-used, partial/orphaned sims are ignored once their files are > 7 min old)
```
cd /home/sxing/project/OS_final_project/changes/2_deployable_peak/wp2_deployed && source env.sh
# 1) anything running? (must be empty before relaunching)
pgrep -af "src/wp2.py|simulate_ap|wp2_launch_train" | grep -v pgrep
# 2) relaunch the last queue (stage 2; already complete as of 2026-10-03 04:14) -- prints "N to run"
Q='[["D",["F1PT"],[2,3]],["C",["F1PT"],[1]],["D",["F1EIM"],[2,3]],["C",["F1PT"],[2,3]],["Ea-0.5",["F1PT"],[1]],["D2",["F1PT"],[1]],["Epf",["F1PT"],[1]],["D",["F1CPSAT"],[2,3]],["C",["F1EIM"],[1]],["C",["F1EIM"],[2,3]],["Ea-1.0",["F1PT"],[1]]]'
nohup taskset -c 8-11,20-23 $BALEEN_PY -B src/wp2.py --queue "$Q" -j 16 >> logs/wp2_stage2.out 2>&1 &
# 3) the current/last queue is recorded below as "QUEUE <time>: ..." -- relaunch that one instead if newer
# 4) summaries: $BALEEN_PY -B src/summarize.py ; $BALEEN_PY -B src/summarize.py report ; $BALEEN_PY -B src/learn_summary.py
```
(CPU: sims pin to 0-23 / cap 14 only while ../TIMING_IDLE exists, else 8-11,20-23 / cap 6 -- automatic in SimSlot.)

## FINALIST RULE (written 2026-10-03 00:20, BEFORE any confirmation retrain is launched)
- Candidates: Ising-family configurations only (labels from PT or EIM: F1PT, F1EIM, P0, T2) in arms D, D2, E
  (E = D's models + load-adaptive threshold alpha, or + load-aware prefetch models). Dc (CP-SAT labels) is a
  comparison arm and is not eligible; arm C (no load) is not eligible (H3' requires `load`).
- Eligible: >= 3 matched retrains on every one of the 8 dev instances.
- Score S(X) = mean over the 8 dev instances of min(A_i - X_i, B_i - X_i), where X_i, A_i, B_i are mean P100 over all
  matched retrains (improvement over the better of the two baselines on each instance; positive = better).
- Finalists = the eligible configurations with S(X) > 0, ranked by S (tie-break: number of instances with X below both
  A and B), at most 3; rank 1 = primary finalist X1 of PROTOCOL_v2_H3. If no eligible configuration has S > 0 there is
  no finalist and H3' is reported as not supported on dev (no test run proposed).
- Confirmation (reps 2-3) is run for D:F1PT and D:F1EIM (the two configurations with a positive screen improvement
  over both A and B); a D2/E variant is confirmed only if its rep-1 screen improvement over min(A, B) exceeds that of
  D:F1PT rep 1 (paired, same instances). Dc and arm C get 3 retrains for the primary design (comparison / 2x2).
- 00:25 stage-2 driver launched (priority queue, 100 evaluations): D:F1PT r2-3, C:F1PT r1, D:F1EIM r2-3, C:F1PT r2-3, Ea-0.5:F1PT r1 (adaptive alpha=-0.5 on D:F1PT's models), D2:F1PT r1, Epf:F1PT r1 (Region7), Dc r2-3, C:F1EIM r1.
- 01:35 D:F1PT confirmed (3 retrains x 8): S = -0.14 (screen +0.32 regressed): Region6 s0/s0.1 better than both baselines (41.88/39.05 vs A 43.33/40.86), Region7 s0/s0.3 worse (retrains 36.2-42.3 on Region7 s0.3); first-access admission on Region7 drops 6-11% -> 1.5-3%.
- 02:15 TIMING_IDLE appeared -> stage-2 driver restarted with -j 16 (sims may use 0-23, cap 14 while the flag exists); queue extended by C:F1EIM r2-3 and Ea-1.0:F1PT r1; orphan sims held by hold_slots.py.
- 2026-10-03 04:14 (logged on resume 2026-10-04 05:17) stage-2 queue COMPLETE (124 planned; total 212 rows in trials.csv, 0 failed, 3 unmatched). Coordinator session ended ~02:15+ Oct 3; nothing in flight.
- 2026-10-04 05:25 RULE APPLIED to the D2/E screens (rep-1 S over min(A,B), paired with D:F1PT rep 1 = 0.237 on the same
  instances): Ea-1.0:F1PT 1.156 and Ea-0.5:F1PT 0.752 -> CONFIRM (reps 2-3 on D:F1PT's retrains); D2:F1PT -2.035 and
  Epf:F1PT -1.622 (vs -0.919 on its 4 Region7 instances) -> not confirmed. Eligible so far (>= 3 retrains): D:F1PT
  S = -0.142, D:F1EIM S = -0.238. Unmatched (WR steps across the +-1% window, 7 sims each): C:F1PT Region7 s0 r1,
  Region7 s0.1 r3, C:F1EIM Region6 s0.3 r1 -> one extra retrain (seed 4) each (labels solved), to keep >= 3 matched.
- Added (reported only, NOT eligible, rule unchanged): attribution controls with the same adaptive threshold on
  Baleen's own models (Ba = arm B's retrains + alpha, Aa = arm A's retrains + alpha), and Ea-1.0 on the CP-SAT labels
  (Dc + alpha, the Ising-vs-classical comparison under the same option). Alpha tuning screens (dev only): Ea-2.0:F1PT,
  Ea-1.0:F1EIM (confirmed only if their rep-1 screen beats D:F1PT rep 1, as the rule says).
- QUEUE 2026-10-04 05:26 (stage 3, logs/wp2_stage3.out; relaunch with this --queue if interrupted):
  [["Ea-1.0",["F1PT"],[2,3]],["Ea-0.5",["F1PT"],[2,3]],["Ba-1.0",["baleen"],[1,2,3]],["Ea-2.0",["F1PT"],[1]],["Ea-1.0",["F1EIM"],[1]],["Ba-0.5",["baleen"],[1,2,3]],["Ea-1.0",["F1CPSAT"],[1,2,3]],["C",["F1PT"],[4],["Region7_s0","Region7_s0.1"]],["C",["F1EIM"],[4],["Region6_s0.3"]],["Aa-1.0",["baleen"],[1,2,3]]]
- 06:10 stage 3 at 30/147; interim S (not final): Ea-1.0:F1PT 1.02 (2 retrains), Ea-0.5:F1PT 0.32 (2 retrains).
- 06:50 confirmations complete: Ea-1.0:F1PT S = +1.027 (3 retrains x 8, eligible), Ea-0.5:F1PT S = +0.386 (eligible); still running: Ea-2.0/Ea-1.0:F1EIM screens, Ba/Aa controls, Ea-1.0 on CP-SAT labels, C rep-4 fills.
- 07:30 alpha screens: Ea-2.0:F1PT unmatched on 8/8 instances (WR 39-69 MB/s at the threshold bound theta=1: with g >= 0.25 the high-demand periods alone exceed the budget) -> not confirmed; Ea-1.0:F1EIM screen 0.320 vs D:F1PT r1 0.346 on the same 7 instances (8th pending).
- 08:25 stage 3 COMPLETE (147 evaluations, 0 failed; trials.csv 359 rows, 40 unmatched). FINAL RULE APPLICATION:
  eligible with S > 0: Ea-1.0:F1PT S = +1.027 (rank 1), Ea-0.5:F1PT S = +0.386 (rank 2); D:F1PT -0.142 and D:F1EIM
  -0.238 eligible but S < 0. Variant screens: Ea-1.0:F1EIM 0.206 vs D:F1PT r1 0.237 (8 instances) -> not confirmed;
  D2, Epf -> not confirmed; Ea-2.0:F1PT unmatched on 8/8 (see next) -> no valid screen -> not confirmed (NOT re-screened:
  conservative, no further alpha tuning). => FINALISTS: X1 = Ea-1.0:F1PT, X2 = Ea-0.5:F1PT (no third eligible).
- 08:30 FINDING (tool limitation, not a rule change): every unmatched alpha-variant row stopped at the threshold
  search bound theta ~ 1 (`converge` clamps theta < 1; with the load-adaptive multiplier g in [0.25, 4] the meaningful
  base threshold range is (0, 4]). Affected: the attribution CONTROLS Ba-1.0/Aa-1.0 on all Region6 cells (WR 46-55 at
  theta = 1), Ba-0.5 (3 Region6 cells), Ea-1.0:F1CPSAT Region6 s0.1 r2, and Ea-2.0. The two finalists matched inside
  the bound on every cell (unaffected). Re-run of the affected CONTROL/comparison cells with the theta search widened to
  (0, 4] under distinct names Bx/Ax/Ex (= the same configuration; merged with the matched Ba/Aa/Ea rows in the analysis;
  the unmatched rows stay in trials.csv). Also C:F1PT Region7 s0.1 r5 (r1, r4 hit WR steps; label seed 5).
- QUEUE 2026-10-04 08:26 (stage 4, logs/wp2_stage4.out; relaunch with this --queue if interrupted): [["Bx-1.0",["baleen"],[1,2,3],["Region6_s0","Region6_s0.1","Region6_s0.2","Region6_s0.3"]],["Ax-1.0",["baleen"],[1,2,3],["Region6_s0","Region6_s0.1","Region6_s0.2","Region6_s0.3"]],["Bx-0.5",["baleen"],[1,2],["Region6_s0.3"]],["Bx-0.5",["baleen"],[3],["Region6_s0"]],["Ex-1.0",["F1CPSAT"],[2],["Region6_s0.1"]],["C",["F1PT"],[5],["Region7_s0.1"]]]
- 09:10 stage 4 COMPLETE (29/29 matched, 0 failed): controls Ba/Aa (Region6) and Ea-1.0:F1CPSAT Region6 s0.1 r2 now matched with the widened search (base theta 1.01-1.29); C:F1PT Region7 s0.1 r5 matched. ALL DEV RUNS DONE (388 rows). Next: final summaries, RESULTS_dev.md, PROTOCOL_v2_H3.md.
- 09:12 FINAL (rule applied mechanically on all 388 rows): finalists X1 = Ea-1.0:F1PT (S = +1.027; vs A +1.30 +- 0.25,
  6/8; vs B +1.24 +- 0.26, 6/8), X2 = Ea-0.5:F1PT (S = +0.386). Attribution (paired, `results/attribution.txt`): X1 vs
  Baleen labels + the same alpha (Aa-1.0) +0.68 (5/8; instance SE 0.63), vs Ba-1.0 +1.23 (5/8); alpha = -1 gains
  +1.17 +- 0.29 on F1PT labels (8/8), +0.62 on Baleen orig, +0.02 on Baleen + load, +0.28 on CP-SAT labels; X1 vs the
  same option on CP-SAT labels +1.26 (5/8). Gains concentrate on Region6 (peak window no longer a big-offset scan in
  10/12 retrains). Writing PROTOCOL_v2_H3.md (final) and RESULTS_dev.md.
- 09:15 CP2 deliverables written: RESULTS_dev.md, PROTOCOL_v2_H3.md (FINAL; X1 = Ea-1.0:F1PT primary, X2 = Ea-0.5:F1PT; H3'-labels secondary vs A+alpha/B+alpha; theta search (0,4] for alpha arms), trials.csv (388 rows), results/ (summary.md, attribution.txt, mechanism_by_region.txt, integrity.txt). Leak check (only foreign files) + check_frozen (OK, 94 files) in results/integrity.txt. STOP at CP2 (nothing running).
