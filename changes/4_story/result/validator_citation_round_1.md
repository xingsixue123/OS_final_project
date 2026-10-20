# Validator 1 (citation and fact check), round 1 of 5

**Target:** `changes/4_story/STORY.md` (story-writer round 1, run 20261020_154140, 92 findings).
**Validator run:** 2026-10-20. Read-only: no file other than this one was written.

## Method

1. **Automated check.** `python3 changes/4_story/code/check_story.py` returns `n_problems 0`, `n_findings 92` and no warnings.
   - The checker is weak:
     - it ignores the integers 0–12, 0.1–0.9, 24, 100 and 2026, so win counts such as "5/6" and "3/6" are never checked;
     - it only tests that a number occurs somewhere in a cited file, ignoring line anchors, arm, instance and budget;
     - it does not check the abstract, sections 8–9 or the appendices.
   - Its pass is therefore no evidence of correctness, and every finding was checked by hand.
2. **Manual audit.** All 92 findings were audited, all 9 P0 and all 39 P1 included, plus:
   - the abstract and legend;
   - the section 8 claims table (22 rows) and section 9;
   - Appendix A.1–A.11, Appendix B (timeline) and Appendix D (one-liners).

   Each cited ref was opened at its anchor. Every number was checked for value, units, sign, arm, instance and budget. The wording, the evidence tag and the directness of each ref were also checked. Commit hashes and times were checked with `git log --all`.
3. **Recomputation.** `python3 changes/4_story/code/recompute.py` (stdout only) is byte-identical to `changes/4_story/result/recompute_out.txt`.
4. **Independent spot checks.** I recomputed from the raw CSVs with my own script, not `recompute.py` (see "Spot checks" below).

Classification rules used in this round:
- **BLOCKING:**
  - a wrong number or a wrong claim;
  - a claim contradicted by its source;
  - a statement supported by **no cited file** and with no explicit `(Fxx)` cross-reference;
  - an evidence tag that conflicts with the legend or with the source.
- **NON-BLOCKING:**
  - the claim is in a cited file but outside the `#L` anchor;
  - the claim is backed by an explicit `(Fxx)` cross-reference;
  - imprecise wording, omitted caveats, or rounding inherited from the source.

## Blocking problems

