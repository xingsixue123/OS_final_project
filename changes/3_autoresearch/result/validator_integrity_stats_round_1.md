# Integrity, statistics and code validator: run 20261020_004634, round 1

**Reviewer role.** An independent check of the sandbox, the code that produced the numbers, and the statistics. I recomputed everything from raw files: logs, result `.lzma` files, ledgers and label files. I did not rely on the worker's summaries.

**What I wrote.** I edited no worker file and made no git writes. Running `python3 code/validate.py --integrity-only`, as instructed, rewrote `result/deterministic_validation.json`. The output was `problems: []` and `integrity_ok: true`. Integrity-only mode does not run the claim check, so the earlier "no claim file yet" note is absent until the next full run. My scratch analysis lives in the session scratchpad only.

**State reviewed** (2026-10-20, 06:45–06:58 EDT):
- No claim file exists.
- One test has been spent: T1, `work/t1u_region2`.
  - TEST_GO was written at 06:26:50 for commit `76cf5c8d`.
  - The test is still running. `trials_test.csv` had 122 rows at 06:58, and the extra seeds r4 and r5 are in progress.
  - There is no `CHAIN_DONE` and no `evaluation.json` yet.
- T2 is unspent. `chain_test_t2u.sh` is waiting at its step 2.

**Verdict:**
- What I checked is correct:
  - sandbox, train lock and scope;
  - arm definitions, threshold convergence and the P100 metric;
  - frozen static replays and the overlay's bit-exact evidence;
  - the mechanical dev finalist;
  - the ledger.
- **Two findings are blocking:**
  - **B1.** T1 cannot be evaluated as pre-registered, and the committed T2 chain halts on that outcome. This independently confirms red-team B1, with new evidence: reference arm A also fails to match on two more instances.
  - **B2.** The G1_v5 report that the protocol, the SCOPE amendment and the lab notebook cite does not exist under that name. A copy-paste bug wrote it to `G1_v4.md`. The bit-exact evidence itself is sound; I verified it.

## 1. Sandbox, train lock, scope

| check | evidence | result |
|---|---|---|
| `validate.py --integrity-only` | `problems: []`. Contract sha256, `check_frozen` ("frozen OK (94 files)"), reserve scan and privacy are clean. One test is registered: T1, `76cf5c8d`. | OK |
| Nothing outside `changes/3_autoresearch/` modified | No commit of this run (`9650674`..`b822b47`) touches a path outside `changes/3_autoresearch/`. A repo-wide scan for files newer than `autoscript/.leak_marker` outside `3_autoresearch` (`.git` and `.pyc` excluded) returns nothing. That scan is wider than `validate.py`'s, which covers only three directories plus three files. The two untracked files outside scope predate the run: `2_deployable_peak/TIMING_IDLE` (Oct 3) and `wp3_test/G3_SIGNED` (Oct 5). | OK |
| Sandbox: sub-process logs | 1,033 logs with a command line across `cls_table`, `union` and `union_t2`. Every one begins `taskset -c <set> bwrap --dev-bind / / --bind <work>/systmp/<unique> /tmp -- <env python> -B`: 981 in the Baleen env, 52 in the solver env, 0 deviations. The 144 label-solve logs without a command line (`union/logs/test/labels`, `union_t2/logs/test/labels`) were launched with `PY=$SOLVER_PY src/sbx.sh src/labels.py`, after `source env.sh` (transcript 08:20:36Z; `union_t2/src/prep_t2_all.sh:9`). `sbx.sh` also applies taskset, bwrap with a private jobtmp, and `-B`. | OK |
| Sandbox: worker transcript | 323 Bash calls and no subagents. Every Baleen or solver launch goes through `src/sbx.sh`, either directly or inside the chain scripts; there is no direct `$BALEEN_PY` or `$SOLVER_PY` call. System `python3` is used only for read-only analysis (`dev_eval.py`, `eval_test.py`, `ast.parse`), which imports no BCacheSim and launches nothing. | OK |
| Live processes | Running sims have affinity 0-23 (the idle set, since `TIMING_IDLE` exists) and a private `/tmp` bind. | OK |
| `env.sh` | The three copies are identical. They redirect HOME, XDG_*, TMPDIR and the caches into the work dir, and set PYTHONNOUSERSITE and PYTHONDONTWRITEBYTECODE. `sbx.sh` refuses to run without `AR_ROOT`, and `wpcommon.base_env` asserts `AR_ROOT == W`, so a missing sandbox fails closed. | OK |
| Train lock | Every train call site is inside `C.TrainLock()` (flock on `2_deployable_peak/.train.lock`): `cls.py:168`, `union.py:84`, `prep.py:61`, `prep_day1.py:51`, and `_train` in `g1v4.py`/`g1v5.py`. Empirically, the 134 train logs (birth time = start, inside the lock; mtime = end) have **zero overlapping intervals**. | OK |

