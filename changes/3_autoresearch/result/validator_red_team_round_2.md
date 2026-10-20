# Red-team validator, run 20261020_004634, round 2

**Reviewer role:** an independent, skeptical check for selection bias, leakage and p-hacking. I edited no worker file and made no git writes. All recomputations were made in my own scratchpad from the raw ledgers.

**State reviewed** (2026-10-20, about 11:30 EDT; HEAD `e964491`):
- **No claim file exists.** `result/STOP_EXHAUSTED` is written, and `result/FINAL_REPORT.md` states a negative result.
- **Two tests are spent:**
  - T1 (`work/t1u_region2`): protocol `76cf5c8d` committed 04:36:45; TEST_GO 06:26:50; closed as spent, failed and unevaluable.
  - T2 (`work/t2u_region4`): protocol `1cda6af` committed 05:19:24; TEST_GO 07:05:04; failed.
- The only uncommitted changes under `changes/3_autoresearch` are the launcher-managed `LOOP_STATUS.txt` and `deterministic_validation.json`.
- `changes/2_deployable_peak/TIMING_IDLE` (Oct 3) and `wp3_test/G3_SIGNED` (Oct 5) predate this run and are unrelated.

**Verdict:** the round-2 process is clean.
- The round-1 blocking finding B1 was fixed exactly as required, and in the required order.
- T2 ran as pre-registered with the same Y, control, arms, code and pool.
- No test-pool or reserve data was used for any choice.
- No ledger row was lost, and no extra seed was run.
- Every number I recomputed matches the reports.
- The negative outcome is reported honestly, including the classical control.

**No blocking finding remains.** The non-blocking items below are disclosure or wording fixes.

## Status of round-1 findings

| round-1 item | evidence in round 2 | status |
|---|---|---|
| **B1:** T1 is unevaluable; next step undefined | **Fail-closed decision committed first.** `539f39e` (07:04:06), LAB_NOTEBOOK 07:05 entry:<br>• T1 is spent and failed; s0.2 stays in the pool; `matched` is not relaxed;<br>• no seed beyond 6; no re-registration; no subset reading is called a pass.<br>**It came before any `evaluation.json` read.** In the worker transcript (`worker_events_round_2.jsonl`), the only earlier command (11:03:49Z) printed directory listings and chain logs ("T1 good_result=None"). The first `evaluation.json` read is at 11:05:33Z.<br>**T2 chain condition changed in one place only.** `git diff 1cda6af HEAD -- union_t2/src/chain_test_t2u.sh` shows that single condition. It is committed with `ADDENDUM_T1_UNEVALUABLE.md` in `3fdba1b` (07:04:57), before TEST_GO (07:05:04). PROTOCOL.md is unchanged.<br>**T1 report shows all 132 rows**, with a matched/total table and the descriptive section labelled "NOT the pre-registered rule; non-confirmatory; never a pass" (`t1u_region2/RESULTS_test.md`). | **fixed** |
| N1: T1 static rows unmatched | Stated in `RESULTS_test.md` §3 and FINAL_REPORT §3 and §5.5. `supp_rejectx.csv` is never substituted. All T2 static rows are matched (WR 35.57–35.61). | fixed (disclosed) |
| N2: R4 / ADDENDUM_R4 after the protocol commit | FINAL_REPORT §5.2–5.3. | fixed (disclosed) |
| N3: DEV_RULES timing; `sed` header rewrites | FINAL_REPORT §5.1. Round-2 entries take their times from `date`; corrections are appended (notebook 07:04, 07:16, 11:26). DEV_RULES.md is unchanged since `4e25e7e`. | fixed |
| N4: thin Ising-vs-classical evidence | **Union dev controls confirmed:** 44 evaluations, 120/120 dev rows matched, 3 retrains × 10 instances.<br>**Objective tie reported** (36/36 and 30/30 pool solves).<br>**No gain attributed** to better Ising optimization (FINAL_REPORT §4). | fixed |
| N5: T2 must stay locked | STATUS 07:17 says "Locked". Y, control, arms, pool and test code are unchanged (see the table below). | fixed |
| N6: reserve rows in a printed listing | FINAL_REPORT §5.9. Nothing new in round 2. | fixed (disclosed) |
| N7: ledgers rewritten in full | Snapshots were committed at each step, and I verified the rewrites lose nothing (below). Per-ledger counts are in FINAL_REPORT §5.11; per-cell tables are in both RESULTS files. | fixed |
| N8: `validate.py` sees only working-tree TEST_GO files | Coordinator remit. Both TEST_GO files are committed (`f74bf8b`, `f27cdc2`), and only these two were ever added (`git log --diff-filter=A`). | open for the coordinator; no impact |

## What I checked in round 2

