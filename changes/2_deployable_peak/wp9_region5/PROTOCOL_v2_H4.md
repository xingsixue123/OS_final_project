# PROTOCOL v2: H4 (load-adaptive threshold on Baleen's own models), Region5 test protocol

**Status: FINAL as written by Track D (WP9) on 2026-10-16, before any run on Region5 s0.1–s0.6.** The coordinator commits this file, then creates `wp9_region5/TEST_GO`; the driver (`src/wp9.py --mode test`) refuses to start without that file. Nothing here was chosen by looking at Region5 deployed outcomes: the only deployed Region5 run so far is the s0 pipeline dry run (arm A, 1 retrain; `PROGRESS.md`), which is not a test instance.

Source of the hypothesis: `wp8_trackC/PLAN_C.md` §6 (coordinator addendum, commit `d10e572`). This file only makes it executable; it changes no rule fixed there. Track C produced no finalist (`wp8_trackC/RESULTS_dev.md`), so there is no arm Y (PLAN_C §6, second bullet).

## 1. Hypotheses

**H4 (primary, pre-registered in PLAN_C §6).** On Region5, the load-adaptive admission threshold applied to Baleen's own models, **A+α** (Baleen's labels, original features `meta+block+chunk`, α = −1), beats **both**:
- arm A: Baleen's labels, original features;
- arm B: Baleen's labels + the `load` feature;

at matched write rate, with ≥ 3 matched retrains each, and is below RejectX and CoinFlip.

**Secondary (reported with the same rule, no claim).** B+α (arm B's retrains + α = −1) vs A and vs B.

**Ising record (no pass/fail beyond reporting the rule).** X1 = F1PT Ising labels + `load` + α = −1 (the H3′ primary configuration, unchanged) vs A, vs B and vs A+α.

## 2. Instances

- **Test, touched once, after this file is committed:** Region5 (trace group 20230325, 0.1% sampling), samples **0.1, 0.2, 0.3, 0.4, 0.5, 0.6**: 6 instances. None has been run deployed, tuned on or inspected through a deployed model. WP1 used them only OFFLINE (H1′ breadth: OPT on full traces).
- **Pipeline dry run, not part of any verdict:** Region5 s0, arm A, 1 retrain (done; `PROGRESS.md`).
- **Reserve, untouched:** samples 0.7–0.9. No job, instance dump or label set exists for them (`src/make_jobs_test.py` asserts it; the driver refuses them).

## 3. Configurations (all overlay arms through the reviewed overlay `wp0_overlay/overlay`, `PATCH.diff` sha256 `2a914eb589bb`, unchanged since `f79808f`)

### Common to every arm

**Commands.**
- Base: the authors' per-sample Fig 9 Baleen TrainCommand / ReproduceCommand from `results_release.csv.gz`. For Region5 the Fig 9 variant (lowest mean P100 over the trace's canonical Baleen rows, `add_pfbest`) is **"ML-Range on Partial Hit"**, experiment `20230421_alltraces_pfalways`: simulator `--prefetch-when partial --prefetch-range acctime-episode-predict`, with the ML-Range prefetch models trained by the same train command (`--train-models admit prefetch`). One row per sample; `src/make_jobs_test.py` asserts the variant and the experiment.
- Path rewrite, `+ --eviction-policy LRU`, `- --offline-ap-decisions`, exactly as `explore/common/src/make_jobs.py` (copy of `0_reproduce/repro/common.py` in `src/rc_common.py`, unmodified apart from the CSV path).
- On top of that, only the arm's options below, plus `--exp`/`-o`/`--job-id` and `--ap-threshold`. Jobs: `jobs.json` (Region5 s0 and s0.1–s0.6 only). The OPT-row eviction ages equal WP1's independent extraction for all 7 instances.

