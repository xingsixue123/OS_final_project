### 8. Learning-Augmented Heuristics: Simple Yet Smart, Robust and Interpretable Cache Eviction — S4-FIFO (OSDI'26)

- **Repo:** https://github.com/cacheMon/osdi26-s4-fifo — Apache-2.0; last commit 2026-05-12 (`000095f`); 672 KB checkout, no LFS.
  - **Submodules:** libCacheSim fork `haochengxia/libCacheSim@1f62efc` (GPL-3.0, 128 MB) and CacheLib fork `williamnixon20/CacheLib@72bb810`.
- **What it is:** S3-FIFO with 5 cache-level settings: small-queue ratio, ghost ratio, two promotion thresholds, and a skip ratio. After a warmup it collects 73 cache-level features, and an offline-trained LightGBM classifier makes **one** prediction that picks 1 of 18 settings bundles. The data path stays O(1) FIFO queues; inference is exported to C/C++ with m2cgen.
- **Paper eval setup:**
  - **Traces:** 5,175 production traces from 14 sources, split 4,140 train / 1,035 test ("randomly"); cache sizes 0.1/1/10%.
  - **Labels:** grid search over 168 settings combinations.
  - **Test protocol:** run defaults for 20% of the trace, predict once, then either switch for the remaining 80% ("v1 online") or apply the prediction to the whole trace ("v2 retrospective").
  - **Baselines:** S3-FIFO, LIRS, ARC, LRB, 3L-Cache, LHD, GL-Cache, LeCaR.
  - **Throughput:** CacheBench at 48 threads.
  - **Hardware:** a 20-node × 32-core cluster.
- **Reproduction target:** **Figure 6(a), mean miss-ratio reduction versus FIFO at the large (10%) cache.** The claim: +26% over S3-FIFO, +8% over 3L-Cache, and v2 within 0.2% of the offline grid-search best. Figure 7a/c (worst case / 10th percentile) comes from the same runs. This has to be **scaled to a public-trace subset with a retrained model** (see Data and Key risks).

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| gcc ≥ 11, cmake ≥ 3.12 | README; `libCacheSim/CMakeLists.txt:1` | ✅ | builds with **`-Werror`** (`CMakeLists.txt:92`); add `-Wno-error` if gcc 12 complains |
| glib-2.0 dev, zstd dev | `CMakeLists.txt:123-150` | ❌ runtime only | conda-forge `glib zstd pkg-config` |
| argp; tcmalloc optional | `CMakeLists.txt:135,156` | ✅ / skip | — |
| `sudo apt install …`; Docker image | README; `install_dependency.sh`; Dockerfile | ❌ | replay the steps via conda |
| LightGBM / XGBoost C libraries (only for 3L-Cache/LRB/GL-Cache baselines) | `CMakeLists.txt:171-194` | missing | conda-forge `liblightgbm libxgboost` |
| Python: numpy, pandas, sklearn, xgboost, lightgbm, joblib, m2cgen, torch (unpinned) | `requirements.txt` | user install | py3.11 env; CPU torch is enough |
| Cluster task runner: hard-coded `/mnt/cfs/…`, distComp format, scp to node1..19 | `grid_search/yield_tasks.py:7-9`, `apply.sh` | ⚠️ unusable as-is | rewrite paths; `parallel -j30` |
| **Intermediate CSVs** (`features_20pct.csv`, `cleaned/*/grid_full.csv`, `baselines.csv`) | `analysis/.gitignore` (verified) | ❌ **not released** | regenerate by simulation and write the missing glue (log dumps → CSV) |
| **The paper's trained model** (20 trees, depth 9) | paper §4.4.3 | ❌ **not released** | only a "lite" 5 × 50-tree, depth-4 model exists in the CacheLib fork (47% top-1). Retrain |
| **Online inference inside the simulator** | `REPRODUCTION.md:106,154` suggests `s4fifo -e collect-features` predicts | ❌ **absent**: `S4FIFO.c` only snapshots features at PREDICTION and calls an optional callback, and `S4FIFO_set_phase_callback` has **no callers** (verified) | v2 can be scored by table lookup; v1 needs ~100 lines of C (model header + queue resize) |
| CacheLib throughput (Figure 8) | README (`sudo … install-system-deps`) | ❌ sudo step; 48 vs 32 threads | optional; getdeps from source is fragile |
| Label-generation compute (paper: 20 × 32 cores) | paper | 1 × 32 threads | fits CPU-wise at ~1/20 throughput, so use a trace subset |

**Data** (public `cache-datasets` S3 bucket, oracleGeneral)

| dataset | size | subset needed |
|---|---|---|
| CloudPhysics (104) + MSR (14) + Meta Storage (5) + Meta CDN (3) | **≈ 12.6 GiB**, ~2.8 B requests | ✅ core subset (126 traces) |
| Tencent CBS (3,370) | ≈ 142 GiB | add ~500 random traces (≈ 21 GiB) so the 18-class model has enough training data; the name mapping `tencentBlock.nsN` ↔ `tencentBlock_N` is unverified |
| Alibaba (552) | ≈ 93 GiB | optional |
| Twitter sample10, Meta KV, Tencent Photo, Wiki | 50–134 GiB each | skip |
| CDN1 (Akamai, 163), CDN2 (890), FIU, Systor | ~22% of the corpus | ❌ **private / on request** |
| Sample traces in repo | 3–62 MB | smoke test (miss ratio ≈ 0.48) |
| All public traces at paper scale | ≈ 560 GiB, ≈ 11 days on this box | ❌ doesn't fit |

