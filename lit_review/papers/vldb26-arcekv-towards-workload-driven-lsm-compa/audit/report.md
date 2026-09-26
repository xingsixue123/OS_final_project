# ArceKV: Towards Workload-driven LSM-compactions for Key-Value Store Under Dynamic Workloads

PVLDB 19(5):958–972, 2026. Junfeng Liu, Haoxuan Xie, Siqiang Luo (NTU Singapore).
Artifact: https://github.com/NTU-Siqiang-Group/ArceKV (named in the paper's
"PVLDB Artifact Availability" block, p.1). Extended/technical report: arXiv 2508.03565.

---

## 1. Paper summary

**Problem.** Workload-aware LSM tuners (Dostoevsky, Wacky, Moose, Ruskey, CAMAL) compute a
*structural configuration* — size ratios, level capacities, runs-per-level — that is optimal for
one static workload. When the workload shifts, the optimal configuration shifts too, and the
*transition* between configurations is either expensive (greedy resizing ⇒ write-stall spikes) or
slow (lazy adaptation ⇒ long degraded period). §2.3 and Figure 2 frame this as the core gap: no
existing method gets both responsiveness and low transition cost.

**Key idea (two parts).**

1. **ElasticLSM** (§3.1) — delete the structural constraints entirely. The tree is just a bag of
   sorted runs tagged with (timestamp, size, key range). The only invariant kept is cross-level
   timestamp ordering (Figure 4). This admits three compaction patterns: intra-level (P1),
   adjacent-level (P2), multi-level (P3, spanning i…j with j > i+1). Write stalls are decoupled
   from compaction: throttle at rate `k` when *total* run count `s` exceeds a threshold `c`.
   Table 1 contrasts this with Dostoevsky/Ruskey/Moose.
2. **Arce** (§3.2–3.4) — a score-based decision engine. Operations are bucketed into *count
   windows* of `u = F/E` updates (F = MemTable size, E = entry size), inside which the tree state
   is assumed stable. Per-window costs: point lookup `P(s) = (αs+1)·I_r` (Eq 1), range lookup
   `R(s) = s·I_r` (Eq 2), update `U(s) = (F/B)·I_w + k·1(s>c)` (Eq 3). A compaction of `X` bytes
   is assumed to finish after `t` windows where the foreground I/O time catches up with the
   compaction's I/O time (Eq 4–5). Choosing the globally optimal sequence of `m` compactions is
   NP-hard (Lemma 3.2), so Arce scores each *intermediate* candidate with
   `E(s,t,y) = M·E_l(y) − E_s(s,t)` (Eq 9–11), trading a long-term run-reduction benefit against a
   short-term read-slowdown + write-stall penalty. Lemma 3.3 shows only non-dominated candidates
   (the "left frontier" of Figure 6) can win. The tuple `(M, c, k)` is re-selected by a
   brute-force background simulation (Algorithm 1, p.7) whenever tree state or workload drifts
   more than `d = 0.1`.

**Implementation (§4, Figure 7).** All inside RocksDB: Workload Statistics (windowed `(r,u,p)`
every 1M ops), ElasticLSM, a background simulation thread running Algorithm 1 with 16 threads,
and the score-based picker. Parameter pruning: `M` step 5, `c` step 2 capped at 4× current run
count, `k` initialised to RocksDB's default 6 and doubled twice, `MaxIterTime = 400`.
Multi-threading is folded in via Amdahl's law with φ = 0.5 (following Cosine).

**Evaluation setup (§5).** i9-13900K, 128 GB RAM, 1 TB NVMe, Ubuntu 22.04 + ext4; memory capped
at 75 GiB with cgroups (following Disco). Keys 24 B, values 1000 B, Bloom 10 bits/key,
write buffer 2 MB, `num_levels = 4` for ArceKV, `I_w = 15 µs`, `I_r = 12 µs`. Baselines:
1-Leveling (RocksDB default), Leveling, Tiering, LazyLeveling, Moose, Ruskey, CAMAL — all except
Ruskey and CAMAL re-implemented on the MooseLSM codebase; Ruskey obtained privately from its
authors. Industrial baselines: Pebble, WiredTiger, Cassandra. Workloads: ten `(range, update,
point)` mixes A–J (Table 2) chained into Workload I (A,B,D,J,C,E — abrupt shift, 245.76M ops,
+74 GiB), Workload II (J,E,B,F,D,C — gradual, 245.76M ops, +94 GiB), Workload III (G,H,I, 61.44M
ops) for multi-threading and industrial comparison. A 40 GiB sequential preload precedes every
run.

**Headline numbers.**
- Figure 9 (left table): normalized average throughput — ArceKV **2.92×** on Workload I and
  **2.17×** on Workload II, versus 1-Leveling 1.45×/1.53× (the strongest baseline), Moose
  1.40×/1.53×, CAMAL 1.57×/1.72×, Ruskey 1.07×/1.42×. Per sub-workload the gap is largest on B
  (98% update): ArceKV 10.60× vs 1-Leveling 2.29×.
- Figure 9(a)–(d): ArceKV simultaneously holds low write-stall time (like Tiering) and low read
  I/O (like 1-Leveling), with the fastest run-count collapse under read-heavy phases.
- Figure 10(a)(b): stabilises within ~20M ops after a B→D / B→F shift.
- Figure 10(c): best scaling at 1/4/8/16 foreground threads; (d) >10× over Cassandra/WiredTiger,
  ~3× over Pebble.
- Table 3 (YCSB): ArceKV top on all six of YCSB-A…F (e.g. 4.18× on A, 5.47× on E).
- Figure 11(c)(d): the cost model tracks measured latency; compaction-duration estimates are
  within 3 windows over 500 compactions.
- Figure 12(d): space amplification only 0.05 above Leveling; Figure 12(e): simulation costs ~2%
  of background CPU, decision-making <1%.

**Stated limitations / assumptions.** Number of levels is capped (<8, typically 4) to keep the P3
candidate set tractable (§3.1, footnote 1). Space efficiency is explicitly not an objective
(§5.2 "Space Amplification"). The cost model assumes a single foreground thread and one
background compaction worker; multi-threading is bolted on with Amdahl's law (§4). Adopting
GRF-style range-filter position encoding is left as future work (§5.3).

---

## 2. Artifact audit

### 2.1 What the repository is

The clone is the **`main`** branch, HEAD `04371f7`, 2026-04-29, 2089 files, 38.9 MB, a fork of
**RocksDB 9.5.0** (`include/rocksdb/version.h:14-16`).

**The single most important finding of this audit** is the first line of `README.md`:

> ⚠️ This repository contains **environment-specific adaptations** for the TikTok Recommendation
> Service and **does not represent a faithful implementation of** ArceKV.
> **[29/04/2026]** We publish an on-disk version of ArceKV under the `dev` branch.

`README.md:6-15` lists the deviations: (a) a "simplified write-stop strategy … to avoid costly
searches over a large parameter space", (b) **one SSTable per run**, (c) range-filter policy
removed. The `dev` branch (checked on GitHub) is a *different* codebase again — it uses
`kCompactionStyleArce` / `ArceCompactionController` rather than `kCompactionStyleDynamic` /
`AdaptiveCompactionController`, ships an `examples/arce_dynamic_compaction_integration` harness,
contains a `claude_md/` directory, and its README advertises that it "preserves multi-SST
sorted-run structure" — i.e. it is a re-implementation, not the audited `main` tree.