## 2. Code correctness of what produced the numbers

| check | evidence | result |
|---|---|---|
| Convergence and metric | `cls.converge`: target 35.599, tolerance 1%, at most 7 full sims. θ is in [1e-4, 0.9999] for A and B, and in [1e-4, 4] whenever an α, table or union schedule is set (`cls.py:334`). `matched` = \|wr − 35.599\|/35.599 ≤ 0.01. `p100` = `results["PeakServiceTimeUtil1"]` (`wpcommon.metrics`). For every ledger row present at check time (114), I reopened its `result_file`. P100, WR, `matched`, best-of-tried and `n_sims` all reproduce exactly: 0 mismatches. | OK, but see N1 |
| Arms are what their names say | I parsed all 238 test sim command lines then present. **A:** no α, `meta+block+chunk`, θ < 1. **B:** `+load`. **Aa-1.0:** `--ap-load-adapt-alpha -1.0`, `meta+block+chunk`, θ in (0, 4]. **Ba-1.0:** α = −1.0, `+load`. **XA-F1PT / XA-F1CPSAT:** α = −1.0; main model is `A_baleen_<inst>_r<k>` on `meta+block+chunk`; union model is `D_<labels>_<inst>_r<k>` on `+load`. Every sim's model belongs to its own (instance, k): 0 deviations. Train logs: every `A_baleen` train (r1–r5) uses `meta+block+chunk`; every B and D train uses `+load`. All 38 X configs point to `labels/<inst>_<labels>_s<k>.npz` with the matching k, and every X train log contains `[PB4] call`. | OK, but see N2 |
| Overlay | `union/overlay` equals `PATCH_v5.diff` (`3cadbdf4a638`; delta `6a0eb8a6ca66`; v4 `6dc6ef935e6f`), matching protocol §2. No overlay file is newer than `g1v5_summary.json`, and there is no diff since `76cf5c8`. `SCOPE_AMENDMENT.md` (1.2d) is present. **G1_v5 evidence, recomputed:** I decompressed all 8 a/b pairs (RejectX, CoinFlip, pinned pipeline, same models, α v4/v5, class table v4/v5, union-never, union-self). All results and batch series are identical; only `SimWallClockTime`, `SimRAMUsage` and `realtime_elapsed` differ. | Evidence OK; the report file is misnamed (B2) |
| Code changed after the protocol commit | In `76cf5c8..HEAD`, `union/src` changes only `cls.py`, `union.py` (`and sp["rep"] <= 3` inside `C.MODE == "dev"`) and `chain_union_dev.py` (dev), plus new files. The test paths are unchanged. The T2 copy (`union_t2/src`, `overlay`) is identical to `union` except for `W`, and `t2u_region4/PROTOCOL.md` is unchanged since `1cda6af`. | OK |
| Ising component and classical control | **PT side:** `labels.py` F1PT calls `q2run.make_level_solver("pt")`, i.e. `q2anneal.eim` with `eim_pmode="quad"`. That is replica exchange on the QUBO-penalty energy (R = 16, frozen 10 s config from `plan_F1.json`), started from an LP solution. **CP-SAT side:** F1CPSAT calls `q2cpsat` on the same `make_form(I, {"name": "F1"})`, the same day-1 instance, the same single level f = 1, and the same 10 s budget. The `q2lib` files are byte-identical to `explore/q2/src` and to the WP9 copy. **PT changes its start:** its LP start is deterministic, yet PT returns 6 distinct label sets per instance across seeds 1–6 (s0.1, s0.3–s0.6). So PT, not the LP, produces Y's labels. **Same objective:** confirmed, and the objective values tie (N4). | OK (§1 met literally) |
| Static baselines are frozen-code replays | All 12 rows come from `work_frozen`, which points to `0_reproduce/baleen_code` (`check_frozen` OK). All 18 static train logs and 188 sim logs ran in `union/work_frozen`, with trains under the TrainLock. P100 recomputed from the result files matches. The replays are asserted to run only after TEST_GO (`prep.py:179`). | OK; matched status: N3 |

