
**T2** (held-out, 3 retrains per instance; P100 util %, matched WR only)

| instance | retrains (matched/all) | P100 mean +- sd | per retrain | Baleen online (3) | diff (Baleen - cfg) | RejectX | CoinFlip | win vs Baleen |
|---|---|---|---|---|---|---|---|---|
| Region7_s0.1 | 3/3 | 38.39 +- 3.73 | 36.05, 42.69, 36.42 | 36.57 +- 0.25 | -1.82 | 38.66 | 46.00 | no |
| Region7_s0.2 | 2/3 | 36.69 +- 0.13 | 36.78, 36.60 | 36.79 +- 0.00 | +0.10 | 38.00 | 41.97 | yes |
| Region7_s0.3 | 3/3 | 41.39 +- 2.19 | 42.85, 42.45, 38.86 | 37.81 +- 0.25 | -3.58 | 38.89 | 45.19 | no |
| Region6_s0.1 | 3/3 | 42.28 +- 0.56 | 42.88, 42.17, 41.78 | 40.93 +- 0.07 | -1.34 | 42.25 | 50.02 | no |
| Region6_s0.2 | 3/3 | 36.29 +- 0.46 | 35.98, 36.82, 36.06 | 36.26 +- 0.10 | -0.03 | 37.29 | 43.85 | no |
| Region6_s0.3 | 3/3 | 36.70 +- 0.16 | 36.69, 36.55, 36.86 | 36.96 +- 0.26 | +0.26 | 39.19 | 41.09 | yes |

Criteria: wins 2/6 (need >= 4) -> FAIL; mean improvement -1.068 vs 2 SE = 0.850 (retrain SE; instance-level 2 SE = 1.218) -> FAIL; mean P100 38.62 vs RejectX 39.05 / CoinFlip 44.69 -> PASS. **Q3 for T2: NO**

**C2** (held-out, 3 retrains per instance; P100 util %, matched WR only)

| instance | retrains (matched/all) | P100 mean +- sd | per retrain | Baleen online (3) | diff (Baleen - cfg) | RejectX | CoinFlip | win vs Baleen |
|---|---|---|---|---|---|---|---|---|
| Region7_s0.1 | 3/3 | 36.68 +- 0.36 | 37.00, 36.74, 36.29 | 36.57 +- 0.25 | -0.11 | 38.66 | 46.00 | no |
| Region7_s0.2 | 3/3 | 37.05 +- 0.24 | 36.77, 37.21, 37.16 | 36.79 +- 0.00 | -0.26 | 38.00 | 41.97 | no |
| Region7_s0.3 | 3/3 | 38.08 +- 1.42 | 39.15, 36.47, 38.63 | 37.81 +- 0.25 | -0.27 | 38.89 | 45.19 | no |
| Region6_s0.1 | 3/3 | 44.06 +- 4.72 | 49.50, 41.03, 41.66 | 40.93 +- 0.07 | -3.13 | 42.25 | 50.02 | no |
| Region6_s0.2 | 3/3 | 36.14 +- 0.09 | 36.12, 36.05, 36.24 | 36.26 +- 0.10 | +0.12 | 37.29 | 43.85 | yes |
| Region6_s0.3 | 3/3 | 36.75 +- 0.16 | 36.83, 36.57, 36.87 | 36.96 +- 0.26 | +0.21 | 39.19 | 41.09 | yes |

Criteria: wins 2/6 (need >= 4) -> FAIL; mean improvement -0.573 vs 2 SE = 0.956 (retrain SE; instance-level 2 SE = 1.035) -> FAIL; mean P100 38.13 vs RejectX 39.05 / CoinFlip 44.69 -> PASS. **Q3 for C2: NO**

**P0** (held-out, 3 retrains per instance; P100 util %, matched WR only)

| instance | retrains (matched/all) | P100 mean +- sd | per retrain | Baleen online (3) | diff (Baleen - cfg) | RejectX | CoinFlip | win vs Baleen |
|---|---|---|---|---|---|---|---|---|
| Region7_s0.1 | 3/3 | 36.11 +- 0.25 | 36.38, 36.07, 35.88 | 36.57 +- 0.25 | +0.46 | 38.66 | 46.00 | yes |
| Region7_s0.2 | 3/3 | 36.89 +- 0.18 | 36.70, 36.91, 37.05 | 36.79 +- 0.00 | -0.10 | 38.00 | 41.97 | no |
| Region7_s0.3 | 3/3 | 38.50 +- 0.56 | 38.92, 38.72, 37.87 | 37.81 +- 0.25 | -0.69 | 38.89 | 45.19 | no |
| Region6_s0.1 | 3/3 | 41.66 +- 0.25 | 41.79, 41.83, 41.38 | 40.93 +- 0.07 | -0.73 | 42.25 | 50.02 | no |
| Region6_s0.2 | 3/3 | 37.74 +- 2.80 | 36.40, 35.87, 40.96 | 36.26 +- 0.10 | -1.49 | 37.29 | 43.85 | no |
| Region6_s0.3 | 3/3 | 36.90 +- 0.06 | 36.85, 36.97, 36.89 | 36.96 +- 0.26 | +0.06 | 39.19 | 41.09 | yes |

Criteria: wins 2/6 (need >= 4) -> FAIL; mean improvement -0.414 vs 2 SE = 0.562 (retrain SE; instance-level 2 SE = 0.568) -> FAIL; mean P100 37.97 vs RejectX 39.05 / CoinFlip 44.69 -> PASS. **Q3 for P0: NO**
