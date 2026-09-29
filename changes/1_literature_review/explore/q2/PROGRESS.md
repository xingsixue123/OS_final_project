# Track B (q2) progress log

## B0 environment (done 2026-09-28 15:58)
- `conda create -y -p X/env --override-channels -c conda-forge python=3.11` under the q2 sandbox (q2/env.sh: HOME, XDG,
  TMPDIR, pip/conda/MPL/numba/torch caches inside X; CONDA_REGISTER_ENVS=false; PYTHONNOUSERSITE=1; PYTHONDONTWRITEBYTECODE=1).
- pip: numpy 2.4.6, scipy 1.17.1, numba 0.67.0, highspy 1.15.1, PySCIPOpt 6.2.1, ortools 9.15.6755, optuna 5.0.0,
  torch 2.14.0+cpu, simulated-bifurcation 2.0.0, dwave-samplers 1.8.0, dimod 0.12.22, openjij 0.12.2, mindquantum 0.12.0,
  pandas 3.0.6 -- all installed, none skipped (env/install_outcomes.tsv, env/env.lock.txt). ENV_READY written.
- Known issue: ortools and highspy cannot share a process (ortools bundles HiGHS; undefined-symbol ImportError).
  CP-SAT runs in its own process without highspy.
- Leak check after install: empty (no file outside explore/ newer than q2/.leak_marker).

## B1 infrastructure (done 16:25)
- Code in q2/src (harness_eval code copied to src/orig_harness/ for reference; nothing under harness_eval/ touched):
  q2core (instance, formulations F1/F2a/F2b, numba shared repair incl. exact lazy greedy for F2b, nested driver with a
  global deadline, final order, nested objective), q2lp (HiGHS LP/MILP), q2cpsat (CP-SAT, own process, scipy-HiGHS LP
  start), q2scip (SCIP; exact convex MIQCP for F2b), q2anneal (one numba chain kernel shared by the classical LS
  [hard budget, independent chains, restarts] and the Ising EIM/PT [native hinge+ALM or QUBO penalty, replica exchange]),
  q2sb (matrix-free SB ballistic/discrete/heated), q2mq (contested-subset QUBO LNS: MindQuantum bSB/dSB/CAC, dwave SA,
  OpenJij SA), q2hybrid (LNS with EIM sub-sampler, optional sub-MILP share), q2run (one trial -> trials.csv), q2tune
  (Optuna, equal trials), q2heldout, q2policy/q2launch_train/q2sim (replay Policy + OPT-mode converge), q2analyze.
- Dev instances: q2/inst/dev_Region{7,6}.npz = copies of harness_eval/work/inst/dump_Region{7,6}_dump.npz (sha256 equal).
- Protocol-level choices fixed BEFORE tuning (same for every method): 8 nested levels f = 0.65..1.00 (converged OPT
  cutoffs in harness_eval were 0.71-0.86 W); level time = remaining * w_k / sum_{j>=k} w_j with w = [2,1,...,1] (level 1
  is the only big sub-problem); objective = mean over levels of the formulation objective of the PREFIX sets of the
  emitted order (what the simulator admits); clock starts after instance load + numba warm-up; MILP/CP-SAT/SCIP
  solutions returned after their level deadline are discarded.
- Smoke findings (10 s): F1 is degenerate on dev Region7 (LP bound 24.088 at every level: one floor window), so
  F1 cannot give a strict win there; F2b with tau = 0.8*greedy peak is degenerate (objective 0) -> tau_rel = 0.6 fixed.
  HiGHS MIP presolve ignores its time limit (2.4 s on F1, 23 s on F2b tangent model) -> presolve on/off is tunable.
- Primary formulation for Q1/Q2: F2b (squared-hinge soft peak, tau = 0.6 x Baleen-greedy peak at W, per instance),
  chosen because it is quadratic (MILP needs tangent cuts, CP-SAT needs products, SCIP MIQCP) and Ising-native.
## B1 tuning (running from 16:28): F2b, 10 s, 10 trials per solver (ls, eim, milp, pt, cpsat, hlns, lp, sb, scip, mq)
- INCIDENT 16:53: a chained F1-tuning launcher used a pgrep pattern with '{' (regex error -> treated as "not running")
  and started F1 tuning concurrently with the F2b tuner on cores 0-7 for ~25 s (16:53:08-16:53:35). Killed at 16:53:35.
  The 8 trials.csv rows that overlapped (F2b lp trials t4-t6, F1 ls t0 + its greedy ref) are flagged
  status=contaminated_overlap; the F1 study was deleted; the whole F2b lp study is re-run cleanly afterwards.
- PRE-REGISTERED (17:00, before any held-out run): Q1 and the Q2 simulation clause use the 300 s held-out solutions of
  (a) every Ising finalist, all 3 seeds, and (b) the per-instance best classical method at 300 s (all its seeds).
  If the shared train lock / wall clock prevents completing all of them, the seed-0 subset is reported for ALL methods
  equally. Q2 objective comparison unit: per (instance, budget), Ising mean over its 3 seeds vs the best classical
  method's mean (deterministic methods: 1 run). Dev sim so far: F2b peak-aware greedy on Region7 -> P100 28.53 @ WR 35.47
  (harness_eval Baleen peak-blind OPT on the same instance: 34.52).

