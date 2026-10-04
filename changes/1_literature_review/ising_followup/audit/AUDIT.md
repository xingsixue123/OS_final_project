# Ising / QUBO solvers for peak-aware admission: CPU benchmark on synthetic instances

Everything lives in `audit/`: `instance.py`, `solvers/*.py`, `run_bench.py`, `make_tables.py`, `results.csv`, `results/raw/*.json` (one JSON per job), `results/logs/` (per-job stdout and outer-loop logs; the logs are opened in append mode, so a job that was killed and restarted shows both runs), and `env.lock.txt`. No Baleen code was touched and no Baleen simulation was run. Nothing was committed.

## 1. Environment

* Machine: AMD Ryzen 9 9900X (12 cores / 24 hardware threads), 123 GB RAM, **no GPU**. Everything ran on the CPU.
* Sandbox: `env.sh` redirects HOME, the XDG dirs, the pip and conda caches, TMPDIR, MPL, TORCH and NUMBA to `audit/` and sets `CONDA_REGISTER_ENVS=false` and `PYTHONNOUSERSITE=1`. `.leak_marker` was touched before any install.
* Conda: `conda create -p audit/env python=3.11` failed at first with `CondaToSNonInteractiveError`. The redirected HOME has no accepted Anaconda ToS for `repo.anaconda.com`. Instead of accepting the ToS (that would have written to the real `<home file>`), I used `--override-channels -c conda-forge`, which gave Python 3.11.16. `<home file>` was not modified; see the leak check in section 8.
* Package versions (full list in `env.lock.txt`): numpy 2.4.6, scipy 1.17.1, highspy 1.15.1, torch 2.14.0+cpu (CPU wheel index), simulated-bifurcation 2.0.0, dwave-samplers 1.8.0, dimod 0.12.22, openjij 0.12.2 (jij-cimod 1.7.5), cim-optimizer 1.0.4, mindquantum 0.12.0, numba 0.67.0. numba was added for the true-objective local search.
* Threads: each job sets `torch.set_num_threads` and OMP/OPENBLAS/MKL/NUMBA_NUM_THREADS explicitly. The torch-based solvers (mfSB, SB package) used 4 threads, cim-optimizer used 2, and everything else used 1. The one exception is `sb_discrete` at n=50k, which used 8 threads and a 900 s cap (see caveats). Each row's thread count is in `results.csv` under `threads` and `params.torch_threads`. Jobs ran in parallel through a core- and memory-aware scheduler. For about 40 minutes a second scheduler oversubscribed the machine (up to ~30 runnable threads on 24 hardware threads). **Wall times are therefore contended times**, not isolated per-solver timings.

### Install outcomes
| package | result |
|---|---|
| numpy, scipy, highspy, torch (CPU), simulated-bifurcation, dwave-samplers, dimod, openjij | installed from PyPI with no problems |
| cim-optimizer | `pip install cim-optimizer` worked (1.0.4, sdist build under 1 min), so the GitHub fallback was not needed. Its API differs from the docs: `Ising(J,h).solve()` returns a `solver` object, the results are in `.result`, and there is no `ahc_ext_time_stop`. Because h ≠ 0 it runs the external-field AHC ("extAHC") path. |
| mindquantum 0.12.0 (optional item 1) | installed in under 1 min. The QAIA BSB/DSB/CAC CPU backend works with scipy-sparse J and with the matrix-free J swap. |
| numba | installed, and used by the local search |

## 2. Instance (`instance.py`)
* m = 144 ten-minute windows. The diurnal baseline has a main peak around window 84 (about 14:00), a morning bump, and a small evening bump. A constant floor is chosen by bisection so that **peak/mean = 2.00 exactly**.
* Episodes: length ∈ {1, 2, 3} with probabilities (0.40, 0.35, 0.25). The start is drawn from a mixture of 20% uniform and 80% ∝ diurnal shape (biased toward busy hours) and clipped so the episode fits in the day.
* Savings: d_{e,w} = (episode factor, lognormal σ=1.2) × (per-window factor, lognormal σ=0.5). This is heavy-tailed.
* Write cost: s_e = (Σ_w d_{e,w})^0.8 × lognormal(0, 0.7), normalized to mean 1. The log-log correlation with total savings is about 0.84.
* Baseline load: C_w = K·shape_w with K = 1.5·max_w(S_w/shape_w), so C_w ≥ 1.5·S_w for every window, where S_w is all savings available in w. Everything is scaled so that max C = 1, which makes peaks read as fractions of the un-admitted peak.
* Budget: W = bytes of the greedy savings-per-byte prefix that admits round(0.06·n) episodes. That is 2.9–3.4% of the total bytes.
* D is scipy CSR (n×m). nnz(D) ≈ 1.85·n. The implied QUBO matrix Q = D·diag(α)·Dᵀ has up to ≈ 3.0e4 / 2.9e6 / 7.2e7 / 1.1e9 nonzeros at n = 1k / 10k / 50k / 200k. As a dense float32 matrix it takes 0.004 / 0.4 / 10 / 160 GB.
* Sizes: n ∈ {1k, 10k, 50k, 200k}, seeds {0, 1, 2}. The expensive dense and explicit-sparse solvers at 50k ran 1 seed. The explicit Ising solvers were not run at 200k, and neither was any solver that needs Q.

