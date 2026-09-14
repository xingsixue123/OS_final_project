### 4. SIEVE is Simpler than LRU: an Efficient Turn-Key Eviction Algorithm for Web Caches (NSDI'24)

- **Repo:** https://github.com/cacheMon/NSDI24-SIEVE — last commit 2024-08-01 (`0861f82`), 204 MB, C/C++/Python.
  - **License:** Apache-2.0 at the top level; the bundled libCacheSim copy is GPL-3.0.
  - **Official:** the paper points to this repo.
- **What it is:** a FIFO queue with a "visited" bit and a moving hand that either clears the bit or evicts. It is simpler than LRU yet has a lower miss ratio. The repo contains a libCacheSim snapshot with SIEVE (`cache/eviction/Sieve.c`, 286 lines, verified) and all the baselines, plus links to 5 production libraries patched with SIEVE: groupcache, mnemonist, lru-rs, lru-dict and CacheLib.
- **Paper eval setup:**
  - **Traces:** 1,559 traces from 7 datasets. CDN1 (1,273 traces) and CDN2 (219) are **proprietary**. The public ones are Twitter KV, Meta KV, Meta CDN, Wiki CDN and Tencent Photo.
  - **Miss ratio:** libCacheSim on CloudLab nodes; cache sizes of 0.1% and 10% of unique objects; reported as miss-ratio reduction versus FIFO.
  - **Throughput:** a CacheLib prototype on a 2-socket Xeon at 1–16 threads, with turbo off and threads pinned to one NUMA node.
- **Reproduction target:** **Figure 4(a)/(b), miss-ratio reduction versus FIFO on the public Meta KV, Meta CDN, Wiki and Tencent datasets.** The claim: at the large cache size (10%), SIEVE beats all 10 other algorithms on all four datasets. All 11 algorithms exist in the snapshot. Figures 3 and 5 depend on the proprietary CDNs, and Figure 6 (throughput) needs the full CacheLib/folly build.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| cmake ≥ 3.12, C/C++17 | `libCacheSim/CMakeLists.txt:1,12` | ✅ cmake 3.25.1, gcc 12.2 | as-is |
| GLib 2 dev headers, required | `CMakeLists.txt:141` | ❌ not on system (no `/usr/include/glib-2.0`, no `.pc`; verified) | `conda install -c conda-forge glib pkg-config` (glib 2.88 available, verified) |
| zstd (on by default; reads `.zst` traces) | `CMakeLists.txt:150` | headers only in conda | conda-forge `zstd` |
| argp | `CMakeLists.txt:146` | ✅ in glibc | as-is |
| tcmalloc (optional, speed only) | `FindTcmalloc.cmake` | missing | conda `gperftools`, or skip |
| `install_dependency.sh` | 6 × `sudo` (verified) | ❌ unusable as written | **don't run it**; the conda route above replaces it |
| README build path | `README.md:22` (wrong dir) | doc bug | build in `libCacheSim/_build` |
| numpy/matplotlib for plots | `requirements.txt` | user install | conda |
| Hard-coded plot paths (`/disk/data`, `/disk/cphy/result/`) | `scripts/plot_mrc_size.py:182` | ⚠️ | edit or write own driver |
| Figure 6: CacheLib fork (folly/fbthrift pinned) with ~20 apt `-dev` packages; turbo-boost toggle | `cachelib-sosp23/contrib/*`, `mybench/turboboost.sh` | ❌ heavy / needs root | skip Figure 6; absolute throughput isn't comparable anyway |

**Data** (public oracleGeneral `.zst` from the `cache-datasets` S3 bucket / CMU FTP; read directly without decompressing)

| dataset | size | subset needed |
|---|---|---|
| Meta CDN (3 traces) | **2.2 GB** (verified by HEAD) | all 3 |
| Meta KV | 67 GB in the bucket today, but 2 files are dated 2023-12/2024-01, **later than the paper**; which 5 files the paper used is unclear | minimum: `meta_kvcache_traces_1` (1.7 GB) |
| Wiki CDN (3) | 53.6 GB | minimum: `wiki_2019t` (2.0 GB) |
| Tencent Photo (2) | 72 GB | optional |
| Twitter KV (54) | 1.6 TB full; S3 has only 10% samples (152 GB) | not needed for Figure 4 |
| CDN1 / CDN2 | proprietary | ❌ unobtainable |
| Zipf smoke-test trace | 2.8 MB, in the repo | smoke test |

