# 3L-Cache: Low Overhead and Precise Learning-based Eviction Policy for Caches

FAST '25 · Zhou, Niu, Xiong, Fang, Wang (BJUT + Microsoft Research)
Repo audited: `repo/` = https://github.com/optiq-lab/3L-Cache @ `134cd15` (2025-08-09)

## 1. Paper summary

**Problem.** Object-level learned eviction policies (LRB, HALP) reach the best byte/object
miss ratios but cost 10–172× the CPU of LRU (Table 1, p.4; Figure 1 shows peak overhead of
LRB reaching ~300× LRU). That cost is what blocks production deployment (§2.2). The paper
decomposes the overhead: training + prediction are ~70–91% of an object-level policy's CPU
(Figure 2, p.4), with prediction dominating at small cache sizes and training at large ones.

**Key idea.** 3L-Cache keeps object-level GBM learning but attacks both components (§3.1
challenges C-1/C-2/C-3):

1. *Training-data collection* (§4.2.1): a coarse-grained sliding window sized as
   `hsw × |cache queue|`, plus object-oriented sampling/labelling rules that drop repeat
   samples of already-sampled objects, so the model can be retrained every `M = 64K` labelled
   entries instead of on a fixed high frequency (Figure 3 motivates: dropping LRB's training
   frequency from 2³ to 2⁻³ per million cuts CPU 48% with negligible miss-ratio change).
2. *Bidirectional sampling* (§4.3.1, Figure 5): sample eviction candidates both from the LRU
   tail (all objects in the first `x%`, then only objects with freq ≤ `f`) and from the head
   via a "recorded queue" of newly admitted objects capped at `Q%` of cache bytes. Goal: raise
   the fraction of genuinely unpopular objects among candidates.
3. *Efficient eviction* (§4.3.2): fixed **eviction ratio = 1/2** (evict half of each candidate
   batch) and a max-heap + hash-table structure holding *accumulated* predictions, so the
   object with the furthest predicted next request can be found without re-predicting.
4. *Parameter auto-tuning* (§4.4, Table 2): online rules for `hsw, f, x, Q, n`.

**Model.** LightGBM GBDT, 16 iterations / 32 leaves / 1 thread, 6 features (age, size,
frequency, 3 most recent inter-arrival times), label = log(next-arrival interval);
out-of-window objects get a large synthetic label (§4.2.2).

**Evaluation setup** (§5.1): trace-driven simulation on top of libCacheSim, 4855 traces from
8 public datasets (Table 3, p.9: CloudPhysics, TencentPhoto, Wikipedia CDN, Tencent CBS,
Twitter, Alibaba, Meta KV, Meta CDN; 266.95 B requests). Two cache sizes per trace: 0.1% and
10% of the trace footprint. 12 policies compared. Metrics: miss-ratio *reduction from LRU*
and CPU overhead *relative to LRU*. Hardware: dual Xeon Gold 5128R, 192 GB. A small Flask
prototype (§5.6) validates the simulator (byte hit ratio within 2%).

**Headline numbers.**
- CPU: 3L-Cache cuts mean CPU overhead 60.9% vs HALP and 94.9% vs LRB; mean overhead is
  6.4× LRU (small cache) and 3.4× LRU (large) — §5.3 and Figure 10 (p.12).
- Composition: training+prediction is only 37.3% of 3L-Cache's CPU at large cache size vs
  64.5% (HALP) / 90.9% (LRB) — Table 4 and Table 5 (p.12).
- Miss ratio: lowest BMR on 69.8% of traces (small) / 41.2% (large); lowest OMR on 66.3% /
  29.3% (§5.2.1, §5.2.2). On Tencent CBS it cuts LRU's BMR by 11.6% (small) vs LRB's 8.6%
  (Figure 6b) and 7.9% vs 6.7% (Figure 6f).
- Auto-tuning beats random/default parameters on 81.6% / 53.6% of traces (Figure 11).
- Applying the sampling+eviction design to LRB cuts LRB's CPU by 80% and BMR by 0.6%
  (§5.5, Figure 12).

**Stated limitations** (§7 and §5.2.2): (a) on workloads with weak Zipf skew the bidirectional
sampler "may not effectively represent low popularity" and degenerates to random sampling —
explicitly named as future work; (b) at large cache sizes GDSF beats 3L-Cache on object miss
ratio because sampling-based eviction only sees a small candidate pool; (c) on the small Meta
CDN / Tencent Photo datasets several heuristics win.

## 2. Artifact audit

### Repo structure and provenance

