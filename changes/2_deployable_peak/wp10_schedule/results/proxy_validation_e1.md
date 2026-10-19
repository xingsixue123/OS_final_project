# E1 proxy validation (criterion pre-registered in PROGRESS.md, E1 PRE-REGISTRATION)

Retrains: 120; variant rows: 272. Sim = WP2 matched P100.

## P1

- **C1** within-retrain pairs with |sim Δ| ≥ 0.25: 126; concordant 79 (0.63); sign-test p = 0.00277 → FAIL
- **C2** α=−1 minus none, cells {A,B}×8: mean sim Δ -0.320 vs proxy Δ -0.400 (same sign: True); sign agreement on |sim Δ| ≥ 0.25 cells: 6/9 → FAIL
- **verdict: NOT VALID**

| cell | n | sim Δ | proxy Δ |
|---|---|---|---|
| A:baleen Region6_s0 | 3 | -0.43 | +0.567 |
| A:baleen Region6_s0.1 | 3 | -1.90 | -0.750 |
| A:baleen Region6_s0.2 | 3 | +0.06 | -0.919 |
| A:baleen Region6_s0.3 | 3 | -0.40 | +0.528 |
| A:baleen Region7_s0 | 3 | -0.35 | -0.552 |
| A:baleen Region7_s0.1 | 3 | -0.92 | -1.602 |
| A:baleen Region7_s0.2 | 3 | +0.15 | -0.683 |
| A:baleen Region7_s0.3 | 3 | -1.21 | -0.781 |
| B:baleen Region6_s0 | 3 | -0.10 | +0.421 |
| B:baleen Region6_s0.1 | 3 | +2.36 | -0.318 |
| B:baleen Region6_s0.2 | 3 | -0.16 | -0.413 |
| B:baleen Region6_s0.3 | 3 | -0.07 | -0.044 |
| B:baleen Region7_s0 | 3 | +0.11 | -0.385 |
| B:baleen Region7_s0.1 | 3 | -1.32 | -0.561 |
| B:baleen Region7_s0.2 | 3 | +0.03 | -0.578 |
| B:baleen Region7_s0.3 | 3 | -0.99 | -0.332 |

Per-instance Spearman (all variants of all retrains): Region6_s0 +0.73, Region6_s0.1 +0.39, Region6_s0.2 +0.16, Region6_s0.3 +0.22, Region7_s0 -0.48, Region7_s0.1 +0.39, Region7_s0.2 -0.65, Region7_s0.3 -0.45
Pooled Pearson: -0.01

## P2

- **C1** within-retrain pairs with |sim Δ| ≥ 0.25: 126; concordant 82 (0.65); sign-test p = 0.000453 → FAIL
- **C2** α=−1 minus none, cells {A,B}×8: mean sim Δ -0.320 vs proxy Δ -1.011 (same sign: True); sign agreement on |sim Δ| ≥ 0.25 cells: 6/9 → FAIL
- **verdict: NOT VALID**

| cell | n | sim Δ | proxy Δ |
|---|---|---|---|
| A:baleen Region6_s0 | 3 | -0.43 | -0.559 |
| A:baleen Region6_s0.1 | 3 | -1.90 | -1.945 |
| A:baleen Region6_s0.2 | 3 | +0.06 | -0.403 |
| A:baleen Region6_s0.3 | 3 | -0.40 | -1.073 |
| A:baleen Region7_s0 | 3 | -0.35 | -0.818 |
| A:baleen Region7_s0.1 | 3 | -0.92 | -2.438 |
| A:baleen Region7_s0.2 | 3 | +0.15 | -0.284 |
| A:baleen Region7_s0.3 | 3 | -1.21 | +0.766 |
| B:baleen Region6_s0 | 3 | -0.10 | -1.221 |
| B:baleen Region6_s0.1 | 3 | +2.36 | -1.327 |
| B:baleen Region6_s0.2 | 3 | -0.16 | -2.084 |
| B:baleen Region6_s0.3 | 3 | -0.07 | -1.185 |
| B:baleen Region7_s0 | 3 | +0.11 | -1.811 |
| B:baleen Region7_s0.1 | 3 | -1.32 | -1.737 |
| B:baleen Region7_s0.2 | 3 | +0.03 | -0.401 |
| B:baleen Region7_s0.3 | 3 | -0.99 | +0.345 |

Per-instance Spearman (all variants of all retrains): Region6_s0 +0.32, Region6_s0.1 +0.19, Region6_s0.2 +0.19, Region6_s0.3 +0.29, Region7_s0 -0.46, Region7_s0.1 +0.63, Region7_s0.2 -0.79, Region7_s0.3 -0.01
Pooled Pearson: +0.39

## P3

- **C1** within-retrain pairs with |sim Δ| ≥ 0.25: 126; concordant 77 (0.61); sign-test p = 0.00791 → FAIL
- **C2** α=−1 minus none, cells {A,B}×8: mean sim Δ -0.320 vs proxy Δ -0.220 (same sign: True); sign agreement on |sim Δ| ≥ 0.25 cells: 7/9 → PASS
- **verdict: NOT VALID**

| cell | n | sim Δ | proxy Δ |
|---|---|---|---|
| A:baleen Region6_s0 | 3 | -0.43 | -0.316 |
| A:baleen Region6_s0.1 | 3 | -1.90 | +0.470 |
| A:baleen Region6_s0.2 | 3 | +0.06 | -0.919 |
| A:baleen Region6_s0.3 | 3 | -0.40 | +0.570 |
| A:baleen Region7_s0 | 3 | -0.35 | -0.552 |
| A:baleen Region7_s0.1 | 3 | -0.92 | -0.848 |
| A:baleen Region7_s0.2 | 3 | +0.15 | -0.414 |
| A:baleen Region7_s0.3 | 3 | -1.21 | -0.526 |
| B:baleen Region6_s0 | 3 | -0.10 | -0.189 |
| B:baleen Region6_s0.1 | 3 | +2.36 | +0.281 |
| B:baleen Region6_s0.2 | 3 | -0.16 | -0.312 |
| B:baleen Region6_s0.3 | 3 | -0.07 | +0.993 |
| B:baleen Region7_s0 | 3 | +0.11 | -0.385 |
| B:baleen Region7_s0.1 | 3 | -1.32 | -0.696 |
| B:baleen Region7_s0.2 | 3 | +0.03 | -0.247 |
| B:baleen Region7_s0.3 | 3 | -0.99 | -0.423 |

Per-instance Spearman (all variants of all retrains): Region6_s0 +0.22, Region6_s0.1 +0.62, Region6_s0.2 +0.37, Region6_s0.3 -0.17, Region7_s0 -0.53, Region7_s0.1 +0.39, Region7_s0.2 -0.37, Region7_s0.3 -0.37
Pooled Pearson: -0.07

