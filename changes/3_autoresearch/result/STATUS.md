# STATUS (3_autoresearch, run 20261020_004634)

**Updated:** 2026-10-20 03:25, round 1. G1_v4 PASS (`work/cls_table/G1_v4.md`).
- **Screen decided (03:22):** CB:pt is the only candidate through the R0 gate. Its confirmation (`queue_dev2.txt`, 22 evaluations) is running inside `chain_dev2`. The finalist rule follows automatically; then `chain_test_t1` either spends T1 or stops.
- **Test spends:** 0 of 2. The T1 PROTOCOL (conditional) is committed: `96506745`.
- **T1 prerequisites (no outcome read):** jobs (`work/cls_table/jobs_test.json`) and instance dumps (`work/cls_table/inst_test/`) are built. Static replays are blocked in code until TEST_GO.
- **Families under study:** H-CLS (`work/cls_table/`):
  - per-retrain Ising class tables CA/CB:pt|ptm;
  - pooled leave-one-out Ising class table UB:ptm (plan B, DEV_RULES R2).
- **Overlay v4** = v3 + `PATCH_v4_delta.diff` (`SCOPE_AMENDMENT.md`, item 1.2c); G1_v4 PASS.

## Detached jobs (dev; resumable; finished sims are re-used; ledger `work/cls_table/trials_dev.csv`)
| job | log | what |
|---|---|---|
| dev queue | `work/cls_table/logs/queue_dev1c.out` | `queue_dev1c.txt` (02:47): the remaining candidate r1 screen + Region5_s0 / Region1_s0 refs (A, B, Aa, Ba × r1–3). Report-only work (controls r1, probe) is in `queue_report.txt`, to run after the decision/test |
| chain_dev2 | `work/cls_table/logs/chain_dev2.out` | waits for the r1 screen → R0 gate → confirmation queue `queue_dev2.txt` (≤ 2 candidates + controls: r2–3 DEV8, r1–3 Region1_s0/Region5_s0) → finalist rule → `results/dev_finalist.json` |
| chain_test_t1 | `work/cls_table/logs/chain_test_t1.out` | waits for `dev_finalist.json`; no finalist → `work/t1_region2/CHAIN_DONE`, no spend; else G1_v4 check → TEST_GO → static + test + `eval_test.py` |
| G1_v4 | `work/cls_table/logs/g1v4.out` | `results/g1v4_summary.json` when done |

The earlier per-arm drivers (probe, screen, screen_m, extra refs, UB) were stopped at 01:56 so that one driver works through the evaluations in priority order. Their 14 partial sims were deleted; finished sims are re-used.

## RESUME (from the repo root; idempotent)
```
cd changes/3_autoresearch/work/cls_table && source env.sh
setsid nohup src/sbx.sh src/cls.py --mode dev --queue queue_dev1c.txt -j 14 >> logs/queue_dev1c.out 2>&1 < /dev/null &
# later (report only): setsid nohup src/sbx.sh src/cls.py --mode dev --queue queue_report.txt -j 14 >> logs/queue_report.out 2>&1 < /dev/null &
setsid nohup src/sbx.sh src/chain_dev2.py >> logs/chain_dev2.out 2>&1 < /dev/null &          # if no results/dev_finalist.json yet
setsid nohup bash src/chain_test_t1.sh >> logs/chain_test_t1.out 2>&1 < /dev/null &       # idempotent (CHAIN_DONE)
setsid nohup src/sbx.sh src/g1v4.py >> logs/g1v4.out 2>&1 < /dev/null &
# running?  ps -eo pid,etimes,args | grep 3_autoresearch/work | grep -v grep
# screen table: python3 src/dev_eval.py screen ; finalist rule: python3 src/dev_eval.py final --arms <cfg>
```
Before relaunching after a kill, delete partial `work/runs/dev/*/converge/th_*` dirs (no `*_cache_perf.txt.lzma`).
