# Prompt Cache: Modular Attention Reuse for Low-Latency Inference

*Desk review only. Nothing was built, installed, or executed. Every claim below is traced to a
paper section/figure or a repository path. The `pages/` directory of rendered page images was not
present in the input tree (checked with a glob), so figure *content* (bar heights, curve shapes)
is taken from the prose that describes each figure, and I flag where that limits confidence.*

---

## 1. Paper summary

**Problem.** Prefill (time-to-first-token, TTFT) dominates latency for long prompts because
self-attention over the prompt is quadratic in prompt length (§2.2, §5.4). The standard KV Cache
removes redundant computation *within* one request but not *across* requests. Existing cross-request
reuse is limited to identical **prefixes** (paged attention prefix sharing, §2.2).

**Key idea.** Precompute and store the key/value attention states of frequently-reused *text
segments* ("prompt modules") so that any prompt that imports them skips their prefill (§1, Fig. 1c).
Two obstacles are attacked together (§3.1):

1. *Position dependence* — solved by a **Prompt Markup Language (PML)** schema that assigns each
   module a fixed, absolute range of position IDs derived from its location in the schema (§3.2,
   §3.3).
2. *Segment recognition* — solved by making reuse explicit: a prompt declares `schema="..."` and
   imports modules by tag (§3.2.1).

The enabling empirical claim is that LLMs tolerate **discontinuous position IDs** as long as
relative order is preserved (§3.1), so a prompt can import an arbitrary subset of modules and leave
position-ID gaps where modules were omitted.

**Design.** PML adds: parameters (`<parameter name len>` — `<unk>`-padded placeholder slots whose
position IDs are later reused by the supplied argument, §3.2.2/§3.3); unions (`<union>` — mutually
exclusive modules sharing a start position, §3.2.3); nested modules; and chat-template tags
(`<system>/<user>/<assistant>`). §3.4 ("Cached inference") concatenates the cached module KV
tensors, computes KV only for arguments and trailing user text, and hands the concatenation to the
model as a `past_key_values`. §3.3 states the approximation explicitly: attention is confined to the
span of each prompt module, analogous to local masked attention, and offers **"scaffolding"** — sets
of modules encoded *together* so they share an attention span, "at the cost of additional memory" —
as the escape hatch for semantically dependent modules.

**Implementation.** ~3K lines of Python on HuggingFace `transformers` (§4). Prompt modules live in
CPU DRAM or GPU HBM (§4.1). ~20 lines per architecture are needed to support discontinuous position
IDs: RoPE and ALiBi become position-ID-indexed lookups (§4.2). A buffered concat operator avoids
reallocation (§4.2).

**Evaluation setup (§5.1).** CPUs: i9-13900K (DDR5-5600) and Ryzen 9 7950X (DDR4-3600). GPUs: RTX
4090, A40, A100 — "LLMs that fit within the memory capacity of a single GPU (40 GB)". Models:
Llama2 7B/13B, CodeLlama 7B, MPT 7B, Falcon 7B. Workload: **LongBench** (4K–10K contexts, 21
datasets); each LongBench document becomes one prompt module, task directives stay uncached.
Baseline: ordinary KV Cache through the *same* inference pipeline.

**Headline numbers.**
- Fig. 3 (GPU TTFT, Llama2-7B, 8 LongBench datasets × 3 GPUs): **1.5–3× with modules in CPU memory,
  5–10× with modules in GPU memory** (§5.2.1). The abstract rounds this to "8× for GPU".
- Fig. 4 (CPU TTFT): up to **70×** (Intel) / **20×** (AMD) (§5.2.2).
- Table 1 (accuracy, LongBench, greedy decoding, 4 models): scores "comparable to the baseline",
  with the paper itself bolding outliers. Notable regressions: Passage Retrieval Llama2-7B
  7.50 → 4.25 and 13B 9.08 → 6.50; 2WikiMQA 7B 16.63 → 13.95. Notable *gains*: 2WikiMQA MPT-7B
  10.44 → 13.70, MuSiQue 13B 10.03 → 12.14.
- Fig. 5: the "cache advantage" — recompute cost grows quadratically while memcpy grows linearly;
  at 5K tokens, host→host 3.79 ms, host→device 5.34 ms, device→device 0.23 ms (§5.4).
- Table 2: memory per cached token — 0.5 MB/token for Llama-7B, 0.78 for 13B, 2.5 for 70B.
- §5.4 end-to-end: RTX 4090 / Llama-7B / 3K context, TTFT 900 ms → 90 ms, TPOT unchanged at ~32 ms.

