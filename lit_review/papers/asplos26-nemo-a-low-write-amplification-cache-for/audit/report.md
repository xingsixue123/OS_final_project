# Nemo: A Low-Write-Amplification Cache for Tiny Objects on Log-Structured Flash Devices

ASPLOS '26 (Yang et al., Xiamen University / Tsinghua / CQUPT).
Repo: https://github.com/XMU-DISCLab/Cachelib-Nemo (branch `nemo`, head `66db041`, 2026-01-21).
Desk review only — nothing was built or run.

## 1. Paper summary

**Problem.** Flash key–value caches for *tiny* objects (~250 B) must jointly optimize three
things: miss ratio, DRAM overhead for metadata, and write amplification (WA). ZNS/FDP SSDs
kill device-level WA (DLWA), so *application*-level WA (ALWA) dominates (§1, §2.2). The
SOTA hierarchical design FairyWREN (OSDI'24) buffers objects in a small log (HLog, 5 % of
flash) and migrates them into a large set-associative tier (HSet, 95 %). The authors
reproduced FairyWREN's artifact, found and fixed "two major implementation bugs in the
HLog-to-HSet migration logic" that had under-reported HSet writes, and measured ALWA > 15×
on Twitter traces (§3, p. 4).

**Analysis (§3).** They model ALWA as `1/E(FR_i) + L2SWA` (Eq. 1). The log-to-set term
decomposes into passive migration (Case 2) and active migration folded into GC (Case 3),
giving `L2SWA = (2-p)·N'_Set/(2·N_Log)` (Eq. 8). Measured: L2SWA(P) = 8.5 vs theory ≈ 9;
overall L2SWA = 14.2 with p ≈ 25 %; only ~2.04 new objects land in a 4 KB set per set-write
(Fig. 4, 5), i.e. a **set fill rate of ~7 %**. The root cause is the *large* hash range of
HSet: hash collisions before migration are rare, so batching is ineffective (Observations
1–4). Growing HLog to 20 % (+73 % memory) or OP to 50 % (half the capacity wasted) only
gets WA to 4.12 / 6.56 (Fig. 12b).

**Key idea (§4).** Invert the design: use a *small* hash space so collisions are frequent.
A **Set-Group (SG)** is a large logical unit (sized to one ZNS zone, 1077 MB = 275,712
4 KB sets) that is filled in DRAM and flushed to flash **whole**, sequentially; the on-flash
SG pool is FIFO and eviction is SG-granular. WA then equals `1/E(FR_SG)` (Eq. 9).
Three mechanisms defeat the short-term hash skew that would otherwise make a freshly
opened SG flush at ~7 % fill (Fig. 8, 9):
1. **Buffered in-memory SGs** (a circular queue; default 2) — delay the front SG's flush.
2. **Probabilistic / count-based flushing** — instead of flushing when a set overflows,
   sacrifice (evict) a few objects; only after a threshold (Table 3: 4,096) is a real
   flush forced.
3. **Hotness-aware writeback** — on SG eviction, hot objects from the victim SG are
   re-inserted into the SG about to be flushed, which also tops up its fill rate.
Fill rate goes 6.78 % → 31.32 % (B) → 36.77 % (P) → 64.13 % (B+P) → **89.34 %** (B+P+W)
(Fig. 17).

**Index (§4.3).** No exact object→SG map (that would cost >40 bits/obj). Instead a
**Parallel Bloom Filter Group (PBFG)**: one BF per *set* per SG; all set-level BFs with
the same intra-SG offset across SGs form one PBFG that is queried in parallel to get
candidate SGs. PBFGs are packed so one PBFG fits in one 4 KB flash page (Fig. 10), stored
in an on-flash index pool, with 50 % cached in DRAM (index cache, FIFO).

**Hotness (§4.4).** 1 bit per object (bitmap) *only for objects in the last 30 % of the
cache*, ANDed with "is this set's PBFG currently in the index cache" (recency), with
periodic cooling (Fig. 11).

**Evaluation (§5).** 24-core Intel, 128 GB RAM, Ubuntu 22.04 / Linux 5.15, **WD Ultrastar
DC ZN540 ZNS SSD** (1,077 MB zones), libzbd. 360 GB flash cache; baselines Log, Set,
FairyWREN (bug-fixed), Kangaroo (+ZNS support added by the authors) — all as CacheLib
engines (Table 4). Workload: Twitter clusters 14/29/34/52 (Table 5), merged and amplified
across 4 disjoint key spaces, mean object size 246 B.
Headline numbers: **WA 1.56 (Nemo) vs 15.20 (FairyWREN), 16.31 (Set), 55.59 (Kangaroo),
1.08 (Log)** — Fig. 12a, p. 11; memory **8.3 bits/obj** vs 9.9 (FW) (Table 6); OP < 1 %;
p50/p99/p9999 read latency lower and far more stable than FW (Fig. 15); comparable miss
ratio (Fig. 16). Stated cost: read amplification is **>3× FairyWREN's** (§5.5).

**Stated limitations (§6).** (a) Index accuracy vs read amplification is a genuine
trade-off — a lower BF FP rate enlarges the index pool and costs *more* flash reads
(Appendix A models this; 0.01 % FP is worse than 0.1 %). (b) Scaling flash capacity raises
the SG count N and hence read amplification; the proposed fix (partition the device into
independent Nemo instances) is **suggested but never evaluated**. (c) **Free-riding** in
hybrid hotness tracking: cold objects survive eviction because their PBFG group is hot.

