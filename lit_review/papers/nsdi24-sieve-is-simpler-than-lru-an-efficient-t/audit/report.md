# SIEVE is Simpler than LRU: an Efficient Turn-Key Eviction Algorithm for Web Caches

*Desk review only. Nothing in this repository was built or executed. Every claim below is
traceable to a paper section/figure or a repository path.*

## 1. Paper summary

**Problem.** Cache eviction algorithms have grown steadily more complex (ARC, LIRS, LHD,
CACHEUS, LRB, GLCache), and the complexity buys little in production: per-object metadata
grows, critical sections lengthen, parameters need tuning, and implementations are
bug-prone (§2.2, "The trouble with complexity" — the authors report finding two distinct
LIRS bugs in two open-source simulators). Consequently almost all deployed caches still
run FIFO or LRU (§1).

**Key idea.** SIEVE is a one-line-of-thought change to FIFO-Reinsertion/CLOCK. Both keep a
single FIFO queue with a per-object *visited* bit. CLOCK moves a retained ("survived")
object to the head; SIEVE leaves it exactly where it is and instead advances a `hand`
pointer from tail toward head (Fig. 1, Fig. 2, Alg. 1 on p.5). Because survived objects
accumulate and the hand skips over them, the hand spends most of its time near the head,
where newly admitted objects sit — so SIEVE gets *lazy promotion* (no work on a hit beyond
setting a bit) and *quick demotion* (new objects are examined almost immediately) from one
pointer and one bit (§3.1, §2.3). SIEVE has **zero parameters** (§4.4).

**Design/analysis.** §5.2 gives the invariant: for two consecutively retained objects, the
one closer to the head has the smaller inter-examination time, so any retained object's
inter-arrival time is bounded by the tail object's inter-examination time (Eq. 1). The
"mesh size" of the sieve therefore self-adjusts: more evictions in a round ⇒ longer tail
inter-examination time ⇒ more objects retained next round. §5.3 illustrates this on
synthetic Zipfian workloads (Fig. 8 miss ratio and "popular object ratio" vs. size; Fig. 9
vs. skew α and hand-position-over-time; Fig. 10 adaptivity across a workload changeover).

**Implementation.** Simulation in libCacheSim (§3.2); prototypes in five production
libraries — CacheLib (C++), groupcache (Go), mnemonist (JS), lru-dict (Python+C), lru-rs
(Rust) — at ≤21 LOC each (Table 2, p.8).

**Eval setup.** §4.1: 1559 traces, 7 datasets, 247 B requests / 14.9 B objects (Table 1,
p.6). Two of the seven datasets — CDN1 (1273 traces) and CDN2 (219 traces) — are
**proprietary**; the other five (Tencent Photo, Wiki CDN, Twitter KV, Meta KV, Meta CDN =
67 traces) are public. Metric is miss-ratio reduction from FIFO; cache sizes are 0.1% and
10% of each trace's object footprint. Simulations ran on CloudLab; throughput ran on a
c6420 (dual-socket Xeon Gold 6142, 384 GB), turbo off, threads pinned to one NUMA node.

**Headline numbers.**
- Efficiency: SIEVE has the lowest miss ratio on >45% of the 1559 traces vs. 15% for the
  runner-up (TwoQ) (Abstract, Fig. 5a p.7). Up to 63.2% lower miss ratio than ARC, mean
  1.5% (§4.2). Fig. 4a (p.7): SIEVE beats every other algorithm on **all four** of the
  small public datasets (Meta KV, Meta CDN, Wiki, Tencent) at the large cache size.
- Throughput: in CacheLib, 17% faster than optimized LRU at 1 thread and >2× at 16 threads
  (Fig. 6, p.8).
- Primitive: replacing LRU with SIEVE inside ARC/TwoQ/LeCaR improves all three;
  ARC-SIEVE reduces ARC's miss ratio by 3.7% mean, up to 62.5% (Fig. 12a/b, p.12).
  With oracle foresight, SIEVE-Belady is best on 97%/94% of traces (Fig. 12c).

**Stated limitations.** §4.2: at the 0.1% cache size TwoQ and LHD sometimes win, because
"new objects cannot demonstrate their popularity before being evicted"; TwoQ avoids this
by reserving a fixed 25% for new objects. §7.1/Fig. 14: LRB beats SIEVE on byte miss ratio
at 1–2% cache sizes. §7.2: **"SIEVE is not scan-resistant"** — on block workloads SIEVE is
sometimes worse than LRU, and "having a ghost is critical to be scan-resistant" at small
cache sizes. §7.3: TTL-friendliness is *claimed* but never evaluated.

## 2. Artifact audit

### Repo structure

`repo/` is a shallow clone of `github.com/cacheMon/NSDI24-SIEVE` (head `0861f82`,
2024-08-01, Apache-2.0, 87 stars, 1 open issue). Top level is `README.md`, `doc/`,
`mydata/`, and `libCacheSim/` — the latter being a **snapshot of libCacheSim**
(`repo/README.md:14`), ~78 kLOC C/C++ plus ~5.9 kLOC Python.

The repository contains only the **simulator**. The five prototypes are external links
(`repo/README.md:63-67` → `cacheMon/groupcache`, `cacheMon/mnemonist`, `cacheMon/lru-rs`,
`cacheMon/lru-dict`, `Thesys-lab/cachelib-sosp23`). Nothing under `repo/` is thread-safe.

### Paper component → code path

