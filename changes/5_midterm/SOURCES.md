# Mid-term slides: content, code and outputs

The slide deck in one file. Each section shows what is on a slide (tables as markdown tables, algorithms in full). After it, the **Code** that produced it, the **Output** files the numbers are read from, and the **Report** that states the result. Paths are repo-relative. Live deck: https://claude.ai/artifact/XTyrUmxzuVWm4A2p1NVZH4 (source in `changes/5_midterm/slides/`).

**Every number** is also listed in the appendix, with the exact file and line. `python3 changes/5_midterm/code/check_sources.py` checks each of them against the file. Numbers derived for the slides (Baleen's OPT column, the 14–25% gap, the % changes) come from `changes/5_midterm/code/recompute.py` → `changes/5_midterm/result/recompute_out.txt`.

---

## Slide 2 · The task

Decide what enters a flash cache under a write budget, so that the peak disk load is lowest.

- **Path of a request.** A GET first tries the flash cache (366 GB); a hit costs the disks nothing. A miss goes to the HDDs and costs disk-head time.
- **The policy we design: admission.** On a miss, should the block be written into flash?
- **Constraint.** The flash write rate stays at 35.6 MB/s (± 1%).
- **Objective.** Minimize P100, the HDD utilization (%) of the busiest 10-minute window.
- **Data.** Meta Tectonic traces from Region1–7, 0.1% samples, replayed in BCacheSim, Baleen’s simulator.
  - A *Region* is one Tectonic storage cluster, which can span a whole datacenter. Regions 1–3 were recorded in 2019, Region4 in 2021 and Regions 5–7 in 2023.
  - A *sample* `sX` is a 0.1% slice of that cluster’s blocks.

| Item | Code | Output | Report |
|---|---|---|---|
| Simulator, metric `PeakServiceTimeUtil1` | `changes/0_reproduce/baleen_code/BCacheSim/cachesim/` (frozen artifact) | per-run `*_cache_perf.txt.lzma` (not in git) | `changes/SCOPE.md` (L42–L49: metric, write-rate matching) |
| Operating point: 366.475 GB, 35.6 MB/s, 0.1% | `changes/0_reproduce/repro/make_jobs.py` (authors’ commands) | `changes/0_reproduce/work/results/fig9_jobs.csv` | `changes/0_reproduce/RESULTS.md` (L5) |
| What a Region and a sample are | — | trace directories `tectonic/201910` (Region1–3), `202110` (Region4) and `20230325` (Region5–7) | `documents/Baleen_FAST24_Wong.pdf` §5 “Workloads” |

---

## Slide 3 · Baselines we ran

Baleen beats the simple policies, but its own offline oracle shows the peak can go much lower.

| Trace | Year | Samples | CoinFlip | RejectX | Baleen | Baleen’s OPT (offline) |
|---|---|---|---|---|---|---|
| Paper, Fig. 9 | 2019–23 | avg of 7 | 34.63 | 31.95 | 28.11 | — |
| Region7 | 2023 | s0 | 48.96 | 42.46 | 40.10 | 34.52 |
| Region6 | 2023 | s0 | 43.45 | 42.32 | 43.25 | 35.56 |
| Region6 + 7 | 2023 | s0.4–0.6 | 48.64 | 40.73 | 39.27 | 33.62 |
| Region5 | 2023 | s0.1–0.6 | 44.47 | 39.35* | 36.17 | 30.10 |
| Region4 | 2021 | s0.2–0.6 | 68.84 | 65.84 | 50.72 | 38.13 |
| Region1 | 2019 | s0.1–0.6 | 50.39 | 28.20 | 24.14 | — |

- **Units.** P100 (%), lower is better, all at 35.6 MB/s. Baleen is the mean of 3–9 retrains.
- **\*RejectX on Region5.** It cannot hit the write rate on 5 of the 6 samples, so the authors’ probabilities were used.
- **Callout: 14–25%.** On the held-out sets, Baleen online sits this far above its own offline oracle (Region6 + 7: 14.4%, Region5: 16.8%, Region4: 24.8%).

| Row | Code | Output | Report |
|---|---|---|---|
| Paper, Fig. 9 | `changes/0_reproduce/repro/stage_a.py` (runs the authors’ notebook on their CSV) | `changes/0_reproduce/work/results/notebooks/fig-09-202309.ipynb` | `changes/0_reproduce/RESULTS.md` §1 |
| Region7 / Region6, s0 | `changes/0_reproduce/repro/run.py`, `analyze.py`, `retrain_dist.py` | `changes/0_reproduce/work/results/fig9_summary.md`, `retrain_dist.csv` | `changes/0_reproduce/RESULTS.md` §2, §4 |
| Region6 + 7, s0.4–0.6 | `changes/2_deployable_peak/wp3_test/src/wp3.py` (runs), `src/prep.py` (RejectX/CoinFlip), `src/evaluate_test.py` | `changes/2_deployable_peak/wp3_test/trials.csv`, `results/static_baselines.csv`, `results/evaluation.json` | `changes/2_deployable_peak/wp3_test/RESULTS_test.md` §1 |
| Region5, s0.1–0.6 | `changes/2_deployable_peak/wp9_region5/src/wp9.py`, `src/prep.py`, `src/evaluate_test.py` | `changes/2_deployable_peak/wp9_region5/trials.csv`, `results/static_baselines.csv`, `results/evaluation.json` | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md` §1 |
| Region4, s0.2–0.6 | `changes/3_autoresearch/work/union_t2/src/` (chain and `eval_test.py`) | `changes/3_autoresearch/work/t2u_region4/trials_test.csv`, `results_test/evaluation.json` | `changes/3_autoresearch/work/t2u_region4/RESULTS_test.md`, `changes/3_autoresearch/result/FINAL_REPORT.md` §3 |
| Region1, s0.1–0.6 | `changes/2_deployable_peak/wp10_schedule/src/wp10.py`, `src/evaluate_test.py` | `changes/2_deployable_peak/wp10_schedule/trials_test.csv`, `results_test/static_baselines.csv`, `results_test/evaluation.json` | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md` §1 |
| Baleen’s OPT column, the 14–25% gap | `changes/2_deployable_peak/wp1_offline/src/wp1.py` (OPT sims, column `R0`); `changes/5_midterm/code/recompute.py` | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`; `changes/5_midterm/result/recompute_out.txt` (L2–L17) | `changes/2_deployable_peak/wp1_offline/RESULTS.md` |

---

## Slide 4 · PeakBaleen design

A peak-aware offline teacher, plus a load-aware gate online. Blue = new in PeakBaleen; gray = kept from Baleen.

```
OFFLINE (training day)
  [Day-1 trace] → [Episodes] → [Min–max QUBO]* → [Ising solver: parallel tempering]* → [Train GBM: Baleen features + load_t]*
                                                                                                      │ trained model
ONLINE (every request)                                                                                ▼
  [Request a at t] → [Load meter: load_t, past 10 min only]* → [Adaptive bar θ_t]* → [Admit? s > θ_t] ← [GBM score s = f(a, load_t)]
                                                                                        → flash, else HDD
  * = new in PeakBaleen
```

| Block | Code |
|---|---|
| Episodes | `changes/0_reproduce/baleen_code/BCacheSim/episodic_analysis/` (frozen) |
| Min–max QUBO (instance, loads, objective) | `changes/2_deployable_peak/wp3_test/src/q2lib/q2core.py` (`make_form`, `obj_nb`) |
| Ising solver | `changes/2_deployable_peak/wp3_test/src/q2lib/q2run.py` (L113–L128: `pt` = `q2anneal.eim` with a QUBO penalty); `q2lib/q2anneal.py` (`eim`, L383) |
| Labels into Baleen’s trainer | `changes/2_deployable_peak/wp3_test/src/labels.py` (solve), `src/pb4_policy.py` (apply by episode identity) |
| Load feature, load meter, adaptive bar | `changes/2_deployable_peak/wp0_overlay/PATCH.diff` (`cachesim/load_features.py`: `DemandLoad` L108, `window_st` L130, `group_features` L150, clip L98/L211; `admission_policies.py` `batchAccept` L28; `train_ap.py` L366+); rebuilt by `wp0_overlay/rebuild_overlay.sh` |
| Gates for the patch | `changes/2_deployable_peak/wp0_overlay/CP1.md` (G1 bit-exact, parity), `G3_REVIEW.md` |

---

## Slide 5 · Algorithms (in full)

**Algorithm 1 · Baleen (baseline)**
```
Require: episodes E with size s_e and disk time saved d_e; flash write budget B
 1: sort E by d_e / s_e, descending                              ▷ average-optimal OPT
 2: y_e ← 1 on the longest prefix whose writes fit in B, else 0
 3: f ← TrainGBM(φ, y)
 4: for each access a do                                         [same in Alg. 2]
 5:     admit a iff f(φ(a)) > θ                                  [same in Alg. 2]
 6: end for                                                      [same in Alg. 2]
 7: tune θ so the flash write rate = B                           [same in Alg. 2]
```

**Algorithm 2 · PeakBaleen (ours)**
```
Require: as Alg. 1, plus per-window disk time saved d_{e,w} and no-cache load C_w
 1: x ← LP relaxation, rounded and repaired                      ▷ warm start            [new]
 2: L_w(x) ← C_w − Σ_e d_{e,w} x_e                                ▷ load left in window w [core]
 3: E(x) ← LSE_γ(L(x)) + P (Σ_e s_e x_e − B)²                     ▷ min–max QUBO          [core]
 4: x ← ParallelTempering(E, x, 16 replicas)                     ▷ Ising solver          [core]
 5: y_e ← x_e                                                    ▷ peak-aware labels     [new]
 6: f ← TrainGBM([φ, ℓ], y)                                                              [new]
 7: for each access a at time t do                                                       [same]
 8:     ℓ_t ← GET disk time in [t − 10 min, t)                   ▷ causal load           [new]
 9:     g ← clip((ℓ_t / 20)^−1, 0.25, 4)                                                 [new]
10:     admit a iff f(φ(a), ℓ_t) > θ · g                                                 [new]
11: end for                                                                              [same]
12: tune θ so the flash write rate = B                                                   [same]
```
The slide renders are `changes/5_midterm/algorithm/alg1.png` and `alg2.png`. They are built from `changes/5_midterm/algorithm/alg.tex` by `build.sh`.

| Line | Code |
|---|---|
| Alg. 1 L1 | `changes/0_reproduce/baleen_code/BCacheSim/episodic_analysis/policies.py` L410–L411 (`score_service_time_size_fixed` = service_time_saved / chunks_written) |
| Alg. 1 L2 | `changes/0_reproduce/baleen_code/BCacheSim/episodic_analysis/train_ap.py` L67 (label = threshold < target write rate) |
| Alg. 1 L3, Alg. 2 L6 | `changes/0_reproduce/baleen_code/BCacheSim/episodic_analysis/train_ap.py` L320 (`lgb.train`); Alg. 2 adds the `load` columns via `wp0_overlay/PATCH.diff` (`train_ap.py` hunk) |
| Alg. 1 L5 | `changes/0_reproduce/baleen_code/BCacheSim/cachesim/admission_policies.py` L317–L322 (`pred > self.threshold`) |
| Alg. 1 L7, Alg. 2 L12 | `changes/2_deployable_peak/wp3_test/src/wp3.py` L335 (`converge`: threshold search to 35.599 MB/s ± 1%) |
| Alg. 2 L1 | `changes/2_deployable_peak/wp3_test/src/q2lib/q2run.py` L55 (`start_solution`, “lp”); `q2lib/q2core.py` L534 (`lp_start_scipy`), L261 (`repair_nb`) |
| Alg. 2 L2–L3 | `changes/2_deployable_peak/wp3_test/src/q2lib/q2core.py` L128 (`obj_nb`); `q2lib/q2anneal.py` L6, L12–L13 (LSE objective, QUBO penalty P·(s·x − B)²) |
| Alg. 2 L4 | `changes/2_deployable_peak/wp3_test/src/q2lib/q2run.py` L113–L128; `q2lib/q2anneal.py` L383 (`eim`: replica exchange); settings in `changes/2_deployable_peak/wp1_offline/RESULTS.md` L27 |
| Alg. 2 L5 | `changes/2_deployable_peak/wp3_test/src/labels.py`, `src/pb4_policy.py` |
| Alg. 2 L8–L10 | `changes/2_deployable_peak/wp0_overlay/PATCH.diff` L97–L214 (`load_features.py`), L28 (`batchAccept`); summary in `wp0_overlay/G3_REVIEW.md` L9–L11 |

---

## Slide 6 · Results so far

The teacher wins offline; online, the load-aware gate is what transfers so far.

| Setting | Baleen | PeakBaleen | Change | Status |
|---|---|---|---|---|
| Offline teacher, 39 samples (Region4–7) | 33.00 | 28.59 | −13.7% | wins 37 of 39 samples |
| Full design (labels + gate), Region6 + 7 | 39.27 | 40.53 | +3.2% | fails: one collapse (Region7 s0.5) |
| Gate only, Region6 + 7 | 39.27 | 38.30 | −2.5% | observed, not pre-registered |
| Gate only, Region5 (fresh) | 36.17 | 35.02 | −3.2% | pre-registered pass, 5/6 |
| Gate only, Region4 | 50.72 | 42.87 | −15.5% | observed, not pre-registered |
| Gate only, Region1 (low load) | 24.14 | 24.62 | +2.0% | no gain |

- **Why the labels don’t transfer.** They fit day 1’s peak. In Region7 s0.5 the peak is a big scan, 48% of the window’s accesses. The Ising-label models admit 4–14% of that window; Baleen admits 56–69%.
- **Solver check.** Offline, LP (−13.0%) and CP-SAT (−13.2%) match the Ising solver: the gain comes from the min–max formulation.

| Row | Code | Output | Report |
|---|---|---|---|
| Offline teacher | `changes/2_deployable_peak/wp1_offline/src/wp1.py`, `src/wp1_analyze.py` | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`, `wp1_summary.json` | `changes/2_deployable_peak/wp1_offline/RESULTS.md` L7–L9 |
| Full design and gate, Region6 + 7 | `changes/2_deployable_peak/wp3_test/src/wp3.py`, `src/evaluate_test.py` | `changes/2_deployable_peak/wp3_test/trials.csv` (arms `Ea-1.0`/F1PT and `Aa-1.0`), `results/evaluation.json` | `changes/2_deployable_peak/wp3_test/RESULTS_test.md` §0–§3 |
| Gate, Region5 | `changes/2_deployable_peak/wp9_region5/src/wp9.py`, `src/evaluate_test.py` | `changes/2_deployable_peak/wp9_region5/trials.csv`, `results/evaluation.json` | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md` §0 |
| Gate, Region4 | `changes/3_autoresearch/work/union_t2/src/` | `changes/3_autoresearch/work/t2u_region4/trials_test.csv` | `changes/3_autoresearch/result/FINAL_REPORT.md` L66, L75 |
| Gate, Region1 | `changes/2_deployable_peak/wp10_schedule/src/wp10.py`, `src/evaluate_test.py` | `changes/2_deployable_peak/wp10_schedule/trials_test.csv`, `results_test/evaluation.json` | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md` |
| % changes | `changes/5_midterm/code/recompute.py` | `changes/5_midterm/result/recompute_out.txt` L20–L24 | — |
| Scan mechanism | `changes/2_deployable_peak/wp3_test/src/emu.py` (peak-window admission) | `changes/2_deployable_peak/wp3_test/trials.csv` (columns `peak_adm`, `peak_bigoff_share`) | `changes/2_deployable_peak/wp3_test/RESULTS_test.md` L45–L47 |

---

## Slide 7 · Next (Nov 2 – Dec 2)

- Finish the baselines: reproduce Baleen on all 7 traces, as the proposal promised.
- Make the teacher transfer: labels that survive a change in peak type (scan vs burst), for example by training over several days.
- Ablations: labels vs load feature vs gate, and when load-awareness helps (load level, peak type).
- Final test and paper: one run on samples 0.7–0.9, which have not been touched yet (`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md` L3).

---

## Appendix: every value, with file and line (checked by `code/check_sources.py`)

| Slide | Value | Source | What it is |
|---|---|---|---|
| 2 | 366 | `changes/0_reproduce/RESULTS.md#L5` | cache size, 366.475 GB |
| 2 | 35.6 | `changes/0_reproduce/RESULTS.md#L5` | flash write rate, MB/s |
| 2 | 0.1% | `changes/0_reproduce/RESULTS.md#L5` | trace sample size |
| 2 | 10 | `RESEARCH.md#L12` | the peak metric uses 10-minute windows |
| 2 | Region | `documents/Baleen_FAST24_Wong.pdf` | §5 "Workloads": 7 Meta Tectonic clusters, each can span a datacenter; 3 years; block-key sampling; day 1 trains, the rest tests |
| 2 | 201910 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L3` | Region1 recorded 2019-10 (Regions 2, 3 likewise: `changes/3_autoresearch/documents/GOOD_RESULT.md#L22-L24`) |
| 2 | 202110 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L19` | Region4 recorded 2021-10 |
| 2 | 20230325 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L19` | Regions 5–7 recorded 2023-03-25 |
| 3 | 34.63 | `changes/0_reproduce/RESULTS.md#L9` | paper Fig. 9 average, CoinFlip |
| 3 | 31.95 | `changes/0_reproduce/RESULTS.md#L9` | paper Fig. 9 average, RejectX |
| 3 | 28.11 | `changes/0_reproduce/RESULTS.md#L9` | paper Fig. 9 average, Baleen |
| 3 | 48.96 | `changes/0_reproduce/RESULTS.md#L18` | Region7 s0, CoinFlip (ours = authors') |
| 3 | 42.46 | `changes/0_reproduce/RESULTS.md#L17` | Region7 s0, RejectX |
| 3 | 40.10 | `changes/0_reproduce/RESULTS.md#L50` | Region7 s0, Baleen, mean of 9 retrains |
| 3 | 34.52 | `changes/5_midterm/result/recompute_out.txt#L2` | Region7 s0, Baleen's offline OPT (WP1 `R0`) |
| 3 | 43.45 | `changes/0_reproduce/RESULTS.md#L20` | Region6 s0, CoinFlip |
| 3 | 42.32 | `changes/0_reproduce/RESULTS.md#L19` | Region6 s0, RejectX |
| 3 | 43.25 | `changes/0_reproduce/RESULTS.md#L51` | Region6 s0, Baleen, mean of 9 retrains |
| 3 | 35.56 | `changes/5_midterm/result/recompute_out.txt#L3` | Region6 s0, Baleen's offline OPT |
| 3 | 48.64 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L28` | Region6+7 s0.4–0.6, CoinFlip |
| 3 | 40.73 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L28` | Region6+7 s0.4–0.6, RejectX |
| 3 | 39.27 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L28` | Region6+7 s0.4–0.6, Baleen (arm A) |
| 3 | 33.62 | `changes/5_midterm/result/recompute_out.txt#L4` | Region6+7 s0.4–0.6, Baleen's offline OPT |
| 3 | 44.47 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L31` | Region5 s0.1–0.6, CoinFlip |
| 3 | 39.35 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L31` | Region5 s0.1–0.6, RejectX (authors' probabilities) |
| 3 | 36.17 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L31` | Region5 s0.1–0.6, Baleen |
| 3 | 30.10 | `changes/5_midterm/result/recompute_out.txt#L5` | Region5 s0.1–0.6, Baleen's offline OPT |
| 3 | s0.4 is matched | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L33` | footnote: RejectX misses the write rate on the other 5 Region5 samples |
| 3 | 68.84 | `changes/3_autoresearch/result/FINAL_REPORT.md#L68` | Region4 s0.2–0.6, CoinFlip |
| 3 | 65.84 | `changes/3_autoresearch/result/FINAL_REPORT.md#L68` | Region4 s0.2–0.6, RejectX |
| 3 | 50.72 | `changes/3_autoresearch/result/FINAL_REPORT.md#L66` | Region4 s0.2–0.6, Baleen |
| 3 | 38.13 | `changes/5_midterm/result/recompute_out.txt#L6` | Region4 s0.2–0.6, Baleen's offline OPT |
| 3 | 50.39 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L31` | Region1 s0.1–0.6, CoinFlip |
| 3 | 28.20 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L31` | Region1 s0.1–0.6, RejectX |
| 3 | 24.14 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L31` | Region1 s0.1–0.6, Baleen |
| 3 | 14 | `changes/5_midterm/result/recompute_out.txt#L15` | lower end of "14–25%" (Baleen above its OPT, Region6+7 test: 14.4%) |
| 3 | 25 | `changes/5_midterm/result/recompute_out.txt#L17` | upper end of "14–25%" (Region4: 24.8%) |
| 3 | 9 | `changes/0_reproduce/RESULTS.md#L48` | footnote "3–9 retrains": reproduction rows use 9 retrains |
| 3 | 3 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L21` | footnote "3–9 retrains": test rows use 3 matched retrains |
| 4 | 10 | `changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md#L9` | load meter: GET disk time over the last 10 minutes, strictly before t |
| 5 | service_time_saved, rl.chunks_written | `changes/0_reproduce/baleen_code/BCacheSim/episodic_analysis/policies.py#L410-L411` | Algorithm 1 line 1: Baleen's OPT ranks episodes by d_e / s_e |
| 5 | 16 replicas | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L27` | Algorithm 2 lines 1, 4: PT with 16 replicas, LP start, QUBO budget penalty |
| 5 | LSE_g | `changes/2_deployable_peak/wp2_deployed/src/q2lib/q2anneal.py#L6` | Algorithm 2 line 3: smooth max over windows |
| 5 | P*(s.x - B)^2 | `changes/2_deployable_peak/wp2_deployed/src/q2lib/q2anneal.py#L12` | Algorithm 2 line 3: QUBO budget penalty |
| 5 | 0.25, 4 | `changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md#L11` | Algorithm 2 line 9: θ_t = θ · clip((load_10m/20)^α, 0.25, 4) |
| 5 | α = −1 | `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L15` | the α used in every tested arm |
| 6 | 33.00 | `changes/5_midterm/result/recompute_out.txt#L27` | offline: Baleen's OPT, mean of 39 samples |
| 6 | 28.59 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L9` | offline: min–max PT (Ising), mean of 39 samples |
| 6 | 13.7 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L9` | offline: mean per-sample reduction 13.69% |
| 6 | 37 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L9` | offline: wins 37 of 39 |
| 6 | 40.53 | `changes/5_midterm/result/recompute_out.txt#L20` | full design X1, Region6+7 test |
| 6 | 3.2 | `changes/5_midterm/result/recompute_out.txt#L20` | X1 vs Baleen, +3.2% |
| 6 | 52.30 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L26` | the collapse: Region7 s0.5, X1 |
| 6 | 38.30 | `changes/5_midterm/result/recompute_out.txt#L21` | gate only (A+α), Region6+7 test |
| 6 | 2.5 | `changes/5_midterm/result/recompute_out.txt#L21` | A+α vs Baleen, −2.5% |
| 6 | 35.02 | `changes/5_midterm/result/recompute_out.txt#L22` | gate only, Region5 (pre-registered H4) |
| 6 | 3.2 | `changes/5_midterm/result/recompute_out.txt#L22` | A+α vs Baleen on Region5, −3.2% |
| 6 | 5/6 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L11` | H4 wins vs Baleen |
| 6 | 42.87 | `changes/5_midterm/result/recompute_out.txt#L23` | gate only, Region4 |
| 6 | 15.5 | `changes/5_midterm/result/recompute_out.txt#L23` | A+α vs Baleen on Region4, −15.5% |
| 6 | 24.62 | `changes/5_midterm/result/recompute_out.txt#L24` | gate only, Region1 |
| 6 | 2.0 | `changes/5_midterm/result/recompute_out.txt#L24` | A+α vs Baleen on Region1, +2.0% |
| 6 | 48% | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L45` | Region7 s0.5 peak window: share of big-offset (scan) accesses |
| 6 | 4–14% | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L47` | peak-window admission, Ising-label models |
| 6 | 56–69% | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L46` | peak-window admission, Baleen-label models |
| 6 | 13.0 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L7` | offline LP, −13.03% |
| 6 | 13.2 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L8` | offline CP-SAT, −13.15% |
| 7 | 0.7–0.9 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L3` | reserve samples, untouched |