| # | Finding | Issue | Evidence (file:line) | Required fix |
|---|---|---|---|---|
| B1 | Abstract (STORY.md L16) | **Missing ref.** "Ising peak labels: phase-1 Q3 and … H3′" cites only the H3′ file. Q3 is not cited anywhere in the abstract. | `changes/1_literature_review/explore/q3/RESULTS.md:8` "**Q3 — … — NO.** None of the three Ising-family finalists passes" | Add `changes/1_literature_review/explore/q3/RESULTS.md#L6-L15` (or "(F33)"). |
| B2 | Abstract (STORY.md L22) | **Missing ref.** "It also helped post hoc on Regions 6/7 and Region4, and did not help on the low-load Region1" has no ref and no cross-reference. The only ref in the paragraph is the Region5 file. | `changes/2_deployable_peak/wp3_test/RESULTS_test.md:53-60` (A+α 38.30, post hoc); `changes/3_autoresearch/result/FINAL_REPORT.md:75` (A 50.72 → A+α 42.87); `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md:19` (A+α 24.62 vs A 24.14) | Add these three refs, or "(F47, F66, F60; F69)". |
| B3 | F13 | **Missing ref.** "F1 … used by every Q1/Q2, H1′ and H2′ configuration and by the phase-2 F1-label arms": all three refs are phase-1 files. Nothing cited supports the H1′, H2′ or phase-2 label claims. | `changes/2_deployable_peak/wp1_offline/RESULTS.md:26-27` "F1 (min-max peak), 8 nested levels"; `changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md:12,27` "OPT-mode F1 instances … F1: minimise max_w L_w(x)"; `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md:58` "X1 (primary) \| F1PT" | Add these refs. |
| B4 | F21 | **Wrong meaning of a number.** "SB V = −11.64%, the lowest of the four Ising solvers": the rule is "the two lowest V are the finalists". SB's −11.64% is the **highest**, i.e. worst, V. | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md:189` "the two lowest V are the finalists"; L193–196: pt −14.58, eim −14.14, mq −12.50, sb −11.64 | Write "the worst (highest) V of the four". Widen the anchor to `#L187-L196`. |
| B5 | F21 (title and harness_eval bullet) | **Unsupported or overclaimed.** "The proposal's own Ising design … was the weakest Ising arm" is contradicted by harness_eval, a cited file. There, C5 is analytically worse than C4 (SoS + matrix-free SB) on both traces, and C4 is named the best Ising arm in simulation. The bullet compares C4 only with C2 and R2. | `changes/1_literature_review/harness_eval/RESULTS.md:166-167` (Region7 C4 24.343 vs C5 24.376; Region6 23.044 vs 23.373); L197 "The best Ising arms are C4 (27.97 / 27.87) and C5"; L250 "For the best Ising arm, C4" | Limit "weakest" to the phase-1 dev tuning (q2) and the WP5 finalist rule. State that in harness_eval C4 beat C5 analytically and was the best Ising arm in simulation. |
| B6 | F44 | **Silent contradiction / unsupported claim (P0).** "Test set: Region7/Region6 × samples 0.4–0.6, touched once" repeats PROTOCOL_v2_H3 ("None of them has been used for any tuning, selection or inspection"). But WP1 had already simulated the offline OPT of exactly these 6 instances, committed `08ad0d2` 2026-10-03 00:11, before `cba9970` 2026-10-04 09:16. F48 itself uses those WP1 OPT values for retention. F92 corrects the same "untouched" wording for the reserve but not for the test set. | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv` (rows Region6/7 s0.4–0.6); `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md:25-27`; `changes/2_deployable_peak/wp1_offline/RESULTS.md:111-113` (WP1 ≥0.4 not used by WP5); STORY F48 "with WP1's offline OPT values" | Write "touched once in deployed mode; their offline OPT peaks were already simulated in WP1 (used for retention, not for any selection)". Cite `wp1_table.csv` and WP1 RESULTS L111–113. Add the same caveat to F92 or F75-style text. |
| B7 | F48 (title), echoed in F40 ("reversed on test") and F70 ("H3′: CP-SAT labels better by 0.89") | **Overclaim.** "CP-SAT labels deploy better than PT labels" rests on a mean difference of 0.89 with instance SE 0.84 (≈1 SE). Each side wins 3/6. Region7 s0.5 contributes 4.81 of the 5.33 summed difference. The protocol attached no pass/fail. F40 calls a ≈2-SE dev effect "no claim" but treats this ≈1-SE test effect as a reversal, an asymmetric standard. | `changes/2_deployable_peak/wp3_test/RESULTS_test.md:14` "CP-SAT labels better by 0.89 (3/6; instance SE 0.84)"; `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md:98`; recomputed from `wp3_test/trials.csv`: per-instance Dc+α vs X1 = −0.433, −0.375, +0.107, −0.368, **+4.808**, +1.594 | Title: "CP-SAT labels have the lower mean by 0.89 (≈1 instance SE, 3/6 each way, driven by Region7 s0.5)". Soften F40's "reversed on test" and F70's bullet the same way. |
| B8 | F60 | **Wrong evidence tag.** TEST-PREREG means "a pre-registered test whose protocol was fixed before the run". This comparison was listed only under "Reported, no claim", with no rule. The cited result file says "Not pre-registered", and the story's own F69 files the same Region1 result under TEST-POSTHOC. | `changes/2_deployable_peak/wp10_schedule/PROTOCOL_v2_H5.md:62-64`; `changes/2_deployable_peak/wp10_schedule/RESULTS_test.md:19` "Not pre-registered (H4 was a Region5 test)"; STORY F69 row "Region1 … declared as a reported comparison, no claim, and no pass rule" | Either retag F60 TEST-POSTHOC, or add a legend tag for "pre-declared reported comparison, no pass/fail" and use it consistently (see N-TAG). Replace "contradicts its own protocol" with "is in tension with". |
| B9 | F71 (and section 8 row 20, "TEST-PREREG (reported metric)") | **Wrong evidence tag.** Retention was "also reported (no pass/fail)" in both protocols. The 60% criterion appears in **no** phase-2 protocol, only in the proposal. Scoring test retention against 60% is therefore post hoc. The priority line "they carry weight" as pre-declared overstates this. | `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md:100-103`; `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md:84-87`; `documents/proposal_docx_compose/proposal.js:201` | Retag TEST-POSTHOC (pre-declared metric, criterion from the proposal), or use the new legend tag, and reword the priority line. Also say "mean retention": WP2 dev per-instance X1 reaches +0.74 (`wp2_deployed/RESULTS_dev.md:232`). |
| B10 | F64 (priority line) | **Contradicts its source.** "Its loss came from a design defect rather than an effect" conflicts with the T1 report: "No reading of T1 favours Y. The T1 failure is not an artefact of s0.2." F64's own body says no reading favours Y beyond noise. | `changes/3_autoresearch/work/t1u_region2/RESULTS_test.md:61` | Write "It was unevaluable as pre-registered because of a design defect (s0.2 infeasible; A unmatched), and the descriptive s0.3–0.6 numbers do not favour Y either". |
| B11 | F72 | **Wrong claim.** "Region6 first-access admission stays at or below 1.3% in every WP2 and Track C arm" is false. WP2 arm D:P0 averages 2.9% on Region6 (maximum 5.6%). The cited table lists only A, B, A+α, D:F1PT and X1. | `changes/2_deployable_peak/wp2_deployed/results/mechanism_by_region.txt:13` "D:P0 … k0_adm 0.029"; recomputed from `wp2_deployed/trials.csv` (matched, Region6, D:P0): mean 2.89%, max 5.61%, n = 4 | Write "≤ 1.3% in every F1- and Baleen-label WP2 arm and every Track C arm; the phase-1 design P0 reaches 2.9%". Cite `mechanism_by_region.txt`. |
| B12 | F77 | **Missing refs.** "Every stage reports `check_frozen.sh` → 'frozen OK (94 files)'" names 12 stages, but the refs cover only CP1, WP5 and WP2. The 16:22 date is also uncited. | Sources: `0_reproduce/RESULTS.md:69`, `1_literature_review/explore/q2/RESULTS.md:342`, `explore/q3/RESULTS.md:320`, `harness_eval/RESULTS.md:280`, `wp3_test/RESULTS_test.md:78`, `wp8_trackC/RESULTS_dev.md:108`, `wp9_region5/RESULTS_test.md:52`, `wp10_schedule/RESULTS_test.md:39`, `3_autoresearch/work/t1u_region2/RESULTS_test.md:105`, `3_autoresearch/work/t2u_region4/RESULTS_test.md:61`, `wp5_ising/RESULTS_dev.md:405` (16:22) | Add these refs (paths relative to `changes/`). |
| B13 | F80 | **Unsupported claim.** "Both solver families were exposed alike" (phase-1 Q2 SMT-sibling exposure) is in no file. The same sentence says the sibling load is "unquantified", so equality cannot be known. In WP5 the same setup gave *unequal* exposure. | `changes/2_deployable_peak/wp5_ising/PROGRESS.md:67` "the 1-s `deval` runs … were NOT equally exposed"; `changes/1_literature_review/explore/q2/RESULTS.md:46` only says both families were pinned to cores 0–7 | Write "both families ran under the same pinning; per-family sibling exposure was not measured". |
| B14 | F89 | **Missing ref.** The title "did no work" and "changed only the loop status files" are not supported by `changes/3_autoresearch/README.md#L1-L9`, which does not mention Codex or either run id. `git_timeline.txt` gives only commit subjects. | `changes/3_autoresearch/result/LAB_NOTEBOOK.md:1-8` "The earlier run (20261019_233548) only changed LOOP_STATUS"; `git show --stat 74577ee f4d758e` | Add `changes/3_autoresearch/result/LAB_NOTEBOOK.md#L1-L8`. |

