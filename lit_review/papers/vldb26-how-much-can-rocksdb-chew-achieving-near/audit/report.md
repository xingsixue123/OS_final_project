# How Much Can RocksDB Chew? Achieving Near-Zero Write Stalls with Sustainable RocksDB

PVLDB 19(11):3202–3215, 2026 · Shin, Lee, Yoo, Choi (Dankook University)
Repo audited: `repo/` = https://github.com/shinhojin/Sustainable-RocksDB @ `77e25ee` (2026-05-31)

---

## 1. Paper summary

**Problem.** RocksDB decouples foreground write ingestion from background flush/compaction. When
ingress persistently exceeds background drain capacity, L0 files and pending-compaction bytes
accumulate until a hard threshold is crossed, at which point RocksDB's reactive safeguards
(`write slowdown`, `write stop`) freeze or delay foreground writes (§2.2). The paper argues this
is structurally a bang-bang controller (Eq. 2, §3.1) and therefore produces a *limit cycle*:
Figure 2 shows throughput oscillating between ~200 MB/s and 0 with 1.36M stalled writes in a single
30-minute window of a 12-hour `fillrandom` run. Static rate limiting (§3.2, Figure 3) is shown to
be a poor fix: a 100 MB/s cap still leaves 68% of the baseline stalled writes, and only an
over-conservative 30 MB/s cap eliminates them.

**Key idea.** Reframe stall avoidance as *continuous admission control*. Regulate admitted ingress
`B_u(t) = m_t · B_u^req(t)` (Eq. 5) so that it tracks the time-varying internal service capacity
`B_int(t) = B_f(t) + B_c(t)` (Eq. 3). Notably §4.1 explicitly declines to estimate `B_f`/`B_c`
directly, using pressure signals (pending compaction bytes, L0 count) as integral proxies instead.

**Design (§5).** A hierarchical controller running at 1-second epochs, split into an in-process
C++ poller/actuator and an out-of-process Python controller (Figure 6):
- **UNSAFE** — stall observed (write-stop flag, positive delayed-write rate, or stall counter
  increase) ⇒ `m ← m_min = 0.01`, held for `T_hold = 10 s` (§5.3.1, §5.4.1).
