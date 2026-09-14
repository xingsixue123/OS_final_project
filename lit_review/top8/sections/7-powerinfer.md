### 7. PowerInfer: Fast Large Language Model Serving with a Consumer-grade GPU (SOSP'24)

- **Repo:** https://github.com/SJTU-IPADS/PowerInfer (now redirects to `Tiiny-AI/PowerInfer`) — MIT; 77 MB checkout; C++/C/CUDA/Python.
  - **History:** last commit 2026-05-11 (a README edit). The core engine was last really changed in 2024-09.
  - **Artifact:** no tags or separate AE repo; the SOSP artifact is `main`.
  - **Not released:** **the offline profiler and predictor training** (`README.md:298` "[ ] Release predictor training code", verified). Activation statistics and trained predictors come ready-made inside the GGUF files on Hugging Face.
- **What it is:** a llama.cpp/ggml fork for ReLU-sparse LLMs split across GPU and CPU. An offline ILP puts frequently activated ("hot") FFN neurons on the GPU and leaves "cold" ones on the CPU. Small MLP predictors choose which neurons to compute per token, using sparse operators on both sides. `--vram-budget` replaces llama.cpp's `-ngl`.
- **Paper eval setup:**
  - **Machines:** PC-High = i9-13900K + 192 GB + RTX 4090 24 GB; PC-Low = i7-12700K + 64 GB + RTX 2080Ti 11 GB.
  - **Models:** OPT 7B–175B, Falcon-40B, LLaMA2(ReGLU) 7B/13B/70B, Bamboo-7B; FP16 and INT4.
  - **Baselines:** llama.cpp, SpecInfer, vLLM.
  - **Headline:** up to 11.69× (Falcon-40B FP16).
