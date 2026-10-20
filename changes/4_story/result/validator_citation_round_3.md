# Validator 1 (citation and fact check), round 3 of 5

**Target:** `changes/4_story/STORY.md` (story-writer round 3, run 20261020_154140, 104 findings).
**Validator run:** 2026-10-20. Read-only: the only file written is this report.
- **Side effect.** Step 1 runs `check_story.py`, which always rewrites `changes/4_story/result/check_story.json`. Its content depends only on STORY.md and the files the story cites. Across a rewrite observed during this audit the md5 stayed the same.

## Method

1. **Automated check.** `python3 changes/4_story/code/check_story.py` gives `n_problems 0`, no warnings and `n_findings 104`. The checker does not verify:
   - that a link target is tracked in git;
   - that an anchor actually contains the claim;
   - the arm, instance or budget a number refers to.
2. **Manual audit, every finding.**
   - **Coverage.** All 104 findings were audited. 90 were checked in full (each ref opened at its anchor; numbers, wording, evidence tag and directness checked). That includes all 9 P0 and all 44 P1 findings, and every finding that is new or edited in round 3 (`git diff`).
   - **Numbers and dates only:** F74, F77–F82, F85, F86 and F88–F91 (14 P2/P3 findings).
   - **Also checked:** the header, abstract, legend and index; all 23 rows and the summary of §8; §9; Appendix A cell by cell (A.7, A.9, A.10, A.11 and A.6 were recomputed from the raw ledgers); every commit hash and time in Appendix B (32/32 match `git show`); every Appendix C path (all exist and are tracked); and Appendix D items 3–10, re-run.
   - **How the work was split.** Six read-only sub-audits (one per story section) gathered evidence in parallel. I re-verified every blocking item below against the source myself.
3. **Recomputation.** The stdout of `python3 -B changes/4_story/code/recompute.py` is byte-identical to `changes/4_story/result/recompute_out.txt`. Item 9, run with its output redirected, reproduces `untracked_evidence.txt` byte for byte.
4. **Independent spot checks.** I recomputed numbers from the raw CSVs and JSONs with my own scripts, independent of `recompute.py` and not committed. See "Spot checks" below.
5. **Privacy.** `python3 -B tools/privacy_scrub.py --check` is clean (exit 0). This report uses only repo-relative paths.

Classification is unchanged from rounds 1–2.
- **BLOCKING:**
  - a wrong number or claim;
  - a claim its source contradicts;
  - a statement supported by no cited file and no explicit `(Fxx)` cross-reference;
  - a wrong evidence tag.
- **NON-BLOCKING:**
  - the claim is in a cited file but outside the anchor;
  - imprecise wording or an omitted caveat;
  - rounding or wording inherited from the source.

## Round-2 blocking items: status

| Round-2 item | Status in round 3 |
|---|---|
| R2-B1 (LP start: legend, F14, F21) | **Fixed and correct in substance.** Checked against the code: `q3solve.py:282-286` starts from Baleen's selection; WP2's copied `q3lib/q3solve.py` is byte-identical, so D:P0 and D:T2 inherit that start; `labels_c.py:126-131` uses `start = "baleen"` / `"prev_round"`; every F1PT/F1EIM label JSON has `cfg.start = "lp"` (196/196). **But** the new clause "every deployed F1PT/F1EIM label set (WP2, WP3, WP9, the union)" has no ref for WP9 or the union (R3-B2). |
| R2-B2 (F31 harness C4) | Fixed: harness L197–198, L231–233, L250. |
| R2-B3 (§8 rows 8 and 19) | Fixed: both are scoped, and row 8 adds "C4 beat C5 analytically" (harness L166–167). |
| R2-B4 (F70 "three rows exceed 2 retrain SE") | Fixed: 2.68 / 2.14 / 2.50, matching my recomputation (S6). |
| R2-B5 (F95 Region3) | Fixed: cites `PROTOCOL_v2_H5.md#L24` and `3_autoresearch/README.md#L7`. No tracked csv/json/jsonl mentions Region3. |
| R2-B6 (F101 largest gap) | Fixed: 4.81 on Region6 s0.9; Region4 s0.3 is 4.01 (S7). |

The round-2 non-blocking items N1–N28 were re-checked and are addressed, with two exceptions:
- **N8** is only partly fixed: F31's title still says "in at most 214 MB" (see N12).
- **N13's** post-hoc marker is in F53 but not in F52's title (see N24).

## Blocking problems (round 3)

