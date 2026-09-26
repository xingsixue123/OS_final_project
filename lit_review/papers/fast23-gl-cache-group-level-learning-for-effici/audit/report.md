# GL-Cache: Group-level learning for efficient and high-performance caching

*Desk review only — nothing was built or run. Every claim below points at a paper
section/figure or a repository path.*

## 1. Paper summary

**Problem.** Learned cache-eviction policies sit at one of two bad extremes (§1, Table 1,
p. 3). Object-level learning (LRB) uses 44 features and 189 B of metadata per object and
must run inference + ranking at every eviction — measured at 200 µs per eviction on one
core, i.e. ≤5,000 evictions/s (§2.2.1), a 775× slowdown vs LRU. Learning-from-distribution
(LHD) and learning-from-simple-experts (LeCaR, Cacheus) are cheaper but use only 1–2
features and still sample/rank objects per eviction (§2.2.2–2.2.3).

**Key idea.** Learn at the granularity of *object groups* (§3.2): cluster objects into
fixed-size groups at insertion, learn a per-group "utility", and evict whole groups. This
amortizes both the storage (<1 B/object) and the inference cost over tens–thousands of
objects, and accumulates more training signal per learned entity because cache workloads
are Zipfian.

**Design.**
- *Grouping* (§3.3): objects are grouped by **write time** only, because that is universally
  available and maps onto a log-structured cache. §3.3 explicitly lists tenant id, content
  type and object size as alternative grouping keys that are *not* explored. Fig. 2a shows
  write-time groups have a lower coefficient of variation of mean reuse time than random
  groups, and that this advantage shrinks as group size grows.
- *Group utility* (§3.4, Eq. 1–2): `U_group(t) = Σ_{o∈group} 1 / (T_o(t) · s_o)` — cost of
  one miss over freed bytes × time-to-next-access. Note the explicit `1/s_o`: large objects
  are penalized.
