# Track A WP3 progress: test preparation for PROTOCOL_v2_H3 (committed at cba9970)

**Rules in force:**
- No overlay test arm (A, B, X1, X2, A+α, B+α, Dc+α) runs until G3 is signed. The driver enforces this: `src/wp3.py --mode test` refuses to start unless `wp3_test/G3_SIGNED` exists.
- Test samples: Region7/Region6 × 0.4, 0.5, 0.6.
- Sandbox `env.sh`; bwrap with a private /tmp per job; `flock 2_deployable_peak/.train.lock` around every train.
- CPUs 0-23 / ≤ 14 sims (`TIMING_IDLE` exists); 8-11,20-23 / ≤ 6 otherwise (automatic in `SimSlot`).
- No commits. Nothing under `0_reproduce/` or `1_literature_review/` modified (copies only).

## Status (2026-10-04 17:00): every prerequisite of PROTOCOL §7 except G3 (§7.1) is READY

| PROTOCOL §7 item | status | where |
|---|---|---|
| 1. G3 teammate review of PATCH.diff | **PENDING** (guide `wp0_overlay/G3_REVIEW.md`) | coordinator creates `wp3_test/G3_SIGNED` when signed |
| 2. Test jobs (samples 0.4-0.6) from `results_release.csv.gz`, make_jobs logic | READY | `jobs.json` (`src/make_jobs_test.py`; uses a copy of `0_reproduce/repro/common.py`); OPT EAs equal WP1's independent extraction |
| 3. day-1 + fullml instances through the unmodified driver | READY, sha256 recorded | `INSTANCES.md`, `results/instances_sha256.csv` (`src/prep.py dumps`, frozen code + phase-1 dump Policy) |
| 4. Label sets F1PT + F1CPSAT, seeds 1-6, frozen configs | READY (72 sets) | `labels/`, `results/labels_summary.csv` (one cfg per design, 10 s) |
| 5. RejectX / CoinFlip replays (FROZEN code) | READY: 12/12 matched with the authors' own `--ap-probability`; P100 equal to the authors' to 4 decimals | `results/static_baselines.csv` |
| Retention inputs (§5): WP1 offline OPT, not recomputed | READY | `results/retention_inputs_wp1.csv` (from `wp1_offline/results/wp1_table.csv`: R0 = peak-blind, `pt` = peak-aware PT 300 s; CP-SAT/LP for reference) |
| Test driver + evaluation | READY; dry-run OK on dev Region7 s0 only | `src/wp3.py`, `src/evaluate_test.py`; dry run in `dryrun/` |

**RejectX / CoinFlip (frozen, matched WR):**

| instance | RejectX P100 | RejectX WR | CoinFlip P100 | CoinFlip WR |
|---|---|---|---|---|
| Region7 s0.4 | 39.29 | 35.85 | 49.24 | 35.60 |
| Region7 s0.5 | 42.05 | 35.55 | 51.60 | 35.60 |
| Region7 s0.6 | 39.31 | 35.56 | 43.19 | 35.63 |
| Region6 s0.4 | 38.56 | 35.51 | 45.07 | 35.60 |
| Region6 s0.5 | 37.96 | 35.76 | 44.68 | 35.60 |
| Region6 s0.6 | 47.21 | 35.73 | 58.04 | 35.60 |
| **mean** | **40.73** | | **48.64** | |