## Non-blocking problems (fix recommended)

| # | Finding | Issue | Evidence (file:line) | Suggested fix |
|---|---|---|---|---|
| N-TAG | F30, F48, F54 (and section 8 rows 7, 20) | The legend has no tag for "pre-declared reported comparison, no pass/fail". These use TEST-PREREG, but their titles disclose "no criterion" or "no pass/fail", so a reader is not misled. Same root cause as B8 and B9. F54's window-924 analysis (14/15 retrains, share 0.515) is post hoc on raw `trials.csv`. | `wp5_ising/PROTOCOL_v2_H2.md:82-86`; `wp2_deployed/PROTOCOL_v2_H3.md:98`; `wp9_region5/PROTOCOL_v2_H4.md:80` | Add a legend tag (e.g. TEST-REPORTED) and apply it to F30, F48, F54, F60 and F71. Mark the F54 window analysis "post hoc". |
| N1 | Header L5 | "Every number in a finding below is checked by `check_story.py` against the files that finding cites" overclaims (trivial numbers are skipped; presence only; no anchors). | `changes/4_story/code/check_story.py:27` (`TRIVIAL`) | Write "every non-trivial number occurs somewhere in a cited file". |
| N2 | Abstract L11 | "the same held across 39 instances": wins were 36–37/39. | `wp1_offline/RESULTS.md:7-9` | Write "on 36–37 of 39 instances". |
| N3 | Abstract L13; L1501–1504 | The Q2 sentence cites only the H2′ file. "Ising/QUBO solvers match but do not beat classical solvers" understates the losses at 1 s, 60/300 s and in rolling windows. "about 16% on three of four regions": Region5 alone is 13.0–14.6%. | `explore/q2/RESULTS.md:12-31`; `wp1_offline/RESULTS.md:12` | Add the q2 ref. Write "are competitive with" and "≈16% pooled over Regions 5–7 (13–18% per region)". |
| N4 | Abstract L15 | "every Ising/QUBO component failed its pre-registered test": Track C and H-CLS failed pre-registered *dev gates* and never reached a test. | `wp8_trackC/RESULTS_dev.md:7`; `3_autoresearch/result/FINAL_REPORT.md:24-28` | Add "or its pre-registered dev gate". |
| N5 | F03 | "exactly one causal demand-load signal" omits the optional hour-of-day sin/cos in the same group, which WP2's D2 arm used (F42). | `changes/SCOPE_v2.md:20` | Mention the optional tod sin/cos. |
| N6 | F06, F09 | F06's "without a GPU" is supported only via F90. F09's "every later protocol requires ≥3 retrains" is not in its refs. | `explore/q2/RESULTS.md:46`; `changes/SCOPE_v2.md:37` | Add the refs. |
| N7 | F11, F12 | F11: "No Ising arm reaches LP-round + repair at any size" is a median statement; at 1k they are comparable. F12: "8.3%" is outside its anchor; the bit-identical claim covers bSB/dSB only, not CAC. | `ising_followup/audit/AUDIT.md:159,162,166,190` | Add "(median; comparable at 1k)". Widen the anchor to L162. Write "bSB/dSB". |
| N8 | F14 | The title's "day-1 extended-Ising energy" sits at L6–7, outside the anchor. | `explore/common/Q3_FORMULATION.md:6-7` | Use anchor `#L6-L56`. |
| N9 | F26 | "coincides … on only 6/39, 9/39 and 6/39" drops the source's "(±10 min)". Exact coincidence is 5/4/3 (recomputed from `wp1_table.csv`). | `wp1_offline/RESULTS.md:102-103` | Add "(±10 min)". |
| N10 | F27 | The list of R0 peaks on the "other samples" omits Region4 s0.6 at d3 03:20 (window 452). | `wp1_offline/RESULTS.md:52`; `wp1_table.csv` `R0_argmax` = 452 | Write "d3 03:20/03:30, d5 14:10 or d6 00:50". |
| N11 | F30 | The table omits LP 26.708, which beats LS 26.740, without saying so. Also missing: seed 0 only, and a Pylance burst during the first PT windows. | `wp5_ising/RESULTS_test.md:140,150,174-176` | Add the LP row or an omission note, and add the caveats. |
| N12 | F32 | "the finalists used F1PT" is outside the anchor. | `wp2_deployed/RESULTS_dev.md:25` | Add `#L25`. |
| N13 | F33, F34, F35 | F33: "3 retrains each", but T2 Region7 s0.2 has 2. F34: "40.18" is the source's rounding of 40.1749. F35: "relabelled 0.13–0.44" includes a non-scan instance (0.13–0.41 on the three scan instances); the title generalises from 3/6 instances. | `explore/q3/RESULTS.md:201,252,266-295` | Add the caveats. Write "on 3/6 held-out instances". |
| N14 | F36, F37 | F36: "bit-identical" excludes wall-clock and RAM, and "+217/−6" counts non-blank lines (numstat gives +256/−6). F37: the title says "Ising peak-aware labels", but F1CPSAT also passes and the Ising C2 design fails. | `wp0_overlay/CP1.md:66`; `wp2_deployed/RESULTS_dev.md:103-108` | Qualify. Write "F1 (min–max) peak-aware labels". |
| N15 | F41 | The priority line ("depended on scans being present on day 1") is not in F41's refs. | `wp3_test/RESULTS_test.md:49` | Add the ref. |
| N16 | F46 | "Window 378 … for every arm" is true per arm but not per retrain: B+α rep 1 peaks at window 636 (share 0.064). The "why the F1 labels miss it" paragraph is the source's diagnosis, stated as fact. | `wp3_test/trials.csv` (Ba-1.0, Region7_s0.5, rep 1, argmax 636); `wp3_test/RESULTS_test.md:42` "diagnosis, not a re-analysis" | Write "(20 of 21 retrains)" and "Diagnosis (source):". |
| N17 | F49, F50 | "Top-k ≈ F1" is at PLAN_C L98, outside `#L85-L96`. The commit `19d7992` and "64 evaluations, all matched" are outside F50's anchors. | `wp8_trackC/PLAN_C.md:98`; `wp8_trackC/RESULTS_dev.md:3-4,28` | Fix the anchors. |
| N18 | F52 | "α = −1 and ref = 20 were fixed from Region6/7 dev": L53 says only "fixed"; the Region6/7 origin is at L92. | `wp9_region5/PROTOCOL_v2_H4.md:92` | Add `#L92`. |
| N19 | F54 | "one catastrophic scan-type instance" hides a second large loss. On s0.6 X1 scores 40.78 vs A 36.38 (−4.40), and the peak window has a big-offset share of ≈0.44. | `wp9_region5/trials.csv`; my recomputation: X1 vs A per instance s0.6 −4.405 | Mention s0.6. |
| N20 | F57 | The title "find the same threshold tables" holds on 46/48 packs. "31.28" is the source's figure; the raw mean is 31.2747. | `wp10_schedule/PROGRESS.md:84-85` | Write "the same (scale-equivalent) tables on 46/48 packs". |
| N21 | F59, F63, F65, F73, F74 | The claim is in a cited file but outside the anchor, or backed by an explicit (Fxx) cross-reference. F59: deviation (cross-referenced as F83) at L42. F63: "9 of 16" (cross-referenced as F84) at L107. F65: "before any T1 run" at L63. F73: void `9650674` at L147. F74: TEST_GO at L3. | `wp10_schedule/RESULTS_test.md:42`; `3_autoresearch/result/FINAL_REPORT.md:63,107,147`; `wp9_region5/PROTOCOL_v2_H4.md:3` | Widen or add the anchors. |
| N22 | F70 | Anchors: "Classical best … in rolling windows" is at wp5 RESULTS_test L138–165, not L41–43. "Ising best at 10 s / 3 s" is at q2 L243–245 and wp5 L22–24. "CP-SAT labels deployed better on one retrain" is backed only by the cross-reference to F50 (source wp8 RESULTS_dev L20, not cited in F70). | `wp5_ising/RESULTS_test.md:22-24,138-165`; `explore/q2/RESULTS.md:243-245`; `wp8_trackC/RESULTS_dev.md:20` | Add the anchors. |
| N23 | F72 | "WP2 dev: 2.4–2.8%" covers D:F1PT and X1 only; the source text says "2–3%", and other F1 arms span 1.4–3.2%. | `wp2_deployed/RESULTS_dev.md:229`; `mechanism_by_region.txt` | Write "2–3% (D:F1PT 2.4%, X1 2.8%)". |
| N24 | F73 | The table omits H1′ (WP1). It was pre-registered in PLAN (`27fb6f0`, 09-29) before WP1 ran (10-01), so the claim holds, but the table is incomplete. | `changes/2_deployable_peak/PLAN.md:18-19` | Add a row, or scope the table to deployed and solver tests. |
| N25 | F79, F84, F86, F90 | F79: the title says "each handled by superseding or flagging rows", but items 4–6 involved no rows. F84 item 6: "because it was pre-registered" is an inference. F86 item 3 is partly in the notebook (L408). F90: the desk check "assumed" the Threadripper, but it actually ran on it. | `wp5_ising/RESULTS_test.md:174-185`; `3_autoresearch/result/LAB_NOTEBOOK.md:408`; `documents/top_doable_papers_filtered.md:12-17` | Reword. |
| N26 | F80 | The sources conflict on when Track B was pinned: 15:05 vs 15:00. Not a story error. | `wp5_ising/PROGRESS.md:52`; `wp1_offline/RESULTS.md:116` | Optionally note it. |
| N27 | F87 | The disclosure is incomplete. The tracked `tools/privacy_scrub.py` still contains the redacted patterns as regex literals and skips itself in `--check`, so the public tree, not only git history, still shows them. Names are deliberately not repeated here. | `tools/privacy_scrub.py:19-28` | Disclose this in F87. |
| N28 | F92 | PLAN itself scheduled WP1's offline use of 0.7–0.9 (L19, L44), so it was planned, not a deviation. Reserve instance dumps exist on disk, untracked and git-ignored: `wp1_offline/inst/full_Region{4..7}_s0.{7,8,9}.npz`. That makes PROTOCOL_v2_H5 L27 ("No job or instance exists for them") literally false. | `changes/2_deployable_peak/PLAN.md:19,44`; `changes/2_deployable_peak/.gitignore:10`; `wp10_schedule/PROTOCOL_v2_H5.md:27` | Add both points. |
| N29 | Section 8 | Row 7: "rolling windows reverse it" holds on dev at 1 and 3 s; the test ran at 1 s only. Row 18: the proposal averages over traces; the per-trace means are 12.8 / 12.9 / 13.5% (recomputed), not 13.0–13.7%, and the verdict is unchanged. Row 19 omits that the proposal's H2 was about the SoS surrogate (F21). Row 20: "Not supported" is defined for dev/offline evidence. Status words outside the five defined (rows 1, 3, 7, 17, 18, 19). Rows 5 and 9 lack the phase-1 git caveat that row 2 has. | `wp5_ising/RESULTS_dev.md:18-20`; `wp5_ising/RESULTS_test.md:138`; `documents/proposal_docx_compose/proposal.js:199-200`; STORY L1468-1473 | Reword the rows and harmonise the status vocabulary. |
| N30 | Section 9 item 3 | "Per-window attribution of the peak" is not at RESEARCH.md L122; it comes from the proposal. | `RESEARCH.md:122`; `documents/proposal_docx_compose/proposal.js:211` | Fix the ref. |
| N31 | Appendix A.1, A.8 | A.1: the "ours" Baleen values 43.27 / 40.06 are single runs at WR 33.879 / 38.578; the Region7 run fails the WR check, and the file verdict is "NOT PASSED". A.8: "D8 rows are … sim-only" follows RESULTS_dev L24, but PROGRESS L126–127 says D8 trains and E8 is sim-only. The sources disagree; the numbers are unaffected. | `0_reproduce/work/results/fig9_summary.md:9,14,36,38`; `wp8_trackC/RESULTS_dev.md:24`; `wp8_trackC/PROGRESS.md:126-127` | Add a note to each. |
| N32 | Appendix B | `b0d6e2b` (final report) is at 10:03:31, not 10:01. The dev control was launched at 10:01, not 10:03. WP2's area was set up at 16:25; label solves began at 16:27 and the first ledger row is 17:11. | `changes/4_story/result/git_timeline.txt:60`; `3_autoresearch/result/validator_red_team_round_2.md:52` | Correct the times. |
| N33 | Appendix D | Item 4's grep also matches `changes/4_story/STORY.md`. The story says "matches only `changes/SCOPE.md`". Item 1: "Every recomputed value agrees" — WP9 raw −0.246 / +1.183 vs the report's −0.24 / +1.19 (disclosed in F53). | Running the item-4 command prints `changes/SCOPE.md` and `changes/4_story/STORY.md` | Add `\|4_story` to `grep -v`. Write "agrees to the source's rounding". |

