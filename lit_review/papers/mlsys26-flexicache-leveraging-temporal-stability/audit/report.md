# FlexiCache: Leveraging Temporal Stability of Attention Heads for Efficient KV Cache Management

MLSys 2026 · Takbir, Alikhani, Dutt, Abdu Jyothi (UC Irvine) · repo `github.com/NazmulTakbir/FlexiCache`
Desk review only — nothing was built or run. Every claim below cites a paper section/figure or a repo path.

---

## 1. Paper summary

**Problem.** In LLM serving, the KV cache grows with context *and* generation length, must stay resident
in HBM for the whole request, and is re-read every decode step. That caps batch size and therefore
decode throughput (§1, §2).

**Prior art and the gap.** Eviction methods (StreamingLLM, SnapKV, MorphKV) permanently discard KV, which
hurts long *generation* because a discarded token can become important later. Quest re-selects top-K pages
every step over the *full* KV cache — accurate, but the whole cache must stay on the GPU, so no memory is
saved. LServe converts ~half the heads to streaming heads, which is again permanent eviction for those
heads (§1, §6).

**Key observation (§2.1–§2.3).** KV heads differ in how *temporally stable* their top-K page set is across
consecutive decode steps. The paper defines a random-corrected overlap (RCO) that subtracts the
hypergeometric chance overlap `K/N_t`, and a per-head temporal-stability score `TS = mean RCO over a
W=16-step window` (§2.2). Figure 1 (layer 4 of Llama-3.1-8B, SPACE task) shows some heads hold high RCO
that decays slowly while others sit near zero. Crucially the identity of the unstable heads is
*model-intrinsic*: cross-task overlap of the bottom-quartile head sets averages 0.83 / 0.83 / 0.76 / 0.81
for Llama-3.1-8B, Mistral-7B-v0.2, Mistral-Small-24B and Qwen2.5-32B (Table 1, Table 2a–c). So one offline
profiling run per model suffices (§2.3; footnote 1: ~2 h for Llama-3.1-8B on GovReport).

**Design (§3).** Classify the least-stable 25% of KV heads as *unstable*, the rest *stable*.

- G1 (compute): sparse decode attention over only the top-K pages per head (§3.1).
- G2 (memory): unstable heads keep their full KV on the GPU; stable heads keep only their top-K pages on
  the GPU and the full KV in pinned host memory (§3.3, Figure 3).
- G3 (I/O): unstable heads are re-scored every step (free — their KV is on the GPU); stable heads are
  re-scored every 16 steps, and only *newly promoted* pages are fetched H2D (§3.2, §3.3). Each stable page
  is offloaded exactly once (big offload after prefill, then incremental as pages fill). Transfers run on
  a low-priority background stream with capped grid size and chunking, using a custom UVA kernel that
  reads/writes pinned host memory directly to avoid CPU-side gather/scatter (§3.3, Figure 4). The
  scheduler pauses *only* the request being reloaded; ~1/16 of the batch is idle at any time.
- Scoring reuses Quest's per-page min/max key vectors, but stores them in a dedicated **MinMax cache**
  that stays on the GPU even when the page itself is offloaded — that is what makes an offloaded page
  scoreable and recallable (§3.2).
- G4 (accuracy): nothing is ever discarded, so top-K selection always ranges over the whole KV.
- Block-table machinery (§3.4): per-(layer, head) block tables (B,L,H,N) with **dirty-range** H2D copies,
  **physical block recycling** during rerank via a fused CUDA kernel, and a **null block** to keep the
  table dense/vectorizable.

**Eval setup (§4.1).** 1× H100 94 GB, 2× EPYC 9554, 1.1 TB DDR5, **PCIe 5.0 @ 64 GB/s**, 180 GB of host
memory for the KV cache, PyTorch 2.7 / CUDA 12.8. Models: Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.2
(+ Mistral-Small-24B, Qwen2.5-32B for some results). Baseline: stock vLLM Triton Flash-Decoding for system
numbers; LServe for accuracy-under-sparsity. Datasets: LongBench, L-Eval.

**Headline numbers.**
- Accuracy: LongBench avg ratio to dense = 1.00 (Llama) / 0.99 (Mistral) at K=64 pages (1024 tokens),
  64 unstable heads, rerank 16 (Table 3). L-Eval avg ratio 0.99–1.00 at budget 2048, vs LServe 0.94
  (Table 5). Ablations in Table 5 show reranking is worth +0.10 and unstable heads +0.03.
- Throughput: 1.38–1.55× (Llama) and 1.44–1.46× (Mistral) token throughput over vLLM, gain growing with
  output length (Figure 5a,b); 1.46×/1.41× request throughput (Figure 5c); 1.37×/1.33× for the 24B/32B
  models (Figure 7).
- Online: mean TPOT 34.6 ms vs 71.5 ms at 0.4 req/s (2.1×); vLLM's TTFT collapses past 0.35 req/s while
  FlexiCache stays flat (Figure 6a–c).
- Microbenchmarks: decode kernel up to 4× at batch 40 (Figure 8); stability-aware rerank 2.44× faster than
  reranking all heads every step (Figure 9); >70% GPU KV savings at ≥20k sequence length (Figure 10).
- Knob sensitivity: Table 6 — retention 0.9932 (25% unstable, interval 16) degrading gracefully to 0.9628
  (6.25% unstable, interval 32).

**Stated limitations / future work (§5).** Two-level GPU–CPU hierarchy only (NVMe/distributed pools
deferred); binary stable/unstable classification chosen "for system simplicity" even though stability is a
continuous spectrum and multi-tier intervals/budgets "could further specialize KV management policies"
(§2.3); composition with prefill/decode disaggregation and speculative decoding untested; cluster-level
scheduling with stability signals is open.

---

## 2. Artifact audit

### 2.1 Structure

The repo is a **fork of vLLM 0.8.2** (`README.md:125`) with FlexiCache patched in, plus three
FlexiCache-specific top-level directories. 2164 files, 106 MB, 350k lines of Python / 24k `.cu` / 16k
`.cuh` (mostly inherited vLLM). HEAD `ab0f495`, 2026-03-08. Apache-2.0. 3 stars, 0 open issues — it is a
release-and-forget artifact drop, created 2026-03-04, last pushed 2026-03-09.

### 2.2 Paper component → code path

