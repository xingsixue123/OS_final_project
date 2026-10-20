# Validator: integrity + statistics + code

You are an independent reviewer of the PeakBaleen auto-research loop. Repo root = the git work tree containing `RESEARCH.md`. The contract is `changes/3_autoresearch/documents/GOOD_RESULT.md`.

**Check:**
1. **Sandbox.**
   - Every Baleen or solver launch in the worker's code and logs goes through `taskset ... bwrap --dev-bind / / --bind <private tmp> /tmp -- <env python> -B`, with env.sh sandboxing.
   - Every train runs under the flock train lock.
   - Nothing outside `changes/3_autoresearch/` was modified. Run `python3 changes/3_autoresearch/code/validate.py --integrity-only` (read-only apart from its own JSON).
2. **Code correctness of what produced the numbers.**
   - Threshold convergence to 35.599 MB/s ± 1%; P100 = `PeakServiceTimeUtil1`.
   - The arms really are what their names say: the α arms use `--ap-load-adapt-alpha -1` with the threshold search over (0, 4].
   - Overlay changes, if any, have a SCOPE amendment and a G1 bit-exact report whose evidence exists.
   - The Ising solver really produced Y's decisive component, and the classical control used the same objective.
3. **Statistics.**
   - Recompute the claim's comparisons from the raw trials CSV yourself. Do not trust the worker's summary or `validate.py` blindly; reconcile any differences.
   - Check that no rows are excluded beyond the protocol.
   - Check that the static baselines are frozen-code replays.

Do not edit any worker file. Write your review to the required output path. It must end with exactly two lines:
```
OPEN_FINDINGS=<number of blocking findings>
VALIDATOR_STATUS=PASS|FAIL
```
PASS requires OPEN_FINDINGS=0. Give each finding the evidence and the concrete fix.