## 3. Statistics, recomputed from raw rows

### 3a. Dev finalist (the mechanical selection that fixed Y)
I reimplemented the rule in pure Python, not using `dev_eval.py`, on matched, non-`__FAILED_` rows from:
- `2_deployable_peak/wp2_deployed/trials.csv` (DEV8 references);
- `cls_table/trials_dev.csv` (Region5_s0 / Region1_s0 references);
- `union/trials_dev.csv` (candidates);

with A+α = `Aa-1.0` ∪ `Ax-1.0` and B+α = `Ba-1.0` ∪ `Bx-1.0`.

Results: n = 10 instances, need ≥ 7 wins. Best α = A+α (mean 36.162, against 36.618 for B+α).

| candidate | vs A (wins, mean R − X, SE, worst) | vs B | vs A+α | qualifies |
|---|---|---|---|---|
| XA-F1PT | 10/10, +1.4226, 0.1873, +0.0167 | 9/10, +1.4078, 0.1934, −0.2812 | 7/10, +0.8025, 0.1835, −0.8223 | yes |
| XG-F1PT | 10/10, +1.2525, 0.1506, +0.0684 | 8/10, +1.2377, 0.1582, −0.1902 | 7/10, +0.6323, 0.1458, −1.5785 | yes |

- **Tie-break:** the larger min over R of mean(R − X) is 0.8025 against 0.6323, so XA-F1PT is the finalist. This equals `union/results/dev_finalist.json` to every printed digit.
- **Exclusions:** only unmatched rows are excluded, all of them kept in the ledgers. The 24 WP2 Region6 `Aa-1.0`/`Ba-1.0` rows that hit the (0, 1) cap (WR 46–55) were replaced by `Ax`/`Bx` runs over (0, 4], as published in `wp2_deployed/RESULTS_dev.md:241`.
- **Union dev ledger:** 76 rows, 0 failed, 0 unmatched.
- **Both dev ledgers** contain only the 10 allowed dev instances, with reps 1–3.

### 3b. T1 ledger (`work/t1u_region2/trials_test.csv`; 122 rows at 06:58; matched/total per cell)

At 07:01 (131 rows), A had reached s0.1 0/5 and s0.5 **2/6 (final)**, and s0.2 had r6 for every arm (0/6).

| arm | s0.1 | s0.2 | s0.3 | s0.4 | s0.5 | s0.6 |
|---|---|---|---|---|---|---|
| Y = XA-F1PT | 3/3 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| A | **0/4** | 0/5 | 3/3 | 3/3 | **1/4** | 3/3 |
| B | 3/3 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| A+α = Aa-1.0 | 3/3 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| B+α = Ba-1.0 | 3/3 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| control = XA-F1CPSAT | 3/3 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |

**Ledger integrity:**
- Driver log against ledger: 114 `== <key>` lines map one-to-one to 114 rows at check time. Nothing is missing or extra, and there are no tracebacks.
- The 2 rows committed in `f74bf8b` are unchanged.

**No exclusion beyond the protocol:**
- `validate.py` and `eval_test.py` drop only `matched=False` rows.
- The extra seeds run exactly as protocol §3 specifies: r4 and r5 batches for the 8 deficient cells (`union/logs/test_t1u.out`).

**Pass rule:** not computable.
- `validate.py:check_claim` would stop at "arm Y (XA-F1PT) has < 3 matched retrains on Region2_s0.2".
- `eval_test.py:59` would write `evaluation.json` with `missing` and no `good_result`.
- My implementation, run in memory, gives the same result. I did not run `eval_test.py`, because it writes a worker file.

**Descriptive snapshot (not the pre-registered rule; non-confirmatory; R − Y > 0 means Y is better).** On s0.3–s0.6, where every arm has at least one matched row (A on s0.5 has only one), mean P100 is:

| arm | mean P100 |
|---|---|
| Y | 10.246 |
| A | 10.245 |
| B | 10.201 |
| A+α | 10.188 |
| B+α | 10.135 |
| control | 10.246 |

