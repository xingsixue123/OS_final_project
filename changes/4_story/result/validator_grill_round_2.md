# Validator 2 (grill: completeness, priorities, honesty), round 2 of 5

**Target:** `changes/4_story/STORY.md`, story-writer round 2 (run 20261020_154140, 103 findings).
**Run:** 2026-10-20. Read-only; this is the only file written.

## Method
1. **What I read.**
   - The whole round-2 story, `RESEARCH.md` and `changes/4_story/result/WRITER_NOTES.md`.
   - My own round-1 report, and validator 1's round-2 report (`validator_citation_round_2.md`).
2. **Round-1 fixes.** I re-checked every round-1 blocking item (G1–G9) and the 17 non-blocking items against the new text.
3. **Sources opened for this round:**
   - the four lightly cited progress logs: `wp0_overlay`, `wp1_offline`, `wp3_test`, `harness_eval`;
   - `wp8_trackC/PROGRESS.md` and `PLAN_C.md`;
   - `q2/PROGRESS.md` and q2 RESULTS §5;
   - harness_eval RESULTS §3;
   - `PROTOCOL_v2_H2.md` §7–8 and SCOPE_v2 §1a/§3;
   - `SCOPE_v2_1b.md`;
   - FINAL_REPORT §3–7, the T2 PROTOCOL and the LAB_NOTEBOOK prerequisites entries;
   - the proposal's §3.1 (`proposal.js:199-201`).
4. **A keyword sweep** (incident, bug, deviation, post hoc, killed, contaminated …) over every tracked `RESULTS*.md`, `PROGRESS.md`, `LAB_NOTEBOOK.md`, `CP1.md` and `G1*.md`. Every hit is covered by a finding, except the items below.
5. **Raw-data checks** (read-only, inline, nothing written):
   - `wp10_schedule/results/solves_test.csv`: the fitted tables per retrain;
   - the mtimes of the `wp3_test` ledger, `evaluation.json` and the T2 prerequisites.
6. **Link check.** All 1,108 links resolve on disk, all 103 `#Fxx` anchors exist, and every `#Lx-Ly` range falls inside its file. Four targets are not tracked in git (endorsed from validator 1 below).
7. **Ledger-hypothesis check.** Every ledger hypothesis still has a finding:
   - R: F07, F08, F98;
   - Q1: F18; Q2: F20; Q3: F33;
   - H1′: F25; H2′: F28; S: F31;
   - H3′: F44, F45; H4: F52, F53; H5: F59;
   - the loop: F61–F67.
8. **No duplication of validator 1.** Where one of its items also fails a grill criterion, I list it under "Endorsed" and do not count it. The one exception is a non-blocking item I promote, and I say so where I do it.

