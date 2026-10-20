# Story writer notes

## Round 1 (run 20261020_154140, started 2026-10-20 15:41)

### What was done
**Sources read:**
- `RESEARCH.md`, both SCOPE files and PLAN.md;
- the proposal text (`documents/proposal_docx_compose/proposal.js`) and the paper-selection report;
- the reproduction reports;
- the phase-1 lit reviews, the synthetic audit, harness_eval, Q2 and Q3;
- every phase-2 WP report, protocol and progress log (WP0, 1, 5, 2, 3, 8, 9, 10);
- the auto-research contract, dev rules, final report, T1/T2 reports, scope amendments, G1_v4/v5 and all four validator reports;
- `git log --all`.

**Wrote `changes/4_story/STORY.md`:**
- 92 findings: P0 9, P1 39, P2 29, P3 15.
- Sections: abstract, legend, an auto-generated index, sections 1–9, a claims table (section 8), open questions (section 9), and appendices A (per-experiment tables), B (timeline), C (file map) and D (one-liners).

**Read-only helpers under `changes/4_story/`:**
- `code/recompute.py` → `result/recompute_out.txt`: recomputes test-arm means, pass-rule statistics and mechanism splits from the raw `trials*.csv` and `wp1_table.csv`. Every value matches the reports.
- `result/git_timeline.txt` and `result/protocol_commits.txt`: commit times for the pre-registration timeline.
- `code/make_index.py`: regenerates the index from the finding headers.
- `code/renumber.py`: renumbers findings in document order. Used once this round; **do not use again**, because validators reference these ids.

**Self-fact-check.** Four independent read-only fact-check agents audited every finding, the tables and the timeline against the sources. All their findings were applied. The main corrections:
- **F92 (reserve):** WP1 *did* simulate samples 0.7–0.9 offline, including the Region6/7 reserve. The earlier "never built or simulated" was wrong and was corrected in F92, the abstract and §9.
- **F71:** dev retention now quotes the Ising arm C4, not the classical R2.
- **F46:** the first-access numbers are labelled pooled vs Region7-only (recomputed from `trials.csv`).
- **F54 and F60:** retagged TEST-PREREG (reported comparisons with no pass/fail).
- **F72:** retagged DEV.
- **Wording:** about fifteen scope and overclaim fixes (titles and claims tightened to match their sources).
- **New disclosure findings** for the incidents the first draft missed: F80 (SMT siblings, seed reuse, lost session), F82 (smaller disclosures), F86 (six round-2 validator items) and F85 (round-1 validator failures).

`check_story.py`: 0 problems. `python3 tools/privacy_scrub.py --check`: clean.

### Judgement calls a validator may want to challenge
1. **Phase-1 Q1–Q3 are tagged TEST-PREREG / NEGATIVE-TEST** (F18, F20, F33). The protocol is file-dated, but its first git commit (`be284a3`) postdates the held-out runs. This is stated in the legend, F18, F20, F33 and F75. TEST-POSTHOC would misdescribe hypotheses that *were* pre-specified on held-out data.
2. **Cross-cutting findings in §6 are tagged by the evidence their main claim rests on**, with dev items marked inline:
   - F68 and F69: TEST-POSTHOC;
   - F70: OFFLINE;
   - F72: DEV;
   - F71: TEST-PREREG, because retention was a pre-declared reported metric.
3. **H4 (F52) is P0 TEST-PREREG.** Its caveats are in F53 (P1): retrain-level SE, the s0.5 concentration, and a margin under twice the instance-level SE.
4. **F54 (X1 on Region5) and F60 (α arms on Region1) are tagged TEST-PREREG** because their protocols listed them as reported comparisons with no pass/fail. F60 notes that WP10's results report calls it "not pre-registered", contradicting its protocol.

### Discrepancies found in the sources (reported in the story, not fixed in the sources)
- **≈11.3% (RESEARCH.md):** no derivation anywhere (F08, Appendix D).
- **Dense SB limit:** RESEARCH.md's "≈70k" vs the observed OOM at 62.5k under a 64 GB cap (F31).
- **Amendments 1.2c/1.2d** are not recorded in SCOPE_v2 §1a (F04, F88).
- **SCOPE_v2** is still "pending confirmation" by the teammates (F03, F76).
- **Timestamps:**
  - the PROTOCOL_v2_H5 header time 19:25 is later than its commit at 19:23:04 (F83);
  - Track C's progress log says "~23:xx", but its results commit is 20:27 (F81).
- **The "untouched" reserve:** PROTOCOL_v2_H3 calls the reserve "untouched", yet WP1 simulated it offline (F92).
- **First-access labels:** WP3's RESULTS labels the pooled first-access numbers as "the known Region7 failure mode" (F46).
- **Round-2 auto-research validators:** six non-blocking items are not reflected in the notebook or final report (F86).

### Still open for later rounds
- **Unseen anchors.** The anchors were checked by the four fact-check agents; remaining off-by-a-few anchors in rarely cited files are possible.
- **Coverage could deepen:**
  - the WP5 hl-split and day-1 label timing tables (dev);
  - the Track C stage-1 per-design table (only summarised in F49);
  - the WP10 E1 per-proxy cell table;
  - the H-CLS per-candidate dev rows beyond the final report;
  - per-instance retention values.
- **WP3 timing.** The H3′ test ran from its 2026-10-05 launch to the 2026-10-16 result commit, but no source states when it finished. The story gives only the launch and the commit.
