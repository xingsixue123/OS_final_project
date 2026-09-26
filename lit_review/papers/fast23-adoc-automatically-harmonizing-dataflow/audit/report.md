# ADOC: Automatically Harmonizing Dataflow Between Components in Log-Structured Key-Value Stores for Improved Performance

FAST '23 · Jinghuan Yu (CityU HK), Sam H. Noh (UNIST/Virginia Tech), Young-ri Choi (UNIST), Chun Jason Xue (CityU HK)
Repo audited: `https://github.com/supermt/FEAT_7.11` @ `5ed60f5` (2023-03-06)

## 1. Paper summary

**Problem.** LSM-KV stores (RocksDB) suffer *write stalls* — sudden throughput collapses under
write pressure (paper Figure 1, p.2). Prior work blames one cause each: CPU/bandwidth
exhaustion, L0–L1 compaction serialization, or deep-level compaction contention.

**Observation.** §3 re-runs `fillrandom` on four device classes (PM, NVMe SSD, SATA SSD, SATA
HDD; Table 1, p.5) sweeping thread count 2–20 and batch size 64 MB/512 MB, and shows each prior
explanation fails somewhere (Table 2, p.5, limitations L1–L5). Key counter-evidence: stalls occur
with idle CPU *and* spare bandwidth (Figure 5, p.6 shows a large unused-bandwidth gap on NVMe/PM;
Figure 10, p.9 shows stalls at flat, low CPU and disk utilization).

**Key idea.** §4 generalizes "disk overflow" into **data overflow** — rapid expansion of one LSM
component because the producing rate exceeds the consuming rate. Three kinds (Figure 9, p.8):
- **MMO** (memory overflow): input rate > flush rate ⇒ MT stall.
- **L0O**: flush rate > L0–L1 compaction rate ⇒ L0 stall.
- **RDO** (redundancy overflow): redundant-data generation > deep-level compaction ⇒ PS stall
  (RocksDB defaults: soft 64 GB / hard 128 GB pending compaction bytes, §2.3).

**Design (§5).** ADOC is an online AIMD controller that wakes every `Tw = 1 s`, classifies the
current overflow, and turns exactly two knobs: **total background thread count** and **batch
size** (memtable size, which is mirrored into `target_file_size_base` and
`max_bytes_for_level_base`). Responses: MMO ⇒ fewer threads + bigger batch; L0O ⇒ more threads,
batch unchanged; RDO ⇒ more threads + smaller batch. Priority order L0O > RDO > MMO. AIMD: +2
threads / +64 MB batch on increase, halve on decrease. Flush threads stay at ¼ of total, as in
stock RocksDB. Claimed footprint: ~300 LOC (250 tuner + 50 stats).

**Evaluation setup (§3.1, §6.1).** 2× Xeon Gold 6230 (40 cores), 128 GB DRAM, Ubuntu 18.04, four
devices. `db_bench fillrandom`, 16 B key / 1000 B value, 3600 s, 3 runs averaged. Schemes (Table 3,
p.10): RocksDB-DF, RocksDB-AT (auto-tuned rate limiter), SILK-D/-P/-O (SILK on RocksDB 5.7.1,
"-O" = exhaustively hand-tuned to 8 threads / 512 MB), ADOC on RocksDB v7.5.3. Macro: YCSB
load + A,B,C,D,F then reload + E (Table 4, p.12), 50 M entries of 10 B key / 1000 B value.

**Headline numbers.**
- Figure 12 (p.11): `fillrandom` average throughput. NVMe SSD — RocksDB-DF 40.9, RocksDB-AT 47.2,
  SILK-P 53.8, SILK-O 85.1, **ADOC 117.4 kOps/s**. PM — ADOC 211.5 vs SILK-O 126.9 (+66.7 %).
- Figure 13 (p.11): stall duration cut 45.2 % / 8.7 % / 10.3 % vs SILK-O on PM / SATA SSD / HDD;
  +1.5 % on NVMe.
- Figure 17 (p.12): YCSB — ADOC beats RocksDB-AT by 7.6–11.4 %; SILK-O wins A/B/C/F.
- Figure 18 (p.12): SILK-O uses up to 76.8 % more DRAM than ADOC (22.2 % on average).
- Figure 20/21 (p.13): ablation — ADOC-T (threads only) is good on PM, bad on HDD; ADOC-B (batch
  only) the reverse; tuning both stabilizes the control loop.

**Stated weaknesses.** ADOC's p99 write latency is 70.1 % / 131.2 % / 242.9 % *worse* than SILK-O
on NVMe / SATA SSD / HDD (Figure 16, p.12), and CPU time is up to 72.5 % higher (Figure 14, p.11);
the authors attribute both to ADOC simply ingesting 46–67 % more data. SILK could not be ported
past RocksDB v6 (§6.1).

## 2. Artifact audit

### Provenance

