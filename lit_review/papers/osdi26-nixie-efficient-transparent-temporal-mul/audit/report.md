# Nixie: Efficient, Transparent Temporal Multiplexing for Consumer GPUs

OSDI '26 · Yechen Xu, Yifei Wang, Nathanael Ren, Yiran Chen, Danyang Zhuo (Duke University)
Repo audited: `https://github.com/XOR-op/Nixie` @ `56f3fc1` (2026-09-06), 13.2 kLOC Rust, Apache-2.0.

---

## 1. Paper summary

**Problem.** Consumer desktops increasingly run several large local ML workloads at once
(LLM inference, diffusion image generation, image editing, background batch jobs). On a
consumer GPU each application's working set *nearly fills* GPU memory, so two concurrent
applications trivially oversubscribe it (§1, §2.1). The transparent mechanism people reach
for — NVIDIA UVM — degrades badly here. The paper identifies four UVM limitations (§2.2):
(i) no coordination between compute scheduling and memory placement ⇒ thrashing (worked
example: two 24 GB models on a 32 GB GPU ⇒ ≥16 GB migrated per forward pass ⇒ 4–12×
slowdown); (ii) page-fault handling serialises eviction and fetch, so only *half* of the
full-duplex PCIe link is ever used (Figure 1); (iii) LRU metadata is only updated on
faults, so eviction decisions are poor; (iv) every GPU-resident page needs a *pinned* CPU
backing page, which is unswappable and crushes host RAM. UVM-derived systems (nvshare [3],
TGS [34]) inherit all four.

**Key idea.** Nixie is a user-space *system service* that makes the currently scheduled
application's whole working set GPU-resident, and explicitly moves it out when the
application is descheduled — no demand paging at all. Two components (Figure 2, §3):

- **Nixie Shim** — an `LD_PRELOAD` library that interposes CUDA Runtime/Driver calls:
  allocation (`cudaMalloc`/`cudaFree`), implicit allocators (`cudaStreamCreate`),
  memory reporting (`cudaMemGetInfo`), kernel and CUDA-graph launches, and blocking
  synchronisation. Kernels still run in the application's own CUDA context, so there is
  no launch-path overhead while the application is scheduled in (§4, §7.1 Figure 10a).
- **Nixie Daemon** — a central service that decides *which* application may launch
  kernels, *where* each memory chunk lives, and *in what order* transfers are issued.

**Design details.**
- *Transparency mechanics* (§4): CUDA VMM API is used to reserve stable GPU virtual
  addresses and re-map them onto different physical allocations across migrations; new
  launches are blocked and `cuCtxSynchronize` is issued before migration so no in-flight
  kernel touches migrated memory; CUDA-graph capture windows are detected so the shim
  issues no CUDA calls during capture; `cudaMemGetInfo` reports only the caller's own
  usage so apps like SGLang size their KV cache sensibly.
- *Memory hierarchy* (§5.1, Figure 3): allocation-granularity **chunks** capped at 128 MB,
  split into 2 MB **blocks** (the VMM minimum). Four tiers — GPU, CPU pinned, CPU paged,
  disk — with exactly one copy per chunk (not a cache hierarchy), so GPU-resident data
  needs *no* pinned shadow, unlike UVM.
- *Fast context switch* (§5.2, Figures 4–5): planning is separated from orchestration. A
  **planner** emits a global block-move plan (block id, src tier, dst tier, direction,
  order) and the final per-tier state, avoiding the deadlock/extra-traffic pathologies of
  local back-pressure. An **orchestrator** keeps separate up/down queues, prioritises
  moves that unblock the other direction, and reserves a small pinned **streaming window**
  so GPU→pinned eviction overlaps pinned→GPU fetch (true full-duplex use). Straggler
  transfers are handled by dynamically evicting a few extra blocks.
- *Scheduling* (§6): GPUs expose neither `yield()` nor blocking-syscall signals, and NVML
  takes ~600 ms to report idleness, so Nixie infers idleness with a **100 ms timeout**
  since the last CUDA API return (blocking APIs are bracketed so a blocked app is not
  mis-classified). An **MLFQ-like** policy (Algorithm 1) demotes an app that exhausts its
  allotment and promotes an app that has been idle long enough, with a *soft priority
  recovery* rule that subtracts `R · (pending time)` with `R < 1/N` to prevent jitter and
  starvation. Defaults: allotment `T = 8 s`, preemption threshold `S = 4 s` at the top
  queue, doubling per level. The head of the scheduler queue is used to **prefetch** the
  likely-next application's data upward.

**Evaluation setup** (§7): AMD Ryzen 9 9950X, 96 GB DDR5, 2 × RTX 5090 (32 GB, PCIe
5.0×8), Debian 12, CUDA 12.9, driver 580.95.05. Apps: Ollama 0.12.11, SGLang 0.5.4.post1,
llama.cpp b7027, ComfyUI `eaf68c9`. Models: Qwen3 / Qwen3-MoE / Qwen3-VL / Qwen3-Coder /
Gemma3 GGUFs, Z-Image (BF16 6B), Qwen-Image (FP8 20B). Baselines: Ollama's own model
swapping, a UVM shim (hooks only `cudaMalloc`/`cudaFree`/`cudaMemGetInfo`), nvshare, TGS,
and a "2 GPUs" zero-switch upper bound. Datasets: DreamBench++ prompts, GSM8K,
HumanEval-FIM. ~10 kLOC Rust (Shim ~1.9 k, Daemon ~7.4 k, shared ~0.7 k).

**Headline numbers.**
- Context-switch TTFT reduced 44.0–82.3 % (Ollama) and 29.7–36.3 % (SGLang) vs UVM/nvshare
  (§7.1, Figure 6).
- ~2× UVM's host↔GPU throughput, near the `nvbandwidth` bi-directional ceiling
  (Figure 7; ~20.7 GB/s vs ~9.6 GB/s in the Gemma3-27B-Q8 case).
- Matches UVM's latency with 33.2–40.2 % of UVM's pinned memory (Figure 9) ⇒ the "66.8 %
  pinned-memory reduction" headline.
- Zero measurable launch overhead vs vanilla (Figure 10a, ResNet-18…152, batch 1);
  `cudaMalloc` faster than vanilla above 128 MB (Figure 10b).
- Case #1 prompt-expanded image generation: 1.3–1.4× over nvshare(W=4), 60–66 % of 2 GPUs
  (Figure 11). TGS cannot finish Qwen-Image in 15 min.
- Case #2 multi-agent (KVCOMM planner + math/code workers): 1.6× over nvshare (Figure 12).
- Case #3 code completion + long-running agent: 3.1–3.8× lower completion latency than
  nvshare(W=4); +90.6 %/+39.5 % background throughput in modest/sparse regimes but
  −23.5 % in the frequent regime; the `Nixie-RR` round-robin ablation is much worse
  (Figure 13).