- **SEMI-SAFE** — pre-stall region entered on backlog ≥ 32 GB, fast backlog rise, or L0 ≥ 16
  (below RocksDB's native margins of ~20 L0 files / 64 GB) ⇒ deterministic step-down with
  floor/cap (Eq. 10), learning disabled, hysteresis + hard-lock (§5.3.2, §5.4.2).
- **SAFE** — online **linear-function-approximation Q-learning** over a 12-dim state
  (Eq. 12: L0, backlog, flush backlog, delayed rate, ingress, P99, time-since-UNSAFE, `m`, one-hot
  state) picks `Δm ∈ {−0.02, −0.01, 0, +0.01, +0.02}` (Eq. 11). α=0.05, γ=0.95, ε=0.25.
  Reward (Eq. 15–16): −200 on stall, else `1 + 1.8·m − 0.18|Δm| − 0.18·backlog_norm − 0.15·ΔP99_norm`.
- A **SAFE-only, actuation-synchronized training gate** prevents credit assignment when guardrails
  overrode the learned action (§5.5.2).

**Evaluation setup (§6.1, Table 1).** Single server, 2× Xeon Gold 6338, 504 GB RAM, Samsung 870 EVO
SATA SSD (1/2 TB). Five variants: RocksDB 10.6.0 (2 BG threads, 64 MB memtable), S-RocksDB(R)
(same resources, m_max=0.2), SILK 5.7.0 (4 threads, 128 MB), S-RocksDB(S) (matched to SILK,
m_max=0.5), ADOC 7.7.0. Workload: 16 B keys, 1 KB values, write-intensive.

**Headline numbers.**
- 24-hour `fillrandom` (§6.2): stalled writes 64.3M (RocksDB), 555.3M (SILK), 142.9M (ADOC) →
  **10,206** (S-RocksDB(R)) and **69** (S-RocksDB(S)). Stall time/1-min bucket 49.3 s / 45.5 s →
  0.013 s / 0.007 s (Figure 10). ADOC has a single 1056 s write-stop episode.
- Tail latency (Figure 11): both S-RocksDB configs keep P99.99 < 0.1 ms and extreme tail ≤ 3 ms,
  vs. 54.54 ms P99.999 for ADOC and millisecond-range for RocksDB/SILK.
- Throughput in the stabilized 12–24 h window: 9.48 → 9.66 MB/s (R vs RocksDB), 13.35 → 14.2 MB/s
  (S vs SILK), with far lower variance (σ 62.34 MB/s for ADOC vs 12.84 MB/s for S-RocksDB(S)).
- Resource use (Figure 12): 98.8% CPU / 2.80 GB → 79.1% CPU / 2.37 GB (R vs RocksDB);
  10.86 GB → 3.52 GB memory (S vs SILK). Controller CPU overhead 0.4% (§6.3).
- YCSB (§6.4, Figure 14a): S-RocksDB finishes the load phase with **zero** pending compaction bytes
  and zero L0 files vs 32.95–33.99 GB for the baselines; read-only C/D throughput 209K/206K ops/s
  vs 68K/73K for RocksDB. Write-heavy A/F are "comparable or slightly lower".
- Controller ablation (§6.6): Table 3 (12 h) Q-learning 18.6 MB/s / 50 stalls vs PID 14.5 MB/s /
  105 stalls vs AIMD 18.3 MB/s / 0.63M stalls vs RocksDB 13.8 MB/s / 31M stalls. Table 4 (3 h,
  S-RocksDB(R)): SEMI-SAFE on = 14.55 MB/s / 1 stall / P99.99 81.3 µs; off = 16.31 MB/s /
  69,828 stalls / P99.99 1194.6 µs.
- Hardware robustness (§6.5, Table 2): 3 setups (SATA, NVMe, different CPU), same controller
  parameters except the `write_mb_per_sec` normalization reference (500 for SATA, 3000 for NVMe).

**Stated limitations / future work.** §6.8 only sketches portability to Cassandra/HBase/ScyllaDB;
no experiment. There is no multi-client / multi-column-family evaluation, no burst workload, no
read-side signal in the controller, and no analysis of where the throttled time goes from the
client's point of view.

---

## 2. Artifact audit

### 2.1 Repo structure

The repository is a full fork of RocksDB 10.6.0 (2104 files, 40.6 MB, 547k lines of `.cc`) plus
four S-RocksDB-specific top-level directories:

```
srocksdb_src/rl_poller.cc        1900 LOC  C++ workload driver + metrics poller + FIFO actuator
srocksdb_src/agent_rl_fifo.py    1800 LOC  out-of-process controller (Linear-Q / AIMD / PID)
srocksdb_options/rl_options_{r,s}.ini      the two option presets of Table 1
srocksdb_scripts/*.sh            8 runners (main, YCSB, time-varying, sensitivity, 3 baselines)
```
plus in-tree modifications to upstream RocksDB (see map below).

### 2.2 Paper component → code path

| paper element | code |
|---|---|
| Actuator: `B_u(t) = m_t · base_rate` (Eq. 5) | `db/db_impl/db_impl.cc:4770` `SetWriteIngressMultiplier` → `rl_ingress_limiter_->SetBytesPerSecond(base_rate * m)` at `:4844` |
| ingress rate limiter creation | `db/db_impl/db_impl.cc:278-284` (`NewGenericRateLimiter`, 100 ms refill, `kWritesOnly`) |
| throttle on the write path | `db/db_impl/db_impl_write.cc:495-499` → `MaybeThrottleWriteIngress` (`db/db_impl/db_impl.cc:807`) |
| `Δm_max` slew limit (Eq. 8) | `db/db_impl/db_impl.cc:4802-4810` (`rl_write_delta_max`) |
| runtime control channel | `SetDBOptions("rl_write_multiplier", …)` special-cased at `db/db_impl/db_impl.cc:1512-1531`; FIFO reader `srocksdb_src/rl_poller.cc:513` `FifoCommandThread` |
| metrics sampler (1 s / 500 ms epochs) | `db/db_impl/db_impl.cc:827-980` `StartRLMetricsSampler` / `RLMetricsSampler`; new `rocksdb.rl.*` properties |
| new DB options (`rl_enable_metrics`, `rl_enable_write_throttling`, `rl_write_base_rate_bytes_per_sec`, `rl_write_m_min`, `rl_write_delta_max`, `rl_write_emergency_override`) | `include/rocksdb/options.h`, `options/db_options.{h,cc}`, `options/options_helper.cc` |
| tail-latency percentiles P99.9/99.99/99.999 (Figure 11) | added to `HistogramData`; computed in `monitoring/histogram.cc:236-238`, read at `db/db_impl/db_impl.cc:900-913` from the `DB_WRITE` histogram |
| "stalled writes" metric (§4.2) | `srocksdb_src/rl_poller.cc:1654-1668`, `WRITE_STALL` histogram `count` |
| state vector `s_t` (Eq. 12) | `srocksdb_src/agent_rl_fifo.py:421-487` `make_state` — exactly the 12 features of Eq. 12 |
| Linear-Q update (Eq. 13–14) | `srocksdb_src/agent_rl_fifo.py:231-272` `LinearQAgent` |
| state classification SAFE/SEMI-SAFE/UNSAFE (§5.3) | `srocksdb_src/agent_rl_fifo.py:1250-1323` |
| state-dependent policies (Eq. 9–11) | `srocksdb_src/agent_rl_fifo.py:1392-1490` |
| SAFE-only actuation-synced training gate (§5.5.2) | `srocksdb_src/agent_rl_fifo.py:1383-1391` (`trainable = … and actuation_synced`) |
| reward shaping (Eq. 15–16) | `srocksdb_src/agent_rl_fifo.py:1512-1536`; defaults C=200, λ=1.8, η=0.18, ε_b=0.18, ε_ℓ=0.15 in `srocksdb_scripts/run_agent_rl_LQ.sh:46-68` |
| PID / AIMD baselines (Table 3) | `srocksdb_src/agent_rl_fifo.py:1411-1469`; runners `srocksdb_scripts/run_agent_pid_backlog.sh`, `run_agent_pid_l0.sh`, `run_agent_aimd_stall_only.sh` |
| SEMI-SAFE ablation (Table 4) | `--soft_guard_disabled` flag, `srocksdb_scripts/run_agent_fifo.sh:308` |
| sensitivity sweep (Figure 16) | `srocksdb_scripts/run_sensitivity_3h.sh` (15 one-factor cases) |
| YCSB A–F and time-varying workloads (Figs 14, 15) | `srocksdb_src/rl_poller.cc:1010-1227` `YcsbThread`; runners `run_agent_rl_ycsb.sh`, `run_agent_rl_LQ_timevarying.sh` |

Every design element of §5 has a concrete implementation. The mapping is unusually clean.

### 2.3 Build route on this machine

`make -j32 rl_poller` (README "Build"; target defined at `Makefile:1345`, source resolved at
`Makefile:644`). This builds the full static `librocksdb.a` and links `srocksdb_src/rl_poller.cc`.
Requirements per README: Linux, gcc/g++, make, python3, numpy — all present (gcc 12.2, make 4.3,
Python 3.12 conda). `rl_poller.cc` includes only `rocksdb/{db,options,statistics,utilities/options_util}.h`
— no gflags, no gtest. Compression libs are optional in RocksDB's Makefile; if snappy/zstd are
absent the build falls back to no compression (which, for these 62-symbol random values, barely
matters). Expect ~15–30 min of wall clock for a cold `-j32` build. **No root required.**

### 2.4 Dependency pins and age

There are effectively none: no `requirements.txt`, no pinned Python versions, no CUDA, no ML
framework. `numpy` is the only Python dependency (`agent_rl_fifo.py:31`). The code is a
2026 RocksDB fork against a 2026 toolchain — zero dependency rot risk. This is the lowest-risk
dependency profile of any artifact in this venue class.

### 2.5 Data / traces / models

None needed. The workload is generated in-process:
`WriterThread` (`srocksdb_src/rl_poller.cc:918`) is the `fillrandom` driver — random int32 keys,
`DbBenchStyleValueGenerator` values (`:727`, the db_bench `RandomGenerator` pattern), open-loop
paced at `--write_mb_per_sec`. `YcsbThread` (`:1010`) implements YCSB A–F plus `r10w90/r90w10/r50w50`
with a built-in Zipf generator and a bounded key space (`max_inserted_key`). **H4 is trivially
satisfiable**: no downloads, no licences, no proprietary traces.

### 2.6 Evaluation scripts: present and absent

Present: single-run, YCSB batch, time-varying, 15-case sensitivity sweep, PID and AIMD baseline
runners. All controller and safety constants of §5 are exposed as CLI flags
(`srocksdb_scripts/run_agent_fifo.sh:115-223` lists ~90 options). Outputs are well-defined CSVs
(`rl_metrics.csv`, `agent_log.csv`, `resource_usage.csv`) whose columns cover every quantity
plotted in the paper.

Absent, and this is the main artifact gap:
1. **No plotting or analysis scripts.** Nothing in the tree turns `rl_metrics.csv` / `agent_log.csv`
   into Figures 2, 8–16 or Tables 2–4. Every number must be re-derived by the team.
2. **No vanilla-RocksDB baseline runner.** Reproducing "RocksDB: 64.3M stalled writes" requires
   running `rl_poller` manually with `rl_enable_write_throttling=false` and no agent — doable
   (the same binary and workload driver serve as the baseline) but undocumented.
3. **No SILK or ADOC.** Those baselines live in external repos at RocksDB 5.7.0 / 7.7.0; the paper's
   cross-system comparisons (Figs 8–12) cannot be reproduced from this repo alone.
4. **Machine-specific defaults.** `DB_PATH=/mnt/f2fs/rlrocksdb_log` (F2FS) in
   `run_agent_rl_LQ.sh:20`, `run_sensitivity_3h.sh:13`, `run_agent_rl_ycsb.sh:9`. README §"Before
   You Run" flags this and every script accepts `--db_path`.
5. `run_sensitivity_3h.sh:4` does `ulimit -n 1048576` under `set -e`; if the user's hard `nofile`
   limit is lower this script aborts immediately. Trivial to edit; the main runner does not do it.

### 2.7 Measurement caveat found by reading the code

`MaybeThrottleWriteIngress` is called at `db/db_impl/db_impl_write.cc:498`, i.e. at the very top of
`DBImpl::WriteImpl` (which starts at `:370`). The `DB_WRITE` histogram's `StopWatch` is only
constructed at `db/db_impl/db_impl_write.cc:556`, *after* that call. Therefore the time a write
spends blocked in S-RocksDB's own ingress rate limiter is **excluded** from the `DB_WRITE`
histogram — which is precisely the histogram from which the paper's P99…P99.999 numbers are taken
(`db/db_impl/db_impl.cc:904-913`). RocksDB's native stall delay, by contrast, happens inside
`PreprocessWrite` (`:1498`), i.e. *inside* the StopWatch and therefore fully counted.

So Figure 11 and Table 2 compare "RocksDB latency including stall wait" against "S-RocksDB latency
excluding admission wait". The `fillrandom` driver (`WriterThread`, `:918`) records no per-Put
latency of its own, so there is no end-to-end number to cross-check against; only the YCSB path
(`RecordYcsbLogicalOpLatencyUs`, `:1125`/`:1222`) times the full operation, and the paper reports
only throughput for YCSB. This does not invalidate the stall-count results (which are unambiguous),
but it means the headline "sub-0.11 ms P99.99" claim has not been shown to hold end-to-end. It is
the basis of add-on A1.

---

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper's "PVLDB Artifact Availability" statement (p. 1) names https://github.com/shinhojin/Sustainable-RocksDB; GitHub owner `shinhojin` matches first author Hojin Shin (`hojin03s@dankook.ac.kr`). The tree contains the actual system, not a stub: the RocksDB-side hooks (`db/db_impl/db_impl.cc:4770`, `db/db_impl/db_impl_write.cc:495`), the poller/actuator (`srocksdb_src/rl_poller.cc`), the Q-learning controller (`srocksdb_src/agent_rl_fifo.py:231`), the two option presets of Table 1, and runners for the microbenchmark, YCSB, time-varying and sensitivity experiments. |
| `H2_no_root` | **pass** | Nothing in the S-RocksDB path needs privilege: user-space process, a FIFO in `/tmp`, `ps` and `/proc/meminfo` for the resource monitor (`srocksdb_scripts/run_agent_fifo.sh:392-446`). `SUDO_CMD` defaults to empty (`run_agent_rl_LQ.sh:97`) and is used only for optional log copying. No kernel module, eBPF, `perf`, KVM, hugepages, or `/proc/sys` writes. The `sudo`/`docker`/`sysctl` red-flag hits in `repo_facts.json` are all upstream RocksDB CI and documentation (`.github/workflows/*`, `build_tools/ubuntu20_image/Dockerfile`, `include/rocksdb/advanced_options.h:355` comment). Minor: `run_sensitivity_3h.sh:4` raises `ulimit -n`, which may fail if the hard limit is low — one-line edit. |
| `H3_hardware_fit` | **pass (with mandatory scale-down)** | Single node, CPU-only, no GPU, 4 background jobs max (`rl_options_s.ini:18`). RAM: the paper's peak is 10.86 GB (SILK); S-RocksDB uses 2.4–3.5 GB (§6.2) — far under 125 GB. The binding constraint is **disk**: `fillrandom` uses random int32 keys, so essentially every Put is a new key; at the paper's ~14–19 MB/s a 24 h run stores ~0.8–1.3 TB, versus ~257 GB free on `/home`. Paper-scale 12 h/24 h runs are therefore out of reach, but the paper's own **3-hour** ablation (Table 4, ~160–180 GB) fits, and unbounded growth is avoidable altogether by using the built-in bounded-keyspace modes (`--ycsb_workload=r10w90 --ycsb_record_count=…`, `srocksdb_src/rl_poller.cc:1199`), which the paper itself uses for Figure 15. Our NVMe (PM9A3) differs from the paper's primary SATA SSD, but §6.5/Table 2 (HW-B, HW-C) already validates NVMe with `write_mb_per_sec=3000`, and `run_agent_rl_LQ.sh:28` defaults to exactly that. |
| `H4_obtainable_deps_data` | **pass** | Dependencies: gcc/make (present), python3 + numpy (`README.md` "Requirements", `agent_rl_fifo.py:31`) — installable in user space. No datasets, traces or model weights: both workload generators are in-tree (`srocksdb_src/rl_poller.cc:918` and `:1010`). The SILK/ADOC baselines are external but both are publicly released, and none of the add-ons below require them. |

No `fail`, no `unclear`.

---

## 4. Reproduction plan

**Target.** **Table 4** (§6.6, p. 3213): *S-RocksDB(R) with SEMI-SAFE on = 14.55 MB/s with 1 stalled
write and P99.99 = 81.3 µs; with SEMI-SAFE off = 16.31 MB/s with 69,828 stalled writes and
P99.99 = 1,194.6 µs.* This supports the paper's core claim that the deterministic pre-stall guardrail
— not the learning alone — is what suppresses stalls. It is the best target because (a) it is a
3-hour experiment, the only headline result that fits our disk at paper scale; (b) it needs only
code in this repo (no SILK, no ADOC); (c) the ablation switch already exists as a CLI flag
(`--soft_guard_disabled`, `srocksdb_scripts/run_agent_fifo.sh:308`); (d) both arms use
`rl_options_r.ini`, the R preset, whose defaults (2 BG jobs, 64 MB memtable) are RocksDB defaults.

A third arm — vanilla RocksDB 10.6.0, same driver, `rl_enable_write_throttling=false`, no agent —
gives the "31M stalled writes" reference point of Table 3 in a 3-hour form and costs one more run.

**Scale-down.**
- 3 h per arm (paper scale for Table 4), `--db_path` on `/home`, ext4 instead of F2FS.
- `--write_mb_per_sec 3000` (NVMe normalization reference per §6.5) — note this sets both the
  offered-load pacing of `WriterThread` *and* the rate-limiter base (`run_agent_fifo.sh:526`),
  so `m ≈ 0.005–0.05` will correspond to the same absolute MB/s as the paper's SATA setting.
- Clear the DB between arms (default `CLEAR_DB_BEFORE=1`); peak footprint ~180 GB per arm, so
  arms must run **sequentially**, never concurrently.
- For any run longer than ~4 h, switch to bounded keyspace: `--ycsb_workload r10w90
  --ycsb_record_count 100000000` caps the DB at ~100 GB while keeping compaction saturated.

**Steps.**
1. `make -j32 rl_poller` (~0.5 day incl. fixing any missing optional compression lib).
2. Write a small analysis script: parse `agent_log.csv` + `rl_metrics.csv` + `db_LOG` into
   (throughput, cumulative `write_stall_hist_count`, DB_WRITE P99/P99.9/P99.99). ~0.5 day — the
   repo ships none.
3. Smoke run: 10-minute `run_agent_rl_LQ.sh` with `--db_path`, `--options_file rl_options_r.ini`,
   `--m_max 0.2`, confirm `[rl] write_multiplier changed` appears in the RocksDB LOG and
   `agent_log.csv` shows SAFE/SEMI_SAFE/UNSAFE transitions.
4. Arm 1: 3 h, `--soft_guard_enabled` (default). Arm 2: 3 h, `-- --soft_guard_disabled`.
   Arm 3: 3 h vanilla. ~10 h wall clock plus cleanup.
5. Compare against Table 4. Expect the *ordering* and the order-of-magnitude stall gap to hold;
   absolute MB/s will differ (NVMe vs SATA, ext4 vs F2FS, 16 vs 32 cores).

**Effort.** ≈ 4 person-days + ≈ 15 machine-hours (CPU only, no GPU), ≈ 200 GB scratch disk.

**Level: M.** Not H because: no plotting/analysis code for any figure or table in the repo; no
baseline runner for the vanilla arm; machine-specific paths throughout; paper-scale 12/24 h results
are out of disk reach so only the 3 h ablation is reproducible at paper scale; no artifact
badge or reproducibility report found. Not L because: the build is a single `make` target with no
exotic dependencies, the ablation flag and every controller constant are already exposed on the
command line, the workload generator is in-tree, and all raw quantities the paper plots are already
emitted as CSV columns.

---

## 5. Add-on ideas

### A1 — End-to-end admission latency: does the tail improvement survive honest accounting?

> **Hypothesis.** We hypothesize that measuring Put latency at the client (including the ingress
> rate-limiter wait) erases most of S-RocksDB's reported P99.99/P99.999 advantage over vanilla
> RocksDB at matched offered load, and that replacing the burst-refill rate limiter with a
> delay-target pacer (admission that regulates *queueing delay* rather than *rate*) restores a
> genuine end-to-end tail-latency improvement under sustained `fillrandom` and YCSB-A.

- **mechanism.** (i) Instrument `WriterThread` with the per-op histogram machinery that already
  exists for the YCSB path (`RecordYcsbLogicalOpLatencyUs`), so the `fillrandom` microbenchmark
  reports client-observed P99…P99.999 alongside the `DB_WRITE` numbers. (ii) Add a
  `DB_WRITE_E2E`-style measurement by moving/duplicating the StopWatch above the throttle call.
  (iii) Replace the actuator: instead of `SetBytesPerSecond(base·m)` on a `GenericRateLimiter` with
  a 100 ms refill period (`db/db_impl/db_impl.cc:280-283`), pace each write batch with a smooth
  token bucket and export the achieved queueing delay as a new controller signal; then change the
  SAFE-region reward (`agent_rl_fifo.py:1512-1536`) to penalize measured admission delay instead of
  only ΔP99 of `DB_WRITE`.
- **code_locations.** `db/db_impl/db_impl_write.cc:495`, `db/db_impl/db_impl.cc:807`,
  `db/db_impl/db_impl.cc:278`, `srocksdb_src/rl_poller.cc:918`, `srocksdb_src/agent_rl_fifo.py:1512`
- **motivating_evidence.** `db_impl_write.cc:498` (throttle) precedes `db_impl_write.cc:556`
  (`StopWatch … DB_WRITE`), while RocksDB's native stall wait occurs inside `PreprocessWrite`
  (`db_impl_write.cc:1498`) and is therefore counted. The paper's Figure 11 / Table 2 percentiles
  come from that histogram (`db_impl.cc:904-913`). §6.2 concedes S-RocksDB "trades transient
  throughput peaks" but never accounts for where the traded time goes from the client's view.
- **feasibility: H.** Instrumentation is ~100 LOC reusing the existing histogram helpers; the pacer
  is a localized change to one function; evaluable with the existing runners on 3-hour runs. Well
  within 2–4 students × 10 weeks.
- **research_value: H.** This is a soundness question about the paper's headline claim, and both
  outcomes are informative: if the end-to-end tail still wins, the result is *stronger* than the
  paper shows; if it does not, the community learns that admission control relocates rather than
  removes the wait, and the delay-target variant is the fix. A VLDB reviewer would ask exactly this.
- **scoop_check.** `result: partial`. Queries: "LSM-tree write stall admission control
  client-observed tail latency rate limiting 2026"; "CruiseDB admission control LSM-tree SLA write
  stall tail latency". Closest work: [CruiseDB (ICDE 2021)](https://ieeexplore.ieee.org/document/9458700/),
  an SLA-oriented RocksDB extension that "adaptively admits only an appropriate number of user
  requests … in unit time" with explicit latency SLA targets — the same family of idea, applied to
  a different controller, and notably *not cited by this paper*. Also
  [RaKV (TACO 2025)](https://dl.acm.org/doi/full/10.1145/3774424) uses token-bucket admission for
  cloud-block-storage SLAs (cited as [61]). Neither audits S-RocksDB's measurement boundary, and
  no work found does the specific end-to-end-vs-internal comparison.

### A2 — Does the Q-learner beat a controller that simply measures the drain rate?

> **Hypothesis.** We hypothesize that a non-learned controller that directly estimates
> `B_int(t) = B_f(t) + B_c(t)` from RocksDB's flush/compaction byte counters and sets
> `m_t = (B_int(t) − k·backlog_error)/base_rate` achieves throughput within 5% of the SAFE-region
> Q-learner at equal or fewer stalled writes, on the same 3-hour `fillrandom` and on the
> time-varying workload — i.e. that the paper's gain comes from the SEMI-SAFE guardrail and the
> admission abstraction, not from reinforcement learning.

- **mechanism.** Export `COMPACT_WRITE_BYTES`, `FLUSH_WRITE_BYTES` (and their per-epoch deltas) as
  new columns of `rl_metrics.csv` from the poller's statistics read (the `WRITE_STALL` histogram is
  already read the same way). Add a `CAPACITY` controller mode alongside `RL_DELTA_M`/`PID`/`AIMD`,
  reusing the existing dispatch and the identical SAFE/SEMI-SAFE/UNSAFE state machine so only the
  SAFE-region policy differs. Run head-to-head with the unchanged runners.
- **code_locations.** `srocksdb_src/rl_poller.cc:1654`, `srocksdb_src/agent_rl_fifo.py:1411`,
  `srocksdb_src/agent_rl_fifo.py:616`, `srocksdb_scripts/run_agent_pid_backlog.sh`
- **motivating_evidence.** §4.1 states outright: "In S-RocksDB, we do not require direct estimation
  of `B_f(t)` or `B_c(t)`" — yet the entire model (Eq. 3–4) is written in those terms, and the
  signals are available for free from RocksDB statistics. The two heuristic baselines in Table 3
  are both *pressure*-driven (PID on backlog target, AIMD on stall events); neither observes the
  actual drain bandwidth, so the paper's "heuristics are insufficient" argument has a gap. Table 4
  further shows that removing SEMI-SAFE alone inflates stalls by 70,000×, suggesting the guardrail,
  not the learner, carries most of the benefit.
- **feasibility: H.** Two new CSV columns plus one new controller branch (~250 LOC total), no
  changes to the RocksDB core, evaluated with the existing 3-hour harness on this machine.
- **research_value: M.** A strengthened baseline and a clean "is the RL load-bearing?" ablation —
  genuinely useful, but Table 3's PID/AIMD comparison already occupies part of this ground, and a
  well-tuned closed-loop estimator performing comparably is a plausible-but-unsurprising outcome.
- **scoop_check.** `result: clear`. Queries: "estimate compaction drain bandwidth feedback
  controller admission rate LSM write stall RocksDB"; "multi-tenant RocksDB per-tenant write
  admission control fairness compaction backlog 2025 2026". Related but different:
  [RBC / bandwidth-aware SSD contention control] and
  [FlexEngine (PACMMOD 2025)](https://doi.org/10.1145/3786667), which does two-level I/O admission
  control for multi-tenant serverless RocksDB but targets bandwidth over-subscription across
  partitions, not a single-instance drain-rate estimator compared against RL.

### A3 — Burst/idle workloads: the unexplored regime for a conservative equilibrium controller

> **Hypothesis.** We hypothesize that under on/off bursty offered load (duty cycles of 10–50% with
> idle gaps of 30–300 s), S-RocksDB's learned equilibrium multiplier leaves the device idle during
> burst arrivals and therefore *increases* burst completion time relative to vanilla RocksDB at the
> same stall budget, and that adding a "drain credit" — permitting `m > m_learned` while backlog and
> L0 are near zero, repaid when pressure rises — recovers burst completion time without increasing
> stalled writes.

- **mechanism.** Add burst parameters to the `fillrandom` driver (`--burst_period_sec`,
  `--burst_duty`, `--burst_rate_mb_per_sec`) so the offered rate is a square wave rather than the
  constant pacing at `srocksdb_src/rl_poller.cc:949-958`. Add a credit accumulator to the
  controller: track backlog-below-threshold time, allow `m_cap = m_learned + credit` in SAFE, and
  decay credit as backlog rises. Report burst completion time and per-burst P99.9 as new metrics.
- **code_locations.** `srocksdb_src/rl_poller.cc:918`, `srocksdb_src/agent_rl_fifo.py:1470`,
  `srocksdb_src/agent_rl_fifo.py:421`, `srocksdb_scripts/run_agent_rl_LQ_timevarying.sh`
- **motivating_evidence.** Every microbenchmark in §6.2 is a *constant* open-loop rate, and the only
  dynamic experiment (§6.5, Figure 15) is three 3-hour phases — far coarser than real burst
  timescales. §6.4 already observes the failure mode in a mild form: on YCSB A and F "S-RocksDB
  shows comparable or slightly lower throughput … the controller adopts conservative admission".
  §5.2 caps `m_max = 0.5` explicitly "to restrict aggressive admission during long-run training",
  and Figure 13b shows `m` settling into a narrow 0.01–0.2 band — precisely the behaviour that would
  waste idle capacity. The reward (Eq. 16) has no term for unused capacity.
- **feasibility: M.** Needs a new workload generator mode *and* a new metric (burst completion time)
  *and* a controller change; the evaluation is a new sweep over duty cycles. Each configuration is
  short (bursty runs write far less data, so disk is not a constraint), but it is a cross-cutting
  change rather than a localized one.
- **research_value: H.** Bursty, diurnal ingest is the dominant real-world pattern for the
  microservice/AI-serving backends the introduction invokes, and it is exactly the regime where an
  equilibrium-seeking admission controller is most suspect. Either outcome is publishable: it either
  extends the paper's claim to a regime it never tested, or identifies a real limit of the design.
- **scoop_check.** `result: clear`. Query: "bursty write workload LSM-tree idle time compaction
  scheduling burst completion time key-value store 2025". Nearest work is compaction-side
  (SILK's use of idle periods for compaction scheduling, STEM's pipelined compaction,
  [a 2025 LSM survey](https://arxiv.org/pdf/2507.09642) noting "cumulative bursty compaction");
  nothing found regulates *admission* with an idle-earned credit, and no follow-up to this paper
  exists yet.

### A4 — Cold start: the policy is thrown away after every run, and ε never decays to zero

> **Hypothesis.** We hypothesize that persisting the learned Q weights across runs (warm start) and
> annealing ε from 0.25 to ~0 after convergence reduces time-to-sustainable-rate and raises
> first-hour throughput by ≥10% at equal or fewer stalled writes, relative to the shipped cold-start
> configuration, on 3-hour `fillrandom` and on the YCSB load phase.

- **mechanism.** Serialize `LinearQAgent.W` to disk on a timer and at shutdown; add `--rl_load_policy`
  to restore it. Extend the ε schedule (currently: `args.rl_exploration_epsilon` for the first 180 s,
  then a hard-coded 0.1 forever) with a proper decay to a small floor, gated on TD-error stability.
  Measure the transient explicitly: time until `m` first reaches 90% of its stabilized band,
  cumulative bytes admitted in the first hour, and stalls during the transient.
- **code_locations.** `srocksdb_src/agent_rl_fifo.py:231`, `srocksdb_src/agent_rl_fifo.py:814`,
  `srocksdb_src/agent_rl_fifo.py:1211`, `srocksdb_scripts/run_agent_fifo.sh:60`
- **motivating_evidence.** `LinearQAgent.W` is zero-initialized at `agent_rl_fifo.py:247`/`:814` and
  never written to disk; the only checkpointing code (`OnlineLearner.ckpt_dir`,
  `agent_rl_fifo.py:194`) belongs to a different, *disabled* learner
  (`RL_ONLINE_LEARNING_ENABLED=0`, `run_agent_fifo.sh:60`, and `run_agent_rl_LQ.sh` never enables it).
  So every experiment in the paper relearns from scratch. Separately, `agent_rl_fifo.py:1211-1216`
  pins ε at 0.1 for the entire remaining run unless the schedule is `constant` — a permanent 10%
  random-action rate over an action set of ±0.02, which the paper does not discuss. Figure 13a shows
  TD error "initially elevated", and §6.4 attributes low YCSB A/F write throughput to early
  conservatism — both consistent with a cold-start cost.
- **feasibility: H.** `np.save`/`np.load` plus a schedule change; ~100 LOC, no RocksDB changes,
  measurable with the existing harness. The transient is short, so experiments are cheap.
- **research_value: M.** Warm-starting a linear policy helping is an expected result, and the gain
  is confined to the transient. What raises it above L is that the permanent ε=0.1 floor is an
  undocumented design choice that plausibly costs steady-state throughput too, which makes the
  ablation a real (if narrow) correction to the paper.
- **scoop_check.** `result: clear`. Queries: "S-RocksDB Sustainable RocksDB write stall admission
  control reinforcement learning VLDB 2026"; "reinforcement learning storage controller warm start
  policy persistence". No citing or follow-up work found — the paper is from PVLDB Vol 19 (2026) and
  the repository has 2 stars and 0 forks, so no third party has built on it yet.

### A5 — A write-only controller in a read-write world

> **Hypothesis.** We hypothesize that adding read-side signals (read P99 and L0 file count as an
> explicit read-amplification penalty) to the state vector and reward lets S-RocksDB reduce read
> P99/P99.9 by ≥20% under YCSB-A and YCSB-F at equal write throughput, compared with the shipped
> write-only controller.

- **mechanism.** Split the poller's single YCSB latency histogram into per-op-type histograms
  (read / write / scan) and export read percentiles as `rl_metrics.csv` columns. Extend `make_state`
  with normalized read-P99 and read-amplification proxies, and add a read-latency penalty term to
  the reward alongside the existing backlog/ΔP99 terms. Evaluate on YCSB A/F and on `r50w50`.
- **code_locations.** `srocksdb_src/rl_poller.cc:686`, `srocksdb_src/rl_poller.cc:1671`,
  `srocksdb_src/agent_rl_fifo.py:421`, `srocksdb_src/agent_rl_fifo.py:1522`
- **motivating_evidence.** The 12-dim state (Eq. 12, implemented at `agent_rl_fifo.py:468-484`)
  contains no read metric whatsoever, and the reward (`:1522-1536`) penalizes only write-path ΔP99
  and backlog. The paper's own read-side gains in §6.4 (209K vs 68K ops/s on YCSB-C) are an
  *incidental* consequence of ending the load phase with zero L0 files — never an optimization
  target. `RecordYcsbLogicalOpLatencyUs` (`rl_poller.cc:686`) aggregates reads and writes into a
  single histogram, so the artifact cannot currently even report read tail latency separately.
- **feasibility: M.** Requires poller changes (per-op histograms), controller changes (state and
  reward), and a YCSB-based evaluation whose load phase (`LOAD_RECORD_COUNT=50000000` ≈ 50 GB)
  must be re-run per configuration — several hours per point, but well within our disk and time
  budget. Cross-cutting rather than localized.
- **research_value: M.** A natural and defensible extension that broadens the controller from
  write-stall avoidance to read/write SLA balancing, but the direction of the result (admitting
  fewer writes helps reads) is largely predictable; the interesting part is the achievable
  Pareto frontier rather than the existence of the trade-off.
- **scoop_check.** `result: partial`. Queries: "LSM-tree read tail latency admission control
  read-write trade-off reinforcement learning"; "CruiseDB admission control LSM-tree SLA".
  [CruiseDB (ICDE 2021)](https://ieeexplore.ieee.org/document/9458700/) already optimizes admission
  against combined read/write SLA objectives, and
  [vLSM (arXiv 2407.15581)](https://arxiv.org/pdf/2407.15581) targets read tail latency structurally
  — but neither does read-aware *learned* admission inside the SAFE/SEMI-SAFE/UNSAFE framework, and
  neither is a follow-up to this paper.

---

## 6. Risks and open questions

1. **Disk is the binding constraint.** `fillrandom` with random int32 keys grows the DB
   monotonically (`srocksdb_src/rl_poller.cc:925-935`); a 12 h or 24 h paper-scale run needs
   0.8–1.3 TB against ~257 GB free. Any experiment longer than ~4 h must use the bounded-keyspace
   YCSB modes. Teams that copy the paper's run lengths verbatim will fill the shared `/home`
   partition — a real operational hazard.
2. **The reported tail latency excludes the controller's own delay** (see §2.7). Anyone reproducing
   Figure 11 will get S-RocksDB's numbers "for free" without learning what the client experiences.
   Treat this as the primary validity question, not a detail.
3. **Absolute numbers will not transfer.** SATA 870 EVO + F2FS + 2×Xeon 6338 (32 cores) vs our
   NVMe PM9A3 + ext4 + 16-core Threadripper. The paper's own Table 2 shows the sustainable rate
   moves with the device, so expect different MB/s; only the *ordering* and the stall-count
   order-of-magnitude should be treated as reproducible.
4. **No plotting or analysis code at all.** Every figure and table must be re-derived from the CSVs.
   Budget for it explicitly; it is the single largest unlisted cost in the artifact.
5. **Single-threaded offered load.** `WriterThread` is one thread (`rl_poller.cc:918`, started once
   at `:1495`), and YCSB is likewise single-threaded (`:1490`). The entire evaluation therefore has
   exactly one concurrent writer. Whether the shared `GenericRateLimiter` actuator behaves sanely
   under 8–32 concurrent writers is untested and unknown; this makes multi-writer experiments
   attractive but also means a team may hit undiscovered behaviour. (Note that per-tenant fairness
   in RocksDB is partly occupied ground — FlexEngine, FAIRDB — so frame it as a mechanism question,
   not a fairness paper.)
6. **Repository maturity.** 2 stars, 0 forks, created 2026-02-27, last push 2026-05-31, no issues,
   no tests for the controller, no CI for the S-RocksDB paths. No artifact-evaluation badge or
   reproducibility report was found for PVLDB Vol 19; only the paper's own availability statement.
7. **`ulimit -n 1048576` under `set -e`** in `run_sensitivity_3h.sh:4` will abort the sensitivity
   sweep if the user's hard `nofile` limit is lower. One-line fix, but it will look like a build
   failure if unanticipated.
8. **Reproducing the SILK/ADOC comparisons is out of scope** for a 10-week project: SILK is
   RocksDB 5.7.0 and ADOC is 7.7.0, both external, both with their own build stacks. Any add-on
   should be framed against vanilla RocksDB 10.6.0 and against S-RocksDB's own PID/AIMD modes,
   all of which live in this one tree.

---

## 7. Evidence index

**Paper.**
§2.1–2.3 (write path, threshold safeguards, rate limiting) · §3.1 + Figure 2 (limit-cycle,
1.36M stalls/30 min) · §3.2 + Figure 3a/3b (static rate limits, 1.25M stalls, 100 MB/s→0.85M) ·
§4.1 Eq. 3–4 (`B_int`, pressure dynamics) and the "we do not require direct estimation" statement ·
§4.2 (stalled-writes metric) · §4.4 Eq. 5–8 (multiplier, clipping, Δm cap) · §5 (control design),
§5.2 (m_min=0.01, m_max=0.5, Δm_max=0.02), §5.3.1–5.3.3 (UNSAFE/SEMI-SAFE/startup guard),
§5.4 Eq. 9–11, §5.5.1 Eq. 12 (12-dim state), §5.5.2 Eq. 13–14 + training gate,
§5.6 Eq. 15–16 (reward constants), §5.7 (parameter roles) ·
§6.1 + Table 1 (hardware, five variants, versions) · §6.2 + Figures 8, 9, 10, 11, 12 (24 h results,
stall counts 64.3M/555.3M/142.9M → 10,206/69, tail latency, CPU/memory) · §6.3 + Figure 13a/13b
(TD error, m trajectory, 0.4% CPU) · §6.4 + Figure 14a/14b (YCSB load-phase backlog, A–F throughput) ·
§6.5 + Figure 15 + Table 2 (time-varying workload, three hardware setups, `write_mb_per_sec`
normalization) · §6.6 + Table 3 (PID/AIMD/Q-learning) + Table 4 (SEMI-SAFE ablation) ·
§6.7 + Figure 16 (Pareto sensitivity) · §6.8 (portability sketch) · §7 (related work) ·
p. 1 PVLDB Artifact Availability statement.
Page images read: `pages/page-09.png` (Figures 10–13), `pages/page-11.png` (Tables 3–4, Figure 16).

**Repository.**
`README.md` (layout, build, requirements, runner defaults, DB_PATH warning) ·
`Makefile:644`, `Makefile:781`, `Makefile:1345` (`rl_poller` target) ·
`db/db_impl/db_impl.cc:278-284` (ingress limiter creation), `:784-824` (`IsRLMetricsEnabled`,
`MaybeRecordWriteIngressBytes`, `MaybeThrottleWriteIngress`), `:827-980` (metrics sampler),
`:900-913` (DB_WRITE percentiles), `:1504-1531` + `:1681-1683` (`rl_write_multiplier` SetDBOptions
hook), `:4770-4857` (`SetWriteIngressMultiplier`, clamp/slew/emergency, `SetBytesPerSecond`) ·
`db/db_impl/db_impl_write.cc:370` (`WriteImpl` entry), `:495-499` (throttle call), `:556`
(`StopWatch … DB_WRITE`), `:1498` (`PreprocessWrite`) ·
`db/db_impl/db_impl.h:2392-2395`, `:2953`, `:2967` ·
`monitoring/histogram.cc:236-238`, `monitoring/statistics.cc:541-542` (added percentiles) ·
`include/rocksdb/options.h`, `options/db_options.{h,cc}`, `options/options_helper.cc` (new rl_* options) ·
`srocksdb_src/rl_poller.cc:94-168` (stall stat extraction), `:513` (FIFO command thread), `:727-758`
(value generator), `:686-723` (YCSB latency histogram), `:918-978` (`WriterThread`), `:1010-1227`
(`YcsbThread`, workloads A–F and r10w90/r90w10/r50w50), `:1229-1330` (CLI), `:1446-1473` (CSV header),
`:1654-1669` (`WRITE_STALL` histogram count) ·
`srocksdb_src/agent_rl_fifo.py:1-16` (self-audit docstring), `:47-76` (defaults, metrics header),
`:102-228` (unused `OnlineLearner` + checkpointing), `:231-272` (`LinearQAgent`), `:421-487`
(`make_state`, Eq. 12), `:540-578` (FIFO writer), `:616-617` (controller modes), `:814-824` (agent
init, zeroed W), `:1101-1233` (stall detection, near-stall triggers, ε schedule), `:1242-1323`
(SEMI-SAFE latch / hard lock / FSM), `:1338-1351` (TD update), `:1383-1391` (training gate),
`:1392-1506` (state-dependent policies + overrides), `:1512-1553` (reward, transition storage),
`:1562-1599` (FIFO send-on-change) ·
`srocksdb_options/rl_options_r.ini`, `srocksdb_options/rl_options_s.ini` (the R and S presets of
Table 1) ·
`srocksdb_scripts/run_agent_fifo.sh` (full launcher; `:60` online learning off, `:113` outdir,
`:307-311` soft-guard flags, `:392-446` resource monitor, `:526-528` option upsert, `:551` poller
launch, `:660` agent launch) ·
`srocksdb_scripts/run_agent_rl_LQ.sh` (`:14` 12 h default, `:20` F2FS path, `:28` NVMe 3000 MB/s,
`:36-43` R vs S presets, `:46-95` controller defaults matching §5, `:97` empty SUDO_CMD,
`:133-148` DB cleanup) ·
`srocksdb_scripts/run_agent_rl_ycsb.sh:13-22` (50M records, 1 h run phase) ·
`srocksdb_scripts/run_sensitivity_3h.sh:4` (`ulimit -n`), `:11` (3 h), `:85-120` (15 cases) ·
`srocksdb_scripts/run_agent_rl_LQ_timevarying.sh`, `run_agent_pid_backlog.sh`,
`run_agent_pid_l0.sh`, `run_agent_aimd_stall_only.sh` ·
`repo_facts.json` (head commit 2026-05-31, 2 stars/0 forks, red-flag hits all in upstream CI) ·
`fetch_result.json`.

**Web (scoop check only).**
[CruiseDB, ICDE 2021](https://ieeexplore.ieee.org/document/9458700/) ·
[RaKV, ACM TACO](https://dl.acm.org/doi/full/10.1145/3774424) ·
[FlexEngine, PACMMOD 2025](https://doi.org/10.1145/3786667) ·
[Delta Fair Sharing / FAIRDB](https://arxiv.org/pdf/2601.20030) ·
[vLSM](https://arxiv.org/pdf/2407.15581) ·
[Rethinking LSM-tree based Key-Value Stores: A Survey](https://arxiv.org/pdf/2507.09642).
No paper citing or extending S-RocksDB was found.
