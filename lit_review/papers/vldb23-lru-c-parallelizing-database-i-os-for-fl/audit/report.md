# LRU-C: Parallelizing Database I/Os for Flash SSDs

PVLDB 16(9):2364–2376, 2023 — Bo-Hyun Lee, Mijin An, Sang-Won Lee (Sungkyunkwan Univ.)
Repo: https://github.com/LeeBohyun/LRU-C (MySQL 5.6.26 fork, GPL-2.0, 11 stars, last push 2023-05-24)

## 1. Paper summary

**Problem.** A conventional DBMS buffer manager serializes I/O in two ways (§2.3, Fig. 2, Fig. 3):

- *RW-serialization from read stalls*: on a page miss with no clean victim in the scan window, the
  foreground thread must write a dirty LRU-tail page and only then issue its read (the RAW protocol).
  Measured on MySQL/InnoDB + TPC-C, the average read-stall wait is 4.86 ms, worst > 500 ms (§2.3).
- *Mutex-induced RR- and RW-serialization*: all foreground readers and the background flusher contend
  for one `lru_list_mutex` per buffer-pool instance while scanning/repositioning the LRU list; a thread
  spends ~1.3% of benchmark runtime waiting on it (§2.3).

Table 2 (§3) quantifies the motivation: at buffer/DB ratios of 5–25%, 5–33% of reads are read-stalled,
TPS is 175–756, 95th latency 450–152 ms, and CPU utilization only 24–41%.

**Key idea (§4.1–4.2, Fig. 4, Algorithm 1).** Maintain an **LRU-C pointer** per buffer-pool instance to
the least-recently-used *clean* page. On a miss, the victim is taken directly from the pointer (O(1)),
then the pointer is advanced to the next clean page toward the head. This removes the read stall and
shortens the mutex hold time of the victim scan.

**Two optimizations (§4.3, Fig. 5).**
- *Dynamic-batch-write*: the pointer partitions the LRU into a **mixed region** (head-side) and a
  **dirty region** (tail-side). The background flusher writes *all* dirty pages in the dirty region per
  wakeup instead of a fixed `innodb_lru_scan_depth` count.
- *Parallel LRU-list manipulation*: split the LRU mutex into **LRU-M** (mixed region, foreground) and
  **LRU-D** (dirty region, background flusher), so reads and writes can be issued concurrently.

**Admitted costs/limits.** Hit ratio drops (§4.4, Table 7: miss ratio 1.04–1.36× Vanilla). Checkpointing
still needs LRU-M, so a residual RW-serialization remains (§4.3, last paragraph). Basic LRU-C still
read-stalls "when the number of page misses momentarily spikes (e.g., as the working set changes)" and
the pointer reaches the LRU head (§5.2.2, p. 8) — a regime never evaluated.

