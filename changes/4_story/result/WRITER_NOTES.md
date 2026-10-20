# Story writer notes

## Round 3 (run 20261020_154140, started 2026-10-20 17:41)

### Validator feedback: how each blocking item was resolved
**Citation validator, round 2** (6 blocking):

| Item | Resolution |
|---|---|
| R2-B1 | The LP-start claim is scoped. The LP start applies to Q1/Q2, harness_eval C2 and every deployed F1PT/F1EIM label set. The Q3 PT started from Baleen's selection (`q3solve.py#L282-L286`). Track C's ANC started from Baleen's set and STU from the previous round (`labels_c.py#L1-L11`, `#L126-L131`). Fixed in F21, F14 and the legend. |
| R2-B2 | F31: harness C4 was deployed on dev only (harness RESULTS L197–198, L231–233, L250). |
| R2-B3 | §8 rows 8 and 19 reworded. |
| R2-B4 | F70: three rows exceed 2 retrain SE. The union row shows 0.36/0.42 SE (2.1/1.8) and is marked "run after the T2 outcome". §8 row 23 reworded. |
| R2-B5 | F95 cites `PROTOCOL_v2_H5.md#L24` and `3_autoresearch/README.md#L7` for Region3. |
| R2-B6 | F101: Region6 s0.9 carries the 4.81 gap (recomputed: largest \|d\| 4.814; Region4 s0.3 −4.014). |

**Grill validator, round 2** (4 blocking):

| Item | Resolution |
|---|---|
| 1 | F73's firewall timing is rewritten from wp8 PROGRESS L9, L82–86, L97, L105–110, PLAN_C L105–108 and `untracked_evidence.txt`. F44 and F50 edited; Appendix B rows added for the Track C gap and the H3′ evaluation. |
| 2 | F96's title, bullet and priority line name the Q1 forking path (q2 PROGRESS L50–53). F18 points to it. |
| 3 | H5's neutral tables: F59 gets a bullet and a new priority line (10/18 test retrains neutral; PT = exhaustive optimum on 18/18, recomputed). F57's timing, §8 row 13 and the abstract's H5 bullet updated. |
| 4 | §8 row 19 is now "Not supported / DEV" (`proposal.js#L199-L200`, q2 RESULTS L132–143, harness L128–137, q2 PROGRESS L50–51). |

### Non-blocking items
**Citation N1–N28** (N14, N18, N23–N26 were already done or needed nothing):
- N1: F03's `tod` sentence names D2 as the only deployed arm and cites the learnability gate and the WP0 parity test.
- N2: F13 says "held-out Q1/Q2".
- N3: F15 and F19 exclude C3/C3L (28.9–29.6).
- N4: F36 gives the exclusions (wall-clock/RAM, `realtime_elapsed`). It adds that CP1's +217/−6 equals the non-blank added lines, while all added lines give +256/−6 (recomputed).
- N5: F41: 2–3% (D:F1PT 2.4%, X1 2.8%) vs 8–10% (A 8.7%).
- N6: F44's title carries its numbers; F38 cites `PLAN.md#L107`.
- N7: F28's title says "fail the pre-registered criteria (better only at 3 s)".
- N8: F31: memory is extra above the loaded instance (~355–410 MB, WP5 RESULTS_dev L343).
- N9: F32's qualifiers (8-instance rows; seed-1 means rounded to 0.1).
- N10: F102 is retagged TEST-POSTHOC and cites `PROTOCOL_v2_H2.md#L79-L80`.
- N11: F24 notes that the `lp` row is a proxy for PT's start.
- N12: F35 gives both ranges, 18–42% (table) and 25–42% (text).
- N13: F53's decomposition is marked post hoc.
- N15: F60's title, the abstract and F59 say "worse than Baleen" (A+α 1/6, −0.49; TB:pt −0.314, ≈2.2 instance SE).
- N16: F67 is "the final report's interpretation".
- N17: F70 says "lower on only 11/24 cells", and its Data column carries evidence tags.
- N19: F68 cites `wp3_test/RESULTS_test.md#L26`.
- N20: F92 notes that RESEARCH.md L121/L124 also says "untouched".
- N21: F72's first-access sentence is rewritten from q3 RESULTS L25–28 and L244–250 and PROGRESS L99–101. The two q3 ranges (14–28% vs 15–28%) are both given. The suggested "mostly via zero-value positives" is too strong: T5c, with no zero-value additions, still reached 14.8%.
- N22: Appendix D documents the WP2 Ax/Bx/Ex merge and lists the round-3 additions.
- N27: G3_SIGNED and TIMING_IDLE are no longer linked. Their content and mtimes are in the new `result/untracked_evidence.txt` (Appendix D item 9; the command reproduces the file byte-identically).
- N28: `.git/objects` is no longer backticked.

