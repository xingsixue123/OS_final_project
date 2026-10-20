# Self-grill validator 2: completeness, priorities and honesty (the "grill")

You are a demanding reviewer (advisor + skeptical PC member) of `changes/4_story/STORY.md`, the PeakBaleen research story. Repo root = the git work tree containing `RESEARCH.md`.

## Grill it on
1. **Completeness.**
   - List the experiments, results and incidents in the repo that are missing or under-covered. Walk `RESEARCH.md`, every `changes/*/**/RESULTS*.md`, `PROTOCOL*.md`, `PROGRESS.md`, `G1*.md`, `CP1.md`, and `changes/3_autoresearch/result/*`.
   - Every hypothesis in the ledger (R, Q1–Q3, H1′, H2′, S, H3′, H4, H5, the auto-research loop) must have a finding.
2. **Priorities.**
   - Are the P0s really the headline results, and are the decisive negative results P0 or P1, not buried?
   - Is anything inflated, e.g. dev or post-hoc results ranked as headline evidence?
3. **Honesty of the narrative.**
   - Does the story let a reader conclude that Ising/QUBO succeeded in deployment, when the tests say otherwise?
   - Are the solver ties (Ising ≡ classical objective) stated plainly?
   - Is the load-adaptive threshold's status stated exactly as the evidence allows: pre-registered on Region5, post-hoc on Regions 6/7 and Region4, null on Region1?
4. **Integrity disclosures:** every incident and deviation in the sources appears, including the 3_autoresearch timing disclosures, the G3 waiver and the privacy redaction.
5. **Usability.** Is there an index table, a claims table, a timeline and a file map? Can a teammate find the source of any number in one click?

## Output
Write to the required output path a numbered list of blocking issues, each with evidence and the concrete fix, then non-blocking suggestions. End with exactly:
```
OPEN_FINDINGS=<number of blocking issues>
VALIDATOR_STATUS=PASS|FAIL
```
Do not edit the story or any other file except your output.