- *Learning* (§3.5): XGBoost GBM, regression on L2 loss, **7 features** (static: request
  rate, write rate, miss ratio and mean object size at group-creation time; dynamic: age,
  #requests, #requested objects), 8,000 training samples (256 KB), **retrained from scratch
  once per day of trace wall-clock**. Labels come from online accumulation plus ghost
  entries for evicted-but-sampled groups (Fig. 3).
- *Eviction* (§3.6, Fig. 4): merge-based, as in Segcache. Pick the lowest-utility group,
  merge it with the `N_merge − 1` groups *closest in write time*, retain one group's worth of
  objects using a fixed lightweight score `1/(size · age)`, evict the rest. §3.6 notes that
  merging the `N_merge` *least useful* groups instead costs up to 20% hit ratio.
- *Spectrum* (§3.7, Table 2): three knobs — `S_group`, `N_merge`, `F_eviction`.

**Evaluation setup** (§4.1, Table 3). 118 traces: 103 CloudPhysics VM block-I/O, 14 MSR
block-I/O, 1 Wikimedia CDN. Two artifacts: a Rust *prototype* on Pelikan Segcache, and a
storage-oblivious *micro-implementation* in C on libCacheSim (the paper says it "focus[es]
our evaluation on the micro-implementation results"). Two operating points:
GL-Cache-E (`S_group=60, N_merge=2, F_evict=0.02`) and GL-Cache-T (`S_group=200, N_merge=5,
F_evict=0.1`). Baselines: FIFO, LRU, Cacheus, LHD, LRB, size-aware Belady (micro) and
Segcache, Cachelib, TinyLFU, LHD (prototype). 3-day warmup (1-day in Fig. 14). Hardware:
CloudLab m510 (micro) and c6420 (prototype) — plain x86 servers, CPU only.

**Headline numbers.**
- Fig. 7 (box plots, hit-ratio increase over FIFO across 103+14 traces): GL-Cache-E is the
  best learned cache at the median on MSR small sizes (+60% over LHD for the median
  workload, §4.3); up to +37.8% vs LHD and +87% vs LRB.
- Fig. 8 / §4.4: GL-Cache-E is 228× LRB's throughput, GL-Cache-T 586×; GL-Cache-E is 64%
  faster than the fastest other learned cache.
- Table 4 (Wikimedia, p. 11): at 200 GB, miss ratio FIFO 0.16, LRB 0.048, GL-Cache-E 0.041;
  throughput 7.91 / 0.04 / 3.91 MQPS.
- Fig. 5: oracle-assisted *group* eviction ≈ oracle-assisted *object* eviction (size-aware
  Belady) — so group granularity is not the efficiency bottleneck.
- Fig. 9a/9c: feature importance is workload- and cache-size-dependent; frequency and age
  dominate (median ≈0.3), mean object size next, then request rate / miss ratio / write rate
  (median ≈0.05 each).
- §4.6: per-workload retraining-interval tuning is worth "up to 10%" hit ratio.

## 2. Artifact audit

### Repo structure

`https://github.com/Thesys-lab/fast23-glcache`, head commit `fbb8240`, **2023-05-12**,
410 files, 12.4 MB, 51 stars, no open issues, frozen since. Two top-level trees:

| path | what |
|---|---|
| `micro-implementation/` | snapshot of libCacheSim (C, ~27 kLOC C + 16 kLOC headers). The paper's primary evaluation vehicle. |
| `prototype/` | Rust (~13.8 kLOC), snapshot of Pelikan Segcache with an `l2cache` crate = GL-Cache. |

### Paper component → code map

| paper | code |
|---|---|
| Group = segment; group params `S_group`/`N_merge`/`F_evict` (§3.7, Table 2) | `micro-implementation/libCacheSim/cache/eviction/GLCache/GLCache.c:25-43` (`segment_size`, `n_merge`, `rank_intvl`), CLI parse at `GLCache.c:45-100` |
| Grouping by write time (§3.3) | `GLCache.c:310-344` (`GLCache_insert` always appends to `params->buckets[0]`); `const.h:3` `#define MAX_N_BUCKET 1` |
| Group utility Eq. 1–2 (§3.4) | online label accumulation in `dataPrep.c:244-257` (`train_utility += 1e6/age/obj_size`); oracle version `segment.c:180-209` (`cal_seg_utility`) |
| Features (§3.5) | `dataPrep.c:97-127` (`prepare_one_row`): x = {age, mean obj size, n_hit, n_active, req_rate, miss_ratio}; `const.h:18-19` `N_FEATURE_TIME_WINDOW 0`, `N_FEATURE_NORMAL 6`; `init.c:58` |
| XGBoost GBM, L2 regression, daily retrain (§3.5) | `train.c:22-106` (`gbtree`, `reg:squarederror`, `nthread=1`, ≤20 rounds with early stop); retrain trigger `GLCache.c:288-303`; `retrain_intvl=86400` at `GLCache.c:30` |
| Training-data snapshot + ghost entries (§3.5, Fig. 3) | `dataPrep.c:203-236` (`snapshot_segs_to_training_data`), ghost handling in `GLCache.c:225-281` (`GLCache_check`) and `eviction.c:33-43` |
| Inference + ranking, `F_eviction` (§3.5) | `inference.c:75-150`, `segSel.c:84-173` (`rank_segs`), `segSel.c:324-410` (`select_segs_learned`, re-ranks when `ranked_seg_pos >= n_ranked_segs * rank_intvl`) |
| Merge-based eviction, retain by `1/(size·age)` (§3.6, Fig. 4) | `eviction.c:57-136` (`GLCache_merge_segs`), cutoff `segment.c:145-172` (`find_cutoff`), score `obj.h:47-88` (`cal_obj_score`, `OBJ_SCORE_AGE_BYTE` selected at `GLCache.c:135-137`) |
| Oracle variants for Fig. 5 | `GLCacheInternal.h:8-13` (`logOracle`/`itemOracle`/`twoOracle`), selectable via `-e type=logOracle` |
| Baselines FIFO/LRU/Cacheus/LHD/Belady/BeladySize/LeCaR/Hyperbolic/ARC/SLRU/GDSF | `micro-implementation/libCacheSim/cache/eviction/*.c`, `.../LHD/`, dispatched in `libCacheSim/bin/cachesim/cli.c:271-335` |
| Prototype (Rust) | `prototype/src/l2cache/src/eviction/policy.rs`, `.../learning/learner.rs`, `.../segments/segments.rs` |

**Baselines that are *not* in the repo:** LRB (grep for `LRB`/`lrb` hits only
`repo/README.md`), TinyLFU, Cachelib, Segcache-as-baseline. The paper says LRB came from
"code open-sourced by the authors" (§4.1) — i.e. an external repository the team must build
separately. This matters: the headline "228× throughput, +7% hit ratio vs LRB" claim cannot
be reproduced from this repo alone.

### Discrepancy found by reading the code

The paper says GL-Cache uses **seven** features including write rate (§3.5, and Fig. 9a
plots a `write rate` bar). The micro-implementation compiles **six**: `dataPrep.c:105-110`
writes age, mean object size, n_hit, n_active, req_rate, miss_ratio; `write_rate` is tracked
on the segment (`GLCacheInternal.h:116`, `GLCache.c:319-321`) and averaged on merge
(`eviction.c:79-80`) but never enters the feature vector. Any attempt to reproduce Fig. 9
will therefore differ from the paper.

### Build route on *this* machine

`micro-implementation/CMakeLists.txt` needs: cmake ≥3.12 (have 3.25.1), **GLib-2.0**
(required, `CMakeLists.txt:140`), **zstd** (required when `SUPPORT_ZSTD_TRACE=ON`, the
default, `:150-160`), **tcmalloc** (optional, `:165-171`), **XGBoost** (required when
`ENABLE_GLCACHE=ON`, the default, `:180-185` — `find_package(xgboost REQUIRED)`).

`micro-implementation/README.md:33-60` and `scripts/setup.sh` use `sudo apt` / `sudo make
install`, but nothing needs root: both `cmake/Modules/FindGLib.cmake:30-34` and
`FindZSTD.cmake:93-94` go through `pkg-config`, so a conda-forge env (`glib zstd gperftools
xgboost`) with `PKG_CONFIG_PATH`/`CMAKE_PREFIX_PATH` pointed at it satisfies them; failing
that, XGBoost/zstd build from source into `$HOME` with `-DCMAKE_INSTALL_PREFIX=$HOME/local`.
`USE_HUGEPAGE` (default ON) is *not* a root requirement — the only use is `madvise(...,
MADV_HUGEPAGE)` (`dataStructure/hashtable/chainedHashtable.c:96-99`,
`chainedHashTableV2.c:94-96`), which is unprivileged, and the option can be turned off.

Known friction: on Linux `CMakeLists.txt:120-122` *overwrites* `CFLAGS` with only
`-Wl,--export-dynamic`, dropping `-std=gnu99`; with gcc 12 defaulting to gnu17 the GNU
extensions used (`strsep` in `GLCache.c:50-51`, `strcasestr` in `cli.c:268`) may need
`-D_GNU_SOURCE`. CI (`micro-implementation/.github/workflows/build.yml`) only has a
`self-hosted` job — every hosted-runner job is commented out, so there is no public green
build. A lower-risk alternative route exists: the same GLCache code lives in the maintained
upstream `github.com/1a1a11a/libCacheSim` (active as of Aug 2025, has
`scripts/install_dependency.sh`, `-DENABLE_GLCACHE=ON`) — but it has diverged from this
FAST'23 snapshot, so it is a fallback, not the artifact.

The **prototype** is riskier: `prototype/Cargo.toml:26` and
`prototype/src/l2cache/Cargo.toml:45-60` pull three *git* dependencies
(`twitter/rustcommon`, `1a1a11a/rustcommon`, `1a1a11a/rust-xgboost` rev `360af10`).
`Cargo.lock` pins revisions, but the upstream repos must still resolve, and the old
`rust-xgboost` bindings need bindgen/clang (not installed; conda-installable). Rust itself
installs fine via rustup in user space.

### Data sources

`repo/README.md:28` points at
`https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/fast23_glcache/`. I fetched the
listing: `cloudphysics/` has **106** files `w01..w106.oracleGeneral.bin.zst` (11 MB–781 MB,
≈15–20 GB total), `msr/` has **14** files (14 MB–665 MB, ≈1.5 GB), plus
`wiki_2016u.oracleGeneral.zst` at **23 GB**. Format is documented in `README.md:30-38`
(`uint32 ts, uint64 obj_id, uint32 size, int64 next_access_vtime`). The micro-implementation
reads zstd directly (`SUPPORT_ZSTD_TRACE`), the prototype needs decompressed traces
(`prototype/README.md:20`), so Wikimedia uncompressed (≈67 GB at 2,804 M × 24 B) is the only
storage-heavy item. Everything fits in ~257 GB free. A 220 KB sample trace ships in-repo
(`micro-implementation/data/trace.oracleGeneral.bin`, `trace.vscsi`) for smoke tests.

### Evaluation scripts

**Essentially absent.** The only scripts are `micro-implementation/scripts/setup.sh`
(dependency install) and `scripts/dataGen.py`. There is no trace-download script, no batch
sweep over the 118 traces, no plotting code, and no figure-to-command mapping. What *does*
exist is a first-class driver binary: `libCacheSim/bin/cachesim` with
`--warmup-sec`, `--num-thread`, `--num-req`, `--ignore-obj-size`,
`--consider-obj-metadata`, `-e "k=v"` eviction params, `-a` admission
(`libCacheSim/bin/cachesim/cli.c:45-68`), documented in
`micro-implementation/doc/quickstart_cachesim.md`. Its single-size path prints object miss
ratio **and** throughput in MQPS (`bin/cachesim/sim.c:68-81`); its multi-size path prints
object miss ratio **and byte miss ratio** (`bin/cachesim/main.c:55-67`). So the two metrics
the paper plots are emitted natively; only the sweep/aggregation/box-plot layer must be
written.

### Artifact badges

None. FAST introduced artifact evaluation in **2024** (per sysartifacts.github.io/fast), so
a FAST'23 paper cannot carry badges. The repo has no badge claims.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper §Availability (p. 14): "We open-source our implementation at https://github.com/Thesys-lab/fast23-glcache". The repo contains the real system, not a stub: `micro-implementation/libCacheSim/cache/eviction/GLCache/` holds all seven design components (grouping, utility, XGBoost training, inference, merge eviction, ghost entries, oracle variants), and `prototype/src/l2cache/` holds the Segcache-based prototype. Apache-2.0 per `README.md:42-55` and `micro-implementation/LICENSE`. |
| `H2_no_root` | **pass** | Pure user-space trace-driven simulation. No kernel module, eBPF, perf counter, KVM or `/proc/sys` use anywhere in the eviction or harness code. The `sudo` red flags in `repo_facts.json` are all in dependency-install docs (`micro-implementation/scripts/setup.sh:5`, `.travis.yml:51`, and a fully commented-out `.github/workflows/build.yml:22`) and are replaceable with conda / `$HOME`-prefix source builds, since `FindGLib.cmake:30` and `FindZSTD.cmake:93` use pkg-config. `USE_HUGEPAGE` is only `madvise(MADV_HUGEPAGE)` (`chainedHashtable.c:96-99`) — unprivileged, and `-DUSE_HUGEPAGE=OFF` exists (`CMakeLists.txt:46`). The `pmem` grep hits are a doc comment in `prototype/src/l2cache/src/datapool/file.rs:6`, not a requirement. |
| `H3_hardware_fit` | **pass** | Single-node, CPU-only, no GPU. Paper hardware (§4.1) is a 64 GB CloudLab m510 for the micro-implementation — strictly weaker than this machine's 16 cores / 125 GB. The micro-implementation stores only metadata, not object values (`micro-implementation/README.md:19`, paper §4.1), so a simulated 16 GB cache costs far less than 16 GB of RAM. Traces: ≈20 GB compressed for CloudPhysics+MSR, 23 GB for Wikimedia; well inside ~257 GB free. Multi-trace sweeps parallelize across the 16 cores (`cachesim --num-thread`). |
| `H4_obtainable_deps_data` | **pass** | Deps (glib, zstd, tcmalloc, xgboost, cmake, gcc) are all conda-forge/user-space installable and resolved via pkg-config. Data: all 118 traces are public downloads from `ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/fast23_glcache/` (listing verified: 106 CloudPhysics + 14 MSR + 1 Wikimedia), in the exact binary format the simulator reads. No proprietary traces, no model weights. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** Fig. 7(a) and Fig. 7(c) — *hit-ratio increase over FIFO* box plots on
CloudPhysics and MSR at the small cache size — together with the corresponding throughput
box plots Fig. 8(a)/8(c). The claim under test is the paper's core one: *group-level
learning gets learned-cache-level hit ratio at near-FIFO throughput* (GL-Cache-E ≥ LHD at
the median with ≥50% of FIFO's throughput, GL-Cache-T at ~0.8× FIFO throughput).

**Scale-down.**
- Drop **LRB** from the comparison (not in this repo; needs a separate build of the LRB
  authors' C++/LightGBM code). Reproduce the FIFO / LRU / Cacheus / LHD / GL-Cache-E /
  GL-Cache-T bars, all of which exist (`bin/cachesim/cli.c:271-335`). State this omission.
- Use ~20–30 of the 103 CloudPhysics traces (pick a size-stratified sample; the small ones
  are 11–50 MB compressed) plus all 14 MSR traces, instead of the full 103.
- Cache sizes: 1 GB and 16 GB for CloudPhysics (paper §4.1); 0.01% / 0.1% / 1% of footprint
  for MSR, obtainable via `cachesim ... auto` (doc `quickstart_cachesim.md:44-50`).
- Warmup: `--warmup-sec=259200` (3 days, §4.1); cross-check with 86400 (Fig. 14).
- **Throughput runs must use `--num-thread=1`** — the multi-size path defaults to 16 threads
  (`cli.c:58`, `main.c:31-33`), which would corrupt MQPS numbers. Run miss-ratio sweeps
  multi-threaded, throughput sweeps single-threaded.

**Steps.**
1. Create a conda env: `glib zstd gperftools xgboost=1.7 cmake`; export
   `PKG_CONFIG_PATH`/`CMAKE_PREFIX_PATH`. (Fallback: build XGBoost 1.7 from source into
   `$HOME/local`.)
2. `cmake -B _build -DCMAKE_BUILD_TYPE=Release -DENABLE_GLCACHE=ON -DUSE_HUGEPAGE=OFF`;
   expect to add `-D_GNU_SOURCE` / restore `-std=gnu99` (see §2). Smoke test on the shipped
   `data/trace.oracleGeneral.bin`: `./cachesim ../data/trace.oracleGeneral.bin
   oracleGeneral glcache auto`.
3. Download CloudPhysics + MSR traces with `wget -r` (≈20 GB); keep them zstd-compressed.
4. Write the missing sweep driver (~100 lines of bash/Python): for each trace × size ×
   algorithm, invoke `cachesim`, parse the `miss ratio`/`throughput` line from
   `sim.c:68-75`, write CSV.
5. Configure the two GL-Cache points from §4.1:
   `-e "segment-size=60,n-merge=2,rank-intvl=0.02"` (E) and
   `-e "segment-size=200,n-merge=5,rank-intvl=0.1"` (T).
6. Compute `(HR_alg − HR_FIFO)/HR_FIFO` and `R_alg/R_FIFO` per trace; plot box plots with
   the paper's percentile convention (median, 25/75 box, 10/90 whiskers, §4.1).

**Effort.** ≈5 person-days (2 days build/deps, 1 day download, 2 days harness + plotting)
plus ≈150–300 CPU-core-hours of simulation (no GPU, no GPU-hours). On 16 cores that is
roughly 1–2 days of wall clock for the scaled-down sweep.

**Level: M.** Not H, because there is no evaluation script, no plotting code, no
trace-download script, no figure→command mapping, no public CI signal, the dependency
install instructions assume root, and the LRB baseline — half of the headline claim — is
absent. Not L, because the driver binary natively emits exactly the two metrics plotted,
every non-LRB baseline is in-tree, the parameters for both GL-Cache operating points are
stated verbatim in §4.1, all traces are public in the simulator's native format, and the
whole thing is CPU-only and comfortably under this machine's limits.

## 5. Add-on ideas

### A1 — Byte-aware group utility

> We hypothesize that replacing GL-Cache's size-penalizing group utility
> `U = Σ 1/(T·s)` (and its matching `1/(size·age)` object-retention score) with a
> size-neutral / byte-oriented variant reduces **byte miss ratio** by ≥10% on CloudPhysics,
> MSR and Wikimedia, at a bounded object-miss-ratio cost and without giving up GL-Cache's
> throughput advantage over LHD/LRB.

- **Mechanism.** Introduce an exponent `α` on the size term and expose it as a CLI eviction
  parameter. Three touch points, all a handful of lines: the online label
  `train_utility += 1e6/age/obj_size` (`dataPrep.c:254`) becomes `.../pow(obj_size, α)`; the
  object retention score `OBJ_SCORE_AGE_BYTE = 1e8/size/age` (`obj.h:63-64`) gets the same
  exponent; the prediction normalization `pred * 1e6 / n_byte` (`inference.c:107-110`) must
  be made consistent. Add `utility-alpha` to the parser (`GLCache.c:55-99`) and the defaults
  (`GLCache.c:25-43`). Also add byte miss ratio to the single-size output path
  (`bin/cachesim/sim.c:68-81`) — the multi-size path already computes it
  (`bin/cachesim/main.c:59-64`), so this is ~5 lines. Sweep `α ∈ {0, 0.5, 1}` and plot the
  object-MR / byte-MR / throughput Pareto surface, extending the paper's Fig. 13.
- **Code locations.** `micro-implementation/libCacheSim/cache/eviction/GLCache/dataPrep.c:254`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/obj.h:63`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/inference.c:107`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/GLCache.c:55`,
  `micro-implementation/libCacheSim/bin/cachesim/sim.c:68`,
  `micro-implementation/libCacheSim/bin/cachesim/main.c:59`.
- **Motivating evidence.** 3L-Cache (FAST'25) reports that among learned policies
  "GL-Cache has the lowest object miss ratio, but its byte miss ratio is the worst, even
  higher than LRU". The GL-Cache paper never reports byte miss ratio anywhere; §4.1 says it
  deliberately *retargeted* LRB "from byte miss ratio to object miss ratio", and Eq. 1–2
  bakes `1/s_o` into the utility, so the bias is by construction. This is a published,
  named weakness with an untested one-parameter fix.
- **Feasibility: H.** Under ~200 LOC across five files; no new harness (the existing
  `cachesim` multi-size path already reports byte miss ratio); runs entirely on this machine
  in the same sweep as the reproduction.
- **Research value: H.** A FAST'25 paper names this exact failure and solves it by building
  a *different, object-level* system at 3–6× LRU overhead. Showing that GL-Cache's own
  utility can be re-weighted to get competitive byte miss ratio *at GL-Cache throughput*
  would be a new Pareto point; showing it *cannot* would establish that high byte miss ratio
  is intrinsic to merge-based group eviction (you cannot selectively retain large objects
  when you evict whole groups) — which is an equally publishable negative result. Either
  outcome teaches something a FAST reviewer would care about.
- **Scoop check.** Queries: `"GL-Cache" cache eviction comparison S3-FIFO SIEVE learned
  cache 2024`; `3L-Cache FAST 2025 ... GL-Cache byte miss ratio`; `"group-level learning"
  cache eviction ... 2025 2026`. Closest work: **3L-Cache**
  (https://www.usenix.org/conference/fast25/presentation/zhou-wenbin) — identifies the
  weakness, but builds an object-level learner instead of fixing GL-Cache's group utility.
  **Result: `partial`.**

### A2 — Multi-key grouping (activate the dead multi-bucket path)

> We hypothesize that grouping objects by *(write time × object-size class)* instead of
> write time alone lowers GL-Cache's object miss ratio on traces with heterogeneous object
> sizes (Wikimedia CDN, MSR at small cache sizes), because groups become more homogeneous in
> utility and the model no longer has to average over wildly different object sizes.

- **Mechanism.** `const.h:3` hard-codes `#define MAX_N_BUCKET 1`, yet the entire bucket
  machinery — per-bucket segment chains, per-bucket ranked chains, round-robin bucket
  selection — is already written and loops over `MAX_N_BUCKET`
  (`segSel.c:94`, `segSel.c:155`, `segSel.c:202-241`, `inference.c:50`, `inference.c:101`,
  `dataPrep.c:217`, `init.c:87-93`). Raise `MAX_N_BUCKET` to K; assign `bucket_id` at
  insertion from `log2(req->obj_size)` instead of the hard-coded `&params->buckets[0]`
  (`GLCache.c:312`); make the global ranking compare utilities across buckets fairly
  (`segSel.c:84-173` already ranks globally then re-links per bucket); optionally add the
  bucket key as a model feature (`dataPrep.c:105-110` + `init.c:58`). Expect to fight the
  fragmentation path that already warns "evicting and cannot merge" (`GLCache.c:352-368`),
  which becomes much more likely with K buckets — that interaction is itself a finding.
- **Code locations.** `micro-implementation/libCacheSim/cache/eviction/GLCache/const.h:3`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/GLCache.c:312`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/segSel.c:94`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/inference.c:50`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/dataPrep.c:105`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/init.c:87`.
- **Motivating evidence.** §3.3: "Depending on workload types, such features include time,
  tenant id, content type, object size, etc. In this work, we focus on grouping based on
  write time" — an explicitly unexplored design axis. Fig. 2a shows the write-time grouping
  advantage (lower coefficient of variation of reuse time) *shrinks toward random grouping*
  as group size grows, i.e. the grouping key is the weak link at large `S_group`, exactly
  where GL-Cache-T operates. Fig. 9c shows object size is the *most* important feature at
  1 GB, suggesting size is a natural clustering key. And the code shows the multi-bucket path
  is dead (`MAX_N_BUCKET 1`), so the hypothesis is testable by turning on machinery the
  authors wrote but never evaluated.
- **Feasibility: H.** The loops already exist; the change is bucket assignment plus fixing
  whatever breaks in cross-bucket ranking — roughly 300–600 LOC. Evaluable with the
  reproduction harness on the same traces.
- **Research value: M.** A natural and expected extension that the paper itself flags; the
  interesting part (does finer grouping beat the write-time locality that motivated the
  log-structured design, and how badly does bucketing fragment the segment pool?) is real
  but of moderate reviewer interest.
- **Scoop check.** Queries: `learned cache eviction grouping objects by size class or TTL
  bucket instead of write time group-level learning segment`; `"group-level learning" cache
  eviction improve grouping heuristic multi-feature buckets 2025 2026`. Nothing found that
  changes GL-Cache's grouping key; the closest items (3L-Cache, SL-Cache DASFAA'26,
  Cold-RL) are all object-level learners. **Result: `clear`.**

### A3 — Learned object retention inside the merge (two-level learning)

> We hypothesize that replacing the fixed `1/(size·age)` object-retention score used during
> merge-based eviction with a group-conditioned, learned object score (reusing the
> per-object `freq` the cache already tracks) closes ≥30% of the hit-ratio gap between
> GL-Cache and the oracle-assisted group eviction of Fig. 5, at ≤2× GL-Cache's eviction cost.

- **Mechanism.** `obj.h:47-88` already enumerates six object score types
  (`OBJ_SCORE_FREQ`, `FREQ_BYTE`, `FREQ_AGE`, `FREQ_AGE_BYTE`, `AGE_BYTE`, `ORACLE`) but
  `GLCache.c:135-137` hard-wires `OBJ_SCORE_AGE_BYTE` for the learned mode and there is no
  CLI knob. Step 1 (baseline): expose `obj-score-type` as a parameter (`GLCache.c:55-99`) and
  measure what the *existing* alternatives buy — this alone tells you how much the fixed
  choice costs. Step 2 (the actual contribution): add a score type whose weights on
  (freq, age, size) are fit online, using the ghost-entry reuse signal already collected in
  `dataPrep.c:244-257` as the label, either as a tiny per-cache linear model or as weights
  read off the group model's predicted utility. Plumb through `find_cutoff`
  (`segment.c:145-172`) and `GLCache_merge_segs` (`eviction.c:87-103`). Measure against the
  `type=twoOracle` / `type=itemOracle` variants (`GLCacheInternal.h:8-13`), which give you
  the Fig. 5 upper bound for free.
- **Code locations.** `micro-implementation/libCacheSim/cache/eviction/GLCache/obj.h:47`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/segment.c:145`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/eviction.c:87`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/GLCache.c:135`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/dataPrep.c:244`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/GLCacheInternal.h:15`.
- **Motivating evidence.** §3.6 is candid that the object score is a heuristic: "object
  selection uses a simple metric based on object age and size: 1/(size·age) ... We choose to
  use this metric because recency and size are the two most common metrics used in other
  eviction algorithms". Fig. 5 shows oracle-assisted *group* eviction matches size-aware
  Belady — so the group granularity is not the bottleneck and the remaining gap in the real
  system lives in (a) the utility prediction and (b) this retention heuristic. And §4.5 /
  Fig. 9a shows **frequency** is the joint-highest-importance feature at the group level,
  yet frequency is entirely absent from the object retention score that decides which
  individual objects survive.
- **Feasibility: H.** The enum, the score array, the cutoff machinery and the ghost-entry
  label pipeline all exist; the minimal version is a new branch in `cal_obj_score` plus a
  weight-update hook. Oracle upper bounds are already selectable via `-e type=...`. Fits
  well inside 10 weeks for 2–4 students.
- **Research value: M.** A solid, well-motivated improvement to a component the authors
  explicitly left as a heuristic, with a clean oracle upper bound to measure against — but
  the direction ("use learning for the second level too") is what a reviewer would expect,
  and the gain is bounded by Fig. 5.
- **Scoop check.** Queries: `segment merge eviction retain objects learned score Segcache
  GL-Cache improve object retention policy research`; `"SL-Cache" selective learning cache
  eviction priority retention hot objects GL-Cache group`. Closest work: **SL-Cache**
  (DASFAA 2026, https://link.springer.com/chapter/10.1007/978-981-92-0363-5_36) does
  hotness-aware retention, but through object-level sampling, not inside a group merge; it
  does not touch GL-Cache. **Result: `partial`.**

### A4 — Adaptive learning cadence (self-tuning retrain and rank intervals)

> We hypothesize that a closed-loop controller that sets `retrain_intvl` and `rank_intvl`
> from signals GL-Cache already computes (validation RMSE drift across retrainings, observed
> interval miss-ratio degradation) recovers most of the "up to 10%" hit-ratio gain the paper
> attributes to per-workload retraining-interval tuning, *without* per-workload tuning, at
> ≤10% throughput cost.

- **Mechanism.** The retrain trigger is a fixed wall-clock comparison against
  `retrain_intvl = 86400` (`GLCache.c:288-303`, default set at `GLCache.c:30`). The training
  loop already parses per-round train/valid RMSE and early-stops on stability
  (`train.c:55-76`) — but `last_valid_loss` is a local and is thrown away. Persist it into
  `learner_t` (`GLCacheInternal.h:43-72`), and add a controller: if the new model's
  validation loss is close to the previous one *and* the interval miss ratio (already
  reported in `bin/cachesim/sim.c:47-58`, and derivable inside the cache from
  `cache_state_t.miss_ratio`, `GLCacheInternal.h:74-86`) is stable, lengthen the interval;
  if either jumps, shorten it. Do the same for the re-ranking cadence at `segSel.c:343`
  (`ranked_seg_pos >= n_ranked_segs * rank_intvl`), trading inference cost against staleness.
  Evaluate against the paper's own oracle: an offline sweep of fixed `retrain-intvl` per
  trace gives the per-workload-tuned upper bound the controller must approach.
- **Code locations.** `micro-implementation/libCacheSim/cache/eviction/GLCache/GLCache.c:288`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/train.c:55`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/GLCacheInternal.h:43`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/segSel.c:343`,
  `micro-implementation/libCacheSim/cache/eviction/GLCache/cacheState.h`.
- **Motivating evidence.** §4.6 verbatim: "the best retraining interval depends on the
  workload — some workloads show higher hit ratios with half-day retraining, and some others
  benefit from two-day retraining. While fine-tuning retraining intervals can improve the hit
  ratio by up to 10%, one-day retraining achieves a good performance across workloads." That
  is a quantified, self-declared 10% left on the table. §3.5 also justifies wall-clock
  retraining partly by *metastable-failure* avoidance, so any controller must be shown not to
  reintroduce that risk — a genuine design constraint, not a free lunch.
- **Feasibility: H.** The signals exist and are already computed; the change is confined to
  the trigger logic and one struct field, well under 500 LOC. The evaluation is the same
  sweep plus a fixed-interval oracle sweep (≈3× the compute of the base reproduction, still
  affordable on 16 cores).
- **Research value: M.** The paper itself identifies the opportunity and bounds it at 10%,
  so the ceiling is known and modest; and dynamic training-frequency adjustment has already
  been done for object-level learners. Still worth doing because nobody has shown whether the
  group-level signal is strong enough to drive the controller.
- **Scoop check.** Queries: `3L-Cache FAST 2025 ... dynamic training frequency parameter
  auto-tuning`; `"GL-Cache" ... 2024`. Closest work: **3L-Cache** (FAST'25) "dynamically
  adjusts the training frequency" and adds "a parameter auto-tuning method to enhance
  adaptability across traces" — same idea, but applied to an object-level learner, not to
  GL-Cache's group-level model or its ranking cadence. **Result: `partial`.**

### Idea deliberately dropped

An obvious fifth idea — *train one GBM offline on many traces and transfer it zero-shot to
unseen traces*, which would be nearly free to implement because `train.c:98-119` already has
`DUMP_MODEL`/`LOAD_MODEL` hooks — is **scooped**. "Learning-Augmented Heuristics: Simple, yet
Smart, Robust and Interpretable Cache Eviction" (arXiv:2608.27975, Aug 2026) trains exactly
one offline model on 4,140 production traces, evaluates zero-shot on 1,035 held-out traces,
explicitly discusses GL-Cache as the only prior periodic-prediction work, and compares
against GL-Cache, 3L-Cache, LRB, LHD, S3-FIFO. Do not spend the project on it.

## 6. Risks and open questions

1. **The LRB baseline is not in the repo.** grep for `LRB`/`lrb` across `repo/` hits only
   `README.md`. The headline claims "228× throughput / +7% hit ratio vs LRB" (Abstract, §4.4,
   Table 4) therefore require building the LRB authors' separate C++/LightGBM project and its
   own trace pipeline. Plan the reproduction *without* LRB and say so, or budget extra days.
   TinyLFU and Cachelib (Fig. 6) are likewise absent.
2. **Feature-count discrepancy.** The paper says seven features (§3.5, Fig. 9a includes a
   `write rate` bar); the code compiles six (`const.h:19` `N_FEATURE_NORMAL 6`,
   `dataPrep.c:105-110` — write rate is tracked but never fed to the model). Fig. 9 cannot be
   reproduced exactly. This is a finding worth reporting, but it also means "add the missing
   write-rate feature" is a trivial baseline everyone should run first.
3. **Build friction.** `CMakeLists.txt:120-122` clobbers `CFLAGS` on Linux, dropping
   `-std=gnu99`; GNU extensions (`strsep`, `strcasestr`) are used. `find_package(xgboost
   REQUIRED)` needs XGBoost's CMake config package — conda-forge may or may not ship it, in
   which case build XGBoost from source into `$HOME/local`. XGBoost ≥2.x may have moved the C
   API used in `train.c`/`inference.c`; pin ~1.7 (paper-era) first. No public CI: every
   hosted-runner job in `.github/workflows/build.yml` is commented out.
4. **Prototype is the risky half.** `prototype/Cargo.toml:26` and
   `src/l2cache/Cargo.toml:45-60` depend on three git repos (`twitter/rustcommon`,
   `1a1a11a/rustcommon`, `1a1a11a/rust-xgboost` rev `360af10`). If any has moved or fails to
   build with a modern rustc/bindgen, Fig. 6 and Fig. 13(a) are out of reach. Treat the
   micro-implementation as the deliverable and the prototype as stretch.
5. **Throughput measurement is easy to get wrong.** The multi-size path defaults to
   `--num-thread=16` (`cli.c:58`, `main.c:31-33`) and only the single-size path reports MQPS
   (`sim.c:68-75`). Any throughput comparison must be single-threaded and on an otherwise
   idle machine — and this is a *shared* machine per `env.md`, so throughput numbers will be
   noisier than the paper's dedicated CloudLab nodes. Report medians over repeats.
6. **Non-determinism.** `sim.c:16-17` seeds from `time(NULL)`, and `next_rand()` drives the
   fallback segment-selection paths (`segSel.c:183`, `segSel.c:306`). Runs are not bit-
   reproducible; pin the seed before doing any A/B comparison of an add-on.
7. **Frozen artifact.** Last commit 2023-05-12, 0 open issues, no releases. The authors are
   unlikely to answer questions. The maintained fork of the same code
   (`1a1a11a/libCacheSim`) is a better *build* target but has diverged; deciding which tree
   to modify is an early project decision with real consequences for comparability.
8. **Storage and download time.** ≈20 GB (CloudPhysics+MSR) + 23 GB (Wikimedia, compressed)
   over HTTP from a university FTP mirror; Wikimedia must be *decompressed* (≈67 GB) for the
   prototype. Fits in ~257 GB but leaves less slack than it first appears.
9. **Open question I could not settle by reading.** Whether the multi-bucket code path
   (add-on A2) is actually correct — it has never been exercised with `MAX_N_BUCKET > 1`, and
   several `DEBUG_ASSERT`s in `segSel.c:392-396` and `eviction.c:60-61` assume all merged
   segments share a bucket. Budget debugging time; "the dead path is broken" is a plausible
   early finding.

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; `pages/page-NN.png` for figures)
- Abstract & §1 (pp. 2–3): headline numbers, three categories of learned caches.
- Table 1 (p. 3): learning granularity / features / metadata bytes / throughput vs FIFO.
- §2.2.1 (p. 4): LRB 44 features, 189 B/object, 200 µs/eviction, ≤5,000 evictions/s.
- §3.1–3.2 (p. 5), Fig. 1: overview, amortization and signal-accumulation arguments.
- §3.3 (pp. 5–6), Fig. 2a/2b (page-06.png): write-time grouping; explicit list of unexplored
  grouping keys (tenant id, content type, object size).
- §3.4, Eq. 1–2 (p. 6): object and group utility, the `1/s_o` size term.
- §3.5 (p. 7), Fig. 3: seven features, XGBoost GBM, L2 regression, daily retraining, 8,000
  samples, ghost entries.
- §3.6 (p. 8), Fig. 4: merge-based eviction, `1/(size·age)` retention, "merging the N_merge
  least useful groups shows ... up to 20% decrease in hit ratio".
- §3.7, Table 2 (p. 8): `S_group`, `N_merge`, `F_eviction`.
- §4.1, Table 3 (pp. 8–9): 118 traces, GL-Cache-E/T parameters, CloudLab m510/c6420,
  3-day warmup, LRB retargeted to object miss ratio, LRB/LHD from authors' code.
- §4.2, Fig. 5 (p. 9, page-09.png): oracle group eviction ≈ size-aware Belady.
- §4.3, Fig. 6, Fig. 7 (pp. 9–10, page-10.png): prototype and micro-implementation hit ratios.
- §4.4, Table 4, Fig. 8 (p. 11, page-11.png): Wikimedia miss ratio/throughput; 228× / 586×;
  training 10–50 ms, inference 0.4–3 ms; 5 B object metadata.
- §4.5, Fig. 9a/9b/9c (p. 12): feature importance across traces and cache sizes.
- §4.6, Figs. 10–14 (pp. 12–13): sensitivity to `S_group`, `F_eviction`, `N_merge`;
  "fine-tuning retraining intervals can improve the hit ratio by up to 10%"; 1-day warmup.
- §Availability (p. 14): repo URL.

**Repository** (paths relative to `repo/`)
- `README.md` (repo structure, trace URL and binary format, Apache-2.0, citation)
- `micro-implementation/README.md`, `micro-implementation/scripts/setup.sh`,
  `micro-implementation/.github/workflows/build.yml`, `micro-implementation/LICENSE`
- `micro-implementation/CMakeLists.txt` (deps, `ENABLE_GLCACHE`, `USE_HUGEPAGE`,
  `SUPPORT_ZSTD_TRACE`, CFLAGS clobber)
- `micro-implementation/cmake/Modules/FindGLib.cmake`, `.../FindZSTD.cmake` (pkg-config)
- `micro-implementation/libCacheSim/include/config.h`,
  `.../include/libCacheSim/mem.h` (allocator macros)
- `micro-implementation/libCacheSim/cache/eviction/GLCache/` — `GLCache.c`,
  `GLCacheInternal.h`, `const.h`, `obj.h`, `init.c`, `dataPrep.c`, `train.c`, `inference.c`,
  `segSel.c`, `segment.c`, `eviction.c`, `README`
- `micro-implementation/libCacheSim/cache/cache.c` (admission hook, `cache_get_base`)
- `micro-implementation/libCacheSim/cache/eviction/` (baseline list incl. `LHD/`,
  `Cacheus.c`, `BeladySize.c`; **no LRB, no TinyLFU**)
- `micro-implementation/libCacheSim/bin/cachesim/` — `cli.c` (options, algorithm dispatch),
  `sim.c` (miss ratio + MQPS output), `main.c` (multi-size, byte miss ratio output)
- `micro-implementation/doc/quickstart_cachesim.md` (driver usage, `auto` sizes, `-e` params)
- `micro-implementation/data/trace.oracleGeneral.bin`, `trace.vscsi` (in-repo smoke traces)
- `micro-implementation/libCacheSim/dataStructure/hashtable/chainedHashtable.c`,
  `chainedHashTableV2.c` (the only `USE_HUGEPAGE` uses — `madvise`)
- `prototype/README.md`, `prototype/Cargo.toml`, `prototype/src/l2cache/Cargo.toml`,
  `prototype/src/l2cache/src/{eviction,learning,segments}/`

**External**
- Trace listings fetched from `https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/fast23_glcache/`
  (`cloudphysics/`: 106 files, 11 MB–781 MB; `msr/`: 14 files, 14 MB–665 MB;
  `wiki_2016u.oracleGeneral.zst`: 23 GB).
- `https://sysartifacts.github.io/fast` — FAST artifact evaluation began in 2024 ⇒ no badges
  possible for FAST'23.
- 3L-Cache, FAST'25 — https://www.usenix.org/conference/fast25/presentation/zhou-wenbin
- SL-Cache, DASFAA'26 — https://link.springer.com/chapter/10.1007/978-981-92-0363-5_36
- Learning-Augmented Heuristics (LAH / S4-FIFO), arXiv:2608.27975 —
  https://arxiv.org/abs/2608.27975
- Upstream maintained libCacheSim — https://github.com/1a1a11a/libCacheSim
