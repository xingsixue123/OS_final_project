# Validator 2 (grill: completeness, priorities, honesty), round 3 of 5

**Target:** `changes/4_story/STORY.md`, story-writer round 3 (run 20261020_154140, 104 findings).
**Run:** 2026-10-20. Read-only. This report is the only file written in the repo; my recomputation scripts live outside it.

## Method
1. **What I read.**
   - The whole round-3 story, `RESEARCH.md`, and `changes/4_story/result/WRITER_NOTES.md` (round 3).
   - My round-2 report, and validator 1's round-3 report (`validator_citation_round_3.md`), so as not to duplicate it.
2. **Round-2 fixes.** I re-checked my four round-2 blocking items, the items I endorsed, and my non-blocking items 1–9 against the new text.
3. **Uncited-source sweep.** I listed every tracked `RESULTS*.md`, `PROTOCOL*.md`, `PROGRESS.md`, `G1*.md`, `CP1.md` and `changes/3_autoresearch/result/*` file. Each is cited by the story at least once, except `changes/3_autoresearch/result/deterministic_validation.json` (non-blocking item 5).
   - I also read the tracked but uncited evidence files that could hold results or incidents: the six `integrity.txt` files (WP0, WP3, WP9, WP10, T1, T2), `wp5_ising/results/label_evidence.md` and `wp2_deployed/results/attribution.txt`.
   - The integrity files agree with F77 and F81. The other two are covered by F32 and F39, except for their arm-B rows (blocking item 1).
4. **Keyword sweep** (incident, kill, bug, deviation, race, outside, by hand …) over the WP0, WP1, WP3, WP9 and WP10 progress logs. Every hit maps to an existing finding.
5. **Recomputation** from the raw ledgers (matched rows only; the story's conventions):
   - arm B − arm A on the four test ledgers (WP3, WP9, WP10 and T2) and the per-retrain T2 values;
   - PT vs CP-SAT day-1 F1 objectives on the 36 H3′ test label pairs (`wp3_test/labels/*.json`, `label_peak_util`).
6. **Ledger-hypothesis check.** Every ledger hypothesis still has a finding:
   - R: F07, F08, F98;
   - Q1: F18; Q2: F20; Q3: F33;
   - H1′: F25; H2′: F28; S: F31;
   - H3′: F44, F45; H4: F52, F53; H5: F59;
   - the loop: F61–F67.

**Own error corrected here.** My round-2 fix text for F73 said "Track C ran only 10-05 14:18–~15:05". That time comes from Track C's progress log, but its own ledgers keep writing until 15:25:55 (validator 1, R3-B3, endorsed below). The writer copied my wording, so the correction overrides it.

## Round-2 blocking items: status
| Item | Status |
|---|---|
| 1. H3′/Track C firewall | **Fixed:** F73, F44, F50 and Appendix B. One time is wrong, and it came from my own fix text (R3-B3, endorsed). |
| 2. F96 and the Q1 forking path | **Fixed:** title, bullet, priority line and the F18 pointer. 6.0–7.3 points re-checked (34.52 − 28.53 = 5.99 … 35.56 − 28.24 = 7.32). |
| 3. H5 neutral tables, Ising = enumeration | **Fixed:** F59 (body, P0 title, priority line), F57, §8 row 13 and the abstract. F59 stays P0; see non-blocking item 3. |
| 4. §8 row 19 (proposal H2) | **Fixed:** now "Not supported / DEV", with parts (a) and (b) named. 1.38–1.96% re-checked. |

**Endorsed in round 2:**
- R2-B1: fixed; the refs are still missing (R3-B2).
- R2-B3 and R2-B4: fixed.
- N13: fixed in F53, not in F52 (validator 1, N24).
- N15: fixed.
- N27/N28: fixed through `untracked_evidence.txt`.

**My round-2 non-blocking items:**
- 2–9 are done.
- Item 1 is partly done: the P0 rows for F18 and F52 still carry no key number (non-blocking item 1).

## Blocking issues

### 1. The standalone deployed effect of the scope-v2 `load` feature (arm B vs A) is missing, though it is null or harmful on every test pool and the T2 report flags a large harm
**Why it matters.** Scope v2 exists to add one causal `load` feature to Baleen's model (F03). Arm B (Baleen's labels + `load`) is a pass-rule reference in every phase-2 test. Its result against A is therefore the direct test-level answer to "does the new feature help Baleen?", and PLAN named it as a risk in advance: "The `load` feature helps Baleen as much as it helps us (arm B ≈ D)" (`changes/2_deployable_peak/PLAN.md#L111`).