**Dry run (dev Region7 s0 only, 1 retrain, `--mode dev_dryrun`):**
- Arms: A, X1 (which trained its D:F1PT base retrain on demand from WP2 dev labels), and A+α (re-using A's retrain).
- All matched: A 39.89, X1 39.66, A+α 39.18. All are within the WP2 dev spread for that instance (A 40.00 ± 0.14; X1 39.90 ± 0.11; A+α 39.65 ± 0.12).
- The θ ranges follow PROTOCOL §3: (0, 1) for A; (0, 4] for the α arms.
- `evaluate_test.py`, run on the WP2 dev trials, reproduces the dev comparisons exactly (X1 vs A +1.301 ± 0.251, 6/8 …).
- Guard check: `--mode test` without `G3_SIGNED` refuses (AssertionError); no test trial file exists.

**Notes:**
- `results/wrmap_pairs.jsonl` holds WP2's emulator/simulator write-rate pairs, used for threshold seeding only.
- The emulator feature caches for the test fullml instances are computed at the first test evaluation; features only, no outcomes.

## Exact command that launches the H3′ test once G3 is signed
```
cd /home/sxing/project/OS_final_project/changes/2_deployable_peak/wp3_test && source env.sh
touch G3_SIGNED            # by the coordinator, only after the teammate's G3 sign-off is recorded
nohup taskset -c 0-23 $BALEEN_PY -B src/wp3.py --mode test --arms X1 X2 A B Aa Ba Dca -j 16 > logs/wp3_test.out 2>&1 &
# after it finishes (includes the PROTOCOL §4 extra-retrain pass, seeds 4-6):
$BALEEN_PY -B src/evaluate_test.py          # -> results/evaluation.json (H3', H3'-labels, X2, Dc+alpha, retention, secondary)
```
**Size:** 7 arms × 6 instances × 3 retrains = 126 evaluations.
- Trainings: 4 base arms (A, B, D:F1PT, D:F1CPSAT) × 18 = 72, about 40 s each when the machine is idle, under the train lock.
- Sims: about 2–3 per evaluation, about 300 sims. At 14 concurrent, roughly 3–4 hours.

## RESUME (the drivers are resumable: finished evaluations are skipped via trials.csv, finished sims re-used)
```
cd /home/sxing/project/OS_final_project/changes/2_deployable_peak/wp3_test && source env.sh
pgrep -af "src/wp3.py|simulate_ap|wp2_launch_train|src/prep.py|src/run_labels.py" | grep -v pgrep   # must be empty
# preparation (all complete; re-running is a no-op):
$BALEEN_PY -B src/make_jobs_test.py
nohup taskset -c 0-23 $BALEEN_PY -B src/prep.py dumps  > logs/prep_dumps.out 2>&1 &
nohup taskset -c 0-23 $BALEEN_PY -B src/prep.py static > logs/prep_static.out 2>&1 &
nohup taskset -c 0-23 $BALEEN_PY -B src/run_labels.py  > logs/run_labels.out 2>&1 &
$BALEEN_PY -B src/prep.py sha
# dry run (dev only):
nohup taskset -c 0-23 $BALEEN_PY -B src/wp3.py --mode dev_dryrun --arms A X1 Aa --insts Region7_s0 --reps 1 -j 4 > dryrun/wp3_dryrun.out 2>&1 &
# test (ONLY after G3_SIGNED exists): the launch command above; relaunching the same command resumes.
```

## Log
- 16:23 `.leak_marker`; area created:
  - `work/BCacheSim` → overlay; `work_frozen/BCacheSim` → frozen; `data` → explore common data (read-only);
  - copies of the phase-1/WP2 code (`src/`).
- 16:24 `jobs.json` (6 instances; Baleen Fig 9 variant + RejectX/CoinFlip static/tracedrop + OPT row).
- 16:24–16:36 instance dumps (12; frozen driver); RejectX/CoinFlip replays (12/12 matched, exact author P100).
- 16:26–16:40 label sets: 72 (F1PT/F1CPSAT × seeds 1-6).
- 16:30 test driver `src/wp3.py` (from `wp2.py`); G3 guard verified.
- 16:36–16:57 dev dry run (Region7 s0; A, X1, A+α): all matched.
- 16:50 `src/evaluate_test.py` written before any test data exist; verified on WP2 dev trials.
- 16:58 integrity:
  - `check_frozen.sh` → frozen OK (94 files);
  - nothing under `0_reproduce/` or `1_literature_review/` is newer than the marker;
  - no `__pycache__`;
  - the leak check lists only 18 `.git/objects` from other git activity (this work ran no git command); `results/integrity.txt`.
- 17:00 **STOP** (WP3 preparation complete; waiting for G3).
