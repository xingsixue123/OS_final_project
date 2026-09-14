STATUS: complete
TOTAL_PAPERS: 354
INCLUDED: 47

## Sources

- **Paper list (primary):** the official PVLDB Volume 18 index at https://vldb.org/pvldb/volumes/18/ - fetched with `curl` and parsed from the embedded `__NEXT_DATA__` JSON (title, authors, PDF URL, page range and abstract for every entry). PVLDB Volume 18 is the volume presented at VLDB 2025 (London, September 2025).
- **Track boundary (primary):** the per-issue *Letter from the Editors in Chief* PDFs, `https://www.vldb.org/pvldb/vol18/FrontMatterVol18NoN.pdf`. The Issue 12 letter states verbatim that *"the first eleven issues covered research track papers accepted to PVLDB and presented at the VLDB 2025 Conference in London, Issue 12 includes all other contributions"* (Industrial, Demonstrations, Tutorials, Panels, Keynotes). The Issue 13 letter states that its papers *"are published after VLDB 2025 (London)"* and *"will roll over to be presented at VLDB 2026 (Boston)"*. So the main research track of VLDB 2025 = PVLDB Vol. 18, Issues 1-11. The research track itself spans four PVLDB categories - Regular Research, Experiment Analysis & Benchmark, Scalable Data Science and Vision - all of which are counted here.
- **Count cross-check:** the paper counts stated in each issue's editor letter were compared against the number of entries parsed from the volume index (front matter and errata excluded). Issue 1 = six, 2 = 33, 3 = 31, 4 = 25, 5 = 20, 6 = 33, 7 = 23, 8 = 34, 9 = 35, 10 = 33, 11 = 81. The parsed index gives exactly the same per-issue numbers, summing to **354**. Page ranges are also contiguous across the volume (p1 to p4762 for Issues 1-11), which is consistent with ~354 papers of ~13 pages.
- DBLP (`dblp.org/db/journals/pvldb/pvldb18.html`) was attempted as a third source but is behind an anti-bot proof-of-work challenge and could not be fetched from this host; the two independent PVLDB-side sources above were used instead.
- **Code check:** for every surviving paper the released PDF was downloaded and scanned for repository URLs (github / gitlab / zenodo / anonymous.4open.science / figshare), and the PVLDB per-paper "Artifacts" availability flag from the volume index was used as a second signal. All 46 GitHub links in the Included table were verified to return HTTP 200.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | Can Graph Reordering Speed Up Graph Neural Network Training? An Experimental Study | https://doi.org/10.14778/3705829.3705846 | https://www.vldb.org/pvldb/vol18/p293-merkel.pdf | https://github.com/gnn-benchmark/reordering | ml-systems | Single-node empirical study of 12 graph reordering strategies inside PyTorch Geometric and DGL - CPU and single-GPU training. Artifact released. Concern: it is an evaluation study so the improvement angle would be a new reordering or selection policy |
| 2 | CUBIT: Concurrent Updatable Bitmap Indexing | https://doi.org/10.14778/3705829.3705854 | https://www.vldb.org/pvldb/vol18/p399-athanassoulis.pdf | https://github.com/junchangwang/CUBIT | other-userspace | Latch-free concurrent updatable bitmap index - pure user-space C++ structure whose claim is scaling with core count; 16 cores / 32 threads is enough to reproduce the trend |
| 3 | Themis: A GPU-accelerated Relational Query Execution Engine | https://doi.org/10.14778/3705829.3705856 | https://www.vldb.org/pvldb/vol18/p426-han.pdf | https://github.com/postechdblab/themis | scheduling | Intra- and inter-warp load balancing for GPU query pipelines - GPU work scheduling, runs on a single Ampere GPU in user space |
| 4 | cedar: Optimized and Unified Machine Learning Input Data Pipelines | https://doi.org/10.14778/3705829.3705861 | https://www.vldb.org/pvldb/vol18/p488-zhao.pdf | https://github.com/stanford-mast/cedar | ml-systems | Framework plus optimizer for ML input-data pipelines; local execution is the default mode and distributed workers are optional |
| 5 | GraphAr: An Efficient Storage Scheme for Graph Data in Data Lakes | https://doi.org/10.14778/3712221.3712223 | https://www.vldb.org/pvldb/vol18/p530-li.pdf | https://github.com/apache/incubator-graphar | storage | Columnar storage scheme with custom encodings on top of Parquet; user-space C++ library on one machine |
| 6 | Laser: Buffer-Aware Learned Query Scheduling in Master-Standby Databases | https://doi.org/10.14778/3712221.3712239 | https://www.vldb.org/pvldb/vol18/p743-li.pdf | https://github.com/hyw498169842/LASER | scheduling | Learned buffer-aware query scheduler; master and standby can be two DBMS processes on the same host. Concern: needs a full DBMS deployment and workload traces |
| 7 | Towards Ideal Temporal Graph Neural Networks: Evaluations and Conclusions after 10,000 GPU Hours | https://doi.org/10.14778/3717755.3717758 | https://www.vldb.org/pvldb/vol18/p956-yang.pdf | https://github.com/Yang-yuxin/BenchTGNN | ml-systems | Unified TGNN design-space search framework with released code; each configuration is single-GPU. Concern: the published study consumed 10000 GPU hours so only a scaled-down slice of the space is feasible |
| 8 | Kishu: Time-Traveling for Computational Notebooks | https://doi.org/10.14778/3717755.3717759 | https://www.vldb.org/pvldb/vol18/p970-li.pdf | https://github.com/illinoisdata/kishu | storage | Incremental checkpoint / restore of notebook session state with dedup and CoW-style diffing - a pure user-space checkpointing system. Repo is not cited in the PDF; the official repo is illinoisdata/kishu |
| 9 | IncrCP: Decomposing and Orchestrating Incremental Checkpoints for Effective Recommendation Model Training | https://doi.org/10.14778/3717755.3717765 | https://www.vldb.org/pvldb/vol18/p1049-du.pdf | https://github.com/linqy71/IncrCP_paper | ml-systems | Incremental checkpointing with 2-D chunking and dedup; the I/O and storage design is per-node and testable on one machine with NVMe. Concern: paper trains recommendation models on many devices, needs scale-down |
| 10 | Are Joins over LSM-trees Ready: Take RocksDB as an Example | https://doi.org/10.14778/3717755.3717767 | https://www.vldb.org/pvldb/vol18/p1077-luo.pdf | https://github.com/we1pingyu/lsmjoin | storage | Systematic benchmark of join algorithms and secondary indexes over RocksDB; single-node disk-based LSM work with full code |
| 11 | Graph Neural Network Training Systems: A Performance Comparison of Full-Graph and Mini-Batch. | https://doi.org/10.14778/3717755.3717776 | https://www.vldb.org/pvldb/vol18/p1196-bajaj.pdf | https://github.com/saurabhbajaj123/GNN_minibatch_vs_fullbatch | ml-systems | Time-to-accuracy comparison of full-graph vs mini-batch GNN training systems. Concern: several baselines are multi-GPU or multi-node so a single-GPU subset must be chosen |
| 12 | DumpKV: Learning based lifetime aware garbage collection for key value separation in LSM-tree | https://doi.org/10.14778/3717755.3717778 | https://www.vldb.org/pvldb/vol18/p1223-zhuang.pdf | https://github.com/BilyZ98/DumpKV | storage | Learning-based lifetime-aware garbage collection for KV-separated LSM stores built on RocksDB; single node, disk-bound |
| 13 | Efficient Concurrent Updates to Persistent Randomized Binary Search Trees | https://doi.org/10.14778/3718057.3718074 | https://www.vldb.org/pvldb/vol18/p1481-wang.pdf | https://github.com/CUHK-DBGroup/Contreap | other-userspace | Concurrent multi-version in-memory search tree for multicore - user-space C++ concurrency work |
| 14 | BACH: Bridging Adjacency List and CSR Format using LSM-Trees for HGTAP Workloads | https://doi.org/10.14778/3718057.3718076 | https://www.vldb.org/pvldb/vol18/p1509-miao.pdf | https://github.com/2600254/BACH | storage | LSM-tree whose compaction transforms the data layout; disk-based single-node storage engine |
| 15 | FB+-tree: A Memory-Optimized B+-tree with Latch-Free Update | https://doi.org/10.14778/3725688.3725691 | https://www.vldb.org/pvldb/vol18/p1579-li.pdf | https://github.com/Spear-Neil/IndexResearch | other-userspace | Latch-free cache-optimized B+-tree; headline numbers use 96 threads, our 32 threads is a scale-down but the mechanism and the contention story are unchanged |
| 16 | GPEmu: A GPU Emulator for Faster and Cheaper Prototyping and Evaluation of Deep Learning System Research | https://doi.org/10.14778/3725688.3725716 | https://www.vldb.org/pvldb/vol18/p1919-wang.pdf | https://github.com/mengwanguc/gpemu | ml-systems | GPU emulator explicitly built so DL-systems research can be prototyped without real GPUs - unusually good fit for a constrained single-GPU machine |
| 17 | Tabular: Efficiently Building Efficient Indexes | https://doi.org/10.14778/3725688.3725721 | https://www.vldb.org/pvldb/vol18/p1991-yan.pdf | https://github.com/sfu-dis/tabular | other-userspace | Library that builds concurrent persistent indexes on top of an ACID table engine; user-space multicore system |
| 18 | Approximation-First Timeseries Query At Scale | https://doi.org/10.14778/3742728.3742732 | https://www.vldb.org/pvldb/vol18/p2348-zhu.pdf | https://github.com/Froot-NetSys/promsketch | caching | PromSketch is a sketch-based approximate cache layer for Prometheus and VictoriaMetrics rule queries; standalone user-space module |
| 19 | LogCloud: Fast Search of Compressed Logs on Object Storage | https://doi.org/10.14778/3742728.3742733 | https://www.vldb.org/pvldb/vol18/p2362-wang.pdf | https://github.com/marsupialtail/rottnest-vldb-repro | storage | Compressed log storage plus an FM-index searchable directly from object storage. Concern: designed for S3 so a local MinIO or filesystem backend is needed to reproduce |
| 20 | QPET: A Versatile and Portable Quantity-of-Interest-preservation Framework for Error-Bounded Lossy Compression | https://doi.org/10.14778/3742728.3742739 | https://www.vldb.org/pvldb/vol18/p2440-liang.pdf | https://github.com/JLiu-1/QPET-Artifact | storage | Error-bounded lossy compression framework layered on existing compressors; user-space C++ on one node |
| 21 | Fair Transaction Processing For Multi-Tenant Databases | https://doi.org/10.14778/3742728.3742751 | https://www.vldb.org/pvldb/vol18/p2602-cheng.pdf | https://github.com/audreyccheng/fair-txn-scheduler | scheduling | DRFT fair-share scheduling for transactions - resource-manager policy work evaluated on single-node benchmarks |
| 22 | AQETuner: Reliable Query-level Configuration Tuning for Analytical Query Engines | https://doi.org/10.14778/3742728.3742759 | https://www.vldb.org/pvldb/vol18/p2709-han.pdf | https://github.com/chenlx0/aqetuner | ml-for-systems | Bayesian-optimization query-level knob tuner for analytical engines - ML-based system tuning. Concern: tuning campaigns are long-running |
| 23 | Saving Private Hash Join | https://doi.org/10.14778/3742728.3742762 | https://www.vldb.org/pvldb/vol18/p2748-kuiper.pdf | https://github.com/lnkuiper/experiments | memory | Larger-than-memory hash join with a unified buffer pool and memory allocation across concurrent joins, implemented in DuckDB; single node |
| 24 | Locality-Aware Cache Replacement Policy for Graph Traversals | https://doi.org/10.14778/3746405.3746413 | https://www.vldb.org/pvldb/vol18/p2859-korkmaz.pdf | https://github.com/zeynepsaka/graphs-LAC | caching | LAC cache replacement policy evaluated both in a simulator and inside Neo4j - textbook eviction-policy work that a course project can extend |
| 25 | Keigo: Co-designing Log-Structured Merge Key-Value Stores with a Non-Volatile, Concurrency-aware Storage Hierarchy | https://doi.org/10.14778/3746405.3746414 | https://www.vldb.org/pvldb/vol18/p2872-macedo.pdf | https://github.com/dsrhaslab/keigo | storage | Storage middleware that places LSM files across a device hierarchy under RocksDB and LevelDB. Concern: needs more than one device class - our box has one NVMe tier so tiers must be emulated with cgroups or loopback devices |
| 26 | Why Are Learned Indexes So Effective but Sometimes Ineffective? | https://doi.org/10.14778/3746405.3746415 | https://www.vldb.org/pvldb/vol18/p2886-liu.pdf | https://github.com/qyliu-hkust/bench_search | ml-for-systems | Analysis of why PGM learned indexes under-perform plus PGM++; in-memory user-space benchmark, directly improvable |
| 27 | Decentralized Actor Scheduling and Reference-based Storage in Xorbits: a Native Scalable Data Science Engine | https://doi.org/10.14778/3746405.3746420 | https://www.vldb.org/pvldb/vol18/p2955-lu.pdf | https://github.com/xorbitsai/xorbits | scheduling | Decentralized actor scheduling and reference-based intermediate storage for data-science pipelines. Concern: designed for a cluster but runs as multiple processes on one host |
| 28 | STsCache: An Efficient Semantic Caching Scheme for Time-series Data Workloads Based on Hybrid Storage | https://doi.org/10.14778/3746405.3746421 | https://www.vldb.org/pvldb/vol18/p2964-li.pdf | https://github.com/ts-lab1024/ts-semantic-caching | caching | Semantic cache over DRAM plus NVMe SSD with slab management and eviction policies; user-space, single node |
| 29 | ArrayMorph: Optimizing Hyperslab Queries on the Cloud for Machine Learning Pipelines | https://doi.org/10.14778/3746405.3746437 | https://www.vldb.org/pvldb/vol18/p3189-jiang.pdf | https://github.com/ruochenj123/ArrayMorph | storage | Cost-based planner choosing chunked reads vs byte-range reads for array data. Concern: targets S3 and Azure - MinIO substitution is needed and the cloud cost model will not transfer |
| 30 | GpJSON: High-performance JSON Data Processing on GPUs | https://doi.org/10.14778/3746405.3746439 | https://www.vldb.org/pvldb/vol18/p3216-bonetta.pdf | https://github.com/gpjson-vldb/gpjson | other-userspace | GPU JSON parser and query library; evaluated on one A100 and works on one A5000. Concern: needs a GraalVM toolchain installed in user space |
| 31 | Déjà Vu: Efficient Video-Language Query Engine with Learning-based Inter-Frame Computation Reuse | https://doi.org/10.14778/3748191.3748195 | https://www.vldb.org/pvldb/vol18/p3284-hwang.pdf | https://github.com/casys-kaist/DejaVu | ml-systems | Inter-frame computation reuse for ViT-based video-language inference plus memory-compute compaction to turn FLOP savings into speedup; single GPU |
| 32 | Improving Time Series Data Compression in Apache IoTDB | https://doi.org/10.14778/3748191.3748204 | https://www.vldb.org/pvldb/vol18/p3406-tang.pdf | https://github.com/yuxin370/CompressIoTDB | storage | Homomorphic compression in Apache IoTDB - querying directly on compressed data; single-node JVM system |
| 33 | RapidStore: An Efficient Dynamic Graph Storage System for Concurrent Queries | https://doi.org/10.14778/3748191.3748217 | https://www.vldb.org/pvldb/vol18/p3587-sun.pdf | https://github.com/SJTU-Liquid/RapidStore | other-userspace | Concurrency-optimized in-memory dynamic graph store with decoupled version data; multicore user-space system |
| 34 | LogLite: Lightweight Plug-and-Play Streaming Log Compression | https://doi.org/10.14778/3749646.3749652 | https://www.vldb.org/pvldb/vol18/p3757-yang.pdf | https://github.com/benzhaotang/LogLite | storage | Streaming lossless log compressor; pure user-space algorithm with released implementation |
| 35 | Efficient Graph Data Access for Out-of-Memory GPU Streaming Graph Processing | https://doi.org/10.14778/3749646.3749659 | https://www.vldb.org/pvldb/vol18/p3854-wang.pdf | https://github.com/Yongze-zzz/C-GpuStreamGraph | caching | Grapin caches hot subgraphs in GPU memory for out-of-core streaming graph processing - the paper itself evaluates on a single NVIDIA A5000, exactly our GPU |
| 36 | Diva: Dynamic Range Filter for Var-Length Keys and Queries | https://doi.org/10.14778/3749646.3749664 | https://www.vldb.org/pvldb/vol18/p3923-eslami.pdf | https://github.com/n3slami/Diva | storage | Dynamic range filter for key-value stores (SuRF / Rosetta line); in-memory user-space data structure |
| 37 | DobLIX: A Dual-Objective Learned Index for Log-Structured Merge Trees | https://doi.org/10.14778/3749646.3749667 | https://www.vldb.org/pvldb/vol18/p3965-heidari.pdf | https://github.com/ah89/DobLIX | ml-for-systems | Learned index co-optimized with LSM data access plus an RL agent that tunes parameters, integrated into RocksDB |
| 38 | AnyBlox: A Framework for Self-Decoding Datasets | https://doi.org/10.14778/3749646.3749672 | https://www.vldb.org/pvldb/vol18/p4017-gienieczko.pdf | https://github.com/AnyBlox/vldb-2025 | storage | WebAssembly self-decoding dataset format integrated with DuckDB and Spark; Rust and wasm toolchains install in user space |
| 39 | Improving DBMS Scheduling Decisions with Accurate Performance Prediction on Concurrent Queries | https://doi.org/10.14778/3749646.3749686 | https://www.vldb.org/pvldb/vol18/p4185-wu.pdf | https://github.com/wuziniu/IconqSched | scheduling | Non-intrusive query scheduler driven by a learned concurrency-aware runtime predictor. Concern: the Redshift half of the evaluation cannot be reproduced, the Postgres half can |
| 40 | GraphCSR: A Degree-Equalized CSR Format for Large-scale Graph Processing | https://doi.org/10.14778/3749646.3749691 | https://www.vldb.org/pvldb/vol18/p4255-gan.pdf | https://anonymous.4open.science/r/GraphCSR-450E | memory | Degree-equalized CSR format that cuts memory footprint and improves batch access; single-node evaluation is meaningful. Concerns: the headline result uses a 79024-node supercomputer and the only artifact link is an anonymous.4open.science repo |
| 41 | TreeCat: Standalone Catalog Engine for Large Data Systems | https://doi.org/10.14778/3749646.3749696 | https://www.vldb.org/pvldb/vol18/p4323-oh.pdf | https://github.com/umddb/treecat | storage | Standalone catalog storage engine with a versioned range-optimized format and concurrent readers and writers; single node with code released |
| 42 | Select Edges Wisely: Monotonic Path Aware Graph Layout Optimization for Disk-based ANN Search | https://doi.org/10.14778/3749646.3749697 | https://www.vldb.org/pvldb/vol18/p4337-zheng.pdf | https://github.com/CodenameYZY/MARGO | storage | Disk-resident ANN graph layout optimization - contribution is disk locality and I/O reduction. Concern: sits between storage and vector indexing, audit should decide |
| 43 | Beyond Compression: A Comprehensive Evaluation of Lossless Floating-Point Compression | https://doi.org/10.14778/3749646.3749701 | https://www.vldb.org/pvldb/vol18/p4396-hishida.pdf | https://github.com/lemolatoon/ebi | storage | Benchmark plus Rust library of lossless floating-point compressors including in-situ query execution on compressed data; single node |
| 44 | Sphinx: A Succinct Perfect Hash Index for x86 | https://doi.org/10.14778/3749646.3749703 | https://www.vldb.org/pvldb/vol18/p4424-maghrebi.pdf | https://github.com/sfmqrb/sphinx | storage | Succinct perfect-hash in-memory index for key-value stores tuned for commodity x86; user-space, memory-footprint driven |
| 45 | Robust Recursive Query Parallelism in Graph Database Management Systems | https://doi.org/10.14778/3749646.3749706 | https://www.vldb.org/pvldb/vol18/p4465-chakraborty.pdf | https://github.com/anuchak/kuzu | scheduling | Morsel dispatching policies for parallel recursive joins in Kuzu - a multicore task-scheduling design space study; artifact is a Kuzu fork |
| 46 | The FastLanes File Format | https://doi.org/10.14778/3749646.3749718 | https://www.vldb.org/pvldb/vol18/p4629-afroozeh.pdf | https://github.com/cwida/FastLanes | storage | Open-source columnar file format with cascading lightweight data-parallel encodings; portable auto-vectorizing C++, single node |
| 47 | Turbocharging Vector Databases using Modern SSDs | https://doi.org/10.14778/3749646.3749724 | https://www.vldb.org/pvldb/vol18/p4710-do.pdf | https://github.com/FlashSQL/io-optimized-pgvector | storage | SSD-aware pgvector optimizations using io_uring parallel I/O, insertion reordering and locality-preserving colocation; io_uring needs no root |

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | The Key to Effective UDF Optimization: Before Inlining, First Perform Outlining | out-topic | query optimization or estimation - not a systems resource-management topic |
| 2 | CUTTANA: Scalable Graph Partitioning for Faster Distributed Graph Databases and Analytics | out-topic | graph mining or graph learning algorithm |
| 3 | Cardinality Estimation for Having-Clauses | out-topic | cardinality estimation for having-clauses - query optimization topic |
| 4 | Chameleon: a Heterogeneous and Disaggregated Accelerator System for Retrieval-Augmented Language Models | out-machine | core contribution is an FPGA vector-search accelerator in a disaggregated CPU-GPU-FPGA cluster |
| 5 | LLM-R2: A Large Language Model Enhanced Rule-based Rewrite System for Boosting Query Efficiency | out-topic | query optimization or estimation - not a systems resource-management topic |
| 6 | Nitro: Boosting Distributed Reinforcement Learning with Serverless Computing | out-machine | training engine depends on AWS Lambda serverless functions plus EC2 - no cloud or multi-node resources available |
| 7 | RED: Effective Trajectory Representation Learning with Comprehensive Information | out-topic | time-series or spatial data mining |
| 8 | Accurate and Fast Approximate Graph Pattern Mining at Scale | out-topic | graph mining or graph learning algorithm |
| 9 | QueryArtisan: Generating Data Manipulation Codes for Ad-hoc Analysis in Data Lakes | out-topic | LLM-generated data-manipulation code for data lakes |
| 10 | Efficient and Effective Algorithms for A Family of Influence Maximization Problems with A Matroid Constraint | out-topic | influence maximization - graph algorithm |
| 11 | COLOR: A Framework for Applying Graph Coloring to Subgraph Cardinality Estimation | out-topic | query optimization or estimation - not a systems resource-management topic |
| 12 | Fully Automated Correlated Time Series Forecasting in Minutes | out-topic | time-series or spatial data mining |
| 13 | From Logs to Causal Inference: Diagnosing Large Systems | out-topic | causal-inference tooling for diagnosing systems from logs - an analysis method not a systems artifact |
| 14 | NeutronTP: Load-Balanced Distributed Full-Graph GNN Training with Tensor Parallelism | out-machine | distributed full-graph GNN training with tensor parallelism across many GPUs and machines |
| 15 | Unleash the Power of Ellipsis: Accuracy-enhanced Sparse Vector Technique with Exponential Noise and Optimal Threshold Correction | out-topic | privacy or security topic |
| 16 | Maximum Defective Clique Computation: Improved Time Complexities and Practical Performance | out-topic | graph mining or graph learning algorithm |
| 17 | Substructure-aware Log Anomaly Detection | out-topic | time-series or spatial data mining |
| 18 | Less is More: Efficient Time Series Dataset Condensation via Two-fold Modal Matching | out-topic | time-series or spatial data mining |
| 19 | A Memory Guided Transformer for Time Series Forecasting | out-topic | time-series or spatial data mining |
| 20 | LEAP: LLM-powered End-to-end Automatic Library for Processing Social Science Queries on Unstructured Data | out-topic | LLM application for data tasks - not a serving or inference system |
| 21 | TEAM: Topological Evolution-aware Framework for Traffic Forecasting | out-topic | graph mining or graph learning algorithm |
| 22 | Chimera: A system design of dual storage and traversal-join unified query processing for SQL/PGQ | out-topic | graph query processing over dual relational and graph storage |
| 23 | Can Graph Reordering Speed Up Graph Neural Network Training? An Experimental Study | included | in scope as ml-systems - see Included table |
| 24 | HyperBlocker: Accelerating Rule-based Blocking in Entity Resolution using GPUs | out-topic | data cleaning integration or discovery |
| 25 | Calibrating Noise for Group Privacy in Subsampled Mechanisms | out-topic | privacy or security topic |
| 26 | Outback: Fast and Communication-efficient Index for Key-Value Store on Disaggregated Memory | out-machine | key-value index designed for RDMA over disaggregated memory pools - needs RDMA and multiple nodes |
| 27 | Making CRDTs Not So Eventual | out-topic | conflict-free replicated data type consistency work |
| 28 | Maximum k-Plex Search: An Alternated Reduction-and-Bound Method | out-topic | graph mining or graph learning algorithm |
| 29 | Discovering Leitmotifs in Multidimensional Time Series | out-topic | time-series or spatial data mining |
| 30 | SIMformer: Single-Layer Vanilla Transformer Can Learn Free-Space Trajectory Similarity | out-topic | time-series or spatial data mining |
| 31 | CUBIT: Concurrent Updatable Bitmap Indexing | included | in scope as other-userspace - see Included table |
| 32 | Privacy-Enhanced Database Synthesis for Benchmark Publishing | out-topic | privacy or security topic |
| 33 | Themis: A GPU-accelerated Relational Query Execution Engine | included | in scope as scheduling - see Included table |
| 34 | Finding Convincing Views to Endorse a Claim | out-topic | data exploration and claim-vetting technique |
| 35 | Quantifying Point Contributions: A Lightweight Framework for Efficient and Effective Query-Driven Trajectory Simplification | out-topic | graph mining or graph learning algorithm |
| 36 | MILLION: A General Multi-Objective Framework with Controllable Risk for Portfolio Management | out-topic | data science explanation or ML modelling topic |
| 37 | The Cost of Representation by Subset Repairs | out-topic | data cleaning integration or discovery |
| 38 | cedar: Optimized and Unified Machine Learning Input Data Pipelines | included | in scope as ml-systems - see Included table |
| 39 | Goku: A Schemaless Time Series Database for Large Scale Monitoring at Pinterest | out-no-code | Pinterest-internal time-series database; PVLDB artifact flag is no and the PDF contains no repository link - only OpenTSDB and AWS documentation URLs |
| 40 | Agent-OM: Leveraging LLM Agents for Ontology Matching | out-topic | LLM application for data tasks - not a serving or inference system |
| 41 | GraphAr: An Efficient Storage Scheme for Graph Data in Data Lakes | included | in scope as storage - see Included table |
| 42 | Cardinality Estimation for Similarity Search on High-Dimensional Data Objects: The Impact of Reference Objects | out-topic | query optimization or estimation - not a systems resource-management topic |
| 43 | Efficient Top-k Frequent Subgraph Mining Using Tight Upper and Lower Bounds | out-topic | graph mining or graph learning algorithm |
| 44 | MSGNN: Masked Schema based Graph Neural Networks | out-topic | graph mining or graph learning algorithm |
| 45 | How Reliable Are Streams? End-to-End Processing-Guarantee Validation and Performance Benchmarking of Stream Processing Systems | out-topic | benchmark or evaluation study outside the scope topic table |
| 46 | Towards Sufficient GPU-accelerated Dynamic Graph Management: Survey and Experiment | out-topic | survey and experiments on GPU dynamic graph management - graph processing topic |
| 47 | RDPro: Distributed Processing of Big Raster Data | out-topic | time-series or spatial data mining |
| 48 | Approximate Anchored Densest Subgraph Search on Large Static and Dynamic Graphs | out-topic | graph mining or graph learning algorithm |
| 49 | PRICE: A Pretrained Model for Cross-Database Cardinality Estimation | out-topic | query optimization or estimation - not a systems resource-management topic |
| 50 | Datalog with First-Class Facts | out-topic | Datalog language design and deductive reasoning |
| 51 | T-Assess: An Efficient Data Quality Assessment System Tailored for Trajectory Data | out-topic | time-series or spatial data mining |
| 52 | LEAP: A Low-cost Spark SQL Query Optimizer using Pairwise Comparison | out-topic | query optimization or estimation - not a systems resource-management topic |
| 53 | Towards Practical Oblivious Map | out-topic | privacy or security topic |
| 54 | PolyBase: Adapting to Data Affinity Changes in Geo-Replicated Database via Row-Level Consensus-Group Affiliation Re-Assignment | out-topic | transaction replication or distributed protocol work |
| 55 | Explaining GNN-based Recommendations in Logic | out-topic | graph mining or graph learning algorithm |
| 56 | Efficient Computation of Hyper-triangles on Hypergraphs | out-topic | graph mining or graph learning algorithm |
| 57 | Laser: Buffer-Aware Learned Query Scheduling in Master-Standby Databases | included | in scope as scheduling - see Included table |
| 58 | A Single Machine System for Querying Big Graphs with PRAM | out-topic | graph mining or graph learning algorithm |
| 59 | A CPU-GPU Hybrid Labelling Algorithm for Massive Shortest Distance Queries on Road Networks | out-topic | graph mining or graph learning algorithm |
| 60 | SDEcho: Efficient Explanation of Aggregated Sequence Difference | out-topic | explaining differences between aggregated query result sequences |
| 61 | MLP-Mixer based Masked Autoencoders Are Effective, Explainable and Robust for Time Series Anomaly Detection | out-topic | time-series or spatial data mining |
| 62 | Efficient Data-aware Distance Comparison Operations for High-Dimensional Approximate Nearest Neighbor Search | out-topic | vector or similarity search indexing |
| 63 | Seer: Accelerating Blockchain Transaction Execution by Fine-Grained Branch Prediction | out-topic | blockchain or BFT topic |
| 64 | The ParClusterers Benchmark Suite (PCBS): A Fine-Grained Analysis of Scalable Graph Clustering | out-topic | graph mining or graph learning algorithm |
| 65 | Semantic Conformance Testing of Relational DBMS | out-topic | DBMS testing debugging or verification tooling |
| 66 | RankPQO: Learning-to-Rank for Parametric Query Optimization | out-topic | query optimization or estimation - not a systems resource-management topic |
| 67 | Datamap-Driven Tabular Coreset Selection for Classifier Training | out-topic | data science explanation or ML modelling topic |
| 68 | Towards Scalable and Practical Batch-Dynamic Connectivity | out-topic | graph mining or graph learning algorithm |
| 69 | IcedTea: Efficient and Responsive Time-Travel Debugging in Dataflow Systems | out-topic | time-travel debugging paradigm for distributed dataflow jobs |
| 70 | Representative Time Series Discovery for Data Exploration | out-topic | time-series or spatial data mining |
| 71 | Efficient Graph Embedding Generation and Update for Large-Scale Temporal Graph | out-topic | temporal graph embedding maintenance algorithm |
| 72 | FaDE: More Than a Million What-ifs Per Second | out-topic | query optimization or estimation - not a systems resource-management topic |
| 73 | Towards Ideal Temporal Graph Neural Networks: Evaluations and Conclusions after 10,000 GPU Hours | included | in scope as ml-systems - see Included table |
| 74 | Kishu: Time-Traveling for Computational Notebooks | included | in scope as storage - see Included table |
| 75 | GTI: Graph-based Tree Index with Logarithm Updates for Nearest Neighbor Search in High-Dimensional Spaces | out-topic | vector or similarity search indexing |
| 76 | Incremental Detection of Denial Constraint Violations | out-topic | query optimization or estimation - not a systems resource-management topic |
| 77 | Revisiting CNNs for Trajectory Similarity Learning | out-topic | time-series or spatial data mining |
| 78 | Most Similar Biclique Search at Scale | out-topic | graph mining or graph learning algorithm |
| 79 | SPECIAL: Synopsis Assisted Secure Collaborative Analytics | out-topic | privacy or security topic |
| 80 | IncrCP: Decomposing and Orchestrating Incremental Checkpoints for Effective Recommendation Model Training | included | in scope as ml-systems - see Included table |
| 81 | WeShap: Weak Supervision Source Evaluation with Shapley Values | out-topic | data valuation for weak supervision - ML modelling topic |
| 82 | Are Joins over LSM-trees Ready: Take RocksDB as an Example | included | in scope as storage - see Included table |
| 83 | Interactive Graph Search for Multiple Targets on DAGs | out-topic | graph mining or graph learning algorithm |
| 84 | AdaNDV: Adaptive Number of Distinct Value Estimation via Learning to Select and Fuse Estimators | out-topic | query optimization or estimation - not a systems resource-management topic |
| 85 | UNIFY: Unified Index for Range Filtered Approximate Nearest Neighbors Search | out-topic | vector or similarity search indexing |
| 86 | In-depth Analysis of Densest Subgraph Discovery in a Unified Framework | out-topic | graph mining or graph learning algorithm |
| 87 | Sphinteract: Resolving Ambiguities in NL2SQL Through User Interaction | out-topic | LLM application for data tasks - not a serving or inference system |
| 88 | Noise Matters: Cross Contrastive Learning for Flink Anomaly Detection | out-topic | time-series or spatial data mining |
| 89 | RCRank: Multimodal Ranking of Root Causes of Slow Queries in Cloud Database Systems | out-topic | ML-based root-cause ranking for slow cloud queries - a diagnosis model not a systems artifact |
| 90 | Ranking Indicator Discovery from Very Large Knowledge Graphs | out-topic | graph mining or graph learning algorithm |
| 91 | Graph Neural Network Training Systems: A Performance Comparison of Full-Graph and Mini-Batch. | included | in scope as ml-systems - see Included table |
| 92 | Discovering Approximate Inclusion Dependencies | out-topic | data cleaning integration or discovery |
| 93 | DumpKV: Learning based lifetime aware garbage collection for key value separation in LSM-tree | included | in scope as storage - see Included table |
| 94 | RGS-Sketch: An Accurate, Invertible, and Mergeable Sketch for Online Super Spreader Detection in High-speed Data Streams | out-topic | algorithmic or language-level data management topic |
| 95 | Vortex: Overcoming Memory Capacity Limitations in GPU-Accelerated Large-Scale Data Analytics | out-machine | the central IO primitive routes data through several GPUs over multiple PCIe links - needs a multi-GPU host |
| 96 | Dandelion: Smaller Clusters, Bigger Speeds—Distributed Transactions Redefined | out-topic | transaction replication or distributed protocol work |
| 97 | Esc: An Early-Stopping Checker for Budget-aware Index Tuning | out-no-code | budget-aware index tuning on a commercial optimizer; PVLDB artifact flag is no and the only repository cited is the third-party join-order benchmark |
| 98 | Jodes: Efficient Oblivious Join in the Distributed Setting | out-topic | privacy or security topic |
| 99 | OpenFGL: A Comprehensive Benchmark for Federated Graph Learning | out-topic | federated graph learning benchmark |
| 100 | Evaluating Continuous Queries with Inconsistency Annotations | out-topic | query optimization or estimation - not a systems resource-management topic |
| 101 | On More Efficiently and Versatilely Querying Historical k-Cores | out-topic | temporal graph indexing for historical k-core queries |
| 102 | GeoBloom: Revisiting Lightweight Models for Geographic Information Retrieval | out-topic | time-series or spatial data mining |
| 103 | VerIso: Verifiable Isolation Guarantees for Database Transactions | out-topic | DBMS testing debugging or verification tooling |
| 104 | A Hybrid Approach to Integrating Deterministic and Non-deterministic Concurrency Control in Database Systems | out-topic | transaction replication or distributed protocol work |
| 105 | From Genesis to Maturity: Managing Knowledge Graph Ecosystems Through Life Cycles | out-topic | knowledge graph life-cycle management methodology |
| 106 | Avoiding Materialisation for Guarded Aggregate Queries | out-topic | query optimization or estimation - not a systems resource-management topic |
| 107 | Synergetic Community Search over Large Multilayer Graphs | out-topic | graph mining or graph learning algorithm |
| 108 | Searching and Detecting Structurally Similar Communities in Large Heterogeneous Information Networks | out-topic | graph mining or graph learning algorithm |
| 109 | Cabinet: Dynamically Weighted Consensus Made Fast | out-topic | transaction replication or distributed protocol work |
| 110 | Mining the Minoria: Unknown, Under-represented, and Under-performing Minority Groups | out-topic | identifying under-represented groups in data |
| 111 | Efficient Concurrent Updates to Persistent Randomized Binary Search Trees | included | in scope as other-userspace - see Included table |
| 112 | Explaining Black-Box Clustering Pipelines With Cluster-Explorer | out-topic | time-series or spatial data mining |
| 113 | BACH: Bridging Adjacency List and CSR Format using LSM-Trees for HGTAP Workloads | included | in scope as storage - see Included table |
| 114 | FLEET: High-Performance Durable Replicated State Machines using Scattered and Coordinated Log Entries | out-topic | transaction replication or distributed protocol work |
| 115 | BigVectorBench: Heterogeneous Data Embedding and Compound Queries are Essential in Evaluating Vector Databases | out-topic | vector or similarity search indexing |
| 116 | A Systematic Study on Early Stopping Metrics in HPO and the Implications of Uncertainty | out-topic | data science explanation or ML modelling topic |
| 117 | TELESAFE - Detecting Private/Work Boundary Crossings in Energy Consumption Trails in Telework | out-topic | privacy application over energy-consumption traces |
| 118 | FB+-tree: A Memory-Optimized B+-tree with Latch-Free Update | included | in scope as other-userspace - see Included table |
| 119 | VStream: A Distributed Streaming Vector Search System | out-topic | vector or similarity search indexing |
| 120 | Efficient Historical Butterfly Counting in Large Temporal Bipartite Networks via Graph Structure-aware Index | out-topic | graph mining or graph learning algorithm |
| 121 | PlanRGCN: Predicting SPARQL Query Performance | out-topic | query optimization or estimation - not a systems resource-management topic |
| 122 | Holistic query Approximation via RL Modeling | out-topic | query optimization or estimation - not a systems resource-management topic |
| 123 | Unleashing Graph Partitioning for Large-Scale Nearest Neighbor Search | out-topic | graph mining or graph learning algorithm |
| 124 | BiST: A Lightweight and Efficient Bi-directional Model for Spatiotemporal Prediction | out-topic | time-series or spatial data mining |
| 125 | QOVIS: Understanding and Diagnosing Query Optimizer via a Visualization-assisted Approach (Revision) | out-topic | query optimization or estimation - not a systems resource-management topic |
| 126 | Unsupervised Anomaly Detection in Multivariate Time Series across Heterogeneous Domains | out-topic | time-series or spatial data mining |
| 127 | NeutronTask: Scalable and Efficient Multi-GPU GNN Training with Task Parallelism | out-machine | multi-GPU GNN training with task parallelism - no meaningful single-GPU version of the contribution |
| 128 | Quantum Data Management in the NISQ Era | out-topic | quantum data management outlook |
| 129 | G-View: View Management for Graph Databases | out-topic | query optimization or estimation - not a systems resource-management topic |
| 130 | Privacy for Free: Leveraging Local Differential Privacy Perturbed Data from Multiple Services | out-topic | privacy or security topic |
| 131 | K2: On Optimizing Distributed Transactions in a Multi-region Data Store with True-time Clocks | out-topic | transaction replication or distributed protocol work |
| 132 | Maximum Inner Product is Query-Scaled Nearest Neighbor | out-topic | maximum inner product search - vector indexing |
| 133 | Migration-Free Elastic Storage of Time Series in Apache IoTDB | out-machine | elastic shard and replica placement in a distributed IoTDB cluster - inherently multi-node |
| 134 | GQL and SQL/PGQ: Theoretical Models and Expressive Power | out-topic | theory and expressive power of graph query languages |
| 135 | A Practical Theory of Generalization in Selectivity Learning | out-topic | query optimization or estimation - not a systems resource-management topic |
| 136 | Revisiting the Index Construction of Proximity Graph-Based Approximate Nearest Neighbor Search | out-topic | vector or similarity search indexing |
| 137 | Mining Platoon Patterns from Traffic Videos | out-topic | time-series or spatial data mining |
| 138 | Agamotto: Scheduling of Deadline-Oriented Incremental Query Execution under Uncertain Resource Price | out-no-code | scheduler prototype; PVLDB artifact flag is no and the PDF contains no code URL - no matching repository found by name search |
| 139 | SCompression: Enhancing Database Knob Tuning Efficiency Through Slice-Based OLTP Workload Compression | out-no-code | workload-compression tuner; PVLDB artifact flag is no and the PDF cites no repository |
| 140 | Fucci: Database Transaction Fuzzing via Random Conflict Construction and Multilevel Constraint Solving | out-topic | DBMS testing debugging or verification tooling |
| 141 | Streaming Time Series Subsequence Anomaly Detection: A Glance and Focus Approach | out-topic | time-series or spatial data mining |
| 142 | Infinite Stream Estimation under Personalized w-Event Privacy | out-topic | privacy or security topic |
| 143 | GPEmu: A GPU Emulator for Faster and Cheaper Prototyping and Evaluation of Deep Learning System Research | included | in scope as ml-systems - see Included table |
| 144 | Causal DAG Summarization | out-topic | data science explanation or ML modelling topic |
| 145 | mLoRA: Fine-Tuning LoRA Adapters via Highly-Efficient Pipeline Parallelism in Multiple GPUs | out-machine | LoRA fine-tuning via pipeline parallelism across multiple GPUs and machines |
| 146 | Anarchy in the Database: A Survey and Evaluation of Database Management System Extensibility | out-topic | survey of DBMS extension ecosystems |
| 147 | A Flexible Framework for Query-oriented Interactive Community Search | out-topic | graph mining or graph learning algorithm |
| 148 | Tabular: Efficiently Building Efficient Indexes | included | in scope as other-userspace - see Included table |
| 149 | Efficient Maintenance of 2-Hop Labeling Index on Dynamic Small-World Graphs | out-topic | graph mining or graph learning algorithm |
| 150 | Vive la Différence: Practical Diff Testing of Stateful Applications | out-topic | diff testing methodology for software rollout |
| 151 | GREAT: Generalized Reservoir Sampling based Triangle Counting Estimation over Streaming Graphs | out-topic | graph mining or graph learning algorithm |
| 152 | Efficient Discovery of Relaxed Functional Dependencies | out-topic | data cleaning integration or discovery |
| 153 | SimRN: Trajectory Similarity Learning in Road Networks based on Distributed Deep Reinforcement Learning | out-topic | graph mining or graph learning algorithm |
| 154 | BIRDIE: Natural Language-Driven Table Discovery Using Differentiable Search Index | out-topic | vector or similarity search indexing |
| 155 | SkyStore: Cost-Optimized Object Storage Across Regions and Clouds | out-machine | object store spanning multiple cloud regions and providers - needs paid multi-cloud accounts |
| 156 | The Power of Constraints in Natural Language to SQL Translation | out-topic | LLM application for data tasks - not a serving or inference system |
| 157 | ACE: A Cardinality Estimator for Set-Valued Queries | out-topic | query optimization or estimation - not a systems resource-management topic |
| 158 | Accio: Bolt-on Query Federation | out-topic | bolt-on query federation - query processing topic |
| 159 | Falcon: Advancing Asynchronous BFT Consensus for Lower Latency and Enhanced Throughput | out-topic | blockchain or BFT topic |
| 160 | Scalable Pre-Training of Compact Urban Spatio-Temporal Predictive Models on Large-Scale Multi-Domain Data | out-topic | time-series or spatial data mining |
| 161 | HADES: Range-Filtered Private Aggregation on Public Data | out-topic | privacy or security topic |
| 162 | Optimized Batch Prompting for Cost-effective LLMs | out-topic | LLM application for data tasks - not a serving or inference system |
| 163 | Truss Decomposition in Hypergraphs | out-topic | graph mining or graph learning algorithm |
| 164 | Optimal Sharding for Scalable Blockchains with Deconstructed SMR | out-topic | blockchain or BFT topic |
| 165 | Auto-Prep: Holistic Prediction of Data Preparation Steps for Self-Service Business Intelligence | out-topic | data cleaning integration or discovery |
| 166 | Time Series Motif Discovery: A Comprehensive Evaluation | out-topic | time-series or spatial data mining |
| 167 | EinDecomp: Decomposition of Declaratively-Specified Machine Learning and Numerical Computations for Parallel Execution | out-machine | intra-operator parallelism that splits operators across many devices - a GPU server or CPU cluster |
| 168 | Continuous Lifelong Conflict-Aware AGV Routing with Kinematic Constraints | out-topic | AGV routing optimization application |
| 169 | Wolverine: Highly Efficient Monotonic Search Path Repair for Graph-based ANN Index Updates | out-topic | ANN index update repair - vector indexing |
| 170 | Detecting Schema-Related Logic Bugs in Relational DBMSs via Equivalent Database Construction | out-topic | DBMS testing debugging or verification tooling |
| 171 | GraphSparseNet: a Novel Method for Large Scale Traffic Flow Prediction | out-topic | graph mining or graph learning algorithm |
| 172 | TMLKD: Few-shot Trajectory Metric Learning via Knowledge Distillation | out-topic | time-series or spatial data mining |
| 173 | Oze: Decentralized Graph-based Concurrency Control for Long-running Update Transactions | out-topic | transaction replication or distributed protocol work |
| 174 | Hermes: Off-the-Shelf Real-Time Transactional Analytics | out-topic | transaction replication or distributed protocol work |
| 175 | Approximation-First Timeseries Query At Scale | included | in scope as caching - see Included table |
| 176 | LogCloud: Fast Search of Compressed Logs on Object Storage | included | in scope as storage - see Included table |
| 177 | Weak-to-Strong Prompts with Lightweight-to-Powerful LLMs for High-Accuracy, Low-Cost, and Explainable Data Transformation | out-topic | LLM application for data tasks - not a serving or inference system |
| 178 | ChatTS: Aligning Time Series with LLMs via Synthetic Data for Enhanced Understanding and Reasoning | out-topic | time-series or spatial data mining |
| 179 | Federated Data Shift Distance Estimation | out-topic | privacy or security topic |
| 180 | Instance-Optimal Acyclic Join Processing Without Regret: Engineering the Yannakakis Algorithm in Column Stores | out-topic | instance-optimal acyclic join processing - query execution algorithm |
| 181 | Asymmetric Linearizable Local Reads | out-topic | transaction replication or distributed protocol work |
| 182 | QPET: A Versatile and Portable Quantity-of-Interest-preservation Framework for Error-Bounded Lossy Compression | included | in scope as storage - see Included table |
| 183 | OpenMEL: Unsupervised Multimodal Entity Linking Using Noise-Free Expanded Queries and Global Coherence | out-topic | LLM application for data tasks - not a serving or inference system |
| 184 | Unraveling the Impact of Window Semantics: Optimizing Join Order for Efficient Stream Processing | out-topic | query optimization or estimation - not a systems resource-management topic |
| 185 | Deduplicated Sampling On-Demand | out-topic | algorithmic or language-level data management topic |
| 186 | The Limits of Graph Samplers for Training Inductive Recommender Systems | out-topic | graph mining or graph learning algorithm |
| 187 | HoliPaxos: Towards More Predictable Performance in State Machine Replication | out-topic | transaction replication or distributed protocol work |
| 188 | Data-Agnostic Cardinality Learning from Imperfect Workloads | out-topic | query optimization or estimation - not a systems resource-management topic |
| 189 | BLAEQ: A Multigrid Index for Spatial Query on Geometry Data | out-topic | time-series or spatial data mining |
| 190 | Simple Testing Can Expose Most Critical Transaction Bugs: Understanding and Detecting Write-Specific Serializability Violations in Database Systems | out-topic | DBMS testing debugging or verification tooling |
| 191 | Efficient and Adaptive Estimation of Local Triadic Coefficients | out-topic | graph mining or graph learning algorithm |
| 192 | VecCity: A Taxonomy-guided Library for Map Entity Representation Learning [Experiment, Analysis & Benchmark] | out-topic | benchmark or evaluation study outside the scope topic table |
| 193 | Evaluating Methods for Efficient Entity Count Estimation | out-topic | data cleaning integration or discovery |
| 194 | Fair Transaction Processing For Multi-Tenant Databases | included | in scope as scheduling - see Included table |
| 195 | LobRA: Multi-tenant Fine-tuning over Heterogeneous Data | out-machine | multi-tenant LoRA fine-tuning with heterogeneous parallel configurations across many GPUs |
| 196 | Robust Plan Evaluation based on Approximate Probabilistic Machine Learning | out-topic | query optimization or estimation - not a systems resource-management topic |
| 197 | CatDB: Data-catalog-guided, LLM-based Generation of Data-centric ML Pipelines | out-topic | LLM application for data tasks - not a serving or inference system |
| 198 | Conformal Prediction for Verifiable Learned Query Optimization | out-topic | conformal prediction for learned query optimizers - query optimization topic |
| 199 | Is Integer Linear Programming All You Need for Deletion Propagation? A Unified and Practical Approach for Generalized Deletion Propagation | out-topic | query optimization or estimation - not a systems resource-management topic |
| 200 | Magneto: Combining Small and Large Language Models for Schema Matching | out-topic | LLM application for data tasks - not a serving or inference system |
| 201 | Efficient and Accurate Subgraph Counting: A Bottom-up Flow-learning based Approach | out-topic | graph mining or graph learning algorithm |
| 202 | AQETuner: Reliable Query-level Configuration Tuning for Analytical Query Engines | included | in scope as ml-for-systems - see Included table |
| 203 | PipeTGL: (Near) Zero Bubble Memory-based Temporal Graph Neural Network Training via Pipeline Optimization | out-machine | pipeline-parallel temporal GNN training designed for multi-GPU bubble elimination |
| 204 | Is Long Context All You Need? Leveraging LLM's  Extended Context for NL2SQL | out-topic | LLM application for data tasks - not a serving or inference system |
| 205 | Saving Private Hash Join | included | in scope as memory - see Included table |
| 206 | Concurrency Control as a Service | out-topic | transaction replication or distributed protocol work |
| 207 | TAB: Unified Benchmarking of Time Series Anomaly Detection Methods | out-topic | time-series or spatial data mining |
| 208 | Heta: Distributed Training of Heterogeneous Graph Neural Networks | out-machine | distributed HGNN training whose contribution is communication reduction across machines |
| 209 | The UDFBench Benchmark for General-purpose UDF Queries | out-topic | query optimization or estimation - not a systems resource-management topic |
| 210 | eXpath: Explaining Knowledge Graph Link Prediction with Ontological Closed Path Rules | out-topic | graph mining or graph learning algorithm |
| 211 | The LAW theorem: Local Reads and Linearizable Asynchronous Replication | out-topic | transaction replication or distributed protocol work |
| 212 | Using Read Promotion and Mixed Isolation Levels for Performant Yet Serializable Execution of Transaction Programs | out-topic | transaction replication or distributed protocol work |
| 213 | Locality-Aware Cache Replacement Policy for Graph Traversals | included | in scope as caching - see Included table |
| 214 | Keigo: Co-designing Log-Structured Merge Key-Value Stores with a Non-Volatile, Concurrency-aware Storage Hierarchy | included | in scope as storage - see Included table |
| 215 | Why Are Learned Indexes So Effective but Sometimes Ineffective? | included | in scope as ml-for-systems - see Included table |
| 216 | Still More Shades of Null: An Evaluation Suite for Responsible Missing Value Imputation [Experiment, Analysis and Benchmark] | out-topic | data cleaning integration or discovery |
| 217 | OpenForge: Probabilistic Metadata Integration | out-topic | LLM application for data tasks - not a serving or inference system |
| 218 | Maximum k-Plex Finding: Choices of Pruning Techniques Matter! | out-topic | graph mining or graph learning algorithm |
| 219 | A Comprehensive Survey and Experimental Study of Learning-based Community Search | out-topic | graph mining or graph learning algorithm |
| 220 | Decentralized Actor Scheduling and Reference-based Storage in Xorbits: a Native Scalable Data Science Engine | included | in scope as scheduling - see Included table |
| 221 | STsCache: An Efficient Semantic Caching Scheme for Time-series Data Workloads Based on Hybrid Storage | included | in scope as caching - see Included table |
| 222 | Cache Coherence Over Disaggregated Memory | out-machine | cache coherence protocol built on RDMA atomics over disaggregated memory across compute nodes |
| 223 | Triparts: Scalable Streaming Graph Partitioning to Enhance Community Structure | out-topic | streaming graph partitioning algorithm |
| 224 | The LDBC Financial Benchmark: Transaction Workload | out-topic | LDBC graph transaction benchmark specification |
| 225 | Alchemy: A Query Optimization Framework for Oblivious SQL | out-topic | privacy or security topic |
| 226 | DocETL: Agentic Query Rewriting and Evaluation for Complex Document Processing | out-topic | LLM application for data tasks - not a serving or inference system |
| 227 | HAKES: Scalable Vector Database for Embedding Search Service | out-topic | vector or similarity search indexing |
| 228 | Path-centric Cardinality Estimation for Subgraph Matching | out-topic | query optimization or estimation - not a systems resource-management topic |
| 229 | A Comprehensive Study of Shapley Value in Data Analytics | out-topic | study of Shapley value use in data analytics |
| 230 | Effective and Efficient Distributed Temporal Graph Learning through Hotspot Memory Sharing | out-machine | distributed temporal GNN training with shared node memory across machines and GPUs |
| 231 | Stochastic SketchRefine: Scaling In-Database Decision-Making under Uncertainty to Millions of Tuples | out-topic | algorithmic or language-level data management topic |
| 232 | CXL Memory Performance for In-Memory Data Processing | out-machine | measurement and placement study that requires CXL-attached memory devices |
| 233 | LLMLog: Advanced Log Template Generation via LLM-driven Multi-Round Annotation | out-topic | LLM-driven log template generation - log parsing accuracy not a systems artifact |
| 234 | Cuckoo Heavy Keeper and the balancing act of maintaining heavy hitters in stream processing | out-topic | concurrent sketch for heavy hitters - streaming approximation algorithm |
| 235 | Rebirth-Retire: A Concurrency Control Protocol Adaptable to Different Levels of Contention | out-topic | transaction replication or distributed protocol work |
| 236 | UFGTime: Mining Intertwined Dependencies in Multivariate Time Series via an Efficient Pure Graph Approach (Flavor: Foundations and Algorithms Papers) | out-topic | graph mining or graph learning algorithm |
| 237 | ArrayMorph: Optimizing Hyperslab Queries on the Cloud for Machine Learning Pipelines | included | in scope as storage - see Included table |
| 238 | Inference-friendly Graph Compression for Graph Neural Networks | out-topic | graph mining or graph learning algorithm |
| 239 | GpJSON: High-performance JSON Data Processing on GPUs | included | in scope as other-userspace - see Included table |
| 240 | Beyond Shortest Paths: Node Fairness in Route Recommendation | out-topic | graph mining or graph learning algorithm |
| 241 | Access Control for Information-Theoretically Secure Data | out-topic | privacy or security topic |
| 242 | Dynamic Range-Filtering Approximate Nearest Neighbor Search | out-topic | vector or similarity search indexing |
| 243 | LEGO-GraphRAG: Modularizing Graph-based Retrieval-Augmented Generation for Design Space Exploration | out-topic | LLM application for data tasks - not a serving or inference system |
| 244 | Déjà Vu: Efficient Video-Language Query Engine with Learning-based Inter-Frame Computation Reuse | included | in scope as ml-systems - see Included table |
| 245 | Parachute: Single-Pass Bi-Directional Information Passing | out-topic | query optimization or estimation - not a systems resource-management topic |
| 246 | Twisted Twin: A Collaborative and Competitive Memory Management Approach in HTAP Systems | out-no-code | memory manager evaluated inside the proprietary GaussDB-HTAP engine; PVLDB artifact flag is no and only a tech-report PDF is linked |
| 247 | Customization Meets 2-Hop Labeling: Efficient Routing in Road Networks | out-topic | graph mining or graph learning algorithm |
| 248 | X-Blossom: Massive Parallelization of Graph Maximum Matching | out-topic | graph mining or graph learning algorithm |
| 249 | Data Imputation with Limited Data Redundancy Using Data Lakes | out-topic | data imputation using data lakes |
| 250 | Chimera: Mitigating Ownership Transfers in Multi-Primary Shared-Storage Cloud-Native Databases | out-topic | transaction replication or distributed protocol work |
| 251 | Sectric: Towards Accurate, Privacy-preserving and Efficient Triangle Counting | out-topic | privacy or security topic |
| 252 | When Speed meets Accuracy: an Efficient and Effective  Graph Model for Temporal Link Prediction | out-topic | graph mining or graph learning algorithm |
| 253 | Improving Time Series Data Compression in Apache IoTDB | included | in scope as storage - see Included table |
| 254 | On LLM-Enhanced Mixed-Type Data Imputation with High-Order Message Passing | out-topic | LLM-enhanced mixed-type data imputation |
| 255 | Meaningful Data Erasure in the Presence of Dependencies | out-topic | semantics of data erasure under dependencies |
| 256 | Sonata: Multi-Database Transactions Made Fast and Serializable | out-topic | transaction replication or distributed protocol work |
| 257 | MOMENTI: Scalable Motif Mining in Multidimensional Time Series | out-topic | time-series or spatial data mining |
| 258 | How and Why False Denial Constraints are Discovered | out-topic | data cleaning integration or discovery |
| 259 | Efficient 𝑘-Clique Densest Subgraph Discovery: Towards Bridging Practice and Theory | out-topic | graph mining or graph learning algorithm |
| 260 | AutoPrep: Natural Language Question-Aware Data Preparation with a Multi-Agent Framework | out-topic | LLM application for data tasks - not a serving or inference system |
| 261 | Accelerating Approximate Nearest Neighbor Search in Hierarchical Graphs: Efficient Level Navigation with Shortcuts | out-topic | vector or similarity search indexing |
| 262 | Federated Incomplete Tabular Data Prediction with Missing Complementarity | out-topic | privacy or security topic |
| 263 | LakeVisage: Towards Scalable, Flexible and Interactive Visualization Recommendation for Data Discovery over Data Lakes | out-topic | data cleaning integration or discovery |
| 264 | PS-MI: Accurate, Efficient, and Private Data Valuation in Vertical Federated Learning | out-topic | privacy or security topic |
| 265 | Towards Pattern-aware Data Augmentation for Temporal Knowledge Graph Completion | out-topic | graph mining or graph learning algorithm |
| 266 | RapidStore: An Efficient Dynamic Graph Storage System for Concurrent Queries | included | in scope as other-userspace - see Included table |
| 267 | GORAM: Graph-oriented ORAM for Efficient Ego-centric Queries on Federated Graphs | out-topic | privacy or security topic |
| 268 | Authenticated Aggregate Queries with Boolean Range Predicates on Blockchains | out-topic | blockchain or BFT topic |
| 269 | FSMDTW: A Fast Index-free Subsequence Matching Algorithm for Dynamic Time Warping | out-topic | time-series or spatial data mining |
| 270 | Fused Gromov-Wasserstein Alignment for Graph Edit Distance Computation and Beyond | out-topic | graph mining or graph learning algorithm |
| 271 | EVOSCHEMA: TOWARDS TEXT-TO-SQL ROBUSTNESS AGAINST SCHEMA EVOLUTION | out-topic | LLM application for data tasks - not a serving or inference system |
| 272 | Effective and Efficient Community Search for Complex Network Semantics Capture: From Coarse-Grain to Fine-Grain | out-topic | graph mining or graph learning algorithm |
| 273 | HAWK: A Workload-driven Hierarchical Deadlock Detection Approach in Distributed Database System | out-topic | transaction replication or distributed protocol work |
| 274 | Doctopus: Budget-aware Structural Table Extraction from Unstructured Documents | out-topic | LLM application for data tasks - not a serving or inference system |
| 275 | S^3AND: Efficient Subgraph Similarity Search Under Aggregated Neighbor Difference Semantics | out-topic | graph mining or graph learning algorithm |
| 276 | Lighter-X: An Efficient and Plug-and-play Strategy for Graph-based Recommendation through Decoupled Propagation | out-topic | graph mining or graph learning algorithm |
| 277 | Not Small Enough? SegPQ: A Learned Approach to Compress Product Quantization Codebooks | out-topic | vector or similarity search indexing |
| 278 | The Accuracy of Cardinality Estimators: Unraveling the Evaluation Result Conundrum | out-topic | query optimization or estimation - not a systems resource-management topic |
| 279 | LogLite: Lightweight Plug-and-Play Streaming Log Compression | included | in scope as storage - see Included table |
| 280 | Enabling Efficient Attack Investigation via Human-in-the-Loop Security Analysis | out-topic | privacy or security topic |
| 281 | Shifting Transaction Isolation on Graphs: From Systems to Data | out-topic | transaction replication or distributed protocol work |
| 282 | Fast Graph Vector Search via Hardware Acceleration and Delayed-Synchronization Traversal | out-machine | vector search accelerator prototyped on FPGAs |
| 283 | Fremer: Lightweight and Effective Frequency Transformer for Workload Forecasting in Cloud Services | out-topic | time-series or spatial data mining |
| 284 | TabulaX: Leveraging Large Language Models for Multi-Class Table Transformations | out-topic | LLM application for data tasks - not a serving or inference system |
| 285 | Bonspiel: Low Tail Latency Transactions in Geo-Distributed Databases | out-topic | transaction replication or distributed protocol work |
| 286 | Efficient Graph Data Access for Out-of-Memory GPU Streaming Graph Processing | included | in scope as caching - see Included table |
| 287 | Extensible and Robust Evaluation of Similarity Queries | out-topic | query optimization or estimation - not a systems resource-management topic |
| 288 | PBench: Workload Synthesizer with Real Statistics for Cloud Analytics Benchmarking | out-topic | cloud analytics workload synthesizer - benchmarking tool |
| 289 | Accelerating Subgraph Matching through Fine-grained and Powerful Equivalences | out-topic | graph mining or graph learning algorithm |
| 290 | How to Optimize SQL Queries? A Comparison Between Split, Holistic, and Hybrid Approaches | out-topic | query optimization or estimation - not a systems resource-management topic |
| 291 | Diva: Dynamic Range Filter for Var-Length Keys and Queries | included | in scope as storage - see Included table |
| 292 | Approximate 2-hop neighborhoods on incremental graphs: An efficient lazy approach | out-topic | approximate 2-hop neighborhood maintenance - graph algorithm |
| 293 | Cracking Vector Search Indexes | out-topic | vector or similarity search indexing |
| 294 | DobLIX: A Dual-Objective Learned Index for Log-Structured Merge Trees | included | in scope as ml-for-systems - see Included table |
| 295 | CoLA: Model Collaboration for Log-based Anomaly Detection | out-topic | time-series or spatial data mining |
| 296 | Towards Designing Future-Proof Data Processing Systems | out-topic | vision paper with no reusable artifact |
| 297 | Advancing Fact Attribution for Query Answering: Aggregate Queries and Novel Algorithms | out-topic | query optimization or estimation - not a systems resource-management topic |
| 298 | What If: Causal Analysis with Graph Databases | out-topic | causal analysis on top of graph databases |
| 299 | AnyBlox: A Framework for Self-Decoding Datasets | included | in scope as storage - see Included table |
| 300 | Federated and Balanced Clustering for High-dimensional Data | out-topic | privacy or security topic |
| 301 | Relational Data Models for Genetic VCF data | out-topic | data cleaning integration or discovery |
| 302 | BURST: Rendering Clustering Techniques Suitable for Evolving Streams | out-topic | time-series or spatial data mining |
| 303 | Environmental Footprints of Query Processing: A Vision for Sustainable Database Architectures | out-topic | vision paper on sustainability with no artifact |
| 304 | Semantic Integrity Constraints: Declarative Guardrails for AI-Augmented Data Processing Systems | out-topic | query optimization or estimation - not a systems resource-management topic |
| 305 | RICH: Real-time Identification of negative Cycles for High-efficiency Arbitrage | out-topic | data science explanation or ML modelling topic |
| 306 | Balancing Privacy and Utility in Correlated Data: A Study of Bayesian Differential Privacy | out-topic | privacy or security topic |
| 307 | Enhancing Transaction Processing through Indirection Skipping | out-topic | transaction replication or distributed protocol work |
| 308 | UniClean: A Scalable Data Cleaning Solution for Mixed Errors based on Unified Cleaners and Optimized Cleaning Workflow | out-topic | data cleaning integration or discovery |
| 309 | ShaRP: Explaining Rankings and Preferences with Shapley Values | out-topic | data science explanation or ML modelling topic |
| 310 | SQLStorm: Taking Database Benchmarking into the LLM Era | out-topic | query optimization or estimation - not a systems resource-management topic |
| 311 | Suna: Scalable Causal Confounder Discovery over Relational Data | out-topic | data science explanation or ML modelling topic |
| 312 | Semantic Operators and Their Optimization:  Towards AI-Based Data Analytics with Accuracy Guarantees | out-topic | LLM application for data tasks - not a serving or inference system |
| 313 | Improving DBMS Scheduling Decisions with Accurate Performance Prediction on Concurrent Queries | included | in scope as scheduling - see Included table |
| 314 | Practical and Accurate Local Edge Differentially Private Graph Algorithms | out-topic | privacy or security topic |
| 315 | Continuous Publication of Weighted Graphs with Local Differential Privacy | out-topic | privacy or security topic |
| 316 | TxnSails: Achieving Serializable Transaction Scheduling with Self-Adaptive Isolation Level Selection | out-topic | transaction replication or distributed protocol work |
| 317 | No Cap, This Memory Slaps: Breaking Through the Memory Wall of Transactional Database Systems with Processing-in-Memory | out-machine | OLTP engine designed for processing-in-memory DRAM hardware (UPMEM-class) |
| 318 | GraphCSR: A Degree-Equalized CSR Format for Large-scale Graph Processing | included | in scope as memory - see Included table |
| 319 | Effective and Efficient Attributed Hypergraph Embedding on Nodes and Hyperedges | out-topic | graph mining or graph learning algorithm |
| 320 | Subgraph Matching: A New Decomposition Based Approach | out-topic | query optimization or estimation - not a systems resource-management topic |
| 321 | SSD-iq: Uncovering the Hidden Side of SSD Performance | out-machine | benchmark requires provisioning nine different datacenter SSD models and low-level device access |
| 322 | Faster Convergence in Mini-batch Graph Neural Networks Training with Pseudo Full Neighborhood Compensation | out-topic | graph mining or graph learning algorithm |
| 323 | TreeCat: Standalone Catalog Engine for Large Data Systems | included | in scope as storage - see Included table |
| 324 | Select Edges Wisely: Monotonic Path Aware Graph Layout Optimization for Disk-based ANN Search | included | in scope as storage - see Included table |
| 325 | Powerful GPUs or Fast Interconnects: Analyzing Relational Workloads on Modern GPUs | out-machine | benchmark requires RTX3090 plus A100 plus H100 plus GH200 and PCIe5 and NVLink interconnects |
| 326 | TSB-AutoAD: Towards Automated Solutions for Time-Series Anomaly Detection [E, A & B] | out-topic | time-series or spatial data mining |
| 327 | Time-Series Clustering: A Comprehensive Study of Data Mining, Machine Learning, and Deep Learning Methods | out-topic | time-series or spatial data mining |
| 328 | Beyond Compression: A Comprehensive Evaluation of Lossless Floating-Point Compression | included | in scope as storage - see Included table |
| 329 | ThriftLLM: On Cost-Effective Selection of Large Language Models for Classification Queries | out-topic | LLM application for data tasks - not a serving or inference system |
| 330 | Sphinx: A Succinct Perfect Hash Index for x86 | included | in scope as storage - see Included table |
| 331 | NaviX: A Native Vector Index Design for Graph DBMSs With Robust Predicate-Agnostic Search Performance | out-topic | vector index design inside a graph DBMS - vector indexing |
| 332 | DIM-SUM: Dynamic IMputation for Smart Utility Management | out-topic | time-series or spatial data mining |
| 333 | Robust Recursive Query Parallelism in Graph Database Management Systems | included | in scope as scheduling - see Included table |
| 334 | OasisDB: An Oblivious and Scalable System for Relational Data | out-topic | privacy or security topic |
| 335 | CEDAR: A System for Cost-Efficient Data-Driven Claim Verification | out-topic | LLM application for data tasks - not a serving or inference system |
| 336 | Benchmarking Adaptive Multidimensional Indices | out-topic | query optimization or estimation - not a systems resource-management topic |
| 337 | Scaling GPU-Accelerated Databases beyond GPU Memory Size | out-no-code | hybrid CPU-GPU out-of-core query strategy; PVLDB artifact flag is no and the only GitHub links are to the BlazingSQL and Spark-RAPIDS baselines |
| 338 | PAR2QO: Parametric Penalty-Aware Robust Query Optimization | out-topic | query optimization or estimation - not a systems resource-management topic |
| 339 | LIMAO: A Framework for Lifelong Modular Learned Query Optimization | out-topic | query optimization or estimation - not a systems resource-management topic |
| 340 | QUEST: Query Optimization in Unstructured Document Analysis | out-topic | query optimization or estimation - not a systems resource-management topic |
| 341 | CENTS: A Flexible and Cost-Effective Framework for LLM-Based Table Understanding | out-topic | LLM application for data tasks - not a serving or inference system |
| 342 | OmniMatch: Joinability Discovery in Data Products | out-topic | joinability discovery across tabular data products |
| 343 | Pistis: A Decentralized Knowledge Graph Platform Enabling Ownership-Preserving SPARQL Querying | out-topic | privacy or security topic |
| 344 | Selective Late Materialization in Modern Analytical Databases | out-topic | query optimization or estimation - not a systems resource-management topic |
| 345 | The FastLanes File Format | included | in scope as storage - see Included table |
| 346 | POLARIS: An Interactive and Scalable Data Infrastructure for Polar Science | out-topic | time-series or spatial data mining |
| 347 | Efficiently Joining Large Relations on Multi-GPU Systems | out-machine | multi-GPU sort-merge join relying on P2P interconnects between GPUs |
| 348 | Stress-Testing ML Pipelines with Adversarial Data Corruption | out-topic | adversarial data-corruption stress testing of ML pipelines |
| 349 | PrivAGM: Secure Construction of Differentially Private Directed Attributed Graph Models on Decentralized Social Graphs | out-topic | privacy or security topic |
| 350 | OmniSQL: Synthesizing High-quality Text-to-SQL Data at Scale | out-topic | text-to-SQL training data synthesis |
| 351 | Turbocharging Vector Databases using Modern SSDs | included | in scope as storage - see Included table |
| 352 | SIEVE: Effective Filtered Vector Search with Collection of Indexes | out-topic | filtered vector search with multiple indexes |
| 353 | Enhancing Graph Edit Distance Computation: Stronger and Orientation-based ILP Formulations | out-topic | graph mining or graph learning algorithm |
| 354 | ParSEval: Plan-aware Test Database Generation for SQL Equivalence Evaluation | out-topic | DBMS testing debugging or verification tooling |