## 3. Methods (all return a binary x, and then the same repair is applied)
**Shared repair** (`solvers/common.py`). Phase 1: while sᵀx > W, drop the selected episode with the smallest d_{e,w*}/s_e, where w* is the current argmax window, breaking ties by largest s_e. Phase 2: while budget remains, add the unselected, budget-fitting episode with the largest (strict max-load reduction)/s_e, and stop when no add strictly reduces the max. The first implementation (`repair_ref`) was O(n) per step and turned out to be the bottleneck at n ≥ 50k: up to 59 s per call. I replaced it with an exact equivalent. Only episodes covering the unique argmax window can reduce the max, and an episode not covering w* has key 0, so the largest such s_e is dropped first. On 18 test inputs (greedy, LP-round, and random x at 0.3–20% density, n up to 50k) the new version gives **bit-identical output** and is up to 34× faster. Jobs finished before the switch have identical solutions and only slower timing.

1. `greedy`: sort by Σ_w d/s descending and admit the prefix within W. This is the Baleen-style rule.
2. `lp`: HiGHS LP on the epigraph model. It gives z_LP and the number of fractional variables (7–26, as expected from a vertex solution with 145 rows), then round-down and repair.
3. `milp`: HiGHS MILP with a 60 s limit at n ≤ 10k and 300 s above, 1 thread. The raw result is the incumbent, which then goes through the repair.
4. QUBO surrogate (`solvers/qubo.py`): E(x) = Σ_w α_w (C_w − τ − (Dᵀx)_w)² + μ sᵀx. Every inner solver runs inside the **same outer loop**:
   * Initialization from greedy: α_w = clip(exp(β(L_w/max L − 1)), 1e-3, 1) with β = 8, and τ = greedy peak − δ, where δ = 0.3% of the greedy peak.
   * Up to 10 outer iterations, each bisecting μ in log space. The first iteration uses 8 steps over [1e-4·μ_max, μ_max], where μ_max is the price at which no single episode has negative marginal energy. Later iterations use 4 steps over [μ_prev/4, 4μ_prev]. Bisection stops early once the raw use lands in [0.95, 1.0]·W.
   * Every bisection candidate is repaired, and the iteration keeps the best repaired peak. Then α is updated from that candidate's loads, and τ = min(best solver peak, greedy peak) − δ.
   * Caps: 40 inner calls and a wall-time cap of 300 / 900 / 2400 / 2400 s at n = 1k / 10k / 50k / 200k. The cap is checked between calls, so a single long call can overrun it.
   * The reported "raw" x is the solver's own inner output from the iterate with the best repaired peak. Greedy is only used to seed α and τ and is never reported as a solver result.
   * Inner solvers:
     * 4a `sb_ballistic` / `sb_discrete`: `simulated_bifurcation.minimize` on the **dense** float32 Q plus linear terms, domain="binary", early stopping. 64 agents and 1000 steps at n ≤ 10k; 16 agents and 500 steps at 50k.
     * 4b `dwave_sa`: SimulatedAnnealingSampler on a dimod BQM built from the **sparse** upper triangle of Q. 16 reads × 1000 sweeps at n ≤ 10k; 4 × 200 at 50k. `dwave_tabu`: TabuSampler, 4 reads with a 2 s timeout each.
     * 4c `openjij_sa`: SASampler on the same BQM, same reads and sweeps as 4b.
     * 4d `cim_extahc`: cim-optimizer on dense J and h, scaled by the max absolute row-sum. 4 parallel runs × 1000 time steps, random hyperparameter tuning off, defaults otherwise.
     * 4e `mfsb`: my **matrix-free ballistic SB** in PyTorch (`solvers/mfsb.py`), following Goto et al. 2021. It uses x = (1+σ)/2, J = −½·offdiag(Q), h = −½(Q1 + c), and e0 = ¼1ᵀQ1 + ¼trQ + ½cᵀ1 + k. The local field J·y + h is computed as −½(D(α⊙(Dᵀy)) − diag(Q)⊙y) + h. Dᵀy is a sparse CSR matmul and D·z uses 3 banded gathers, so the n×n matrix is never formed. ξ0 = 0.7·√N / √(‖J‖²_F + 2‖h‖²), with ‖Q‖²_F = tr(AMAM) and M = DᵀD (144×144). dt = 1.25, a(t) ramps linearly from 0 to 1, and the walls are inelastic. Settings: 64 agents × 1000 steps at n ≤ 50k and 16 agents × 1000 steps at 200k, float32. **Energy check on n = 1000:** the Ising energy, the matrix-free QUBO energy, and the explicit xᵀQx + cᵀx + k agree to a max relative error of **1.7e-16** (Lagrangian) and **3.0e-12** (with the penalty term P(sᵀx−W)²). The MindQuantum matrix-free operator matches the explicit sparse J to 3.4e-7 relative (float32).
   * Optional item 1, MindQuantum QAIA (`solvers/inner_mq.py`): `mq_bsb`, `mq_dsb` and `mq_cac` use an explicit scipy-sparse J with batch 32 and 1000 iterations. `mq_*_mf` builds each solver with an empty sparse J, then swaps in an operator whose `.dot` and `@` compute the matrix-free field. ξ is supplied from the MQ default formula. For CAC I reproduce the library's CPU formula `sum(J**2)`, which on a scipy matrix is actually Σ(J@J) = ‖J1‖². **BSB and DSB matrix-free give bit-identical solutions to the explicit versions** (same seeds, same rows in the tables).
