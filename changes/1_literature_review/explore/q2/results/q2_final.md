
## Q2 objective: F1, Ising = pt

| instance | budget | Ising mean +- sd (n) | best classical | classical mean +- sd (n) | gap % | Ising <= ? |
|---|---|---|---|---|---|---|
| full_Region6_s0.1 | 10 | 20.6606 +- 0.0111 (3) | ls | 20.6732 +- 0.0071 (3) | -0.061 | yes |
| full_Region6_s0.2 | 10 | 22.3456 +- 0.0035 (3) | ls | 22.3536 +- 0.0118 (3) | -0.036 | yes |
| full_Region6_s0.3 | 10 | 21.5559 +- 0.0085 (3) | ls | 21.5503 +- 0.0102 (3) | +0.026 | no |
| full_Region7_s0.1 | 10 | 23.1407 +- 0.0014 (3) | ls | 23.2084 +- 0.0081 (3) | -0.292 | yes |
| full_Region7_s0.2 | 10 | 25.4120 +- 0.0000 (3) | cpsat | 25.4120 +- 0.0000 (3) | +0.000 | tie |
| full_Region7_s0.3 | 10 | 22.0264 +- 0.0092 (3) | ls | 22.2138 +- 0.0150 (3) | -0.844 | yes |
| full_Region6_s0.1 | 60 | 20.6479 +- 0.0186 (3) | cpsat | 20.4875 +- 0.0689 (3) | +0.783 | no |
| full_Region6_s0.2 | 60 | 22.3118 +- 0.0169 (3) | cpsat | 22.1599 +- 0.0326 (3) | +0.686 | no |
| full_Region6_s0.3 | 60 | 21.5343 +- 0.0102 (3) | cpsat | 21.3746 +- 0.0353 (3) | +0.747 | no |
| full_Region7_s0.1 | 60 | 23.1360 +- 0.0059 (3) | milp | 23.1448 +- 0.0000 (1) | -0.038 | yes |
| full_Region7_s0.2 | 60 | 25.4120 +- 0.0000 (3) | milp | 25.4120 +- 0.0000 (1) | +0.000 | tie |
| full_Region7_s0.3 | 60 | 22.0047 +- 0.0036 (3) | cpsat | 21.9110 +- 0.0152 (3) | +0.428 | no |
| full_Region6_s0.1 | 300 | 20.6255 +- 0.0207 (3) | cpsat | 20.3847 +- 0.0274 (3) | +1.181 | no |
| full_Region6_s0.2 | 300 | 22.3202 +- 0.0069 (3) | cpsat | 21.9801 +- 0.0075 (3) | +1.547 | no |
| full_Region6_s0.3 | 300 | 21.5244 +- 0.0136 (3) | cpsat | 21.2057 +- 0.0085 (3) | +1.503 | no |
| full_Region7_s0.1 | 300 | 23.1260 +- 0.0080 (3) | cpsat | 23.1166 +- 0.0000 (3) | +0.040 | no |
| full_Region7_s0.2 | 300 | 25.4120 +- 0.0000 (3) | milp | 25.4120 +- 0.0000 (1) | +0.000 | tie |
| full_Region7_s0.3 | 300 | 22.0091 +- 0.0065 (3) | cpsat | 21.7771 +- 0.0200 (3) | +1.065 | no |

         n_le  n_tie  n      ising  classical  obj_ok  avg_strict
budget                                                          
10.0       5      1  6  22.523523  22.568558    True        True
60.0       2      1  6  22.507773  22.414942   False       False
300.0      1      1  6  22.502867  22.312698   False       False
Objective criterion: budgets with >=5/6 = 1 (need >= 2) -> FAIL
Average criterion (all instance-budgets): Ising 22.5114 vs classical 22.4321 -> FAIL

## Simulated offline P100 (300 s solutions), Ising = pt

         instance  ising_p100  ising_sd  ising_n  ising_unmatched  ising_wr classical  classical_p100  classical_n   r0_p100  trackA_opt_p100
full_Region7_s0.1   27.606093  0.164142        3                0 35.583412     cpsat       27.380358            3 33.675829        33.675829
full_Region7_s0.2   27.896999  0.544918        3                0 35.752798      milp       28.206925            1 35.277357        35.277357
full_Region7_s0.3   26.759205  0.207860        3                0 35.293092     cpsat       26.638641            3 31.228357        31.228357
full_Region6_s0.1   26.406517  0.197864        3                0 35.761343     cpsat       26.112444            3 30.901256        30.901256
full_Region6_s0.2   26.382705  0.106114        3                0 35.622484     cpsat       26.227985            3 30.615595        30.615595
full_Region6_s0.3   27.324786  0.170359        3                0 35.611533     cpsat       27.154979            3 31.964177        31.964177
Simulation clause (mean over 6 instances): Ising 27.063 vs classical 26.954 -> FAIL
Q1 vs Track A baselines.csv OPT: below on 6/6; mean 27.063 vs 32.277 -> PASS
Q1 vs our R0 (same pipeline): below on 6/6; mean 27.063 vs 32.277 -> PASS

## Q2 objective: F1, Ising = eim