**Grill non-blocking 1–9:**
1. The P0 titles carry key numbers: F20, F28, F33, F44, F59.
2. F76 and F04: the later overlays (PATCH_v3 = PATCH.diff + 43/−1, then v4 and v5) had only G1 gates. No teammate review was required or recorded, and H5 and both auto-research tests ran on them.
3. F65: the T2 prerequisites were built 04:57–05:04, before the 05:19 protocol commit. This is disclosed and unread (red-team round 2, L44).
4. Done in the blocking round.
5. The header names the story loop's own round-2 incidents.
6. The §8 summary says "fresh Region5 (fresh = never run deployed; prior load-based attempts: F95)".
7. Appendix C adds `work/union_t2/`, `code/validate.py` and the proposal slides PDF.
8. F84 item 1 adds the transcript confirmation. The transcript is untracked; the red-team round-1 report checked it (L24, L105–106).
9. F100: Track C's anchored-energy comparison is the main non-optimal 10 s comparison. Its PT side finished 2026-10-05 14:40–14:44, before the foreign job. Its CP-SAT side finished 2026-10-16 13:36–13:41, during it. This is recomputed from the Track C label ledger. F70's Track C row is corrected to match: the round-2 wording said both sides ran next to the foreign job.

### Other changes
- **New finding F104** (P2, INFRA). The founding 2026-09-14 paper audit already proposed "peak-aware episode scoring and load-adaptive gating", including the load-adaptive *admission threshold*. It targeted ≥ 5%, made no QUBO/Ising mention, and its scoop check was two queries. So the one deployed gain predates the Ising work. It is referenced from the abstract, from Appendix B (09-14) and from Appendix D item 10.
- **Other coverage:**
  - F54: Region5's F1PT labels did cut the day-1 label peak on every instance (`wp9_region5/INSTANCES.md`).
  - §9 items 7–8 gain two entries: the Track C re-solve and the review of PATCH_v3–v5.
  - Appendix C lists `wp9_region5/INSTANCES.md`.
- **`recompute.py`:**
  - Round-2 items are back under their heading (the round-3 heading had been printed above them).
  - New this round: the Track C ANC10/ANC10CP finish times, the `PATCH.diff` line counts, and the arithmetic on quoted values (§8 row 19's 1.38–1.96%; F96's 6.0–7.3 points).
  - The output is regenerated; only the additions and the order changed.
- **New file `result/untracked_evidence.txt`.**
- **Files outside 4_story.** These were already modified in the working tree before this story run and were not touched by the writer: `changes/3_autoresearch/result/LOOP_STATUS.txt` (mtime 11:44, STATUS=EXHAUSTED) and `deterministic_validation.json` (mtime 15:34).
- **Privacy.** `python3 -B tools/privacy_scrub.py --check` is clean; nothing was imported this round.

### Self-audit after the validator fixes
Two independent read-only fact-check agents checked every added line of this round's diff (about 175 claims). All their findings were applied.

**Blocking:**
- **F104.** The ranking table is from 09-26 (`527f8bc`). The 09-14 table is `documents/top_doable_papers_filtered.md#L72`.
- **F104 and F03.** The prefetch `load` gate was *not* part of X1. Every Ea row has an empty `pf_subset`; only WP2's Epf:F1PT dev screen used it.
- **F04.** The G1 gates also check that degenerate settings reproduce the α run. They do not review the new code.
- **F100.** "The *main* non-optimal comparison": the auto-research Region5_s0 dev solves also differ (0.16–0.31%), and the WP3/WP9 shared-core solves have no recorded objective comparison.