5. Optional item 2, `ls_greedy` / `ls_lp` (`solvers/local_search.py`, numba): simulated annealing on the **true** objective, with no QUBO. It keeps L_w and the budget use incrementally, so each move touches 1–3 windows. The move mix is 70% swap (add an unselected episode covering one of the top-3 windows and drop a random selected one), 15% add, and 15% drop. The budget is a hard constraint. Acceptance is on a log-sum-exp smooth max with g = 2000/peak, and the true max is tracked. Moves = min(3e7, max(2e6, 300n)), with T geometric from 2e-3·peak down to 1e-6·peak. It is warm-started from greedy and from LP round-down.
6. Extra attribution baseline, `repair_only`: x_raw = 0 fed through the shared repair, which amounts to a pure peak-aware greedy add. I added it because several "solvers" return almost-empty raw vectors, and then the repair does all the work.
7. Lagrangian vs penalty check at n = 1000: `mfsb_penalty_k{0.1,1,10}` uses the same outer loop with μ = 0, no bisection (1 call per outer iteration, so 10 calls), and a P(sᵀx − W)² term with P = k·μ_max/W. The rank-1 s sᵀ term is also applied matrix-free.

Metrics per row in `results.csv`: peak_raw, peak_rep, use_raw, use_rep, nsel, z_lp, greedy_peak, headroom = greedy − z_LP, gap_abs = peak_rep − z_LP, gap_pct = 100·gap_abs/headroom, wall_time, peak RSS (ru_maxrss of the job process), threads, params (JSON), and extra (JSON: inner calls, inner time, MILP gap and nodes, LP fractional count, repair drops and adds). For greedy, repair_only, lp, milp and ls, `wall_time` excludes the repair (that is in `repair_time_incl`). For the QUBO methods, `wall_time` includes the repair of every candidate.

## 4. Results (median over seeds; `seeds` column = number of seeds; peaks normalized so un-admitted max C = 1)

Columns: peak raw/repaired = max_w L_w of the method's raw x / after the shared repair; use = sᵀx/W; gap = repaired peak − z_LP; gap % = gap/(greedy − z_LP)·100; wall s = method wall time (QUBO arms include repairs); inner calls = per-seed number of QUBO solver calls. MILP at n=200k produced no incumbent (not shown; `status=no_solution` in results.csv).

### n = 1,000  (median over seeds: z_LP = 0.95670, greedy peak = 0.99438, headroom greedy - z_LP = 0.03658 = 3.68% of greedy peak)