Checked and found correct (no problem): F01, F02, F04, F05, F07, F08, F10, F15, F16, F17, F19, F20, F22, F23, F24, F25, F28, F29, F31, F38, F39, F40 (numbers), F42, F43, F45, F47, F51, F53, F55, F56, F58, F61, F62, F66, F67, F68, F69 (numbers), F75, F76, F78, F81, F82, F83, F85, F88, F91, and the tables A.2–A.7 and A.9–A.11.
- Every commit hash and time in F73 and Appendix B matches `git log --all`.
- Every protocol commit precedes its go-file, and each go-file precedes the first test row in the ledger.
- No RESEARCH.md number is repeated in the story while its primary file contradicts it unflagged. The known discrepancies (≈11.3%, ≈70k, last-updated date) are already flagged in F08, F31 and F88.

## Spot checks (my own recomputation from raw CSVs, matched rows only)

Script: `/tmp/claude-243161/-home-sxing-project-OS-final-project/4452541b-7597-4a41-ac0b-cce0073915a0/scratchpad/spot.py` and `/tmp/claude-243161/-home-sxing-project-OS-final-project/4452541b-7597-4a41-ac0b-cce0073915a0/scratchpad/wp1.py`. They are independent of `recompute.py`. The configuration mean is the mean over instances of the per-instance retrain mean. SE_inst = sd(d_i)/√n; SE_retrain = √(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i)/n.

