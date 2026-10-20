# PROTOCOL (3_autoresearch test spend #2, union family): pool T2 = Region4 s0.2–0.6. Conditional pre-registration

**Status:** final when committed. Written by the 3_autoresearch worker (run 20261020_004634) under `changes/3_autoresearch/documents/GOOD_RESULT.md`.

**Timing:** committed before any T1 or T2 test simulation, before any T1 outcome exists, and before the union dev finalist is known (its confirmation was running).

**When this test runs** (mechanically, `work/union_t2/src/chain_test_t2u.sh`). It runs only if all of the following hold, otherwise it writes `CHAIN_DONE` and stops without a TEST_GO (T2 not spent):
1. `work/union/results/dev_finalist.json` names a FINALIST (DEV_RULES R3 + R4, as for T1);
2. that finalist was tested on T1 (`work/t1u_region2/TEST_GO` exists, CHAIN_DONE written);
3. the T1 evaluation (`work/t1u_region2/results_test/evaluation.json`) has `good_result` = false. If T1 passed, T2 is not needed.

**Y and its control are the T1 configuration, fixed before T1 ran.** Nothing about Y, its hyperparameters or the arms is chosen from T1's outcome. Only the decision whether to spend a second pool depends on whether T1 passed.

**The pool** follows the second-spend rule (`result/LAB_NOTEBOOK.md`, 2026-10-20 04:56, written before any T1 test run).

TEST_GO (this directory, holding the commit hash and `POOL=T2`) is written only after this file is committed, only if G1_v5 passed, and only if this file is unchanged.

## 1. Pool and instances
- **T2** = Region4 (trace group 202110, 0.1%) samples 0.2, 0.3, 0.4, 0.5, 0.6 (n = 5), touched once. Samples 0.7 and above are never built or touched.
- **Jobs:** `work/union_t2/jobs_test.json` (sha256 `3bbf9fa365ab`), built by `src/make_jobs_t2.py` from the authors' release command rows. No constructed rows.
  - Baleen: Fig 9 variant "All on Partial Hit", experiment `20230412_XX_rerun2`;
  - RejectX and CoinFlip: the authors' rows of experiment `20230412_XX_rerun2` (Region4's only static rows).
- **Prerequisites built before this commit** (none read; frozen code):
  - `work/union_t2/inst_test/fullml_*` and `day1_*` dumps;
  - 60 F1 label sets `work/union_t2/labels/Region4_s0.{2..6}_{F1PT,F1CPSAT}_s{1..6}.npz`.

## 2. Configurations
**Identical to `work/t1u_region2/PROTOCOL.md` §2 (commit `76cf5c8d`) and its `ADDENDUM_R4.md`:**
- overlay v5: `work/union_t2/overlay/`, byte-identical to `work/union/overlay/`; `PATCH_v5.diff` sha256 `3cadbdf4a638`; G1_v5 PASS;
- arms A, B, A+α (`Aa-1.0`), B+α (`Ba-1.0`);
- Y = FINALIST ∈ {`XA-F1PT`, `XG-F1PT`} (Baleen's model A OR the F1-PT-label model X; κ = θ_X*/θ_A* and G = the day-1 q75 of load_10m, both from the training day; α = −1);
- control = its F1CPSAT twin;
- RejectX / CoinFlip, frozen code, the authors' probability, bisected only if it misses ±1%.

The code is `work/union_t2/src/` of this commit. It equals `work/union/src/` except for the work-dir constant and the T2 prep scripts.

**Matched write rate.** 35.599 MB/s ± 1%, θ by full simulation (at most 7 sims), (0, 1) for A/B and (0, 4] for the adaptive arms.

## 3. Retrains, unmatched runs, ledger
- k = 1, 2, 3 (new trainings: A, B, and X with label seed k).
- A cell with fewer than 3 matched retrains gets k = 4, 5, 6 until 3 are matched.
- Every evaluation is a row of `work/t2u_region4/trials_test.csv`; static replays go to `work/t2u_region4/results_test/static_baselines.csv`.

## 4. Pass rule and evaluator
The contract §4 rule (n = 5), computed by `work/union_t2/src/eval_test.py --pool T2`, identical to `code/validate.py`. For R ∈ {A, B, best α}:
- wins ≥ 4/5;
- mean(R − Y) > 2.5 × SE_retrain;
- no instance worse by more than 2.0;
- and Y below RejectX and CoinFlip.

If the rule passes, `result/GOOD_RESULT_CLAIM.json` is written (contract §5). Otherwise the negative result is recorded, the budget is exhausted, and `result/FINAL_REPORT.md` plus `result/STOP_EXHAUSTED` follow.

## 5. Known caveats
- **WP1 (published, offline):** Region4 had the smallest offline peak-aware headroom (−3 to −5% vs about −16% on Regions 5–7).
- Region4 uses the same "All on Partial Hit" prefetch variant as Region2.
- If this test runs, Y has already failed T1. It is a replication on a fresh pool, not a re-selection.

## 6. Run
```
cd changes/3_autoresearch/work/union_t2 && setsid nohup bash src/chain_test_t2u.sh >> logs/chain_test_t2u.out 2>&1 < /dev/null &
```
