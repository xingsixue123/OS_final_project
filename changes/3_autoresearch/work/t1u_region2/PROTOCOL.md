# PROTOCOL (3_autoresearch test spend #1, union family): pool T1 = Region2 s0.1–0.6. Conditional pre-registration

**Status:** final when committed. Written by the 3_autoresearch worker (run 20261020_004634) under `changes/3_autoresearch/documents/GOOD_RESULT.md`.
- **Timing:** committed before any T1 simulation of this family and before its dev finalist is known. The retrain-1 screen was still running; the confirmation had not started.
- **Relation to the earlier T1 protocol** (`work/t1_region2/PROTOCOL.md`, commit `96506745`, cls_table family): that protocol is void unless its dev finalist file names a finalist. Its candidate CB:pt fails the finalist rule (6/10 wins vs A+α; `result/LAB_NOTEBOOK.md`). No TEST_GO was written and no T1 sample was simulated, so T1 is still unspent. Only one of the two can write a TEST_GO for T1:
  - this chain refuses if `work/t1_region2/TEST_GO` exists;
  - the earlier chain stops without a TEST_GO when its finalist file is null.
- **The finalist is fixed mechanically** by `work/union/src/chain_union_dev.py`, which applies `result/DEV_RULES.md` R3 (the R0 screen gate and finalist rule, unchanged) to `work/union/trials_dev.csv` plus the published/WP2 and cls_table reference rows, and writes `work/union/results/dev_finalist.json`.
- **If FINALIST is null, no test runs and no TEST_GO is written.**
- **TEST_GO** (this directory) is written by `work/union/src/chain_test_t1u.sh`. It requires all of:
  - a finalist;
  - `work/union/results/g1v5_summary.json` with `G1_v5_pass` and `v5_paths_pass` true;
  - this file committed and unchanged since its commit.

## 1. Pool and instances
Identical to the earlier T1 protocol §1. In short:
- **Pool:** Region2 (201910, 0.1%) samples 0.1–0.6, n = 6, touched once.
- **Jobs:** `work/union/jobs_test.json` = `work/cls_table/jobs_test.json` (sha256 `52d09103502c`), the authors' Fig 9 "All on Partial Hit" commands.
- **Constructed rows:** Baleen s0.2 ← s0.1; RejectX s0.1 ← s0, s0.2 ← s0.3; CoinFlip s0.2 ← s0.1.
- **Prerequisites built before this commit** (no outcome read):
  - `inst_test/fullml_*` (seeding only);
  - frozen day-1 dumps `work/union/inst_test/day1_Region2_s0.{1..6}.npz`;
  - F1 label sets `work/union/labels/Region2_s0.{1..6}_{F1PT,F1CPSAT}_s{1..6}.npz`, whose statistics files were not opened.
- Samples 0.7 and above are never built or touched.

## 2. Configurations
**Code: overlay v5** (`work/union/overlay/`) = `work/union/PATCH_v5.diff` (9 files, sha256 `3cadbdf4a638`) = `work/cls_table/PATCH_v4.diff` (`6dc6ef935e6f`, G1_v4 PASS) + `PATCH_v5_delta.diff` (`6a0eb8a6ca66`, SCOPE amendment 1.2d, `work/union/SCOPE_AMENDMENT.md`); G1_v5: `work/union/G1_v5.md`. All drivers and the evaluator are the files of this commit under `work/union/src/`.

| arm (trials `arm` value) | models | admission | role |
|---|---|---|---|
| `A` | A_k: Baleen labels, `meta+block+chunk` | θ | baseline A |
| `B` | Baleen labels, `meta+block+chunk+load` | θ | baseline B |
| `Aa-1.0` | A_k | θ·g, α = −1 (ref 20, 10 min) | A+α |
| `Ba-1.0` | B_k | α = −1 | B+α |
| **Y** = FINALIST ∈ {`XA-F1PT`, `XG-F1PT`} | A_k (the same retrain as arm A) + X_k = the F1-**PT**-label model | **admit iff s_A > θ·g OR s_X > κ·θ·g** (`XG`: the second clause only where load_10m ≥ G); α = −1 | the hypothesis |
| control = `XA-F1CPSAT` / `XG-F1CPSAT` (the twin of Y) | A_k + the F1-**CP-SAT**-label model | same | classical control |
| RejectX, CoinFlip | none | the authors' `20230410_static_pf` commands (constructed rows above), FROZEN code, the authors' probability, bisected only if it misses ±1% | static baselines |

