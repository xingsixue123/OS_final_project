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

## 2026-10-20 02:20 UB:ptm (pooled table) fails the R0 screen gate; queue trimmed
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

## 2026-10-20 02:23 T1 protocol (conditional) and chains
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

## 2026-10-20 02:35 Disclosed change after the protocol commit (`chain_dev2.py`, ordering only)
`src/chain_dev2.py` was edited at 02:35, after commit `96506745`. The edit is ordering only:
- **Before:** the confirmation queue ran each confirmed candidate *and* its classical control before the finalist rule.
- **After:** the candidates run first (Region5_s0 / Region1_s0 r1–3 first, then DEV8 r2–3). The controls' dev confirmation goes to `queue_dev2_controls.txt`, report only, to run after the decision.

Rationale: R0 says the controls are reported, never candidates, so they cannot affect the finalist. Running them first would have delayed the decision by about 2 h. The R0 gate, the finalist rule, the candidate set and PROTOCOL.md are unchanged. The test still runs the finalist's control arm on T1 (protocol §2).

**Screen status at 02:34 (retrain 1):**
| candidate | instances done | mean d | wins | worst d |
|---|---|---|---|---|
| CB:pt | 7/8 | +0.36 | 6 | −0.15 |
| CB:ptm | 4/8 | +0.44 | | |
| CA:pt | 2/8 | −0.40 | | |
| CA:ptm | 1/8 | −0.54 | | |
| UB:ptm | 7/8 | −0.64 | | −4.52 (gate failed) |