- Case #4 three batch jobs: 85 % of ideal throughput, +5 % from auto-prefetch, vs 49.5 %
  for nvshare(W=4) (Figure 14).
- **§7.3 "Performance on Other Hardware": the authors re-run Case #2 on an RTX A5000
  (24 GB, PCIe 4.0×16), CUDA 12.4 / driver 550.67, with Q4 models — Nixie is 3.4× faster
  than nvshare and reaches 73 % of 2 GPUs (Figure 15).** This is the same GPU as ours.

**Stated limitations / future work** (§8): no semantic knowledge, so immutable data such
as model weights is migrated back to CPU even when a host copy already exists ("white-box
solutions"); policies are deliberately conservative and application-agnostic ("policy
extensibility" — learning from execution history, treating weights vs activations vs KV
cache differently); **no spatial multiplexing** when co-tenants are small enough to fit
together ("co-locating with small models"); no multi-tenant security model; Linux-only
prototype.

---

## 2. Artifact audit

### 2.1 Repository structure

```
Cargo.toml                    workspace: src/daemon, src/common, src/sidecar
src/common/     (~?)          IPC: shm.rs, shm_buffer.rs, sync.rs, rpc.rs, constant.rs
src/sidecar/    (~1.9 kLOC)   the LD_PRELOAD shim  -> libnixiesidecar.so (cdylib)
src/daemon/     (~7.4 kLOC)   the daemon + `nixie` CLI
docs/cli.md                   a thorough, code-derived CLI reference
.github/workflows/check.yml   cargo check / fmt / clippy / test (--features cuda-13)
```

No Dockerfile, no shell scripts, no Python, no evaluation code, no data. `repo_facts.json`
reports **zero red-flag hits** (no sudo / kernel module / eBPF / perf / KVM / RDMA / CXL
strings). Confirmed by grep: the only `is-root` mention is an unused dependency line in
`src/daemon/Cargo.toml:61`; no `mlock`, `RLIMIT`, `/proc/sys`, `hugepage`, or `setuid` use
anywhere in `src/`.

### 2.2 Paper component → code path

| paper section | mechanism | code |
|---|---|---|
| §4 transparency | `LD_PRELOAD` hooks of `cudaMalloc`/`cudaFree`/`cudaMemGetInfo`, small-vs-large allocation split at 2 MB | `src/sidecar/src/intercept.rs:82` (`cudaMalloc`), `:46-61` (`cudaMemGetInfo`) |
| §4 launch control | kernel / graph launch interposition, graph-capture detection | `src/sidecar/src/intercept_launch.rs`, `is_during_capture()` used at `src/sidecar/src/schedule/mod.rs:81` |
| §4 sync bracketing | blocking-API before/after hooks feeding idleness detection | `src/sidecar/src/intercept_sync.rs`, `src/sidecar/src/schedule/mod.rs:199-217` |
| §4 stable VAs (CUDA VMM) | reserve VA, remap physical handles | `src/sidecar/src/memory/alloc_tracking.rs`, `src/sidecar/src/memory/mod.rs`, `src/common/src/shm.rs` (`PhysicalMemoryHandle`, `HandleList`) |
| §5.1 chunk = 128 MB, block = 2 MB | constants | `src/common/src/constant.rs:5-6` (`MIN_ALLOCATION_SIZE = 2 MiB`, `MAX_ALLOCATION_SIZE = 128 MiB`) |
| §5.1 four tiers | GPU / pinned SHM / paged host / disk managers | `src/daemon/src/runtime/migration/{shm_buffer,hostmem_buffer,storage_buffer}.rs`, `BufferLocation` in `migration/mod.rs` |
| §5.2 planner | global block-move plan, eviction candidate choice, capacity accounting | `src/daemon/src/runtime/migration/migration_plan.rs:129` (`realtime_migrate_task`), `:430` (`local_prefetch_task`) |
| §5.2 orchestrator, full-duplex, streaming window | separate up/down transfer paths + worker threads | `src/daemon/src/runtime/migration/execution.rs:257` (`run`), `:546` (`device_to_host_transfer`), `:632` (`host_to_device_transfer`), `:829` (`backend_to_shm_transfer`) |
| §5.2 pinned staging registered with CUDA | `cuMemHostRegister` over the shared `/dev/shm` region | `src/sidecar/src/init.rs:84-99`, `src/sidecar/src/cu_api.rs:46` |
| §6.1 100 ms idleness timeout | per-API-class thresholds and the monitor loop | `src/sidecar/src/schedule/mod.rs:230-283` (`KERNEL_INTERVAL = 100 ms`, `GRAPH = 200 ms`, `MALLOC/TRANSFER = 300 ms`, check every 20 ms) |
| §6.2 Algorithm 1 (priority inference) | demotion / soft promotion with pending-time compensation | `src/daemon/src/runtime/schedule/policy.rs:392-474` (`update_priority`) |
| §6.3 T = 8 s, S = 4 s, doubling | quantum + preemption tables | `policy.rs:74-93` (`priority_level_to_time_quantum`, `priority_level_to_cooldown`) |
| §6.3 round-robin within level, preemption rule | queue ordering and preemption decision | `policy.rs:489` (`compute_prioritization`), `policy.rs:524` (`compute_can_preempt`) |
| §6.3 auto-prefetch of queue head | build an upward move list for the head pid | `policy.rs:283-299`, `policy.rs:336` (`construct_prefetch_plan`) |
| §3 exclusivity + migration on switch | Disable victim → migrate → Enable incoming | `src/daemon/src/runtime/schedule/scheduler.rs:250` (`handle_sched_request`), `:311` (`Disable`), `:329` (`perform_migration`), `:347-357` (`Enable`) |
| CLI `--shmem/--hostmem/--device-limit/--auto-prefetch` | config plumbing | `src/daemon/src/config.rs:158-256`, `docs/cli.md` |

The mapping is complete: every mechanism claimed in §3–§6 has identifiable code, and the
scheduler and migration planner ship with real unit tests
(`policy.rs:590-1150`, `execution.rs:1356-1472`). This is the system, not a stub.

### 2.3 Evaluation code — in a **second** repository

The audited repo contains **no** evaluation scripts, workloads, baselines, or plotting
code. The scout's note points at `https://github.com/XOR-op/nixie-eval`, which I fetched:
it exists and is a complete harness (Python, `uv`-managed):

- runners: `run.py -b rotate-builtin | trend-analysis | space:{gemma3,qwen3} |
  comfyui-all:{qwen-image,z-image} | coding-all:all | mix-kvcomm-all | batching-all |
  malloc_bench | resnet_bench`, driven by a `command_server.py` and
  `config/service_config.toml` (paths to `daemon_path`, `shared_lib_path`).
