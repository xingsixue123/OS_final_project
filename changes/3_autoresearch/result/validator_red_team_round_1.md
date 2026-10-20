# Red-team validator, run 20261020_004634, round 1

**Reviewer role:** an independent, skeptical check for selection bias, leakage and p-hacking. I edited no worker file and made no git writes.

**State reviewed** (2026-10-20, about 06:35–06:50 EDT):
- No claim file exists.
- One test has been spent: T1, `work/t1u_region2`. The protocol was committed at 04:36:45 (`76cf5c8d`) and TEST_GO was written at 06:26:50. The T1 test is still running; `trials_test.csv` had 63 rows at review time.
- T2 has a conditional protocol (`1cda6af`) and has not been spent.

**Verdict:** the process so far is mostly clean.
- No leakage or post-hoc selection was found.
- The dev finalist reproduces exactly from the raw rows.

**One blocking defect is open:** the pre-registered T1 pool contains an instance, Region2 s0.2, that no arm can match. T1 therefore cannot produce a valid result. It also leaves the next step undefined at a point where test data have already been seen.

## What I checked

| check | evidence | result |
|---|---|---|
| TEST_GO vs protocol commit | TEST_GO mtime 06:26:50 > commit `76cf5c8d` 04:36:45. `git diff 76cf5c8 -- work/t1u_region2/PROTOCOL.md` is empty. | OK |
| Protocols edited after commit | t1_region2, t1u_region2 and t2u_region4 `PROTOCOL.md` are all unchanged since their commits. `ADDENDUM_R4.md` was edited once after its commit (see N2). | OK |
| Only one TEST_GO, never re-spent | `git log --diff-filter=A -- 'work/*/TEST_GO'` returns only `t1u_region2/TEST_GO` (f74bf8b). `work/t1_region2` has CHAIN_DONE and no TEST_GO, with no trials file. `cls_table/results_test/` holds only `cfg_prep/`. | OK |
| Code changed after the union protocol commit | `union/src/cls.py`, `union.py` and `chain_union_dev.py` changed in 4e25e7e. The `cls.py` and `union.py` edits are gated on `C.MODE == "dev"`, so the test code paths are unchanged. `write_claim.py` and `supp_rejectx.py` are new and do not touch the test runs. | OK |
| Times of DEV_RULES vs data | The worker transcript (`output/auto_runs/.../worker_events_round_1.jsonl`, UTC) has the Write/append of R0 at 04:56:42Z = 00:56:42 EDT, R1 at 01:04:53, R2 at 01:42:38, R3 at 03:56:47 and R4 at about 04:48. Each precedes the simulations it governs. | OK (see N3) |
| Test-pool data read before TEST_GO | Before TEST_GO the transcript shows only `ls`/`wc` on `union/labels`, `inst_test` and the logs. No label-statistics file or dump content was printed. The release reads printed command-row existence and flags, never a metric column. | OK |
| Reserve samples 0.7–0.9 | No file, job, dump or simulation exists for them. `make_jobs_t1.py` restricts templates to ≤ 0.6. The `RESERVE_RE` scan is clean. One printed listing showed that their *rows exist* (N6). | OK, informational |
| Ledgers | No deleted line in the git history of `cls_table/trials_dev.csv`, `union/trials_dev.csv` or `t1u_region2/trials_test.csv`. The working-tree diff of `trials_test.csv` is only a header extension (`x_model,kappa,gate`) plus float repr; both committed rows are present and unchanged. The `__FAILED_` row (UB-cdm) is kept, and unmatched rows are kept. | OK |
| Extra seeds | Union dev candidates: 30 rows each, every rep ≤ 3, 0 unmatched, so R4 never fired. Test: reps 1–2 so far. | OK |
| Dev finalist recomputed independently | From the WP2 trials (A, B, A+α = Aa ∪ Ax, B+α = Ba ∪ Bx), the cls_table trials (Region1_s0 / Region5_s0 references) and the union trials, I get best α = A+α (36.162 vs 36.618). XA:F1PT vs A: 10/10, +1.423, SE 0.187; vs B: 9/10, +1.408, 0.193; vs A+α: 7/10, +0.802, 0.183, worst −0.822. XG:F1PT: 10/10, 8/10, 7/10, +0.632, worst −1.579. The tie-break picks XA. This equals `union/results/dev_finalist.json`. | OK, mechanical |
| Fair arms on test | Y = A_k (the same retrain as arm A) OR X_k (label seed k). Threshold search range is (0, 1) for A and B and (0, 4] for every α/adaptive arm, with the same 7-sim cap and ±1% match tolerance. All arms use overlay v5 (G1_v5 PASS, bit-identical on the default and α paths). | OK |

