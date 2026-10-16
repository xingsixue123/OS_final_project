# Track C (wp8_trackC): deployment-aware Ising objectives — progress log

**Mission (Stage 1, DEV only):** make the Ising labels themselves carry deployed gain. Build and validate a cheap
deployed proxy, implement deployment-aware Ising energies (PT, the q2 F1 solver family), tabulate offline /
learnability / proxy metrics on the 8 dev instances, write `PLAN_C.md` (Stage-2 screen, finalist rule, fresh test).
No full simulation and no artifact `train` run in Stage 1.

**Data split (hard rule):** dev = Region6/Region7 samples 0, 0.1, 0.2, 0.3 only. Nothing on samples >= 0.4 of
Region6/7 is read or computed; `wp3_test/` results/logs/trials are never read. Region5/1-4 deployed: only the
authors' CSV rows are read, to plan Stage 3.

**Sandbox:** `env.sh` (HOME/XDG/TMPDIR/caches inside wp8_trackC, CONDA_REGISTER_ENVS=false, PYTHONNOUSERSITE=1,
PYTHONDONTWRITEBYTECODE=1, <= 4 threads). Every process: `src/run.sh baleen|solver <script>` =
`taskset -c 8-11,20-23 bwrap --dev-bind / / --bind work/systmp/<job> /tmp -- <env python> -B ...`, cwd `work/`
(`work/BCacheSim` -> the reviewed overlay, `work/data` -> explore/common/data, read-only). <= 2 heavy processes.
`.leak_marker` touched 2026-10-05 14:18:00 (before any run).

## Log
- 2026-10-05 14:18 start; leak marker; read RESEARCH, SCOPE_v2, PLAN, RESULTS_dev, PROTOCOL_v2_H3, Q3_FORMULATION,
  q3/RESULTS. Copied wp2_deployed/src (emu, learn, labels, pb4_policy, wpcommon, wp2, q2lib, q3lib) and the dev
  simfeat caches. WP2's 196 trained-model sets are on disk (`wp2_deployed/work/tmp/<train_key>/...`), read-only.
- 14:25 pre-registration below written BEFORE any proxy value was computed.
- 14:27-14:45 `src/pm_points.py`: WP2's 196 trained admission models scored on the fullml instances; emulated
  measures at all 1,075 WP2 simulated thresholds -> `results/pm_points.csv` (calibration data). Sanity: the copied
  emulator reproduces WP2's recorded emu WR and k0_adm exactly (e.g. A Region7 s0 r1: 64.692 / 0.0711).
- 14:30-14:40 design exploration (offline only, seed 1; logged as stage `explore` in `results/ledger_labels.csv`):
  F1PT4 reproduces WP2's F1PT on Region7 s0 (day-1 peak 22.14 vs 22.14, J 0.468 vs 0.465). Anchor grid chosen from
  offline Jaccard only: ANC3/10/30 -> J 0.85/0.92/0.98 (Region7 s0), peaks 22.5/23.3/25.0 (F1 22.1, Baleen 28.9).
  Top-k: TK3/TK10/TK30 ~= F1 on day 1 (the min-max optimum is a plateau of >= 30 windows, so CVaR_k = max for
  k <= 30); TK72 (half-day CVaR) differs (J 0.67, peak 23.7 on Region6 s0) -> table keeps TK10 and TK72.
  Student: STU3/10/30 R1 on Region7 s0 (labels 1518/1371/1292, peak 22.18/22.33/22.58).
- 14:45 `src/calib.py` (pre-registered rule, (theta, sim WR) pairs only): LOCO RMSE of log sim WR on matched sims:
  acc 0.0448, ep 0.0466, mix 0.0478 -> **acc selected** (`results/wr_calibration.json`).
- 14:43 phase A label solves running (`src/run_labels_c.py --phase A`, 1 process, 4 numba threads).
- 14:47 PL validation (`pl_eval.py --what wp2`) then PM (`--what pm`) running (1 process, LightGBM 4 threads).

## PRE-REGISTRATION: proxy validation (written 2026-10-05 14:25, before computing any proxy value)

