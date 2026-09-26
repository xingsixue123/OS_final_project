# Structural Designs Meet Optimality: Exploring Optimized LSM-tree Structures in a Colossal Configuration Space

*(SIGMOD / PACMMOD 2, 3, Article 175, June 2024 — Liu, Wang, Mo, Luo, NTU. Repo: `NTU-Siqiang-Group/MooseLSM`.)*
Desk review only: nothing was built or run. Every claim below points at a paper section/figure or a repository path.

## 1. Paper summary

**Problem.** Mainstream LSM-trees fix the size ratio `T` and the number of sorted runs per level
globally (leveling) or nearly globally (tiering, Dostoevsky's two run-counts, LSM-Bush's doubling
size ratios). The paper argues (§1, "Problem 1"/"Problem 2", p.2–3; Table 1, p.2) that this
constrained configuration space prevents co-optimizing *point lookup*, *range lookup* and *update*
at the same time.

**Key idea.** "LSM-tree generalization" (§3.1, p.5): give every level `i` its own run count `n_i`
and run magnification `s_i`, so the per-level size ratio is `r_i = s_i · n_i` (Eq. 1) and Bloom
filter bits-per-key can differ per level. Cost models are then re-derived over this space:
update `U = O(Σ 1/B · N_i/N_{i-1} · 1/n_i)` (Eq. 2, §3.2), range lookup `R = O(Σ n_i)` (Eq. 3),
point lookup `Z = O(Σ n_i · p_i)` (Eq. 4).

**Design.** Two insights drive **Moose**:
1. Optimal point lookup needs a *large last level* — maximizing `Σ N_i log N_i` under `Σ N_i = N`
   pushes capacity into `N_L` (§3.3, Eq. 11, p.10).
2. The Pareto-optimal range-lookup/update ("RU") curve is reached when `n_i = k·√r_i` (§3.3;
   restated §3.6, p.16).

Given `N_L`, the remaining level capacities `{N_1..N_{L-1}}` minimizing `A = Σ √(N_i/N_{i-1})` are
found by **dynamic programming** over states `S(N_d, N_r)` (Eq. 12, §3.4, p.11, Fig. 2). Bloom bits
follow a Monkey-style rule generalized to per-run sizes: `n_i·p_i/N_i` constant across levels
(Eq. 10, §3.3). Default Moose: `N_L = 0.8N`, `k = 1`. Space amplification is bounded by
`(N/N_L)·n_L < 3.54` in the default setting (Eq. 15–16, §3.5, p.15).

**Smoose** (§3.6, p.16–17) is the workload-aware variant: minimize `L = s·S + u·U + z·Z` (Eq. 17)
by enumerating `N_L` from `0.5N` to `N` in steps of the buffer size `F`, running the DP for each,
and enumerating `k` (running example uses `k ∈ [0.5, 2]`). The search takes 1.52 s on average
(max 4.43 s) for `N` from 1 GB to 16 GB.

**Eval setup** (§4, p.17). Intel Xeon W-2235 @3.8 GHz, **32 GB RAM, 512 GB SATA SSD**, Ubuntu 20.04,
ext4. Implementation on top of RocksDB. ~11 GB bulk-loaded (24 B key + 1000 B value), then 2,000,000
operations per workload. Buffer 2 MB, Bloom budget 5 bits/key, Monkey filter policy applied to *all*
baselines. Baselines: Leveling (T=10), Tiering (T=10), LazyLeveling (T=10), QLSM-Bush (T=2, X=2),
and workload-aware Dostoevsky + tuned RocksDB.

**Headline numbers.**
- Fig. 7 (p.17): normalized throughput on two- and three-way mixes; Moose beats all non-workload-aware
  baselines except two range-heavy points where Leveling is slightly better.
- Fig. 8 + Table 4 (p.18): ranking across 10 workloads A–J. Average rank: Smoose **1.0**, Dostoevsky 3.1,
  Moose 3.2, tuned RocksDB 3.7, Leveling 5.2, LazyLeveling 5.8, Tiering 6.3, QLSM-Bush 7.3.
- Table 5 (p.19): raw `#IO-per-query / compacted GB / #compactions`. e.g. workload J:
  Leveling 2.94/22/203, Moose 3.06/9/221, Smoose 2.35/12/222.
- Table 3 (p.17): Smoose's chosen `{r_i}`/`{n_i}` per workload (e.g. J → ris 11,12,11,6; nis 2,2,2,1).
- Fig. 9 (p.19): (A) Moose vs RocksDB across storage layouts/KV sizes; (B,C) with Snappy/Zlib/BZip2;
  (D) measured space amplification (Leveling smallest, Moose second).
- Fig. 10 (p.21): (A) `k` sweep, (B) `N_L` sweep justifying `0.8N`, (C) growing `N` to 8 GB,
  (D) cost-model prediction vs measured latency.

**Stated limitations.** §3.5 "Assumptions and Relaxations" (p.14): the analysis is worst-case and
needs real-system validation. §3.6 (p.16): "the cost of non-zero result point lookup is not
specialized in the model since its probabilistic is uncertain for Smoose". §3.6 (p.17): Smoose is
"initially designed for static workload tuning"; substantial workload change "require[s] structural
transformation", for which the authors only *suggest* a lazy strategy and preemptive compaction.
§6 (p.23): future work is integration into a full DBMS.

