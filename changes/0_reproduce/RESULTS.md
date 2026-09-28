# Baleen (FAST '24) reproduction: results

We reproduced Baleen and its two baselines on the paper's Figure 9 benchmark (Region7 and Region6, sample 0). The baselines match the authors' runs exactly. Baleen matches the authors' runs to within 0.6 points once both are measured with the released code's metric. The paper's own Figure 9 Baleen values for these two traces come from an older, unreleased version of the metric and cannot be reproduced exactly.

Setup: 2026-09-26/27, one 24-core machine, CPU only (no GPU). Artifact: Baleen-FAST24 `4e3a920`, BCacheSim `ddeb2d8`, frozen and unmodified. Operating point: 366.475 GB cache, target flash write rate 35.6 MB/s (the CSV's "Target DWPD 7.5"), 0.1% trace sample, sample 0. Metric: peak backend load (%) in 10-minute windows, after the first (training) day.

## 1. Stage A: Fig 9 from the authors' results CSV

Executing the authors' own `fig-09-202309.ipynb` in our environment gives Baleen **28.11**, RejectX **31.95**, CoinFlip **34.63**, and a 12.0% saving. These match the paper exactly.

## 2. Baselines: RejectX and CoinFlip (bit-exact)

Each job replays one authors' run using the exact command stored in `results_release.csv.gz`.

| Trace | Method | Authors' peak (write rate) | Ours |
|---|---|---|---|
| Region7 | RejectX | 42.455 (36.00) | **42.455 (36.00)** |
| Region7 | CoinFlip | 48.961 (35.69) | **48.961 (35.69)** |
| Region6 | RejectX | 42.321 (35.67) | **42.321 (35.67)** |
| Region6 | CoinFlip | 43.445 (35.57) | **43.445 (35.57)** |

These are the authors' `20230410_static_pf` runs. Their `tracedrop` runs of the same policies match on write rate but not on peak (see §4).

## 3. Baleen with the released metric: within 0.6 points of the authors

Replays of the authors' `20230421_alltraces_pfalways` Baleen runs. This experiment used the same metric version as the released code (no-cache peak 63.42 for Region7, 59.14 for Region6). Following the paper's §4.1, the admission threshold was re-converged until the write rate was within 1% of 35.6 MB/s.

| Trace | Prefetching | Authors' peak (write rate) | Ours at matched write rate | Δ |
|---|---|---|---|---|
| Region7 | ML-Range on Partial Hit | 40.57 (34.67) | **40.03** (35.46) | −0.54 |
| Region7 | ML-Range on Every Miss | 42.56 (35.23) | **42.91** (35.58) | +0.35 |
| Region6 | ML-Range on Partial Hit | 42.00 (35.27) | **42.21** (35.41) | +0.21 |
| Region6 | ML-Range on Every Miss | 43.89 (36.01) | **43.38** (35.86) | −0.51 |

All four are within ±0.6 points. The pass tolerance was ±2 points, and the authors' own repeated runs of one policy differ by up to 1.7 points.

## 4. Why the paper's Fig 9 Baleen bars do not match exactly

For Region7 and Region6 at sample 0, the paper's Fig 9 Baleen values (Region7 37.59, Region6 41.31) come from the authors' `20230327_tracedrop_*` experiments. Those experiments computed disk-head time differently from the released code:

- The trace is identical: same IOPS, chunk queries and total no-cache DT.
- The **no-cache peak differs**: 64.69 vs 63.42 for Region7, and 59.24 vs 59.14 for Region6.
- The released code has no option that reproduces this.
- The effect shows directly on the baselines. Our replays of `tracedrop` RejectX and CoinFlip match the authors' write rate to 3 decimals, but their peak by only 0.5–1.9 points.

Retraining Baleen is not deterministic: LightGBM is hard-coded to 20 threads, and episode generation uses 8 worker processes. We therefore ran **8 extra retrains per trace** of the Fig 9 Baleen configuration, each at the matched write rate:

| Trace | Fig 9 variant | Ours: mean ± SD over 9 models (range) | Paper Fig 9 (`tracedrop`) |
|---|---|---|---|
| Region7 | ML-Range on ML-When | 40.10 ± 0.18 (39.93–40.42) | 37.59 |
| Region6 | All on Partial Hit | 43.25 ± 0.04 (43.21–43.32) | 41.31 |

The spread across retrains is far smaller than the gap, so the gap is systematic rather than training noise. Consistent with that, the peak is almost insensitive to the admission threshold: less than 0.6 points of change as the write rate moves from 28 to 45 MB/s. What sets the peak is the model and the metric, not the write budget.

## 5. README smoke test (Region1)

Baleen saves **16.61%** of peak load over RejectX; the authors' `example.ipynb` reports 16.11%. Running the authors' `example.ipynb` on our results gives the same 16.61%.

## Deviations from the authors' commands

None of these changes an algorithm parameter.

1. We add `--eviction-policy LRU`, the recorded `EvictionPolicy` for every row. The authors' commands predate the flag, and the frozen simulator's default of `None` crashes.
2. We drop `--offline-ap-decisions`. The decisions file `train.py` produces covers only day 1, so the simulator raises `KeyError` on later days. For these policies the file only feeds diagnostic counters, and the README configs omit the flag too.
3. Training steps run one at a time, because of the hard-coded 20 threads. Simulations run in parallel with `OMP_NUM_THREADS` capped per job.
4. For Baleen we re-converge the admission threshold to the target write rate, as in paper §4.1, because retrained models are not bit-identical to the authors'.

## Integrity
- `check_frozen.sh`: all 94 artifact files are unchanged.
- `check_no_leak.sh`: nothing was written outside `changes/0_reproduce/` since the sandbox was added. Setup-time items outside the directory are listed in README.md.
- Every job and simulation runs under `bwrap`, with `/tmp` mapped to `work/systmp`.

## Where the numbers are
Everything below is under `work/results/`:
- `fig9_summary.md` and `fig9_jobs.csv`: per-job replays;
- `converge_*.csv`: every threshold tried;
- `retrain_dist.csv`: the 18 retrain replicates;
- `notebooks/`: the executed authors' notebooks.