**Evaluation setup (§5.1).** Intel Xeon Silver 4216 (32 cores), 64 GB RAM, ext4, four SSDs (Table 1) plus
a separate Samsung 850 PRO log device. 100 GB database, 16 KB pages, 64 clients, 30-min runs after 5-min
warm-up, 3-run average. Workloads: Percona `tpcc-mysql` (1,000 warehouses) and LinkBench (100 M nodes).
Baselines: knob-tuned "Vanilla" MySQL 5.6 (§5.2.1), WAR (SIGMOD'22), CF-LRU emulated by varying
`innodb_lru_scan_depth` (Table 4).

**Headline numbers.**
- Fig. 6 (drill-down, SSD-A, 10% buffer): Vanilla 247 → Basic LRU-C 404 → +Dynamic-Batch-Write 537 →
  +LRU-D mutex 755 TPS. Table 3: read-stall ratio 1.56% → 0.83% → 0%; LRU mutex wait 0.18 → 0.07 ms.
- Fig. 7a: LRU-C ≈ 3× Vanilla and ≈ 1.52× WAR on TPC-C across 5–25% buffer ratios; Fig. 7b LinkBench
  2× Vanilla / 1.42× WAR.
- Table 5: read IOPS 6,860 → 25,510; total bandwidth 171 → 524 MB/s (64% of the FIO-measured device
  peak vs. 25% for Vanilla); CPU util. 24% → 84%.
- Table 6: avg/95th/99th latency 4.04/332/583 ms (Vanilla) → 1.32/53.0/391 ms (LRU-C).
- Secondary: Fig. 8 (R:W ratio sweep), Fig. 9 (8–128 threads), Fig. 10 (Cosmos+ OpenSSD channel count),
  Fig. 11 (4 SSD models), Fig. 12 (GCP/Azure), Fig. 13 (HDD — no gain, as expected).

## 2. Artifact audit

### Repo structure

The repository is a **full MySQL 5.6.26 source tree** (`VERSION`: 5.6.26; 239 MB, 14,594 files), not a
standalone artifact. `README.md` states modifications are confined to
`storage/innobase/buf/{buf0lru.cc, buf0flu.cc, buf0buf.cc}` and
`storage/innobase/include/{buf0lru.h, buf0buf.h}`, marked with `For LRU-C` / `/* lbh */` comments.
Grepping confirms that scope: 67 matches for LRU-C identifiers across 7 InnoDB files, nothing elsewhere.

### Paper component → code path

| Paper component | Code |
|---|---|
| LRU-C pointer (§4.1) | `storage/innobase/include/buf0buf.h:1979` — `buf_page_t* LRU_oldest_clean_page` in `buf_pool_t`; initialized `storage/innobase/buf/buf0buf.cc:1380` |
| LRU-D mutex (§4.3) | `storage/innobase/include/buf0buf.h:1986` `LRU_dirty_tail_list_mutex` + accessor macros at `buf0buf.h:2041-2050`; created at `storage/innobase/buf/buf0buf.cc:1364`; PFS key at `buf0buf.cc:279` |
| Victim selection / pointer advance (Alg. 1) | `storage/innobase/buf/buf0lru.cc:456` `buf_update_oldest_clean_page()`, `buf0lru.cc:554` `buf_oldest_clean_page_is_valid()` |
| Page-miss path rewritten (Fig. 4, Steps 1-2) | `storage/innobase/buf/buf0lru.cc:1414-1446` inside `buf_LRU_get_free_block()` — the original "scan LRU tail / single-page flush (RAW)" path is **deleted**, replaced by pointer lookup + retry loop |
| Dynamic-batch-write (§4.3) | `storage/innobase/buf/buf0flu.cc:2309` `buf_flush_LRU_tail()` (rewritten), and `buf0flu.cc:1510` `buf_flush_LRU_list_batch()` |
| Flusher takes LRU-D instead of LRU mutex | `storage/innobase/buf/buf0flu.cc:1857-1859` (`buf_flush_batch`), `:1929-1961` (`buf_flush_start`), `:1981-2012` (`buf_flush_end`), `:1090-1096` (`buf_flush_page`), `:1169-1208` (`buf_flush_check_neighbor`) |
| Per-page batch-write bookkeeping | `storage/innobase/include/buf0buf.h:1469-1470` `LRU_batch_write_victim`, `aio_write_finished`; used at `buf0lru.cc:1639,1937,2243,2358` and `buf0flu.cc:2398-2399` |

The implementation is real and matches the design. It is *not* a placeholder.

### Paper ↔ code discrepancies found by reading

These matter for anyone reproducing the numbers:

1. **"Dynamic" batch is actually capped.** §4.3 says the flusher writes *all* dirty pages behind the
   pointer. The code caps the scan at `UT_LIST_GET_LEN(buf_pool->LRU) / 8` (`buf0flu.cc:2348`) and at
   `buf_pool->LRU_old_len / 2` in `buf_flush_LRU_list_batch` (`buf0flu.cc:1539`), and skips the whole
   batch when `lru_len < free_len * 2` (`buf0flu.cc:2331`).
2. **The LRU-C pointer never reaches the LRU head.** §4.2/§5.2.2 describe the pointer marching toward
   the head until it meets it. The code stops the clean-page search at the "old" sublist boundary
   (`bpage != buf_pool->LRU_old`, `buf0lru.cc:494`), breaks when `scanned > buf_pool->LRU_old_len`
   (`:506`), and requires `buf_page_is_old(bpage)` (`:515`). Implemented LRU-C is therefore
   **clean-first eviction with a window equal to the InnoDB old sublist** (`innodb_old_blocks_pct`,
   default 37%) plus an O(1) pointer — i.e. much closer to CF-LRU than §6 argues, with the window fixed
   rather than tuned. This is the single most interesting finding of this audit.
3. **A debug `fprintf` is live on the hottest path**: `buf0lru.cc:1399`
   `fprintf(stderr, "free block from free list\n");` fires on *every* free-list hit. Left enabled it
   will both distort throughput and grow the error log without bound. Every other `fprintf` in the
   LRU-C code is commented out; this one is not.
4. **Apparent mutex-balance bug** in `buf_flush_LRU_tail`: the loop acquires `LRU_dirty_tail_list_mutex`
   at `buf0flu.cc:2353` and releases at `:2412`; when the loop condition goes false the mutex is not
   held, yet `:2419` releases it again. Also `scan_depth` is read uninitialized at `:2326`
   (`scan_depth = ut_min(srv_LRU_scan_depth, scan_depth);`) and then never used.
5. **No on/off knob.** There is no `innodb_lru_c` system variable (`grep lbh storage/innobase/handler/ha_innodb.cc`
   → no matches). LRU-C is always on, and the original RAW fallback in `buf_LRU_get_free_block` is gone.
   The "Vanilla" and "Basic LRU-C" / "+Dynamic-Batch-Write" bars of Fig. 6 cannot be produced from this
   binary; they need separate builds.

### Build route on this machine

- No Dockerfile for the artifact (`packaging/rpm-docker` is stock MySQL packaging, not an artifact
  container). Build is plain CMake + make, entirely in user space, install prefix in `$HOME`.
- `CMakeLists.txt:16` is `CMAKE_MINIMUM_REQUIRED(VERSION 2.6)`. The system cmake 3.25.1 accepts this
  with a deprecation warning; the pip-installed cmake 4.x would **reject** it. Use the system cmake.
- MySQL 5.6.26 is a 2015 codebase; gcc 12.2 with its default `-std=gnu++17` will not compile it as-is
  (removed `register` keyword, dynamic exception specifications, stricter narrowing). Realistic route:
  a conda `gcc_linux-64` 9.x/10.x toolchain plus `-std=gnu++03`/`gnu++11` and
  `-fpermissive -Wno-error`. This is user-space-installable, but it is real porting work and I could
  not verify it by reading alone.
- No boost needed at 5.6 (that starts at 5.7). `-DWITH_SSL=bundled` avoids OpenSSL 3.x; bundled
  zlib/libedit avoid more system deps. ncurses + bison are needed and are conda-installable.
- **libaio matters**: `storage/innobase/CMakeLists.txt:25-30` only defines `LINUX_NATIVE_AIO=1` if
  `libaio.h` and `libaio` are found; otherwise InnoDB silently falls back to *simulated* AIO. Since the
  paper's whole claim is about parallel asynchronous writes, a simulated-AIO build would invalidate the
  experiment. libaio must be installed via conda or built from source into `$HOME`.
- `INNODB_PAGE_ATOMIC_REF_COUNT` defaults to `ON` (`CMakeLists.txt:327`) and must stay on: the new
  per-page fields were added only inside the `#ifdef PAGE_ATOMIC_REF_COUNT` branch of `buf_page_t`
  (`buf0buf.h:1461-1472`), so turning it off breaks the build.
- Running mysqld needs no root: user-owned datadir, port > 1024, unix socket in `$HOME`.

### Data / benchmarks / eval scripts

- **No evaluation scripts, configs, my.cnf, or plotting code are in the repository.** `scripts/` is
  stock MySQL tooling only. `README.md` delegates to an external guide,
  `github.com/LeeBohyun/mysql-tpcc/.../how-to-install-and-run-mysql-tpcc.md`, which targets MySQL 5.7.24
  and uses `sudo apt-get` for deps (all replaceable with conda) and a `nobarrier` mount for the log
  device (needs root — must be skipped).
- Workload generators are public and buildable in user space: Percona `tpcc-mysql`
  (github.com/Percona-Lab/tpcc-mysql, cited [37]) and LinkBench
  (github.com/facebookarchive/linkbench, cited [17]). No proprietary traces are used; TPC-C data is
  generated locally.
- Baselines: stock MySQL 5.6.26 source is publicly archived (mysql/mysql-server tag `mysql-5.6.26`,
  downloads.mysql.com archives), so "Vanilla" is obtainable. CF-LRU is emulated purely with
  `innodb_lru_scan_depth` (Table 4), so it is free. **WAR (An et al., SIGMOD'22) has no public
  implementation I could find** — the group's released repos (`meeeejin/rw-rbuf`,
  `meeeejin/mysql-57-nvdimm-caching`) are different papers — so the 1.52×-over-WAR claim is not
  checkable here.
- Metrics used by the paper are all root-free: `performance_schema` mutex waits (Table 3),
  `SHOW ENGINE INNODB STATUS` hit/miss ratios (Table 7), `iostat` over `/proc/diskstats` (Table 5),
  `tpcc_start` latency output (Table 6). No `perf`, no eBPF, no hardware counters anywhere.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper p. 1 "PVLDB Artifact Availability … https://github.com/LeeBohyun/LRU-C"; first author's account. The tree contains the real mechanism, not a stub: `buf0buf.h:1979` (LRU-C pointer), `buf0lru.cc:456` (pointer maintenance), `buf0lru.cc:1414-1446` (rewritten miss path), `buf0flu.cc:2309` (dynamic batch), `buf0buf.h:2041` (LRU-D mutex). |
| `H2_no_root` | **pass** | Pure user-space C++ change inside InnoDB; build is CMake + make into `$HOME`, mysqld runs as an unprivileged user. `repo_facts.json` red flags are all false positives: "reboot" strings are stock MySQL/NDB comments (`sql/nt_servc.cc:479`), "docker" is `packaging/rpm-docker` (`CMakeLists.txt:498`), "Infiniband" is an NDB SCI transporter comment, "Hugepagesize" is stock `mysys/my_largepage.c:103` (only used when `--large-pages` is requested; leave it off). Caveats that must be dropped, not worked around: the paper's `dd` device pre-conditioning, its raw/separate log device, and the install guide's `nobarrier` mount all need root and are skippable at the cost of absolute-number comparability. |
| `H3_hardware_fit` | **pass** | CPU-and-NVMe-only; no GPU involved. 16c/32t ≥ the paper's 64-client concurrency point is reachable (paper's own Fig. 9 runs 8–128 clients on 32 cores). The paper's 100 GB DB does not fit comfortably in ~257 GB free with logs + a second baseline datadir, but the paper itself uses a **10 GB / 100-warehouse** configuration with 10% buffer for Figs. 10 and 12, giving a documented scale-down. Fig. 10 (Cosmos+ OpenSSD channel count), Fig. 11 (4 distinct SSD models), Fig. 12 (GCP/Azure) and Fig. 13 (HDD) are out of reach — but they are secondary to the headline claim. |
| `H4_obtainable_deps_data` | **pass** | All deps user-space installable (conda gcc toolchain, ncurses, bison, libaio; bundled SSL/zlib/libedit; system cmake 3.25.1). Workloads are synthetic and public: `tpcc-mysql` [37] and LinkBench [17]. Baseline "Vanilla" = public MySQL 5.6.26 source. No proprietary traces. Only the WAR baseline is unobtainable, which removes one comparison curve but not the datasets. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** Figure 7a at the 10% buffer point, plus its companion Table 3 / Table 7 rows:
*LRU-C delivers ≈3× the TPC-C throughput of a knob-tuned Vanilla MySQL, with the read-stall ratio
driven to ~0 and the miss ratio only ~1.25× higher.* Equivalently, the Vanilla (247) vs. final LRU-C
(755) endpoints of Figure 6. I would **not** target the intermediate Fig. 6 bars ("Basic LRU-C",
"+Dynamic-Batch-Write") as the first result, because the repo has no knob to disable the optimizations
individually (§2, discrepancy 5) — those bars need code surgery and belong to week 3+.