| instance | budget | Ising mean +- sd (n) | best classical | classical mean +- sd (n) | gap % | Ising <= ? |
|---|---|---|---|---|---|---|
| full_Region6_s0.1 | 10 | 20.6685 +- 0.0109 (3) | ls | 20.6732 +- 0.0071 (3) | -0.023 | yes |
| full_Region6_s0.2 | 10 | 22.4056 +- 0.0508 (3) | ls | 22.3536 +- 0.0118 (3) | +0.233 | no |
| full_Region6_s0.3 | 10 | 21.5728 +- 0.0181 (3) | ls | 21.5503 +- 0.0102 (3) | +0.104 | no |
| full_Region7_s0.1 | 10 | 23.1795 +- 0.0094 (3) | ls | 23.2084 +- 0.0081 (3) | -0.125 | yes |
| full_Region7_s0.2 | 10 | 25.4120 +- 0.0000 (3) | cpsat | 25.4120 +- 0.0000 (3) | +0.000 | tie |
| full_Region7_s0.3 | 10 | 22.0795 +- 0.0173 (3) | ls | 22.2138 +- 0.0150 (3) | -0.605 | yes |
| full_Region6_s0.1 | 60 | 20.5910 +- 0.0241 (3) | cpsat | 20.4875 +- 0.0689 (3) | +0.505 | no |
| full_Region6_s0.2 | 60 | 22.3144 +- 0.0232 (3) | cpsat | 22.1599 +- 0.0326 (3) | +0.697 | no |
| full_Region6_s0.3 | 60 | 21.4939 +- 0.0079 (3) | cpsat | 21.3746 +- 0.0353 (3) | +0.558 | no |
| full_Region7_s0.1 | 60 | 23.1566 +- 0.0040 (3) | milp | 23.1448 +- 0.0000 (1) | +0.051 | no |
| full_Region7_s0.2 | 60 | 25.4120 +- 0.0000 (3) | milp | 25.4120 +- 0.0000 (1) | +0.000 | tie |
| full_Region7_s0.3 | 60 | 22.0427 +- 0.0324 (3) | cpsat | 21.9110 +- 0.0152 (3) | +0.601 | no |
| full_Region6_s0.1 | 300 | 20.5418 +- 0.0129 (3) | cpsat | 20.3847 +- 0.0274 (3) | +0.771 | no |
| full_Region6_s0.2 | 300 | 22.2447 +- 0.0251 (3) | cpsat | 21.9801 +- 0.0075 (3) | +1.204 | no |
| full_Region6_s0.3 | 300 | 21.4322 +- 0.0189 (3) | cpsat | 21.2057 +- 0.0085 (3) | +1.068 | no |
| full_Region7_s0.1 | 300 | 23.1546 +- 0.0000 (3) | cpsat | 23.1166 +- 0.0000 (3) | +0.164 | no |
| full_Region7_s0.2 | 300 | 25.4120 +- 0.0000 (3) | milp | 25.4120 +- 0.0000 (1) | +0.000 | tie |
| full_Region7_s0.3 | 300 | 21.9951 +- 0.0027 (3) | cpsat | 21.7771 +- 0.0200 (3) | +1.001 | no |

         n_le  n_tie  n      ising  classical  obj_ok  avg_strict
budget                                                          
10.0       4      1  6  22.552969  22.568558   False        True
60.0       1      1  6  22.501767  22.414942   False       False
300.0      1      1  6  22.463395  22.312698   False       False
Objective criterion: budgets with >=5/6 = 0 (need >= 2) -> FAIL
Average criterion (all instance-budgets): Ising 22.5060 vs classical 22.4321 -> FAIL

## Simulated offline P100 (300 s solutions), Ising = eim

         instance  ising_p100  ising_sd  ising_n  ising_unmatched  ising_wr classical  classical_p100  classical_n   r0_p100  trackA_opt_p100
full_Region7_s0.1   27.341956  0.224230        3                0 35.737550     cpsat       27.380358            3 33.675829        33.675829
full_Region7_s0.2   28.019840  0.176464        3                0 35.668374      milp       28.206925            1 35.277357        35.277357
full_Region7_s0.3   26.487644  0.306815        3                0 35.444867     cpsat       26.638641            3 31.228357        31.228357
full_Region6_s0.1   25.943872  0.388843        3                0 35.576878     cpsat       26.112444            3 30.901256        30.901256
full_Region6_s0.2   26.536206  0.240022        3                0 35.791189     cpsat       26.227985            3 30.615595        30.615595
full_Region6_s0.3   27.378486  0.075492        3                0 35.554639     cpsat       27.154979            3 31.964177        31.964177
Simulation clause (mean over 6 instances): Ising 26.951 vs classical 26.954 -> PASS
Q1 vs Track A baselines.csv OPT: below on 6/6; mean 26.951 vs 32.277 -> PASS
Q1 vs our R0 (same pipeline): below on 6/6; mean 26.951 vs 32.277 -> PASS

Track A OPT (baselines_summary.csv): {'full_Region6_s0': 35.556, 'full_Region6_s0.1': 30.901, 'full_Region6_s0.2': 30.616, 'full_Region6_s0.3': 31.964, 'full_Region7_s0': 34.522, 'full_Region7_s0.1': 33.676, 'full_Region7_s0.2': 35.277, 'full_Region7_s0.3': 31.228}
