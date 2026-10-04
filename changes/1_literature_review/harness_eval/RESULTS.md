# QUBO/Ising episode selectors inside the real Baleen harness: results

**Verdict.**
- **(a) Offline (OPT mode): satisfied by every candidate**, Ising or classical. At matched write rate, every arm cut the simulated P100 by 5.5–8.0 points below Baleen's peak-blind OPT selection (R0) on both traces. For example, R0 34.52 → R2 27.77 on Region7, and 35.56 → 27.60 on Region6. The Ising arms reached 27.7–28.3 in simulation. The classical arms reached 27.6–28.3, and the best of them was the time-limited MILP polish (R2).
- **(b) Deployed (ML mode): not satisfied by any candidate.** Once the selection is distilled into the unchanged GBMs, every arm lands on Baleen online, within about ±0.6 points:
  - Region7: every arm scores 40.06–40.85; none is below Baleen online's 40.10 ± 0.18.
  - Region6: no arm is below RejectX (42.32). The best arm is R2 at 42.38 ± 0.95 over 5 retrains. It is 0.87 below Baleen online, but its retrain spread is large and it is 0.06 above RejectX.
- The two gains are lost at different stages:
  - **Offline:** about half of the analytic gain disappears in simulation through peak migration. The analytic peak is about 24.1 on Region7, while the simulated peak is about 27.8 at a different window.
  - **Deployed:** almost all of the remaining offline gain is lost in distillation. The retention R = (ML-Baleen − ML-Peak)/(OPT-Baleen − OPT-Peak) is −0.04 on Region7 and +0.11 on Region6 for R2.

Setup: 2026-09-28, 24-thread AMD Ryzen 9 9900X, 123 GB RAM, CPU only. The frozen artifact is Baleen-FAST24 `4e3a920` with BCacheSim `ddeb2d8`, from `0_reproduce/baleen_code`, unmodified (`check_frozen.sh` OK). Both traces are sample 0 of 20230325 (0.1%). Cache 366.475 GB; target write rate 35.599 MB/s ±1%. The metric is `PeakServiceTimeUtil1`, 10-minute windows after day 1.

## 1. What was built (all under `harness_eval/`, "H")

- **The one swappable block** (`src/peakbaleen_policy.py`). `PolicyPeakBaleen(Policy)` follows the template exactly: `rl.init(**rl_init_kwargs); rl.recompute()`; order; `rl.apply_policy(order, scores=<Baleen's own scores>, policy=name)`. It computes Baleen's order with the artifact's own `score_service_time_size_fixed`, then does one of two things:
  - **Mode `baleen`:** emits Baleen's order unchanged (R0 and the skeleton).
  - **Mode `solver`:** dumps the instance to `.npz` and calls the solver CLI in the solver env through `subprocess`. It then emits the selected set in nested order, followed by the remaining episodes in Baleen's order. The complete order is fixed by episode identity at the first sort call, because train.py re-sorts up to 3 times and numpy's argsort breaks score ties by position.
- **Invariants asserted in every run:**
  - Σ_w d(e,w) equals `rl.service_time_saved[e]` for every episode.
  - At each of train.py's sort calls, the label rule `threshold < 35.599` reproduces the selected set exactly (`prefix rule reproduces |S|=… exactly` in every train log).
  - The class never touches episodes, residency lists or globals except through `apply_policy`.
- **Our own entry module** (`src/launch_train.py`) registers the class in `policies.__dict__` and then calls the unmodified `BCacheSim.episodic_analysis.train.main()`. Nothing else is patched. The policy reads its configuration from the env var `HE_POLICY_CONFIG`.
- **d(e,w) and C_w** are computed inside the module from the harness's episodes (filter_=prefetch model = what `service_time_saved__prefetch` assumes), using the artifact's own `episodes.service_time`:
  - **Admitted episode:** its chunk range is fetched at the first access, costing `service_time(1, num_chunks)`, and every later access hits.
  - **Episode not admitted:** every access pays `service_time(1, chunks(a))`.
  - So d(e,w(a₁)) += st(1,c(a₁)) − st(1,N_e), and d(e,w(a_k)) += st(1,c(a_k)) for k ≥ 2, with w(a) = ⌊(a.ts − trace_start)/600⌋.
  - C_w = Σ over GET accesses in w of st(1,c(a)).
  - s_e = `rl.chunks_written`.
  - The budget B is the largest chunk count with `th.upsample(B/8)/th.duration < 35.599`, i.e. the harness's own label rule.
