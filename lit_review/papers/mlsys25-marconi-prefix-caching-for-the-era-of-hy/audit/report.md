# Marconi: Prefix Caching for the Era of Hybrid LLMs

MLSys 2025 · Pan, Wang, Jia, Karakus, Zancato, Dao, Wang, Netravali (Princeton + AWS)
Repo: <https://github.com/ruipeterpan/marconi> (head commit 2025-03-05)

---

## 1. Paper summary

**Problem.** Hybrid LLMs interleave a few Attention layers with many recurrent/SSM
(Mamba-style) layers. SSM layers update their state *in place*, so a state that
represents tokens `1..q` cannot be rolled back to represent `1..p` (paper §3, "SSM
State Properties" 1–3, p. 4). Prefix caching therefore requires **exact-match**
SSM state hits. Maximizing reuse then demands fine-grained checkpointing (a state
every *x* tokens), but each SSM state is fixed-size and 10–100× larger than one
token's KVs (§3). The measured consequence (Fig. 3a, p. 4): at block size 32,
25.0 % of KV token blocks are reused but only **0.4 %** of SSM states — a 65.3×
gap; and a single 10 K-token sequence of a 7B hybrid model costs 17.4 GB of state
(Fig. 3b), 3.3× a Transformer of the same size. Net effect: cache thrashing with
large, sparsely-hit entries.

**Key idea.** Two policies on a single radix tree that holds KVs *and* SSM states
per node (§4, Fig. 4, p. 5):

1. **Judicious admission (§4.1).** A taxonomy of reuse: *purely-input* prefixes
   (system prompts, few-shot examples) vs *input-and-output* prefixes
   (conversation history, agent trajectories). For the latter Marconi checkpoints
   only the state at the **last decoded token**; for the former it runs a
   **speculative insertion** of the input tokens before prefill and, if that would
   create a new intermediate (branch-off) node, checkpoints the state **at the
   branch point**. At most **two** SSM states per sequence are admitted. Cost: a
   purely-input prefix is only reusable from its *third* occurrence (§4.1,
   "Tradeoffs", p. 6). Obtaining the state mid-prefill is done either by
   materializing the second-to-last chunk state (chunked-state-passing models) or
   by a **two-pass prefill** (§4.1, "Obtaining states during prefill").
2. **FLOP-aware eviction (§4.2).** New metric *FLOP efficiency* = FLOPs saved /
   bytes of state (Eq. 1; Table 1, p. 15). For KVs this is near-constant in
   sequence length; for SSM states it grows ~linearly (Fig. 5, p. 6), so size is a
   bad proxy for value. Utility `S(n) = recency(n) + α · flop_efficiency(n)`
   (Eq. 2), both min-max normalized. α is tuned **retrospectively once**: run LRU
   until the first eviction, then observe a bootstrap window of 5–15× that many
   requests, then grid-search α by replaying the window in parallel across CPU
   cores (§4.2, "Managing the balance"). Implementation notes (§4.3): all nodes
   with ≤1 child are eviction candidates (not just leaves); an evicted
   intermediate node releases its SSM state and its KVs are absorbed by its child;
   on a hit only the accessed node's timestamp is updated, not ancestors'.

**Evaluation setup (§5.1, p. 8).** Baselines: vanilla (no caching), **vLLM+**
(fine-grained checkpointing, block size 32), **SGLang+** (Marconi's admission +
plain LRU eviction). Metric: **token hit rate** (tokens that skipped prefill /
total input tokens), plus P5/P50/P95 TTFT. Workloads: LMSys-Chat-1M, ShareGPT,
and SWE-Agent trajectories on SWE-Bench-Verified, all tokenized with the
Llama-2-7B tokenizer; 100 sessions each, sweeping session arrival rate and cache
size. Model: 7B hybrid, {4 Attn, 24 SSM, 28 MLP}, D = 4096, N = 128, FP16. TTFT
numbers come from profiling **Jamba-1.5-Mini on 4×A100-40GB**; the trace-driven
policy experiments ran on the CPUs of a p4d.24xlarge.

**Headline numbers.** Token hit rate vs vLLM+ improves by 4.5× / 7.3× / 34.4×
(mean) on LMSys / ShareGPT / SWEBench (Fig. 7, p. 8). Vs SGLang+ (i.e. isolating
FLOP-aware eviction): P95 wins of 45.6 % / 19.0 % / 219.7 % (Fig. 8, p. 9). P95
TTFT drops up to 36.1 % / 71.1 % / 46.8 % (275.4 / 103.3 / 617.0 ms) vs vLLM+
(Fig. 9, p. 9). Fine-grained analysis (Fig. 10, p. 9): Marconi loses up to 3.0 %
hit rate on <7 K-token requests and gains up to 25.5 % on >7 K, for +90.3 % total
FLOPs saved; P5 TTFT is 6.3 % worse (2.1 ms) while P50/P95 improve 13.4 %/22.0 %.
Microbenchmarks: benefits peak at *moderate* cache contention (Fig. 11, p. 10),
grow with SSM:Attn ratio (Fig. 12a) and with SSM state dimension — 5.7× → 35.4×
vs vLLM+ as N goes 16 → 128 (Fig. 12b) — and grow with contention from arrival
rate (Fig. 13).

**Stated limitations / future work.** Only up to two SSM states per sequence, so
arbitrary-prefix reusability is reduced (§4.1 Tradeoffs). Purely-input prefixes
miss their second occurrence. Chunk-based checkpointing "may miss some prefix
caching opportunities within a chunk" and the two-pass alternative has runtime
cost — neither is quantified. Only Mamba is evaluated; other recurrent layers are
claimed to behave similarly (§6). Cost-aware eviction (GDSF etc.) is declared
*complementary*, not integrated (§4.2, "Comparisons with existing size-based
eviction algorithms").

---

## 2. Artifact audit

### Repo structure (29 files, 4.25 kLOC Python, 0.2 MB)

```
radix_cache_hybrid.py   561 lines — Marconi: radix tree, admission, evict_v1/evict_v2
radix_cache_vllm.py     416 lines — vLLM+ baseline: block-granular tree, LRU on leaves
config_tuner.py         121 lines — retrospective α grid search (ProcessPoolExecutor)
utils.py                169 lines — FLOP / state-size formulas (paper Table 1)
policy_exploration.py   354 lines — experiment driver: config sweep, runs vLLM+/V1/V2/V3
toy_example.py           59 lines — 6-prompt radix-tree walkthrough
run_all_experiments.sh   14 lines — bash loop over the three datasets
plotting/  (11 scripts)          — figure scripts
utils/     (4 scripts)           — generate_trace.py (trace construction), log parsers
data/ttft_AI21-Jamba-1.5-Mini.pickle — profiled TTFT-vs-seqlen table (the only GPU-derived data)
environment.yml                  — conda env (Python 3.11.9)
artifact_evaluation.md           — full artifact appendix
```

### Paper component → code path

| paper | code |
|---|---|
| Radix tree holding KVs + SSM states (§4, Fig. 4) | `radix_cache_hybrid.py:32` `TreeNode`, `:69` `RadixCache` |
| Speculative insertion before prefill (§4.1) | `radix_cache_hybrid.py:220` `match_prefix(..., actually_inserting=False)` called from `insert()` at `:158`; `branchoff_required` at `:247` |
| Admit ≤2 SSM states/sequence (§4.1) | `radix_cache_hybrid.py:163` `num_extra_mamba_states = 2 if branchoff_required else 1` |
| Branch-point checkpoint (§4.1) | `radix_cache_hybrid.py:322` `_split_node(..., state_at_branchoff)` |
| FLOP efficiency, Eq. 1 / Table 1 | `utils.py:21-168` (`get_attn_flops`, `get_mlp_flops`, `get_mamba1_flops`, `get_kvs_size`, `get_mamba_state_size`, `get_flops_efficiency`) |
| Utility score, Eq. 2 (§4.2) | `radix_cache_hybrid.py:534-546` (`_normalize`, `eff_weight * eff_score + recency_score`) |
| α bootstrap + grid search (§4.2) | `radix_cache_hybrid.py:147-155`, `config_tuner.py:58` `tune_config`, `:13` `replay_trace` |
| §4.3(1) evict nodes with ≤1 child; child absorbs KVs | `radix_cache_hybrid.py:383` `_collect_leaf_and_single_child_nodes`, `:417` `_evict_intermediate_node` |
| §4.3(2) only accessed node's timestamp updated | `radix_cache_hybrid.py:256-261`, and the `evict_policy_version in [1]` branches at `:269`/`:346` that keep SGLang+ behaviour |
| vLLM+ baseline (block size 32) | `radix_cache_vllm.py` (`block_size=32` set at `policy_exploration.py:227`) |
| SGLang+ baseline (= Marconi admission + LRU) | `evict_policy_version=1` → `radix_cache_hybrid.py:484` `evict_v1` |
| Offline-optimal static-α oracle (V3; not in paper) | `evict_policy_version=3`, `policy_exploration.py:268-316` |
| 7B hybrid model config (§5.1 Models) | `policy_exploration.py:196-202` (24 SSM / 4 Attn / 28 MLP, D=4096, N=128) |
| Cache-size & arrival-rate sweeps (Fig. 11, 13) | `policy_exploration.py:159` `generate_configs` |
| Fig. 7 | `plotting/token_hit_rate.py` |
| Fig. 8 | `plotting/sglang_comparison.py` |
| Fig. 9 / 10b (TTFT) | `plotting/ttft.py` + `data/ttft_AI21-Jamba-1.5-Mini.pickle` |
| Figs. 10a, 11, 12a, 12b, 13 | `plotting/fine_grained_analysis.py`, `microbenchmark_contention.py`, `microbenchmark_layer_composition.py`, `microbenchmark_dstate.py`, `microbenchmark_arrivalrate.py` |
| Trace construction (§5.1 Workloads, Fig. 6) | `utils/generate_trace.py` (LMSys, ShareGPT, SWEBench, plus an unused WildChat path) |

**What the artifact is.** A **trace-driven simulator**, not a serving-engine
integration. `state_at_leaf` / `state_at_branchoff` are passed the integer
`session_id` (`policy_exploration.py:125-126`), i.e. states are placeholders; only
their *sizes* and *FLOP savings* are modelled through `utils.py`. This matches the
paper: §5.1's primary metric is token hit rate, and TTFT is derived from a
profiled latency table rather than measured end to end. Nothing in the repo runs a
model.

**Build route on this machine.** `conda env create -f environment.yml` creates a
Python 3.11.9 env. The file pins **exact conda build strings** (e.g.
`libgcc-ng=13.2.0=h77fa898_11`, `python=3.11.9=hb806964_0_cpython`) plus a pip
block with `torch==2.4.0`, `triton`, and the `nvidia-*-cu12` wheels. Exact-build
solves are the most likely failure mode. The simulator itself only imports
`scipy`, `transformers`, `datasets`, `numpy`, `pandas`, `pytz`, `tqdm`,
`matplotlib`, `scikit-learn` (`plotting/ttft.py:10`) and `gdown`; `torch` is only
needed by `utils/generate_trace.py` and `toy_example.py`. A hand-built conda env
with those ~10 packages is the safe fallback. No root, no Docker, no compilation.
Note `NUM_CPUS = os.cpu_count()` (`policy_exploration.py:27`, `config_tuner.py:11`)
→ 32 workers here, which is fine for a 21-point grid search but each worker holds
a `pickle`-deep-copied radix tree (`config_tuner.py:78`), so peak RSS scales with
32 × tree size.

**Data sources.** Pre-tokenized request traces (~700 MB compressed / 6.3 GB
expanded) are hosted on **Google Drive**, fetched with `gdown`
(`artifact_evaluation.md:69`). Raw datasets, if regenerating: LMSys-Chat-1M
(HF `lmsys/lmsys-chat-1m` — **gated**, requires accepting terms), ShareGPT
(`anon8231489123/ShareGPT_Vicuna_unfiltered` — ungated), SWE-bench experiments
(public GitHub). `utils/generate_trace.py:12` uses the **gated**
`meta-llama/Llama-2-7b-hf` tokenizer and hard-codes
`/home/ubuntu/SWE-bench-experiments/...` at line 232. The only model weights
needed for the main results are none; the GPU-profiled TTFT table is already
checked in.

**Eval scripts present/absent.** `run_all_experiments.sh` + `policy_exploration.py`
produce `logs/{lmsys,sharegpt,swebench}.txt` and pickles under `results/`.
`plotting/token_hit_rate.py` (Fig. 7) and `plotting/sglang_comparison.py` (Fig. 8)
read those logs directly and are the officially supported AE targets
(`artifact_evaluation.md:110-113`). The remaining plotting scripts are explicitly
disclaimed: `plotting/ttft.py:218-221` hard-codes *SOSP-version* log filenames
(`../logs/1029_lmsys_initw0.0_wind=1000.txt`) that the sweep does not produce, and
applies a `LinearRegression` smoothing plus a `multiplier = 10` fudge for a
self-documented unit bug (`plotting/ttft.py:16-18`). So **Figs. 9–13 are not
turn-key**.

**Provenance / badges.** The paper states "Marconi is open sourced at
https://github.com/ruipeterpan/marconi" (§1, p. 2) and the artifact appendix
(§B.3.1, p. 16) names the same repo plus Zenodo DOI 10.5281/zenodo.14970139.
`ruipeterpan` is the first author (correspondence `ruipan@princeton.edu`, which
also appears in `artifact_evaluation.md:32`). The MLSys 2025 virtual poster page
links the repo as the project page. I found **no explicit ACM/MLSys badge image or
badge list**; the presence of a full Artifact Appendix + archived Zenodo DOI +
cTuning methodology links (`artifact_evaluation.md:129-133`) indicates the artifact
went through MLSys AE, but I cannot confirm which badges were awarded.

---

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper §1 p. 2 names `github.com/ruipeterpan/marconi`; artifact appendix §B.3.1 repeats it with Zenodo DOI 10.5281/zenodo.14970139; `ruipeterpan` is first author Rui Pan. The repo contains the real system, not a stub: admission + FLOP-aware eviction in `radix_cache_hybrid.py` (561 lines), α tuner in `config_tuner.py`, both baselines (`radix_cache_vllm.py`, `evict_policy_version=1`), the sweep driver `policy_exploration.py`, and plotting. It is a simulator — but so is the paper's own evaluation harness. |
| `H2_no_root` | **pass** | Pure Python + one bash loop (`run_all_experiments.sh`). No Dockerfile, no kernel module, no eBPF, no perf, no `sudo` anywhere in the tree. `repo_facts.json` red flags are all false positives: `big_gpu` hits are matplotlib `axhline` annotations in `plotting/plotting.py:81,85,347`; `multi_gpu` is the `nvidia-nccl-cu12` transitive pin in `environment.yml:147` (unused by the simulator); `multi_node` hits are Cloudlab prose in `artifact_evaluation.md:29,32`. |
| `H3_hardware_fit` | **pass** | The experiments are CPU-only trace replay; the paper's p4d.24xlarge (§5.1 Setup, p. 8) was used for its 96 CPUs, and the 4×A100 Jamba-1.5-Mini profiling produced `data/ttft_AI21-Jamba-1.5-Mini.pickle`, which is already in the repo. The "60–140 GB cache size" sweep (Fig. 11) is a *simulated* byte budget (`capacity_bytes` at `policy_exploration.py:162-175`), not real GPU memory. 16 c / 32 t and 111 GB RAM cover the 32-way grid search; ~13–20 GB disk for traces fits in 257 GB free. No GPU is needed for Figs. 7 and 8. |
| `H4_obtainable_deps_data` | **pass** | All deps are conda/pip, user space (`environment.yml`); the simulator needs only ~10 pure-Python/NumPy packages. Pre-tokenized traces are publicly downloadable via `gdown` from a Drive link given in `artifact_evaluation.md:69`; no credentials. Regeneration path also exists (`utils/generate_trace.py`) from ShareGPT (ungated HF) and the public SWE-bench-experiments repo. Caveats (see §6): LMSys-Chat-1M on HF and the `meta-llama/Llama-2-7b-hf` tokenizer used at `utils/generate_trace.py:12` are gated, and the Drive link is a single point of failure. |

---

## 4. Reproduction plan

**Target.** **Fig. 7** (paper p. 8) and its claim: *judicious admission raises the
token hit rate by a mean of 4.5× / 7.3× / 34.4× over vLLM+ on LMSys / ShareGPT /
SWEBench*. Secondary, same run: **Fig. 8** (p. 9), Marconi vs SGLang+ P95 wins of
45.6 % / 19.0 % / 219.7 %, which isolates FLOP-aware eviction. These are the two
figures the authors themselves designate as the AE targets
(`artifact_evaluation.md:110-113`), and both plotting scripts consume only the
logs the sweep produces.

**Scale-down.**

1. Drop the **V3 offline-oracle** sweep (`policy_exploration.py:268-316`): 21 extra
   full-trace replays per config that are not in the paper. This removes ~85 % of
   the compute and does not touch Fig. 7 or Fig. 8. (Keep the V2-internal
   `ConfigTuner` grid search — that *is* Marconi.)
2. Run the LMSys (30 configs) and ShareGPT (36 configs) sweeps in full — the README
   quotes ~30 s and ~5 s per trace on a 32-core box.
3. For SWEBench (72 configs at 5–10 min/trace) run a **quarter-sweep**: the 4 cache
   sizes × `sessions_per_second ∈ {0.25, 1, 10}` × `avg_response_time = 5`, i.e.
   12 configs. The boxplot then has 12 instead of 72 points but still covers the
   contention and arrival-rate axes that drive the claim.
4. If RSS becomes a problem, cap the tuner's worker count by patching
   `NUM_CPUS` (`config_tuner.py:11`) to 16.

**Steps.**

1. `conda create -n marconi python=3.11` and install
   `numpy pandas scipy matplotlib scikit-learn transformers datasets tqdm pytz gdown`
   by name (do **not** solve `environment.yml`'s exact build strings; see §6).
2. `gdown --fuzzy <Drive link from artifact_evaluation.md:69>`; `tar -xzf`;
   `mkdir logs results figures/eval`.
3. Sanity check: `python toy_example.py` (needs the `EleutherAI/gpt-neox-20b`
   tokenizer, ungated) — exercises insert / split / evict on 6 prompts.
4. Patch out the V3 block and reduce the SWEBench config list, then
   `bash run_all_experiments.sh`.
5. `cd plotting && python token_hit_rate.py` → prints the per-percentile
   Marconi/vLLM+ ratios and the **average improvement** that Fig. 7's caption
   reports; `python sglang_comparison.py` → Fig. 8.
6. Compare the printed means against 4.5× / 7.3× / 34.4×.

**Effort.** ≈ 3 person-days (1 for env + traces, 1 for the V3/config patch and a
first LMSys+ShareGPT run, 1 for the SWEBench subset and comparison) + ≈ 30–60
CPU-core-hours, **0 GPU-hours**. A full un-scaled sweep is closer to 1–2 machine-days
of wall clock even with V3 removed, which is why the subset matters.

**Level: H.** Reasons: the exact scripts for the target figures exist and read the
exact logs the driver writes; determinism is engineered in
(`use_logical_ts=True`, `radix_cache_hybrid.py:80`, so results do not depend on
wall-clock timing); the workload is CPU-only and the machine has more RAM than the
simulator needs; there are no model weights, no CUDA kernels, and no build step.
The two real frictions — the exact-build `environment.yml` and the Drive-hosted
traces — are both routine porting work, not blockers, which is exactly the H/M
boundary; I place it at H because neither touches the scientific content and the
authors ship a documented regeneration path.

---

## 5. Add-on ideas

### A1 — Block-aligned checkpointing: is the headline hit rate an artifact of an idealized assumption?

**Hypothesis.** We hypothesize that constraining SSM checkpoints to fall on
fixed block boundaries — as every shipping hybrid engine actually does — reduces
Marconi's token hit rate by a large, workload-dependent margin (we predict >30 %
relative on SWEBench, with occasional collapse to near-zero reuse), and that an
**alignment-aware admission policy** (checkpoint at the largest block boundary
≤ the branch point, and additionally admit the boundary *after* it when the branch
point falls mid-block) recovers most of the loss at ≤1 extra SSM state per
sequence.

**Mechanism.** `radix_cache_hybrid.py` has **no notion of block or chunk size at
all** (grep for `chunk|block_size` in that file returns nothing): `_split_node`
materializes a state at the *exact* branch offset, and `match_prefix` credits the
full matched prefix. Add a `chunk_size` parameter; in `match_prefix`, floor the
reusable prefix length to `chunk_size * floor(prefix_len / chunk_size)` relative to
the node's checkpoint position; in `insert`/`_split_node`, place the branch-off
checkpoint at the floored boundary and charge the missing suffix as recompute.
Then implement the alignment-aware variant as a new `evict_policy_version` /
admission flag, and sweep `chunk_size ∈ {32, 64, 128, 256}` — the paper itself
cites "every 256 tokens" as the realistic checkpoint interval (§1, p. 1).

**Code locations.** `radix_cache_hybrid.py:220` (`match_prefix`),
`radix_cache_hybrid.py:120` (`insert`), `radix_cache_hybrid.py:322`
(`_split_node`), `radix_cache_hybrid.py:163` (state-count accounting),
`utils.py`, `policy_exploration.py:196`.

**Motivating evidence.** §4.1 "Obtaining states during prefill" (p. 5–6) concedes
the chunked approach "may miss some prefix caching opportunities within a chunk",
and the alternative is a two-pass prefill — neither is quantified anywhere in the
paper, and the simulator silently assumes the *exact* checkpoint is free. Real
systems have since discovered this is the dominant failure mode: vLLM's hybrid
prefix cache only supports `mamba_cache_mode="align"`, and because
`HybridKVCacheCoordinator` requires *every* group to match, a misaligned Mamba
checkpoint **vetoes** the attention groups' hits — a 100-token prompt shift flips a
workload between 52/64 hits (433 ms TTFT) and 0/64 hits (905 ms TTFT)
([vllm#45238](https://github.com/vllm-project/vllm/issues/45238)).

**Feasibility: H.** Self-contained change to one 561-line file plus a config knob;
the existing `run_all_experiments.sh` → `plotting/token_hit_rate.py` harness
measures it unchanged; CPU-only. Well inside 2–4 students × 10 weeks.

**Research value: H.** It re-examines the paper's headline claim under the
assumption that broke it in practice, and either outcome is publishable: if
alignment barely matters, Marconi's result is stronger than stated; if it matters
a lot, the 34.4× is an upper bound and the alignment-aware policy is a genuine
contribution to a live engineering problem.

**Scoop check.** Queries: *"prefix caching Mamba hybrid model SSM state
checkpointing chunk granularity 2026"*, *"arXiv 2026 prefix cache eviction policy
hybrid Mamba attention SSM states admission improve Marconi"*. Result: **partial**.
Closest work: [Sparse Prefix Caching for Hybrid and Recurrent LLM Serving,
arXiv:2605.05219](https://arxiv.org/abs/2605.05219) (Shirokikh & Nikolenko, Apr
2026) stores sparse exact checkpoints and *recomputes the suffix* from the deepest
one, with a DP for checkpoint placement — a different remedy (recompute) for the
same asymmetry, and it does not evaluate Marconi's admission/eviction policies.
[vllm#45238](https://github.com/vllm-project/vllm/issues/45238) and the
[tracking issue vllm#26201](https://github.com/vllm-project/vllm/issues/26201)
document the pathology operationally but propose no policy. No paper re-evaluates
Marconi under aligned checkpointing.

---

### A2 — Branching workloads: the taxonomy's blind spot

**Hypothesis.** We hypothesize that on high-fan-out workloads — self-consistency
sampling, tree-of-thought, best-of-n, and agent trees, where many requests branch
from one shared prefix — Marconi's cap of ≤2 SSM states per sequence and its
"reuse only from the third occurrence" rule cost it substantial token hit rate
versus a **fan-out-adaptive checkpoint budget** that admits *k* states at nodes
whose observed branching factor exceeds a threshold.

**Mechanism.** Marconi hard-codes `num_extra_mamba_states = 2 if branchoff_required
else 1` (`radix_cache_hybrid.py:163`). Replace with a budget derived from each
node's historical child count (the tree already has the information;
`_collect_keystone_nodes` at `radix_cache_hybrid.py:396` enumerates multi-child
nodes). Add a small count-min sketch over prefix hashes so a purely-input prefix
can be admitted on its *second* occurrence when its hash was already seen.
Requires a new branching trace generator: emit *m* sibling requests sharing a
prefix per session, with a configurable fan-out distribution, in the same JSONL
schema as `utils/generate_trace.py` (`session_id`, `turn_id`, `ts`,
`input_tokens`, `output_tokens`).

**Code locations.** `radix_cache_hybrid.py:163`, `radix_cache_hybrid.py:120`
(`insert`), `radix_cache_hybrid.py:396` (`_collect_keystone_nodes`),
`utils/generate_trace.py`, `policy_exploration.py:159` (`generate_configs`).

**Motivating evidence.** §4.1 states the assumption explicitly: Marconi values
only "SSM states that represent the last decoded token between conversation
rounds, **which conversations typically append to, as opposed to branch off
from**" (p. 5). §4.1 Tradeoffs concedes reduced coverage from ≤2 states/sequence.
All three evaluated workloads (Fig. 6, p. 6) are strictly append-structured
multi-turn traces; no branching workload appears anywhere in §5.

**Feasibility: M.** The policy change is small, but a new workload generator and a
new sweep axis are needed, and the fan-out parameterization has to be defended
(ideally derived from a real reasoning trace rather than invented). Still CPU-only.

**Research value: H.** Branching inference is the dominant 2025–26 workload shift,
and it attacks the load-bearing assumption of the paper's admission taxonomy. A
negative result ("append-bias is fine even under fan-out") would also be
informative.

**Scoop check.** Queries: *"prefix caching parallel sampling branching
tree-of-thought reasoning workload KV cache reuse hybrid SSM 2026"*. Result:
**partial**. Closest: [ArborKV: Structure-Aware KV Cache Management for Scaling
Tree-based LLM Reasoning, arXiv:2605.22106](https://arxiv.org/pdf/2605.22106) —
tree-structured reasoning KV management, but Transformer KV only, no recurrent
state and no admission policy for exact-match SSM entries. Nothing found on
branching workloads for hybrid prefix caches.

---

### A3 — Real arrival timestamps: recency is currently measured in request count

**Hypothesis.** We hypothesize that replacing Marconi's logical (request-count)
recency with the **real arrival timestamps already present in every trace record**
changes eviction decisions enough to improve token hit rate under bursty and
heterogeneous arrival — the regime Fig. 13 shows the system is sensitive to — and
that a session-lifetime-aware admission rule (do not admit the last-token state of
a session predicted to be finished) adds a further gain.

**Mechanism.** `utils/generate_trace.py` writes a wall-clock `"ts"` field for every
request (lines 104, 196, 278, 383) and sorts by it, but the simulator **never reads
it**: `policy_exploration.py:107-127` consumes only `input_tokens`,
`output_tokens`, `session_id`, and `RadixCache` increments an integer
`logical_ts` by 1 per operation (`radix_cache_hybrid.py:102-105, 134-135`). The
`use_logical_ts=False` path falls back to `time.time()` — the simulator's own wall
clock, not the trace's. Feed `request["ts"]` in as the node timestamp, recompute
`recency = 1/(current_ts - ts)` (`radix_cache_hybrid.py:535`) in trace-time, and
re-run the α grid search. Then add the session-lifetime predictor and evaluate on
bursty (Poisson/Gamma) inter-session arrivals rather than the uniform
`session_id / sessions_per_second` spacing the generator currently uses.

**Code locations.** `radix_cache_hybrid.py:41` (`TreeNode.last_access_time`),
`radix_cache_hybrid.py:102`, `radix_cache_hybrid.py:510-535` (`evict_v2`
recency), `policy_exploration.py:107`, `utils/generate_trace.py:70`.

**Motivating evidence.** A simplifying assumption the paper never names: under
logical time, a session idle for ten minutes is exactly as "recent" as one idle for
one second, provided the same number of requests passed. Fig. 13 (p. 10) shows the
hit rate *is* sensitive to arrival pattern (48.7 % → 43.0 % as sessions/s goes 0.5
→ 2; 25.9 % → 24.1 % as inter-request time goes 5 s → 10 s), so the ordering that
recency imposes is load-bearing. The generator's uniform session spacing
(`utils/generate_trace.py:70`, `curr_ts = session_id / sessions_per_second`) also
means burstiness was never tested.

**Feasibility: H.** The `use_logical_ts` switch and the timestamp plumbing already
exist; the `ts` field is already in the traces on disk; the existing harness
measures the outcome. Mostly a correctness fix plus one new arrival model.

**Research value: M.** It is a real, unexamined modelling assumption and the
burstiness regime is unexplored, but the likely magnitude is moderate and the
direction is not surprising — this is a solid ablation rather than a new idea.

**Scoop check.** Queries: *"UniCache unifying prefix cache eviction SIGMETRICS
2026"*, *"prefix cache offload SSM recurrent state CPU memory tiering hybrid LLM
serving 2026"*. Result: **partial**. [UniCache: Unifying Prefix Cache Eviction for
Heterogeneous LLM Serving Workloads (SIGMETRICS
'26)](https://jxing.me/pdf/unicache-sigmetrics26.pdf) builds a trace-driven prefix
cache simulator and argues LRU is wrong for heterogeneous mixed workloads — same
spirit, but Transformer KV only, no recurrent state, no FLOP-efficiency term. No
work found that revisits Marconi's timestamp model.

---

### A4 — Does frozen α survive workload drift?

**Hypothesis.** We hypothesize that on non-stationary traces (interleaved
LMSys + SWEBench sessions, or a mid-trace shift in arrival rate / cache pressure)
Marconi's one-shot retrospective α loses a measurable fraction of the gap to the
offline-optimal static-α oracle (V3, already implemented), and that periodic
re-tuning on a sliding window — or a cheap 3-arm shadow-cache bandit over
{0, α̂, 2α̂} — recovers most of that gap at bounded CPU cost.

**Mechanism.** α is tuned exactly once: `evict()` records
`num_reqs_before_eviction` on the first eviction and sets
`bootstrap_window_size = bootstrap_multiplier * num_reqs_before_eviction`
(`radix_cache_hybrid.py:469-472`); when `len(request_history)` reaches it,
`ConfigTuner.tune_config` runs a 21-point parallel replay and the result is frozen
(`radix_cache_hybrid.py:147-155`). The author's own comment at
`radix_cache_hybrid.py:113` marks the continuous-tuning path as "legacy code".
Re-enable a windowed re-tune (reusing `config_tuner.py:13` `replay_trace`),
measure its CPU cost per re-tune against the paper's "few seconds" claim on this
16-core machine, and compare against V3 as the ceiling. Drift traces are produced
by interleaving existing JSONL traces by `ts` — a ~30-line script.

**Code locations.** `config_tuner.py:58` (`tune_config`), `config_tuner.py:13`
(`replay_trace`), `radix_cache_hybrid.py:147`, `radix_cache_hybrid.py:469`,
`policy_exploration.py:159`.

**Motivating evidence.** §4.2 "Managing the balance" (p. 7) describes a single
bootstrap-then-freeze cycle and justifies it by the bootstrap window "capturing a
representative workload sample" — an assumption only valid for the stationary,
single-dataset traces of §5. `args.bootstrap_multiplier` is even dataset-specific
(15 for LMSys, 5 otherwise, `policy_exploration.py:193-194`), which suggests the
tuner is sensitive to workload shape. The V3 oracle exists in the code but its
results "weren't included in the paper" (`artifact_evaluation.md:103`) — the
headroom is therefore unreported.

**Feasibility: H.** The oracle, the replay machinery, and the parallel grid search
are all already written; the work is re-wiring plus a trace-mixing script, all
CPU-only.

**Research value: M.** Adaptive-parameter-under-drift is a well-trodden pattern and
the expected direction is obvious; its value here is quantifying an unreported gap
(V2 vs V3) and the CPU cost of closing it, not a conceptual advance. UniCache
already argues the heterogeneity case for KV-only caches.

**Scoop check.** Queries: as A3, plus *"Marconi prefix caching hybrid LLMs MLSys
2025 follow-up work citing SSM state cache eviction"*. Result: **partial** —
[UniCache (SIGMETRICS '26)](https://jxing.me/pdf/unicache-sigmetrics26.pdf) covers
heterogeneous-workload eviction for Transformer prefix caches;
[Not All Tokens Are Worth Caching, arXiv:2605.18825](https://arxiv.org/html/2605.18825)
does learned/semantic eviction for prefix caches. Neither touches hybrid models or
Marconi's α.

---

### A5 — Validate the TTFT model and the unmeasured checkpointing overhead on real hardware

**Hypothesis.** We hypothesize that when Marconi's TTFT savings are recomputed
from **measured** prefill latencies of a real hybrid model on one A5000 — and
charged for the state-acquisition cost the paper never measures (two-pass prefill,
or chunk-boundary rounding) — the reported P95 TTFT wins over SGLang+ (17.2 % /
12.8 % / 24.7 %, §5.2 p. 9) shrink by a measurable margin, and the P5 regression
(6.3 %, §5.3) grows.

**Mechanism.** The paper's TTFT numbers come from `plotting/ttft.py`, which loads
`data/ttft_AI21-Jamba-1.5-Mini.pickle`, fits a **single global linear regression**
over seqlen (`linear_smooth`, `plotting/ttft.py:33-56`), and applies a
`multiplier = 10` to work around a self-documented unit bug ("accidentally used
1e2 for s to ms conversion instead of 1e3", `plotting/ttft.py:16-17`); lookups are
a step function over profiled seqlens (`get_approximate_ttft`, line 16). Replace
that table with one profiled on this machine: a small hybrid model that fits in
24 GB FP16 (e.g. a Mamba2-Attention hybrid in the 1–3 B class via HF
`transformers`, whose `Mamba2Cache` exposes state save/restore), sweeping prefill
length; separately profile the cost of a two-pass prefill vs a single pass to get a
per-checkpoint overhead. Feed both into a corrected `ttft.py` and re-derive Fig. 9
and Fig. 10b. Also fix the hard-coded SOSP log filenames at
`plotting/ttft.py:218-221` so the figure becomes turn-key.

**Code locations.** `plotting/ttft.py`, `data/ttft_AI21-Jamba-1.5-Mini.pickle`,
`radix_cache_hybrid.py:163` (where the extra checkpoint would be charged),
`utils.py`.

**Motivating evidence.** §4.1 "Obtaining states during prefill" introduces the
two-pass prefill and the chunk rounding as the *only* ways to obtain a mid-sequence
SSM state, then never costs either. Meanwhile the entire latency story rests on a
regression-smoothed lookup from a **different, much larger model** (Jamba-1.5-Mini,
12 B active / 52 B total on 4×A100, §5.1 Models) than the 7B hybrid used for the
hit-rate results — a model/latency mismatch the paper does not discuss. The known
unit bug in the conversion makes independent re-derivation worthwhile on its own.

**Feasibility: M.** Requires real GPU work: choosing a hybrid model with usable
HF/`transformers` state save-restore, writing a profiling harness, and living with
driver 535 / CUDA ≤ 12.2 (no FP8 on Ampere, but FP16 hybrid inference is fine).
A 7B hybrid in FP16 (~14 GB) fits in 24 GB; Jamba-1.5-Mini does not, so the
absolute ms values will differ from the paper and only the *relative* erosion is
comparable. Modest GPU-hours (tens), but real integration risk.

**Research value: H.** It converts the paper's only latency claim from a modelled
number into a measured one and puts a number on the paper's single largest
unquantified cost. Either outcome — overhead is negligible, or it eats a quarter of
the win — is a result a MLSys reviewer would want.

**Scoop check.** Queries: *"arXiv 2026 prefix cache eviction policy hybrid Mamba
attention SSM states admission improve Marconi"*, *"prefix cache offload SSM
recurrent state CPU memory tiering hybrid LLM serving 2026"*. Result: **partial**.
[vllm#37898 "[Hybrid] Marconi-style admission policy for hybrid cache"](https://github.com/vllm-project/vllm/pull/37898)
(merged 2026-06-10) ports Marconi's *admission* idea into vLLM — without the radix
tree and without the FLOP-aware eviction — and reports up to 40 %/66 % latency
improvement on synthetic tests, but it does not measure checkpoint-acquisition
overhead or validate Marconi's TTFT model. The [LMSYS Unified Radix Cache
blog (2026-08-11)](https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/)
describes SGLang's hybrid radix cache but reports no Marconi comparison. Note that
this PR *lowers the risk* of A5 — a reference implementation now exists to read.

---

## 6. Risks and open questions

1. **`environment.yml` pins exact conda build strings** (`environment.yml:7-70`,
   e.g. `libgcc-ng=13.2.0=h77fa898_11`, `python=3.11.9=hb806964_0_cpython`). These
   are routinely removed from conda-forge; the solve may simply fail. Mitigation:
   install the ~10 packages the simulator actually imports by name. Low severity,
   high likelihood.
2. **Traces live on a single Google Drive link** (`artifact_evaluation.md:69`).
   `gdown` is prone to quota errors and the authors already warn about it
   (`artifact_evaluation.md:63-66`). If the link dies, regeneration needs the
   **gated** `meta-llama/Llama-2-7b-hf` tokenizer (`utils/generate_trace.py:12`),
   the **gated** `lmsys/lmsys-chat-1m` dataset, and a hard-coded path
   `/home/ubuntu/SWE-bench-experiments/...` (`utils/generate_trace.py:232`).
   Ungated tokenizer mirrors exist, and ShareGPT + SWE-bench are ungated, but LMSys
   would require accepting HF terms. **Check this link works before committing to
   the paper.**
3. **Runtime is larger than the artifact claims.** `artifact_evaluation.md:16` says
   ~12 h total, but the SWEBench sweep alone is 72 configs × (3 serial runs at
   5–10 min + a 21-way parallel V3 batch). On 16 cores this plausibly runs into
   machine-days. The V3-removal and config-subset scale-down in §4 is not optional.
4. **The artifact is a simulator, and several figures are not turn-key.**
   `plotting/ttft.py:218-221` reads SOSP-era log filenames the sweep never
   produces; `artifact_evaluation.md:113` states that Figs. 10–13 "either do not
   exactly reproduce the figures in the paper … or contain hardcoded numbers
   (handpicked from log files)". Only Figs. 7 and 8 should be treated as
   reproduction targets.
5. **A known FLOP-formula change between submission and camera-ready.**
   `utils.py:104-107` documents that the Mamba FLOP formula "missed a term" in the
   original submission and that camera-ready numbers use the corrected version.
   Any comparison against pre-print numbers must use the current formula.
6. **Apparent bugs to watch for when extending.** `evict_v2` charges bytes using
   `len(node.value)` of the *loop variable* `node` rather than `node_to_evict`
   (`radix_cache_hybrid.py:555`); the MLP savings term subtracts
   `get_attn_flops(seqlen_parent, ...)` from `get_mlp_flops(seqlen_total, ...)`
   (`radix_cache_hybrid.py:526`), mixing layer types; `self.num_nodes` is marked
   "NOTE(ruipan): buggy?" (`radix_cache_hybrid.py:89`). None of these invalidate the
   headline result by inspection, but they will confound any add-on that changes
   the eviction accounting — quantifying their effect is itself a defensible
   contribution.
7. **`evict_v2` is O(tree) per evicted node** — it re-walks the whole tree and
   recomputes every candidate's FLOP efficiency inside the eviction loop
   (`radix_cache_hybrid.py:506-531`). This is why SWEBench traces take 5–10 min.
   Any add-on that increases the number of admitted states will make this worse;
   budget for an incremental/heap-based rewrite if so.
8. **Concurrency is not modelled.** `policy_exploration.py:107` replays requests
   strictly one at a time in trace order; there is no batching, no in-flight
   request set, and no reference counting on cache entries (unlike real vLLM/SGLang,
   which cannot evict a block in use). Claims about behaviour under load should be
   made carefully.
9. **Artifact badges unconfirmed.** A full artifact appendix (§B, p. 15–16), a
   Zenodo DOI (10.5281/zenodo.14970139) and cTuning methodology links are present,
   but I could not find an explicit badge award on the MLSys 2025 poster page or
   the proceedings page. Treat "badged" as unverified.
10. **The field has moved.** Marconi's admission idea is now merged into vLLM
    ([vllm#37898](https://github.com/vllm-project/vllm/pull/37898), 2026-06-10) and
    SGLang has a unified hybrid radix cache
    ([LMSYS blog, 2026-08-11](https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/)),
    and [arXiv:2605.05219](https://arxiv.org/abs/2605.05219) proposes a
    recompute-based alternative. None of these reproduce or falsify Marconi's
    policy comparison, but any add-on must position against them.

---

## 7. Evidence index

**Paper.** Abstract (p. 1); §1 Introduction incl. open-source URL (p. 1–2);
Fig. 1 model architectures (p. 2); Fig. 2 prefix caching / sparse entries (p. 2);
§2.1 SSMs and hybrids (p. 3); §2.2 prefix caching background (p. 3); §3 challenges
+ "SSM State Properties" 1–3 (p. 4); Fig. 3a block reuse 25.0 % vs 0.4 %, Fig. 3b
17.4 GB per 10 K-token sequence (p. 4); §4 design overview + Fig. 4 speculative
insertion (p. 5); §4.1 admission taxonomy, speculative insertion, "Obtaining
states during prefill" (chunked / two-pass), "Tradeoffs" (≤2 states, third
occurrence), "Comparison with SGLang" (p. 5–6); Fig. 5 FLOP efficiency vs seqlen
(p. 6); §4.2 Eq. 1 FLOP efficiency, Eq. 2 utility score, "Managing the balance"
(bootstrap + grid search), "Comparisons with existing size-based eviction
algorithms" (p. 6–7); Fig. 6 sequence-length distributions (p. 6); §4.3
implementation details (1) ≤1-child eviction, (2) ancestor timestamps (p. 7);
§5.1 baselines / metrics / workloads / models / setup (p. 8, read as
`pages/page-08.png`); Fig. 7 token hit rate 4.5×/7.3×/34.4× (p. 8); §5.2 + Fig. 8
SGLang+ comparison, Fig. 9 P95 TTFT (p. 9); §5.3 + Fig. 10 fine-grained analysis
(p. 9); §5.4 + Fig. 11 contention, Fig. 12a/12b layer composition & state dim,
Fig. 13 arrival patterns (p. 10); §6 Related work (p. 10–11); §7 Conclusion
(p. 11); Appendix A.1 + Table 1 FLOP efficiency per layer, Table 2 notation,
Fig. 14 FLOP breakdown (p. 15); Appendix B Artifact Appendix incl. Zenodo DOI,
checklist, dataset sources, per-figure script map (p. 15–16).

**Repository** (all paths relative to `repo/`).
`README.md`;
`artifact_evaluation.md` (lines 16, 29, 32, 63-66, 69, 94, 103, 110-113, 123-125, 129-133);
`environment.yml` (lines 7-70 exact build pins, 72 `torch==2.4.0`, 147 `nvidia-nccl-cu12`);
`run_all_experiments.sh`;
`radix_cache_hybrid.py` (:32 `TreeNode`, :41 `last_access_time`, :69 `RadixCache`,
:80 `use_logical_ts`, :89 "buggy?" note, :102-105 logical clock, :113 "legacy code
for continuous tuning", :120 `insert`, :134-155 α bootstrap hook, :158 speculative
`match_prefix`, :163 `num_extra_mamba_states`, :220 `match_prefix`, :247
`branchoff_required`, :256-261 single-node timestamp update, :269/:346
`evict_policy_version in [1]` SGLang+ branches, :322 `_split_node`, :383
`_collect_leaf_and_single_child_nodes`, :396 `_collect_keystone_nodes`, :417
`_evict_intermediate_node`, :465 `evict`, :469-472 bootstrap window, :484
`evict_v1`, :503 `evict_v2`, :506-531 O(tree) candidate scan, :526 MLP/attn term
mix, :534-546 Eq. 2, :555 `len(node.value)`);
`radix_cache_vllm.py` (:70 block-granular `RadixCache`, :116 `block_size`, :395
LRU-on-leaves `evict`);
`config_tuner.py` (:11 `NUM_CPUS`, :13 `replay_trace`, :58 `tune_config`, :61
21-point α grid, :78 pickle deep-copy, :84 `ProcessPoolExecutor`);
`utils.py` (:2 `_key_match`, :11 `_normalize`, :21/:49/:68 FLOP formulas, :104-107
corrected-formula note, :110/:124 state sizes, :163 `get_flops_efficiency`);
`policy_exploration.py` (:27 `NUM_CPUS`, :29 `TRACE_DIR`, :33 `load_request_trace`,
:53 `run_trace_with_config`, :73-76 admission-strategy → class map, :107-127 replay
loop, :159 `generate_configs`, :162-175 cache-size / arrival sweeps, :193-194
dataset-specific `bootstrap_multiplier`, :196-202 7B hybrid config, :227
`block_size: 32`, :245 V1/V2 runs, :268-316 V3 oracle sweep);
`toy_example.py`;
`utils/generate_trace.py` (:12 Llama-2 tokenizer, :70 uniform session spacing,
:104/:196/:278/:383 `"ts"` emitted, :115/:207/:297/:394 sort by `ts`, :232
hard-coded SWE-bench path, :412-426 generation driver);
`plotting/token_hit_rate.py` (:26 log regex, :68-71 printed improvement ratios,
:118-123 log filenames);
`plotting/sglang_comparison.py`;
`plotting/ttft.py` (:10 sklearn, :16-22 `get_approximate_ttft` + `multiplier = 10`
unit-bug workaround, :33-56 `linear_smooth`, :59 profiled pickle, :218-221
hard-coded SOSP log filenames);
`plotting/plotting.py` (:81, :85, :347 A100-80GB annotation lines — the `big_gpu`
red-flag false positives);
`data/ttft_AI21-Jamba-1.5-Mini.pickle`;
`repo_facts.json`, `fetch_result.json`, `meta.json`.

**External.**
[MLSys 2025 poster page](https://mlsys.org/virtual/2025/poster/3360) (links the
repo as project page; no badge list found);
[proceedings entry](https://proceedings.mlsys.org/paper_files/paper/2025/hash/7c180af017258d239bac6248d1eb26ac-Abstract-Conference.html);
[arXiv:2411.19379](https://arxiv.org/abs/2411.19379);
[vllm#45238 — align-mode Mamba checkpoint kills prefix cache hits](https://github.com/vllm-project/vllm/issues/45238);
[vllm#26201 — tracking issue, prefix caching for hybrid models](https://github.com/vllm-project/vllm/issues/26201);
[vllm#37898 — Marconi-style admission policy for hybrid cache (merged 2026-06-10)](https://github.com/vllm-project/vllm/pull/37898);
[arXiv:2605.05219 — Sparse Prefix Caching for Hybrid and Recurrent LLM Serving](https://arxiv.org/abs/2605.05219);
[arXiv:2605.22106 — ArborKV](https://arxiv.org/pdf/2605.22106);
[arXiv:2605.18825 — Not All Tokens Are Worth Caching](https://arxiv.org/html/2605.18825);
[UniCache, SIGMETRICS '26](https://jxing.me/pdf/unicache-sigmetrics26.pdf);
[LMSYS Unified Radix Cache blog, 2026-08-11](https://www.lmsys.org/blog/2026-08-11-unified-radix-cache/).