## 2026-10-20 02:36 G1_v4 PASS (`work/cls_table/G1_v4.md`)
Every check is bit-identical (all result keys, per-window series, histograms and counters; byte-identical model files):
- RejectX and CoinFlip, frozen vs v4; both also equal phase 1's published runs.
- Pinned Baleen training, frozen vs v4; the models also equal CP1's.
- The Baleen pipeline, and the same models through both simulators.
- α = −1, v3 vs v4; the exact power-law table, v3 vs v4.
- **A class table with identical class rows == the 1.2b table** (P100 39.5715164464613, the same value as G1_v3's table check).

Class-table results now count under the contract §2.

## 2026-10-20 02:47 Screen nearly complete; queue restricted to decision-relevant work
**Retrain-1 screen** (mean d vs the better α arm per instance):
| candidate | instances | mean d | worst d | gate |
|---|---|---|---|---|
| CB:pt | 7/8 | +0.36 | −0.15 | pending |
| CB:ptm | 8/8 | −0.10 | −1.68 | fails |
| CA:pt | 7/8 | −0.16 | −1.13 | fails unless its last instance is large |
| CA:ptm | 3/8 | −0.35 | | |
| UB:ptm | 8/8 | −0.73 | −4.52 | fails |

**Calibration from published data:** WP10's TB:pt (3 dev retrains) under my dev finalist rule:
- passes vs A (+0.97, 6/8 wins, SE 0.16) and vs B (+0.91, 7/8);
- misses vs the best α (A+α) only on margin: +0.34 with 6/8 wins, but 2.5 × SE = 0.37;
- its worst instance is Region7 s0.3 (−1.31), where B's models are poor (B 38.60, B+α 37.61, A+α 36.01).

**Operational:** the queue was restarted at 02:47 (`queue_dev1c.txt`) with only the remaining candidate r1 runs and the Region5_s0 / Region1_s0 references. The report-only controls r1 and probe went to `queue_report.txt`. 14 partial sims were deleted.

**Region1_s0 references so far** (dev): A 27.00 (2 retrains), A+α 26.21 (1). So α helps on this dev sample, unlike on WP10's Region1 test.

## 2026-10-20 02:59 Can the training-day fit choose between A's and B's models? No (published dev data only)
Analysis of WP10's dev ledgers (`solves_dev.csv` + `trials_dev.csv`, 3 retrains × 8 instances), per (instance, retrain):
- An oracle choosing TA:pt or TB:pt per instance would give 37.32, beating A+α on 7/8 instances.
- A training-day selector does not get there:
  - picking the lower fitted energy: mean 37.97, vs A+α −0.10 (4/8 wins);
  - picking the larger fitted day-1 gain: 37.83, vs A+α +0.05 (6/8 wins, worst −1.71);
  - both are worse than always using TB:pt (37.54, +0.34, worst −1.31).

This confirms E1 for model choice too. No new candidate is derived from it.

## 2026-10-20 03:22 R0 screen decision (mechanical, `work/cls_table/results/dev_screen.json`)
| candidate | complete | mean d | worst d | wins /8 | mean P100 | gate |
|---|---|---|---|---|---|---|
| **CB:pt** | yes | **+0.313** | −0.151 | 6 | 37.41 | **PASS** |
| CB:ptm | yes | −0.097 | −1.683 | 4 | 37.82 | fail |
| CA:pt | yes | −0.151 | −1.131 | 4 | 37.87 | fail |
| UB:ptm | yes | −0.732 | −4.516 | 2 | 38.45 | fail |
| CA:ptm | no (Region7 s0.1 r1 unmatched: WR step 34.92 / 37.2 MB/s) | | | | | fail |

(d = min(A+α, B+α) r1 − X r1.)

- **Confirmation (CB:pt only):** Region5_s0 and Region1_s0 retrains 1–3, then DEV8 retrains 2–3 (`queue_dev2.txt`, 22 evaluations). Then the finalist rule (contract §4 on dev, n = 10 if every reference is complete).
- **Reading:** the class-monotone constraint (ptm) did *not* help: CB:ptm < CB:pt. CB:pt's retrain-1 mean (37.41) is close to WP10's TB:pt r1 (37.31), but per instance they differ.
  - **Corrected 03:24:** only 1 of the 8 retrain-1 B tables has identical class rows (Region6 s0.1, bit-identical to TB:pt r1 at 38.2008). An earlier sentence here said "several"; that was wrong.
  - CB:pt r1 − TB:pt r1: Region7 s0.3 −1.36, s0.2 −0.38, Region6 s0.3 −0.15 (CB better); Region6 s0.2 +2.29, Region7 s0.1 +0.19, Region6 s0 +0.11, Region7 s0 +0.03 (CB worse).

## 2026-10-20 03:59 New family "union" (H-UX): Baleen's model OR the Ising peak-label model (DEV_RULES R3)
**Motivation** (published dev/test data only):
- X1 (WP2 Ea-1.0:F1PT, Ising F1 labels + load + α) has the best dev mean of any configuration (37.20 vs A+α 37.88). It wins large on Region6, where peaks are scans (+3.6, +1.4, +2.1, +0.6 vs A+α).
- It loses on Region7: its labels have no zero-value positives, so first-access admission falls (2.8% vs 8.4%).
- On test it failed by catastrophes (Region7 s0.5, Region5 s0.5), where its model did not admit a scan peak that Baleen's model admits (56–69%).

**Hypothesis.** A union "admit iff s_A > θg OR s_X > κθg" keeps Baleen's first-access and scan admissions as a floor (fixing both failure modes) and adds the peak-label model's Region6 admissions.

**Design** (`work/union/`, overlay v5 = v4 + `PATCH_v5_delta.diff`, 2 files; `SCOPE_AMENDMENT.md` 1.2d; G1_v5 running):
- κ = θ_X*/θ_A* from the training day (≈ 0.66–0.68 on the instances checked);
- `XG` gates X to load ≥ the day-1 q75.
- The Ising component is the label selection: the F1 min–max QUBO solved by PT. The classical control is the same F1 solved by CP-SAT.

**Pipeline for non-WP2 instances** (WP9 code, copied; also what a test would use): `prep_day1.py` (frozen day-1 dump) → `labels.py` → X training with `PolicyPeakBaleen4`.
- Region5_s0's day-1 dump is WP9's.
- Region1_s0's was built here (4 s).
- 12 label sets were solved (F1PT / F1CPSAT × seeds 1–3 × 2 instances, all rc = 0). The X models are training in the background.

**Operational:** the union dir's SimSlot now points at `work/cls_table/.sim_slots.d`, so all drivers share one 14-slot cap.

## 2026-10-20 04:24 Union T1 prerequisites (no outcome read)
For a possible union test on T1 (allowed before TEST_GO; nothing below is read for any choice):
- frozen day-1 dumps `work/union/inst_test/day1_Region2_s0.{1..6}.npz` (`src/prep_day1.py --mode test`);
- 72 F1 label sets: F1PT / F1CPSAT × seeds 1–6 × 6 instances, all rc = 0. Seeds 4–6 cover the extra-seed rule for unmatched cells. Their statistics files were not opened.

The union driver gained test mode (TEST_GO required; extra seeds 4–6 for cells with < 3 matched retrains, as WP9/WP10).

## 2026-10-20 04:36 CB:pt fails the finalist rule (anticipated; mechanical file pending), union protocol for T1
**CB:pt under the finalist rule** (21 of 22 confirmation evaluations; the last one is Region7 s0.3 r3, already a loss):
- **Against A+α** (best α on dev, n = 10): 6/10 wins, need 7. Losses on Region7 s0.3 (37.29 vs 36.01), Region6 s0.1 (40.48 vs 38.96: r2 collapsed to 43.36), Region5_s0 (32.62 vs 32.37) and Region1_s0 (26.37 vs 26.23).
- The cls_table chain will write `dev_finalist.json` with FINALIST null. `chain_test_t1` then stops without TEST_GO, and **T1 is not spent**.

**Union screen (retrain 1, 9 of 16 at 04:34)**, d vs the better α arm:
- **XA:F1PT:** Region6 s0 +4.03, s0.1 +4.32, s0.2 +2.20, s0.3 +0.82; Region7 s0.2 +0.24.
- **XG:F1PT:** Region6 s0 +3.93; Region7 s0.1 +0.35, s0.2 +0.21, s0 −0.23.

These are the largest dev effects of the whole project, as hypothesised. Still retrain 1 only.

**`work/t1u_region2/PROTOCOL.md`:** a new conditional pre-registration on T1 for the union family, committed before the union finalist is known; the screen is still running.
- Y is the finalist of `chain_union_dev.py` (R3); the control is its F1CPSAT twin.
- The chain refuses to run if `work/t1_region2/TEST_GO` exists, so T1 can be spent only once.
- All union T1 prerequisites (day-1 dumps, 72 label sets) were built before the commit; none was read.

## 2026-10-20 04:48 cls_table: no finalist (mechanical); R4 extra seeds for the union confirmation
- **`work/cls_table/results/dev_finalist.json`:** FINALIST null.
  - CB:pt is *ineligible*: Region1_s0 r2 ended unmatched (WR 36.14 after 7 sims), so that cell has 2 matched retrains.
  - It would have failed anyway: 6/10 wins vs A+α (need 7).
  - `chain_test_t1` stopped at 04:42:40: `work/t1_region2/CHAIN_DONE`, **no TEST_GO; T1 not spent.**
- **DEV_RULES R4 (04:48)** and `work/t1u_region2/ADDENDUM_R4.md`, committed before any union confirmation simulation: unmatched candidate cells get retrains 4–6, as in the test protocols.
- **Code changes after the union protocol commit, dev only:**
  - `chain_union_dev.py`: the R4 step;
  - `cls.py` / `union.py`: DEV8 retrains above 3 are trained here.
- `union/results/train/` now holds copies of cls_table's A/B train records for Region1_s0/Region5_s0, so the union arm re-uses the same A_k as the reference arm A (paired by retrain).
- All 12 F1-label X models for Region1_s0/Region5_s0 were trained (labels.py + PolicyPeakBaleen4; every log shows `[PB4] call`).

## 2026-10-20 04:56 G1_v5 PASS; union screen: both candidates pass the R0 gate
- **`work/union/G1_v5.md`: PASS on every check.**
  - RejectX / CoinFlip frozen vs v5, pinned training (models byte-identical, equal to CP1's), the pipeline, the same models: all bit-identical.
  - α and class-table paths: v5 == v4.
  - Union with a second model that can never admit (κ = 1e9) == A+α on v4, bit-identical (P100 39.5715164464613).
  - Union of A with itself (κ = 1) == A+α on v4, bit-identical.
- **R0 screen** (`work/union/results/dev_screen.json`, DEV8 r1, d = min(A+α, B+α) − X):
  - XA:F1PT: mean +1.460, worst −0.276, 6/8 wins, mean P100 36.26 (better-α mean 37.72);
  - XG:F1PT: mean +1.072, worst −0.228, 7/8 wins, mean P100 36.65.
  - Both are confirmed: DEV8 r2–3, Region5_s0 / Region1_s0 r1–3, then R4 extra seeds, then the finalist rule. The finalist goes to `chain_test_t1u` (T1).

## 2026-10-20 04:56 Second-spend pool rule (written before any T1 test run or outcome)
If a second test spend happens, it goes to **T2** (Region4 0.2–0.6):
- whatever the T1 outcome;
- with the authors' Fig 9 Baleen rows and the authors' RejectX/CoinFlip rows of experiment `20230412_XX_rerun2` (the only static rows Region4 has).

T3 is used only if T2's prerequisites cannot be built. The configuration for a second spend is chosen on dev only, never from T1 outcomes (contract §3).

## 2026-10-20 04:57 T2 prerequisites started (no outcome read; for a possible second spend)
`work/union_t2/` is a copy of the union code with its own `jobs_test.json` (Region4 s0.2–0.6, `src/make_jobs_t2.py`).
- Rows: Fig 9 "All on Partial Hit" Baleen rows (experiment `20230412_XX_rerun2`) and the authors' RejectX/CoinFlip rows of the same experiment. No constructed rows.
- `src/prep_t2_all.sh` builds the frozen fullml + day-1 dumps and 60 F1 label sets (F1PT/F1CPSAT × seeds 1–6).

Nothing here is simulated or read. A T2 protocol would be a separate pre-registration, committed before any T2 test run.
- 05:04 T2 prerequisites done: fullml + day-1 dumps for Region4 s0.2–0.6, 60 label sets (all rc = 0).

## 2026-10-20 05:19 T2 conditional pre-registration (before any T1 test run)
`work/t2u_region4/PROTOCOL.md` + `work/union_t2/src/chain_test_t2u.sh`.
- **Condition:** if the union dev finalist is tested on T1 and does not pass, the *same* Y (fixed now, before any T1 outcome) is tested on T2 = Region4 0.2–0.6.
- Only the decision to spend depends on T1's pass/fail; nothing about Y does.
- T2 prerequisites were built at 04:57–05:04, none read.

## 2026-10-20 05:41 Union confirmation in progress; mechanism check (dev; partial)
**XA:F1PT vs A+α** (means over the retrains done so far):
- **wins:** Region6 s0 +3.81, s0.1 +2.21, s0.2 +2.43, s0.3 +0.68; Region7 s0.1 +0.82, s0.2 +0.20; Region5_s0 +0.41;
- **losses:** Region7 s0.3 −0.82, Region1_s0 −0.16, Region7 s0 −0.13.

That is 7/10 at the moment, exactly the required count. Large retrain variance: Region6 s0.1 34.66 / 38.84; Region7 s0.3 35.84 / 38.79 / 35.86.

**Mechanism by region** (DEV8, matched rows so far; WP2 rows for A+α and X1):
| region | config | P100 | mean DT | first-access adm | peak-window adm | peak big-offset share |
|---|---|---|---|---|---|---|
| Region6 | A+α | 38.65 | 21.55 | 0.7% | 0.29 | 0.33 |
| Region6 | X1 | 36.73 | 21.72 | 0.4% | 0.41 | 0.10 |
| Region6 | XA:F1PT | 36.72 | 21.54 | 0.5% | 0.42 | 0.10 |
| Region6 | XG:F1PT | 36.58 | 21.76 | 0.6% | 0.40 | 0.13 |
| Region7 | A+α | 37.11 | 21.29 | 8.4% | 0.38 | 0.13 |
| Region7 | X1 | 37.67 | 22.02 | 2.8% | 0.38 | 0.19 |
| Region7 | XA:F1PT | 37.58 | 21.82 | 2.9% | 0.41 | 0.14 |
| Region7 | XG:F1PT | 36.71 | 21.67 | 3.6% | 0.44 | 0.12 |

**Reading (against my 03:59 hypothesis):**
- The Region6 scan gain is reproduced: peaks move off big-offset windows (share 0.10 vs 0.33).
- But the union does **not** restore Baleen's first-access admission on Region7 (2.9% vs 8.4%). Matching the write rate with the extra X admissions raises the shared base θ (≈ 1.2–1.7 vs ≈ 0.9 for A+α), which thins out model A's admissions.
- So XA behaves much like X1 on dev. The "Baleen floor" against unadmitted scan peaks is weaker than designed; whether it suffices on a fresh pool is exactly what a test measures.
- XG (X only at load ≥ day-1 q75) keeps more of A's budget at low load and looks better on Region7 so far (4 instances).

No rule is changed by this reading.

## 2026-10-20 06:01 Round 1 end-state (union confirmation 24/44; finalist pending)
**Per-instance means so far** (dev; best α on n = 10 is A+α):
| instance | A+α | XA:F1PT | XG:F1PT | XA:F1CPSAT (r1) | XG:F1CPSAT (r1) |
|---|---|---|---|---|---|
| Region7 s0 | 39.65 | 39.78 | 39.74 | 39.88 | 39.91 |
| Region7 s0.1 | 35.89 | 34.71 | 34.55 | 34.31 | 34.32 |
| Region7 s0.2 | 36.87 | 36.71 | 36.68 | 36.76 | 36.69 |
| Region7 s0.3 | 36.01 | 36.83 | 35.87 | 39.32 | 39.00 |
| Region6 s0 | 42.90 | 39.33 | 38.84 | 42.73 | 42.45 |
| Region6 s0.1 | 38.96 | 37.40 | 37.86 | 43.69 | 43.13 |
| Region6 s0.2 | 36.30 | 34.47 | 34.03 | 35.46 | 34.45 |
| Region6 s0.3 | 36.43 | 35.75 | 35.60 | 36.09 | 36.18 |
| Region5_s0 | 32.37 | 32.11 | 32.07 | | |
| Region1_s0 | 26.23 | 26.36 | 26.46 | | |

- XA:F1PT currently wins 7/10 vs A+α (the minimum). XG:F1PT has fewer retrains yet.
- **Ising vs classical labels inside the union** (controls are r1 only; report, no claim): the CP-SAT-label union does not get the Region6 s0 / s0.1 gains (42.73 / 43.69 vs 39.33 / 37.40) and is worse on Region7 s0.3. The same F1 formulation, solved by PT, deploys much better here; WP2 saw the same direction for X1 vs Dc+α.
- **Next, automatic:** `chain_union_dev` finishes XG, applies R4 extra seeds and then the finalist rule. `chain_test_t1u` spends T1 only if there is a finalist (and G1_v5 PASS, protocol unchanged). `chain_test_t2u` spends T2 only if the finalist fails T1.

## 2026-10-20 06:27 Union finalist XA:F1PT (mechanical) → T1 spent (TEST_GO 06:26:50)
**`work/union/results/dev_finalist.json`** (DEV_RULES R3 + R0 finalist rule, n = 10 dev instances, best α = A+α; no R4 extra seed was needed since every cell matched):
| config | mean P100 | vs A (wins, mean, SE, worst) | vs B | vs A+α |
|---|---|---|---|---|
| **XA:F1PT** | 35.36 | 10/10, +1.42, 0.19, +0.02 | 9/10, +1.41, 0.19, −0.28 | **7/10, +0.80, 0.18 (2.5 SE = 0.46), −0.82** |
| XG:F1PT | 35.53 | 10/10, +1.25, 0.15, +0.07 | 8/10, +1.24, 0.16, −0.19 | 7/10, +0.63, 0.15, −1.58 |

Both qualify. The tie-break (larger min over R of mean(R − X)) picks XA:F1PT; its control is XA:F1CPSAT.

**T1 test running** (`work/t1u_region2/`):
- TEST_GO = commit `76cf5c8d`, POOL=T1, written by `chain_test_t1u.sh` at 06:26:50 (protocol committed 04:36:45, unchanged).
- Arms A, B, Aa-1.0, Ba-1.0, XA-F1PT, XA-F1CPSAT × retrains 1–3 (108 evaluations, plus extra seeds if unmatched); static replays in parallel.
- `validate.py --integrity-only`: clean, test registered.

**Test spends: 1 of 2.** The second spend (T2, same Y) is pre-registered and runs only if this one fails.

## 2026-10-20 06:30 T1 pipeline check: the RejectX static replays cannot be matched (pipeline diagnosis, no outcome used)
While checking the first T1 minutes for crashes (trainings and sims run normally), the RejectX replay for Region2 s0.2 ended unmatched after 15 sims (WR 2.0, P100 240.6).

**Diagnosis** (frozen code, `admission_policies.construct('rejectx')`):
- RejectX's history window = `ap_probability × num_cache_elems`. Region2's authors' `20230410_static_pf` RejectX rows use a factor of ~1e5, i.e. an effectively unbounded window.
- So the protocol's "bisect the authors' probability" moves nothing: every replay of an instance gives the same WR. Observed: s0.1 21.19, s0.2 2.00, s0.3 36.47 (+2.4%), s0.4 31.68 MB/s.
- WR is set by X = 1 alone. (Region5/Region1/Region6/7 rows used small factors, so the knob worked there; Region4's rows use 0.16–0.32.)

**Consequences, stated before any Y result was read:**
1. The protocol procedure was followed. `static_baselines.csv` will record these RejectX replays as `matched = False`.
2. The protocol's RejectX mean includes s0.2's 240.6, so the contract condition "Y below RejectX" is uninformative on T1. It will be reported as such and not leaned on.
3. A **supplementary, non-protocol** RejectX (the same commands, the window factor bisected in its effective range) will be reported separately, clearly labelled. It does not enter the pass rule. The pass/fail verdict is the protocol's.
4. s0.2 (a constructed row; the authors have no Baleen or RejectX row for it) looks degenerate for RejectX (almost no re-accesses at X = 1). Every arm runs on it as pre-registered.

## 2026-10-20 07:05 T1 CLOSED: spent and FAILED (unevaluable as pre-registered); written before evaluation.json was opened
**Validator findings B1** (red team and integrity/statistics, round 1):
- Region2_s0.2 cannot reach the target write rate for any arm: every row ends at the search floor θ = 1e-4 (admit everything) with WR 11.51 MB/s and P100 189.07.
- Reference arm A is also short of 3 matched retrains on s0.1 and s0.5 after the pre-registered seeds 4–6 (write-rate cliffs).
- The T1 chain finished at 07:03:10. Its `evaluation.json` has no `good_result` (the `missing` branch). The T2 chain stopped at 07:03:24 ("T1 evaluation incomplete (None)").

**Decision, fixed now, fail-closed, before reading `evaluation.json`:**
1. **T1 is spent and FAILED (closed as unevaluable).**
   - Region2_s0.2 stays in the pool.
   - The `matched` rule is not relaxed.
   - No seed beyond 6 is run.
   - T1 is not re-registered or re-spent.
   - No 5-instance or subset reading is ever called a pass.
2. **The T1 report will show every row**, the matched/total table per (arm, instance), and the unmatched static baselines. Any subset summary is labelled descriptive and non-confirmatory.
3. **T2 runs exactly as pre-registered** (`work/t2u_region4/PROTOCOL.md`, `1cda6af`): the same Y = XA-F1PT, control XA-F1CPSAT, the same arms and pool.
   - The only change is the T2 chain's T1 condition: a missing/None `good_result` (with T1 TEST_GO and CHAIN_DONE present) counts as "T1 not passed".
   - This is recorded in `work/t2u_region4/ADDENDUM_T1_UNEVALUABLE.md` and committed before any T2 TEST_GO.
4. **Root cause, disclosed:**
   - The constructed Region2_s0.2 row was not checked for feasibility at the operating point. The authors' release has no s0.2 row at DWPD 7.5 / 366.47 GB for any policy; the s0.2 dumps and day-1 label statistics were much smaller than the others.
   - I noticed s0.2 was degenerate for RejectX (06:30) but did not check whether it was degenerate for every arm.

**Process note (validator N3):** from now on every rule and dated note is committed immediately, times come from `date`, and no dated header is rewritten; corrections are appended.
