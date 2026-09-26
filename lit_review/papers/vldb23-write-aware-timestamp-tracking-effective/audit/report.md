# Write-Aware Timestamp Tracking: Effective and Efficient Page Replacement for Modern Hardware

*Desk review only — nothing was built or run. Every claim below points at a paper section/figure
or a repository path.*

## 1. Paper summary

**Problem.** Page replacement in a DBMS buffer manager, revisited for NVMe SSDs and many-core
CPUs. The paper states four goals (p. 1, §1): replacement effectiveness, write awareness (flash
read/write asymmetry and endurance), CPU efficiency (>1M IOPS ⇒ millions of replacements/s), and
multi-core scalability (no global lists/queues).

**Key idea (§3).** *WATT* keeps a bounded per-page **access log of timestamps** (default 8 read
timestamps + 4 write timestamps, §4.3 table) instead of a single recency rank or counter. For each
order *i* it computes a *subfrequency* `SF_i = i / (t_now − t_i)` (Eq. 1) and takes the maximum over
orders as the page value (Eq. 2). The total value is
`PV = PV*_access + write_weight · PV*_write` (Eq. 3), so a single knob `write_weight` trades read
misses against write-backs. Two refinements: (a) the first-order subfrequency is **dampened** by a
constant (default 0.1, Fig. 6); (b) `t_now` is an **epoch counter** incremented once every
`cacheSize / k` evictions (default 4 epochs per full RAM replacement, Fig. 5), which both bounds
history usefulness and kills cache-line ping-pong on hot pages (§5.1).

**Finding victims (§3.2, §5.2, Listing 2).** No global ordering is possible because values change
with `t_now`, so WATT uses **random sampling with lazy evaluation** (as in Hyperbolic Caching):
sample a few pages to get a value threshold, then sample a larger batch and evict everything below
the threshold. Sampled frames are explicitly **prefetched**, and the page value is computed with
**AVX2** (Listing 3: one `__m256i` holds exactly 8 32-bit timestamps; a lookup table `iQuotient`
fixes up the `i` values for the cyclic insertion head and folds in the dampening factor).

**Concurrency (§5.1, §5.3).** Timestamps and heads are `std::atomic` written with
`memory_order_release` (single `MOV` on x86, no fences). Because of epochs, a hot page is usually
*not* written on access — 6 x86 instructions to check, 6 more to update. Races are argued to be
benign (§5.3): the worst case makes a page look *more* valuable, which is harmless.

**Evaluation setup.**
- *Simulation (§4)*: an in-house simulator, 10 algorithms (Table 1) × 5 traces (Table 2: TPC-C,
  TPC-E from instrumented Shore-MT; ZipfRO, dynZipfRO, dynZipfRW synthetic), 1–2 M accesses,
  10k–66k pages, buffer-pool ratio swept 1 %→100 %.
- *System (§6.1)*: WATT, Hyperbolic, Random and LeanEvict inside LeanStore on an **AMD EPYC 7713
  (64 c / 128 t), 512 GB RAM, Samsung PM1733 3.8 TB PCIe-4 SSD**, Linux 5.15. YCSB (α = 0.9, 25 GB
  and 400 GB, 100R and 90R/10W) and TPC-C (50 / 1600 / 3200 warehouses ⇒ 9 / 264 / 588 GB), **8 GB
  buffer pool**, 120 worker threads, up to 8 (scalability: 32) page-evictor threads, 20-minute runs.

**Headline numbers.**
- Fig. 1 (p. 5): misses normalised to WATT across 9 competitors × 5 traces × buffer ratios; WATT is
  best on average, though individual panels contain red (WATT worse) regions.
- Fig. 2 (p. 6): read/write trade-off. Raising `write_weight` cuts writes >10 % on TPC-C (20 % on
  TPC-E) for <15 % (7 %) more misses.
- Fig. 9 (p. 10): reads/writes per TX in LeanStore. vs WATT: LeanEvict +12 % reads (YCSB 100R),
  +26 % writes (YCSB 90R10W); Hyperbolic +5 % reads / +11 % writes; Random +11 % reads / +36 %
  writes. TPC-C 3200: LeanEvict +10 % reads / +19 % writes.
- Fig. 10 (p. 11): single-evictor throughput — WATT ≥ 2× LeanEvict's evictions/s, closing ~half the
  gap to Random; Hyperbolic slightly ahead of WATT.
- Fig. 11 (p. 11): per-TX cycles / instructions / L1 misses / branch misses of a *worker* thread are
  "at noise level" across the four policies (in-memory).
- Fig. 12 (p. 11): eviction scales to 32 evictor threads; only LeanEvict plateaus (~1 M/s).
- Fig. 13 (p. 12): end-to-end WATT +6 % TX/s over Hyperbolic on YCSB 90R10W, +7 % over
  LeanEvict/Hyperbolic on TPC-C; Random ≥22 % worse on TPC-C.

