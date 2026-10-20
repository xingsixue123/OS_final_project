# Integrity, statistics and code validator: run 20261020_004634, round 2

**Reviewer role.** An independent check of the sandbox, the code that produced the numbers, and the statistics. I recomputed every decision number from raw files: result `.lzma` files, sim and train logs, ledgers, label files and the worker transcript. I did not rely on the worker's summaries, on `eval_test.py`, or on `validate.py`'s claim path.

**What I wrote.** I edited no worker file and made no git writes. Running `python3 code/validate.py --integrity-only`, as instructed, rewrote `result/deterministic_validation.json`. The result was `problems: []` and `integrity_ok: true`. Integrity-only mode drops the loop's "no claim file yet" note, so I copied back the file as it was before my run. Its JSON is identical to the loop's own round-2 output (`output/auto_runs/20261020_004634/validation_round_2.log`). My scratch scripts are in the session scratchpad only.

**State reviewed** (2026-10-20, 11:34–11:42 EDT):
- HEAD is `e964491`.
- No claim file exists, and `result/STOP_EXHAUSTED` is written.
- No 3_autoresearch process is running.
- Two tests are spent:
  - T1: `work/t1u_region2`, TEST_GO 06:26:50 on `76cf5c8d`.
  - T2: `work/t2u_region4`, TEST_GO 07:05:04 on `1cda6af`. CHAIN_DONE was written at 10:00:33.
- Every ledger in the working tree equals its committed snapshot.

**Verdict:**
- **The negative result is correct and fully reproducible.** T2 fails the pass rule against the best α arm, and T1 cannot be evaluated as pre-registered. The budget is 2 of 2.
- Both round-1 blockers are resolved.
- Everything I checked is correct:
  - sandbox, train lock and scope;
  - arm definitions, threshold convergence and the P100 metric;
  - the T2 frozen static replays;
  - overlay identity;
  - the Ising and control label provenance;
  - the handling of the incident rows;
  - every FINAL_REPORT number.
- **No blocking findings.** Five non-blocking findings concern wording, disclosure and coordinator items.

## 0. Status of round-1 findings
| round-1 finding | evidence in round 2 | status |
|---|---|---|
| **B1:** T1 unevaluable; the T2 chain halts | Fail-closed entry `539f39e` (07:04:06). Worker transcript call #1 listed `results_test/` but did not open `evaluation.json`. The T1 evaluation holds only `missing`, so it has no outcome to read. `ADDENDUM_T1_UNEVALUABLE.md` and the one-condition chain change (`3fdba1b`, 07:04:57) were committed before T2's TEST_GO (07:05:04). `git diff 1cda6af HEAD -- work/union_t2/src` contains only that condition, the `g1v5_report.py` output name and two new report helpers that launch nothing. `t2u_region4/PROTOCOL.md`, `jobs_test.json` (sha `3bbf9fa365ab`) and the overlay are unchanged. | **resolved** |
| **B2:** `G1_v5.md` missing (written as `G1_v4.md`) | `work/union/G1_v5.md` exists, with heading "G1_v5". It is byte-identical to the original `6d4a7a3:work/union/G1_v4.md`, and `work/union/G1_v4.md` is gone. Both `g1v5_report.py` copies now write `G1_v5.md`. The citations in `t1u_region2/PROTOCOL.md:27` and `union/SCOPE_AMENDMENT.md:7,28` resolve. The correction is appended to the notebook (07:04). | **resolved** |
| N1: convergence stall | Disclosed in FINAL_REPORT §5.6 and in T1 `RESULTS_test.md` §1. T2 has 0 repeated-θ rounds: every row's `n_sims` equals its number of distinct `th_*` result directories. | disclosed |
| N2: latent base-model race | It never fired, because T2 needed no extra seed. All 15/15 T2 `A_baleen` trains used `meta+block+chunk`, as did all 27/27 T1 trains. | disclosed; not triggered |
| N3: T1 static baselines unmatched | Reported as uninformative in T1 `RESULTS_test.md` §3 and FINAL_REPORT §3. All T2 static rows are matched. | disclosed |
| N4: PT and CP-SAT objectives tie | FINAL_REPORT §4 reports the tie and attributes no gain to better optimization. The dev control is now confirmed with 3 retrains. | disclosed |
| N5: `validate.py` robustness | Coordinator's item. No impact, because there is no claim (see N5 below). | open (coordinator) |