| # | Finding | Issue | Evidence (file:line) | Required fix |
|---|---|---|---|---|
| R3-B1 | **F70** (P1), STORY L1519 ("Reading", first bullet) | **Wrong claim, and a cited ref contradicts it.** F70 says "For the F1 rows the objectives tie, so the deployed differences come from *which* (near-)co-optimal label set each solver returns: PT's sets vary by seed, CP-SAT's barely do". That holds only for the auto-research test-pool solves. **H3′ test labels:** CP-SAT's F1 day-1 objective is *lower* than PT's on **36/36** solves (6 instances × seeds 1–6), by 0.04–0.20 util points (0.20–0.88%); the means are PT 21.057 and CP-SAT 20.965. So the H3′ row (CP-SAT labels deployed better by 0.89) is not a pure co-optimal-set effect. **WP2 dev labels:** CP-SAT lower on 10, PT lower on 10, 4 exact ties (within ±0.57%). **Stability:** F70's own cited ref says CP-SAT is "about as stable" (Jaccard 0.74 vs PT 0.76). | `changes/2_deployable_peak/wp3_test/labels/Region7_s0.5_F1PT_s1.json` (`label_peak_util` 22.0129; `info.per_level[0].obj` 22.0129, solver `pt`, budget 10) vs `…/Region7_s0.5_F1CPSAT_s1.json` (21.8859, `cp_status` FEASIBLE, budget 10); the same values are in `changes/2_deployable_peak/wp3_test/trials.csv`, column `label_peak_day1`. `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md:182` ("about as stable (Jaccard 0.74)", inside the cited L172–184); `changes/2_deployable_peak/wp2_deployed/PROGRESS.md:40` ("F1PT 0.76, F1CPSAT 0.74"). The auto-research scope of the tie claim is `changes/3_autoresearch/result/FINAL_REPORT.md:77-79,91-93`. Recomputed: S10. | Restrict the tie and stability sentence to the auto-research test pools. State that the WP2 dev objectives are near-ties either way (10/10/4), and that on the H3′ test labels CP-SAT had the better objective on every solve (shared cores, F100). Add the WP3 result under "Budget-dependent winners". Align §8 row 23 ("The F1 objectives tie where compared") and scope F32's title to WP2 dev (N45). |
| R3-B2 | **F21** (P1), STORY L632, and **F24** (P1), STORY L677; legend L70 | **Missing ref.** The claim "every deployed F1PT/F1EIM label set (WP2, WP3, WP9, the union)" started from the LP is **true**: 196/196 label JSONs record `cfg.start = "lp"` at 10 s. But no cited file covers WP9 or the union. F21 cites only WP2's `labels.py#L1-L4` (plan_F1 10 s), which, together with q2 L165–167 ("LP start"), covers WP2. F24 cites only `PROTOCOL_v2_H3.md#L67-L71`, which covers WP2 and WP3. | Direct sources: `changes/2_deployable_peak/wp9_region5/PROTOCOL_v2_H4.md:55` ("frozen 10 s configuration (`explore/q2/plan_F1.json`, `pt`, `cfg_by_budget["10"]`, LP start"); `changes/2_deployable_peak/wp9_region5/INSTANCES.md:29` ("identical to WP3 … LP start"); `changes/3_autoresearch/work/t1u_region2/PROTOCOL.md:41` ("the frozen 10 s configuration of `explore/q2/plan_F1.json`"); `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md:70` ("LP start"). | Cite H3 L70, H4 L55 (or INSTANCES L29) and t1u PROTOCOL L41 in F21 and F24. The text needs no change. |
| R3-B3 | **F73** (P1), STORY L1592; also Appendix B L2289 | **Wrong time; the source's own ledgers contradict it.** F73 says Track C "ran only 10-05 14:18 to ~15:05", and Appendix B says "stage 1 had run 14:18–15:05 on 10-05". Track C's ledgers keep writing until **15:25:55**: 72 label rows after 15:06, and 462 proxy-ledger rows after 15:06 (last at 15:18:51). The source's log is internally inconsistent: it says "~15:05 the session ended. By then: … PM (336 rows) done", but the PM rows are timestamped 15:16:53–15:18:51. The conclusion is unaffected: Track C stopped long before the H3′ test ended (17:41) and stayed idle until 10-16. This is the same kind of error as R2-B6: a source statement that the source's own data contradicts. | `changes/2_deployable_peak/wp8_trackC/results/ledger_labels.csv` (10-05 rows 14:32:49–15:25:55; the last is `Region6_s0.3_STU10R2_s3`, a table row); `changes/2_deployable_peak/wp8_trackC/results/proxy_ledger.csv` (10-05 rows 14:46:22–15:18:51); `changes/2_deployable_peak/wp8_trackC/PROGRESS.md:82` | Write "ran 10-05 14:18 to ~15:26 (last ledger row; its log says the session ended ~15:05)". Make the matching change in Appendix B L2289, and note that stage 1 resumed and finished on 10-16 (N41). F44 L1076 ("session was down from ~15:05") may stay as the source's wording, with the ledger time added. |
| R3-B4 | **F100** (P3), STORY L1782–1784 | **Claim contradicted by tracked files.** F100 says "No objective comparison is recorded for the WP3/WP9 shared-core label solves" and "**The main non-optimal 10 s comparison is Track C's anchored energy**". In fact WP3's 72 tracked label JSONs record the objective of every PT and CP-SAT solve, and CP-SAT is lower on 36/36 pairs (R3-B1). These were test-label solves run with `taskset -c 0-23` while `TIMING_IDLE` existed. So WP3 is a non-optimal shared-core comparison with a deployed outcome attached. The "no comparison" claim is true only for WP9, which had no CP-SAT twin. | `changes/2_deployable_peak/wp3_test/labels/*_F1PT_s*.json` and `*_F1CPSAT_s*.json` (72 files tracked); `changes/2_deployable_peak/wp3_test/trials.csv` (`label_peak_day1`); `changes/2_deployable_peak/wp3_test/PROGRESS.md:63-65,78` (`taskset -c 0-23`; "16:26–16:40 label sets: 72 (F1PT/F1CPSAT × seeds 1-6)") | Report the WP3 comparison (CP-SAT lower on 36/36, 0.2–0.9%) as a non-optimal shared-core comparison next to Track C, and drop "main". Restrict "no comparison recorded" to WP9. |
| R3-B5 | **F103** (P2), STORY L559–565 | **Wrong claim, contradicted by the cited source.** The title says these levers "were never implemented", and the body says "no later work package implemented them". Two bullets break that. (a) Candidate 3's occupancy model **was implemented** in harness_eval itself; it is the C3/C3L arm reported in F15 and F16. Only the team's confirmation was missing. (b) "Samples 1–9 were not run" was true of harness_eval only; Q1–Q3 later ran s0.1–0.3 and WP1 ran s0–0.9. | `changes/1_literature_review/harness_eval/RESULTS.md:270` ("Items that need a team decision (not implemented)") vs L275 ("Candidate 3's occupancy model **was implemented** purely in-module … The team should still confirm that reading"); `changes/2_deployable_peak/wp1_offline/RESULTS.md:19` (samples 0–0.9); `changes/1_literature_review/explore/q2/RESULTS.md:58` (held-out s0.1–0.3) | Retitle as "…flagged for a team decision were never adopted or confirmed". Reword the C3 bullet: "implemented in harness_eval (C3/C3L, F16) but never confirmed by the team". Scope the samples bullet: "harness_eval's arm set was not run on samples 1–9 (later campaigns ran s0.1–0.9 with other arms; F18, F25)". |
| R3-B6 | **Header** STORY L10 | **Wrong number.** The header says "the writer redacted one absolute scratchpad path". The redacted line held **two** paths, both replaced by `<tmp file>`. | `git diff f387db9 04c873f -- changes/4_story/result/validator_citation_round_1.md`: one changed line, "Script: `<tmp file>` and `<tmp file>`" | Write "two absolute scratchpad paths (one line)". |