| comparison | wins | mean(R − Y) |
|---|---|---|
| Y vs A | 2/4 | −0.001 |
| Y vs B | 2/4 | −0.045 |
| Y vs A+α | 1/4 | −0.058 |
| Y vs B+α | 0/4 | −0.111 |
| Y vs control | 2/4 | −0.000 |

So no subset reading of T1 favours Y. The T1 failure is not an artefact of s0.2.

## Blocking findings

### B1. T1 is unevaluable as pre-registered, and the committed T2 chain halts on that outcome (confirms red-team B1, with new evidence)

**Evidence: s0.2 cannot reach the target for any arm**
- All Region2_s0.2 rows end at θ = 1e-4 (the floor, i.e. admit everything) with WR 11.510 and P100 189.068. Their convergence CSVs repeat θ = 0.0003 six times.
  - At 06:58 there were 30 such rows (6 arms × r1–r5).
  - At 07:01 there were 36 (r1–r6), still all identical.
- At admit-all, the write rate does not depend on the model, so seed 6 cannot change this.
- The frozen-code CoinFlip replay confirms it: on s0.2 it reaches only WR 11.13 at probability 1.18 (`results_test/static_baselines.csv`).
- This is not a pipeline bug. The constructed s0.2 job equals the s0.1 job apart from the trace path (`union/jobs_test.json`). The s0.2 trace file (2.41 MB) is the same size as s0.3–s0.6.

**New evidence: reference arm A also fails to match on two instances**
- Arm A is 0/4 matched on s0.1 and 1/4 on s0.5. Its write rate falls off a cliff at the target:
  - s0.1 r2: 37.21 → 34.28 MB/s between θ 0.553273 and 0.553671;
  - s0.5 r4: 38.11 → 35.15 MB/s between θ 0.639488 and 0.640042, where 35.15 is 0.09 MB/s under the ±1% band.
- **Update at 07:01 (131 rows):**
  - A on s0.5 is at **2/6 matched with seed 6 used**. That cell can never reach 3.
  - A on s0.1 is at **0/5**, with only r6 left.
- So T1 is unevaluable on at least two instances. Even an outcome-informed "drop s0.2" repair could not produce a computable rule.

**Evidence: the chains do not handle this outcome**
- `union/src/eval_test.py:59-62` (`if missing:`) writes `evaluation.json` without `good_result`.
- `union_t2/src/chain_test_t2u.sh:29` reads `.get('good_result')`, which prints `None`, and line 32 then exits 1 ("T1 evaluation incomplete (None) -> stop for inspection").
- `result/STATUS.md` ("Next round") covers only `good_result` true or false.
- So the next step needs a decision after T1 outcomes have been seen.

**Fix: commit, in this order, before `evaluation.json` is read or any T2 action is taken**
1. **Declare T1 closed.** Add a dated note in `result/LAB_NOTEBOOK.md` and `result/STATUS.md`, appended, not rewriting earlier text: T1 is **spent and failed (unevaluable as pre-registered)**. Region2_s0.2 stays in the pool. `matched` is not relaxed. No seed beyond 6 is run. T1 is not re-registered or re-spent. Let the running chain finish its pre-registered seeds; do not kill it.
2. **Let T2 run as pre-registered.** Change only the condition in `union_t2/src/chain_test_t2u.sh:32`, so that a missing or `None` `good_result` (with T1 TEST_GO and CHAIN_DONE present) counts as "T1 not passed". Record the change in a new dated file in `work/t2u_region4/` (for example `ADDENDUM_T1_UNEVALUABLE.md`) and commit it before any T2 TEST_GO. Do not edit any `PROTOCOL.md`, `eval_test.py`, Y, the control, the arms or the pool.
3. **Report T1 in full.** The T1 report shows every row and the matched/total table above, including A's unmatched s0.1 and s0.5 cells. Any subset summary is labelled descriptive and is never called a pass.

### B2. The G1_v5 report cited as the union's fairness gate does not exist under its cited name; the report script writes `G1_v4.md`

**Evidence: where the file is cited**
- `work/t1u_region2/PROTOCOL.md:27` cites "G1_v5: `work/union/G1_v5.md`".
- `work/union/SCOPE_AMENDMENT.md:7` says "A result that uses the union counts only after `G1_v5.md` reports PASS"; line 28 says the same.
- `result/LAB_NOTEBOOK.md:251` asserts "**`work/union/G1_v5.md`: PASS on every check.**"