| method | seeds | peak raw | peak repaired | use raw | use rep | gap abs | gap % of headroom | wall s | peak RSS MB | inner calls |
|---|---|---|---|---|---|---|---|---|---|---|
| greedy | 3 | 0.99438 | 0.99438 | 1.000 | 1.000 | 0.03658 | 100.0 | 0.0 | 244 |  |
| repair_only | 3 | 1.00000 | 0.97319 | 0.000 | 0.983 | 0.01649 | 28.3 | 0.0 | 244 |  |
| lp | 3 | 0.97927 | 0.96662 | 0.759 | 0.992 | 0.00621 | 9.8 | 0.0 | 244 |  |
| milp | 3 | 0.95861 | 0.95861 | 1.000 | 1.000 | 0.00114 | 1.9 | 0.7 | 250 |  |
| ls_greedy | 3 | 0.96175 | 0.96175 | 0.998 | 0.998 | 0.00505 | 11.2 | 2.5 | 357 |  |
| ls_lp | 3 | 0.96175 | 0.96175 | 1.000 | 1.000 | 0.00157 | 3.4 | 2.9 | 357 |  |
| mfsb | 3 | 0.96997 | 0.96713 | 0.929 | 0.998 | 0.01043 | 19.5 | 8.7 | 262 | 37/40/40 |
| sb_ballistic | 3 | 0.99838 | 0.97874 | 0.563 | 0.998 | 0.02205 | 57.9 | 34.3 | 333 | 34/40/40 |
| sb_discrete | 3 | 0.99308 | 0.98269 | 0.741 | 0.995 | 0.02599 | 57.3 | 36.2 | 334 | 35/40/40 |
| dwave_sa | 3 | 0.96204 | 0.96053 | 0.980 | 0.992 | 0.00383 | 10.5 | 8.9 | 273 | 39/28/40 |
| dwave_tabu | 3 | 0.96362 | 0.96165 | 0.907 | 0.993 | 0.00495 | 13.5 | 305.2 | 312 | 38/38/35 |
| openjij_sa | 3 | 0.96915 | 0.96378 | 0.857 | 0.996 | 0.00708 | 14.2 | 18.6 | 286 | 40/40/38 |
| cim_extahc | 3 | 1.00000 | 0.97225 | 0.002 | 0.984 | 0.01555 | 28.3 | 76.7 | 657 | 40/40/35 |
| mq_bsb | 3 | 0.96620 | 0.96315 | 0.871 | 0.997 | 0.00645 | 15.2 | 12.6 | 303 | 32/33/40 |
| mq_dsb | 3 | 0.96457 | 0.96105 | 0.908 | 0.995 | 0.00436 | 11.9 | 14.2 | 303 | 30/40/40 |
| mq_cac | 3 | 0.99652 | 0.96452 | 0.060 | 0.980 | 0.00783 | 21.4 | 110.7 | 305 | 40/40/40 |
| mq_bsb_mf | 3 | 0.96620 | 0.96315 | 0.871 | 0.997 | 0.00645 | 15.2 | 7.3 | 301 | 32/33/40 |
| mq_dsb_mf | 3 | 0.96457 | 0.96105 | 0.908 | 0.995 | 0.00436 | 11.9 | 8.3 | 303 | 30/40/40 |
| mq_cac_mf | 3 | 0.98669 | 0.96452 | 0.350 | 0.984 | 0.00783 | 20.1 | 94.6 | 303 | 40/40/40 |
| mfsb_penalty_k0.1 | 3 | 0.96555 | 0.96368 | 0.925 | 0.987 | 0.00698 | 17.1 | 3.1 | 262 | 10/10/10 |
| mfsb_penalty_k1.0 | 3 | 0.97865 | 0.97001 | 0.653 | 0.997 | 0.01331 | 24.2 | 1.4 | 260 | 10/10/10 |
| mfsb_penalty_k10.0 | 3 | 0.99919 | 0.97685 | 0.307 | 0.998 | 0.02015 | 35.4 | 1.8 | 261 | 10/10/10 |

### n = 10,000  (median over seeds: z_LP = 0.86918, greedy peak = 0.97731, headroom greedy - z_LP = 0.10361 = 10.60% of greedy peak)

