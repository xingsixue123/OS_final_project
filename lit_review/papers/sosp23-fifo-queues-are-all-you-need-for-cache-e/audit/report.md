# FIFO Queues are All You Need for Cache Eviction (S3-FIFO)

SOSP '23 · Yang, Zhang, Qiu, Yue, Rashmi (CMU / Emory / Pelikan) · DOI 10.1145/3600006.3613147
Repo audited: `repo/` = snapshot of https://github.com/Thesys-lab/sosp23-s3fifo @ `6bc49d9` (2024-06-12).

---

## 1. Paper summary

**Problem.** A cache eviction algorithm has to be simultaneously *efficient* (low miss ratio),
*performant* (high single-thread QPS) and *scalable* (QPS grows with cores). Decades of work
built advanced policies on top of LRU queues (ARC, 2Q, LIRS, TinyLFU, LeCaR, CACHEUS, LHD),
but LRU costs two pointers per object and requires a lock-guarded promotion on every hit,
which the authors identify as the scalability bottleneck (§2.2, pp. 2–3, citing the RocksDB
LRU-cache contention report).

**Key observation (§3.1).** For Zipf-like workloads, the *one-hit-wonder ratio* of a
sub-sequence grows sharply as the sub-sequence shortens. Across the 6594-trace corpus, the
median one-hit-wonder ratio is 26% on the full trace but **72% on sub-sequences covering 10%
of the trace's objects and 78% at 1%** (Fig. 3, p. 4; per-dataset values in Table 1, p. 7).
Since a cache of size *C* only ever "sees" a window of ~*C* objects before it must evict,
most objects it holds are one-hit wonders at eviction time. Fig. 4 (p. 5) confirms this with
LRU and Belady simulations. Conclusion: **quick demotion** — evicting new objects fast — is
the dominant lever, not sophisticated ranking.

**Design (§4, Fig. 5 + Algo. 1, pp. 5–6).** S3-FIFO = three static FIFO queues:
- **S** (small/probationary), 10% of cache size;
- **M** (main), 90%, run as FIFO-reinsertion with a 2-bit capped frequency counter (a 2-bit CLOCK);
- **G** (ghost), holding metadata for as many entries as M.

Read: hit ⇒ `freq = min(freq+1, 3)` (an atomic byte write, no pointer surgery, and *no*
update at all after the third request). Write: new object → S, unless it is in G, in which
case it goes straight to M. Evicting from S: tail with `freq > 1` is promoted to M, otherwise
demoted to G. Evicting from M: tail with `freq > 0` is reinserted with `freq-1`, else evicted.
§4.2 notes the queues can be linked lists (easy to retrofit) or ring buffers (lower overhead,
more scalable, but wastes space under deletions) — **the ring-buffer version is described but
never built or measured**. §4.3 puts ghost overhead at ~0.09% and the 2 bits at <0.01% of
cache size.