**Retrains.**
- Retrain k = a new episode generation (the artifact's own nondeterminism, SCOPE_v2 §1a), new GBMs (admission and ML-Range prefetch), and, for X1, label-solver seed k.
- A+α and B+α re-use retrain k of A and B; X1 re-uses retrain k of its base D:F1PT (same labels and features, trained without α). The threshold is a simulation-only option, so these comparisons are paired.

**Matched write rate.** Target 35.599 MB/s ± 1%. `--ap-threshold` converged by full simulation: sequential, seeded by the emulator, at most 7 sims (code: `src/wp9.py`, WP3's convergence code unchanged).
- **Threshold search range:** (0, 1) for A and B; **(0, 4] for A+α, B+α and X1** (PLAN_C §6 fixes (0, 4]).
- Emulator seeding for Region5 starts from Region6's phase-1 write-rate maps (`WRMAP0`) and is refit online from this run's own sims. Seeding affects only how many sims a search takes, never which result counts.

### Arms

| Arm | Labels (day 1) | Admission features | Options | Role |
|---|---|---|---|---|
| A | Baleen (authors' `PolicyUtilityServiceTimeSize2`) | `meta+block+chunk` | none | baseline |
| B | Baleen | `meta+block+chunk+load` | none | baseline (signal alone) |
| **A+α** | Baleen | `meta+block+chunk` | `--ap-load-adapt-alpha -1.0` (A's retrains) | **H4** |
| B+α | Baleen | `meta+block+chunk+load` | α = −1.0 (B's retrains) | secondary |
| X1 | F1PT | `meta+block+chunk+load` | α = −1.0 (D:F1PT's retrains) | Ising record |
| RejectX, CoinFlip | none | none | the authors' `20230410_static_pf` commands, FROZEN code (`0_reproduce/baleen_code`) | baselines |

**Load-adaptive threshold (overlay defaults, as H3′):** θ_t = θ · clip((load_10m / 20)^α, 0.25, 4), load_10m = trailing 10-minute GET demand in utilisation % at the access time; `--ap-load-adapt-ref 20 --ap-load-adapt-window 10`. α = −1 and ref = 20 are fixed; **no α or ref tuning on Region5.**

**F1PT labels (X1).** True min–max day-1 peak (q2 F1) on `inst/day1_<inst>.npz` (all 145 day-1 windows, harness budget B), q2 parallel-tempering finalist with its frozen 10 s configuration (`explore/q2/plan_F1.json`, `pt`, `cfg_by_budget["10"]`, LP start, 8 numba threads), single level f = 1.0, seed = retrain k; fill re-applied in each run by `PolicyPeakBaleen4`. Exactly the WP3 configuration. Solved for seeds 1–6 (`labels/`, `results/labels_summary.csv`).

**RejectX / CoinFlip.** Frozen-code replays of the authors' `20230410_static_pf` commands, starting at the authors' own `--ap-probability`; bisected on the probability only when the authors' value misses 35.599 ± 1% (as `explore/common/src/a0.py` / WP3). Values: `results/static_baselines.csv`; author check: `results/static_author_check.csv` (P100 at the authors' own probability equals the authors' CSV value on all 12, max difference 3e-10).
- CoinFlip: matched on 6/6 at the authors' probability. Mean P100 **44.47**.
- **RejectX cannot be matched on Region5 s0.1, 0.2, 0.3, 0.5, 0.6.** Its write rate jumps across the target band between two probabilities 1e-6 apart (e.g. s0.1: 29.54 MB/s at p = 0.021652, 38.87 MB/s at p = 0.021653); the authors' own rows are off-target too (WR 37.4–39.5). The bisection (14 steps) ends on the above-step side, whose P100 equals the authors' value. s0.4 matches at the authors' probability.
- **Rule fixed here:** the RejectX condition must hold against **both** sides of the step. An arm is "below RejectX" only if its mean P100 is below the mean of the authors' bit-exact replays (`static_baselines.csv`, **39.35**) **and** below the mean of the closest replays under the band (`results/static_rejectx_bracket.csv`, column `rejectx_low_side_p100`, **39.28**; s0.4 uses its matched value). The two differ by at most 0.41 per instance.

## 4. Retrains, unmatched runs, logging

- 3 retrains per (arm, instance), seeds 1, 2, 3: 5 arms × 6 instances × 3 = **90 evaluations** (trainings: A, B, D:F1PT × 18 = 54).
- A retrain whose threshold search ends unmatched is excluded and reported. A cell with fewer than 3 matched retrains gets extra retrains with seeds 4, 5, 6 until 3 are matched (at most 6). The driver does this automatically after the main pass.
- Every evaluation, including failures, is one row of `wp9_region5/trials.csv` with a unique key. A failed evaluation (crash) is re-run by relaunching the same command; both rows stay in the ledger.

## 5. Pass criteria (the PROTOCOL_v2_H3 §5 / phase-1 Q3 rule)

P100 = `PeakServiceTimeUtil1`: per instance, the mean over matched retrains; then over the 6 test instances.

For a configuration X and a reference R:
- **wins:** X's mean P100 below R's on ≥ 4/6 instances; and
- **margin:** mean improvement (R − X) > 2 SE, with SE = sqrt(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i) / 6 (retrain-level). The instance-level SE (sd of the 6 paired differences / √6) is reported too and does not enter the verdict.

**H4 = YES iff A+α meets** wins and margin **vs A** and **vs B**, **and** its mean P100 is below RejectX's (both values of §3) and below CoinFlip's means (over the same 6 instances). Otherwise NO.

**B+α:** the same rule vs A and B, reported as secondary; no claim rests on it.

**X1:** the rule vs A, vs B and vs A+α is reported (Ising record); no pass/fail on X1.

Evaluation code, written and checked before any test data exist: `src/evaluate_test.py` → `results/evaluation.json`. Checked on WP3's published trials, it reproduces `wp3_test/RESULTS_test.md` exactly (A+α vs A +0.965, 5/6, SE 0.160 / 0.391; X1 vs A −1.265).

**Also reported (no pass/fail):**
- P99, top-5 mean, mean DT, write rate;
- first-access admission and peak-window admission (emulator mechanism statistics, as WP3), peak-window big-offset share;
- retention R = (A − X)/(OPT_peak-blind − OPT_peak-aware), using WP1's offline OPT on these instances (`results/retention_inputs_wp1.csv`: R0 = peak-blind, `pt` = peak-aware PT 300 s), not recomputed;
- per-instance tables, threshold values, sims per search.

## 6. Known caveats (stated before the test)

- **α = −1 and ref = 20 were chosen on Region6/7 dev data**, and A+α was best on the H3′ test only as a post-hoc observation. Region5 is a transfer test of that choice.
- **The Region5 Fig 9 variant differs from Region6/7** (ML-Range prefetch on partial hits). The threshold multiplier acts only on admission; prefetch decisions use the unchanged ML-Range models.
- On the H3′ test the A+α gain was +0.96 (retrain SE 0.16, instance SE 0.39). With 6 instances, the 4/6-wins condition can fail on a smaller or noisier effect even if the mean margin passes.
- WP1 offline headroom on these instances is ≈ 3.3–5.9 util-pts (R0 − PT), so retention values are small fractions.
- The machine is shared with `<another project>`; that slows simulations but does not change results (every result is a deterministic function of the retrain's models and the threshold).

## 7. Prerequisites (none looked at test outcomes)

| item | status | where |
|---|---|---|
| Test jobs (Region5 s0.1–0.6) + dry-run job (s0) from the release CSV | **ready** | `jobs.json`, `src/make_jobs_test.py` |
| Day-1 + fullml instances through the frozen driver, sha256 | **ready** (14 files) | `INSTANCES.md`, `results/instances_sha256.csv` |
| F1PT label sets, seeds 1–6 | **ready** (36 sets) | `labels/`, `results/labels_summary.csv` |
| RejectX / CoinFlip frozen replays | **ready**; bit-exact vs authors; RejectX step rule above | `results/static_*.csv` |
| Retention inputs (WP1 offline OPT) | **ready** | `results/retention_inputs_wp1.csv` |
| Dry run Region5 s0, arm A, 1 retrain | **done**: matched in 3 sims, P100 32.93, WR 35.78, θ 0.683; ML-Range prefetch models trained and loaded; no fix needed | `dryrun/` |
| This file committed; `TEST_GO` created by the coordinator | pending | |

## 8. Launch (only after §7's last item)
```
cd changes/2_deployable_peak/wp9_region5 && source env.sh
touch TEST_GO                                   # coordinator, after committing this file
setsid nohup taskset -c 0-23 $BALEEN_PY -B src/wp9.py --mode test --arms A B Aa Ba X1 -j 16 > logs/wp9_test.out 2>&1 < /dev/null &
# after it finishes (includes the §4 extra-retrain pass):
$BALEEN_PY -B src/evaluate_test.py              # -> results/evaluation.json
```