## Non-blocking problems (fix recommended)

| # | Finding | Issue | Evidence (file:line) | Suggested fix |
|---|---|---|---|---|
| N1 | F04 L284 | "bit-identical on all 425 result keys" (G1_v4/v5) leaves out the keys the G1 code skips. This is round-2 N4's caveat, now for F04. | `changes/2_deployable_peak/wp10_schedule/src/g1v3.py:38` (`SKIP_RESULT_KEYS`); `changes/3_autoresearch/work/cls_table/src/g1v4.py:39` | Add "(excluding wall-clock/RAM keys and realtime series)". |
| N2 | F04 L287 | "No teammate review was required": the most direct source for v4/v5 is not cited. | `changes/3_autoresearch/documents/GOOD_RESULT.md:13` | Optionally cite it. |
| N3 | F104 L321, L323; abstract L34 | (a) In the audit, load-adaptive *admission-threshold* modulation appears only in the hypothesis sentence and the top-8 table; mechanism step (ii) is the ML-When prefetch gate. (b) The audit itself cites Baleen §5.6's failed high-load admission, which the "scoop check" bullet does not say. | `lit_review/papers/fast24-baleen-ml-admission-and-prefetching-for/audit/report.md:213,223-226,231-233` | State both points. |
| N4 | F104 L329 | The ledger evidence for "empty `pf_subset`" cites only WP3. WP10, T1 and T2 have no `pf_subset` column; their drivers hard-code `pf_subset=None`. | `changes/2_deployable_peak/wp10_schedule/src/wp10.py:69`; `changes/3_autoresearch/work/union/src/cls.py:77`; `changes/2_deployable_peak/wp9_region5/trials.csv` | Add these refs. |
| N5 | F104 L328, L331 | The direct ancestor is not shown. SCOPE_v2 credits items 1.2/1.3 to the proposal, which puts the threshold modulation next to its QUBO plan. | `changes/SCOPE_v2.md:8`; `documents/proposal_docx_compose/proposal.js:245` | State the chain audit → proposal → SCOPE_v2. |
| N6 | F13 L481, L488, L494 | "F1 over the post-day-1 windows … 8 nested levels" holds for offline instances only. The F1-label arms solve over the 145 day-1 windows at a single level, f = 1.0. | `changes/2_deployable_peak/wp2_deployed/PROTOCOL_v2_H3.md:69-70`; `changes/1_literature_review/harness_eval/RESULTS.md:31` | Add "(labels: day-1 windows, f = 1.0)". |
| N7 | F15 L516, F17 L553, F19 L592 | "Classical 27.6–28.3" leaves out R1_L6 on Region6 (27.53). Inherited from the source's summary line. | `changes/1_literature_review/harness_eval/RESULTS.md:4,148` | "27.5–28.3". |
| N8 | F16 L536–537 | 288 → 660, 361 → 154 and the 3.3–4.6-point excess are for R1 (LP) only. | `changes/1_literature_review/harness_eval/RESULTS.md:105-108` | Add "for R1 (LP)". |
| N9 | Legend L58 | The list of TEST-POSTHOC "pre-declared, no pass/fail" findings leaves out F102. | STORY L137 | Add F102. |
| N10 | F24 L674 | The 99.40% share's denominator *includes* the ~200k LP-start operations, so "After the start … the rest were shared-repair operations" misplaces them. PT 10 s: sampler 37,331,820, start 223,923, final repair 235. | `changes/1_literature_review/explore/q2/RESULTS.md:254-257`; `explore/q2/trials.csv` (`moves`) | "99.40–99.9994% of accepted moves including the LP-rounding start; the rest are start operations plus < 1k final repairs". |
| N11 | F24 tag vs F102 tag | F24 (held-out solver objectives, post-hoc decomposition) is tagged OFFLINE. F102 (the same kind of data on H2′ test instances) was retagged TEST-POSTHOC. The legend gives no precedence between OFFLINE and TEST-POSTHOC. | STORY L57–60 | Add a one-line precedence rule to the legend, or retag one of them. |
| N12 | F31 title L822; L838 | Round-2 N8 is only partly fixed. "in at most 214 MB" and "stays under 165 MB" are *extra* memory above the loaded instance; the body explains this, the title does not. | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md:343,392` | "+214 MB above the loaded instance"; "+165 MB at most". |
| N13 | F27 L730–733 | (a) For CP-SAT and PT on Region4 s0.8, the simulated window (455) is within ±10 min of the planned one (454), so by F26's rule the peak did not migrate. Migration holds for LP s0.8 and CP-SAT s0.9. (b) "Win a few points" understates Region4 wins of up to 14.1%. Inherited. | `changes/2_deployable_peak/wp1_offline/RESULTS.md:96-100`; `wp1_table.csv` (`*_argmax`, `*_plan_argmax`) | Qualify both points, or mark them as the source's reading. |
| N14 | F25 title, index L92 and L132 | "beats … by −13.0% to −13.7%" is a double negative. | — | "by 13.0–13.7% on average". |
| N15 | F28 title | "better only at 3 s" holds for PT. EIM at 3 s meets the count rule (5/6) but not the mean (22.7158 vs 22.7157). | `changes/2_deployable_peak/wp5_ising/RESULTS_test.md:13,32,39` | "PT better only at 3 s". |
| N16 | F28 L763 | The first h2test ledger row is 01:24:28; the source says 01:24:38. Conclusion unaffected. | `changes/2_deployable_peak/wp5_ising/trials.csv` (phase `h2test`) | Optional. |
| N17 | F29 L781 | "8 tunable solvers" is outside the cited anchors. | `changes/2_deployable_peak/wp5_ising/RESULTS_dev.md:395` | Add `#L395`. |
| N18 | F21 refs | `harness_eval/RESULTS.md#L42` is cited twice. | STORY L639 | Drop the duplicate. |
| N19 | §5 intro L876 | "every configuration gets ≥ 3 retrains": the WP2 screens and all Track C configurations had 1 retrain. | `changes/2_deployable_peak/wp2_deployed/RESULTS_dev.md:129-133`; `changes/2_deployable_peak/wp8_trackC/RESULTS_dev.md:45` | "every tested or finalist configuration; dev screens use 1". |
| N20 | F44 L1076 | (a) "Evaluated on 2026-10-16" rests on the `evaluation.json` mtime; F73 says so, F44 does not. (b) "Track C's processes never read WP3 output" is Track C's own statement, which F73 calls "a statement, not a mechanism". | `changes/4_story/result/untracked_evidence.txt:11`; `changes/2_deployable_peak/wp8_trackC/PROGRESS.md:109` | Add "(mtime)" and "per Track C's log". |
| N21 | F44 L1075 | Ledger `ts` values are completion times. The test launched at 14:13:16: the earliest `ts − wall_secs` (and the first job log) falls 15 s after the G3 commit. | `changes/2_deployable_peak/wp3_test/trials.csv`; `untracked_evidence.txt` | Optional: "launched 14:13; rows 14:23:12–17:41:42". |
| N22 | F34 L916, F37 L956, F42 L1038 | Inherited rounding. Baleen control 40.18 vs raw 40.1749 (the source prints both 40.17 and 40.18). P0 ±0.005 vs raw net_se 0.00446. "16–30%" vs Region7 ledger means of 20.2–29.7%. | `explore/q3/RESULTS.md:142,252`; `wp2_deployed/results/learnability_summary.csv`; `wp2_deployed/results/mechanism_by_region.txt:26-27` | Optional. |
| N23 | F40 priority line | It gives only the instance-level reading. F70 lists the same row at 2.7 retrain-level SE. | STORY F70 table | Optional: add "(2.7 retrain SE)". |
| N24 | F52 title, L1193 | The 69% share and the other five's +0.43 are post-hoc decompositions, shown under a TEST-PREREG tag without a marker. F53 L1219 marks them; F52 does not. Round-2 N13 was fixed in F53 only. | `changes/2_deployable_peak/wp9_region5/RESULTS_test.md:17` (no 69%); `recompute_out.txt` | Add "(post hoc)". |
| N25 | Abstract L36, F52, F53, F69, §8 row 15 | "+1.16" is the report's rounding; the raw value 1.1546 rounds to 1.15. Appendix D's "Agreement" lists WP9's other rounding exceptions but not this one. | `wp9_region5/RESULTS_test.md:11`; `wp9_region5/results/evaluation.json` (`mean_improvement` 1.15458); `recompute_out.txt` ("+1.155") | Add it to the listed exceptions, or write +1.15. |
| N26 | F57 L1285 | The raw dev exhaustive enumeration takes 1.50–2.41 s (9/48 solves above 2.35 s). "1.5–2.3 s" is inherited from PROGRESS L83. | `changes/2_deployable_peak/wp10_schedule/results/solves_dev.csv` (`solver=ex`, `wall_s`) | "1.5–2.4 s". |
| N27 | F59 L1318, L1323 | The bullet is labelled "raw `solves_test.csv`" but quotes the dev enumeration time. On the 18 test fits the exhaustive solve took 0.69–0.88 s. | `changes/2_deployable_peak/wp10_schedule/results/solves_test.csv` (`solver=ex`, `wall_s`) | "1.5–2.4 s on dev (F57), 0.7–0.9 s on the test fits". |
| N28 | F59 L1318 | "i.e. plain arm B" is right about the models and policy. TB:pt's P100 equals B's same-retrain value on 9/10 neutral retrains; Region1_s0.5 r2 gives 23.062 vs 22.750, because θ converged separately. | `changes/2_deployable_peak/wp10_schedule/trials_test.csv` | Optional precision. |
| N29 | F61 L1354 | "only the sub-processes it launched were [sandboxed]" overstates. Only the Baleen/solver launches went through `sbx.sh`; the worker's read-only analysis scripts ran unsandboxed. | `changes/3_autoresearch/result/validator_integrity_stats_round_2.md:47` | Say so. |
| N30 | F73 table, H1′ row L1579 | "WP1 solves from 2026-10-01" covers only the new solves. 6 of the 39 instances reuse the phase-1 Q2 held-out solves from 09-28/29. | `changes/2_deployable_peak/wp1_offline/trials.csv` (phase `wp1_reused_phase1_heldout`, 18 rows); `wp1_offline/RESULTS.md:30` | Add this caveat. |
| N31 | F70 L1503, F100 L1785 | The text implies only the CP-SAT side was contended. The PT side (ANC10, 10-05 14:40–14:44) ran while the H3′ test simulations were running (14:13–17:41). | `wp3_test/trials.csv`; `wp8_trackC/PROGRESS.md:14` | Add one clause. |
| N32 | F100 L1770 | "WP2's label solves ran earlier, before H2′" holds for the 144 main sets. Three seed-4 sets were solved 10-04 05:19, with `TIMING_IDLE` present. None is in a PT/CP-SAT comparison. | `changes/2_deployable_peak/wp2_deployed/PROGRESS.md:85`; label file mtimes | "WP2's 144 main label sets". |
| N33 | F76 L1686 | "no human review" is stated as fact; the sources show only that none is recorded. | `wp10_schedule/SCOPE_v2_1b.md:15`; `3_autoresearch/work/union/SCOPE_AMENDMENT.md:28-31` | "no recorded review". |
| N34 | F70 table | The table is called "the full record" but leaves out the union XG:F1PT vs XG:F1CPSAT row: 6/10, +0.44, SE 0.28 / 0.22, i.e. 1.58 retrain-level and **1.97 instance-level** SE, favouring PT. | `changes/3_autoresearch/result/FINAL_REPORT.md:86`; `recompute_out.txt` ("Union dev: XG-F1CPSAT vs XG-F1PT") | Add the row, or say "XA only". |
| N35 | F74 L1626 | "written … before any test data" is inherited from the source. WP3's static RejectX/CoinFlip replays on the test instances (16:24–16:36) preceded the evaluator (16:50); they equal the authors' published values. | `changes/2_deployable_peak/wp3_test/PROGRESS.md:74-79` | "before any test-arm data". |
| N36 | F92 L1946, F93 L1967 | "Regions 4–7 × samples 0–0.9" overstates: there are 39 instances, because Region4 s0.1 has no OPT-AP row. | `changes/2_deployable_peak/wp1_offline/RESULTS.md:19-20` | "39 instances". |
| N37 | §8 row 23 | "The F1 objectives tie where compared" is too strong. On dev Region5_s0 they differ by 0.16–0.31%, and on the H3′ test labels by 0.2–0.9% (R3-B1). | `changes/3_autoresearch/result/FINAL_REPORT.md:78` | Align with R3-B1. |
| N38 | §8 row 19 | "the analytic ≥ 3% … holds on dev for every solver" is true only for F1; on F2b no solver beat the peak-aware greedy by more than 0.15%. The simulated comparator is the F2b peak-aware greedy. | `changes/1_literature_review/explore/q2/RESULTS.md:145-147`; `explore/q2/PROGRESS.md:50` | "on F1"; name F2b for the greedy. |
| N39 | §8 row 18 | The operating-point caveat is missing: the proposal's H1 assumes 400 GB at 3 DWPD, while every result uses 366.475 GB at 7.5 DWPD. | `documents/proposal_docx_compose/proposal.js:199`; STORY F10 | Add "(at the artifact's operating point; F10)". |
| N40 | §8 row 1 | "sample 0 of two traces only" leaves out the Region1 smoke test that F98 includes. | `changes/0_reproduce/RESULTS.md:55-57` | Add it. |
| N41 | Appendix B L2289 | "stage 1 had run 14:18–15:05": stage 1 also resumed on 10-16 (proxy validation, learnability, ANC10CP solves). See R3-B3 for the time. | `changes/2_deployable_peak/wp8_trackC/PROGRESS.md:86-98` | "began 14:18, paused; resumed and finished 10-16". |
| N42 | Appendix A.8b | Five of the 14 designs are left out without a note: F1PT4, ANC10TK10, STU10R2, STU30R1, ANC10CP. | `changes/2_deployable_peak/wp8_trackC/results/stage1_table.md:16,22,24-26` | Add a note, as A.5 does. |
| N43 | Appendix C L2328 | The "overlay copy" in `union_t2/` is git-ignored; git tracks only the v4/v5 diffs. | `changes/3_autoresearch/.gitignore:17` | Say so. |
| N44 | Appendix D items 1 and 2 | (a) Item 1's "Raw inputs" list leaves out four files `recompute.py` reads: `union/trials_dev.csv`, `wp10_schedule/results/solves_test.csv`, `wp8_trackC/results/ledger_labels.csv` and `wp0_overlay/PATCH.diff`. (b) Re-running item 2 now adds the round-2 commit `04c873f`, so the committed `git_timeline.txt` is a snapshot that lags by one round. | `changes/4_story/code/recompute.py:138,153,161,268` | Add the four files, and note that the timeline is a snapshot. |
| N45 | F32 title | "the deployed F1 label sets of PT and CP-SAT have the same day-1 peak" holds for the WP2 dev seed-1 sets, which is how the body scopes it. On the H3′ test sets CP-SAT is lower on 36/36 (S10). | STORY F32 L863; `wp3_test/labels/*.json` | Scope the title to "on WP2 dev". |
| N46 | Story-wide | `changes/4_story/result/untracked_evidence.txt` is cited but is still untracked (`??`). It is not git-ignored, so the launcher's `git add changes/4_story` will commit it. | `git status --short`; `changes/4_story/autoscript/run_story.sh:70` | No action needed while the launcher keeps `git add changes/4_story`. |