So the artifact is official and it *does* contain the real Arce engine, but **neither branch is
claimed by the authors to be the code that produced the paper's numbers**. That is a reproduction
risk, not an H1 failure: the actual decision engine, the elastic action enumeration, the picker
and the write-stall hook are all present and readable in `main`.

### 2.2 Paper component → code path

| paper component | code path | notes |
|---|---|---|
| ElasticLSM action space, patterns P1/P2/P3 (§3.1) | `include/rocksdb/dyncompactionv4.h:81-157` (`TreeState::EnumerateActions`) | incremental size-sorted enumeration exactly as described; `DynAction` = a bitmap of removed runs per level |
| Tree state `S` = runs × sizes (Figure 5) | `include/rocksdb/dyncompactionv4.h:53-58`; populated from RocksDB in `db/compaction/compaction_picker_dynamic.cc:46-66` | one entry per SST file, so "run" == "file" on `main` |
| Windowed cost model, Eq 4–5 (§3.2) | `db/dyncompactioner.cc:7-28` (`get_win_acc_ios`) | note `p * (1 + cur_total_runs * 0.01)` — the Bloom FPR α is **hard-coded to 0.01** |
| Effectiveness score, Eq 9–11 (§3.3) | `db/dyncompactioner.cc:30-62` (`get_reward_for_action`) | `reward *= (r + p*0.01) * M` then subtracts the short-term cost |
| Stall rate `k` (Eq 3) | `db/dyncompactioner.cc:5` — `kStallCost = 4`, `kStoppedCost = 1e10` | **static constants**; the paper's tuned `k` (init 6, doubled twice) is absent — this is README modification (a) |
| Algorithm 1 `FindBestParams(M,c,k)` (§3.4) | `db/dyncompactioner.cc:199-235` (`FindBestMC`) + `129-197` (`get_cost_for_mc`) | searches `M ∈ {5,10,…,95}` × `c ∈ {4,8,…,2·runs} ∪ {10^6}`; `k` is **not** searched |
| Parallel simulation, 16 threads (§4) | `db/dyncompactioner.cc:216-224` — `omp_set_num_threads(16); #pragma omp parallel for` | OpenMP, **not** the Eigen/SIMD vectorisation the paper describes in §4 |
| Re-selection threshold `d = 0.1` (§3.4) | `include/rocksdb/dyncompactionv4.h:167` (`state_change_threshold`), `250-263` (`need_reset_Mc`) | drift is measured on the *average run count*, not on the workload tuple |
| Background tuning agent (Figure 7) | `include/rocksdb/advanced_options.h:106-169` (`find_first_mc_when_ready`, `start_tuning_agent`) | detached thread, 5 s poll |
| Compaction picker / ElasticLSM → RocksDB | `db/compaction/compaction_picker_dynamic.cc:348-416` (`PickCompactionActionV3`), `441-461` | ~330 of 462 lines in this file are commented-out dead variants (V1/V2/V3) |
| One-SST-per-run (README mod (b)) | `db/compaction/compaction_picker_dynamic.cc:404` — `/* max file size */ 100UL * (1<<30)` | 100 GiB output file cap ⇒ every compaction emits one SST |
| Write-stall controller driven by `c` (§2.2, §3.1) | `db/column_family.cc:922-946` (`DynamicWriteStallCause`) + `988-994` | stalls at `s ≥ c`, stops at `s ≥ 4c`, where `s` is summed over **all** levels — matches the paper's "total runs" semantics |
| `kCompactionStyleDynamic` plumbing | `include/rocksdb/advanced_options.h:183`, `db/version_set.cc`, `db/db_impl/db_impl_open.cc`, `options/options_helper.cc` | |
| Grafite range filter (§5.3) | `table/block_based/range_filter.cc`, `include/rocksdb/filter_policy.h:211` (`NewDynamicRangeFilter`), `table/block_based/filter_policy_internal.h:19,327` | **unconditionally** `#include "../grafite/include/grafite/grafite.hpp"` ⇒ the submodule is a hard build dependency even though README mod (c) says the policy is unused |
| (nothing) | — | `M`/`c` are never written back to RocksDB's `WriteController` rate; only the thresholds are used |

### 2.3 Evaluation harnesses

Two exist; only one is built.

**`tools/arce_bench.cc` (built).** Driven by gflags: `--compaction_style={dynamic,leveling}`,
`--read_ratio/--write_ratio`, `--buffer_size`, `--parallel`, `--test_size`, `--benchmark_file`.
Limitations that matter:
- `RunBenchmark` (`tools/arce_bench.cc:182-220`) handles `INSERT` and `READ`; the `SCAN` branch at
  line 200-202 is **empty** and `UPDATE` is not recognised at all. So **no range lookups** and
  YCSB traces containing `UPDATE` would be silently dropped.
- The workload ratio is a single constant for the whole run (`tools/arce_bench.cc:26-27`) — there
  is **no phase-changing / compound workload**, which is the paper's entire point.
- Only two policies: ArceKV and RocksDB default leveling. No Tiering/LazyLeveling/Moose.
- `num_levels` is pinned to 4 and stall triggers to `INT_MAX` (`:274-276`).
- The README's own results table (read_ratio 0.1…0.9, ArceKV vs RocksDB) is what this binary
  produces; `tmp.py` at the repo root is the 28-line scraper that turns its logs into `tmp.csv`.

**`tools/dynamic_test.cc` + `tools/dynamic_test_util.h` + `tools/dynamic_test_monitor.h` (NOT
built).** This is the harness that actually matches the paper: it reads a workload trace file with
`INSERT/UPDATE/READ/SCAN/SCANUP` records, slices it into count windows of `buffer_size /
(key+value)` updates (`tools/dynamic_test_util.h:276-288`), runs point/range/upper-bounded-range
lookups, supports `--use_continuous` (Figure 13(c)(d)), `--use_rangefilter` (Figure 13(e)(f)),
`--cache_size` (Figure 12(b)), `--parallel` (Figure 10(c)), and `--change_threshold` (Figure
11(a)). It is **commented out of the build** at `tools/CMakeLists.txt:17`.

Four things about it are worth flagging:

1. **It is probably bit-rotted.** `tools/dynamic_test_util.h:388` and `:485` call `FindBestMC(...)`
   unqualified, but the function is declared inside `namespace DynamicLookForward`
   (`include/rocksdb/dynamic_lookforward.h:7-13`) and the first argument's associated namespace is
   `DynCompaction`, so ADL will not find it and there is no `using` directive in either
   `dynamic_test_util.h` or `dynamic_test_monitor.h`. Expect a compile error on re-enabling.
   `GetMooseOptions` is commented out (`tools/dynamic_test.cc:73-91`), so the Moose/Tiering/
   LazyLeveling baselines are not reachable from here either.
2. **The workload is fed to Arce as an oracle.** At `tools/dynamic_test_util.h:431-467`, before
   window *i* finishes, the harness sets the compactioner's workload to the *true* `(r,u,p)` counts
   of window `i+1`; and `remaining_window_cnt` (`:473-479`) is computed from
   `new_workload_starts`, a list of future workload-change points precomputed over the whole trace
   in `InitWorkloadFromFile` (`:296-309`). So the system is told both what the next workload will
   be and exactly how many windows remain before it changes. The paper (§4) describes the Workload
   Statistics module as *monitoring* operations and reporting counts every 1M ops.
