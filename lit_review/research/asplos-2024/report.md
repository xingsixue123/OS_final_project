STATUS: complete
TOTAL_PAPERS: 194
INCLUDED: 31

## Sources

- Official ASPLOS 2024 main program: `https://www.asplos-conference.org/asplos2024/main-program/index.html` (fetched with curl and parsed; gives title, authors and the DOI of every talk) and the companion abstracts page `https://www.asplos-conference.org/asplos2024/main-program/abstracts/index.html` (189 abstracts).
- Crossref REST API (`api.crossref.org`), used as the authoritative table of contents. ASPLOS 2024 is the 29th conference and has **four** proceedings volumes: Volume 1 `10.1145/3617232` (28 papers), Volume 2 `10.1145/3620665` (76), Volume 3 `10.1145/3620666` (70, of which 4 entries are keynote abstracts), Volume 4 `10.1145/3622781` (24). Total main-track papers = 28 + 76 + 66 + 24 = **194**.
- Cross-check: the program page lists 169 talks with DOIs in Volumes 1-3, which matches Crossref exactly once the 4 keynote entries are removed (28 + 75 + 66, the one apparent gap being FOCAL whose title cell is wrapped in an award badge). The 24 Volume-4 papers do not appear in the 2024 program because they were presented at ASPLOS 2025; they are nevertheless ASPLOS '24 (29th conference) proceedings papers and are included here.
- Papers in the 2024 program carrying DOI prefix `10.1145/3623278` (23 of them) belong to **ASPLOS '23 Volume 4** (28th conference) and were deliberately excluded from this venue-year; they belong to the ASPLOS 2023 scout.
- DBLP (`dblp.org/db/conf/asplos/asplos2024-*`) was attempted but is behind an anti-bot challenge; ACM DL is behind Cloudflare. Crossref plus the official program were used instead.
- Code checks: GitHub repository search API, targeted web searches, artifact links on author/lab pages, and grepping author-copy / arXiv PDFs for `github`, `gitlab` and `zenodo` URLs.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | Amanda: Unified Instrumentation Framework for Deep Neural Networks | https://doi.org/10.1145/3617232.3624864 | https://horizon-lab.org/pubs/asplos24-amanda.pdf | https://github.com/uchuhimo/amanda | ml-systems | User-space operator-level instrumentation layer over PyTorch/TensorFlow; pure Python/C++ extension, single GPU is enough. Easy to extend with new instrumentation tools. |
| 2 | Loupe: Driving the Development of OS Compatibility Layers | https://doi.org/10.1145/3617232.3624861 | https://arxiv.org/pdf/2309.15996 | https://github.com/unikraft/loupe | other-userspace | Dynamic syscall-usage analysis for OS compatibility layers; user-space ptrace/seccomp tooling plus a public results database. Concern - upstream harness wraps runs in Docker so it must be ported to a conda/bwrap setup. |
| 3 | ngAP: Non-blocking Large-scale Automata Processing on GPUs | https://doi.org/10.1145/3617232.3624848 | https://getianao.github.io/papers/asplos24ngap.pdf | https://github.com/getianao/ngAP | other-userspace | GPU automata-processing engine; artifact was tested on an RTX 3090 (Ampere 24 GB) which matches the A5000 almost exactly. Clear room for scheduling/memoization improvements. |
| 4 | Optimizing Deep Learning Inference via Global Analysis and Tensor Expressions | https://doi.org/10.1145/3617232.3624858 | https://cuihuimin.github.io/papers/asplos24spring.pdf | https://github.com/summerspringwei/souffle-ae | ml-systems | Inter-operator DNN inference compiler; single NVIDIA GPU evaluation. Concern - artifact is packaged with Docker files that must be reproduced with conda/pip since Docker is unavailable. |
| 5 | Proteus: A High-Throughput Inference-Serving System with Accuracy Scaling | https://doi.org/10.1145/3617232.3624849 | unknown | https://github.com/UMass-LIDS/Proteus | ml-systems | Inference-serving system with accuracy scaling driven by real and synthetic traces. Concern - designed for a small heterogeneous cluster; would need scale-down to one GPU plus CPU workers or trace-driven simulation. |
| 6 | TrackFM: Far-out Compiler Support for a Far Memory World | https://doi.org/10.1145/3617232.3624856 | https://users.cs.northwestern.edu/~simonec/files/Research/papers/MEMORY_ASPLOS_2024.pdf | https://github.com/compiler-disagg/TrackFM | memory | LLVM compiler plus user-space runtime for far memory; no kernel changes needed on the application side. Concern - the far-memory backend was run on CloudLab; a local loopback or second-process memory server would be needed here. |
| 7 | Compiling Loop-Based Nested Parallelism for Irregular Workloads | https://doi.org/10.1145/3620665.3640405 | https://www.andrew.cmu.edu/user/mrainey/papers/HELIX_ASPLOS_2024.pdf | https://github.com/arcana-lab/heartbeatcompiler | other-userspace | LLVM/NOELLE compiler plus user-space heartbeat scheduling runtime for nested parallelism on a multicore CPU; 16C/32T Threadripper is a reasonable target. Concern - the interrupt-based rollforward variant may need a signal/timer path that should be checked. |
| 8 | GIANTSAN: Efficient Memory Sanitization with Segment Folding | https://doi.org/10.1145/3620665.3640391 | unknown | https://github.com/AceSrc/GiantSan-Artifact | other-userspace | LLVM-based memory sanitizer with a new shadow encoding; purely user-space, CPU-only. Concern - headline numbers use SPEC CPU2017 which is licensed; open benchmarks would have to substitute. |
| 9 | GMLake: Efficient and Transparent GPU Memory Defragmentation for Large-scale DNN Training with Virtual Memory Stitching | https://doi.org/10.1145/3620665.3640423 | https://www.cs.sjtu.edu.cn/~leng-jw/resources/Files/guo2024asplos-gmlake.pdf | https://github.com/antgroup/glake | memory | GPU virtual-memory stitching allocator inside the PyTorch caching allocator. Concern - paper uses A100 80 GB; on a 24 GB A5000 the study must use smaller models or LoRA/recompute settings, but the fragmentation mechanism is unchanged. |
| 10 | MaxK-GNN: Extremely Fast GPU Kernel Design for Accelerating Graph Neural Networks Training | https://doi.org/10.1145/3620665.3640426 | https://arxiv.org/pdf/2312.08656 | https://github.com/xiexi51/MaxK-GNN | ml-systems | Single-GPU SpGEMM/SSpMM kernels plus a nonlinearity for GNN training; Ampere-class GPU is the target. Fits the machine directly. |
| 11 | PyTorch 2: Faster Machine Learning Through Dynamic Python Bytecode Transformation and Graph Compilation | https://doi.org/10.1145/3620665.3640366 | https://pytorch.org/assets/pytorch2-2.pdf | https://github.com/pytorch/pytorch | ml-systems | TorchDynamo/TorchInductor (torch.compile); fully open, runs on a single GPU or CPU. Very large codebase - scope an improvement narrowly (e.g. a guard or fusion heuristic). |
| 12 | RAP: Resource-aware Automated GPU Sharing for Multi-GPU Recommendation Model Training and Input Preprocessing | https://doi.org/10.1145/3620665.3640406 | https://storage.googleapis.com/yuke_profile/ASPLOS24_RAP.pdf | https://github.com/Ash-Zheng/RAP-artifacts | ml-systems | Co-running DLRM input preprocessing with training on the same GPU via resource-aware kernel fusion. Concern - paper is multi-GPU, but the co-running cost model and horizontal fusion are per-GPU and can be studied on one A5000. |
| 13 | Slapo: A Schedule Language for Progressive Optimization of Large Deep Learning Model Training | https://doi.org/10.1145/3620665.3640399 | https://arxiv.org/pdf/2302.08005 | https://github.com/awslabs/slapo | ml-systems | Schedule language decoupling PyTorch model definition from optimization. Concern - 3D-parallelism results need many GPUs; single-GPU primitives (kernel replacement, activation checkpointing) are still evaluable. Artifact repo is chhzh123/slapo-artifact. |
| 14 | TGLite: A Lightweight Programming Framework for Continuous-Time Temporal Graph Neural Networks | https://doi.org/10.1145/3620665.3640414 | unknown | https://github.com/ADAPT-uiuc/tglite | ml-systems | Lightweight framework and TBlock abstraction for continuous-time temporal GNNs; single-GPU evaluation against TGL. |
| 15 | 8-bit Transformer Inference and Fine-tuning for Edge Accelerators | https://doi.org/10.1145/3620666.3651368 | https://openreview.net/forum?id=LWGStRcP9h | https://github.com/jeffreyyu0602/quantized-training | ml-systems | Software FP8/Posit8 quantization-emulation library for Transformer inference and LoRA fine-tuning. Concern - Ampere has no native FP8 so numerics are emulated (which is what the artifact does anyway); the accompanying edge accelerator hardware results are out of reach. |
| 16 | AUDIBLE: A Convolution-Based Resource Allocator for Oversubscribing Burstable Virtual Machines | https://doi.org/10.1145/3620666.3651376 | unknown | https://github.com/seyedali14/audible-artifact-asplos24 | scheduling | Burstable-VM oversubscription allocator evaluated by trace-driven simulation over production traces; CPU-only and squarely within the machine budget. |
| 17 | CSSTs: A Dynamic Data Structure for Partial Orders in Concurrent Execution Analysis | https://doi.org/10.1145/3620666.3651358 | https://arxiv.org/pdf/2403.17818 | https://github.com/hcantunc/cssts | other-userspace | Collective Sparse Segment Trees, a drop-in replacement for vector clocks in dynamic concurrency analyses; user-space CPU-only library with a Zenodo artifact (10.5281/zenodo.10798906). |
| 18 | DTC-SpMM: Bridging the Gap in Accelerating General Sparse Matrix Multiplication with Tensor Cores | https://doi.org/10.1145/3620666.3651378 | unknown | https://github.com/HPMLL/DTC-SpMM_ASPLOS24 | ml-systems | Tensor-core SpMM formats, reordering and pipelining; single modern NVIDIA GPU. Ampere tensor cores are supported. |
| 19 | EVT: Accelerating Deep Learning Training with Epilogue Visitor Tree | https://doi.org/10.1145/3620666.3651369 | unknown | https://github.com/apuaaChen/EVT_AE | ml-systems | Epilogue Visitor Tree compiler for training-graph fusion built on CUTLASS; single GPU. Concern - CUTLASS templates were tuned for A100 (SM80); SM86 retuning may be needed. |
| 20 | Felix: Optimizing Tensor Programs with Gradient Descent | https://doi.org/10.1145/3620666.3651348 | unknown | https://github.com/uiuc-arc/felix | ml-systems | Gradient-descent search over a differentiable relaxation of TVM/Ansor schedules; evaluated on single GPUs and finishes searches in minutes, which suits a 10-week budget. |
| 21 | Flexible Non-intrusive Dynamic Instrumentation for WebAssembly | https://doi.org/10.1145/3620666.3651338 | unknown | https://github.com/titzer/wizard-engine | other-userspace | Non-intrusive bytecode-level dynamic instrumentation in the Wizard WebAssembly research engine; user-space, CPU-only, written in Virgil. |
| 22 | Getting a Handle on Unmanaged Memory | https://doi.org/10.1145/3620666.3651326 | https://arxiv.org/pdf/2405.00038 | https://github.com/PrescienceLab/alaska-asplos24-artifact | memory | ALASKA - compiler plus runtime that adds handles to unmanaged C/C++ so the heap can be compacted; drop-in malloc replacement, user-space only. Main repo is nickwanninger/alaska. |
| 23 | Going Green for Less Green: Optimizing the Cost of Reducing Cloud Carbon Emissions | https://doi.org/10.1145/3620666.3651374 | unknown | https://zenodo.org/records/10888009 | scheduling | GAIA carbon-aware batch scheduler; the artifact ships both an AWS ParallelCluster driver and a pure simulation interface, and the simulator alone reproduces most figures on one machine. |
| 24 | Hector: An Efficient Programming and Compilation Framework for Implementing Relational Graph Neural Networks in GPU Architectures | https://doi.org/10.1145/3620666.3651322 | https://arxiv.org/pdf/2301.06284 | https://github.com/K-Wu/HET | ml-systems | Two-level IR and CUDA code generator for relational GNNs; single-GPU evaluation against DGL/PyG on OGB heterogeneous graphs. |
| 25 | MAGIS: Memory Optimization via Coordinated Graph Transformation and Scheduling for DNN | https://doi.org/10.1145/3620666.3651330 | unknown | https://github.com/pku-liang/MAGIS | ml-systems | Coordinated graph transformation plus scheduling for DNN memory reduction; single-GPU, and memory-constrained studies are a natural fit for a 24 GB card. |
| 26 | Optimal Kernel Orchestration for Tensor Programs with Korch | https://doi.org/10.1145/3620666.3651383 | https://arxiv.org/pdf/2406.09465 | https://github.com/humuyan/Korch | ml-systems | Operator fission plus ILP-based kernel orchestration for DNN inference; evaluated on single V100/A100 GPUs, so an A5000 run is a direct scale-down. |
| 27 | PATHFINDER: Practical Real-Time Learning for Data Prefetching | https://doi.org/10.1145/3620666.3651332 | https://users.cs.utah.edu/~rajeev/pubs/asplos24.pdf | https://github.com/linjiaty/Pathfinder | ml-for-systems | Spiking-neural-network data prefetcher evaluated in ChampSim, which is a CPU-only trace-driven simulator that runs fine here. Concern - the paper also has an RTL/hardware cost analysis that cannot be reproduced. |
| 28 | SpecInfer: Accelerating Large Language Model Serving with Tree-based Speculative Inference and Verification | https://doi.org/10.1145/3620666.3651335 | https://arxiv.org/pdf/2305.09781 | https://github.com/flexflow/FlexFlow | llm-inference | Tree-based speculative decoding and parallel verification for LLM serving; the offloading configuration is explicitly single-GPU, so 7B-class models fit in 24 GB. AE repo is goliaro/specinfer-ae. |
| 29 | FastGL: A GPU-Efficient Framework for Accelerating Sampling-Based GNN Training at Large Scale | https://doi.org/10.1145/3622781.3674167 | https://arxiv.org/pdf/2409.14939 | https://github.com/a1bc2def6g/fastgl-ae | ml-systems | GPU-efficient sampling, memory-IO and computation pipeline for large-scale GNN training on a single GPU with host-memory graph storage. |
| 30 | MaxEmbed: Maximizing SSD bandwidth utilization for huge embedding models serving | https://doi.org/10.1145/3622781.3674172 | unknown | https://github.com/Ksitta/MaxEmbed | storage | Maximizes NVMe bandwidth for SSD-resident embedding tables in recommendation serving; the machine has two PM9A3 NVMe drives. Concern - if the artifact needs SPDK-style raw device binding that requires root, an io_uring path would have to be used instead. |
| 31 | VertexSurge: Variable Length Graph Pattern Match on Billion-edge Graphs | https://doi.org/10.1145/3622781.3674173 | unknown | https://github.com/madsys-dev/VertexSurge | other-userspace | Single-machine C++/TBB engine for variable-length graph pattern matching; builds with cmake and user-space libraries. Concern - billion-edge LDBC datasets need a lot of RAM and disk, so a smaller scale factor may be necessary. |

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | Amanda: Unified Instrumentation Framework for Deep Neural Networks | included | in scope - ml-systems; official code at https://github.com/uchuhimo/amanda |
| 2 | Automatic Generation of Vectorizing Compilers for Customizable Digital Signal Processors | out-topic | DSP vectorizing-compiler generation |
| 3 | BypassD: Enabling fast userspace access to shared SSDs | out-machine | core idea extends IOMMU hardware to translate file offsets and needs OS page-table changes; no root, no kernel modification |
| 4 | CC-NIC: a Cache-Coherent Interface to the NIC | out-machine | proposes a cache-coherent NIC hardware interface |
| 5 | Cocco: Hardware-Mapping Co-Exploration towards Memory Capacity-Communication Optimization | out-topic | accelerator hardware-mapping design-space exploration |
| 6 | CodeCrunch: Improving Serverless Performance via Function Compression and Cost-Aware Warmup Location Optimization | out-machine | function compression and warmup placement are evaluated on a container-based serverless cluster; Docker is not installed and cannot be installed without root |
| 7 | CrossPrefetch: Accelerating I/O Prefetching for Modern Storage | out-machine | artifact ships a modified Linux 5.14 kernel (Cross-OS half of the design); rebuilding and booting a kernel is impossible without root |
| 8 | EagleEye: Nanosatellite constellation design for high-coverage, high-resolution sensing | out-topic | nanosatellite constellation design |
| 9 | Everywhere All at Once: Co-Location Attacks on Public Cloud FaaS | out-topic | cloud co-location attack measurement study |
| 10 | Expanding Datacenter Capacity with DVFS Boosting: A safe and scalable deployment experience | out-machine | fleet-wide DVFS boosting deployed in production datacenters; needs root-level frequency control |
| 11 | Exploiting Human Color Discrimination for Memory- and Energy-Efficient Image Encoding in Virtual Reality | out-topic | VR image encoding and display energy |
| 12 | Formal Mechanised Semantics of CHERI C: Capabilities, Undefined Behaviour, and Provenance | out-topic | formal mechanised semantics of CHERI C |
| 13 | GPU-based Private Information Retrieval for On-Device Machine Learning Inference | out-topic | cryptographic private information retrieval, not one of the in-scope systems topics |
| 14 | HIDA: A Hierarchical Dataflow Compiler for High-Level Synthesis | out-topic | high-level synthesis compiler for FPGA dataflow accelerators |
| 15 | Lightweight, Modular Verification for WebAssembly-to-Native Instruction Selection | out-topic | formal verification of instruction selection rules |
| 16 | Loupe: Driving the Development of OS Compatibility Layers | included | in scope - other-userspace; official code at https://github.com/unikraft/loupe |
| 17 | ngAP: Non-blocking Large-scale Automata Processing on GPUs | included | in scope - other-userspace; official code at https://github.com/getianao/ngAP |
| 18 | Optimizing Deep Learning Inference via Global Analysis and Tensor Expressions | included | in scope - ml-systems; official code at https://github.com/summerspringwei/souffle-ae |
| 19 | Performance-aware Scale Analysis with Reserve for Homomorphic Encryption | out-topic | homomorphic-encryption scale analysis |
| 20 | Proteus: A High-Throughput Inference-Serving System with Accuracy Scaling | included | in scope - ml-systems; official code at https://github.com/UMass-LIDS/Proteus |
| 21 | RainbowCake: Mitigating Cold-starts in Serverless with Layer-wise Container Caching and Sharing | out-machine | layer-wise container pre-warming is evaluated on OpenWhisk clusters; needs Docker plus multiple nodes, neither available |
| 22 | Scaling Up Memory Disaggregated Applications with SMART | out-machine | RDMA-based disaggregated memory across machines |
| 23 | SoCFlow: Efficient and Scalable DNN Training on SoC-Clustered Edge Servers | out-machine | requires SoC-clustered edge server hardware |
| 24 | SoD2: Statically Optimizing Dynamic Deep Neural Network Execution | out-no-code | searched GitHub repo search and the web for SoD2 / Rank and Dimension Propagation artifacts and found none; evaluation is also mobile-SoC only |
| 25 | TrackFM: Far-out Compiler Support for a Far Memory World | included | in scope - memory; official code at https://github.com/compiler-disagg/TrackFM |
| 26 | Training Job Placement in Clusters with Statistical In-Network Aggregation | out-machine | in-network aggregation on programmable switches in a multi-node training cluster |
| 27 | UBFuzz: Finding Bugs in Sanitizer Implementations | out-topic | fuzzing sanitizer implementations |
| 28 | ZENO: A Type-based Optimization Framework for Zero Knowledge Neural Network Inference | out-topic | zero-knowledge-proof neural network inference |
| 29 | A Fault-Tolerant Million Qubit-Scale Distributed Quantum Computer | out-topic | quantum computer architecture |
| 30 | A Journey of a 1,000 Kernels Begins with a Single Step: A Retrospective of Deep Learning on GPUs | out-machine | longitudinal characterization across three GPU generations using device-API and microarchitecture counters; needs perf-class counters and hardware we do not have |
| 31 | A Quantitative Analysis and Guidelines of Data Streaming Accelerator in Modern Intel Xeon Scalable Processors | out-machine | requires the Intel Data Streaming Accelerator in Xeon Scalable CPUs |
| 32 | Achieving Near-Zero Read Retry for 3D NAND Flash Memory | out-machine | 3D NAND flash chip characterization and firmware changes |
| 33 | An Encoding Scheme to Enlarge Practical DNA Storage Capacity by Reducing Primer-Payload Collisions | out-topic | DNA data storage encoding |
| 34 | Atalanta: A Bit is Worth a “Thousand” Tensor Values | out-topic | DNN accelerator datapath |
| 35 | AttAcc! Unleashing the Power of PIM for Batched Transformer-based Generative Model Inference | out-machine | processing-in-memory hardware for batched transformer inference |
| 36 | Avoiding Instruction-Centric Microarchitectural Timing Channels Via Binary-Code Transformations | out-topic | microarchitectural timing-channel defense |
| 37 | BitPacker: Enabling High Arithmetic Efficiency in Fully Homomorphic Encryption Accelerators | out-topic | fully homomorphic encryption accelerator |
| 38 | BVAP: Energy and Memory Efficient Automata Processing for Regular Expressions with Bounded Repetitions | out-topic | automata-processing hardware for regular expressions |
| 39 | Carat: Unlocking Value-Level Parallelism for Multiplier-Free GEMMs | out-topic | multiplier-free GEMM hardware |
| 40 | CIM-MLC: A Multi-level Compilation Stack for Computing-In-Memory Accelerators | out-machine | compilation stack for computing-in-memory accelerator hardware |
| 41 | CMC: Video Transformer Acceleration via CODEC Assisted Matrix Condensing | out-topic | video transformer acceleration hardware |
| 42 | Codesign of quantum error-correcting codes and modular chiplets in the presence of defects | out-topic | quantum error-correcting codes and chiplets |
| 43 | Compiling Loop-Based Nested Parallelism for Irregular Workloads | included | in scope - other-userspace; official code at https://github.com/arcana-lab/heartbeatcompiler |
| 44 | Cornucopia Reloaded: Load Barriers for CHERI Heap Temporal Safety | out-machine | CHERI capability hardware for heap temporal safety |
| 45 | Design of Novel Analog Compute Paradigms with Ark | out-topic | analog compute design |
| 46 | Direct Memory Translation for Virtualized Clouds | out-machine | new MMU/address-translation hardware evaluated in simulation |
| 47 | Efficient Microsecond-scale Blind Scheduling with Tiny Quanta | out-machine | Tiny Quanta is built on Caladan, which needs a custom kernel module, DPDK and dedicated NIC queues with root |
| 48 | Eliminating Storage Management Overhead of Deduplication over SSD Arrays Through a Hardware/Software Co-Design | out-machine | hardware/software co-design inside the SSD array controller |
| 49 | Elivagar: Efficient Quantum Circuit Search for Classification | out-topic | quantum circuit search |
| 50 | Energy Efficient Convolutions with Temporal Arithmetic | out-topic | temporal-arithmetic convolution hardware |
| 51 | ExeGPT: Constraint-Aware Resource Scheduling for LLM Inference | out-no-code | checked GitHub repo search and web search for an ExeGPT release and found none; the system is also a multi-GPU distributed serving stack |
| 52 | FaaSGraph: Enabling Scalable, Efficient, and Cost-Effective Graph Processing with Serverless Computing | out-machine | artifact setup script installs Docker and builds container images on every host; container runtime cannot be installed without root |
| 53 | FOCAL: A First-Order Carbon Model to Assess Processor Sustainability | out-topic | first-order carbon model for processor sustainability, not an in-scope systems topic |
| 54 | FPGA Technology Mapping Using Sketch-Guided Program Synthesis | out-topic | FPGA technology mapping |
| 55 | GIANTSAN: Efficient Memory Sanitization with Segment Folding | included | in scope - other-userspace; official code at https://github.com/AceSrc/GiantSan-Artifact |
| 56 | GMLake: Efficient and Transparent GPU Memory Defragmentation for Large-scale DNN Training with Virtual Memory Stitching | included | in scope - memory; official code at https://github.com/antgroup/glake |
| 57 | Grafu: Unleashing the Full Potential of Future Value Computation for Out-of-core Synchronous Graph Processing | out-no-code | searched GitHub and the web for a Grafu artifact and found none |
| 58 | Greybox Fuzzing for Concurrency Testing | out-topic | greybox fuzzing for concurrency bugs |
| 59 | Heet: Accelerating Elastic Training in Heterogeneous Deep Learning Clusters | out-machine | elastic training over heterogeneous multi-GPU clusters |
| 60 | Hydride: A Retargetable and Extensible Synthesis-based Compiler for Modern Hardware Architectures | out-topic | retargetable compiler synthesis for SIMD ISAs |
| 61 | In-Storage Domain-Specific Acceleration for Serverless Computing | out-machine | computational-storage hardware acceleration |
| 62 | JUNO: Optimizing High-Dimensional Approximate Nearest Neighbour Search with Sparsity-Aware Algorithm and Ray-Tracing Core Mapping | out-no-code | checked GitHub repo search, web search and the arXiv PDF; the only repository referenced is faiss, no Juno artifact was released |
| 63 | Kimbap: A Node-Property Map System for Distributed Graph Analytics | out-machine | distributed multi-node graph analytics |
| 64 | Last-Level Cache Side-Channel Attacks Are Feasible in the Modern Public Cloud | out-topic | last-level cache side-channel attacks |
| 65 | LazyBarrier: Reconstructing Android IO Stack for Barrier-Enabled Flash Storage | out-machine | rewrites the Android kernel I/O stack for barrier-enabled flash |
| 66 | LazyDP: Co-Designing Algorithm-Software for Scalable Training of Differentially Private Recommendation Models | out-no-code | checked GitHub repo search, web search and the arXiv PDF; no LazyDP artifact is released |
| 67 | Lifting Micro-Update Models from RTL for Formal Security Analysis | out-topic | formal security analysis lifted from RTL |
| 68 | Lightweight Fault Isolation: Practical, Efficient, and Secure Software Sandboxing | out-machine | the multi-sandbox SFI scheme is ARM64-specific (uses ARM64 addressing and guard regions); target machine is x86-64 |
| 69 | Marple: Scalable Spike Sorting for Untethered Brain-Machine Interfacing | out-topic | spike-sorting hardware for brain-machine interfaces |
| 70 | MaxK-GNN: Extremely Fast GPU Kernel Design for Accelerating Graph Neural Networks Training | included | in scope - ml-systems; official code at https://github.com/xiexi51/MaxK-GNN |
| 71 | MECH: Multi-Entry Communication Highway for Superconducting Quantum Chiplets | out-topic | superconducting quantum chiplet interconnect |
| 72 | METAL: Caching Multi-level Indexes in Domain-Specific Architectures | out-topic | index caching inside domain-specific accelerator hardware |
| 73 | MicroVSA: An Ultra-Lightweight Vector Symbolic Architecture-based Classifier Library for Always-On Inference on Tiny Microcontrollers | out-machine | always-on inference on tiny microcontrollers |
| 74 | MulBERRY: Enabling Bit-Error Robustness for Energy-Efficient Multi-Agent Autonomous Systems | out-topic | bit-error robustness for multi-agent autonomous system hardware |
| 75 | Multi-Dimensional and Message-Guided Fuzzing for Robotic Programs in Robot Operating System | out-topic | fuzzing robotic programs in ROS |
| 76 | One Gate Scheme to Rule Them All: Introducing a Complex Yet Reduced Instruction Set for Quantum Computing | out-topic | quantum instruction set design |
| 77 | Optimizing Dynamic-Shape Neural Networks on Accelerators via On-the-Fly Micro-Kernel Polymerization | out-no-code | checked GitHub repo search, web search and the author PDF; no MikPoly artifact found, and half the evaluation targets Ascend NPUs |
| 78 | ORIANNA: An Accelerator Generation Framework for Optimization-based Robotic Applications | out-topic | accelerator generation for robotics |
| 79 | Palantir: Hierarchical Similarity Detection for Post-Deduplication Delta Compression | out-no-code | checked GitHub repo search, web search and the author PDF; the Palantir implementation is not released |
| 80 | PDIP: Priority Directed Instruction Prefetching | out-topic | hardware instruction prefetcher |
| 81 | Pentimento: Data Remanence in Cloud FPGAs | out-machine | data remanence in cloud FPGAs |
| 82 | PIM-DL: Expanding the Applicability of Commodity DRAM-PIMs for Deep Learning via Algorithm-System Co-Optimization | out-machine | commodity DRAM-PIM hardware |
| 83 | PIM-STM: Software Transactional Memory for Processing-In-Memory Systems | out-machine | software transactional memory for UPMEM processing-in-memory hardware |
| 84 | Plankton: Reconciling Binary Code and Debug Information | out-topic | reconciling binary code and debug information |
| 85 | PyTorch 2: Faster Machine Learning Through Dynamic Python Bytecode Transformation and Graph Compilation | included | in scope - ml-systems; official code at https://github.com/pytorch/pytorch |
| 86 | QuFEM: Fast and Accurate Quantum Readout Calibration Using the Finite Element Method | out-topic | quantum readout calibration |
| 87 | RAP: Resource-aware Automated GPU Sharing for Multi-GPU Recommendation Model Training and Input Preprocessing | included | in scope - ml-systems; official code at https://github.com/Ash-Zheng/RAP-artifacts |
| 88 | Red-QAOA: Efficient Variational Optimization through Circuit Reduction | out-topic | variational quantum circuit optimization |
| 89 | RPG2: Robust Profile-Guided Runtime Prefetch Generation | out-machine | artifact requires Linux perf profiling (perf record / perf2bolt) to drive BOLT prefetch injection; perf_event_paranoid=3 blocks hardware profiling on this machine |
| 90 | Rubix: Reducing the Overhead of Secure Rowhammer Mitigations via Randomized Line-to-Row Mapping | out-topic | randomized line-to-row mapping for rowhammer mitigation in hardware |
| 91 | SEER: Super-Optimization Explorer for High-Level Synthesis using E-graph Rewriting | out-topic | high-level synthesis superoptimization |
| 92 | SEVeriFast: Minimizing the root of trust for fast startup of SEV microVMs | out-machine | AMD SEV microVM boot path; needs KVM and root |
| 93 | sIOPMP: Scalable and Efficient I/O Protection for TEEs | out-topic | hardware I/O physical memory protection for TEEs |
| 94 | Skip It: Take Control of Your Cache! | out-machine | microarchitectural cache-writeback extensions implemented on the BOOM RISC-V core |
| 95 | Slapo: A Schedule Language for Progressive Optimization of Large Deep Learning Model Training | included | in scope - ml-systems; official code at https://github.com/awslabs/slapo |
| 96 | SpotServe: Serving Generative Large Language Models on Preemptible Instances | out-machine | the contribution is dynamic reparallelization and migration across multiple preemptible GPU instances; it cannot be exercised on a single GPU |
| 97 | SUIT: Secure Undervolting with Instruction Traps | out-topic | undervolting security with instruction traps |
| 98 | T3: Transparent Tracking & Triggering for Fine-grained Overlap of Compute & Collectives | out-machine | near-memory hardware triggering combined with multi-accelerator collectives |
| 99 | Tandem Processor: Grappling with Emerging Operators in Neural Networks | out-topic | neural network accelerator datapath |
| 100 | TGLite: A Lightweight Programming Framework for Continuous-Time Temporal Graph Neural Networks | included | in scope - ml-systems; official code at https://github.com/ADAPT-uiuc/tglite |
| 101 | Two-Face: Combining Collective and One-Sided Communication for Efficient Distributed SpMM | out-machine | distributed multi-node SpMM with collective and one-sided communication |
| 102 | Verifying Rust Implementation of Page Tables in a Software Enclave Hypervisor | out-topic | formal verification of hypervisor page tables in Rust |
| 103 | WASP: Workload-Aware Self-Replicating Page-Tables for NUMA Servers | out-machine | kernel-level page-table replication on multi-socket NUMA servers |
| 104 | What You Trace is What You Get: Dynamic Stack-Layout Recovery for Binary Recompilation | out-topic | stack-layout recovery for binary recompilation |
| 105 | 8-bit Transformer Inference and Fine-tuning for Edge Accelerators | included | in scope - ml-systems; official code at https://github.com/jeffreyyu0602/quantized-training |
| 106 | A Midsummer Night’s Tree: Efficient and High Performance Secure SCM | out-topic | secure storage-class-memory hardware |
| 107 | A shared compilation stack for distributed-memory parallelism in stencil DSLs | out-machine | distributed-memory stencil compilation for HPC clusters |
| 108 | Accelerating Multi-Scalar Multiplication for Efficient Zero Knowledge Proofs with Multi-GPU Systems | out-machine | multi-GPU multi-scalar multiplication for zero-knowledge proofs |
| 109 | ACES: Accelerating Sparse Matrix Multiplication with Adaptive Execution Flow and Concurrency-Aware Cache Optimizations | out-topic | sparse matrix multiplication accelerator |
| 110 | AdaPipe: Optimizing Pipeline Parallelism with Adaptive Recomputation and Partitioning | out-machine | pipeline-parallel training across many GPUs |
| 111 | AERO: Adaptive Erase Operation for Improving Lifetime and Performance of Modern NAND Flash-Based SSDs | out-machine | modifies NAND flash erase operations in SSD firmware |
| 112 | AUDIBLE: A Convolution-Based Resource Allocator for Oversubscribing Burstable Virtual Machines | included | in scope - scheduling; official code at https://github.com/seyedali14/audible-artifact-asplos24 |
| 113 | BeeZip: Towards An Organized and Scalable Architecture for Data Compression | out-topic | data-compression hardware architecture |
| 114 | Boost Linear Algebra Computation Performance via Efficient VNNI Utilization | out-machine | the entire contribution is exploiting Intel AVX512-VNNI; the Threadripper PRO 5955WX (Zen3) has no AVX-512/VNNI |
| 115 | C4CAM: A Compiler for CAM-based In-memory Accelerators | out-topic | compiler for CAM-based in-memory accelerators |
| 116 | Centauri: Enabling Efficient Scheduling for Communication-Computation Overlap in Large Model Training via Communication Partitioning | out-machine | communication partitioning for multi-GPU/multi-node large model training |
| 117 | Characterizing a Memory Allocator at Warehouse Scale | out-machine | characterization and A/B evaluation run fleet-wide inside Google production; no reusable artifact for the study |
| 118 | Characterizing Power Management Opportunities for LLMs in the Cloud | out-machine | needs GPU power-capping control (root) and production cluster power telemetry |
| 119 | CSSTs: A Dynamic Data Structure for Partial Orders in Concurrent Execution Analysis | included | in scope - other-userspace; official code at https://github.com/hcantunc/cssts |
| 120 | Dr. DNA: Combating Silent Data Corruptions in Deep Learning using Distribution of Neuron Activations | out-no-code | checked GitHub repo search and web search; no Dr. DNA artifact is released |
| 121 | DTC-SpMM: Bridging the Gap in Accelerating General Sparse Matrix Multiplication with Tensor Cores | included | in scope - ml-systems; official code at https://github.com/HPMLL/DTC-SpMM_ASPLOS24 |
| 122 | Energy-Adaptive Buffering for Efficient, Responsive, and Persistent Batteryless Systems | out-machine | batteryless energy-harvesting embedded hardware |
| 123 | Enforcing C/C++ Type and Scope at Runtime for Control-Flow and Data-Flow Integrity | out-topic | runtime type/scope enforcement for control-flow and data-flow integrity |
| 124 | EVT: Accelerating Deep Learning Training with Epilogue Visitor Tree | included | in scope - ml-systems; official code at https://github.com/apuaaChen/EVT_AE |
| 125 | Explainable Port Mapping Inference with Sparse Performance Counters for AMD's Zen Architectures | out-machine | port-mapping inference fundamentally needs hardware performance counters, which are blocked (perf_event_paranoid=3) |
| 126 | FaaSMem: Improving Memory Efficiency of Serverless Computing with Memory Pool Architecture | out-machine | offloads container memory to a remote memory-pool architecture with kernel-side page bucketing |
| 127 | FEASTA: A Flexible and Efficient Accelerator for Sparse Tensor Algebra in Machine Learning | out-topic | sparse tensor algebra accelerator |
| 128 | Felix: Optimizing Tensor Programs with Gradient Descent | included | in scope - ml-systems; official code at https://github.com/uiuc-arc/felix |
| 129 | Fermihedral: On the Optimal Compilation for Fermion-to-Qubit Encoding | out-topic | fermion-to-qubit encoding compilation |
| 130 | Flexible Non-intrusive Dynamic Instrumentation for WebAssembly | included | in scope - other-userspace; official code at https://github.com/titzer/wizard-engine |
| 131 | Fractal: Joint Multi-Level Sparse Pattern Tuning of Accuracy and Performance for DNN Pruning | out-no-code | checked GitHub repo search and web search; no Fractal/PatternIR artifact is released |
| 132 | FUYAO: DPU-enabled Direct Data Transfer for Serverless Computing | out-machine | requires a DPU for direct data transfer |
| 133 | Getting a Handle on Unmanaged Memory | included | in scope - memory; official code at https://github.com/PrescienceLab/alaska-asplos24-artifact |
| 134 | GMT: GPU Orchestrated Memory Tiering for the Big Data Era | out-machine | GPU-orchestrated NVMe access in the style of BaM; needs a custom NVMe driver and exclusive device binding, i.e. root |
| 135 | Going Green for Less Green: Optimizing the Cost of Reducing Cloud Carbon Emissions | included | in scope - scheduling; official code at https://zenodo.org/records/10888009 |
| 136 | GSCore: Efficient Radiance Field Rendering via Architectural Support for 3D Gaussian Splatting | out-topic | 3D Gaussian splatting rendering accelerator |
| 137 | Harp: Leveraging Quasi-Sequential Characteristics to Accelerate Sequence-to-Graph Mapping of Long Reads | out-topic | sequence-to-graph mapping hardware accelerator |
| 138 | Hector: An Efficient Programming and Compilation Framework for Implementing Relational Graph Neural Networks in GPU Architectures | included | in scope - ml-systems; official code at https://github.com/K-Wu/HET |
| 139 | IANUS: Integrated Accelerator based on NPU-PIM Unified Memory System | out-machine | NPU-PIM unified memory hardware |
| 140 | Kaleidoscope: Precise Invariant-Guided Pointer Analysis | out-topic | invariant-guided pointer analysis |
| 141 | Limoncello: Prefetchers for Scale | out-machine | disables hardware prefetchers via privileged MSR writes and is evaluated on Google's fleet |
| 142 | Longnail: High-Level Synthesis of Portable Custom Instruction Set Extensions for RISC-V Processors from Descriptions in the Open-Source CoreDSL Language | out-topic | high-level synthesis of RISC-V instruction set extensions |
| 143 | MAGIS: Memory Optimization via Coordinated Graph Transformation and Scheduling for DNN | included | in scope - ml-systems; official code at https://github.com/pku-liang/MAGIS |
| 144 | MemSnap μCheckpoints: A Data Single Level Store for Fearless Persistence | out-machine | introduces a new per-thread dirty-set tracking mechanism inside the kernel |
| 145 | Merlin: Multi-tier Optimization of eBPF Code for Performance and Compactness | out-machine | optimizes eBPF programs; unprivileged BPF is disabled (unprivileged_bpf_disabled=2) |
| 146 | More Apps, Faster Hot-Launch on Mobile Devices via Fore/Background-aware GC-Swap Co-design | out-machine | Android GC/swap co-design evaluated on mobile phones |
| 147 | MorphQPV: Exploiting Isomorphism in Quantum Programs to Facilitate Confident Verification | out-topic | quantum program verification |
| 148 | NDPipe: Exploiting Near-data Processing for Scalable Inference and Continuous Training in Photo Storage | out-machine | near-data processing hardware in photo storage servers |
| 149 | NetRen: Service Migration-Driven Network Renascence with Synthesizing Updated Configuration | out-topic | network configuration synthesis for service migration |
| 150 | NeuPIMs: NPU-PIM Heterogeneous Acceleration for Batched LLM Inferencing | out-machine | NPU-PIM heterogeneous hardware for LLM inference |
| 151 | OnePerc: A Randomness-aware Compiler for Photonic Quantum Computing | out-topic | photonic quantum compiler |
| 152 | Optimal Kernel Orchestration for Tensor Programs with Korch | included | in scope - ml-systems; official code at https://github.com/humuyan/Korch |
| 153 | Pathfinder: High-Resolution Control-Flow Attacks Exploiting the Conditional Branch Predictor | out-topic | conditional branch predictor side-channel attack |
| 154 | PATHFINDER: Practical Real-Time Learning for Data Prefetching | included | in scope - ml-for-systems; official code at https://github.com/linjiaty/Pathfinder |
| 155 | PrimePar: Efficient Spatial-temporal Tensor Partitioning for Large Transformer Model Training | out-machine | spatial-temporal tensor partitioning for large transformer training across many GPUs |
| 156 | Promatch: Extending the Reach of Real-Time Quantum Error Correction with Adaptive Predecoding | out-topic | real-time quantum error correction decoding |
| 157 | ProxiML: Building Machine Learning Classifiers for Photonic Quantum Computing | out-topic | photonic quantum computing classifiers |
| 158 | Pythia: Compiler-Guided Defense Against Non-Control Data Attacks | out-topic | compiler-guided defense against non-control data attacks |
| 159 | RTL-Repair: Fast Symbolic Repair of Hardware Design Code | out-topic | symbolic repair of RTL hardware designs |
| 160 | SIRO: Empowering Version Compatibility in Intermediate Representations via Program Synthesis | out-topic | IR version compatibility via program synthesis |
| 161 | SlimSLAM: An Adaptive Runtime for Visual-Inertial Simultaneous Localization and Mapping | out-no-code | checked GitHub repo search and web search; no SlimSLAM artifact is released |
| 162 | SmartMem: Layout Transformation Elimination and Adaptation for Efficient DNN Execution on Mobile | out-machine | layout optimization targets mobile devices and 2.5D mobile memory; evaluation needs phones |
| 163 | SpecInfer: Accelerating Large Language Model Serving with Tree-based Speculative Inference and Verification | included | in scope - llm-inference; official code at https://github.com/flexflow/FlexFlow |
| 164 | SpecPIM: Accelerating Speculative Inference on PIM-Enabled System via Architecture-Dataflow Co-Exploration | out-machine | speculative inference on PIM-enabled hardware |
| 165 | TAPA-CS: Enabling Scalable Accelerator Design on Distributed HBM-FPGAs | out-machine | distributed HBM-FPGA accelerator design |
| 166 | TAROT: A CXL SmartNIC-Based Defense Against Multi-bit Errors by Row-Hammer Attacks | out-machine | CXL SmartNIC-based rowhammer defense |
| 167 | TCCL: Discovering Better Communication Paths for PCIe GPU Clusters | out-machine | collective communication paths across a multi-GPU PCIe cluster |
| 168 | Thesios: Synthesizing Accurate Counterfactual I/O Traces from I/O Samples | out-no-code | only the synthesized trace dataset is public (google-research-datasets/thesios); the Thesios synthesis implementation itself was not released |
| 169 | TinyForge: A Design Space Exploration to Advance Energy and Silicon Area Trade-offs in tinyML Compute Architectures with Custom Latch Arrays | out-topic | tinyML compute architecture design-space exploration |
| 170 | Zoomie: A Software-like Debugging Tool for FPGAs | out-topic | FPGA debugging tooling |
| 171 | A Software Caching Runtime for Embedded NVRAM Systems | out-machine | embedded NVRAM platform |
| 172 | Bounding Speculative Execution of Atomic Regions to a Single Retry | out-topic | hardware speculation/atomic region support |
| 173 | CINM (Cinnamon): A Compilation Infrastructure for Heterogeneous Compute In-Memory and Compute Near-Memory Paradigms | out-machine | compilation infrastructure for compute-in-memory and compute-near-memory hardware |
| 174 | Clapton: Clifford Assisted Problem Transformation for Error Mitigation in Variational Quantum Algorithms | out-topic | error mitigation for variational quantum algorithms |
| 175 | Control Logic Synthesis: Drawing the Rest of the OWL | out-topic | hardware control logic synthesis |
| 176 | Don't Repeat Yourself! Coarse-Grained Circuit Deduplication to Accelerate RTL Simulation | out-topic | RTL simulation / EDA tooling |
| 177 | FastGL: A GPU-Efficient Framework for Accelerating Sampling-Based GNN Training at Large Scale | included | in scope - ml-systems; official code at https://github.com/a1bc2def6g/fastgl-ae |
| 178 | FMCC: Flexible Measurement-based Quantum Computation over Cluster State | out-topic | measurement-based quantum computation |
| 179 | GUST: Graph Edge-Coloring Utilization for Accelerating Sparse Matrix Vector Multiplication | out-machine | software/hardware co-design whose target is an FPGA accelerator |
| 180 | Hassert: Hardware Assertion-Based Verification Framework with FPGA Acceleration | out-machine | FPGA-accelerated hardware assertion verification |
| 181 | Litmus: Fair Pricing for Serverless Computing | out-no-code | checked GitHub repo search, web search and the arXiv PDF; no Litmus artifact is released, and the pricing probes rely on hardware performance counters |
| 182 | Manta: Hybrid-Sensitive Type Inference Toward Type-Assisted Bug Detection for Stripped Binaries | out-topic | type inference for stripped binaries |
| 183 | MaxEmbed: Maximizing SSD bandwidth utilization for huge embedding models serving | included | in scope - storage; official code at https://github.com/Ksitta/MaxEmbed |
| 184 | MPC-Pipe: an Efficient Pipeline Scheme for Semi-honest MPC Machine Learning | out-topic | secure multi-party computation protocol pipelining |
| 185 | Proactive Runtime Detection of Aging-Related Silent Data Corruptions: A Bottom-Up Approach | out-machine | detection of aging-related silicon faults |
| 186 | QRCC: Evaluating Large Quantum Circuits on Small Quantum Computers through Integrated Qubit Reuse and Circuit Cutting | out-topic | quantum circuit cutting and qubit reuse |
| 187 | Salus: A Practical Trusted Execution Environment for CPU-FPGA Heterogeneous Cloud Platforms | out-machine | CPU-FPGA trusted execution environment |
| 188 | Sharing is leaking: blocking transient-execution attacks with core-gapped confidential VMs | out-machine | core-gapped confidential VMs; needs hypervisor and root |
| 189 | TensorTEE: Unifying Heterogeneous TEE Granularity for Efficient Secure Collaborative Tensor Computing | out-machine | unified TEE hardware granularity for tensor computing |
| 190 | The Mutators Reloaded: Fuzzing Compilers with Large Language Model Generated Mutation Operators | out-topic | compiler fuzzing with LLM-generated mutation operators |
| 191 | Toleo: Scaling Freshness to Tera-scale Memory Using CXL and PIM | out-machine | CXL plus processing-in-memory freshness hardware |
| 192 | Towards Unified Analysis of GPU Consistency | out-topic | GPU memory consistency model analysis |
| 193 | Validating JVM Compilers via Maximizing Optimization Interactions | out-topic | JVM compiler testing |
| 194 | VertexSurge: Variable Length Graph Pattern Match on Billion-edge Graphs | included | in scope - other-userspace; official code at https://github.com/madsys-dev/VertexSurge |