**What the story says.**
- B's means appear only as table cells: F44, F52, F59 and F65, plus A.7, A.9, A.10 and A.11.
- No finding, §8 row or summary line states what B did against A.
- F38 gives only the dev main effect (+0.06).
- F03's priority line reads "it defines the only new signal, which became the source of the one deployed win" (STORY L271). Read alone, that credits the feature. The win (A+α) uses `load_10m` only to scale the threshold of a model trained *without* the feature.

**What the ledgers show** (recomputed; B − A, positive = B worse):

| Pool | A | B | B − A | B worse on | Note |
|---|---|---|---|---|---|
| WP2 dev, 8 inst. | 38.50 | 38.44 | −0.06 | — | F38 |
| H3′ test (Regions 6/7) | 39.27 | 39.17 | −0.09 (inst SE 0.16) | 2/6 | |
| H4 test (Region5) | 36.17 | 36.37 | +0.19 (0.23) | 3/6 | |
| H5 test (Region1) | 24.14 | 24.54 | +0.40 (0.17, ≈2.4 SE) | 5/6 | |
| T2 test (Region4) | 50.72 | 56.71 | **+5.99** (4.38) | 3/5 | s0.5 **+22.39**: B 55.31 / 55.12 / 55.31 on all three retrains vs A 32.85; s0.4 one B retrain collapsed (73.03) |
| T1 (Region2, descriptive) | 10.255 | 10.201 | −0.05 | — | F64 |

**Sources:**
- `changes/2_deployable_peak/wp3_test/trials.csv`, `changes/2_deployable_peak/wp9_region5/trials.csv`, `changes/2_deployable_peak/wp10_schedule/trials_test.csv` and `changes/3_autoresearch/work/t2u_region4/trials_test.csv` (arms `A` and `B`, design `baleen`);
- the T2 source's own sentence, "B's models are poor on Region4" (`changes/3_autoresearch/work/t2u_region4/RESULTS_test.md#L36`);
- the learnability gate already showed that Baleen's labels gain nothing from `load` (0.001 ± 0.001, F37).

**Why blocking (criteria 1 and 3).**
- This is the only scope-v2 component besides α, and it was compared on every test pool. Its result is never stated, and one test shows a 12% regression (a 68% one on one instance) that the source reports.
- A reader who stops at F03's priority line, or at the abstract's "the scope-v2 load-adaptive admission threshold", can come away thinking the scope-v2 feature was vindicated. In fact only the threshold use of the signal helped.

**Fix.**
1. **New finding** (P1, TEST-POSTHOC; the next free ID, F105): "The causal `load` feature on Baleen's own labels (arm B) never improved Baleen in a deployed test, and on Region4 it badly hurt". Give the table above, cite the four ledgers, `t2u_region4/RESULTS_test.md#L36`, `PLAN.md#L111` and F37/F38. State that no B-vs-A pass rule existed (B was a reference arm), so the finding is post hoc.
2. **§8, new row:** "Adding the causal `load` feature to Baleen's model improves deployed Baleen (arm B vs A)". Status: **Not supported** (post hoc; −0.09 to +5.99 across the four test pools; dev −0.06).
3. **F03 priority line:** "it defines the `load` signal. As a model feature (arm B) it never helped on test (F105); the one deployed win uses it only to scale the admission threshold (A+α)."
4. **Optional, one sentence in F52 or F53.** On WP2 dev, α did nothing on B's models (B − B+α = +0.016 ± 0.386, 5/8; `changes/2_deployable_peak/wp2_deployed/results/attribution.txt#L17`). H4's secondary arm B+α (6/6 on Region5) therefore rests on the H3′ post-hoc result (F47), not on dev.

### 2. The headline solver summaries leave out that classical solvers beat the Ising sampler on the day-1 label instances, the instances that produced every deployed label set
**What the story says.**
- **Abstract (L21–24):** "The Ising samplers won only at one short budget per test: 10 s in Q2, 3 s in H2′. They lost at 1 s, at 60/300 s and in rolling re-solves. They tie exactly where both families reach the optimum."
- **§8 row 7 (L2004)** and **§8 summary bullet 2 (L2024)** say the same: wins "at one short budget per test (10 s; 3 s)", losses at 1 s, 60/300 s and rolling.