| check | evidence | result |
|---|---|---|
| **TEST_GO vs protocol commit** | **T1:** TEST_GO mtime 06:26:50 > `76cf5c8` at 04:36:45. Content: `76cf5c8d…`, POOL=T1.<br>**T2:** TEST_GO mtime 07:05:04.39 > `1cda6af` at 05:19:24. Content: `1cda6afb…`, POOL=T2.<br>The T2 TEST_GO mtime did not change on the 07:07 relaunch (transcript 11:07:35Z). | OK |
| **Protocols or addenda edited after commit** | `git diff <commit> -- PROTOCOL.md` is empty for `t1_region2`, `t1u_region2` and `t2u_region4`.<br>`ADDENDUM_T1_UNEVALUABLE.md` is unchanged since `3fdba1b`; `ADDENDUM_R4.md` is unchanged since `6d4a7a3`. | OK |
| **T2 test code vs protocol** | **Changes since `1cda6af` in `union_t2/src`:**<br>• the chain condition (above);<br>• `g1v5_report.py` output filename (B2 fix; report only);<br>• new files `write_claim.py` (unused) and `report_tables.py` (report only).<br>**Code identical to T1's test path.** `diff -r union/src union_t2/src` differs only in the `wpcommon.py` work-dir constant. The overlays are byte-identical. `jobs_test.json` sha256 `3bbf9fa365ab` matches the protocol. | OK |
| **Pool data read before TEST_GO** | **T2 prerequisites built before the protocol, unread.** Dumps and labels were built 04:57–05:04, before the T2 protocol commit and before Y was fixed (06:26). For Region4, the round-1 transcript shows only `ls` output and the authors' command parameters (EA, threshold, RejectX/CoinFlip probability; the jobs builder at 08:57:17Z). No label statistics, dump contents or P100 were printed.<br>**No T2 sims before TEST_GO.** The first T2 test-run artefact is at 07:05:24 and the first static replay at 07:05:14, both after TEST_GO. `prep.py:179` asserts TEST_GO before any static replay. | OK |
| **Reserve samples 0.7–0.9** | No file under `work/` (ignored files included) is named for a reserve sample. `git grep` over `changes/3_autoresearch` finds no reserve reference outside the validator reports, and the full round-2 transcript has none. | OK |
| **WP3/WP9/WP10 test samples** | `union/trials_dev.csv` (120 rows) and `cls_table/trials_dev.csv` (105 rows) use only DEV8, Region5_s0 and Region1_s0, with retrains 1–3. | OK |
| **Ledger integrity, T2** | **198c76d → 80233a6** (−9/+99 lines): a header widening from 15 to 39 columns. All 8 `__FAILED_` rows are kept, every trial_key survives, and no shared column value changed. HEAD equals `80233a6`.<br>**Contents:** 98 rows = 90 evaluations + 8 incident rows; no duplicate keys; retrains 1–3 only.<br>**Incident rows were re-run, not re-rolled.** The successful A/A+α retrain-1 rows reuse the retrain-1 train records written at 07:05:36–07:06:41, before the relaunch, so no seed was added. | OK |
| **Ledger integrity, others** | Numstat per commit: `union/trials_dev.csv` and `cls_table/trials_dev.csv` are append-only (0 deletions). `t1u_region2/trials_test.csv` has only the round-1-verified re-serialisation, plus one appended row in `f27cdc2`. | OK |
| **Extra seeds** | **T1:** retrains 4–6 only in cells short of 3 matched (all s0.2 cells, A s0.1, A s0.5), as pre-registered; none beyond 6.<br>**T2:** none needed (30/30 cells 3/3). | OK |
| **T2 pass rule recomputed from raw rows** | **matched** = \|WR − 35.599\| ≤ 1%: 0 disagreements with the flag. WR range 35.25–35.93.<br>**Means:** Y 43.170, A 50.718, B 56.711, A+α 42.870, B+α 43.865, control 44.366. Best α = A+α.<br>**Y vs R:**<br>• vs A: 4/5, +7.547, SE 1.028;<br>• vs B: 5/5, +13.541, SE 1.691;<br>• **vs A+α: 1/5, −0.300, SE 1.117, worst −0.909 → FAIL;**<br>• vs control: 2/5, +1.196.<br>**Static:** RejectX 65.836, CoinFlip 68.838, all 10 rows matched.<br>This equals `evaluation.json` (`good_result: false`) and the reports. | OK |
| **Fair arms on T2** | Same A_k for A, A+α, Y and the control: `train_key` = `A_baleen_<inst>_r<k>` in every XA row. X = `D_<solver>_<inst>_r<k>`, label seed k.<br>All 15 A trainings used `--ap-feat-subset meta+block+chunk`.<br>The θ range is (0, 1) for A/B and (0, 4] for every adaptive arm, the same as `wp9_region5/src/wp9.py:346`. TOL 0.01; ≤ 7 sims (max used: 5). | OK |
| **Post-test dev work** | **Pre-planned, report-only control confirmation.** The 44-evaluation queue was written at 04:55 (header of `queue_dev2_controls.txt`) and was listed as post-T2 report-only work at 07:17, before any T2 outcome. It was launched at 10:01.<br>**Selection files untouched.** No candidate, rule or finalist changed: `dev_finalist.json` and `dev_screen.json` were last changed in `f74bf8b` / `6d4a7a3`. | OK |
| **FINAL_REPORT numbers recomputed** | **Dev finalist** (vs A 10/10 +1.423; vs B 9/10 +1.408; vs A+α 7/10 +0.802, SE 0.183, worst −0.822): matches.<br>**Ising vs CP-SAT twin:** XA 6/10 +0.768 (SE 0.358, best +3.790); XG 6/10 +0.437 (SE 0.277). Matches.<br>**CP-SAT unions vs A+α:** +0.034 (worst −2.935) and +0.195 (worst −2.487). Matches.<br>**T1 descriptive** (s0.3–0.6: Y 10.246, A+α 10.188, 1/4 wins, −0.058): matches.<br>**Ledger counts** (105/102/2/1, 120/120/0/0, 132/86/46/0, 98/90/0/8): match.<br>**F1 objective PT = CP-SAT:** 36/36 on Region2 and 30/30 on Region4. Matches. | OK |