## 2. Artifact audit

### 2.1 Provenance and structure

Official beyond doubt: the paper's Artifact Appendix (p. 16, §A.3.1) names
`https://github.com/XMU-DISCLab/Cachelib-Nemo` and `https://doi.org/10.5281/zenodo.18332674`;
the Zenodo record is titled *"XMU-DISCLab/Cachelib-Nemo: Zenodo-nemo-asplos26-artifact"*
and archives **exactly the commit we cloned** (`XMU-DISCLab-Cachelib-Nemo-66db041.zip`).

The repo is a fork of Meta's CacheLib (~V17, 2022 vintage; `CHANGELOG.md`) with a new Navy
engine. Only two branches exist (`nemo`, `FairyWREN` — checked via the GitHub API); the
shallow clone here has only `nemo` (`repo/.git/packed-refs`).

```
repo/
  cachelib/navy/znskvcache/        <- Nemo itself (the only new engine)
  cachelib/navy/common/Device.cpp  <- ZNSDevice (libzbd)
  cachelib/allocator/nvmcache/NavySetup.cpp, NavyConfig.{h,cpp}
  cachelib/cachebench/             <- unmodified CacheBench + trace replay
  test.sh, clean_wa.py             <- the entire evaluation harness
  contrib/build*.sh                <- CacheLib's stock source-build scripts
```

### 2.2 Paper → code map

| paper component | code |
|---|---|
| Set-Group, SG flush, FIFO SG pool | `cachelib/navy/znskvcache/ZNSKVCache.cpp:182` (`flushRegion`), `:203` (`performFlush`), `:264` (`flush`), `ZonePool.{h,cpp}` |
| Set / bucket layout (4 KB) | `RegionBucket.{h,cpp}`, `RegionBucketStorage.{h,cpp}` |
| Buffered in-memory SGs (technique B) | `ZNSKVCache.cpp:479` (`getFreeDataRegionId`), `dataRegion[2]`, `isEnableDoubleBuffer` |
| Probabilistic/count flushing (technique P) | `ZNSKVCache.cpp:386-394` (`waitTimesBeforeFlush`, `maxWaitTimesBeforeFlush{1000}` in `ZNSKVCache.h:228`; `FLUSH_THRESHOLD 90` in `ZNSKVCache.h:25`) |
| Hotness-aware writeback (technique W) | `ZNSKVCache.cpp:846` (`writeBack`), `:897` (`reInsert`), `:909` (`evictZone`) |
| PBFG / set-level bloom filters | `PBFG.{h,cpp}`, `metaDataRegion` in `ZNSKVCache.cpp:109-118`, `calZoneId` at `:782`, `getPBFGFromDevice` at `:746` |
| Index cache (FIFO, 50 %) | `PBFGList.{h,cpp}` (`push`/`pop` = strict FIFO, `PBFGList.cpp:20-35`), sized at `ZNSKVCache.cpp:130` from `bucketRatio` |
| 1-bit hotness + cooling | `visitedMask` (`ZNSKVCache.cpp:134`, set at `:612-617`), `coldZone` `:678`, `coldAllStepZones` `:668` |
| Config knobs of Table 3 | `cachelib/cachebench/util/CacheConfig.h:144-178`, `cachelib/allocator/nvmcache/NavyConfig.h`, `NavySetup.cpp:103` (`setupZNSKVCache`) |
| Experiment config (Table 4) | `cachelib/cachebench/test_configs/ssd_perf/znskvcache/znscache_test.json` |

