# Track D WP9 progress: Region5 test for H4 (PLAN_C §6, `d10e572`) — preparation

**Rules in force:**
- No test arm (A, B, A+α, B+α, X1) runs on Region5 s0.1–0.6 until the coordinator commits `PROTOCOL_v2_H4.md` and creates `wp9_region5/TEST_GO`. The driver enforces this: `src/wp9.py --mode test` refuses to start without `TEST_GO`.
- Reserve s0.7–0.9: no job, dump or label exists; `make_jobs_test.py`, `prep.py` and `wp9.py` refuse them.
- Sandbox `env.sh` (HOME/XDG/TMPDIR inside wp9, `CONDA_REGISTER_ENVS=false`, `PYTHONNOUSERSITE=1`, `PYTHONDONTWRITEBYTECODE=1`); every Baleen/solver process `taskset -c <cpus> bwrap --dev-bind / / --bind <private job tmp> /tmp -- <env python> -B`; every train under `flock 2_deployable_peak/.train.lock`.
- CPUs 0-23 / ≤ 14 sims while `TIMING_IDLE` exists (automatic in `SimSlot`). The machine is shared with `<another project>`: sims take ≈ 14 min each (results unaffected).
- No git writes. Nothing under `0_reproduce/` or `1_literature_review/` modified (copies and read-only symlinks only).

## Status (2026-10-16 21:30): preparation COMPLETE; protocol written; STOPPED, waiting for the coordinator

| item | status | where |
|---|---|---|
| Area: copy of `wp3_test` (env.sh, src/, .gitignore; `work/` → overlay, `work_frozen/` → frozen, `data` → explore common data, read-only) | done | `src/` (`wp3.py` → `wp9.py`) |
| Jobs Region5 s0 + s0.1–0.6 (Fig 9 variant ML-Range on Partial Hit, `20230421_alltraces_pfalways`; asserted) | READY; OPT EAs equal WP1's | `jobs.json` |
| Day-1 + fullml dumps (frozen driver), sha256 | READY, 14 files | `INSTANCES.md`, `results/instances_sha256.csv` |
| F1PT labels, seeds 1–6, frozen 10 s config | READY, 36 sets, all rc 0 | `labels/`, `results/labels_summary.csv` |
| RejectX / CoinFlip frozen replays | READY; bit-exact vs authors at their own p (12/12, max diff 3e-10); CoinFlip 6/6 matched; **RejectX matched 1/6** (WR step, below) | `results/static_baselines.csv`, `static_author_check.csv`, `static_rejectx_bracket.csv` |
| Retention inputs (WP1 offline OPT, not recomputed) | READY | `results/retention_inputs_wp1.csv` |
| Evaluation code (H4 rule) | READY; reproduces `wp3_test/RESULTS_test.md` on WP3's trials | `src/evaluate_test.py` |
| Dry run Region5 s0, arm A, 1 retrain | **OK** | `dryrun/` |
| Protocol | written, **awaiting commit + `TEST_GO`** | `PROTOCOL_v2_H4.md` |

