# Story writer notes

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
