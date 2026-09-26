# Symbiosis: The Art of Application and Kernel Cache Cooperation

FAST '24 — Yifan Dai, Jing Liu, Andrea Arpaci-Dusseau, Remzi Arpaci-Dusseau (UW–Madison).
Repository: https://github.com/daiyifandanny/Symbiosis (head commit 2023-12-16, pushed 2024-01-24).

## 1. Paper summary

**Problem.** Modern KV storage engines cache twice: an application-level cache of
*decompressed, deserialized* blocks, and the kernel page cache holding the *compressed*
on-disk form. The two share one memory budget `M = Ma + Mk`. How to split `M` is a
tuning nightmare: the paper's motivating experiment (§2.2, Figure 2, p.4) shows that on
LevelDB, `Ma = 1 GB` beats `Ma = 8 MB` by 2.5–3× when `Du = 1 GB`, and *loses* by up to
7× when `Du = 2 GB`.

**Offline study (§3, Figures 4 and 5).** A simpy-based simulator sweeps `Mk` over the
parameter space (`Du` 1–10 GB, compression ratio α 0.1–0.9, app miss cost `Ca` 10–100 µs,
`Ck` fixed 100 µs, uniform/skewed/read+scan workloads) using `Le = (1−Ha)·(Ca + (1−Hk)·Ck)`.
Findings: for *uniform* workloads the optimum is always at one of the two endpoints
(`Mk = 0` or `Mk = min(M, α·Du)`) and which one wins depends on every factor; for *skewed*
and *mixed read+scan* workloads (Figure 5, p.6) the optimum is interior and
"highly unpredictable". Gains over a bad static choice reach 9×. §3.3 concludes the
curves are smooth, so an approximate online simulator is viable.

**Design (§4, Figure 6, p.7).** Symbiosis is an in-engine module with two parts:
- **Tracker** continuously computes `Le` from observed app/kernel hit ratios and
  *statically configured* miss costs; a >10% change in `Le` triggers the *Adapting* state.
- **GhostSim** simulates 9 candidate `<Ma,Mk>` splits (`num_searches_ = 8` equal steps)
  with a single ghost cache, pipelined in order of increasing `Ma` to exploit the LRU
  stack property. Four optimisations: a **reset policy** (fall back to the engine's
  default `Ma` when `Le` worsened), **incremental ghost-cache reuse**, **misalignment-aware
  sampling** (group `G = 32` contiguous blocks before hashing; sample ratio `R = 1/64`)
  plus a read-ahead compensation heuristic (§4.2.3, Figure 7, p.7), and a **guardrail**
  that applies a new size only if the predicted gain exceeds a threshold.

**Stated limitations (§4.2.5).** Workloads are assumed to change infrequently; write-heavy
workloads "will require additional research" because compaction perturbs the cache access
trace. §6 names exclusive (duplication-free) app/kernel caching as future work.

**Implementation (§4.3).** ~1 000 LoC added to LevelDB (30 kLoC); <100 LoC to WiredTiger;
minimal effort for RocksDB (using its built-in compressed block cache + direct I/O instead
of the kernel cache). A WiredTiger eviction bug was found and worked around.

**Evaluation setup (§5, Table 1, p.9).** HW1 = Xeon 5128R 2.9 GHz + Optane SSD 900P
(~10 µs); HW2 = Xeon D-1548 2.0 GHz + Toshiba NVMe flash (~70 µs). `M` fixed at 1 GB by
cgroup. `Du ∈ {5, 2.5, 1.67, 1.25, 1} GB` (i.e. `M/Du` 0.2–1.0). Five YCSB access patterns
(uniform, zipfian, hotspot{30,20,10}). Baselines: `StaticMa=8MB` (LevelDB default) and
`StaticMa=1GB` (`Mk ≈ 0`).

**Headline numbers.**
- Figure 8 (p.10), 5 panels × 5 patterns × 5 `M/Du`: Symbiosis always matches the *better*
  static baseline and beats the worse one by up to 5.77×; it beats *both* by up to 1.32×
  (6.9% average gain over the better baseline on HW2, 11.1% at α = 0.22).
- Figure 12 (p.12), 18 two-phase dynamic workloads: 24% average gain over `StaticMa=8MB`,
  42% over `StaticMa=1GB`, best case 42% over the better of the two; convergence 15.4 s
  average / 40 s worst.
- Table 3 (p.13): with sampling + reuse, ghost cache costs 0.46 MB and 0.09 µs/op (1.3%);
  without sampling 51 MB and 42%.
- Table 2 (p.13): p99 tail-latency overhead 15.3% median, 52% worst.
- Figure 15 (p.14): 4-phase RocksDB `mix_graph` production-like trace — Symbiosis adopts
  3 of 4 size changes and correctly rejects the 4th.
- Figure 9 (p.10): with 20% overwrites the benefit largely evaporates; 9(b) shows the
  hit-rate prediction error grows with compaction throughput.

## 2. Artifact audit

### Repository layout (top level)

| path | what |
|---|---|
| `ae_readme.txt` | the artifact-evaluation instructions (the only README) |
| `leveldb/` | modified LevelDB 1.23 — the primary implementation |
| `rocksdb/` | modified RocksDB 6.27 (`rocksdb/adapter/`) |
| `wiredtiger/` | modified WiredTiger + `wiredtiger/app/` driver |
| `sqlite/`, `mongo/` | side experiments, not used for the headline results |
| `simulator/` | the §3 offline simpy simulator |
| `scripts/` | ~50 experiment/plot scripts, incl. 4 `ae_*.py` AE drivers |
| `traces/` | 36 request traces (~3 GB) — all workloads used in §5 |
| `bpf/bcc/` | a vendored copy of iovisor/BCC, used only by the `*_cachestat.py` measurement scripts |
| `init_after_reboot.sh` | 2-line root helper (mount NVMe, chown cgroup v1 tree) |

### Paper component → code path