**Evaluation setup (§5.1, pp. 7–8).** 6594 traces / 14 datasets (Table 1, p. 7), 856 B requests,
11 open + 3 proprietary datasets (CDN 1, CDN 2, Social Network 1). Simulator = libCacheSim;
prototype = CacheLib fork; throughput on CloudLab c6420 nodes with turbo off and `numactl`
pinning. Two cache sizes: 10% ("large") and 0.1% ("small") of trace footprint in objects.
Metric = miss-ratio *reduction relative to FIFO*. **Object sizes are ignored by default**
("we ignore object size in the simulator … we remark that supporting object size is non-trivial",
p. 7) and **per-algorithm metadata is not charged against capacity** ("we do not consider the
metadata size in different algorithms", p. 7). The full sweep cost ~10⁶ CPU-core-hours.

**Headline numbers.**
- Fig. 6a (p. 8): S3-FIFO has the largest miss-ratio reduction at nearly every percentile;
  mean reduction 14%, P90 > 32% at the large cache size.
- Fig. 7 (p. 10): S3-FIFO has the lowest mean miss ratio on **10 of 14 datasets** at the large
  size (7/14 at the small size) and is top-3 on 13/14; the runner-up (LIRS) wins on 2.
- Fig. 8 (p. 10): CacheLib prototype reaches **>6× the throughput of CacheLib's optimized LRU
  at 16 threads** (~40 Mops/s vs ~6 Mops/s at the large size).
- Fig. 9 (p. 11): used as a flash *admission* filter, a 0.1%-of-cache DRAM S beats both a
  probabilistic filter and Flashield's SVM on miss ratio *and* write bytes.
- §6.1 / Fig. 10 / Table 2 (pp. 11–12): the mechanism is explained as high **demotion precision
  at a predictable demotion speed**; ARC's adaptive sizing over/undershoots, TinyLFU shows
  non-monotonic miss-ratio cliffs.

**Stated limitations / open ends (the add-on surface).**
- §5.2 "Adversarial workloads for S3-FIFO": traces where most objects are accessed exactly
  twice and the second request falls just outside S — S3-FIFO loses to plain LRU/FIFO there.
- §6.2: S3-FIFO-d (the adaptive variant) is **worse than static S3-FIFO on most traces**;
  "tuning for a few traces is easy, but obtaining good results across traces is very
  challenging"; the paper explicitly suggests "downsized simulations using spatial sampling"
  as an unexplored route.
- §5.1: object size and metadata size are both excluded from the simulation.
- §4.2: the ring-buffer, lock-free implementation is asserted but never evaluated.

---

## 2. Artifact audit

### 2.1 Repository structure

```
README.md                 build/run instructions, trace download links, Apache-2.0 text
doc/AE.md                 artifact-evaluation recipe, figure by figure (433 lines)
libCacheSim/              vendored snapshot of libCacheSim (the simulator; ~70 kLOC C/C++)
scripts/                  Python plotting + the Flashield baseline
result/                   pre-computed per-trace simulation output (Figs. 6, 7, 10, 11)
distributedComputation/   Redis-based job farm used on CloudLab (100 nodes) — optional
requirements.txt          numpy, matplotlib
```

No top-level LICENSE file (`repo_facts.json.github.license = null`) but `README.md:116-130`
carries the Apache-2.0 notice and `libCacheSim/LICENSE` exists.

### 2.2 Paper component → code path

| Paper component | Code |
|---|---|
| S3-FIFO (Algo. 1, §4.1) | `libCacheSim/libCacheSim/cache/eviction/S3FIFO.c` — S/M/G are three nested `FIFO_init` caches; `S3FIFO_evict_fifo` (l. 310) implements `evictS`, `S3FIFO_evict_main` (l. 362) implements `evictM` with the 2-bit clock (`MIN(freq,3)-1`, l. 386) |
| S size / promotion threshold knobs | `S3FIFO.c:51` `DEFAULT_CACHE_PARAMS = "fifo-size-ratio=0.10,ghost-size-ratio=0.90,move-to-main-threshold=2"`, parsed at `S3FIFO.c:486` |
| S3-FIFO-d (adaptive, §6.2) | `libCacheSim/libCacheSim/cache/eviction/S3FIFOd.c` (two eviction-tracking ghost caches, l. 37-40) |
| Flash filter / QD-LP (§5.4, Fig. 9) | `libCacheSim/libCacheSim/cache/eviction/QDLP.c`, driver `libCacheSim/libCacheSim/bin/SOSP23/flash/flash.cpp` (write-byte accounting incl. reinsertion rewrites at l. 68-80) |
| Probabilistic flash admission baseline | `libCacheSim/libCacheSim/cache/eviction/other/flashProb.c` |
| Flashield (SVM) baseline | `scripts/flashield/flashield.py` (needs `scikit-learn`, `lru-dict`) |
| One-hit-wonder measurement (Figs. 2, 3) | `libCacheSim/libCacheSim/bin/SOSP23/oneHit/` → binary `traceOneHit`; plots `scripts/plot_one_hit_zipf.py`, `scripts/plot_one_hit_trace.py` |
| 12 baselines (LRU, ARC, 2Q, SLRU, LIRS, W-TinyLFU, LeCaR, CACHEUS, LHD, Clock, FIFO-Merge, B-LRU) | `libCacheSim/libCacheSim/cache/eviction/{LRU,ARC,TwoQ,SLRU,LIRS,WTinyLFU,LeCaR,Cacheus,FIFO_Merge,Clock}.c`, `eviction/LHD/`, bloom-filter admission in `cache/admission/bloomfilter.c`; dispatch table `bin/cachesim/cache_init.h:31-153` |
| Eviction-age / demotion instrumentation (Figs. 4, 10) | `#define TRACK_EVICTION_V_AGE` / `TRACK_DEMOTION` in `libCacheSim/libCacheSim/include/config.h`, consumed at `S3FIFO.c:136,282,325,344` |
| Miss-ratio plots (Figs. 6, 7) | `scripts/libCacheSim/plot_miss_ratio.py` + `load_miss_ratio_data.py`; data in `result/cachesim/` (14 dataset dirs + `all/`) |
| Queue-size sweep (Fig. 11) | `scripts/libCacheSim/plot_fifo_size.py`; data in `result/cachesim_fifo/` |
| Demotion speed/precision (Fig. 10) | `scripts/libCacheSim/plot_demotion.py`; data `result/demotion/demotion_{0.001,0.1}` |
| Throughput prototype (Fig. 8) | **not in this repo** — `README.md:45` and `doc/AE.md:227` tell you to `git clone https://github.com/Thesys-lab/cachelib-sosp23`; only the plotting script `scripts/plot_throughput.py` (with numbers hard-coded) is here |

`S3LRU.c` and `Sieve.c` are also present, i.e. the "LRU instead of FIFO" ablation of §6.3 and
the authors' later SIEVE algorithm are already available as comparison points.

### 2.3 Build route on this machine

`doc/AE.md:8` and `libCacheSim/scripts/install_dependency.sh` are Ubuntu `sudo apt` scripts,
but the actual dependency set is small and entirely conda-installable:

- `find_package(GLib REQUIRED)` → `cmake/Modules/FindGLib.cmake:30-36` goes through **pkg-config**,
  so `conda install -c conda-forge glib` + `PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig` suffices.
- `find_package(ZSTD)` (`CMakeLists.txt:152`, required because `SUPPORT_ZSTD_TRACE=ON`) →
  `conda install -c conda-forge zstd`.
- `find_package(Tcmalloc)` is **optional** (`CMakeLists.txt:167-175` only prints "cannot find tcmalloc").
- `xgboost` / `LightGBM` in `install_dependency.sh` are only needed for `ENABLE_GLCACHE` /
  `ENABLE_LRB`, both **OFF** by default (`CMakeLists.txt:20,23`). Skip them.
- gcc 12.2 + `-std=c11` / C++17: fine. No AVX-512, no GPU, no CUDA anywhere.

**Concrete gotcha:** `libCacheSim/CMakeLists.txt:1` is `cmake_minimum_required(VERSION 3.2)`.
The system CMake 3.25.1 accepts this (deprecation warning only); the `pip install cmake` 4.x
route mentioned in `env.md` would **hard-fail** on `<3.5` compatibility. Use the system cmake,
or patch line 1.

Build = `mkdir _build && cd _build && cmake .. && make -j` (`libCacheSim/scripts/install_libcachesim.sh`).
`make install` is *not* needed for the `cachesim`/`flash`/`traceOneHit` binaries.

### 2.4 Dependency pins and age

There are effectively no pins: `requirements.txt` is `numpy` + `matplotlib`; C deps are
distro/conda glib-2.0 and zstd. Head commit is 2024-06-12, ~2¼ years old at audit time, but
the code is plain C11 against stable libraries — no framework rot risk. `dockerfile`
(`libCacheSim/dockerfile`) exists but is not required; its RUN steps are the same apt list.

### 2.5 Data sources

`README.md:69` / `doc/AE.md:22` → `https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/`.
I fetched this index: it is an open directory with **12 dataset folders**
(alibabaBlock, cloudphysics, fiu, metaCDN, metaKV, metaStorage, msr, systor, tencentBlock,
tencentPhoto, twitter, wiki), several refreshed in 2025. The 3 proprietary datasets of Table 1
(CDN 1, CDN 2, Social Network 1) are **not** there, exactly as the paper states — but their
*pre-computed results* are shipped in `result/cachesim/CDN1/`, `CDN2/`, `SocialNetwork1/`.

Trace format is a 24-byte record (`ts, obj_id, obj_size, next_access_vtime`), zstd-compressed,
readable without decompression. `doc/AE.md:44` warns the full corpus is ~2 TB compressed —
more than the ~257 GB free on this machine, so a subset must be chosen (see §4).

### 2.6 Eval scripts: present / absent

| Figure/Table | Script present? | Pre-computed data present? |
|---|---|---|
| Fig. 2a/2b (Zipf one-hit) | ✅ `scripts/plot_one_hit_zipf.py` | n/a (generated) |
| Fig. 2c/2d (real traces) | ✅ `scripts/plot_one_hit_trace.py` | needs 2 downloads (~GB) |
| Fig. 3 (all traces) | ✅ same script `--plotbox` | ✅ downloadable `oneHit.zst` |
| Fig. 4 (freq at eviction) | ✅ `scripts/libCacheSim/plot_eviction_freq.py` (+ recompile with `TRACK_EVICTION_V_AGE`) | ❌ must run sims (cheap) |
| **Figs. 6, 7** | ✅ `scripts/libCacheSim/plot_miss_ratio.py` | ✅ `result/cachesim/` (14 dirs + `all/`) |
| Fig. 8 (throughput) | ⚠️ `scripts/plot_throughput.py` plots hard-coded numbers; the CacheLib prototype is an **external repo** | ❌ |
| Fig. 9 (flash) | ✅ `flash` binary + `scripts/plot_write_amp.py` (numbers pre-filled) | partially |
| Table 2 | ✅ exact command lines in `doc/AE.md:323-341` | ❌ (cheap to run) |
| Fig. 10 | ✅ `scripts/libCacheSim/plot_demotion.py` | ✅ `result/demotion/` |
| Fig. 11 | ✅ `scripts/libCacheSim/plot_fifo_size.py` | ✅ `result/cachesim_fifo/` |

Caveat: `plot_miss_ratio.py:73-75` raises `RuntimeError` if *any* of the 14 dataset dirs is
empty, so regenerating one dataset means dropping your own output into the shipped tree rather
than starting from scratch.

---

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper §"Availability" (p. 14) names `https://github.com/TheSys-lab/sosp23-s3fifo`, which is the repo cloned here. It contains the real implementation (`libCacheSim/libCacheSim/cache/eviction/S3FIFO.c`, 526 lines of C, plus 12 baselines), the AE recipe (`doc/AE.md`), and pre-computed results (`result/`) — not a placeholder. SOSP'23 AE results page lists it with **Artifacts Available + Functional + Results Reproduced** badges. |
| `H2_no_root` | **pass** | Nothing in the simulation path needs privilege. The `sudo` hits are (a) `doc/AE.md:8` / `libCacheSim/scripts/install_dependency.sh:4-5`, an apt convenience script replaceable by `conda install -c conda-forge glib zstd` because `cmake/Modules/FindGLib.cmake:30` uses pkg-config; (b) `libCacheSim/CMakeLists.txt:17` and `libCacheSim/doc/performance.md:13`, *commented* THP tuning — the code only calls unprivileged `madvise(..., MADV_HUGEPAGE)` (`libCacheSim/libCacheSim/traceReader/reader.c:132`) whose return value is ignored, and `-DUSE_HUGEPAGE=OFF` is available (`CMakeLists.txt:18`). `libCacheSim/dockerfile` is optional. No kernel module, eBPF, perf counter, or KVM use anywhere. Caveat: `doc/AE.md:231` `bash turboboost.sh disable` for the **CacheLib throughput figure only** does need root — that figure is out of scope for the simulation-side reproduction. |
| `H3_hardware_fit` | **pass** | CPU-only, single-node, single-process-per-simulation. `cachesim` uses `--num-thread` merely to run independent (algo, size) simulations in parallel (`bin/cachesim/cli_parser.c:99-104`), so 16 cores/32 threads is a good match, and the paper's own scalability claim was measured at 16 threads (Fig. 8). The 10⁶ core-hour full sweep is *not* reproducible here, but the paper ships the per-trace results and the per-dataset claim is reproducible dataset-by-dataset. 125 GB RAM is ample: the largest simulations cache ≤10% of a trace's objects at ~64 B of metadata each. The `distributedComputation/` CloudLab job farm is optional tooling, not part of the algorithm. |
| `H4_obtainable_deps_data` | **pass** | Deps = glib-2.0, zstd (+ optional tcmalloc), numpy, matplotlib, and (for the Flashield baseline only) scikit-learn + lru-dict — all conda/pip-installable in user space. Data: I verified the PDL FTP index is live and open, with 12 of the 14 datasets (MSR, FIU, CloudPhysics, Systor, Tencent Block, Tencent Photo, Alibaba, Twitter, Wikimedia, Meta KV, Meta CDN, Meta Storage). The 3 proprietary datasets are unavailable but the repo ships their computed results (`result/cachesim/CDN1|CDN2|SocialNetwork1/`) and the headline claim survives on the open subset. Disk is the real constraint: 2 TB of traces vs ~257 GB free ⇒ pick a subset (§4). |

No `fail`, no `unclear`.

---

## 4. Reproduction plan

**Target.** **Figure 7a (p. 10), the MSR / FIU / Systor rows** — "S3-FIFO has the lowest mean
miss-ratio reduction from FIFO on most datasets", at the large cache size (10% of trace
footprint). Secondary, essentially free target: **Table 2 (p. 11), the two MSR blocks** — the
exact miss ratios of S3-FIFO and W-TinyLFU at S ∈ {0.01 … 0.40}, for which `doc/AE.md:323-341`
gives literal command lines.