| method | seeds | peak raw | peak repaired | use raw | use rep | gap abs | gap % of headroom | wall s | peak RSS MB | inner calls |
|---|---|---|---|---|---|---|---|---|---|---|
| greedy | 3 | 0.97731 | 0.97731 | 1.000 | 1.000 | 0.10361 | 100.0 | 0.0 | 251 |  |
| repair_only | 3 | 1.00000 | 0.91838 | 0.000 | 0.999 | 0.04822 | 43.1 | 0.0 | 251 |  |
| lp | 3 | 0.89244 | 0.87597 | 0.910 | 1.000 | 0.00679 | 6.9 | 0.0 | 251 |  |
| milp | 3 | 0.86980 | 0.86980 | 1.000 | 1.000 | 0.00095 | 0.8 | 60.1 | 377 |  |
| ls_greedy | 3 | 0.88407 | 0.88406 | 1.000 | 1.000 | 0.01112 | 10.7 | 12.8 | 358 |  |
| ls_lp | 3 | 0.88451 | 0.88309 | 1.000 | 1.000 | 0.01391 | 13.8 | 9.8 | 358 |  |
| mfsb | 3 | 0.90217 | 0.89132 | 0.870 | 1.000 | 0.01855 | 19.0 | 81.6 | 341 | 37/34/40 |
| sb_ballistic | 3 | 0.99998 | 0.94486 | 0.469 | 0.999 | 0.07487 | 68.7 | 1137.0 | 2643 | 3/3/3 |
| sb_discrete | 3 | 0.98873 | 0.95169 | 0.745 | 1.000 | 0.08251 | 73.8 | 1023.9 | 2662 | 3/3/8 |
| dwave_sa | 3 | 0.91773 | 0.90534 | 0.502 | 0.999 | 0.03910 | 32.6 | 938.8 | 642 | 8/9/9 |
| dwave_tabu | 1 | 0.89960 | 0.89221 | 0.802 | 0.999 | 0.02304 | 23.6 | 941.9 | 5246 | 17 |
| openjij_sa | 3 | 0.88712 | 0.88040 | 0.922 | 1.000 | 0.01193 | 10.0 | 687.5 | 918 | 32/38/33 |
| cim_extahc | 1 | 1.00000 | 0.91929 | 0.000 | 0.998 | 0.05012 | 51.2 | 1095.6 | 3681 | 1 |
| mq_bsb | 3 | 0.99971 | 0.91440 | 0.008 | 0.999 | 0.04351 | 40.2 | 983.6 | 381 | 10/10/10 |
| mq_dsb | 3 | 0.98111 | 0.91457 | 0.066 | 1.000 | 0.04280 | 40.3 | 970.4 | 381 | 9/8/3 |
| mq_cac | 3 | 0.99610 | 0.91721 | 0.050 | 1.000 | 0.04775 | 42.0 | 1046.4 | 416 | 7/7/7 |
| mq_bsb_mf | 3 | 0.93157 | 0.90660 | 0.829 | 1.000 | 0.04037 | 33.7 | 929.7 | 316 | 19/17/21 |
| mq_dsb_mf | 3 | 0.91205 | 0.88986 | 0.889 | 1.000 | 0.02068 | 21.1 | 723.0 | 319 | 38/34/32 |
| mq_cac_mf | 3 | 0.99594 | 0.91472 | 0.039 | 1.000 | 0.04813 | 40.2 | 921.0 | 321 | 8/8/9 |

### n = 50,000  (median over seeds: z_LP = 0.83821, greedy peak = 0.95118, headroom greedy - z_LP = 0.11228 = 11.80% of greedy peak)

| method | seeds | peak raw | peak repaired | use raw | use rep | gap abs | gap % of headroom | wall s | peak RSS MB | inner calls |
|---|---|---|---|---|---|---|---|---|---|---|
| greedy | 3 | 0.95118 | 0.95118 | 1.000 | 1.000 | 0.11228 | 100.0 | 0.0 | 277 |  |
| repair_only | 3 | 1.00000 | 0.89876 | 0.000 | 1.000 | 0.06054 | 53.8 | 0.0 | 278 |  |
| lp | 3 | 0.84553 | 0.83908 | 0.983 | 1.000 | 0.00122 | 1.1 | 0.1 | 280 |  |
| milp | 3 | 0.83913 | 0.83906 | 1.000 | 1.000 | 0.00128 | 1.1 | 300.3 | 720 |  |
| ls_greedy | 3 | 0.85944 | 0.85944 | 1.000 | 1.000 | 0.01918 | 16.4 | 33.2 | 370 |  |
| ls_lp | 3 | 0.84333 | 0.84222 | 0.994 | 1.000 | 0.00253 | 2.0 | 35.2 | 373 |  |
| mfsb | 3 | 0.86469 | 0.84961 | 0.770 | 1.000 | 0.01163 | 10.6 | 1532.4 | 499 | 40/40/40 |
| sb_ballistic | 1 | 1.00000 | 0.90756 | 0.134 | 1.000 | 0.07149 | 63.7 | 4361.2 | 58180 | 1 |
| sb_discrete | 1 | 0.91043 | 0.97847 | 9.865 | 1.000 | 0.14240 | 126.8 | 1038.2 | 58206 | 1 |
| dwave_sa | 1 | 0.94818 | 0.88912 | 0.115 | 1.000 | 0.05305 | 47.2 | 2834.1 | 6081 | 8 |
| openjij_sa | 1 | 0.94830 | 0.88803 | 0.115 | 1.000 | 0.05196 | 46.3 | 2858.4 | 16683 | 5 |
| mq_bsb_mf | 1 | 0.90775 | 0.87771 | 0.577 | 1.000 | 0.04164 | 37.1 | 2521.0 | 378 | 12 |
| mq_dsb_mf | 1 | 0.90731 | 0.87393 | 0.753 | 1.000 | 0.03786 | 33.7 | 2415.5 | 392 | 11 |
| mq_cac_mf | 1 | 0.98964 | 0.89273 | 0.057 | 1.000 | 0.05666 | 50.5 | 2426.1 | 392 | 6 |

### n = 200,000  (median over seeds: z_LP = 0.84530, greedy peak = 0.96065, headroom greedy - z_LP = 0.11367 = 11.83% of greedy peak)

