# PROTOCOL v2: H5 (Ising-fitted admission-threshold table), Region1 test protocol: CONDITIONAL pre-registration

**Status:** FINAL. Written by Track E (WP10) on 2026-10-19 19:25, before any run on a Region1 test sample (s0.1–0.6) and before the E3 confirmation outcome was inspected.
- The E3 confirmation driver finished at 19:20. Its rows are in `trials_dev.csv`. `src/e3_eval.py` has NOT been run on them; no confirmation P100 was read.
- The finalist is not known at commit time. It is fixed by the already-written FINALIST RULE (`PROGRESS.md`, ≈17:32, before any E3 sim), computed mechanically by `src/e3_eval.py` from `trials_dev.csv`.
- **If that rule yields no finalist, no test runs.**
- The test runs only through `src/chain.sh`. The chain checks that this file is committed, then creates `TEST_GO`. The drivers refuse test samples without `TEST_GO`.

## 1. Finalist (conditional, deterministic)
- **Candidates:** `TA-pt` (arm A's models + PT table) and `TB-pt` (arm B's models + PT table).
- **The rule** (`PROGRESS.md`, FINALIST RULE, unchanged):
  - Screen gate: S1 > 0. Both candidates passed it (rep 1; `results/e3_screen.csv`).
  - Then, with 3 matched dev retrains per instance, against WP2's A+α and B+α:
    - (a) S3 = mean_i min((A+α)_i − X_i, (B+α)_i − X_i) > 0;
    - (b) ≥ 5/8 wins vs each of A+α and B+α;
    - (c) per region, mean (X − B+α) ≤ 0.5.