**Scale-down.** 100 warehouses (~10 GB TPC-C database) instead of 1,000 (~100 GB), matching the paper's
own configuration for §5.2.6/§5.2.7-cloud. Buffer pool swept 5–25% → 0.5–2.5 GB, 8 buffer-pool
instances, 64 client threads, `innodb_flush_method=O_DIRECT`, redo log on the same NVMe (no second
device available), 10-minute measurement after 5-minute warm-up, 3 runs. A single 10 GB dataset is
reloaded between runs from a `mysqldump`/datadir snapshot to control for aging. Expect *absolute* TPS
to differ from the paper (different SSD, no raw device, no separate log device, no `nobarrier`); the
testable quantity is the **ratio** LRU-C/Vanilla at each buffer size.

**Steps.**
1. Create a conda env with gcc 9/10, bison, ncurses, libaio; verify `LINUX_NATIVE_AIO=1` appears in the
   cmake output (`storage/innobase/CMakeLists.txt:25-30`).
2. Build the LRU-C tree with the *system* cmake 3.25.1 (not pip cmake 4.x, see `CMakeLists.txt:16`),
   `-DWITH_SSL=bundled -DCMAKE_INSTALL_PREFIX=$HOME/...`, keeping `INNODB_PAGE_ATOMIC_REF_COUNT=ON`.