**Evidence: the file does not exist, and why**
- `find changes/3_autoresearch -name 'G1_v5*'` returns nothing.
- `work/union/src/g1v5_report.py:59` (copied from `g1v4_report.py`) writes `G1_v4.md`. Its docstring says it writes `G1_v5.md`. The same bug is in `work/union_t2/src/g1v5_report.py:59`.
- So `work/union/G1_v4.md`, first committed in `6d4a7a3`, is in fact the G1_v5 report: its heading is "# G1_v5: default equivalence of overlay v5 + the union checks".
- A reader following the protocol citation finds no gate report. A file named for v4 holds the v5 verdict, which breaks the provenance of the contract §2 requirement.
- The underlying evidence is sound: see §2, where I recomputed all 8 pairs. No re-run is needed.

**Fix: one new commit, before any T2 TEST_GO and before any claim**
1. Change the output path in both copies of `g1v5_report.py:59` to `G1_v5.md`. This script is not on any test path; the chains read `g1v5_summary.json`.
2. Regenerate `work/union/G1_v5.md` from the unchanged `results/g1v5_summary.json`, or `git mv work/union/G1_v4.md work/union/G1_v5.md`.
3. Do not leave a v5 report named `G1_v4.md` in `work/union/`. The canonical v4 report is `work/cls_table/G1_v4.md`.
4. Append a dated correction to `LAB_NOTEBOOK.md`; do not rewrite line 251.
5. Do not touch either `PROTOCOL.md` or `SCOPE_AMENDMENT.md`. Once the file exists, their citations resolve.

## Non-blocking findings (disclose in the T1/T2 report or the final report)

### N1. The threshold search stalls and wastes budget on write-rate plateaus and cliffs. The code is pre-registered, so it must be disclosed, not changed

**Evidence: the stall**
- In `cls.py:305-318` (`next_theta`), `a = min(above, key=wr)` breaks WR ties by the earliest point. The interpolation therefore keeps returning the same θ.
- The duplicate guard (`cls.py:353-356`) adds +2e-4 once and never re-checks. `sim_at` then re-reads the cached result directory, so a round is used up with no new simulation.
- Example: `A_baleen_Region2_s0.5_r1` tried θ = 0.601112 three times while its bracket (37.04 above / 30.76 below) was never bisected.
- In the T1 directory, 19 of 102 convergence files had repeated rounds at check time; all except that one are s0.2 rows, where the stall is harmless.

**Evidence: the one-sided search**
- The update is plain false position, with no Illinois or bisection safeguard. On step-shaped WR(θ) curves it approaches from one side and stops just outside the band.
- Example: A s0.1 r2 spent 5 sims below a 37.21 → 34.28 cliff 0.0004 wide.
- Example: A s0.5 r4 ended at 35.15.

**Impact**
- Outside s0.2, reference arm A is unmatched in 7 of 17 rows, against 0 of 15 for Y.
- The unmatched rows are kept and replaced by seeds per protocol, so no row is hidden and no matched value is wrong.
- But which retrains match is not random with respect to the model, and A's cells become the binding constraint.
- This is the WP9/WP10 `converge` code, fixed by both the T1 and T2 protocols.

**Fix**
- Do not change it for T1 or T2. A change after unblinding would alter A's matched set.
- In the report, list per cell: `n_sims`, the repeated-θ rounds, and the unmatched count.
- For any future protocol, use a safeguarded bracket (Illinois or a bisection fallback) and re-check the duplicate guard in a loop.

### N2. A latent race can train model A_k on the wrong feature subset; it fails closed and has not fired

**Evidence: the defect**
- XA and XG arms have `ap = meta+block+chunk+load` and `base = "A"` (`union.py:40`).
- `union.run_eval` calls `B.train(sp)` with the XA spec (`union.py:129`).
- `cls._train` caches by `base_key = A_baleen_<inst>_r<k>`, but sets `--ap-feat-subset sp["ap_subset"]` (`cls.py:165`), which is `+load` for an XA caller.

**When it fires**
- In the extra-seed pass (`cls.py:443-458`), suppose Y or its control needs seed k on an instance where arms A and Aa do not.
- Then the XA spec is the first caller, and A_k is trained on `+load` and cached for every arm.

