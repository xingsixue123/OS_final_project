# CAPSULE: A Storage Prefetcher Harnessing Spatio-Temporal Locality for Cloud-Scale Workloads

*Desk review only. Nothing was built, installed, or run. Every claim below is a prediction
backed by a paper section/figure or a repository path.*

## 1. Paper summary

**Problem.** Cloud block-storage workloads have working sets far larger than the cache and
long stack distances (LSD): blocks are reused only after millions of intervening accesses
(§2.1, §2.3). Replacement policies therefore evict blocks before reuse (LRU misses 84.4% of
CloudPhysics w85, §2.3), and temporal/association prefetchers such as Mithril only shave this
to 79.7%. The authors' measurement is that the missed LBAs are *not* random: applying DBSCAN
to the miss stream shows 37.4% (MSR) to 69.7% (CloudPhysics) of misses fall inside dense
spatial clusters (Table 1, §2.3).

**Key idea.** CAPSULE = "Clustering-Assisted Prefetching Scheme Utilizing Locality
Exploration". Replace DBSCAN's O(n²) ε-neighborhood with a cheap bucketed approximation:
`C_n = ⌊LBA/ε⌋` (Eq. 1, §4.2). Each `ClusterBucket` stores the LBAs seen in that bucket plus
links to left/right ε-neighbor buckets (Eq. 2, Algorithm 1). On a miss, CAPSULE prefetches the
frequently accessed members of the current bucket and of its two neighbors (Algorithm 2, §4.5).

**Design details.**
- Adaptive ε (§4.3): every 10,000 requests, sample the first 1,000 LBAs and score 11 candidate
  ε values {512 … 512K} with the Davies–Bouldin Index; "the ε yielding the **lowest** DBI score
  is selected".
- Member selection (§4.4): only prefetch LBAs seen ≥ t = 2 times.
- Metadata budget (§4.6): ≤ 10% of cache capacity, 104 B fixed per cluster + 5 B per LBA,
  LFU eviction of whole clusters (LRU was tried and rejected).
- I/O load control (§4.7): two-strike filter (a prefetched LBA unused twice is dropped from the
  candidate set) plus a rate cap of ≤ 100 prefetches per 100 requests. Both "heuristically chosen".
- Composability (§4, §5.2): CAPSULE is a *second chance* layer — OBL/PG/Mithril fire first, and
  CAPSULE supplies candidates when the primary prefetcher finds none (OBL-CAPSULE, MITHRIL-CAPSULE).

**Evaluation setup (§5.1, Table 3).** Trace-driven simulation only, on one desktop
(i7-10700K, 32 GB RAM, 1 TB SATA SSD, Ubuntu 18.04), using libCacheSim extended by 2,056 LOC,
plus IOBlazer for real-I/O timing. 729 traces: MSR 14, CloudPhysics 106, Tencent CBS 597,
Alibaba Block 5, Meta Tectonic 7. Default cache 256 MB, 4 KB blocks, metadata ≤ 10%.
Baselines: LRU, LFU, ARC, Belady, CACHEUS (eviction) and PG, OBL, Mithril, Baleen (prefetch).

**Headline numbers.**
- Fig. 8 / Table 4: MSR — OBL-CAPSULE averages **+43.56 %p** hit rate over OBL.
- Fig. 9a: CloudPhysics w94 — OBL-CAPSULE lifts hit rate 3.79% → 22.95% (**6.1×**);
  over all 106 CP traces CAPSULE adds 27.4% to OBL, 12.6% to Mithril (§5.2, Fig. 9b).
- Fig. 11: Tencent CBS 597 traces — OBL-CAPSULE +29.82 %p on average.
- Fig. 13 / Table 5: Meta Tectonic Region 1 — CAPSULE 70.71% vs Baleen 46.13%.
- §5.6, Fig. 21/22: on CloudPhysics w92 CAPSULE reaches 48.9% hit (vs 17.0% LRU) for 1.17× the
  device I/O; on msr_proj_4, 50.83% vs 5.71% for ~10% more I/O. Overhead: 0.47 µs per request
  for cluster assignment, 87.06 µs per ε update every 10K requests.

**Stated limitations (§7).** Prefetch pollution (CAPSULE loses to LRU/ARC on `msr_prxy_1` and to
Belady on `msr_proj_0`, visible in Fig. 8); the chosen traces intrinsically favour spatially
clustered prefetchers; no demand-vs-prefetch QoS/priority; no coordination between prefetchers
in distributed deployments; §5.5 explicitly suggests LSH-style locality-aware sharding as future
work because modulo sharding "destroys adjacency".

## 2. Artifact audit

**Provenance.** `github.com/imagesid/capsule`, stated in the paper itself (§1, last bullet of
the contributions). `README.md:3-10` self-identifies as the artifact for the SIGMETRICS 2026
camera-ready and declares the fork relationship to libCacheSim. GPL-3.0, HEAD `8a596dc`
(2026-01-08), 503 files / 12.9 MB, 0 stars, 0 issues (`repo_facts.json`). Fresh, single-author,
un-exercised by anyone else.

**Structure.** A fork of `libCacheSim` (`README.md:32-57` lists what is inherited vs added):