**Minor:**
- **F70:**
  - only WP2 X1 reaches ≈2.1 instance SE (title updated);
  - the union CP-SAT twin's retrain 1 on the 8 Region6/7 instances ran before T1;
  - the foreign-job CPU figure is dated 14:37.
- **§8 rows:**
  - row 8: "C4 beat C5 analytically";
  - row 19: 1.38–1.96% (recomputed) with the right harness anchor;
  - row 23: Track C's objectives do not tie.
- **F76:** "automated bit-exact gates, no human review", and wider anchors.
- **F96:** 6.0–7.3 points (recomputed); "unlikely to depend on it".
- **Wording:**
  - F31: five Ising solvers in phase-1 tuning; only SB/PT memory is extra memory;
  - F21 and the legend: C2's own start; WP2's D:P0/D:T2 reuse the Q3 PT start;
  - F95: the Region3 pool cites F61/F64/F65;
  - F104: "on Region1 (the H5 test pool) A+α was worse".
- **Refs added:**
  - F84: `3_autoresearch/.gitignore#L2` (the transcript is untracked);
  - F73: Track C PROGRESS L16–19;
  - F44: `untracked_evidence.txt` and PROGRESS L81–86;
  - F50: `git_timeline.txt`;
  - F24: `q2/trials.csv`.
- **Appendix D:** item 1's "Used by" list and item 9's list (adds F73) updated.

### Still open
- Anchors in rarely cited long files may still be off by a few lines.
- The validator reports printed absolute paths in round 1. If they do so again, the next round's privacy check will fail on committed files (see round 2).

## Round 2 (run 20261020_154140, started 2026-10-20 16:55)

### Validator feedback: how each blocking item was resolved
**Citation validator** (14 blocking):

| Item | Resolution |
|---|---|
| B1 | Abstract cites `explore/q3/RESULTS.md#L6-L15` for Q3. |
| B2 | Abstract cites WP3 L53–60, FINAL_REPORT L75 and WP10 L19, plus (F69). |
| B3 | F13 cites WP1, PROTOCOL_v2_H2 and PROTOCOL_v2_H3 for F1's use. |
| B4 | F21: SB's V = −11.64% is the *worst (highest)* V. |
| B5 | F21's title is scoped to phase-1 dev and WP5. The harness_eval exception is stated: C4 beat C5 analytically and was the best Ising arm in simulation and retention. |
| B6 | F44 now says "touched once in deployed mode". The new F93 lists every test pool WP1 simulated offline. F92 is updated too. |
| B7 | F48 (title and body) gives the per-instance differences, ≈1 instance SE, and Region7 s0.5 carrying the result. F40 and F70 are reworded. |
| B8 | F60 retagged TEST-POSTHOC; "in tension with" instead of "contradicts". |
| B9 | F71 retagged TEST-POSTHOC; "mean retention"; dev range −0.23 to +0.74; 60% shown to come from the proposal only. |
| B10 | F64's priority line follows the T1 report: unevaluable because of a design defect, and the descriptive numbers do not favour Y. |
| B11 | F72: ≤1.3% for the F1/Baleen-label WP2 arms and every Track C arm; P0 2.89% (max 5.61%) and T2 1.04%, recomputed. |
| B12 | F77 cites all 12 frozen-check sources and the 16:22 line. |
| B13 | F80: "same pinning; per-family sibling exposure not measured". WP5's unequal exposure is noted. |
| B14 | F89 cites LAB_NOTEBOOK L1–8. |

**Citation validator, non-blocking items** (N-TAG and N1–N33): all addressed.
- **Tags.** The legend now defines that pre-declared "reported, no pass/fail" comparisons are tagged TEST-POSTHOC. F30, F48, F54, F60 and F71 were retagged to match. `check_story.py`'s tag set is fixed, so a new tag was not possible.
- **Header.** It now says what the checker does *not* check.
- **Abstract.** It gives the 36–37/39 wins and the Q2 ref, and adds "or its pre-registered dev gate".
- **Anchors.** Fixed across F12, F14, F32, F49, F50, F52, F59, F63, F65, F70, F73 and F74.
- **Wording.** F11 (median; comparable at 1k), F26 (±10 min), F27 (03:20), F30 (LP row, seed 0, editor burst), F33 (T2 had 2 retrains), F35 (3/6), F37 (F1 labels), F46 (20/21 retrains; "diagnosis"), F54 (second loss on s0.6), F57 (46/48), F72 (2–3%), F73 (H1′ row), F79, F84, F86 and F90.
- **Other findings.** F87 privacy gap; F92 (planned use; dumps on disk); §8 statuses closed; §9 WP4 ref; A.1 and A.8 notes; Appendix B times; Appendix D grep and "to the source's rounding".