| paper component | code path |
|---|---|
| SIEVE algorithm (Alg. 1, §3.1) | `libCacheSim/libCacheSim/cache/eviction/Sieve.c` — `Sieve_evict` at :218-232 is the hand loop; `Sieve_find` :125-133 sets the visited bit; `Sieve_insert` :146-153 prepends |
| per-object visited bit (Table 3, 17 B) | `libCacheSim/libCacheSim/include/libCacheSim/cacheObj.h:173` (`Sieve_obj_params_t sieve`); `Sieve.c:58-62` sets `obj_md_size = 1` |
| SIEVE-Belady (Fig. 12c) | `libCacheSim/libCacheSim/cache/eviction/belady/Sieve_Belady.c`, plus `LRU_Belady.c`, `FIFO_Belady.c` |
| baselines of Fig. 3/4 | `eviction/ARC.c`, `LIRS.c`, `TwoQ.c`, `Cacheus.c`, `Hyperbolic.c`, `Clock.c` (registered as `clock`/`fifo-reinsertion`/`second-chance`), `WTinyLFU.c` (registered as `tinylfu`), `LHD/` (C++), `LFU.c`, `FIFO.c`, `LRU.c` |
| B-LRU (Bloom-filter LRU) | not an eviction algo — it is `lru` + `--admission bloom-filter`, `cache/admission/bloomfilter.c` |
| LRB (Fig. 14) | `eviction/LRB/lrb.cpp` — behind `ENABLE_LRB` (OFF by default, needs LightGBM) |
| algorithm registry / CLI | `libCacheSim/libCacheSim/bin/cachesim/cache_init.h` (`sieve` at :139-140, `sieve-belady` at :128-129), `bin/cachesim/cli_parser.c` |
| fractional cache sizes (0.001 / 0.1 of footprint) | `bin/cachesim/cli_parser.c:426-451` (`conv_cache_sizes`) and `:453-483` (8 auto sizes `{0.001,0.003,0.01,0.03,0.1,0.2,0.4,0.8}`) |
| spatial trace sampling (scale-down lever) | `bin/cachesim/cli_parser.c:304-307` → `traceReader/sampling/spatial.c:33` (`--sample-ratio`) |
| synthetic Zipfian workloads (§5.3, Figs. 8–11) | `libCacheSim/scripts/data_gen.py` (`gen_zipf`, writes `oracleGeneral` binary) |
| MRC plotting | `libCacheSim/scripts/plot_mrc_size.py`, `plot_mrc_time.py` |
| **ARC-SIEVE / TwoQ-SIEVE / LeCaR-SIEVE (Fig. 12a/b)** | **absent.** Grepping `Sieve_init` callers (`QDLP.c:131`, `WTinyLFU.c:142`, `S3FIFOd.c:127`, `test/common.h:256`, `example/cacheSimulatorConcurrent/main.cpp:47`) shows SIEVE is only composed into S3FIFO-style algorithms. `eviction/fifo/LP_ARC.c:110-120` is ARC-over-**Clock** (`"LP-ARC-Clock"`), not ARC-over-SIEVE. |
| **CacheLib throughput prototype (Fig. 6)** | **absent** — external repo `Thesys-lab/cachelib-sosp23` |
| Fig. 3/4 box-plot scripts | `libCacheSim/scripts/priv/plot/plot_mr_red_box.py` + `load_miss_ratio.py` — present but **internal/stale**: `plot_mr_red_box.py:265-266` hardcodes `/disk/cphy/result/`, its algorithm list (`S3FIFO_delay-0.1000-2-0.50`) does not match any paper figure, and `load_miss_ratio.py:15` imports `scripts.str_utils`, which does not exist (the module is at `libCacheSim/scripts/utils/str_utils.py`). |

### Build route on this machine

`repo/README.md:22` says `cd scripts && bash install_dependency.sh && bash
install_libcachesim.sh`. `libCacheSim/scripts/install_dependency.sh:3-6` is
`sudo apt install libglib2.0-dev libgoogle-perftools-dev build-essential cmake
google-perftools xxhash`, plus a source build of zstd 1.5.0 (`:46-56`) ending in
`sudo make install`, plus XGBoost and LightGBM (`:16-44`) — also with `sudo make install`.
**None of this is required as written.** From `libCacheSim/CMakeLists.txt`:

- `find_package(GLib REQUIRED)` (:141) and `find_package(argp REQUIRED)` (:146) — glib is
  on conda-forge; `argp` is part of glibc on Linux (`cmake/Modules/Findargp.cmake`).
- ZSTD is required when `OPT_SUPPORT_ZSTD_TRACE=ON` (default, :150-162) — conda-forge
  `zstd`. This matters: it lets traces stay `.zst`-compressed on disk.
- tcmalloc is **optional** (:169-177, prints "cannot find tcmalloc" and continues).
- `ENABLE_GLCACHE` (XGBoost) and `ENABLE_LRB` (LightGBM) are **OFF by default** (:23, :26),
  so neither ML dependency is needed for any figure except Fig. 14.
- `USE_HUGEPAGE=ON` (:21) only compiles in `madvise(..., MADV_HUGEPAGE)`
  (`dataStructure/hashtable/chainedHashTableV2.c:102`), which is a per-process hint needing
  no root and failing harmlessly; it can also be set `OFF`.

So the route is: conda env with `glib zstd cmake gperftools`, then
`cmake .. -DUSE_HUGEPAGE=OFF -DENABLE_TESTS=ON && make -j`. gcc 12.2 / cmake 3.25.1 on the
target machine satisfy `cmake_minimum_required(3.12)` and `CMAKE_CXX_STANDARD 17`.

### Dependency age

C/C++ deps are stable and old-but-fine (glib2, zstd, gperftools). Python side is only
`numpy` + `matplotlib` (`scripts/plot_mrc_size.py:6-7`, `scripts/data_gen.py:19`) with no
pinned versions and no `requirements.txt` — trivially satisfiable under Python 3.12.
`libCacheSim/.travis.yml` and `libCacheSim/dockerfile` are dead weight, not build paths.

### Data / trace sources

`repo/README.md:52-58` links five public dataset directories on
`ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/` (tencentPhoto, wiki,
twitter, metaKV, metaCDN). CDN1 and CDN2 are proprietary and **not** linked (paper Table 1
marks them so). Traces are in `oracleGeneral` format: 24 bytes/request
(`traceReader/customizedReader/oracle/oracleGeneralBin.h:24`, fields `real_time, obj_id,
obj_size, next_access_vtime`), readable zstd-compressed. Bundled tiny data:
`libCacheSim/data/trace.oracleGeneral.bin`, `data/twitter_cluster52.csv`,
`data/twitter_cluster52_10m.csv.zst`, and `mydata/zipf/zipf_1.0`.

