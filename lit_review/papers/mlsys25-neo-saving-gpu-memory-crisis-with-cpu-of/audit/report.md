# NEO: Saving GPU Memory Crisis with CPU Offloading for Online LLM Inference

MLSys 2025 · Jiang, Zhou, Cao, Stoica, Yu · repo: https://github.com/NEO-MLSys25/NEO
Desk review only — nothing was built or run. Every claim below cites a paper section/figure
or a repository path.

## 1. Paper summary

**Problem.** Online LLM serving throughput scales with batch size, but batch size is capped by
GPU memory because the KV cache grows linearly with sequence length (§2.1, p2–3). The paper
calls this the "GPU memory crisis": GPU compute keeps growing while GPU memory stagnates
(§6, p11: "H100 triples the compute of A100 but with the same 80GB").

**Key idea.** Offload the *decoding attention* — both its compute and its KV cache — for a
*subset* of requests to the local host CPU. Decoding attention is the only memory-bandwidth-bound
op in the transformer and needs no model weights (§2.2, p3); the GPU/CPU memory-bandwidth gap
(600 vs ~200 GB/s) is far smaller than the compute gap (125 vs 1.2 TFLOPS), so CPU attention is
competitive where GPU attention is not. Offloading compute (not just memory) avoids the
PCIe-bound KV swapping that sinks FlexGen-style designs.

**Design.** Two mechanisms.

- *Asymmetric pipelining* (§3.1, Figs 3–5, p4–5). Two strawmen are rejected: simple offloading
  (CPU idle during linear ops) and symmetric pipelining as used by FastDecode (GPU KV memory
  unused, CPU becomes the bottleneck, sub-batches cannot be split evenly). NEO instead keeps a
  GPU-cache and a CPU-cache, assigns each prefilled request wholly to one of them, and builds two
  *deliberately unequal* sub-batches: batch-0 = all prefills + all GPU-decodes + a few CPU-decodes
  (long linear stage, short CPU stage); batch-1 = the bulk of CPU-decodes (short linear stage, long
  CPU attention stage). The two overlap, so prefill compute on the GPU hides CPU attention.
  Layer-wise swapping overlaps the KV swap-out of freshly prefilled requests with compute.
- *Load-aware scheduling* (§3.2, p6; pseudo-code in Appendix A, p14). Per iteration, the scheduler
  builds both a GPU-only schedule and a two-batch pipelined schedule, estimates `T/x` for each from
  offline-profiled cost tables plus linear interpolation, and picks the better. Constraints
  `Tca0 ≤ Tl1 + Tga0` and `Tca1 ≤ Tl0` keep the CPU from becoming the bottleneck. Scheduling
  overhead is measured at <3 ms/iteration.

**Implementation** (§4, p7). Built on SwiftLLM (a ~2K-LOC vLLM clone); ~4K lines Python + 1.5K C++.
The CPU kernel PACPU is a Torch extension whose inner loops are written in Intel ISPC (portable to
AVX2/AVX-512/Neon), using Flash-Decoding-style task partitioning along the sequence dimension.
Triton kernels were replaced with hand-written CUDA to cut launch overhead 1.2 ms → 0.6 ms/layer.
Multi-GPU TP added via Ray + NCCL.

**Evaluation setup** (§5.1, Table 1, p7). AWS g4dn.4xlarge (T4, 8-core Xeon, 64 GB),
g5.{2,4,8,16}xlarge (A10G, 2n-core EPYC, 16n GB), and a local 8×H100 box (only 2 GPUs +
1 NUMA node used). Models Llama-2-7B, Llama-3.1-8B, Llama-3.1-70B. Baselines: vLLM (with
`--enable-chunked-prefill`), SwiftLLM (= NEO's own GPU-only mode), and FastDecode+ (their
re-implementation of full offloading). Workloads: Azure LLM coding trace (AC), OpenAI
summarization comparisons (OSC), and synthetic fixed-length workloads.

**Headline numbers.**
- Fig 6 (p8): load–latency curves. +14.3 % sustained rate on 2×H100+70B at 2 s, +6.4 % on
  A10G+8B at 2 s, **+563 % on T4+Llama-2-7B at 1 s** — the T4 gain is large precisely because the
  T4's KV budget is tiny.
- Fig 9 (p9): relative throughput vs. SwiftLLM over synthetic workloads: up to 1.14× (H100),
  1.26× (A10G), 7.5× (T4). Notably NEO drops **below** 1.0 at short output lengths and decays back
  toward 1.0 at long output lengths.
- Fig 10a (p10): CPU sensitivity across g5.2/4/8/16xlarge → 12.2 %, 13.3 %, 29.7 %, **79.3 %**
  gain; peak gain tracks CPU *memory bandwidth*, not core count.
- Fig 8 (p9): FastDecode+ collapses to <60 % of the GPU-only baseline as output length grows;
  NEO never does, because it can fall back to GPU-only.
- Fig 11 (Appendix B, p14): vLLM chunked-prefill barely helps on memory-constrained GPUs.

**Stated limitations / future work** (§5.4, §6, p9–11): offline profiling is inaccurate and causes
suboptimal scheduling at long output lengths; NEO is *worse* than the baseline at short output
lengths because it speculatively offloads and swaps back; chunked-prefill integration is sketched
but not implemented ("modify step 5 … remove *chunks* of prefilling requests"); offloading dense
(non-attention) ops to the idle CPU in GPU-bound regimes is "not validated"; remote CPUs, 4/8-GPU
integration into vLLM, and energy accounting are left open.

## 2. Artifact audit