**Grill validator** (9 blocking):

| Item | Resolution |
|---|---|
| G1 | The legend's "Solver names" bullet says PT/EIM are LP-started CPU replica-exchange samplers. F24 (now P1) quantifies it: the LP start reaches 94.5% of the greedy→PT analytic reduction, recomputed from q2 §8.1. F21, F32, F39 and the abstract say "LP-started". |
| G2 | H4's caveat is in the abstract, in F52's title and first lines, in §8 row 15 and in the summary: instance level ≈1.5 SE, and s0.5 is 69% of the gain while the other five average +0.43. F66 adds Region4's s0.3 concentration (69%). |
| G3 | §8 summary rewritten (tie / win at one budget / lose elsewhere). F65 retitled "= FAIL …". |
| G4 | F70 now carries the full PT vs CP-SAT label-set table: dev and test, wins, SE, the T1 tie, the T2 control, and the fact that H4 had no twin. F32 adds the day-1 label-instance objectives, where CP-SAT and LS beat EIM and PT and PT was worst. F64 and F65 add the control rows. |
| G5 | New F95 covers prior art and novelty (Baleen §5.6, thesis §7.4.1/7.4.2/7.4.3, novelty table, outstanding search). The abstract, §8 row 15 and §9 item 3 reference it. |
| G6 | F87 says that the tracked scrub tool still contains the patterns and excludes itself from the check, without quoting any pattern. §9 item 8 repeats it. |
| G7 | F61 discloses that the worker ran with `--dangerously-skip-permissions`, together with the validators' mitigations (no out-of-scope files, 1,529 sandboxed sub-process logs, no subagents). The story's own loop is disclosed in the header. |
| G8 | Every ref is now a relative markdown link with its line anchor, and every finding has an `<a id>` anchor. All (Fxx) mentions, the index, §8 and Appendix B are linked. `make_index.py` emits a P0 headline table. `code/linkify.py` is new. `check_story.py` gained *stricter* checks: line anchors within the file, link targets exist, anchors exist. §8 "Main refs" have line anchors. Appendix C lists the progress logs, the auto-research protocols and amendments, G1_v4/v5 and the validator reports. |
| G9 | New F94 covers PLAN's dev-signal gate: it failed, its pivot was not taken, and the sequence was rep-1 screen 00:10, rule 00:20, D fails 01:35, X1 queued 02:15. It is cross-referenced from F38, F39 and F44, and the events are in Appendix B. |

**Grill non-blocking 1–17:** all addressed.
- The H3′ run window comes from the ledger's `ts` column (F44, F73, Appendix B; one-liner D.7).
- `G3_SIGNED` holds a waiver (F74, F76).
- `TIMING_IDLE` gets its own finding (F100).
- Post-data rule edits are covered in F53 (WP9's RejectX rule) and F83 (WP10's tie-break), and F74 is softened.
- Phase-1 forking paths and interim looks: F96.
- Omitted secondaries:
  - WP1 P99/top-5 in F25;
  - H3′ P99/top-5 in F44;
  - B+α instance SEs and transfer caveats in F53;
  - WP10's omitted reported items in F59;
  - the hl-split in F29;
  - the 3-s rolling arms added after the fact in F30.
- Mechanism and region notes:
  - the trainer nuance in F68;
  - dev Region1_s0 in F69;
  - the value of the SB scaling result in F31.
- New findings:
  - reproduction scope in F98;
  - harness_eval deviations in F99 (the classical R2 note is in F15);
  - plan coverage deviations in F97.