| paper component | code |
|---|---|
| Tracker (§4.1.1), state machine | `leveldb/util/adapter.cc:28` `Adapter::StateFunction`; states in `leveldb/util/adapter.h:347` |
| `Le = (1−Ha)(Ca+(1−Hk)Ck)` | `leveldb/util/adapter.h:60` `CacheStat::Calculate` |
| GhostSim, 9 candidates (§4.2.2) | `leveldb/util/adapter.h:77` `class Simulator`; `num_searches_=8` at `:83`; pipelining in `Simulator::IncrementSearchStage` (`:145`) |
| Misalignment-aware sampling (§4.2.3) | `leveldb/util/adapter.h:168` `Simulator::Simulate` — `grouping_factor=5` (G=32) at `:87`, `sampling_factor=6` (R=1/64) at `:86`; read-ahead compensation is the `+10000000` fudge at `:150` and the `size_factor` at `:274` |
| Stack-property ghost cache (§4.2.2) | `leveldb/util/cache.cc:322` `MultiLengthLRUCache` (rank bookkeeping at `:352–:380`) |
| Reset policy (§4.2.1) | `leveldb/util/adapter.cc:75–:79` (`ChangeCacheCapacity(default_app_cache_size_)`) |
| Guardrail (§4.2.4) | `leveldb/util/adapter.cc:178` (`jump_tolerance_ = 0.9`, `adapter.h:363`) |
| Stats collection on the read path | `leveldb/table/table.cc:201` `Adapter::instance->Record(...)` inside `Table::BlockReader2` |
| Kernel hit/miss **inferred from timing** | `leveldb/table/format.cc:162` `ReadBlock3` — `*kernel_hit = pair.second - pair.first < 8;` at `:177` |
| Dynamic app-cache resize | `leveldb/db/db_impl.cc:1484` `DBImpl::ChangeCacheCapacity` → `Cache::ChangeCapacity` (`leveldb/util/cache.cc:221`, `:301`) |
| Offline simulator (§3) | `simulator/main.py`, `simulator/cache.py`, `simulator/system.py`, `simulator/application.py`, `simulator/adapter.py` |
| RocksDB port (§4.3) | `rocksdb/adapter/adapter.h`, `rocksdb/adapter/adapter.cc` |
| WiredTiger port (§4.3) | `wiredtiger/app/adapter.h`, `wiredtiger/app/adapter.cc`, `wiredtiger/app/simple_read.cpp` |

### Evaluation scripts

- `scripts/ae_eval_static.py` → Figure 8(b) (`--benchmarks=readtrace`, snappy, 5 patterns ×
  5 ratios × {adapter, Mk0, baseline} = 75 runs).
- `scripts/ae_eval_dynamic.py` → Figure 12 (§5.2.2).
- `scripts/ae_eval_final.py` → Figure 15 (§5.3), uses the four `rocksdb_*` mix_graph traces.
- `scripts/ae_simulator.py` → Figure 4 (§3).
- Non-AE originals: `scripts/run_eval_static.py`, `run_eval_dynamic.py`, `run_eval_final.py`,
  `run_eval_static_wt.py`, `run_eval_static_rocksdb.py`, `run_eval_write.py`,
  `run_eval_static10.py` (the `M = 10 GB` Figure 8(a) variant).
- **No plotting scripts for Figures 8/12/15.** `scripts/plot_*.py` only cover the §3
  simulator figures. Figure 8 must be re-plotted from the `*.output` / `*.latency` files.

### Build route on *this* machine

LevelDB (the only target that matters for the headline result):
1. All third-party deps are **vendored in-tree** — `leveldb/third_party/ordered-map`,
   `third_party/googletest`, `third_party/benchmark` are all present; no submodule fetch
   needed. (`.gitmodules` at the repo root refers to a `third_party/rocksdb` path that does
   not exist — a stale leftover.)
2. `leveldb/CMakeLists.txt:45,:288–:289` links `snappy` and `zstd`. Not installed system-wide
   here → `conda install -c conda-forge snappy zstd` and set `CMAKE_PREFIX_PATH`.
3. `<sys/sdt.h>` is `#include`d by four files (`leveldb/table/block.cc:12`,
   `leveldb/table/table.cc:19`, `leveldb/db/table_cache.cc:11`,
   `leveldb/benchmarks/db_bench.cc:10`) and needs `systemtap-sdt-dev`. The `DTRACE_PROBE2`
   calls are only for the (unused) BCC tracing path, so a 5-line stub header is sufficient.
4. `cmake 3.25.1` and `gcc 12.2` are present and adequate (`cmake_minimum_required(VERSION 3.9)`,
   C++11, `-march=native`). `__rdtscp` and `_mm_crc32_u32` are plain unprivileged x86
   instructions available on Zen 3.
5. RocksDB 6.27 (Nov 2021) with gcc 12 typically needs a handful of `#include <cstdint>`
   patches — a known, documented annoyance, not a blocker. WiredTiger's `app/makefile:5`
   hard-codes `/usr/local/lib/libwiredtiger.a`, so WiredTiger must be built with
   `--prefix=$HOME` and the makefile edited.

### Root-requiring pieces and their substitutes

| in the artifact | why | substitute without root |
|---|---|---|
| `ae_readme.txt:10` "Root access is required for clearing kernel page cache"; `leveldb/benchmarks/db_bench.cc:1411` `system("sync; echo 3 \| sudo tee /proc/sys/vm/drop_caches; sudo fstrim -av")` | cold-start each data point | the call's return value is already ignored, so it fails silently. Replace with `posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED)` over the DB files (the codebase already uses this idiom at `leveldb/util/env_posix.cc:614`), and/or destroy+recreate the cgroup between runs |
| `cgexec -g memory:10` (cgroup **v1**) in `scripts/run_eval_static.py:4`, `run_eval_dynamic.py:4`, `run_eval_final.py:4`, `run_eval_write.py:10` | enforce `M = 1 GB` | cgroup **v2** is mounted here with `memory` delegated to the user slice: `mkdir` a sub-cgroup, `echo 1G > memory.max`, `echo $$ > cgroup.procs`. Unprivileged |
| `scripts/setup_cgroup.py:8–:19` — `cgcreate`, `swapoff -a`, SMT off, `scaling_max_freq` | noise reduction | skippable; costs run-to-run variance. Swap cannot be disabled, so `memory.swap.max = 0` should be set in the v2 cgroup instead |
| `bpf/` + `scripts/run_*_cachestat.py` (`sudo python3` BCC) | measuring page-cache hit ratios for the *motivation* figures | not on the path to any headline result; skip entirely |
| `init_after_reboot.sh` | mounts `/dev/nvme0n1`, chowns the cgroup v1 tree | not needed; point `--db=` at `$HOME` |

