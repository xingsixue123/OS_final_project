# Addendum to PROTOCOL.md (T2, commit `1cda6af`): T1 closed as unevaluable

**Written:** 2026-10-20 07:04 (from `date`). Committed before any T2 TEST_GO and before any T2 simulation. PROTOCOL.md is unchanged.

**Situation:**
- The union finalist XA-F1PT was tested on T1 (TEST_GO `76cf5c8d`). T1 cannot be evaluated as pre-registered:
  - Region2_s0.2 cannot reach the target write rate for any arm (admit-all gives 11.5 MB/s);
  - reference arm A is short of 3 matched retrains on s0.1 and s0.5 after seeds 4–6.
- T1's `evaluation.json` therefore has no `good_result`.
- T1 is closed as **spent and failed** (`result/LAB_NOTEBOOK.md`, 07:05 entry, commit `539f39e`).

**The only change:** `work/union_t2/src/chain_test_t2u.sh`, step 2. The chain used to stop when T1's `good_result` was neither true nor false. It now treats a missing/None `good_result` (with T1's TEST_GO and CHAIN_DONE present) as "T1 not passed", as the round-1 validators (red team B1, integrity/statistics B1) required.

**What does not change:**
- Y = XA-F1PT and control = XA-F1CPSAT, exactly as fixed before T1 ran;
- the arms, hyperparameters, pool (Region4 s0.2–0.6), retrain rule (seeds 1–3, extra seeds 4–6), pass rule and evaluator;
- all T2 test code under `work/union_t2/src/` except that chain condition.

**Known open risk, disclosed and not fixed** (validator N2; a test-code change would need the coordinator's sign-off):
- In an extra-seed pass where Y or its control needs seed k but arms A and A+α do not, the shared model A_k could be trained by the Y spec with the `+load` feature subset.
- That fails closed: the overlay's feature-count assertions crash those sims, giving `__FAILED_` rows and no wrong number.
- After T2, every `logs/test/A_baleen_*/train.log` will be audited for `--ap-feat-subset meta+block+chunk`.

**Convergence code** (validator N1): unchanged, as pre-registered. Per-cell `n_sims`, repeated-θ rounds and unmatched counts will be reported.