## 2. Artifact audit

### Repo structure

`repo/` is a **fork of RocksDB 8.9.0** (`include/rocksdb/version.h:14-16`), 2058 files, 39 MB,
655 k lines of C/C++. HEAD `ede0e34`, dated **2024-06-11**; GitHub `pushed_at` 2026-04-14 (metadata
touch only — the working tree here is the 2024-06 state). 6 stars, 4 forks, not archived,
license NOASSERTION (README §License: "NTUITIVE PTE LTD Dual License").

**Officiality.** `NTU-Siqiang-Group` is the corresponding author's lab org; `README.md:9` links
`https://siqiangluo.com/docs/SIGMOD24_MOOSE_Camera___Junfeng___Fan.pdf` and gives the exact BibTeX
for this article (`README.md:12-21`). The paper itself contains **no** artifact/availability
statement and does not cite the repo (grep for `artifact|github` in `paper.txt` returns only
references [10],[22],[23]). No ACM artifact badge found.

### Paper component → code path

| paper component | code |
|---|---|
| LSM-tree generalization: per-level `{N_i}`, `{n_i}` (§3.1, Eq. 1) | `include/rocksdb/options.h` / `options/cf_options.{h,cc}`: `level_capacities` (vector of **physical run** capacities) and `run_numbers` (runs per logical level) |
| new compaction style | `include/rocksdb/advanced_options.h:37` `kCompactionStyleMoose = 0x4`; registered in `options/options_helper.cc:336,808`; dispatched in `db/column_family.cc:607` |
| merge policy for non-integer `s_i` ("active run" until full, then static) (§3.2, p.6) | `db/compaction/compaction_picker_moose.cc` — `MooseCompactionBuilder::PickFileToCompact():256`, `PickFilesForLevel():306`, `PickFilesForL0():329`; `VersionStorageInfo::EnableDynamicRun()` at `db/version_set.cc:3400` decides "compact into an existing run" vs "only into an empty physical level" |
| compaction triggering over logical levels | `db/version_set.cc:3412` `ComputeCompactionScoreForMoose` (score = logical-level bytes / logical capacity, or run-count/`n_i` when dynamic runs are off) |
| trivial-move rule for Moose | `db/compaction/compaction.cc:477-482` |
| Monkey per-level BPK allocation (§3.3, Eq. 10) | `db/monkey_filter.cc:5` `MonkeyBpks()`; policy in `table/block_based/filter_policy.cc:1831-1850` (`MonkeyBloomFilterPolicy`, `NewMonkeyFilterPolicy`), declared `include/rocksdb/filter_policy.h:211`, wired for Moose at `table/block_based/filter_policy.cc:1758` |
| **DP for `{N_i}` given `N_L`** (§3.4, Eq. 12) | **only** in the web calculator: `front-end/moose/src/components/Tree/algm.ts` (`dp()` at :13, `dpInner()` at :102, cost `calCost()` at :98) |
| **Smoose: workload-aware search over `N_L` and `k`** (§3.6, Eq. 17) | **not present anywhere in the repo** (see below) |
| experiment driver | `tools/rw_test.cc` (+ `tools/rw_test.sh`), built by `tools/CMakeLists.txt:19` |
| db_bench integration | `tools/db_bench_tool.cc:4156-4170` (parses `-level_capacities` / `-run_numbers`); example invocations in `moose_bench.sh` |
| HTTP KV server demo | `tools/kv_server.cc` — **commented out** of the build at `tools/CMakeLists.txt:29-31` (needs Drogon) |

### Gaps found by reading

1. **Smoose is not implemented in the artifact.** `algm.ts` only performs the inner DP that minimizes
   `A`. Its objective, `calCost(ri, ni) = ni + 16/internalDiv + (ri-1)/internalDiv/ni`
   (`algm.ts:99`), has **no** `s,u,z` workload weights, **no** point-lookup / FPR term, and hard-codes
   the run count as `ni = round(√ri)` (`algm.ts:126,133`), i.e. `k = 1`. There is no enumeration of
   `N_L ∈ [0.5N, N]` and no enumeration of `k`. The `N_L` in `dp()` is a caller-supplied argument.
   So the §3.6 "tractable structure adaptation" that produces Table 3 and the Smoose rows of
   Fig. 8 / Table 5 must be re-implemented.
2. **No experiment harness for the paper's figures.** The only runnable scripts are
   `tools/rw_test.sh` (one hard-coded Moose config `run_numbers=1,4,5,4`,
   `level_capacities=2097152,39845888,1075838976,21516779520`, vs stock RocksDB) and `moose_bench.sh`
   (mostly commented-out `db_bench` lines). `BalancedWorkload` in `tools/rw_test.cc:90-152` is a
   **fixed 25/25/25/25** mix of non-empty get / empty get / put / 16-entry scan — the operation
   proportions of workloads A–J are not configurable. No Leveling/Tiering/LazyLeveling/QLSM-Bush/
   Dostoevsky config vectors, no plotting scripts, no result data.
