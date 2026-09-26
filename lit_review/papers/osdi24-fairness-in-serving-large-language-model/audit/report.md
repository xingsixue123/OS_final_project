# Fairness in Serving Large Language Models

*(OSDI '24, Sheng et al., UC Berkeley / Stanford / Duke. Desk review only — nothing in this
report was built or executed.)*

## 1. Paper summary

**Problem.** Production LLM services schedule FCFS and bolt on a requests-per-minute (RPM)
cap per client for isolation. FCFS gives no isolation (a client that floods the queue starves
everyone else, `paper.txt:63-76`), and RPM is not work-conserving — it throttles a client even
when the GPU is idle (`paper.txt:77-82`, quantified in Figure 14 / Table 2: RPM(5) throughput
340 tok/s vs 779 tok/s for VTC).

**Why classic fair queueing does not transfer** (§2.3, `paper.txt:358-441`): (i) output length is
unknown before the request finishes, which kills SFQ/WFQ start/finish tags and DRR quanta;
(ii) the cost of an input token ≠ the cost of an output token (prefill parallelizes, decode does
not); (iii) the server's token/s capacity is *not* constant — it depends on how many requests fit
in the KV-cache memory pool, i.e. on the length mix (Figure 2).

**Definition (§3).** Service received by client *f* over `[t1,t2)` is `W_f = h(n_p, n_q)` for a
monotone cost function `h`; the paper mostly uses the linear `w_p·n_p + w_q·n_q` with
`w_p=1, w_q=2` following OpenAI pricing (`paper.txt:1066-1069`). Max–min fairness is then
required in three parts: equal service for backlogged clients, backlogged ≥ non-backlogged, and
work conservation (`paper.txt:550-561`).

**Key idea — Virtual Token Counter (VTC), Algorithm 2 (`paper.txt:628-686`).** Keep one counter
`c_i` per client. On each batch-formation opportunity, repeatedly admit the oldest request of the
client with the smallest `c_i`, charging `w_p · input_len` at admission (line 24); after every
decode step charge `w_q` per client per running request (line 30). When a client re-enters an
empty per-client queue, *lift* its counter to `min{c_i : i ∈ Q}` (lines 12–13) so that idle credit
cannot be hoarded; if the whole queue was empty, lift to the counter of the last client that left
(lines 8–10).

**Theory (§4.1).** Invariant `max_{i∈Q} c_i − min_{i∈Q} c_i ≤ U = max(w_p·L_input, w_q·M)`
(Lemma 4.3) ⇒ `|W_f − W_g| ≤ 2U` for backlogged clients (Theorem 4.4), and `W_f ≥ W_g − 4U`
for a backlogged *f* vs any *g* (Theorem 4.9). Theorem 4.8 shows any non-preemptive
work-conserving scheduler suffers `≥ w_q·M`, so the bound is tight within 2×. `M` = tokens that
fit in a running batch, so the bound scales with the KV-cache pool — confirmed empirically in
Figure 15a. Variants: weighted VTC (§4.3), VTC with length prediction (§4.4 / Algorithm 3).

**Evaluation setup (§5.1, `paper.txt:997-1060`).** Implemented as ~100 LOC on top of S-LoRA
(LightLLM backbone, continuous batching + PagedAttention with block size 1). Baselines: FCFS,
RPM (rate limits 5/10/15/20/30), LCF (VTC minus the counter lift), plus VTC(predict) (mean of the
last five outputs) and VTC(oracle). Main setting: **Llama-2-7b on one A10G (24 GB), KV pool =
10 000 tokens**. Real workload: LMSYS Chatbot Arena trace, one "client" per served model,
27 clients, 210 req/min over 10 min. Ablation: Llama-2-13b on A100 (80 GB), pools of 35 000 and
65 000 tokens.

**Headline numbers.**
- Figure 3a (`pages/page-11.png`): with two backlogged clients (90 and 180 req/min, 256 in /
  256 out), FCFS's accumulated service difference grows roughly linearly to ≈3×10⁵ by t≈500 s,
  while VTC stays flat and small. This is the empirical instantiation of Theorem 4.4.
- Table 2 (`paper.txt:1643-1696`), real trace: max/avg service difference FCFS 759.97 / 433.53,
  LCF 750.49 / 323.82, **VTC 368.40 / 251.66**, VTC(oracle) 329.46 / 227.51, at essentially
  identical throughput (777 / 778 / 779 / 781 tok/s). RPM(5) is fairer (143.86 / 83.58) but at
  340 tok/s — the fairness-vs-throughput dilemma of rate limiting.
- Figure 15 (`paper.txt:1704-1767`): service difference grows with KV pool size (35 000 → 65 000)
  and with request length (256 → 512 → 768, saturating at 512 because the bound `2U` is reached).

