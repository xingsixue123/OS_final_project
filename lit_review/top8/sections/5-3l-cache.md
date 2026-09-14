### 5. 3L-Cache: Low Overhead and Precise Learning-based Eviction Policy for Caches (FAST'25)

- **Repo:** https://github.com/optiq-lab/3L-Cache — GPL-3.0; last commit 2025-08-09 (`134cd15`, "update 3LCache+"); 925 MB checkout, of which `data/` sample traces are 722 MB. It contains a vendored libCacheSim and a **modified LightGBM 2.2.2**.
- **What it is:** a learned per-object eviction policy, about 870 lines of C++ in `3LCache/`. It predicts each object's next arrival with a LightGBM model, and keeps overhead low with bidirectional sampling, batched eviction and automatic parameter tuning.
- **Paper eval setup:**
  - **Traces:** 4,855 traces from 8 public datasets (CloudPhysics 106, Tencent CBS 4,030, Alibaba 652, Twitter 54, …), 267 B requests.
  - **Baselines:** 12 policies, including LRB, GL-Cache and HALP.
  - **Sizes and metrics:** cache sizes 0.1% and 10%; byte and object miss-ratio reduction versus LRU; CPU overhead measured as a simulator-throughput ratio.
  - **Hardware:** a dual-Xeon server with 192 GB.
- **Reproduction target:** **Figure 6(a)+(e), CloudPhysics byte miss-ratio reduction versus LRU at small and large sizes.** The same runs also give Figure 8(a)/(e) and a CloudPhysics-only Figure 10 (CPU overhead). The claim: the largest reduction at nearly every percentile, at about 6.4× LRU's CPU, 94.9% less than LRB. CloudPhysics fits well: the public copy has exactly the paper's 106 traces in 9 GB.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| "Ubuntu 18.04, cmake 3.28.6" | README | Debian 12, cmake 3.25.1 | top-level CMake only needs ≥ 3.12, so fine |
| **Current version doesn't configure:** `cache/eviction/CMakeLists.txt:97-99` references `../../../../3LCache+`, one level above the repo | verified: that path doesn't exist; `../../../3LCache+` does | ❌ as shipped | one-line `sed` fix, or check out `fa5caa6` (the commit before 3LCache+ was added) |
| glib-2.0 dev | `CMakeLists.txt:142` | ❌ runtime only | conda-forge `glib` |
| zstd dev (required) | `CMakeLists.txt:150-159` | ❌ runtime only | conda-forge `zstd` |
| argp, OpenMP (libgomp) | — | ✅ | — |
| tcmalloc | `CMakeLists.txt:171-179` | missing, optional | conda `gperftools` or skip |
| `install_dependency.sh` (sudo apt; 3× `sudo make install`) | `scripts/install_dependency.sh:4-5,29,44,55` | ❌ | replace with user-prefix installs |
| **Modified LightGBM 2.2.2** (required for 3L-Cache and LRB) | non-standard C API: `LGBM_BoosterPredictForCSR` takes a `std::unordered_map` (`c_api.h`, verified) | ⚠️ must build the vendored copy | prebuilt conda/pip LightGBM **won't link**. Build `scripts/LightGBM` into `$HOME/local`; gcc 12 likely needs `#include <limits>` in ~5 files (`common.h` lacks it, verified), or use a conda gcc 9/10 |
| xgboost 2.0.0 (GL-Cache; on by default and required) | `CMakeLists.txt:26,187-190` | missing | `-DENABLE_GLCACHE=OFF` (GL-Cache isn't in the repo's scripts anyway), or build it into a prefix |
| HALP baseline | only a plot label | ❌ **not in the repo** (verified) | drop HALP from the figures |
| Python numpy, matplotlib + undeclared pandas, openpyxl, psutil | `requirements.txt`; scripts | user install | pip |
| Dockerfile | builds *upstream* libCacheSim, not this fork | not applicable | ignore |

**Data**

| dataset | size | subset needed |
|---|---|---|
| In-repo `data/` samples (57 CSVs truncated to 1 M / 100 K requests, plus a Tencent zip) | 722 MB | smoke test only; not comparable with the paper's cache sizes |
| CloudPhysics (oracleGeneral `.zst`, public S3 `2015_cloudphysics/`) | **106 traces, 9.0 GB** | ✅ target (Figures 6a/e, 8a/e) |
| Tencent CBS | 163 GB (378 large traces: 79 GB) | stretch: the only dataset with explicit numbers in the paper (Figure 6b: mean 11.6% vs LRB 8.6%) |
| Alibaba / Twitter (S3 copies are 10% samples) / Wiki / Tencent Photo / Meta | 2–152 GB each | not needed |
| Full 8-dataset corpus | ≈ 620 GB | exceeds disk |