3. **Two inconsistent option conventions.** `tools/rw_test.cc:183-192` expands logical capacities into
   per-run *physical* capacities and sets `num_levels = Σ run_numbers`, whereas
   `tools/db_bench_tool.cc:4168-4169` assigns the flag vector to `options.level_capacities`
   unchanged and never sets `num_levels`. `moose_bench.sh:6` passes 14 capacities (= Σ of its
   `run_numbers`) together with `-num_levels=64`. db_bench's Moose path also never installs the
   Monkey filter policy, so a db_bench-based reproduction would not match the paper's filter setup.
4. **Brittleness.** `db/monkey_filter.cc:26-28` calls `exit(0)` (not an error return) when a computed
   per-level FPR falls outside `[0,1]` — a mis-specified capacity vector silently terminates the
   benchmark.
5. **`README.md:35` says `make install`** — the default `CMAKE_INSTALL_PREFIX` is `/usr/local`, which
   needs root on this machine. Build the targets directly or set `-DCMAKE_INSTALL_PREFIX=$HOME/local`.

### Build route on this machine

`cmake_minimum_required(VERSION 3.10)` (`CMakeLists.txt:35`), C++17 (`CMakeLists.txt:84-85`).
System `cmake 3.25.1` + `gcc 12.2.0` + `make 4.3` are sufficient; RocksDB 8.9 (Dec-2023) compiles
cleanly with gcc 12. `WITH_TOOLS` defaults ON (`CMakeLists.txt:1149`) and `WITH_GFLAGS` defaults ON
for non-MSVC (`CMakeLists.txt:114`), so `tools/rw_test` is built by default; **gflags** is the only
non-stock dependency (`README.md:25-28`) and is a one-line conda install. Snappy/Zlib/BZip2 (needed
only for Fig. 9 B/C) are likewise conda packages. The `Dockerfile`s in the tree are inherited RocksDB
CI files and are not on the build path. `Vagrantfile`/`.circleci/config.yml` `sudo` hits in
`repo_facts.json` are inherited RocksDB CI, not part of the artifact's build or evaluation.

### Data

Fully synthetic — no external datasets, traces or model weights. `KeyGenerator`
(`tools/rw_test.cc:30-68`) materialises the integer key range `[0, prepare_entries)`, shuffles it,
and zero-pads keys/values to the requested sizes; `db_bench` generates its own. Default
`--prepare_entries=10000000`, `--kvsize=1024` → ~10 GB, close to the paper's 11 GB. Note the key
generator holds all keys in a `std::vector<uint64_t>` (80 MB at 10 M keys — fine here).

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | `github.com/NTU-Siqiang-Group/MooseLSM` is under the corresponding author's lab org; `README.md:9,12-21` links the paper PDF and gives this article's BibTeX. It contains the real system, not a stub: `db/compaction/compaction_picker_moose.cc` (360 lines), `db/version_set.cc:3400-3462`, `db/monkey_filter.cc`, `table/block_based/filter_policy.cc:1831-1850`, `tools/rw_test.cc`. Caveat (not a fail): Smoose's §3.6 search is absent and the DP exists only as TypeScript in `front-end/moose/src/components/Tree/algm.ts`. |
| `H2_no_root` | **pass** | Pure user-space RocksDB fork. Build is `cmake` + `make` (`README.md:30-36`); no kernel module, eBPF, perf counter, KVM or `/proc/sys` use anywhere on the Moose path. `tools/rw_test.cc:234-235` enables `use_direct_reads` / `use_direct_io_for_flush_and_compaction`, which is plain `O_DIRECT` — no privileges. The `sudo`/`sysctl`/`hugepage` grep hits in `repo_facts.json` are inherited RocksDB CI config (`.circleci/config.yml`) and doc comments (`include/rocksdb/advanced_options.h:489` documents an *optional* hugepage memtable). Dockerfiles are inherited RocksDB CI and unnecessary — deps are gflags (+ optional snappy/zlib/bzip2) from conda. Only fix needed: avoid `make install` into `/usr/local` (`README.md:35`). |
| `H3_hardware_fit` | **pass** | Single node, CPU-only, no GPU. Paper's machine (6 cores, 32 GB RAM, 512 GB SATA SSD, §4 p.17) is *smaller* than ours in every dimension except that our 125 GB RAM can cache the whole 11 GB DB. Dataset ~11 GB, and the largest config in `tools/rw_test.sh:10` totals ~22.6 GB; with the `_backup` copy (`rw_test.sh:16`) that is < 50 GB against ~257 GB free. Cache-size divergence is controllable: `tools/rw_test.cc:234-235` already uses direct I/O for the measurement phase, and cgroup-v2 `memory` is delegated to the user slice (env.md) if a 32 GB cap is wanted. |
| `H4_obtainable_deps_data` | **pass** | Deps: gflags, cmake, gcc/g++ (`README.md:25-28`) — all present or conda-installable in user space; base is RocksDB 8.9.0 with vendored third-party (`third-party/`). No datasets required: all keys/values are synthesized in-process (`tools/rw_test.cc:30-68`, `PrepareDB():70`), and `db_bench` self-generates. No proprietary traces anywhere. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Primary target.** Table 5 (p.19) + Fig. 8 ranking (p.18), restricted to the four
non-workload-aware baselines plus Moose, on workload **J** (33 % range / 33 % update / 33 % point)
and workload **F** (49/49/2). The claim under test: *Moose's per-level `{r_i},{n_i}` beats Leveling,
Tiering, LazyLeveling and QLSM-Bush on three-way mixed workloads while keeping compacted bytes and
compaction counts moderate* — Table 5 row J gives Leveling 2.94 IO/22 GB/203 compactions vs Moose
3.06/9/221, and Table 4 gives Moose average rank 3.2 vs 5.2/6.3/5.8/7.3.

