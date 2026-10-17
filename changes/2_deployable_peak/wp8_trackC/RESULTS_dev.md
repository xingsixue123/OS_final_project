# Track C (wp8) Stage 2: dev full-simulation screen of deployment-aware Ising labels

**Dev only:** Region7/Region6 × samples 0, 0.1, 0.2, 0.3. Run 2026-10-16, approved by the coordinator; PLAN_C.md
§2–§3 (commit 19d7992) was applied unchanged. No Region5 run; no wp3_test output was read.

## 0. Verdict
- **Screen gate: no configuration passes.** S1 = mean_i min(X1_i − Y_i, A+α_i − Y_i), each side rep 1, must be > 0.
  - S1 values: E8:STU10R1 −0.26, E8:ANC3 −0.84, E8:ANC10 −1.80. The comparison arm E8:ANC10CP gets −0.94.
  - So, per the rule, no confirmation retrains were run and **there is no Track C finalist**.
  - Track C reports a **negative dev result**. Stage 3 adds no Track C arm. PLAN_C §6 says the Region5 test runs anyway, with A, B, A+α, B+α and X1.
- **Near miss, reported but not acted on.**
  - E8:STU10R1 has the lowest rep-1 dev mean of any configuration: 36.78, against X1 rep 1 37.07 and A+α rep 1 37.86.
  - Against the 3-retrain means of X1/A+α it scores +0.04 with 6/8 wins on each.
  - The pre-registered rep-1 vs rep-1 gate (S1 = −0.26) rejects it. This is a single retrain, inside the retrain noise of X1 (instance sd up to 2.6).
- **Mechanism: C-anchor does what it was designed to do on Region7, but loses Region6.**
  - E8:ANC3 restores first-access admission on Region7 (0.121 vs X1 0.028; A+α 0.084).
  - Its Region7 mean is the best of all configurations: 36.46 vs A+α 37.11 vs X1 37.67.
  - But keeping Baleen's labels also keeps Baleen's Region6 failure. Peaks stay on big-offset scans (scan peak 2/4; X1 2/12), and the Region6 mean is 38.27 vs X1 36.73.
  - The Stage-1 proxy (not valid as a ranker) had predicted exactly this region trade-off.
- **Ising vs classical, anchored energy, 1 retrain:** CP-SAT labels (ANC10CP) deployed better than PT labels (ANC10): 37.46 vs 38.32. This is a single retrain; no claim.

## 1. Setup
- **Configurations.** Each uses Track C labels (PT, 10 s, seed = retrain), `meta+block+chunk+load`, and the load-adaptive threshold α = −1 (E8).
  - The same retrain is also simulated with α = none (D8), as a sim-only variant.
  - ANC10CP is the same anchored energy solved by CP-SAT. It is a comparison arm only.
- **Pipeline.** Driver `src/wp8.py`, a copy of WP2's `wp2.py`; the theta search is (0, 4] for α arms.
  - Labels are applied in-run by `PolicyPeakBaleen4`. The train logs confirm the in-run core equals the offline set (e.g. ANC3 R7 s0: 2376).
  - Matched WR is 35.599 ± 1%. All 64 evaluations matched; 0 failed; 2.83 sims per evaluation on average.
- **References.** WP2's dev trials, not re-run: X1 = Ea-1.0:F1PT; A+α = Aa-1.0 ∪ Ax-1.0; also A, B, B+α, D:F1PT.