- **Tie-break among qualifiers:** larger S3, then more total wins (vs A+α plus vs B+α), then name order (`TA-pt` before `TB-pt`).
- **Output:** `results/finalist.json` gives `FINALIST` (F) and `CONTROL` (Fc = the same arm's classical `cd` table).

## 2. Instances
- **Test, touched once: Region1** (trace group 201910, 0.1% sampling), samples **0.1–0.6**.
- **Why not Region2.** The brief named Region2. Its authors' release CSV (`results_release.csv.gz`) has **no Baleen Fig 9 row for s0.2** and **no RejectX row for s0.1 and s0.2**, so the arms and baselines cannot be built from the authors' commands.
- **Why Region1.** Region1 has Baleen Fig 9 rows for every sample. The variant is "ML-Range on Partial Hit", experiment `20230421_alltraces_pfalways`, the same as Region5/H4. Its `20230410_static_pf` RejectX/CoinFlip rows exist for every sample.
- **Region3 was not used:** it lacks s0.4–0.6.
- Region1 has never been run by this project. WP1 used Regions 4–7.
- **Dry run, no verdict: Region1 s0**, 1 retrain, already done (`dryrun/trials_dryrun.csv`). Every step worked: train A/B, day-1 pack, PT/CD/exhaustive solve (PT = exhaustive optimum), table sims, convergence in 2 sims. P100: A 27.32, TA-pt 27.32, TB-pt 27.22. No fix was needed.
- **Reserve, untouched:** samples 0.7–0.9 of every region. No job or instance exists for them, and the code asserts this.

## 3. Configurations
- **Code.** Overlay v3 (`overlay/`, built by `rebuild_overlay.sh` from `PATCH_v3.diff`, sha256 `03f1523e688d`). That is `wp0_overlay/PATCH.diff` (`2a914eb589bb`) plus the SCOPE_v2_1b table flag. G1_v3 passed, and table == power law was bit-identical (`G1_v3.md`).
- **Commands.** As PROTOCOL_v2_H4 §3: the authors' per-sample Fig 9 TrainCommand/ReproduceCommand (`jobs_test.json`, `src/make_jobs_test.py`), path rewrite, `+ --eviction-policy LRU`, `- --offline-ap-decisions`.
- **Retrains.** k = 1, 2, 3, each a new overlay training (the artifact's own nondeterminism). Every adaptive arm re-uses retrain k of its base arm, so comparisons are paired.
- **Matched write rate.** 35.599 ± 1%, θ converged by full sims (WP9 code, at most 7). Range (0, 1) for A, B; **(0, 4]** for A+α, B+α and the table arms. Emulator seeding uses Region6's map (seeding only).

| arm | models | schedule | role |
|---|---|---|---|
| A | Baleen labels, `meta+block+chunk` | none | baseline |
| B | Baleen labels, `+load` | none | baseline |
| A+α (`Aa-1.0`) | A's retrain | `--ap-load-adapt-alpha -1` (ref 20, 10 min) | H4 arm |
| B+α (`Ba-1.0`) | B's retrain | α = −1 | H4 arm |
| **F** (finalist, `TA-pt` or `TB-pt`) | A's or B's retrain | `--ap-load-adapt-table` fitted by **PT** on that retrain's day-1 pack | **H5** |
| Fc (`TA-cd` / `TB-cd`) | same | table fitted by classical coordinate descent | classical control |
| RejectX, CoinFlip | none | authors' `20230410_static_pf` commands, FROZEN code (`src/prep.py static`), authors' probability, bisected only if it misses ±1% | baselines |

**Table fit (training window only, as in dev; no setting changed).**
- `src/e2_pack.py --mode test`, then `src/e2_solve.py --mode test --solvers pt cd ex`.
- Day-1 accesses only. K = 6 buckets at the day-1 load quantiles (0.25, 0.5, 0.75, 0.9, 0.97).
- Grid {0.25 … 4}. Hamiltonian = peak + 0.1·top5 + 0.02·Σ|log2 m| + 50·monotonicity violations.
- Hard budget repair with W1 from the pooled dev seeding map (a = −1.029, b = 1.1615; Region1 has no map).
- PT: 16 replicas, 10 s, seed = k. CD: 10 s, seed = k.
- A `cd` table that is scale-equivalent to the `pt` table defines the same policy family, so it re-uses the `pt` result (flagged `reused_from`).

## 4. Retrains, unmatched runs, ledger
- 3 retrains per (arm, instance): 6 arms × 6 instances × 3 = 108 evaluations (trainings: A, B × 18).
- A cell with < 3 matched retrains gets seeds 4, 5, 6 until 3 are matched. `src/wp10.py --mode test` does this automatically.
- Every evaluation, including failures, is one row of `trials_test.csv`. Every solve is a row of `results/solves_test.csv`.

## 5. Pass rule (as PROTOCOL_v2_H4 §5)
- P100 = `PeakServiceTimeUtil1`. Take the mean over matched retrains per instance, then over the 6 instances.
- **X vs R:** wins on ≥ 4/6 instances AND mean (R − X) > 2 SE, with SE = sqrt(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i)/6 (retrain level). The instance-level SE is reported and is not used.
- **H5 = YES iff F meets the rule vs A, vs B AND vs the better α arm** (the one of A+α, B+α with the lower mean test P100). F's mean must also be below RejectX's and CoinFlip's means. Where a static replay is unmatched, that holds both for the closest/authors' replays and for the closest replays with WR ≤ target·1.01 (the WP9 step rule).
- **Reported, no claim:**
  - F vs the other α arm; Fc with the same rule; F vs Fc (Ising vs classical, deployed);
  - A+α, B+α vs A, B (H4 on a new region);
  - P99, top-5, mean DT, WR, θ, first-access admission, peak-window admission;
  - solver ledger (PT vs CD vs exhaustive energies).
- **Evaluator:** `src/evaluate_test.py --finalist <F>` → `results_test/evaluation.json`. It was written before any test data. Run on WP9's published trials (`--no-static`), it reproduces WP9's numbers exactly (A+α vs A: 5/6, +1.155, SE 0.094 / 0.745; B+α vs B: 6/6, +1.887).

## 6. Known caveats (stated before the test)
- **E1: no training-window proxy was valid.** Within-retrain concordance with simulated P100 was 0.61–0.65 < 0.70, and even the simulator's own day-1 peak reached only 0.61. The table's day-1 fit is therefore a candidate generator, not a validated optimiser. The dev full-sim screen is the only evidence that selected F.
- **Ising and classical give the same tables.** On dev, PT reached the exhaustive optimum on 48/48 fits and CD on 46/48; the tables were scale-equivalent on 46/48. The Ising-vs-classical deployed comparison is expected to be mostly identical by construction.
- F is selected on 8 dev instances with 2 candidates. The dev margins are optimistic.
- The machine is shared with `<another project>`. That slows sims but does not change results.

## 7. Prerequisites (none read a test outcome)
| item | status |
|---|---|
| `jobs_test.json` (Region1 s0–0.6), `inst/fullml_Region1_*.npz` (frozen dumps) | ready |
| overlay v3 + G1_v3 | PASS (`G1_v3.md`) |
| dry run Region1 s0 | done (§2) |
| `src/evaluate_test.py` checked on WP9 trials | done |
| this file committed + pushed | this commit |

## 8. Launch (detached; `src/chain.sh`, idempotent)
```
cd changes/2_deployable_peak/wp10_schedule && setsid nohup bash src/chain.sh >> logs/chain.out 2>&1 < /dev/null &
```
The chain runs these steps in order:
1. Wait for the E3 driver to exit.
2. Run `e3_eval.py` → `results/finalist.json`.
3. If there is no finalist, write `results/CHAIN_DONE` and stop.
4. Otherwise, check that this file is committed and create `TEST_GO`.
5. Run the static replays, the dry run (resume) and the test (`wp10.py --mode test --arms A B Aa Ba <F> <Fc> --reps 1 2 3`).
6. Run `evaluate_test.py`.
7. Write `check_frozen` + the leak count → `results_test/integrity.txt`.
8. Write `results/CHAIN_DONE`.
