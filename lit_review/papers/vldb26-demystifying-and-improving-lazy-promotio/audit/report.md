# Demystifying and Improving Lazy Promotion in Cache Eviction

*Desk review only — nothing in this report was built or executed. Every claim about the
code is from reading files at the shallow clone in `repo/` (HEAD `7e50398`, 2026-01-06).*

## 1. Paper summary

**Problem.** LRU promotes an object to the list head on every hit; each promotion needs a
lock, so LRU does not scale with core count (§2.1, p.2–3). Production systems have
independently invented *relaxations* of LRU promotion — Meta CacheLib's delayed
promotion, Meta HHVM's try-lock probabilistic promotion, CliqueMap/Ristretto's batched
promotion, RocksDB/PostgreSQL's FIFO-reinsertion, Redis's sampled eviction. These are
collectively "Lazy Promotion" (LP). The paper's claim is that nobody has measured whether
they actually trade efficiency for scalability, or which of them is best (§1, p.2).

**Key idea / contributions.**
1. A large trace-driven benchmark of five LP techniques (Probabilistic-LRU, Batch-LRU,
   Delay-LRU, FIFO-reinsertion, Random-LRU) over 6357 production traces from 9 companies
   (Table 2, p.4), plus concurrent implementations for throughput measurement.
2. A new metric, **promotion efficiency** = `(#miss_FIFO − #miss_A) / #promos_A`
   (§3, p.4) — misses avoided per promotion. LRU's is 0.037; Delay-LRU reaches 0.72 and
   1-bit FIFO-reinsertion is a close second (§3.6, p.9).
3. An oracle study (§4): "Belady early eviction" (BEE) evicts at access time if the next
   reuse distance exceeds the estimated average eviction age `cache_size/miss_ratio`.
   Belady-Random and Belady-RandomLRU have essentially the same miss ratio (Fig. 9a/9b),
   i.e. **ranking objects for eviction is unnecessary** given a good binary
   reused-before-eviction signal; BEE cuts LRU's miss ratio by 14% at tolerance 5.
   Offline FIFO-reinsertion (iteratively un-marking reinsertions that led to no hit)
   removes >90% of LRU's promotions *and* lowers miss ratio (Fig. 10, p.10).
4. Two new practical algorithms (§5): **D-FR** (don't increment the FIFO-reinsertion
   frequency counter for hits clustered within `delay_ratio × cache_size` insertions) and
   **AGE** (at eviction, refuse to reinsert an object whose age exceeds
   `cache_size/miss_ratio × factor`). Both cut promotions 20–60% below FIFO-reinsertion at
   similar-or-lower miss ratio, roughly doubling promotion efficiency (Fig. 11, p.11).

**Evaluation setup.** Miss-ratio/promotion results are deterministic simulations on a
Cloudlab c8220 cluster, cache size = 1% of the working set, `--ignore-obj-size`
(so every object counts as size 1). Scalability is measured separately on one Cloudlab
r650 (2×36-core Xeon 8360Y, 256 GB), hyperthreading and turbo disabled, one NUMA domain,
using a **synthetic Zipfian trace** (α=1.0), 5 repetitions, cache sizes chosen per
algorithm so that all reach a 1% miss ratio (§3, p.4).

**Headline numbers.** Delay-LRU at delay ratio 0.1: promotions down to 24% of LRU with no
visible miss-ratio change, 5× throughput at 16 threads; up to 12× at delay ratio 0.9
(§3.3, Fig. 4). FIFO-reinsertion with a 2-bit counter *reduces* LRU's miss ratio by ~2%
(§3.4, Fig. 5c). Probabilistic-LRU raises miss ratio ~2% even at prob=0.5 (§3.1). D-FR
cuts FIFO-reinsertion's promotions by a further 60% on the median trace (§5.1, Fig. 11).

**Topic.** `caching` — a pure cache-eviction-policy study; the artifact is a user-space
CPU simulator. This is the archetypal fit for the course.

## 2. Artifact audit

### 2.1 Provenance and structure

The paper states on p.1 under *PVLDB Artifact Availability*: "The source code and data are
available at https://github.com/cacheMon/Lazy-Promotions." That is exactly the cloned
repo, and `cacheMon` is the same GitHub org that hosts libCacheSim, the simulator this
work extends. **Official: yes.** No ACM/VLDB reproducibility badge was found in web
searches; the repo has no `LICENSE` at top level (`repo_facts.json: license: null`),
though `simulator-concurrent/LICENSE` (inherited from libCacheSim) exists. 4 stars, 2
forks, created 2025-10-01, last push 2026-01-06 — actively maintained through publication.

```
README.md                 build + per-figure reproduction instructions
simulator/                libCacheSim fork, sequential — miss ratio & promotion counts
simulator-concurrent/     libCacheSim fork, threaded — throughput / scalability
scripts/                  task generation, result parsing, figure generation, datasets.txt
scripts/data/*.tar.gz     the authors' released raw results (also on Google Drive)
```
104 k lines of C, 66 k of headers, 12.5 k C++, 7.7 k Python. This is the real system, not a
placeholder.

### 2.2 Paper component → code path

