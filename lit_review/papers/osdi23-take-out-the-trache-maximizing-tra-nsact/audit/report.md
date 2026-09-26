# Take Out the TraChe: Maximizing (Tra)nsactional Ca(che) Hit Rate

OSDI '23 · Cheng, Chu, Li, Chan, Crooks, Hellerstein, Stoica (UC Berkeley), Yu (UW–Madison)
Repo audited: `repo/` = https://github.com/audreyccheng/detox @ `b36054be` (2023-08-24)

## 1. Paper summary

**Problem.** Standard cache policies (LRU, LFU, GDSF, even offline Belady) maximize *object
hit rate*. For transactional workloads this is the wrong objective: a transaction's latency is
set by its *critical length* — the longest chain of non-cached, sequentially-dependent accesses
in its execution DAG (paper §3.2, Def. 5). Keys requested in parallel have an all-or-nothing
property: caching one of `{a2,a3}` in Figure 1 buys nothing. On Meta's TAOBench Product Group 3,
>90% of the keys LRU/LFU keep resident are "unhelpful" (§2.1, Figure 2a), and LRU/LFU reach
object hit rates up to 51 points above their transactional hit rates (Figure 2b).

**Key idea.** Define **transactional hit rate (THR)** = `Σ(L(Gi,{}) − L(Gi,Ci)) / Σ L(Gi,{})`
(§3.3, Def. 7) and score *groups* of keys, not individual keys. Belady is shown non-optimal for
THR (§2.2, Figure 3), and optimal offline transactional caching is proven NP-hard by reduction
from variable-sized caching (§3.4, Appendix A.2).

**Design (DeToX).**
- *Complete groups* (§4.1, Def. 8): minimal key sets whose caching reduces critical length;
  extracted at compile time from statically-derived transaction execution graphs.
- *Group score* (§4.2.1): `SCORE_G(g) = min(F_g) · L_g / S_g` — minimum key frequency in the
  group (a cold key "contaminates" its hot partners), critical-length reduction, group byte size.
- *Instance → key score* (§4.2.2–4.2.3): greedily assign the highest-scoring complete group's
  score to its keys, iterate over supersets; aggregate as `SCORE_K = TS_key/F_key + A_global`,
  where `A_global` is the GDSF-style aging factor reset to each evicted key's score.
- *Interchangeability* (§5.1, Def. 9): compress the exponential set of complete groups into
  swappable equivalence classes so only a linear number need run-time scoring.
- *Levels* (§5.2): fallback when application code is unavailable — group keys that are issued
  to the store in parallel. This is what is used for TAOBench (§8.1, footnote 1).
- *Prefetching* (§6): per-request tracking of the most frequent subsequent dependent key set,
  fetched preemptively, bounded by a set-count cap and a frequency threshold.

**Implementation (§7).** ~7K LOC Java shim over Redis 7.0 + Postgres 12.10 (or TiKV 5.4.3);
2PL with timeout deadlock detection in the shim; writes go to the store and update the cache at
commit; `MGET` is overloaded in Redis to delimit a parallel group and recompute scores
("less than 100 lines of code"); a Python trace simulator for offline Belady / Transactional Belady.

**Evaluation setup (§8.1).** Four EC2 roles: shim + Postgres on `c5a.4xlarge` (16 vCPU/32 GB),
Redis on `r5.4xlarge` (16 vCPU/128 GB), clients on `c5a.16xlarge`; 0.2 ms intra-region RTT;
3 × 5-minute runs with 60 s warm-up; eviction by sampling 10 candidates. Workloads: TAOBench
PG1/PG2/PG3 (100M objects ≈ 1 TB), Epinions (2M users/1M items ≈ 1 TB), SmallBank (500M uniform
accounts ≈ 1 TB), TPC-C (100 warehouses ≈ 8 GB). Baselines: LRU, LFU, GDSF, LIFE (PACMan),
ChronoCache.

**Headline numbers.** Up to 76% higher THR on TAOBench PG2/PG3 (Figure 8a/8b); at 25% relative
cache size DeToX reaches 88% THR on PG2 where the best single-object policy needs 3.4× more
cache (§8.2); +31% throughput / −30% latency on PG2 (Figure 9). Epinions +41% THR, 1.6× cache
efficiency (Figure 10a). SmallBank 1.3× THR, +28% throughput, ~2/3 of it from prefetching (§8.2,
Figure 11). **Negative results the paper reports itself:** PG1 (97% point reads) gains 2%;
TPC-C (write-heavy, long tail) gains nothing — "DeToX performs on par with single-object policies"
(§8.2). Figure 14 shows DeToX has among the *lowest* object hit rates, i.e. THR trades I/O
bandwidth for latency (§8.5). Overheads: <5% CPU vs LRU for levels/interchangeable groups;
complete groups blow up past transaction size 15 (Figure 12a/12b); metadata <1–2% of cache (§8.3).

## 2. Artifact audit

### Repo structure (as shipped)

| dir | what | size/role |
|---|---|---|
| `redis/` | Redis (version.h says `255.255.255`, i.e. an unstable/7.x snapshot) with 4 added eviction policies | the DeToX **eviction** policy lives here |
| `sys/` | the Java shim ("shield" — inherited from the Obladi/Shield codebase) + benchmark drivers | the DeToX **shim, prefetching, THR metric** |
| `simulator/` | 2 Python files: offline Belady and Transactional Belady | Figure 14 offline curves |
| `chronocache/`, `oltpbench-chronocache/` | modified ChronoCache + OLTPBench, for the ChronoCache baseline and Epinions | baseline only |

Repo is 293 MB / 15 117 files, but most of that is noise: `sys/external-jars/openemr-5.0.0/`
is a vendored PHP EMR application (leftover from an unused FreeHealth benchmark) and accounts
for the 716 K lines of `.js`. Actual DeToX-specific code is small.

