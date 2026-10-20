# PeakBaleen: the research story

**Peak-aware (min–max) Ising/QUBO episode selection for Baleen (FAST '24) flash-cache admission.** Graduate Operating Systems course project, University of Notre Dame, Fall 2026. Team: Ching-Hao Chiu, Jie Fu, Sixue Xing (captain).

This is the cited record of everything the project did, from the reproduction to the auto-research loop. Every number in a finding below is checked by `changes/4_story/code/check_story.py` against the files that finding cites. Recomputations are in Appendix D. Status: story-writer round 1 of 5 (run 20261020_154140). Open items are in `changes/4_story/result/WRITER_NOTES.md`.

## 0. Abstract

Baleen trains its admission model on an offline selection that maximises *average* disk-head time (DT) saved, but disks are provisioned for the *peak* 10-minute window (`./RESEARCH.md#L10-L13`). We asked two questions. Can a min–max selection, written as a QUBO/Ising problem, lower the peak at the same flash write rate? And does that gain survive Baleen's online ML model?

**Offline, yes.** In phase 1, Ising-selected episodes beat Baleen's peak-blind oracle on 6/6 held-out instances (27.06 vs 32.28 P100) (`changes/1_literature_review/explore/q2/RESULTS.md#L12-L20`). In phase 2 the same held across 39 instances in four regions: −13.0% to −13.7% on average, and about −16% outside Region4 (`changes/2_deployable_peak/wp1_offline/RESULTS.md#L3-L15`). The gain comes from the formulation, not the solver: classical LP and CP-SAT selections do just as well.

**Ising vs classical solvers.** The Ising solvers never beat classical solvers by the pre-registered criteria, either in phase 1 (Q2) or at tight 1/3/10 s budgets (H2′) (`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L7-L24`). Where both families reach the optimum, their objectives are identical.

**Deployed, every Ising/QUBO component failed its pre-registered test:**
- Ising peak labels: phase-1 Q3 and the scope-v2 test H3′ (`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L6-L16`);
- an Ising-fitted threshold table: H5 (`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L9-L17`);
- a peak-label union model: an unattended auto-research loop (`changes/3_autoresearch/result/FINAL_REPORT.md#L1-L7`).

For the label-based tests the recurring mechanism is that day-1 min–max labels are brittle when the peak *type* changes (big-offset scan vs burst of new episodes).

**The one deployed win** is the scope-v2 load-adaptive admission threshold on Baleen's *own* models, a non-Ising control. It was first seen post hoc and then confirmed by pre-registration on a fresh region (H4, Region5: 35.02 vs 36.17, 5/6) (`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L19`). It also helped post hoc on Regions 6/7 and Region4, and did not help on the low-load Region1.

The reserve samples 0.7–0.9 have never been used in any deployed run. Their only use was WP1's offline H1′ breadth simulations (F92).

## How to read this document

- **Finding format.** `### F<id> [priority] [evidence] title`, then the claim, a one-line reason for the priority, and `Refs:`. Refs are repo-relative paths; `#Lx-Ly` points at lines.
- **Priority:**
  - **P0:** headline results and decisive negatives.
  - **P1:** important supporting results and mechanisms.
  - **P2:** secondary, dev or mechanism detail.
  - **P3:** infrastructure, incidents, minor notes.
- **Evidence:**
  - **TEST-PREREG:** a pre-registered test whose protocol was fixed before the run.
  - **NEGATIVE-TEST:** a pre-registered test that failed.
  - **TEST-POSTHOC:** an observation on test data that was not the pre-registered hypothesis.
  - **DEV:** selection-biased development data.
  - **OFFLINE:** offline OPT or solver results.
  - **REPRO:** the reproduction.
  - **INFRA:** tooling, gates and integrity.
- **Two caveats about the evidence labels:**
  1. **Phase-1 tests (Q1–Q3).** Their pre-registration is file-dated (`changes/1_literature_review/explore/PROTOCOL.md#L3`) and was committed to git only after the held-out runs (F75). They carry TEST-PREREG / NEGATIVE-TEST because they were the pre-specified hypotheses on held-out data, but read them as weaker than the phase-2 tests, whose protocols were git-committed first (F73).
  2. **H1′ (WP1).** It is tagged OFFLINE. Its criterion was fixed in `changes/2_deployable_peak/PLAN.md#L19` before WP1 ran, but it is an offline solver/OPT result.
- **Arm names used throughout:**
  - **A:** Baleen labels, original features.
  - **B:** A + the causal `load` feature.
  - **A+α / B+α:** A or B with the load-adaptive admission threshold θ·clip((load_10m/20)^α, 0.25, 4), α = −1.
  - **X1:** Ising (parallel-tempering) min–max F1 labels + `load` + α = −1.
  - **P100:** `PeakServiceTimeUtil1`, the peak backend load in % over 10-minute windows after day 1, at matched write rate 35.599 MB/s ± 1% (`changes/SCOPE.md#L42-L49`).

## 0.1 Findings index

<!-- INDEX:BEGIN -->
92 findings: P0 9, P1 39, P2 29, P3 15. Evidence: DEV 21, INFRA 32, NEGATIVE-TEST 8, OFFLINE 12, REPRO 4, TEST-POSTHOC 7, TEST-PREREG 8.

**P0 findings (headline results and decisive negatives):** F18, F20, F25, F28, F33, F44, F52, F59, F65.

| ID | Priority | Evidence | Claim | Section |
|---|---|---|---|---|
| F01 | P1 | INFRA | The question: optimise the peak 10-minute window, not average DT saved, and keep the gain online | 1. Question, proposal and scope |
| F02 | P1 | INFRA | Scope v1 (frozen 2026-09-27): only the offline selection Policy may change; operating point and metric fixed for every method | 1. Question, proposal and scope |
| F03 | P1 | INFRA | Scope v2 (2026-09-29) widens the boundary by exactly one causal demand-load signal; CP1 fixes its details | 1. Question, proposal and scope |
| F04 | P2 | INFRA | Amendments 1.2b (threshold table), 1.2c (load × access-class table) and 1.2d (union of two admission models), each behind a bit-exact gate | 1. Question, proposal and scope |
| F05 | P2 | INFRA | Team decision log: reproduce first, freeze the boundary, keep Ising central against the literature review's LP-first advice | 1. Question, proposal and scope |
| F06 | P3 | INFRA | How Baleen was chosen: an automated paper-feasibility pipeline ranked it first of eight shortlisted papers | 1. Question, proposal and scope |
| F07 | P1 | REPRO | The baselines replay bit-exactly and the authors' Figure 9 notebook reproduces exactly | 2. Reproduction of Baleen |
| F08 | P1 | REPRO | Baleen matches the authors' released-metric runs within ±0.6 points; the paper's Figure 9 Baleen bars (`tracedrop`) do not reproduce | 2. Reproduction of Baleen |
| F09 | P2 | REPRO | Retraining is nondeterministic, and episode order is its only source; the peak is almost insensitive to the write budget | 2. Reproduction of Baleen |
| F10 | P2 | REPRO | README smoke test passes; the operating point is DWPD 7.5, not the proposal's 3 drive-writes per day | 2. Reproduction of Baleen |
| F11 | P1 | OFFLINE | The literature review and a synthetic CPU audit predicted the gain would come from the formulation, with LP beating Ising solvers | 3. Formulation, solvers and the literature review |
| F12 | P2 | OFFLINE | Synthetic audit: matrix-free SB scales to 200k variables in about 512 MB; the dense SB package needs 58 GB at 50k | 3. Formulation, solvers and the literature review |
| F13 | P1 | INFRA | The real-harness formulation: true min–max F1 over the post-day-1 windows, nested-prefix output, and two equally tuned solver families | 3. Formulation, solvers and the literature review |
| F14 | P2 | INFRA | The phase-1 deployed (Q3) labels used an extended-Ising energy on day 1 | 3. Formulation, solvers and the literature review |
| F15 | P1 | DEV | Phase-1 harness test on sample 0: the offline gain is real, but distillation into the unchanged GBM keeps almost none of it | 3. Formulation, solvers and the literature review |
| F16 | P2 | OFFLINE | Gate 0: the analytic window loads match the simulator, and peak-aware plans migrate; the evidence points to admissions overrunning the cache | 3. Formulation, solvers and the literature review |
| F17 | P2 | OFFLINE | Phase-1 harness solver attribution: inside the hybrids the classical sub-solvers did most of the work, and the one analytic Ising edge was EIM on Region7 | 3. Formulation, solvers and the literature review |
| F18 | P0 | TEST-PREREG | Q1 = YES: min–max selection beats Baleen's peak-blind oracle offline on 6/6 held-out instances | 4. Offline results |
| F19 | P1 | OFFLINE | The offline gain is a formulation effect, not a solver effect | 4. Offline results |
| F20 | P0 | NEGATIVE-TEST | Q2 = NO: on the same F1 formulation the Ising samplers beat the best classical solver only at the 10 s budget | 4. Offline results |
| F21 | P1 | DEV | The proposal's own Ising design (a sum-of-squares QUBO surrogate solved by simulated bifurcation) was the weakest Ising arm; the "Ising" finalists are replica-exchange samplers on the true objective | 4. Offline results |
| F22 | P3 | DEV | Q2 post hoc: the 10 s Ising win and the 60 s CP-SAT win do not depend on the nested time split | 4. Offline results |
| F23 | P3 | DEV | Phase-1 dev on the squared-hinge F2b: the classical local search led at 10 s, so the held-out solver comparison was run on F1 | 4. Offline results |
| F24 | P3 | OFFLINE | Q2 bookkeeping: the replica-exchange samplers made almost all accepted moves, and the MILP guard discarded late solutions | 4. Offline results |
| F25 | P0 | OFFLINE | H1′ breadth: on 39 instances in four regions, peak-aware selection beats the peak-blind oracle on 36–37 of them by −13.0% to −13.7% on average; about −16% outside Region4 | 4. Offline results |
| F26 | P1 | OFFLINE | Peak migration is the rule offline: the planned peak window almost never is the simulated one | 4. Offline results |
| F27 | P1 | OFFLINE | Region4 has little peak headroom; its peaks are short bursts the oracle already absorbs, and the losses come from migration | 4. Offline results |
| F28 | P0 | NEGATIVE-TEST | H2′ = NO: at re-solve budgets of 1, 3 and 10 s the tuned Ising solvers are not better than the best classical solver | 4. Offline results |
| F29 | P2 | DEV | H2′ dev tuning: equal trials for both families, and the ranking flips with the budget | 4. Offline results |
| F30 | P2 | TEST-PREREG | Rolling re-solve at 1 s (pre-declared secondary, no criterion): the exact classical solvers win on the small window instances | 4. Offline results |
| F31 | P1 | OFFLINE | Scaling (contribution S): matrix-free SB runs real unions of up to 125541 QUBO variables in at most 214 MB, where the dense SB package runs out of memory | 4. Offline results |
| F32 | P2 | DEV | Choosing the label solver: WP5 recommended EIM, the deployed tests used PT, and the choice matters far less than the formulation | 4. Offline results |
| F33 | P0 | NEGATIVE-TEST | Q3 = NO: Ising-family peak labels distilled into Baleen's unchanged GBM lose to Baleen on held-out instances | 5.1 Phase 1 (Q3) |
| F34 | P1 | DEV | Q3 mechanism: the Ising labels changed first-access admission, not peak targeting | 5.1 Phase 1 (Q3) |
| F35 | P1 | TEST-POSTHOC | Q3 held-out: P100 is set by rare scan-like windows, and relabelling moves those decisions in either direction | 5.1 Phase 1 (Q3) |
| F36 | P1 | INFRA | The scope-v2 overlay passes CP1: bit-exact default equivalence and exact train/serve parity of `load` | 5.2 Scope v2 |
| F37 | P1 | DEV | Learnability gate PASSES: given `load`, the GBM fits Ising peak-aware labels much better, and Baleen's own labels not at all | 5.2 Scope v2 |
| F38 | P1 | DEV | The plain 2×2 hypothesis (Ising labels + `load`, arm D) does not survive confirmation on dev | 5.3 WP2 |
| F39 | P1 | DEV | The WP2 finalists X1/X2 (F1PT labels + `load` + α) come from a rule written before confirmation; about half of X1's dev gain is the threshold alone | 5.3 WP2 |
| F40 | P2 | DEV | On dev, Ising (PT/EIM) vs classical (CP-SAT) labels of the same F1 formulation: no claim either way; with α the PT labels lead by +1.26 (5/8) | 5.3 WP2 |
| F41 | P1 | DEV | WP2 mechanism: on Region6 the Ising labels plus α admit the big-offset scans that set the peak; on Region7 they suppress first-access admission | 5.3 WP2 |
| F42 | P2 | DEV | The other WP2 ablations failed their screens or the confirmation rule | 5.3 WP2 |
| F43 | P3 | INFRA | WP2 bookkeeping: 40 unmatched rows, all reported; the threshold-search bound was a tool limitation | 5.3 WP2 |
| F44 | P0 | NEGATIVE-TEST | H3′ = NO: Ising peak labels + `load` + the load-adaptive threshold (X1) lose to Baleen on the test set | 5.4 WP3 |
| F45 | P1 | NEGATIVE-TEST | H3′-labels = NO: X1 is not better than the same threshold on Baleen's own models | 5.4 WP3 |
| F46 | P1 | TEST-POSTHOC | Why H3′ failed: one big-offset scan peak (Region7 s0.5) that the F1-label models do not admit | 5.4 WP3 |
| F47 | P1 | TEST-POSTHOC | Post hoc on the H3′ test: the load-adaptive threshold on Baleen's own models is the best configuration | 5.4 WP3 |
| F48 | P2 | TEST-PREREG | H3′ pre-declared comparisons without pass/fail: CP-SAT labels deploy better than PT labels, and retention is negative for every Ising- or CP-SAT-label arm | 5.4 WP3 |
| F49 | P2 | DEV | Track C stage 1: the cheap deployed proxy fails its pre-registered validation, so every screen used full simulations | 5.5 Track C (WP8) |
| F50 | P1 | DEV | Track C stage 2 is negative: no deployment-aware Ising objective passes the pre-registered dev screen | 5.5 Track C (WP8) |
| F51 | P3 | DEV | Track C near miss: a single retrain of STU10R1 had the lowest dev mean, but the pre-registered gate rejected it | 5.5 Track C (WP8) |
| F52 | P0 | TEST-PREREG | H4 = YES: the load-adaptive admission threshold on Baleen's own models beats Baleen on fresh Region5 (pre-registered) | 5.6 WP9 |
| F53 | P1 | TEST-PREREG | H4 caveats: the margin rests on the retrain-level SE, one instance carries most of the gain, and RejectX could not be matched | 5.6 WP9 |
| F54 | P1 | TEST-PREREG | The Ising record X1 fails the reported rule again on Region5 (no pass/fail was attached), by the same mechanism: one catastrophic scan-type instance | 5.6 WP9 |
| F55 | P3 | INFRA | WP9 preparation: the dry run and the static replays | 5.6 WP9 |
| F56 | P2 | DEV | WP10 E1: no training-window proxy ranks threshold variants well enough (pre-registered validity criterion) | 5.7 WP10 |
| F57 | P1 | OFFLINE | WP10 E2: the Ising solver (PT) and the classical solver (coordinate descent) find the same threshold tables | 5.7 WP10 |
| F58 | P2 | DEV | WP10 E3: TB:pt is the dev finalist under a rule written before any E2 solve or E3 simulation | 5.7 WP10 |
| F59 | P0 | NEGATIVE-TEST | H5 = NO: the Ising-fitted load-bucket threshold table does not beat Baleen on fresh Region1 | 5.7 WP10 |
| F60 | P1 | TEST-PREREG | On low-load Region1 the α arms do not help either (a comparison declared in advance as reported, no claim) | 5.7 WP10 |
| F61 | P2 | INFRA | The auto-research contract: an Ising-centric Y, a fresh pre-registered pool, a stricter rule and at most two test spends | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F62 | P2 | DEV | Auto-research H-CLS (Ising-fitted load × access-class threshold tables): no finalist | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F63 | P2 | DEV | Auto-research H-UX (union of Baleen's model and an Ising-label model): the dev finalist XA:F1PT | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F64 | P1 | NEGATIVE-TEST | Auto-research T1 (Region2): spent, failed, and unevaluable as pre-registered | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F65 | P0 | NEGATIVE-TEST | Auto-research T2 (Region4): the Ising-label union beats Baleen by a wide margin but not the threshold arm, so the loop ends NEGATIVE | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F66 | P1 | TEST-POSTHOC | Region4 replicates the H4 effect post hoc: A+α is 15% below Baleen | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F67 | P1 | TEST-POSTHOC | Why the union did not transfer: neither test pool has scan peaks | 5.8 The auto-research loop (3_autoresearch, run 20261020_004634) |
| F68 | P1 | TEST-POSTHOC | Day-1 min–max labels are brittle when the peak *type* changes (big-offset scan vs burst of new episodes) | 6. Cross-cutting mechanisms |
| F69 | P1 | TEST-POSTHOC | The load-adaptive threshold's evidence status, region by region: pre-registered YES on Region5, post-hoc on Regions 6/7 and 4, null on Region1 | 6. Cross-cutting mechanisms |
| F70 | P1 | OFFLINE | Ising and classical solvers: identical objectives where both reach the optimum, budget-dependent winners elsewhere, and no objective advantage that survived deployment | 6. Cross-cutting mechanisms |
| F71 | P1 | TEST-PREREG | Retention of the offline gain never approached the proposal's 60% target for any Ising-label configuration | 6. Cross-cutting mechanisms |
| F72 | P2 | DEV | First-access admission is the recurring lever on Region7 (mostly dev evidence) | 6. Cross-cutting mechanisms |
| F73 | P1 | INFRA | Every phase-2 and auto-research test protocol was committed to git before its test ran | 7. Methodology and integrity |
| F74 | P2 | INFRA | Each deployed test's evaluator was written and validated on earlier data before the test data existed, and the drivers refused to run without a go-file | 7. Methodology and integrity |
| F75 | P2 | INFRA | Phase-1 pre-registration (Q1–Q3) is file-dated, not git-attested | 7. Methodology and integrity |
| F76 | P1 | INFRA | Gate G3 (a teammate review of the overlay patch) was waived by the captain; no teammate sign-off is recorded for scope v2 | 7. Methodology and integrity |
| F77 | P3 | INFRA | Frozen-artifact checks always passed and sandboxing was the rule (with the exceptions in F78–F82); leak-check hits came from other tools and agents | 7. Methodology and integrity |
| F78 | P3 | INFRA | Phase-1 incidents: a 25-second tuning overlap and a stray `__pycache__` file in the frozen tree's wrapper | 7. Methodology and integrity |
| F79 | P3 | INFRA | Phase-2 timing incidents (WP1/WP5), each handled by superseding or flagging rows | 7. Methodology and integrity |
| F80 | P2 | INFRA | SMT-sibling exposure in phase-1 timing and early WP5 tuning, a seed-reuse artefact in tuning, and a lost session | 7. Methodology and integrity |
| F81 | P3 | INFRA | Track C, WP9 and WP10 operational deviations | 7. Methodology and integrity |
| F82 | P3 | INFRA | Smaller recorded disclosures not listed elsewhere in this story | 7. Methodology and integrity |
| F83 | P2 | INFRA | WP10 committed its H5 protocol after the dev confirmation had run, before its P100 values were read | 7. Methodology and integrity |
| F84 | P1 | INFRA | Auto-research integrity disclosures (final report §5) | 7. Methodology and integrity |
| F85 | P3 | INFRA | The round-1 auto-research validators failed the run on two blocking findings; both were fixed before T2's TEST_GO | 7. Methodology and integrity |
| F86 | P2 | INFRA | Six items the round-2 validators raised are not carried into the auto-research notebook or final report | 7. Methodology and integrity |
| F87 | P2 | INFRA | Privacy redaction of a public repo (2026-10-04); git history still holds the originals | 7. Methodology and integrity |
| F88 | P3 | INFRA | Documentation drift in the index file | 7. Methodology and integrity |
| F89 | P3 | INFRA | An earlier auto-research launch (Codex worker, run 20261019_233548) did no work | 7. Methodology and integrity |
| F90 | P2 | INFRA | The hardware differed from the proposal's plan: no GPU | 7. Methodology and integrity |
| F91 | P2 | INFRA | Planned but never measured | 7. Methodology and integrity |
| F92 | P1 | INFRA | The 0.7–0.9 reserve was never used in a deployed run, but WP1 simulated it offline, including the Region6/7 reserve | 7. Methodology and integrity |
<!-- INDEX:END -->

## 1. Question, proposal and scope

The proposal (`documents/PeakBaleen_Proposal.pdf`; text source `documents/proposal_docx_compose/proposal.js`) set three hypotheses:
- H1: an offline min–max gain;
- H2: an Ising solver beating greedy;
- H3: an online model retaining at least 60% of the offline gain.

The course spec (`documents/CourseProject-Fall2026.pdf`) allows an "improvement paper" on a recent top-venue system. Baleen is `documents/Baleen_FAST24_Wong.pdf`.

The swap boundary started narrow (v1: only the offline selection `Policy`) and widened step by step:
- v2 added one causal demand-load signal and an optional load-adaptive threshold;
- amendments 1.2b, 1.2c and 1.2d added threshold tables and a two-model union.

Every widening came with a bit-exact default-equivalence gate.

### F01 [P1] [INFRA] The question: optimise the peak 10-minute window, not average DT saved, and keep the gain online
Baleen ranks episodes by DT saved per byte written, which maximises total (average) DT saved. Provisioning, however, follows the peak: the P100 of backend utilisation over 10-minute windows. The project asks two things:
1. Can a min–max episode selection, formulated as QUBO/Ising, lower peak backend load at the same flash write rate?
2. Does that gain survive deployment through Baleen's online ML model?

The proposal's quantitative hypotheses:
- **H1:** min–max selection reduces Peak DT by at least 5% relative to stock Baleen, averaged over the seven Meta traces.
- **H2:** an Ising solver on a sum-of-squares surrogate beats both the artifact's greedy peak-scoring policy and a greedy warm start by at least 3%.
- **H3:** an online model with causal load features and no oracle peak window retains at least 60% of the offline gain.

**Why this priority:** it frames every verdict below; it is the reference point for "success".
Refs: `./RESEARCH.md#L10-L13`, `changes/SCOPE.md#L19`, `changes/SCOPE.md#L47`, `documents/proposal_docx_compose/proposal.js#L199-L201`

### F02 [P1] [INFRA] Scope v1 (frozen 2026-09-27): only the offline selection Policy may change; operating point and metric fixed for every method
`changes/SCOPE.md` makes PeakBaleen one new `Policy` subclass. It must emit the selected set for the training budget W = 35.599 MB/s first, so that the harness's prefix rule reproduces it. Everything else is frozen: simulator, episode model, features, GBMs, label rule `threshold < target_wr`, training driver and data.

Both evaluation modes use one contract:
- **Offline:** OPT, via `simulate_ap --ap opt`.
- **Deployed:** the labels train Baleen's unchanged GBMs, then `--ap mlnew`.
- **Common settings:** cache 366.475 GB, target write rate 35.599 MB/s with the threshold re-converged to ±1%, metric `PeakServiceTimeUtil1` after day 1, train on day 1.

Consequence written at the time: the proposal's causal load features were out of scope in v1. H3 therefore became "how much offline gain survives the *unchanged* GBM", and "losing most of the gain is an expected, reportable outcome".
**Why this priority:** this contract makes every later comparison fair and comparable.
Refs: `changes/SCOPE.md#L3-L33`, `changes/SCOPE.md#L35-L63`

### F03 [P1] [INFRA] Scope v2 (2026-09-29) widens the boundary by exactly one causal demand-load signal; CP1 fixes its details
**Why v2.** It exists because phase-1 peak labels did not survive distillation (retention ≈ 0; the GBM has no time or load signal).

**What may change.** All changes go into an overlay copy of BCacheSim:
- a `load` feature group: trailing *demand-side* DT over the last 10, 30 and 60 minutes. Demand-side is required because it is identical in training and serving, which rules out train/serve skew.
- optionally, a load-adaptive threshold θ_t = θ·g(load_t) with a fixed shape parameter, off by default;
- optionally, `load` for the prefetch models.

**CP1 clarifications (2026-10-01):**
- `load` counts GET demand only;
- one plumbing line in `train.py`;
- a known train/serve skew for the prefetch-model `load` (arm E only);
- the admission `load` is exact on 26,499 accesses;
- ≥3 retrains per configuration.

**Gates:** G1 default bit-equivalence; G2 the same pipeline for every method; G3 a teammate review of the diff.

**Not confirmed.** The file still says "agreed by Sixue Xing (captain) on 2026-09-29, pending confirmation by Ching-Hao Chiu and Jie Fu". No later confirmation is recorded in it.
**Why this priority:** it defines the only new signal, which became the source of the one deployed win.
Refs: `changes/SCOPE_v2.md#L3-L25`, `changes/SCOPE_v2.md#L33-L50`

### F04 [P2] [INFRA] Amendments 1.2b (threshold table), 1.2c (load × access-class table) and 1.2d (union of two admission models), each behind a bit-exact gate
**1.2b** (WP10, 2026-10-19) replaces the power law g by a piecewise-constant table, fitted on the training day only (`--ap-load-adapt-table`).
- It is recorded in `changes/SCOPE_v2.md` §1a.
- It lives in a separate overlay `PATCH_v3.diff` (+43/−1 lines over `PATCH.diff`).
- G1_v3 passed, and a table reproducing the power law was bit-identical to `--ap-load-adapt-alpha -1` (P100 39.5715164464613 both).

**1.2c (class table) and 1.2d (union)** were proposed by the auto-research worker on 2026-10-20.
- Both are "used only inside" `changes/3_autoresearch/work/`. They are **not** recorded in `changes/SCOPE_v2.md` §1a, which mentions only 1.2b.
- G1_v4 and G1_v5 passed:
  - frozen vs overlay are bit-identical on all 425 result keys;
  - a union whose second model can never admit (κ = 1e9), or that unions a model with itself, reproduces the A+α run bit-for-bit.

**Why this priority:** it shows how far the boundary moved and that each move was gated; it is secondary to the results.
Refs: `changes/SCOPE_v2.md#L44`, `changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md#L1-L21`, `changes/2_deployable_peak/wp10_schedule/G1_v3.md#L6-L15`, `changes/3_autoresearch/work/cls_table/SCOPE_AMENDMENT.md#L1-L11`, `changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md#L1-L5`, `changes/3_autoresearch/work/cls_table/G1_v4.md#L5-L19`, `changes/3_autoresearch/work/union/G1_v5.md#L5-L19`

### F05 [P2] [INFRA] Team decision log: reproduce first, freeze the boundary, keep Ising central against the literature review's LP-first advice
`./RESEARCH.md` §4 records these decisions:
- 09-26: reproduce Baleen first, freeze the artifact and sandbox every run.
- 09-27: fix the swap boundary (recorded in `changes/SCOPE.md`).
- 09-27: exclude Wong's thesis method from the baselines. The only source is "chat with captain"; there is no file record beyond the index.
- 09-28: reject "LP as the main method" and keep searching for Ising/QUBO selectors (captain). The literature review had recommended exactly that LP/MILP pipeline as the primary selector (`changes/1_literature_review/lit_review_qubo/REPORT.md#L5`).
- 09-28: pre-register Q1–Q3.
- 09-29: scope v2.
- 10-01: restore Ising as required (H3′ uses Ising labels; H2′ required; scaling reported; commit `5e49299`).
- 10-03 / 10-04: commit the H2′ and H3′ protocols before the tests.
- 10-16: after H3′ failed, pre-register H4 (the load-adaptive threshold on Baleen's models) for a fresh Region5 test.

**Why this priority:** it explains the project's shape (Ising kept as a required arm by decision), but the decisions themselves are not results.
Refs: `./RESEARCH.md#L52-L67`, `changes/SCOPE.md#L1-L5`, `changes/1_literature_review/lit_review_qubo/REPORT.md#L5`, `changes/2_deployable_peak/PLAN.md#L18-L25`

### F06 [P3] [INFRA] How Baleen was chosen: an automated paper-feasibility pipeline ranked it first of eight shortlisted papers
On 2026-09-14 an agent pipeline ranked candidate papers for the "improvement paper" track.
- It pre-ranked 1,254 papers, then desk-checked the top 8: cloned repos, read docs, sized data. Nothing was built or run.
- Baleen (FAST '24) had the highest repository score: 26/30, verdict DOABLE, minimum data 17 MB, reproduction feasibility H.

**The yardstick machine differed from the one used.** The check assumed a "Threadripper PRO 5955WX … 16 cores / 32 threads … 125 GiB" with an RTX A5000 GPU. All experiments later ran on a different machine without a GPU (F90).
**Why this priority:** project provenance; no result depends on it.
Refs: `documents/top_doable_papers_filtered.md#L1-L40`, `lit_review/README.md#L1-L4`, `lit_review/paper_list.md#L870`

## 2. Reproduction of Baleen

The artifact (Baleen-FAST24 `4e3a920`, BCacheSim `ddeb2d8`) was frozen, checksummed and run unmodified under `bwrap` (`changes/0_reproduce/README.md#L5-L15`).

The headline reproduction is good, with one systematic nuance: the paper's Figure 9 Baleen bars for Regions 6/7 come from an older, unreleased DT metric (`tracedrop`).

### F07 [P1] [REPRO] The baselines replay bit-exactly and the authors' Figure 9 notebook reproduces exactly
**Stage A.** The authors' own `fig-09-202309.ipynb`, run in our environment, gives Baleen 28.11, RejectX 31.95, CoinFlip 34.63 and a 12.0% saving, matching the paper exactly.

**Stage B.** Replays of the authors' `20230410_static_pf` runs are bit-exact. Peak (write rate):

| Trace | RejectX | CoinFlip |
|---|---|---|
| Region7 | 42.455 (36.00) | 48.961 (35.69) |
| Region6 | 42.321 (35.67) | 43.445 (35.57) |

`check_frozen.sh` reports all 94 artifact files unchanged.
**Why this priority:** a faithful baseline is the precondition for every comparison; it is supporting, not a project result.
Refs: `changes/0_reproduce/RESULTS.md#L5-L22`, `changes/0_reproduce/RESULTS.md#L68-L71`, `changes/0_reproduce/work/results/fig9_summary.md#L11-L18`

### F08 [P1] [REPRO] Baleen matches the authors' released-metric runs within ±0.6 points; the paper's Figure 9 Baleen bars (`tracedrop`) do not reproduce
**Released-metric runs match.** Against the authors' `20230421_alltraces_pfalways` Baleen runs, at matched write rate, our replays differ by −0.54, +0.35, +0.21 and −0.51 points.

**The Figure 9 bars do not.**
- The paper's Fig 9 Baleen bars (Region7 37.59, Region6 41.31) come from `20230327_tracedrop_*` runs that computed disk-head time differently. The no-cache peak is 64.69 vs 63.42 (Region7) and 59.24 vs 59.14 (Region6), and no released option reproduces this.
- Nine models per trace give 40.10 ± 0.18 (Region7) and 43.25 ± 0.04 (Region6), so the gap is systematic, not training noise.

**The automatic per-bar checker says "NOT PASSED".**
- It compares against those `tracedrop` rows: Region7 Baleen is +2.47 above its bar.
- At sample 0 the Region6 ordering fails: saving vs RejectX −2.2% ours vs 3.0% authors.

**The ≈11.3% figure is unverified.** `./RESEARCH.md` states that "re-averaged with a consistent metric, the 12% headline is ≈11.3%". No derivation of 11.3 exists under `changes/0_reproduce/` (search in Appendix D).
**Why this priority:** this is the main reproduction nuance a reader of the paper needs; the unverified 11.3% is flagged so nobody quotes it as measured.
Refs: `changes/0_reproduce/RESULTS.md#L24-L53`, `changes/0_reproduce/work/results/fig9_summary.md#L20-L38`, `./RESEARCH.md#L36`

### F09 [P2] [REPRO] Retraining is nondeterministic, and episode order is its only source; the peak is almost insensitive to the write budget
**Why retrains differ.** Retraining Baleen is not deterministic: LightGBM is hard-coded to 20 threads and episode generation uses 8 worker processes. The reproduction therefore ran 8 extra retrains per trace.

**The write budget barely moves the peak.** The peak changes by less than 0.6 points as the write rate moves from 28 to 45 MB/s.

**The source of nondeterminism (later).** CP1's pinned test showed the source is `Pool.imap_unordered` episode order:
- pinning it makes frozen and overlay training byte-identical;
- LightGBM is deterministic given identical ordered inputs.

This is why every later protocol requires ≥3 retrains.
**Why this priority:** it explains the retrain-variance design of all later tests; it is a mechanism detail.
Refs: `changes/0_reproduce/RESULTS.md#L46-L53`, `changes/2_deployable_peak/wp0_overlay/CP1.md#L71-L75`, `changes/2_deployable_peak/wp0_overlay/CP1.md#L94-L96`

### F10 [P2] [REPRO] README smoke test passes; the operating point is DWPD 7.5, not the proposal's 3 drive-writes per day
**Smoke test.** The README example on Region1 gives a Baleen saving over RejectX of 16.61%, against 16.11% in the authors' `example.ipynb`. Running the authors' notebook on our results also gives 16.61%.

**Operating point.** The artifact's target write rate of 35.599 MB/s is the CSV's "Target DWPD = 7.5"; the plan adds "This is not 3 DWPD." The proposal had assumed "400 GB flash, 3 drive-writes per day"; every result here uses the artifact's operating point.

**Deviations from the authors' commands.** There were four, none of them touching an algorithm parameter:
- `--eviction-policy LRU`;
- dropping `--offline-ap-decisions`;
- serialised training;
- for Baleen, re-converging the admission threshold to the target write rate (paper §4.1).

**Why this priority:** it documents a setup mismatch with the proposal and the adaptations; it changes no verdict.
Refs: `changes/0_reproduce/RESULTS.md#L55-L66`, `changes/0_reproduce/REPRODUCE_PLAN.md#L11-L17`, `documents/proposal_docx_compose/proposal.js#L250`

## 3. Formulation, solvers and the literature review

Formulation (P):
- **Notation:** episode e, decision x_e ∈ {0,1}, write cost s_e, per-window saving d(e,w), no-cache load C_w, window load L_w(x) = C_w − Σ_e d(e,w) x_e.
- **Problem:** minimise max_w L_w(x) subject to Σ s_e x_e ≤ B.
- **QUBO surrogates:** a sum-of-squares penalty and an LSE soft peak.
- **Constraint handling:** a budget penalty or a native hinge.

Solvers:
- **Ising family:** parallel tempering (PT), the Extended Ising Machine (EIM, hinge + augmented Lagrangian), matrix-free simulated bifurcation (SB), and MindQuantum QAIA (bSB/dSB/CAC on contested sub-QUBOs).
- **Classical family:** greedy, peak-aware greedy, LP + round + repair, HiGHS MILP, CP-SAT, SCIP and true-objective local search (LS).

### F11 [P1] [OFFLINE] The literature review and a synthetic CPU audit predicted the gain would come from the formulation, with LP beating Ising solvers
**Synthetic audit** (`ising_followup/audit/`):
- The peak-blind greedy leaves headroom above the LP bound of 3.7%, 10.6%, 11.8% and 11.8% of the greedy peak at n = 1k, 10k, 50k and 200k.
- LP round-down + repair captures 90–99.8% of that headroom in 0.002–1.7 s.
- No Ising arm reaches LP-round + repair at any size.
- At 200k the HiGHS MILP found no incumbent in 300 s.

**The reports' reading.** Ising solvers win on dense quadratic objectives with few constraints at n ≤ 300, and lose or tie at realistic size with many linear rows. The report titles: "Win on formulation, then let Ising compete" and "Solve the peak LP first, anneal second".

**Caveats.** The instance is synthetic, the runs were CPU-only, and slow arms were under-converged under fixed caps.
**Why this priority:** it is the prior the experiments later confirmed (formulation wins, Ising ≈ classical); it was synthetic, so it supports but does not decide.
Refs: `changes/1_literature_review/ising_followup/audit/AUDIT.md#L145-L166`, `changes/1_literature_review/ising_followup/audit/AUDIT.md#L195-L202`, `changes/1_literature_review/SWAPPABLE_QUBO_ISING_REPORT.md#L3`, `changes/1_literature_review/lit_review_qubo/REPORT.md#L1-L5`

### F12 [P2] [OFFLINE] Synthetic audit: matrix-free SB scales to 200k variables in about 512 MB; the dense SB package needs 58 GB at 50k
`mfsb` never forms Q:
- at 200k it took 45 s per inner call with 512 MB peak RSS;
- it reached 8.3% of headroom there.

The dense SB package at 50k needed 58 GB RSS and 17–73 minutes for a single call. MindQuantum's matrix-free J swap gives bit-identical solutions to the explicit J.
**Why this priority:** it motivated the matrix-free implementation later used for the real-instance scaling contribution (F31).
Refs: `changes/1_literature_review/ising_followup/audit/AUDIT.md#L168-L190`

### F13 [P1] [INFRA] The real-harness formulation: true min–max F1 over the post-day-1 windows, nested-prefix output, and two equally tuned solver families
**Instances** come from the unmodified training driver through a Policy dump:
- d(e,w) is the DT saved in 10-minute window w;
- C_w is the no-cache DT;
- B is the harness chunk budget at 35.599 MB/s.

**Formulations:**
- **F1:** max_w L_w, used by every Q1/Q2, H1′ and H2′ configuration and by the phase-2 F1-label arms (the phase-1 Q3 labels used F4, see F14);
- **F2a:** the top-4 mean;
- **F2b:** a squared hinge;
- **F3:** a capacity/eviction-coupled QKP, not implemented;
- **F4:** Track A's day-1 energy.

**Nested prefix.** The simulator's converged OPT cutoff admits only a prefix of the selection (0.72–0.89·W in harness_eval). Selections are therefore solved bottom-up at 8 nested levels f = 0.65 … 1.00 of B (harness_eval used 11 levels from 0.50).

**Solver families.** Ising: pt, eim, hlns, matrix-free SB on the QUBO surrogate Σ_w α_w(C_w − τ − (Dᵀx)_w)² + μ s·x, and mq (MindQuantum bSB/dSB/CAC on sub-QUBOs). Classical: greedy, pgreedy, lp, milp (HiGHS), cpsat, scip and ls.

**Fairness.** Both families get the same number of Optuna trials and the same pinned cores 0–7.
**Why this priority:** every offline and label result below uses this formulation; it is the method, not a result.
Refs: `changes/1_literature_review/explore/q2/RESULTS.md#L46-L125`, `changes/1_literature_review/explore/q2/RESULTS.md#L289-L293`, `changes/1_literature_review/harness_eval/RESULTS.md#L31`

### F14 [P2] [INFRA] The phase-1 deployed (Q3) labels used an extended-Ising energy on day 1
E = A·LSE_γ(L(x)) + a DT blend + a trust region toward Baleen's labels, plus optional kNN feature couplings, under a native hard budget.
- It was solved by numba parallel tempering (16 replicas).
- `q3form.py` reproduces the solver's energies exactly: Baleen start 24.5180 and solution 22.4457 on dev Region7 day 1.
- Finalists: P0 (pure soft peak), T2 (+ DT blend + trust region) and C2 (T2's energy over ~1.6k feature cells).
**Why this priority:** it is the method behind the Q3 labels; detail.
Refs: `changes/1_literature_review/explore/common/Q3_FORMULATION.md#L13-L56`

### F15 [P1] [DEV] Phase-1 harness test on sample 0: the offline gain is real, but distillation into the unchanged GBM keeps almost none of it
**Offline (OPT).** Every arm cut the simulated P100 by 5.5–8.0 points below Baleen's peak-blind OPT (R0):
- Region7 34.52 → 27.77 (R2);
- Region6 35.56 → 27.60;
- Ising arms 27.7–28.3, classical arms 27.6–28.3.

**Deployed.**
- Every Region7 arm scored 40.06–40.85, against Baleen online 40.10 ± 0.18.
- The best Region6 arm, R2, scored 42.38 ± 0.95, still above RejectX at 42.32.
- Retention R = (ML-Baleen − ML-Peak)/(OPT-Baleen − OPT-Peak) was −0.04 (Region7) and +0.11 (Region6) for R2, and +0.01 for the best Ising arm C4.

This is sample 0 only, i.e. the later dev instance.
**Why this priority:** it is the first evidence of the deployment gap that motivated scope v2; dev-only, so not a test result.
Refs: `changes/1_literature_review/harness_eval/RESULTS.md#L3-L10`, `changes/1_literature_review/harness_eval/RESULTS.md#L220-L257`

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
Refs: `changes/1_literature_review/harness_eval/RESULTS.md#L98-L114`, `changes/1_literature_review/harness_eval/RESULTS.md#L200-L218`

### F17 [P2] [OFFLINE] Phase-1 harness solver attribution: inside the hybrids the classical sub-solvers did most of the work, and the one analytic Ising edge was EIM on Region7
Analytic peak, averaged over the 11 nested levels on sample 0.
- **Only one Ising arm beat the MILP polish (R2), and only on one trace.** C2 (EIM: hinge + ALM + replica exchange) did so on Region7 (24.165 vs 24.220). On Region6, R2 is best (22.611 vs C2 22.917).
- **Inside C1** (LP + peak-window LNS racing three sub-solvers), accepted moves came from the HiGHS sub-MILP 243 times, true-objective SA 118 times, and the sum-of-squares sub-QUBO SA twice.
- **Inside C5** (contested-subset QUBO), the explicit QUBO heuristics do not beat a HiGHS sub-MILP on the same subset: on Region6, sub-MILP 23.33 vs MindQuantum bSB 23.37.
- **In simulation** all LP-family and Ising arms fall within 27.6–28.3.

**Why this priority:** it is early evidence for the Ising ≈ classical pattern (F70); detail.
Refs: `changes/1_literature_review/harness_eval/RESULTS.md#L162-L182`

## 4. Offline results: the min–max gain and the solver comparison

Offline (OPT mode), the min–max selection lowers the simulated peak by about 16% on Regions 5–7, and by less on Region4. Ising and classical solvers give the same simulated peak. The solver comparison (Q2 in phase 1, then H2′ at tight budgets) was pre-registered twice and failed twice. The Ising samplers were the best family only at one short budget each time.

### F18 [P0] [TEST-PREREG] Q1 = YES: min–max selection beats Baleen's peak-blind oracle offline on 6/6 held-out instances
The held-out set was Region7/Region6 × samples 0.1–0.3, never used for tuning, at matched write rate. All 52 simulations matched (WR 35.26–35.95).
- **F1 + PT:** P100 27.06 vs Baleen's peak-blind OPT 32.28 (−5.21), on 6/6 instances.
- **F1 + EIM:** 26.95 (−5.33), on 6/6.

**Pass rule:** ≥ 5/6 instances and lower on average.

**Pre-registration caveat.** `changes/1_literature_review/explore/PROTOCOL.md` says "Frozen: 2026-09-28, before any tuning". Its first git commit, however, is `be284a3` (2026-09-29 15:02), after the held-out runs (F75).
**Why this priority:** this is the project's headline positive result, the offline premise of everything after it.
Refs: `changes/1_literature_review/explore/q2/RESULTS.md#L12-L20`, `changes/1_literature_review/explore/q2/RESULTS.md#L259-L277`, `changes/1_literature_review/explore/PROTOCOL.md#L3-L12`, `changes/4_story/result/protocol_commits.txt`

### F19 [P1] [OFFLINE] The offline gain is a formulation effect, not a solver effect
Classical and Ising selections land on the same simulated peak at every stage:
- **Phase 1 (held-out).** The best classical selections simulate at 26.954, against PT 27.063 and EIM 26.951.
- **harness_eval.** Ising arms 27.7–28.3 vs classical 27.6–28.3.
- **WP1 (39 instances).** PT − CP-SAT = −0.18 on average, with PT lower on 18/39. Taking the best of the three methods per instance would give 14.6%.

Selections with near-identical analytic objectives can still differ by up to ~1 P100 point in simulation (peak migration), with no family pattern.
**Why this priority:** it determines what can be credited to Ising (nothing offline beyond parity); a central supporting fact.
Refs: `changes/1_literature_review/explore/q2/RESULTS.md#L18-L24`, `changes/1_literature_review/explore/q2/RESULTS.md#L271-L277`, `changes/1_literature_review/harness_eval/RESULTS.md#L4`, `changes/2_deployable_peak/wp1_offline/RESULTS.md#L91-L95`

### F20 [P0] [NEGATIVE-TEST] Q2 = NO: on the same F1 formulation the Ising samplers beat the best classical solver only at the 10 s budget
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

Pre-registration caveat as in F18.
**Why this priority:** it is the decisive negative on "Ising beats classical solvers" for the proposal's H2-type question.
Refs: `changes/1_literature_review/explore/q2/RESULTS.md#L12-L31`, `changes/1_literature_review/explore/q2/RESULTS.md#L243-L249`, `changes/1_literature_review/explore/q2/RESULTS.md#L297-L315`

### F21 [P1] [DEV] The proposal's own Ising design (a sum-of-squares QUBO surrogate solved by simulated bifurcation) was the weakest Ising arm; the "Ising" finalists are replica-exchange samplers on the true objective
**What the proposal planned.** H2 assumed a sum-of-squares penalty on window loads solved by an Ising solver, with simulated bifurcation (GPU-accelerated) as the primary Ising machine.

**How that design performed:**
- **Phase-1 dev tuning (F1, % vs peak-aware greedy).** SB reached −13.217 at 10 s, last among the Ising arms (PT −15.010, EIM −14.973, HLNS −14.066, MQ −13.891).
- **harness_eval.** C4 (matrix-free SB on the SoS QUBO) scored an analytic 24.343 / 23.044 (Region7 / Region6), vs EIM C2 24.165 / 22.917 and the MILP polish 24.220 / 22.611.
- **WP5 finalist rule.** SB V = −11.64%, the lowest of the four Ising solvers (PT −14.58%).

**What the finalists are.** PT and EIM are replica-exchange (parallel-tempering) samplers on the LSE-smoothed true peak, with a QUBO budget penalty or a native hinge. They sit inside the protocol's Ising/QUBO family ("parallel tempering … on a QUBO/Ising energy"), but they are CPU samplers, not physical or GPU Ising machines (F90).

**Why this priority:** it fixes what "Ising" means in every result in this story, and shows that the proposal's surrogate route under-performed.
Refs: `documents/proposal_docx_compose/proposal.js#L200`, `documents/proposal_docx_compose/proposal.js#L244`, `changes/1_literature_review/explore/q2/RESULTS.md#L127-L143`, `changes/1_literature_review/harness_eval/RESULTS.md#L162-L168`, `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L187-L195`, `changes/1_literature_review/explore/PROTOCOL.md#L37`

### F22 [P3] [DEV] Q2 post hoc: the 10 s Ising win and the 60 s CP-SAT win do not depend on the nested time split
On dev, giving level 1 a weight of 6 (46% of T):
- PT 23.174 vs CP-SAT 23.355 at 10 s;
- PT 23.163 vs CP-SAT 23.048 at 60 s.

The ordering is the same as with the default split (23.183 vs 23.321; 23.160 vs 23.080). This is post hoc, dev-only, and not part of any verdict.
**Why this priority:** it rules out an artefact of the driver; minor.
Refs: `changes/1_literature_review/explore/q2/RESULTS.md#L317-L334`

### F23 [P3] [DEV] Phase-1 dev on the squared-hinge F2b: the classical local search led at 10 s, so the held-out solver comparison was run on F1
**F2b at 10 s on dev** (10 trials each, % vs peak-aware greedy):
- classical LS −0.143 (best);
- PT −0.134;
- EIM −0.104;
- SB and SCIP never improved on their greedy start within 10 s.

**Why F1.** F1 went to held-out because the Ising samplers led there at 10 s: PT −15.010 and EIM −14.973, vs LS −14.901 and CP-SAT −14.566. F2b's 60 s stage was not run.

**Why this priority:** it records how the formulation for Q2 was chosen; minor.
Refs: `changes/1_literature_review/explore/q2/RESULTS.md#L127-L163`

### F24 [P3] [OFFLINE] Q2 bookkeeping: the replica-exchange samplers made almost all accepted moves, and the MILP guard discarded late solutions
**Move shares.** The replica-exchange sampler made 99.40% (PT, 10 s) to 99.9994% (EIM, 300 s) of all accepted moves; the rest were shared-repair operations.

**Run status.** All 288 held-out runs finished. One HiGHS MILP run at the 10 s budget exceeded the over-budget limit of 1.05 T + 0.5 s (11.03 s); no verdict depends on it. The guard discarded 5 of HiGHS's 144 held-out level solutions that came back after their deadline.
**Why this priority:** it shows the "Ising" arms really were Ising-driven and the runs were clean; bookkeeping.
Refs: `changes/1_literature_review/explore/q2/RESULTS.md#L196-L218`, `changes/1_literature_review/explore/q2/RESULTS.md#L254-L257`

### F25 [P0] [OFFLINE] H1′ breadth: on 39 instances in four regions, peak-aware selection beats the peak-blind oracle on 36–37 of them by −13.0% to −13.7% on average; about −16% outside Region4
Phase-1 frozen 300 s configurations (no tuning), Regions 4–7 × samples 0–0.9. Region4 s0.1 has no OPT-AP row, which leaves 39 instances. 156/156 simulations matched.

| Method | Wins vs R0 | Mean P100 reduction |
|---|---|---|
| LP + repair | 36/39 | 13.03% |
| CP-SAT | 36/39 | 13.15% |
| PT | 37/39 | 13.69% |

- **Regions 5–7:** 30/30 for all three methods (15.6 / 16.2 / 16.2%).
- **Region4:** 6/9, 6/9, 7/9 with only 4.6 / 3.0 / 5.4%.
- **H1′ criterion** (`changes/2_deployable_peak/PLAN.md#L19`: ≥ 80% wins and mean ≥ 10%, judged over all instances): passed by all three methods.
- **Headroom gate** (`changes/2_deployable_peak/PLAN.md#L105`: mean reduction ≥ 10%): met overall and on Regions 5, 6, 7 separately; not met on Region4 alone. Region4 also falls short of 80% wins (6/9, 6/9, 7/9).

Recomputed from `wp1_table.csv` (Appendix D).
**Why this priority:** it is the robust, broad offline result; the strongest positive evidence in the project.
Refs: `changes/2_deployable_peak/wp1_offline/RESULTS.md#L3-L38`, `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`, `changes/4_story/result/recompute_out.txt`, `changes/2_deployable_peak/PLAN.md#L19`, `changes/2_deployable_peak/PLAN.md#L105`, `./RESEARCH.md#L38`

### F26 [P1] [OFFLINE] Peak migration is the rule offline: the planned peak window almost never is the simulated one
- **The window moves.** The simulated peak window differs from R0's on 30/39 (LP), 34/39 (CP-SAT) and 33/39 (PT) instances.
- **The plan rarely matches.** The planned (analytic) peak window of the admitted prefix coincides with the simulated one on only 6/39, 9/39 and 6/39.
- **The plan is optimistic.** Planned peaks are below the simulated ones by 4.4–5.2 points on average (range −2.5 to +14.7).
- **The peak hour moves.** R0 peaks cluster at 13–14 h; PT's peaks spread over 0–3 h and 13–15 h.
**Why this priority:** it is the main offline mechanism and a warning that the analytic objective is a proxy.
Refs: `changes/2_deployable_peak/wp1_offline/RESULTS.md#L101-L108`

### F27 [P1] [OFFLINE] Region4 has little peak headroom; its peaks are short bursts the oracle already absorbs, and the losses come from migration
Region4 peaks are short bursts:
- window 291 = d2 00:30 on samples 0, 0.2 and 0.5, with no-cache load C_w = 84–182% util;
- on the other samples, R0 peaks at d3 03:30, d5 14:10 or d6 00:50.

The peak-aware solvers mostly tie R0 or win a few points. The exceptions are losses where the simulated peak migrated:
- CP-SAT −6.9% (s0.9) and −4.8% (s0.8);
- PT −4.1% (s0.8);
- LP −1.6% (s0.8).

**Why this priority:** it bounds the offline claim by region; it matters later because Region4 was the auto-research T2 pool.
Refs: `changes/2_deployable_peak/wp1_offline/RESULTS.md#L11-L15`, `changes/2_deployable_peak/wp1_offline/RESULTS.md#L47-L55`, `changes/2_deployable_peak/wp1_offline/RESULTS.md#L96-L100`

### F28 [P0] [NEGATIVE-TEST] H2′ = NO: at re-solve budgets of 1, 3 and 10 s the tuned Ising solvers are not better than the best classical solver
**PT vs the best classical method per cell:**
- ≤ on 1/6 instances at 1 s (a floored tie), 6/6 at 3 s and 4/6 at 10 s. The count criterion (≥ 5/6 at ≥ 2 budgets) is met at one budget only.
- Average over the 18 pairs: 22.7336 vs 22.7166. FAIL.

**EIM:** 0/6, 5/6 and 3/6; average 22.8413. FAIL.

**Which method was best where:**
- 1 s: the classical true-objective local search, on every test instance;
- 3 s: the replica-exchange samplers;
- 10 s: PT, LS and CP-SAT within ±0.3%.

**Run hygiene.** 324/324 runs ok, 0 over budget; the foreign-load audit had zero entries during the test.

**Pre-registration.** `PROTOCOL_v2_H2.md` and the plan were committed as `fd54e76` (2026-10-03 01:13) before the test runs (01:24:38 to 01:45). Dev had predicted this failure (F29).
**Why this priority:** the decisive pre-registered negative on the Ising-solver question at the budgets that motivated it.
Refs: `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L1-L24`, `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L104-L105`, `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L167-L173`, `changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L69-L78`, `changes/4_story/result/protocol_commits.txt`

### F29 [P2] [DEV] H2′ dev tuning: equal trials for both families, and the ranking flips with the budget
Each of 8 tunable solvers got 12 Optuna trials per budget (2,304 tuning runs). Dev-evaluation means:

| Budget | Result |
|---|---|
| 1 s | LS best: 23.03 vs PT 23.25, EIM 23.54 |
| 3 s | PT 22.73 and EIM 22.77 vs LS 22.87 |
| 10 s | near tie: PT 22.685, LS 22.703, EIM 22.702, CP-SAT 22.81 |

**Finalists.** PT and EIM, by a rule pre-registered at 14:55 on Oct 1: V = −14.58% and −14.14%, vs MQ −12.50% and SB −11.64%.

**Dev reading.** It predicted H2′ = FAIL.
**Why this priority:** it shows the test was set up fairly and its outcome anticipated; dev detail.
Refs: `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L6-L17`, `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L187-L199`, `changes/2_deployable_peak/wp5_ising/PROGRESS.md#L27`

### F30 [P2] [TEST-PREREG] Rolling re-solve at 1 s (pre-declared secondary, no criterion): the exact classical solvers win on the small window instances
Rolling re-solve (6-h windows, 3-h step) on the 6 test instances. Stitched full-trace peak:

| Method | Peak |
|---|---|
| CP-SAT | 26.440 |
| MILP | 26.445 |
| LS | 26.740 |
| EIM | 26.860 |
| PT | 26.903 |
| Best classical per instance | 26.426 |

- PT and EIM are ≤ the best classical method on 0/6 instances.
- Rolling costs about 4 util points against the one-shot full-trace solve at the same budget.

On dev (at 1 s and 3 s) the same held, so the Ising 3 s edge does not carry over to periodic re-labelling; the test itself ran at 1 s only.
**Why this priority:** it addresses the stated motivation for tight budgets (periodic re-labelling) and answers it negatively; secondary.
Refs: `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L138-L165`, `changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md#L82-L86`, `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L18-L23`

### F31 [P1] [OFFLINE] Scaling (contribution S): matrix-free SB runs real unions of up to 125541 QUBO variables in at most 214 MB, where the dense SB package runs out of memory
**Matrix-free SB** (32 agents):
- 0.3–1.9 ms per step and +12–86 MB on every real day-1 and full-trace instance (up to 32k variables);
- 4.5–12.7 ms per step and +111–214 MB on real 0.2–0.4% unions (62k–126k variables).

**The dense simulated-bifurcation package:**
- On the full traces: 1.5–3.6 s per step and 12–22 GB RSS, i.e. ~1,400–3,600× slower per step.
- It fails out of memory at the 64 GB cap on all three unions. The 62515-variable union died at 53.8 GB RSS.

**PT (sparse):** 5–31 M proposals/s with at most 165 MB.

**What was measured.** The level-1 QUBO surrogate (pure solver cost, no repair loop).

**Wording discrepancy.** `./RESEARCH.md` says the dense package fails "beyond ≈70k variables". That is the projected limit on the 123-GB machine; the observed failure was at 62.5k variables under the 64 GB cap.
**Why this priority:** this is the one reported Ising contribution that stands (engineering scalability); no pass/fail was attached.
Refs: `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L27-L31`, `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L333-L392`, `changes/2_deployable_peak/wp5_ising/results/scaling_summary.md`, `./RESEARCH.md#L41`

### F32 [P2] [DEV] Choosing the label solver: WP5 recommended EIM, the deployed tests used PT, and the choice matters far less than the formulation
**WP5 recommended EIM** for the WP2 labels: best Ising day-1 objective, and dev simulated P100 27.32 vs PT 27.33. It added a caveat: all peak-aware selections simulate within ~0.4 P100 of each other.

**What was used.** WP2 ran both F1PT and F1EIM label sets, and the finalists used F1PT. PROTOCOL_v2_H3 fixed the label solver to the phase-1 PT 10 s configuration "which is exactly what dev used", noting that H2′ had failed.
**Why this priority:** it explains why "Ising labels" means PT in every deployed test; detail.
Refs: `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L24-L26`, `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L241-L249`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L66-L69`, `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L67-L76`

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

### F33 [P0] [NEGATIVE-TEST] Q3 = NO: Ising-family peak labels distilled into Baleen's unchanged GBM lose to Baleen on held-out instances
Three finalists, held-out Region7/Region6 × samples 0.1–0.3, 3 retrains each, matched WR:

| Finalist | Wins vs Baleen online (need ≥ 4/6) | Mean improvement | 2 SE |
|---|---|---|---|
| P0 | 2/6 | −0.41 | 0.56 |
| T2 | 2/6 | −1.07 | 0.85 |
| C2 | 2/6 | −0.57 | 0.96 |

- All three are below RejectX 39.05 and CoinFlip 44.69, but so is Baleen (37.55), so that criterion does not discriminate.
- **Dev looked positive, held-out reversed it.** On dev the finalists were 0.74–1.17 points below Baleen on Region7.
- **Retrain swings are large.** For example T2 Region7 s0.1: 36.05 / 42.69 / 36.42.

Pre-registration caveat as in F18.
**Why this priority:** this is the first decisive deployment negative and the reason scope v2 exists.
Refs: `changes/1_literature_review/explore/q3/RESULTS.md#L6-L23`, `changes/1_literature_review/explore/PROTOCOL.md#L20-L23`

### F34 [P1] [DEV] Q3 mechanism: the Ising labels changed first-access admission, not peak targeting
**How the labels act.**
- An episode with a single access saves nothing, so the peak energy is indifferent to it. The stochastic PT leaves many such zero-value episodes selected: 44% of P0's Region7 labels, 26% of T2's, 10% of T5's.
- Each one is a positive first-access row. The trained GBM then admits new episodes at their first access far more often: on Region7, 6% → 15–28%.

**Evidence on dev.**
- Across 13 matched Region7 dev trials, corr(first-access admission, P100) = −0.79.
- Ablations (one retrain each): Baleen control 40.18; T5 39.26; T5 with its zero-value additions removed 39.90. JUNK10, a non-Ising control that swaps random zero-value episodes into Baleen's labels, gives 39.51. So about three quarters of T5's gain does not need a solver.
- Region6 barely moves (dev effects within −0.9..+0.1).

**Why this priority:** it is the mechanism that recurs on Region7 through every later phase (F72).
Refs: `changes/1_literature_review/explore/q3/RESULTS.md#L236-L259`

### F35 [P1] [TEST-POSTHOC] Q3 held-out: P100 is set by rare scan-like windows, and relabelling moves those decisions in either direction
**What sets the peak.** On Region7 s0.3, Region6 s0.1 and Region6 s0.2, the peak lies in scan-like windows: 25–42% of the window's accesses end beyond 8 MB. The fraction of those accesses a model admits varies with the labels and the retrain (Baleen 0.20–0.42; relabelled models 0.13–0.44).

**What carries over.** The first-access shift persists on held-out (Region7 8–11% → 14–36%), and Region7's mean load drops, but P100 does not follow the mean.

**Status.** Post-hoc analysis; the configurations were frozen before the held-out run.
**Why this priority:** it is the first sighting of the scan-vs-burst brittleness that later decided H3′ and X1 on Region5.
Refs: `changes/1_literature_review/explore/q3/RESULTS.md#L261-L299`

## 5.2 Scope v2: the causal load feature and the learnability gate

### F36 [P1] [INFRA] The scope-v2 overlay passes CP1: bit-exact default equivalence and exact train/serve parity of `load`
**G1 (Region7/Region6 s0):**
- RejectX/CoinFlip frozen vs overlay are bit-identical on all 425 result keys and every per-window series.
- Pinned Baleen training is identical in rows, labels and all 5 model files. The frozen and overlay end-to-end pipelines give the same P100 on both code bases: 40.130989380934864 (Region7) and 43.26696451693124 (Region6).
- Unpinned runs differ only in the ways frozen-vs-frozen also differs: on Region6, 8 label flips vs 16 between two frozen runs.

**Parity.** All 79,497 `load` values on 26,499 training accesses equal the simulator's values exactly (max abs diff 0).

**Patch.** `PATCH.diff`: 9 files, +217/−6.
**Why this priority:** it is the gate that makes every scope-v2 deployed result attributable to the intended change only.
Refs: `changes/2_deployable_peak/wp0_overlay/CP1.md#L5-L17`, `changes/2_deployable_peak/wp0_overlay/CP1.md#L57-L98`, `changes/2_deployable_peak/wp0_overlay/CP1.md#L100-L109`

### F37 [P1] [DEV] Learnability gate PASSES: given `load`, the GBM fits Ising peak-aware labels much better, and Baleen's own labels not at all
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
Refs: `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L96-L112`, `changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L23`

## 5.3 WP2: the deployed 2×2 on dev and the finalists X1/X2

### F38 [P1] [DEV] The plain 2×2 hypothesis (Ising labels + `load`, arm D) does not survive confirmation on dev
With 3 retrains on 8 dev instances:
- D:F1PT scores 38.37, vs A 38.50 and B 38.44 (finalist score S = −0.142);
- D:F1EIM scores 38.46 (S = −0.238).

**The interaction is positive but about 1 SE.** `load` helps peak-aware labels more than Baleen's: +0.44 and +0.63 vs +0.06. The interaction is +0.38 ± 0.61 (F1PT) and +0.57 ± 0.49 (F1EIM).

**Without `load` the peak-aware labels are worse than Baleen's:** C:F1PT 38.81, C:F1EIM 39.09.

**Arm A reproduces phase 1:** mean |diff| 0.16.
**Why this priority:** it is the dev answer to the scope-v2 hypothesis as originally planned (labels + signal); negative.
Refs: `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L16-L23`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L91-L94`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L123-L170`

### F39 [P1] [DEV] The WP2 finalists X1/X2 (F1PT labels + `load` + α) come from a rule written before confirmation; about half of X1's dev gain is the threshold alone
**The rule** was written 2026-10-03 00:20, before any confirmation retrain: S = mean_i min(A_i − X_i, B_i − X_i), finalists need S > 0.

**The finalists:**
- **X1** = Ea-1.0:F1PT, 37.20 (S = +1.027): vs A +1.30 (retrain SE 0.25, instance SE 0.64; 6/8), vs B +1.24 (0.26 / 0.51; 6/8).
- **X2** = Ea-0.5:F1PT, 37.84 (S = +0.386).

**Attribution.** The same threshold on Baleen's own models (A+α) scores 37.88, +0.62 vs A. X1 vs A+α is only +0.68 (5/8; instance SE 0.63).

**Selection bias, stated in the source.** 5 label designs, 5 variants and 2 α values were screened on the same 8 instances, so "the dev scores of X1/X2 are optimistic".
**Why this priority:** it defines the test configuration of H3′ and already shows that α carries much of the effect.
Refs: `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L25-L39`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L114-L134`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L186-L198`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L246-L247`, `changes/2_deployable_peak/wp2_deployed/PROGRESS.md#L64`

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
**Why this priority:** it is the dev answer to "does the Ising solver matter for labels"; suggestive at best on dev (≈2 instance-level SE with α), and reversed on test (F48).
Refs: `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L172-L184`

### F41 [P1] [DEV] WP2 mechanism: on Region6 the Ising labels plus α admit the big-offset scans that set the peak; on Region7 they suppress first-access admission
**Region6.** Its peaks are long big-offset scans.
- X1 admits 41% of the peak window's accesses (A: 22%).
- Its peak sits in a scan window in only 2/12 retrains, against 9/12 for A. A+α leaves 9/12.

**Region7.** Its peaks are bursts of new episodes.
- The F1 labels have no zero-value positives, so first-access admission falls to 2.4–2.8% vs Baleen's 8.7%.
- Mean DT rises by about 0.7, and X1 ≈ A (37.67 vs 37.69).

**Retention on dev:** X1 0.24 (per-instance mean).
**Why this priority:** it shows the dev gain depended on scans being present on day 1, which is exactly what failed on test (F46).
Refs: `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L200-L233`, `changes/2_deployable_peak/wp2_deployed/results/mechanism_by_region.txt`

### F42 [P2] [DEV] The other WP2 ablations failed their screens or the confirmation rule
- **D2 (+ hour of day):** screen −2.04 (Region6 s0.3 47.4). One training day gives one example per hour, which PLAN.md flagged as a risk.
- **Epf (prefetch-model `load`):** screen −1.62 vs −0.92. It carries the known train/serve skew.
- **D:P0 / D:T2 (phase-1 designs):** −1.20 / −1.42. They restore first-access admission (16–30%) but are unstable: Region7 s0.1 41.7 for T2, Region6 s0.2 42.1 for P0.
- **Ea-1.0:F1EIM:** positive screen (+0.206), but not confirmed: it lost the variant comparison to D:F1PT's rep 1 (0.237).
- **Ea-2.0:** unmatched on 8/8, so no valid screen; not re-screened.
**Why this priority:** it closes the obvious alternative designs; secondary.
Refs: `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L123-L134`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L228-L230`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L246-L249`, `changes/2_deployable_peak/PLAN.md#L110-L113`

### F43 [P3] [INFRA] WP2 bookkeeping: 40 unmatched rows, all reported; the threshold-search bound was a tool limitation
**Totals.** 388 evaluations and 1,075 full simulations; 348 matched, 40 unmatched, 0 failed.

**Unmatched rows.**
- 36 came from the convergence search capping θ < 1, while the α arms (g ∈ [0.25, 4]) can need θ > 1.
- The affected control/comparison cells were re-run with the search widened to (0, 4] (Ax/Bx/Ex): all 28 matched, at θ 1.01–1.29 per the report (ledger minimum 1.0046).
- Both finalists had matched inside the original bound.
- 4 C-arm rows were write-rate steps.

**Interruptions.** Two session interruptions, resumed without loss.
**Why this priority:** a disclosure, not a result.
Refs: `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L7-L9`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L235-L251`, `changes/4_story/result/recompute_out.txt`

## 5.4 WP3: the pre-registered deployability test H3′

### F44 [P0] [NEGATIVE-TEST] H3′ = NO: Ising peak labels + `load` + the load-adaptive threshold (X1) lose to Baleen on the test set
Test set: Region7/Region6 × samples 0.4–0.6, touched once.

**X1 vs the baselines:**
- X1 scores 40.53, vs A 39.27 and B 39.17.
- It wins 5/6 instances against each, but its mean is worse: A − X1 = −1.27, B − X1 = −1.36 (retrain SE 0.15 / 0.17; instance SE 2.41 / 2.55).
- It is below RejectX only barely (40.73) and below CoinFlip (48.64).

**X2** is also NO: 4/6, −1.61 / −1.70, and its mean (40.88) is not below RejectX (40.73).

**Run.** 126 evaluations, 126 matched. The arm means were recomputed from `trials.csv` (Appendix D).

**Pre-registration.** `PROTOCOL_v2_H3.md` was committed as `cba9970` (2026-10-04 09:16) before the test. The test was launched 2026-10-05, after the G3 waiver.
**Why this priority:** this is the decisive pre-registered answer to "does the Ising peak gain survive deployment".
Refs: `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L1-L41`, `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L84-L97`, `changes/2_deployable_peak/wp3_test/trials.csv`, `changes/4_story/result/recompute_out.txt`, `changes/4_story/result/protocol_commits.txt`

### F45 [P1] [NEGATIVE-TEST] H3′-labels = NO: X1 is not better than the same threshold on Baleen's own models
- X1 vs A+α: 3/6, −2.23 (retrain SE 0.21; instance SE 2.66).
- X1 vs B+α: 3/6, −2.15.

The protocol pre-registered this secondary test because on dev part of X1's gain came from the threshold alone. Had H3′ been YES with H3′-labels NO, the gain would have been attributed to the threshold, not the Ising labels.
**Why this priority:** it is the attribution test; it removes any residual credit for the labels on this test.
Refs: `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L10-L12`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L30-L38`, `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L15-L19`, `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L95-L97`

### F46 [P1] [TEST-POSTHOC] Why H3′ failed: one big-offset scan peak (Region7 s0.5) that the F1-label models do not admit
**One catastrophic instance.** On five of six instances X1 is below A, by 0.1–2.3. On Region7 s0.5 all three X1 retrains land at 51.7–52.8 (mean 52.30), against A 39.07 and above even RejectX (42.05).

**The peak window is a scan.** Window 378 has 48% of its accesses ending beyond 8 MB, for every arm.
- The Baleen-label models A and A+α admit 56–69% of the window's accesses.
- The F1-label models admit 4–14% (X1, X2); the CP-SAT labels 10–34%.

**Why the F1 labels miss it.** They are fitted to Region7's day-1 peaks, which are not scans, so the GBM learns that big-offset episodes are not worth admitting.

**The first-access gap persists.** Averaged over all six test instances it is 1.8–1.9% (F1 arms) vs 4.1–4.8% (Baleen arms). On Region7 alone (recomputed from `trials.csv`) it is 3.3–3.6% vs 7.6–9.4%.

**Without that instance** (description only): A 39.31, A+α 38.57, X1 38.18, Dc+α 38.07.
**Why this priority:** it is the concrete failure mechanism behind the headline negative.
Refs: `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L42-L51`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L61`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L20-L28`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L63-L73`, `changes/2_deployable_peak/wp3_test/trials.csv`, `changes/4_story/result/recompute_out.txt`

### F47 [P1] [TEST-POSTHOC] Post hoc on the H3′ test: the load-adaptive threshold on Baleen's own models is the best configuration
A+α scores 38.30, −2.5% vs Baleen.

| Comparison | Wins | Mean improvement | SE (retrain / instance) |
|---|---|---|---|
| A+α vs A | 5/6 | +0.96 | 0.16 / 0.39 |
| B+α vs B | 6/6 | +0.79 | |
| A+α vs B | 5/6 | +0.87 | |

The report states that A+α "was a control here and not the hypothesis", so it "needs its own pre-registered test (fresh region or reserve) before any claim". That test is H4 (F52).
**Why this priority:** it is the observation that redirected the project; post-hoc by construction.
Refs: `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60`, `changes/4_story/result/recompute_out.txt`

### F48 [P2] [TEST-PREREG] H3′ pre-declared comparisons without pass/fail: CP-SAT labels deploy better than PT labels, and retention is negative for every Ising- or CP-SAT-label arm
**Solver comparison.** Dc+α (same configuration, CP-SAT labels) beats X1 by 0.89 (3/6; instance SE 0.84).

**Retention** R = (A − X)/(OPT_peak-blind − OPT_peak-aware), with WP1's offline OPT values:

| Arm | X1 | X2 | B | A+α | B+α | Dc+α |
|---|---|---|---|---|---|---|
| R | −0.28 | −0.33 | +0.02 | +0.16 | +0.15 | −0.12 |

The proposal's H3 target was at least 60% retention.
**Why this priority:** pre-declared secondary metrics; they reinforce the verdict without adding a new one.
Refs: `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L14`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L75`, `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L98-L105`, `documents/proposal_docx_compose/proposal.js#L201`

## 5.5 Track C (WP8): deployment-aware Ising objectives, dev only

### F49 [P2] [DEV] Track C stage 1: the cheap deployed proxy fails its pre-registered validation, so every screen used full simulations
**The proxy fails.** The validity criterion was written 2026-10-05 14:25, before any proxy value existed.
- The label-level proxy PL has a median per-instance Spearman of 0.49 against simulated P100 (< 0.5) → C1 FAIL. C2 and C3 pass.
- PM, built on WP2's actual trained models, does no better (median 0.37).
- The proxy's first-access-admission estimate is reliable (Pearson 0.98 over 128 cells).

**Designs explored:**
- **Anchored (ANC):** small edits of Baleen's labels. ANC3 keeps 96% of F1's day-1 peak cut with ~300 label flips.
- **Top-k (TK):** ≈ F1 on day 1.
- **Student-field (STU):** STU10R1.

**Why this priority:** it explains why Track C cost full simulations and why no cheap screen exists for deployed effects; secondary.
Refs: `changes/2_deployable_peak/wp8_trackC/results/proxy_validation.md#L1-L28`, `changes/2_deployable_peak/wp8_trackC/results/proxy_validation.md#L63`, `changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L37`, `changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L9-L17`, `changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L85-L96`

### F50 [P1] [DEV] Track C stage 2 is negative: no deployment-aware Ising objective passes the pre-registered dev screen
**The screen.** The finalist rule was committed as `19d7992` before stage 2. Rep-1 screen score S1 = mean_i min(X1_i − Y_i, A+α_i − Y_i):

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
Refs: `changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L6-L20`, `changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md#L5-L41`, `changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L72-L100`, `changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L43-L55`

### F51 [P3] [DEV] Track C near miss: a single retrain of STU10R1 had the lowest dev mean, but the pre-registered gate rejected it
- E8:STU10R1 rep 1 averages 36.78, vs X1 rep 1 37.07 and A+α rep 1 37.86.
- Against the 3-retrain means of X1 and A+α it would score +0.041, with 6/8 wins on each.
- The pre-registered rep-1 vs rep-1 gate (S1 = −0.26) rejects it, and the source reports it "not acted on". It is one retrain inside X1's retrain noise (instance sd up to 2.6).
**Why this priority:** recorded so nobody resurrects it as evidence; minor.
Refs: `changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L11-L14`, `changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md#L39`

## 5.6 WP9: H4, the load-adaptive threshold on a fresh region (Region5)

### F52 [P0] [TEST-PREREG] H4 = YES: the load-adaptive admission threshold on Baleen's own models beats Baleen on fresh Region5 (pre-registered)
Region5 samples 0.1–0.6 had never been run deployed.

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

See F53 for the caveats that limit how strongly this can be read.
**Why this priority:** the project's only pre-registered deployed win.
Refs: `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L1-L19`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L7-L18`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L53`, `changes/2_deployable_peak/wp8_trackC/PLAN_C.md#L105-L108`, `changes/2_deployable_peak/wp9_region5/trials.csv`, `changes/4_story/result/recompute_out.txt`, `changes/4_story/result/protocol_commits.txt`

### F53 [P1] [TEST-PREREG] H4 caveats: the margin rests on the retrain-level SE, one instance carries most of the gain, and RejectX could not be matched
**One instance carries the gain.** On Region5 s0.5, A+α is 4.76 below A. On the other five instances the differences are −0.24 to +1.19 per the report (raw: −0.246 on s0.2 to +1.183 on s0.6).

**The margin passes only at retrain level.** The pre-registered rule uses the retrain-level SE (0.09). The instance-level SE (0.75) is reported but not used, and the +1.16 improvement is less than twice it. The same holds vs B (+1.35 vs instance SE 0.94).

**RejectX could not be matched.** On 5 of 6 instances RejectX's write rate jumps across the ±1% band between probabilities 1e-6 apart. The protocol therefore fixed, before the test, a two-sided rule (below both the authors' replays, 39.35, and the closest replays under the band, 39.28).

**Transfer.** α = −1 was chosen on Region6/7 dev data, so Region5 tests its transfer. The protocol stated before the test that 4/6 wins can fail on a smaller or noisier effect.
**Why this priority:** it states exactly how strong the one positive deployed result is.
Refs: `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L15-L17`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L33`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L59-L60`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L68-L76`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L90-L96`, `changes/4_story/result/recompute_out.txt`

### F54 [P1] [TEST-PREREG] The Ising record X1 fails the reported rule again on Region5 (no pass/fail was attached), by the same mechanism: one catastrophic scan-type instance
**Result.** X1 scores 38.09.
- vs A: 3/6, −1.92;
- vs B: 2/6, −1.73;
- vs A+α: 2/6, −3.07.

**Mechanism.**
- On s0.5, X1 scores 51.46 vs A 42.72. In 14 of the 15 matched s0.5 retrains (all arms), the peak is window 924, where 0.515 of the accesses end beyond 8 MB (raw `trials.csv`). The auto-research union amendment describes this instance as a big-offset scan peak that Baleen's model admits.
- X1's labels again cut first-access admission (2.2% vs 3.8%) and raise mean DT by 0.8.

**Retention:** X1 −0.54 vs A+α 0.31.

**Status.** The protocol reported the rule for X1 as an "Ising record" without attaching a pass/fail. It fails the rule against every reference.
**Why this priority:** it is the second fresh-region failure of the Ising-label configuration; it confirms H3′ was not a one-off.
Refs: `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L13`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L19-L31`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L35-L49`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L17`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L80`, `changes/3_autoresearch/work/union/SCOPE_AMENDMENT.md#L8-L12`, `changes/2_deployable_peak/wp9_region5/trials.csv`

### F55 [P3] [INFRA] WP9 preparation: the dry run and the static replays
**Dry run.** Region5 s0, arm A, 1 retrain. It matched in 3 sims at P100 32.93 and θ 0.683; the authors' s0 Baleen row has P100 33.47.

**Static replays.** RejectX/CoinFlip replays are bit-exact against the authors at their own probability (12/12, max diff 3e-10). CoinFlip matched on 6/6; RejectX on 1/6 only.
**Why this priority:** a pipeline check; no verdict depends on it.
Refs: `changes/2_deployable_peak/wp9_region5/PROGRESS.md#L18-L24`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L57-L60`

## 5.7 WP10: an Ising-fitted threshold table, tested on Region1 (H5)

### F56 [P2] [DEV] WP10 E1: no training-window proxy ranks threshold variants well enough (pre-registered validity criterion)
The criterion needed ≥ 0.70 within-retrain sign concordance with full simulations:
- P1 (day-1 emulator): 0.63 → FAIL;
- P2 (full trace, diagnostic): 0.65;
- P3 (delta proxy): 0.61.

Post hoc, even the simulator's own day-1 peak (P4) reaches only 0.61. So the limit is the day-1 → later-days shift, not emulator fidelity. Data: 120 WP2 retrains, 272 matched variant rows, 126 pairs.
**Why this priority:** it means table fits are candidate generators only; dev detail.
Refs: `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L16-L49`, `changes/2_deployable_peak/wp10_schedule/results/e1_verdict.json`

### F57 [P1] [OFFLINE] WP10 E2: the Ising solver (PT) and the classical solver (coordinate descent) find the same threshold tables
**Search space.** One-hot spins over 9 multipliers × 6 load buckets; 3003 monotone tables in total.

**Results.**
- PT (10 s) reaches the exhaustive optimum on 48/48 dev packs; CD on 46/48 (max gap 0.006).
- The tables are scale-equivalent on 46/48. On test, TB:cd produced the same tables as TB:pt and hence identical results.

**In-sample day-1 replayed peak:** 31.28 for the neutral table, 29.75 fitted (−1.5). The proxy is not valid (F56), so this is not evidence.
**Why this priority:** a clean instance of the Ising ≡ classical tie (F70), on the component that was tested on Region1.
Refs: `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L51-L60`, `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L82-L86`, `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L15`, `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L71`

### F58 [P2] [DEV] WP10 E3: TB:pt is the dev finalist under a rule written before any E2 solve or E3 simulation
**Screen.** S1 = TB:pt +0.41, TA:pt +0.10; both pass.

**Confirmation.**
- TB:pt qualifies: S3 = +0.19, 6/8 vs A+α, 7/8 vs B+α, dev mean 37.54.
- TA:pt fails: S3 = −0.30.

**Rule timing.** The finalist rule was written ≈17:32, before any E2 solve or E3 simulation.
**Why this priority:** it defines the H5 configuration; dev only.
Refs: `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L70-L80`, `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L98-L116`, `changes/2_deployable_peak/wp10_schedule/results/e3_tables.md#L13-L14`

### F59 [P0] [NEGATIVE-TEST] H5 = NO: the Ising-fitted load-bucket threshold table does not beat Baleen on fresh Region1
TB:pt scores 24.45.

| Reference | Mean | Wins | Mean improvement | SE |
|---|---|---|---|---|
| A | 24.14 | 1/6 | −0.31 | |
| B | 24.54 | 3/6 | +0.09 | 0.14 |
| B+α (best α arm) | 24.48 | 3/6 | +0.02 | 0.09 |

- It is below RejectX (28.20) and CoinFlip (50.39).
- **Run.** 108 evaluations, all matched.
- **Pre-registration.** `2738cba` (2026-10-19 19:23), with a disclosed deviation (F83).
- **Why Region1.** Region2 lacked the authors' release rows (no Baleen Fig 9 row for s0.2; no RejectX rows for s0.1/s0.2).
**Why this priority:** a decisive pre-registered negative for "put Ising in the threshold schedule".
Refs: `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L1-L17`, `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L20-L27`, `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L58-L64`, `changes/2_deployable_peak/wp10_schedule/trials_test.csv`, `changes/4_story/result/recompute_out.txt`, `changes/4_story/result/protocol_commits.txt`

### F60 [P1] [TEST-PREREG] On low-load Region1 the α arms do not help either (a comparison declared in advance as reported, no claim)
**Result.** A+α scores 24.62 and B+α 24.48, vs A 24.14. Recomputed: A+α vs A 1/6, −0.487; B+α vs A 1/6, −0.338.

**Why.** Region1 is a low-load trace: mean DT ≈ 12 util-% vs ≈ 19–21 on Regions 5–7, and Baleen's peak ≈ 24 vs 36–39. The threshold arms raise mean DT by ≈ 0.25 without lowering the peak.

**Status.** PROTOCOL_v2_H5 listed "A+α, B+α vs A, B (H4 on a new region)" in advance under "Reported, no claim"; H4's pass rule applied only to Region5. The results report labels it "Not pre-registered (H4 was a Region5 test)", which contradicts its own protocol. The source calls the load dependence "a hypothesis to examine (WP4), not a claim".
**Why this priority:** it bounds the one deployed win (F69).
Refs: `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19-L36`, `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L62-L64`, `changes/4_story/result/recompute_out.txt`

## 5.8 The auto-research loop (3_autoresearch, run 20261020_004634)

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
**Why this priority:** it defines how the negative verdict below should be read; infrastructure.
Refs: `changes/3_autoresearch/documents/GOOD_RESULT.md#L1-L59`, `changes/3_autoresearch/README.md#L1-L9`, `changes/3_autoresearch/autoscript/run_auto.sh#L1-L40`

### F62 [P2] [DEV] Auto-research H-CLS (Ising-fitted load × access-class threshold tables): no finalist
**Candidates.**
- **CB:pt** passed the retrain-1 screen (mean d +0.313, worst −0.151, 6/8) but failed the finalist rule: ineligible because Region1_s0 r2 was unmatched, and only 6/10 wins vs A+α (needs 7).
- **CB:ptm, CA:pt and CA:ptm** failed the gate.
- **UB:ptm** (one pooled table) failed the gate: −0.732, worst −4.516, with a Region6 s0.1 collapse.

**Lesson recorded.** A per-instance day-1 fit helps mainly by switching load adaptivity *off* where day 1 shows no gain.
**Why this priority:** a dev negative inside the loop; secondary.
Refs: `changes/3_autoresearch/result/FINAL_REPORT.md#L18-L32`

### F63 [P2] [DEV] Auto-research H-UX (union of Baleen's model and an Ising-label model): the dev finalist XA:F1PT
**Rule.** Admit iff s_A > θ·g OR s_X > κ·θ·g, where X is a GBM trained on the F1 min–max day-1 labels solved by PT.

**Screen.** Mean d +1.460 (XA, 6/8) and +1.072 (XG, 7/8).

**Finalist rule (n = 10 dev instances).** XA:F1PT scores 35.36:
- 10/10 vs A (+1.42, SE 0.19);
- 9/10 vs B;
- 7/10 vs A+α (+0.80, SE 0.18, worst −0.82).

**Mechanism.** The dev gain came mainly from Region6 scans: 36.77 vs A+α 38.65, peak big-offset share 0.20 vs 0.33. Region7 is nearly level (37.01 vs 37.11). The union did not restore Region7 first-access admission (3.0% vs 8.4% for A+α; A is 8.7% per the round-2 validator's correction).

**Caveat.** The union T1 protocol was committed after 9 of 16 union screen results had been read (F84).
**Why this priority:** it defines the configuration spent on T1/T2; selection-biased dev data.
Refs: `changes/3_autoresearch/result/FINAL_REPORT.md#L34-L58`, `changes/3_autoresearch/work/union/results/dev_finalist.json`, `changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L176-L186`

### F64 [P1] [NEGATIVE-TEST] Auto-research T1 (Region2): spent, failed, and unevaluable as pre-registered
**Why it could not be evaluated.**
- Region2_s0.2 cannot reach the target write rate for any arm: admit-all gives 11.5 MB/s.
- The release has no s0.2 row at DWPD 7.5, and the day-1 instance has 164 episodes vs 1285–1984 for the others. This was "not checked" before the protocol.
- Arm A had 0/6 matched retrains on s0.1 and 2/6 on s0.5.

**Fail-closed decision.** It was committed (`539f39e`) before `evaluation.json` was opened.

**Descriptive only (s0.3–0.6).** No reading favours Y beyond noise: Y is level with A and trails B, A+α and B+α.

| Y | A | B | A+α | B+α |
|---|---|---|---|---|
| 10.246 | 10.255 | 10.201 | 10.188 | 10.135 |

**Static baselines.** RejectX was unmatched on 6/6, and the baseline condition was uninformative.

**Load.** Region2 is very low-load (Baleen's peak ≈ 10).
**Why this priority:** it is one of the two test spends; its loss came from a design defect rather than an effect, hence P1.
Refs: `changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L1-L38`, `changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L45-L66`, `changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L79-L93`

### F65 [P0] [NEGATIVE-TEST] Auto-research T2 (Region4): the Ising-label union beats Baleen by a wide margin but not the threshold arm, so the loop ends NEGATIVE
Y = XA-F1PT scores 43.17.

| Reference | Mean | Wins | mean(R − Y) | SE_retrain | Rule |
|---|---|---|---|---|---|
| A | 50.72 | 4/5 | +7.547 | | ok |
| B | 56.71 | 5/5 | +13.541 | | ok |
| A+α (best α arm) | 42.87 | 1/5 | −0.300 | 1.117 | FAIL |

- Y is below RejectX (65.84) and CoinFlip (68.84).
- **Run.** All 30 cells have 3/3 matched retrains; 8 `__FAILED_` incident rows are kept.
- **Pre-registration.** `1cda6af` (05:19) was committed before any T1 or T2 test run. TEST_GO came at 07:05:04, after addendum `3fdba1b`.
- **Outcome.** The test budget (2 of 2) is exhausted and the loop's verdict is NEGATIVE.

Means recomputed (Appendix D).
**Why this priority:** it is the last and cleanest pre-registered test of an Ising/QUBO deployed component, and it shows the gain over Baleen is the threshold's.
Refs: `changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L1-L38`, `changes/3_autoresearch/result/FINAL_REPORT.md#L1-L7`, `changes/3_autoresearch/work/t2u_region4/trials_test.csv`, `changes/4_story/result/recompute_out.txt`, `changes/4_story/result/protocol_commits.txt`

### F66 [P1] [TEST-POSTHOC] Region4 replicates the H4 effect post hoc: A+α is 15% below Baleen
- A 50.72 → A+α 42.87 (−15%).
- Recomputed: A+α vs A 5/5, +7.847 (SE_retrain 0.446; instance SE 5.125); vs B 5/5, +13.841.
- A+α was a reference arm in T2, not a hypothesis; the source calls it "a new-region replication of H4, not pre-registered as H4 here".
- Region4's peaks are high-load bursts (peak-window big-offset share 0.02–0.04).
**Why this priority:** the strongest (post-hoc) support for the threshold's load dependence (F69).
Refs: `changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L40-L52`, `changes/3_autoresearch/result/FINAL_REPORT.md#L75`, `changes/4_story/result/recompute_out.txt`

### F67 [P1] [TEST-POSTHOC] Why the union did not transfer: neither test pool has scan peaks
The union's added value on dev was admitting big-offset scans at peak load (Region6). On the pools, the peak window's big-offset share is ≈ 0.01 (Region2) and 0.02–0.04 (Region4), against 0.33 for A+α on dev Region6.
- On Region4, Y lands at A+α's level with slightly lower peak-window admission (0.31 vs 0.41).
- The final report's conclusion: "the deployed peak gain comes from spending the write budget at high load, not from the Ising labels".
**Why this priority:** it is the mechanism of the loop's negative result, consistent with F68.
Refs: `changes/3_autoresearch/result/FINAL_REPORT.md#L71-L75`, `changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L50-L52`, `changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L63-L66`

## 6. Cross-cutting mechanisms

These findings combine evidence across phases and interpret the reported mechanism tables. Each is tagged by the evidence its main claim rests on. Supporting dev observations are marked "dev" inline and are not evidence on their own.

### F68 [P1] [TEST-POSTHOC] Day-1 min–max labels are brittle when the peak *type* changes (big-offset scan vs burst of new episodes)
The same pattern appears in every phase:
- **Phase-1 Q3 (held-out).** On 3/6 instances P100 was decided by rare scan-like windows (25–42% of accesses ending beyond 8 MB), and relabelling moved them either way.
- **WP2 dev.** The F1 labels plus α helped exactly where Region6's scans were present on day 1 (scan peaks 2/12 vs 9/12).
- **H3′ test.** Region7 s0.5's peak window was a scan (48% big-offset). The PT F1-label models (X1, X2) admitted 4–14% of its accesses and the CP-SAT F1-label models 10–34%, against 56–69% for A and A+α. X1 averaged 52.30.
- **H4 test.** X1 again had one catastrophic instance: Region5 s0.5, 51.46 vs A 42.72.
- **Union (auto-research).** It helped on dev Region6 scans but had nothing to act on in pools without scan peaks.

**Interpretation.** Labels optimised for one day's peak teach the GBM which *kind* of episode to admit. When the test days' peak is of another kind, the model rejects exactly the accesses that matter. This is post-hoc diagnosis across tests, not a pre-registered hypothesis.
**Why this priority:** this is the main explanation for the deployed negatives; mechanism, hence P1.
Refs: `changes/1_literature_review/explore/q3/RESULTS.md#L291-L299`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L207-L229`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L42-L51`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L19-L31`, `changes/3_autoresearch/result/FINAL_REPORT.md#L56-L58`, `changes/3_autoresearch/result/FINAL_REPORT.md#L71-L75`

### F69 [P1] [TEST-POSTHOC] The load-adaptive threshold's evidence status, region by region: pre-registered YES on Region5, post-hoc on Regions 6/7 and 4, null on Region1
| Region | Status | Source | A+α vs A |
|---|---|---|---|
| Region5 | **pre-registered (H4), YES** | F52 | 35.02 vs 36.17; 5/6; +1.16 |
| Regions 6/7 | **post-hoc** (WP3 control arm) | F47 | 38.30 vs 39.27; 5/6; +0.96 |
| Region4 | **post-hoc** (T2 reference arm) | F66 | 42.87 vs 50.72; 5/5; +7.847 |
| Region1 | **null / worse** (WP10; declared as a reported comparison, no claim, and no pass rule) | F60 | 24.62 vs 24.14; 1/6; −0.487 |
| Region2 | **descriptive only** (T1 unevaluable) | F64 | 10.188 vs 10.255 on s0.3–0.6 |

**Interpretation.** The pattern suggests the threshold helps where load is high: mean DT ≈ 12 on Region1 vs ≈ 19–21 on Regions 5–7, and Baleen's peak ≈ 10 on Region2 vs 50.72 on Region4. WP10 calls this "a hypothesis to examine (WP4), not a claim". Only the Region5 result is confirmatory.

None of these arms uses Ising/QUBO.
**Why this priority:** it states precisely how far the one deployed win generalises; it is a synthesis of mostly post-hoc evidence.
Refs: `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L31`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L53-L60`, `changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L23-L31`, `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L19-L36`, `changes/3_autoresearch/work/t1u_region2/RESULTS_test.md#L57-L66`, `changes/4_story/result/recompute_out.txt`

### F70 [P1] [OFFLINE] Ising and classical solvers: identical objectives where both reach the optimum, budget-dependent winners elsewhere, and no objective advantage that survived deployment
**Exact ties.**
- Phase 1: the floored Region7 s0.2 instance is reached (25.412) by CP-SAT, LS, PT and EIM at every budget.
- H2′ test: the floored Region7 s0.4 (23.8766) and Region6 s0.5 (23.6721) are ties.
- WP10: PT reaches the exhaustive table optimum on 48/48 packs and CD on 46/48. The tables are scale-equivalent on 46/48 packs, so TB:cd = TB:pt on 23/24 dev retrains and on the whole H5 test.
- Auto-research: PT and CP-SAT give identical F1 objectives on 36/36 Region2 and 30/30 Region4 label solves.

**Budget-dependent winners.**
- Ising best at 10 s in Q2 and at 3 s in H2′.
- Classical best at 60/300 s, at 1 s, and in rolling windows.
- On Track C's anchored energy, PT's mean objective was lower than CP-SAT's (13.55 vs 14.31; PT lower on 11/24 cells; CP-SAT never proved optimality). Yet CP-SAT's labels deployed better on one retrain (F50).

**Deployed differences between solver families come from *which* (near-)co-optimal label set each returns.**
- H3′: CP-SAT labels better by 0.89.
- Auto-research dev: PT labels better by 0.77 in the union.
- The final report: "It is not evidence that the Ising solver optimizes the QUBO better."

**Why this priority:** it answers plainly what Ising contributed as an optimiser: parity, not superiority.
Refs: `changes/1_literature_review/explore/q2/RESULTS.md#L251-L252`, `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L41-L43`, `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L83-L84`, `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L115`, `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L15`, `changes/3_autoresearch/result/FINAL_REPORT.md#L77-L94`, `changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L94-L96`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L14`

### F71 [P1] [TEST-PREREG] Retention of the offline gain never approached the proposal's 60% target for any Ising-label configuration
Retention R = (A − X)/(OPT_peak-blind − OPT_peak-aware) was a pre-declared "also reported" metric in the H3′ and H4 protocols. The proposal's H3 target was at least 60%.

**Test values:**
- H3′: X1 −0.28.
- H4: X1 −0.54.
- The highest test retentions belong to arms that use Baleen's labels, not peak labels: A+α 0.31 and B+α 0.46 on Region5. Their retention measures something other than label distillation.

**Dev context, not tests:**
- harness_eval: the best Ising arm C4 +0.01 / +0.01. The classical R2 arm had −0.04 / +0.11.
- WP2: X1 0.24.

**Why this priority:** it directly scores the proposal's H3; the test values are pre-declared reporting, so they carry weight.
Refs: `documents/proposal_docx_compose/proposal.js#L201`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L75`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L49`, `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L100-L105`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L84-L88`, `changes/1_literature_review/harness_eval/RESULTS.md#L250`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L231-L233`

### F72 [P2] [DEV] First-access admission is the recurring lever on Region7 (mostly dev evidence)
**Raising it helped on dev.** Phase-1 labels raised Region7 first-access admission from 6% to 15–28% via zero-value positives.

**The F1 labels lower it, and Region7 suffers.**
- WP2 dev: 2.4–2.8% vs Baleen's 8.7%.
- H3′ test, pooled over both regions: 1.8–1.9% vs 4.1–4.8%.

**Restoring it fixes Region7 but not Region6.**
- Track C's anchored labels restored it (0.121 vs X1 0.028) and gave the best Region7 dev mean, but lost Region6.
- The union did not restore it: 3.0%, vs A+α 8.4% (A 8.7%).

Region6 first-access admission stays at or below 1.3% in every WP2 and Track C arm.
**Why this priority:** a mechanism detail tying the phases together; secondary.
Refs: `changes/1_literature_review/explore/q3/RESULTS.md#L244-L251`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L207-L229`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L63-L73`, `changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L15-L19`, `changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L85-L95`, `changes/3_autoresearch/result/FINAL_REPORT.md#L56-L58`, `changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L176-L186`

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

### F73 [P1] [INFRA] Every phase-2 and auto-research test protocol was committed to git before its test ran
Commits from `git log`; run times from each report.

| Test | Protocol commit | Test run |
|---|---|---|
| H2′ | `fd54e76`, 2026-10-03 01:13:51 | 01:24:38 to 01:45 |
| H3′ | `cba9970`, 2026-10-04 09:16:01 | launched 2026-10-05 (G3 waiver `84a0c1d` 14:13:01); result committed 2026-10-16 (`46608e0`) |
| Track C rule | `19d7992`, 2026-10-16 13:54:17 | stage-2 driver first launched un-bwrapped ≈1 minute before its 13:56 relaunch |
| H4 | `d10e572`, 2026-10-16 13:54:30, then `c8f655a`, 21:30:11 | to 2026-10-17 05:31 |
| H5 | `2738cba`, 2026-10-19 19:23:04 | chain 19:23 to 20:47 |
| T1 (union) | `76cf5c8`, 2026-10-20 04:36:45 | TEST_GO 06:26:50 |
| T2 | `1cda6af`, 05:19:24 | TEST_GO 07:05:04, after addendum `3fdba1b` at 07:04:57 |

The earlier cls_table T1 protocol (`9650674`) is void: it had no finalist and wrote no TEST_GO.
**Why this priority:** this is what makes the TEST-PREREG labels in this story auditable.
Refs: `changes/4_story/result/protocol_commits.txt`, `changes/4_story/result/git_timeline.txt`, `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L3-L5`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L4`, `changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L132`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L1-L4`, `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L1-L5`, `changes/3_autoresearch/result/FINAL_REPORT.md#L60-L69`

### F74 [P2] [INFRA] Each deployed test's evaluator was written and validated on earlier data before the test data existed, and the drivers refused to run without a go-file
- **WP3.** `evaluate_test.py` was written at 16:50 on 2026-10-04, before any test data. Run on WP2's dev trials, it reproduces the dev comparisons exactly (X1 vs A +1.301 ± 0.251, 6/8). The test driver refused to start without `G3_SIGNED`.
- **WP9.** Its evaluator, checked on WP3's published trials, reproduces the WP3 report (A+α vs A +0.965, 5/6, SE 0.160 / 0.391; X1 vs A −1.265). The driver required `TEST_GO`.
- **WP10.** Its evaluator, checked on WP9's trials, reproduces WP9 (A+α vs A 5/6, +1.155, SE 0.094 / 0.745; B+α vs B 6/6, +1.887).
- **Auto-research T2.** The evaluator is identical to the contract's `validate.py`.

**Why this priority:** it removes "the analysis was tuned to the outcome" as an explanation for any test verdict.
Refs: `changes/2_deployable_peak/wp3_test/PROGRESS.md#L1-L4`, `changes/2_deployable_peak/wp3_test/PROGRESS.md#L36-L39`, `changes/2_deployable_peak/wp3_test/PROGRESS.md#L81`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L82`, `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L67`, `changes/3_autoresearch/work/t2u_region4/PROTOCOL.md#L44-L51`

### F75 [P2] [INFRA] Phase-1 pre-registration (Q1–Q3) is file-dated, not git-attested
**What the files say.**
- `changes/1_literature_review/explore/PROTOCOL.md` states "Frozen: 2026-09-28, before any tuning".
- The finalist rules are timestamped inside progress logs (Q3 rule at 19:35; Q2 simulation plan at 17:00).
- Q3 ran 2026-09-28 15:53 → 2026-09-29 02:30; the Q2 held-out campaign started 18:25.
- Track B states "No git commits".

**What git says.** The first commit containing the protocol is `be284a3` (2026-09-29 15:02:03), after these runs.

**Consequence.** The Q1–Q3 verdicts are credible as pre-specified held-out evaluations, but their pre-registration cannot be verified from git.
**Why this priority:** it qualifies three phase-1 verdicts; it does not change them.
Refs: `changes/1_literature_review/explore/PROTOCOL.md#L3`, `changes/1_literature_review/explore/q3/RESULTS.md#L3`, `changes/1_literature_review/explore/q2/RESULTS.md#L77`, `changes/1_literature_review/explore/q2/RESULTS.md#L338-L341`, `changes/1_literature_review/explore/q3/PROGRESS.md#L79`, `changes/1_literature_review/explore/q2/PROGRESS.md#L38`, `changes/4_story/result/protocol_commits.txt`

### F76 [P1] [INFRA] Gate G3 (a teammate review of the overlay patch) was waived by the captain; no teammate sign-off is recorded for scope v2
Scope v2 required one teammate to review `PATCH.diff` before any held-out run (G3).
- It was waived by the captain on 2026-10-05 (commit `84a0c1d`), recorded before the WP3 test.
- The coordinator review at CP1, G1 and parity stand.
- `PATCH.diff` sha256 `2a914eb589bb` was unchanged through WP9 and WP10.

`changes/SCOPE_v2.md` still reads "pending confirmation by Ching-Hao Chiu and Jie Fu". The amendments were recorded by the coordinator under the captain's standing approval (1.2b) or not at all (1.2c, 1.2d; F04).
**Why this priority:** it is a governance deviation that a reader must know about; it touches every scope-v2 result.
Refs: `changes/SCOPE_v2.md#L3`, `changes/SCOPE_v2.md#L40-L44`, `changes/SCOPE_v2.md#L50`, `./RESEARCH.md#L76`, `changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md#L1-L5`, `changes/2_deployable_peak/wp3_test/RESULTS_test.md#L4`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L52`, `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L41`, `changes/4_story/result/git_timeline.txt`

### F77 [P3] [INFRA] Frozen-artifact checks always passed and sandboxing was the rule (with the exceptions in F78–F82); leak-check hits came from other tools and agents
**Frozen artifact.** Every stage reports `check_frozen.sh` → "frozen OK (94 files)": reproduction, Q2, Q3, harness_eval, CP1, WP2, WP5, WP3, Track C, WP9, WP10, and the auto-research T1/T2.

**Sandboxing rules:**
- every Baleen process under `bwrap` with a private `/tmp`;
- one `train` at a time (flock);
- timing on cores 0–7, with SMT siblings 12–19 kept idle from 2026-10-01 16:22 (before that, see F80);
- envs used read-only.

**Leak-check hits outside the project** came from other tools and agents:
- the editor, Copilot and desktop files;
- an unrelated user project;
- git activity by the coordinator or another agent: 25 `.git/objects` files at CP1, 101 at WP5 dev, 318 at H2′, and 371 files under `.git/` at WP2.

**Why this priority:** routine hygiene; recorded for completeness.
Refs: `./RESEARCH.md#L96-L116`, `changes/2_deployable_peak/wp0_overlay/CP1.md#L141-L160`, `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L430-L440`, `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L189-L195`, `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L263-L281`

### F78 [P3] [INFRA] Phase-1 incidents: a 25-second tuning overlap and a stray `__pycache__` file in the frozen tree's wrapper
1. **Tuning overlap.** A chained launcher's `pgrep` pattern containing '{' failed and started F1 tuning concurrently with the F2b tuner on cores 0–7 for ~25 s.
   - The 8 overlapping rows are kept and flagged `contaminated_overlap`.
   - The affected studies were deleted and re-run.
2. **Stray `__pycache__` file.** An interactive inspection created the file 0_reproduce/repro/__pycache__/common.cpython-311.pyc at 15:54, before the sandbox was sourced.
   - It was removed at 16:06 and the directory mtime restored.
   - `check_frozen.sh` was OK before and after.
3. **Synthetic-audit leak check** (not empty; 72 lines), attributed to other processes. It includes `changes/1_literature_review/ising_followup/survey.md`, "presumably written by another agent". The auditor could not prove the attribution of the fontconfig caches.

**Why this priority:** disclosed incidents with no effect on any verdict.
Refs: `changes/1_literature_review/explore/q2/RESULTS.md#L355-L358`, `changes/1_literature_review/explore/q3/RESULTS.md#L310-L314`, `changes/1_literature_review/ising_followup/audit/AUDIT.md#L208-L217`, `./RESEARCH.md#L111`

### F79 [P3] [INFRA] Phase-2 timing incidents (WP1/WP5), each handled by superseding or flagging rows
1. **Unpinned script on the timing cores.** An unpinned ad-hoc script ran on cores 0–2 on Oct 1, 14:44:30–14:47:40.
   - All WP5 tuning up to then was superseded: 193 rows kept as `superseded_restart`.
   - The WP1 Region4 s0 solves were re-run.
2. **SMT sibling exposure.** The first 1-s dev evaluation ran with Track A on the SMT siblings for the Ising runs only. 192 rows were superseded and the evaluation re-run; conclusions unchanged (LS 23.03 vs PT 23.25).
3. **Foreign processes on cores 0–7.** 63 timing runs had a mean foreign load > 0.2 CPUs: 55 tuning instance-runs, 6 hl-split LP runs and 2 WP1 solves. None was a selected trial; all are kept and flagged.
4. **Scaling driver.** It was launched unpinned and stopped at its affinity assertion before any run.
5. **Analysis script.** The H2′ analysis script got two bug fixes after the runs and before its first output (a pandas column access and an f-string), with no rule change.
6. **Rolling secondary.** It overlapped a short editor-process burst.

**Why this priority:** disclosed; none affected a selected configuration or a verdict.
Refs: `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L406-L425`, `changes/2_deployable_peak/wp1_offline/RESULTS.md#L111-L116`, `changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L174-L185`, `./RESEARCH.md#L112-L115`

### F80 [P2] [INFRA] SMT-sibling exposure in phase-1 timing and early WP5 tuning, a seed-reuse artefact in tuning, and a lost session
**SMT siblings.** Logical CPUs k and k+12 share a physical core.
- The phase-1 rule (timing on cores 0–7, Baleen sims on 8–23) let simulations run on the SMT siblings of the timing cores. WP5's log notes "phase-1 timings had the same exposure".
- The phase-1 core audit sampled only cores 0–7 (94.5 CPU-s of foreign use in the held-out phase), so the sibling load during the Q2 timing runs is unquantified. Both solver families were exposed alike.
- From 15:05 on Oct 1 Track B pinned its sims to 8–11 and 20–23, and Track A kept off 12–19 from 16:22.
- WP5 tuning still averaged about 2 sibling threads (Ising 2.1, classical 1.8). Dev-evaluation, hl-split and label runs had 0.

**Seed reuse.** Trial 0 is each solver's phase-1 configuration, and the TPE sampler is seeded as in phase 1. As a result LS and EIM repeat that configuration and have 11 distinct configurations each; CP-SAT has 10–11 and LP 2, against 12 for PT, MILP, SB and MQ. "Equal trials" therefore means equal trial counts, not equal distinct configurations.

**Lost session.** The coordinator session ended on the evening of Oct 1. The resumable drivers restarted scaling and the extra rolling runs, and nothing was lost or duplicated.

**Why this priority:** it qualifies the timing fairness behind the phase-1 10 s Ising win and the "equal tuning" statement; disclosed in the sources.
Refs: `changes/2_deployable_peak/wp5_ising/PROGRESS.md#L50-L54`, `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L395-L406`, `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L423-L425`, `changes/1_literature_review/explore/q2/RESULTS.md#L348-L354`, `changes/SCOPE_v2.md#L45`

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
Refs: `changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md#L102-L110`, `changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L100-L107`, `changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L141-L143`, `changes/4_story/result/git_timeline.txt`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L51-L56`, `changes/2_deployable_peak/wp9_region5/PROGRESS.md#L71`, `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L6`, `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L14`, `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L91-L95`

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
Refs: `changes/1_literature_review/explore/q3/RESULTS.md#L315-L317`, `changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L109-L110`, `changes/2_deployable_peak/wp8_trackC/PROGRESS.md#L132`, `changes/3_autoresearch/result/FINAL_REPORT.md#L104-L134`

### F83 [P2] [INFRA] WP10 committed its H5 protocol after the dev confirmation had run, before its P100 values were read
**Disclosed deviation.**
- The E3 confirmation driver finished at 19:20.
- `PROTOCOL_v2_H5.md` was committed at 19:23:04 (`2738cba`).
- `e3_eval.py` was run on those rows only inside the chain afterwards.
- The finalist (TB:pt) was chosen mechanically by the rule written ≈17:32.

**Header-time inconsistency.** The protocol's own header says it was written at "19:25", after its own commit time. The header time is therefore approximate.
**Why this priority:** a real deviation from "protocol before the data exist", mitigated by a mechanical rule; it matters for H5's evidence label.
Refs: `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L42`, `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L1-L7`, `changes/2_deployable_peak/wp10_schedule/PROGRESS.md#L105-L116`, `changes/4_story/result/protocol_commits.txt`

### F84 [P1] [INFRA] Auto-research integrity disclosures (final report §5)
1. **DEV_RULES timing.** R0–R2 had no git attestation until `96506745` (02:23). Their headers were written with guessed times and rewritten in place with `sed`, contradicting the file's "never edited" line.
2. **Post-commit procedure changes.**
   - `chain_dev2.py` ordering was changed.
   - DEV_RULES R4 and `ADDENDUM_R4.md` came 12 minutes after the union T1 protocol commit, motivated by CB:pt's ineligibility. R4 never fired.
3. **Late union protocol.** The union T1 protocol was committed after 9 of 16 union screen results had been read (large, positive).
4. **T1 design defect.** The constructed Region2_s0.2 row was infeasible at the operating point and was not checked.
5. **T1 static baselines** were unmatched, and the evaluator averages static P100 regardless of `matched`.
6. **Convergence search** stalls on write-rate plateaus; it was left unchanged because it was pre-registered.
7. **Latent base-model race.** It is fail-closed and never fired (27/27 and 15/15 A trainings audited).
8. **T2 incident.** 8 pre-simulation `__FAILED_` rows.
9. **Non-dev information seen.** Trace-directory sizes, and the existence (no values) of reserve-sample rows in one printed listing.
10. **Bookkeeping errors**, e.g. the G1_v5 report was first written as `G1_v4.md`.

**Why this priority:** these bear on the credibility of the loop's process. The verdict is negative, so they cannot have inflated a claim.
Refs: `changes/3_autoresearch/result/FINAL_REPORT.md#L96-L134`

### F85 [P3] [INFRA] The round-1 auto-research validators failed the run on two blocking findings; both were fixed before T2's TEST_GO
**B1 (both validators).**
- T1 contained an instance no arm can match. On Region2_s0.2 every arm ends at the θ floor of 1e-4 (admit-all), with WR 11.510 and P100 189.068.
- The committed T2 chain would have halted on T1's missing `good_result`.
- **Fix:** T1 was closed as spent and failed (`539f39e`), and the T2 chain condition was amended (`3fdba1b`), both before T2's TEST_GO.

**B2.** The G1_v5 report had been written under the name `G1_v4.md` by a copied report script. It was renamed (`e45a7fd`).

**Round 2:** both validators PASS with 0 open findings.
**Why this priority:** the validator loop worked as intended; process detail.
Refs: `changes/3_autoresearch/result/validator_integrity_stats_round_1.md#L118-L170`, `changes/3_autoresearch/result/validator_integrity_stats_round_1.md#L273-L274`, `changes/3_autoresearch/result/validator_red_team_round_1.md#L32-L40`, `changes/3_autoresearch/result/validator_red_team_round_2.md#L106-L107`, `changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L229-L230`, `changes/3_autoresearch/work/t2u_region4/ADDENDUM_T1_UNEVALUABLE.md#L1-L24`, `changes/4_story/result/git_timeline.txt`

### F86 [P2] [INFRA] Six items the round-2 validators raised are not carried into the auto-research notebook or final report
Both round-2 validators passed with 0 blocking findings, but list non-blocking items. Checked here against the files:
1. **Interim look.** At 08:18, with 28 of 90 T2 evaluations done, the worker printed per-arm P100 of the completed rows ("report planning only"). `LAB_NOTEBOOK.md` has no entry for it. T2 was fully locked by then, so the verdict is unaffected.
2. **Jaccard ranges.** The ranges in FINAL_REPORT §4 and the T2 report §4 are slightly wrong: CP-SAT goes down to 0.569 on Region4_s0.5.
3. **Retrain from scratch.** One T2 training (B r1, Region4_s0.2) was killed and retrained from scratch, which §5.8 does not mention.
4. **Stale STATUS.** The body of `STATUS.md` is stale below its final header.
5. **Thin classical-control evidence.** The H-CLS evidence (CD tables) is retrain-1 only, n = 1–4 instances per arm, and was never compared. The final report does not say so.
6. **A mislabelled baseline.** FINAL_REPORT §2.2 still says the union did not restore "Baleen's" first-access admission (3.0% vs 8.4%). The 8.4% is A+α; Baleen A is 8.7%.
**Why this priority:** open disclosure gaps in the record; no verdict impact.
Refs: `changes/3_autoresearch/result/validator_red_team_round_2.md#L55-L90`, `changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L158-L203`, `changes/3_autoresearch/result/LAB_NOTEBOOK.md#L417-L446`, `changes/3_autoresearch/result/FINAL_REPORT.md#L56-L58`

### F87 [P2] [INFRA] Privacy redaction of a public repo (2026-10-04); git history still holds the originals
The repo is public.
- Leak-check listings, CPU audits and notes had included paths and process names from the user's unrelated work: file names only, never contents.
- They were replaced by category labels with `tools/privacy_scrub.py` (commit `55a125b`, 2026-10-04). Code, results and numbers are unchanged.
- **Earlier commits still contain the originals.** Purging them needs a history rewrite, which is the captain's decision.
- `python3 tools/privacy_scrub.py --check` must print nothing before every push.
**Why this priority:** a disclosure about the repository, not about results.
Refs: `./RESEARCH.md#L108`, `./RESEARCH.md#L117`, `tools/privacy_scrub.py`, `changes/4_story/result/git_timeline.txt`

### F88 [P3] [INFRA] Documentation drift in the index file
`./RESEARCH.md` is partly stale or imprecise:
- It says "Last updated: 2026-10-16" but records 2026-10-19/20 results.
- Its file map lists only wp0/wp1/wp5/wp2 under `2_deployable_peak` and omits WP3/WP8/WP9/WP10 and `3_autoresearch`.
- WP4, WP6 and WP7 are still "to do".
- It states the unverified ≈11.3% (F08) and the "≈70k" dense-SB limit (F31).
- `changes/SCOPE_v2.md` §1a records amendment 1.2b but not 1.2c/1.2d (F04).
**Why this priority:** a reader using the index should know which statements to check; minor.
Refs: `./RESEARCH.md#L4`, `./RESEARCH.md#L28-L29`, `./RESEARCH.md#L36`, `./RESEARCH.md#L41`, `./RESEARCH.md#L78-L89`, `changes/SCOPE_v2.md#L44`

### F89 [P3] [INFRA] An earlier auto-research launch (Codex worker, run 20261019_233548) did no work
That run made two auto commits about one minute apart (`74577ee`, `f4d758e`). They changed only the loop status files (validation note "no claim file yet"). The launcher was then replaced by the headless Opus 5.5 launcher (`204bce2`). The reported run is 20261020_004634.
**Why this priority:** completeness of the record; no results.
Refs: `changes/4_story/result/git_timeline.txt`, `changes/3_autoresearch/README.md#L1-L9`

### F90 [P2] [INFRA] The hardware differed from the proposal's plan: no GPU
**Planned:** "16 cores / 32 threads, 125 GiB RAM, one 24 GB GPU".

**Used:** a 24-thread AMD Ryzen 9 9900X with 123 GB and no GPU. The paper-selection desk check had likewise assumed a 16-core Threadripper with a 24 GB RTX A5000 (F06).

**Consequence.** Simulated bifurcation and CIM, which are designed for GPUs and FPGAs, ran only on CPU. The audit notes the slow-per-call arms were "under-converged, not intrinsically worse". Every phase-2 Ising timing result is a CPU result.
**Why this priority:** it limits how far the Ising-solver negatives generalise to GPU or hardware Ising machines.
Refs: `documents/proposal_docx_compose/proposal.js#L250`, `changes/1_literature_review/explore/q2/RESULTS.md#L46-L50`, `changes/1_literature_review/ising_followup/audit/AUDIT.md#L195-L198`, `documents/top_doable_papers_filtered.md#L13-L20`

### F91 [P2] [INFRA] Planned but never measured
- **The artifact's own peak policy.** `PolicyUtilityPeakServiceTimeSize` (oracle peak window) is SCOPE.md's ablation (a), and the proposal's H2 required beating it. No results file reports a run: not measured (search in Appendix D).
- **F3 and F4.** F3 (the eviction-coupled QKP, where an Ising edge was considered most plausible) was not implemented. Q2 was not run on F4.
- **Region coverage.** Offline breadth covered Regions 4–7 only. The proposal's H1 was "averaged over the seven Meta traces"; Regions 1–3 were never run offline.
- **Phase-1 harness test.** Samples 1–9 were not run.
- **Work packages.** WP4 (mechanism), WP6 (mid-term report) and WP7 (paper) are "to do".
**Why this priority:** these gaps bound the claims; secondary.
Refs: `changes/SCOPE.md#L63`, `documents/proposal_docx_compose/proposal.js#L199-L200`, `changes/1_literature_review/explore/q2/RESULTS.md#L279-L295`, `changes/2_deployable_peak/wp1_offline/RESULTS.md#L17-L23`, `changes/1_literature_review/harness_eval/RESULTS.md#L276`, `./RESEARCH.md#L29`

### F92 [P1] [INFRA] The 0.7–0.9 reserve was never used in a deployed run, but WP1 simulated it offline, including the Region6/7 reserve
**What the plan says** (PLAN §3):
- dev = Region7/Region6 samples 0–0.3;
- test = samples 0.4–0.6;
- "Reserve for the final paper: samples 0.7–0.9, touched once, at the end";
- H1′ breadth: Region4 and Region5, samples 0–0.9, offline only.

**What WP1 did.** WP1 (H1′, committed `08ad0d2` on 2026-10-03) built and simulated *offline* (OPT) instances for Regions 4–7 × samples 0–0.9. That includes the 6 Region6/7 reserve instances (s0.7–0.9) among 12 reserve-sample rows in `wp1_table.csv`.

**What later protocols say.** PROTOCOL_v2_H3 §2 then lists the reserve as "untouched", which is true only for deployed runs. Every deployed protocol and the auto-research contract exclude the reserve:
- PROTOCOL_v2_H4 §2: "no job, instance dump or label set exists" in WP9's area;
- PROTOCOL_v2_H5 §2;
- auto-research contract §3. The loop's report: "No reserve sample was built or simulated".

**Mitigation.** WP1's offline results on samples ≥ 0.4 were not used for any WP5 choice.

**Consequence.** A final deployed confirmation on the reserve is still uncontaminated by any deployed or tuning outcome. Their offline OPT peaks are known, though, so the reserve is not pristine.
**Why this priority:** it qualifies the one remaining clean test set (section 9) and corrects the "untouched" wording in the protocols.
Refs: `changes/2_deployable_peak/PLAN.md#L27-L31`, `changes/2_deployable_peak/wp1_offline/RESULTS.md#L1-L3`, `changes/2_deployable_peak/wp1_offline/RESULTS.md#L111-L113`, `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`, `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md#L29`, `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md#L23`, `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md#L27`, `changes/3_autoresearch/documents/GOOD_RESULT.md#L34-L35`, `changes/3_autoresearch/result/FINAL_REPORT.md#L116-L120`, `changes/4_story/result/git_timeline.txt`

## 8. What we can and cannot claim

Status words:
- **Supported:** the evidence meets its rule.
- **Refuted:** a pre-registered test failed.
- **Not supported:** the dev or offline evidence is negative or absent.
- **Post-hoc:** an observation only.
- **Not measured:** never run.

| # | Claim | Status | Evidence | Findings | Main refs |
|---|---|---|---|---|---|
| 1 | Baleen's released artifact reproduces the paper | Supported with nuance: baselines bit-exact; Baleen within ±0.6 of released-metric runs; the Fig 9 `tracedrop` bars do not reproduce; "≈11.3%" unverified | REPRO | F07, F08 | `changes/0_reproduce/RESULTS.md` |
| 2 | Min–max (peak-aware) selection lowers the simulated peak offline vs Baleen's peak-blind oracle | **Supported**: 6/6 held-out (27.06 vs 32.28); 36–37/39 instances, −13.0 to −13.7%; about −16% on Regions 5–7 | TEST-PREREG (Q1, git caveat) + OFFLINE | F18, F25 | `changes/1_literature_review/explore/q2/RESULTS.md`, `changes/2_deployable_peak/wp1_offline/RESULTS.md` |
| 3 | …also on Region4 | Weak: 3–5%; headroom gate not met | OFFLINE | F27 | `changes/2_deployable_peak/wp1_offline/RESULTS.md` |
| 4 | The offline gain is due to the Ising/QUBO solver | **Not supported**: classical LP/CP-SAT selections simulate the same | OFFLINE | F19 | `changes/2_deployable_peak/wp1_offline/RESULTS.md` |
| 5 | Ising beats classical solvers on the same formulation (10/60/300 s) | **Refuted** (Q2) | NEGATIVE-TEST | F20 | `changes/1_literature_review/explore/q2/RESULTS.md` |
| 6 | Ising beats classical solvers at tight 1/3/10 s budgets | **Refuted** (H2′) | NEGATIVE-TEST | F28 | `changes/2_deployable_peak/wp5_ising/RESULTS_test.md` |
| 7 | Ising samplers are the best family at one short budget | Descriptive only (10 s in Q2; 3 s in H2′); not a pass; rolling windows reverse it | TEST-PREREG (secondary) | F20, F28, F30 | same |
| 8 | Matrix-free SB scales to real 0.4% unions on CPU where the dense SB package does not | **Supported** (reported contribution, no pass/fail) | OFFLINE | F31 | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md` |
| 9 | Ising peak labels survive distillation into Baleen's unchanged GBM | **Refuted** (Q3) | NEGATIVE-TEST | F33 | `changes/1_literature_review/explore/q3/RESULTS.md` |
| 10 | With the causal `load` feature the GBM can fit peak-aware labels | Supported on dev (learnability gate) | DEV | F37 | `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md` |
| 11 | Ising labels + `load` (+ α) beat Baleen deployed | **Refuted** (H3′). X1 also fails on Region5, where the rule was reported without a pass/fail | NEGATIVE-TEST | F44, F54 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md` |
| 12 | Ising labels add deployed value beyond the load-adaptive threshold | **Refuted** (H3′-labels; auto-research T2 vs A+α) | NEGATIVE-TEST | F45, F65 | `changes/3_autoresearch/work/t2u_region4/RESULTS_test.md` |
| 13 | An Ising-fitted threshold table beats Baleen deployed | **Refuted** (H5, Region1) | NEGATIVE-TEST | F59 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md` |
| 14 | Deployment-aware Ising labels (anchored, top-k, student) help | Not supported on dev (no finalist); never tested | DEV | F50 | `changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md` |
| 15 | The load-adaptive threshold on Baleen's own models beats Baleen deployed on a fresh region | **Supported** on Region5 (H4), with caveats: retrain-level SE; one instance carries most of the gain | TEST-PREREG | F52, F53 | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md` |
| 16 | …and on other regions | Post-hoc: yes on Regions 6/7 and Region4; no on Region1; uninformative on Region2 | TEST-POSTHOC | F47, F60, F66, F69 | see F69 |
| 17 | The threshold's benefit depends on the load level | Hypothesis only (WP4) | TEST-POSTHOC | F60, F69 | `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md` |
| 18 | Proposal H1 (≥ 5% vs stock Baleen, averaged over 7 traces) | Offline vs Baleen's own peak-blind oracle: met on average over the 4 traces measured (13.0–13.7%), but Region4 alone gives only 3.0–5.4%, and Regions 1–3 were not measured. Deployed (Ising labels vs stock Baleen): not met | OFFLINE / NEGATIVE-TEST | F25, F44, F91 | `documents/proposal_docx_compose/proposal.js` |
| 19 | Proposal H2 (Ising beats the artifact's greedy peak policy and a greedy warm start by ≥ 3%) | Beats Baleen-order greedy by far; the artifact's peak policy was **not measured**; does not beat classical solvers | OFFLINE | F20, F91 | `changes/1_literature_review/explore/q2/RESULTS.md` |
| 20 | Proposal H3 (≥ 60% retention online) | **Not supported**: test retention of Ising-label arms −0.28 and −0.54, a pre-declared reported metric with no pass/fail | TEST-PREREG (reported metric) | F71 | `changes/2_deployable_peak/wp3_test/RESULTS_test.md` |
| 21 | An Ising/QUBO-centric component beats deployed Baleen and the threshold arm (auto-research contract) | **Refuted**: T1 unevaluable, T2 failed vs A+α; budget exhausted | NEGATIVE-TEST | F64, F65 | `changes/3_autoresearch/result/FINAL_REPORT.md` |
| 22 | Ising and classical solvers return the same objective where both reach the optimum | Supported (exact ties on floored instances, WP10 tables, auto-research F1 labels) | OFFLINE | F57, F70 | see F70 |

**One-sentence summary for a paper:**
- The min–max *formulation* is a robust offline win, about 16% on three of four regions.
- Ising/QUBO solvers match but do not beat classical solvers.
- The Ising peak labels did not survive deployment in any pre-registered test.
- The only confirmed deployed gain, −3.2% on Region5, comes from a load-adaptive admission threshold on Baleen's own models.

## 9. Open questions and next steps

1. **The reserve is unused for deployment.** Samples 0.7–0.9 have never been used in a deployed run. WP1 did simulate them offline (OPT) for H1′ on Regions 4–7, including the Region6/7 reserve (F92). PLAN.md reserves them for one final use (`changes/2_deployable_peak/PLAN.md#L28-L31`).
2. **What a final confirmation should test** (recommendation, not a pre-registration):
   - **The arm:** the only surviving claim, the load-adaptive threshold (A+α, and B+α) vs A and B, with α = −1 and ref = 20 frozen.
   - **Where:** on the reserve of the regions with peak pressure (Region5, Regions 6/7, Region4), committed before any run.
   - **The margin rule:** require the instance-level SE as well as the retrain-level one, because H4 passed only on the latter (F53).
   - **Load dependence:** state it explicitly as a hypothesis (F69).
   - **Pool feasibility:** check it first (admit-all write rate ≥ target; static-baseline knob sensitivity), as the auto-research report recommends after the T1 defect (`changes/3_autoresearch/result/FINAL_REPORT.md#L136-L140`).
3. **WP4 mechanism work is still open** (`./RESEARCH.md#L122`):
   - per-window attribution of the peak;
   - why B+α is more uniform than A+α on Region5 (`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L17`);
   - the scan-vs-burst classification of peak windows across regions.
4. **What an Ising/QUBO contribution would need** (`changes/3_autoresearch/result/FINAL_REPORT.md#L140`): a mechanism the threshold cannot reach, or a workload whose peaks are scans present in the training day. Candidates never built:
   - the eviction-coupled QKP F3 (`changes/1_literature_review/explore/q2/RESULTS.md#L281-L288`);
   - GPU or hardware Ising machines (F90).
5. **Never measured** (F91):
   - the artifact's own peak policy;
   - Regions 1–3 offline;
   - F4 in the solver comparison;
   - harness samples 1–9.
6. **Tooling debts:**
   - the convergence search stalls on write-rate plateaus;
   - `validate.py` trusts `matched` and averages unmatched static rows (`changes/3_autoresearch/result/validator_integrity_stats_round_2.md#L204-L214`);
   - the auto-research notebook lacks the interim-look entry (F86).
7. **Governance:**
   - teammate confirmation of scope v2 and G3 (F76);
   - recording amendments 1.2c/1.2d in `changes/SCOPE_v2.md` if any of their results is ever cited as more than a negative;
   - the history-rewrite decision for the privacy redaction (F87).
8. **Deliverables:** the mid-term talk/report (WP6) and the paper (WP7) are still "to do" (`./RESEARCH.md#L29`).

## Appendix A. Per-experiment tables (copied from the cited sources)

## A.1 Reproduction, Figure 9 bars at sample 0 (`changes/0_reproduce/work/results/fig9_summary.md#L20-L29`)
| trace | policy | prefetch | author | ours | Δ | spread of authors' runs | pass |
|---|---|---|---|---|---|---|---|
| 20230325/Region6 | Baleen | All on Partial Hit | 41.31 | 43.27 | +1.96 | 0.00 | PASS |
| 20230325/Region6 | CoinFlip | No prefetching | 44.42 | 43.45 | -0.98 | 1.95 | PASS |
| 20230325/Region6 | RejectX | No prefetching | 42.59 | 42.32 | -0.26 | 0.53 | PASS |
| 20230325/Region7 | Baleen | ML-Range on ML-When | 37.59 | 40.06 | +2.47 | 0.00 | FAIL |
| 20230325/Region7 | CoinFlip | No prefetching | 49.71 | 48.96 | -0.75 | 1.50 | PASS |
| 20230325/Region7 | RejectX | No prefetching | 41.59 | 42.46 | +0.86 | 1.73 | PASS |

Released-metric Baleen runs (`changes/0_reproduce/RESULTS.md#L28-L33`):

| Trace | Prefetching | Authors' peak (write rate) | Ours at matched write rate | Δ |
|---|---|---|---|---|
| Region7 | ML-Range on Partial Hit | 40.57 (34.67) | 40.03 (35.46) | −0.54 |
| Region7 | ML-Range on Every Miss | 42.56 (35.23) | 42.91 (35.58) | +0.35 |
| Region6 | ML-Range on Partial Hit | 42.00 (35.27) | 42.21 (35.41) | +0.21 |
| Region6 | ML-Range on Every Miss | 43.89 (36.01) | 43.38 (35.86) | −0.51 |

## A.2 Phase 1, Q1 and the Q2 simulation clause, 300 s selections (`changes/1_literature_review/explore/q2/RESULTS.md#L259-L269`)
| instance | PT P100 (3 seeds) | EIM P100 (3 seeds) | best classical at 300 s: P100 | Baleen peak-blind OPT | PT − OPT |
|---|---|---|---|---|---|
| Region7_s0.1 | 27.61 ± 0.16 | 27.34 ± 0.22 | cpsat 27.38 | 33.68 | −6.07 |
| Region7_s0.2 | 27.90 ± 0.54 | 28.02 ± 0.18 | milp 28.21 | 35.28 | −7.38 |
| Region7_s0.3 | 26.76 ± 0.21 | 26.49 ± 0.31 | cpsat 26.64 | 31.23 | −4.47 |
| Region6_s0.1 | 26.41 ± 0.20 | 25.94 ± 0.39 | cpsat 26.11 | 30.90 | −4.49 |
| Region6_s0.2 | 26.38 ± 0.11 | 26.54 ± 0.24 | cpsat 26.23 | 30.62 | −4.23 |
| Region6_s0.3 | 27.32 ± 0.17 | 27.38 ± 0.08 | cpsat 27.15 | 31.96 | −4.64 |
| **mean** | **27.063** | **26.951** | **26.954** | **32.277** | **−5.21** |

Q2 mean objective per method over the 6 held-out instances (`changes/1_literature_review/explore/q2/RESULTS.md#L200-L211`):

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

## A.3 Phase 1, Q3 held-out verdict (`changes/1_literature_review/explore/q3/RESULTS.md#L11-L17`)
| finalist | wins vs Baleen online (need ≥ 4/6) | mean improvement (need > 2 SE) | mean P100 vs RejectX 39.05 / CoinFlip 44.69 | Q3 |
|---|---|---|---|---|
| P0 pure soft peak (LSE) | 2/6 | −0.41 vs 2 SE = 0.56 | 37.97 | NO |
| T2 LSE + DT blend + trust region | 2/6 | −1.07 vs 2 SE = 0.85 | 38.62 | NO |
| C2 T2 energy over GBM-feature cells | 2/6 | −0.57 vs 2 SE = 0.96 | 38.13 | NO |

Per-instance means (3 matched retrains; T2 has 2 on Region7 s0.2) (`changes/1_literature_review/explore/q3/RESULTS.md#L196-L233`):

| instance | Baleen online | P0 | T2 | C2 | RejectX | CoinFlip |
|---|---|---|---|---|---|---|
| Region7_s0.1 | 36.57 | 36.11 | 38.39 | 36.68 | 38.66 | 46.00 |
| Region7_s0.2 | 36.79 | 36.89 | 36.69 | 37.05 | 38.00 | 41.97 |
| Region7_s0.3 | 37.81 | 38.50 | 41.39 | 38.08 | 38.89 | 45.19 |
| Region6_s0.1 | 40.93 | 41.66 | 42.28 | 44.06 | 42.25 | 50.02 |
| Region6_s0.2 | 36.26 | 37.74 | 36.29 | 36.14 | 37.29 | 43.85 |
| Region6_s0.3 | 36.96 | 36.90 | 36.70 | 36.75 | 39.19 | 41.09 |

## A.4 WP1, H1′ by region (recomputed from `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`; output `changes/4_story/result/recompute_out.txt`)
| method | all 39: wins / mean reduction | Region4 (9) | Regions 5–7 (30) |
|---|---|---|---|
| LP + repair | 36 / 13.03% | 6 / 4.59% | 30 / 15.57% |
| CP-SAT 300 s | 36 / 13.15% | 6 / 3.04% | 30 / 16.19% |
| PT 300 s | 37 / 13.69% | 7 / 5.37% | 30 / 16.18% |

## A.5 H2′ test, per-budget means over the 6 test instances (`changes/2_deployable_peak/wp5_ising/RESULTS_test.md#L29-L39`)
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

## A.6 WP2 dev, mean P100 over 8 dev instances (`changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md#L138-L153`)
| config | mean | config | mean |
|---|---|---|---|
| A | 38.50 | X1 Ea-1.0:F1PT | 37.20 |
| B | 38.44 | X2 Ea-0.5:F1PT | 37.84 |
| C:F1PT | 38.81 | Ea-1.0:F1CPSAT | 38.46 |
| D:F1PT | 38.37 | A+α (Aa-1.0) | 37.88 |
| C:F1EIM | 39.09 | B+α (Ba-1.0) | 38.43 |
| D:F1EIM | 38.46 | B with α = −0.5 (Ba-0.5) | 38.05 |
| Dc:F1CPSAT | 38.74 | RejectX / CoinFlip | 39.88 / 45.07 |

## A.7 H3′ test, P100 per instance (`changes/2_deployable_peak/wp3_test/RESULTS_test.md#L18-L28`)
| instance | A | B | A+α | B+α | X1 | X2 | Dc+α | RejectX | CoinFlip |
|---|---|---|---|---|---|---|---|---|---|
| Region6 s0.4 | 37.58 | 37.43 | 36.12 | 36.57 | 36.93 | 37.36 | 37.36 | 38.56 | 45.07 |
| Region6 s0.5 | 38.75 | 38.95 | 37.50 | 38.17 | 37.24 | 38.00 | 37.61 | 37.96 | 44.68 |
| Region6 s0.6 | 43.04 | 42.94 | 43.79 | 42.72 | 42.02 | 42.01 | 41.91 | 47.21 | 58.04 |
| Region7 s0.4 | 39.51 | 39.86 | 38.66 | 38.71 | 37.20 | 37.78 | 37.57 | 39.29 | 49.24 |
| Region7 s0.5 | 39.07 | 38.31 | 36.95 | 37.05 | **52.30** | **52.15** | 47.49 | 42.05 | 51.60 |
| Region7 s0.6 | 37.65 | 37.55 | 36.80 | 37.05 | 37.51 | 37.96 | 35.91 | 39.31 | 43.19 |
| **mean** | 39.27 | 39.17 | **38.30** | 38.38 | 40.53 | 40.88 | 39.64 | 40.73 | 48.64 |

## A.8 Track C stage 2, rep-1 screen (`changes/2_deployable_peak/wp8_trackC/results/stage2_summary.md#L7-L18`)

The D8 rows are the same retrains without α (sim-only, not eligible).

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

## A.9 H4 test (Region5), P100 per instance (`changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L21-L31`)
| instance | A | B | A+α | B+α | X1 | RejectX* | CoinFlip |
|---|---|---|---|---|---|---|---|
| s0.1 | 39.92 | 40.36 | 39.32 | 39.55 | 40.89 | 46.69 | 46.96 |
| s0.2 | 33.92 | 33.79 | 34.16 | 33.51 | 33.22 | 36.08 | 37.87 |
| s0.3 | 37.72 | 37.94 | 37.47 | 37.28 | 36.00 | 39.68 | 46.75 |
| s0.4 | 26.39 | 26.18 | 26.02 | 25.95 | 26.22 | 28.12 | 29.21 |
| s0.5 | 42.72 | 43.91 | 37.96 | 35.07 | 51.46 | 46.05 | 61.36 |
| s0.6 | 36.38 | 36.02 | 35.19 | 35.51 | 40.78 | 39.50 | 44.67 |
| **mean** | 36.17 | 36.37 | **35.02** | **34.48** | 38.09 | 39.35 | 44.47 |

\* RejectX is matched only on s0.4; the low-side mean is 39.28 (two-sided rule, F53).

## A.10 H5 test (Region1), P100 per instance (`changes/2_deployable_peak/wp10_schedule/RESULTS_test.md#L21-L31`)
| instance | A | B | A+α | B+α | TB:pt (= TB:cd) | RejectX | CoinFlip |
|---|---|---|---|---|---|---|---|
| s0.1 | 24.81 | 25.19 | 25.50 | 25.37 | 25.19 | 27.53 | 35.33 |
| s0.2 | 22.02 | 22.27 | 22.15 | 22.41 | 22.17 | 24.62 | 47.40 |
| s0.3 | 30.69 | 31.69 | 30.60 | 30.45 | 31.18 | 37.20 | 59.42 |
| s0.4 | 22.68 | 22.72 | 23.33 | 22.72 | 22.78 | 25.81 | 55.18 |
| s0.5 | 22.13 | 22.90 | 22.53 | 22.55 | 23.00 | 25.40 | 42.86 |
| s0.6 | 22.50 | 22.47 | 23.63 | 23.35 | 22.39 | 28.63 | 62.13 |
| **mean** | **24.14** | 24.54 | 24.62 | 24.48 | 24.45 | 28.20 | 50.39 |

## A.11 Auto-research T2 (Region4), P100 per instance (`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L23-L31`)
| instance | A | B | A+α | B+α | Y = XA-F1PT | control XA-F1CPSAT | RejectX | CoinFlip |
|---|---|---|---|---|---|---|---|---|
| s0.2 | 59.07 | 58.88 | 49.58 | 50.85 | 49.61 | 55.05 | 58.31 | 64.52 |
| s0.3 | 76.14 | 75.99 | 48.95 | 51.38 | 49.37 | 51.23 | 77.09 | 83.26 |
| s0.4 | 51.72 | 59.60 | 51.60 | 51.15 | 51.22 | 50.96 | 73.35 | 74.19 |
| s0.5 | 32.85 | 55.25 | 32.41 | 33.45 | 32.93 | 32.60 | 55.84 | 56.74 |
| s0.6 | 33.81 | 33.84 | 31.81 | 32.49 | 32.72 | 32.00 | 64.59 | 65.48 |
| **mean** | 50.72 | 56.71 | **42.87** | 43.87 | **43.17** | 44.37 | 65.84 | 68.84 |

## Appendix B. Timeline

Commit times come from `changes/4_story/result/git_timeline.txt` (all branches, `git log --all`); run times come from the cited reports.

| Date (2026) | Event | Record |
|---|---|---|
| 09-14 | Literature-review pipeline and top-8 feasibility report (`2264e66`) | git |
| 09-26 | Proposal documents (`527f8bc`); reproduction starts | `changes/0_reproduce/RESULTS.md#L5` |
| 09-27 | Scope v1 frozen | `changes/SCOPE.md#L3` |
| 09-28 00:17 | Reproduction and QUBO literature review committed (`0981c50`) | git |
| 09-28 | harness_eval (sample 0); Q1–Q3 protocol frozen in-file; Track A runs 15:53 → 09-29 02:30 (Q3 held-out 21:50 → 02:21); Q2 held-out from 18:25 (core audit 18:31 → 01:31) | F15, F75 |
| 09-29 15:02 | Real-harness and deep-explore campaign committed (`be284a3`); phase-2 plan + scope v2 (`27fb6f0`) | F75 |
| 10-01 | Plan restores Ising as required (`5e49299`); CP1 overlay committed (`f79808f`, 16:20) | F05, F36 |
| 10-01 → 10-03 | WP5 tuning; WP1 runs; WP2 dev runs begin (10-01 16:25) | F29, F25 |
| 10-03 00:11 | WP1 H1′ committed (`08ad0d2`) | F25 |
| 10-03 01:13 | H2′ protocol committed (`fd54e76`); test 01:24–01:45; result `b6f44e2` 02:10 | F28 |
| 10-04 09:16 | H3′ protocol + WP2 dev results (`cba9970`) | F39, F44 |
| 10-04 17:30 | Privacy redaction (`55a125b`) | F87 |
| 10-05 14:13 | G3 waived (`84a0c1d`); H3′ test launched; Track C stage 1 starts (14:18) | F76 |
| 10-16 12:40 | H3′ result: FAIL (`46608e0`) | F44 |
| 10-16 13:54 | Track C stage-1 results and finalist rule (`19d7992`); H4 pre-registered (`d10e572`) | F49, F50, F52 |
| 10-16 20:27 | Track C stage 2 negative (`4ba4bcc`) | F50 |
| 10-16 21:30 | H4 protocol (`c8f655a`); Region5 test runs to 10-17 05:31 | F52 |
| 10-19 16:14 | H4 result: YES (`cad1603`) | F52 |
| 10-19 17:03 → 19:23 | WP10 E0–E3 dev; H5 protocol (`2738cba`, 19:23) | F56–F58, F83 |
| 10-19 20:50 | H5 result: NO (`b4c4a95`) | F59 |
| 10-19 23:34 | Auto-research contract and Codex loop (`3a79daf`); the Codex run does no work | F61, F89 |
| 10-20 00:43–00:56 | Opus launcher (`204bce2`); DEV_RULES R0 written 00:56 | F61, F84 |
| 10-20 02:23 | cls_table T1 protocol (`9650674`, later void) | F62, F73 |
| 10-20 04:36 / 05:19 | Union T1 protocol (`76cf5c8`) / T2 protocol (`1cda6af`) | F73 |
| 10-20 06:27 | Union finalist XA:F1PT; T1 TEST_GO 06:26:50 (`f74bf8b`) | F63, F64 |
| 10-20 07:04–07:05 | T1 closed as unevaluable (`539f39e`); T2 addendum (`3fdba1b`); T2 TEST_GO 07:05:04 | F64, F65 |
| 10-20 10:01 | T2 result: FAILED (`80233a6`); final report (`b0d6e2b`) | F65 |
| 10-20 10:03–11:26 | Dev control confirmation; STOP_EXHAUSTED written 11:26 (`4fe0688`). The EXHAUSTED loop status (11:44) is uncommitted in the working tree | `changes/3_autoresearch/result/STOP_EXHAUSTED`, `changes/3_autoresearch/result/LOOP_STATUS.txt` |
| 10-20 15:41 | This story loop (run 20261020_154140) | `changes/4_story/result/LOOP_STATUS.txt` |

## Appendix C. File map (where each kind of evidence lives)

| Topic | Primary files |
|---|---|
| Index, ledger, decisions | `./RESEARCH.md`, `changes/SCOPE.md`, `changes/SCOPE_v2.md`, `changes/2_deployable_peak/PLAN.md` |
| Proposal, spec, paper | `documents/PeakBaleen_Proposal.pdf` (text: `documents/proposal_docx_compose/proposal.js`), `documents/CourseProject-Fall2026.pdf`, `documents/Baleen_FAST24_Wong.pdf` |
| Reproduction | `changes/0_reproduce/RESULTS.md`, `changes/0_reproduce/REPRODUCE_PLAN.md`, `changes/0_reproduce/work/results/fig9_summary.md`, `changes/0_reproduce/work/results/retrain_dist.csv` |
| Literature review | `changes/1_literature_review/lit_review_qubo/REPORT.md`, `changes/1_literature_review/SWAPPABLE_QUBO_ISING_REPORT.md`, `changes/1_literature_review/ising_followup/survey.md`, `changes/1_literature_review/ising_followup/audit/AUDIT.md` |
| Phase-1 real harness | `changes/1_literature_review/harness_eval/RESULTS.md` |
| Phase-1 Q1–Q3 | `changes/1_literature_review/explore/PROTOCOL.md`, `changes/1_literature_review/explore/q2/RESULTS.md`, `changes/1_literature_review/explore/q2/trials.csv`, `changes/1_literature_review/explore/q3/RESULTS.md`, `changes/1_literature_review/explore/common/Q3_FORMULATION.md` |
| WP0 overlay | `changes/2_deployable_peak/wp0_overlay/CP1.md`, `changes/2_deployable_peak/wp0_overlay/PATCH.diff`, `changes/2_deployable_peak/wp0_overlay/G3_REVIEW.md` |
| WP1 H1′ | `changes/2_deployable_peak/wp1_offline/RESULTS.md`, `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv` |
| WP5 Ising track | `changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md`, `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md`, `changes/2_deployable_peak/wp5_ising/RESULTS_test.md`, `changes/2_deployable_peak/wp5_ising/results/scaling_summary.md` |
| WP2 deployed dev | `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md`, `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md`, `changes/2_deployable_peak/wp2_deployed/trials.csv` |
| WP3 H3′ test | `changes/2_deployable_peak/wp3_test/RESULTS_test.md`, `changes/2_deployable_peak/wp3_test/trials.csv`, `changes/2_deployable_peak/wp3_test/results/evaluation.json` |
| WP8 Track C | `changes/2_deployable_peak/wp8_trackC/PLAN_C.md`, `changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md`, `changes/2_deployable_peak/wp8_trackC/results/stage1_table.md`, `changes/2_deployable_peak/wp8_trackC/results/proxy_validation.md` |
| WP9 H4 test | `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md`, `changes/2_deployable_peak/wp9_region5/RESULTS_test.md`, `changes/2_deployable_peak/wp9_region5/trials.csv` |
| WP10 H5 test | `changes/2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md`, `changes/2_deployable_peak/wp10_schedule/G1_v3.md`, `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md`, `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md`, `changes/2_deployable_peak/wp10_schedule/trials_test.csv` |
| Auto-research | `changes/3_autoresearch/documents/GOOD_RESULT.md`, `changes/3_autoresearch/result/FINAL_REPORT.md`, `changes/3_autoresearch/result/LAB_NOTEBOOK.md`, `changes/3_autoresearch/result/DEV_RULES.md`, `changes/3_autoresearch/work/t1u_region2/RESULTS_test.md`, `changes/3_autoresearch/work/t2u_region4/RESULTS_test.md` |
| This story | `changes/4_story/code/check_story.py`, `changes/4_story/code/recompute.py`, `changes/4_story/result/recompute_out.txt`, `changes/4_story/result/git_timeline.txt`, `changes/4_story/result/protocol_commits.txt` |

## Appendix D. Recomputation one-liners (all read-only)

1. **Test-arm means and paired pass-rule quantities** (F25, F44, F47, F52, F59, F60, F65, F66, F69). Raw ledgers: `changes/2_deployable_peak/wp3_test/trials.csv`, `changes/2_deployable_peak/wp9_region5/trials.csv`, `changes/2_deployable_peak/wp10_schedule/trials_test.csv`, `changes/3_autoresearch/work/t2u_region4/trials_test.csv` and `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv`. Script `changes/4_story/code/recompute.py`; output `changes/4_story/result/recompute_out.txt`:
   ```
   python3 changes/4_story/code/recompute.py > changes/4_story/result/recompute_out.txt
   ```
   - Only `matched == True` rows count.
   - A configuration's mean is the mean over instances of the per-instance mean over retrains.
   - SE_retrain = sqrt(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i)/n; SE_inst = sd(d_i)/√n.
   - Every recomputed value agrees with its source report.
2. **Git timeline and protocol commit times** (F73, F75, F76, F89):
   ```
   git log --all --reverse --date=format:'%Y-%m-%d %H:%M:%S' --format='%h %ad %s' > changes/4_story/result/git_timeline.txt
   for f in <protocol files>; do echo "$f | added $(git log --diff-filter=A --date=format:'%Y-%m-%d %H:%M:%S' --format='%h %ad' -- $f | tail -1) | last $(git log -1 --date=format:'%Y-%m-%d %H:%M:%S' --format='%h %ad' -- $f)"; done > changes/4_story/result/protocol_commits.txt
   ```
3. **The ≈11.3% reproduction figure has no source other than the index** (F08):
   ```
   grep -rn "11\.3%\|≈11.3" --include=*.md --include=*.csv --include=*.txt --include=*.json . | grep -v "/env/\|\.cache\|site-packages\|4_story"
   ```
   It matches only `RESEARCH.md:36` and an unrelated "11.3%" in `changes/2_deployable_peak/wp1_offline/RESULTS.md#L87` (a top-5 reduction).
4. **The artifact's own peak policy was never run** (F91):
   ```
   grep -rln "PolicyUtilityPeakServiceTimeSize" --include=*.md changes | grep -v "/env/\|baleen_code\|overlay"
   ```
   It matches only `changes/SCOPE.md`.
5. **No interim-look entry in the auto-research notebook** (F86):
   ```
   grep -n "08:18" changes/3_autoresearch/result/LAB_NOTEBOOK.md
   ```
   No output.
6. **The union dev A+α mean** quoted in `./RESEARCH.md#L28` (36.16) equals XA:F1PT's mean (35.359) plus its mean improvement vs A+α (0.802), from `changes/3_autoresearch/work/union/results/dev_finalist.json`:
   ```
   python3 -c "import json;r=json.load(open('changes/3_autoresearch/work/union/results/dev_finalist.json'))['rule'][0];print(round(r['mean']+r['A+a_mean'],2))"
   ```
