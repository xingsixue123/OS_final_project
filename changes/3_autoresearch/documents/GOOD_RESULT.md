# What counts as a "good result" (contract for the auto-research loop)

Fixed by the coordinator on 2026-10-19 **before the loop starts**. The worker may not edit this file; the deterministic validator checks its sha256.

A good result is a **claim file** `changes/3_autoresearch/result/GOOD_RESULT_CLAIM.json` that `code/validate.py` recomputes and confirms from raw trial rows. Every condition below must hold.

## 1. The method must be Ising/QUBO-centric
- The configuration Y under test gets its decisive component from an Ising/QUBO formulation solved by an Ising-family solver (PT, SB, EIM, SA on spins, QAIA, ...). Qualifying components: admission labels, threshold schedule, selection, or another decision.
- The claim names that component, and it names a classical-solver control arm of the same formulation (CP-SAT, LP, greedy, CD). The control's result is reported.
- Beating the classical control is **not** required for a good result. A good result only shows that the Ising/QUBO formulation helps deployed Baleen.

## 2. Fair deployed evaluation
- **Pipeline:** BCacheSim, through the reviewed overlay (`wp0_overlay`) or a documented overlay extension. Any extension needs a SCOPE amendment file plus a G1 bit-exact default-equivalence report, as `wp10_schedule/G1_v3.md`.
- **Operating point and metric:**
  - write rate matched at 35.599 MB/s ± 1%, threshold converged by full simulation;
  - cache 366.475 GB;
  - metric `PeakServiceTimeUtil1` (P100).
- **Retrains:** ≥ 3 matched retrains per (arm, instance), every row logged, nothing excluded silently.

## 3. A fresh, pre-registered test
**Test pools** (never run deployed by this project). At most **2 test spends** in total, each on one pool:
- **T1:** Region2 (201910) samples 0.1–0.6
- **T2:** Region4 (202110) samples 0.2–0.6
- **T3:** Region3 (201910) samples 0.1–0.3. Small; allowed only as the second spend.

**Before the test** (the validator enforces all of these):
- The test directory holds `PROTOCOL.md`, committed to git; the commit must exist.
- `TEST_GO` contains that commit hash, and its mtime is later than the commit time.
- The protocol fixes:
  - configuration Y and every hyperparameter;
  - the instances, arms, rule and evaluator;
  - any selection in the protocol (e.g. "the finalist chosen by rule R from dev ledger L") must be mechanical.

**Data that is never used:**
- **Never touched:** samples 0.7–0.9 of every region (final reserve).
- **No tuning or selection** on:
  - any WP3/WP9/WP10 test sample (Region6/7 ≥ 0.4, Region5 ≥ 0.1, Region1 ≥ 0.1);
  - any T-pool sample.

**Dev data allowed for search:**
- Region6/7 samples 0–0.3;
- Region5 s0 and Region1 s0;
- everything already published in the repo.

## 4. The pass rule (stricter than earlier protocols: a 2-test Bonferroni correction plus a tail guard)
Write ref − Y as the per-instance mean P100 difference over matched retrains, with n instances (n = 6 for T1, 5 for T2, 3 for T3). Y must meet **all** of these against **each** reference R in {A, B, best of (A+α, B+α)}:

1. **Wins:** Y's mean P100 is lower than R's on ≥ ⌈2n/3⌉ instances.
2. **Margin:** mean(R − Y) > **2.5 ×** SE_retrain, where SE_retrain = sqrt(Σ_i s²_Y,i/n_Y,i + s²_R,i/n_R,i)/n.
3. **Tail guard:** no instance has Y worse than R by more than 2.0 util-points.

In addition:
- Y's mean P100 must be below RejectX's and below CoinFlip's (frozen replays).
- The best α arm is chosen by mean P100 on the same test instances. This is the toughest comparison and is computed by the validator.
- **Arm definitions:**
  - A = Baleen labels, original features;
  - B = Baleen labels + `load`;
  - A+α / B+α = A or B with the load-adaptive threshold α = −1, threshold search (0, 4].
  - All arms run with the same seeds and pipeline as WP9.

## 5. Claim file format (`result/GOOD_RESULT_CLAIM.json`)
```json
{"config": "...", "ising_component": "...", "classical_control_arm": "...",
 "test_dir": "changes/3_autoresearch/work/<test dir>", "protocol_commit": "<hash>",
 "trials_csv": "<path relative to repo>", "arm_names": {"Y": "...", "A": "...", "B": "...", "A+alpha": "...", "B+alpha": "...", "control": "..."},
 "static_baselines_csv": "<path>"}
```
- **Trials CSV columns:** `arm`, `inst`, `rep`, `matched`, `p100`, `wr` at least. The `arm` value must equal the `arm_names` value.
- **Static CSV columns:** `instance`, `method` (RejectX / CoinFlip), `p100`.
- The validator recomputes every condition. Prose cannot satisfy it.

## 6. Honest outcomes are acceptable
If the budget is spent and no configuration passes, the loop ends with `result/FINAL_REPORT.md` stating the negative result. Repeating tests, re-defining pools or changing this rule after seeing data is forbidden and fails validation.