**Hard filters** — H1 ✅ named in the paper and its Artifact Appendix · H2 ✅ with work: sudo appears only in the dependency script, and every dependency installs to a user prefix · H3 ✅ CPU-only; CPU overhead comes from simulator throughput, not perf counters · H4 ✅ for CloudPhysics (9 GB); ❌ full corpus (620 GB).

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | **2** | sudo-based one-liner; **current version doesn't configure** (bad `3LCache+` path); modified LightGBM 2.2.2 fork likely hits gcc-12 `<limits>` errors |
| dependency fit | 4 | glib/zstd headers via conda; LightGBM from the vendored copy; xgboost optional; the modified API rules out prebuilt packages |
| data fit | 4 | CloudPhysics has exactly the paper's 106 traces in 9 GB; the authors' preprocessed CSVs aren't published and the Twitter copies are 10% samples |
| hardware fit | 4 | Single-threaded sims; CloudPhysics and even Tencent fit in hours to a day or two; only disk limits the full corpus |
| repro scripts | 3 | `run_scripts.sh` (executor → collect → draw → Figures 6/8/10), but it reads only `.csv` from a hard-coded `../../data/`, looks up sizes by CSV name, omits LRB/GL-Cache/HALP, and has no download scripts |
| extensibility | 4 | Policy cleanly split into `lookup/admit/evict/sample/rank/train/prediction` in `3LCache/TLCache.cpp`; `3LCache+/` already shows how to add a variant (~5 lines of registration) |
| **total** | **21 / 30** | |

**Verdict: 🟡 DOABLE-WITH-WORK** · confidence medium (build issues checked by path resolution and headers; nothing compiled) · setup ≈2–3 person-days (1 dependencies + patches, 0.5–1 script adaptation to `.zst` and fractional sizes, 0.5 plots) · compute: CloudPhysics × 10 policies × 2 sizes ≈ 10–20 core-hours (2–4 h wall); +40–80 core-hours if LRB is included; Tencent stretch 79–163 GB disk, 100–300 core-hours.

**Key risks**
- **Broken CMake path at the current commit;** 3LCache+ also changed `TLCache.cpp`, so pick a version deliberately.
- **LightGBM fork:** non-standard API; gcc-12 compile fixes needed.
- **Preprocessing mismatch:** the S3 oracleGeneral traces may differ from the authors' unpublished CSVs, so compare rankings and relative reductions, using fractional sizes `0.001,0.1`.
- **Incomplete baselines:** HALP isn't implemented, GL-Cache needs xgboost, and LRB (~20× the CPU) dominates compute.
- **Machine contention skews Figure 10:** the executor launches 32 concurrent jobs, so run throughput passes with ≤ 16 jobs.
- **Garbled hardware in the paper:** "Xeon Gold 5128R" isn't a real part number; only the ratios matter.

**Where an add-on plugs in**
- **Policy hooks** in `3LCache/TLCache.cpp`: `train()` :12, `sample()` :63, `lookup()` :75, `admit()` :159, `rank()` :192, `evict()` :301/308, `evict_predobj()` :343, `prediction()` :383. These cover sampling, features, eviction ratio and retraining triggers.
- **Features and tunables** in `3LCache/TLCache.h`: `Meta` :57; `sample_rate`, `eviction_rate`, `reserved_space` ~:250-268; LightGBM `training_params` ~:297; `batch_size` :27.
- **New variant:** copy `3LCache/TLCache_Interface.cpp`, as `3LCache+/TLCacheN_Interface.cpp` does, and register it in `bin/cachesim/cache_init.h:141-149`, `evictionAlgo.h:131-133` and `cache/eviction/CMakeLists.txt:92-99`.
- **Experiment lists:** `3LCache/scripts/executor_libcachesim.py:66` and `libcachesim_result_collect.py`.

**Build route (not executed)**
1. `conda create -y -n 3lc -c conda-forge python=3.11 glib zstd gperftools pkg-config numpy matplotlib pandas openpyxl psutil awscli`
2. Fix the path: `sed -i 's#\.\./\.\./\.\./\.\./3LCache+#../../../3LCache+#' libCacheSim/cache/eviction/CMakeLists.txt`
3. Add `#include <limits>` to the ~5 LightGBM files; `cmake -S scripts/LightGBM -B scripts/LightGBM/build -DCMAKE_INSTALL_PREFIX=$HOME/local/3lc && cmake --build … -j32 && cmake --install …`
4. `cmake -S . -B _build -DCMAKE_BUILD_TYPE=Release -DENABLE_GLCACHE=OFF -DENABLE_LRB=ON -DENABLE_TESTS=OFF -DCMAKE_PREFIX_PATH="$HOME/local/3lc;$CONDA_PREFIX" && cmake --build _build -j32`
5. Smoke test on the bundled Tencent sample; expect miss ratio ≈ 0.3380 (README.md:75)
6. `aws s3 sync --no-sign-request s3://cache-datasets/cache_dataset_oracleGeneral/2015_cloudphysics/ ~/traces/cloudphysics/` (9 GB)
7. Run 10 policies × `0.001,0.1` per trace; patch the executor to glob `*.zst` and the collector to key by trace name; plot the CloudPhysics panels; re-run throughput with ≤ 16 jobs for Figure 10