3. **Comment out `buf0lru.cc:1399`** before any timing run, and re-check the `buf0flu.cc:2412/2419`
   mutex balance; run first under a low-concurrency smoke test to see whether the double-release
   manifests.
4. Build stock `mysql-5.6.26` from the MySQL archive with identical flags → "Vanilla"; apply the
   §5.2.1 I/O knob tuning (`innodb_io_capacity`, `innodb_io_capacity_max`, `innodb_flush_neighbors=0`)
   and record the exact my.cnf, since the paper only describes it prose-wise.
5. Build `tpcc-mysql`, load 100 warehouses, snapshot the datadir.
6. Sweep buffer ratio 5/10/15/20/25% × {Vanilla, LRU-C}; collect TPS and latency from `tpcc_start`,
   miss ratio from `SHOW ENGINE INNODB STATUS`, mutex waits from `performance_schema`, device IOPS from
   `iostat`.
7. Derive the read-stall ratio (Table 3) by instrumenting single-page flushes on the miss path — the
   paper defines it as single-page-flush count / total misses (§5.2.2); no counter for this exists in
   the repo, so ~20 lines must be added to both builds.

**Effort.** ≈ 6–9 person-days (dominated by getting a 2015 codebase to compile and by re-deriving the
Vanilla my.cnf) + ≈ 30–40 machine-hours of benchmark time (0 GPU-hours). Data loading of 100 warehouses
is itself a few hours per reload.

**Level: M.** Not H because: no evaluation scripts, configs or plotting code ship with the artifact; the
baselines are separate builds the team must assemble; the dependency pins are a decade old and the
toolchain on this machine is far newer; the exact "tuned Vanilla" configuration is described only in
prose (§5.2.1); and the released code contains a live hot-path `fprintf` and at least one apparent
mutex-balance bug that must be fixed before any number is trustworthy. Not L because the mechanism is
fully present, the workloads are public and synthetic, the metrics need no root, and the paper supplies
a 10 GB scale-down configuration itself.

## 5. Add-on ideas

### A1 — Is LRU-C just CF-LRU with an O(1) pointer? Adaptive clean-window

**Hypothesis.** We hypothesize that making the clean-eviction window adaptive (controlled online from
free-list starvation and observed miss-ratio slope) reduces LRU-C's miss-ratio penalty (Table 7:
1.21–1.36× Vanilla) by at least half at ≤5% TPS cost, and that LRU-C's throughput is *materially
sensitive* to the currently-implicit window size — under TPC-C and LinkBench at 5–25% buffer ratios.

