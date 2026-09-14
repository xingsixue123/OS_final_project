STATUS: complete
TOTAL_PAPERS: 250
INCLUDED: 93

## Sources

Primary list: the official SIGMOD 2025 conference site, Accepted Papers for SIGMOD
(https://2025.sigmod.org/sigmod_papers.shtml). That page groups the research-track
papers presented in Berlin (June 22-27, 2025) into the four submission rounds of the
2025 cycle: Round 1 = 17, Round 2 = 30, Round 3 = 85, Round 4 = 118, total 250.

Second source for titles, DOIs and abstracts: the ACM OpenTOC pages the same site links
to, which are served from the ACM Digital Library:
- https://2025.sigmod.org/toc-2-6.html (PACMMOD Vol. 2, No. 6, Dec 2024) - 30 papers
- https://2025.sigmod.org/toc-3-1.html (PACMMOD Vol. 3, No. 1, Feb 2025) - 85 papers
- https://2025.sigmod.org/toc-3-3.html (PACMMOD Vol. 3, No. 3, Jun 2025) - 118 papers
These three issues account for Rounds 2-4 (233 papers). The 17 Round-1 papers are
published in PACMMOD Vol. 2, No. 4 (Aug 2024), which the conference site does not link.

Cross-check of the count: the Crossref REST API for the PACMMOD journal (ISSN
2836-6573), https://api.crossref.org/journals/2836-6573/works, returns 18 / 31 / 86 /
119 records for volumes 2(4), 2(6), 3(1) and 3(3) respectively. Each issue contains
exactly one PACMMOD editorial, so the paper counts are 17 / 30 / 85 / 118 = 250, which
matches the per-round counts on the conference site exactly. Titles, DOIs and abstracts
used for screening come from this Crossref pull; the master list is in
scratch/papers.json.

DBLP could not be used - dblp.org and its mirrors are currently behind an anti-bot
proof-of-work challenge that blocks both the HTML pages and the search API.

PODS papers (PACMMOD Vol. 3, No. 2), SIGMOD industry-track papers, demos, tutorials and
workshop papers are excluded, as instructed (main research track only).

Paper links are the ACM DL DOI landing pages; PACMMOD is fully open access, so the
direct PDF is the same DOI under /doi/pdf/. Repository links were located by searching
the GitHub repository index for each system name plus distinguishing keywords, and by
URLs given in the paper abstracts. Where a search returned nothing that is
identifiably the authors' artifact, the repo is recorded as unknown rather than as
out-no-code, since a desk check of the GitHub index alone is not conclusive.

## Included
| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | Adaptive Quotient Filters | https://dl.acm.org/doi/10.1145/3677128 | https://dl.acm.org/doi/pdf/10.1145/3677128 | https://github.com/splatlab/adaptiveqf | storage | Filter/auxiliary-structure design for KV stores; pure user-space C/C++ data structure, trivially fits one machine |
| 2 | Atom: An Efficient Query Serving System for Embedding-based Knowledge Graph Reasoning with Operator-level Batching | https://dl.acm.org/doi/10.1145/3677129 | https://dl.acm.org/doi/pdf/10.1145/3677129 | unknown | ml-systems | Operator-level batching and scheduling for an embedding-model query serving system; single-GPU serving workload |
| 3 | BT-Tree: A Reinforcement Learning Based Index for Big Trajectory Data | https://dl.acm.org/doi/10.1145/3677130 | https://dl.acm.org/doi/pdf/10.1145/3677130 | unknown | ml-for-systems | Learned/RL-built index structure; CPU-only, user space |
| 4 | CAMAL: Optimizing LSM-trees via Active Learning | https://dl.acm.org/doi/10.1145/3677138 | https://dl.acm.org/doi/pdf/10.1145/3677138 | unknown | ml-for-systems | Active-learning tuner for LSM-tree knobs integrated into RocksDB; single-node, user space |
| 5 | Tao: Improving Resource Utilization while Guaranteeing SLO in Multi-tenant Relational Database-as-a-Service | https://dl.acm.org/doi/10.1145/3677141 | https://dl.acm.org/doi/pdf/10.1145/3677141 | unknown | scheduling | Coroutine-based tasklet scheduler with SLO guarantees on top of the open-source Hyrise DBMS; pure user-space CPU scheduling |
| 6 | Camel: Efficient Compression of Floating-Point Time Series | https://dl.acm.org/doi/10.1145/3698802 | https://dl.acm.org/doi/pdf/10.1145/3698802 | unknown | storage | Floating-point compression codec plus index; user-space library |
| 7 | High-Performance Query Processing with NVMe Arrays: Spilling without Killing Performance | https://dl.acm.org/doi/10.1145/3698813 | https://dl.acm.org/doi/pdf/10.1145/3698813 | unknown | storage | Out-of-memory hash operators and spilling compression on NVMe; machine has 2 NVMe devices so a scaled-down study is possible - concern: paper uses a larger NVMe array |
| 8 | iRangeGraph: Improvising Range-dedicated Graphs for Range-filtering Nearest Neighbor Search | https://dl.acm.org/doi/10.1145/3698814 | https://dl.acm.org/doi/pdf/10.1145/3698814 | https://github.com/YuexuanXu7/iRangeGraph | other-userspace | In-memory graph index for range-filtered ANN; single-machine C++ |
| 9 | Live Patching for Distributed In-Memory Key-Value Stores | https://dl.acm.org/doi/10.1145/3698816 | https://dl.acm.org/doi/pdf/10.1145/3698816 | unknown | other-userspace | User-space live patching of Redis processes; concern - built for a Redis Cluster, would need multiple processes on one host |
| 10 | LSMGraph: A High-Performance Dynamic Graph Storage System with Multi-Level CSR | https://dl.acm.org/doi/10.1145/3698818 | https://dl.acm.org/doi/pdf/10.1145/3698818 | https://github.com/iDC-NEU/LSMGraph | storage | LSM-tree + CSR hybrid disk-based graph storage engine; single machine |
| 11 | Memento Filter: A Fast, Dynamic, and Robust Range Filter | https://dl.acm.org/doi/10.1145/3698820 | https://dl.acm.org/doi/pdf/10.1145/3698820 | https://github.com/n3slami/Memento_Filter | storage | Range filter data structure for LSM key-value stores; user-space C++ |
| 12 | Navigating Labels and Vectors: A Unified Approach to Filtered Approximate Nearest Neighbor Search | https://dl.acm.org/doi/10.1145/3698822 | https://dl.acm.org/doi/pdf/10.1145/3698822 | https://github.com/YZ-Cai/Unified-Navigating-Graph | other-userspace | Graph index for filtered ANN search; single-machine in-memory |
| 13 | CtxPipe: Context-aware Data Preparation Pipeline Construction for Machine Learning | https://dl.acm.org/doi/10.1145/3698831 | https://dl.acm.org/doi/pdf/10.1145/3698831 | https://github.com/ctxpipe/ctxpipe | ml-systems | Automatic construction of ML data-preparation pipelines; CPU-bound, user space |
| 14 | Pasta: A Cost-Based Optimizer for Generating Pipelining Schedules for Dataflow DAGs | https://dl.acm.org/doi/10.1145/3698832 | https://dl.acm.org/doi/pdf/10.1145/3698832 | unknown | scheduling | Cost-based scheduler for pipelined execution of dataflow DAGs; user-space scheduling problem |
| 15 | λ-Tune: Harnessing Large Language Models for Automated Database System Tuning | https://dl.acm.org/doi/10.1145/3709652 | https://dl.acm.org/doi/pdf/10.1145/3709652 | https://github.com/gsvic/lambda-tune | ml-for-systems | LLM-driven DBMS knob tuning on PostgreSQL/MySQL; concern - needs external LLM API access |
| 16 | AquaPipe: A Quality-Aware Pipeline for Knowledge Retrieval and Large Language Models | https://dl.acm.org/doi/10.1145/3709661 | https://dl.acm.org/doi/pdf/10.1145/3709661 | unknown | llm-inference | Pipelines disk-based ANNS retrieval with LLM prefill in a RAG serving system; 7B-class models fit 24 GB |
| 17 | Aster: Enhancing LSM-structures for Scalable Graph Database | https://dl.acm.org/doi/10.1145/3709662 | https://dl.acm.org/doi/pdf/10.1145/3709662 | https://github.com/NTU-Siqiang-Group/Aster | storage | Graph-oriented LSM key-value storage engine; single machine |
| 18 | Automatic Database Configuration Debugging using Retrieval-Augmented Language Models | https://dl.acm.org/doi/10.1145/3709663 | https://dl.acm.org/doi/pdf/10.1145/3709663 | unknown | ml-for-systems | RAG/LLM-based DBMS configuration diagnosis; concern - needs LLM API access |
| 19 | B-Trees Are Back: Engineering Fast and Pageable Node Layouts | https://dl.acm.org/doi/10.1145/3709664 | https://dl.acm.org/doi/pdf/10.1145/3709664 | unknown | storage | Engineering study of pageable B-Tree node layouts with variable-size records; user-space storage engine |
| 20 | Capsule: An Out-of-Core Training Mechanism for Colossal GNNs | https://dl.acm.org/doi/10.1145/3709669 | https://dl.acm.org/doi/pdf/10.1145/3709669 | https://github.com/USTC-DataDarknessLab/Capsule | ml-systems | Out-of-core GNN training that keeps computation on one GPU; designed for limited GPU memory |
| 21 | Cardinality Estimation of LIKE Predicate Queries using Deep Learning | https://dl.acm.org/doi/10.1145/3709670 | https://dl.acm.org/doi/pdf/10.1145/3709670 | https://github.com/sykwon/sigmod2025like | ml-for-systems | Learned cardinality estimator inside the query optimizer; CPU/GPU training fits one node |
| 22 | Centrum: Model-based Database Auto-tuning with Minimal Distributional Assumptions | https://dl.acm.org/doi/10.1145/3709671 | https://dl.acm.org/doi/pdf/10.1145/3709671 | unknown | ml-for-systems | Model-based DBMS auto-tuning; single-node tuning loop |
| 23 | Data Chunk Compaction in Vectorized Execution | https://dl.acm.org/doi/10.1145/3709676 | https://dl.acm.org/doi/pdf/10.1145/3709676 | https://github.com/embryo-labs/Chunk-Compaction-in-Vectorized-Execution | ml-for-systems | Learning-based runtime decision inside a vectorized engine (DuckDB); user space |
| 24 | DEG: Efficient Hybrid Vector Search Using the Dynamic Edge Navigation Graph | https://dl.acm.org/doi/10.1145/3709679 | https://dl.acm.org/doi/pdf/10.1145/3709679 | https://github.com/Heisenberg-Yin/DEG | other-userspace | Graph-based ANN index for hybrid vector queries; single machine |
| 25 | Disco: A Compact Index for LSM-trees | https://dl.acm.org/doi/10.1145/3709683 | https://dl.acm.org/doi/pdf/10.1145/3709683 | https://github.com/SheldonZhong/disco | storage | Compact index for LSM-trees, integrated in a key-value store; user space |
| 26 | Efficiently Processing Joins and Grouped Aggregations on GPUs | https://dl.acm.org/doi/10.1145/3709689 | https://dl.acm.org/doi/pdf/10.1145/3709689 | https://github.com/BowenforGit/sigmod25-reprod | other-userspace | GPU join and group-by operator optimizations; single GPU, fits a 24 GB A5000 |
| 27 | Graph-Based Vector Search: An Experimental Evaluation of the State-of-the-Art | https://dl.acm.org/doi/10.1145/3709693 | https://dl.acm.org/doi/pdf/10.1145/3709693 | https://github.com/iliasazizi/GVS | other-userspace | Experimental evaluation and unified framework for graph-based vector search; concern - largest datasets are 1B vectors, would need scale-down |
| 28 | LCP: Enhancing Scientific Data Management with L ossy C ompression for P articles | https://dl.acm.org/doi/10.1145/3709700 | https://dl.acm.org/doi/pdf/10.1145/3709700 | unknown | storage | Lossy compressor for particle data; user-space library, CPU |
| 29 | LeaFi: Data Series Indexes on Steroids with Learned Filters | https://dl.acm.org/doi/10.1145/3709701 | https://dl.acm.org/doi/pdf/10.1145/3709701 | https://github.com/qtwang/LeaFi | ml-for-systems | Learned filters that improve pruning inside tree-based data series indexes |
| 30 | MAST: Towards Efficient Analytical Query Processing on Point Cloud Data | https://dl.acm.org/doi/10.1145/3709702 | https://dl.acm.org/doi/pdf/10.1145/3709702 | https://github.com/gravesprite/MAST | ml-systems | Approximate invocation of deep models for point-cloud analytical queries; single-GPU inference |
| 31 | MEMO: Fine-grained Tensor Management For Ultra-long Context LLM Training | https://dl.acm.org/doi/10.1145/3709703 | https://dl.acm.org/doi/pdf/10.1145/3709703 | https://github.com/pinxuezhao/MEMO | ml-systems | Activation offloading and fine-grained tensor/memory management for long-context LLM training; concern - evaluated on a multi-GPU node, needs scale-down to one A5000 |
| 32 | Modyn: Data-Centric Machine Learning Pipeline Orchestration | https://dl.acm.org/doi/10.1145/3709705 | https://dl.acm.org/doi/pdf/10.1145/3709705 | https://github.com/eth-easl/modyn | ml-systems | Open-source orchestration platform for continuous ML training pipelines; runs on one node |
| 33 | Optimizing Block Skipping for High-Dimensional Data with Learned Adaptive Curve | https://dl.acm.org/doi/10.1145/3709710 | https://dl.acm.org/doi/pdf/10.1145/3709710 | unknown | ml-for-systems | Learned space-filling curve for data layout and block skipping; user space |
| 34 | Parallel kd-tree with Batch Updates | https://dl.acm.org/doi/10.1145/3709712 | https://dl.acm.org/doi/pdf/10.1145/3709712 | https://github.com/ucrparlay/Pkd-tree | other-userspace | Parallel cache-efficient in-memory kd-tree for a 16-core machine |
| 35 | Randomized Sketches for Quantile in LSM-tree based Store | https://dl.acm.org/doi/10.1145/3709717 | https://dl.acm.org/doi/pdf/10.1145/3709717 | unknown | storage | Pre-computed randomized sketches stored in LSM components; user-space KV store change |
| 36 | Revisiting the Design of In-Memory Dynamic Graph Storage | https://dl.acm.org/doi/10.1145/3709720 | https://dl.acm.org/doi/pdf/10.1145/3709720 | https://github.com/SJTU-Liquid/DynamicGraphStorage | storage | Common abstraction plus generic test framework for in-memory dynamic graph storage; strong reproduction/improvement target on one machine |
| 37 | Subspace Collision: An Efficient and Accurate Framework for High-dimensional Approximate Nearest Neighbor Search | https://dl.acm.org/doi/10.1145/3709729 | https://dl.acm.org/doi/pdf/10.1145/3709729 | https://github.com/WeiJiuQi/SuCo | other-userspace | Clustering-based ANN index framework; single machine |
| 38 | SymphonyQG: Towards Symphonious Integration of Quantization and Graph for Approximate Nearest Neighbor Search | https://dl.acm.org/doi/10.1145/3709730 | https://dl.acm.org/doi/pdf/10.1145/3709730 | unknown | other-userspace | SIMD-friendly integration of quantization and graph ANN index; CPU-only, cache/memory-access focused |
| 39 | TGraph: A Tensor-centric Graph Processing Framework | https://dl.acm.org/doi/10.1145/3709731 | https://dl.acm.org/doi/pdf/10.1145/3709731 | unknown | ml-systems | Graph processing expressed on tensor runtimes (PyTorch-style backends); runs on a single GPU |
| 40 | VEGA: An Active-tuning Learned Index with Group-Wise Learning Granularity | https://dl.acm.org/doi/10.1145/3709736 | https://dl.acm.org/doi/pdf/10.1145/3709736 | unknown | ml-for-systems | Learned index with online model building under a memory budget; user space |
| 41 | DiskGNN: Bridging I/O Efficiency and Model Accuracy for Out-of-Core GNN Training | https://dl.acm.org/doi/10.1145/3709738 | https://dl.acm.org/doi/pdf/10.1145/3709738 | https://github.com/Liu-rj/DiskGNN | ml-systems | Disk-based out-of-core GNN training with I/O-efficient feature packing; single GPU plus NVMe |
| 42 | Tribase: A Vector Data Query Engine for Reliable and Lossless Pruning Compression using Triangle Inequalities | https://dl.acm.org/doi/10.1145/3709743 | https://dl.acm.org/doi/pdf/10.1145/3709743 | https://github.com/xuqianmamba/Tribase | other-userspace | Cluster-based vector query engine with pruning; CPU, single machine |
| 43 | A New Paradigm in Tuning Learned Indexes: A Reinforcement Learning Enhanced Approach | https://dl.acm.org/doi/10.1145/3725257 | https://dl.acm.org/doi/pdf/10.1145/3725257 | unknown | ml-for-systems | RL-based end-to-end tuner for learned index structures; user space |
| 44 | Accelerating Graph Indexing for ANNS on Modern CPUs | https://dl.acm.org/doi/10.1145/3725260 | https://dl.acm.org/doi/pdf/10.1145/3725260 | https://github.com/ZJU-DAILY/HNSW-Flash | other-userspace | SIMD and memory-access optimizations for HNSW-style graph index construction on modern CPUs |
| 45 | Alsatian: Optimizing Model Search for Deep Transfer Learning | https://dl.acm.org/doi/10.1145/3725264 | https://dl.acm.org/doi/pdf/10.1145/3725264 | https://github.com/hpides/alsatian | ml-systems | Model search system that shares inference work across candidate models; single GPU |
| 46 | Cache-Craft: Managing Chunk-Caches for Efficient Retrieval-Augmented Generation | https://dl.acm.org/doi/10.1145/3725273 | https://dl.acm.org/doi/pdf/10.1145/3725273 | unknown | llm-inference | KV-cache reuse for RAG chunks; core KV-cache management topic, single-GPU 7B-class models feasible |
| 47 | Debunking the Myth of Join Ordering: Toward Robust SQL Analytics | https://dl.acm.org/doi/10.1145/3725283 | https://dl.acm.org/doi/pdf/10.1145/3725283 | https://github.com/embryo-labs/Robust-Predicate-Transfer | other-userspace | Predicate transfer integrated into DuckDB for join-order robustness; single node, user space |
| 48 | FAAQP: Fast and Accurate Approximate Query Processing based on Bitmap-augmented Sum-Product Network | https://dl.acm.org/doi/10.1145/3725292 | https://dl.acm.org/doi/pdf/10.1145/3725292 | unknown | ml-for-systems | Learned sum-product-network model used inside the DBMS for approximate query answering |
| 49 | Fast and Scalable Data Transfer Across Data Systems | https://dl.acm.org/doi/10.1145/3725294 | https://dl.acm.org/doi/pdf/10.1145/3725294 | https://github.com/polydbms/xdbc | other-userspace | Configurable data-transfer pipeline framework between data systems; can be run as processes on one host |
| 50 | Femur: A Flexible Framework for Fast and Secure Querying from Public Key-Value Store | https://dl.acm.org/doi/10.1145/3725299 | https://dl.acm.org/doi/pdf/10.1145/3725299 | https://github.com/alibaba-edu/mpc4j | storage | Learned-index-based key-value retrieval framework with tunable security; user-space, single machine |
| 51 | Galley: Modern Query Optimization for Sparse Tensor Programs | https://dl.acm.org/doi/10.1145/3725301 | https://dl.acm.org/doi/pdf/10.1145/3725301 | https://github.com/kylebd99/Galley | ml-systems | Cost-based optimizer/compiler for sparse tensor programs; ML-compiler topic, single node |
| 52 | Rule-Based Graph Cleaning with GPUs on a Single Machine | https://dl.acm.org/doi/10.1145/3725303 | https://dl.acm.org/doi/pdf/10.1145/3725303 | unknown | other-userspace | Explicitly a single-machine CPU+GPU+IO pipelined system; fits the target machine by construction |
| 53 | GTX: A Write-Optimized Latch-free Graph Data System with Transactional Support | https://dl.acm.org/doi/10.1145/3725305 | https://dl.acm.org/doi/pdf/10.1145/3725305 | https://github.com/purduedb/gfe_driver_sigmod2025 | storage | Main-memory latch-free graph store with transactions and concurrency control; multicore user space |
| 54 | HoneyComb: A Parallel Worst-Case Optimal Join on Multicores | https://dl.acm.org/doi/10.1145/3725307 | https://dl.acm.org/doi/pdf/10.1145/3725307 | unknown | other-userspace | Parallel worst-case optimal join engineered for large multicore shared-memory machines |
| 55 | How Good are Learned Cost Models, Really? Insights from Query Optimization Tasks | https://dl.acm.org/doi/10.1145/3725309 | https://dl.acm.org/doi/pdf/10.1145/3725309 | https://github.com/DataManagementLab/lcm-eval | ml-for-systems | Systematic evaluation of learned cost models in query optimization; reproduction-friendly, single node |
| 56 | How to Grow an LSM-tree? Towards Bridging the Gap Between Theory and Practice | https://dl.acm.org/doi/10.1145/3725310 | https://dl.acm.org/doi/pdf/10.1145/3725310 | unknown | storage | LSM-tree growth scheme design and analysis with a prototype key-value store |
| 57 | Intra-Query Runtime Elasticity for Cloud-Native Data Analysis | https://dl.acm.org/doi/10.1145/3725315 | https://dl.acm.org/doi/pdf/10.1145/3725315 | https://github.com/Blueratzxk/Accordion_engine | scheduling | Runtime elasticity - changing degree of parallelism mid-query; concern - built on Presto, which is normally run distributed |
| 58 | Learned Offline Query Planning via Bayesian Optimization | https://dl.acm.org/doi/10.1145/3725316 | https://dl.acm.org/doi/pdf/10.1145/3725316 | unknown | ml-for-systems | Offline learned query planner using Bayesian optimization on PostgreSQL |
| 59 | Maximus: A Modular Accelerated Query Engine for Data Analytics on Heterogeneous Systems | https://dl.acm.org/doi/10.1145/3725324 | https://dl.acm.org/doi/pdf/10.1145/3725324 | unknown | other-userspace | Modular CPU+GPU query engine; concern - the paper also targets DPUs/SmartNICs and disaggregated memory, only the CPU/GPU part is reproducible here |
| 60 | MIRAGE-ANNS: Mixed Approach Graph-based Indexing for Approximate Nearest Neighbor Search | https://dl.acm.org/doi/10.1145/3725325 | https://dl.acm.org/doi/pdf/10.1145/3725325 | https://github.com/dsg-uwaterloo/mirage | other-userspace | Graph-based ANN index combining clustering and graph traversal; single machine |
| 61 | Mitigating the Impedance Mismatch between Prediction Query Execution and Database Engine | https://dl.acm.org/doi/10.1145/3725326 | https://dl.acm.org/doi/pdf/10.1145/3725326 | unknown | ml-systems | Prediction-aware operator with inference context reuse and batching inside a DB engine; single GPU |
| 62 | Mnemosyne: Dynamic Workload-Aware BF Tuning via Accurate Statistics in LSM trees | https://dl.acm.org/doi/10.1145/3725327 | https://dl.acm.org/doi/pdf/10.1145/3725327 | https://github.com/BU-DiSC/Mnemosyne | storage | Workload-aware Bloom filter memory allocation in LSM-trees; user-space KV store |
| 63 | Moving on From Group Commit: Autonomous Commit Enables High Throughput and Low Latency on NVMe SSDs | https://dl.acm.org/doi/10.1145/3725328 | https://dl.acm.org/doi/pdf/10.1145/3725328 | https://github.com/leanstore/leanstore/tree/latency | storage | Commit/logging protocol tuned for NVMe SSD parallelism; user-space DBMS change, machine has NVMe |
| 64 | Nested Parquet Is Flat, Why Not Use It? How To Scan Nested Data With On-the-Fly Key Generation and Joins | https://dl.acm.org/doi/10.1145/3725329 | https://dl.acm.org/doi/pdf/10.1145/3725329 | unknown | storage | Scanning nested Parquet efficiently in a relational engine; pure user-space file-format work |
| 65 | NEXT: A New Secondary Index Framework for LSM-based Data Storage | https://dl.acm.org/doi/10.1145/3725330 | https://dl.acm.org/doi/pdf/10.1145/3725330 | unknown | storage | Secondary index framework for LSM-based key-value stores |
| 66 | PDX: A Data Layout for Vector Similarity Search | https://dl.acm.org/doi/10.1145/3725333 | https://dl.acm.org/doi/pdf/10.1145/3725333 | https://github.com/cwida/PDX | other-userspace | Vector data layout that changes memory access patterns and auto-vectorization; CPU-only, single machine |
| 67 | PLM4NDV: Minimizing Data Access for Number of Distinct Values Estimation with Pre-trained Language Models | https://dl.acm.org/doi/10.1145/3725336 | https://dl.acm.org/doi/pdf/10.1145/3725336 | https://github.com/bytedance/plm4ndv | ml-for-systems | Pre-trained language model used as a learned estimator inside the DBMS; code released by ByteDance |
| 68 | PQCache: Product Quantization-based KVCache for Long Context LLM Inference | https://dl.acm.org/doi/10.1145/3725338 | https://dl.acm.org/doi/pdf/10.1145/3725338 | https://github.com/HugoZHL/PQCache | llm-inference | Product-quantization-based KV cache management for long-context inference; directly on-topic, single GPU |
| 69 | Privacy and Accuracy-Aware AI/ML Model Deduplication | https://dl.acm.org/doi/10.1145/3725340 | https://dl.acm.org/doi/pdf/10.1145/3725340 | unknown | storage | Deduplication of model weights for serving systems; user-space, single GPU; concern - part of the contribution is privacy analysis |
| 70 | Rethinking The Compaction Policies in LSM-trees | https://dl.acm.org/doi/10.1145/3725344 | https://dl.acm.org/doi/pdf/10.1145/3725344 | unknown | storage | Compaction policy design in LSM-trees treating compaction as a resource investment; classic single-machine storage work |
| 71 | RWalks: Random Walks as Attribute Diffusers for Filtered Vector Search | https://dl.acm.org/doi/10.1145/3725349 | https://dl.acm.org/doi/pdf/10.1145/3725349 | https://github.com/AnasAito/rwalks-reproduce-v2 | other-userspace | Index-agnostic filtered vector search; single machine, CPU |
| 72 | Self-Enhancing Video Data Management System for Compositional Events with Large Language Models | https://dl.acm.org/doi/10.1145/3725352 | https://dl.acm.org/doi/pdf/10.1145/3725352 | https://github.com/uwdb/VOCAL-UDF | ml-systems | Video data management system that generates and distills UDF models; single-GPU vision models plus LLM API |
| 73 | Serf : Streaming Error-Bounded Floating-Point Compression | https://dl.acm.org/doi/10.1145/3725353 | https://dl.acm.org/doi/pdf/10.1145/3725353 | https://github.com/Spatio-Temporal-Lab/Serf | storage | Streaming error-bounded floating-point compression; user-space library |
| 74 | SHIELD: Encrypting Persistent Data of LSM-KVS from Monolithic to Disaggregated Storage | https://dl.acm.org/doi/10.1145/3725354 | https://dl.acm.org/doi/pdf/10.1145/3725354 | https://github.com/asu-idi/SHIELD | storage | Encryption design for LSM key-value store persistent data; monolithic deployment runs on one machine, concern - the disaggregated setup needs two nodes |
| 75 | SPACE: Cardinality Estimation for Path Queries Using Cardinality-Aware Sequence-based Learning | https://dl.acm.org/doi/10.1145/3725355 | https://dl.acm.org/doi/pdf/10.1145/3725355 | unknown | ml-for-systems | Learned sequence-based cardinality estimator for path queries |
| 76 | SpareLLM: Automatically Selecting Task-Specific Minimum-Cost Large Language Models under Equivalence Constraint | https://dl.acm.org/doi/10.1145/3725356 | https://dl.acm.org/doi/pdf/10.1145/3725356 | https://github.com/saehanjo/spare-llm | llm-inference | Cost-aware selection/routing among LLMs under an equivalence constraint; concern - mainly uses hosted model APIs |
| 77 | Styx: Transactional Stateful Functions on Streaming Dataflows | https://dl.acm.org/doi/10.1145/3725363 | https://dl.acm.org/doi/pdf/10.1145/3725363 | https://github.com/delftdata/styx | other-userspace | Deterministic transactional runtime for stateful functions on a dataflow engine; concern - normally deployed as a multi-worker cluster, would run as processes on one host |
| 78 | T3: Accurate and Fast Performance Prediction for Relational Database Systems With Compiled Decision Trees | https://dl.acm.org/doi/10.1145/3725364 | https://dl.acm.org/doi/pdf/10.1145/3725364 | https://github.com/MaxRieger96/T3 | ml-for-systems | Compiled decision-tree model for query performance prediction; low-latency learned component in the DB |
| 79 | Apt-Serve: Adaptive Request Scheduling on Hybrid Cache for Scalable LLM Inference Serving | https://dl.acm.org/doi/10.1145/3725394 | https://dl.acm.org/doi/pdf/10.1145/3725394 | https://github.com/eddiegaoo/apt-serve | llm-inference | Request scheduling plus hybrid KV/hidden cache for LLM serving; directly on-topic and single-GPU friendly |
| 80 | Athena: An Effective Learning-based Framework for Query Optimizer Performance Improvement | https://dl.acm.org/doi/10.1145/3725395 | https://dl.acm.org/doi/pdf/10.1145/3725395 | unknown | ml-for-systems | Learned plan explorer and comparator on top of PostgreSQL |
| 81 | cuMatch: A GPU-based Memory-Efficient Worst-case Optimal Join Processing Method for Subgraph Queries with Complex Patterns | https://dl.acm.org/doi/10.1145/3725398 | https://dl.acm.org/doi/pdf/10.1145/3725398 | unknown | other-userspace | GPU worst-case-optimal join with explicit GPU memory efficiency goals; single GPU |
| 82 | DIGRA: A Dynamic Graph Indexing for Approximate Nearest Neighbor Search with Range Filter | https://dl.acm.org/doi/10.1145/3725399 | https://dl.acm.org/doi/pdf/10.1145/3725399 | unknown | other-userspace | Dynamic graph index for range-filtered ANN; single machine |
| 83 | Efficient Dynamic Indexing for Range Filtered Approximate Nearest Neighbor Search | https://dl.acm.org/doi/10.1145/3725401 | https://dl.acm.org/doi/pdf/10.1145/3725401 | unknown | other-userspace | Dynamic range-filtered ANN index with linear space; single machine |
| 84 | Fast Approximate Similarity Join in Vector Databases | https://dl.acm.org/doi/10.1145/3725403 | https://dl.acm.org/doi/pdf/10.1145/3725403 | unknown | other-userspace | Similarity join operator for vector databases; CPU, single machine |
| 85 | GPH: An Efficient and Effective Perfect Hashing Scheme for GPU Architectures | https://dl.acm.org/doi/10.1145/3725406 | https://dl.acm.org/doi/pdf/10.1145/3725406 | unknown | other-userspace | GPU hash table design with a micro-benchmark and performance model; single GPU |
| 86 | High-Throughput Ingestion for Video Warehouse: Comprehensive Configuration and Effective Exploration | https://dl.acm.org/doi/10.1145/3725407 | https://dl.acm.org/doi/pdf/10.1145/3725407 | unknown | ml-systems | Configuration search for video ingestion pipelines with model selection; single-GPU video analytics |
| 87 | Aero: Adaptive Query Processing of ML Queries | https://dl.acm.org/doi/10.1145/3725408 | https://dl.acm.org/doi/pdf/10.1145/3725408 | https://github.com/georgia-tech-db/aero | ml-systems | Adaptive query processing for ML/UDF queries in an ML-centric DBMS; single GPU |
| 88 | Logical and Physical Optimizations for SQL Query Execution over Large Language Models | https://dl.acm.org/doi/10.1145/3725411 | https://dl.acm.org/doi/pdf/10.1145/3725411 | unknown | llm-inference | Logical and physical operators and optimizations for executing queries over LLMs; concern - relies on LLM API calls |
| 89 | Low Rank Learning for Offline Query Optimization | https://dl.acm.org/doi/10.1145/3725412 | https://dl.acm.org/doi/pdf/10.1145/3725412 | https://github.com/zixy17/LimeQO | ml-for-systems | Low-rank learning for offline query plan selection; cheap to reproduce on one node |
| 90 | Practical and Asymptotically Optimal Quantization of High-Dimensional Vectors in Euclidean Space for Approximate Nearest Neighbor Search | https://dl.acm.org/doi/10.1145/3725413 | https://dl.acm.org/doi/pdf/10.1145/3725413 | https://github.com/VectorDB-NTU/Extended-RaBitQ | other-userspace | Extended RaBitQ quantization for ANN; CPU SIMD, single machine |
| 91 | Scalable Complex Event Processing on Video Streams | https://dl.acm.org/doi/10.1145/3725419 | https://dl.acm.org/doi/pdf/10.1145/3725419 | unknown | ml-systems | Complex event processing over video streams with model invocation scheduling; single GPU |
| 92 | Wait and See: A Delayed Transactions Partitioning Approach in Deterministic Database Systems for Better Performance | https://dl.acm.org/doi/10.1145/3725422 | https://dl.acm.org/doi/pdf/10.1145/3725422 | unknown | scheduling | Batch transaction partitioning/scheduling in a deterministic database; concern - shared-nothing design, evaluated with partitions that can be colocated |
| 93 | Zombie Hashing: Reanimating Tombstones in Graveyard | https://dl.acm.org/doi/10.1145/3725424 | https://dl.acm.org/doi/pdf/10.1145/3725424 | unknown | other-userspace | Linear-probing hash table redesign to avoid rebuild stalls; user-space data structure |

## All papers
| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | A Lovász-Simonovits Theorem for Hypergraphs with Application to Local Clustering | out-topic | graph/hypergraph clustering theory, no systems artifact |
| 2 | A Profit-Maximizing Data Marketplace with Differentially Private Federated Learning under Price Competition | out-topic | data marketplace pricing and federated learning economics |
| 3 | Adaptive Quotient Filters | included | topic storage - Filter/auxiliary-structure design for KV stores; pure user-space C/C++ data structure, trivially fits one machine |
| 4 | Atom: An Efficient Query Serving System for Embedding-based Knowledge Graph Reasoning with Operator-level Batching | included | topic ml-systems - Operator-level batching and scheduling for an embedding-model query serving system; single-GPU serving workload - official repo not confirmed, listed as unknown |
| 5 | BT-Tree: A Reinforcement Learning Based Index for Big Trajectory Data | included | topic ml-for-systems - Learned/RL-built index structure; CPU-only, user space - official repo not confirmed, listed as unknown |
| 6 | Discovering Top-k Relevant and Diversified Rules | out-topic | rule discovery / data mining algorithm |
| 7 | Efficient and Accurate PageRank Approximation on Large Graphs | out-topic | PageRank approximation algorithm |
| 8 | Efficient Approximation Algorithms for Minimum Cost Seed Selection with Probabilistic Coverage Guarantee | out-topic | seed selection approximation algorithms |
| 9 | Enabling Adaptive Sampling for Intra-Window Join: Simultaneously Optimizing Quantity and Quality | out-topic | stream join sampling algorithm, statistical contribution |
| 10 | GABoost: Graph Alignment Boosting via Local Optimum Escape | out-topic | graph alignment algorithm |
| 11 | Near-Duplicate Text Alignment with One Permutation Hashing | out-topic | sequence alignment / hashing algorithm |
| 12 | On the Feasibility and Benefits of Extensive Evaluation | out-topic | evaluation-methodology study, no reusable system artifact |
| 13 | CAMAL: Optimizing LSM-trees via Active Learning | included | topic ml-for-systems - Active-learning tuner for LSM-tree knobs integrated into RocksDB; single-node, user space - official repo not confirmed, listed as unknown |
| 14 | Pluto: Sample Selection for Robust Anomaly Detection on Polluted Log Data | out-topic | log anomaly detection ML method |
| 15 | SketchQL: Video Moment Querying with a Visual Query Interface | out-topic | video query interface / UX contribution |
| 16 | Tao: Improving Resource Utilization while Guaranteeing SLO in Multi-tenant Relational Database-as-a-Service | included | topic scheduling - Coroutine-based tasklet scheduler with SLO guarantees on top of the open-source Hyrise DBMS; pure user-space CPU scheduling - official repo not confirmed, listed as unknown |
| 17 | Theoretically and Practically Efficient Maximum Defective Clique Search | out-topic | defective clique enumeration algorithm |
| 18 | A Universal Sketch for Estimating Heavy Hitters and Per-Element Frequency Moments in Data Streams with Bounded Deletions | out-topic | streaming sketch algorithm |
| 19 | An Efficient and Exact Algorithm for Locally h -Clique Densest Subgraph Discovery | out-topic | densest subgraph algorithm |
| 20 | Buffered Persistence in B+ Trees | out-machine | core design targets non-volatile memory (NVM/PMEM) with cache-flush/fence semantics - no PMEM on this machine |
| 21 | Camel: Efficient Compression of Floating-Point Time Series | included | topic storage - Floating-point compression codec plus index; user-space library - official repo not confirmed, listed as unknown |
| 22 | Common Neighborhood Estimation over Bipartite Graphs under Local Differential Privacy | out-topic | local differential privacy estimation |
| 23 | Connectivity-Oriented Property Graph Partitioning for Distributed Graph Pattern Query Processing | out-topic | distributed graph partitioning for a cluster |
| 24 | Constant-time Connectivity Querying in Dynamic Graphs | out-topic | dynamic graph connectivity algorithm |
| 25 | Directional Queries: Making Top-k Queries More Effective in Discovering Relevant Results | out-topic | top-k query semantics |
| 26 | Disclosure-Compliant Query Answering | out-topic | query answering under disclosure policies |
| 27 | DPconv: Super-Polynomially Faster Join Ordering | out-topic | join-ordering complexity/algorithm result |
| 28 | Finding Logic Bugs in Spatial Database Engines via Affine Equivalent Inputs | out-topic | database testing / logic-bug finding |
| 29 | GIDCL: A Graph-Enhanced Interpretable Data Cleaning Framework with Large Language Models | out-topic | LLM-based data cleaning |
| 30 | GOLAP: A GPU-in-Data-Path Architecture for High-Speed OLAP | out-machine | needs direct SSD-to-GPU streaming (GPUDirect-style) over a multi-SSD array to reach ~100 GiB/s; requires root-level storage stack setup |
| 31 | High-Performance Query Processing with NVMe Arrays: Spilling without Killing Performance | included | topic storage - Out-of-memory hash operators and spilling compression on NVMe; machine has 2 NVMe devices so a scaled-down study is possible - concern: paper uses a larger NVMe array - official repo not confirmed, listed as unknown |
| 32 | iRangeGraph: Improvising Range-dedicated Graphs for Range-filtering Nearest Neighbor Search | included | topic other-userspace - In-memory graph index for range-filtered ANN; single-machine C++ |
| 33 | Live Patching for Distributed In-Memory Key-Value Stores | included | topic other-userspace - User-space live patching of Redis processes; concern - built for a Redis Cluster, would need multiple processes on one host - official repo not confirmed, listed as unknown |
| 34 | Transforming RDF Graphs to Property Graphs using Standardized Schemas | out-topic | RDF-to-property-graph schema transformation |
| 35 | LSMGraph: A High-Performance Dynamic Graph Storage System with Multi-Level CSR | included | topic storage - LSM-tree + CSR hybrid disk-based graph storage engine; single machine |
| 36 | Memento Filter: A Fast, Dynamic, and Robust Range Filter | included | topic storage - Range filter data structure for LSM key-value stores; user-space C++ |
| 37 | Multivariate Time Series Cleaning under Speed Constraints | out-topic | time series cleaning algorithm |
| 38 | Navigating Labels and Vectors: A Unified Approach to Filtered Approximate Nearest Neighbor Search | included | topic other-userspace - Graph index for filtered ANN search; single-machine in-memory |
| 39 | Online Detection of Anomalies in Temporal Knowledge Graphs with Interpretability | out-topic | temporal knowledge graph anomaly detection ML |
| 40 | Personalized Truncation for Personalized Privacy | out-topic | differential privacy mechanism |
| 41 | Provenance-Enabled Explainable AI | out-topic | explainable AI provenance semantics |
| 42 | SPID-Join: A Skew-resistant Processing-in-DIMM Join Algorithm Exploiting the Bank- and Rank-level Parallelisms of DIMMs | out-machine | requires Processing-in-DIMM hardware (UPMEM-style In-DIMM Processors) |
| 43 | Towards a Converged Relational-Graph Optimization Framework | out-topic | relational-graph query optimizer semantics |
| 44 | Understanding and Reusing Test Suites Across Database Systems | out-topic | database test-suite reuse study |
| 45 | CtxPipe: Context-aware Data Preparation Pipeline Construction for Machine Learning | included | topic ml-systems - Automatic construction of ML data-preparation pipelines; CPU-bound, user space |
| 46 | Pasta: A Cost-Based Optimizer for Generating Pipelining Schedules for Dataflow DAGs | included | topic scheduling - Cost-based scheduler for pipelined execution of dataflow DAGs; user-space scheduling problem - official repo not confirmed, listed as unknown |
| 47 | Automating Vectorized Distributed Graph Computation | out-topic | distributed graph computation vectorization compiler for clusters |
| 48 | λ-Tune: Harnessing Large Language Models for Automated Database System Tuning | included | topic ml-for-systems - LLM-driven DBMS knob tuning on PostgreSQL/MySQL; concern - needs external LLM API access |
| 49 | Online Marketplace: A Benchmark for Data Management in Microservices | out-topic | microservices data management benchmark |
| 50 | A Local Search Approach to Efficient ( k,p )-Core Maintenance | out-topic | (k,p)-core maintenance algorithm |
| 51 | A Rank-Based Approach to Recommender System's Top-K Queries with Uncertain Scores | out-topic | recommender top-k query semantics |
| 52 | Accelerating Core Decomposition in Billion-Scale Hypergraphs | out-topic | hypergraph core decomposition algorithm |
| 53 | Agree to Disagree: Robust Anomaly Detection with Noisy Labels | out-topic | anomaly detection ML method |
| 54 | An Adaptive Benchmark for Modeling User Exploration of Large Datasets | out-topic | user-exploration benchmark |
| 55 | An Elephant Under the Microscope: Analyzing the Interaction of Optimizer Components in PostgreSQL | out-topic | measurement study of PostgreSQL optimizer components, query-optimizer topic |
| 56 | An Experimental Comparison of Tree-data Structures for Connectivity Queries on Fully-dynamic Undirected Graphs | out-topic | experimental comparison of graph connectivity data structures |
| 57 | AquaPipe: A Quality-Aware Pipeline for Knowledge Retrieval and Large Language Models | included | topic llm-inference - Pipelines disk-based ANNS retrieval with LLM prefill in a RAG serving system; 7B-class models fit 24 GB - official repo not confirmed, listed as unknown |
| 58 | Aster: Enhancing LSM-structures for Scalable Graph Database | included | topic storage - Graph-oriented LSM key-value storage engine; single machine |
| 59 | Automatic Database Configuration Debugging using Retrieval-Augmented Language Models | included | topic ml-for-systems - RAG/LLM-based DBMS configuration diagnosis; concern - needs LLM API access - official repo not confirmed, listed as unknown |
| 60 | B-Trees Are Back: Engineering Fast and Pageable Node Layouts | included | topic storage - Engineering study of pageable B-Tree node layouts with variable-size records; user-space storage engine - official repo not confirmed, listed as unknown |
| 61 | BⓈ X : Subgraph Matching with Batch Backtracking Search | out-topic | subgraph matching algorithm |
| 62 | BCviz: A Linear-Space Index for Mining and Visualizing Cohesive Bipartite Subgraphs | out-topic | bipartite subgraph mining index |
| 63 | Boosting OLTP Performance with Per-Page Logging on NVDIMM | out-machine | requires a real NVDIMM device as durable log cache |
| 64 | Capsule: An Out-of-Core Training Mechanism for Colossal GNNs | included | topic ml-systems - Out-of-core GNN training that keeps computation on one GPU; designed for limited GPU memory |
| 65 | Cardinality Estimation of LIKE Predicate Queries using Deep Learning | included | topic ml-for-systems - Learned cardinality estimator inside the query optimizer; CPU/GPU training fits one node |
| 66 | Centrum: Model-based Database Auto-tuning with Minimal Distributional Assumptions | included | topic ml-for-systems - Model-based DBMS auto-tuning; single-node tuning loop - official repo not confirmed, listed as unknown |
| 67 | Cohesiveness-aware Hierarchical Compressed Index for Community Search on Attributed Graphs | out-topic | community search index |
| 68 | Computing Approximate Graph Edit Distance via Optimal Transport | out-topic | graph edit distance algorithm |
| 69 | Constant Optimization Driven Database System Testing | out-topic | database system testing |
| 70 | CRDV: Conflict-free Replicated Data Views | out-topic | CRDT replication semantics |
| 71 | Data Chunk Compaction in Vectorized Execution | included | topic ml-for-systems - Learning-based runtime decision inside a vectorized engine (DuckDB); user space |
| 72 | DataVinci: Learning Syntactic and Semantic String Repairs | out-topic | string repair learning |
| 73 | Deep Overlapping Community Search via Subspace Embedding | out-topic | community search embedding |
| 74 | DEG: Efficient Hybrid Vector Search Using the Dynamic Edge Navigation Graph | included | topic other-userspace - Graph-based ANN index for hybrid vector queries; single machine |
| 75 | Density Decomposition of Bipartite Graphs | out-topic | bipartite graph density decomposition theory |
| 76 | Dialogue Benchmark Generation from Knowledge Graphs with Cost-Effective Retrieval-Augmented LLMs | out-topic | dialogue benchmark generation with LLMs |
| 77 | DISCES: Systematic Discovery of Event Stream Queries | out-topic | event stream query discovery |
| 78 | Disco: A Compact Index for LSM-trees | included | topic storage - Compact index for LSM-trees, integrated in a key-value store; user space |
| 79 | Dual-Hierarchy Labelling: Scaling Up Distance Queries on Dynamic Road Networks | out-topic | road-network distance labelling |
| 80 | Efficient Index Maintenance for Effective Resistance Computation on Evolving Graphs | out-topic | effective-resistance index maintenance |
| 81 | Efficient Maximum s -Bundle Search via Local Vertex Connectivity | out-topic | s-bundle search algorithm |
| 82 | Efficiently Counting Triangles in Large Temporal Graphs | out-topic | temporal triangle counting algorithm |
| 83 | Efficiently Processing Joins and Grouped Aggregations on GPUs | included | topic other-userspace - GPU join and group-by operator optimizations; single GPU, fits a 24 GB A5000 |
| 84 | Entity/Relationship Graphs: Principled Design, Modeling, and Data Integrity Management of Graph Databases | out-topic | graph data modeling / integrity theory |
| 85 | FastPDB: Towards Bag-Probabilistic Queries at Interactive Speeds | out-topic | probabilistic database query evaluation |
| 86 | Graph-Based Vector Search: An Experimental Evaluation of the State-of-the-Art | included | topic other-userspace - Experimental evaluation and unified framework for graph-based vector search; concern - largest datasets are 1B vectors, would need scale-down |
| 87 | H-Rocks: CPU-GPU accelerated Heterogeneous RocksDB on Persistent Memory | out-machine | requires persistent memory (Optane-class) hardware for the RocksDB backend |
| 88 | HyperMR: Efficient Hypergraph-enhanced Matrix Storage on Compute-in-Memory Architecture | out-machine | requires Compute-in-Memory hardware architecture |
| 89 | In-Database Time Series Clustering | out-topic | in-database time series clustering algorithm |
| 90 | ISSD: Indicator Selection for Time Series State Detection | out-topic | time series state detection indicators |
| 91 | Largest Triangle Sampling for Visualizing Time Series in Database | out-topic | time series visualization sampling |
| 92 | LCP: Enhancing Scientific Data Management with L ossy C ompression for P articles | included | topic storage - Lossy compressor for particle data; user-space library, CPU - official repo not confirmed, listed as unknown |
| 93 | LeaFi: Data Series Indexes on Steroids with Learned Filters | included | topic ml-for-systems - Learned filters that improve pruning inside tree-based data series indexes |
| 94 | MAST: Towards Efficient Analytical Query Processing on Point Cloud Data | included | topic ml-systems - Approximate invocation of deep models for point-cloud analytical queries; single-GPU inference |
| 95 | MEMO: Fine-grained Tensor Management For Ultra-long Context LLM Training | included | topic ml-systems - Activation offloading and fine-grained tensor/memory management for long-context LLM training; concern - evaluated on a multi-GPU node, needs scale-down to one A5000 |
| 96 | Minimum Spanning Tree Maintenance in Dynamic Graphs | out-topic | minimum spanning tree maintenance algorithm |
| 97 | Modyn: Data-Centric Machine Learning Pipeline Orchestration | included | topic ml-systems - Open-source orchestration platform for continuous ML training pipelines; runs on one node |
| 98 | Nezha: An Efficient Distributed Graph Processing System on Heterogeneous Hardware | out-machine | distributed cluster with RDMA interconnect and multiple GPU machines |
| 99 | OBIR-tree: An Efficient Oblivious Index for Spatial Keyword Queries on Secure Enclaves | out-topic | oblivious index needs SGX secure enclaves |
| 100 | Optimizing Block Skipping for High-Dimensional Data with Learned Adaptive Curve | included | topic ml-for-systems - Learned space-filling curve for data layout and block skipping; user space - official repo not confirmed, listed as unknown |
| 101 | Pandora: An Efficient and Rapid Solution for Persistence-Based Tasks in High-Speed Data Streams | out-topic | persistence-based stream sketching |
| 102 | Parallel kd-tree with Batch Updates | included | topic other-userspace - Parallel cache-efficient in-memory kd-tree for a 16-core machine |
| 103 | PoneglyphDB: Efficient Non-interactive Zero-Knowledge Proofs for Arbitrary SQL-Query Verification | out-topic | zero-knowledge proofs for SQL verification |
| 104 | Practical DB-OS Co-Design with Privileged Kernel Bypass | out-machine | DB-OS co-design via virtualization; needs KVM and elevated privilege for the DB process |
| 105 | Progressive Entity Matching: A Design Space Exploration | out-topic | entity matching design space |
| 106 | QURE: AI-Assisted and Automatically Verified UDF Inlining | out-topic | UDF inlining verification / program analysis |
| 107 | Randomized Sketches for Quantile in LSM-tree based Store | included | topic storage - Pre-computed randomized sketches stored in LSM components; user-space KV store change - official repo not confirmed, listed as unknown |
| 108 | Rapid Data Ingestion through DB-OS Co-design | out-machine | zicIO is a kernel-level DB-OS co-design requiring custom kernel support |
| 109 | Reliable Text-to-SQL with Adaptive Abstention | out-topic | text-to-SQL abstention |
| 110 | Revisiting the Design of In-Memory Dynamic Graph Storage | included | topic storage - Common abstraction plus generic test framework for in-memory dynamic graph storage; strong reproduction/improvement target on one machine |
| 111 | RLER-TTE: An Efficient and Effective Framework for En Route Travel Time Estimation with Reinforcement Learning | out-topic | travel-time estimation with RL |
| 112 | Schema-Based Query Optimisation for Graph Databases | out-topic | graph query optimization semantics |
| 113 | SecureXGB: A Secure and Efficient Multi-party Protocol for Vertical Federated XGBoost | out-topic | secure multi-party XGBoost protocol |
| 114 | Shapley Value Estimation based on Differential Matrix | out-topic | Shapley value estimation |
| 115 | SHARQ: Explainability Framework for Association Rules on Relational Data | out-topic | association-rule explainability |
| 116 | SNAILS: Schema Naming Assessments for Improved LLM-Based SQL Inference | out-topic | schema naming for LLM SQL generation |
| 117 | Subspace Collision: An Efficient and Accurate Framework for High-dimensional Approximate Nearest Neighbor Search | included | topic other-userspace - Clustering-based ANN index framework; single machine |
| 118 | SymphonyQG: Towards Symphonious Integration of Quantization and Graph for Approximate Nearest Neighbor Search | included | topic other-userspace - SIMD-friendly integration of quantization and graph ANN index; CPU-only, cache/memory-access focused - official repo not confirmed, listed as unknown |
| 119 | TGraph: A Tensor-centric Graph Processing Framework | included | topic ml-systems - Graph processing expressed on tensor runtimes (PyTorch-style backends); runs on a single GPU - official repo not confirmed, listed as unknown |
| 120 | Ultraverse: An Efficient What-if Analysis Framework for Software Applications Interacting with Database Systems | out-topic | what-if analysis for application/DB workloads |
| 121 | User-Centric Property Graph Repairs | out-topic | property graph repair semantics |
| 122 | VEGA: An Active-tuning Learned Index with Group-Wise Learning Granularity | included | topic ml-for-systems - Learned index with online model building under a memory budget; user space - official repo not confirmed, listed as unknown |
| 123 | Bursting Flow Query on Large Temporal Flow Networks | out-topic | temporal flow network query algorithm |
| 124 | DiskGNN: Bridging I/O Efficiency and Model Accuracy for Out-of-Core GNN Training | included | topic ml-systems - Disk-based out-of-core GNN training with I/O-efficient feature packing; single GPU plus NVMe |
| 125 | Federated Heavy Hitter Analytics with Local Differential Privacy | out-topic | federated heavy hitter LDP protocol |
| 126 | InTime: Towards Performance Predictability In Byzantine Fault Tolerant Proof-of-Stake Consensus | out-topic | blockchain BFT-PoS incentive design |
| 127 | On Graph Representation for Attributed Hypergraph Clustering | out-topic | attributed hypergraph clustering |
| 128 | Sequoia: An Accessible and Extensible Framework for Privacy-Preserving Machine Learning over Distributed Data | out-topic | privacy-preserving ML over distributed data |
| 129 | Tribase: A Vector Data Query Engine for Reliable and Lossless Pruning Compression using Triangle Inequalities | included | topic other-userspace - Cluster-based vector query engine with pruning; CPU, single machine |
| 130 | Multi-Level Graph Representation Learning Through Predictive Community-based Partitioning | out-topic | graph representation learning method |
| 131 | U-DPAP: Utility-aware Efficient Range Counting on Privacy-preserving Spatial Data Federation | out-topic | privacy-preserving spatial federation |
| 132 | SPAS: Continuous Release of Data Streams under w-Event Differential Privacy | out-topic | differential privacy stream release |
| 133 | A Cost-Effective LLM-based Approach to Identify Wildlife Trafficking in Online Marketplaces | out-topic | LLM application for wildlife trafficking detection |
| 134 | A New Paradigm in Tuning Learned Indexes: A Reinforcement Learning Enhanced Approach | included | topic ml-for-systems - RL-based end-to-end tuner for learned index structures; user space - official repo not confirmed, listed as unknown |
| 135 | A Structured Study of Multivariate Time-Series Distance Measures | out-topic | time-series distance measure study |
| 136 | Accelerate Distributed Joins with Predicate Transfer | out-machine | core claim is about distributed joins across a cluster; single-node scale-down loses the contribution |
| 137 | Accelerating Graph Indexing for ANNS on Modern CPUs | included | topic other-userspace - SIMD and memory-access optimizations for HNSW-style graph index construction on modern CPUs |
| 138 | Accelerating Skyline Path Enumeration with a Core Attribute Index on Multi-attribute Graphs | out-topic | skyline path enumeration algorithm |
| 139 | Adda: Towards Efficient in-Database Feature Generation via LLM-based Agents | out-topic | LLM agents for automatic feature engineering |
| 140 | AJOSC: Adaptive Join Order Selection for Continuous Queries | out-topic | stream join order selection algorithm |
| 141 | Alsatian: Optimizing Model Search for Deep Transfer Learning | included | topic ml-systems - Model search system that shares inference work across candidate models; single GPU |
| 142 | Approximate DBSCAN under Differential Privacy | out-topic | DBSCAN under differential privacy |
| 143 | Approximating Opaque Top-k Queries | out-topic | opaque top-k approximation algorithm |
| 144 | Are Database System Researchers Making Correct Assumptions about Transaction Workloads? | out-topic | transaction workload assumption study |
| 145 | Automated Validating and Fixing of Text-to-SQL Translation with Execution Consistency | out-topic | text-to-SQL validation |
| 146 | BPF-DB: A Kernel-Embedded Transactional Database Management System For eBPF Applications | out-machine | BPF-DB is embedded in the Linux kernel as eBPF programs; unprivileged eBPF is disabled on this machine |
| 147 | Cache-Craft: Managing Chunk-Caches for Efficient Retrieval-Augmented Generation | included | topic llm-inference - KV-cache reuse for RAG chunks; core KV-cache management topic, single-GPU 7B-class models feasible - official repo not confirmed, listed as unknown |
| 148 | CARINA: An Efficient CXL-Oriented Embedding Serving System for Recommendation Models | out-machine | requires CXL-attached memory hardware |
| 149 | Clementi: Efficient Load Balancing and Communication Overlap for Multi-FPGA Graph Processing | out-machine | requires a multi-FPGA platform |
| 150 | Community Detection in Heterogeneous Information Networks Without Materialization | out-topic | community detection algorithm |
| 151 | Cracking SQL Barriers: An LLM-based Dialect Translation System | out-topic | LLM SQL dialect translation |
| 152 | Credible Intervals for Knowledge Graph Accuracy Estimation | out-topic | knowledge graph accuracy estimation statistics |
| 153 | Dangers of List Processing in Querying Property Graphs | out-topic | property graph query language semantics |
| 154 | Data Enhancement for Binary Classification of Relational Data | out-topic | relational data augmentation for classification |
| 155 | Debunking the Myth of Join Ordering: Toward Robust SQL Analytics | included | topic other-userspace - Predicate transfer integrated into DuckDB for join-order robustness; single node, user space |
| 156 | DFlush: DPU-Offloaded Flush for Disaggregated LSM-based Key-Value Stores | out-machine | requires a DPU (SmartNIC) to offload LSM flush |
| 157 | Dupin: A Parallel Framework for Densest Subgraph Discovery in Fraud Detection on Massive Graphs | out-topic | densest subgraph mining for fraud detection |
| 158 | Efficient and Accurate Differentially Private Cardinality Continual Releases | out-topic | differentially private cardinality release |
| 159 | Extending SQL to Return a Subdatabase | out-topic | SQL language extension semantics |
| 160 | FAAQP: Fast and Accurate Approximate Query Processing based on Bitmap-augmented Sum-Product Network | included | topic ml-for-systems - Learned sum-product-network model used inside the DBMS for approximate query answering - official repo not confirmed, listed as unknown |
| 161 | Fair and Actionable Causal Prescription Ruleset | out-topic | causal prescription rule mining |
| 162 | Fast and Scalable Data Transfer Across Data Systems | included | topic other-userspace - Configurable data-transfer pipeline framework between data systems; can be run as processes on one host |
| 163 | Fast Hypertree Decompositions via Linear Programming: Fractional and Generalized | out-topic | hypertree decomposition algorithm |
| 164 | Femur: A Flexible Framework for Fast and Secure Querying from Public Key-Value Store | included | topic storage - Learned-index-based key-value retrieval framework with tunable security; user-space, single machine |
| 165 | Finding Logic Bugs in Graph-processing Systems via Graph-cutting | out-topic | graph-processing system testing / bug finding |
| 166 | Galley: Modern Query Optimization for Sparse Tensor Programs | included | topic ml-systems - Cost-based optimizer/compiler for sparse tensor programs; ML-compiler topic, single node |
| 167 | Rule-Based Graph Cleaning with GPUs on a Single Machine | included | topic other-userspace - Explicitly a single-machine CPU+GPU+IO pipelined system; fits the target machine by construction - official repo not confirmed, listed as unknown |
| 168 | Graph Edit Distance Estimation: A New Heuristic and A Holistic Evaluation of Learning-based Methods | out-topic | graph edit distance heuristic and evaluation |
| 169 | GTX: A Write-Optimized Latch-free Graph Data System with Transactional Support | included | topic storage - Main-memory latch-free graph store with transactions and concurrency control; multicore user space |
| 170 | HoneyComb: A Parallel Worst-Case Optimal Join on Multicores | included | topic other-userspace - Parallel worst-case optimal join engineered for large multicore shared-memory machines - official repo not confirmed, listed as unknown |
| 171 | HotStuff-1: Linear Consensus with One-Phase Speculation | out-topic | BFT consensus protocol design |
| 172 | How Good are Learned Cost Models, Really? Insights from Query Optimization Tasks | included | topic ml-for-systems - Systematic evaluation of learned cost models in query optimization; reproduction-friendly, single node |
| 173 | How to Grow an LSM-tree? Towards Bridging the Gap Between Theory and Practice | included | topic storage - LSM-tree growth scheme design and analysis with a prototype key-value store - official repo not confirmed, listed as unknown |
| 174 | Incremental Rule Discovery in Response to Parameter Updates | out-topic | incremental rule discovery algorithm |
| 175 | Integral Densest Subgraph Search on Directed Graphs | out-topic | directed densest subgraph algorithm |
| 176 | Intra-Query Runtime Elasticity for Cloud-Native Data Analysis | included | topic scheduling - Runtime elasticity - changing degree of parallelism mid-query; concern - built on Presto, which is normally run distributed |
| 177 | Learned Offline Query Planning via Bayesian Optimization | included | topic ml-for-systems - Offline learned query planner using Bayesian optimization on PostgreSQL - official repo not confirmed, listed as unknown |
| 178 | Low-Latency Transaction Scheduling via Userspace Interrupts: Why Wait or Yield When You Can Preempt? | out-machine | relies on x86 userspace interrupts (Intel UINTR) plus kernel support; machine is AMD with no root |
| 179 | LpBound : Pessimistic Cardinality Estimation Using ℓ p -Norms of Degree Sequences | out-topic | analytical cardinality bound, not a learned or systems component |
| 180 | Malleus: Straggler-Resilient Hybrid Parallel Training of Large-scale Models via Malleable Data and Model Parallelization | out-machine | straggler-resilient hybrid parallelism needs a multi-GPU cluster; no meaningful single-GPU version |
| 181 | MatCo: Computing Match Cover of Subgraph Query over Graph Data | out-topic | subgraph match cover algorithm |
| 182 | Maximus: A Modular Accelerated Query Engine for Data Analytics on Heterogeneous Systems | included | topic other-userspace - Modular CPU+GPU query engine; concern - the paper also targets DPUs/SmartNICs and disaggregated memory, only the CPU/GPU part is reproducible here - official repo not confirmed, listed as unknown |
| 183 | MIRAGE-ANNS: Mixed Approach Graph-based Indexing for Approximate Nearest Neighbor Search | included | topic other-userspace - Graph-based ANN index combining clustering and graph traversal; single machine |
| 184 | Mitigating the Impedance Mismatch between Prediction Query Execution and Database Engine | included | topic ml-systems - Prediction-aware operator with inference context reuse and batching inside a DB engine; single GPU - official repo not confirmed, listed as unknown |
| 185 | Mnemosyne: Dynamic Workload-Aware BF Tuning via Accurate Statistics in LSM trees | included | topic storage - Workload-aware Bloom filter memory allocation in LSM-trees; user-space KV store |
| 186 | Moving on From Group Commit: Autonomous Commit Enables High Throughput and Low Latency on NVMe SSDs | included | topic storage - Commit/logging protocol tuned for NVMe SSD parallelism; user-space DBMS change, machine has NVMe |
| 187 | Nested Parquet Is Flat, Why Not Use It? How To Scan Nested Data With On-the-Fly Key Generation and Joins | included | topic storage - Scanning nested Parquet efficiently in a relational engine; pure user-space file-format work - official repo not confirmed, listed as unknown |
| 188 | NEXT: A New Secondary Index Framework for LSM-based Data Storage | included | topic storage - Secondary index framework for LSM-based key-value stores - official repo not confirmed, listed as unknown |
| 189 | OpenSearch-SQL: Enhancing Text-to-SQL with Dynamic Few-shot and Consistency Alignment | out-topic | text-to-SQL prompting method |
| 190 | Parallel k -Core Decomposition: Theory and Practice | out-topic | parallel k-core decomposition algorithm |
| 191 | PDX: A Data Layout for Vector Similarity Search | included | topic other-userspace - Vector data layout that changes memory access patterns and auto-vectorization; CPU-only, single machine |
| 192 | Physical Visualization Design: Decoupling Interface and System Design | out-topic | visualization interface design |
| 193 | PilotDB: Database-Agnostic Online Approximate Query Processing with A Priori Error Guarantees | out-topic | approximate query processing sampling with statistical guarantees |
| 194 | PLM4NDV: Minimizing Data Access for Number of Distinct Values Estimation with Pre-trained Language Models | included | topic ml-for-systems - Pre-trained language model used as a learned estimator inside the DBMS; code released by ByteDance |
| 195 | Pneuma : Leveraging LLMs for Tabular Data Representation and Retrieval in an End-to-End System | out-topic | LLM-based table discovery/retrieval application |
| 196 | PQCache: Product Quantization-based KVCache for Long Context LLM Inference | included | topic llm-inference - Product-quantization-based KV cache management for long-context inference; directly on-topic, single GPU |
| 197 | Privacy and Accuracy-Aware AI/ML Model Deduplication | included | topic storage - Deduplication of model weights for serving systems; user-space, single GPU; concern - part of the contribution is privacy analysis - official repo not confirmed, listed as unknown |
| 198 | PrivPetal: Relational Data Synthesis via Permutation Relations | out-topic | relational data synthesis under differential privacy |
| 199 | Relevance Queries for Interval Data | out-topic | interval data query semantics |
| 200 | Rethinking The Compaction Policies in LSM-trees | included | topic storage - Compaction policy design in LSM-trees treating compaction as a resource investment; classic single-machine storage work - official repo not confirmed, listed as unknown |
| 201 | Revisiting Graph Analytics Benchmark | out-topic | graph analytics benchmark, platforms are distributed |
| 202 | RLOMM: An Efficient and Robust Online Map Matching Framework with Reinforcement Learning | out-topic | online map matching with RL |
| 203 | Robust Privacy-Preserving Triangle Counting under Edge Local Differential Privacy | out-topic | local differential privacy triangle counting |
| 204 | RWalks: Random Walks as Attribute Diffusers for Filtered Vector Search | included | topic other-userspace - Index-agnostic filtered vector search; single machine, CPU |
| 205 | Self-Enhancing Video Data Management System for Compositional Events with Large Language Models | included | topic ml-systems - Video data management system that generates and distills UDF models; single-GPU vision models plus LLM API |
| 206 | Serf : Streaming Error-Bounded Floating-Point Compression | included | topic storage - Streaming error-bounded floating-point compression; user-space library |
| 207 | SHIELD: Encrypting Persistent Data of LSM-KVS from Monolithic to Disaggregated Storage | included | topic storage - Encryption design for LSM key-value store persistent data; monolithic deployment runs on one machine, concern - the disaggregated setup needs two nodes |
| 208 | SPACE: Cardinality Estimation for Path Queries Using Cardinality-Aware Sequence-based Learning | included | topic ml-for-systems - Learned sequence-based cardinality estimator for path queries - official repo not confirmed, listed as unknown |
| 209 | SpareLLM: Automatically Selecting Task-Specific Minimum-Cost Large Language Models under Equivalence Constraint | included | topic llm-inference - Cost-aware selection/routing among LLMs under an equivalence constraint; concern - mainly uses hosted model APIs |
| 210 | SPARTAN: Data-Adaptive Symbolic Time-Series Approximation | out-topic | symbolic time series approximation |
| 211 | Subgroup Discovery with Small and Alternative Feature Sets | out-topic | subgroup discovery data mining |
| 212 | SuSe: Summary Selection for Regular Expression Subsequence Aggregation over Streams | out-topic | regex subsequence aggregation over streams |
| 213 | SWASH: A Flexible Communication Framework with Sliding Window-Based Cache Sharing for Scalable DGNN Training | out-machine | distributed multi-machine DGNN training with cross-node communication |
| 214 | SwiftSpatial: Spatial Joins on Modern Hardware | out-machine | FPGA accelerator for spatial joins |
| 215 | Synthesizing Third Normal Form Schemata that Minimize Integrity Maintenance and Update Overheads: Parameterizing 3NF by the Numbers of Minimal Keys and Functional Dependencies | out-topic | schema normalization theory |
| 216 | Styx: Transactional Stateful Functions on Streaming Dataflows | included | topic other-userspace - Deterministic transactional runtime for stateful functions on a dataflow engine; concern - normally deployed as a multi-worker cluster, would run as processes on one host |
| 217 | T3: Accurate and Fast Performance Prediction for Relational Database Systems With Compiled Decision Trees | included | topic ml-for-systems - Compiled decision-tree model for query performance prediction; low-latency learned component in the DB |
| 218 | Table Overlap Estimation through Graph Embeddings | out-topic | table overlap estimation with embeddings |
| 219 | TableDC: Deep Clustering for Tabular Data | out-topic | deep clustering for tabular data |
| 220 | The Best of Both Worlds: On Repairing Timestamps and Attribute Values for Multivariate Time Series | out-topic | time series repair algorithm |
| 221 | Apt-Serve: Adaptive Request Scheduling on Hybrid Cache for Scalable LLM Inference Serving | included | topic llm-inference - Request scheduling plus hybrid KV/hidden cache for LLM serving; directly on-topic and single-GPU friendly |
| 222 | Athena: An Effective Learning-based Framework for Query Optimizer Performance Improvement | included | topic ml-for-systems - Learned plan explorer and comparator on top of PostgreSQL - official repo not confirmed, listed as unknown |
| 223 | Auto-Test: Learning Semantic-Domain Constraints for Unsupervised Error Detection in Tables | out-topic | table error detection with learned constraints |
| 224 | Computing Inconsistency Measures Under Differential Privacy | out-topic | inconsistency measures under differential privacy |
| 225 | cuMatch: A GPU-based Memory-Efficient Worst-case Optimal Join Processing Method for Subgraph Queries with Complex Patterns | included | topic other-userspace - GPU worst-case-optimal join with explicit GPU memory efficiency goals; single GPU - official repo not confirmed, listed as unknown |
| 226 | DIGRA: A Dynamic Graph Indexing for Approximate Nearest Neighbor Search with Range Filter | included | topic other-userspace - Dynamic graph index for range-filtered ANN; single machine - official repo not confirmed, listed as unknown |
| 227 | Divide-and-Conquer: Scalable Shortest Path Counting on Large Road Networks | out-topic | shortest path counting algorithm |
| 228 | Efficient Dynamic Indexing for Range Filtered Approximate Nearest Neighbor Search | included | topic other-userspace - Dynamic range-filtered ANN index with linear space; single machine - official repo not confirmed, listed as unknown |
| 229 | Efficient Indexing for Flexible Label-Constrained Shortest Path Queries in Road Networks | out-topic | label-constrained shortest path index |
| 230 | Fast Approximate Similarity Join in Vector Databases | included | topic other-userspace - Similarity join operator for vector databases; CPU, single machine - official repo not confirmed, listed as unknown |
| 231 | Fast Maximum Common Subgraph Search: A Redundancy-Reduced Backtracking Approach | out-topic | maximum common subgraph search algorithm |
| 232 | Faster and Efficient Density Decomposition via Proportional Response with Exponential Momentum | out-topic | density decomposition optimization |
| 233 | GPH: An Efficient and Effective Perfect Hashing Scheme for GPU Architectures | included | topic other-userspace - GPU hash table design with a micro-benchmark and performance model; single GPU - official repo not confirmed, listed as unknown |
| 234 | High-Throughput Ingestion for Video Warehouse: Comprehensive Configuration and Effective Exploration | included | topic ml-systems - Configuration search for video ingestion pipelines with model selection; single-GPU video analytics - official repo not confirmed, listed as unknown |
| 235 | Aero: Adaptive Query Processing of ML Queries | included | topic ml-systems - Adaptive query processing for ML/UDF queries in an ML-centric DBMS; single GPU |
| 236 | Interactive Graph Search Made Simple | out-topic | interactive graph search algorithm |
| 237 | LICS: Towards Theory-Informed Effective Visual Abstraction of Property Graph Schemas | out-topic | property graph schema visual abstraction |
| 238 | Logical and Physical Optimizations for SQL Query Execution over Large Language Models | included | topic llm-inference - Logical and physical operators and optimizations for executing queries over LLMs; concern - relies on LLM API calls - official repo not confirmed, listed as unknown |
| 239 | Low Rank Learning for Offline Query Optimization | included | topic ml-for-systems - Low-rank learning for offline query plan selection; cheap to reproduce on one node |
| 240 | Practical and Asymptotically Optimal Quantization of High-Dimensional Vectors in Euclidean Space for Approximate Nearest Neighbor Search | included | topic other-userspace - Extended RaBitQ quantization for ANN; CPU SIMD, single machine |
| 241 | PrivRM : A Framework for Range Mean Estimation under Local Differential Privacy | out-topic | local differential privacy range mean estimation |
| 242 | RM 2 : Answer Counting Queries Efficiently under Shuffle Differential Privacy | out-topic | shuffle differential privacy counting |
| 243 | SBSC: A fast Self-tuned Bipartite proximity graph-based Spectral Clustering | out-topic | spectral clustering algorithm |
| 244 | Scalable Complex Event Processing on Video Streams | included | topic ml-systems - Complex event processing over video streams with model invocation scheduling; single GPU - official repo not confirmed, listed as unknown |
| 245 | Understanding the Black Box: A Deep Empirical Dive into Shapley Value Approximations for Tabular Data | out-topic | Shapley approximation empirical study |
| 246 | Using Process Calculus for Optimizing Data and Computation Sharing in Complex Stateful Parallel Computations | out-topic | process calculus / program transformation for parallel simulations |
| 247 | Wait and See: A Delayed Transactions Partitioning Approach in Deterministic Database Systems for Better Performance | included | topic scheduling - Batch transaction partitioning/scheduling in a deterministic database; concern - shared-nothing design, evaluated with partitions that can be colocated - official repo not confirmed, listed as unknown |
| 248 | Yannakakis+: Practical Acyclic Query Evaluation with Theoretical Guarantees | out-topic | acyclic query evaluation algorithm |
| 249 | Zombie Hashing: Reanimating Tombstones in Graveyard | included | topic other-userspace - Linear-probing hash table redesign to avoid rebuild stalls; user-space data structure - official repo not confirmed, listed as unknown |
| 250 | Two Birds with One Stone: Efficient Deep Learning over Mislabeled Data through Subset Selection | out-topic | subset selection / mislabel detection ML method |