3. **A hand-coded special case.** `tools/dynamic_test_util.h:493-496`:
   `if (p > 0.9*(r+u+p)) { m = 5; c = 1000000; }` — i.e. for point-lookup-dominated workloads
   (sub-workload C is 98% point) the simulation result is discarded and replaced with a constant
   that disables write stalls. This is not in the paper.
4. **A leaked credential and a sudo call.** `tools/dynamic_test_util.h:555-564` (`reclaim_frag`,
   invoked every 10.24M ops from `StartProcessing:503`) shells out to
   `echo "<hard-coded password>" | sudo -S fstrim -v /tmp`. On a machine without sudo this
   `system()` call simply returns non-zero and prints "fail to trim", so it is *skippable* — but
   it means the reference runs periodically TRIMmed the SSD between phases, which we cannot
   replicate, and the password should be reported to the authors.

`tools/dynamic_test.cc:144` also hard-codes the DB path to `/tmp/db` with no flag.

### 2.4 What is missing

- **No workload generator.** Table 2's A–J mixes and the Workload I/II/III chains have no script.
  The trace format is YCSB-like (`OP key` per line, `tools/dynamic_test_util.h:247-275`), so YCSB
  or a ~100-line Python generator can produce it, but it has to be written.
- **No plotting or driver scripts** for any paper figure. The only analysis code is `tmp.py`.
- **No baselines in-tree** beyond RocksDB leveling. Moose/Tiering/LazyLeveling live in
  `NTU-Siqiang-Group/MooseLSM` (public, cited in the paper's footnote 4), CAMAL in
  `NTU-Siqiang-Group/CAMAL` (public, footnote 3), and **Ruskey is not public** — the paper says it
  "was obtained from the original authors" (footnote 2).
- **No artifact-evaluation badge.** I found no ACM/PVLDB reproducibility badge for this paper; the
  PVLDB entry carries only the "Artifact Availability" statement.

### 2.5 Build route on this machine

CMake is the **only** viable route: `src.mk` contains neither `db/dyncompactioner.cc` nor
`table/block_based/range_filter.cc`, so `make` would link-fail. CMake lists them at
`CMakeLists.txt:708` and `:835`.

Requirements and how each is met without root:

| need | evidence | status on this machine |
|---|---|---|
| cmake ≥ 3.10 | `CMakeLists.txt:35` | 3.25.1 present |
| C++17, gcc | RocksDB 9.5 | gcc 12.2.0 present |
| **OpenMP, REQUIRED** | `CMakeLists.txt:47-48`, `include/rocksdb/dynamic_lookforward.h:5` | libgomp ships with gcc 12 — fine |
| **TBB**, linked unconditionally into every tool | `tools/CMakeLists.txt:26` (`... tbb`), `tools/arce_bench.cc:13` (`<tbb/concurrent_queue.h>`) | `conda install -c conda-forge tbb tbb-devel` — note `WITH_TBB` at `CMakeLists.txt:404` defaults OFF, so `-ltbb` must be on the link line by hand or via `CMAKE_PREFIX_PATH` |
| gflags | `CMakeLists.txt:134` (ON by default on Linux) | conda-forge `gflags` |
| **grafite submodule** (+ its own `lib/sux`, `lib/sdsl-lite`) | `.gitmodules` (`git@github.com:marcocosta97/grafite.git`, **SSH**), `CMakeLists.txt:988-991`, `table/block_based/filter_policy_internal.h:19` | clone manually over HTTPS, or `git config url."https://github.com/".insteadOf git@github.com:`. Only include directories are added — no `libsdsl` link target — so header-only use via `-DSUCCINCT_LIB_SUX` is expected. **Untested; the most likely build blocker.** |
| `FAIL_ON_WARNINGS` defaults ON | `CMakeLists.txt:356` | pass `-DFAIL_ON_WARNINGS=OFF`; a research fork + gcc 12 will almost certainly warn |
| `sudo make install -j` in README | `README.md:27` | not needed — build `arce_bench` in-tree and run it from `build/tools/` |
| `sudo mount -t tmpfs` for the benchmark | `README.md:53` | not needed — point `--db_path` at `/dev/shm/...` (already a tmpfs, world-writable) or at NVMe |

No kernel module, eBPF, perf counter, KVM, hugepage, or `/proc/sys` dependency anywhere in the
build or run path. The `sudo`/`sysctl`/`Docker` grep hits in `repo_facts.json` are all in
inherited upstream RocksDB CI files (`.circleci/config.yml`, `.github/actions/...`,
`build_tools/ubuntu20_image/Dockerfile`, `tools/Dockerfile`) plus doc prose about machine
*crash/reboot* — none is on the path to building or running ArceKV.

### 2.6 Data and disk

Everything is synthetic: keys are integers in `[0, 10^10)` padded to 24 B, values are the padded
key at 1000 B (`tools/arce_bench.cc:176-215`, `tools/dynamic_test_util.h:84-104`). YCSB (Table 3)
is a public, freely downloadable generator. No proprietary trace anywhere.

Disk: paper preload 40 GiB + Workload I 74 GiB ≈ 114 GiB live, times ~1.2–1.4 space amplification
(Figure 12(d)) plus compaction transients ⇒ ~160–200 GB peak. Our ~257 GB free on `/home` fits
Workload I at full scale but leaves little headroom; Workload II (+94 GiB) is tighter. Memory:
the paper's 75 GiB cgroup cap is reproducible with the delegated cgroup-v2 `memory` controller.

---

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | The paper's PVLDB Artifact Availability block (p.1) names `github.com/NTU-Siqiang-Group/ArceKV`; the org is the last author's group (Siqiang Luo, NTU). The clone contains the real system, not a stub: the Arce cost model and score (`db/dyncompactioner.cc`), the ElasticLSM action enumeration (`include/rocksdb/dyncompactionv4.h:81-157`), the RocksDB picker (`db/compaction/compaction_picker_dynamic.cc:348-416`) and the write-stall hook (`db/column_family.cc:922-946`). **Caveat:** `README.md:2` disclaims that `main` is "a faithful implementation of ArceKV" (it is a TikTok in-memory adaptation with a simplified write-stop, one SST per run, and no range-filter policy), and the `dev` branch is a separate re-implementation using different class names. Code is released and it is the real mechanism, so this passes — but §6 records the fidelity risk. |
| `H2_no_root` | **pass** | Nothing in the build or run path needs privilege. `README.md:27` (`sudo make install`) is avoidable by running from `build/tools/`; `README.md:53` (`sudo mount -t tmpfs`) is avoidable by using `/dev/shm` or an NVMe path. The only in-code `sudo` is `tools/dynamic_test_util.h:555-564` (`sudo -S fstrim`), which lives in an unbuilt header, is called via `system()` and only prints "fail to trim" on failure. No kernel module / eBPF / `perf_event` / KVM / hugepage use; the `repo_facts.json` red flags are inherited upstream RocksDB CI and docs. |
| `H3_hardware_fit` | **pass** | CPU-only, single node, no GPU. Paper hardware is an i9-13900K / 128 GB / 1 TB NVMe (§5 p.8); our 16-core Threadripper + 125 GiB + NVMe RAID is a superset except single-thread clock. Workload I is 245.76M ops / +74 GiB on top of a 40 GiB preload ⇒ ~160–200 GB peak against ~257 GB free — fits, and any sub-scale (e.g. 10 GiB preload, 8M ops/phase) still exercises the mechanism because the count window is `F/E = 2 MiB / 1024 B ≈ 2048` updates regardless of scale. The 75 GiB memory cap is reproducible via the delegated cgroup-v2 `memory` controller. Figure 10(c)'s 16 foreground threads fit exactly on 16 cores. |
| `H4_obtainable_deps_data` | **pass** | Deps: cmake/gcc (present), OpenMP (libgomp, ships with gcc), TBB + gflags (conda-forge), grafite + sux + sdsl-lite (public GitHub, SSH URL in `.gitmodules` needs an HTTPS rewrite). All user-space. Data is fully synthetic (`tools/arce_bench.cc:176-215`); YCSB for Table 3 is public. No proprietary trace. The workload *generator* for Table 2 / Workloads I–III is absent from the repo — that is missing tooling to be written, not unobtainable data. |

No `fail`, no `unclear`.

---

## 4. Reproduction plan

**Target.** Figure 9 (left table), Workload I, the **ArceKV-vs-1-Leveling ratio on the
point-lookup/update-only sub-workloads B (98% update) and C (98% point)**: the paper reports
ArceKV 10.60× / 3.08× against 1-Leveling 2.29× / 2.60×, i.e. ArceKV should be ≈**4.6× faster than
RocksDB default leveling under B** and roughly **on par (≈1.2×) under C**. These two are reachable
with the binary that actually builds (`tools/arce_bench.cc`), since neither contains range lookups.
The supporting claim is the paper's core one: a single elastic policy beats a fixed structure at
*both* ends of the read/write spectrum. Secondary, cheaper target: the repo's own README table
(`README.md:67-86`), ArceKV vs RocksDB at read_ratio 0.1…0.9, which `tools/arce_bench.cc` + the
`tmp.py` scraper reproduce directly and which serves as a build-correctness smoke test.

**Scale-down.**
- Preload 10 GiB instead of 40 GiB; 8M ops per phase instead of 40.96M (≈1/5 scale). Keep
  key = 24 B, value = 1000 B, write buffer = 2 MB, Bloom = 10 bpk, `num_levels = 4`,
  `simulation_iter = 400` — all as §5 specifies, so the count window and the `(M,c)` search space
  are unchanged.
- DB on `/home` NVMe (not `/dev/shm`) so that compaction I/O is real, as in the paper.
- Cap RSS at ~16 GiB with a cgroup-v2 `memory.max` on the user slice (same 1:5 memory:data ratio
  the paper's 75 GiB : ~380 GiB-of-traffic setup implies at full scale).
- Single foreground thread, RocksDB default background jobs — matching §5's "one background
  compaction thread and one flush thread".

**Steps.**
1. Fetch `grafite` over HTTPS (`git config url."https://github.com/".insteadOf git@github.com:`
   then `git submodule update --init --recursive`); verify `grafite/include/grafite/grafite.hpp`,
   `grafite/lib/sux`, `grafite/lib/sdsl-lite/include` exist.
2. `conda create` an env with `gflags`, `tbb`, `tbb-devel`; configure
   `cmake .. -DCMAKE_BUILD_TYPE=Release -DFAIL_ON_WARNINGS=OFF -DWITH_TESTS=OFF
   -DWITH_ALL_TESTS=OFF -DWITH_BENCHMARK_TOOLS=OFF -DWITH_GFLAGS=ON`; `make -j16 arce_bench`.
   Budget real time here for grafite/sdsl header issues and for gcc-12 warnings in a RocksDB 9.5
   fork.
3. Smoke test: reproduce two rows of `README.md:67-86` (`--read_ratio=0.1` and `--read_ratio=0.9`,
   dynamic vs leveling) at reduced `--test_size`, parse with `tmp.py`. If ArceKV's write latency
   is not several-fold below leveling at read_ratio 0.1, the build or the `(M,c)` agent is broken.
4. Patch `tools/arce_bench.cc` minimally: (a) map `UPDATE` to `Put` in `RunBenchmark:186-217`;
   (b) add a `--preload_bytes` flag doing the sequential 10 GiB load; (c) add a `--phases` flag
   that switches `rratio/wratio` in `WorkloadGenerator` and calls
   `opt.comp_controller->set_workload(...)` (`include/rocksdb/advanced_options.h:88-104`) at each
   boundary — this is the minimal path to a *compound* workload without resurrecting
   `dynamic_test.cc`.
5. Run phases B and C back to back (B: 1% point / 98% update / 1% range→0; C: 98% point /
   1% update) for `--compaction_style=dynamic` and `=leveling`; compute the throughput ratio.
6. Optional, for the full Figure 9: un-comment `tools/CMakeLists.txt:17`, fix the `FindBestMC`
   namespace-lookup break in `tools/dynamic_test_util.h:388,485`, make the `/tmp/db` path in
   `tools/dynamic_test.cc:144` a flag, stub out `reclaim_frag()`, and write a Table-2 workload
   generator. Only then are range lookups and the A/D/J/E phases in play.
7. Optional, for the baselines: clone `NTU-Siqiang-Group/MooseLSM` and `NTU-Siqiang-Group/CAMAL`
   separately. Ruskey cannot be obtained.

**Effort.** ≈**8 person-days + ~60 machine-hours** (no GPU). Roughly: 2 days on build/grafite/TBB,
1 day on the `arce_bench` patches, 1 day on the workload generator and run scripts, 2 days of
runs + analysis, 2 days of slack. Full-scale Workload I runs are ~1.5–4 h per method (Figure 10's
timeline shows ArceKV at ~1016 s for 50M ops, RKY ~3358 s), so the 1/5 scale-down brings a
two-method comparison to well under a day.

**Level: M.** Not **H** because: the paper-matching harness is excluded from the build
(`tools/CMakeLists.txt:17`) and does not compile as written; there is no workload generator, no
plotting script, and no run driver; the binary that does build lacks range lookups and phase
changes; the grafite submodule is an untested hard dependency reachable only after a URL rewrite;
and the README explicitly disclaims that `main` is a faithful ArceKV. Not **L** because the entire
decision engine, picker and write-stall hook are present and legible, the build is plain CMake
with user-space-installable dependencies, the machine comfortably exceeds the paper's, the data is
synthetic, and the repo ships its own quantitative result table to check the build against.

---

## 5. Add-on ideas

### A. Oracle-free workload estimation ("does ArceKV still win when it has to *learn* the shift?")

**Hypothesis.** We hypothesize that replacing ArceKV's supplied next-window workload tuple and
known change-point horizon with an *online* estimator (EWMA over completed count windows +
CUSUM/Page-Hinkley change detection + a hazard-rate estimate of the remaining horizon) costs
**less than 20% of the reported speedup on gradual shifts (Workload II) but substantially more on
abrupt shifts (Workload I, B→D)**, measured as normalized average throughput and as
time-to-restabilise after a phase boundary, compared with the paper's system.

**Mechanism.** (1) Add a foreground counter that accumulates `(r,u,p)` per completed count window
and exposes a smoothed estimate; (2) replace the `set_workload(...)` call that currently receives
the *next* window's ground truth with that estimate; (3) replace `remaining_window_cnt` — today a
lookup into a precomputed list of future change points — with an online hazard estimate
(e.g. mean observed phase length, reset on detection); (4) delete the
`if (p > 0.9*(r+u+p)) { m=5; c=1000000; }` override; (5) report both variants side by side so the
oracle gap is the measurement.

**Code locations.**
- `tools/dynamic_test_util.h` (lines 431–467 set the next window's true `(r,u,p)`; 473–479 derive
  `remaining_window_cnt` from `new_workload_starts`; 296–309 precompute the change points;
  493–496 the hard-coded override)
- `include/rocksdb/advanced_options.h` (`set_workload`, lines 88–104 — where an estimator would
  feed in)
- `include/rocksdb/dyncompactionv4.h` (`need_reset_Mc`, lines 250–263 — today drift is detected on
  average run count only, never on the workload tuple)
- `db/dyncompactioner.cc` (`FindBestMC` / `get_cost_for_mc`, lines 129–235 — consume
  `remaining_window_cnt`)
- `tools/arce_bench.cc` (the harness that actually builds; needs the phase-switching flag)

**Motivating evidence.** The paper's §4 describes Workload Statistics as *monitoring* operations
and reporting counts every 1M ops, and §5.1 credits ArceKV with adapting "within 20 million
operations" (Figure 10(a)(b)). But the only paper-shaped harness in the repo hands the engine the
true composition of the *next* window before that window runs
(`tools/dynamic_test_util.h:431-467`) and tells it exactly how many windows remain until the next
shift (`:473-479`, from `:296-309`). `remaining_window_cnt` is a first-class input to the cost
integral (`db/dyncompactioner.cc:152-156`, where the simulation horizon is clamped to it), so it
is not a cosmetic parameter. The paper's Figure 9 table never separates "adapted because it
measured the change" from "adapted because it was told". Either outcome is informative: if the gap
is small, the paper's claim is robustly re-confirmed; if it is large, the headline 2.17–2.92×
needs an asterisk.

**Feasibility: M.** The estimator itself is small (~300–500 LOC) and local. The cost is the
harness: either resurrect `tools/dynamic_test.cc` (fix the `FindBestMC` namespace break, unpin
`/tmp/db`, stub `reclaim_frag`) or extend `tools/arce_bench.cc` with phase switching, plus write a
Table-2 workload generator. Runs are CPU/NVMe only and fit easily at 1/5 scale.

**Research value: H.** It tests the validity of the paper's central claim rather than adding a
feature, it is the kind of question a VLDB reviewer asks first about any "adaptive" system, and
the hard-coded `p > 0.9` override found at `tools/dynamic_test_util.h:493-496` makes the question
sharper. It also produces a reusable artefact (an online workload estimator) that any of the other
add-ons can build on.

**Scoop check: `clear`.** Queries: "ElasticLSM Arce compaction follow-up citing ArceKV 2026";
"LSM-tree compaction online workload prediction change-point detection adaptive compaction 2026";
"ArceKV workload-driven LSM compactions VLDB 2026 artifact". No work citing ArceKV was found
(the arXiv version is 2508.03565, Aug 2025; PVLDB issue is 19(5), 2026). The closest neighbours
are [Endure](https://www.vldb.org/pvldb/vol15/p1605-huynh.pdf) (robust tuning under workload
*uncertainty*, but for a static structure and offline) and
[SA-LSM](https://www.vldb.org/pvldb/vol15/p2161-zhang.pdf) (survival analysis to detect workload
properties for data layout, not compaction scheduling). Neither audits an oracle assumption in a
score-based elastic compactor.

---

### B. Key-range-overlap-aware action enumeration

**Hypothesis.** We hypothesize that extending ElasticLSM's candidate set with *partial,
key-range-scoped* compactions — and charging them a cost proportional to overlapping bytes rather
than to whole-run bytes — reduces write amplification (compacted GB, Figure 9(b)) by **≥30% at
equal or better read latency** under skewed update workloads (YCSB-A/D Zipfian, and the
multi-version hot-key workload of §5.3), compared with the paper's system.

**Mechanism.** ArceKV's three patterns are all *whole-run*: P1 takes k smallest runs of a level,
P2/P3 take **all** runs of levels i…j. Candidate cost is `compaction_size` = the sum of run sizes,
scaled by a constant `rw_ratio/4096` (`include/rocksdb/dyncompactionv4.h:147-156`). Key ranges are
never consulted, even though §3.1 states a run carries "a timestamp, size, and key range". The
change: (1) store per-run `[smallest_key, largest_key]` in `TreeState` (available from RocksDB's
`FileMetaData`); (2) in `EnumerateActions`, emit additional candidates restricted to a key
sub-range, with `compaction_size` = estimated *overlapping* bytes and `reward` (run reduction)
discounted to the fraction of the key space cleared; (3) in the picker, translate a ranged action
into `CompactionInputFiles` by intersecting with `vstorage_->LevelFiles(i)` instead of taking
whole levels; (4) relax the 100 GiB output-file cap so a partial compaction can emit multiple SSTs.

**Code locations.**
- `include/rocksdb/dyncompactionv4.h` (`TreeState`, lines 53–58; `EnumerateActions`, 81–157;
  `DynAction::removed_files` bitmap, 18–51)
- `db/dyncompactioner.cc` (`get_reward_for_action`, 30–62; `apply_to_tree`, 70–111 — the
  simulation must model partial merges too)
- `db/compaction/compaction_picker_dynamic.cc` (`GetCurrentStateForCompactedAction`, 46–66, to
  carry key ranges; `PickCompactionActionV3`, 348–416, and the `max file size` at line 404)

**Motivating evidence.** The paper's cost model (Eq 1–5) is purely a function of the *number* of
runs `s` and the *bytes* `X`; key ranges enter nowhere. §5.2 "Space Amplification" reports ArceKV
0.05 above Leveling only because "lookup-driven compactions still merge overlapping runs" — an
incidental effect, not a designed one. Figure 9(b) shows ArceKV's compacted bytes are comparable
to the eager baselines on Workload I, i.e. the flexibility buys latency, not write amplification.
And the `main` branch makes this worse by design: `db/compaction/compaction_picker_dynamic.cc:404`
caps output files at 100 GiB so every run is a single SST, meaning a P2 compaction of a large
level rewrites the whole level even when only a thin key band was updated — exactly the regime of
§5.3's 1M-hot-key MVCC workload and of YCSB-A/D.

**Feasibility: M.** Cross-cutting: it touches the state representation, the enumerator, the
simulation's `apply_to_tree`, and the picker's file selection, and the candidate set grows, so the
pruning heuristics of §3.1/§4 need revisiting to keep the 30 µs decision budget. Still ~1–2k LOC
in four files, all in one repo, evaluable on this machine with YCSB traces.

**Research value: H.** It attacks the paper's own simplifying assumption head-on (ElasticLSM is
"a flexible collection of sorted runs, each tagged with … key range", yet the key range is never
used), and it is the axis on which RocksDB's production picker — which is entirely
key-range-driven — beats naive whole-level merging. A negative result is also publishable inside
the project: it would say the run-count abstraction is sufficient and the enumeration cost of
range-awareness is not worth it.

**Scoop check: `partial`.** Range-partitioned / overlap-aware compaction is standard in RocksDB's
leveled picker and is studied in e.g.
[EcoTune, "Rethinking The Compaction Policies in LSM-trees", SIGMOD 2025](https://people.iiis.tsinghua.edu.cn/~huanchen/publications/ecotune-sigmod25.pdf),
and partitioning by overlapping key ranges appears in
[DownForce/DF-Compaction, ICPP 2025](https://dl.acm.org/doi/10.1145/3754598.3754675). No work
integrates key-range-scoped candidates into ArceKV's *unconstrained, score-ranked* action space
under dynamic workloads, and nothing citing ArceKV was found.

---

### C. Concurrent compaction: choose action *sets*, not single actions

**Hypothesis.** We hypothesize that letting Arce select a *set* of non-conflicting compactions for
multiple background workers — and modelling worker occupancy in the short-term penalty instead of
the current Amdahl fudge factor — improves throughput under 8–16 foreground threads (the regime of
Figure 10(c)) by **≥25%** over ArceKV with the same number of background workers, compared with
the paper's system.

**Mechanism.** Today `GetBestAction` returns one `DynAction`
(`include/rocksdb/dyncompactionv4.h:188-208`), and the picker **bails out entirely** —
`return nullptr` — if *any* file in levels `[start_level, output_level]` is already
`being_compacted` (`db/compaction/compaction_picker_dynamic.cc:383-387`). So a second background
worker is effectively starved whenever the first is busy in overlapping levels. The change:
(1) make `EnumerateActions` exclude in-flight runs and emit disjoint candidates; (2) add a greedy
set-selection pass that repeatedly picks the highest-scoring action disjoint from those already
scheduled, until workers are exhausted; (3) replace the `parallel_factor > 1 ⇒ factor /= 2`
heuristic (`db/dyncompactioner.cc:21-24`, `40-43`; mirroring §4's Amdahl φ = 0.5) with an explicit
model of `w` workers and their aggregate I/O share; (4) fix the latent index mismatch between the
`being_compacted`-filtered state built at
`db/compaction/compaction_picker_dynamic.cc:46-66` and the unfiltered `LevelFiles` indexing at
`:374-396`.

**Code locations.**
- `db/compaction/compaction_picker_dynamic.cc` (lines 348–416, especially the `being_compacted`
  bail at 383–387 and the state/index mismatch with 46–66)
- `include/rocksdb/dyncompactionv4.h` (`GetBestAction`, 188–208; `EnumerateActions`, 81–157)
- `db/dyncompactioner.cc` (`get_win_acc_ios` parallel factor, 7–28; `get_reward_for_action`,
  30–62; `get_cost_for_mc`, 129–197)
- `tools/dynamic_test_util.h` (`ProcessWindowInParallel`, 210–231 — the multi-thread harness)

**Motivating evidence.** §4 "Multi-threading Extension" claims ArceKV "tracks available compaction
threads … applying a large penalty when resources become saturated", but §5 fixes the
configuration to "one background compaction thread and one flush thread", and Figure 10(c)
explicitly says "the Moose framework does not support multiple background workers, so we fix the
number of background threads to one and vary only the number of foreground query threads". So the
paper's own multi-worker mechanism is never evaluated. Meanwhile the code shows the mechanism is
not merely unevaluated but structurally blocked by the `nullptr` bail-out. On a 16-core machine
with a fast NVMe, a single compaction worker is the obvious bottleneck for write-heavy phase B.

**Feasibility: M.** The picker and scorer changes are contained, but the evaluation needs the
multi-threaded harness (`ProcessWindowInParallel`), which lives in the unbuilt
`tools/dynamic_test.cc` path, and concurrency bugs in a modified RocksDB compaction picker are
time sinks. Compute is cheap and local.

**Research value: M.** "More compaction parallelism helps on a 16-core box" is a fairly expected
outcome, and pipelined/parallel compaction has an existing literature. The genuinely interesting
part — does a *greedy single-action* score remain near-optimal once several actions execute
concurrently, or does the domination argument of Lemma 3.3 break? — is real but narrower than A
or B.

**Scoop check: `partial`.**
[DownForce: "Revisiting Multi-threaded Compaction in LSM-trees: Enabling Compaction Pipelining",
ICPP 2025](https://dl.acm.org/doi/10.1145/3754598.3754675) pipelines and parallelises compaction
tasks split by overlapping key ranges, which overlaps with the *mechanism* but not with the
question of multi-action selection inside a score-based elastic action space under dynamic
workloads. Nothing citing ArceKV found.

---

### D. A space-amplification and delete-aware term in the effectiveness score

**Hypothesis.** We hypothesize that adding a garbage-ratio term (duplicate + tombstone bytes per
run) to Arce's effectiveness score `E(s,t,y)` reduces peak space amplification by **≥20%** on
update- and delete-heavy dynamic workloads at **<10% throughput loss**, compared with the paper's
system.

**Mechanism.** Eq 11 trades run-count reduction against read slowdown and stall penalty; nothing
represents reclaimable bytes, and `DynAction` carries no notion of garbage
(`include/rocksdb/dyncompactionv4.h:18-51`). The change: (1) carry per-run `num_entries`,
`num_deletions` and the key-range overlap fraction into `TreeState` from RocksDB's `FileMetaData`;
(2) add a third term `M_s · E_g(action)` to `get_reward_for_action`, where `E_g` estimates bytes
reclaimed; (3) extend the `FindBestMC` grid with the new weight `M_s` (it currently searches only
`M ∈ {5..95}` × `c`, `db/dyncompactioner.cc:211-215`); (4) extend `apply_to_tree`
(`db/dyncompactioner.cc:70-111`) so the simulated post-compaction run size shrinks by the
reclaimed bytes rather than being the plain sum of inputs; (5) add a `DELETE` op to the benchmark
and report DB size over time alongside latency.

**Code locations.**
- `db/dyncompactioner.cc` (`get_reward_for_action`, 30–62; `apply_to_tree`, 70–111; `FindBestMC`
  grid, 199–235)
- `include/rocksdb/dyncompactionv4.h` (`DynAction`, 18–51; `TreeState`, 53–58)
- `db/compaction/compaction_picker_dynamic.cc` (`GetCurrentStateForCompactedAction`, 46–66 — the
  only place `FileMetaData` is read)
- `tools/arce_bench.cc` (`RunBenchmark`, 182–220 — add `DELETE`; `BenchmarkListener`, 222–256 —
  add a size/space-amplification probe)

**Motivating evidence.** §5.2 "Space Amplification" states outright that "ArceKV focuses on read
and write performance rather than space efficiency" and reports Figure 12(d) as a reassurance,
not a design goal — and the reassurance is measured on sub-workload J (uniform 33/33/33) with no
deletes anywhere in Table 2's A–J. §5.3's MVCC case study shows the one regime where garbage
matters (1M hot keys, long version chains) and reports that ElasticLSM "converges to Leveling-like
behavior" there *by accident*, because small incoming runs happen to get low penalties — not
because the score knows about duplicates. A workload with deletes (or a tighter disk budget, which
is exactly our 257 GB situation) is an unexplored regime where an unconstrained action space could
plausibly do much worse than a structured one.

**Feasibility: H.** Fully localized: two headers and one `.cc` for the engine, plus a handful of
lines in `tools/arce_bench.cc` — the harness that *already builds* — for the DELETE op and the
size probe. `FileMetaData` already carries `num_entries`/`num_deletions`, so no new bookkeeping in
the storage engine. Well inside 1–2k LOC and a 10-week budget for 2–4 students, with cheap runs.

**Research value: M.** Delete-aware compaction is well trodden — [Lethe (SIGMOD
2020)](https://dl.acm.org/doi/10.1145/3318464.3389757) introduced FADE/KiWi for exactly this — so
the *direction* is expected. What is new is putting a space term inside an unconstrained,
score-ranked action space where the system is free to defer compactions indefinitely
(`c` can be set to 10^6, `tools/dynamic_test_util.h:495`), which is a genuinely more dangerous
setting than a fixed-structure LSM. Solid but not surprising.

**Scoop check: `partial`.** [Lethe: A Tunable Delete-Aware LSM
Engine](https://dl.acm.org/doi/10.1145/3318464.3389757) covers delete persistence and space
amplification for a fixed-structure LSM;
[Scavenger+ (2025)](https://arxiv.org/pdf/2508.13935) revisits space–time tradeoffs for key-value
separated LSM-trees. Neither addresses ElasticLSM's unconstrained action space, and no work citing
ArceKV was found.

---

## 6. Risks and open questions

1. **Fidelity of the released code to the paper — the dominant risk.** `README.md:2` states in the
   first line that `main` "does not represent a faithful implementation of ArceKV". Concretely:
   the stall rate `k` is a compile-time constant (`db/dyncompactioner.cc:5`, `kStallCost = 4`)
   rather than a searched parameter (the paper initialises `k = 6` and doubles it twice, §4), so
   `FindBestMC` searches `(M, c)` only (`db/dyncompactioner.cc:211-215`) — Algorithm 1 in the
   paper searches `(M, c, k)`. Every compaction emits one 100 GiB-capped SST
   (`db/compaction/compaction_picker_dynamic.cc:404`). The simulation uses OpenMP, not the
   Eigen/SIMD vectorisation §4 describes. The `dev` branch is a *third* codebase with different
   class names (`kCompactionStyleArce`, `ArceCompactionController`) and a `claude_md/` directory.
   **Before committing the project, ask the authors which commit produced Figure 9.**
2. **`tools/dynamic_test.cc` — the only paper-shaped harness — is not in the build and likely does
   not compile.** `tools/CMakeLists.txt:17` comments it out; `tools/dynamic_test_util.h:388,485`
   call `FindBestMC` unqualified while it is declared in `namespace DynamicLookForward`
   (`include/rocksdb/dynamic_lookforward.h:7-13`) with no `using` in scope and no ADL path.
   Budget time for repair, and treat "we could not build the paper's harness" as a possible
   finding in itself.
3. **Oracle workload signal.** See add-on A: the harness supplies the *next* window's true
   `(r,u,p)` and the exact number of windows until the next shift
   (`tools/dynamic_test_util.h:431-479`, `:296-309`). If the paper's numbers were produced this
   way, "adapts within 20M operations" (Figure 10) measures the compaction engine, not the
   adaptation loop.
4. **Hard-coded special case.** `tools/dynamic_test_util.h:493-496` overrides the simulation with
   `m = 5, c = 1000000` whenever point lookups exceed 90% of the mix — precisely sub-workload C
   (98% point). Any re-run must report results with and without this branch.
5. **Leaked sudo password.** `tools/dynamic_test_util.h:557` embeds a plaintext password for
   `sudo -S fstrim -v /tmp`, called every 10.24M ops (`:503`). Harmless here (no sudo ⇒ the
   `system()` call just fails and prints), but it (a) should be reported to the authors and (b)
   means the reference environment periodically TRIMmed the SSD between phases — a confound for
   long write-heavy runs on our NVMe that we cannot replicate.
6. **grafite is an unconditional build dependency.** `table/block_based/filter_policy_internal.h:19`
   includes `../grafite/include/grafite/grafite.hpp` with no guard, and that header is pulled in
   across the table layer. `.gitmodules` uses an SSH URL, and grafite itself nests `lib/sux` and
   `lib/sdsl-lite`. `CMakeLists.txt:988-991` adds include directories but no link target, implying
   header-only use under `-DSUCCINCT_LIB_SUX` — **unverified**, and the most likely place the
   build stops. There is no configure switch to disable the range filter.
7. **TBB is linked into every tool unconditionally** (`tools/CMakeLists.txt:26`) while
   `WITH_TBB` defaults OFF (`CMakeLists.txt:404`); a bare `cmake ..` may fail to find `-ltbb`
   unless the conda prefix is on the link path.
8. **`FAIL_ON_WARNINGS` is ON by default** (`CMakeLists.txt:356`) — a research fork of RocksDB 9.5
   compiled with gcc 12.2 will very likely need `-DFAIL_ON_WARNINGS=OFF`.
9. **Baseline coverage is incomplete by construction.** Ruskey is not public (paper footnote 2:
   "obtained from the original authors"), so one of the eight Figure 9 rows is unreproducible.
   Moose/Tiering/LazyLeveling require the separate MooseLSM repo; CAMAL a third repo. A faithful
   Figure 9 means building three codebases, not one.
10. **Fixed-size action bitmaps and `num_levels = 4`.** `DynAction::removed_files` is allocated as
    20×100 ints per action (`include/rocksdb/dyncompactionv4.h:19`) and every candidate copies it;
    with `c` allowed to reach 10^6 the run count can grow far past 100 per level, which is both a
    correctness hazard and an allocation cost inside the 30 µs decision budget the paper claims
    (§3.1). Any scale-up experiment should assert on these bounds.
11. **Disk headroom.** Full-scale Workload II (40 GiB preload + 94 GiB inserted, times ~1.2–1.4
    space amplification, plus compaction transients) is uncomfortably close to the ~257 GB free on
    `/home`, especially with ArceKV free to defer compactions. Use the scale-down in §4 and watch
    `df` during runs.
12. **Single-thread clock.** The paper's i9-13900K boosts to 5.4 GHz; our Threadripper PRO 5955WX
    is a Zen 3 part at a lower clock. Absolute latencies will be higher; only the *ratios* between
    ArceKV and its baselines are meaningful, which is what Figure 9 reports anyway.
13. **No artifact badge found**, so there is no independent evidence that anyone outside the author
    group has rebuilt these results.

---

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; `pages/page-NN.png` for figures)
- p.1 Abstract + PVLDB Artifact Availability (repo URL) + §1 Introduction (dynamic-workload gap,
  Meta/Netflix motivation, claimed 2.17×–2.92×)
- p.2 Table 1 (ElasticLSM vs Dostoevsky/Ruskey/Moose); "Our Vision"; contributions
- p.3 §2.1 LSM background, Figure 1; §2.2 write-stall controller; §2.3 open challenges
- p.4 Figure 2 (greedy vs lazy vs Ruskey vs ElasticLSM transition table); §3.1 patterns P1/P2/P3,
  pruning, "<8 levels", "30 µs" decision time
- p.5 Figures 3–5 (count window, tree state); §3.2 Eq 1–6 cost model
- p.6 §3.3 Eq 7–11, Lemma 3.2 (NP-hardness), Figure 6 (domination frontier)
- p.7 Algorithm 1 `FindBestParams(M,c,k)`; Lemma 3.3; §3.4 parameter selection, `d = 0.1`
- p.7–8 Figure 7 (architecture); §4 parallel simulation (16 threads, Eigen/SIMD), parameter
  pruning (`M` step 5, `c` step 2, `k` init 6, `MaxIterTime = 400`), multi-threading extension
  (Amdahl, φ = 0.5)
- p.8 §5 hardware (i9-13900K/128 GB/1 TB NVMe, 75 GiB cgroup cap), baselines, implementation
  settings (24 B key / 1000 B value / 10 bpk / 2 MB buffer / `num_levels = 4` / `I_w = 15 µs` /
  `I_r = 12 µs`), footnotes 2–4 (Ruskey private; CAMAL and MooseLSM repos), Table 2 (A–J mixes)
- p.9 **Figure 8** (avg + P99.9 latency), **Figure 9** (normalized throughput table; write stall;
  compacted bytes; run count; read I/O), Workload I/II/III definitions, 40 GiB preload
  — image read: `pages/page-09.png`
- p.10 §5.1 discussion; Figure 10(a)–(d) (stabilisation, 1/4/8/16 threads, industrial systems);
  Table 3 (YCSB A–F)
- p.11 §5.2 recompute threshold `d`, MaxIterTime, cost-model validation (Figure 11(c)(d)),
  Figure 12 (buffer/cache/entry size, space amplification, background cost)
- p.12 §5.3 case studies (MVCC, continuous workload, Grafite range filter); §6 related work; §7
  conclusion
- p.13 refs [1] technical report (arXiv 2508.03565), [21] Grafite, [39] Eigen, [58] Moose,
  [64] Ruskey, [98] CAMAL

**Repository** (paths relative to `repo/`)
- `README.md` (fidelity disclaimer :2; `dev`-branch note :4; key modifications :6-15; deps :17-21;
  build :23-28; `GetDynamicOptions` example :30-47; tmpfs benchmark :49-63; results table :65-86;
  WIP list :88-91)
- `include/rocksdb/version.h:14-16` (RocksDB 9.5.0)
- `include/rocksdb/advanced_options.h` (`AdaptiveCompactionController` :38-170; `set_workload`
  :88-104; `find_first_mc_when_ready` :106-136; `start_tuning_agent` :138-169;
  `kCompactionStyleDynamic` :183; `comp_controller` field :1243)
- `include/rocksdb/dyncompactionv4.h` (`DynAction` :18-51; `TreeState` :53-58;
  `EnumerateActions` :81-157; `DynamicCompactioner` :160-266; `GetBestAction` :188-208;
  `state_change_threshold` :167; `need_reset_Mc` :250-263)
- `include/rocksdb/dynamic_lookforward.h` (OpenMP include :5; `FindBestMC` declaration :7-14)
- `db/dyncompactioner.cc` (`kStallCost = 4` / `kStoppedCost = 1e10` :5-6; `get_win_acc_ios` :7-28;
  `get_reward_for_action` :30-62; `apply_to_tree` :70-111; `get_best_action_with_forward` :113-127;
  `get_cost_for_mc` :129-197; `FindBestMC` + OpenMP 16 threads :199-235)
- `db/compaction/compaction_picker_dynamic.cc` (`NeedsCompaction` :12-15;
  `GetCurrentStateForCompactedAction` :46-66; dead V1/V2/V3 variants :117-346;
  `PickCompactionActionV3` :348-416, `being_compacted` bail :383-387, 100 GiB file cap :404;
  `PickCompaction` :441-461)
- `db/compaction/compaction_picker_dynamic.h`
- `db/column_family.cc` (`DynamicWriteStallCause` :922-936; dispatch :938-946; total-run
  computation :982-994)
- `tools/arce_bench.cc` (flags :17-28; `WorkloadGenerator` :32-119; `RunBenchmark` :182-220 with
  the empty `SCAN` branch :200-202; `BenchmarkListener` :222-256; `GetBasedOptions` :258-268;
  `GetDynamicOptions` :270-284; `GetLevelingOptions` :286-290)
- `tools/dynamic_test.cc` (flags :12-29; `GetBasedOptions` + range filter :49-71; commented
  `GetMooseOptions` :73-91; `GetDynamicOptions` :93-106; `GetLevelingOptions` :108-118;
  hard-coded `/tmp/db` :144)
- `tools/dynamic_test_util.h` (op implementations :84-184; `ProcessWindow` :186-208;
  `ProcessWindowInParallel` :210-231; `InitWorkloadFromFile` / window slicing :240-353, change
  points :296-309; `StartProcessing` :356-511, oracle next-window workload :431-467,
  `remaining_window_cnt` :473-479, `p > 0.9` override :493-496, `reclaim_frag` call :503;
  `reclaim_frag` with sudo password :555-564)
- `tools/dynamic_test_monitor.h` (`DynamicTestListener` :38-89)
- `tools/CMakeLists.txt` (`arce_bench.cc` :14; `# dynamic_test.cc` :17; unconditional `tbb`
  link :26)
- `CMakeLists.txt` (`find_package(OpenMP REQUIRED)` :47-48; `WITH_GFLAGS` default :131-135;
  `FAIL_ON_WARNINGS` :356; `WITH_TBB` default OFF :404-408; `db/dyncompactioner.cc` :708;
  `table/block_based/range_filter.cc` :835; grafite include dirs + SUCCINCT defines :988-991;
  `WITH_TOOLS` :1194)
- `table/block_based/range_filter.cc` (grafite serialisation :14-24; `NewDynamicRangeFilter`
  :26-28)
- `table/block_based/filter_policy_internal.h` (unconditional grafite include :19; `grafite::filter`
  member :327)
- `include/rocksdb/filter_policy.h:211` (`NewDynamicRangeFilter`)
- `src.mk` (contains neither `dyncompactioner.cc` nor `range_filter.cc` ⇒ Makefile route unusable)
- `.gitmodules` (grafite over SSH), `tmp.py` (log scraper), `tmp.csv`
- `repo_facts.json` (HEAD `04371f7`, 2026-04-29; 2089 files; red-flag hits, all in upstream
  RocksDB CI/docs)

**External**
- [PVLDB entry, ArceKV, 19(5)](https://dl.acm.org/doi/10.14778/3796195.3796208) and
  [PDF](https://www.vldb.org/pvldb/vol19/p958-liu.pdf) — artifact URL confirmation, no badge
- [arXiv 2508.03565 (extended version / technical report)](https://arxiv.org/abs/2508.03565)
- [ArceKV `dev` branch on GitHub](https://github.com/NTU-Siqiang-Group/ArceKV/tree/dev) —
  `kCompactionStyleArce`, `ArceCompactionController`, `claude_md/`, multi-SST runs
- [Lethe: A Tunable Delete-Aware LSM Engine, SIGMOD 2020](https://dl.acm.org/doi/10.1145/3318464.3389757)
- [Revisiting Multi-threaded Compaction in LSM-trees (DownForce), ICPP 2025](https://dl.acm.org/doi/10.1145/3754598.3754675)
- [Rethinking The Compaction Policies in LSM-trees (EcoTune), SIGMOD 2025](https://people.iiis.tsinghua.edu.cn/~huanchen/publications/ecotune-sigmod25.pdf)
- [Endure, PVLDB 15(8)](https://www.vldb.org/pvldb/vol15/p1605-huynh.pdf)
- [SA-LSM, PVLDB 15(10)](https://www.vldb.org/pvldb/vol15/p2161-zhang.pdf)
- [Scavenger+, arXiv 2508.13935](https://arxiv.org/pdf/2508.13935)