## 2. Screen (rep 1; P100 util %)
| config | Region7_s0 | Region7_s0.1 | Region7_s0.2 | Region7_s0.3 | Region6_s0 | Region6_s0.1 | Region6_s0.2 | Region6_s0.3 | mean | S1 | d_i>0 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| X1 (r1) | 39.91 | 36.33 | 37.19 | 39.25 | 39.20 | 34.60 | 34.16 | 35.91 | 37.07 | | |
| A+α (r1) | 39.57 | 35.48 | 36.89 | 36.34 | 42.92 | 38.99 | 36.36 | 36.30 | 37.86 | | |
| D8:ANC10 | 39.30 | 37.46 | 36.77 | 42.59 | 43.11 | 40.26 | 35.77 | 37.28 | 39.07 | -2.548 | 2/8 |
| D8:ANC10CP | 40.06 | 35.25 | 37.02 | 35.40 | 43.10 | 43.39 | 36.53 | 37.41 | 38.52 | -2.001 | 2/8 |
| D8:ANC3 | 39.38 | 34.95 | 36.89 | 35.75 | 42.88 | 41.83 | 35.68 | 36.34 | 37.96 | -1.443 | 4/8 |
| D8:STU10R1 | 40.10 | 34.80 | 37.20 | 35.97 | 39.30 | 38.53 | 37.22 | 35.87 | 37.37 | -0.854 | 3/8 |
| E8:ANC10 | 39.28 | 34.75 | 36.88 | 39.72 | 42.12 | 43.18 | 33.96 | 36.67 | 38.32 | -1.801 | 4/8 |
| E8:ANC10CP | 39.71 | 34.07 | 36.98 | 35.44 | 40.04 | 42.98 | 33.78 | 36.66 | 37.46 | -0.937 | 3/8 |
| E8:ANC3 | 39.40 | 34.20 | 36.68 | 35.57 | 40.09 | 40.10 | 36.27 | 36.61 | 37.36 | -0.843 | 4/8 |
| E8:STU10R1 | 39.70 | 34.44 | 37.20 | 35.53 | 38.48 | 36.66 | 36.29 | 35.92 | 36.78 | -0.257 | 3/8 |

## 3. All matched retrains (finalist-rule view; Track C configs have 1 retrain because none passed the gate)
| config | n | Region7_s0 | Region7_s0.1 | Region7_s0.2 | Region7_s0.3 | Region6_s0 | Region6_s0.1 | Region6_s0.2 | Region6_s0.3 | mean | S | wins vs X1 | wins vs A+α | R7 − A+α | R6 − A+α |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | 3-3 | 40.00 | 36.81 | 36.73 | 37.22 | 43.33 | 40.86 | 36.23 | 36.83 | 38.50 | -1.683 | 2/8 | 2/8 | +0.58 | +0.67 |
| B | 3-3 | 39.50 | 36.51 | 37.08 | 38.60 | 42.79 | 40.36 | 36.23 | 36.47 | 38.44 | -1.625 | 2/8 | 3/8 | +0.82 | +0.32 |
| A+a | 3-3 | 39.65 | 35.89 | 36.87 | 36.01 | 42.90 | 38.96 | 36.30 | 36.43 | 37.88 | -1.059 | 3/8 | 0/8 | +0.00 | +0.00 |
| B+a | 3-3 | 39.61 | 35.19 | 37.11 | 37.61 | 42.69 | 42.73 | 36.07 | 36.41 | 38.43 | -1.609 | 3/8 | 5/8 | +0.27 | +0.83 |
| D:F1PT | 3-3 | 40.25 | 36.01 | 37.42 | 39.33 | 41.88 | 39.05 | 35.95 | 37.05 | 38.37 | -1.551 | 0/8 | 2/8 | +1.15 | -0.17 |
| X1 | 3-3 | 39.90 | 35.10 | 37.42 | 38.26 | 39.29 | 37.56 | 34.23 | 35.83 | 37.20 | -0.382 | 0/8 | 5/8 | +0.56 | -1.92 |
| D8:ANC10 | 1-1 | 39.30 | 37.46 | 36.77 | 42.59 | 43.11 | 40.26 | 35.77 | 37.28 | 39.07 | -2.250 | 2/8 | 3/8 | +1.92 | +0.46 |
| D8:ANC10CP | 1-1 | 40.06 | 35.25 | 37.02 | 35.40 | 43.10 | 43.39 | 36.53 | 37.41 | 38.52 | -1.703 | 2/8 | 2/8 | -0.17 | +1.46 |
| D8:ANC3 | 1-1 | 39.38 | 34.95 | 36.89 | 35.75 | 42.88 | 41.83 | 35.68 | 36.34 | 37.96 | -1.145 | 4/8 | 6/8 | -0.36 | +0.54 |
| D8:STU10R1 | 1-1 | 40.10 | 34.80 | 37.20 | 35.97 | 39.30 | 38.53 | 37.22 | 35.87 | 37.37 | -0.557 | 3/8 | 5/8 | -0.09 | -0.92 |
| E8:ANC10 | 1-1 | 39.28 | 34.75 | 36.88 | 39.72 | 42.12 | 43.18 | 33.96 | 36.67 | 38.32 | -1.503 | 4/8 | 4/8 | +0.55 | +0.34 |
| E8:ANC10CP | 1-1 | 39.71 | 34.07 | 36.98 | 35.44 | 40.04 | 42.98 | 33.78 | 36.66 | 37.46 | -0.640 | 5/8 | 4/8 | -0.56 | -0.28 |
| E8:ANC3 | 1-1 | 39.40 | 34.20 | 36.68 | 35.57 | 40.09 | 40.10 | 36.27 | 36.61 | 37.36 | -0.545 | 4/8 | 6/8 | -0.65 | -0.38 |
| E8:STU10R1 | 1-1 | 39.70 | 34.44 | 37.20 | 35.53 | 38.48 | 36.66 | 36.29 | 35.92 | 36.78 | +0.041 | 6/8 | 6/8 | -0.39 | -1.81 |

