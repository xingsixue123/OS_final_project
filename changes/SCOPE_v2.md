# PeakBaleen scope v2 (phase 2): the swap boundary widens by one signal

**Status:** agreed by Sixue Xing (captain) on 2026-09-29, pending confirmation by Ching-Hao Chiu and Jie Fu. **v1 (`SCOPE.md`) still governs every phase-1 result**; v2 applies only to work under `changes/2_deployable_peak/`.

**Why v2 exists.** In phase 1, peak-aware labels could not survive distillation into Baleen's GBM:
- Retention was about 0 (`harness_eval/RESULTS.md`, `explore/q3/RESULTS.md`).
- The cause is that the model has no time or load signal.
- The proposal (§4.1, H3) always planned *causal load features* and a *load-adaptive ML-When gate*, but v1 excluded them. v2 lets exactly those in, and nothing else.

## 1. What may change (in addition to v1's selection `Policy`)
All changes live in an **overlay copy** of the BCacheSim package: `changes/2_deployable_peak/overlay/BCacheSim/`. It is copied from the frozen `ddeb2d8`, and our edits are one reviewed patch file (`overlay/PATCH.diff`). The frozen tree in `0_reproduce/baleen_code/` is never touched.

The patch may only do the following:

1. **Add one new feature group, `load`, computed identically in training and serving:**
   - **In training:** a new branch in `episodic_analysis/train_ap.py`, next to the existing `feat_dynamic_b` / `feat_metadata` rows.
   - **In serving:** `cachesim/sim_features.py` (`count_feat`, plus the feature assembly) and the existing `collect_features` path used by `sim_cache.py`.
   - **What the group contains:**
     - trailing *demand-side* load, i.e. the disk-head time of all requests seen in the last 10, 30 and 60 minutes, normalised by the sampling ratio;
     - optionally, hour of day as sin/cos.
   - **Demand-side load is required,** not backend (post-cache) load. It comes from the request stream only, so it is identical in training and serving and independent of the admission policy, which rules out train/serve skew.
   - The group is enabled through the existing `--ap-feat-subset` string (e.g. `meta+block+chunk+load`). The default subset must behave exactly as before.
2. **Optionally make the admission threshold load-adaptive** in `NewMLAP`: θ_t = θ · g(load_t), with a fixed shape parameter. The base θ is still converged to the target write rate. It is off by default.
3. **Optionally add the same `load` group to the prefetch models** (ML-Range and ML-When), which is the proposal's load-adaptive gate. The default is unchanged.

## 2. What stays frozen
- **The simulator:** its datapath, eviction, prefetch mechanics, disk-time accounting and output fields.
- **The episode model** and the label rule `threshold < target_wr`.
- **GBM training:** hyperparameters, train/test split and eviction-age handling.
- **Data and operating point:** traces, sampling, 366.475 GB cache, 35.599 MB/s write rate.
- **Evaluation:** `PeakServiceTimeUtil1`, and matched write rate within ±1%.

## 1a. Clarifications recorded at checkpoint CP1 (2026-10-01, coordinator review of `wp0_overlay/PATCH.diff`, 9 files, +217/−6)
- **`load` uses GET demand only.** That is exactly the simulator's no-cache counterpart of `PeakServiceTimeUtil1`; PUTs are excluded.
- **Item 1.3 needs one plumbing line in `episodic_analysis/train.py`,** which passes `--pf-feat-subset` to the prefetch trainer. Accepted as part of 1.3; the default is unchanged.
- **Known skew, arm E only.** The prefetch-model `load` is taken at an episode's first access in training, but at the triggering access in serving. The admission-model `load` has no such skew; the parity test found exact equality on 26,499 accesses.
- **Retrain variance** keeps the artifact's own nondeterminism (`imap_unordered`), with ≥3 retrains per configuration, the same as every baseline.
- **Feature subsets** must be written in canonical order, e.g. `meta+block+chunk+load+tod`.
- **G1 and parity passed** (`wp0_overlay/CP1.md`).
- **Review status:**
  - G3: coordinator review done; teammate review still required before any test-set (WP3) run.
  - Rebuilding the overlay: `wp0_overlay/rebuild_overlay.sh` (verified identical).
- **CPU topology.** Logical CPUs k and k+12 are the two hyperthreads of one physical core. While timing runs hold cores 0–7, other work must avoid 12–19 and use `8-11,20-23` only.

## 3. Fairness gates (must pass before any v2 result counts)
- **G1: default equivalence.** With the default feature subset and no adaptive threshold, the overlay reproduces the frozen artifact **bit-exactly** on the dev instances. That means RejectX, CoinFlip and Baleen at a fixed seed, and each Baleen retrain's labels and model file.
- **G2: same pipeline for every method.** Every method in a comparison runs through the overlay, including "Baleen + load features" as its own baseline.
- **G3: the diff is reviewed.** `PATCH.diff` is reviewed by one teammate and committed before any held-out run.
