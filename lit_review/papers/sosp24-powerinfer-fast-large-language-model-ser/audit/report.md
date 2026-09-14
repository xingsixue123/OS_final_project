# PowerInfer: Fast Large Language Model Serving with a Consumer-grade GPU

*Desk review only. Nothing in this report was built, installed, or executed. Every claim
about the code is a claim about what I read in `repo/`, with a path.*

---

## 1. Paper summary

**Problem.** Running an LLM locally on one consumer GPU is bounded by VRAM. Existing
offloading designs lose: GPU-centric offloading (FlexGen) spends >99.5% of its time
moving weights over PCIe (§2.2, Fig. 3b), and layer-granularity hybrid offloading
(llama.cpp) pushes 98% of the compute onto the CPU when a 30B model meets a 24 GB GPU
(§2.2, Fig. 3b). The paper frames this as a *locality mismatch*: every decode iteration
touches every parameter, so there is no working set to cache.

**Key insight.** Neuron activation follows a power law (§3.1, Fig. 4). In OPT-30B, 17% of
neurons account for 80% of all activations model-wide; 26% do so within a single MLP block.
The hot set is stable across downstream tasks — >90% overlap in the top-20% neurons across
PIQA / Arc-easy / TruthfulQA / BoolQ (§3.1, Fig. 5b). Second insight (§3.2, Fig. 6): for
batch < 32, computing a CPU-resident neuron *on the CPU with AVX2* is faster than shipping
its weights to the GPU.

**Design.**
- *Offline* (§6): a profiler counts per-neuron activation frequency on a general corpus
  (C4, Wikipedia); a solver places neurons on GPU/CPU by maximising Σ activation-frequency
  on the GPU (Eq. 1–2) subject to a VRAM constraint (Ineq. 6) and a *communication*
  constraint that forces each layer to get either ≥ C_l neurons or zero (Ineq. 4, 7, 8).
  Neurons are batched 64-at-a-time to keep the ILP tractable (~10 s, §6.3.3).
- *Online* (§5): adaptive per-layer MLP activation predictors sized by layer sparsity and
  skew, held to ~6–7% of model parameters (§5.1, Table 6); two neuron tables mapping split
  rows back to original matrix positions (§5.2); a GPU executor and a CPU executor pulling
  from a global operator DAG queue (§5.3); 10 neuron-aware sparse operators that check a
  neuron's predicted-active bit and then do a vector-vector product, on both CPU (AVX2) and
  GPU (§5.4). The KV cache deliberately stays in **CPU memory** so VRAM goes to hot neurons
  (§7).

**Eval setup** (§8.1). PC-High = i9-13900K / 192 GB / RTX 4090 24 GB / PCIe 4.0.
PC-Low = i7-12700K / 64 GB / RTX 2080Ti 11 GB / PCIe 3.0. Models: OPT 7B–175B (ReLU),
Falcon(ReLU)-40B, LLaMA2(ReGLU) 7B/13B/70B, Bamboo-7B, plus SwiGLU models (Yi-34B,
LLaMA2-13B). Workloads: Alpaca + ChatGPT-prompts, input 8–128, output 8–512, batch 1.
Baselines: llama.cpp and SpecInfer.

**Headline numbers.**
- 8.32 tok/s avg FP16, 13.20 tok/s avg INT4 on PC-High; up to **11.69×** over llama.cpp
  (Falcon-40B FP16, Fig. 10).
- Long-prompt latency: Table 4 — LLaMA(ReGLU)-13B-FP16 49.91 ms → 14.38 ms/token (3.47×);
  Falcon(ReLU)-40B 321.63 → 56.48 ms (5.69×); LLaMA(ReGLU)-70B 92.76 → 37.17 ms (2.50×),
  all at 1.5K input / 256 output.
- Closes the 4090-vs-A100 gap from 93%/92% to 18%/23% (Fig. 18a).
- GPU's share of neuron load rises from ~20% to ~70% on PC-High (Fig. 12).
- Ablation (Fig. 15): +predictors/operators → 3.32×, +hybrid engine → 7.80×,
  +ILP policy → 11.69× on Falcon-40B.
- Accuracy is preserved (Table 7); predictor overhead <10% of inference time (Fig. 17).

**Stated limits.** Gains scale with sparsity: SwiGLU models only get 1.47–1.7× (§8.4,
Table 8). Long prompt + short output gives only 1.07–4× because prefill falls back to dense
GPU compute and the CPU becomes the bottleneck (§8.2). Batch scaling decays 11.69× → 4.38×
from batch 1 to 32 because joint activation sparsity shrinks (Fig. 14). The residual gap to
the A100 "mainly stems from the CPU's considerable computational load" (§8.3.5).

---

## 2. Artifact audit

### Repository

`https://github.com/SJTU-IPADS/PowerInfer` (MIT, 9.8k stars, 2,376 files, 69 MB;
`repo_facts.json`). SJTU-IPADS is the authors' institute (paper byline: "Institute of
Parallel and Distributed Systems, SEIEE, Shanghai Jiao Tong University"). The repo now
redirects to / is mirrored as `Tiiny-AI/PowerInfer` — `README.md:109` instructs
`git clone https://github.com/Tiiny-AI/PowerInfer`, and `README.md:13` announces a 2026
commercial product. The SOSP'24 system is still the top-level tree.

