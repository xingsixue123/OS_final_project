STATUS: complete
TOTAL_PAPERS: 297
INCLUDED: 68

## Sources

**Primary list.** `https://vldb.org/2026/program.html` — the official VLDB 2026 (Boston, 31 Aug – 4 Sep
2026) conference program, fetched with `curl` as raw HTML (2.29 MB) and parsed with a script rather than
summarized. The `#tab-oral` ("Research sessions") block contains one card per presented paper with paper
type badge (REG / EA&B / SDS / VIS / VLDB J.), title, PVLDB PDF link, authors, affiliations and the full
abstract. Parsing it yields **304 cards**: 297 PVLDB research-track papers and 7 invited VLDB Journal talks.
The 7 VLDB Journal papers (which link to Springer VLDBJ articles, not PVLDB) are excluded from the count,
as are the industry sessions, demonstrations, tutorials, panels and workshops, which live in separate tabs.
**TOTAL_PAPERS = 297.**

**Cross-check 1 — PVLDB Volume 19 table of contents.** `https://vldb.org/pvldb/volumes/19/` is a Next.js
page; the embedded `__NEXT_DATA__` JSON was extracted and parsed. It lists **457 entries** across 12 issues.
Removing the 12 per-issue Front Matter entries and the 165 industry-track papers of issue 12 leaves
**280 research papers in vol 19 issues 1–11**. The program's 297 research papers decompose into exactly
**280 vol-19 papers** (278 exact title matches plus 2 with trivial title variants: "RED-ANNS: An/A RDMA-Enabled…"
and "Toward Temporal Attribution Analytics in Dataflows [Vision Paper]") and **17 PVLDB vol-18 papers**
(vol 18 issue 12, e.g. `vol18/p5638-misegiannis.pdf`), which is the expected roll-over of the last vol-18
issue into the following conference. The two sources therefore agree exactly on the vol-19 side
(280 = 280) and the remaining 17 are accounted for by their vol-18 PDF URLs.

**Cross-check 2 — poster sessions.** The program's `#tab-poster` block lists 296 research posters; all 296
paper IDs are a subset of the oral research-session paper IDs, confirming that the research-session tab is
the complete presented set and not a selected subset.

**DBLP** (`dblp.org/db/journals/pvldb/`) was attempted but is behind an Anubis proof-of-work challenge that
blocks scripted fetching, so the PVLDB volume page was used as the second source instead.

**Per-paper artifact checks.** For every paper that survived the topic and machine screens the official PDF
was downloaded from `vldb.org/pvldb/vol19/…` or `vol18/…` and the "PVLDB Artifact Availability" statement on
the first page was read (`pdftotext`); the extracted URLs were then HTTP-checked. 68 of the 70 surviving
papers declare a reachable artifact. Two were rejected: "GPU Acceleration of SQL Analytics on Compressed
Data" has no artifact statement at all and a GitHub search for its TQP-based prototype returned nothing, and
"FlatStor" declares `github.com/SJTU-Storage-Lab/FlatStor-Columnar-Layout`, which returns 404 while the
`SJTU-Storage-Lab` organisation lists no such repository.