## Blocking finding

### B1. T1 contains an instance that no arm can match, so T1 can never be evaluated, and the protocol does not say what happens next

**Evidence**
- `work/t1u_region2/trials_test.csv`, all 12 Region2_s0.2 rows so far (lines 2, 3, 6, 8, 20, 27, 32, 37, 42, 45, 53, 63; A, Aa-1.0, B, Ba-1.0, XA-F1PT and XA-F1CPSAT for r1 and r2):
  - each has `threshold = 0.0001` (the search floor, i.e. admit everything), `n_sims = 7`, `matched = False`;
  - each has `wr = 11.509735` MB/s, against a target of 35.599;
  - P100 is the same for every arm (189.07).
- Admitting everything cannot reach the target write rate. More retrains (seeds 4–6) cannot change this, because the write rate at threshold 0 does not depend on the model.
- The static replays fail the same way. `results_test/static_baselines.csv` line 3 has RejectX s0.2 at WR 2.0, P100 240.6; line 9 has CoinFlip s0.2 at WR 11.1, P100 223.7, unmatched after 15 sims.
- **Consequences:**
  - `code/validate.py:check_claim` returns "arm … has < 3 matched retrains on Region2_s0.2", so no T1 claim is possible whatever the other 5 instances show.
  - `work/union/src/eval_test.py:59` (`if missing:`) writes `evaluation.json` **without** a `good_result` key.
  - `work/union_t2/src/chain_test_t2u.sh:32` then stops: "T1 evaluation incomplete (None) -> stop for inspection".
  - `result/STATUS.md:5-8` ("Next round") covers only `good_result` true or false, not this case. So round 2 must make an unplanned decision after T1 outcomes have been seen.
- **This was foreseeable from data that are not outcomes, before the protocol commit:**
  - The authors' release has **no Region2 s0.2 row at the default operating point** (Target DWPD 7.5, 366.47 GB) for any policy. Its s0.2 rows exist only at DWPD 1.0, 2.5 and 3.75, or at 50/100 GB. The worker's own query at 01:03 EDT (transcript 05:03:21Z) printed the `Target DWPD` column for these rows. The missing canonical rows are what `canonical()` produces through its `DWPDNotFar` / `Target DWPD == 7.5` filter: the authors did not, or could not, run s0.2 at this write rate.
  - `cls_table/inst_test/fullml_Region2_s0.2.npz` is 362 KB, against 600–761 KB for s0.1 and s0.3–0.6 (built 01:10).
  - The day-1 label statistics committed in `76cf5c8` (for example `union/labels/Region2_s0.2_F1PT_s1.json`) show n = 164 episodes against 1285–1984 for the others, `use_frac` 0.31, labels identical to Baleen's, and 49 zero-value labels.
- The protocol constructed this row instead (`t1u_region2/PROTOCOL.md:19`, "Baleen s0.2 ← s0.1"). Its caveats (§5, line 69 ff.) do not mention feasibility.
- The worker noticed that s0.2 is degenerate for RejectX (`LAB_NOTEBOOK.md:356`), but not that it is degenerate for every arm.

**Why this is blocking.** Nothing improper has happened yet. But the loop now faces an open decision, made after seeing T1 data, about how to treat an unevaluable pre-registered test. Each of the obvious "repairs" is outcome-informed re-definition, which contract §6 forbids:
- dropping s0.2 and evaluating n = 5 (wins ≥ 4);
- relaxing `matched` for s0.2 because all arms tie;
- counting ties;
- treating T1 as "not really spent" and re-registering a T1 test;
- choosing a different Y for T2.

The deterministic validator would reject a T1 claim anyway. The risk lies in the T2 decision and in how T1 is reported.