Official. Paper reference **[3]** (p.15) is literally `https://github.com/supermt/FEAT_7.11`, the
repo audited here, and `repo/README.md:3` states "This is the implementation of the paper published
on the conference FAST'23". FAST '23 predates USENIX FAST artifact evaluation (AE starts with
FAST '24 per the FAST '24 Call for Artifacts), so **no artifact badges** are expected or found.

### Structure

A full RocksDB fork, 1952 files, 33 MB, ~453 kLOC C++ (`repo_facts.json`). Only a handful of files
are ADOC's. Version is **7.7.0** (`include/rocksdb/version.h:14-16`), not the v7.5.3 claimed in
§6.1 — a minor but real discrepancy.

### Paper component → code path

| paper element | code |
|---|---|
| ADOC tuner (§5), MMO/L0O/RDO logic | `utilities/DOTA/DOTA_tuner.cc:427` (`TuneByTEA`), `:449` (`TuneByFEA`) |
| state scoring (flush rate, L0 count, pending bytes, thread idle) | `utilities/DOTA/DOTA_tuner.cc:75` (`ScoreTheSystem`) |
| AIMD actions (+2 threads / +64 MB, halve) | `utilities/DOTA/DOTA_tuner.cc:286` (`FillUpChangeList`), `:240` (`SetThreadNum`), `:251` (`SetBatchSize`) |
| "flush threads = ¼ of total" assumption | `utilities/DOTA/DOTA_tuner.cc:181-185` (idle-time normalisation by `/4` and `*3/4`) |
| batch size mirrored into SST / L1 size | `utilities/DOTA/DOTA_tuner.cc:258-283` |
| 1 s tuning window, applying changes online | `utilities/DOTA/report_agent.cc:40` (`DetectAndTuning`), `:106` (`ApplyChangePointsInstantly` → `SetDBOptions`/`SetOptions`) |
| per-second CSV of qps / batch size / thread count | `utilities/DOTA/report_agent.cc:54` (`ReportLine`), header at `include/rocksdb/utilities/report_agent.h:155` |
| the "50 LOC of state collection" | `db/flush_job.cc:1055-1061`, `db/compaction/compaction_job.cc`, structs in `include/rocksdb/compaction_job_stats.h:16` (`FlushMetrics`) and `:24` (`QuicksandMetrics`), plumbed via `options/db_options.h:112-113` (`job_stats`, `flush_stats`) |
| new immutable options `core_number`, `max_memtable_size` | `include/rocksdb/options.h:1397-1403` |
| thread-pool idle accounting (new Env API) | `include/rocksdb/env.h:685`, `env/env_posix.cc:420` (`GetThreadPoolWaitingTime`) |
| ADOC / ADOC-T / ADOC-B switches (Figure 20) | `tools/db_bench_tool.cc:784-785` (`--FEA_enable`, `--TEA_enable`), wired at `:3856-3873` |
| SILK baseline (Table 3) | `utilities/DOTA/report_agent.cc:188` (`ReporterAgentWithSILK`) — **a placeholder**, see below |
| YCSB macro benchmark (§6.3) | `ycsbcore/*` (vendored YCSB-cpp), `tools/db_bench_tool.cc:3445-3457` (`ycsb`, `ycsb_load`, `ycsb_run`), workload files `ycsb_workload/workloada` … `workloadf` |

### Build route on this machine

- **Must use `make`, not CMake.** `README.md:31` says the CMakeLists was never updated, and indeed
  `CMakeLists.txt` contains no reference to `DOTA` or `ycsbcore` (grep returns nothing), while
  `src.mk:150-155` and `src.mk:278` do. So: `make db_bench -j16`.
- `make db_bench` forces `DEBUG_LEVEL=0` (release) per `Makefile:68`.
- Only hard dependency for `db_bench` is **gflags** (`INSTALL.md:41-44`). `INSTALL.md:56` suggests
  `sudo apt-get`, but gflags is a plain CMake library — installable with conda
  (`conda install -c conda-forge gflags`) or built into `$HOME`. Compression libs (snappy/zstd/lz4)
  are optional; RocksDB compiles without them.
- gcc 12.2 vs a Sept-2022 RocksDB fork is the main build risk; `Makefile:501-502` exposes
  `DISABLE_WARNING_AS_ERROR=1`, which is the standard escape hatch.
- No CUDA, no GPU, no kernel/privileged component anywhere in the ADOC path.

### Data / traces / models

None needed. `fillrandom` is synthetic (`db_bench`); YCSB workload property files ship in
`ycsb_workload/`; the YCSB core generator is vendored in `ycsbcore/`. No proprietary traces.

### Evaluation scripts — mostly absent from this repo

