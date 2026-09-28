# Phase 1 — Baleen reproduction plan

**Paper:** `documents/Baleen_FAST24_Wong.pdf` (FAST '24)
**Frozen code:** `baleen_code/` is read-only. Commits are recorded in `FROZEN_baleen_code.txt`, and file checksums in `baleen_code.sha256`. Check them with `cd baleen_code && sha256sum -c ../baleen_code.sha256`.
**Working area:** `work/` (data, runs and temporary files). Nothing is ever written into `baleen_code/`.

## Target: Figure 9 (peak backend load per trace) on 2 aligned traces

In Figure 9, **Baleen** is the best prefetch variant for each trace. **RejectX** and **CoinFlip** run with **no prefetching**. The notebook is `notebooks/paper-figs/fig-09-202309.ipynb`.

Operating point, as used in the artifact:
- cache size 366.475 GB (the "400 GB-equivalent" cache)
- target write rate 35.599 MB/s, which the CSV labels **Target DWPD = 7.5**. This is not 3 DWPD.
- 0.1% trace sample, sample 0
- train on day 1, measure from day 2 on (`stats_start = 86400`)

Metric: `P100ServiceTimeUtil@10m`, the peak backend load in %.

### Endpoint values we reproduce

These are the authors' sample-0 values at 0.1%, from `results_release.csv.gz`.

| Trace | Policy | Prefetch | Peak (%) | Median (%) | IO miss | Write rate (MB/s) |
|---|---|---|---|---|---|---|
| **Region7** (20230325) | Baleen | ML-Range on ML-When | **37.59** | 21.19 | 0.732 | 36.35 |
| | RejectX | none | **41.59** | 22.75 | 0.792 | 35.86 |
| | CoinFlip | none | **49.71** | 23.97 | 0.859 | 35.68 |
| **Region6** (20230325) | Baleen | All on Partial Hit | **41.31** | | | |
| | RejectX | none | **42.59** | | | |
| | CoinFlip | none | **44.42** | | | |

Derived savings: Region7 Baleen vs RejectX **9.6%** (vs CoinFlip 24.4%). Region6 Baleen vs RejectX **3.0%** (vs CoinFlip 7.0%).

> **Correction (2026-09-26).** The first version of this table built the Region6 row from `Region == Region6`. That also pulled in rows from a *different* trace (`202302/Region6`, the Feb 2023 capture), which Fig 9 excludes. The Fig 9 notebook filters on `Trace == 20230325/Region6`. The corrected sample-0 values are above: each is the mean of the authors' runs, with RejectX 42.32/42.85 and CoinFlip 43.45/45.40. With the correct filter, the all-sample means reproduce Fig 9 exactly: R6 38.87/40.84/46.46, R7 37.21/39.08/46.12.
>
> The Region6 gap between Baleen and RejectX at sample 0 (1.3 points) is within the authors' own run-to-run spread (up to 1.7 points). Region6 at sample 0 is therefore a weak test of the ordering. Region7 is the primary benchmark. For a stronger Region6 result, run all 10 samples (`setup/02_data.sh --samples10`, `make_jobs.py --samples 0 0.1 … 0.9`), which compares directly against the Fig 9 bars.
>
> **Every target is the mean of 1–3 authors' runs.** The runs within one cell differ by up to 1.7 points (Region7 RejectX: 42.46 vs 40.73), which is why the peak tolerance is ±2 points.
For context, the Figure 9 values averaged over all samples are R7 37.21/39.08/46.12 and R6 38.87/40.84/46.46.

**Why these two traces.** They are the least noisy traces across samples (SD of peak load 1.5–5 points), their policy order at sample 0 is clean, and `notebooks/reproduce/reproduce_commands.sh` ships converged parameters for them.
- Region4 has the largest effect in Figure 9 (17%), but at sample 0 the three policies are tied within 0.6 points, with an SD across samples of about 17 points.
- Region5 separates Baleen from RejectX by only 3.7%.
- Figure 9 runs Region1/2 at 1% samples and Region3 at 5%, not 0.1%.

### Pass criteria (per trace)
1. Peak load of each policy within **±2 points** of the target above.
2. Achieved write rate within **±5%** of 35.6 MB/s. Always report it.
3. Order **Baleen < RejectX < CoinFlip** holds, and Baleen's saving over RejectX has the same sign and is within ±3 points.

## Stages
- **A. Re-plot:** rebuild the Figure 9 table from `results_release.csv.gz` and match 28.11 / 31.95 / 34.63 exactly. This checks our metric extraction.
- **0. Smoke test:** the README example on Region1, sample 0. The expected Baleen saving vs RejectX is **16.1%**.
- **B. Re-simulate:** every authors' run behind the 6 bars (2 traces × {Baleen, RejectX, CoinFlip}, sample 0), which is 10 runs. Each uses the authors' exact `TrainCommand` and `ReproduceCommand`, stored per row in `results_release.csv.gz`. This settles which of the duplicated parameter sets in `reproduce_commands.sh` was actually used. Only paths and the experiment name are rewritten.
- **B+ (optional):** rerun the eviction-age and threshold convergence loop from scratch, and add Baleen (No Prefetch) as an ablation.

## Known issues in the artifact
- Trace paths in `reproduce_commands.sh` are wrong, in two different ways: `…/Region5/processed/…` and `…/processed/Region5/…`. The real path is `data/tectonic/<group>/<Region>/full_0_0.1.trace`.
- The script lists baselines twice, with different converged parameters. The wrapper must choose one set and record which.
- A missing model file makes the run print "Failed to load … continues" and keep going. The wrapper must treat this as a hard error.
- Absolute DT uses the university testbed's disk constants, not Meta's. Compare against the CSV, which was produced by the same released code, not against production numbers.