**Stated limitations / open ends.** `write_weight` is explicitly device- and workload-dependent
("Because write costs depend on the used hardware and workload…", §4.3) yet fixed at 4. Scalability
(§6.4) is measured with workers and evictors run **in separate phases** ("it is difficult to
evaluate the scalability of a single software component without influences from the others"), i.e.
interference is deliberately excluded. WATT has the largest metadata footprint of all compared
policies (50 B/page, 1.2 % at 4 KB pages, §3.2 table).

## 2. Artifact audit

### 2.1 What was cloned vs. what the artifact is

The paper's artifact statement (p. 1) is **https://github.com/leanstore/leanstore/tree/WATT** — the
`WATT` *branch*. The driver's shallow clone in `repo/` is the **default branch `master`**
(`repo/.git/packed-refs` contains only `refs/remotes/origin/master` @ `90fcf185`, dated
2025-09-11). `master` contains **no WATT code at all** — a grep for `WATT|watt|Watt` over `repo/`
returns no matches, and `repo/backend/leanstore/storage/buffer-manager/BufferFrame.hpp` has only the
LeanEvict `HOT/COOL/FREE/LOADED` state machine plus a `ContentionTracker` (lines 19–43), while
`repo/backend/leanstore/storage/buffer-manager/PageProviderThread.cpp` implements the classic
LeanEvict three-phase cool/evict/flush loop. `repo/README.md` lists other paper branches (`io`,
`blob`, `latency`, `mvcc`, `btw`, `cidr`) but **does not mention WATT**.

The branch does exist upstream (GitHub API `/branches`: `WATT` @ `8140750f…`), its head commit is
dated **2023-09-27** and authored by **Demian Vöhringer <demian.voehringer@fau.de>**, the paper's
first author ("add VLDB presentation, transcript and video"). So the artifact is genuine and
official; the *clone* is simply on the wrong ref. A team must
`git clone -b WATT https://github.com/leanstore/leanstore`.

### 2.2 The artifact ecosystem

| piece | URL | role | state |
|---|---|---|---|
| `leanstore@WATT` | github.com/leanstore/leanstore/tree/WATT | WATT inside LeanStore (system results, §5–§6) | last commit 2023-09-27, MIT |
| `itodnerd/WATT-simulate` | github.com/itodnerd/WATT-simulate | the §4 simulator, 10+ policies | last push 2025-06-30, MIT, default branch `main` |
| `itodnerd/WATT-traces` | github.com/itodnerd/WATT-traces | the 5 traces of Table 2 | Git-LFS, `WATT_competition_traces/{TPC_C,TPC_E,ZipfRO,dynZipfRO,dynZipfRW}/trace.csv` (TPC_C = 11.2 MB) |
| `itodnerd/WATT-Overview` | github.com/itodnerd/WATT-Overview | hub linking all of the above + VLDB'23 slides/video | — |

The `WATT` branch README points at the Overview repo and names the two implementation sites
("tracking mechanism within the BufferFrame", "replacement logic in the Page Evictor").

### 2.3 Paper component → code map (paths are on the `WATT` branch; all of them also exist by the
same name in the cloned `master` tree, which is what makes them usable as anchor points)

| paper | code |
|---|---|
| §3.1/§5.1 `PageTracker`, `accessLog[8]`/`writeLog[4]`, `accessHead`, `track()` (Listing 1) | `backend/leanstore/storage/buffer-manager/BufferFrame.hpp` — `struct alignas(64) Tracker { std::atomic<WATT_TIME> reads[kr], writes[kw]; std::atomic<u8> readPos, writePos; trackRead(); trackWrite(); merge(); getValue(); }`, `static const u8 kr = 8, kw = 4;`, `static std::atomic<WATT_TIME> globalTrackerTime;`, and `Tracker tracker = Tracker();` inside `BufferFrame::Header` |
| Eq. 3 `write_weight` | same file: `return readFreq + writeFreq * FLAGS_write_costs;` inside `getValue()` |
| Listing 3, AVX2 page value | same file: `simd_getFreq(...)` using `U8/F8` AVX2 wrappers, `table_8[pos] / table_4[pos]` (the `iQuotient` lookup table), `_mm256_min_ps(div, one)` |
| Listing 2, sampling + threshold + epoch bump | `backend/leanstore/storage/buffer-manager/PageProviderThread.cpp` — `findThreshold(int samples)` (`calculated_min = (min + next_min)/2.0`), batch prefetch loop `for (u32 j=0;j<batch;j++){ frames[j]=getNextBufferFrame(myPartition); __builtin_prefetch(frames[j]); }`, and `BufferFrame::globalTrackerTime++` |
| §3.2 epoch size / sample size / write weight knobs | `backend/leanstore/Config.cpp` — `DEFINE_uint32(watt_samples, 50, "How much samples for picking a page")`, `DEFINE_uint32(epoch_size, 1000, "size of epoch: ram/epoch_size")`, `DEFINE_uint32(write_costs, 1, "how much does one write should costs more then a read")`, `DEFINE_bool(watt_history, false, "Use watt history?")`, `DEFINE_uint32(watt_log_size, 0, "what is the largest expected page_id")` |
| (not in the paper) evicted-page history | `BufferFrame.hpp` — `struct Tracker_store` (non-atomic, serialisable) and `struct WATT_LOG { std::vector<Tracker_store> pid_trackers; store(PID,…); load(PID,…); }` plus `static WATT_LOG watt_backlog;`, gated by `FLAGS_watt_history` |
| async dirty write-back (§5.2, "ACE-like") | `backend/leanstore/storage/buffer-manager/AsyncWriteBuffer.cpp/.hpp` (libaio) |
| §6 workloads | `frontend/ycsb/ycsb.cpp`, `frontend/tpc-c/tpcc.cpp` (+ `TPCCWorkload.hpp`) |
| §4 simulator, 10 policies | `WATT-simulate/algos/` — `lru.hpp`, `lru_k.hpp`, `lru_wsr.hpp`, `cf_lru.hpp`, `ARC.hpp`, `CLOCK.hpp`, `hyperbolic.hpp`, `lean_evict.hpp`, `random.hpp`, `WATT.cpp/.hpp`; plus *post-paper* additions `sieve.hpp`, `opt.hpp`, `staticOpt.cpp`, `LRFU.cpp`, `lruStackDist.cpp` |
| §4 sweeps for Fig. 3–8 | `WATT-simulate/evalAccessTable/evalAccessTable.cpp` (33 KB) — hard-coded sweeps: `randSize` 1…64, `KR` 1…64+max, epochs {1,2,4,8,16,32,64,128,max}, dampening 0…100 step 5, aggregation `{mod_min,mod_avg,mod_median,mod_max,mod_lucas}`, `KW` 1…64+max, write cost 0…200 step 5 |

### 2.4 Build route on *this* machine

- **Language/build**: pure C++20 + CMake (`repo/CMakeLists.txt` sets `CMAKE_CXX_STANDARD 20`,
  `-mavx2 -mcx16 -m64`). gcc 12.2 and cmake 3.25 on the machine are sufficient; AVX2 is present on
  Zen 3 (AVX-512 is *not* needed — `btree_hints` AVX512 mode is opt-in via
  `DEFINE_int64(btree_hints, 1, "0: disabled 1: serial 1: AVX512")`).
