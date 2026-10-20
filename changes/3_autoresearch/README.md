# 3_autoresearch: unattended 24 h search for an Ising/QUBO method that beats deployed Baleen

- **Contract (fixed before launch):** `documents/GOOD_RESULT.md` (sha256 in `autoscript/GOOD_RESULT.sha256`). The validator recomputes the claim from raw rows.
- **Loop:** `autoscript/run_auto.sh`, following the `autoresearch/neural_bench` launcher pattern.
  - A headless Claude Code worker round (Opus 5.5 1M, effort xhigh, permissions skipped by the captain's instruction; ≤ 6 h; session resumed each round), then `code/validate.py` (deterministic, fail-closed), then 2 independent validators (red team; integrity + statistics + code), then a git sync (privacy scrub first).
  - It repeats until a GOOD RESULT passes every gate, the worker declares the test budget exhausted, or 24 h pass.
- **Test budget:** 2 fresh pools at most (Region2 0.1–0.6, Region4 0.2–0.6, Region3 0.1–0.3), each pre-registered and committed before `TEST_GO`. Reserve samples 0.7–0.9 are never touched.

**Launch / resume:**
```
cd changes/3_autoresearch && autoscript/run_auto.sh --detach          # new run
RUN_ID=<same id> autoscript/run_auto.sh --detach                      # continue a dead run, same deadline
cat result/LOOP_STATUS.txt; tail output/launcher_all.log                    # status
```