**Dry run (Region5 s0, A, rep 1, `--mode dryrun`).** Train 89 s (ML-Range prefetch models `prefetch_{offset_start,offset_end,size,pred_net_pf_st_binary}` trained and loaded by `LearnedRangePrefetcherModel`; prefetch `partial` / `acctime-episode-predict` as the authors' row). Threshold search (0, 1): θ 0.830 → WR 25.50; 0.635 → 38.92; 0.683 → **35.78, matched** (3 sims), P100 **32.93**, first-access admission 3.5%. The authors' s0 Baleen row: θ 0.701, WR 34.64, P100 33.47. Wall 49 min. Nothing broke; no code change was needed beyond the WP9 adaptations.

**RejectX / CoinFlip (frozen, `20230410_static_pf`).**

| instance | RejectX P100 (authors' p) | its WR | RejectX P100 below the step (WR) | CoinFlip P100 | CoinFlip WR |
|---|---|---|---|---|---|
| Region5 s0.1 | 46.69 | 39.54 | 46.67 (29.54) | 46.96 | 35.62 |
| Region5 s0.2 | 36.08 | 37.77 | 35.68 (28.47) | 37.87 | 35.60 |
| Region5 s0.3 | 39.68 | 38.47 | 39.62 (28.76) | 46.75 | 35.61 |
| Region5 s0.4 | 28.12 | 35.62 (matched) | = | 29.21 | 35.65 |
| Region5 s0.5 | 46.05 | 37.44 | 46.26 (28.12) | 61.36 | 35.60 |
| Region5 s0.6 | 39.50 | 38.16 | 39.33 (29.19) | 44.67 | 35.54 |
| **mean** | **39.35** | | **39.28** | **44.47** | |

On 5/6 instances RejectX's write rate jumps over the ±1% band between probabilities 1e-6 apart, so it cannot be matched (the authors' rows are off-target as well). PROTOCOL_v2_H4 §3 therefore requires an arm to be below **both** RejectX means. The "baseline" column of `static_baselines.csv` is the closest-WR bisection point, whose P100 equals the authors' value on all 5 (its WR is 37.27–38.87).

**Code adaptations (all in wp9's own copies):** Region5 keys and Fig 9 variant (`make_jobs_test.py`); `wpcommon.py` (W, `WP9_ROOT`, TEST/DRY/RESERVE lists, `configure('dryrun')`); `wp9.py` (arms A B Aa Ba X1, `TEST_GO` guard, reserve refusal, WRMAP0 seeding for Region5 = Region6's maps); `run_labels.py` (F1PT only); `prep.py` (key guard); `evaluate_test.py` (H4/B+α/X1 rules, RejectX two-sided condition); new `check_static.py`, `summarize_prep.py`. Training, convergence and extra-retrain logic are WP3's, unchanged.

## Launch (only after the coordinator commits the protocol and creates TEST_GO)
```
cd /home/sxing/project/OS_final_project/changes/2_deployable_peak/wp9_region5 && source env.sh
setsid nohup taskset -c 0-23 $BALEEN_PY -B src/wp9.py --mode test --arms A B Aa Ba X1 -j 16 > logs/wp9_test.out 2>&1 < /dev/null &
$BALEEN_PY -B src/evaluate_test.py          # after it finishes -> results/evaluation.json
```
Size: 90 evaluations; 54 trainings (A, B, D:F1PT × 18) under the train lock; ≈ 3 sims per evaluation ≈ 270 sims at ≈ 14 min each with ≤ 14 concurrent: roughly 5–7 h on the shared machine.

## RESUME (drivers are resumable: finished evaluations are skipped via trials.csv; finished sims and trainings re-used)
```
cd /home/sxing/project/OS_final_project/changes/2_deployable_peak/wp9_region5 && source env.sh
pgrep -af "wp9_region5|src/wp9.py|src/prep.py|src/run_labels.py" | grep -v pgrep     # must be empty before relaunching
# preparation (complete; re-running is a no-op):
$BALEEN_PY -B src/make_jobs_test.py
setsid nohup taskset -c 0-23 $BALEEN_PY -B src/prep.py dumps --keys Region5_s0 Region5_s0.1 Region5_s0.2 Region5_s0.3 Region5_s0.4 Region5_s0.5 Region5_s0.6 > logs/prep_dumps.out 2>&1 < /dev/null &
setsid nohup taskset -c 0-23 $BALEEN_PY -B src/prep.py static > logs/prep_static.out 2>&1 < /dev/null &
setsid nohup taskset -c 0-23 $BALEEN_PY -B src/run_labels.py > logs/run_labels.out 2>&1 < /dev/null &
$BALEEN_PY -B src/prep.py sha && $BALEEN_PY -B src/summarize_prep.py && $BALEEN_PY -B src/check_static.py
# dry run (Region5 s0 only; done):
setsid nohup bash dryrun/launch_dryrun.sh > dryrun/wp9_dryrun.out 2>&1 < /dev/null &
# test (ONLY after TEST_GO exists): the launch command above; relaunching the same command resumes.
```

## Log
- 20:28 `.leak_marker`; area created (copies of `wp3_test` env.sh/src/.gitignore; symlinks to the overlay, the frozen artifact, the explore data).
- 20:29 `jobs.json` (Region5 s0, s0.1–0.6; variant and experiment asserted; OPT EAs = WP1's).
- 20:29–21:00 dumps (14), labels (36), static replays (12; RejectX step found); `evaluate_test.py` checked on WP3's trials (A+α vs A +0.965 5/6 etc., exactly `wp3_test/RESULTS_test.md`).
- 20:35–21:23 dry run Region5 s0 arm A: matched, P100 32.93.
- 21:25 RejectX two-sided rule written into `PROTOCOL_v2_H4.md` and `evaluate_test.py` (before any test run).
- 21:29 integrity (`results/integrity.txt`): `check_frozen.sh` → frozen OK (94 files); nothing under `0_reproduce/` or `1_literature_review/` (envs included) newer than the marker; 125 known foreign cpython-312/313 `.pyc` dated 10-10 (left untouched); no `__pycache__`/`.pyc` in wp9 or the overlay; outside wp9 only 25 `.git/objects` (other git activity; this work ran only read-only git commands); `PATCH.diff` sha256 `2a914eb589bb`.
- 21:30 **STOP**: preparation complete; waiting for the coordinator to commit `PROTOCOL_v2_H4.md` and create `TEST_GO`.