**Why this target.** It is the claim the paper leads with, the shipped `result/cachesim/{MSR,FIU,SYSTOR}/`
files give a per-trace ground truth to diff against (format: one line per algo × size, e.g.
`result/cachesim/MSR/hm_0.IQI.bin.txt:1`), and the three datasets are the three *smallest* open
block collections in Table 1 (MSR 13 traces / 410 M req, FIU 9 / 514 M, Systor 6 / 3.7 B — Systor
can be trimmed if disk is tight).

**Scale-down.** Download only `msr/`, `fiu/` and `systor/` from the PDL FTP (order of tens of GB
compressed, well inside 257 GB; traces are consumed zstd-compressed so no decompression needed
except for `traceOneHit`). Run

```
./libCacheSim/_build/bin/cachesim <trace> oracleGeneral \
    FIFO,LRU,Clock,ARC,LIRS,TinyLFU,2Q,SLRU,S3FIFO 0 --ignore-obj-size 1 --num-thread 8
```

per trace (size `0` sweeps the 8 fractions of trace footprint the result files use). Cap
parallelism at ~8 concurrent (algo, size) simulations to stay inside RAM. If Systor is too
large, use `--sample-ratio 0.1` (spatial sampling, `libCacheSim/libCacheSim/traceReader/sampling/spatial.c`)
and note the sampling in the write-up — miss ratios shift slightly but the *ordering* across
algorithms, which is what Fig. 7 claims, is preserved.