### What is validated
- **PL (label-level proxy; the screening proxy).** For (instance i, configuration c, k = 1..3): labels (Baleen = the
  day-1 instance's Baleen prefix within B; design d = WP2 label file `<i>_<d>_s<k>.npz`) -> LightGBM refit with the
  artifact's GBAdmissionTrainer parameters (binary, 63 leaves, lr 0.005, ff/bf 0.9, bagging_freq 5, min_data_in_leaf
  50, min_sum_hessian 5, <= 2000 rounds, early stop 25 on a 30% block split seeded k, LightGBM seed k,
  num_threads 4) on the trainer's day-1 rows (k < 15) of `day1_<i>.npz`, features = the configuration's subset
  (18 or 18 + load) -> scores of every GET access of `fullml_<i>.npz` (emu.InstEmu) -> base threshold theta chosen by
  the write-rate calibration below (with the configuration's alpha in the emulated admission rule
  g > theta * clip((load_10m/20)^alpha, 0.25, 4), theta search (0, 4] for alpha arms, (0, 1) otherwise) ->
  `q3lib.emulate_loads` -> emulated P100 = max over windows >= 144 (util %). Configuration value = mean over k.
- **PM (model-level proxy; diagnostic only).** Identical, but with WP2's actual trained admission model of retrain k
  (no refit). Tells whether a PL failure comes from the refit or from the emulation itself.

### Write-rate calibration (uses only WP2's (theta, simulated WR) pairs; never a simulated P100)
For every WP2 simulation (all 1,075 sims of all trials, matched or not) the real model's emulated write measures at
that sim's theta are computed: `ep` (whole-episode chunk span at admission, the existing emulator), `acc` (chunk
span accessed from the admitting access on). Per instance, log(sim WR) is regressed on log(emu measure) (one
measure, or both = `mix`). The calibration used by PL/PM = the variant {ep, acc, mix} with the smallest
leave-one-configuration-out RMSE of log sim WR on the matched sims, pooled over the 8 instances. The proxy's theta
is where the calibrated WR equals 35.599 MB/s.

### Configurations (WP2 dev configs with >= 3 matched retrains on all 8 instances; 13)
A, B, A+alpha (Aa-1.0 U Ax-1.0), B+alpha (Ba-1.0 U Bx-1.0), B+alpha0.5 (Ba-0.5 U Bx-0.5), C:F1PT, C:F1EIM, D:F1PT,
D:F1EIM, Dc = D:F1CPSAT, X1 = Ea-1.0:F1PT, X2 = Ea-0.5:F1PT, Ec = Ea-1.0:F1CPSAT (U Ex-1.0). Sim value = WP2's mean
P100 over matched retrains (trials.csv). 1-retrain screens (D:P0, D:T2, Ea-1.0:F1EIM) reported, not in the criterion.

### Criterion (PL with the selected calibration; all must hold for "PROXY VALID")
- **C1 (ranking).** Per instance, Spearman rho_i between PL and sim over the 13 configurations:
  median_i rho_i >= 0.5 AND rho_i > 0 on >= 6/8 instances.
- **C2 (key contrasts, dev means over 8 instances).** PL reproduces the SIGN of X1 - A, X1 - (A+alpha) and
  D:F1PT - A (sim: -1.30, -0.68, -0.13).
- **C3 (per-instance X1 vs A+alpha).** On the instances where the sim |X1 - (A+alpha)| >= 0.5, PL has the same sign
  on >= 5 of them (7 such instances on dev).
Reported regardless: the same for PM; pooled within-instance (instance-demeaned) Pearson/Spearman over all
(instance, config) cells; proxy k0 admission vs WP2's `k0_adm`.