### Paper component → code path

| paper section | code |
|---|---|
| §7.2 eviction, group score `min(F)/S + A` | `redis/src/t_string.c:557-612` (`mgetCommand` hijacked as "commit": computes `minF`, `S`, writes `o->fsl`) |
| §4.2.3 aggregate score = running average | `redis/src/t_string.c:596-603` (`MAXMEMORY_AVG_FSL` branch: `total_fs/number_fs`) |
| §4.2.3 global aging factor `A_global` | `redis/src/evict.c:293-300` (`FSLGetL`/`FSLSetL`), updated to the evicted key's score at `redis/src/evict.c:705-714, 806-807` |
| sampled eviction (§8.1, 10 samples) | `redis/src/evict.c:150-196` (`evictionPoolPopulate`, `idle = ULLONG_MAX - fsl*10000`) |
| GDSF baseline (§8) | `redis/src/t_string.c:127-129, 333-335` |
| LIFE baseline (PACMan) | `redis/src/t_string.c:604-609` (`fsl = 1/(S+1)`) |
| policy registration | `redis/src/config.c:55-66`; `redis/src/server.h:533-536`; new `robj` fields `fsl/total_fs/number_fs` at `redis/src/server.h:857` |
| §5.2 levels (parallel batch = one `MGET`) | `sys/src/main/java/shield/client/RedisPostgresClient.java:1108-1140` |
| §6 prefetching (dependency sets, freq threshold, cap) | `sys/src/main/java/shield/client/RedisPostgresClient.java:43-111, 986-1057` |
| §7.1 2PL shim | `sys/src/main/java/shield/client/RedisPostgresClient.java:1059-1098` (per-key `ReentrantReadWriteLock`, randomized 500–2000 ms timeout) |
| §3.3 THR measurement | `sys/src/main/java/shield/benchmarks/utils/CacheStats.java:18-51` — `spedUpLayers/totalLayers` is THR, `cachedRequests/totalRequests` is OHR |
| Appendix A.1 Transactional Belady | `simulator/dag_txn_belady.py` |
| Figure 14 Belady | `simulator/dag_belady_cache.py` |
| benchmarks | `sys/src/main/java/shield/benchmarks/{taobench,smallbank,tpcc}/` |

### What is **not** in the repo

1. **Complete groups (§4.1) and interchangeability (§5.1) are absent.** A case-insensitive grep
   for `interchangeab|completeGroup|criticalLength` over the whole repo returns only hits in
   vendored third-party files (OpenEMR licences, Lua docs). A grep for `roup` across
   `sys/src/main/java/shield` returns 42 hits in 7 files — all Netty `EventLoopGroup` and
   TAOBench key-range variables named `group_1/2/3`. There is no DAG, no longest-path, no
   powerset/subset enumeration anywhere (`powerset|subsets|combinations|longest.?path|topolog`
   → no files). **The released DeToX is the levels-only variant.** Consequently Figures 12a–12d
   (Microbenchmarks 1 and 2, the entire "need for dependency analysis" story) cannot be
   reproduced from this artifact without reimplementing §4.1/§5.1.
2. **The `L_group` term is missing from the shipped group score.** Paper §4.2.1 is
   `min(F)·L/S`; `redis/src/t_string.c:591` computes `minF/S + A`. Consistent with levels
   (where `L = 1` per level), but it means the critical-length weighting is untested.
3. **`S` is a key count, not a byte count.** `redis/src/t_string.c:581` does `S++` per non-null
   string key; `S_group` in §4.2.1 is "the sum of all key sizes". Harmless for the paper's
   workloads (TAOBench values are fixed at 75 bytes —
   `sys/.../taobench/TaoBenchExperimentConfiguration.java:34`), but it means the variable-size
   claim is never exercised.
4. **No `*ExpConfig.json` files.** The README (lines 37–53) tells you to configure
   `____ExpConfig.json`; grep for `ExpConfig` under `sys/` returns nothing. `sys/benchmarks/`
   contains only `cs6410/` and `cs6410tmp/` — ORAM configs
   (`"backing_store_type": "parallel_ring_oram"`) from the unrelated Shield project. The JSON key
   names are recoverable from the `getProp*` calls in
   `sys/.../taobench/TaoBenchExperimentConfiguration.java:170-195` and
   `sys/.../config/NodeConfiguration.java:640-650`, so this is transcription work, not a blocker.
5. **PG1/PG2/PG3 workload parameterisation is undocumented commented-out constants.**
   `TaoBenchExperimentConfiguration.java:27-43` has e.g. `PROB_TRX_READ = 58.0; //49.0; // 59.0;`
   and three `TXN_SIZES_*` lists; `taobench/ReadTransaction.java:45-47` and
   `ReadScan.java:49-53` have alternate key-generation expressions commented out. Which variant
   is PG2 vs PG3 must be re-derived from the paper's prose (§8.2).
6. **No Epinions driver for DeToX.** Epinions exists only under `oltpbench-chronocache/` (the
   ChronoCache baseline); `sys/src/main/java/shield/benchmarks/` has taobench, smallbank, tpcc,
   ycsb, freehealth, micro — no epinions. Figure 10a's DeToX curve is therefore not directly
   reproducible.
7. **Simulator is incomplete.** Both `simulator/*.py` start with `import workload`; no
   `workload.py` exists (the directory has exactly 2 files). `dag_txn_belady.py:176` hardcodes
   `"test3.txt"`, which is not shipped, and no trace dumper exists in the shim. The import is
   dead code (easy to delete) but the traces must be generated by instrumenting the shim.
