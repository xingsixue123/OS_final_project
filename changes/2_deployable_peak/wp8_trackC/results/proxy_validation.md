# Proxy validation (pre-registered criterion, PROGRESS.md 2026-10-05 14:25)

Cells: 128 (instance x configuration); 13 criterion configurations; sim = WP2 mean matched P100.
Calibration: `results/wr_calibration.json` (selected variant: see calib output).

### PL: label-level proxy (refit GBM) -- PRIMARY (`pl`)

| instance | Region6_s0 | Region6_s0.1 | Region6_s0.2 | Region6_s0.3 | Region7_s0 | Region7_s0.1 | Region7_s0.2 | Region7_s0.3 | median |
|---|---|---|---|---|---|---|---|---|---|
| Spearman rho_i | +0.48 | +0.63 | +0.55 | +0.49 | +0.32 | +0.76 | +0.32 | +0.03 | +0.49 |

- **C1** median rho = +0.49, rho > 0 on 8/8 -> FAIL
- **C2** dev-mean contrasts (proxy vs sim): X1-A: -0.66 vs -1.30; X1-(A+a): -0.75 vs -0.68; D:F1PT-A: -0.08 vs -0.13 -> PASS
- **C3** X1-(A+a) sign agreement on instances with |sim| >= 0.5: 6/7 (proxy -0.25, -9.19, -0.05, +0.01, -0.33, +1.15, +1.17; sim -3.61, -1.40, -2.06, -0.60, -0.80, +0.55, +2.25) -> PASS
- pooled within-instance correlation over 104 cells: Pearson +0.43, Spearman +0.42
- **verdict: PROXY NOT VALID**

### PM: WP2's actual models, calibrated theta -- diagnostic (`pm`)

| instance | Region6_s0 | Region6_s0.1 | Region6_s0.2 | Region6_s0.3 | Region7_s0 | Region7_s0.1 | Region7_s0.2 | Region7_s0.3 | median |
|---|---|---|---|---|---|---|---|---|---|
| Spearman rho_i | +0.09 | +0.43 | +0.71 | +0.46 | +0.26 | +0.68 | -0.27 | +0.30 | +0.37 |

- **C1** median rho = +0.37, rho > 0 on 7/8 -> FAIL
- **C2** dev-mean contrasts (proxy vs sim): X1-A: -1.17 vs -1.30; X1-(A+a): -0.02 vs -0.68; D:F1PT-A: -0.66 vs -0.13 -> PASS
- **C3** X1-(A+a) sign agreement on instances with |sim| >= 0.5: 5/7 (proxy -1.04, +0.48, -0.59, -0.59, -0.46, -0.35, +1.63; sim -3.61, -1.40, -2.06, -0.60, -0.80, +0.55, +2.25) -> PASS
- pooled within-instance correlation over 104 cells: Pearson +0.48, Spearman +0.43
- **verdict: PROXY NOT VALID**

### PM at the simulation's converged theta (oracle threshold) -- diagnostic (`pm_simtheta`)

| instance | Region6_s0 | Region6_s0.1 | Region6_s0.2 | Region6_s0.3 | Region7_s0 | Region7_s0.1 | Region7_s0.2 | Region7_s0.3 | median |
|---|---|---|---|---|---|---|---|---|---|
| Spearman rho_i | +0.02 | -0.23 | +0.73 | +0.36 | +0.18 | +0.77 | +0.36 | +0.39 | +0.36 |

- **C1** median rho = +0.36, rho > 0 on 7/8 -> FAIL
- **C2** dev-mean contrasts (proxy vs sim): X1-A: -0.33 vs -1.30; X1-(A+a): +0.41 vs -0.68; D:F1PT-A: +0.26 vs -0.13 -> FAIL
- **C3** X1-(A+a) sign agreement on instances with |sim| >= 0.5: 6/7 (proxy -0.83, +0.97, -0.46, -0.20, -0.71, +0.21, +2.38; sim -3.61, -1.40, -2.06, -0.60, -0.80, +0.55, +2.25) -> PASS
- pooled within-instance correlation over 104 cells: Pearson +0.37, Spearman +0.32
- **verdict: PROXY NOT VALID**

### Dev means over 8 instances (util %)

| config | sim | PL | PM | PM@sim-theta | sim k0 | PL k0 |
|---|---|---|---|---|---|---|
| A | 38.50 | 35.68 | 35.92 | 35.21 | 0.045 | 0.035 |
| B | 38.44 | 35.84 | 35.76 | 35.55 | 0.049 | 0.035 |
| A+a | 37.88 | 35.76 | 34.77 | 34.47 | 0.046 | 0.041 |
| B+a | 38.43 | 35.92 | 35.38 | 34.52 | 0.043 | 0.039 |
| B+a0.5 | 38.05 | 35.60 | 35.07 | 34.81 | 0.044 | 0.035 |
| C:F1PT | 38.81 | 35.82 | 36.03 | 35.61 | 0.009 | 0.011 |
| C:F1EIM | 39.09 | 35.74 | 35.85 | 35.83 | 0.007 | 0.009 |
| D:F1PT | 38.37 | 35.59 | 35.25 | 35.46 | 0.013 | 0.015 |
| D:F1EIM | 38.46 | 35.78 | 36.07 | 36.21 | 0.010 | 0.012 |
| Dc | 38.74 | 35.84 | 35.61 | 35.04 | 0.016 | 0.021 |
| X1 | 37.20 | 35.02 | 34.75 | 34.88 | 0.016 | 0.020 |
| X2 | 37.84 | 35.13 | 34.97 | 35.08 | 0.014 | 0.018 |
| Ec | 38.46 | 35.32 | 35.84 | 36.01 | 0.019 | 0.025 |
| D:P0 | 39.42 | 35.84 | 37.30 | 36.03 | 0.163 | 0.129 |
| D:T2 | 39.65 | 35.32 | 35.24 | 34.93 | 0.106 | 0.088 |
| E:F1EIM | 38.02 | 34.87 | 34.89 | 35.17 | 0.011 | 0.016 |

k0 (first-access admission): PL vs WP2 sim-model k0 Pearson over 128 cells: +0.98