Head commit is **2026-05-11**, i.e. ~18 months after the paper. Most of that drift lives in
`smallthinker/` — a *separate*, much newer llama.cpp fork for the 2025 SmallThinker MoE
models (`smallthinker/README.md`, its own `CMakeLists.txt`, its own submodules for
perfetto/liburing/libaio). **It is not the SOSP'24 artifact and should be ignored.** All the
red flags in `repo_facts.json` for multi-GPU / multi-node / CANN / SYCL point into
`smallthinker/` or into vendored llama.cpp docs.

### Paper component → code map

| paper component | code |
|---|---|
| §6.3 ILP neuron placement solver | `powerinfer-py/powerinfer/solver.py` (90 lines, `cvxopt.glpk.ilp`) |
| §6.3 objective = Σ activation frequency | `solver.py:19-33` (loads `activation_{i}.pt`, sorts, negates, batches by 256) |
| Ineq. 6 memory constraint | `solver.py:43-50` (`CAP`) |
| Ineq. 4/7/8 communication constraint (C_l) | `solver.py:52-68` — **driven by `--threshold`, which defaults to 0 (`__main__.py:18`) and is never passed by the engine (`llama.cpp:3122-3133`). With threshold=0 the constraint is a no-op.** |
| §5.2 neuron tables (`gpu_idx`, `gpu_bucket`) | `powerinfer-py/powerinfer/export_split.py:24-51`; consumed at `llama.cpp:2757-2920` |
| §4.1 step ③ load split per policy | `llama.cpp:3082-3157` (`llm_load_gpu_split*`); invokes the Python solver via `system("python3 -m powerinfer …")` at `llama.cpp:3134`, caches result as `<model>.generated.gpuidx` |
| §5.3 hybrid GPU/CPU FFN execution | `llama.cpp:4546-4757` (`llm_build_sparse_mul_mat`, `llm_build_sparse_axpy`, `llm_build_ffn_sparse`); CPU half + GPU half are separate ops merged by `ggml_add` |
| §5.1 online predictors | `llama.cpp:4688-4695` (`pre_w1` → ReLU → `pre_w2` → `mlp_pre_out` sparsity index) |
| §5.4 GPU neuron-aware operators | `ggml-cuda.cu:4479-4800` (`dequantize_mul_mat_axpy_sparse{,_pro,_batch}`, `dequantize_mul_mat_vec_sparse`, `dequantize_mul_mat_batch_sparse`), dispatch at `ggml-cuda.cu:8787-8801` |
| §5.4 CPU neuron-aware operators (AVX2) | `ggml.c:13855-14760` (`ggml_compute_forward_mul_mat_sparse{,_head}`, `..._axpy{,_q4_0,_head}`, `ggml_axpy_avx_f16` at `ggml.c:14292`) |
| activation threshold | `ggml.c:44` (`sparse_pred_threshold`), `ggml-cuda.cu:119` (`dev_sparse_threshold`), overridable by `LLAMA_SPARSE_PRED_THRESHOLD` (`llama.cpp:1269`, `llama.cpp:2349`) |
| §7 KV cache in CPU memory | default; `llama.cpp:3392-3421` (`llama_reserve_model_kv_cache`) only pulls KV into VRAM when *all* layers are already offloaded |
| `--vram-budget` / `--reset-gpu-index` / `--disable-gpu-index` | `common/common.cpp:474,476,566,812` |
| OPT support | `llama.cpp:5086` `build_opt()` **exists**, contradicting the README TODO — but no OPT PowerInfer weights are published |

### Build route on this machine

`cmake -S . -B build -DLLAMA_CUBLAS=ON && cmake --build build --config Release`
(`README.md:117-122`). Requirements: CMake ≥ 3.17 for the CUDA path
(`CMakeLists.txt:251-254`) — system cmake is 3.25.1, fine. `find_package(CUDAToolkit)`
picks up system nvcc 11.8. Default `CMAKE_CUDA_ARCHITECTURES` is `52;61;70`
(`CMakeLists.txt:290-299`), which does **not** list sm_86; the team should pass
`-DCMAKE_CUDA_ARCHITECTURES=86` for the A5000. AVX2/F16C are on by default
(`CMakeLists.txt:68,75`) and are exactly what the CPU kernels need — the Threadripper
5955WX has AVX2/FMA/F16C and no AVX-512 is required. No root, no Docker, no kernel
anything. The `.devops/` Dockerfiles and `.github/workflows/*.yml` `sudo apt-get` lines
are CI-only and irrelevant to the documented build.

One wrinkle: the engine **shells out to Python** (`llama.cpp:3134`) to run the solver the
first time a model is loaded, so `python3 -m powerinfer` must resolve on `PATH` — an active
conda env satisfies this.

### Dependency pins and their age

- `requirements.txt`: `numpy>=1.24.4`, `sentencepiece>=0.1.98`, `transformers>=4.33.2`,
  `./gguf-py`, `./powerinfer-py`. All floors, no ceilings — the conversion scripts are the
  only consumers and may need an older `transformers` for `convert.py`.
