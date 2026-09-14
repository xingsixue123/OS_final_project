### 3. Demystifying and Improving Lazy Promotion in Cache Eviction (VLDB'26)

- **Repo:** https://github.com/cacheMon/Lazy-Promotions — last commit 2025-12-08 (`7e50398`), 231 MB cloned.
  - **License:** no top-level LICENSE; the vendored simulator is GPL-3.0.
  - **Official:** the paper's "PVLDB Artifact Availability" section names this repo.
- **What it is:** a libCacheSim fork that adds lazy-promotion eviction policies (Prob-LRU, Batch-LRU, Delay-LRU, FIFO-reinsertion/CLOCK, Random-LRU, lazy ARC/2Q, and offline oracles) plus the paper's two new algorithms **D-FR** (`DelayFR.c`, 330 lines) and **AGE** (`AGE.c`, 382 lines). It also includes a separate concurrent simulator for throughput tests and Python scripts that turn per-trace outputs into every paper figure.
- **Paper eval setup:**
  - **Miss ratio and promotions:** 6,357 production traces (346 B requests; MSR, FIU, CloudPhysics, Tencent, Alibaba, Twitter, Wiki, Meta, plus 2 private CDNs), replayed in libCacheSim on CloudLab. Cache size is 1% of working-set size, results relative to LRU.
  - **Throughput:** a Zipf trace at 16 threads on a 36-core Xeon with SMT and turbo off.