## Checked and found correct (no problem)

- **P0 findings:** F18, F20, F25, F28, F33, F44, F52, F59 and F65. Their numbers, verdicts, tags and pre-registration times are correct. The only open items are the title wording in N14, N15 and N24.
- **P1 findings correct apart from the items above:**
  - F01, F02, F03, F07, F08, F11, F13 (N6), F15 (N7) and F19 (N7);
  - F21 and F24 (refs only, R3-B2), F26, F27 (N13) and F31 (N12);
  - F34–F39, F41, F45–F47 and F50;
  - F53, F54, F57 (N26), F60, F64, F66 and F67;
  - F68, F69, F71, F75, F76 (N33), F84, F92–F95.
  - **Exceptions:** F70 and F73, whose blocking items are R3-B1 and R3-B3.
- **P2/P3 findings:** F04, F05, F06, F09, F10, F12, F14, F16, F17, F22, F23, F29, F30, F32, F40, F42, F43, F48, F49, F51, F55, F56, F58, F61–F63, F72, F96, F97, F98, F101, F102 and F104 are correct apart from the N items. F74, F77–F82, F85, F86, F88–F91 and F99 were checked for numbers and dates, and all match.
- **Timing.** Every protocol commit precedes its test, checked against the earliest test start (`ts − wall_secs`):

  | Test | Protocol commit | Earliest test start |
  |---|---|---|
  | H4 | 21:30:11 | 21:30:16 |
  | H3′ | 10-04 09:16 | 10-05 14:13:16 |
  | H5 | 19:23:04 | 19:23:09 |
  | T1 | 04:36:45 | 06:26:49 |
  | T2 | 05:19:24 | 07:05:03 |
  | H2′ | 01:13:51 | 01:24:28 (first row) |