- **Nested prefix.** The simulator's converged OPT cutoff lands at 0.72–0.89·W, so it admits only a prefix of S. Offline selections are therefore solved bottom-up at 11 budgets, f = 0.50, 0.55, …, 1.00 of B, with S_k forced into S_{k+1}. Each increment is emitted in Baleen order, followed by the harness's strict-prefix fill in Baleen order. Deployed labels depend only on the set at W, so deployed solves use f = 1.0 only.
- **Solvers** (`src/solve.py`, `pbcore.py`, `pbsolvers.py`, `pbising.py`, `pbcap.py`; solver env = `ising_followup/audit/env`, read-only). The code was written anew for arbitrary episode spans; the audit's code assumes ≤ 3 windows.
  - Every arm shares the same repair:
    1. Drop episodes by the smallest peak-window saving per byte.
    2. Add episodes that strictly reduce the peak.
    3. Lexicographic tie-break: a Baleen-order fill that never raises the peak.
  - R0: Baleen peak-blind.
  - R1: epigraph LP (HiGHS), then a lexicographic stage that maximises DT saved subject to z ≤ z_LP(1+10⁻⁶), then round down and repair.
  - R2: R1 followed by a HiGHS MILP polish (warm start, 30 s per level offline, 60 s deployed).
  - R3: true-objective SA (numba, hard budget) started from the repaired LP.
  - C1: LP + peak-window LNS. Neighbourhoods are the top-k windows, the LP fractional core, or a 6–24-window block. Three sub-solvers race: HiGHS sub-MILP, restricted true-objective SA, and dwave-samplers SA on the sum-of-squares sub-QUBO. A move is accepted only if the true peak improves.
  - C2: EIM-style constrained Ising on the true objective. It uses log-sum-exp peak + native hinge budget with an ALM multiplier, 24-replica exchange with numba prange, and starts from the repaired LP.
  - C4: sum-of-squares peak QUBO, Σ_w α_w(C_w−τ−(Dᵀx)_w)² + μsᵀx, solved by matrix-free ballistic SB (PyTorch CPU sparse). Window duals (SAIM/ALM-style) reweight α and the price μ, followed by repair.
  - C5: contested subset after LP reduced-cost pegging (≤ 1,500 vars). An explicit sub-QUBO is solved by dwave SA, dwave Tabu (both warm-started from the LP) and MindQuantum bSB/dSB, and compared against a HiGHS MILP on the same subset.
  - RB4: robustness variant. It minimises the mean of the top-4 windows (CVaR LP), then round + repair + top-4 SA.
  - C3L/C3: capacity-coupled (§3.3).

## 2. Environment and exact commands

- `source H/env.sh` sandboxes HOME, the XDG dirs, TMPDIR, the pip/conda/MPL/numba/torch caches, `CONDA_REGISTER_ENVS=false`, `PYTHONNOUSERSITE=1` and `PYTHONDONTWRITEBYTECODE=1`, all inside H.
- Every Baleen process runs as `bwrap --dev-bind / / --bind H/work/systmp /tmp -- …` with cwd `H/work`. There, `BCacheSim -> ../../../0_reproduce/baleen_code/BCacheSim` and `data -> ../../../0_reproduce/work/data` are relative symlinks, verified to resolve.
- All `train` invocations with GBMs are serialized by a flock on `H/work/.train.lock`.
- Simulations run with `OMP_NUM_THREADS=2`, at most 20 concurrently (later a flock slot pool, `H/work/.sim_slots`).
- `OMP_WAIT_POLICY=PASSIVE` is set for all processes. LightGBM's hard-coded 20 threads otherwise stalled for more than 20 minutes while simulations shared the CPU. This changes only OpenMP's idle-wait behaviour, not the model or its parameters.
- Environments:
  - Baleen: `0_reproduce/env`, used read-only (python 3.11, lightgbm 3.3.5).
  - Solvers: `ising_followup/audit/env`, used read-only (highspy 1.15.1, numba 0.67.0, dimod 0.12.22, dwave-samplers 1.8.0, torch 2.14.0+cpu, mindquantum 0.12.0).

