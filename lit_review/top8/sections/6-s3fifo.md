### 6. FIFO Queues are All You Need for Cache Eviction — S3-FIFO (SOSP'23)

- **Repo:** https://github.com/Thesys-lab/sosp23-s3fifo — last commit 2024-06-12 (`6bc49d9`); 1.0 GB checked out, of which `result/` is 760 MB.
  - **License:** Apache-2.0 per the README; the bundled libCacheSim is GPL-3.0.
  - **Throughput prototype:** a separate repo, `Thesys-lab/cachelib-sosp23`.
- **What it is:** eviction with three FIFO queues: a small queue S (10% of the cache), a main queue M, and a ghost queue G. Quick demotion through S keeps one-hit wonders out of M. The artifact is a libCacheSim snapshot with `cache/eviction/S3FIFO.c` and about 20 baselines, plotting scripts, **precomputed per-trace results for all 14 datasets (verified)**, and a Redis-based multi-node job runner.
- **Paper eval setup:**
  - **Simulation:** 6,594 traces from 14 datasets, of which 3 are proprietary (CDN1, CDN2, SocialNetwork1): 856 B requests, cache sizes of 10% and 0.1%, reported as miss-ratio reduction versus FIFO.
  - **Compute:** about 1 M core-hours on CloudLab.
  - **Figure 8 throughput:** CacheLib on Intel nodes with turbo off, 1–16 threads.
- **Reproduction target:** **Figures 6a/7a (large cache, 10%)**, recomputed on the public, unsampled block datasets MSR (14 traces), FIU (10) and CloudPhysics (106), 130 traces in total. The claim: S3-FIFO has the largest miss-ratio reduction versus FIFO across percentiles and the lowest mean miss ratio per dataset. **Our outputs can be diffed per trace against the shipped `result/cachesim/{MSR,FIU,Cloudphysics}/*.txt`.** Stretch goal: Table 2 (small-queue size sweep on `msr_hm_0`).

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| cmake ≥ 3.2; C11/C++17 | `libCacheSim/CMakeLists.txt:1,121` | ✅ cmake 3.25, gcc 12.2 | as-is (gcc 12 untested, low risk) |
| glib-2.0 dev headers (required) | `CMakeLists.txt:140` | ❌ not on system (verified) | `conda install -c conda-forge glib pkg-config` |
| zstd (fatal if missing) | `CMakeLists.txt:150-156` | only in miniconda base | conda-forge `zstd` in the env |
| tcmalloc | `CMakeLists.txt:167-175` | missing, optional | conda `gperftools` or skip |
| xgboost / LightGBM | `install_dependency.sh` (`sudo make install`) | not needed (GLCache/LRB are off) | skip |
| One-line dependency installer | `README.md:28` → `install_dependency.sh` | ❌ on Debian it falls into the `sudo yum` branch | use the conda route instead |
| artifact-evaluation `apt` line (glib, boost, zstd) | `doc/AE.md:8` | needs sudo; boost is unused | conda glib + zstd |
| numpy + matplotlib | `requirements.txt` | trivial | pip/conda |
| Plot script requires all 14 dataset dirs | `scripts/libCacheSim/plot_miss_ratio.py:48-75` | ⚠️ small edit | edit its `datasets` list |
| Exact flags for all 14 algorithms in Figure 6 | `AE.md:200` lists only 8 | ⚠️ undocumented | reconstruct from `cache_init.h`, `cli_parser.c` |
| distComp multi-node runner (Redis, parallel-ssh) | `distributedComputation/` | not needed | loop traces locally; `cachesim` already uses all cores |
| Figure 8: CacheLib with folly/fbthrift and ~30 apt packages; turbo/MSR control | `cachelib-sosp23/contrib/*`, `mybench/turboboost.sh` | ❌ brittle on Debian 12 without apt; turbo toggle needs root | skip; at best qualitative |

**Data** (CMU PDL public FTP, `.zst`, read directly)

| dataset | size | subset needed |
|---|---|---|
| MSR (14 files, verified) | 1.6 GB | ✅ target |
| FIU (10) | 1.3 GB | ✅ target |
| CloudPhysics (106) | 8.6 GB | ✅ target |
| Meta CDN / wiki_2019t | 2.2 GB / 1.9 GB | optional |
| Twitter (54) | 1.6 TB full; 141 GB sample10; 14 GB sample100 | skip. **The artifact docs' Twitter URL now returns 404 (verified)**; files moved to `twitter/sample10/` |
| Alibaba / Tencent block, Meta KV, TencentPhoto, SYSTOR | 35–230 GB each | skip |
| CDN1, CDN2, SocialNetwork1 | proprietary | ❌ precomputed results only |
| Precomputed results | 760 MB, in repo | ground truth for the diff |