**Repo shape** (`repo_facts.json`): 63 files, 0.4 MB, 5.5 K Python + 0.8 K CUDA + 0.7 K C/C++,
Apache-2.0, 99 stars, last push 2025-06-16, not archived. Top level: `swiftllm/` (engine),
`csrc/` (CUDA/C++ Torch extension), `pacpu/` (ISPC CPU attention), `evaluation/`, `examples/`,
`docs/`, `requirements.txt`, `setup.py`.

**Provenance.** The paper's abstract (p1) gives `https://github.com/NEO-MLSys25/NEO`; the Artifact
Appendix §C.2 (p15) repeats it and adds Zenodo DOI `10.5281/zenodo.14964833`, whose record is
uploaded by first author Xuanlin Jiang and contains `NEO-master.zip` pointing at the same repo.
This is the official implementation.

**Paper component → code map.**

| paper component | code |
|---|---|
| Asymmetric pipelining, two-sub-batch forward (§3.1, Fig 5) | `swiftllm/worker/model.py:278` `_forward_pipeline`; `swiftllm/worker/layers/transformer_layer.py:430` `forward_double`, `:451` `forward_first_stage`, `:477` `forward_last_stage` |
| Load-aware scheduler, steps 1–6 + greedy mode choice (§3.2, App. A) | `swiftllm/server/scheduler.py:237` `_get_next_batch_new`, `:142` `_decide_mode_and_gen_batch` (step 5 mode comparison at `:224-234`) |
| Cost model `T ≈ L·(max{Tl0,Tca1}+max{Tl1+Tga0,Tca0})` | `swiftllm/structs.py:148` `BatchPerfData`, `swiftllm/server/scheduler.py:132` `_get_remains` |
| Offline profiling + linear interpolation (§3.2) | `swiftllm/server/profiler.py:41` `init_profile_tables` (`_profile_linr/_pref/_gdec/_cdec`), `swiftllm/perfpredictor.py:70` `TablePerfPredictor` |
| PACPU ISPC paged attention + Flash-Decoding-style task split (§4) | `pacpu/pacpu.ispc` (`qk_product`, `softmax`, `av_product`, `attn_one_seq`, `gather_output_one_seq:156`), `pacpu/core.h:222` `ispc_attention_tasks` (OpenMP task distribution) |
| GPU-cache / CPU-cache split, layer-wise swapping (§3.1) | `swiftllm/worker/block_swapper.py:12` `Swapper`, `csrc/src/block_swapping.cpp:22` `swap_blocks`, `swiftllm/server/block_manager.py:136` `BlockManager` |
| Extra KV layer used to overlap CPU-prefill swap-out | `--extra-layer-for-cprf` (`swiftllm/engine_config.py:161`), used in `transformer_layer.py:194` |
| Custom CUDA kernels replacing Triton (§4) | `csrc/src/small_kernels.cu`, `csrc/src/linear.cu`; residual Triton in `swiftllm/worker/kernels/*.py` |
| Multi-GPU TP via Ray/NCCL (§4) | `swiftllm/server/executor.py:93` `RayExecutor`, `swiftllm/worker/model.py:377` `RemoteLlamaModel` |
| FastDecode+ baseline (§5.1) | `--disable-partial-offl` (`engine_config.py:151`), server name `"fsdc"` in `evaluation/server.py:52-66` |
| vLLM / SwiftLLM baselines | `evaluation/server.py:23-51` (vLLM CLI), `"base"` = `--always-use-gpu` (`scheduler.py:399` → `_get_next_batch_old`) |

**Eval scripts present / absent.** Present: `evaluation/reproduce-fig6c.py`,
`evaluation/reproduce-fig10a.py`, plus the harness (`benchmark.py`, `server.py`, `api_client.py`,
`illustrator.py`) and two ready configs (`evaluation/configs/config-t4-7b.json`,
`config-a10-8b.json`). **Absent:** driver scripts for Figs 7, 8, 9, 10b, 11 and all H100/70B/2-GPU
results. The FastDecode+ server mode exists in code but has no reproduction script.

**Data / models.** The OSC workload is shipped pre-digested in
`evaluation/data/osc-Llama-2-7b-hf.json` (prompt lengths + `max_tokens` only); prompts are
synthesized as `[10] * input_len` (`evaluation/benchmark.py:115`), and Fig 10a's workload is fully
synthetic (`benchmark.py:82` `_get_rand_array`). **No dataset download is needed at all.** Model
weights are the only external artifact: Llama-2-7B / Llama-3.1-8B in `.safetensors` (README:106).
These are license-gated on HuggingFace, but (a) ungated community mirrors exist and (b) the engine
has `--use-dummy` (`swiftllm/engine_config.py:79`, `swiftllm/worker/model.py:156`); since prompts
are dummy token IDs and output length is forced by `max_tokens`, throughput/latency numbers do not
depend on weight values (only `config.json` is required, `swiftllm/model_config.py:57`).
The vLLM baseline does need a real tokenizer/config.

**Build route on this machine** (all user-space, no root):

1. conda env, Python 3.10–3.12, `torch>=2.4` cu121 wheel (driver 535 supports CUDA ≤12.2).
2. `conda install -c conda-forge gxx=13` for the CPU kernel; keep the system `g++ 12.2` as the
   "<13" compiler nvcc accepts. `pacpu/build.sh:2-3` looks up the literal names `g++-11` and
   `g++-13` via `which`, so two PATH shims in `~/bin` are needed (or a 3-line edit).
3. ISPC 1.23: README:17 says `sudo snap install ispc` — **substitutable**: ISPC ships prebuilt
   Linux tarballs on GitHub Releases; extract into `$HOME` and put it on PATH. CMake's
   `enable_language(ISPC)` (`pacpu/CMakeLists.txt:18`) only needs the binary.
