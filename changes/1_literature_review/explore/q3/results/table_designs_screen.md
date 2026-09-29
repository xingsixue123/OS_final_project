| config | description | instance | retrains (matched/all) | P100 mean +- sd (matched) | per retrain | vs Baleen ref | mean DT | J vs Baleen labels | day-1 label peak |
|---|---|---|---|---|---|---|---|---|---|
| T5 | PT, LSE peak (gamma 2) + DT blend beta=1 + trust region mu=5 | Region7_s0 | 3/3 | 39.35 +- 0.32 | 39.26, 39.70, 39.07 | -0.75 | 21.29 | 0.77 | 23.11 |
| T5 | PT, LSE peak (gamma 2) + DT blend beta=1 + trust region mu=5 | Region6_s0 | 3/3 | 43.01 +- 0.09 | 43.07, 42.91, 43.05 | -0.24 | 22.05 | 0.85 | 21.25 |
| PW4 | PT, peak-weighted DT knapsack (phi=(C/mean C)^4), no peak term | Region7_s0 | 1/1 | 40.26 | 40.26 | +0.16 | 21.59 | 1.00 | 27.63 |
| PW4 | PT, peak-weighted DT knapsack (phi=(C/mean C)^4), no peak term | Region6_s0 | 1/1 | 42.81 | 42.81 | -0.44 | 21.94 | 0.37 | 22.24 |
| SAT12 | PT T5 + forced coverage of episodes with block count>=12 at offsets>8MB | Region7_s0 | 1/1 | 39.37 | 39.37 | -0.73 | 21.48 | 0.83 | 24.66 |
| SAT12 | PT T5 + forced coverage of episodes with block count>=12 at offsets>8MB | Region6_s0 | 1/1 | 43.32 | 43.32 | +0.08 | 22.05 | 0.85 | 22.01 |
| C2 | PT on feature CELLS (op/ns/user, log size, history bins, #rows bin) + beta=0.5 + mu=2 | Region7_s0 | 3/3 | 38.93 +- 0.56 | 38.89, 39.50, 38.39 | -1.17 | 21.38 | 0.77 | 25.81 |
| C2 | PT on feature CELLS (op/ns/user, log size, history bins, #rows bin) + beta=0.5 + mu=2 | Region6_s0 | 3/3 | 43.21 +- 0.13 | 43.20, 43.08, 43.35 | -0.04 | 22.00 | 0.72 | 22.92 |
| SATB10 | coverage (b0>=10, >8MB) forced + DT/trust only (no peak term) | Region7_s0 | 0/1 |  |  |  |  |  |  |
| SATB10 | coverage (b0>=10, >8MB) forced + DT/trust only (no peak term) | Region6_s0 | 0/1 |  |  |  |  |  |  |
| P0 | PT, pure LSE peak (no DT blend, no trust region) | Region7_s0 | 3/3 | 39.16 +- 0.40 | 38.71, 39.31, 39.46 | -0.93 | 21.29 | 0.37 | 23.06 |
| P0 | PT, pure LSE peak (no DT blend, no trust region) | Region6_s0 | 3/3 | 42.93 +- 0.18 | 42.94, 42.75, 43.11 | -0.32 | 21.96 | 0.38 | 20.81 |
| T2 | PT, LSE peak + beta=0.5 + trust mu=2 | Region7_s0 | 3/3 | 39.36 +- 0.17 | 39.23, 39.30, 39.55 | -0.74 | 21.25 | 0.55 | 23.06 |
| T2 | PT, LSE peak + beta=0.5 + trust mu=2 | Region6_s0 | 3/3 | 42.78 +- 0.40 | 42.33, 43.03, 42.99 | -0.46 | 22.02 | 0.67 | 20.83 |
| R0 | control: Baleen's own labels through the solver path (identity) | Region7_s0 | 1/1 | 40.17 | 40.17 | +0.08 | 21.57 | 1.00 | 28.90 |
| R0 | control: Baleen's own labels through the solver path (identity) | Region6_s0 | 1/1 | 43.27 | 43.27 | +0.02 | 21.97 | 1.00 | 25.93 |
| TK10 | PT, top-10-window mean peak + beta=1 + trust mu=5 | Region7_s0 | 2/4 | 39.20 +- 0.23 | 39.04, 39.36, 39.08*, 39.48* | -0.89 | 21.35 | 0.78 | 23.51 |
| TK10 | PT, top-10-window mean peak + beta=1 + trust mu=5 | Region6_s0 | 3/3 | 43.07 +- 0.18 | 43.27, 42.95, 42.98 | -0.18 | 22.04 | 0.87 | 21.81 |
| L5 | PT, LSE peak + beta=0.5 + mu=2 + kNN feature-consistency couplings lam=5 | Region7_s0 | 3/3 | 39.12 +- 0.18 | 39.21, 39.23, 38.92 | -0.98 | 21.27 | 0.61 | 22.99 |
| L5 | PT, LSE peak + beta=0.5 + mu=2 + kNN feature-consistency couplings lam=5 | Region6_s0 | 3/3 | 43.21 +- 0.07 | 43.28, 43.21, 43.15 | -0.04 | 22.10 | 0.72 | 20.88 |
| T5c | T5 with zero-value additions removed (Baleen-order fill) | Region7_s0 | 1/1 | 39.90 | 39.90 | -0.20 | 21.40 | 0.87 | 23.17 |
| T5c | T5 with zero-value additions removed (Baleen-order fill) | Region6_s0 | 1/1 | 43.05 | 43.05 | -0.19 | 22.05 | 0.85 | 21.18 |

(* = not within +-1% WR; excluded from the mean)