Target total ≈ **11.5 GB**; the full corpus is ≈ 2.5 TB.

**Hard filters** — H1 ✅ official repo named in the paper · H2 ✅ simulator (sudo only in the dependency script and the throughput tooling); ❌ exact Figure 8 conditions · H3 ✅ single-threaded C simulations; the 130-trace target fits in a day (paper scale is a budget limit, not a hardware mismatch) · H4 ✅ for the 11.5 GB subset; the full corpus is ~2.5 TB and 3 datasets are proprietary.

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | Simulator is `cmake .. && make -j` with 3 small libraries; only the dependency script is broken off Ubuntu; CacheLib is heavy |
| dependency fit | 4 | glib, zstd and gperftools from conda-forge; the Figure 8 folly stack is the weak spot |
| data fit | 3 | Block datasets are small (11.5 GB target), but the full corpus is 2.5 TB and 3 datasets are proprietary |
| hardware fit | 4 | Single-core sims fit easily; paper-scale sweeps and Intel/turbo-off throughput can't be matched |
| repro scripts | 4 | `AE.md` gives per-figure commands, plot scripts and precomputed results; missing are the full Figure 6 command line, a subset-friendly plot script, and one stale URL |
| extensibility | 5 | Pluggable per-algorithm interface with a written recipe (`libCacheSim/doc/advanced_lib_extend.md`), separate admission modules, and `-e key=value` parameter parsing |
| **total** | **24 / 30** | |

**Verdict: ✅ DOABLE (simulator); Figure 8 CacheLib throughput is DOABLE-WITH-WORK and not recommended** · confidence high · setup ≈2 person-days (0.5 build, 1 reconstructing flags, names and subset plots, 0.5 data) · compute: MSR+FIU+CloudPhysics ≈ 3 B requests × 14 algorithms × 8 sizes ≈ 50–150 core-hours ≈ 2–6 h on 32 threads, 12 GB disk.

**Key risks**
- **Undocumented algorithm flags.** Figure 6 needs 14 algorithms (window-size variants of W-TinyLFU, 4-segment SLRU, B-LRU, FIFO-Merge), and a wrong flag gives mismatched numbers.
- **Algorithm output names may differ** from those in the shipped results, and the loader silently skips traces with missing algorithms, which could quietly shrink the sample.
- **130 traces give different percentile shapes than 6,594**, even when the per-trace numbers match.
- **Conda glib/zstd may conflict with system libraries**, so set an rpath.
- **Twitter can't be matched per trace** without the full 1.6 TB traces.
- **Shared machine:** the largest CloudPhysics runs may need fewer threads.

**Where an add-on plugs in**
- **S3-FIFO variant:** `libCacheSim/cache/eviction/S3FIFO.c`. Key functions: `S3FIFO_evict_fifo()` (promotion test `freq >= move_to_main_threshold`), `S3FIFO_evict_main()` (reinsertion), `S3FIFO_find()` / `S3FIFO_insert()` (ghost hit → admit to M), and `S3FIFO_parse_params()` (`-e fifo-size-ratio=…,ghost-size-ratio=…,move-to-main-threshold=…`).
- **Registration:** `cache/eviction/CMakeLists.txt`, `include/libCacheSim/evictionAlgo.h`, `bin/cachesim/cache_init.h`.
- **Per-object metadata:** the union in `include/libCacheSim/cacheObj.h` (next to `S3FIFO_obj_metadata_t`).
- **Admission filters:** `cache/admission/{bloomfilter,prob,size}.c`, run with `cachesim --admission`.
- **Instrumentation:** `TRACK_EVICTION_V_AGE` / `TRACK_DEMOTION` in `include/config.h`. The flash-tier simulator is in `bin/SOSP23/flash`.

**Build route (not executed)**
1. `conda create -y -n s3fifo -c conda-forge python=3.11 glib zstd gperftools pkg-config numpy matplotlib && conda activate s3fifo`
2. `cd repo/libCacheSim && mkdir -p _build && cd _build && PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig cmake .. -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DCMAKE_BUILD_RPATH=$CONDA_PREFIX/lib && make -j32`
3. Smoke test: `./bin/cachesim ../data/trace.oracleGeneral.bin oracleGeneral fifo,lru,s3fifo 0.1 --ignore-obj-size 1`
4. `wget -r -np -nd -A '*.zst'` MSR, FIU and CloudPhysics from `ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/` (~11.5 GB)
5. Sanity check: run `cachesim` on `msr_hm_0` and diff against `result/cachesim/MSR/hm_0.IQI.bin.txt`
6. Run all 14 algorithms × 8 sizes per trace; normalize names; restrict `plot_miss_ratio.py` to `["FIU","MSR","Cloudphysics"]`; compare against the same script on the shipped results for the same 130 traces
