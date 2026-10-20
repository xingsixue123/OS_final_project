# PROTOCOL (3_autoresearch test spend #1): pool T1 = Region2 s0.1–0.6. Conditional pre-registration

**Status:** final when committed. Written by the 3_autoresearch worker (run 20261020_004634), under the contract `changes/3_autoresearch/documents/GOOD_RESULT.md`.
- It is committed before any T1 simulation and before the dev finalist is known.
- **The finalist is fixed mechanically** by `work/cls_table/src/chain_dev2.py`, which applies the already-written rules `result/DEV_RULES.md` R0–R2 to the dev ledger `work/cls_table/trials_dev.csv` and writes `work/cls_table/results/dev_finalist.json`.
- **If `FINALIST` is null, no test runs and no `TEST_GO` is written:** this protocol is then void and T1 is not spent.
- **`TEST_GO`** (this directory) is written only after this file is committed. It holds that commit hash and `POOL=T1`. The test drivers refuse to run without it.
- **Gate:** the test also requires `work/cls_table/results/g1v4_summary.json` with `G1_v4_pass` and `v4_adaptive_paths_pass` both true (`work/cls_table/G1_v4.md`). Otherwise no `TEST_GO` is written.

## 1. Pool and instances
- **T1** = Region2 (trace group 201910, 0.1% sampling), samples 0.1, 0.2, 0.3, 0.4, 0.5, 0.6 (n = 6), touched once. The reserve samples (0.7 and above) are never built or touched.
- **Why T1 first:** the pool-choice rule (`result/LAB_NOTEBOOK.md`, 2026-10-20 01:08, written before any pool job or dump existed).
- **Jobs:** `work/cls_table/jobs_test.json`, built by `src/make_jobs_t1.py` from the authors' release rows (command rows only, no metric).
  - Path rewrite as WP9/WP10: + `--eviction-policy LRU`, − `--offline-ap-decisions`.
  - Fig 9 Baleen variant: "All on Partial Hit", experiment `20230403_19traces`.
  - **Constructed rows** (the authors' release has no row for them): nearest sample of the same policy, variant and experiment, ties to the lower sample, sample-start substitution, the template's eviction age kept.
    - Baleen s0.2 ← s0.1 (EA 9223.515);
    - RejectX static s0.1 ← s0;
    - RejectX static s0.2 ← s0.3;
    - CoinFlip static s0.2 ← s0.1.
- **Instance dumps** (threshold seeding and the training-day packs only): `work/cls_table/inst_test/fullml_Region2_s0.{1..6}.npz`, frozen code, `src/prep.py dumps`.

## 2. Configurations
**Code: overlay v4** (`work/cls_table/overlay/`), built by `rebuild_overlay_v4.sh` from `PATCH_v4.diff` (9 files, sha256 `6dc6ef935e6f`):
- = `wp10_schedule/PATCH_v3.diff` (`03f1523e688d`) + `PATCH_v4_delta.diff` (`c1aff81239aa`), SCOPE amendment 1.2c (`work/cls_table/SCOPE_AMENDMENT.md`);
- G1_v4: `work/cls_table/G1_v4.md`.

All drivers and the evaluator are the files of this commit under `work/cls_table/src/`.

**Arms** (each Y/control arm re-uses retrain k of its base arm; comparisons are paired by retrain):
| arm (trials `arm` value) | models | admission threshold | role |
|---|---|---|---|
| `A` | Baleen labels, `meta+block+chunk` | none | baseline A |
| `B` | Baleen labels, `meta+block+chunk+load` | none | baseline B |
| `Aa-1.0` | A's retrain | `--ap-load-adapt-alpha -1` (ref 20, 10 min) | A+α |
| `Ba-1.0` | B's retrain | α = −1 | B+α |
| **Y** = FINALIST, one of `CB-pt`, `CB-ptm`, `CA-pt`, `CA-ptm`, `UB-ptm` | B's (CB, UB) or A's (CA) retrain | load × class table fitted by the **Ising solver (parallel tempering)** | the hypothesis |
| control = CONTROL, one of `CB-cd`, `CB-cdm`, `CA-cd`, `CA-cdm`, `UB-cdm` (the classical twin of Y) | same | the same energy solved by classical coordinate descent | classical control |
| RejectX, CoinFlip | none | the authors' `20230410_static_pf` commands (constructed rows above), FROZEN code, the authors' probability, bisected only if it misses ±1% | static baselines |

UB-ptm cannot become the finalist: it failed the R0 screen gate at 02:21, before this protocol was written. It is listed only for completeness.

**Class table** (C* arms; `src/cls_pack.py`, `src/cls_fit.py`), fitted per retrain k right after that retrain's training, on the TRAINING DAY only:
- Pack: day-1 accesses of the fullml instance, the retrain's admission-GBM scores, causal `load_10m`.
- Load buckets: K = 6, edges at the day-1 access quantiles (0.25, 0.5, 0.75, 0.9, 0.97).
- Classes: J = 2, end offset ≤ / > 8 MiB (`endoff`, class edge 8388608).
- Grid {0.25, 0.35, 0.5, 0.7, 1, 1.4, 2, 2.8, 4}; one-hot spins per cell (12 cells).
- Write budget W1: the day-1 emulated chunks of the plain model at the pooled seeding map (a = −1.029, b = 1.1615); hard repair.
- Energy H = peak_day1 + 0.1·top5_day1 + 0.02·Σ|log2 m| + 0.02·Σ_b|log2 m_big,b − log2 m_small,b| + 50·(load-monotonicity violations), plus, for the `m` variants, 50·[m_big,b > m_small,b].
- PT: 16 replicas, T ∈ [0.005, 1] geometric, 20 s, seed = k. CD: 20 s, seed = k.

**Pooled table** (UB arms): `work/cls_table/tables/dev/pool_loo_all_B_ptm.json` (sha256 `500959a0711b`) / `_cdm.json` (`3616023c6c88`), fixed now, on the test instance's own day-1 load edges.

**Matched write rate.** 35.599 MB/s ± 1%; the base θ is converged by full simulation (WP9/WP10 code, at most 7 sims), range (0, 1) for A and B, (0, 4] for every adaptive arm. Seeding uses Region6's map (seeding only).

## 3. Retrains, unmatched runs, ledger
- k = 1, 2, 3, each a new overlay training (the artifact's own nondeterminism). Trains are serialized by `2_deployable_peak/.train.lock`.
- A cell with fewer than 3 matched retrains gets seeds 4, 5, 6 until 3 are matched (automatic in `src/cls.py --mode test`).
- Every evaluation, including failures, is a row of `work/t1_region2/trials_test.csv`. Every table solve is a row of `work/cls_table/results/solves_test.csv`. Static replays go to `work/t1_region2/results_test/static_baselines.csv`.

## 4. Pass rule and evaluator
The contract §4 rule, computed by `work/cls_table/src/eval_test.py` (identical to `code/validate.py:check_claim`) → `results_test/evaluation.json`. For R ∈ {A, B, best α}, with best α = the one of A+α / B+α with the lower mean test P100:
- wins ≥ 4/6;
- mean(R − Y) > 2.5 × SE_retrain;
- no instance with Y worse than R by more than 2.0;
- and Y's mean P100 below RejectX's and CoinFlip's means.

**Reported (no pass/fail):** the control with the same rule; Y vs control (Ising vs classical); A+α and B+α vs A and B; secondary metrics.

If the rule passes, `result/GOOD_RESULT_CLAIM.json` is written in the contract §5 format. If not, the negative result is recorded and T1 is spent.

## 5. Known caveats (stated before the test)
- **No training-day proxy is valid** (WP10 E1). The table fit is a candidate generator; the dev screen and confirmation decided.
- **Dev selection.** The finalist is chosen among up to 5 candidates on dev, so its dev margins are optimistic.
- **Region2 is a 201910 trace,** like Region1, where no load-adaptive policy helped (WP10). The pool was fixed by the 01:08 availability rule, not by expected favourability.
- **Constructed rows** (§1) are a deviation from the authors' per-sample commands. They are applied identically to every arm.
- The machine is shared with `<another project>`. That slows sims; it does not change results.

## 6. Run (detached; idempotent)
```
cd changes/3_autoresearch/work/cls_table && setsid nohup bash src/chain_test_t1.sh >> logs/chain_test_t1.out 2>&1 < /dev/null &
```
The chain runs these steps in order:
1. Wait for `results/dev_finalist.json`. If FINALIST is null, stop.
2. Check G1_v4.
3. Check this file is committed, then write `TEST_GO` (commit hash, `POOL=T1`).
4. Static replays.
5. Test: `src/cls.py --mode test --arms A B Aa Ba <Y> <control> --reps 1 2 3`, plus extra seeds.
6. `src/eval_test.py`, then the integrity checks.
