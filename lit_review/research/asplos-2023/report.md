STATUS: complete
TOTAL_PAPERS: 151
INCLUDED: 28

## Sources

ASPLOS 2023 (the 28th conference, Vancouver, 25-29 March 2023) was the first ASPLOS run
with multiple submission cycles, and its proceedings were issued as four ACM volumes:

- Volume 1 - doi:10.1145/3567955 (9 papers, pp. 1-137)
- Volume 2 - doi:10.1145/3575693 (65 papers, pp. 1-947)
- Volume 3 - doi:10.1145/3582016 (54 papers + 2 keynote abstracts, pp. 1-820)
- Volume 4 - doi:10.1145/3623278 (23 papers, pp. 1-411, published October 2023; these are
  the papers of the last ASPLOS 2023 cycle, presented at the following conference)

Paper list construction:

1. Primary enumeration - Crossref REST API. I deep-paged every `proceedings-article`
   with DOI prefix `10.1145` published 2022-12-01 to 2023-12-31 (32811 records) and kept
   every record whose `container-title` is one of the four ASPLOS 2023 volumes. This
   yielded 153 article records; two of them are the keynote abstracts in Volume 3
   ("Direct Mind-Machine Teaming" p. 1, "Language Models: The Most Important Compute
   Challenge of Our Time" p. 2), which I excluded, leaving 151 main-track papers.
   Page ranges are contiguous within every volume, confirming nothing is missing.
   (ACM DL TOC pages and DBLP both refuse scripted access - 403 / anti-bot challenge.)
2. Cross-check 1 - the official program page
   https://asplos-conference.org/asplos2023/index.html%3Fp=3602.html was fetched and
   parsed: 27 sessions, 128 paper entries. That is exactly Volume 1 + Volume 2 +
   Volume 3 (9 + 65 + 54 = 128), i.e. every paper presented at the conference itself.
   Volume 4 (23 papers) is the remaining cycle and is not on that program page.
3. Cross-check 2 - the conference-publishing.com tables of contents
   (https://www.conference-publishing.com/toc/ASPLOSA23/ , .../ASPLOSB23/ ,
   .../ASPLOSC23/) give 137 entries for Volumes 1-3 including front matter, consistent
   with the 128 papers plus title pages, chairs' messages and committee lists. These
   pages also carry the ACM artifact badges and the "Published Artifact" DOIs, which I
   used as the primary evidence for the code check.
4. Abstracts were pulled from the Semantic Scholar Graph API (batch endpoint) for all
   151 DOIs and used for the topic screen where the title was ambiguous.
5. Code check - artifact DOIs from (3), plus GitHub repository-search and
   repository-existence queries against the GitHub API, plus targeted web searches for
   each surviving paper. There is no sysartifacts.github.io page for ASPLOS and the
   ASPLOS 2023 site has no artifact-results page, so badges came from (3).

Scratch files (fetched HTML, parsed JSON) are under `scratch/`.

## Included
| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | Cooperative Concurrency Control for Write-Intensive Key-Value Workloads | https://doi.org/10.1145/3567955.3567957 | https://dl.acm.org/doi/pdf/10.1145/3567955.3567957 | https://doi.org/10.5281/zenodo.7182800 | storage | In-memory key-value store concurrency control on multicore CPUs - pure user space  fits 16-core host  AE artifact released on Zenodo |
| 2 | Glign: Taming Misaligned Graph Traversals in Concurrent Graph Processing | https://doi.org/10.1145/3567955.3567963 | https://dl.acm.org/doi/pdf/10.1145/3567955.3567963 | https://doi.org/10.5281/zenodo.7173860 | other-userspace | Single-machine concurrent graph-processing runtime - CPU only user space  Zenodo artifact  alignment heuristics are an obvious improvement target |
| 3 | Betty: Enabling Large-Scale GNN Training with Batch-Level Graph Partitioning | https://doi.org/10.1145/3575693.3575725 | https://dl.acm.org/doi/pdf/10.1145/3575693.3575725 | https://github.com/PASAUCMerced/Betty | ml-systems | GNN training on a single GPU under memory pressure - batch-level partitioning is exactly a one-GPU memory problem  Zenodo + GitHub artifact |
| 4 | Carbon Explorer: A Holistic Framework for Designing Carbon Aware Datacenters | https://doi.org/10.1145/3575693.3575754 | https://arxiv.org/pdf/2201.10036 | https://github.com/facebookresearch/CarbonExplorer | scheduling | Trace-driven datacenter carbon/capacity simulator - pure Python user space  open source  policies are easy to extend |
| 5 | ElasticFlow: An Elastic Serverless Training Platform for Distributed Deep Learning | https://doi.org/10.1145/3575693.3575721 | https://dl.acm.org/doi/pdf/10.1145/3575693.3575721 | https://github.com/pkusys/ElasticFlow | scheduling | DL-training job scheduler with an open trace-driven simulator - simulator runs on CPU; concern the physical testbed uses a multi-GPU cluster |
| 6 | EVStore: Storage and Caching Capabilities for Scaling Embedding Tables in Deep Recommendation Systems | https://doi.org/10.1145/3575693.3575718 | https://dl.acm.org/doi/pdf/10.1145/3575693.3575718 | https://github.com/ucare-uchicago/ev-store-dlrm | caching | Multi-layer embedding-table cache for DLRM inference - single node CPU/GPU user space  cache admission/eviction policy is a clean improvement target |
| 7 | Hidet: Task-Mapping Programming Paradigm for Deep Learning Tensor Programs | https://doi.org/10.1145/3575693.3575702 | https://arxiv.org/pdf/2210.09603 | https://github.com/hidet-org/hidet | ml-systems | DL compiler with task-mapping scheduling - single NVIDIA GPU actively maintained open source  Ampere supported |
| 8 | LeaFTL: A Learning-Based Flash Translation Layer for Solid-State Drives | https://doi.org/10.1145/3575693.3575744 | https://arxiv.org/pdf/2301.00072 | https://github.com/platformxlab/LeaFTL | ml-for-systems | Learned-index flash translation layer - ships a trace-driven SSD simulator that runs in user space; concern the full FEMU setup wants KVM which is unavailable |
| 9 | Lucid: A Non-intrusive, Scalable and Interpretable Scheduler for Deep Learning Training Jobs | https://doi.org/10.1145/3575693.3575705 | https://dl.acm.org/doi/pdf/10.1145/3575693.3575705 | https://github.com/S-Lab-System-Group/Lucid | scheduling | DL-cluster scheduler evaluated by trace-driven simulation with public traces - runs entirely on one CPU host |
| 10 | NNSmith: Generating Diverse and Valid Test Cases for Deep Learning Compilers | https://doi.org/10.1145/3575693.3575707 | https://arxiv.org/pdf/2207.13066 | https://github.com/ise-uiuc/nnsmith | ml-systems | DL-compiler fuzzing - pure user-space Python runs against TVM/ONNXRuntime on one machine  widely used open source |
| 11 | TensorIR: An Abstraction for Automatic Tensorized Program Optimization | https://doi.org/10.1145/3575693.3576933 | https://arxiv.org/pdf/2207.04296 | https://github.com/tlc-pack/tvm-tensorir | ml-systems | Tensorized-program abstraction for TVM - single GPU/CPU auto-scheduling  fully open source and upstreamed into Apache TVM |
| 12 | TiLT: A Time-Centric Approach for Stream Query Optimization and Parallelization | https://doi.org/10.1145/3575693.3575704 | https://arxiv.org/pdf/2301.12030 | https://doi.org/10.5281/zenodo.7493145 | other-userspace | Stream-query compiler and runtime - CPU only user space  Zenodo AE artifact |
| 13 | TLP: A Deep Learning-Based Cost Model for Tensor Program Tuning | https://doi.org/10.1145/3575693.3575737 | https://arxiv.org/pdf/2211.03578 | https://github.com/zhaiyi000/tlp | ml-for-systems | Learned cost model for tensor-program tuning - trains and runs on one GPU  open source  a natural target for better models or cheaper search |
| 14 | VClinic: A Portable and Efficient Framework for Fine-Grained Value Profilers | https://doi.org/10.1145/3575693.3576934 | https://dl.acm.org/doi/pdf/10.1145/3575693.3576934 | https://github.com/VClinic/VClinic | other-userspace | Dynamic-binary-instrumentation value profiler - user space no root or perf counters required  GitHub + Zenodo artifact |
| 15 | WACO: Learning Workload-Aware Co-optimization of the Format and Schedule of a Sparse Tensor Program | https://doi.org/10.1145/3575693.3575742 | https://dl.acm.org/doi/pdf/10.1145/3575693.3575742 | https://github.com/nullplay/Workload-Aware-Co-Optimization | ml-for-systems | Learned cost model that co-optimizes sparse tensor format and schedule - CPU only  GitHub + Zenodo artifact |
| 16 | Characterizing and Optimizing End-to-End Systems for Private Inference | https://doi.org/10.1145/3582016.3582065 | https://arxiv.org/pdf/2207.07177 | https://doi.org/10.5281/zenodo.7633678 | ml-systems | End-to-end characterization and optimization of private-inference serving - client and server can be two processes on one host with one GPU; concern the contribution is partly cryptographic-protocol level |
| 17 | DrGPUM: Guiding Memory Optimization for GPU-Accelerated Applications | https://doi.org/10.1145/3582016.3582044 | https://dl.acm.org/doi/pdf/10.1145/3582016.3582044 | https://github.com/Lin-Mao/DrGPUM | memory | GPU memory profiler built on CUPTI - single GPU user space no root or perf counters  GitHub + Zenodo artifact |
| 18 | Efficient Compactions between Storage Tiers with PrismDB | https://doi.org/10.1145/3582016.3582052 | https://dl.acm.org/doi/pdf/10.1145/3582016.3582052 | https://github.com/princeton-sns/prismdb | storage | LSM key-value store with tier-aware compaction - user-space RocksDB-style engine on NVMe  GitHub + Zenodo artifact; concern the paper uses QLC+SLC tiers that must be emulated here |
| 19 | GRACE: A Scalable Graph-Based Approach to Accelerating Recommendation Model Inference | https://doi.org/10.1145/3582016.3582029 | https://dl.acm.org/doi/pdf/10.1145/3582016.3582029 | https://github.com/Linestro/GRACE | ml-systems | Graph-based acceleration of recommendation-model inference on one CPU/GPU node - GitHub + Zenodo artifact |
| 20 | Heron: Automatically Constrained High-Performance Library Generation for Deep Learning Accelerators | https://doi.org/10.1145/3582016.3582061 | https://dl.acm.org/doi/pdf/10.1145/3582016.3582061 | https://github.com/IPRC-ICT/Heron | ml-systems | Constrained auto-scheduling for tensor libraries - supports NVIDIA tensor-core GPUs and CPUs; concern part of the evaluation uses a Cambricon accelerator we do not have |
| 21 | RepCut: Superlinear Parallel RTL Simulation with Replication-Aided Partitioning | https://doi.org/10.1145/3582016.3582034 | https://dl.acm.org/doi/pdf/10.1145/3582016.3582034 | https://doi.org/10.5281/zenodo.7621336 | other-userspace | Parallel RTL simulation by replication-aided partitioning - CPU-only user-space simulator that scales with the 16 cores here  Zenodo AE artifact |
| 22 | SparseTIR: Composable Abstractions for Sparse Compilation in Deep Learning | https://doi.org/10.1145/3582016.3582047 | https://arxiv.org/pdf/2207.04606 | https://github.com/uwsampl/SparseTIR | ml-systems | Sparse tensor compilation for DL on a single NVIDIA GPU - GitHub + Zenodo AE artifact  well documented |
| 23 | TeraHeap: Reducing Memory Pressure in Managed Big Data Frameworks | https://doi.org/10.1145/3582016.3582045 | https://dl.acm.org/doi/pdf/10.1145/3582016.3582045 | https://github.com/jackkolokasis/teraheap | memory | Adds an NVMe-backed second heap to the JVM to cut GC pressure for Spark/Giraph - user-space OpenJDK build on one node  GitHub + Zenodo artifact |
| 24 | BaCO: A Fast and Portable Bayesian Compiler Optimization Framework | https://doi.org/10.1145/3623278.3624770 | https://arxiv.org/pdf/2212.11142 | https://github.com/baco-authors/baco | ml-for-systems | Bayesian autotuner for compiler/scheduling search spaces (TACO RISE HPVM) - pure user-space Python on one CPU/GPU node  open source |
| 25 | MiniMalloc: A Lightweight Memory Allocator for Hardware-Accelerated Machine Learning | https://doi.org/10.1145/3623278.3624752 | https://dl.acm.org/doi/pdf/10.1145/3623278.3624752 | https://github.com/google/minimalloc | memory | Offline static memory allocator (2D packing solver) for ML accelerator buffers - single-threaded C++ CPU solver with open benchmarks  fully open source |
| 26 | RECom: A Compiler Approach to Accelerating Recommendation Model Inference with Massive Embedding Columns | https://doi.org/10.1145/3623278.3624761 | https://dl.acm.org/doi/pdf/10.1145/3623278.3624761 | https://github.com/AlibabaResearch/recom | ml-systems | Compiler that fuses massive embedding-column subgraphs for recommendation inference on one GPU - open source from Alibaba |
| 27 | ShapleyIQ: Influence Quantification by Shapley Values for Performance Debugging of Microservices | https://doi.org/10.1145/3623278.3624771 | https://dl.acm.org/doi/pdf/10.1145/3623278.3624771 | https://github.com/lonyle/ShapleyIQ | other-userspace | Shapley-value performance attribution for microservice traces - code and data released; analysis runs offline on traces on one host  concern the original setting is a production cluster |
| 28 | Supporting Descendants in SIMD-Accelerated JSONPath | https://doi.org/10.1145/3623278.3624754 | https://dl.acm.org/doi/pdf/10.1145/3623278.3624754 | https://github.com/rsonquery/rsonpath | other-userspace | SIMD JSONPath query engine in Rust with descendant support - CPU only user space  actively maintained open source with a benchmark harness |

## All papers
| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | AQUATOPE: QoS-and-Uncertainty-Aware Resource Management for Multi-stage Serverless Workflows | out-machine | Serverless workflow scheduler built on Kubernetes + OpenWhisk across a multi-node FaaS cluster; Docker/k8s not installed and only one machine is available |
| 2 | CAFQA: A Classical Simulation Bootstrap for Variational Quantum Algorithms | out-topic | Quantum variational algorithm compilation |
| 3 | Cooperative Concurrency Control for Write-Intensive Key-Value Workloads | included | In-memory key-value store concurrency control on multicore CPUs - pure user space  fits 16-core host  AE artifact released on Zenodo |
| 4 | DecoMine: A Compilation-Based Graph Pattern Mining System with Pattern Decomposition | out-no-code | Checked GitHub repo search author pages and the ACM entry - no artifact badge and no public DecoMine repository found |
| 5 | Erms: Efficient Resource Management for Shared Microservices with SLA Guarantees | out-machine | Microservice resource manager deployed on a multi-node Kubernetes cluster with container images |
| 6 | Glign: Taming Misaligned Graph Traversals in Concurrent Graph Processing | included | Single-machine concurrent graph-processing runtime - CPU only user space  Zenodo artifact  alignment heuristics are an obvious improvement target |
| 7 | Overlap Communication with Dependent Computation via Decomposition in Large Deep Learning Models | out-machine | Communication/computation decomposition for large models on TPU pods and multi-host XLA |
| 8 | Risotto: A Dynamic Binary Translator for Weak Memory Model Architectures | out-machine | Dynamic binary translator whose contribution is x86-to-Arm weak-memory correctness - needs an Arm host |
| 9 | TelaMalloc: Efficient On-Chip Memory Allocation for Production Machine Learning Accelerators | out-machine | On-chip SRAM allocator for Google TPU accelerators - no commodity-GPU path and artifact is internal |
| 10 | Achieving Sub-second Pairwise Query over Evolving Graphs | out-no-code | SGraph - checked GitHub search authors' pages and ACM entry  no artifact badge and no public repository found |
| 11 | AfterImage: Leaking Control Flow Data and Tracking Load Operations via the Hardware Prefetcher | out-topic | Microarchitectural side-channel security |
| 12 | A Generic Service to Provide In-Network Aggregation for Key-Value Streams | out-machine | In-network aggregation requires programmable switches |
| 13 | A Prediction System Service | out-no-code | Perceptron-based prediction system service - no AE artifact badge and no public implementation found by GitHub or web search |
| 14 | AtoMig: Automatically Migrating Millions Lines of Code from TSO to WMM | out-topic | Source-to-source migration for memory-model correctness |
| 15 | BeeHive: Sub-second Elasticity for Web Services with Semi-FaaS Execution | out-machine | Semi-FaaS offloading needs a distributed FaaS platform plus multiple nodes  no artifact found either |
| 16 | Better Than Worst-Case Decoding for Quantum Error Correction | out-topic | Quantum error correction decoding |
| 17 | Betty: Enabling Large-Scale GNN Training with Batch-Level Graph Partitioning | included | GNN training on a single GPU under memory pressure - batch-level partitioning is exactly a one-GPU memory problem  Zenodo + GitHub artifact |
| 18 | Carbon Explorer: A Holistic Framework for Designing Carbon Aware Datacenters | included | Trace-driven datacenter carbon/capacity simulator - pure Python user space  open source  policies are easy to extend |
| 19 | CommonGraph: Graph Analytics on Evolving Data | out-no-code | Checked GitHub search and author pages - no artifact badge and no public CommonGraph repository found |
| 20 | Compilation Consistency Modulo Debug Information | out-topic | Compiler debug-information consistency |
| 21 | Compiling Distributed System Models with PGo | out-topic | Formal distributed-system model compilation (PlusCal/TLA+) |
| 22 | Copy-on-Pin: The Missing Piece for Correct Copy-on-Write | out-machine | Linux kernel copy-on-write/pinning fix - needs kernel patching and root |
| 23 | Decker: Attack Surface Reduction via On-Demand Code Mapping | out-topic | Attack-surface-reduction security |
| 24 | DeepUM: Tensor Migration and Prefetching in Unified Memory | out-machine | Requires a modified NVIDIA UVM kernel driver (root + kernel module) and no public artifact was found |
| 25 | Ditto: End-to-End Application Cloning for Networked Cloud Services | out-machine | Clones multi-tier networked services across a cluster and captures kernel activity |
| 26 | DPACS: Hardware Accelerated Dynamic Neural Network Pruning through Algorithm-Architecture Co-design | out-machine | FPGA/accelerator co-design for DNN pruning |
| 27 | Ecovisor: A Virtual Energy System for Carbon-Efficient Applications | out-machine | Needs a physical energy system testbed (battery grid-switching programmable power) |
| 28 | ElasticFlow: An Elastic Serverless Training Platform for Distributed Deep Learning | included | DL-training job scheduler with an open trace-driven simulator - simulator runs on CPU; concern the physical testbed uses a multi-GPU cluster |
| 29 | EVStore: Storage and Caching Capabilities for Scaling Embedding Tables in Deep Recommendation Systems | included | Multi-layer embedding-table cache for DLRM inference - single node CPU/GPU user space  cache admission/eviction policy is a clean improvement target |
| 30 | FLAT: An Optimized Dataflow for Mitigating Attention Bottlenecks | out-machine | Attention dataflow for DNN accelerators evaluated with accelerator simulation |
| 31 | FrozenQubits: Boosting Fidelity of QAOA by Skipping Hotspot Nodes | out-topic | Quantum QAOA fidelity |
| 32 | GPU-Initiated On-Demand High-Throughput Storage Access in the BaM System Architecture | out-machine | GPU-initiated NVMe access needs custom kernel drivers and specific SSD hardware |
| 33 | GZKP: A GPU Accelerated Zero-Knowledge Proof System | out-no-code | GPU zero-knowledge-proof system - no AE artifact badge and no public repository found by GitHub or web search |
| 34 | Hacky Racers: Exploiting Instruction-Level Parallelism to Generate Stealthy Fine-Grained Timers | out-topic | Timing side-channel security |
| 35 | Hidet: Task-Mapping Programming Paradigm for Deep Learning Tensor Programs | included | DL compiler with task-mapping scheduling - single NVIDIA GPU actively maintained open source  Ampere supported |
| 36 | HuffDuff: Stealing Pruned DNNs from Sparse Accelerators | out-topic | Model-stealing attack on sparse accelerators |
| 37 | Junkyard Computing: Repurposing Discarded Smartphones to Minimize Carbon | out-machine | Requires racks of discarded smartphones |
| 38 | Khuzdul: Efficient and Scalable Distributed Graph Pattern Mining Engine | out-machine | Distributed multi-node graph pattern mining engine |
| 39 | KIT: Testing OS-Level Virtualization for Functional Interference Bugs | out-machine | Kernel/container virtualization testing needs root and VM control |
| 40 | LeaFTL: A Learning-Based Flash Translation Layer for Solid-State Drives | included | Learned-index flash translation layer - ships a trace-driven SSD simulator that runs in user space; concern the full FEMU setup wants KVM which is unavailable |
| 41 | Lucid: A Non-intrusive, Scalable and Interpretable Scheduler for Deep Learning Training Jobs | included | DL-cluster scheduler evaluated by trace-driven simulation with public traces - runs entirely on one CPU host |
| 42 | MC Mutants: Evaluating and Improving Testing for Memory Consistency Specifications | out-topic | Memory-consistency test generation |
| 43 | Mobius: Fine Tuning Large-Scale Models on Commodity GPU Servers | out-no-code | Pipeline parallelism over several GPUs in one server - no artifact badge and no public repository found; would also need multiple GPUs |
| 44 | MSCCLang: Microsoft Collective Communication Language | out-machine | Collective-communication language for multi-GPU/multi-node systems |
| 45 | Navigating the Dynamic Noise Landscape of Variational Quantum Algorithms with QISMET | out-topic | Quantum noise-aware transpilation |
| 46 | NNSmith: Generating Diverse and Valid Test Cases for Deep Learning Compilers | included | DL-compiler fuzzing - pure user-space Python runs against TVM/ONNXRuntime on one machine  widely used open source |
| 47 | NUBA: Non-Uniform Bandwidth GPUs | out-machine | GPU microarchitecture study in a cycle-level simulator |
| 48 | Optimus-CC: Efficient Large NLP Model Training with 3D Parallelism Aware Communication Compression | out-machine | 3D-parallel training over a multi-node GPU cluster |
| 49 | Pond: CXL-Based Memory Pooling Systems for Cloud Platforms | out-machine | CXL memory pooling hardware |
| 50 | Prism: Optimizing Key-Value Store for Modern Heterogeneous Storage Devices | out-machine | Key-value store design depends on Intel Optane DCPMM persistent memory |
| 51 | Probabilistic Concurrency Testing for Weak Memory Programs | out-topic | Concurrency testing / program verification |
| 52 | Propeller: A Profile Guided, Relinking Optimizer for Warehouse-Scale Applications | out-topic | Post-link compiler/linker optimization; profiling also relies on hardware sampling |
| 53 | Protecting Data Integrity of Web Applications with Database Constraints Inferred from Application Code | out-topic | Web-application data-integrity analysis |
| 54 | Qompress: Efficient Compilation for Ququarts Exploiting Partial and Mixed Radix Operations for Communication Reduction | out-topic | Quantum compilation for ququarts |
| 55 | RAIZN: Redundant Array of Independent Zoned Namespaces | out-machine | Linux device-mapper kernel module over ZNS SSDs - needs root and zoned devices |
| 56 | Revisiting Log-Structured Merging for KV Stores in Hybrid Memory Systems | out-machine | LSM design for DRAM + persistent memory hybrids |
| 57 | Scoped Buffered Persistency Model for GPUs | out-machine | GPU persistency model evaluated in simulation with persistent memory |
| 58 | ShakeFlow: Functional Hardware Description with Latency-Insensitive Interface Combinators | out-topic | Hardware description language |
| 59 | Sigma: Compiling Einstein Summations to Locality-Aware Dataflow | out-machine | Compiler targeting a spatial dataflow accelerator |
| 60 | SMAPPIC: Scalable Multi-FPGA Architecture Prototype Platform in the Cloud | out-machine | Multi-FPGA prototyping platform |
| 61 | Spada: Accelerating Sparse Matrix Multiplication with Adaptive Dataflow | out-machine | Sparse matrix multiplication accelerator |
| 62 | SpecPMT: Speculative Logging for Resolving Crash Consistency Overhead of Persistent Memory | out-machine | Persistent-memory crash consistency |
| 63 | Stepwise Debugging for Hardware Accelerators | out-topic | Hardware accelerator debugging |
| 64 | STI: Turbocharge NLP Inference at the Edge via Elastic Pipelining | out-no-code | Edge transformer inference - checked GitHub and the authors' pages  arXiv preprint only  no implementation released |
| 65 | TensorIR: An Abstraction for Automatic Tensorized Program Optimization | included | Tensorized-program abstraction for TVM - single GPU/CPU auto-scheduling  fully open source and upstreamed into Apache TVM |
| 66 | TiLT: A Time-Centric Approach for Stream Query Optimization and Parallelization | included | Stream-query compiler and runtime - CPU only user space  Zenodo AE artifact |
| 67 | TLP: A Deep Learning-Based Cost Model for Tensor Program Tuning | included | Learned cost model for tensor-program tuning - trains and runs on one GPU  open source  a natural target for better models or cheaper search |
| 68 | Towards a Machine Learning-Assisted Kernel with LAKE | out-machine | Runs ML inference inside the Linux kernel - needs kernel modules and root |
| 69 | uBFT: Microsecond-Scale BFT using Disaggregated Memory | out-machine | BFT over RDMA disaggregated memory |
| 70 | uGrapher: High-Performance Graph Operator Computation via Unified Abstraction for Graph Neural Networks | out-no-code | GNN graph-operator abstraction - no artifact badge and no public repository found by GitHub or web search |
| 71 | VClinic: A Portable and Efficient Framework for Fine-Grained Value Profilers | included | Dynamic-binary-instrumentation value profiler - user space no root or perf counters required  GitHub + Zenodo artifact |
| 72 | VDom: Fast and Unlimited Virtual Domains on Multiple Architectures | out-machine | In-process isolation relying on architecture-specific protection-key hardware |
| 73 | WACO: Learning Workload-Aware Co-optimization of the Format and Schedule of a Sparse Tensor Program | included | Learned cost model that co-optimizes sparse tensor format and schedule - CPU only  GitHub + Zenodo artifact |
| 74 | Where Did My Variable Go? Poking Holes in Incomplete Debug Information | out-topic | Debug-information completeness analysis |
| 75 | ABNDP: Co-optimizing Data Access and Load Balance in Near-Data Processing | out-machine | Near-data-processing architecture evaluated in simulation |
| 76 | Accelerating Sparse Data Orchestration via Dynamic Reflexive Tiling | out-machine | Sparse accelerator tiling hardware |
| 77 | APEX: A Framework for Automated Processing Element Design Space Exploration using Frequent Subgraph Analysis | out-machine | Processing-element hardware design space exploration |
| 78 | Beyond Static Parallel Loops: Supporting Dynamic Task Parallelism on Manycore Architectures with Software-Managed Scratchpad Memories | out-machine | Targets a manycore chip with software-managed scratchpads |
| 79 | CaQR: A Compiler-Assisted Approach for Qubit Reuse through Dynamic Circuit | out-topic | Quantum qubit-reuse compilation |
| 80 | CaT: A Solver-Aided Compiler for Packet-Processing Pipelines | out-machine | Compiler for programmable switch packet pipelines |
| 81 | Characterizing and Optimizing End-to-End Systems for Private Inference | included | End-to-end characterization and optimization of private-inference serving - client and server can be two processes on one host with one GPU; concern the contribution is partly cryptographic-protocol level |
| 82 | Cohort: Software-Oriented Acceleration for Heterogeneous SoCs | out-machine | Heterogeneous SoC hardware acceleration |
| 83 | Coyote: A Compiler for Vectorizing Encrypted Arithmetic Circuits | out-topic | Compiler for encrypted arithmetic circuits |
| 84 | DefT: Boosting Scalability of Deformable Convolution Operations on GPUs | out-no-code | GPU deformable-convolution kernel work - no artifact badge and no public repository found by GitHub or web search |
| 85 | Disaggregated RAID Storage in Modern Datacenters | out-machine | RAID over disaggregated NVMe-oF storage across nodes |
| 86 | DrGPUM: Guiding Memory Optimization for GPU-Accelerated Applications | included | GPU memory profiler built on CUPTI - single GPU user space no root or perf counters  GitHub + Zenodo artifact |
| 87 | Efficient Compactions between Storage Tiers with PrismDB | included | LSM key-value store with tier-aware compaction - user-space RocksDB-style engine on NVMe  GitHub + Zenodo artifact; concern the paper uses QLC+SLC tiers that must be emulated here |
| 88 | Efficient Scheduler Live Update for Linux Kernel with Modularization | out-machine | Live update of the Linux kernel scheduler - kernel modules and root |
| 89 | eHDL: Turning eBPF/XDP Programs into Hardware Designs for the NIC | out-machine | Compiles eBPF/XDP to NIC hardware; eBPF is disabled for unprivileged users |
| 90 | Exit-Less, Isolated, and Shared Access for Virtual Machines | out-machine | Virtual machine I/O path requiring KVM |
| 91 | Finding Unstable Code via Compiler-Driven Differential Testing | out-topic | Compiler differential testing |
| 92 | Flexagon: A Multi-dataflow Sparse-Sparse Matrix Multiplication Accelerator for Efficient DNN Processing | out-machine | Sparse-sparse matmul accelerator |
| 93 | Going beyond the Limits of SFI: Flexible and Secure Hardware-Assisted In-Process Isolation with HFI | out-topic | Hardware-assisted isolation security extension |
| 94 | GRACE: A Scalable Graph-Based Approach to Accelerating Recommendation Model Inference | included | Graph-based acceleration of recommendation-model inference on one CPU/GPU node - GitHub + Zenodo artifact |
| 95 | Graphene: An IR for Optimized Tensor Computations on GPUs | out-no-code | NVIDIA-internal tensor IR - no artifact badge and no public release found |
| 96 | Heron: Automatically Constrained High-Performance Library Generation for Deep Learning Accelerators | included | Constrained auto-scheduling for tensor libraries - supports NVIDIA tensor-core GPUs and CPUs; concern part of the evaluation uses a Cambricon accelerator we do not have |
| 97 | Homunculus: Auto-Generating Efficient Data-Plane ML Pipelines for Datacenter Networks | out-machine | Generates ML pipelines for programmable data-plane switches |
| 98 | Hyperscale Hardware Optimized Neural Architecture Search | out-machine | NAS for Google TPU fleets |
| 99 | Infinity Stream: Portable and Programmer-Friendly In-/Near-Memory Fusion | out-machine | In-/near-memory fusion evaluated in gem5-class simulation |
| 100 | In-Network Aggregation with Transport Transparency for Distributed Training | out-machine | In-network aggregation on switches for distributed training |
| 101 | Kodan: Addressing the Computational Bottleneck in Space | out-no-code | Orbital edge computing - checked GitHub (CMUAbstract) and web  the ASPLOS20 OEC artifact exists but no Kodan release was found |
| 102 | LEGO: Empowering Chip-Level Functionality Plug-and-Play for Next-Generation IoT Devices | out-machine | IoT chip-level hardware plug-and-play |
| 103 | Mapping Very Large Scale Spiking Neuron Network to Neuromorphic Hardware | out-machine | Neuromorphic hardware mapping |
| 104 | Mosaic Pages: Big TLB Reach with Small Pages | out-machine | TLB microarchitecture proposal evaluated in architectural simulation |
| 105 | MP-Rec: Hardware-Software Co-design to Enable Multi-path Recommendation | out-machine | Co-design needs several accelerator types (GPU TPU and custom) to select among embedding paths |
| 106 | NosWalker: A Decoupled Architecture for Out-of-Core Random Walk Processing | out-no-code | Out-of-core random-walk engine - no artifact badge and no public repository found by GitHub or web search |
| 107 | Occamy: Elastically Sharing a SIMD Co-processor across Multiple CPU Cores | out-machine | Shared SIMD co-processor hardware |
| 108 | Persistent Memory Disaggregation for Cloud-Native Relational Databases | out-machine | Disaggregated persistent memory with RDMA |
| 109 | PipeSynth: Automated Synthesis of Microarchitectural Axioms for Memory Consistency | out-topic | Formal synthesis of memory-consistency axioms |
| 110 | Protect the System Call, Protect (Most of) the World with BASTION | out-topic | System-call integrity security monitor |
| 111 | Re-architecting I/O Caches for Emerging Fast Storage Devices | out-machine | I/O cache modules live in the Linux block layer (device mapper) and the study needs enterprise all-flash arrays |
| 112 | Reconfigurable Virtual Memory for FPGA-Driven I/O | out-machine | FPGA-driven I/O virtual memory |
| 113 | RepCut: Superlinear Parallel RTL Simulation with Replication-Aided Partitioning | included | Parallel RTL simulation by replication-aided partitioning - CPU-only user-space simulator that scales with the 16 cores here  Zenodo AE artifact |
| 114 | Rosebud: Making FPGA-Accelerated Middlebox Development More Pleasant | out-machine | FPGA middlebox framework |
| 115 | Simulator Independent Coverage for RTL Hardware Languages | out-topic | RTL coverage tooling |
| 116 | Skybox: Open-Source Graphic Rendering on Programmable RISC-V GPUs | out-machine | RISC-V GPU on FPGA |
| 117 | Snape: Reliable and Low-Cost Computing with Mixture of Spot and On-Demand VMs | out-no-code | Spot/on-demand VM mixing policy with RL on Azure traces - no artifact badge and no public code or trace release found |
| 118 | Space-Efficient TREC for Enabling Deep Learning on Microcontrollers | out-machine | Deep learning on microcontrollers - needs MCU boards |
| 119 | SparseTIR: Composable Abstractions for Sparse Compilation in Deep Learning | included | Sparse tensor compilation for DL on a single NVIDIA GPU - GitHub + Zenodo AE artifact  well documented |
| 120 | SPLENDID: Supporting Parallel LLVM-IR Enhanced Natural Decompilation for Interactive Development | out-topic | Decompilation / parallelizing compiler tooling |
| 121 | TeraHeap: Reducing Memory Pressure in Managed Big Data Frameworks | included | Adds an NVMe-backed second heap to the JVM to cut GC pressure for Spark/Giraph - user-space OpenJDK build on one node  GitHub + Zenodo artifact |
| 122 | The Sparse Abstract Machine | out-machine | Abstract machine for sparse tensor hardware evaluated with a hardware simulator |
| 123 | Towards an Adaptable Systems Architecture for Memory Tiering at Warehouse-Scale | out-no-code | Google production memory-tiering system (TMTS) - deployment paper with no released implementation |
| 124 | TPP: Transparent Page Placement for CXL-Enabled Tiered-Memory | out-machine | Linux kernel page placement for CXL tiered memory |
| 125 | Transparent Runtime Change Handling for Android Apps | out-machine | Android runtime - needs the Android stack and devices |
| 126 | Untangle: A Principled Framework to Design Low-Leakage, High-Performance Dynamic Partitioning Schemes | out-topic | Cache-partitioning security against side channels |
| 127 | Verification of Nondeterministic Quantum Programs | out-topic | Quantum program verification |
| 128 | Vidi: Record Replay for Reconfigurable Hardware | out-machine | Record/replay for FPGA hardware |
| 129 | Accurate Disassembly of Complex Binaries Without Use of Compiler Metadata | out-topic | Binary disassembly / reverse engineering |
| 130 | BaCO: A Fast and Portable Bayesian Compiler Optimization Framework | included | Bayesian autotuner for compiler/scheduling search spaces (TACO RISE HPVM) - pure user-space Python on one CPU/GPU node  open source |
| 131 | CPS: A Cooperative Para-virtualized Scheduling Framework for Manycore Machines | out-machine | Para-virtualized scheduling needs hypervisor and kernel changes |
| 132 | DataFlower: Exploiting the Data-flow Paradigm for Serverless Workflow Orchestration | out-machine | Serverless workflow orchestration evaluated on a container cluster across nodes |
| 133 | DREAM: A Dynamic Scheduler for Dynamic Real-time Multi-model ML Workloads | out-machine | Scheduler for a multi-tenant DNN accelerator evaluated in a cycle-level accelerator simulator |
| 134 | Explainable-DSE: An Agile and Explainable Exploration of Efficient HW/SW Codesigns of Deep Learning Accelerators Using Bottleneck Analysis | out-topic | Design-space exploration of DNN accelerator hardware |
| 135 | Exploiting the Regular Structure of Modern Quantum Architectures for Compiling and Optimizing Programs with Permutable Operators | out-topic | Quantum program compilation |
| 136 | Fast Instruction Selection for Fast Digital Signal Processing | out-topic | Instruction selection for DSP compilers |
| 137 | FITS: Inferring Intermediate Taint Sources for Effective Vulnerability Analysis of IoT Device Firmware | out-topic | IoT firmware vulnerability analysis |
| 138 | Flame: A Centralized Cache Controller for Serverless Computing | out-no-code | Serverless function-cache controller - no artifact badge and no public repository found by GitHub or web search |
| 139 | FreePart: Hardening Data Processing Software via Framework-based Partitioning and Isolation | out-topic | Software partitioning/isolation security |
| 140 | HIR: An MLIR-based Intermediate Representation for Hardware Accelerator Description | out-topic | MLIR dialect for hardware accelerator description |
| 141 | LightRidge: An End-to-end Agile Design Framework for Diffractive Optical Neural Networks | out-machine | Diffractive optical neural network hardware |
| 142 | Manticore: Hardware-Accelerated RTL Simulation with Static Bulk-Synchronous Parallelism | out-machine | RTL simulation on a many-core FPGA/manycore accelerator |
| 143 | MiniMalloc: A Lightweight Memory Allocator for Hardware-Accelerated Machine Learning | included | Offline static memory allocator (2D packing solver) for ML accelerator buffers - single-threaded C++ CPU solver with open benchmarks  fully open source |
| 144 | Predict; Don't React for Enabling Efficient Fine-Grain DVFS in GPUs | out-machine | GPU hardware DVFS controller |
| 145 | RECom: A Compiler Approach to Accelerating Recommendation Model Inference with Massive Embedding Columns | included | Compiler that fuses massive embedding-column subgraphs for recommendation inference on one GPU - open source from Alibaba |
| 146 | ShapleyIQ: Influence Quantification by Shapley Values for Performance Debugging of Microservices | included | Shapley-value performance attribution for microservice traces - code and data released; analysis runs offline on traces on one host  concern the original setting is a production cluster |
| 147 | Sleuth: A Trace-Based Root Cause Analysis System for Large-Scale Microservices with Graph Neural Networks | out-no-code | GNN-based trace root-cause analysis - no artifact badge and no public repository or dataset release found |
| 148 | Supporting Descendants in SIMD-Accelerated JSONPath | included | SIMD JSONPath query engine in Rust with descendant support - CPU only user space  actively maintained open source with a benchmark harness |
| 149 | VarSaw: Application-tailored Measurement Error Mitigation for Variational Quantum Algorithms | out-topic | Quantum measurement error mitigation |
| 150 | Veil: A Protected Services Framework for Confidential Virtual Machines | out-machine | Confidential VM services require AMD SEV-SNP and hypervisor control |
| 151 | λFS: A Scalable and Elastic Distributed File System Metadata Service using Serverless Functions | out-machine | Distributed file system metadata service on cloud serverless functions across many nodes |
