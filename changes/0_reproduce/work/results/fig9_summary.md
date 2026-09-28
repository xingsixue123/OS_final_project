# Reproduction: fig9

10/10 jobs done. Metric: P100ServiceTimeUtil@10m (peak backend load, %).

## Per job (1:1 vs the authors' row)

| job | author peak | ours | Δ | author WR | ours WR | bit-exact |
|---|---|---|---|---|---|---|
| 20230325_Region6_s0_baleen_20230327_tracedrop_old | 41.31 | 43.27 | +1.96 | 35.776 | 33.879 |  |
| 20230325_Region6_s0_coinflip_20230327_tracedrop_old | 45.40 | 43.45 | -1.95 | 35.598 | 35.598 |  |
| 20230325_Region6_s0_coinflip_20230410_static_pf | 43.45 | 43.45 | -0.00 | 35.569 | 35.569 | yes |
| 20230325_Region6_s0_rejectx_20230327_tracedrop_old | 42.85 | 42.32 | -0.53 | 35.612 | 35.612 |  |
| 20230325_Region6_s0_rejectx_20230410_static_pf | 42.32 | 42.32 | -0.00 | 35.673 | 35.673 | yes |
| 20230325_Region7_s0_baleen_20230327_tracedrop_XX | 37.59 | 40.06 | +2.47 | 36.345 | 38.578 |  |
| 20230325_Region7_s0_coinflip_20230327_tracedrop_XX | 50.46 | 48.96 | -1.50 | 35.670 | 35.670 |  |
| 20230325_Region7_s0_coinflip_20230410_static_pf | 48.96 | 48.96 | +0.00 | 35.686 | 35.686 | yes |
| 20230325_Region7_s0_rejectx_20230327_tracedrop_XX | 40.73 | 42.46 | +1.73 | 35.710 | 35.710 |  |
| 20230325_Region7_s0_rejectx_20230410_static_pf | 42.46 | 42.46 | -0.00 | 36.000 | 36.000 | yes |

## Per Fig 9 bar

| trace | policy | prefetch | author | ours | Δ | spread of authors' runs | pass |
|---|---|---|---|---|---|---|---|
| 20230325/Region6 | Baleen | All on Partial Hit | 41.31 | 43.27 | +1.96 | 0.00 | PASS |
| 20230325/Region6 | CoinFlip | No prefetching | 44.42 | 43.45 | -0.98 | 1.95 | PASS |
| 20230325/Region6 | RejectX | No prefetching | 42.59 | 42.32 | -0.26 | 0.53 | PASS |
| 20230325/Region7 | Baleen | ML-Range on ML-When | 37.59 | 40.06 | +2.47 | 0.00 | FAIL |
| 20230325/Region7 | CoinFlip | No prefetching | 49.71 | 48.96 | -0.75 | 1.50 | PASS |
| 20230325/Region7 | RejectX | No prefetching | 41.59 | 42.46 | +0.86 | 1.73 | PASS |

## Per trace: ordering and Baleen saving over RejectX

- **20230325/Region6**: saving vs RejectX authors 3.0% / ours -2.2%; order Baleen<RejectX<CoinFlip: False -> FAIL
- **20230325/Region7**: saving vs RejectX authors 9.6% / ours 5.6%; order Baleen<RejectX<CoinFlip: True -> FAIL

- Write rate within ±5% of 35.599 MB/s for all jobs: FAIL 20230325_Region7_s0_baleen_20230327_tracedrop_XX

**Overall: NOT PASSED**

## Deviations from the authors' commands (applied to every job)

- added --eviction-policy LRU (flag absent in authors' command; frozen simulator default None crashes)
- dropped --offline-ap-decisions (diagnostic-only here; as in README configs)
- training steps serialized (artifact hard-codes LightGBM num_threads=20); simulations run in parallel with OMP_NUM_THREADS capped per job
