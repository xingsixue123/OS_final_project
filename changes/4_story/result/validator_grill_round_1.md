# Validator 2 (grill: completeness, priorities, honesty), round 1 of 5

**Target:** `changes/4_story/STORY.md`, story-writer round 1 (run 20261020_154140, 92 findings).
**Run:** 2026-10-20. Read-only; this is the only file written.

## Method
1. **What I read.** The whole story, `RESEARCH.md`, `changes/4_story/result/WRITER_NOTES.md` and validator 1's round-1 report (`validator_citation_round_1.md`).
2. **The auto-research sources, read myself in full:**
   - `changes/3_autoresearch/result/`: FINAL_REPORT, LAB_NOTEBOOK, DEV_RULES, STATUS, LOOP_STATUS, STOP_EXHAUSTED, deterministic_validation.json, and all four validator reports;
   - the T1/T2 `RESULTS_test.md` and `PROTOCOL.md`, `GOOD_RESULT.md`, the README and `autoscript/run_auto.sh`.
3. **Two read-only sub-audits** walked every other source against the story:
   - phase 0/1: `0_reproduce`, `explore/PROTOCOL.md`, q2/q3 RESULTS + PROGRESS, harness_eval RESULTS + PROGRESS, the audit and the literature reviews;
   - phase 2: PLAN, CP1, G3_REVIEW, and every WP's RESULTS, PROTOCOL and PROGRESS, plus G1_v3 and SCOPE_v2_1b.

   I re-opened every item I promote to blocking below, and the evidence quoted is what I saw.
4. **Recomputation.** I recomputed the H4 and Region4 per-instance gains from the raw `trials*.csv` (matched rows; per-instance mean over retrains).
5. **Ledger-hypothesis check.** Every ledger hypothesis has a finding:
   - R: F07, F08;
   - Q1: F18; Q2: F20; Q3: F33;
   - H1′: F25; H2′: F28; S: F31;
   - H3′: F44, F45; H4: F52, F53; H5: F59;
   - the loop: F61–F67.

   So the gaps below are about what those findings leave out and how they are framed, not about missing verdicts.
6. **No duplication of validator 1.** I do not repeat its anchor and number items. Where one of its items also fails a grill criterion, I say so under "Endorsed from validator 1" and do not count it again.

## Blocking issues

### G1. Every "Ising" result is a hybrid started from the classical LP + round + repair solution, and the story never says so
**Evidence.**
- **Phase-1 finalists.** `changes/1_literature_review/explore/q2/RESULTS.md:165-167`:
  - "F1 + PT (replica exchange … 16 replicas, **LP start**)";
  - "F1 + EIM (… 16 replicas, **LP start**)".
- **The source's own attribution.** `q2/RESULTS.md:254-257` says the accepted moves came "after the LP-rounding start … Relative to that classical start (LP + round + repair, `lp` row: 23.04), the samplers contribute the whole improvement to 22.50-22.55".
- **How much the classical start already does.** `q2/RESULTS.md:204-211`: Baleen-order greedy 31.816 → LP + round + repair 23.039 → PT 22.524 (10 s, analytic). The classical start therefore delivers (31.816 − 23.039)/(31.816 − 22.524) ≈ 94% of the analytic reduction that the abstract credits to "Ising-selected episodes".
- **Phase 2.** `changes/2_deployable_peak/wp5_ising/PROTOCOL_v2_H2.md:58`: "Warm starts: both families choose from {LP rounding + repair, peak-aware greedy}".
- **The deployed labels.** The F1PT labels behind X1, X2, the union Y and WP1's PT are the same LP-started configuration. `changes/3_autoresearch/result/validator_integrity_stats_round_1.md:46`: "replica exchange on the QUBO-penalty energy … started from an LP solution".
- **How the story handles it:**
  - F21 claims to fix "what 'Ising' means in every result in this story" but never mentions the LP start.
  - F24 cites `q2/RESULTS.md#L254-L257`, drops the LP-start clause, and concludes that the arms "really were Ising-driven".
  - Abstract L11: "Ising-selected episodes beat Baleen's peak-blind oracle on 6/6".

