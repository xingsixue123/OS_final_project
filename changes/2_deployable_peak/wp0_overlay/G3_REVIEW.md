# G3 review guide: `wp0_overlay/PATCH.diff`

**For:** Ching-Hao Chiu or Jie Fu. **Time needed:** about 30–45 minutes.

**Why:** `changes/SCOPE_v2.md` §3 (G3) requires one teammate to review the phase-2 code change before any run on the test samples (H3′, `wp2_deployed/PROTOCOL_v2_H3.md`). You are checking that the patch does only what scope v2 allows, and that it cannot leak future information or change default behaviour. You are *not* re-running experiments; the gate evidence is already recorded.

## 1. What the patch does (9 files, +217/−6, against frozen BCacheSim `ddeb2d8`)
- **New module `cachesim/load_features.py`.**
  - It adds the **`load`** feature group: trailing *demand-side* GET disk-head time over the last 10/30/60 minutes, counting only requests with timestamp **strictly before** the access, in utilisation % (the same units as the peak metric). It is built from the trace's request stream, so it never depends on the cache's admission decisions.
  - It adds the **`tod`** group: hour of day as sin/cos.
  - It provides the optional **load-adaptive threshold** θ_t = θ · clip((load_10m/20)^α, 0.25, 4).
- **Training:** `episodic_analysis/train_ap.py` (feature rows and subset names), `train_prefetcher.py` (optional prefetch-model features), and one plumbing line in `train.py`.
- **Serving:** `cachesim/sim_features.py` (`count_feat`, `collect_features`), `sim_cache.py` (builds the demand series; prefetch batch), `admission_policies.py` (`NewMLAP` column guard; adaptive threshold in `batchAccept`), `prefetchers.py` (column guard), and `simulate_ap.py` (new flags, all off by default).

## 2. What to check (tick each one)
1. **Causality.** In `DemandLoad.window_st`, the window is `[t − w, t)`: `searchsorted(..., side='left')` at both ends, so a request at exactly `t` is excluded. Nothing reads requests after `t`.
2. **Same function on both sides.** Training (`train_ap.py`: `load_features.group_features(demand, grp, ac.ts)`) and serving (`sim_features.py`: `group_features(demand, feat_idx, acc.ts.physical)`) both call the same function on the same trace file (`demand_for_trace_kwargs` and `demand_for_trace` resolve to the same path).
3. **Off by default.** With the default feature subset (`meta+block+chunk`), no `--pf-feat-subset`, and `--ap-load-adapt-alpha` unset:
   - no new code path runs;
   - the `DemandLoad` series is not even built (the guard in `sim_cache.py` around `demand_load = None`).
4. **Nothing outside SCOPE_v2 §1 changes.** Check all of these are untouched:
   - eviction logic;
   - disk-time accounting and output metrics;
   - the episode model and the label rule (`threshold < target_wr`);
   - GBM hyperparameters and the train/test split.

   The `train.py` line only passes `--pf-feat-subset` (accepted in SCOPE_v2 §1a).
5. **Column-order guard.** `check_admission_feature_names` makes the simulator refuse a model whose `load`/`tod` columns are not where `collect_features` puts them.

## 3. Evidence already recorded (skim; no need to re-run)
- **`CP1.md`:** the full gate report.
- **G1, default equivalence** (`results/g1_summary.json`, `results/g1det_summary.json`, `results/g1_replay.json`), run overlay vs frozen on Region7 and Region6 sample 0:
  - RejectX and CoinFlip are bit-identical on all 425 result keys.
  - Baleen produces identical features, labels and models once the artifact's own randomness is pinned.
  - Running the same models through both simulators gives bit-identical results.
- **Parity** (`results/parity_summary.json`): `load` values from training equal serving's exactly, on 26,499 accesses.
- **Demand sanity** (`results/demand_vs_sim.json`): the series' 10-minute sums equal the simulator's own no-cache disk time on all 996 windows.
- **Rebuild check:** `rebuild_overlay.sh` rebuilds the overlay from the frozen tree + `PATCH.diff`, and the result is identical.

## 4. How to sign off
Append one line to `changes/SCOPE_v2.md` §1a and commit it:

`- G3 reviewed by <name> on <date>: PATCH.diff sha256 <first 12 chars of: sha256sum wp0_overlay/PATCH.diff> — <approved | changes requested: ...>`

If you request changes, the H3′ test stays blocked until they are made and G1 + parity are re-run.
