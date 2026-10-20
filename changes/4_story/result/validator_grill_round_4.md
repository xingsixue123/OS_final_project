# Validator 2 (grill: completeness, priorities, honesty), round 4 of 5

**Target:** `changes/4_story/STORY.md`, story-writer round 4 (run 20261020_154140, 105 findings, uncommitted working tree).
**Run:** 2026-10-20. Read-only. This report is the only file written in the repo. My recomputation scripts live outside it.

## Method
1. **What I read.**
   - The whole round-4 story.
   - `RESEARCH.md` and `changes/4_story/result/WRITER_NOTES.md` (round 4).
   - My round-3 report, and validator 1's round-4 report (`validator_citation_round_4.md`), so as not to duplicate it.
2. **Round-3 fixes.** I re-checked my two round-3 blocking items, the round-3 items I endorsed, and my non-blocking items 1–7 against the new text.
3. **Source sweep.** Every tracked `RESULTS*.md`, `PROTOCOL*.md`, `PROGRESS.md`, `G1*.md` and `CP1.md` file, `RESEARCH.md`, and every file in `changes/3_autoresearch/result/` (including `STOP_EXHAUSTED`) is cited by the story at least once (scripted check: no uncited file).
   - I also re-read FINAL_REPORT §4–§6 and the LAB_NOTEBOOK headings after 07:00.
   - I checked the git history of FINAL_REPORT after the T2 outcome: `b0d6e2b` 10:03, `4fe0688` 11:26:33 and `e964491` 11:26:53. The round-2 validators committed at 11:44, after all three, so they reviewed the final text.
   - The WP9 evaluation was mechanical: `evaluation.json` was written 7 s after the last ledger row (10-17 05:31). So the 2.5-day gap before the result commit (`cad1603`, 10-19 16:14) is not an evaluation gap.
4. **Story-loop integrity.** Outside `changes/4_story/`, the only path modified since the loop started (15:41) is the `tools/` directory, with mtime 17:09:09. That is the round-2 bytecode-cache incident the header discloses; `tools/` now holds only `privacy_scrub.py`. `python3 -B tools/privacy_scrub.py --check` is clean.
5. **Recomputation from the raw ledgers** (matched rows; the story's conventions, which reproduce the story's A+α vs A values on H4 and T2 exactly):
   - B+α vs A+α, A+α vs A and B+α vs B on the four test ledgers (WP3, WP9, WP10, T2);
   - the Region5 per-instance A − B+α and B − B+α;
   - H1′ with and without the six instances reused from phase-1 Q1 (`wp1_offline/trials.csv`, phase `wp1_reused_phase1_heldout`);
   - X1 vs A and vs A+α with the one catastrophic instance removed (H3′, H4).
6. **Ledger-hypothesis check.** Every ledger hypothesis still has a finding:
   - R: F07, F08, F98;
   - Q1: F18; Q2: F20; Q3: F33;
   - H1′: F25; H2′: F28; S: F31;
   - H3′: F44, F45; H4: F52, F53; H5: F59;
   - the loop: F61–F67.

## Round-3 blocking items: status
| Item | Status |
|---|---|
| 1. Arm B (the `load` feature) vs A | **Fixed** for the no-threshold half: F105, §8 row 24, F03's priority line, the abstract, the §8 summary, and F53's dev note. The with-threshold half is missing, and the new summary wording overreaches (blocking item 1 below). |
| 2. Day-1 label-instance solver losses in the headlines | **Fixed:** abstract, §8 row 7, §8 summary bullet 2, F32 (1/3/10 s table). Validator 1's R4-N1 and R4-N4 are wording only. |