### Consequence
- PROXY VALID -> Stage 2 may use PL to pre-screen designs (a design is dropped only if its PL is worse than X1's PL
  by more than the proxy's typical within-instance error); every finalist decision still uses full sims.
- PROXY NOT VALID -> Stage 2 screens every short-listed config with full sims; PL is reported only as a diagnostic.
  The criterion is not changed after seeing the numbers.

## Log (continued)
- 2026-10-05 ~15:05 the session ended. By then: phases A-E label solves done, PL validation (336 rows) and PM (336
  rows) done (ledger complete, 672 unique keys; no partial rows). Detail: the PL validation process was restarted
  once at ~14:55 to use a faster but numerically identical `acc` measure (checked equal on 3 thresholds); an
  accidental `pkill` pattern also killed the launching shell; no row was lost or duplicated.
- 2026-10-16 resumed (coordinator: H3' driver exited; CPUs 8-23, <= 8 threads). `env.sh` updated accordingly.
  `validate.py` run on the complete ledger with the UNCHANGED pre-registered criterion -> **PROXY NOT VALID**
  (results/proxy_validation.md): PL median per-instance Spearman 0.49 (< 0.5; rho > 0 on 8/8) -> C1 FAIL; C2 PASS
  (X1-A -0.66 vs sim -1.30; X1-(A+a) -0.75 vs -0.68; D:F1PT-A -0.08 vs -0.13); C3 PASS (6/7). PM (real WP2 models,
  calibrated theta): median 0.37 -> FAIL; PM at the simulated theta: 0.36, C2 FAIL. The emulated first-access
  admission tracks WP2's model-based k0 (Pearson 0.98, 128 cells).
- Learnability (learn.py protocol, seed 1) for Baleen + the 10 designs; PL for the 10 designs (alpha none / -1,
  seeds 1-3, 480 rows); CP-SAT anchored control ANC10CP (24 solves). Stage-1 table: `results/stage1_table.md`.
- Solver comparison on the anchored energy (peak + field, util %, 24 instance x seed cells, 10 s each):
  PT (ANC10) 13.55 vs CP-SAT (ANC10CP) 14.31 mean; PT lower on 11/24 cells (CP-SAT never proved optimality:
  FEASIBLE; its mean is hurt by a few bad cells).
- PLAN_C.md written (Stage-2 screen, FINALIST RULE, Stage-3 Region5 fresh test, short-list E8:ANC3, E8:ANC10,
  E8:STU10R1). Integrity: see "Integrity" below.

## Integrity (2026-10-16)
- `bash 0_reproduce/check_frozen.sh`: `frozen OK (94 files)`.
- Files under 0_reproduce/ or 1_literature_review/ newer than `.leak_marker`: 148, ALL dated 2026-10-10
  (01:06 and 19:13) and all `__pycache__/*.cpython-312.pyc` / `*.cpython-313.pyc` in the two envs' site-packages
  (lightgbm, pytz, defusedxml; optuna, colorlog). Not written by Track C: this track was not running on 2026-10-10
  (session down 10-05 ~15:05 to 10-16), every Track C process used the envs' own python 3.11 with `-B` and
  PYTHONDONTWRITEBYTECODE=1, and no cpython-311 file is among them. Left in place (not ours to delete); reported
  to the coordinator.
- `tools/privacy_scrub.py --check`: clean. No `__pycache__` in wp8_trackC or the overlay. No git writes.
- Data split: only Region6/7 samples 0-0.3 were loaded (asserted in proxy.py/pl_eval.py/labels_c.py); wp3_test
  was never read; Region5: only availability of the authors' rows was printed (no P100 values).

## RESUME
Stage 1 is COMPLETE. Nothing is running. To regenerate the reports (all resumable / idempotent):
```
cd changes/2_deployable_peak/wp8_trackC && source env.sh
src/run.sh baleen ../src/validate.py        # proxy validation report
src/run.sh baleen ../src/table.py           # Stage-1 table
# re-running drivers skips finished work:
python3 -B src/run_labels_c.py --phase A B C D E F
src/run.sh baleen ../src/pl_eval.py --what wp2 ; src/run.sh baleen ../src/pl_eval.py --what pm
src/run.sh baleen ../src/pl_eval.py --what c --designs F1PT4 ANC3 ANC10 ANC30 TK10 TK72 ANC10TK10 STU10R1 STU10R2 STU30R1
```
Next: Stage 2 per PLAN_C.md (needs coordinator go-ahead; full sims + trainings).