| method | seeds | peak raw | peak repaired | use raw | use rep | gap abs | gap % of headroom | wall s | peak RSS MB | inner calls |
|---|---|---|---|---|---|---|---|---|---|---|
| greedy | 3 | 0.96065 | 0.96065 | 1.000 | 1.000 | 0.11367 | 100.0 | 0.0 | 376 |  |
| repair_only | 3 | 1.00000 | 0.90219 | 0.000 | 1.000 | 0.05689 | 49.7 | 0.0 | 380 |  |
| lp | 3 | 0.84632 | 0.84548 | 0.997 | 1.000 | 0.00025 | 0.2 | 1.3 | 387 |  |
| ls_greedy | 3 | 0.85932 | 0.85932 | 1.000 | 1.000 | 0.01408 | 12.5 | 91.4 | 448 |  |
| ls_lp | 3 | 0.84595 | 0.84582 | 0.999 | 1.000 | 0.00052 | 0.5 | 90.4 | 448 |  |
| mfsb | 3 | 0.86363 | 0.85465 | 0.844 | 1.000 | 0.00934 | 8.3 | 2069.8 | 512 | 40/40/38 |
| mq_bsb_mf | 1 | 0.97011 | 0.89694 | 0.046 | 1.000 | 0.05524 | 46.4 | 2687.5 | 637 | 3 |
| mq_dsb_mf | 1 | 0.96485 | 0.89460 | 0.083 | 1.000 | 0.05289 | 44.5 | 2885.7 | 685 | 3 |
| mq_cac_mf | 1 | 0.99494 | 0.89664 | 0.042 | 1.000 | 0.05494 | 46.2 | 3408.9 | 686 | 2 |


## 5. Findings

### Headroom (greedy peak − z_LP) on this synthetic instance
The median is **0.0366 (3.7% of the greedy peak) at n = 1k**, 0.104 (10.6%) at 10k, 0.112 (11.8%) at 50k, and 0.114 (11.8%) at 200k. The peak-unaware savings-per-byte greedy leaves a lot on the table. **LP round-down + repair captures 90–99.8% of that headroom in 0.002–1.7 s**: the gap is 9.8% of headroom at 1k, 6.9% at 10k, 1.1% at 50k and 0.2% at 200k. The relaxation gets tighter as n grows because only ≤ 26 LP variables are fractional.

### Does any Ising solver beat greedy?
Yes, and trivially so. After the shared repair, every QUBO/Ising arm beats greedy on every seed at every size, with one exception: `sb_discrete` at 50k. It made one call, returned raw use = 9.9·W, and after repair its peak was 0.978, worse than greedy's 0.948. **This is not evidence for Ising.** The repair alone, starting from x = 0 (`repair_only`, a pure peak-aware greedy add), already removes 46–72% of the headroom. Several "solvers" return an almost-empty raw vector and are really just `repair_only`: cim-optimizer returns use_raw ≈ 0.000–0.002 at 1k and 10k; MQ CAC 0.04–0.06; the explicit `mq_bsb` at 10k 0.008. Their repaired peaks sit on top of `repair_only`, for example cim at 10k gives 0.9193 against repair_only's 0.9184. The honest question is whether they beat repair_only, and the per-seed counts are:
* n = 1k: dwave_sa, dwave_tabu, openjij, mfsb, mq_bsb/dsb (explicit and mf) beat it 3/3. cim beats it 1/3 and CAC 2/3. **sb_ballistic, sb_discrete and mfsb_penalty_k10 beat it 0/3.**
* n = 10k: mfsb, dwave_sa, openjij, mq_bsb, mq_bsb_mf, mq_dsb_mf and mq_cac beat it 3/3. cim beats it 0/1, and **sb_ballistic and sb_discrete 0/3** (repaired peaks 0.945 and 0.952, against 0.918 for repair_only).
* n = 50k: mfsb beats it 3/3 (0.8496 vs 0.8988). dwave_sa, openjij and mq_*_mf manage 1 call to 12 calls in 40 min and beat the median repair_only by 0.006–0.025. sb_ballistic and sb_discrete do not.
* n = 200k: mfsb beats it 3/3 (0.8547 vs 0.9022). mq_*_mf ran 2–3 calls and beat it by only 0.005–0.008.