- **Reproduction target:** **Table 4, LLaMA(ReGLU)-13B-FP16 on a 24 GB GPU, 1.5K-token input / 256-token output: llama.cpp 49.91 ms/token vs PowerInfer 14.38 ms/token (3.47×).** Why this row:
  - The released files (28.3 GB) are just larger than 24 GB of VRAM, the case the engine is built for. With a model that fits entirely on the GPU there is no speedup (issue #128).
  - No gated models are needed.
  - Cheap follow-up: emulate PC-Low with `--vram-budget 11`; Bamboo-7B needs no conversion at all.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| CMake ≥ 3.17 (CUDA); C11/C++11 | `CMakeLists.txt:1,252` | ✅ 3.25.1, gcc 12.2 | as-is (gcc 14 breaks it, #267; gcc 12 is fine) |
| CUDA toolkit + cuBLAS | `CMakeLists.txt:254-288` | ✅ system nvcc 11.8 + `libcublas.so.11` + `g++-11` host compiler (verified) | pass `-DCMAKE_CUDA_COMPILER=/usr/bin/nvcc -DCMAKE_CUDA_HOST_COMPILER=g++-11`. **Don't use conda CUDA ≥ 12.3**: driver 535 gives PTX errors (#229) |
| CUDA arch default `52;61;70` / `60;61;70` (no 86) | `CMakeLists.txt:290-299` (verified) | ⚠️ JIT fallback is slow | `-DCMAKE_CUDA_ARCHITECTURES=86` |
| CPU SIMD: AVX2/F16C/FMA; AVX-512 **off** by default | `CMakeLists.txt:69-71`; the paper's 13900K has no AVX-512 either | ✅ Zen 3 has AVX2/F16C/FMA (verified) | no AVX-512 assumption |
| Python ≥ 3.8: numpy, sentencepiece, transformers, local `gguf-py`, `powerinfer-py` | `requirements.txt` | user install | `conda create -n powerinfer python=3.10` + pip |
| torch ≥ 2, cvxopt 1.3.2 (GLPK ILP solver) | `powerinfer-py/pyproject.toml:18-19` | user install | CPU torch wheel is enough |
| Runtime calls `python3 -m powerinfer` on first load | `llama.cpp:3120-3134` | ⚠️ | keep the conda env active |
| Docker images | `.devops/full-cuda.Dockerfile` (stale: calls `make`, no Makefile) | not applicable | native CMake build |
| 24 GB GPU (paper: RTX 4090) | paper | A5000 24 GB, Ampere sm_86 | same VRAM; lower GPU memory bandwidth (768 vs 1,008 GB/s); #184 says a 3090 (sm_86) behaved correctly |
| Host RAM for spill-over (paper: 192 GB) | paper | 125 GiB | fine for 7B/13B FP16 and 40B/70B INT4; **70B FP16 (~140 GB) doesn't fit** |

**Models** (Hugging Face; sizes and gating verified via API)

| artifact | size | gated? | needed |
|---|---|---|---|
| `Tiiny/ReluLLaMA-13B-PowerInfer-GGUF` | **28.3 GB** | no | ✅ PowerInfer side of the target |
| `SparseLLM/ReluLLaMA-13B` (safetensors) | **26.0 GB** | no | ✅ only to `convert-dense.py` into a ~26 GB f16 baseline GGUF, then delete |
| `Tiiny/Bamboo-base-v0.1-gguf` | 39.4 GB total | no | optional cheap check (Figure 11 / Table 5) |
| `Tiiny/ReluLLaMA-70B-PowerInfer-GGUF` (Q4) | 42.2 GB | no | stretch; dense Q4 baseline source is 276 GB → over disk |
| `Tiiny/ReluFalcon-40B-PowerInfer-GGUF` (Q4) | 25.5 GB | **yes (auto)** | stretch only, needs an HF token |
| `SparseLLM/ReluFalcon-40B` (FP32) + predictor | 167 + 14 GB | no | ❌ the 11.69× FP16 headline needs ≈ 264 GB > 253 GB free |
| OPT-13B/30B/66B/175B predictors | — | **not released** | ❌ OPT results can't be reproduced |
| Prompts (ChatGPT-prompts, Alpaca) | small | public | no sampling script, so write a ~1.5K-token prompt file |

Minimum for the target: ~54 GB download, ~81 GB peak disk, ~55 GB after cleanup.

**Hard filters** — H1 ✅ official repo, MIT (the profiler and predictor trainer are unreleased) · H2 ✅ user-space CMake + pip; no kernel, driver or Docker · H3 ✅ one 24 GB GPU, AVX2 only; absolute speeds differ from a 4090 · H4 ✅ for the 7B/13B targets; ❌ for Falcon-40B FP16 (disk), 70B FP16 (RAM) and OPT-30B+ (predictors unreleased).

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | One documented cmake command; needs extra flags for the Debian nvcc path and arch 86, plus an active Python env at runtime |
| dependency fit | 4 | System CUDA 11.8 + gcc-11 works with driver 535; torch/cvxopt have wheels |
| data fit | 3 | 7B/13B GGUFs are public at 15–28 GB; the flagship Falcon-40B FP16 and 70B FP16 don't fit; Falcon Q4 is gated; OPT predictors are missing |
| hardware fit | 4 | Same 24 GB VRAM and AVX2-only CPU assumption; `--vram-budget` emulates the 11 GB PC-Low; slower GPU, less RAM, and different CPU memory bandwidth |
| repro scripts | **2** | No figure or benchmark scripts; `llama-bench` lacks `--vram-budget`; only README one-liners |
| extensibility | 4 | Neuron placement is a clean Python plug-in (`powerinfer-py/powerinfer/solver.py`, `export_split.py`); the runtime is huge single files (`llama.cpp` 423 KB, `ggml.c` 680 KB, `ggml-cuda.cu` 367 KB); predictor changes are hard without the trainer |
| **total** | **21 / 30** | |

**Verdict: 🟡 DOABLE-WITH-WORK** · confidence medium-high · setup ≈2–3 person-days (½ build, ½ downloads + dense conversion, 1–2 benchmark harness) · compute: ~54 GB download (1–2 h), ~15 min build, ~15 min conversion, < 2 GPU-hours for Table 4 with 5 repeats + PC-Low emulation.

**Key risks**
- **Baseline fidelity.** The "llama.cpp" baseline must be this repo's dense mode on a `convert-dense.py` GGUF with `-ngl`; upstream llama.cpp can't run ReLU LLaMA correctly, and the paper's exact baseline build isn't documented.
- **This CPU may shrink the ratio.** The Threadripper's 8-channel DDR4 likely has more memory bandwidth than the 13900K, which speeds up llama.cpp's CPU layers and could reduce the 3.47×.
- **Small spill-over.** 13B FP16 is only ~5 GB over 24 GB, so the result is sensitive to `--vram-budget` accounting, which is known to be inaccurate. Report the actual offloaded MiB from the logs.
- **Ampere correctness** (A100 anomalies reported in #184): sanity-check outputs first.
- **Headline gap.** The 11.69× Falcon result and the OPT results can't be reproduced here; a 13B result confirms the mechanism, not the biggest number.
- **ILP caching.** The solver has a 30 s GLPK limit and caches `*.generated.gpuidx`, so pass `--reset-gpu-index` whenever the budget changes.
- **Unmaintained core.** No CUDA CI.

**Where an add-on plugs in**
- **Hot/cold placement policy:** `powerinfer-py/powerinfer/solver.py::solve_gpu_split` (ILP) and `export_split.py::export_split`, called from `llama.cpp:3088 llm_load_gpu_split_with_budget`. Communication-aware, budget-adaptive or workload-specific placements can be swapped in **without touching C++**.
- **Online / dynamic re-placement:** `llama.cpp:2781 llama_gpu_split_loader`, `:10130 llama_model_offload_ffn_split`, `:3000 buffered_tensor_allocator`.
- **VRAM budgeting:** `llama.cpp:188 llama_set_vram_budget`; flags in `common/common.cpp:474-566`.
- **Predictor threshold / adaptive sparsity:** `llama.cpp:4652 llm_build_ffn_sparse`; env `LLAMA_SPARSE_PRED_THRESHOLD` (`llama.cpp:1269`).
- **Sparse operators:** CPU `ggml.c:14030 ggml_compute_forward_mul_mat_sparse` (AVX2 axpy :14285-14330); GPU `ggml-cuda.cu:8787 ggml_cuda_mul_mat_sparse`.

**Build route (not executed)**
1. `conda create -n powerinfer python=3.10 -y && conda activate powerinfer && pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements.txt "huggingface_hub[cli]"`
2. `cmake -S . -B build -DLLAMA_CUBLAS=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/bin/nvcc -DCMAKE_CUDA_HOST_COMPILER=g++-11 -DCMAKE_CUDA_ARCHITECTURES=86 && cmake --build build -j 32`
3. `huggingface-cli download Tiiny/ReluLLaMA-13B-PowerInfer-GGUF` and `SparseLLM/ReluLLaMA-13B` (safetensors)
4. `python convert-dense.py --outtype f16 --outfile …/llama-13b-relu.f16.gguf …/ReluLLaMA-13B`, then delete the safetensors
5. Sanity run: `./build/bin/main -m …powerinfer.gguf -n 32 -t 16 -p "Once upon a time"`; the log should show `offloaded … MiB of FFN weights to GPU`
6. Table 4 PowerInfer: `-c 2048 -f prompt_1500tok.txt -n 256 --ignore-eos -t 16`; read ms/token from `llama_print_timings`, ×5
7. Table 4 baseline: dense f16 GGUF with the largest `-ngl` that fits (~34–36 of 40), ×5; compare to 49.91 vs 14.38
8. Optional PC-Low: `--vram-budget 11 --reset-gpu-index` vs an `-ngl` that fits in 11 GB
