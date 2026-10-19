# E1 proxy validation (criterion pre-registered in PROGRESS.md 2026-10-19 17:40)

Retrains: 120; variant rows: 272. Sim = WP2 matched P100.

## P1

- **C1** within-retrain pairs with |sim Δ| ≥ 0.25: 126; concordant 77 (0.61); sign-test p = 0.00791 → FAIL
- **C2** α=−1 minus none, cells {A,B}×8: mean sim Δ -0.320 vs proxy Δ -0.275 (same sign: True); sign agreement on |sim Δ| ≥ 0.25 cells: 8/9 → PASS
- **verdict: NOT VALID**

| cell | n | sim Δ | proxy Δ |
|---|---|---|---|
| A:baleen Region6_s0 | 3 | -0.43 | -0.285 |
| A:baleen Region6_s0.1 | 3 | -1.90 | +0.026 |
| A:baleen Region6_s0.2 | 3 | +0.06 | -0.577 |
| A:baleen Region6_s0.3 | 3 | -0.40 | -0.086 |
| A:baleen Region7_s0 | 3 | -0.35 | -0.407 |
| A:baleen Region7_s0.1 | 3 | -0.92 | -1.124 |
| A:baleen Region7_s0.2 | 3 | +0.15 | -0.134 |
| A:baleen Region7_s0.3 | 3 | -1.21 | -0.262 |
| B:baleen Region6_s0 | 3 | -0.10 | -0.204 |
| B:baleen Region6_s0.1 | 3 | +2.36 | +0.036 |
| B:baleen Region6_s0.2 | 3 | -0.16 | -0.566 |
| B:baleen Region6_s0.3 | 3 | -0.07 | -0.030 |
| B:baleen Region7_s0 | 3 | +0.11 | -0.232 |
| B:baleen Region7_s0.1 | 3 | -1.32 | -0.209 |
| B:baleen Region7_s0.2 | 3 | +0.03 | -0.028 |
| B:baleen Region7_s0.3 | 3 | -0.99 | -0.309 |

Per-instance Spearman (all variants of all retrains): Region6_s0 +0.40, Region6_s0.1 +0.70, Region6_s0.2 +0.23, Region6_s0.3 -0.04, Region7_s0 -0.52, Region7_s0.1 +0.44, Region7_s0.2 -0.65, Region7_s0.3 -0.46
Pooled Pearson: -0.09

## P2

- **C1** within-retrain pairs with |sim Δ| ≥ 0.25: 126; concordant 77 (0.61); sign-test p = 0.00791 → FAIL
- **C2** α=−1 minus none, cells {A,B}×8: mean sim Δ -0.320 vs proxy Δ -0.275 (same sign: True); sign agreement on |sim Δ| ≥ 0.25 cells: 8/9 → PASS
- **verdict: NOT VALID**

| cell | n | sim Δ | proxy Δ |
|---|---|---|---|
| A:baleen Region6_s0 | 3 | -0.43 | -0.285 |
| A:baleen Region6_s0.1 | 3 | -1.90 | +0.026 |
| A:baleen Region6_s0.2 | 3 | +0.06 | -0.577 |
| A:baleen Region6_s0.3 | 3 | -0.40 | -0.086 |
| A:baleen Region7_s0 | 3 | -0.35 | -0.407 |
| A:baleen Region7_s0.1 | 3 | -0.92 | -1.124 |
| A:baleen Region7_s0.2 | 3 | +0.15 | -0.134 |
| A:baleen Region7_s0.3 | 3 | -1.21 | -0.262 |
| B:baleen Region6_s0 | 3 | -0.10 | -0.204 |
| B:baleen Region6_s0.1 | 3 | +2.36 | +0.036 |
| B:baleen Region6_s0.2 | 3 | -0.16 | -0.566 |
| B:baleen Region6_s0.3 | 3 | -0.07 | -0.030 |
| B:baleen Region7_s0 | 3 | +0.11 | -0.232 |
| B:baleen Region7_s0.1 | 3 | -1.32 | -0.209 |
| B:baleen Region7_s0.2 | 3 | +0.03 | -0.028 |
| B:baleen Region7_s0.3 | 3 | -0.99 | -0.309 |

Per-instance Spearman (all variants of all retrains): Region6_s0 +0.40, Region6_s0.1 +0.70, Region6_s0.2 +0.23, Region6_s0.3 -0.04, Region7_s0 -0.52, Region7_s0.1 +0.44, Region7_s0.2 -0.65, Region7_s0.3 -0.46
Pooled Pearson: -0.09

## P3

- **C1** within-retrain pairs with |sim Δ| ≥ 0.25: 126; concordant 77 (0.61); sign-test p = 0.00791 → FAIL
- **C2** α=−1 minus none, cells {A,B}×8: mean sim Δ -0.320 vs proxy Δ -0.275 (same sign: True); sign agreement on |sim Δ| ≥ 0.25 cells: 8/9 → PASS
- **verdict: NOT VALID**

| cell | n | sim Δ | proxy Δ |
|---|---|---|---|
| A:baleen Region6_s0 | 3 | -0.43 | -0.285 |
| A:baleen Region6_s0.1 | 3 | -1.90 | +0.026 |
| A:baleen Region6_s0.2 | 3 | +0.06 | -0.577 |
| A:baleen Region6_s0.3 | 3 | -0.40 | -0.086 |
| A:baleen Region7_s0 | 3 | -0.35 | -0.407 |
| A:baleen Region7_s0.1 | 3 | -0.92 | -1.124 |
| A:baleen Region7_s0.2 | 3 | +0.15 | -0.134 |
| A:baleen Region7_s0.3 | 3 | -1.21 | -0.262 |
| B:baleen Region6_s0 | 3 | -0.10 | -0.204 |
| B:baleen Region6_s0.1 | 3 | +2.36 | +0.036 |
| B:baleen Region6_s0.2 | 3 | -0.16 | -0.566 |
| B:baleen Region6_s0.3 | 3 | -0.07 | -0.030 |
| B:baleen Region7_s0 | 3 | +0.11 | -0.232 |
| B:baleen Region7_s0.1 | 3 | -1.32 | -0.209 |
| B:baleen Region7_s0.2 | 3 | +0.03 | -0.028 |
| B:baleen Region7_s0.3 | 3 | -0.99 | -0.309 |

Per-instance Spearman (all variants of all retrains): Region6_s0 +0.40, Region6_s0.1 +0.70, Region6_s0.2 +0.23, Region6_s0.3 -0.04, Region7_s0 -0.52, Region7_s0.1 +0.44, Region7_s0.2 -0.65, Region7_s0.3 -0.46
Pooled Pearson: -0.09