**Why blocking (honesty, criterion 3).** A reader cannot tell that each Ising arm is a classical LP solution polished by a sampler. That changes how Q1, H1′, Q2, H2′ and every Ising-label deployment must be read.

**Fix.**
1. Add a "Solver names" bullet to the legend: PT/EIM = replica exchange on the LSE peak energy, started from LP + round + repair (H2′: the warm start is tuned over {LP + repair, pgreedy} for both families).
2. State in F21 and F24 that the sampler's contribution is 23.04 → 22.50–22.55 analytic, with ≈94% of the reduction from greedy already in the classical start.
3. Reword F24's priority line to "the improvement over the classical LP start came from the sampler".
4. Write "LP-started replica-exchange (Ising) selections" in the abstract, and say in F32/F39 that the deployed F1PT labels are LP-started.

### G2. The one deployed win (H4) is headlined as "confirmed" with none of its limiting caveats; the P0 finding defers all of them to a P1
**Evidence.**
- **The headline wording.**
  - Abstract L22: "first seen post hoc and then confirmed by pre-registration on a fresh region (H4, Region5: 35.02 vs 36.17, 5/6)".
  - §8 summary L1504: "The only confirmed deployed gain, −3.2% on Region5".
  - F52 (P0) only says "See F53 for the caveats"; F53 is P1.
- **The caveats, recomputed from `changes/2_deployable_peak/wp9_region5/trials.csv`:**
  - per-instance A − A+α = +0.607, −0.246, +0.251, +0.374, **+4.758** (s0.5) and +1.183;
  - s0.5 is 69% of the summed gain (6.927); the other five average **+0.43** (≈ −1.2%);
  - the mean +1.155 is 1.55 × the instance-level SE (0.745);
  - the rule passed only on the retrain-level SE (0.094), as `wp9_region5/RESULTS_test.md:15-17` and `PROTOCOL_v2_H4.md:59-60` state.
- **The same pattern in Region4 (F66, P1, "the strongest (post-hoc) support").** From `changes/3_autoresearch/work/t2u_region4/trials_test.csv`:
  - per-instance A − A+α = +9.49, **+27.19** (s0.3), +0.12, +0.44, +2.00;
  - s0.3 is 69% of the sum, and the other four average +3.01;
  - F66 gives the instance SE (5.125) but not the concentration.

**Why blocking (priorities and honesty, criteria 2–3).** The single positive deployed result is the story's headline, and in both places a reader would take away an effect larger and more uniform than the evidence shows.

**Fix.**
1. Put one clause in the abstract, in F52's body, in the §8 summary and in §8 row 15: "passes the pre-registered rule on the retrain-level SE; at instance level +1.16 ± 0.75 (≈1.5 SE), and s0.5 alone gives 4.76 of the 6.93 summed gain (+0.43 mean on the other five)".
2. Retitle F52 "H4 = YES (pre-registered, retrain-level SE; one instance carries 69%)", or keep the title and make the caveat its first line.
3. Add the s0.3 concentration to F66.

### G3. Two headline sentences read more favourably to Ising than the evidence
**Evidence.**
1. **The §8 paper summary (L1502).** It says "Ising/QUBO solvers match but do not beat classical solvers", but the pre-registered tests show the Ising finalists *losing*:
   - at 1 s: LS 22.83 vs PT 23.00 (`wp5_ising/RESULTS_test.md:29-39`);
   - at 60 s and 300 s: CP-SAT 22.418 and 22.313 vs PT 22.508 and 22.503 (`q2/RESULTS.md:204-207`);
   - in rolling windows: CP-SAT 26.440 vs PT 26.903, with PT ≤ the best classical on 0/6 (`wp5_ising/RESULTS_test.md:138-165`);
   - they lead only at 10 s (Q2) and 3 s (H2′). "Match" is true only for the exact ties (F70).