**Screening conventions used.** VLDB is a data-management venue, so a line had to be drawn inside the very
large indexing / vector-search / graph-algorithm population. `other-userspace` was applied only to papers
whose contribution is a general systems mechanism (synchronization and concurrency, code generation and
runtimes, parallel parsing and sorting, GPU or RT-core resource use), not to papers whose contribution is a
data-management algorithm or a query-semantics protocol. Approximate-nearest-neighbour papers were kept only
when the contribution is an OS-level resource mechanism — caching, disk I/O, or CPU–GPU co-processing — and
dropped when it is index construction, quantization, or search-parameter tuning. Likewise `ml-for-systems`
was applied to learned components that control system resources (knobs, compaction, buffer pools, admission,
index layout) rather than to learned models of query semantics or cardinality.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | CloudGlide: Deconstructing the Landscape of Cloud-Based Analytics | https://doi.org/10.14778/3773731.3773739 | https://www.vldb.org/pvldb/vol18/p5638-misegiannis.pdf | https://github.com/mikegeo98/cloudglide_olap | scheduling | White-box discrete-event simulator for provisioning caching scheduling and pricing policies in cloud analytics; exactly the trace and simulator driven policy study the scope allows on one machine. Simulator is pure user-space Python |
| 2 | Bespoke OLAP: Synthesizing Workload-Specific One-size-fits-one Database Engines | https://doi.org/10.14778/3836663.3836723 | https://www.vldb.org/pvldb/vol19/p3759-wehrstein.pdf | https://github.com/DataManagementLab/BespokeOLAP | ml-for-systems | LLM-driven synthesis of workload-specific OLAP engines compared against DuckDB and Umbra; a learned or LLM-based system-generation loop that runs entirely in user space. Concern: needs a paid LLM API and long synthesis loops |
| 3 | LiquidCache: Efficient Pushdown Caching for Cloud-Native Data Analytics | https://doi.org/10.14778/3773731.3773741 | https://www.vldb.org/pvldb/vol18/p5662-hao.pdf | https://github.com/XiangpengHao/liquid-cache | caching | Pushdown cache layer that transcodes Parquet into a Liquid format to cut cache CPU time; built on Apache DataFusion in Rust. Cache and compute servers are separate processes and can both run on this host |
| 4 | A Resource-centric Analysis and Optimization of NoSQL Workloads using Distressed Resource Volume Metric | https://doi.org/10.14778/3819518.3819520 | https://www.vldb.org/pvldb/vol19/p1867-simmhan.pdf | https://aka.ms/LoadStar | scheduling | Open-sourced Cosmos DB replica traces plus the LoadStar policy simulator for packing and migration; trace-driven resource-management study with no cluster needed. Concern: artifact is behind an aka.ms redirect |
| 5 | Breaking the Isolation-Freshness Trade-off: Joint Adaptive Storage Optimization for HTAP Systems | https://doi.org/10.14778/3797919.3797924 | https://www.vldb.org/pvldb/vol19/p1142-ding.pdf | https://github.com/DBXAI/Jasper | storage | Adaptive row and column storage layout selection for HTAP implemented in TiDB; the mechanism is a storage layout policy. Concern: needs a TiDB plus TiFlash deployment which is heavy but can run as multiple processes on one host |
| 6 | TVA: A Version-aware Temporal Graph Storage System for Real-time Analytics | https://doi.org/10.14778/3828612.3828613 | https://www.vldb.org/pvldb/vol19/p2536-li.pdf | https://github.com/Sakuraaa0/TVA | storage | Multi-version temporal graph storage engine with custom hashing and version metadata layout; single-node storage engine work with an open repo |
| 7 | Sampling-based Predictive Database Buffer Management | https://doi.org/10.14778/3773731.3773734 | https://www.vldb.org/pvldb/vol18/p5569-khalaji.pdf | https://github.com/serene-lamport/postgresql-test-scripts | caching | Sampling-based predictive buffer replacement evaluated both by simulation on Redshift traces and by patching PostgreSQL; a textbook cache-policy improvement target that fits this machine perfectly |
| 8 | LiBox: A Learned Index as an Array to Minimize Last-Mile Search | https://doi.org/10.14778/3796195.3796199 | https://www.vldb.org/pvldb/vol19/p836-jiang.pdf | https://github.com/strivesnail/Libox | ml-for-systems | Learned index that reduces last-mile search to a single SIMD step. Concern: the key mechanism uses an AVX-512 instruction and this Zen 3 Threadripper has no AVX-512 so the headline result cannot be reproduced without an AVX2 fallback |
| 9 | Rethinking Learned Index and LSM-tree Integration | https://doi.org/10.14778/3836663.3836671 | https://www.vldb.org/pvldb/vol19/p3034-zhao.pdf | https://github.com/ErosBryant/WildTurkey | ml-for-systems | Wild Turkey integrates learned indexes into LSM-trees with an RL controller for SSTable sizing and error bounds; RocksDB-based single-node artifact |
| 10 | Learned Static Function Data Structures | https://doi.org/10.14778/3796195.3796205 | https://www.vldb.org/pvldb/vol19/p917-vinciguerra.pdf | https://github.com/gvinciguerra/LearnedStaticFunction | ml-for-systems | Learned static function data structures that use per-key predicted distributions to beat the zero-order entropy bound; pure user-space C++ library |
| 11 | Mil: Cost-guided Minimum Makespan Scheduling for Applications of Multiple LLMs | https://doi.org/10.14778/3819518.3819522 | https://www.vldb.org/pvldb/vol19/p1893-fang.pdf | https://github.com/puddingfjz/Mil | scheduling | Makespan scheduling for offline multi-LLM applications with an inference simulator and processing-rate estimators. Concern: GPU allocation and parallelism selection assume several GPUs so only the simulator and a single-GPU scaled-down setting are reproducible |
| 12 | DeXOR: Enabling XOR in Decimal Space for Streaming Lossless Compression of Floating-point Data | https://doi.org/10.14778/3796195.3796200 | https://www.vldb.org/pvldb/vol19/p849-li.pdf | https://github.com/SuDIS-ZJU/DeXOR | storage | Streaming lossless floating-point compression framework; small self-contained user-space codec ideal for a 10-week improvement project |
| 13 | Accelerating String-Heavy Queries with LLM Token Tables | https://doi.org/10.14778/3836663.3836714 | https://www.vldb.org/pvldb/vol19/p3635-schmidt.pdf | https://github.com/umbra-db/token-vldb2026 | storage | Reuses an LLM tokenizer as a global string symbol table so joins and aggregations run on encoded data. Concern: implemented inside Umbra which is not open source although the authors released a token-table artifact repo |
| 14 | RAGPerf: An End-to-End Benchmarking Framework for Retrieval-Augmented Generation Systems | https://doi.org/10.14778/3836663.3836718 | https://www.vldb.org/pvldb/vol19/p3689-li.pdf | https://github.com/platformxlab/RAGPerf | llm-inference | End-to-end RAG serving benchmark that measures throughput host and GPU memory and CPU GPU utilization across vector stores and LLMs; open-sourced and single-node |
| 15 | ArceKV: Towards Workload-driven LSM-compactions for Key-Value Store Under Dynamic Workloads | https://doi.org/10.14778/3796195.3796208 | https://www.vldb.org/pvldb/vol19/p958-liu.pdf | https://github.com/NTU-Siqiang-Group/ArceKV | storage | Workload-driven LSM compaction decision engine implemented on top of RocksDB; a clean single-node storage improvement target |
| 16 | Dynamic read & write optimization with TurtleKV | https://doi.org/10.14778/3819518.3819523 | https://www.vldb.org/pvldb/vol19/p1907-astolfi.pdf | https://github.com/mathworks/turtle_kv | storage | New on-disk read write balanced TurtleTree structure with explicit write-memory tuning knobs evaluated with YCSB; single-node key-value store |
| 17 | How Much Can RocksDB Chew? Achieving Near-Zero Write Stalls with Sustainable RocksDB | https://doi.org/10.14778/3836663.3836683 | https://www.vldb.org/pvldb/vol19/p3202-shin.pdf | https://github.com/shinhojin/Sustainable-RocksDB | storage | Reframes RocksDB write stalls as a control problem and adds an online RL admission controller; single-node and directly reproducible on NVMe |
| 18 | Tidehunter: Large-Value Storage With Minimal Data Relocation | https://doi.org/10.14778/3836663.3836725 | https://www.vldb.org/pvldb/vol19/p3786-zablotchi.pdf | https://github.com/MystenLabs/tidehunter | storage | WAL-as-permanent-storage key-value engine with lock-free writes on NVMe; production-quality Rust artifact. Concern: the 1 TB dataset experiment must be scaled down to the free space available |
| 19 | Abacus: A Cost-Based Optimizer for Semantic Operator Systems | https://doi.org/10.14778/3796195.3796215 | https://www.vldb.org/pvldb/vol19/p1060-russo.pdf | https://github.com/mitdbg/palimpzest | ml-systems | Cost-based optimizer for LLM-powered semantic operator pipelines released inside the Palimpzest system. Concern: optimization quality depends on LLM API cost and non-determinism |
| 20 | stratum: A System Infrastructure for Massive Agent-Centric ML Workloads | https://doi.org/10.14778/3836663.3836726 | https://www.vldb.org/pvldb/vol19/p3799-phani.pdf | https://github.com/deem-data/stratum | ml-systems | Vision paper proposing a runtime for executing thousands of agent-generated Python ML pipelines; artifact repo exists. Concern: vision-track paper so the prototype may be early stage |
| 21 | AQD: Online Adaptive Query Dispatcher for HTAP Databases | https://doi.org/10.14778/3801059.3801071 | https://www.vldb.org/pvldb/vol19/p1586-wu.pdf | https://github.com/earthwuyang/aqd | ml-for-systems | Learned online query dispatcher that routes queries between row and column engines with low latency. Concern: needs an HTAP dual-engine deployment |
| 22 | RayDB: Building Databases with Ray Tracing Cores | https://doi.org/10.14778/3772181.3772185 | https://www.vldb.org/pvldb/vol19/p43-shi.pdf | https://github.com/LonelySlim/myOptixDB | other-userspace | Query engine that maps operator pipelines onto GPU ray-tracing cores via OptiX; the RTX A5000 has second-generation RT cores so the mechanism is reproducible on this machine |
| 23 | High-Performance DBMSs with io_uring: When and How to Use It | https://doi.org/10.14778/3819518.3819553 | https://www.vldb.org/pvldb/vol19/p2317-jasny.pdf | https://github.com/mjasny/vldb26-iouring | storage | Systematic study of io_uring in a buffer manager and in network shuffling with concrete design guidelines; user-space Linux I O work. Concern: NVMe passthrough experiments may need device permissions this account lacks |
| 24 | Chipmink: Efficient Delta Identification for Massive Object Graphs | https://doi.org/10.14778/3785297.3785303 | https://www.vldb.org/pvldb/vol19/p603-chockchowwat.pdf | https://github.com/illinoisdata/pod | storage | Delta identification and incremental persistence for large Python object graphs replacing full pickle snapshots; user-space storage and dedup work with an open artifact |
| 25 | Ken: An Execution Engine for Unstructured Database Systems | https://doi.org/10.14778/3796195.3796204 | https://www.vldb.org/pvldb/vol19/p902-kossmann.pdf | https://github.com/ferdiko/ken_submission | ml-systems | Execution engine that adapts model cascades to query load while managing GPU memory and data movement. Concern: model sizes must be kept within 24 GB |
| 26 | Aker: Density-Aware Approximate Caching for Vector Search | https://doi.org/10.14778/3828612.3828627 | https://www.vldb.org/pvldb/vol19/p2727-oh.pdf | https://github.com/sjoon-oh/aker | caching | Approximate cache for disk-based vector search with a density-adaptive hit predicate and a staleness-bounded refresh mechanism integrated into pgvector; a genuine cache admission and consistency contribution |
| 27 | SVFusion: A CPU-GPU Co-Processing Architecture for Large-Scale Real-Time Vector Search | https://doi.org/10.14778/3796195.3796216 | https://www.vldb.org/pvldb/vol19/p1074-yang.pdf | https://github.com/zjuDBSystems/svfusion | other-userspace | CPU GPU disk co-processing architecture with workload-aware GPU-memory caching and CUDA multi-stream coordination; explicitly designed around limited GPU memory so it scales to one A5000 |
| 28 | I/O Optimizations in Graph-Based Disk-Resident Approximate Nearest Neighbor Search: A Design Space Exploration | https://doi.org/10.14778/3801059.3801064 | https://www.vldb.org/pvldb/vol19/p1484-li.pdf | https://github.com/LeonLee666/IObench4DiskANN | storage | I O-first design space exploration for SSD-resident graph ANN indexes with a page-level cost model and the OctopusANN composition; an experiment-analysis paper whose whole point is storage I O behaviour |
| 29 | Bridging the Indexing Gap in Fused GPU Query Engines | https://doi.org/10.14778/3828612.3828637 | https://www.vldb.org/pvldb/vol19/p2853-bu.pdf | https://github.com/benbii/fusebmpidx | other-userspace | Fused GPU bitmap indexing that keeps intermediates in registers. Concern: evaluated on an RTX 5090 D so absolute numbers will differ on Ampere but the technique is single-GPU |
| 30 | ThunderGNN: Unlocking Tensor Cores for Graph Neural Networks | https://doi.org/10.14778/3828612.3828625 | https://www.vldb.org/pvldb/vol19/p2699-chen.pdf | https://github.com/yuang-chen/ThunderGNN-VLDB2026 | ml-systems | Sparsity-aware reordering and condensed storage to run GNN kernels on Tensor Cores; Ampere has Tensor Cores so this is reproducible on one A5000 |
| 31 | FlowLog: Efficient and Extensible Datalog via Incrementality | https://doi.org/10.14778/3778092.3778098 | https://www.vldb.org/pvldb/vol19/p361-zhao.pdf | https://github.com/flowlog-rs/FlowLog-VLDB | other-userspace | Datalog engine with a per-rule relational IR that separates recursion from logical planning; user-space Rust runtime and compiler work |
| 32 | Why Database Manuals Are Not Enough: Efficient and Reliable Configuration Tuning for DBMSs via Code-Driven LLM Agents | https://doi.org/10.14778/3797919.3797940 | https://www.vldb.org/pvldb/vol19/p1358-zhang.pdf | https://github.com/DBXAI/SysInsight | ml-for-systems | Mines knob tuning rules from DBMS source code with static analysis plus LLM reasoning; the tuning loop runs against a local PostgreSQL or MySQL |
| 33 | Scarf: Self-Adaptive Tuning via Multi-Objective Reinforcement Learning for Apache Flink | https://doi.org/10.14778/3801059.3801066 | https://www.vldb.org/pvldb/vol19/p1516-gao.pdf | https://github.com/ZJU-DAILY/Scarf | ml-for-systems | Multi-objective RL configuration tuning for Apache Flink. Concern: Flink must be run as a local multi-process cluster and throughput numbers will not match a real cluster |
| 34 | E2ETune: End-to-End Knob Tuning via Fine-tuned Generative Language Model | https://doi.org/10.14778/3773731.3773732 | https://www.vldb.org/pvldb/vol18/p5540-huang.pdf | https://github.com/RUCKBReasoning/E2ETune | ml-for-systems | Fine-tunes a generative language model to emit a whole knob configuration in one shot; Mistral-7B class models fit in 24 GB with parameter-efficient tuning |
| 35 | Efficient GNN Training on Giant Graphs with Collective Batching and Scheduling | https://doi.org/10.14778/3797919.3797927 | https://www.vldb.org/pvldb/vol19/p1184-zhang.pdf | https://github.com/initzhang/MorphGL | ml-systems | MorphGL adaptively splits mini-batch preparation between CPU and GPU on a single CPU GPU machine; explicitly a one-node system that adapts to the host CPU GPU balance |
| 36 | DOT: Dynamic Knob Selection and Online Sampling for Automated Database Tuning | https://doi.org/10.14778/3785297.3785302 | https://www.vldb.org/pvldb/vol19/p589-wang.pdf | https://github.com/Orange-OpenSource/dot | ml-for-systems | Knob importance pruning plus Bayesian optimization with no warm-up phase; runs against a local DBMS with sysbench and TPC-H |
| 37 | Libra: One-Shot Parameter Sensitivity Estimation for Transfer Learning in Database Performance Prediction | https://doi.org/10.14778/3796195.3796207 | https://www.vldb.org/pvldb/vol19/p945-nakamori.pdf | https://github.com/Tatzhiro/DBMSTransferLearning | ml-for-systems | One-shot parameter sensitivity profiles for transferring performance models across contexts. Concern: the published study spans seven hardware environments so only the released measurement data can be reused here |
| 38 | MFTune: An Efficient Multi-fidelity Framework for Spark SQL Configuration Tuning | https://doi.org/10.14778/3836663.3836715 | https://www.vldb.org/pvldb/vol19/p3649-xu.pdf | https://github.com/PKU-DAIR/MFTune | ml-for-systems | Multi-fidelity Spark SQL configuration tuning using representative query subsets as cheap proxies. Concern: Spark must run in local or pseudo-cluster mode |
| 39 | AXE: A Task Decomposition Approach to Learned LSM Tuning | https://doi.org/10.14778/3773731.3773735 | https://www.vldb.org/pvldb/vol18/p5582-huynh.pdf | https://github.com/BU-DiSC/proj_axe | ml-for-systems | Decomposes learned LSM tuning into cost-model training and a separate solver so that no database executions are needed at deployment time; artifact is a self-contained Python tuner plus RocksDB harness |
| 40 | DBAIOps: A Reasoning LLM-Enhanced Database Operation and Maintenance System using Knowledge Graphs | https://doi.org/10.14778/3797919.3797937 | https://www.vldb.org/pvldb/vol19/p1319-zhou.pdf | https://github.com/weAIDB/DBAIOps | ml-for-systems | Reasoning LLM plus knowledge graph system for database anomaly diagnosis and recovery; agent and knowledge base run in user space against a local DBMS |
| 41 | RetroInfer: A Vector Storage Engine for Scalable Long-Context LLM Inference | https://doi.org/10.14778/3796195.3796212 | https://www.vldb.org/pvldb/vol19/p1016-lu.pdf | https://github.com/microsoft/RetrievalAttention | llm-inference | Vector storage engine for sparse-attention KV cache with a GPU CPU wave buffer; the whole point is fitting long-context inference into limited GPU memory which is exactly this machine profile. Concern: paper uses an 80 GB GPU so contexts must be scaled down |
| 42 | OrbitFlow: SLO-Aware Long-Context LLM Serving with Fine-Grained KV Cache Reconfiguration | https://doi.org/10.14778/3796195.3796214 | https://www.vldb.org/pvldb/vol19/p1046-ma.pdf | https://github.com/omnia-postech/OrbitFlow | llm-inference | SLO-aware per-layer KV cache placement between GPU and host memory with an ILP solver and runtime refinement; a single-GPU serving problem |
| 43 | Efficient Cooperation-Aware Key and Value Management for LLM Inference | https://doi.org/10.14778/3819518.3819541 | https://www.vldb.org/pvldb/vol19/p2154-hu.pdf | https://github.com/ZJU-DIVER/CoKV | llm-inference | Cooperation-aware head-level KV cache budget allocation; pure inference-time memory management that runs on one GPU |
| 44 | Unified Static–Dynamic Pruning for Efficient LLM Inference | https://doi.org/10.14778/3836663.3836665 | https://www.vldb.org/pvldb/vol19/p2950-kim.pdf | https://github.com/AIDASLab/SPDP | llm-inference | Unified static and dynamic weight pruning with custom CUDA-core and Tensor-Core kernels. Concern: kernels are tuned for newer inference GPUs so Ampere performance must be re-measured |
| 45 | QStore: Quantization-Aware Compressed Model Storage | https://doi.org/10.14778/3778092.3778100 | https://www.vldb.org/pvldb/vol19/p388-li.pdf | https://github.com/illinoisdata/qstore | storage | Lossless joint storage of high and low precision model weights as base plus residual; a compression and model-storage contribution that needs no large GPU |
| 46 | PRISM: A Training System to Unlock the Potential of Temporal Graph Learning Through Staleness Avoidance | https://doi.org/10.14778/3819518.3819544 | https://www.vldb.org/pvldb/vol19/p2196-islam.pdf | https://github.com/cseduashraful/PRISM | ml-systems | Multi-versioned memory training system for temporal GNNs that removes staleness without losing GPU parallelism; single-GPU training system |
| 47 | Blaze: Compiling JSON Schema for 10x Faster Validation | https://doi.org/10.14778/3773749.3773764 | https://www.vldb.org/pvldb/vol19/p279-viotti.pdf | https://github.com/sourcemeta-research/jsonschema-benchmark | other-userspace | Ahead-of-time compilation of JSON Schema into a fast validation representation with a 10x speedup; user-space C++ compiler and runtime with a public benchmark artifact |
| 48 | Rhyme Native: Efficient Code Generation for Structured and Semi-Structured Workloads | https://doi.org/10.14778/3836663.3836717 | https://www.vldb.org/pvldb/vol19/p3676-guo.pdf | https://github.com/rhyme-lang/rhyme | other-userspace | Code generation for a declarative query language covering both relational and nested JSON workloads including a corrected loop scheduler; compiler and runtime work in user space |
| 49 | Eureka: Enabling Fine-Grained Access and Range Queries on Compressed Scientific Data via Data-Index Co-Compression | https://doi.org/10.14778/3785297.3785305 | https://www.vldb.org/pvldb/vol19/p631-wan.pdf | https://github.com/ningyan11/Eureka | storage | Data and index co-compression for scientific arrays enabling selective decompression and range queries; user-space compression plus indexing on HPC datasets |
| 50 | How to Write to SSDs | https://doi.org/10.14778/3801059.3801063 | https://www.vldb.org/pvldb/vol19/p1469-lee.pdf | https://github.com/LeeBohyun/ZLeanStore | storage | Redesigns LeanStore to write out-of-place cutting flash write amplification by up to 9.8x. Concern: the ZNS and FDP extensions need special SSD interfaces but the core out-of-place design runs on a normal file |
| 51 | Garnet: A Next-Generation Cache-Store for Accelerating Applications and Services | https://doi.org/10.14778/3773749.3773760 | https://www.vldb.org/pvldb/vol19/p224-chandramouli.pdf | https://github.com/microsoft/garnet | caching | Redis-compatible cache-store rethought for thread scalability durability and transactions; mature open-source .NET artifact that runs on one node |
| 52 | Operation-Aware Hybrid Locking for Modern In-Memory Indexes | https://doi.org/10.14778/3811243.3811253 | https://www.vldb.org/pvldb/vol19/p1804-gupta.pdf | https://github.com/rs3lab/opal | other-userspace | Operation-aware hybrid lock that picks optimistic version locking batching or MCS per operation type inside in-memory indexes; a concurrency-library contribution that suits a 32-thread machine |
| 53 | Scalable GPU Acceleration of Scalar Functions in Analytical Databases: Compilation, Benchmarking and Optimization | https://doi.org/10.14778/3801059.3801061 | https://www.vldb.org/pvldb/vol19/p1441-rajan.pdf | https://doi.org/10.6084/m9.figshare.29452214 | other-userspace | LLVM MLIR toolchain that lifts production CPU scalar function implementations into GPU kernels plus a benchmark that stresses scalar functions; single-GPU compiler work |
| 54 | Demystifying and Improving Lazy Promotion in Cache Eviction | https://doi.org/10.14778/3785297.3785299 | https://www.vldb.org/pvldb/vol19/p549-yang.pdf | https://github.com/cacheMon/Lazy-Promotions | caching | Trace-driven benchmark and improvement of five lazy-promotion cache eviction strategies plus two new algorithms; the archetypal cache-policy paper for this course and runs on libCacheSim traces |
| 55 | CrocSort: Resource-Efficient, Skew-Resilient Parallel External Merge Sort | https://doi.org/10.14778/3836663.3836667 | https://www.vldb.org/pvldb/vol19/p2978-otaki.pdf | https://github.com/rotaki/ES | other-userspace | Parallel external merge sort with explicit memory and thread configuration rules and skew-resilient range partitioning; resource-efficiency work on NVMe that fits this host |
| 56 | One Pass to Parse Them All: Fused Parallel CSV Processing | https://doi.org/10.14778/3836663.3836710 | https://www.vldb.org/pvldb/vol19/p3579-ellmann.pdf | https://github.com/ackxolotl/csveee-evaluation | other-userspace | Fused parallel CSV parsing and processing with a new vectorization and zero-copy record construction strategy; multicore user-space parsing |
| 57 | Succinct and Fast Tiny Pointer Hash Tables | https://doi.org/10.14778/3819518.3819542 | https://www.vldb.org/pvldb/vol19/p2168-tang.pdf | https://github.com/Xilinion/TinyPtr | other-userspace | Succinct and latency-oriented hash tables built on tiny pointers with dynamic resizing; a self-contained data-structure and memory-footprint contribution |
| 58 | Automated Tensor-Relational Decomposition for Large-Scale Sparse Tensor Computation | https://doi.org/10.14778/3797919.3797921 | https://www.vldb.org/pvldb/vol19/p1101-tang.pdf | https://github.com/yuxineverforever/upper-case-lower-case-einstein-notation | ml-systems | Automatic rewriting of Einstein-notation tensor computations into a tensor-relational form so sparsity is handled relationally and dense kernels do the math. Concern: the reference system targets large-scale sparse tensors so inputs must be scaled down |
| 59 | Global Hash Tables Strike Back! An Analysis of Parallel GROUP BY Aggregation | https://doi.org/10.14778/3778092.3778110 | https://www.vldb.org/pvldb/vol19/p523-marcus.pdf | https://github.com/danielxue/global-hash-tables-strike-back | other-userspace | Shows a purpose-built concurrent global hash table matches or beats partitioned GROUP BY aggregation in morsel-driven engines; a pure multicore concurrency study |
| 60 | CAPS: Cost-Aware ML Pipeline Selection | https://doi.org/10.14778/3801059.3801060 | https://www.vldb.org/pvldb/vol19/p1427-kontaxakis.pdf | https://github.com/akontaxakis/CAPS | ml-systems | Cost-aware AutoML pipeline selection that avoids wasting time and memory on doomed pipelines; user-space Python that plugs into existing AutoML frameworks |
| 61 | Morphing-based Compression for Data-centric ML Pipelines | https://doi.org/10.14778/3778092.3778104 | https://www.vldb.org/pvldb/vol19/p440-baunsgaard.pdf | https://github.com/damslab/reproducibility/tree/master/vldb2026-BWARE | ml-systems | Pushes lossless matrix compression through feature transformations in data-centric ML pipelines inside SystemDS; memory and I O reduction work that runs on CPU |
| 62 | SEMA: A High-performance System for LLM-based Semantic Query Processing | https://doi.org/10.14778/3836663.3836685 | https://www.vldb.org/pvldb/vol19/p3231-zhao.pdf | https://github.com/BITQiKangK/Sema | ml-systems | Semantic query engine built on DuckDB with adaptive execution operator fusion and prompt handling for LLM operators. Concern: end-to-end numbers depend on LLM API latency and cost |
| 63 | Active Data Lakes: Regaining Physical Data Independence Without Losing Interoperability | https://doi.org/10.14778/3797919.3797941 | https://www.vldb.org/pvldb/vol19/p1372-ginter.pdf | https://github.com/ActiveDataLake/vldb-26 | storage | Mechanisms that restore physical data independence over Parquet-based data lakes so new storage layouts can be adopted without breaking interoperability; user-space file-format and storage work |
| 64 | LakeHelm: Zero-Shot Lakehouse Advisor for Joint Engine-Format Selection and Configuration | https://doi.org/10.14778/3811243.3811250 | https://www.vldb.org/pvldb/vol19/p1768-xu.pdf | https://github.com/umich-db/LakeHelm | ml-for-systems | Zero-shot mixture-of-experts advisor that jointly picks a lakehouse engine and table format plus its configuration. Concern: reproducing the training data needs Spark Trino and Presto installations |
| 65 | Swan: Hybrid MVCC Management for Efficient Transaction Processing in LSM-Tree-Based Key-Value Stores | https://doi.org/10.14778/3819518.3819528 | https://www.vldb.org/pvldb/vol19/p1977-guo.pdf | https://github.com/LAccordeur/swan | storage | Hybrid in-memory and out-of-memory MVCC for LSM-based key-value stores with transaction-aware data separation and concurrent memtable flushing; single-node storage engine |
| 66 | LIO: A lightweight and interpretable query optimizer based on an evolutionary forest | https://doi.org/10.14778/3797919.3797920 | https://www.vldb.org/pvldb/vol19/p1088-ye.pdf | https://github.com/MaxBlack214/LIO | ml-for-systems | Lightweight interpretable learned query optimizer based on an evolutionary forest that emits hints; trains and runs entirely on one machine |
| 67 | UniTG: A Unified System for Efficient and Seamless Textual Graph Learning | https://doi.org/10.14778/3836663.3836688 | https://www.vldb.org/pvldb/vol19/p3273-liu.pdf | https://github.com/zxmeng98/TiGraph | ml-systems | Fuses the language model and GNN phases of textual graph learning into one runtime with co-designed components. Concern: larger language-model backbones may exceed 24 GB so a scaled-down backbone is needed |
| 68 | SafeLoad: Efficient Admission Control Framework for Identifying Memory-Overloading Queries in Cloud Data Warehouses | https://doi.org/10.14778/3785297.3785311 | https://www.vldb.org/pvldb/vol19/p713-li.pdf | https://github.com/SafeLoad-project/SafeBench | scheduling | Admission control that predicts memory-overloading queries and reroutes them plus a released labelled benchmark; an admission and resource-management policy learnable from the published traces |

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | SafeQL: Search-based Refinement for Safe and Efficient LLM-based Text-to-SQL | out-topic | LLM text-to-SQL generation quality |
| 2 | Dial: A Knowledge-Grounded Dialect-Specific NL2SQL System | out-topic | dialect-specific NL2SQL generation |
| 3 | NL2SQLBench: A Modular Benchmarking Framework for LLM-Enabled NL2SQL Solutions | out-topic | NL2SQL benchmarking framework |
| 4 | Developing and Benchmarking Verification Algorithms to Improve Text-to-SQL Generation | out-topic | text-to-SQL verification algorithms |
| 5 | Pervasive Annotation Errors Break Text-to-SQL Benchmarks and Leaderboards | out-topic | text-to-SQL benchmark annotation quality |
| 6 | A Comparative Evaluation of Schema Subsetting for LLM-based NL-to-SQL over Large-Schema Databases | out-topic | schema subsetting for NL2SQL prompts |
| 7 | CloudGlide: Deconstructing the Landscape of Cloud-Based Analytics | included | in scope as scheduling -- White-box discrete-event simulator for provisioning caching scheduling and pricing policies in cloud analytics |
| 8 | BtrLog: Low-Latency Logging for Cloud Database Systems | out-machine | cloud WAL service whose core design replicates log records across a quorum of remote SSD-backed log nodes and archives to object storage; needs a multi-node storage cluster |
| 9 | Bespoke OLAP: Synthesizing Workload-Specific One-size-fits-one Database Engines | included | in scope as ml-for-systems -- LLM-driven synthesis of workload-specific OLAP engines compared against DuckDB and Umbra |
| 10 | LiquidCache: Efficient Pushdown Caching for Cloud-Native Data Analytics | included | in scope as caching -- Pushdown cache layer that transcodes Parquet into a Liquid format to cut cache CPU time |
| 11 | Redbench: Workload Synthesis From Cloud Traces | out-topic | workload and benchmark generator for cloud data warehouses |
| 12 | Matryoshka: Uncovering Relevant Features in Data Lakes to Enhance Machine Learning Applications | out-topic | feature discovery in data lakes for ML |
| 13 | FedAugment: Table Augmentation Search over Decentralized Data Repositories | out-topic | federated table augmentation search |
| 14 | MosaicJoin: Compact Semantic Sketches for Value-Level Join Discovery | out-topic | value-level join discovery over data lakes |
| 15 | IncreQueryFusion: On-demand Data Fusion Framework in Dynamic Data Lakes | out-topic | on-demand data fusion in data lakes |
| 16 | Discovering Approximate Denial Constraints in Large Databases | out-topic | denial constraint discovery |
| 17 | BaCon: Efficient Batch Processing of Counting Queries | out-topic | batch counting query algorithms |
| 18 | Finding Non-Redundant Simpson's Paradox in Multidimensional Data | out-topic | statistical pattern discovery in multidimensional data |
| 19 | Scalable Grid-based Computation of Kendall's Tau Correlation | out-topic | correlation computation algorithm |
| 20 | Optimal Approximate Matrix Multiplication over Sliding Windows | out-topic | sliding window matrix sketching theory |
| 21 | ConRAD: Conformal Risk-Aware Neural Databases | out-topic | conformal risk control for neural databases |
| 22 | A Resource-centric Analysis and Optimization of NoSQL Workloads using Distressed Resource Volume Metric | included | in scope as scheduling -- Open-sourced Cosmos DB replica traces plus the LoadStar policy simulator for packing and migration |
| 23 | Shard: A Scalable and Resize-optimized Hash Index on Disaggregated Memory | out-machine | hash index designed for RDMA disaggregated memory which this single machine has no equivalent of |
| 24 | CIDER: Boosting Memory-Disaggregated Key-Value Stores with Pessimistic Synchronization | out-machine | memory-disaggregated key-value store whose synchronization design targets RDMA one-sided verbs |
| 25 | Efficient, Scalable, and Fair Locking on Disaggregated Memory with Decentralized Coordination | out-machine | lock design for RDMA disaggregated memory with decentralized coordination |
| 26 | Breaking the Isolation-Freshness Trade-off: Joint Adaptive Storage Optimization for HTAP Systems | included | in scope as storage -- Adaptive row and column storage layout selection for HTAP implemented in TiDB |
| 27 | TVA: A Version-aware Temporal Graph Storage System for Real-time Analytics | included | in scope as storage -- Multi-version temporal graph storage engine with custom hashing and version metadata layout |
| 28 | Kirin: Efficient In-Storage Learned Compaction for LSM-Trees via System-Algorithm Co-Design | out-machine | learned compaction offloaded to a computational storage device; evaluated on DaisyPlus OpenSSD hardware that is not available |
| 29 | Sampling-based Predictive Database Buffer Management | included | in scope as caching -- Sampling-based predictive buffer replacement evaluated both by simulation on Redshift traces and by patching PostgreSQL |
| 30 | Aquila: A High-Concurrency System for Incremental Graph Query | out-topic | incremental graph pattern query processing |
| 31 | CEMR: An Effective Subgraph Matching Algorithm with Redundant Extension Elimination | out-topic | subgraph matching algorithm |
| 32 | Efficient Temporal Subgraph Management: A New Interval Index | out-topic | temporal subgraph interval index |
| 33 | TRIM: An Efficient Framework for Exact Eccentricity Computation on Large-Scale Graphs | out-topic | graph eccentricity computation |
| 34 | GPU-Accelerated 𝜂-threshold Decomposition for Uncertain Graphs | out-topic | uncertain graph decomposition algorithm |
| 35 | Characterizing Parallel Subgraph Matching Performance: A Systematic Study of Interactions, Scalability, and Enumeration | out-topic | parallel subgraph matching performance study |
| 36 | Balancing the Blend: An Experimental Analysis of Trade-offs in Hybrid Search | out-topic | hybrid search quality trade-off study |
| 37 | RT-RkNN: Reverse k Nearest Neighbor Queries as a Graphics Ray Casting Problem | out-topic | reverse k nearest neighbour query algorithm |
| 38 | Harmonizing Efficiency and Accuracy in Filtered Vector Search | out-topic | filtered vector search index algorithm |
| 39 | CGIF: Combining Proximity Graphs and Inverted Files for Efficient Filtered Vector Search over Arbitrary Predicates | out-topic | filtered vector search index algorithm |
| 40 | Elastic Index Selection for Label-Hybrid AKNN Search | out-topic | index selection for label-hybrid ANN search |
| 41 | ANNiE: A Learned Query Cost Estimator for Graph-Based Approximate Nearest Neighbor Search | out-topic | learned cost model for ANN search parameters; vector index search tuning rather than an OS-level resource mechanism |
| 42 | An Experimental Evaluation of Hybrid Querying on Vectors | out-topic | experimental evaluation of hybrid vector querying |
| 43 | Revisiting Filtered ANN Benchmarks: A Hardness-Controlled Benchmark Generator for Realistic Evaluation | out-topic | filtered ANN benchmark generator |
| 44 | LiBox: A Learned Index as an Array to Minimize Last-Mile Search | included | in scope as ml-for-systems -- Learned index that reduces last-mile search to a single SIMD step. Concern: the key mechanism uses an AVX-512 instruction and this Zen 3 Threadripper has no AVX-512 so the headline result cannot be reproduced without an AVX2 fallback |
| 45 | Rethinking Learned Index and LSM-tree Integration | included | in scope as ml-for-systems -- Wild Turkey integrates learned indexes into LSM-trees with an RL controller for SSTable sizing and error bounds |
| 46 | Learned Static Function Data Structures | included | in scope as ml-for-systems -- Learned static function data structures that use per-key predicted distributions to beat the zero-order entropy bound |
| 47 | STEM2: A Fast and Space-efficient Data Structure for Exact Multi-Set Membership Query | out-topic | multi-set membership data structure |
| 48 | Index Intersection for High-Dimensional Range Queries | out-topic | high-dimensional range query index |
| 49 | An Evaluation of N-Gram Selection Strategies for Regular Expression Indexing in Contemporary Text Analysis Tasks | out-topic | n-gram selection for regular expression indexing |
| 50 | GPU-Accelerated ANNS: Quantized for Speed, Built for Change | out-topic | GPU ANN index construction and quantization algorithm |
| 51 | GPU-Native Approximate Nearest Neighbor Search with IVF-RaBitQ: Fast Index Build and Search | out-topic | GPU ANN index construction and quantization algorithm |
| 52 | JHQ: Johnson-Lindenstrauss Enhanced Hierarchical Quantization for High-Dimensional Approximate Nearest Neighbor Search | out-topic | hierarchical quantization algorithm for ANN |
| 53 | ConANN: Conformal Approximate Nearest Neighbor Search | out-topic | conformal prediction for ANN search |
| 54 | Bolt-on, Verifiable Provenance for LLM-Powered Data Processing | out-topic | verifiable provenance for LLM data processing |
| 55 | V3DB: Audit-on-Demand Zero-Knowledge Proofs for Verifiable Vector Search over Committed Snapshots | out-topic | zero-knowledge proofs for vector search |
| 56 | Database Views as Explanations for Relational Deep Learning | out-topic | explanations for relational deep learning |
| 57 | Toward Temporal Attribution Analytics in Dataflows | out-topic | vision paper on temporal attribution analytics |
| 58 | Dinkel: State-Aware and Granular Framework for Validating Graph Databases | out-topic | graph database validation and fuzzing |
| 59 | Mil: Cost-guided Minimum Makespan Scheduling for Applications of Multiple LLMs | included | in scope as scheduling -- Makespan scheduling for offline multi-LLM applications with an inference simulator and processing-rate estimators. Concern: GPU allocation and parallelism selection assume several GPUs so only the simulator and a single-GPU scaled-down setting are reproducible |
| 60 | DeepPrep: An LLM-Powered Agentic System for Autonomous Data Preparation | out-topic | LLM agent for data preparation |
| 61 | BRIEF: Bi-level Coreset Selection for Efficient Instruction Tuning in LLMs | out-topic | coreset selection for LLM instruction tuning |
| 62 | Data-efficient Online Training for Direct Alignment in LLMs | out-topic | online data selection for LLM alignment |
| 63 | Resilience-Aware Elastic Scaling for Cloud-Native Online DL Training on Multi-Tenant GPU Clusters | out-machine | elastic scaling and GPU leasing across multi-tenant GPU clusters |
| 64 | Efficient Banzhaf-Based Data Valuation for $k$-Nearest Neighbors Classification | out-topic | data valuation algorithm |
| 65 | CaSh: Shapley Value Computation with Cache Optimization | out-topic | memoization for Shapley value approximation |
| 66 | CLaP - State Detection from Time Series | out-topic | time series state detection |
| 67 | CounterSnake: A lossless and generalized compression framework for diverse sketches | out-topic | sketch counter compression for stream analytics |
| 68 | KDSelector: A Framework of Knowledge-Enhanced and Data-Efficient Selector Learning for Anomaly Detection Model Selection in Time Series | out-topic | anomaly detection model selection |
| 69 | FB*: A Compact Index for Efficient and Exact Density-based Clustering | out-topic | density-based clustering index |
| 70 | DeXOR: Enabling XOR in Decimal Space for Streaming Lossless Compression of Floating-point Data | included | in scope as storage -- Streaming lossless floating-point compression framework |
| 71 | Continuous Query for Top-K Maximal Sum Intervals over Streaming Data | out-topic | streaming top-k interval queries |
| 72 | PILOT-C: Physics-Informed Low-Distortion Optimal Trajectory Compression | out-topic | physics-informed trajectory compression |
| 73 | A Topology-Aware Localized Update Strategy for Graph-Based ANN Index | out-topic | localized update strategy for ANN graph indexes |
| 74 | Unveiling Challenges for LLMs in Enterprise Data Engineering | out-topic | evaluation of LLMs on enterprise data engineering tasks |
| 75 | LLMs as Stratification Signals for KG Accuracy Evaluation | out-topic | LLM-based knowledge graph accuracy evaluation |
| 76 | Auto-Fill: Learning to Predict Missing Values Accurately with Specialist Language Models | out-topic | missing value prediction with language models |
| 77 | Accelerating String-Heavy Queries with LLM Token Tables | included | in scope as storage -- Reuses an LLM tokenizer as a global string symbol table so joins and aggregations run on encoded data. Concern: implemented inside Umbra which is not open source although the authors released a token-table artifact repo |
| 78 | Schuyler: Self-Supervised Clustering of Tables in Relational Databases | out-topic | self-supervised clustering of database tables |
| 79 | Replacing Multi-Step Assembly of Data Preparation Pipelines with One-Step LLM Pipeline Generation for Table QA | out-topic | one-step LLM pipeline generation for table QA |
| 80 | Human-Centered Exploration of Table Unionability | out-topic | human-centred study of table unionability |
| 81 | SciTables : A Dataset and Evaluation Framework for Complex Table-to-Text Generation | out-topic | table-to-text dataset and evaluation |
| 82 | Vodka: Rethink Benchmarking Philosophy in HTAP Systems | out-topic | HTAP benchmarking methodology |
| 83 | TPCx-AI under the Microscope: A Benchmarking Debt Analysis | out-topic | TPCx-AI benchmarking debt analysis |
| 84 | SQL-Exchange: Transforming SQL Queries Across Domains | out-topic | cross-domain SQL query transformation |
| 85 | RAGPerf: An End-to-End Benchmarking Framework for Retrieval-Augmented Generation Systems | included | in scope as llm-inference -- End-to-end RAG serving benchmark that measures throughput host and GPU memory and CPU GPU utilization across vector stores and LLMs |
| 86 | Benchmarking the Full Pipeline of Materialized-View-Based Query Rewriting | out-topic | materialized view rewriting benchmark |
| 87 | Near-Duplicate Text Alignment under Weighted Jaccard Similarity | out-topic | weighted Jaccard text alignment algorithm |
| 88 | Featurized-Decomposition Join: Low-Cost Semantic Joins with Guarantees | out-topic | semantic join algorithm |
| 89 | SeDA: Bridging the Gap between Efficient Syntactic and Precise Semantic Search of Similar Passages in Large Text Corpora | out-topic | similar passage search method |
| 90 | Can we trust LLM Self-Explanations for Entity Resolution? | out-topic | study of LLM self-explanations for entity resolution |
| 91 | Terark-DS: A High-Performance and Storage-Efficient Key-Value Separation Storage Engine on Disaggregated Storage | out-machine | key-value separation engine whose differentiated redundancy adaptive WAL and network-efficient GC are all designed for compute-storage disaggregation over a network |
| 92 | ArceKV: Towards Workload-driven LSM-compactions for Key-Value Store Under Dynamic Workloads | included | in scope as storage -- Workload-driven LSM compaction decision engine implemented on top of RocksDB |
| 93 | Dynamic read & write optimization with TurtleKV | included | in scope as storage -- New on-disk read write balanced TurtleTree structure with explicit write-memory tuning knobs evaluated with YCSB |
| 94 | How Much Can RocksDB Chew? Achieving Near-Zero Write Stalls with Sustainable RocksDB | included | in scope as storage -- Reframes RocksDB write stalls as a control problem and adds an online RL admission controller |
| 95 | Tidehunter: Large-Value Storage With Minimal Data Relocation | included | in scope as storage -- WAL-as-permanent-storage key-value engine with lock-free writes on NVMe |
| 96 | gMatch: Fine-Grained and Hardware-Efficient Subgraph Matching on GPUs | out-topic | GPU subgraph matching algorithm |
| 97 | Effective Durable Community Search in Large Temporal Graph | out-topic | durable community search in temporal graphs |
| 98 | Efficient Partition-based Approaches for Diversified Top-k Subgraph Matching | out-topic | diversified top-k subgraph matching |
| 99 | Mix & Match: Subgraph Matching for Absolute Coverage | out-topic | subgraph matching for coverage |
| 100 | Subgraph Enumeration: Beyond Tree Decomposition | out-topic | subgraph enumeration theory |
| 101 | Abacus: A Cost-Based Optimizer for Semantic Operator Systems | included | in scope as ml-systems -- Cost-based optimizer for LLM-powered semantic operator pipelines released inside the Palimpzest system. Concern: optimization quality depends on LLM API cost and non-determinism |
| 102 | ReSequel: Robust LLM-assisted Query Rewriting and Optimization using Templatization and Sampling | out-topic | LLM-assisted query rewriting |
| 103 | SemBench: A Benchmark for Semantic Query Processing Engines | out-topic | benchmark for semantic query processing engines |
| 104 | ELT-Bench: An End-to-End Benchmark for Evaluating AI Agents on ELT Pipelines | out-topic | benchmark for AI agents on ELT pipelines |
| 105 | stratum: A System Infrastructure for Massive Agent-Centric ML Workloads | included | in scope as ml-systems -- Vision paper proposing a runtime for executing thousands of agent-generated Python ML pipelines |
| 106 | OBELISK: Efficient Offline Query Planning with Bayesian Optimization-Informed Language Model Reasoning | out-topic | LLM reasoning for offline query planning |
| 107 | TATA: An Efficient Framework for Task Transfer in Query Plan Representation | out-topic | task transfer for query plan representation learning |
| 108 | Graph Transformers for Query Plan Representation: Potentials and Challenges | out-topic | graph transformer study for query plan representation |
| 109 | AQD: Online Adaptive Query Dispatcher for HTAP Databases | included | in scope as ml-for-systems -- Learned online query dispatcher that routes queries between row and column engines with low latency. Concern: needs an HTAP dual-engine deployment |
| 110 | QDBO: A Real-time Quantum-augmented Database System Optimizer | out-machine | requires a quantum annealer for the core sampling step |
| 111 | Tux: Efficient Drop-in Networking for Database Systems | out-machine | kernel-bypass network stack built on eBPF and XDP which are disabled for unprivileged users on this host |
| 112 | dpKernels: Harvesting DPU Compute Resources for Data-path Efficiency in Cloud Data Processing | out-machine | harvests DPU compute resources; requires SmartNIC or DPU hardware |
| 113 | MGI: A Communication Framework for Data Processing in Massive GPU Infrastructures | out-machine | communication framework for massive multi-GPU infrastructures |
| 114 | RayDB: Building Databases with Ray Tracing Cores | included | in scope as other-userspace -- Query engine that maps operator pipelines onto GPU ray-tracing cores via OptiX |
| 115 | High-Performance DBMSs with io_uring: When and How to Use It | included | in scope as storage -- Systematic study of io_uring in a buffer manager and in network shuffling with concrete design guidelines |
| 116 | Analyzing Near-Network Hardware Acceleration with Co-Processing on DPUs | out-machine | near-network acceleration study requiring DPU hardware |
| 117 | Repairing Property Graphs under PG-Constraints | out-topic | property graph repair under constraints |
| 118 | A Unified Query Planning Framework for Conjunctive Regular Path Queries | out-topic | regular path query planning |
| 119 | Structural Normalization of Property Graphs | out-topic | structural normalization of property graphs |
| 120 | Sankofa: Online Query-adaptive Dynamic Graph Summaries | out-topic | query-adaptive graph summarization |
| 121 | Chipmink: Efficient Delta Identification for Massive Object Graphs | included | in scope as storage -- Delta identification and incremental persistence for large Python object graphs replacing full pickle snapshots |
| 122 | TurboLynx: Schemaless Graph Engine Strikes Back for General-Purpose Analytics | out-topic | schemaless graph analytics engine |
| 123 | Document-to-Database: Extraction Meets Relational Semantics | out-topic | extraction from documents into relational schemas |
| 124 | QA-GraphRAG: Query-Adaptive Plug-and-Play Retrieval Integration for Graph-based Retrieval-Augmented Generation | out-topic | query-adaptive graph RAG retrieval method |
| 125 | TACO: A Benchmark for Open-Domain Text-to-SQL with Ambiguous and Cross-Database Queries | out-topic | open-domain text-to-SQL benchmark |
| 126 | In-depth Analysis of Graph-based RAG in a Unified Framework | out-topic | analysis of graph-based RAG quality |
| 127 | BookRAG: A Hierarchical Structure-aware Index-based Approach for Retrieval-Augmented Generation on Complex Documents | out-topic | hierarchical RAG index for documents |
| 128 | MGRAG: Semantic Subgraph Matching and Graph-Aware Caching for Multimodal Retrieval-Augmented Generation | out-topic | multimodal graph RAG retrieval quality; the caching component is secondary to retrieval accuracy |
| 129 | OpenSQL: Data-Efficient Text-to-SQL for Open-Source LLMs via Synthesized Intermediate Supervision | out-topic | data-efficient text-to-SQL training for open-source LLMs |
| 130 | PrepBench: How Far Are We from Natural-Language-Driven Data Preparation? | out-topic | benchmark for natural-language-driven data preparation |
| 131 | Quantization Meets Projection: A Happy Marriage for Approximate k-Nearest Neighbor Search | out-topic | projection plus quantization algorithm for ANN |
| 132 | RNSG: A Range-Aware Graph Index for Efficient Range-Filtered Approximate Nearest Neighbor Search | out-topic | range-filtered ANN graph index |
| 133 | HEXA: A Disjoint-Subgraph-Based Indexing Framework for Approximate Nearest Neighbor Search at Billion Scale | out-topic | disjoint subgraph ANN indexing framework |
| 134 | GAS: A Lightweight Framework for Filtered Search over Wide-table Vectors | out-topic | filtered search over wide-table vectors |
| 135 | Revisiting Task-Oriented Dataset Search in the Era of Large Language Models: Challenges, Benchmark, and Solution | out-topic | dataset search benchmark and solution |
| 136 | Relational Deep Dive: Error-Aware Queries Over Unstructured Data | out-topic | error-aware extraction over unstructured data |
| 137 | Ken: An Execution Engine for Unstructured Database Systems | included | in scope as ml-systems -- Execution engine that adapts model cascades to query load while managing GPU memory and data movement. Concern: model sizes must be kept within 24 GB |
| 138 | Multi-Objective Agentic Rewrites for Unstructured Data Processing | out-topic | agentic rewrite optimization for LLM pipeline accuracy |
| 139 | RED-ANNS: An RDMA-Enabled Distributed Framework for Graph-Based Approximate Nearest Neighbor Search | out-machine | distributed ANN framework whose core design is RDMA-enabled |
| 140 | Computing Why-Provenance for Property Graph Queries | out-topic | why-provenance for property graph queries |
| 141 | CONDA: A Connectivity-Aware Dynamic Index for Approximate Nearest Neighbor Search over Evolving Data | out-topic | dynamic ANN index for evolving data |
| 142 | Aker: Density-Aware Approximate Caching for Vector Search | included | in scope as caching -- Approximate cache for disk-based vector search with a density-adaptive hit predicate and a staleness-bounded refresh mechanism integrated into pgvector |
| 143 | PAIL: Efficient kNN Search on Set-Valued Attributes | out-topic | kNN search over set-valued attributes |
| 144 | QBAT: Model-based Query Budget Autotuner for Clustering-based Approximate Nearest Neighbor Search | out-topic | query budget autotuning for clustering-based ANN search |
| 145 | SVFusion: A CPU-GPU Co-Processing Architecture for Large-Scale Real-Time Vector Search | included | in scope as other-userspace -- CPU GPU disk co-processing architecture with workload-aware GPU-memory caching and CUDA multi-stream coordination |
| 146 | I/O Optimizations in Graph-Based Disk-Resident Approximate Nearest Neighbor Search: A Design Space Exploration | included | in scope as storage -- I O-first design space exploration for SSD-resident graph ANN indexes with a page-level cost model and the OctopusANN composition |
| 147 | GPU Acceleration of SQL Analytics on Compressed Data | out-no-code | no PVLDB artifact availability statement in the paper and no public repository found; the prototype extends the closed-source Microsoft TQP engine |
| 148 | PystachIO: Efficient Distributed GPU Query Processing with PyTorch over Fast Networks & Fast Storage | out-machine | distributed GPU query processing over RDMA networks and multi-node NVMe storage |
| 149 | Bridging the Indexing Gap in Fused GPU Query Engines | included | in scope as other-userspace -- Fused GPU bitmap indexing that keeps intermediates in registers. Concern: evaluated on an RTX 5090 D so absolute numbers will differ on Ampere but the technique is single-GPU |
| 150 | ThunderGNN: Unlocking Tensor Cores for Graph Neural Networks | included | in scope as ml-systems -- Sparsity-aware reordering and condensed storage to run GNN kernels on Tensor Cores |
| 151 | Terabyte-Scale Analytics in the Blink of an Eye | out-machine | explicitly targets distributed clusters of GPUs with group communication primitives |
| 152 | Hybrid Mixed Integer Linear Programming for Large-Scale Join Order Optimisation | out-topic | MILP formulation for join order optimization |
| 153 | One Join Order Does Not Fit All: Reducing Intermediate Results with Per-Split Query Plans | out-topic | per-split join plan optimization |
| 154 | FlowLog: Efficient and Extensible Datalog via Incrementality | included | in scope as other-userspace -- Datalog engine with a per-rule relational IR that separates recursion from logical planning |
| 155 | Robust Predicate Transfer with Dynamic Execution | out-topic | predicate transfer and Bloom filter optimization |
| 156 | Window Function Optimization: Co-Evaluation and Other Techniques | out-topic | window function optimization |
| 157 | BBC: Improving Large-𝑘 Approximate Nearest Neighbor Search with a Bucket-based Result Collector | out-topic | result collector for large-k ANN search |
| 158 | Toward Drift-Aware Database Benchmarking | out-topic | vision paper on drift-aware benchmarking |
| 159 | Storage-Centric Relation Design via High-Quality Approximate Functional Dependencies | out-topic | relational schema design with approximate functional dependencies |
| 160 | Why Database Manuals Are Not Enough: Efficient and Reliable Configuration Tuning for DBMSs via Code-Driven LLM Agents | included | in scope as ml-for-systems -- Mines knob tuning rules from DBMS source code with static analysis plus LLM reasoning |
| 161 | Scarf: Self-Adaptive Tuning via Multi-Objective Reinforcement Learning for Apache Flink | included | in scope as ml-for-systems -- Multi-objective RL configuration tuning for Apache Flink. Concern: Flink must be run as a local multi-process cluster and throughput numbers will not match a real cluster |
| 162 | Detecting Data-Type-Related Logic Bugs in Relational DBMSs via Compatible Database Construction | out-topic | logic bug detection in relational DBMSs |
| 163 | E2ETune: End-to-End Knob Tuning via Fine-tuned Generative Language Model | included | in scope as ml-for-systems -- Fine-tunes a generative language model to emit a whole knob configuration in one shot |
| 164 | A Practical Sublinear Approximation for Group Steiner Tree | out-topic | group Steiner tree approximation |
| 165 | Theoretically and Practically Efficient Resistance Distance Computation on Large Graphs | out-topic | resistance distance computation on graphs |
| 166 | Efficient Locally h-Clique Densest Subgraph Discovery via Divide-and-Conquer | out-topic | densest subgraph discovery algorithm |
| 167 | Efficient Hyper-truss Decomposition over Hypergraphs | out-topic | hypergraph truss decomposition |
| 168 | Anchored Maximum Communities over Large Directed Graphs | out-topic | community search in directed graphs |
| 169 | MDS-FSM: Coverage-Based Frequent Subgraph Mining in Single Graphs | out-topic | frequent subgraph mining |
| 170 | Breaking Structural Isolation: Scalable Graph Clustering via Community-Aware Sampling and Structural Entropy | out-topic | graph clustering via structural entropy |
| 171 | Sparse Neighborhood Graph-Based Approximate Nearest Neighbor Search Revisited: Theoretical Analysis and Optimization | out-topic | theoretical analysis of sparse neighbourhood ANN graphs |
| 172 | Efficient GNN Training on Giant Graphs with Collective Batching and Scheduling | included | in scope as ml-systems -- MorphGL adaptively splits mini-batch preparation between CPU and GPU on a single CPU GPU machine |
| 173 | FeLoG: Scalable and Efficient Distributed Graph Embedding with Feedback Loop Mechanism | out-machine | distributed graph embedding across a cluster |
| 174 | Resource-Efficient FirmCore Decomposition on Billion-scale Multilayer Graphs | out-topic | FirmCore decomposition on multilayer graphs |
| 175 | Scalable GNN Explanations with Distributed Shapley Values | out-machine | distributed Shapley value computation for GNN explanations |
| 176 | DOT: Dynamic Knob Selection and Online Sampling for Automated Database Tuning | included | in scope as ml-for-systems -- Knob importance pruning plus Bayesian optimization with no warm-up phase |
| 177 | Libra: One-Shot Parameter Sensitivity Estimation for Transfer Learning in Database Performance Prediction | included | in scope as ml-for-systems -- One-shot parameter sensitivity profiles for transferring performance models across contexts. Concern: the published study spans seven hardware environments so only the released measurement data can be reused here |
| 178 | MFTune: An Efficient Multi-fidelity Framework for Spark SQL Configuration Tuning | included | in scope as ml-for-systems -- Multi-fidelity Spark SQL configuration tuning using representative query subsets as cheap proxies. Concern: Spark must run in local or pseudo-cluster mode |
| 179 | AXE: A Task Decomposition Approach to Learned LSM Tuning | included | in scope as ml-for-systems -- Decomposes learned LSM tuning into cost-model training and a separate solver so that no database executions are needed at deployment time |
| 180 | DBAIOps: A Reasoning LLM-Enhanced Database Operation and Maintenance System using Knowledge Graphs | included | in scope as ml-for-systems -- Reasoning LLM plus knowledge graph system for database anomaly diagnosis and recovery |
| 181 | RetroInfer: A Vector Storage Engine for Scalable Long-Context LLM Inference | included | in scope as llm-inference -- Vector storage engine for sparse-attention KV cache with a GPU CPU wave buffer |
| 182 | OrbitFlow: SLO-Aware Long-Context LLM Serving with Fine-Grained KV Cache Reconfiguration | included | in scope as llm-inference -- SLO-aware per-layer KV cache placement between GPU and host memory with an ILP solver and runtime refinement |
| 183 | Efficient Cooperation-Aware Key and Value Management for LLM Inference | included | in scope as llm-inference -- Cooperation-aware head-level KV cache budget allocation |
| 184 | Unified Static–Dynamic Pruning for Efficient LLM Inference | included | in scope as llm-inference -- Unified static and dynamic weight pruning with custom CUDA-core and Tensor-Core kernels. Concern: kernels are tuned for newer inference GPUs so Ampere performance must be re-measured |
| 185 | Compass: SLO-aware Query Planner for Compound AI Serving at Scale | out-machine | compound AI query planner that places operators across cloud and edge infrastructure tiers with heterogeneous devices; inherently multi-node |
| 186 | QStore: Quantization-Aware Compressed Model Storage | included | in scope as storage -- Lossless joint storage of high and low precision model weights as base plus residual |
| 187 | TIMEST: Temporal Information Motif Estimator Using Sampling Trees | out-topic | temporal motif estimation algorithm |
| 188 | Mayura: Exploiting Similarities in Motifs for Temporal Co-Mining | out-topic | temporal motif co-mining |
| 189 | Worst-Case Optimal BGPs on Temporal Graphs | out-topic | worst-case optimal joins on temporal graphs |
| 190 | PRISM: A Training System to Unlock the Potential of Temporal Graph Learning Through Staleness Avoidance | included | in scope as ml-systems -- Multi-versioned memory training system for temporal GNNs that removes staleness without losing GPU parallelism |
| 191 | AGIS: Fast Approximate Graph Pattern Mining with Structure-Informed Sampling | out-topic | approximate graph pattern mining |
| 192 | Secure Join Operations in Multi-Identifier Databases: Performance and Practicality | out-topic | secure multi-identifier join operations |
| 193 | Secure Multi-Party Sampling over Joins | out-topic | secure multi-party sampling over joins |
| 194 | Enabling Index-free Adjacency in Oblivious Graph Processing with Delayed Duplications | out-topic | oblivious graph processing |
| 195 | SACK: Shielding Dynamic Attribute-based Access Control in Persistent Key-Value Stores | out-machine | shielded access control built on Intel SGX which this AMD machine does not provide |
| 196 | Blaze: Compiling JSON Schema for 10x Faster Validation | included | in scope as other-userspace -- Ahead-of-time compilation of JSON Schema into a fast validation representation with a 10x speedup |
| 197 | Streaming Validation of JSON Documents Against Schemas | out-topic | streaming JSON validation algorithms and complexity |
| 198 | Rhyme Native: Efficient Code Generation for Structured and Semi-Structured Workloads | included | in scope as other-userspace -- Code generation for a declarative query language covering both relational and nested JSON workloads including a corrected loop scheduler |
| 199 | Craw: A Unified and Efficient Querying Framework for Large-Scale Video Datasets | out-topic | multi-level video query framework |
| 200 | Eureka: Enabling Fine-Grained Access and Range Queries on Compressed Scientific Data via Data-Index Co-Compression | included | in scope as storage -- Data and index co-compression for scientific arrays enabling selective decompression and range queries |
| 201 | How to Write to SSDs | included | in scope as storage -- Redesigns LeanStore to write out-of-place cutting flash write amplification by up to 9.8x. Concern: the ZNS and FDP extensions need special SSD interfaces but the core out-of-place design runs on a normal file |
| 202 | Garnet: A Next-Generation Cache-Store for Accelerating Applications and Services | included | in scope as caching -- Redis-compatible cache-store rethought for thread scalability durability and transactions |
| 203 | SIDLE: Tree-structure Aware Indexes for CXL-based Heterogeneous Memory | out-machine | index placement designed for CXL-based heterogeneous memory |
| 204 | Operation-Aware Hybrid Locking for Modern In-Memory Indexes | included | in scope as other-userspace -- Operation-aware hybrid lock that picks optimistic version locking batching or MCS per operation type inside in-memory indexes |
| 205 | Scalable GPU Acceleration of Scalar Functions in Analytical Databases: Compilation, Benchmarking and Optimization | included | in scope as other-userspace -- LLVM MLIR toolchain that lifts production CPU scalar function implementations into GPU kernels plus a benchmark that stresses scalar functions |
| 206 | Demystifying and Improving Lazy Promotion in Cache Eviction | included | in scope as caching -- Trace-driven benchmark and improvement of five lazy-promotion cache eviction strategies plus two new algorithms |
| 207 | CrocSort: Resource-Efficient, Skew-Resilient Parallel External Merge Sort | included | in scope as other-userspace -- Parallel external merge sort with explicit memory and thread configuration rules and skew-resilient range partitioning |
| 208 | One Pass to Parse Them All: Fused Parallel CSV Processing | included | in scope as other-userspace -- Fused parallel CSV parsing and processing with a new vectorization and zero-copy record construction strategy |
| 209 | Succinct and Fast Tiny Pointer Hash Tables | included | in scope as other-userspace -- Succinct and latency-oriented hash tables built on tiny pointers with dynamic resizing |
| 210 | Automated Tensor-Relational Decomposition for Large-Scale Sparse Tensor Computation | included | in scope as ml-systems -- Automatic rewriting of Einstein-notation tensor computations into a tensor-relational form so sparsity is handled relationally and dense kernels do the math. Concern: the reference system targets large-scale sparse tensors so inputs must be scaled down |
| 211 | Global Hash Tables Strike Back! An Analysis of Parallel GROUP BY Aggregation | included | in scope as other-userspace -- Shows a purpose-built concurrent global hash table matches or beats partitioned GROUP BY aggregation in morsel-driven engines |
| 212 | CAPS: Cost-Aware ML Pipeline Selection | included | in scope as ml-systems -- Cost-aware AutoML pipeline selection that avoids wasting time and memory on doomed pipelines |
| 213 | Stress-Testing ML Pipelines with Adversarial Data Corruption | out-topic | adversarial data corruption for ML pipeline robustness |
| 214 | PipeLens: Identifying Interventions for Resolving Malfunctioning Data Science Pipelines | out-topic | debugging malfunctioning data science pipelines |
| 215 | Local Shapley: Model-Induced Locality and Optimal Reuse in Data Valuation | out-topic | data valuation with model-induced locality |
| 216 | Morphing-based Compression for Data-centric ML Pipelines | included | in scope as ml-systems -- Pushes lossless matrix compression through feature transformations in data-centric ML pipelines inside SystemDS |
| 217 | Fault Lines: Benchmarking the Impact of Label Data Quality on ML Robustness and Fairness | out-topic | benchmark on label data quality effects |
| 218 | Efficient GPU-Accelerated Adaptive Minimum Cost Seed Selection | out-topic | GPU seed selection algorithm for influence maximization |
| 219 | Efficient GPU-Accelerated Local Subgraph Counting | out-topic | GPU local subgraph counting algorithm |
| 220 | Augmenting Social Influence of Uncertain Seeds via Probabilistic Link Insertion | out-topic | social influence augmentation via link insertion |
| 221 | Counting HyperGraphlets via Color Coding: a Quadratic Barrier and How to Break It | out-topic | hypergraphlet counting algorithm |
| 222 | X-Wim: Massive Parallelization of Weighted Matching in Bipartite Graphs | out-topic | parallel weighted bipartite matching algorithm |
| 223 | Cleaning both Data Errors and Inaccurate Constraints on Numerical Sequential Data | out-topic | data and constraint cleaning for sequential data |
| 224 | SQL-Factory: A Multi-Agent Framework for High-Quality and Large-Scale SQL Generation | out-topic | multi-agent SQL corpus generation |
| 225 | LLM-AutoDP: Automatic Data Processing via LLM Agents for Model Fine-tuning | out-topic | LLM agents for fine-tuning data processing |
| 226 | SEMA: A High-performance System for LLM-based Semantic Query Processing | included | in scope as ml-systems -- Semantic query engine built on DuckDB with adaptive execution operator fusion and prompt handling for LLM operators. Concern: end-to-end numbers depend on LLM API latency and cost |
| 227 | Unstructured Data Analysis using LLMs: A Comprehensive Benchmark | out-topic | benchmark of LLM unstructured data analysis |
| 228 | ALER: An Active Learning Hybrid System for Efficient Entity Resolution | out-topic | active learning for entity resolution |
| 229 | LEAD: Iterative Data Selection for Efficient LLM Instruction Tuning | out-topic | data selection for LLM instruction tuning |
| 230 | Doppio: Communication-Efficient and Secure Multi-Party Shuffle Differential Privacy | out-topic | secure multi-party shuffle differential privacy |
| 231 | Bifrost: A Much Simpler Secure Two-Party Data Join Protocol for Secure Data Analytics | out-topic | secure two-party join protocol |
| 232 | PrivSTD: Differentially Private Spatio-temporal Trajectory Density Data Publication | out-topic | differentially private trajectory publication |
| 233 | Efficient and Secure Range Counting over Distributed Geographic Data with Query Range Protection | out-topic | secure range counting over distributed geographic data |
| 234 | Highly-Efficient Large-Scale k-means with Individual Fairness | out-topic | fair k-means clustering algorithm |
| 235 | A Workload-Aware Encrypted Index for Efficient Privacy-Preserving Range Queries | out-topic | encrypted index for private range queries |
| 236 | I-Rex: An Interactive Debugger for SQL | out-topic | interactive SQL debugger |
| 237 | Efficient Query Repair for Aggregate Constraints | out-topic | query repair for aggregate constraints |
| 238 | Testing Graph Databases via Transformations Between Fixed-Length and Variable-Length Queries | out-topic | graph database testing via query transformations |
| 239 | Exploring Exploratory Querying | out-topic | vision paper on exploratory querying |
| 240 | Decisionhouse: Prescriptive Analytics in the Data Stack | out-topic | vision paper on prescriptive analytics |
| 241 | FlatStor: An Efficient Embedded-Index Based Columnar Data Layout for Multimodal Data Workloads | out-no-code | the declared artifact URL github.com/SJTU-Storage-Lab/FlatStor-Columnar-Layout returns 404 and the lab GitHub organisation lists no FlatStor repository |
| 242 | Active Data Lakes: Regaining Physical Data Independence Without Losing Interoperability | included | in scope as storage -- Mechanisms that restore physical data independence over Parquet-based data lakes so new storage layouts can be adopted without breaking interoperability |
| 243 | Interoperable ACID Transactions for Open Table Formats | out-topic | multi-table ACID transaction protocol for open table formats |
| 244 | LakeHelm: Zero-Shot Lakehouse Advisor for Joint Engine-Format Selection and Configuration | included | in scope as ml-for-systems -- Zero-shot mixture-of-experts advisor that jointly picks a lakehouse engine and table format plus its configuration. Concern: reproducing the training data needs Spark Trino and Presto installations |
| 245 | Storing and Indexing Multiple Tables by Interesting Orderings: For Efficient Joins, Groupings, and Updates in Relational Databases | out-topic | physical database design with merged indexes and interesting orderings |
| 246 | Understanding Disclosure Risk in Differential Privacy with Applications to Noise Calibration and Auditing | out-topic | disclosure risk analysis for differential privacy |
| 247 | Composition for Pufferfish Privacy | out-topic | privacy composition theory |
| 248 | Measuring Database Unfairness via Dependency Quantification Under Differential Privacy | out-topic | fairness measurement under differential privacy |
| 249 | Fast and Private Max-Sum Diversification | out-topic | private max-sum diversification algorithm |
| 250 | Fast Verification of Strong Database Isolation | out-topic | verification of database isolation levels |
| 251 | Pisco: An Isolation Bug Case Reduction and Deduplication Framework | out-topic | isolation bug case reduction and deduplication |
| 252 | SunStorm: Geographically distributed transactions over Aurora-style systems | out-machine | geographically distributed transactions across cloud regions |
| 253 | Orca: Flexible Quorums Meet Dynamic Quorums | out-machine | distributed quorum replication protocols |
| 254 | Swan: Hybrid MVCC Management for Efficient Transaction Processing in LSM-Tree-Based Key-Value Stores | included | in scope as storage -- Hybrid in-memory and out-of-memory MVCC for LSM-based key-value stores with transaction-aware data separation and concurrent memtable flushing |
| 255 | LIO: A lightweight and interpretable query optimizer based on an evolutionary forest | included | in scope as ml-for-systems -- Lightweight interpretable learned query optimizer based on an evolutionary forest that emits hints |
| 256 | The Data World Is Not Flat: Efficient Factorized Execution for Relational Systems | out-topic | factorized relational query execution |
| 257 | NeurIDA: Dynamic Modeling for Effective In-Database Analytics | out-topic | in-database predictive analytics modeling |
| 258 | Towards Efficient Random-Order Enumeration for Join Queries | out-topic | random-order join enumeration theory |
| 259 | EcoTable: Cost-effective Table Integration in Data Lakes for Natural Language Queries | out-topic | table integration in data lakes for NL queries |
| 260 | Remora: Scale-out Deterministic Execution for Smart Contracts | out-machine | scale-out smart contract execution with centralized dispatch and distributed executors |
| 261 | Understanding Evolving Graph Structures for Large Discrete-Time Dynamic Graph Representation | out-topic | dynamic graph representation learning |
| 262 | Efficient Temporal Edge-Core Maintenance in Streaming Graphs | out-topic | temporal edge-core maintenance algorithm |
| 263 | FlareDTDG: Harnessing Temporal Recency for Scalable Discrete-Time Dynamic Graph Training | out-machine | distributed dynamic graph training framework with cross-node communication |
| 264 | Finding Time-Proximity Communities in Temporal Heterogeneous Information Networks | out-topic | temporal community detection |
| 265 | A Semantics-aware Approach for Graph Edit Distance Estimation over Knowledge Graphs | out-topic | graph edit distance estimation |
| 266 | NeutronCloud: Resource-Aware Distributed GNN Training in Fluctuating Cloud Environments | out-machine | distributed GNN training in fluctuating cloud clusters |
| 267 | Multimodal Knowledge Graph Completion via Relation-Aware Negative Sampling with Diffusion-Based Interpolation | out-topic | multimodal knowledge graph completion |
| 268 | UniTG: A Unified System for Efficient and Seamless Textual Graph Learning | included | in scope as ml-systems -- Fuses the language model and GNN phases of textual graph learning into one runtime with co-designed components. Concern: larger language-model backbones may exceed 24 GB so a scaled-down backbone is needed |
| 269 | Maximum Defective Biclique Search in Large Bipartite Graphs | out-topic | defective biclique search algorithm |
| 270 | MH-GIN: Multi-scale Heterogeneous Graph-based Imputation Network for AIS Data | out-topic | graph imputation network for AIS data |
| 271 | FutureLight: An Efficient Future Traffic Data-Driven Reinforcement Learning Framework for Traffic Signal Controls | out-topic | reinforcement learning for traffic signal control |
| 272 | KAFY: An Extensible and Scalable Transformers-Based System for Trajectory Data Analysis | out-topic | transformer-based trajectory analysis system |
| 273 | MS-Index: Fast Top-k Subsequence Search for Multivariate Time Series under Euclidean Distance | out-topic | multivariate time series subsequence index |
| 274 | Error-bounded Point Cloud Compression Using Truncated Octahedron Quantization | out-topic | point cloud compression for a specific domain |
| 275 | FairDAG: Consensus Fairness over Multi-Proposer Causal Design | out-topic | consensus fairness in blockchain |
| 276 | Fides: Secure and Scalable Asynchronous DAG Consensus via Trusted Components | out-topic | asynchronous DAG consensus protocol |
| 277 | HarborMaster: Rollback Detection for Trusted Distributed Computing | out-topic | rollback detection for trusted distributed computing |
| 278 | Fugue: Online Elasticity for Distributed Stateful Stream Processing | out-topic | elasticity and state migration protocol for distributed stream processing |
| 279 | APEROL: Adaptive Parallel Edge-to-Cloud Runtime Optimization for Layered Workflow Execution | out-machine | adaptive runtime spanning edge and cloud tiers |
| 280 | Incremental Stream Query Deployment under Continuous Infrastructure Changes in the Cloud-Edge Continuum | out-machine | stream query deployment across the cloud-edge continuum |
| 281 | Meerkat: Scalable, Network-Aware Failure Recovery for the Internet of Things | out-machine | failure recovery across Internet-of-Things devices |
| 282 | SHARP: Shared State Reduction for Efficient Matching of Sequential Patterns | out-topic | shared state reduction for complex event processing |
| 283 | SafeLoad: Efficient Admission Control Framework for Identifying Memory-Overloading Queries in Cloud Data Warehouses | included | in scope as scheduling -- Admission control that predicts memory-overloading queries and reroutes them plus a released labelled benchmark |
| 284 | Love-at-First-Sight: First Answers Without the Awkward Silence in Big Knowledge Graphs | out-topic | progressive answering of SPARQL exploratory queries |
| 285 | Noisy Interactive Graph Search: An Uncertainty-Based Approach with Online Modeling of Latent Expertise and Difficulty | out-topic | noisy interactive graph search |
| 286 | Nav-Index: A High-Performance, Adaptive Index for Shortest Path Queries in RDBMS | out-topic | shortest path index inside an RDBMS |
| 287 | CRAFT: Corpus Relatedness Analysis Using Fourier Transforms | out-topic | corpus relatedness analysis |
| 288 | Lower-Bound Distance Queries under Partial Information | out-topic | distance queries under partial information |
| 289 | On Fair Epsilon Net and Geometric Hitting Set | out-topic | fair epsilon net and hitting set theory |
| 290 | Unbiased Binning for Fairness-aware Attribute Representation | out-topic | fairness-aware attribute binning |
| 291 | Auditing for Demographic Bias in Opaque Rankings | out-topic | auditing demographic bias in rankings |
| 292 | Sample-based Distinct Cardinality Estimation for Multiple Attributes in Multi-Dataset Queries | out-topic | sample-based distinct cardinality estimation |
| 293 | Algorithmic Data Minimization for Machine Learning over Internet-of-Things Data Streams | out-topic | algorithmic data minimization for IoT ML streams |
| 294 | Aggregating maximal cliques in real-world graphs | out-topic | maximal clique aggregation algorithm |
| 295 | Revisiting the Maximum Defective Clique Problem: Faster Branching and a Tighter Upper Bound | out-topic | defective clique search algorithm |
| 296 | CREST: Approximate k-Clique Counting in Real-World Networks via Refinement of Star-Based Sample Space | out-topic | approximate k-clique counting |
| 297 | Scalable Approximate Biclique Counting over Large Bipartite Graphs | out-topic | biclique counting over bipartite graphs |