**What the sources show.** Every deployed Ising label set (WP2, WP3, WP9, the union) is a 10-s PT solve of the *day-1 label instance*. On those instances the Ising samplers were never the best family:
- **WP5 dev, 8 day-1 instances, nested objective:**
  - LS is best at 1 s (22.666) and 3 s (22.336); CP-SAT is best at 10 s (22.258), with PT last (22.607);
  - source: `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md#L220-L235`; F32 shows only the 10-s rows, and F70 mentions only 10 s.
- **H3′ test labels (single level f = 1, the deployed PT configuration):**
  - CP-SAT's F1 day-1 objective is lower than PT's on **36/36** seed-matched pairs, by 0.04–0.20 util points; the means are 20.965 vs 21.057;
  - recomputed from `changes/2_deployable_peak/wp3_test/labels/*.json` (`label_peak_util`); validator 1 found the same (S10).
- **Dev Region5_s0 (auto-research):** CP-SAT is lower on 2 of 3 seeds (`changes/3_autoresearch/result/FINAL_REPORT.md#L78`).
- **Exact ties** hold only on the auto-research test pools and Region1_s0.

So the "10 s in Q2" win holds on the full-trace offline instances only. At the same 10-s budget, on the instances whose solutions were actually deployed, classical solvers matched or beat PT, and on the H3′ test they beat it on every solve.

**Why blocking (criterion 3).**
- The abstract and the claims-table summary are where a reader learns what Ising contributed.
- Listing only the Ising wins and the classical wins *elsewhere* hides the one solver comparison tied to the deployed pipeline. That comparison goes against Ising.
- Together with the over-general "for the F1 rows the objectives tie" in F70 (validator 1, R3-B1), the story currently overstates solver parity exactly where it matters for H3′.
- R3-B1 fixes F70, F100, F32 and §8 row 23. This item covers the headline summaries, which R3-B1 does not touch.

**Fix.**
1. **Abstract, second bullet:** "They lost at 1 s, at 60/300 s, in rolling re-solves, and on the day-1 label instances that produce the deployed labels: classical LS/CP-SAT were best at every budget on WP5 dev ([F32](#F32)), and CP-SAT's objective was lower than PT's on all 36 H3′ test label solves (10 s, shared cores, [F70](#F70), [F100](#F100))."
2. **§8 row 7:** add "On the day-1 label instances the classical solvers were best at every budget (WP5 dev) and on 36/36 H3′ test solves", plus refs.
3. **§8 summary bullet 2:** append "…and on the label-size instances used for deployment".
4. **F32:** add the 1-s and 3-s rows of the cited day-1 table, or say "LS best at 1 and 3 s, CP-SAT at 10 s".

## Endorsed from validator 1 (they also fail a grill criterion; not counted again)
- **R3-B1 (criterion 3, solver ties).** The F70 tie/stability sentence is wrong for the H3′ test labels and for WP2 dev. Blocking item 2 is the headline-level counterpart; fix them together.
- **R3-B3 (criterion 4, firewall timing).** Track C ran to ~15:26 on 10-05, not ~15:05. The error came from my round-2 fix text.
- **R3-B4 (criteria 3 and 4).** F100's "main non-optimal comparison" and "no objective comparison recorded for WP3" are false, because the WP3 label JSONs record the objectives.
- **R3-B5 (criterion 1).** F103's "never implemented" is false for C3/C3L and for "samples 1–9".
- **N24 (criterion 2).** The P0 table and F52's title present the 69% share, a post-hoc decomposition, under TEST-PREREG without a marker.
- **N37 (criterion 3).** §8 row 23's "The F1 objectives tie where compared".

## Non-blocking suggestions
1. **P0 headline table:** add the key number to the two rows still without one.
   - F18: 27.06 vs 32.28 (−5.21), 6/6.
   - F52: 35.02 vs A 36.17, +1.16, 5/6.
