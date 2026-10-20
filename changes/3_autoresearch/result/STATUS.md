# STATUS (3_autoresearch, run 20261020_004634)

**Updated:** 2026-10-20 01:58, round 1.
- **Test spends:** 0 of 2.
- **T1 prerequisites (no outcome read):** jobs (`work/cls_table/jobs_test.json`) and instance dumps (`work/cls_table/inst_test/`) are built. Static replays are blocked in code until TEST_GO.
- **Families under study:** H-CLS (`work/cls_table/`):
  - per-retrain Ising class tables CA/CB:pt|ptm;
  - pooled leave-one-out Ising class table UB:ptm (plan B, DEV_RULES R2).
- **Overlay v4** = v3 + `PATCH_v4_delta.diff` (`SCOPE_AMENDMENT.md`, item 1.2c); the G1_v4 gate is running.

## Detached jobs (dev; resumable; finished sims are re-used; ledger `work/cls_table/trials_dev.csv`)
| job | log | what |
|---|---|---|
| dev queue | `work/cls_table/logs/queue_dev1.out` | `queue_dev1.txt`, in priority order: candidates r1 → UB:ptm r2–3 → Region1_s0 / Region5_s0 refs (A, B, Aa, Ba × r1–3) → controls r1 → UB:cdm r2–3 → probe |
| G1_v4 | `work/cls_table/logs/g1v4.out` | `results/g1v4_summary.json` when done |

The earlier per-arm drivers (probe, screen, screen_m, extra refs, UB) were stopped at 01:56 so that one driver works through the evaluations in priority order. Their 14 partial sims were deleted; finished sims are re-used.

## RESUME (from the repo root; idempotent)
```
cd changes/3_autoresearch/work/cls_table && source env.sh
setsid nohup src/sbx.sh src/cls.py --mode dev --queue queue_dev1.txt -j 14 >> logs/queue_dev1.out 2>&1 < /dev/null &
setsid nohup src/sbx.sh src/g1v4.py >> logs/g1v4.out 2>&1 < /dev/null &
# running?  ps -eo pid,etimes,args | grep 3_autoresearch/work | grep -v grep
# screen table: python3 src/dev_eval.py screen ; finalist rule: python3 src/dev_eval.py final --arms <cfg>
```
Before relaunching after a kill, delete partial `work/runs/dev/*/converge/th_*` dirs (no `*_cache_perf.txt.lzma`).