**Own errors corrected here.**
- Two round-2 errors came from my round-1 wording:
  - the "while Track C ran" firewall, from my non-blocking item 1 (blocking item 1 below);
  - the over-general LP-start sentence, from G1 (validator 1's R2-B1).
- I name them so the writer knows the fix overrides my earlier text.

## Round-1 blocking items: status

| Item | Status |
|---|---|
| G1 LP-started "Ising" | Fixed in the legend, F21, F24 and the abstract. **But overreached:** "every deployed label set" is false for the Q3 and Track C labels (validator 1 R2-B1, endorsed). |
| G2 H4 caveats | Fixed in the abstract, the F52 title and lead, F53, §8 row 15, the summary and F66. |
| G3 headline wording | Fixed in the §8 summary and the F65 title. |
| G4 full label-solver record | Fixed in F70, F32, F64 and F65. The retrain-SE count is wrong (validator 1 R2-B4, endorsed). |
| G5 prior art | Fixed: F95, abstract, §8 row 15, §9 item 3. |
| G6 privacy in the current tree | Fixed: F87, §9 item 8. No pattern is quoted. |
| G7 permissions skipped | Fixed: F61 and the header. |
| G8 one-click usability | Fixed: links, anchors and line ranges all resolve. Untracked targets remain (validator 1 N27/N28, endorsed). |
| G9 PLAN dev-signal gate | Fixed: F94, cross-references, Appendix B. |

The round-1 non-blocking items 1–17 are all addressed, apart from the error introduced by item 1 (blocking item 1 below).

## Blocking issues

### 1. The H3′/Track C "firewall" is misstated: Track C did not run during the 11-day gap, and its stage-2 rule was fixed after the H3′ outcome was known to the coordinator
**What the story says.**
- **F73 (STORY L1557):** "**Firewall.** The H3′ outcome sat unevaluated for 11 days while Track C ran, and Track C records that `wp3_test` was never read."
- **F44 (P0, L1048):** "in between, Track C ran without reading any WP3 output".
- **Appendix B (L2238–2240)** has no row for the gap or for the H3′ evaluation time.
- This wording came from my round-1 non-blocking item 1.

**What the sources say.**
- **The H3′ test ended on 10-05.** The `wp3_test/trials.csv` mtime is 2026-10-05 17:41:42, the last ledger row.
- **Track C ran only briefly on 10-05, alongside the H3′ test, and was then down until 10-16.**
  - `wp8_trackC/PROGRESS.md:82`: "2026-10-05 ~15:05 the session ended".
  - `:86`: "2026-10-16 resumed (coordinator: H3' driver exited …)".
  - `:105`: "session down 10-05 ~15:05 to 10-16".
  - Its stage 1 ran 14:18–15:05 on 10-05, at the same time as the H3′ test (14:23–17:41).
- **The H3′ outcome was known before Track C's stage-2 rule was committed.**
  - `wp3_test/results/evaluation.json` mtime: 2026-10-16 12:33:58. The result was committed at 12:40:27 (`46608e0`).
  - Track C's stage-2 finalist rule and short-list were written on 10-16 (`PROGRESS.md:97`; `PLAN_C.md` §3 "fixed 2026-10-16, before any Stage-2 simulation"; no clock time is logged).
  - That rule was committed at 13:54:17 (`19d7992`), 74 min after the H3′ result commit, in the same minute as the coordinator's H4 addendum (`d10e572`).
  - `PLAN_C.md:105-108` states that the coordinator wrote the addendum "based on the H3′ result" and that "Track C remains blind to the H3′ test outcome in its design work … It changes no Track C design, short-list or finalist rule".
- **The gap was not a firewall.** The 11 days separated the test from its evaluation, but no Track C work happened in them. The firewall that does exist is narrower:
  - Track C's own processes never read `wp3_test` (`PROGRESS.md:9`, `:110`);
  - the coordinator asserts in writing that Track C stayed blind (`PLAN_C.md:108`).

**Why blocking (criterion 4).** F73 is the finding that "makes the TEST-PREREG labels in this story auditable", and F44 is a P0. Both state a firewall the record does not show. They also omit that a dev decision rule (Track C stage 2) was fixed after the coordinator had seen a test outcome. Track C's result was negative, so no claim was inflated, but the integrity record must be exact.

**Fix.**
1. **F73.** Replace the Firewall sentence with: "The H3′ test finished 10-05 17:41 and was evaluated 10-16 12:33 (`evaluation.json` mtime; result `46608e0` 12:40). Track C ran only 10-05 14:18–~15:05 and was down until 10-16. Its stage-2 finalist rule was written on 10-16 and committed (`19d7992`, 13:54:17) after the H3′ result, together with the H4 addendum. The coordinator records that Track C's design stayed blind to H3′ (`PLAN_C.md:108`), and Track C's processes never read `wp3_test` (`PROGRESS.md:9,110`)."
2. **F44.** Change "in between, Track C ran without reading any WP3 output" to "Track C's processes never read WP3 output; its session was down 10-05 ~15:05 → 10-16 ([F73](#F73))".
3. **F50.** Add one clause: the finalist rule was committed after the H3′ result (refs above).
4. **Appendix B.** Add "10-05 ~15:05 → 10-16: Track C session down" and "10-16 12:33: H3′ evaluated (`evaluation.json`)".
5. **Refs.** Cite `wp8_trackC/PROGRESS.md#L82-L86`, `#L97`, `#L105` and `PLAN_C.md#L105-L108`. This also resolves validator 1's N18.

### 2. F96 says every phase-1 forking path was "followed by negative verdicts", but the Q2 formulation switch also set the formulation of the headline positive Q1
**What the story says.**
- **The title** (L184, L1612): "Phase-1 forking paths and interim looks, all followed by negative verdicts".
- **The priority line** (L1628): "none changed a held-out verdict, which was negative each time".
- **The Q2 switch bullet** mentions only that "Q2 failed anyway".

**What the sources say.**
- **The switch.** `q2/PROGRESS.md:31-32` makes F2b the "Primary formulation for Q1/Q2". `:52-53` switches the "primary Q2 formulation" to F1 on dev evidence that favoured Ising: "Ising ahead at 10 s on both dev instances; F2b favours the classical LS".
- **Q1 used the switched formulation.** Q1 (P0, TEST-PREREG, the headline positive) is judged on the F1 + PT and F1 + EIM 300-s selections (F18; `q2/PROGRESS.md:38-41`: "Q1 … use the 300 s held-out solutions of every Ising finalist").
- **The switch probably did not change Q1.** F2b's own dev selections also simulated far below Baleen's peak-blind OPT: F2b pgreedy / LS / PT 28.53 / 28.47 / 28.53 on Region7 and 28.26 / 28.28 / 28.24 on Region6, against 34.52 / 35.56 (`q2/PROGRESS.md:50-51`).

**Why blocking (criteria 3 and 4).** The finding meant to disclose forking paths states the opposite of the record for the project's headline positive result. A reviewer who checks it will find that the formulation behind Q1 = YES was chosen after a dev look.

**Fix.**
1. **Title:** "Phase-1 forking paths and interim looks; the formulation switch also preceded Q1 (YES), all others negative".
2. **Q2-switch bullet.** Add: "The switch also fixed the formulation on which Q1 passed. It was decided on the solver race, not on the peak gain, and F2b's own dev selections also simulated ≈6–7 points below Baleen's peak-blind OPT (`q2/PROGRESS.md#L50-L51`), so Q1 is unlikely to depend on it."
3. **Priority line:** "… none changed a held-out verdict; the one positive verdict downstream of a switch (Q1) is insensitive to it on dev".
4. **F18:** add a one-line pointer to F96.

### 3. H5 is ranked as a "decisive" P0 negative, but the fitted table was the neutral (no-op) table on 10 of 18 test retrains, and the "Ising" fit equals an exhaustive enumeration that takes ~2 s
This promotes validator 1's non-blocking N14, which I re-verified, and adds the enumeration point.

**Evidence.**
- **Neutral tables.** `wp10_schedule/results/solves_test.csv` (`mult`, solver `pt`, 18 test retrains): 10 of 18 fitted tables are all 1.0:
  - s0.1 r1–r3;
  - s0.2 r2–r3;
  - s0.4 r1, r3;
  - s0.5 r1–r3.
  
  A neutral table is plain arm B. On dev only 3 of 48 packs were neutral (`wp10_schedule/PROGRESS.md:85`).
- **PT adds nothing over classical solvers.** On all 18 test retrains, PT's table is identical to the classical exhaustive (`ex`) and CD tables in the same file. `PROGRESS.md:83`: "exhaustive enumeration takes 1.5–2.3 s (3003 tables)", against PT's 10 s. The search space is small enough to enumerate, so an Ising solver cannot add anything here.
- **The test barely exercised a table.** TB:pt 24.45 vs B 24.54 (F59). The test largely compared B with B-like arms.
- **What the story says.**
  - F59's priority line: "a decisive pre-registered negative for 'put Ising in the threshold schedule'".
  - The abstract (L28) lists H5 as a failed "Ising-fitted threshold table".
  - §8 row 13 says "Refuted".
  - F57 calls WP10 "a clean instance of the Ising ≡ classical tie" without saying that exhaustive search is faster.
  - Neither the source report nor the story mentions the neutral fits.

**Why blocking (criteria 2 and 3).** A P0 headline negative should say what was actually tested. Here the "Ising component" was a no-op in most test retrains, and where it was not, it reproduced a 2-s brute-force enumeration. A reader of the P0 table would conclude that Ising-fitted schedules were tried and failed. Strictly, the test shows only that per-retrain day-1 table fitting does not help on low-load Region1, and it says nothing about Ising solving.

**Fix.**
1. **F59:** add "On the test, the fitted table was neutral (all multipliers 1.0, i.e. arm B) on 10 of 18 retrains, and PT's tables equal the exhaustive enumeration's on all 18 (raw `solves_test.csv`; not in the report)".
2. **F59's priority line:** "the pre-registered negative for per-retrain day-1 table fitting on Region1. As a test of Ising solving it is uninformative, because the table space is enumerable in ~2 s and the fit was mostly neutral."
3. **F57:** add the enumeration timing (`PROGRESS.md#L83`).
4. **§8 row 13 and the abstract's H5 bullet:** add "(table neutral on 10/18 test retrains; Ising = exhaustive optimum)".
5. **Optional.** Lower F59 to P1, since it no longer meets "decisive".

### 4. §8 row 19 rates the proposal's H2 "Partly supported" on dev, analytic evidence that does not separate Ising from LP and is not the proposal's metric
**What the story says** (L1966). "**Partly supported**: the SoS-surrogate SB beat the peak-aware greedy on dev (−13.217% at 10 s) … no Ising solver passed a pre-registered comparison", with the evidence tag OFFLINE.

**What the sources say.**
- **The proposal's H2** (`proposal.js:200`) has three parts:
  - the SoS surrogate is "a sufficient surrogate for the true min–max objective";
  - an Ising solver on it beats (a) the artifact's greedy peak policy and (b) a greedy warm start;
  - both by at least 3% **Peak DT**, the simulator's metric (H1 at `:199` defines Peak DT as what "the unmodified simulator … reports").
- **The −13.217% is not that metric, and it does not separate Ising from LP.**
  - It is the analytic F1 objective vs peak-aware greedy, on the two dev instances, from phase-1 tuning (`q2/RESULTS.md:132-143`; validator 1 N23 notes that the anchor is wrong).
  - The classical LP + round + repair gets −13.172% in the same table. SB beats it by 0.045 points, so the "≥ 3% over greedy" clause is met by every method, classical included.
- **In simulation, SB on the SoS surrogate is within noise of LP and below the 3% bar.** The only simulated SB-on-SoS selections are harness_eval C4: 27.97 (Region7) and 27.87 (Region6). That is level with LP + repair R1 (28.10 / 27.77; `harness_eval/RESULTS.md` §3.1 tables). The same dev instances' peak-aware greedy (F2b) simulated at 28.53 / 28.26 (`q2/PROGRESS.md:50`), so C4 is 2.0% / 1.4% below it. That is under the proposal's 3% bar, although the comparison crosses campaigns.
- **The "sufficient surrogate" clause** is contradicted by F21: SB on the SoS surrogate is the weakest Ising solver in phase-1 dev tuning and by the WP5 rule.
- **Part (a)** is not measured (F91).

**Why blocking (criterion 2).** This is "dev results ranked as headline evidence". The claims table is the story's verdict list, and it grants partial support to a proposal hypothesis on dev analytic data. That data is not the hypothesis's metric and is matched by classical LP.

**Fix.**
1. **Status:** "**Not supported**". Name the parts:
   - (a) not measured;
   - (b) the analytic ≥ 3% over greedy holds on dev for every solver, LP included (−13.17%), so it does not distinguish Ising; on the proposal's simulated Peak DT, SB-on-SoS (harness_eval C4) is level with LP + repair and ≈1.4–2.0% below the dev peak-aware greedy (cross-campaign);
   - the surrogate is the weakest Ising route (F21, scoped as validator 1 R2-B3 requires).
2. **Evidence tag:** DEV.
3. **Refs:** `q2/RESULTS.md#L132-L143`, `harness_eval/RESULTS.md` (C4 and R1 rows), `q2/PROGRESS.md#L50-L51`.

## Endorsed from validator 1 (they also fail a grill criterion; not counted again)
- **R2-B1 (honesty, criterion 3).** My G1 fix was generalised too far. The Q3 labels come from a PT started at Baleen's selection with a trust region toward Baleen's labels, and the Track C designs start from Baleen's set or the previous round. "Every deployed label set is LP-started" mis-describes the Q3 P0 negative's arm.
- **R2-B3 (honesty).** The unscoped "SB is the weakest Ising solver" in §8 rows 8 and 19. My item 4 is a different defect in row 19; fix both together.
- **R2-B4 (honesty).** The corrected count makes F70's record two-to-one *for* PT at retrain level on dev. Keep the instance-level framing as the headline, so that the correction does not read as a PT advantage.
- **N13.** F53's post-hoc decomposition sits under a TEST-PREREG tag.
- **N15.** On Region1 the α arms are worse than A at 2.7 instance SE. "Did not help" in the abstract understates it; F69's "null / worse" is right.
- **N18.** Superseded by my item 1.
- **N27, N28.** `G3_SIGNED` and `TIMING_IDLE` are untracked, so their links are dead on the public repo, and the link to `.git/objects` is not a file. `G3_SIGNED` is the only record of the go-file's waiver text: quote its one line in F76 (it contains no private data).

## Non-blocking suggestions
1. **P0 headline table: add the key number to every row, not only H4 and T2.** For example:
   - F20: PT 22.524 vs 22.569 at 10 s, but 22.508 vs 22.415 at 60 s;
   - F28: 22.7336 vs 22.7166;
   - F33: 2/6, −0.41 to −1.07;
   - F44: X1 40.53 vs A 39.27;
   - F59: 24.45 vs A 24.14, 1/6.
2. **F76 and F04: the later overlays had no review gate.** PATCH_v3 (the H5 test's overlay, `SCOPE_v2_1b.md`) and PATCH_v4/v5 (T1/T2) had neither a teammate nor a coordinator code review. They had only G1 and the functional equivalence checks (G1_v3: table ≡ power law; G1_v5: κ = 1e9 ≡ A+α).
   - F76's "`PATCH.diff` … unchanged through WP9 and WP10" is true, but WP10's test ran on `PATCH.diff` + 43/−1 lines. Say so.
3. **F65: disclose the T2 prerequisites.** The instance dumps and 60 label sets of the T2 pool were built 04:57–05:04, before the protocol commit at 05:19. The protocol discloses it (`t2u_region4/PROTOCOL.md#L23-L25`; LAB_NOTEBOOK 04:57). Add it for parity with F53's WP9 static replays.
4. **F70, union row.** The 10-instance PT-vs-CP-SAT dev confirmation was launched at 10:01, when the T2 FAILED result was committed (Appendix B), and is "report only". Say "run after the T2 outcome".
5. **Header: the story loop's own incidents.**
   - WRITER_NOTES records that the writer edited another agent's report (redacting one line of `validator_citation_round_1.md`) and briefly created `tools/__pycache__` outside its write area. Add one line to the header's "How it was produced", since the story is "the record of everything".
   - Appendix B could also note that `3_autoresearch/result/deterministic_validation.json` is modified in the working tree (its "no claim file yet" note was cleared), next to the uncommitted LOOP_STATUS.
6. **§8 summary, last bullet.** Add "(fresh = never run deployed; prior load-based attempts: [F95](#F95))", so that the paper sentence carries both qualifiers, as row 15 does.
7. **Appendix C.** Add:
   - `changes/3_autoresearch/work/union_t2/`: the T2 label sets and their overlay patches, the source of the 30/30 Region4 objective ties;
   - `changes/3_autoresearch/code/validate.py`;
   - `documents/OS Final Project Proposal.pdf`: the team's slide proposal, which frames the question as "adopting Ising Machine".
8. **F84 item 1.** Add the source's mitigation: "the worker transcript confirms each rule precedes its simulations" (FINAL_REPORT §5.1).
9. **F100's "how much it matters".** Name Track C's anchored-energy comparison as the one non-optimal 10-s comparison run next to the ~15-CPU foreign job. F70 reports its objective gap (13.55 vs 14.31) as a solver difference.

## Assessment against the five grill criteria
| Criterion | Verdict | Blocking items |
|---|---|---|
| 1. Completeness | Every ledger hypothesis has a finding, and the round-1 gaps (prior art, PLAN gate, label-solver record, secondaries) are filled. Missing: the neutral H5 fits and the Track C gap | 1, 3 |
| 2. Priorities | The P0 set is right, and no DEV finding is P0. Two ratings are inflated: H5 as "decisive", and the proposal's H2 as "Partly supported" on dev analytic data | 3, 4 |
| 3. Honesty | The solver ties are plain, H4's caveats are up front, and the threshold's region status is exact. Wrong: a forking path is mis-stated next to the headline Q1, the H5 framing, the proposal-H2 row, and the LP-start overreach (endorsed) | 2, 3, 4 |
| 4. Integrity disclosures | Present: the 3_autoresearch timing items, the G3 waiver, the privacy redaction (including the current tree) and the skipped permissions. The H3′/Track C firewall is misstated | 1, 2 |
| 5. Usability | Index, P0 table, claims table, timeline and file map are all present. All 1,108 links resolve and all line ranges are in range. Remaining: untracked targets (endorsed) and missing key numbers in the P0 table | — |

OPEN_FINDINGS=4
VALIDATOR_STATUS=FAIL