- **Appendix B:** all 32 commit hashes and times match `git show`.
- **Appendix D items 3–10** give the stated output. Item 7 gives `2026-10-05T14:23:12 2026-10-05T17:41:42 126`; item 10 gives `2264e66 2026-09-14 10:53:49` and `527f8bc 2026-09-26 14:02:59`.
- **Contradictions with RESEARCH.md.** I found none that are silent. The known drifts (≈11.3%, ≈70k, "reserve untouched") are flagged in F08, F31 and F92.

## Spot checks (my own recomputation from the raw files; matched rows only)

My scripts are independent of `recompute.py`.
- A configuration's mean is the mean over instances of the per-instance retrain means.
- SE_inst = sd(d_i)/√n.
- SE_retrain = √(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i)/n.

| # | Story claim | Raw source | Recomputed | Verdict |
|---|---|---|---|---|
| S1 | F59: TB:pt 24.45 vs A 24.14, 1/6, −0.314 (≈2.2 instance SE, ≈3.4 retrain SE) | `changes/2_deployable_peak/wp10_schedule/trials_test.csv` | 24.4523 vs 24.1378, 1/6, −0.3145, SE_inst 0.1417 (2.22), SE_ret 0.0918 (3.43); TB:cd identical | match |
| S2 | Abstract, F60: A+α 1/6, −0.49 (≈2.7 / ≈7.9 SE); B+α 1/6, −0.338 | same | A+α 24.6243, 1/6, −0.4865, 0.1787 / 0.0612 (2.72 / 7.95); B+α 24.4761, 1/6, −0.3382 | match |
| S3 | Abstract, F59, §8 row 13: neutral on 10/18 test retrains; PT = exhaustive | `changes/2_deployable_peak/wp10_schedule/results/solves_test.csv` | 10/18 PT tables all 1.0 (s0.1 ×3, s0.2 ×2, s0.4 ×2, s0.5 ×3); PT = ex = CD tables and energies on 18/18; ex wall time 0.69–0.88 s | match (N27 on timing) |
| S4 | F44, F47: X1 40.53 vs A 39.27, 5/6; A+α vs A +0.96, 5/6 | `changes/2_deployable_peak/wp3_test/trials.csv` (126/126 matched) | X1 40.5318 vs A 39.2667, 5/6, −1.2651; A+α 38.3022, 5/6, +0.9645 (SE 0.160 / 0.391) | match |
| S5 | F65, F66, F70: Y vs A+α 1/5, −0.30, SE 1.117; A+α vs A 5/5, −15%, s0.3 69%; Y vs control +1.20, 2/5, SE 1.05 | `changes/3_autoresearch/work/t2u_region4/trials_test.csv` | 1/5, −0.3002, 1.1166; 5/5, +7.8474, −15.47%, s0.3 27.186 / 39.237 = 0.693; +1.1961, 2/5, 1.0475 | match |
| S6 | F70: union XA +0.77, 6/10, SE 0.36 / 0.42 (2.1 / 1.8) | `changes/3_autoresearch/work/union/trials_dev.csv` | +0.7681, 6/10, 0.3585 (2.14) / 0.4212 (1.82). XG: +0.4368, 6/10, 0.2765 (1.58) / 0.2213 (**1.97**), not in the table | match (N34) |
| S7 | F19, F25, F26: wins 36/36/37; 13.03/13.15/13.69%; Region4 4.6/3.0/5.4%; P99 8.6/9.2/9.2; top-5 10.8/11.2/11.3; PT − CP-SAT −0.18, 18/39; best of three 14.6%; window differs 30/34/33; plan coincides 6/9/6; plan gap 4.4–5.2 (−2.5 to +14.7) | `changes/2_deployable_peak/wp1_offline/results/wp1_table.csv` | 36/36/37; 13.03/13.15/13.69; 4.59/3.04/5.37; 8.61/9.19/9.24; 10.82/11.23/11.26; −0.184, 18; 14.59; 30/34/33; 6/9/6; 4.44/5.15/5.12, −2.45 to +14.67 | match |
| S8 | F52, F53: A+α vs A 5/6, +1.16, SE 0.09 / 0.75; vs B +1.35 (0.08 / 0.94); B+α 6/6, +1.70 / +1.89, instance SEs 1.19 / 1.40 | `changes/2_deployable_peak/wp9_region5/trials.csv` | +1.1546 (0.0938 / 0.7454); +1.3455 (0.0811 / 0.9433); +1.6959 (1.1944), +1.8868 (1.3953), both 6/6 | match (N25 on rounding) |
| S9 | F100: ANC10 finished 10-05 14:40:49–14:44:33, ANC10CP 10-16 13:36:49–13:41:20; F73: Track C ran only to ~15:05 | `changes/2_deployable_peak/wp8_trackC/results/ledger_labels.csv`, `results/proxy_ledger.csv` | 24 + 24 rows at exactly those times. Last 10-05 rows: 15:25:55 (labels) and 15:18:51 (proxy) | F100 times match; **F73 mismatch → R3-B3** |
| S10 | F70: "for the F1 rows the objectives tie"; F100: "no objective comparison recorded" for WP3 | `changes/2_deployable_peak/wp3_test/labels/*.json`, `changes/2_deployable_peak/wp2_deployed/labels/*.json` | WP3: CP-SAT lower on 36/36, by 0.040–0.198 (0.20–0.88%), means 21.057 vs 20.965. WP2: 10 / 10 / 4 ties, within ±0.57% | **mismatch → R3-B1, R3-B4** |
| S11 | F73: every protocol committed before its test | the five test ledgers (`ts − wall_secs`) and `git show` | see the timing table above | match |

