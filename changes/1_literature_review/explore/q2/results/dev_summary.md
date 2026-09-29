
### F1, 10 s (value = mean over dev of objective / peak-aware greedy - 1, in %)

| solver | family | trials | value % | Region7 % | Region6 % |
|---|---|---|---|---|---|
| pt | ising | 10 | -15.010 | -12.067 | -17.953 |
| eim | ising | 10 | -14.973 | -11.968 | -17.978 |
| ls | classical | 10 | -14.901 | -11.863 | -17.939 |
| milp | classical | 10 | -14.760 | -11.969 | -17.550 |
| cpsat | classical | 10 | -14.566 | -11.764 | -17.368 |
| hlns | ising | 10 | -14.066 | -11.651 | -16.482 |
| mq | ising | 10 | -13.891 | -11.614 | -16.168 |
| sb | ising | 10 | -13.217 | -11.176 | -15.258 |
| lp | classical | 10 | -13.172 | -11.086 | -15.258 |

### F1, 60 s (value = mean over dev of objective / peak-aware greedy - 1, in %)

| solver | family | trials | value % | Region7 % | Region6 % |
|---|---|---|---|---|---|
| cpsat | classical | 3 | -15.530 | -12.061 | -18.998 |
| ls | classical | 3 | -15.229 | -11.930 | -18.529 |
| pt | ising | 3 | -15.167 | -12.093 | -18.241 |
| eim | ising | 3 | -15.110 | -11.994 | -18.225 |
| milp | classical | 3 | -14.798 | -11.936 | -17.659 |
| hlns | ising | 3 | -14.796 | -11.997 | -17.596 |
| mq | ising | 3 | -14.036 | -11.849 | -16.222 |
| sb | ising | 3 | -13.236 | -11.215 | -15.258 |
| lp | classical | 3 | -13.149 | -10.963 | -15.336 |

### F2b_tau_rel0.6, 10 s (value = mean over dev of objective / peak-aware greedy - 1, in %)

| solver | family | trials | value % | Region7 % | Region6 % |
|---|---|---|---|---|---|
| ls | classical | 10 | -0.143 | -0.094 | -0.193 |
| pt | ising | 10 | -0.134 | -0.072 | -0.196 |
| eim | ising | 10 | -0.104 | -0.038 | -0.169 |
| hlns | ising | 10 | -0.059 | -0.046 | -0.073 |
| lp | classical | 10 | -0.020 | -0.008 | -0.032 |
| milp | classical | 10 | -0.019 | -0.008 | -0.031 |
| mq | ising | 10 | -0.019 | -0.024 | -0.014 |
| cpsat | classical | 10 | -0.010 | -0.000 | -0.020 |
| sb | ising | 10 | +0.000 | +0.000 | +0.000 |
| scip | classical | 10 | +0.000 | +0.000 | +0.000 |

trials.csv rows by phase/status:
 phase  status              
tune   contaminated_overlap      8
       ok                      455
