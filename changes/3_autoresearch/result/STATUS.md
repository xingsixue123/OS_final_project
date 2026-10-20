# STATUS (3_autoresearch, run 20261020_004634)

**Updated:** 2026-10-20 06:28, end of round 1.
- **T1 SPENT (test running).** The union finalist XA:F1PT (control XA:F1CPSAT) was chosen mechanically at 06:26:49; TEST_GO was written at 06:26:50 (commit `76cf5c8d`, POOL=T1). The test runs detached in `chain_test_t1u` (`work/union/logs/test_t1u.out`), then `eval_test.py` writes `work/t1u_region2/results_test/evaluation.json` and `CHAIN_DONE`.
- **Next round:**
  - (1) If `work/t1u_region2/CHAIN_DONE` exists, read `evaluation.json`.
  - (2) If `good_result` is true: `cd work/union && python3 src/write_claim.py --test-dir ../t1u_region2`, then `python3 code/validate.py`.
  - (3) If false: write the T1 negative result. `chain_test_t2u` (`work/union_t2/`) then spends T2 automatically with the same Y; afterwards write FINAL_REPORT.md + STOP_EXHAUSTED if T2 also fails.
  - (4) If the chain died, relaunch it (idempotent; the drivers re-use finished trains and sims).

- **Test spends:** 1 of 2 (T1, union). Two conditional T1 protocols were committed; only the union one wrote a TEST_GO.
  - `work/t1_region2/PROTOCOL.md` (`96506745`, cls_table family): **void.** No finalist; CHAIN_DONE 04:42 without TEST_GO.
  - `work/t1u_region2/PROTOCOL.md` (`76cf5c8d`, union family): Y is the finalist of `chain_union_dev.py` (DEV_RULES R3).
- **Families:**
  - H-CLS (`work/cls_table/`, overlay v4, G1_v4 PASS): screened; only CB:pt passed the screen gate; finalist rule failed.
  - **H-UX union** (`work/union/`, overlay v5 = v4 + union 1.2d, **G1_v5 PASS**): screen passed (XA +1.46, XG +1.07 mean d); confirmation running. ADDENDUM_R4 (`4e25e7e4`) adds dev extra seeds.
  - `work/t2u_region4/PROTOCOL.md` (`1cda6af`): the T2 conditional protocol (same Y; runs only if Y fails T1). T2 prerequisites are in `work/union_t2/`.
- **T1 prerequisites (no outcome read):**
  - jobs `work/*/jobs_test.json`;
  - fullml dumps `work/cls_table/inst_test/`;
  - day-1 dumps and 72 F1 label sets `work/union/inst_test/`, `work/union/labels/`.

## Detached jobs (all resumable; finished sims are re-used)
| job | log | what |
|---|---|---|
| cls_table chain_dev2 | `work/cls_table/logs/chain_dev2.out` | last CB:pt confirmation run → `results/dev_finalist.json` (expected FINALIST null) |
| cls_table chain_test_t1 | `work/cls_table/logs/chain_test_t1.out` | stops with `work/t1_region2/CHAIN_DONE` if no finalist |
| union screen | `work/union/logs/screen_x_r1.out` | XA/XG × F1PT/F1CPSAT × DEV8 × retrain 1 |
| union chain_union_dev | `work/union/logs/chain_union_dev.out` | R0 gate → confirmation `queue_dev2.txt` (r2–3 DEV8, r1–3 Region5_s0/Region1_s0) → finalist → `work/union/results/dev_finalist.json` |
| union chain_test_t1u | `work/union/logs/chain_test_t1u.out` | finalist? → G1_v5? → TEST_GO (`work/t1u_region2/`) → static + test + `eval_test.py` |
| G1_v5 | `work/union/logs/g1v5.out` | `work/union/results/g1v5_summary.json` |
| X pretrain | `work/union/logs/pretrain_x.out` | F1-label models for Region5_s0/Region1_s0 (done) |
| union chain_test_t2u | `work/union_t2/logs/chain_test_t2u.out` | dormant; spends T2 only if the union finalist fails T1 |

All sims share one 14-slot pool (`work/cls_table/.sim_slots.d`); every train holds `2_deployable_peak/.train.lock`.

## RESUME (from the repo root; idempotent; delete partial `work/*/work/runs/*/*/converge/th_*` dirs without `*_cache_perf.txt.lzma` first)
```
cd changes/3_autoresearch/work/cls_table && source env.sh
setsid nohup src/sbx.sh src/chain_dev2.py >> logs/chain_dev2.out 2>&1 < /dev/null &          # if no results/dev_finalist.json
setsid nohup bash src/chain_test_t1.sh >> logs/chain_test_t1.out 2>&1 < /dev/null &
cd ../union && source env.sh
setsid nohup src/sbx.sh src/union.py --mode dev --arms XA:F1PT XG:F1PT XA:F1CPSAT XG:F1CPSAT --reps 1 -j 14 >> logs/screen_x_r1.out 2>&1 < /dev/null &
setsid nohup src/sbx.sh src/chain_union_dev.py >> logs/chain_union_dev.out 2>&1 < /dev/null &   # if no results/dev_finalist.json
setsid nohup bash src/chain_test_t1u.sh >> logs/chain_test_t1u.out 2>&1 < /dev/null &
setsid nohup src/sbx.sh src/g1v5.py >> logs/g1v5.out 2>&1 < /dev/null &                         # if no results/g1v5_summary.json
cd ../union_t2 && source env.sh && setsid nohup bash src/chain_test_t2u.sh >> logs/chain_test_t2u.out 2>&1 < /dev/null &
# later, report only: cd ../cls_table && setsid nohup src/sbx.sh src/cls.py --mode dev --queue queue_report.txt -j 14 >> logs/queue_report.out 2>&1 < /dev/null &
# running?  ps -eo pid,etimes,args | grep 3_autoresearch/work | grep -v grep
```