| paper component | code path |
|---|---|
| CAPSULE prefetcher shell (create/find/prefetch hooks) | `libCacheSim/cache/prefetch/Capsule.c` |
| **All** CAPSULE logic — clustering, DBI, LFU cluster eviction, load control | `libCacheSim/cache/prefetch/ClusterPrefetcher.h` (1,935 lines, `static` functions in a header) |
| Eq. 1 bucket assignment + member append (§4.2, §4.4) | `ClusterPrefetcher.h:605` `assignDataToCluster`, `:163` `computeCompositeIds` |
| Algorithm 2, neighbour prefetch (§4.5) | `ClusterPrefetcher.h:1027` `prefetchCluster` |
| Adaptive ε / DBI (§4.3) | `ClusterPrefetcher.h:1759` `preAssignment`, `:1542` `compute_dbi`, `:89` ε candidate array |
| Metadata budget + LFU cluster eviction (§4.6) | `ClusterPrefetcher.h:408` `evict_LFU_cluster`, `:84` `LFU_EVICTION`, `:605-698` budget check |
| I/O load control (§4.7) | `ClusterPrefetcher.h:65` `limiter`, `:54` `get_prefstat`, `:1119-1271` cap/2-strike checks |
| OBL-CAPSULE / MITHRIL-CAPSULE / PG-CAPSULE "second chance" (§4, §5.2) | `OBLCluster.c:164-195`, `Cluster4.c`, `PGCluster.c` |
| prefetcher registration / CLI names | `libCacheSim/include/libCacheSim/prefetchAlgo.h:55-90` |
| CLI knobs `--fixed --adaptive --neighbor --io --max-prefetch --max-metadata` | `libCacheSim/bin/cachesim/cli_parser.c:112-116`, `main.c:43-48` |
| IOBlazer real-I/O path (Fig. 21d/22d completion time) | `libCacheSim/bin/cachesim/sim.c:45-368` `mainx`, `ioblazer/ioblazer.h` |
| pure-simulation path (all hit-rate figures) | `libCacheSim/bin/cachesim/sim.c:373-484` `simulate` |

The implementation size matches the paper's "extended with 2,056 lines of code" (§5.1):
`Capsule.c` (244) + `ClusterPrefetcher.h` (1,935) ≈ 2.2k lines. This is the real system, not a stub.

**Eval scripts present.**
- Figure 8: `test/download-msr.sh` (14 named MSR oracleGeneral traces from
  `cache-datasets.s3.amazonaws.com/.../2007_msr`), `test/run-msr.py` (14 traces × 12 configs,
  256 MB, parses `miss ratio` from stdout into `logs/result-msr.csv`), `test/plot-msr.py`.
- Figure 9a: `test/download-cp.sh` (w90–w95), `test/run-cp.py`, `test/plot-cp.py`.
- `README.md:192-219` gives the exact three-command recipe for each.

**Eval scripts absent.** Everything else: Fig. 9b/11 heatmaps (106 + 597 traces), Fig. 12
(Alibaba), **Fig. 13 (Baleen comparison — no Baleen code, no Tectonic loader anywhere in the
repo; `grep -i baleen` returns nothing)**, Fig. 14/15 (ε variants — the flags exist, the sweep
script does not), Fig. 16/17 (cache-size sweep and the multi-tenant mix — no trace mixer),
Fig. 18/19 (two-level hierarchy / N storage nodes — `example/cacheCluster/main.cpp` is upstream
libCacheSim with consistent hashing, LRU only and **no prefetcher wiring**), Fig. 20 (metadata
budget sweep — `--max-metadata` exists, script does not), Table 5 (I/O counts).

**Build route on this machine.** `cmake .. && make -j` (`README.md:104-114`).
Dependencies from `CMakeLists.txt:155-192` and `doc/install.md`: **glib-2.0** (via pkg-config,
`cmake/Modules/FindGLib.cmake:30-34`), **argp** (in glibc 2.36), **zstd** (required, traces are
read compressed), **libaio** (`ioblazer/ioblazer.h:99` is unconditionally included by
`ClusterPrefetcher.h:25` and `sim.c:8`), tcmalloc optional, xgboost/LightGBM off by default.
None of these need root: conda-forge provides `glib`, `zstd`, `pkg-config`, `libaio`, or they
can be built into `$HOME` (libaio is a ~1k-line makefile project). cmake 3.25 on the machine
satisfies `cmake_minimum_required(3.12)`. gcc 12.2 ≥ the Ubuntu-18.04 gcc the authors used.

