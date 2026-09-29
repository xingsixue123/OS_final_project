# Phase 2 plan: making peak-aware admission deployable

**Date:** 2026-09-29. **Owners:** Ching-Hao Chiu (CC), Jie Fu (JF), Sixue Xing (SX).

**Scope:** `changes/SCOPE_v2.md`. **Branch:** `phase2-deployable-peak`, cut from `phase1-reproduce-and-litreview`.

## 1. Where we stand (phase 1, all reproducible from the repo)
| Result | Evidence | Status |
|---|---|---|
| Baleen artifact reproduced | RejectX and CoinFlip bit-exact; Baleen within ±0.6 of the authors' released-metric runs | `0_reproduce/RESULTS.md` |
| **H1 offline:** min-max episode selection lowers the simulated peak | −16% vs Baleen's peak-blind oracle, 6/6 held-out instances (27.0 vs 32.3) | `explore/q2/RESULTS.md` |
| **H2:** Ising vs classical solvers | Ising beats greedy by about 16% on the planned peak. Against the best classical solver it wins only at 10 s; CP-SAT wins at 60–300 s | `explore/q2/RESULTS.md` |
| **H3 deployed:** gain survives distillation into Baleen's GBM | No: retention about 0; worse than Baleen on held-out (2/6 wins) | `explore/q3/RESULTS.md`, `harness_eval/RESULTS.md` |
| Why H3 failed | The GBM has no time or load signal. The only lever it responded to was first-access admission, and that did not generalise; rare scan windows set held-out peaks | same |

**Phase-2 thesis:** the offline gain is real, and it is lost at distillation. Giving the online model the proposal's causal load signal (SCOPE v2) should let part of it survive. We test that with controls that separate the effect of the signal from the effect of the labels.

## 2. Hypotheses (pre-registered in `PROTOCOL_v2.md` before any test-set run)
- **H1′ (breadth):** peak-aware offline selection beats Baleen's peak-blind oracle on at least 80% of instances across 4 traces (Region4–7) × 10 samples, with a mean reduction of 10% or more.
- **H3′ (deployability):** peak-aware labels plus the `load` feature beat **both** Baleen (original features) **and** Baleen plus `load` (the control) on the test set. This is judged at matched write rate with at least 3 retrains, using the same pass rule as phase-1 Q3: ≥4/6 instances, mean improvement > 2 SE, and below RejectX/CoinFlip.
- **H2′ (optional; only if the motivation holds):** at tight time budgets (≤10 s per solve, e.g. labels re-solved periodically), Ising solvers beat the best classical solver. Tested on fresh samples only.

## 3. Instances
- **Dev (tuning allowed):** Region7 and Region6, samples 0, 0.1, 0.2, 0.3. Phase 1 used 0.1–0.3 only to evaluate the old hypotheses, so they are fair to use as dev for the new ones.
- **Test (never used for tuning):** Region7 and Region6, samples 0.4, 0.5, 0.6 (6 instances).
- **Reserve for the final paper:** samples 0.7–0.9, touched once, at the end.
- **H1′ breadth:** Region4 (202110) and Region5 (20230325), samples 0–0.9, offline only. Use them for deployed runs only if the dev results justify it.

## 4. Work packages

### WP0: hygiene and overlay (CC lead, SX review), Sep 30 – Oct 2
1. Cut the branch. Create `2_deployable_peak/{overlay,src,work,results}`, reusing `explore/common/data` (read-only symlink) and the `explore/env` solver env.
2. Copy BCacheSim into `overlay/` and implement the `load` feature group in training (`train_ap.py`) and serving (`sim_features.py` / `collect_features`). Then implement the optional adaptive threshold θ_t = θ·g(load_t) and the optional prefetch-model `load` features. Write `PATCH.diff`.
3. **Gate G1:** with the default settings, the overlay must be bit-exact with the frozen artifact (RejectX, CoinFlip, Baleen labels, model files, P100) on Region7 and Region6 sample 0.
4. **Train/serve parity test:** the `load` values computed in `train_ap` must equal those computed in the simulator for the same accesses, on 10k sampled accesses.

**Exit:** G1 passed, parity passed, `PATCH.diff` reviewed (G3).

### WP1: H1′ breadth, offline (JF), Oct 1 – Oct 8, runs in parallel with WP2
- Build instances for Regions 4–7, samples 0–0.9, from the authors' OPT-AP commands (reusing `explore/common/src`).
- **Methods:** Baleen peak-blind oracle, LP + repair, CP-SAT (300 s), and PT (the phase-1 finalist), each simulated with `--ap opt` at matched write rate.
- **Outputs:** per-instance P100 table, mean reduction, win rate, and where the peak window moves.
- **Cost:** about 40 instances × 4 methods × about 6 simulations ≈ 960 simulations ≈ 6 h at 14 parallel. Solver time: 40 × 300 s × 2 ≈ 7 h on the pinned cores 0–7.

### WP2: 2×2 deployed study on dev (SX lead, CC infra), Oct 3 – Oct 12
Arms, each at matched write rate with at least 3 retrains, on 8 dev instances:

| Arm | Labels | Online model | Purpose |
|---|---|---|---|
| A | Baleen | original features | reference (reproduces phase 1) |
| B | Baleen | + `load` | control: effect of the signal alone |
| C | peak-aware (best of LP/CP-SAT/PT, F1) | original features | phase-1 result (expected ≈ A) |
| D | peak-aware | + `load` | **the hypothesis** |
| D2 | peak-aware | + `load` + hour-of-day | ablation |
| E | peak-aware | + `load` + adaptive threshold / load-aware ML-When | ablation |

Also run the phase-1 label variants (P0/T2/C2) inside arm D, and a label-purity check (can the GBM, given `load`, fit the peak-aware labels on day 1?) before spending simulation time.

- **Cost:** about 6 arms × 8 instances × 3 retrains = 144 deployed evaluations, each about 6 simulations × 5 min, ≈ 5 h at 14 parallel. Training is serialised at about 30 s each.
- **Metrics:** P100, P99, top-5 mean, mean DT, write rate, first-access admission, the retention ratio R, and the peak window's big-offset share (the scan-event signature).

**Exit:** choose at most 3 finalist arms/configurations with a rule written down *before* the last dev retrains finish (as in phase 1).

### WP3: pre-registration and test (SX, all review), Oct 13 – Oct 16
- Write and commit `PROTOCOL_v2.md` (criteria from §2, finalists, seeds, retrain count) **before** any test-set run.
- Run the finalists plus arms A and B, and RejectX/CoinFlip/peak-blind oracle, on the 6 test instances, ≥3 retrains each. Cost ≈ 5 configurations × 6 × 3 = 90 evaluations ≈ 3 h, plus baselines.
- Report pass/fail for each criterion, whatever the outcome.

### WP4: mechanism and attribution (SX, JF), Oct 13 – Oct 20
- Retention R for each arm; the 2×2 interaction (does `load` help peak-aware labels more than Baleen labels?).
- Per-window attribution of the peak window: late admissions, scan events, prefetch-ineffective windows.
- Peak migration from the planned window to the simulated one; how train/serve feature values are distributed.

### WP5 (optional): H2′ tight-budget solver study (JF), Oct 14 – Oct 25
Only if we write down a concrete re-solve latency requirement first. Then pre-register it and test on samples 0.7–0.9 with the phase-1 harness in `explore/q2`.

### WP6: mid-term report and talk (all), prepared by the mid-term date (TBC, after mid-term break)
- **Talk (10–15 min):** the reproduction and its nuances (bit-exact baselines; the Figure 9 metric version), the offline −16% (with the WP1 breadth if ready), the solver comparison, the deployment gap and its mechanism, and the phase-2 design with early WP2 results.
- **Report (PDF):** the same content, following the course template, "done / challenges solved / remaining".

### WP7: full evaluation and paper (all), Nov 2 – Dec 2
If H3′ passes: extend the deployed evaluation to Regions 4/5 and the reserve samples (touched once). Either way, write the paper. Planned outline:
1. Motivation: peak disk-head time drives provisioning.
2. Baleen reproduction, and the Figure 9 metric caveat.
3. Min-max episode selection, as LP and QUBO/Ising.
4. Offline results (H1′).
5. Solver study (H2/H2′).
6. Deployability (H3′), with the 2×2 design and mechanism.
7. Limits.

## 5. Decision gates
| Gate | When | Condition | If it fails |
|---|---|---|---|
| G1 / parity | Oct 2 | overlay bit-exact; train/serve `load` values identical | fix the overlay; no v2 results until it passes |
| Headroom | Oct 8 (WP1) | offline mean reduction ≥ 10% on Regions 4–7 | narrow the claims to the traces where it holds |
| Learnability | Oct 6 (WP2) | with `load`, the GBM fits the peak-aware day-1 labels better than without (label-purity / Bayes-ceiling check) | skip arm D's heavy runs and report that the signal is insufficient |
| Dev signal | Oct 12 | arm D beats both A and B on the dev mean, beyond 2 SE | report a negative H3′ with the mechanism, and pivot the paper to a "contemporary + analysis" framing |
| Test | Oct 16 | PROTOCOL_v2 criteria | report as is |

## 6. Risks and mitigations
- **The `load` feature helps Baleen as much as it helps us** (arm B ≈ D). Then the contribution is "the missing signal", not the labels. Still reportable, and the 2×2 design makes it visible.
- **One training day of hour-of-day** can overfit (only one example per hour). It is kept as an ablation (D2), not the main arm.
- **Scan events dominate held-out peaks.** Track the big-offset share of the peak window; consider reporting P99 and top-5 alongside P100 (both are already logged).
- **Train/serve skew.** Demand-side load only, plus the parity test in WP0.
- **Compute contention.** Keep the phase-1 rules: pinned cores, one training at a time (flock), OMP caps, and time budgets measured on quiet cores.
- **Over-tuning on dev.** Test and reserve samples stay untouched until the pre-registration is committed. Log every trial.

## 7. Process rules (carried over from phase 1)
- **Sandbox and integrity:** sandboxed envs; every Baleen process runs under `bwrap` with a private `/tmp`; leak check and `check_frozen.sh` at every milestone.
- **What gets committed:** code, reports and small result CSVs. Envs, traces, runs and instance/solution files stay out of git (`.gitignore`).
- **Progress reporting:** `PROGRESS.md` is updated at each milestone. Each WP ends with a `RESULTS.md` that reports every outcome, including negative ones.