4. CUDA toolkit ≥12.2 (Artifact §C.3.3) — system `nvcc` is 11.8, so `conda install
   nvidia/label/cuda-12.2.0::cuda-toolkit` (or `cuda-nvcc`). System cmake 3.25.1 ≥ the required 3.18.
5. `pip install -r requirements.txt`, `pip install -e .`, `pip install -e csrc`,
   `cd pacpu && bash build.sh llama2_7b 1`.
6. Edit `evaluation/server.py:21` to drop the `numactl` wrapper (single NUMA node here; the binary
   is not part of a default Debian install) and point `model_path` at the local weights.
7. For the vLLM baseline, a **second** conda env is cleanest: vLLM 0.7.3 and NEO pin different
   torch versions, and the harness starts vLLM as a separate subprocess anyway.

**Dependency pins and their age.** `requirements.txt` is loose (`fastapi>=0.111`, `ray[default]>=2.21`,
`safetensors>=0.4.3`, `transformers>=4.40`, `uvicorn>=0.29`, `vllm_flash_attn>=2.6.1`, `matplotlib`).
The sharp edge is `vllm_flash_attn`: `swiftllm/worker/layers/transformer_layer.py:8` does a
**top-level** `import vllm_flash_attn_2_cuda`, and on compute capability ≥ 8 (our A5000) the code
*takes* that path (`transformer_layer.py:277`). The standalone `vllm-flash-attn` wheels are ABI-tied
to specific torch builds (2.6.x era, torch 2.4/cu121) and are no longer maintained separately. Two
mitigations exist: pin torch to the matching version, or flip the `major >= 8` branch to use the
in-repo Triton `prefill_attention` (`swiftllm/worker/kernels/prefill_attn.py:102`), which costs some
prefill performance but removes the dependency. Everything else is current and unpinned.

**Red flags checked, not taken at face value.** The single `sudo` hit is README:17 (ispc via snap) —
substitutable as above. The 32 "multi_gpu" hits are all `tensor_parallel_size/degree` plumbing;
both shipped configs set it to `1` (`config-t4-7b.json:9`, `config-a10-8b.json:9`) and
`SingleProcExecutor` (`swiftllm/server/executor.py:61`) is the TP=1 path with no Ray actors for the
model. No Dockerfile, no kernel module, no eBPF, no `perf`, no RDMA/CXL anywhere.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper p1 (abstract) and Artifact Appendix §C.2 (p15) both name `github.com/NEO-MLSys25/NEO`; Zenodo `10.5281/zenodo.14964833` is uploaded by first author Xuanlin Jiang. The repo holds the real system — engine (`swiftllm/`), CPU kernel (`pacpu/pacpu.ispc`, `pacpu/core.h`), CUDA extension (`csrc/src/*.cu`), scheduler (`swiftllm/server/scheduler.py`), plus two reproduction scripts — not a stub or plot-only drop. |
| `H2_no_root` | **pass** | No kernel module, eBPF, `perf`, KVM, hugepage or `/proc/sys` use anywhere in the tree; no Dockerfile. The only `sudo` is README:17 (`snap install ispc`) plus Artifact §C.4's `apt install g++-13 libomp-dev numactl`, all replaceable with conda/prebuilt-tarball installs in `$HOME`. `numactl` is invoked only as an optional wrapper in `evaluation/server.py:21` and is unnecessary on this 1-NUMA-node host. Host-pinned KV memory (`swiftllm/worker/block_swapper.py:53`, `pin_memory=True`) is CUDA page-locking, which does not require root. |
| `H3_hardware_fit` | **pass** | The headline mechanism is explicitly "1 GPU + its local host CPU" (§1, p2). Both shipped configs are `tensor_parallel_size: 1`. Our 24 GB Ampere A5000 ≥ the paper's T4 (16 GB) and matches the A10G (24 GB); 16 cores/32 threads sits between the paper's g5.8xlarge (16 cores) and g5.16xlarge (32 cores), i.e. squarely inside the Fig 10a sweep. `--num-gpu-blocks-override` (`swiftllm/engine_config.py:97`; already `54` in `config-t4-7b.json:11`) lets us *pin* the GPU KV budget and so emulate the memory-constrained regime the paper's claim depends on. Weights (7–8 B, FP16 ≈ 13–16 GB) fit. Out of reach: the 70B / 2×H100 results (Figs 6a, 8, 9a, 10b) — but those are the *weakest* gains in the paper (14 %), and the single-GPU T4/A10G results carry the claim. `config-a10-8b.json:12` asks for 120 GB pinned CPU KV, which must be cut to ~40–60 GB on this shared 125 GiB box (documented `--swap-space` knob). PACPU does **not** need AVX-512: `pacpu/CMakeLists.txt:7-8` leaves `ISPC_TARGETS` commented out (host-detected) and README:102 requires only "CPU with AVX2 support" — Zen 3 qualifies. |
| `H4_obtainable_deps_data` | **pass** | Workload data is *in the repo*: `evaluation/data/osc-Llama-2-7b-hf.json` for Fig 6c, and Fig 10a is synthetic (`evaluation/benchmark.py:92`). Prompts are dummy tokens (`benchmark.py:115`, `:101`), so no dataset licence issue. All deps install in user space: torch/ray/fastapi/transformers via pip, gxx-13 + CUDA 12.2 via conda, ISPC 1.23 from its GitHub release tarball. Model weights are gated on HF but have ungated mirrors, and `--use-dummy` (`swiftllm/engine_config.py:79`) removes the dependency entirely for performance measurement. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** **Figure 6c** (p8) — the T4 + Llama-2-7B + OSC load–latency curve, supporting the
paper's strongest claim: *on a GPU whose KV budget is tiny, CPU offloading sustains ~6× the request
rate of vLLM at equal per-token latency* (§5.2: "563 % higher on T4 (at 1 s latency)"). Driver
exists: `evaluation/reproduce-fig6c.py`. Secondary target: **Figure 10a** (p10) via
`evaluation/reproduce-fig10a.py`, which reproduces the "x16large" line (79.3 % gain) — our
16-core/32-thread host is the closest analogue.

