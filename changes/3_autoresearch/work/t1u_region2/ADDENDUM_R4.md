# Addendum to PROTOCOL.md (commit `76cf5c8d`): dev extra seeds (DEV_RULES R4)

**Written:** 2026-10-20 ≈04:48 (committed 04:48:58 in `4e25e7e4`).
- After the protocol commit; before any union confirmation simulation; while the retrain-1 screen was still running.
- Committed before the union finalist exists.
- PROTOCOL.md itself is unchanged.

**What changed.** The mechanical finalist step (`work/union/src/chain_union_dev.py`) now applies `result/DEV_RULES.md` R4 between the confirmation and the finalist rule:
- a candidate cell with fewer than 3 matched dev retrains gets retrains 4, 5, 6, in order, until it has 3;
- on DEV8 these retrains are trained here: a new Baleen A training, plus F1 labels with seed k on the published `explore/common/inst/day1_<inst>.npz` and a new X training (`cls.py` / `union.py` dev paths for k > 3).

The screen gate, the finalist rule, the candidate set and every test-mode code path are unchanged. The test already had the same extra-seed rule (PROTOCOL.md §3).

**Why.** The cls_table candidate CB:pt was ineligible because a single cell ended unmatched on a write-rate step (Region1_s0 r2, 36.14 MB/s after 7 sims). Without the provision the dev rule can reject any candidate on such a step. The decision used no union confirmation outcome; none existed.