**X_k (Ising component):**
- Labels = the phase-1/WP2 **F1 min–max day-1 selection** (QUBO over episodes; `explore/q2`, true day-1 peak, single level f = 1), solved on `day1_<inst>.npz`:
  - by **parallel tempering** with the frozen 10 s configuration of `explore/q2/plan_F1.json` (`labels.py`, design `F1PT`, seed = k, 8 numba threads);
  - control: the same formulation by CP-SAT (`F1CPSAT`, 10 s).
- The labels are applied in training by `PolicyPeakBaleen4` (the strict-prefix Baleen fill re-applied in-run), and the overlay trainer runs with `--ap-feat-subset meta+block+chunk+load`. Exactly WP2/WP3/WP9 arm D.

**κ and G (training day only, `union.py:union_params`):**
- κ = θ_X*/θ_A*: the two models' day-1 emulated thresholds at the same day-1 budget (SchedEmu, pooled seeding target, a = −1.029, b = 1.1615);
- G = the day-1 access-level 0.75 quantile of load_10m.

**Matched write rate.** 35.599 MB/s ± 1%; base θ converged by full simulation (at most 7 sims), range (0, 1) for A and B, (0, 4] for every adaptive arm.

## 3. Retrains, unmatched runs, ledger
- k = 1, 2, 3. Each arm A/B training is a new overlay training. Each X_k is a new training on label seed k. Trains are serialized by `2_deployable_peak/.train.lock`.
- A cell with fewer than 3 matched retrains gets k = 4, 5, 6 (label seeds 4–6 exist) until 3 are matched (`union.py --mode test`).
- Every evaluation, including failures, is a row of `work/t1u_region2/trials_test.csv`. Static replays: `work/t1u_region2/results_test/static_baselines.csv`.

## 4. Pass rule and evaluator
The contract §4 rule, computed by `work/union/src/eval_test.py` (identical to `code/validate.py:check_claim`) → `results_test/evaluation.json`. For R ∈ {A, B, best α}, with best α = the one of A+α / B+α with the lower mean test P100:
- wins ≥ 4/6;
- mean(R − Y) > 2.5 × SE_retrain;
- no instance with Y worse than R by more than 2.0;
- and Y's mean P100 below RejectX's and CoinFlip's means.

**Reported (no pass/fail):** the control with the same rule; Y vs control (Ising vs classical labels); A+α and B+α vs A and B; secondary metrics.

If the rule passes, `result/GOOD_RESULT_CLAIM.json` is written in the contract §5 format with:
- `ising_component` = "F1 min-max day-1 peak-label QUBO solved by parallel tempering (labels of the union's second model)";
- `classical_control_arm` = the control.

## 5. Known caveats (stated before the test)
- **The F1 labels have failed twice on test as a stand-alone model** (WP3, WP9: catastrophic unadmitted scan peaks). The union is designed against exactly that failure, but dev cannot show that it removes it.
- **Dev selection:** the finalist is chosen among 2 union candidates (after 5 cls_table candidates failed), so dev margins are optimistic.
- **Region2 is a 201910 trace.** On Region1 (WP10 test) no load-adaptive policy helped. The pool was fixed by the 01:08 availability rule.
- **Constructed rows** are a deviation from the authors' per-sample commands, applied identically to every arm.

## 6. Run (detached; idempotent)
```
cd changes/3_autoresearch/work/union && setsid nohup bash src/chain_test_t1u.sh >> logs/chain_test_t1u.out 2>&1 < /dev/null &
```
The chain runs these steps in order:
1. Wait for `results/dev_finalist.json`. If FINALIST is null, stop.
2. Check G1_v5.
3. Check this file is committed and unchanged. Refuse if `work/t1_region2/TEST_GO` exists. Then write `TEST_GO` (commit hash, `POOL=T1`).
4. Static replays, then the test: `src/union.py --mode test --arms A B Aa Ba <Y> <control> --reps 1 2 3`, plus extra seeds.
5. `src/eval_test.py`, then the integrity checks.
