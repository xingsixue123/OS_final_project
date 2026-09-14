STATUS: complete
TOTAL_PAPERS: 168
INCLUDED: 30

## Sources

**Primary list.** The official ASPLOS 2026 program page,
https://www.asplos-conference.org/asplos2026/program/ (conference held in Pittsburgh,
24-26 March 2026). The page embeds a structured detailed program: 36 technical sessions
(1A-9D) with one `paper-title`/`paper-authors` block per talk. Parsing the raw HTML with
`curl` + a regex over those blocks yields **168 distinct paper titles** (no duplicates).
The program overview text on the same page says "167 unique papers", a one-off
discrepancy I could not reconcile; I report the 168 entries I actually enumerated.

**What the 168 consist of.** ASPLOS 2026 (the 31st ASPLOS) has two published proceedings
volumes so far, confirmed through Crossref:
Volume 1 = `10.1145/3760250` (ISBN 9798400721656) and Volume 2 = `10.1145/3779212`
(ISBN 9798400723599). No Volume 3 for the 31st ASPLOS exists in Crossref as of
2026-09-14. Cross-checking DOIs showed that **16 of the 168 programmed papers carry
`10.1145/3676642.x` DOIs**, i.e. they were published in *ASPLOS 2025 Volume 3* (the 30th
ASPLOS, last cycle) but were presented at the ASPLOS 2026 conference: PowerMove,
HybridTier, DeepContext, PUSHtap, Neuralink, ASDR, SylQ-SV, Voyager, Syno, TempGraph,
Hopps/Leveraging Sparsity, COGENT, DejaVuzz, Lambda-trim, Fault Escaping and Wave.
I kept them, since the brief asks for all cycles and both years are inside the 2023-2026
window; their rows say so.

**Cross-checks on the count.**
1. `github.com/RealZST/csconf-papers/blob/main/papers/2026/ASPLOS.md` (snapshot
   2026-09-10, built from the ACM DL) lists 155 entries = 3 keynotes + **152 papers**,
   and those 152 are exactly the ASPLOS 2026 Vol 1 + Vol 2 papers. 152 + 16 carry-over
   papers = the 168 in the program. This list is also the source of the ACM DOI and
   ACM PDF links in the tables.
2. DBLP (`dblp.org/db/conf/asplos/asplos2026-1.html` and `-2.html`, reached through the
   `r.jina.ai` reader because DBLP is behind an Anubis proof-of-work wall) reports 21
   records for Volume 1 and 136 for Volume 2 (minus front matter and 3 keynotes), i.e.
   about 153 papers - consistent with the 152 above. DBLP has no `asplos2026-3` entries.
3. The ACM DL TOC pages themselves (`dl.acm.org/doi/proceedings/10.1145/3760250`) return
   HTTP 403 to scripted access, so they were used only indirectly via Crossref.

**Abstracts.** OpenAlex `api.openalex.org/works?search=<title>` (86 exact matches before
the daily quota ran out), arXiv `arxiv.org/abs/<id>` pages for the 61 papers with a
preprint listed by the csconf index, plus targeted reads of author PDFs and vendor pages
for a handful of remaining cases. Records whose OpenAlex hit was a false match (12 of
them, e.g. "I/O Analysis is All You Need" matching a nursing-methods paper) were
discarded rather than used.

