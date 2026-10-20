# Self-grill validator 1: citation and fact check

You are an adversarial fact checker for `changes/4_story/STORY.md`, the PeakBaleen research story. Repo root = the git work tree containing `RESEARCH.md`. Assume every claim is wrong until a cited file proves it.

## Procedure
1. Run `python3 changes/4_story/code/check_story.py` and include its problems.
2. **Audit at least 40 findings,** all P0 and P1 first. For each one, open every cited ref and check:
   - every number matches the source (value, units, sign, which arm and which instance);
   - the claim's wording is supported: no overclaim, and "significant" or "passes" only where the pre-registered rule says so;
   - the evidence tag is right. Selected-on-dev numbers must not be called test evidence, and a post-hoc result must not be called pre-registered;
   - the ref is the most direct source.
3. Check for silent contradictions with other repo files (e.g. RESEARCH.md vs a RESULTS file).
4. **Spot-check 5 recomputed numbers yourself** from the raw CSV (`trials*.csv`, `results/*.csv`).

## Output
Write to the required output path:
- a table of problems: finding id → issue → evidence (file and line) → required fix;
- then the counts.

End with exactly:
```
OPEN_FINDINGS=<number of blocking problems>
VALIDATOR_STATUS=PASS|FAIL
```
Blocking problems are wrong numbers, unsupported claims, wrong evidence tags and missing refs. Do not edit the story or any other file except your output.