Finalist rule (PLAN_C §3): **no finalist** (no configuration has ≥ 3 retrains, because none passed the screen gate).

## 4. Mechanism by region
- First-access adm = the trained GBM's first-access admission rate.
- Peak-window adm = admitted share of the simulated peak window's accesses.
- Big-offset share = share of that window's accesses ending beyond 8 MB.
- Scan peak = retrains whose peak window has > 25% big-offset accesses.
- WP2 references use 3 retrains × 4 instances; Track C configs use 1 × 4.

| region | config | P100 | P99 | top-5 | mean DT | first-access adm | peak-window adm | big-offset share | scan peak |
|---|---|---|---|---|---|---|---|---|---|
| Region7 | A | 37.69 | 32.62 | 35.81 | 21.24 | 0.087 | 0.358 | 0.155 | 0/12 |
| Region7 | A+a | 37.11 | 32.08 | 35.21 | 21.29 | 0.084 | 0.384 | 0.129 | 0/12 |
| Region7 | X1 | 37.67 | 31.92 | 35.28 | 22.02 | 0.028 | 0.378 | 0.189 | 2/12 |
| Region7 | D8:ANC10 | 39.03 | 32.10 | 35.65 | 21.04 | 0.165 | 0.345 | 0.214 | 1/4 |
| Region7 | D8:ANC10CP | 36.93 | 32.32 | 35.36 | 21.09 | 0.130 | 0.286 | 0.186 | 1/4 |
| Region7 | D8:ANC3 | 36.74 | 31.78 | 34.75 | 21.08 | 0.185 | 0.398 | 0.115 | 0/4 |
| Region7 | D8:STU10R1 | 37.02 | 32.16 | 35.41 | 21.84 | 0.036 | 0.370 | 0.115 | 0/4 |
| Region7 | E8:ANC10 | 37.66 | 31.70 | 34.99 | 21.20 | 0.124 | 0.368 | 0.226 | 1/4 |
| Region7 | E8:ANC10CP | 36.55 | 31.82 | 34.92 | 21.25 | 0.099 | 0.380 | 0.115 | 0/4 |
| Region7 | E8:ANC3 | 36.46 | 31.55 | 34.50 | 21.34 | 0.121 | 0.418 | 0.115 | 0/4 |
| Region7 | E8:STU10R1 | 36.72 | 31.77 | 35.14 | 21.95 | 0.039 | 0.395 | 0.106 | 0/4 |
| Region6 | A | 39.31 | 33.11 | 37.09 | 21.43 | 0.002 | 0.215 | 0.336 | 9/12 |
| Region6 | A+a | 38.65 | 32.68 | 36.06 | 21.55 | 0.007 | 0.289 | 0.334 | 9/12 |
| Region6 | X1 | 36.73 | 32.63 | 35.28 | 21.72 | 0.004 | 0.407 | 0.102 | 2/12 |
| Region6 | D8:ANC10 | 39.11 | 33.19 | 36.86 | 21.52 | 0.005 | 0.277 | 0.338 | 3/4 |
| Region6 | D8:ANC10CP | 40.11 | 33.23 | 37.68 | 21.52 | 0.004 | 0.256 | 0.250 | 2/4 |
| Region6 | D8:ANC3 | 39.18 | 33.29 | 37.08 | 21.60 | 0.010 | 0.307 | 0.249 | 2/4 |
| Region6 | D8:STU10R1 | 37.73 | 32.84 | 36.15 | 21.61 | 0.008 | 0.336 | 0.143 | 1/4 |
| Region6 | E8:ANC10 | 38.98 | 32.63 | 36.74 | 21.67 | 0.009 | 0.321 | 0.243 | 2/4 |
| Region6 | E8:ANC10CP | 38.36 | 32.60 | 36.42 | 21.60 | 0.009 | 0.334 | 0.250 | 2/4 |
| Region6 | E8:ANC3 | 38.27 | 32.85 | 36.24 | 21.69 | 0.013 | 0.375 | 0.217 | 2/4 |
| Region6 | E8:STU10R1 | 36.84 | 32.45 | 35.30 | 21.74 | 0.009 | 0.393 | 0.219 | 2/4 |