**Steps.**
1. `conda create -n s3fifo -c conda-forge glib zstd python=3.11 numpy matplotlib`;
   export `PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig`.
2. `cd libCacheSim && mkdir _build && cd _build && cmake .. -DUSE_HUGEPAGE=OFF && make -j16`
   (use **system** cmake 3.25, not pip cmake 4.x — see §2.3). Smoke-test on the bundled
   `libCacheSim/data/trace.oracleGeneral.bin`.
3. `wget -r` the msr / fiu / systor folders.
4. Run the sweep above; collect into `myresult/cachesim/{MSR,FIU,SYSTOR}/`.
5. Diff against `result/cachesim/{MSR,FIU,SYSTOR}/` line by line (miss ratios should match to
   the printed 4 decimals — the simulator is deterministic for these algorithms).
6. Copy the shipped dirs for the other 11 datasets, drop in your three, run
   `python3 scripts/libCacheSim/plot_miss_ratio.py --datapath=myresult/cachesim/` and compare
   the MSR/FIU/Systor rows of `miss_ratio_per_dataset_2.pdf` with Fig. 7a.
7. Run the Table 2 MSR commands verbatim (single trace, ~15 runs) as an exact-number check.

**Effort.** ~2–3 person-days (most of it download + babysitting), ~20–60 CPU-core-hours.
Peak disk ~60 GB, peak RAM well under 32 GB at 8-way parallelism.

**Level: H.** Build instructions and evaluation scripts exist *for this specific figure*;
dependencies are trivial and current; the workload fits the machine at paper scale for these
datasets; the artifact carries a **Results Reproduced** badge from SOSP'23 AE; and the shipped
per-trace results give an unambiguous pass/fail criterion. The only thing *not* reproducible
is Fig. 8 (needs the external `cachelib-sosp23` repo, a multi-hour CacheLib build, and root for
turbo-boost control) and the full 6594-trace sweep.

---

## 5. Add-on ideas

### A1 — Size-aware S3-FIFO (`S3FIFO-sz`)

> **Hypothesis.** We hypothesize that making S3-FIFO's promotion decision size-aware —
> promoting S-tail objects to M on a *benefit-per-byte* criterion rather than a raw
> `freq >= 2` threshold, and sizing S in bytes rather than objects — reduces **byte miss
> ratio** by ≥5% on CDN/object workloads with heavy-tailed size distributions (Wikimedia,
> Tencent Photo, Meta CDN), at no more than a 1% request-miss-ratio regression.

- **mechanism.** Replace the scalar test at `S3FIFO.c:324` (`obj_to_evict->S3FIFO.freq >= params->move_to_main_threshold`)
  with a per-object score `freq / size^α` compared against a running quantile of the scores of
  recently promoted objects (a 256-bucket log-size histogram updated on each promotion, O(1) per
  eviction, no per-object pointers). Keep the ghost admission path unchanged so scan resistance is
  preserved. Add `alpha` and `size-aware` to `S3FIFO_parse_params` (`S3FIFO.c:486`) and register
  the variant in `bin/cachesim/cache_init.h`. Evaluate with the existing byte-miss-ratio output
  path (already printed by `cachesim`) and with `--ignore-obj-size 0`.
- **code_locations.** `libCacheSim/libCacheSim/cache/eviction/S3FIFO.c` (l. 310–360 `S3FIFO_evict_fifo`,
  l. 486 param parser), `libCacheSim/libCacheSim/bin/cachesim/cache_init.h`,
  `libCacheSim/libCacheSim/cache/eviction/CMakeLists.txt`.
- **motivating_evidence.** §5.1 (p. 7): "we ignore object size in the simulator because most
  production systems use slab storage … However, we remark that supporting object size is
  non-trivial for systems that do not use slab-based memory management." §5.2 (p. 10): the byte
  miss ratio results are relegated to one paragraph and "not shown due to space limit". CDN
  deployments are precisely the ones that care about byte miss ratio (§2.1), and S3-FIFO's
  `S3FIFO_can_insert` (l. 468) currently just rejects any object bigger than S.
- **feasibility: H.** ~300 LOC in one file plus a registration line; the harness, traces
  (wiki, tencentPhoto, metaCDN are all on the open FTP) and metric already exist; each trace is
  a few CPU-hours.
- **research_value: M.** It closes a simplifying assumption the paper itself flags, and a
  negative result ("size-awareness does not help S3-FIFO") would also be publishable as a
  robustness statement. But size-aware caching is a well-trodden area (GDSF, AdaptSize, LHD),
  so a reviewer would call the direction expected rather than surprising.
