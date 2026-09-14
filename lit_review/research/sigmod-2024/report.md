STATUS: complete
TOTAL_PAPERS: 213
INCLUDED: 61

## Sources

- Official conference program, SIGMOD research sessions: https://2024.sigmod.org/program_sigmod.shtml - fetched with curl and parsed directly from the HTML list items. It yields 212 research-track talks across 36 research sessions (sessions 1-36).
- Official SIGMOD 2024 proceedings table of contents (ACM OpenTOC snapshot hosted by the conference): https://2024.sigmod.org/toc.html - fetched with curl and parsed. It contains 217 entries, of which 4 are PACMMOD issue editorials (Vol 1 Issue 3, Vol 1 Issue 4, Vol 2 Issue 1, Vol 2 Issue 3 - the four SIGMOD 2024 review rounds), leaving 213 research papers with DOIs and abstracts.
- Cross-check: the two lists agree on 212 papers after normalising 12 title variants (working titles in the program versus final titles in the proceedings, e.g. System-X vs DoppelGanger++, LST-Meter vs LST-Bench, Range-Filtering ANN Search vs SeRF). The proceedings TOC contains exactly one paper that has no talk slot in the program, Towards Buffer Management with Tiered Main Memory. TOTAL_PAPERS is therefore 213 - the union, i.e. the proceedings list.
- DBLP (dblp.org and the Trier mirror) was attempted as a third source but is behind an anti-bot proof-of-work challenge and returned no data; dl.acm.org returns 403 to direct requests, which is why the conference-hosted OpenTOC copy was used.
- Code checks: GitHub repository search API (multiple query formulations per paper) plus targeted web searches, and HTTP checks on every repository URL listed below (all return 200).

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | OptiQL: Robust Optimistic Locking for Memory-Optimized Indexes | https://dl.acm.org/doi/10.1145/3617336 | https://dl.acm.org/doi/pdf/10.1145/3617336 | https://github.com/sfu-dis/optiql | other-userspace | Optimistic queue-based reader-writer lock for in-memory B+-tree/ART indexes - pure user-space multicore concurrency work; 16C/32T CPU is ample and no root is needed |
| 2 | ALP: Adaptive Lossless floating-Point Compression | https://dl.acm.org/doi/10.1145/3626717 | https://dl.acm.org/doi/pdf/10.1145/3626717 | https://github.com/cwida/ALP | storage | Lightweight lossless float compression scheme with a DuckDB integration; CPU/SIMD only and trivially fits the machine |
| 3 | Structural Designs Meet Optimality: Exploring Optimized LSM-tree Structures in a Colossal Configuration Space | https://dl.acm.org/doi/10.1145/3654978 | https://dl.acm.org/doi/pdf/10.1145/3654978 | https://github.com/NTU-Siqiang-Group/MooseLSM | storage | LSM-tree level-capacity and run-count design space built on RocksDB; single-node NVMe; only limit is the 257 GB free disk for very large datasets |
| 4 | GTS: GPU-based Tree Index for Fast Similarity Search | https://dl.acm.org/doi/10.1145/3654945 | https://dl.acm.org/doi/pdf/10.1145/3654945 | unknown | storage | GPU metric-space tree index for similarity search; the paper uses a single GPU so an A5000 fits. Concern: no official repo found via GitHub repo search or web search, so repo is unknown |
| 5 | CaaS-LSM: Compaction-as-a-Service for LSM-based Key-Value Stores in Storage Disaggregated Infrastructure | https://dl.acm.org/doi/10.1145/3654927 | https://dl.acm.org/doi/pdf/10.1145/3654927 | https://github.com/asu-idi/CaaS-LSM | storage | LSM compaction offloading built on RocksDB. Concern: the design targets storage-disaggregated deployments (separate compute/storage nodes, container orchestration) - on one machine it can only be emulated with multiple processes |
| 6 | AirIndex: Versatile Index Tuning Through Data and Storage | https://dl.acm.org/doi/10.1145/3617308 | https://dl.acm.org/doi/pdf/10.1145/3617308 | https://github.com/illinoisdata/airindex-public | storage | I/O-aware hierarchical index builder; single-node storage profiling on NVMe, user space only |
| 7 | Robustness of Updatable Learning-based Index Advisors against Poisoning Attack | https://dl.acm.org/doi/10.1145/3639265 | https://dl.acm.org/doi/pdf/10.1145/3639265 | https://github.com/XMUDM/PIDPA | ml-for-systems | Poisoning robustness of learning-based index advisors - a learned component inside a DBMS; PostgreSQL in user space is enough |
| 8 | PACE: Poisoning Attacks on Learned Cardinality Estimation | https://dl.acm.org/doi/10.1145/3639292 | https://dl.acm.org/doi/pdf/10.1145/3639292 | unknown | ml-for-systems | Poisoning attacks on learned cardinality estimators - learned component inside the query optimizer. Concern: no artifact found in GitHub search, repo unknown |
| 9 | Machine Unlearning in Learned Databases: An Experimental Analysis | https://dl.acm.org/doi/10.1145/3639304 | https://dl.acm.org/doi/pdf/10.1145/3639304 | unknown | ml-for-systems | Experimental analysis of unlearning/update handling in learned DB components (cardinality estimation, learned indexes); CPU+1 GPU is enough. Concern: no repo found in GitHub search |
| 10 | CAFE: Towards Compact, Adaptive, and Fast Embedding for Large-scale Recommendation Models | https://dl.acm.org/doi/10.1145/3639306 | https://dl.acm.org/doi/pdf/10.1145/3639306 | https://github.com/HugoZHL/CAFE | ml-systems | Embedding-table compression for DLRM training/inference; single-GPU DLRM runs fit in 24 GB |
| 11 | STile: Searching Hybrid Sparse Formats for Sparse Deep Learning Operators Automatically | https://dl.acm.org/doi/10.1145/3639323 | https://dl.acm.org/doi/pdf/10.1145/3639323 | https://github.com/STile-project/STile | ml-systems | Sparse-format search for sparse DL operators - an ML compiler/codegen artifact; single GPU (Ampere) is the paper's setting |
| 12 | SIMPLE: Efficient Temporal Graph Neural Network Training at Scale with Dynamic Data Placement | https://dl.acm.org/doi/10.1145/3654977 | https://dl.acm.org/doi/pdf/10.1145/3654977 | unknown | ml-systems | Temporal GNN training system with dynamic data placement between CPU and GPU; single-node. Concern: no repo found in GitHub search, repo unknown |
| 13 | Starling: An I/O-Efficient Disk-Resident Graph Index Framework for High-Dimensional Vector Similarity Search on Data Segment | https://dl.acm.org/doi/10.1145/3639269 | https://dl.acm.org/doi/pdf/10.1145/3639269 | https://github.com/zilliztech/starling | storage | I/O-efficient disk-resident graph index for vector search; explicitly designed for a small memory budget on a single node |
| 14 | Dias: Dynamic Rewriting of Pandas Code | https://dl.acm.org/doi/10.1145/3639313 | https://dl.acm.org/doi/pdf/10.1145/3639313 | https://github.com/ADAPT-uiuc/dias | other-userspace | User-space runtime that rewrites pandas code at execution time; pure Python/CPU, no root |
| 15 | Rethinking Learned Cost Models: Why Start from Scratch? | https://dl.acm.org/doi/10.1145/3626769 | https://dl.acm.org/doi/pdf/10.1145/3626769 | unknown | ml-for-systems | Learned cost models for query optimization, transferability across databases. Concern: no artifact found in GitHub search, repo unknown |
| 16 | LST-Bench: Benchmarking Log-Structured Tables in the Cloud | https://dl.acm.org/doi/10.1145/3639314 | https://dl.acm.org/doi/pdf/10.1145/3639314 | https://github.com/microsoft/lst-bench | storage | Benchmark harness for log-structured tables (Delta/Hudi/Iceberg). Concern: designed for cloud object storage and multi-node engines; a single-node Spark/Trino scale-down is possible but is not the paper's setting |
| 17 | Revisiting B-tree Compression: An Experimental Study | https://dl.acm.org/doi/10.1145/3654972 | https://dl.acm.org/doi/pdf/10.1145/3654972 | unknown | storage | Experimental study of seven B-tree compression techniques - a reusable single-node index benchmark. Concern: checked GitHub repo search and web search, no artifact link found |
| 18 | PLATON: Top-down R-tree Packing with Learned Partition Policy | https://dl.acm.org/doi/10.1145/3626742 | https://dl.acm.org/doi/pdf/10.1145/3626742 | https://github.com/Jamesyang2333/PLATON | ml-for-systems | Learned partition policy for R-tree packing - a learned component inside a spatial index; CPU only |
| 19 | BladeDISC: Optimizing Dynamic Shape Machine Learning Workloads via Compiler Approach | https://dl.acm.org/doi/10.1145/3617327 | https://dl.acm.org/doi/pdf/10.1145/3617327 | https://github.com/alibaba/BladeDISC | ml-systems | Dynamic-shape ML compiler; single GPU is enough to reproduce most kernels. Concern: large build, CUDA/TF/PyTorch version pinning against driver 535 |
| 20 | MirrorKV: An Efficient Key-Value Store on Hybrid Cloud Storage with Balanced Performance of Compaction and Querying | https://dl.acm.org/doi/10.1145/3626736 | https://dl.acm.org/doi/pdf/10.1145/3626736 | unknown | storage | LSM key-value store splitting hot/cold across fast and slow storage; can be emulated with NVMe plus a throttled/slow tier. Concern: checked GitHub and web search, no artifact found |
| 21 | PreVision: An Out-of-Core Matrix Computation System with Optimal Buffer Replacement | https://dl.acm.org/doi/10.1145/3639297 | https://dl.acm.org/doi/pdf/10.1145/3639297 | https://github.com/snu-dbs/prevision | caching | Out-of-core matrix computation with an optimal buffer-replacement policy - a user-space caching/eviction problem on one node |
| 22 | Hyper: A High-Performance and Memory-Efficient Learned Index via Hybrid Construction | https://dl.acm.org/doi/10.1145/3654948 | https://dl.acm.org/doi/pdf/10.1145/3654948 | unknown | ml-for-systems | Hybrid bottom-up/top-down construction for learned indexes; single machine, concurrency experiments fit 32 threads. Concern: no artifact found in GitHub/web search |
| 23 | ChainedFilter: Combining Membership Filters by Chain Rule | https://dl.acm.org/doi/10.1145/3626721 | https://dl.acm.org/doi/pdf/10.1145/3626721 | https://github.com/ChainedFilter/ChainedFilter | storage | Composition of membership filters (Bloom/cuckoo/perfect hashing) with LSM and other storage use cases; CPU only |
| 24 | High-Ratio Compression for Machine-Generated Data | https://dl.acm.org/doi/10.1145/3626732 | https://dl.acm.org/doi/pdf/10.1145/3626732 | https://github.com/antgroup/pbc | storage | High-ratio compression for machine-generated data inside storage engines; CPU only |
| 25 | CAVE: Concurrency-Aware Graph Processing on SSDs | https://dl.acm.org/doi/10.1145/3654928 | https://dl.acm.org/doi/pdf/10.1145/3654928 | https://github.com/BU-DiSC/CAVE | storage | Out-of-core graph processing that tunes concurrent I/O to a single SSD; user space, no root, NVMe present |
| 26 | Query Compilation Without Regrets | https://dl.acm.org/doi/10.1145/3654968 | https://dl.acm.org/doi/pdf/10.1145/3654968 | https://github.com/nebulastream/nautilus | other-userspace | Trace-based JIT compiler framework for query engines - a user-space runtime/compiler artifact; CPU only |
| 27 | Cabin: A Compressed Adaptive Binned Scan Index | https://dl.acm.org/doi/10.1145/3639312 | https://dl.acm.org/doi/pdf/10.1145/3639312 | https://github.com/schencoding/Cabin | storage | Compressed scan index for main-memory analytics; CPU/SIMD only |
| 28 | One Seed, Two Birds: A Unified Learned Structure for Exact and Approximate Counting | https://dl.acm.org/doi/10.1145/3639270 | https://dl.acm.org/doi/pdf/10.1145/3639270 | unknown | ml-for-systems | Unified learned structure serving both exact counting and cardinality estimation. Concern: no artifact found in GitHub search |
| 29 | Making In-Memory Learned Indexes Efficient on Disk | https://dl.acm.org/doi/10.1145/3654954 | https://dl.acm.org/doi/pdf/10.1145/3654954 | https://github.com/embryo-labs/Efficient-Disk-Learned-Index | ml-for-systems | Makes in-memory learned indexes work on disk; single NVMe, user space |
| 30 | GE2: A General and Efficient Knowledge Graph Embedding Learning System | https://dl.acm.org/doi/10.1145/3654986 | https://dl.acm.org/doi/pdf/10.1145/3654986 | unknown | ml-systems | Graph/knowledge-graph embedding training system targeting CPU-GPU overlap; single-node GPU setting. Concern: no repo found in GitHub search |
| 31 | Lemo: A Cache-Enhanced Learned Optimizer for Concurrent Queries | https://dl.acm.org/doi/10.1145/3626734 | https://dl.acm.org/doi/pdf/10.1145/3626734 | unknown | ml-for-systems | Learned query optimizer with a cache for concurrent queries. Concern: no artifact found in GitHub search |
| 32 | ASM: Harmonizing Autoregressive Model, Sampling, and Multi-dimensional Statistics Merging for Cardinality Estimation | https://dl.acm.org/doi/10.1145/3639300 | https://dl.acm.org/doi/pdf/10.1145/3639300 | unknown | ml-for-systems | Autoregressive-model cardinality estimator combined with sampling; single GPU is enough. Concern: no artifact found in GitHub search |
| 33 | LPLM: A Neural Language Model for Cardinality Estimation of LIKE-Queries | https://dl.acm.org/doi/10.1145/3639309 | https://dl.acm.org/doi/pdf/10.1145/3639309 | https://github.com/dbis-ukon/lplm | ml-for-systems | Neural language model for LIKE-query cardinality estimation; small models, single GPU |
| 34 | A Learned Cuckoo Filter for Approximate Membership Queries over Variable-sized Sliding Windows on Data Streams | https://dl.acm.org/doi/10.1145/3626758 | https://dl.acm.org/doi/pdf/10.1145/3626758 | unknown | ml-for-systems | Learned cuckoo filter for approximate membership over sliding windows - a learned filter inside a stream engine. Concern: no artifact found in GitHub search |
| 35 | NOCAP: Near-Optimal Correlation-Aware Partitioning Joins | https://dl.acm.org/doi/10.1145/3626739 | https://dl.acm.org/doi/pdf/10.1145/3626739 | https://github.com/BU-DiSC/NOCAP-join | storage | I/O- and buffer-aware partitioning for storage-based hash joins; single-node NVMe, user space |
| 36 | MOST: Model-Based Compression with Outlier Storage for Time Series Data | https://dl.acm.org/doi/10.1145/3626737 | https://dl.acm.org/doi/pdf/10.1145/3626737 | https://github.com/schencoding/mostdb | storage | Model-based time-series compression with outlier storage; CPU only |
| 37 | Spruce: a Fast yet Space-saving Structure for Dynamic Graph Storage | https://dl.acm.org/doi/10.1145/3639282 | https://dl.acm.org/doi/pdf/10.1145/3639282 | https://github.com/Stardust-SJF/Spruce | storage | Space-efficient in-memory dynamic graph storage structure; 125 GiB RAM is ample |
| 38 | Learning to Optimize LSM-trees: Towards A Reinforcement Learning based Key-Value Store for Dynamic Workloads | https://dl.acm.org/doi/10.1145/3617333 | https://dl.acm.org/doi/pdf/10.1145/3617333 | unknown | ml-for-systems | RL-based tuning of LSM-tree compaction/configuration on top of RocksDB. Concern: no artifact found in GitHub search, repo unknown |
| 39 | SALI: A Scalable Adaptive Learned Index Framework based on Probability Models | https://dl.acm.org/doi/10.1145/3626752 | https://dl.acm.org/doi/pdf/10.1145/3626752 | https://github.com/cds-ruc/SALI | ml-for-systems | Scalable concurrent learned index built on LIPP; CPU only, 32 threads is a reasonable concurrency range |
| 40 | SWIX: A Memory-efficient Sliding Window Learned Index | https://dl.acm.org/doi/10.1145/3639296 | https://dl.acm.org/doi/pdf/10.1145/3639296 | https://github.com/SWIXProject/SWIX | ml-for-systems | Memory-efficient learned index for sliding windows; CPU only |
| 41 | GRF: A Global Range Filter for LSM-Trees with Shape Encoding | https://dl.acm.org/doi/10.1145/3654944 | https://dl.acm.org/doi/pdf/10.1145/3654944 | unknown | storage | Global range filter for LSM-trees with shape encoding - direct RocksDB-level artifact. Concern: checked GitHub repo search and web search, no artifact link found |
| 42 | SeRF: Segment Graph for Range-Filtering Approximate Nearest Neighbor Search | https://dl.acm.org/doi/10.1145/3639324 | https://dl.acm.org/doi/pdf/10.1145/3639324 | https://github.com/rutgers-db/SeRF | other-userspace | Range-filtering ANN search index; CPU only, single node, modest memory |
| 43 | ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data | https://dl.acm.org/doi/10.1145/3654923 | https://dl.acm.org/doi/pdf/10.1145/3654923 | https://github.com/guestrin-lab/ACORN | other-userspace | Predicate-agnostic hybrid vector search built on FAISS/HNSW; CPU only, single node |
| 44 | Rethinking the Encoding of Integers for Scans on Skewed Data | https://dl.acm.org/doi/10.1145/3626751 | https://dl.acm.org/doi/pdf/10.1145/3626751 | unknown | storage | Integer encoding for bit-parallel scans with early pruning; CPU/SIMD only. Concern: checked GitHub and web search, no artifact link found |
| 45 | LeCo: Lightweight Compression via Learning Serial Correlations | https://dl.acm.org/doi/10.1145/3639320 | https://dl.acm.org/doi/pdf/10.1145/3639320 | https://github.com/yhliu918/Learn-to-Compress | storage | Learned lightweight column compression exploiting serial correlation; CPU only |
| 46 | Grafite: Taming Adversarial Queries with Optimal Range Filters | https://dl.acm.org/doi/10.1145/3639258 | https://dl.acm.org/doi/pdf/10.1145/3639258 | https://github.com/marcocosta97/grafite | storage | Range filter with worst-case guarantees, evaluated inside key-value workloads; CPU only |
| 47 | ChainKV: A Semantics-Aware Key-Value Store for Ethereum System | https://dl.acm.org/doi/10.1145/3626713 | https://dl.acm.org/doi/pdf/10.1145/3626713 | https://github.com/czh-rot/ChainKV | storage | Semantics-aware LSM key-value store for Ethereum state; single-node NVMe |
| 48 | LIT: Lightning-fast In-memory Temporal Indexing | https://dl.acm.org/doi/10.1145/3639275 | https://dl.acm.org/doi/pdf/10.1145/3639275 | https://github.com/GiorgosChristodoulou/LIT | storage | In-memory temporal index; CPU and RAM only |
| 49 | Practical Dynamic Extension for Sampling Indexes | https://dl.acm.org/doi/10.1145/3626744 | https://dl.acm.org/doi/pdf/10.1145/3626744 | https://github.com/psu-db/sampling-extension | storage | Bentley-Saxe dynamization framework for sampling indexes; CPU only, user space |
| 50 | Cackle: Analytical Workload Cost and Performance Stability With Elastic Pools | https://dl.acm.org/doi/10.1145/3626720 | https://dl.acm.org/doi/pdf/10.1145/3626720 | unknown | scheduling | Elastic-pool provisioning policy mixing cloud functions and VMs - a scheduling/resource-allocation policy. Concern: the evaluation needs a cloud account; only a trace-driven simulation is feasible here, and no artifact was found in GitHub search |
| 51 | High-performance Effective Scientific Error-bounded Lossy Compression with Auto-tuned Multi-component Interpolation | https://dl.acm.org/doi/10.1145/3639259 | https://dl.acm.org/doi/pdf/10.1145/3639259 | https://github.com/JLiu-1/HPEZ-QoZ2.0 | storage | Error-bounded lossy compressor with auto-tuned interpolation; CPU only, user-space build |
| 52 | SkyPIE: A Fast & Accurate Oracle for Object Placement | https://dl.acm.org/doi/10.1145/3639310 | https://dl.acm.org/doi/pdf/10.1145/3639310 | https://github.com/hydro-project/cloud_oracle_skypie | scheduling | Precomputed placement-policy oracle evaluated on traces - policy/placement work that runs offline on one machine. Concern: the repo ships Docker instructions, so deps must be reproduced by hand with conda/cargo |
| 53 | Predictive and Near-Optimal Sampling for View Materialization in Video Databases | https://dl.acm.org/doi/10.1145/3639274 | https://dl.acm.org/doi/pdf/10.1145/3639274 | unknown | ml-systems | Predictive frame sampling for view materialization in video analytics; multi-object tracking models run on a single GPU. Concern: no artifact found in GitHub search |
| 54 | RaBitQ: Quantizing High-Dimensional Vectors with a Theoretical Error Bound for Approximate Nearest Neighbor Search | https://dl.acm.org/doi/10.1145/3654970 | https://dl.acm.org/doi/pdf/10.1145/3654970 | https://github.com/gaoj0017/RaBitQ | other-userspace | Vector quantization with error bounds for ANN search; CPU/SIMD only, very reproducible |
| 55 | Homomorphic Compression: Making Text Processing on Compression Unlimited | https://dl.acm.org/doi/10.1145/3626765 | https://dl.acm.org/doi/pdf/10.1145/3626765 | https://github.com/lihy0529/lossless_homomorphic_compression | storage | Compression format that supports processing directly on compressed text; CPU only |
| 56 | Udon: Efficient Debugging of User-Defined Functions in Big Data Systems with Line-by-Line Control | https://dl.acm.org/doi/10.1145/3626712 | https://dl.acm.org/doi/pdf/10.1145/3626712 | https://github.com/Texera/Udon | other-userspace | User-space debugger for UDFs in a data-processing engine; JVM/Python, no root. Concern: needs a Scala/Java toolchain installed in user space |
| 57 | Modeling Shifting Workloads for Learned Database Systems | https://dl.acm.org/doi/10.1145/3639293 | https://dl.acm.org/doi/pdf/10.1145/3639293 | unknown | ml-for-systems | Training-set construction for learned database components under workload shift. Concern: no artifact found in GitHub search |
| 58 | Cardinality Estimation over Knowledge Graphs with Embeddings and Graph Neural Networks | https://dl.acm.org/doi/10.1145/3639299 | https://dl.acm.org/doi/pdf/10.1145/3639299 | unknown | ml-for-systems | GNN plus embedding cardinality estimator for knowledge-graph queries; single GPU. Concern: no artifact found in GitHub search |
| 59 | Can Learned Indexes be Built Efficiently? A Deep Dive into Sampling Trade-offs | https://dl.acm.org/doi/10.1145/3654919 | https://dl.acm.org/doi/pdf/10.1145/3654919 | unknown | ml-for-systems | Sampling trade-offs for building learned indexes efficiently; CPU only. Concern: no artifact found in GitHub search |
| 60 | ThalamusDB: Approximate Query Processing on Multi-Modal Data | https://dl.acm.org/doi/10.1145/3654989 | https://dl.acm.org/doi/pdf/10.1145/3654989 | https://github.com/itrummer/ThalamusDB | ml-systems | Approximate query processing that schedules zero-shot ML inference inside relational operators; single GPU is enough for the CLIP/Whisper-class models used |
| 61 | Keep It Simple: Testing Databases via Differential Query Plans | https://dl.acm.org/doi/10.1145/3654991 | https://dl.acm.org/doi/pdf/10.1145/3654991 | https://github.com/sqlancer/sqlancer | other-userspace | Differential-query-plan DBMS testing implemented in SQLancer; runs DBMSs in user space, no root |

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | OptiQL: Robust Optimistic Locking for Memory-Optimized Indexes | included | in scope as other-userspace - Optimistic queue-based reader-writer lock for in-memory B+-tree/ART indexes - pure user-space multicore concurrency work; 16C/32T CPU is ample and no root is needed |
| 2 | ALP: Adaptive Lossless floating-Point Compression | included | in scope as storage - Lightweight lossless float compression scheme with a DuckDB integration; CPU/SIMD only and trivially fits the machine |
| 3 | Structural Designs Meet Optimality: Exploring Optimized LSM-tree Structures in a Colossal Configuration Space | included | in scope as storage - LSM-tree level-capacity and run-count design space built on RocksDB; single-node NVMe; only limit is the 257 GB free disk for very large datasets |
| 4 | GTS: GPU-based Tree Index for Fast Similarity Search | included | in scope as storage - GPU metric-space tree index for similarity search; the paper uses a single GPU so an A5000 fits. |
| 5 | CaaS-LSM: Compaction-as-a-Service for LSM-based Key-Value Stores in Storage Disaggregated Infrastructure | included | in scope as storage - LSM compaction offloading built on RocksDB. |
| 6 | AirIndex: Versatile Index Tuning Through Data and Storage | included | in scope as storage - I/O-aware hierarchical index builder; single-node storage profiling on NVMe, user space only |
| 7 | Language-Model Based Informed Partition of Databases to Speed Up Pattern Mining | out-topic | pattern mining over knowledge graphs |
| 8 | Robustness of Updatable Learning-based Index Advisors against Poisoning Attack | included | in scope as ml-for-systems - Poisoning robustness of learning-based index advisors - a learned component inside a DBMS; PostgreSQL in user space is enough |
| 9 | Settling Time vs. Accuracy Tradeoffs for Clustering Big Data | out-topic | clustering algorithm theory and practice |
| 10 | PACE: Poisoning Attacks on Learned Cardinality Estimation | included | in scope as ml-for-systems - Poisoning attacks on learned cardinality estimators - learned component inside the query optimizer. |
| 11 | Learning-based Property Estimation with Polynomials | out-topic | data property estimation algorithms |
| 12 | Machine Unlearning in Learned Databases: An Experimental Analysis | included | in scope as ml-for-systems - Experimental analysis of unlearning/update handling in learned DB components (cardinality estimation, learned indexes); CPU+1 GPU is enough. |
| 13 | SAGA: A Scalable Framework for Optimizing Data Cleaning Pipelines for Machine Learning Applications | out-topic | data cleaning pipeline selection for ML accuracy |
| 14 | FedCSS: Joint Client-and-Sample Selection for Hard Sample-Aware Noise-Robust Federated Learning | out-topic | federated learning sample selection algorithm |
| 15 | Splitting Tuples of Mismatched Entities | out-topic | entity resolution and data quality |
| 16 | Certain and Approximately Certain Models for Statistical Learning | out-topic | statistical learning over incomplete data |
| 17 | In-Database Data Imputation | out-topic | missing value imputation in SQL |
| 18 | Akane: Perplexity-Guided Time Series Data Cleaning | out-topic | time series data cleaning |
| 19 | Fast Maximal Quasi-clique Enumeration: A Pruning and Branching Co-Design Approach | out-topic | graph mining - quasi-clique enumeration |
| 20 | Modularity-based Hypergraph Clustering: Random Hypergraph Model, Hyperedge-cluster Relation, and Computation | out-topic | hypergraph clustering algorithm |
| 21 | Maximum k-Plex Computation: Theory and Practice | out-topic | graph mining - maximum k-plex |
| 22 | Efficient Algorithm for Budgeted Adaptive Influence Maximization: An Incremental RR-set Update Approach | out-topic | influence maximization algorithm |
| 23 | Efficient Maximum k-Defective Clique Computation with Improved Time Complexity | out-topic | graph mining - k-defective clique |
| 24 | Scalable Approximate Butterfly and Bi-triangle Counting for Large Bipartite Networks | out-topic | bipartite motif counting algorithms |
| 25 | Optimizing Disjunctive Queries with Tagged Execution | out-topic | query optimization for disjunctive predicates |
| 26 | Optimizing Nested Recursive Queries | out-topic | Datalog recursive query optimization |
| 27 | A Unified Approach for Resilience and Causal Responsibility with Integer Linear Programming (ILP) and LP Relaxations | out-topic | query resilience and causal responsibility theory |
| 28 | Selectivity Estimation for Queries Containing Predicates over Set-Valued Attributes | out-topic | selectivity estimation for set-valued predicates |
| 29 | Sub-optimal Join Order Identification with L1-error | out-topic | cardinality error metric analysis |
| 30 | PLAQUE: Automated Predicate Learning at Query Time | out-topic | predicate learning for query optimization |
| 31 | CAFE: Towards Compact, Adaptive, and Fast Embedding for Large-scale Recommendation Models | included | in scope as ml-systems - Embedding-table compression for DLRM training/inference; single-GPU DLRM runs fit in 24 GB |
| 32 | The Image Calculator: 10x Faster Image-AI Inference by Replacing JPEG with Self-designing Storage Format | out-no-code | in-topic ml-systems work, but no official artifact - checked GitHub repo search twice and a web search; Harvard DASlab page lists no code release |
| 33 | STile: Searching Hybrid Sparse Formats for Sparse Deep Learning Operators Automatically | included | in scope as ml-systems - Sparse-format search for sparse DL operators - an ML compiler/codegen artifact; single GPU (Ampere) is the paper's setting |
| 34 | SIMPLE: Efficient Temporal Graph Neural Network Training at Scale with Dynamic Data Placement | included | in scope as ml-systems - Temporal GNN training system with dynamic data placement between CPU and GPU; single-node. |
| 35 | On Efficient Large Sparse Matrix Chain Multiplication | out-topic | sparsity estimation and multiplication ordering algorithm |
| 36 | FACET: Robust Counterfactual Explanation Analytics | out-topic | counterfactual explanation analytics |
| 37 | Missing Data Imputation with Uncertainty-Driven Network | out-topic | missing data imputation model |
| 38 | OTClean: Data Cleaning for Conditional Independence Violations using Optimal Transport | out-topic | data repair under independence constraints |
| 39 | Towards Metric DBSCAN: Exact, Approximate, and Streaming Algorithms | out-topic | DBSCAN clustering algorithms |
| 40 | WeBridge: Synthesizing Stored Procedures for Large-Scale Real-World Web Applications | out-topic | program synthesis of stored procedures for web apps |
| 41 | TEE-based General-purpose Computational Backend for Secure Delegated Data Processing | out-machine | core contribution is a trusted-execution backend that requires Intel SGX/TEE hardware, which this machine does not expose |
| 42 | Waffle: An Online Oblivious Datastore for Protecting Data Access Patterns | out-topic | oblivious datastore for access-pattern privacy |
| 43 | Efficient k-Clique Listing: An Edge-Oriented Branching Strategy | out-topic | k-clique listing algorithm |
| 44 | Efficient High-Quality Clustering for Large Bipartite Graphs | out-topic | bipartite graph clustering algorithm |
| 45 | Efficient Core Maintenance in Large Bipartite Graphs | out-topic | bipartite core maintenance algorithm |
| 46 | Efficient Maximal Biplex Enumerations with Improved Worst-Case Time Guarantee | out-topic | maximal biplex enumeration algorithm |
| 47 | HERO: A Hierarchical Set Partitioning and Join Framework for Speeding up the Set Intersection Over Graphs | out-topic | set intersection algorithm for graph operators |
| 48 | A Comprehensive Survey and Experimental Study of Subgraph Matching: Trends, Unbiasedness, and Interaction | out-topic | subgraph matching survey and algorithm study |
| 49 | ROME: Robust Query Optimization via Parallel Multi-Plan Execution | out-topic | robust query optimization via parallel plans |
| 50 | Proving Query Equivalence Using Linear Integer Arithmetic | out-topic | SQL query equivalence proving |
| 51 | FedKNN: Secure Federated k-Nearest Neighbor Search | out-topic | secure federated kNN protocol |
| 52 | Relational Algorithms for Top-k Query Evaluation | out-topic | top-k conjunctive query evaluation algorithms |
| 53 | Efficient Approximation Framework for Attribute Recommendation | out-topic | attribute recommendation approximation for OLAP |
| 54 | Starling: An I/O-Efficient Disk-Resident Graph Index Framework for High-Dimensional Vector Similarity Search on Data Segment | included | in scope as storage - I/O-efficient disk-resident graph index for vector search; explicitly designed for a small memory budget on a single node |
| 55 | Automated Data Visualization from Natural Language via Large Language Models: An Exploratory Study | out-topic | LLM-based natural-language-to-visualization study |
| 56 | Optimizing Dataflow Systems for Scalable Interactive Visualization | out-topic | interactive visualization dataflow optimization |
| 57 | Time Series Representation for Visualization in Apache IoTDB | out-topic | time series visualization representation |
| 58 | Dias: Dynamic Rewriting of Pandas Code | included | in scope as other-userspace - User-space runtime that rewrites pandas code at execution time; pure Python/CPU, no root |
| 59 | On The Reasonable Effectiveness of Relational Diagrams: Explaining Relational Query Patterns and the Pattern Expressiveness of Relational Languages | out-topic | relational query pattern expressiveness theory |
| 60 | Summarized Causal Explanations For Aggregate Views | out-topic | causal explanations for aggregate views |
| 61 | Memory-Efficient and Flexible Detection of Heavy Hitters in High-Speed Networks | out-topic | network measurement sketch algorithm |
| 62 | Closest Pairs Search Over Data Stream | out-topic | closest-pair search algorithm over streams |
| 63 | PECJ: Stream Window Join on Disorder Data Streams with Proactive Error Compensation | out-topic | stream window join accuracy compensation |
| 64 | Low-Latency Adaptive Distributed Stream Join System Based on a Flexible Join Model | out-machine | in-topic as a stream-processing system, but the contribution is a distributed multi-node join system - no cluster is available and the paper's join model is about cross-node routing |
| 65 | DecoPa: Query Decomposition for Parallel Complex Event Processing | out-topic | complex event processing query decomposition |
| 66 | Convolution and Cross-Correlation of Count Sketches Enables Fast Cardinality Estimation of Multi-Join Queries | out-topic | sketch-based cardinality estimation algorithm |
| 67 | Rethinking Learned Cost Models: Why Start from Scratch? | included | in scope as ml-for-systems - Learned cost models for query optimization, transferability across databases. |
| 68 | Sibyl: Forecasting Time-Evolving Query Workloads | out-no-code | in-topic ml-for-systems, but it is a Microsoft-internal workload forecasting stack - checked GitHub repo search twice, no public artifact |
| 69 | LST-Bench: Benchmarking Log-Structured Tables in the Cloud | included | in scope as storage - Benchmark harness for log-structured tables (Delta/Hudi/Iceberg). |
| 70 | DoppelGanger++: Towards Fast Dependency Graph Generation for Database Replay | out-no-code | in-topic as DBMS replay tooling, but it is an SAP HANA internal system - checked GitHub repo search, no public artifact |
| 71 | Revisiting B-tree Compression: An Experimental Study | included | in scope as storage - Experimental study of seven B-tree compression techniques - a reusable single-node index benchmark. |
| 72 | PLATON: Top-down R-tree Packing with Learned Partition Policy | included | in scope as ml-for-systems - Learned partition policy for R-tree packing - a learned component inside a spatial index; CPU only |
| 73 | BladeDISC: Optimizing Dynamic Shape Machine Learning Workloads via Compiler Approach | included | in scope as ml-systems - Dynamic-shape ML compiler; single GPU is enough to reproduce most kernels. |
| 74 | Nexus: Correlation Discovery over Collections of Spatio-Temporal Tabular Data | out-topic | correlation discovery over tabular datasets |
| 75 | DGC: Training Dynamic Graphs with Spatio-Temporal Non-Uniformity using Graph Partitioning by Chunks | out-machine | GNN training system whose core contribution is distributed graph partitioning across machines and GPUs |
| 76 | HongTu: Scalable Full-Graph GNN Training on Multiple GPUs | out-machine | the contribution is multi-GPU communication deduplication and CPU-offload across a 4xA100 server; the mechanism has no meaningful single-GPU form |
| 77 | Efficient Algorithm for K-Multiple-Means | out-topic | clustering algorithm |
| 78 | FeatureLTE: Learning to Estimate Feature Importance | out-topic | feature importance estimation for ML |
| 79 | Wii: Dynamic Budget Reallocation In Index Tuning | out-no-code | in-topic as automated DBMS tuning, but built on Microsoft SQL Server's internal what-if API - checked GitHub, no public artifact |
| 80 | MirrorKV: An Efficient Key-Value Store on Hybrid Cloud Storage with Balanced Performance of Compaction and Querying | included | in scope as storage - LSM key-value store splitting hot/cold across fast and slow storage; can be emulated with NVMe plus a throttled/slow tier. |
| 81 | Limousine: Blending Learned and Classical Indexes to Self-Design Larger-than-Memory Cloud Storage Engines | out-no-code | in-topic storage-engine self-design work, but no artifact released - checked GitHub repo search twice; Harvard DASlab publishes no code for Limousine |
| 82 | PreVision: An Out-of-Core Matrix Computation System with Optimal Buffer Replacement | included | in scope as caching - Out-of-core matrix computation with an optimal buffer-replacement policy - a user-space caching/eviction problem on one node |
| 83 | Hyper: A High-Performance and Memory-Efficient Learned Index via Hybrid Construction | included | in scope as ml-for-systems - Hybrid bottom-up/top-down construction for learned indexes; single machine, concurrency experiments fit 32 threads. |
| 84 | Wred: Workload Reduction for Scalable Index Tuning | out-no-code | in-topic as index tuning, but built on Microsoft SQL Server internals - checked GitHub, no public artifact |
| 85 | DProvDB: Differentially Private Query Processing with Multi-Analyst Provenance | out-topic | differentially private query processing |
| 86 | DP-starJ: A Differential Private Scheme towards Analytical Star-Join Queries | out-topic | differential privacy for star joins |
| 87 | Anchor: A Library for Building Secure Persistent Memory Systems | out-machine | requires byte-addressable persistent memory and CXL-attached devices, which this machine does not have |
| 88 | Veil: A Storage and Communication Efficient Volume-Hiding Algorithm | out-topic | encrypted search volume hiding |
| 89 | An LDP Compatible Sketch for Securely Approximating Set Intersection Cardinalities | out-topic | private set intersection sketch |
| 90 | Local Differentially Private Heavy Hitter Detection in Data Streams with Bounded Memory | out-topic | local differential privacy heavy hitters |
| 91 | ChainedFilter: Combining Membership Filters by Chain Rule | included | in scope as storage - Composition of membership filters (Bloom/cuckoo/perfect hashing) with LSM and other storage use cases; CPU only |
| 92 | Reservoir Sampling over Joins | out-topic | sampling over joins algorithm |
| 93 | StarfishDB: A Query Execution Engine for Relational Probabilistic Programming | out-topic | probabilistic programming query engine |
| 94 | High-Ratio Compression for Machine-Generated Data | included | in scope as storage - High-ratio compression for machine-generated data inside storage engines; CPU only |
| 95 | AS-Parser: Log Parsing Based on Adaptive Segmentation | out-topic | log parsing algorithm |
| 96 | RITA: Group Attention is All You Need for Timeseries Analytics | out-topic | transformer architecture for time series embeddings |
| 97 | MCR-Tree: An Efficient Index for Multi-dimensional Core Search | out-topic | multi-dimensional core search index for graphs |
| 98 | Efficient and Provable Effective Resistance Computation on Large Graphs: An Index-based Approach | out-topic | effective resistance computation on graphs |
| 99 | Graph Summarization: Compactness Meets Efficiency | out-topic | graph summarization algorithm |
| 100 | A Counting-based Approach for Efficient k-Clique Densest Subgraph Discovery | out-topic | densest subgraph discovery algorithm |
| 101 | Implementation Strategies for Views over Property Graphs | out-topic | property graph view implementation strategies |
| 102 | CAVE: Concurrency-Aware Graph Processing on SSDs | included | in scope as storage - Out-of-core graph processing that tunes concurrent I/O to a single SSD; user space, no root, NVMe present |
| 103 | Query Compilation Without Regrets | included | in scope as other-userspace - Trace-based JIT compiler framework for query engines - a user-space runtime/compiler artifact; CPU only |
| 104 | Cabin: A Compressed Adaptive Binned Scan Index | included | in scope as storage - Compressed scan index for main-memory analytics; CPU/SIMD only |
| 105 | Efficient Approximation of Kemeny's Constant for Large Graphs | out-topic | Kemeny constant approximation on graphs |
| 106 | Worst-Case-Optimal Similarity Joins on Graph Databases | out-topic | similarity join algorithms on graph databases |
| 107 | Hierarchical Cut Labelling - Scaling Up Distance Queries on Road Networks | out-topic | road network distance labelling |
| 108 | MWP: Multi-Window Parallel Evaluation of Regular Path Queries on Streaming Graphs | out-topic | regular path queries on streaming graphs |
| 109 | Lorentz: Learned SKU Recommendation Using Profile Data | out-no-code | in-topic as learned resource configuration, but it is a Microsoft-internal cloud SKU recommender - checked GitHub, no public artifact |
| 110 | SchemaPile: A Large Collection of Relational Database Schemas | out-topic | dataset of relational schemas |
| 111 | Solo: Data Discovery Using Natural Language Questions Via A Self-Supervised Approach | out-topic | natural-language data discovery |
| 112 | Controllable Tabular Data Synthesis Using Diffusion Models | out-topic | tabular data synthesis with diffusion models |
| 113 | One Seed, Two Birds: A Unified Learned Structure for Exact and Approximate Counting | included | in scope as ml-for-systems - Unified learned structure serving both exact counting and cardinality estimation. |
| 114 | Making In-Memory Learned Indexes Efficient on Disk | included | in scope as ml-for-systems - Makes in-memory learned indexes work on disk; single NVMe, user space |
| 115 | Origin-Destination Travel Time Oracle for Map-based Services | out-topic | travel time estimation oracle |
| 116 | Demystifying the QoS and QoE of Edge-hosted Video Streaming Applications in the Wild with SNESet | out-topic | measurement study and dataset of edge video QoE |
| 117 | Temporal JSON Keyword Search | out-topic | temporal JSON keyword search |
| 118 | Proximity Queries on Point Clouds using Rapid Construction Path Oracle | out-topic | proximity queries on point clouds |
| 119 | FineMon: An Innovative Adaptive Network Telemetry Scheme for Fine-Grained, Multi-Metric Data Monitoring with Dynamic Frequency Adjustment and Enhanced Data Recovery | out-topic | network telemetry measurement scheme |
| 120 | Optimizing Time Series Queries with Versions | out-topic | versioned time series query semantics and optimization |
| 121 | Parallel Algorithms for Hierarchical Nucleus Decomposition | out-topic | nucleus decomposition algorithms |
| 122 | View-based Explanations for Graph Neural Networks | out-topic | GNN explanation |
| 123 | GE2: A General and Efficient Knowledge Graph Embedding Learning System | included | in scope as ml-systems - Graph/knowledge-graph embedding training system targeting CPU-GPU overlap; single-node GPU setting. |
| 124 | TeraHAC: Hierarchical Agglomerative Clustering of Trillion-Edge Graphs | out-machine | hierarchical clustering designed for trillion-edge graphs on a large distributed cluster |
| 125 | Neural Attributed Community Search at Billion Scale | out-topic | attributed community search |
| 126 | Enriching Recommendation Models with Logic Conditions | out-topic | logic conditions for recommendation models |
| 127 | GEqO: ML-Accelerated Semantic Equivalence Detection | out-no-code | in-topic as an ML component inside a query engine, but it is Microsoft SCOPE-internal - checked GitHub repo search twice, no public artifact |
| 128 | Lemo: A Cache-Enhanced Learned Optimizer for Concurrent Queries | included | in scope as ml-for-systems - Learned query optimizer with a cache for concurrent queries. |
| 129 | ASM: Harmonizing Autoregressive Model, Sampling, and Multi-dimensional Statistics Merging for Cardinality Estimation | included | in scope as ml-for-systems - Autoregressive-model cardinality estimator combined with sampling; single GPU is enough. |
| 130 | LPLM: A Neural Language Model for Cardinality Estimation of LIKE-Queries | included | in scope as ml-for-systems - Neural language model for LIKE-query cardinality estimation; small models, single GPU |
| 131 | A Learned Cuckoo Filter for Approximate Membership Queries over Variable-sized Sliding Windows on Data Streams | included | in scope as ml-for-systems - Learned cuckoo filter for approximate membership over sliding windows - a learned filter inside a stream engine. |
| 132 | NOCAP: Near-Optimal Correlation-Aware Partitioning Joins | included | in scope as storage - I/O- and buffer-aware partitioning for storage-based hash joins; single-node NVMe, user space |
| 133 | MOST: Model-Based Compression with Outlier Storage for Time Series Data | included | in scope as storage - Model-based time-series compression with outlier storage; CPU only |
| 134 | Spruce: a Fast yet Space-saving Structure for Dynamic Graph Storage | included | in scope as storage - Space-efficient in-memory dynamic graph storage structure; 125 GiB RAM is ample |
| 135 | Learning to Optimize LSM-trees: Towards A Reinforcement Learning based Key-Value Store for Dynamic Workloads | included | in scope as ml-for-systems - RL-based tuning of LSM-tree compaction/configuration on top of RocksDB. |
| 136 | SALI: A Scalable Adaptive Learned Index Framework based on Probability Models | included | in scope as ml-for-systems - Scalable concurrent learned index built on LIPP; CPU only, 32 threads is a reasonable concurrency range |
| 137 | SWIX: A Memory-efficient Sliding Window Learned Index | included | in scope as ml-for-systems - Memory-efficient learned index for sliding windows; CPU only |
| 138 | GRF: A Global Range Filter for LSM-Trees with Shape Encoding | included | in scope as storage - Global range filter for LSM-trees with shape encoding - direct RocksDB-level artifact. |
| 139 | Data Acquisition for Improving Model Confidence | out-topic | data acquisition for model confidence |
| 140 | SeRF: Segment Graph for Range-Filtering Approximate Nearest Neighbor Search | included | in scope as other-userspace - Range-filtering ANN search index; CPU only, single node, modest memory |
| 141 | ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data | included | in scope as other-userspace - Predicate-agnostic hybrid vector search built on FAISS/HNSW; CPU only, single node |
| 142 | Generation of Training Examples for Tabular Natural Language Inference | out-topic | training example generation for tabular NLI |
| 143 | On Querying Historical Connectivity in Temporal Graphs | out-topic | temporal graph connectivity index |
| 144 | uBlade: Efficient Batch Processing for Uncertainty Graph Queries | out-topic | uncertain graph query batch processing |
| 145 | Materialized View Selection & View-Based Query Planning for Regular Path Queries | out-topic | materialized view selection for regular path queries |
| 146 | TabEE: Tabular Embeddings Explanations | out-topic | explanations for tabular embeddings |
| 147 | Auto-Formula: Recommend Formulas in Spreadsheets using Contrastive Learning for Table Representations | out-topic | spreadsheet formula recommendation |
| 148 | Qr-Hint: Actionable Hints Towards Correcting Wrong SQL Queries | out-topic | SQL debugging hints for learners |
| 149 | SH2O: Efficient Data Access for Work-Sharing Databases | out-no-code | in-topic as a shared-scan data access operator, but built inside EPFL's closed Proteus engine - checked GitHub repo search twice, no public artifact |
| 150 | Lightweight Materialization for Fast Dashboards Over Joins | out-topic | incremental materialization for dashboard queries |
| 151 | Rethinking the Encoding of Integers for Scans on Skewed Data | included | in scope as storage - Integer encoding for bit-parallel scans with early pruning; CPU/SIMD only. |
| 152 | Determining Exact Quantiles with Randomized Summaries | out-topic | quantile summary algorithm |
| 153 | Scalable Distributed Inverted List Indexes in Disaggregated Memory | out-machine | requires RDMA-connected disaggregated memory hardware |
| 154 | Fault Tolerance Placement in the Internet of Things | out-topic | fault tolerance placement for IoT edge deployments |
| 155 | LeCo: Lightweight Compression via Learning Serial Correlations | included | in scope as storage - Learned lightweight column compression exploiting serial correlation; CPU only |
| 156 | Grafite: Taming Adversarial Queries with Optimal Range Filters | included | in scope as storage - Range filter with worst-case guarantees, evaluated inside key-value workloads; CPU only |
| 157 | ChainKV: A Semantics-Aware Key-Value Store for Ethereum System | included | in scope as storage - Semantics-aware LSM key-value store for Ethereum state; single-node NVMe |
| 158 | LIT: Lightning-fast In-memory Temporal Indexing | included | in scope as storage - In-memory temporal index; CPU and RAM only |
| 159 | Practical Dynamic Extension for Sampling Indexes | included | in scope as storage - Bentley-Saxe dynamization framework for sampling indexes; CPU only, user space |
| 160 | VeriTxn: Verifiable Transactions for Cloud-Native Databases with Storage Disaggregation | out-machine | verifiable transactions for cloud-native databases with separate compute and storage tiers plus TEE assumptions |
| 161 | Cackle: Analytical Workload Cost and Performance Stability With Elastic Pools | included | in scope as scheduling - Elastic-pool provisioning policy mixing cloud functions and VMs - a scheduling/resource-allocation policy. |
| 162 | High-performance Effective Scientific Error-bounded Lossy Compression with Auto-tuned Multi-component Interpolation | included | in scope as storage - Error-bounded lossy compressor with auto-tuned interpolation; CPU only, user-space build |
| 163 | SkyPIE: A Fast & Accurate Oracle for Object Placement | included | in scope as scheduling - Precomputed placement-policy oracle evaluated on traces - policy/placement work that runs offline on one machine. |
| 164 | Vexless: A Serverless Vector Data Management System Using Cloud Functions | out-machine | the whole system is built on Azure Cloud Functions; there is no single-machine form of the contribution |
| 165 | Understanding the Performance Implications of the Design Principles in Storage-Disaggregated Databases | out-machine | measurement study that requires a real storage-disaggregated cloud database deployment |
| 166 | Rethink Query Optimization in HTAP Databases | out-machine | query optimization for distributed HTAP databases with separate row and column replicas across nodes |
| 167 | Correlation Joins over Time Series Data Streams Utilizing Complementary Dimension Reduction and Transformation | out-topic | correlation join algorithms over time series streams |
| 168 | In-depth Analysis of Continuous Subgraph Matching in a Common Delta Query Compilation Framework | out-topic | continuous subgraph matching study |
| 169 | gSWORD: GPU-accelerated Sampling for Subgraph Counting | out-topic | subgraph counting sampling algorithm |
| 170 | Zero-sided RDMA: Network-driven Data Shuffling for Disaggregated Heterogeneous Cloud DBMSs | out-machine | requires RDMA NICs and a programmable switch |
| 171 | PimPam: Efficient Graph Pattern Matching on Real Processing-in-Memory Hardware | out-machine | requires real UPMEM processing-in-memory hardware |
| 172 | F3KM: Federated, Fair, and Fast k-means | out-topic | fair federated k-means algorithm |
| 173 | Faster Algorithms for Fair Max-Min Diversification in Rd | out-topic | fair diversity maximization algorithms |
| 174 | SeeSaw: Interactive Ad-hoc Search Over Image Databases | out-topic | interactive image search interface |
| 175 | Predictive and Near-Optimal Sampling for View Materialization in Video Databases | included | in scope as ml-systems - Predictive frame sampling for view materialization in video analytics; multi-object tracking models run on a single GPU. |
| 176 | RaBitQ: Quantizing High-Dimensional Vectors with a Theoretical Error Bound for Approximate Nearest Neighbor Search | included | in scope as other-userspace - Vector quantization with error bounds for ANN search; CPU/SIMD only, very reproducible |
| 177 | CodeS: Towards Building Open-source Language Models for Text-to-SQL | out-topic | text-to-SQL language model training - the contribution is a model, not a serving or inference system |
| 178 | NOC-NOC: Towards Performance-optimal Distributed Transactions | out-machine | distributed transaction protocol requiring a multi-node deployment |
| 179 | Efficient Distributed Hop-Constrained Path Enumeration on Large-Scale Graphs | out-machine | distributed path enumeration across a cluster |
| 180 | Historical Embedding-Guided Efficient Large-Scale Federated Graph Learning | out-machine | federated graph learning across distributed parties |
| 181 | Play like a Vertex: A Stackelberg Game Approach for Streaming Graph Partitioning | out-topic | streaming graph partitioning algorithm |
| 182 | Optimizing Distributed Protocols with Query Rewrites | out-machine | rewrites for distributed protocols such as Paxos and 2PC, evaluated on a cluster |
| 183 | ADGNN: Towards Scalable GNN Training with Aggregation-Difference Aware Sampling | out-machine | distributed GNN training across multiple machines |
| 184 | Determining the Largest Overlap between Tables | out-topic | table overlap detection |
| 185 | High Precision ≠ High Cost: Temporal Data Fusion for Multiple Low-Precision Sensors | out-topic | sensor data fusion |
| 186 | Homomorphic Compression: Making Text Processing on Compression Unlimited | included | in scope as storage - Compression format that supports processing directly on compressed text; CPU only |
| 187 | Table-GPT: Table Fine-tuned GPT for Diverse Table Tasks | out-topic | LLM fine-tuning for table tasks - the contribution is a model |
| 188 | Udon: Efficient Debugging of User-Defined Functions in Big Data Systems with Line-by-Line Control | included | in scope as other-userspace - User-space debugger for UDFs in a data-processing engine; JVM/Python, no root. |
| 189 | Banzhaf Values for Facts in Query Answering | out-topic | Banzhaf value computation for query provenance |
| 190 | Modeling Shifting Workloads for Learned Database Systems | included | in scope as ml-for-systems - Training-set construction for learned database components under workload shift. |
| 191 | Cardinality Estimation over Knowledge Graphs with Embeddings and Graph Neural Networks | included | in scope as ml-for-systems - GNN plus embedding cardinality estimator for knowledge-graph queries; single GPU. |
| 192 | Approximate Sketches | out-topic | sketching for filtered join cardinality |
| 193 | PreLog: A Pre-trained Model for Log Analytics | out-topic | pre-trained model for log analytics |
| 194 | Can Learned Indexes be Built Efficiently? A Deep Dive into Sampling Trade-offs | included | in scope as ml-for-systems - Sampling trade-offs for building learned indexes efficiently; CPU only. |
| 195 | ThalamusDB: Approximate Query Processing on Multi-Modal Data | included | in scope as ml-systems - Approximate query processing that schedules zero-shot ML inference inside relational operators; single GPU is enough for the CLIP/Whisper-class models used |
| 196 | Query Refinement for Diverse Top-k Selection | out-topic | query refinement for diverse top-k |
| 197 | Equitable Top-k Results for Long Tail Data | out-topic | fairness in top-k results |
| 198 | FairHash: A Fair and Memory/Time-efficient Hashmap | out-topic | fairness-constrained hashmap construction |
| 199 | Fast Shapley Value Computation in Data Assemblage Tasks as Cooperative Simple Games | out-topic | Shapley value computation |
| 200 | Relative Keys: Putting Feature Explanation into Context | out-topic | feature explanation |
| 201 | Counterfactual Explanation at Will, with Zero Privacy Leakage | out-topic | private counterfactual explanations |
| 202 | Privacy Amplification by Sampling under User-level Differential Privacy | out-topic | differential privacy amplification theory |
| 203 | Keep It Simple: Testing Databases via Differential Query Plans | included | in scope as other-userspace - Differential-query-plan DBMS testing implemented in SQLancer; runs DBMSs in user space, no root |
| 204 | Continual Observation of Joins under Differential Privacy | out-topic | differentially private continual join observation |
| 205 | Object-oriented Unified Encrypted Memory Management for Heterogeneous Memory Architectures | out-machine | encrypted memory management for heterogeneous memory hardware such as persistent memory and CXL tiers |
| 206 | Secure Sampling for Approximate Multi-party Query Processing | out-topic | secure multi-party sampling protocols |
| 207 | The Battleship Approach to the Low Resource Entity Matching Problem | out-topic | entity matching with language models |
| 208 | Watchog: A Light-weight Contrastive Learning based Framework for Column Annotation | out-topic | column type annotation model |
| 209 | Unstructured Data Fusion for Schema and Data Extraction | out-topic | schema and data extraction from text |
| 210 | R2D2: Reducing Redundancy and Duplication in Data Lakes | out-topic | redundancy detection in data lakes |
| 211 | DTT: An Example-Driven Tabular Transformer for Joinability by Leveraging Large Language Models | out-topic | LLM-based tabular transformation for joinability |
| 212 | Discovering Functional Dependencies through Hitting Set Enumeration | out-topic | functional dependency discovery algorithm |
| 213 | Towards Buffer Management with Tiered Main Memory | out-machine | in-topic memory-tiering work, but every design studied needs RDMA- or CXL-attached remote memory; this host has one NUMA node and no such interconnect |