### How close do they get to LP / MILP?
**No Ising arm reaches LP-round + repair at any size**, and none matches MILP.
* n = 1k, where every solver got about 40 calls: the MILP is optimal (gap < 1e-4) at a peak of 0.9586 in 0.7 s. The best Ising arm is `dwave_sa` at 0.9605, 10.5% of headroom. Then mq_dsb at 0.9611 (11.9%), dwave_tabu at 0.9617 (13.5%), mq_bsb at 0.9632, openjij at 0.9638, mfsb at 0.9671 (19.5%), cim at 0.9723 (≈ repair_only), and the SB package at 0.979–0.983 (58%). LP+repair gives 0.9666 (9.8%). Per seed, dwave_sa beats LP+repair on 2 of 3 seeds (10.5 vs 27.1% and 9.6 vs 9.8%) and loses on the third (13.7 vs 8.5%). It never beats the MILP (1.8–5.2%) or `ls_lp` (2.5–13.8%).
* n = 10k: the MILP incumbent after 60 s is 0.8698, a 0.8% gap to z_LP with HiGHS reporting a 0.05–0.13% MIP gap. LP+repair gives 0.8760 (6.9%). The best Ising arm is `openjij_sa` at 0.8804 (10.0%, about 33 calls at ~18 s each). Next come mq_dsb_mf at 0.8899 (21%), mfsb at 0.8913 (19%), and dwave_tabu at 0.8922 with 1 seed. dwave_sa only reached 0.9053 because it fit 8–9 calls into the cap at 108 s per call. The SB package reached 0.945–0.952, worse than repair_only, with 3 calls at ~350 s per call on the dense Q.
* n = 50k: MILP after 300 s gives 0.8391 with a 0.1–0.2% MIP gap, essentially the same as LP+repair (0.8391, 1.1%). The best Ising arm is `mfsb` at 0.8496 (10.6%). Everything else ended at 34% of headroom or more, because the time cap allowed only 1–12 inner calls.
* n = 200k: the MILP found **no incumbent and not even a root bound in 300 s**, on all 3 seeds. LP+repair takes 1.3 s and gives 0.8455, only 0.2% of headroom above z_LP. mfsb gives 0.8547 (8.3%). `ls_lp` gives 0.8458 (0.5%) and `ls_greedy` 0.8593 (12.5%).
* The true-objective local search (optional item 2) is the fair classical reference; the comparison below uses median gap % of headroom.
  * `ls_greedy`: at 1k it scores 11.2%, on par with the best Ising arms (dwave_sa 10.5%, mq_dsb 11.9%) and ahead of all the others. At 10k it scores 10.7%, and only openjij (10.0%) is better. At 50k and 200k it scores 16.4% and 12.5%, so mfsb is better there (10.6% and 8.3%), but ls_greedy runs 40–60× faster (33–91 s against 1500–2100 s).
  * `ls_lp` scores 3.4%, 13.8%, 2.0% and 0.5% at 1k, 10k, 50k and 200k. It starts from the *unrepaired* LP round-down, so on some seeds it ends above LP+repair (for example 10k seed 0: 14.2% vs 6.9%). Starting it from the repaired LP solution would be the obvious fix; I did not run it.
  * Overall, no Ising arm beats the cheap classical pipeline "LP → round → repair (→ local search)" at n ≥ 10k. At 1k they are comparable.

### Does matrix-free SB scale to 200k?
**Yes.** `mfsb` never forms Q, which as dense float32 would be 160 GB at 200k, and the explicit sparse Q would have about 1.1e9 nonzeros. Measured on this contended machine:

| n | agents × steps | s per inner call (median) | calls | total wall (s) | peak RSS |
|---|---|---|---|---|---|
| 1k | 64×1000 | 0.22 | 37–40 | 9 | 262 MB |
| 10k | 64×1000 | 2.4 | 34–40 | 82 | 341 MB |
| 50k | 64×1000 | 38 | 40 | 1532 | 499 MB |
| 200k | 16×1000 | 45 | 38–40 | 2070 | 512 MB |

At 200k, about 14% of the wall time (≈ 300 s of 2070 s) went outside the inner solver, on μ_max, repairing the bisection candidates, and energy bookkeeping. At 50k and below that share is under 2%. The first implementation (torch.where plus the sparse-CSR D·z) ran about 2× slower per step. Before I replaced it, the O(n) `repair_ref` dominated at 50k and above, taking up to 59 s per repair (section 3). For comparison, the dense SB package at 50k needed **58 GB RSS and 17–73 min for a single call**. mindquantum's CPU backend with the matrix-free J swap also scales in memory (≤ 0.7 GB at 200k), but its numpy loop took 15–28 min per call at 200k, so only 2–3 calls fit in the 40-min cap. I did not tune its parallelism.

### Lagrangian vs. quadratic penalty (n = 1k, mfsb inner, 3 seeds)
With P = k·μ_max/W:
* k = 0.1: repaired peak 0.9637 (17.1% of headroom) with only 10 calls.
* k = 1: 0.9700 (24.2%), raw use 0.65.
* k = 10: 0.9769 (35.4%), raw use 0.31, and worse than repair_only (0/3 seeds).
* Lagrangian with bisection: 0.9671 (19.5%) with 37–40 calls.

A small, well-chosen penalty was slightly better *and* 4× cheaper than the bisected Lagrangian here. A large penalty over-shrinks the selection, as expected, because it adds a dense rank-1 term s sᵀ that dominates D·diag(α)·Dᵀ. The result depends on the scale, and the sample is small (3 seeds, one inner solver).