**Predicted build break (important).** `ClusterPrefetcher.h` is included by six translation
units (`Capsule.c:14`, `Cluster4.c:19`, `OBLCluster.c:23`, `PGCluster.c:27`, `Mithril.c:19`,
`OBL.c:23`) and contains *tentative definitions of non-static globals*:
`ClusterPrefetcher.h:883` `Point *points;`, `:1407` `int last_prefetched_cluster;`,
`:1408` `int next_ts;`. `ioblazer/ioblazer.h:1395-1402` does the same (`int fd;`,
`OUTSTANDING_IO x_outIO[MAX_OUT];`, `io_context_t x_ctx_id;`, `struct io_event *x_events;`) and
is included by seven TUs. gcc ≥ 10 defaults to `-fno-common`, so these become *multiple
definition* link errors; gcc 7 on Ubuntu 18.04 (the authors' platform, Table 3) defaulted to
`-fcommon` and linked fine. Expected fix: configure with `-DCMAKE_C_FLAGS=-fcommon`
(or add `static`). Budget half a day for this class of issue.

**Other build/run notes.**
- `.github/workflows/build.yml:38` calls `scripts/install_dependency.sh`, which does not exist
  in the repo — CI has never been green for this fork.
- `ioblazer/CMakeLists.txt:1` references `ioblazerbup.c`, which does not exist; harmless,
  because the top-level `CMakeLists.txt:360-373` globs `ioblazer/*.c` instead of using that file.
- `USE_HUGEPAGE=ON` (`CMakeLists.txt:21`) with a `sudo tee .../transparent_hugepage` comment is
  cosmetic: the macro is only used in `bulkChainingHashTable.c.unfinished`, which is not compiled,
  and it only guards `madvise(MADV_HUGEPAGE)`, which is unprivileged anyway.
- Both hot paths write debug logs to `/dev/shm` on essentially every request:
  `sim.c:417-428` opens/closes `/dev/shm/lll.txt` per request (fprintf commented out) and
  `ClusterPrefetcher.h:1291-1316` rewrites `/dev/shm/prefetched<N>.txt` and *appends* to
  `/dev/shm/lll.txt` on every prefetching request. Runtime tax and a shared-file hazard if runs
  are parallelised; `/dev/shm/lll.txt` is never truncated.

**Data.** All traces are the public `cacheMon/cache_dataset` oracleGeneral corpus
(`README.md:123-133`), hosted on `cache-datasets.s3.amazonaws.com`; MSR 2007, CloudPhysics 2015,
Tencent CBS 2020, Alibaba Block 2020, Meta Storage 2023 are all listed there. The two download
scripts fetch only 20 traces (~a few GB compressed), far inside the 257 GB free. The full
729-trace corpus is much larger (CloudPhysics alone is 2.1 B requests) — subsample rather than
mirror. Meta Tectonic traces for the Baleen comparison exist publicly but the *integration*
does not (see above).

**Dependency pin age.** `requirements.txt` is three unpinned lines (`numpy`, `pandas`,
`matplotlib`); `README.md:181-188` says Python 3.11. `test/plot-msr.py:26` uses
`matplotlib.cm.get_cmap`, removed in matplotlib 3.9 — the plot scripts need a pinned
`matplotlib<3.9` or a one-line edit. The C side has no pinned versions at all.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | URL given in the paper (§1 contributions: "We publicly release the source code and experimental artifacts at https://github.com/imagesid/capsule"); `README.md:3-10` names the SIGMETRICS 2026 camera-ready; the actual prefetcher is present (`libCacheSim/cache/prefetch/Capsule.c`, `ClusterPrefetcher.h`, ≈2.2k lines, matching §5.1's "2,056 lines of code"), plus baselines, CLI, and two figure-reproduction pipelines in `test/`. |
| `H2_no_root` | **pass** | The hit-rate results come from `simulate()` (`sim.c:373`), a pure user-space trace replay; `--io` defaults to false (`cli_parser.c:116`, `cli_parser.c:273`). The only privileged-looking pieces are optional or inert: the IOBlazer path hard-codes `/mnt/new_root` (`sim.c:63`, `sim.c:136`) but is off by default; `DEVICE_PATH "/dev/sdb"` (`ioblazer.h:178`) is an unused default; `USE_HUGEPAGE` only guards `madvise()` in an uncompiled `.unfinished` file; the `sudo` grep hits are in `.travis.yml` and a comment at `CMakeLists.txt:20`. No kernel module, eBPF, perf counter, or KVM anywhere. |
| `H3_hardware_fit` | **pass** | Single-machine trace simulation, no GPU. The paper's own platform (Table 3: 8-core i7, 32 GB RAM, 1 TB SATA SSD) is *weaker* than the target machine (16C/32T, 125 GB RAM, NVMe). Simulated cache 256 MB–32 GB (§5.4) fits in RAM; metadata is capped at 10% of cache (`ClusterPrefetcher.h:605-698`) plus a 1–4 M-entry `PrefStat` table of 2 B entries (`ClusterPrefetcher.h:890-896`). The only multi-node result (§5.5, Figs. 18/19) is itself a simulation of N sharded caches in one process, so it needs no second machine. |
| `H4_obtainable_deps_data` | **pass** | Deps (glib, zstd, libaio, argp, optional tcmalloc — `CMakeLists.txt:155-192`, `doc/install.md`) are all installable in user space via conda-forge or source builds into `$HOME`; no system package is unavoidable. Traces are the public cacheMon oracleGeneral corpus fetched by `test/download-msr.sh` and `test/download-cp.sh` over plain HTTPS from S3. Caveat, not a fail: the Baleen/Meta-Tectonic comparison (Fig. 13) cannot be redone from this repo because the Baleen integration is absent. |

## 4. Reproduction plan

**Target.** Figure 8 (§5.2) — hit rate of 12 policies on the 14 MSR traces — and the claim it
supports: *"OBL-CAPSULE achieves the highest hit rates, averaging a 43.56% improvement over
OBL"* (§5.2, restated in Table 4). Secondary, near-free target: Figure 9a (CloudPhysics
w90–w95) and its 6.1× w94 claim, via `test/download-cp.sh` + `test/run-cp.py` + `test/plot-cp.py`.

**Scale-down.** None required — Figure 8 runs at full paper scale (14 traces, 256 MB cache,
~410 M requests total, ~a few GB of zstd traces). If runtime bites, cut to the 6 traces the
paper discusses by name (`msr_web_2`, `msr_proj_0`, `msr_proj_4`, `msr_prxy_1`, `msr_hm_0`,
`msr_src1_0`) and drop `cacheus` (the slowest baseline). For the 729-trace claims, subsample
Tencent CBS to ~50 of 597 traces.

**Steps.**
1. `conda create -n capsule -c conda-forge python=3.11 glib zstd pkg-config libaio cmake make`
   (or build libaio from source into `$HOME/local`); pin `matplotlib<3.9` for `test/plot-*.py:26`.
2. `cmake -B _build -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_FLAGS=-fcommon -DENABLE_TESTS=OFF ..`,
   `make -j16`. Expect to fight `-fno-common` multiple-definition errors (§2) and the
   `-Wall -Wshadow -Winline` noise from `CMakeLists.txt:131-139`.
3. Smoke test: `./_build/bin/cachesim data/w25.oracleGeneral.bin.zst oracleGeneral lru 256MB
   --prefetch=CAPSULE` (`README.md:135-139`), confirm a `miss ratio` line is printed
   (`sim.c:462-468`) — this is what `run-msr.py:42` greps for.
4. `bash test/download-msr.sh` (~a few GB), `python test/run-msr.py`, `python test/plot-msr.py`;
   compare `logs/hit-msr.png` against `figures/hit-msr.png` and paper Fig. 8.
5. Repeat with `test/download-cp.sh` / `run-cp.py` / `plot-cp.py` for Fig. 9a.
6. Guard rails: truncate `/dev/shm/lll.txt` between runs; if parallelising across cores, patch
   out the `/dev/shm` writes (`sim.c:417-428`, `ClusterPrefetcher.h:1291-1316`) first, since all
   processes append to the same file.

**Effort.** ≈3–5 person-days (dominated by the no-root dependency bootstrap and the predicted
link-flag fix) + ≈10–20 CPU-hours for the 168 MSR runs plus 72 CloudPhysics runs; 0 GPU-hours.
Trivially parallel across the 16 cores once the `/dev/shm` logging is neutralised.

**Level: M.** Build instructions and a purpose-built script exist for exactly this figure, the
data download is scripted and public, and the workload fits the machine at paper scale — that
is H-grade. It is knocked to M by real porting work that reading the code makes near-certain:
apt-only dependency instructions (`doc/install.md`) must be replayed under conda without root,
gcc 12's `-fno-common` will very likely break the link given the header-scoped globals, the
plot scripts use a removed matplotlib API, and the repo has never been built by anyone outside
the author's machine (no green CI, `scripts/install_dependency.sh` missing, 0 issues/forks).
A further open question that only running can settle: `run-msr.py:74-88` uses default flags
(`--neighbor=false`, `--adaptive=true`, `--max-prefetch=100000`), and the paper never states
which variant produced Fig. 8 — the numbers may need a flag sweep to match.

## 5. Add-on ideas

### A1. Utility-driven ε selection (and the paper↔code divergence it exposes)

**Hypothesis.** We hypothesize that selecting the clustering granularity ε by an online
*prefetch-utility* criterion (hits per prefetched block over the previous window) improves hit
rate per prefetched block, compared with the released CAPSULE's ε selector, on the MSR and
CloudPhysics suites — and, more pointedly, that CAPSULE's published gains are insensitive to the
Davies–Bouldin criterion the paper credits them to.

**Mechanism.** Replace the selector in `preAssignment` with a sliding-window multi-armed bandit
(ε-greedy or UCB) over the 11 candidates in `ClusterPrefetcher.h:89`, rewarded by
(prefetched-and-later-hit)/(prefetched) measured from the existing `PrefStat` accounting. Run
four arms head-to-head on identical traces: (i) the artifact's selector as released,
(ii) true *minimum*-DBI as §4.3 describes, (iii) best fixed ε chosen offline per trace,
(iv) the bandit. Report hit rate *and* prefetch volume, so the comparison is on the Pareto
frontier rather than hit rate alone.

**code_locations.** `libCacheSim/cache/prefetch/ClusterPrefetcher.h:1759` (`preAssignment`,
the selection loop is at 1877-1917), `libCacheSim/cache/prefetch/ClusterPrefetcher.h:1542`
(`compute_dbi`), `libCacheSim/bin/cachesim/cli_parser.c:113`, `test/run-msr.py`.

**Motivating evidence.** §4.3 states "the ε yielding the **lowest** DBI score is selected, as a
lower DBI indicates more compact and well-separated clusters". The artifact does the opposite:
`ClusterPrefetcher.h:1892` keeps the candidate with `if (dbi > best_dbi)` (maximum DBI), and
before that, line 1884 short-circuits (`if(pickme) … break;`) on the *first, i.e. smallest* ε
that yields any bucket with more than `min` members (`min = 25` when `sparse`, else 5,
`ClusterPrefetcher.h:1545-1548, 1592-1594`). So the released "adaptive ε" is a density
threshold, not a DBI minimiser. The paper's own Fig. 14 corroborates that the criterion may not
matter: fixed ε = 512 K reaches ~52% hit rate on `msr_proj_4` while adaptive variants sit at
45–50%, adaptive winning only on prefetch volume. Either outcome of this experiment is
publishable: a better selector, or evidence that the paper's central adaptive mechanism is not
the source of its numbers.

**feasibility: H.** One function plus a small bandit (<300 LOC), evaluated with the existing
`test/run-msr.py` / `run-cp.py` harness and the existing `--fixed`/`--adaptive` flags on this
machine. Well inside 10 weeks for 2–4 students.

**research_value: H.** It targets the paper's headline novelty (adaptive, DBI-guided
clustering) at exactly the point where the artifact and the text disagree, and it separates
"spatial clustering helps" from "this particular clustering-quality metric helps". A SIGMETRICS
reviewer or artifact evaluator would care about both possible answers.

