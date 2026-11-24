# 6_final v3: where every number on the v3 slides comes from

Deck: `PeakBaleen_Final_v3.pptx` (13 slides + 2 backup), built by `build_deck_v3.py`. v3 = v2 with slide 2 rewritten (its sketch is schematic and carries no data). Chart values come from `result/numbers.json` (`code/recompute_final.py`) and `result/numbers_v2.json` (`code/recompute_final_v2.py`), both computed from the raw result ledgers.

| Slide | Content | Main source |
|---|---|---|
| 2–5 | Motivation, task, baselines, key idea | as in `SOURCES.md` (v1) |
| 6–7 | Design and algorithm | `changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md` (either-model admission), `changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md`, `algorithm_v2/alg.tex` |
| 8–9 | Offline and solver | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`, `wp5_ising/RESULTS_test.md`, `wp5_ising/RESULTS_dev.md` |
| Slide 10 | Online with Ising labels (dev) | `changes/2_deployable_peak/wp2_deployed/trials.csv` |
| Slide 11 | PeakBaleen on 10 dev samples | `changes/3_autoresearch/work/union/trials_dev.csv`, `results/dev_finalist.json` |
| Slide 12 | New clusters | `changes/3_autoresearch/work/t2u_region4/trials_test.csv`, `changes/2_deployable_peak/wp9_region5/trials.csv` |
| 15–16 | Backup | `changes/2_deployable_peak/wp9_region5/trials.csv`, `changes/0_reproduce/RESULTS.md` |

## Every value, with file and line (checked by `code/check_sources.py SOURCES_v3.md`)

| Slide | Value | Source | What |
|---|---|---|---|
| 2 | Motivation | Baleen paper §3.1 (`documents/Baleen_FAST24_Wong.pdf`) |
| 3 | Task and test protocol | `changes/0_reproduce/RESULTS.md`, `changes/SCOPE_v2.md` |
| 4 | Baselines table | same rows as the mid-term slide 3 (`changes/5_midterm/SOURCES.md`) |
| 5 | Key idea (schematic, illustrative values) and formulation | `changes/2_deployable_peak/wp2_deployed/src/q2lib/q2anneal.py`, `documents/proposal_docx_compose/figures/fig2.py` |
| 3 | 366 | `changes/0_reproduce/RESULTS.md#L5` | cache size, 366.475 GB |
| 3 | 35.6 | `changes/0_reproduce/RESULTS.md#L5` | flash write rate, MB/s |
| 3 | 0.1% | `changes/0_reproduce/RESULTS.md#L5` | trace sample size |
| 3 | 10 | `RESEARCH.md#L12` | the peak metric uses 10-minute windows |
| 3 | Region | `documents/Baleen_FAST24_Wong.pdf` | §5 "Workloads": 7 Meta Tectonic clusters, each can span a datacenter; 3 years; block-key sampling; day 1 trains, the rest tests |
| 3 | 201910 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L3` | Region1 recorded 2019-10 (Regions 2, 3 likewise: `changes/3_autoresearch/documents/GOOD_RESULT.md#L22-L24`) |
| 3 | 202110 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L19` | Region4 recorded 2021-10 |
| 3 | 20230325 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L19` | Regions 5–7 recorded 2023-03-25 |
| 4 | 34.63 | `changes/0_reproduce/RESULTS.md#L9` | paper Fig. 9 average, CoinFlip |
| 4 | 31.95 | `changes/0_reproduce/RESULTS.md#L9` | paper Fig. 9 average, RejectX |
| 4 | 28.11 | `changes/0_reproduce/RESULTS.md#L9` | paper Fig. 9 average, Baleen |
| 4 | 48.96 | `changes/0_reproduce/RESULTS.md#L18` | Region7 s0, CoinFlip (ours = authors') |
| 4 | 42.46 | `changes/0_reproduce/RESULTS.md#L17` | Region7 s0, RejectX |
| 4 | 40.10 | `changes/0_reproduce/RESULTS.md#L50` | Region7 s0, Baleen, mean of 9 retrains |
| 4 | 34.52 | `changes/5_midterm/result/recompute_out.txt#L2` | Region7 s0, Baleen's offline OPT (WP1 `R0`) |
| 4 | 43.45 | `changes/0_reproduce/RESULTS.md#L20` | Region6 s0, CoinFlip |
| 4 | 42.32 | `changes/0_reproduce/RESULTS.md#L19` | Region6 s0, RejectX |
| 4 | 43.25 | `changes/0_reproduce/RESULTS.md#L51` | Region6 s0, Baleen, mean of 9 retrains |
| 4 | 35.56 | `changes/5_midterm/result/recompute_out.txt#L3` | Region6 s0, Baleen's offline OPT |
| 4 | 48.64 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L28` | Region6+7 s0.4–0.6, CoinFlip |
| 4 | 40.73 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L28` | Region6+7 s0.4–0.6, RejectX |
| 4 | 39.27 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L28` | Region6+7 s0.4–0.6, Baleen (arm A) |
| 4 | 33.62 | `changes/5_midterm/result/recompute_out.txt#L4` | Region6+7 s0.4–0.6, Baleen's offline OPT |
| 4 | 44.47 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L31` | Region5 s0.1–0.6, CoinFlip |
| 4 | 39.35 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L31` | Region5 s0.1–0.6, RejectX (authors' probabilities) |
| 4 | 36.17 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L31` | Region5 s0.1–0.6, Baleen |
| 4 | 30.10 | `changes/5_midterm/result/recompute_out.txt#L5` | Region5 s0.1–0.6, Baleen's offline OPT |
| 4 | s0.4 is matched | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L33` | footnote: RejectX misses the write rate on the other 5 Region5 samples |
| 4 | 68.84 | `changes/3_autoresearch/result/FINAL_REPORT.md#L68` | Region4 s0.2–0.6, CoinFlip |
| 4 | 65.84 | `changes/3_autoresearch/result/FINAL_REPORT.md#L68` | Region4 s0.2–0.6, RejectX |
| 4 | 50.72 | `changes/3_autoresearch/result/FINAL_REPORT.md#L66` | Region4 s0.2–0.6, Baleen |
| 4 | 38.13 | `changes/5_midterm/result/recompute_out.txt#L6` | Region4 s0.2–0.6, Baleen's offline OPT |
| 4 | 50.39 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L31` | Region1 s0.1–0.6, CoinFlip |
| 4 | 28.20 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L31` | Region1 s0.1–0.6, RejectX |
| 4 | 24.14 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L31` | Region1 s0.1–0.6, Baleen |
| 4 | 14 | `changes/5_midterm/result/recompute_out.txt#L15` | lower end of "14–25%" (Baleen above its OPT, Region6+7 test: 14.4%) |
| 4 | 25 | `changes/5_midterm/result/recompute_out.txt#L17` | upper end of "14–25%" (Region4: 24.8%) |
| 4 | 9 | `changes/0_reproduce/RESULTS.md#L48` | footnote "3–9 retrains": reproduction rows use 9 retrains |
| 4 | 3 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L21` | footnote "3–9 retrains": test rows use 3 matched retrains |
| 3 | ±1% | `changes/SCOPE_v2.md#L31` | write rate matched within ±1% |
| 3 | ≥3 retrains | `changes/SCOPE_v2.md#L37` | every configuration retrained at least 3 times |
| 5 | 16 replicas | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L27` | parallel tempering, 16 replicas, LP start |
| 6 | 0.25 | `changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md#L11` | adaptive bar formula (clip 0.25-4, reference 20, α = −1) |
| 6 | 10/30/60 | `changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md#L9` | load feature windows |
| 8 | 37.46 | `changes/6_final/result/recompute_final_out.txt#L7` | Region4 OPT mean; ours 35.54 → 35.5; −5.4%, 7/9 |
| 8 | 35.54 | `changes/6_final/result/recompute_final_out.txt#L7` | Region4, ours |
| 8 | 5.4 | `changes/6_final/result/recompute_final_out.txt#L7` | Region4 reduction |
| 8 | 7/9 | `changes/6_final/result/recompute_final_out.txt#L7` | Region4 wins |
| 8 | 28.74 | `changes/6_final/result/recompute_final_out.txt#L8` | Region5 OPT |
| 8 | 24.60 | `changes/6_final/result/recompute_final_out.txt#L8` | Region5 ours |
| 8 | 14.6 | `changes/6_final/result/recompute_final_out.txt#L8` | Region5 reduction |
| 8 | 10/10 | `changes/6_final/result/recompute_final_out.txt#L8` | Region5 wins |
| 8 | 33.27 | `changes/6_final/result/recompute_final_out.txt#L9` | Region6 OPT |
| 8 | 27.71 | `changes/6_final/result/recompute_final_out.txt#L9` | Region6 ours |
| 8 | 16.6 | `changes/6_final/result/recompute_final_out.txt#L9` | Region6 reduction |
| 8 | 32.98 | `changes/6_final/result/recompute_final_out.txt#L10` | Region7 OPT |
| 8 | 27.21 | `changes/6_final/result/recompute_final_out.txt#L10` | Region7 ours |
| 8 | 17.3 | `changes/6_final/result/recompute_final_out.txt#L10` | Region7 reduction |
| 8 | 13.69 | `changes/6_final/result/recompute_final_out.txt#L4` | all 39 samples, Ising (shown −13.7%) |
| 8 | 37/39 | `changes/6_final/result/recompute_final_out.txt#L4` | samples won |
| 8 | 30/30 | `changes/6_final/result/recompute_final_out.txt#L11` | Regions 5–7 wins |
| 8 | 16.2 | `changes/6_final/result/recompute_final_out.txt#L11` | Regions 5–7 reduction |
| 16 | 42.455 | `changes/0_reproduce/RESULTS.md#L17` | bit-exact RejectX |
| 16 | 48.961 | `changes/0_reproduce/RESULTS.md#L18` | bit-exact CoinFlip |
| 16 | 0.6 | `changes/0_reproduce/RESULTS.md#L3` | Baleen within 0.6 points |
| 16 | 37.59 | `changes/0_reproduce/RESULTS.md#L50` | paper Fig 9 Region7 Baleen |
| 16 | 41.31 | `changes/0_reproduce/RESULTS.md#L51` | paper Fig 9 Region6 Baleen |
| 16 | 40.10 ± 0.18 | `changes/0_reproduce/RESULTS.md#L50` | ours, 9 retrains |
| 16 | 43.25 ± 0.04 | `changes/0_reproduce/RESULTS.md#L51` | ours, 9 retrains |
| 16 | 28.11 | `changes/0_reproduce/RESULTS.md#L9` | notebook: paper averages exact |
| 16 | §4.1 | `changes/0_reproduce/RESULTS.md#L66` | threshold re-converged to the write rate |
| 9 | 13.69 | `changes/6_final/result/recompute_final_out.txt#L4` | Ising (13.7%) |
| 9 | 13.15 | `changes/6_final/result/recompute_final_out.txt#L3` | CP-SAT (13.2%) |
| 9 | 13.03 | `changes/6_final/result/recompute_final_out.txt#L2` | LP (13.0%) |
| 9 | 6/6 | `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L12` | 3 s budget: Ising ≤ best classical on 6/6 |
| 10 | 38.50 | `changes/6_final/result/recompute_final_v2_out.txt#L2` | dev, Baleen |
| 10 | 37.20 | `changes/6_final/result/recompute_final_v2_out.txt#L2` | dev, Ising labels + load-aware admission |
| 10 | -3.4% | `changes/6_final/result/recompute_final_v2_out.txt#L2` | dev change |
| 10 | 6/8 | `changes/6_final/result/recompute_final_v2_out.txt#L2` | dev wins |
| 10 | 39.31 | `changes/6_final/result/recompute_final_v2_out.txt#L3` | Region6 dev, Baleen |
| 10 | 36.73 | `changes/6_final/result/recompute_final_v2_out.txt#L3` | Region6 dev, Ising labels |
| 10 | -6.6% | `changes/6_final/result/recompute_final_v2_out.txt#L3` | Region6 change |
| 10 | 4/4 | `changes/6_final/result/recompute_final_v2_out.txt#L3` | Region6 wins |
| 10 | 0.22 | `changes/6_final/result/recompute_final_v2_out.txt#L5` | Region6 peak window cached, Baleen (22%) |
| 10 | 0.41 | `changes/6_final/result/recompute_final_v2_out.txt#L6` | Region6 peak window cached, Ising labels (41%) |
| 10 | 9/12 | `changes/6_final/result/recompute_final_v2_out.txt#L5` | peak on a scan, Baleen |
| 10 | 2/12 | `changes/6_final/result/recompute_final_v2_out.txt#L6` | peak on a scan, Ising labels |
| 10 | +1.17 | `changes/6_final/result/recompute_final_v2_out.txt#L7` | bar gain on Ising labels |
| 10 | 8/8 | `changes/6_final/result/recompute_final_v2_out.txt#L7` | samples |
| 10 | +0.62 | `changes/6_final/result/recompute_final_v2_out.txt#L7` | bar gain on Baleen labels |
| 11 | 35.36 | `changes/6_final/result/recompute_final_v2_out.txt#L10` | PeakBaleen (Ising labels), dev |
| 11 | 36.78 | `changes/6_final/result/recompute_final_v2_out.txt#L10` | Baleen, dev |
| 11 | -3.9% | `changes/6_final/result/recompute_final_v2_out.txt#L10` | change vs Baleen |
| 11 | 10/10 | `changes/6_final/result/recompute_final_v2_out.txt#L10` | wins vs Baleen |
| 11 | 36.77 | `changes/6_final/result/recompute_final_v2_out.txt#L10` | Baleen + load |
| 11 | 9/10 | `changes/6_final/result/recompute_final_v2_out.txt#L10` | wins vs Baleen + load |
| 11 | 36.16 | `changes/6_final/result/recompute_final_v2_out.txt#L10` | Baleen + load-aware admission |
| 11 | 7/10 | `changes/6_final/result/recompute_final_v2_out.txt#L10` | wins vs it |
| 11 | 36.13 | `changes/6_final/result/recompute_final_v2_out.txt#L11` | PeakBaleen with CP-SAT labels |
| 11 | 6/10 | `changes/6_final/result/recompute_final_v2_out.txt#L11` | Ising-label version lower |
| 11 | 10 | `changes/3_autoresearch/work/union/results/dev_finalist.json#L8` | 10 development samples (DEV8 + Region5_s0 + Region1_s0) |
| 12 | 50.72 | `changes/6_final/result/recompute_final_v2_out.txt#L14` | Region4 Baleen |
| 12 | 56.71 | `changes/6_final/result/recompute_final_v2_out.txt#L14` | Region4 Baleen + load |
| 12 | 43.17 | `changes/6_final/result/recompute_final_v2_out.txt#L14` | Region4 PeakBaleen |
| 12 | 44.37 | `changes/6_final/result/recompute_final_v2_out.txt#L14` | Region4 CP-SAT labels |
| 12 | -14.9% | `changes/6_final/result/recompute_final_v2_out.txt#L14` | vs Baleen |
| 12 | wins 4/5 | `changes/6_final/result/recompute_final_v2_out.txt#L14` | wins vs Baleen |
| 12 | -23.9% | `changes/6_final/result/recompute_final_v2_out.txt#L14` | vs Baleen + load |
| 12 | wins 5/5 | `changes/6_final/result/recompute_final_v2_out.txt#L14` | wins vs Baleen + load |
| 12 | -3.2 | `changes/6_final/result/recompute_final_v2_out.txt#L15` | Region5 load-aware admission |
| 12 | -4.7 | `changes/6_final/result/recompute_final_v2_out.txt#L15` | with load feature |
| 12 | 'wins': 5 | `changes/6_final/result/recompute_final_v2_out.txt#L15` | 5/6 |
| 12 | 'wins': 6 | `changes/6_final/result/recompute_final_v2_out.txt#L15` | 6/6 |
| 12 | YES | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L11` | Region5 pre-registered test passed |
| 12 | 202110 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L19` | Region4 is the 2021 trace |
| 15 | 39.92 | `changes/6_final/result/recompute_final_out.txt#L60` | Region5_s0.1, Baleen |
| 15 | 39.32 | `changes/6_final/result/recompute_final_out.txt#L60` | Region5_s0.1, + load-aware admission |
| 15 | 39.55 | `changes/6_final/result/recompute_final_out.txt#L60` | Region5_s0.1, + load + load-aware admission |
| 15 | 33.92 | `changes/6_final/result/recompute_final_out.txt#L61` | Region5_s0.2, Baleen |
| 15 | 34.16 | `changes/6_final/result/recompute_final_out.txt#L61` | Region5_s0.2, + load-aware admission |
| 15 | 33.51 | `changes/6_final/result/recompute_final_out.txt#L61` | Region5_s0.2, + load + load-aware admission |
| 15 | 37.72 | `changes/6_final/result/recompute_final_out.txt#L62` | Region5_s0.3, Baleen |
| 15 | 37.47 | `changes/6_final/result/recompute_final_out.txt#L62` | Region5_s0.3, + load-aware admission |
| 15 | 37.28 | `changes/6_final/result/recompute_final_out.txt#L62` | Region5_s0.3, + load + load-aware admission |
| 15 | 26.39 | `changes/6_final/result/recompute_final_out.txt#L63` | Region5_s0.4, Baleen |
| 15 | 26.02 | `changes/6_final/result/recompute_final_out.txt#L63` | Region5_s0.4, + load-aware admission |
| 15 | 25.95 | `changes/6_final/result/recompute_final_out.txt#L63` | Region5_s0.4, + load + load-aware admission |
| 15 | 42.72 | `changes/6_final/result/recompute_final_out.txt#L64` | Region5_s0.5, Baleen |
| 15 | 37.96 | `changes/6_final/result/recompute_final_out.txt#L64` | Region5_s0.5, + load-aware admission |
| 15 | 35.07 | `changes/6_final/result/recompute_final_out.txt#L64` | Region5_s0.5, + load + load-aware admission |
| 15 | 36.38 | `changes/6_final/result/recompute_final_out.txt#L65` | Region5_s0.6, Baleen |
| 15 | 35.19 | `changes/6_final/result/recompute_final_out.txt#L65` | Region5_s0.6, + load-aware admission |
| 15 | 35.51 | `changes/6_final/result/recompute_final_out.txt#L65` | Region5_s0.6, + load + load-aware admission |
| 15 | 36.17 | `changes/6_final/result/recompute_final_out.txt#L19` | Region5 mean |
| 15 | 35.02 | `changes/6_final/result/recompute_final_out.txt#L21` | Region5 mean |
| 15 | 34.48 | `changes/6_final/result/recompute_final_out.txt#L22` | Region5 mean |
| 12 | fresh | `changes/3_autoresearch/result/FINAL_REPORT.md#L11` | Region4 is a fresh test pool, not used for design |