## 1. Sandbox, train lock, scope

| check | evidence | result |
|---|---|---|
| `validate.py --integrity-only` | `problems: []`. The contract sha, `check_frozen` ("frozen OK (94 files)"), reserve scan and privacy check are clean. Exactly 2 tests are registered: T1 `76cf5c8d` (commit 04:36:45 < GO 06:26:50) and T2 `1cda6af` (commit 05:19:24 < GO 07:05:04). Git history adds exactly two 3_autoresearch TEST_GO files (`f74bf8b`, `f27cdc2`) and deletes none. | OK |
| Nothing outside `changes/3_autoresearch/` modified | Repo-wide `find -newer autoscript/.leak_marker` outside 3_autoresearch (excluding `.git` and `.pyc`) returns nothing. No commit `8491a94..e964491` touches a path outside scope. The two untracked files outside scope predate the run (Oct 3 and Oct 5). The 4 partial static-sim directories deleted in the incident were in `union_t2/work_frozen/runs/prep`, a real directory inside scope; only `BCacheSim` and `data` are symlinks there. | OK |
| Sandbox: sub-process logs | I parsed every log with a command line under `work/*/logs`: 1,529 in total, 374 of them written in round 2 (283 in `union_t2`, 91 in `union` from the dev control confirmation). Every one begins `$ cd <work dir> && taskset -c 0-23 bwrap --dev-bind / / --bind <unique private systmp dir> /tmp -- <env python> -B`. The interpreter is the Baleen env or the solver env, never anything else. No private /tmp dir is reused. Deviations: **0**. | OK |
| Sandbox: worker transcript, round 2 | 81 tool calls, 77 of them Bash, and no subagents. Every launch goes through the chain (`source ./env.sh` → `src/sbx.sh`) or directly through `src/sbx.sh` (call #58, after `source env.sh`): call #7 is the T2 chain, call #19 its relaunch, call #58 the dev controls. System `python3` ran only read-only analysis (`report_tables.py`, `dev_eval.py`, `eval_test.py`, pandas one-liners), `g1v5_report.py` (JSON to Markdown) and `validate.py`. None of these imports BCacheSim or launches a sub-process. | OK |
| `env.sh` / `sbx.sh` | Unchanged from round 1 (HOME, XDG, TMPDIR and caches confined to the work dir; PYTHONNOUSERSITE and PYTHONDONTWRITEBYTECODE set). `sbx.sh` refuses to run without `AR_ROOT`. | OK |
| Train lock | Every train call site is inside `C.TrainLock()`: `cls._train`, `union._train_x` and `prep.run_train` (`prep.py:61`). Empirically, across all 228 train logs in `cls_table`, `union` and `union_t2` (71 from round 2, including the killed one), there are **0 overlapping [birth, mtime] intervals**. Each log is created inside the lock. | OK |

## 2. Code correctness of what produced the numbers

| check | evidence | result |
|---|---|---|
| Convergence and metric | `wpcommon`: `TARGET_WR = 35.599`, `TOL = 0.01`. `converge` uses θ ≤ 0.9999 without a schedule and ≤ 4.0 with α. `p100 = results["PeakServiceTimeUtil1"]`. For all 90 T2 evaluation rows I reopened the row's `result_file` and every `th_*` result in its converge directory. WR and P100 match the ledger exactly. `matched`, recomputed from WR, equals the ledger value. The row is the best-of-tried point, and `n_sims` equals the number of sims. Mismatches: **0**. | OK |
| Arms are what their names say (T2) | I parsed the command line of each row's best sim (90 rows): 0 deviations. **A:** `meta+block+chunk`, no α, θ < 1. **B:** `+load`, no α. **Aa-1.0 / Ba-1.0:** `--ap-load-adapt-alpha -1.0`, θ in (0, 4], with the A or B model of the same (instance, k). **XA-F1PT / XA-F1CPSAT:** α = −1.0, main model `A_baleen_<inst>_r<k>` on `meta+block+chunk`, union model `D_<labels>_<inst>_r<k>` on `+load`, no gate, and κ equal to `params/test/<inst>_<labels>_r<k>.json`. In every sim the trace matches the instance, the cache is `--size_gb 366.475`, and `--offline-ap-decisions` is absent. Train logs: 15 A (`meta+block+chunk`), 15 B (`+load`), and 15 D_F1PT plus 15 D_F1CPSAT (`+load`, `PolicyPeakBaleen4`, `[PB4] call` present). | OK |
| Overlay | `diff -r union/overlay union_t2/overlay` is identical. `PATCH_v5.diff` sha is `3cadbdf4a638` in both copies and in `results_test/integrity.txt`. There is no overlay diff in round 2. The SCOPE amendment and the G1_v5 bit-exact evidence were verified in round 1, and the report now exists under its cited name. | OK |
| Ising component and classical control (T2) | All 30 `results_test/cfg/D_*.json` point to `labels/Region4_s0.X_<labels>_s<k>.npz`, with the label kind and seed matching the retrain. **PT produces Y's labels:** F1PT gives 6 distinct label sets per instance over seeds 1–6, against 1 for F1CPSAT. **Same objective:** `label_peak_util` is identical for PT and CP-SAT on 30/30 Region4 solves, 36/36 Region2 solves and 3/3 Region1_s0 solves. On Region5_s0, PT − CP-SAT = +0.170%, +0.155% and −0.309%, matching FINAL_REPORT's "0.16–0.31%". | OK (§1 met literally) |
| Static baselines are frozen-code replays (T2) | All 10 rows ran in `union_t2/work_frozen` (`BCacheSim → 0_reproduce/baleen_code`, `check_frozen` OK). Train and sim logs are sandboxed and use no overlay flag. Each replay is 1 sim at the authors' probability from `jobs_test.json` (experiment `20230412_XX_rerun2`): RejectX 0.163–0.319, CoinFlip 0.044–0.067. All are matched (WR 35.57–35.61) with `--size_gb 366.475`. P100 and WR re-read from the result files are exact. `prep.py:179` asserts TEST_GO first. | OK |
| Incident handling (8 `__FAILED_` rows) | All 8 rows are A or Aa-1.0 retrain 1 on s0.2, s0.3, s0.4 and s0.6, with `FileNotFoundError` from `emu.get` (`cls.py:414`), raised after training and before `converge`. **No sim directory for those keys predates the 07:07:25 relaunch.** The pre-registered driver re-ran the same keys automatically: FAILED keys carry a suffix, so they stay in `todo`. The re-runs reused the original retrain-1 train records (07:05:36–07:07:03). The killed B r1 s0.2 training (`train.log.killed`, 07:07:15) never produced a row. Its retrain was trained again from scratch at 07:13. | OK (see N3) |

## 3. Statistics, recomputed from raw rows

### 3a. T2: the decisive test (`work/t2u_region4/trials_test.csv`)
**Ledger:** 98 rows = 90 evaluations + 8 incident `__FAILED_` rows. Every cell of 6 arms × 5 instances is **3/3 matched with reps {1, 2, 3}**, so no extra seed was due. The evaluator drops only the 8 `matched=False` FAILED rows, which have no P100. No other row is excluded.

**Per-instance mean P100 over the 3 matched retrains:**

| arm | s0.2 | s0.3 | s0.4 | s0.5 | s0.6 | mean |
|---|---|---|---|---|---|---|
| Y = XA-F1PT | 49.606 | 49.370 | 51.224 | 32.931 | 32.720 | **43.170** |
| A | 59.067 | 76.140 | 51.716 | 32.854 | 33.811 | 50.718 |
| B | 58.876 | 75.993 | 59.598 | 55.246 | 33.841 | 56.711 |
| A+α (Aa-1.0) | 49.579 | 48.954 | 51.595 | 32.412 | 31.810 | **42.870** (best α) |
| B+α (Ba-1.0) | 50.849 | 51.383 | 51.149 | 33.454 | 32.490 | 43.865 |
| control XA-F1CPSAT | 55.049 | 51.230 | 50.960 | 32.596 | 31.997 | 44.366 |

**Pass rule (n = 5, need 4 wins).** Positive R − Y means Y is better.

| Y vs R | wins | mean(R − Y) | SE_retrain | 2.5 SE | worst | rule |
|---|---|---|---|---|---|---|
| A | 4/5 | +7.5472 | 1.0275 | 2.5688 | −0.0775 | ok |
| B | 5/5 | +13.5408 | 1.6910 | 4.2275 | +1.1214 | ok |
| **A+α (best α)** | **1/5** | **−0.3002** | 1.1166 | 2.7914 | −0.9092 | **FAIL** (wins, margin) |
| B+α (not the reference) | 3/5 | +0.6947 | 1.0745 | 2.6862 | −0.2293 | (would also fail) |
| control (report only) | 2/5 | +1.1961 | 1.0475 | | −0.7225 | |

- **Static baselines:** RejectX 65.836 and CoinFlip 68.838, all matched. Y is below both.
- **Verdict:** `good_result = false`.
- My numbers equal `results_test/evaluation.json`, `t2u_region4/RESULTS_test.md` and FINAL_REPORT §3 to every printed digit. That includes the per-retrain values (Y s0.2 46.67 / 42.87 / 59.28, sd 8.59), the B collapses (s0.4 73.03; s0.5 55.1–55.3) and the mechanism table.
- Convergence used 4–10 sims per cell, with 0 repeated-θ rounds and 0 unmatched rows.

### 3b. T1 (`work/t1u_region2/trials_test.csv`): final state
**Ledger:** 132 rows: 86 matched, 46 unmatched, 0 FAILED.

**Matched/total:**
- Every arm is 0/6 on s0.2. All 36 s0.2 rows sit at θ = 1e-4, WR 11.510 and P100 189.068.
- A is 0/6 on s0.1 and 2/6 on s0.5.
- Every other cell is 3/3.

So the rule cannot be computed. `evaluation.json` lists exactly these 8 missing cells and has no `good_result`.

**Descriptive only, s0.3–s0.6:**
- Mean P100: Y 10.2461, A 10.2548, B 10.2008, A+α 10.1878, B+α 10.1349, control 10.2459.
- Y vs A+α: 1/4 wins, −0.058.

These match the T1 report and FINAL_REPORT, and they are labelled non-confirmatory.

**T1 statics:** RejectX is unmatched on 6/6 and CoinFlip on s0.2. They are reported as uninformative.

**Benign "mismatches" in my T1 check, explained:**
- `n_sims` exceeds the number of distinct sim directories only on stalled rows. These are the 30 per-arm s0.2 rounds and A s0.5 r1, the known N1 stall: cached re-reads.
- On two unmatched A rows, ties on a WR plateau (identical WR and P100) make the earliest-tried point the chosen one. No number changes.

### 3c. Dev evidence reported in FINAL_REPORT
My reimplementation uses matched, non-FAILED rows with rep ≤ 3. A+α = Aa-1.0 ∪ Ax-1.0 and B+α = Ba-1.0 ∪ Bx-1.0 come from the WP2 ledger, plus the `cls_table` and `union` dev ledgers.

**Union dev ledger:** 120 rows, all matched, 0 FAILED, reps 1–3. All 120 re-read from their result files exactly.

**Ising arm vs its CP-SAT twin** (n = 10; positive means Ising is better):

| Ising arm vs CP-SAT twin | wins | mean(control − Ising) | SE | worst | best | means (Ising / CP-SAT) |
|---|---|---|---|---|---|---|
| XA:F1PT vs XA:F1CPSAT | 6/10 | +0.7681 | 0.3585 (2.14 SE) | −0.2924 | +3.7897 | 35.359 / 36.127 |
| XG:F1PT vs XG:F1CPSAT | 6/10 | +0.4368 | 0.2765 | −0.2872 | +1.7976 | 35.529 / 35.966 |

**CP-SAT unions vs A+α:** +0.034 (worst −2.935) and +0.196 (worst −2.487). So neither would qualify. ✓

**Finalist rule:** it still reproduces: XA:F1PT vs A+α gives 7/10, +0.8025, SE 0.1835 and worst −0.8223.

**R0 screen (DEV8, retrain 1, d = min(A+α, B+α) − X):**

| candidate | mean d | worst | wins |
|---|---|---|---|
| CB-pt | +0.313 | −0.151 | 6/8 |
| CB-ptm | −0.097 | −1.683 | 4/8 |
| CA-pt | −0.151 | −1.131 | 4/8 |
| CA-ptm | — | — | — (an unmatched r1 cell) |
| UB-ptm | −0.732 | −4.516 | 2/8 |
| XA-F1PT | +1.460 | −0.276 | 6/8 |
| XG-F1PT | +1.072 | −0.228 | 7/8 |

All equal FINAL_REPORT §2.

**Mechanism** (all three DEV8 retrains):

| | XA:F1PT | A+α |
|---|---|---|
| Region6 P100 | 36.77 | 38.65 |
| Region6 peak big-offset share | 0.199 | 0.334 |
| Region7 P100 | 37.01 | 37.11 |
| Region7 first-access admission | 2.96% | 8.44% |

**Ledger counts in FINAL_REPORT §5.11:** `cls_table` 105 / 102 / 2 / 1, union 120 / 120 / 0 / 0, T1 132 / 86 / 46 / 0, T2 98 / 90 / 0 / 8. All four are exact.

**Ledger history:** across every committed snapshot of the four ledgers, no row was ever removed. The only value differences are pandas re-serialization in the 16th or 17th digit (`wall_secs`, `p100` of two FAILED/s0.2 rows), which are lossless.

## Blocking findings
None.

## Non-blocking findings (disclosure and wording; none changes any verdict)

### N1. An interim look at partial T2 outcomes is not in the notebook (confirms red-team round-2 N1)
**Evidence**
- Worker call #44, made while the T2 chain was running, was labelled "Peek at partial T2 results (report planning only)".
- It printed per-arm P100 for the completed T2 rows, for example Region4_s0.3: A 76.05, Aa 50.04, XA-F1PT 50.60.
- Calls #21–#53 also tailed the driver log, which prints P100 per round.

**Impact:** none on the verdict.
- After TEST_GO, T2 had no decision point: arms, seeds, the extra-seed rule and the evaluator were all fixed.
- `git diff 1cda6af..HEAD -- work/union_t2/src` shows no test-code change after 07:04.
- The only later launch is the dev control queue, committed at 04:56 (`6d4a7a3`).

**Fix:** append a dated notebook line saying that partial T2 outcomes were viewed during the run for report planning, and that no code, seed or protocol action followed.

### N2. Small descriptive inaccuracies (FINAL_REPORT §2.2 and §4; T2 `RESULTS_test.md` §4)
**Evidence (label files, `jaccard_vs_baleen`)**
- PT: Region2 0.41–1.00 and Region4 0.22–0.73. FINAL_REPORT §4 says "0.2–0.9".
- CP-SAT: Region2 0.80–1.00 and Region4 0.569–0.74. FINAL_REPORT §4 says "0.6–0.9"; T2 `RESULTS_test.md` §4 says "0.61–0.74". Region4_s0.5 CP-SAT is 0.569, and on Region2_s0.2 both solvers return Baleen's labels exactly (J = 1.0).
- FINAL_REPORT §2.2 says the union "did not restore **Baleen's** first-access admission on Region7 (3.0% vs 8.4%)". But 8.44% is A+α; Baleen A is 8.66%.

**Fix:** append corrections:
- PT 0.22–1.00 and CP-SAT 0.57–1.00 across the pools, noting that both are 1.0 on Region2_s0.2;
- T2 CP-SAT 0.57–0.74;
- "8.4% (A+α; A 8.7%)".

### N3. FINAL_REPORT §5.8 omits that one T2 retrain (B r1, Region4_s0.2) was retrained from scratch
**Evidence**
- In the 07:07 cleanup (call #18), the in-progress B r1 s0.2 training was killed and its log moved to `logs/test/B_baleen_Region4_s0.2_r1/train.log.killed` (07:07:15).
- The relaunched chain trained that retrain again (`train.log`, 07:13:05).
- FINAL_REPORT §5.8 says "the same retrains were re-run". That holds for the 8 FAILED rows, whose original retrain-1 train records were reused, but not for B r1 s0.2. That model is a fresh training run.
- The killed attempt produced no model, no sim and no row, and nothing was selected. The notebook's 07:07 entry does mention "set aside 1 partial train log".

**Fix:** add to §5.8: "One in-progress training (B r1 Region4_s0.2) was killed in the stop and retrained from scratch; it had produced no output."

### N4. The body of `result/STATUS.md` is stale below its final header
**Evidence**
- The header (11:26) correctly says "FINAL … No detached job is running".
- But the "Families" bullet still says the union "confirmation running".
- The detached-jobs table and RESUME block describe live jobs. One of them is the T2 chain, which is idempotent and harmless because CHAIN_DONE exists.

**Fix:** label everything below the header as the round-1/2 historical job record, or trim it.

### N5. Coordinator items carried over (no current impact, because no claim exists)
**Weaknesses in `code/validate.py`**
- (a) It trusts the CSV `matched` column (`:162`) instead of recomputing it from `wr`.
- (b) It averages static P100 regardless of `matched` (`:189-196`).
- (c) It does not require the claim paths to be the test directory's own files.
- (d) It counts only working-tree TEST_GO files, not git history.
- (e) `check_untouched` covers only three directories and three files.

**Why there is no impact:** my own checks cover all of these for this run. I recomputed `matched` from WR, all T2 static rows are matched, git history holds 2 TEST_GO files, and my repo-wide scan is clean.

**Fix (coordinator):** make those checks part of `validate.py` before any future run. Add the pool-feasibility gate from FINAL_REPORT §6.1 as well.

## Relation to the red-team review (round 2)
I read it only after finishing my own recomputation.
- **We agree:** no blocking finding, and the negative verdict is reproducible.
- **Their N1** (interim T2 look) is my N1, confirmed from the transcript.
- **Their N2** (Jaccard ranges) is my N2. I add the Region7 first-access wording.
- **Their N3** (H-CLS classical-control evidence is retrain-1 only and partial) is consistent with my ledger counts. I did not raise it separately.
- **Not in their review:**
  - my N3, the B r1 s0.2 retrain;
  - my N4, the stale STATUS body;
  - the independent per-row result-file reproduction of T2, T1 and union dev (0 mismatches);
  - the 228-log train-lock interval check;
  - the 1,529-log sandbox parse.

OPEN_FINDINGS=0
VALIDATOR_STATUS=PASS