## B1 dev results so far (17:35)
- F2b 10 s (value = mean over dev of obj/pgreedy - 1): classical ls -0.143%, lp -0.020%, milp -0.019%, cpsat -0.010%,
  scip 0.000%; Ising pt -0.134%, eim -0.104%, hlns -0.059%, mq -0.019%, sb 0.000%.  => classical LS leads.
- F1 10 s: Ising pt -15.010%, eim -14.973% vs classical ls -14.901%, milp -14.760%, cpsat -14.566%, hlns -14.066%,
  lp -13.172%.  => Ising leads at 10 s (both dev instances).
- Dev sims (OPT mode, matched WR): F2b pgreedy R7 28.53 / R6 28.26; F2b ls(t6) 28.47 / 28.28; F2b pt(t8) 28.53 / 28.24
  (harness_eval Baleen peak-blind OPT: 34.52 / 35.56).
- Decision (dev evidence): primary Q2 formulation = F1 (Ising ahead at 10 s on both dev instances; F2b favours the
  classical LS). F1 60 s stage (top-2 of 10 s + default, 3 trials per solver) chained.
- Track A published common/Q3_FORMULATION.md at ~17:30 (F4 = day-1 energy, DRAFT, final configs pending). A second
  full held-out Q2 campaign for F4 does not fit on the exclusive timing cores next to F1 (~6 h each); F4 is documented,
  not run, unless time remains after F1.

## B1 F1 60 s stage (done 18:24) and finalists
- F1 60 s (top-2 of 10 s + default, 3 trials each): classical cpsat -15.530%, ls -15.229%, milp -14.798%, lp -13.149%;
  Ising pt -15.167%, eim -15.110%, hlns -14.796%, mq -14.036%, sb -13.236%.  => on dev Ising leads only at 10 s.
- Dev F1 sims: pt(t5) R7 28.96 / R6 27.65; ls(t1) R7 27.85 / R6 27.76.
- Finalists (dev only): (F1, pt) and (F1, eim) = the two best Ising configs at both 10 s and 60 s. Classical set:
  greedy, pgreedy, lp, milp (deterministic, 1 run), cpsat, ls (3 seeds). SCIP omitted for F1 (linear; protocol lists
  SCIP for quadratic formulations; HiGHS and CP-SAT cover the MIP side).
## B2 held-out (started 18:25): q2heldout.py --plan plan_F1.json (288 runs, instance-major, 300 s block first);
  q2simloop.py simulates the 300 s solutions of pt/eim (3 seeds) and the per-instance best classical (all seeds).
  core_audit.sh logs any non-q2run process with >5% CPU on cores 0-7 (logs/core_audit.log).
- 18:30 audit: core_audit.py (per-thread CPU deltas on cores 0-7, excluding q2run.py) -> logs/core_audit3.log. Only the
  user's VS Code Pylance server appeared (transient bursts, ~14 CPU-s in the first minutes); not touched.
- Dev per-level insight (60 s, F1): Region7 -> PT at the 24.088 floor on all 8 levels, CP-SAT/LS miss it only at level 1;
  Region6 -> CP-SAT better on every level, PT's deficit grows on the small later increments (5% of B each).
- R0 (Baleen peak-blind order) queued for the 6 held-out instances through the identical pipeline (q2r0.py) as a
  same-pipeline Q1 comparator next to Track A's baselines.csv.
- 19:15 held-out R0 (Baleen peak-blind order through the identical q2 pipeline, OPT mode, matched WR): P100
  R7 s0.1 33.676, s0.2 35.277, s0.3 31.228; R6 s0.1 30.901, s0.2 30.616, s0.3 31.964.
- Dev sims of the 60 s-stage F1 solutions: cpsat 27.85/27.91, ls 27.95/27.59, pt 27.88/27.86 (R7/R6).
- check_frozen.sh at 18:58: frozen OK (94 files).
- 19:16 first held-out block (R7 s0.1, 300 s): cpsat 23.1166 on all 3 seeds (proves every level optimal in 23-32 s);
  pt 23.118/23.125/23.134; ls 23.147/23.153/23.153; eim 23.1546 x3; lp 23.407; milp 25.498 (219 s); pgreedy 27.503;
  greedy 33.023. The instance is floored at 23.1166 on every level; all differences come from level 1 (65% of B).
  => at 60/300 s the best classical is the proven optimum; Ising can only tie there.