**Stated limitations / future work (Appendix C.3, `paper.txt:3179-3231`).** No preemption ("if the
difference in service is larger than a threshold, we can preempt the requests in processing and
swap in requests from clients with lower counters" — explicitly left open); no distributed /
multi-replica counter synchronisation; no interaction with auto-scaling. Appendix C.1
(`paper.txt:2879-2987`) additionally flags the conflict between VTC and cache-aware (prefix-shared)
scheduling as future research. Appendix B.2 says choosing the cost function / pricing model is
"designated for future research" (`paper.txt:2646-2651`).

## 2. Artifact audit

### 2.1 Provenance and shape

- Repo: `https://github.com/Ying1123/VTC-artifact`, head `192c2e2` dated **2024-06-06**
  (`repo_facts.json`). 402 files, 34.9 MB, 19 322 lines of Python + 1 578 lines of `.cuh`.
- **Official**: the paper abstract itself says "The reproducible code is available at
  https://github.com/Ying1123/VTC-artifact" (`paper.txt:48-49`); `Ying1123` is first author Ying
  Sheng. `repo/README.md:1` is titled "VTC Artifact for 'Fairness in Serving Large Language
  Models'". `repo/fair_bench/README.md:1` is headed "Instructions for Artifact Evaluation".
- Badges: I could not fetch the USENIX presentation page (403) and web search returned no badge
  listing. The presence of an AE instruction file is suggestive but **not** proof; recorded as
  "none found".
- Content: this is a **fork of S-LoRA**, so most of the tree is the S-LoRA/LightLLM engine. The VTC
  contribution is the `slora/server/router/*_req_queue.py` family plus `fair_bench/`.

### 2.2 Paper component → code map

| Paper | Code |
|---|---|
| Algorithm 2, VTC (lines 20–26 select, line 24 prefill charge, line 30 decode charge) | `slora/server/router/vtc_req_queue.py` — `generate_new_batch()` (`:104-141`, `min(active_served, key=…)` at `:107`, input charge at `:121-129`), `update_counter()` (`:144-152`) |
| Counter lift (Alg. 2 lines 7–13) | `slora/server/router/vtc_req_queue.py:44-50` |
| Cost function `h` (§3.1 / §4.2) | `linear` branch in `vtc_req_queue.py:121-129`; profiled quadratic `h` of Appendix B.2 in `slora/server/router/req_queue.py:107-110` (`0.21x + 0.101y + 0.00399xy + 0.00325y² + 1.146`); profiling driver `fair_bench/profile_cost_function.py` |
| Weighted VTC (§4.3) | `self.fairw` in `vtc_req_queue.py:28-33`, divisor at `:122-123, :147`; CLI `--fair-weights` (`fair_bench/launch_server.py:17`, `slora/server/api_server.py:370`) |
| Algorithm 3, VTC with length prediction (§4.4) | `slora/server/router/vtc_pred_len_req_queue.py` (last-`window` running mean at `:180-187`); oracle / ±range predictor in `slora/server/router/vtc_oracle_req_queue.py:123-124` |
| FCFS baseline | `slora/server/router/req_queue.py` (`--scheduler slora`) |
| LCF baseline | `slora/server/router/lcf_req_queue.py` |
| RPM baseline (§5.1, Figs 13–14) | `slora/server/router/lshare_req_queue.py` (per-adapter 60-second admission control at `:49-64`) |
| Adapted DRR (Appendix C.2) | `slora/server/router/mdrr_req_queue.py` |
| Scheduler registry | `slora/server/router/manager.py:37-82` |
| `can_add_new_request()` / continuous-batching loop (Alg. 1) | `slora/server/router/manager.py:208-285` (`max_wait_tokens = 10` at `:115`) |
| Workload generators (§5.2 uniform / poisson / on-off / increase / dist-shift) | `fair_bench/trace.py:36-324`; configs in `fair_bench/exp_suite.py:31-252` |
| Real trace (§5.3) | `fair_bench/trace.py:327-401` + bundled `fair_bench/real_trace.pkl`, loaded at `fair_bench/run_exp.py:211-225` |
| Figures 3–10 / 11–14 / 15 | `fair_bench/plot/plot_6.2.py`, `plot_6.2_work_diff.py`, `plot_6.2_shift.py`, `plot_6.3_real.py`, `plot_6.3_calculate_stats_with_abort.py`, `plot_6.4_work_diff.py`, plus per-figure `plot_5.2_*.py` |
| Appendix B revision experiments | `fair_bench/REVISION.md`, `fair_bench/plot/plot_revision.py`, `plot_revision_profile.py` |

### 2.3 Build route on this machine

No Dockerfile and no `requirements.txt` exist in the repo (glob for `Dockerfile*`, `requirements*.txt`,
`*.yml`, `*.yaml` returns nothing), so there is nothing to port. The route is:

1. `conda create -n vtc python=3.10` (3.10, not 3.9: `slora/server/router/manager.py:470` uses the
   single-argument `traceback.format_exception(e)` form, which is 3.10+; `dict[str,int]` annotations
   at `vtc_req_queue.py:92` need ≥3.9).
2. `pip install torch==2.1.2 --index-url .../cu118` (`fair_bench/README.md:5` recommends PyTorch
   2.1.2 + Triton 2.1.0; the top-level `README.md:44` says 1.13–2.0.1 — follow `fair_bench`,
   since `setup.py:64` pins `triton==2.1.0` which ships with torch 2.1.x).
3. `pip install -e .` — builds the CUDA extension `slora._kernels` from
   `slora/csrc/lora_ops.cc` + `slora/csrc/bgmv/*.cu` (`setup.py:28-34`). System `nvcc` 11.8 matches
   the cu118 wheels. The kernels use `nv_bfloat16` (`slora/csrc/lora_ops.cc:111-118`), which needs
   sm_80+ — the A5000 is sm_86, fine. **These kernels are not on the evaluated path**:
   `fair_bench/launch_server.py:34` always passes `--no-lora`, and
   `fair_bench/README.md:205` confirms "LoRA computations have been turned off for a vanilla
   evaluation".
4. Attention/rmsnorm/rotary are pure Triton (`slora/models/llama*/triton_kernel/*.py`); there is
   no dependency on flash-attn, xformers, vLLM or flashinfer (grep over `slora/` finds only
   comments crediting vLLM).

Everything is user-space pip/conda. No root, no kernel module, no eBPF, no `perf`, no Docker,
no KVM.

### 2.4 Dependency pins and their age

`setup.py:53-68`: `aiohttp, einops, fastapi, ninja, packaging, pyzmq, rpyc, safetensors,
transformers, triton==2.1.0, uvloop, uvicorn, psutil`. Only `triton` is pinned. `triton==2.1.0`
(Oct 2023) is the main aging risk — it must be co-installed with torch 2.1.x, and torch 2.1.2+cu118
wheels are still on PyPI. `transformers` is unpinned and is used only for the tokenizer
(`slora/server/tokenizer.py`) and for token counting in `fair_bench/trace.py:329`; a modern
`transformers` may need `AutoTokenizer` compatibility care for the Llama slow/fast tokenizer.
No pin is abandoned or unbuildable.

### 2.5 Data / traces / weights

- **Model weights are not needed.** `fair_bench/launch_server.py:31` always passes `--dummy`;
  `slora/utils/model_utils.py:6-14` then takes the architecture from a hard-coded table
  (`slora/mprophet/model_config.py:49-61`, `llama-7b` = 32 layers / 4096 hidden / 11008 FFN) and
  `slora/models/llama/layer_weights/transformer_layer_weight.py:37-54` fills random tensors. Only
  the **tokenizer** of `huggyllama/llama-7b` is downloaded
  (`slora/server/detokenization/manager.py:26-29`), which is public and non-gated. Prompts are
  `"Hello " * prompt_len` (`fair_bench/trace.py:32-33`), so token content is irrelevant.
- **Synthetic traces** are generated in-process (`fair_bench/trace.py`), no download.
- **Real trace** is bundled: `fair_bench/real_trace.pkl`, loaded at `fair_bench/run_exp.py:213-217`.
  The raw `dummy_chat_conv_20231016.json` is *absent*, but the `.pkl` short-circuits it. Caveat from
  `fair_bench/README.md:207-209`: prompts are masked ("Hello Hello …"), and "We lost the original
  trace file … the current trace file is resampled from a different time range … The plots then look
  different from the ones in the paper. The trends and conclusion are maintained same." So §5.3
  numbers (Figures 12–14, Table 2) are **not** bit-reproducible; §5.2 synthetic figures are.
- Ground-truth result files from the authors' own runs are committed
  (`fair_bench/all_results_overload.jsonl`, `all_results_poisson_short_long.jsonl`, …), so a team can
  diff their runs against the authors' before touching anything.

### 2.6 Eval scripts

Present and per-figure explicit. `fair_bench/README.md:14-199` gives, for each of Figures 3–15,
the exact `launch_server.py` + `run_exp.py --suite … --output …` pair, the wall-clock cost for the
slow ones ("around 25 mins", "around 30 mins", "around 18 mins"), and the output PDF path.
`fair_bench/REVISION.md` covers the Appendix B variants. Plot scripts read the `jsonl` files and
also emit the LaTeX fairness tables (`plot_6.2_work_diff.py:114-134`).

One numbering wrinkle: the AE README labels figures by the arXiv numbering (its "Figure 14" is the
USENIX Figure 15, its "Figure 11/12/13" are USENIX 12/13/14), and the plot filenames say `sec6.2`
where the USENIX paper says §5.2. Cosmetic, but worth knowing before hunting for a missing script.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | Paper abstract names the repo (`paper.txt:48-49`); owner `Ying1123` is the first author; `repo/README.md:1` and `repo/fair_bench/README.md:1` identify it as the VTC artifact / AE instructions. It contains the real system, not a stub: the scheduler family `slora/server/router/{vtc,vtc_pred_len,vtc_oracle,vtc_max,lcf,mdrr,lshare}_req_queue.py`, the full serving engine (`slora/`, 19 k LOC Python + CUDA/Triton kernels), the workload generators (`fair_bench/trace.py`) and all plot scripts (`fair_bench/plot/`). |
| `H2_no_root` | **pass** | Pure user-space: `pip install -e .` (`setup.py`) builds one CUDA extension with the system `nvcc`; server is a FastAPI/uvicorn process binding `127.0.0.1:8000` (`slora/server/api_server.py:325-326`) with zmq on localhost ports (`slora/server/router/manager.py:119-122`). No Dockerfile/compose file in the tree. `repo_facts.json` red flags list only `big_gpu` and `multi_gpu` — no sudo, kernel-module, eBPF, perf, KVM, RDMA or CXL hits. `--tp` defaults to 1 (`slora/server/api_server.py:341`), so the S-LoRA tensor-parallel path is never entered. |
| `H3_hardware_fit` | **pass** (with one noted gap) | The headline setting is *one* A10G 24 GB, Llama-2-7b, KV pool 10 000 tokens (`paper.txt:1040-1042`, `fair_bench/README.md:4,15`) — the A5000 is the same class (Ampere, 24 GB, sm_86 vs sm_86/sm_80 for A10G), and dummy fp16 7B weights (~13.5 GB) + 10 000-token KV pool (32 layers × 2 × 4096 × 2 B × 10 000 ≈ 5.2 GB) ≈ 19 GB < 24 GB. Repo size 34.9 MB and no weight download ⇒ disk is a non-issue vs ~257 GB free. **Gap**: the §5.4 ablation (Figure 15) uses Llama-2-13b on A100 80 GB with pools of 35 000/65 000 tokens (`fair_bench/README.md:167-192`, suites `overload-s4-*` in `fair_bench/exp_suite.py:87-163`); 13B fp16 ≈ 26 GB does not fit in 24 GB. That ablation needs a scale-down to the 7B model with two pool sizes (e.g. 6 000 vs 12 000), which still tests the claim "service difference grows with `M`". Everything in §5.2 and §5.3 runs at paper scale. |
| `H4_obtainable_deps_data` | **pass** | Deps are all pip/conda-installable (`setup.py:53-68`); nothing needs a system package. No model weights are downloaded at all — `--dummy` synthesises them (`fair_bench/launch_server.py:31`, `slora/models/llama/layer_weights/transformer_layer_weight.py:37-54`); only the public, non-gated `huggyllama/llama-7b` tokenizer is fetched (`slora/server/detokenization/manager.py:29`). Synthetic traces are generated locally (`fair_bench/trace.py`); the real LMSYS trace is committed as `fair_bench/real_trace.pkl` (`fair_bench/run_exp.py:213-217`). No proprietary data. |

## 4. Reproduction plan

**Target.** **Figure 3a** (`pages/page-11.png`; caption at `paper.txt:1147-1153`): "Absolute
Difference in Service" over time for two continuously backlogged clients (90 vs 180 req/min,
256 input / 256 output tokens), VTC vs FCFS. The claim it supports is Theorem 4.4 — VTC's
accumulated service difference stays bounded and independent of the interval length, while FCFS's
grows without bound (to ≈3×10⁵ by t≈500 s). Secondary target, free with the same runs: the
`{overload}_quant_fairness.tex` table emitted by `plot_6.2_work_diff.py:114-134`, which is the
synthetic analogue of Table 2.