- **Vendored deps** are fetched by CMake `ExternalProject_Add` from GitHub at configure time
  (`repo/libs/gflags.cmake`, `tabluate.cmake`, `rapidjson.cmake`) — network is available, no root.
- **System deps**: `repo/backend/CMakeLists.txt:25` links `gflags Threads::Threads aio tbb atomic
  tabluate rapidjson`. The README's `sudo apt-get install …` line is *not* a blocker: `libaio` is a
  ~5-file library that builds with `make prefix=$HOME/local install`, and TBB is available in
  conda-forge. Point CMake at them with `CMAKE_PREFIX_PATH`/`LDFLAGS`.
- **Gotcha**: `frontend/CMakeLists.txt` on the WATT branch still defines a `rocksdb_tpcc` target
  linking `rocksdb … zstd uring`. A bare `make -j` will fail; build `make -j ycsb tpcc` (or delete
  that block). Master's `frontend/CMakeLists.txt` is worse (RocksDB + WiredTiger + LMDB targets).
- **Storage**: `repo/backend/leanstore/LeanStore.cpp:60` opens `--ssd_path` with
  `O_RDWR | O_DIRECT`. A regular file on the ext4 `/home` works; no block device and no root needed.
  `repo/backend/leanstore/storage/buffer-manager/BufferManager.cpp:41–50` uses anonymous `mmap` +
  `madvise(MADV_HUGEPAGE|MADV_DONTFORK)` — THP `madvise` hints are advisory and need no root, no
  explicit hugepage reservation.
- **perf counters**: `repo/shared-headers/PerfEvent.hpp:100` calls `perf_event_open`, and
  `DEFINE_bool(cpu_counters, true, …)` (`repo/backend/leanstore/Config.cpp:25`) enables it by
  default. On this machine `perf_event_paranoid=3` makes the syscall fail — **but the code degrades
  gracefully**: `PerfEvent.hpp:101–106` prints "Error opening counter" and does
  `events.resize(0); names.resize(0); return;`. Counters then report 0. Run with
  `--cpu_counters=false`. Consequence: **Figure 11 (cycles / instructions / L1 / branch misses per
  TX) cannot be reproduced** on this machine.
- **root-only path**: `BufferManager.cpp:90` calls `setpriority(PRIO_PROCESS, 0, -20)` only
  `if (FLAGS_root)`, and `DEFINE_bool(root, false, …)` defaults to off. Fine.
- **Simulator**: `cmake && make`, needs Boost only for the `Boost_Test/` targets. Traces need
  **git-lfs** (`WATT_competition_traces/.gitattributes` = `.csv filter=lfs diff=lfs merge=lfs
  -text`); the git-lfs release tarball unpacks into `$HOME` without root. Trace format is
  `pages,is_write` per line (asserted in `evalAccessTable.cpp`); output is a CSV of
  `algorithm, ram_size, elements, reads, writes`.

### 2.5 Eval scripts present / absent

