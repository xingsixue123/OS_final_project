# MorphServe: Efficient and Workload-Aware LLM Serving via Runtime Quantized Layer Swapping and KV Cache Resizing

**Bottom line up front:** the paper is a good fit for the course on every axis except the
one that is non-negotiable. The official repository
(https://github.com/ds2-lab/MorphServe, cloned at `repo/`) contains exactly two files —
`LICENSE` and `README.md` — and the README states *"We are currently preparing the
codebase for public release … The full code will be released soon."* There is no
implementation to build on, so `H1_open_repo` fails and the paper is a **reject** under
the rubric. The rest of this report records what would be true *if* the code appeared,
so the paper can be re-audited cheaply later.

## 1. Paper summary

**Problem.** Production LLM workloads are bursty (paper §3, Figure 1a, using the Azure
LLM Inference 2023 trace and BurstGPT). A fixed-precision serving engine such as vLLM
hits a *saturation point* — the load at which GPU memory can no longer admit a new
prefill or continue an in-flight decode — after which TTFT spikes and the 2 s TTFT SLO is
violated (§3, Figure 1b). The obvious fix, static quantization (AWQ INT4), pays accuracy
for efficiency *all the time*, including during idle periods (§3, Figure 1c).

**Key idea.** Make weight precision and KV-cache capacity into *runtime, reversible*
control knobs. Under memory pressure, swap selected FP16 decoder layers for pre-quantized
INT4/INT8 copies, and hand the freed GPU memory to the paged KV allocator as extra
blocks. Reverse both when pressure subsides. Adaptation is mid-inference and
state-preserving: no model flush, no re-prefill, no scheduler restart (§4.1, "State-
Preserving Morphing During Inference"). Granularity is token-level — within one request,
early tokens can be FP16 and later tokens mixed-precision (§4.1, illustrated verbatim in
Appendix B.1).

**Design** (§4, Figure 2 on p.4):
- *Serving Monitor* — collects GPU memory utilization, queue depth, throughput,
  TTFT/TPOT, smoothed over short windows.
- *Morphing Controller* — global memory manager; fires when user thresholds are crossed
  (the paper's examples: KV memory > 85 %, queueing delay > 100 ms) (§4.1).
- *Morphing Executor* — per-worker; runs `LayerSwapper` and `KVResizer`.
- *Offline profiling* (§4.2, Appendix A) — a **Layer Importance Score**
  `LIS_p = α1·LTS_p + α2·LRS_p + β·MDS_p` (Eq. 5), with α1=α2=0.25, β=0.5, built by the
  greedy Algorithm 1 (Appendix A.2) on a WikiText-2 calibration subset. Notably, Table 8
  shows LIS barely beats a plain Front-to-Back order, and §A.3 admits MorphServe
  *defaults to Front-to-Back* when profiling is unavailable.
- *LayerSwapper* (§4.3) — all layer variants (FP16/W8/W4) preloaded in pinned host DRAM,
  kernels precompiled on dummy data, GPU regions preallocated so a swap is a single
  `cudaMemcpyAsync` into the same addresses (no pointer remapping). Quoted cost: ~4 ms
  PCIe transfer for an INT4 Llama-2-7B layer, ~6 ms end-to-end, overlapped with decode.
- *KVResizer* (§4.4, Appendix C) — extends PagedAttention with custom **Triton** kernels
  for dynamic block registration / index remapping, so non-contiguous memory reclaimed
  from swapped-out FP16 layers can be attached as KV blocks. Runs on a separate CUDA
  stream.

**Evaluation setup** (§5, Appendix C). Models: Vicuna 7B v1.5, Llama 2 7B (MHA, 512/256
prompt/response), Llama 3 8B, CodeLlama 34B (GQA, 1024/512). Traces: Azure LLM Inference
2023 downscaled 4.75×, BurstGPT downscaled 1.75×; a 72-second snippet of each. Datasets:
GovReport, QMSum, DuReader, Multi-News; metrics F1 and ROUGE-L. Baselines: FP16, static
AWQ INT4, LLM-PQ (offline ILP mixed precision), PyramidKV (KV compression). Hardware:
**NVIDIA L4, 24 GB HBM + 256 GB DRAM** for the 7B/8B models; A100 80 GB for CodeLlama
34B. Implementation: ~2,200 lines Python + ~500 lines C++/CUDA on top of
[SwiftLLM](https://github.com/interestingLSY/swiftLLM) (§5, Appendix C).

**Headline numbers.**
- Figure 4 (p.7): a 4×4 grid of latency–accuracy scatter plots (x = P95 TTFT, y =
  F1/ROUGE-L) over {Azure, BurstGPT} × 4 datasets × 4 models. MorphServe is up-and-left of
  every baseline. P95 TTFT 2.9×–15.7× better than FP16 (2.2×–3.9× in accuracy mode) at
  0.51 %–3.82 % quality loss; static INT4 loses 2.34 %–9.47 %.
- Figure 6 (p.9): TTFT vs RPS; saturation delayed, 1.6×–1.83× higher throughput than FP16.
- Figure 5 (p.8): KV block occupancy over the 72 s trace; KV capacity expanded up to
  32.97 % beyond the FP16 limit, queueing delay down 3.8×.
- Figure 7 (p.9): TPOT CDF; average TPOT ≈ FP16, P99 up to 1.23× better.
- Table 5 (p.11): the cleanest ablation — runtime adaptation (F1 24.63, P95 TTFT 1.77 s,
  0 % SLO violations) beats every *static* selective-quantization setting (8 layers: F1
  24.16 but 4.2 % violations; 16 layers: F1 23.93).

**Stated limitations** (§6 and Appendix D): ~2× model size held in host DRAM; morphing is
layer-granular only (no separate attention/MLP control); the controller is *reactive*, not
predictive; memory headroom shrinks under native FP8/FP4 regimes; weight-only quantization
(no activation or KV quantization).

## 2. Artifact audit

### Repository structure

```
repo/
├── LICENSE      (MIT)
└── README.md    (49 lines of prose)
```

That is the entire repository. `repo_facts.json` confirms `file_count: 2`,
`size_mb: 0.0`, `build_files: []`, `lines_by_extension: {}`, `stargazers_count: 0`,
`open_issues_count: 0`. I re-fetched https://github.com/ds2-lab/MorphServe on 2026-09-14
and it still shows only those two files.

`repo/README.md:7-11` is explicit:

> ## 🚧 Code Release Status
> We are currently preparing the codebase for public release. The repository is being
> cleaned, documented, and organized for reproducibility … **The full code will be
> released soon. Stay tuned!**

The repo was created 2026-04-21 and last pushed 2026-04-21 (`repo_facts.json`
`created_at` / `pushed_at`). Five months later there has been no further commit. The
README links to the MLSys 2026 oral page (`repo/README.md:43`) and cites the authors'
arXiv preprint with the correct author list (`repo/README.md:52-57`), and the repo lives
under `ds2-lab`, Yue Cheng's group — so it *is* the official repo, it just has no code.

I checked the rest of the `ds2-lab` GitHub organization for a differently-named
implementation (ZipLLM, ELF, infinicache, Wukong, LambdaFS, NotebookOS, ALPS, FaaSNet) —
none is a MorphServe implementation or a SwiftLLM fork. A web search for the code turned
up only the arXiv/MLSys/aggregator pages, no mirror or fork with source.

### Paper component → code path map

| Paper component | Section | Code path |
|---|---|---|
| Serving Monitor | §4.1 | **absent** |
| Morphing Controller (thresholds, hysteresis) | §4.1, §6 | **absent** |
| LayerSwapper (`cudaMemcpyAsync`, pinned host pool) | §4.3, App. C | **absent** |
| KVResizer (Triton block registration/remap kernels) | §4.4, App. C | **absent** |
| LIS offline profiler + greedy Algorithm 1 | §4.2, App. A.2 | **absent** |
| Trace replay / workload generator | §5, App. C | **absent** |
| Baselines (AWQ, LLM-PQ, PyramidKV harness) | §5 | **absent** |
| Plotting for Figures 4–7 | §5 | **absent** |

Nothing in the paper's design has a corresponding file. The map is empty by construction.

### Build route on this machine (hypothetical)

If the ~2,700 LOC were released, the route would be plausible and root-free:
SwiftLLM is a pip/`setup.py` Python project with Triton and CUDA extensions; a conda env
with Python 3.10–3.11, PyTorch ≥2.1 + cu121 wheels, Triton, and `autoawq` would cover it.
Driver 535 (CUDA ≤ 12.2) is compatible with cu121 wheels; the system `nvcc` 11.8 would
likely need a conda-installed CUDA 12.1 toolkit to compile the C++/CUDA extension. No
Docker, no root, no perf counters, no eBPF are implied anywhere in the paper. This is a
prediction from the paper text only — there are no dependency pins to read.

### Data / trace / model sources (all verifiable from the paper)

Appendix C names public URLs for everything: Azure LLM Inference Dataset 2023
(`github.com/Azure/AzurePublicDataset`), BurstGPT (`github.com/HPMLL/BurstGPT`),
GovReport (`huggingface.co/datasets/launch/gov_report`), QMSum
(`github.com/Yale-LILY/QMSum`), DuReader (`github.com/baidu/DuReader`), Multi-News
(`github.com/Alex-Fabbri/Multi-News`), Vicuna-7B-v1.5 (`huggingface.co/lmsys/vicuna-7b-v1.5`).
Llama 2 7B and Llama 3 8B are gated on Hugging Face and would need a license acceptance;
Vicuna 7B v1.5 is ungated and is one of the paper's four models, so a substitute exists.

### Eval scripts

None present. No `requirements.txt`, no `setup.py`, no `scripts/`, no config files, no
figure notebooks.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **fail** | `repo/` contains only `LICENSE` and `README.md`. `repo/README.md:7-11` — "We are currently preparing the codebase for public release … The full code will be released soon." `repo_facts.json`: `file_count: 2`, `build_files: []`, `lines_by_extension: {}`. Re-verified on github.com 2026-09-14; no code in the `ds2-lab` org or any fork. This is exactly the "code coming soon" placeholder the rubric names. |
| `H2_no_root` | **pass** | Judged from the paper only, since there is no code. Appendix C describes pinned host memory, `cudaMemcpyAsync`, precompiled GEMM kernels, separate CUDA streams, and Triton KV-mapping kernels — all user-space CUDA. §5 says it is built on SwiftLLM, a Python inference framework. No kernel module, eBPF, `perf`, KVM, hugepage, or `/proc/sys` requirement appears anywhere in §4, §5, or Appendix C. |
| `H3_hardware_fit` | **pass** | §5 / Appendix C: the three 7B–8B models (Vicuna 7B v1.5, Llama 2 7B, Llama 3 8B) were evaluated on an **NVIDIA L4 with 24 GB HBM and 256 GB DRAM** — the same GPU memory as the A5000 here, and the A5000 (Ampere, 8.6) is the faster part. Traces are already downscaled 1.75×/4.75× by the authors to fit 24 GB. Only CodeLlama 34B needs the A100 80 GB; dropping it is a clean scale-down that still covers MHA and GQA. Host DRAM is the one gap: the paper assumes 256 GB and this machine has 125 GB shared, but ~2× a 7B model in pinned FP16+W8+W4 host copies is well under 40 GB, so it fits. FP8 kernels are irrelevant — the paper is INT4/INT8 weight-only. |
| `H4_obtainable_deps_data` | **pass** | Appendix C gives public URLs for both traces and all four datasets (listed in §2 above). Vicuna 7B v1.5 is ungated on HF; AWQ INT4 checkpoints are publicly distributed. SwiftLLM, the base framework, is public. Llama 2/3 weights are license-gated, which is a friction point, not a blocker, since Vicuna covers the MHA case. The unobtainable dependency is MorphServe itself, which is `H1`'s problem, not `H4`'s. |

Any `fail` ⇒ **reject**. The `H1` failure is decisive and not a judgement call.

## 4. Reproduction plan

**Level: L.**

**Target (if code existed):** Figure 6, p.9 — the TTFT-vs-RPS saturation curve on
DuReader for Vicuna 7B v1.5 and Llama 2 7B. It supports the claim that MorphServe delays
the saturation point and delivers 1.6×–1.83× higher throughput than FP16 serving. It is
the best target because it is a sweep over a scalar knob (RPS) rather than a trace replay,
so it needs no timestamp alignment machinery, and it only needs the FP16 and static-INT4
baselines, both of which are off-the-shelf.

**Scale-down:** drop CodeLlama 34B entirely (needs 80 GB). Keep Vicuna 7B v1.5 (ungated)
and, license permitting, Llama 3 8B. Keep the authors' own 1.75×/4.75× trace downscaling
and the 512/256 (MHA) and 1024/512 (GQA) prompt/response lengths — these were chosen for a
24 GB L4 and transfer to the 24 GB A5000 unchanged. Use AWQ INT4 checkpoints from the Hub
rather than re-quantizing.

**Why L, not M.** "Reproducible with real porting work" (M) assumes there is something to
port. Here the first step is not porting but *reimplementing* the paper: ~2,200 lines of
Python and ~500 lines of C++/CUDA (§5), including the two pieces the paper itself flags as
the hard parts (Appendix C): zero-overhead precision switching via weight-pointer
redirection into preallocated GPU regions, and custom Triton kernels for registering
non-contiguous reclaimed memory as PagedAttention blocks. Neither has pseudocode in the
paper. Threshold values are given only as illustrative examples (KV > 85 %, queue delay >
100 ms, §4.1); the three runtime modes (default / performance / accuracy) are named in §5
but never parameterized; the hysteresis window length (§6, Appendix D) is never given.
Reproducing Figure 6 therefore means re-deriving a system, not re-running one.

**Effort estimate (only if the code is released):** ~8–12 person-days to stand up the
environment, fetch weights and traces, replay the DuReader sweep for two models × three
configurations, and plot — plus ~30–50 GPU-hours on the A5000. **As the repository stands
today:** 6–10 person-weeks of reimplementation before the first reproduction attempt, with
no guarantee the reimplementation matches the authors' constants. That is most of the
10-week budget spent before any novel contribution begins.

## 5. Add-on ideas

All five ideas below are grounded in limitations the authors state themselves
(§6 "Future Work", Appendix D "Limitations"), which is the strongest possible motivation.
Every one of them, however, presupposes a working MorphServe.

**A note on `code_locations`.** The rubric requires paths that exist in `repo/`. The only
two files in `repo/` are `LICENSE` and `README.md`, neither of which is code. I therefore
list `README.md` for every add-on and name the *intended* insertion point in the mechanism
text. This is not evasion — it is the honest representation of an artifact with zero
source files, and it is the reason the feasibility ratings below are depressed.

---

### 5.1 Predictive morphing from trace forecasting

**Hypothesis.** We hypothesize that replacing MorphServe's reactive threshold trigger with
a short-horizon workload forecast reduces P95 TTFT and SLO-violation rate on the leading
edge of a burst, under the BurstGPT and Azure traces, compared with MorphServe's reactive
controller — at equal or better average generation quality (because fewer *total* layers
need to be swapped when swapping starts earlier).

**Mechanism.** Add a forecaster to the Morphing Controller (§4.1): an EWMA or small AR /
gradient-boosted model over the last N seconds of (arrival rate, prompt-token volume, KV
occupancy) predicting KV occupancy `H` seconds ahead. Fire `LayerSwapper` when the
*predicted* occupancy crosses the threshold, keeping the existing hysteresis as a
fallback. The swap is ~6 ms (§4.3) while the burst onset is hundreds of ms, so the win is
not the swap latency — it is avoiding the queue that builds while the reactive controller
waits for pressure to *persist across multiple forward passes* (§6, "Stability under
Oscillating Load"). Sweep `H` to expose the precision/recall tradeoff: over-eager
forecasting quantizes layers that were not needed, costing accuracy for nothing.

**Code locations.** `README.md` (no controller module exists; the insertion point would be
the Morphing Controller described in §4.1 / Figure 2).

**Motivating evidence.** Appendix D, verbatim: *"MorphServe reacts to system pressure in
real time but does not anticipate upcoming surges. Integrating lightweight workload
forecasting could enable proactive morphing decisions and further improve responsiveness
under bursty traffic."* Figure 1b shows TTFT already above the 2 s SLO at the burst onset,
which is precisely the interval a forecast would cover.

**Feasibility: M.** The forecaster itself is a few hundred lines and the evaluation reuses
the existing trace-replay harness and Figure 4/6 plots. But it only becomes an "add-on"
after MorphServe exists; against today's repo this is L. Rated M on the assumption of a
code release.

**Research value: M.** The authors named it as future work, so a reviewer would find it
expected rather than surprising — but the negative result is genuinely interesting: if
6 ms swaps mean reaction is already fast enough that forecasting buys nothing, that is a
clean, publishable falsification of the authors' own stated direction.

**Scoop check: partial.** Searched "proactive workload forecasting predictive precision
adaptation LLM serving quantized layer swapping 2026" and "papers citing MorphServe
2506.02006". Forecast-driven LLM serving exists but at a different control knob:
[SageServe](https://arxiv.org/pdf/2502.14617) forecasts demand to drive cluster
*auto-scaling*, and [Predictive-LoRA](https://arxiv.org/html/2512.20210) uses an LSTM
traffic predictor to prefetch *LoRA adapters*. Neither forecasts to drive *weight-precision*
morphing. No paper citing MorphServe was found.

---

### 5.2 Sub-layer morphing granularity (attention vs MLP)

**Hypothesis.** We hypothesize that morphing attention and MLP submodules independently,
rather than whole decoder layers, achieves a strictly better accuracy-per-byte-freed
frontier under the same memory-pressure schedule, compared with MorphServe's layer-granular
swapping.

**Mechanism.** Split the LIS profiler (§4.2, Algorithm 1) so LTS/LRS/MDS are computed per
submodule (`self_attn.{q,k,v,o}_proj`, `mlp.{gate,up,down}_proj` — the names appear in
Figure 3e) instead of per layer, producing a ranked list of ~7×L entries. Extend the
swapping sequence and the preallocated-GPU-region bookkeeping to submodule granularity. In
a Llama-2-7B decoder layer the MLP is roughly twice the attention block, so submodule
granularity gives both a finer memory quantum (~0.13 GB vs 0.4 GB) and the option to
quantize the cheap-to-quantize half of a layer whose other half is sensitive.

**Code locations.** `README.md` (no profiler or swapper module exists; would touch the LIS
profiler of §4.2/Appendix A.2 and the LayerSwapper of §4.3).

**Motivating evidence.** Appendix D, verbatim: *"MorphServe currently applies morphing at
the transformer layer level. While effective, finer-grained adaptation, such as
independently adjusting attention and MLP submodules, could unlock additional efficiency
and precision flexibility."* Table 8 gives the opening: LIS barely separates from
Front-to-Back at layer granularity (Llama 2 7B, 16 layers: 5.52 vs 5.54), suggesting the
layer-level signal is nearly saturated and the remaining headroom is below the layer.

**Feasibility: M.** The profiler change is small and offline (§A.3: full LIS for a 32-layer
model takes under 15 minutes on one GPU, so ~7× that is still trivial). The runtime change
is more invasive — the "same memory addresses, no pointer remapping" invariant of §4.3
assumes layer-sized regions, so the allocator bookkeeping must be reworked. Cross-cutting,
hence M.

**Research value: M.** Directly addresses a named limitation and is the kind of result that
transfers to any precision-switching system. Marked down from H because the likely outcome
(finer granularity helps somewhat) is not surprising, and Table 8's flatness hints the
effect may be small.

**Scoop check: partial.** Per-submodule and per-channel mixed-precision assignment is
well-trodden in the *static* PTQ literature the paper itself cites (HAWQ, channel-wise
mixed-precision assignment, AffineQuant). What is unclaimed is doing it as a *runtime,
reversible* knob inside a serving loop. No follow-up to MorphServe found.

---

### 5.3 SSD-backed layer streaming instead of a 2× host-DRAM resident pool

**Hypothesis.** We hypothesize that streaming quantized layer variants from NVMe on demand,
with a small host-DRAM cache, holds P99 TPOT within a few percent of the fully-resident
design while cutting host memory for layer variants by more than 2×, under the paper's
Azure and BurstGPT traces.

**Mechanism.** Replace the "all variants pinned in host DRAM" preloading of §4.3 with a
two-tier store: the top-`k` entries of the LIS swap sequence stay pinned in DRAM, the tail
lives on NVMe and is read with `O_DIRECT` / `io_uring` into a pinned staging buffer, then
DMA'd to GPU. The paper's own numbers make this testable: a swap is ~6 ms end-to-end with
~4 ms of PCIe transfer for an INT4 Llama-2-7B layer; a ~0.1 GB INT4 layer off a PM9A3 at
several GB/s adds tens of ms, so the interesting question is whether the prefetch depth
can hide it. Sweep `k` from 0 (pure streaming) to L (the paper's design).

**Code locations.** `README.md` (no preloading module exists; would replace the model-
preloading path of §4.3).

**Motivating evidence.** Appendix D, verbatim: *"To support runtime layer swapping,
MorphServe stores both full-precision and quantized variants in host memory. Although this
increases memory usage, the overhead is typically under 2× the model size … Future work may
further reduce this cost by streaming layers from SSD to host memory on demand or directly
fetching them from SSD via GPUDirect Storage."* §6 adds "demand-driven layer streaming" as
an explicit open item.

**Feasibility: M.** Fits this machine well — 2 × PM9A3 NVMe, ~257 GB free, and the
experiment is *about* the memory constraint this machine actually has (125 GB shared vs the
paper's 256 GB). GPUDirect Storage proper needs `nvidia-fs`, which is not installable
without root, so the design must use the ordinary read-then-DMA path; that is a real
restriction but it does not invalidate the hypothesis. Needs a new microbenchmark harness
on top of the end-to-end one.

**Research value: M.** Turns the paper's throwaway "under 2× and clusters have plenty of
DRAM" hand-wave into a measured tradeoff, and it is exactly the direction that makes
MorphServe viable for the edge deployments §6 says the authors care about. Not H because
tiered weight streaming is a familiar pattern.

**Scoop check: clear.** No work found that applies SSD-tiered variant storage to *runtime
precision switching*. Weight streaming from SSD is standard for offloaded inference
(FlexGen, DeepSpeed-Inference, ServerlessLLM — the last is cited by the paper), but those
stream a *single* precision's weights to fit a model that does not fit, not multiple
precision variants to support reversible morphing.

---

### 5.4 Joint weight-precision and KV-precision morphing

**Hypothesis.** We hypothesize that adding KV-cache quantization as a third runtime knob,
co-scheduled with layer swapping, sustains a higher request rate before saturation than
weight-only morphing at matched end-to-end generation quality, under long-context workloads
(GovReport, 2k+ token documents).

**Mechanism.** Add a `KVQuantizer` alongside `KVResizer` (§4.4) that can demote *cold* KV
blocks (belonging to older positions of long-running sequences) from FP16 to INT8 in place,
and a joint policy in the Morphing Controller that chooses, per pressure event, between
swapping another layer and demoting another tranche of KV blocks. The two knobs trade off
differently: layer swapping costs accuracy on *future* tokens of *all* requests, KV
demotion costs accuracy on *past* context of *specific* requests. The policy question —
which is cheaper per byte freed — is the research content.

**Code locations.** `README.md` (no KVResizer module exists; would extend the PagedAttention
block manager of §4.4 / Appendix C).

**Motivating evidence.** §6, verbatim: *"MorphServe can extend beyond weight-only
quantization to include activation and KV quantization. Such extensions promise higher
efficiency but raise calibration and scheduling challenges."* §4.4 is explicit that
"KVResizer does not quantize or compress existing KV caches" — the lever is simply unused.
The paper's own comparison against PyramidKV (§5.1) shows KV compression buys accuracy but
little TTFT, which sets up the hybrid as the interesting middle.

**Feasibility: M.** INT8 KV quantization has mature open kernels to borrow, and the
evaluation reuses the existing harness. But touching the paged block layout while
KVResizer is concurrently attaching and detaching blocks is the most delicate part of the
system, and the paper already calls the non-contiguous block management a central
challenge (Appendix C). Heavier than 5.1.

**Research value: H.** This is the one add-on where either outcome teaches something
non-obvious. The paper's whole thesis is that *reversible, coordinated* adaptation beats
static compression; showing whether a second, qualitatively different knob composes with
the first — or whether the two interfere because both degrade the same output — is a
genuine test of that thesis rather than an extension of it. A reviewer at MLSys would care.

**Scoop check: partial.** KV quantization (KIVI, QServe's KV4, Atom — the last two cited by
the paper) and adaptive KV budgeting (PyramidKV, AdaKV, DynamicKV — all cited) are
well-covered as *standalone static* policies. Search surfaced
[FineServe](https://arxiv.org/abs/2509.21081) on precision-aware KV slabs and two-level
scheduling for heterogeneous-precision serving, which is the closest neighbour, but it
schedules across models of fixed precision rather than co-morphing weight and KV precision
for one model at runtime. No direct scoop found.

---

### 5.5 Fairness and per-request quality accounting under morphing

**Hypothesis.** We hypothesize that MorphServe's pressure-triggered morphing distributes
accuracy degradation unevenly across requests — concentrating it on requests unlucky enough
to be decoding during a burst — and that a quality-aware admission/scheduling policy
equalizes the per-request degradation distribution at negligible cost to P95 TTFT.

**Mechanism.** First, measure: instrument the decode loop to tag each generated token with
the active precision configuration, then report the *distribution* over requests of
"fraction of tokens generated under quantized layers", not just the aggregate F1. Second,
if the distribution is skewed, add a quality budget per request to the scheduler — a
request that has already exceeded its degraded-token budget gets priority for FP16 layers,
or is deferred rather than degraded further.

**Code locations.** `README.md` (no scheduler or executor module exists; would instrument
the decode loop and extend the FIFO continuous-batching scheduler discussed in §6).

**Motivating evidence.** The paper reports only aggregate F1/ROUGE-L (Figure 4, Tables 4,
5, 9) and the mixed-precision study in Table 1 is a *hand-constructed* schedule (first 1 K
FP16 / last 1 K W4, etc.), not the distribution that the real controller produces. §6's
"Fairness" paragraph asserts fairness holds because continuous batching preserves FIFO and
chunked prefill prevents starvation — but that argument is about *latency* fairness and
says nothing about *quality* fairness, which is the axis MorphServe newly introduces.
Table 1 also shows the schedule matters a lot: "First 1 K FP16 / last 1 K W4" scores F1
16.61 while the reverse scores 14.71, a 13 % spread at identical quantized-token count.

**Feasibility: H.** The measurement half is pure instrumentation — a per-token precision
tag and a histogram — and reuses every existing workload and baseline. The policy half is a
localized scheduler change. This is comfortably inside the "few modules, existing harness"
bar, *conditional on the code existing*.

**Research value: H.** It identifies a metric the paper does not report and whose absence
is load-bearing for the paper's central claim ("without compromising generation quality").
A per-request tail-quality metric is the natural analogue of tail latency, and Table 1's
13 % schedule-dependent spread suggests the tail is real. Either result is informative: a
flat distribution vindicates the design under a sharper lens, a skewed one exposes a
fairness problem the paper explicitly claimed not to have.

**Scoop check: clear.** Searched for follow-ups on MorphServe and for quality-fairness in
mixed-precision serving; nothing found. Fairness in LLM serving is an active area (e.g.
VTC, OSDI'24) but is framed entirely around throughput/latency share, not around
degradation-quality share — that axis only exists once precision becomes a runtime
variable, which is new with this paper.

---

Note for the driver: because `H1_open_repo` fails, the verdict is **reject** regardless of
these ratings. They are recorded so the paper can be re-scored quickly if the authors
publish the code.

## 6. Risks and open questions

1. **The artifact does not exist.** This is the whole finding. `repo/README.md:7-11` says
   the code is coming; the repo has been untouched since 2026-04-21. Nothing in this audit
   about the implementation is verified — every `H2`/`H3`/`H4` judgement rests on the paper
   text alone.
2. **No release date, and no signal.** MLSys 2026 has already happened. Five months of no
   commits, 0 stars, 0 issues, 0 forks. A team choosing this paper would be betting the
   semester on an event with no announced timeline. If the release slips past week 3, the
   project has no fallback.
3. **Reimplementation is not a viable Plan B here.** 2,700 LOC sounds tractable, but the
   two hardest components (Triton kernels for dynamic non-contiguous KV block registration;
   in-place weight-pointer redirection with precompiled per-precision GEMM dispatch) are
   described only in prose in Appendix C. There is no pseudocode, and the controller's
   actual thresholds, mode definitions, and hysteresis window are never given as numbers.
4. **MLSys has no artifact-evaluation badge program**, so there is no external "Results
   Reproduced" signal to fall back on — nothing in the paper, the proceedings page, or the
   repo claims a badge.
5. **Host DRAM is tighter here than in the paper.** §5 used 256 GB; this machine has 125 GB
   shared with other users. Fine for 7B/8B (~40 GB of pinned variants), but it removes all
   slack, and pinned memory cannot be swapped.
6. **Llama 2 / Llama 3 weights are license-gated on Hugging Face** while `env.md` only
   guarantees non-gated HF access. Vicuna 7B v1.5 (ungated) covers the MHA case, so this is
   friction rather than a blocker — but it halves the model coverage if gating cannot be
   cleared.
7. **CodeLlama 34B is out of reach** (A100 80 GB in the paper). Any reproduction covers 3
   of the paper's 4 models at most.
8. **`nvcc` 11.8 vs a likely CUDA 12.x requirement.** SwiftLLM-class projects target recent
   PyTorch/Triton. A conda-installed CUDA 12.1 toolkit is the route, and driver 535 supports
   ≤ 12.2, so anything pinned to CUDA 12.4+ kernels would be a problem. Unverifiable without
   the code.
9. **Even the LIS contribution is soft.** Table 8 shows LIS ≈ Front-to-Back across all four
   models, and §A.3 admits Front-to-Back is the default when profiling is unavailable. A
   reproduction that targeted the profiling contribution would be measuring a near-null
   effect; the systems mechanisms are where the value is.

## 7. Evidence index

**Paper — sections**
- §1 Introduction (p.1–2) — contributions, headline claims (92.45 % SLO reduction, 2.2×–3.9× P95 TTFT).
- §2 Related Work (p.2–3) — positioning vs LLM-PQ, PMPD, MARLIN, LayerSkip, FlexiDepth.
- §3 Motivation (p.3) — burstiness, saturation point, 2 s TTFT SLO.
- §4.1 Architecture and Workflow (p.4) — Serving Monitor / Morphing Controller / Morphing Executor; thresholds (KV > 85 %, queue delay > 100 ms); token-level adaptation; state-preserving morphing.
- §4.2 Offline Profiling (p.5) — Eq. 1–5, LIS, α1=α2=0.25, β=0.5; cosine vs L2 rationale.
- §4.3 LayerSwapper (p.6) — preloading, kernel precompilation, `cudaMemcpyAsync`, ~4 ms / ~6 ms swap costs, ~0.4 GB FP16 / ~0.1 GB INT4 per Llama-2-7B layer.
- §4.4 KVResizer (p.6–7) — block attach/detach, separate CUDA streams, prefill queueing and decode preemption arguments.
- §5 Experiment (p.7–8) — models, traces (4.75× / 1.75× downscale, 72 s snippets), datasets, **L4 24 GB + 256 GB DRAM / A100 80 GB**, implementation size (2,200 Py + 500 C++/CUDA on SwiftLLM), baselines, three runtime modes.
- §5.1 Main Results (p.8–10); §5.2 Ablation Study (p.10).
- §6 Discussion and Future Work (p.11) — user tolerance, scalability, fairness, oscillation stability, FP8/FP4 outlook, KV/activation quantization.
- Appendix A.1–A.3 (p.16–18) — LIS design, hyperparameter and cosine-vs-L2 ablations, Algorithm 1, "under 15 minutes" profiling, Front-to-Back default.
- Appendix B.1–B.2 (p.18–19) — verbatim mixed-precision output; AWQ vs uniform INT4.
- **Appendix C Implementation Details (p.18–20)** — pinned host preloading of FP16/W8/W4, precompiled GEMM kernels, in-place swap without pointer remapping, custom Triton KV mapping kernels, and public URLs for both traces and all four datasets.
- Appendix D Limitations and Broader Impacts (p.20) — 2× host memory, layer-level granularity, reactive-not-predictive, FP8/FP4 headroom, hysteresis.

**Paper — figures and tables**
- Figure 1a–d (p.3) — trace burstiness; FP16 TTFT spikes vs SLO; static-W4 constant accuracy drop; Pareto summary.
- Figure 2 (p.4) — system architecture and 6-step workflow.
- Figure 3a–f (p.6) — layer morphing and KV block attach/detach; submodule names (`self_attn.q_proj`, `mlp.gate_proj`).
- **Figure 4 (p.7, read as `pages/page-07.png`)** — 4×4 latency–accuracy scatter grid, x = P95 TTFT, y = F1/ROUGE-L, over {Azure, BurstGPT} × {GovReport, QMSum, DuReader, Multi-News} × {Vicuna 7B, Llama 2 7B, Llama 3 8B, CodeLlama 34B}.
- Figure 5 (p.8) — KV block usage over the 72 s BurstGPT trace; FP16 capacity line at 958 / 2599 / 3435 blocks.
- **Figure 6 (p.9)** — TTFT vs RPS, DuReader; the reproduction target.
- Figure 7 (p.9) — TPOT CDF, Azure trace.
- Table 1 (p.8) — hand-constructed mixed-precision schedules on Llama 3 8B / BookSum (F1 14.47 → 17.65 bounds; 16.61 vs 14.71 for reversed schedules).
- Tables 2, 3 (p.10) — layer-quantization additivity; LIS cross-dataset generalization.
- Tables 4, 9 (p.11, p.19) — AWQ vs uniform INT4.
- **Table 5 (p.11)** — runtime adaptation vs static selective quantization (the cleanest ablation).
- Tables 6, 7, 8 (p.17–18) — LIS hyperparameters, cosine vs L2, and swap-order comparison showing LIS ≈ Front-to-Back.

**Repository paths**
- `repo/README.md` — whole file; lines 7–11 are the code-release disclaimer, line 43 the MLSys link, lines 52–57 the citation.
- `repo/LICENSE` — MIT.
- (no other files exist; `repo/.git/` only)

**Driver-computed facts**
- `repo_facts.json` — `file_count: 2`, `size_mb: 0.0`, `top_level: ["LICENSE", "README.md"]`, `build_files: []`, `lines_by_extension: {}`, `red_flags: {}`, `head_commit_date: 2026-04-20`, `created_at: 2026-04-21`, `pushed_at: 2026-04-21`, `stargazers_count: 0`, `forks_count: 0`, `open_issues_count: 0`.
- `fetch_result.json` — repo `official: "unclear"` ("link taken from the research list; not independently verified"); upgraded to `yes` here by the `ds2-lab` org + README citation + MLSys link.
- `meta.json` — venue MLSys 2026, `repo_url`, scout's note.

**External lookups (2026-09-14)**
- https://github.com/ds2-lab/MorphServe — re-verified: 2 files, no source.
- https://api.github.com/orgs/ds2-lab/repos — no MorphServe implementation or SwiftLLM fork elsewhere in the org.
- Web search "MorphServe … code github" — only arXiv 2506.02006, mlsys.org/virtual/2026/oral/3816, and aggregator pages; no mirror or fork.
- https://github.com/interestingLSY/swiftLLM — the public base framework named in §5.
- Scoop-check neighbours: [SageServe](https://arxiv.org/pdf/2502.14617), [Predictive-LoRA](https://arxiv.org/html/2512.20210), [FineServe](https://arxiv.org/abs/2509.21081).