- **Endorsed in round 3:** R3-B1, R3-B3, R3-B4 and R3-B5 are fixed (validator 1 confirms). N24 is fixed (F52's title marks the 69% as post hoc). N37 is fixed.
- **My round-3 non-blocking items:** 1, 3, 4, 5, 6 and 7 are done. Item 2 is done in F66's body, F69 and §8 row 16, but F66's *title* is unchanged (non-blocking item 2).

## Blocking issues

### 1. The `load` feature's record under the threshold (B+α vs A+α) is missing, so "never helped beyond noise" is half a record. B+α's Region5 gain (−4.7%) is given without the concentration caveat the story applies to A+α.
**What the story says.**
- **Abstract L34:** "The scope-v2 `load` *feature* itself never helped beyond noise as a model input (arm B vs A; …)".
- **§8 summary, last bullet (L2066), unscoped:** "the `load` signal as a model feature never helped beyond noise ([F105](#F105)). It passed on the retrain-level SE, but at instance level it is ≈1.5 SE …".
- **F105** calls itself "the direct test-level answer to 'does the scope-v2 feature help Baleen?'", but it compares only B with A. Its one with-threshold statement is WP2 dev B − B+α.
- **F52 (P0)** reports "Secondary arm B+α: 34.48; 6/6 vs A (+1.70) and 6/6 vs B (+1.89); −4.7%". "Read this first" caveats only A+α. F53 gives B+α's instance SEs but not its concentration.
- **§9 item 4** repeats the source's "why B+α is more uniform than A+α on Region5". §9 item 2 recommends B+α for the final confirmation.

**What the ledgers show.** These are recomputed from `changes/2_deployable_peak/wp3_test/trials.csv`, `changes/2_deployable_peak/wp9_region5/trials.csv`, `changes/2_deployable_peak/wp10_schedule/trials_test.csv` and `changes/3_autoresearch/work/t2u_region4/trials_test.csv`, using arms `Aa-1.0` and `Ba-1.0`. The dev row comes from STORY A.6. Positive means B+α is better.

| Pool | A+α | B+α | B+α − A+α gain | B+α better on | SE_inst (ratio) | SE_retrain (ratio) |
|---|---|---|---|---|---|---|
| WP2 dev (A.6) | 37.88 | 38.43 | −0.55 | — | — | — |
| H3′ (Regions 6/7) | 38.302 | 38.380 | −0.078 | 1/6 | 0.247 (0.3) | 0.272 (0.3) |
| H4 (Region5) | 35.020 | 34.479 | **+0.541** | 4/6 | 0.492 (1.1) | 0.216 (**2.5**) |
| H5 (Region1) | 24.624 | 24.476 | **+0.148** | 4/6 | 0.119 (1.2) | 0.060 (**2.5**) |
| T2 (Region4) | 42.870 | 43.865 | **−0.995** | 1/5 | 0.464 (**2.1**) | 0.546 (1.8) |
| T1 (Region2, descriptive) | 10.188 | 10.135 | +0.053 | — | — | — |

- **Two standards in one bullet.** H4 = YES rests on the retrain-level SE (F52: "passes on the retrain-level SE"). By that same standard, the feature improved the threshold arm beyond 2 SE on H4 and on H5. By the instance-level standard that the same bullet uses to qualify H4, it never helped, and it hurt on T2 (2.1 instance SE).
- **The honest summary is a two-way, noise-level record under the threshold.** "Never helped beyond noise" is true only of B vs A, or at instance level.
- **B+α's −4.7% on Region5 is more concentrated than A+α's.** A − B+α per instance is +0.373, +0.404, +0.435, +0.439, **+7.656 (s0.5)** and +0.869. s0.5 gives 75% of the 10.175 summed gain, and the other five average +0.504 (≈1.4% of A's 36.17).
  - Against B, s0.5 gives 8.849 of 11.321 (78%).
  - "More uniform (6/6)" (source `wp9_region5/RESULTS_test.md#L17`) is true of the sign only. In magnitude B+α is *less* uniform than A+α (69%).

**Why blocking (criteria 1–3).**
- F105 was added to answer the feature question, and it omits the half of the comparison that includes the project's best pre-registered deployed number (B+α, 6/6, −4.7%).
- The §8 "Summary for a paper" makes a statistical claim, "never beyond noise". The story's own retrain-level convention, the one that makes H4 "YES" in the same bullet, contradicts it on two test pools.
- Round 1 made the A+α concentration blocking (G2) because a P0 finding showed a gain larger and more uniform than the evidence. The P0 finding F52 now does the same for B+α, and §9 calls it "more uniform".

**Fix.**
1. **F105.**
   - Add a second table, "With the threshold: B+α vs A+α", with the rows above (both SE levels). Add the computation to `recompute.py`'s round-5 additions.
   - Retitle F105 to: "The causal `load` feature as a model input: without the threshold (B vs A) it never improved Baleen beyond noise and badly hurt on Region4; with the threshold (B+α vs A+α) the record is two-way: better on H4 and H5 at ≈2.5 retrain SE (≈1.1–1.2 instance SE), worse on T2 (2.1 instance SE) and on WP2 dev".
   - Update the priority line to match.
2. **Abstract L34 and F03's priority line.** Keep "(arm B vs A)" and add "with the threshold its effect is two-way and noise-level at instance level ([F105](#F105))".
3. **§8 summary, last bullet.** Replace "the `load` signal as a model feature never helped beyond noise" with "as a model input the `load` feature did not help Baleen alone (B vs A) and is two-way under the threshold (B+α vs A+α; [F105](#F105))".
4. **§8 row 24.** Add the B+α vs A+α range: −1.00 to +0.54, with H4 and H5 at ≈2.5 retrain SE and T2 at −2.1 instance SE.
5. **F52.** Add one bullet to "Read this first" and the same clause to F53: "B+α (−4.7%, 6/6) is more concentrated: s0.5 gives 75% of its summed gain vs A (7.66 of 10.18; 78% vs B), and the other five average +0.50 (≈1.4%) (post hoc)".
6. **§9 item 4.** Write "why B+α is more uniform than A+α in sign (6/6) though more concentrated in magnitude (75% on s0.5)". In §9 item 2, keep B+α, but note that the concentration rule in the margin bullet applies to it too.

## Endorsed from validator 1 (they also fail a grill criterion; not counted again)
- **R4-B1 (criterion 3, solver ties).** F100 says "the two non-optimal 10 s comparisons with deployed rows" are WP3's and Track C's. But the union dev rows in F70 rest on non-tied, partly shared-core label solves (Region5_s0: 0.16–0.31%) and on WP2's near-tie labels.
  - Those rows are the union XA row, PT-favouring at 2.1 retrain SE, and the XG row at 2.0 instance SE.
  - F70's "Reading" then explains the PT-favouring evidence by co-optimal sets only for the test pools, and is silent on these dev rows.
  - Fix F100 as validator 1 asks, and add to F70's union rows: "objectives not tied on Region5_s0; DEV8 labels are WP2's near-ties".
- **R4-N5 (criteria 1 and 4).** H1′'s six reused phase-1 instances: see non-blocking item 1 for the numbers that close it.
- **R4-N11 (criterion 4).** WP9 built its dumps and X1's 36 label sets before the protocol commit, alongside the static replays. Add this to the F73 H4 row, as F65 already does for T2.
- **R4-N13 (criterion 4).** F74's title says each deployed test's evaluator was "validated on earlier data". No such validation is recorded for the auto-research `eval_test.py` (T1 or T2).
  - The protocols only assert that it is "identical to `code/validate.py`" (`t2u_region4/PROTOCOL.md#L45`, `t1u_region2/PROTOCOL.md#L57`).
  - The story's own F84 item 5 records a known defect in both: static P100 is averaged regardless of `matched`.
  - Scope F74's title to WP3/WP9/WP10, and say that the T1/T2 evaluator was asserted identical but not validated and had that defect. No verdict depends on it: T1 was closed before `evaluation.json` was read, and T2 failed.

## Non-blocking suggestions
1. **H1′ and the six reused Q1 instances (F25, legend caveat 2, F73's title).**
   - The H1′ bar (≥ 80% wins, mean ≥ 10%; `PLAN.md#L19`, `27fb6f0` 09-29 15:06) was committed after Q1's −16% on the six Region6/7 s0.1–0.3 instances was known. Those same six instances are inside H1′'s 39 (18 reused rows, 09-28 18:54 → 09-29 01:05).
   - **Recomputed from `wp1_table.csv`:**
     - without them, LP 30/33 (12.54%), CP-SAT 30/33 (12.53%), PT 31/33 (13.18%), so H1′ still passes;
     - the six alone give 6/6 and 15.7–16.6%.
   - Add this to F25 and to legend caveat 2. Change F73's title to "…before its test ran (H1′: 6 of 39 instances reuse solves that predate PLAN; [F25](#F25))", since the title is currently contradicted by its own first row.
2. **F66's title** still reads "Region4 replicates the H4 effect post hoc: A+α is 15% below Baleen". Its own body says the replication is "mostly the threshold rescuing a Baleen failure" (93.5% from two instances where Baleen ≈ RejectX). Suggested title: "Region4 (post hoc): A+α beats Baleen on 5/5 instances; the 15% mean is 93.5% from two instances where Baleen was level with RejectX". The index row inherits the title.
3. **F31 and §8 row 8 (scaling, "the one reported Ising contribution that stands").**
   - The scaling run (`wp5_ising/RESULTS_dev.md#L333-L392`) has three arms: matrix-free SB, the dense SB package and PT. It has no classical solver, and it measures cost per step, not solution quality on the unions.
   - On the synthetic audit, LP + round + repair handled 200k variables in ≤ 1.7 s ([F11](#F11)). LP and CP-SAT also solved every real full-trace instance in WP1.
   - Add one line so that "scales where the dense SB package does not" is not read as a scaling advantage of Ising over classical solvers.
4. **Apply the concentration lens to the Ising negatives too (F45, §8 row 12).**
   - H3′-labels' −2.23 (instance SE 2.66, ≈0.8 SE) rests on Region7 s0.5. Without it, X1 beats A on 5/5 (+1.13) and A+α by +0.39 (3/5) (recomputed; F46's means agree).
   - On Region5, X1 trails A+α even without s0.5: −0.99, 2/5, driven by s0.6.
   - The pre-registered verdict stands. One sentence in F45 keeps the story's caveats symmetric between the positive and the negative results.
5. **Region1 status wording.** F69's title says "null on Region1", while F60, F69's own table ("null / worse") and the abstract say "worse" (A+α −0.487, ≈2.7 instance SE, ≈7.9 retrain SE; a reported comparison with no pass rule). Use one word everywhere, e.g. "worse (post hoc, no pass rule)".
6. **§8 row 7's status.** The 10 s (Q2) and 3 s (H2′) results are per-budget outcomes of pre-registered tests, not post-hoc observations. "Post-hoc" fits only the day-1 label-instance and rolling parts. Consider "Partly supported (per-budget results of Q2/H2′; neither test passed)" (see also validator 1's R4-N14 on the Evidence column).
7. **Appendix C.** `documents/prompt.txt` (tracked) is the captain's original prompt to the paper-selection pipeline behind F06. It is the only tracked file under `documents/` that the file map omits. Add it to the "Proposal, spec, paper, paper selection" row.
8. **Privacy reminder for the next round.** This report and validator 1's round-4 report contain no absolute paths, and the privacy check is clean on tracked files. The untracked round-4 reports will be checked only after they are committed.

## Assessment against the five grill criteria
| Criterion | Verdict | Blocking items |
|---|---|---|
| 1. Completeness | Every ledger hypothesis has a finding, every required source file is cited, and no incident in the sources is missing. Missing: the `load` feature's effect under the threshold (B+α vs A+α), which includes the project's best pre-registered deployed number. Minor: H1′'s reused instances (non-blocking item 1) | 1 |
| 2. Priorities | The P0 set is right. The decisive negatives (Q2, H2′, Q3, H3′, H5, T2) are P0, Track C and T1 are P1, and no DEV result is P0. Inflated: B+α's −4.7% inside the P0 finding F52, without its concentration (blocking item 1). F66's title (non-blocking item 2) | 1 |
| 3. Honesty | No reader can conclude that Ising succeeded in deployment. The solver ties are stated plainly, apart from the union dev rows (R4-B1, endorsed). The threshold's status is stated as the evidence allows: pre-registered YES on Region5 on the retrain SE (≈1.5 instance SE, 69% one instance); post hoc on Regions 6/7 and Region4 (Region4 mostly a Baleen failure); worse on Region1 without a pass rule; descriptive on Region2. The §8 summary judges the threshold and the feature by different SE standards (blocking item 1) | 1 |
| 4. Integrity disclosures | Present: the auto-research timing items (F84, F63, F65, F86, Appendix B 15:34), the G3 waiver with its go-file text (F74, F76), the privacy redaction including the current tree (F87), the skipped permissions (F61, header), the Track C firewall timing (F73) and the story loop's own incidents (header; file times re-checked). Endorsed refinements: R4-N11 and R4-N13 | — |
| 5. Usability | Index, P0 headline table, claims table (24 rows), timeline, file map and recomputation appendix are present. Every ref is a link, and validator 1's checker reports 0 problems. One tracked document is missing from the file map (non-blocking item 7) | — |

```
OPEN_FINDINGS=1
VALIDATOR_STATUS=FAIL
```