**Stated limitations / future work (§4.1, §5.5, §6).** No cache replacement or prefetching policy
across the CPU/GPU tiers ("We leave the development of a system that incorporates cache replacement
and prefetching strategies to future research"); no KV compression or GQA exploitation; no GPU
primitive for sharing module states across concurrent requests (batching benefit is argued only
qualitatively in §3.4 and §5.4); RAG integration is speculative.

---

## 2. Artifact audit

### 2.1 Provenance and shape

- Repo: `https://github.com/yale-sys/prompt-cache`, head commit `9027040`, dated **2024-11-09**
  (`repo_facts.json`). 77 files, 0.5 MB, 8,902 lines of Python.
- Officiality is decisive: paper §1 (end) states *"Our source code and data used for evaluation are
  available at github.com/yale-sys/prompt-cache"*, and `repo/README.md:3` links back to the arXiv
  version and `repo/README.md:241-246` carries the paper's BibTeX. Org `yale-sys` matches the
  authors' affiliation (Yale CS).
- Licence present (`repo/LICENSE`). No Dockerfile anywhere — pure `pip install -r requirements.txt`.
- Submodules are declared but not fetched in this clone (`repo/.gitmodules`:
  `dependency/LongBench`, `dependency/bleurt`); `repo/dependency/` is empty here.

### 2.2 Paper component → code map

| Paper | Code |
|---|---|
| PML schema/prompt parsing, modules, unions, parameters, nesting (§3.2) | `promptcache/schema.py` (`Module` 262-435, `UnionModule` 185-259, `Parameter` 100-153, `Schema` 527-533), `promptcache/prompt.py` |
| Position-ID assignment; union children share a start offset; parameter slots reserve `len` position IDs (§3.3) | `promptcache/schema.py:132` (`Parameter._position_ids`), `:170` (`TokenSequence._position_ids`), `:210` + `:225` (union offset/length = max child) |
| Scaffold = the concrete module selection used for encoding (§3.3) | `promptcache/schema.py:439-523` (`Scaffold`) |
| Prompt module encoding (§3.3) | `promptcache/cache_engine.py:185-307` (`SchemaCache._process`) |
| Cached inference: concatenate module KV + compute the rest (§3.4) | `promptcache/cache_engine.py:388-522` (`CacheEngine.process`), `promptcache/cache_engine.py:115-156` (`PromptCache.update`) |
| CPU/GPU placement of modules (§4.1) | `promptcache/cache_engine.py:50-83` (`TokenSequenceCache.host_cache/device_cache/upload/free`), `:290-292` |
| Discontinuous position IDs for RoPE / ALiBi (§4.2) | vendored models: `promptcache/model/llama2.py:202-210` (`apply_rotary_pos_emb` indexes `cos/sin` by `position_ids`), `:357` (`seq_len=torch.max(position_ids)+1`), `promptcache/model/falcon.py`, `promptcache/model/mpt.py` |
| Compression hooks (future work, §6) | `promptcache/model/__init__.py:116-126` — `store_k_hook/store_v_hook/read_k_hook/read_v_hook`, all identity, wired in at `cache_engine.py:284-285` and `:513` |
| Generation loop / TTFT measurement | `promptcache/generation_engine.py:91-147` |
| Fig. 3/4 TTFT harness | `eval_sys.py:300-378` (`run_latency_eval`) |
| Fig. 5 crossover (memcpy vs recompute) | `eval_sys.py:88-215` (`run_critical_point`), `benchmark_memcpy.py` |
| Table 1 accuracy | `eval.py:221-280` (`Eval.run`) writes JSON; `get_scores.py` scores it with `metrics.py` |
| LongBench → schema/prompt conversion | `benchmark/longbench.py:85-135` (writes one `schema_<id>.xml` per sample under `benchmark/schema/<dataset>/`) |
| §5.6 application case studies | `examples/code_generation_game.xml`, `examples/personalization-education.xml`, `examples/parameterized_prompts.xml`, driven by `demo.py` |

### 2.3 Three implementation facts that the paper's text does not prepare you for

These matter for both reproduction and for the add-ons, so I give the exact lines.

**(a) Modules are *not* encoded in isolation — a whole scaffold is encoded in one forward pass and
then sliced.** `SchemaCache._process` builds `scaffold = self.schema.get_scaffold(path)`
(`cache_engine.py:221`), takes `scaffold.token_ids()` / `scaffold.position_ids()` for the **entire
schema** under that selection (`:223-224`), runs a single `self.lm(...)` (`:243-248`), and then
slices per-`TokenSequence` KV out of the result (`:261-296`). So within one scaffold, every module
attends to all modules preceding it. §3.3's statement that "Prompt Cache confines attention score
computation to the span of each prompt module" is therefore *not* what the code does: the real
approximation is "each module's KV was computed conditioned on the scaffold's default selection,
which may differ from what the prompt actually imports". The only mechanism that generates extra
scaffolds is a `<union>` (`cache_engine.py:192-210` enumerates non-default union branches). This
substantially changes how one should read Table 1, and it is the basis of add-on A1.

**(b) The "scaffolding" feature of §3.3 is declared but not implemented.** `SchemaCache.cache_l2`
is typed (`cache_engine.py:171`), initialised (`:179`), and read (`get_cache_l2`, `:316-322`), but
**nothing ever writes to it** (verified by grepping `cache_l2` across the repo — 4 hits, all of the
above). There is no `<scaffold>` tag in `schema.py`; the `scaffold=` attribute on `<union>` and
`<parameter>` is a different thing (a *placeholder*, `schema.py:134-141`, `:214-219`). So the
paper's stated remedy for cross-module dependence does not exist in the artifact.

**(c) The "prompt modules in GPU memory" configuration — the headline 5–10× / 8× — is not exposed as
a flag.** `cache_engine.py:290-292` moves every encoded module to host memory whenever
`self.target_device != 'cpu'`; `CacheEngine.process` then stages the used modules into a
GPU-resident ring buffer per request (`PromptCache.update`, `:115-156`), i.e. a host→device copy on
every request. `TokenSequenceCache.upload()`/`.free()` (`:65-73`), the obvious hooks for keeping a
module resident in HBM, are **never called** anywhere in the repo. Reproducing the blue bars of
Fig. 3 requires a (small) edit at `cache_engine.py:290`.

### 2.4 Build route on *this* machine

No root needed; no Docker to port. The route is:

1. `conda create -n pc python=3.10` — **not 3.12**. `requirements.txt:13` pins
   `transformers==4.34.0` (Oct 2023), whose `tokenizers` dependency has no cp312 wheels; the code
   also uses `match` statements (`eval.py:87`, `schema.py:334`) so ≥3.10 is required.
2. `pip install -r requirements.txt` — `torch==2.3.0` (cu121 wheel) runs on driver 535 via CUDA
   minor-version compatibility; the system `nvcc` 11.8 is irrelevant since nothing is compiled.
3. **Undeclared dependencies**: every eval path passes `load_in_8bit=True`
   (`eval.py:36`, `eval_sys.py:37`, `eval_acc.py:79`, `demo.py:28`), which needs `bitsandbytes` and
   `accelerate`; neither is in `requirements.txt`. `sentencepiece`/`protobuf` are needed by
   `LlamaTokenizer` (`promptcache/model/__init__.py:188`).
4. `bleurt` (README lines 15-20) can be **skipped**: it is imported only by `benchmark/metrics.py:3`,
   which is not imported by `eval.py`, `eval_acc.py`, or `get_scores.py` (they use the top-level
   `metrics.py`, which needs only `rouge`, `jieba`, `fuzzywuzzy`). This avoids dragging in TensorFlow.
5. FlashAttention-2 is optional — `LlamaFlashAttention2` is only selected if
   `config._flash_attn_2_enabled` (`promptcache/model/llama2.py:591-595`), and the eager path is the
   default. (Its `flash_attn_func` import is in fact missing from the file, so the FA2 path would
   `NameError` if enabled — leave it off.)

**Dependency age:** the pins are ~2 years old as of 2026-09. They are still installable, and because
the repo *vendors* its own `LlamaForCausalLM`/`FalconForCausalLM`/`MptForCausalLM` copied from
transformers 4.34, upgrading `transformers` is not an option — `promptcache/model/llama2.py:34`
imports `transformers.pytorch_utils.ALL_LAYERNORM_LAYERS` and `:593` keys off
`config._flash_attn_2_enabled`, both of which were removed in later transformers. Pinning is the
correct strategy here, not upgrading.

### 2.5 Data, traces, weights

- **Datasets**: `benchmark/longbench.py:90` does `load_dataset('THUDM/LongBench', subset)` — public,
  non-gated on HF. `benchmark/squad_v2.py`, `benchmark/multi_news.py`, `benchmark/ms_marco_v1_1.py`
  likewise use public HF datasets. Schemas are *generated* at runtime into
  `benchmark/schema/<dataset>/` (`benchmark_base.py:49-51`, `longbench.py:124-126`), so no schema
  corpus needs shipping. Total download is small (LongBench is ~hundreds of MB).
- **Weights**: `config/llm_config_llama2_7b.json` names `meta-llama/Llama-2-7b-chat-hf`, which is
  **gated** on HF (licence click-through). Ungated alternatives are already configured in the repo:
  `config/llm_config_falcon_7b.json` (`tiiuae/falcon-7b-instruct`) and `config/llm_config_mpt_7b.json`
  (`mosaicml/mpt-7b-chat-8k`), and `config/llm_config_vicuna_7b.json`. Both Falcon-7B and MPT-7B
  appear in Table 1, so a Llama-free reproduction is still a paper-comparable reproduction.
- **No proprietary traces anywhere.**

### 2.6 Eval scripts: present, absent, and broken

Present: `eval.py` (accuracy + per-entry latency), `eval_sys.py` (Fig. 3/4/5 harness),
`eval_acc.py` (quick accuracy), `get_scores.py` (Table 1 scoring), `benchmark_memcpy.py`,
`scripts/run_benchmarks.py` (sweep driver), five `.slurm` files for NCSA Delta.

Gaps and rough edges found by reading:

- `eval_sys.py:428-437`: `main()` calls `eval.run_critical_point22()`; the two
  `eval.run_latency_eval(...)` calls that produce Fig. 3/4 are **commented out**. One-line fix, but
  you have to notice it.
- `eval_sys.py:286`: `run_critical_point22` writes into `./benchmark/aaa`, a directory that does not
  exist in the repo; `run_critical_point` writes into `benchmark/results_latency`, also absent
  (`os.makedirs` is only called in `run_latency_eval`, `:313`). Expect a `FileNotFoundError`.
- `eval_sys.py:91-104`: the synthetic cache shape in `run_critical_point` is **hard-coded to Llama2
  13B** (`num_layers=40, num_heads=40`) with the 7B values commented out — so Fig. 5's memcpy curve
  does not follow `--llm_config_path`.
- `get_scores.py:73` reads `./results_13b/{model}-{dset}/`, while `eval.py:155-156` writes to
  `./benchmark/results/{model}-{dataset}/`. Path mismatch; trivially fixed.
- `eval_acc.py:105` hard-codes `dataset.init(limit_entries=3)` — three samples per dataset. This is
  a smoke test, not Table 1. Table 1 must be reproduced via `eval.py run()` + `get_scores.py`, which
  do iterate the full split.
- **No plotting scripts.** `benchmark/results/README.md` is a one-line stub
  ("Benchmark results will be stored here."). Figures must be redrawn from the JSON.
- `Makefile:4` defaults `LLM_CONFIG_PATH` to `./config/llm_config_llama2.json`, a file that does not
  exist (the real ones are `llm_config_llama2_7b.json` / `_13b.json`). Same stale name in
  `scripts/benchmark_setup.json:3`.
- Debug `print()`s left in the hot path (`cache_engine.py:18-33`, `eval.py:178`, `:239`,
  `generation_engine.py:118`).
- `scripts/benchmark_setup.json:25-34` documents datasets the authors **skipped**: `lcc`,
  `repobench-p`, `samsum` ("code syntax interferes with xml syntax of prompt cache") and `lsht`,
  `vcsum`, `dureader` ("out of memory"). This is a real, undiscussed limitation of the PML approach
  and useful context for scoping a reproduction.

### 2.7 Red flags from `repo_facts.json`

One hit, `multi_node`, at `g.sh:1` — an `srun` convenience wrapper. It is
`--nodes=1 --ntasks=1`, i.e. single node, and every `.slurm` file requests
`--gpus-per-node=1` (e.g. `eval_sys_a40-7b-gpu.slurm:14`). Not a multi-node artifact; the SLURM
files are simply how the authors reached NCSA Delta and are irrelevant here.

---

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper §1 (p.2): "Our source code and data used for evaluation are available at github.com/yale-sys/prompt-cache". `repo/README.md:3` links the paper; `README.md:241-246` gives its BibTeX. The repo contains the actual system, not a stub: `promptcache/cache_engine.py` (523 lines) implements §3.3/§3.4, `promptcache/schema.py` (534 lines) implements §3.2, and `promptcache/model/{llama2,falcon,mpt}.py` are the §4.2 position-ID-aware architectures. |
| `H2_no_root` | **pass** | Pure Python/PyTorch. No Dockerfile in `repo_facts.json["top_level"]`, no kernel/eBPF/`perf`/KVM/hugepage usage anywhere. Timing uses `torch.cuda.Event` (`generation_engine.py:104-114`, `eval_sys.py:338-351`) and `torch.profiler` (`eval_sys.py:413`), which are CUPTI-based and do not need `perf_event_paranoid` relaxation. The `.slurm`/`g.sh` files are optional cluster wrappers. |
| `H3_hardware_fit` | **pass** | The headline configuration is Llama2-7B on **one** GPU (paper §5.1: "LLMs that fit within the memory capacity of a single GPU"; `eval_sys_a40-7b-gpu.slurm:14`: `--gpus-per-node=1`), loaded 8-bit (`config/llm_config_llama2_7b.json:5`) with `max_ctx_length` 4096 — comfortably inside 24 GB on the A5000 (Ampere SM 8.6, same generation as the paper's A40). Module storage is host DRAM (`cache_engine.py:290-292`); Table 2 gives 0.5 MB/token for a 7B model, so a 3.5K-token module is ~1.75 GB — fine in 125 GB. Concern to note, not a fail: `config/llm_config_falcon_40b.json` and `llm_config_mpt_30b.json` (used for Table 1's 30B/40B rows via `scripts/benchmark_setup.json:35-48`) will **not** fit 24 GB even in 8-bit; those rows are out of reach. Fig. 4's CPU numbers are reproducible in kind but not in magnitude (16-core Zen 3 ≠ i9-13900K). |
| `H4_obtainable_deps_data` | **pass** | Deps are pip-installable in user space (`requirements.txt`); `bitsandbytes`/`accelerate` are undeclared but pip-installable; `bleurt`/TensorFlow is avoidable (§2.4). Data is `THUDM/LongBench` from HF, public and non-gated (`benchmark/longbench.py:90`); schemas are generated at runtime. Weights: `meta-llama/Llama-2-7b-chat-hf` is gated, but the repo itself names ungated substitutes that the paper also evaluates — `tiiuae/falcon-7b-instruct` (`config/llm_config_falcon_7b.json`) and `mosaicml/mpt-7b-chat-8k` (`config/llm_config_mpt_7b.json`), both columns of Table 1. No proprietary traces. |

No `fail`, no `unclear`.

---

## 4. Reproduction plan

**Target.** **Figure 3**, Llama2-7B (or Falcon-7B), the *yellow* bars: TTFT of Prompt Cache with
prompt modules in **CPU memory** versus the KV-Cache baseline, across LongBench datasets, on one
Ampere GPU. Claim supported: §5.2.1's "1.5× to 3× when using CPU memory". Stretch target within the
same run: the *blue* bars (modules resident in GPU memory, 5–10×, i.e. the abstract's 8×) after the
one-line change at `cache_engine.py:290`.

Why this target and not Table 1: Fig. 3 is a prefill-only measurement (`eval_sys.py:345-351` calls
the model once and stops), so it costs minutes of GPU time, whereas Table 1 requires full
autoregressive generation over whole LongBench splits for both arms.

**Scale-down.**
- One GPU (RTX A5000 24 GB) instead of three; report it as an Ampere data point alongside the
  paper's A40. Drop the A100/4090 columns.
- Llama2-7B-chat 8-bit (already the repo default). If the HF gate is an obstacle, use
  `config/llm_config_falcon_7b.json` — Falcon-7B is a Table 1 model and is ungated.
- `max_tokens=3500`, `max_ctx_length=4096` unchanged (`config/llm_config_llama2_7b.json:7-8`).
- Keep `eval_sys.py`'s built-in subsampling: `dataset.init(limit_entries=5)` and 3 repeats
  (`eval_sys.py:305`, `:318`, `:29`). 13 datasets × 5 entries × 3 reps × {cache, no-cache}.
- Skip the 13B/30B/40B rows entirely (H3 note above).
- Fig. 4 (CPU inference) optional: `--use_cpu_for_inference=True` on 2–3 datasets only; §5.6
  reports ~76 s per uncached prompt on an i9, so a full sweep is hours of wall clock for little
  extra signal.

**Steps.**
1. `conda create -n pc python=3.10`; `pip install -r requirements.txt` plus
   `bitsandbytes accelerate sentencepiece protobuf`.
2. `huggingface-cli download` the chosen 7B checkpoint and `THUDM/LongBench`
   (`benchmark/longbench.py:90` will do it on first run).
3. `mkdir -p benchmark/results_latency` (the script only creates it inside `run_latency_eval`,
   `eval_sys.py:313`, but `run_critical_point*` does not).
4. Edit `eval_sys.py:432-437`: uncomment `eval.run_latency_eval(False)` and
   `eval.run_latency_eval(True)`; comment out `eval.run_critical_point22()`.
5. Run `python eval_sys.py --memo=a5000 --llm_config_path=./config/llm_config_llama2_7b.json
   --use_cpu_for_inference=False`. Output: one JSON per dataset per arm under
   `benchmark/results_latency/`, with `cache_time` (staging memcpy) and `response_time` (prefill).
6. Write a ~50-line plotting script (none exists) that bars `cache_time + response_time` for the
   cached arm against `response_time` for the baseline arm — note that the correct TTFT for Prompt
   Cache is the **sum**, since `cache_time` is measured separately at `cache_engine.py:391-509`.
   Getting this wrong would inflate the speedup; verify the paper's ratio is reproduced with the sum.
7. Stretch: delete/guard the `.cpu()` at `cache_engine.py:290-292` so modules stay in HBM, re-run,
   and compare against the blue bars.
8. Sanity anchor before any of this: `python demo.py` / `python demo.py --enable_cache=False`, which
   README lines 85-104 annotate with expected TTFTs (286.9 ms → 78.2 ms on a 4090).

**Effort.** ~3–4 person-days (env + gated-model workaround + the four script fixes in §2.6 + a
plotting script) and ~5 GPU-hours including weight downloads and smoke tests. Adding the CPU-inference
arm costs another ~1 person-day and ~6 CPU-hours. Reproducing Table 1 at full LongBench scale would
be a further ~30–60 GPU-hours and should not be attempted in week 2.

**Level: M.** Not H, because four separate edits are needed before the headline figure can be
produced at all (commented-out entry point, missing output dirs, undeclared `bitsandbytes`, gated
weights), the *headline* GPU-resident variant is not reachable by configuration, there are no
plotting scripts, and the pins are two years old. Not L, because the harness, the datasets, the
schema generation, the baseline arm, and the metric are all present and directly correspond to
Fig. 3; the model fits the GPU at paper scale; and nothing about the mechanism needs hardware we
lack. No artifact badge was found for this paper (MLSys 2024 ran a voluntary AE process, but the
proceedings entry and the PDF show no badge), so "Results Reproduced" evidence does not exist to
raise confidence.

---

## 5. Add-on ideas

### A1 — Budgeted co-encoding ("scaffold groups"): pay memory, not compute, to repair cross-module attention

> **Hypothesis.** We hypothesize that precomputing co-encoded KV for a small, *selected* set of
> prompt-module groups (the paper's unimplemented "scaffolding") recovers most of the accuracy lost
> to modular encoding — measured as LongBench F1/accuracy gap versus full prefill — at a bounded
> cache-memory overhead, on multi-module prompts (multi-document QA and passage retrieval), where
> Prompt Cache's Table 1 already shows its largest regressions.

- **Mechanism.** (i) First build an honest *independent-encoding* mode: encode each module in its
  own forward pass instead of slicing it out of a whole-scaffold pass, so the §3.3 approximation is
  actually the one being measured. This separates "Prompt Cache is accurate" from "Prompt Cache's
  modules happened to be co-encoded" (see §2.3(a)) and gives the true upper bound on the damage.
  (ii) Then populate `cache_l2`: for a schema with modules M₁..Mₙ, encode chosen *groups* together
  (starting with adjacent pairs) and store the group's KV as an override that `CacheEngine.process`
  prefers when all members of the group are imported — exactly the semantics §3.3 specifies. (iii)
  Add a selection policy under a memory budget B: rank candidate groups by a cheap proxy for
  cross-module dependence (e.g. mean L2 deviation between a module's independently-encoded V and its
  co-encoded V, which needs one extra forward pass per candidate) and greedily admit groups until B
  is exhausted. (iv) Sweep B ∈ {0, 0.25×, 0.5×, 1×} of the L1 cache size and plot accuracy vs memory
  vs TTFT — the third axis matters because a larger group means more tokens to copy per request.
- **Code locations.** `promptcache/cache_engine.py` (`SchemaCache._process` at 185-307 is where the
  encoding passes are issued; `cache_l2`/`get_cache_l2` at 171, 179, 316-322 are the empty slots to
  fill; `CacheEngine.process` at 388-522 is where the override must be consulted before
  `get_cache_l1` at 499), `promptcache/schema.py` (`Scaffold`, 439-523, already knows how to
  materialise a selection — a group is a `Scaffold` over a subset), `benchmark/longbench.py:85-135`
  (must be changed to emit *multi-module* schemas: today it emits exactly one `<module
  name="context">` per sample, line 105, which is why LongBench barely exercises modularity at all),
  `eval.py:221-280` + `get_scores.py` (existing accuracy harness).
- **Motivating evidence.** §3.3 names scaffolding as the remedy for semantically dependent modules
  and explicitly frames it as a memory/quality trade — and the artifact does not implement it
  (§2.3(b)). Table 1's Passage Retrieval column drops 7.50→4.25 (Llama2-7B) and 9.08→6.50 (13B), and
  2WikiMQA drops 16.63→13.95, so the degradation regime is real and named by the paper's own bolding.
  Meanwhile the whole-scaffold encoding shortcut (§2.3(a)) means Table 1 probably *understates* the
  damage of true modular reuse; establishing that is itself a result. The scout's note
  ("schema-based reuse can perturb output quality, so an improvement claim needs an accuracy
  control") points at exactly this.
- **Feasibility: H.** All four pieces are localized: an alternate encoding loop in `_process`, a
  dictionary that already exists, a lookup in `process`, and a schema generator tweak. No new
  serving infrastructure. Well under ~1–2k LOC. Evaluated with the repo's own accuracy harness on
  one 7B model in 8-bit; the expensive part is generation over LongBench splits, which can be capped
  at ~100 samples/dataset on 3–4 datasets (~10–15 GPU-hours per arm).
- **Research value: H.** It tests whether the paper's central accuracy claim survives the encoding
  discipline the paper says it uses, and it explores a trade-off (spend *memory* to restore
  cross-module attention) that is the complement of everything the follow-up literature does (spend
  *compute*). Both outcomes are informative: if co-encoding is unnecessary, the "LLMs tolerate
  discontinuous positions" claim is strengthened at module granularity; if it is necessary, Prompt
  Cache's memory model (Table 2) is materially understated.
- **Scoop check: partial.** Queries: *"CacheBlend cross-attention KV cache fusion reused text chunks
  recompute EuroSys 2025"*, *"prompt cache modular attention reuse follow-up KV cache eviction policy
  non-prefix modules"*. Closest work attacks the same problem with **recomputation**, not
  precomputed groups: [CacheBlend (EuroSys'25 best paper)](https://dl.acm.org/doi/10.1145/3689031.3696098)
  selectively recomputes the top-k tokens with the largest V-value discrepancy; follow-ups EPIC,
  KVLink and [A³](https://arxiv.org/pdf/2511.17560) / [CacheClip](https://arxiv.org/pdf/2510.10129)
  do position-independent linking or trainable cross-chunk tokens. I found **no** work that
  precomputes co-encoded module groups under an explicit memory budget, and none that audits Prompt
  Cache's own scaffold-slicing shortcut. The honest framing for a course paper is therefore:
  *memory-for-quality (co-encoding) vs compute-for-quality (CacheBlend-style recompute) on one GPU* —
  and CacheBlend then becomes an obvious, implementable baseline rather than a scoop.

### A2 — A cost-aware tiered prompt-module cache (the paper's own "left to future research")

> **Hypothesis.** We hypothesize that a cost-aware GPU-residency policy that ranks prompt modules by
> (recompute_time − transfer_time) per byte, rather than by recency/frequency, reduces mean TTFT
> relative to LRU, LFU, and Prompt Cache's current usage-counter staging, under a multi-schema
> workload with Zipfian module popularity and a GPU cache budget well below the working-set size.

- **Mechanism.** Turn `PromptCache` into a real two-tier cache. (i) Actually use
  `TokenSequenceCache.upload()/free()` (currently dead code) so that admitted modules stay resident
  in HBM across requests instead of being re-copied every request. (ii) Replace the current staging
  rule — sort by `usage_counter`, keep the longest matching prefix of the previous layout, re-copy
  the rest (`PromptCache.update`, 115-156) — with a pluggable policy interface, and implement LRU,
  LFU, GDSF-style size-aware, and a cost-aware policy whose value is the *measured* per-module
  (recompute − transfer) time from the paper's own Fig. 5 curve. (iii) Add optional prefetch driven
  by `<union>` structure, which §3.2.3 explicitly suggests ("the system can utilize this structure
  for optimizations, such as prefetching"). (iv) Build the missing workload generator: today the
  harness adds one schema, serves one prompt, and calls `remove_all_schemas()` (`eval.py:280`,
  `eval_sys.py:363`), so **no cross-request reuse is ever exercised** — the artifact never measures
  the situation Prompt Cache is designed for. The generator should hold N schemas resident and draw
  module sets from a Zipf distribution.
- **Code locations.** `promptcache/cache_engine.py` (`PromptCache.__init__`/`update` at 87-166,
  `TokenSequenceCache.upload`/`free` at 65-73, `CacheEngine.add_schema`/`remove_all_schemas` at
  353-386, `CacheEngine.process` at 388-522), `eval_sys.py:88-215` (`run_critical_point` already
  measures the upload-vs-recompute crossover that the policy needs, per-sequence-length), plus a new
  generator alongside `benchmark/benchmark_base.py`.
- **Motivating evidence.** §4.1: "We leave the development of a system that incorporates cache
  replacement and prefetching strategies to future research." §6 repeats it. §5.5 notes that at
  0.5–2.5 MB/token the working set of "hundreds of prompt modules" is "tens of gigabytes", i.e.
  larger than a 24 GB GPU — so the policy question is forced, not hypothetical, on exactly this
  machine. And the artifact's dead `upload()`/`free()` shows the authors anticipated the tier but
  never populated it.
- **Feasibility: M.** The cache code is small and the policies are textbook, but this is
  cross-cutting (cache engine + a new multi-schema workload generator + new metrics: hit rate, bytes
  copied, TTFT distribution) and the evaluation is a new harness rather than the existing one.
  Compute is cheap — prefill-only, 7B, one GPU — but the engineering is a genuine 10-week,
  multi-student scope. Cache budgets can be enforced in-process; no cgroup or root tricks needed.
- **Research value: M.** A reviewer would recognise the question as the paper's own stated gap, and
  the *module* granularity (non-prefix, variable-size, with a known recompute cost) is a genuinely
  different caching object from a prefix block. But tiered KV caching is a crowded area and a
  "cost-aware beats LRU" result is close to expected; the surprise would have to come from the
  crossover regime (short modules are cheaper to recompute than to ship — Fig. 5 puts host→device at
  5.34 ms for 5K tokens, so the crossover is at a non-trivial length).
- **Scoop check: partial.** Queries: *"hierarchical GPU host KV cache tiering eviction prefetch LLM
  serving AttentionStore CachedAttention ATC 2024"*, *"prompt cache ... eviction policy non-prefix
  modules 2025"*. Closest: [CachedAttention/AttentionStore, USENIX ATC'24](https://www.usenix.org/system/files/atc24-gao-bin-cost.pdf)
  — multi-tier (HBM/DRAM/disk) KV cache with scheduler-aware prefetch and eviction, but for
  *multi-turn conversation prefixes*; [SGLang HiCache](https://www.lmsys.org/blog/2025-09-10-sglang-hicache/)
  — hierarchical radix-tree prefix cache across GPU/CPU/disk; and recent learned prefix-cache
  eviction work ("Not All Tokens Are Worth Caching", arXiv 2605.18825). All of these are
  **prefix-tree** structured; none handles the schema/module structure, the position-ID constraints,
  or the recompute-vs-transfer crossover for arbitrary composable segments. Not scooped, but the
  novelty must be argued on the module granularity, and the prefix-caching baselines should be cited
  and ideally emulated.

### A3 — Quantized module store + a per-module compute-or-load rule

> **Hypothesis.** We hypothesize that storing prompt modules in INT8 (and INT4) per-head-quantized
> form, combined with a per-module rule that *recomputes* modules shorter than the measured
> transfer/compute crossover instead of shipping them over PCIe, reduces TTFT for GPU inference with
> host-resident modules — the paper's weakest configuration at 1.5–3× (Fig. 3, yellow) — without a
> measurable LongBench score change, on a 24 GB Ampere GPU.

- **Mechanism.** The artifact already has the right seams: `store_k_hook`/`store_v_hook` are applied
  when a module's KV is captured (`cache_engine.py:284-285`) and `read_k_hook`/`read_v_hook` when it
  is handed to the model (`cache_engine.py:513`); all four are identity today
  (`promptcache/model/__init__.py:116-126`). Implement (a) per-head/per-channel affine INT8 and INT4
  quantization in the store hooks with dequantization in the read hooks, so only the quantized bytes
  cross PCIe; (b) a per-module dispatch in `CacheEngine.process` that consults a calibration table —
  produced by the repo's own `run_critical_point` (`eval_sys.py:88-215`) — and recomputes short
  modules on the GPU rather than uploading them; (c) measure both the `cache_time` component and the
  prefill component separately (they are already separated at `cache_engine.py:391-509`), plus
  accuracy via `eval.py` + `get_scores.py`. Note FP8 is *not* an option: the A5000 is SM 8.6, so INT8
  via `torch` integer ops is the right target.
- **Code locations.** `promptcache/model/__init__.py:116-126` (the four hooks — the designated
  extension point), `promptcache/cache_engine.py:50-83` (`TokenSequenceCache`, where the stored
  representation lives), `:115-156` (`PromptCache.update`, the copy path), `:496-513`
  (`CacheEngine.process`, where dispatch and the read hooks sit), `eval_sys.py:88-215` (calibration),
  `eval.py` + `get_scores.py` (accuracy control).
- **Motivating evidence.** §6 names both halves as future work: "the integration of compression
  techniques in the KV cache, or utilization of grouped query attention". §5.5 makes the memory case
  (2.5 MB/token at 70B "leaves CPU memory as the only option"). §5.4 measures host→device at 5.34 ms
  vs host→host 3.79 ms and device→device 0.23 ms for 5K tokens — i.e. for GPU inference the PCIe
  copy *is* the overhead, and it is the difference between the 1.5–3× and 5–10× bars in Fig. 3. And
  the existence of four unused hooks is the authors telling you where to put this.
- **Feasibility: H.** Quantization in the hooks is a contained change (hundreds of LOC); the
  calibration harness exists; evaluation runs on the existing scripts on one GPU. The only subtlety
  is that the dequantized tensors must match the vendored models' expected dtype/layout at
  `llama2.py:363-364`.
- **Research value: M.** The direction is well trodden and the expected outcome (INT8 is nearly
  free, INT4 costs some accuracy) is not surprising. What is less expected, and worth the
  experiment, is the *interaction*: once modules are 2–4× smaller, the compute-or-load crossover
  moves, and the optimal policy may flip for a whole class of module sizes. That interaction, on a
  single-node PCIe budget rather than a network, is the defensible contribution.
- **Scoop check: partial.** Queries: *"KV cache quantization compression to reduce host-to-device
  PCIe transfer latency cached context loading CacheGen"*. Closest:
  [CacheGen (SIGCOMM'24)](https://dl.acm.org/doi/10.1145/3651890.3672274) compresses KV into
  bitstreams for *network* fetch (3.5–4.3× over a quantization baseline);
  ["Compute or Load KV Cache? Why not both?" (Cake, arXiv 2410.03065)](https://arxiv.org/html/2410.03065v1)
  explicitly overlaps loading and recomputing; ZipCache/KIVI-style quantization is standard. So both
  ingredients exist separately. Not scooped for the *modular, host-to-device, single-node* setting,
  but this add-on should be positioned as "port two known techniques into Prompt Cache and measure
  the crossover shift", which is honest and still publishable as an improvement paper — and it is
  the weakest of the four on novelty.

### A4 — Cross-request module sharing in a batch

> **Hypothesis.** We hypothesize that materialising a shared prompt module's KV **once** per batch
> (as a broadcast view or a block table) rather than once per request increases sustained
> throughput and the maximum feasible batch size for prompts drawn from a common schema, on a 24 GB
> GPU — a benefit the paper argues arithmetically (§3.4, §5.4) but never measures.

- **Mechanism.** The serving path is strictly batch-size-1: `CacheEngine.process` returns a single
  token-id list, and both `eval.py:192-198` and `generation_engine.py:96-102` add a redundant batch
  dimension with `unsqueeze(0)`. Add a batched path that (i) groups queued prompts by schema,
  (ii) builds a per-batch KV where shared modules are `expand`-ed (stride-0) rather than copied and
  unshared suffixes are padded, (iii) supplies the right additive attention mask so padded slots are
  ignored — the vendored `LlamaModel._prepare_decoder_attention_mask`
  (`promptcache/model/llama2.py:798-819`) already composes a causal mask with a padding mask, so the
  hook exists, and (iv) measures tokens/s and peak `torch.cuda.max_memory_allocated` versus batch
  size, against a per-request-copy control.
- **Code locations.** `promptcache/cache_engine.py:87-166` (`PromptCache`, the device staging
  buffer — currently `[num_head, max_ctx_length, head_dim]` with no batch dimension, line 104-107),
  `:388-522` (`CacheEngine.process`), `promptcache/generation_engine.py:91-147` (the decode loop),
  `promptcache/model/llama2.py:798-819` (mask construction) and `:361-369` (where `past_key_value`
  is concatenated and would need to tolerate an expanded view), `eval.py:172-219`.
- **Motivating evidence.** §3.4 "Memory optimization in batch inference" and §5.4 both claim the
  benefit numerically ("100 requests, each with a 2K token prompt … reduce the memory footprint by
  50%") without an experiment; §6 lists "GPU primitives for sharing attention states across
  concurrent requests" as future work and notes it would improve TPOT, not just TTFT — the one
  latency component Prompt Cache currently cannot touch (§5.4: TPOT unchanged at ~32 ms/token).
- **Feasibility: M.** This is the most invasive of the four: it touches the cache engine, the
  generation loop, and the vendored attention/mask code, and it needs a new throughput harness
  (the repo has none — every script measures a single request). It is squarely doable on one GPU
  with a 7B 8-bit model, but it is a 10-week, multi-student job and carries real risk that the
  `expand`-ed view is materialised by `torch.cat` at `llama2.py:363-364` anyway, silently removing
  the benefit — which the team would have to detect and work around.
- **Research value: M.** vLLM/SGLang already share *prefix* blocks across requests by reference
  counting with copy-on-write, so the concept is established; the contribution is showing it for
  *non-prefix, schema-composed* modules and quantifying the batch-size/throughput headroom the paper
  only asserted. Solid, expected, moderately interesting.
- **Scoop check: partial.** Query: *"sharing non-prefix KV cache blocks across concurrent requests
  in a batch paged attention modular reuse throughput 2025"*. Paged-attention block sharing with
  reference counting and copy-on-write is standard practice, and recent work
  ([GraniKV, arXiv 2608.15584](https://arxiv.org/html/2608.15584);
  [CoDec, arXiv 2505.17694](https://arxiv.org/pdf/2505.17694)) refines shared-prefix paging and
  prefix-shared decoding kernels. Nothing found that batches *schema-composed non-prefix* modules
  with discontinuous position IDs, but the marginal novelty over prefix sharing is thin and a
  reviewer would press on it.

---

## 6. Risks and open questions

1. **The paper's §3.3 description and the code disagree about what is masked.** Modules are encoded
   by one forward pass over the whole scaffold and then sliced (`cache_engine.py:221-296`), so within
   a schema each module attends to its predecessors. Table 1's "accuracy is preserved" may therefore
   be measuring a much weaker approximation than §3.3 advertises. This is simultaneously the largest
   threat to the paper's claim, the best add-on hook (A1), and something I could only establish by
   reading — it deserves an explicit empirical check early.
2. **The headline 8× configuration is not reachable from a config file.** `cache_engine.py:290-292`
   always demotes modules to host memory when the target device is a GPU, and `upload()`/`free()`
   are dead code. Either the paper's GPU-memory bars came from a code path that was not released, or
   they came from a trivial variant of line 290. Reproducing the blue bars therefore requires an
   (educated) edit, which weakens "we reproduced Figure 3" to "we reproduced Figure 3 after a
   one-line change we believe matches the paper".
3. **The evaluation never exercises cross-request reuse.** `remove_all_schemas()` is called after
   every entry (`eval.py:280`, `eval_sys.py:363`), and schema encoding time is excluded from the
   reported TTFT. The measured speedup is thus an upper bound that assumes an infinitely warm,
   never-evicted cache — exactly the assumption A2 is designed to remove. Any improvement claim must
   state amortisation explicitly.
4. **LongBench barely tests modularity.** `benchmark/longbench.py:105` puts the entire document in a
   single `<module name="context">`, so the accuracy evaluation is effectively single-module (i.e.
   prefix) reuse. Multi-module behaviour is demonstrated only in the §5.6 qualitative case studies
   (`examples/*.xml`), which have no metric. Any accuracy claim about *modular* reuse needs new
   multi-module schemas.
5. **Undocumented dataset exclusions.** `scripts/benchmark_setup.json:25-34` shows `lcc`,
   `repobench-p` and `samsum` were dropped because "code syntax interferes with xml syntax of prompt
   cache" — an inherent fragility of an XML-based PML that the paper does not discuss — and
   `lsht`/`vcsum`/`dureader` for OOM. Expect the same on this machine, with a smaller GPU.
6. **Statistical strength.** `eval_sys.py` uses 5 entries × 3 repeats per dataset (`:305`, `:318`,
   `:29`); `eval_acc.py` uses 3 entries (`:105`). `get_scores.py` does report a std (`:99`) but the
   paper's tables do not. Effect sizes in Table 1 (e.g. 16.63 vs 13.95) may not be separable from
   noise. A reproduction should report confidence intervals — and that alone is a defensible
   "Contemporary paper" fallback if the improvement does not pan out.
7. **Gated weights.** `meta-llama/Llama-2-7b-chat-hf` and `codellama/CodeLlama-7b-Instruct-hf`
   (used by `demo.py:27`) require HF licence acceptance. Falcon-7B/MPT-7B configs in the repo are
   the ungated fallback, but MPT requires `trust_remote_code=True`
   (`promptcache/model/__init__.py:264`) and sets `use_full_position_ids=True` (`:275`), a
   materially different code path with less coverage in the repo.
8. **Frozen dependency stack.** Because the repo vendors transformers-4.34 model files, the project
   is locked to a 2023-era stack (`promptcache/model/llama2.py:34`, `:593`). That is fine for a
   reproduction but means an add-on cannot casually adopt a modern `transformers`, FlashAttention-2
   (the FA2 path at `llama2.py:413-584` is missing its `flash_attn_func` import), or an SDPA kernel
   without porting work — relevant to A4 in particular.
9. **A5000 ≠ A40/4090.** The paper's GPUs have more memory (A40 48 GB, A100 40 GB) and, for the
   4090, substantially more compute. Absolute TTFTs will differ; the *ratio* is the claim to
   reproduce, and ratios should hold since both arms run on the same device.
10. **Scoop pressure is real and rising.** CacheBlend, EPIC, KVLink, A³, CacheClip, CachedAttention,
    SGLang HiCache and CacheGen collectively cover large parts of the obvious improvement space
    around this paper. The defensible angles are the ones grounded in what the *artifact* does not
    do (A1's memory-for-quality trade and the scaffold-slicing audit; A2's module-granularity
    tiering), not generic "make KV reuse better" proposals.

---

## 7. Evidence index

**Paper** (`paper.txt`, page-marked):
- Abstract, §1 Introduction (p.1–2) — problem, 8×/60× claims, code URL (p.2).
- §2.2 Key-Value Cache (p.3) — baseline, prefix-sharing related work.
- §3.1 Overview (p.3–4) — discontinuous position IDs.
- §3.2 PML: schema vs prompt, parameters, unions, nesting, chat tags (p.4–5); §3.2.3 prefetching hint.
- §3.3 Encoding schema, attention masking effect, **scaffolding** (p.6).
- §3.4 Cached inference; batch memory optimization (p.6).
- §4 Implementation; §4.1 CPU/GPU module storage and the "future research" note; §4.2 RoPE/ALiBi
  lookup tables, buffered concat (p.7).
- §5.1 Evaluation environment (p.7) — CPUs, GPUs, "single GPU (40 GB)", LongBench.
- §5.2.1 GPU latency / **Figure 3** (p.8) — 1.5–3× CPU-memory, 5–10× GPU-memory.
- §5.2.2 CPU latency / **Figure 4** (p.8) — 70×/20×.
- §5.3 + **Table 1** (p.8–9) — accuracy across Llama2-7B/13B, MPT-7B, Falcon-7B.
- §5.4 + **Figure 5** (p.9) — quadratic advantage, memcpy timings, TTFT 900→90 ms, TPOT 32 ms.
- §5.5 + **Table 2** (p.9–10) — memory per cached token.
- §5.6 + **Figures 6/7/8** (p.10–11) — code generation, personalization, parameterized prompts.
- §6 Conclusions and future work (p.11) — replacement strategies, compression/GQA, batch sharing, RAG.

*(`pages/*.png` were not present in this input tree; figure values above are taken from the paper's
own prose in §5.2–§5.5, which states them numerically.)*

**Repository** (paths relative to `repo/`):
- `README.md` (1-104 install/demo/expected TTFTs, 106-221 PML reference, 225-237 eval commands,
  239-247 citation)
- `requirements.txt`, `Makefile`, `.gitmodules`, `LICENSE`, `g.sh`
- `promptcache/__init__.py`, `promptcache/cache_engine.py`, `promptcache/schema.py`,
  `promptcache/prompt.py`, `promptcache/generation_engine.py`, `promptcache/compiler.py`
- `promptcache/model/__init__.py`, `promptcache/model/llama2.py`, `promptcache/model/falcon.py`,
  `promptcache/model/mpt.py`
- `eval.py`, `eval_acc.py`, `eval_sys.py`, `get_scores.py`, `metrics.py`, `demo.py`,
  `benchmark_memcpy.py`
- `benchmark/benchmark_base.py`, `benchmark/longbench.py`, `benchmark/metrics.py`,
  `benchmark/utils.py`, `benchmark/results/README.md`
- `config/llm_config_llama2_7b.json`, `config/llm_config_llama2_13b.json`,
  `config/llm_config_falcon_7b.json`, `config/llm_config_falcon_40b.json`,
  `config/llm_config_mpt_7b.json`, `config/llm_config_mpt_30b.json`,
  `config/llm_config_vicuna_7b.json`
- `scripts/run_benchmarks.py`, `scripts/benchmark_setup.json`, `scripts/README.md`
- `eval_sys_a40-7b-gpu.slurm` (and the three sibling `.slurm` files)
- `examples/code_generation_game.xml`, `examples/personalization-education.xml`,
  `examples/parameterized_prompts.xml`, `examples/persona_generation.xml`
- `repo_facts.json`, `fetch_result.json`, `meta.json` (driver-supplied)

**External (scoop check / provenance):**
- CacheBlend, EuroSys'25 — https://dl.acm.org/doi/10.1145/3689031.3696098 (arXiv 2405.16444)
- A³: Attention-Aware Accurate KV Cache Fusion — https://arxiv.org/pdf/2511.17560
- CacheClip: Accelerating RAG with Effective KV Cache Reuse — https://arxiv.org/pdf/2510.10129
- CachedAttention / AttentionStore, USENIX ATC'24 — https://www.usenix.org/system/files/atc24-gao-bin-cost.pdf
- SGLang HiCache — https://www.lmsys.org/blog/2025-09-10-sglang-hicache/
- CacheGen, SIGCOMM'24 — https://dl.acm.org/doi/10.1145/3651890.3672274
- Compute or Load KV Cache? Why not both? — https://arxiv.org/html/2410.03065v1
- GraniKV — https://arxiv.org/html/2608.15584 ; CoDec — https://arxiv.org/pdf/2505.17694
- MLSys 2024 CFP / AE policy — https://mlsys.org/Conferences/2024/CallForPapers (no badge found for
  this paper on the proceedings page or in the PDF)