2. **The F65 title (P0).** It is the last decisive negative, yet it leads with "the Ising-label union beats Baleen by a wide margin". The source's own reading is that "its gain over Baleen on Region4 is the load-adaptive threshold's" (`t2u_region4/RESULTS_test.md:5`). Someone scanning the index of P0 titles sees a win.

**Fix.**
1. Summary: "Ising/QUBO solvers tie classical solvers where both reach the optimum, win only at one short budget per test (10 s; 3 s), and lose at 1 s, at 60/300 s and in rolling re-solves; no pre-registered solver test passed."
2. F65 title: "T2 (Region4) = FAIL: the Ising-label union does not beat the threshold arm A+α (1/5, −0.30); its gain over Baleen is the threshold's, so the loop ends NEGATIVE".

### G4. The Ising-vs-classical record for the deployed labels is incomplete, and what is shown is the favourable part
**Evidence.**
- **The label solver itself.** On WP5's day-1 (label-size) instances at 10 s, the classical solvers beat both Ising arms (`changes/2_deployable_peak/wp5_ising/RESULTS_dev.md:222-245`):

  | Solver | Family | Nested objective |
  |---|---|---|
  | CP-SAT | classical | 22.2579 |
  | LS | classical | 22.2677 |
  | EIM | Ising | 22.3257 |
  | PT | Ising | **22.6071** |

  - **PT, the solver of every deployed Ising label set, is the worst of the four.** Its 10-s configuration "is worse on day 1 than its 3-s one".
  - **LS gives the best offline simulated P100 on dev** (27.067; L210).
  - **F32 hides this.** It says only "WP5 recommended EIM: best Ising day-1 objective", which hides that the classical solvers were better.
- **The contract.** `GOOD_RESULT.md` (F61) requires "a classical-solver control reported".
- **T2.** The test reports Y vs control: 2/5 wins, +1.20, "carried by s0.2, where Y's r3 = 59.28 … Not significant, and not attributable to better optimization" (`t2u_region4/RESULTS_test.md:56`; `FINAL_REPORT.md:80`). F65 does not report this comparison; only the A.11 table shows the control's mean.
- **T1.** F64 omits that Y ≈ control (10.246 vs 10.246) (`t1u_region2/RESULTS_test.md`; `FINAL_REPORT.md:80`).
- **F70's "Deployed differences".** It lists "Auto-research dev: PT labels better by 0.77" without its qualifiers in `FINAL_REPORT.md:83-89`:
  - 6/10 wins, SE 0.36;
  - three high-variance instances carry it;
  - "about 2.1 SE, from one test of two label solvers";
  - "Neither CP-SAT union would qualify on dev".

  It omits the T2 test comparison entirely.
- **Region5.** H4 had no CP-SAT-label twin of X1 (`PROTOCOL_v2_H4.md` arms), which the story does not say.

**Why blocking (completeness and criterion 3).** Over all label comparisons, the PT-vs-CP-SAT record goes both ways:

| Comparison | Data | Who led | Margin |
|---|---|---|---|
| WP5 day-1 objective at 10 s | dev | CP-SAT | 22.26 vs 22.61 |
| WP2 | dev | PT | +1.26, 5/8 |
| H3′ | test | CP-SAT | 0.89, 3/6 |
| Track C | dev, one retrain | CP-SAT | — |
| Union | dev | PT | +0.77, 6/10 |
| T2 | test | PT | +1.20, 2/5, n.s. |
| T1 | test | tie | — |

None is significant at instance level, and the objectives tie. The story shows only the subset that reads as direction-specific.