The repo has **no experiment driver and no plotting scripts**. `README.md:47` points to a second
repo, `supermt/ADOC-Rocks-tracker` (Python runners `db_bench_runner.py`,
`db_bench_dynamic_runner.py`, `db_bench_sine_runner.py`, examples for `fillrandom`,
`rate-limited-fillrandom`, `bandwidth_influence` via cgroup, `on_cpu_analysis` via perf), whose
README in turn points to a third repo `supermt/FEAT_data_visual` for plots. The tracker needs
`iostat`, `pidstat`, `top`, `perf`, `cgroup` — **`perf` is blocked on this machine**
(`perf_event_paranoid=3`) and cgroup **io** is not delegated (only `cpu memory pids`), so the
`on_cpu_analysis` and `bandwidth_influence` examples are not usable as-is. The good news is that
ADOC's own reporter already writes `secs_elapsed,interval_qps,batch_size,thread_num` every second
(`utilities/DOTA/report_agent.cc:54-64`), which is exactly the data behind Figures 12 and 21 — the
core reproduction needs no external tooling at all.

### Known artifact defect: the SILK baseline is not real

`README.md:83-88`: *"The SILK implementation in this repo is a placeholder, since we failed to
reproduce the read performance as mentioned in its paper."* What is actually in
`utilities/DOTA/report_agent.cc:188-231` is a ~40-line imitation: pause/resume background work and
retune the rate limiter from observed user bandwidth. The paper's SILK numbers come from the
original `theoanab/SILK-USENIXATC2019` on RocksDB 5.7.1 (§6.1). **Any ADOC-vs-SILK claim is
therefore out of reach of this repo alone.**

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper reference [3] (p.15) is `github.com/supermt/FEAT_7.11`; `README.md:3` confirms. Contains the real tuner (`utilities/DOTA/DOTA_tuner.cc`, 474 lines), the instrumentation (`db/flush_job.cc:1055-1061`, `include/rocksdb/compaction_job_stats.h:16`), and the benchmark wiring (`tools/db_bench_tool.cc:3856-3873`). Not a stub. |
| `H2_no_root` | **pass** | ADOC is pure user-space RocksDB: online `SetDBOptions`/`SetOptions` (`utilities/DOTA/report_agent.cc:72-92`) and a new Env thread-pool idle counter (`env/env_posix.cc:420`). `repo_facts.json` sudo/docker/hugepage hits are all upstream RocksDB CI/doc leftovers (`.circleci/config.yml`, `INSTALL.md`, `include/rocksdb/advanced_options.h:445` hugepage *comment*); none is on the ADOC path. Dockerfiles under `build_tools/`/`tools/` are upstream CI images, replaceable by conda+gflags. The external tracker's `perf` step is optional. |
| `H3_hardware_fit` | **pass** (with scale-down) | Single node, CPU + NVMe only, no GPU. 16 cores ≥ the paper's useful thread range (`--core_num` flag at `tools/db_bench_tool.cc:780` caps `max_thread`, `include/rocksdb/utilities/DOTA_tuner.h:247`); 125 GB RAM ≫ the ≤2 GB footprints in Figure 18. Binding constraint is **disk**: Figure 14 (p.11) shows the 3600 s runs ingest ~400–800 GB, versus ~257 GB free — so runs must be shortened and/or stall thresholds scaled (see §4). Three of four device classes (PM, SATA SSD, HDD) do not exist here, so the device-transparency sweep can only be approximated with RocksDB's own `--rate_limiter_bytes_per_sec` (`tools/db_bench_tool.cc:1456`), not reproduced. |
| `H4_obtainable_deps_data` | **pass** | Only gflags is required (`INSTALL.md:41-44`), installable via conda/source in `$HOME`. All workloads are synthetic or shipped: `db_bench fillrandom`, vendored YCSB-cpp (`ycsbcore/`) plus `ycsb_workload/workloada`–`workloadf`. No proprietary traces. The tracker's optional dynamic runner uses Alibaba `clusterdata`, which is public on GitHub. |

## 4. Reproduction plan

**Target.** Figure 12, p.11, **NVMe SSD row**: `fillrandom` average throughput
RocksDB-DF 40.9 → RocksDB-AT 47.2 → **ADOC 117.4 kOps/s**. The claim is ADOC ≈ 2.5× auto-tuned
RocksDB on a modern NVMe device with no human tuning. Secondary target: Figure 21, p.13 (the
per-second thread-count / batch-size trace), which falls straight out of ADOC's own CSV reporter.

**Deliberately *not* targeting** the ADOC-vs-SILK-O comparison: the repo's SILK is a self-declared
placeholder (`README.md:83-88`) and real SILK is a 2018 RocksDB-5.7.1 fork in a different repo.