- `powerinfer-py/pyproject.toml:17-20`: `torch>=2`, **`cvxopt==1.3.2`** (Aug 2023, hard
  pin). `solver.py:4` imports `cvxopt.glpk`, which only exists if the wheel was built with
  GLPK. cp312 wheels for 1.3.2 are doubtful — **use a Python 3.10/3.11 conda env** for the
  solver. This is the single most likely install failure.
- The C++ side vendors everything (ggml, httplib, json, stb) — no external C++ deps beyond
  CUDA and pthreads.

### Data / model sources

All public, non-gated Hugging Face (`README.md:145-186`):
- Ready-made PowerInfer GGUF (weights + predictors + `activation/activation_*.pt`
  profiling stats): `PowerInfer/ReluLLaMA-{7B,13B,70B}-PowerInfer-GGUF`,
  `PowerInfer/ReluFalcon-40B-PowerInfer-GGUF`, `PowerInfer/prosparse-llama-2-{7b,13b}-gguf`,
  `PowerInfer/Bamboo-{base,DPO}-v0.1-gguf`.
- Originals + separate predictors under `SparseLLM/*` and `PowerInfer/*-Predictor`, for
  models >40 GB that HF cannot host as one file.
- `scripts/get-wikitext-2.sh` for perplexity; `scripts/run-all-ppl.sh`.
- Workload prompts (Alpaca, `MohamedRashad/ChatGPT-prompts`) are public HF datasets but are
  **not wired into any script in this repo**.

**Not released:** the offline *profiler* (the monitoring kernel of §6.1) and the
*predictor training* code (`README.md:298` TODO, unchecked). Published
`activation_*.pt` files substitute for the profiler for the 8 supported models, but you
cannot sparsify a new model or re-profile on a new corpus with released code.
**No OPT PowerInfer weights are published**, so Fig. 12, Fig. 17, Fig. 18 and the OPT rows
of Table 8 are out of reach even though `build_opt()` is implemented.

### Evaluation scripts

There is **no paper-figure harness**: no `eval/`, no plotting scripts, no run scripts that
reproduce Fig. 10–18. What exists is the inherited llama.cpp tooling, which is enough to
build one: `examples/main/main.cpp` (prints per-token eval timings),
`examples/llama-bench/llama-bench.cpp`, `examples/batched-bench/batched-bench.cpp` (for the
Fig. 14 batch sweep), `examples/perplexity/perplexity.cpp` (Table 7-style accuracy),
`examples/server/server.cpp`. `docs/token_generation_performance_tips.md` is the only
performance doc.

---

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | `github.com/SJTU-IPADS/PowerInfer` under the authors' institute org (paper byline = SJTU IPADS); MIT; contains the actual system, not a stub — GPU sparse kernels at `ggml-cuda.cu:4479-4800`, CPU AVX2 sparse kernels at `ggml.c:13855-14760`, hybrid FFN graph at `llama.cpp:4546-4757`, ILP solver at `powerinfer-py/powerinfer/solver.py`. Repo now also served as `Tiiny-AI/PowerInfer` (`README.md:109`); same code, authors' successor org. No ACM artifact badge found for the SOSP'24 paper. |
| `H2_no_root` | **pass** | Documented build is `cmake -DLLAMA_CUBLAS=ON` (`README.md:117-122`), user-space, CMake 3.17+ (`CMakeLists.txt:252`) vs system 3.25.1. No kernel module, no eBPF, no perf counters, no KVM, no hugepages. `ggml.c:1906` only *reads* `/proc/sys/kernel/numa_balancing` to print a warning. `sudo` hits are confined to `.github/workflows/*` CI and `.github/ISSUE_TEMPLATE/bug.md`; `.devops/*` Dockerfiles are optional and their steps are just `apt install cuda + cmake build`, replayable with conda. Runtime shells out to `python3 -m powerinfer` (`llama.cpp:3134`) — no privilege needed. |
| `H3_hardware_fit` | **pass** | The paper's own target *is* this machine class: PC-High = one RTX 4090 24 GB (§8.1); our A5000 is 24 GB Ampere, same VRAM. CPU kernels need AVX2 only (`README.md:81`, `ggml.c:14292`) — the 5955WX has it, and 16 cores ≥ the paper's 8. Multi-GPU is an unimplemented TODO (`README.md:300`), so nothing here assumes >1 GPU. Caveat, noted not fatal: 125 GiB RAM vs the paper's 192 GiB means FP16 Falcon-40B (~87 GB resident) is tight and FP16 LLaMA-70B (~150 GB) is out; INT4 versions of both fit easily, and the 7B/13B FP16 results (Table 4 row 1, Fig. 10/11) fit with room to spare. |
| `H4_obtainable_deps_data` | **pass** | Deps installable in user space: system CUDA 11.8 + gcc 12 + cmake 3.25 for C++; pip/conda for `torch>=2`, `cvxopt==1.3.2`, `transformers`, `numpy`, `sentencepiece` (`requirements.txt`, `powerinfer-py/pyproject.toml`). Models and the profiled activation statistics are public, ungated HF repos (`README.md:145-186`). `scripts/get-wikitext-2.sh` fetches the perplexity data. Alpaca / ChatGPT-prompts are public HF datasets. Gaps that do **not** trip the filter: no published OPT PowerInfer weights (so OPT figures are unreproducible), and no predictor-training code (so no new models can be sparsified). |

