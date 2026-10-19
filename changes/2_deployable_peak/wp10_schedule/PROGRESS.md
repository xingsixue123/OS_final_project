# WP10 (Track E): Ising-fitted admission-threshold schedule, progress log

Brief: keep Ising/QUBO central but put it in the **admission-threshold schedule**. A piecewise-constant multiplier table m_b over K load buckets (one-hot spins over a grid) is chosen by an Ising solver (PT) on the TRAINING window (day 1) and deployed with Baleen's own trained models (arms A / B). Hard rules: see the task brief (sandbox, train lock, ≤ 14 sims, dev = Region6/7 s0–0.3 only, reserve 0.7–0.9 never touched, no git writes except the E4 protocol commit).

## Log
(Clock times corrected at 18:00 from file timestamps; the first version of this log carried estimated times. The order of events is unchanged: each pre-registration was written before the code that computes its outcome existed or ran.)


### 2026-10-19 17:03 E0 start
- `.leak_marker` created 17:03:33. `env.sh` (HOME/XDG/TMPDIR inside wp10, `CONDA_REGISTER_ENVS=false`, `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`). Every Baleen/solver process: `taskset -c 0-23 bwrap --dev-bind / / --bind <private job tmp> /tmp -- <env python> -B` (`src/sbx.sh` for drivers; `wpcommon.run_logged` for each train/sim). Trains under `flock 2_deployable_peak/.train.lock`; sims through wp10's own `SimSlot` pool (cap 14 while `TIMING_IDLE` exists).
- Overlay v3: `PATCH_v3.diff` (9 files, +259/−6) = `PATCH.diff` + `PATCH_v3_delta.diff` (4 files, +43/−1). `rebuild_overlay.sh` → `overlay/BCacheSim` (verified identical to the development copy). `wp0_overlay/` untouched.
- `SCOPE_v2_1b.md` written.
- **E4 region check (release CSV, not outcomes):** Region2 (201910) has **no Baleen row for s0.2** and **no RejectX row for s0.1/s0.2** → cannot be used. **Region1 (201910)** has Baleen Fig 9 rows for s0–0.9 (variant "ML-Range on Partial Hit", experiment `20230421_alltraces_pfalways`, as Region5) and RejectX/CoinFlip `20230410_static_pf` rows for every sample → **E4 region = Region1** (Region3 lacks s0.4–0.6). Region1 has never been run by this project (WP1 used Regions 4–7).
- G1_v3 driver launched 17:12 (`src/g1v3.py`). First launch: a race between two threads that shared the frozen static training (second thread found the files already present → no "Filenames generated" block → RuntimeError). Fixed with a per-tag lock; the already-launched sims were left to finish (deterministic, re-used by the relaunch).

### 2026-10-19 ≈17:12 E1 PRE-REGISTRATION (written before any proxy value is computed)

**Question.** Does a cheap replay of "trained model + threshold schedule → per-window load" rank threshold variants of the SAME trained model the way full simulations do?

**Data (dev only).** WP2 retrains (`wp2_deployed/trials.csv`, `results/train/*.json`, model files read-only, copied into `wp10/work/models/`) that have ≥ 2 matched threshold variants of the same models:
- A (24 retrains): none, α = −1 (`Aa-1.0` ∪ `Ax-1.0`);
- B (24): none, α = −1 (`Ba-1.0` ∪ `Bx-1.0`), α = −0.5 (`Ba-0.5` ∪ `Bx-0.5`);
- D:F1PT (24): none, α = −1 (`Ea-1.0`), α = −0.5 (`Ea-0.5`);
- D:F1CPSAT (24): none, α = −1 (`Ea-1.0` ∪ `Ex-1.0`); D:F1EIM (8, r1): none, α = −1.
- α = −2 is excluded (all 8 unmatched). Only matched rows are used. Sim value = WP2 P100 of that variant.

**Proxies** (all use the WP2 emulator: simulator-style features of every GET access of `fullml_<inst>.npz`, the retrain's admission GBM scores, first-admission emulation `q3lib.first_admit` + `emulate_loads`; multiplier g at each access from its causal `load_10m`):
- **P1 (deployable; the one E2 would use):** day-1 only. Admission allowed only for accesses in windows 0–143. Write budget W1 = the day-1 emulated chunks written by the plain model (g ≡ 1) at θ_c, where θ_c makes the day-1 emulated write rate (`TARGET·wch/(B·f1)`, f1 = day-1 share of the trace duration) equal the regional seeding map's emulated target (WP2 `WRMAP0[(region, kind)]`, fixed phase-1 constants). Each variant's θ is bisected so its day-1 written chunks equal W1 (hard repair). P1 = max over day-1 windows of the emulated load (util %).
- **P2 (diagnostic only, NOT deployable):** the same on the full trace (budget from θ_c on the full emulated WR), P2 = max over windows ≥ 144.
- **P3 (deployable in principle; delta proxy):** P3 = max over day-1 windows of [S_w + (L_w(variant) − L_w(none))·US], where S_w is the simulator's own day-1 per-window used load under the plain variant (on dev: the first 144 windows of WP2's matched none-variant sim; in deployment this would be a day-1 replay at θ_c). L from P1's emulation.