| paper component | code path | notes |
|---|---|---|
| Probabilistic-LRU (§3.1) | `simulator/libCacheSim/cache/eviction/LRUProb.c`, `lpLRU_prob.c` | CLI `lru-prob -e prob=` (`bin/cachesim/cache_init.h:155`) |
| Batch-LRU (§3.2) | `simulator/libCacheSim/cache/eviction/lpFIFO_batch.c` | CLI `batch -e batch-size=` (`cache_init.h:195`) |
| Delay-LRU (§3.3) | `simulator/libCacheSim/cache/eviction/LRUdelay.c` | delay check at `LRUdelay.c:166`, promotion counter at `:173` |
| FIFO-reinsertion (§3.4) | `simulator/libCacheSim/cache/eviction/Clock.c`, `FIFO_Reinsertion.c` | CLI `clock -e n-bit-counter=` |
| Random-LRU (§3.5) | `simulator/libCacheSim/cache/eviction/RandomLRU.c`; concurrent: `RandomK.c` | naming is inconsistent between the two trees; `parse_data.py:73-74` maps `Random`→"RandomK", `RandomLRU`→"Random" |
| LP on ARC / 2Q (§3.7) | `ARC_{LRU,Prob,Delay,Batch,FR}.c`, `TwoQ_{Prob,Batch,FR}.c` | promotion counts summed over T1/T2 (`ARC_Delay.c:238`) |
| Belady early eviction (§4.1) | `RandomBelady.c`, `BeladyRandomLRU.c` | CLI `-e scaler=` = the tolerance factor θ |
| Offline FIFO-reinsertion (§4.2) | `Opt_Clock.cpp`, `offlineFR.c` | CLI `opt-clock -e iter=5` |
| **D-FR** (§5.1) | `simulator/libCacheSim/cache/eviction/DelayFR.c` | delay check `DelayFR.c:146-151`, reinsertion+`n_promotion` at `:217-223` — matches Listing 5 exactly |
| **AGE** (§5.2) | `simulator/libCacheSim/cache/eviction/AGE.c` | `expected_reuse_distance = cache_size/miss_ratio` at `AGE.c:234-235`, retention filter `is_retained1()` at `AGE.c:310-328` — matches Listing 6 |
| promotion metric | `cache->n_promotion`, reported by `bin/cachesim/main.c:52` | parsed by `scripts/parse_data.py:15` |
| promotion-efficiency metric | `scripts/process_data.py:24-26` | `(mr_FIFO − mr_A)·#req / #promos` — matches §3's definition |
| Fig. 1–13 | `scripts/generate_figures.py` (one function per sub-figure) | `python generate_figures.py figure11a figure11b ...` |
| scalability harness | `simulator-concurrent/libCacheSim/bin/cachesim/sim.c:85-199` | `parallel_simulate()`; pthreads + `pthread_spin_lock` (`eviction/LRU.c:142`) |

**Gap:** `AGE` is not implemented in `simulator-concurrent/` (grep for `AGE_init` /
`"age"` finds nothing under that tree; `cache_init.h` there maps only
`fifo/lru/lru-prob/lru-delay/batch/clock/delayfr/randomK`). So the paper has **no measured
throughput for AGE** — consistent with Fig. 1 (right) plotting only promotions vs miss
ratio for D-FR/AGE, and with §5.1 reporting a throughput number for D-FR only.

### 2.3 Build route on this machine

Dependencies (`simulator/CMakeLists.txt:143-181`): GLib (required), argp (in glibc on
Debian), zstd (required because `OPT_SUPPORT_ZSTD_TRACE` defaults ON, and every trace in
`datasets.txt` is `.zst`), tcmalloc (optional — `CMakeLists.txt:173` only prints a
warning), pthreads. `ENABLE_GLCACHE` and `ENABLE_LRB` default OFF, so xgboost/LightGBM
are *not* needed. C11 / C++17, cmake ≥ 3.12 — all satisfied by gcc 12.2 / cmake 3.25.

`simulator/scripts/install_dependency.sh` uses `sudo apt` and `sudo make install`, which
we cannot run. The equivalent user-space route is a conda env with `glib`, `zstd`
(`gperftools` optional); this is a package-manager swap, not a blocker. The repo README
already anticipates compiler strictness and gives the fallback flags
(`README.md:48-54`: `-Wno-implicit-int … -fpermissive`), which suggests the code does not
build cleanly on newer toolchains — on gcc 12 it is likelier to build than on the Ubuntu
24.04 the authors targeted, but this is an unverified prediction.

`USE_HUGEPAGE` defaults ON but resolves to `madvise(MADV_HUGEPAGE)` guarded by
`#ifndef MADV_HUGEPAGE` in `libCacheSim/include/config.h:46-49` — unprivileged, and it can
be switched off with `-DUSE_HUGEPAGE=OFF`. The CMake comment on line 22 mentioning
`sudo tee /sys/kernel/mm/transparent_hugepage/enabled` is a tuning hint, not a requirement.

Python side: `scripts/requirements.txt` pins pandas 2.3.1 / numpy 2.3.2 / seaborn 0.13.2 /
matplotlib 3.10.6 — all current (2025-era), pip-installable. Two gaps:
`scripts/process_data.py:2` imports `textual_pandas` (unused, not in requirements — delete
the line) and `:6` imports `scipy` (not in requirements — `pip install scipy`).
`scripts/parse_data.py:113` opens `./datasets.txt` relative to the CWD, so the scripts must
be run from `scripts/`.

### 2.4 Data

`README.md:70` points at `https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/`,
`trace_type = oracleGeneral`. I fetched that index: it serves `alibabaBlock`,
`cloudphysics`, `fiu`, `metaCDN`, `metaKV`, `metaStorage`, `msr`, `systor`,
`tencentBlock`, `tencentPhoto`, `twitter`, `wiki`. `scripts/datasets.txt` lists 6362
lines, 6357 of which match the paper's trace collections; **1506 of them are
`akamai/…` (CDN 1) or `cf/…` (CDN 2)** — the two unnamed "private CDN service companies" —
and those two directories are *not* on the public server. So ~4851 of 6357 traces (76%)
are publicly downloadable; the rest are not obtainable and have no named substitute.

Mitigating: `scripts/data/lazy_promotions_data.tar.gz` and `lazy_throughput.tar.gz` ship
the authors' own raw results in-repo (plus Google Drive mirrors,
`README.md:159,323`), so the figure pipeline can be exercised end-to-end and any locally
re-run subset can be diffed against the authors' numbers trace-by-trace. I could not
inspect the tarball contents (no shell), so whether they hold raw `.cachesim` output or a
pre-parsed frame is **unclear**.

### 2.5 Evaluation scripts