8. **No plotting scripts, no run scripts.** The only `.sh` under `sys/` outside vendored code is
   `sys/benchmarks/cs6410/run.sh` (ORAM) and `sys/src/main/java/shield/network/messages/compile.sh`
   (protobuf).

### Build route on *this* machine

- **Redis**: `cd redis && make`. Plain C, vendored deps (jemalloc, hiredis, lua). gcc 12.2 and
  make 4.3 are present. No root. The shipped `redis/redis.conf` is already
  `maxmemory 12mb` / `maxmemory-policy min-fsl` / `maxmemory-samples 5` (lines 1084, 1114, 1125)
  — note the paper says 10 samples (§8.1).
- **Shim**: `cd sys && mvn clean install && mvn assembly:single`. **Maven is not on this machine**
  (not in `env.md`'s software table); it installs as a user-space tarball into `$HOME`, no root.
  `sys/pom.xml:97-99` pins `maven.compiler.source/target = 1.8`; JDK 17 and 21 are both on PATH
  and both still accept `-source 8` (with a deprecation warning).
- **Postgres**: README lines 62–74 use `sudo apt install postgresql` + `systemctl` + editing
  `/etc/postgresql/12/main/pg_hba.conf`. **None of that is required**: a user-space Postgres
  (conda-forge `postgresql`, or built from source into `$HOME`) with `initdb` into `$HOME`, a
  non-default port and a local `pg_hba.conf` gives the same thing without root. Everything runs
  on one host so the "allow 0.0.0.0/0" step is unnecessary.
- **TiKV**: not needed for the Postgres results; would require `tiup playground` (single-node PD +
  TiKV is possible on this box, but it is extra work and only needed for Figure 16).

### Dependency pins and their age (`sys/pom.xml`)

| dep | pin | note |
|---|---|---|
| `redis.clients:jedis` | 4.1.1 (2022) | fine |
| `postgresql:postgresql` | `9.1-901-1.jdbc4` (2011) | **risk**: this driver predates SCRAM-SHA-256; against a modern (PG ≥ 10) server with default `scram-sha-256` auth it will fail. Fix: set `md5`/`trust` in the user-space `pg_hba.conf`, or bump to `org.postgresql:postgresql:42.x` |
| `org.tikv:tikv-client-java` | 3.1.0 | only needed on the TiKV path; pulls a large shaded tree |
| `com.amazonaws:aws-java-sdk` | 1.11.268 (2017) | huge, unused at run time but resolved at build |
| `mysql:mysql-connector-java` | 6.0.6 | legacy coordinates, still on Central |
| `io.netty:netty-all` | 4.1.20.Final | legacy Shield networking, unused on the Redis path |
| `org.mapdb:mapdb`, `bouncycastle`, `commons-crypto` | 2017-era | Shield leftovers |

All are on Maven Central and resolvable in user space (`~/.m2`). Nothing needs a system package.

### Data / traces / models

None are downloaded. **All workloads are generated in-process**: `TaoBenchGenerator.java`,
`SmallBankGenerator.java`, `TPCCGenerator.java` synthesise Zipfian/uniform key streams;
`TaoBenchLoader.java` populates Postgres. There is no Meta trace file, no external dataset, no
model weights. `nb_objects` / `base_size` / `nb_accounts` are JSON-configurable
(`TaoBenchExperimentConfiguration.java:170-171, 191`), with defaults `NB_OBJECTS = 100000` —
i.e. the code already defaults to a 1000× scale-down of the paper's 100M.

### Eval harness present/absent

Present: end-to-end runnable clients that print exactly the headline metrics —
`StartSmallBankTrxClient.main` (`sys/.../smallbank/StartSmallBankTrxClient.java:155-170`) prints
throughput, latency, prefetch memory, then `CacheStats.printReport()` which prints
`spedUpLayers/totalLayers` (= THR) and `cachedRequests/totalRequests` (= OHR). Same for TAOBench
and TPC-C. Absent: config files, sweep scripts, plotting, Epinions, §4.1/§5.1, simulator traces.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper Appendix B (Artifact Appendix, p. 22) names `https://github.com/audreyccheng/detox` as the artifact; `audreyccheng` is first author Audrey Cheng. Page 2 carries a USENIX "Artifact Evaluated — Available" badge. The repo contains the real system: DeToX eviction in `redis/src/t_string.c:557-612` + `redis/src/evict.c:150-196`, shim/prefetch in `sys/src/main/java/shield/client/RedisPostgresClient.java`, THR metric in `sys/.../utils/CacheStats.java`, benchmarks, simulator. **Caveat:** the complete-group/interchangeability machinery of §4.1/§5.1 is not present anywhere in the repo (grep evidence in §2). The released system is the levels variant — enough for Figures 8/10 but not Figure 12. |
| `H2_no_root` | **pass** | No kernel module, eBPF, `perf`, KVM, hugepage setup or cgroup requirement in any DeToX code path. `redis/Makefile` is a plain source build. The only root steps are README lines 62–74 (`sudo apt install postgresql`, `systemctl`, editing `/etc/postgresql/.../pg_hba.conf`), all replaceable by a user-space Postgres (conda-forge or source + `initdb` in `$HOME` on a user port); everything is co-located so the network-opening step is moot. `repo_facts.json` red flags are false positives: `sysctl_hugepages` hits are vendored jemalloc *reading* `/proc/sys/vm/overcommit_memory` (`redis/deps/jemalloc/src/pages.c:475-496`); `custom_kernel` hits are upstream Redis comments (`redis/src/sentinel.c`, `redis/src/config.c`); `kernel_module` is a line in an unused dstat plugin under `oltpbench-chronocache/tools/`. Maven is not installed but is a user-space tarball. |
| `H3_hardware_fit` | **pass** | Four EC2 roles (§8.1) collapse onto one host: client threads, shim, Redis and Postgres are all ordinary user processes; 16 cores / 125 GB RAM is comparable to the sum of the paper's roles for a scaled-down dataset. No GPU is used at all. The 1 TB datasets are a config knob, not a design requirement (`nb_objects` default is already 100 000, `TaoBenchExperimentConfiguration.java:32`), and the x-axis of every THR figure is *relative* cache size, so scale-down preserves the claim. §8.6 explicitly argues THR is independent of system specifics. Multi-node is only needed for TiKV (Figure 16), which is optional. Disk: a 1M-object TAOBench at 75 B values is well under 1 GB in Postgres; ~250 GB free is ample. |
| `H4_obtainable_deps_data` | **pass** | No datasets at all: every workload is synthesised in-repo (`sys/.../taobench/TaoBenchGenerator.java`, `smallbank/SmallBankGenerator.java`, `tpcc/TPCCGenerator.java`). TAOBench here is the *benchmark generator*, not a Meta trace. All Maven deps are public Central artifacts installable into `~/.m2`; Redis vendors its own C deps; Java 17/21 already on PATH; Maven installs user-space. The only friction is the 2011 Postgres JDBC pin vs modern server auth (fix in `pg_hba.conf` or bump the pin). |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** Figure 8a (TAOBench Product Group 2): THR vs relative cache size for DeToX vs LRU /
LFU / GDSF / LIFE, supporting the claim "at 25% relative cache size DeToX reaches ~88% THR while
the best single-object policy needs 3.4× more cache" (§8.2). Fallback/companion target:
Figure 10b (SmallBank, 1.3× THR) — simpler workload, driver present, fewer undocumented knobs.

**Scale-down.** `nb_objects = 1,000,000` (vs 100M), 75-byte values ⇒ ~100–200 MB of Postgres
data; Redis `maxmemory` set to {1, 5, 10, 25, 40, 55, 70, 85, 100}% of that. Everything on one
box: 4 benchmark threads × 3 request threads (`threads` / `req_threads_per_bm_thread` in the
config), 90 s runs with 30 s ramp-up instead of 5 min + 60 s, 2 repeats instead of 3. Absolute
throughput/latency will *not* match the paper (the paper had a 0.2 ms network between tiers and
dedicated machines; here the loopback is ~0.02 ms, which *shrinks* the cache-vs-store latency
gap and hence the throughput win — see §8.6 / Figure 15a, where the DeToX advantage grows with
store latency). THR, the target metric, is the one the paper argues is setup-independent. If the
throughput delta is needed, inject artificial delay on the Postgres path as the paper does in §8.6.

**Steps.**
1. Install Maven 3.9 tarball into `$HOME`; install Postgres (conda-forge, pin a 12.x/14.x build),
   `initdb -D ~/pgdata`, set `pg_hba.conf` to `md5`/`trust`, start on port 5433, create
   `admin/password` and database `benchmark` (matching `NodeConfiguration.java:428-432`).
2. `cd redis && make` → `src/redis-server`. Edit `redis/redis.conf`: `maxmemory <X>`,
   `maxmemory-policy min-fsl` (or `avg-fsl` — see risk below), `maxmemory-samples 10`.
3. Flip `USE_SQL` to `true` at
   `sys/src/main/java/shield/client/RedisPostgresClient.java:52` — it is hard-coded `false` and
   never reassigned, so the shipped default routes to **TiKV**, not Postgres, contradicting the
   README's "default database is Postgres".
4. Write `TaoBenchLoadConfig.json` and `TaoBenchExpConfig.json` from the `getProp*` keys in
   `TaoBenchExperimentConfiguration.java:170-195` and `NodeConfiguration.java:640-650`
   (`client_type: "redis_postgres"`, `redis_enabled`, `redis_prefetch`, `nb_objects`, `threads`,
   `exp_length`, `postgres_hostname`, …). Load with `redis_enabled: false` (README step 4).
5. Build both jars (`pom.xml:103-117` hard-codes the TAOBench main class and final name; edit for
   SmallBank/TPC-C), load, then sweep cache sizes × policies, reading THR off
   `CacheStats.printReport()`.
6. Plot by hand (no plotting scripts exist).

**Effort.** ≈ 5–8 person-days (2 students) + ~25 CPU-hours, 0 GPU-hours. Breakdown: 1–2 days for
the user-space Postgres + Maven + JDBC-auth plumbing and re-deriving the config JSONs; 1 day for
the loader/runner loop and the `USE_SQL` / policy-name discrepancies; 1 day to pin down which
commented-out constants in `TaoBenchExperimentConfiguration.java:27-43` give PG2 vs PG3; the rest
is sweeping (9 cache sizes × 5 policies × 2 repeats × ~2.5 min ≈ 4 h per workload, plus reload
time) and plotting.

**Level: M.** The policy code, the baselines and the THR metric are all present and print the
target number directly, and the machine comfortably fits a scale-down — that is the "H" part.
But the artifact has no config files, no run scripts, no plotting, a hard-coded default that
selects the wrong backend, undocumented per-product-group constants, a root-flavoured Postgres
install that must be substituted, and a 14-year-old JDBC pin. That is real porting work in the
sense the rubric defines for **M**, not the "scripts exist, just run them" of **H**. The artifact
carries only the *Available* badge — there is no evidence of a *Reproduced* badge to lean on.

## 5. Add-on ideas

### A1 — Does dependency analysis actually pay off? (complete/interchangeable groups vs levels on real workloads)

- **Hypothesis.** We hypothesize that implementing complete groups + interchangeability (§4.1,
  §5.1) yields less than 5 percentage points of THR over the shipped levels policy on every
  *real* OLTP benchmark (TPC-C `Order-Status`/`New-Order`, SmallBank, Epinions) — i.e. the
  paper's most complex mechanism is unnecessary outside its hand-built Microbenchmark 2 — while
  costing measurable run-time CPU on deep, unbalanced transaction topologies.
- **Mechanism.** Add a compile-time pass over a declarative description of each benchmark's
  transaction DAG (the DAGs are already implicit in the driver code, e.g.
  `sys/.../tpcc/OrderStatusTransaction.java`), enumerate complete groups by the powerset +
  critical-length algorithm of §4.1, compress them into interchangeable classes per §5.1, and
  replace the single per-level `MGET` score update with a shim-side instance-scoring pass
  (§4.2.2 greedy superset iteration) that pushes explicit per-key scores to Redis via a new
  command (or by writing `o->fsl` through an extended `MGET`-like verb). Then sweep the three
  grouping strategies (complete / interchangeable / levels) plus T-DeToX on the real benchmarks,
  not just on the synthetic topology of Figure 6a.
- **`code_locations`**: `sys/src/main/java/shield/client/RedisPostgresClient.java`,
  `sys/src/main/java/shield/client/RedisStatement.java`,
  `sys/src/main/java/shield/benchmarks/tpcc/OrderStatusTransaction.java`,
  `redis/src/t_string.c`, `redis/src/server.h`.
- **Motivating evidence.** (a) The mechanism is simply **absent from the artifact** (grep evidence,
  §2). (b) The paper concedes §8.2: "Since all transactions in these workloads have symmetric
  structures, there is no difference in performance between our various grouping techniques."
  (c) The only place complete groups win is Microbenchmark 2 (Figure 12d), a single hand-designed
  transaction type with hot/cold branches. (d) §5.2 states levels "produce identical results …
  for transactions in which all keys and groups are interchangeable (… including all the ones we
  evaluate in Section 8)". So the paper's own text says the headline evaluation never exercises
  §4.1/§5.1 — nobody has shown whether they matter on a real workload.
- **feasibility: M.** Cross-cutting: new compile-time component, a new shim→Redis scoring path,
  and a new comparison harness. But the algorithms are fully specified in the paper, the
  transaction set is small (TPC-C has 5 types, SmallBank 6), and the eval reuses the existing
  `CacheStats` THR counter on this machine. Comfortably a 10-week task for 2–4 students, but not
  a localized patch.
- **research_value: H.** It fills the artifact's biggest hole *and* tests the paper's central
  design claim in the regime the paper skipped. Either outcome is publishable-shaped: "levels
  are enough, drop the compile-time analysis" is a strong simplification result; "complete groups
  win by X% on TPC-C" completes the paper's own evaluation.
- **scoop_check: clear.** Queries: "DeToX transactional hit rate caching follow-up 2025";
  "learned cache eviction transaction dependency groups DeToX improvement 2024 2025";
  "Audrey Cheng Berkeley transactional caching follow-up 2024 2025". No follow-up on transactional
  caching found; the first author's later work is on transaction *scheduling*
  ([Towards Optimal Transaction Scheduling, VLDB '24](https://www.vldb.org/pvldb/vol17/p2694-cheng.pdf))
  and concurrency conflicts, not caching. Closest related work is
  [PACMan (NSDI '12)](https://www.usenix.org/system/files/conference/nsdi12/pacman.pdf), already
  a baseline.

### A2 — Write-aware group scoring (fixing the TPC-C null result)

- **Hypothesis.** We hypothesize that discounting a group's score by the write rate of its member
  keys (expected residency before invalidation) improves THR by ≥10% relative on write-heavy
  transactional workloads (TPC-C, and a TAOBench variant with the write fraction raised from ~4%
  to 20–40%), compared with DeToX's write-oblivious `min(F)/S` score.
- **Mechanism.** Add a per-object write counter and a decayed write-rate estimate to `robj`
  alongside `fsl/total_fs/number_fs`; increment it on the cache-update path taken at commit
  (`setGenericCommand`). Change the group score from `min(F_g)/S_g` to
  `min(F_g)·Π(1−ŵ_k·Δ)/S_g` (or the simpler `min_k(F_k/(1+ŵ_k))/S_g`), so a group containing one
  frequently-invalidated key is de-prioritised the same way a cold key contaminates its partners
  today. Expose the write-penalty weight as a `redis.conf` knob and sweep it.
- **`code_locations`**: `redis/src/t_string.c`, `redis/src/server.h`, `redis/src/db.c`,
  `redis/src/evict.c`, `redis/src/config.c`,
  `sys/src/main/java/shield/benchmarks/tpcc/NewOrderTransaction.java`.
- **Motivating evidence.** The paper reports an explicit negative on TPC-C (§8.2: "TPC-C cannot
  benefit from transactional caching … DeToX performs on par with single-object policies") and
  attributes it to hot/cold mixing and recency, without ever considering invalidation. Yet the
  shim sends **all writes straight to the store and refreshes the cache at commit** (§7.1), so in
  a write-heavy workload a group's members are repeatedly reset —
  `redis/src/db.c:226-229` deliberately carries `fsl` across an overwrite, and `object.c:57-60`
  resets it on creation, i.e. write behaviour visibly affects scoring but is never modelled. THR
  as measured also counts a level as a hit only if *every* request in it is served from cache
  (`CacheStats.java:20`), so write-containing levels can never be transactional hits — an
  interaction the paper does not discuss.
- **feasibility: H.** Localized: a few hundred lines across 4 Redis files plus config plumbing;
  the TPC-C driver and the THR counter already exist; runs on this machine with no extra data.
- **research_value: H.** It targets the paper's own clearest failure case with a mechanism the
  paper never considered, and both outcomes teach something: if it works, transactional caching
  extends to write-heavy OLTP; if it does not, the paper's "hot/cold contamination" explanation
  for TPC-C is confirmed against a real alternative hypothesis.
- **scoop_check: partial.** Write-aware / cost-aware eviction is well-trodden for single objects
  (GD-Wheel, cost-aware GreedyDual, [TinyLFU](https://dl.acm.org/doi/10.1145/3149371)), but I
  found nothing applying it to *transactional group* scores. Queries: "transactional hit rate
  cache admission policy transaction groups OLTP write-aware eviction"; "transactional caching
  variable object sizes all-or-nothing group caching 2025". Related but distinct:
  [Lightweight Inter-transaction Caching with … Dynamic Self-invalidation](https://arxiv.org/pdf/2003.04150)
  (invalidation protocol, not scoring).

### A3 — Transaction-aware cache *admission*

- **Hypothesis.** We hypothesize that a group-aware admission filter — refusing to admit keys
  whose enclosing level's `min(F)` falls below the current eviction-pool score — raises THR at
  small relative cache sizes (1–10%) by ≥15% relative and cuts cache write traffic by ≥2×,
  compared with DeToX's admit-everything policy, on TAOBench PG3 and TPC-C.
- **Mechanism.** Today every miss is populated into Redis unconditionally by the shim
  (`RedisPostgresClient` write-back after a store read) and `mgetCommand` scores whatever is
  resident. Add an admission decision at the level boundary: compute the prospective group score
  before insertion and compare it against `FSLGetL()` (the aging factor, which already equals the
  last evicted key's score, `redis/src/evict.c:806-807`); admit the whole group or none of it —
  the all-or-nothing property applies to admission exactly as it does to eviction. Implement as a
  new Redis command invoked in place of the current per-key `SET`, plus a shim-side batch.
- **`code_locations`**: `redis/src/t_string.c`, `redis/src/evict.c`, `redis/src/config.c`,
  `sys/src/main/java/shield/client/RedisPostgresClient.java`, `redis/redis.conf`.
- **Motivating evidence.** The paper states this as explicit future work (§9, Admission
  algorithms): "While we focus on eviction and prefetching in this paper, our grouping and scoring
  strategies can feasibly extend to admission, which we will explore in future work." The regime
  where it should matter most is visible in Figures 8 and 10: at 1–10% relative cache size all
  policies, DeToX included, sit near the bottom of the THR curve.
- **feasibility: H.** Small, localized, reuses the existing aging factor as a threshold and the
  existing THR harness; the 1–10% cache-size points are the cheapest to run.
- **research_value: M.** Well-motivated and useful, but it is the extension the authors
  themselves signposted, and "group admission helps at small caches" is close to the expected
  outcome — a solid rather than surprising result.
- **scoop_check: clear.** Queries as above. Nothing found that applies admission control at the
  transactional-group level; the admission literature found
  ([TinyLFU](https://dl.acm.org/doi/10.1145/3149371),
  [size-aware admission](https://arxiv.org/pdf/2105.08770)) is all single-object.

### A4 — Variable object sizes: the regime the formalism claims but the evaluation never tests

- **Hypothesis.** We hypothesize that under heavy-tailed object sizes (Zipfian/lognormal value
  sizes spanning 3 orders of magnitude, as in real KV caches) the shipped DeToX loses its THR
  advantage over GDSF — and that restoring the paper's true `S_group = Σ sizes` (instead of the
  implemented key count) recovers it, by ≥10 percentage points of THR at 10–25% relative cache
  size on TAOBench PG3.
- **Mechanism.** (i) Fix `mgetCommand` to accumulate `stringObjectLen(o)` rather than `S++`,
  matching §4.2.1. (ii) Extend the TAOBench generator/loader to draw value sizes from a
  configurable heavy-tailed distribution (the `DATA_SIZES`/`DATA_WEIGHTS` lists already exist and
  are set to the degenerate `[75]` / `[1.0]`). (iii) Sweep DeToX (count-`S` vs byte-`S`) against
  GDSF, LRU, LFU, LIFE; report THR and bytes-per-transactional-hit.
- **`code_locations`**: `redis/src/t_string.c`,
  `sys/src/main/java/shield/benchmarks/taobench/TaoBenchExperimentConfiguration.java`,
  `sys/src/main/java/shield/benchmarks/taobench/TaoBenchGenerator.java`,
  `sys/src/main/java/shield/benchmarks/taobench/TaoBenchLoader.java`.
- **Motivating evidence.** The paper's NP-hardness proof reduces from *variable-sized* caching
  (§3.4, Appendix A.2) and `S_group` is one of three terms in `SCORE_G` (§4.2.1) — yet every
  evaluated workload uses near-uniform objects (TAOBench `DATA_SIZES = [75]`,
  `TaoBenchExperimentConfiguration.java:34`) and the shipped code doesn't even measure bytes
  (`redis/src/t_string.c:581`). The size term is therefore entirely untested, and GDSF — the
  size-aware baseline DeToX was derived from — has never been given the regime it was designed for.
- **feasibility: H.** A one-line semantic fix in Redis plus a generator change; the sweep is the
  same harness and fits easily on this machine.
- **research_value: M.** Variable object size is the canonical caching regime and finding a
  paper/implementation divergence is a genuine contribution, but the expected story ("size term
  matters when sizes vary") is not surprising on its own; value depends on whether the ranking
  actually flips.
- **scoop_check: clear.** Queries: "transactional caching variable object sizes all-or-nothing
  group caching 2025"; results were all single-object size-aware caching
  ([Practical Bounds on Optimal Caching with Variable Object Sizes](https://arxiv.org/pdf/1711.03709),
  [Lightweight Robust Size Aware Cache Management](https://arxiv.org/pdf/2105.08770)) — related
  but not transactional.

### A5 — How far is DeToX from the transactional optimum?

- **Hypothesis.** We hypothesize that a sharing-aware offline policy (greedy over a bounded
  lookahead, maximizing transactional hits per cached byte and accounting for keys shared across
  transactions) achieves ≥10 points higher THR than Transactional Belady on TAOBench PG3 and
  SmallBank, showing that the DeToX-to-optimum gap in Figure 14b is substantially larger than the
  paper's Transactional-Belady line suggests.
- **Mechanism.** Add a trace dumper to the shim (emit one line per transaction, `;`-separated
  levels, `,`-separated keys — exactly the format `dag_txn_belady.py:44-50` already parses),
  repair the simulator (`import workload` is dead and the module is missing; `test3.txt` is
  hardcoded at `dag_txn_belady.py:176`), then add a third policy that scores cached sets by
  (number of future transactional hits enabled)/(bytes) over a window, rather than by
  next-hit distance.
- **`code_locations`**: `simulator/dag_txn_belady.py`, `simulator/dag_belady_cache.py`,
  `sys/src/main/java/shield/client/RedisPostgresClient.java`,
  `sys/src/main/java/shield/benchmarks/utils/CacheStats.java`.
- **Motivating evidence.** Appendix A.1 (Figure 17) *proves* Transactional Belady is not optimal
  precisely because "Transactional Belady does not account for shared keys across transactions",
  yet Figure 14b uses it as the de-facto upper bound and the paper never quantifies the residual
  gap. Without a real bound, nobody knows whether DeToX's remaining headroom is 5 points or 40.
- **feasibility: M.** Pure Python on dumped traces — cheap to run, and the only new system work
  is the trace dumper. But the simulator is incomplete (missing module, missing traces, no
  generator) and a lookahead-based policy over millions of requests needs care to stay tractable,
  so it is more than a localized patch.
- **research_value: M.** A headroom study is genuinely useful to anyone building on THR and
  directly follows the paper's own Appendix, but it produces a measurement rather than a system
  improvement — a reviewer would call it a good section, not a good paper.
- **scoop_check: clear.** Queries as above; no work found computing offline bounds for
  transactional hit rate. The nearest analogue is
  [Berger et al., Practical Bounds on Optimal Caching with Variable Object Sizes](https://arxiv.org/pdf/1711.03709),
  which does exactly this for the *object* hit rate — a good methodological template, and its
  absence in the transactional setting is the gap.

## 6. Risks and open questions

1. **Which policy name *is* DeToX?** `redis.conf:1114` ships `min-fsl`, which assigns the raw
   instance score (`minF/S + A`, `t_string.c:590-595`). But §4.2.3 and Figure 13b say DeToX uses
   the **average** of instance scores — that is `avg-fsl` (`t_string.c:596-603`). The README
   (line 87) lists both without saying which is the paper's system. A reproduction must run both
   and report which matches Figure 8. **Unresolved by reading.**
2. **Wrong backend by default.** `RedisPostgresClient.java:52` hard-codes `USE_SQL = false` and
   nothing ever assigns it, so a fresh build targets TiKV while the README says Postgres is the
   default. Silent misconfiguration risk.
3. **Missing config files** (`*ExpConfig.json`) and **undocumented PG1/2/3 constants**
   (`TaoBenchExperimentConfiguration.java:27-43`, `ReadTransaction.java:45-47`) mean the exact
   workload of Figures 8a/8b must be reverse-engineered from §8.2 prose. Expect the absolute THR
   values to differ from the paper even if the *ordering* of policies reproduces.
4. **§4.1/§5.1 are unreleased.** Figures 12a–12d are out of reach without reimplementation; any
   claim about "complete groups" in the project must be about the team's own implementation, not
   the authors'.
5. **Single-host timing distortion.** Co-locating client/shim/Redis/Postgres on 16 cores removes
   the paper's 0.2 ms inter-tier network; §8.6/Figure 15 shows DeToX's throughput advantage grows
   with store latency, so the co-located setup is the *least* favourable case for DeToX.
   Additionally `RedisPostgresClient.java:1115` busy-waits (`while (!r.done) {}`) per request,
   which burns cores under oversubscription. Keep thread counts low, or inject artificial store
   latency as §8.6 does. THR should be unaffected; throughput/latency will be.
6. **Old JDBC pin vs modern Postgres auth.** `pom.xml:17-20` pins the 2011 `postgresql
   9.1-901-1.jdbc4` driver, which cannot do SCRAM-SHA-256. Must pin an older server, set
   `md5`/`trust` in the user-space `pg_hba.conf`, or bump the driver.
7. **Maven not installed.** `env.md` does not list `mvn`; it must be unpacked into `$HOME`
   (no root needed, but it is an extra setup step and the first thing that will fail).
8. **Simulator is not runnable as shipped** (missing `workload.py`, missing `test3.txt`, no trace
   dumper). Anything touching Figure 14 needs the dumper written first.
9. **Repo hygiene.** 293 MB dominated by `sys/external-jars/openemr-5.0.0/` (a vendored PHP app)
   and `sys/benchmarks/cs6410*` (ORAM configs from the unrelated Shield project). Harmless but it
   makes "where is the real code?" slow, and `git clone` is heavy.
10. **Only the "Available" badge.** The page-2 stamp is Artifacts Available; I found no evidence
    of Functional or Reproduced badges, so there is no external confirmation that anyone outside
    the authors has re-run these numbers.

## 7. Evidence index

**Paper** (`paper.txt`, `pages/page-NN.png`):
§1 Introduction (contributions, 1.3×/3.4× headline); §2.1 + Figure 2a/2b (90% unhelpful keys,
51-point OHR/THR gap); §2.2 + Figure 3 (Belady non-optimality); §3.1–3.3 Defs. 1–7 (execution
graph, critical length, THR); §3.4 + Appendix A.2 (NP-hardness from variable-sized caching);
§4.1 Def. 8 (complete groups); §4.2.1 (`SCORE_G = min(F)·L/S`); §4.2.2 (instance scoring);
§4.2.3 (`SCORE_K = TS/F + A_global`); §5.1 Def. 9 + Figure 7 (interchangeability); §5.2 (levels,
"identical results … including all the ones we evaluate in Section 8"); §6 (prefetching);
§7.1–7.2 (shim, 2PL, <100 LOC Redis change, Python simulator); §8.1 (EC2 setup, workload sizes,
10 eviction samples); §8.2 + Figures 8, 9, 10, 11 (TAOBench/Epinions/SmallBank/TPC-C results,
PG1 and TPC-C null results); §8.3 + Figure 12 (grouping overheads, Microbenchmarks 1/2, metadata);
§8.4 + Figure 13 (Min instance score, Avg aggregate score); §8.5 + Figure 14 (OHR vs THR,
Belady / Transactional Belady); §8.6 + Figures 15, 16 (network latency, simulation, TiKV);
§9 Admission ("we will explore in future work"); Appendix A.1 + Figure 17 (Transactional Belady
non-optimality, shared keys); Appendix B (Artifact Appendix, repo URL, commit 604c9bd, deps);
page-02.png (USENIX "Artifact Evaluated — Available" badge); page-11.png (Figures 8, 9);
page-22.png (Appendix B).

**Repository** (paths relative to `repo/`):
`README.md` (structure, build steps, `sudo apt install postgresql`, policy names, EC2 note);
`.gitignore`; `redis/redis.conf` (lines 1084, 1114, 1125); `redis/Makefile`;
`redis/src/t_string.c` (34, 127-129, 333-335, 552-612); `redis/src/evict.c` (150-196, 293-300,
642, 705-714, 806-807); `redis/src/server.h` (533-536, 857, 3167-3168); `redis/src/config.c`
(55-66, 2833); `redis/src/db.c` (113-115, 226-229); `redis/src/object.c` (57-60, 108-111);
`redis/src/version.h`; `redis/deps/jemalloc/src/pages.c` (475-496, false-positive red flag);
`sys/pom.xml` (10-96 deps, 97-99 source/target 1.8, 103-117 assembly);
`sys/src/main/java/shield/client/RedisPostgresClient.java` (43-52 `PREFETCH_*` + `USE_SQL`,
54-111 `PrefetchTracker`/`PrefetchSet`, 141-146 `lastLayerMap`, 971-1154 `executeOps`,
1156+ `executeOpsTiKV`);
`sys/src/main/java/shield/client/RedisStatement.java`;
`sys/src/main/java/shield/benchmarks/utils/CacheStats.java` (6-51);
`sys/src/main/java/shield/config/NodeConfiguration.java` (422-432, 640-650);
`sys/src/main/java/shield/benchmarks/taobench/TaoBenchExperimentConfiguration.java`
(23-43, 32 `NB_OBJECTS`, 34 `DATA_SIZES`, 170-195);
`sys/src/main/java/shield/benchmarks/taobench/TaoBenchGenerator.java`;
`sys/src/main/java/shield/benchmarks/taobench/TaoBenchLoader.java` (26-51);
`sys/src/main/java/shield/benchmarks/taobench/ReadTransaction.java` (45-47);
`sys/src/main/java/shield/benchmarks/taobench/ReadScan.java` (49-53);
`sys/src/main/java/shield/benchmarks/smallbank/StartSmallBankTrxClient.java` (63-171);
`sys/src/main/java/shield/benchmarks/tpcc/OrderStatusTransaction.java`;
`sys/src/main/java/shield/benchmarks/tpcc/NewOrderTransaction.java`;
`sys/src/main/java/shield/benchmarks/utils/ClientUtils.java` (17-42 `ClientType`);
`sys/benchmarks/cs6410/proram-batch10-lat0-threads-1.json` (ORAM leftovers);
`sys/src/main/java/shield/tests/config/interactiveConfig.json` (Shield leftovers);
`simulator/dag_txn_belady.py` (1-2 dead `import workload`, 36-68 trace format, 108-157 THR
accounting, 176 hardcoded `test3.txt`); `simulator/dag_belady_cache.py` (1-2, 50-60);
`oltpbench-chronocache/src/com/oltpbenchmark/benchmarks/epinions/` (Epinions exists only here);
`repo_facts.json` (head commit, red flags, GitHub metadata: 14 stars, Apache-2.0, pushed
2023-12-13).

**Web:** [USENIX OSDI '23 presentation page](https://www.usenix.org/conference/osdi23/presentation/cheng)
(authors; page itself returned 403 to automated fetch, badge read from `pages/page-02.png` instead);
[Audrey Cheng's site](https://audreyccheng.com/) (repo owner = first author);
[Towards Optimal Transaction Scheduling, VLDB '24](https://www.vldb.org/pvldb/vol17/p2694-cheng.pdf)
(first author's later work — not a caching follow-up);
[PACMan, NSDI '12](https://www.usenix.org/system/files/conference/nsdi12/pacman.pdf) (LIFE baseline);
[TinyLFU](https://dl.acm.org/doi/10.1145/3149371) and
[Lightweight Robust Size Aware Cache Management](https://arxiv.org/pdf/2105.08770) (single-object
admission, scoop-check comparators);
[Practical Bounds on Optimal Caching with Variable Object Sizes](https://arxiv.org/pdf/1711.03709)
(offline-bound methodology for A5).