**Scale-down.** We do not have a T4, so reproduce the *claim* rather than the absolute curve:
keep `config-t4-7b.json`'s `num_gpu_blocks_override: 54` (= 864 KV tokens on GPU) so the A5000 is
artificially starved exactly like the T4, and compare NEO vs. vLLM **on the same machine** — which
is what both scripts already do. Absolute req/s will be higher than the paper's (A5000 compute >
T4), so the falsifiable statement is the *ratio* of sustainable rates at a fixed latency target, not
the raw rates. `reproduce-fig6c.py:21-22` already sweeps a reduced rate list and
`benchmark.py:114` already truncates the trace to 100 requests. For Fig 10a: drop `swap_space` from
120 → 48 GB (`config-a10-8b.json:12`), keep `num_data = 2000` (the script warns not to go below 800),
and trim `output_lens` (`reproduce-fig10a.py:30`) to 3 points for a first pass.

**Steps.**
1. conda env: python 3.10, torch 2.4.x+cu121, `vllm-flash-attn` matching that torch (fallback: flip
   `transformer_layer.py:277` to the Triton path), ray, fastapi, uvicorn, transformers, safetensors.
2. conda `gxx=13` + CUDA 12.2 toolkit; PATH shims named `g++-11` (→ system g++ 12.2) and `g++-13`.
3. ISPC 1.23 tarball → `$HOME/local/ispc/bin` on PATH.
4. `pip install -e . && pip install -e csrc && (cd pacpu && bash build.sh llama2_7b 1)`.
5. Fetch an ungated Llama-2-7B mirror in `.safetensors`; set `model_path` in
   `evaluation/configs/config-t4-7b.json:3`.
6. Strip `numactl` from `evaluation/server.py:21`; second conda env for the vLLM baseline server.
7. `python evaluation/reproduce-fig6c.py` (first run spends ~10 min in `ModelProfiler`
   grid-profiling — `swiftllm/server/profiler.py`; cached to `profile_results/`).
8. Then `reproduce-fig10a.py` with the reduced `swap_space`.

**Effort.** ≈ 6 person-days (the toolchain — gxx-13 + ISPC + CUDA 12.2 + the torch/vllm-flash-attn
ABI pin — is most of it) + ≈ 20 GPU-hours (profiling passes, the reduced Fig 6c sweep, and a
trimmed Fig 10a sweep; Artifact §C.2 budgets 10–15 h for full reproduction).

**Level: M.** Not H, because four separate toolchain hazards must be cleared by hand
(two GCC versions under exact names, an ISPC install the README only documents via snap, a CUDA
toolkit newer than the system's 11.8, and an unmaintained `vllm_flash_attn` ABI pin), because the
target GPU differs from the paper's and the headline config must be emulated via
`--num-gpu-blocks-override`, and because `config-a10-8b.json`'s 120 GB pinned swap space does not
fit this shared host. Not L, because the exact figure has a released driver script, the workload
ships inside the repo, the config files are checked in, the tunable knobs are all CLI flags, and
the mechanism's design point (1 GPU + host CPU) is exactly this machine.

## 5. Add-on ideas

### A1 — Chunked-prefill-aware load-aware scheduling

- **Hypothesis.** We hypothesize that replacing NEO's all-or-nothing prefill admission with
  *chunked* prefill admission inside the asymmetric pipeline improves sustained throughput at a
  fixed per-token latency target under long-prompt workloads (input ≥ 4 K tokens) on a
  memory-constrained GPU, compared with NEO as published.
- **Mechanism.** Give `Request` a `prefilled_len` so a prompt can be admitted in chunks; in
  scheduler step 3 admit `min(chunk, remaining_prompt)` tokens instead of whole prompts; in step 5
  (`_decide_mode_and_gen_batch`, the `while batches[0].get_num_prefs()` loop) shrink the *chunk
  size* rather than evicting an entire prefill request, giving continuous rather than discrete
  control of `Tl0`; defer the KV swap-out of a CPU-request until its last chunk completes
  (`_swap_out_blocks`). The cost tables are already parameterised by token count `S`
  (`perfpredictor.get_pref_T`), so chunk sizes are interpolated for free. Add a long-prompt
  workload by raising `input_len` in the synthetic generator.
- **Code locations.** `swiftllm/server/scheduler.py:286` (step 4, prefill admission loop),
  `swiftllm/server/scheduler.py:217` (step 5, prefill reduction),
  `swiftllm/structs.py:226` (`add_pref` / `pop_pref`),
  `swiftllm/server/block_manager.py:79` (`alloc`, `omit_last` semantics),
  `swiftllm/worker/layers/transformer_layer.py:181` (`_swap_out_blocks`),
  `evaluation/benchmark.py:92` (`prepare_mock_test`, long-prompt generator).
- **Motivating evidence.** The paper *itself* proposes this and does not do it (§6, p10):
  "NEO could integrate with chunked-prefill … instead of removing the whole prefilling requests,
  NEO could remove chunks of prefilling requests, thereby having a finer-grained control for
  CPU-GPU balancing. Chunked prefill would be especially useful for NEO when context length gets
  very large while GPU memory is limited." The published evaluation never goes there — the T4 config
  caps `max_model_len` at 832 tokens (`evaluation/configs/config-t4-7b.json:6`) and Fig 9c tops out
  at 500-token inputs — so the long-context regime is entirely unexplored.
- **Feasibility: M.** Cross-cutting: request state, scheduler steps 3–5, block allocation and the
  swap-out trigger all change, and a new long-prompt workload is needed. But no new kernels, the
  perf tables already cover arbitrary `S`, and the eval harness (`server.py`/`benchmark.py`) is
  reusable as-is. Compute is modest (single GPU, 7B model). Realistic for 2–4 students in 10 weeks.
- **Research value: H.** It closes the paper's own stated gap, and both outcomes are informative:
  if chunking helps, it extends NEO to the long-context regime it currently cannot serve; if it
  does not, it validates the paper's counter-argument (Appendix B: chunked prefill is useless on
  memory-constrained GPUs because too few decodes can be piggybacked) in the *offloaded* setting,
  which nobody has tested.
