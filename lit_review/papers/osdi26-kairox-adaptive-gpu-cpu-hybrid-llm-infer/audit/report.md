# Kairox: Adaptive GPU-CPU Hybrid LLM Inference via Online Neuron Balancing

*Desk review only. Nothing was built or run; every claim below is a prediction backed by a
paper section/figure or a repository path.*

## 1. Paper summary

**Problem.** On a consumer PC, an LLM whose weights exceed VRAM must be split between GPU
and CPU. Activation-sparse systems such as PowerInfer place *hot* FFN neurons on the GPU and
*cold* ones on the CPU using an **offline** profile. The paper's motivation section (§3.1,
Fig. 3, Fig. 4) argues this static split breaks at runtime: cold-neuron activations drift
sharply between adjacent tokens (Layer 0 of OPT-6.7B swings from ~0 to >3,000 activated cold
neurons), CPU compute time within one 256-token sequence ranges ~30–150 ms, TPOT ranges
~50–200 ms, and at batch size 1→20 CPU latency grows 102.8 ms → 551.7 ms (Fig. 3 left).

**Key idea.** *Online neuron balancing*: continuously migrate FFN neuron **groups** between
host DRAM and a GPU-resident neuron cache according to the runtime activation pattern
(Fig. 1 right). §3.2 shows a strawman LRU reloader over a 2,000–3,000-neuron GPU cache already
cuts CPU workload a lot at modest PCIe cost (Fig. 5), then names three challenges: (1) hiding
transfer latency behind computation, (2) not wasting bandwidth on transient "one-hit wonder"
neurons, (3) choosing balancing intensity when CPU-bound and I/O-bound are opposing regimes.

**Design** (Fig. 6 system overview):

* **Live Pipeline (§5).** *Adjacent prediction*: the sparsity predictor for layer *i+1* is
  driven by the **attention output of layer *i*** (≈98% cosine similarity between adjacent
  hidden states), opening an overlap window spanning FFN(*i*) + Attn(*i+1*) in which the
  transfers for layer *i+1* run (Fig. 7c). Layer 0 is prefetched during the previous token's
  sampling phase. *Co-activation grouping* (§5.2): neurons are clustered offline by a weighted
  graph-partitioning problem (Eq. 1–4, NP-hard) approximated with METIS, then physically
  reordered, so a transfer unit is a group of `GS` neurons. Table 2 motivates this:
  single-neuron transfers reach only 3.3/5.8 GB/s of 16/32 GB/s theoretical on PCIe 3.0/4.0
  (~21%/18%), rising to 10.8/22.3 GB/s at GS=24.
* **Locality-aware balancing / TAM (§6).** Fig. 8 shows conditional reactivation probability
  P(A_{t+δ} | A_t) decays fast for cold neurons (<0.2 for δ>2). **Temporal Activation
  Momentum** is a Hawkes-inspired EMA, `S_{t+1} = λ·S_t + (1−λ)·A_t` (Eq. 5), generalized to
  groups with a normalized intra-group intensity. Groups scoring above
  `τ_load = (1−λ)+ε` are load candidates; the top-K by score are kept resident.
* **Adaptive Neuron Balancer (§7, Algorithm 1).** λ is turned into a *control variable*:
  pipeline-stall feedback classifies the step as IO_BOUND (λ ← min(λ(1+α), λmax), more inertia,
  fewer reloads) or CPU_BOUND (λ ← max(λ(1−α), λmin), more reloads). λ is initialized to ~0.5.

**Implementation (§8).** ~5,700 lines of C++/CUDA on top of llama.cpp. Three CUDA streams
(compute, critical I/O, reload) with preemption of queued reload tasks; fused XOR/AND kernels
for group-mask set-difference; a CUDA argsort constrained to ≤1024 groups. Offline: >400k
activation patterns from C4, used to train the adjacent predictors and build the co-activation
graph.

**Evaluation setup (§9.1).** Two PCs: **PC-Low** = RTX 3080 Ti (12 GB), Xeon E5-2680 v4 capped
at 12 threads, 64 GB RAM, PCIe 3.0; **PC-High** = RTX 4090 (24 GB), EPYC 7542 capped at 16
threads, 128 GB RAM, PCIe 4.0. Models: OPT-6.7B/13B/30B-Q8/Q4/66B-Q4, Prosparse-LLaMA2-7B/13B,
Bamboo-7B, SparseQwen2-7B, ReLUFalcon-40B-Q8. Prompts: fixed ShareGPT subset, ctx 1024,
max output 512, batch size 1 (plus speculative decoding with 5 draft tokens). Baselines:
llama.cpp, PowerInfer (ported to the same backend), Neuralink (**re-implemented by the authors
on top of Kairox**, not open source), Q-Infer.

**Headline numbers.** Fig. 9 (top, standard completion): up to **7.53×** over llama.cpp on
PC-Low and **7.57×** on PC-High; geomean 4.45× / 5.00×; best case 3.70× / 6.35× / 3.76× over
PowerInfer / Neuralink / Q-Infer. Fig. 15 ablation: PowerInfer → +LP 1.91× → +NB 3.23× →
+ANB 3.70× (OPT-13B, PC-Low), i.e. the adaptive controller is worth the last ~15%. Fig. 10:
Top-K vs TAM vs TAM-T reload/CPU-latency trade-off. Fig. 11: λ evolution per layer and
resulting reload intensity. Fig. 12: GPU utilization up to 5.35× higher. Fig. 13: throughput
vs. VRAM budget (PC-Low 7–12 GB Bamboo-7B; PC-High 14–24 GB OPT-13B) — Kairox at 14 GB beats
all baselines at 24 GB. Fig. 14: TPOT stability. Table 3: non-ReLU models, gains shrink to
7–33%. Table 4: ≤0.5% average downstream-accuracy change.