Minimum partial Figure 4 ≈ **6 GB**; full Figure 4 ≈ 150–195 GB of the 253 GB free.

**Hard filters** — H1 ✅ official repo named in the paper · H2 ✅ for the simulator (the only sudo is the dependency script, replaced by conda); ❌ for faithful Figure 6 (turbo toggle, apt prerequisites) · H3 ✅ CPU-only, single node · H4 ✅ with caveats: the Meta KV file set has drifted since publication, and CDN1/CDN2 are unobtainable.

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | One plain CMake build; the documented dependency step is sudo-based and the README path is wrong |
| dependency fit | 4 | Only GLib dev and zstd are missing, both on conda-forge; the Figure 6 CacheLib stack is heavy |
| data fit | 3 | Public; minimum 6 GB, but full Figure 4 is 150–195 GB, the Meta KV set is ambiguous, and 2 datasets are proprietary |
| hardware fit | 4 | Simulator runs at paper scale per trace; Figure 6 needs a 2-socket node with turbo off |
| repro scripts | 2 | Only generic `cachesim` + `plot_mrc_size.py`; the Figure 4 plot script is left over from S3-FIFO (SIEVE missing, hard-coded paths), so the aggregation must be written by hand |
| extensibility | 5 | Function-pointer cache interface (`include/libCacheSim/cache.h:74-106`): a new policy is one `.c` file plus 3 registration lines |
| **total** | **22 / 30** | |

**Verdict: ✅ DOABLE (simulator, Figure 4); Figure 6 throughput is not realistically reproducible** · confidence high for build and run, medium for matching Figure 4 exactly · setup ≈1–2 person-days (0.5 day build + smoke test, 0.5–1 day Figure 4 driver) · compute: 6 GB subset < 1 h on 16 threads; full Figure 4 ≈ 0.5–1 day, tens of GB of RAM on Tencent.

**Key risks**
- **Meta KV file set drifted:** those points in Figure 4 may not match the paper.
- **The libCacheSim snapshot isn't pinned to an upstream commit.** Upstream has since changed algorithms and defaults, so use the snapshot for fidelity. gcc 12 with conda GLib is untested.
- **The FIFO-baseline formula and the Figure 4 aggregation must be re-implemented.**
- **Large traces at 10% cache size may need fewer threads** to bound memory.
- **GPL-3.0 applies to the libCacheSim code**, which matters only if modified code is redistributed.

**Where an add-on plugs in**
- **New eviction policy:** copy `libCacheSim/cache/eviction/Sieve.c` (implement `init/get/find/insert/to_evict/evict/remove`), declare it in `include/libCacheSim/evictionAlgo.h`, add a name branch in `bin/cachesim/cache_init.h`, and add it to `cache/eviction/CMakeLists.txt`.
- **Per-object metadata** (for example a multi-bit counter instead of the visited bit): `include/libCacheSim/cacheObj.h:126`. A frequency-aware variant already exists at `Sieve.c:165`.
- **Admission add-on** (like B-LRU): `cache/admission/*.c`, registered in `admissionAlgo.h`, run with `cachesim -a <name>`.
- **Tests:** `test/test_evictionAlgo.c` (`test_Sieve`).

**Build route (not executed)**
1. `conda create -y -n sieve -c conda-forge python=3.11 glib zstd pkg-config gperftools numpy matplotlib && conda activate sieve`
2. `cd repo/libCacheSim && mkdir -p _build && cd _build`
3. `PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DENABLE_TESTS=OFF -DCMAKE_INSTALL_RPATH=$CONDA_PREFIX/lib -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON && make -j32`
4. Smoke test: `./bin/cachesim ../data/trace.oracleGeneral.bin oracleGeneral fifo,lru,clock,sieve 0 --ignore-obj-size 1`
5. Download Meta CDN ×3 + `wiki_2019t` + `meta_kvcache_traces_1` (~6 GB)
6. For each trace: `cachesim $t oracleGeneral fifo,sieve,arc,wtinylfu,twoq,lirs,lhd,cacheus,hyperbolic,clock,lru 0.001,0.1 --ignore-obj-size 1 --num-thread 16`; B-LRU is `lru -a bloomfilter`
7. Write a ~50-line parser + plot that computes the reduction versus FIFO for Figure 4a/b