| Paper component | Code |
|---|---|
| Head classification, stable/unstable sets (§2.3, §3.3) | `vllm/v1/flexicache/config.py` (`FlexiCacheConfig`, singleton; `_build()` at :104 turns the head list into per-layer masks/tensors) |
| Precomputed unstable-head sets for 4 models (Tables 1–2) | `vllm/v1/flexicache/model_data.py` — literal `[layer, head]` lists, keyed `unstable-{M}-profile-{task}-topk-{K}` |
| Host-pool size, avg tokens/req, MinMax block size (§3.2, §4.1) | `vllm/v1/flexicache/config.json` (`cpu_kv_cache_size: 180` GB, `avg_num_tokens_per_req: 20000`, `minmax_key_cache_block_size: 128`) |
| MinMax page scoring `s_p = Σ max(q·k_min, q·k_max)` (§3.2) | `vllm/attention/ops/flexi_cache_triton_kernels.py:818 kernel_compute_block_scores_minmax` (+ a `_qwen32` variant at :949) |
| MinMax cache write path (prefill / decode) | same file, `store_minmax_key_cache_for_prefill:11`, `..._for_decode:107`; launched from `vllm/v1/worker/gpu_model_runner.py:2168, :2202` |
| Stability-aware rerank schedule (§3.2) | `vllm/v1/worker/gpu_model_runner.py:1449-1458` — `dec_step % rank_f == 0` selects requests to rerank; `write_top_k_blocks:1085` / `write_top_k_blocks_post:1112` in `flexi_cache_triton_kernels.py` do the actual top-K |
| Sparse decode attention on top-K pages (§3.1) | `flexi_cache_triton_kernels.py:376 kernel_paged_attention_2d_flexicache`, `:555 ..._3d_flexicache`, `:718 kernel_reduce_segments_flexicache`; wired in `vllm/v1/attention/backends/triton_attn.py:191-200` |
| Hierarchical placement + per-(layer,head) allocation (§3.3, §3.4) | `vllm/v1/core/kv_cache_manager.py` (per-layer `BlockPool`s at :67-73, `allocate_slots` at :266+), `vllm/v1/core/block_pool.py:29-49` (separate GPU + CPU free queues) |
| GPU/CPU/MinMax pool sizing (§3.3) | `vllm/v1/core/kv_cache_utils.py:643-704`; per-layer weights from `config.py:148-173`; **hard floor** `min_blocks_per_gpu_layer` at `config.py:76-77` with fallback + `ValueError` at `:183-193` |
| Pool allocation (pinned host, UVA registration) | `gpu_model_runner.py:1985-2045` (`torch.zeros(..., pin_memory=True)` at :2002, `register_cpu_kv_cache_pinned` at :2045) |
| UVA D2H offload kernel, no CPU gather/scatter (§3.3) | `vllm/v1/flexicache/kernels/cuda/kv_d2h_tx_gpu_mapped.cu` (`build_pairs_kernel:17`, `d2h_copy_blocks_kernel:155`, `cudaHostRegister/cudaHostGetDevicePointer` at :216-224) |
| UVA H2D reload kernel | `vllm/v1/flexicache/kernels/cuda/h2d_copy_blocks.cu` |
| Physical block recycling during rerank (§3.4) | `vllm/v1/flexicache/kernels/cuda/topk_swap_map.cu`; called at `gpu_model_runner.py:2313-2325` |
| Dirty-range block-table H2D (§3.4) | `vllm/v1/flexicache/kernels/cuda/block_table_h2d_dirty.cu`; `vllm/v1/worker/block_table.py` (`build_dirty_ranges`, `finalize_commit`), driven from `gpu_model_runner.py:2139-2164` |
| Overlap / pause-the-reloading-request (§3.3, Figure 4) | `gpu_model_runner.py:2294-2372` (`reload_kv_cache_h2d`, background stream, `poll_finished_kv_cache_reloads`) + `vllm/v1/core/sched/scheduler.py:115-122, 172-175, 601-603, 716-727` (`kv_reload_inflight`, `deferred_finish_for_reload`) |
| CLI knobs | `vllm/engine/arg_utils.py:125-128, 512-529` → `--enable-flexicache --num-unstable-heads --rerank-frequency --topK-budget --unstable_heads_profile_task` |
| Stability analysis (Figure 1, Tables 1–2) | `TopK-Analysis/{analyze_head_stability,stability,similarity,preprocess}.py`, `overlap.ipynb`, `parse_output.ipynb`, `run_analysis.sh` |

This is the real system, not a stub. The FlexiCache-specific surface is ~200 `flexicache` references across
23 vLLM files plus 4 hand-written CUDA kernels and ~1200 lines of Triton.

### 2.3 Evaluation scripts

Present and push-button:

- `FlexiCache/LongBench.sh <Llama8b|Mistral7b|Mistral24b|Qwen32b>` → `benchmarks/FlexiCache/Language_Modelling/LongBench/{Llama8b.sh,run_benchmark.py,eval.py,make_longbench_table_csv.py}`. Correctly avoids profile leakage: GovReport is evaluated with the `paper_assistant` profile and everything else with `gov_report` (`LongBench/Llama8b.sh:36-46`), matching §4.3.
- `FlexiCache/Throughput.sh <model>` → `benchmarks/FlexiCache/Throughput/{run_throughput.sh,Llama8b.sh,plot_throughput.py,generate_table.py}`, driving `benchmarks/benchmark_throughput.py --dataset-name leval` (dataset class registered at `benchmark_throughput.py:17,317,535`).
- `FlexiCache/LEval.sh <model>` for the L-Eval accuracy tables.
- `FlexiCache/README.md` + `FlexiCache/Artifact_Evaluation.pdf` reproduce the paper's Appendix A, including
  expected numbers (README Tables at :150-173 == paper Tables 7–8) and a Zenodo DOI
  `10.5281/zenodo.18918856`.

