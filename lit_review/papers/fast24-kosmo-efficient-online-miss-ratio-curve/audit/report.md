# Kosmo: Efficient Online Miss Ratio Curve Generation for Eviction Policy Evaluation

FAST '24 · Kia Shakiba, Sari Sultan, Michael Stumm (University of Toronto)
Repo: https://github.com/Stumm-Lab/kosmo-fast24 (HEAD 48a843d, 2025-05-11)
Desk review only — nothing was built or run.

## 1. Paper summary

**Problem.** A miss ratio curve (MRC) plots miss ratio vs. cache size and is the main
tool for sizing an in-memory cache (§1, Fig. 1). Almost every MRC algorithm (Mattson,
Olken, PARDA, SHARDS) assumes the *inclusion property* and therefore only models LRU-like
policies (§2.2). The one general method, Waldspurger's **Miniature Simulations (MiniSim)**,
runs `N_C` (typically 100) independent scaled-down cache simulations; because the
simulations share nothing, the same object is stored 100× and memory blows up — measured
averages of 113 MiB (LFU), 57 MiB (FIFO), 40 MiB (2Q), 31 MiB (LRFU), up to 3.1 GiB (§1,
§2.3). That precludes running it *online*, next to the production cache. A second MiniSim
drawback: `C_max` must be fixed before the trace starts, so cache sizes cannot be focused
on the actual working set (§2.3, footnote 3).

**Key idea.** Kosmo keeps **one** copy of each object in a *global table*, and attaches to
it a policy-specific **eviction map**: a small sorted list of *eviction records* recording
"object was evicted from the cache of size S, and here is the policy state at that point"
(§3.1). From the eviction map, Kosmo can (i) find the smallest cache size that still holds
the object — its reuse distance, (ii) compute the object's sorting key *as it would be* in
a cache of any size S, and (iii) insert a new eviction record. On each access Kosmo
increments a reuse-distance histogram (Mattson-style) and then *reconstructs* the stacks of
the caches smaller than the reuse distance to decide who gets evicted (§3.2). The MRC is
the inverse CDF of the histogram.

**Design details.** Four optimizations make this tractable (§3.3): a *granularity* parameter
`G` bounding the number of stacks reconstructed per access (G = 10 chosen from Fig. 3);
*eviction-record pruning* (on evicting at size S, drop all records with S' < S — assumes the
non-strict inclusion property; reduces eviction-map size ~387×, Fig. 4); *SHARDS* spatial
sampling (fixed-rate R and fixed-size S_max, the latter bounding the global table); and
*parallel stack reconstruction* via a thread pool. Eviction maps are given for LFU (§3.4),
FIFO, 2Q, LRFU, LRU, MRU (§3.5), plus variable object sizes (§3.6), TTLs (§3.7) and
simultaneous multi-policy generation (§3.8). Footnote 6 says an S3-FIFO eviction map was
also built but is omitted for space.

**Evaluation.** 52 public traces / ~126 B accesses: MSR (13 traces, 434 M accesses),
Twitter cache-trace (24), SEC EDGAR (15) — Table 2, §4. Baseline is the authors'
re-implementation of MiniSim with 100 simulated caches, extended to fixed-size SHARDS
(§4.1). Three SHARDS configs: fixed-rate R = 0.001, fixed-size S_max ∈ {1024, 2048}.
Metrics: peak memory (`VmHWM`), throughput (accesses/ms, IO excluded), and MAE against a
"accurate" MRC obtained by 100 *full* cache simulations per trace per policy (§4.3).
Machine: Threadripper 3990X, 64 cores, 256 GB (§4.2).

**Headline numbers.** Kosmo uses **3.6× less memory** on average (up to 36×) — Fig. 6;
**1.3× higher throughput** on average — Fig. 7 (but 0.54× on 2Q, because two stacks are
rebuilt per access); MAE within 0.25% of MiniSim on average — Fig. 8. Kosmo's **CPU time
per access is 1.85–2× *higher*** than MiniSim's (Fig. 9) — the throughput win comes from
better thread utilization, not less work. §4.5 measures inclusion-property violations:
LFU 1.49%, FIFO 20.61%, 2Q 10.49%, LRFU 0.08%, MRU 29.12% of accesses (100 sizes).

**Stated limitations** (§1, "Limitations"). Only six policies described; which *classes*
of policies eviction maps can express is open. The MRCs are monotonically decreasing by
construction, which inflates error for policies with non-monotonic behaviour. MiniSim's
performance depends on the underlying cache implementation. Future work (§6): ARC, LIRS,
LHD eviction maps; lower CPU overhead via specialized data structures.

## 2. Artifact audit

**Structure.** 46 files, 5,103 lines of Rust, one crate, three binaries. Top level is only
`Cargo.toml`, `LICENSE`, `README.md`, `src/`, `traces/`. There are **no shell/Python
scripts, no Makefile, no CI, no plotting scripts, no trace converter** — the repo is the
algorithm plus a CLI.