**Stated limitations / future work.** MoE serving is explicitly out of scope (§10, "we leave
to future work"); non-ReLU / low-sparsity architectures are called out as an open opportunity
(§9.5); mobile/unified-memory platforms are excluded (§10).

## 2. Artifact audit

**Repo.** `https://github.com/Anhelor/kairox.cpp`, MIT, head commit `6eeba16` dated
2026-05-19, 2,602 files / 148.7 MB, created 2026-05-05 (`repo_facts.json`). It is a **fork of
llama.cpp** with the Kairox system merged in; `README.md:1-3` points at
`ARTIFACTS_EVALUATION.md`, which names the paper, all eight authors, "OSDI '26", and this exact
repository URL. The HF account that hosts the model artifacts (`Anhelor/SPIF-GGUF`) matches the
GitHub account. Provenance is solid.

**Paper component → code map** (all paths verified to exist):

| paper component | code |
|---|---|
| Cache manager, VRAM budget split across layers, weight reordering by the offline permutation | `src/llama-kairox.cpp:91-393`, `src/llama-kairox.h` |
| Per-layer cache state (scores, masks, group maps, reload plan) | `ggml/include/ggml-kairox.hpp:52-101` |
| Adjacent prediction (§5.1) — predictor for layer *i+1* built from layer *i*'s output | `src/llama-graph.cpp:1385-1393`, predictor MLP at `src/llama-graph.cpp:1240-1275` |
| Layer-0 wrap-around prefetch (§5.1 special case) | `src/llama-graph.cpp:1366-1371` (`reload_kairox_lc = is_last ? layer_caches[0] : ...`) |
| TAM score update (Eq. 5) + top-K + XOR/AND set difference (§6) | `src/llama-graph.cpp:1295-1319` (`build_sparse_ffn_dfr`), CUDA at `ggml/src/ggml-cuda/dfr-fusion.cu`, EMA coefficients uploaded per call at `ggml/src/ggml-cuda/binbcast.cu:432-440` |
| Reload planning (load/evict pairing, budget truncation) | `src/llama-kairox.cpp:41-89` (`kairox_reload_plan`), driver at `ggml/src/ggml-cuda/ggml-cuda.cu:2558-2578` |
| Reload execution + async I/O executor + stream anchors (§8 priority-aware streams) | `ggml/src/ggml-cuda/ggml-cuda.cu:2580-2648`, `ggml/include/ggml-kairox.hpp:106-277` |
| Adaptive balancing intensity (§7 / Alg. 1 Phase 1) | `ggml/include/ggml-kairox.hpp:194-201` — **adapts the reload budget `dfr_clamp_k`, not λ** (see below) |
| Sparse CPU kernels (AVX) | `ggml/src/ggml-cpu/ggml-cpu.c:1692-1891` (`mul_mat_sparse`), `:2371-2470` (`axpy_sparse`, AVX-512 path with an **AVX2 fallback** at `:2395`) |
| Sparse/quantized CUDA kernels | `ggml/src/ggml-cuda/ggml-cuda.cu:2500-2549`, `ggml/src/ggml-cuda/act-fusion.cu` |
| CLI surface (`-kairox-ms`, `-vb`, `-cffn`) | `common/arg.cpp:2330-2351`, CPU-FFN buffer override at `common/common.h:991-996` |
| Benchmark harness (`--bench-runs/--bench-prompt-file`, "benchmark summary") | `tools/completion/completion.cpp:391-526`, `examples/speculative/speculative.cpp:608-720` |
| Eval drivers / result parser | `bench_models.sh`, `test_kairox.sh`, `compile_kairox.sh`, `parse_bench_logs.py`, `prompts.txt` |

**What is *not* in the repo.** The entire **offline stage** of Fig. 6 — activation profiling on
C4, predictor training, co-activation graph construction, METIS partitioning, and production of
the `*-sparkinfer-model-split-N.gguf` files — is absent. `grep -i metis|co-activation|reorder_perm`
matches only consumers (`src/llama-kairox.cpp:256`, `:340-351`) and the docs. The split files
are downloaded pre-built from Hugging Face. Consequence: any add-on that needs a *different*
grouping (e.g. a different `GS`) must re-derive the offline pipeline. The file-name suffix is
the group count, so `GS = n_ff / suffix`: prosparse-llama-2-7b → 11008/688 = **16**;
opt-*/ReluFalcon → 16384/1024 = 16; SparseQwen2-7B → 18944/592 = **32** — matching the "(16)"
and "(32)" annotations in Fig. 8(b).

**Baselines in the artifact.** `bench_models.sh:49` runs only `llama_cpp`, `kairox`,
`neuralink`. "Neuralink" is *the same binary* with `KAIROX_DFR_LAMBDA_INIT=0.00` and
`KAIROX_DFR_LAMBDA_ADAPT_RATE=0.00` (`test_kairox.sh:97-116`) — i.e. no momentum and no
adaptivity, consistent with §9.1's statement that Neuralink was re-implemented on top of
Kairox. **PowerInfer and Q-Infer are not included**; `ARTIFACTS_EVALUATION.md:28` says
evaluators need not build them. So 3 of the 5 bars of Fig. 9 are reproducible from this
artifact alone.

**Two paper/implementation divergences found by reading the code** (these matter for §4–§6):

1. **§7 / Algorithm 1 adapts λ; the released code adapts K.** λ is set once from
   `KAIROX_DFR_LAMBDA_INIT` (default 0.67) into a 3-float host tensor at
   `src/llama-kairox.cpp:338, 384`, and there is **no writer** to `dfr_ema_coeffs` after init
   (grep across the tree finds only the init and the per-call `cudaMemcpyToSymbolAsync` at
   `binbcast.cu:436`). Instead, `k_kairox_dfr_lambda_adapt_rate` is used at
   `ggml/include/ggml-kairox.hpp:194-201` to multiply an atomic **`dfr_clamp_k`** (a per-layer
   cap on reload *pairs per step*, consumed at `src/llama-kairox.cpp:63-64`) by (1±α),
   depending on whether any compute task had queued up behind the I/O anchor. That is a
   different controller (a reload-rate limiter) with a cruder feedback signal (a boolean
   `to_move.empty()`), and it means **Fig. 11(left), the evolution of λ, cannot be produced by
   the released artifact as-is**. The comment at `ggml-kairox.hpp:194` ("For simplicity,
   decrease the maximum load directly when reloading") is candid about the substitution.
2. **The τ_load one-hit-wonder threshold of §6 / Alg. 1 lines 10–15 is not in the graph.**
   `build_sparse_ffn_dfr` (`src/llama-graph.cpp:1300-1318`) computes the TAM update, takes
   `ggml_argsort_top_k(dfr_scores, n_cached_groups)`, and diffs against the residency mask.
   There is no `S > (1−λ)+ε` filter and no ε anywhere in the repo.

One thing I checked and found *correct*: residency bookkeeping stays consistent when the budget
truncates the plan — `ggml-cuda.cu:2569-2573` copies `group_mask_host` back over the GPU
`group_mask` whenever `reload_count < reload_planned_count`, so groups that were planned but
not loaded are not falsely marked resident.

**Build route on this machine.** `compile_kairox.sh` is a thin cmake wrapper
(`-DGGML_CUDA=ON -DGGML_CUDA_GRAPHS=OFF -DCMAKE_CUDA_ARCHITECTURES=native`, targets
`llama-completion llama-speculative llama-quantize`). Its first four lines try
`apt install libssl-dev` — unguarded by `set -e` and redirected to `/dev/null`, so without root
it fails silently; adding `-DLLAMA_OPENSSL=OFF` (`CMakeLists.txt:116`) removes the need
entirely, and none of the three build targets need the HTTP stack. `ARTIFACTS_EVALUATION.md`
prescribes a `pytorch:2.11.0-cuda12.8` Docker image; Docker is not installed here and is not
required — the container only supplies a CUDA toolkit, git-lfs and `huggingface_hub`, all of
which conda/pip provide in user space. **Dependency-age note:** the tree is current llama.cpp
(Nov–Dec 2025 vintage; upstream CI in `.github/workflows/build.yml:813,852` uses CUDA 12.4/12.6),
so the system `nvcc` 11.8 is likely too old; a per-user conda `cuda-toolkit=12.2` matches driver
535 exactly and is the safe choice. `native` arch resolves to `sm_86` for the A5000 — fully
supported, no FP8/Hopper kernels are involved.

**Data / models.** `https://huggingface.co/Anhelor/SPIF-GGUF` is public, non-gated, MIT
(verified 2026-09-14); it holds the base GGUFs, the draft models for speculative decoding, and
the `*-sparkinfer-model-split-N.gguf` companion files. The prompt set (`prompts.txt`) is in the
repo, so the ShareGPT dependency is already materialized. The repo advertises files up to
62.3 GB, so the *full* download will not fit in ~257 GB of free space — selective
`hf download --include` (documented at `ARTIFACTS_EVALUATION.md:108-128`) is mandatory.

**Eval scripts present/absent.** Present: build, per-backend runner, profile driver, log
parser, warmup/repeat logic, fixed seed 42. Absent: any reference/expected-result file, any
plotting script, and any harness for Figs. 10–14 (reload-policy ablation, λ evolution, GPU
utilization, VRAM-budget sweep, per-token TPOT) — although `--bench-token-latency`
(`tools/completion/completion.cpp:405-414, 488-494`) prints per-token latencies, which is
exactly what Fig. 14 needs, and `-vb` gives the Fig. 13 sweep for free.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | `ARTIFACTS_EVALUATION.md:1-30` maps the repo to the paper and its eight authors and declares it the OSDI'26 artifact; the tree contains the real system (`src/llama-kairox.cpp`, `ggml/include/ggml-kairox.hpp`, `ggml/src/ggml-cuda/dfr-fusion.cu`, sparse CPU/CUDA kernels, `bench_models.sh`), not a stub. Caveat, not a fail: the offline profiling/METIS/predictor-training pipeline is not released — only its GGUF outputs. |
| `H2_no_root` | **pass** | No kernel module, eBPF, `/proc/sys` write or hugepage setup is required by the system. The Docker image in `ARTIFACTS_EVALUATION.md:63-96` is only a CUDA/Python environment and is replayable with conda+pip per `env.md`. `compile_kairox.sh:3-6` calls `apt` but is non-fatal and bypassable with `-DLLAMA_OPENSSL=OFF` (`CMakeLists.txt:116`). Nsight Systems is used only for Fig. 12 (§9.3), which is not on the reproduction path. |
| `H3_hardware_fit` | **pass** | The target hardware *is* the paper's PC-High class: 1 × 24 GB GPU, 16 CPU threads, PCIe 4.0, >64 GB RAM (`§9.1`). `test_kairox.sh:81-95` hard-codes exactly `4090 → gpu_vram=24, threads=16`. PC-Low can be emulated with `-vb 12`. Single-node, single-GPU by construction (`CUDA_VISIBLE_DEVICES=0`, `test_kairox.sh:3`). Concerns: the A5000 is ~3–4× slower than a 4090 in FP16, so absolute t/s and the CPU/I/O balance point shift; and the largest models (ReLUFalcon-40B-Q8 ≈ 43 GB, opt-66b-Q4, opt-30b-Q8) must be dropped or run one at a time to stay inside 257 GB of disk. |
| `H4_obtainable_deps_data` | **pass** | Models/traces: `Anhelor/SPIF-GGUF` on HF is public, non-gated, MIT (checked 2026-09-14); prompts ship in `prompts.txt`. Deps: cmake ≥3.18 (`pip install cmake`), CUDA 12.x toolkit (conda), gcc 12 (present). No proprietary trace. PowerInfer/Q-Infer are optional extras (`ARTIFACTS_EVALUATION.md:28`) and both are public on GitHub anyway. |

## 4. Reproduction plan

**Target.** Figure 9, top row, PC-High panel, restricted to the two 13B models
(**Prosparse-LLaMA2-13B** and **OPT-13B**). Claim under test: *under a 24 GB VRAM budget,
Kairox's decode throughput exceeds llama.cpp's layer-offloading baseline by a large factor
(paper: 7.54× and 6.61×) and exceeds the eager-reload (Neuralink) policy*. This is exactly the
artifact's own pass criterion, `kairox > llama_cpp AND kairox > neuralink`
(`ARTIFACTS_EVALUATION.md:174-178`).

**Scale-down.**
* Use the `high` profile (24 GB, 16 threads) unchanged; it matches the machine.
* Trim `MODELS` in `bench_models.sh:32-38` to the `prosparse-llama-2-13b` and `opt-13b` entries
  (~26 GB each + split files ≈ 70 GB total) and drop ReluFalcon-40B-Q8 / opt-30b-Q8 /
  opt-66b-Q4, which together would blow the disk budget.
* Lower `BENCH_RUNS` from 20 to 8–10 (`bench_models.sh:30`) — the harness already discards runs
  that emit <16 tokens (`tools/completion/completion.cpp:470`) and reports a mean over included
  runs.
* Expect *lower absolute* t/s than the paper (A5000 ≈ 1/3 of a 4090's FP16 throughput) and
  therefore a *larger* Kairox-vs-llama.cpp ratio to be less certain: a slower GPU makes the
  system less I/O-bound relative to the paper, which should if anything help Kairox, but the
  magnitude is a genuine unknown. Treat "ratio > 1 in the same ordering" as the success
  criterion, not "7.5×".

**Steps.**
1. `conda create -n kairox python=3.11 cuda-toolkit=12.2 cmake ninja` (driver 535 supports
   CUDA ≤12.2 natively; avoids the minor-version-compatibility gamble of the prescribed 12.8).
2. `pip install "huggingface_hub[hf_xet]"`; `hf download Anhelor/SPIF-GGUF --include` the five
   files for the two chosen models + `Llama-160M-Chat-v1-Q8_0.gguf` + `opt-125m-Q8_0.gguf`.
3. Point `MODEL_ROOT` (`bench_models.sh:4`) at a writable path instead of `/root/SPIF-GGUF`.
4. Build: `cmake -B build_rel -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON -DGGML_CUDA_GRAPHS=OFF
   -DCMAKE_CUDA_ARCHITECTURES=86 -DLLAMA_OPENSSL=OFF --target llama-completion
   llama-speculative` (i.e. `compile_kairox.sh` minus its `apt` preamble).
5. `bash bench_models.sh high simple` — the smoke path (builds + runs all three backends on one
   model, ~30 min).
6. `bash bench_models.sh high full` with the trimmed model list; then
   `python parse_bench_logs.py high_logs --out results_summary.md --csv results_summary.csv`.
7. Free bonus, same harness: sweep `-vb` (14/18/22/24) via `test_kairox.sh` to recreate the
   shape of Fig. 13(right), which is the same model (OPT-13B) on the same profile.

**Effort.** ≈5 person-days (2 for the conda/CUDA port and first successful build, 1 for
downloads and path surgery, 2 for runs + analysis) + **≈10 GPU-hours** (12 backend×mode×model
configurations × ~10 measured runs of 512 tokens, plus model load time for 26 GB files) +
≈80 GB of disk.

**Level: M.** Not H because: the documented path is Docker + CUDA 12.8 and must be ported;
no expected-results file or plotting script ships with the artifact, so "did it reproduce?" is
judged only by an ordering test; two of the five Fig. 9 baselines (PowerInfer, Q-Infer) are
outside the artifact; and the GPU is a different class from both paper machines. Not L because
a single command builds and runs the whole thing, the harness computes the headline metric
itself, and every input is a public download. The `simple_validation` sub-path alone is close
to H.

## 5. Add-on ideas

### A1 — Score-ordered admission under a constrained reload budget

* **Hypothesis.** We hypothesize that ordering the reload plan by TAM score (load the
  highest-scoring absent groups, evict the lowest-scoring resident ones) instead of by group
  index improves decode throughput and reduces per-token latency variance under tight VRAM
  budgets and tight reload budgets (the 14–18 GB region of Fig. 13 and the I/O-bound layers of
  Fig. 11), compared with the paper's system.
* **Mechanism.** `kairox_reload_plan` scans groups in **ascending index order** to fill
  `groups_to_load` / `groups_to_evict` and then takes the *first* `reload_budget` pairs. When
  demand exceeds budget — exactly the state the adaptive controller drives the system into —
  which groups get admitted is decided by group index, and each load is paired with an arbitrary
  eviction victim at the same list position. Change: carry the top-K scores (already computed on
  the GPU at `llama-graph.cpp:1308`) to the host alongside the load/evict masks, sort load
  candidates by descending score and evict candidates by ascending score, and pair them
  greedily. ~150 LOC plus one extra D2H copy of `n_groups ≤ 1024` floats in the existing
  synchronous plan step.
* **Code locations.** `src/llama-kairox.cpp:41`, `src/llama-graph.cpp:1295`,
  `ggml/src/ggml-cuda/ggml-cuda.cu:2558`, `ggml/include/ggml-kairox.hpp:52`.
* **Motivating evidence.** `src/llama-kairox.cpp:52-88` (index-order selection + positional
  pairing); the paper's own §6 argument that *which* group is resident is what matters; Fig. 13
  shows Kairox's advantage is largest exactly where the budget binds; Fig. 11(right) shows reload
  intensity is actively clamped, so truncation is the common case, not an edge case.
* **Feasibility: H.** Localized to one host function plus a copy; evaluable with the existing
  `-vb` sweep and `--bench-token-latency` harness on this machine; no new data or offline
  pipeline needed.
* **Research value: M.** A reviewer would recognize it as the cache-admission question the paper
  raises but does not close, and the Fig. 13 regime is the one that matters on 24 GB hardware —
  but "score-ordered beats index-ordered" is the expected outcome; only the *magnitude* and the
  interaction with the rate limiter are surprising.
* **Scoop check: `partial`.** Queries: "activation sparsity neuron cache eviction policy GPU CPU
  offloading LLM inference dynamic reload budget"; "admission control cache one-hit wonder expert
  cache prefetch budget score-aware eviction 2026 LLM". Closest work is in the MoE expert-cache
  line — [ExpertFlow](https://arxiv.org/pdf/2510.26730) and
  [Fine-Grained Expert Offloading](https://arxiv.org/pdf/2502.05370) use explicit prefetch/eviction
  priority scores and deadline-constrained prefetch budgets — but at expert granularity in MoE
  models, not neuron groups in dense FFNs, and not against Kairox. Nothing found that redoes
  Kairox's admission order.

### A2 — Implement Algorithm 1 as written: adapt λ, add the τ_load filter, use a measured stall signal

* **Hypothesis.** We hypothesize that the controller described in §7/Algorithm 1 (per-layer
  adaptive **λ** plus the `τ_load = (1−λ)+ε` one-hit-wonder filter, driven by measured per-layer
  reload-wait vs. CPU-FFN time) achieves higher throughput and lower reload volume than the
  released implementation's reload-rate limiter, on models with many short activation windows
  (OPT-family, per Fig. 8), compared with the paper's system as shipped.
* **Mechanism.** (a) Write a per-layer λ into the existing `dfr_ema_coeffs` host tensor, which is
  already re-uploaded to the GPU on every `SCALE_ADD` call (`binbcast.cu:432-440`) — so the
  plumbing for a time-varying λ exists and only the writer is missing. (b) Add the `S > (1−λ)+ε`
  candidate filter before the top-K, either as a bias in the fused mask kernel or as a
  `ggml_shifted_step` mask on `dfr_scores`. (c) Replace the boolean `to_move.empty()` signal with
  real timings: CUDA events around the reload window and a host timer around the CPU sparse-FFN
  split, both already exposed through the scheduler's split anchors. Then A/B the three
  controllers (shipped K-limiter, λ-controller, both) — this is precisely the Top-K / TAM / TAM-T
  comparison of Fig. 10, plus the λ trace of Fig. 11.
* **Code locations.** `ggml/include/ggml-kairox.hpp:168`, `src/llama-kairox.cpp:338`,
  `src/llama-graph.cpp:1300`, `ggml/src/ggml-cuda/binbcast.cu:432`,
  `ggml/src/ggml-cuda/dfr-fusion.cu`.
* **Motivating evidence.** §7 and Algorithm 1 lines 1–15 specify λ-adaptation and τ_load; the
  code adapts `dfr_clamp_k` instead (`ggml-kairox.hpp:194-201`) and has no ε (grep). Fig. 15
  attributes ~15% of the end-to-end gain to `+ANB`, so the mechanism is load-bearing. Fig. 11
  is not derivable from the artifact, which makes the comparison genuinely open.
* **Feasibility: H.** All three pieces are localized; the λ upload path already exists; the
  evaluation is the existing benchmark plus counters the code already keeps
  (`reload_count`, `reload_planned_count` at `ggml-kairox.hpp:91-92`).
* **Research value: M.** Closing a documented design/implementation gap and measuring which
  controller actually wins is useful and either outcome is informative (if the K-limiter wins,
  the paper's central §7 story is weaker than claimed); but it is a re-derivation of the paper's
  own design rather than a new idea, so a reviewer would call it careful, not novel.
* **Scoop check: `clear`.** Queries: "Kairox OSDI 2026 online neuron balancing"; "DynamicInfer
  runtime-aware sparse neuron offloading ICLR 2026 scheduler eviction". The only citing/adjacent
  system found is [DynamicInfer (ICLR 2026)](https://openreview.net/forum?id=CvjmvjlczZ), which is
  concurrent work with its own hierarchical cache and load-aware activation — it does not
  evaluate Kairox's controller. Nobody has published a Kairox re-implementation study.

### A3 — Pinned staging for neuron reloads, and re-tuning group size on top of it

* **Hypothesis.** We hypothesize that DMA-ing neuron groups out of **pinned** host memory (a
  double-buffered staging ring, or registering the FFN weight buffers) raises achieved PCIe
  bandwidth and lets Kairox run at a *smaller* group size at equal bandwidth — improving
  throughput at a given VRAM budget by cutting over-fetch — compared with the paper's system.
* **Mechanism.** With `-cffn`, the FFN weights are placed in `ggml_backend_cpu_buffer_type()`
  (`common/common.h:994-996`), i.e. ordinary malloc'd, **pageable** memory; the reload path then
  issues `cudaMemcpyAsync(..., cudaMemcpyHostToDevice)` directly from it
  (`ggml-cuda.cu:2587-2594`). Copies from pageable memory are staged by the driver and are not
  truly asynchronous, which is a plausible explanation for Table 2's 18–21% of peak at GS=1 and
  ~70% at GS=32. Change: allocate a pinned staging ring in the I/O executor (or use
  `ggml_backend_cuda_host_buffer_type()`, already used for the cache-manager tensors at
  `src/llama-kairox.cpp:264`, for the hot fraction of FFN weights), memcpy group → pinned →
  DMA, and double-buffer against the existing reload window (`reload_window_size = 4`,
  `ggml-kairox.hpp:93`). Then sweep `GS` — which requires re-deriving the offline grouping, so
  the honest version of this add-on also rebuilds a minimal co-activation + `pymetis` grouper
  that emits a compatible split GGUF (the consumed keys are `ffn_group_size`,
  `ffn_normalized_pattern`, `blk.N.ffn_reorder_perms`, `src/llama-kairox.cpp:140-142, 256`).
* **Code locations.** `ggml/src/ggml-cuda/ggml-cuda.cu:2580`, `common/common.h:994`,
  `src/llama-kairox.cpp:262`, `ggml/include/ggml-kairox.hpp:106`.
* **Motivating evidence.** Table 2 is the paper's own evidence that PCIe utilization is far below
  peak, and §5.2 frames GS purely as a granularity trade-off without considering the host-memory
  pinning that bounds the achievable bandwidth. All shipped splits use only GS=16 or 32
  (file-name suffixes in `bench_models.sh:17-38`), so the GS trade-off curve of §5.2 is asserted
  but never swept in the artifact.
* **Feasibility: H** for the pinning half (a few hundred LOC in the reload path, measurable
  immediately with the existing `reload latency` accounting and end-to-end benchmark);
  **M** if the GS sweep is included, because the offline grouper must be rewritten. Scope the
  project as "pinning first, GS sweep if time permits".
* **Research value: M.** The bandwidth result would be an engineering win a reviewer expects;
  what raises it above pure polish is the second-order claim — that better transfer efficiency
  *changes the optimal granularity*, and therefore the over-fetch tax, which is a design-space
  statement the paper makes without evidence.
* **Scoop check: `partial`.** Queries as in A1 plus "pinned host memory async DMA weight
  streaming llama.cpp". Pinned-buffer streaming is standard practice and appears in the MoE
  offloading literature (e.g. [SeqMoE](https://arxiv.org/html/2609.12978),
  [ExpertFlow](https://arxiv.org/pdf/2510.26730)) and in llama.cpp's own MoE-streaming
  discussions ([ggml-org/llama.cpp#24528](https://github.com/ggml-org/llama.cpp/discussions/24528)),
  so the technique is not novel; its interaction with co-activation group size in Kairox is not
  published.

### A4 — Does online neuron balancing survive realistic context lengths?

* **Hypothesis.** We hypothesize that Kairox's speedup over llama.cpp shrinks substantially as
  context grows from 1k to 8k–32k tokens — because the KV cache takes VRAM away from the neuron
  cache (the budget is computed once, after context allocation) and because attention takes a
  growing share of a decode step — and that a context-aware budget policy (KV offload via
  `-nkvo`, or a neuron-cache floor) recovers part of the loss, compared with the paper's system.
* **Mechanism.** The VRAM budget for the neuron cache is `min(budget − already_used, free)`
  computed **once** at context creation (`src/llama-kairox.cpp:102-130`), where `already_used`
  includes the fully pre-allocated KV cache. At ctx=1024 (the paper's setting,
  `test_kairox.sh:6`) the KV cache is negligible; at 32k on a 13B model it is several GB, i.e. a
  direct subtraction from `n_group_cache_budget` (`src/llama-kairox.cpp:177-194`). Build a
  long-context workload (long ShareGPT/LongBench prompts through `--bench-prompt-file`), measure
  decode throughput and neuron-cache occupancy vs. ctx for llama.cpp / Neuralink-config /
  Kairox, then add policies: (i) `-nkvo` to push KV to host, (ii) a minimum guaranteed
  neuron-cache size with KV spill, (iii) layer-skewed re-allocation using the existing
  `ffn_normalized_pattern` weighting.
* **Code locations.** `src/llama-kairox.cpp:102`, `src/llama-kairox.cpp:177`,
  `common/arg.cpp:2026`, `test_kairox.sh:6`, `tools/completion/completion.cpp:391`.
* **Motivating evidence.** §9.2 caps context at 1024 tokens and output at 512 for *every*
  experiment; the paper's target use case (a local assistant on a consumer PC) routinely runs
  8k+ contexts, so the headline speedups are measured in the regime most favourable to
  weight-side optimization. Nothing in §9 varies context length. The static, one-shot budget
  computation is visible in the code.
* **Feasibility: M.** No new kernels, but it needs a new long-context workload generator, a way
  to log neuron-cache occupancy per configuration, and more compute (32k-context runs on 13B
  models are minutes each). Memory is fine: 125 GB host RAM absorbs offloaded KV. Cross-cutting
  only in that budget policy touches context creation.
* **Research value: H.** This is the "unexplored regime that a reviewer at the original venue
  would care about" case: it probes whether the paper's central claim generalizes beyond a
  1k-token bench, and both outcomes are informative — if the speedup holds, the paper is
  stronger than it shows; if it collapses, the KV/weight-cache co-partitioning problem becomes
  the interesting follow-on.
* **Scoop check: `partial`.** Queries: "KV cache growth competing with weight cache GPU memory
  elastic partitioning long context sparse offloading"; "co-partition GPU memory between
  offloaded weight cache and KV cache dynamically LLM inference consumer GPU 2026". KV-vs-weight
  memory tension is heavily discussed in the KV-offloading literature
  ([KVSwap](https://arxiv.org/pdf/2511.11907), [KVDrive](https://arxiv.org/pdf/2605.18071)), and
  long-context KV offloading for on-device inference is an active area — but none of it is
  paired with *neuron-level* weight caching, and no paper evaluates Kairox at long contexts.

### A5 — Batch-aware group scoring for speculative and multi-request decoding

* **Hypothesis.** We hypothesize that a batch-aware group score (weighting a group by how many
  sequences in the batch activate it, and/or scoring per-request and unioning at admission time)
  improves decode throughput at draft widths of 8–16 and at 4–8 concurrent requests, relative to
  Kairox's single global TAM score, compared with the paper's system.
* **Mechanism.** At batch >1 the activation mask is OR-ed across tokens: `ggml_sum_cols` over the
  predictor output (`src/llama-graph.cpp:1301-1303`) and the multi-token branch of the mask
  kernel (`dfr-fusion.cu:175-185`) collapse all tokens into one group-activation intensity,
  which is normalized by `sparse_idx->ne[1] * group_size` (`llama-graph.cpp:1307`). A group
  activated by one sequence out of eight scores the same as one activated weakly by all eight.
  Change: keep a per-column count in the DFR-update kernel (it already accumulates per-column at
  `dfr-fusion.cu:30-46`) and expose a coverage-weighted score; additionally raise the dense-GEMM
  cutover threshold `b->ne[1] <= 8` (`src/llama-graph.cpp:1284`) to a measured value. Evaluate
  with `--draft-max` sweeps in `test_kairox.sh:226-239` and, if the server path can be made to
  work, with `llama-server -np N`.
* **Code locations.** `src/llama-graph.cpp:1284`, `src/llama-graph.cpp:1301`,
  `ggml/src/ggml-cuda/dfr-fusion.cu:151`, `examples/speculative/speculative.cpp:608`,
  `test_kairox.sh:226`.
* **Motivating evidence.** §3.1's first motivating bottleneck is *batch* workload expansion
  (throughput saturating at batch 4–8, CPU latency 102.8 → 551.7 ms), yet §9.2 evaluates only
  batch 1 plus 5-token speculative decoding, and §9.2 itself admits llama.cpp sometimes *beats*
  the sparse systems under speculative decoding because "dense batched GEMMs can surpass sparse
  kernels". Fig. 9(bottom) has several sub-1× bars for the sparse baselines. So the batched
  regime is both the paper's stated motivation and its weakest results.
* **Feasibility: M.** The scoring change is contained, but the build targets exclude
  `llama-server` (`compile_kairox.sh:43`) and the Kairox path's interaction with continuous
  batching is untested — getting a multi-request harness working is real integration risk; the
  speculative-only version is safer and is H.
* **Research value: M.** The regime matters and the paper under-serves it, but the known result
  from the sparsity literature is that union sparsity collapses with batch size, so a modest,
  partly predictable gain is the likely outcome.
* **Scoop check: `partial`.** Queries: "batched decoding union activation sparsity diminishes
  batch size neuron offloading scheduling per-request". [Polar Sparsity
  (NeurIPS 2025)](https://arxiv.org/pdf/2505.14884) directly studies the collapse of MLP union
  sparsity under batching and moves the sparsity to attention heads — it pre-empts the
  *diagnosis* but not the offloading/admission policy, and it does not do GPU–CPU weight
  balancing. [DynamicInfer](https://openreview.net/forum?id=CvjmvjlczZ) also does token- and
  sentence-level scheduling but on a single stream.

## 6. Risks and open questions

1. **Paper ≠ artifact on the §7 controller.** The released code adapts a reload-rate cap, not λ
   (`ggml/include/ggml-kairox.hpp:194-201` vs. Algorithm 1). Fig. 11 (λ evolution) is therefore
   not reproducible as shipped, and the `+ANB` column of Fig. 15 measures a different mechanism
   from the one described. Anyone quoting "Kairox's adaptive λ" must check this first.
2. **τ_load / ε is absent from the code** (`src/llama-graph.cpp:1300-1318`), so §6's one-hit-wonder
   filtering happens only implicitly through momentum decay and top-K. Any add-on that "adds
   thresholding" is really implementing the paper, not extending it — frame it honestly.
3. **The offline stage is not released.** No profiling, predictor training, co-activation graph,
   or METIS driver. Add-ons that need new models, new group sizes, or new architectures must
   rebuild that pipeline from the paper description (§5.2, §8) and from the GGUF keys the loader
   expects (`src/llama-kairox.cpp:140-142`). Budget ≥1 person-week for that if it is on the
   critical path; prefer add-ons that reuse the shipped splits.
4. **Two of five Fig. 9 baselines are missing**, and "Neuralink" is a configuration of Kairox
   itself (`test_kairox.sh:97-116`), not the original system (§9.1 says it was re-implemented
   because it is closed source). Comparisons against Neuralink are therefore comparisons against
   the authors' interpretation; do not present them as third-party validation.
5. **GPU class mismatch.** An RTX A5000 has roughly a third of a 4090's FP16 throughput at the
   same 24 GB and PCIe 4.0. This shifts where the CPU/I/O balance point sits and will change the
   *magnitude* of every speedup. All add-on claims must be stated relative to the re-measured
   baseline on this machine, never against the paper's absolute numbers.
6. **CUDA/driver risk.** The artifact prescribes CUDA 12.8; driver 535 supports 12.2 natively.
   Minor-version compatibility usually works, but the safe route is a conda CUDA 12.2 toolkit.
   Whether the current llama.cpp base still compiles cleanly against 12.2 is **unclear** from
   reading alone — upstream CI (`.github/workflows/build.yml:813,852`) tests 12.4/12.6 only.
   This is the single largest first-week schedule risk.
7. **Disk.** The full `SPIF-GGUF` set exceeds the ~257 GB free (one advertised file is 62.3 GB).
   Selective download is mandatory and must be planned per experiment.
8. **The pageable-memory claim in A3 is a code-reading inference, not a measurement.**
   `common/common.h:994` places FFN weights in the plain CPU buffer type and
   `ggml-cuda.cu:2592` DMAs from it; whether that actually costs the bandwidth Table 2 implies
   can only be settled by running. Treat "pinning helps" as the hypothesis, not the premise.
9. **Artifact badge status unconfirmed.** `ARTIFACTS_EVALUATION.md:13-21` states the artifact was
   submitted for **Artifacts Available only** (explicitly not Functional or Reproduced). The
   USENIX presentation page returned HTTP 403 to automated fetching, so the awarded badge could
   not be verified independently. Assume no Functional/Reproduced badge.
10. **Repo is young and low-traffic** (created 2026-05-05, last push 2026-05-19, 2 stars, 0 open
    issues): no upstream community to ask when a build breaks, and no sign of post-AE fixes.

## 7. Evidence index

**Paper.** §1 (contributions, headline speedups); §2.1–2.2 (activation sparsity, FFN share,
hybrid vs. GPU-only); §3.1 + Fig. 3 (CPU bottleneck, batch 1→20 latency 102.8→551.7 ms) +
Fig. 4 (semantic drift) + Fig. 5 (LRU strawman); §3.2 (three challenges); §4 + Fig. 6 (system
overview, Table 1 notation); §5.1 + Fig. 7 (adjacent prediction, pipeline variants); §5.2 +
Table 2 (PCIe bandwidth vs. group size, METIS, Eq. 1–4); §6 + Fig. 8 (reactivation heatmaps,
TAM Eq. 5, τ_load); §7 + Algorithm 1 (λ feedback control); §8 (implementation, 5,700 LOC,
three streams, argsort ≤1024 groups); §9.1 (PC-Low/PC-High specs, models, ShareGPT, baselines);
§9.2 + Fig. 9 (end-to-end, page 11 image); §9.3 + Figs. 10, 11, 12, 13 (policy ablation, λ
evolution, GPU utilization, VRAM-budget sweep, page 12 image) + Fig. 14 (TPOT);
§9.4 + Fig. 15 (component ablation); §9.5 + Table 3 (non-ReLU); §9.6 + Fig. 16, Table 4
(predictor accuracy, downstream accuracy); §10 (related work, MoE left to future work).

**Repository** (`repo/`).
`README.md`; `ARTIFACTS_EVALUATION.md`; `bench_models.sh`; `test_kairox.sh`;
`compile_kairox.sh`; `parse_bench_logs.py`; `prompts.txt`; `CMakeLists.txt:116`;
`src/llama-kairox.h`; `src/llama-kairox.cpp:41-89, 91-131, 133-393` (notably `:52-88`,
`:102-130`, `:140-142`, `:177-194`, `:256-258`, `:262-269`, `:338`, `:384`);
`src/llama-graph.cpp:1240-1275, 1277-1293, 1295-1319, 1361-1541`;
`ggml/include/ggml-kairox.hpp:12-101, 106-277` (notably `:48-50`, `:91-93`, `:168-204`);
`ggml/src/ggml-cuda/ggml-cuda.cu:2500-2549, 2558-2578, 2580-2648, 3586-3620`;
`ggml/src/ggml-cuda/dfr-fusion.cu:1-232`; `ggml/src/ggml-cuda/binbcast.cu:27-34, 432-440`;
`ggml/src/ggml-cpu/ggml-cpu.c:1692-1891, 2371-2470`; `ggml/src/ggml.c:2276-2295, 5432-5440`;
`common/arg.cpp:1233, 2026, 2330-2351`; `common/common.h:991-996`;
`tools/completion/completion.cpp:391-526`; `examples/speculative/speculative.cpp:608-720`;
`.github/workflows/build.yml:813, 852`.

**Driver data.** `repo_facts.json` (head commit 6eeba16 @ 2026-05-19, 2,602 files, 148.7 MB,
MIT, 2 stars, red-flag greps for sudo/docker/multi-gpu — all traced to upstream llama.cpp CI,
docs and unrelated backends, none to the Kairox path); `fetch_result.json`; `meta.json`.

**Web.** `https://huggingface.co/Anhelor/SPIF-GGUF` (public, non-gated, MIT — checked
2026-09-14); `https://www.usenix.org/conference/osdi26/presentation/jiang-yapeng` (403 to
automated fetch; title/authors confirmed via search);
[DynamicInfer, ICLR 2026](https://openreview.net/forum?id=CvjmvjlczZ);
[Polar Sparsity, NeurIPS 2025](https://arxiv.org/pdf/2505.14884);
[ExpertFlow](https://arxiv.org/pdf/2510.26730);
[Fine-Grained Expert Offloading](https://arxiv.org/pdf/2502.05370);
[Q-Infer, TACO 2025](https://dl.acm.org/doi/full/10.1145/3764589);
[PowerInfer artifact](https://github.com/Tiiny-AI/PowerInfer).