**Criterion (applied identically to P1, P2, P3; computed once).**
- **C1 (within-retrain ranking):** over all within-retrain variant pairs whose simulated P100 differ by ≥ 0.25 util-pts, the share with sign(proxy Δ) = sign(sim Δ) must be ≥ 0.70, and a one-sided sign test vs 0.5 must give p < 0.05.
- **C2 (sign of α = −1 minus none, Baleen models):** cells = {A, B} × 8 dev instances (mean over the cell's matched retrains). (i) The mean over the 16 cells of proxy Δ = P(α=−1) − P(none) has the same sign as that of sim Δ; and (ii) the signs agree on ≥ 70% of the cells with |sim Δ| ≥ 0.25.
- **VALID iff C1 and C2 pass.** E2 uses P1 if valid; else P3 if valid; P2 can never be used for fitting (it reads post-training windows). **If neither P1 nor P3 is valid, that is reported plainly**, E2 still fits tables with P1 (the only training-window proxy available without sims) as a *candidate generator*, and the E3 full-simulation screen is the only evidence (the brief's "use full sims in the dev screen").
- Also reported, no pass/fail: per-instance Spearman over all variants of all retrains of that instance; pooled Pearson; the cell table.

### 2026-10-19 17:25 E1 RESULT: NO PROXY IS VALID (criterion applied unchanged)
`src/e1_proxy.py` → `results/e1_cells.csv`, `results/proxy_validation_e1.md`, `results/e1_verdict.json`. 120 WP2 retrains, 272 matched variant rows, 126 within-retrain pairs with |sim Δ| ≥ 0.25.

| proxy | C1 concordance (≥ 0.70) | C2 mean sign / cell agreement (≥ 70%) | verdict |
|---|---|---|---|
| P1 emulator, day 1 (deployable) | 0.63 (p = 0.003) FAIL | same sign (−0.40 vs −0.32); 6/9 FAIL | **NOT VALID** |
| P2 emulator, full trace (diagnostic) | 0.65 FAIL | same sign; 6/9 FAIL | NOT VALID |
| P3 delta proxy, day 1 (sim anchor) | 0.61 FAIL | same sign; 7/9 PASS | NOT VALID |

- Before the emulator ran, a sanity check matched it exactly to `q3lib.first_admit/emulate_loads` (max |ΔL| = 0, the same written chunks). Its windows are aligned with the simulator's (nocache rel. diff 3e-12; util scale = US).
- **Post-hoc diagnostic (not pre-registered; `src/e1_diag.py`, `results/e1_diag/`):** P4 = the SIMULATOR's own day-1 peak of each variant's run (same run, same θ as its P100). Its C1 concordance is also only **0.61** (C2 8/9). So even a perfect training-window replay ranks threshold variants for days 2–7 no better than the emulator. The limit is the day-1 → later-days shift, not the emulator's fidelity.
- **Consequence (pre-registered branch):** nothing validates. E2 fits tables with P1 as a *candidate generator* only. The E3 full-simulation screen is the only evidence.

### 2026-10-19 ≈17:32 E2 CONFIGURATION (fixed before any solve) and E3 FINALIST RULE (fixed before any E3 sim)

**E2 fit (training window only).** Pack per (dev instance, arm A/B, WP2 retrain k = 1, 2, 3) (`src/e2_pack.py`): day-1 scores of that retrain's admission GBM, causal `load_10m`, day-1 no-cache loads, budget W1 (P1 definition), K = 6 load buckets with edges at the day-1 access-level quantiles (0.25, 0.5, 0.75, 0.9, 0.97) of `load_10m`.
- **Spins:** one-hot x[b, v] over grid G = {0.25, 0.35, 0.5, 0.7, 1, 1.4, 2, 2.8, 4} per bucket (54 spins).
- **Hamiltonian:** H = peak_day1 + 0.1·top5_day1 (replayed, util %) + 0.02·Σ_b |log2 m_b| (local fields; prior towards 1) + 50·#(adjacent buckets with m increasing in load) (couplings; monotone non-increasing shape, like the power law).
- **Write budget = hard repair:** each state's θ is set exactly so that the day-1 written chunks are ≤ W1.
- **Solvers** (`src/e2_solve.py`, solver env, one numba replay kernel shared by all):
  - `pt` = **Ising, parallel tempering**: 16 replicas, geometric T ∈ [0.005, 1] util-pts, neighbour swaps, one-hot-preserving moves, **10 s**, seed = k.
  - `cd` = **classical** greedy coordinate descent + perturbation restarts, **10 s**, seed = k.
  - `ex` = classical exact reference: all 3003 monotone tables.
  - Ledger: `results/solves_dev.csv`.
- **Deployment:** table → `--ap-load-adapt-table`, with the SAME WP2 retrain's models (A: `meta+block+chunk`; B: `+load`). Base θ converged by full sims to 35.599 ± 1%, search range (0, 4] (as the α arms), at most 7 sims, WP2/WP3/WP9 convergence code.
- **Time-of-day cells are not used:** one training day gives one example per hour, and WP2's `+tod` arm failed for that reason.

**E3 configurations (screen = WP2 retrain 1 × 8 dev instances):**
- `TA:pt`, `TB:pt`: the Ising candidates.
- `TA:cd`, `TB:cd`: the classical controls.
- If a control's table is identical to its PT table on an instance, the deterministic PT result is reused and flagged (no duplicate sim).

**FINALIST RULE (written ≈17:32, before any E2 solve and any E3 sim; applied unchanged):**
- References are WP2's dev trials, reused, paired per instance: A+α = `Aa-1.0` ∪ `Ax-1.0` and B+α = `Ba-1.0` ∪ `Bx-1.0`, matched rows.
- For a config X, per instance i: d_A,i = (A+α)_i − X_i and d_B,i = (B+α)_i − X_i (positive = X better).
- **Candidates:** only the Ising configs `TA:pt`, `TB:pt`. The `cd` controls are reported but cannot become finalists.
- **Screen gate (rep 1, paired by retrain: X r1 vs A+α r1 and B+α r1):** S1 = mean_i min(d_A,i, d_B,i) > 0. At most 2 configs pass to confirmation, the 2 largest S1. Confirmation = retrains 2 and 3 (WP2 retrains 2, 3; tables fitted on their own packs). The `cd` control of a confirmed arm also gets retrains 2 and 3, for the Ising-vs-classical comparison.
- **Finalist (3 matched retrains per instance; per-instance means vs WP2's 3-retrain means of A+α and B+α).** X qualifies iff all of the following hold:
  - (a) S3 = mean_i min(d_A,i, d_B,i) > 0. This is "mean improvement > 0 over the worse of the two" taken per instance; it implies mean improvement > 0 vs each.
  - (b) d_A,i > 0 on ≥ 5/8 instances AND d_B,i > 0 on ≥ 5/8.
  - (c) For each region (Region6, Region7), mean_i∈region (X_i − (B+α)_i) ≤ 0.5.
- The finalist is the qualifying config with the larger S3. Its classical control (same arm, `cd`) goes to E4.
- **If no config passes the screen or qualifies: NO FINALIST.** Write `RESULTS_dev.md` and stop (no E4).

### 2026-10-19 17:45 E2 done (48 packs = 8 dev instances × A/B × WP2 retrains 1–3; ledger `results/solves_dev.csv`, 144 solves)
- **Ising PT (10 s) reaches the exhaustive monotone optimum on 48/48 packs.** Classical CD (10 s) reaches it on 46/48 (max gap 0.006 in H). PT is better on 2, CD on 0, tie on 46. About 15k distinct energy evaluations per 10 s solve for both; exhaustive enumeration takes 1.5–2.3 s (3003 tables).
- PT and CD tables are scale-equivalent (same admission family, θ absorbs the scale) on 46/48 packs. So most `cd` control evaluations in E3 re-use the `pt` result (flagged).
- **In-sample day-1 replayed peak** (mean of 48): neutral table 31.28, power law (α = −1 projected on the grid) 31.09, **fitted table 29.75 (−1.5)**. Tables are mostly steep steps: m ≈ 2–4 at low load and 0.25–0.7 at the top bucket. On 3 packs the optimum is the neutral table.
- The proxy is NOT valid (E1). These in-sample gains are not evidence. E3 decides.

### 2026-10-19 17:50 E3 screen launched
`src/wp10.py --mode dev --arms TA:pt TB:pt TA:cd TB:cd --reps 1` (16 sims at a time max via SimSlot cap 14). Finalist rule above, unchanged.

### 2026-10-19 18:05 Integrity at the end of E0–E2
- `bash changes/0_reproduce/check_frozen.sh`: **frozen OK (94 files)**.
- Files under `0_reproduce/` and `1_literature_review/` newer than `.leak_marker`: **0**.
- The known foreign `cpython-312/313 .pyc` files are 125, all dated 2026-10-10, in the two envs' `site-packages/__pycache__`. They are listed and left in place; they are older than the marker.
- Disclosed: two short import checks (`numba`/`lightgbm` availability in the two envs) ran outside bwrap at 17:15. They were read-only, with `PYTHONDONTWRITEBYTECODE=1` from `env.sh`. Every other process ran sandboxed.
- E4 preparation, no outcomes involved: `jobs_test.json` (Region1 s0–0.6 from the release CSV, `src/make_jobs_test.py`) and the `fullml` instance dumps `inst/fullml_Region1_s{0,…,0.6}.npz` (frozen code, `src/prep.py dumps`; trains under the lock). No Region1 simulation has run. Static replays of test samples are blocked in code until `TEST_GO` exists.

### 2026-10-19 18:25 E3 screen result (rep 1; `src/e3_eval.py` → `results/e3_screen.csv`, `results/e3_tables.md`)
- 32 evaluations, all matched, 0 failed. 16 real (2 sims each); 16 `cd` controls re-used the `pt` result (scale-equivalent tables on all 16 rep-1 packs).
- S1 = mean_i min(A+α r1 − X, B+α r1 − X): **TB:pt +0.41** (6/8 wins vs A+α r1 and vs B+α r1; mean 37.31) and **TA:pt +0.10** (5/8, 4/8; mean 37.62).
  - References on the same retrains: A+α r1 37.86, B+α r1 38.40.
  - The `cd` controls are identical (same tables).
- **Both Ising candidates pass the screen gate (S1 > 0) → confirmation with WP2 retrains 2 and 3** for TA:pt, TB:pt and their `cd` controls (rule unchanged).

### 2026-10-19 19:25 E3 confirmation finished (19:20), NOT yet evaluated; PROTOCOL_v2_H5 (conditional) written
- Confirmation (WP2 retrains 2, 3 for TA/TB pt + cd): 64 rows, 0 failed (`trials_dev.csv`). Per the coordinator, the protocol is committed BEFORE `e3_eval.py` is run on these rows; their P100s have not been inspected.
- Region1 s0 dry run (A, TA/TB pt/cd; 1 retrain) is done; the pipeline works (§2 of the protocol).
- **Test region = Region1, not Region2:** Region2's release CSV has no Baleen Fig 9 row for s0.2 and no RejectX row for s0.1/s0.2. Region1 has all rows (same Fig 9 variant as Region5). Region3 lacks s0.4–0.6.
- `src/e3_eval.py` gained the deterministic tie-break and the `results/finalist.json` output only (rule unchanged). `src/chain.sh` runs the rest detached (protocol §8).

### 2026-10-19 19:23 Protocol committed (`2738cba`, pushed); chain launched (pid 1118179); E3 FINALIST = TB-pt
- `e3_eval.py` ran (inside the chain) on the complete 3-retrain dev data. The rule was applied unchanged:
  - **TB:pt qualifies:** S3 = +0.19; wins 6/8 vs A+α and 7/8 vs B+α; region mean (X − B+α) is R6 −1.36 and R7 −0.42. Dev mean 37.54, vs A+α 37.88 and B+α 38.43.
  - **TA:pt fails:** S3 = −0.30, 4/8 and 4/8.
  - Control TB:cd: its tables are scale-equivalent to TB:pt on 23/24 dev retrains, so its dev results are identical.
- The chain created `TEST_GO`. It is running the static replays, the dry-run resume and the test (`--arms A B Aa Ba TB:pt TB:cd --reps 1 2 3`, 108 evaluations), then `evaluate_test.py --finalist TB-pt`, integrity, and `results/CHAIN_DONE`. Log: `logs/chain.out`.

## RESUME
```
# Detached chain (E3 eval -> finalist -> E4 test -> evaluation -> integrity -> results/CHAIN_DONE); idempotent:
cd changes/2_deployable_peak/wp10_schedule && setsid nohup bash src/chain.sh >> logs/chain.out 2>&1 < /dev/null &
cd changes/2_deployable_peak/wp10_schedule && source env.sh
# E3 screen / confirmation (resumable; re-uses finished sims; trials_dev.csv is the ledger):
setsid nohup src/sbx.sh src/wp10.py --mode dev --arms TA:pt TB:pt TA:cd TB:cd --reps 1 -j 16 > logs/e3_screen.out 2>&1 < /dev/null &
setsid nohup src/sbx.sh src/wp10.py --mode dev --arms TA:pt TB:pt TA:cd TB:cd --reps 2 3 -j 16 > logs/e3_confirm.out 2>&1 < /dev/null &
# G1_v3 (re-uses finished sims):
setsid nohup src/sbx.sh src/g1v3.py > logs/g1v3.out 2>&1 < /dev/null &
```