**Missing.** The instrumented run that *produces* the top-K index dumps consumed by `TopK-Analysis` is not
in the repo. `TopK-Analysis/preprocess.py:40` expects `Data-Sorted/<model>/<dataset>/sample-XXX/decode-step-{N}-prompt-len-{P}.pt`
tensors of shape `[L,H,K]`, and nothing in `vllm/` writes them (grep for `Data-Sorted`/dump under `vllm/`
returns only unrelated upstream hits). Consequences:
1. Figure 1 and Tables 1–2 (the paper's central *observation*) are **not** reproducible as shipped.
2. A new model cannot be profiled without first writing the dumper.
3. Table 6's ablation over unstable-head fraction is **not** reproducible: `model_data.py` only ships
   `M ∈ {64 (Llama/Mistral-7B), 80 (Mistral-24B), 128 (Qwen32B)} × topk ∈ {64,128} × task ∈ {gov_report, paper_assistant}`,
   and `config.py:88-95` asserts the exact key exists, so `--num-unstable-heads 16` or `32` raises.

### 2.4 Build route on *this* machine

Documented route (`README.md:127-142`, `FlexiCache/README.md:85-110`): conda py3.12 → `export CUDA_HOME=/usr/local/cuda-12.8` → `pip install -e .` (30–60 min) → `pip install -r flexicache_requirements.txt` → `huggingface-cli login`. All user-space; the many Dockerfiles at the repo root are inherited from upstream vLLM and are *not* used by the artifact instructions.

Deltas needed here:

1. **CUDA toolkit.** System `nvcc` is 11.8; the pins want 12.4/12.8. Install `cuda-toolkit=12.4` into the
   conda env and point `CUDA_HOME`/`CUDACXX` there. Driver 535 (CUDA ≤12.2 native) runs cu124 wheels
   through CUDA minor-version compatibility — standard, but a risk worth watching for any PTX/JIT path.
2. **GPU arch.** `README.md:151` hardcodes `TORCH_CUDA_ARCH_LIST="9.0;9.0a"` (Hopper) for the runtime
   `torch.utils.cpp_extension.load` of the four `.cu` files (`gpu_model_runner.py:321-363`). Must become
   `"8.6"` for the A5000. The README explicitly tells you to (`:167`). I read all four kernels
   (`kv_d2h_tx_gpu_mapped.cu`, `h2d_copy_blocks.cu`, `topk_swap_map.cu`, `block_table_h2d_dirty.cu`):
   plain `uint4` vectorised copies, `atomicAdd`, `__threadfence_system`, `cudaHostRegister`. Nothing
   Hopper-specific, nothing FP8 — they should compile and run on sm_86.
3. **Build shortcut.** `csrc/` appears untouched by FlexiCache (all FlexiCache CUDA lives under
   `vllm/v1/flexicache/kernels/cuda/` and is JIT-loaded), so `VLLM_USE_PRECOMPILED=1 pip install -e .`
   (`setup.py:331,545,643,673`) should skip the long C++ build. Fallback is the full source build,
   comfortable on 16 cores / 125 GB RAM.
4. **`numactl`.** `benchmarks/FlexiCache/Throughput/Llama8b.sh:90` prefixes every run with
   `numactl --cpunodebind=0 --membind=0`. This machine is single-NUMA and `numactl` may not be installed —
   delete the prefix (the script's own comment at :84-88 says it is a no-op on single-socket systems).
5. **`fastchat`.** `flexicache_requirements.txt:4` asks for `fastchat`, but
   `LongBench/run_benchmark.py:8` imports `from fastchat.model import get_conversation_template`, which is
   provided by the **`fschat`** distribution. PyPI `fastchat` is an unrelated 0.1.0 stub (2024-02-29).
   Expect to substitute `fschat` (or stub the import — it is only used for vicuna/longchat prompts, which
   none of the four supported models take, `run_benchmark.py:78-97`).

### 2.5 Dependency pins and age

`requirements/cuda.txt:8-11` torch==2.6.0 / torchvision 0.21 / torchaudio 2.6; artifact appendix A.3.3
torch 2.6.0+cu124, Triton 3.2.0, Transformers 4.50.0, Datasets 3.6.0, Python 3.12; `flexicache_requirements.txt`
pins `transformers==4.50.0`, `datasets<4`, `huggingface_hub<1`. These are ~1 year old as of 2026-09 but all
still installable from PyPI, and the `<4`/`<1` caps are already defensive. Nothing abandoned.

### 2.6 Data / model sources

- LongBench: `load_dataset('zai-org/LongBench', <task>)` (`run_benchmark.py:61-63`) — public HF.
- L-Eval: vendored harness at `benchmarks/FlexiCache/Language_Modelling/L-Eval/LEval/` (MIT); dataset public.
- Throughput prompts: **bundled in-repo**, `benchmarks/FlexiCache/Throughput/Prompts/prompts-Llama-3.1-8B-Instruct.json`
  and `...-Mistral-7B-Instruct-v0.2.json` — no download, which removes a whole class of failure.
- Weights: `config/model2path.json` → `meta-llama/Llama-3.1-8B-Instruct`, `mistralai/Mistral-7B-Instruct-v0.2`,
  `mistralai/Mistral-Small-24B-Instruct-2501`, `Qwen/Qwen2.5-32B-Instruct`. The first two are public but
  behind a click-through HF licence (artifact A.2: "requires ... a configured Hugging Face account" and
  "must accept the model agreement"). Free, but a gate, and `env.md` only guarantees non-gated HF reach.
- Head profiles: shipped in `model_data.py`; no external download.

---

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper §1 final bullet and Artifact Appendix A.3.1 both give `https://github.com/NazmulTakbir/FlexiCache`; the GitHub account matches the first author (`ntakbir@uci.edu`, paper p.1). The repo README opens with "Accepted to MLSys 2026". It contains the full system — `vllm/v1/flexicache/` (config + 4 CUDA kernels), the sparse-decode and MinMax-scoring Triton kernels in `vllm/attention/ops/flexi_cache_triton_kernels.py`, hierarchical allocation in `vllm/v1/core/{kv_cache_manager,block_pool,kv_cache_utils}.py`, reload/pause scheduling in `vllm/v1/core/sched/scheduler.py` — plus eval scripts and `FlexiCache/Artifact_Evaluation.pdf` with Zenodo DOI `10.5281/zenodo.18918856`. Not a placeholder, not plotting-only. |
| `H2_no_root` | **pass** | Install is conda + `pip install -e .` (`FlexiCache/README.md:85-110`); no kernel module, eBPF, `perf`, KVM, `/proc/sys` or hugepage step anywhere in the FlexiCache path. The 24 `sudo` hits and 147 `docker` hits in `repo_facts.json` are all in upstream vLLM Dockerfiles/`docs/source/**` that the artifact never invokes. Host pinning uses `torch.zeros(pin_memory=True)` (`gpu_model_runner.py:2002`) and `cudaHostRegister` (`kv_d2h_tx_gpu_mapped.cu:218`), both driver-mediated and not root-gated. Only `numactl` (`Throughput/Llama8b.sh:90`) is an external binary, and it is optional on a single-NUMA host. |
| `H3_hardware_fit` | **pass** (with a documented scale-down and one residual risk) | Single GPU by construction: every script passes `--tensor-parallel-size 1`; the `multi_gpu` grep hits are exactly those lines. But the artifact demands 80 GB HBM minimum, ≥256 GB host RAM, 180 GB pinned pool and PCIe Gen5 (`FlexiCache/README.md:32-35`, paper §4.1) vs. our 24 GB / 125 GB / PCIe 4.0. Every capacity knob is exposed and data-driven: `cpu_kv_cache_size` and `avg_num_tokens_per_req` in `vllm/v1/flexicache/config.json`, `--max-model-len` / `--max-num-seqs` / `--topK-budget` on the CLI, and per-layer pool sizing derives from them (`config.py:148-193`, `kv_cache_utils.py:643-704`). With Llama-3.1-8B fp16 (16.1 GB weights) at `--max-model-len 8192`, `avg_num_tokens_per_req 8000`, `cpu_kv_cache_size 40`: the `min_blocks_per_gpu_layer` floor falls back to `ceil(8192/16)*8 = 4096` blocks/layer ≈ 1.1 GB (`config.py:186-188`), well inside the ~3.5–4.5 GB of KV budget left on a 24 GB card. At 6–8k-token prompts that still yields roughly 2× the concurrent batch of dense vLLM (FlexiCache needs ~1408 GPU blocks/layer/request vs 4096 for dense), so hierarchical placement, stability-aware rerank and sparse decode are all genuinely exercised. Residual risk: the `ValueError("Not enough GPU blocks...")` at `config.py:190-193` is a hard abort, and PCIe 4.0 (~32 GB/s) halves the bandwidth the reload pipeline (§3.3) assumes, so the *ratio* may not hold even if the system runs. |
| `H4_obtainable_deps_data` | **pass** | Deps are PyPI/conda user-space (`requirements/cuda.txt`, `flexicache_requirements.txt`, artifact A.3.3); nothing needs a system package. LongBench downloads from `zai-org/LongBench` (`run_benchmark.py:61-63`); L-Eval is vendored under `benchmarks/FlexiCache/Language_Modelling/L-Eval/LEval/`; the throughput workload is a **bundled JSON** (`benchmarks/FlexiCache/Throughput/Prompts/prompts-Llama-3.1-8B-Instruct.json`); head profiles are hardcoded in `vllm/v1/flexicache/model_data.py`. No proprietary traces anywhere. Two frictions, neither a blocker: Llama-3.1-8B / Mistral-7B-v0.2 need a free click-through HF licence (artifact A.2), and `flexicache_requirements.txt:4` `fastchat` is very likely a typo for `fschat`. |

No `fail`, no `unclear`.

---

## 4. Reproduction plan

**Primary target.** Paper **Table 3** (LongBench accuracy retention, Llama-3.1-8B, avg FlexiCache/dense
ratio = 1.00) = artifact §A.6.1 **Table 7** (8-task subset), produced by
`bash FlexiCache/LongBench.sh Llama8b` → `benchmarks/.../LongBench/longbench_table.csv`. This is the claim
that FlexiCache's never-discard hierarchy preserves model quality at a 1024-token attention budget.

**Stretch target.** Paper **Figure 5(a)** = artifact §A.6.2 **Table 8** (token throughput vs output length,
FlexiCache-1024 vs vLLM, 1.11×→2.08×), via `bash FlexiCache/Throughput.sh Llama8b`. This is the headline
system claim and the one most at risk from our PCIe generation and HBM size.

**Scale-down.**

| knob | paper / artifact | here | why |
|---|---|---|---|
| model | Llama-3.1-8B-Instruct fp16 | same (fallback Mistral-7B-v0.2, 14.5 GB, profile also shipped) | 16.1 GB of 24 GB; both profiles present in `model_data.py` |
| `--max-model-len` | unset → 131072 (`config/model2maxlen.json:2`) | **8192–16384**, and mirror it into `model2maxlen.json` | otherwise `config.py:186-188`'s fallback floor demands ~17 GB of GPU blocks; `run_benchmark.py:136-149` does not pass `max_model_len`, so add it |
| `avg_num_tokens_per_req` | 20000 (`config.json:2`) | 6000–8000 | drives `min_blocks_per_gpu_layer` at `config.py:76-77` |
| `cpu_kv_cache_size` | 180 GB (`config.json:3`) | 32–48 GB | only 111 GiB available and the pool is pinned |
| prompt length | 10k–30k (`Throughput/Llama8b.sh:16`) | 4k–8k | fits `max-model-len` and the reduced host pool |
| `--max-num-seqs` | 64 (throughput) / 15 (LongBench) | 8–16 | GPU KV budget |
| `--num-prompts` | 500 | 80–150 | wall-clock |
| output lengths | 100/500/1000/1500 | 100/500/1000 first, 1500 if time | the gain grows with output length, so keep ≥500 |
| `TORCH_CUDA_ARCH_LIST` | `9.0;9.0a` | `8.6` | Ampere |

The *ratio* (FlexiCache ÷ dense, same truncation, same batch) is the quantity to compare; absolute
LongBench scores will differ from Table 3 because of the shorter truncation length.

**Steps.**
1. conda env py3.12 + `cuda-toolkit=12.4`; `export CUDA_HOME=$CONDA_PREFIX`, `CUDACXX=$CONDA_PREFIX/bin/nvcc`, `TORCH_CUDA_ARCH_LIST=8.6`.
2. `VLLM_USE_PRECOMPILED=1 pip install -e .`; if the 0.8.2 wheel is no longer fetchable, fall back to a full source build with `MAX_JOBS=12`.
3. `pip install -r flexicache_requirements.txt` with `fastchat` → `fschat`.
4. HF: accept the Llama-3.1 licence, `huggingface-cli login`, pre-download weights (~16 GB) and LongBench.
5. Edit `vllm/v1/flexicache/config.json` (`cpu_kv_cache_size`, `avg_num_tokens_per_req`); add `max_model_len` to the `LLM(...)` call in `LongBench/run_benchmark.py:136`; drop `numactl` from `Throughput/Llama8b.sh:90`; lower `BATCH_SIZE` in `LongBench/Llama8b.sh:16`.
6. Smoke test with the README's `vllm serve ... --enable-flexicache` one-liner on a short prompt — this is where the `config.py:190-193` abort, the JIT `.cu` build, and the pinned-pool allocation will surface.
7. Dense baseline first (`--flexicache` off), then FlexiCache, on 3–4 LongBench tasks; compute the ratio.
8. Throughput sweep at reduced `--num-prompts`, alternating dense/FlexiCache per output length.

**Effort.** ≈ 5 person-days + ≈ 20 GPU-hours. Breakdown: 1 day env/build, 1.5 days memory-budget surgery
and debugging the block-floor/pinned-pool path, 0.5 day harness edits, 2 days running + analysis.
Accuracy subset ~4 GPU-h, throughput sweep ~10 GPU-h, ~6 GPU-h of retries.

**Level: M.** Not **H**, because the artifact's stated hardware minimum (80 GB HBM, 256 GB host RAM,
PCIe Gen5) is 3× our GPU memory, 2× our RAM and 2× our interconnect bandwidth, so the configuration must be
re-derived rather than replayed, and the `min_blocks_per_gpu_layer` check is a hard abort that reading the
code cannot prove satisfiable at any given context length. The throughput *ratio* in particular depends on
the reload completing inside one decode step (§3.3), an assumption tuned for 64 GB/s. Not **L**, because
every script, config file, prompt corpus and head profile needed for both headline results is in the repo,
all the knobs that must change are plain config values or CLI flags, the CUDA is arch-generic, the pins are
installable, the eval harness emits the exact CSVs the appendix promises, and the artifact went through
MLSys AE with a Zenodo archive.

---

## 5. Add-on ideas

### A1. Per-head, drift-triggered rerank intervals (replace the single global interval-16)

- **Hypothesis.** We hypothesize that giving each KV head its own rerank deadline, driven by its *online*
  measured top-K drift, improves LongBench/L-Eval accuracy retention at equal throughput (or improves
  throughput at equal retention) compared with FlexiCache's binary stable/unstable split plus a fixed
  16-step interval, under long-context long-generation workloads.
- **Mechanism.** At every rerank the system already holds both the previous and the new top-K sets on the
  GPU — `self.input_batch.old_top_k_blocks` and `self.input_batch.top_k_blocks` are passed side by side
  into the swap-map kernel. Add a small kernel that, per (layer, head), computes the random-corrected
  overlap between them (the paper's own RCO formula, §2.2) and folds it into an EMA. Replace the scalar
  `rank_f` test with a per-head deadline: a head is re-ranked when its predicted RCO falls below a target
  τ, with a floor and ceiling on the interval. Crucially, **leave the memory layout alone** — unstable
  heads still keep full KV on the GPU, stable heads still keep only top-K — so the block allocator and the
  pool-sizing math are untouched and the change stays inside the worker. Expose τ as a CLI flag alongside
  `--rerank-frequency`.
- **Code locations.** `vllm/v1/worker/gpu_model_runner.py` (rerank selection at `:1449-1458`, reload at
  `:2294-2364`), `vllm/attention/ops/flexi_cache_triton_kernels.py` (`write_top_k_blocks_post` at `:1112`),
  `vllm/v1/flexicache/config.py` (`RERANK_FREQUENCY` at `:139`), `vllm/engine/arg_utils.py` (`:512-529`).
- **Motivating evidence.** §2.3 verbatim: "While stability scores of heads form a continuous spectrum, we
  adopt a binary classification (stable vs. unstable) for system simplicity. In principle, a finer-grained
  categorization (e.g., multiple stability tiers with different reranking intervals or top-K budgets) could
  further specialize KV management policies." Figure 1 shows per-head RCO decaying at visibly different
  rates. Table 6 shows retention falling from 0.9932 to 0.9936/0.9628 as the interval and unstable fraction
  move, i.e. the knob matters. §4.5 closes with "Further model- or workload-specific tuning could likely
  yield additional throughput gains."
- **Feasibility: H.** Localized — one new scoring kernel, a per-head deadline array, and a changed branch;
  well under 1k LOC across three files. All required tensors already exist on the GPU at the right moment.
  Evaluable with the shipped `FlexiCache/LongBench.sh` / `LEval.sh` / `Throughput.sh` at the scale-down in §4.
- **Research value: H.** It is the exact generalisation the authors name and explicitly defer for
  control-plane-complexity reasons, so a reviewer at MLSys would want to know the answer. Both outcomes
  teach: if per-head intervals win, it is a real improvement on a published system; if the overhead eats
  the gain, that empirically *validates* the paper's simplicity argument, which is publishable as a
  negative result.
- **Scoop check: partial.** Queries: "FlexiCache arXiv 2511.00868 citing papers", "adaptive rerank interval
  sparse attention KV cache per-head budget 2026", "online runtime head classification without offline
  profiling 2026". Closest: [Predict, Reuse, and Repair (arXiv 2606.30389)](https://arxiv.org/abs/2606.30389)
  uses an EMA predictor over top-K block selections, but to hide the *selection→attention* dependency
  entirely within GPU memory — no offloading, no per-head interval scheduling, no memory hierarchy.
  [Ada-KV (arXiv 2407.11550)](https://arxiv.org/pdf/2407.11550) adapts per-head *budgets* for eviction, not
  per-head rerank *frequency* under a GPU/host hierarchy. Nothing found that adapts FlexiCache's interval.

### A2. Does temporal stability survive genuinely long generation? (4k–16k output tokens)

- **Hypothesis.** We hypothesize that FlexiCache's accuracy retention degrades monotonically as generation
  length grows from ~400 to ≥4000 tokens at a fixed 16-step rerank interval — because drift accumulates over
  many more windows — and that A1's drift trigger recovers most of the loss, on LongGenBench / LongWriter
  style long-form generation.
- **Mechanism.** Build a generation-length-swept harness on top of the existing LongBench driver: reuse
  `run_benchmark.py`'s vLLM setup but swap in LongGenBench/LongWriter prompts and `max_tokens` ∈
  {500, 1k, 2k, 4k, 8k}; report retention ratio vs. dense at each length, for rerank interval ∈ {8, 16, 32}
  and unstable fraction fixed at 25% (the only shipped profile). Then re-run with A1's adaptive trigger.
  Also instrument per-head RCO over decode-step index to see whether stability itself decays with position.
- **Code locations.** `benchmarks/FlexiCache/Language_Modelling/LongBench/run_benchmark.py`,
  `benchmarks/FlexiCache/Language_Modelling/LongBench/config/dataset2maxlen.json`,
  `benchmarks/FlexiCache/Language_Modelling/LongBench/eval.py`,
  `vllm/v1/worker/gpu_model_runner.py` (instrumentation point at `:1449-1458`).
- **Motivating evidence.** §4.3 makes the case itself: "LongBench ... has a key limitation in evaluating
  sparse attention: most tasks generate short outputs ... the average generation length is below 50 tokens".
  The paper switches to L-Eval — but its own **Table 4** shows L-Eval generations are only **81–390 tokens**.
  So the paper's central differentiator over eviction methods ("long-context, **long-generation**", §1, §7)
  is never measured beyond ~400 tokens. §1 cites LongWriter and LongGenBench ("benchmarks evaluating LLMs
  on outputs as long as 32k tokens") and then never uses them.
- **Feasibility: M.** Needs a new workload driver and scoring metric (LongGenBench's per-task checks), and
  generating 4k–8k tokens × dozens of samples × 3 interval settings × {dense, FlexiCache} is compute-heavy
  on one A5000 — but affordable at reduced sample counts (~15–25 GPU-h), and it composes with A1.
- **Research value: H.** It tests the paper's headline claim in the exact regime the paper claims to target
  and does not measure. A clean negative (stability holds out to 8k tokens) strengthens the paper; a
  positive (retention decays) identifies a real limitation and motivates A1.
- **Scoop check: partial.** Queries: "LongGenBench / LongWriter sparse attention KV cache long generation
  degradation". [SCBench (ICLR'25, arXiv 2412.10319)](https://arxiv.org/pdf/2412.10319) and
  [Retrospective Sparse Attention (arXiv 2508.09001)](https://arxiv.org/pdf/2508.09001) both show that
  long-generation tasks are far more budget-sensitive than long-input tasks — which supports the hypothesis
  — but neither evaluates FlexiCache or a head-stability-based hierarchy. No one has stress-tested
  FlexiCache's rerank interval against generation length.

### A3. Online head classification: drop the offline profiling pass

- **Hypothesis.** We hypothesize that the stable/unstable head partition estimated **online** from the
  system's own rerank-time top-K overlaps, after a short warm-up, matches the accuracy of FlexiCache's
  offline ~2 GPU-hour profile within noise on LongBench, thereby letting FlexiCache be applied to an
  unprofiled model with no offline pass.
- **Mechanism.** Warm-up phase: run the first N requests with all heads treated as unstable (full KV on
  GPU, rerank every step — this is the `--num-unstable-heads` = all configuration the code already
  supports); accumulate per-(layer,head) RCO from `old_top_k_blocks` vs `top_k_blocks`; at the end of
  warm-up freeze the bottom-quartile set and apply it to all subsequent requests. Compare the resulting set
  against the shipped `gov_report` set in `model_data.py` (set overlap, the paper's own Table 1 metric) and
  compare end-to-end LongBench retention. The complication is that `FlexiCacheConfig` is a process-wide
  singleton whose head sets drive per-layer GPU/CPU pool *sizing* at startup (`config.py:148-173` →
  `kv_cache_utils.py:671`), so the pools must be sized for the worst case and the partition swapped only at
  request boundaries.
- **Code locations.** `vllm/v1/flexicache/config.py` (`_build` at `:104`, `_populate_globals` at `:128`,
  `_get_layerwise_block_distribution_weight` at `:148`), `vllm/v1/flexicache/model_data.py`,
  `vllm/v1/worker/gpu_model_runner.py:2294-2364`, `vllm/v1/core/kv_cache_utils.py:643-704`,
  `TopK-Analysis/analyze_head_stability.py` (reference implementation of the RCO/consensus statistic).
- **Motivating evidence.** §2.3 and footnote 1 make offline profiling a per-model prerequisite (~2 h for
  Llama-3.1-8B), and §4.2 stakes the whole design on the "model-intrinsic" claim (mean cross-task overlap
  0.76–0.83, Tables 1–2). But the artifact ships only *precomputed* head sets for four models
  (`vllm/v1/flexicache/model_data.py`) and **does not ship the dumper** that feeds `TopK-Analysis`
  (`TopK-Analysis/preprocess.py:40` expects `decode-step-*.pt` files nothing in the repo writes), so today a
  fifth model simply cannot be supported — a concrete, checkable artifact gap. An online estimator both
  closes that gap and independently re-tests the paper's central claim.
- **Feasibility: M.** The measurement half is trivial (same tensors as A1), but swapping the partition
  interacts with per-layer pool sizing and the block allocator, which is cross-cutting rather than local;
  worst-case pool sizing costs GPU memory that is scarce on 24 GB. Still clearly a 10-week, 2–4-student job.
- **Research value: H.** It removes the artifact's single biggest usability limitation, and it gives an
  independent test of "head instability is a model-intrinsic characteristic" (§2.3) using a different
  estimator than the authors'. A disagreement between the online and offline sets would be a genuinely
  interesting result.
- **Scoop check: partial.** Queries: "online runtime head classification retrieval streaming heads without
  offline profiling 2026", "citing FlexiCache". [DuoAttention (ICLR'25)](https://arxiv.org/pdf/2410.10819)
  and HeadKV/Ada-KV-family work classify heads, but all via an offline optimisation/profiling pass;
  [HeadWiseKV (arXiv 2609.02029)](https://arxiv.org/html/2609.02029) does budgeted per-head residency but
  again with precomputed head roles. No work found that derives FlexiCache-style stability tiers online
  from a serving system's own rerank telemetry.

### A4. Bandwidth-aware FlexiCache for commodity PCIe 4.0 / small-HBM GPUs

- **Hypothesis.** We hypothesize that on a PCIe-4.0, 24 GB-HBM machine FlexiCache's fixed operating point
  (25% unstable heads, K=64 pages, interval 16, `CHUNK_PAIRS=8192`, `GRID_BLOCKS=32`) leaves throughput on
  the table, and that a start-up calibration that measures actual H2D block-copy bandwidth and then picks
  the transfer-shaping parameters and rerank interval recovers a measurable fraction of the gap to the
  paper's H100/PCIe-5 speedups.
- **Mechanism.** (i) A calibration pass at engine init that times the existing `h2d_copy_blocks` kernel
  over a synthetic promoted-page set at several `(chunk_pairs, grid_blocks)` points and picks the knee —
  these two values are currently hardcoded constants in the reload path. (ii) A simple cost model relating
  measured bandwidth, the observed promoted-KV volume per rerank (the paper's Table 4 reports 44–67 MB for
  Llama-3.1-8B at budget 2048) and the decode-step time, used to pick the rerank interval such that a
  reload still finishes within one decode step — the assumption §3.3 states but never checks against
  bandwidth. (iii) Report a bandwidth-sensitivity curve (throttle effective H2D bandwidth by varying
  `grid_blocks`) as the headline figure.
- **Code locations.** `vllm/v1/worker/gpu_model_runner.py:2341-2351` (the hardcoded `CHUNK_PAIRS = 8192`,
  `GRID_BLOCKS = 32` and the background-stream reload), `vllm/v1/flexicache/kernels/cuda/h2d_copy_blocks.cu`,
  `vllm/v1/flexicache/kernels/cuda/kv_d2h_tx_gpu_mapped.cu`, `vllm/v1/flexicache/config.json`,
  `benchmarks/FlexiCache/Throughput/Llama8b.sh`.
- **Motivating evidence.** §4.1 pins the testbed to "PCIe 5.0 with a peak bidirectional bandwidth of
  64 GB/s" and 180 GB of host KV cache; §3.3 asserts reloads "typically complete within one decode step" and
  that "only a small fraction of the batch (about 1/16 ...) is idle at any point" — both bandwidth-dependent
  claims. The paper contains **no** sensitivity study to interconnect bandwidth or to HBM capacity, and the
  three transfer-shaping techniques in §3.3 (low-priority stream, grid cap, chunking) are presented with
  fixed constants and no tuning methodology.
- **Feasibility: M.** The calibration harness is new code and the sweeps are GPU-hour-heavy; worse, one
  natural axis — the unstable-head fraction — is effectively frozen, because `model_data.py` only ships
  `M ∈ {64, 80, 128}` and `config.py:88-95` asserts on the exact profile key, so exploring 12.5% or 6.25%
  (paper Table 6) requires A3 or a re-written dumper first. Still fits the machine and the term.
- **Research value: M.** A portability/sensitivity study is genuinely useful — "does this design survive on
  the hardware most people actually have?" — and it directly stress-tests two unquantified assumptions. But
  a reviewer would read it as careful characterisation plus parameter auto-tuning rather than a new
  mechanism, and prefetch-to-hide-PCIe is already a crowded space.
- **Scoop check: partial.** Queries: "PCIe 4.0 vs 5.0 KV cache offloading bandwidth sensitivity",
  "prefetch predicted promoted KV pages hide host-to-device stall vLLM 2026".
  [STS (arXiv 2605.15508)](https://arxiv.org/pdf/2605.15508) prefetches KV blocks over PCIe Gen5 using
  speculative token sparsity; [vLLM Hybrid HiSparse](https://vllm.ai/blog/2026-09-08-glm53-part1-hybrid-sparse-offloading)
  and [tiered KV offloading in vLLM](https://vllm.ai/blog/2026-09-10-tiered-kv-offloading) now ship
  hot/cold GPU–host tiering for sparse MLA. None of these calibrate to measured bandwidth or study
  FlexiCache's head-stability-driven reload volume specifically, but the prefetch idea itself is taken.

*(Deliberately not proposed: an NVMe third tier. §5 suggests it, and we have 257 GB free, but
[Tutti (arXiv 2605.03375)](https://arxiv.org/html/2605.03375) and
[KVSwap (arXiv 2511.11907)](https://arxiv.org/pdf/2511.11907) already do SSD-backed KV cache, and a
~7 GB/s NVMe under a design that already strains a 32 GB/s PCIe link is unlikely to teach much here.)*

---

## 6. Risks and open questions

1. **24 GB is the binding constraint, and the failure mode is a hard abort.**
   `vllm/v1/flexicache/config.py:190-193` raises `ValueError("Not enough GPU blocks to satisfy per-layer
   minimum")` when the profiled GPU budget is below `min_blocks_per_gpu_layer × num_layers`. The floor is
   `ceil(avg_num_tokens_per_req/block_size) × num_kv_heads × 4` with a fallback to
   `ceil(max_model_len/block_size) × num_kv_heads`. With Llama-3.1's default `max_model_len = 131072` and
   the shipped `avg_num_tokens_per_req = 20000`, neither term is satisfiable on a 24 GB card holding 16 GB
   of weights. Both must be lowered by hand, and `LongBench/run_benchmark.py:136-149` does not currently
   expose `max_model_len`. I cannot verify by reading that a satisfying point exists — this is the first
   thing to test.
2. **PCIe 4.0 (~32 GB/s) vs the paper's PCIe 5.0 (64 GB/s).** §3.3's whole overlap argument rests on a
   reload finishing inside one decode step. Halving the bandwidth may push the reload past a decode step,
   in which case the scheduler's per-request pause (`scheduler.py:172-175`) stops being "about 1/16 of the
   batch" and the throughput ratio shrinks. The reproduction may show the system working but the *speedup*
   not reproducing — which is itself a legitimate Contemporary-track result, and is the motivation for A4.
3. **Pinned-memory allocation at scale.** `gpu_model_runner.py:2002` allocates the whole host KV pool with
   `pin_memory=True` and then `cudaHostRegister`s it (`kv_d2h_tx_gpu_mapped.cu:218`). CUDA pinned
   allocations normally bypass `RLIMIT_MEMLOCK`, but a 32–48 GB pinned pool on a *shared* 125 GiB machine
   (111 GiB free at measurement) is still a large, non-swappable reservation. Unverifiable by reading.
4. **The stability-observation pipeline is not reproducible as shipped.** `TopK-Analysis/` consumes
   `Data-Sorted/<model>/<dataset>/sample-*/decode-step-*.pt` (`preprocess.py:40`) that nothing in the repo
   produces. Figure 1 and Tables 1–2 cannot be regenerated, no new model can be profiled, and Table 6's
   unstable-fraction ablation is unreachable because `model_data.py` ships only `M ∈ {64, 80, 128}` while
   `config.py:88-95` asserts on the exact key. This shapes A3 and caps A4's feasibility.
5. **Gated model weights.** Artifact A.2/A.3 require accepting the Llama-3.1 licence on Hugging Face and a
   logged-in account; `env.md` only guarantees non-gated HF reachability. Free but a gate; Mistral-7B-v0.2
   is the fallback (profile shipped, 1.6 GB smaller).
6. **Small dependency/environment papercuts.** `flexicache_requirements.txt:4` `fastchat` is almost
   certainly a typo for `fschat` (PyPI `fastchat` is an unrelated 0.1.0 stub from 2024) and will break
   `run_benchmark.py:8`. `benchmarks/FlexiCache/Throughput/Llama8b.sh:90` unconditionally prefixes
   `numactl`, which may not be installed. `README.md:151` hardcodes Hopper arch flags. All trivially fixed,
   but they will all bite on day one.
7. **CUDA 12.4/12.8 wheels on driver 535.** cu124 wheels normally run on ≥525 via minor-version
   compatibility, and the four FlexiCache kernels are JIT-compiled for the local arch, so this should be
   fine — but any JIT/PTX path that assumes a newer driver is a known risk class on this machine.
8. **Model-specific kernel branch.** `flexi_cache_triton_kernels.py:949` defines
   `kernel_compute_block_scores_minmax_qwen32` alongside the generic `:818` scorer, hinting at
   shape-specific specialisation. Harmless for Llama/Mistral, but a sign that adding a fifth model may need
   more than a head profile.
9. **Unmaintained artifact.** Created 2026-03-04, last pushed 2026-03-09, 3 stars, 0 issues, 0 commits
   since. Expect no upstream help; budget accordingly.

---

## 7. Evidence index

**Paper.** §1 (motivation, prior-art gap, contributions incl. repo URL); §2 (prefill/decode, PagedAttention);
§2.1–§2.2 (temporal stability, RCO and TS definitions, Figure 1); §2.3 (model-intrinsic claim, Table 1,
binary-classification simplification and the multi-tier future-work sentence); §3.1 (G1–G4, architecture,
Figure 2, footnote 1 on 2 h profiling); §3.2 (MinMax scoring, decoupled MinMax cache, per-class rerank
frequency); §3.3 (hierarchical placement Figure 3, minimizing transfer size, overlap pipeline Figure 4,
fragmentation/UVA kernel, the three SM-contention techniques, the "pause only the reloading request"
argument); §3.4 (dirty tracking, physical block reuse, null block); §4.1 (testbed: H100 94 GB, PCIe 5.0
64 GB/s, 180 GB host KV, torch 2.7/CUDA 12.8; models; metrics; baselines); §4.2 (Table 2a–c cross-task
overlaps); §4.3 (Table 3 LongBench, Table 4 L-Eval statistics incl. 81–390-token generations and 44–67 MB
promoted KV, Table 5 L-Eval + LServe, the LongBench-is-inadequate argument); §4.4 (Figures 5a–c, 6a–c, 7);
§4.5 (Figure 8 decode speedup, Figure 9 rerank speedup, Figure 10 memory savings, Table 6 interval ×
unstable-fraction retention); §5 (future work: multi-tier/NVMe, disaggregation, cluster scheduling); §6
(related work); Appendix A.1–A.8 (artifact abstract, checklist incl. Zenodo DOI, hardware/software deps,
install, workflow, Tables 7–8 expected results, customization). Rendered pages read for figures:
`pages/page-10.png` (Figures 5–7), `pages/page-11.png` (Figures 8–10, Table 6).

**Repo paths relied on.**
`README.md` (:99-121 testbed, :125-142 install, :146-167 quick start + arch flags, :182-191 supported models),
`FlexiCache/README.md` (:28-50 hardware/software, :54-77 checklist + DOI, :85-110 install, :112-142 workflow,
:148-175 expected results, :179-287 additional experiments),
`FlexiCache/{LongBench.sh,Throughput.sh,LEval.sh,Artifact_Evaluation.pdf}`,
`flexicache_requirements.txt`, `requirements/cuda.txt`, `setup.py` (:331,:545,:643,:673 precompiled path),
`vllm/v1/flexicache/{config.json,config.py,model_data.py}`,
`vllm/v1/flexicache/kernels/cuda/{kv_d2h_tx_gpu_mapped.cu,h2d_copy_blocks.cu,topk_swap_map.cu,block_table_h2d_dirty.cu}`,
`vllm/attention/ops/flexi_cache_triton_kernels.py`, `vllm/attention/ops/chunked_prefill_paged_decode.py`,
`vllm/v1/attention/backends/triton_attn.py`,
`vllm/v1/worker/{gpu_model_runner.py,gpu_input_batch.py,block_table.py,gpu_worker.py}`,
`vllm/v1/core/{kv_cache_utils.py,kv_cache_manager.py,block_pool.py,sched/scheduler.py}`,
`vllm/v1/kv_cache_interface.py`, `vllm/engine/arg_utils.py`,
`benchmarks/benchmark_throughput.py`,
`benchmarks/FlexiCache/Throughput/{run_throughput.sh,Llama8b.sh,Prompts/prompts-Llama-3.1-8B-Instruct.json,Prompts/prompts-Mistral-7B-Instruct-v0.2.json,plot_throughput.py,generate_table.py}`,
`benchmarks/FlexiCache/Language_Modelling/LongBench/{Llama8b.sh,run_benchmark.py,eval.py,make_longbench_table_csv.py,config/model2path.json,config/model2maxlen.json,config/dataset2maxlen.json}`,
`benchmarks/FlexiCache/Language_Modelling/L-Eval/LEval/`,
`TopK-Analysis/{run_analysis.sh,analyze_head_stability.py,preprocess.py,stability.py,similarity.py,overlap.ipynb,parse_output.ipynb}`.

**External.** [arXiv 2511.00868](https://arxiv.org/abs/2511.00868) (preprint of this paper);
[MLSys 2026 proceedings entry](https://proceedings.mlsys.org/paper_files/paper/2026/hash/94bcb01789fccf15afe2764d8fe0f40e-Abstract-Conference.html)
(fetched — lists no artifact badges and no code link);
[Predict, Reuse, and Repair (arXiv 2606.30389)](https://arxiv.org/abs/2606.30389);
[Ada-KV (arXiv 2407.11550)](https://arxiv.org/pdf/2407.11550);
[DuoAttention (arXiv 2410.10819)](https://arxiv.org/pdf/2410.10819);
[HeadWiseKV (arXiv 2609.02029)](https://arxiv.org/html/2609.02029);
[SCBench (arXiv 2412.10319)](https://arxiv.org/pdf/2412.10319);
[Retrospective Sparse Attention (arXiv 2508.09001)](https://arxiv.org/pdf/2508.09001);
[STS (arXiv 2605.15508)](https://arxiv.org/pdf/2605.15508);
[vLLM Hybrid HiSparse offloading](https://vllm.ai/blog/2026-09-08-glm53-part1-hybrid-sparse-offloading);
[tiered KV cache offloading in vLLM](https://vllm.ai/blog/2026-09-10-tiered-kv-offloading);
[Tutti (arXiv 2605.03375)](https://arxiv.org/html/2605.03375);
[KVSwap (arXiv 2511.11907)](https://arxiv.org/pdf/2511.11907);
[PyPI `fastchat`](https://pypi.org/project/fastchat/) (unrelated 0.1.0 stub, confirming the `fschat` typo).