**Code search.** For each surviving paper I looked for the official artifact in this
order: (a) the DataCite API for Zenodo/figshare artifact DOIs mentioning ASPLOS 2026 or
ASPLOS'26 (118 hits, several of which are GitHub mirror releases and expose the upstream
repository in their `relatedIdentifier`); (b) the GitHub repository search API with
`"ASPLOS 2026" in:readme`, `"ASPLOS'26" in:readme`, `asplos26`, `asplos-26` and
`asplos2026`, which returned 174 distinct repositories; (c) per-system GitHub repository
searches by name and by distinctive phrases from the title; (d) web search and the arXiv
/ ACM landing page for the remaining ones. The ASPLOS'26 AEC site
(`sites.google.com/view/asplos26aec`) publishes no artifact-badge results list, and
`sysartifacts.github.io` has no ASPLOS pages, so there is no single authoritative
artifact index for this venue-year.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | Bullet: Boosting GPU Utilization for LLM Serving via Dynamic Spatial-Temporal Orchestration | https://doi.org/10.1145/3779212.3790135 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790135 | https://github.com/zejia-lin/BulletServe | llm-inference | Single-GPU spatial-temporal sharing of prefill and decode - exactly the kind of intra-GPU serving mechanism one A5000 can host with a 7B model |
| 2 | QoServe: Breaking the Silos of LLM Inference Serving | https://doi.org/10.1145/3779212.3790206 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790206 | https://github.com/microsoft/sarathi-serve | llm-inference | QoS-driven scheduling on top of Sarathi-Serve; artifact is the niyama_asplos2026 branch. Concern: paper evaluates an A100 cluster so a single-replica scale-down is needed |
| 3 | PAT: Accelerating LLM Decoding via Prefix-Aware Attention with Resource Efficient Multi-Tile Kernel | https://doi.org/10.1145/3779212.3790200 | https://arxiv.org/pdf/2511.22333 | https://github.com/flashserve/PAT | llm-inference | Prefix-aware attention decode kernel; pure CUDA/Triton kernel work that runs on one Ampere GPU. Zenodo AE artifact 10.5281/zenodo.18217189 |
| 4 | ZipServ: Fast and Memory-Efficient LLM Inference with Hardware-Aware Lossless Compression | https://doi.org/10.1145/3779212.3790250 | https://arxiv.org/pdf/2603.17435 | https://github.com/HPMLL/ZipServ_ASPLOS26 | llm-inference | Lossless weight compression plus fused decompress-GEMM kernels; Tensor-Core path exists on Ampere. Concern: FP8/FP4 variants would need Ada or Hopper |
| 5 | SNIP: An Adaptive Mixed Precision Framework for Subbyte Large Language Model Training | https://doi.org/10.1145/3779212.3790223 | https://arxiv.org/pdf/2602.01410 | https://github.com/pyjhzwh/SNIP | ml-systems | Adaptive mixed-precision LLM training policy; authors themselves evaluate with a pseudo-quantization proxy because they lack Blackwell, so it is GPU-portable. Concern: pretraining compute must be scaled to small models |
| 6 | SpecProto: A Parallelizing Compiler for Speculative Decoding of Large Protocol Buffers Data | https://doi.org/10.1145/3779212.3790225 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790225 | https://github.com/AutomataLab/SpecProto | other-userspace | Parallelizing compiler for Protobuf decoding; CPU-only artifact that targets 16 physical cores which this machine has |
| 7 | GFS: A Preemption-aware Scheduling Framework for GPU Clusters with Predictive Spot Instance Management | https://doi.org/10.1145/3760250.3762231 | https://arxiv.org/pdf/2509.11134 | https://github.com/Xu-Sheng-lin/GFS-asplos-26 | scheduling | Preemption-aware GPU-cluster scheduler with demand forecasting; policy work that can be studied trace-driven or in simulation. Concern: repo has no README yet and the paper evaluates a real cluster |
| 8 | Insum: Sparse GPU Kernels Simplified and Optimized with Indirect Einsums | https://doi.org/10.1145/3779212.3790176 | https://arxiv.org/pdf/2510.17505 | https://github.com/nullplay/IndirectEinsum | ml-systems | Sparse GPU kernel compiler lowering indirect Einsums through the PyTorch compiler; single-GPU, user-space |
| 9 | MoDM: Efficient Serving for Image Generation via Mixture-of-Diffusion Models | https://doi.org/10.1145/3760250.3762220 | https://arxiv.org/pdf/2503.11972 | https://github.com/stsxxx/MoDM | llm-inference | Caching-based serving for diffusion models; retrieval cache plus small/large model mix. Concern: artifact assumes a 48 GB A40 so SDXL-class models need scale-down or offload on 24 GB |
| 10 | FastTTS: Accelerating Test-Time Scaling for Edge LLM Reasoning | https://doi.org/10.1145/3779212.3790161 | https://arxiv.org/pdf/2509.00195 | https://github.com/ihc-fan-lab/FastTTS | llm-inference | Test-time-scaling serving framework built as a vLLM plug-in for memory-constrained devices; a 24 GB GPU is a realistic target |
| 11 | GS-Scale: Unlocking Large-Scale 3D Gaussian Splatting Training via Host Offloading | https://doi.org/10.1145/3779212.3790167 | https://arxiv.org/pdf/2509.15645 | https://github.com/SNU-ARC/GS-Scale | ml-systems | Host-offloading 3DGS training explicitly aimed at consumer GPUs; 125 GiB host RAM plus one 24 GB GPU is the intended setting |
| 12 | CLM: Removing the GPU Memory Barrier for 3D Gaussian Splatting | https://doi.org/10.1145/3779212.3790140 | https://arxiv.org/pdf/2511.04951 | https://github.com/nyu-systems/CLM-GS | ml-systems | CPU-offloading for 3DGS on a single consumer GPU - the paper itself targets one RTX 4090 |
| 13 | Triton-Sanitizer: A Fast and Device-Agnostic Memory Sanitizer for Triton with Rich Diagnostic Context | https://doi.org/10.1145/3779212.3790241 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790241 | https://github.com/Deep-Learning-Profiling-Tools/TritonSanitizer-Experiments | ml-systems | Device-agnostic memory sanitizer for Triton kernels; user-space, single GPU. Concern: the AE scripts assume a ROCm Docker image so the NVIDIA path needs porting since Docker is unavailable |
| 14 | Trinity: Three-Dimensional Tensor Program Optimization via Tile-level Equality Saturation | https://doi.org/10.1145/3779212.3790240 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790240 | https://github.com/kaist-ina/Trinity-AE | ml-systems | Tile-level equality saturation tensor compiler emitting Triton kernels; single-GPU compile-and-benchmark loop |
| 15 | Linear Layouts: Robust Code Generation of Efficient Tensor Computation Using F2 | https://doi.org/10.1145/3760250.3762221 | https://arxiv.org/pdf/2505.23819 | https://github.com/triton-lang/triton | ml-systems | Linear-algebra formulation of tensor layouts inside the Triton compiler; implementation is upstream in Triton so it builds and runs on one Ampere GPU |
| 16 | It Takes Two to Entangle | https://doi.org/10.1145/3779212.3790178 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790178 | https://github.com/nyu-systems/Entangle | ml-systems | Equivalence checker that relates sequential and distributed ML computation graphs; the artifact itself is a user-space analysis tool. Concern: the motivating bugs come from multi-GPU training runs |
| 17 | Tilus: A Tile-Level GPGPU Programming Language for Low-Precision Computation | https://doi.org/10.1145/3760250.3762219 | https://arxiv.org/pdf/2504.12984 | https://github.com/NVIDIA/tilus | ml-systems | Tile-level GPGPU DSL for low-precision kernels; Ampere is a supported target. Concern: some tutorials target Blackwell-only features |
| 18 | LPO: Discovering Missed Peephole Optimizations with Large Language Models | https://doi.org/10.1145/3779212.3790184 | https://arxiv.org/pdf/2508.16125 | https://github.com/uw-pluverse/lpo-artifact | ml-for-systems | LLM proposes LLVM peephole rewrites that Alive2 verifies; entirely user-space and CPU-bound. Concern: needs an LLM API budget and is closer to compilers than to classic systems |
| 19 | Nemo: A Low-Write-Amplification Cache for Tiny Objects on Log-Structured Flash Devices | https://doi.org/10.1145/3779212.3790191 | https://arxiv.org/pdf/2603.09605 | https://github.com/XMU-DISCLab/Cachelib-Nemo | storage | Set-associative flash-cache design built as a CacheLib module; runs in user space on the local NVMe drives |
| 20 | CacheMind: From Miss Rates to Why – Natural-Language, Trace-Grounded Reasoning for Cache Replacement | https://doi.org/10.1145/3779212.3790136 | https://arxiv.org/pdf/2602.12422 | https://github.com/kaushal1803/cachemind | ml-for-systems | LLM plus RAG reasoning over cache traces with a released benchmark; trace-driven and CPU-only. Concern: the repo is author-named and not linked from the paper so ownership is unconfirmed |
| 21 | Syno: Structured Synthesis for Neural Operators | https://doi.org/10.1145/3676642.3736118 | https://dl.acm.org/doi/pdf/10.1145/3676642.3736118 | https://github.com/tsinghua-ideal/Syno | ml-systems | Structured synthesis of neural operators; search plus single-GPU kernel evaluation. Published in ASPLOS 2025 Volume 3 and presented at ASPLOS 2026 |
| 22 | LOOPRAG: Enhancing Loop Transformation Optimization with Retrieval-Augmented Large Language Models | https://doi.org/10.1145/3779212.3790183 | https://arxiv.org/pdf/2512.15766 | https://github.com/Git-zyj/LOOPRAG | ml-for-systems | Retrieval-augmented LLM loop transformation with compile-and-check validation; CPU-only pipeline |
| 23 | cuJSON: A Highly Parallel JSON Parser for GPUs | https://doi.org/10.1145/3760250.3762222 | https://dl.acm.org/doi/pdf/10.1145/3760250.3762222 | https://github.com/AutomataLab/cuJSON | other-userspace | Massively parallel JSON parser for GPUs; user-space single-GPU artifact |
| 24 | Lobster: A GPU-Accelerated Framework for Neurosymbolic Programming | https://doi.org/10.1145/3760250.3762232 | https://arxiv.org/pdf/2503.21937 | https://github.com/P-bibs/Lobster | ml-systems | End-to-end GPU execution of a Datalog-based neurosymbolic language; user-space, single GPU |
| 25 | Skyler: Static Analysis for Predicting API-Driven Costs in Serverless Applications | https://doi.org/10.1145/3779212.3790221 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790221 | https://github.com/cloudsys-dpss-inescid/Skyler | other-userspace | Static cost analysis tool for serverless applications; user-space Java/Python tooling. Concern: it is a static analyzer rather than a runtime system so the improvement axis is analysis precision |
| 26 | Wax: Optimizing Data Center Applications With Stale Profile | https://doi.org/10.1145/3779212.3790248 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790248 | https://github.com/ice-rlab/Wax | other-userspace | Matching stale profiles to new binaries for data-center PGO; user-space compiler work. Concern: collecting fresh profiles normally needs perf/LBR sampling which is blocked, so the project depends on the shipped profiles |
| 27 | M2XFP: A Metadata-Augmented Microscaling Data Format for Efficient Low-bit Quantization | https://doi.org/10.1145/3779212.3790185 | https://arxiv.org/pdf/2601.19213 | https://github.com/SJTU-ReArch-Group/M2XFP_ASPLOS26 | llm-inference | Metadata-augmented microscaling quantization; the released artifact is a pseudo-quantization and perplexity workflow on vLLM that fits one 24 GB GPU. Concern: the speedup claims rest on a hardware unit that cannot be built here |
| 28 | Cheddar: A Swift Fully Homomorphic Encryption Library Designed for GPU Architectures | https://doi.org/10.1145/3760250.3762223 | https://arxiv.org/pdf/2407.13055 | https://github.com/scale-snu/cheddar-fhe | other-userspace | CUDA CKKS library; pure user-space GPU code that fits a single A5000 |
| 29 | CHEHAB RL: Learning to Optimize Fully Homomorphic Encryption Computations | https://doi.org/10.1145/3779212.3790138 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790138 | https://github.com/Abderraouf-D/CHEHAB_FHE_Compiler_RL | ml-for-systems | Reinforcement learning to drive an FHE compiler optimizer; CPU-only, user-space learned-tuning system |
| 30 | CEMU: Enabling Full-System Emulation of Computational Storage beyond Hardware Limits | https://doi.org/10.1145/3779212.3790137 | https://dl.acm.org/doi/pdf/10.1145/3779212.3790137 | https://github.com/cs-qyzhang/CEMU | storage | Emulator for computational-storage devices, a user-space storage research vehicle. Concern: QEMU-based full-system emulation without /dev/kvm falls back to TCG and will be slow |

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | Towards High-Goodput LLM Serving with Prefill-decode Multiplexing | out-no-code | GitHub repository search for MuxWise and for the paper title returns nothing and neither the arXiv page (2504.14489) nor the ACM page links an artifact |
| 2 | Bullet: Boosting GPU Utilization for LLM Serving via Dynamic Spatial-Temporal Orchestration | included | Single-GPU spatial-temporal sharing of prefill and decode - exactly the kind of intra-GPU serving mechanism one A5000 can host with a 7B model |
| 3 | QoServe: Breaking the Silos of LLM Inference Serving | included | QoS-driven scheduling on top of Sarathi-Serve; artifact is the niyama_asplos2026 branch. Concern: paper evaluates an A100 cluster so a single-replica scale-down is needed |
| 4 | Shift Parallelism: Low-Latency, High-Throughput LLM Inference for Dynamic Workloads | out-machine | Shift Parallelism is defined as switching between tensor and sequence parallelism across GPUs; it needs at least two GPUs and the ArcticInference artifact is built for multi-GPU nodes |
| 5 | XY-Serve: End-to-End Versatile Production Serving for Dynamic LLM Workloads | out-machine | XY-Serve is an Ascend NPU native serving stack built on tile-based DSA kernels; no CUDA path |
| 6 | PAT: Accelerating LLM Decoding via Prefix-Aware Attention with Resource Efficient Multi-Tile Kernel | included | Prefix-aware attention decode kernel; pure CUDA/Triton kernel work that runs on one Ampere GPU. Zenodo AE artifact 10.5281/zenodo.18217189 |
| 7 | ZipServ: Fast and Memory-Efficient LLM Inference with Hardware-Aware Lossless Compression | included | Lossless weight compression plus fused decompress-GEMM kernels; Tensor-Core path exists on Ampere. Concern: FP8/FP4 variants would need Ada or Hopper |
| 8 | BlendServe: Optimizing Offline Inference with Resource-Aware Batching | out-no-code | Checked the arXiv page (2411.16102), the ACM DL entry and GitHub repository search for BlendServe; no official implementation is released |
| 9 | BAT: Efficient Generative Recommender Serving with Bipartite Attention | out-no-code | Checked GitHub repository search for BAT and for bipartite attention generative recommender plus the ACM DL entry; no artifact found |
| 10 | MoE-APEX: An Efficient MoE Inference System with Adaptive Precision Expert Offloading | out-no-code | Only a third-party reproduction repo exists on GitHub; no official MoE-APEX artifact from the authors |
| 11 | PowerMove: Optimizing Compilation for Neutral Atom Quantum Computers with Zoned Architecture | out-topic | Neutral-atom quantum compiler |
| 12 | Reconfigurable Quantum Instruction Set Computers for High Performance Attainable on Hardware | out-topic | Quantum ISA design |
| 13 | QTurbo: A Robust and Efficient Compiler for Analog Quantum Simulation | out-topic | Analog quantum simulation compiler |
| 14 | Reducing T Gates with Unitary Synthesis | out-topic | Quantum gate synthesis |
| 15 | Borrowing Dirty Qubits in Quantum Programs | out-topic | Quantum program qubit reuse |
| 16 | HybridTier: An Adaptive and Lightweight CXL-Memory Tiering System | out-machine | CXL-attached memory tiering; needs a real CXL memory device plus kernel-level page migration, both ruled out |
| 17 | vCXLGen: Automated Synthesis and Verification of CXL Bridges for Heterogeneous Architectures | out-topic | Hardware synthesis and verification of CXL bridge RTL |
| 18 | CXLMC: Model Checking CXL Shared Memory Programs | out-topic | Model checking of CXL memory-consistency programs; formal methods rather than a systems artifact |
| 19 | A Programming Model for Disaggregated Memory over CXL | out-machine | Programming model for CXL-attached disaggregated memory; requires CXL hardware |
| 20 | Cxlalloc: Safe and Efficient Memory Allocation for a CXL Pod | out-machine | Allocator for a multi-host CXL pod; requires CXL shared memory hardware |
| 21 | SNIP: An Adaptive Mixed Precision Framework for Subbyte Large Language Model Training | included | Adaptive mixed-precision LLM training policy; authors themselves evaluate with a pseudo-quantization proxy because they lack Blackwell, so it is GPU-portable. Concern: pretraining compute must be scaled to small models |
| 22 | Fine-grained and Non-intrusive LLM Training Monitoring via Microsecond-level Traffic Measurement | out-machine | Pulse does microsecond RDMA traffic measurement on NICs across a multi-node training cluster |
| 23 | SuperOffload: Unleashing the Power of Large-Scale LLM Training on Superchips | out-machine | Targets Grace-Hopper superchips and NVLink-C2C; no equivalent on this machine |
| 24 | DIP: Efficient Large Multimodal Model Training with Dynamic Interleaved Pipeline | out-machine | Interleaved pipeline parallelism for multimodal training across many GPUs |
| 25 | Dynamic Sparsity in Large-Scale Video DiT Training | out-machine | Large-scale video DiT training with context parallelism; a 24 GB single GPU cannot train video diffusion transformers even scaled down |
| 26 | DFVG: A Heterogeneous Architecture for Speculative Decoding with Draft-on-FPGA and Verify-on-GPU | out-machine | Draft model runs on an FPGA |
| 27 | SwiftSpec: Disaggregated Speculative Decoding and Fused Kernels for Low-Latency LLM Inference | out-machine | Disaggregates draft and target models across GPUs in an 8xH800 node and uses NCCL low-latency primitives; no single-GPU form |
| 28 | SpeContext: Enabling Efficient Long-context Reasoning with Speculative Context Sparsity in LLMs | out-no-code | Checked GitHub repository search for SpeContext and the arXiv page 2512.00722; no released implementation found |
| 29 | SpecProto: A Parallelizing Compiler for Speculative Decoding of Large Protocol Buffers Data | included | Parallelizing compiler for Protobuf decoding; CPU-only artifact that targets 16 physical cores which this machine has |
| 30 | EARTH: An Efficient MoE Accelerator with Entropy-Aware Speculative Prefetch and Result Reuse | out-topic | MoE hardware accelerator design |
| 31 | gShare: Efficient GPU Sharing with Aggressive Scheduling in Multi-tenant FaaS platform | out-no-code | Checked GitHub repository search for gShare and for GPU sharing in multi-tenant FaaS; no official artifact found |
| 32 | GFS: A Preemption-aware Scheduling Framework for GPU Clusters with Predictive Spot Instance Management | included | Preemption-aware GPU-cluster scheduler with demand forecasting; policy work that can be studied trace-driven or in simulation. Concern: repo has no README yet and the paper evaluates a real cluster |
| 33 | Asynchrony and GPUs: Bridging this Dichotomy for I/O with AGIO | out-no-code | Checked GitHub repository search for AGIO and asynchronous GPU I/O; no official artifact found |
| 34 | MSCCL++: Rethinking GPU Communication Abstractions for AI Inference | out-machine | Communication library for multi-GPU and multi-node AI inference; the whole contribution is cross-device collectives |
| 35 | Insum: Sparse GPU Kernels Simplified and Optimized with Indirect Einsums | included | Sparse GPU kernel compiler lowering indirect Einsums through the PyTorch compiler; single-GPU, user-space |
| 36 | RowArmor: Efficient and Comprehensive Protection Against DRAM Disturbance Errors | out-topic | In-DRAM read-disturbance mitigation hardware |
| 37 | APT: Securing Against DRAM Read Disturbance via Adaptive Probabilistic In-DRAM Trackers | out-topic | In-DRAM probabilistic tracker hardware |
| 38 | STRAW: Stress-Aware WL-Based Read Disturbance Management for High-Density NAND Flash Memory | out-topic | In-SSD wordline-level read-reclaim policy inside the flash controller |
| 39 | Trust-V: Toward Secure and Reliable Storage for Trusted Execution Environments | out-machine | Secure storage for TEEs; requires trusted execution hardware |
| 40 | Optimizer-Friendly Instrumentation for Event Quantification with PRUE Algorithm | out-no-code | Checked GitHub repository search for PRUE and for the paper title; no released instrumentation artifact found |
| 41 | I/O Analysis is All You Need: An I/O Analysis for Long-Sequence Attention | out-no-code | Checked GitHub repository search and the ACM DL entry for this I/O analysis of long-sequence attention; no artifact released |
| 42 | REPA: Reconfigurable PIM for the Joint Acceleration of KV Cache Offloading and Processing | out-topic | Reconfigurable processing-in-memory hardware |
| 43 | STARC: Selective Token Access with Remapping and Clustering for Efficient LLM Decoding on PIM Systems | out-topic | PIM-based KV-cache decoding; evaluated on a Ramulator/AttAcc PIM simulator, not real hardware this machine has |
| 44 | Mugi: Value Level Parallelism For Efficient LLMs | out-topic | Value-level-parallelism microarchitecture for LLMs |
| 45 | TPLA: Tensor Parallel Latent Attention for Efficient Disaggregated Prefill & Decode Inference | out-no-code | Checked GitHub repository search for TPLA and tensor parallel latent attention plus the ACM DL entry; no artifact found. It also assumes multi-device tensor parallelism |
| 46 | LAER-MoE: Load-Adaptive Expert Re-layout for Efficient Mixture-of-Experts Training | out-machine | Expert-parallel MoE training; the artifact requires a 4-node cluster of 8xA100 with InfiniBand |
| 47 | oFFN: Outlier and Neuron-aware Structured FFN for Fast yet Accurate LLM Inference | out-no-code | Checked GitHub repository search for oFFN and outlier neuron-aware FFN; no artifact found |
| 48 | MoDM: Efficient Serving for Image Generation via Mixture-of-Diffusion Models | included | Caching-based serving for diffusion models; retrieval cache plus small/large model mix. Concern: artifact assumes a 48 GB A40 so SDXL-class models need scale-down or offload on 24 GB |
| 49 | Taming the Long-Tail: Efficient Reasoning RL Training with Adaptive Drafter | out-machine | Reasoning RL training with an adaptive drafter trained on idle GPUs; the mechanism needs spare GPUs and the paper runs on 8xH100. GRPO on 24 GB is only possible at toy scale |
| 50 | FastTTS: Accelerating Test-Time Scaling for Edge LLM Reasoning | included | Test-time-scaling serving framework built as a vLLM plug-in for memory-constrained devices; a 24 GB GPU is a realistic target |
| 51 | GS-Scale: Unlocking Large-Scale 3D Gaussian Splatting Training via Host Offloading | included | Host-offloading 3DGS training explicitly aimed at consumer GPUs; 125 GiB host RAM plus one 24 GB GPU is the intended setting |
| 52 | Neo: Real-Time On-Device 3D Gaussian Splatting with Reuse-and-Update Sorting Acceleration | out-topic | On-device 3DGS sorting accelerator hardware |
| 53 | CLM: Removing the GPU Memory Barrier for 3D Gaussian Splatting | included | CPU-offloading for 3DGS on a single consumer GPU - the paper itself targets one RTX 4090 |
| 54 | Nebula: Infinite-Scale 3D Gaussian Splatting in VR via Collaborative Rendering and Accelerated Stereo Rasterization | out-machine | VR collaborative rendering with a custom stereo rasterization accelerator and a headset |
| 55 | AGS: Accelerating 3D Gaussian Splatting SLAM via CODEC-Assisted Frame Covisibility Detection | out-topic | Algorithm-hardware co-design with a CODEC-assisted accelerator for 3DGS SLAM |
| 56 | Detecting Inconsistencies in ARM CCA’s Formally Verified Specification | out-topic | Formal specification checking of Arm CCA firmware |
| 57 | WorksetEnclave: Towards Optimizing Cold Starts in Confidential Serverless with Workset-Based Enclave Restore | out-machine | Confidential serverless cold starts on Intel SGX enclaves |
| 58 | TEEM³: Core-Independent and Cooperating Trusted Execution Environments | out-machine | Runs on a custom hardware platform; the artifact requires a Xilinx VCU118 FPGA |
| 59 | WAVE: Leveraging Architecture Observation for Privacy-Preserving Model Oversight | out-machine | Monitors LLM inference with GPU performance counters collected through Nsight Compute; PMC access is not available |
| 60 | Compass: Navigating the Design Space of Taint Schemes for RTL Security Verification | out-topic | RTL security verification taint schemes |
| 61 | T-Control: An Efficient Dynamic Tensor Rematerialization System for DNN Training | out-no-code | Checked GitHub repository search for T-Control and dynamic tensor rematerialization plus the ACM DL entry; no artifact found |
| 62 | NotebookOS: A Replicated Notebook Platform for Interactive Training with On-Demand GPUs | out-machine | Raft-replicated notebook kernels spread over multiple GPU servers; the artifact is an AWS multi-node deployment |
| 63 | DeepContext: A Context-aware, Cross-platform, and Cross-framework Tool for Performance Profiling and Analysis of Deep Learning Workloads | out-machine | Cross-platform DL profiler that correlates with hardware performance metrics through CUPTI/PAPI-style counters, which are blocked here; no public artifact either |
| 64 | Triton-Sanitizer: A Fast and Device-Agnostic Memory Sanitizer for Triton with Rich Diagnostic Context | included | Device-agnostic memory sanitizer for Triton kernels; user-space, single GPU. Concern: the AE scripts assume a ROCm Docker image so the NVIDIA path needs porting since Docker is unavailable |
| 65 | LAIKA: Machine Learning-Assisted In-Kernel APU Acceleration | out-machine | In-kernel ML acceleration on an APU integrated GPU; needs kernel code and an APU |
| 66 | FuseFlow: A Fusion-Centric Compilation Framework for Sparse Deep Learning on Streaming Dataflow | out-topic | Sparse DL compiler targeting reconfigurable dataflow accelerators and a cycle-accurate dataflow simulator; no CPU or GPU backend |
| 67 | Trinity: Three-Dimensional Tensor Program Optimization via Tile-level Equality Saturation | included | Tile-level equality saturation tensor compiler emitting Triton kernels; single-GPU compile-and-benchmark loop |
| 68 | RedFuser: An Automatic Operator Fusion Framework for Cascaded Reductions on AI Accelerators | out-machine | Operator fusion framework for Ascend-class AI accelerators |
| 69 | Linear Layouts: Robust Code Generation of Efficient Tensor Computation Using F2 | included | Linear-algebra formulation of tensor layouts inside the Triton compiler; implementation is upstream in Triton so it builds and runs on one Ampere GPU |
| 70 | Streaming Tensor Program: A streaming abstraction for dynamic parallelism | out-topic | Streaming abstraction for spatial dataflow accelerators |
| 71 | AlphaSyndrome: Tackling the Syndrome Measurement Circuit Scheduling Problem for QEC Codes | out-topic | Quantum error correction circuit scheduling |
| 72 | PropHunt: Automated Optimization of Quantum Syndrome Measurement Circuits | out-topic | Quantum syndrome measurement circuit optimization |
| 73 | iSwitch: QEC on Demand via In-Situ Encoding of Bare Qubits for Ion Trap Architectures | out-topic | Trapped-ion QEC architecture |
| 74 | Architecting Scalable Trapped Ion Quantum Computers using Surface Codes | out-topic | Trapped-ion surface-code architecture |
| 75 | Accelerating Computation in Quantum LDPC Code | out-topic | Quantum LDPC decoding |
| 76 | DARTH-PUM: A Hybrid Processing-Using-Memory Architecture | out-topic | Processing-using-memory architecture |
| 77 | PUSHtap: PIM-based In-Memory HTAP with Unified Data Storage Format | out-topic | PIM-based HTAP hardware |
| 78 | CoGraf: Fully Accelerating Graph Applications with Fine-Grained PIM | out-topic | Fine-grained PIM graph accelerator |
| 79 | Ouroboros: Wafer-Scale SRAM CIM with Token-Grained Pipelining for Large Language Model Inference | out-topic | Wafer-scale SRAM compute-in-memory |
| 80 | A Cost-Effective Near-Storage Processing Solution for Offline Inference of Long-Context LLMs | out-machine | Near-storage processing accelerators for long-context LLM inference; requires computational storage hardware |
| 81 | TetriServe: Efficiently Serving Mixed DiT Workloads | out-machine | Step-level sequence parallelism that reallocates GPUs per request; the artifact is a multi-GPU diffusion serving system |
| 82 | Segment Only Where You Look: Leveraging Human Gaze Behavior for Efficient Computer Vision Applications in Augmented Reality | out-machine | Needs an AR headset with eye tracking |
| 83 | Compositional AI Beyond LLMs: System Implications of Neuro-Symbolic-Probabilistic Architectures | out-topic | Workload characterization and system-implications study of neuro-symbolic-probabilistic stacks rather than a reusable system artifact |
| 84 | It Takes Two to Entangle | included | Equivalence checker that relates sequential and distributed ML computation graphs; the artifact itself is a user-space analysis tool. Concern: the motivating bugs come from multi-GPU training runs |
| 85 | Tilus: A Tile-Level GPGPU Programming Language for Low-Precision Computation | included | Tile-level GPGPU DSL for low-precision kernels; Ampere is a supported target. Concern: some tutorials target Blackwell-only features |
| 86 | Neuralink: Fast on-Device LLM Inference with Neuron Co-Activation Linking | out-no-code | Checked GitHub repository search for Neuralink neuron co-activation linking and the ACM DL entry; no artifact found. It also targets smartphone flash IOPS behaviour |
| 87 | Lifetime-Aware Design for Item-Level Intelligence at the Extreme Edge | out-topic | Flexible printed electronics for extreme-edge items |
| 88 | FlashMem: Supporting Modern DNN Workloads on Mobile with GPU Memory Hierarchy Optimizations | out-machine | Mobile GPU memory hierarchy optimizations; needs a smartphone SoC |
| 89 | ASDR: Exploiting Adaptive Sampling and Data Reuse for CIM-based Instant Neural Rendering | out-topic | Compute-in-memory neural rendering accelerator |
| 90 | BitRed: Taming Non-Uniform Bit-Level Sparsity with a Programmable RISC-V ISA for DNN Acceleration | out-topic | RISC-V ISA extension for DNN acceleration |
| 91 | Graphiti: Formally Verified Out-of-Order Execution in Dataflow Circuits | out-topic | Formal verification of dataflow circuits |
| 92 | Highly Automated Verification of Security Properties for Unmodified System Software | out-topic | Automated verification of system software security properties |
| 93 | SylQ-SV: Scaling Symbolic Execution of Hardware Designs with Query Caching | out-topic | Symbolic execution of hardware designs |
| 94 | Once-for-All: Skeleton-Guided SMT Solver Fuzzing with LLM-Synthesized Generators | out-topic | SMT solver fuzzing |
| 95 | LPO: Discovering Missed Peephole Optimizations with Large Language Models | included | LLM proposes LLVM peephole rewrites that Alive2 verifies; entirely user-space and CPU-bound. Concern: needs an LLM API budget and is closer to compilers than to classic systems |
| 96 | Nemo: A Low-Write-Amplification Cache for Tiny Objects on Log-Structured Flash Devices | included | Set-associative flash-cache design built as a CacheLib module; runs in user space on the local NVMe drives |
| 97 | ICARUS: Criticality and Reuse based Instruction Caching for Datacenter Applications | out-topic | Instruction-cache microarchitecture |
| 98 | CacheMind: From Miss Rates to Why – Natural-Language, Trace-Grounded Reasoning for Cache Replacement | included | LLM plus RAG reasoning over cache traces with a released benchmark; trace-driven and CPU-only. Concern: the repo is author-named and not linked from the paper so ownership is unconfirmed |
| 99 | Toasty: Speeding up network I/O with cache-warm buffers | out-machine | Cache-warm network buffers; the mechanism lives in the kernel network stack and depends on DDIO behaviour |
| 100 | Hitchhike: Efficient Request Submission via Deferred Enforcement of Address Contiguity | out-machine | Requires specific PCIe 4.0/5.0 NVMe SSDs and ships a modified Linux kernel (Hitchhike-Linux) which cannot be installed without root |
| 101 | History Doesn’t Repeat Itself but Rollouts Rhyme: Accelerating Reinforcement Learning with HistoRL | out-machine | RhymeRL accelerates rollout in large-scale LLM RL training across many GPU workers; also no public artifact was found |
| 102 | Hardwired-Neuron Language Processing Units as General-Purpose Cognitive Substrates | out-topic | Hardwired-neuron processing unit architecture |
| 103 | Voyager: Input-Adaptive Algebraic Transformations for High-Performance Graph Neural Networks | out-no-code | Checked GitHub repository search for Voyager input-adaptive algebraic GNN transformations and the ACM DL entry; no artifact found |
| 104 | CREATE: Cross-Layer Resilience Characterization and Optimization for Efficient yet Reliable Embodied AI Systems | out-topic | Cross-layer resilience characterization for embodied AI hardware |
| 105 | Syno: Structured Synthesis for Neural Operators | included | Structured synthesis of neural operators; search plus single-GPU kernel evaluation. Published in ASPLOS 2025 Volume 3 and presented at ASPLOS 2026 |
| 106 | Parameterized Hardware Design with Latency-Abstract Interfaces | out-topic | Hardware design language |
| 107 | Anvil: A General-Purpose Timing-Safe Hardware Description Language | out-topic | Hardware description language |
| 108 | Rage Against the State Machine: Type-Stated Hardware Peripherals for Increased Driver Correctness | out-topic | Type-stated hardware peripheral drivers; HDL/embedded PL work |
| 109 | RTeAAL Sim: Using Tensor Algebra to Represent and Accelerate RTL Simulation | out-topic | RTL simulation acceleration |
| 110 | Sequential Specifications for Precise Hardware Exceptions | out-topic | Hardware exception specifications |
| 111 | TempGraph: An Efficient Chain-driven Temporal Graph Computing Framework on the GPU | out-no-code | Checked GitHub repository search for TempGraph chain-driven temporal graph framework and the ACM DL entry; no artifact found |
| 112 | Leveraging Sparsity to Accelerate Automata Processing | out-topic | Automata-processing accelerator (Hopps) |
| 113 | SLAWS: Spatial Locality Analysis and Workload Orchestration for Sparse Matrix Multiplication | out-topic | Sparse matrix multiplication accelerator orchestration |
| 114 | Efficient Temporal Graph Network Training via Unified Redundancy Elimination | out-no-code | Checked GitHub repository search for temporal graph network redundancy elimination training and the ACM DL entry; no artifact found |
| 115 | Understanding Query Optimization Bugs in Graph Database Systems | out-topic | Empirical bug study of graph database query optimizers |
| 116 | Efficient Remote Memory Ordering for Non-Coherent Systems | out-machine | Remote memory ordering for non-coherent disaggregated systems; needs multi-host hardware |
| 117 | CPU-Oblivious Offloading of Failure-Atomic Transactions for Disaggregated Memory | out-machine | Failure-atomic transactions offloaded in a disaggregated memory fabric |
| 118 | PIPM: Partial and Incremental Page Migration for Multi-host CXL Disaggregated Shared Memory | out-machine | Multi-host CXL disaggregated shared memory page migration |
| 119 | CREST: High-Performance Contention Resolution for Disaggregated Transactions | out-machine | Disaggregated transaction contention resolution over RDMA-class fabrics |
| 120 | Understanding and Optimizing Database Pushdown on Disaggregated Storage | out-machine | Database pushdown on disaggregated storage; TapDB needs separate compute and storage nodes |
| 121 | A Framework for Developing and Optimizing Fully Homomorphic Encryption Programs on GPUs | out-no-code | Checked GitHub repository search for this FHE-on-GPU compilation framework and the ACM DL entry; no artifact found |
| 122 | HEPIC: Private Inference over Homomorphic Encryption with Client Intervention | out-no-code | Checked GitHub repository search for HEPIC private inference over homomorphic encryption and the ACM DL entry; no artifact found |
| 123 | Falcon: Algorithm-Hardware Co-Design for Efficient Fully Homomorphic Encryption Accelerator | out-topic | FHE hardware accelerator |
| 124 | Maverick: Rethinking TFHE Bootstrapping on GPUs via Algorithm-Hardware Co-Design | out-topic | Algorithm-hardware co-design for TFHE bootstrapping; the contribution is an accelerator design |
| 125 | COGENT: Adaptable Compiler Toolchain for Tagging RISC-V Binaries | out-topic | RISC-V binary tagging compiler toolchain for hardware tag extensions |
| 126 | Finding Reusable Instructions via E-Graph Anti-Unification | out-topic | ISA extension synthesis via e-graph anti-unification |
| 127 | LOOPRAG: Enhancing Loop Transformation Optimization with Retrieval-Augmented Large Language Models | included | Retrieval-augmented LLM loop transformation with compile-and-check validation; CPU-only pipeline |
| 128 | Evaluating Compiler Optimization Impacts on zkVM Performance | out-topic | Measurement study of compiler flags on zkVM performance |
| 129 | DejaVuzz: Disclosing Transient Execution Bugs with Dynamic Swappable Memory and Differential Information Flow Tracking assisted Processor Fuzzing | out-topic | Processor fuzzing for transient execution bugs |
| 130 | Signal Breaker: Fuzzing Digital Signal Processors | out-topic | DSP fuzzing |
| 131 | Scaling Automated Database System Testing | out-topic | Automated DBMS testing |
| 132 | SEVI: Silent Data Corruption of Vector Instructions in Hyper-Scale Datacenters | out-machine | Silent data corruption study that needs a hyperscale fleet of CPUs |
| 133 | Co-Exploration of RISC-V Processor Microarchitectures and FreeRTOS Extensions for Lower Context Switch Latency | out-topic | RISC-V microarchitecture and RTOS co-exploration |
| 134 | Chips Need DIP: Time-Proportional Per-Instruction Cycle Stacks at Dispatch | out-topic | Per-instruction cycle stacks in the processor pipeline |
| 135 | Arm Weak Memory Consistency on Apple Silicon: What Is It Good For? | out-machine | Measurement of Arm weak memory behaviour on Apple Silicon hardware |
| 136 | A Data-Driven Dynamic Execution Orchestration Architecture | out-topic | Dynamic execution orchestration architecture |
| 137 | cuJSON: A Highly Parallel JSON Parser for GPUs | included | Massively parallel JSON parser for GPUs; user-space single-GPU artifact |
| 138 | CHERI-SIMT: Implementing Capability Memory Protection in GPGPUs | out-machine | CHERI capability hardware for GPGPUs; evaluated on an FPGA SIMT core |
| 139 | Lobster: A GPU-Accelerated Framework for Neurosymbolic Programming | included | End-to-end GPU execution of a Datalog-based neurosymbolic language; user-space, single GPU |
| 140 | ReliaFHE: Resilient Design for Fully Homomorphic Encryption Accelerators | out-topic | Resilience design for FHE accelerators |
| 141 | Lambda-trim: Reducing Monetary and Performance Cost of Serverless Cold Starts with Cost-driven Application Debloating | out-no-code | Checked GitHub repository search for Lambda-trim and lambda-trim serverless debloating and the ACM DL entry; no artifact found |
| 142 | Skyler: Static Analysis for Predicting API-Driven Costs in Serverless Applications | included | Static cost analysis tool for serverless applications; user-space Java/Python tooling. Concern: it is a static analyzer rather than a runtime system so the improvement axis is analysis precision |
| 143 | Enabling fast networking in the public cloud | out-machine | Kernel-bypass networking evaluated on public-cloud VMs with specific NIC support |
| 144 | SG-IOV: Socket-Granular I/O Virtualization for SmartNIC-Based Container Networks | out-machine | SmartNIC-based I/O virtualization |
| 145 | PACT: A Criticality-First Design for Tiered Memory | out-machine | Criticality-first tiered memory placement; needs a real slow memory tier plus hardware access sampling, and this host has one NUMA node and no perf counters |
| 146 | CounterPoint: Using Hardware Event Counters to Refute and Refine Microarchitectural Assumptions | out-machine | The entire method is built on hardware event counters, which are blocked by perf_event_paranoid=3 |
| 147 | Performance Predictability in Heterogeneous Memory | out-machine | CAMP predicts slowdown from up to 12 hardware performance counters on a DRAM plus CXL system |
| 148 | PF-LLM: Large Language Model Hinted Hardware Prefetching | out-no-code | Checked GitHub repository search for PF-LLM and LLM-hinted hardware prefetching and the ACM DL entry; no artifact found |
| 149 | Neura: A Unified Framework for Hierarchical and Adaptive CGRAs | out-topic | CGRA architecture framework |
| 150 | Transforming Torus Fabrics for Efficient Multi-tenant ML | out-topic | Torus interconnect fabric for multi-tenant ML accelerators |
| 151 | The Configuration Wall: Characterization and Elimination of Accelerator Configuration Overhead | out-topic | Accelerator configuration overhead |
| 152 | Static Analysis for Efficient Streaming Tokenization | out-no-code | Checked GitHub repository search for static analysis for streaming tokenization and the ACM DL entry; no artifact found |
| 153 | Arancini: A Hybrid Binary Translator for Weak Memory Model Architectures | out-machine | Arancini translates x86-64 binaries to run on Arm hosts; it needs an Arm machine to evaluate |
| 154 | Wax: Optimizing Data Center Applications With Stale Profile | included | Matching stale profiles to new binaries for data-center PGO; user-space compiler work. Concern: collecting fresh profiles normally needs perf/LBR sampling which is blocked, so the project depends on the shipped profiles |
| 155 | M2XFP: A Metadata-Augmented Microscaling Data Format for Efficient Low-bit Quantization | included | Metadata-augmented microscaling quantization; the released artifact is a pseudo-quantization and perplexity workflow on vLLM that fits one 24 GB GPU. Concern: the speedup claims rest on a hardware unit that cannot be built here |
| 156 | Cheddar: A Swift Fully Homomorphic Encryption Library Designed for GPU Architectures | included | CUDA CKKS library; pure user-space GPU code that fits a single A5000 |
| 157 | COMPAS: A Distributed Multi-Party SWAP Test for Parallel Quantum Algorithms | out-topic | Distributed quantum algorithm |
| 158 | TreeVQA: A Tree-Structured Execution Framework for Shot Reduction in Variational Quantum Algorithms | out-topic | Variational quantum algorithm execution |
| 159 | CHEHAB RL: Learning to Optimize Fully Homomorphic Encryption Computations | included | Reinforcement learning to drive an FHE compiler optimizer; CPU-only, user-space learned-tuning system |
| 160 | CEMU: Enabling Full-System Emulation of Computational Storage beyond Hardware Limits | included | Emulator for computational-storage devices, a user-space storage research vehicle. Concern: QEMU-based full-system emulation without /dev/kvm falls back to TCG and will be slow |
| 161 | Fault Escaping: Improving Robustness of DPU Enhanced Platform with Mutual Assisted VM Recovery | out-machine | DPU-assisted VM recovery; requires a DPU and hypervisor access |
| 162 | Radshield: Software Radiation Protection for Commodity Hardware in Space | out-topic | Software radiation fault tolerance for spacecraft; none of the scope topics cover it and no official artifact was found |
| 163 | TierX: A Simulation Framework for Multi-tier BCI System Design Evaluation and Exploration | out-topic | Brain-computer-interface system simulation framework |
| 164 | PrioriFI: More Informed Fault Injection for Edge Neural Networks | out-topic | Fault injection for edge neural network reliability |
| 165 | TiNA: Tiered Network Buffer Architecture for Fast Networking in Chiplet-based CPU | out-topic | Chiplet network buffer architecture |
| 166 | An MLIR Lowering Pipeline for Stencils at Wafer-Scale | out-machine | MLIR stencil lowering for the Cerebras wafer-scale engine |
| 167 | JOSer: Just-In-Time Object Serialization for Heavy Java Serialization Workloads | out-no-code | Checked GitHub repository search for JOSer just-in-time object serialization and the ACM DL entry; no artifact found |
| 168 | Wave: Offloading Resource Management to SmartNIC Cores | out-machine | Offloads resource management onto SmartNIC cores |