**Scale-down.** *None required.* Run exactly the AE recipe: Llama-7b dummy weights on the single
A5000 24 GB, `--num-token 10000`, suite `overload` (2 clients, req_rate `[1.5, 3]`/s, duration
6 min, in/out 256 — `fair_bench/exp_suite.py:54-64`). If the A5000's throughput differs enough from
the A10G's that client 1 is no longer backlogged, lower `--num-token` to 8000 or raise both
`req_rate` entries — both clients only need to exceed capacity, which is exactly what the figure
assumes. For the §5.4 ablation, substitute 7B with pools {6000, 12000} for the S4/A100 pools
{35000, 65000}.

**Steps.**
1. `conda create -n vtc python=3.10`; `pip install torch==2.1.2` (cu118); `pip install -e .`
   (compiles `slora._kernels`; ~10 min on 16 cores). Set `HF_HOME` under `$HOME`.
2. Smoke test: `cd fair_bench && python launch_server.py` then
   `python run_exp.py --debug --suite default` (1-minute debug suite,
   `fair_bench/exp_suite.py:256-266`).
3. VTC run: `python launch_server.py` (defaults to `--scheduler vtc_fair`, `--num-token 10000`) then
   `python run_exp.py --suite overload --output VTC/all_results_overload.jsonl` (~25 min per
   `fair_bench/README.md:22`).