- Smaller items:
  - the sibling-load source conflict in F80;
  - the auto-research smaller items in F63 and F84.
- Priorities: F75 raised to P1, and the new F94/F95 are P1.

### Other changes
- **Recomputations.** `code/recompute.py` adds:
  - the LP-start share;
  - the H4 and Region4 concentration;
  - per-instance X1 − Dc+α;
  - Region7 s0.5 peak windows;
  - Region6 first-access admission by arm (WP2, Track C);
  - dev Region1_s0 means;
  - WP1 per-region means;
  - Region5 s0.6 peak windows.
- **New findings:** F93–F103 (11).
- **Privacy.**
  - The round-1 citation validator's report contained an absolute `/tmp` path of its own scratchpad. It was committed in round 1 and then failed `privacy_scrub.py --check`, because the check looks only at tracked files.
  - I redacted that one line in `result/validator_citation_round_1.md` with the repo's own `scrub_text`. The path became `<tmp file>`; nothing else changed.
  - **Launcher owner: validator reports that print absolute paths will keep tripping the next round's check.**
- **Incident (mine, disclosed here).** Importing `tools/privacy_scrub.py` to scrub that file created `tools/__pycache__/privacy_scrub.cpython-312.pyc` at 17:09. It is outside the write area and git-ignored. I deleted it immediately and `git status tools` is clean.

### Self-audit after the validator fixes
Three independent read-only fact-check agents audited every rewritten or new part. All their findings were applied. The main corrections:
- **F70:** "no row beyond ≈2 *instance-level* SE"; at retrain level, two rows exceed 2 SE, one each way (2.68, 2.50; recomputed). Both SE levels are shown, the Track C reverse case is stated, and the wrong anchor is fixed.
- **F48:** retrain SE 0.36 added; Region7 s0.5 = 4.81 of 5.33 summed (90%).
- **F32:** the day-1 objective table measures the WP5-tuned PT. The deployed phase-1 PT labels have the same day-1 peak as CP-SAT's (21.5), and the title is reworded.
- **F21, F24, legend:** in H2′ the finalists used the *greedy* start at 1 s and LP at 3/10 s.
- **Abstract:** the threshold was first seen as a WP2 dev control.
- **Header:** says what the checker does and does not check, and that "writes only in 4_story" is an instruction, not enforced.
- **F94:** the sequence is corrected (X1 named at 08:25, not 06:50; the gate failure is the story's reading once both D arms were negative). It also states that α was already allowed by scope v2 and PLAN, and that the fork made it part of the *tested hypothesis*.
- **F100:** WP2's label solves predate H2′.
- **§8:** rows 3, 8/22 (definition of Supported), 15, 19, 20 and 23 reworded; summary heading renamed.
- **§9 item 1** scoped to the offline-known pools.
- **Appendix B:** X1 timeline corrected.
- **Appendix D:** protocol file list written out, with `--all`.
- **Wording:** smaller fixes in F12, F15, F30, F49, F53, F57, F59, F63, F65, F72, F95 and F98.

`protocol_commits.txt` and `git_timeline.txt` were regenerated with `--all`; the content is identical apart from the header line and the newer story commit.

**Added for coverage:**
- F101 (WP1 R0 vs the authors' OPT rows);
- F102 (H2′ per-level mechanism);
- F103 (harness_eval's untried levers, including simulator-in-the-loop reweighting);
- appendix tables A.8b (Track C stage-1 designs), A.10b (WP10 E1 proxies) and A.10c (H-CLS screen).

Total 103 findings.

### Still open
- Rarely cited long files may still have a few anchors that are off by a few lines.
- Possible deepening:
  - per-design Track C stage-1 rows (F49 summarises them);
  - the WP10 E1 per-proxy table;
  - the H-CLS per-candidate dev rows.

## Round 1 (summary)
- Wrote the first STORY.md (92 findings) and the helper scripts (`recompute.py`, `make_index.py`, `renumber.py`), plus the git timeline files.
- Four fact-check agents audited round 1, and every correction was applied.
- Finding IDs were renumbered once in round 1, before any validator referenced them. They are stable from round 2 on: new findings are appended as F93+, and `renumber.py` must not be used again.