**scoop_check: clear.** Queries: "CAPSULE clustering-assisted prefetching scheme storage
prefetcher SIGMETRICS 2026 Ramadhan Choi" (only the paper itself and the SIGMETRICS 2026
accepted-papers page); "spatial region based history prefetcher block storage LBA bitmap 2025".
Nothing cites or re-examines CAPSULE (paper is March 2026, repo created 2026-01-06 with 0 stars
and 0 forks). Adaptive prefetch-granularity selection exists in the CPU world (DSPatch,
Bingo — [arXiv:1910.03075](https://arxiv.org/pdf/1910.03075)), but no re-audit of CAPSULE's ε
selector exists.

### A2. Demand/prefetch priority split in the cache (a real prefetch buffer)

**Hypothesis.** We hypothesize that inserting CAPSULE's prefetched blocks into a bounded,
low-priority segment that is promoted to the main stack only on a demand hit improves hit rate
on pollution-prone traces (`msr_prxy_1`, `msr_proj_0`, the two where the paper's own Fig. 8
shows prefetching losing to LRU/ARC/Belady), without regressing the traces where CAPSULE wins.

**Mechanism.** Today `prefetchCluster` evicts from and inserts into the single shared cache at
full priority (`ClusterPrefetcher.h:1140-1147`, repeated at 1204-1212 and 1256-1262). Add a
`is_prefetched` bit to the cache object, implement a segmented-LRU wrapper (probationary segment
sized as a tunable fraction of the cache, demand hits promote, prefetch insertions can only
evict other un-hit prefetched blocks), and expose the segment fraction as a CLI flag. Sweep the
fraction 0–100% so the paper's current behaviour is the endpoint of the sweep.

**code_locations.** `libCacheSim/cache/prefetch/ClusterPrefetcher.h:1027` (`prefetchCluster`),
`libCacheSim/cache/cache.c:254` (prefetch hook in `cache_get_base`),
`libCacheSim/cache/eviction/LRU.c`, `libCacheSim/bin/cachesim/cli_parser.c:112`.

**Motivating evidence.** §7: "prefetches may waste cache space and evict useful demand-fetched
data. This behavior is already evident in Figure 8, where prefetching techniques underperform
Belady in workloads such as `msr_proj_0`, and even lag behind LRU and ARC in `msr_prxy_1`."
Also a paper↔code gap: Fig. 6 and §4 describe prefetched blocks landing in a distinct "prefetch
buffer" with its own LFU eviction, but the code inserts them straight into the shared cache
governed by the user-selected eviction policy.

**feasibility: H.** Localized (a bit on the cache object + one eviction wrapper, a few hundred
LOC), evaluated with the existing MSR/CP harness at 256 MB, no new data.

**research_value: M.** It fixes a limitation the authors name and would likely produce a real
win on the regression cases, but "insert prefetches at lower priority / segregate prefetch
buffer" is a well-established technique, so a reviewer would find a positive result expected.

**scoop_check: partial.** Query: "storage cache prefetch low-priority insertion prevent cache
pollution block trace libCacheSim 2025". The general technique is prior art in CPU caches —
[Mitigating Prefetcher-Caused Pollution Using Informed Caching Policies for Prefetched Blocks,
TACO 2015](https://dl.acm.org/doi/10.1145/2677956), and
[Reducing cache pollution of prefetching in a small data cache](https://ieeexplore.ieee.org/document/955085/).
No work applies it to CAPSULE or to cluster-based storage prefetching on these traces.

### A3. Cost-aware prefetch controller replacing the fixed 100-per-100 rate cap

**Hypothesis.** We hypothesize that replacing CAPSULE's fixed prefetch rate cap and its
2-strike aliased utility filter with a closed-loop controller that targets a measured
prefetch-accuracy setpoint improves hit rate at equal or lower *total storage I/O* (the Table 5
metric) under prefetch-dominated workloads such as CloudPhysics w92.

**Mechanism.** (a) Replace `get_prefstat`, which indexes a 1–4 M-entry table by
`lba % PREFSTAT_TABLE_SIZE` and therefore conflates unrelated LBAs from a 10⁹-wide address
space, with a tagged or counting-Bloom structure. (b) Replace the constant
`limiter.prefetch_limit` with AIMD control on measured accuracy, and make the per-cluster degree
adaptive rather than the global `--max-prefetch` constant. (c) Report hit rate per prefetched
block, not just hit rate.

**code_locations.** `libCacheSim/cache/prefetch/ClusterPrefetcher.h:54` (`get_prefstat`),
`libCacheSim/cache/prefetch/ClusterPrefetcher.h:65` (`limiter`),
`libCacheSim/cache/prefetch/ClusterPrefetcher.h:1027` (cap and 2-strike checks at 1119-1271),
`libCacheSim/bin/cachesim/cli_parser.c:112`.

**Motivating evidence.** §4.7 concedes "Both parameters are heuristically chosen based on
empirical observation". §5.6 reports that without load control CAPSULE issues ~16 M requests
(70.2% hit) vs ~9.4 M with it (48.9% hit) on w92 — a huge, unexplored operating curve that a
single constant currently collapses to one point. Table 5 shows prefetch I/O of 2.3 M vs
Mithril's 1.4 M on Alibaba ns101, and Fig. 21a shows CAPSULE's I/O budget consumed almost
entirely by speculation. The hard-coded `BILLION_L = 3000` override
(`ClusterPrefetcher.h:1909`, `ioblazer/ioblazer.h:119`) that raises the cap 30× for large-LBA
traces is an undocumented magic constant that the controller would subsume.

**feasibility: H.** Confined to three functions in one header plus a CLI flag; measured with
counters the code already keeps; no new traces.

**research_value: M.** The I/O-efficiency axis is under-explored in the paper and the aliasing
bug is real, but feedback-directed prefetch throttling is a well-known idea
(FDP, AMP), so a positive result is expected rather than surprising.

**scoop_check: partial.** Query: "feedback directed adaptive prefetch aggressiveness accuracy
timeliness storage cache AMP adaptive multi-stream prefetching degree control". Prior art:
[Feedback Directed Prefetching, HPCA 2007](https://dl.acm.org/doi/abs/10.1109/HPCA.2007.346185),
[APAC: an accurate and adaptive prefetch framework](https://par.nsf.gov/servlets/purl/10251073),
and AMP (FAST'07), which the paper itself cites as a baseline family. Nothing applies feedback
control to CAPSULE's cluster prefetcher, and the `PrefStat` aliasing defect is specific to this
artifact.

### A4. Tenant-aware cluster metadata under multi-tenant mixes

**Hypothesis.** We hypothesize that partitioning CAPSULE's cluster table and metadata budget per
tenant (separate ε per tenant, per-tenant LFU victim pools, proportional budget shares) improves
both aggregate hit rate and the worst-tenant hit rate under the multi-tenant mix of §5.4,
compared with the paper's single global cluster table.

**Mechanism.** Extend `CompositeClusterId` with a tenant/namespace id so that numerically
overlapping LBAs from different tenants cannot land in the same ε-bucket; keep one LFU list per
tenant in `lfu_buckets`; split the 10% metadata budget by equal or hit-rate-proportional shares.
Build the missing harness: a trace mixer that interleaves MSR `msr_proj_4`, CloudPhysics w85,
Tencent `ns11904` and Alibaba `ns105` into one stream with a tenant tag (the paper's Fig. 17
setup, ~19.8 M requests), and report per-tenant as well as aggregate hit rate.

**code_locations.** `libCacheSim/cache/prefetch/ClusterPrefetcher.h:100`
(`CompositeClusterId`) and `:152` (`clusterHashTable`),
`libCacheSim/cache/prefetch/ClusterPrefetcher.h:408` (`evict_LFU_cluster`),
`libCacheSim/cache/prefetch/ClusterPrefetcher.h:605` (`assignDataToCluster`),
`test/run-cp.py`.

**Motivating evidence.** Multi-tenancy is the paper's stated motivation (§1: "cloud storage
environments, where multi-tenancy and dynamic scheduling result in highly heterogeneous
workloads"; §2.3 repeats it). Yet §5.4's multi-tenant experiment simply concatenates four
traces into one request stream, and the implementation keeps exactly one global ε
(`ClusterPrefetcher.h:841`), one global cluster hash table, and one global LFU victim pool — so
one aggressive tenant can evict another's clusters, and unrelated tenants' LBAs collide in the
same buckets. The paper reports only aggregate hit rate for Fig. 17, never per-tenant, so
interference is entirely unmeasured.

**feasibility: M.** The id change touches every `switch (scheme)` site in the header and the
multi-tenant harness (mixer + per-tenant accounting) does not exist in the repo and must be
written. Compute is cheap; engineering is cross-cutting.

**research_value: H.** It attacks the regime the paper claims as its target and never actually
isolates, the measurement (per-tenant hit rate / interference) is new for this system, and a
negative result — "clustering is robust to tenant mixing because LBA ranges rarely collide" —
would be an equally useful characterisation.

**scoop_check: partial.** Query: "multi-tenant interference storage cache prefetching per-tenant
isolation block cache 2026". Multi-tenant *cache-space* partitioning is well covered —
[OC-Cache](https://ranger.uta.edu/~sjiang/pubs/papers/wang18-oc-cache.pdf),
[NyxCache, FAST'22](https://research.cs.wisc.edu/wind/Publications/fast22-kan.pdf),
[Delta Fair Sharing](https://arxiv.org/pdf/2601.20030) — but partitioning a *prefetcher's*
clustering metadata per tenant, and measuring prefetcher interference specifically, was not
found.

### A5. Locality-preserving sharding for the multi-node hierarchy

**Hypothesis.** We hypothesize that replacing modulo/hash sharding with a locality-preserving
mapping (range or LSH-based, so numerically adjacent LBAs stay on one node) raises CAPSULE's
per-node hit rate at 4–16 simulated storage nodes, especially on MSR, where the paper reports
CAPSULE *degrading* beyond eight nodes.

**Mechanism.** Wire a prefetcher into the (currently LRU-only, consistent-hash) cluster
simulator, add a pluggable shard function (modulo-N as the paper's baseline, fixed-range, and
p-stable LSH), and reproduce the paper's two-level setup: per-client LRU absorbing short-term
reuse, per-node server cache running LRU / Mithril / CAPSULE, 256 MB per node, N ∈ {2,4,8,16}.
Report hit rate and cross-node prefetch redundancy.

**code_locations.** `example/cacheCluster/main.cpp`,
`example/cacheCluster/consistentHash.c`, `example/cacheCluster/include/cacheCluster.hpp`,
`libCacheSim/include/libCacheSim/prefetchAlgo.h:55`.

**Motivating evidence.** §5.5 verbatim: "MSR is an exception — it dips slightly beyond eight
nodes as spatial locality fragments under modulo sharding… Simple hashing destroys adjacency by
scattering nearby LBAs across nodes. A locality-aware mapping such as LSH could co-locate
proximate LBAs, which would further improve CAPSULE's prefetch efficiency." The paper also
admits the Fig. 19 gains are confounded ("increasing the node count also increases aggregate
cache capacity"), so a properly capacity-controlled re-run is itself a contribution.

**feasibility: M.** `example/cacheCluster` is upstream libCacheSim scaffolding with no
prefetcher plumbing (`main.cpp:55-60` builds `Cache(size, algo, hashpower)` only) and is not
even added by the top-level `CMakeLists.txt`; the whole Fig. 18/19 harness must be rebuilt.
Compute stays trivial (still one process, one machine).

**research_value: M.** The paper explicitly names this as the fix, so a positive result is the
expected outcome; the interesting part is the capacity-controlled ablation rather than the
mechanism itself.

**scoop_check: clear.** Query: "locality preserving sharding LSH distributed cache prefetching
co-locate adjacent blocks storage nodes". LSH sharding exists generally
([Layered LSH](https://web.stanford.edu/~ashishg/papers/darpa_unpub2.pdf)) but nothing applies
it to prefetcher-aware block-cache sharding; no follow-up to CAPSULE exists.

## 6. Risks and open questions

1. **`-fno-common` link failure is likely.** Non-static globals are defined in headers included
   by 6–7 translation units (`ClusterPrefetcher.h:883,1407,1408`; `ioblazer/ioblazer.h:1395-1402`).
   gcc 12.2 on this machine defaults to `-fno-common`; the authors' gcc 7 did not. Mitigation is
   a one-line `-DCMAKE_C_FLAGS=-fcommon`, but budget time for cascading fixes.
2. **Paper↔code divergences that may change what "reproducing CAPSULE" means.** (a) ε selection
   maximises DBI / picks the first dense bucket rather than minimising DBI (§4.3 vs
   `ClusterPrefetcher.h:1877-1917`). (b) Algorithm 1's ε-neighbour test (Eq. 2, the `dist ≤ ε`
   check) is not implemented — `setLeftNeighbor`/`setRightNeighbor` (`ClusterPrefetcher.h:935-948`)
   are empty stubs, the `Cluster` struct (`:120-149`) has no left/right fields, and
   `prefetchCluster` unconditionally walks buckets ±1 (`:1070-1077`). (c) §4.6 says LRU cluster
   eviction was evaluated and rejected, but `evict_LRU_cluster` is commented out
   (`ClusterPrefetcher.h:650`). (d) Cluster members are appended without de-duplication
   (`:765-767`, `:816-818`), so a repeatedly missed LBA occupies several metadata slots, which
   interacts with the 10% budget claim in §4.6 and Fig. 20.
3. **Which configuration produced Figure 8 is unstated.** `test/run-msr.py:74-88` uses CLI
   defaults (`--neighbor=false`, `--adaptive=true`, `--max-prefetch=100000`,
   `--max-metadata=0.1`) while §5.3 evaluates neighbour-on variants; the paper never pins the
   Fig. 8 configuration. Expect a flag sweep before the numbers line up.
4. **Only 2 of ~15 figures have scripts.** Figs. 9b, 11, 12, 13, 14–20 and Table 5 have no
   harness; in particular the Baleen/Meta-Tectonic comparison (Fig. 13, the largest single
   claimed margin, +24.58 %p) cannot be re-run from this repository at all.
5. **Global mutable state in a header.** All CAPSULE state is `static` file scope in
   `ClusterPrefetcher.h`, duplicated per translation unit and never reset. Any add-on that wants
   two caches, two tenants, or two prefetchers in one process (A4, A5) must first refactor this
   state into the `prefetcher_t->params` struct — a prerequisite cost, not a blocker.
6. **`/dev/shm` side-effects.** `sim.c:417-428` and `ClusterPrefetcher.h:1291-1316` open, write,
   and append to `/dev/shm/lll.txt` and `/dev/shm/prefetched<N>.txt` on the request path, never
   truncating. On a shared machine this both taxes runtime and makes parallel runs collide.
7. **Unverifiable by desk review.** Whether the simulator actually reaches the reported miss
   ratios; whether zstd trace reading, `belady`, and `cacheus` all work in this fork; actual
   per-run wall-clock; the on-disk size of the 20 downloaded traces. All require running.
8. **Novelty risk for the add-ons.** A2 and A3 restate techniques that are textbook in the CPU
   prefetching literature; their contribution must be framed as *quantifying them for
   cluster-based storage prefetching on public cloud traces*, not as new mechanisms.

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; `pages/page-12.png` read for Fig. 8/9 layout)
- Abstract, §1 (pp. 1-3): motivation, 6.1× / 1.89× headline, artifact URL, three-stage design.
- §2.1 (p. 3-4): stack distance, LSD.
- §2.3, Table 1, Table 2 (pp. 5-7): trace counts (729), X_c clustering fractions, miss rates with
  DBSCAN/K-Means/MeanShift/K-Medoids.
- §3 (pp. 6-7): candidate clustering algorithms, DBSCAN chosen.
- §4.2, Eq. 1-2, Algorithm 1 (pp. 8-9): `C_n = ⌊LBA/ε⌋`, ε-neighbour definition and assignment.
- §4.3 (p. 9): adaptive ε every 10,000 requests, 1,000-LBA sample, 11 candidates, "lowest DBI".
- §4.4-4.5, Algorithm 2 (pp. 9-10): t = 2, current + left + right cluster prefetch.
- §4.6 (p. 10): 10% metadata budget, 104 B/cluster + 5 B/LBA, LFU cluster eviction.
- §4.7 (p. 10): two-strike filter, 100 prefetches per 100 requests, "heuristically chosen".
- §5.1, Table 3 (p. 11): platform, libCacheSim + 2,056 LOC, IOBlazer, 729 traces, 256 MB / 4 KB.
- §5.2, Figs. 8, 9a, 9b, 10, 11, 12, 13, Table 4 (pp. 11-14): +43.56 %p MSR, 6.1× w94,
  +29.82 %p Tencent, +39.16 %p Alibaba, Baleen comparison.
- §5.3, Figs. 14, 15 (pp. 14-15): ε variants, fixed 512K vs adaptive, neighbour on/off.
- §5.4, Figs. 16, 17 (pp. 15-16): cache-size sweep 128 MB–32 GB, 4-workload multi-tenant mix.
- §5.5, Figs. 18, 19 (pp. 16-17): two-level hierarchy, modulo sharding, LSH future-work remark.
- §5.6, Fig. 20, Figs. 21-22, Table 5 (pp. 18-20): metadata budget sweep, 0.47 µs/request,
  I/O counts with and without load control.
- §7 (pp. 21-22): pollution limitation, trace bias, no QoS, no prefetcher coordination.

**Repository** (`repo/`)
- `README.md` (artifact statement, deps, build, run flags, Fig. 8/9a recipes, dataset URL)
- `CMakeLists.txt` (deps at 155-192, source globs at 279-373, flags at 131-147, hugepage at 83)
- `doc/install.md` (apt-based dependency list incl. `libaio-dev`)
- `requirements.txt` (unpinned numpy/pandas/matplotlib)
- `libCacheSim/cache/prefetch/Capsule.c` (prefetcher hooks, params, metadata accounting)
- `libCacheSim/cache/prefetch/ClusterPrefetcher.h` (:54 `get_prefstat`, :65 `limiter`,
  :89 ε array, :100/:120/:152 cluster structures, :408 `evict_LFU_cluster`, :605
  `assignDataToCluster`, :650 commented-out LRU eviction, :883/:1407-1408 header globals,
  :885 `init`, :935-948 empty neighbour stubs, :1027 `prefetchCluster`, :1119-1271 rate cap,
  :1291-1316 `/dev/shm` logging, :1542 `compute_dbi`, :1759 `preAssignment`, :1877-1917
  ε selection, :1909 `BILLION_L` override)
- `libCacheSim/cache/prefetch/OBLCluster.c:164-195` (OBL then CAPSULE second chance)
- `libCacheSim/cache/prefetch/Cluster4.c`, `PGCluster.c`, `Mithril.c`, `OBL.c`, `PG.c`
- `libCacheSim/include/libCacheSim/prefetchAlgo.h:55-90` (prefetcher name registration)
- `libCacheSim/bin/cachesim/cli_parser.c:112-116, 269-273` (CAPSULE flags and defaults)
- `libCacheSim/bin/cachesim/main.c:32-48` (flags plumbed into the cache struct)
- `libCacheSim/bin/cachesim/sim.c:8, 45-368` (ioblazer path, `/mnt/new_root`), `:373-484`
  (simulation path, `miss ratio` output, `/dev/shm` logging)
- `libCacheSim/cache/cache.c:180-259` (`handle_find` / `prefetch` hook sites)
- `libCacheSim/cache/eviction/LRU.c`, `LFU.c` (eviction policies for A2)
- `test/download-msr.sh`, `test/run-msr.py`, `test/plot-msr.py`, `test/download-cp.sh`,
  `test/run-cp.py`, `test/plot-cp.py`
- `example/cacheCluster/main.cpp`, `consistentHash.c`, `include/cacheCluster.hpp`
- `ioblazer/ioblazer.h:99, 117-119, 178, 1395-1402`, `ioblazer/ioblazer.c:2`,
  `ioblazer/CMakeLists.txt:1`
- `cmake/Modules/FindGLib.cmake:30-34`, `Findargp.cmake`, `FindZSTD.cmake`
- `.github/workflows/build.yml:38` (missing `scripts/install_dependency.sh`)
- `figures/hit-msr.png`, `figures/hit-cp.png` (author-produced versions of Figs. 8 and 9a)
- `repo_facts.json`, `fetch_result.json` (provenance, HEAD 8a596dc 2026-01-08, GPL-3.0)

**External**
- [cacheMon/cache_dataset](https://github.com/cacheMon/cache_dataset) — public oracleGeneral
  corpus (MSR 2007, CloudPhysics 2015, Tencent CBS 2020, Alibaba Block 2020, Meta Storage 2023).
- [ACM DL record for the paper](https://dl.acm.org/doi/10.1145/3788088) and the
  [SIGMETRICS 2026 accepted papers list](https://www.sigmetrics.org/sigmetrics2026/accepted.html)
  — no artifact badge shown for this paper.