**Reading.**
- **Region7.** Anchored labels raise first-access admission 3–6× over X1 and give the best Region7 P100 (E8:ANC3 36.46; D8:ANC3 36.74 even without α). This fixes X1's Region7 failure mode, as planned.
- **Region6.** X1's gain came from admitting the big scan episodes in the peak window (peak-window adm 0.41, scan peaks 2/12). The anchors relabel too few of them (peak-window adm 0.32–0.38; scan peaks remain), so Region6 falls back toward A+α.
- **The student design (STU10R1)** keeps X1's Region6 behaviour (36.84) and is comparable on Region7 (36.72). It is closest to a combined gain, but not by the pre-registered gate.

## 5. Deviations and integrity
- **Driver restarts.**
  - First launch: un-bwrapped (as WP2 did); killed after 1 minute and relaunched under bwrap (nested bwrap verified).
  - Second restart: to improve threshold seeding (anchored designs use the Baleen-kind WR map; seeding only). It was done when no train was running; the 14 orphan sims held their slots (`src/hold_orphans.sh`) and were reused.
- **Foreign CPU load.** A foreign job (another project; it uses the Baleen env's interpreter from outside this repo, running since 10-10) occupied ~15 of 24 CPUs. Sims ran ~4× slower. Results are unaffected (deterministic in their inputs).
- **Shared resources.** Every train held `2_deployable_peak/.train.lock`. Sims took slots from wp8's own SimSlot pool (cap 14 while TIMING_IDLE exists; nothing else of this project was running). Every Baleen process ran under taskset + bwrap with a private /tmp.
- **`check_frozen.sh`: frozen OK (94 files).**
- **Files under 0_reproduce/1_literature_review newer than `.leak_marker`:** 148, all dated 2026-10-10. All are `cpython-312/313 .pyc` files in the env site-packages. They are known, not from this project, and were left in place.
- **Privacy and git.** `privacy_scrub --check`: clean. Files carrying absolute paths (`results/train`, `cfg`, `converge`, `wrmap_pairs.jsonl`) are git-ignored. No git writes.
