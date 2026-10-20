# Validator 2 (grill: completeness, priorities, honesty), round 5 of 5

**Target:** `changes/4_story/STORY.md`, story-writer round 5, final (run 20261020_154140, 105 findings, uncommitted working tree).
**Run:** 2026-10-20. Read-only. This report is the only file written in the repo. My recomputation scripts live outside it.

## Method
1. **What I read.**
   - The whole round-5 story.
   - `RESEARCH.md` and the round-5 section of `changes/4_story/result/WRITER_NOTES.md`.
   - My round-4 report, and validator 1's round-5 report (`validator_citation_round_5.md`), so as not to duplicate it.
   - Sources re-read this round:
     - `wp9_region5/PROTOCOL_v2_H4.md` §1 and §5, and `wp9_region5/RESULTS_test.md` §0;
     - `wp3_test/PROGRESS.md`;
     - `3_autoresearch/result/FINAL_REPORT.md` §5–§7;
     - two result tables the story does not cite: `wp5_ising/results/label_evidence.md` and `wp10_schedule/results/proxy_validation_e1.md`.
2. **Round-4 fixes.** I re-checked my round-4 blocking item, the items I endorsed, and my non-blocking items 1–8 against the new text.
3. **Source sweep.**
   - A scripted check finds every tracked `RESULTS*.md`, `PROTOCOL*.md`, `PROGRESS.md`, `G1*.md`, `CP1.md`, `RESEARCH.md`, and every file in `changes/3_autoresearch/result/`, cited at least once. No file is uncited.
   - The tracked `.md` files the story does not cite fall into three groups:
     - secondary result tables, such as the two above and `q3/results/q3eval_heldout.md`;
     - the literature review's research notes;
     - the paper-selection pipeline's per-paper audits.
   - The two tables I read contain nothing that contradicts the story or is missing from it.
   - FINAL_REPORT §5 items 1–11 all appear (F84 items 1–11, F82, F86).
4. **Story-loop integrity.**
   - Outside `changes/4_story/`, nothing in the work tree is newer than the loop start (15:41), except the `tools/` directory mtime 17:09:09. That is the disclosed round-2 bytecode cache; `tools/` holds only `privacy_scrub.py`.
   - Two uncommitted changes sit under `changes/3_autoresearch/result/`: `LOOP_STATUS.txt` (11:44) and `deterministic_validation.json` (15:34). Both predate the loop, and Appendix B discloses them.
   - `python3 -B tools/privacy_scrub.py --check` is clean. That check covers tracked files only.
   - I also ran the tool's own `scrub_text` on three untracked files: `STORY.md`, `WRITER_NOTES.md` and `validator_citation_round_5.md`. I used `-B`, so no cache was written. All three came back unchanged.
   - `check_story.py` reports 0 problems over 105 findings.