**Hard filters** — H1 ✅ official repo, Apache-2.0, public pinned submodules · H2 ✅ user-space cmake + conda; sudo only for optional CacheLib · H3 ✅ CPU-only trace simulation; paper scale is only a time problem · H4 ✅ at subset scale; ❌ for exact numbers (private CDN traces, and the model, labels and feature CSVs are unreleased).

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | One documented cmake/make with common libraries; `-Werror` + conda glib add friction; CacheLib optional |
| dependency fit | 4 | glib/zstd headers trivial via conda; apt lines skipped |
| data fit | 3 | 12–35 GiB public subset is enough for a scaled target, but ~22% of paper traces are private and no labels, features or model are released |
| hardware fit | 3 | Runs, but label generation used 20 × 32 cores; paper scale ≈ 2 weeks here |
| repro scripts | **2** | Training and plot scripts exist but read unreleased CSVs; task generators hard-code `/mnt/cfs`; the log→CSV glue is missing; the grid JSONs (54/72/72 combos) don't match the paper's 168; docs reference missing scripts; **the simulator has no inference path** |
| extensibility | 4 | Clean phase state machine in `S4FIFO.c`, separate feature header, table-driven registration, single training script with explicit config/cost-matrix/split functions |
| **total** | **20 / 30** | |

**Verdict: 🟡 DOABLE-WITH-WORK** · confidence medium · setup ≈**4–6 person-days** (0.5 build, 0.5 data, 1.5–2 rebuilding the 168-combo grid + CSV glue, 1 training/eval/plots, +1–1.5 for true v1 online switching in C) · compute: 126 traces × 168 combos × 2 sizes ≈ 9.4e11 simulated requests ≈ 6 h on 30 jobs; +500 Tencent ≈ +11 h; 0.5–1.5 machine-days, CPU only, 15–40 GB disk.

**Key risks**
- **`s4fifo` in the simulator never runs a model** (verified), so v1 "online" numbers need new code.
- **Three inconsistent models:**
  - Paper: 20 trees, depth 9.
  - Training script: an ensemble of 20 LightGBM classifiers with 200–580 trees, depth 6–9, ~75 features.
  - Released: only the lite 5 × 50-tree model.
- **The split contradicts "randomly split"** (verified). `train_xgb_18class.py:295-329` forces ~30 worst-case traces (where S4-FIFO/ARC/LeCaR did worst) into **training** and hand-picked "showcase" traces into **test**, so the Figure 7 robustness claim may not survive a truly random split. **This is itself a strong course-project angle.**
- **Private traces are ~22% of the corpus,** and accuracy depends on thousands of training traces, so a subset-trained model will likely fall short of +26%. Compare against the grid-search offline best to separate data effects from method effects.
- **Doc drift:** the 168 grid must be rebuilt (7 small ratios × ghost {0.9, 3, 6} × 2 × 2 × 2), and the trace filters differ (100K vs 1M objects).
- **`-Werror` build risk;** CacheLib throughput is the riskiest part.

**Where an add-on plugs in**
- **`S4FIFO.c`:**
  - `S4FIFO_transition_phase` (:153), PREDICTION branch: call an m2cgen C model and resize the queues. **This is the missing online step.**
  - `S4FIFO_update_phase` (:187) with `prediction-interval`: periodic or drift-triggered re-prediction.
  - `S4FIFO_parse_params` (:451): new settings.
- **`S4FIFO.h`:** `S4FIFO_base_params_t` (:40), `S4FIFO_shared_init_queues` (:109) for runtime queue resizing. **`S4FIFO_features.h`:** new or sampled features.
- **Learning side:** `analysis/train_xgb_18class.py` (`SELECTED_CONFIGS` :15-34, `engineer_features` :82, `split_by_trace` :167, `build_empirical_cost_matrix` :402), `create_grid_optimal.py`, `export_models_multilang.py`.
- **Real cache:** CacheLib fork `cachelib/allocator/MMS4FIFO.h`, `S4FIFOLightGBMPredictor.h`.

**Build route (not executed)**
1. `git submodule update --init libCacheSim` (the pinned checkout already exists at `../libCacheSim`)
2. `conda create -y -n s4fifo -c conda-forge python=3.11 glib zstd gperftools pkg-config ninja liblightgbm libxgboost lightgbm xgboost pandas numpy scikit-learn matplotlib seaborn joblib parallel awscli && pip install m2cgen`
3. `cmake -S libCacheSim -B libCacheSim/_build -G Ninja -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DCMAKE_BUILD_RPATH=$CONDA_PREFIX/lib -DENABLE_3L_CACHE=ON -DENABLE_LRB=ON` (+ `-Wno-error` if needed); `ninja -C libCacheSim/_build`
4. Smoke test: `cachesim libCacheSim/data/cloudPhysicsIO.vscsi vscsi s4fifo 1GB -n 100000` (≈ 0.48), then `s4fifo-base`, `s3fifo`
5. `aws s3 cp --no-sign-request --recursive` CloudPhysics, MSR, metaStorage and metaCDN (+ ~500 Tencent)
6. Patch `grid_search/yield_tasks.py`: local paths, the 168-combo grid, sizes {0.001, 0.1}; pipe to `parallel -j30`
7. Patch `feature/yield_feature_tasks.py` (20%, local paths); run the baselines with `parallel -j30 cachesim …`
8. Write the glue (aggregate → `cleaned/*/grid_full.csv`, `baselines.csv`, `features_20pct.csv`); `create_grid_optimal.py`
9. `train_xgb_18class.py` twice: as shipped, and with the forced train/test lists emptied (true random split); `plot_cleaned_data.py` → Figures 6/7
10. Optional v1 online: m2cgen export → wire into `S4FIFO_transition_phase`, rebuild, rerun test traces