Present: the full simulator driver with every Fig. 3–8 parameter sweep hard-coded, and the two
LeanStore benchmark binaries with all §6 flags. Absent: **any plotting scripts and any run
scripts/Makefile that pin the §6 command lines** — the buffer-pool/thread/warehouse settings must be
re-derived from §6.1 and the README example command lines. The WATT branch README's example is a
TPC-C invocation only.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper p. 1 "PVLDB Artifact Availability: … https://github.com/leanstore/leanstore/tree/WATT". The branch exists (GitHub API `/repos/leanstore/leanstore/branches` → `WATT` @ `8140750f…`), head commit 2023-09-27 by the first author Demian Vöhringer, MIT-licensed, and contains the real implementation (`backend/leanstore/storage/buffer-manager/BufferFrame.hpp` holds `struct Tracker` with `reads[kr]/writes[kw]`, SIMD `getValue()`; `PageProviderThread.cpp` holds `findThreshold()` + `globalTrackerTime++`). The simulator and traces are separate official repos linked from that branch's README via `itodnerd/WATT-Overview`. **Caveat, not a fail:** the clone in `repo/` is the `master` branch and contains **zero** WATT code (`repo/.git/packed-refs` has only `origin/master`; grep for `WATT` in `repo/` = no matches) — use `-b WATT`. |
| `H2_no_root` | **pass** | Pure user-space C++: buffer pool is anonymous `mmap` (`repo/backend/leanstore/storage/buffer-manager/BufferManager.cpp:41`), I/O is `O_DIRECT` + libaio on a plain file (`repo/backend/leanstore/LeanStore.cpp:60`, `AsyncWriteBuffer.cpp`). No kernel module, eBPF, KVM, RDMA or `/proc/sys` writes anywhere in the tree. `repo_facts.json` red flags are (a) `sudo apt-get` lines in README/CI, which are ordinary dev deps replayable with conda/source, and (b) `shared-headers/PerfEvent.hpp:100` `perf_event_open`, which **fails soft** (`PerfEvent.hpp:101–106` clears the counter list) and is switchable off with `--cpu_counters=false`. The only root path, `setpriority(-20)`, is behind `DEFINE_bool(root, false, …)` (`repo/backend/leanstore/Config.cpp:29`). Cost: Figure 11 (hardware-counter figure) is out of reach. |
| `H3_hardware_fit` | **pass** | CPU-only, no GPU. §4's simulation runs at *full paper scale* on one core (traces are 1–2 M accesses over ≤66 k pages, `WATT-traces` TPC_C trace.csv = 11.2 MB). §6's system experiments need scale-down: the paper used 512 GB RAM / 64 c / 3.8 TB SSD with 400 GB YCSB and 264–588 GB TPC-C (§6.1), while this machine has 125 GB RAM, 16 c / 32 t and ~257 GB free. The mechanism is a *ratio* effect (buffer pool ÷ dataset, swept 1–100 % in Fig. 1), so e.g. 2 GB buffer pool over a 100 GB YCSB dataset (2 %, exactly the paper's 8/400 GB ratio) with 24 workers and 1–8 evictors reproduces the same regime. TPC-C 3200 wh (588 GB) is impossible; ~400 wh (~66 GB) is. Fig. 12's 32-evictor point cannot be run honestly (16 physical cores). |
| `H4_obtainable_deps_data` | **pass** | Deps: gflags/tabulate/rapidjson auto-fetched by CMake (`repo/libs/gflags.cmake` ExternalProject from github.com); `aio`, `tbb`, `atomic` (`repo/backend/CMakeLists.txt:25`) — TBB from conda-forge, libaio buildable into `$HOME`. Data: all five §4 traces are public in `itodnerd/WATT-traces` (Git-LFS, ~12 MB repo); YCSB and TPC-C datasets are **generated in-process** by `frontend/ycsb/ycsb.cpp` and `frontend/tpc-c/tpcc.cpp` — no proprietary trace anywhere. No model weights, no gated downloads. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Primary target: Figure 1 (p. 5) + Figure 2 (p. 6)** — "WATT has the best replacement
effectiveness on average across 9 competitors × 5 traces × buffer-pool ratios" (§4.2), and "WATT
trades >10 % of TPC-C writes for <15 % more misses via `write_weight`". This is the paper's Goal-1 /
Goal-2 claim and the basis for everything in §6.

**Scale-down:** none needed. The traces are 1–2 M accesses over 10 k–66 k pages; a full sweep of
10 policies × 5 traces × ~20 buffer ratios is minutes-to-hours of single-core work and embarrassingly
parallel over 32 threads.

**Steps.**
1. `git clone https://github.com/itodnerd/WATT-simulate` (branch `main`); install git-lfs into
   `$HOME`; `git clone https://github.com/itodnerd/WATT-traces` and `git lfs pull`.
2. `mkdir build && cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo .. && make -j` (Boost only needed for
   `Boost_Test/`; disable if it fights conda).
3. `./evalAccessTable <trace.csv> <outdir>` for each of the five traces; the buffer-size sweep and
   the default parameter set live in `evalAccessTable/evalAccessTable.cpp`.
4. Normalise every policy's miss count by WATT's, per (trace, ram_size) — that is exactly Fig. 1's
   y-axis. Re-plot in Python (no plotting scripts shipped).
5. For Fig. 2, sweep `write cost` (the code already sweeps 0…200 step 5) on TPC-C/TPC-E at the
   fixed RAM size and plot misses-relative vs writes-relative.

**Secondary target: Figure 9 (p. 10)** — reads/writes per TX in LeanStore, WATT vs LeanEvict vs
Hyperbolic vs Random. Steps: `git clone -b WATT …/leanstore`; build libaio+TBB into `$HOME`;
`make -j ycsb tpcc` (skip `rocksdb_tpcc`); create a 120 GB backing file on `/home`; run
`ycsb --ssd_path=… --target_gib=100 --dram_gib=2 --worker_threads=24 --pp_threads=4
--ycsb_read_ratio={100,90} --run_for_seconds=1200 --cpu_counters=false --csv_path=…` for each
policy (the WATT branch selects the policy at build/flag level — check
`PageProviderThread.cpp`/`Config.cpp` for the switch), then the same for TPC-C at ~400 warehouses.
Read `log_bm.csv` for reads/writes per TX.

**Effort.** Fig. 1 + Fig. 2: ~3 person-days + ~20–40 CPU-hours (mostly the parameter sweeps, which
parallelise). Fig. 9 scaled down: +5–7 person-days (build porting, dataset generation, 4 policies ×
2 workloads × 20 min × 2 reps ≈ 6 machine-hours for YCSB, similar for TPC-C, plus ~2 h per dataset
regeneration).

**Level: H.** The simulator is a self-contained CMake program whose configurations for Figures 1–8
are hard-coded in `evalAccessTable.cpp`, the traces are public and tiny, dependencies are a 2025-era
C++/CMake/Boost stack, and the whole thing fits at *paper scale* on this machine. The only friction
is absent plotting scripts and the git-lfs fetch. (The LeanStore half alone would be **M**: real
porting work — wrong branch cloned, libaio/TBB from source, a broken `rocksdb_tpcc` target, no run
scripts, and a mandatory dataset/thread scale-down.)

## 5. Add-on ideas

### A1 — Self-tuning write weight

**Hypothesis.** We hypothesize that replacing WATT's fixed `write_weight` with a closed-loop
controller that sets it from *measured* device read/write service times and the current dirty-page
backlog improves end-to-end TX/s (and reduces host write volume at equal throughput) under workloads
whose write intensity changes over time (YCSB switching between 100R and 70R/30W phases, TPC-C with
a growing dataset), compared with the paper's `write_costs = 4`.

**Mechanism.** Instrument `AsyncWriteBuffer` to maintain an EWMA of per-page write completion
latency and of `pread` completion latency, plus the evictor's stall time waiting for the write
buffer. Once per epoch (the existing `globalTrackerTime++` site in the evictor loop), update
`write_costs` by a bounded multiplicative step in the direction that reduces estimated total I/O
service time per eviction (or, in "endurance mode", drives measured host writes/s toward a
configured budget). `getValue()` already multiplies `writeFreq` by `FLAGS_write_costs`, so the only
data-plane change is making that a relaxed-atomic double instead of a gflag read.

**code_locations.** `backend/leanstore/storage/buffer-manager/BufferFrame.hpp` (the
`return readFreq + writeFreq * FLAGS_write_costs;` in `Tracker::getValue()`),
`backend/leanstore/storage/buffer-manager/PageProviderThread.cpp` (epoch-advance site; controller
tick), `backend/leanstore/storage/buffer-manager/AsyncWriteBuffer.cpp` (latency/throughput
measurement), `backend/leanstore/Config.cpp` (`write_costs` → adaptive mode flag),
`frontend/ycsb/ycsb.cpp` (phase-changing read/write-ratio workload).

**motivating_evidence.** §4.3: "Because write costs depend on the used hardware and workload, the
page value function of WATT includes a `write_weight` parameter" — yet the default is a single
constant 4 picked from Fig. 8, and Fig. 8 shows total I/O is non-monotonic in `write_weight` with
the optimum differing per workload (TPC-C, TPC-E, dynZipfRW curves). §6 never varies it at all.

**feasibility: H.** Localized: one expression in `getValue()`, a controller of a few dozen lines in
the evictor, and counters in `AsyncWriteBuffer`. Well under 1k LOC. Evaluable with the existing
YCSB/TPC-C frontends at the scale-down of §4, and cheaply pre-screened in `WATT-simulate` (which
already sweeps write cost 0…200).

**research_value: M.** Removes the paper's one admitted hardware/workload-dependent knob and targets
SSD endurance, which reviewers care about — but cost-aware *self-adaptive* buffer replacement is a
known family, so the novelty is the setting (sampling-based, many-core, NVMe, measured rather than
assumed cost ratio) rather than the idea.

**scoop_check: partial.** Queries: "self-tuning adaptive write penalty cost-aware buffer replacement
flash database 2024 2025"; Semantic Scholar citation list of DOI 10.14778/3611479.3611529. Closest
prior work is the CASA / [ACR](https://www.researchgate.net/publication/221422739_ACR_An_Adaptive_Cost-Aware_Buffer_Replacement_Algorithm_for_Flash_Storage_Devices) /
[FD-Buffer](https://www.researchgate.net/publication/264561687_FD-Buffer_A_Cost-Based_Adaptive_Buffer_Replacement_Algorithm_for_Flash_Memory_Devices)
line (2010–2015, embedded-flash era, LRU-list based, single-threaded) — none of which WATT cites and
none of which touch a sampling-based many-core buffer manager. No paper in WATT's 11-paper citation
list does this.

---

### A2 — Decoupling the epoch clock from the eviction rate

**Hypothesis.** We hypothesize that advancing `globalTrackerTime` on `min(evictions,
buffer-pool accesses, wall-clock)` rather than on evictions alone reduces misses after a workload
phase change, under workloads that alternate between an in-memory phase (eviction stalls, clock
freezes) and an out-of-memory phase, compared with the paper's eviction-driven epoch clock.

**Mechanism.** Today `globalTrackerTime++` fires only inside the page-evictor loop after
`cacheSize/epoch_size` evictions (Listing 2 step 3; `FLAGS_epoch_size`). When the working set
temporarily fits in RAM the evictor sleeps, the clock stops, and every page's `t_now − t_i` freezes —
so on resumption a page last touched at the start of the quiet period scores identically to one
touched at the end. Add a second, cheap clock source: a per-worker access counter aggregated into a
padded shared counter (or a coarse `CLOCK_MONOTONIC_COARSE` read on the evictor's wake-up path) that
can also advance the epoch, with the epoch rate capped so the cache-line-ping-pong argument of §5.1
still holds. Measure the ping-pong cost directly (it is the reason epochs exist).

**code_locations.** `backend/leanstore/storage/buffer-manager/PageProviderThread.cpp`
(`BufferFrame::globalTrackerTime++` site and the evictor sleep/wake path),
`backend/leanstore/storage/buffer-manager/BufferFrame.hpp` (`globalTrackerTime`, `Tracker::trackRead`
early-out `if (now != reads[pos])`), `backend/leanstore/storage/buffer-manager/BufferManager.cpp`
(evictor startup / free-list thresholds), `backend/leanstore/Config.cpp` (`epoch_size`),
`frontend/ycsb/ycsb.cpp` (phase-alternating workload driver).

**motivating_evidence.** §3.2 "An approach we found to work well is to couple the growth of `t_now`
to the number of pages replaced" — and Fig. 5 only sweeps *how many* epochs per full replacement,
never the *source* of the clock. §5.1 justifies epochs purely by contention. Neither the simulation
(which replays a trace with no idle time) nor §6 (steady-state 20-minute runs at a fixed 8 GB buffer
pool) ever exercises a stalled-eviction phase, so this assumption is untested.

**feasibility: H.** A counter plus a few lines in the evictor loop; the existing YCSB frontend needs
a phase script (change `dram_gib`-relative working set or read ratio mid-run). Cheaply pre-screened
in `WATT-simulate` by injecting idle gaps into the traces. Fits the existing harness.

**research_value: M.** Attacks a core, undocumented design assumption, and either outcome is
informative (if the eviction-driven clock is robust to stalls, that is itself a useful finding about
why WATT works). Not a headline-grabbing result, but a real gap in the paper's parameter study.

**scoop_check: clear.** Queries: Semantic Scholar citations of the WATT DOI (11 citing papers, none
about epoch/clock design); "epoch clock page replacement buffer manager eviction rate coupled";
"Sampling-based Predictive Database Buffer Management" (VLDB'25, scan-prediction based — orthogonal).
Nothing found that revisits WATT's clock source.

---

### A3 — Write-aware quick-demotion: WATT vs S3-FIFO/SIEVE in a real buffer manager

**Hypothesis.** We hypothesize that a *write-aware* quick-demotion policy (S3-FIFO-style small/main
FIFO queues, sharded per partition, with a dirty-page penalty applied at demotion) matches or beats
WATT's miss+write counts on the paper's five traces and on YCSB/TPC-C in LeanStore, while using
≤2 B/page of metadata instead of WATT's 50 B/page, under out-of-memory OLTP workloads.

**Mechanism.** (i) In the simulator, add `s3fifo.hpp` next to the existing `sieve.hpp`, with a
`write_cost` parameter that, on demotion from the small queue, re-inserts dirty pages once (a
write-aware analogue of WATT's Eq. 3). Sweep exactly the grid `evalAccessTable.cpp` already uses.
(ii) In LeanStore, implement the winner inside the page-evictor: replace the sample-and-threshold
step with per-partition ring buffers of frame pointers (LeanStore already shards frames into
`1 << partition_bits` partitions, so the "FIFO queues don't scale" objection of §1 Goal 4 can be
tested rather than assumed) and shrink `BufferFrame::Header::Tracker` to a 2-bit frequency counter +
dirty bit. (iii) Report misses, writes, evictions/s, TX/s and metadata bytes/page side by side.

**code_locations.** `backend/leanstore/storage/buffer-manager/PageProviderThread.cpp` (eviction
path: `findThreshold` + sampling loop → queue-based victim selection),
`backend/leanstore/storage/buffer-manager/BufferFrame.hpp` (`Tracker` → compact counter),
`backend/leanstore/storage/buffer-manager/Partition.hpp` (per-partition queue state),
`backend/leanstore/storage/buffer-manager/BufferManager.cpp` (frame→partition mapping, evictor
wiring), `backend/leanstore/Config.cpp` (policy-selection flag).

**motivating_evidence.** WATT's competitor set (Table 1) is entirely pre-2018; S3-FIFO (SOSP'23) and
SIEVE (NSDI'24) appeared essentially concurrently and claim ARC-beating effectiveness with ~1 bit of
metadata and no list-head contention — directly contesting WATT's central premise that "storing more
information should lead to more accurate page replacement" (§3). WATT pays the highest metadata cost
in the paper's own table (50 B/page, 1.2 %, §3.2) and the second-slowest evictor in Fig. 10
(Hyperbolic is faster). The authors themselves added `sieve.hpp` to `WATT-simulate` *after*
publication, i.e. they consider the comparison open. Fig. 1 also shows panels where competitors beat
WATT.

**feasibility: M.** The simulator half is easy (drop-in `algos/` file, existing sweeps). The
LeanStore half is cross-cutting: it replaces the victim-selection path, touches the frame header
layout, and needs its own correctness shakeout under optimistic latching — realistic for 2–4
students in 10 weeks, but it is the bulk of the project, and the TX/s comparison needs the full
scaled-down §6 harness (which does not ship as scripts).

**research_value: H.** A VLDB reviewer would care: it tests whether WATT's rich per-page history
earns its 50 B under a fair, modern baseline, and it produces the first write-aware variant of
quick-demotion caching for a DBMS buffer pool. Both outcomes are publishable — "WATT still wins, and
here is why history beats quick demotion on OLTP page traces" is as interesting as the converse.

**scoop_check: partial.** Queries: "write-aware S3-FIFO flash SSD buffer pool eviction dirty page
penalty"; Semantic Scholar citations of the WATT DOI; "SIEVE database buffer manager write aware".
Found [ECR: eviction-cost-aware cache management for page-level flash SSDs](https://onlinelibrary.wiley.com/doi/10.1002/cpe.5395)
(2021, chip-queue-latency aware, LRU family) and
[S3-FIFO](https://s3fifo.com/blog/2023/08/01/fifo-queues-are-all-you-need-for-cache-eviction/)
itself (key-value caches, write-oblivious, no DBMS buffer pool). No work combining quick demotion
with a write penalty in a DBMS buffer manager, and none benchmarking S3-FIFO/SIEVE against WATT.

---

### A4 — Bounded ghost trackers for evicted pages

**Hypothesis.** We hypothesize that retaining a *memory-bounded* ghost history of the WATT tracker of
recently evicted pages (≤2 % of buffer-pool bytes) reduces read misses by a measurable margin under
small buffer-pool ratios (1–10 % of dataset) and shifting-hot-set workloads (dynZipfRO, TPC-C),
compared with WATT's stateless re-admission, and captures most of the benefit of the unbounded
history already present but unevaluated in the artifact.

**Mechanism.** The WATT branch already contains `struct Tracker_store` and
`struct WATT_LOG { std::vector<Tracker_store> pid_trackers; store(PID, const Tracker&);
load(PID, Tracker&); }` with a `static WATT_LOG watt_backlog;` behind `FLAGS_watt_history` (default
`false`) and `FLAGS_watt_log_size` ("what is the largest expected page_id") — i.e. an **O(dataset)**
array, which is why it is unusable in practice and, presumably, why no figure reports it. Replace it
with a fixed-capacity sharded open-addressing table of `(PID, Tracker_store)` with CLOCK/FIFO
eviction of ghost entries, sized as a fraction of the buffer pool; restore the tracker on page-in and
store it on evict; age ghost timestamps against the current epoch so stale ghosts decay. Sweep ghost
capacity 0 / 0.5 / 1 / 2 / 5 / ∞ % and report misses, writes and memory.

**code_locations.** `backend/leanstore/storage/buffer-manager/BufferFrame.hpp` (`Tracker_store`,
`WATT_LOG`, `watt_backlog`), `backend/leanstore/storage/buffer-manager/BufferManager.cpp` (page-in
path where a freed frame is reused — where `load()` must be called),
`backend/leanstore/storage/buffer-manager/PageProviderThread.cpp` (evict path — where `store()` must
be called, and `BufferFrame::reset()` clears the tracker),
`backend/leanstore/Config.cpp` (`watt_history`, `watt_log_size` → capacity flag),
`frontend/tpc-c/tpcc.cpp` (shifting-working-set workload).

**motivating_evidence.** §3.2 bounds history *per resident page* but the paper never discusses what
happens on eviction: a page that is read back starts with an empty log, so in the §6 regime
(8 GB pool over a 400 GB dataset, i.e. 2 %) almost every access is to a page with no history — which
undercuts the paper's own thesis that "storing more information should lead to more accurate page
replacement" (§3). ARC, which does keep ghost lists, is the strongest competitor in Fig. 1 and beats
WATT in several panels. And the artifact's own unevaluated `FLAGS_watt_history` shows the authors
considered it and stopped at an O(dataset) prototype.

**feasibility: H.** The data structure and both call sites already exist in skeleton form; the work
is bounding memory, adding ghost eviction, and wiring `load()`/`store()` into the page-in/evict
paths. A few hundred LOC. Pre-screenable in `WATT-simulate` (which already implements ghost-list
policies in `ARC.hpp`). Uses the existing frontends.

**research_value: M.** It closes a genuine gap between the paper's thesis and its implementation, and
the result is not obvious (ghost entries cost bytes that could have held real pages — the classic
ARC trade-off, here at 4 KB pages where the ratio is very different from web caches). But "add ghost
lists" is a well-trodden mechanism, so a reviewer would call it solid rather than surprising.

**scoop_check: partial.** Queries: "ghost list evicted page history sampling-based eviction
hyperbolic caching 2024 2025"; Semantic Scholar citations of the WATT DOI. Ghost lists are standard
(ARC, FAST'03; 2Q) and there are patents on ghost-list adjustment factors, but nothing applies them
to *sampled, timestamp-log* page values or evaluates a bounded ghost tracker in a DBMS buffer pool.
The closest citing work, [Sampling-based Predictive Database Buffer Management](https://cs.uwaterloo.ca/~r9guo/publication/pbm.html)
(PVLDB 18(13), 2025), is sampling-based but predicts *future* accesses from long-running scans rather
than retaining *past* history — related, not the same.

---

### Rejected idea, for the record

An "NVMe-aware grouped write-back / out-of-place placement to cut device write amplification" add-on
(the natural reading of Goal 2, since the paper only ever measures *host* write volume, never device
WAF, and `FLAGS_out_of_place` sits unevaluated in the code) is **scooped**:
[*How to Write to SSDs*, Lee, Ziegler & Leis, PVLDB 19(7):1469–1483, 2026](https://www.vldb.org/pvldb/vol19/p1469-lee.pdf)
([arXiv 2603.09927](https://arxiv.org/abs/2603.09927), artifact
[LeeBohyun/ZLeanStore](https://github.com/LeeBohyun/ZLeanStore)) redesigns exactly this LeanStore to
write out-of-place, reporting 1.65–2.24× throughput and 6.2–9.8× fewer flash writes on YCSB-A. It
also cites WATT. Additionally, device-level WAF cannot be measured on this machine (`nvme smart-log`
needs privileged access to `/dev/nvme*`).

## 6. Risks and open questions

1. **Wrong branch cloned.** `repo/` is `master`, which contains no WATT code. Everything in §5
   assumes `git clone -b WATT`. The file *names* used as `code_locations` exist in both trees, but
   their *contents* on `master` are the LeanEvict implementation, not WATT. Anyone acting on this
   report must re-clone first.
2. **Artifact is frozen at 2023-09-27** and forked from the *pointer-swizzling* LeanStore, which
   upstream has since replaced with the vmcache design (PVLDB'24, `repo/README.md:55`). The WATT
   branch will never receive upstream fixes, and porting WATT to modern LeanStore is itself a
   project. Conversely, this makes the code stable and easy to reason about.
3. **No hardware counters.** `perf_event_paranoid=3` ⇒ Figure 11 is unreproducible; CPU-efficiency
   claims (Goal 3) can only be checked via evictions/s (Fig. 10) and wall-clock TX/s (Fig. 13), not
   via cycles/instructions per TX.
4. **Core count.** 16 physical cores vs the paper's 64. Fig. 12 sweeps up to 32 evictor threads and
   Fig. 9/13 use 120 workers; on this machine the scalability claim (Goal 4) can only be tested to
   ~16 threads, and the worker:evictor ratio that makes eviction the bottleneck differs. Any
   scalability result must be presented as a 16-core restatement, not a reproduction.
5. **Disk budget.** ~257 GB free. TPC-C 3200 wh (588 GB) and 1600 wh (264 GB) are both out; YCSB
   400 GB is out. The buffer/dataset *ratio* can be preserved, but absolute-scale effects (SSD
   internal GC, queue depth at 1M IOPS) cannot.
6. **Shared machine.** 111 of 125 GiB RAM were free at measurement time and the NVMe pair is shared.
   Out-of-memory storage-engine benchmarks are extremely sensitive to co-tenant I/O; runs need
   repetition and interleaving, and the paper's median-of-2400-samples methodology (§6.2) should be
   copied.
7. **No run/plot scripts.** §6's exact flag sets are not in the repo; they must be reconstructed from
   §6.1 prose and the README example. Expect a day of guessing the policy-selection mechanism on the
   WATT branch (flag vs compile-time switch — this could not be settled by desk review).
8. **Git-LFS.** The traces are LFS pointers; `git lfs` must be installed into `$HOME`. If LFS
   bandwidth quota on the account is exhausted the traces become unfetchable — mitigation: the
   Zipf traces can be regenerated from §4.1's description, but TPC-C/TPC-E traces (Shore-MT
   instrumentation) cannot.
9. **Same-group scoop pressure.** The Leis group is actively publishing on LeanStore buffer
   management (PVLDB'24 LeanStore/vmcache; *How to Write to SSDs* PVLDB'26; *Predictive Translation*
   SIGMOD'26). Any add-on in the write-path or page-translation area risks being overtaken; A2/A3/A4
   were chosen partly because they sit outside those lines.
10. **`getValue()` detail not fully resolved by desk review.** The WATT branch's SIMD path contains
    `_mm256_min_ps(div, one)`, i.e. subfrequencies are clamped at 1 — a detail not present in the
    paper's Eq. 1/Listing 3. Its effect on the reported numbers is unknown and should be checked
    before any claim of "reproduced".

## 7. Evidence index

**Paper.**
- p. 1 §1 Goals 1–4; PVLDB Artifact Availability statement (`…/leanstore/tree/WATT`).
- p. 2 §2.1 LeanEvict description; §2.2 Hyperbolic/CFLRU/LRU_WSR.
- p. 3 Table 1 (10 policies × 4 goals); §3.1 Eq. 1 (subfrequency), Eq. 2 (max aggregation).
- p. 4 §3.2 sampling & lazy evaluation; Eq. 3 `write_weight`; epoch bounding + memory-overhead table
  (WATT = 50 B/page, 1.2 %); Table 2 workload statistics.
- p. 5 **Figure 1** (replacement algorithm comparison, read from `pages/page-05.png`); §4.1 trace
  construction; §4.2.
- p. 6 **Figure 2** (read/write trade-off); §4.3 parameter table (untuned vs tuned); Figures 3–8.
- p. 7 §4.3 aggregation-function table; parameter-correlation note.
- p. 7–8 §5.1 Listing 1 (`PageTracker::track`), epochs & cache-line ping-pong, release stores.
- p. 8 §5.2 Listing 2 (3-step replacement, sample 8 → threshold → sample 64 → evict → epoch bump).
- p. 9 Listing 3 (AVX2 `PVaccess`, `iQuotient` table); §5.3 race analysis; §6.1 hardware &
  workloads (EPYC 7713, 512 GB, PM1733 3.8 TB; YCSB 25/400 GB; TPC-C 50/1600/3200 wh; 8 GB pool,
  120 workers).
- p. 10 **Figure 9** (reads/writes per TX, read from `pages/page-10.png`); §6.2 per-workload deltas.
- p. 11 Figures 10–12 (evictions/s, hardware counters per TX, scalability to 32 evictors); §6.4
  "measuring the multi-core scalability of page eviction in isolation".
- p. 12 Figure 13 (overall TX/s); §7 summary.

**Cloned repository (`repo/`, branch `master` @ `90fcf185`, 2025-09-11).**
- `repo/.git/packed-refs` — only `refs/remotes/origin/master`.
- `repo/README.md` — lists paper branches; **no WATT entry**; `sudo apt-get install …` line 9;
  line 55 vmcache rewrite.
- `repo/CMakeLists.txt:13,18` — C++20, `-mavx2 -mcx16 -m64`.
- `repo/backend/CMakeLists.txt:25` — links `gflags Threads::Threads aio tbb atomic tabluate rapidjson`.
- `repo/frontend/CMakeLists.txt:9,17,37,48,58` — `ycsb`, `tpcc`, and the RocksDB/WiredTiger/LMDB
  targets that break a bare `make -j`.
- `repo/libs/gflags.cmake:9–21` — `ExternalProject_Add` from github.com (network at configure time).
- `repo/backend/leanstore/Config.cpp:3,7,24,25,29,75` — `dram_gib`, `pp_threads`, `worker_threads`,
  `cpu_counters=true`, `root=false`, `replacement_chunk_size`.
- `repo/backend/leanstore/LeanStore.cpp:60` — `O_RDWR | O_DIRECT`.
- `repo/backend/leanstore/storage/buffer-manager/BufferManager.cpp:41–50` — anonymous `mmap`,
  `MADV_HUGEPAGE`, `MADV_DONTFORK`; `:74–96` — page-provider thread startup, `FLAGS_root`
  `setpriority`.
- `repo/backend/leanstore/storage/buffer-manager/BufferFrame.hpp:19–43,84` — LeanEvict state machine,
  `ContentionTracker`, `isDirty()` (contrast with the WATT branch's `Tracker`).
- `repo/backend/leanstore/storage/buffer-manager/PageProviderThread.cpp:28–320` — LeanEvict 3-phase
  loop (cool / evict / poll async writes).
- `repo/shared-headers/PerfEvent.hpp:85–108` — `perf_event_open` and the graceful-degradation path.
- `repo/backend/leanstore/profiling/counters/CPUCounters.cpp:11–16` — per-thread `PerfEvent`.
- `repo/repo_facts.json` — 158 files, 1.0 MB, `.hpp` 12 972 + `.cpp` 10 768 LOC; red flags `sudo` (7)
  and `perf_counters` (1); GitHub 651 stars, MIT, not archived.

**Upstream (read via GitHub API / raw, desk review only).**
- `GET /repos/leanstore/leanstore/branches` — `WATT` @ `8140750f8ca6487c4165d5ecf6cfb28d3873d2aa`.
- `GET /repos/leanstore/leanstore/commits/WATT` — 2023-09-27, Demian Vöhringer.
- `raw…/WATT/backend/leanstore/storage/buffer-manager/BufferFrame.hpp` — `struct alignas(64) Tracker`,
  `kr = 8, kw = 4`, `globalTrackerTime`, `getValue()` with `FLAGS_write_costs`, `simd_getFreq`
  (`_mm256_min_ps`), `Tracker_store`, `WATT_LOG`, `watt_backlog`.
- `raw…/WATT/backend/leanstore/storage/buffer-manager/PageProviderThread.cpp` — `findThreshold(int
  samples)`, `__builtin_prefetch` batch of 100, `BufferFrame::globalTrackerTime++`, `FLAGS_epoch_size`,
  `FLAGS_watt_samples`, `FLAGS_watt_history`, `FLAGS_out_of_place`.
- `raw…/WATT/backend/leanstore/Config.cpp` — `watt_samples=50`, `epoch_size=1000`, `write_costs=1`,
  `watt_history=false`, `watt_log_size=0`, `cool_pct=10`.
- `raw…/WATT/frontend/CMakeLists.txt` — targets `frontend`, `ycsb`, `tpcc`, `min`, `rocksdb_tpcc`.
- `GET /repos/leanstore/leanstore/contents/{frontend,frontend/ycsb,frontend/tpc-c,backend/leanstore/storage/buffer-manager}?ref=WATT`
  — confirms every `code_locations` path exists on the artifact branch as well as in `repo/`.
- `github.com/itodnerd/WATT-Overview` — artifact hub (paper, video, code, simulator, traces).
- `github.com/itodnerd/WATT-simulate` — `algos/` (23 files incl. `WATT.cpp`, `ARC.hpp`,
  `hyperbolic.hpp`, `lean_evict.hpp`, `cf_lru.hpp`, `lru_wsr.hpp`, `sieve.hpp`, `opt.hpp`),
  `evalAccessTable/evalAccessTable.cpp` (sweeps, CSV output, trace header `pages,is_write`);
  pushed 2025-06-30, MIT.
- `github.com/itodnerd/WATT-traces` — `WATT_competition_traces/{TPC_C,TPC_E,ZipfRO,dynZipfRO,
  dynZipfRW}/trace.csv`, Git-LFS (`.gitattributes`: `.csv filter=lfs …`), TPC_C trace = 11 190 497 B.
- Semantic Scholar citation graph for DOI 10.14778/3611479.3611529 — 11 citing papers (used for
  scoop checks).