### Other observations
* The MindQuantum matrix-free swap is exact. BSB and DSB matrix-free give bit-identical solutions to explicit-J, 1.7× faster at 1k. At 10k, under the same 900 s cap, it fit 2–4× more calls, which improved DSB from 40% to 21% of headroom.
* MQ CAC's default step overflowed (NaN) at 10k on a test QUBO. I map NaN spins to "not admitted", which makes CAC effectively return x ≈ 0 and repair_only-like results.
* cim-optimizer's extAHC with default hyperparameters always drove every spin to −1 (x = 0) on this problem. The field is uniformly negative (h_i < 0 for all i) because selecting everything is far over budget. With the Frobenius/√n scaling instead it overshot to 1.3–1.9·W. I did not tune it beyond trying 3 scalings and 2 time steps.
* The raw Ising outputs are rarely budget-exact. use_raw ranges from 0 to 9.9·W, and even the best arms land at 0.85–0.98·W. The repair is doing real work in every arm.

## 6. Caveats
* **Synthetic data.** The instance is shaped like the real problem: diurnal peak/mean = 2, 1–3-window episodes, heavy-tailed savings, 6% admission. It does not use Baleen traces, and the ~11% headroom is a property of this generator. That figure depends strongly on C_w ≥ 1.5·S_w, the busy-hour start bias, and the s–savings correlation.
* **CPU only; no GPU.** SB, CAC and CIM are designed for GPUs and FPGAs. The dense SB and cim timings here are CPU matmuls on a machine running up to ~30 threads on 24 hardware threads. Wall times are contended and only indicative. The fixed wall-time caps therefore also penalized the slow-per-call arms (SB package, cim, dwave_sa at ≥ 10k, MQ explicit at 10k, all MQ at ≥ 50k), which got 1–12 calls instead of 40. Those arms are **under-converged, not intrinsically worse**. Only at n = 1k did every arm get the full ~40 calls.
* Only modest, untuned settings were used: one β, one δ, fixed agent and step counts, library defaults for dwave, openjij, cim and MQ. The penalty study covers a single inner solver.
* Seeds: 3 per size, except 1 seed for dense SB, dwave_sa, openjij and all MQ arms at 50k, MQ at 200k, and cim and dwave_tabu at 10k. `sb_discrete` at 50k was restarted after I killed it to avoid running two 58 GB jobs at once, and the rerun used 8 threads and a 900 s cap; its single call took 1038 s.
* Timing consistency: the 1k matrix-free and greedy/LP rows were re-run after the kernel, repair and timing fixes (superseded JSONs are in `results/superseded/`). The earlier 1k/10k explicit-solver rows ran with the slower but output-identical `repair_ref`, so their wall times include somewhat more repair time. The MQ `_mf` rows at 1k were re-run after a fix that stopped them from building sparse Q only to read diag(Q) and Q·1.
* MILP: HiGHS single-threaded, no warm start. At 200k it did not finish the root LP in 300 s, while the plain LP took 1.3 s. The MILP presolve and root at that scale is the bottleneck.
* Peak RSS is `ru_maxrss` of the whole job process, including the instance and the reference LP.

## 7. Optional additions requested mid-task
* (1) MindQuantum QAIA, **done**: BSB, DSB and CAC, explicit sparse J at 1k and 10k, and a matrix-free J swap at 1k, 10k, 50k and 200k. SimCIM and LQA were not run.
* (2) Custom true-objective SA or swap local search with a hard budget, **done**: `ls_greedy` and `ls_lp` at all sizes, 3 seeds each.

## 8. Leak check
Command, run at the end:
`find /home/sxing /tmp -xdev -newer $A/.leak_marker -type f 2>/dev/null | grep -v "^$A/" | grep -vE "/\.claude/|/\.vscode-server/|python-languageserver|tracker3|/\.codex/|^<tmp file>"`

The output is **not empty**. The full list is in `results/leak_check.txt` (72 lines). It contains three kinds of file:
1. `<editor/agent state>`, the Claude Code client's own state file. The grep excludes `/.claude/` but not `.claude.json`.
2. `/home/sxing/project/OS_final_project/changes/1_literature_review/ising_followup/survey.md`, dated 02:06. This audit never wrote or opened it; it is a sibling deliverable in the parent directory, presumably written by another agent.
3. 70 fontconfig caches under `<other conda env>`, all dated 01:54:06. They belong to a different conda env (`retrial`). My `conda create` had finished at 01:53:10 (log mtime), and at 01:54 I was running the pip install of torch inside `audit/env`, which cannot write into `envs/retrial`. I believe they came from another process using that env. I cannot prove it from here.

`<home file>` was last modified on 2026-09-26, so the env was not registered. No pip or conda cache, `<home file>` or `/tmp` files were written by this audit.