**Mechanism.** The released code silently confines the LRU-C pointer to the InnoDB *old* sublist
(`buf0lru.cc:494,506,515`), i.e. it already implements a fixed clean-first window of
`innodb_old_blocks_pct` (default 37%). Step 1: expose that window as a first-class system variable and
sweep it (this is the CF-LRU window sweep of Table 4, but with LRU-C's O(1) pointer, so the scan cost
that made CF-LRU non-monotone is removed — the sweep directly tests §6's claim that LRU-C "is not just a
victim selection policy"). Step 2: replace the fixed bound with an AIMD controller that grows the window
when the free list starves (read stalls imminent) and shrinks it when the measured miss ratio rises
faster than the throughput gain.

**Code locations.** `storage/innobase/buf/buf0lru.cc:456` (`buf_update_oldest_clean_page`, the
`LRU_old` / `LRU_old_len` / `buf_page_is_old` bounds), `storage/innobase/buf/buf0lru.cc:1417`
(`buf_LRU_get_free_block` fallback), `storage/innobase/buf/buf0flu.cc:2309` (flusher feedback signal),
`storage/innobase/handler/ha_innodb.cc:16044` (new sysvar next to `lru_scan_depth`),
`storage/innobase/srv/srv0srv.cc:223`.

**Motivating evidence.** §4.4 and Table 7 concede the hit-ratio loss and never study how to bound it.
Table 4 shows CF-LRU's window is strongly non-monotone (TPS 243→346→316 as scan depth goes
512→4,096→16,384) and §6 argues LRU-C is categorically different — but the code shows LRU-C *is* window-
bounded, just with an undeclared, untuned window. The paper never sweeps it.

**Feasibility: H.** ~300–600 LOC in two files plus one sysvar; evaluated with the same `tpcc-mysql`
harness at the 10 GB scale-down; no new hardware. Well within 2–4 students × 10 weeks.

**Research value: M.** A VLDB reviewer would care about the CF-LRU-equivalence question, and the
sensitivity sweep is cheap and informative. But the delivered mechanism (an adaptive window) is a
standard, expected fix, and part of the work is a parameter sweep, which caps the value.

**Scoop check.** Queries: *"clean-first eviction hit ratio loss adaptive CF-LRU window workload shift
database buffer 2024 2025"*; Semantic Scholar citation list for DOI 10.14778/3598581.3598605.
`result: partial`. Adaptive clean-first variants exist in the older literature (CFDC, FD-Buffer [35]) and
adaptive multi-grained buffering (MDPI Future Internet 13(12):303) is adjacent, but no work re-examines
LRU-C's own window. Closest: https://www.mdpi.com/1999-5903/13/12/303.

### A2 — Do LRU-C's gains survive on an engine with multi-threaded page cleaners?

**Hypothesis.** We hypothesize that porting LRU-C to an InnoDB generation with multiple page-cleaner
threads and a natively split LRU-list mutex (MySQL 5.7.x, stretch goal 8.0.x) shrinks the reported 3×
TPC-C speedup over Vanilla to well under 2×, because much of the measured gain in the paper comes from a
single-cleaner, 2015-vintage baseline rather than from the LRU-C pointer itself.

**Mechanism.** Re-apply the ~300–1,000 LOC of LRU-C (pointer, LRU-D mutex, dynamic batch) onto
MySQL 5.7's `buf0lru.cc`/`buf0flu.cc`, which are structurally close to 5.6 but add
`innodb_page_cleaners`. Then run a 2×2: {stock, LRU-C} × {1 cleaner, N cleaners}, decomposing how much
of the gain is read-stall removal, how much is mutex splitting, and how much simply disappears when the
baseline flusher is allowed to be parallel.

**Code locations.** `storage/innobase/buf/buf0lru.cc:1414` (miss path to be re-applied),
`storage/innobase/buf/buf0flu.cc:2309` (`buf_flush_LRU_tail`, which becomes per-cleaner in 5.7),
`storage/innobase/buf/buf0flu.cc:1857` (`buf_flush_batch` mutex choice),
`storage/innobase/include/buf0buf.h:1979` (pointer and LRU-D fields to port),
`storage/innobase/buf/buf0buf.cc:1364` (mutex creation).

**Motivating evidence.** The artifact is MySQL 5.6.26 (`VERSION`), released 2015 and EOL 2021; the
paper's §2.3 argument rests on "MySQL/InnoDB has *recently* divided `buffer_pool_mutex` into three
mutexes" and on a single `page_cleaner_thread` (§4.5). Fig. 9 shows Vanilla TPS *halving* from 8 to 16
threads — an unusually fragile baseline that a reviewer would immediately question. Nothing in the paper
tests a modern flusher. The course rubric explicitly accepts "reproduction showing the results are more
nuanced" as a landing spot, and either outcome here is publishable-shaped.

**Feasibility: M.** Cross-version port: the InnoDB buffer module changed between 5.6 and 5.7 (page
cleaner coordinator/worker split, `buf_flush_page_cleaner_coordinator`), so this is a careful re-write
rather than a patch application, and 5.7 needs boost. The evaluation reuses the A-plan harness. Heavy
but sized for a 10-week team project.

**Research value: H.** It attacks the paper's headline number at its weakest joint — the baseline — in a
regime the paper ignores. A negative result ("the gain is mostly a stale-baseline artifact") and a
positive result ("LRU-C still wins with N cleaners") are both genuinely interesting to the venue.