**Week-1 smoke target** (much cheaper, directly supported by a committed script): Fig. 9(A)
row-store points — Moose vs stock RocksDB under the fixed balanced workload, using
`tools/rw_test.sh` as shipped with `--kvsize` varied.

**Scale-down.** Paper scale is affordable, but shrink for turnaround:
- Keep 24 B keys / 1000 B values, drop the dataset from 11 GB to **4 GB** (≈4 M entries) and the
  operation count from 2 M to **500 k** per workload; keep the 2 MB buffer and 5 bits/key so the
  number of levels (4–5) and the structural story are preserved.
- Run everything with direct I/O (already the default for the test phase,
  `tools/rw_test.cc:234-235`) and additionally under a cgroup-v2 `memory.max` of ~8 GB so that the
  125 GB of RAM does not turn the experiment into an in-memory benchmark. This is the single most
  important deviation from the paper's 32 GB machine.
- DB on `/home` (not `/tmp`, which `tools/rw_test.sh:4-5` hard-codes) via `--path`.

**Steps.**
1. `conda create` env with `gflags` (+ `snappy zlib bzip2` if Fig. 9 B/C is wanted); build with
   `cmake -DCMAKE_BUILD_TYPE=Release -DWITH_GFLAGS=ON ..` and `make -j16 rw_test db_bench`
   (no `make install`). ~0.5 person-day.
2. Run `tools/rw_test.sh` unchanged (both branches — the shipped file has `test_moose` commented
   out at `rw_test.sh:37-38`) to get the Moose-vs-RocksDB smoke number. ~0.5 person-day + ~4 h wall.
3. Generalize `BalancedWorkload` (`tools/rw_test.cc:90`) into a driver with `--range_pct
   --update_pct --point_pct --scan_length --empty_query_pct` flags and per-operation latency
   histograms. ~1 person-day, ~150 LOC.