**Scale-down.**
1. NVMe only (PM9A3, the machine's only device class). Emulate the SATA-SSD / HDD regimes, if
   wanted at all, with `--rate_limiter_bytes_per_sec` (490 MB/s, 210 MB/s per paper Table 1) rather
   than real hardware — document this as an approximation, not a reproduction.
2. `--core_num=16` instead of the 20 used in the paper (default flag value is 20,
   `tools/db_bench_tool.cc:780`), matching the 16 physical cores here.
3. Shorten `fillrandom` from 3600 s to **1200 s** and cap `--num` so the DB stays under ~120 GB.
   At paper scale the NVMe run ingests ~400+ GB (Figure 14) and there is ~257 GB free; at 1200 s on
   a faster CPU/SSD expect ~130–180 GB, so also keep one scheme's DB at a time and delete between
   runs.
4. To keep RDO/PS stalls reachable at the shorter scale, scale
   `soft_pending_compaction_bytes_limit` / `hard_pending_compaction_bytes_limit` down from the
   64 GB / 128 GB defaults proportionally (they are read at
   `utilities/DOTA/DOTA_tuner.cc:162-164`), and report this as a deviation.
5. Keep `--value_size=1000`, `--benchmark_write_rate_limit=0` (peak pressure), report interval 1 s.

**Steps.**
1. `conda create` env; install gflags (+ optionally snappy/zstd) into `$CONDA_PREFIX`.
2. `DISABLE_WARNING_AS_ERROR=1 make db_bench -j16`; expect to patch a handful of gcc-12 warnings.
   Do **not** use CMake (no DOTA/ycsbcore targets).
3. Smoke test: 120 s `fillrandom` with `--report_interval_seconds=1 --TEA_enable --FEA_enable
   --core_num=16`; confirm the CSV's `thread_num`/`batch_size` columns actually move and that the
   "slow flush, decrease thread" / "lo/ro increase, thread" stdout traces
   (`utilities/DOTA/DOTA_tuner.cc:437,443,456,461`) appear.
4. Run the three schemes × 3 repetitions at 1200 s: RocksDB-DF (no flags), RocksDB-AT
   (`--rate_limiter_bytes_per_sec=<device bw> --rate_limiter_auto_tuned`,
   `tools/db_bench_tool.cc:1456-1461`), ADOC (`--TEA_enable --FEA_enable`).
5. Plot mean throughput per scheme from the CSVs; compare the *ratio* ADOC/RocksDB-AT (≈2.49× in
   Figure 12) rather than absolute kOps/s, since the CPU and SSD differ from the paper's.
6. Bonus at near-zero extra cost: ADOC-T / ADOC-B (Figure 20) are one flag each.

**Effort.** ≈ 4–6 person-days (build + gcc-12 fixes + harness scripting + analysis) and ≈ 40–60
machine-hours wall-clock for 3 schemes × 3 runs × 1200 s plus re-runs and DB teardown. No GPU
hours. Disk churn is the scheduling constraint, not compute.

**Level: M.** Not H because the repo ships no experiment driver or plotting scripts (they live in
two other repos, one of which needs `perf` and cgroup-io that this machine denies), the CMake path
is broken by the authors' own admission, the SILK baseline is a placeholder, the code is a
2022-vintage fork that must be coaxed through gcc 12, and disk capacity forces a documented
deviation from the paper's 3600 s scale. Not L because the mechanism is two command-line flags on a
`make`-able `db_bench`, the target result needs no external data, and ADOC's own per-second CSV
reporter emits exactly the series plotted in Figures 12 and 21.

## 5. Add-on ideas

### A1 — Split-aware thread tuning (flush vs compaction, not just total)

**Hypothesis.** We hypothesize that tuning the *flush:compaction thread split*
(`max_background_flushes` / `max_background_compactions`) jointly with the total thread count
improves `fillrandom` throughput and reduces MT-stall duration under peak write pressure on NVMe,
compared with ADOC's fixed "flush = ¼ of total" rule.

**Mechanism.** `SetThreadNum` currently emits a single `max_background_jobs` ChangePoint
(`utilities/DOTA/DOTA_tuner.cc:240-249`), leaving RocksDB to derive the ¼ split
(`db/db_impl/db_impl_compaction_flush.cc:2540-2559`). Extend `ChangePoint` emission to set
`max_background_flushes` and `max_background_compactions` explicitly — both are already *mutable*
DB options (`options/db_options.cc:68`, `:128`) and therefore go through the existing
`SetDBOptions` path in `ApplyChangePointsInstantly` with no new plumbing. Add a third AIMD vote:
MMO ⇒ shift one thread from the compaction pool to the flush pool (instead of halving the total);
L0O/RDO ⇒ shift toward compaction; total bounded by `core_num`. Also fix the hard-coded `/4` and
`*3/4` normalisation of thread idle time at `utilities/DOTA/DOTA_tuner.cc:181-185` so the detector
stays consistent with the actual split.

**Motivating evidence.** §5 (p.9): *"After the adjustment, the number of threads that are allocated
for flush jobs will also be adjusted to a quarter of the total number, just as the default
setting."* §4.2 (p.9): *"as the number of threads increases, more threads are forced to share the
limited bandwidth, resulting in less bandwidth being allocated to the flush threads."* ADOC's MMO
response is therefore an *indirect* way to buy flush bandwidth — it halves the total thread count
and throws away compaction parallelism as a side effect. Figure 20 (p.13) shows ADOC-T degrading
exactly where this matters (slower devices). Whether the flush share can be raised *without*
sacrificing compaction parallelism is untested.

**Code locations.** `utilities/DOTA/DOTA_tuner.cc`, `include/rocksdb/utilities/DOTA_tuner.h`,
`utilities/DOTA/report_agent.cc`, `options/db_options.cc`, `db/db_impl/db_impl_compaction_flush.cc`

**Feasibility: H.** ≲300 LOC in one file plus a flag; both target options are already dynamically
settable; measurable with the existing per-second reporter and RocksDB's stall counters. No new
harness.

**Research value: M.** A reviewer would read this as a well-motivated extra knob rather than a new
insight; a positive result is somewhat expected. It does, however, directly test the paper's causal
story ("fewer threads ⇒ more flush bandwidth").

**Scoop check — `partial`.** Queries: *"RocksDB dynamic flush compaction thread pool split ratio
tuning research paper 2024 2025 background jobs write stall"*; *"LSM-tree online tuning flush
compaction thread allocation write stall 2025 RocksDB"*. Closest: **ELMo-Tune-V2**
(https://arxiv.org/abs/2502.17606) tunes "compaction, flush, and cache sizes" over a broad space
with an LLM and does real-time adjustment — overlapping parameter space, entirely different method,
and it does not isolate the flush/compaction split as a write-stall control lever. No paper found
that changes ADOC's ¼ rule.

### A2 — Decayed reference scores and phase-aware detection

**Hypothesis.** We hypothesize that replacing ADOC's monotonically-increasing `max_scores`
reference with a windowed/decayed reference plus hysteresis improves throughput and reduces
configuration oscillation under **warm-DB and phase-changing workloads** (YCSB load→run
transitions, time-varying write pressure), compared with stock ADOC.

**Mechanism.** Every ADOC decision is a ratio against a *running maximum*:
`current_score_.flush_speed_avg < max_scores.flush_speed_avg * TEA_slow_flush`
(`utilities/DOTA/DOTA_tuner.cc:435`, `:452`). `UpdateMaxScore`
(`include/rocksdb/utilities/DOTA_tuner.h:167-214`) only ever increases these maxima, and
`SystemScores::Reset()` is never called on `max_scores` — so a fast early flush burst on an empty
DB permanently biases the "slow flush" test toward `kHalf`. Replace the running max with an
EWMA or sliding-window high percentile over the `scores` deque that already exists
(`include/rocksdb/utilities/DOTA_tuner.h:107`, window length `score_array_len` at `:123`); note
`CalculateAvgScore()` (`utilities/DOTA/DOTA_tuner.cc:465`) already computes an average that the
decision logic never consults. Add hysteresis: require *k* consecutive windows of the same verdict
before firing an AIMD action.

**Motivating evidence.** Figure 21 (p.13) shows thread count and batch size oscillating across the
full hour even for full ADOC — the paper's own illustration of control instability, presented as a
*relative* improvement over ADOC-T/ADOC-B rather than as stability. Every experiment in the paper
starts from an empty DB (§3.1, §6.2), so the monotonic-reference bias is never exercised; YCSB
(§6.3) reloads between phases. §5 justifies AIMD by "agility", which is precisely the trade-off
this add-on re-examines.

**Code locations.** `include/rocksdb/utilities/DOTA_tuner.h`, `utilities/DOTA/DOTA_tuner.cc`,
`utilities/DOTA/report_agent.cc`, `tools/db_bench_tool.cc`

**Feasibility: M.** The controller change itself is small and local (~200 LOC, one file), and the
oscillation metric is already logged per second. The cost is the evaluation harness: a *warm-DB*
protocol means pre-building a ~100 GB database and restoring it identically before each scheme,
which is tight against ~257 GB free and adds substantial wall-clock per run. `--use_existing_db`
plus chained `db_bench` benchmarks covers the phase-change workload without new code.

**Research value: H.** It names a concrete, code-level assumption (empty-DB start, monotonic
reference) that the paper never tests, and probes a regime — steady-state warm store with shifting
phases — that is the normal case in production. Either outcome is informative: if ADOC's 2.5× gain
survives warm start, that strengthens the paper; if it collapses, that is a genuine finding about
online AIMD tuners for LSM stores.

**Scoop check — `partial`.** Queries: *"LSM auto-tuning controller oscillation AIMD phase change
workload dynamic write stall adaptive 2025"*; *"ADOC FAST 2023 write stall RocksDB follow-up data
overflow tuning tail latency"*. Closest: **ArceKV**
(https://arxiv.org/abs/2508.03565) targets workload-driven LSM *compaction policy* transitions
under dynamic workloads — same motivating regime, different mechanism, and it does not touch ADOC's
controller. Nothing found that analyses or fixes ADOC's reference-score decay.

### A3 — Memory-budget-aware batch tuning

**Hypothesis.** We hypothesize that co-tuning batch (memtable) size against block-cache capacity
under a *fixed total DRAM budget* lets ADOC match or exceed SILK-O on read-heavy YCSB (A/B/C/F) at
equal memory, compared with ADOC's unconstrained batch growth.

**Mechanism.** `SetBatchSize` (`utilities/DOTA/DOTA_tuner.cc:251-284`) grows the memtable, SST
size, and L1 size, bounded only by `max_memtable_size`
(`include/rocksdb/utilities/DOTA_tuner.h:249`, flag at `tools/db_bench_tool.cc:781`); the block
cache is never considered. Introduce `--adoc_memory_budget`: total =
`max_write_buffer_number × write_buffer_size + block_cache_capacity`. When FEA votes
`kLinearIncrease`, shrink the block cache by the same delta via `Cache::SetCapacity`, and vice
versa. This needs a small extension to `ChangePoint` / `ApplyChangePointsInstantly`
(`utilities/DOTA/report_agent.cc:106-137`), which today can only carry string-valued RocksDB
options, to also carry a cache-capacity action.

**Motivating evidence.** §6.3 (p.12): *"SILK-O uses as much as 76.8 % more memory than ADOC. Larger
memory allows more requests to be serviced from the data buffered in memory"* — the paper's own
explanation for why it loses YCSB A/B/C/F in Figure 17 (p.12). Figure 18 (p.12) quantifies the gap.
The paper frames ADOC's lower memory use as a win, but never runs the obvious controlled
experiment: give ADOC the same DRAM and let it decide how to spend it.

**Code locations.** `utilities/DOTA/DOTA_tuner.cc`, `utilities/DOTA/report_agent.cc`,
`include/rocksdb/utilities/DOTA_tuner.h`, `tools/db_bench_tool.cc`, `ycsbcore/core_workload.cc`

**Feasibility: M.** Cross-cutting: the ChangePoint mechanism must learn a non-string action, and the
evaluation is the expensive one (YCSB load of 50 M × 1 KB ≈ 50 GB, then six 1-hour run phases per
scheme). Scale down to ~20 M entries and 20-minute phases to fit disk and wall-clock.

**Research value: M.** The fairness question is real and the read-heavy regime is where ADOC is
weakest, but the direction of the result is fairly predictable, and the "compare at equal memory
budget" framing has already been staked out by others (see scoop).

**Scoop check — `partial`.** Queries: *"ADOC LSM key-value store citing papers 2024 2025 extend
tuner memory budget block cache memtable"*; *"arXiv vLSM low tail latency LSM key-value store 2024
compare ADOC SILK write stall"*. Closest: **vLSM**
(https://arxiv.org/abs/2407.15581) explicitly argues the same-memory-budget comparison, reports
ADOC "reduces tail latency by sacrificing I/O amplification", and beats it — but by *redesigning*
the LSM structure, not by making ADOC memory-budget-aware. The specific experiment proposed here
(ADOC given SILK-O's DRAM, allocating it itself) is not in the literature found.

### A4 — ADOC under a CPU budget (multi-tenant regime)

**Hypothesis.** We hypothesize that making ADOC's thread-count controller aware of an enforced CPU
budget (cgroup v2 `cpu.max`) preserves most of its throughput gain and avoids the CPU-cost blowup,
under a co-located/limited-CPU regime, compared with stock ADOC which assumes it owns all cores.

**Mechanism.** `max_thread` is set once from `core_number`
(`include/rocksdb/utilities/DOTA_tuner.h:246-248`, `tools/db_bench_tool.cc:4649`), and the idle-time
signal is normalised by the *configured* thread count, not by CPU actually available
(`utilities/DOTA/DOTA_tuner.cc:181-185`). Under a `cpu.max` quota, adding threads buys no work and
the `kIdle`/`kBandwidthCongestion` classifiers mis-fire. Add a runtime CPU-budget estimator
(read `cpu.stat` throttling counters from the process's own delegated cgroup — available
unprivileged since `cpu` is delegated to the user slice on this machine) and clamp/re-normalise
`max_thread` and the idle thresholds against it.

**Motivating evidence.** Figure 14 (p.11) and §6.2: ADOC spends up to **72.5 % more CPU time** than
SILK-O, and Figure 15 shows up to 143.6 % more background operations. The paper explicitly treats
CPU as free ("write stalls are triggered even when the hardware resources are sufficient", §1) and
evaluates only on a dedicated 40-core server. The paper's second design principle is *device*
transparency; *compute* transparency is never claimed or tested.

**Code locations.** `include/rocksdb/utilities/DOTA_tuner.h`, `utilities/DOTA/DOTA_tuner.cc`,
`tools/db_bench_tool.cc`, `utilities/DOTA/report_agent.cc`

**Feasibility: M.** The controller change is small, but this needs a new experimental harness: run
`db_bench` inside a delegated cgroup v2 sub-tree with varying `cpu.max`, plus a co-located
CPU-hog tenant, and a sweep over budgets. That is scriptable without root on this machine
(`cpu memory pids` are delegated), but it is a workload generator that does not exist in either the
paper's or the authors' tracker repo. Compute cost is moderate (short runs, many points).

**Research value: M.** A regime the paper ignores and that matters for real deployments; the
finding "an auto-tuner that assumes exclusive CPU misbehaves when it does not have it" is plausible
but not shocking. Upgraded above "parameter tuning" because a negative result would qualify the
paper's central automation claim.

**Scoop check — `clear`.** Queries: *"LSM-tree online tuning flush compaction thread allocation
write stall 2025 RocksDB"*; *"LSM auto-tuning controller oscillation AIMD phase change workload
dynamic write stall adaptive 2025"*; *"ADOC FAST 2023 write stall RocksDB follow-up data overflow
tuning tail latency"*. Nothing found that evaluates ADOC (or an LSM write-stall auto-tuner) under
enforced CPU quotas / co-location. Adjacent but distinct: **RESYSTANCE** (arXiv 2603.05162) uses
eBPF to reshape compaction — out of scope for this machine anyway, and not a CPU-budget study.

## 6. Risks and open questions

1. **Data race in the metrics path.** `db/flush_job.cc:1061` does
   `db_options_.flush_stats->push_back(metrics)` from flush threads with no lock, while the tuner
   thread iterates the same `std::vector` (`utilities/DOTA/DOTA_tuner.cc:98-109`,
   `:125-136`). A `push_back` reallocation during iteration is undefined behaviour. The paper's
   runs are an hour long with thousands of flushes, so this may simply be latent luck. Expect
   sporadic crashes; a small fix (mutex or a fixed-capacity ring) may be needed before any long
   run, and should be reported as a deviation.
2. **Unbounded metric growth.** `flush_stats` / `job_stats` are never trimmed — the clear is
   commented out at `utilities/DOTA/report_agent.cc:43`. Harmless at paper scale, but worth
   watching in longer runs.
3. **Version mismatch.** Paper §6.1 says RocksDB v7.5.3; the repo is 7.7.0
   (`include/rocksdb/version.h:14-16`). The paper itself shows (Figure 17, "ADOC-5.7.1") that the
   RocksDB base version materially shifts ADOC's numbers, so exact absolute values should not be
   expected.
4. **SILK is not reproducible from this artifact** (`README.md:83-88`). Any comparison to SILK needs
   `theoanab/SILK-USENIXATC2019`, a RocksDB 5.7.1 fork from 2018 — high build risk on gcc 12,
   and the paper's own porting attempt to newer RocksDB failed.
5. **Disk capacity.** ~257 GB free vs the ~400–800 GB ingested per 3600 s run in Figure 14. Every
   experiment must be shortened or thresholds rescaled; back-to-back scheme comparison requires
   deleting each DB before the next.
6. **Device sweep is not reproducible.** Only NVMe exists here. The paper's central
   "device-transparency" claim spans PM / NVMe / SATA SSD / HDD. cgroup **io** is not delegated on
   this machine, so the authors' own `bandwidth_influence` approach is unavailable; the closest
   substitute is RocksDB's internal rate limiter, which throttles background I/O only and is not
   equivalent to a slower device.
7. **`perf` is blocked** (`perf_event_paranoid=3`), so Figure 15 (operation breakdown, obtained by
   sampling the call stack at 99 Hz, §6.2) cannot be reproduced at all.
8. **Shared machine.** 125 GB RAM with other users; page cache and CPU contention will add variance
   to throughput numbers that the paper reports with std-dev under 10 %.
9. **Open question.** `LocateThreadStates` / `LocateBatchStates`
   (`utilities/DOTA/DOTA_tuner.cc:31-73`) belong to the base `DOTA_Tuner`, but `FEAT_Tuner`
   overrides `DetectTuningOperations` and never calls them — the shipped ADOC path is
   `TuneByTEA`/`TuneByFEA` with its own, simpler thresholds. Reading the code alone cannot settle
   whether the paper's described MMO/L0O/RDO priority ordering (§5, "L0O, RDO, MMO order") is the
   one actually evaluated; `TuneByFEA` overwrites `result.BatchOp` unconditionally
   (`utilities/DOTA/DOTA_tuner.cc:414-417`). This should be resolved empirically before building on
   the controller.

## 7. Evidence index

**Paper.** §1 Introduction & Figure 1 (p.2, write stalls across devices); §2.1–2.3 (p.3–5,
background, Table 1 device specs, stall types and default thresholds); §3.1 (p.4–5, experimental
setup: 2× Xeon 6230/40 cores/128 GB, Ubuntu 18.04, RocksDB 6.11, fillrandom 16 B/1000 B, 1 h);
Table 2 (p.5, confirmations C1–C5 and limitations L1–L5); Figures 3–5 (p.5–6, stalls / CPU /
bandwidth vs thread count); Figure 6 (p.6, L0–L1 compaction vs stall timing); Figures 7–8 (p.7,
background-job rates and stall breakdown); §4.1 & Figure 9 (p.7–8, MMO/L0O/RDO); §4.2 & Figure 10
(p.8–9, stalls under low utilisation); §5 & Figure 11 (p.9, ADOC control flow, AIMD, ~300 LOC,
Tw = 1 s, ¼ flush threads); §6.1 & Table 3 (p.10, schemes; RocksDB v7.5.3; SILK on 5.7.1);
§6.2 & Figure 12 (p.11, throughput — ADOC 117.4 kOps/s NVMe); Figure 13 (p.11, stall duration);
Figure 14 (p.11, CPU / disk space / **input data size 400–800 GB**); Figure 15 (p.11, perf-sampled
operation breakdown); Figure 16 (p.12, p99 tail latency, ADOC worse by 70–243 %); §6.3, Table 4 and
Figures 17–18 (p.12, YCSB throughput and memory footprint); Figure 19 (p.13, read-while-writing);
§6.4 and Figures 20–21 (p.13, ADOC-T / ADOC-B ablation and tuning-action traces); §7 Related Work
(p.13–14); References [3] (p.15, the repo URL).

**Repository.** `README.md` (:3 official claim, :31 make-not-cmake, :39-43 ADOC/-T/-B flags, :47
tracker repo, :83-88 SILK placeholder); `include/rocksdb/utilities/DOTA_tuner.h` (:26-81
`SystemScores`, :96-262 `DOTA_Tuner`, :107 scores deque, :123 `score_array_len`, :167-214
`UpdateMaxScore`, :240-250 option-name constants and thread/batch bounds, :246-248
`core_num`/`max_thread`, :265-319 `FEAT_Tuner`);
`utilities/DOTA/DOTA_tuner.cc` (:31-73 `LocateThreadStates`/`LocateBatchStates`, :75-193
`ScoreTheSystem` incl. :162-164 pending-bytes ratio and :181-185 ¼ / ¾ idle normalisation, :240-249
`SetThreadNum`, :251-284 `SetBatchSize`, :286-311 `FillUpChangeList`, :382-421
`FEAT_Tuner::DetectTuningOperations`, :427-447 `TuneByTEA`, :449-464 `TuneByFEA`, :465-472
`CalculateAvgScore`);
`utilities/DOTA/report_agent.cc` (:40-52 1 s tuning loop, :54-64 CSV reporter, :65-70
`UseFEATTuner`, :72-92 `SetDBOptions`/`SetOptions`, :106-137 `ApplyChangePointsInstantly`, :188-244
SILK placeholder); `include/rocksdb/utilities/report_agent.h` (:37-127 `ReporterAgent`, :144-232
`ReporterAgentWithTuning`, :155 CSV header, :234-292 `ReporterWithMoreDetails`);
`tools/db_bench_tool.cc` (:76 & :98-104 includes, :775-797 ADOC flags incl. :780 `core_num`,
:781 `max_memtable_size`, :784-785 `FEA_enable`/`TEA_enable`, :1456-1461 rate-limiter flags,
:3445-3457 YCSB benchmarks, :3854-3887 reporter selection, :4649-4650 option wiring, :4954-5106
YCSB driver); `include/rocksdb/options.h` (:1397-1403 `core_number`, `max_memtable_size`);
`include/rocksdb/compaction_job_stats.h` (:16-22 `FlushMetrics`, :24-49 `QuicksandMetrics`);
`options/db_options.h` (:110-113 `core_number`, `max_memtable_size`, `job_stats`, `flush_stats`);
`options/db_options.cc` (:68, :128 mutable `max_background_compactions` / `max_background_flushes`);
`db/flush_job.cc` (:1055-1061 unsynchronised metric push); `db/db_impl/db_impl_compaction_flush.cc`
(:2540-2559 `GetBGJobLimits`, the ¼ rule); `include/rocksdb/env.h` (:685) and `env/env_posix.cc`
(:420) `GetThreadPoolWaitingTime`; `src.mk` (:150-155 ycsbcore, :278 DOTA sources);
`CMakeLists.txt` (no DOTA/ycsbcore references — confirms make-only build);
`Makefile` (:68 `make db_bench` ⇒ DEBUG_LEVEL=0, :501-502 `DISABLE_WARNING_AS_ERROR`);
`INSTALL.md` (:41-44 gflags requirement, :56 apt suggestion); `include/rocksdb/version.h` (:14-16
version 7.7.0); `ycsbcore/` (vendored YCSB-cpp, e.g. `core_workload.cc`, `ycsbc.cc`);
`ycsb_workload/workloada`–`workloadf`; `repo_facts.json` (red flags, all upstream RocksDB).

**External.** `https://github.com/supermt/ADOC-Rocks-tracker` (experiment runners, README naming
iostat/pidstat/top/perf/cgroup deps and pointing to `supermt/FEAT_data_visual` for plots);
`https://www.usenix.org/conference/fast24/call-for-artifacts` (FAST artifact evaluation starts at
FAST '24 ⇒ no badges for FAST '23); `https://arxiv.org/abs/2407.15581` (vLSM);
`https://arxiv.org/abs/2502.17606` (ELMo-Tune-V2); `https://arxiv.org/abs/2508.03565` (ArceKV).