- **Reproduction target:** **Figure 11a/b/c.** The claim: D-FR (delay ratio 0.05) and AGE (factor 0.5) cut promotions relative to FR and LRU without hurting miss ratio. D-FR removes about 60% of FR's promotions on the median trace, and promotion efficiency is about 48% versus about 24% for FR.
  - **Cost:** 8 `cachesim` configs per trace.
  - **Determinism:** the metrics are hardware-independent.
  - **Checkable:** the repo ships **per-trace results for all traces** (`scripts/data/lazy_promotions_data.tar.gz`, 18.8 MB, 159k files, verified), so a public-subset run can be diffed row by row.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| cmake ≥ 3.12; C11/C++17 | `simulator/CMakeLists.txt:1,12-17` | ✅ cmake 3.25, gcc 12.2 | as-is (the README's extra flags are for gcc ≥ 13) |
| glib-2.0 dev (pkg-config) | `CMakeLists.txt:143` | ❌ runtime `.so` only | `conda install -c conda-forge glib pkg-config` |
| zstd dev (required) | `CMakeLists.txt:152-163` | ❌ runtime only | conda-forge `zstd` |
| argp | `CMakeLists.txt:148` | ✅ glibc | — |
| tcmalloc | `FindTcmalloc.cmake` (hard-coded system paths) | missing, optional | conda `gperftools` + `-DHT_DEPENDENCY_LIB_DIR`, or skip |
| `install_dependency.sh` (sudo apt, `sudo make install`) | `simulator/scripts/install_dependency.sh` | ❌ | don't run; use conda |
| Dockerfile | `simulator/dockerfile` | not applicable | leftover upstream file |
| libCacheSim | vendored (diverged fork, no pinned base; ~mid-2024 upstream) | n/a | nothing to fetch; **upstream cannot be substituted** |
| Python pandas 2.3.1, numpy 2.3.2, seaborn, matplotlib | `scripts/requirements.txt` | user install | py3.12 env + pip |
| Undeclared Python deps: pyarrow, scipy, `textual_pandas` | `process_data.py:2` (verified) | missing | `pip install pyarrow scipy textual-pandas`, or drop the unused import |
| `process_data.py:101` always reads `scalability.feather` | verified | ⚠️ crashes without it | run `parse_scalability.py` on the shipped `lazy_throughput.tar.gz` first (19 KB; the explorer's 64.8 MB figure was wrong) |
| distComp + Redis orchestration | README | not needed | `xargs -P 28` over the generated task commands |
| Hard-coded `/ltdata`, `/mnt/nfs`, `~/Lazy-Promotions` | `scripts/generate_task.sh:4-9` | ⚠️ | edit variables |
| "≥ 256 GB RAM for larger traces" | README | 125 GiB | only matters for the biggest Twitter/Meta KV traces; not the target |
| Throughput runs: `sudo wrmsr` turbo off, SMT off | `scripts/disable_turbo.sh` | ❌ no root, AMD CPU | Figures 1b/2b–5b/6a are only approximate; not the target |

**Data** (CMU PDL public FTP, zstd oracleGeneral)

| dataset | size | subset needed |
|---|---|---|
| MSR (14) + FIU (9) + CloudPhysics (106) + MetaCDN (3) + MetaStorage (5) | **≈ 14 GB**, ~3.3 B requests | ✅ minimum for Figure 11 (137 traces) |
| Tencent CBS (4,048) | ≈ 154 GB | optional second tier |
| Alibaba block (609) | ≈ 94 GB | optional; not together with Tencent (248 GB is too tight) |
| Tencent Photo / Wiki / Meta KV | 67 / 50 / 61 GB | optional |
| Twitter (51) | ≈ 1.5 TB | skip |
| CDN 1 / CDN 2 (1,506 traces, ~24% of the paper) | private | ❌ figures only via the shipped results |
| Shipped per-trace results | 18.8 MB (verified) | reference for the diff, and regenerates every miss-ratio figure without simulating |

**Hard filters** — H1 ✅ named in the paper's artifact section · H2 ✅ cmake + conda glib/zstd; sudo only in the replaceable installer and the throughput scripts · H3 ✅ single-threaded CPU simulations; throughput not faithfully reproducible · H4 ✅ at subset scale (14 GB + shipped per-trace references); ❌ at full scale (private CDNs, 1.5 TB Twitter).

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | Documented plain `cmake .. && make`; only friction is pointing CMake at conda glib/zstd |
| dependency fit | 4 | All on conda-forge; minus for the sudo installer, tcmalloc's hard-coded paths and 3 undeclared Python deps |
| data fit | 3 | 14 GB public subset plus shipped references, but 1,506 traces are private and Twitter is 1.5 TB |
| hardware fit | 4 | Deterministic, hardware-independent metrics; throughput needs a root-tuned Xeon |
| repro scripts | 4 | `generate_task.sh` (exact sweeps) → `parse_data.py` → `process_data.py` → `generate_figures.py figure11a` (verified); minus for distComp/Redis, hard-coded paths and the unconditional feather read |
| extensibility | 5 | One file per policy (DelayFR/AGE as templates), registered in 3 places; the shared `n_promotion` counter plus a parser dict make new policies appear in the figures automatically |
| **total** | **24 / 30** | |

**Verdict: ✅ DOABLE** · confidence high for Figure 11 (miss ratio / promotions), medium for throughput · setup ≈1–1.5 person-days · compute: 137 traces × 8 configs ≈ 26 B simulated requests ≈ 2–4 CPU-hours (< 30 min wall at 28 workers), 14 GB disk.

**Key risks**
- **Subset versus paper distribution:** without the private CDNs and Twitter, Figure 11 medians will differ. Diff against the shipped rows for the same traces (exact match expected).
- **Prob-LRU uses unseeded `rand()`** (`lpLRU_prob.c:154`), so results are reproducible only while the RNG path stays the same.
- **Parser coupling:** a new policy must print a name that `parse_data.py`'s regex and dict accept, or its rows are **silently dropped**. Traces with fewer than 1 M requests are also filtered out.
- **The build may silently pick up system runtime libraries** instead of conda's, so set an rpath.
- **Diverged vendored fork:** upstream fixes won't carry over; stale `priv/` and `customized/` code may break on stricter compilers.

**Where an add-on plugs in**
- **New policy:** `simulator/libCacheSim/cache/eviction/<X>.c`, templated on `DelayFR.c` / `AGE.c`. Increment `cache->n_promotion` wherever a promotion happens (`include/libCacheSim/cache.h:104`).
- **Registration:** `cache/eviction/CMakeLists.txt`, `include/libCacheSim/evictionAlgo.h` (see `DelayFR_params_t` :65), `include/libCacheSim/cacheObj.h` (`DelayFR_obj_metadata_t` :47), `bin/cachesim/cache_init.h`.
- **Evaluation pipeline:** a sweep loop in `scripts/generate_task.sh`, a name + parameter parser in `scripts/parse_data.py`, and a `figureXX` in `scripts/generate_figures.py` modeled on `figure11a` (:573).
- **Throughput version:** port the policy into the diverged `simulator-concurrent/`.

**Build route (not executed)**
1. `conda create -n lazyp -c conda-forge python=3.12 glib pkg-config zstd gperftools -y && conda activate lazyp`
2. `cd repo/simulator && mkdir -p _build && cd _build && PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DCMAKE_BUILD_RPATH=$CONDA_PREFIX/lib .. && make -j32 cachesim`
3. Smoke test: `./bin/cachesim ../data/cloudPhysicsIO.oracleGeneral.bin oracleGeneral delayfr -e delay-ratio=0.05 0.01 --ignore-obj-size 1`
4. `wget -r -np` MSR, FIU, CloudPhysics, MetaCDN and MetaStorage (~14 GB); symlink `cphy/` → `cloudphysics/` for `datasets.txt`
5. Edit `generate_task.sh:4-9`, keep only the 8 Figure 11 configs, and run them with `xargs -P 28`
6. `pip install -r scripts/requirements.txt pyarrow scipy textual-pandas`
7. Reference figure: untar both shipped archives → `parse_scalability.py` → `parse_data.py ref` → `process_data.py` → `generate_figures.py figure11a figure11b figure11c`
8. Own figure: `parse_data.py ~/lp_results` → same steps; diff miss-ratio and promotion columns against the reference rows for the 137 traces