Present and per-figure specific: `scripts/generate_task.sh` emits every
(trace × algorithm × parameter) command (9 prob values, 9 batch, 9 delay, 8 clock bits,
8 random-LRU samples, 11 × 2 Belady scalers, 5 ARC + 5 2Q variants, 6 D-FR ratios, 10 AGE
factors, + LRU/FIFO/opt-clock ≈ 70 runs per trace); `README.md:216-305` maps each figure to
the `grep` that selects its subset. Orchestration assumes the authors' `distComp` +
redis + systemd cluster manager, but the task file is just a list of shell commands —
replaceable by `xargs -P16` on this machine. `generate_scalability_task.sh` drives the
concurrent binary, and prefixes `disable_turbo.sh` / `disable_hyperthread.sh`, which need
root (see §3, H2).

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper p.1 "PVLDB Artifact Availability: … https://github.com/cacheMon/Lazy-Promotions"; repo is under the authors' `cacheMon` org and contains the actual algorithms, not stubs — `simulator/libCacheSim/cache/eviction/AGE.c` and `DelayFR.c` implement Listings 5 and 6 of §5 line-for-line (`DelayFR.c:146-151`, `AGE.c:231-254`), plus 104 k lines of supporting C. |
| `H2_no_root` | **pass** | The sequential simulator is a plain user-space CLI (`simulator/libCacheSim/bin/cachesim/main.c`); the concurrent one uses pthreads + `pthread_spin_lock` (`simulator-concurrent/.../eviction/LRU.c:142`), no privileged syscalls. Red flags are all avoidable: `simulator/scripts/install_dependency.sh:4` `sudo apt` → replaceable by conda (glib/zstd); `scripts/disable_turbo.sh:6,23` (`modprobe msr`, `wrmsr`) and `scripts/disable_hyperthread.sh` are *measurement-stability* helpers for the scalability runs only and can be skipped (at the cost of noisier throughput — see §6); `simulator-concurrent/dockerfile` is inherited from upstream libCacheSim and is not on any documented path; `USE_HUGEPAGE` is `madvise`-based (`libCacheSim/include/config.h:46-49`) and can be disabled at configure time. No kernel module, eBPF, perf counter, or KVM use anywhere in the build or run path. |
| `H3_hardware_fit` | **pass** | CPU-only trace simulation, no GPU at all. Paper scale needed "at least a day using 15 nodes (64 core, 376 GB RAM)" (`README.md:157-158`), so *full* scale does not fit — but the headline claims are distributions over independent per-trace simulations, so a trace subset is a faithful scale-down. Two caveats: `README.md:154` says "at least 256 GB of RAM … required to run some larger traces" vs our 125 GB, and the largest collections (twitter ≈ 4.6 B requests/trace, tencentBlock 33 B total, Table 2 p.4) would both exceed RAM (the hash table holds every distinct object) and eat the 257 GB of free disk. Mitigation is to use the small/medium public collections. |
| `H4_obtainable_deps_data` | **pass** | Deps are user-space installable (§2.3: GLib, zstd, optional tcmalloc; xgboost/LightGBM off by default per `CMakeLists.txt:188-213`). Traces: the public CMU index at `ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/` (linked from `README.md:70`) serves cloudphysics, msr, fiu, metaKV, metaCDN, tencentBlock, tencentPhoto, alibabaBlock, twitter, wiki — 4851 of the 6357 entries in `scripts/datasets.txt`. The 1506 `akamai/` + `cf/` entries (the two anonymous CDNs) are *not* public and have no named substitute; this shrinks but does not invalidate the benchmark, and the authors' own raw results for those traces are shipped in `scripts/data/lazy_promotions_data.tar.gz` for comparison. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** Figure 11a + 11b (p.11) and the abstract's headline claim: *"D-FR and AGE
reduce promotions by 20–60% while achieving a similar or lower miss ratio"* — specifically
that, relative to LRU, D-FR (`delay-ratio=0.05`, 1-bit) and AGE (`scaler=0.5`) sit at a
much lower relative-promotion value than Delay/FR/Batch/Prob at the same or better relative
miss ratio. Secondary target, essentially free once the pipeline runs: Figure 4a/4c
(Delay-LRU at `delay-time=0.1` → 24% of LRU's promotions with no visible miss-ratio
increase) and Figure 5c (2-bit FIFO-reinsertion beats LRU's miss ratio by ~2%).

**Scale-down.** Replace `scripts/datasets.txt` (6362 lines) with a public subset of
~200–400 traces that preserves collection diversity: all of cloudphysics (106), msr (14),
fiu (9–10), metaKV (5), metaCDN (3), wiki (3–4), plus a stratified random sample of
~100 tencentBlock, ~50 alibabaBlock and ~10 twitter clusters, skipping any trace whose
uncompressed object count would blow past ~60 GB of RAM. Drop the `akamai/` and `cf/`
lines entirely. Keep the paper's cache size (1% of working set) and
`--ignore-obj-size 1`. Report distributions (box plots) over the subset, not means over
6357 traces, and state the subset explicitly.

**Steps.**
1. Conda env: `glib`, `zstd`, `gperftools` (optional), cmake; `pip install -r
   scripts/requirements.txt scipy`; delete `import textual_pandas` at
   `scripts/process_data.py:2`.
2. `cmake -DCMAKE_BUILD_TYPE=Release -DUSE_HUGEPAGE=OFF -DENABLE_TESTS=OFF ..` in
   `simulator/_build`; fall back to the flags in `README.md:50-53` if the build breaks.
   Smoke-test on the bundled trace `simulator-concurrent/data/cloudPhysicsIO.oracleGeneral.bin`.
3. `wget` the chosen traces from the CMU FTP index (budget ≤ 150 GB of the 257 GB free).
4. Edit `scripts/generate_task.sh` paths (`traces_dir`, `simulator`, `output_dir`,
   `datasets_file`) and run it; then, instead of distComp, feed the generated `~/task`
   file through `cut -d: -f5- | xargs -P 14 -I{} bash -c '{}'`. Run the `lru` and `fifo`
   lines first — `README.md:207` notes both are required baselines for every figure.
5. `cd scripts && python parse_data.py <results_dir> && python process_data.py &&
   python generate_figures.py figure11a figure11b figure11c figure4a figure4c figure5c`.
   (`process_data.py:101` unconditionally reads `data/scalability.feather`, so either run
   `parse_scalability.py` on an empty dir first or guard that read.)
6. Cross-check: untar `scripts/data/lazy_promotions_data.tar.gz` and diff per-trace miss
   ratios / promotion counts against the locally regenerated ones for the same traces.

**Effort.** ~4–6 person-days (1 day environment + build, 1 day trace download, 1–2 days
replacing distComp and debugging the parse/plot pipeline, 1 day writing up), plus roughly
100–300 CPU-core-hours of simulation for ~250 traces × ~70 configurations — i.e. under a
day of wall-clock on 14–16 cores if the largest traces are excluded. No GPU hours.

**Level: H.** Per-figure task selectors exist (`README.md:216-305`), the figure code is
one function per sub-figure (`scripts/generate_figures.py`), the metric definitions in
`process_data.py:24-33` match the paper's formulas, the released raw results give a
ground-truth cross-check, dependencies are current, and the whole thing is deterministic
CPU simulation with no GPU/kernel/hardware requirement. It is *not* "clone and run": the
orchestration layer (distComp + redis + systemd) has to be replaced, `datasets.txt` has to
be pruned to the public traces, and two Python imports are missing from
`requirements.txt`. That is the ordinary porting friction an H still allows, not an M.

## 5. Add-on ideas

### A1 — Trace-driven concurrency, and the missing AGE throughput number

**Hypothesis.** We hypothesize that driving the concurrent cache with *real production
traces* instead of the hard-coded synthetic Zipfian generator changes the throughput
ranking of the five lazy-promotion techniques at 16 threads (Figs. 2b/3b/4b/5b/6a), and
that AGE — for which the paper reports no throughput at all — pays back less of its
promotion reduction in throughput than D-FR does, because its retention filter lengthens
the eviction-time critical section.

**Mechanism.** (a) Port `AGE.c` into `simulator-concurrent/libCacheSim/cache/eviction/`
with the same `pthread_spin_lock` discipline the other concurrent algorithms use, and
register it in the concurrent `cache_init.h`. (b) Extend `parallel_simulate()` so the
request stream can come from an `oracleGeneral` reader instead of `generate_zipf()`,
sharding requests across threads the way the Zipf path already does at `sim.c:152-166`.
(c) Sweep Zipf α ∈ {0.6, 0.8, 1.0, 1.2} and cache/working-set ratios other than the
~90% implied by the hard-coded constants, and compare against the trace-driven numbers.

**Code locations.** `simulator-concurrent/libCacheSim/bin/cachesim/sim.c`,
`simulator-concurrent/libCacheSim/bin/cachesim/cache_init.h`,
`simulator-concurrent/libCacheSim/cache/eviction/DelayFR.c`,
`simulator-concurrent/libCacheSim/cache/eviction/CMakeLists.txt`,
`simulator/libCacheSim/cache/eviction/AGE.c`, `scripts/generate_scalability_task.sh`,
`scripts/parse_scalability.py`.

**Motivating evidence.** Every throughput claim in the paper (Figs. 1a, 2b, 3b, 4b, 5b,
6a and the "12× speedup") rests on a single synthetic configuration: §3 says the harness
uses "10 million requests for 1 million unique objects, with a skewness parameter of 1.0",
but the code at `sim.c:92-95` sets `req_cnt = 10000000`, **`obj_num = 100000`** and
`alpha = 1` — a 10× smaller working set than the paper states, and the cache sizes in
`generate_scalability_task.sh` (88 000–94 000) are then ~90% of that working set, an
unusually large cache for a skew study. The paper itself notes the ranking depends on
workload skew ("the effectiveness of Batch-LRU depends on the skewness of the workload",
§3.2) but never varies α. And AGE simply has no concurrent implementation (no `AGE_init`
anywhere under `simulator-concurrent/`), so the paper's second new algorithm is never
shown to be scalable at all.

**Feasibility: M.** The port itself is small (AGE is ~380 lines; the reader already exists
in libCacheSim), but this is a *throughput* experiment on a shared machine with no root:
we cannot disable turbo (`scripts/disable_turbo.sh` needs `wrmsr`) or hyperthreading
(`scripts/disable_hyperthread.sh` needs root), and 16 threads on 16 cores/32 threads will
contend with whatever else is running. The experiment is still meaningful with
many repetitions, `taskset` pinning to one core set, and reporting variance — but it needs
careful methodology, and building a trace-driven concurrent harness is new eval plumbing.

**Research value: H.** The paper's central selling point is "LP buys scalability without
efficiency loss"; showing that the scalability half of that claim is measured on a single
synthetic point whose parameters do not even match the paper text is a genuine finding,
and the AGE gap is a hole a VLDB reviewer would have flagged. Either outcome is
informative.

**Scoop check.** Queries: *"concurrent scalable SIEVE S3-FIFO lock contention throughput
multi-thread evaluation 2026 cache"*, *"Mobius lock-free cache throughput-optimized
SIGMETRICS 2025"*, plus the paper's Semantic Scholar citation list. Result: **partial**.
[Mobius — "Using Lock-Free Design for Throughput-Optimized Cache Eviction", SIGMETRICS/POMACS 2025](https://dl.acm.org/doi/10.1145/3727136)
does evaluate concurrent cache throughput on both synthetic and real high-concurrency
workloads, but it proposes a lock-free FIFO design; it does not measure the five LP
techniques' throughput ranking, and it predates this paper. The three works citing this
paper (Clock2Q+ arXiv:2511.21958, ORBIT, BufBench) do not touch concurrency of LP.

---

### A2 — Learned Belady-early-eviction: a binary reuse classifier in place of the age heuristic

**Hypothesis.** We hypothesize that a lightweight *online* binary classifier predicting
"will this object be requested again before it reaches the average eviction age?", trained
on features the cache already tracks (age since last access, frequency counter, position
in the queue, inter-arrival gap), closes a substantial fraction of the miss-ratio gap
between AGE/FIFO-reinsertion and the Belady-early-eviction oracle, at a promotion count no
higher than AGE's — on block and CDN traces where AGE currently *increases* miss ratio.

**Mechanism.** Replace AGE's single-feature threshold rule
(`is_retained1()`, which predicts next-reuse-time = current age and compares it to
`scaler × cache_size/miss_ratio`) with a small online logistic-regression / counting
classifier. Labels are free and online: when an object is evicted, we know whether it was
hit since its last reinsertion decision; feed that back as the training signal. Keep the
decision at eviction time only (the paper proves in §4.2 that eviction-time promotion
dominates hit-time promotion), so the classifier is invoked once per eviction, not once
per request. Use `RandomBelady`/`BeladyRandomLRU` (θ sweep) as the achievable upper bound
and `AGE`/`Clock` as the lower bound on the same traces.

**Code locations.** `simulator/libCacheSim/cache/eviction/AGE.c`,
`simulator/libCacheSim/cache/eviction/BeladyRandomLRU.c`,
`simulator/libCacheSim/cache/eviction/RandomBelady.c`,
`simulator/libCacheSim/include/libCacheSim/cacheObj.h`,
`simulator/libCacheSim/bin/cachesim/cache_init.h`, `scripts/generate_task.sh`.

**Motivating evidence.** §4.1 states the idea and leaves it undone: *"If we employ a binary
classifier to predict whether an object will be reused before being evicted[,] the model
can be used to trigger early eviction. This differs from existing learned eviction
algorithms, e.g., LRB, which predict each object's reuse distance using regression"* —
with a footnote arguing binary classification is the easier objective. The headroom is
quantified by the paper's own figures: BEE cuts LRU's miss ratio by 14% at θ=5 (Fig. 9a/9b,
p.10) and offline FIFO-reinsertion removes >90% of promotions while *lowering* miss ratio
(Fig. 10, p.10), whereas the practical AGE only matches FIFO-reinsertion's miss ratio and
"increases the miss ratio for some traces" (§5.2, p.11). The oracle baselines are already
implemented, so the gap is directly measurable trace-by-trace.

**Feasibility: M.** The change is localized (a new eviction algorithm plus a few fields in
the `cache_obj_t` union in `cacheObj.h`, well under 1–2 k LOC) and the existing harness,
baselines and metrics all apply unchanged. The risks that keep this off H: the feature set
and online-learning schedule need real experimentation to beat a one-line heuristic, and
demonstrating that the classifier is *cheap* (the paper calls per-request binary prediction
"computationally expensive", §4.2) means also getting the concurrent tree to build it —
which, per A1, is a separate measurement problem.

**Research value: H.** This is the paper's own stated open problem, the upper bound is
already computed in the artifact, and both outcomes teach something: if a tiny online
classifier captures most of the BEE gap, that is a strong practical result; if it does not,
that quantifies how much of BEE's advantage is irreducibly oracular — which would sharpen
the paper's "ranking is unnecessary" claim.

**Scoop check.** Queries: *"learned binary classifier early eviction cache reused before
eviction libCacheSim 2025"*, *"cache eviction predict will be reused before eviction binary
classification learned policy 2025 2026"*. Result: **partial**. Learned eviction exists —
LRB (regression on reuse distance), GL-Cache (segment-level),
[LearnedCache (perceptron for the Linux page cache, arXiv:2605.26168)](https://arxiv.org/html/2605.26168v1),
[a learned eviction framework with minimal overhead (arXiv:2301.11886)](https://arxiv.org/pdf/2301.11886) —
but none of them formulates the BEE binary "reused before the average eviction age" label
or plugs it into FIFO-reinsertion's eviction-time decision. Most 2026 hits for this
phrasing are LLM KV-cache token eviction, which is a different problem.

---

### A3 — Object-size-aware lazy promotion

**Hypothesis.** We hypothesize that when object sizes are honoured instead of ignored, the
promotion-efficiency ranking of the LP techniques changes on CDN and object-cache traces,
and that a size-weighted delay/age threshold (promote cheaply-stored objects more readily
than large ones) lowers *byte* miss ratio at an equal promotion count compared with
size-blind D-FR and AGE.

**Mechanism.** Drop `--ignore-obj-size 1` and re-run the sweep with byte-denominated cache
sizes. Then make the two new algorithms size-aware: in D-FR, scale `delay_time` by
`obj_size / mean_obj_size` so that large objects must wait longer before earning a
frequency increment; in AGE, scale the retention threshold
(`expected_reuse_distance × scaler`) inversely with object size, so a large stale object is
evicted sooner than a small one of the same age. Report both object and byte miss ratio,
which `main.c` already emits.

**Code locations.** `simulator/libCacheSim/cache/eviction/DelayFR.c`,
`simulator/libCacheSim/cache/eviction/AGE.c`,
`simulator/libCacheSim/cache/eviction/LRUdelay.c`,
`simulator/libCacheSim/bin/cachesim/main.c`, `scripts/generate_task.sh`,
`scripts/process_data.py`.

**Motivating evidence.** Every single simulation in the paper is run with
`--ignore-obj-size 1` (`README.md:77-148`, and every line of `scripts/generate_task.sh`),
and `process_data.py:12` hard-filters to `Ignore Obj Size == 1` — so all 6357 traces are
evaluated as if every object were one unit. Yet Table 2 (p.4) shows the corpus is dominated
by object and CDN caches with wildly varying object sizes (Meta CDN: 231 M requests but
8594 TB of traffic; CDN 2: 2079 TB). The size fields are in the traces and the code already
tracks `n_byte_rewritten` (`DelayFR.c:221`, `AGE.c:244`) and byte miss ratio
(`main.c`), but none of it is reported. This is a clean, explicitly-visible simplifying
assumption.

**Feasibility: H.** No new harness: the simulator supports sized objects natively, the
change is a command-line flag plus a handful of lines in three eviction files, and the
metrics pipeline needs only a widened filter in `process_data.py:12`. Compute cost is the
same as a normal sweep.

**Research value: M.** A reviewer would agree it is a real gap and the byte-miss-ratio
result is worth having, but "sizes matter for CDN caches" is a well-established finding
(GDSF, LHD, LRB all model size), so the surprise is bounded: the interesting part is
whether the *LP ranking* — not the eviction ranking — is size-sensitive.

**Scoop check.** Queries: *"applying lazy promotion delay FIFO-reinsertion size-aware cache
promotion efficiency"*, and the paper's citation list. Result: **clear**. Size-aware
eviction is old, but no work applies it to the promotion/reinsertion decision or measures
promotion efficiency under sized objects.

---

### A4 — Lazy promotion on quick-demotion algorithms (S3-FIFO, SIEVE, W-TinyLFU)

**Hypothesis.** We hypothesize that S3-FIFO and SIEVE already operate near the
offline-FIFO-reinsertion promotion-efficiency bound, so adding delay/batch/probabilistic
relaxations to them yields <10% further promotion reduction with no miss-ratio benefit —
whereas W-TinyLFU, which still maintains an LRU window, behaves like ARC/2Q and benefits
as much as they do.

**Mechanism.** Instrument `cache->n_promotion` in `Sieve.c`, `S3FIFO.c` and `WTinyLFU.c`
(they currently do not count promotions, so they are invisible to
`process_data.py`), then add `_Delay` / `_Batch` / `_Prob` / `_FR` variants of their
in-queue promotion points, following exactly the pattern the authors used for ARC and 2Q
in `ARC_Delay.c` / `TwoQ_FR.c`. Register the new names in `cache_init.h` and extend
`generate_task.sh` and the `algorithms` map in `parse_data.py:64-81`.

**Code locations.** `simulator/libCacheSim/cache/eviction/Sieve.c`,
`simulator/libCacheSim/cache/eviction/S3FIFO.c`,
`simulator/libCacheSim/cache/eviction/ARC_Delay.c`,
`simulator/libCacheSim/cache/eviction/TwoQ_FR.c`,
`simulator/libCacheSim/bin/cachesim/cache_init.h`, `scripts/parse_data.py`.

**Motivating evidence.** §3.7 deliberately limits the advanced-algorithm study to ARC and
2Q ("We illustrate this with 2Q and ARC"), while §4.1 makes an *unmeasured* claim about
exactly the algorithms left out: *"This observation also explains why the new eviction
algorithm[s], such as S3-FIFO and SIEVE, achieve state-of-the-art efficiency. They evict
new objects quickly (called quick demotion) without ranking."* Both are already
implemented in the repo (`Sieve.c`, `S3FIFO.c`, `S3FIFOd.c`, `WTinyLFU.c` in the concurrent
tree), so the claim is testable with the paper's own promotion-efficiency metric.

**Feasibility: H.** The template exists (five ARC variants and five 2Q variants are already
in the tree), the metric pipeline is unchanged, and the compute cost is one more sweep over
the same trace subset.

**Research value: M.** It closes a stated-but-unmeasured claim and would strengthen the
paper's conclusion that "future LP techniques can be built on top of a FIFO queue using
FIFO-reinsertion" (§4.2) — but the expected answer (SIEVE/S3-FIFO are already lazy) is the
one most readers would guess, so the surprise potential is moderate.

**Scoop check.** Queries: *"applying lazy promotion delay FIFO-reinsertion to S3-FIFO SIEVE
promotion efficiency evaluation"*, plus the citation list of the paper. Result:
**partial** — [Clock2Q+ (arXiv:2511.21958)](https://arxiv.org/pdf/2511.21958), which cites
this paper, combines CLOCK with 2Q for VMware vSAN metadata caching, and
[LAH/S4-FIFO (arXiv:2608.27975)](https://arxiv.org/html/2608.27975v1) tunes S3-FIFO's
parameters with a learned model; neither measures promotion efficiency of SIEVE/S3-FIFO
or adds LP relaxations to them.

---

### A5 — Self-tuning lazy promotion under a promotion budget

**Hypothesis.** We hypothesize that an online controller that adapts the delay threshold
(Delay-LRU / D-FR) or the age scaler (AGE) to hold a *target promotion rate* achieves a
lower miss ratio than the best static parameter at the same promotion count, with the gain
concentrated on the low-skew traces where Batch-LRU and Probabilistic-LRU currently fail.

**Mechanism.** Add a feedback loop that, every `cache_size` insertions, compares the
realized promotions-per-request against the operator-specified budget and adjusts the
threshold multiplicatively, with a secondary guard that backs off if the windowed miss
ratio drifts above the FIFO-reinsertion baseline. AGE already computes a *dynamic*
`expected_reuse_distance = cache_size / miss_ratio` from the running miss ratio
(`AGE.c:234-235`) but multiplies it by a *static* `scaler`; the controller replaces that
static scaler. Evaluate against the per-trace best static parameter (an oracle the sweep in
`generate_task.sh` already produces for free: 6 D-FR ratios, 10 AGE factors, 9 delay
ratios).

**Code locations.** `simulator/libCacheSim/cache/eviction/AGE.c`,
`simulator/libCacheSim/cache/eviction/DelayFR.c`,
`simulator/libCacheSim/cache/eviction/LRUdelay.c`,
`simulator/libCacheSim/cache/eviction/lpFIFO_batch.c`,
`simulator/libCacheSim/bin/cachesim/cache_init.h`.

**Motivating evidence.** The paper's own parameter-sensitivity figures (Fig. 12 for D-FR,
Fig. 13 for AGE, p.12) are framed as reassurance — "D-FR is not sensitive to delay ratio",
"Age is not sensitive to the factor parameter" — but they are *aggregate* box plots; §3.2
explicitly reports that per-trace behaviour is highly variable ("the long box indicates
that some traces enjoy a huge promotion reduction, while others do not observe much
benefit… the effectiveness of Batch-LRU depends on the skewness of the workload"). A
promotion budget is also the natural operator-facing knob: the whole point of LP is to hit a
lock-contention target, which is a rate, not a ratio.

**Feasibility: H.** Fully localized — a controller struct plus ~50 lines in each of three
eviction files, no new harness, and the static-parameter sweep that forms the comparison
baseline is already generated by `scripts/generate_task.sh`.

**Research value: M.** Adaptive parameter tuning is a solid, expected improvement rather
than a surprising one, and the paper pre-empts part of the motivation by arguing its
parameters are insensitive; the interesting result would be the *per-trace* (not aggregate)
regret against the best static setting.

**Scoop check.** Queries: *"adaptive delay ratio self-tuning lazy promotion cache delay-LRU
adaptive parameter tuning"*. Result: **partial** —
[LAH / S4-FIFO (arXiv:2608.27975)](https://arxiv.org/html/2608.27975v1) pre-trains a model
on 4140 production traces to pick S3-FIFO's parameters, which is the same *idea* (learned
/ adaptive configuration of a cache heuristic) applied to a different algorithm family and
a different objective (miss ratio, not promotion budget). Classic adaptive caches (ARC,
CACHEUS, LeCaR) adapt eviction policy, not promotion frequency.

## 6. Risks and open questions

1. **Memory ceiling.** `README.md:154` recommends ≥256 GB RAM "required to run some larger
   traces"; this machine has 125 GB (111 GB free, shared). The tencentBlock/twitter/CDN 2
   traces are the ones at risk. Unverified by reading alone — the team must probe trace
   sizes empirically and prune. This is the single most likely practical blocker for a
   naive "run everything in datasets.txt" attempt.
2. **1506 of 6357 traces are unobtainable.** `akamai/` (CDN 1) and `cf/` (CDN 2) are not on
   the public CMU index. Aggregate means/percentiles reproduced locally will therefore
   differ from the paper's by a collection-composition effect, not by a bug — any
   reproduction must say so explicitly and compare per-collection rather than globally.
3. **Throughput results are not honestly reproducible on this machine.** The paper's
   methodology (turbo off, hyperthreading off, single NUMA domain, dedicated node) is
   unreachable without root: `scripts/disable_turbo.sh:6,23` needs `modprobe msr` +
   `wrmsr`, `scripts/disable_hyperthread.sh:13` refuses to run as non-root. On a shared
   32-thread machine, a 16-thread scalability curve will be noisy. Any throughput claim
   should be reported with many repetitions and visible variance, or reframed as a
   promotion-count claim (which *is* deterministic and fully reproducible).
4. **Paper/code disagreement on the scalability workload.** §3 says the synthetic trace has
   "1 million unique objects"; `simulator-concurrent/libCacheSim/bin/cachesim/sim.c:93`
   sets `obj_num = 100000`. Combined with the 88 000–94 000 cache sizes in
   `generate_scalability_task.sh`, the measured configuration is a ~90%-of-working-set
   cache over 100 k objects. Either the released code is not the version used for the
   figures, or the paper's description is wrong. Worth resolving with the authors before
   building A1 on top of it.
5. **AGE has no concurrent implementation**, so one of the paper's two contributions has no
   scalability evidence at all. Reading confirms absence (`AGE_init` appears nowhere under
   `simulator-concurrent/`); whether the authors measured it and omitted it is unknown.
6. **Contents of the released result tarballs are unverified.** `scripts/data/*.tar.gz`
   could hold raw `.cachesim` stdout (directly consumable by `parse_data.py`) or an
   already-parsed frame; I could not open them. If they are pre-parsed, the per-trace
   cross-check in step 6 of §4 becomes harder.
7. **Build cleanliness.** `README.md:48-53` pre-emptively supplies
   `-Wno-implicit-int … -fpermissive` for "stricter compilers", which signals the C is not
   warning-clean. gcc 12.2 is older than the Ubuntu 24.04 toolchain the authors targeted, so
   it will probably build, but this is a prediction, not a test.
8. **Small methodological wrinkles in the scripts.** `process_data.py:2` imports
   `textual_pandas` (absent from `requirements.txt`, apparently unused), `:6` imports
   `scipy` (also absent), and `:101` reads `data/scalability.feather` unconditionally so
   the miss-ratio pipeline fails if scalability data was never generated.
   `parse_data.py:113` resolves `./datasets.txt` against the CWD. All trivially fixable,
   but they mean "pip install -r requirements.txt && run" will not work as written.
9. **No license at the repository root** (`repo_facts.json`, GitHub metadata `license:
   null`). The vendored `simulator-concurrent/LICENSE` comes from libCacheSim. For a course
   project this is a non-issue, but for any released derivative it should be clarified.

## 7. Evidence index

**Paper (`paper.txt`, page-marked; `pages/page-01.png`, `pages/page-11.png` read as images).**
- p.1 Abstract; PVLDB Artifact Availability statement (repo URL).
- p.1 Fig. 1 (left: promotions/throughput overview; right: D-FR and AGE).
- §1 Introduction, p.2 — motivation, production LP deployments, contribution list.
- §2.1–2.2, p.2–3 + Table 1, p.3 — the five LP techniques and their deployed systems.
- §3 dataset/testbed/metric definitions, p.4 + Table 2, p.4 — 6357 traces, Cloudlab c8220
  (miss ratio) and r650 with turbo/HT disabled (throughput), synthetic Zipf α=1.0,
  "10 million requests for 1 million unique objects", cache size = 1% of working set.
- §3.1 Probabilistic-LRU + Fig. 2, p.5. §3.2 Batch-LRU + Fig. 3, p.5–6 (skew dependence).
- §3.3 Delay-LRU + Fig. 4, p.6 (24% of LRU's promotions at ratio 0.1; 5×/12× throughput).
- §3.4 FIFO-reinsertion + Fig. 5, p.7 (2-bit counter beats LRU's miss ratio by ~2%).
- §3.5 Random-LRU + Fig. 6, p.8. §3.6 promotion efficiency + Fig. 7, p.9.
- §3.7 LP on ARC and 2Q + Fig. 8, p.9.
- §4.1 Belady early eviction, oracle definition, the binary-classifier future-work
  sentence, and the S3-FIFO/SIEVE remark + Fig. 9, p.9–10.
- §4.2 Offline FIFO-reinsertion + Fig. 10, p.10.
- §5.1 D-FR + Listing 5, §5.2 AGE + Listing 6, + Fig. 11, p.11; Figs. 12–13, p.12.

**Repository (paths relative to `repo/`).**
- `README.md` — structure (9-12), deps (20-33), build + strict-compiler flags (41-54),
  per-algorithm CLI (74-149), trace source (70), hardware/RAM recommendation (153-159),
  distComp orchestration (161-195), per-figure task selectors (216-305), scalability setup
  incl. `disable_turbo.sh` / `disable_hyperthreading.sh` (307-323), analysis scripts
  (324-357).
- `simulator/CMakeLists.txt` — USE_HUGEPAGE (22-23, 71-75), GLCache/LRB off by default
  (25,28,188-213), GLib/argp/zstd/tcmalloc discovery (143-181), C11/C++17 (12-16).
- `simulator/libCacheSim/include/config.h:44-49` — `MADV_HUGEPAGE` guard.
- `simulator/libCacheSim/cache/eviction/AGE.c` — dynamic reuse-distance estimate (231-254),
  retention filter (303-328), param parsing (343-378).
- `simulator/libCacheSim/cache/eviction/DelayFR.c` — delayed frequency increment (143-158),
  reinsertion + `n_promotion` (208-225), `delay_time = delay_ratio × cache_size` (309-315).
- `simulator/libCacheSim/cache/eviction/LRUdelay.c:166-176` — delay check and promotion count.
- `simulator/libCacheSim/cache/eviction/lpFIFO_batch.c` — Batch-LRU.
- `simulator/libCacheSim/cache/eviction/{LRUProb.c, lpLRU_prob.c, Clock.c, FIFO_Reinsertion.c,
  RandomLRU.c, RandomBelady.c, BeladyRandomLRU.c, Opt_Clock.cpp, offlineFR.c}`.
- `simulator/libCacheSim/cache/eviction/{ARC_LRU,ARC_Prob,ARC_Delay,ARC_Batch,ARC_FR}.c`,
  `{TwoQ_Prob,TwoQ_Batch,TwoQ_FR}.c` — §3.7; `ARC_Delay.c:238` sums T1/T2 promotions.
- `simulator/libCacheSim/cache/eviction/{Sieve.c, S3FIFO.c, S3FIFOd.c}` — present but not
  instrumented for promotions.
- `simulator/libCacheSim/include/libCacheSim/cacheObj.h` — per-object metadata union.
- `simulator/libCacheSim/bin/cachesim/cache_init.h` — CLI→algorithm map (lines 30, 36, 50,
  134-138, 155-157, 195-204).
- `simulator/libCacheSim/bin/cachesim/main.c:52` — output line incl. `n_promotion`.
- `simulator/libCacheSim/profiler/simulator.c:133` — promotion count propagated to results.
- `simulator/scripts/install_dependency.sh` — `sudo apt` / `sudo make install` route.
- `simulator-concurrent/libCacheSim/bin/cachesim/sim.c` — `parallel_simulate` (85-199),
  hard-coded `req_cnt/obj_num/warmup/alpha` (92-95), Zipf request sharding (152-166),
  pthread create/join (170-176), throughput output line (194-199).
- `simulator-concurrent/libCacheSim/bin/cachesim/data_gen.cpp` — Zipf generator.
- `simulator-concurrent/libCacheSim/bin/cachesim/cli_parser.c:273` — `trace_path` defaults to
  the bundled `dummy.txt`, so the concurrent binary needs no real trace.
- `simulator-concurrent/libCacheSim/bin/cachesim/cache_init.h` — concurrent algorithm map;
  contains `delayfr` (102), `lru-delay` (123), `batch` (143), `randomK` (44) but **no**
  `age`.
- `simulator-concurrent/libCacheSim/cache/eviction/LRU.c:67-179` — `pthread_spin_lock` usage.
- `simulator-concurrent/libCacheSim/cache/eviction/{DelayFR.c, Clock.c, LRUdelay.c,
  lpFIFO_batch.c, lpLRU_prob.c, RandomK.c, bp_wrapper.c, Sieve.c, S3FIFO.c, WTinyLFU.c}`.
- `simulator-concurrent/dockerfile` — upstream libCacheSim leftover (comments only).
- `scripts/generate_task.sh` — full parameter sweep (35-77), `--ignore-obj-size 1` everywhere.
- `scripts/generate_scalability_task.sh` — per-algorithm cache sizes 88 000–94 000, 16 threads,
  5 iterations.
- `scripts/parse_data.py` — output regex incl. promotion (9-16), algorithm name map (64-81),
  `./datasets.txt` dependence (113).
- `scripts/process_data.py` — promotion-efficiency formula (24-26), relative promotion/miss
  ratio vs LRU (28-40), `ignore obj size == 1` filter (12), unconditional
  `scalability.feather` read (101), stray `textual_pandas`/`scipy` imports (2, 6).
- `scripts/parse_scalability.py`, `scripts/generate_figures.py` (figure1b at 43-78 shows the
  exact parameter choices behind Fig. 1b/11), `scripts/style.py`,
  `scripts/matplotlib_wrapper.py`, `scripts/requirements.txt`.
- `scripts/datasets.txt` — 6362 lines, 6357 matching the paper's collections, 1506 of them
  `akamai/` or `cf/`. `scripts/traces.md` — per-collection counts vs the paper.
- `scripts/data/lazy_promotions_data.tar.gz`, `scripts/data/lazy_throughput.tar.gz` —
  released raw results (contents not inspected).
- `scripts/disable_turbo.sh:6,23,26` (`modprobe msr`, `wrmsr`),
  `scripts/disable_hyperthread.sh:13` ("Must run as root").
- `repo_facts.json` — HEAD 2026-01-06, 900 files, 135 MB, language breakdown, GitHub
  metadata (4 stars, not archived, `license: null`).

**External.**
- `https://ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/` — public trace
  index; confirms akamai/cf absence.
- https://github.com/cacheMon/Lazy-Promotions — repo under the authors' org.
- https://doi.org/10.14778/3785297.3785299, https://arxiv.org/abs/2608.29993 — paper.
- https://dl.acm.org/doi/10.1145/3727136 — Mobius, SIGMETRICS/POMACS 2025 (A1 scoop check).
- https://arxiv.org/html/2608.27975v1 — LAH / S4-FIFO (A4, A5 scoop checks).
- https://arxiv.org/pdf/2511.21958 — Clock2Q+, cites this paper (A4 scoop check).
- https://arxiv.org/html/2605.26168v1, https://arxiv.org/pdf/2301.11886 — learned eviction
  (A2 scoop check).
- Semantic Scholar citation list for arXiv:2608.29993 — 3 citing works (Clock2Q+, ORBIT,
  BufBench), none overlapping the proposed add-ons.