| # | Story claim | Raw source | Recomputed | Verdict |
|---|---|---|---|---|
| S1 | F44: X1 40.53; A 39.27; X1 vs A 5/6, −1.27, SE 0.15 / 2.41; F46: Region7 s0.5 X1 retrains 51.7–52.8, mean 52.30; without s0.5: A 39.31, A+α 38.57, X1 38.18, Dc+α 38.07; first-access pooled 1.8–1.9% vs 4.1–4.8%, Region7 3.3–3.6% vs 7.6–9.4% | `changes/2_deployable_peak/wp3_test/trials.csv` (126 matched) | X1 40.532, A 39.267; 5/6, −1.265, 0.154 / 2.413; retrains 51.67 / 52.46 / 52.77 (52.30); 39.307 / 38.573 / 38.178 / 38.073; pooled F1 1.77–1.94%, Baleen 4.09–4.82%; Region7 F1 3.26–3.58%, Baleen 7.61–9.41% | match |
| S2 | F52/F53: A+α 35.02 vs A 36.17, 5/6, +1.16, SE 0.09 / 0.75; −3.2%; B+α 34.48, 6/6 vs A (+1.70) and vs B (+1.89); F54: window 924 in 14/15 s0.5 retrains, share 0.515; X1 first-access 2.2% vs 3.8%; mean DT +0.8 | `changes/2_deployable_peak/wp9_region5/trials.csv` (90 matched) | 35.020 vs 36.174, 5/6, +1.155, 0.094 / 0.745; −3.19%; 34.479, +1.696, +1.887; 924 in 14/15 (B+α rep 2 at 336), 0.5154; 2.21% vs 3.79%; 19.605 − 18.802 = +0.80 | match |
| S3 | F59/F60: TB:pt 24.45; vs A 1/6, −0.31; vs B+α 3/6, +0.02, SE 0.09; A+α vs A 1/6, −0.487; B+α vs A −0.338; α arms raise mean DT ≈0.25 | `changes/2_deployable_peak/wp10_schedule/trials_test.csv` (108 matched) | 24.452; 1/6, −0.314; 3/6, +0.024, SE_retrain 0.091; −0.487; −0.338; mean DT 12.262 / 12.268 vs 12.023 (+0.24 / +0.25) | match |
| S4 | F65/F66: Y 43.17; vs A+α 1/5, −0.300, SE_retrain 1.117; A+α vs A 5/5, +7.847, SE 0.446 / 5.125, −15%; 8 `__FAILED_` rows; peak-window admission Y 0.31 vs A+α 0.41 | `changes/3_autoresearch/work/t2u_region4/trials_test.csv` (98 rows, 90 matched) | 43.170; 1/5, −0.300, 1.117; 5/5, +7.847, 0.446 / 5.125, −15.47%; 8 FAILED rows; 0.311 vs 0.410 | match |
| S5 | F25/F19: PT 37/39, 13.69%; Region4 7/9, 5.37%; Regions 5–7 30/30, 16.18%; LP 36/39, 13.03%; CP-SAT 36/39, 13.15%; 156/156 matched; PT − CP-SAT −0.18, PT lower 18/39; best-of-three 14.6%; F27 losses | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv` (39 rows) | identical (13.69 / 5.37 / 16.18; 13.03; 13.15); 156/156; −0.184, 18/39; 14.59%; CP-SAT −6.9% (s0.9) and −4.8% (s0.8), PT −4.1% (s0.8), LP −1.6% (s0.8) | match |
| S6 (extra) | F72: Region6 first-access ≤ 1.3% in every WP2 and Track C arm | `changes/2_deployable_peak/wp2_deployed/trials.csv`, `changes/2_deployable_peak/wp8_trackC/trials.csv` | WP2 D:P0 Region6 mean 2.89% (max 5.61%); D:T2 1.04%; all other WP2 arms ≤ 0.74%; Track C means ≤ 1.26% | **mismatch → B11** |

## Counts

- Findings audited: **92/92** (P0 9/9, P1 39/39, P2 29/29, P3 15/15). Also audited: the abstract, the legend, section 8 (22 rows), section 9 and appendices A.1–A.11, B and D.
- `check_story.py` problems: **0**. The checker is weak, see Method item 1.
- Recomputed numbers: **5 required spot checks + 1 extra**. All match except S6, which confirms B11.
- **Blocking problems: 14.**

  | Kind | Count | Items |
  |---|---|---|
  | Wrong number or claim | 2 | B4, B11 |
  | Unsupported, contradicted or overclaimed | 5 | B5, B6, B7, B10, B13 |
  | Wrong evidence tag | 2 | B8, B9 |
  | Missing refs | 5 | B1, B2, B3, B12, B14 |

  By priority:

  | Priority | Count | Items |
  |---|---|---|
  | P0 | 1 | B6 (F44) |
  | P1 | 6 | B3 (F13), B4 and B5 (F21), B8 (F60), B9 (F71), B10 (F64) |
  | P2 | 3 | B7 (F48), B11 (F72), B13 (F80) |
  | P3 | 2 | B12 (F77), B14 (F89) |
  | Abstract | 2 | B1, B2 |
- Non-blocking problems: **34** (N-TAG and N1–N33).

```
OPEN_FINDINGS=14
VALIDATOR_STATUS=FAIL
```
