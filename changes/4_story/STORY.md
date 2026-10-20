# PeakBaleen: the research story

**Peak-aware (min–max) Ising/QUBO episode selection for Baleen (FAST '24) flash-cache admission.** Graduate Operating Systems course project, University of Notre Dame, Fall 2026. Team: Ching-Hao Chiu, Jie Fu, Sixue Xing (captain).

This is the cited record of everything the project did, from the reproduction to the auto-research loop.
- **Checking.** [`changes/4_story/code/check_story.py`](../../changes/4_story/code/check_story.py) verifies that every non-trivial number in a finding occurs somewhere in a file the finding cites. It checks only that line anchors fall inside their files (and that link targets exist), not that they point at the supporting text. It does not check arms, instances or budgets, and it skips the integers 0–12 and a few other constants. Those were checked by hand and by the two validators.
- **Recomputations** are in Appendix D.
- **Status:** story-writer round 3 of 5 (run 20261020_154140). Open items are in [`changes/4_story/result/WRITER_NOTES.md`](../../changes/4_story/result/WRITER_NOTES.md).
- **How it was produced.** This story is written by a headless writer/validator loop that, like the auto-research loop ([F61](#F61)), runs with permission checks skipped ([`changes/4_story/autoscript/run_story.sh#L24-L27`](../../changes/4_story/autoscript/run_story.sh#L24-L27)). It is instructed to write only inside `changes/4_story/` ([`changes/4_story/autoscript/agent_prompt.md#L69`](../../changes/4_story/autoscript/agent_prompt.md#L69)). This is an instruction, not an enforced sandbox.
- **The story loop's own incidents** (round 2; details in [`changes/4_story/result/WRITER_NOTES.md`](../../changes/4_story/result/WRITER_NOTES.md)): the writer redacted one absolute scratchpad path that the round-1 citation validator had printed in its committed report ([`changes/4_story/result/validator_citation_round_1.md`](../../changes/4_story/result/validator_citation_round_1.md)), because it failed the repo's privacy check; and importing the scrub tool for that briefly created a git-ignored bytecode cache under tools/, outside the write area. The writer deleted it at once.

## 0. Abstract

Baleen trains its admission model on an offline selection that maximises *average* disk-head time (DT) saved, but disks are provisioned for the *peak* 10-minute window ([`./RESEARCH.md#L10-L13`](../../RESEARCH.md#L10-L13)). We asked two questions. Can a min–max selection, written as a QUBO/Ising problem, lower the peak at the same flash write rate? And does that gain survive Baleen's online ML model?

**Offline, yes, and the gain belongs to the formulation.**
- **Phase 1.** Min–max selections beat Baleen's peak-blind oracle on 6/6 held-out instances (27.06 vs 32.28 P100) ([`changes/1_literature_review/explore/q2/RESULTS.md#L12-L20`](../../changes/1_literature_review/explore/q2/RESULTS.md#L12-L20)). They were found by the project's "Ising" solvers: CPU replica-exchange samplers started from the classical LP + round + repair solution ([F21](#F21)).
- **Phase 2.** Peak-aware selections beat the oracle on 36–37 of 39 instances in four regions, by −13.0% to −13.7% on average; pooled over Regions 5–7 the reduction is about −16% (13–18% per region) ([`changes/2_deployable_peak/wp1_offline/RESULTS.md#L3-L15`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L3-L15)).
- **Not a solver effect.** Classical LP and CP-SAT selections do just as well ([F19](#F19)). The classical LP start already delivers ≈94% of the greedy → PT analytic reduction at 10 s ([`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt); [F24](#F24)).

**Ising vs classical solvers: no pre-registered solver test passed.**
- The Ising samplers won only at one short budget per test: 10 s in Q2, 3 s in H2′.
- They lost at 1 s, at 60/300 s and in rolling re-solves.
- They tie exactly where both families reach the optimum ([`changes/1_literature_review/explore/q2/RESULTS.md#L12-L31`](../../changes/1_literature_review/explore/q2/RESULTS.md#L12-L31), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L7-L24`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L7-L24); [F70](#F70)).

**Deployed, every Ising/QUBO component failed its pre-registered test or its pre-registered dev gate:**
- Ising peak labels: phase-1 Q3 ([`changes/1_literature_review/explore/q3/RESULTS.md#L6-L15`](../../changes/1_literature_review/explore/q3/RESULTS.md#L6-L15)) and the scope-v2 test H3′ ([`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L6-L16`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L6-L16));
- deployment-aware Ising labels (Track C): failed their dev screen and never reached a test ([F50](#F50));
- an Ising-fitted threshold table: H5 ([`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L9-L17`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L9-L17)). The table was neutral on 10/18 test retrains, and PT equals the exhaustive optimum ([F59](#F59));
- a peak-label union model: the auto-research loop, whose last test failed against the threshold arm ([`changes/3_autoresearch/result/FINAL_REPORT.md#L1-L7`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L1-L7)).

For the label-based tests the recurring mechanism is that day-1 labels are brittle when the peak *type* changes (big-offset scan vs burst of new episodes). Part of this comes from how Baleen's trainer learns scans ([F68](#F68)).

**The one deployed win** is the scope-v2 load-adaptive admission threshold on Baleen's *own* models (A+α), a non-Ising control. The idea predates the Ising work: the 2026-09-14 paper audit that picked Baleen already proposed load-adaptive gating of the admission threshold ([F104](#F104)).
- **First seen as a control, then pre-registered.** It was first seen as a positive control on WP2 dev ([F39](#F39)), and then post hoc on the H3′ test ([F47](#F47)). A pre-registered test on fresh Region5 (H4) gave 35.02 vs 36.17, 5/6 ([`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L19`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L19)).
- **The margin passed only on the retrain-level SE.** At instance level the gain is +1.16 ± 0.75 (≈1.5 SE), and one instance (s0.5) gives 69% of the summed gain; the other five average +0.43 ([F53](#F53)).
- **Other regions, post hoc.** It helped on Regions 6/7 ([`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60)) and Region4 ([`changes/3_autoresearch/result/FINAL_REPORT.md#L75`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L75)). On low-load Region1 it was worse than Baleen (A+α 1/6, −0.49) ([`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19)) ([F60](#F60), [F69](#F69)).
- **Prior art.** Two earlier load-based admission attempts (Baleen §5.6 and Wong's thesis §7.4.1) did not reduce the peak, or barely did; how A+α differs is discussed in [F95](#F95).

**Freshness and the reserve.**
- "Fresh" test pools here mean *never run deployed*. WP1 had already simulated the offline OPT of the H3′, H4 and T2 pools ([F93](#F93)).
- Samples 0.7–0.9 have never been used in a deployed run. WP1 simulated them offline, and their offline instance dumps exist on disk ([F92](#F92)).

## How to read this document

- **Finding format.** `### F<id> [priority] [evidence] title`, then the claim, a one-line reason for the priority, and `Refs:`.
  - Refs are repo-relative paths; `#Lx-Ly` points at lines.
  - Each ref is a link (relative to this file).
  - Each finding has an anchor, so `[F18](#F18)` jumps to it.
- **Priority:**
  - **P0:** headline results and decisive negatives.
  - **P1:** important supporting results and mechanisms.
  - **P2:** secondary, dev or mechanism detail.
  - **P3:** infrastructure, incidents, minor notes.
- **Evidence:**
  - **TEST-PREREG:** a pre-registered pass/fail test whose protocol was committed before the run.
  - **NEGATIVE-TEST:** such a test that failed.
  - **TEST-POSTHOC:** any other observation on test data. This includes comparisons a protocol listed in advance as "reported, no pass/fail" ([F30](#F30), [F48](#F48), [F54](#F54), [F60](#F60), [F71](#F71)): no rule was tested, so they are not tagged TEST-PREREG, and their titles say "pre-declared, no pass/fail".
  - **DEV:** selection-biased development data.
  - **OFFLINE:** offline OPT or solver results.
  - **REPRO:** the reproduction.
  - **INFRA:** tooling, gates, integrity and context.
- **Caveats about the evidence labels:**
  1. **Phase-1 tests (Q1–Q3).** Their pre-registration is file-dated ([`changes/1_literature_review/explore/PROTOCOL.md#L3`](../../changes/1_literature_review/explore/PROTOCOL.md#L3)) and was committed to git only after the held-out runs ([F75](#F75)). They carry TEST-PREREG / NEGATIVE-TEST because they were the pre-specified hypotheses on held-out data, but read them as weaker than the phase-2 tests, whose protocols were git-committed first ([F73](#F73)).
  2. **H1′ (WP1).** It is tagged OFFLINE. Its criterion was fixed in [`changes/2_deployable_peak/PLAN.md#L19`](../../changes/2_deployable_peak/PLAN.md#L19) before WP1 ran, but it is an offline solver/OPT result.
  3. **"Fresh" test pools.** These were never run deployed, but some had offline OPT runs ([F93](#F93)).
- **Solver names.**
  - **"Ising" solvers.** PT and EIM are replica-exchange (parallel-tempering) samplers on the LSE-smoothed true peak, with a QUBO budget penalty (PT) or a native hinge plus augmented Lagrangian (EIM).
    - They run on CPU (no GPU, [F90](#F90)).
    - They start from the classical LP + round + repair solution in phase-1 Q1/Q2 and in every deployed F1PT/F1EIM label set. The Q3 designs (phase-1 Q3, and WP2's D:P0/D:T2) and Track C's anchored and student labels instead started from Baleen's set or the previous round ([F14](#F14), [F21](#F21)).
    - In H2′ the warm start was tuned over {LP + repair, peak-aware greedy} for both families alike; the finalists chose LP at 3/10 s and the greedy start at 1 s ([F21](#F21), [F24](#F24)).
    - SB is matrix-free simulated bifurcation on a sum-of-squares QUBO surrogate; MQ is MindQuantum QAIA (or dwave/OpenJij SA; tuned) on sub-QUBOs.
  - **Classical solvers:** LP + round + repair, HiGHS MILP, CP-SAT, and true-objective local search (LS).
- **Arm names used throughout:**
  - **A:** Baleen labels, original features.
  - **B:** A + the causal `load` feature.
  - **A+α / B+α:** A or B with the load-adaptive admission threshold θ·clip((load_10m/20)^α, 0.25, 4), α = −1.
  - **X1:** LP-started PT min–max F1 labels + `load` + α = −1.
  - **P100:** `PeakServiceTimeUtil1`, the peak backend load in % over 10-minute windows after day 1, at matched write rate 35.599 MB/s ± 1% ([`changes/SCOPE.md#L42-L49`](../../changes/SCOPE.md#L42-L49)).

## 0.1 Findings index

<!-- INDEX:BEGIN -->
104 findings: P0 9, P1 44, P2 34, P3 17. Evidence: DEV 21, INFRA 41, NEGATIVE-TEST 8, OFFLINE 13, REPRO 5, TEST-POSTHOC 13, TEST-PREREG 3.

**Headlines at a glance (the P0 findings):**

| ID | Evidence | Verdict and key number |
|---|---|---|
| F18 | TEST-PREREG | Q1 = YES: min–max selection beats Baleen's peak-blind oracle offline on 6/6 held-out instances |
| F20 | NEGATIVE-TEST | Q2 = NO: on the same F1 formulation the Ising samplers beat the best classical solver only at the 10 s budget (PT 22.524 vs 22.569 at 10 s; 22.508 vs 22.415 at 60 s) |
| F25 | OFFLINE | H1′ breadth: on 39 instances in four regions, peak-aware selection beats the peak-blind oracle on 36–37 of them by −13.0% to −13.7% on average; 30/30 and 13.0–17.7% per region on Regions 5–7 |
| F28 | NEGATIVE-TEST | H2′ = NO: at re-solve budgets of 1, 3 and 10 s the tuned Ising solvers fail the pre-registered criteria (better only at 3 s; PT 22.7336 vs best classical 22.7166 over all 18 cells) |
| F33 | NEGATIVE-TEST | Q3 = NO: Ising-family peak labels distilled into Baleen's unchanged GBM lose to Baleen on held-out instances (2/6 wins each; −0.41 to −1.07) |
| F44 | NEGATIVE-TEST | H3′ = NO: Ising peak labels + `load` + the load-adaptive threshold (X1) win 5/6 instances but lose to Baleen on the mean (40.53 vs A 39.27), failing the pre-registered rule |
| F52 | TEST-PREREG | H4 = YES: the load-adaptive admission threshold on Baleen's own models beats Baleen on fresh Region5 (pre-registered; passes on the retrain-level SE, and one instance carries 69% of the gain) |
| F59 | NEGATIVE-TEST | H5 = NO: the Ising-fitted load-bucket threshold table does not beat Baleen on fresh Region1 (24.45 vs A 24.14, 1/6); the fitted table was neutral on 10/18 test retrains |
| F65 | NEGATIVE-TEST | Auto-research T2 (Region4) = FAIL: the Ising-label union does not beat the threshold arm A+α (1/5, −0.30); its gain over Baleen is the threshold's, so the loop ends NEGATIVE |

**All findings, in document order:**

| ID | Priority | Evidence | Claim | Section |
|---|---|---|---|---|
| F01 | P1 | INFRA | The question: optimise the peak 10-minute window, not average DT saved, and keep the gain online | 1. Question, proposal and scope |
| F02 | P1 | INFRA | Scope v1 (frozen 2026-09-27): only the offline selection Policy may change; operating point and metric fixed for every method | 1. Question, proposal and scope |
| F03 | P1 | INFRA | Scope v2 (2026-09-29) widens the boundary by one causal demand-load feature group (plus optional hour of day); CP1 fixes its details | 1. Question, proposal and scope |
| F04 | P2 | INFRA | Amendments 1.2b (threshold table), 1.2c (load × access-class table) and 1.2d (union of two admission models), each behind a bit-exact gate | 1. Question, proposal and scope |
| F05 | P2 | INFRA | Team decision log: reproduce first, freeze the boundary, keep Ising central against the literature review's LP-first advice | 1. Question, proposal and scope |
| F06 | P3 | INFRA | How Baleen was chosen: an automated paper-feasibility pipeline ranked it first of eight shortlisted papers | 1. Question, proposal and scope |
| F104 | P2 | INFRA | The load-adaptive admission threshold was in the project's founding idea: the 2026-09-14 paper audit proposed peak-aware scoring plus load-adaptive gating, with no QUBO/Ising, targeting ≥ 5% | 1. Question, proposal and scope |
| F07 | P1 | REPRO | The baselines replay bit-exactly and the authors' Figure 9 notebook reproduces exactly | 2. Reproduction of Baleen |
| F08 | P1 | REPRO | Baleen matches the authors' released-metric runs within ±0.6 points; the paper's Figure 9 Baleen bars (`tracedrop`) do not reproduce | 2. Reproduction of Baleen |
| F09 | P2 | REPRO | Retraining is nondeterministic, and episode order is its only source; the peak is almost insensitive to the write budget | 2. Reproduction of Baleen |
| F10 | P2 | REPRO | README smoke test passes; the operating point is DWPD 7.5, not the proposal's 3 drive-writes per day | 2. Reproduction of Baleen |
| F98 | P2 | REPRO | Reproduction scope: sample 0 of two traces plus a Region1 smoke test; Region6 at s0 is a weak test, and no Stage B+ results are recorded | 2. Reproduction of Baleen |
| F11 | P1 | OFFLINE | The literature review and a synthetic CPU audit predicted the gain would come from the formulation, with LP beating Ising solvers | 3. Formulation, solvers and the literature review |
| F95 | P1 | INFRA | Prior art: Baleen and Wong's thesis already tried load-based admission and a fixed-window peak OPT; the novelty search is outstanding | 3. Formulation, solvers and the literature review |
| F12 | P2 | OFFLINE | Synthetic audit: matrix-free SB scales to 200k variables in about 512 MB; the dense SB package needs 58 GB at 50k | 3. Formulation, solvers and the literature review |
| F13 | P1 | INFRA | The real-harness formulation: true min–max F1 over the post-day-1 windows, nested-prefix output, and two equally tuned solver families | 3. Formulation, solvers and the literature review |
| F14 | P2 | INFRA | The phase-1 deployed (Q3) labels used an extended-Ising energy on day 1 | 3. Formulation, solvers and the literature review |
| F15 | P1 | DEV | Phase-1 harness test on sample 0: the offline gain is real, but distillation into the unchanged GBM keeps almost none of it | 3. Formulation, solvers and the literature review |
| F16 | P2 | OFFLINE | Gate 0: the analytic window loads match the simulator, and peak-aware plans migrate; the evidence points to admissions overrunning the cache | 3. Formulation, solvers and the literature review |
| F17 | P2 | OFFLINE | Phase-1 harness solver attribution: inside the hybrids the classical sub-solvers did most of the work, and the one analytic Ising edge was EIM on Region7 | 3. Formulation, solvers and the literature review |
| F103 | P2 | INFRA | Design levers harness_eval flagged for a team decision were never implemented | 3. Formulation, solvers and the literature review |
| F18 | P0 | TEST-PREREG | Q1 = YES: min–max selection beats Baleen's peak-blind oracle offline on 6/6 held-out instances | 4. Offline results |
| F19 | P1 | OFFLINE | The offline gain is a formulation effect, not a solver effect | 4. Offline results |
| F20 | P0 | NEGATIVE-TEST | Q2 = NO: on the same F1 formulation the Ising samplers beat the best classical solver only at the 10 s budget (PT 22.524 vs 22.569 at 10 s; 22.508 vs 22.415 at 60 s) | 4. Offline results |
| F21 | P1 | DEV | The proposal's own Ising design (a sum-of-squares QUBO surrogate solved by simulated bifurcation) was the weakest Ising solver in phase-1 dev tuning and in WP5; the "Ising" finalists are LP-started replica-exchange samplers on the true objective | 4. Offline results |
| F22 | P3 | DEV | Q2 post hoc: the 10 s Ising win and the 60 s CP-SAT win do not depend on the nested time split | 4. Offline results |
| F23 | P3 | DEV | Phase-1 dev on the squared-hinge F2b: the classical local search led at 10 s, so the held-out solver comparison was run on F1 | 4. Offline results |
| F24 | P1 | OFFLINE | The phase-1 "Ising" arms are a classical LP start polished by a sampler: LP + round + repair already reaches ≈94% of the greedy → PT analytic reduction, and the sampler supplies the rest | 4. Offline results |
| F25 | P0 | OFFLINE | H1′ breadth: on 39 instances in four regions, peak-aware selection beats the peak-blind oracle on 36–37 of them by −13.0% to −13.7% on average; 30/30 and 13.0–17.7% per region on Regions 5–7 | 4. Offline results |
| F26 | P1 | OFFLINE | Peak migration is the rule offline: the planned peak window almost never is the simulated one | 4. Offline results |
| F27 | P1 | OFFLINE | Region4 has little peak headroom; its peaks are short bursts the oracle already absorbs, and the losses come from migration | 4. Offline results |
| F101 | P3 | OFFLINE | WP1's peak-blind oracle R0 reproduces the authors' OPT-AP rows closely, so the H1′ comparator is the paper's own oracle | 4. Offline results |
| F28 | P0 | NEGATIVE-TEST | H2′ = NO: at re-solve budgets of 1, 3 and 10 s the tuned Ising solvers fail the pre-registered criteria (better only at 3 s; PT 22.7336 vs best classical 22.7166 over all 18 cells) | 4. Offline results |
| F102 | P2 | TEST-POSTHOC | H2′ mechanism (pre-declared per-level report, no pass/fail): at 1 s the first nested level decides, and the exact solvers cannot get past their LP rounding there | 4. Offline results |
| F29 | P2 | DEV | H2′ dev tuning: equal trials for both families, and the ranking flips with the budget | 4. Offline results |
| F30 | P2 | TEST-POSTHOC | Rolling re-solve at 1 s (pre-declared secondary, no pass/fail): the exact classical solvers win on the small window instances | 4. Offline results |
| F31 | P1 | OFFLINE | Scaling (contribution S): matrix-free SB runs real unions of up to 125541 QUBO variables in at most 214 MB, where the dense SB package runs out of memory | 4. Offline results |
| F32 | P2 | DEV | Choosing the label solver: WP5 recommended EIM, the deployed tests used the phase-1 PT configuration, and the deployed F1 label sets of PT and CP-SAT have the same day-1 peak | 4. Offline results |
| F33 | P0 | NEGATIVE-TEST | Q3 = NO: Ising-family peak labels distilled into Baleen's unchanged GBM lose to Baleen on held-out instances (2/6 wins each; −0.41 to −1.07) | 5.1 Phase 1 (Q3) |
| F34 | P1 | DEV | Q3 mechanism: the Ising labels changed first-access admission, not peak targeting | 5.1 Phase 1 (Q3) |
| F35 | P1 | TEST-POSTHOC | Q3 held-out: on 3/6 instances P100 is set by rare scan-like windows, and relabelling moves those decisions in either direction | 5.1 Phase 1 (Q3) |
| F36 | P1 | INFRA | The scope-v2 overlay passes CP1: bit-exact default equivalence and exact train/serve parity of `load` | 5.2 Scope v2 |
| F37 | P1 | DEV | Learnability gate PASSES: given `load`, the GBM fits the F1 (min–max) peak-aware labels much better, PT- or CP-SAT-solved alike, and Baleen's own labels not at all | 5.2 Scope v2 |
| F38 | P1 | DEV | The plain 2×2 hypothesis (Ising labels + `load`, arm D) does not survive confirmation on dev | 5.3 WP2 |
| F39 | P1 | DEV | The WP2 finalists X1/X2 (F1PT labels + `load` + α) come from a rule written after the rep-1 screen but before confirmation; about half of X1's dev gain is the threshold alone | 5.3 WP2 |
| F40 | P2 | DEV | On dev, Ising (PT/EIM) vs classical (CP-SAT) labels of the same F1 formulation: no claim either way; with α the PT labels lead by +1.26 (5/8) | 5.3 WP2 |
| F41 | P1 | DEV | WP2 mechanism: on Region6 the Ising labels plus α admit the big-offset scans that set the peak; on Region7 they suppress first-access admission | 5.3 WP2 |
| F42 | P2 | DEV | The other WP2 ablations failed their screens or the confirmation rule | 5.3 WP2 |
| F43 | P3 | INFRA | WP2 bookkeeping: 40 unmatched rows, all reported; the threshold-search bound was a tool limitation | 5.3 WP2 |
| F44 | P0 | NEGATIVE-TEST | H3′ = NO: Ising peak labels + `load` + the load-adaptive threshold (X1) win 5/6 instances but lose to Baleen on the mean (40.53 vs A 39.27), failing the pre-registered rule | 5.4 WP3 |
| F45 | P1 | NEGATIVE-TEST | H3′-labels = NO: X1 is not better than the same threshold on Baleen's own models | 5.4 WP3 |
| F46 | P1 | TEST-POSTHOC | Why H3′ failed: one big-offset scan peak (Region7 s0.5) that the F1-label models do not admit | 5.4 WP3 |
| F47 | P1 | TEST-POSTHOC | Post hoc on the H3′ test: the load-adaptive threshold on Baleen's own models is the best configuration | 5.4 WP3 |
| F48 | P2 | TEST-POSTHOC | H3′ pre-declared comparisons (no pass/fail): CP-SAT labels have the lower mean by 0.89 at ≈1 instance SE, and retention is negative for every F1-label arm | 5.4 WP3 |
| F49 | P2 | DEV | Track C stage 1: the cheap deployed proxy fails its pre-registered validation, so every screen used full simulations | 5.5 Track C (WP8) |
| F50 | P1 | DEV | Track C stage 2 is negative: no deployment-aware Ising objective passes the pre-registered dev screen | 5.5 Track C (WP8) |
| F51 | P3 | DEV | Track C near miss: a single retrain of STU10R1 had the lowest dev mean, but the pre-registered gate rejected it | 5.5 Track C (WP8) |
| F52 | P0 | TEST-PREREG | H4 = YES: the load-adaptive admission threshold on Baleen's own models beats Baleen on fresh Region5 (pre-registered; passes on the retrain-level SE, and one instance carries 69% of the gain) | 5.6 WP9 |
| F53 | P1 | TEST-PREREG | H4 caveats: the margin rests on the retrain-level SE, one instance carries most of the gain, and RejectX could not be matched | 5.6 WP9 |
| F54 | P1 | TEST-POSTHOC | The Ising record X1 on Region5 (pre-declared, no pass/fail): it fails the reported rule again, with one catastrophic scan-type instance and a second large loss | 5.6 WP9 |
| F55 | P3 | INFRA | WP9 preparation: the dry run and the static replays | 5.6 WP9 |
| F56 | P2 | DEV | WP10 E1: no training-window proxy ranks threshold variants well enough (pre-registered validity criterion) | 5.7 WP10 |
| F57 | P1 | OFFLINE | WP10 E2: the Ising solver (PT) and the classical solver (coordinate descent) find the same (scale-equivalent) threshold tables on 46/48 packs | 5.7 WP10 |
| F58 | P2 | DEV | WP10 E3: TB:pt is the dev finalist under a rule written before any E2 solve or E3 simulation | 5.7 WP10 |
| F59 | P0 | NEGATIVE-TEST | H5 = NO: the Ising-fitted load-bucket threshold table does not beat Baleen on fresh Region1 (24.45 vs A 24.14, 1/6); the fitted table was neutral on 10/18 test retrains | 5.7 WP10 |
| F60 | P1 | TEST-POSTHOC | On low-load Region1 the α arms are worse than Baleen (A+α 1/6, −0.49; pre-declared reported comparison, no pass/fail) | 5.7 WP10 |
| F61 | P2 | INFRA | The auto-research contract: an Ising-centric Y, a fresh pre-registered pool, a stricter rule and at most two test spends | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F62 | P2 | DEV | Auto-research H-CLS (Ising-fitted load × access-class threshold tables): no finalist | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F63 | P2 | DEV | Auto-research H-UX (union of Baleen's model and an Ising-label model): the dev finalist XA:F1PT | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F64 | P1 | NEGATIVE-TEST | Auto-research T1 (Region2): spent, failed, and unevaluable as pre-registered | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F65 | P0 | NEGATIVE-TEST | Auto-research T2 (Region4) = FAIL: the Ising-label union does not beat the threshold arm A+α (1/5, −0.30); its gain over Baleen is the threshold's, so the loop ends NEGATIVE | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F66 | P1 | TEST-POSTHOC | Region4 replicates the H4 effect post hoc: A+α is 15% below Baleen | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F67 | P1 | TEST-POSTHOC | Why the union did not transfer (the final report's interpretation): neither test pool has scan peaks | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F68 | P1 | TEST-POSTHOC | Day-1 min–max labels are brittle when the peak *type* changes (big-offset scan vs burst of new episodes) | 6. Cross-cutting mechanisms |
| F69 | P1 | TEST-POSTHOC | The load-adaptive threshold's evidence status, region by region: pre-registered YES on Region5, post-hoc on Regions 6/7 and 4, null on Region1 | 6. Cross-cutting mechanisms |
| F70 | P1 | OFFLINE | Ising and classical solvers: identical objectives where both reach the optimum, budget-dependent winners elsewhere, and a two-way record for deployed labels (at most ≈2.1 instance-level SE) | 6. Cross-cutting mechanisms |
| F71 | P1 | TEST-POSTHOC | Mean retention of the offline gain never approached the proposal's 60% target for any Ising-label configuration (pre-declared metric, no pass/fail; the 60% criterion comes only from the proposal) | 6. Cross-cutting mechanisms |
| F72 | P2 | DEV | First-access admission is the recurring lever on Region7 (mostly dev evidence) | 6. Cross-cutting mechanisms |
| F73 | P1 | INFRA | Every phase-2 and auto-research test protocol was committed to git before its test ran | 7. Methodology and integrity |
| F94 | P1 | INFRA | PLAN's pre-stated "dev signal" gate failed; instead of the pre-stated negative-and-pivot, H3′ was re-specified around PLAN's ablation arm E (labels + `load` + α) | 7. Methodology and integrity |
| F74 | P2 | INFRA | Each deployed test's evaluator was written and validated on earlier data before the test data existed, and the drivers refused to run without a go-file | 7. Methodology and integrity |
| F75 | P1 | INFRA | Phase-1 pre-registration (Q1–Q3) is file-dated, not git-attested | 7. Methodology and integrity |
| F96 | P2 | INFRA | Phase-1 forking paths and interim looks: the formulation switch also preceded Q1 (YES); all the others were followed by negative verdicts | 7. Methodology and integrity |
| F97 | P2 | INFRA | Deployed testing went beyond PLAN's instance plan, each time under its own protocol; the later G1 re-runs used one trace | 7. Methodology and integrity |
| F76 | P1 | INFRA | Gate G3 (a teammate review of the overlay patch) was waived by the captain; no teammate sign-off is recorded for scope v2 | 7. Methodology and integrity |
| F77 | P3 | INFRA | Frozen-artifact checks always passed and sandboxing was the rule (with the exceptions in F78–F82); leak-check hits came from other tools and agents | 7. Methodology and integrity |
| F78 | P3 | INFRA | Phase-1 incidents: a 25-second tuning overlap and a stray `__pycache__` file in the frozen tree's wrapper | 7. Methodology and integrity |
| F99 | P3 | INFRA | harness_eval's operational deviations | 7. Methodology and integrity |
| F79 | P3 | INFRA | Phase-2 timing incidents (WP1/WP5), handled by superseding, flagging or re-running | 7. Methodology and integrity |
| F80 | P2 | INFRA | SMT-sibling exposure in phase-1 timing and early WP5 tuning, a seed-reuse artefact in tuning, and a lost session | 7. Methodology and integrity |
| F100 | P3 | INFRA | The 10 s label and table solves outside WP5 ran without core isolation; after H2′ the timing cores were released to all tracks | 7. Methodology and integrity |
| F81 | P3 | INFRA | Track C, WP9 and WP10 operational deviations | 7. Methodology and integrity |
| F82 | P3 | INFRA | Smaller recorded disclosures not listed elsewhere in this story | 7. Methodology and integrity |
| F83 | P2 | INFRA | WP10 committed its H5 protocol after the dev confirmation had run, before its P100 values were read | 7. Methodology and integrity |
| F84 | P1 | INFRA | Auto-research integrity disclosures (final report §5) | 7. Methodology and integrity |
| F85 | P3 | INFRA | The round-1 auto-research validators failed the run on two blocking findings; both were fixed before T2's TEST_GO | 7. Methodology and integrity |
| F86 | P2 | INFRA | Six items the round-2 validators raised are not carried into the auto-research notebook or final report | 7. Methodology and integrity |
| F87 | P2 | INFRA | Privacy redaction of a public repo (2026-10-04): git history still holds the originals, and so does the current tree, inside the redaction tool | 7. Methodology and integrity |
| F88 | P3 | INFRA | Documentation drift in the index file | 7. Methodology and integrity |
| F89 | P3 | INFRA | An earlier auto-research launch (Codex worker, run 20261019_233548) did no work | 7. Methodology and integrity |
| F90 | P2 | INFRA | The hardware differed from the proposal's plan: no GPU | 7. Methodology and integrity |
| F91 | P2 | INFRA | Planned but never measured | 7. Methodology and integrity |
| F92 | P1 | INFRA | The 0.7–0.9 reserve was never used in a deployed run, but WP1 simulated it offline, including the Region6/7 reserve | 7. Methodology and integrity |
| F93 | P1 | INFRA | "Fresh" test pools were fresh only in deployed mode: WP1 had simulated the offline OPT of the H2′/H3′, H4 and T2 test instances before those tests | 7. Methodology and integrity |
<!-- INDEX:END -->

## 1. Question, proposal and scope

The proposal ([`documents/PeakBaleen_Proposal.pdf`](../../documents/PeakBaleen_Proposal.pdf); text source [`documents/proposal_docx_compose/proposal.js`](../../documents/proposal_docx_compose/proposal.js)) set three hypotheses:
- H1: an offline min–max gain;
- H2: an Ising solver beating greedy;
- H3: an online model retaining at least 60% of the offline gain.

The course spec ([`documents/CourseProject-Fall2026.pdf`](../../documents/CourseProject-Fall2026.pdf)) allows an "improvement paper" on a recent top-venue system. Baleen is [`documents/Baleen_FAST24_Wong.pdf`](../../documents/Baleen_FAST24_Wong.pdf).

The swap boundary started narrow (v1: only the offline selection `Policy`) and widened step by step:
- v2 added one causal demand-load signal and an optional load-adaptive threshold;
- amendments 1.2b, 1.2c and 1.2d added threshold tables and a two-model union.

Every widening came with a bit-exact default-equivalence gate.

<a id="F01"></a>
### F01 [P1] [INFRA] The question: optimise the peak 10-minute window, not average DT saved, and keep the gain online
Baleen ranks episodes by DT saved per byte written, which maximises total (average) DT saved. Provisioning, however, follows the peak: the P100 of backend utilisation over 10-minute windows. The project asks two things:
1. Can a min–max episode selection, formulated as QUBO/Ising, lower peak backend load at the same flash write rate?
2. Does that gain survive deployment through Baleen's online ML model?

The proposal's quantitative hypotheses:
- **H1:** min–max selection reduces Peak DT by at least 5% relative to stock Baleen, averaged over the seven Meta traces.
- **H2:** an Ising solver on a sum-of-squares surrogate beats both the artifact's greedy peak-scoring policy and a greedy warm start by at least 3%.
- **H3:** an online model with causal load features and no oracle peak window retains at least 60% of the offline gain.

**Why this priority:** it frames every verdict below; it is the reference point for "success".
Refs: [`./RESEARCH.md#L10-L13`](../../RESEARCH.md#L10-L13), [`changes/SCOPE.md#L19`](../../changes/SCOPE.md#L19), [`changes/SCOPE.md#L47`](../../changes/SCOPE.md#L47), [`documents/proposal_docx_compose/proposal.js#L199-L201`](../../documents/proposal_docx_compose/proposal.js#L199-L201)

<a id="F02"></a>
### F02 [P1] [INFRA] Scope v1 (frozen 2026-09-27): only the offline selection Policy may change; operating point and metric fixed for every method
[`changes/SCOPE.md`](../../changes/SCOPE.md) makes PeakBaleen one new `Policy` subclass. It must emit the selected set for the training budget W = 35.599 MB/s first, so that the harness's prefix rule reproduces it. Everything else is frozen: simulator, episode model, features, GBMs, label rule `threshold < target_wr`, training driver and data.

Both evaluation modes use one contract:
- **Offline:** OPT, via `simulate_ap --ap opt`.
- **Deployed:** the labels train Baleen's unchanged GBMs, then `--ap mlnew`.
- **Common settings:** cache 366.475 GB, target write rate 35.599 MB/s with the threshold re-converged to ±1%, metric `PeakServiceTimeUtil1` after day 1, train on day 1.

Consequence written at the time: the proposal's causal load features were out of scope in v1. H3 therefore became "how much offline gain survives the *unchanged* GBM", and "losing most of the gain is an expected, reportable outcome".
**Why this priority:** this contract makes every later comparison fair and comparable.
Refs: [`changes/SCOPE.md#L3-L33`](../../changes/SCOPE.md#L3-L33), [`changes/SCOPE.md#L35-L63`](../../changes/SCOPE.md#L35-L63)

<a id="F03"></a>
### F03 [P1] [INFRA] Scope v2 (2026-09-29) widens the boundary by one causal demand-load feature group (plus optional hour of day); CP1 fixes its details
**Why v2.** It exists because phase-1 peak labels did not survive distillation (retention ≈ 0; the GBM has no time or load signal).

**What may change.** All changes go into an overlay copy of BCacheSim:
- a `load` feature group: trailing *demand-side* DT over the last 10, 30 and 60 minutes, optionally with hour of day as sin/cos (the `tod` group; the only deployed arm using it was WP2's D2 ablation, [F42](#F42); it was also fitted in the learnability gate and parity-tested in WP0). Demand-side is required because it is identical in training and serving, which rules out train/serve skew.
- optionally, a load-adaptive threshold θ_t = θ·g(load_t) with a fixed shape parameter, off by default;
- optionally, `load` for the prefetch models.

**CP1 clarifications (2026-10-01):**
- `load` counts GET demand only;
- one plumbing line in `train.py`;
- a known train/serve skew for the prefetch-model `load` ("arm E only"; in practice only WP2's Epf screen used prefetch `load`, [F104](#F104));
- the admission `load` is exact on 26,499 accesses;
- ≥3 retrains per configuration.

**Gates:** G1 default bit-equivalence; G2 the same pipeline for every method; G3 a teammate review of the diff.

**Not confirmed.** The file still says "agreed by Sixue Xing (captain) on 2026-09-29, pending confirmation by Ching-Hao Chiu and Jie Fu". No later confirmation is recorded in it.
**Why this priority:** it defines the only new signal, which became the source of the one deployed win.
Refs: [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L98-L111`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L98-L111), [`changes/2_deployable_peak/wp0_overlay/PROGRESS.md#L20`](../../changes/2_deployable_peak/wp0_overlay/PROGRESS.md#L20), [`changes/SCOPE_v2.md#L3-L25`](../../changes/SCOPE_v2.md#L3-L25), [`changes/SCOPE_v2.md#L33-L50`](../../changes/SCOPE_v2.md#L33-L50)

<a id="F04"></a>
### F04 [P2] [INFRA] Amendments 1.2b (threshold table), 1.2c (load × access-class table) and 1.2d (union of two admission models), each behind a bit-exact gate
**1.2b** (WP10, 2026-10-19) replaces the power law g by a piecewise-constant table, fitted on the training day only (`--ap-load-adapt-table`).
- It is recorded in [`changes/SCOPE_v2.md`](../../changes/SCOPE_v2.md) §1a.
- It lives in a separate overlay `PATCH_v3.diff` (+43/−1 lines over `PATCH.diff`).
- G1_v3 passed, and a table reproducing the power law was bit-identical to `--ap-load-adapt-alpha -1` (P100 39.5715164464613 both).

**1.2c (class table) and 1.2d (union)** were proposed by the auto-research worker on 2026-10-20.
- Both are "used only inside" `changes/3_autoresearch/work/`. They are **not** recorded in [`changes/SCOPE_v2.md`](../../changes/SCOPE_v2.md) §1a, which mentions only 1.2b.
- G1_v4 and G1_v5 passed:
  - frozen vs overlay are bit-identical on all 425 result keys;
  - a union whose second model can never admit (κ = 1e9), or that unions a model with itself, reproduces the A+α run bit-for-bit.

**No review gate.** These gates are automated bit-exact equivalence checks: the default path is unchanged, and degenerate settings of the new option reproduce the existing α run bit-for-bit. They do not review the new code path itself. No teammate review was required or recorded for `PATCH_v3`, v4 or v5, while the G3 review of `PATCH.diff` was itself waived ([F76](#F76)). The H5 test ran on overlay v3, and both auto-research tests that ran (T1 and T2 of the union family) ran on v5.

**Why this priority:** it shows how far the boundary moved and that each move was gated; it is secondary to the results.
Refs: [`changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md#L15`](../../changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md#L15), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L30`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L30), [`changes/3_autoresearch/work/t1u_region2/PROTOCOL.md#L27`](../../changes/3_autoresearch/work/t1u_region2/PROTOCOL.md#L27), [`changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L29`](../../changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L29), [`changes/SCOPE_v2.md#L44`](../../changes/SCOPE_v2.md#L44), [`changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md#L1-L21`](../../changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md#L1-L21), [`changes/2_deployable_peak/wp10_schedule/G1_v3.md#L6-L15`](../../changes/2_deployable_peak/wp10_schedule/G1_v3.md#L6-L15), [`changes/3_autoresearch/work/cls_table/SCOPE_AMENDMENT.md#L1-L11`](../../changes/3_autoresearch/work/cls_table/SCOPE_AMENDMENT.md#L1-L11), [`changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md#L1-L5`](../../changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md#L1-L5), [`changes/3_autoresearch/work/cls_table/G1_v4.md#L5-L19`](../../changes/3_autoresearch/work/cls_table/G1_v4.md#L5-L19), [`changes/3_autoresearch/work/union/G1_v5.md#L5-L19`](../../changes/3_autoresearch/work/union/G1_v5.md#L5-L19)

<a id="F05"></a>
### F05 [P2] [INFRA] Team decision log: reproduce first, freeze the boundary, keep Ising central against the literature review's LP-first advice
[`./RESEARCH.md`](../../RESEARCH.md) §4 records these decisions:
- 09-26: reproduce Baleen first, freeze the artifact and sandbox every run.
- 09-27: fix the swap boundary (recorded in [`changes/SCOPE.md`](../../changes/SCOPE.md)).
- 09-27: exclude Wong's thesis method from the baselines. The only source is "chat with captain"; there is no file record beyond the index.
- 09-28: reject "LP as the main method" and keep searching for Ising/QUBO selectors (captain). The literature review had recommended exactly that LP/MILP pipeline as the primary selector ([`changes/1_literature_review/lit_review_qubo/REPORT.md#L5`](../../changes/1_literature_review/lit_review_qubo/REPORT.md#L5)).
- 09-28: pre-register Q1–Q3.
- 09-29: scope v2.
- 10-01: restore Ising as required (H3′ uses Ising labels; H2′ required; scaling reported; commit `5e49299`).
- 10-03 / 10-04: commit the H2′ and H3′ protocols before the tests.
- 10-16: after H3′ failed, pre-register H4 (the load-adaptive threshold on Baleen's models) for a fresh Region5 test.

**Why this priority:** it explains the project's shape (Ising kept as a required arm by decision), but the decisions themselves are not results.
Refs: [`./RESEARCH.md#L52-L67`](../../RESEARCH.md#L52-L67), [`changes/SCOPE.md#L1-L5`](../../changes/SCOPE.md#L1-L5), [`changes/1_literature_review/lit_review_qubo/REPORT.md#L5`](../../changes/1_literature_review/lit_review_qubo/REPORT.md#L5), [`changes/2_deployable_peak/PLAN.md#L18-L25`](../../changes/2_deployable_peak/PLAN.md#L18-L25)

<a id="F06"></a>
### F06 [P3] [INFRA] How Baleen was chosen: an automated paper-feasibility pipeline ranked it first of eight shortlisted papers
On 2026-09-14 an agent pipeline ranked candidate papers for the "improvement paper" track.
- It pre-ranked 1,254 papers, then desk-checked the top 8: cloned repos, read docs, sized data. Nothing was built or run.
- Baleen (FAST '24) had the highest repository score: 26/30, verdict DOABLE, minimum data 17 MB, reproduction feasibility H.

**The yardstick machine differed from the one used.** The desk check was sized for, and run on, a "Threadripper PRO 5955WX … 16 cores / 32 threads … 125 GiB" with an RTX A5000 GPU. All experiments later ran on a 24-thread Ryzen 9 9900X with no GPU ([F90](#F90)).
**Why this priority:** project provenance; no result depends on it.
Refs: [`documents/top_doable_papers_filtered.md#L1-L40`](../../documents/top_doable_papers_filtered.md#L1-L40), [`lit_review/README.md#L1-L4`](../../lit_review/README.md#L1-L4), [`lit_review/paper_list.md#L870`](../../lit_review/paper_list.md#L870), [`changes/1_literature_review/explore/q2/RESULTS.md#L46`](../../changes/1_literature_review/explore/q2/RESULTS.md#L46)

<a id="F104"></a>
### F104 [P2] [INFRA] The load-adaptive admission threshold was in the project's founding idea: the 2026-09-14 paper audit proposed peak-aware scoring plus load-adaptive gating, with no QUBO/Ising, targeting ≥ 5%
The audit that ranked Baleen first ([F06](#F06)) lists add-on A1, "Peak-aware episode scoring and load-adaptive gating ("PeakBaleen")". The audit report was committed in `2264e66` on 2026-09-14 and never changed afterwards. A1 is the add-on named in that day's top-8 table ([`documents/top_doable_papers_filtered.md#L72`](../../documents/top_doable_papers_filtered.md#L72)), and later in the ranking table committed with the proposal on 2026-09-26 (`527f8bc`; one-liner in Appendix D).
- **Hypothesis.** Scoring episodes by their contribution to the peak 10-minute windows, and "modulating the admission threshold and the ML-When prefetch gate by the current load level", reduces Peak DT by ≥ 5% over stock Baleen at the same write rate on the 7 Meta traces.
- **Mechanism.** (i) Weight each episode's DT saved by the load percentile of the windows its hits fall in. (ii) Raise the ML-When confidence threshold off-peak and lower it near peak, from a short trailing-load estimate. (iii) Re-run the convergence loop so the write-rate constraint still holds.
- **Scoop check "clear"**, from two web queries. The closest prior work it names is CacheSack (a knapsack over admission policies for *average* cost) and HALP (eviction). It did not find Wong's thesis load-dependent thresholds, which the later literature review did ([F95](#F95)).
- The audit does not mention QUBO or Ising (a case-insensitive grep finds only the substrings in "surprising" and "optimising").

**How the idea maps onto what was tested.**
- Part (i) became the min–max episode selection: an offline win ([F18](#F18), [F25](#F25)), not a deployed one.
- The load-adaptive admission threshold became SCOPE_v2 item 1.2, arm A+α. It is the source of the only pre-registered deployed gain (H4, −3.2% on Region5, [F52](#F52)). That is below A1's ≥ 5% hypothesis, and on Region1 (the H5 test pool) A+α was worse than Baleen ([F60](#F60)).
- The prefetch gate became SCOPE_v2 item 1.3, the `load` group in the prefetch models ("the proposal's load-adaptive gate"). PLAN listed it as an option of arm E, but it was tested only as WP2's dev screen Epf:F1PT (Region7 only, 1 retrain × 4 instances, not confirmed; [F42](#F42)). X1 and every test arm used the default prefetch models (empty `pf_subset` in the ledgers).

**Why this priority:** it fixes the provenance of the one deployed gain: the threshold predates the QUBO/Ising work and was not derived from it. This bears on how the result may be credited; it is not a result itself.
Refs: [`changes/2_deployable_peak/PLAN.md#L60`](../../changes/2_deployable_peak/PLAN.md#L60), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L63`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L63), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L132`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L132), [`changes/2_deployable_peak/wp3_test/trials.csv`](../../changes/2_deployable_peak/wp3_test/trials.csv), [`documents/top_doable_papers_filtered.md#L72`](../../documents/top_doable_papers_filtered.md#L72), [`lit_review/papers/fast24-baleen-ml-admission-and-prefetching-for/audit/report.md#L203-L258`](../../lit_review/papers/fast24-baleen-ml-admission-and-prefetching-for/audit/report.md#L203-L258), [`lit_review/ranking.md#L9`](../../lit_review/ranking.md#L9), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt), [`changes/SCOPE_v2.md#L23-L24`](../../changes/SCOPE_v2.md#L23-L24), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L15`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L15)

## 2. Reproduction of Baleen

The artifact (Baleen-FAST24 `4e3a920`, BCacheSim `ddeb2d8`) was frozen, checksummed and run unmodified under `bwrap` ([`changes/0_reproduce/README.md#L5-L15`](../../changes/0_reproduce/README.md#L5-L15)).

The headline reproduction is good, with one systematic nuance: the paper's Figure 9 Baleen bars for Regions 6/7 come from an older, unreleased DT metric (`tracedrop`).

<a id="F07"></a>
### F07 [P1] [REPRO] The baselines replay bit-exactly and the authors' Figure 9 notebook reproduces exactly
**Stage A.** The authors' own `fig-09-202309.ipynb`, run in our environment, gives Baleen 28.11, RejectX 31.95, CoinFlip 34.63 and a 12.0% saving, matching the paper exactly.

**Stage B.** Replays of the authors' `20230410_static_pf` runs are bit-exact. Peak (write rate):

| Trace | RejectX | CoinFlip |
|---|---|---|
| Region7 | 42.455 (36.00) | 48.961 (35.69) |
| Region6 | 42.321 (35.67) | 43.445 (35.57) |

`check_frozen.sh` reports all 94 artifact files unchanged.
**Why this priority:** a faithful baseline is the precondition for every comparison; it is supporting, not a project result.
Refs: [`changes/0_reproduce/RESULTS.md#L5-L22`](../../changes/0_reproduce/RESULTS.md#L5-L22), [`changes/0_reproduce/RESULTS.md#L68-L71`](../../changes/0_reproduce/RESULTS.md#L68-L71), [`changes/0_reproduce/work/results/fig9_summary.md#L11-L18`](../../changes/0_reproduce/work/results/fig9_summary.md#L11-L18)

<a id="F08"></a>
### F08 [P1] [REPRO] Baleen matches the authors' released-metric runs within ±0.6 points; the paper's Figure 9 Baleen bars (`tracedrop`) do not reproduce
**Released-metric runs match.** Against the authors' `20230421_alltraces_pfalways` Baleen runs, at matched write rate, our replays differ by −0.54, +0.35, +0.21 and −0.51 points.

**The Figure 9 bars do not.**
- The paper's Fig 9 Baleen bars (Region7 37.59, Region6 41.31) come from `20230327_tracedrop_*` runs that computed disk-head time differently. The no-cache peak is 64.69 vs 63.42 (Region7) and 59.24 vs 59.14 (Region6), and no released option reproduces this.
- Nine models per trace give 40.10 ± 0.18 (Region7) and 43.25 ± 0.04 (Region6), so the gap is systematic, not training noise.

**The automatic per-bar checker says "NOT PASSED".**
- It compares against those `tracedrop` rows: Region7 Baleen is +2.47 above its bar.
- At sample 0 the Region6 ordering fails: saving vs RejectX −2.2% ours vs 3.0% authors.

**The ≈11.3% figure is unverified.** [`./RESEARCH.md`](../../RESEARCH.md) states that "re-averaged with a consistent metric, the 12% headline is ≈11.3%". No derivation of 11.3 exists under `changes/0_reproduce/` (search in Appendix D).
**Why this priority:** this is the main reproduction nuance a reader of the paper needs; the unverified 11.3% is flagged so nobody quotes it as measured.
Refs: [`changes/0_reproduce/RESULTS.md#L24-L53`](../../changes/0_reproduce/RESULTS.md#L24-L53), [`changes/0_reproduce/work/results/fig9_summary.md#L20-L38`](../../changes/0_reproduce/work/results/fig9_summary.md#L20-L38), [`./RESEARCH.md#L36`](../../RESEARCH.md#L36)

<a id="F09"></a>
### F09 [P2] [REPRO] Retraining is nondeterministic, and episode order is its only source; the peak is almost insensitive to the write budget
**Why retrains differ.** Retraining Baleen is not deterministic: LightGBM is hard-coded to 20 threads and episode generation uses 8 worker processes. The reproduction therefore ran 8 extra retrains per trace.

**The write budget barely moves the peak.** The peak changes by less than 0.6 points as the write rate moves from 28 to 45 MB/s.

**The source of nondeterminism (later).** CP1's pinned test showed the source is `Pool.imap_unordered` episode order:
- pinning it makes frozen and overlay training byte-identical;
- LightGBM is deterministic given identical ordered inputs.

This is why scope v2 keeps the artifact's own nondeterminism and requires ≥3 retrains per configuration, as every later protocol does.
**Why this priority:** it explains the retrain-variance design of all later tests; it is a mechanism detail.
Refs: [`changes/0_reproduce/RESULTS.md#L46-L53`](../../changes/0_reproduce/RESULTS.md#L46-L53), [`changes/2_deployable_peak/wp0_overlay/CP1.md#L71-L75`](../../changes/2_deployable_peak/wp0_overlay/CP1.md#L71-L75), [`changes/2_deployable_peak/wp0_overlay/CP1.md#L94-L96`](../../changes/2_deployable_peak/wp0_overlay/CP1.md#L94-L96), [`changes/SCOPE_v2.md#L37`](../../changes/SCOPE_v2.md#L37), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L80`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L80)

<a id="F10"></a>
### F10 [P2] [REPRO] README smoke test passes; the operating point is DWPD 7.5, not the proposal's 3 drive-writes per day
**Smoke test.** The README example on Region1 gives a Baleen saving over RejectX of 16.61%, against 16.11% in the authors' `example.ipynb`. Running the authors' notebook on our results also gives 16.61%.

**Operating point.** The artifact's target write rate of 35.599 MB/s is the CSV's "Target DWPD = 7.5"; the plan adds "This is not 3 DWPD." The proposal had assumed "400 GB flash, 3 drive-writes per day"; every result here uses the artifact's operating point.

**Deviations from the authors' commands.** There were four, none of them touching an algorithm parameter:
- `--eviction-policy LRU`;
- dropping `--offline-ap-decisions`;
- serialised training;
- for Baleen, re-converging the admission threshold to the target write rate (paper §4.1).

**Why this priority:** it documents a setup mismatch with the proposal and the adaptations; it changes no verdict.
Refs: [`changes/0_reproduce/RESULTS.md#L55-L66`](../../changes/0_reproduce/RESULTS.md#L55-L66), [`changes/0_reproduce/REPRODUCE_PLAN.md#L11-L17`](../../changes/0_reproduce/REPRODUCE_PLAN.md#L11-L17), [`documents/proposal_docx_compose/proposal.js#L250`](../../documents/proposal_docx_compose/proposal.js#L250)

<a id="F98"></a>
### F98 [P2] [REPRO] Reproduction scope: sample 0 of two traces plus a Region1 smoke test; Region6 at s0 is a weak test, and no Stage B+ results are recorded
**What was reproduced.**
- Stage B replayed the 10 authors' runs behind the Figure 9 bars for Region7 and Region6 at sample 0.
- Stage 0 ran the README smoke test on Region1.
- The multi-sample option exists, but only the sample-0 results are reported.

**Its limits.**
- The plan calls Region6 at sample 0 "a weak test of the ordering": the 1.3-point gap is within the authors' 1.7-point spread. Region7 is the primary benchmark.
- Stage B+ was optional (rerunning the eviction-age/threshold convergence loop from scratch, and the Baleen no-prefetch ablation). No B+ results are recorded. The admission-threshold re-convergence was done for Baleen as deviation 4, but not the eviction-age loop.

**A dangling pointer.** RESULTS.md's integrity note says setup-time items outside the directory "are listed in README.md", but README.md contains no such list.
**Why this priority:** it bounds the "reproduces" claim (section 8, row 1).
Refs: [`changes/0_reproduce/REPRODUCE_PLAN.md#L34-L36`](../../changes/0_reproduce/REPRODUCE_PLAN.md#L34-L36), [`changes/0_reproduce/REPRODUCE_PLAN.md#L51-L55`](../../changes/0_reproduce/REPRODUCE_PLAN.md#L51-L55), [`changes/0_reproduce/README.md#L31-L48`](../../changes/0_reproduce/README.md#L31-L48), [`changes/0_reproduce/RESULTS.md#L59-L71`](../../changes/0_reproduce/RESULTS.md#L59-L71), [`changes/0_reproduce/work/results/fig9_summary.md#L1-L5`](../../changes/0_reproduce/work/results/fig9_summary.md#L1-L5)

## 3. Formulation, solvers and the literature review

Formulation (P):
- **Notation:** episode e, decision x_e ∈ {0,1}, write cost s_e, per-window saving d(e,w), no-cache load C_w, window load L_w(x) = C_w − Σ_e d(e,w) x_e.
- **Problem:** minimise max_w L_w(x) subject to Σ s_e x_e ≤ B.
- **QUBO surrogates:** a sum-of-squares penalty and an LSE soft peak.
- **Constraint handling:** a budget penalty or a native hinge.

Solvers:
- **Ising family:** parallel tempering (PT), the Extended Ising Machine (EIM, hinge + augmented Lagrangian), matrix-free simulated bifurcation (SB), and MindQuantum QAIA (bSB/dSB/CAC on contested sub-QUBOs).
- **Classical family:** greedy, peak-aware greedy, LP + round + repair, HiGHS MILP, CP-SAT, SCIP and true-objective local search (LS).

<a id="F11"></a>
### F11 [P1] [OFFLINE] The literature review and a synthetic CPU audit predicted the gain would come from the formulation, with LP beating Ising solvers
**Synthetic audit** (`ising_followup/audit/`):
- The peak-blind greedy leaves headroom above the LP bound of 3.7%, 10.6%, 11.8% and 11.8% of the greedy peak at n = 1k, 10k, 50k and 200k.
- LP round-down + repair captures 90–99.8% of that headroom in 0.002–1.7 s.
- In the median over seeds, no Ising arm reaches LP-round + repair at any size. At n = 1k they are comparable, and per seed `dwave_sa` beat LP + repair on 2 of 3 seeds.
- At 200k the HiGHS MILP found no incumbent in 300 s.

**The reports' reading.** Ising solvers win on dense quadratic objectives with few constraints at n ≤ 300, and lose or tie at realistic size with many linear rows. The report titles: "Win on formulation, then let Ising compete" and "Solve the peak LP first, anneal second".

**Caveats.** The instance is synthetic, the runs were CPU-only, and slow arms were under-converged under fixed caps.
**Why this priority:** it is the prior the experiments later confirmed (formulation wins, Ising ≈ classical); it was synthetic, so it supports but does not decide.
Refs: [`changes/1_literature_review/ising_followup/audit/AUDIT.md#L145-L166`](../../changes/1_literature_review/ising_followup/audit/AUDIT.md#L145-L166), [`changes/1_literature_review/ising_followup/audit/AUDIT.md#L195-L202`](../../changes/1_literature_review/ising_followup/audit/AUDIT.md#L195-L202), [`changes/1_literature_review/SWAPPABLE_QUBO_ISING_REPORT.md#L3`](../../changes/1_literature_review/SWAPPABLE_QUBO_ISING_REPORT.md#L3), [`changes/1_literature_review/lit_review_qubo/REPORT.md#L1-L5`](../../changes/1_literature_review/lit_review_qubo/REPORT.md#L1-L5)

<a id="F95"></a>
### F95 [P1] [INFRA] Prior art: Baleen and Wong's thesis already tried load-based admission and a fixed-window peak OPT; the novelty search is outstanding
The literature review's prior-art section records two kinds of earlier attempt.

**Load-based admission.**
- **Baleen §5.6.** An "admit only during high load" extension "saved flash writes but 'did not reduce Peak DT'".
- **Wong's thesis (CMU-CS-24-152) §7.4.1.** Load-dependent thresholds on OPT cut flash writes 8.0% but Peak DT "only 1.4% on Region3".

**Peak optimisation.**
- **Thesis §7.4.2, PeakOPT** (episodes reweighted for a *fixed* peak period). It cut Peak DT 29% analytically, but "we could not translate these savings over to simulation" because of peak migration.
- **Thesis §7.4.3, future work.** It proposes per-10-minute DT accounting, i.e. this project's d(e,w).

**Novelty table.**
- "First min-max peak-optimizing admission": ~75% for "first published, successful in simulation", ~0% for "first attempt".
- "First QUBO/Ising formulation of budget-constrained flash-cache admission": likely holds (~80%), but "Never write 'first QUBO for caching'".
- A cited-by and patent search "remain[s] **outstanding before any novelty sentence is finalized**".

**How this project's results relate.** This is an interpretation; no new measurement was made.
- **Offline.** The all-window min–max survived simulation at matched write rate ([F18](#F18), [F25](#F25)), where the fixed-window PeakOPT did not, though peaks still migrate ([F26](#F26)).
- **Deployed.** A+α differs from both earlier load-based attempts in mechanism:
  - it scales Baleen's own trained-model threshold continuously with trailing demand load, θ·clip((load_10m/20)^α, 0.25, 4);
  - the base θ is re-converged to the target write rate;
  - it is judged on P100 at a matched write rate.
- **Open question.** Whether those differences explain its different outcome (−3.2% on Region5, against a 1.4% or zero peak reduction before) was not measured. The thesis result is on Region3, which this project never ran: it was excluded from H5 for lacking samples 0.4–0.6, and the auto-research loop never spent its Region3 pool ([F61](#F61), [F64](#F64), [F65](#F65)).
- **Framing.** The review's suggested framing makes Ising "an evaluated solver, not the headline".

**Why this priority:** it is the first question a reviewer will ask about both of the story's positive results.
Refs: [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L24`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L24), [`changes/3_autoresearch/README.md#L7`](../../changes/3_autoresearch/README.md#L7), [`changes/SCOPE_v2.md#L23`](../../changes/SCOPE_v2.md#L23), [`changes/1_literature_review/lit_review_qubo/REPORT.md#L77-L90`](../../changes/1_literature_review/lit_review_qubo/REPORT.md#L77-L90), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L15`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L15), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L53`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L53)

<a id="F12"></a>
### F12 [P2] [OFFLINE] Synthetic audit: matrix-free SB scales to 200k variables in about 512 MB; the dense SB package needs 58 GB at 50k
`mfsb` never forms Q:
- at 200k it took 45 s per inner call with 512 MB peak RSS;
- it ended 8.3% of the headroom above the LP bound there (the gap still remaining).

The dense SB package at 50k needed 58 GB RSS and 17–73 minutes for a single call. MindQuantum's matrix-free J swap gives bit-identical solutions to the explicit J for bSB and dSB.
**Why this priority:** it motivated the matrix-free implementation later used for the real-instance scaling contribution ([F31](#F31)).
Refs: [`changes/1_literature_review/ising_followup/audit/AUDIT.md#L158-L190`](../../changes/1_literature_review/ising_followup/audit/AUDIT.md#L158-L190)

<a id="F13"></a>
### F13 [P1] [INFRA] The real-harness formulation: true min–max F1 over the post-day-1 windows, nested-prefix output, and two equally tuned solver families
**Instances** come from the unmodified training driver through a Policy dump:
- d(e,w) is the DT saved in 10-minute window w;
- C_w is the no-cache DT;
- B is the harness chunk budget at 35.599 MB/s.

**Formulations:**
- **F1:** max_w L_w, used by every held-out Q1/Q2 configuration, every H1′ and H2′ configuration, and by the phase-2 F1-label arms (the phase-1 Q3 labels used F4, see [F14](#F14));
- **F2a:** the top-4 mean;
- **F2b:** a squared hinge;
- **F3:** a capacity/eviction-coupled QKP, not implemented;
- **F4:** Track A's day-1 energy.

**Nested prefix.** The simulator's converged OPT cutoff admits only a prefix of the selection (0.72–0.89·W in harness_eval). Selections are therefore solved bottom-up at 8 nested levels f = 0.65 … 1.00 of B (harness_eval used 11 levels from 0.50).

**Solver families.** Ising: pt, eim, hlns, matrix-free SB on the QUBO surrogate Σ_w α_w(C_w − τ − (Dᵀx)_w)² + μ s·x, and mq (MindQuantum bSB/dSB/CAC on sub-QUBOs, or dwave/OpenJij SA; choice tuned). Classical: greedy, pgreedy, lp, milp (HiGHS), cpsat, scip and ls.

**Fairness.** Both families get the same number of Optuna trials and the same pinned cores 0–7.
**Why this priority:** every offline and label result below uses this formulation; it is the method, not a result.
Refs: [`changes/1_literature_review/explore/q2/RESULTS.md#L46-L125`](../../changes/1_literature_review/explore/q2/RESULTS.md#L46-L125), [`changes/1_literature_review/explore/q2/RESULTS.md#L289-L293`](../../changes/1_literature_review/explore/q2/RESULTS.md#L289-L293), [`changes/1_literature_review/harness_eval/RESULTS.md#L31`](../../changes/1_literature_review/harness_eval/RESULTS.md#L31), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L25-L29`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L25-L29), [`changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L12-L15`](../../changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L12-L15), [`changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L26-L30`](../../changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L26-L30), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L58`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L58), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L67-L71`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L67-L71)

<a id="F14"></a>
### F14 [P2] [INFRA] The phase-1 deployed (Q3) labels used an extended-Ising energy on day 1
E = A·LSE_γ(L(x)) + a DT blend + a trust region toward Baleen's labels, plus optional kNN feature couplings, under a native hard budget.
- It was solved by numba parallel tempering (16 replicas), started from Baleen's selection (not the LP start of the Q1/Q2 solvers).
- `q3form.py` reproduces the solver's energies exactly: Baleen start 24.5180 and solution 22.4457 on dev Region7 day 1.
- Finalists: P0 (pure soft peak), T2 (+ DT blend + trust region) and C2 (T2's energy over ~1.6k feature cells).
**Why this priority:** it is the method behind the Q3 labels; detail.
Refs: [`changes/1_literature_review/explore/q3/src/q3solve.py#L282-L286`](../../changes/1_literature_review/explore/q3/src/q3solve.py#L282-L286), [`changes/1_literature_review/explore/common/Q3_FORMULATION.md#L6-L56`](../../changes/1_literature_review/explore/common/Q3_FORMULATION.md#L6-L56)

<a id="F15"></a>
### F15 [P1] [DEV] Phase-1 harness test on sample 0: the offline gain is real, but distillation into the unchanged GBM keeps almost none of it
**Offline (OPT).** Every arm cut the simulated P100 by 5.5–8.0 points below Baleen's peak-blind OPT (R0):
- Region7 34.52 → 27.77 (R2);
- Region6 35.56 → 27.60;
- Ising arms 27.7–28.3, classical arms 27.6–28.3 (excluding the capacity-coupled C3/C3L at 28.9–29.6, [F16](#F16)).

**Deployed.**
- Every Region7 arm scored 40.06–40.85, against Baleen online 40.10 ± 0.18.
- The best Region6 arm, R2, scored 42.38 ± 0.95, still above RejectX at 42.32.
- Retention R = (ML-Baleen − ML-Peak)/(OPT-Baleen − OPT-Peak) was −0.04 (Region7) and +0.11 (Region6) for R2, and +0.01 for the best Ising arm C4.

The only deployed arm more than 2 SE below Baleen online was the *classical* R2 on Region6 (−0.87, beyond 2 × SE = 0.85), and it was not below RejectX. No Ising arm came close.

This is sample 0 only, i.e. the later dev instance. The run's operational deviations are listed in [F99](#F99).
**Why this priority:** it is the first evidence of the deployment gap that motivated scope v2; dev-only, so not a test result.
Refs: [`changes/1_literature_review/harness_eval/RESULTS.md#L200-L218`](../../changes/1_literature_review/harness_eval/RESULTS.md#L200-L218), [`changes/1_literature_review/harness_eval/RESULTS.md#L3-L10`](../../changes/1_literature_review/harness_eval/RESULTS.md#L3-L10), [`changes/1_literature_review/harness_eval/RESULTS.md#L220-L257`](../../changes/1_literature_review/harness_eval/RESULTS.md#L220-L257)

<a id="F16"></a>
### F16 [P2] [OFFLINE] Gate 0: the analytic window loads match the simulator, and peak-aware plans migrate; the evidence points to admissions overrunning the cache
**The analytic model matches.**
- C_w equals the simulator's per-window no-cache DT to within 6·10⁻¹¹ on all 997 windows.
- Baleen's own selection is modelled with r = 0.994 (Region7) and 0.985 (Region6).

**Peak-aware plans migrate.**
- The analytic argmax window moves in simulation: 288 → 660 (Region7) and 361 → 154 (Region6).
- The simulated peak exceeds the analytic one by 3.3–4.6 points.

**Mechanism evidence** (a correlation, which the source labels "mechanism evidence"):
- The analytic occupancy of Baleen's own admitted set exceeds the 3,002-chunk cache in about 40% of windows (maximum 1.5× and 2.0×).
- That occupancy correlates with the sim − analytic residual: r = 0.64 and 0.78.

**Capacity coupling (C3).** It raised fidelity (R² 0.990 and 0.979) but worsened the peak (simulated P100 28.9–29.6).
**Why this priority:** it explains why analytic peak gains shrink in simulation; mechanism detail.
Refs: [`changes/1_literature_review/harness_eval/RESULTS.md#L98-L114`](../../changes/1_literature_review/harness_eval/RESULTS.md#L98-L114), [`changes/1_literature_review/harness_eval/RESULTS.md#L200-L218`](../../changes/1_literature_review/harness_eval/RESULTS.md#L200-L218)

<a id="F17"></a>
### F17 [P2] [OFFLINE] Phase-1 harness solver attribution: inside the hybrids the classical sub-solvers did most of the work, and the one analytic Ising edge was EIM on Region7
Analytic peak, averaged over the 11 nested levels on sample 0.
- **Only one Ising arm beat the MILP polish (R2), and only on one trace.** C2 (EIM: hinge + ALM + replica exchange) did so on Region7 (24.165 vs 24.220). On Region6, R2 is best (22.611 vs C2 22.917).
- **Inside C1** (LP + peak-window LNS racing three sub-solvers), accepted moves came from the HiGHS sub-MILP 243 times, true-objective SA 118 times, and the sum-of-squares sub-QUBO SA twice.
- **Inside C5** (contested-subset QUBO), the explicit QUBO heuristics do not beat a HiGHS sub-MILP on the same subset: on Region6, sub-MILP 23.33 vs MindQuantum bSB 23.37.
- **In simulation** all LP-family and Ising arms fall within 27.6–28.3.

**Why this priority:** it is early evidence for the Ising ≈ classical pattern ([F70](#F70)); detail.
Refs: [`changes/1_literature_review/harness_eval/RESULTS.md#L162-L182`](../../changes/1_literature_review/harness_eval/RESULTS.md#L162-L182)

<a id="F103"></a>
### F103 [P2] [INFRA] Design levers harness_eval flagged for a team decision were never implemented
harness_eval listed these as needing a decision, and no later work package implemented them:
- **Simulator-in-the-loop reweighting of training.** Re-solve after up-weighting the simulator's worst windows, or calibrate C3's κ or a per-window savings haircut against simulated residuals. Gate 0 shows this targets the right mechanism (peak migration, [F16](#F16)), and the source calls it "the most direct fix for migration".
- **Peak-aware tail ordering** beyond the W prefix: not needed on the admit side, and a solve above W·(1+δ) would violate SCOPE §1.
- **Per-episode prefetch options:** the slot emits only an order and scores.
- **Candidate 3's occupancy model** needs team confirmation.
- **Samples 1–9** were not run.

**Why this priority:** it records the main untried idea against peak migration (see also §9).
Refs: [`changes/1_literature_review/harness_eval/RESULTS.md#L270-L276`](../../changes/1_literature_review/harness_eval/RESULTS.md#L270-L276)

## 4. Offline results: the min–max gain and the solver comparison

Offline (OPT mode), the min–max selection lowers the simulated peak by about 16% on Regions 5–7, and by less on Region4. Ising and classical solvers give the same simulated peak. The solver comparison (Q2 in phase 1, then H2′ at tight budgets) was pre-registered twice and failed twice. The Ising samplers were the best family only at one short budget each time.

<a id="F18"></a>
### F18 [P0] [TEST-PREREG] Q1 = YES: min–max selection beats Baleen's peak-blind oracle offline on 6/6 held-out instances
The held-out set was Region7/Region6 × samples 0.1–0.3, never used for tuning, at matched write rate. All 52 simulations matched (WR 35.26–35.95).
- **F1 + PT:** P100 27.06 vs Baleen's peak-blind OPT 32.28 (−5.21), on 6/6 instances.
- **F1 + EIM:** 26.95 (−5.33), on 6/6.

**Pass rule:** ≥ 5/6 instances and lower on average.

**Forking path.** The F1 formulation was chosen after a dev look ([F96](#F96)); F2b's dev selections were equally far below the oracle.

**Pre-registration caveat.** [`changes/1_literature_review/explore/PROTOCOL.md`](../../changes/1_literature_review/explore/PROTOCOL.md) says "Frozen: 2026-09-28, before any tuning". Its first git commit, however, is `be284a3` (2026-09-29 15:02), after the held-out runs ([F75](#F75)).
**Why this priority:** this is the project's headline positive result, the offline premise of everything after it.
Refs: [`changes/1_literature_review/explore/q2/RESULTS.md#L12-L20`](../../changes/1_literature_review/explore/q2/RESULTS.md#L12-L20), [`changes/1_literature_review/explore/q2/RESULTS.md#L259-L277`](../../changes/1_literature_review/explore/q2/RESULTS.md#L259-L277), [`changes/1_literature_review/explore/PROTOCOL.md#L3-L12`](../../changes/1_literature_review/explore/PROTOCOL.md#L3-L12), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt)

<a id="F19"></a>
### F19 [P1] [OFFLINE] The offline gain is a formulation effect, not a solver effect
Classical and Ising selections land on the same simulated peak at every stage:
- **Phase 1 (held-out).** The best classical selections simulate at 26.954, against PT 27.063 and EIM 26.951.
- **harness_eval.** Ising arms 27.7–28.3 vs classical 27.6–28.3 (excluding the capacity-coupled C3/C3L at 28.9–29.6).
- **WP1 (39 instances).** PT − CP-SAT = −0.18 on average, with PT lower on 18/39. Taking the best of the three methods per instance would give 14.6%.

Selections with near-identical analytic objectives can still differ by up to ~1 P100 point in simulation (peak migration), with no family pattern.
**Why this priority:** it determines what can be credited to Ising (nothing offline beyond parity); a central supporting fact.
Refs: [`changes/1_literature_review/harness_eval/RESULTS.md#L200-L218`](../../changes/1_literature_review/harness_eval/RESULTS.md#L200-L218), [`changes/1_literature_review/explore/q2/RESULTS.md#L18-L24`](../../changes/1_literature_review/explore/q2/RESULTS.md#L18-L24), [`changes/1_literature_review/explore/q2/RESULTS.md#L271-L277`](../../changes/1_literature_review/explore/q2/RESULTS.md#L271-L277), [`changes/1_literature_review/harness_eval/RESULTS.md#L4`](../../changes/1_literature_review/harness_eval/RESULTS.md#L4), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L91-L95`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L91-L95)

<a id="F20"></a>
### F20 [P0] [NEGATIVE-TEST] Q2 = NO: on the same F1 formulation the Ising samplers beat the best classical solver only at the 10 s budget (PT 22.524 vs 22.569 at 10 s; 22.508 vs 22.415 at 60 s)
**PT vs the best classical method per (instance, budget):**
- ≤ on 5/6 instances at 10 s, 2/6 at 60 s and 1/6 at 300 s. The rule needs ≥ 5/6 at ≥ 2 of 3 budgets.
- Means 22.524 vs 22.569 (10 s), 22.508 vs 22.415 (60 s) and 22.503 vs 22.313 (300 s).
- Over all 18 pairs: 22.511 vs 22.432.

**EIM:** 4/6, 1/6 and 1/6.

**Simulation clause.** PT fails it (27.063 > 26.954). EIM passes by 0.003, which is far inside the seed spread.

**Mechanism.** The nested F1 problem has one hard level.
- The samplers reach near-optimal loads in 1–2 s.
- CP-SAT's LP-guided search wins once level 1 gets 13 s (60 s budget) or 67 s (300 s budget).
- PT's mean improves by only 0.005 from 60 s to 300 s, against CP-SAT's 0.105.

Pre-registration caveat as in [F18](#F18).
**Why this priority:** it is the decisive negative on "Ising beats classical solvers" for the proposal's H2-type question.
Refs: [`changes/1_literature_review/explore/q2/RESULTS.md#L12-L31`](../../changes/1_literature_review/explore/q2/RESULTS.md#L12-L31), [`changes/1_literature_review/explore/q2/RESULTS.md#L243-L249`](../../changes/1_literature_review/explore/q2/RESULTS.md#L243-L249), [`changes/1_literature_review/explore/q2/RESULTS.md#L297-L315`](../../changes/1_literature_review/explore/q2/RESULTS.md#L297-L315)

<a id="F21"></a>
### F21 [P1] [DEV] The proposal's own Ising design (a sum-of-squares QUBO surrogate solved by simulated bifurcation) was the weakest Ising solver in phase-1 dev tuning and in WP5; the "Ising" finalists are LP-started replica-exchange samplers on the true objective
**What the proposal planned.** H2 assumed a sum-of-squares penalty on window loads solved by an Ising solver, with simulated bifurcation (GPU-accelerated) as the primary Ising machine.

**How that design performed:**
- **Phase-1 dev tuning** (F1, % vs peak-aware greedy). SB reached −13.217 at 10 s, last among the Ising arms (PT −15.010, EIM −14.973, HLNS −14.066, MQ −13.891).
- **WP5 finalist rule.** Lower V is better, and the two lowest V become finalists. SB's V = −11.64% is the worst (highest) of the four Ising solvers (PT −14.58%, EIM −14.14%, MQ −12.50%).
- **harness_eval is the exception.** C4 (matrix-free SB on the SoS QUBO) scored an analytic 24.343 / 23.044 (Region7 / Region6).
  - That is behind EIM C2 (24.165 / 22.917) and the MILP polish (24.220 / 22.611), but ahead of the contested-subset QUBO C5 (24.376 / 23.373).
  - In simulation C4 was one of the two best Ising arms (27.97 / 27.87), and the source calls it "the best Ising arm" for retention (+0.01).

**What the finalists are.**
- PT and EIM are replica-exchange (parallel-tempering) samplers on the LSE-smoothed true peak, with a QUBO budget penalty (PT) or a native hinge plus ALM (EIM).
- **Phase-1 Q1/Q2.** Both finalists start from the classical LP + round + repair solution ("16 replicas, LP start"). So do harness_eval's EIM-style arm C2 (24 replicas, "starts from the repaired LP") and every deployed F1PT/F1EIM label set (WP2, WP3, WP9, the union).
- **Not every "Ising" label set.** The Q3 designs (P0/T2/C2, [F14](#F14)), used in phase-1 Q3 and again in WP2's deployed dev arms D:P0 and D:T2, come from a PT started at Baleen's selection with a native hard budget. Track C's anchored (ANC) designs start from Baleen's set, and its student (STU) designs from the previous round's labels.
- **H2′.** The start was a tuned choice: LP at 3 s and 10 s, but the peak-aware greedy at 1 s, for both PT and EIM.
- [F24](#F24) quantifies what the sampler adds to the LP start.
- They sit inside the protocol's Ising/QUBO family ("parallel tempering … on a QUBO/Ising energy"), but they are CPU samplers, not physical or GPU Ising machines ([F90](#F90)).

**Why this priority:** it fixes what "Ising" means in every result in this story, and shows that the proposal's surrogate route under-performed in the solver comparisons.
Refs: [`changes/1_literature_review/explore/q2/RESULTS.md#L165-L167`](../../changes/1_literature_review/explore/q2/RESULTS.md#L165-L167), [`changes/1_literature_review/harness_eval/RESULTS.md#L42`](../../changes/1_literature_review/harness_eval/RESULTS.md#L42), [`changes/2_deployable_peak/wp2_deployed/src/labels.py#L1-L4`](../../changes/2_deployable_peak/wp2_deployed/src/labels.py#L1-L4), [`changes/1_literature_review/explore/q3/src/q3solve.py#L282-L286`](../../changes/1_literature_review/explore/q3/src/q3solve.py#L282-L286), [`changes/2_deployable_peak/wp8_trackC/src/labels_c.py#L1-L11`](../../changes/2_deployable_peak/wp8_trackC/src/labels_c.py#L1-L11), [`changes/2_deployable_peak/wp8_trackC/src/labels_c.py#L126-L131`](../../changes/2_deployable_peak/wp8_trackC/src/labels_c.py#L126-L131), [`changes/1_literature_review/harness_eval/RESULTS.md#L42`](../../changes/1_literature_review/harness_eval/RESULTS.md#L42), [`changes/2_deployable_peak/wp5_ising/results/plan_H2test.json`](../../changes/2_deployable_peak/wp5_ising/results/plan_H2test.json), [`documents/proposal_docx_compose/proposal.js#L200`](../../documents/proposal_docx_compose/proposal.js#L200), [`documents/proposal_docx_compose/proposal.js#L244`](../../documents/proposal_docx_compose/proposal.js#L244), [`changes/1_literature_review/explore/q2/RESULTS.md#L127-L143`](../../changes/1_literature_review/explore/q2/RESULTS.md#L127-L143), [`changes/1_literature_review/explore/q2/RESULTS.md#L163-L167`](../../changes/1_literature_review/explore/q2/RESULTS.md#L163-L167), [`changes/1_literature_review/harness_eval/RESULTS.md#L162-L168`](../../changes/1_literature_review/harness_eval/RESULTS.md#L162-L168), [`changes/1_literature_review/harness_eval/RESULTS.md#L184-L197`](../../changes/1_literature_review/harness_eval/RESULTS.md#L184-L197), [`changes/1_literature_review/harness_eval/RESULTS.md#L250`](../../changes/1_literature_review/harness_eval/RESULTS.md#L250), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L187-L196`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L187-L196), [`changes/1_literature_review/explore/PROTOCOL.md#L37`](../../changes/1_literature_review/explore/PROTOCOL.md#L37)

<a id="F22"></a>
### F22 [P3] [DEV] Q2 post hoc: the 10 s Ising win and the 60 s CP-SAT win do not depend on the nested time split
On dev, giving level 1 a weight of 6 (46% of T):
- PT 23.174 vs CP-SAT 23.355 at 10 s;
- PT 23.163 vs CP-SAT 23.048 at 60 s.

The ordering is the same as with the default split (23.183 vs 23.321; 23.160 vs 23.080). This is post hoc, dev-only, and not part of any verdict.
**Why this priority:** it rules out an artefact of the driver; minor.
Refs: [`changes/1_literature_review/explore/q2/RESULTS.md#L317-L334`](../../changes/1_literature_review/explore/q2/RESULTS.md#L317-L334)

<a id="F23"></a>
### F23 [P3] [DEV] Phase-1 dev on the squared-hinge F2b: the classical local search led at 10 s, so the held-out solver comparison was run on F1
**F2b at 10 s on dev** (10 trials each, % vs peak-aware greedy):
- classical LS −0.143 (best);
- PT −0.134;
- EIM −0.104;
- SB and SCIP never improved on their greedy start within 10 s.

**Why F1.** F1 went to held-out because the Ising samplers led there at 10 s: PT −15.010 and EIM −14.973, vs LS −14.901 and CP-SAT −14.566. F2b's 60 s stage was not run.

**Why this priority:** it records how the formulation for Q2 was chosen; minor.
Refs: [`changes/1_literature_review/explore/q2/RESULTS.md#L127-L163`](../../changes/1_literature_review/explore/q2/RESULTS.md#L127-L163)

<a id="F24"></a>
### F24 [P1] [OFFLINE] The phase-1 "Ising" arms are a classical LP start polished by a sampler: LP + round + repair already reaches ≈94% of the greedy → PT analytic reduction, and the sampler supplies the rest
**Phase 1 (held-out, 10 s, mean analytic objective over 6 instances).**
- Baleen-order greedy 31.816 → LP + round + repair 23.039 → PT 22.524.
- The classical LP start therefore covers 94.5% of the greedy → PT reduction (recomputed in Appendix D). The sampler adds the remaining 0.515.
- This uses the `lp` method's row as a proxy for PT's own start, which was not logged separately; the source makes the same equivalence.
- The source's own wording: "Relative to that classical start (LP + round + repair …), the samplers contribute the whole improvement to 22.50-22.55".

**Move shares.**
- Both phase-1 finalists start from the LP ("16 replicas, LP start").
- After the start, the replica-exchange sampler made 99.40% (PT, 10 s) to 99.9994% (EIM, 300 s) of all accepted moves; the rest were shared-repair operations.

**Phase 2.**
- Every deployed F1PT label set was solved by the same LP-started PT 10 s configuration.
- In H2′ the warm start was a tuned choice from {LP rounding + repair, peak-aware greedy}, available to both families. PT and EIM chose LP at 3 s and 10 s, and the greedy start at 1 s.

**Run bookkeeping.**
- All 288 held-out runs finished.
- One HiGHS MILP run at the 10 s budget exceeded the over-budget limit of 1.05 T + 0.5 s (11.03 s); no verdict depends on it.
- The guard discarded 5 of HiGHS's 144 held-out level solutions that came back after their deadline.

**Why this priority:** it bounds what the Ising sampler can be credited with: the improvement over its classical start, not the gain over Baleen.
Refs: [`changes/1_literature_review/explore/q2/trials.csv`](../../changes/1_literature_review/explore/q2/trials.csv), [`changes/2_deployable_peak/wp5_ising/results/plan_H2test.json`](../../changes/2_deployable_peak/wp5_ising/results/plan_H2test.json), [`changes/1_literature_review/explore/q2/RESULTS.md#L163-L167`](../../changes/1_literature_review/explore/q2/RESULTS.md#L163-L167), [`changes/1_literature_review/explore/q2/RESULTS.md#L196-L218`](../../changes/1_literature_review/explore/q2/RESULTS.md#L196-L218), [`changes/1_literature_review/explore/q2/RESULTS.md#L254-L257`](../../changes/1_literature_review/explore/q2/RESULTS.md#L254-L257), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L58`](../../changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L58), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L67-L71`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L67-L71)

<a id="F25"></a>
### F25 [P0] [OFFLINE] H1′ breadth: on 39 instances in four regions, peak-aware selection beats the peak-blind oracle on 36–37 of them by −13.0% to −13.7% on average; 30/30 and 13.0–17.7% per region on Regions 5–7
Phase-1 frozen 300 s configurations (no tuning), Regions 4–7 × samples 0–0.9. Region4 s0.1 has no OPT-AP row, which leaves 39 instances. 156/156 simulations matched.

| Method | Wins vs R0 | Mean P100 reduction |
|---|---|---|
| LP + repair | 36/39 | 13.03% |
| CP-SAT | 36/39 | 13.15% |
| PT | 37/39 | 13.69% |

- **Regions 5–7:** 30/30 for all three methods (15.6 / 16.2 / 16.2%).
- **Region4:** 6/9, 6/9, 7/9 with only 4.6 / 3.0 / 5.4%.
- **H1′ criterion** ([`changes/2_deployable_peak/PLAN.md#L19`](../../changes/2_deployable_peak/PLAN.md#L19): ≥ 80% wins and mean ≥ 10%, judged over all instances): passed by all three methods.
- **Headroom gate** ([`changes/2_deployable_peak/PLAN.md#L105`](../../changes/2_deployable_peak/PLAN.md#L105): mean reduction ≥ 10%): met overall and on Regions 5, 6, 7 separately; not met on Region4 alone. Region4 also falls short of 80% wins (6/9, 6/9, 7/9).

**Secondary metrics** (mean reduction vs R0):
- P99: 8.6% (LP), 9.2% (CP-SAT), 9.2% (PT). That is below the 10% bar used for P100; the P99 gain is smaller than the P100 gain.
- Top-5 window mean: 10.8%, 11.2%, 11.3%.

**Not a solver advantage.** PT has the highest mean reduction, but it is lower than CP-SAT on only 18/39 instances ([F19](#F19)).

**Instance reuse.** These offline OPT instances include the later H2′/H3′ test samples (0.4–0.6), the H4 and T2 pools, and the reserve ([F92](#F92), [F93](#F93)).

Recomputed from `wp1_table.csv` (Appendix D).
**Why this priority:** it is the robust, broad offline result; the strongest positive evidence in the project.
Refs: [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L3-L38`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L3-L38), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L87-L95`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L87-L95), [`changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`](../../changes/2_deployable_peak/wp1_offline/results/wp1_table.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/2_deployable_peak/PLAN.md#L19`](../../changes/2_deployable_peak/PLAN.md#L19), [`changes/2_deployable_peak/PLAN.md#L105`](../../changes/2_deployable_peak/PLAN.md#L105), [`./RESEARCH.md#L38`](../../RESEARCH.md#L38)

<a id="F26"></a>
### F26 [P1] [OFFLINE] Peak migration is the rule offline: the planned peak window almost never is the simulated one
- **The window moves.** The simulated peak window differs from R0's on 30/39 (LP), 34/39 (CP-SAT) and 33/39 (PT) instances.
- **The plan rarely matches.** The planned (analytic) peak window of the admitted prefix coincides with the simulated one (±10 min) on only 6/39, 9/39 and 6/39.
- **The plan is optimistic.** Planned peaks are below the simulated ones by 4.4–5.2 points on average (range −2.5 to +14.7).
- **The peak hour moves.** R0 peaks cluster at 13–14 h; PT's peaks spread over 0–3 h and 13–15 h.
**Why this priority:** it is the main offline mechanism and a warning that the analytic objective is a proxy.
Refs: [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L101-L108`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L101-L108)

<a id="F27"></a>
### F27 [P1] [OFFLINE] Region4 has little peak headroom; its peaks are short bursts the oracle already absorbs, and the losses come from migration
Region4 peaks are short bursts:
- window 291 = d2 00:30 on samples 0, 0.2 and 0.5, with no-cache load C_w = 84–182% util;
- on the other samples, R0 peaks at d3 03:20 or 03:30, d5 14:10, or d6 00:50.

The peak-aware solvers mostly tie R0 or win a few points. The exceptions are losses where the simulated peak migrated:
- CP-SAT −6.9% (s0.9) and −4.8% (s0.8);
- PT −4.1% (s0.8);
- LP −1.6% (s0.8).

**Why this priority:** it bounds the offline claim by region; it matters later because Region4 was the auto-research T2 pool.
Refs: [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L11-L15`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L11-L15), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L47-L55`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L47-L55), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L96-L100`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L96-L100)

<a id="F101"></a>
### F101 [P3] [OFFLINE] WP1's peak-blind oracle R0 reproduces the authors' OPT-AP rows closely, so the H1′ comparator is the paper's own oracle
- **Agreement.** Across the 39 instances, R0 − the authors' OPT-AP P100 is −0.55 on average (mean |diff| 1.02).
- **Largest gap.** It is 4.81, on Region6 s0.9 (R0 33.62 vs the authors' 38.44). The source's summary line says "max 4.81 on Region4 s0.3", but its own per-instance table gives Region4 s0.3 a gap of 4.01 (42.34 vs 46.35); recomputed.
- **Why they differ.** Our R0 is converged to 35.599 MB/s ± 1%, while the authors' rows sit at 34.0–35.8 MB/s.
- **Instance identity.** Rebuilt Region7 s0.1 is identical to the phase-1 instance up to episode permutation.

**Why this priority:** pipeline fidelity for the strongest positive result ([F25](#F25)); minor.
Refs: [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L17-L38`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L17-L38), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L49`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L49), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L75`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L75), [`changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`](../../changes/2_deployable_peak/wp1_offline/results/wp1_table.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

<a id="F28"></a>
### F28 [P0] [NEGATIVE-TEST] H2′ = NO: at re-solve budgets of 1, 3 and 10 s the tuned Ising solvers fail the pre-registered criteria (better only at 3 s; PT 22.7336 vs best classical 22.7166 over all 18 cells)
**PT vs the best classical method per cell:**
- ≤ on 1/6 instances at 1 s (a floored tie), 6/6 at 3 s and 4/6 at 10 s. The count criterion (≥ 5/6 at ≥ 2 budgets) is met at one budget only.
- Average over the 18 pairs: 22.7336 vs 22.7166. FAIL.

**EIM:** 0/6, 5/6 and 3/6; average 22.8413. FAIL.

**Which method was best where:**
- 1 s: the classical true-objective local search, on every test instance;
- 3 s: the replica-exchange samplers;
- 10 s: PT, LS and CP-SAT within ±0.3%.

**Run hygiene.** 324/324 runs ok, 0 over budget; the foreign-load audit had zero entries during the test.

**Pre-registration.** `PROTOCOL_v2_H2.md` and the plan were committed as `fd54e76` (2026-10-03 01:13) before the test runs (01:24:38 to 01:45). Dev had predicted this failure ([F29](#F29)).
**Why this priority:** the decisive pre-registered negative on the Ising-solver question at the budgets that motivated it.
Refs: [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L1-L24`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L1-L24), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L104-L105`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L104-L105), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L167-L173`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L167-L173), [`changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L69-L78`](../../changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L69-L78), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt)

<a id="F102"></a>
### F102 [P2] [TEST-POSTHOC] H2′ mechanism (pre-declared per-level report, no pass/fail): at 1 s the first nested level decides, and the exact solvers cannot get past their LP rounding there
- **Level 1 at 1 s.** Level 1 (65% of B, given 2/9 of T) decides the 1 s result.
  - LP, MILP and CP-SAT stay at the LP rounding (level-1 mean 30.8).
  - PT and EIM reach 23.5–23.8, and LS 23.4.
  - LS is also best on every later level.
- **3 s and 10 s.** PT's level-1 sets (22.97 / 22.86) are the best of any method. At the full-budget level, LS is best at 3 s (22.37 vs PT 22.39), and PT, EIM, CP-SAT and LS are within 0.01 at 10 s.
- **Early returns.** MILP and CP-SAT return before the budget, because they solve the small later levels exactly and the split only carries unused time forward.

**Why this priority:** it explains the budget-dependent ranking behind the H2′ verdict; mechanism detail.
Refs: [`changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L79-L80`](../../changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L79-L80), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L69-L102`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L69-L102), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L135-L136`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L135-L136)

<a id="F29"></a>
### F29 [P2] [DEV] H2′ dev tuning: equal trials for both families, and the ranking flips with the budget
Each of 8 tunable solvers got 12 Optuna trials per budget (2,304 tuning runs). Dev-evaluation means:

| Budget | Result |
|---|---|
| 1 s | LS best: 23.03 vs PT 23.25, EIM 23.54 |
| 3 s | PT 22.73 and EIM 22.77 vs LS 22.87 |
| 10 s | near tie: PT 22.685, LS 22.703, EIM 22.702, CP-SAT 22.81 |

**Finalists.** PT and EIM, by a rule pre-registered at 14:55 on Oct 1: V = −14.58% and −14.14%, vs MQ −12.50% and SB −11.64%.

**Dev reading.** It predicted H2′ = FAIL. The pre-declared allocate-to-hard-level split (w1 = 6) changed no dev conclusion and was not run on test.
**Why this priority:** it shows the test was set up fairly and its outcome anticipated; dev detail.
Refs: [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L6-L17`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L6-L17), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L187-L199`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L187-L199), [`changes/2_deployable_peak/wp5_ising/PROGRESS.md#L27`](../../changes/2_deployable_peak/wp5_ising/PROGRESS.md#L27)

<a id="F30"></a>
### F30 [P2] [TEST-POSTHOC] Rolling re-solve at 1 s (pre-declared secondary, no pass/fail): the exact classical solvers win on the small window instances
Rolling re-solve (6-h windows, 3-h step) on the 6 test instances; seed 0 only. Stitched full-trace peak:

| Method | Peak |
|---|---|
| CP-SAT | 26.440 |
| MILP | 26.445 |
| LP | 26.708 |
| LS | 26.740 |
| EIM | 26.860 |
| PT | 26.903 |
| Best classical per instance | 26.426 |

The peak-aware greedy (29.726) and greedy (33.791) rows are omitted.
- PT and EIM are ≤ the best classical method on 0/6 instances.
- Rolling costs about 4 util points against the one-shot full-trace solve at the same budget.
- **Caveat.** A short editor-process burst overlapped the first windows of PT on Region7 s0.4.

**On dev** (1 s and 3 s) the same held, so the Ising 3 s edge does not carry over to periodic re-labelling. Two qualifications:
- The test itself ran at 1 s only.
- On dev, the 3-s rolling comparison originally covered PT, EIM and LS only. MILP, CP-SAT and LP were added after the 1-s rolling result showed the exact solvers winning ("fill-in analysis, not part of any verdict").

**Why this priority:** it addresses the stated motivation for tight budgets (periodic re-labelling) and answers it negatively; secondary.
Refs: [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L138-L165`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L138-L165), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L174-L176`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L174-L176), [`changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L82-L86`](../../changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L82-L86), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L18-L23`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L18-L23), [`changes/2_deployable_peak/wp5_ising/PROGRESS.md#L83-L85`](../../changes/2_deployable_peak/wp5_ising/PROGRESS.md#L83-L85)

<a id="F31"></a>
### F31 [P1] [OFFLINE] Scaling (contribution S): matrix-free SB runs real unions of up to 125541 QUBO variables in at most 214 MB, where the dense SB package runs out of memory
**Matrix-free SB** (32 agents):
- 0.3–1.9 ms per step and +12–86 MB on every real day-1 and full-trace instance (up to 32k variables);
- 4.5–12.7 ms per step and +111–214 MB on real 0.2–0.4% unions (62k–126k variables). The matrix-free SB and PT memory figures are *extra* memory above the loaded instance (~355–410 MB); the dense package's failure figures are absolute RSS.

**The dense simulated-bifurcation package:**
- On the full traces: 1.5–3.6 s per step and 12–22 GB RSS, i.e. ~1,400–3,600× slower per step.
- It fails out of memory at the 64 GB cap on all three unions. The 62515-variable union died at 53.8 GB RSS.

**PT (sparse):** 5–31 M proposals/s with at most 165 MB.

**What was measured.** The level-1 QUBO surrogate (pure solver cost, no repair loop).

**What this is worth.**
- The solver that scales is matrix-free SB. Its solution quality was last of the five Ising solvers in phase-1 dev tuning, and the worst of four by the WP5 rule ([F21](#F21)).
- It is in no phase-2 finalist or deployed test configuration. In phase-1 harness_eval, however, C4 (matrix-free SB on the SoS QUBO) was deployed on dev (sample 0): it tied Baleen (Region7 40.07, Region6 43.20) with retention +0.01.
- The sparse PT used everywhere also stays under 165 MB.
- So this is a scalability result for matrix-free SB, not a contribution of Ising solving to PeakBaleen's peak.

**Wording discrepancy.** [`./RESEARCH.md`](../../RESEARCH.md) says the dense package fails "beyond ≈70k variables". That is the projected limit on the 123-GB machine; the observed failure was at 62.5k variables under the 64 GB cap.
**Why this priority:** this is the one reported Ising contribution that stands (engineering scalability); no pass/fail was attached.
Refs: [`changes/1_literature_review/explore/q2/RESULTS.md#L133-L139`](../../changes/1_literature_review/explore/q2/RESULTS.md#L133-L139), [`changes/1_literature_review/harness_eval/RESULTS.md#L197-L198`](../../changes/1_literature_review/harness_eval/RESULTS.md#L197-L198), [`changes/1_literature_review/harness_eval/RESULTS.md#L231-L233`](../../changes/1_literature_review/harness_eval/RESULTS.md#L231-L233), [`changes/1_literature_review/harness_eval/RESULTS.md#L250`](../../changes/1_literature_review/harness_eval/RESULTS.md#L250), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L27-L31`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L27-L31), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L333-L392`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L333-L392), [`changes/2_deployable_peak/wp5_ising/results/scaling_summary.md`](../../changes/2_deployable_peak/wp5_ising/results/scaling_summary.md), [`./RESEARCH.md#L41`](../../RESEARCH.md#L41)

<a id="F32"></a>
### F32 [P2] [DEV] Choosing the label solver: WP5 recommended EIM, the deployed tests used the phase-1 PT configuration, and the deployed F1 label sets of PT and CP-SAT have the same day-1 peak
**WP5 recommended EIM** for the WP2 labels as the best *Ising* day-1 objective. Dev simulated P100 was 27.32 for EIM vs 27.33 for PT, and the source adds that all peak-aware selections simulate within ~0.4 P100 of each other.

**Day-1 (label-size) instances at 10 s.** These are the WP5-tuned configurations, with an 8-level nested objective, mean of 8. They are not the configuration that produced the deployed labels:

| Solver | Family | Objective |
|---|---|---|
| CP-SAT | classical | 22.2579 |
| LS | classical | 22.2677 |
| EIM | Ising | 22.3257 |
| PT | Ising | 22.6071 |

- The WP5-tuned PT is the worst of the four: its 10-s configuration, tuned on the 7× larger full traces, is worse on day 1 than its own 3-s one.
- The deployed labels instead used the *phase-1* PT 10 s configuration at a single level f = 1. At that setting the seed-1 day-1 label peak of F1PT equals F1CPSAT's (21.5; F1EIM 21.6), as seed-1 means over 8 instances rounded to 0.1.
- On dev full traces, LS 10 s gives the best offline simulated P100 among the 8-instance rows (27.067).

**What was used.**
- WP2 ran both F1PT and F1EIM label sets, and the finalists used F1PT.
- PROTOCOL_v2_H3 fixed the label solver to the phase-1 LP-started PT 10 s configuration, "which is exactly what dev used", noting that H2′ had failed.
- The WP2 label solves ran on cores 8–11 and 20–23, or 0–23 while `TIMING_IDLE` existed, never under the exclusive timing lock ([F100](#F100)).

**Why this priority:** it explains why "Ising labels" means the phase-1 PT configuration in every deployed test; detail.
Refs: [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L71-L80`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L71-L80), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L24-L26`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L24-L26), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L203-L249`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L203-L249), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L25`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L25), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L66-L69`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L66-L69), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L257`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L257), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L67-L76`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L67-L76)

## 5. Deployment: from Ising labels to the load-adaptive threshold

Deployed means:
1. the labels train Baleen's GBMs on day 1;
2. the simulator runs `--ap mlnew` on the remaining days;
3. the admission threshold is converged to the matched write rate;
4. every configuration gets ≥ 3 retrains.

The sequence was:
- **Phase 1 (Q3):** Ising labels with frozen features.
- **Scope v2:** add a causal `load` feature and the learnability gate.
- **WP2:** a 2×2 on dev, plus the load-adaptive threshold α.
- **WP3:** the H3′ test.
- **Track C:** deployment-aware Ising labels, dev only.
- **WP9:** the H4 test on Region5.
- **WP10:** an Ising-fitted threshold table, tested on Region1 (H5).
- **3_autoresearch:** an unattended search with two test spends.

## 5.1 Phase 1 (Q3): Ising labels into Baleen's unchanged GBM

<a id="F33"></a>
### F33 [P0] [NEGATIVE-TEST] Q3 = NO: Ising-family peak labels distilled into Baleen's unchanged GBM lose to Baleen on held-out instances (2/6 wins each; −0.41 to −1.07)
Three finalists, held-out Region7/Region6 × samples 0.1–0.3, 3 retrains each (only 2 matched for T2 on Region7 s0.2), matched WR:

| Finalist | Wins vs Baleen online (need ≥ 4/6) | Mean improvement | 2 SE |
|---|---|---|---|
| P0 | 2/6 | −0.41 | 0.56 |
| T2 | 2/6 | −1.07 | 0.85 |
| C2 | 2/6 | −0.57 | 0.96 |

- All three are below RejectX 39.05 and CoinFlip 44.69, but so is Baleen (37.55), so that criterion does not discriminate.
- **Dev looked positive, held-out reversed it.** On dev the finalists were 0.74–1.17 points below Baleen on Region7.
- **Retrain swings are large.** For example T2 Region7 s0.1: 36.05 / 42.69 / 36.42.

Pre-registration caveat as in [F18](#F18).
**Why this priority:** this is the first decisive deployment negative and the reason scope v2 exists.
Refs: [`changes/1_literature_review/explore/q3/RESULTS.md#L6-L23`](../../changes/1_literature_review/explore/q3/RESULTS.md#L6-L23), [`changes/1_literature_review/explore/q3/RESULTS.md#L196-L207`](../../changes/1_literature_review/explore/q3/RESULTS.md#L196-L207), [`changes/1_literature_review/explore/PROTOCOL.md#L20-L23`](../../changes/1_literature_review/explore/PROTOCOL.md#L20-L23)

<a id="F34"></a>
### F34 [P1] [DEV] Q3 mechanism: the Ising labels changed first-access admission, not peak targeting
**How the labels act.**
- An episode with a single access saves nothing, so the peak energy is indifferent to it. The stochastic PT leaves many such zero-value episodes selected: 44% of P0's Region7 labels, 26% of T2's, 10% of T5's.
- Each one is a positive first-access row. The trained GBM then admits new episodes at their first access far more often: on Region7, 6% → 15–28%.

**Evidence on dev.**
- Across 13 matched Region7 dev trials, corr(first-access admission, P100) = −0.79.
- Ablations (one retrain each): Baleen control 40.18; T5 39.26; T5 with its zero-value additions removed 39.90. JUNK10, a non-Ising control that swaps random zero-value episodes into Baleen's labels, gives 39.51. So about three quarters of T5's gain does not need a solver.
- Region6 barely moves (dev effects within −0.9..+0.1).

**Why this priority:** it is the mechanism that recurs on Region7 through every later phase ([F72](#F72)).
Refs: [`changes/1_literature_review/explore/q3/RESULTS.md#L236-L259`](../../changes/1_literature_review/explore/q3/RESULTS.md#L236-L259)

<a id="F35"></a>
### F35 [P1] [TEST-POSTHOC] Q3 held-out: on 3/6 instances P100 is set by rare scan-like windows, and relabelling moves those decisions in either direction
**What sets the peak.** On Region7 s0.3, Region6 s0.1 and Region6 s0.2, the peak lies in scan-like windows: 18–42% of the window's accesses end beyond 8 MB (the range of the report's table over all four label sets; its text says 25–42%). The fraction of those accesses a model admits varies with the labels and the retrain: Baleen 0.20–0.42, relabelled models 0.13–0.44 over all six instances (0.13–0.41 on the three scan instances).

**What carries over.** The first-access shift persists on held-out (Region7 8–11% → 14–36%), and Region7's mean load drops, but P100 does not follow the mean.

**Status.** Post-hoc analysis; the configurations were frozen before the held-out run.
**Why this priority:** it is the first sighting of the scan-vs-burst brittleness that later decided H3′ and X1 on Region5.
Refs: [`changes/1_literature_review/explore/q3/RESULTS.md#L261-L299`](../../changes/1_literature_review/explore/q3/RESULTS.md#L261-L299)

## 5.2 Scope v2: the causal load feature and the learnability gate

<a id="F36"></a>
### F36 [P1] [INFRA] The scope-v2 overlay passes CP1: bit-exact default equivalence and exact train/serve parity of `load`
**G1 (Region7/Region6 s0):**
- RejectX/CoinFlip frozen vs overlay are bit-identical on all 425 result keys (except wall-clock and RAM) and every per-window series (except `realtime_elapsed`).
- Pinned Baleen training is identical in rows, labels and all 5 model files. The frozen and overlay end-to-end pipelines give the same P100 on both code bases: 40.130989380934864 (Region7) and 43.26696451693124 (Region6).
- Unpinned runs differ only in the ways frozen-vs-frozen also differs: on Region6, 8 label flips vs 16 between two frozen runs.

**Parity.** All 79,497 `load` values on 26,499 training accesses equal the simulator's values exactly (max abs diff 0).

**Patch.** `PATCH.diff`: 9 files, +217/−6 lines per CP1, which equals the number of non-blank added lines. Counting every added line, as git's numstat does, gives +256/−6 (recomputed, Appendix D).
**Why this priority:** it is the gate that makes every scope-v2 deployed result attributable to the intended change only.
Refs: [`changes/2_deployable_peak/wp0_overlay/PATCH.diff`](../../changes/2_deployable_peak/wp0_overlay/PATCH.diff), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/2_deployable_peak/wp0_overlay/CP1.md#L5-L17`](../../changes/2_deployable_peak/wp0_overlay/CP1.md#L5-L17), [`changes/2_deployable_peak/wp0_overlay/CP1.md#L57-L98`](../../changes/2_deployable_peak/wp0_overlay/CP1.md#L57-L98), [`changes/2_deployable_peak/wp0_overlay/CP1.md#L100-L109`](../../changes/2_deployable_peak/wp0_overlay/CP1.md#L100-L109)

<a id="F37"></a>
### F37 [P1] [DEV] Learnability gate PASSES: given `load`, the GBM fits the F1 (min–max) peak-aware labels much better, PT- or CP-SAT-solved alike, and Baleen's own labels not at all
Net validation-logloss gain from `load`, after subtracting a shuffled-load control, over 8 dev instances:

| Labels | Net gain | Instances positive |
|---|---|---|
| F1PT | 0.041 ± 0.006 | 8/8 |
| F1CPSAT | 0.042 ± 0.006 | 8/8 |
| F1EIM | 0.038 ± 0.006 | 8/8 |
| P0 | 0.026 ± 0.005 | 8/8 |
| T2 | 0.019 ± 0.003 | 8/8 |
| C2 | 0.003 ± 0.002 | (fails) |
| Baleen | 0.001 ± 0.001 | |

- The criterion was fixed in the progress log at 16:35, before reading.
- A time split (first 70% → last 30% of day 1) is positive on every Region7 instance but negative on Region6 s0.1 and s0.3.

**Why this priority:** it is the stated precondition for the scope-v2 hypothesis; it passed, so the later failure is not "the signal is unlearnable".
Refs: [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L96-L112`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L96-L112), [`changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L23`](../../changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L23)

## 5.3 WP2: the deployed 2×2 on dev and the finalists X1/X2

<a id="F38"></a>
### F38 [P1] [DEV] The plain 2×2 hypothesis (Ising labels + `load`, arm D) does not survive confirmation on dev
With 3 retrains on 8 dev instances:
- D:F1PT scores 38.37, vs A 38.50 and B 38.44 (finalist score S = −0.142);
- D:F1EIM scores 38.46 (S = −0.238).

**The interaction is positive but about 1 SE.** `load` helps peak-aware labels more than Baleen's: +0.44 and +0.63 vs +0.06. The interaction is +0.38 ± 0.61 (F1PT) and +0.57 ± 0.49 (F1EIM).

**Without `load` the peak-aware labels are worse than Baleen's:** C:F1PT 38.81, C:F1EIM 39.09.

**Arm A reproduces phase 1:** mean |diff| 0.16.

**Consequence for the plan.** This failed PLAN's pre-stated "dev signal" gate for arm D, and the plan's pre-stated response (a negative H3′ and a pivot) was not taken ([F94](#F94)).
**Why this priority:** it is the dev answer to the scope-v2 hypothesis as originally planned (labels + signal); negative.
Refs: [`changes/2_deployable_peak/PLAN.md#L107`](../../changes/2_deployable_peak/PLAN.md#L107), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L16-L23`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L16-L23), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L91-L94`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L91-L94), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L123-L170`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L123-L170)

<a id="F39"></a>
### F39 [P1] [DEV] The WP2 finalists X1/X2 (F1PT labels + `load` + α) come from a rule written after the rep-1 screen but before confirmation; about half of X1's dev gain is the threshold alone
**The rule.**
- It was written 2026-10-03 00:20, after the rep-1 D screen had been logged and before any confirmation retrain.
- It scores S = mean_i min(A_i − X_i, B_i − X_i), and finalists need S > 0.
- It made PLAN's ablation arm E (D + α) eligible.
- X1's own rep-1 screen (Ea-1.0:F1PT) was queued at 02:15, after D:F1PT's confirmation had failed (S = −0.14) ([F94](#F94)).
- The F1PT labels are the LP-started PT 10 s configuration ([F24](#F24)).

**The finalists:**
- **X1** = Ea-1.0:F1PT, 37.20 (S = +1.027): vs A +1.30 (retrain SE 0.25, instance SE 0.64; 6/8), vs B +1.24 (0.26 / 0.51; 6/8).
- **X2** = Ea-0.5:F1PT, 37.84 (S = +0.386).

**Attribution.** The same threshold on Baleen's own models (A+α) scores 37.88, +0.62 vs A. X1 vs A+α is only +0.68 (5/8; instance SE 0.63).

**Selection bias, stated in the source.** 5 label designs, 5 variants and 2 α values were screened on the same 8 instances, so "the dev scores of X1/X2 are optimistic".
**Why this priority:** it defines the test configuration of H3′ and already shows that α carries much of the effect.
Refs: [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L25-L39`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L25-L39), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L114-L134`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L114-L134), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L186-L198`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L186-L198), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L246-L247`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L246-L247), [`changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L45-L48`](../../changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L45-L48), [`changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L64-L79`](../../changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L64-L79)

<a id="F40"></a>
### F40 [P2] [DEV] On dev, Ising (PT/EIM) vs classical (CP-SAT) labels of the same F1 formulation: no claim either way; with α the PT labels lead by +1.26 (5/8)
Paired over 8 dev instances:

| Comparison | Wins | Mean | SE (retrain / instance) |
|---|---|---|---|
| D:F1PT vs Dc:F1CPSAT | 3/8 | +0.37 | 0.42 / 0.54 |
| D:F1EIM vs Dc:F1CPSAT | 5/8 | +0.27 | — / 0.55 |
| X1 vs Ea-1.0:F1CPSAT | 5/8 | +1.26 | 0.47 / 0.61 |

- CP-SAT's day-1 label sets are as good (label peak 21.5).
- Its deployed models are worse on Region7 s0.3 (43.1) and volatile on Region6 s0.1 (40.3 ± 3.7).
- The source calls this "suggestive at best; no claim".
**Why this priority:** it is the dev answer to "does the Ising solver matter for labels"; suggestive at best on dev (≈2 instance-level SE with α). On test the sign flips, but only at ≈1 instance SE ([F48](#F48)). The full record is in [F70](#F70).
Refs: [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L172-L184`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L172-L184)

<a id="F41"></a>
### F41 [P1] [DEV] WP2 mechanism: on Region6 the Ising labels plus α admit the big-offset scans that set the peak; on Region7 they suppress first-access admission
**Region6.** Its peaks are long big-offset scans.
- X1 admits 41% of the peak window's accesses (A: 22%).
- Its peak sits in a scan window in only 2/12 retrains, against 9/12 for A. A+α leaves 9/12.

**Region7.** Its peaks are bursts of new episodes.
- The F1 labels have no zero-value positives, so first-access admission falls to 2–3% (D:F1PT 2.4%, X1 2.8%) vs 8–10% for the Baleen-label arms (A 8.7%).
- Mean DT rises by about 0.7, and X1 ≈ A (37.67 vs 37.69).

**Retention on dev:** X1 0.24 (per-instance mean).
**Why this priority:** it shows the dev gain depended on scans being present on day 1, which is exactly what failed on test ([F46](#F46)).
Refs: [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L200-L233`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L200-L233), [`changes/2_deployable_peak/wp2_deployed/results/mechanism_by_region.txt`](../../changes/2_deployable_peak/wp2_deployed/results/mechanism_by_region.txt), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L49`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L49)

<a id="F42"></a>
### F42 [P2] [DEV] The other WP2 ablations failed their screens or the confirmation rule
- **D2 (+ hour of day):** screen −2.04 (Region6 s0.3 47.4). One training day gives one example per hour, which PLAN.md flagged as a risk.
- **Epf (prefetch-model `load`):** screen −1.62 vs −0.92. It carries the known train/serve skew.
- **D:P0 / D:T2 (phase-1 designs):** −1.20 / −1.42. They restore first-access admission (16–30%) but are unstable: Region7 s0.1 41.7 for T2, Region6 s0.2 42.1 for P0.
- **Ea-1.0:F1EIM:** positive screen (+0.206), but not confirmed: it lost the variant comparison to D:F1PT's rep 1 (0.237).
- **Ea-2.0:** unmatched on 8/8, so no valid screen; not re-screened.
**Why this priority:** it closes the obvious alternative designs; secondary.
Refs: [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L123-L134`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L123-L134), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L228-L230`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L228-L230), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L246-L249`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L246-L249), [`changes/2_deployable_peak/PLAN.md#L110-L113`](../../changes/2_deployable_peak/PLAN.md#L110-L113)

<a id="F43"></a>
### F43 [P3] [INFRA] WP2 bookkeeping: 40 unmatched rows, all reported; the threshold-search bound was a tool limitation
**Totals.** 388 evaluations and 1,075 full simulations; 348 matched, 40 unmatched, 0 failed.

**Unmatched rows.**
- 36 came from the convergence search capping θ < 1, while the α arms (g ∈ [0.25, 4]) can need θ > 1.
- The affected control/comparison cells were re-run with the search widened to (0, 4] (Ax/Bx/Ex): all 28 matched, at θ 1.01–1.29 per the report (ledger minimum 1.0046).
- Both finalists had matched inside the original bound.
- 4 C-arm rows were write-rate steps.

**Interruptions.** Two session interruptions, resumed without loss.
**Why this priority:** a disclosure, not a result.
Refs: [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L7-L9`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L7-L9), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L235-L251`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L235-L251), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

## 5.4 WP3: the pre-registered deployability test H3′

<a id="F44"></a>
### F44 [P0] [NEGATIVE-TEST] H3′ = NO: Ising peak labels + `load` + the load-adaptive threshold (X1) win 5/6 instances but lose to Baleen on the mean (40.53 vs A 39.27), failing the pre-registered rule
**Test set.** Region7/Region6 × samples 0.4–0.6, touched once in deployed mode.
- Their offline OPT peaks had already been simulated in WP1 (committed 2026-10-03, before this protocol). They were used for retention only, never for selection ([F93](#F93)).
- The protocol's claim that they were never used "for any tuning, selection or inspection" is therefore true only of deployed runs.

**X1 vs the baselines:**
- X1 scores 40.53, vs A 39.27 and B 39.17.
- It wins 5/6 instances against each, but its mean is worse: A − X1 = −1.27, B − X1 = −1.36 (retrain SE 0.15 / 0.17; instance SE 2.41 / 2.55).
- It is below RejectX only barely (40.73) and below CoinFlip (48.64).

**X2** is also NO: 4/6, −1.61 / −1.70, and its mean (40.88) is not below RejectX (40.73).

**Run.**
- 126 evaluations, 126 matched; the arm means were recomputed from `trials.csv` (Appendix D).
- The ledger's timestamps put the whole test on 2026-10-05, from 14:23:12 to 17:41:42.
- It was evaluated on 2026-10-16 and committed that day (`46608e0`). Track C's processes never read WP3 output; its session was down from 10-05 ~15:05 to 10-16 ([F73](#F73)).

**P100 only.** X1's loss is a peak-window event: its P99 (31.82) and top-5 mean (36.02) are level with A's (31.96, 36.02).

**Pre-registration.** `PROTOCOL_v2_H3.md` was committed as `cba9970` (2026-10-04 09:16) before the test. The test was launched 2026-10-05, after the G3 waiver.
**Why this priority:** this is the decisive pre-registered answer to "does the Ising peak gain survive deployment". How X1 became the primary configuration is in [F94](#F94).
Refs: [`changes/4_story/result/untracked_evidence.txt`](../../changes/4_story/result/untracked_evidence.txt), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L81-L86`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L81-L86), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L1-L41`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L1-L41), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L63-L73`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L63-L73), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L23-L31`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L23-L31), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L84-L97`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L84-L97), [`changes/2_deployable_peak/wp3_test/trials.csv`](../../changes/2_deployable_peak/wp3_test/trials.csv), [`changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`](../../changes/2_deployable_peak/wp1_offline/results/wp1_table.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt)

<a id="F45"></a>
### F45 [P1] [NEGATIVE-TEST] H3′-labels = NO: X1 is not better than the same threshold on Baleen's own models
- X1 vs A+α: 3/6, −2.23 (retrain SE 0.21; instance SE 2.66).
- X1 vs B+α: 3/6, −2.15.

The protocol pre-registered this secondary test because on dev part of X1's gain came from the threshold alone. Had H3′ been YES with H3′-labels NO, the gain would have been attributed to the threshold, not the Ising labels.
**Why this priority:** it is the attribution test; it removes any residual credit for the labels on this test.
Refs: [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L10-L12`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L10-L12), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L30-L38`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L30-L38), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L15-L19`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L15-L19), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L95-L97`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L95-L97)

<a id="F46"></a>
### F46 [P1] [TEST-POSTHOC] Why H3′ failed: one big-offset scan peak (Region7 s0.5) that the F1-label models do not admit
**One catastrophic instance.** On five of six instances X1 is below A, by 0.1–2.3. On Region7 s0.5 all three X1 retrains land at 51.7–52.8 (mean 52.30), against A 39.07 and above even RejectX (42.05).

**The peak window is a scan.** Window 378 has 48% of its accesses ending beyond 8 MB. It is the peak window in 20 of the 21 matched retrains (one B+α retrain peaks in window 636).
- The Baleen-label models A and A+α admit 56–69% of the window's accesses.
- The F1-label models admit 4–14% (X1, X2); the CP-SAT labels 10–34%.

**Why the F1 labels miss it** (the source's diagnosis, "not a re-analysis"). They are fitted to Region7's day-1 peaks, which are not scans, so the GBM learns that big-offset episodes are not worth admitting. [F68](#F68) discusses how Baleen's trainer contributes.

**The first-access gap persists.** Averaged over all six test instances it is 1.8–1.9% (F1 arms) vs 4.1–4.8% (Baleen arms). On Region7 alone (recomputed from `trials.csv`) it is 3.3–3.6% vs 7.6–9.4%.

**Without that instance** (description only): A 39.31, A+α 38.57, X1 38.18, Dc+α 38.07.
**Why this priority:** it is the concrete failure mechanism behind the headline negative.
Refs: [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L42-L51`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L42-L51), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L61`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L61), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L20-L28`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L20-L28), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L63-L73`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L63-L73), [`changes/2_deployable_peak/wp3_test/trials.csv`](../../changes/2_deployable_peak/wp3_test/trials.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

<a id="F47"></a>
### F47 [P1] [TEST-POSTHOC] Post hoc on the H3′ test: the load-adaptive threshold on Baleen's own models is the best configuration
A+α scores 38.30, −2.5% vs Baleen.

| Comparison | Wins | Mean improvement | SE (retrain / instance) |
|---|---|---|---|
| A+α vs A | 5/6 | +0.96 | 0.16 / 0.39 |
| B+α vs B | 6/6 | +0.79 | |
| A+α vs B | 5/6 | +0.87 | |

The report states that A+α "was a control here and not the hypothesis", so it "needs its own pre-registered test (fresh region or reserve) before any claim". That test is H4 ([F52](#F52)).
**Why this priority:** it is the observation that redirected the project; post-hoc by construction.
Refs: [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

<a id="F48"></a>
### F48 [P2] [TEST-POSTHOC] H3′ pre-declared comparisons (no pass/fail): CP-SAT labels have the lower mean by 0.89 at ≈1 instance SE, and retention is negative for every F1-label arm
**Solver comparison.** Dc+α (same configuration, CP-SAT labels) has a mean 0.89 below X1: 3/6 wins each way, retrain SE 0.36, instance SE 0.84.
- Per instance, X1 − Dc+α = −0.433, −0.375, +0.107, −0.368, +4.808, +1.594 (Region6 s0.4–0.6, then Region7 s0.4–0.6; recomputed).
- Region7 s0.5 alone gives 4.81 of the 5.33 summed per-instance difference (90%); the other five average +0.105.
- The gap is about 2.5 SE at the retrain level and about 1 SE at the instance level. Given that concentration and the 3/6 split, this is not evidence that either solver's labels deploy better.

**Retention** R = (A − X)/(OPT_peak-blind − OPT_peak-aware), with WP1's offline OPT values:

| Arm | X1 | X2 | B | A+α | B+α | Dc+α |
|---|---|---|---|---|---|---|
| R | −0.28 | −0.33 | +0.02 | +0.16 | +0.15 | −0.12 |

The proposal's H3 target was at least 60% retention (scored in [F71](#F71)).
**Why this priority:** pre-declared secondary metrics with no pass/fail; they reinforce the verdict without adding a new one.
Refs: [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L14`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L14), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L38`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L38), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L75`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L75), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L98-L105`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L98-L105), [`changes/2_deployable_peak/wp3_test/trials.csv`](../../changes/2_deployable_peak/wp3_test/trials.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`documents/proposal_docx_compose/proposal.js#L201`](../../documents/proposal_docx_compose/proposal.js#L201)

## 5.5 Track C (WP8): deployment-aware Ising objectives, dev only

<a id="F49"></a>
### F49 [P2] [DEV] Track C stage 1: the cheap deployed proxy fails its pre-registered validation, so every screen used full simulations
**The proxy fails.** The validity criterion was written 2026-10-05 14:25, before any proxy value existed.
- The label-level proxy PL has a median per-instance Spearman of 0.49 against simulated P100 (< 0.5) → C1 FAIL. C2 and C3 pass.
- PM, built on WP2's actual trained models, does no better (median 0.37).
- The proxy's first-access-admission estimate is reliable (Pearson 0.98 over 128 cells).

**Designs explored:**
- **Anchored (ANC):** small edits of Baleen's labels. ANC3 keeps 96% of F1's day-1 peak cut with ~300 label flips.
- **Top-k (TK):** TK10 ≈ F1 on day 1; TK72 gives up most of the peak edit (day-1 peak 26.0).
- **Student-field (STU):** STU10R1.

**Why this priority:** it explains why Track C cost full simulations and why no cheap screen exists for deployed effects; secondary.
Refs: [`changes/2_deployable_peak/wp8_trackC/results/proxy_validation.md#L1-L28`](../../changes/2_deployable_peak/wp8_trackC/results/proxy_validation.md#L1-L28), [`changes/2_deployable_peak/wp8_trackC/results/proxy_validation.md#L63`](../../changes/2_deployable_peak/wp8_trackC/results/proxy_validation.md#L63), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L37`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L37), [`changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L9-L17`](../../changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L9-L17), [`changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L85-L103`](../../changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L85-L103)

<a id="F50"></a>
### F50 [P1] [DEV] Track C stage 2 is negative: no deployment-aware Ising objective passes the pre-registered dev screen
**The screen.** The finalist rule was committed as `19d7992` before stage 2, but after the H3′ test result had been committed ([F73](#F73)). Rep-1 screen score S1 = mean_i min(X1_i − Y_i, A+α_i − Y_i):

| Config | S1 |
|---|---|
| E8:STU10R1 | −0.26 |
| E8:ANC3 | −0.84 |
| E8:ANC10 | −1.80 |
| ANC10CP (comparison) | −0.94 |

So there was no confirmation, no finalist, and no Track C arm in the Region5 test. 64 evaluations, all matched.

**Mechanism.** E8:ANC3 does what it was designed to do on Region7, but gives back Region6.
- Region7: it restores first-access admission (0.121 vs X1 0.028) and has the best Region7 mean of any configuration (36.46; A+α 37.11; X1 37.67).
- Region6: it keeps Baleen's scan-peak failure (38.27 vs X1 36.73).

**Solver comparison** on the anchored energy, single retrain, no claim: CP-SAT labels deployed better than PT labels (37.46 vs 38.32).
**Why this priority:** it is the dev-level negative for "make the Ising labels themselves deployment-aware"; dev only, hence P1, not P0.
Refs: [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt), [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L1-L28`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L1-L28), [`changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md#L1-L41`](../../changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md#L1-L41), [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L72-L100`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L72-L100), [`changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L43-L55`](../../changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L43-L55)

<a id="F51"></a>
### F51 [P3] [DEV] Track C near miss: a single retrain of STU10R1 had the lowest dev mean, but the pre-registered gate rejected it
- E8:STU10R1 rep 1 averages 36.78, vs X1 rep 1 37.07 and A+α rep 1 37.86.
- Against the 3-retrain means of X1 and A+α it would score +0.041, with 6/8 wins on each.
- The pre-registered rep-1 vs rep-1 gate (S1 = −0.26) rejects it, and the source reports it "not acted on". It is one retrain inside X1's retrain noise (instance sd up to 2.6).
**Why this priority:** recorded so nobody resurrects it as evidence; minor.
Refs: [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L11-L14`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L11-L14), [`changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md#L39`](../../changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md#L39)

## 5.6 WP9: H4, the load-adaptive threshold on a fresh region (Region5)

<a id="F52"></a>
### F52 [P0] [TEST-PREREG] H4 = YES: the load-adaptive admission threshold on Baleen's own models beats Baleen on fresh Region5 (pre-registered; passes on the retrain-level SE, and one instance carries 69% of the gain)
**Read this first.**
- The pre-registered rule passed on the retrain-level SE (0.09).
- At instance level the gain is +1.16 ± 0.75 (≈1.5 SE).
- Region5 s0.5 alone gives 4.76 of the 6.93 summed gain (69%), and the other five instances average +0.43.
- Details and further caveats are in [F53](#F53).

Region5 samples 0.1–0.6 had never been run deployed; WP1 had simulated them offline only ([F93](#F93)).

**Primary arm A+α:**
- It scores 35.02, vs A 36.17 and B 36.37.
- vs A: 5/6 wins, +1.16 (retrain SE 0.09, instance SE 0.75).
- vs B: 5/6, +1.35 (0.08 / 0.94).
- It is below RejectX (39.35; low side 39.28) and CoinFlip (44.47). That is −3.2% vs Baleen.

**Secondary arm B+α:** 34.48; 6/6 vs A (+1.70) and 6/6 vs B (+1.89); −4.7%.

**Run.** 90 evaluations, all matched. Means and paired statistics were recomputed from `trials.csv` (Appendix D).

**Pre-registration.**
- H4 was pre-registered in PLAN_C §6 (`d10e572`, 2026-10-16 13:54).
- It was made executable in `PROTOCOL_v2_H4.md` (`c8f655a`, 2026-10-16 21:30) before the test run (2026-10-16 to 2026-10-17 05:31).
- α = −1 and ref = 20 were fixed from Region6/7 dev, with no tuning on Region5.
**Why this priority:** the project's only pre-registered deployed win.
Refs: [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L1-L19`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L1-L19), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L7-L18`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L7-L18), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L53`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L53), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L92`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L92), [`changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L105-L108`](../../changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L105-L108), [`changes/2_deployable_peak/wp9_region5/trials.csv`](../../changes/2_deployable_peak/wp9_region5/trials.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt)

<a id="F53"></a>
### F53 [P1] [TEST-PREREG] H4 caveats: the margin rests on the retrain-level SE, one instance carries most of the gain, and RejectX could not be matched
**One instance carries the gain.**
- On Region5 s0.5, A+α is 4.76 below A. On the other five instances the differences are −0.24 to +1.19 per the report (raw: −0.246 on s0.2 to +1.183 on s0.6).
- Recomputed, post hoc (not part of the pre-registered rule): s0.5 is 69% of the 6.927 summed gain; the other five average +0.434 (≈1.2% of A's mean); mean/SE_inst = 1.55.

**The margin passes only at retrain level.**
- The pre-registered rule uses the retrain-level SE (0.09).
- The instance-level SE (0.75) is reported but not used, and the +1.16 improvement is less than twice it. The same holds vs B (+1.35 vs instance SE 0.94).
- The secondary arm B+α passes 6/6, but its instance-level SEs are 1.19 (vs A) and 1.40 (vs B), so it too passes only at retrain level.

**RejectX could not be matched.** On 5 of 6 instances RejectX's write rate jumps across the ±1% band between probabilities 1e-6 apart.
- The protocol therefore fixed, before the test, a two-sided rule: below both the authors' replays (39.35) and the closest replays under the band (39.28).
- That rule was written at 21:25, after the static replays of the test instances (20:29–21:00) had exposed the step. Those replays carry no arm outcome, and A+α clears both values by about 4 points.

**Transfer caveats, stated in the protocol before the test.**
- α = −1 was chosen on Region6/7 dev data, so Region5 tests its transfer.
- Region5's Fig 9 variant differs (ML-Range on Partial Hit).
- WP1's offline headroom on these instances is only ≈3.3–5.9 util-points.
- 4/6 wins can fail on a smaller or noisier effect.
**Why this priority:** it states exactly how strong the one positive deployed result is.
Refs: [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L17`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L17), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L33`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L33), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L59-L60`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L59-L60), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L68-L76`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L68-L76), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L90-L96`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L90-L96), [`changes/2_deployable_peak/wp9_region5/PROGRESS.md#L65-L70`](../../changes/2_deployable_peak/wp9_region5/PROGRESS.md#L65-L70), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

<a id="F54"></a>
### F54 [P1] [TEST-POSTHOC] The Ising record X1 on Region5 (pre-declared, no pass/fail): it fails the reported rule again, with one catastrophic scan-type instance and a second large loss
**Result.** X1 scores 38.09.
- vs A: 3/6, −1.92;
- vs B: 2/6, −1.73;
- vs A+α: 2/6, −3.07.

**Mechanism.**
- On s0.5, X1 scores 51.46 vs A 42.72. In 14 of the 15 matched s0.5 retrains (all arms), the peak is window 924, where 0.515 of the accesses end beyond 8 MB (raw `trials.csv`). The auto-research union amendment describes this instance as a big-offset scan peak that Baleen's model admits.
- A second large loss: on s0.6 X1 scores 40.78 vs A 36.38. All three X1 retrains peak in window 927, where 0.44 of the accesses end beyond 8 MB; A peaks there in 2 of 3 retrains, at lower P100 (recomputed).
- The window analyses above are post hoc, on raw `trials.csv`.
- X1's labels again cut first-access admission (2.2% vs 3.8%) and raise mean DT by 0.8.
- **The labels themselves did cut the training-day peak.** On every test instance the F1PT label sets' day-1 peak (17.11–22.11; means over 6 seeds, util %) is below that of Baleen's labels (22.55–33.53). They contain no zero-value labels, and their Jaccard overlap with Baleen's labels is 0.426–0.550. On s0.5, the catastrophic instance, the pair is 20.47 vs 24.57. The reading that the loss arises in deployment rather than in the labels' offline objective is the story's interpretation.

**Retention:** X1 −0.54 vs A+α 0.31.

**Status.** The protocol reported the rule for X1 as an "Ising record" without attaching a pass/fail. It fails the rule against every reference.
**Why this priority:** it is the second fresh-region failure of the Ising-label configuration; it confirms H3′ was not a one-off.
Refs: [`changes/2_deployable_peak/wp9_region5/INSTANCES.md#L29-L38`](../../changes/2_deployable_peak/wp9_region5/INSTANCES.md#L29-L38), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L13`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L13), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L19-L31`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L19-L31), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L35-L49`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L35-L49), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L17`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L17), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L80`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L80), [`changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md#L8-L12`](../../changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md#L8-L12), [`changes/2_deployable_peak/wp9_region5/trials.csv`](../../changes/2_deployable_peak/wp9_region5/trials.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

<a id="F55"></a>
### F55 [P3] [INFRA] WP9 preparation: the dry run and the static replays
**Dry run.** Region5 s0, arm A, 1 retrain. It matched in 3 sims at P100 32.93 and θ 0.683; the authors' s0 Baleen row has P100 33.47.

**Static replays.** RejectX/CoinFlip replays are bit-exact against the authors at their own probability (12/12, max diff 3e-10). CoinFlip matched on 6/6; RejectX on 1/6 only.
**Why this priority:** a pipeline check; no verdict depends on it.
Refs: [`changes/2_deployable_peak/wp9_region5/PROGRESS.md#L18-L24`](../../changes/2_deployable_peak/wp9_region5/PROGRESS.md#L18-L24), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L57-L60`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L57-L60)

## 5.7 WP10: an Ising-fitted threshold table, tested on Region1 (H5)

<a id="F56"></a>
### F56 [P2] [DEV] WP10 E1: no training-window proxy ranks threshold variants well enough (pre-registered validity criterion)
The criterion needed ≥ 0.70 within-retrain sign concordance with full simulations:
- P1 (day-1 emulator): 0.63 → FAIL;
- P2 (full trace, diagnostic): 0.65;
- P3 (delta proxy): 0.61.

Post hoc, even the simulator's own day-1 peak (P4) reaches only 0.61. So the limit is the day-1 → later-days shift, not emulator fidelity. Data: 120 WP2 retrains, 272 matched variant rows, 126 pairs.
**Why this priority:** it means table fits are candidate generators only; dev detail.
Refs: [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L16-L49`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L16-L49), [`changes/2_deployable_peak/wp10_schedule/results/e1_verdict.json`](../../changes/2_deployable_peak/wp10_schedule/results/e1_verdict.json)

<a id="F57"></a>
### F57 [P1] [OFFLINE] WP10 E2: the Ising solver (PT) and the classical solver (coordinate descent) find the same (scale-equivalent) threshold tables on 46/48 packs
**Search space.** One-hot spins over 9 multipliers × 6 load buckets; 3003 monotone tables in total.

**Results.**
- PT (10 s) reaches the exhaustive optimum on 48/48 dev packs; CD on 46/48 (max gap 0.006).
- The classical exhaustive reference enumerates all 3003 tables in 1.5–2.3 s, against 10 s for PT and CD. On the 18 test fits, PT = exhaustive = CD ([F59](#F59)).
- The tables are scale-equivalent on 46/48. On test, TB:cd produced the same tables as TB:pt and hence identical results.

**In-sample day-1 replayed peak:** 31.28 for the neutral table, 29.75 fitted (−1.5). The proxy is not valid ([F56](#F56)), so this is not evidence.

**Timing caveat.** These 10 s solves ran with `taskset -c 0-23` while other work used the machine, not on the exclusive timing cores ([F100](#F100)). PT reached the exhaustive optimum on every pack, so its result is not budget-limited. CD's two misses (gap ≤ 0.006) may be.
**Why this priority:** a clean instance of the Ising ≡ classical tie ([F70](#F70)), on the component that was tested on Region1.
Refs: [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L10`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L10), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L51-L60`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L51-L60), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L82-L86`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L82-L86), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L15`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L15), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L71`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L71)

<a id="F58"></a>
### F58 [P2] [DEV] WP10 E3: TB:pt is the dev finalist under a rule written before any E2 solve or E3 simulation
**Screen.** S1 = TB:pt +0.41, TA:pt +0.10; both pass.

**Confirmation.**
- TB:pt qualifies: S3 = +0.19, 6/8 vs A+α, 7/8 vs B+α, dev mean 37.54.
- TA:pt fails: S3 = −0.30.

**Rule timing.** The finalist rule was written ≈17:32, before any E2 solve or E3 simulation.
**Why this priority:** it defines the H5 configuration; dev only.
Refs: [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L70-L80`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L70-L80), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L98-L116`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L98-L116), [`changes/2_deployable_peak/wp10_schedule/results/e3_tables.md#L13-L14`](../../changes/2_deployable_peak/wp10_schedule/results/e3_tables.md#L13-L14)

<a id="F59"></a>
### F59 [P0] [NEGATIVE-TEST] H5 = NO: the Ising-fitted load-bucket threshold table does not beat Baleen on fresh Region1 (24.45 vs A 24.14, 1/6); the fitted table was neutral on 10/18 test retrains
TB:pt scores 24.45.

| Reference | Mean | Wins | Mean improvement | SE |
|---|---|---|---|---|
| A | 24.14 | 1/6 | −0.31 | |
| B | 24.54 | 3/6 | +0.09 | 0.14 |
| B+α (best α arm) | 24.48 | 3/6 | +0.02 | 0.09 |

- It is below RejectX (28.20) and CoinFlip (50.39).
- Against A it is *worse*: −0.314 (≈2.2 instance SE, ≈3.4 retrain SE; recomputed).
- **What the test exercised** (raw `solves_test.csv`; not in the report). The fitted table was neutral on 10 of the 18 test retrains: all multipliers 1.0, i.e. plain arm B. PT's tables equal the classical exhaustive enumeration's (and CD's) on all 18. The 3003-table space enumerates in 1.5–2.3 s ([F57](#F57)).
- **Run.** 108 evaluations, all matched.
- **Pre-registration.** `2738cba` (2026-10-19 19:23), with a disclosed deviation ([F83](#F83)).
- **Not reported.** The results report omits several items its protocol listed as "Reported, no claim": F vs the other α arm (A+α), P99, top-5, θ, first-access and peak-window admission, and the solver ledger. They are not in the report. The raw values are in `trials_test.csv`, and the solver ledger in [`changes/2_deployable_peak/wp10_schedule/results/solves_test.csv`](../../changes/2_deployable_peak/wp10_schedule/results/solves_test.csv).
- **Why Region1.** Region2 lacked the authors' release rows (no Baleen Fig 9 row for s0.2; no RejectX rows for s0.1/s0.2).
**Why this priority:** the pre-registered negative for per-retrain day-1 table fitting on Region1. As a test of Ising solving it is uninformative: the table space is enumerable in ~2 s, and the fit was mostly neutral.
Refs: [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L82-L85`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L82-L85), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L1-L17`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L1-L17), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L42`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L42), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L20-L27`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L20-L27), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L58-L66`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L58-L66), [`changes/2_deployable_peak/wp10_schedule/trials_test.csv`](../../changes/2_deployable_peak/wp10_schedule/trials_test.csv), [`changes/2_deployable_peak/wp10_schedule/results/solves_test.csv`](../../changes/2_deployable_peak/wp10_schedule/results/solves_test.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt)

<a id="F60"></a>
### F60 [P1] [TEST-POSTHOC] On low-load Region1 the α arms are worse than Baleen (A+α 1/6, −0.49; pre-declared reported comparison, no pass/fail)
**Result.** A+α scores 24.62 and B+α 24.48, vs A 24.14. Recomputed: A+α vs A 1/6, −0.487 (≈2.7 instance SE, ≈7.9 retrain SE); B+α vs A 1/6, −0.338.

**Why.** Region1 is a low-load trace: mean DT ≈ 12 util-% vs ≈ 19–21 on Regions 5–7, and Baleen's peak ≈ 24 vs 36–39. The threshold arms raise mean DT by ≈ 0.25 without lowering the peak.

**Status.** PROTOCOL_v2_H5 listed "A+α, B+α vs A, B (H4 on a new region)" in advance under "Reported, no claim"; H4's pass rule applied only to Region5. The results report labels it "Not pre-registered (H4 was a Region5 test)". That is in tension with the protocol's listing, but it is accurate in that no pass rule was attached, which is why this finding is tagged TEST-POSTHOC. The source calls the load dependence "a hypothesis to examine (WP4), not a claim".
**Why this priority:** it bounds the one deployed win ([F69](#F69)).
Refs: [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19-L36`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19-L36), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L62-L64`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L62-L64), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

## 5.8 The auto-research loop (3_autoresearch, run 20261020_004634)

<a id="F61"></a>
### F61 [P2] [INFRA] The auto-research contract: an Ising-centric Y, a fresh pre-registered pool, a stricter rule and at most two test spends
`GOOD_RESULT.md` was fixed by the coordinator before the loop and is sha256-checked.

**What Y must be.** Its decisive component must come from an Ising/QUBO formulation, with a classical-solver control reported. Beating the control is not required.

**The pass rule.** On a fresh pre-registered pool, Y must beat A, B and the better of A+α/B+α:
- wins on ≥ ⌈2n/3⌉ instances;
- margin > 2.5 × SE_retrain;
- no instance worse by more than 2.0;
- below RejectX and CoinFlip.

**The pools.** T1 Region2 s0.1–0.6, T2 Region4 s0.2–0.6, T3 Region3 s0.1–0.3 (second spend only). Reserve samples 0.7–0.9 are never touched.

**The loop.** A headless Opus 5.5 worker, a deterministic `validate.py`, and two LLM validators per round.

**Permissions skipped (disclosure).** The worker ran with Claude Code's permission checks disabled (`--dangerously-skip-permissions`, "permissions skipped by the captain's instruction"). The worker process itself was therefore not sandboxed; only the sub-processes it launched were. The validators recorded these mitigations:
- the repo-wide scans for files newer than the run's leak marker, outside `3_autoresearch` (`.git` and `.pyc` excluded), returned nothing;
- every one of the 1,529 sub-process logs with a command line begins `taskset … bwrap` with a private `/tmp`;
- the worker used no subagents.
**Why this priority:** it defines how the negative verdict below should be read; infrastructure.
Refs: [`changes/3_autoresearch/documents/GOOD_RESULT.md#L1-L59`](../../changes/3_autoresearch/documents/GOOD_RESULT.md#L1-L59), [`changes/3_autoresearch/README.md#L1-L9`](../../changes/3_autoresearch/README.md#L1-L9), [`changes/3_autoresearch/autoscript/run_auto.sh#L1-L40`](../../changes/3_autoresearch/autoscript/run_auto.sh#L1-L40), [`changes/3_autoresearch/result/validator_integrity_stats_round_1.md#L26-L33`](../../changes/3_autoresearch/result/validator_integrity_stats_round_1.md#L26-L33), [`changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L40-L47`](../../changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L40-L47)

<a id="F62"></a>
### F62 [P2] [DEV] Auto-research H-CLS (Ising-fitted load × access-class threshold tables): no finalist
**Candidates.**
- **CB:pt** passed the retrain-1 screen (mean d +0.313, worst −0.151, 6/8) but failed the finalist rule: ineligible because Region1_s0 r2 was unmatched, and only 6/10 wins vs A+α (needs 7).
- **CB:ptm, CA:pt and CA:ptm** failed the gate.
- **UB:ptm** (one pooled table) failed the gate: −0.732, worst −4.516, with a Region6 s0.1 collapse.

**Lesson recorded.** A per-instance day-1 fit helps mainly by switching load adaptivity *off* where day 1 shows no gain.
**Why this priority:** a dev negative inside the loop; secondary.
Refs: [`changes/3_autoresearch/result/FINAL_REPORT.md#L18-L32`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L18-L32)

<a id="F63"></a>
### F63 [P2] [DEV] Auto-research H-UX (union of Baleen's model and an Ising-label model): the dev finalist XA:F1PT
**Rule.** Admit iff s_A > θ·g OR s_X > κ·θ·g, where X is a GBM trained on the F1 min–max day-1 labels solved by PT.

**Screen.** Mean d +1.460 (XA, 6/8) and +1.072 (XG, 7/8).

**Finalist rule (n = 10 dev instances).** XA:F1PT scores 35.36:
- 10/10 vs A (+1.42, SE 0.19);
- 9/10 vs B;
- 7/10 vs A+α (+0.80, SE 0.18, worst −0.82).

XG:F1PT (35.53) also qualified; the pre-written tie-break chose XA.

**Mechanism.** The dev gain came mainly from Region6 scans: 36.77 vs A+α 38.65, peak big-offset share 0.20 vs 0.33. Region7 is nearly level (37.01 vs 37.11). The union did not restore Region7 first-access admission (3.0% vs 8.4% for A+α; A is 8.7% per the round-2 validator's correction).

**Caveat.** The union T1 protocol was committed after 9 of 16 union screen results had been read ([F84](#F84)).
**Why this priority:** it defines the configuration spent on T1/T2; selection-biased dev data.
Refs: [`changes/3_autoresearch/result/DEV_RULES.md#L43`](../../changes/3_autoresearch/result/DEV_RULES.md#L43), [`changes/3_autoresearch/result/FINAL_REPORT.md#L34-L58`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L34-L58), [`changes/3_autoresearch/result/FINAL_REPORT.md#L107`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L107), [`changes/3_autoresearch/work/union/results/dev_finalist.json`](../../changes/3_autoresearch/work/union/results/dev_finalist.json), [`changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L176-L186`](../../changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L176-L186)

<a id="F64"></a>
### F64 [P1] [NEGATIVE-TEST] Auto-research T1 (Region2): spent, failed, and unevaluable as pre-registered
**Why it could not be evaluated.**
- Region2_s0.2 cannot reach the target write rate for any arm: admit-all gives 11.5 MB/s.
- The release has no s0.2 row at DWPD 7.5, and the day-1 instance has 164 episodes vs 1285–1984 for the others. This was "not checked" before the protocol.
- Arm A had 0/6 matched retrains on s0.1 and 2/6 on s0.5.

**Fail-closed decision.** It was committed (`539f39e`) before `evaluation.json` was opened.

**Descriptive only (s0.3–0.6).** No reading favours Y beyond noise: Y is level with A and trails B, A+α and B+α. Y and its CP-SAT-label control are tied (10.246 vs 10.246).

| Y | A | B | A+α | B+α |
|---|---|---|---|---|
| 10.246 | 10.255 | 10.201 | 10.188 | 10.135 |

**Static baselines.** RejectX was unmatched on 6/6, and the baseline condition was uninformative.

**Load.** Region2 is very low-load (Baleen's peak ≈ 10).
**Why this priority:** one of the two test spends. It was unevaluable as pre-registered because of a design defect (s0.2 infeasible; A unmatched), and the descriptive s0.3–0.6 numbers do not favour Y either (the source: "The T1 failure is not an artefact of s0.2"). P1 rather than P0 because T2 is the clean test.
Refs: [`changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L1-L38`](../../changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L1-L38), [`changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L45-L66`](../../changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L45-L66), [`changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L79-L100`](../../changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L79-L100)

<a id="F65"></a>
### F65 [P0] [NEGATIVE-TEST] Auto-research T2 (Region4) = FAIL: the Ising-label union does not beat the threshold arm A+α (1/5, −0.30); its gain over Baleen is the threshold's, so the loop ends NEGATIVE
Y = XA-F1PT scores 43.17.

| Reference | Mean | Wins | mean(R − Y) | SE_retrain | Rule |
|---|---|---|---|---|---|
| A | 50.72 | 4/5 | +7.547 | | ok |
| B | 56.71 | 5/5 | +13.541 | | ok |
| A+α (best α arm) | 42.87 | 1/5 | −0.300 | 1.117 | FAIL |

- Y is below RejectX (65.84) and CoinFlip (68.84).
- **Classical control** (the same union with CP-SAT labels, XA-F1CPSAT, 44.37; reported, no pass/fail): Y has the lower mean by 1.20 but wins only 2/5. The lead is carried by s0.2 (Y 49.61 vs control 55.05), where Y's own retrains span 42.87–59.28 (sd 8.59). The source: "Not significant, and not attributable to better optimization".
- **Run.** All 30 cells have 3/3 matched retrains; 8 `__FAILED_` incident rows are kept.
- **Pre-registration.** `1cda6af` (05:19) was committed before any T1 or T2 test run. TEST_GO came at 07:05:04, after addendum `3fdba1b`.
- **Prerequisites built before the protocol.** The T2 instance dumps and the 60 F1 label sets were built at 04:57–05:04, before the 05:19 protocol commit and before Y was fixed. The protocol and the notebook disclose this and state that none was read; the round-2 red-team validator found no read before TEST_GO. The pool choice was fixed in the notebook at 04:56.
- **Outcome.** The test budget (2 of 2) is exhausted and the loop's verdict is NEGATIVE.

Means recomputed (Appendix D).
**Why this priority:** it is the last and cleanest pre-registered test of an Ising/QUBO deployed component, and it shows the gain over Baleen is the threshold's.
Refs: [`changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L14`](../../changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L14), [`changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L23-L25`](../../changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L23-L25), [`changes/3_autoresearch/result/LAB_NOTEBOOK.md#L268-L280`](../../changes/3_autoresearch/result/LAB_NOTEBOOK.md#L268-L280), [`changes/3_autoresearch/result/validator_red_team_round_2.md#L44`](../../changes/3_autoresearch/result/validator_red_team_round_2.md#L44), [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L1-L38`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L1-L38), [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L54-L56`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L54-L56), [`changes/3_autoresearch/result/FINAL_REPORT.md#L1-L7`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L1-L7), [`changes/3_autoresearch/result/FINAL_REPORT.md#L60-L69`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L60-L69), [`changes/3_autoresearch/work/t2u_region4/trials_test.csv`](../../changes/3_autoresearch/work/t2u_region4/trials_test.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt)

<a id="F66"></a>
### F66 [P1] [TEST-POSTHOC] Region4 replicates the H4 effect post hoc: A+α is 15% below Baleen
- A 50.72 → A+α 42.87 (−15%).
- Recomputed: A+α vs A 5/5, +7.847 (SE_retrain 0.446; instance SE 5.125); vs B 5/5, +13.841.
- **Concentrated, as on Region5.** Per instance, A − A+α = +9.488, +27.186 (s0.3), +0.120, +0.442, +2.001. s0.3 alone is 69% of the summed gain, and the other four average +3.013.
- A+α was a reference arm in T2, not a hypothesis; the source calls it "a new-region replication of H4, not pre-registered as H4 here".
- Region4's peaks are high-load bursts (peak-window big-offset share 0.02–0.04).
**Why this priority:** the strongest (post-hoc) support for the threshold's load dependence ([F69](#F69)).
Refs: [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L40-L52`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L40-L52), [`changes/3_autoresearch/result/FINAL_REPORT.md#L75`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L75), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

<a id="F67"></a>
### F67 [P1] [TEST-POSTHOC] Why the union did not transfer (the final report's interpretation): neither test pool has scan peaks
The union's added value on dev was admitting big-offset scans at peak load (Region6). On the pools, the peak window's big-offset share is ≈ 0.01 (Region2) and 0.02–0.04 (Region4), against 0.33 for A+α on dev Region6.
- On Region4, Y lands at A+α's level with slightly lower peak-window admission (0.31 vs 0.41).
- The final report's conclusion: "the deployed peak gain comes from spending the write budget at high load, not from the Ising labels".
**Why this priority:** it is the mechanism of the loop's negative result, consistent with [F68](#F68).
Refs: [`changes/3_autoresearch/result/FINAL_REPORT.md#L71-L75`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L71-L75), [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L50-L52`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L50-L52), [`changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L63-L66`](../../changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L63-L66)

## 6. Cross-cutting mechanisms

These findings combine evidence across phases and interpret the reported mechanism tables. Each is tagged by the evidence its main claim rests on. Supporting dev observations are marked "dev" inline and are not evidence on their own.

<a id="F68"></a>
### F68 [P1] [TEST-POSTHOC] Day-1 min–max labels are brittle when the peak *type* changes (big-offset scan vs burst of new episodes)
The same pattern appears in every phase:
- **Phase-1 Q3 (held-out).** On 3/6 instances P100 was decided by rare scan-like windows (25–42% of accesses ending beyond 8 MB), and relabelling moved them either way.
- **WP2 dev.** The F1 labels plus α helped exactly where Region6's scans were present on day 1 (scan peaks 2/12 vs 9/12).
- **H3′ test.** Region7 s0.5's peak window was a scan (48% big-offset). The PT F1-label models (X1, X2) admitted 4–14% of its accesses and the CP-SAT F1-label models 10–34%, against 56–69% for A and A+α. X1 averaged 52.30.
- **H4 test.** X1 again had one catastrophic instance: Region5 s0.5, 51.46 vs A 42.72.
- **Union (auto-research).** It helped on dev Region6 scans but had nothing to act on in pools without scan peaks.

**Interpretation.** Labels optimised for one day's peak teach the GBM which *kind* of episode to admit. When the test days' peak is of another kind, the model rejects exactly the accesses that matter. This is post-hoc diagnosis across tests, not a pre-registered hypothesis.

**Not only a label problem.**
- Baleen's frozen trainer keeps only each episode's first 15 accesses. Big-offset, high-count scan accesses are therefore learned from a few, mostly negative rows.
- On dev Region6 it was *Baleen's own* model that failed the scan peak (phase-1 window 712; WP2: A has a scan peak in 9/12 retrains, [F41](#F41)).
- So the brittleness lies in the GBM/trainer combined with day-1 labels, and min–max labels amplify it when the day-1 peak is not a scan.
**Why this priority:** this is the main explanation for the deployed negatives; mechanism, hence P1.
Refs: [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L26`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L26), [`changes/1_literature_review/explore/q3/RESULTS.md#L291-L299`](../../changes/1_literature_review/explore/q3/RESULTS.md#L291-L299), [`changes/1_literature_review/explore/q3/RESULTS.md#L28-L35`](../../changes/1_literature_review/explore/q3/RESULTS.md#L28-L35), [`changes/1_literature_review/explore/q3/RESULTS.md#L94-L101`](../../changes/1_literature_review/explore/q3/RESULTS.md#L94-L101), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L207-L229`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L207-L229), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L42-L51`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L42-L51), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L19-L31`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L19-L31), [`changes/3_autoresearch/result/FINAL_REPORT.md#L56-L58`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L56-L58), [`changes/3_autoresearch/result/FINAL_REPORT.md#L71-L75`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L71-L75)

<a id="F69"></a>
### F69 [P1] [TEST-POSTHOC] The load-adaptive threshold's evidence status, region by region: pre-registered YES on Region5, post-hoc on Regions 6/7 and 4, null on Region1
| Region | Status | Source | A+α vs A |
|---|---|---|---|
| Region5 | **pre-registered (H4), YES** | [F52](#F52) | 35.02 vs 36.17; 5/6; +1.16 |
| Regions 6/7 | **post-hoc** (WP3 control arm) | [F47](#F47) | 38.30 vs 39.27; 5/6; +0.96 |
| Region4 | **post-hoc** (T2 reference arm) | [F66](#F66) | 42.87 vs 50.72; 5/5; +7.847 |
| Region1 | **null / worse** (WP10; declared as a reported comparison, no claim, and no pass rule) | [F60](#F60) | 24.62 vs 24.14; 1/6; −0.487 |
| Region2 | **descriptive only** (T1 unevaluable) | [F64](#F64) | 10.188 vs 10.255 on s0.3–0.6 |

**Interpretation.** The pattern suggests the threshold helps where load is high: mean DT ≈ 12 on Region1 vs ≈ 19–21 on Regions 5–7, and Baleen's peak ≈ 10 on Region2 vs 50.72 on Region4. WP10 calls this "a hypothesis to examine (WP4), not a claim". Only the Region5 result is confirmatory.

**Dev context weakens the simple load story.** On dev Region1_s0 the threshold did help: A 26.97 → A+α 26.23, 3 retrains each (auto-research reference arms, recomputed). Low load is therefore not by itself a sufficient explanation of the Region1 test result.

None of these arms uses Ising/QUBO.
**Why this priority:** it states precisely how far the one deployed win generalises; it is a synthesis of mostly post-hoc evidence.
Refs: [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L31`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L31), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60), [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L23-L31`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L23-L31), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19-L36`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19-L36), [`changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L57-L66`](../../changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L57-L66), [`changes/3_autoresearch/work/cls_table/trials_dev.csv`](../../changes/3_autoresearch/work/cls_table/trials_dev.csv), [`changes/3_autoresearch/result/LAB_NOTEBOOK.md#L167`](../../changes/3_autoresearch/result/LAB_NOTEBOOK.md#L167), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

<a id="F70"></a>
### F70 [P1] [OFFLINE] Ising and classical solvers: identical objectives where both reach the optimum, budget-dependent winners elsewhere, and a two-way record for deployed labels (at most ≈2.1 instance-level SE)
**Exact ties.**
- Phase 1: the floored Region7 s0.2 instance is reached (25.412) by CP-SAT, LS, PT and EIM at every budget.
- H2′ test: the floored Region7 s0.4 (23.8766) and Region6 s0.5 (23.6721) are ties.
- WP10: PT reaches the exhaustive table optimum on 48/48 packs and CD on 46/48. The tables are scale-equivalent on 46/48 packs, so TB:cd = TB:pt on 23/24 dev retrains and on the whole H5 test.
- Auto-research: PT and CP-SAT give identical F1 objectives on 36/36 Region2 and 30/30 Region4 label solves.

**Budget-dependent winners (objective).**
- Ising best at 10 s in Q2 and at 3 s in H2′.
- Classical best at 60/300 s, at 1 s, and in rolling windows ([F30](#F30)).
- On the label-size day-1 instances at 10 s (WP5-tuned configurations, 8-level nested objective), CP-SAT and LS beat EIM and PT ([F32](#F32)).
- On Track C's anchored energy (10 s), PT's mean objective was lower than CP-SAT's (13.55 vs 14.31), but PT was lower on only 11/24 cells, and CP-SAT never proved optimality. The two sides did not run under the same conditions: the CP-SAT solves finished 11 days after the PT solves, while the foreign job was active (running since 10-10; ~15 of 24 CPUs when noted at 14:37 that day); the PT solves predate that job ([F100](#F100)).

**Deployed label sets, PT vs CP-SAT, the full record** (the finding's OFFLINE tag covers the objective comparisons; the evidence level of each deployed row is given in its Data column; the WP2 and union rows are recomputed from raw ledgers in Appendix D). No comparison had a pass/fail. Only the WP2 X1 row reaches ≈2.1 *instance-level* SE (recomputed 2.07); all others are below 2. At the retrain level used by the project's pass rules, three rows exceed 2 SE: WP2 dev (2.7) and the union on dev (2.1) favour PT, and the H3′ test (2.5) favours CP-SAT. The headline remains the instance-level reading: no row is clearly beyond 2 SE, and the two PT-favouring rows are dev.

| Comparison | Data | Lower mean | Margin | Wins | SE / note |
|---|---|---|---|---|---|
| WP2 D:F1PT vs Dc:F1CPSAT | dev (DEV) | PT | +0.37 | 3/8 | 0.42 / 0.54 |
| WP2 X1 vs Ea-1.0:F1CPSAT | dev (DEV) | PT | +1.26 | 5/8 | 0.47 / 0.61 |
| H3′ X1 vs Dc+α | test (TEST-POSTHOC) | CP-SAT | 0.89 | 3/6 each way | 0.36 / 0.84; Region7 s0.5 carries it ([F48](#F48)) |
| Track C E8:ANC10 vs E8:ANC10CP | dev, 1 retrain (DEV) | CP-SAT | 38.32 vs 37.46 | — | no claim |
| Union XA:F1PT vs XA:F1CPSAT | dev, n = 10, completed after the T2 outcome; retrain 1 on the 8 Region6/7 instances ran before T1 (report only; DEV) | PT | +0.77 | 6/10 | 0.36 / 0.42 (2.1 / 1.8 SE); three high-variance instances carry it; neither CP-SAT union would qualify |
| T2 Y vs control | test (TEST-POSTHOC) | PT | +1.20 | 2/5 | SE 1.05; carried by s0.2; "not significant" |
| T1 Y vs control | test (descriptive; TEST-POSTHOC) | tie | 10.246 vs 10.246 | 2/4 | — |
| H4 (Region5) | test | not measured: no CP-SAT twin of X1 was run | | | |

**Reading.**
- For the F1 rows the objectives tie, so the deployed differences come from *which* (near-)co-optimal label set each solver returns: PT's sets vary by seed, CP-SAT's barely do. The final report: "It is not evidence that the Ising solver optimizes the QUBO better."
- On Track C's anchored energy the reverse occurred: PT had the lower mean objective (lower on 11/24 cells) but its labels deployed worse (one retrain).

**Timing caveat.** After H2′ the `TIMING_IDLE` flag, which releases the timing cores to other tracks, stayed in place, so the 10 s label, table and Track C solves ran on shared cores ([F100](#F100)).
**Why this priority:** it answers plainly what Ising contributed as an optimiser: parity, not superiority.
Refs: [`changes/3_autoresearch/result/LAB_NOTEBOOK.md#L309-L322`](../../changes/3_autoresearch/result/LAB_NOTEBOOK.md#L309-L322), [`changes/3_autoresearch/result/LAB_NOTEBOOK.md#L435-L436`](../../changes/3_autoresearch/result/LAB_NOTEBOOK.md#L435-L436), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/1_literature_review/explore/q2/RESULTS.md#L243-L252`](../../changes/1_literature_review/explore/q2/RESULTS.md#L243-L252), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L22-L24`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L22-L24), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L41-L43`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L41-L43), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L138-L165`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L138-L165), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L220-L239`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L220-L239), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L83-L84`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L83-L84), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L115`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L115), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L15`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L15), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L172-L184`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L172-L184), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L14`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L14), [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L20`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L20), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L94-L96`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L94-L96), [`changes/3_autoresearch/result/FINAL_REPORT.md#L77-L94`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L77-L94), [`changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L57-L59`](../../changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L57-L59), [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L54-L56`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L54-L56), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L42-L51`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L42-L51)

<a id="F71"></a>
### F71 [P1] [TEST-POSTHOC] Mean retention of the offline gain never approached the proposal's 60% target for any Ising-label configuration (pre-declared metric, no pass/fail; the 60% criterion comes only from the proposal)
Retention R = (A − X)/(OPT_peak-blind − OPT_peak-aware) was a pre-declared "also reported" metric with no pass/fail in the H3′ and H4 protocols. The 60% target appears only in the proposal's H3, not in any phase-2 protocol, so scoring against it is post hoc.

**Test values:**
- H3′: X1 −0.28.
- H4: X1 −0.54.
- The highest test retentions belong to arms that use Baleen's labels, not peak labels: A+α 0.31 and B+α 0.46 on Region5. Their retention measures something other than label distillation.

**Dev context, not tests:**
- harness_eval: the best Ising arm C4 +0.01 / +0.01. The classical R2 arm had −0.04 / +0.11.
- WP2: X1 0.24 as a per-instance mean; individual instances range from −0.23 to +0.74.

**Why this priority:** it directly scores the proposal's H3. The metric was declared before the test, but the threshold it is scored against was not.
Refs: [`documents/proposal_docx_compose/proposal.js#L201`](../../documents/proposal_docx_compose/proposal.js#L201), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L75`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L75), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L49`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L49), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L100-L105`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L100-L105), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L84-L88`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L84-L88), [`changes/1_literature_review/harness_eval/RESULTS.md#L250`](../../changes/1_literature_review/harness_eval/RESULTS.md#L250), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L231-L233`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L231-L233)

<a id="F72"></a>
### F72 [P2] [DEV] First-access admission is the recurring lever on Region7 (mostly dev evidence)
**Raising it helped on dev.** Phase-1 labels raised Region7 first-access admission from 6% to 14–28% (the q3 report says 14–28% in its summary and 15–28% in its mechanism section). Zero-value positives account for the top of that range: P0, whose labels are 44% zero-value one-hit wonders, reached 28%, while T5c (zero-value additions removed) reached 14.8% and C2 14.3%. Across the 13 Region7 dev trials, corr(first-access admission, P100) = −0.79.

**The F1 labels lower it, and Region7 suffers.**
- WP2 dev: 2–3% (D:F1PT 2.4%, X1 2.8%) vs Baleen's 8.7%.
- H3′ test, pooled over both regions: 1.8–1.9% vs 4.1–4.8%.

**Restoring it fixes Region7 but not Region6.**
- Track C's anchored labels restored it (0.121 vs X1 0.028) and gave the best Region7 dev mean, but lost Region6.
- The union did not restore it: 3.0%, vs A+α 8.4% (A 8.7%).

**Region6 first-access admission stays small**, by mean per arm:
- ≤ 1.3% in every WP2 arm except D:P0, and in every Track C arm;
- the phase-1 design D:P0 reaches more: 2.89% (max 5.61%). D:T2 (1.04%) sits above the WP2 F1 and Baleen arms (≤0.74%) but within the 1.3% bound (recomputed).
**Why this priority:** a mechanism detail tying the phases together; secondary.
Refs: [`changes/1_literature_review/explore/q3/RESULTS.md#L25-L28`](../../changes/1_literature_review/explore/q3/RESULTS.md#L25-L28), [`changes/1_literature_review/explore/q3/RESULTS.md#L244-L250`](../../changes/1_literature_review/explore/q3/RESULTS.md#L244-L250), [`changes/1_literature_review/explore/q3/PROGRESS.md#L99-L101`](../../changes/1_literature_review/explore/q3/PROGRESS.md#L99-L101), [`changes/1_literature_review/explore/q3/RESULTS.md#L244-L251`](../../changes/1_literature_review/explore/q3/RESULTS.md#L244-L251), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L207-L229`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L207-L229), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L63-L73`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L63-L73), [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L15-L19`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L15-L19), [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L85-L95`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L85-L95), [`changes/3_autoresearch/result/FINAL_REPORT.md#L56-L58`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L56-L58), [`changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L176-L186`](../../changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L176-L186), [`changes/2_deployable_peak/wp2_deployed/results/mechanism_by_region.txt`](../../changes/2_deployable_peak/wp2_deployed/results/mechanism_by_region.txt), [`changes/2_deployable_peak/wp2_deployed/trials.csv`](../../changes/2_deployable_peak/wp2_deployed/trials.csv), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)

## 7. Methodology and integrity

How the tests were made credible:
- protocols committed before the runs;
- bit-exact gates for every code change;
- a frozen artifact (`check_frozen.sh`);
- sandboxed processes (`bwrap` with a private `/tmp`);
- one training at a time;
- timing on pinned cores with idle SMT siblings;
- a ledger row for every evaluation.

The full set of recorded incidents and deviations follows.

<a id="F73"></a>
### F73 [P1] [INFRA] Every phase-2 and auto-research test protocol was committed to git before its test ran
Commits from `git log`; run times from each report.

| Test | Protocol commit | Test run |
|---|---|---|
| H1′ (offline) | criterion in `PLAN.md` (`27fb6f0`, 2026-09-29 15:06:02) | WP1 solves from 2026-10-01; committed `08ad0d2`, 2026-10-03 00:11:36 |
| H2′ | `fd54e76`, 2026-10-03 01:13:51 | 01:24:38 to 01:45 |
| H3′ | `cba9970`, 2026-10-04 09:16:01 | G3 waiver `84a0c1d` 2026-10-05 14:13:01; ledger rows 14:23:12 to 17:41:42 that day; result committed 2026-10-16 (`46608e0`) |
| Track C rule | `19d7992`, 2026-10-16 13:54:17 | stage-2 driver first launched un-bwrapped ≈1 minute before its 13:56 relaunch |
| H4 | `d10e572`, 2026-10-16 13:54:30, then `c8f655a`, 21:30:11 | to 2026-10-17 05:31 |
| H5 | `2738cba`, 2026-10-19 19:23:04 | chain 19:23 to 20:47 |
| T1 (union) | `76cf5c8`, 2026-10-20 04:36:45 | TEST_GO 06:26:50 |
| T2 | `1cda6af`, 05:19:24 | TEST_GO 07:05:04, after addendum `3fdba1b` at 07:04:57 |

The earlier cls_table T1 protocol (`9650674`) is void: it had no finalist and wrote no TEST_GO.

**H3′ timing and the Track C firewall.**
- **Test and evaluation.** The H3′ test finished 10-05 17:41 (last ledger row). It was evaluated 10-16 12:33 (`evaluation.json` mtime), and the result was committed 12:40 (`46608e0`).
- **Track C was not running in the gap.** It ran only 10-05 14:18 to ~15:05, at the same time as the H3′ test, and its session was down until 10-16.
- **Its stage-2 rule came after the H3′ result.** The finalist rule and short-list were written on 10-16 and committed at 13:54:17 (`19d7992`), after the H3′ result commit and in the same minute as the coordinator's H4 addendum, which was written "based on the H3′ result".
- **What the firewall actually is.** Track C's own processes never read `wp3_test`, and the coordinator records that Track C's design stayed blind to the H3′ outcome. That is a statement, not a mechanism. Track C's result was negative, so no claim depends on it.
**Why this priority:** this is what makes the TEST-PREREG labels in this story auditable.
Refs: [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L16-L19`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L16-L19), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L3-L5`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L3-L5), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L4`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L4), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L132`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L132), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L1-L4`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L1-L4), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L1-L5`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L1-L5), [`changes/3_autoresearch/result/FINAL_REPORT.md#L60-L69`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L60-L69), [`changes/3_autoresearch/result/FINAL_REPORT.md#L147`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L147), [`changes/2_deployable_peak/wp3_test/trials.csv`](../../changes/2_deployable_peak/wp3_test/trials.csv), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L9`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L9), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L82-L86`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L82-L86), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L97`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L97), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L105-L110`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L105-L110), [`changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L105-L108`](../../changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L105-L108), [`changes/4_story/result/untracked_evidence.txt`](../../changes/4_story/result/untracked_evidence.txt), [`changes/2_deployable_peak/PLAN.md#L18-L19`](../../changes/2_deployable_peak/PLAN.md#L18-L19)

<a id="F94"></a>
### F94 [P1] [INFRA] PLAN's pre-stated "dev signal" gate failed; instead of the pre-stated negative-and-pivot, H3′ was re-specified around PLAN's ablation arm E (labels + `load` + α)
**What PLAN fixed in advance.**
- Arm D (Ising labels + `load`) is "**the hypothesis**".
- Arm E (D + adaptive threshold or load-aware ML-When) is an "ablation".
- The gate: "Dev signal | Oct 12 | arm D beats both A and B on the dev mean, beyond 2 SE | report a negative H3′ with the mechanism, and pivot the paper to a 'contemporary + analysis' framing".

**What happened** (WP2's progress log):
- **2026-10-03 00:10.** The rep-1 D screen is logged: D:F1PT 37.99, +0.51 vs A (4/8), +0.45 vs B (2/8).
- **00:20.** The finalist rule is written. Its candidates include arms D, D2 *and* E, and a D2/E variant is confirmed if its rep-1 screen beats D:F1PT's.
- **00:25.** The queue includes Ea-0.5:F1PT r1.
- **01:35.** D:F1PT, confirmed with 3 retrains, scores S = −0.14. D:F1EIM is later logged at S = −0.238 (10-04 05:25). With both D arms negative, the dev-signal gate failed ([F38](#F38)); the progress log does not state the gate, so this is the story's reading.
- **02:15.** The queue is extended by Ea-1.0:F1PT r1, i.e. X1.
- **10-04 05:25.** The rule is applied: Ea-1.0:F1PT screen 1.156 → confirm.
- **06:50.** Its confirmation finishes at S = +1.027.
- **08:25.** The final rule application names it X1, the H3′ primary.

**What the protocol says.** PROTOCOL_v2_H3 records the result ("the only configurations that met the finalist rule are of PLAN arm type E … X1 therefore includes that threshold") and replaces an earlier 2026-10-01 17:23 draft. Neither it nor RESULTS_dev names the PLAN gate or the pivot that was not taken.

**Consequence.**
- The adaptive threshold had been allowed by scope v2 and defined as PLAN's arm E from the start; Ea-0.5 was queued before D failed. This fork is where α became part of the *tested hypothesis* (the H3′ primary X1). The threshold later became the post-hoc winner ([F47](#F47)) and then the pre-registered H4 ([F52](#F52)).
- H3′ was still committed before its test and failed ([F44](#F44)). So the deviation changed *what* was tested, not the integrity of the test.

**Why this priority:** a pre-registered decision gate that was not followed, at the point that shaped both H3′ and H4.
Refs: [`changes/2_deployable_peak/PLAN.md#L49-L60`](../../changes/2_deployable_peak/PLAN.md#L49-L60), [`changes/2_deployable_peak/PLAN.md#L107`](../../changes/2_deployable_peak/PLAN.md#L107), [`changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L42-L48`](../../changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L42-L48), [`changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L64-L79`](../../changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L64-L79), [`changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L81-L99`](../../changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L81-L99), [`changes/SCOPE_v2.md#L23`](../../changes/SCOPE_v2.md#L23), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L1-L13`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L1-L13), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L16-L19`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L16-L19)

<a id="F74"></a>
### F74 [P2] [INFRA] Each deployed test's evaluator was written and validated on earlier data before the test data existed, and the drivers refused to run without a go-file
- **WP3.** `evaluate_test.py` was written at 16:50 on 2026-10-04, before any test data. Run on WP2's dev trials, it reproduces the dev comparisons exactly (X1 vs A +1.301 ± 0.251, 6/8). The test driver refused to start without the go-file G3_SIGNED. That file is untracked in git, and its one line is the captain's *waiver* of G3, not a sign-off: "G3 waived by captain Sixue Xing 2026-10-05 (SCOPE_v2 §1a, commit 84a0c1d); PATCH.diff sha256 2a914eb589bb" (copied into [`changes/4_story/result/untracked_evidence.txt`](../../changes/4_story/result/untracked_evidence.txt); [F76](#F76)).
- **WP9.** Its evaluator, checked on WP3's published trials, reproduces the WP3 report (A+α vs A +0.965, 5/6, SE 0.160 / 0.391; X1 vs A −1.265). The driver required `TEST_GO`, created by the coordinator after the protocol commit.
- **WP10.** Its evaluator, checked on WP9's trials, reproduces WP9 (A+α vs A 5/6, +1.155, SE 0.094 / 0.745; B+α vs B 6/6, +1.887).
- **Auto-research T2.** The evaluator is identical to the contract's `validate.py`.

**Why this priority:** it makes "the analysis was tuned to the outcome" unlikely as an explanation of a test verdict. Two exceptions, where rules were edited after non-outcome test-instance data or confirmation data existed, are disclosed in [F53](#F53) and [F83](#F83).
Refs: [`changes/2_deployable_peak/wp3_test/PROGRESS.md#L1-L4`](../../changes/2_deployable_peak/wp3_test/PROGRESS.md#L1-L4), [`changes/2_deployable_peak/wp3_test/PROGRESS.md#L36-L39`](../../changes/2_deployable_peak/wp3_test/PROGRESS.md#L36-L39), [`changes/2_deployable_peak/wp3_test/PROGRESS.md#L81`](../../changes/2_deployable_peak/wp3_test/PROGRESS.md#L81), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L3`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L3), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L82`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L82), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L67`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L67), [`changes/4_story/result/untracked_evidence.txt`](../../changes/4_story/result/untracked_evidence.txt), [`changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L44-L51`](../../changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L44-L51)

<a id="F75"></a>
### F75 [P1] [INFRA] Phase-1 pre-registration (Q1–Q3) is file-dated, not git-attested
**What the files say.**
- [`changes/1_literature_review/explore/PROTOCOL.md`](../../changes/1_literature_review/explore/PROTOCOL.md) states "Frozen: 2026-09-28, before any tuning".
- The finalist rules are timestamped inside progress logs (Q3 rule at 19:35; Q2 simulation plan at 17:00).
- Q3 ran 2026-09-28 15:53 → 2026-09-29 02:30; the Q2 held-out campaign started 18:25.
- Track B states "No git commits".

**What git says.** The first commit containing the protocol is `be284a3` (2026-09-29 15:02:03), after these runs.

**Consequence.** The Q1–Q3 verdicts are credible as pre-specified held-out evaluations, but their pre-registration cannot be verified from git.
**Why this priority:** it qualifies three P0 verdicts (including the headline positive Q1) without changing them.
Refs: [`changes/1_literature_review/explore/PROTOCOL.md#L3`](../../changes/1_literature_review/explore/PROTOCOL.md#L3), [`changes/1_literature_review/explore/q3/RESULTS.md#L3`](../../changes/1_literature_review/explore/q3/RESULTS.md#L3), [`changes/1_literature_review/explore/q2/RESULTS.md#L77`](../../changes/1_literature_review/explore/q2/RESULTS.md#L77), [`changes/1_literature_review/explore/q2/RESULTS.md#L338-L341`](../../changes/1_literature_review/explore/q2/RESULTS.md#L338-L341), [`changes/1_literature_review/explore/q3/PROGRESS.md#L79`](../../changes/1_literature_review/explore/q3/PROGRESS.md#L79), [`changes/1_literature_review/explore/q2/PROGRESS.md#L38`](../../changes/1_literature_review/explore/q2/PROGRESS.md#L38), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt)

<a id="F96"></a>
### F96 [P2] [INFRA] Phase-1 forking paths and interim looks: the formulation switch also preceded Q1 (YES); all the others were followed by negative verdicts
**The Q2 formulation switch.**
- F2b (squared hinge) was first declared the primary Q1/Q2 formulation, "chosen because it is quadratic … and Ising-native".
- After dev tuning, F1 was chosen instead because it put the "Ising ahead at 10 s on both dev instances; F2b favours the classical LS".
- The choice used dev data only, before any held-out run. Q2 failed anyway ([F20](#F20)).
- **It also fixed the formulation on which Q1 passed ([F18](#F18)).** It was decided on the solver race, not on the peak gain. F2b's own dev selections also simulated 6.0–7.3 points below Baleen's peak-blind OPT (recomputed): pgreedy / LS / PT 28.53 / 28.47 / 28.53 (Region7) and 28.26 / 28.28 / 28.24 (Region6), vs 34.52 / 35.56. So Q1 is unlikely to depend on the switch.

**The Q3 finalist pool grew after the 19:35 rule.**
- The rule named candidates T5, TK10, T2 and L5.
- P0 reps 2–3 were queued at 20:42 ("P0 rep1 heading to ~38.7 on R7"), and C2 reps 2–3 at 20:58 ("C2 rep1 R7 38.89"), to meet the eligibility bar.
- Both became finalists. Q3 failed for all three ([F33](#F33)).

**Interim looks.**
- Q2: interim tables at 3/6 and 4/6 held-out instances. After instance 4 the objective criterion was "decided as FAIL", and the remaining runs completed the tables.
- Q3: a preliminary held-out evaluation at 27/54 runs ("Q3 is heading to NO").
- No configuration or rule change followed either look.

**Why this priority:** disclosed choices that favoured Ising on dev. None changed a held-out verdict, and the one positive verdict downstream of a switch (Q1) is unlikely to depend on it.
Refs: [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/1_literature_review/explore/q2/PROGRESS.md#L31-L32`](../../changes/1_literature_review/explore/q2/PROGRESS.md#L31-L32), [`changes/1_literature_review/explore/q2/PROGRESS.md#L50-L53`](../../changes/1_literature_review/explore/q2/PROGRESS.md#L50-L53), [`changes/1_literature_review/explore/q2/PROGRESS.md#L95-L99`](../../changes/1_literature_review/explore/q2/PROGRESS.md#L95-L99), [`changes/1_literature_review/explore/q3/PROGRESS.md#L79-L96`](../../changes/1_literature_review/explore/q3/PROGRESS.md#L79-L96), [`changes/1_literature_review/explore/q3/PROGRESS.md#L126-L131`](../../changes/1_literature_review/explore/q3/PROGRESS.md#L126-L131)

<a id="F97"></a>
### F97 [P2] [INFRA] Deployed testing went beyond PLAN's instance plan, each time under its own protocol; the later G1 re-runs used one trace
**Regions.** PLAN restricted deployed runs to Region7/6. Region4 and Region5 were "offline only. Use them for deployed runs only if the dev results justify it". Later tests went further, each under its own protocol committed first ([F73](#F73)):
- H4 ran deployed on Region5 (PLAN_C §6, PROTOCOL_v2_H4);
- H5 on Region1, which is in no plan;
- the auto-research T1/T2 on Region2 and Region4, under the loop's contract.

**G1 re-runs.** G1_v3, G1_v4 and G1_v5 checked default equivalence on Region7 s0 only. CP1's G1 covered both Region7 and Region6 s0.
**Why this priority:** plan deviations a reader should know about; none bypassed a protocol.
Refs: [`changes/2_deployable_peak/PLAN.md#L27-L31`](../../changes/2_deployable_peak/PLAN.md#L27-L31), [`changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L57-L66`](../../changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L57-L66), [`changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L105-L108`](../../changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L105-L108), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L20-L27`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L20-L27), [`changes/3_autoresearch/documents/GOOD_RESULT.md#L20-L24`](../../changes/3_autoresearch/documents/GOOD_RESULT.md#L20-L24), [`changes/2_deployable_peak/wp10_schedule/G1_v3.md#L1-L6`](../../changes/2_deployable_peak/wp10_schedule/G1_v3.md#L1-L6), [`changes/3_autoresearch/work/cls_table/G1_v4.md#L1-L5`](../../changes/3_autoresearch/work/cls_table/G1_v4.md#L1-L5), [`changes/3_autoresearch/work/union/G1_v5.md#L1-L5`](../../changes/3_autoresearch/work/union/G1_v5.md#L1-L5), [`changes/2_deployable_peak/wp0_overlay/CP1.md#L5-L17`](../../changes/2_deployable_peak/wp0_overlay/CP1.md#L5-L17)

<a id="F76"></a>
### F76 [P1] [INFRA] Gate G3 (a teammate review of the overlay patch) was waived by the captain; no teammate sign-off is recorded for scope v2
Scope v2 required one teammate to review `PATCH.diff` before any held-out run (G3). G3 was also a WP0 exit criterion in PLAN and the first listed prerequisite of the H3′ protocol.
- It was waived by the captain on 2026-10-05 (commit `84a0c1d`), recorded before the WP3 test. The driver's go-file G3_SIGNED (untracked) contains that waiver text, quoted in [F74](#F74).
- The coordinator review at CP1, G1 and parity stand.
- `PATCH.diff` sha256 `2a914eb589bb` itself was unchanged through WP9 and WP10. But WP10 ran on a later overlay, `PATCH_v3.diff` = `PATCH.diff` + 4 files, +43/−1 lines, and the auto-research ran on overlays v4 and v5 built on top of that.
- Those later overlays had only automated bit-exact equivalence gates (G1_v3/v4/v5 and their extra reproduction checks), no human review. None of the three amendments requires a teammate (G3-type) review, and none is recorded ([F04](#F04)).

[`changes/SCOPE_v2.md`](../../changes/SCOPE_v2.md) still reads "pending confirmation by Ching-Hao Chiu and Jie Fu". The amendments were recorded by the coordinator under the captain's standing approval (1.2b) or not at all (1.2c, 1.2d; [F04](#F04)).
**Why this priority:** it is a governance deviation that a reader must know about; it touches every scope-v2 result.
Refs: [`changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md#L15`](../../changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md#L15), [`changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md#L21`](../../changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md#L21), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L11`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L11), [`changes/3_autoresearch/work/cls_table/SCOPE_AMENDMENT.md#L34-L37`](../../changes/3_autoresearch/work/cls_table/SCOPE_AMENDMENT.md#L34-L37), [`changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md#L28-L31`](../../changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md#L28-L31), [`changes/SCOPE_v2.md#L3`](../../changes/SCOPE_v2.md#L3), [`changes/SCOPE_v2.md#L40-L44`](../../changes/SCOPE_v2.md#L40-L44), [`changes/SCOPE_v2.md#L50`](../../changes/SCOPE_v2.md#L50), [`./RESEARCH.md#L76`](../../RESEARCH.md#L76), [`changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md#L1-L5`](../../changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md#L1-L5), [`changes/2_deployable_peak/PLAN.md#L41`](../../changes/2_deployable_peak/PLAN.md#L41), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L123-L125`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L123-L125), [`changes/4_story/result/untracked_evidence.txt`](../../changes/4_story/result/untracked_evidence.txt), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L4`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L4), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L52`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L52), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L41`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L41), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt)

<a id="F77"></a>
### F77 [P3] [INFRA] Frozen-artifact checks always passed and sandboxing was the rule (with the exceptions in F78–F82); leak-check hits came from other tools and agents
**Frozen artifact.** Every stage reports `check_frozen.sh` → "frozen OK (94 files)": reproduction, Q2, Q3, harness_eval, CP1, WP2, WP5, WP3, Track C, WP9, WP10, and the auto-research T1/T2.

**Sandboxing rules:**
- every Baleen process under `bwrap` with a private `/tmp`;
- one `train` at a time (flock);
- timing on cores 0–7, with SMT siblings 12–19 kept idle from 2026-10-01 16:22 (before that, see [F80](#F80));
- envs used read-only.

**Leak-check hits outside the project** came from other tools and agents:
- the editor, Copilot and desktop files;
- an unrelated user project;
- git activity by the coordinator or another agent: 25 .git/objects files at CP1, 101 at WP5 dev, 318 at H2′, and 371 files under `.git/` at WP2.

**Why this priority:** routine hygiene; recorded for completeness.
Refs: [`./RESEARCH.md#L96-L116`](../../RESEARCH.md#L96-L116), [`changes/0_reproduce/RESULTS.md#L69`](../../changes/0_reproduce/RESULTS.md#L69), [`changes/1_literature_review/explore/q2/RESULTS.md#L342`](../../changes/1_literature_review/explore/q2/RESULTS.md#L342), [`changes/1_literature_review/explore/q3/RESULTS.md#L318-L321`](../../changes/1_literature_review/explore/q3/RESULTS.md#L318-L321), [`changes/1_literature_review/harness_eval/RESULTS.md#L280`](../../changes/1_literature_review/harness_eval/RESULTS.md#L280), [`changes/2_deployable_peak/wp0_overlay/CP1.md#L141-L160`](../../changes/2_deployable_peak/wp0_overlay/CP1.md#L141-L160), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L405`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L405), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L430-L440`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L430-L440), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L189-L195`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L189-L195), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L263-L281`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L263-L281), [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L78`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L78), [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L108`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L108), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L52`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L52), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L39`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L39), [`changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L105`](../../changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L105), [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L61`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L61)

<a id="F78"></a>
### F78 [P3] [INFRA] Phase-1 incidents: a 25-second tuning overlap and a stray `__pycache__` file in the frozen tree's wrapper
1. **Tuning overlap.** A chained launcher's `pgrep` pattern containing '{' failed and started F1 tuning concurrently with the F2b tuner on cores 0–7 for ~25 s.
   - The 8 overlapping rows are kept and flagged `contaminated_overlap`.
   - The affected studies were deleted and re-run.
2. **Stray `__pycache__` file.** An interactive inspection created the file 0_reproduce/repro/__pycache__/common.cpython-311.pyc at 15:54, before the sandbox was sourced.
   - It was removed at 16:06 and the directory mtime restored.
   - `check_frozen.sh` was OK before and after.
3. **Synthetic-audit leak check** (not empty; 72 lines), attributed to other processes. It includes [`changes/1_literature_review/ising_followup/survey.md`](../../changes/1_literature_review/ising_followup/survey.md), "presumably written by another agent". The auditor could not prove the attribution of the fontconfig caches.

**Why this priority:** disclosed incidents with no effect on any verdict.
Refs: [`changes/1_literature_review/explore/q2/RESULTS.md#L355-L358`](../../changes/1_literature_review/explore/q2/RESULTS.md#L355-L358), [`changes/1_literature_review/explore/q3/RESULTS.md#L310-L314`](../../changes/1_literature_review/explore/q3/RESULTS.md#L310-L314), [`changes/1_literature_review/ising_followup/audit/AUDIT.md#L208-L217`](../../changes/1_literature_review/ising_followup/audit/AUDIT.md#L208-L217), [`./RESEARCH.md#L111`](../../RESEARCH.md#L111)

<a id="F99"></a>
### F99 [P3] [INFRA] harness_eval's operational deviations
- **Threshold convergence.** When the target was not yet bracketed, the loop extrapolated with a secant step instead of converge.py's fixed ±0.02 steps; "It is otherwise the same loop". SCOPE.md mandates converge.py.
- **OpenMP.** `OMP_WAIT_POLICY=PASSIVE` was set for all processes. It changes only the idle-wait behaviour.
- **Replaced retrain.** C2's Region7 rep 2 training returned early ("files already exist") and was replaced by rep 4.
- **Retrain counts** were unequal: R2 had 5 retrains, the other deployed arms 3, and the R0 control 1.

**Why this priority:** disclosed process deviations in a dev-only phase; no verdict depends on them.
Refs: [`changes/1_literature_review/harness_eval/RESULTS.md#L54`](../../changes/1_literature_review/harness_eval/RESULTS.md#L54), [`changes/1_literature_review/harness_eval/RESULTS.md#L80`](../../changes/1_literature_review/harness_eval/RESULTS.md#L80), [`changes/1_literature_review/harness_eval/RESULTS.md#L225-L238`](../../changes/1_literature_review/harness_eval/RESULTS.md#L225-L238), [`changes/1_literature_review/harness_eval/PROGRESS.md#L61-L64`](../../changes/1_literature_review/harness_eval/PROGRESS.md#L61-L64), [`changes/SCOPE.md#L46`](../../changes/SCOPE.md#L46)

<a id="F79"></a>
### F79 [P3] [INFRA] Phase-2 timing incidents (WP1/WP5), handled by superseding, flagging or re-running
1. **Unpinned script on the timing cores.** An unpinned ad-hoc script ran on cores 0–2 on Oct 1, 14:44:30–14:47:40.
   - All WP5 tuning up to then was superseded: 193 rows kept as `superseded_restart`.
   - The WP1 Region4 s0 solves were re-run.
2. **SMT sibling exposure.** The first 1-s dev evaluation ran with Track A on the SMT siblings for the Ising runs only. 192 rows were superseded and the evaluation re-run; conclusions unchanged (LS 23.03 vs PT 23.25).
3. **Foreign processes on cores 0–7.** 63 timing runs had a mean foreign load > 0.2 CPUs: 55 tuning instance-runs, 6 hl-split LP runs and 2 WP1 solves. None was a selected trial; all are kept and flagged.
4. **Scaling driver.** It was launched unpinned and stopped at its affinity assertion before any run.
5. **Analysis script.** The H2′ analysis script got two bug fixes after the runs and before its first output (a pandas column access and an f-string), with no rule change.
6. **Rolling secondary.** It overlapped a short editor-process burst.

**Why this priority:** disclosed; none affected a selected configuration or a verdict.
Refs: [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L406-L425`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L406-L425), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L111-L116`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L111-L116), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L174-L185`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L174-L185), [`./RESEARCH.md#L112-L115`](../../RESEARCH.md#L112-L115)

<a id="F80"></a>
### F80 [P2] [INFRA] SMT-sibling exposure in phase-1 timing and early WP5 tuning, a seed-reuse artefact in tuning, and a lost session
**SMT siblings.** Logical CPUs k and k+12 share a physical core.
- The phase-1 rule (timing on cores 0–7, Baleen sims on 8–23) let simulations run on the SMT siblings of the timing cores. WP5's log notes "phase-1 timings had the same exposure".
- The phase-1 core audit sampled only cores 0–7 (94.5 CPU-s of foreign use in the held-out phase), so the sibling load during the Q2 timing runs is unquantified. Both families ran under the same pinning, but per-family sibling exposure was not measured. In WP5 the same setup did expose the two families *unequally* ([F79](#F79), item 2).
- On Oct 1 Track B pinned its sims to 8–11 and 20–23, and Track A kept off 12–19 from 16:22. The sources disagree on when Track B pinned: 15:05 in WP5's log, 15:00 in WP1's report.
- WP5 tuning still had sibling load. The sources disagree on its size: Ising 2.1 vs classical 1.8 threads on average in RESULTS_dev, but 4.1 vs 3.9 in the progress log. Dev-evaluation, hl-split and label runs had 0.

**Seed reuse.** Trial 0 is each solver's phase-1 configuration, and the TPE sampler is seeded as in phase 1. As a result LS and EIM repeat that configuration and have 11 distinct configurations each; CP-SAT has 10–11 and LP 2, against 12 for PT, MILP, SB and MQ. "Equal trials" therefore means equal trial counts, not equal distinct configurations.

**Lost session.** The coordinator session ended on the evening of Oct 1. The resumable drivers restarted scaling and the extra rolling runs, and nothing was lost or duplicated.

**Why this priority:** it qualifies the timing fairness behind the phase-1 10 s Ising win and the "equal tuning" statement; disclosed in the sources.
Refs: [`changes/2_deployable_peak/wp5_ising/PROGRESS.md#L50-L54`](../../changes/2_deployable_peak/wp5_ising/PROGRESS.md#L50-L54), [`changes/2_deployable_peak/wp5_ising/PROGRESS.md#L66-L71`](../../changes/2_deployable_peak/wp5_ising/PROGRESS.md#L66-L71), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L116`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L116), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L395-L406`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L395-L406), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L423-L425`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L423-L425), [`changes/1_literature_review/explore/q2/RESULTS.md#L348-L354`](../../changes/1_literature_review/explore/q2/RESULTS.md#L348-L354), [`changes/SCOPE_v2.md#L45`](../../changes/SCOPE_v2.md#L45)

<a id="F100"></a>
### F100 [P3] [INFRA] The 10 s label and table solves outside WP5 ran without core isolation; after H2′ the timing cores were released to all tracks
**The timing-isolation flag.**
- Track B created the empty flag file TIMING_IDLE (untracked; mtime 2026-10-03 02:08:54, recorded in [`changes/4_story/result/untracked_evidence.txt`](../../changes/4_story/result/untracked_evidence.txt)) at 01:11 on Oct 3, once its timing runs were done.
- The coordinator deleted it before the H2′ test (01:13:42), and it was re-created at 02:08:5x afterwards. It still exists.
- While it exists, other tracks may use CPUs 0–23.

**Which comparisons were affected.** These later 10 s comparisons ran on shared cores:
- the WP3/WP9 label solves. WP2's label solves ran earlier, before H2′, on cores 8–11 and 20–23 only, alongside Track B's timing work;
- WP10's PT vs CD table fits (`taskset -c 0-23`);
- Track C's PT vs CP-SAT anchored solves;
- the auto-research label solves.

Some ran next to a foreign job holding ~15 of 24 CPUs ([F81](#F81)).

**Which were not.** The WP5 day-1 label-timing table ([F32](#F32)) ran under the exclusive cores-0-7 lock.

**How much it matters.** Contention matters most where the solvers did not reach a common optimum.
- WP10's PT reached the exhaustive optimum.
- The auto-research F1 objectives tie on every test-pool solve and on Region1_s0; on Region5_s0 they differ by 0.16–0.31% (CP-SAT lower on 2 of 3 seeds).
- No objective comparison is recorded for the WP3/WP9 shared-core label solves.

**The main non-optimal 10 s comparison is Track C's anchored energy** ([F70](#F70)), and its two sides ran under different conditions (ledger completion times, recomputed in Appendix D):
- the 24 PT solves (ANC10) finished on 2026-10-05 between 14:40:49 and 14:44:33, before the foreign job started (10-10);
- the 24 CP-SAT solves (ANC10CP) finished on 2026-10-16 between 13:36:49 and 13:41:20, while the foreign job was running (Track C noted it at 14:37 that day).

CP-SAT never proved optimality there, so it may have searched less under contention. How much was not measured.
**Why this priority:** a timing caveat on secondary solver comparisons ([F70](#F70)).
Refs: [`changes/3_autoresearch/result/FINAL_REPORT.md#L78`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L78), [`changes/2_deployable_peak/wp8_trackC/results/ledger_labels.csv`](../../changes/2_deployable_peak/wp8_trackC/results/ledger_labels.csv), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L92-L96`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L92-L96), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L141`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L141), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/2_deployable_peak/wp5_ising/PROGRESS.md#L86-L88`](../../changes/2_deployable_peak/wp5_ising/PROGRESS.md#L86-L88), [`changes/2_deployable_peak/wp5_ising/PROGRESS.md#L94`](../../changes/2_deployable_peak/wp5_ising/PROGRESS.md#L94), [`changes/2_deployable_peak/wp5_ising/PROGRESS.md#L103`](../../changes/2_deployable_peak/wp5_ising/PROGRESS.md#L103), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L186-L188`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L186-L188), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L401-L404`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L401-L404), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L8`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L8), [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L257`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L257), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L10`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L10), [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L105-L107`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L105-L107), [`changes/4_story/result/untracked_evidence.txt`](../../changes/4_story/result/untracked_evidence.txt), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L12-L16`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L12-L16), [`changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L44`](../../changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L44)

<a id="F81"></a>
### F81 [P3] [INFRA] Track C, WP9 and WP10 operational deviations
**Track C:**
- The first stage-2 launch ran un-bwrapped and was killed after 1 minute.
- A restart changed threshold seeding only.
- A foreign job occupied ~15 of 24 CPUs since 10-10, making sims ~4× slower (results are deterministic).
- Track C counted 148 foreign cpython-312/313 `.pyc` files dated 2026-10-10 in the envs' site-packages and left them in place.
- The progress log dates the screen's completion "~23:xx", but its results commit `4ba4bcc` is 2026-10-16 20:27:07, so the logged time is a guess.

**WP9/WP10:**
- WP9 and WP10 each list 125 such files. The sources do not explain the difference from Track C's 148.
- WP10 ran two read-only import checks outside bwrap (17:15).
- WP10's G1_v3 driver hit a thread race and was relaunched.
- WP10's progress-log clock times were corrected from file timestamps at 18:00.

**Why this priority:** minor process deviations, disclosed in the sources.
Refs: [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L102-L110`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L102-L110), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L100-L107`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L100-L107), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L141-L143`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L141-L143), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L51-L56`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L51-L56), [`changes/2_deployable_peak/wp9_region5/PROGRESS.md#L71`](../../changes/2_deployable_peak/wp9_region5/PROGRESS.md#L71), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L6`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L6), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L14`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L14), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L91-L95`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L91-L95)

<a id="F82"></a>
### F82 [P3] [INFRA] Smaller recorded disclosures not listed elsewhere in this story
**Phase-1 Q3.**
- The abandoned SATB10 runs are kept with `matched=False`.
- One dev row (T5 Region7 rep 3) was written by hand from its result file after its driver was stopped.

**Track C.**
- The in-flight training from the un-bwrapped first launch was reused by the resume logic.
- Before H4, the availability of Region5's authors' rows was printed (no P100 values).

**Auto-research** (final report §5):
- `ADDENDUM_R4.md`'s "Written" line was edited once after its commit.
- A supplementary, non-protocol RejectX for T1 was designed after the T1 static outcomes were seen. It is reported only and matched 1/6.
- The Fig 9 Baleen variant labels were read via the authors' `best_baleen_prefetch` rule.
- A notebook claim that CB:pt reproduces TB:pt "on several instances" was true for 1/8.
- The UB-cdm control-twin race fired once (1 `__FAILED_` row, not re-run).
- The cls_table probe and CA/CB control runs were stopped part-way; 7 probe rows and 11 control rows are kept.

**Why this priority:** completeness of the incident record; none affects a verdict.
Refs: [`changes/1_literature_review/explore/q3/RESULTS.md#L315-L317`](../../changes/1_literature_review/explore/q3/RESULTS.md#L315-L317), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L109-L110`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L109-L110), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L132`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L132), [`changes/3_autoresearch/result/FINAL_REPORT.md#L104-L134`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L104-L134)

<a id="F83"></a>
### F83 [P2] [INFRA] WP10 committed its H5 protocol after the dev confirmation had run, before its P100 values were read
**Disclosed deviation.**
- The E3 confirmation driver finished at 19:20.
- `PROTOCOL_v2_H5.md` was committed at 19:23:04 (`2738cba`).
- `e3_eval.py` was run on those rows only inside the chain afterwards.
- Before that run, `e3_eval.py` gained a deterministic tie-break and its `finalist.json` output, after the confirmation data existed but before any of it was read. The tie-break did not decide anything: TB:pt was the only qualifier.
- The finalist (TB:pt) was chosen mechanically by the rule written ≈17:32.

**Header-time inconsistency.** The protocol's own header says it was written at "19:25", after its own commit time. The header time is therefore approximate.
**Why this priority:** a real deviation from "protocol before the data exist", mitigated by a mechanical rule; it matters for H5's evidence label.
Refs: [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L42`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L42), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L1-L7`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L1-L7), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L105-L116`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L105-L116), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt)

<a id="F84"></a>
### F84 [P1] [INFRA] Auto-research integrity disclosures (final report §5)
1. **DEV_RULES timing.** R0–R2 had no git attestation until `96506745` (02:23). Their headers were written with guessed times and rewritten in place with `sed`, contradicting the file's "never edited" line. The final report adds that the worker transcript confirms each rule precedes its simulations; the transcript is not tracked in git, and the round-1 red-team validator checked those times against it.
2. **Post-commit procedure changes.**
   - The T2 chain's T1 condition (`3fdba1b`) was changed after T1's outcomes had been seen. The validators required this change, and it was committed before T2's TEST_GO ([F85](#F85)).
   - `chain_dev2.py` ordering was changed.
   - DEV_RULES R4 and `ADDENDUM_R4.md` came 12 minutes after the union T1 protocol commit, motivated by CB:pt's ineligibility. R4 never fired.
3. **Late union protocol.** The union T1 protocol was committed after 9 of 16 union screen results had been read (large, positive).
4. **T1 design defect.** The constructed Region2_s0.2 row was infeasible at the operating point and was not checked.
5. **T1 static baselines** were unmatched, and the evaluator averages static P100 regardless of `matched`.
6. **Convergence search** stalls on write-rate plateaus and approaches cliffs from one side. The source records it as pre-registered code that "was not changed".
7. **Latent base-model race.** It is fail-closed and never fired (27/27 and 15/15 A trainings audited).
8. **T2 incident.** 8 pre-simulation `__FAILED_` rows.
9. **Non-dev information seen.** Trace-directory sizes, and the existence (no values) of reserve-sample rows in one printed listing.
10. **Bookkeeping errors**, e.g. the G1_v5 report was first written as `G1_v4.md`.
11. **Ledgers rewritten.** The ledgers were rewritten in full rather than appended (red-team round 1, N7). Snapshots were committed, and round 2 verified that every rewrite is lossless.

**Why this priority:** these bear on the credibility of the loop's process. The verdict is negative, so they cannot have inflated a claim.
Refs: [`changes/3_autoresearch/.gitignore#L2`](../../changes/3_autoresearch/.gitignore#L2), [`changes/3_autoresearch/result/FINAL_REPORT.md#L100`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L100), [`changes/3_autoresearch/result/validator_red_team_round_1.md#L24`](../../changes/3_autoresearch/result/validator_red_team_round_1.md#L24), [`changes/3_autoresearch/result/validator_red_team_round_1.md#L105-L106`](../../changes/3_autoresearch/result/validator_red_team_round_1.md#L105-L106), [`changes/3_autoresearch/result/FINAL_REPORT.md#L96-L134`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L96-L134), [`changes/3_autoresearch/result/validator_red_team_round_1.md#L143`](../../changes/3_autoresearch/result/validator_red_team_round_1.md#L143), [`changes/3_autoresearch/result/validator_red_team_round_2.md#L34`](../../changes/3_autoresearch/result/validator_red_team_round_2.md#L34), [`changes/3_autoresearch/work/t2u_region4/ADDENDUM_T1_UNEVALUABLE.md#L1-L24`](../../changes/3_autoresearch/work/t2u_region4/ADDENDUM_T1_UNEVALUABLE.md#L1-L24)

<a id="F85"></a>
### F85 [P3] [INFRA] The round-1 auto-research validators failed the run on two blocking findings; both were fixed before T2's TEST_GO
**B1 (both validators).**
- T1 contained an instance no arm can match. On Region2_s0.2 every arm ends at the θ floor of 1e-4 (admit-all), with WR 11.510 and P100 189.068.
- The committed T2 chain would have halted on T1's missing `good_result`.
- **Fix:** T1 was closed as spent and failed (`539f39e`), and the T2 chain condition was amended (`3fdba1b`), both before T2's TEST_GO.

**B2.** The G1_v5 report had been written under the name `G1_v4.md` by a copied report script. It was renamed (`e45a7fd`).

**Round 2:** both validators PASS with 0 open findings.
**Why this priority:** the validator loop worked as intended; process detail.
Refs: [`changes/3_autoresearch/result/validator_integrity_stats_round_1.md#L118-L170`](../../changes/3_autoresearch/result/validator_integrity_stats_round_1.md#L118-L170), [`changes/3_autoresearch/result/validator_integrity_stats_round_1.md#L273-L274`](../../changes/3_autoresearch/result/validator_integrity_stats_round_1.md#L273-L274), [`changes/3_autoresearch/result/validator_red_team_round_1.md#L32-L40`](../../changes/3_autoresearch/result/validator_red_team_round_1.md#L32-L40), [`changes/3_autoresearch/result/validator_red_team_round_2.md#L106-L107`](../../changes/3_autoresearch/result/validator_red_team_round_2.md#L106-L107), [`changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L229-L230`](../../changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L229-L230), [`changes/3_autoresearch/work/t2u_region4/ADDENDUM_T1_UNEVALUABLE.md#L1-L24`](../../changes/3_autoresearch/work/t2u_region4/ADDENDUM_T1_UNEVALUABLE.md#L1-L24), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt)

<a id="F86"></a>
### F86 [P2] [INFRA] Six items the round-2 validators raised are not carried into the auto-research notebook or final report
Both round-2 validators passed with 0 blocking findings, but list non-blocking items. Checked here against the files:
1. **Interim look.** At 08:18, with 28 of 90 T2 evaluations done, the worker printed per-arm P100 of the completed rows ("report planning only"). `LAB_NOTEBOOK.md` has no entry for it. T2 was fully locked by then, so the verdict is unaffected.
2. **Jaccard ranges.** The ranges in FINAL_REPORT §4 and the T2 report §4 are slightly wrong: CP-SAT goes down to 0.569 on Region4_s0.5.
3. **Retrain from scratch.** One T2 training (B r1, Region4_s0.2) was killed and retrained from scratch. The notebook's 07:07 entry does mention setting aside its partial train log, but §5.8 still says "the same retrains were re-run".
4. **Stale STATUS.** The body of `STATUS.md` is stale below its final header.
5. **Thin classical-control evidence.** The H-CLS evidence (CD tables) is retrain-1 only, n = 1–4 instances per arm, and was never compared. The final report does not say so.
6. **A mislabelled baseline.** FINAL_REPORT §2.2 still says the union did not restore "Baleen's" first-access admission (3.0% vs 8.4%). The 8.4% is A+α; Baleen A is 8.7%.
**Why this priority:** open disclosure gaps in the record; no verdict impact.
Refs: [`changes/3_autoresearch/result/validator_red_team_round_2.md#L55-L90`](../../changes/3_autoresearch/result/validator_red_team_round_2.md#L55-L90), [`changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L158-L203`](../../changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L158-L203), [`changes/3_autoresearch/result/LAB_NOTEBOOK.md#L401-L412`](../../changes/3_autoresearch/result/LAB_NOTEBOOK.md#L401-L412), [`changes/3_autoresearch/result/LAB_NOTEBOOK.md#L417-L446`](../../changes/3_autoresearch/result/LAB_NOTEBOOK.md#L417-L446), [`changes/3_autoresearch/result/FINAL_REPORT.md#L56-L58`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L56-L58), [`changes/3_autoresearch/result/FINAL_REPORT.md#L115`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L115)

<a id="F87"></a>
### F87 [P2] [INFRA] Privacy redaction of a public repo (2026-10-04): git history still holds the originals, and so does the current tree, inside the redaction tool
The repo is public.
- Leak-check listings, CPU audits and notes had included paths and process names from the user's unrelated work: file names only, never contents.
- They were replaced by category labels with [`tools/privacy_scrub.py`](../../tools/privacy_scrub.py) (commit `55a125b`, 2026-10-04). Code, results and numbers are unchanged.
- **Earlier commits still contain the originals.** Purging them needs a history rewrite, which is the captain's decision.
- **The current tree is not clean either.** The tracked [`tools/privacy_scrub.py`](../../tools/privacy_scrub.py) itself contains the redacted patterns as literals and excludes itself from `--check`, so the public tree still exposes them, and a history rewrite alone would not remove them. This story deliberately does not quote the patterns.
- `python3 tools/privacy_scrub.py --check` must print nothing before every push.
**Why this priority:** a disclosure about the repository, not about results.
Refs: [`./RESEARCH.md#L108`](../../RESEARCH.md#L108), [`./RESEARCH.md#L117`](../../RESEARCH.md#L117), [`tools/privacy_scrub.py#L17-L33`](../../tools/privacy_scrub.py#L17-L33), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt)

<a id="F88"></a>
### F88 [P3] [INFRA] Documentation drift in the index file
[`./RESEARCH.md`](../../RESEARCH.md) is partly stale or imprecise:
- It says "Last updated: 2026-10-16" but records 2026-10-19/20 results.
- Its file map lists only wp0/wp1/wp5/wp2 under `2_deployable_peak` and omits WP3/WP8/WP9/WP10 and `3_autoresearch`.
- WP4, WP6 and WP7 are still "to do".
- It states the unverified ≈11.3% ([F08](#F08)) and the "≈70k" dense-SB limit ([F31](#F31)).
- [`changes/SCOPE_v2.md`](../../changes/SCOPE_v2.md) §1a records amendment 1.2b but not 1.2c/1.2d ([F04](#F04)).
**Why this priority:** a reader using the index should know which statements to check; minor.
Refs: [`./RESEARCH.md#L4`](../../RESEARCH.md#L4), [`./RESEARCH.md#L28-L29`](../../RESEARCH.md#L28-L29), [`./RESEARCH.md#L36`](../../RESEARCH.md#L36), [`./RESEARCH.md#L41`](../../RESEARCH.md#L41), [`./RESEARCH.md#L78-L89`](../../RESEARCH.md#L78-L89), [`changes/SCOPE_v2.md#L44`](../../changes/SCOPE_v2.md#L44)

<a id="F89"></a>
### F89 [P3] [INFRA] An earlier auto-research launch (Codex worker, run 20261019_233548) did no work
That run made two auto commits about one minute apart (`74577ee`, `f4d758e`). They changed only the loop status files (validation note "no claim file yet"). The launcher was then replaced by the headless Opus 5.5 launcher (`204bce2`). The reported run is 20261020_004634.
**Why this priority:** completeness of the record; no results.
Refs: [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt), [`changes/3_autoresearch/result/LAB_NOTEBOOK.md#L1-L8`](../../changes/3_autoresearch/result/LAB_NOTEBOOK.md#L1-L8), [`changes/3_autoresearch/README.md#L1-L9`](../../changes/3_autoresearch/README.md#L1-L9)

<a id="F90"></a>
### F90 [P2] [INFRA] The hardware differed from the proposal's plan: no GPU
**Planned:** "16 cores / 32 threads, 125 GiB RAM, one 24 GB GPU".

**Used:** a 24-thread AMD Ryzen 9 9900X with 123 GB and no GPU. The paper-selection desk check had been sized for, and run on, a 16-core Threadripper with a 24 GB RTX A5000 ([F06](#F06)).

**Consequence.** Simulated bifurcation and CIM, which are designed for GPUs and FPGAs, ran only on CPU. The audit notes the slow-per-call arms were "under-converged, not intrinsically worse". Every phase-2 Ising timing result is a CPU result.
**Why this priority:** it limits how far the Ising-solver negatives generalise to GPU or hardware Ising machines.
Refs: [`documents/proposal_docx_compose/proposal.js#L250`](../../documents/proposal_docx_compose/proposal.js#L250), [`changes/1_literature_review/explore/q2/RESULTS.md#L46-L50`](../../changes/1_literature_review/explore/q2/RESULTS.md#L46-L50), [`changes/1_literature_review/ising_followup/audit/AUDIT.md#L195-L198`](../../changes/1_literature_review/ising_followup/audit/AUDIT.md#L195-L198), [`documents/top_doable_papers_filtered.md#L13-L20`](../../documents/top_doable_papers_filtered.md#L13-L20)

<a id="F91"></a>
### F91 [P2] [INFRA] Planned but never measured
- **The artifact's own peak policy.** `PolicyUtilityPeakServiceTimeSize` (oracle peak window) is SCOPE.md's ablation (a), and the proposal's H2 required beating it. No results file reports a run: not measured (search in Appendix D).
- **F3 and F4.** F3 (the eviction-coupled QKP, where an Ising edge was considered most plausible) was not implemented. Q2 was not run on F4.
- **Region coverage.** Offline breadth covered Regions 4–7 only. The proposal's H1 was "averaged over the seven Meta traces"; Regions 1–3 were never run offline.
- **Phase-1 harness test.** Samples 1–9 were not run.
- **Reproduction.** No Stage B+ results are recorded: the convergence loop from scratch and the Baleen no-prefetch ablation ([F98](#F98)).
- **Work packages.** WP4 (mechanism), WP6 (mid-term report) and WP7 (paper) are "to do".
**Why this priority:** these gaps bound the claims; secondary.
Refs: [`changes/SCOPE.md#L63`](../../changes/SCOPE.md#L63), [`documents/proposal_docx_compose/proposal.js#L199-L200`](../../documents/proposal_docx_compose/proposal.js#L199-L200), [`changes/1_literature_review/explore/q2/RESULTS.md#L279-L295`](../../changes/1_literature_review/explore/q2/RESULTS.md#L279-L295), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L17-L23`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L17-L23), [`changes/1_literature_review/harness_eval/RESULTS.md#L276`](../../changes/1_literature_review/harness_eval/RESULTS.md#L276), [`./RESEARCH.md#L29`](../../RESEARCH.md#L29)

<a id="F92"></a>
### F92 [P1] [INFRA] The 0.7–0.9 reserve was never used in a deployed run, but WP1 simulated it offline, including the Region6/7 reserve
**What the plan says** (PLAN §3):
- dev = Region7/Region6 samples 0–0.3;
- test = samples 0.4–0.6;
- "Reserve for the final paper: samples 0.7–0.9, touched once, at the end";
- H1′ breadth: Region4 and Region5, samples 0–0.9, offline only.

**What WP1 did.** WP1 (H1′, committed `08ad0d2` on 2026-10-03) built and simulated *offline* (OPT) instances for Regions 4–7 × samples 0–0.9. That includes the 6 Region6/7 reserve instances (s0.7–0.9) among 12 reserve-sample rows in `wp1_table.csv`.
- PLAN itself scheduled this: H1′ covers "Region4–7 × 10 samples", and WP1 builds "samples 0–0.9". So it was planned, not a deviation, but it means the reserve is offline-known.
- The 12 reserve instance dumps still exist on disk, untracked and git-ignored (`wp1_offline/inst/full_Region{4..7}_s0.{7,8,9}.npz`). PROTOCOL_v2_H5 §2's "No job or instance exists for them" is therefore literally true only of WP10's own area.

**What later protocols say.** PROTOCOL_v2_H3 §2 then lists the reserve as "untouched", which is true only for deployed runs. Every deployed protocol and the auto-research contract exclude the reserve:
- PROTOCOL_v2_H4 §2: "no job, instance dump or label set exists" in WP9's area;
- PROTOCOL_v2_H5 §2;
- auto-research contract §3. The loop's report: "No reserve sample was built or simulated".

**Mitigation.** WP1's offline results on samples ≥ 0.4 were not used for any WP5 choice.

**[`./RESEARCH.md`](../../RESEARCH.md) also says** the reserve is "untouched". That is likewise true only of deployed runs.

**Consequence.** A final deployed confirmation on the reserve is still uncontaminated by any deployed or tuning outcome. Their offline OPT peaks are known, though, so the reserve is not pristine.
**Why this priority:** it qualifies the one remaining clean test set (section 9) and corrects the "untouched" wording in the protocols.
Refs: [`./RESEARCH.md#L121-L124`](../../RESEARCH.md#L121-L124), [`changes/2_deployable_peak/PLAN.md#L19`](../../changes/2_deployable_peak/PLAN.md#L19), [`changes/2_deployable_peak/PLAN.md#L27-L31`](../../changes/2_deployable_peak/PLAN.md#L27-L31), [`changes/2_deployable_peak/PLAN.md#L44`](../../changes/2_deployable_peak/PLAN.md#L44), [`changes/2_deployable_peak/.gitignore#L10`](../../changes/2_deployable_peak/.gitignore#L10), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L1-L3`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L1-L3), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L111-L113`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L111-L113), [`changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`](../../changes/2_deployable_peak/wp1_offline/results/wp1_table.csv), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L29`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L29), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L23`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L23), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L27`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L27), [`changes/3_autoresearch/documents/GOOD_RESULT.md#L34-L35`](../../changes/3_autoresearch/documents/GOOD_RESULT.md#L34-L35), [`changes/3_autoresearch/result/FINAL_REPORT.md#L116-L120`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L116-L120), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt)

<a id="F93"></a>
### F93 [P1] [INFRA] "Fresh" test pools were fresh only in deployed mode: WP1 had simulated the offline OPT of the H2′/H3′, H4 and T2 test instances before those tests
**The plan's rule.** "Test and reserve samples stay untouched until the pre-registration is committed."

**What WP1 ran.** WP1 (committed `08ad0d2`, 2026-10-03 00:11) ran offline OPT selections and simulations on Regions 4–7 × samples 0–0.9. That covers:
- Region6/7 s0.4–0.6: the H2′ and H3′ test instances;
- Region5 s0.1–0.6: the H4 pool;
- Region4 s0.2–0.6: the T2 pool.

Region1 (H5) and Region2 (T1) were never run offline.

**How the sources treat it.**
- **H2′.** Its test instances *are* WP1's dumps, listed with sha256. Its protocol states that WP1's frozen-configuration runs on samples ≥ 0.4 "were not used for any choice here", and WP1 states its results on samples ≥ 0.4 were not used by WP5.
- **H3′ and H4.** Both use WP1's offline OPT values for retention, a pre-declared reported metric ([F48](#F48), [F54](#F54)).
- **H4's protocol** discloses that WP1 used its pool "only OFFLINE".
- **T2's protocol** cites WP1's Region4 headroom as a known caveat.
- **H3′'s protocol** says its test instances were never used "for any tuning, selection or inspection". That is accurate only for deployed runs.

**Assessment.** The offline OPT peak of a peak-blind vs a peak-aware selection is not a deployed outcome, and no deployed configuration was chosen on these data. "Fresh" should nonetheless read "never run deployed".
**Why this priority:** it qualifies the freshness claim behind every deployed test, including the headline H4.
Refs: [`changes/2_deployable_peak/PLAN.md#L116`](../../changes/2_deployable_peak/PLAN.md#L116), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L1-L3`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L1-L3), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L111-L113`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L111-L113), [`changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`](../../changes/2_deployable_peak/wp1_offline/results/wp1_table.csv), [`changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L3-L24`](../../changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L3-L24), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L25-L27`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L25-L27), [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L19-L21`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L19-L21), [`changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L54`](../../changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L54), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt)

## 8. What we can and cannot claim

Status words (closed list; only these are used):
- **Supported:** the evidence meets its stated rule. For a rule-free offline measurement, the measurement shows the claim as worded.
- **Partly supported:** part of the claim meets its rule; the part is named.
- **Refuted:** a pre-registered pass/fail test of the claim failed.
- **Not supported:** the evidence is negative or absent, but there was no pre-registered pass/fail test of this exact claim.
- **Post-hoc:** observed on test data without a pre-registered rule.
- **Hypothesis:** a proposed explanation that was not tested.
- **Not measured:** never run.

| # | Claim | Status | Evidence | Findings | Main refs |
|---|---|---|---|---|---|
| 1 | Baleen's released artifact reproduces the paper | **Partly supported**: baselines bit-exact; Baleen within ±0.6 of released-metric runs; the Fig 9 `tracedrop` bars do not reproduce; "≈11.3%" unverified; sample 0 of two traces only | REPRO | [F07](#F07), [F08](#F08), [F98](#F98) | [`changes/0_reproduce/RESULTS.md#L7-L53`](../../changes/0_reproduce/RESULTS.md#L7-L53) |
| 2 | Min–max (peak-aware) selection lowers the simulated peak offline vs Baleen's peak-blind oracle | **Supported**: 6/6 held-out (27.06 vs 32.28; phase-1 git caveat, [F75](#F75)); 36–37/39 instances, −13.0 to −13.7%; 30/30 and 13.0–17.7% per region on Regions 5–7 | TEST-PREREG (Q1) + OFFLINE | [F18](#F18), [F25](#F25) | [`changes/1_literature_review/explore/q2/RESULTS.md#L12-L20`](../../changes/1_literature_review/explore/q2/RESULTS.md#L12-L20), [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L3-L15`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L3-L15) |
| 3 | …also on Region4, by H1′'s bar (≥ 80% wins, mean ≥ 10%) | **Not supported** by that bar: 6–7/9 wins and 3.0–5.4%, i.e. a small positive effect; headroom gate not met | OFFLINE | [F27](#F27) | [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L11-L15`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L11-L15) |
| 4 | The offline gain is due to the Ising/QUBO solver | **Not supported**: classical LP/CP-SAT selections simulate the same, and the LP start already reaches ≈94% of the analytic reduction | OFFLINE | [F19](#F19), [F24](#F24) | [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L91-L95`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L91-L95), [`changes/1_literature_review/explore/q2/RESULTS.md#L254-L257`](../../changes/1_literature_review/explore/q2/RESULTS.md#L254-L257) |
| 5 | Ising beats classical solvers on the same formulation (10/60/300 s) | **Refuted** (Q2; phase-1 git caveat) | NEGATIVE-TEST | [F20](#F20) | [`changes/1_literature_review/explore/q2/RESULTS.md#L12-L31`](../../changes/1_literature_review/explore/q2/RESULTS.md#L12-L31) |
| 6 | Ising beats classical solvers at tight 1/3/10 s budgets | **Refuted** (H2′) | NEGATIVE-TEST | [F28](#F28) | [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L7-L24`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L7-L24) |
| 7 | Ising samplers are the best family at one short budget | **Post-hoc** (10 s in Q2, 3 s in H2′; not a pass). Rolling re-solves reverse it: on dev at 1 and 3 s, on test at 1 s | TEST-POSTHOC | [F20](#F20), [F28](#F28), [F30](#F30) | [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L138-L165`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L138-L165) |
| 8 | Matrix-free SB scales to real 0.4% unions on CPU where the dense SB package does not | **Supported** (reported contribution, no pass/fail). SB itself was the weakest Ising solver in phase-1 dev tuning and by the WP5 rule; in harness_eval, C4 beat C5 analytically | OFFLINE | [F31](#F31), [F21](#F21) | [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L333-L392`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L333-L392), [`changes/1_literature_review/harness_eval/RESULTS.md#L164-L167`](../../changes/1_literature_review/harness_eval/RESULTS.md#L164-L167) |
| 9 | Ising peak labels survive distillation into Baleen's unchanged GBM | **Refuted** (Q3; phase-1 git caveat) | NEGATIVE-TEST | [F33](#F33) | [`changes/1_literature_review/explore/q3/RESULTS.md#L6-L23`](../../changes/1_literature_review/explore/q3/RESULTS.md#L6-L23) |
| 10 | With the causal `load` feature the GBM can fit peak-aware labels | **Supported** on dev (learnability gate) | DEV | [F37](#F37) | [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L96-L112`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L96-L112) |
| 11 | Ising labels + `load` (+ α) beat Baleen deployed | **Refuted** (H3′). X1 also fails on Region5, where the rule was reported without a pass/fail | NEGATIVE-TEST | [F44](#F44), [F54](#F54) | [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L6-L16`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L6-L16), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L13`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L13) |
| 12 | Ising labels add deployed value beyond the load-adaptive threshold | **Refuted** (H3′-labels; auto-research T2 vs A+α) | NEGATIVE-TEST | [F45](#F45), [F65](#F65) | [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L30-L38`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L30-L38), [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L14-L21`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L14-L21) |
| 13 | An Ising-fitted threshold table beats Baleen deployed | **Refuted** (H5, Region1). The table was neutral on 10/18 test retrains and PT = exhaustive optimum, so this refutes day-1 table fitting, not Ising solving specifically | NEGATIVE-TEST | [F59](#F59) | [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L9-L17`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L9-L17) |
| 14 | Deployment-aware Ising labels (anchored, top-k, student) help | **Not supported** on dev (no finalist); never tested | DEV | [F50](#F50) | [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L6-L20`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L6-L20) |
| 15 | The load-adaptive threshold on Baleen's own models beats Baleen deployed on a fresh region | **Supported** on Region5 (H4) by the pre-registered rule, which uses the retrain-level SE. At instance level: +1.16 ± 0.75 (≈1.5 SE); s0.5 gives 69% of the gain. "Fresh" = never run deployed ([F93](#F93)). Earlier load-based attempts in Baleen and the thesis did not cut, or barely cut (1.4%), the peak ([F95](#F95)) | TEST-PREREG | [F52](#F52), [F53](#F53), [F93](#F93), [F95](#F95) | [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L19`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L19) |
| 16 | …and on other regions | **Post-hoc**: yes on Regions 6/7 and Region4 (Region4 also concentrated); no on Region1; uninformative on Region2 | TEST-POSTHOC | [F47](#F47), [F60](#F60), [F66](#F66), [F69](#F69) | [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60), [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L50-L52`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L50-L52), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19) |
| 17 | The threshold's benefit depends on the load level | **Hypothesis** (WP4); dev Region1_s0 cuts against it | TEST-POSTHOC | [F60](#F60), [F69](#F69) | [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L33-L36`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L33-L36) |
| 18 | Proposal H1 (≥ 5% vs stock Baleen, averaged over 7 traces) | **Partly supported**: offline vs Baleen's own peak-blind oracle, the per-trace mean over the 4 traces measured is 12.8–13.5% (per-region means averaged; recomputed), but Region4 alone gives 3.0–5.4% and Regions 1–3 were not measured. Deployed (Ising labels vs stock Baleen): refuted (H3′) | OFFLINE / NEGATIVE-TEST | [F25](#F25), [F44](#F44), [F91](#F91) | [`documents/proposal_docx_compose/proposal.js#L199`](../../documents/proposal_docx_compose/proposal.js#L199), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt) |
| 19 | Proposal H2 (an Ising solver on a sum-of-squares surrogate beats the artifact's greedy peak policy and a greedy warm start by ≥ 3% Peak DT) | **Not supported**. (a) The artifact's peak policy is **not measured**. (b) The analytic ≥ 3% over the peak-aware greedy holds on dev for every solver, LP included (SB −13.217%, LP −13.172%), so it does not distinguish Ising. On the proposal's simulated Peak DT, SB-on-SoS (harness_eval C4: 27.97 / 27.87) is level with LP + repair (R1: 28.10 / 27.77) and only 1.38–1.96% below the dev peak-aware greedy (28.53 / 28.26; cross-campaign; recomputed in [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt)). The surrogate route was the weakest Ising solver in phase-1 dev tuning and by the WP5 rule ([F21](#F21)) | DEV | [F20](#F20), [F21](#F21), [F91](#F91) | [`documents/proposal_docx_compose/proposal.js#L199-L200`](../../documents/proposal_docx_compose/proposal.js#L199-L200), [`changes/1_literature_review/explore/q2/RESULTS.md#L132-L143`](../../changes/1_literature_review/explore/q2/RESULTS.md#L132-L143), [`changes/1_literature_review/harness_eval/RESULTS.md#L128-L160`](../../changes/1_literature_review/harness_eval/RESULTS.md#L128-L160), [`changes/1_literature_review/explore/q2/PROGRESS.md#L50-L51`](../../changes/1_literature_review/explore/q2/PROGRESS.md#L50-L51) |
| 20 | Proposal H3 (≥ 60% retention online) | **Not supported**: test retention is X1 −0.28 (H3′) and −0.54 (H4), and X2 −0.33; pre-declared metric, no pass/fail | TEST-POSTHOC | [F71](#F71) | [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L75`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L75), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L49`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L49) |
| 21 | An Ising/QUBO-centric component beats deployed Baleen and the threshold arm (auto-research contract) | **Refuted**: T1 unevaluable, T2 failed vs A+α; budget exhausted | NEGATIVE-TEST | [F64](#F64), [F65](#F65) | [`changes/3_autoresearch/result/FINAL_REPORT.md#L1-L7`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L1-L7) |
| 22 | Ising and classical solvers return the same objective where both reach the optimum | **Supported** (exact ties on floored instances, WP10 tables, auto-research F1 labels) | OFFLINE | [F57](#F57), [F70](#F70) | [`changes/3_autoresearch/result/FINAL_REPORT.md#L77-L94`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L77-L94), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L82-L86`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L82-L86) |
| 23 | The deployed P100 of PT- vs CP-SAT-label arms differs systematically | **Not supported**: a two-way record. Only WP2's X1 row reaches ≈2.1 instance-level SE; at retrain level three rows exceed 2 SE (two dev rows favouring PT, one test row favouring CP-SAT). The F1 objectives tie where compared (exactly in the auto-research test-pool solves); Track C's anchored-energy row does not | DEV + TEST-POSTHOC | [F70](#F70) | [`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L14`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L14), [`changes/3_autoresearch/result/FINAL_REPORT.md#L80-L89`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L80-L89) |

**Summary for a paper:**
- The min–max *formulation* is a robust offline win: ≈16% pooled over Regions 5–7 (13.0–17.7% per region), little on Region4.
- Ising/QUBO solvers tie classical solvers where both reach the optimum. They win only at one short budget per test (10 s; 3 s) and lose at 1 s, at 60/300 s and in rolling re-solves; no pre-registered solver test passed.
- The Ising peak labels did not survive deployment in any pre-registered test.
- The only pre-registered deployed gain, −3.2% on fresh Region5 (fresh = never run deployed; prior load-based attempts: [F95](#F95)), comes from a load-adaptive admission threshold on Baleen's own models. It passed on the retrain-level SE, but at instance level it is ≈1.5 SE and one instance carries 69% of it.

## 9. Open questions and next steps

1. **The reserve is unused for deployment.**
   - Samples 0.7–0.9 have never been used in a deployed run.
   - WP1 did simulate them offline (OPT) for H1′ on Regions 4–7, including the Region6/7 reserve, and their dumps are on disk ([F92](#F92)).
   - All deployed test pools except H5's Region1 and T1's Region2 were likewise offline-known ([F93](#F93)).
   - PLAN.md reserves the samples for one final use ([`changes/2_deployable_peak/PLAN.md#L28-L31`](../../changes/2_deployable_peak/PLAN.md#L28-L31)).
2. **What a final confirmation should test** (recommendation, not a pre-registration):
   - **The arm:** the only surviving claim, the load-adaptive threshold (A+α, and B+α) vs A and B, with α = −1 and ref = 20 frozen.
   - **Where:** on the reserve of the regions with peak pressure (Region5, Regions 6/7, Region4), committed before any run.
   - **The margin rule:** require the instance-level SE as well as the retrain-level one, and report the largest instance's share, because H4 passed only on the retrain-level SE and was concentrated ([F53](#F53)).
   - **Load dependence:** state it explicitly as a hypothesis ([F69](#F69)).
   - **Pool feasibility:** check it first (admit-all write rate ≥ target; static-baseline knob sensitivity), as the auto-research report recommends after the T1 defect ([`changes/3_autoresearch/result/FINAL_REPORT.md#L136-L140`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L136-L140)).
3. **Prior art and novelty:**
   - compare A+α directly with the two earlier load-based attempts (Baleen §5.6; thesis §7.4.1, on Region3);
   - finish the outstanding cited-by/patent novelty search before any novelty sentence ([F95](#F95)).
4. **WP4 mechanism work is still open** ([`./RESEARCH.md#L122`](../../RESEARCH.md#L122); per-window attribution is in [`changes/2_deployable_peak/PLAN.md#L74-L77`](../../changes/2_deployable_peak/PLAN.md#L74-L77)):
   - per-window attribution of the peak;
   - why B+α is more uniform than A+α on Region5 ([`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L17`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L17));
   - the scan-vs-burst classification of peak windows across regions;
   - how Baleen's first-15-accesses trainer handles scans ([F68](#F68)).
5. **What an Ising/QUBO contribution would need** ([`changes/3_autoresearch/result/FINAL_REPORT.md#L140`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L140)): a mechanism the threshold cannot reach, or a workload whose peaks are scans present in the training day. Candidates never built:
   - the eviction-coupled QKP F3 ([`changes/1_literature_review/explore/q2/RESULTS.md#L281-L288`](../../changes/1_literature_review/explore/q2/RESULTS.md#L281-L288));
   - GPU or hardware Ising machines ([F90](#F90)).
6. **Never measured** ([F91](#F91)):
   - the artifact's own peak policy;
   - Regions 1–3 offline;
   - F4 in the solver comparison;
   - harness samples 1–9;
   - reproduction Stage B+ ([F98](#F98)).
7. **Tooling debts:**
   - the convergence search stalls on write-rate plateaus;
   - `validate.py` trusts `matched` and averages unmatched static rows ([`changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L204-L214`](../../changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L204-L214));
   - the auto-research notebook lacks the interim-look entry ([F86](#F86));
   - `TIMING_IDLE` left solver comparisons without core isolation ([F100](#F100)); Track C's PT vs CP-SAT anchored comparison would need both sides re-solved under the same conditions before it can count.
8. **Governance:**
   - teammate confirmation of scope v2 and G3 ([F76](#F76)), and a review of the later overlays `PATCH_v3`–v5 on which H5 and the auto-research tests ran ([F04](#F04));
   - PLAN's dev-signal gate decision, recorded after the fact ([F94](#F94));
   - recording amendments 1.2c/1.2d in [`changes/SCOPE_v2.md`](../../changes/SCOPE_v2.md) if any of their results is ever cited as more than a negative;
   - the privacy decision ([F87](#F87)): a history rewrite alone is not enough, because the redaction tool in the current tree still contains the patterns.
9. **Deliverables:** the mid-term talk/report (WP6) and the paper (WP7) are still "to do" ([`./RESEARCH.md#L29`](../../RESEARCH.md#L29)).

## Appendix A. Per-experiment tables (copied from the cited sources)

## A.1 Reproduction, Figure 9 bars at sample 0 ([`changes/0_reproduce/work/results/fig9_summary.md#L20-L29`](../../changes/0_reproduce/work/results/fig9_summary.md#L20-L29))

Note: the "ours" Baleen values (43.27, 40.06) are single replays of the `tracedrop` rows, at WR 33.879 and 38.578. The Region7 run fails the ±5% WR check, and the file's overall verdict is "NOT PASSED" ([`changes/0_reproduce/work/results/fig9_summary.md#L9-L14`](../../changes/0_reproduce/work/results/fig9_summary.md#L9-L14), `#L36-L38`). The matched-WR comparison is the second table.

| trace | policy | prefetch | author | ours | Δ | spread of authors' runs | pass |
|---|---|---|---|---|---|---|---|
| 20230325/Region6 | Baleen | All on Partial Hit | 41.31 | 43.27 | +1.96 | 0.00 | PASS |
| 20230325/Region6 | CoinFlip | No prefetching | 44.42 | 43.45 | -0.98 | 1.95 | PASS |
| 20230325/Region6 | RejectX | No prefetching | 42.59 | 42.32 | -0.26 | 0.53 | PASS |
| 20230325/Region7 | Baleen | ML-Range on ML-When | 37.59 | 40.06 | +2.47 | 0.00 | FAIL |
| 20230325/Region7 | CoinFlip | No prefetching | 49.71 | 48.96 | -0.75 | 1.50 | PASS |
| 20230325/Region7 | RejectX | No prefetching | 41.59 | 42.46 | +0.86 | 1.73 | PASS |

Released-metric Baleen runs ([`changes/0_reproduce/RESULTS.md#L28-L33`](../../changes/0_reproduce/RESULTS.md#L28-L33)):

| Trace | Prefetching | Authors' peak (write rate) | Ours at matched write rate | Δ |
|---|---|---|---|---|
| Region7 | ML-Range on Partial Hit | 40.57 (34.67) | 40.03 (35.46) | −0.54 |
| Region7 | ML-Range on Every Miss | 42.56 (35.23) | 42.91 (35.58) | +0.35 |
| Region6 | ML-Range on Partial Hit | 42.00 (35.27) | 42.21 (35.41) | +0.21 |
| Region6 | ML-Range on Every Miss | 43.89 (36.01) | 43.38 (35.86) | −0.51 |

## A.2 Phase 1, Q1 and the Q2 simulation clause, 300 s selections ([`changes/1_literature_review/explore/q2/RESULTS.md#L259-L269`](../../changes/1_literature_review/explore/q2/RESULTS.md#L259-L269))
| instance | PT P100 (3 seeds) | EIM P100 (3 seeds) | best classical at 300 s: P100 | Baleen peak-blind OPT | PT − OPT |
|---|---|---|---|---|---|
| Region7_s0.1 | 27.61 ± 0.16 | 27.34 ± 0.22 | cpsat 27.38 | 33.68 | −6.07 |
| Region7_s0.2 | 27.90 ± 0.54 | 28.02 ± 0.18 | milp 28.21 | 35.28 | −7.38 |
| Region7_s0.3 | 26.76 ± 0.21 | 26.49 ± 0.31 | cpsat 26.64 | 31.23 | −4.47 |
| Region6_s0.1 | 26.41 ± 0.20 | 25.94 ± 0.39 | cpsat 26.11 | 30.90 | −4.49 |
| Region6_s0.2 | 26.38 ± 0.11 | 26.54 ± 0.24 | cpsat 26.23 | 30.62 | −4.23 |
| Region6_s0.3 | 27.32 ± 0.17 | 27.38 ± 0.08 | cpsat 27.15 | 31.96 | −4.64 |
| **mean** | **27.063** | **26.951** | **26.954** | **32.277** | **−5.21** |

Q2 mean objective per method over the 6 held-out instances ([`changes/1_literature_review/explore/q2/RESULTS.md#L200-L211`](../../changes/1_literature_review/explore/q2/RESULTS.md#L200-L211)):

| method | family | 10 s | 60 s | 300 s |
|---|---|---|---|---|
| pt | Ising | 22.524 | 22.508 | 22.503 |
| eim | Ising | 22.553 | 22.502 | 22.463 |
| ls | classical | 22.569 | 22.462 | 22.434 |
| cpsat | classical | 22.689 | 22.418 | 22.313 |
| milp | classical | 22.958 | 23.582 | 22.763 |
| lp | classical | 23.039 | 23.039 | 23.001 |
| pgreedy | classical | 26.693 | 26.693 | 26.693 |
| greedy (Baleen order + repair) | classical | 31.816 | 31.816 | 31.816 |

## A.3 Phase 1, Q3 held-out verdict ([`changes/1_literature_review/explore/q3/RESULTS.md#L11-L17`](../../changes/1_literature_review/explore/q3/RESULTS.md#L11-L17))
| finalist | wins vs Baleen online (need ≥ 4/6) | mean improvement (need > 2 SE) | mean P100 vs RejectX 39.05 / CoinFlip 44.69 | Q3 |
|---|---|---|---|---|
| P0 pure soft peak (LSE) | 2/6 | −0.41 vs 2 SE = 0.56 | 37.97 | NO |
| T2 LSE + DT blend + trust region | 2/6 | −1.07 vs 2 SE = 0.85 | 38.62 | NO |
| C2 T2 energy over GBM-feature cells | 2/6 | −0.57 vs 2 SE = 0.96 | 38.13 | NO |

Per-instance means (3 matched retrains; T2 has 2 on Region7 s0.2) ([`changes/1_literature_review/explore/q3/RESULTS.md#L196-L233`](../../changes/1_literature_review/explore/q3/RESULTS.md#L196-L233)):

| instance | Baleen online | P0 | T2 | C2 | RejectX | CoinFlip |
|---|---|---|---|---|---|---|
| Region7_s0.1 | 36.57 | 36.11 | 38.39 | 36.68 | 38.66 | 46.00 |
| Region7_s0.2 | 36.79 | 36.89 | 36.69 | 37.05 | 38.00 | 41.97 |
| Region7_s0.3 | 37.81 | 38.50 | 41.39 | 38.08 | 38.89 | 45.19 |
| Region6_s0.1 | 40.93 | 41.66 | 42.28 | 44.06 | 42.25 | 50.02 |
| Region6_s0.2 | 36.26 | 37.74 | 36.29 | 36.14 | 37.29 | 43.85 |
| Region6_s0.3 | 36.96 | 36.90 | 36.70 | 36.75 | 39.19 | 41.09 |

## A.4 WP1, H1′ by region (recomputed from [`changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`](../../changes/2_deployable_peak/wp1_offline/results/wp1_table.csv); output [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt))
| method | all 39: wins / mean reduction | Region4 (9) | Regions 5–7 (30) |
|---|---|---|---|
| LP + repair | 36 / 13.03% | 6 / 4.59% | 30 / 15.57% |
| CP-SAT 300 s | 36 / 13.15% | 6 / 3.04% | 30 / 16.19% |
| PT 300 s | 37 / 13.69% | 7 / 5.37% | 30 / 16.18% |

## A.5 H2′ test, per-budget means over the 6 test instances ([`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L29-L39`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L29-L39))
| method | family | 1 s | 3 s | 10 s |
|---|---|---|---|---|
| pt | Ising finalist | 22.9996 | 22.6008 | 22.6004 |
| eim | Ising finalist | 23.2044 | 22.7158 | 22.6036 |
| lp | classical | 24.6935 | 23.0888 | 23.0888 |
| milp | classical | 24.6690 | 22.8303 | 22.7991 |
| cpsat | classical | 24.6759 | 22.9688 | 22.6382 |
| ls | classical | 22.8335 | 22.7589 | 22.6222 |
| best classical per cell | – | 22.8335 | 22.7157 | 22.6006 |

(The greedy and pgreedy rows, 32.6532 and 26.7305 at every budget, are omitted.)

## A.6 WP2 dev, mean P100 over 8 dev instances ([`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L138-L153`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L138-L153))
| config | mean | config | mean |
|---|---|---|---|
| A | 38.50 | X1 Ea-1.0:F1PT | 37.20 |
| B | 38.44 | X2 Ea-0.5:F1PT | 37.84 |
| C:F1PT | 38.81 | Ea-1.0:F1CPSAT | 38.46 |
| D:F1PT | 38.37 | A+α (Aa-1.0) | 37.88 |
| C:F1EIM | 39.09 | B+α (Ba-1.0) | 38.43 |
| D:F1EIM | 38.46 | B with α = −0.5 (Ba-0.5) | 38.05 |
| Dc:F1CPSAT | 38.74 | RejectX / CoinFlip | 39.88 / 45.07 |

## A.7 H3′ test, P100 per instance ([`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L18-L28`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md#L18-L28))
| instance | A | B | A+α | B+α | X1 | X2 | Dc+α | RejectX | CoinFlip |
|---|---|---|---|---|---|---|---|---|---|
| Region6 s0.4 | 37.58 | 37.43 | 36.12 | 36.57 | 36.93 | 37.36 | 37.36 | 38.56 | 45.07 |
| Region6 s0.5 | 38.75 | 38.95 | 37.50 | 38.17 | 37.24 | 38.00 | 37.61 | 37.96 | 44.68 |
| Region6 s0.6 | 43.04 | 42.94 | 43.79 | 42.72 | 42.02 | 42.01 | 41.91 | 47.21 | 58.04 |
| Region7 s0.4 | 39.51 | 39.86 | 38.66 | 38.71 | 37.20 | 37.78 | 37.57 | 39.29 | 49.24 |
| Region7 s0.5 | 39.07 | 38.31 | 36.95 | 37.05 | **52.30** | **52.15** | 47.49 | 42.05 | 51.60 |
| Region7 s0.6 | 37.65 | 37.55 | 36.80 | 37.05 | 37.51 | 37.96 | 35.91 | 39.31 | 43.19 |
| **mean** | 39.27 | 39.17 | **38.30** | 38.38 | 40.53 | 40.88 | 39.64 | 40.73 | 48.64 |

## A.8 Track C stage 2, rep-1 screen ([`changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md#L7-L18`](../../changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md#L7-L18))

The D8 rows are the same retrains without α (not eligible). The sources disagree on which variant trained:
- RESULTS_dev calls the D8 variant "sim-only" ([`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L23-L25`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L23-L25));
- the progress log says D8 trains and E8 is sim-only ([`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L126-L127`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L126-L127)).

The numbers are unaffected.

| config | mean (8 dev) | S1 | d_i > 0 |
|---|---|---|---|
| X1 (r1) | 37.07 | | |
| A+α (r1) | 37.86 | | |
| D8:ANC10 | 39.07 | −2.548 | 2/8 |
| D8:ANC10CP | 38.52 | −2.001 | 2/8 |
| D8:ANC3 | 37.96 | −1.443 | 4/8 |
| D8:STU10R1 | 37.37 | −0.854 | 3/8 |
| E8:ANC10 | 38.32 | −1.801 | 4/8 |
| E8:ANC10CP | 37.46 | −0.937 | 3/8 |
| E8:ANC3 | 37.36 | −0.843 | 4/8 |
| E8:STU10R1 | 36.78 | −0.257 | 3/8 |

## A.8b Track C stage 1, design table ([`changes/2_deployable_peak/wp8_trackC/results/stage1_table.md#L11-L26`](../../changes/2_deployable_peak/wp8_trackC/results/stage1_table.md#L11-L26))

Offline columns are on the day-1 instances. PL is the proxy, which failed its validation and is a diagnostic only.

| design | day-1 peak | #labels | J vs Baleen | stability J | zero-value | learnability net | PL α=−1 |
|---|---|---|---|---|---|---|---|
| Baleen | 28.14 | 1790 | 1.000 | 1.000 | 0.0 | 0.001 ± 0.003 | 35.92 ± 0.34 |
| F1PT | 21.51 | 1130 | 0.428 | 0.759 | 0.0 | 0.041 ± 0.018 | 35.02 ± 0.56 |
| F1CPSAT | 21.51 | 1181 | 0.459 | 0.743 | 0.0 | 0.042 ± 0.017 | 35.32 ± 1.12 |
| ANC3 | 21.78 | 1805 | 0.836 | 0.923 | 0.0 | 0.025 ± 0.011 | 35.29 ± 1.19 |
| ANC10 | 22.66 | 1809 | 0.916 | 0.949 | 0.0 | 0.014 ± 0.009 | 35.39 ± 1.29 |
| ANC30 | 24.30 | 1800 | 0.974 | 0.980 | 0.0 | 0.006 ± 0.007 | 36.26 ± 0.84 |
| TK10 | 21.62 | 1226 | 0.462 | 0.870 | 0.0 | 0.047 ± 0.021 | 35.31 ± 1.25 |
| TK72 | 25.99 | 1486 | 0.655 | 0.975 | 0.0 | 0.020 ± 0.014 | 35.08 ± 1.09 |
| STU10R1 | 21.67 | 1022 | 0.385 | 0.748 | 34.2 | 0.052 ± 0.026 | 34.89 ± 1.04 |

## A.9 H4 test (Region5), P100 per instance ([`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L21-L31`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L21-L31))
| instance | A | B | A+α | B+α | X1 | RejectX* | CoinFlip |
|---|---|---|---|---|---|---|---|
| s0.1 | 39.92 | 40.36 | 39.32 | 39.55 | 40.89 | 46.69 | 46.96 |
| s0.2 | 33.92 | 33.79 | 34.16 | 33.51 | 33.22 | 36.08 | 37.87 |
| s0.3 | 37.72 | 37.94 | 37.47 | 37.28 | 36.00 | 39.68 | 46.75 |
| s0.4 | 26.39 | 26.18 | 26.02 | 25.95 | 26.22 | 28.12 | 29.21 |
| s0.5 | 42.72 | 43.91 | 37.96 | 35.07 | 51.46 | 46.05 | 61.36 |
| s0.6 | 36.38 | 36.02 | 35.19 | 35.51 | 40.78 | 39.50 | 44.67 |
| **mean** | 36.17 | 36.37 | **35.02** | **34.48** | 38.09 | 39.35 | 44.47 |

\* RejectX is matched only on s0.4; the low-side mean is 39.28 (two-sided rule, [F53](#F53)).

## A.10 H5 test (Region1), P100 per instance ([`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L21-L31`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L21-L31))
| instance | A | B | A+α | B+α | TB:pt (= TB:cd) | RejectX | CoinFlip |
|---|---|---|---|---|---|---|---|
| s0.1 | 24.81 | 25.19 | 25.50 | 25.37 | 25.19 | 27.53 | 35.33 |
| s0.2 | 22.02 | 22.27 | 22.15 | 22.41 | 22.17 | 24.62 | 47.40 |
| s0.3 | 30.69 | 31.69 | 30.60 | 30.45 | 31.18 | 37.20 | 59.42 |
| s0.4 | 22.68 | 22.72 | 23.33 | 22.72 | 22.78 | 25.81 | 55.18 |
| s0.5 | 22.13 | 22.90 | 22.53 | 22.55 | 23.00 | 25.40 | 42.86 |
| s0.6 | 22.50 | 22.47 | 23.63 | 23.35 | 22.39 | 28.63 | 62.13 |
| **mean** | **24.14** | 24.54 | 24.62 | 24.48 | 24.45 | 28.20 | 50.39 |

## A.10b WP10 E1, training-window proxy validation ([`changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L38-L48`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L38-L48))

| proxy | C1 concordance (≥ 0.70) | C2 mean sign / cell agreement (≥ 70%) | verdict |
|---|---|---|---|
| P1 emulator, day 1 (deployable) | 0.63 (p = 0.003), FAIL | same sign (−0.40 vs −0.32); 6/9, FAIL | NOT VALID |
| P2 emulator, full trace (diagnostic) | 0.65, FAIL | same sign; 6/9, FAIL | NOT VALID |
| P3 delta proxy, day 1 (sim anchor) | 0.61, FAIL | same sign; 7/9, PASS | NOT VALID |
| P4 simulator's own day-1 peak (post hoc) | 0.61 | 8/9 | — |

## A.10c Auto-research H-CLS, retrain-1 screen ([`changes/3_autoresearch/result/FINAL_REPORT.md#L22-L28`](../../changes/3_autoresearch/result/FINAL_REPORT.md#L22-L28))

| candidate | mean d vs the better α arm / worst d / wins | outcome |
|---|---|---|
| CB:pt (B models) | +0.313 / −0.151 / 6 of 8 | confirmed; finalist rule failed (ineligible: Region1_s0 r2 unmatched; 6/10 wins vs A+α, needs 7) |
| CB:ptm (class-monotone) | −0.097 / −1.683 / 4 | gate failed |
| CA:pt (A models) | −0.151 / −1.131 / 4 | gate failed |
| CA:ptm | incomplete (an unmatched r1 cell) | gate failed |
| UB:ptm (one pooled table, leave-one-instance-out) | −0.732 / −4.516 / 2 | gate failed |

## A.11 Auto-research T2 (Region4), P100 per instance ([`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L23-L31`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L23-L31))
| instance | A | B | A+α | B+α | Y = XA-F1PT | control XA-F1CPSAT | RejectX | CoinFlip |
|---|---|---|---|---|---|---|---|---|
| s0.2 | 59.07 | 58.88 | 49.58 | 50.85 | 49.61 | 55.05 | 58.31 | 64.52 |
| s0.3 | 76.14 | 75.99 | 48.95 | 51.38 | 49.37 | 51.23 | 77.09 | 83.26 |
| s0.4 | 51.72 | 59.60 | 51.60 | 51.15 | 51.22 | 50.96 | 73.35 | 74.19 |
| s0.5 | 32.85 | 55.25 | 32.41 | 33.45 | 32.93 | 32.60 | 55.84 | 56.74 |
| s0.6 | 33.81 | 33.84 | 31.81 | 32.49 | 32.72 | 32.00 | 64.59 | 65.48 |
| **mean** | 50.72 | 56.71 | **42.87** | 43.87 | **43.17** | 44.37 | 65.84 | 68.84 |

## Appendix B. Timeline

Commit times come from [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt) (all branches, `git log --all`); run times come from the cited reports.

| Date (2026) | Event | Record |
|---|---|---|
| 09-14 | Literature-review pipeline and top-8 feasibility report (`2264e66`); its Baleen audit proposes peak-aware scoring plus load-adaptive gating | git, [F104](#F104) |
| 09-26 | Proposal documents (`527f8bc`); reproduction starts | [`changes/0_reproduce/RESULTS.md#L5`](../../changes/0_reproduce/RESULTS.md#L5) |
| 09-27 | Scope v1 frozen | [`changes/SCOPE.md#L3`](../../changes/SCOPE.md#L3) |
| 09-28 00:17 | Reproduction and QUBO literature review committed (`0981c50`) | git |
| 09-28 | harness_eval (sample 0); Q1–Q3 protocol frozen in-file; Track A runs 15:53 → 09-29 02:30 (Q3 held-out 21:50 → 02:21); Q2 held-out from 18:25 (core audit 18:31 → 01:31) | [F15](#F15), [F75](#F75) |
| 09-29 15:02 | Real-harness and deep-explore campaign committed (`be284a3`); phase-2 plan + scope v2 (`27fb6f0`) | [F75](#F75) |
| 10-01 | Plan restores Ising as required (`5e49299`); CP1 overlay committed (`f79808f`, 16:20) | [F05](#F05), [F36](#F36) |
| 10-01 → 10-03 | WP5 tuning; WP1 runs; WP2 area set up 10-01 16:25, label solves from 16:27, first ledger row 17:11 | [F29](#F29), [F25](#F25) |
| 10-03 00:10–02:15 | WP2: rep-1 D screen logged (00:10); finalist rule written (00:20); D:F1PT confirmation fails, S = −0.14 (01:35); X1's screen queued (02:15). PLAN's dev-signal gate failed and its pivot was not taken | [F94](#F94) |
| 10-03 00:11 | WP1 H1′ committed (`08ad0d2`) | [F25](#F25) |
| 10-03 01:13 | H2′ protocol committed (`fd54e76`); test 01:24–01:45; result `b6f44e2` 02:10 | [F28](#F28) |
| 10-03 02:15 → 10-04 08:25 | WP2: X1's screen queued 10-03 02:15 (stage 2 finished 04:14); rule applied 10-04 05:25; confirmed 06:50; named X1, the H3′ primary, at 08:25 | [F39](#F39), [F94](#F94) |
| 10-04 09:16 | H3′ protocol + WP2 dev results (`cba9970`) | [F39](#F39), [F44](#F44) |
| 10-04 17:30 | Privacy redaction (`55a125b`) | [F87](#F87) |
| 10-05 14:13 | G3 waived (`84a0c1d`); H3′ test ledger rows 14:23:12 → 17:41:42; Track C stage 1 starts (14:18) | [F76](#F76), [F44](#F44) |
| 10-05 ~15:05 → 10-16 | Track C session down (stage 1 had run 14:18–15:05 on 10-05) | [F73](#F73) |
| 10-16 12:33 | H3′ evaluated (`evaluation.json` mtime) | [F73](#F73) |
| 10-16 12:40 | H3′ result: FAIL (`46608e0`) | [F44](#F44) |
| 10-16 13:54 | Track C stage-1 results and finalist rule (`19d7992`); H4 pre-registered (`d10e572`) | [F49](#F49), [F50](#F50), [F52](#F52) |
| 10-16 20:27 | Track C stage 2 negative (`4ba4bcc`) | [F50](#F50) |
| 10-16 21:30 | H4 protocol (`c8f655a`); Region5 test runs to 10-17 05:31 | [F52](#F52) |
| 10-19 16:14 | H4 result: YES (`cad1603`) | [F52](#F52) |
| 10-19 17:03 → 19:23 | WP10 E0–E3 dev; H5 protocol (`2738cba`, 19:23) | [F56](#F56)–[F58](#F58), [F83](#F83) |
| 10-19 20:50 | H5 result: NO (`b4c4a95`) | [F59](#F59) |
| 10-19 23:34 | Auto-research contract and Codex loop (`3a79daf`); the Codex run does no work | [F61](#F61), [F89](#F89) |
| 10-20 00:43–00:56 | Opus launcher (`204bce2`); DEV_RULES R0 written 00:56 | [F61](#F61), [F84](#F84) |
| 10-20 02:23 | cls_table T1 protocol (`9650674`, later void) | [F62](#F62), [F73](#F73) |
| 10-20 04:36 / 05:19 | Union T1 protocol (`76cf5c8`) / T2 protocol (`1cda6af`) | [F73](#F73) |
| 10-20 06:27 | Union finalist XA:F1PT; T1 TEST_GO 06:26:50 (`f74bf8b`) | [F63](#F63), [F64](#F64) |
| 10-20 07:04–07:05 | T1 closed as unevaluable (`539f39e`); T2 addendum (`3fdba1b`); T2 TEST_GO 07:05:04 | [F64](#F64), [F65](#F65) |
| 10-20 10:01–10:03 | T2 result: FAILED (`80233a6`, 10:01:13); final report (`b0d6e2b`, 10:03:31) | [F65](#F65) |
| 10-20 10:01–11:26 | Dev control confirmation (launched 10:01); STOP_EXHAUSTED written 11:26 (`4fe0688`). The EXHAUSTED loop status (11:44) is uncommitted in the working tree | [`changes/3_autoresearch/result/STOP_EXHAUSTED`](../../changes/3_autoresearch/result/STOP_EXHAUSTED), [`changes/3_autoresearch/result/LOOP_STATUS.txt`](../../changes/3_autoresearch/result/LOOP_STATUS.txt) |
| 10-20 15:41 | This story loop (run 20261020_154140) | [`changes/4_story/result/LOOP_STATUS.txt`](../../changes/4_story/result/LOOP_STATUS.txt) |

## Appendix C. File map (where each kind of evidence lives)

| Topic | Primary files |
|---|---|
| Index, ledger, decisions | [`./RESEARCH.md`](../../RESEARCH.md), [`changes/SCOPE.md`](../../changes/SCOPE.md), [`changes/SCOPE_v2.md`](../../changes/SCOPE_v2.md), [`changes/2_deployable_peak/PLAN.md`](../../changes/2_deployable_peak/PLAN.md) |
| Proposal, spec, paper, paper selection | [`documents/PeakBaleen_Proposal.pdf`](../../documents/PeakBaleen_Proposal.pdf) (text: [`documents/proposal_docx_compose/proposal.js`](../../documents/proposal_docx_compose/proposal.js)), [`documents/CourseProject-Fall2026.pdf`](../../documents/CourseProject-Fall2026.pdf), [`documents/Baleen_FAST24_Wong.pdf`](../../documents/Baleen_FAST24_Wong.pdf), [`documents/top_doable_papers_filtered.md`](../../documents/top_doable_papers_filtered.md), [`lit_review/README.md`](../../lit_review/README.md), documents/OS Final Project Proposal.pdf (the proposal slides) |
| Reproduction | [`changes/0_reproduce/README.md`](../../changes/0_reproduce/README.md), [`changes/0_reproduce/REPRODUCE_PLAN.md`](../../changes/0_reproduce/REPRODUCE_PLAN.md), [`changes/0_reproduce/RESULTS.md`](../../changes/0_reproduce/RESULTS.md), [`changes/0_reproduce/work/results/fig9_summary.md`](../../changes/0_reproduce/work/results/fig9_summary.md), [`changes/0_reproduce/work/results/fig9_jobs.csv`](../../changes/0_reproduce/work/results/fig9_jobs.csv), [`changes/0_reproduce/work/results/retrain_dist.csv`](../../changes/0_reproduce/work/results/retrain_dist.csv) |
| Literature review | [`changes/1_literature_review/lit_review_qubo/REPORT.md`](../../changes/1_literature_review/lit_review_qubo/REPORT.md), [`changes/1_literature_review/SWAPPABLE_QUBO_ISING_REPORT.md`](../../changes/1_literature_review/SWAPPABLE_QUBO_ISING_REPORT.md), [`changes/1_literature_review/ising_followup/survey.md`](../../changes/1_literature_review/ising_followup/survey.md), [`changes/1_literature_review/ising_followup/audit/AUDIT.md`](../../changes/1_literature_review/ising_followup/audit/AUDIT.md) |
| Phase-1 real harness | [`changes/1_literature_review/harness_eval/RESULTS.md`](../../changes/1_literature_review/harness_eval/RESULTS.md), [`changes/1_literature_review/harness_eval/PROGRESS.md`](../../changes/1_literature_review/harness_eval/PROGRESS.md), [`changes/1_literature_review/harness_eval/results/tables.md`](../../changes/1_literature_review/harness_eval/results/tables.md) |
| Phase-1 Q1–Q3 | [`changes/1_literature_review/explore/PROTOCOL.md`](../../changes/1_literature_review/explore/PROTOCOL.md), [`changes/1_literature_review/explore/q2/RESULTS.md`](../../changes/1_literature_review/explore/q2/RESULTS.md), [`changes/1_literature_review/explore/q2/PROGRESS.md`](../../changes/1_literature_review/explore/q2/PROGRESS.md), [`changes/1_literature_review/explore/q2/trials.csv`](../../changes/1_literature_review/explore/q2/trials.csv), [`changes/1_literature_review/explore/q2/results/q2_final.md`](../../changes/1_literature_review/explore/q2/results/q2_final.md), [`changes/1_literature_review/explore/q3/RESULTS.md`](../../changes/1_literature_review/explore/q3/RESULTS.md), [`changes/1_literature_review/explore/q3/PROGRESS.md`](../../changes/1_literature_review/explore/q3/PROGRESS.md), [`changes/1_literature_review/explore/common/Q3_FORMULATION.md`](../../changes/1_literature_review/explore/common/Q3_FORMULATION.md), [`changes/1_literature_review/explore/common/INSTANCES.md`](../../changes/1_literature_review/explore/common/INSTANCES.md) |
| WP0 overlay | [`changes/2_deployable_peak/wp0_overlay/CP1.md`](../../changes/2_deployable_peak/wp0_overlay/CP1.md), [`changes/2_deployable_peak/wp0_overlay/PROGRESS.md`](../../changes/2_deployable_peak/wp0_overlay/PROGRESS.md), [`changes/2_deployable_peak/wp0_overlay/PATCH.diff`](../../changes/2_deployable_peak/wp0_overlay/PATCH.diff), [`changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md`](../../changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md) |
| WP1 H1′ | [`changes/2_deployable_peak/wp1_offline/RESULTS.md`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md), [`changes/2_deployable_peak/wp1_offline/PROGRESS.md`](../../changes/2_deployable_peak/wp1_offline/PROGRESS.md), [`changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`](../../changes/2_deployable_peak/wp1_offline/results/wp1_table.csv) |
| WP5 Ising track | [`changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md`](../../changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md), [`changes/2_deployable_peak/wp5_ising/PROGRESS.md`](../../changes/2_deployable_peak/wp5_ising/PROGRESS.md), [`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md`](../../changes/2_deployable_peak/wp5_ising/RESULTS_dev.md), [`changes/2_deployable_peak/wp5_ising/RESULTS_test.md`](../../changes/2_deployable_peak/wp5_ising/RESULTS_test.md), [`changes/2_deployable_peak/wp5_ising/results/scaling_summary.md`](../../changes/2_deployable_peak/wp5_ising/results/scaling_summary.md), [`changes/2_deployable_peak/wp5_ising/results/h2test_verdict.json`](../../changes/2_deployable_peak/wp5_ising/results/h2test_verdict.json) |
| WP2 deployed dev | [`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md), [`changes/2_deployable_peak/wp2_deployed/PROGRESS.md`](../../changes/2_deployable_peak/wp2_deployed/PROGRESS.md), [`changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md`](../../changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md), [`changes/2_deployable_peak/wp2_deployed/trials.csv`](../../changes/2_deployable_peak/wp2_deployed/trials.csv), [`changes/2_deployable_peak/wp2_deployed/results/summary.md`](../../changes/2_deployable_peak/wp2_deployed/results/summary.md), [`changes/2_deployable_peak/wp2_deployed/results/mechanism_by_region.txt`](../../changes/2_deployable_peak/wp2_deployed/results/mechanism_by_region.txt) |
| WP3 H3′ test | [`changes/2_deployable_peak/wp3_test/RESULTS_test.md`](../../changes/2_deployable_peak/wp3_test/RESULTS_test.md), [`changes/2_deployable_peak/wp3_test/PROGRESS.md`](../../changes/2_deployable_peak/wp3_test/PROGRESS.md), [`changes/2_deployable_peak/wp3_test/INSTANCES.md`](../../changes/2_deployable_peak/wp3_test/INSTANCES.md), [`changes/2_deployable_peak/wp3_test/trials.csv`](../../changes/2_deployable_peak/wp3_test/trials.csv), [`changes/2_deployable_peak/wp3_test/results/evaluation.json`](../../changes/2_deployable_peak/wp3_test/results/evaluation.json) |
| WP8 Track C | [`changes/2_deployable_peak/wp8_trackC/PLAN_C.md`](../../changes/2_deployable_peak/wp8_trackC/PLAN_C.md), [`changes/2_deployable_peak/wp8_trackC/PROGRESS.md`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md), [`changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md`](../../changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md), [`changes/2_deployable_peak/wp8_trackC/results/stage1_table.md`](../../changes/2_deployable_peak/wp8_trackC/results/stage1_table.md), [`changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md`](../../changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md), [`changes/2_deployable_peak/wp8_trackC/results/proxy_validation.md`](../../changes/2_deployable_peak/wp8_trackC/results/proxy_validation.md), [`changes/2_deployable_peak/wp8_trackC/trials.csv`](../../changes/2_deployable_peak/wp8_trackC/trials.csv) |
| WP9 H4 test | [`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md`](../../changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md), [`changes/2_deployable_peak/wp9_region5/PROGRESS.md`](../../changes/2_deployable_peak/wp9_region5/PROGRESS.md), [`changes/2_deployable_peak/wp9_region5/RESULTS_test.md`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md), [`changes/2_deployable_peak/wp9_region5/trials.csv`](../../changes/2_deployable_peak/wp9_region5/trials.csv), [`changes/2_deployable_peak/wp9_region5/results/evaluation.json`](../../changes/2_deployable_peak/wp9_region5/results/evaluation.json), [`changes/2_deployable_peak/wp9_region5/INSTANCES.md`](../../changes/2_deployable_peak/wp9_region5/INSTANCES.md) (instance build and label statistics) |
| WP10 H5 test | [`changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md`](../../changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md), [`changes/2_deployable_peak/wp10_schedule/G1_v3.md`](../../changes/2_deployable_peak/wp10_schedule/G1_v3.md), [`changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md`](../../changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md), [`changes/2_deployable_peak/wp10_schedule/PROGRESS.md`](../../changes/2_deployable_peak/wp10_schedule/PROGRESS.md), [`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md`](../../changes/2_deployable_peak/wp10_schedule/RESULTS_test.md), [`changes/2_deployable_peak/wp10_schedule/trials_test.csv`](../../changes/2_deployable_peak/wp10_schedule/trials_test.csv), [`changes/2_deployable_peak/wp10_schedule/results/e3_tables.md`](../../changes/2_deployable_peak/wp10_schedule/results/e3_tables.md) |
| Auto-research: contract, rules, notes | [`changes/3_autoresearch/README.md`](../../changes/3_autoresearch/README.md), [`changes/3_autoresearch/autoscript/run_auto.sh`](../../changes/3_autoresearch/autoscript/run_auto.sh), [`changes/3_autoresearch/documents/GOOD_RESULT.md`](../../changes/3_autoresearch/documents/GOOD_RESULT.md), [`changes/3_autoresearch/result/DEV_RULES.md`](../../changes/3_autoresearch/result/DEV_RULES.md), [`changes/3_autoresearch/result/LAB_NOTEBOOK.md`](../../changes/3_autoresearch/result/LAB_NOTEBOOK.md), [`changes/3_autoresearch/result/STATUS.md`](../../changes/3_autoresearch/result/STATUS.md), [`changes/3_autoresearch/result/FINAL_REPORT.md`](../../changes/3_autoresearch/result/FINAL_REPORT.md), [`changes/3_autoresearch/code/validate.py`](../../changes/3_autoresearch/code/validate.py) (the deterministic fail-closed validator) |
| Auto-research: scope and gates | [`changes/3_autoresearch/work/cls_table/SCOPE_AMENDMENT.md`](../../changes/3_autoresearch/work/cls_table/SCOPE_AMENDMENT.md), [`changes/3_autoresearch/work/cls_table/G1_v4.md`](../../changes/3_autoresearch/work/cls_table/G1_v4.md), [`changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md`](../../changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md), [`changes/3_autoresearch/work/union/G1_v5.md`](../../changes/3_autoresearch/work/union/G1_v5.md) |
| Auto-research: protocols and tests | [`changes/3_autoresearch/work/t1_region2/PROTOCOL.md`](../../changes/3_autoresearch/work/t1_region2/PROTOCOL.md) (void), [`changes/3_autoresearch/work/t1u_region2/PROTOCOL.md`](../../changes/3_autoresearch/work/t1u_region2/PROTOCOL.md), [`changes/3_autoresearch/work/t1u_region2/ADDENDUM_R4.md`](../../changes/3_autoresearch/work/t1u_region2/ADDENDUM_R4.md), [`changes/3_autoresearch/work/t1u_region2/RESULTS_test.md`](../../changes/3_autoresearch/work/t1u_region2/RESULTS_test.md), [`changes/3_autoresearch/work/t2u_region4/PROTOCOL.md`](../../changes/3_autoresearch/work/t2u_region4/PROTOCOL.md), [`changes/3_autoresearch/work/t2u_region4/ADDENDUM_T1_UNEVALUABLE.md`](../../changes/3_autoresearch/work/t2u_region4/ADDENDUM_T1_UNEVALUABLE.md), [`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md`](../../changes/3_autoresearch/work/t2u_region4/RESULTS_test.md), [`changes/3_autoresearch/work/t2u_region4/trials_test.csv`](../../changes/3_autoresearch/work/t2u_region4/trials_test.csv), `changes/3_autoresearch/work/union_t2/` (the T2 code and overlay copy) |
| Auto-research: dev ledgers | [`changes/3_autoresearch/work/cls_table/trials_dev.csv`](../../changes/3_autoresearch/work/cls_table/trials_dev.csv), [`changes/3_autoresearch/work/union/trials_dev.csv`](../../changes/3_autoresearch/work/union/trials_dev.csv), [`changes/3_autoresearch/work/union/results/dev_finalist.json`](../../changes/3_autoresearch/work/union/results/dev_finalist.json) |
| Auto-research: validators | [`changes/3_autoresearch/result/validator_red_team_round_1.md`](../../changes/3_autoresearch/result/validator_red_team_round_1.md), [`changes/3_autoresearch/result/validator_red_team_round_2.md`](../../changes/3_autoresearch/result/validator_red_team_round_2.md), [`changes/3_autoresearch/result/validator_integrity_stats_round_1.md`](../../changes/3_autoresearch/result/validator_integrity_stats_round_1.md), [`changes/3_autoresearch/result/validator_integrity_stats_round_2.md`](../../changes/3_autoresearch/result/validator_integrity_stats_round_2.md) |
| Privacy | [`tools/privacy_scrub.py`](../../tools/privacy_scrub.py) |
| This story | [`changes/4_story/code/check_story.py`](../../changes/4_story/code/check_story.py), [`changes/4_story/code/recompute.py`](../../changes/4_story/code/recompute.py), [`changes/4_story/code/make_index.py`](../../changes/4_story/code/make_index.py), [`changes/4_story/code/linkify.py`](../../changes/4_story/code/linkify.py), [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt), [`changes/4_story/result/git_timeline.txt`](../../changes/4_story/result/git_timeline.txt), [`changes/4_story/result/protocol_commits.txt`](../../changes/4_story/result/protocol_commits.txt), [`changes/4_story/result/WRITER_NOTES.md`](../../changes/4_story/result/WRITER_NOTES.md) |

## Appendix D. Recomputation one-liners (read-only, except that items 1, 2 and 9 write their own output files under `changes/4_story/result/`)

1. **Test-arm means, paired pass-rule quantities, and the round-2 derived numbers.**
   - **Used by:** [F21](#F21), [F24](#F24), [F25](#F25), [F36](#F36), [F44](#F44), [F46](#F46), [F47](#F47), [F48](#F48), [F52](#F52)–[F54](#F54), [F59](#F59), [F60](#F60), [F65](#F65), [F66](#F66), [F69](#F69), [F70](#F70), [F72](#F72), [F96](#F96), [F100](#F100), [F101](#F101) and §8 rows 18 and 19.
   - **Raw inputs:** [`changes/2_deployable_peak/wp3_test/trials.csv`](../../changes/2_deployable_peak/wp3_test/trials.csv), [`changes/2_deployable_peak/wp9_region5/trials.csv`](../../changes/2_deployable_peak/wp9_region5/trials.csv), [`changes/2_deployable_peak/wp10_schedule/trials_test.csv`](../../changes/2_deployable_peak/wp10_schedule/trials_test.csv), [`changes/3_autoresearch/work/t2u_region4/trials_test.csv`](../../changes/3_autoresearch/work/t2u_region4/trials_test.csv), [`changes/2_deployable_peak/wp2_deployed/trials.csv`](../../changes/2_deployable_peak/wp2_deployed/trials.csv), [`changes/2_deployable_peak/wp8_trackC/trials.csv`](../../changes/2_deployable_peak/wp8_trackC/trials.csv), [`changes/3_autoresearch/work/cls_table/trials_dev.csv`](../../changes/3_autoresearch/work/cls_table/trials_dev.csv), [`changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`](../../changes/2_deployable_peak/wp1_offline/results/wp1_table.csv), and the §8.1 table of [`changes/1_literature_review/explore/q2/RESULTS.md`](../../changes/1_literature_review/explore/q2/RESULTS.md).
   - **Script:** [`changes/4_story/code/recompute.py`](../../changes/4_story/code/recompute.py); **output:** [`changes/4_story/result/recompute_out.txt`](../../changes/4_story/result/recompute_out.txt):
     ```
     python3 changes/4_story/code/recompute.py > changes/4_story/result/recompute_out.txt
     ```
   - **Conventions:**
     - Only `matched == True` rows count.
     - A configuration's mean is the mean over instances of the per-instance mean over retrains.
     - SE_retrain = sqrt(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i)/n; SE_inst = sd(d_i)/√n.
     - **WP2 dev merge.** For WP2 dev comparisons, the widened-search re-runs are merged into their arms before averaging: Ax-1.0 → Aa-1.0, Bx-1.0 → Ba-1.0, Bx-0.5 → Ba-0.5, Ex-1.0 → Ea-1.0 (`cells_merged` in the script). WP2's own report merges them the same way ([`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L241`](../../changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L241)), and so does Track C's proxy validation ([`changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L61-L63`](../../changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L61-L63)). The WP2 and union rows of [F70](#F70) are computed from the raw ledgers this way, not copied from a report.
   - **Agreement.** Every recomputed value agrees with its source report to the source's rounding. One source rounds differently from raw: WP9's −0.24 / +1.19 vs raw −0.246 / +1.183, noted in [F53](#F53).
   - **Round-2 additions:**
     - the LP-start share: (31.816 − 23.039)/(31.816 − 22.524);
     - the H4 and Region4 concentration;
     - the per-instance X1 − Dc+α differences;
     - the Region7 s0.5 peak windows;
     - Region6 first-access admission by arm;
     - dev Region1_s0 means;
     - WP1 per-region means;
     - the Region5 s0.6 peak windows.
   - **Round-3 additions:**
     - PT vs CP-SAT label arms on WP2 dev (merged as above) and on the union dev ledger ([F70](#F70));
     - WP10's test table fits: neutral tables, and PT equal to the exhaustive and CD tables ([F59](#F59));
     - WP1 R0 minus the authors' OPT-AP P100 ([F101](#F101));
     - when Track C's ANC10 and ANC10CP solves finished ([F100](#F100));
     - the added/removed line counts of `PATCH.diff` ([F36](#F36));
     - differences between values quoted in reports: harness C4 vs the F2b dev greedy (§8 row 19) and Baleen's peak-blind OPT minus the F2b dev sims ([F96](#F96)).
2. **Git timeline and protocol commit times** ([F73](#F73), [F75](#F75), [F76](#F76), [F89](#F89), [F93](#F93)):
   ```
   git log --all --reverse --date=format:'%Y-%m-%d %H:%M:%S' --format='%h %ad %s' > changes/4_story/result/git_timeline.txt
   for f in changes/SCOPE.md changes/SCOPE_v2.md changes/1_literature_review/explore/PROTOCOL.md changes/2_deployable_peak/PLAN.md changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md changes/2_deployable_peak/wp8_trackC/PLAN_C.md changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md changes/3_autoresearch/documents/GOOD_RESULT.md changes/3_autoresearch/result/DEV_RULES.md changes/3_autoresearch/work/t1_region2/PROTOCOL.md changes/3_autoresearch/work/t1u_region2/PROTOCOL.md changes/3_autoresearch/work/t1u_region2/ADDENDUM_R4.md changes/3_autoresearch/work/t2u_region4/PROTOCOL.md changes/3_autoresearch/work/t2u_region4/ADDENDUM_T1_UNEVALUABLE.md; do echo "$f | added $(git log --all --diff-filter=A --date=format:'%Y-%m-%d %H:%M:%S' --format='%h %ad' -- $f | tail -1) | last $(git log --all -1 --date=format:'%Y-%m-%d %H:%M:%S' --format='%h %ad' -- $f)"; done   # header line omitted; output equals changes/4_story/result/protocol_commits.txt
   ```
3. **The ≈11.3% reproduction figure has no source other than the index** ([F08](#F08)):
   ```
   grep -rn "11\.3%\|≈11.3" --include=*.md --include=*.csv --include=*.txt --include=*.json . | grep -v "/env/\|\.cache\|site-packages\|4_story"
   ```
   It matches only `RESEARCH.md:36` and an unrelated "11.3%" in [`changes/2_deployable_peak/wp1_offline/RESULTS.md#L87`](../../changes/2_deployable_peak/wp1_offline/RESULTS.md#L87) (a top-5 reduction).
4. **The artifact's own peak policy was never run** ([F91](#F91)):
   ```
   grep -rln "PolicyUtilityPeakServiceTimeSize" --include=*.md changes | grep -v "/env/\|baleen_code\|overlay\|4_story"
   ```
   It matches only [`changes/SCOPE.md`](../../changes/SCOPE.md).
5. **No interim-look entry in the auto-research notebook** ([F86](#F86)):
   ```
   grep -n "08:18" changes/3_autoresearch/result/LAB_NOTEBOOK.md
   ```
   No output.
6. **The union dev A+α mean** quoted in [`./RESEARCH.md#L28`](../../RESEARCH.md#L28) (36.16) equals XA:F1PT's mean (35.359) plus its mean improvement vs A+α (0.802), from [`changes/3_autoresearch/work/union/results/dev_finalist.json`](../../changes/3_autoresearch/work/union/results/dev_finalist.json):
   ```
   python3 -c "import json;r=json.load(open('changes/3_autoresearch/work/union/results/dev_finalist.json'))['rule'][0];print(round(r['mean']+r['A+a_mean'],2))"
   ```
7. **The H3′ test run window** ([F44](#F44), [F73](#F73)), from the ledger's `ts` column:
   ```
   python3 -c "import csv;t=[r['ts'] for r in csv.DictReader(open('changes/2_deployable_peak/wp3_test/trials.csv'))];print(min(t),max(t),len(t))"
   ```
   Output: `2026-10-05T14:23:12 2026-10-05T17:41:42 126`.
8. **The reserve instance dumps on disk** ([F92](#F92)):
   ```
   ls changes/2_deployable_peak/wp1_offline/inst | grep -c "s0\.[789]\.npz"
   ```
   Output: `12`. They are git-ignored by [`changes/2_deployable_peak/.gitignore#L10`](../../changes/2_deployable_peak/.gitignore#L10).
9. **Untracked files and file times** ([F73](#F73), [F74](#F74), [F76](#F76), [F100](#F100)). The go-file G3_SIGNED and the flag file TIMING_IDLE are not in git, so their content and modification times are copied into [`changes/4_story/result/untracked_evidence.txt`](../../changes/4_story/result/untracked_evidence.txt) by:
   ```
   P=changes/2_deployable_peak; { echo "# Evidence from untracked files and filesystem metadata (this working tree; not in git). Generated by Appendix D item 9."; for f in $P/wp3_test/G3_SIGNED $P/TIMING_IDLE; do echo "## content of $f (untracked)"; cat $f; echo; done; echo "## mtimes (stat -c '%y %n')"; stat -c '%y %n' $P/wp3_test/G3_SIGNED $P/TIMING_IDLE $P/wp3_test/trials.csv $P/wp3_test/results/evaluation.json; } > changes/4_story/result/untracked_evidence.txt
   ```
   File times can change if the files are copied or touched; they are evidence about this working tree only.
10. **When the Baleen paper audit and the ranking table entered git** ([F104](#F104)):
   ```
   for f in lit_review/papers/fast24-baleen-ml-admission-and-prefetching-for/audit/report.md lit_review/ranking.md; do echo "$f: added $(git log --diff-filter=A --date=format:'%Y-%m-%d %H:%M:%S' --format='%h %ad' -- $f); commits $(git log --format=%h -- $f | tr '\n' ' ')"; done
   ```
   Output: the audit report was added in `2264e66` 2026-09-14 10:53:49 (its only commit); [`lit_review/ranking.md`](../../lit_review/ranking.md) in `527f8bc` 2026-09-26 14:02:59 (its only commit).
