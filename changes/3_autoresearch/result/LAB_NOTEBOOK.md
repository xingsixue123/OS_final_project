# Lab notebook (3_autoresearch, run 20261020_004634)

All numbers come from real runs: dev only unless a test is explicitly registered. Times are local (EDT).

## 2026-10-20 00:46 Round 1 start: orientation
- **State at start:**
  - `work/` was empty; no test spent; `validate.py --integrity-only` clean.
  - The earlier run (20261019_233548) only changed LOOP_STATUS.
- **Read:** contract (`documents/GOOD_RESULT.md`), `RESEARCH.md`, and the results of WP2 dev, WP3, WP8, WP9 and WP10 (plus the PROTOCOL / G1 / SCOPE files of WP10).
- **What the published evidence says (background):**
  1. **The load-adaptive threshold (α = −1) is the robust deployed lever on high-load traces:**
     - WP3 test: A+α −0.96 vs A;
     - WP9 Region5: −1.16 / B+α −1.70;
     - Region1 (low load): no gain, A+α worse than A.
  2. **Ising/F1 labels fail by one catastrophic instance per test** (Region7 s0.5, Region5 s0.5). The peak was a big-offset scan, and the F1-label models stop admitting it.
  3. **WP10's Ising load-bucket table on B's models (TB:pt):**
     - dev 37.54 vs A+α 37.88 / B+α 38.43 (6/8 and 7/8 wins); Region1 test: no gain;
     - PT = CD = exhaustive on 6-bucket tables.
  4. **No day-1 proxy ranks threshold variants well** (E1 concordance 0.61–0.65). A day-1 fit is a candidate generator; dev full sims decide.
- **Contract implications:**
  - Y must beat A, B and the *better* α arm on ≥ ⌈2n/3⌉ instances, by > 2.5 SE_retrain, with no instance worse by > 2.
  - Y must therefore add something on top of the α mechanism without any catastrophe. Label-changing designs carry the catastrophic-scan risk; threshold designs on Baleen's own models do not.
- **Disclosure:** while listing `explore/common/data/tectonic/` I saw the on-disk sizes of every region's trace directory (all regions, including the pool regions). These are file sizes, not outcomes. They are not used for any choice. The pool choice rule will be written before any pool data is built (see later entries).

## 2026-10-20 00:55 Hypothesis H-CLS (scan-aware Ising threshold table)
- **Hypothesis.** The extra deployed gain over the α arms is available in the *big-offset scan* accesses during high load:
  - Baleen's own models do not admit them;
  - X1's Region6 gain came from admitting them;
  - X1's catastrophes came from *not* admitting them.
- **Design.** A threshold table over load bucket × access class (class = end offset > 8 MiB) on Baleen's own models:
  - fitted per retrain on day 1 by an Ising solver (PT over one-hot spins: 2 × 6 cells × 9 grid values; Potts coupling between the classes of one bucket);
  - classical control: coordinate descent on the same energy.
  - It needs an overlay extension, `work/cls_table/SCOPE_AMENDMENT.md` (item 1.2c), and the `G1_v4` gate.
- **Mechanism check (no sims; `work/cls_table/analysis/mech0.py`, `mech0.csv`).** Scope: WP2 retrain 1, the α = −1 run of A and B, 8 dev instances.
  - Big-offset accesses are ~5% of accesses but **9–37% of the simulated peak window's no-cache DT** (Region6 s0 37.5%, s0.2 29%).
  - Their peak-window admission is ≈ 0 for both A+α and B+α. Their median GBM score at high load is 0.01–0.30, against a θ·g of ≈ 0.4–0.56.
  - New-block accesses (all block counts 0) carry 10–30% of peak DT, but their scores are tiny (median 0.04–0.09), so they are out of reach of a multiplier ≥ 0.25.
  - **Decision:** class = end offset > 8 MiB (J = 2).