4. FCFS run: restart with `python launch_server.py --scheduler slora`, then
   `python run_exp.py --suite overload --output FCFS/all_results_overload.jsonl` (~25 min).
5. `cd plot && python plot_6.2_work_diff.py` → `sec6.2_overload_acc_service_diff.pdf`; and
   `python plot_6.2.py` → per-client service-rate curves (Figure 3b).
6. Cross-check against the authors' committed run
   `fair_bench/all_results_overload.jsonl` before drawing conclusions.

**Effort.** ≈3 person-days (1 for the environment + CUDA-extension build, 1 for the two runs plus
the plotting/numbering archaeology, 1 of slack for the Triton 2.1 / transformers pin) + ≈2 GPU-hours
for Figure 3 (2 × 25 min plus retries). Adding all of §5.2 (Figures 3–10, both schedulers) is
roughly +6 GPU-hours; the real-trace §5.3 sweep (VTC, FCFS, LCF, RPM×4) is a further ≈9 GPU-hours
at 10 min per run plus server restarts.

**Level: H.** Per-figure commands with stated runtimes exist (`fair_bench/README.md`), the plot
scripts are committed, the authors' own result `jsonl` files are committed for diffing, the target
hardware class is identical (24 GB Ampere), and no model weights or external datasets are needed.
The only real risks are packaging (torch 2.1.2 + triton 2.1.0 + a modern `transformers`) and a
throughput offset A10G→A5000 that may need a `--num-token` nudge — both ordinary porting, not
blockers. Note the caveat that the §5.3 *real-trace* numbers are explicitly **not** expected to
match the paper (`fair_bench/README.md:207-209`), so Figure 3a (synthetic) is the right target.

## 5. Add-on ideas

### AO1 — Preemptive VTC with a deficit threshold

**Hypothesis.** We hypothesize that adding bounded-deficit preemption (evict the newest running
request of the highest-counter client whenever `max_i c_i − min_i c_i > θ·U`, refund its
uncharged output cost, and re-admit it later by recompute) reduces the max and average service
difference by ≥2× under backlogged long-request workloads, at <10% aggregate throughput loss,
compared with non-preemptive VTC.