- Held-out sims so far (300 s, R7 s0.1): pt s2 27.50, s1 27.80; eim s2 27.60, s1 27.26, s0 27.17 (R0 33.68).
- 19:28 instance 1 done (R7 s0.1). Means: 10 s pt 23.141 | eim 23.180 | ls 23.208 | cpsat 23.276 | milp 23.398 | lp 23.439;
  60 s pt 23.136 | milp 23.145 | eim 23.157 | ls 23.157 | cpsat 23.165 | lp 23.407; 300 s cpsat 23.117 (optimal) | pt 23.126
  | ls 23.151 | eim 23.155 | lp 23.407 | milp 25.498. Sims (300 s): pt 27.61, eim 27.34, cpsat 27.38 (R0 33.68).
  CAVEAT (to report): exact solvers finish later levels early and the pre-registered nested split only passes unused
  time FORWARD, so at 10/60 s cpsat used 6/15-18 s and milp 3.6/12.8 s of the budget; level 1 (the only hard level)
  gets 2/9 of the budget for every method.
- 20:28 instance 2 done (R7 s0.2): floored at 25.4120 on every level incl. level 1; cpsat, ls, pt, eim all = 25.4120 at
  10/60/300 s (milp too at 60/300 s; 25.676 at 10 s); lp 25.59-25.82; pgreedy 27.461; greedy 34.536. Complete tie.
- 21:39 instance 3 done (R7 s0.3, not floored; floor 21.453). Means: 10 s pt 22.026 | eim 22.080 | ls 22.214 | cpsat 22.229;
  60 s cpsat 21.911 | pt 22.005 | ls 22.018 | eim 22.043; 300 s cpsat 21.777 | milp 21.868 | ls 21.973 | eim 21.995 | pt 22.009.
- BASELINES_READY (Track A, 19:30): peak-blind OPT P100 = R7 33.676/35.277/31.228, R6 30.901/30.616/31.964 -- identical to
  our same-pipeline R0 on all 6 (cross-validation of both pipelines). Wired into q2final.py.
- Interim (3/6 instances): pt <= best classical at 10 s 3/3, 60 s 2/3, 300 s 1/3; pt sims below OPT on 3/3.
- 22:50 instance 4 done (R6 s0.1). Means: 10 s pt 20.661 | eim 20.669 | ls 20.673 | cpsat 20.838; 60 s cpsat 20.488 | ls 20.558
  | eim 20.591 | pt 20.648; 300 s cpsat 20.385 | milp 20.440 | ls 20.534 | eim 20.542 | pt 20.626.
  => Q2 objective criterion is decided as FAIL for both finalists (pt: 60 s has 2 and 300 s 3 instances with Ising >
  best classical, so neither can reach 5/6; eim: 60 s already 3 'no'). Remaining runs complete the tables and Q1.
- 00:11 instance 5 done (R6 s0.2). Means: 10 s pt 22.346 | ls 22.354 | eim 22.406 | cpsat 22.590; 60 s cpsat 22.160 | ls 22.221
  | pt 22.312 | eim 22.314; 300 s cpsat 21.980 | milp 22.069 | ls 22.159 | eim 22.245 | pt 22.320.
- 01:31 instance 6 done (R6 s0.3): 10 s ls 21.550 | pt 21.556 | eim 21.573 | cpsat 21.792; 60 s cpsat 21.375 | ls 21.407 |
  eim 21.494 | pt 21.534; 300 s cpsat 21.206 | milp 21.291 | ls 21.377 | eim 21.432 | pt 21.524.
## B2 held-out DONE (01:31): 288/288 runs ok (1 MILP run 11.03 s at 10 s flagged over-budget, not decisive);
  52/52 held-out sims matched (+6 R0).
- Q2 (F1+PT): <= best classical 5/6 @10 s, 2/6 @60 s, 1/6 @300 s -> objective FAIL; average FAIL (22.511 vs 22.432);
  simulation FAIL (27.063 vs 26.954).  Q2 (F1+EIM): 4/6, 1/6, 1/6 -> FAIL; average FAIL; simulation pass by 0.003.
- Q1 (both): 6/6 below Baleen peak-blind OPT (Track A baselines = our R0); means PT 27.06, EIM 26.95 vs OPT 32.28 -> YES.
- Move shares: sampler 99.4-99.999% of accepted moves. Core audit: 94.5 foreign CPU-s on cores 0-7 over 7 h.
- 01:31 post-hoc dev sensitivity (pt vs cpsat, default split vs level-1 weight 6, 10/60 s, seeds 0-2) started.
- 01:55 sensitivity done (dev, 48 runs): default split 10 s pt 23.183 < cpsat 23.321, 60 s cpsat 23.080 < pt 23.160;
  level-1 weight 6: 10 s pt 23.174 < cpsat 23.355, 60 s cpsat 23.048 < pt 23.163 -> ordering robust to the split.
- 01:55 check_frozen: frozen OK (94 files); leak check (prescribed command): empty. Background loops stopped.
- HiGHS level-overrun guard fired on 5/144 held-out MILP levels (never the best classical cell) -- documented.
## DONE: RESULTS.md written (Q1 = yes for F1+PT and F1+EIM; Q2 = no for both).