Raw sizes implied by Table 1 × 24 B: Twitter ≈ 4.7 TB, Tencent ≈ 136 GB, Wiki ≈ 69 GB,
Meta KV ≈ 39 GB, Meta CDN ≈ 5.5 GB. **The full public corpus does not fit in ~257 GB
uncompressed**; keeping traces `.zst` and subsetting Twitter is mandatory.

### Eval scripts present / absent

Present and usable: `cachesim` CLI (multi-algorithm, multi-size, fractional sizes,
`--num-thread`, `--sample-ratio`, `--admission`), `scripts/plot_mrc_size.py`,
`scripts/plot_mrc_time.py` (Fig. 7b/7c style), `scripts/data_gen.py` (§5.3 workloads),
`scripts/traceAnalysis/*`, `test/` with CTest.
Absent or unusable: any driver that sweeps a trace *corpus* and emits Figs. 3/4/5/12/13;
the "popular object ratio" metric of Figs. 8b/9b/10b (grep finds no implementation); the
CacheLib throughput harness; the SIEVE-composed algorithms of Fig. 12a/b.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper §Availability (p.13): "The code and data used in this work are open-sourced at https://github.com/cacheMon/NSDI24-SIEVE." `fetch_result.json` confirms that URL was cloned. The clone contains the real algorithm (`libCacheSim/libCacheSim/cache/eviction/Sieve.c`, 287 lines), all Fig. 3 baselines, and the CLI that produces the paper's miss ratios — not a stub. |
| `H2_no_root` | **pass** | No kernel module, eBPF, KVM, or `/proc/sys` write anywhere in the tree. `sudo` hits are confined to the convenience installer `libCacheSim/scripts/install_dependency.sh:4,9,28,43,55` and dead CI (`libCacheSim/.travis.yml`); every one of those packages (glib, zstd, gperftools, xxhash, cmake) is conda-forge-installable in user space, and XGBoost/LightGBM are not needed because `ENABLE_GLCACHE`/`ENABLE_LRB` default OFF (`libCacheSim/CMakeLists.txt:23,26`). `CMakeLists.txt:20` mentions `sudo tee .../transparent_hugepage` but only as a comment; the code path is `madvise(MADV_HUGEPAGE)` (`chainedHashTableV2.c:102`), unprivileged, and `-DUSE_HUGEPAGE=OFF` removes it. `libCacheSim/dockerfile` is optional. **One caveat:** Fig. 11 (instructions/request) was measured with `perf stat` (§6.1), which is blocked by `perf_event_paranoid=3` — that single figure needs a substitute (valgrind/callgrind, which is user-space). It is not a headline result. |
| `H3_hardware_fit` | **pass** | The artifact is a CPU-only, single-node, user-space simulator; no GPU, no network, no second machine. The paper's own throughput evaluation used 16 threads (§4.1, Fig. 6), matching this machine's 16 cores. Full-corpus simulation at paper scale does not fit (see §4), but the CLI supports exactly the needed scale-downs: fractional cache sizes (`cli_parser.c:426-451`), `--num-req` cap (`cli_parser.c:140-142`), and spatial object sampling (`cli_parser.c:304-307` → `traceReader/sampling/spatial.c:33`), and the claim under test (relative miss-ratio ranking of algorithms on a trace) survives subsetting the trace *corpus*. |
| `H4_obtainable_deps_data` | **pass** | Deps: glib/zstd/gperftools/cmake via conda, numpy+matplotlib via pip — all user-space (`CMakeLists.txt:141-177`, `scripts/plot_mrc_size.py:6-7`). Data: five of seven datasets are publicly downloadable and directly linked from the artifact (`repo/README.md:52-58`, ftp.pdl.cmu.edu). CDN1/CDN2 (1492 of 1559 traces) are proprietary, but the paper's own public set includes three CDN object-cache datasets (Wiki CDN, Tencent Photo, Meta CDN) that serve as the substitute regime, and Fig. 3c/3f, Fig. 4 and 5 of the Twitter/Meta/Wiki/Tencent columns rest entirely on public data. Recorded as a risk in §6, not a fail. |

## 4. Reproduction plan

**Target.** **Figure 4a (p.7)** and the corresponding columns of **Figure 5a**: *"SIEVE
outperforms all other algorithms on all four datasets [Meta KV, Meta CDN, Wiki CDN, Tencent
Photo] at the large cache size"* (§4.2, "Four small datasets"). This is the paper's
strongest efficiency claim that rests **100% on public traces** (13 traces total), it is
crisply falsifiable (is SIEVE's miss-ratio-reduction-from-FIFO the maximum among the 10
baselines, per trace?), and it exercises the exact code path the paper's contribution lives
in. Secondary/stretch target: Fig. 3c (Twitter, 54 traces, large cache).

**Scale-down.**
1. Keep every trace `.zst`-compressed on disk (supported by default,
   `CMakeLists.txt:150-162`); download Meta KV (5), Meta CDN (3), Wiki (3), Tencent (2)
   first — 13 traces, the smallest of the public sets. Skip CDN1/CDN2 entirely (proprietary).
2. For Tencent (1038 M objects) run with `--sample-ratio 0.05` and for Twitter with
   `--sample-ratio 0.01`; spatial sampling preserves per-object popularity structure and
   is the library's own supported downscale (`traceReader/sampling/spatial.c`).
3. Run **one algorithm at a time** with both cache sizes
   (`./cachesim TRACE oracleGeneral sieve 0.001,0.1 --ignore-obj-size 1 --num-thread 16`)
   rather than 11 algorithms × 2 sizes concurrently — `main.c:35` builds
   `n_algo × n_size` live caches in memory, and at 10% of a 1 B-object footprint each cache
   is multiple GB. Serial-by-algorithm keeps peak RSS in the low tens of GB on a machine
   with 111 GB available and shared.
4. Skip `--consider-obj-metadata` (paper §4.2 ignores object size in the efficiency
   section anyway: `--ignore-obj-size 1`).