Some paper parameters are **hard-coded, not configurable**: `NUM_BUCKETS 275712`,
`METADATARATIO 50` (SGs : index groups = 50:1), `FLUSH_THRESHOLD 90`,
`maxWaitTimesBeforeFlush = 1000` (the paper's Table 3 says 4,096) — `ZNSKVCache.h:21-27`,
`:228`. Anyone sweeping these must recompile.

### 2.3 Build route on this machine

`contrib/build.sh` builds *everything* from source into `./opt/cachelib`
(`build-package.sh:290`): libzbd, zstd, gflags, glog, googletest, sparsemap, fmt, folly,
fizz, wangle, fbthrift, then cachelib. That part is user-space friendly. Problems:

* **Distro.** `build.sh:151-158` has no case for `debian12` and calls `die` — must be run
  with `-O` (skip OS packages), which then assumes the system already provides boost,
  libevent, double-conversion, libsodium, libunwind, libelf, libdwarf, binutils-dev,
  jemalloc, snappy, lz4, bz2, zlib, openssl (`contrib/prerequisites-debian10.sh`). With no
  root these must come from conda-forge and be found via `CMAKE_PREFIX_PATH`. Doable,
  unverified, and historically the hardest part of building CacheLib.
* **`sudo` in the build.** `build-package.sh:356-361` runs `sudo make install` for libzbd
  before re-configuring with `--prefix=$PREFIX`; that line must be deleted (the second
  `./configure --prefix=$PREFIX` shows it is redundant).
* **Toolchain age.** folly/fizz/wangle/fbthrift come from git submodules pinned at
  CacheLib-2022 commits (`.gitmodules`; submodules not fetched in this clone). Building a
  2022 folly with gcc 12.2 typically needs a handful of `#include <cstdint>`-class patches.
* **cmake.** `cachelib/CMakeLists.txt:20` is `cmake_minimum_required(VERSION 3.12)`; the
  system cmake 3.25 is fine, the pip cmake 4.x in `env.md` would **reject** it.

### 2.4 Device requirement — the binding problem

The Nemo engine is wired to a zoned device and there is no fallback:

* `NavySetup.cpp:359` → `createZNSDevice(...)` whenever `navyZonedDevice` is true;
  `Device.cpp:458-514` calls `zbd_open` / `zbd_list_zones` (libzbd) and **fails on any
  non-zoned block device**.
* `setupZNSKVCache` (`NavySetup.cpp:119-123`) dereferences `usesZnsArg.dev_`, which is only
  assigned inside `if (config.usesZonedDevice())` (`:264-268`) — so configuring ZNSKVCache
  with a plain file device is a null dereference, not a supported mode.
* `test.sh:118-120,143` runs `sudo nvme zns reset-zone /dev/<dev> -a`,
  `sudo tee /sys/block/<dev>/queue/scheduler`, and `sudo cachebench` on the raw device.
* The paper's own Artifact Appendix §A.3.2: *"The evaluation machine is equipped with a
  14 TB Western Digital ZN540 ZNS SSD. If a ZNS SSD is not available locally, the
  experiments cannot be fully reproduced on alternative hardware."*

Mitigation that reading the code does support: the ZNS-specific surface is **thin**.
`ZNSDevice::writeImpl/readImpl` are plain `pwrite`/`pread` (`Device.cpp:291-307`); only
`finishImpl`/`resetImpl` call libzbd (`:277-289`), and `MemoryDevice`/`FileDevice`'s
`resetImpl` already just `return true` (`Device.cpp:232`). Nemo writes a whole SG in one
`Device::write` at a zone-aligned offset (`performFlush`, `:203-255`) and calls
`device.reset(loc, euCap)` on eviction (`:930`) — semantics a file-backed "pseudo-zoned"
device can satisfy exactly. Adding such a device (~50–100 LOC in `Device.cpp` +
`Factory.cpp` + one config flag, reusing the existing `Device(size, …, ioNoOfZones,
ioZoneSize, ioZoneCapSize)` ctor at `Device.h:77-90`) removes both the hardware and the
root requirement. Nothing verifies this claim except reading; it is a prediction.

### 2.5 Data

Twitter cluster traces 14/29/34/52 are public (`twitter/cache-trace`, ref [27,28]).
The replay format is trivial: `key,OpType,size,repeats` CSV
(`ReplayGenerator.h:39-50`, `AmplifiedReplayGenerator.h:44-50`) — note **op type is parsed
and discarded** (`ReplayGenerator.h:81` "TODO optype parsing"), so the evaluated workload is
GET-only with lookaside fill. The repo contains **no script** that produces the
`merge.csv` described in §5.1 (4 clusters, 4 disjoint key spaces, 2×/3× size downscaling);
that preprocessing must be re-derived from the paper.

### 2.6 Evaluation scripts

Present: `test.sh` (one config, one run) and `clean_wa.py` (log → WA CSV).
Absent: any plotting script, any script per figure, any baseline-sweep driver, any
configs for Log/Set/Kangaroo (only `znscache_test.json` and an unrelated
`kvcache_l2_wc/config_zns.json`). The FairyWREN baseline lives on another branch and must
be built separately. The Artifact Appendix also refers to "Figure 11/13/14/15" where the
paper has Figures 12/14/15/16 — the numbering is off by one, minor but worth noting.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper Artifact Appendix §A.3.1 (p. 16) names the GitHub repo and Zenodo DOI 10.5281/zenodo.18332674; the Zenodo record archives commit `66db041`, the head of our clone. The repo contains the full engine (`cachelib/navy/znskvcache/`, ~2.9k LOC of new C++), not a stub. |
| `H2_no_root` | **unclear** | As released the evaluation needs root: `test.sh:118` `sudo nvme zns reset-zone`, `:120` writing `/sys/block/*/queue/scheduler`, `:143` `sudo cachebench` on a raw NVMe device; `build-package.sh:360` `sudo make install`. None of these needs a *kernel* change, and each is individually removable (libzbd can install to `$PREFIX`; the scheduler write is a tuning step). But obtaining a zoned block device at all on this machine would need root (`null_blk zoned` modprobe / QEMU+KVM / zloop on ≥6.14), so "no root" only holds *after* the file-backed device port of §2.4, which is a code change nobody has done. |
| `H3_hardware_fit` | **unclear** | Paper §A.3.2 states the experiments cannot be fully reproduced without a ZNS SSD; we have conventional PM9A3 NVMe in software RAID under `/home`, no raw-device access, ~257 GB free vs the paper's 360 GB cache on a 14 TB drive. CPU/RAM fit fine (16c/125 GB vs 24c/128 GB), no GPU needed. The headline metric (ALWA, Fig. 12a) is computed from in-engine counters (`logicalWrittenCount_`, `Device::bytesWritten_`, `clean_wa.py:44-59`), i.e. device-independent, and the paper's own Fig. 8 studies SG sizes down to 64 MB, so a scaled-down file-backed run *should* still test the claim — but only after the port, and read-latency results (Fig. 15) would be meaningless on a shared RAID volume. |
| `H4_obtainable_deps_data` | **pass** | All heavy deps are built from source into `./opt/cachelib` (`contrib/build-package.sh:113-255`: libzbd, zstd, gflags, glog, gtest, fmt, sparsemap, folly, fizz, wangle, fbthrift); remaining system libs (boost, libevent, double-conversion, libsodium, libunwind, elfutils/libdwarf, jemalloc, snappy, lz4) are all in conda-forge. Traces are the public Twitter cache traces ([27,28], `github.com/twitter/cache-trace`); trace format is a 4-column CSV (`ReplayGenerator.h:39-50`) so preprocessing is a small script. No proprietary data. Risk (not a fail): 2022-era folly vs gcc 12.2, and the missing `merge.csv` recipe. |

## 4. Reproduction plan

**Target.** Figure 12a (p. 11): steady-state write amplification, **Nemo 1.56 vs
FairyWREN 15.20** — the paper's central claim (a ~9× reduction in flash writes). Secondary,
cheaper target: Figure 17 (p. 12), the fill-rate breakdown naïve 6.78 % → B 31.32 % → B+P
36.77 % → B+P+W 89.34 %, which needs only Nemo and is a pure ablation via existing flags.

**Scale-down.**
* Replace the ZNS device with a **file-backed pseudo-zoned device** on `/home`
  (new branch in `createDevice`, `NavySetup.cpp:359`; new `PseudoZonedFileDevice` in
  `Device.cpp` reusing `Device.h:77` ctor, `resetImpl`/`finishImpl` = no-op or
  `fallocate(PUNCH_HOLE)`).
* 64 GB backing file, **256 MB pseudo-zones** ⇒ `numBuckets = 65536` (safely under the
  hard-coded `NUM_BUCKETS 275712`, `ZNSKVCache.h:27`), 256 zones ⇒ dataPool 250 /
  metaPool 5 (`ZNSKVCache.cpp:121-125`, needs ≥ 51 zones because `METADATARATIO 50`).
  In-memory SGs = 2 × 256 MB = 512 MB, `visitedMask` ≈ 130 MB — trivial on 125 GB.
* `navyRegionSizeMB: 256`, `nvmCacheSizeMB ≈ 65000`, DRAM cache 1000 MB as in
  `znscache_test.json`.
* Traces: clusters 52 + 34 (smallest WSS, 14 GB / 11.5 GB) merged with `ampFactor` tuned so
  WSS ≈ 2–3 × cache, giving the same "cache under pressure, eviction + writeback active"
  regime at ~1/6 the scale. Report WA vs ops (Fig. 14 style) to show steady state was
  reached.
* Do **not** attempt Fig. 15 (latency) — a file on the shared RAID cannot stand in for a
  ZNS SSD.

**Steps.** (1) conda env with the system libs; (2) `./contrib/build.sh -O -j -v` after
deleting the `sudo make install` line, patching folly for gcc 12 as needed — budget most of
the risk here; (3) write `pseudo_zoned` device + config flag; (4) write the Twitter→CSV
preprocessor (~50 lines Python) and validate mean object size ≈ 246 B; (5) run Nemo, parse
with `clean_wa.py`; (6) build the `FairyWREN` branch (same device port must be repeated
there) and run the matching config; (7) plot (no plotting scripts exist).

**Effort.** ≈ 10–14 person-days for two systems (build 3–5 d, device port 2 d, trace prep
1–2 d, runs/debug 3–4 d) + ~100 wall-clock machine-hours of replay; no GPU.

**Level: M.** Nothing is missing — engine, baseline, harness, public traces all exist, and
the headline metric is device-independent — but four separate pieces of real porting work
(no-root CacheLib build on an unsupported distro, 2022 folly on gcc 12, the pseudo-zoned
device, trace preprocessing) stand between the team and the first number, and the authors
themselves say the artifact cannot be fully reproduced without a ZNS SSD. Not H. Not L,
because each obstacle is well-understood and localized.

## 5. Add-on ideas

### A1. Nemo under real op mixes: updates, deletes, and stale copies

* **Hypothesis.** We hypothesize that replaying the Twitter traces' *actual* operation mix
  (get/set/delete/cas) instead of the GET-only replay used in the paper raises Nemo's
  effective WA and miss ratio disproportionately versus FairyWREN, because Nemo never
  invalidates superseded or deleted copies, and that SG-level tombstones plus
  BF-guided invalidation restore Nemo's advantage at < 1 bit/object extra DRAM.
* **Mechanism.** (a) Teach the replay generator to parse the op-type column it currently
  discards and issue real `set`/`delete`; (b) implement `ZNSKVCache::remove` (today a
  no-op that returns `Ok`) as an in-memory-SG tombstone recorded in the set-level BF plus a
  deleted-slot bitmap per on-flash set, consulted by `scanBucket`; (c) account for
  duplicate versions of the same key living in several SGs when computing effective
  capacity; report WA, miss ratio, and "fraction of lookups that hit a stale version".
* **`code_locations`**: `cachelib/navy/znskvcache/ZNSKVCache.cpp` (`remove` at :630,
  `lookupInSSD` at :582, `scanBucket`), `cachelib/navy/znskvcache/RegionBucket.cpp`,
  `cachelib/cachebench/workload/ReplayGenerator.h`,
  `cachelib/cachebench/workload/AmplifiedReplayGenerator.h`.
* **Motivating evidence.** `ReplayGenerator.h:81` "TODO optype parsing" — every request is
  `OpType::kGet`; `ZNSKVCache.cpp:630-633` `remove()` increments a counter and returns `Ok`
  without touching any data. The paper (§2.1, p. 3) itself stresses that "deletion is
  user-driven, while eviction is initiated by the cache" as the defining property of a KV
  *cache*, yet never exercises deletes. Twitter's own trace analysis (ref [27]) reports
  substantial set/delete fractions in several clusters.
* **Feasibility: M.** Tombstones touch the on-flash bucket format and the BF, and every
  baseline must be re-run; but all of it is inside one engine plus one generator, and the
  workload harness already exists.
* **Research value: H.** It questions whether the headline 9× WA win survives the workload
  the system claims to target, and either outcome is informative: if WA holds up, Nemo's
  case gets stronger; if not, the comparison against FairyWREN (which does implement
  removal) was measured in a regime that flattered Nemo.
* **`scoop_check`: clear.** Searches: "Nemo low write amplification cache tiny objects
  ASPLOS 2026", "FairyWREN Kangaroo flash cache follow-up write amplification 2026". The
  paper appeared on arXiv 2026-03-10 and no citing or follow-up work surfaced; the closest
  neighbour is [Towards Efficient Flash Caches with Emerging NVMe FDP SSDs
  (EuroSys'25)](https://arxiv.org/pdf/2503.11665), which studies FDP placement, not
  invalidation semantics.

### A2. Stop the free-riders: fill-rate-budgeted writeback

* **Hypothesis.** We hypothesize that replacing Nemo's "re-insert hot objects, then
  re-insert cold ones until the set is full" writeback with a fill-rate-*budgeted*,
  frequency-ranked writeback lowers the miss ratio at equal write amplification, most
  visibly on the least-skewed trace (cluster 34, Zipf α = 1.14).
* **Mechanism.** `writeBack()` runs two passes over each victim bucket: the first
  re-inserts objects whose hotness bit is set, the second re-inserts objects whose bit is
  **clear**, purely to fill space. Replace pass two with an explicit budget: re-insert cold
  objects only while the destination set is below a target fill (the WA target), choosing
  victims by a 2-bit counter instead of 1 bit, and charge re-inserted-cold bytes to logical
  writes so the WA/miss-ratio trade-off is visible. Sweep the budget from 0 (hot-only) to
  ∞ (current behaviour) and plot the WA–miss-ratio Pareto frontier the paper never shows.
* **`code_locations`**: `cachelib/navy/znskvcache/ZNSKVCache.cpp:846` (`writeBack`),
  `cachelib/navy/znskvcache/ZNSKVCache.cpp:909` (`evictZone`),
  `cachelib/navy/znskvcache/ZNSKVCache.h:140`.
* **Motivating evidence.** §6 "Limitations of hybrid hotness tracking": *"some cold objects
  may be mistakenly kept because they are part of a group marked as hot. This
  'free-riding' may reduce the accuracy of eviction."* The code is stronger evidence: the
  second loop at `ZNSKVCache.cpp:874-890` re-inserts objects with the hotness bit *clear*,
  and even computes `auto random = folly::Random::randDouble01();` (`:883`) that is never
  used — a probabilistic admission policy was evidently intended and abandoned. Fig. 17
  attributes 25 points of fill rate (64.13 → 89.34 %) to this mechanism, so its cost is
  material.
* **Feasibility: H.** ~200 LOC in one function plus one counter width change; evaluated
  with the existing harness and the two metrics it already reports.
* **Research value: M.** It fixes a limitation the authors named themselves, so the
  direction is expected; the value is in quantifying a trade-off (WA vs miss ratio) that
  the paper reports only at its own operating point.
* **`scoop_check`: clear.** Searched for follow-ups to Nemo and for hot-object-writeback
  policies in flash caches; nothing addresses Nemo's writeback. Related but different:
  Kangaroo's RRIParoo/threshold re-insertion (SOSP'21) and Flashield's admission (NSDI'19).

### A3. The index cache *is* the hotness oracle — give it a better policy

* **Hypothesis.** We hypothesize that replacing Nemo's strict-FIFO PBFG index cache with a
  lazy-promotion policy (CLOCK / S3-FIFO-style, one reference bit per entry) simultaneously
  reduces index reads from flash (Fig. 19b: today 8 % of requests at a 50 % cached ratio)
  and improves eviction accuracy — because index-cache membership is *also* the recency
  half of the hotness signal — at identical memory and without LRU's lock contention.
* **Mechanism.** `PBFGList` is a `deque` + map with `push` evicting from the front and no
  promotion on hit (`getPBFG` only looks up). Add a reference bit set in `getPBFG`, and
  evict with a CLOCK sweep; optionally a small "probationary" FIFO for one-hit-wonder
  PBFGs. Then measure (i) PBFG miss ratio vs the paper's Fig. 19b curve, (ii) read
  amplification (the paper's admitted >3× FW, §5.5), (iii) object miss ratio, since the
  hotness rule "hot = counter bit set AND PBFG cached" changes meaning.
* **`code_locations`**: `cachelib/navy/znskvcache/PBFGList.cpp`,
  `cachelib/navy/znskvcache/PBFGList.h`,
  `cachelib/navy/znskvcache/ZNSKVCache.cpp:582` (`lookupInSSD`, push at :622-625).
* **Motivating evidence.** §5 Implementation: *"The index cache is FIFO-style, which reduces
  lock contention under high access pressure compared to LRU [78,79]"* — the choice is
  justified only on contention grounds, never on hit ratio, even though §4.4 makes the same
  structure the recency signal for eviction. `PBFGList.cpp:29-35` confirms insert-order-only
  eviction. §5.5 concedes read amplification is >3× FairyWREN's, and index retrieval is
  named as one of the two sources.
* **Feasibility: H.** `PBFGList` is 52 lines of `.cpp` plus a small header; the metrics
  needed (`PBFGListHitMiss_`, `readSSDCount_`) are already instrumented.
* **Research value: M.** Applying modern FIFO-family policies to an index cache is a
  natural, well-motivated improvement, and the coupling to eviction accuracy makes it more
  than a cache-policy swap — but a reviewer would expect it to work.
* **`scoop_check`: clear.** Searched "flash cache bloom filter index cache replacement
  policy S3-FIFO SIEVE lazy promotion 2026". [S3-FIFO
  (SOSP'23)](https://s3fifo.com/blog/2023/06/01/fifo-is-better-than-lru-the-power-of-lazy-promotion-and-quick-demotion/)
  and [SIEVE (NSDI'24)](https://blog.jasony.me/system/cache/2024/06/12/sieve) are the
  policies to borrow, not prior work on Nemo's index cache; no one has applied them to a
  PBFG-style approximate index.

### A4. Wake the dormant two-choice/kick-off path: past 89 % fill

* **Hypothesis.** We hypothesize that two-choice set placement with bounded cuckoo-style
  kicking raises the SG fill rate from 89.3 % toward >95 % (WA 1.56 → ~1.05–1.15, i.e.
  within noise of the log-structured lower bound of 1.08) at the cost of up to 2× lookup
  read amplification, and that a hybrid (second choice used only for sets below the flush
  threshold) sits strictly inside that Pareto frontier.
* **Mechanism.** The engine already contains a second hash (`getZNSKVCacheBucketId2`,
  `keyHash2`), a load-balancing two-choice insert, a bounded `kickLoop`, and a two-probe
  lookup — all gated by `isEnableDoubleHash` / `isEnableKickOff`, both **false** in the
  shipped config. Turn them on, find the missing pieces (the PBFG must be consulted for
  both candidate sets, and `bfRebuild` must run on every kick), and sweep `maxNumKicks`.
  Then implement the hybrid gate and measure fill rate, WA, read amplification, p99 latency.
* **`code_locations`**: `cachelib/navy/znskvcache/ZNSKVCache.cpp:352` (`insert`),
  `cachelib/navy/znskvcache/ZNSKVCache.cpp:489` (`kickLoop`),
  `cachelib/navy/znskvcache/ZNSKVCache.cpp:537` (`lookup`),
  `cachelib/cachebench/util/CacheConfig.h`,
  `cachelib/cachebench/test_configs/ssd_perf/znskvcache/znscache_test.json`.
* **Motivating evidence.** `znscache_test.json:35-38` ships
  `navyZNSKVCacheEnableDoubleHash: false`, `EnableKickOff: false`; the paper never mentions
  two-choice hashing or kicking anywhere, so a whole placement mechanism sits in the
  artifact unevaluated. The paper's C1 framing (§4.2) is entirely about *delaying* flushes
  to beat short-term hash skew — two-choice placement attacks the same skew directly, and
  the 10.7 % of an SG still unfilled is exactly the residual WA.
* **Feasibility: H.** Flags exist; the change is config + completing the PBFG/lookup side;
  evaluated with the existing harness and the fill-rate counters used for Fig. 17.
* **Research value: M.** Two-choice hashing raising set-associative load factor is a
  textbook result, so the *direction* is unsurprising; what is interesting and unreported is
  the WA-vs-read-amplification exchange rate in a design that already pays >3× read
  amplification, i.e. whether Nemo has any headroom left.
* **`scoop_check`: clear.** Searched "cuckoo two-choice hashing set-associative flash cache
  fill rate write amplification 2026" — results are generic cuckoo-hashing literature
  (e.g. [MemC3/concurrent cuckoo,
  EuroSys'14](https://www.cs.princeton.edu/~mfreed/docs/cuckoo-eurosys14.pdf)) plus the Nemo
  paper itself; no one has evaluated this inside Nemo.

### A5. Does Nemo generalize off the Zipf-1.2 / single-instance operating point?

* **Hypothesis.** We hypothesize that Nemo's miss-ratio parity with FairyWREN and its
  read-amplification budget both degrade as workload skew falls (Zipf α 1.2 → 0.7) or as
  the SG-pool size N grows, because per-lookup candidate SGs scale as 1 + (N−1)·fp and the
  hotness inference depends on strong set-level skew; and that the partitioning scheme the
  paper proposes but never evaluates (Appendix A) bounds read amplification at a measurable
  WA and miss-ratio cost.
* **Mechanism.** (a) Drive CacheBench's synthetic generator at α ∈ {0.7, 0.9, 1.1, 1.3}
  with a 246 B mean size, and sweep the SG count N by shrinking the pseudo-zone size at
  constant total capacity; (b) instrument candidate-SG counts per lookup
  (`calZoneId`) and compare with Eq. (10); (c) implement partitioning by instantiating k
  independent `ZNSKVCache` engines over disjoint zone ranges (the engine is already
  parameterized by `cacheBaseOffset` / `dataZoneOffsetId`) and sweep k.
* **`code_locations`**: `cachelib/navy/znskvcache/ZNSKVCache.cpp:782` (`calZoneId`),
  `cachelib/navy/znskvcache/ZNSKVCache.cpp:746` (`getPBFGFromDevice`),
  `cachelib/allocator/nvmcache/NavySetup.cpp`,
  `cachelib/navy/znskvcache/ZonePool.cpp`.
* **Motivating evidence.** Appendix A, *"Impact of scaling flash capacity"*: partitioning is
  asserted to bound read amplification with **no experiment**. §5.4/Fig. 19a shows the
  hotness machinery leaning on "≈70 % of accesses in the top 30 % of sets" — a property of
  the four chosen traces (Table 5: α = 1.14–1.30). Table 5's selection criteria explicitly
  filter for α ≈ 1 and large WSS, so low-skew behaviour is untested; §5.5 already concedes
  3× read amplification at N = 350.
* **Feasibility: M.** The skew sweep is cheap and uses stock CacheBench generators, but
  multi-instance partitioning means touching `setupCacheProtos`/`NavySetup`, which assumes
  a single small-object engine, and the sweep multiplies run time.
* **Research value: H.** It tests the generality of the central claim and settles an
  unevaluated assertion in the paper's own appendix; a negative result (Nemo's advantage is
  skew-dependent) would be a genuine contribution, and a positive one strengthens the design.
* **`scoop_check`: clear.** Same searches as A1 plus a scan of ASPLOS'26 program listings;
  no follow-up evaluates Nemo at other skews or with partitioning. Related context:
  [FairyWREN, ACM TOS 2025](https://doi.org/10.1145/3718390) extends the OSDI'24 paper but
  predates Nemo.

## 6. Risks and open questions

1. **No zoned device, no root.** The single biggest risk. Everything hinges on the
   pseudo-zoned file device described in §2.4 being as easy as the code suggests. If the
   engine turns out to depend on real zone semantics somewhere we did not read (e.g.
   implicit zone-open limits, write-pointer behaviour on partial writes), the project
   stalls. Mitigation: prototype the device in week 1 before committing.
2. **CacheLib build without root on Debian 12.** `build.sh` has no Debian 12 recipe;
   2022-era folly + gcc 12.2 is a known friction point; conda-provided boost/libevent/
   double-conversion must be discovered by CMake. Budget days, not hours.
3. **Fidelity of a file-backed run.** Page-cache effects (the device is opened with
   `O_DIRECT`? not verified — `Device.cpp` `openInFile` flags were not read in detail) and a
   shared RAID volume mean latency figures (Fig. 15) and any DLWA statement cannot be
   reproduced. Only ALWA and fill-rate results should be claimed.
4. **Baseline symmetry.** The FairyWREN comparison requires porting the *same* pseudo-zoned
   device to the `FairyWREN` branch; if the port differs, the 9× gap is not a fair
   measurement. The paper's own FairyWREN numbers come from the authors' bug-fixed fork
   (§3, p. 4), which is itself an unverified claim about a third party's artifact.
5. **Hard-coded parameters.** `NUM_BUCKETS 275712`, `METADATARATIO 50`,
   `maxWaitTimesBeforeFlush 1000` vs Table 3's 4,096 (`ZNSKVCache.h:25-27,228`): the shipped
   default does not match the paper's stated configuration, so the first reproduction may
   not land on 1.56 without a recompile. Worth an early sanity check.
6. **Latent correctness issues visible in the code.** `visitedMask[...] | (1 << objId)`
   (`ZNSKVCache.cpp:615-616`) shifts an `int` into an `int64_t` mask — undefined for
   objId ≥ 31, reachable if objects are much smaller than 246 B. `reInsert` (`:897`) is
   declared `bool` but returns nothing. `findEuId` (`:166`) has no return. These do not
   block reproduction at the paper's object size but constrain add-on workloads (A5's
   small-object sweeps).
7. **Run length.** Figure 14 runs to ~10^5 million operations to reach steady state; even
   scaled down, expect multi-day unattended runs (the Artifact Appendix says "one to two
   weeks" for the full set). Plan the 10-week schedule around one or two long runs, not many.
8. **Deletes/updates are outside the evaluated envelope** (A1) — this is simultaneously the
   most interesting add-on and a caveat on any reproduction: the reproduced numbers describe
   a GET-only regime.

## 7. Evidence index

**Paper** (`paper.txt`, page markers; `pages/page-NN.png` for figures)
* Abstract & §1 (pp. 1–2): problem, FairyWREN ALWA > 15×, Nemo ALWA 1.56, 8.3 bits/obj.
* §2.2–2.3 (p. 3), Table 1: ALWA/DLWA definitions, three prior design families.
* §3 (p. 4): FairyWREN bug fixes; Fig. 3 WA breakdown.
* §3.2 (pp. 5–6), Eq. 1–8, Figs. 4, 5, 6: L2SWA(P) = 8.5 measured vs ≈9 theory; 2.04 objects
  per set write; p ≈ 25 %; Observations 1–4.
* §4.1 (pp. 6–7), Fig. 7, Eq. 9: SG architecture, PBFG, selective metadata offload.
* §4.2 (pp. 8–9), Figs. 8, 9: short-term hash skew, three fill-rate techniques.
* §4.3 (p. 9), Fig. 10: set-level PBFG breakdown and page-aligned packing.
* §4.4 (pp. 9–10), Fig. 11, Table 3: hybrid hotness, cooling, configuration
  (275,712 sets/SG, p_th 4,096, 50 % cached PBFG, last 30 % hotness window).
* §5.1 (p. 10), Tables 4, 5: ZN540 ZNS SSD, 360 GB cache, baselines, Twitter clusters
  14/29/34/52, 246 B mean object.
* §5.2 (p. 11), **Fig. 12a** (read from `pages/page-11.png`): WA 1.56 / 1.08 / 15.20 /
  16.31 / 55.59; Fig. 12b: FW OP20 9.29, OP50 6.56, Log20 4.12; Figs. 13–16.
* §5.3 (p. 12), Fig. 17: fill-rate ablation 6.78 → 31.32 → 36.77 → 64.13 → 89.34 %.
* §5.4 (p. 12), Figs. 18, 19: p_th sweep; set-access skew; PBFG miss ratio.
* §5.5 (pp. 12–13), Table 6: 8.3 bits/obj breakdown; read amplification >3× FW.
* §6 (p. 13): device compatibility, index-accuracy trade-off, free-riding limitation.
* Appendix A (pp. 16–17): Eq. 10–11, N = 350, 0.1 % vs 0.01 % FP, partitioning proposal.
* Artifact Appendix (pp. 16–17): GitHub + Zenodo URLs, "ZNS SSD required", ">32 GB memory",
  figure list for reproduction.
* `pages/page-01.png`: no ACM artifact badges on the arXiv version.

**Repository** (paths relative to `repo/`)
* `README.md` (build/run instructions, FairyWREN branch, `clean_wa.py` usage).
* `test.sh:101-143` (build, `sudo nvme zns reset-zone`, scheduler, `sudo cachebench`).
* `clean_wa.py:44-59` (WA = (physical − logical + soc)/soc).
* `cachelib/cachebench/test_configs/ssd_perf/znskvcache/znscache_test.json` (full config).
* `cachelib/navy/znskvcache/ZNSKVCache.h` (:21-27 constants, :120-130 bucket-id hashing,
  :183-229 members, :228 `maxWaitTimesBeforeFlush`).
* `cachelib/navy/znskvcache/ZNSKVCache.cpp` (:45-139 ctor/sizing, :182-262 flush path,
  :352-460 insert, :462-476 `flushLoop`, :479-487 `getFreeDataRegionId`, :489-535 `kickLoop`,
  :537-628 lookup/`lookupInSSD`, :630-633 no-op `remove`, :668-681 cooling, :746-800
  PBFG retrieval/`calZoneId`, :846-895 `writeBack`, :897-907 `reInsert`, :909-932
  `evictZone`).
* `cachelib/navy/znskvcache/PBFGList.cpp:7-48`, `PBFGList.h`, `PBFG.h` (FIFO index cache).
* `cachelib/navy/znskvcache/ZonePool.h` (FIFO SG pool arithmetic).
* `cachelib/navy/common/Device.cpp:24` (`libzbd/zbd.h`), `:232` (file/memory `resetImpl`),
  `:240-309` (`ZNSDevice`), `:458-514` (`createZNSDevice`, `zbd_open`/`zbd_list_zones`).
* `cachelib/navy/common/Device.h:61-90,158-196` (zone-aware `Device` ctor and accessors).
* `cachelib/allocator/nvmcache/NavySetup.cpp:103-157` (`setupZNSKVCache`), `:244-325`
  (`setupCacheProtos`), `:353-388` (`createDevice`).
* `cachelib/cachebench/util/CacheConfig.h:144-178` (ZNSKVCache knobs).
* `cachelib/cachebench/workload/ReplayGenerator.h:39-83` (CSV format, "TODO optype parsing"),
  `AmplifiedReplayGenerator.h:31-104`.
* `cachelib/cachebench/runner/Stressor.cpp:142-146` (`generator: replay` →
  `AmplifiedReplayGenerator`).
* `contrib/build.sh:84-92,150-159` (source-built deps, distro dispatch),
  `contrib/build-package.sh:113-255,290-296,356-361` (pins, `$PWD/opt/cachelib` prefix,
  `sudo make install` for libzbd), `contrib/prerequisites-debian10.sh` (system packages).
* `cachelib/CMakeLists.txt:20,85` (cmake ≥ 3.12, C++17). `CHANGELOG.md` (CacheLib V17).
* `.gitmodules`, `.git/packed-refs` (only `origin/nemo` in this shallow clone).

**Web**
* https://api.github.com/repos/XMU-DISCLab/Cachelib-Nemo/branches → branches `FairyWREN`,
  `nemo`.
* https://zenodo.org/doi/10.5281/zenodo.18332674 → "XMU-DISCLab/Cachelib-Nemo:
  Zenodo-nemo-asplos26-artifact", archive of commit `66db041`, Apache-2.0, no badge mention.
* Scoop-check searches (2026-09-14): Nemo follow-ups, FairyWREN/Kangaroo successors,
  cuckoo/two-choice set-associative flash caches, S3-FIFO/SIEVE-style index caches — nothing
  that pre-empts A1–A5.