The paper's footnote 1 (§1, p.3) states "The source code is available at
https://github.com/optiq-lab/3L-Cache", which is exactly the audited repo → **official**.
The repo is a fork of libCacheSim with the new policy dropped in as a top-level directory.
3L-Cache has since been merged into upstream libCacheSim (issue
[1a1a11a/libCacheSim#119](https://github.com/1a1a11a/libCacheSim/issues/119), closed as
completed by PR #126), which is an independent corroboration of officialness and a possible
alternative base.

| paper component | code path |
|---|---|
| whole policy, `lookup/admit/evict` (§4.1, Figure 4) | `3LCache/TLCache.cpp`, `3LCache/TLCache.h` |
| online training, `M = 64K` batch, hsw update (§4.2.1, Eq.1/Eq.2) | `3LCache/TLCache.cpp:12-60` (`train()`), `batch_size = 131072/2` at `3LCache/TLCache.h:27`, hsw rule at `TLCache.cpp:52-58` |
| sliding-window sizing `hsw × |queue|`, window eviction/labelling | `3LCache/TLCache.cpp:130-156` (`erase_out_cache()`), sampling at `TLCache.cpp:63-68`, 25% label-keep probability at `TLCache.cpp:93` |
| GBM features (age, size, freq, 3 inter-arrival times) (§4.2.2) | `3LCache/TLCache.h:174-229` (`TrainingData::emplace_back`), `TLCache.cpp:397-430` |
| bidirectional sampling — tail (`x%`, freq ≤ `f`) (§4.3.1) | `3LCache/TLCache.cpp:192-272` (`rank()`), esp. `:207-219` |
| bidirectional sampling — head / recorded queue `Q%` (§4.3.1) | `3LCache/TLCache.cpp:275-298` (`quick_demotion()`), `new_obj_keys` at `TLCache.h:246` |
| eviction ratio 1/2 (§4.3.2) | `3LCache/TLCache.h:253` (`eviction_rate = 2`), used at `3LCache/TLCache.cpp:353-355` |
| heap + hash accumulated predictions (§4.3.2) | `3LCache/TLCache.cpp:343-380` (`evict_predobj()`), `:449-469` (heap push), `pred_map`/`pred_times` at `TLCache.h:240-242` |
| auto-tuning of `f, x, Q, n` (§4.4, Table 2) | `3LCache/TLCache.cpp:220-263` |
| BMR vs OMR objective (§5.2.2 weight `reuse × size`) | `3LCache/TLCache.cpp:449-469`; CLI names `3lcache` / `3lcache-omr` at `libCacheSim/bin/cachesim/cache_init.h:141-149` |
| libCacheSim glue | `3LCache/TLCache_Interface.cpp` |
| baselines LRB / GL-Cache / LHD / GDSF / S3-FIFO / SIEVE / TinyLFU / LeCaR / CACHEUS / ARC | `libCacheSim/cache/eviction/LRB/`, `GLCache/`, `LHD/`, `cpp/GDSF.cpp`, `S3FIFO.c`, `Sieve.c`, `WTinyLFU.c`, `LeCaR.c`, `Cacheus.c`, `ARC.c` |
| **HALP baseline** | **absent** — the only occurrences of "HALP" in the repo are plot labels in `3LCache/scripts/draw_figure.py:19,76` |
| **"modified-LRB" of §5.5 / Figure 12** | **absent** — `libCacheSim/cache/eviction/LRB/lrb.cpp:273-410` is vanilla LRB random sampling (`sample_rate` candidates, evict 1) |
| eval driver (Fig. 6/8 miss ratios) | `3LCache/scripts/miss_ratio_boxplot.py`, `3LCache/scripts/executor_libcachesim.py`, `3LCache/scripts/libcachesim_result_collect.py`, `3LCache/scripts/draw_figure.py`, `3LCache/scripts/run_scripts.sh` |
| eval driver (Fig. 10 CPU overhead) | `3LCache/scripts/cpu_overhead_boxplot.py` |
| cache sizes = 0.1%/10% of footprint | `3LCache/scripts/trace_info/{dataset,tencentblock,alibaba,twitter,cloudphysics}_info.txt` (unique-byte per trace), used at `cpu_overhead_boxplot.py:81` and `libcachesim_result_collect.py:128-136` |
| prototype (§5.6, Flask) | **absent** — only the simulator is released |
| undocumented extra: `3LCache+` (`TLCacheN`) | `3LCache+/TLCacheN.cpp`, registered as algo `3LCache+` at `libCacheSim/bin/cachesim/cache_init.h:141`; not described in the paper |

### CPU-overhead metric — how it is actually measured

`libCacheSim/bin/cachesim/sim.c:75-97` computes throughput as
`req_cnt / wall-clock runtime` (`gettime()`), printed as `MQPS`. The scripts then define
"CPU overhead relative to LRU" as `throughput(LRU) / throughput(algo)`
(`3LCache/scripts/cpu_overhead_boxplot.py:112-119`, `draw_figure.py:197-202`). **No perf
counters, no `/proc` sampling, no root.** The paper's definition (`CPUload × time`, §2.1)
therefore maps onto pure wall-clock timing in the artifact.

### Build route on this machine

`scripts/install_libcachesim.sh` is just `mkdir _build && cmake .. && make -j` — fine.
`scripts/install_dependency.sh` is the problem: it calls `sudo apt install`, `sudo make
install` for xgboost/zstd and `sudo make install` for the vendored LightGBM. Every one of its
steps has a user-space equivalent, so this is a porting job, not a blocker:

- `libglib2.0-dev` → conda-forge `glib`; `zstd` → conda-forge `zstd`; `google-perftools`
  (tcmalloc) → optional, `CMakeLists.txt:171-180` prints "cannot find tcmalloc" and continues.
- `argp` is in glibc 2.36 (`cmake/Modules/Findargp.cmake`).
- xgboost is needed only for GL-Cache; either conda-forge `libxgboost`/`xgboost` or
  `-DENABLE_GLCACHE=OFF` (`CMakeLists.txt:187-195`).
- LightGBM is **vendored** at `scripts/LightGBM/` — `scripts/LightGBM/VERSION.txt` says
  **2.2.2** (2018). Build it with `-DCMAKE_INSTALL_PREFIX=$HOME/local`; CMake finds it via
  `find_path(LIGHTGBM_PATH LightGBM)` / `find_library(LIGHTGBM_LIB _lightgbm)`
  (`CMakeLists.txt:197-229`), so `CMAKE_PREFIX_PATH=$HOME/local` suffices. Risk: a 2018 C++
  codebase under gcc 12 / glibc 2.36 may need small patches.
- `USE_HUGEPAGE` defaults ON but is only `madvise(..., MADV_HUGEPAGE)`
  (`libCacheSim/dataStructure/hashtable/chainedHashTableV2.c:101-103`); it degrades silently
  without root and can be turned off with `-DUSE_HUGEPAGE=OFF`.
- cmake ≥ 3.12 required (`CMakeLists.txt:1`); system cmake 3.25.1 is fine.

**Likely build break at HEAD.** `libCacheSim/cache/eviction/CMakeLists.txt:93-94` adds the
3LCache sources as `../../../3LCache/TLCache.cpp` (correct: three levels up from
`libCacheSim/cache/eviction` is the repo root), but lines 97-100 add the 3LCache+ sources as
`../../../../3LCache+/TLCacheN.cpp` — **four** levels up, i.e. the parent of the repo. Unless
the repo is checked out inside a directory that happens to contain a sibling `3LCache+/`,
CMake should fail at configure time with "Cannot find source file". The fix is one `../`, or
check out the pre-`3LCache+` state. Flagged rather than asserted, since I cannot run cmake.

### Data

README "Traces" table lists public sources for all 8 datasets (SNIA/IOTTA for Tencent Photo
and Tencent CBS, `github.com/alibaba/block-traces`, `github.com/twitter/cache-traces`,
cachelib.org for Meta KV/CDN, CMU PDL ftp + `lrb.cs.princeton.edu` for Wikipedia). The
repo ships **~50 ready-to-run sample traces** in `data/` (Twitter `clusterN.csv`, CloudPhysics
`wNN.csv`, Alibaba `io.traces.nsNNN.csv`, Tencent `tencentBlock.nsNNNN.csv`) in the
3-column `time id size` format (verified by reading `data/w01.csv`), plus a sample result file
`3LCache/scripts/result/io.traces.ns117.csv` and a sample output figure
`3LCache/scripts/figures/bmr.pdf`. Raw upstream traces need conversion to that format
(README Step 2); helpers exist at `libCacheSim/bin/traceUtils/traceConvMain.cpp` and
`libCacheSim/bin/dep/cpp/{tencent,alibaba}.h`. Python deps are trivial
(`requirements.txt` = numpy, matplotlib; scripts also need pandas, openpyxl, psutil).

### Harness caveat worth knowing before running

`3LCache/scripts/executor_libcachesim.py:61-76` and `cpu_overhead_boxplot.py:175-180` launch
**32 concurrent simulations** through a `ThreadPoolExecutor` while the CPU-overhead metric is
wall-clock throughput. Throughput measured under 32-way self-contention is not the quantity
Figure 10 reports; for the overhead figure the runs must be serialised (and ideally pinned)
on this shared 16-core machine.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper §1 footnote 1 (p.3) points at `github.com/optiq-lab/3L-Cache`; the repo contains the full policy (`3LCache/TLCache.cpp`, 472 lines; `3LCache/TLCache.h`), the libCacheSim integration (`3LCache/TLCache_Interface.cpp`, `libCacheSim/bin/cachesim/cache_init.h:141-149`), baselines, eval scripts (`3LCache/scripts/*.py`) and sample traces (`data/`). Not a placeholder or plot-only drop. Upstream adoption: libCacheSim issue #119 closed by PR #126. |
| `H2_no_root` | **pass** | Pure user-space C/C++ simulator; overhead is wall-clock throughput in `libCacheSim/bin/cachesim/sim.c:75-96` — no perf/PMU, no eBPF, no KVM, no kernel code. `sudo` appears only in `scripts/install_dependency.sh:4-9,29,44,55` and `.travis.yml`, all replaceable by conda/pip + `CMAKE_INSTALL_PREFIX=$HOME` (see §2). `USE_HUGEPAGE` is `madvise(MADV_HUGEPAGE)` only (`libCacheSim/dataStructure/hashtable/chainedHashTableV2.c:101`) and is an off-switchable CMake option (`CMakeLists.txt:24`). `dockerfile` exists but is inherited from libCacheSim and is not the documented path (README "Build and Install" uses the two shell scripts). |
| `H3_hardware_fit` | **pass** | CPU-only, single-process, single-node. Paper's machine is 2×20-core/192 GB; ours is 16-core/125 GB — same class. Working set is bounded by the metadata of one trace (the sliding window holds `hsw ≤ 6 ×` the cache queue, `3LCache/TLCache.cpp:56,131`); the shipped traces run at ~0.6 MQPS for 3L-Cache (README example: 13.6 M requests, 1 GiB cache). The only real constraint is disk: the full 4855-trace corpus is many TB vs ~257 GB free, so a subset is mandatory — a scale-down that still tests the claim (per-trace box plots). |
| `H4_obtainable_deps_data` | **pass** | All deps installable in user space (glib/zstd/xgboost via conda-forge; LightGBM 2.2.2 vendored at `scripts/LightGBM/`; gperftools optional). All 8 datasets are public and linked in README (SNIA IOTTA, alibaba/block-traces, twitter/cache-traces, cachelib.org Meta traces, CMU PDL wiki); no proprietary trace is required, and ~50 sample traces ship in `data/` so a first result needs no download at all. Minor risk: the `lrb.cs.princeton.edu` wiki links may be stale, but Wikipedia is one of 8 datasets and has a CMU PDL mirror. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** Figure 10(a)/(b) (p.12) plus the §5.3 sentence it supports: *"the mean CPU
overhead of 3L-Cache is 6.4× LRU for small cache sizes and 3.4× for large"*, together with the
box-plot shape showing 3L-Cache sitting with the heuristics rather than with LRB. Secondary
target, produced by the same runs: Figure 6(b)/(f) — byte-miss-ratio reduction from LRU on
Tencent CBS (paper: 11.6% mean small, 7.9% mean large, vs LRB 8.6% / 6.7%).

**Scale-down.** Instead of 4855 traces:
- start with the ~50 traces already in `data/` (Twitter / CloudPhysics / Alibaba / Tencent),
- then add 30–60 Tencent CBS + CloudPhysics traces downloaded from SNIA/CloudPhysics and
  converted to the 3-column format, keeping total trace bytes under ~50 GB of the 257 GB free;
- cache sizes stay at the paper's 0.1% and 10% of each trace's unique bytes, read from
  `3LCache/scripts/trace_info/*_info.txt`;
- policy set = the 9–11 that ship (LRU, LHD, GDSF, ARC, SIEVE, S3-FIFO, TinyLFU, LeCaR,
  CACHEUS, 3L-Cache, and LRB/GL-Cache if their optional deps are built). **HALP cannot be
  reproduced at all** (no implementation anywhere in the repo), so the "60.9% vs HALP" number
  is out of reach; the "94.9% vs LRB" number is in reach.

**Steps.**
1. conda env: `glib`, `zstd`, `xgboost`(optional), pandas/openpyxl/psutil/matplotlib.
2. Build vendored LightGBM 2.2.2 into `$HOME/local`; expect small gcc-12 patches.
3. Fix `libCacheSim/cache/eviction/CMakeLists.txt:97-100` (`../../../../3LCache+` →
   `../../../3LCache+`) or drop the 3LCache+ target; configure with
   `-DCMAKE_PREFIX_PATH=$HOME/local -DUSE_HUGEPAGE=OFF -DENABLE_LRB=ON`.
4. Smoke test the README example on `data/tencentBlock_ns3964.zip` and compare against the
   miss ratios printed in README lines 75-80 (0.3380 OMR / 0.1034 BMR) — a free correctness
   oracle.
5. Miss-ratio sweep: `miss_ratio_boxplot.py` (multi-size mode prints byte miss ratio via
   `libCacheSim/bin/cachesim/main.c:60`).
6. CPU sweep: rewrite the 32-way `ThreadPoolExecutor` in `cpu_overhead_boxplot.py:175` to a
   serial loop with `taskset`, 3 repeats, median; otherwise the throughput numbers are
   contention artefacts.
7. `libcachesim_result_collect.py` + `draw_figure.py` to regenerate the box plots.

**Effort.** ≈7 person-days (2 build/deps, 2 trace download+convert, 1 harness serialisation,
2 runs + analysis) + ≈100 CPU-hours, 0 GPU-hours, ~50 GB disk.

**Level: M.** Not H because: the dependency script assumes root and must be re-derived for
conda; the vendored ML library is 8 years old; the HEAD `CMakeLists` path for `3LCache+`
looks broken; the headline figure aggregates 4855 traces that must be downloaded and
format-converted; one of the two compared baselines (HALP) is simply not in the artifact; and
the CPU-overhead harness measures throughput under self-inflicted 32-way contention. Not L
because the policy, nine baselines, the plotting pipeline, the per-trace cache-size metadata,
~50 ready-to-run traces and a known-good expected output all ship in the repo.

## 5. Add-on ideas

### A1. Skew-aware sampling guard (the paper's own future work)

- **Hypothesis.** We hypothesize that an online sampling-precision detector that falls back to
  a wider candidate pool (or to plain LRU/FIFO eviction) when bidirectional sampling stops
  beating random sampling improves worst-case byte miss ratio relative to LRU under low-skew /
  scan-heavy workloads (small Zipf exponent, high one-hit-wonder fraction), at ≤20% extra CPU,
  compared with stock 3L-Cache.
- **Mechanism.** 3L-Cache already measures, per sampling round, how many sampled objects were
  actually evicted, in `evcition_distribution[0..3]` and the `p1 > p2` test used to move `x`
  (`3LCache/TLCache.cpp:236-258`). Turn that into an explicit *precision* statistic and compare
  it against the precision a uniform sampler would achieve (estimable from the queue's evicted
  fraction). When precision ≈ random for `k` consecutive rounds, (i) raise the candidate budget
  `sample_rate`/lower the eviction ratio, or (ii) bypass prediction entirely and evict from the
  tail, and re-arm the detector periodically. Add a synthetic workload generator (Zipf α swept
  0.6→1.2, plus scan + uniform mixes) and select real low-skew traces with the existing
  popularity analyser.
- **Code locations.** `3LCache/TLCache.cpp` (`rank()` at :192-272, auto-tune block :236-258),
  `3LCache/TLCache.h` (:244-269 counters), `libCacheSim/traceAnalyzer/popularity.cpp` (Zipf/
  popularity estimation for trace selection), `3LCache/scripts/miss_ratio_boxplot.py` (eval).
- **Motivating evidence.** §7: *"If an atypical web caching workload exhibits fewer Zipf access
  patterns, the objects sampled by 3L-Cache may not effectively represent low popularity …
  causing the sampling effectiveness to degrade to that of random sampling. In future work, we
  plan to … design an efficient eviction policy that can adapt to diverse workloads."* The
  paper simultaneously claims in §5.2.1 that 3L-Cache is *less* affected by a falling power-law
  exponent than S3-FIFO — an untested claim in direct tension with §7. Independent evidence
  that the worst case is real: the LAH/S4-FIFO preprint reports 3L-Cache *increasing* FIFO's
  miss ratio by 8.8% in the worst case vs 0.8% for S4-FIFO.
- **Feasibility M.** The policy change is localized, but a credible evaluation needs a new
  low-skew workload generator and a trace-selection pass over the corpus, plus a definition of
  "random-sampling precision" that is cheap to compute online. Fits the machine (CPU-only).
- **Research value H.** It is the limitation the authors themselves flagged, it targets the
  regime where the whole design premise (Zipf ⇒ tail = unpopular) fails, and both outcomes are
  publishable: either the guard removes the worst-case regression, or it shows the regression
  is intrinsic to object-level sampling.
- **Scoop check — `partial`.** Queries: "3L-Cache non-Zipf low skew robustness", "learned cache
  eviction worst-case robustness FIFO anchor 2026", "3L-Cache follow-up citing".
  Closest work: [Learning-Augmented Heuristics / S4-FIFO,
  arXiv 2608.27975](https://arxiv.org/html/2608.27975v1) — documents 3L-Cache's worst-case
  regression and optimises robustness, but by learning cache-level parameters of S3-FIFO, not
  by fixing 3L-Cache's sampler; and [SL-Cache, DASFAA
  2026](https://link.springer.com/chapter/10.1007/978-981-92-0363-5_36) — adds hotness-aware
  adaptive sampling to an object-level learner, aimed at throughput and hot-object retention
  rather than low-skew robustness. Neither adds a degradation detector/fallback inside
  3L-Cache.

### A2. Adaptive eviction-ratio controller

- **Hypothesis.** We hypothesize that replacing 3L-Cache's fixed eviction ratio of 1/2 with a
  controller that adapts the per-batch eviction count to the observed prediction quality
  reduces byte miss ratio at equal CPU overhead (or cuts CPU at equal miss ratio) on traces
  where the tail and head samplers do *not* contribute candidates in the assumed 1:1 ratio.
- **Mechanism.** `evict_nums = rank() / eviction_rate` with `eviction_rate = 2` hard-coded
  (`3LCache/TLCache.cpp:353-355`, `3LCache/TLCache.h:253`). Track, per batch, how many evicted
  objects were re-requested shortly after eviction (the out-of-cache window at
  `TLCache.h:281` already retains their metadata, so "evicted and came back within W" is free
  to measure), and use a hill-climb / additive-increase-multiplicative-decrease loop on
  `eviction_rate ∈ [1, 8]` — exactly the style of controller the paper already uses for
  `x`, `Q`, `f` (Table 2). Also make the head/tail candidate split adaptive instead of the
  assumed 1:1.
- **Code locations.** `3LCache/TLCache.cpp:343-380` (`evict_predobj`), `3LCache/TLCache.cpp:192-272`
  (`rank`), `3LCache/TLCache.h:249-266` (`evict_nums`, `eviction_rate`, `reserved_space`),
  `3LCache/scripts/cpu_overhead_boxplot.py` (overhead/miss-ratio trade-off plot).
- **Motivating evidence.** §4.3.2 justifies 1/2 with a population-level average ("the number of
  eviction candidates sampled by these two methods is approximately 1:1 **overall**") and then
  asserts without a figure that raising the ratio causes "a sharp increase in the miss ratio".
  Every other parameter in the design is auto-tuned (Table 2); the eviction ratio is the one
  that is not, and it is the knob that directly sets prediction overhead (48.5% of CPU at small
  cache sizes, Table 4).
- **Feasibility H.** ≈100–300 LOC inside one class, no new harness: the existing
  miss-ratio and CPU scripts already produce the two axes of the trade-off.
- **Research value M.** A natural, expected extension — completing the auto-tuning story the
  paper started. Interesting but not surprising if it works; mildly interesting if the fixed
  1/2 turns out to be near-optimal across traces (which would validate the paper).
- **Scoop check — `partial`.** Queries: "adaptive eviction ratio learned cache 2026",
  "3L-Cache eviction count adaptive". No work found that tunes 3L-Cache's eviction ratio;
  the nearest is [SL-Cache](https://link.springer.com/chapter/10.1007/978-981-92-0363-5_36),
  which adapts *sampling/demotion* (not the eviction count) in a new object-level learner.

### A3. Avoid recomputation: warm-start training + prediction reuse across model updates

- **Hypothesis.** We hypothesize that (i) updating the GBM incrementally (appending trees to
  the existing booster) instead of retraining from scratch, and (ii) retaining still-valid
  cached predictions across model updates and sampling-round boundaries instead of flushing
  them, together reduce 3L-Cache's CPU overhead relative to LRU by ≥25% at equal byte miss
  ratio, with the largest gains at small cache sizes where prediction dominates.
- **Mechanism.** `train()` frees the old booster and builds a new one every 64K labels
  (`3LCache/TLCache.cpp:14,34-41`); the vendored LightGBM already exports
  `LGBM_BoosterMerge` and `LGBM_BoosterCreateFromModelfile`
  (`scripts/LightGBM/include/LightGBM/c_api.h:352,387`), so a warm-start path is available.
  Separately, the entire prediction cache is dropped on every model update
  (`3LCache/TLCache.cpp:44-46`) and at every end-of-round (`:230-232`); replace the
  all-or-nothing invalidation with a staleness bound (keep predictions whose object features
  have not changed and whose producing model is ≤k updates old, re-scoring lazily on heap pop).
  Measure the training/prediction split the way Table 4 does (the class already has
  `training_time` / `inference_time` fields at `3LCache/TLCache.h:288-289`).
- **Code locations.** `3LCache/TLCache.cpp:12-60` (`train`), `3LCache/TLCache.cpp:220-232`
  (round-end flush), `3LCache/TLCache.cpp:343-380` + `:449-469` (heap/hash validity protocol),
  `3LCache/TLCache.h:240-242,288-289`, `scripts/LightGBM/include/LightGBM/c_api.h`.
- **Motivating evidence.** Table 4: prediction is 48.5% and training 12.5% of 3L-Cache's CPU at
  small cache sizes (18.3% / 19.0% at large) — i.e. 61% of the remaining overhead is in exactly
  the two paths that currently throw away work. §4.3.2 already argues that "the prediction
  results are accurate prior to model updates", which is precisely the assumption a staleness
  bound generalises; the paper never tests how much accuracy survives *past* an update.
- **Feasibility H.** Localized to one class plus a C-API call; evaluable with the shipped
  harness. Risk: LightGBM 2.2.2's merge semantics may force a newer LightGBM (upstream
  libCacheSim's 3L-Cache port is a fallback base).
- **Research value M.** Bounded headroom (≤61% of 3L-Cache's own overhead, and the policy is
  already only 3.4–6.4× LRU), and "reuse stale predictions" is an expected engineering move —
  but it sharpens the paper's central overhead/accuracy trade-off and the negative result
  (predictions rot immediately after a model update) would also be informative.
- **Scoop check — `partial`.** Queries: "LightGBM incremental training cache eviction 2026",
  "learned cache reuse predictions across model updates". Incremental GBM training is standard
  practice and [SL-Cache](https://link.springer.com/chapter/10.1007/978-981-92-0363-5_36)
  attacks the same overhead from a different angle ("not all objects necessitate precise
  prediction" — skipping, not reusing). No work found that reuses 3L-Cache's accumulated
  predictions across model updates.

### A4. Charge the metadata: fair-accounting evaluation + compact metadata

- **Hypothesis.** We hypothesize that when per-object learning metadata is charged against the
  cache budget, 3L-Cache's byte-miss-ratio advantage over LRU/S3-FIFO/SIEVE shrinks
  substantially at small cache sizes (0.1% of footprint), and that a compact-metadata variant
  (quantised inter-arrival times, no heap-allocated `MetaExtra`, byte-bounded history window)
  recovers most of the lost advantage at unchanged CPU overhead.
- **Mechanism.** libCacheSim supports charging metadata: `--consider-obj-metadata`
  (`libCacheSim/bin/cachesim/cli_parser.c:94,165`) makes each policy add its declared
  `obj_md_size` to every cached object. 3L-Cache declares **180 bytes**
  (`3LCache/TLCache_Interface.cpp:85-89`, copied from LRB's
  `libCacheSim/cache/eviction/LRB/LRB_Interface.cpp:89`) while LRU declares 16
  (`libCacheSim/cache/eviction/LRU.c:67`) and the paper claims 67 bytes/object (§4.2.2).
  Step 1: re-run the Figure 6 comparison with the flag on, for all policies, and also account
  for the out-of-cache history (`hsw ≤ 6 ×` the cache queue, `3LCache/TLCache.cpp:56,131`),
  which nothing charges today. Step 2: shrink `Meta`/`MetaExtra` (`3LCache/TLCache.h:35-98`) —
  16-bit log-quantised distances, inline array instead of `vector<uint32_t>` + `new`, drop
  `_sample_times` for non-sampled objects — and set `obj_md_size` to the measured value.
- **Code locations.** `3LCache/TLCache_Interface.cpp` (`:85-89` metadata declaration),
  `3LCache/TLCache.h` (`:35-98` `Meta`/`MetaExtra`), `3LCache/TLCache.cpp:130-156`
  (history window sizing), `libCacheSim/bin/cachesim/cli_parser.c` (flag),
  `3LCache/scripts/miss_ratio_boxplot.py` (harness).
- **Motivating evidence.** §4.2.2 states the metadata cost is "approximately 2.5% of the cache
  space for small cache sizes", i.e. non-negligible exactly where the paper's wins are largest
  (69.8% best-BMR share at small sizes, §5.2.1) — yet none of the released scripts pass
  `--consider-obj-metadata`, so every reported miss ratio treats learning metadata as free,
  for 3L-Cache *and* for LRB. And the code's own declaration (180 B) is 2.7× the paper's
  claimed 67 B, so even the paper's own 2.5% estimate may be optimistic.
- **Feasibility H.** Step 1 is a flag plus a re-run; step 2 is a contained struct rewrite. Both
  use the existing harness and fit the machine.
- **Research value M.** It is primarily a fairness/measurement result plus a modest engineering
  fix, so a reviewer might call it incremental — but "does the win survive honest accounting?"
  is a question a FAST reviewer genuinely cares about, and the 67-vs-180-byte discrepancy makes
  it concrete. Either outcome is informative.
- **Scoop check — `clear`.** Queries: "3L-Cache metadata overhead cache budget consider object
  metadata", "learned cache eviction metadata charged miss ratio fair comparison". Found no
  follow-up that re-evaluates 3L-Cache (or LRB) with metadata charged; the two known follow-ups
  (S4-FIFO, SL-Cache) do not address metadata accounting.

## 6. Risks and open questions

1. **Probable configure failure at HEAD.** `libCacheSim/cache/eviction/CMakeLists.txt:97-100`
   references `../../../../3LCache+/TLCacheN.cpp`, one directory level above the repo root,
   whereas the analogous 3LCache entry at `:93-94` uses three levels. Desk-review conclusion,
   not verified by running cmake. One-line fix, or use the pre-3LCache+ commit / upstream
   libCacheSim.
2. **Eight-year-old vendored LightGBM.** `scripts/LightGBM/VERSION.txt` = 2.2.2 (2018) built
   with gcc 12 / glibc 2.36. Likely fine, possibly needs small patches; swapping in a modern
   LightGBM changes the model and hence the numbers.
3. **No root ⇒ dependency script must be rewritten.** `scripts/install_dependency.sh` is
   sudo-only end to end; everything has a conda/`$HOME` equivalent but it is real work, and the
   README's claimed platform (Ubuntu 18.04, cmake 3.28.6) differs from Debian 12 / cmake 3.25.
4. **HALP is absent.** The 60.9%-vs-HALP headline cannot be checked; nor can §5.5/Figure 12
   (the "modified-LRB"), since `libCacheSim/cache/eviction/LRB/lrb.cpp` is stock LRB. Any
   project that wants those comparisons must reimplement them.
5. **CPU-overhead measurement is fragile.** Wall-clock throughput
   (`libCacheSim/bin/cachesim/sim.c:75-96`) measured while the shipped drivers run 32
   simulations at once (`executor_libcachesim.py:61`, `cpu_overhead_boxplot.py:175`), on a
   machine that is shared with other users. Numbers will not match the paper unless runs are
   serialised, pinned and repeated; expect variance to be the dominant error term.
6. **Trace subsetting threatens the claim.** The paper's statements are percentile/box-plot
   statements over 4855 traces; with 50–100 traces the 10th/90th percentiles are noisy, and the
   4030 Tencent CBS traces dominate the corpus, so a "representative" subset is itself a
   methodological choice the team must defend.
7. **Two undocumented artifacts.** `3LCache+` / `TLCacheN` (added 2025-08-09, registered as
   algorithm `3LCache+`) is not mentioned in the paper; results obtained with it are not the
   paper's results. Also, `data/` traces named `*.sample.csv` are sampled, not full.
8. **Metadata accounting.** `3LCache/TLCache_Interface.cpp:86` charges 180 B/object vs the
   paper's claimed 67 B (§4.2.2), and no released script enables `--consider-obj-metadata`
   (see A4).
9. **Some trace links may be stale.** README points at `lrb.cs.princeton.edu` for the Wikipedia
   traces; unverified. Not fatal (7 other datasets, ~50 bundled traces).
10. **Open question.** §5.2.1 claims 3L-Cache is *less* sensitive than S3-FIFO to a falling
    power-law exponent, while §7 says its sampler degenerates to random on weakly-Zipf
    workloads. No figure settles this; A1 is built on that gap.

## 7. Evidence index

**Paper** (`paper.txt` page markers in parentheses):
- Abstract + §1 (p.2–3): headline claims, footnote 1 repo link, contributions.
- Table 1 (p.4): per-policy BMR/OMR/CPU vs LRU; §2.2 + Figure 1 (p.4): real-time CPU overhead.
- Figure 2 (p.4): training/prediction/other overhead split for LRB and HALP.
- §3 + Figure 3 (p.4–5): training-frequency vs miss-ratio/CPU; eviction-ratio definition.
- §3.1 (p.5): challenges C-1, C-2.1, C-2.2, C-3.
- §4.1 + Figure 4 (p.5–6): architecture; §4.2.1–4.2.2 (p.6): window sizing, labelling, M=64K,
  6 features, 67 B/object metadata claim.
- §4.3.1 + Figure 5 (p.7): bidirectional sampling; §4.3.2 (p.7–8): eviction ratio 1/2, heap+hash.
- §4.4 + Table 2 (p.8): auto-tuning rules and Eq.1/Eq.2.
- §5.1 + Table 3 (p.9): datasets, 4855 traces, cache sizes, simulator/prototype, hardware.
- §5.2.1 + Figures 6–7 (p.9–10), §5.2.2 + Figures 8–9 (p.10–11), §5.2.3 (p.11).
- §5.3 + Figure 10 + Tables 4–5 (p.12, page image read): CPU overhead headline, overhead split.
- §5.4 + Figure 11 (p.12), §5.5 + Figure 12 (p.13), §5.6 + Figure 13 (p.13).
- §6.2 (p.13) related-work taxonomy; §7 (p.13): stated limitation / future work.

**Repository** (paths relative to `repo/`):
- `README.md`, `FAQ.md`, `3LCache/README.md`, `requirements.txt`, `.github/workflows/build.yml`
- `CMakeLists.txt` (:1, :24, :171-229, :263-333), `libCacheSim/cache/CMakeLists.txt`,
  `libCacheSim/cache/eviction/CMakeLists.txt` (:85-100), `libCacheSim/bin/cachesim/CMakeLists.txt`
- `scripts/install_dependency.sh`, `scripts/install_libcachesim.sh`,
  `scripts/LightGBM/VERSION.txt`, `scripts/LightGBM/include/LightGBM/c_api.h` (:352, :387)
- `3LCache/TLCache.h` (:23-27, :35-98, :174-229, :236-306, :240-269, :288-289)
- `3LCache/TLCache.cpp` (:12-60, :63-68, :75-127, :130-156, :159-189, :192-272, :275-298,
  :301-341, :343-380, :383-470)
- `3LCache/TLCache_Interface.cpp` (:61-121, :85-89, :228-263, :314-345)
- `3LCache+/TLCacheN.cpp`, `3LCache+/README.md`
- `libCacheSim/bin/cachesim/cache_init.h` (:141-157), `libCacheSim/bin/cachesim/sim.c` (:19-108),
  `libCacheSim/bin/cachesim/main.c` (:57-66), `libCacheSim/bin/cachesim/cli_parser.c` (:94, :165, :317-345)
- `libCacheSim/cache/eviction/LRB/lrb.cpp` (:88-410), `libCacheSim/cache/eviction/LRB/LRB_Interface.cpp` (:89),
  `libCacheSim/cache/eviction/LRU.c` (:67), `libCacheSim/cache/eviction/GLCache/`, `libCacheSim/cache/eviction/LHD/`
- `libCacheSim/dataStructure/hashtable/chainedHashTableV2.c` (:101-103)
- `libCacheSim/traceAnalyzer/popularity.cpp`, `libCacheSim/bin/traceUtils/traceConvMain.cpp`,
  `libCacheSim/bin/dep/cpp/tencent.h`
- `3LCache/scripts/run_scripts.sh`, `executor_libcachesim.py` (:26-76), `cpu_overhead_boxplot.py`
  (:81, :112-119, :175-180), `libcachesim_result_collect.py` (:113-136, :192), `draw_figure.py`
  (:19, :76, :145, :197-202), `3LCache/scripts/trace_info/*.txt`,
  `3LCache/scripts/result/io.traces.ns117.csv`, `3LCache/scripts/figures/bmr.pdf`
- `data/` (~50 sample traces; `data/w01.csv` format check, `data/tencentBlock_ns3964.zip`)

**External** (scoop check / provenance):
- libCacheSim issue [#119](https://github.com/1a1a11a/libCacheSim/issues/119) — 3L-Cache merged
  upstream by PR #126.
- [Learning-Augmented Heuristics / S4-FIFO, arXiv 2608.27975](https://arxiv.org/html/2608.27975v1).
- [SL-Cache, DASFAA 2026](https://link.springer.com/chapter/10.1007/978-981-92-0363-5_36).
- USENIX paper page https://www.usenix.org/conference/fast25/presentation/zhou-wenbin
  (returned HTTP 403 to automated fetch; artifact badges could not be confirmed).
