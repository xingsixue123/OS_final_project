### 2. Kosmo: Efficient Online Miss Ratio Curve Generation for Eviction Policy Evaluation (FAST'24)

- **Repo:** https://github.com/Stumm-Lab/kosmo-fast24 — MIT, ~5.1k lines of Rust; 40 MB checkout, of which 33 MB is the bundled trace `traces/wdev.bin`.
  - **Last commit:** 2025-05-11, "Upgrade dependencies + modernize outdated code". The paper version is tag `v1.0.0-fast24`, identical to Zenodo 10569925.
- **What it is:** approximate miss-ratio curves (MRCs) for eviction policies that break the inclusion property (LFU, FIFO, 2Q, LRFU, plus LRU). Kosmo keeps one global object table with per-policy "eviction maps" and rebuilds cache stacks only when needed, where MiniSim keeps 100 separate caches.
  - **Three CLI tools:** `wss` (working-set size), `accurate` (100 full simulations as ground truth) and `mrc` (Kosmo or MiniSim with SHARDS sampling; reports MAE, memory or throughput).
- **Paper eval setup:**
  - **Hardware:** Threadripper 3990X, 64 cores, 256 GB.
  - **Traces:** 52 public traces, ~126 B accesses: MSR 13, Twitter 24, SEC 15.
  - **Sampling:** 3 SHARDS configs, granularity G = 10, 100 MiniSim caches.
  - **Scale:** the README estimates ~6 months of compute over ~4 TiB for the full campaign.