**Required fix.** Commit it as a dated note in `LAB_NOTEBOOK.md` and `STATUS.md` **before** `evaluation.json` is read or any T2 action is taken. Do not edit PROTOCOL.md.
1. T1 is **spent and failed (closed as unevaluable)**:
   - Region2_s0.2 stays in the pool;
   - the `matched` rule is not relaxed;
   - no seed beyond 6 is run;
   - T1 is not re-registered or re-spent.
2. The T1 report shows every row, including s0.2. Any 5-instance summary must be labelled descriptive and non-confirmatory, and must never be called a pass.
3. Amend `work/union_t2/src/chain_test_t2u.sh` so that a missing or `None` `good_result` counts as "T1 not passed".
   - Commit the change before any T2 TEST_GO.
   - Change only that condition. Do not touch PROTOCOL.md, Y, the control, the arms or the pool.
   - Then let T2 run exactly as pre-registered (same Y = XA-F1PT, control XA-F1CPSAT).
4. Optional: let the T1 chain finish its pre-registered seeds 4–6 rather than killing it. If it is stopped instead, record that it was stopped and why.

## Non-blocking findings (fix before the claim or the final report)

### N1. The protocol's static baselines on T1 are unmatched, and the pass rule never checks `matched` for static rows
**Evidence**
- `static_baselines.csv`: all 6 RejectX rows have `matched=False` (WR 21.2 / 2.0 / 36.5 / 31.7 / 25.4 / 29.3), and so does CoinFlip s0.2 (WR 11.1).
- `code/validate.py:189-196` and `eval_test.py` average `p100` over all static rows regardless of `matched`. So "Y below RejectX / CoinFlip" is satisfied trivially by the 240.6 and 223.7 values on s0.2.
- The supplementary `supp_rejectx.py` was designed after T1 static outcomes were seen (`LAB_NOTEBOOK.md:344-356`), which is acceptable because it is labelled non-protocol. It also failed to match on 5 of 6 instances (`results_test/supp_rejectx.csv`): the window factor does not move the write rate.

**Fix**
- Any report must state that the static comparisons on T1 are uninformative, and give their matched status.
- `write_claim.py` correctly points at `static_baselines.csv`. Never substitute `supp_rejectx.csv`.
- For the coordinator: consider having `validate.py` require `matched` static rows, or flag them. That is outside the worker's remit.
- T2's `20230412_XX_rerun2` rows use factors 0.16–0.32, where the knob works, so this should not recur there.

### N2. The union selection procedure was changed after the union T1 protocol commit, which itself came after the first union screen results were read
**Evidence**
- The union protocol was committed at 04:36:45, after the worker had read 9 of 16 union retrain-1 results, which were large and positive (`LAB_NOTEBOOK.md:227-231`).
- Twelve minutes later, R4 (`DEV_RULES.md:83`), `ADDENDUM_R4.md` and the matching `chain_union_dev.py` edit (4e25e7e) changed the mechanical finalist step. The change was motivated by an outcome: CB:pt was ruled ineligible.
- `ADDENDUM_R4.md` was edited again after its own commit (6d4a7a3: its "Written" line changed from ≈04:50 to 04:48).
- **Impact: none in fact.** All 60 candidate cells were matched on retrains 1–3, R4 never fired, and the finalist reproduces without it.

**Fix**
- State this in the final report.
- From now on, put the extra-seed rule and the whole selection procedure in a protocol before it is committed, and never edit a committed protocol or addendum. A correction goes in a new dated file.

### N3. DEV_RULES R0–R2 had no git attestation until 02:23, and rule headers were edited with `sed`
**Evidence**
- `DEV_RULES.md` first appears in commit 9650674 (02:23:37), after the screen results had started arriving.
- Its timing claims are confirmed only by the worker transcript, which I checked (see the table above).
- The headers were first written with guessed times and then rewritten in place: R0 01:20→00:56, R1 01:14→01:04, R2 01:43→01:42, R3 03:58→03:56, R4 04:52→04:48 (transcript lines with `sed -i 's/^## R…`). This contradicts the file's own rule, "rules are never edited after the fact". The rule text itself did not change.