| paper component | code path |
|---|---|
| Kosmo algorithm (§3.2), granularity G (§3.3), parallel reconstruction | `src/kosmo.rs` (`GRANULARITY = 10` at `src/kosmo.rs:35`; `perform_evictions` `:175–206`; `reconstruct_policy_stacks` `:219–234`) |
| Eviction map abstraction — 3 ops of §3.1 (`insert` / `reuse_distance` / `as_local_object`) | `src/kosmo/eviction_map.rs:32–41` |
| LFU eviction map (§3.4, Alg. 1) | `src/kosmo/eviction_map/lfu_eviction_map.rs` |
| FIFO eviction map (§3.5, Alg. 2) incl. pruning | `src/kosmo/eviction_map/fifo_eviction_map.rs` (pruning loop `:37–45`) |
| 2Q (Alg. 3), LRFU, LRU eviction maps | `src/kosmo/eviction_map/{two_q,lrfu,lru}_eviction_map.rs` |
| Global table entry / per-policy maps (§3.8) | `src/kosmo/global_object.rs` |
| Stack reconstruction + sorting keys | `src/kosmo/reconstructed_stack.rs` + `reconstructed_stack/*.rs`, `src/kosmo/local_object*.rs` |
| Reuse-distance histogram (§2.3) | `src/histogram.rs` (64 KiB buckets, `BUCKET_SIZE` `:11`) |
| Histogram → MRC (inverse CDF ⇒ monotone) | `src/curve.rs:62–115`; MAE at `src/curve.rs:171–189` |
| SHARDS fixed-rate / fixed-size (§2.3) | `src/shards.rs`, `src/shards/fixed_rate.rs`, `src/shards/fixed_size.rs` |
| MiniSim baseline, `N_C = 100`, fixed-size rescaling (§4.1) | `src/minisimulations.rs` (`NUM_CACHES = 100` `:18`; `rescale` `:130–150`) |
| Real cache implementations for MiniSim + ground truth | `src/cache.rs`, `src/cache/{lfu,fifo,two_q,lrfu,lru}_cache.rs` |
| `wss` / `accurate` / `mrc` tools (Artifact Appendix) | `src/wss.rs`, `src/accurate.rs`, `src/mrc.rs` |
| Memory HWM + throughput measurement (§4.3) | `src/mrc.rs:104–107, 159–178` (kwik `sys::mem::clear`/`hwm`) |

**Gaps vs. the paper.** MRU (§3.5) and S3-FIFO (footnote 6) are **not in the repo** — grep
for `mru|S3|Sieve|Arc` in `src/` returns nothing; `KosmoPolicy` (`src/kosmo/policy.rs:20`)
has only Lfu/Fifo/TwoQ/Lrfu/Lru. TTL support (§3.7) is **not implemented**: `Access.ttl`
is parsed (`src/access.rs:58`) and then never read by any algorithm. Simultaneous
multi-policy generation (§3.8) *is* implemented inside `Kosmo` (`policies: Vec<KosmoPolicy>`,
`src/kosmo.rs:43`) but the CLI refuses more than one policy and panics if both Kosmo and
MiniSim are requested (`src/mrc.rs:90`), so the paper's flagship "simultaneous" capability
is unreachable from the shipped tool and is never measured in §4. `Algorithm::resize` and
`Algorithm::clean` (`src/algorithm.rs:33–35`), the hooks that would make Kosmo *online*
(windowed histograms, shrinking the global table), are implemented in `src/kosmo.rs:74–81`
but called from nowhere.

**Build route on this machine.** `cargo build -r`. Requirements and their risks:
- `edition = "2024"` (`Cargo.toml:4`) plus `#![feature(btree_cursors)]` (`src/mrc.rs:8`,
  `src/accurate.rs:8`) ⇒ a **Rust nightly ≥ 1.85**. Rust is not installed but rustup
  installs entirely into `$HOME` — fine, no root.
- `fasthash = "0.4.0"` (`Cargo.toml:9`), used only for `murmur3::hash128` in
  `src/shards.rs:11,55`. fasthash 0.4.0 is an unmaintained 2019 crate whose `fasthash-sys`
  build compiles C++ through bindgen and needs **libclang**, which is not installed on this
  machine (conda `clang`/`libclang` + `LIBCLANG_PATH` is the user-space route). Fallback if
  it will not compile on a 2025 nightly: swap in a pure-Rust murmur3 crate — a two-line
  change in `src/shards.rs`; note this perturbs SHARDS sampling decisions, so numbers would
  be statistically rather than bit-wise comparable.
- `kwik` is pulled from git at tag `v1.16.5` (`Cargo.toml:11`) — needs network at build
  time; it supplies the binary trace reader, the progress bar, the gnuplot wrapper, and the
  `VmHWM` reader.
- `gnuplot v5.4` is required for plotting (README "Dependencies"); conda-installable, and
  only needed for the per-run PDF, not for the numbers.
- Pins are current as of the 2025-05-11 HEAD (`rayon 1.10`, `clap 4.5.38`, `serde 1.0.219`,
  `rustc-hash 2.1.1`); `fasthash` is the only stale one.