- **Scoop check.** Queries: `"chunked prefill" combined with CPU attention offloading LLM serving
  scheduler 2026 asymmetric pipelining long context`; `NEO MLSys 2025 CPU offloading attention
  "chunked prefill" follow-up scheduling paper 2026`. Result: **partial.** Closest work is
  [APEX (arXiv 2506.03296)](https://arxiv.org/abs/2506.03296), a NEO successor that replaces the
  greedy heuristic with profiling-informed asynchronous dispatch on T4/A10 + Llama-2-7B/3.1-8B, but
  its abstract describes no chunked prefill. Chunked-prefill scheduling papers exist
  ([2606.09061](https://arxiv.org/pdf/2606.09061), Sarathi-Serve) but none in the CPU-offload
  pipeline. Nothing found that does the specific combination.

### A2 — Closed-loop, online-recalibrated performance predictor

- **Hypothesis.** We hypothesize that replacing NEO's one-shot offline profiling tables with an
  online, feedback-calibrated predictor removes the sub-baseline throughput region of Fig 9 (short
  output lengths) and the decay at long output lengths, improving relative throughput by ≥5 % across
  the output-length sweep, and eliminating the ~10-minute cold-start profiling pass.
- **Mechanism.** The engine *already* measures, per layer and per stage, exactly the four
  quantities the cost model needs (`TransformerEvents.linr_time / pref_time / gdec_time /
  cdec_time`). Add a `FeedbackPerfPredictor(PerfPredictor)` that starts from a coarse table (or a
  closed-form initial guess), and after every iteration folds the measured times back into the
  table cells that were used, via EWMA with a per-cell confidence. Make `monitor_performance`
  always-on with a cheap sampling rate. Also replace the hard-coded `lnch_T = 0.8`
  (`perfpredictor.py:128`) and the magic `linr_S_threshold = 128` (`:89`) with measured values.
- **Code locations.** `swiftllm/perfpredictor.py:70` (`TablePerfPredictor` — subclass/extend),
  `swiftllm/server/profiler.py:41` (`init_profile_tables`, shrink the cold-start grid),
  `swiftllm/worker/layers/transformer_layer.py:33` (`TransformerEvents` — already emits the signals),
  `swiftllm/worker/model.py:48` (`ModelPerfResult` — aggregation path),
  `swiftllm/server/engine.py:189` (`_main_event_loop` — hook to feed results back).
- **Motivating evidence.** §5.4 (p9): NEO is "sometimes slightly worse [than baseline] due to
  suboptimal scheduling decisions caused by the inevitable inaccuracy of the offline performance
  profiling", and Fig 9b/9c show relative throughput dipping *below* 1.0. Artifact §C.8 (p16)
  notes the profiling pass makes first startup take "less than ten minutes". The predictor is also
  workload-blind: `_profile_cdec` (`profiler.py:311`) profiles only *evenly split* sequence lengths,
  whereas real traces are heavily skewed (the paper's own Fig 7 caption calls the length
  distribution skewed).
- **Feasibility: H.** Localized: one new class in `perfpredictor.py`, one hook in the engine loop,
  reusing instrumentation that already exists. Evaluable with the shipped `reproduce-fig10a.py`
  sweep on this machine. Well under 1 K LOC.
- **Research value: M.** A solid, expected improvement in a regime the paper admits it loses, and
  the "remove offline profiling entirely" angle has practical appeal — but a reviewer would call the
  direction predictable, and APEX has already staked out "better cost-model-driven dispatch for NEO".
- **Scoop check.** Queries: `LLM inference scheduler "offline profiling" inaccurate replace with
  online feedback cost model CPU offload adaptive calibration 2026`; `papers citing NEO "CPU
  offloading" LLM inference 2026 GPU-CPU pipelining scheduler improvement`. Result: **partial.**
  [APEX (arXiv 2506.03296)](https://arxiv.org/abs/2506.03296) explicitly criticises NEO's "greedy,
  heuristic algorithm that can lead to suboptimal decisions" and uses profiling-informed dynamic
  dispatch, reporting up to 96 % throughput improvement; [Pie (arXiv 2411.09317)](https://arxiv.org/pdf/2411.09317)
  does online "adaptive expansion" of CPU swap memory. Neither is described as *feedback-recalibrating
  the cost table from in-flight measurements*, but the territory is occupied — an implementation on
  NEO would need to position itself against APEX explicitly.

### A3 — Latency-aware mode selection instead of pure throughput-greedy

- **Hypothesis.** We hypothesize that replacing the scheduler's throughput-only objective
  (`tokens / iteration-time`) with a latency-aware objective that accounts for queueing delay
  removes NEO's documented per-token latency penalty at intermediate request rates without lowering
  the maximum sustainable rate, measured on the Fig 6c load–latency curve and the p99 of Fig 7.
- **Mechanism.** Step 6 of the scheduler currently compares `len(batch)/gpu_time` for the GPU-only
  and pipelined schedules and takes the larger (`scheduler.py:225-234`). Replace it with a cost that
  adds an estimated queueing term derived from the (already-tracked) `waiting_q` /
  `cpu_decoding_q` lengths and each request's accumulated per-token latency, so that pipelining is
  only chosen when the throughput gain actually pays for the longer iteration. Add hysteresis to the
  swap-out/swap-in thresholds (`scheduler.py:253-256`) so a request is not offloaded and swapped
  back within a few iterations. Optionally let requests carry a deadline and prefer GPU placement
  for near-deadline requests.
- **Code locations.** `swiftllm/server/scheduler.py:224` (step 5/6, mode comparison),
  `swiftllm/server/scheduler.py:252` (swap thresholds),
  `swiftllm/server/scheduler.py:184` (CPU-decode admission loop, `min_out_cpu_len` heuristic),
  `swiftllm/structs.py:27` (`Request` — carry arrival time / deadline),
  `evaluation/benchmark.py:30` (`run_test` — already records per-request start/end for p99).
- **Motivating evidence.** §5.2 (p8) concedes NEO shows "slightly higher latencies at intermediate
  rates" and attributes part of it to the fact that "NEO actively seeks opportunities to offload
  requests, even though offloading may not help, which consequently leads to more system-level
  overheads in scheduling and swapping". §5.4 attributes the sub-1.0 region of Fig 9 at short output
  lengths to the same cause. The scheduler is strict FCFS with a throughput-only objective
  (`scheduler.py:89` docstring), so requests that land on the CPU tier have no latency protection.
- **Feasibility: H.** Confined to `swiftllm/server/scheduler.py` plus a field on `Request`;
  the latency metrics are already emitted by `evaluation/benchmark.py:67-73` and plotted by
  `illustrator.py`. Same compute budget as the baseline experiments.
- **Research value: M.** It fixes a weakness the paper names, and online serving reviewers care
  about tail latency — but SLO-aware LLM scheduling is a crowded area, so the contribution is
  "SLO-awareness *for the CPU-offload tier*" rather than a new idea.
- **Scoop check.** Queries: `"NEO" LLM inference CPU offload "latency-aware" OR "SLO-aware"
  scheduling tail latency offloaded requests 2026`. Result: **partial.** Closest:
  [OmniServe (arXiv 2603.12831)](https://arxiv.org/abs/2603.12831), which does CPU-GPU attention
  piggybacking with SLO guarantees for mixed latency-sensitive/best-effort loads, and
  [Memory Offloading … with Latency SLO Guarantees (arXiv 2502.08182)](https://arxiv.org/pdf/2502.08182).
  Both are cluster/multi-tenant framings; neither modifies NEO's greedy per-iteration mode choice.

### A4 — Quantized CPU-tier KV cache to relieve CPU memory bandwidth

- **Hypothesis.** We hypothesize that storing the CPU-resident KV cache in 8-bit (per-block scaled)
  instead of FP16 raises NEO's peak relative throughput and shifts the peak to longer output
  lengths on a fixed-bandwidth host, because CPU decoding attention is memory-bandwidth-bound —
  measured on the Fig 9b / Fig 10a output-length sweep at equal GPU configuration.
- **Mechanism.** Change `data_t` for the *CPU* cache only (`pacpu/dtype.h:5-8`) to `int8` with a
  per-(block, head) scale; quantize during swap-out and in the `store_kv` fast path; dequantize
  inside the ISPC inner loops (`qk_product`/`av_product` already accumulate in FP32 `itmd_t`, so
  only the load-and-convert changes). Halving bytes per KV token also doubles the CPU cache capacity
  for a given `--swap-space`. Report perplexity/accuracy alongside throughput so the accuracy cost
  is on the record.
- **Code locations.** `pacpu/dtype.h:5` (`data_t` typedef), `pacpu/pacpu.ispc:5` (`qk_product`),
  `pacpu/pacpu.ispc:68` (`av_product`), `pacpu/core.h:11` (`brute::store_kv`),
  `swiftllm/worker/block_swapper.py:53` (`k_swap`/`v_swap` allocation and dtype),
  `csrc/src/block_swapping.cpp:22` (`swap_blocks`, byte-size arithmetic assumes a single dtype).
- **Motivating evidence.** §5.5 (p9–10) is unambiguous: "The peak throughput gain is positively
  related to the CPU memory bandwidth. This supports the fact that the memory bandwidth, rather than
  computing power (i.e., number of cores), is the factor that determines the performance of attention
  operation on CPUs." Fig 10a shows a 12.2 % → 79.3 % spread driven purely by bandwidth. The paper
  also positions itself as *not* trading accuracy (§1, §7), so it never explores this axis — and our
  Threadripper host has fewer memory channels than the g5.16xlarge that produced the 79.3 % number,
  making bandwidth the binding constraint here.
- **Feasibility: M.** The ISPC kernel, the swap path and the C++ byte arithmetic all change
  together, and a mixed-dtype swap (FP16 on GPU, INT8 on CPU) means `swap_blocks` can no longer be a
  plain `cudaMemcpyAsync` — a conversion kernel is needed. Doable but touches three languages.
- **Research value: M.** The direction is well trodden in general (KV quantization is a whole
  literature), so the surprise is limited; the specific contribution is quantifying how much of
  NEO's CPU-bandwidth wall a cheap quantization buys, which is a useful but expected result.
- **Scoop check.** Queries: `CPU attention offloading LLM inference INT8 quantized KV cache CPU
  memory bandwidth 2026`. Result: **partial.** KV quantization for offloaded caches is widespread
  (e.g. INT8 KV-cache compression work, Q-Hitter); [ScoutAttention (arXiv 2603.27138)](https://arxiv.org/abs/2603.27138)
  reduces CPU-side work via block-wise *sparsity* rather than quantization. Nothing found that
  quantizes the CPU tier inside a NEO-style asymmetric pipeline and reports the bandwidth→throughput
  transfer function.

### A5 — Intra-sequence tiering: split one request's KV across GPU and CPU

- **Hypothesis.** We hypothesize that relaxing NEO's "a request's KV lives entirely on one device"
  invariant — computing partial attention on the GPU-resident suffix and on the CPU-resident prefix
  and merging with log-sum-exp — increases throughput and reduces swap traffic for workloads with
  highly skewed sequence lengths, compared with NEO's whole-request placement.
- **Mechanism.** Allow a sequence's block table to span both tiers with a split point; issue the
  GPU paged-attention kernel over the GPU blocks and the PACPU kernel over the CPU blocks for the
  *same* request in the same iteration; merge the two partial outputs with the log-sum-exp
  combination that `pacpu.ispc` already implements for intra-CPU segments
  (`gather_output_one_seq`, which returns `log(sum)+max` per head). The scheduler then places
  *blocks*, not requests, letting it use the last few GPU blocks that currently go to waste and
  removing the "swap the whole 20 K-token sequence" decision.
- **Code locations.** `pacpu/pacpu.ispc:156` (`gather_output_one_seq` — the LSE merge already exists),
  `swiftllm/worker/layers/transformer_layer.py:258` (`_attention` — where the GPU and CPU attention
  calls would both fire for one request), `swiftllm/worker/kernels/paged_attn.py` (GPU partial
  attention; it already does seq-block partitioning via `batch.seq_block_size`),
  `swiftllm/server/block_manager.py:153` (`_alloc_blocks_for_batch` — per-request device choice),
  `swiftllm/server/scheduler.py:120` (`_get_block_needed` — per-request block accounting).
- **Motivating evidence.** §3.1 (p4) states the simplifying assumption explicitly: "its KV cache
  will either reside entirely in the GPU-cache … or entirely in the CPU-cache". The consequence is
  visible in the scheduler, where whole requests are swapped out one at a time
  (`scheduler.py:265-271`) and CPU admission is cut off by a single length threshold
  (`min_out_cpu_len`, `scheduler.py:190-199`). With skewed real traces (the paper's own Fig 7
  caption) this is coarse.
- **Feasibility: M.** No new numerical algorithm is needed (the merge exists, and both attention
  kernels already produce partial results), but block tables, the block manager, the two-tier
  accounting in the scheduler and the cost model all have to learn about split sequences, and
  numerical equivalence must be validated against the unsplit path.
- **Research value: M.** Relaxing an explicit design assumption is the kind of thing a reviewer
  likes, but the mechanism has been demonstrated elsewhere (see scoop), so the novelty would be the
  *online-serving throughput* framing rather than the technique.
- **Scoop check.** Queries: `split single sequence KV cache across GPU and CPU partial attention
  log-sum-exp merge hybrid decode 2026`. Result: **partial**, close to scooped.
  [HGCA (arXiv 2507.03153)](https://arxiv.org/abs/2507.03153) does dense GPU attention on the recent
  KV plus sparse CPU attention on selected KV and merges with log-sum-exp fusion;
  [RetrievalAttention (arXiv 2409.10516)](https://arxiv.org/pdf/2409.10516) splits the KV set across
  GPU/CPU and combines partial outputs; HybridGen (arXiv 2604.18529) preserves attention semantics
  under CPU-GPU KV partitioning. All target long-context *latency*, not batch-size-limited online
  throughput, so the NEO framing is not literally done — but the core mechanism is.

## 6. Risks and open questions

1. **`vllm_flash_attn` ABI pin.** `swiftllm/worker/layers/transformer_layer.py:8` imports
   `vllm_flash_attn_2_cuda` at module scope, and `:277` selects that path on compute capability ≥ 8
   (our A5000). The standalone `vllm-flash-attn` wheels are tied to specific torch builds and are no
   longer released independently. Likely the single biggest install hazard; the escape hatch is to
   force the in-repo Triton prefill kernel (`swiftllm/worker/kernels/prefill_attn.py`), at some
   prefill-throughput cost that would have to be reported.
2. **Toolchain.** Two GCC versions must exist under the exact names `g++-11` and `g++-13`
   (`pacpu/build.sh:2-3`); CUDA ≥ 12.2 is required (Artifact §C.3.3) while the system `nvcc` is 11.8;
   ISPC 1.23 is documented only via `snap`. All solvable in `$HOME`, none verified by running.
3. **Host RAM on a shared machine.** `config-a10-8b.json:12` requests 120 GB of *pinned* CPU KV
   cache (`swiftllm/worker/block_swapper.py:53`). With 111 GiB available and other users on the box,
   this must be cut; how much the reduction eats into the Fig 10a gain is unknown until measured.
4. **Result transferability.** The paper's biggest number (7.5× on T4) comes from a GPU with a
   16 GB / very small KV budget. We emulate that with `--num-gpu-blocks-override`, but the A5000's
   much higher compute changes the GPU/CPU balance point, so the reproduced *ratio* may legitimately
   differ from the paper's. This is a reproduction nuance to report, not a failure.
5. **Coverage of released scripts.** Only Figs 6c and 10a have drivers. Figs 7, 8, 9, 10b and 11
   (including the FastDecode+ comparison, whose server mode exists as `"fsdc"` in
   `evaluation/server.py:52-66`) would have to be re-derived from the paper text.
6. **Model geometry is compile-time.** `pacpu/dtype.h:21-39` hard-codes layer/head counts for four
   Llama variants and `#error`s otherwise; any add-on evaluated on a different model needs a code
   edit plus a rebuild (`bash build.sh <model> <tp>`).
7. **Measurement noise.** PACPU grabs `omp_get_max_threads()` threads (`pacpu/core.h:239`) and the
   engine's scheduling runs in the same Python process; on a shared 32-thread host, other users'
   CPU load will directly perturb the CPU-attention timings that the scheduler's cost model depends
   on. Experiments should be repeated and the host load recorded.
8. **APEX overlap.** [APEX (arXiv 2506.03296)](https://arxiv.org/abs/2506.03296) already attacks
   NEO's scheduler on the same hardware class with large claimed gains. Any scheduler-centric add-on
   (A2, A3) must read APEX first and position against it; A1 (chunked prefill) and A4 (quantized CPU
   tier) are the least exposed.
9. **Unresolved by reading.** Whether MLSys 2025 awarded artifact badges (the paper carries a full
   Artifact Appendix following the cTuning/ACM badging methodology, §C.9 p16, and a Zenodo DOI, but
   no badge is displayed on the proceedings page or the Zenodo record); whether CUDA page-locking of
   tens of GB succeeds under this host's `RLIMIT_MEMLOCK`; and the real end-to-end cost of the
   cold-start profiling pass on this machine.

## 7. Evidence index

**Paper.** Abstract + §1 (p1–2: problem, contributions, repo URL); §2.1 (p2–3: batch size vs GPU
memory); §2.2 (p3: bandwidth-vs-compute argument, 600/200 GB/s, 125/1.2 TFLOPS); §2.3 (p3:
challenges); §3.1 + Figs 3–5 (p4–5: strawmen, asymmetric pipelining, layer-wise swapping);
§3.2 (p6: scheduling principles, cost model, six steps, <3 ms overhead); §4 (p7: SwiftLLM base,
PACPU/ISPC, Triton→CUDA, Ray TP); §5.1 + Table 1 (p7: testbeds, models, baselines, workloads);
§5.2 + Fig 6 (p8: 14.3 %/6.40 %/563 %; intermediate-rate latency penalty); Fig 7 (p9: latency CDF);
§5.3 + Fig 8 (p9: FastDecode+ collapse); §5.4 + Fig 9 (p9: 14 %/26 %/750 %, sub-baseline at short
outputs, profiling inaccuracy at long outputs); §5.5 + Fig 10 (p9–10: CPU sensitivity 12.2 →
79.3 %, bandwidth-not-cores conclusion; SwiftLLM vs vLLM); §6 (p10–11: chunked-prefill integration
sketch, dense-op offloading, remote CPUs, energy); §7 (p11: related work); Appendix A (p14:
scheduler pseudo-code); Appendix B + Fig 11 (p14: chunked-prefill comparison); Appendix C (p15–16:
artifact check-list, Zenodo DOI, deps, workflow, 10–15 h full / <1 h reduced).
Page images read: `pages/page-08.png`, `pages/page-10.png`.

**Repo paths relied on.** `README.md` (:12-17 compilers/ISPC, :29-36 pacpu build, :98-108
non-AWS instructions incl. "CPU with AVX2 support"); `requirements.txt`; `setup.py`;
`csrc/setup.py`; `csrc/src/block_swapping.cpp`; `pacpu/build.sh`; `pacpu/CMakeLists.txt`;
`pacpu/dtype.h`; `pacpu/core.h`; `pacpu/pacpu.cpp`; `pacpu/pacpu.ispc`;
`swiftllm/engine_config.py`; `swiftllm/model_config.py`; `swiftllm/perfpredictor.py`;
`swiftllm/structs.py`; `swiftllm/server/engine.py`; `swiftllm/server/executor.py`;
`swiftllm/server/profiler.py`; `swiftllm/server/scheduler.py`; `swiftllm/server/block_manager.py`;
`swiftllm/worker/model.py`; `swiftllm/worker/block_swapper.py`;
`swiftllm/worker/layers/transformer_layer.py`; `swiftllm/worker/kernels/prefill_attn.py`;
`evaluation/server.py`; `evaluation/benchmark.py`; `evaluation/reproduce-fig6c.py`;
`evaluation/reproduce-fig10a.py`; `evaluation/configs/config-t4-7b.json`;
`evaluation/configs/config-a10-8b.json`; `evaluation/data/osc-Llama-2-7b-hf.json` (existence).
Driver facts: `repo_facts.json` (head 33e4a0f, 2025-06-16; red-flag hits inspected in context).

**External (scoop / provenance).**
[Zenodo 14964833](https://zenodo.org/records/14964833) ·
[MLSys 2025 proceedings page](https://proceedings.mlsys.org/paper_files/paper/2025/hash/66a026c0d17040889b50f0dfa650e5e0-Abstract-Conference.html) ·
[APEX, arXiv 2506.03296](https://arxiv.org/abs/2506.03296) ·
[HGCA, arXiv 2507.03153](https://arxiv.org/abs/2507.03153) ·
[ScoutAttention, arXiv 2603.27138](https://arxiv.org/abs/2603.27138) ·
[OmniServe, arXiv 2603.12831](https://arxiv.org/abs/2603.12831) ·
[Pie, arXiv 2411.09317](https://arxiv.org/pdf/2411.09317) ·
[RetrievalAttention, arXiv 2409.10516](https://arxiv.org/pdf/2409.10516) ·
[Memory Offloading with Latency SLO Guarantees, arXiv 2502.08182](https://arxiv.org/pdf/2502.08182) ·
[Fairness-Aware Chunked-Prefill Scheduling, arXiv 2606.09061](https://arxiv.org/pdf/2606.09061)