- **scoop_check: partial.** Queries: *"size-aware S3-FIFO byte miss ratio CDN variable object
  size eviction improvement libCacheSim"*, *"S3-FIFO size-aware variable object size cache
  eviction follow-up 2025"*. Closest work: **3L-Cache** (FAST '25,
  https://www.usenix.org/system/files/fast25-zhou-wenbin.pdf) — a learned, size-aware CDN
  eviction policy that uses S3-FIFO as a baseline; and **SCION** (arXiv 2605.01055), which
  *selects among* size-aware experts (GDSF, LHD) and S3-FIFO per workload and reports beating
  S3-FIFO on large-object traces. Neither makes S3-FIFO itself size-aware — they route around
  it — so the specific mechanism is unclaimed, but the headline finding ("S3-FIFO is weak on
  large-object CDN traces") is already known.

---

### A2 — Sampled-shadow-simulation adaptive S sizing (`S3FIFO-mini`)

> **Hypothesis.** We hypothesize that choosing S3-FIFO's small-queue ratio online from a set of
> spatially-sampled miniature shadow simulations (1/100-scale S3-FIFO instances at S ∈ {1, 2, 5,
> 10, 20, 40}%) matches static S=10% on the bulk of traces *and* recovers most of the loss on the
> tail of traces where 10% is far from optimal — outperforming the paper's own S3-FIFO-d on both
> mean and P10 miss-ratio reduction.

- **mechanism.** libCacheSim already has spatial sampling (`traceReader/sampling/spatial.c`,
  exposed as `--sample-ratio`). Instantiate *k* shadow S3-FIFO caches inside a new
  `S3FIFO-mini` cache object, each sized to `sample_ratio × cache_size` and fed only the requests
  whose object-ID hash falls in the sample (a cheap hash test in `find`). Every *W* requests,
  pick the shadow with the lowest windowed miss ratio and move the real S boundary toward its
  ratio by a bounded step. The main cache's data path is untouched, so the scalability argument
  survives. Compare against `S3FIFO.c` (static) and `S3FIFOd.c` (marginal-hit adaptation) on the
  same trace set used for Fig. 11.
- **code_locations.** `libCacheSim/libCacheSim/cache/eviction/S3FIFOd.c` (the adaptation loop to
  replace), `libCacheSim/libCacheSim/cache/eviction/S3FIFO.c`,
  `libCacheSim/libCacheSim/traceReader/sampling/spatial.c`,
  `libCacheSim/libCacheSim/include/libCacheSim/sampling.h`,
  `scripts/libCacheSim/plot_fifo_size.py`, `result/cachesim_fifo/`.
- **motivating_evidence.** §6.2 (pp. 12–13) is a page-long admission of failure: "S3-FIFO is
  better than S3-FIFO-d on most traces except the 2% traces at the tail"; "tuning for a few
  traces is easy, but obtaining good results across traces is very challenging"; "we believe
  adaptations are still important, but **how to adapt remains to be explored**"; and the paper
  itself points at the remedy — "for systems that need to find the best parameter, downsized
  simulations using spatial sampling can be used [135, 136]" — without ever trying it. Fig. 11
  (p. 13) quantifies the headroom: at the large cache size the P90 reduction is best at S=1%
  while the P10 is best at a larger S, so no single static value is right everywhere.
- **feasibility: H.** One new ~500-LOC eviction module reusing an existing sampler; evaluated with
  the unmodified `cachesim` harness against shipped `result/cachesim_fifo/` ground truth. A
  4-dataset sweep is tens of CPU-hours on 16 cores. The main risk is that shadow caches at 1/100
  scale are too noisy — but that is exactly the hypothesis under test, and a negative result is
  informative.
- **research_value: H.** This is the paper's own named open problem, it was left open by the
  authors after they tried and failed with a different mechanism, and either outcome teaches
  something: if miniature simulation works, the "static is better than adaptive" thesis of §6.2
  is overturned; if it fails, the paper's claim that simplicity beats adaptation gets a much
  stronger empirical backing than one hand-tuned variant.
- **scoop_check: partial.** Queries: *"miniature simulation shadow cache online parameter tuning
  S3-FIFO small queue size adaptive 2026"*, *"adaptive queue size S3-FIFO miss ratio curve
  spatial sampling 2025 2026"*. The *technique* is Waldspurger et al., "Cache Modeling and
  Optimization using Miniature Simulations", USENIX ATC '17
  (https://www.usenix.org/conference/atc17/technical-sessions/presentation/waldspurger) — which
  already auto-tunes the LIRS stack limit and **2Q queue sizes**, i.e. the closest cousins of S.
  Reference [135] in the paper is that work. No follow-up applying it to S3-FIFO was found;
  `DynamicAdaptiveClimb` (arXiv 2511.21235) does adaptive resizing but for a Climb-family policy.
  So: mechanism known, application to S3-FIFO unclaimed. The project must frame the contribution
  as the empirical question, not the technique.

---

### A3 — Charging metadata against capacity: a fair re-evaluation

> **Hypothesis.** We hypothesize that when per-algorithm metadata is charged against the cache's
> byte budget — LRU/ARC/2Q/LIRS paying 16 B of pointers per object, S3-FIFO paying 2 bits plus its
> ghost-queue entries — S3-FIFO's mean miss-ratio reduction over LRU on small-object KV workloads
> (Twitter, Meta KV, mean object size ≈ 200–300 B from Table 1) grows by a further ≥3 percentage
> points, while on 4 KB block workloads (MSR, Systor) the change is <0.5 points and S3-FIFO's
> ghost queue costs it ground at very small cache sizes.

- **mechanism.** libCacheSim already has the plumbing: `common_cache_params_t.consider_obj_metadata`
  (`include/libCacheSim/cache.h:33`), a per-cache `obj_md_size` charged on every insert/evict
  (`cache/cache.c:208,231,281`), the CLI flag `--consider-obj-metadata`
  (`bin/cachesim/cli_parser.c:146`), and correct values already set for some baselines
  (`LRU.c:66` = 16 B, `ARCv0.c:111`, `LIRS.c:88`, `LeCaRv0.c:97`). But **S3-FIFO hard-codes
  `cache->obj_md_size = 0` at `S3FIFO.c:101`, ignoring `consider_obj_metadata` entirely**, and the
  ghost queue's storage is never charged. The work: (i) set S3-FIFO's `obj_md_size` honestly
  (2 bits, rounded to the implementation's byte, plus the amortised fingerprint+timestamp ghost
  cost the paper describes in §4.2), (ii) audit and fill in the missing `obj_md_size` for TwoQ,
  SLRU, WTinyLFU, Clock, FIFO_Merge, (iii) re-run Fig. 6/Fig. 7 on the open datasets with and
  without `--consider-obj-metadata` and report the delta.
- **code_locations.** `libCacheSim/libCacheSim/cache/eviction/S3FIFO.c:101`,
  `libCacheSim/libCacheSim/cache/eviction/LRU.c`, `libCacheSim/libCacheSim/cache/eviction/TwoQ.c`,
  `libCacheSim/libCacheSim/cache/eviction/WTinyLFU.c`, `libCacheSim/libCacheSim/cache/cache.c`,
  `libCacheSim/libCacheSim/bin/cachesim/cli_parser.c`,
  `scripts/libCacheSim/plot_miss_ratio.py`.
- **motivating_evidence.** §5.1 (p. 7): "we do not consider the metadata size in different
  algorithms, **although S3-FIFO often requires fewer metadata than other algorithms**" — the
  paper concedes the comparison is biased and asserts (without measuring) that the bias is against
  itself. §4.3 (p. 7) gives the arithmetic (ghost ≈ 0.09%, 2 bits < 0.01%, saving 16 B/object vs
  LRU ≈ 0.4%) but only for a 4 KB mean object size; Table 1 shows Twitter/Social-Network KV traces
  with mean objects an order of magnitude smaller, where 16 B/object is a several-percent capacity
  tax. §2.2 makes "LRU needs two pointers per object" a headline motivation, so quantifying it is
  squarely on-thesis.
- **feasibility: H.** Almost all of the work is filling in constants in ~8 files plus a careful
  accounting of the ghost queue; the harness, flag and plotting are untouched. Evaluation is the
  same MSR/FIU/Systor/Twitter sweep as the reproduction, run twice.
- **research_value: M.** A SOSP reviewer would care — it turns a hand-waved footnote into a
  measured result and could either strengthen or partly deflate the headline margin. But it is a
  methodological correction rather than a new mechanism, and the expected direction is already
  stated by the authors, which caps the surprise.
- **scoop_check: clear.** Query: *"cache eviction simulator metadata overhead fair comparison
  S3-FIFO LRU pointers charged cache capacity study"*. Nothing found that re-evaluates the
  S3-FIFO corpus under a metadata-charged budget. Related but different: Eytan et al.,
  "It's Time to Revisit LRU vs. FIFO", HotStorage '20
  (https://www.usenix.org/system/files/hotstorage20_paper_eytan.pdf), which argues about
  LRU-vs-FIFO methodology but predates S3-FIFO and does not charge metadata.

---

### A4 — Write-amplification-aware main queue for DRAM+flash S3-FIFO

> **Hypothesis.** We hypothesize that replacing M's *physical* reinsertion (which re-writes an
> object when its frequency bit is set) with an in-place frequency update plus a segment-aligned
> eviction scan reduces flash write bytes by ≥25% at equal or lower miss ratio, on the Wikimedia
> and Tencent Photo CDN traces at the DRAM ratios of Fig. 9 (0.1%, 1%, 10%).

- **mechanism.** `flash.cpp:68-80` already shows that when S3-FIFO/QDLP's main cache is a Clock,
  the write-byte count is `n_byte_admit_to_main + n_byte_move_to_main + clock_params->n_byte_rewritten`,
  i.e. reinsertion is a first-class source of flash writes and is measured. The paper's Fig. 9 only
  varies the *admission* filter and pins the flash eviction to plain FIFO, so the write cost of
  S3-FIFO's own main-queue reinsertion is never exposed. The change: add a main-cache variant that
  (a) keeps the 2-bit counter in a DRAM-resident index instead of beside the data, (b) at eviction
  scans a fixed-size window (a "segment") of the flash FIFO tail and drops the coldest objects
  rather than rewriting the hot ones, (c) only rewrites when a whole segment is evicted (FIFO-merge
  style). Sweep segment size and compare (miss ratio, write bytes) Pareto fronts against the paper's
  three points.
- **code_locations.** `libCacheSim/libCacheSim/bin/SOSP23/flash/flash.cpp`,
  `libCacheSim/libCacheSim/cache/eviction/QDLP.c`,
  `libCacheSim/libCacheSim/cache/eviction/Clock.c`,
  `libCacheSim/libCacheSim/cache/eviction/FIFO_Merge.c`,
  `libCacheSim/libCacheSim/cache/eviction/other/flashProb.c`,
  `scripts/plot_write_amp.py`.
- **motivating_evidence.** §5.4 (p. 11): "Because the flash cache eviction algorithm is orthogonal
  to the admission policy, we used FIFO in all experiments (including in S3-FIFO)" — an explicitly
  unexplored axis. §2.1 (p. 2) argues flash lifetime is a first-class metric and that small random
  writes cause device-level write amplification; §4.1's `evictM` reinsertion (Algo. 1 l. 36) is
  exactly such a write. Fig. 9 shows the admission filter alone moves normalised write bytes from
  ~3× to well under 1×, so the remaining write budget is dominated by exactly the mechanism the
  paper left as FIFO.
- **feasibility: M.** The harness (`flash` binary), the write-byte accounting and both traces
  (`wiki_2019t`, `tencent_photo1`, both on the open FTP, downloads listed at `doc/AE.md:283-284`)
  exist, which is a big head start. But it is a cross-cutting change (a new main-cache type that
  must cooperate with QDLP's accounting) and, if the team wants the Flashield comparison line,
  `scripts/flashield/flashield.py` is documented as taking "more than one day to run" per
  configuration (`doc/AE.md:309`) — budget for that or reuse the pre-filled numbers in
  `scripts/plot_write_amp.py`.
- **research_value: H.** It attacks the one place where the paper's simplification ("eviction is
  orthogonal to admission") is most likely to be false, in a regime — flash endurance — that the
  paper itself argues is economically important and that production systems (Cachelib LOC,
  Google Colossus, Memcached extstore, all cited in §2.1) actually care about. A negative result
  ("reinsertion writes are negligible after quick demotion") is a genuinely useful confirmation
  of the orthogonality claim.
- **scoop_check: clear.** Queries: *"S3-FIFO flash cache admission write amplification follow-up
  reinsertion flash-friendly 2025 2026"*. Closest work: **CacheSack** (ACM TOS 2023,
  https://dl.acm.org/doi/10.1145/3582014), Google's flash *admission* optimiser — same metric
  pair, but an admission-policy optimiser, not an eviction/reinsertion redesign, and it predates
  S3-FIFO's flash section. Nothing found that measures or removes S3-FIFO's reinsertion write cost.

---

### Not proposed (and why)

A **lock-free / ring-buffer S3-FIFO throughput** add-on looks attractive — §4.2 describes the
ring-buffer design but never builds it, and Fig. 8 was measured on a linked-list CacheLib port.
I am **not** proposing it because it is **scooped**: "Using Lock-Free Design for
Throughput-Optimized Cache Eviction" (Mobius), SIGMETRICS / POMACS 2025,
https://dl.acm.org/doi/10.1145/3727136, builds exactly this — two lock-free FIFO queues with a
consecutive-detection merge to cut data races — and reports the concurrency results. It would also
have required the external `cachelib-sosp23` repo plus root for turbo-boost control
(`doc/AE.md:231`). Similarly, improving M's reinsertion policy *for miss ratio* is largely covered
by "Demystifying and Improving Lazy Promotion in Cache Eviction" (PVLDB vol. 19,
https://www.vldb.org/pvldb/vol19/p549-yang.pdf), which benchmarks FIFO-reinsertion variants and
proposes Delayed FIFO-reinsertion and Age-Guided Eviction.

---

## 6. Risks and open questions

1. **Disk vs corpus.** The full 6594-trace corpus is ~2 TB compressed against ~257 GB free. Every
   result in this project must be scoped to a named, downloadable subset, and the write-up must be
   explicit that it re-tests the claim on 3–5 of 14 datasets rather than all 14. Any add-on claiming
   "across traces" robustness inherits this weakness.
2. **Proprietary datasets.** CDN 1, CDN 2 and Social Network 1 (1711 of the 6594 traces, and 2 of
   the 14 rows of Fig. 7) cannot be downloaded. Add-on claims can only be validated on the open 12.
3. **Fig. 8 is effectively out of reach.** The throughput prototype lives in a separate repo
   (`Thesys-lab/cachelib-sosp23`), CacheLib takes "a few minutes up to one hour" to build with a
   large C++ dependency tree, `doc/AE.md:219` asks for an Intel CPU (we have Zen 3), and
   `turboboost.sh disable` needs root. Do not promise any scalability result.
4. **CMake version trap.** `libCacheSim/CMakeLists.txt:1` requires `VERSION 3.2`; CMake 4.x (the
   `pip install cmake` route) rejects `<3.5`. Use system cmake 3.25.1 or bump line 1.
5. **Bugs in the reference implementation.** `S3FIFO.c:290` is `obj->S3FIFO.freq == 0;` — a
   no-op comparison where an assignment was clearly intended (freq happens to be zeroed by the
   underlying FIFO insert, so behaviour may be accidentally correct, but any fork must verify this
   before attributing a miss-ratio delta to its own change). Also `cache_init.h:98` makes
   `fifo-reinsertion` unreachable as a distinct algorithm (it is caught by the `clock` branch at
   l. 89). Establish a byte-for-byte baseline match against `result/cachesim/` before changing anything.
6. **Memory at high parallelism.** `doc/AE.md:46` warns that running many algorithms × sizes in
   parallel multiplies DRAM use; `--num-thread` defaults to `n_cores()` (`cli_parser.c:206`), i.e.
   32 here. Cap it explicitly or large traces will thrash into the 44 GiB swap.
7. **Add-on A2 depends on sampling fidelity.** If 1/100-scale shadow caches are too noisy at the
   0.1%-footprint ("small") cache size — where the cache holds only thousands of objects — the
   shadow instances may hold tens of objects and be useless. Mitigation: restrict the adaptive
   claim to the large cache size, or use a coarser sample ratio and accept more overhead.
8. **Crowded field.** Since 2023 the S3-FIFO line has attracted SIEVE (NSDI '24, already vendored as
   `eviction/Sieve.c`), Mobius (SIGMETRICS '25), 3L-Cache (FAST '25), the PVLDB '26 lazy-promotion
   study and SCION. A literature check should be redone at proposal time; the "obvious" improvement
   directions are being taken quickly.
9. **`repo_facts.json` red flags are benign.** The `multi_node` hits are all CloudLab/`distComp`
   references in `distributedComputation/` and acknowledgements; the `docker` hits are comments
   inside `libCacheSim/dockerfile`; the `sudo` hits are apt scripts and commented THP tuning. None
   are load-bearing. Verified by reading each file.

---

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; page images in `pages/`)
- Abstract & intro, p. 1 — 6594 traces / 14 datasets, 6× throughput at 16 threads, 26% → 72% one-hit-wonder.
- §2.1 metrics incl. flash writes, p. 2; §2.2 LRU's three problems, pp. 2–3.
- §3.1 one-hit-wonder observation + Fig. 2 (p. 4), Fig. 3 (p. 4, all-trace distribution), Fig. 4 (p. 5, freq at eviction).
- §3.2 need for quick demotion, p. 5; Fig. 5 S3-FIFO illustration, p. 5.
- §4.1 design + Algorithm 1, pp. 5–6; §4.2 implementation (ring buffer vs linked list, fingerprint ghost), p. 6; §4.3 overhead analysis, pp. 6–7.
- Table 1 dataset table, p. 7.
- §5.1 evaluation setup — simulator, "ignore object size", "do not consider metadata size", 10% / 0.1% cache sizes, CloudLab c6420, pp. 7–8.
- §5.2 + **Fig. 6** (p. 8, `pages/page-08.png`) — per-percentile miss-ratio reduction; per-baseline discussion pp. 8–9; "Adversarial workloads for S3-FIFO" p. 9.
- **Fig. 7** (p. 10, `pages/page-10.png`) — per-dataset mean reduction, 10/14 datasets.
- §5.3 + **Fig. 8** (p. 10) — throughput scaling, 6× at 16 threads.
- §5.4 + Fig. 9 (p. 11) — flash admission, "flash cache eviction algorithm is orthogonal to the admission policy … we used FIFO".
- §6.1 + Fig. 10 + Table 2 (pp. 11–12) — demotion speed/precision, S-size sensitivity.
- §6.2 (pp. 12–13) + Fig. 11 (p. 13) — S3-FIFO-d, "how to adapt remains to be explored", spatial-sampling suggestion.
- §6.3 (p. 13) — LRU vs FIFO ablation. §7 related work, pp. 13–14. Availability, p. 14.

**Repository** (paths relative to `repo/`)
- `README.md` (build/run, trace URL, Apache-2.0, CacheLib external repo at l. 45)
- `doc/AE.md` (figure-by-figure recipe; deps l. 8, data l. 22, size warning l. 44, Fig. 6/7 l. 170-208, Fig. 8 l. 211-255, Fig. 9 l. 278-320, Table 2 l. 323-341, Fig. 10 l. 345-400, Fig. 11 l. 402-422)
- `libCacheSim/CMakeLists.txt` (l. 1 cmake 3.2, l. 17-18 hugepage, l. 20/23 GLCache/LRB off, l. 140 GLib, l. 150-160 ZSTD, l. 167-175 optional tcmalloc)
- `libCacheSim/cmake/Modules/FindGLib.cmake:30-36` (pkg-config route)
- `libCacheSim/scripts/install_dependency.sh`, `libCacheSim/scripts/install_libcachesim.sh`
- `libCacheSim/libCacheSim/cache/eviction/S3FIFO.c` (l. 51 defaults, l. 101 `obj_md_size = 0`, l. 212 find, l. 262 insert, l. 290 `freq == 0` no-op, l. 310 evictS, l. 362 evictM, l. 468 can_insert, l. 486 param parser)
- `libCacheSim/libCacheSim/cache/eviction/S3FIFOd.c` (l. 27-43 adaptive params, l. 45 defaults)
- `libCacheSim/libCacheSim/cache/eviction/CMakeLists.txt` (compiled algorithm list)
- `libCacheSim/libCacheSim/cache/eviction/{LRU.c:66, ARCv0.c:111, LIRS.c:88, LeCaRv0.c:97}` (metadata sizes)
- `libCacheSim/libCacheSim/cache/cache.c` (l. 208/231/281 metadata charged to occupancy)
- `libCacheSim/libCacheSim/include/libCacheSim/cache.h` (l. 33 `consider_obj_metadata`, l. 136 `obj_md_size`)
- `libCacheSim/libCacheSim/bin/cachesim/cache_init.h` (l. 31-153 algorithm dispatch; l. 110 s3fifo)
- `libCacheSim/libCacheSim/bin/cachesim/cli_parser.c` (l. 72 `--ignore-obj-size`, l. 99-104/206 threads, l. 146 `--consider-obj-metadata`, l. 286-289 spatial sampler)
- `libCacheSim/libCacheSim/traceReader/reader.c:128-134` (unprivileged `madvise` hugepage hint)
- `libCacheSim/libCacheSim/traceReader/sampling/spatial.c`, `include/libCacheSim/sampling.h`, `traceReader/CMakeLists.txt:9`
- `libCacheSim/libCacheSim/bin/SOSP23/CMakeLists.txt` (builds `traceOneHit`, `flash`)
- `libCacheSim/libCacheSim/bin/SOSP23/flash/flash.cpp:14-80` (write-byte accounting incl. `n_byte_rewritten`)
- `libCacheSim/libCacheSim/cache/eviction/QDLP.c`, `eviction/other/flashProb.c`, `eviction/Clock.c`, `eviction/FIFO_Merge.c`, `eviction/Sieve.c`, `eviction/other/S3LRU.c`
- `scripts/libCacheSim/plot_miss_ratio.py` (l. 19-27 Fig. 7 algo list, l. 73-75 requires all 14 dirs, l. 314-326 main)
- `scripts/libCacheSim/{plot_fifo_size.py, plot_demotion.py, plot_eviction_freq.py, load_miss_ratio_data.py}`, `scripts/{plot_one_hit_zipf.py, plot_one_hit_trace.py, plot_throughput.py, plot_write_amp.py}`, `scripts/flashield/flashield.py`
- `result/cachesim/MSR/hm_0.IQI.bin.txt` (ground-truth format), `result/cachesim/{FIU,SYSTOR,all}/`, `result/cachesim_fifo/`, `result/demotion/demotion_{0.001,0.1}`
- `requirements.txt` (numpy, matplotlib)
- `libCacheSim/data/trace.oracleGeneral.bin` (bundled smoke-test trace)

**External**
- SOSP '23 artifact-evaluation results — https://sysartifacts.github.io/sosp2023/results — lists this paper with Artifacts Available, Artifacts Evaluated–Functional, and **Results Reproduced** (v1.1).
- Trace host index — https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/ — 12 open dataset folders, live as of 2026-09-14.
- Scoop-check hits: Mobius / lock-free eviction, SIGMETRICS '25 — https://dl.acm.org/doi/10.1145/3727136 ; Lazy promotion study, PVLDB 19(4) — https://www.vldb.org/pvldb/vol19/p549-yang.pdf ; 3L-Cache, FAST '25 — https://www.usenix.org/system/files/fast25-zhou-wenbin.pdf ; SCION — https://arxiv.org/abs/2605.01055 ; Waldspurger et al., miniature simulations, ATC '17 — https://www.usenix.org/conference/atc17/technical-sessions/presentation/waldspurger ; CacheSack, ACM TOS 2023 — https://dl.acm.org/doi/10.1145/3582014 ; Eytan et al., HotStorage '20 — https://www.usenix.org/system/files/hotstorage20_paper_eytan.pdf