**Scoop check.** Queries: Semantic Scholar citations of the paper (16 citing works, listed in §7);
*"io_uring InnoDB buffer pool page cleaner asynchronous I/O database 2025"*. `result: clear`. None of the
16 citing works re-implements or re-evaluates LRU-C; the closest systems work, LeanStore VLDB'24
(https://dl.acm.org/doi/10.14778/3685800.3685915), is a different engine and does not revisit LRU-C.

### A3 — Feedback-controlled write batching for tail latency

**Hypothesis.** We hypothesize that replacing LRU-C's fixed `LRU_len/8` flush batch with a controller
that targets a free-list level and a bounded device queue occupancy improves TPC-C 99.9th-percentile
latency by ≥2× at equal or better TPS, under write-heavy mixes (R:W 1:1–2:1) at 5–10% buffer ratios.

**Mechanism.** `buf_flush_LRU_tail` currently bursts up to `UT_LIST_GET_LEN(buf_pool->LRU)/8` pages per
wakeup and then calls `buf_dblwr_flush_buffered_writes()` once (`buf0flu.cc:2414`), a synchronous
serialization point at the end of each burst. Replace the fixed cap with a PI/AIMD controller over
(free-list length, in-flight `n_flush[BUF_FLUSH_LRU]`), and chunk the doublewrite flush so foreground
reads are never queued behind a whole batch. Measure p50/p99/p99.9 with a per-transaction latency
histogram rather than the paper's single 95th/99th figures.

**Code locations.** `storage/innobase/buf/buf0flu.cc:2309` (`buf_flush_LRU_tail`),
`storage/innobase/buf/buf0flu.cc:2348` (the `/8` cap), `storage/innobase/buf/buf0flu.cc:1510`
(`buf_flush_LRU_list_batch`), `storage/innobase/buf/buf0dblwr.cc`,
`storage/innobase/handler/ha_innodb.cc:16044`.

**Motivating evidence.** §4.3 claims the batch is "all dirty pages behind the pointer" but the code caps
it at `LRU_len/8` (`buf0flu.cc:2348`) — the paper's described mechanism and its artifact disagree, and
neither variant is justified by a measurement. Table 6 shows LRU-C's 99th latency is still 391 ms —
7.4× its 95th — so the tail is far from solved even though the paper advertises tail-latency reduction.
Table 5 shows LRU-C reaching only 64% of device peak bandwidth, and the paper concedes "there is still
some room for further optimization".

**Feasibility: H.** Localized to the flusher (one file, a few hundred LOC) plus a latency histogram in
the client; reuses the reproduction harness; no extra hardware.

**Research value: M.** Tail-latency control for buffer-pool flushing is well-trodden territory
(InnoDB's own adaptive flushing, MySQL WL#7868), so a win is expected rather than surprising; the
novelty is in the LRU-C-specific interaction between dynamic batching and the clean window.

**Scoop check.** Queries: *"adaptive batch size page cleaner flush tail latency database buffer pool SSD
2024 2025"*; citation list. `result: partial`. InnoDB already chunks "furious flushing" by
`innodb_io_capacity` since 8.0.19 (https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool-flushing.html),
and *Set associative address mapping … reduce tail latency in SSDs* (JSA 2025) attacks tail latency
inside the device, not in the buffer manager. No LRU-C-specific work found.

### A4 — io_uring-backed dynamic batch write

**Hypothesis.** We hypothesize that issuing LRU-C's dynamic batch through io_uring (registered files,
batched submission, `IOSQE_IO_LINK`-free independent SQEs) instead of `libaio`/`io_submit` raises
achieved write IOPS and closes a meaningful part of the 64% → 100% device-peak gap of Table 5,
improving TPC-C TPS at 5–10% buffer ratios where the flusher is the bottleneck.

**Mechanism.** Add an io_uring backend alongside InnoDB's native-AIO path in `os0file.cc`, selected by a
system variable, with one ring per write-I/O thread; keep the existing completion handshake
(`aio_write_finished` in `buf0lru.cc:2358`) so the LRU-C pointer logic is untouched. liburing is built
into `$HOME`; kernel 6.1 on this machine supports io_uring for unprivileged users.

**Code locations.** `storage/innobase/os/os0file.cc` (AIO array / `os_aio_linux_*`),
`storage/innobase/buf/buf0flu.cc:2396` (submission site in the LRU batch),
`storage/innobase/buf/buf0dblwr.cc` (doublewrite writes),
`storage/innobase/include/buf0buf.h:1470` (`aio_write_finished` completion flag).

**Motivating evidence.** Table 5: LRU-C uses 524 MB/s of a measured 815 MB/s device ceiling and the
paper explicitly says there is "still some room for further optimization". §2.2 notes the flusher
"use[s] Linux AIO"; `storage/innobase/CMakeLists.txt:25-30` confirms libaio is the only async path and
that its absence silently degrades to simulated AIO. The paper never measures whether the remaining
36% is a buffer-manager limit or an I/O-submission-layer limit — that is exactly the question.

**Feasibility: M.** Cross-cutting: touching InnoDB's AIO layer risks destabilizing the whole engine, and
the 5.6 AIO code is tightly coupled to its simulated-AIO abstraction. No root needed and the compute
fits, but it is the riskiest of the four to land.

**Research value: M.** The direction is plausible and the diagnostic ("is the residual gap in the buffer
manager or the syscall layer?") is worthwhile, but "io_uring is faster than libaio for DBMS writes" is
close to an expected result and has been studied generally.

**Scoop check.** Queries: *"io_uring InnoDB buffer pool page cleaner asynchronous I/O database 2025"*;
citation list. `result: partial`. *io_uring for High-Performance DBMSs: When and How to Use It*
(https://arxiv.org/pdf/2512.04859) covers io_uring in DBMSs generally, and *Flexible I/O for Database
Management Systems with xNVMe* (CIDR'26) cites LRU-C while doing I/O-interface work — so the general
io_uring-for-DBMS question is taken. The LRU-C-specific combination (does the clean-pointer architecture
still gate throughput once submission is cheap?) is not.

### A5 — Removing the residual checkpoint serialization

**Hypothesis.** We hypothesize that making checkpoint flushing of mixed-region dirty pages lock-free
with respect to LRU-M (e.g. by flushing from the flush-list under `flush_list_mutex` only, with a
deferred LRU reposition) removes the last RW-serialization LRU-C admits to, improving TPS during
checkpoint-heavy phases (small redo logs, write-heavy mixes) by a measurable margin.

**Mechanism.** Today the flusher must take LRU-M to checkpoint dirty pages that sit ahead of the LRU-C
pointer. Instead, checkpoint writes would touch only `flush_list` state and enqueue LRU repositioning
onto a per-instance deferred queue drained by the foreground thread that next holds LRU-M. Evaluate with
`innodb_log_file_size` varied to force different checkpoint pressures.

**Code locations.** `storage/innobase/buf/buf0flu.cc:1864` (`BUF_FLUSH_LIST` branch that still takes
`buf_pool->mutex`), `storage/innobase/buf/buf0flu.cc:1090` (mutex choice inside `buf_flush_page`),
`storage/innobase/log/log0log.cc`, `storage/innobase/include/buf0buf.h:2029` (flush-list mutex macros).

**Motivating evidence.** §4.3, final paragraph: "LRU-C is not free from RW-serialization: it incurs
another RW-serialization due to the checkpointing … the background flusher in LRU-C also has to acquire
the LRU-M mutex". The paper asserts without measurement that "the peril of checkpoint-induced I/O
serialization is insignificant" — an untested simplifying assumption, and exactly the kind a reviewer
would probe.

**Feasibility: M.** Deferred-reposition queues inside InnoDB's buffer pool are delicate (page relocation,
`flush_list_hp`, shutdown paths); the change is cross-cutting but bounded, and the evaluation reuses the
existing harness with one extra knob sweep.

**Research value: M.** It closes the paper's own stated loose end. Downgraded from H because the same
lab appears to have moved in this direction already (see scoop check), so the headline may be taken.

**Scoop check.** Queries: *"Hot-Page-Aware Checkpointing for Flash SSDs" ICDEW 2026*; citation list.
`result: partial`. *Hot-Page-Aware Checkpointing for Flash SSDs* (Park & Lee, ICDEW 2026,
doi 10.1109/ICDEW71238.2026.00007, https://borecraft.com/2026/05/03/hot-page-aware-checkpointing-for-flash-ssds/)
is by the same group and targets flash-aware checkpointing; I could not read it to confirm whether it
specifically removes the LRU-M/checkpoint interaction. Treat this add-on as likely-contested and read
that paper before committing to it.

Also noted for context: **twCache** (ICDE 2025, https://ieeexplore.ieee.org/document/11113152/)
partitions the replacement-policy structure into thread-wise sublists to kill LRU lock contention. That
overlaps with any add-on of the form "shard the LRU mutex further than two regions", so I deliberately
did not propose one.

## 6. Risks and open questions

1. **Building a 2015 codebase with gcc 12.2 / glibc 2.36 is the single largest unknown.** I could not
   verify compilability by reading. Mitigation: conda gcc 9/10 + `-std=gnu++03 -fpermissive`. If that
   fails, the whole project fails; the team should spend day 1 on this, not week 3.
2. **cmake version trap.** `CMakeLists.txt:16` declares `VERSION 2.6`; the pip cmake 4.x documented in
   `env.md` will refuse it. Use the system cmake 3.25.1.
3. **libaio availability is unconfirmed.** Without it, `storage/innobase/CMakeLists.txt:25-30` falls back
   to simulated AIO and the paper's central "parallel async writes" premise is no longer being tested.
   Verify `LINUX_NATIVE_AIO=1` in the cmake log before trusting any number.
4. **Live debug output on the hot path** (`buf0lru.cc:1399`) and an **apparent unbalanced mutex release**
   (`buf0flu.cc:2412` vs. `:2419`) plus an **uninitialized read** (`buf0flu.cc:2326`) mean the released
   binary is not the binary that produced the paper's figures, or the paper's figures were produced with
   these defects in place. Either way the first reproduction result should be treated as provisional
   until these are resolved.
5. **The artifact has no eval harness at all** — no my.cnf, no run scripts, no plotting. The §5.2.1
   "tuned Vanilla" configuration exists only as prose, so the 3× ratio is sensitive to how the team
   tunes the baseline. There is a real risk of accidentally producing a *larger* speedup by
   under-tuning Vanilla.
6. **No LRU-C on/off knob**, so Vanilla and LRU-C are different binaries; compiler flags, `-O` level and
   `INNODB_PAGE_ATOMIC_REF_COUNT` must be pinned identically across builds or the comparison is invalid.
7. **Storage budget and shared-machine noise.** ~257 GB free on a *shared* 2×NVMe software RAID. The
   10 GB scale-down is mandatory; even so, repeated TPC-C loads plus two datadirs plus snapshots will
   consume 100+ GB, and sustained write benchmarks on a shared box will both suffer from and cause
   interference. Absolute IOPS numbers will not match Table 5.
8. **No root ⇒ no raw device, no `dd` pre-conditioning, no `nobarrier`.** SSD steady-state behaviour
   (the paper runs each device "half-full" and pre-conditions it) cannot be reproduced; results will be
   on a file in ext4 on a RAID, which changes write amplification and GC behaviour.
9. **Unreproducible figures:** Fig. 10 (Cosmos+ OpenSSD), Fig. 11 (SSD-B/C/D), Fig. 12 (GCP/Azure),
   Fig. 13 (HDD). The WAR baseline (Fig. 7, Tables 5–6) appears to have no public code, so the
   1.52×-over-WAR claim is out of reach.
10. **Open question, and the most scientifically interesting one:** the implemented LRU-C confines its
    clean-page search to the old sublist (`buf0lru.cc:494,506,515`), contradicting §4.2/§5.2.2's
    description of a pointer that can reach the LRU head. Is the evaluated system the one the paper
    describes? A1 is designed to answer this.

## 7. Evidence index

**Paper.** Abstract (p. 1); Fig. 1 (p. 1); §2.1 Table 1 (p. 2); §2.2 Fig. 2 (p. 3); §2.3 read-stall
4.86 ms / 1.3% mutex wait (p. 3), Fig. 3 (p. 4); §3 Table 2 (p. 4); §4.1 key idea (p. 5); §4.2
Algorithm 1 + Fig. 4 (p. 5); §4.3 dynamic-batch-write, LRU-M/LRU-D, Fig. 5, checkpoint caveat (pp. 5–6);
§4.4 hit-ratio cost (p. 7); §4.5 prototype "<300 lines" (p. 7); §5.1 setup + workloads (p. 7);
§5.2.1 tuned Vanilla (p. 7); §5.2.2 Fig. 6 + Table 3 + "working set changes" caveat (pp. 7–8);
§5.2.3 Fig. 7a/7b, Table 4 (CF-LRU scan-depth sweep), Table 5 (IOPS/BW/CPU), Table 6 (latency),
Table 7 (miss ratio) (pp. 8–9); §5.2.4 Fig. 8 (p. 10); §5.2.5 Fig. 9 (p. 10); §5.2.6 Fig. 10 (p. 10);
§5.2.7 Fig. 11, Fig. 12, Fig. 13 (pp. 10–11); §6 CF-LRU / WAR / Shore-MT comparison (pp. 11–12);
artifact availability statement (p. 1). Page image read: `pages/page-07.png` (Fig. 6, Table 3, §5.1).

**Repo paths.** `README.md`; `VERSION`; `CMakeLists.txt:16,327,498`; `config.h.cmake:554`;
`storage/innobase/CMakeLists.txt:25-30`; `storage/innobase/include/buf0buf.h:1461-1472,1977-1987,2029-2051`;
`storage/innobase/include/buf0types.h:29-31`; `storage/innobase/buf/buf0buf.cc:279,1364,1378-1381,1439-1442,3438-3441`;
`storage/innobase/buf/buf0lru.cc:451-546,548-581,1380-1465,1638-1648,1921-1952,2173-2175,2241-2246,2358`;
`storage/innobase/buf/buf0flu.cc:1090-1096,1169-1208,1501-1664,1850-1888,1917-2013,2300-2435,2672,2695-2735`;
`storage/innobase/handler/ha_innodb.cc:16044`; `storage/innobase/srv/srv0srv.cc:223`;
`storage/innobase/srv/srv0start.cc:2727`; `storage/innobase/os/os0file.cc`;
`storage/innobase/buf/buf0dblwr.cc`; `storage/innobase/log/log0log.cc`; `scripts/*.sh`;
`mysys/my_largepage.c:103`; `sql/nt_servc.cc:479`;
`storage/ndb/src/common/transporter/SCI_Transporter.hpp:46`.

**External.** Semantic Scholar citation list for DOI 10.14778/3598581.3598605 (16 citing papers, incl.
LeanStore VLDB'24, twCache ICDE'25, Hot-Page-Aware Checkpointing ICDEW'26, xNVMe CIDR'26, *How to Write
to SSDs* VLDB'26); https://github.com/LeeBohyun/mysql-tpcc installation guide (build/run procedure);
https://github.com/Percona-Lab/tpcc-mysql; https://github.com/facebookarchive/linkbench;
https://ieeexplore.ieee.org/document/11113152/ (twCache);
https://borecraft.com/2026/05/03/hot-page-aware-checkpointing-for-flash-ssds/;
https://arxiv.org/pdf/2512.04859 (io_uring for DBMSs);
https://dl.acm.org/doi/10.14778/3685800.3685915 (LeanStore VLDB'24);
https://dl.acm.org/doi/abs/10.1145/3514221.3526126 (WAR, SIGMOD'22 — no public artifact found).