- baselines: naive UVM (`make all` in `executable/`), **nvshare** commit `1a8f211` with
  `patch/nvshare.patch` (CUDA-graph fix), **TGS** commit `e1c6a31` with `patch/tgs.patch`.
- an explicit figure map: `figure/rotate_llm.py` → Figs 6 & 7, `figure/trend_analysis.py`
  → Fig 8, `figure/space_analysis.py` → Fig 9, `figure/overhead_{malloc,resnet}_bench.py`
  → Fig 10, `figure/case_study_comfyui.py` → Fig 11,
  `figure/case_study_mix_kvcomm.py` → Fig 12, `figure/case_study_coding.py` → **Fig 13**,
  `figure/case_study_batching.py` → Fig 14; `generate_all_figures.py` does all of them.
- it pins the main repo to commit **`b7466db`** ("we use `nihilphase` as our internal
  codename"), *not* the head we cloned (`56f3fc1`).

This is a big plus for reproduction but it means the audited clone alone is not
reproducible — the team must clone a second repo, and pin the main repo back to
`b7466db` (or port the eval config forward).

### 2.4 Build route on *this* machine

1. `rustup` into `$HOME` (Rust ≥ 1.90 per README; edition 2024 is used, so ≥ 1.85 is a
   hard floor). No system packages needed.
2. **Do not** use the default `cuda-system` feature: `src/sidecar/build.rs:61` shells out
   to `nvcc --version` and would pick up the system CUDA 11.8, which is not one of the
   feature paths the authors test. Build with
   `cargo build --release --no-default-features --features cuda-12`, which selects
   `cudarc/cuda-12000 + fallback-dynamic-loading`
   (`src/{common,daemon,sidecar}/Cargo.toml`), i.e. `libcuda.so` is `dlopen`ed at runtime
   and no CUDA toolkit is needed to build. Our driver 535.216.01 exposes the CUDA 12.2
   driver API, a superset of the 12.0 symbols cudarc binds. The `cuda-13` path used in CI
   (`.github/workflows/check.yml:46`) is *not* usable here.
3. Runtime prerequisites are all unprivileged: a Unix socket at `/tmp/nixie-ctl.sock`,
   `shm_open` regions under `/dev/shm` (`src/common/src/shm_buffer.rs:22`,
   `src/daemon/src/runtime/shm.rs:13`), `cuMemHostRegister` over that region
   (`src/sidecar/src/init.rs:91`), NVML for device memory probing
   (`src/daemon/src/config.rs:182-195`), and `LD_PRELOAD` injection by `nixie run`.
4. Sizing for 125 GiB RAM: defaults are `--shmem 32g --hostmem 32g`
   (`config.rs:168-169`). `/dev/shm` on Debian defaults to RAM/2 ≈ 62 GiB, so 32 GiB of
   pinned SHM is admissible, but on a *shared* machine (111 GiB free at measurement) the
   team should start at `--shmem 16g --hostmem 24g`. Both values must be multiples of
   2 MiB (`config.rs:236`).
5. Set `--device-limit 'g:0.92'` or so; the default `g:0.95` of 24 GB ≈ 22.8 GB, which is
   tight but workable — the planner already reserves `2 × 128 MB` for API inaccuracy
   (`migration_plan.rs:176-177`).

### 2.5 Dependency ages

All Cargo pins are recent (checked against `Cargo.toml`, head 2026-09-06):
`cudarc 0.19.8`, `tokio 1.38`, `tarpc 0.35`, `nix 0.29`, `clap 4.5`, `nvml-wrapper 0.10`,
`mimalloc 0.1.48`, `serde 1`, `bincode 1.3.3`. `Cargo.lock` is committed. Nothing
abandoned. Rust edition 2024. The *application* pins live in nixie-eval and are from
late 2025 (llama.cpp b7027, SGLang 0.5.4.post1, Ollama 0.12.11, ComfyUI `eaf68c9`) — all
still fetchable from GitHub/PyPI.

### 2.6 Data / model sources

All public: Qwen3, Qwen3-MoE, Qwen3-VL, Qwen3-Coder and Gemma3 GGUFs (auto-downloaded by
llama.cpp/SGLang on first run per nixie-eval README); `Comfy-Org/z_image_turbo` and
`Comfy-Org/qwen_image` (+ `lightx2v/Qwen-Image-Lightning`) on Hugging Face; DreamBench++,
GSM8K and HumanEval-FIM are public datasets. Ollama models are produced locally from the
GGUFs via the `ollama_modelfiles/` Modelfiles. No proprietary traces anywhere.

---

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper §1 end: "Our source is available at https://github.com/XOR-op/Nixie"; `README.md:31` links back to the USENIX OSDI '26 page and `README.md:83-91` carries the paper's BibTeX. The clone is the real system: 13.2 kLOC Rust matching the paper's "~10,000 lines of Rust" (§7), with the shim (`src/sidecar/`), the daemon (`src/daemon/`), the planner (`migration/migration_plan.rs`), the orchestrator (`migration/execution.rs`) and the MLFQ policy (`schedule/policy.rs`) all present and unit-tested. Paper p.1 carries a USENIX "Artifact Evaluated — Available" badge (`pages/page-02.png`, top right). |
| `H2_no_root` | **pass** | Entirely user-space: `LD_PRELOAD` (`docs/cli.md:8`), Unix socket `/tmp/nixie-ctl.sock` (`docs/cli.md:9`), POSIX shm (`src/common/src/shm_buffer.rs:22`), `cuMemHostRegister` on that region (`src/sidecar/src/init.rs:91`), CUDA VMM + NVML. Grep over `src/` finds no `mlock`/`RLIMIT`/`/proc/sys`/hugepage/kernel-module/eBPF/`perf` use; `repo_facts.json` red_flags is empty. No Dockerfile. The only caveat is a baseline, not Nixie: nvshare and especially **TGS** (a Kubernetes/container-oriented system) live in nixie-eval and may not be runnable here — the team can drop TGS (the paper itself excludes it from microbenchmarks, §7) and keep the UVM shim + Ollama baselines, which are pure user-space. |
| `H3_hardware_fit` | **pass** | The paper itself runs Nixie end-to-end on **1 × RTX A5000 24 GB, Ampere, PCIe 4.0×16** in §7.3 / Figure 15, with Q4 models chosen precisely because "RTX A5000 has smaller memory". Our machine is that GPU. 16 cores / 125 GB RAM comfortably cover the daemon's `--shmem 32g --hostmem 32g` defaults (`config.rs:168`), and ~35–50 GB of GGUFs fit in 257 GB free. The mechanism (temporal multiplexing of two oversubscribing apps) needs exactly one GPU; the "2 GPUs" bars in Figures 6/11/15 are an upper-bound reference we simply omit. No FP8 kernels are required on the LLM path (GGUF Q4/Q6 on llama.cpp); only the ComfyUI Qwen-Image case uses FP8 weights, which ComfyUI upcasts on Ampere — a slow-but-working path, and Z-Image BF16 is the cheaper alternative. |
| `H4_obtainable_deps_data` | **pass** | Rust via `rustup` into `$HOME`; all crates from crates.io with a committed `Cargo.lock`; the `cuda-12` feature avoids needing any CUDA toolkit at build time (`Cargo.toml` feature tables + `src/sidecar/build.rs:21`). Workloads: llama.cpp (cmake + system nvcc 11.8 or a conda CUDA 12.2), Ollama (user-space tarball), SGLang/ComfyUI (pip/conda). `uv` for nixie-eval installs via pip. All models/datasets public (§2.6). The one flagged risk (not a fail): SGLang 0.5.4 pulls PyTorch cu12.6/12.8 wheels, which rely on CUDA minor-version compatibility against driver 535 — if that breaks, every figure except 6/7's SGLang bars can still be produced with llama.cpp alone. |

No `fail`, no `unclear`.

---

## 4. Reproduction plan

**Target: Figure 13 (Case #3, §7.2) — "Nixie is 3.1×–3.8× faster than nvshare (W = 4) for
interactive code-completion latency while keeping background throughput competitive, and
the `Nixie-RR` round-robin ablation is far worse."** This is the paper's abstract-level
claim ("improves the latency of interactive code-completion tasks co-located with a
long-running LLM by up to 3.8×") and the one that exercises the contribution that is
*most* distinctive — the MLFQ scheduler — rather than only the transfer engine.

**Why this one.** It needs a single application stack (llama.cpp), two model instances,
a public dataset (HumanEval-FIM), and it ships with both a runner
(`run.py -b coding-all:all`) and a plotting script (`figure/case_study_coding.py`) in
nixie-eval. It also contains a self-contained ablation (`Nixie-RR`) that requires **no**
external baseline, so a partial result is obtainable even if nvshare refuses to build.

**Scale-down.** The paper's Fig-13 config is Qwen3-Coder 30B-**Q6** (FIM) + Gemma3
27B-**Q8** (background agent) on a 32 GB RTX 5090. Neither fits in 24 GB at those
quantisations. Follow the authors' own A5000 recipe from §7.3 and drop to **Q4**:
Qwen3-Coder-30B-A3B-Instruct Q4_K_M (~18 GB) + Gemma3-27B-it Q4_K_M (~16.5 GB). Each fits
individually in 24 GB; combined 34.5 GB still oversubscribes by ~11 GB, so the phenomenon
under test (whole-working-set context switching) is preserved. Daemon:
`nixie daemon --shmem 20g --hostmem 24g --device-limit 'g:0.92'`. Keep all three arrival
regimes (1 s / 3 s / 6 s intervals) and the 4 s `Nixie-RR` window. Absolute latencies will
be higher than the paper's (PCIe 4.0×16 ≈ 26 GB/s bidirectional vs their 5.0×8), so
compare **ratios**, not absolute seconds — and note the paper's own A5000 run (Fig 15)
shows *larger* Nixie-vs-nvshare ratios on this hardware, not smaller.

**Steps.**
1. `rustup` install; `git clone` Nixie, `git checkout b7466db` (the commit nixie-eval
   pins); `cargo build --release --no-default-features --features cuda-12`. Smoke-test
   `nixie daemon` + `nixie status` + `nixie run -d 0 <trivial cuda binary>`.
2. Build llama.cpp b7027 with CUDA (`-DGGML_CUDA=ON`, `CMAKE_CUDA_ARCHITECTURES=86`),
   using system nvcc 11.8 or conda `cuda-toolkit=12.2`.
3. Download the two Q4 GGUFs (~35 GB) from Hugging Face; fetch HumanEval-FIM.
4. `pip install uv`; clone nixie-eval; `uv sync`; edit `config/service_config.toml`
   (`daemon_path`, `shared_lib_path`, model paths, quantisation).
5. Run `uv run command_server.py` then `uv run run.py -b coding-all:all` for
   Nixie and Nixie-RR first; plot with `figure/case_study_coding.py`.
6. Then add baselines: the naive UVM shim (`make all` in `executable/`, trivial) and
   nvshare `1a8f211` + `patch/nvshare.patch` (source build, user-space scheduler). Skip
   TGS — it is container/Kubernetes-oriented and the paper already reports it fails on
   these workloads.
7. Cross-check the cheap sanity figure on the way: `uv run run.py -b malloc_bench`
   → Figure 10b takes minutes and validates the whole shim/daemon plumbing.

**Effort.** ≈ **6 person-days + ~15 GPU-hours.** Breakdown: 1 pd Rust build + smoke test,
1 pd llama.cpp + model download, 2 pd porting the nixie-eval harness (hard-coded paths,
no Docker, model re-quantisation), 1.5 pd nvshare/UVM baselines, 0.5 pd plotting. Compute:
3 arrival regimes × 4 configurations × ~30–45 min ≈ 8–10 GPU-h for Fig 13, plus ~5 GPU-h
of debugging runs.

**Level: M.** Everything needed exists and is public, the paper validated this exact GPU,
and there is a figure-level script for the target. It is not H because (a) the eval code
lives in a *second* repo that pins a *different* commit of the audited one, (b) the
harness has machine-specific configuration and no container, so it must be ported by hand,
(c) our driver 535 / CUDA ≤ 12.2 is two major releases behind the authors' 580.95 / 12.9
and the repo only offers `cuda-12`/`cuda-13` build paths — the CUDA VMM + `cuMemHostRegister`
behaviour on 535 is unverified, and the paper itself notes UVM behaves differently on the
older-driver A5000 box (§7.3: "We observed increase in PCIe idleness on this hardware…
we suspect the root cause is the older NVIDIA driver"), and (d) the models must be
re-quantised, so only ratios, not absolute numbers, can be matched. The artifact carries
only the **Available** badge — no Functional/Reproduced evidence.

---

## 5. Add-on ideas

### A1 — Scheduler-aware eviction victim selection in the pinned tier

**Hypothesis.** We hypothesize that choosing pinned-tier (SHM) eviction victims by
scheduler order — demoting blocks belonging to the application *furthest* from the head of
the MLFQ queue — reduces mean and p95 context-switch time and interactive TTFT under
**three or more co-located applications whose combined footprint exceeds SHM + host tiers**
(so that blocks actually spill to disk), compared with Nixie's current victim choice.

**Mechanism.** §5.2 states the planner "treats [the likely next application's] blocks as
less attractive eviction candidates, which preserves useful prefetching state". The code
does not implement this: `realtime_migrate_task` builds
`shm_eviction_candidates = data_manager.shm_buffer_ids()` and only removes the *incoming*
pid (`migration_plan.rs:192-193`), then pops victims with
`shm_eviction_candidates.iter().next()` (`migration_plan.rs:286-291`) — i.e. arbitrary
`HashMap` iteration order, which is randomised per process in Rust. Change: thread the
scheduler's ordered queue (already computed by `compute_prioritization`,
`policy.rs:489`) into the planner as a per-pid rank, sort candidates by
(rank, last-scheduled-time) instead of hash order, and apply the same rule to
`local_prefetch_task` (`migration_plan.rs:430`). ~200–400 LOC plus a rank-passing plumb
through `scheduler.rs:329 perform_migration`.

**Code locations.** `src/daemon/src/runtime/migration/migration_plan.rs:286`,
`src/daemon/src/runtime/schedule/policy.rs:489`,
`src/daemon/src/runtime/schedule/scheduler.rs:329`.

**Motivating evidence.** A documented design/implementation gap: the paper claims a
next-app-aware eviction preference (§5.2) that the released planner does not have. The
paper also never evaluates >3 co-located apps (Case #4 uses exactly three), and the only
scheduler/memory-interaction ablation reported is auto-prefetch on/off, worth +5 %
(Figure 14).

**Feasibility: H.** Localized to one planner function plus a rank argument; the
`construct_prefetch_plan`/`local_prefetch_task` unit tests (`policy.rs:1072`,
`execution.rs:1356`) give a regression harness; evaluable with
`run.py -b batching-all` (Fig 14) extended to 4–5 llama.cpp instances of 6–14 B Q4 models
on one A5000, well within 24 GB-oversubscription range and a few GPU-hours.

**Research value: M.** It closes a stated-vs-implemented gap and probes a regime the paper
skips, but "pick better victims" is an expected win; a reviewer would want the >3-app
regime to be the story, not the policy itself.

**Scoop check: clear.** Searched "Nixie … follow-up", "transparent GPU time-sharing
LD_PRELOAD CUDA VMM context switch scheduler 2026". Nothing addresses Nixie's pinned-tier
victim policy. Closest neighbours are
[MSched (arXiv 2512.24637)](https://arxiv.org/abs/2512.24637) and
[XSched, ATC '25](https://www.usenix.org/system/files/atc25-fan.pdf), neither of which
manages a pinned staging tier this way.

---

### A2 — Migration-cost-adaptive time quanta

**Hypothesis.** We hypothesize that setting each application's time quantum from the
*measured* cost of the switch that admitted it — targeting a fixed switch-overhead
fraction rather than the fixed 8/16/32/64/128 s ladder — moves the
interactive-latency vs background-throughput frontier outward, specifically recovering
most of the **23.5 % background-throughput loss Nixie suffers in the "frequent"
(1 s-interval) regime of Figure 13** at equal or better completion latency.

**Mechanism.** Today `priority_level_to_time_quantum` and `priority_level_to_cooldown`
are hard-coded ladders (`policy.rs:74-93`), and `compute_cooldown` estimates migration
time from a **hard-coded `pcie_speed = 16.0` GB/s with a `× 1.5` fudge**
(`policy.rs:149-160`) — a constant that is simply wrong on PCIe 5.0×8 (their box) and on
our PCIe 4.0×16. Replace with: (i) an EWMA of actually observed per-switch bytes and
wall-clock duration, exported from the orchestrator (`execution.rs:257 run`, which already
returns `swap_out` bytes into `scheduler.rs:359`); (ii) a quantum rule
`T_p = max(T_min, k · T̂_migrate(p))` with the overhead fraction `1/k` as the single tunable;
(iii) keep the MLFQ promotion/demotion logic untouched. ~300–600 LOC, plus a new daemon
config knob in `config.rs:80-89`.

**Code locations.** `src/daemon/src/runtime/schedule/policy.rs:74`,
`src/daemon/src/runtime/schedule/policy.rs:149`,
`src/daemon/src/runtime/migration/execution.rs:257`,
`src/daemon/src/runtime/schedule/scheduler.rs:359`, `src/daemon/src/config.rs`.

**Motivating evidence.** The paper makes the tradeoff explicit and unresolved: "under
frequent interactive arrivals, Nixie sacrifices background throughput to keep
code-completion latency low" (§7.2, Case #3), and §8 "Policy extensibility" invites
exactly this ("These policies are intentionally conservative; refining them is a promising
direction"). The hard-coded 16 GB/s constant is a concrete, citable simplification.

**Feasibility: H.** One module, the measurement plumbing already exists
(`perform_migration` returns swapped-out bytes), and the evaluation is the existing
`run.py -b coding-all:all` sweep plus `batching-all`, ~10–15 GPU-hours on the scaled-down
Q4 models.

**Research value: M.** A clean, well-motivated Pareto study that the paper explicitly
defers, but "make the quantum proportional to the switch cost" is the textbook answer;
the surprise would only be in the magnitude or in a non-monotonic result.

**Scoop check: partial.** [MSched (arXiv 2512.24637, Dec 2025)](https://arxiv.org/abs/2512.24637)
co-designs scheduling and memory placement for GPU multitasking, but by *predicting
working sets* to replace demand paging, not by sizing quanta from measured migration cost,
and it operates on a UVM/page-fault substrate rather than Nixie's chunk planner. No work
found that adapts Nixie's MLFQ quanta.

---

### A3 — Opportunistic co-residency (spatial sharing when the working sets fit)

**Hypothesis.** We hypothesize that letting two applications stay **simultaneously
resident and runnable** whenever their combined footprint fits under the device limit —
instead of always paying a full context switch — reduces interactive p95 latency by a
large factor and raises aggregate throughput, under the very common consumer mix of a
*small* latency-sensitive model (e.g. Qwen3-4B-Q4, ~2.5 GB, code completion) alongside a
*large* background model (e.g. Qwen3-Coder-30B-Q4, ~18 GB), compared with Nixie's
unconditional temporal multiplexing; and that the crossover point where SM contention
makes co-residency *worse* than switching is measurable and workload-predictable.

**Mechanism.** Nixie's daemon hard-codes a single runnable application:
`ActiveClientState::Active { pid, .. }` (`scheduler.rs:47`, `:342`), and
`handle_sched_request` unconditionally sends `SchedulingArgs::Disable` to the incumbent
(`scheduler.rs:311-328`) before migrating and `Enable`-ing the incoming one
(`scheduler.rs:347`). Change: (i) generalise `ActiveClientState` to a small *set* of
resident-and-enabled pids; (ii) in `handle_sched_request`, query the planner for whether
the incoming app's residual can be admitted **without evicting** the incumbent (the
planner already computes `into_gpu_requirement` against free GPU space,
`migration_plan.rs:142-184`) and, if so, skip the `Disable` + migration path entirely;
(iii) keep the MLFQ as the arbiter for when the set must shrink, and keep the shim's
`set_allow_running` semantics unchanged (`src/sidecar/src/schedule/mod.rs:78`) so
transparency is preserved. Add a `--max-coresident` knob in `config.rs`.

**Code locations.** `src/daemon/src/runtime/schedule/scheduler.rs:311`,
`src/daemon/src/runtime/schedule/scheduler.rs:342`,
`src/daemon/src/runtime/migration/migration_plan.rs:142`,
`src/sidecar/src/schedule/mod.rs:78`, `src/daemon/src/config.rs`.

**Motivating evidence.** §8 "Co-locating with small models" names this as the paper's own
open problem: "When there is a set of small models, it is possible to perform spatial
multiplexing … How to integrate spatial multiplexing into Nixie is a promising future
direction." The paper's own workloads are all large-vs-large, so the regime is entirely
unexplored — yet it is arguably the *most* common consumer case (a 3–8 B completion model
next to one big agent). Either outcome is informative: if concurrent execution costs the
interactive app more in SM contention than a 1–2 s context switch would, that is a
publishable negative result about when temporal multiplexing is actually the right
primitive.

**Feasibility: M.** Cross-cutting: the single-active-client invariant is threaded through
`scheduler.rs` (`poll_queue`, `handle_activity_idle`, `handle_activity_yield`,
`handle_prefetch_request`) and through the planner's assumption that the victim's blocks
are being evicted. It also needs a new mixed-size workload generator (the eval harness
only has same-scale pairs). But it needs no new hardware, fits easily on one 24 GB A5000
(2.5 + 18 GB < 22 GB limit), and the transfer engine is untouched. Realistically the core
of a 10-week project for 2–4 students, not a side task.

**Research value: H.** It attacks the paper's explicitly stated limitation, in a regime
the paper never measures, and the answer determines the *scope* of Nixie's central design
decision (whole-application temporal multiplexing). An OSDI reviewer would care about the
crossover characterisation regardless of which side wins.

**Scoop check: partial.** Concurrent 2026 work does transparent *spatial* GPU sharing —
[Detshare / "Performance Isolation and Semantic Determinism in Efficient GPU Spatial
Sharing" (arXiv 2603.15042)](https://arxiv.org/abs/2603.15042), also LD_PRELOAD-based, and
[VUDA (arXiv 2605.01352)](https://arxiv.org/abs/2605.01352) for CUDA–Vulkan spatial
sharing. Neither integrates spatial sharing with a memory-oversubscription temporal
multiplexer, and neither cites or extends Nixie. Queries run: "Nixie … spatial
multiplexing follow-up", "transparent GPU time-sharing LD_PRELOAD CUDA VMM API context
switch scheduler 2026". Position carefully against Detshare in the write-up.

---

### A4 — History-driven predictive prefetch, including into free GPU memory

**Hypothesis.** We hypothesize that predicting the next application from the scheduler's
own execution history and prefetching its blocks **during idle windows, all the way into
free GPU memory** (not just up to the pinned tier) cuts interactive TTFT in the
*sparse*/*modest* arrival regimes of Figure 13 by substantially more than the +5 % that
Nixie's current reactive prefetch delivers in Figure 14.

**Mechanism.** Today auto-prefetch fires only when `sched_req` is already non-empty —
i.e. after a request has arrived (`policy.rs:283-299`) — and
`construct_prefetch_plan` (`policy.rs:336-389`) only emits Storage→Shm, HostMem→Shm and
Storage→HostMem moves: **never into the GPU**. Meanwhile `ClientStatistics` already keeps
a 64-entry `History` of run chunks with durations, stop reasons and priorities
(`statistics.rs:108-131`, `:169`) that is used only for the `nixie history` CLI. Change:
(i) fit a trivial next-app predictor (last-app / Markov over the history ring) and trigger
prefetch on *idleness notification*, not on request arrival; (ii) extend
`construct_prefetch_plan` to emit Shm→Gpu moves sized to `gpu_free_space` minus a safety
margin, reusing the existing GPU-destination prefetch path already present in
`handle_prefetch_request` (`scheduler.rs:369`) and documented in `docs/cli.md:224-234`;
(iii) add an abort path so a real schedule request preempts an in-flight speculative fetch.

**Code locations.** `src/daemon/src/runtime/schedule/policy.rs:283`,
`src/daemon/src/runtime/schedule/policy.rs:336`,
`src/daemon/src/runtime/schedule/statistics.rs:108`,
`src/daemon/src/runtime/schedule/scheduler.rs:369`.

**Motivating evidence.** §6.3 admits the current heuristic is one-step and reactive
("when there is already an application at the head of scheduler queue, it is most likely
to run after the current application is scheduled out"); Figure 14 measures its worth at
only +5 %, and §8 "Policy extensibility" suggests "learning scheduling decisions from
recent execution history" as future work. The sparse (6 s-interval) regime of Figure 13 has
long idle windows that are currently wasted.

**Feasibility: H.** Confined to the policy module plus a prefetch-plan extension; the
transport for every move type already exists in `execution.rs`; evaluated with the existing
`coding-all` and `batching-all` runners on the Q4 scale-down, ~10 GPU-hours.

**Research value: M.** A solid, well-targeted improvement on a mechanism the authors
themselves flag as conservative, but speculative prefetch on a predicted next task is a
familiar idea, and the risk of wasted-bandwidth regressions is the only real surprise.

**Scoop check: partial.** [MSched (arXiv 2512.24637)](https://arxiv.org/abs/2512.24637),
"Towards Fully-fledged GPU Multitasking via Proactive Memory Scheduling", does predictive
working-set preparation at context-switch time with a template-based predictor — the same
*spirit*, but keyed on kernel launch arguments over a UVM substrate, not on a scheduler's
inter-application history, and not inside Nixie's chunk/tier planner. Treat MSched as
related work to beat, not as a scoop.

---

### A5 — Cross-process content dedup in the pinned tier

**Hypothesis.** We hypothesize that content-addressing the 2 MB blocks of the pinned (SHM)
tier so that identical blocks are stored once across processes reduces pinned-memory usage
and eliminates redundant PCIe traffic on context switches, under the consumer-realistic
case of **two applications backed by the same model weights** (e.g. the two identical
llama.cpp/Ollama instances of the paper's own Figure 6 microbenchmark, or an editor
plug-in and a CLI agent sharing one GGUF), improving on the paper's 66.8 %
pinned-memory reduction (Figure 9) — and that on *different*-model mixes the hashing cost
is small enough to be a free option.

**Mechanism.** `ShmBufferManager` keys buffers by `BufferId { pid, device_id, block_id,
size }` (`migration/shm_buffer.rs`, `migration_plan.rs:207-212`), so two processes holding
byte-identical weight blocks occupy two copies. Add a content hash (xxh3 over each 2 MB
block, computed by the existing multi-threaded staging workers in
`execution.rs:829 backend_to_shm_transfer` / `:546 device_to_host_transfer`) and a
refcounted interning table; on `hostmem/shm → GPU` fetch, a block already resident for
another process can be re-used without re-reading the lower tier, and eviction becomes a
refcount decrement. Copy-on-write is unnecessary: blocks in the pinned tier are only
written by the migration engine, never by the application. Extend the planner's capacity
accounting (`shm_free_blocks_count`, `migration_plan.rs:185`) to count unique blocks.

**Code locations.** `src/daemon/src/runtime/migration/shm_buffer.rs`,
`src/daemon/src/runtime/migration/execution.rs:829`,
`src/daemon/src/runtime/migration/migration_plan.rs:185`,
`src/common/src/shm.rs`.

**Motivating evidence.** The paper's own context-switch microbenchmark is "an application
executing a model and then switching to another identical instance of the same application
and model" (§7.1) — a workload where dedup would be nearly total, yet Nixie pays full
migration cost for it. §8 "White-box solutions" identifies the same redundancy from the
other direction ("CUDA memory copies inherently leave duplicate data in both CPU and GPU
memory") and declines to exploit it because it would need semantics; content hashing needs
none.

**Feasibility: M.** The hashing itself is easy and 16 Zen-3 cores can hash far faster than
PCIe delivers, but interning changes the ownership model of the SHM tier (refcounts, ABA
against the existing `alloc_generation` scheme in `src/common/src/shm.rs:26-40`, and
release paths in the planner), so it is cross-cutting rather than local. Evaluation reuses
`run.py -b rotate-builtin` (Figs 6/7) and the Figure-9 pinned-memory sweep unchanged.

**Research value: M.** A real and measurable saving with a clean transparency story, but
its best case (two instances of the same model) is partly an artifact of the paper's
microbenchmark; on the genuinely heterogeneous mixes of Cases #1–#4 the expected gain is
near zero, which caps how much a reviewer would learn.

**Scoop check: clear.** Searched "cross-process deduplication GPU model weights pinned host
memory multiplexing 2025 2026". Related but different: [CrossPool (arXiv
2606.24506)](https://arxiv.org/abs/2606.24506) disaggregates weights/KV-cache for
multi-LLM serving and [Aegaeon (SOSP '25)](https://ennanzhai.github.io/pub/sosp25-aegaeon.pdf)
pools GPUs for concurrent serving — both are datacenter, application-integrated systems,
neither does transparent block-level dedup of a pinned staging tier.

---

## 6. Risks and open questions

1. **The evaluation harness is a second, unaudited repository pinned to a different
   commit.** `nixie-eval` recommends main-repo commit `b7466db`, while the audited clone
   is at `56f3fc1` (2026-09-06). Any add-on must be developed against whichever commit the
   harness actually drives, or the harness must be ported forward. I could not inspect
   `nixie-eval`'s code, only its README — its internal assumptions (absolute paths, GPU
   count, command server ports) are unverified.
2. **Driver 535 / CUDA ≤ 12.2 vs the authors' 580.95 / CUDA 12.9.** The build path is fine
   (`--features cuda-12` uses runtime `dlopen` of `libcuda.so`), but the *runtime* CUDA VMM
   behaviour, `cuMemHostRegister` on a 16–32 GiB `/dev/shm` mapping, and PCIe scheduling on
   an older driver are all unverified by desk review. The paper itself observed
   driver-dependent PCIe idleness on its own A5000 box (§7.3). This is the single largest
   reproduction risk.
3. **CI never builds the configuration we need.** `.github/workflows/check.yml` only runs
   `cargo check/clippy/test --no-default-features --features cuda-13`. The `cuda-12` path
   is untested in CI, and `cuda-system` would auto-detect our system CUDA 11.8, which no
   feature path targets. First build may need a small patch.
4. **Baselines are the porting bottleneck, not Nixie.** nvshare needs a source build plus
   the harness's CUDA-graph patch; TGS is container/Kubernetes-oriented and very likely
   out of reach without root — the paper itself reports TGS failing on these workloads, so
   dropping it is defensible but shrinks the comparison set. Without nvshare, the headline
   3.1–3.8× ratio cannot be reproduced at all (only the `Nixie-RR` ablation).
5. **Model scale-down changes the numbers.** Q8/Q6 → Q4 shrinks both the working set and
   the per-switch byte count, and PCIe 4.0×16 has different duplex characteristics from
   PCIe 5.0×8. Only *ratios* between systems are meaningful; the team must say so
   explicitly rather than claiming to match absolute latencies.
6. **Shared machine, large pinned allocations.** The daemon defaults to 32 GiB pinned +
   32 GiB paged (`config.rs:168-169`) and `cuMemHostRegister`s the whole SHM region
   (`init.rs:91`). On a machine with 111 GiB free and other users, this is antisocial and
   may fail; `/dev/shm` is also capped at RAM/2 by default and cannot be enlarged without
   root. Start small (`--shmem 16g`) and treat pinned-memory sweeps (Figure 9) as the
   riskiest experiment.
7. **SGLang / ComfyUI paths are the fragile ones.** SGLang 0.5.4 wants recent PyTorch CUDA
   wheels on a 535 driver (minor-version compatibility, unverified); Qwen-Image's FP8
   checkpoints have no native Ampere kernels and will be upcast. Prefer llama.cpp-only
   figures (11-Z-Image, 12, 13, 14, 15) for anything on the critical path.
8. **A3's transparency invariant.** Allowing two applications to be `Enable`d at once
   weakens the guarantee that no in-flight kernel touches migrated memory
   (§4 "valid memory access during migration"); the design must ensure that admitting a
   co-resident app never triggers eviction of the incumbent, or the safety argument
   breaks. This is the main correctness hazard in the highest-value add-on.
9. **Single-user threat model.** §8 "Security" notes all processes share one UID and one
   pinned region. Fine for a course project on a personal-style workload, but worth stating
   if the team runs on a shared departmental machine.
10. **Artifact badge is "Available" only** (`pages/page-02.png`). No Functional or
    Reproduced badge was found (the USENIX presentation page returned HTTP 403), so no
    third party has certified that these scripts reproduce these figures.

---

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; `pages/page-NN.png` for figures)
- Abstract, §1 Introduction — problem, contributions, "source available at
  github.com/XOR-op/Nixie" (pp. 2–3).
- §2.1–§2.2 — consumer workload characterisation; four UVM limitations; Figure 1
  (half-duplex page-fault datapath) (pp. 3–4).
- §3 Overview, Figure 2 (Shim + Daemon architecture, 6-step switch protocol) (pp. 4–5).
- §4 Supporting unmodified CUDA apps — `LD_PRELOAD`, CUDA VMM for stable VAs,
  synchronise-before-migrate, graph-capture handling, `cudaMemGetInfo` rewriting (p. 5–6).
- §5.1, Figure 3 — 128 MB chunks / 2 MB blocks, four tiers, one copy per chunk (p. 6).
- §5.2, Figures 4–5 — planner/orchestrator split, streaming window, straggler handling
  (pp. 6–7).
- §6.1 — 100 ms idleness timeout, NVML's ~600 ms lag (pp. 7–8).
- §6.2, Algorithm 1 — soft priority recovery, pending-time factor `R < 1/N` (p. 8).
- §6.3 — `T = 8 s`, `S = 4 s`, doubling per level, prefetch of queue head (p. 8).
- §7 Setup & Baselines — RTX 5090 ×2, CUDA 12.9 / driver 580.95.05, app and model
  versions, ~10 kLOC Rust (p. 9).
- §7.1, Figure 6 — context-switch TTFT, 44.0–82.3 % / 29.7–36.3 % (`pages/page-09.png`).
- §7.1, Figure 7 — bi-directional throughput ≈2× UVM (`pages/page-09.png`).
- §7.1, Figures 8–10 — oversubscription sweep; pinned-memory vs TTFT (33.2–40.2 %);
  ResNet launch overhead; `cudaMalloc` latency (p. 10).
- §7.2 Case #1, Figure 11 — 1.3–1.4× over nvshare; TGS fails (p. 11).
- §7.2 Case #2, Figure 12 — KVCOMM multi-agent, 1.6× (p. 11).
- §7.2 Case #3, Figure 13 — code completion 3.1–3.8×; −23.5 % background throughput in
  the frequent regime; `Nixie-RR` ablation (pp. 11–12).
- §7.2 Case #4, Figure 14 — three batch jobs, 85 % of ideal, +5 % auto-prefetch (p. 12).
- §7.3, Figure 15 — **RTX A5000 24 GB testbed**, Q4 models, 3.4× over nvshare, 73 % of
  2 GPUs, older-driver PCIe idleness note (`pages/page-13.png`).
- §8 Discussion — white-box/immutable-data future work; policy extensibility; co-locating
  with small models; security (`pages/page-13.png`).
- §9 Related work — PipeSwitch, ServerlessLLM, Aegaeon, Prism, DeepUM, G10, XSched,
  Agentix (pp. 13–14).
- Artifact badge "Artifact Evaluated — Available", `pages/page-02.png` (top right).

**Repository** (paths relative to `repo/`)
- `README.md` (:22-31 features + paper link, :39-47 build, :51-75 usage, :83-91 BibTeX)
- `docs/cli.md` (:8-10 LD_PRELOAD/socket, :43-48 defaults, :224-234 prefetch runtime
  caveats, :294-312 config keys)
- `Cargo.toml` (workspace + dependency pins), `Cargo.lock`
- `src/common/Cargo.toml`, `src/daemon/Cargo.toml`, `src/sidecar/Cargo.toml`
  (cuda-system / cuda-12 / cuda-13 feature matrix)
- `src/common/src/constant.rs:1-9` (2 MB / 128 MB / reservation sizes)
- `src/common/src/shm.rs:14-120` (allocation table, physical handle list, generations)
- `src/common/src/shm_buffer.rs:22` (`shm_open`)
- `src/sidecar/build.rs:21-81` (nvcc detection under `cuda-system`)
- `src/sidecar/src/init.rs:84-99` (`cuMemHostRegister` of the SHM region)
- `src/sidecar/src/intercept.rs:46-120` (`cudaMemGetInfo`, `cudaMalloc` hooks)
- `src/sidecar/src/schedule/mod.rs:78-123` (`set_allow_running`), `:199-217` (sync
  bracketing), `:219-285` (idleness monitor thresholds), `:288-303`
  (`require_reserved_memory`)
- `src/daemon/src/config.rs:80-89` (`Config`), `:158-179` (defaults 32 GiB/32 GiB, 0.95),
  `:181-256` (init/validation)
- `src/daemon/src/runtime/schedule/policy.rs:74-93` (quantum/cooldown ladders),
  `:149-160` (`compute_cooldown`, hard-coded 16 GB/s), `:239-303` (`schedule_pop`,
  auto-prefetch trigger), `:336-389` (`construct_prefetch_plan`), `:392-474`
  (`update_priority` = Algorithm 1), `:489-521` (`compute_prioritization`), `:524-556`
  (`compute_can_preempt`), `:590-1150` (unit tests)
- `src/daemon/src/runtime/schedule/statistics.rs:108-131` (`History`), `:138-301`
  (`ClientStatistics`)
- `src/daemon/src/runtime/schedule/scheduler.rs:47` (`ActiveClientState`), `:250-367`
  (`handle_sched_request`: Disable → migrate → Enable → cooldown), `:369`
  (`handle_prefetch_request`), `:531` (`perform_migration`)
- `src/daemon/src/runtime/schedule/control.rs:11-22` (control request enum)
- `src/daemon/src/runtime/migration/migration_plan.rs:129-427`
  (`realtime_migrate_task`; `:176-177` 2-block safety margin, `:185-193` free-block and
  candidate setup, `:286-291` arbitrary victim pop), `:430+` (`local_prefetch_task`)
- `src/daemon/src/runtime/migration/execution.rs:257` (`run`), `:476`
  (`run_for_device`), `:546` (`device_to_host_transfer`), `:632`
  (`host_to_device_transfer`), `:829` (`backend_to_shm_transfer`), `:1356-1472` (tests)
- `src/daemon/src/runtime/migration/{shm_buffer,hostmem_buffer,storage_buffer,channel}.rs`
- `.github/workflows/check.yml:46,73,93` (CI builds only `--features cuda-13`)
- `repo_facts.json` (head `56f3fc1`, 2026-09-06; 13 159 LOC Rust; empty `red_flags`;
  12 stars, 6 forks, Apache-2.0, created 2024-03-21)

**External**
- `https://github.com/XOR-op/nixie-eval` README (fetched 2026-09-14): runners, baseline
  commits + patches, model list, and the figure→script map; pins main repo `b7466db`.
- [MSched, arXiv 2512.24637](https://arxiv.org/abs/2512.24637) — proactive memory
  scheduling for GPU multitasking (A2/A4 scoop check).
- [Detshare / Vitamin-E, arXiv 2603.15042](https://arxiv.org/abs/2603.15042) and
  [VUDA, arXiv 2605.01352](https://arxiv.org/abs/2605.01352) — transparent spatial GPU
  sharing (A3 scoop check).
- [XSched, USENIX ATC '25](https://www.usenix.org/system/files/atc25-fan.pdf) — cited by
  the paper as [28].
- [Aegaeon, SOSP '25](https://ennanzhai.github.io/pub/sosp25-aegaeon.pdf) and
  [CrossPool, arXiv 2606.24506](https://arxiv.org/abs/2606.24506) — A5 scoop check.
- arXiv preprint of the paper: `https://arxiv.org/abs/2601.11743`.
- `https://www.usenix.org/conference/osdi26/presentation/xu-yechen` — returned HTTP 403,
  so badge information was taken from the PDF's first page instead.