- **Reproduction target:** **Figures 6 (memory) + 8 (MAE), on the 13 MSR traces, for LFU and FIFO, all 3 SHARDS configs.** The claim: about **3.6× less memory** than MiniSim on average (up to 36×), with similar MAE (average within 0.25%). Memory is the least hardware-dependent claim; the 1.3× throughput claim (Figure 7) depends on core count.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| **Rust nightly** (`#![feature(btree_cursors)]`) | `src/mrc.rs:8`, `src/wss.rs:8`, `src/accurate.rs:8` (verified) | ❌ not installed | user `rustup`; there is **no `rust-toolchain` pin** |
| Edition 2024 → rustc ≥ 1.85 (the README's "1.77-nightly" is stale) | `Cargo.toml:4` (verified) | ❌ | pin a nightly near the last commit, e.g. `nightly-2025-05-10` |
| Crates (rayon, clap, serde, …); no `Cargo.lock` | `Cargo.toml`, `.gitignore:8` (verified) | fetched by cargo | small version-drift risk |
| `kwik` git dependency at tag v1.16.5 | `Cargo.toml:11` | pure Rust | cargo clones it |
| `fasthash 0.4.0` → 2018-era C++ built with `-msse4.2 -maes -mavx -mavx2` | `Cargo.toml:9` | gcc 12 present; CPU has AES and AVX2 | should build; fallback is a pure-Rust murmur3 in `src/shards.rs:54-56` |
| gnuplot 5.4 with pdfcairo (only for the final PDF) | README | not installed | `conda install -c conda-forge gnuplot=5.4.10` |
| Memory measured via `/proc/self/status` VmHWM | `kwik/src/sys/mem.rs` | ✅ user-readable | no root needed |
| No Docker, apt or sudo anywhere | README | ✅ | — |
| Trace format: 25-byte records (u64 timestamp, u8 command, u64 key, u32 size, u32 ttl) | `src/access.rs:39-63` | ⚠️ **no converter in the repo** | write one; validate against `traces/wdev.bin` (1,326,264 records, verified) |

**Data**

| dataset | size | how obtained | subset needed |
|---|---|---|---|
| MSR wdev (bundled) | 33 MB | in repo | smoke test |
| MSR Cambridge, 13 servers (434 M records) | 3.06 + 1.88 GB compressed → ~10.9 GB converted | SNIA IOTTA (click-through license) | ✅ **all 13 (target), ~16 GB disk** |
| Twitter, 24 clusters | ~749 GB zstd (~2.5 TB converted) | CMU FTP, no login | optional, small clusters only; **full set exceeds disk** |
| SEC EDGAR logs, 15 years | hundreds of GB zipped (~660 GB converted) | sec.gov | optional small years; **full set exceeds disk** |
| Authors' precomputed accurate curves | — | only on the artifact reviewers' VM | ❌ run `accurate` yourself |

> Easier route (my note, not from the explorer): the same MSR traces are published as `oracleGeneral .zst` on the CMU FTP (1.6 GB, no login; see the S3-FIFO section), so converting from that format avoids the SNIA click-through. Keys would then be hashed differently from the authors' `wdev.bin`, so validate on record and GET counts rather than exact keys.

**Hard filters** — H1 ✅ authors' lab repo, MIT, matches Zenodo · H2 ✅ no sudo, apt or Docker; rustup and conda install into `$HOME` · H3 ✅ CPU-only Rust; MSR-scale runs fit · H4 ✅ for the MSR subset (~16 GB); ❌ for full paper scale (Twitter + SEC far exceed 253 GB)

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | One `cargo build -r`, but on an unpinned nightly, with no lock file and 2018-era C++ in fasthash |
| dependency fit | 4 | All user-space (rustup, conda gnuplot); the risk is guessing the right nightly |
| data fit | 3 | The MSR subset is small, but there are no trace converters and the full Twitter/SEC data far exceeds disk |
| hardware fit | 4 | MSR runs at paper scale here; core count only affects the throughput claim |
| repro scripts | 2 | Tools print MAE, memory and throughput per trace, but there are no batch scripts, converters or plots for Figures 3–10 |
| extensibility | 4 | Clean per-policy trait modules (EvictionMap, LocalObject, ReconstructedStack, Cache); a new policy needs dispatch boilerplate in ~5 files |
| **total** | **21 / 30** | |

**Verdict: 🟡 DOABLE-WITH-WORK** · confidence medium · setup ≈2–3 person-days (0.5 toolchain, ~1 converter, ~1 run/plot scripts) · compute: 312 `mrc` runs + 26 `accurate` runs on MSR ≈ 1–3 days wall-clock (`accurate` dominates); < 20 GB disk.

**Key risks**
- **Toolchain drift:** nightly-only feature, edition 2024, no toolchain pin, no lock file.
- **fasthash-sys is unmaintained C/C++.** A pure-Rust murmur3 fallback may sample a different key set.
- **No trace converters and undocumented key hashing.** Whether writes are kept changes the throughput metric.
- **Current `main` is a May-2025 modernized version, not the Jan-2024 paper snapshot.** The README's numbers (5×/9×/1.2×) also disagree with the paper's (3.6×/36×/1.3×).
- **Throughput depends on hardware** (32 vs 64 threads, shared machine).
- **Minor code issues:** batching drops one access per 10 M records; a divide-by-zero on runs under 1 ms.

**Where an add-on plugs in**
- **New Kosmo policy** (e.g. S3-FIFO, mentioned in a paper footnote but not shipped; ARC/LIRS, listed as future work):
  - `src/kosmo/policy.rs`
  - `src/kosmo/eviction_map/<p>_eviction_map.rs`
  - `src/kosmo/local_object/<p>_local_object.rs`
  - `src/kosmo/reconstructed_stack/<p>_reconstructed_stack.rs`
- **Ground truth / MiniSim for that policy:** the `Cache` trait (`src/cache.rs`), plus `src/cache/<p>_cache.rs` and `src/cache/policy.rs`.
- **Algorithm changes** (adaptive granularity, faster stack rebuild): `Kosmo::perform_evictions` / `reconstruct_policy_stacks` in `src/kosmo.rs` (`GRANULARITY` at :35). Multi-policy runs are already supported by `Kosmo::new(&[KosmoPolicy])`, but `init_kosmo` in `src/mrc.rs:197-202` passes only one policy.
- **Sampling:** the `Shards` trait in `src/shards.rs`.

**Build route (not executed)**
1. `curl -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain none --no-modify-path && source ~/.cargo/env`
2. `rustup toolchain install nightly-2025-05-10 --profile minimal && rustup override set nightly-2025-05-10` (in the repo)
3. `conda create -y -n kosmo -c conda-forge gnuplot=5.4.10 zstd python=3.11`
4. `cargo build -r`
5. Smoke test: `./target/release/wss -p traces/wdev.bin` should print 313344512, then run `accurate` and `mrc -k lfu` / `-m lfu` on wdev
6. Get the MSR traces and write `msr_to_kosmo.py` (25-byte records); validate by rebuilding `wdev.bin`
7. Driver: `wss` → `accurate` (lfu, fifo) → `mrc` {Kosmo, MiniSim} × 3 SHARDS configs × {memory, throughput}; parse the `MAE:`, `Memory usage:` and `Throughput:` lines and box-plot against Figures 6–8