4. Derive the baselines as `level_capacities`/`run_numbers` vectors from §4 p.18 (Leveling T=10 →
   `n_i=1`; Tiering T=10 → `n_i=10`; LazyLeveling → `n_i=10` for non-last, `1` for last;
   QLSM-Bush T=2,X=2 per Dayan & Idreos '19). Sanity-check each against the level stats printed by
   `rw_test.cc:250-253` (`rocksdb.stats`). This is the main correctness risk. ~1.5 person-days.
5. Port `algm.ts`'s DP to Python/C++ and wrap it in the §3.6 `N_L`×`k` search with the Eq. 17
   objective to obtain Moose (`N_L=0.8N`, `k=1`) and Smoose configs. ~1.5 person-days.
6. Run workloads J and F for 5 configurations, extract IO/compaction counters from
   `options.statistics` (`rw_test.cc:239,253`). ~4 h wall each at the scale-down.

**Effort.** ≈ **6 person-days + ~30 CPU-hours** (no GPU) for the primary target; ≈ 1 person-day +
4 CPU-hours for the smoke target.

**Level: M.** The system and its options plumbing are complete and the build is trivial on this
machine, but the evaluation harness for the paper's figures does not exist: workload mixes are
hard-coded, baseline configuration vectors must be re-derived from prose, and Smoose's search must
be re-implemented from §3.6 because only the inner DP was released (and only in TypeScript). That is
exactly "reproducible with real porting work". It is not **H** for those reasons and not **L**
because every missing piece is small and fully specified in the paper.

## 5. Add-on ideas

### A1 — Skew- and hit-aware Smoose

**Hypothesis.** We hypothesize that replacing Smoose's all-empty, uniform point-lookup cost term
with a hit-probability- and skew-aware term improves end-to-end throughput by ≥10 % under
Zipfian/YCSB-style workloads with a non-trivial fraction of successful point lookups, compared with
the structure Smoose selects today.

**Mechanism.** (i) Re-implement §3.6's search in C++ (it is missing). (ii) Change the objective from
`Z = k·Σ p_i √r_i` (Eq. 11/§3.6) to `Σ_i [ P(key resides at level ≥ i) · (n_i p_i + hit_i) ]`,
where the per-level residency distribution is estimated from a sampled query log and the recency
distribution of the data (under skew, hot keys live in the *small* levels, which inverts the
"make `N_L` large" insight of §3.3). (iii) Re-derive the Bloom allocation in `MonkeyBpks` from the
same distribution instead of from level capacity alone. (iv) Evaluate under Zipfian θ=0.8/0.99 and
uniform.

**Code locations.** `front-end/moose/src/components/Tree/algm.ts`, `db/monkey_filter.cc`,
`include/rocksdb/monkey_filter.h`, `tools/rw_test.cc`.

**Motivating evidence.** The paper states the gap itself: "the cost of non-zero result point lookup
is not specialized in the model since its probabilistic is uncertain for Smoose" (§3.6, p.16). Every
experiment uses uniformly random keys — `KeyGenerator` (`tools/rw_test.cc:30-68`) shuffles the full
key range uniformly, and `BalancedWorkload` (`:90-152`) issues exactly 25 % hits and 25 % misses.
`MonkeyBpks` (`db/monkey_filter.cc:19-30`) allocates bits purely from level capacities, so with the
default `N_L = 0.8N` the level holding 80 % of the data gets the *fewest* bits per key — a choice
that is right for all-empty lookups and likely wrong when hot keys concentrate.

**Feasibility: M.** The cost model and search are a few hundred lines in user space, and the
workload generator needs a Zipfian key chooser (~50 LOC). But it is two pieces of new code plus a
new harness, and the evaluation must sweep skew × mix, so it is more than a localized patch.

**Research value: H.** It attacks an explicitly stated blind spot of the paper's own cost model, in
the regime (skewed, read-mostly) that dominates real KV workloads. A negative result — "Moose's
`N_L = 0.8N` rule survives skew" — is also publishable evidence about the robustness of the
optimality claim.

**Scoop check.** Queries: *"MooseLSM Structural Designs Meet Optimality citing follow-up"*,
*"LSM-tree level-wise size ratio run number workload-aware tuning skewed Zipfian cost model"*.
Result: **partial**. [CAMAL (SIGMOD'25, same NTU group)](https://arxiv.org/abs/2409.15130) tunes the
LSM design space with active learning but over the conventional (T, policy, BPK) space and does not
use Moose. [Zhu et al., "Dynamic Workload-Aware BF Tuning via Accurate Statistics"
(PACMMOD'25)](https://cs-people.bu.edu/mathan/publications/pacmmod25-zhu.pdf) does workload-aware
*Bloom filter* tuning under skew, which overlaps with part (iii) but not with the structural search
over `{N_i}`/`{n_i}`. Nobody found combining skew-aware point-lookup costs with Moose's generalized
structure.

### A2 — Tail latency of whole-level compaction; key-range-partitioned Moose

**Hypothesis.** We hypothesize that Moose's whole-logical-level compaction inflates p99/p999 write
and read latency and write-stall time relative to stock RocksDB leveling, even where it wins on mean
throughput, and that key-range-partitioned partial compaction inside the Moose picker recovers most
of the tail while retaining ≥90 % of Moose's mean-throughput advantage under three-way mixed
workloads.

**Mechanism.** `MooseCompactionBuilder::PickFilesForLevel` (`db/compaction/compaction_picker_moose.cc:306-327`)
pushes **every** non-being-compacted file of **all** runs of a logical level into one compaction, and
the resulting `Compaction` is constructed with `max_subcompactions = 0`
(`compaction_picker_moose.cc:227`), so a single background thread rewrites the whole level on our
16-core box. The add-on: (i) split each level compaction at key-range boundaries into `p` jobs whose
inputs are the overlapping files of that range across the level's runs, sized by
`max_compaction_bytes`; (ii) let `max_subcompactions` follow the mutable option instead of 0;
(iii) keep `ComputeCompactionScoreForMoose` (`db/version_set.cc:3412-3462`) as the trigger but score
per partition. Measure p50/p99/p999 and cumulative stall time, not just throughput.

**Code locations.** `db/compaction/compaction_picker_moose.cc:306`, `db/compaction/compaction_picker_moose.cc:227`,
`db/version_set.cc:3412`, `db/compaction/compaction.cc:477`, `tools/rw_test.cc`.

**Motivating evidence.** The paper reports only throughput and I/O counts (Fig. 7, Fig. 8, Table 5);
no latency distribution appears anywhere. Table 5 shows Moose performing *more* compactions than
Leveling in every workload (e.g. J: 221 vs 203; B: 656 vs 561) while moving fewer bytes — i.e. many
large level-wide merges. `rw_test.cc:237-238` lowers `level0_slowdown_writes_trigger` to 4 and
`level0_stop_writes_trigger` to 8, which makes stalls more likely, yet stalls are never reported.
This is also the classic failure mode of tiering-like policies, which Moose's `n_i>1` levels are.

**Feasibility: M.** Partitioning a compaction is a well-understood change confined to the picker
(~500–1000 LOC including tests), and RocksDB already provides `GetRange`/`ExpandInputsToCleanCut`
machinery. Correctness risk is real (overlapping ranges across runs in the same logical level) and
the evaluation needs a latency-histogram harness, so not H.

**Research value: H.** A SIGMOD reviewer would care: the paper's optimality argument is about
expected I/O count, and a demonstration that the optimal-I/O structure is tail-pathological — or
that it is not — directly qualifies the headline claim. Either outcome is informative.

**Scoop check.** Query: *"LSM-tree compaction write stall tail latency p99 partial compaction
key-range partitioned"*. Result: **partial**. Tail latency of full vs partial compaction is mapped
generically in [Sarkar et al., "Constructing and Analyzing the LSM Compaction Design Space"
(VLDB'21)](https://vldb.org/pvldb/vol14/p2216-sarkar.pdf) and attacked in
[vLSM (2024)](https://arxiv.org/pdf/2407.15581) and
[Vertiorizon (SIGMOD'25)](https://arxiv.org/abs/2504.17178) (which uses partial compaction in its
vertical part). None of these operate in, or measure, Moose's per-level `{r_i},{n_i}` space; the
Moose artifact itself has no partial compaction at all.

### A3 — Scan-length-aware choice of `k`

**Hypothesis.** We hypothesize that the optimal run-count regulator `k` decreases monotonically with
range-query selectivity, so that Moose's fixed `n_i = k·√r_i` with `k = 1` loses ≥15 % throughput to
a scan-length-aware `k` on workloads whose scans return ≫ B entries, while matching it for short
scans.

**Mechanism.** Eq. 3 (§3.2) drops the retrieval term `t/B` by assuming `t = O(Σ n_i · B)`, i.e. that
every run contributes at least one block; §3.5 (p.14–15) argues the Pareto curve survives for an
*average* `t̄` but does not re-derive `k`. Add the `t̄/B` term explicitly to the Smoose objective
(Eq. 17) so that `S = k·Σ√r_i + t̄/B`, make `t̄` a measured quantity, and re-run the `k` enumeration.
Then validate by sweeping the scan length in the workload driver over {1, 16, 256, 4096} entries and
comparing predicted-optimal `k` with measured-optimal `k`.

**Code locations.** `front-end/moose/src/components/Tree/algm.ts:98`, `tools/rw_test.cc:131-145`,
`tools/rw_test.sh`.

**Motivating evidence.** The released DP objective hard-codes the scan length: `calCost(ri, ni) =
ni + 16/internalDiv + (ri-1)/internalDiv/ni` (`algm.ts:99`), where `internalDiv = blockSize/kvSize`
(`algm.ts:15`) and the literal `16` is exactly the scan length used by the benchmark
(`tools/rw_test.cc:140`: `for (int i = 0; i < 16 && it->Valid(); i++)`). So every published Moose
configuration is tuned for one selectivity, and Fig. 10(A) (p.21) already shows lookup and update
latency moving in opposite directions as `k` varies — the crossover point is what this add-on
predicts should shift.

**Feasibility: H.** No engine change at all: only the configuration generator and the workload
driver's scan loop move, and the existing `rw_test` harness measures it. Well inside 10 weeks for
2–4 students, and the compute is a handful of CPU-hours per point at the scale-down.

**Research value: M.** It converts an unexamined constant in the released artifact into a tunable and
tests a stated simplifying assumption (§3.5), which is a solid contribution — but the *direction* of
the result (longer scans favour fewer runs) is what the cost model already suggests, so a reviewer
would find it expected rather than surprising.

**Scoop check.** Queries: *"Moose LSM-tree level capacities follow-up scan length range query cost
model"*, *"LSM-tree range query selectivity size ratio tuning"*. Result: **clear** for Moose
specifically — range-query-aware LSM tuning exists (Dostoevsky, Endure), but no work was found that
re-derives Moose's `n_i = k√r_i` rule as a function of scan selectivity, and the hard-coded `16` in
`algm.ts` is untouched in the repo's history.

### A4 — Does the I/O-count cost model still rank correctly on NVMe?

**Hypothesis.** We hypothesize that on a modern NVMe SSD with 16 cores, Moose's I/O-count-minimizing
objective (Eq. 17) mispredicts the throughput ranking of structures — because compaction CPU and
merge-iterator work, not I/O count, become the bottleneck — and that adding a per-entry CPU term to
the objective restores agreement with measured latency (Fig. 10(D)) and changes the selected `N_L`
and `k`.

**Mechanism.** Extend the Smoose objective to `L = s·S + u·U + z·Z + γ·(merged entries per update)`,
where `γ` is a device/CPU calibration constant fitted once from a micro-benchmark on the target
machine; re-run the `N_L`×`k` search; compare predicted vs measured latency exactly as Fig. 10(D)
does, on both a cold (direct-I/O, cgroup-capped) and a warm configuration. Instrument
`rw_test.cc`'s statistics dump to separate compaction CPU time from I/O time.

**Code locations.** `front-end/moose/src/components/Tree/algm.ts:98`, `tools/rw_test.cc:154-218`,
`db/version_set.cc:3412`, `moose_bench.sh`.

**Motivating evidence.** §4 (p.17) evaluates on a **SATA SSD** with 6 cores; the entire cost analysis
(§3.2, Eq. 2–4) counts I/Os only, and Fig. 10(D) claims the model tracks measured latency on that
device. Our machine's NVMe RAID has roughly an order of magnitude more IOPS and 16 cores, shifting
the bottleneck. The artifact makes the CPU pressure worse by construction: Moose compactions are
single-threaded (`compaction_picker_moose.cc:227`, `max_subcompactions = 0`) and always level-wide
(`compaction_picker_moose.cc:306-327`). §3.5 explicitly flags that the worst-case analysis
"necessitates the evaluation in real KV-stores".

**Feasibility: H.** Reuses the reproduction harness end-to-end; the only new code is the extra cost
term and a timing breakdown. Cheap in compute (CPU-only, ~20 h) and a natural extension of the
reproduction, which also makes it a safe fallback deliverable ("Contemporary paper" track).

**Research value: M.** Device-sensitivity of analytical LSM cost models is a known concern, so the
question is not novel in the abstract; its value here is that it puts a number on how far Moose's
*specific* optimality claim travels to current hardware. Useful, moderately surprising at best.

**Scoop check.** Queries: *"LSM-tree cost model NVMe CPU bound compaction throughput"*,
*"MooseLSM reproduction NVMe"*. Result: **clear** — no re-evaluation of Moose on NVMe was found; the
closest work is [Keigo (2025)](https://arxiv.org/pdf/2506.14630), which co-designs LSM stores with a
concurrency-aware storage hierarchy but does not evaluate Moose or its cost model.

### A5 — Online restructuring when the workload drifts *(scooped — do not count)*

**Hypothesis.** We hypothesize that migrating a live Moose tree to a newly searched Smoose
configuration with lazy/preemptive compaction beats keeping the stale configuration under workload
drift.

**Mechanism.** Make `level_capacities`/`run_numbers` mutable at runtime and add a migration
controller that re-runs the search and re-shapes levels incrementally.

**Code locations.** `options/cf_options.h`, `db/version_set.cc:3400`,
`db/compaction/compaction_picker_moose.cc:256`.

**Motivating evidence.** §3.6 (p.17) says Smoose is "initially designed for static workload tuning"
and that substantial workload change "require[s] structural transformation", suggesting a lazy
strategy and preemptive compaction as future work. `options.level_capacities` is fixed at `DB::Open`
(`tools/rw_test.cc:165-192`).

**Feasibility: M. Research value: H** — but it does not count.

**Scoop check. Result: scooped.**
[ArceKV, "Towards Workload-driven LSM-compactions for Key-Value Store Under Dynamic Workloads"
(arXiv:2508.03565, PVLDB submission)](https://arxiv.org/html/2508.03565v1) explicitly targets this
gap, stating that Moose "does not offer a robust solution for adapting structural configurations
across varying workloads" and that Moose's configurations differ so much between workloads that
transitions are impractical; ArceKV's ElasticLSM allows compactions among any runs at any time and
adapts within 20 M operations. [Vertiorizon / "How to Grow an LSM-tree?" (SIGMOD'25, Mo, Luo,
Idreos)](https://arxiv.org/abs/2504.17178) additionally covers the growing-`N` half of the problem.

## 6. Risks and open questions

1. **Smoose must be rebuilt from the paper.** The §3.6 search (Eq. 17, the `N_L`/`k` enumeration) is
   nowhere in the repo; only the inner DP exists, in TypeScript, with a fixed objective
   (`front-end/moose/src/components/Tree/algm.ts:98-140`). Any claim about Smoose's numbers
   (Table 3, the SMSE column of Fig. 8/Table 5) rests on a reimplementation, which is a real threat
   to "we reproduced the paper".
2. **Baseline configurations are prose, not code.** Leveling/Tiering/LazyLeveling/QLSM-Bush/
   Dostoevsky/tuned-RocksDB all have to be encoded as `level_capacities`/`run_numbers` vectors from
   §4 p.18. A wrong vector silently produces a different structure; `db/monkey_filter.cc:26-28`
   even `exit(0)`s on an inconsistent one. Budget time for validating each baseline against
   `rocksdb.stats` level output.
3. **Memory divergence.** 125 GB of RAM vs the paper's 32 GB, against an 11 GB dataset, can turn the
   whole benchmark into a page-cache test. `tools/rw_test.cc:234-235` uses direct I/O in the test
   phase, which helps, but the prepare phase and any `db_bench`-based run do not. Plan a cgroup-v2
   `memory.max` cap.
4. **Device divergence.** SATA SSD → NVMe RAID changes the I/O/CPU balance; the paper's ranking may
   not survive, which is simultaneously risk (reproduction "fails") and opportunity (add-on A4).
   Also, the NVMe is a *software RAID on a shared machine* — other users' I/O will add noise;
   repeat runs and report variance.
5. **db_bench vs rw_test inconsistency.** `tools/db_bench_tool.cc:4156-4170` treats
   `-level_capacities` differently from `tools/rw_test.cc:183-192`, never sets `num_levels`, and
   never installs the Monkey filter policy. Using `moose_bench.sh` as-is would not reproduce the
   paper's setup. Prefer `rw_test`.
6. **Unclear what Fig. 9(A)'s "column store" means in code.** No column-layout code path was found in
   the repo (`rw_test.cc` writes flat padded values only); reproducing Fig. 9(A)'s "C" points may be
   impossible without asking the authors. Restrict the target to the "R" points.
7. **No artifact badge, no tests, low activity.** No ACM artifact-evaluation statement in the paper,
   no reproduction scripts, no Moose-specific unit tests found, 6 stars, single substantive commit
   window ending 2024-06-11. Nobody else has demonstrably rebuilt this.
8. **License.** `LICENSE` is an "NTUITIVE PTE LTD Dual License" (GitHub reports NOASSERTION), not the
   usual RocksDB Apache-2/GPLv2. Check the terms before publishing derived code.
9. **Two of the most natural research directions are taken.** Dynamic/structural adaptation is
   ArceKV's stated contribution, and LSM growth is Vertiorizon's. Proposals in that area need a
   sharper differentiator than "make Moose adaptive".

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; page images where noted)
- §1 Introduction, Table 1 (p.2) — configuration-space comparison, Problems 1 & 2.
- §2 Background (p.4–5) — leveling/tiering, BPK/FPR definitions.
- §3.1 LSM-tree generalization, Eq. 1, Fig. 1 (p.5–6) — `n_i`, `s_i`, `r_i = s_i·n_i`.
- §3.2 Eq. 2, 3, 4 (p.6–7) — update / range / point cost models; Table 2 notation (p.7).
- §3.3 Eq. 9–11 (p.9–10) — Monkey-generalized BPK rule; "larger `N_L` helps point lookup".
- §3.4 Eq. 12, Fig. 2 (p.11) — DP over `S(N_d, N_r)`.
- §3.5 (p.14–15) — "Assumptions and Relaxations"; Eq. 15–16 space amplification ≤ 3.54; Fig. 6.
- §3.6 (p.16–17) — Eq. 17 objective; `N_L` and `k` enumeration; static-tuning limitation; Table 3.
- §4 (p.17, `pages/page-17.png`) — machine spec, implementation, baselines, 11 GB / 2 M ops; Fig. 7.
- Fig. 8 + Table 4 (p.18, `pages/page-18.png`) — workload A–J composition and rankings.
- Fig. 9 + Table 5 (p.19, `pages/page-19.png`) — layouts/compression/space amplification; IO,
  compacted bytes, compaction counts.
- Fig. 10 + Discussions 1–6 (p.21, `pages/page-21.png`) — `k` sweep, `N_L = 0.8N` justification,
  growing `N`, cost-model accuracy.
- §5 Related work (p.22–23), §6 Conclusion (p.23).

**Repository** (paths relative to `repo/`)
- `README.md` (:9 paper link, :12-21 BibTeX, :25-36 build, :57-58 license)
- `include/rocksdb/version.h:14-16` (RocksDB 8.9.0)
- `include/rocksdb/advanced_options.h:37` (`kCompactionStyleMoose`)
- `include/rocksdb/options.h`, `options/cf_options.h`, `options/cf_options.cc`,
  `options/options_helper.cc:336,808` (`level_capacities`, `run_numbers`)
- `db/compaction/compaction_picker_moose.cc` (:187 `ComputeLogicalLevel`, :201 `PickCompaction`,
  :227 `max_subcompactions=0`, :236 `SetupInitialFiles`, :256 `PickFileToCompact`, :306
  `PickFilesForLevel`, :329 `PickFilesForL0`)
- `db/compaction/compaction_picker_moose.h`
- `db/version_set.cc:3400` (`EnableDynamicRun`), `:3412` (`ComputeCompactionScoreForMoose`),
  `:3477-3481` (dispatch); `db/version_set.h:615`
- `db/compaction/compaction.cc:477-482` (Moose trivial move)
- `db/monkey_filter.cc:5-32` (`MonkeyBpks`, `exit(0)` at :26-28); `include/rocksdb/monkey_filter.h`
- `table/block_based/filter_policy.cc:1758` (Moose case), `:1831-1850` (`MonkeyBloomFilterPolicy`,
  `NewMonkeyFilterPolicy`); `include/rocksdb/filter_policy.h:211`
- `db/column_family.cc:607` (Moose picker instantiation)
- `tools/rw_test.cc` (:30-68 `KeyGenerator`, :70 `PrepareDB`, :90-152 `BalancedWorkload`,
  :140 scan length 16, :154 `get_default_options`, :165-218 `get_moose_options`, :234-235 direct I/O,
  :237-238 stall triggers, :239/:250-253 statistics)
- `tools/rw_test.sh` (:2 exe path, :4-5 `/tmp` paths, :9-10 hard-coded Moose config, :37-40 which
  branch actually runs)
- `tools/db_bench_tool.cc:4156-4170` (Moose flag handling)
- `tools/kv_server.cc`, `tools/CMakeLists.txt` (:19 `rw_test` built, :29-31 `kv_server` commented out)
- `moose_bench.sh` (:4-12 commented db_bench invocations, :23-27 the live one)
- `front-end/moose/src/components/Tree/algm.ts` (:13 `dp`, :15 `internalDiv`, :98-100 `calCost`,
  :102-141 `dpInner`, :126/:133 `ni = round(√r)`); `front-end/readme.md` ("TODO")
- `CMakeLists.txt` (:35 cmake ≥3.10, :84-85 C++17, :114 `WITH_GFLAGS` ON, :1149 `WITH_TOOLS` ON)
- `repo_facts.json` (HEAD `ede0e34` 2024-06-11, 2058 files, red-flag greps), `fetch_result.json`
  (PDF provenance: authors' corrected copy at `siqiangluo.com/docs/moose_corrected_version.pdf`)

**External (scoop check)**
- [CAMAL: Optimizing LSM-trees via Active Learning (SIGMOD'25)](https://arxiv.org/abs/2409.15130)
- [How to Grow an LSM-tree? / Vertiorizon (SIGMOD'25)](https://arxiv.org/abs/2504.17178)
- [ArceKV (arXiv:2508.03565)](https://arxiv.org/html/2508.03565v1)
- [Dynamic Workload-Aware BF Tuning (PACMMOD'25)](https://cs-people.bu.edu/mathan/publications/pacmmod25-zhu.pdf)
- [Constructing and Analyzing the LSM Compaction Design Space (VLDB'21)](https://vldb.org/pvldb/vol14/p2216-sarkar.pdf)
- [vLSM (arXiv:2407.15581)](https://arxiv.org/pdf/2407.15581)
- [Keigo (arXiv:2506.14630)](https://arxiv.org/pdf/2506.14630)
