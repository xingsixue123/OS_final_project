# Stage-1 table (DEV: Region7/Region6 x samples 0-0.3; 8 instances; label seeds 1-3)

Offline = day-1 instance (all 145 windows), util %. Stability = mean pairwise Jaccard of the label sets of
seeds 1-3. Learnability = learn.py protocol (seed-1 labels, block split): net logloss gain from `load`
= ll(+shuffled load) - ll(+load), mean ± sd over 8 instances. PL = label-level proxy (emulated deployed
P100, refit GBM + calibrated threshold; mean over instances of the per-instance mean over seeds 1-3;
± = mean per-instance sd over seeds). dX1 / dAa = paired proxy difference vs X1 / vs A+α (negative =
design better), mean over instances (wins/8). **The proxy failed its pre-registered validation (see
proxy_validation.md) unless stated otherwise; PL columns are diagnostics, not evidence.**

| design | day-1 peak | top-10 | #labels | J vs Baleen | stability J | zero-value | small (≤2 ch) share | learnability net | PL α none | PL α=−1 | k0 adm (α=−1) | dX1 (α=−1) | dAa (α=−1) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Baleen | 28.14 | 25.49 | 1790 | 1.000 | 1.000 | 0.0 | 0.521 | 0.001 ± 0.003 | 35.84 ± 0.42 | 35.92 ± 0.34 | 0.039 | +0.90 (4/8) | +0.16 (3/8) |
| F1PT | 21.51 | 21.44 | 1130 | 0.428 | 0.759 | 0.0 | 0.362 | 0.041 ± 0.018 | 35.59 ± 0.86 | 35.02 ± 0.56 | 0.020 | +0.00 (0/8) | -0.75 (4/8) |
| F1CPSAT | 21.51 | 21.50 | 1181 | 0.459 | 0.743 | 0.0 | 0.407 | 0.042 ± 0.017 | 35.84 ± 0.91 | 35.32 ± 1.12 | 0.025 | +0.30 (5/8) | -0.45 (5/8) |
| F1PT4 | 21.51 | 21.43 | 1120 | 0.424 | 0.770 | 0.0 | 0.360 | 0.039 ± 0.019 | 35.57 ± 0.75 | 34.97 ± 0.85 | 0.021 | -0.05 (6/8) | -0.80 (5/8) |
| ANC3 | 21.78 | 21.74 | 1805 | 0.836 | 0.923 | 0.0 | 0.517 | 0.025 ± 0.011 | 35.40 ± 0.75 | 35.29 ± 1.19 | 0.056 | +0.27 (5/8) | -0.47 (5/8) |
| ANC10 | 22.66 | 22.64 | 1809 | 0.916 | 0.949 | 0.0 | 0.515 | 0.014 ± 0.009 | 36.05 ± 1.29 | 35.39 ± 1.29 | 0.047 | +0.38 (5/8) | -0.37 (6/8) |
| ANC30 | 24.30 | 24.18 | 1800 | 0.974 | 0.980 | 0.0 | 0.518 | 0.006 ± 0.007 | 36.82 ± 1.29 | 36.26 ± 0.84 | 0.040 | +1.24 (4/8) | +0.50 (3/8) |
| TK10 | 21.62 | 21.28 | 1226 | 0.462 | 0.870 | 0.0 | 0.379 | 0.047 ± 0.021 | 35.61 ± 1.13 | 35.31 ± 1.25 | 0.023 | +0.29 (5/8) | -0.45 (5/8) |
| TK72 | 25.99 | 23.98 | 1486 | 0.655 | 0.975 | 0.0 | 0.456 | 0.020 ± 0.014 | 35.54 ± 1.29 | 35.08 ± 1.09 | 0.027 | +0.07 (5/8) | -0.68 (5/8) |
| ANC10TK10 | 22.69 | 22.54 | 1808 | 0.909 | 0.946 | 0.0 | 0.516 | 0.015 ± 0.009 | 35.69 ± 0.65 | 35.32 ± 1.04 | 0.046 | +0.30 (6/8) | -0.45 (6/8) |
| STU10R1 | 21.67 | 21.65 | 1022 | 0.385 | 0.748 | 34.2 | 0.346 | 0.052 ± 0.026 | 34.93 ± 0.50 | 34.89 ± 1.04 | 0.028 | -0.12 (5/8) | -0.87 (4/8) |
| STU10R2 | 21.78 | 21.75 | 1050 | 0.371 | 0.768 | 79.8 | 0.352 | 0.060 ± 0.026 | 35.07 ± 0.72 | 34.85 ± 1.02 | 0.033 | -0.17 (5/8) | -0.92 (4/8) |
| STU30R1 | 22.05 | 22.02 | 970 | 0.366 | 0.722 | 40.6 | 0.346 | 0.061 ± 0.029 | 35.33 ± 1.26 | 35.00 ± 1.31 | 0.029 | -0.02 (5/8) | -0.76 (5/8) |
| ANC10CP | 23.53 | 23.33 | 1789 | 0.927 | 0.937 | 0.0 | 0.519 | – | – | – | – | – | – |

Baleen-label rows with original features: PL A = 35.68, A+α = 35.76.

### PL α = −1 by region (mean over 4 instances)

| config | Region7 | Region6 |
|---|---|---|
| A+a | 34.98 | 36.55 |
| B+a | 35.19 | 36.65 |
| X1 | 35.86 | 34.18 |
| Ec | 34.83 | 35.80 |
| E:F1PT4 | 35.48 | 34.45 |
| E:ANC3 | 34.68 | 35.90 |
| E:ANC10 | 34.53 | 36.26 |
| E:ANC30 | 35.66 | 36.87 |
| E:TK10 | 35.09 | 35.53 |
| E:TK72 | 34.35 | 35.82 |
| E:ANC10TK10 | 34.68 | 35.96 |
| E:STU10R1 | 34.78 | 35.00 |
| E:STU10R2 | 34.94 | 34.75 |
| E:STU30R1 | 35.07 | 34.93 |