**Mechanism.** Add a `select_preemption_victims(current_batch)` method to `VTCReqQueue` returning
the request ids to evict, called from the router loop right before
`generate_new_batch`. The router already has the machinery: `_filter_batch()`
(`manager.py:321-325`) drives `InferBatch.filter()` (`model_infer/infer_batch.py:142`), which frees
the victim's KV slots through `MemoryManager.free`; a preempted `Req` is pushed back to the *head*
of `self.user_req_list[adapter_dir]` with its `output_ids` reset (recompute policy) or retained
(swap policy, using the engine's existing `--swap` path). Counters are adjusted by subtracting
`w_q · len(output_ids)` for the discarded tokens under recompute, so that the client is not charged
for work that will be redone. Expose `θ` as a CLI flag alongside `--cost-func`.

**Code locations.** `slora/server/router/vtc_req_queue.py`, `slora/server/router/manager.py`,
`slora/server/router/model_infer/infer_batch.py`,
`slora/server/router/model_infer/model_rpc.py`, `fair_bench/exp_suite.py`.

**Motivating evidence.** Appendix C.3 "Preemption" (`paper.txt:3181-3206`) proposes precisely this
and calls it future work; Remark 4.7 (`paper.txt:785-793`) states the fairness-vs-work-conservation
trade-off; Theorem 4.8 (`paper.txt:800-808`) only lower-bounds *non-preemptive* schedulers, so a
preemptive one is allowed to beat `w_q·M`; Figure 15b (`paper.txt:1704-1767`) shows the discrepancy
growing with request length until the bound saturates — exactly the regime preemption should fix.

**Feasibility: M.** The scheduling logic is small, but it is cross-cutting: it touches the queue,
the async router loop, the RPC boundary and the per-rank `InferBatch`, and correctness under
concurrent prefill/decode is fiddly. Evaluation reuses the existing harness and fits in ~10 GPU-hours
(θ sweep × {overload, poisson_short_long_2, real}).
**Research value: H.** It is the paper's own top-listed open question, the theory says something
non-trivial is at stake (the 2× tightness result does not apply), and either outcome is informative —
if the throughput cost of recompute swamps the fairness gain, that is itself a result reviewers of
the original venue would want.
**Scoop check: partial.** Queries: "VTC fairness LLM serving preemption tighter bound", "preemption
fair scheduling LLM serving KV cache fairness bound". Closest work:
[FastSwitch (arXiv 2411.18424)](https://arxiv.org/abs/2411.18424) — optimises *context-switching
efficiency* (I/O utilisation, KV-cache granularity, multi-turn retransmission) for fairness-aware
serving on vLLM, i.e. it makes preemption cheap but does not study the fairness-bound /
work-conservation trade-off curve that VTC's Theorems 4.4/4.8 frame. Also related:
[FairBatching (arXiv 2510.14392)](https://arxiv.org/abs/2510.14392), which is about prefill-vs-decode
resource fairness, not inter-client bounds. A project here must position against FastSwitch
explicitly and should probably adopt its swap mechanics as a baseline.

### AO2 — KV-cache-occupancy (memory-time) service cost

**Hypothesis.** We hypothesize that charging clients for KV-cache *occupancy over time*
(token·seconds resident) in addition to tokens processed improves aggregate throughput and the p95
first-token latency of short-context clients at equal measured service difference, compared with the
paper's linear and profiled cost functions, under a workload mixing long-context and short-context
clients.

**Mechanism.** Add a third branch `"memtime"` to the `cost_func` dispatch. Where `"linear"` adds
`w_q` per running request per decode step (`vtc_req_queue.py:146-147`), `"memtime"` adds
`w_q + λ·(req.input_len + len(req.output_ids))` — i.e. a charge proportional to the KV footprint the
request is holding, accrued every step it stays resident. This makes the counter a *memory-time*
account rather than a token account, which is the LLM-serving analogue of dominant-resource
fairness. Wire the new option through `get_scheduler` and the two CLIs, and add a mixed-context
suite (e.g. client A: 64/64, client B: 768/768, both backlogged) to `exp_suite.py`.

**Code locations.** `slora/server/router/req_queue.py`, `slora/server/router/vtc_req_queue.py`,
`slora/server/router/vtc_oracle_req_queue.py`, `slora/server/router/manager.py`,
`fair_bench/launch_server.py`, `fair_bench/exp_suite.py`.

**Motivating evidence.** §3.1 concedes that neither token counts nor FLOPs "accurately reflect the
actual LLM serving cost" (`paper.txt:509-514`); Appendix B.2 explicitly defers the choice of cost
function ("our goal is not to determine the optimal cost function or pricing model … designated for
future research", `paper.txt:2645-2651`); §2.3 explains that capacity varies precisely because long
contexts consume the memory pool (`paper.txt:378-390`, Figure 2). Yet the profiled `h(n_p,n_q)` in
`req_queue.py:107-110` charges only at token-production time, so a request that sits in the batch
holding 768 KV slots while producing one token per step is charged the same as a 64-token request —
the externality the paper itself identifies is never billed.

**Feasibility: H.** Localised: one new branch in two or three queue classes (<300 LOC), a new
workload suite, and reuse of `plot_6.2_work_diff.py` for the metric. Fits the machine; ≈4 GPU-hours.
**Research value: M.** It is a natural and fairly expected refinement — most reviewers would guess
the direction of the result — but quantifying the throughput/fairness Pareto curve across three cost
functions on the same harness is a solid contribution, and the paper explicitly left the question
open.
**Scoop check: partial.** Queries: "multi-resource fairness LLM serving KV cache occupancy dominant
resource fairness 2025", "memory-time fair share LLM serving".
[Equinox (arXiv 2508.16646)](https://arxiv.org/abs/2508.16646) adds a "Resource Fairness Counter"
measuring throughput and GPU utilisation alongside a user counter, and reports 1.3× throughput /
13% fairness over VTC — overlapping in spirit but not the same construction (Equinox's counter is
prediction-driven and operator-facing; this add-on is a memory-time billing term inside VTC's own
cost function). A project must baseline against Equinox's stated numbers or explain why it cannot.

### AO3 — Sybil-resilient hierarchical VTC (client-identity splitting and rotation)

**Hypothesis.** We hypothesize that a tenant that splits its traffic across `k` client identities
obtains `≈k/(n+k−1)` of server capacity under VTC instead of `1/n` — breaking the isolation property
of §3.2 — and that a two-level hierarchical VTC (tenant counter over per-identity sub-counters)
restores the `1/n` share with <5% throughput loss and no degradation of the Theorem 4.4 bound among
honest tenants.

**Mechanism.** (a) *Attack*: extend `fair_bench/trace.py` with a generator that emits one logical
client's request stream under `k` distinct `adapter_dir` labels (the harness already lets the client
choose its own identity — `run_exp.py:59-70` puts `lora_dir` in the request body, and
`VTCReqQueue.append` (`:38-41`) creates a fresh counter for any unseen label). A second variant
*rotates* identities: because the counter lift at `vtc_req_queue.py:44-50` sets a newcomer's counter
to `min{c_i}` over active clients, a client that retires an identity and registers a fresh one resets
its accumulated debt to the minimum. (b) *Defence*: `HVTCReqQueue` maintaining
`tenant_served[t]` and `served[client]`; selection picks `argmin_t tenant_served[t]`, then
`argmin_{c ∈ t}` within it; both levels charged on admission and per decode step; the lift applied
at both levels. Register it in `get_scheduler`.

**Code locations.** `slora/server/router/vtc_req_queue.py`, `slora/server/router/manager.py`,
`fair_bench/trace.py`, `fair_bench/exp_suite.py`, `fair_bench/launch_server.py`,
`fair_bench/plot/plot_6.2_work_diff.py`.

**Motivating evidence.** The paper's guarantees are all stated *per client* and are explicitly
functions of `n`: Theorem 4.11's latency bound is `2(n−1)U/a` (`paper.txt:857-864`) and Theorem 4.13
requires a client to stay under `T/n − 5U` (`paper.txt:875-885`). §3.2 claims "a misbehaving client
cannot deny the service to other clients, **no matter how many requests it sends**"
(`paper.txt:546-548`) — which says nothing about how many *identities* it uses. Appendix C.3 mentions
hierarchical fair sharing only for the distributed multi-replica case (`paper.txt:3207-3219`), never
as an anti-abuse mechanism. In the artifact, client identity is entirely client-supplied, so the
attack is a one-line change to the load generator.

**Feasibility: H.** Both the attack workload and the hierarchical queue are small, self-contained
changes (<500 LOC total) on top of an existing, per-figure evaluation harness; ≈4 GPU-hours for an
`n`×`k` sweep on the `overload` and `real` suites. Clearly inside 10 weeks for 2–4 students.
**Research value: H.** It attacks the load-bearing mechanism of an OSDI paper (the counter lift) in a
regime the paper never considers, and both outcomes teach something: either the attack is devastating
and the hierarchical fix is necessary, or the counter lift turns out to be more robust than it looks
and the paper's isolation claim survives with a sharper statement. The caveat — which should be
stated honestly in the write-up — is that per-flow-vs-per-aggregate gaming is a known issue in
packet fair queueing, so the novelty is the LLM-serving instantiation and the measurement, not the
concept.
**Scoop check: clear.** Queries: "sybil identity splitting gaming fair queueing LLM serving VTC
multi-tenant hierarchical", "strategic clients fair LLM serving abuse". Nothing found that studies
identity manipulation against VTC or any LLM-serving fair scheduler; the only Sybil hits were
blockchain-consensus papers. The closest adjacent work,
[Locality-aware Fair Scheduling / DLPM (arXiv 2501.14312)](https://arxiv.org/abs/2501.14312) by the
same group, changes the *ordering* policy (prefix locality) and keeps the per-client identity model
unchanged.

### AO4 — Predictor poisoning in VTC-with-length-prediction, and a conservative predictor

**Hypothesis.** We hypothesize that a client which shapes its own output-length pattern (a burst of
very short requests followed by long ones) inflates its received service under VTC(predict) relative
to plain VTC by a measurable margin, and that replacing the running mean with a high-quantile
(pessimistic) estimator removes most of that gain while retaining the bulk of VTC(predict)'s
service-discrepancy reduction.

**Mechanism.** The shipped predictor is a per-client exponentially-weighted mean of that client's own
recent output lengths (`vtc_pred_len_req_queue.py:180-187`), and the predicted cost is charged
up-front at admission (`:126-136`) then reconciled downward on completion (`:167-178`). Because the
client controls `max_new_tokens` (`run_exp.py:66`, with `ignore_eos: True`), it controls its own
predictor. (a) Add an adversarial generator to `fair_bench/trace.py` that alternates short-burst and
long-burst phases per client with a tunable period. (b) Replace the mean with a windowed
`q`-quantile over the last `W` completions (and optionally a "no refund on over-prediction" variant),
exposed as CLI knobs. Measure received service, max/avg service difference and throughput for
{VTC, VTC(predict), VTC(quantile), VTC(oracle)} — the same four-way comparison as Tables 5–6.

**Code locations.** `slora/server/router/vtc_pred_len_req_queue.py`,
`slora/server/router/vtc_oracle_req_queue.py`, `slora/server/router/manager.py`,
`fair_bench/trace.py`, `fair_bench/exp_suite.py`, `fair_bench/REVISION.md`.

**Motivating evidence.** §4.4 (`paper.txt:962-988`) motivates prediction purely as a variance
reducer and notes "the effectiveness of the length predictor is contingent upon both the workload and
the accuracy of predictions", but every evaluation of it (Figure 19, Tables 5–6,
`paper.txt:2744-2782`) uses stationary per-client length distributions or a synthetic ±50% error
model — never an adversarial or shifting one. §5.2's "distribution shift" experiment (Figure 10)
shifts *rates*, not *lengths*, and is run against plain VTC/LCF. The paper's own Theorem 4.8 says the
worst case does not improve with prediction, so the prediction variant is a purely heuristic average-
case gain whose robustness is untested.

**Feasibility: H.** Both the adversarial generator and the quantile predictor are small, localised
edits to files that already exist and are wired into the CLI; the AE `REVISION.md` recipe already
runs exactly this four-way comparison, so the harness needs only a new suite. ≈4 GPU-hours.
**Research value: M.** It is a narrow but real robustness question about a component the paper ships
and recommends, and the finding generalises to every prediction-based fair scheduler. It is not a new
mechanism, which caps its interest.
**Scoop check: partial.** Queries: "output length prediction fairness scheduler VTC service
discrepancy learned predictor", "uncertainty-aware output length prediction LLM scheduling".
[Equinox (arXiv 2508.16646)](https://arxiv.org/abs/2508.16646) replaces VTC's naive predictor with a
mixture-of-prediction-experts framework (L1 error on output tokens 80 → 33) for fairness scheduling —
so "better predictor for fair scheduling" is taken; the *adversarial/self-poisoning* angle and the
conservative-quantile defence are not, and Equinox's predictor would be subject to the same attack.
[Uncertainty-aware output length prediction (arXiv 2604.00499)](https://arxiv.org/abs/2604.00499)
targets SJF-style scheduling, not fairness.

## 6. Risks and open questions

1. **Implementation deviates from Algorithm 2 in the whole-system-idle case.**
   `VTCReqQueue.append` (`vtc_req_queue.py:44-50`) implements only the "`Q ≠ ∅`" branch of the
   counter lift (Alg. 2 lines 11–13). Lines 8–10 — "if `Q = ∅`, let `l` be the last client that left
   `Q`, set `c_u ← max{c_u, c_l}`" (`paper.txt:640-646`) — have no counterpart: when no other client
   has a non-empty per-client deque, `cnts` is empty and **no lift happens at all**. This matters for
   the ON/OFF and dist-shift experiments (Figures 5, 6, 10) where the system can drain. A reproduction
   should check whether the shipped behaviour still yields the paper's plots, and whether restoring
   lines 8–10 changes them — this is a good Contemporary-track finding and a prerequisite for AO3
   (the rotation attack exploits the same code path).
2. **Per-client state is never reclaimed.** `self.served` and `self.user_req_list`
   (`vtc_req_queue.py:21-22, 38-43`) grow monotonically with the number of distinct
   `adapter_dir` labels, and `generate_new_batch` copies the whole `served` dict on every
   batch-formation opportunity (`:103`). Fine at 2–27 clients, a scalability concern for AO3's
   `k`-identity sweeps; worth measuring scheduler overhead per iteration.
3. **Real-trace results are not bit-reproducible by the authors' own admission.**
   `fair_bench/README.md:207-209` states the original Chatbot Arena trace was lost and the bundled
   `real_trace.pkl` is resampled from a different period, so Table 2, Figures 12–14 will differ.
   Any claim about §5.3 must be phrased as trend-level.
4. **Dependency archaeology.** `triton==2.1.0` (`setup.py:64`) pins the stack to torch 2.1.x/cu118.
   The top-level `README.md:44` ("1.13 ≤ PyTorch ≤ 2.0.1") contradicts
   `fair_bench/README.md:5` ("PyTorch 2.1.2"); the `fair_bench` number is the one to trust for the
   VTC experiments. An unpinned modern `transformers` may break the Llama tokenizer path
   (`slora/server/tokenizer.py`, `fair_bench/trace.py:329`). None of this is fatal, but it is the
   most likely place the first week is spent.
5. **Python version floor is higher than advertised.** `setup.py:52` says `>=3.9`, but
   `manager.py:470` uses `traceback.format_exception(e)` (3.10+). Only on the error path, so it will
   bite exactly when something else has already gone wrong.
6. **Throughput offset A5000 vs A10G.** The synthetic suites hard-code request rates chosen so that
   clients are backlogged on an A10G (`exp_suite.py:54-64` etc.). If the A5000 is materially faster,
   "backlogged" may no longer hold and Figure 3a's premise breaks. Mitigation: verify from the
   server log ("current batch size … token used ratio", `manager.py:201`) that the queue never
   drains, and adjust `--num-token` or `req_rate` if it does.
7. **Figure numbering drift** between the arXiv version the artifact was written against and the
   USENIX version used here (AE "Figure 14" = USENIX Figure 15; plot files say `sec6.2` where the
   paper says §5.2). Cheap to trip over.
8. **Crowded follow-up space.** Since 2024 the area has filled in fast: DLPM (locality + fairness,
   same group), FastSwitch (preemption efficiency), Equinox (prediction + resource counters),
   FairBatching (prefill/decode fairness). Any add-on must be positioned against these; the two
   ideas I judged least covered are AO3 (identity manipulation) and AO4's adversarial angle.
9. **Ablation scale-down changes the quantity being varied.** Figure 15's message is "the bound
   scales with `M`". Reproducing it at 7B with pools {6000, 12000} instead of 13B with
   {35000, 65000} preserves the qualitative claim but not the absolute numbers — say so explicitly
   rather than presenting it as a match.

## 7. Evidence index

**Paper** (`paper.txt`, line numbers; page images where cited):
- Abstract / repo URL: `:25-49`
- Intro, FCFS and RPM drawbacks: `:63-92`
- Continuous batching, Algorithm 1: `:209-277`
- Existing fairness approaches (RPM, fair queueing, CFS): `:278-357`
- §2.3 challenges (unknown length, variable token cost, variable capacity), Figure 2: `:358-441`
- §3.1 measurement of service (tokens / FLOPs / weighted tokens / custom `h`): `:489-535`
- §3.2 max-min fairness properties: `:536-585`
- §4.1 Algorithm 2 (VTC) pseudocode: `:628-686`
- Lemma 4.3, Theorem 4.4, Remark 4.7, Theorem 4.8: `:748-816`
- Theorems 4.9 / 4.11 / 4.13 (non-backlogged, latency, non-overloaded): `:822-885`
- §4.2 adapting to other cost functions: `:886-921`
- §4.3 weighted VTC: `:922-961`
- §4.4 VTC with length prediction: `:962-988`
- §5.1 setup, implementation on S-LoRA, baselines, metrics: `:989-1097`
- Figure 3 (target) caption + Figure 4: `:1119-1193`; rendered page `pages/page-11.png`
- Figures 5–10 (ON/OFF, poisson short/long, isolation, dist shift): `:1194-1456`
- §5.3 real workload, Figures 11–14, Table 2: `:1507-1701`
- §5.4 ablation, Figure 15: `:1702-1767`
- Appendix B.1 weighted VTC, B.2 profiled cost function + fitted `h`: `:2514-2600`
- Appendix B.3 length prediction, Algorithm 3, Tables 5–6: `:2737-2782`, `:2997-3069`
- Appendix C.1 general VTC, conflict with cache-aware scheduling: `:2783-2987`
- Appendix C.2 adapted DRR: `:2988-3178`
- Appendix C.3 future work (preemption, distributed, auto-scaling): `:3179-3231`

**Repository** (paths relative to `repo/`):
- `README.md` (S-LoRA fork, requirements, install), `setup.py` (deps, CUDA extension)
- `fair_bench/README.md` (AE instructions, per-figure commands, trace caveats),
  `fair_bench/REVISION.md` (Appendix B recipes)
- `fair_bench/launch_server.py`, `fair_bench/run_exp.py`, `fair_bench/exp_suite.py`,
  `fair_bench/trace.py`, `fair_bench/real_trace.pkl`, `fair_bench/profile_cost_function.py`,
  `fair_bench/run.sh`, `fair_bench/cost_profile.json`
- `fair_bench/plot/plot_6.2.py`, `plot_6.2_work_diff.py`, `plot_6.2_shift.py`, `plot_6.3_real.py`,
  `plot_6.3_calculate_stats_with_abort.py`, `plot_6.4_work_diff.py`, `plot_revision.py`,
  `plot_revision_profile.py`, `visualize.py`
- `slora/server/router/vtc_req_queue.py`, `vtc_pred_len_req_queue.py`, `vtc_oracle_req_queue.py`,
  `vtc_max_req_queue.py`, `lcf_req_queue.py`, `lshare_req_queue.py`, `mdrr_req_queue.py`,
  `req_queue.py`, `abort_req_queue.py`, `manager.py`
- `slora/server/router/model_infer/infer_batch.py`, `model_rpc.py`
- `slora/server/api_server.py`, `slora/server/io_struct.py`,
  `slora/server/detokenization/manager.py`
- `slora/utils/model_utils.py`, `slora/mprophet/model_config.py`,
  `slora/models/llama/layer_weights/transformer_layer_weight.py`
- `slora/common/mem_manager.py`, `slora/common/mem_allocator.py`
- `slora/csrc/lora_ops.cc`, `slora/csrc/bgmv/`
- `slora/models/llama/triton_kernel/`, `slora/models/llama2/triton_kernel/`

**Driver facts / provenance**: `repo_facts.json` (head commit `192c2e2`, 2024-06-06; red flags
`big_gpu`, `multi_gpu` only), `fetch_result.json`, `meta.json`.

**Web (scoop check and provenance)**:
- [Fairness in Serving Large Language Models — USENIX OSDI '24](https://www.usenix.org/conference/osdi24/presentation/sheng) (page returned 403 to the fetcher; no badge info obtained)
- [arXiv 2401.00588 — Fairness in Serving Large Language Models](https://arxiv.org/abs/2401.00588)
- [arXiv 2501.14312 — Locality-aware Fair Scheduling in LLM Serving (DLPM/D²LPM)](https://arxiv.org/abs/2501.14312)
- [arXiv 2411.18424 — FastSwitch: Context Switching Efficiency in Fairness-aware LLM Serving](https://arxiv.org/abs/2411.18424)
- [arXiv 2508.16646 — Equinox: Holistic Fair Scheduling in Serving LLMs](https://arxiv.org/abs/2508.16646)
- [arXiv 2510.14392 — FairBatching: Fairness-Aware Batch Formation for LLM Inference](https://arxiv.org/abs/2510.14392)
- [arXiv 2606.09061 — Fairness-Aware and Latency-Controllable Scheduling for Chunked-Prefill LLM Serving](https://arxiv.org/abs/2606.09061)
- [arXiv 2604.00499 — Scheduling LLM Inference with Uncertainty-Aware Output Length Predictions](https://arxiv.org/abs/2604.00499)