- **Infrastructure** (`work/cls_table/`; copied from wp10_schedule):
  - `src/cls.py` (driver), `cls_pack.py` (day-1 pack + class), `cls_fit.py` (PT / CD), `emu.py` (class tables), `g1v4.py`;
  - overlay v4 = `overlay_v3` (rebuilt from PATCH_v3.diff, verified identical to WP10's) + `PATCH_v4_delta.diff`.
- **Parity check:** the overlay's `g_item` and the emulator's class multiplier agree on 2,000 random accesses (0 mismatches).
- **First fit** (Region6 s0, B r1): PT and CD reach the same energy. Table: small class [1, 1, 1, 1, 1, 0.5], big class [1.4, 1.4, 0.7, 0.5, 0.5, 0.5]. In-sample day-1 peak 29.16 vs 29.73 for WP10's load-only table (not evidence; the proxy is invalid).
- **Rules:** `result/DEV_RULES.md` R0 was written at 00:56:42 (file time), before the probe (00:56:58) and the screen (01:00:42) were launched. It is the contract rule applied on dev. Its header first carried a guessed time (01:20); that was corrected to the file time at 01:02, before any simulation had finished. The rule text is unchanged.

## 2026-10-20 01:00 Launched (dev only)
- **Probe** PB0.5 / PB0.25 (retrain 1, 8 dev):
  - TB:pt's table, with the big-offset class × c in load buckets ≥ 3;
  - a mechanism check vs WP10's TB:pt r1 (same models, same small-class table). Not a candidate.
- **Screen:** CB:pt, CA:pt (candidates) and CB:cd, CA:cd (controls), retrain 1, 8 dev.
- **G1_v4** (Region7 s0): frozen vs v4, plus v4 == v3 on the α / table / class-identical-rows paths.
- **Dev extra references:** Region5_s0 and Region1_s0 × {A, B, A+α, B+α} × retrains 1–3, trained here.

## 2026-10-20 01:08 Pool-choice rule (written before any pool job, dump or replay exists; no pool data read)
The first test spend goes to the pool whose instances can all be built from the authors' own release rows. A pool is complete when every pool sample has:
- the Baleen Fig 9 TrainCommand / ReproduceCommand row;
- the `20230410_static_pf` RejectX and CoinFlip rows.

If both T1 and T2 are complete, T1 goes first (larger n). If neither is complete, T1 goes first with the missing rows constructed mechanically (sample-start substitution in the same region's commands), disclosed in the protocol. T3 can only be the second spend (contract).

The check reads row *existence* only, from `results_release.csv.gz`, never a metric column, as WP10 did for Region1/2/3. Published background (WP10 PROGRESS): Region2 lacks the Baleen row for s0.2 and the RejectX rows for s0.1/s0.2, so T1 is incomplete.

## 2026-10-20 01:08 Pool check result and T1 prerequisites (no outcome read)
- **Release-row existence (canonical Fig 9 rows; metric columns not printed):**
  - **Region2:** Baleen Fig 9 rows for s0.1, 0.3–0.6 (none for s0.2). RejectX static_pf rows for s0.3–0.6 (none for s0.1/0.2). CoinFlip static_pf rows for s0.1, 0.3–0.6 (none for s0.2).
  - **Region4:** Baleen rows for s0.2–0.6. Its RejectX/CoinFlip rows exist only under experiment `20230412_XX_rerun2`, not `20230410_static_pf`.
  - By the literal 01:08 rule, neither pool is complete, so **T1 (Region2) is the first spend** (if any), with constructed rows.
- **Disclosure:** the Fig 9 Baleen variant label of a trace comes from the authors' published rule `rc_common.best_baleen_prefetch` (lowest mean authors' P100 over the trace's Baleen rows, every sample), exactly as WP9/WP10 used it.
  - Calling it for Region2/3/4 printed only the variant label ("All on Partial Hit" for Region2 and Region4; "ML-Range on ML-When" for Region3). No value was printed.
  - It defines what "Baleen" is on that trace (the paper's Fig 9 configuration); it is not a choice of ours.
- **`jobs_test.json` (T1) built by `work/cls_table/src/make_jobs_t1.py`:**
  - Construction rule: nearest sample of the same policy / variant / experiment with a row, ties to the lower sample; sample-start substitution; the template's eviction age is kept.
  - Baleen s0.2 ← s0.1 (EA 9223.515); RejectX s0.1 ← s0; RejectX s0.2 ← s0.3; CoinFlip s0.2 ← s0.1.
  - The jobs carry no authors' outcome fields.
- **Launched `prep.py dumps`** (frozen code, train lock): `inst_test/fullml_Region2_s0.{1..6}.npz`, for threshold seeding and the day-1 packs. Static replays are blocked in code until TEST_GO.

## 2026-10-20 01:45 Interim (screen running) and plan B
- **Interim retrain-1 screen** (15 evaluations at 01:41, `src/dev_eval.py screen`): no clear signal; the large swings are on volatile instances.
  - PB-0.5 on Region6 s0.1: 43.17 vs WP10 TB:pt r1 38.20 (B+α r1 is 42.82 there).
  - PB-0.25 on Region7 s0.3: 36.02 vs 37.85.
- **Plan B (R2, `src/cls_pool.py`): one *pooled* class table** fitted by PT on the mean energy over 21–24 training-day packs.
  - Motivation: E1 showed no day-1 proxy ranks variants within a retrain, so per-retrain fits mostly fit noise. A pooled fit keeps only structure that repeats across instances and retrains.
  - Dev evaluation is leave-one-instance-out, so the dev estimate is out-of-instance.
  - Pooled tables (base B, class-monotone) look like a steep load step plus a mild class tilt: all-DEV8 PT fit small [2, 1, 1, 0.7, 0.7, 0.25], big [1, 1, 0.7, 0.7, 0.7, 0.25].
  - Mean day-1 peak over the 24 packs: 30.35 vs 30.89 for the neutral table. Pooled PT vs CD energies (`results/pool_solves_dev.csv`): equal on 4 of 9 fits, PT lower on 1, CD lower on 4 (by up to 0.042).
- **Throughput:** about 1,000 s per sim and 14 concurrent, so roughly 22 evaluations per hour. Queued: about 130 evaluations (probe, screens, UB r1–3, extra refs) plus G1_v4.
- **Bug fixes during the run** (logged rows kept):
  - the control-twin race produced one `__FAILED_` row (UB-cdm Region7 s0.1 r2);
  - the PT/CD reuse mapping was generalised to cd→pt, cdm→ptm, Ucdm→Uptm.

## 2026-10-20 02:21 UB:ptm (pooled table) fails the R0 screen gate; queue trimmed
**UB:ptm retrain 1** (leave-one-instance-out pooled table, B models). d = min(A+α, B+α) r1 − X:
| instance | Region7 s0 | Region7 s0.1 | Region7 s0.2 | Region6 s0 | Region6 s0.1 | Region6 s0.3 |
|---|---|---|---|---|---|---|
| UB:ptm | 39.58 | 34.97 | 37.10 | 43.08 | 43.51 | 36.13 |
| d | −0.07 | −0.07 | −0.21 | −0.31 | **−4.52** | +0.14 |

The gate's tail limit (d ≥ −2.0) is already violated whatever Region6 s0.2 gives, so UB:ptm cannot be confirmed.

**Mechanism.** On Region6 s0.1, B's models with any steep load adaptivity collapse:
- B+α r1 42.82 (3-retrain mean 42.73), PB-0.5 43.17, UB 43.51;
- the per-retrain fitted tables chose a *mild* table there ([1.4, 1, 1, 1, 1, 0.7]), giving 38.20 (TB:pt = CB:pt = CB:ptm = CB:cdm, bit-identical, as expected when the fitted class rows coincide with a load-only table).

The same adaptivity appears in WP10's Region1 test tables (published background): 4 of 6 retrain-1 B fits were exactly neutral.

**Lesson (not used to change any rule):** the per-instance day-1 fit is valuable less for the shape it finds than for *switching load adaptivity off* where day 1 shows no benefit. A pooled universal table loses that protection. This reverses my 01:45 plan-B premise.

**Operational:**
- The queue driver was restarted at 02:20 with `queue_dev1b.txt`: queue_dev1 minus UB:ptm r2–3 and UB:cdm (32 evaluations no longer able to affect any decision). 13 partial sims deleted; finished sims are re-used.
- `chain_dev2` was restarted with a refs-driver check matching both queue files.

## 2026-10-20 02:25 T1 protocol (conditional) and chains
- **`work/t1_region2/PROTOCOL.md`:** a conditional pre-registration, committed before the dev finalist exists and before any T1 simulation.
  - Y is FINALIST from `work/cls_table/results/dev_finalist.json`, computed mechanically by `src/chain_dev2.py` (DEV_RULES R0–R2).
  - **No finalist → no TEST_GO and no spend.**
  - TEST_GO is written by `src/chain_test_t1.sh` only if: there is a finalist; G1_v4 passed (both verdicts); and PROTOCOL.md is committed and unchanged since its commit.
- **Pre-commit checks of the paths a test would exercise** (dev data only): `cls_pack.py` + `cls_fit.py` on a model trained here (Region1_s0, B, r1).
  - PT and CD reach the same energy.
  - Table: small class neutral; big-offset class [2, 2, 1, 1, 1, 0.7].
  - PATCH_v4.diff (9 files, `6dc6ef935e6f`) rebuilds the overlay byte-identically (`rebuild_overlay_v4.sh`).
- `.gitignore` now also excludes the overlay copies, `work_v3/`, the G1 dumps, train records, instance links and model/pickle files.
- `validate.py --integrity-only`: clean. `privacy_scrub --check`: clean.