2. **F66 / F69: say what Region4's "−15%" is measured against.**
   - On Region4, Baleen's model was no better than the static RejectX baseline on the two instances that carry the gain: s0.2 A 59.07 vs RejectX 58.31, and s0.3 A 76.14 vs RejectX 77.09.
   - Those two give 36.67 of the 39.24 summed A − A+α gain (93%).
   - So the post-hoc Region4 "replication" is mostly the threshold rescuing a Baleen failure. Add one sentence to F66, and soften F69's "strongest (post-hoc) support".
   - Source: `changes/3_autoresearch/work/t2u_region4/RESULTS_test.md`, per-instance table (STORY A.11).
3. **F59 is still P0, but its priority line now calls it "uninformative" as a test of Ising solving.**
   - Either move it to P1, or let the P0-table row say what it decides: "refutes per-retrain day-1 table fitting on Region1".
   - As it stands, the P0 table lists it among the headline Ising negatives.
4. **F73 table: add each test's start time, not only its end.**
   - The H4 row gives only "to 2026-10-17 05:31". Validator 1's earliest starts (`ts − wall_secs`) are H4 21:30:16 (5 s after `c8f655a`) and H5 19:23:09 (5 s after `2738cba`). Printing them makes the title auditable at a glance.
   - Note in the H4 row that the static RejectX/CoinFlip replays of the test instances (20:29–21:00) preceded the protocol commit (F53). Add a matching Appendix B row.
5. **Appendix B: the auto-research validation file was re-run after the loop ended** (my round-2 item 5b, still open in the story).
   - `changes/3_autoresearch/result/deterministic_validation.json` was modified in the working tree at 15:34, after STOP_EXHAUSTED (11:26) and 7 minutes before this story loop started. The re-run dropped the committed note "no claim file yet".
   - WRITER_NOTES records this; the story, which is the record, does not. Add it to the 10-20 10:01–11:26 row, next to the uncommitted LOOP_STATUS.
6. **F104 and the abstract: the proposal itself coupled the threshold to the Ising-label system.** Proposal §4.1 says "causal load features added so that the online policy can modulate its threshold with observed load" (`documents/proposal_docx_compose/proposal.js#L245`).
   - "A non-Ising control" is correct for A+α.
   - "The idea predates the Ising work" is also true: the audit is dated 09-14, the proposal 09-26.
   - Add the audit → proposal → SCOPE_v2 chain in one line. This supports validator 1's N3/N5.
7. **§8 status words.** Row 16 ("…and on other regions") says "yes on Regions 6/7 and Region4 (Region4 also concentrated)". After suggestion 2, add "(Region4: Baleen ≈ RejectX on the two carrying instances)", so that the claims table carries the caveat as row 15 does for Region5.

## Assessment against the five grill criteria
| Criterion | Verdict | Blocking items |
|---|---|---|
| 1. Completeness | Every ledger hypothesis has a finding, every source file class is cited, and the incident sweep finds nothing new. Missing: the standalone test-level result of the scope-v2 `load` feature (arm B), including the large Region4 harm the source reports. F103's overstatement is endorsed (R3-B5) | 1 |
| 2. Priorities | The P0 set is right and no DEV finding is P0. The decisive negatives (Q2, H2′, Q3, H3′, H5, T2) are P0 and Track C is P1, all visible. Minor: F59's P0 rank versus its own "uninformative" line (non-blocking item 3); the post-hoc 69% under TEST-PREREG (N24, endorsed) | — |
| 3. Honesty | No reader can conclude that Ising succeeded in deployment, and the threshold's status (pre-registered on Region5; post hoc on Regions 6/7 and Region4; worse on Region1; descriptive on Region2) is stated exactly. Solver parity is overstated: the headline summaries omit the label-instance losses (item 2), and F70's tie claim is too broad (R3-B1, endorsed) | 1, 2 |
| 4. Integrity disclosures | Present: the 3_autoresearch timing items (F84, F63, F65, F86), the G3 waiver with the go-file text (F74, F76), the privacy redaction including the current tree (F87), the skipped permissions (F61, header) and the story loop's own incidents. Remaining: one Track C time (R3-B3, endorsed) and the post-loop validation re-run (non-blocking item 5) | — |
| 5. Usability | Index, P0 table, claims table, timeline, file map and recomputation appendix are all present, and links resolve (validator 1: 0 checker problems). Two P0 rows lack key numbers (non-blocking item 1) | — |

```
OPEN_FINDINGS=2
VALIDATOR_STATUS=FAIL
```
