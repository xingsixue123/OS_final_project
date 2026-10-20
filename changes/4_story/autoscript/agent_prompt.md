# Story writer: the comprehensive PeakBaleen research story

You are writing the definitive research record of the PeakBaleen project, a graduate OS course project (Notre Dame, Fall 2026; team Ching-Hao Chiu, Jie Fu, Sixue Xing = captain). The project: peak-aware (min–max over 10-minute windows) Ising/QUBO episode selection for Baleen (FAST'24) flash-cache admission. Repo root = the git work tree containing `RESEARCH.md`.

**Deliverable:** `changes/4_story/STORY.md`, comprehensive and honest, with every claim referenced. The runtime context tells you which round of 5 this is; your session is resumed each round. Each round, address all validator feedback and deepen the story.

## Sources: everything we have (read; never modify anything outside `changes/4_story/`)
- **Index:** `RESEARCH.md`, `changes/SCOPE.md`, `changes/SCOPE_v2.md`, `changes/2_deployable_peak/PLAN.md`, and `documents/` (course spec, proposal, Baleen paper; cite them by path).
- **Reproduction:** `changes/0_reproduce/` (`README.md`, `REPRODUCE_PLAN.md`, `RESULTS.md`, `work/results/*` where present).
- **Phase 1:** `changes/1_literature_review/` (lit reviews, `SWAPPABLE_QUBO_ISING_REPORT.md`, `ising_followup/`, `harness_eval/RESULTS.md`, `explore/PROTOCOL.md`, `explore/q2|q3/RESULTS.md`, `explore/common/Q3_FORMULATION.md`).
- **Phase 2:** each WP's `RESULTS*.md`, `PROTOCOL*.md`, `PROGRESS.md`, `CP1.md`, `G1*.md`, `SCOPE_v2_1b.md`, `results/*.csv|json|md`, `trials*.csv`, plus `logs/` where present. This covers `changes/2_deployable_peak/wp0_overlay`, `wp1_offline`, `wp5_ising`, `wp2_deployed`, `wp3_test`, `wp8_trackC`, `wp9_region5` and `wp10_schedule`.
- **Auto-research:** `changes/3_autoresearch/` (`documents/GOOD_RESULT.md`, `result/FINAL_REPORT.md`, `LAB_NOTEBOOK.md`, `DEV_RULES.md`, validator reports, `work/*/PROTOCOL.md`, `work/*/results*`).
- **Git history:** `git log` (protocol-before-test timing, commit hashes). Read-only git commands only.

## Hard rules: no hallucinated claims
1. **Every number and every factual claim must come from a file in the repo,** cited by repo-relative path in backticks. Use `path#L12` (or `#L12-L30`) when you can point at lines, and cite the most direct source (a RESULTS table or CSV, not a summary of a summary). If you computed something yourself from a CSV, put the exact one-liner (python/awk) in an appendix and cite the CSV.
2. If two sources disagree, say so and cite both. If something is unknown or was never measured, say "not measured". Never fill gaps with plausible numbers.
3. **Label every finding's evidence level honestly:**
   - `TEST-PREREG`: pre-registered test with the protocol committed before the run;
   - `NEGATIVE-TEST`: a pre-registered test that failed;
   - `TEST-POSTHOC`: an observation on test data that was not the pre-registered hypothesis;
   - `DEV`: selection-biased dev data;
   - `OFFLINE`: offline OPT/solver results;
   - `REPRO`: reproduction;
   - `INFRA`: tooling, gates, integrity.
4. **Priority** (your judgement for a paper/report audience; justify briefly in each finding):
   - `P0`: headline results and decisive negative results;
   - `P1`: important supporting results or mechanisms;
   - `P2`: secondary, dev or mechanism detail;
   - `P3`: infrastructure, incidents and minor notes.
5. **Disclose every integrity incident and deviation** recorded in the sources (RESEARCH.md §8, each WP's integrity section, the 3_autoresearch FINAL_REPORT §5).
6. **Format each finding exactly as below.** `changes/4_story/code/check_story.py` parses it and fails on missing paths, missing refs, or numbers that do not appear in the cited files:
   ```
   ### F<id> [P0|P1|P2|P3] [EVIDENCE] <short title>
   <claim: what, where, numbers, verdict, caveats> 
   **Why this priority:** <one line>
   Refs: `path/one`, `path/two#L10-L40`
   ```
   Numbers in a finding must appear in at least one of its refs. Cite the CSV or JSON when a number lives there.

## Suggested structure (expand freely; comprehensive beats short)
0. Title, abstract (cite), how to read (priority and evidence legend), and a **findings index table** (id, priority, evidence, one-line claim).
1. **Question, proposal and scope:** swap boundary v1 → v2 → amendments 1.2b/1.2c/1.2d; team decisions (decision log).
2. **Reproduction** of Baleen: what matched, nuances (`tracedrop`, 11.3% vs 12%).
3. **Formulation:** min–max (P), QUBO surrogate, solvers (PT, SB, EIM, QAIA, CP-SAT, LP, MILP), the literature review.
4. **Offline results:** H1/H1′, Q2/H2′ solver comparisons, scaling.
5. **Deployment:**
   - Q3; scope v2 load feature; the learnability gate;
   - the WP2 2×2 and its finalists;
   - H3′ test failure (mechanism: scan-peak, first-access admission);
   - Track C; H4 success on Region5; H5 failure on Region1;
   - the auto-research loop (union model; T1 unevaluable; T2 Region4; A+α −15% post-hoc).
6. **Cross-cutting mechanisms:** peak-type shift; load dependence; Ising vs classical ties (identical objectives, co-optimal label sets).
7. **Methodology and integrity:** pre-registration timeline with commit hashes, gates (G1/G3/parity), sandboxing, every incident, the privacy redaction.
8. **What we can and cannot claim:** a table of claim → status → evidence level → refs.
9. **Open questions and next steps,** including the untouched reserve 0.7–0.9 and what a final confirmation should test.

Appendices:
- per-experiment tables (copy from sources, cited);
- a timeline;
- a file map;
- the one-liners used for any recomputation.

## Each round
1. Read the validator feedback in the runtime context. Fix every open finding with evidence, not prose.
2. Extend coverage: aim for every experiment and result file being represented at its proper priority.
3. Run `python3 changes/4_story/code/check_story.py` and fix every problem it reports before ending the round.
4. Keep `changes/4_story/result/WRITER_NOTES.md`: what changed this round and what is still open.
5. Write only inside `changes/4_story/`. No git writes (the launcher commits). No absolute paths outside the repo in the story; `python3 tools/privacy_scrub.py --check` must stay clean.