No `fail`, no `unclear`.

---

## 4. Reproduction plan

**Target.** Table 4, row **`LLaMA(ReGLU)-13B-FP16`**: llama.cpp 49.91 ms/token →
PowerInfer 14.38 ms/token = **3.47× speedup** at 1.5K input / 256 output on PC-High.
This row supports the paper's central claim (neuron-granular hybrid execution beats
layer-granular offloading when the model exceeds VRAM) at the smallest model size where the
claim is actually load-bearing: ~26 GB of FP16 weights + ~1.8 GB of predictors does not fit
in 24 GB, so the GPU/CPU split is genuinely exercised.

**Scale-down.**
- Model: `PowerInfer/ReluLLaMA-13B-PowerInfer-GGUF` (direct HF download, ~28 GB), or
  `PowerInfer/prosparse-llama-2-13b-gguf` as a second point.
- GPU: RTX A5000 instead of RTX 4090. Expect absolute ms/token to be worse than 14.38 (the
  A5000 has ~75% of the 4090's memory bandwidth and far less FP16 throughput), but the
  *ratio* is what the claim is about, and the CPU side (16 Zen-3 cores vs 8 Raptor Lake
  cores) is if anything favourable.
- Baseline: `convert-dense.py` → dense FP16 GGUF → stock `llama.cpp` at a commit near
  Dec 2023 with `-ngl` tuned to fill 24 GB. If the dense GGUF proves incompatible with
  upstream (the README warns the activation function was altered, `README.md:205`), fall
  back to PowerInfer's own dense mode (`-ngl`, `README.md:229-234`), and say so — it is the
  same comparison the paper's `+PO` ablation baseline uses.
- Prompt: 1.5K tokens sampled from Alpaca/ChatGPT-prompts, `-n 256`, `-t 16`.

**Steps.**
1. conda env with Python 3.10 (not 3.12 — `cvxopt==1.3.2`); `pip install -r requirements.txt`.
2. `cmake -S . -B build -DLLAMA_CUBLAS=ON -DCMAKE_CUDA_ARCHITECTURES=86`; build.
3. `huggingface-cli download` the 13B PowerInfer GGUF including the `activation/` directory.
4. First `./build/bin/main` run triggers `llm_load_gpu_split` → Python ILP →
   `*.generated.gpuidx` (`llama.cpp:3088-3139`). Confirm the log line
   `offloaded N MiB of FFN weights to GPU`.
5. Write a small driver (bash + awk over `main`'s timing lines) to sweep input/output
   lengths; this is the missing harness.
6. Baseline run; compute the ratio.
7. Sanity-check accuracy with `examples/perplexity` on wikitext-2 (`scripts/get-wikitext-2.sh`).

**Effort.** ~4–6 person-days + ~15–25 GPU-hours (dominated by ~60 GB of downloads, the
dense-baseline conversion, and sweeping output lengths 8/128/512 × two models).

**Level: M.** Not H because (a) there is no evaluation script for any paper figure — the
harness must be written; (b) the llama.cpp baseline version is unpinned and the dense-GGUF
compatibility caveat at `README.md:205` is a real fork in the road; (c) the `cvxopt==1.3.2`
pin plus a Python-3.12-default machine is a likely first-day blocker; (d) HEAD is 18 months
past the paper and the tree now carries an unrelated second project in `smallthinker/`, so
the team may need to check out an older commit if the top level has bit-rotted. Not L
because the build is a plain user-space CMake, the exact model is published as a ready-made
GGUF with the profiling statistics bundled, the solver runs automatically, and the target
number is a single ms/token figure printed by `main`.

---

## 5. Add-on ideas

### A1. Calibrate the placement solver: restore the communication constraint and replace frequency with impact

**Hypothesis.** We hypothesize that an ILP whose communication constraint C_l is calibrated
from *measured* T_sync and per-neuron T_GPU/T_CPU on the target machine, and whose objective
weights neurons by contribution magnitude rather than raw activation frequency, improves
decode tokens/s at a fixed VRAM budget compared with PowerInfer's shipped solver, on
ReluLLaMA-13B and Falcon-40B-INT4.

**Mechanism.** Three concrete changes.
(i) The released engine never passes `--threshold`, and `__main__.py` defaults it to 0, so
`solver.py`'s Constraint 2 degenerates to `-Σa ≤ 0` — Inequality 4 of §6.3.1 is *not
enforced in the artifact*. Add a micro-benchmark that measures T_sync (one intra-layer
CPU→GPU merge) and per-neuron GPU/CPU time on this machine, derive C_l per layer, and pass
it through. (ii) Replace `v_i = f_i` (Eq. 1) with `v_i = f_i · E[|a_i|] · ||W_i||`,
profiled once per model with a ~100-line HF-transformers hook script (the paper's own
profiler is not released, but the hook is trivial for ReLU-family MLPs). (iii) Fix the VRAM
accounting: `llama.cpp:3117` uses a magic `4.5` slice multiplier with the authors' own
`// TODO: why 4.5, not 3?` comment, which mis-sizes `neuron_cap`.

**Code locations.** `powerinfer-py/powerinfer/solver.py`,
`powerinfer-py/powerinfer/__main__.py:18`, `powerinfer-py/powerinfer/export_split.py`,
`llama.cpp:3112-3139`, `examples/llama-bench/llama-bench.cpp`.

**Motivating evidence.** Fig. 15 attributes a jump from 7.80× to 11.69× purely to the ILP
policy, versus a "naive neuron partitioning policy that assigns neurons randomly"
(§8.3.1) — a weak baseline. Meanwhile the shipped solver disables the very constraint §6.3.1
argues is essential, and the authors flag their own VRAM accounting as unexplained
(`llama.cpp:3117`). Either outcome is informative: if calibration helps, the paper
under-delivers its own design; if it does not, the policy contribution in Fig. 15 is mostly
"hot-first" ordering, not the ILP.

**Feasibility: H.** `solver.py` is 90 lines; `export_split.py` is 77. The profiling hook and
the T_sync micro-benchmark are each small. Evaluation reuses `main`/`llama-bench` on
13B/40B-INT4 models that fit this machine. Well inside 10 weeks for 2–4 students.

**Research value: M.** It is a reproduction-grade correction plus a modest design
improvement, not a new mechanism. A reviewer would care that a headline ablation rests on a
constraint the artifact does not enforce, but the ceiling on the improvement is bounded by
how much placement matters at all.

**Scoop check.** `clear`. Searched "PowerInfer neuron placement ILP solver reproduction
communication constraint neuron impact metric improvement" and follow-up work citing
PowerInfer; nothing re-examines the solver's fidelity. The closest adjacent work changes
placement *at runtime* (see A2 scoop note) rather than fixing the offline formulation.

---

### A2. Co-allocate VRAM between hot neurons and the KV cache as a function of context length

**Hypothesis.** We hypothesize that dynamically splitting the VRAM budget between hot-neuron
weights and KV-cache pages — instead of PowerInfer's fixed "all VRAM to neurons, KV cache in
host RAM" rule — reduces time-between-tokens by ≥15% at context lengths ≥ 4K on a 24 GB GPU,
while costing little or nothing at the 64–128-token contexts the paper evaluates.

**Mechanism.** Today §7 states the KV cache "continues to reside in CPU memory", and the
code only pulls K/V into VRAM in the degenerate case where every layer is already offloaded
(`llama.cpp:3392-3402`). As context grows, per-token attention work grows linearly and runs
on the CPU, while the marginal value of the *n*-th hot neuron falls off a power law — so
there must be a crossover. Add a KV term to the ILP: a second resource consumer with its own
value function (measured CPU attention ms per 1K tokens of context) competing for the same
`MCap_GPU`, solved per `n_ctx`. On the engine side, extend `llama_set_vram_budget` /
`llama_reduce_vram_budget` (`llama.cpp:188-217`) to reserve a context-dependent KV slice
before `llm_load_gpu_split` runs, and let `llm_build_kqv` (`llama.cpp:4764`) place K/V on
whichever backend the policy chose. Evaluate a TBT-vs-context-length curve at 512 / 2K / 8K /
16K, sweeping the neuron:KV ratio.

**Code locations.** `llama.cpp:188-217`, `llama.cpp:3392-3421`, `llama.cpp:3142-3157`,
`llama.cpp:4764`, `powerinfer-py/powerinfer/solver.py`, `examples/main/main.cpp`.

**Motivating evidence.** The KV-in-CPU decision is asserted in §7 with no sensitivity study,
and the paper's own long-context data point stops at 1.5K input (Table 4). §8.3.5 names the
CPU as the remaining bottleneck versus the A100. The batch-size study (Fig. 14) and the
long-prompt study (§8.2) both show the CPU saturating — and KV-cache attention is the one
CPU cost that grows without bound in context, unlike neuron compute which is capped by
sparsity.

**Feasibility: M.** Cross-cutting: solver, VRAM budgeting, tensor backend assignment, and
the attention graph all move. The evaluation needs a long-context prompt generator, but the
compute is cheap (single-stream decode on a 13B model). No new hardware.

**Research value: H.** It attacks an unargued design assumption in exactly the regime the
paper skips, and it is the regime that matters most for local deployment in 2026 (long
chats, agent traces, RAG contexts). A negative result — "KV in host RAM really is right even
at 16K" — is itself a useful finding that the paper never establishes.

**Scoop check.** `partial`. Searched "PowerInfer KV cache VRAM budget allocation tradeoff
hot neurons long context" and "joint allocation GPU memory between model weights and KV
cache". Closest: [HGCA: Hybrid GPU-CPU Attention for Long Context LLM
Inference](https://arxiv.org/pdf/2507.03153) (hybrid attention, but it optimises attention
itself rather than trading KV against neuron weights under one budget) and
[BaKlaVa](https://arxiv.org/pdf/2502.13176) (per-head KV budgets, dense GPU setting, no
neuron offloading). Note also [DynamicInfer, ICLR
2026](https://openreview.net/forum?id=CvjmvjlczZ), which re-partitions hot/cold neurons at
runtime and beats PowerInfer by 59% — this scoops a naive "make placement adaptive" idea,
so A2 is deliberately scoped to the neuron-vs-KV budget question, which DynamicInfer does
not address.

---

### A3. Activation-affinity request batching to keep union sparsity high at batch > 1

**Hypothesis.** We hypothesize that scheduling concurrent requests into batches by predicted
neuron-set overlap — rather than arrival order — raises end-to-end throughput by ≥20% at
batch sizes 8–32 compared with PowerInfer's FIFO batching, because it keeps the *union* of
activated neurons, and hence the GPU-resident fraction of the work, small.

**Mechanism.** PowerInfer's sparse kernels already take a per-row activation index and skip
below-threshold rows; in the batch path (`dequantize_mul_mat_batch_sparse`,
`ggml-cuda.cu:4758-4800`) a row is computed if *any* column in the batch wants it, so cost
is the union. Add a scheduler in front of the server's batching loop that (i) runs the cheap
predictor MLPs (`llama.cpp:4688-4695`) on each queued request's current hidden state, (ii)
computes a signature (min-hash over the predicted-active set), (iii) groups requests with
high Jaccard similarity into the same micro-batch and runs dissimilar groups as separate
micro-batches. Metric: tokens/s and p95 TBT versus batch size, reproducing Fig. 14's sweep
with and without affinity grouping. Secondary metric: measured union sparsity per batch.

**Code locations.** `examples/server/server.cpp`, `examples/batched-bench/batched-bench.cpp`,
`examples/batched/batched.cpp`, `ggml-cuda.cu:4758`, `llama.cpp:4652-4757`.

**Motivating evidence.** Fig. 14 is the paper's own admission: speedup collapses from
11.69× at batch 1 to 4.38× at batch 32, "attributed to the diminished sparsity of model
joint activations". The paper treats this as a fact of life and never tries to *schedule
around* it. §3.1/Fig. 5b's finding that hot sets are task-stable is the mechanism that makes
affinity grouping plausible: requests from the same domain should share neurons.

**Feasibility: M.** Needs a new multi-request workload generator (arrival process, mixed
domains) and a scheduler in `server.cpp`, plus a cheap predictor pre-pass. The kernels need
no change. Compute is modest but the harness is real work — this is the "needs a new
evaluation harness" case.

**Research value: H.** It reframes a hardware limitation as a scheduling problem, which is
squarely a systems contribution, and it targets the one axis where PowerInfer visibly
degrades. Either outcome teaches something: if affinity grouping fails, that tells us the
per-token activation sets are less clustered than Fig. 5b's aggregate statistics suggest.

**Scoop check.** `partial`. Searched "activation sparsity aware request batching union of
activated neurons batch LLM inference offloading". Closest: [Polar Sparsity
(2025)](https://arxiv.org/pdf/2505.14884), which observes the same union-sparsity collapse
but responds by *shifting* sparsity from MLP to attention heads on a datacenter GPU — it
does not schedule requests and has no CPU-GPU hybrid engine; and [Neuralink
(2024)](https://arxiv.org/pdf/2410.19274), which groups *co-activated neurons* (a weight-layout
optimisation on smartphones), not co-activating *requests*. [Q-Infer, TACO
2025](https://dl.acm.org/doi/10.1145/3764589) does sparsity-aware dynamic scheduling for
GPU-CPU collaborative inference and is the nearest threat — the team should read it in week 1
and re-scope if it already does request-level grouping.

---

### A4. Sparsity-preserving chunked prefill instead of the dense-GPU prefill fallback

**Hypothesis.** We hypothesize that chunked prefill with a chunk size chosen so that the
per-chunk union activation sparsity stays above a target (rather than PowerInfer's
all-or-nothing switch to dense GPU compute) reduces time-to-first-token by ≥25% for prompts
of 2K–8K tokens on a 24 GB GPU, for models whose dense weights do not fit in VRAM.

**Mechanism.** §8.2 says that for long inputs "PowerInfer switches to dense GPU computation
during the prefill stage", which for a model larger than VRAM means streaming weights over
PCIe — exactly the failure mode of §2.2. Instead: split the prompt into chunks, run the
predictors per chunk, and take the sparse hybrid path whenever the chunk's union sparsity
exceeds a threshold, falling back to dense only for chunks that are effectively dense. The
decision point is the `full_gpu` / `gpu_offload_ratio` branch in `llm_build_ffn_sparse`
(`llama.cpp:4672-4673`) and the `full_gpu` fast paths in `llm_build_sparse_mul_mat`
(`llama.cpp:4570-4578`) and `llm_build_sparse_axpy` (`llama.cpp:4623-4631`), which currently
key off a static ratio rather than the observed batch sparsity. Sweep chunk size; report
TTFT and the measured union sparsity per chunk.

**Code locations.** `llama.cpp:4652-4757`, `llama.cpp:4570-4578`, `llama.cpp:4623-4631`,
`ggml-cuda.cu:6994`, `examples/main/main.cpp`, `common/common.cpp:566`.

**Motivating evidence.** §8.2: with long prompts and short outputs PowerInfer gains only
1.07×–4×, "the CPU becomes the primary bottleneck… tasked with processing a considerable
number of cold-activated neurons". Table 4 shows the long-input case only at 1.5K. Fig. 14's
batch-32 data point (4.38×) is direct evidence that *some* sparsity survives at 32-wide
batches — which is exactly a prefill chunk — so the binary dense/sparse switch is leaving
value on the table.

**Feasibility: M.** Localized in the graph builder, but needs a runtime sparsity measurement
that feeds a per-chunk decision, and the batch sparse kernels must be exercised in a regime
(prefill) they were not tuned for. TTFT measurement is cheap.

**Research value: M.** Chunked prefill is standard practice elsewhere, so the *mechanism* is
not novel; the novelty is the sparsity-aware chunk-sizing criterion and the fact that no one
has quantified the dense-prefill cliff in a hybrid offloading engine. A solid, expected-ish
improvement in an ignored regime.

**Scoop check.** `partial`. Searched "sparse chunked prefill activation sparsity prompt
phase PowerInfer hybrid CPU GPU TTFT". Prefill sparsity work exists but is token-selection
based on a dense GPU (SpecPrefill, ICML 2025; [SparseInfer,
2024](https://arxiv.org/pdf/2411.12692) predicts activation sparsity training-free but does
not address chunked prefill on a hybrid engine). Nothing found that sizes prefill chunks by
union activation sparsity in a CPU-GPU offloading engine.

---

*Idea considered and dropped:* "make the hot/cold partition adaptive at runtime instead of a
one-shot offline ILP". This is **scooped** by [DynamicInfer, ICLR
2026](https://openreview.net/forum?id=CvjmvjlczZ) ("PowerInfer's one-time assignment is
based on offline profiling… DynamicInfer introduces hierarchical neural caching, load-aware
neuron activation, and activation-aware prefetching", reporting 59% over PowerInfer), and
partly by [Q-Infer, TACO 2025](https://dl.acm.org/doi/10.1145/3764589). Do not propose it.

---

## 6. Risks and open questions

1. **Repo drift.** HEAD is 2026-05-11, ~18 months after publication, and the tree now hosts
   an unrelated newer project in `smallthinker/`. I cannot tell from a shallow clone whether
   the top-level SOSP'24 code still builds cleanly; the team should be prepared to check out
   a late-2024 commit. *Desk review cannot settle this.*
2. **`cvxopt==1.3.2` on Python 3.12.** `solver.py:4` needs `cvxopt.glpk`, which is only
   present in GLPK-enabled builds; the 2023 pin very likely has no cp312 wheel. Mitigation:
   Python 3.10/3.11 conda env. If GLPK is unavailable at all, `solve_gpu_split` must be
   ported to PuLP/HiGHS — a half-day, but a surprise on day one.
3. **CUDA architecture default.** `CMakeLists.txt:290-299` defaults to `52;61;70`, which
   omits sm_86. Should JIT from PTX, but pass `-DCMAKE_CUDA_ARCHITECTURES=86` explicitly.
4. **Baseline ambiguity.** `README.md:205` warns that `convert-dense.py` output "might not
   work properly with llama.cpp" because the activation function was altered. If upstream
   llama.cpp refuses the dense GGUF, the only baseline left is PowerInfer's own dense mode,
   which is a weaker (though defensible) comparison than the paper's.
5. **Host RAM ceiling.** 125 GiB total / ~111 GiB free on a *shared* machine. FP16
   Falcon-40B needs ~87 GB resident and ~174 GB of disk for download + conversion (257 GB
   free). Plan around INT4 for anything ≥ 40B; do not attempt FP16 70B.
6. **Unreproducible figures.** No public OPT PowerInfer weights ⇒ Fig. 12, Fig. 17, Fig. 18
   (the A100 comparison), and the OPT rows of Table 8 are off the table. No A100 ⇒ Fig. 18
   is unreachable regardless. No profiler/predictor-training code (`README.md:298`) ⇒ the
   adaptive-predictor contribution of §5.1 cannot be re-derived, only used.
7. **The C_l finding is inferred, not executed.** I read `solver.py:52-59`,
   `__main__.py:18` and `llama.cpp:3122-3133` and concluded the communication constraint is
   inert with `threshold=0`. That reading should be confirmed by instrumenting the solver
   before A1 is built on it.
8. **A5000 ≠ 4090.** Lower memory bandwidth and much lower FP16 throughput. Speedup *ratios*
   should hold (both sides of the comparison use the same GPU), but absolute tokens/s will
   not match the paper, and the GPU/CPU crossover point of §3.2/Fig. 6 may shift — which is
   itself a reason A1's on-machine calibration is worth doing.
9. **Scoop pressure is real and rising.** DynamicInfer (ICLR'26), Q-Infer (TACO'25), Polar
   Sparsity, PowerInfer-2 and HGCA all occupy adjacent ground. Week-1 reading of Q-Infer in
   particular should precede committing to A3.

---

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; `pages/page-10.png` read for Fig. 10/Table 3):
- Abstract & §1 — headline 11.69×, 13.20 tok/s, 18% gap to A100, "4,200 lines of C++/CUDA".
- §2.1, Table 1 — activation sparsity by activation function.
- §2.2, Fig. 2, Fig. 3 — offloading taxonomy; FlexGen 99.5% PCIe; llama.cpp 98% CPU time.
- §3.1, Fig. 4, Fig. 5 — power-law activation; 17%/26%/75% of neurons → 80% of activations;
  >90% hot-set overlap across tasks.
- §3.2, Fig. 6 — CPU-direct beats load-then-execute below batch 32.
- §4, Fig. 7, Fig. 8 — architecture and single-layer example.
- §5.1, Fig. 9, Table 6 — adaptive predictor sizing; predictors = 4.88–8.68% of params.
- §5.2 — neuron tables. §5.3 — DAG queue, GPU/CPU pthread executors, GPU-side merge.
- §5.4, Fig. 16 — neuron-aware operators vs PyTorch-sparse / PIT.
- §6.1–6.3, Table 2, Eq. 1–8 — profiler, impact metric v_i=f_i, ILP with communication
  (Ineq. 4) and memory (Ineq. 6) constraints, 64-neuron batching.
- §7 — 4,200 LoC into llama.cpp, 400 LoC into transformers, **KV cache stays in CPU memory**.
- §8.1, Table 3 — PC-High / PC-Low; model list and sparsity.
- §8.2, Fig. 10, Fig. 11, Fig. 12, **Table 4**, Fig. 13, Fig. 14 — end-to-end speedups;
  neuron-load split 20%→70%; long-input latency; INT4; batch-size decay 11.69×→4.38×.
- §8.3.1, Fig. 15 — ablation +PO / +Engine / +Policy.
- §8.3.2, Table 5 — per-task latency distribution. §8.3.4, Fig. 17 — predictor overhead.
- §8.3.5, Fig. 18 — vs A100; "remaining disparity mainly stems from the CPU's… load".
- §8.4, Table 8 — SwiGLU models only 1.47–1.7×. §8.5, Table 7, Table 9 — accuracy.
- §9 — related work; attention sparsity and speculative decoding declared orthogonal.

**Repository** (paths relative to `repo/`):
- `README.md` — build (:117-122), model table (:145-186), dense-mode caveat (:205),
  `--vram-budget` (:220), FAQ/`--reset-gpu-index` (:276-277), TODOs incl. unreleased
  predictor-training code (:298) and no multi-GPU (:300), Tiiny-AI clone URL (:109).
- `CMakeLists.txt` — :1, :68, :75, :82, :251-254, :290-302.
- `requirements.txt`; `powerinfer-py/pyproject.toml:17-20` (`cvxopt==1.3.2`).
- `powerinfer-py/powerinfer/solver.py` — :4, :19-33, :43-50, :52-68, :81.
- `powerinfer-py/powerinfer/__main__.py` — :13-19 (defaults incl. `--threshold 0`).
- `powerinfer-py/powerinfer/export_split.py` — :24-51, :53-75.
- `llama.cpp` — :103, :188-217, :1269, :2347-2349, :2757-2920, :3082-3157 (esp. :3117 magic
  4.5, :3122-3133 solver invocation, :3134 `system()`), :3392-3421, :4546-4757, :4764,
  :5086 (`build_opt`), :6721-6723.
- `ggml.c` — :44, :1906-1910, :13855, :14030-14051, :14285-14292, :14314, :14465, :14620,
  :14893-14928.
- `ggml-cuda.cu` — :119, :4418-4800, :5382-5709, :6994, :7232-7317, :7593-7641, :8787-8801,
  :9634.
- `common/common.cpp` — :474, :476, :566-572, :812, :907.
- `examples/` — `main/main.cpp`, `perplexity/perplexity.cpp`, `llama-bench/llama-bench.cpp`,
  `batched/batched.cpp`, `batched-bench/batched-bench.cpp`, `server/server.cpp`.
- `scripts/get-wikitext-2.sh`, `scripts/run-all-ppl.sh`.
- `repo_facts.json` — head commit 2026-05-11, MIT, 9,791 stars, red-flag inventory.
- `fetch_result.json`, `meta.json`.

**Web** (provenance and scoop checks):
- [SJTU-IPADS/PowerInfer](https://github.com/SJTU-IPADS/PowerInfer) /
  [Tiiny-AI/PowerInfer](https://github.com/Tiiny-AI/PowerInfer) — repo provenance.
- [SOSP'24 proceedings entry](https://dl.acm.org/doi/10.1145/3694715.3695964) — no artifact
  badge found.
- [DynamicInfer, ICLR 2026](https://openreview.net/forum?id=CvjmvjlczZ) — scoops runtime
  hot/cold re-partitioning.
- [Q-Infer, ACM TACO 2025](https://dl.acm.org/doi/10.1145/3764589) — sparsity-aware dynamic
  GPU-CPU scheduling.
- [Polar Sparsity, 2025](https://arxiv.org/pdf/2505.14884) — batched union-sparsity collapse.
- [Neuralink, 2024](https://arxiv.org/pdf/2410.19274) — neuron co-activation linking.
- [HGCA, 2025](https://arxiv.org/pdf/2507.03153) — hybrid GPU-CPU long-context attention.
- [BaKlaVa, 2025](https://arxiv.org/pdf/2502.13176) — budgeted KV allocation.
- [SparseInfer, 2024](https://arxiv.org/pdf/2411.12692) — training-free sparsity prediction.
- [PowerInfer-2, 2024](https://arxiv.org/abs/2406.06282) — authors' smartphone follow-up.