**Consequence: fail-closed**
- The overlay asserts the main model's feature count (`overlay/.../admission_policies.py:358` for A and Aa, `:371` for the union).
- Those sims crash and produce `__FAILED_` rows for A, Aa, Y and the control at seed k on that instance. The seed is lost; no number is wrong.

**Status:** not triggered so far. All 27 test `A_baleen` trains (r1–r6, as of 07:01) used `meta+block+chunk`.

**Fix**
- **Minimal:** after T1, and after T2 if it runs, audit `logs/test/A_baleen_*/train.log`, which must all show `--ap-feat-subset meta+block+chunk`. Report any `__FAILED_` row whose log shows that AssertionError as this race.
- **Optional, the coordinator's call:** a one-line fix (base training uses `arm_def(sp["base"])["ap"]`), committed as a dated T2 addendum before T2 TEST_GO. It enforces the protocol's own definition, "A_k = the same retrain as arm A". But it is a change to test code after T1 unblinding, so it needs sign-off.

### N3. T1's static baselines are not at the operating point, and the pass rule ignores static `matched` (confirms red-team N1)

**Evidence**
- In `results_test/static_baselines.csv`, RejectX is unmatched on all 6 instances: WR 21.19, 2.00, 36.47, 31.68, 25.36 and 29.32. `ap_probability == author_prob` after 15 sims, because the knob does not move WR.
- CoinFlip s0.2 is unmatched (WR 11.13). The bisection also pushed its probability to 1.178713, above 1, because `prep.py:149` does not clamp it.
- `code/validate.py:189-196` and `eval_test.py:70-73` average P100 over every static row, whatever its `matched` value.
- The supplementary `supp_rejectx.csv` matches only s0.3.

**Fix**
- Report the T1 static comparisons as uninformative, stating their matched status.
- Never substitute `supp_rejectx.csv`.
- For the coordinator: require matched static rows in `validate.py`, or flag unmatched ones.

### N4. The Ising and classical solvers tie on the objective on the test pool too (confirms red-team N4 with test-pool training-day data)

**Evidence**
- `label_peak_util` is identical for PT and CP-SAT on every Region2 instance and all 6 seeds: 4.852, 1.249, 7.756, 6.300, 4.870 and 6.855 for s0.1–s0.6.
- PT gives 6 co-optimal sets per instance. Their Jaccard similarity to CP-SAT's sets ranges from 0.49 to 0.99. CP-SAT gives 1–3 sets.
- On s0.2 both solvers return exactly Baleen's labels.

**Fix (as the red team states)**
- Report the equal objectives.
- Attribute no Y-vs-control difference to better optimization by the Ising solver.
- Label the control's dev evidence as retrain 1 only.

### N5. `code/validate.py` robustness (coordinator's remit; no current impact)

**Weaknesses**
- **(a)** It trusts the CSV `matched` column instead of recomputing it from `wr` (`validate.py:162`).
- **(b)** The claim's `trials_csv` and `static_baselines_csv` paths are not required to be the test directory's own files (`validate.py:159`, `:188`).
- **(c)** Static rows are not checked for `matched` (see N3).
- **(d)** Per-cell rep sets are not checked against the protocol (seeds 1–6).
- **(e)** `check_untouched` scans only `0_reproduce`, `1_literature_review`, `2_deployable_peak` and three files. It does not cover `tools/`, `documents/` or `lit_review/`.

**Why there is no current impact:** my recomputation from the raw result files found the ledger consistent, and my repo-wide scan was clean.

**Fix (coordinator):**
- recompute `matched` from `wr`;
- require the claim paths to be `<test_dir>/trials_test.csv` and `<test_dir>/results_test/static_baselines.csv`;
- reject rep > 6;
- scan the whole tree outside `changes/3_autoresearch/`.

## Relation to the red-team review (round 1)
- **Confirmed independently:**
  - B1, with new evidence on arm A;
  - N1, its static-baseline finding (my N3);
  - N4, its solver tie (my N4), now on test-pool data;
  - its fair-arms, ledger and dev-finalist conclusions.
- **Not in the red-team review:**
  - B2, the missing G1_v5 report;
  - N1, the convergence stall;
  - N2, the latent base-model race;
  - N5, the validator weaknesses.
- **No disagreement.**

OPEN_FINDINGS=2
VALIDATOR_STATUS=FAIL
