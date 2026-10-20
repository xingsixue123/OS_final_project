# WP10 results: Region1 fresh test of the Ising threshold table (PROTOCOL_v2_H5, committed `2738cba`)

**Test instances:** Region1 (201910, 0.1%), samples 0.1–0.6, touched once. Reserve 0.7–0.9 untouched.
**Run:** unattended `src/chain.sh`, 2026-10-19 19:23 → 20:47.
- **Evaluations:** 108, **108 matched**, 0 failed.
- **Search cost:** Region1's traces are small, so threshold searches took 1–2 sims each.
- **Evaluation:** `src/evaluate_test.py`, written before the test and checked on WP9's trials, → `results_test/evaluation.json`.

## 0. Verdict

| judgement (PROTOCOL_v2_H5) | result |
|---|---|
| **H5: TB:pt beats A, B and the best α arm (B+α)** | **NO.** vs A: 1/6, −0.31. vs B: 3/6, +0.09 (SE 0.14). vs B+α: 3/6, +0.02 (SE 0.09) |
| Below RejectX (28.20) and CoinFlip (50.39) | yes (24.45) |
| TB:cd (classical control) | identical tables, so identical results (as expected from E2) |

**The Ising-optimized threshold table does not beat Baleen on Region1.**

**Not pre-registered (H4 was a Region5 test):** on Region1, the load-adaptive threshold arms themselves are also no better than Baleen. A+α 24.62 and B+α 24.48, vs A 24.14 (`evaluation.json`).

## 1. P100 per instance (mean of 3 matched retrains)

| instance | A | B | A+α | B+α | TB:pt (= TB:cd) | RejectX | CoinFlip |
|---|---|---|---|---|---|---|---|
| s0.1 | 24.81 | 25.19 | 25.50 | 25.37 | 25.19 | 27.53 | 35.33 |
| s0.2 | 22.02 | 22.27 | 22.15 | 22.41 | 22.17 | 24.62 | 47.40 |
| s0.3 | 30.69 | 31.69 | 30.60 | 30.45 | 31.18 | 37.20 | 59.42 |
| s0.4 | 22.68 | 22.72 | 23.33 | 22.72 | 22.78 | 25.81 | 55.18 |
| s0.5 | 22.13 | 22.90 | 22.53 | 22.55 | 23.00 | 25.40 | 42.86 |
| s0.6 | 22.50 | 22.47 | 23.63 | 23.35 | 22.39 | 28.63 | 62.13 |
| **mean** | **24.14** | 24.54 | 24.62 | 24.48 | 24.45 | 28.20 | 50.39 |

## 2. Interpretation
- **Region1 is a low-load trace.** Mean DT is about 12 util-% vs about 19–21 on Regions 5–7, and Baleen's peak is about 24 vs 36–39. There is little peak pressure for a load-adaptive policy to exploit. The threshold arms raise mean DT by about 0.25 without lowering the peak.
- **Together with WP9,** the deployed benefit of load-adaptive admission depends on the workload. It helps on the high-load Region5 (H4 YES, −3 to −5%) and not on Region1. This is a hypothesis to examine (WP4), not a claim.
- **Ising vs classical:** PT and coordinate descent produced the same tables (E2), so this test cannot separate them.

## 3. Integrity (`results_test/integrity.txt`)
- `check_frozen.sh`: frozen OK (94 files).
- Nothing under `0_reproduce/` or `1_literature_review/` is newer than `.leak_marker` (the 125 known foreign cpython-312/313 `.pyc` files dated 2026-10-10 are older and listed).
- `PATCH_v3.diff` sha256 `03f1523e688d`; `wp0_overlay/PATCH.diff` unchanged (`2a914eb589bb`).
- **Disclosed deviation:** the protocol was committed after the dev confirmation had finished but before its P100 values were read. The finalist was then chosen mechanically by the pre-fixed rule (`PROGRESS.md`).