**Steps.**
1. `conda create -n sieve -c conda-forge glib zstd gperftools cmake numpy matplotlib`.
2. `cd libCacheSim && mkdir _build && cd _build && cmake .. -DUSE_HUGEPAGE=OFF && make -j16`
   (skip `install_dependency.sh` entirely). Verify with `ctest` (`test/CMakeLists.txt`) and
   with the bundled smoke test from `README.md:29`
   (`./_build/bin/cachesim data/trace.oracleGeneral.bin oracleGeneral sieve 1gb`).
3. Sanity-check the pipeline end-to-end on the synthetic Zipfian trace:
   `python3 scripts/data_gen.py -m 1000000 -n 100000000 --alpha 1.0 --bin-output zipf1.0.bin`
   then `scripts/plot_mrc_size.py --algos=fifo,lru,clock,sieve` — this should reproduce the
   qualitative ordering of Fig. 8a (SIEVE < ARC ≈ LFU < LRU).
4. Download the 13 public traces; run the 11-algorithm sweep
   (`sieve,arc,tinylfu,twoq,lirs,lhd,cacheus,hyperbolic,clock,lru` + `lru --admission
   bloom-filter` for B-LRU) at sizes `0.001,0.1`.
5. Write ~80 lines of Python to parse `result/<trace>` lines (format fixed at
   `bin/cachesim/main.c:62-69`) into miss-ratio-reduction-from-FIFO and redraw Fig. 4 /
   Fig. 5. **Do not** try to reuse `scripts/priv/plot/plot_mr_red_box.py` — it has a broken
   import (`load_miss_ratio.py:15`) and hardcoded `/disk/` paths (`:265-266`).

**Effort.** ≈ 4–6 person-days (1–2 d build + smoke test, 1 d trace download/staging, 1 d
sweep babysitting, 1–2 d re-deriving the plotting) + ≈ 200–400 CPU-core-hours (0 GPU-hours)
+ ~120 GB of disk for the compressed public traces.

**Level: M.** Not H, for three concrete reasons: (a) the dependency installer assumes root
and must be re-derived under conda; (b) the scripts that actually draw the paper's figures
are internal, stale and broken (`scripts/priv/plot/*`), so the per-trace aggregation has to
be rewritten; (c) two of seven datasets are proprietary and the public corpus needs
subsetting/sampling to fit 257 GB and 125 GB RAM. Not L, because the algorithm, all ten
baselines, the fractional-cache-size convention, the sampling lever, and a working
single-trace MRC script all ship in the repo, the binary is a self-contained CLI, and there
is no GPU/kernel/network dependency anywhere. No artifact-evaluation badge was found for
this paper (see §6), so "Results Reproduced" evidence is not available to lean on.

## 5. Add-on ideas

---

### A1 — SIEVE-Ghost: buying scan resistance without buying complexity

**Hypothesis.** We hypothesize that augmenting SIEVE with a small FIFO ghost queue of
recently-evicted object IDs — on a ghost hit, admitting the object with its visited bit
already set so the hand skips it once — reduces miss ratio below LRU and below plain SIEVE
on **block/storage traces containing scan and loop patterns** at small cache sizes
(0.1–1% of footprint), while costing <0.5 percentage points of miss ratio and <10% of
throughput on the web traces of Fig. 4.

**Mechanism.** Clone `Sieve.c` into `Sieve_Ghost.c`. Add `cache_t *ghost` initialized as a
`FIFO_init` over IDs only, exactly as S3FIFO does (`S3FIFO.c:117-130`); in `find`, probe the
ghost with `ghost->remove(ghost, req->obj_id)` (the S3FIFO idiom at `S3FIFO.c:247-250`
returns `true` on a ghost hit); in `insert`, set `obj->sieve.freq = 1` instead of `0`
(`Sieve.c:150`) when the insert followed a ghost hit; in `evict`, push the victim's ID into
the ghost before `cache_evict_base` (`Sieve.c:231`). Register `sieve-ghost` in
`cache_init.h` next to `sieve` (:139), declare the init in `evictionAlgo.h` (:166), and add
the file to the eviction `CMakeLists.txt`. Sweep ghost size as a fraction of cache size to
produce an efficiency-vs-metadata curve — the point being to report the *price* of scan
resistance in the paper's own currency (Table 3's LOC and bytes/object).

**Code locations.**
- `libCacheSim/libCacheSim/cache/eviction/Sieve.c`
- `libCacheSim/libCacheSim/cache/eviction/S3FIFO.c`
- `libCacheSim/libCacheSim/cache/eviction/CMakeLists.txt`
- `libCacheSim/libCacheSim/bin/cachesim/cache_init.h`
- `libCacheSim/libCacheSim/include/libCacheSim/evictionAlgo.h`
- `libCacheSim/scripts/priv/traceUtils/customized/msr_convert.py`

