# Mid-term slides: where every number comes from

Each row maps one value shown on a slide (or said in its speaker notes) to the repo file and line it comes from. `python3 changes/5_midterm/code/check_sources.py` checks every row: the file exists, and the value appears in the cited lines (numbers may be shown rounded, e.g. 42.455 → 42.46; a % sign or a minus sign on the slide is ignored). PDF rows are checked for existence only. Values marked `recompute_out.txt` were derived from raw CSVs by `code/recompute.py`; rerun it to reproduce them.

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