Offline (OPT) mode, per arm (`src/offline.py`). The train arguments are the authors' OPT-AP ones for "OPT-Range on OPT-Ep-Start", with the OPT's own converged EA. No GBMs are trained, and the split end is 10⁹ s, so the decisions cover the whole trace:
```
bwrap … $BALEEN_PY -B -m launch_train --exp o11_Region7_C2 --policy PolicyPeakBaleen --region Region7 --sample-ratio 0.1 \
  --sample-start 0.0 --trace-group 20230325 --supplied-ea physical --target-wrs 34 50 100 75 20 10 60 90 30 \
  --target-csizes 366.47461 --output-base-dir runs/off/o11_Region7_C2/train --eviction-age 4442.942 \
  --rl-init-kwargs filter_=prefetch --train-split-secs-start 0 --train-split-secs-end 1000000000
bwrap … $BALEEN_PY -B -m BCacheSim.cachesim.simulate_ap --trace data/tectonic/20230325/Region7/full_0_0.1.trace \
  --offline-ap --ap opt --ap-threshold <converged> --size_gb 366.475 -o runs/off/<exp>/converge/th_<t> \
  --prefetch-when at_start --prefetch-range acctime-episode --batch-size 16 --log-interval 600 \
  --ep-analysis <train analysis csv> --offline-ap-decisions tmp/<exp>/…/decisions_pb_<arm>_ea_4442.94.pkl.bz \
  --job-id <exp>__th_<t> --eviction-policy LRU
```
- The Region6 EA is 3848.741 s.
- The `--ap-threshold` (a cumulative write-rate cutoff in MB/s) is converged to 35.599 ±1% with converge.py's rules: bracket, secant, 3-point grid.

Deployed (ML) mode, per arm and retrain (`src/deployed.py`):
- **Train:** the authors' Fig 9 Baleen `TrainCommand` (from `0_reproduce/work/jobs/fig9.jsonl`) with `--policy PolicyPeakBaleen`, `--exp dep_<trace>_<arm>_rep<k>`, and EA 5653.153 / 4669.873. That is `--train-models admit prefetch --train-split-secs-end 86400`: the day-1 selection is solved on the day-1 instance only.
- **Simulate:** the authors' `ReproduceCommand` for that trace:
  - Region7: ML-Range on ML-When, `--prefetch-when predict --prefetch-range acctime-episode-predict --prefetch-when-threshold 0.5`.
  - Region6: All on Partial Hit, `--prefetch-when partial --prefetch-range acctime-all`.
  - `--ap mlnew`, with our models, plus `--eviction-policy LRU`, without `--offline-ap-decisions`.
- `--ap-threshold` is converged to 35.599 ±1%. Peak-aware labels shift the GBM's probabilities: the write rate at Baleen's 0.62 / 0.79 was only 9–16 MB/s. When the target is not yet bracketed, the loop therefore extrapolates with a secant step instead of converge.py's fixed ±0.02 steps. It is otherwise the same loop.

## 3. P0 / P1: harness fidelity

**Skeleton = Baleen, exactly** (`results/p0_skeleton_verify.csv`, Region7 day 1, EA 5653.153):
- Four runs, all through our launcher: stock `PolicyUtilityServiceTimeSize2` twice, the skeleton, and the solver plumbing with an identity candidate.
- All four give identical scores and identical labels on all 12,320 episodes (2,361 positives, 0 label differences).
- Thresholds differ only inside score-tie groups. Each of the 1,445 groups' threshold range is identical. Two stock runs differ in exactly this way, because of `imap_unordered` plus the unstable argsort.

**Deployed pipeline control:**
- Baleen through our skeleton (R0 deployed) gives 40.05 (Region7) and 43.34 (Region6) at matched write rate.
- The 0_reproduce references are 40.10 ± 0.18 and 43.25 ± 0.04.