**Data.** The tools read a custom **25-byte little-endian record** (timestamp u64, command
u8, key u64, size u32, ttl u32) — README "Access Trace", `src/access.rs:40–73`. The repo
ships exactly one trace, `traces/wdev.bin` (MSR wdev, ~31 MB ≈ 1.27 M records). Source
datasets are public — MSR Cambridge (SNIA IOTTA registry, ref. [23]), Twitter cache-trace
(github.com/twitter/cache-trace, ref. [39]), SEC EDGAR logs (sec.gov, refs. [37,38]) — but
**no converter from any of those formats to the 25-byte binary is included**, so the team
must write one (~100 LOC). The README points the AE reviewers at a now-defunct VM for the
larger traces and the precomputed `accurate/` curves; those are not in the repo.

**Eval scripts.** Present only as documented single-run commands (README "Getting Started").
The per-trace sweep over 52 traces × 4 policies × 3 SHARDS configs, the aggregation, and the
box plots of Figs. 6–9 must all be rebuilt. Note also that the README's Claims section is
**stale**: it says 5× memory / 9× max / 1.2× throughput, whereas the camera-ready says
3.6× / 36× / 1.3× (§ Abstract).

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Artifact Appendix (paper p. 15, "Hosting") gives DOI 10.5281/zenodo.10569925; that Zenodo record is titled "Stumm-Lab/kosmo-fast24: FAST'24" by Kia Shakiba and links `github.com/Stumm-Lab/kosmo-fast24/tree/v1.0.0-fast24` — the org is the senior author's lab. The repo contains the real system: `src/kosmo.rs` + `src/kosmo/eviction_map/*` implement §3.1–3.5 verbatim (Algs. 1–3), `src/minisimulations.rs` the baseline, `src/accurate.rs` the ground truth. 5,103 LOC of Rust, MIT licensed, not a placeholder. |
| `H2_no_root` | **pass** | Pure user-space Rust CLI; `repo_facts.json` red-flag scan is empty. The only privileged-looking operation is `mem::clear(None)` at `src/mrc.rs:105`, which shells out `echo 1 > /proc/self/clear_refs`; `/proc/self/clear_refs` is writable by the process owner, and in any case that path is only taken for `-r memory` and can be replaced by sampling `VmHWM` externally. No kernel module, eBPF, perf counters, KVM, hugepages, Docker (no Dockerfile in the repo). |
| `H3_hardware_fit` | **pass** | CPU-only, single node, no GPU. Kosmo's own footprint is 1–100 MiB and MiniSim's peaks at ~3.1 GiB (§1, Fig. 6) — trivial against 125 GB RAM. Parallelism is rayon over ≤ `G`=10 reconstructed stacks (`src/kosmo.rs:186`), so 16 cores suffice (the paper notes Kosmo's performance saturates once the thread pool exceeds G, §4.2); MiniSim was tuned to #cores = 64 on the authors' box, so absolute MiniSim throughput will differ and the comparison must be re-run, not copied. The binding limit is **disk**: the README states the full corpus is "roughly 4 TiB", against ~257 GB free — so the 52-trace sweep is out and a subset is mandatory (see §4). |
| `H4_obtainable_deps_data` | **pass** | Deps are all user-space installable: rustup nightly into `$HOME`, conda gnuplot, conda clang/libclang for `fasthash`'s bindgen step. Traces are public and free: MSR Cambridge via SNIA IOTTA, Twitter cache-trace on GitHub/S3, SEC EDGAR logs on sec.gov; one MSR trace (`traces/wdev.bin`) ships pre-converted. No proprietary data. Caveat (porting work, not a blocker): the CSV→25-byte-binary converter is not shipped, and the `accurate/` reference curves referenced in the README live only on the retired AE VM. |

## 4. Reproduction plan

**Target.** Figure 6 (memory usage) and Figure 8 (MAE) for the **LFU** and **FIFO**
policies under fixed-size SHARDS `S_max = 2048`, restricted to the MSR dataset — i.e. the
claim "Kosmo uses ~3.6× less memory than MiniSim at comparable MAE" (§4.4, Abstract).
Smoke test first: the exact README commands on the bundled `traces/wdev.bin`
(`wss` must print `313344512`).

**Scale-down.** MSR only: 13 traces / 434 M accesses ≈ 11 GB in the binary format — 4% of
free disk, versus ~4 TiB for the full corpus. Drop Twitter and SEC entirely, or add at most
one small Twitter cluster. For the MAE numbers, `src/accurate.rs` re-reads the whole trace
once per simulated size (100 sizes, serial — `src/accurate.rs:71–96`), so restrict the
ground truth to the ~6 smallest MSR traces (wdev, web, ts, rsrch, hm, prn) and/or cut to 25
accurate points; the paper's own MAE definition resamples at 100 points
(`src/curve.rs:177`), so fewer ground-truth points changes the metric and must be reported
as such. Report memory/throughput as *ratios* Kosmo:MiniSim on our 16-core box, never as
absolute numbers against the paper's 64-core box.

**Steps.**
1. `rustup` nightly into `$HOME`; conda env with `gnuplot`, `clang`, `libclang`;
   `export LIBCLANG_PATH=...`; `cargo build -r`. If `fasthash` fails, swap
   `src/shards.rs:11,55` to a pure-Rust murmur3 and document it.
2. Run the four README commands on `traces/wdev.bin` end-to-end (wss → accurate → mrc
   Kosmo → mrc MiniSim). This alone validates the pipeline and gives one memory ratio.
3. Write the MSR blkparse-CSV → 25-byte-binary converter (timestamp, GET/READ flag, hashed
   LBA as u64 key, request size, ttl = 0), verify it reproduces `wdev.bin`'s WSS of
   313,344,512 bytes from the raw SNIA CSV — that is a free correctness check.
4. Convert the remaining MSR traces; run `wss` on each.
5. Run `accurate` for LFU and FIFO on the small subset (the long pole).
6. Sweep `mrc` for Kosmo and MiniSim × {LFU, FIFO} × {FR 0.001, FS 1024, FS 2048} ×
   traces, in both `-r memory` and `-r throughput` modes; scrape stdout into CSV.
7. Rebuild the Fig. 6/8 box plots (matplotlib) from the scraped CSV.

**Effort.** ≈ 5 person-days (1 toolchain, 1.5 converter + validation, 0.5 sweep driver,
1 plotting/analysis, 1 slack) + ≈ 150 CPU-hours wall, almost all in step 5. No GPU.

**Level: M.** The core system, the baseline, the ground-truth simulator and exact
single-run commands all ship, and the bundled `wdev.bin` makes a first result reachable in
day 1 — that argues for H. It is held to M by real porting work that is not optional: no
trace converter, no sweep driver, no aggregate plotting, no reference `accurate/` curves,
a stale `fasthash`/libclang dependency, and a hardware mismatch (16 vs 64 cores) that makes
the throughput claim of Fig. 7 only reproducible in spirit.

## 5. Add-on ideas

### A1 — Quantify (and share work across) simultaneous multi-policy MRC generation

- **Hypothesis.** We hypothesize that generating MRCs for *k* policies in one Kosmo pass
  costs sub-linearly in *k* (memory and CPU per access grow ≪ k×), so that at k = 4 Kosmo's
  memory advantage over *k* independent MiniSim instances exceeds the paper's single-policy
  3.6×, under the MSR and Twitter traces.
- **Mechanism.** Expose the already-existing `Vec<KosmoPolicy>` through the CLI (today
  `src/mrc.rs:90` panics on >1 policy and `init_kosmo` hard-wires `&[policy]` at
  `src/mrc.rs:201`); add a multi-policy MiniSim driver that instantiates k×100 caches as the
  honest baseline; then push shared work further — `reconstruct_policy_stacks`
  (`src/kosmo.rs:219`) already walks the global table once for all policies, but the
  per-access reuse distance, the step-size schedule and the eviction loop are still
  per-policy (`src/kosmo.rs:186–205`); unify them so the table is touched once per size and
  the k stacks are filled in one pass, and report the per-policy marginal cost.
- **code_locations.** `src/mrc.rs:90`, `src/kosmo.rs:186`, `src/kosmo/global_object.rs:43`,
  `src/minisimulations.rs:103`
- **Motivating evidence.** §3.8 is titled "Simultaneous MRC generation" and the abstract
  sells "simultaneous generation of MRCs for a variety of eviction policies", yet §4
  evaluates one policy at a time and the shipped tool forbids the multi-policy mode. §1
  asserts without measurement that MiniSim's memory "requirements are compounded" for
  multiple policies. This is the paper's central selling point, unquantified.
- **feasibility: H.** Bounded change (a few hundred LOC across two files), reuses the
  existing measurement harness and traces, runs on 16 cores.
- **research_value: M.** It validates rather than extends: a reviewer would expect Kosmo to
  win here, so the surprise budget is limited — unless the shared-work refactor turns the 2Q
  regression (0.54× MiniSim throughput, §4.4) into a win, which would be a genuine result.
- **scoop_check: clear.** Queries: *"papers citing Kosmo Shakiba FAST 2024 miss ratio
  curve 2025 2026"*, *"miss ratio curve 2025 non-stack eviction policy SIEVE S3-FIFO MRC
  generation algorithm online"*. Nothing measures multi-policy MRC cost. Closest: the
  authors' own PaperCache (HotStorage'25, https://dl.acm.org/doi/10.1145/3736548.3737836)
  *consumes* runtime MRCs to switch policies, but reports cache miss ratios, not MRC
  generator cost.

### A2 — Incremental stack reconstruction to cut Kosmo's CPU time per access

- **Hypothesis.** We hypothesize that replacing Kosmo's full global-table rescan with an
  incrementally maintained per-size ordered structure reduces CPU time per access by ≥ 2×
  at unchanged MAE and unchanged memory, under all four evaluated policies — closing the
  1.85–2× CPU gap the paper concedes to MiniSim.
- **Mechanism.** Today every sampled access rebuilds G stacks from scratch: the inner loop
  at `src/kosmo.rs:227–231` iterates *all* `S_max` global-table entries and re-derives each
  object's sorting key, i.e. O(G · S_max · log S_max) per access. Between two consecutive
  accesses only O(G) objects change state (the accessed object plus the evicted ones), so
  keep the G reconstructed stacks resident as order-statistic structures inside `Kosmo` and
  apply deltas — invalidating an object's cached sorting key only when its eviction map is
  mutated (`GlobalObject::evict_by_policy_index`, `src/kosmo/global_object.rs:58`, and
  `update`, `:50`). LFU/FIFO/LRU keys are stable between mutations; LRFU's CRF decays with
  time, so it needs a lazy re-keying rule — a good stress case for the idea.
- **code_locations.** `src/kosmo.rs:219`, `src/kosmo.rs:175`,
  `src/kosmo/reconstructed_stack.rs:22`, `src/kosmo/global_object.rs:58`,
  `src/kosmo/local_object.rs`
- **Motivating evidence.** §6: "We also plan to improve on Kosmo's throughput by reducing
  its computational overhead through the use of more specialized data structures."
  Figure 9: Kosmo's CPU time per access is ~1.85× (LFU) and ~2× (FIFO/2Q/LRFU) MiniSim's;
  §4.4 admits the throughput win comes from thread utilization, not less work — a fragile
  advantage on a 16-core machine, and exactly the property that matters for the paper's
  "online, next to the cache" pitch.
- **feasibility: M.** Cross-cutting: touches the stack trait, all five reconstructed-stack
  implementations, and the eviction loop; correctness must be pinned by diffing MRCs
  against the unmodified Kosmo bit-for-bit before any speedup is claimed. Evaluable with
  the existing harness; ~1–2k LOC. Real risk of subtle divergence on 2Q/LRFU.
- **research_value: H.** It attacks the system's one admitted weakness against its own
  baseline, is the authors' named future work, and a negative result ("the rescan is
  already cheap relative to eviction-map lookups; the bottleneck is elsewhere") is itself
  publishable insight about where Kosmo's time goes — the paper never profiles it.
- **scoop_check: partial.** Queries: *"LAShards Low-Overhead Self-Adaptive MRC Construction
  Non-Stack Algorithms IEEE Transactions on Computers 2025"*, *"Shakiba Stumm 2025 miss
  ratio curve cache sizing eviction map"*. Closest work: **LAShards**, IEEE TC 74(10):3490–
  3503, Oct 2025 (https://www.computer.org/csdl/journal/tc/2025/10/11087706/28xfc5EUReE) —
  reduces the memory/compute overhead of MRC construction for non-stack policies, but in
  the MiniSim/DFShards mini-cache lineage, not by changing Kosmo's stack reconstruction. Not
  the same mechanism; must be cited and, if the artifact is obtainable, compared against.

### A3 — Violation-aware pruning: bounded eviction-record retention for FIFO and 2Q

- **Hypothesis.** We hypothesize that retaining the k most recent sub-threshold eviction
  records instead of discarding all of them reduces Kosmo's MAE for FIFO and 2Q by a
  measurable margin (target: eliminating the +0.44% / +1.56% average MAE deficit vs.
  MiniSim) for a memory increase of < 2×, on the MSR traces where the inclusion property is
  violated most.
- **Mechanism.** `EvictionMap::insert` prunes unconditionally: the FIFO map pops every
  record with `size <= cache_size` (`src/kosmo/eviction_map/fifo_eviction_map.rs:37–45`),
  and the LFU/2Q maps do the equivalent. That hard-codes the assumption "evicted at S ⇒
  absent at every S' < S", which §4.5 shows is wrong for 20.6% of FIFO accesses and 10.5%
  of 2Q accesses. Replace the boolean `exists_at`/`reuse_distance` with a k-record window
  that can represent "present at S₁, absent at S₂ > S₁", and let
  `Curve::from_histogram` (`src/curve.rs:62`) emit a non-monotone curve when the windowed
  records say so. Sweep k ∈ {0,1,2,4,8} to trace the accuracy/memory frontier; k = 0 is the
  paper's design, which makes the ablation self-calibrating.
- **code_locations.** `src/kosmo/eviction_map/fifo_eviction_map.rs:30`,
  `src/kosmo/eviction_map/two_q_eviction_map.rs`,
  `src/kosmo/eviction_map/lfu_eviction_map.rs`, `src/kosmo/eviction_map.rs:32`,
  `src/curve.rs:62`
- **Motivating evidence.** Two of the paper's three stated limitations: "the MRCs Kosmo
  generates are monotonically decreasing which could increase the error for eviction
  policies which display significant non-monotonic behaviour", and §3.3's admission that
  pruning "may introduce inaccuracies for eviction policies which do not adhere to the
  inclusion property". §4.4 reports Kosmo *losing* to MiniSim on FIFO and 2Q MAE and
  attributes it precisely to these violations; the MSR `src1` trace is called out as
  pathological for 2Q. §4.5 quantifies the violation rates that this add-on would exploit.
- **feasibility: M.** The change is localized to the eviction maps and the curve builder,
  but it interacts with the pruning that made Kosmo memory-efficient in the first place
  (Fig. 4: pruning shrinks maps ~387×), so the memory metric must be re-measured, not
  assumed; and the MAE metric itself (`src/curve.rs:171`) needs ground truth from the
  expensive `accurate` tool. Fits the 10-week budget on the MSR subset.
- **research_value: H.** It converts a self-declared limitation into a measured
  accuracy/memory knob, and either outcome is informative: if k = 1 recovers most of the
  MAE gap cheaply, Kosmo strictly dominates MiniSim; if it does not, the paper's claim that
  violations are benign is confirmed with evidence the paper itself does not provide.
- **scoop_check: clear.** Queries: *"inclusion property violation miss ratio curve error
  non-monotonic FIFO 2Q approximation 2025"*, *"miss ratio curve generation ARC adaptive
  replacement cache non-stack algorithm 2025 simulation SHARDS"*. Related but different:
  survey/probabilistic MRC work (e.g. Beckmann & Sanchez's age-based probabilistic MRCs,
  paper ref. [61]) models non-inclusive policies analytically rather than repairing a
  pruning heuristic.

### A4 — An ARC eviction map: does the eviction-map abstraction cover self-tuning policies?

- **Hypothesis.** We hypothesize that ARC's self-tuning partition can be encoded in a
  Kosmo eviction map, yielding ARC MRCs with MAE comparable to MiniSim's (within ~2%) at
  lower memory, under the MSR traces — and that the *per-size* adaptation parameter, not the
  multi-stack structure, is the binding difficulty.
- **Mechanism.** Follow the 2Q template (`src/kosmo/eviction_map/two_q_eviction_map.rs`,
  which already juggles two record sets and the K_in/K_out ratios): ARC needs T1/T2 record
  sets plus the B1/B2 ghost lists, and crucially a *per-cache-size* target `p` that moves on
  every ghost hit. Since Kosmo never materializes a cache, `p(S)` must be reconstructed from
  the eviction records at size S — either carried in the records or recomputed during stack
  reconstruction. Add `KosmoPolicy::Arc` (`src/kosmo/policy.rs:20`), the matching local
  object and reconstructed stack, and — for ground truth and the MiniSim baseline — a real
  ARC cache under `src/cache/` wired into `CachePolicy` (`src/cache/policy.rs`).
- **code_locations.** `src/kosmo/policy.rs:20`, `src/kosmo/eviction_map.rs:43`,
  `src/kosmo/eviction_map/two_q_eviction_map.rs`, `src/kosmo/reconstructed_stack.rs:42`,
  `src/kosmo/local_object.rs`, `src/cache/policy.rs`, `src/cache.rs:114`
- **Motivating evidence.** §6 names ARC, LIRS and LHD as future work; §3.5 says "We believe
  a similar technique would work for other multi-stack eviction policies (e.g., ARC) and
  leave this for future work"; the Limitations paragraph says "it remains an open problem
  which classes of eviction policies Kosmo is able to support". ARC is the sharpest test
  because its behaviour at size S depends on a state variable that itself depends on S —
  something no existing eviction map carries. The repo confirms the gap: no ARC, no LIRS,
  and not even the MRU and S3-FIFO maps the paper describes.
- **feasibility: M.** Roughly 800–1,200 LOC across five files following an existing
  template, plus an ARC cache for ground truth, plus `accurate` runs. Doable by 2–4 students
  in 10 weeks, but the per-size `p` may force a design change rather than a new map — which
  is the interesting risk, not a fatal one (fallback: fixed-`p` ARC, i.e. a strict
  generalization of 2Q, which still answers the multi-stack question).
- **research_value: H.** It directly probes the paper's open problem about the expressive
  power of eviction maps; a negative result ("adaptive policies need per-size state that
  breaks the single-global-copy premise") delimits Kosmo's applicability and is exactly the
  kind of finding the FAST reviewers asked about.
- **scoop_check: clear.** Queries as in A3 plus *"Kosmo miss ratio curve eviction policy
  follow-up 2025 eviction maps ARC LIRS MRC generation"*. Nothing extends Kosmo to ARC;
  MiniSim can already simulate ARC by brute force (that is the baseline, not a scoop). Note
  **S3-FIFO is self-scooped** by the paper's footnote 6 ("We have also designed eviction maps
  to support the S3-FIFO eviction policy"), so pick ARC/LIRS over S3-FIFO; SIEVE (NSDI'24)
  is unclaimed and could be a cheap second policy.

### A5 — Workload-adaptive granularity: where to spend the G reconstructions

- **Hypothesis.** We hypothesize that placing Kosmo's G reconstruction points non-uniformly
  — log-spaced, or concentrated where the running reuse-distance histogram has mass —
  reduces worst-case MAE (the upper whisker of Fig. 3) by ≥ 30% at equal G, or reaches the
  paper's MAE at G = 5 instead of G = 10, on the MSR traces.
- **Mechanism.** `perform_evictions` derives a single uniform `step_size` from the accessed
  object's reuse distance (`src/kosmo.rs:176–180`) and reconstructs at
  `step_size, 2·step_size, …` (`src/kosmo.rs:186–189`), with `GRANULARITY` a compile-time
  constant (`src/kosmo.rs:35`). Replace the arithmetic schedule with a pluggable
  size-schedule trait: (a) geometric spacing, (b) histogram-guided spacing that samples the
  live `Histogram` (`src/histogram.rs`) so points cluster near cliffs, (c) a per-access
  budget that spends fewer reconstructions on small reuse distances and more on large ones.
  Measure MAE, CPU time per access and memory at matched G.
- **code_locations.** `src/kosmo.rs:35`, `src/kosmo.rs:175`, `src/histogram.rs:51`,
  `src/curve.rs:62`
- **Motivating evidence.** §3.3 picks G = 10 from Fig. 3 on the basis of the *mean* MAE
  plateau, but Fig. 3's maximum whisker stays an order of magnitude above the mean at every
  G — some traces are badly served by a uniform schedule, and the paper does not say which.
  The paper's own critique of MiniSim (§2.3, footnote 3) is precisely that uniformly spaced
  sizes hide points of interest when C_max is mis-chosen; Kosmo inherits the uniformity,
  just rescaled per access.
- **feasibility: H.** Self-contained in `perform_evictions` plus a small schedule module;
  no new harness, no new data, cheap to sweep on the MSR subset.
- **research_value: M.** Real but incremental — it is a smarter setting of an existing knob,
  and a reviewer could read it as tuning unless the histogram-guided variant is shown to
  find cliffs that the uniform schedule misses. Pairs naturally with A2 as the "make Kosmo
  cheaper" half of a project.
- **scoop_check: partial.** Closest work: **LAShards**, IEEE TC 74(10), Oct 2025
  (https://www.computer.org/csdl/journal/tc/2025/10/11087706/28xfc5EUReE), described as
  "low-overhead and self-adaptive MRC construction for non-stack algorithms" addressing
  "the inability to adapt to dynamic I/O workloads" — self-adaptive size selection for
  non-stack MRCs, but for mini-cache simulation rather than Kosmo's eviction maps. Read it
  before committing; if its adaptation rule is equivalent, reframe A5 as a comparison study
  or fold it into A2. The full text was not reachable in this desk review (paywalled).

## 6. Risks and open questions

- **`fasthash 0.4.0` is the single build risk.** Unmaintained since 2019, pulls
  `fasthash-sys` which builds C++ via bindgen and needs libclang, absent on this machine
  (conda-installable). Whether it compiles on the nightly required by `edition = "2024"` is
  **unclear** from reading alone. Mitigation is cheap (pure-Rust murmur3, `src/shards.rs:11`)
  but changes SHARDS sampling, so the baseline must be re-derived on our hardware anyway.
- **Nightly-only.** `#![feature(btree_cursors)]` (`src/mrc.rs:8`, `src/accurate.rs:8`) blocks
  stable Rust even though the feature has since stabilized; the team may need to pin a
  specific nightly, or delete the attribute and test on recent stable.
- **No trace converter and no reference `accurate/` curves.** Both were on the AE VM
  described in the README, which is gone. The converter is the first real deliverable; the
  key-hashing choice (MSR LBAs → u64 keys) is unspecified by the paper and will shift the
  absolute numbers.
- **`accurate` is the compute wall.** 100 serial full-trace simulations per trace per policy
  (`src/accurate.rs:71–96`); the paper quotes ~6 months of compute for the full study. Every
  MAE-bearing add-on must budget around this, e.g. by freezing a small ground-truth set
  early.
- **16 cores vs. 64.** The paper tuned MiniSim's thread pool to the core count (§4.2) while
  Kosmo saturates at G = 10 threads. On 16 cores the throughput comparison of Fig. 7 tilts
  toward Kosmo for reasons unrelated to the algorithm. Throughput claims must be reported
  with the thread-pool configuration made explicit, and memory (Fig. 6) is the safer
  headline to target.
- **The artifact is narrower than the paper.** MRU (§3.5), S3-FIFO (footnote 6), TTLs
  (§3.7) and the online resize/clean path are described but absent or unreachable in the
  code. Any add-on that assumes one of these exists (e.g. TTL-aware MRCs) starts from zero,
  not from a working baseline — and TTL-aware MRCs are separately claimed by the same group
  (ref. [36], EuroSys'24 "TTLs Matter"), so that direction is scooped.
- **Author follow-up is active.** PaperCache (HotStorage'25, code at papercache.io) uses
  runtime MRC-driven policy switching from the same lab. Anything framed as "use Kosmo
  online to pick a policy" is taken; the surviving online angle is measuring *Kosmo's own*
  MRC error over time under phase changes, which would first require wiring up the dead
  `Algorithm::resize`/`clean` hooks (`src/algorithm.rs:33–35`, `src/kosmo.rs:74–81`).
- **Artifact badges unverified.** The USENIX presentation page returned HTTP 403 to the
  fetcher and the Zenodo record shows no badge metadata, so "Results Reproduced" could not
  be confirmed despite the paper carrying a full Artifact Appendix.
- **README claims contradict the camera-ready** (5×/9×/1.2× vs. 3.6×/36×/1.3×). Use the
  paper's numbers as the reproduction target and note the discrepancy.

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; figures read from `pages/`):
Abstract (p. 2) — 3.6×/36× memory, 1.3× throughput, 52 traces/126 B accesses.
§1 Introduction (pp. 2–3) — MiniSim memory measurements, contributions, Limitations
paragraph (monotone MRCs, open policy classes). Fig. 1 (p. 2) — example MRC with cliff.
§2.1 (pp. 3–4) — LFU/FIFO/LRU/MRU/2Q/LRFU definitions, K_in = 25%, K_out = 50%.
§2.2 (pp. 4–5) — inclusion property, Table 1 counterexample, Fig. 2 ideal vs. practical LFU.
§2.3 (pp. 5–6) — Mattson, SHARDS (R = 0.001, S_max = 1024/2048, correction), MiniSim and
its two shortcomings, footnote 3 on non-uniform sizes.
§3.1–3.2 (pp. 6–7) — eviction maps, three operations, algorithm sketch.
§3.3 (pp. 7–8) — granularity G, Fig. 3 (MAE vs. G, `pages/page-08.png`), pruning, Fig. 4
(387× record reduction), SHARDS, parallel reconstruction.
§3.4 (pp. 8–9) + Alg. 1 — LFU eviction map; 1.49% violation figure.
§3.5 (pp. 9–11) + Algs. 2–3 — FIFO/2Q/LRFU/LRU/MRU maps; footnote 6 (S3-FIFO designed but
omitted). §3.6 (p. 11) + Fig. 5 — variable object sizes. §3.7 (p. 11) — TTLs.
§3.8 (p. 11) — simultaneous multi-policy generation.
§4 (pp. 12–13) — Table 2 (datasets), §4.1 MiniSim re-implementation, §4.2 environment
(Threadripper 3990X/64 cores/256 GB), §4.3 metrics (VmHWM, IO-excluded throughput, MAE vs.
100 full simulations).
§4.4 (pp. 13–14, figures on `pages/page-13.png`) — Fig. 6 memory, Fig. 7 throughput (2Q =
0.54×), Fig. 8 MAE (+0.44% FIFO, +1.56% 2Q, src1 outlier), Fig. 9 CPU/access (1.85–2×),
MiniSim with 20/50 caches.
§4.5 (p. 14) + Fig. 10 — violation rates 1.49/20.61/10.49/0.08/29.12%.
§5 (p. 14) — related work, DFShards. §6 (p. 14) — future work: ARC, LIRS, LHD; lower CPU
overhead. Appendix A (p. 15) — artifact scope, three tools, Zenodo DOI 10.5281/zenodo.10569925,
Rust 1.77.0-nightly + gnuplot 5.4. References [23] MSR, [34] S3-FIFO, [35] ARC, [36] TTLs
Matter, [37–38] SEC EDGAR, [39] twitter/cache-trace, [44] DFShards, [70] LIRS.

**Repository** (paths relative to `repo/`):
`README.md` (dependencies, 25-byte trace format, three tools, getting-started commands,
VM section, stale Claims section); `Cargo.toml` (edition 2024, fasthash 0.4.0, kwik git tag,
three `[[bin]]` targets); `traces/wdev.bin` (only bundled trace);
`src/kosmo.rs` (:35 GRANULARITY, :43 policies vec, :74–81 clean/resize, :149–171
update_histograms, :175–206 perform_evictions, :219–234 reconstruct_policy_stacks);
`src/kosmo/eviction_map.rs` (:32–41 trait, :43–49 policy enum);
`src/kosmo/eviction_map/fifo_eviction_map.rs` (:30–57 insert/pruning, :104–120 timestamp_at,
:132–165 unit test); `src/kosmo/eviction_map/{lfu,two_q,lrfu,lru}_eviction_map.rs`;
`src/kosmo/global_object.rs` (:43 reuse_distances, :58 evict_by_policy_index);
`src/kosmo/reconstructed_stack.rs` (:22–39 trait, :42–48 policy enum);
`src/kosmo/policy.rs` (:20–26 KosmoPolicy — no MRU/ARC/S3-FIFO);
`src/histogram.rs` (:11 BUCKET_SIZE, :51–94 increment, :127 resize);
`src/curve.rs` (:62–115 inverse-CDF construction, :171–189 MAE);
`src/shards.rs` (:11,:55 fasthash murmur3, :14 MODULUS), `src/shards/fixed_size.rs`;
`src/minisimulations.rs` (:18 NUM_CACHES = 100, :130–150 rescale);
`src/cache.rs` (:19–89 Cache trait, :114–120 re-exports — five policies, no ARC);
`src/access.rs` (:40–73 25-byte record, :30 unused ttl); `src/algorithm.rs` (:14–47 trait);
`src/accurate.rs` (:52–56 100 sizes, :71–96 serial full-trace loop);
`src/mrc.rs` (:8 nightly feature, :90 multi-policy panic, :104–107 mem::clear,
:159–178 memory/throughput reporting, :197–218 init).
`repo_facts.json` — HEAD 48a843d 2025-05-11, 46 files, 31.7 MB, 5,103 LOC Rust, MIT,
11 stars, **empty red-flag set**.

**Web** (provenance and scoop checks only):
Zenodo 10.5281/zenodo.10569925 — "Stumm-Lab/kosmo-fast24: FAST'24", author Kia Shakiba,
links `Stumm-Lab/kosmo-fast24/tree/v1.0.0-fast24`, no badge metadata.
https://www.usenix.org/conference/fast24/presentation/shakiba — HTTP 403, badges unverified.
LAShards, IEEE TC 74(10):3490–3503, Oct 2025 —
https://www.computer.org/csdl/journal/tc/2025/10/11087706/28xfc5EUReE (A2, A5 partial).
PaperCache, HotStorage'25 — https://dl.acm.org/doi/10.1145/3736548.3737836, code at
papercache.io (online policy-switching already claimed by the authors).
kwik `src/sys/mem.rs` v1.16.5 — `hwm()` parses `/proc/self/status` VmHWM, `clear()` writes
`/proc/self/clear_refs`; owner-writable, no root.
