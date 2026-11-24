# 6_final: where every number on the final slides comes from

Deck: `PeakBaleen_Final_v1.pptx` (13 slides + 3 backup), built by `build_deck.py`. Chart values are read from `result/numbers.json`, which `code/recompute_final.py` computes from the raw result CSVs (printed log: `result/recompute_final_out.txt`). No new experiment was run for this deck; every result comes from the runs recorded in `RESEARCH.md`.

| Slide | Content | Main source |
|---|---|---|
| 2 | Motivation | Baleen paper §3.1 (`documents/Baleen_FAST24_Wong.pdf`) |
| 3 | Task and test protocol | `changes/0_reproduce/RESULTS.md`, `changes/SCOPE_v2.md` |
| 4 | Baselines table | same rows as the mid-term slide 3 (`changes/5_midterm/SOURCES.md`) |
| 5 | Key idea (schematic, illustrative values) and formulation | `changes/2_deployable_peak/wp2_deployed/src/q2lib/q2anneal.py`, `documents/proposal_docx_compose/figures/fig2.py` |
| 6–7 | Design and algorithms | `changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md`, `changes/5_midterm/algorithm/alg.tex` |
| 8–9 | Offline result and solvers | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`, `wp5_ising/RESULTS_test.md`, `wp5_ising/RESULTS_dev.md` |
| 10–11 | Deployed results and ablation | `wp3_test/trials.csv`, `wp9_region5/trials.csv`, `3_autoresearch/work/t2u_region4/trials_test.csv`, `wp10_schedule/trials_test.csv` |
| 12 | Why the labels fail | the same trials (columns `peak_adm`, `peak_bigoff_share`), `wp3_test/RESULTS_test.md` §2, `wp2_deployed/RESULTS_dev.md` |
| 15–17 | Backup | `wp9_region5/RESULTS_test.md`, `changes/0_reproduce/RESULTS.md`, `changes/1_literature_review/lit_review_qubo/REPORT.md` |

## Every value, with file and line (checked by `code/check_sources.py`)

| Slide | Value | Source | What |
|---|---|---|---|
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
| 2 | §3.1 | `documents/proposal_docx_compose/proposal.js#L153` | Baleen's own deferral of peak optimization, quoted from the paper (proposal source) |
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
| 8 | 33/39 | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L102` | busiest simulated window moves (continued line) |
| 8 | short bursts | `changes/2_deployable_peak/wp1_offline/RESULTS.md#L96` | Region4 explanation |
| 9 | 13.03 | `changes/6_final/result/recompute_final_out.txt#L2` | LP + repair (shown 13.0%) |
| 9 | 13.15 | `changes/6_final/result/recompute_final_out.txt#L3` | CP-SAT (shown 13.2%) |
| 9 | 13.69 | `changes/6_final/result/recompute_final_out.txt#L4` | Ising (shown 13.7%) |
| 9 | 18/39 | `changes/6_final/result/recompute_final_out.txt#L5` | Ising below CP-SAT |
| 9 | 22/39 | `changes/6_final/result/recompute_final_out.txt#L5` | Ising below LP |
| 9 | 1/6 | `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L12` | tight budget 1 s |
| 9 | 6/6 | `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L12` | tight budget 3 s |
| 9 | 4/6 | `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L12` | tight budget 10 s |
| 9 | >= 5/6 at >= 2 budgets | `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L17` | the pre-registered count rule |
| 9 | 214 MB | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L28-L29` | matrix-free SB memory |
| 9 | 126k | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L29` | variables |
| 9 | 165 MB | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L31` | parallel tempering memory |
| 9 | ~70k | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L31` | dense SB package out of memory |
| 9 | 123-GB | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L31` | machine memory |
| 10 | +13.23 | `changes/6_final/result/recompute_final_out.txt#L40` | Region7 s0.5 collapse (shown +13.2) |
| 10 | +8.74 | `changes/6_final/result/recompute_final_out.txt#L46` | Region5 s0.5 collapse (+8.7) |
| 10 | +4.40 | `changes/6_final/result/recompute_final_out.txt#L47` | Region5 s0.6 (+4.4) |
| 10 | -4.76 | `changes/6_final/result/recompute_final_out.txt#L46` | adaptive bar, Region5 s0.5 (−4.8) |
| 10 | +3.2% | `changes/6_final/result/recompute_final_out.txt#L18` | full design, Region6+7 |
| 10 | wins 5/6 | `changes/6_final/result/recompute_final_out.txt#L18` | full design wins, Region6+7 |
| 10 | +5.3% | `changes/6_final/result/recompute_final_out.txt#L23` | full design, Region5 |
| 10 | wins 3/6 | `changes/6_final/result/recompute_final_out.txt#L23` | full design wins, Region5 |
| 10 | -2.5% | `changes/6_final/result/recompute_final_out.txt#L16` | adaptive bar, Region6+7 |
| 10 | -3.2% | `changes/6_final/result/recompute_final_out.txt#L21` | adaptive bar, Region5 |
| 10 | YES | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L11` | adaptive bar, Region5: pre-registered pass |
| 10 | NO | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L10` | full design, Region6+7: pre-registered fail |
| 12 | 0.48 | `changes/6_final/result/recompute_final_out.txt#L50` | Region7 s0.5 big-offset share (48%) |
| 12 | 0.52 | `changes/6_final/result/recompute_final_out.txt#L53` | Region5 s0.5 big-offset share (52%) |
| 12 | 0.57 | `changes/6_final/result/recompute_final_out.txt#L50` | admission, Baleen |
| 12 | 0.67 | `changes/6_final/result/recompute_final_out.txt#L51` | admission, + adaptive bar |
| 12 | 0.09 | `changes/6_final/result/recompute_final_out.txt#L52` | admission, full design |
| 12 | 0.39 | `changes/6_final/result/recompute_final_out.txt#L53` | admission, Baleen |
| 12 | 0.56 | `changes/6_final/result/recompute_final_out.txt#L54` | admission, + adaptive bar |
| 12 | 0.28 | `changes/6_final/result/recompute_final_out.txt#L55` | admission, full design |
| 12 | 8 MB | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L45` | scan definition (accesses ending beyond 8 MB) |
| 12 | not scans | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L49` | Region7's training-day peaks are not scans |
| 12 | 39.07 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L26` | Region7 s0.5 Baleen (39.1) |
| 12 | 52.30 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L26` | Region7 s0.5 full design (52.3) |
| 12 | 41% | `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L47` | Region6 dev, full design admission |
| 12 | 22% | `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L47` | Region6 dev, Baleen |
| 12 | 10/12 | `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L47` | peak moved off the scan |
| 12 | same mechanism | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L19` | Region5 s0.5 fails the same way |
| 15 | 0.09 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L11` | retrain-level SE used by the rule |
| 15 | 0.75 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L11` | sample-level SE |
| 15 | +1.16 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L11` | mean gain |
| 15 | 69% | `changes/6_final/result/recompute_final_out.txt#L66` | share of the gain from s0.5 |
| 15 | 4.76 | `changes/6_final/result/recompute_final_out.txt#L64` | s0.5 gain |
| 15 | 6/6 | `changes/6_final/result/recompute_final_out.txt#L22` | + load + bar wins |
| 15 | -4.7% | `changes/6_final/result/recompute_final_out.txt#L22` | + load + bar change |
| 16 | 42.455 | `changes/0_reproduce/RESULTS.md#L17` | bit-exact RejectX |
| 16 | 48.961 | `changes/0_reproduce/RESULTS.md#L18` | bit-exact CoinFlip |
| 16 | 0.6 | `changes/0_reproduce/RESULTS.md#L3` | Baleen within 0.6 points |
| 16 | 37.59 | `changes/0_reproduce/RESULTS.md#L50` | paper Fig 9 Region7 Baleen |
| 16 | 41.31 | `changes/0_reproduce/RESULTS.md#L51` | paper Fig 9 Region6 Baleen |
| 16 | 40.10 ± 0.18 | `changes/0_reproduce/RESULTS.md#L50` | ours, 9 retrains |
| 16 | 43.25 ± 0.04 | `changes/0_reproduce/RESULTS.md#L51` | ours, 9 retrains |
| 16 | 28.11 | `changes/0_reproduce/RESULTS.md#L9` | notebook: paper averages exact |
| 16 | §4.1 | `changes/0_reproduce/RESULTS.md#L66` | threshold re-converged to the write rate |
| 17 | 8.0% | `changes/1_literature_review/lit_review_qubo/REPORT.md#L86` | thesis §7.4.1 flash writes |
| 17 | 1.4% | `changes/1_literature_review/lit_review_qubo/REPORT.md#L86` | thesis §7.4.1 peak, Region3 |
| 17 | 29% | `changes/1_literature_review/lit_review_qubo/REPORT.md#L86` | thesis §7.4.2 PeakOPT analytic |
| 17 | did not reduce Peak DT | `changes/1_literature_review/lit_review_qubo/REPORT.md#L86` | Baleen §5.6 |
| 11 | 39.27 | `changes/6_final/result/recompute_final_out.txt#L14` | Region6+7, Baleen |
| 11 | 39.17 | `changes/6_final/result/recompute_final_out.txt#L15` | Region6+7, load (-0.2%) |
| 11 | -0.2% | `changes/6_final/result/recompute_final_out.txt#L15` | Region6+7, load change |
| 11 | 38.30 | `changes/6_final/result/recompute_final_out.txt#L16` | Region6+7, bar (-2.5%) |
| 11 | -2.5% | `changes/6_final/result/recompute_final_out.txt#L16` | Region6+7, bar change |
| 11 | 38.38 | `changes/6_final/result/recompute_final_out.txt#L17` | Region6+7, load_bar (-2.3%) |
| 11 | -2.3% | `changes/6_final/result/recompute_final_out.txt#L17` | Region6+7, load_bar change |
| 11 | 40.53 | `changes/6_final/result/recompute_final_out.txt#L18` | Region6+7, full (+3.2%) |
| 11 | +3.2% | `changes/6_final/result/recompute_final_out.txt#L18` | Region6+7, full change |
| 11 | 36.17 | `changes/6_final/result/recompute_final_out.txt#L19` | Region5, Baleen |
| 11 | 36.37 | `changes/6_final/result/recompute_final_out.txt#L20` | Region5, load (+0.5%) |
| 11 | +0.5% | `changes/6_final/result/recompute_final_out.txt#L20` | Region5, load change |
| 11 | 35.02 | `changes/6_final/result/recompute_final_out.txt#L21` | Region5, bar (-3.2%) |
| 11 | -3.2% | `changes/6_final/result/recompute_final_out.txt#L21` | Region5, bar change |
| 11 | 34.48 | `changes/6_final/result/recompute_final_out.txt#L22` | Region5, load_bar (-4.7%) |
| 11 | -4.7% | `changes/6_final/result/recompute_final_out.txt#L22` | Region5, load_bar change |
| 11 | 38.09 | `changes/6_final/result/recompute_final_out.txt#L23` | Region5, full (+5.3%) |
| 11 | +5.3% | `changes/6_final/result/recompute_final_out.txt#L23` | Region5, full change |
| 11 | 50.72 | `changes/6_final/result/recompute_final_out.txt#L24` | Region4, Baleen |
| 11 | 56.71 | `changes/6_final/result/recompute_final_out.txt#L25` | Region4, load (+11.8%) |
| 11 | +11.8% | `changes/6_final/result/recompute_final_out.txt#L25` | Region4, load change |
| 11 | 42.87 | `changes/6_final/result/recompute_final_out.txt#L26` | Region4, bar (-15.5%) |
| 11 | -15.5% | `changes/6_final/result/recompute_final_out.txt#L26` | Region4, bar change |
| 11 | 43.87 | `changes/6_final/result/recompute_final_out.txt#L27` | Region4, load_bar (-13.5%) |
| 11 | -13.5% | `changes/6_final/result/recompute_final_out.txt#L27` | Region4, load_bar change |
| 11 | 24.14 | `changes/6_final/result/recompute_final_out.txt#L29` | Region1, Baleen |
| 11 | 24.54 | `changes/6_final/result/recompute_final_out.txt#L30` | Region1, load (+1.7%) |
| 11 | +1.7% | `changes/6_final/result/recompute_final_out.txt#L30` | Region1, load change |
| 11 | 24.62 | `changes/6_final/result/recompute_final_out.txt#L31` | Region1, bar (+2.0%) |
| 11 | +2.0% | `changes/6_final/result/recompute_final_out.txt#L31` | Region1, bar change |
| 11 | 24.48 | `changes/6_final/result/recompute_final_out.txt#L32` | Region1, load_bar (+1.4%) |
| 11 | +1.4% | `changes/6_final/result/recompute_final_out.txt#L32` | Region1, load_bar change |