**Fix**
- Commit each rule the moment it is written, so the commit time is the attestation.
- Record times from `date` instead of guessing.
- Never rewrite a dated rule; append corrections.

### N4. The Ising-versus-classical evidence is thin, and the solvers tie on the objective
**Evidence**
- PT and CP-SAT reach the **same F1 objective** on most instances:
  - Region1_s0: `label_peak_util` 15.5827 for both, all seeds;
  - Region2 s0.1–0.6, seed 1: identical for every instance;
  - Region5_s0: within 0.1–0.3%, with CP-SAT *lower* on 2 of 3 seeds (`union/labels/*_F1PT_s*.json` vs `*_F1CPSAT_s*.json`).
- The label sets differ only among co-optimal or near-optimal solutions:
  - Jaccard vs Baleen on Region2 s0.1 is 0.72 for PT and 0.92 for CP-SAT;
  - the PT label set varies by seed, while CP-SAT returns the same set for every seed on Region1_s0.
- So the dev gap XA:F1PT vs XA:F1CPSAT (retrain 1 only: Region6 s0 38.73 vs 42.73, s0.1 34.66 vs 43.69) is a tie-breaking / degeneracy effect of the solver, not better QUBO optimization.
- `LAB_NOTEBOOK.md:325` ("The same F1 formulation, solved by PT, deploys much better here") rests on retrain 1, n = 8.
- The controls' confirmation (`union/queue_dev2_controls.txt`: retrains 2–3 on DEV8 and 1–3 on Region1_s0 / Region5_s0) and the cls_table controls (`queue_report.txt`) were never run. The ledger has CA-cd 1, CB-cd 4, CA-cdm 3 and CB-cdm 3 rows.

**Fix:** in any claim or final report:
1. Run the queued control confirmations, or label the control evidence as retrain 1 only, n = 8.
2. Report that the PT and CP-SAT objectives are equal.
3. Do not attribute any gain to better optimization by the Ising solver.

Contract §1 is still met literally: Y's labels are produced by PT, and the CP-SAT twin is named and reported.

### N5. The worker has now seen T1 outcomes, so T2 must be locked
- The worker read T1 baseline convergence lines (transcript 10:29Z) and static results.
- The T2 protocol fixes Y = the union finalist. Any change to T2's Y, arms or pool now would be informed by T1 and is forbidden.
- **Fix:** none needed beyond B1 step 3. Re-state this in STATUS.md.

### N6. Reserve rows appeared in a printed listing
- The 01:06 query (transcript 05:06:14Z) printed Region2 release-row *existence* for SampleStart 0.7, 0.8 and 0.9: the prefetch label and experiment name only. No metric, trace, dump or simulation was involved.
- `best_baleen_prefetch` (the authors' Fig 9 rule, as in WP9/WP10) averages the authors' P100 over all samples of a trace, including 0.7–0.9. It defines the Baleen baseline the same way for every arm, and the worker printed only the label.
- **Fix:** filter `SampleStart <= 0.6` before printing release rows.

### N7. The ledgers are rewritten in full, not appended
- `trials_test.csv` is re-serialized by pandas, so float repr and header columns change.
- I verified that no committed row was lost. Even so, a full rewrite makes silent deletion harder to detect.
- **Fix:** commit a ledger snapshot at every round end; this round did so in f74bf8b. In the final report, list the row counts per (arm, instance), including unmatched and `__FAILED_` rows.

### N8. The validator's view of test spends is only the working tree
- `validate.py:test_dirs` sees only TEST_GO files that currently exist.
- The T1 TEST_GO is safely committed (f74bf8b), so deleting it would show in git history.
- **Fix (coordinator):** also count TEST_GO files ever added in `git log --diff-filter=A`.

## Summary
- No test or reserve leakage was found.
- No ledger row was dropped.
- No extra seeds were run beyond the rules.
- The finalist selection was mechanical and reproduces exactly.
- The arms are configured fairly.
- The open issue (B1) is a defect in the pre-registration: T1 includes Region2 s0.2, which cannot reach the target write rate, so T1 is unevaluable. The fail-closed handling must be committed before the next step.

OPEN_FINDINGS=1
VALIDATOR_STATUS=FAIL