### Data / traces

All 36 traces are committed in `traces/` (e.g. `uniform_10M_{0.2,0.4,0.6,0.8,1}.out.req.trace`,
`hotspot{70,80,90}_10M_*`, `sczipf80_10M_2G_req.trace`, and the four `rocksdb_*` mix_graph
traces for Figure 15). Format is one integer key per line (`db_bench.cc:1022` `input >> k`).
The DB itself is generated locally with `./db_bench --benchmarks=fillseq --db=leveldb`
(`FLAGS_num = 50 000 000`, `FLAGS_value_size = 80` → `Du ≈ 5 GB`, ≈2.5 GB on disk at α = 0.5).
Nothing proprietary, nothing to download.

### Repo health

8 stars, 0 forks, 0 open issues, no license file, no activity since 2024-01-24. It is a
research dump, not a maintained project: `adapter.cc`/`adapter.h` carry large blocks of
commented-out code and dead branches (`State::SKETCH` is `assert(false)`), `simulator/adapter.py:383`
begins `Adapter2.Record` with an unconditional `return`, and `simulator/main.py:14` hard-codes
`base_dir = "/home/yifan/research/cache/"`. Nothing fatal, but expect to read code rather
than docs.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | The paper's reference [1] (p.15) is literally `https://github.com/daiyifandanny/Symbiosis`; the account is first author Yifan Dai. The repo contains the full modified engines (`leveldb/util/adapter.{h,cc}`, `rocksdb/adapter/`, `wiredtiger/app/`), the §3 simulator (`simulator/main.py`), all evaluation traces (`traces/`), and AE drivers (`scripts/ae_eval_static.py` etc.) — not a placeholder or plot-only drop. |
| `H2_no_root` | **pass** | No kernel patch, no module, no eBPF on the result path. Timing uses the unprivileged `__rdtscp` instruction (`leveldb/util/timer.cc:16`), not `perf_event_open`. The two root touch points are (a) the `sudo … drop_caches` call at `leveldb/benchmarks/db_bench.cc:1411`, whose return is already ignored and which is replaceable by `posix_fadvise(POSIX_FADV_DONTNEED)` (idiom already present at `leveldb/util/env_posix.cc:614`), and (b) cgroup **v1** `cgexec -g memory:10` in `scripts/run_eval_static.py:4`, replaceable by a cgroup v2 sub-cgroup under the delegated user slice (`env.md`: `cpu memory pids` delegated). The vendored `bpf/bcc/` tree — source of almost every red-flag grep hit (sudo/ebpf/kvm/kernel-module/perf) — is an unmodified upstream BCC copy used only by `scripts/run_*_cachestat.py`, which produce motivation-section statistics and are not needed for Figures 8/12/15. |
| `H3_hardware_fit` | **pass** | CPU-and-SSD only; no GPU at all. Paper scale is `M = 1 GB`, `Du ≤ 5 GB`, one single-threaded process (`db_bench` default `FLAGS_threads = 1`, `db_bench.cc:84`). Repo ≈3.2 GB + DB ≈2.5 GB ≪ 257 GB free. Even the largest variant, Figure 8(a) at `M = 10 GB` / `Du = 50 GB` (`scripts/run_eval_static10.py`), fits in 125 GB RAM and on disk. Single node throughout. |
| `H4_obtainable_deps_data` | **pass** | Deps are `cmake`, `gcc`, `snappy`, `zstd`, `systemtap-sdt-dev`, `python3 + numpy + simpy`, `libcgroup-tools`. snappy/zstd/numpy/simpy come from conda-forge/pip in user space; `<sys/sdt.h>` is a single header that can be stubbed (the `DTRACE_PROBE2` sites are dead code for our purposes); `cgexec` is replaced by direct cgroup-v2 writes. All 36 evaluation traces are committed in `traces/`; the database is generated locally by `db_bench --benchmarks=fillseq`. No proprietary data. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** Figure 8(b) "Basic setting" (p.10), produced by `scripts/ae_eval_static.py`:
LevelDB + snappy (α = 0.5), `M = 1 GB`, `Du ∈ {5, 2.5, 1.67, 1.25, 1} GB`, five YCSB access
patterns, three configurations (`Ma = 8 MB`, `Ma = 1 GB`, Symbiosis) = 75 runs of 10 M reads.
**Claim under test:** *at every one of the 25 workload points Symbiosis matches the better of
the two static baselines, and at some points beats both* (§5.1.1 summary: up to 5.77× over the
worse baseline, up to 1.32× over both).

This is the right target because it is the one the authors themselves packaged for artifact
evaluation, it needs only the in-repo traces, and the claim is a *relative ordering* — it
survives the change of storage device (see below).

