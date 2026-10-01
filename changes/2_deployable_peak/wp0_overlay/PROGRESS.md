# Track A (phase 2) progress: WP0 overlay

All times local (EDT). Area: `2_deployable_peak/wp0_overlay/` (+ empty `2_deployable_peak/wp2_deployed/` for later).

- 2026-10-01 14:36 `.leak_marker` touched; `env.sh` (sandboxed HOME/XDG/TMPDIR/pip/conda/MPL/numba/torch caches,
  CONDA_REGISTER_ENVS=false, PYTHONNOUSERSITE=1, PYTHONDONTWRITEBYTECODE=1). `check_frozen.sh`: frozen OK (94 files).
- 14:36 overlay = `cp -a` of the frozen `0_reproduce/baleen_code/BCacheSim` (ddeb2d8) minus its gitfile `.git`;
  `work/` (BCacheSim -> overlay) and `work_frozen/` (BCacheSim -> frozen) with the same relative layout; `data` ->
  `1_literature_review/explore/common/data` (read-only symlink, 70 traces).
- 14:40-14:46 patch implemented (load/tod groups, adaptive threshold, prefetch-model load features); unit check of the
  demand series vs a naive per-request sum (Region7, 12,000 values: max rel diff 7e-16).
- 14:47 G1 launched (`src/g1.py --frozen-repeat`): static baselines + frozen/overlay trainings with dumps + cross sims.
- 14:50 RejectX/CoinFlip (both traces): frozen vs overlay fully bit-identical (425 result keys, all per-window series).
- 14:48-15:00 G1 trainings (frozen, overlay, frozen repeat; both traces; ~33 s each, interleaved with Track B on the
  shared lock) with read-only dumps; finding: the frozen training itself is not deterministic (episode order from
  Pool.imap_unordered -> row order, block split, score-tie order at the label boundary, model bytes).
- 14:55-15:15 model-file replay (`src/g1b.py`): GBMs retrained from one dump with frozen x2 / overlay x2 -> all 8 model
  files byte-identical on both traces (and equal to the original frozen training's files).
- 15:00-15:20 parity + smoke (`src/parity.py`): `meta+block+chunk+load` trains and simulates end to end; load values
  exact on 26,499 training accesses (79,497 values); load+tod and prefetch-model load+tod also exact; alpha=0 adaptive
  path bit-identical to frozen.
- 15:05-15:38 G1-det (`src/g1det.py`): imap_unordered pinned in the launcher for both code bases -> frozen x2 and overlay
  x2 identical in every row/column/label/split/model byte; end-to-end frozen pipeline == overlay pipeline (both traces).
- 15:39 cross-sims of the same model files bit-identical (both traces, both model sets); G1 verdict recomputed with the
  run-to-run criterion (`results/g1_summary.json`): PASS both traces.
- 15:40 leak check + `check_frozen.sh` (frozen OK, 94 files); `PATCH.diff` 9 files +217/-6; `CP1.md` written.
  **STOP at CP1** (WP2 not started).