## Counts

- **Findings audited:** all 104. 90 in full (P0 9/9, P1 44/44, P2/P3 37); 14 P2/P3 for numbers and dates.
- **Also audited:** the header, abstract, legend and index; §8 (23 rows and the summary) and §9; Appendix A (cell by cell), B (32/32 hashes), C (every path tracked) and D (items 3–10 re-run; `recompute.py` byte-identical).
- **`check_story.py` problems:** 0.
- **Recomputed numbers:** 11 spot checks (S1–S11). Nine match; S9 and S10 confirm R3-B3, R3-B1 and R3-B4.
- **Round-2 blocking items:** 6/6 fixed. R2-B1's new wording needs refs (R3-B2).
- **Blocking problems: 6.**

  | Kind | Count | Items |
  |---|---|---|
  | Wrong number or claim, or contradicted by its source | 5 | R3-B1 (F70), R3-B3 (F73), R3-B4 (F100), R3-B5 (F103), R3-B6 (header) |
  | Missing refs | 1 | R3-B2 (F21, F24) |
  | Wrong evidence tag | 0 | — |

  By priority:

  | Priority | Count | Items |
  |---|---|---|
  | P0 | 0 | — |
  | P1 | 3 | R3-B1 (F70), R3-B2 (F21, F24), R3-B3 (F73) |
  | P2 | 1 | R3-B5 (F103) |
  | P3 | 1 | R3-B4 (F100) |
  | Header | 1 | R3-B6 |

- **Non-blocking problems: 46** (N1–N46; N46 needs no action while the launcher stages `changes/4_story`).

```
OPEN_FINDINGS=6
VALIDATOR_STATUS=FAIL
```