**Scale-down.** None on data size; the paper already uses the small configuration
(§5.1.1(b): "to reduce the running time of our experiments, we use 1/10-th the data set sizes
and `M = 1 GB` … the full range of results are extremely similar to that of (a)"). Instead the
*platform* must be adapted:

1. `M = 1 GB` via a cgroup v2 sub-cgroup (`memory.max = 1G`, `memory.swap.max = 0`) under the
   delegated user slice, replacing `cgexec -g memory:10`. **The shipped `ae_eval_static.py`
   omits the memory limit entirely** (compare `scripts/run_eval_static.py:4`, which has it) —
   running the AE script as-is gives a meaningless result, because the page cache would be
   unbounded. This is the single most important fix.
2. Replace the `sudo drop_caches` in `db_bench.cc:1411` with `posix_fadvise(POSIX_FADV_DONTNEED)`
   over the DB directory (or just destroy/recreate the cgroup per run).
3. Recalibrate three hardware constants: `Statistics::frequency = 2900` (`leveldb/util/stats.h:30`)
   is the HW1 TSC rate in MHz and must become this machine's TSC rate; the kernel-hit timing
   threshold `< 8` µs (`leveldb/table/format.cc:177`); and `app_miss_cost_ = 3`,
   `kernel_miss_cost = 16` (`leveldb/util/adapter.h:84–:85`), which are HW1's Optane numbers.
   Our Samsung PM9A3 has ~70–90 µs random-read latency, i.e. `Ca/Ck` is much closer to the
   paper's **HW2** regime (Figure 8(e), `Ca/Ck = 0.0625`) than to HW1's. Report the result
   against Figure 8(e)'s *shape* as well as 8(b)'s, and state this up front — the absolute
   µs values will not match either panel, the ordering claim should.
4. Reduce the sweep if needed: 3 patterns (uniform / hotspot30 / hotspot10) × 5 ratios × 3
   configs = 45 runs still tests the claim.

**Steps.**
1. conda env: `snappy`, `zstd`, `numpy`, `simpy`, `cmake`; stub `sys/sdt.h`. Build
   `leveldb/build` with cmake. *(~0.5 day)*
2. `./db_bench --benchmarks=fillseq --db=$HOME/leveldb` (50 M keys, ≈2.5 GB on disk). *(~1 h)*
3. Write a cgroup-v2 launcher + fadvise-based cache drop; patch `db_bench.cc:1411`. *(~1 day)*
4. Microbenchmark this machine: TSC rate, page-cache-hit `pread` latency vs device `pread`
   latency, snappy decompress cost → set the four constants. *(~1 day)*
5. Run `ae_eval_static.py` (patched) and parse `ae_static/*.latency`; write the Figure 8
   plotting script from scratch (none is shipped). *(~1 day + ~6–10 machine-hours)*
6. Sanity cross-checks: `scripts/ae_simulator.py` reproduces Figure 4 in pure Python
   (minutes, zero risk) and is a good day-1 confidence builder. *(~0.5 day)*

**Effort estimate.** ≈5–7 person-days + ≈20 machine-hours (CPU/SSD only; **0 GPU-hours**).

**Level: M.** Not H, because five separate pieces of porting stand between `git clone` and a
comparable number: the AE script drops the cgroup limit that the paper's own script has;
cgroup v1 → v2; the `sudo drop_caches` baked into the binary; three undocumented
hardware-specific constants that silently change what Symbiosis decides; and no plotting
script for the target figure. Not L, because every trace is in the repo, the eval driver
exists, the artifact is a 1 kLoC delta on a LevelDB that still builds with a modern toolchain,
and nothing about the experiment exceeds this machine.

## 5. Add-on ideas

### A1 — Self-calibrating cost model

**Hypothesis.** We hypothesise that replacing Symbiosis's compile-time miss costs and its
fixed kernel-hit timing threshold with an online, self-calibrated cost model improves the
steady-state latency of the `<Ma,Mk>` split Symbiosis chooses, on storage devices and
compression libraries it was not tuned for (Samsung PM9A3 NVMe, zstd), compared with the
shipped constants.

**Mechanism.** (i) `ReadBlock3` already times every block read; collect a rolling sample of
those latencies, fit a two-mode split (valley of the histogram, or a 2-component 1-D GMM),
set the kernel-hit threshold at the valley instead of the hard-coded `8`, and set
`Ck = mean(device mode) − mean(hit mode)`. (ii) Time the decompress + `new Block` path in
`BlockReader2` to obtain `Ca` online. (iii) Feed both into `CacheStat::Calculate` instead of
the static members. (iv) Derive `Statistics::frequency` at startup by calibrating `__rdtscp`
against `clock_gettime(CLOCK_MONOTONIC)` rather than hard-coding 2900 MHz.
Evaluation: rerun the Figure 8 sweep with (a) shipped constants, (b) calibrated constants,
on our NVMe and on a slowed-down device emulation, and compare the chosen `Ma` against an
exhaustive 9-point static oracle sweep.

**code_locations.** `leveldb/util/adapter.h` (`:60` `Calculate`, `:84–:85` cost constants),
`leveldb/table/format.cc` (`:162` `ReadBlock3`, `:177` threshold), `leveldb/util/stats.h` (`:30`),
`leveldb/util/timer.cc`, `leveldb/table/table.cc`.

**Motivating evidence.** §4.1.1 states the assumption outright: "Tracker continuously audits
the hit/miss result of each cache and calculates `Le` with **statically configured miss costs
by offline measurement**." Table 1 (p.9) shows `Ca` moving 3→9 µs merely by switching snappy→zstd
and `Ck` 16→80 µs by switching hardware, and Figure 4 I(a) shows the *global* minimum flips
from `Mk = α·Du` to `Mk = 0` as `Ca` crosses 60 — i.e. the system's central decision is a step
function of exactly the constants it hard-codes. The claim "Symbiosis needs no manual tuning"
rests on four magic numbers.

**feasibility: H.** Localised: four files, a few hundred LoC, no new harness — the existing
`ae_eval_static.py` sweep is exactly the evaluation. Runs on this machine in hours.

**research_value: M.** A reviewer would recognise it as fixing a real portability hole the
authors acknowledge, and the "the published constants mis-size the cache by X% on a different
SSD" result is a genuine finding — but it is a robustness fix rather than a new mechanism, so
the ceiling is moderate.

**scoop_check: clear.** Searched for follow-ups to Symbiosis (Semantic Scholar / Google /
arXiv, queries: *"papers citing Symbiosis FAST 2024 application kernel cache partitioning"*,
*"Symbiosis Dai Arpaci-Dusseau cache sizing ghost cache follow-up 2025"*,
*"inferring page cache hit miss from read latency threshold user space calibration"*). No
follow-up by the authors or others; the general latency-threshold idea is folklore but nobody
has published it as a portability fix for this system.
Closest: [Yifan Dai's page](https://pages.cs.wisc.edu/~yifann/) lists no successor paper.

---

### A2 — Exclusive application/kernel caching via `fadvise`

**Hypothesis.** We hypothesise that making the two caches approximately *exclusive* — dropping
the page-cache pages fully covered by a block right after that block is admitted to the
application cache — reduces average read latency in the mid-range `M/Du ∈ [0.3, 0.8]` regime,
where the paper shows both endpoint configurations are poor, and shifts the optimum Symbiosis
finds away from the two endpoints.

**Mechanism.** In `BlockReader2`/`ReadBlock3`, after a block is inserted into the block cache,
compute the page range *fully* covered by `[handle.offset(), handle.offset()+handle.size())`
(the misalignment arithmetic already exists in `Simulator::Simulate`, `adapter.h:260–:261`) and
issue `posix_fadvise(fd, off, len, POSIX_FADV_DONTNEED)` on it; pages only partially covered are
left alone so live neighbours are not evicted. Then extend GhostSim's kernel model to be
exclusive — skip inserting kernel keys for blocks currently resident in the app ghost cache —
so the simulator predicts the new regime rather than the duplicated one. Add the existing
guardrail pattern: enable only above an `Ma` threshold, and measure the per-miss syscall cost
against `Ca ≈ 3 µs`.

**code_locations.** `leveldb/table/format.cc`, `leveldb/table/table.cc`,
`leveldb/util/env_posix.cc` (`:614` already uses `POSIX_FADV_DONTNEED`),
`leveldb/util/adapter.h`, `leveldb/util/adapter.cc`.

**Motivating evidence.** §6 names it explicitly: "Achieving exclusiveness in the
application-kernel cache structure with one compressed layer would be an interesting future
work." §3.2.1 explains *why* the middle of the space is bad: "when `0 < Mk < α·Du`, `Le` is
larger than at both extremes because both caches are non-zero and contain duplicates." If the
duplicates go away, the entire endpoint-optimality result of §3 should change — which is a
much stronger claim than a percentage improvement.

**feasibility: M.** The `fadvise` call itself is a few lines, but three things make it
cross-cutting: partial-page ownership must be handled correctly or the system will evict live
data; `DONTNEED` interacts badly with kernel read-ahead (the very effect §4.2.3 had to model);
and GhostSim must be re-derived for the exclusive regime or the guardrail will reject every
candidate. Evaluable with the existing harness on this machine.

**research_value: H.** It is the authors' own named future work, it targets the regime where
the paper's mechanism has the least to offer, and both outcomes are informative: if exclusivity
wins, the paper's endpoint-optimality analysis is incomplete; if `fadvise` overhead or
read-ahead destruction kills it, that is a concrete negative result about why exclusive caching
is hard across the app/kernel boundary.

**scoop_check: partial.** Classic exclusive-caching work (DEMOTE, X-RAY, eviction-based
placement) is already cited in §6 but predates compressed second-level caches and does not use
`fadvise`. The closest modern work is
[Cache is King: Smart Page Eviction with eBPF (arXiv:2502.02750)](https://arxiv.org/abs/2502.02750),
which lets applications customise page-cache *eviction policy* via eBPF — related goal
(app-informed page cache), different mechanism, and it needs eBPF, which this machine forbids.
No paper found that does fadvise-based app/kernel exclusivity for a compressed LSM block cache.

---

### A3 — Compaction-aware adaptation for write-mixed workloads

**Hypothesis.** We hypothesise that making GhostSim compaction-aware — invalidating ghost
entries whose SST files were rewritten, and discounting simulation windows that overlap high
compaction throughput — reduces the application-cache hit-rate prediction error of Figure 9(b)
and lets Symbiosis retain a latency advantage over *both* static baselines at ≥20% overwrites,
where Figure 9(a) shows its benefit largely disappears.

**Mechanism.** Hook compaction completion in `DBImpl` (the `BackgroundCompaction` /
`InstallCompactionResults` path) to notify `Adapter`. On notification, either (a) erase ghost
entries keyed on the obsoleted `cache_id` (the ghost key is `(cache_id << 12) + block_index`,
`adapter.h:191`), or (b) extend/abort the current simulation round if the rewritten fraction of
the working set exceeds a threshold — an application of the existing §4.2.4 guardrail
philosophy to a new failure mode. Additionally, scale the measured `Le` by an estimate of the
compaction-induced read amplification so Tracker does not mistake compaction noise for a
workload change. Evaluate with `db_bench --benchmarks=writetrace`
(`leveldb/benchmarks/db_bench.cc:1055` `WriteTrace`, driven by `scripts/run_eval_write.py`) at
0/10/20/40% overwrites, and reproduce Figure 9(b)'s predicted-vs-observed hit-rate curve.

**code_locations.** `leveldb/db/db_impl.cc`, `leveldb/util/adapter.cc`, `leveldb/util/adapter.h`,
`leveldb/benchmarks/db_bench.cc`, `scripts/run_eval_write.py`, `scripts/gen_ycsb.py`.

**Motivating evidence.** §4.2.5 is an explicit open-problem statement: "The idea of
simulation-based cache size adaption can work with write-heavy workloads, yet will require
additional research to realize in robust form. For example, LSM-based engines often schedule
asynchronous background compaction in the write path; thus, speed differences … can lead to
varying tree structures and thus different cache access traces." Figure 9(b) (p.10) quantifies
the damage: the predicted `Ma = 1 GB` hit ratio diverges from the observed one as compaction
throughput rises from 20 to 40 MB/s, and the paper's only remedy is "by limiting the compaction
rate" — a workaround, not a fix.

**feasibility: M.** Touches the compaction path and the adapter state machine (cross-cutting),
and the write traces are not shipped — they must be generated with `scripts/gen_ycsb.py` and
`run_eval_write.py` must be ported to cgroup v2 like the read scripts. Compute is comfortable:
write-mixed runs are the same 10 M-op scale.

**research_value: H.** The authors named it as the main unaddressed regime; read-only is a
strong assumption for an LSM paper, and a FAST reviewer would care. Both outcomes teach
something — either compaction-awareness is enough, or the deviation is fundamental (the trace
you measure is not the trace the alternative configuration would produce), which is a crisp
statement about the limits of online ghost simulation.

**scoop_check: partial.** Compaction-aware caching exists as a separate line of work
(cache-warmth preservation across SSTable rewrites; see the survey
[Rethinking LSM-tree based Key-Value Stores (arXiv:2507.09642)](https://arxiv.org/pdf/2507.09642)
and [AC-Key, ATC '20](https://www.usenix.org/system/files/atc20-wu-fenggang.pdf), which uses
ghost caches to size *application-level* KV/KP/block caches). None of these addresses the
app↔*kernel* split or the trace-deviation problem Symbiosis identifies. No follow-up to
Symbiosis itself found.

---

### A4 — Co-located instances sharing one page cache

**Hypothesis.** We hypothesise that when two or more Symbiosis-enabled engines share a single
memory budget, their independent sizing decisions degrade aggregate latency relative to the best
static split (mutual eviction and oscillation), and that a shared-budget arbiter that exchanges
the per-instance `Le(Ma)` curves GhostSim already computes recovers most of the single-instance
gain.

**Mechanism.** Phase 1 (measurement): run two `db_bench` instances with different workloads
(e.g. hotspot10 + uniform) inside one cgroup-v2 `memory.max`, and log both `Ma` trajectories and
the aggregate latency against a 2-D static oracle sweep. Phase 2 (fix): `Simulator::BestStat`
(`adapter.h:290`) already produces the full 9-point `Le` vs `Ma` curve; publish it to a shared
memory segment or a Unix socket, and have a coordinator pick the joint allocation by
marginal-benefit greedy across both curves subject to `ΣMa + Mk ≤ M`, instead of each instance
independently claiming memory. Reuse the existing guardrail so the joint decision is applied
only above a gain threshold.

**code_locations.** `leveldb/util/adapter.h`, `leveldb/util/adapter.cc`,
`leveldb/benchmarks/db_bench.cc`, `leveldb/db/db_impl.cc`, `scripts/ae_eval_static.py`.

**Motivating evidence.** The entire evaluation is single-instance and single-threaded
(`db_bench.cc:84` `FLAGS_threads = 1`; §5 Setup: "the available memory `M` is fixed at 1 GB by
cgroup" for one engine), yet §3.1 explicitly motivates `M` as "a containers' resource limit
[26, 38, 72]" — i.e. the multi-tenant setting is the paper's own framing, and it is never
tested. The kernel page cache is a *globally shared* resource: instance A's decision to shrink
its app cache hands memory to a page cache that instance B is also competing for, so the
implicit `Ma + Mk = M` invariant that the whole design rests on simply does not hold.

**feasibility: M.** A new harness is required (multi-process launcher, joint-latency
accounting, 2-D oracle sweep) plus a small IPC layer, but everything is user space and the
machine has 16 cores / 125 GB — several instances at `M = 1–4 GB` fit easily. The 2-D oracle
sweep is the main compute cost (9 × 9 points × a handful of workload pairs ≈ a few hundred runs,
still tens of machine-hours).

**research_value: H.** This is the first question a FAST reviewer asks about any single-tenant
memory-partitioning system, and the paper pre-emptively cites the container setting without
evaluating it. The negative result alone (independent adapters fight and oscillate) would be a
worthwhile contribution; the arbiter, if it works, is a genuine design extension.

**scoop_check: clear.** Multi-tenant KV interference is a studied area
([Performance Interference on Key-Value Stores in Multi-tenant Environments, ICPE '21 companion](https://dl.acm.org/doi/10.1145/3447545.3451191);
Memshare, ATC '17), but those partition an *application* cache among tenants, not the
app-cache/page-cache split, and none builds on Symbiosis. No follow-up found.

---

### A5 — Model-guided candidate search for faster convergence

**Hypothesis.** We hypothesise that replacing GhostSim's exhaustive 9-candidate sweep with a
search that exploits the smoothness of the `Le(Ma)` curve (ternary/golden-section search, or a
1-D surrogate fit refined by a few probes) halves the convergence time reported in Figure 12
without degrading the quality of the chosen `Ma`, and thereby extends Symbiosis to workloads
that change faster than its current 15–40 s round.

**Mechanism.** `Simulator::IncrementSearchStage` (`adapter.h:145`) currently walks stages
0…8 in order, shrinking the kernel ghost cache monotonically to exploit reuse. Replace the
fixed walk with an adaptive order: evaluate the endpoints and midpoint first, fit/inspect the
shape, then probe only the promising sub-interval. Because the pipelined reuse depends on
monotonically increasing `Ma`, a non-monotonic order costs extra ghost-cache warm-up — the
research question is whether fewer stages beats worse reuse. Compare against the shipped
scheme on convergence time, chosen `Ma`, and steady-state latency, using the Figure 12 dynamic
suite (`scripts/ae_eval_dynamic.py`), plus a new faster-oscillation workload that the current
system explicitly cannot serve.

**code_locations.** `leveldb/util/adapter.h`, `leveldb/util/adapter.cc`,
`scripts/ae_eval_dynamic.py`, `simulator/main.py`.

**Motivating evidence.** §4.2.2 states the design choice and its cost: GhostSim divides the
space "into a fixed number of equal ranges (currently 8) **without skipping candidates or
stopping early**". §5.2.2 reports 15.4 s average and 40 s worst-case convergence, and §4.2.5
turns that into a hard limitation: "We assume that workloads change infrequently. … If the
workload changes repeatedly during simulation, Symbiosis stops the simulation as it is unable
to finish and yield benefits." §3.3 supplies the enabling observation: "the curves are
relatively smooth without abrupt changes."

**feasibility: H.** Confined to two files and a few hundred LoC; the offline simulator
(`simulator/main.py`) lets the search policy be prototyped in Python before touching C++; the
existing dynamic-workload harness measures exactly the target metric.

**research_value: M.** Convergence time is a real, author-acknowledged limitation and halving
it unlocks a workload class the paper excludes — but the technique is an expected optimisation
over an exhaustive sweep, and a reviewer would find the direction unsurprising. It becomes more
interesting if the ghost-cache reuse/search-order tension turns out to be fundamental, i.e. if
fewer candidates do *not* mean faster convergence.

**scoop_check: clear.** No follow-up to Symbiosis. Adjacent work on adaptive cache sizing
([DynamicAdaptiveClimb, arXiv:2511.21235](https://arxiv.org/pdf/2511.21235),
[AdCache, EDBT '26](https://openproceedings.org/2026/conf/edbt/paper-89.pdf)) tunes single-level
or application-level caches with hill-climbing / RL, not the candidate-ordering problem inside a
pipelined two-level ghost simulator.

## 6. Risks and open questions

1. **The AE script silently drops the memory limit.** `scripts/ae_eval_static.py` has no
   `cgexec`, while the paper's own `scripts/run_eval_static.py:4` does (`-g memory:10`, 1 GB,
   cgroup v1). Running the AE script verbatim measures nothing meaningful. Any reproduction
   must restore the limit via cgroup v2 first. This is the highest-probability way to "fail to
   reproduce" for the wrong reason.
2. **Three undocumented hardware constants change the system's behaviour.**
   `Statistics::frequency = 2900` (`leveldb/util/stats.h:30`), the kernel-hit threshold `< 8`
   (`leveldb/table/format.cc:177`), and `Ca = 3` / `Ck = 16` (`leveldb/util/adapter.h:84–:85`)
   are all HW1-specific. On our Zen 3 / PM9A3 machine all four are wrong. Nothing in the repo
   says so. Getting them wrong does not crash anything — it just makes Symbiosis pick the
   wrong `Ma`, which would look like a failed reproduction. (This is also what A1 attacks.)
3. **Device mismatch.** The paper's headline HW1 uses an Optane 900P (~10 µs); we have a TLC
   NVMe (~70–90 µs), so our `Ca/Ck` sits near the paper's HW2 point. Absolute latencies will
   not match Figure 8(b); only the *ordering* claim should be asserted. Scale the expected
   outcome to Figure 8(e) as well.
4. **Timing-based kernel-hit inference is fragile on a shared machine.** `env.md` notes the
   machine is shared and SMT is on; `scripts/setup_cgroup.py` disables SMT, pins frequency and
   turns off swap — none of which we can do. An 8 µs threshold on a noisy box will misclassify
   hits, feeding noise straight into `Le`. Expect higher run-to-run variance than the paper;
   budget repeats.
5. **No plotting scripts for the headline figures.** `scripts/plot_*.py` only cover §3. Figures
   8/12/15 must be re-derived from `*.latency`/`*.output` text files; the output format is only
   discoverable by reading `db_bench.cc:992` / `:1031`.
6. **RocksDB 6.27 + gcc 12.** Expect `#include <cstdint>` build failures typical of that era.
   LevelDB is unaffected. WiredTiger additionally hard-codes `/usr/local/lib/libwiredtiger.a`
   (`wiredtiger/app/makefile:5`) and would need a `$HOME` prefix build — treat both non-LevelDB
   ports as stretch goals, not part of the core reproduction.
7. **Artifact badges unverified.** `ae_readme.txt:1–2` says "We aim for Available and Functional
   flag due to inability to provide access to our machine with Optane device" — an *aspiration*,
   not evidence of an award. The USENIX presentation page returns HTTP 403 to automated fetches
   and web search surfaced no badge listing. Treat badges as unknown; note the authors
   themselves disclaimed "Results Reproduced".
8. **Dead/disabled code.** `simulator/adapter.py:383` starts `Adapter2.Record` with an
   unconditional `return` (the simulator's own online adapter is switched off — only the §3
   parameter sweep is live), `State::SKETCH` is `assert(false)` in both `adapter.h:435` and
   `adapter.cc:117`, and `simulator/main.py:14` hard-codes `/home/yifan/research/cache/`.
   Anyone extending the simulator should verify which code paths actually execute.
9. **Repo weight.** ~3.2 GB / 7 662 files, dominated by `traces/` and the vendored BCC,
   RocksDB and WiredTiger trees. Cheap on 257 GB free, but clone time and grep noise are real
   (every kernel/eBPF/KVM red flag in `repo_facts.json` comes from `bpf/bcc/`).
10. **No license file.** GitHub reports `"license": null`. Fine for a course project, worth
    noting before any public release of derived work.

## 7. Evidence index

**Paper.**
§1 Introduction (p.2) — contributions, ~1 kLoC LevelDB delta, >5× claim.
§2.1 (pp.3–4) — two-level cache structure, LevelDB vs WiredTiger caching, Linux 2Q + read-ahead.
§2.2 Figure 2 (p.4) — motivating 2.5–7× swing between the two static configurations.
§2.3 Figure 3 (p.4) — system overview.
§3.1 (pp.4–5) — parameters `M, Du, α, Dmem, Ha, Hk, Ca, Ck`; `Ca` 40–250 µs (WiredTiger), <10 µs (LevelDB).
§3.2.1 Figure 4 I(a)–(d), II(a)–(b) (pp.5–6) — endpoint optimality for uniform; `Ca` crossover at 60; up to 9× gain.
§3.2.2 Figure 5 (p.6) — read+scan workload, interior optima, "more difficult to predict".
§3.3 (p.6) — "the curves are relatively smooth without abrupt changes".
§4.1.1 (p.7) — Tracker, `Le`, **statically configured miss costs by offline measurement**, 10% threshold.
§4.2.1 (p.7) — reset policy. §4.2.2 (p.8) — 8 equal ranges, no early stopping, pipelined reuse.
§4.2.3 Figure 7 (p.8) — misalignment-aware sampling, `R = 1/64`, `G = 32`, read-ahead compensation.
§4.2.4 (p.8) — guardrail / fall-back. §4.2.5 (pp.8–9) — **infrequent-change assumption; write-heavy = future work**; 45 s worst detect+simulate.
§4.3 (p.9) — LevelDB/WiredTiger/RocksDB ports; WiredTiger eviction bug.
Table 1 (p.9) — factors, HW1/HW2, `Ca` 3→9 µs across compression libs, `Ck` 16→80 µs across devices.
§5 Setup (p.9) — `M = 1 GB` by cgroup; baselines `Ma = 8 MB` and `Ma = 1 GB`.
§5.1.1 Figure 8(a)–(e) (p.10) — **primary reproduction target**; up to 5.77× / 1.32×.
§5.1.2 Figure 9(a)(b) (p.10) — 20% overwrites; prediction error vs compaction throughput.
§5.1.3–5.1.4 Figure 10 (p.11) — WiredTiger and RocksDB.
§5.2.1 Figure 11 (p.11) — timeline, ~12 s and ~13 s convergence.
§5.2.2 Figure 12, Table 2 (pp.12–13) — 24%/42% gains, 15.4 s avg / 40 s worst convergence, p99 +15.3% median / +52% worst.
§5.2.3 Figure 13, §5.2.4 Figure 14, Table 3 (p.13) — gradual change; reset-policy ablation; 0.46 MB / 0.09 µs per op.
§5.3 Figure 15 (p.14) — RocksDB mix_graph four-phase trace; 3 adopted, 1 rejected decision.
§6 Related work (p.14) — **"Achieving exclusiveness … would be an interesting future work."**
Reference [1] (p.15) — the repository URL.

**Repository.**
`ae_readme.txt` (AE instructions; root-for-drop_caches note at :10; badge aspiration at :1–2)
`init_after_reboot.sh`
`leveldb/CMakeLists.txt` (:45, :123, :288–:289, :302–:303)
`leveldb/util/adapter.h` (:60 `Calculate`, :77 `Simulator`, :83 `num_searches_`, :84–:85 miss costs, :86–:87 sampling/grouping, :145 `IncrementSearchStage`, :168 `Simulate`, :260–:261 page arithmetic, :290 `BestStat`, :346 `Adapter`, :363 tolerances, :435 dead SKETCH)
`leveldb/util/adapter.cc` (:28 `StateFunction`, :75–:79 reset, :117 dead SKETCH, :178 guardrail)
`leveldb/util/cache.cc` (:221, :301 `ChangeCapacity`, :322–:380 `MultiLengthLRUCache`)
`leveldb/util/stats.h` (:30 `frequency = 2900`)
`leveldb/util/timer.cc` (:16, :23 `__rdtscp`)
`leveldb/util/global.h`
`leveldb/util/env_posix.cc` (:204, :276 `pread`, :614 `posix_fadvise(DONTNEED)`, :969 `MMAP_LIMIT`)
`leveldb/util/page_cache_sim.h` (user-space 2Q + read-ahead page-cache model)
`leveldb/table/table.cc` (:19 `sys/sdt.h`, :142 `BlockReader2`, :172/:187 `ReadBlock3`, :201 `Adapter::Record`)
`leveldb/table/format.cc` (:162 `ReadBlock3`, :177 the `< 8` kernel-hit threshold)
`leveldb/db/db_impl.cc` (:1484 `ChangeCacheCapacity`)
`leveldb/benchmarks/db_bench.cc` (:78 `FLAGS_num`, :84 `FLAGS_threads`, :87 `value_size`, :117 `memory_size`, :681/:1003 `readtrace`, :1022 trace format, :1055 `WriteTrace`, :1411 `sudo drop_caches`)
`leveldb/third_party/ordered-map/`, `leveldb/third_party/benchmark/CMakeLists.txt` (vendored deps present)
`scripts/ae_eval_static.py`, `scripts/ae_eval_dynamic.py`, `scripts/ae_eval_final.py`, `scripts/ae_simulator.py`
`scripts/run_eval_static.py` (:4 `cgexec -g memory:10`), `scripts/run_eval_static10.py`, `scripts/run_eval_write.py` (:10), `scripts/run_eval_static_wt.py`
`scripts/setup_cgroup.py` (:8–:19 root-only host tuning)
`scripts/gen_ycsb.py`, `scripts/plot_*.py` (only §3 figures)
`simulator/main.py` (:14 hard-coded path, :151– CLI), `simulator/adapter.py` (:266 `Simulator`, :383 disabled `Record`), `simulator/cache.py`, `simulator/system.py`, `simulator/application.py`
`rocksdb/adapter/adapter.h`, `rocksdb/include/rocksdb/version.h` (6.27.0)
`wiredtiger/app/adapter.h`, `wiredtiger/app/adapter.cc`, `wiredtiger/app/simple_read.cpp`, `wiredtiger/app/makefile` (:5 `/usr/local/lib/libwiredtiger.a`)
`traces/` (36 trace files, all §5 workloads)
`repo_facts.json` (GitHub metadata: 8 stars, 0 forks, no license, pushed 2024-01-24; red flags all from `bpf/bcc/`)

**Web.**
[USENIX presentation page](https://www.usenix.org/conference/fast24/presentation/dai) (403 to automated fetch; no badge evidence obtained)
[Author page, Yifan Dai](https://pages.cs.wisc.edu/~yifann/) (no follow-up publication)
[Cache is King: Smart Page Eviction with eBPF (arXiv:2502.02750)](https://arxiv.org/abs/2502.02750)
[AC-Key, USENIX ATC '20](https://www.usenix.org/system/files/atc20-wu-fenggang.pdf)
[Rethinking LSM-tree based Key-Value Stores: A Survey (arXiv:2507.09642)](https://arxiv.org/pdf/2507.09642)
[AdCache, EDBT '26](https://openproceedings.org/2026/conf/edbt/paper-89.pdf)
[DynamicAdaptiveClimb (arXiv:2511.21235)](https://arxiv.org/pdf/2511.21235)
[Performance Interference on Key-Value Stores in Multi-tenant Environments (ICPE '21)](https://dl.acm.org/doi/10.1145/3447545.3451191)