**Offline pipeline sanity** (R0 = Baleen's peak-blind selection through `--ap opt`):
- Region7: 34.52 at WR 35.55; the authors' OPT AP is 34.48 at 34.68.
- Region6: 35.56 at 35.68; the authors' is 36.81 at 34.76. At the authors' own cutoff (27.4728) our WR is 34.70, and theirs is 34.76.
- The authors' rows are `tracedrop` runs made with the older DT metric. 0_reproduce/RESULTS.md measured 0.5–1.9-point peak offsets from that metric version.

**Gate 0, analytic L_w vs simulated per-window DT** (`results/gate0_all.csv`). Windows are those after day 1. The admitted set is exactly the episodes with threshold ≤ the converged cutoff.
- C_w equals the simulator's per-window no-cache DT to within 6·10⁻¹¹ (all 997 windows, both traces). This validates d(e,w)'s accounting.
- Baleen's own selection is modelled very well:
  - r = 0.994 (Region7) and 0.985 (Region6).
  - The argmax window is the same.
  - The top-10 overlap is 9/10.
  - The analytic peak is 1.6 points (Region7) and 0.9 points (Region6) below the simulated one.
- **The peak-aware selections show peak migration.** For R1 (LP), r is 0.986 on Region7 and 0.972 on Region6 (R1_L6: 0.987 / 0.947), but the analytic peak window is not where the simulator peaks:
  - Region7: analytic argmax 288 → simulated 660, Baleen's own peak window.
  - Region6: 361 → 154.
  - The simulated peak exceeds the analytic peak by 3.3–4.6 points.
  - The top-10 windows overlap in only 0–3.
  - The residual (sim − analytic) concentrates in the heavily shaved, high no-cache windows: Region7 646/647/660/662 and Region6 152/154/807/816.
- **Mechanism evidence** (`src/occupancy.py`):
  - Under the harness's eviction-age model, the analytic cache occupancy of Baleen's own admitted set exceeds the 3,002-chunk cache in about 40% of windows. The maximum is 1.5× on Region7 and 2.0× on Region6.
  - Occupancy correlates with the residual: r = 0.64 (Region7) and 0.78 (Region6).
  - Admission concentrated into busy periods shortens the real eviction age exactly where the plan counted on hits.

### 3.1 Offline (OPT) results (`results/offline.csv`; P100 etc. = simulated, util %)

- "analytic peak @W" is the solver's peak for the full set S at W.
- "analytic peak @cutoff" is the analytic peak of the set the simulator actually admitted.
- The dP100-vs-online column is for orientation only: OPT mode is an upper bound, not deployable.
- R1_L6 is an earlier R1 run with 6 levels (0.75–1.0). R1_rep2 and R1_rep3 are re-runs of R1 in new processes, with different episode order and tie breaks. They reproduce R1's simulated P100 to the 3rd decimal, so offline differences of about 0.1 point or more are real for this trace, not noise.


**Region7** (R0 = Baleen peak-blind OPT: P100 34.52; Baleen online 40.10 +- 0.18)

| arm | analytic peak @W (%) | gap to z_LP @W | solve (s) | analytic peak @cutoff | R^2 (an. vs sim) | sim P100 | P99 | top-5 mean | mean DT | WR (MB/s) | cutoff (MB/s) | sim argmax | analytic argmax @cutoff | top-5 Jaccard vs R0 | dP100 vs R0 | dP100 vs online |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R0 | 31.36 |  |  | 32.88 | 0.989 | **34.52** | 29.37 | 32.21 | 19.76 | 35.55 | 30.378 | 660 | 660 | 1.00 | +0.00 | -5.58 |
| R1_L6 | 24.39 | 1.2% (z_LP 24.09) | 7 | 24.66 | 0.973 | **27.96** | 26.10 | 27.19 | 19.86 | 35.54 | 30.547 | 660 | 189 | 0.25 | -6.56 | -12.14 |
| R1 | 24.20 | 0.5% (z_LP 24.09) | 11 | 24.44 | 0.971 | **28.10** | 26.05 | 27.08 | 19.95 | 35.48 | 30.035 | 660 | 288 | 0.25 | -6.42 | -12.00 |
| R2 | 24.09 | 0.0% (z_LP 24.09) | 104 | 24.22 | 0.969 | **27.77** | 25.93 | 27.12 | 19.98 | 35.59 | 30.076 | 660 | 155 | 0.25 | -6.76 | -12.33 |
| R3 | 24.09 | 0.0% (z_LP 24.09) | 194 | 24.09 | 0.960 | **28.31** | 26.07 | 27.40 | 20.23 | 35.66 | 30.074 | 660 | 647 | 0.25 | -6.21 | -11.79 |
| C2 | 24.09 | 0.0% (z_LP 24.09) | 221 | 24.09 | 0.964 | **28.34** | 26.16 | 27.61 | 20.20 | 35.61 | 29.654 | 660 | 647 | 0.25 | -6.18 | -11.76 |
| C1 | 24.09 | 0.0% (z_LP 24.09) | 223 | 24.17 | 0.968 | **28.22** | 26.18 | 27.33 | 20.01 | 35.59 | 29.904 | 660 | 624 | 0.25 | -6.31 | -11.88 |
| C3L_k1.5 | 26.68 | 10.8% (z_LP 24.09) | 11 | 26.68 | 0.990 | **28.89** | 26.96 | 27.94 | 19.85 | 35.45 | 31.000 | 660 | 661 | 0.25 | -5.63 | -11.21 |
| RB4 | 24.14 | 0.2% (z_LP 24.09) | 128 | 24.14 | 0.922 | **27.74** | 25.70 | 27.00 | 20.99 | 35.30 | 29.000 | 660 | 647 | 0.25 | -6.78 | -12.36 |
| C4 | 24.21 | 0.5% (z_LP 24.09) | 185 | 24.21 | 0.964 | **27.97** | 26.11 | 27.32 | 20.24 | 35.55 | 29.000 | 647 | 647 | 0.25 | -6.55 | -12.13 |
| C3_k1.5 | 26.50 | 10.0% (z_LP 24.09) | 221 | 26.50 | 0.990 | **29.00** | 26.93 | 27.88 | 19.95 | 35.43 | 31.832 | 660 | 661 | 0.25 | -5.52 | -11.10 |
| C5 | 24.14 | 0.2% (z_LP 24.09) | 444 | 24.15 | 0.967 | **28.20** | 26.01 | 27.22 | 20.27 | 35.64 | 28.740 | 660 | 613 | 0.25 | -6.32 | -11.90 |
| R1_rep3 | 24.20 | 0.5% (z_LP 24.09) | 11 |  |  | **28.10** | 26.05 | 27.04 | 19.95 | 35.56 | 30.050 | 660 |  | 0.25 | -6.42 | -12.00 |
| R1_rep2 | 24.20 | 0.5% (z_LP 24.09) | 12 |  |  | **28.10** | 26.05 | 27.08 | 19.95 | 35.54 | 30.036 | 660 |  | 0.25 | -6.42 | -12.00 |

**Region6** (R0 = Baleen peak-blind OPT: P100 35.56; Baleen online 43.25 +- 0.04)

| arm | analytic peak @W (%) | gap to z_LP @W | solve (s) | analytic peak @cutoff | R^2 (an. vs sim) | sim P100 | P99 | top-5 mean | mean DT | WR (MB/s) | cutoff (MB/s) | sim argmax | analytic argmax @cutoff | top-5 Jaccard vs R0 | dP100 vs R0 | dP100 vs online |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| R0 | 31.80 |  |  | 34.67 | 0.971 | **35.56** | 29.44 | 32.79 | 19.29 | 35.68 | 27.790 | 816 | 816 | 1.00 | +0.00 | -7.69 |
| R1_L6 | 22.09 | 5.8% (z_LP 20.88) | 3 | 22.92 | 0.896 | **27.53** | 26.60 | 27.32 | 20.22 | 35.47 | 26.460 | 154 | 371 | 0.11 | -8.02 | -15.72 |
| R1 | 22.58 | 8.1% (z_LP 20.88) | 6 | 23.50 | 0.946 | **27.77** | 26.34 | 27.50 | 19.84 | 35.61 | 27.191 | 154 | 361 | 0.11 | -7.78 | -15.48 |
| C1 | 22.17 | 6.1% (z_LP 20.88) | 224 | 23.04 | 0.932 | **27.92** | 26.49 | 27.63 | 19.93 | 35.37 | 26.800 | 807 | 567 | 0.11 | -7.64 | -15.33 |
| R3 | 21.74 | 4.1% (z_LP 20.88) | 185 | 23.04 | 0.905 | **27.60** | 26.27 | 27.47 | 20.53 | 35.51 | 26.144 | 154 | 817 | 0.11 | -7.95 | -15.65 |
| R2 | 21.31 | 2.0% (z_LP 20.88) | 342 | 22.71 | 0.882 | **27.60** | 25.97 | 27.42 | 20.37 | 35.67 | 26.027 | 816 | 829 | 0.25 | -7.96 | -15.65 |
| C2 | 21.90 | 4.9% (z_LP 20.88) | 221 | 23.08 | 0.897 | **28.18** | 26.44 | 27.83 | 20.59 | 35.47 | 25.520 | 816 | 268 | 0.25 | -7.38 | -15.07 |
| RB4 | 21.72 | 4.0% (z_LP 20.88) | 123 | 23.09 | 0.904 | **27.88** | 26.58 | 27.68 | 20.54 | 35.27 | 25.800 | 154 | 520 | 0.11 | -7.67 | -15.37 |
| C3L_k1.5 | 26.37 | 26.3% (z_LP 20.88) | 11 | 26.37 | 0.979 | **29.58** | 27.08 | 28.03 | 19.43 | 35.36 | 28.796 | 539 | 805 | 0.11 | -5.98 | -13.67 |
| C4 | 21.86 | 4.7% (z_LP 20.88) | 230 | 23.26 | 0.915 | **27.87** | 26.72 | 27.63 | 20.56 | 35.55 | 25.451 | 807 | 771 | 0.25 | -7.69 | -15.38 |
| C3_k1.5 | 26.13 | 25.2% (z_LP 20.88) | 221 | 26.13 | 0.978 | **29.28** | 27.17 | 28.15 | 19.46 | 35.56 | 28.905 | 539 | 817 | 0.11 | -6.27 | -13.97 |
| C5 | 22.24 | 6.5% (z_LP 20.88) | 231 | 23.26 | 0.942 | **27.69** | 26.08 | 27.39 | 19.99 | 35.65 | 26.695 | 154 | 176 | 0.25 | -7.87 | -15.56 |
| R1_rep3 | 22.54 | 7.9% (z_LP 20.88) | 7 |  |  | **27.77** | 26.34 | 27.50 | 19.83 | 35.60 | 27.217 | 154 |  | 0.11 | -7.78 | -15.48 |
| R1_rep2 | 22.58 | 8.1% (z_LP 20.88) | 7 |  |  | **27.77** | 26.34 | 27.50 | 19.84 | 35.63 | 27.207 | 154 |  | 0.11 | -7.78 | -15.48 |

**H2: Ising vs classical at equal footing** (`results/analytic_levels.csv`, analytic peak averaged over the 11 nested levels, util %):

| Region | R1 LP+repair | R2 MILP polish | R3 true-obj SA | C1 LNS | C2 EIM | C4 mf-SB SoS | C5 contested QUBO | RB4 |
|---|---|---|---|---|---|---|---|---|
| Region7 | 24.570 | 24.220 | 24.243 | 24.297 | **24.165** | 24.343 | 24.376 | 24.281 |
| Region6 | 23.467 | **22.611** | 22.898 | 23.146 | 22.917 | 23.044 | 23.373 | 22.882 |

- **C2 (EIM, hinge + ALM + replica exchange)** is the only Ising arm that beat the MILP polish analytically, and only on Region7 (24.165 vs 24.220). On Region6, R2 is best.
- **C1:** accepted LNS moves were won by the HiGHS sub-MILP 243 times, by true-objective SA 118 times, and by the sum-of-squares sub-QUBO SA twice.
- **C5**, per-solver analytic peak on the contested subset (mean over levels):

  | Solver | Region6 | Region7 |
  |---|---|---|
  | HiGHS sub-MILP | 23.33 | 24.33 |
  | MindQuantum bSB | 23.37 | 24.38 |
  | LP warm start | 23.40 | 24.38 |
  | MindQuantum dSB | 23.41 | 24.48 |
  | dwave SA / Tabu | 23.66 | 24.86 |

  The explicit QUBO heuristics do not beat the sub-MILP on the same subset.
- In simulation, the analytic ordering hardly carries over. All LP-family and Ising arms fall within 27.6–28.3 on both traces, because the migration residual (+3–5 points) dominates.

### 3.2 Candidates with the lowest simulated P100 offline

| Region | Arm | Simulated P100 |
|---|---|---|
| Region7 | RB4 | 27.74 |
| Region7 | R2 | 27.77 |
| Region7 | R1_L6 | 27.96 |
| Region7 | C4 | 27.97 |
| Region6 | R1_L6 | 27.53 |
| Region6 | R2 | 27.60 |
| Region6 | R3 | 27.60 |
| Region6 | C5 | 27.69 |

- The best Ising arms are C4 (27.97 / 27.87) and C5 (28.20 / 27.69).
- These, plus C2 (the most faithful Ising transfer), were taken to deployed mode.

### 3.3 Capacity-coupled C3 (candidate 3)

- **Model:**
  - Each admitted episode keeps its whole chunk range resident from its first access to its last access + EA.
  - occ_w ≤ κ·Cap, with Cap = 366.475 GB × 0.1% = 3,002 chunks.
  - C3L imposes this as LP rows.
  - C3 imposes it as a native occupancy hinge in the EIM energy, seeded by C3L.
- **Fidelity improved:** R² rose to 0.990 on Region7 (0.96–0.97 for LP) and to 0.979 on Region6 (0.88–0.95). The residual sd fell from 0.58–0.67 to 0.36 points on Region7, and from 0.80–0.98 to 0.55 on Region6.
- **The peak got worse:** at κ = 1.5, the analytic peak rose to 26.1–26.7, and the simulated P100 to 28.9–29.6. That is worse than the plain LP arms but still far below R0.
- **Analytic κ sensitivity** (Region7, level 0.85):

  | κ | Analytic peak |
  |---|---|
  | 1.0 | 29.46 |
  | 1.25 | 27.87 |
  | 1.5 | 26.68 |
  | 2.0 | 24.85 |

  We did not tune κ against the simulator. That would be simulator-in-the-loop selection; see §6.

## 4. P3: deployed (ML) results (`results/deployed.csv`)

- References: Baleen online R7 40.10 ± 0.18, R6 43.25 ± 0.04 (9 retrains); RejectX 42.455 / 42.321; CoinFlip 48.961 / 43.445.
- All rows are at matched WR (±1%).

| trace | arm | reps | P100 mean +- sd | per-rep P100 | P99 mean | top-5 mean | mean DT | WR range | vs Baleen online | vs RejectX | vs CoinFlip |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Region7 | R0 | 1 | **40.05 +- 0.00** | 40.05 | 34.39 | 37.45 | 21.58 | 35.66-35.66 | -0.05 | -2.41 | -8.92 |
| Region6 | R0 | 1 | **43.34 +- 0.00** | 43.34 | 34.67 | 39.35 | 21.97 | 35.69-35.69 | +0.09 | +1.02 | -0.11 |
| Region6 | R2 | 5 | **42.38 +- 0.95** | 41.34, 43.12, 41.35, 42.95, 43.14 | 34.62 | 39.01 | 22.05 | 35.40-35.77 | -0.87 | +0.06 | -1.07 |
| Region6 | RB4 | 3 | **42.97 +- 0.25** | 43.26, 42.80, 42.86 | 34.81 | 39.18 | 22.03 | 35.50-35.66 | -0.28 | +0.65 | -0.47 |
| Region7 | C4 | 3 | **40.07 +- 0.03** | 40.06, 40.10, 40.04 | 34.47 | 37.78 | 21.86 | 35.34-35.73 | -0.03 | -2.39 | -8.90 |
| Region7 | C2 | 3 | **40.85 +- 0.34** | 40.48, 40.90, 41.16 | 34.79 | 38.28 | 22.08 | 35.32-35.63 | +0.75 | -1.60 | -8.11 |
| Region6 | C4 | 3 | **43.20 +- 0.10** | 43.26, 43.26, 43.08 | 34.67 | 39.46 | 22.07 | 35.55-35.71 | -0.05 | +0.88 | -0.24 |
| Region6 | C5 | 3 | **43.19 +- 0.31** | 43.19, 43.50, 42.89 | 35.00 | 39.08 | 22.05 | 35.32-35.69 | -0.06 | +0.87 | -0.25 |
| Region6 | C2 | 3 | **43.09 +- 0.16** | 43.12, 43.23, 42.92 | 34.65 | 39.15 | 22.04 | 35.52-35.87 | -0.16 | +0.77 | -0.35 |
| Region7 | RB4 | 3 | **40.19 +- 0.40** | 40.62, 40.13, 39.82 | 34.73 | 37.97 | 21.87 | 35.52-35.72 | +0.09 | -2.27 | -8.77 |
| Region7 | R2 | 5 | **40.35 +- 0.14** | 40.36, 40.36, 40.56, 40.19, 40.26 | 34.82 | 37.84 | 21.98 | 35.45-35.81 | +0.25 | -2.11 | -8.62 |
| Region7 | C5 | 3 | **40.06 +- 0.07** | 40.11, 40.08, 39.98 | 34.28 | 37.79 | 21.88 | 34.90-35.80 | -0.04 | -2.40 | -8.90 |

Criterion (b) needs the mean below Baleen online by more than 2 sd, and below RejectX and CoinFlip, on both traces:

| Region | Arm(s) | Result against (b) |
|---|---|---|
| Region7 | All | Every mean lies between 40.06 and 40.85. None is below 40.10 − 2 × 0.18 = 39.74. C4 and C5 tie Baleen at 40.06–40.07. |
| Region6 | R2 (5 retrains) | 42.38 ± 0.95. This is 0.87 below Baleen online and beyond 2 × SE of the difference (0.85), but it is not below RejectX (42.32). |
| Region6 | Other arms | 42.97–43.20: within about 0.3 of Baleen online and above RejectX. |

Result: **no candidate satisfies (b).**

- Retention of the offline gain for R2 is R = −0.04 (Region7) and +0.11 (Region6). For the best Ising arm, C4, it is +0.01 and +0.01.
- Day-1 labels are very different from Baleen's:
  - Jaccard 0.47–0.56 with Baleen's positives.
  - 22–38% fewer positive episodes.
  - Analytic day-1 peak 20.1–22.4 vs Baleen 25.6–28.9.
  - 9–14% less total DT saved on day 1.
- The GBM (features: metadata + access counts over the last 1–6 h; no time-of-day or load signal) cannot express why an episode was chosen: it lies in a peak window. What it learns is a weaker, noisier admission score. The simulator then needs a much lower probability cutoff (0.40–0.54 vs Baleen's 0.62–0.79) to reach the same write rate.
- The resulting peak is statistically indistinguishable from Baleen on Region7. On Region6 it is at best noisily lower: R2's 5 retrains range from 41.34 to 43.14. Mean DT rises slightly: +0.3–0.5 points on Region7 and +0.05–0.1 on Region6.

## 5. Why the offline gain does not reach deployment

1. **Analytic → simulated (OPT).**
   - The min-max LP flattens hundreds of windows to about the same analytic level. Region7 has an irreducible floor window at 24.09: z_LP, which C2 and R2 reach.
   - The simulator's hits are lost where admissions concentrate, because the cache holds 3,002 chunks and the eviction age shortens. The windows that were shaved hardest therefore come back 3–5 points higher.
   - The simulated peak migrates back to Baleen's own peak windows (Region7 660, Region6 816/154).
   - Offline still keeps about 6.5–8 points over R0. That part is real and deterministic (reruns are identical).
2. **OPT → ML (distillation).**
   - With the frozen features, the label structure that creates the offline peak gain (when an episode occurs) is not learnable.
   - About 90–100% of the offline gain is lost, as SCOPE §4 anticipated for H3.

## 6. Items that need a team decision (not implemented)

- **Peak-aware tail ordering beyond the W prefix.** The simulator's converged cutoff lands at 0.72–0.89·W, so this is not needed on the admit side; nested levels handle it. A solve above W·(1+δ) would violate SCOPE §1.
- **Simulator-in-the-loop reweighting of training.** This covers re-solving after up-weighting the simulator's worst windows. It includes calibrating the C3 κ, or a per-window savings haircut, against simulated residuals. Gate 0 shows it targets the right mechanism, and it is the most direct fix for migration.
- **Per-episode prefetch options** (candidate 7): the slot emits only an order and scores.
- **Candidate 3's occupancy model** was implemented purely in-module (it changes no eviction-age handling). The team should still confirm that reading, as the literature report asked.
- Samples 1–9 were not run.

## 7. Integrity

- `bash 0_reproduce/check_frozen.sh`: **`frozen OK (94 files)`**. It was also run before the runs.
- Nothing under `0_reproduce/` or `ising_followup/` is newer than `H/.leak_marker`: `find … -newer` returned empty. This covers `0_reproduce/work/data`, used through a symlink, and both environments. Nothing was written to <tmp file> or /dev/shm either.
- The leak check was the prescribed command: `find /home/sxing /tmp -xdev -newer H/.leak_marker -type f | grep -v "^H/" | grep -vE "/\.claude/|\.claude\.json|/\.vscode-server/|python-languageserver|tracker3|/\.codex/|^<tmp file>"`. It listed 18 files, none written by this work:
  - `<home file>` (11:34) and `<home file>` (11:36): a wget and a conda invocation outside this work. This work never runs wget or conda, and every harness/solver process has HOME=H/.home.
  - `<editor/agent state>,logs/*}` and `<home cache>`: the VS Code Copilot SDK, running since 10:21.
  - `<home desktop/config>`: the desktop audio daemon.
  - `<home file>` (13:52): an interactive shell.
  - `<tmp file>` and `<home cache>`: agent/IDE tooling.
- Every Baleen process ran under bwrap with /tmp bound to H/work/systmp.

## 8. Where things are

| Path under H | Contents |
|---|---|
| `src/` | All code: policy, launcher, solvers, offline/deployed drivers, gate0, tables |
| `results/offline.csv` | Offline arms |
| `results/deployed.csv` | Deployed retrains |
| `results/gate0_all.csv` (+ `gate0_series_*.npz`) | Gate 0 |
| `results/analytic_levels.csv` | Per-level analytic results |
| `results/converge/*.csv` | Every threshold tried |
| `results/p0_skeleton_verify.csv` | Skeleton verification |
| `results/tables.md` | Rendered tables |
| `work/logs/{p0,off,o11,dep}/<exp>/` | train.log and converge/*.log (full commands on the first line) |
| `work/inst/*.npz` | Instances and solutions |
| `work/cfg/*.json` | Policy configs |
| `PROGRESS.md` | Phase log |