**Motivating evidence.** §7.2 verbatim: *"SIEVE is not scan-resistant… Since SIEVE does not
use a ghost cache… it cannot recognize the popular objects when they are requested again.
This problem is less severe on the large cache size, but when the cache size is small, we
observe that having a ghost is critical to be scan-resistant. We conjecture that not being
scan-resistant is probably the reason why SIEVE remained undiscovered over the decades."*
The paper states the diagnosis and the suspected cure, and evaluates neither. Note the
tension the paper never resolves: SIEVE's entire pitch is simplicity/zero-parameters
(§4.4), and a ghost adds both metadata and a size knob — so a negative result ("the ghost
costs more than it earns") is as publishable as a positive one.

**Feasibility: H.** One new ~300-line file plus four registration lines; the ghost
machinery is already written and debugged two files over in `S3FIFO.c`. Evaluation uses the
existing `cachesim` CLI on MSR Cambridge / CloudPhysics / Alibaba-Tencent block traces,
which are small (single-digit GB) and public, and the repo even ships a converter
(`scripts/priv/traceUtils/customized/msr_convert.py`). CPU-only, no root, comfortably
inside 10 weeks for 2–4 students.

**Research value: M.** It attacks the paper's own headline limitation and would turn SIEVE
from a web-cache algorithm into a general primitive, which an NSDI/FAST reviewer would care
about. Marked down from H because the *direction* is anticipated by the paper itself and by
ARC/S3FIFO/LIRS — a reviewer's first reaction will be "of course a ghost helps scans." The
value lives in the quantification (how much ghost, at what metadata cost, and does the
web-workload win survive), not the idea.

**Scoop check: partial.** Searched: *"SIEVE cache eviction scan resistance ghost cache
extension"*; *"SIEVE-k OR scan-resistant SIEVE OR adaptive SIEVE 2025"*; *"libCacheSim
SIEVE variant ghost queue block trace"*. Closest work:
[Marc Brooker, "Why Aren't We SIEVE-ing?"](https://brooker.co.za/blog/2023/12/15/sieve.html)
sketches **SIEVE-k** (a saturating k-bit counter instead of a bit) as a scan-resistance
idea — a blog post, not a paper, and a *different* mechanism (counter, not ghost).
[ISC, "SIEVE – A Better Algorithm Than LRU?" (2025)](https://www.isc.org/blogs/2025-sieve/)
restates the scan-resistance concern from an operator's view. Upstream libCacheSim's
`develop` branch still ships only a single `Sieve.c` with no ghost/`SieveK` variant
(checked github.com/1a1a11a/libCacheSim/tree/develop/libCacheSim/cache/eviction). No peer-
reviewed follow-up found. Because SIEVE-k is publicly floated, the project should include
SIEVE-k as a *baseline* rather than claim it.

---

### A2 — An adaptive hand floor for the small-cache regime

**Hypothesis.** We hypothesize that preventing SIEVE's hand from advancing into the newest
*f* fraction of the queue — with *f* adapted online from the observed survival rate of
newly inserted objects rather than fixed — reduces miss ratio at the 0.1%-of-footprint
cache size on the public CDN and KV traces, closing SIEVE's gap to TwoQ and LHD, without
regressing at the 10% cache size.

**Mechanism.** `Sieve_evict` (`Sieve.c:218-232`) walks `obj->queue.prev` until it finds
`freq == 0`, with the only wrap condition being `obj->queue.prev == NULL` (i.e., the head).
Add a position counter and a floor: if the hand reaches within `f · n_obj` of the head,
wrap it to `q_tail` instead of continuing, so the freshest *f* of the queue is never an
eviction candidate — SIEVE's structural analogue of TwoQ's fixed 25% reservation
(`TwoQ.c`). The adaptive variant maintains two counters (objects examined in the head
region / objects retained there) and moves *f* by a multiplicative update, preserving the
paper's zero-user-facing-parameter property. Evaluate at the paper's exact sizes
(`0.001,0.1` via `cli_parser.c:426-451`) against `sieve`, `twoq`, `lhd`, `arc`.

**Code locations.**
- `libCacheSim/libCacheSim/cache/eviction/Sieve.c`
- `libCacheSim/libCacheSim/cache/eviction/TwoQ.c`
- `libCacheSim/libCacheSim/bin/cachesim/cache_init.h`
- `libCacheSim/libCacheSim/bin/cachesim/cli_parser.c`

**Motivating evidence.** §4.2: *"When the cache is very small, TwoQ and LHD sometimes
outperform SIEVE… The primary reason for SIEVE's relatively poor performance is that new
objects cannot demonstrate their popularity before being evicted when the cache size is
very small… TwoQ does not suffer from the small cache sizes because it reserves a fixed 25%
of the cache space for new objects, preventing overly aggressive demotion."* Visible in
Fig. 3d–f (small-cache boxplots, where SIEVE is no longer the clear leader) and Fig. 5b
(TwoQ wins both Meta datasets at the small cache size). §5.3/Fig. 9c independently shows
the hand "lingers at positions close to the head for most of the time", which is exactly
the behaviour this add-on bounds.

**Feasibility: H.** Roughly 50–150 LOC confined to one function plus a registration line.
The evaluation harness, cache sizes, baselines and traces are all the reproduction setup
from §4 — marginal compute cost. Clearly doable by 2–4 students in 10 weeks.

**Research value: M.** It targets the precise regime the paper concedes, and the adaptive
formulation is a genuine design question (SIEVE's selling point is having no knobs, so a
self-tuning floor is the only version that preserves the thesis). Marked down from H
because a fixed reservation is a well-trodden idea (TwoQ 1994, S3FIFO 2023) and a modest
small-cache win would not surprise a reviewer.

**Scoop check: clear.** Searched: *"SIEVE cache small cache size limitation improve quick
demotion reserve new objects follow-up 2025 2026"*; *"SIEVE-k OR adaptive SIEVE"*. Found
only the original paper, the authors' `;login:` article, and popular-press coverage
(techxplore, Emory News). The adaptive-parameter literature that does exist attaches to
*other* algorithms — e.g.
[SCION (arXiv 2605.01055)](https://arxiv.org/html/2605.01055) selects among six unmodified
expert policies (SIEVE being one) via a workload fingerprint, and
[Learning-Augmented Heuristics / S4-FIFO (arXiv 2608.27975)](https://arxiv.org/html/2608.27975v1)
adds tunable knobs to **S3-FIFO**, explicitly not to SIEVE. Nothing modifies SIEVE's hand.

---

### A3 — How much of the SIEVE-Belady gap is reachable with O(1) state?

**Hypothesis.** We hypothesize that a decision-maker using only O(1) per-object state
available at eviction time (a 2–4-bit saturating access counter plus the object's insertion
age in hand-revolutions) recovers a measurable fraction — we will test ≥30% — of the
miss-ratio gap between SIEVE and the oracle SIEVE-Belady of Fig. 12c, on the public traces
at both the 0.1% and 10% cache sizes, at <10% added work per request.

**Mechanism.** `belady/Sieve_Belady.c` already implements the oracle rule from §6.2 —
reinsert the hand's candidate iff its next access is within `C/mr`. Step 1: build an
instrumented variant that, at each eviction decision, logs `(access_count, insertion_age,
queue_position, oracle_label)`. Step 2: fit a tiny offline model (decision stump / logistic
regression / small table, scikit-learn, CPU-seconds) on one dataset. Step 3: inline the
learned predicate as a lookup table into a new `Sieve_Learned.c` and evaluate on *held-out*
datasets. Step 4: report the recovered fraction of the oracle gap, and the cost in
metadata bytes against Table 3's 17 B/object. Because `perf stat` is unavailable on the
target machine (`perf_event_paranoid=3`), substitute `valgrind --tool=callgrind` (pure
user-space) for the instructions-per-request methodology of Fig. 11, or report wall-clock
only and say so.

**Code locations.**
- `libCacheSim/libCacheSim/cache/eviction/belady/Sieve_Belady.c`
- `libCacheSim/libCacheSim/cache/eviction/Sieve.c`
- `libCacheSim/libCacheSim/include/libCacheSim/cacheObj.h`
- `libCacheSim/libCacheSim/bin/cachesim/cache_init.h`
- `libCacheSim/libCacheSim/cache/eviction/LHD/lhd.cpp`

**Motivating evidence.** §6.2 / Fig. 12c: with foresight, *"SIEVE achieves the lowest miss
ratio on 97% and 94% of the 1559 traces at the large and small cache size"* — the paper
itself frames this as *"the case that we have a perfect decision-maker choosing between the
eviction candidates suggested by multiple simple eviction algorithms"* and then stops.
That is a large, explicitly-measured, explicitly-unexploited headroom, and it is the direct
test of the paper's own "SIEVE as a turn-key cache primitive" thesis (§6.1). §7.1 gives the
counter-hypothesis to beat: *"When the cache size is large, most objects in the cache have
few requests. Without enough features, a learned model can provide little benefit."*

**Feasibility: M.** Cross-cutting: needs a feature-logging build, an offline training
pipeline that does not exist in the repo, a new eviction algorithm, and a train/test trace
split protocol. All CPU-only and all data is already local, and LHD/GLCache/LRB in-tree show
how learned policies plug into this codebase — but this is meaningfully more than a
localized patch, and the `perf` substitution adds friction.

**Research value: H.** It converts a figure the paper waves at into a quantitative answer,
and *either* outcome teaches something: if a 4-bit counter captures a third of the oracle
gap, SIEVE's primitive thesis is vindicated cheaply; if it captures nothing, that is
concrete evidence for §7.1's claim that eviction-time features are exhausted, which bears
directly on the whole learned-caching line (LRB, GLCache, LHD).

**Scoop check: partial.** Searched: *"learning-augmented cache eviction SIEVE Belady gap
2025"*; *"arxiv 2025 cache eviction builds on SIEVE"*; *"libCacheSim SIEVE variant 2025"*.
Closest:
[Learning-Augmented Heuristics / S4-FIFO (arXiv 2608.27975)](https://arxiv.org/html/2608.27975v1)
— same *philosophy* (simple heuristic in the data plane, learning off the critical path)
and same simulator (libCacheSim), but it tunes **S3-FIFO's** cache-level knobs from
aggregate workload features, explicitly *not* object-level eviction decisions and not
SIEVE; it also never references the SIEVE-Belady headroom.
[SCION (arXiv 2605.01055)](https://arxiv.org/html/2605.01055) picks among unmodified
policies. Neither targets the oracle gap inside SIEVE. Rated *partial* because a reviewer
will ask how this differs from S4-FIFO, and the project must answer that up front
(object-level vs. cache-level; oracle-gap-anchored vs. knob-tuning).

---

### A4 — Reproducing SIEVE's scalability claim without CacheLib

**Hypothesis.** We hypothesize that a concurrent SIEVE built on a sharded hash table with a
lock-free visited bit and a single lock taken only on the eviction path sustains ≥1.8× the
throughput of a promotion-suppressing LRU at 16 threads on the Meta KV and Twitter traces,
and that the resulting races on the hand pointer perturb the miss ratio by <0.1 percentage
points relative to the serial simulator.

**Mechanism.** Build a standalone multi-threaded benchmark under `example/`, modelled on
`example/cacheSimulatorConcurrent/main.cpp` — which today parallelizes *independent*
simulations (`simulate_with_multi_caches`, :56-58), not a shared cache, and so cannot
answer this question. Make `Sieve_obj_params_t::freq` (`cacheObj.h:173`) an atomic byte
written with a relaxed store on hit (`Sieve.c:129`), shard the chained hash table
(`dataStructure/hashtable/chainedHashTableV2.c`), and take a single spinlock only inside
`Sieve_evict` (`Sieve.c:218-232`). Baseline: an LRU with CacheLib's 60-second promotion
suppression (described in §4.3) implemented over the same sharded table, so the comparison
is apples-to-apples. Sweep 1/2/4/8/16 threads as in Fig. 6; additionally report the
miss-ratio delta vs. the serial `cachesim` run, which the paper never measures.

**Code locations.**
- `libCacheSim/example/cacheSimulatorConcurrent/main.cpp`
- `libCacheSim/libCacheSim/cache/eviction/Sieve.c`
- `libCacheSim/libCacheSim/include/libCacheSim/cacheObj.h`
- `libCacheSim/libCacheSim/dataStructure/hashtable/chainedHashTableV2.c`
- `libCacheSim/libCacheSim/cache/eviction/LRU.c`

**Motivating evidence.** The scalability claim in the abstract ("twice the throughput of an
optimized 16-thread LRU implementation") and Fig. 6 rest entirely on a CacheLib prototype
that is **not in this repository** — `repo/README.md:67` points at the external
`Thesys-lab/cachelib-sosp23`, and §4.4 footnote 6 admits CacheLib's LRU optimizations make
the SIEVE diff unquantifiable, so it is excluded from Table 2. Independent confirmation on
a different substrate is therefore genuinely missing. Separately, the paper's core
throughput argument — "cache hits require no locking" (Abstract) — is never paired with a
measurement of what those unsynchronized hits cost in *accuracy*.

**Feasibility: M.** Needs a new harness and careful concurrent-code review; the repo gives
no thread-safe cache to start from. It does fit the machine: 16 cores match the paper's
thread count, and scaling the cache to ≤4 GB per thread (vs. the paper's `4 × nthread` GB,
which would demand 64 GB at 16 threads on a *shared* 125 GB box) keeps it safe. No root, no
GPU. Compute is trivial; the risk is engineering time and correctness debugging.

**Research value: M.** Making a headline result verifiable outside a 100-kLOC production
library is real value, and the miss-ratio-under-races measurement is an unmeasured quantity
that matters to anyone shipping SIEVE (the several lock-free Go/Rust SIEVE ports in the
wild all make this assumption implicitly). Not H because it is confirmatory rather than
novel — the expected answer is "the claim holds."

**Scoop check: partial.** Searched: *"SIEVE lockfree concurrent cache implementation"*;
*"SIEVE scalability reproduction 2025"*. Several independent lock-free SIEVE
implementations exist — [opencoff/go-sieve](https://github.com/opencoff/go-sieve)
advertises "lockfree, concurrent cache" — so the *artifact* is not novel; but none of them
publish a controlled scalability-vs-optimized-LRU comparison or a miss-ratio-under-races
measurement, which is the research content here. No academic follow-up found.

---

## 6. Risks and open questions

1. **1492 of 1559 traces are proprietary.** CDN1 (1273) and CDN2 (219) are marked
   proprietary in Table 1 and are not in `repo/README.md:52-58`. The abstract's flagship
   statistic ("lower miss ratio than 9 algorithms on >45% of the 1559 traces") can
   therefore never be reproduced as stated — only the 67-trace public subset is reachable.
   Any project must reframe the claim in terms of the public datasets, and Fig. 3a/3b/3d/3e
   are permanently out of reach.
2. **The paper's figure-drawing scripts are internal and broken.**
   `scripts/priv/plot/load_miss_ratio.py:15` imports `scripts.str_utils`, which does not
   exist in the tree; `plot_mr_red_box.py:265-266` hardcodes `/disk/cphy/result/` and plots
   algorithms (`S3FIFO_delay-0.1000-2-0.50`) that appear in no paper figure. Budget a day
   to rewrite the aggregation from the stable `main.c:62-69` output format.
3. **Fig. 12a/b is not reproducible from this repo at all.** ARC-SIEVE, TwoQ-SIEVE and
   LeCaR-SIEVE do not exist here — `eviction/fifo/LP_ARC.c:110-120` is ARC-over-Clock, and
   no `Sieve_init` caller composes SIEVE into ARC/TwoQ/LeCaR. If a team wants the "SIEVE as
   primitive" result, they must implement it themselves (which, incidentally, is a fifth
   plausible add-on).
4. **Fig. 6 (throughput/scalability) requires an external artifact.** `Thesys-lab/cachelib-sosp23`
   is a fork of Meta's CacheLib — a very large C++ build with folly/fbthrift dependencies,
   historically Docker-oriented. Porting it to a rootless conda environment is a serious,
   unbounded risk; A4 exists precisely to route around it.
5. **`perf` is unavailable on the target machine** (`perf_event_paranoid=3`), so §6.1 /
   Fig. 11's instructions-per-request methodology cannot be replicated directly. Substitute
   `valgrind --tool=callgrind` (user-space, no root) and state the substitution; note the
   two tools count differently, so absolute numbers will not match the paper.
6. **Memory is the real constraint, not CPU.** `bin/cachesim/main.c:35` instantiates
   `n_algo × n_size` caches simultaneously via `simulate_with_multi_caches`. Naively running
   11 algorithms × 2 sizes on Tencent (1038 M objects, 10% cache) would need hundreds of GB.
   The machine is also shared (111 GB available at measurement time, not guaranteed). Run
   algorithms serially and/or use `--sample-ratio`.
7. **`--sample-ratio` fidelity is unverified.** Spatial object sampling
   (`traceReader/sampling/spatial.c`) is the cheapest scale-down, but neither the paper nor
   the repo documents how much it perturbs the *relative ranking* of algorithms at a given
   cache size. A team relying on it should first validate it on Meta CDN (small enough to
   run both sampled and unsampled) before trusting it on Tencent/Twitter.
8. **No artifact-evaluation badge found.** The USENIX presentation page returned HTTP 403
   to automated fetch and no badge evidence appears in the repository or README, so there is
   no "Results Reproduced" signal to lean on. Treat as unverified rather than absent.
9. **The repo is a frozen snapshot, not upstream.** `libCacheSim/` here is pinned at
   2024-08-01 while upstream `1a1a11a/libCacheSim` has continued to evolve (e.g. a
   `3LCache` directory now exists upstream that is absent here). Development should happen
   against this snapshot for fidelity to the paper's numbers; rebasing onto upstream would
   silently change baselines.
10. **Scoop pressure is rising in the neighbourhood.** CacheBench (UCSC/OSPO, 2025) is
    re-running 18+ algorithms including SIEVE over 8000+ traces on libCacheSim, and SCION /
    S4-FIFO both build on libCacheSim with learned components. A pure re-evaluation of SIEVE
    is close to scooped; the add-ons above are not, but the team should re-run the scoop
    check at proposal time.

## 7. Evidence index

**Paper.**
Abstract (p.2) · §1 Introduction & Fig. 1 (p.2–3) · §2.1 Web caches / access patterns (p.3)
· §2.2 Cache eviction policies, "increasing complexity", "the trouble with complexity" (p.4)
· §2.3 Lazy promotion & quick demotion (p.4) · §3.1 SIEVE design, Fig. 2, Alg. 1 (p.4–5) ·
§3.2 Implementation — libCacheSim + five libraries (p.5) · Table 1 datasets, incl.
proprietary CDN1/CDN2 (p.6) · §4.1 Experimental setup, metrics, CloudLab/c6420 testbed (p.6)
· §4.2 Efficiency results + small-cache concession (p.6–7) · Fig. 3a–f miss-ratio-reduction
boxplots (p.7, image `pages/page-07.png`) · Fig. 4a/b Meta/Wiki/Tencent scatter (p.7) ·
Fig. 5a/b best-performing algorithm per dataset (p.7) · §4.3 Throughput + Fig. 6, cache size
`4 × nthread` GB (p.8, image `pages/page-08.png`) · §4.4 Simplicity, Table 2 LOC, Table 3
LOC + metadata, "ZERO parameter" (p.8) · §5.1 Sifting, Fig. 7a–c (p.9) · §5.2 Analysis,
Eq. 1 (p.9–10) · §5.3 Synthetic workloads, Figs. 8, 9, 10 (p.10–11) · §6.1 Cache primitives
+ Fig. 11 `perf stat` instructions/request (p.11–12) · §6.2 Turn-key eviction, Fig. 12a–c
incl. SIEVE-Belady 97%/94% (p.12) · §7.1 Byte miss ratio, Figs. 13, 14 vs. LRB (p.13) ·
§7.2 "SIEVE is not scan-resistant" (p.13) · §7.3 TTL-friendliness (p.13) · Availability
(p.13).

**Repository.**
`repo/README.md` (:14 snapshot note, :22 install, :29 smoke test, :38/:46 zipf quickstart,
:52-58 public trace links, :63-67 external prototypes) ·
`libCacheSim/CMakeLists.txt` (:20-28 options, :69-73 hugepage, :141-177 deps, :186-211
GLCache/LRB gating, :264-314 source globs, :374-381 tests) ·
`libCacheSim/scripts/install_dependency.sh` (:3-6 apt, :16-56 xgboost/lightgbm/zstd) ·
`libCacheSim/scripts/install_libcachesim.sh` ·
`libCacheSim/scripts/README.md` ·
`libCacheSim/scripts/plot_mrc_size.py` (:22-91 runner, :178-193 stale hardcoded path) ·
`libCacheSim/scripts/plot_mrc_time.py` ·
`libCacheSim/scripts/data_gen.py` (:41-58 `gen_zipf`, :100-113 oracleGeneral writer) ·
`libCacheSim/scripts/priv/plot/plot_mr_red_box.py` (:188-200, :265-266) ·
`libCacheSim/scripts/priv/plot/load_miss_ratio.py` (:15 broken import, :109-157) ·
`libCacheSim/scripts/priv/traceUtils/customized/msr_convert.py` ·
`libCacheSim/libCacheSim/cache/eviction/Sieve.c` (:10-15 params, :125-133 find, :146-153
insert, :165-207 to_evict, :218-232 evict) ·
`libCacheSim/libCacheSim/cache/eviction/belady/Sieve_Belady.c` ·
`libCacheSim/libCacheSim/cache/eviction/S3FIFO.c` (:117-130 ghost init, :240-250 ghost probe) ·
`libCacheSim/libCacheSim/cache/eviction/S3FIFOd.c` (:118-146 `main-cache=sieve`) ·
`libCacheSim/libCacheSim/cache/eviction/fifo/LP_ARC.c` (:110-120 ARC-over-Clock) ·
`libCacheSim/libCacheSim/cache/eviction/TwoQ.c` · `LRU.c` · `Clock.c` · `WTinyLFU.c` ·
`Cacheus.c` · `LIRS.c` · `Hyperbolic.c` · `LHD/lhd.cpp` · `LRB/lrb.cpp` ·
`libCacheSim/libCacheSim/cache/eviction/CMakeLists.txt` ·
`libCacheSim/libCacheSim/cache/admission/bloomfilter.c` ·
`libCacheSim/libCacheSim/bin/cachesim/cache_init.h` (:128-140 sieve registration, :150-165
INCLUDE_PRIV block) ·
`libCacheSim/libCacheSim/bin/cachesim/cli_parser.c` (:56-97 options, :304-307 sampler,
:426-451 fractional sizes, :453-483 auto sizes) ·
`libCacheSim/libCacheSim/bin/cachesim/main.c` (:35-37 multi-cache, :62-69 output format) ·
`libCacheSim/libCacheSim/include/libCacheSim/cacheObj.h:173` ·
`libCacheSim/libCacheSim/include/libCacheSim/evictionAlgo.h` (:157, :166) ·
`libCacheSim/libCacheSim/traceReader/customizedReader/oracle/oracleGeneralBin.h` (:9-28,
24 B records) ·
`libCacheSim/libCacheSim/traceReader/sampling/spatial.c:33` ·
`libCacheSim/libCacheSim/dataStructure/hashtable/chainedHashTableV2.c` (:102 hugepage madvise) ·
`libCacheSim/libCacheSim/cache/cache.c` (:187, :272 TTL paths) ·
`libCacheSim/example/cacheSimulatorConcurrent/main.cpp` (:20-22, :45-58) ·
`libCacheSim/data/` (bundled micro-traces) · `mydata/zipf/zipf_1.0` ·
`libCacheSim/dockerfile` · `libCacheSim/.travis.yml` ·
`repo_facts.json` · `fetch_result.json` · `meta.json`.

**Web (scoop check / provenance).**
[Marc Brooker — "Why Aren't We SIEVE-ing?" (SIEVE-k)](https://brooker.co.za/blog/2023/12/15/sieve.html) ·
[ISC — "SIEVE – A Better Algorithm Than LRU?" (2025)](https://www.isc.org/blogs/2025-sieve/) ·
[USENIX ;login: — "SIEVE: Cache eviction can be simple, effective, and scalable"](https://www.usenix.org/publications/loginonline/sieve-cache-eviction-can-be-simple-effective-and-scalable) ·
[Learning-Augmented Heuristics / S4-FIFO (arXiv 2608.27975)](https://arxiv.org/html/2608.27975v1) ·
[SCION (arXiv 2605.01055)](https://arxiv.org/html/2605.01055) ·
[CacheBench midterm report, UCSC OSPO 2025](https://ucsc-ospo.github.io/report/osre25/harvard/cachebench/2025-08-06-haochengxia/) ·
[opencoff/go-sieve (lock-free SIEVE)](https://github.com/opencoff/go-sieve) ·
[upstream libCacheSim eviction directory](https://github.com/1a1a11a/libCacheSim/tree/develop/libCacheSim/cache/eviction) ·
[USENIX NSDI'24 presentation page](https://www.usenix.org/conference/nsdi24/presentation/zhang-yazhuo) (HTTP 403 to automated fetch; no badge evidence obtained).