5. **Recomputation from the raw ledgers** (matched rows; the story's conventions):
   - **Comparisons:** B+α vs A+α, A vs B+α and A vs A+α, per instance and at both SE levels, on H3′, H4, H5, T2 and T1 (s0.3–0.6).
   - **Story values:** every cell of F105's "with the threshold" table agrees to 3 dp, and so does every B+α concentration number in F52, F53 and F105.
   - **harness_eval:** the arms vs Baleen online in SE units, from `harness_eval/results/deployed.csv` and `0_reproduce/work/results/retrain_dist.csv` (to check validator 1's R5-B1).
6. **Ledger-hypothesis check.** Every ledger hypothesis still has a finding:
   - R: F07, F08, F98;
   - Q1: F18; Q2: F20; Q3: F33;
   - H1′: F25; H2′: F28; S: F31;
   - H3′: F44, F45; H4: F52, F53; H5: F59;
   - the loop: F61–F67.

## Round-4 items: status
| Item | Status |
|---|---|
| 1. B+α vs A+α missing | **Fixed.** The fix covers F105's new table (6 rows, all recomputed identical to 3 dp), its title and priority line, abstract L34, F03, §8 row 24, the §8 summary, F52's "Read this first", F53, and §9 items 2 and 4. Wording residue is validator 1's R5-N3, R5-N11 and R5-N15. Blocking item 1 below, B+α's protocol status, is a new issue. |
| Endorsed: R4-B1, R4-N5, R4-N11, R4-N13 | **Fixed.** See F100/F70 (union rows), F25, the F73 H4 row with F53, and F74 (title and T1/T2 bullet). Validator 1's R5-N22 corrects one detail in F73: the 36 label sets have no sha256 hashes. |
| Non-blocking items 1–8 | **All handled:** |
| | 1: done (F25, legend caveat 2, F73's title). |
| | 2: done (F66's title and index row). |
| | 3: done (F31, §8 row 8; validator 1's R5-N8 refines it). |
| | 4: done (F45; validator 1's R5-N10 refines it). |
| | 5: done ("worse" in F69's title and table; see non-blocking item 1). |
| | 6: done (§8 row 7). |
| | 7: done (Appendix C). |
| | 8: checked. Both round-4 reports were committed in `3de4eff`, and the tracked tree is clean. |

## Blocking issues

### 1. B+α's Region5 result is labelled more strongly than its protocol allows, and more strongly than the story labels the Ising record from the same protocol section
**What the protocol says.**
- **B+α** (`changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md`):
  - L15: "**Secondary (reported with the same rule, no claim).** B+α … vs A and vs B";
  - L78: "**B+α:** the same rule vs A and B, reported as secondary; no claim rests on it."
- **X1, in the same sections:**
  - L17: "**Ising record (no pass/fail beyond reporting the rule).**";
  - L80: "the rule vs A, vs B and vs A+α is reported (Ising record); no pass/fail on X1."
- The protocol thus gives B+α and X1 the same status: the rule is computed and reported, and nothing is claimed.

**How the story treats them.**
- **X1 on Region5** has its own finding, F54 (L1254). It is tagged TEST-POSTHOC, titled "(pre-declared, no pass/fail)", and says "it fails the reported rule".
- **The threshold arms on Region1** were listed by PROTOCOL_v2_H5 as "Reported, no claim". F60 (L1347) tags them TEST-POSTHOC, "which is why this finding is tagged TEST-POSTHOC".
- **B+α on Region5** sits inside the P0 TEST-PREREG finding F52 and the TEST-PREREG finding F53. Nowhere does the story say that no claim rests on it:
  - F52 L1219: "**Secondary arm B+α:** 34.48; 6/6 vs A (+1.70) and 6/6 vs B (+1.89); −4.7%";
  - F52 L1208, "Read this first": "The secondary arm B+α (−4.7%, 6/6) …";
  - F53 L1239: "The secondary arm B+α passes 6/6 … so it too passes only at retrain level".
- **§9 item 2 (L2102)** counts it as part of "the only surviving claim, the load-adaptive threshold (A+α, and B+α)".
- **The legend (L58)** files comparisons that a protocol listed in advance without a pass/fail under TEST-POSTHOC, titled "pre-declared, no pass/fail".

**Why blocking (criteria 2 and 3).**
- **The story's own rule is applied unevenly.** The story applies its labelling rule to the Ising record's failure (F54) and to the threshold's Region1 negative (F60), but not to the threshold's best positive number.
- **The number is the project's largest deployed gain.** B+α's −4.7% (6/6) sits in the P0 headline finding.
- **The wording presents it as confirmed.** "Passes" and "the only surviving claim" read as a confirmed result, and nothing in the story tells the reader that the protocol said no claim rests on it.
- **Correction to my round-4 report.** In round 4 I called B+α "the project's best pre-registered deployed number". That was wrong, and I withdraw the wording.
- **Overlap with validator 1.** Validator 1's R5-N11 covers only the "uniform vs concentrated" wording, not this status question.

**Fix.**
1. **F52 L1219.** Write: "**Secondary arm B+α** (pre-declared secondary, 'reported with the same rule, no claim'; PROTOCOL_v2_H4 L15, L78): it meets the reported rule: 34.48; 6/6 vs A (+1.70) and 6/6 vs B (+1.89); −4.7%. No claim rests on it."
   - Add the refs `PROTOCOL_v2_H4.md#L15` and `PROTOCOL_v2_H4.md#L78`.
   - In "Read this first" (L1208), write "The no-claim secondary arm B+α (−4.7%, 6/6) …".
2. **F53 L1239.** Replace "passes 6/6 … so it too passes only at retrain level" with "meets the reported rule 6/6 (no claim rests on it) … so it too meets it only at retrain level".
3. **§9 item 2 (L2102).** Write "the only surviving claim, A+α vs A and B (B+α was a no-claim secondary in H4: report it as a secondary again, or pre-register it)". Keep the rest of the item.
4. **Legend L58.** Choose one of two options:
   - add H4's B+α to the list of pre-declared no-claim comparisons, and say that F52 and F53 report it under that label;
   - or move the B+α numbers into a TEST-POSTHOC finding parallel to F54.

   Either way, X1 (F54) and B+α must get the same treatment, because the protocol gives them the same status.

## Endorsed from validator 1 (it also fails a grill criterion; not counted again)
- **R5-B1 (F15 L527: "No Ising arm came close"; criterion 3, symmetric honesty).**
  - **Recomputed independently** (matched rows, 9 Baleen-online retrains):
    - Region6: EIM C2 is 0.158 below Baleen online (1.72 SE), the classical R2 0.870 below (2.05 SE) and RB4 0.273 below (1.89 SE).
    - Region7, where the gap runs the other way: C2 is 0.753 *above* Baleen online (≈3.6 SE worse) and R2 0.249 above (≈2.9 SE worse).
  - **What the current text hides.** "Every Region7 arm scored 40.06–40.85, against Baleen online 40.10 ± 0.18" (L523) does not say that the top of that range, the Ising arm C2, is significantly worse.
  - **Fix.** State both directions with the numbers. For example: "On Region6 the closest Ising arm, EIM C2, was 0.16 below Baleen online (≈1.7 SE), against the classical R2's 0.87 (≈2.05 SE) and RB4's 0.27 (≈1.9 SE). On Region7, C2 was 0.75 above Baleen (≈3.6 SE worse) and R2 0.25 above (≈2.9 SE)." Add the computation to `recompute.py`.

## Non-blocking suggestions
1. **Region1 status word.**
   - The grill brief expects "null on Region1". The evidence supports the story's "worse": A+α vs A is −0.487, 1/6, 2.7 instance SE and 7.9 retrain SE (recomputed). Keep "worse".
   - Use the legend's term in F69's title and Region1 row: "(pre-declared, no pass rule)" instead of "(post hoc, no pass rule)", as validator 1's R5-N17 asks. F60 already does this.
2. **Add an instance-SE column to F69's region table.** Recomputed values (A − A+α, mean / SE_inst):
   - Region5 (H4, pre-registered): 1.55;
   - Regions 6/7 (H3′, post hoc): 2.47;
   - Region4 (T2, post hoc): 1.53;
   - Region1: −2.72;
   - Region2 (descriptive): 0.78.

   **What the column shows.**
   - The only threshold comparisons above 2 instance SE are post hoc, on the H3′ pool. Besides A+α vs A (2.47), B+α vs A is 6/6, +0.886, at 3.6 instance SE and 3.8 retrain SE (recomputed). F47's table gives only B+α vs B.
   - The pre-registered H4 sits at 1.55 instance SE.
   - Add the B+α vs A row to F47 as well. It also bears on §9 item 4: B+α's 6/6 sign uniformity vs A also holds on H3′.
3. **Wording, endorsing validator 1:**
   - R5-N3: F03 should add "(1.4 on the descriptive T1)".
   - R5-N15: in F105, write "hurt it beyond 2 retrain SE on none of the test pools (T2 −0.995, 1.8 retrain SE)".
   - R5-N10: in F45, "+0.39" is only 1.9 retrain SE and 0.7 instance SE, and the 3/6 wins vs A+α fail the rule whatever happens to s0.5.
4. **F45's "+1.13" vs A without Region7 s0.5.**
   - That gap is 3.0 instance SE (`recompute_out.txt` L165), but against A+α the same subset gives only 0.7 SE (L166).
   - One clause would stop "+1.13" being read as label value: "(mostly the threshold: vs A+α +0.39, 0.7 instance SE)".
5. **One-click usability for recomputed numbers.**
   - None of the story's 39 links to `changes/4_story/result/recompute_out.txt` carries a line anchor (`grep -c 'recompute_out.txt#L'` → 0). One click opens a 170-line file, not the number.
   - The section heads are at L1, L27, L55, L66, L84, L87, L104, L117 and L148 (round-5 additions).
   - Add `#Lx-Ly` anchors, at least in the P0 findings F25 and F52, and in F45, F53, F70 and F105.
6. **Multiplicity, one sentence (F53 or the §8 summary).**
   - H4 is the only YES among the deployed pre-registered verdicts: Q3 (three finalists), H3′, H3′-labels, H4, H5, T1 and T2.
   - At instance level (1.55 SE) it would not clear even an uncorrected 2 SE bar.
   - The story gives both facts, but not side by side.
7. **Privacy, for the commit after this round.** This report and validator 1's round-5 report contain repo-relative paths only. I checked validator 1's report with the scrub tool's own `scrub_text`.

## Assessment against the five grill criteria
| Criterion | Verdict | Blocking items |
|---|---|---|
| 1. Completeness | **Present:** every ledger hypothesis has a finding; every required source file is cited; FINAL_REPORT §5 is fully carried; no incident in the sources is missing. **Minor gaps:** the instance-level SEs per region and the post-hoc H3′ B+α vs A row (non-blocking item 2) | — |
| 2. Priorities | **Right:** the P0 set; the decisive negatives (Q2, H2′, Q3, H3′, H5, T2) are P0; Track C and T1 are P1; no DEV result is P0. **Inflated:** B+α's no-claim secondary result inside the P0 TEST-PREREG finding F52 and in F53, and called a "claim" in §9 (blocking item 1) | 1 |
| 3. Honesty | No reader can conclude that Ising/QUBO succeeded in deployment. The solver ties are stated plainly, the union and WP2 dev rows included. The threshold's status is stated as the evidence allows: pre-registered YES on Region5 (retrain SE; ≈1.5 instance SE; 69% from one instance), post hoc on Regions 6/7 and Region4 (Region4 mostly a Baleen failure), worse on Region1 with no pass rule, descriptive on Region2. **Asymmetric labelling:** B+α vs X1 and the Region1 arms (blocking item 1). **Endorsed:** R5-B1 (F15), which should state both directions | 1 (same item) |
| 4. Integrity disclosures | **Present:** the auto-research timing items (F84, F63, F65, F86, Appendix B 15:34); the G3 waiver with its go-file text (F74, F76); the privacy redaction, including the current tree (F87); the skipped permissions (F61, header); the Track C firewall timing (F73); the story loop's own incidents (header; file times re-checked this round) | — |
| 5. Usability | **Present:** the index, the P0 headline table, the claims table (24 rows), the timeline, the file map and the recomputation appendix. Every ref is a link, and `check_story.py` reports 0 problems. **Missing:** line anchors on the 39 `recompute_out.txt` links (non-blocking item 5) | — |

```
OPEN_FINDINGS=1
VALIDATOR_STATUS=FAIL
```
