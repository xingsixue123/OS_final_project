# UniCache: Unifying Prefix Cache Eviction for Heterogeneous LLM Serving Workloads

Venue: ACM SIGMETRICS / POMACS Vol. 10, No. 2, Article 54 (June 2026).
Authors: Bei Ouyang (Rice), Yifan Qiao (UC Berkeley), Jiarong Xing (Rice).
Repo: https://github.com/xsyslab/UniCache (head commit 2026-06-04, Apache-2.0, 7 stars).

## 1. Paper summary

**Problem.** Prefix caching reuses KV states across requests that share a prompt prefix. GPU
memory is small relative to KV footprint, so the *eviction* policy determines the achievable hit
ratio. Production engines (vLLM, SGLang) use LRU, and recent work (WA, ATC'25 [34]) partitions by
workload but still runs LRU inside every partition. The paper's motivating measurement (Fig. 1 +
Table 1, p. 2) shows no single heuristic dominates: LFU wins on MASH-QA, LRU/WA win on ShareGPT,
and on the mixed workload WA is best overall but *worst* on the MASH-QA component (0.5083 total for
WA vs LRU 0.4247 on MASH-QA, but WA 0.6717 vs LRU 0.7457 on ShareGPT).

**Key idea.** Two distinct reuse mechanisms exist — *session reuse* (multi-turn, recency-driven,
inter-turn interval is log-normal and task-dependent) and *structural reuse* (single-turn,
template-driven, value decays with the block's positional offset in the prompt). Manage each in
its own queue with its own priority metric, then reconcile queues with a global "hit efficiency"
weight.

**Design (§5).**
- Four+ queues: an *evict-first* queue (decode blocks of single-turn requests, and untemplated
  single-turn prefill blocks), *session-reuse* queues (chat and agentic, separate because their
  inter-turn interval distributions differ), and a *structural-reuse* queue for templated
  single-turn traffic.
- Local priority (Alg. 1, p. 14): multi-turn `s_q = 1 − IntervalCDF(t_now − t_last)` with a
  log-normal CDF fitted offline per task; single-turn `s_q = 1 − offset/max_offset`.
- Global stage (Alg. 2, p. 14): `E_q = H_q / C_q` (hit tokens per unit capacity), normalized by the
  mean, temperature-scaled `(E_q/Ē)^{1/T}`, clipped to `μ ± 2σ`, EMA-smoothed into `α_q`; evict
  `argmin_q α_q · s_q`. The evict-first queue is always drained first.

**Characterization (§4).** Inter-session reuse is 0.72 % (ShareGPT) / 0.044 % (AgentBank) of reused
blocks (Fig. 5); cross-task reuse < 0.01 % (Fig. 7a); decode-block reuse ≤ 3.17 % vs 84–97 % for
prefill on templated tasks (Fig. 7b); tail-first eviction beats head-first (Fig. 8b).

**Simulator (§3).** vLLM's CPU control plane (scheduler + KVCacheManager) is kept; the GPU worker is
replaced by an `OutputSimulator` that replays trace tokens. Virtual clock advanced by a fitted
power-law prefill model (`5.56e-5·BS^0.992·L^1.034`, R²=0.999, Fig. 3) and a constant TPOT. Fidelity:
hit-ratio deviation vs real GPU < 0.0018 (Fig. 4); ~30× faster than GPU execution (4692 s → 150 s).

**Evaluation setup (§6.1).** Baselines LRU, LFU, FIFO, LeCaR, ARC, WA, OPT-Offline. Models
Llama-3.2-1B / 3B / 8B. Three synthesized heterogeneous traces (#1 multi-turn-dominant ~80 %,
#2 balanced, #3 single-turn-dominant ~80 %), each ~1 h, built from 6 task datasets. Cloud
instances with A6000/A100/H200.

**Headline numbers.** Fig. 10 (p. 18, 3 models × 3 traces × budgets 0.5A/0.7A/0.9A): UniCache has
the highest hit ratio in every configuration, +3.86 %–17.32 % over online baselines on average.
Table 5 (p. 19): average QTTFT on a single A100 — Trace#1 UniCache 3.87 s vs LRU 4.94, LFU 8.47,
OPT-offline 3.84; 1.10×–3.63× reduction. Ablation (Fig. 12, p. 20): removing Stage 2 costs
5.36 %–31.30 % hit ratio; UniCache-OPT adds ≤ 0.74 %.

**Stated limitations / assumptions.** (i) Task labels are assumed available from request metadata
(§6.6, "Task type classification") — never evaluated; (ii) log-normal parameters are fitted offline
from historical traces (§5.2); (iii) no public trace has both content and timestamps, so traces are
synthesized (§6.1); (iv) evaluation optimizes hit ratio, QTTFT is measured only at one budget
(0.9A) with one model.

## 2. Artifact audit

### Repo structure

The repo is a **fork of vLLM v0.8.5** (matching the paper's §6 statement) with the simulator and the
eviction policies added. 2440 files, 23.5 MB, 381 k lines of Python — but almost all of that is
upstream vLLM. The UniCache-specific code is a handful of files.

| paper component | code path |
|---|---|
| Eviction policies (LRU/LFU/FIFO/WA/LeCaR/ARC/OPT/OFFSET) | `vllm/core/evictor.py` (`LRUEvictor`:265, `WAEvictor`:375, `LFUEvictor`:529, `FIFOEvictor`:605, `ARCEvictor`:694, `LeCaREvictor`:962, `OPTEvictor`:100, `OffsetEvictor`:178) |
| **UniCache policy** (§5, Alg. 1) | `vllm/core/evictor.py:1254` `SimpleHYBRIDEvictor`; `_naive_evict`:1429 (two-stage eviction), `_select_queue_name`:1302 (queue assignment), `SimpleHYBRIDlockMetaData.calculate_priority`:1214 (local priority `s_q`) |
| Hit-efficiency weighting (§5.3, Alg. 2) | `vllm/core/evictor.py:1702` `update_alpha_balance` (E_q, temperature `T=0.2`, clip `μ±2σ`, EMA `smooth=0.1`), invoked every 10 requests (`evictor.py:1468`) |
| Log-normal reuse horizons (§5.2) | `vllm/core/evictor.py:1177` `TASK_CONFIG` (hard-coded `(μ,σ)` per task: chat `(4.77,1.279)`, agentic `(1.81,1.092)`, plus image/search/file), `_cached_lognorm_cdf`:1167 |
| Task/decode-block labelling (Impl. 3–4) | `vllm/core/block/prefix_caching_block.py:1005` `mark_blocks_simple_hybrid_atrribute` — task type is derived from **hard-coded session-id string prefixes** (`"ShareGPT-multi-turn"`, `"alfred_"`, `"apps_"/"mind2web_"` → `SINGLE_TURN_RANDOM` → evict-first) at lines 1019–1034 |
| Per-queue hit statistics (H_q) | `vllm/simulator/output_simulator.py:94` `update_hit_rates` → `tracked_hit_stats` (line 146), called from `vllm/core/scheduler.py:1607` |
| Simulator loop (Alg. 3) | `vllm/simulator/simulator.py:251` `engine_loop`; arrival generation `init_heap`:210; inter-turn log-normal sampling `_maybe_schedule_next_turn`:393 |
| Virtual clock / TTFT power law | `vllm/simulator/simulator.py:276-303` (`eval` of `--simulator-ttft` expression), `vllm/simulator/timer_utils.py` |
| Worker replacement (Fig. 2) | `vllm/engine/llm_engine.py:288` (`model_executor` not constructed in simulation mode), `:496` (KV cache allocation skipped), `vllm/simulator/output_simulator.py` |
| OPT-Offline / OPT-Online (§4.3, §6.5) | `vllm/simulator/opt_utils.py`, `OPT/readme.md`, `vllm/core/evictor.py:100` |
| WA baseline online interval fitting | `vllm/simulator/wa_helper.py` (exponential fit, periodic refit) |
| Entry points | `run_simulation.py` (CPU simulator), `run_gpu.py` (real GPU, §6.4 QTTFT) |
| Trace configs (Traces #1–#3 etc.) | `TaskData/Hybrid/test1..test9/tasks_config.yaml` + `run.sh` |
| Data preparation | `TaskData/*/prepare_data.py`, `TaskData/*/data.sh`, `prepare_session_data.py`, `models/download.sh` |

### Build route on this machine

The README install script (README.md lines 35–78) creates a conda env with Python 3.10, installs
**CPU** torch 2.6.0 wheels and `requirements/{build,common,cpu}.txt`, then pins
`transformers==4.53.2`, `tokenizers==0.21.2`. It **never runs `pip install -e .`**, and it does not
need to: `run_simulation.py` sits at the repo root and imports the in-tree `vllm/` package, and in
simulation mode the model executor is never constructed (`vllm/engine/llm_engine.py:288-292`), the
KV cache is never allocated (`:496`), and `LLM(..., load_format="dummy")` (`run_simulation.py:188`)
means no weights are loaded. The missing compiled extension is tolerated — `vllm/_custom_ops.py:17-21`
wraps `import vllm._C` in try/except and only logs a warning. So the headline (simulator) results
need **no compiler, no CUDA, no GPU**.

Two porting frictions, both fixable:
- The install script hard-codes `/home/shadeform/anaconda3/bin/conda` (README.md:41) — one-line edit.
- Platform auto-detection (`vllm/platforms/__init__.py:50-75`) selects the CUDA platform whenever
  nvml reports a GPU *and* the installed vllm version string does not contain "cpu". On this machine
  (an A5000 is present, and vllm is not pip-installed at all) the CUDA platform will likely be
  selected even though `--device cpu` is passed. The demo scripts export `VLLM_PLATFORM=cpu`
  (`demo/run.sh:3`), which is **not a recognised env var in this vLLM version** (`vllm/envs.py` only
  has `VLLM_TARGET_DEVICE`). Since the executor is never built this is probably harmless, but it is
  the most likely first-run stumbling block; worst case one installs a CPU-tagged vllm dist-info or
  patches `cpu_platform_plugin`.

For the optional GPU result (§6.4 / Table 5), `run_gpu.py` runs real vLLM on CUDA, so the fork must
be compiled. `use_existing_torch.py` is present at the repo root, so `VLLM_USE_PRECOMPILED=1 pip
install -e .` (python-only build against an upstream 0.8.5 wheel) is the cheap route; a full source
build against conda-installed CUDA 12.1/12.4 + torch 2.6 also works on sm_86. No root needed either
way. `demo/run_gpu.sh` also hard-codes `CUDA_VISIBLE_DEVICES=1` (we have device 0 only) and the
optional LMCache path in `run_gpu.py:239-258` calls `run_simulation` twice, the second time with an
unbound `llm` — a latent bug, avoid `--enable-lmcache`.

### Dependency pins and their age

All pins are vLLM 0.8.5-era (early/mid 2025): torch 2.6.0 CPU, `transformers>=4.51.1` overridden to
4.53.2, `outlines==0.1.11`, `xgrammar==0.1.18`, `compressed-tensors==0.9.3`, `triton==3.2.0`
(`requirements/common.txt`, `requirements/cpu.txt`). Everything is pip-installable in user space;
nothing requires a system package. Python 3.10 via conda (machine default is 3.12, but conda envs
with any version are allowed per `env.md`).

### Data / model sources

| dataset | source in repo | obtainable? |
|---|---|---|
| ShareGPT | `wget` from `huggingface.co/datasets/anon8231489123/ShareGPT_Vicuna_unfiltered` (`TaskData/SharedGPT-multi-turn/readme.md:4`) + `clean_ShareGPT_V3.py`, `deduplicate.py` | yes, public, non-gated |
| AgentBank (alfred, apps) | `load_dataset("Solaris99/AgentBank", task)` (`TaskData/AgentBankData/prepare_agentbank_data.py:28`) + `Alfred_scale_up.py` | yes, public HF |
| CodeParrot | `datasets.load_dataset` in `TaskData/Codeparrot/prepare_data.py:8` | yes, public HF |
| MASH-QA | authors' Google Drive folder (`TaskData/mashqa_data/readme.md:2`) | yes; original MASH-QA is also public on GitHub if the Drive link rots |
| ToolBench | a personal OneDrive link to the Preble dataset `G1_workload_updated_input_output_lengths_4096.json` (`TaskData/ToolBench/readme.md:1`) | **weakest link** — public but on a personal share; StableToolBench on HF is a named substitute |
| Qwen-Bailian traces, CC-Bench trajectories | only used offline to fit (μ,σ); the fitted constants are already in `evictor.py:1177` and in the `tasks_config.yaml` files | not needed to reproduce |
| model files | `models/download.sh` pulls **ungated** `unsloth/Llama-3.2-1B-Instruct`, `unsloth/Llama-3.1-8B-Instruct`, `Qwen/Qwen2.5-14B` with `--exclude "*.safetensors"` | yes — only config + tokenizer are needed, no gated Meta weights |

Disk: the tokenized `*_session_data.jsonl` files store full token-id lists as JSON and will be tens
of GB for ShareGPT-scale inputs; ~257 GB free is comfortable but not unlimited.

### Eval scripts present / absent

Present: a self-contained smoke test (`demo/run.sh` + the 20-session `demo/ShareGPT_cleaned_valid_session_data_head20.jsonl`);
per-trace sweep scripts `TaskData/Hybrid/test{1..9}/run.sh`; OPT trace-collection and replay
(`OPT/run_profile.sh`, `OPT/run_opt.sh`, `TaskData/Hybrid/test1/run_opt.sh`); per-run result dumping
(`vllm/simulator/simulator.py:420` `save_result` → `summary.json` with `global_hit_rate`, plus
`avg_qttft`/`avg_ttft` in GPU mode).

Absent / broken:
- **No aggregation or plotting script for Fig. 10 / Fig. 11 / Table 5.** Only `plot_hit_rates`
  (per-run histogram) exists in `vllm/simulator/utils.py`. The team must write ~50 lines to walk
  `result/**/summary.json` and produce the curves.
- `TaskData/Hybrid/test{2..9}/run.sh` and `test1/run_opt.sh` pass `--tag` and `--enable-hybrid-opt`,
  which **do not exist** in `run_simulation.py`'s argparse (lines 16–139) → `argparse` will abort.
  Only `TaskData/Hybrid/test1/run.sh` is consistent with the current CLI.
- Model paths in the sweep scripts are absolute to the authors' machine
  (`/root/nfs/download/Llama-3.2-1B-Instruct`).
- The paper's x-axis (0.5A / 0.7A / 0.9A of post-weights GPU memory) is **not** the script's unit
  (`--simulator-num-gpu-blocks` 50000…100000 at `--block-size 8`); the mapping must be re-derived
  from the model's per-token KV footprint and the GPU's memory. Nothing in the repo documents it.
- Only `TaskData/Hybrid/test1` and `test9` ship the OPT profile scripts; the trace-#1 config
  (`test1/tasks_config.yaml`) references `Llama-3.1-8B-Instruct`-tokenized data, while the run
  script passes a 1B model — the tokenizers are identical for Llama-3.x, so this is benign, but it
  shows the configs were not cleaned up.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | The paper states "The code is available at https://github.com/xsyslab/UniCache" (§6, p. 15); `xsyslab` is the last author's lab org. The repo contains the actual system, not a stub: `vllm/core/evictor.py:1254` `SimpleHYBRIDEvictor` implements Alg. 1 (evict-first drain at :1433, per-queue candidates at :1448, `argmin α_q·s_q` at :1479), `:1702` implements Alg. 2, and `vllm/simulator/` implements the §3 simulator. All seven baselines are implemented in the same file. |
| `H2_no_root` | **pass** | Headline path is `python run_simulation.py` on CPU: executor and KV cache allocation are skipped (`vllm/engine/llm_engine.py:288-292`, `:496-497`), weights are dummy (`run_simulation.py:188`), `vllm._C` import failure is non-fatal (`vllm/_custom_ops.py:17-21`). The `sudo`/kernel-module/RDMA/multi-GPU red flags in `repo_facts.json` all come from inherited upstream vLLM CI and docs (`.github/workflows/scripts/cuda-install.sh`, `docs/source/getting_started/installation/ai_accelerator/neuron.inc.md`, `.buildkite/*`), none of which is on the artifact's run path. `docker/Dockerfile` is upstream vLLM's and is replaced by the README's conda recipe. No perf counters, eBPF, KVM or `/proc/sys` writes anywhere in the simulator. |
| `H3_hardware_fit` | **pass** | Fig. 10/11 and Fig. 12 — the paper's main results — come from the CPU simulator (§6.1: "We conducted latency experiments (Section 6.4) on real GPUs, while the remaining results were obtained from our simulator"), which needs no GPU at all; the A100/H200 labels only set the block budget. 16 cores / 125 GB RAM are ample (paper reports 150 s per simulated trace). The single GPU result (Table 5, §6.4, Llama-3.1-3B on one A100, budget 0.9A) scales down to our 24 GB A5000: `run_gpu.py:255` uses `load_format="dummy"`, so a 1B or 3B model with a reduced `--simulator-num-gpu-blocks` fits easily (the assertion at `vllm/engine/llm_engine.py:452` only requires the *real* block count ≥ the requested one). No multi-GPU or multi-node requirement (§6.6 "Distributed inference" says the policy is TP-agnostic; `--tensor_parallel_size` defaults to 1). |
| `H4_obtainable_deps_data` | **pass** | Deps are pip/conda-only (`requirements/common.txt`, `cpu.txt`, README.md:63-75). Datasets: ShareGPT (HF, `TaskData/SharedGPT-multi-turn/readme.md:4`), AgentBank (HF `Solaris99/AgentBank`, `prepare_agentbank_data.py:28`), CodeParrot (HF, `TaskData/Codeparrot/prepare_data.py:8`), MASH-QA (authors' Google Drive, `TaskData/mashqa_data/readme.md:2`), ToolBench (public Preble OneDrive share, `TaskData/ToolBench/readme.md:1`). No proprietary trace is needed to run: the Qwen-Bailian production trace is only used to fit (μ,σ), and the fitted constants are hard-coded (`evictor.py:1177-1183`) and duplicated in the yaml configs. Models: `models/download.sh` uses **ungated** `unsloth/*` mirrors and excludes safetensors — only config/tokenizer are required. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** Fig. 10(a) (p. 18): *Trace #1, Llama-3.2-1B, hit ratio vs KV-cache budget for
LRU / LFU / FIFO / LeCaR / ARC / WA / OPT-Offline / UniCache.* Claim under test: UniCache attains the
highest hit ratio among online policies at every budget, and LFU collapses on multi-turn-dominant
traffic (the paper quotes 92.32 % for UniCache vs 91.64 % LRU, 91.19 % FIFO, 79.42 % LFU at 0.7A).
This single figure carries the paper's central claim and needs zero GPU time.

**Scale-down.**
- CPU simulator only; no GPU, no model weights (`load_format="dummy"`).
- Keep `TaskData/Hybrid/test1/tasks_config.yaml`'s six tasks but cut `max_record` from
  1800 → 600 (single-turn tasks) and 500 → 200 (ShareGPT, alfred) for the first pass, and scale
  `--simulator-num-gpu-blocks` down proportionally so the cache-pressure regime is preserved
  (hit ratio depends on the *ratio* of working set to cache, so both must shrink together). Re-run
  at full size once the pipeline works.
- Sweep 3 budgets (the repo's 50000 / 70000 / 100000 blocks at `--block-size 8`) × 8 policies = 24
  runs instead of the paper's 9-panel grid.
- Report the ordering of policies and the UniCache–LRU gap, not the absolute hit ratios (absolute
  values depend on the re-derived budget mapping and on the trace subsample).

**Steps.**
1. conda env (Python 3.10) + CPU torch 2.6.0 + `requirements/{build,common,cpu}.txt` +
   `transformers==4.53.2`; fix the hard-coded conda path in README.md:41. Smoke-test with
   `demo/run.sh` (20 ShareGPT sessions, ships in-repo) after pointing `--model` at a downloaded
   tokenizer dir. If the CUDA platform plugin misfires, patch
   `vllm/platforms/__init__.py:156` or install a cpu-tagged dist-info.
2. `bash models/download.sh` (or the equivalent `huggingface-cli download unsloth/Llama-3.2-1B-Instruct
   --exclude "*.safetensors"`).
3. Data prep: ShareGPT (`wget` → `clean_ShareGPT_V3.py` → `deduplicate.py`), AgentBank
   (`prepare_agentbank_data.py`, `Alfred_scale_up.py`), CodeParrot, MASH-QA, ToolBench; then
   `bash data.sh` in each directory (tokenization — the long pole, hours of CPU for ShareGPT).
   Keep the generated session-id prefixes intact: the task classifier keys on them
   (`prefix_caching_block.py:1019-1034`).
4. Fix `TaskData/Hybrid/test1/run.sh` (model path) and write a variant that loops over all eight
   policies; for OPT-Offline first run `--eviction-policy NONE` with `COLLECT_TRACE=1 PYTHONHASHSEED=0`
   to emit `use_map.json` (`OPT/readme.md`, `simulator.py:619-630`), then replay with
   `--eviction-policy OPT --opt-block-use-map-path ...`.
5. Write the missing aggregator: walk `result/Hybrid/test1/*/summary.json`, read
   `hit_rate_summary.global_hit_rate`, plot vs block budget.
6. Optional (Table 5): build the fork with `VLLM_USE_PRECOMPILED=1 pip install -e .`, run
   `run_gpu.py` with Llama-3.2-1B and a reduced block budget for 2–3 policies to check the QTTFT
   ordering on our A5000.

**Effort.** ≈ 5 person-days + ~30 CPU-core-hours for the simulator sweep (embarrassingly parallel
over the 16 cores; paper reports ~150 s per trace, budget an order of magnitude more for a 1 h trace
with 8200 sessions) + 0 GPU-hours for the target figure. Add ~2 person-days and ~8 GPU-hours if the
optional Table 5 check is attempted.

**Level: M.** The code for the exact result exists and runs without GPU, root, or gated data — that
argues for H. It is capped at M because (i) there is no script that produces Fig. 10 (aggregation
and plotting must be written), (ii) most `TaskData/Hybrid/test*/run.sh` scripts pass CLI flags that
`run_simulation.py` does not accept and will abort, (iii) the paper's budget axis (0.5A/0.7A/0.9A)
has no documented mapping to `--simulator-num-gpu-blocks`, so absolute numbers must be re-derived,
and (iv) five external datasets across HF / Google Drive / a personal OneDrive must be fetched and
tokenized before the first real run. None of these is a research risk; all are porting work.

## 5. Add-on ideas

### A1 — Kill the task-label oracle

**Hypothesis.** We hypothesize that replacing UniCache's oracle task labels with an online,
content-derived classifier (turn-index observation for session reuse + radix-prefix/template
signature clustering for structural reuse) retains most of UniCache's hit-ratio gain over LRU on
Traces #1–#3, and that the gain degrades gracefully (not catastrophically) as label error rises —
or, if it does not, that UniCache's reported advantage is partly an artifact of perfect labelling.

**Mechanism.** Today the task type is read off the session-id string
(`prefix_caching_block.py:1019-1034`: `"alfred_" → MULTI_TURN_AGENTIC`, `"apps_"/"mind2web_" →
SINGLE_TURN_RANDOM` i.e. straight into the evict-first queue), and the same hard-coded mapping
drives the per-queue hit accounting (`output_simulator.py:131-143`). Replace it with a
`TaskClassifier` that sees only what a real engine sees at admission: the prompt token ids, the
request's arrival time, and whether this request's prefix matched a block belonging to a live
session. Concretely: (a) a request whose longest prefix match lands inside a previously-seen
*session* chain is multi-turn, and the observed inter-arrival gap decides chat vs agentic; (b)
single-turn requests are bucketed by the hash of their first *k* blocks (the template signature),
and buckets whose observed reuse rate stays below a threshold are demoted to the evict-first queue,
which is exactly what `SINGLE_TURN_RANDOM` does by fiat today. Then run a controlled sweep that
injects label noise (p = 0 … 0.5) to get a sensitivity curve.

**Code locations.** `vllm/core/block/prefix_caching_block.py:1005`,
`vllm/simulator/output_simulator.py:94`, `vllm/core/evictor.py:1302`, `vllm/simulator/hybrid_utils.py`.

**Motivating evidence.** §6.6 ("Task type classification") asserts that "task categories can often be
inferred from lightweight signals ... such as request metadata" and points at a `type` field in the
Qwen traces — but no experiment in the paper uses an inferred label, and the artifact hard-codes the
ground truth into a string comparison. Implication 3 and the evict-first queue (which contains *all*
untemplated single-turn prefill blocks, §5.2) depend entirely on this label being correct, and
Table 1 already shows that a mis-targeted policy can be worse than LRU for a whole task class.

**Feasibility: H.** Fully inside the simulator, ~500–1000 LOC, no new harness: the existing
`tasks_config.yaml` traces and `summary.json` output are exactly the measurement needed, and label
noise is a one-line perturbation. Runs on CPU.

**Research value: H.** This is the load-bearing assumption of the design and the first thing a
SIGMETRICS reviewer would poke. Both outcomes are publishable: "UniCache survives realistic
labelling" makes the policy deployable, "it does not" reframes the paper's 17 % as an upper bound.

**Scoop check.** Queries: *"UniCache prefix cache eviction heterogeneous LLM serving follow-up"*,
*"KV cache prefix cache admission control policy never-reused blocks 2026"*,
*"per-tenant fairness prefix KV cache eviction 2026"*. Result: **partial**. The closest work is
[SAECache, arXiv 2605.18825](https://arxiv.org/abs/2605.18825) (May 2026), a concurrent preprint
with a near-identical multi-queue design that infers the multi-turn session type with a ~1 M-param
MLP over the model's last-layer hidden state — but it needs model internals (unavailable in the CPU
simulator), releases no code, and never compares against UniCache.
[PEEK, arXiv 2607.02525](https://arxiv.org/abs/2607.02525) builds prefix clusters from a radix tree
for admission/eviction, which overlaps with the template-signature half of the idea but not with the
label-sensitivity study.

---

### A2 — Latency-aware value instead of hit-token value

**Hypothesis.** We hypothesize that replacing UniCache's hit-token-per-capacity efficiency with a
*recompute-cost-per-capacity* value — cost estimated by the paper's own power-law prefill model, and
charged for the suffix blocks that an eviction silently strands — reduces mean and p90 QTTFT under
single-turn-dominant and long-prompt-heavy traffic (Trace #3 / MASH-QA-heavy mixes), at equal or
slightly lower hit ratio.

**Mechanism.** Two changes, both local. (1) In `update_alpha_balance`, replace `H_q` (a raw count of
hit tokens, `output_simulator.py:146`) with `Σ prefill_time(hit_tokens)` using the same
`a·BS^b·L^c` model the simulator already evaluates (`simulator.py:284`): a hit on 2000 tokens of a
MASH-QA document is worth super-linearly more wall-clock than 2000 tokens spread over 40 chat turns,
yet the current metric prices them identically. (2) In `calculate_priority`, charge an eviction for
the *dependent suffix*: because matching is a strict prefix walk (Fig. 8a), evicting an early block
makes every cached descendant unreachable, so a block's value should include the number of
still-resident descendants. The block manager already maintains the prefix trie
(`vllm/core/block/prefix_caching_block.py`), so a cheap descendant counter is available.

**Code locations.** `vllm/core/evictor.py:1702`, `vllm/core/evictor.py:1214`,
`vllm/core/block/prefix_caching_block.py`, `vllm/simulator/simulator.py:276`.

**Motivating evidence.** The paper optimizes hit ratio and only reports QTTFT once (Table 5, p. 19,
one model, one budget). The two do not move together: on Trace #3 UniCache gets 0.10 s vs ARC 0.12 s
— a 17 % QTTFT gap — while the hit-ratio gap over ARC is quoted as only 3.86 % on average, and
OPT-Offline reaches 0.08 s. §5.2's own tail-first ordering (Implication 5) is justified by exactly
the suffix-invalidation argument, but the *value* metric in §5.3 never accounts for it.

**Feasibility: H.** ~300–600 LOC in two functions plus a descendant counter; the existing virtual
clock already yields QTTFT in simulation, and the hit-ratio harness is unchanged. CPU only.

**Research value: M.** Cost/size-aware caching is a well-trodden idea (GDSF and friends), so a
reviewer would expect *some* win; the interesting, non-obvious part is whether the trie-dependency
term matters more than the cost term, and whether hit ratio and latency actually diverge enough to
change the ranking of policies.

**Scoop check.** Queries: *"cost-aware prefix cache eviction suffix invalidation trie LLM GDSF
size-aware KV block"*, *"hotness-aware KV cache scheduling prefix caching"*. Result: **partial**.
[CacheWise (arXiv 2606.16824)](https://arxiv.org/pdf/2606.16824) and
[Hotness-Aware KV Cache Scheduling (ACM 10.1145/3749168)](https://dl.acm.org/doi/pdf/10.1145/3749168)
use recompute-cost-weighted priorities, but neither does it inside a task-partitioned multi-queue
policy, and neither models the stranded-suffix term.

---

### A3 — Distribution shift vs the hard-coded reuse horizons

**Hypothesis.** We hypothesize that UniCache's advantage over LRU shrinks or inverts when the
deployed inter-turn interval distribution differs from the offline-fitted `(μ, σ)` baked into the
policy, and that an online estimator refitted from observed reuse intervals recovers most of the
loss without needing historical traces.

**Mechanism.** `TASK_CONFIG` (`evictor.py:1177-1183`) hard-codes `(4.77, 1.279)` for chat and
`(1.81, 1.092)` for agentic, while the workload generator samples turn gaps from whatever `mu`/`sigma`
the yaml specifies (`simulator.py:393-397`; `TaskData/Hybrid/test1/tasks_config.yaml` uses
`4.15/0.971` for ShareGPT — already a mismatch with the policy's 4.77/1.279). Step 1: sweep the
generator's `(μ, σ)` (and a bimodal / heavy-tailed variant) while holding the policy's constants
fixed, and plot the hit-ratio gap vs LRU as a function of the mismatch. Step 2: wire the policy to an
online estimator — `vllm/simulator/wa_helper.py` already collects per-task reuse intervals and refits
periodically (`collect_hit_interval`:69, `_fit_all`:36) for the WA baseline; swap its exponential fit
for a log-normal MLE and have `calculate_priority` query it instead of the constant. Step 3: an
estimator-free variant that ranks multi-turn blocks by the empirical survival function (a
rank-based hazard estimate) needs no parametric assumption at all.

**Code locations.** `vllm/core/evictor.py:1177`, `vllm/core/evictor.py:1214`,
`vllm/simulator/wa_helper.py`, `TaskData/Hybrid/test1/tasks_config.yaml`,
`vllm/simulator/simulator.py:369`.

**Motivating evidence.** §5.2 states the distribution "can be fitted using historical traces (e.g.,
data from prior days or from the same weekday in previous weeks)" — an explicit assumption of
stationarity that the evaluation never stresses; every trace in §6.1 is generated from the same
log-normal the policy assumes (modulo the 4.15/0.971 vs 4.77/1.279 discrepancy above). The paper's
own Fig. 6 shows chat and agentic horizons differ by ~30× in scale, so the policy is clearly
sensitive to getting them right.

**Feasibility: H.** Step 1 is a yaml sweep with the existing harness (near-zero code); step 2 reuses
an existing helper class; all CPU.

**Research value: M.** The sensitivity study is genuinely new and cheap, and a negative result would
be a legitimate "Contemporary paper" outcome; but the online-fitting fix is the obvious remedy and a
reviewer would expect it to work.

**Scoop check.** Queries: *"UniCache ... follow-up"*, *"online log-normal reuse interval estimation
prefix cache eviction"*. Result: **partial**.
[SAECache (arXiv 2605.18825)](https://arxiv.org/abs/2605.18825) already proposes online MLE of per-task
`(μ, σ)` plus adaptive position decay and queue weights, and reports that "fixed-parameter
alternatives can degrade by up to 2.7× under workload mismatch" — which is essentially step 2 and
part of step 1. It is an unrefereed preprint with no released code that does not cite or compare
against UniCache, so a measured, reproducible study *on the UniCache artifact* is still a
contribution, but the team should treat the adaptive-fitting half as largely anticipated and lead
with the shift-sensitivity characterization and the non-parametric variant.

---

### A4 — One structural queue is not enough

**Hypothesis.** We hypothesize that splitting UniCache's single structural-reuse queue into per-task
queues, and replacing the fixed offset normalizer with each task's measured prompt-length
distribution, improves hit ratio on single-turn-dominant traffic (Trace #3) by more than the Stage-2
weighting alone.

**Mechanism.** Implication 3 says "different single-turn tasks should be managed independently", but
the implementation puts *all* templated single-turn traffic — ToolBench, CodeParrot, MASH-QA — into
one `"single"` queue with one `alpha_single` (`evictor.py:1259-1286`, `_select_queue_name`:1318).
Worse, the positional score uses a global constant `max_offset = 2048`
(`evictor.py:1287` `self.max_num_first_offset`), not "the maximum offset among all blocks" as §5.2
defines it — so for MASH-QA, whose documents routinely exceed 2048 tokens, `offset_factor` saturates
at 0 and the ordering inside the queue degenerates. Add one queue per single-turn task (reusing the
`alpha_q` machinery, which is already dict-keyed) and normalize the offset by a running quantile of
that task's prompt length; optionally replace the linear `1 − offset/max_offset` with the empirically
measured reuse-vs-depth curve (the machinery to measure it exists: `--enable-block-hit-track` and
`block_id_2_count` in `output_simulator.py`).

**Code locations.** `vllm/core/evictor.py:1254`, `vllm/core/evictor.py:1236`,
`vllm/core/evictor.py:1302`, `vllm/simulator/output_simulator.py:56`.

**Motivating evidence.** Fig. 7a (p. 10) shows single-turn reuse ratios ranging from 0.21 % (untemplated)
to 61.13 % (document QA) — a 300× spread the current design collapses into one queue and one weight —
and Table 3 shows the four task templates have completely different structures. The hard-coded 2048
normalizer is a plain implementation/paper mismatch.

**Feasibility: H.** Contained in `SimpleHYBRIDEvictor`, a few hundred LOC, evaluated with the
existing Trace #2/#3 configs on CPU.

**Research value: M.** It tests the paper's own Implication 3 and repairs a real artifact/paper
discrepancy, which is worth reporting, but "more queues help when tasks differ" is close to what the
paper already argues; the surprising outcome would be finding that it *doesn't* help, i.e. that
Stage 2 already absorbs the difference.

**Scoop check.** Queries: *"per-task queues single-turn structural prefix reuse eviction"*,
*"position-aware prefix cache eviction offset decay"*. Result: **partial**. SAECache learns a
position-decay exponent and a per-token-type weight, which subsumes the positional half; no work
found that separates the structural queue per task or reports the saturation bug.

---

### A5 — Demote instead of drop: task-aware GPU→CPU tiering

**Hypothesis.** We hypothesize that spilling UniCache's evicted blocks into a CPU-DRAM second tier,
with the demotion decision driven by the same per-queue hit efficiency, reduces QTTFT relative to
dropping them outright on multi-turn-dominant traffic, and that the benefit inverts once PCIe
transfer time exceeds the recompute time for short prefixes.

**Mechanism.** The evictor currently discards a block (`evictor.py:1429` returns the victim to the
free pool). Add a CPU tier of `--simulator-num-cpu-blocks` capacity (the flag already exists,
`run_simulation.py:53`) holding evicted blocks; on a prefix match that lands in the CPU tier, charge
the virtual clock a modelled PCIe transfer (`bytes / bandwidth`, calibrated on this machine) instead
of a full prefill, and run a second-level eviction there. Use `α_q` to decide *which* queues are
worth spilling — chat blocks with a 372 s P80 reuse horizon are worth CPU space, agentic blocks with
a 12 s horizon may be better recomputed.

**Code locations.** `vllm/core/evictor.py:1429`, `vllm/core/block/cpu_gpu_block_allocator.py`,
`vllm/simulator/output_simulator.py:87`, `vllm/simulator/simulator.py:266`, `vllm/simulator/config.py:113`.

**Motivating evidence.** §7 notes CachedAttention and Pensieve add hierarchical tiers but says nothing
about which *policy* should govern demotion; the artifact already accounts for an LMCache CPU tier in
its summary output (`simulator.py:482-486`, `output_simulator.py:87`) but the simulator path never
exercises it. Fig. 10's hit ratios saturate at large budgets, so the interesting regime — where a
second tier pays — is exactly the small-budget end where UniCache's margin is largest.

**Feasibility: M.** Cross-cutting: it touches the allocator, the evictor and the timing model, and the
transfer-time model must be calibrated (which does need a few GPU-hours on the A5000 to measure real
H2D bandwidth for KV blocks). Still comfortably inside a 10-week budget for 2–4 students.

**Research value: M.** Tiered KV caching is a crowded area, so the placement mechanism itself is not
novel; the novelty is making the *eviction-policy* signal drive demotion and characterizing the
crossover point where recompute beats transfer.

**Scoop check.** Queries: *"task-aware tiered KV cache demotion GPU to CPU prefix cache eviction
policy 2026"*, *"predictive multi-tier memory management KV cache"*. Result: **partial**.
[Predictive Multi-Tier Memory Management for KV Cache (arXiv 2604.26968)](https://arxiv.org/html/2604.26968v2)
and llm-d's tiered prefix cache do promotion/demotion by predicted access probability; CachedAttention
(ATC'24) and Mooncake (FAST'25) do the storage side. None couples the demotion decision to a
task-partitioned hit-efficiency weight, and none is evaluated against UniCache.

## 6. Risks and open questions

- **The label oracle is load-bearing.** `prefix_caching_block.py:1019-1034` decides the queue (and
  hence whether a block goes straight to evict-first) from a session-id string prefix. Any
  re-generated dataset whose ids do not start with `ShareGPT-multi-turn` / `alfred_` / `apps_` /
  `mind2web_` will silently reclassify everything as `SINGLE_TURN` and produce wrong numbers with no
  error. This is both the largest reproduction hazard and the best add-on (A1).
- **Broken run scripts.** `TaskData/Hybrid/test{2..9}/run.sh` and `test1/run_opt.sh` pass `--tag` and
  `--enable-hybrid-opt`, absent from `run_simulation.py`'s parser — every one of them aborts as
  shipped. Only `test1/run.sh` matches the current CLI.
- **No figure pipeline.** Nothing in the repo turns the per-run `summary.json` files into Fig. 10 /
  Fig. 11 / Table 5, and the paper's 0.5A/0.7A/0.9A budget axis has no documented mapping to
  `--simulator-num-gpu-blocks`. Absolute hit ratios will not be directly comparable without
  re-deriving it; the policy *ordering* should be.
- **Platform detection on a GPU host.** `vllm/platforms/__init__.py:50-75` will select the CUDA
  platform on this machine even for a CPU-only run, and the demo scripts rely on a `VLLM_PLATFORM`
  env var that this vLLM version does not read (`vllm/envs.py:146`). Unverified whether the CPU
  simulator starts cleanly as a result — this is a desk review, nothing was executed.
- **`tracked_hit_stats` grows without bound.** `output_simulator.py:146` appends one entry per
  request forever and `update_alpha_balance` sums the whole list every 10 requests
  (`evictor.py:1723`); the "recent window" of §5.3 is implemented only as a 0.95 decay applied to the
  *other* queues. On a long trace this is both an O(N²) cost and a semantic drift from Algorithm 2 —
  worth checking before attributing any measured overhead to the design.
- **Policy/generator parameter mismatch.** The policy assumes chat `(μ,σ) = (4.77, 1.279)`
  (`evictor.py:1178`) while the shipped trace configs generate ShareGPT turns with `(4.15, 0.971)`
  (`TaskData/Hybrid/test1/tasks_config.yaml:56`, matching §6.1). Whether the paper's numbers were
  produced with this mismatch is unclear from the repo; A3 turns it into a deliberate experiment.
- **ToolBench data provenance.** The only pointer is a personal OneDrive share
  (`TaskData/ToolBench/readme.md:1`). If it rots, the task must be substituted (StableToolBench on
  HF) or dropped, which changes the trace composition.
- **GPU-side results need a source build.** `run_gpu.py` executes the real model, so the fork must be
  compiled (`VLLM_USE_PRECOMPILED=1` is the cheap route). `demo/run_gpu.sh:1` hard-codes
  `CUDA_VISIBLE_DEVICES=1`, and the `--enable-lmcache` path in `run_gpu.py:239-258` calls
  `run_simulation` twice with an unbound `llm` — avoid it.
- **Artifact evaluation.** No artifact badge, AE appendix, or "Results Reproduced" evidence was found
  for this POMACS article; treat all feasibility claims above as desk predictions.
- **Concurrent work.** [SAECache (arXiv 2605.18825)](https://arxiv.org/abs/2605.18825) is a
  May-2026 preprint with a strikingly similar multi-queue + hit-efficiency design plus online
  parameter adaptation. It does not cite UniCache and has no code, but it narrows the novelty of any
  add-on that is purely "make UniCache's constants adaptive" (A3).

## 7. Evidence index

**Paper.** §1 Introduction (Fig. 1, Table 1, p. 2); §2.3 motivation (p. 5); §3.1–3.3 simulator
architecture, timing model, fidelity (Fig. 2, Fig. 3 p. 7, Fig. 4 p. 8); §4.1 Observations 1–2
(Fig. 5 p. 8, Fig. 6 p. 10); §4.2 Observations 3–5 (Table 3, Fig. 7 p. 10, Fig. 8 p. 12); §4.3
OPT-Offline (p. 11); §5.1–5.3 design (Fig. 9 p. 13, Alg. 1 & Alg. 2 p. 14); §6.1 setup, baselines,
trace construction (p. 15–16); §6.2 Fig. 10 (p. 18); §6.3 Table 4 + Fig. 11 (p. 19); §6.4 Table 5
(p. 19); §6.5 ablation Fig. 12, block-size Fig. 13 (p. 20–21); §6.6 discussion — model size,
distributed inference, task classification (p. 21); §7 related work (p. 21–22); Appendix A.1 Fig. 14,
A.2 prompt templates, A.3 Alg. 3 (p. 25–27). Rendered pages read: `pages/page-18.png`,
`pages/page-19.png`.

**Repo.** `README.md`; `run_simulation.py`; `run_gpu.py`; `prepare_session_data.py`;
`models/download.sh`; `demo/run.sh`, `demo/run_gpu.sh`, `demo/tasks_config.yaml`,
`demo/ShareGPT_cleaned_valid_session_data_head20.jsonl`; `vllm/core/evictor.py`;
`vllm/core/block_manager.py`; `vllm/core/block/prefix_caching_block.py`; `vllm/core/scheduler.py`;
`vllm/engine/llm_engine.py`; `vllm/_custom_ops.py`; `vllm/platforms/__init__.py`; `vllm/envs.py`;
`vllm/simulator/simulator.py`, `config.py`, `output_simulator.py`, `wa_helper.py`, `hybrid_utils.py`,
`data_parser.py`, `opt_utils.py`; `requirements/common.txt`, `requirements/cpu.txt`;
`TaskData/readme.md`, `TaskData/Hybrid/test1/{run.sh,run_opt.sh,tasks_config.yaml}`,
`TaskData/Hybrid/test2/run.sh`, `TaskData/SharedGPT-multi-turn/{readme.md,data.sh}`,
`TaskData/AgentBankData/{readme.md,prepare_agentbank_data.py,Alfred_scale_up.py,data.sh}`,
`TaskData/Codeparrot/{readme.md,prepare_data.py,data.sh}`, `TaskData/mashqa_data/{readme.md,prepare_data.py,data.sh}`,
`TaskData/ToolBench/{readme.md,data.sh}`, `OPT/readme.md`; `repo_facts.json`; `fetch_result.json`.

**External (scoop check).** SAECache — https://arxiv.org/abs/2605.18825 ;
PEEK — https://arxiv.org/abs/2607.02525 ; PrefixShield — https://arxiv.org/html/2608.01657v1 ;
CacheWise — https://arxiv.org/pdf/2606.16824 ; Hotness-Aware KV Cache Scheduling —
https://dl.acm.org/doi/pdf/10.1145/3749168 ; Predictive Multi-Tier Memory Management for KV Cache —
https://arxiv.org/html/2604.26968v2 ; SIGMETRICS'26 abstract page — https://doi.org/10.1145/3801489.3806861 .