**Fix.**
1. Add the control row to F65 (and to F64).
2. In F70, replace the two bullets with the full table above, giving wins, SE and dev/test for each row, stating "no pass/fail; none beyond ~2 SE; objectives tie", and noting that X1 had no CP-SAT twin on Region5.
3. In F32 (and in F70's "budget-dependent winners"), add the day-1 label-instance result: at 10 s, CP-SAT and LS were below EIM and PT, and PT was the worst of the four.

### G5. Prior art for both of the story's positive results is missing
**Evidence.** `changes/1_literature_review/lit_review_qubo/REPORT.md:82-88`:
- **Baleen itself.** Baleen's own §5.6 "admit only during high load" extension "did not reduce Peak DT".
- **Wong's thesis, threshold.** The thesis (CMU-CS-24-152) §7.4.1 load-dependent thresholds cut "Peak DT only 1.4% on Region3".
- **Wong's thesis, PeakOPT.** The thesis §7.4.2 fixed-window PeakOPT cut Peak DT 29% analytically but failed in simulation through peak migration.
- **Novelty status.** "first min-max peak-optimizing admission" is "~0% for 'first attempt'", and a novelty search "remain[s] outstanding before any novelty sentence is finalized".

**How the story handles it.**
- `grep -n -i "thesis\|5\.6\|prior art\|novel" STORY.md` finds only F05's note that Wong's thesis method was excluded from the baselines.
- The deployed win (a load-adaptive admission threshold, F52 and F69) is a close relative of both load-based prior attempts, and its result differs from theirs.
- The offline win (F25) is exactly the step the thesis says failed in simulation. That point *helps* the story, and it is absent too.

**Why blocking (completeness, criterion 1).** §8 offers a "one-sentence summary for a paper". A PC member's first question about a load-adaptive threshold is "how does this differ from Baleen §5.6 and the thesis §7.4.1?", and the record has no answer.

**Fix.**
1. Add a finding (P1, INFRA or OFFLINE) "Prior art and novelty", citing `lit_review_qubo/REPORT.md:82-88`, and say how A+α differs from the two prior load-based attempts:
   - α scales Baleen's own threshold continuously with trailing demand load;
   - its effect is measured on P100 at a matched write rate.
2. Explain why the outcomes may differ, or state that the comparison is open. Note that the thesis's PeakOPT failed in simulation where the all-window min–max succeeded.
3. Add "novelty search outstanding" to §9.
4. Qualify §8 row 15 and the summary accordingly.

### G6. The privacy-redaction disclosure is incomplete: the redacted identifiers are still in the current public tree, not only in git history
**Evidence.**
- The tracked file `tools/privacy_scrub.py` holds the redacted identifiers as regex literals: `NAME_SUBS` has 5 patterns, and `SENSITIVE` has 22 word tokens.
- Its `SKIP_PREFIXES` includes the file itself, so `python3 tools/privacy_scrub.py --check` prints nothing while the tree still exposes them. I checked this with `ast` and printed no literal.
- F87 says the names "were replaced by category labels" and that "**Earlier commits** still contain the originals. Purging them needs a history rewrite". A reader, and the captain who must make that decision (§9 item 7), would conclude that the current tree is clean and that a history rewrite is sufficient. Neither is true.
- Validator 1 raised this as non-blocking N27. I make it blocking: it is an active disclosure gap in the story's integrity section on a public repo, and it bears directly on a decision the story assigns to the captain.

**Fix.**
1. Add to F87, **without repeating any identifier**: "The tracked `tools/privacy_scrub.py` itself contains the redacted patterns as literals and excludes itself from `--check`, so the public tree still exposes them; a history rewrite alone does not remove them."
2. Add the same point to §9 item 7.
3. The story must not quote the patterns.

### G7. Undisclosed: the unattended auto-research worker ran with permission checks disabled
**Evidence.**
- `changes/3_autoresearch/README.md:5`: "permissions skipped by the captain's instruction".
- `changes/3_autoresearch/autoscript/run_auto.sh:3` and `:39`: `--dangerously-skip-permissions`.
- `grep -n -i "permission\|skip" STORY.md` finds nothing. F61 says only "A headless Opus 5.5 worker".
- **Mitigations the sources record**, which belong next to the disclosure:
  - the repo-wide `find -newer .leak_marker` scans found nothing outside scope (`validator_integrity_stats_round_1.md:31`; round 2 §1);
  - all 1,529 sub-process logs ran under `taskset … bwrap` with a private /tmp (round 2 §1);
  - no subagents were used.

**Why blocking (criterion 4).** This is a deviation from the project's sandbox discipline, which F77 and §7 present as the rule. The worker process itself was unsandboxed and unrestricted. Anyone weighing the loop's credibility needs to know this.

**Fix.** Add it to F61 or F84 together with the mitigations above.

### G8. A teammate cannot reach the source of a number in one click
**Evidence.**
- **No working links.** `grep -c '](' STORY.md` = 0 and `grep -c '<a id' STORY.md` = 0. All 92 `Refs:` lines are code spans, so they are not links, and neither are the index IDs, the (Fxx) cross-references or the timeline's "Record" column.
- **§8 "Main refs" are file-level only.** There are no `#L` anchors, and three cells say "same", "see F69" or "see F70".
- **The Appendix C file map omits whole source classes the grill brief names:**
  - every `PROGRESS.md`, which is where the rule timestamps and incidents live (q2, q3, harness_eval, WP0/1/2/3/5/8/9/10);
  - the three auto-research `PROTOCOL.md` files (T1, T2, void `t1_region2`) and the two scope amendments;
  - `G1_v4.md` / `G1_v5.md`;
  - the four auto-research validator reports;
  - `wp2_deployed/results/mechanism_by_region.txt` and `wp8_trackC/results/stage2_summary.md`.

**Why blocking (criterion 5, as specified).** The brief asks for one-click access. As written, every lookup is a copy, paste and scroll.

**Fix.**
1. Emit refs as markdown links, e.g. ``[`wp9_region5/RESULTS_test.md#L7-L19`](../../changes/2_deployable_peak/wp9_region5/RESULTS_test.md#L7-L19)``. That form is relative to `changes/4_story/` and resolves on GitHub and in IDEs; a root-relative `/changes/...` also works on GitHub.
2. Put an explicit `<a id="F18"></a>` before each finding header. Link the index IDs, every (Fxx) mention, §8's Findings column and Appendix B's Record column.
3. Give §8 "Main refs" line anchors.
4. Complete Appendix C with the files listed above.
5. Make `make_index.py` emit the links, and make `check_story.py` verify that every link target exists and every `#Lx-Ly` range is within the file.

### G9. The story never says that PLAN's pre-stated "Dev signal" gate failed, or that H3′ was re-specified around the α threshold instead of the pre-stated pivot
**Evidence.**
- **What the plan fixed in advance.**
  - `changes/2_deployable_peak/PLAN.md:57` makes D (Ising labels + `load`) "**the hypothesis**".
  - `:60` makes E (D + adaptive threshold) an "ablation".
  - `:107` gate: "Dev signal | arm D beats both A and B on the dev mean, beyond 2 SE | **report a negative H3′ with the mechanism, and pivot** the paper to a 'contemporary + analysis' framing".
- **D failed.** D:F1PT S = −0.142 (F38; `wp2_deployed/RESULTS_dev.md:16-19`).
- **What happened instead.** `wp2_deployed/PROGRESS.md` records the sequence:
  - **10-03 00:10 (L42-48):** the rep-1 D screen is logged (D:F1PT 37.99).
  - **00:20 (L64-76):** the finalist rule is written. It makes the E variants eligible: S over min(A, B), with a D2/E variant confirmed if its rep-1 screen beats D:F1PT's.
  - **01:35 (L78):** D:F1PT's confirmation fails (S = −0.14).
  - **02:15 (L79):** "queue extended by … **Ea-1.0:F1PT r1**". This is X1, queued *after* the hypothesis arm failed.
  - **10-04 05:25–06:50 (L81-93):** X1 is confirmed and becomes the H3′ primary.
- **The protocol records it.** `PROTOCOL_v2_H3.md:3` says the file "replaces the 2026-10-01 17:23 draft", and `:13` says "the only configurations that met the finalist rule are of PLAN arm type E … X1 therefore includes that threshold".
- **The story does not.** F38, F39 and F44 report the numbers but never name the gate, its failure, or the consequence that was not taken. F39's "a rule written before confirmation" is true but omits that the rule post-dates the screen and that X1 was queued after D failed.

**Why blocking (criteria 1 and 4).** This is a pre-registered decision gate that was not followed, and it is the fork at which the α threshold entered the project. That threshold later became the only deployed win (F47 → F52). A reader needs this to judge both H3′ and H4.

**Fix.**
1. Add a P1 INFRA finding in §7: "PLAN's dev-signal gate failed (D S = −0.14); instead of the pre-stated negative-and-pivot, H3′ was re-specified as labels + `load` + α (PLAN ablation E). The finalist rule was written after the rep-1 D screen, and X1 was queued after D's confirmation failed (refs above)."
2. Cross-reference it in F38, F39 and F44.
3. Add the 10-03 00:20 / 01:35 / 02:15 events to Appendix B.

## Endorsed from validator 1 (they also fail a grill criterion; not counted again)
- **B5 (F21 overclaim, honesty).** Harness_eval contradicts "weakest Ising arm"; C4 was the best Ising arm in simulation and in retention, as F71 itself says. The phase-1 sub-audit found this independently.
- **B6 (freshness, integrity).** Extend it beyond WP3:
  - WP1 also simulated offline Region5 s0.1–0.6 (the H4 pool; disclosed in `PROTOCOL_v2_H4.md:21`) and Region4 s0.2–0.6 (the T2 pool; `t2u_region4/PROTOCOL.md:54` cites WP1's Region4 headroom as a known caveat).
  - It also simulated the H2′ test instances before their protocol (`PLAN.md:116`: test samples "stay untouched until the pre-registration is committed").
  - State once, in F92 or a sibling finding, that "fresh" means "never run deployed", and list which test pools had offline OPT runs.
- **B8, B9 and N-TAG (evidence tags).** A tag for "pre-declared reported comparison, no pass/fail" is needed so that TEST-PREREG means pass/fail tests only.
- **B10 (F64 priority line contradicts its source).**
- **N3 and N4 (abstract wording).**

## Non-blocking suggestions
1. **H3′ run time is knowable.** The ledger `ts` column of `wp3_test/trials.csv` shows the test ran 2026-10-05 14:23:12 → 17:41:42. `results/evaluation.json` is dated 2026-10-16 12:33, so the outcome sat unevaluated for 11 days while Track C ran.
   - Put this in F44, F73 and Appendix B; it resolves WRITER_NOTES' open item.
   - Add Track C's "wp3_test was never read" statement (`wp8_trackC/PROGRESS.md:109-110`) as the firewall evidence.
2. **The go-files are untracked, and G3's encodes a waiver.**
   - `wp3_test/G3_SIGNED` contains "G3 waived by captain …" (mtime 10-05 14:13, 15 s after `84a0c1d`), not a sign-off, and is untracked. `TIMING_IDLE` is untracked too.
   - F74's "refused to start without `G3_SIGNED`" reads as if G3 was signed. Say what the file holds.
   - Add that G3 was a listed prerequisite in `PROTOCOL_v2_H3.md:125` and a WP0 exit criterion (`PLAN.md:41`).
3. **TIMING_IDLE stayed on after H2′.**
   - It was re-created at 02:08:54 (`wp5_ising/RESULTS_test.md:187-188`) and still exists.
   - So later 10-s solver comparisons (WP10 E2 PT vs CD; Track C PT vs CP-SAT; WP2 label solves) ran without core isolation, partly next to a foreign job holding about 15 CPUs (F81).
   - Add a timing caveat to F57 and F70.
4. **Post-data analysis or rule edits.**
   - **WP10.** `e3_eval.py` gained its tie-break after the confirmation data existed (`wp10_schedule/PROGRESS.md:109`; outcome unaffected) → F83.
   - **WP9.** The two-sided RejectX rule was written at 21:25, after the test-instance static replays at 20:29–21:00 had exposed the RejectX step (`wp9_region5/PROGRESS.md:67-70`) → F53.
   - **F74.** Soften "removes 'the analysis was tuned to the outcome' as an explanation for any test verdict".
5. **Phase-1 forking paths, all favouring Ising and all followed by a negative or replicated verdict.** Add these to F23, F33 and F75:
   - **Q2 formulation switch.** F2b was declared primary (`q2/PROGRESS.md:31-32`), then switched to F1 because Ising led there on dev (`:52-53`).
   - **Q3 finalist pool.** It grew after the 19:35 rule: P0 and C2 were queued after promising rep-1 values (`q3/PROGRESS.md:79-96`).
   - **Interim looks.** Q2 was decided after 4/6 instances (`q2/PROGRESS.md:95-99`), and Q3 was previewed at 27/54 (`q3/PROGRESS.md:129-130`). Disclose these as F86 does for the auto-research look.
6. **Omitted pre-declared secondaries.**
   - **WP1 P99 and top-5.** The P99 reduction is only 8.6–9.2%, below the 10% bar; top-5 is 10.8–11.3% (`wp1_offline/RESULTS.md:87-89`).
   - **H3′ and H4 P99/top-5.** X1's loss is a P100-only tail event: P99 31.82 vs A 31.96 (`wp3_test/RESULTS_test.md:65-73`).
   - **B+α instance-level SEs.** 1.19 and 1.40 (`wp9_region5/RESULTS_test.md:12`), so B+α also passes only at retrain level.
   - **H4's pre-stated transfer caveats.** Region5 uses a different Fig 9 variant, and its WP1 headroom is 3.3–5.9 points (`PROTOCOL_v2_H4.md:93,95`).
   - **WP10's report** omits several items its protocol listed as "Reported, no claim" (`PROTOCOL_v2_H5.md:62-66`): F vs A+α, P99, top-5, θ, admission statistics and the solver ledger.
   - **WP5's hl-split secondary** (`wp5_ising/RESULTS_dev.md:161-185`) is not reported.
   - **WP5's 3-s rolling classical arms** were added after the 1-s rolling result (`wp5_ising/PROGRESS.md:83-85`). F30's "on dev (at 1 s and 3 s)" should say so.
7. **F68's mechanism is not label-specific.**
   - The frozen trainer keeps only the first 15 accesses per episode, so big-offset scans are learned from a few mostly negative rows (`q3/RESULTS.md:32-33, 94-101`).
   - On dev Region6 it was *Baleen's own* model that missed the scan (`q3/RESULTS.md:298-299`; F41: A 9/12 scan peaks).
   - So F68 should say that the brittleness is in the GBM/trainer plus day-1 labels, not in min–max labels alone.
8. **F69 nuance (dev).** On dev Region1_s0, α helped: A 26.97 → A+α 26.23 over 3 retrains each (`3_autoresearch/work/cls_table/trials_dev.csv`; LAB_NOTEBOOK.md:167), unlike the Region1 test. This weakens the "low load → no benefit" reading; mention it as dev context.
9. **F31 and §8 row 8: what scaled, and what it is worth.**
   - The solver that scales (SB on the SoS surrogate) had the lowest solution quality of the four Ising solvers by the WP5 finalist rule (V −11.64%) and is in no finalist or deployed configuration.
   - Say so, so that "the one Ising contribution that stands" is not read as "Ising contributes scalability to PeakBaleen".
   - Likewise, F25 should say that PT's best mean reduction is not a solver advantage (F19: PT lower on only 18/39).
10. **Reproduction scope.**
    - It covers sample 0 of Regions 6/7 plus the Region1 smoke test. The plan itself calls Region6 at s0 "a weak test of the ordering" (`0_reproduce/REPRODUCE_PLAN.md:36`).
    - Stage B+ (the convergence loop from scratch, the Baleen no-prefetch ablation) was not run (`:55`).
    - Add this to F91 and §8 row 1. Also, `0_reproduce/RESULTS.md:70` points to a README list that does not exist.
11. **harness_eval deviations.** Add these to F15 or F82:
    - secant convergence instead of SCOPE.md's mandated `converge.py`;
    - `OMP_WAIT_POLICY=PASSIVE`;
    - C2 Region7 rep 2 was replaced by rep 4 (`harness_eval/PROGRESS.md:61-64`; `RESULTS.md:54,80`);
    - the only phase-1 deployed arm more than 2 SE below Baleen online was the *classical* R2 on Region6 (−0.87, `harness_eval/RESULTS.md:7`).
12. **Auto-research smaller items.**
    - The T2 chain-condition change (`3fdba1b`) was a post-commit procedure change made after T1 outcomes were seen. List it in F84 item 2, as F85 already describes it as a fix.
    - XG:F1PT also qualified, and the tie-break chose XA (F63).
    - Ledgers were rewritten in full, though losslessly (red-team round 1 N7).
13. **Plan deviations in instance coverage.** PLAN limited deployed runs to Regions 6/7, with Regions 4/5 "only if dev justifies" (`PLAN.md:27-31`). H4 (Region5) and H5 (Region1, never in the plan) each had their own protocol. Note them as deviations in the plan. Also, G1_v3 ran on one trace only (`G1_v3.md`), against CP1's two.
14. **Source conflict.** Sibling-load figures disagree: Ising 4.1 vs classical 3.9 (`wp5_ising/PROGRESS.md:71`) against 2.1 vs 1.8 (`RESULTS_dev.md:405`). F80 quotes only the latter.
15. **Abstract.**
    - Define "Ising solvers" as CPU replica-exchange samplers, LP-started (G1), with no GPU (F90).
    - Change "Their only use was WP1's offline H1′ breadth simulations": reserve dumps exist on disk (validator 1, N28), and the authors' published reserve-sample P100s feed `best_baleen_prefetch` (red-team round 1, N6).
16. **Priorities.**
    - Raise F75 to P1: it qualifies three P0 verdicts, including the headline positive Q1.
    - Make the new prior-art finding (G5) and the gate-deviation finding (G9) P1.
    - Turn the P0 list in §0.1 into a mini-table with verdict, key number and link, so that it is the "headline at a glance".
17. **Usability extras.**
    - Appendix B lacks the WP2 gate events (G9) and the H3′ run window (item 1).
    - §8's status vocabulary should be closed (validator 1, N29).

## Assessment against the five grill criteria
| Criterion | Verdict | Blocking items |
|---|---|---|
| 1. Completeness | Every ledger hypothesis has a finding. Gaps: prior art, the PLAN gate deviation, the classical-control and label-solver record, and several pre-declared secondaries | G4, G5, G9 |
| 2. Priorities | The P0 set is right (9 = Q1, Q2, H1′, H2′, Q3, H3′, H4, H5, T2), no DEV finding is P0, and the decisive negatives are P0. The P0 for H4 is stated without its caveats | G2 |
| 3. Honesty | Solver ties are plain in F70 and the abstract, and the threshold's region-by-region status (F69) is exact. But "Ising" is never disclosed as LP-started, the H4 and summary wording overstate, and the solver record is selective | G1, G2, G3, G4 |
| 4. Integrity disclosures | The 3_autoresearch timing items, the G3 waiver and the privacy redaction are present (F84, F86, F76, F87). Two gaps: the redaction is incomplete in the current tree, and the worker ran with permissions skipped | G6, G7 |
| 5. Usability | The index, claims table, timeline and file map exist, but nothing is clickable and the file map omits the progress logs and auto-research protocols | G8 |

OPEN_FINDINGS=9
VALIDATOR_STATUS=FAIL