## Blocking findings

None.

## Non-blocking findings (wording or disclosure; they do not affect any verdict)

### N1. An interim look at partial T2 outcomes is not disclosed in the notebook
**Evidence**
- At 08:18 EDT (transcript `[771]`, 12:18:32Z), with 28 of 90 T2 evaluations done, the worker printed the per-arm P100 of every matched T2 row so far ("A quick look at the partial picture only helps plan the report").
- `LAB_NOTEBOOK.md` has no entry for it.
- **Impact: none.** T2 was fully locked by then, and no file under `union_t2/src`, `t2u_region4/` or `DEV_RULES.md` changed afterwards. The only later actions were the pre-planned control confirmation and the reports.
- It is still test-outcome access before the test finished. A pre-registration audit trail should record it.

**Fix:** append a dated LAB_NOTEBOOK line: "08:18: interim look at 28/90 T2 rows (report planning only); no change followed". In future runs, do not read test metrics before CHAIN_DONE.

### N2. Small inaccuracies in the Jaccard ranges (descriptive text only)
**Evidence** (from `union/labels/Region2_*` and `union_t2/labels/Region4_*` JSON, field `jaccard_vs_baleen`):
- `t2u_region4/RESULTS_test.md` §4 says "CP-SAT 0.61–0.74". The actual range is **0.569**–0.742: Region4_s0.5 F1CPSAT is 0.569 on every seed.
- FINAL_REPORT §4 says "PT 0.2–0.9 … CP-SAT 0.6–0.9 on the pools". The actual ranges are PT 0.215–1.00 and CP-SAT 0.569–1.00. The 1.00 values are Region2 s0.2, where both solvers return Baleen's own labels.

**Fix:** correct the two ranges with an appended, dated correction. No conclusion changes.

### N3. The H-CLS classical-control evidence stays retrain-1 and partial
**Evidence**
- `cls_table/trials_dev.csv` has CA-cd 1, CB-cd 4, CA-cdm 3, CB-cdm 3 and UB-cdm 1 rows.
- `queue_report.txt`, listed as optional in STATUS 07:17, was never run.
- FINAL_REPORT §5.11 discloses that these runs were stopped and "the rest were never run". It does not say that the H-CLS PT-vs-CD comparison therefore rests on these few rows.

**Impact:** none on any decision. H-CLS had no finalist, and the PT/CD energies are reported equal or near-equal.

**Fix:** add one sentence to FINAL_REPORT §2.1: "Classical-control (CD) deployed evidence for H-CLS: retrain 1 only, n = 1–4 instances per arm; not compared."

### N4. Coordinator items carried over (no current impact)
- `code/validate.py` averages static P100 regardless of `matched`, and counts only working-tree TEST_GO files (round-1 N1 and N8). On T2 every static row is matched, so the verdict is unaffected.
- Pool-feasibility checks before pre-registration (admit-all WR ≥ target; static-knob sensitivity) should become a coordinator gate, as FINAL_REPORT §6.1 recommends. T1's s0.2 defect would have been caught by it.

## Contract §1 (Ising-centricity)
No claim exists, so this criterion is not triggered.
- **Ising component:** for the record, Y's decisive component (the F1 peak labels) is produced by parallel tempering.
- **Control:** the CP-SAT twin of the same formulation was run on dev (n = 10, 3 retrains) and on both pools, and is reported.
- **Interpretation:** FINAL_REPORT §4 states that the objectives tie, that the PT/CP-SAT deployed difference comes from which co-optimal label set each solver returns, and that no gain is attributed to better Ising optimization. That is the honest reading of the data.

## Summary
- **Leakage:** none. No test-pool, past-test or reserve sample was used for tuning or selection, and nothing touched samples 0.7–0.9.
- **Fail-closed order:** T1 was closed as spent and failed before its evaluation was read.
- **Rule and protocol changes:** T2's single post-commit change (unevaluable counts as not passed) was the one the round-1 validators required, and it was committed before T2's TEST_GO. No rule or protocol was changed after data were seen.
- **Reporting:** no row was dropped, the incident rows are kept, no extra seeds were run, and every rewritten ledger is lossless.
- **Fairness:** the comparisons share models, seeds, search ranges and code, and are configured as in WP9.
- **Reproduction:** every reported number I recomputed matches.
- **Remaining items:** only disclosure and wording fixes.

OPEN_FINDINGS=0
VALIDATOR_STATUS=PASS
