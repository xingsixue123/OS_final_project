STATUS: complete
TOTAL_PAPERS: 304
INCLUDED: 69

## Sources

- Primary enumeration: the official PVLDB volume 17 index at https://www.vldb.org/pvldb/volumes/17/ . The page is a Next.js app; I fetched the raw HTML with `curl` and parsed the embedded `__NEXT_DATA__` JSON, which carries every entry of issues 1-13 with title, authors, start/end page, PDF URL, abstract and artifact flag. Scratch files are in `scratch/` (`pvldb17_next.json`, `papers_all.json`, `papers_research.json`).
- VLDB 2024 (50th VLDB, Guangzhou, August 2024) presents PVLDB volume 17. The raw dump has 435 entries: 13 "Front Matter" records plus 422 papers.
- Track split: issue 12 (pages 3720-4556, 118 entries) is the special issue holding the industrial track, tutorials, demonstrations, panels, keynotes and vision talks - I listed all of its titles to confirm this. Issues 1-11 and 13 are the research track. 435 - 13 front matter - 118 issue-12 entries = **304 research-track papers**.
- Cross-check: DBLP (https://dblp.org/db/journals/pvldb/pvldb17.html) and its search API are behind an Anubis bot challenge and could not be fetched from this host, so I cross-checked completeness structurally instead: the parsed records tile the entire volume page range 1-4880 with **zero gaps and zero overlaps** across all 13 issues (verified programmatically), which means no paper is missing from the enumeration. DOIs (10.14778/...) extracted from each downloaded PDF give a second, per-paper confirmation against the ACM DL.
- Code check: I downloaded the PDFs of all 75 papers that survived the topic and machine screens and extracted the "PVLDB Artifact Availability" statement from each; that statement is the authoritative official-implementation link and is what appears in the Repo column. For the four papers with no such statement I additionally searched the web and GitHub before marking them `out-no-code`.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | ElasticNotebook: Enabling Live Migration for Computational Notebooks | https://doi.org/10.14778/3626292.3626296 | https://www.vldb.org/pvldb/vol17/p119-li.pdf | https://github.com/illinoisdata/ElasticNotebook | other-userspace | user-space checkpoint-restore of Python notebook sessions; pure Python, one machine, no root |
| 2 | An Empirical Evaluation of Columnar Storage Formats | https://doi.org/10.14778/3626292.3626298 | https://www.vldb.org/pvldb/vol17/p148-zeng.pdf | https://github.com/XinyuZeng/EvaluationOfColumnarFormats | storage | Parquet-ORC storage-format deep dive with a released benchmark harness; C++/Arrow builds in user space, GPU-decode part optional |
| 3 | ALECE: An Attention-based Learned Cardinality Estimator for SPJ Queries on Dynamic Workloads | https://doi.org/10.14778/3626292.3626302 | https://www.vldb.org/pvldb/vol17/p197-li.pdf | https://github.com/pfl-cs/ALECE | ml-for-systems | learned cardinality estimator wired into PostgreSQL; single node, fits 24 GB GPU |
| 4 | Flash-LLM: Enabling Low-Cost and Highly-Efficient Large Generative Model Inference With Unstructured Sparsity | https://doi.org/10.14778/3626292.3626303 | https://www.vldb.org/pvldb/vol17/p211-xia.pdf | https://github.com/AlibabaResearch/flash-llm | llm-inference | unstructured-sparsity SpMM kernels for generative inference; A5000 is Ampere so FP16 tensor cores work and no FP8 is needed. Concern: paper uses A100 80GB with OPT-30B/66B, so a 7B-class scale-down is required |
| 5 | SmartLite: A DBMS-based Serving System for DNN Inference in Resource-constrained Environments | https://doi.org/10.14778/3632093.3632095 | https://www.vldb.org/pvldb/vol17/p278-wu.pdf | https://github.com/lynn2089/SmartLite | ml-systems | DNN serving inside a lightweight DBMS for resource-constrained devices; CPU-only and scales down naturally |
| 6 | NeutronStream: A Dynamic GNN Training Framework with Sliding Window for Graph Streams | https://doi.org/10.14778/3632093.3632108 | https://www.vldb.org/pvldb/vol17/p455-chen.pdf | https://github.com/iDC-NEU/NeutronStream | ml-systems | dynamic GNN training framework; single machine CPU + one GPU |
| 7 | An Efficient Transfer Learning Based Configuration Adviser for Database Tuning | https://doi.org/10.14778/3632093.3632114 | https://www.vldb.org/pvldb/vol17/p539-zhang.pdf | https://github.com/Blairruc-pku/OpAdviser | ml-for-systems | transfer-learning knob adviser for DBMS tuning; PostgreSQL/MySQL run in user space |
| 8 | RALF: Accuracy-Aware Scheduling for Feature Store Maintenance | https://doi.org/10.14778/3632093.3632116 | https://www.vldb.org/pvldb/vol17/p563-wooders.pdf | https://github.com/feature-store/ralf | scheduling | accuracy-aware scheduling policy for feature-store maintenance. Concern: paper runs on 800 cores, so the policy must be re-evaluated at reduced scale or on traces |
| 9 | The Art of Latency Hiding in Modern Database Engines | https://doi.org/10.14778/3632093.3632117 | https://www.vldb.org/pvldb/vol17/p577-huang.pdf | https://github.com/sfu-dis/mosaicdb | other-userspace | stackless coroutines plus scheduling to hide I/O and synchronization latency in an OLTP engine; user-space C++, no root |
| 10 | TVM: A Tile-based Video Management Framework | https://doi.org/10.14778/3636218.3636224 | https://www.vldb.org/pvldb/vol17/p671-zhang.pdf | https://github.com/InkosiZhong/TVM | other-userspace | tile-based video storage and semantic index that cuts decoded data volume; single machine, GPU used for the DNN oracle |
| 11 | Sample-Efficient Cardinality Estimation Using Geometric Deep Learning | https://doi.org/10.14778/3636218.3636229 | https://www.vldb.org/pvldb/vol17/p740-reiner.pdf | https://github.com/dbis-ukon/jgmp | ml-for-systems | geometric deep learning cardinality estimator with an end-to-end PostgreSQL benchmark |
| 12 | Algorithmic Complexity Attacks on Dynamic Learned Indexes | https://doi.org/10.14778/3636218.3636232 | https://www.vldb.org/pvldb/vol17/p780-yang.pdf | https://github.com/ds2-lab/aca-dlis | ml-for-systems | complexity attacks on the ALEX dynamic learned index; pure user-space C++ experiments |
| 13 | Experimental Analysis of Large-scale Learnable Vector Storage Compression | https://doi.org/10.14778/3636218.3636234 | https://www.vldb.org/pvldb/vol17/p808-zhang.pdf | https://github.com/HugoZHL/Hetu/tree/embedmem/tools/EmbeddingMemoryCompression | ml-systems | modular benchmark of 14 embedding-compression methods. Concern: full recommender datasets are large, scale-down likely needed |
| 14 | A Comparative Study and Component Analysis of Query Plan Representation Techniques in ML4DB Studies | https://doi.org/10.14778/3636218.3636235 | https://www.vldb.org/pvldb/vol17/p823-zhao.pdf | https://github.com/zhaoyue-ntu/qp_evaluation | ml-for-systems | component analysis of query-plan representation models used in ML-for-DB work; released evaluation testbed |
| 15 | FusionFlow: Accelerating Data Preprocessing for Machine Learning with CPU-GPU Cooperation | https://doi.org/10.14778/3636218.3636238 | https://www.vldb.org/pvldb/vol17/p863-kim.pdf | https://github.com/omnia-unist/FusionFlow | ml-systems | CPU-GPU cooperative data-preprocessing scheduler for DL training. Concern: multi-GPU results are not reproducible, single-GPU path is |
| 16 | BOSS - An Architecture for Database Kernel Composition | https://doi.org/10.14778/3636218.3636239 | https://www.vldb.org/pvldb/vol17/p877-mohr-daurat.pdf | https://github.com/lsds/MultiKernelBOSS | other-userspace | composable DBMS kernel architecture gluing Arrow, Velox and ArrayFire; builds in user space, one GPU |
| 17 | CoroGraph: Bridging Cache Efficiency and Work Efficiency for Graph Algorithm Execution | https://doi.org/10.14778/3636218.3636240 | https://www.vldb.org/pvldb/vol17/p891-zhi.pdf | https://github.com/DBGroup-SUSTech/corograph | other-userspace | coroutine-based software prefetching and cache-efficient in-memory graph engine; CPU only |
| 18 | Eraser: Eliminating Performance Regression on Learned Query Optimizer | https://doi.org/10.14778/3641204.3641205 | https://www.vldb.org/pvldb/vol17/p926-zhu.pdf | https://github.com/duoyw/Eraser | ml-for-systems | eliminating performance regressions of learned query optimizers on PostgreSQL |
| 19 | PilotScope: Steering Databases with Machine Learning Drivers | https://doi.org/10.14778/3641204.3641209 | https://www.vldb.org/pvldb/vol17/p980-zhu.pdf | https://github.com/alibaba/pilotscope | ml-for-systems | platform for plugging ML drivers into PostgreSQL/openGauss; strong base for an improvement project |
| 20 | Database Native Model Selection: Harnessing Deep Neural Networks in Database Systems | https://doi.org/10.14778/3641204.3641212 | https://www.vldb.org/pvldb/vol17/p1020-xing.pdf | https://github.com/nusdbsystem/Trails | ml-systems | in-database neural model selection; single GPU is enough |
| 21 | ETC: Efficient Training of Temporal Graph Neural Networks over Large-scale Dynamic Graphs | https://doi.org/10.14778/3641204.3641215 | https://www.vldb.org/pvldb/vol17/p1060-gao.pdf | https://github.com/eddiegaoo/ETC | ml-systems | temporal GNN training system for large dynamic graphs; single machine GPU |
| 22 | Comprehensive Evaluation of GNN Training Systems: A Data Management Perspective | https://doi.org/10.14778/3648160.3648167 | https://www.vldb.org/pvldb/vol17/p1241-yuan.pdf | https://github.com/iDC-NEU/NeutronBench | ml-systems | systematic evaluation of GNN training systems from a data-management perspective. Concern: distributed configurations must be dropped |
| 23 | DAHA: Accelerating GNN Training with Data and Hardware Aware Execution Planning | https://doi.org/10.14778/3648160.3648176 | https://www.vldb.org/pvldb/vol17/p1364-li.pdf | https://github.com/fr8nkL/DAHA | ml-systems | cost-model-driven execution planning and pipelining for GNN training on CPU-GPU |
| 24 | CGgraph: An Ultra-fast Graph Processing System on Modern Commodity CPU-GPU Co-processor | https://doi.org/10.14778/3648160.3648179 | https://www.vldb.org/pvldb/vol17/p1405-yuan.pdf | https://github.com/DBGroup-SUSTech/CGgraph | other-userspace | CPU-GPU cooperative graph engine that handles GPU memory oversubscription; one GPU is the target setting |
| 25 | FCBench: Cross-Domain Benchmarking of Lossless Compression for Floating-point Data | https://doi.org/10.14778/3648160.3648180 | https://www.vldb.org/pvldb/vol17/p1418-tao.pdf | https://github.com/hipdac-lab/FCBench | storage | cross-domain lossless floating-point compression benchmark with CPU and GPU codecs. Concern: the roofline analysis uses hardware counters that are blocked here |
| 26 | MetaStore: Analyzing Deep Learning Meta-Data at Scale | https://doi.org/10.14778/3648160.3648182 | https://www.vldb.org/pvldb/vol17/p1446-cao.pdf | https://github.com/Mazic4/MetaStore | ml-systems | system for storing and analyzing deep-learning gradient metadata at scale; single machine with one GPU |
| 27 | RTScan:  Efficient Scan with Ray Tracing Cores | https://doi.org/10.14778/3648160.3648183 | https://www.vldb.org/pvldb/vol17/p1460-lv.pdf | https://github.com/AntaresAlice/RTScan | other-userspace | index scan offloaded to GPU ray-tracing cores; the A5000 is Ampere and has RT cores, OptiX works on driver 535 |
| 28 | FreshGNN: Reducing Memory Access via Stable Historical Embeddings for Graph Neural Network Training | https://doi.org/10.14778/3648160.3648184 | https://www.vldb.org/pvldb/vol17/p1473-huang.pdf | https://github.com/xxcclong/history-cache | ml-systems | historical-embedding cache policy that cuts feature loading in GNN mini-batch training; single-GPU configuration exists |
| 29 | AeonG: An Efficient Built-in Temporal Support in Graph Databases | https://doi.org/10.14778/3648160.3648187 | https://www.vldb.org/pvldb/vol17/p1515-lu.pdf | https://github.com/hououou/AeonG | storage | built-in temporal storage support in a graph database; JVM installable through conda |
| 30 | Refactoring Index Tuning Process with Benefit Estimation | https://doi.org/10.14778/3654621.3654622 | https://www.vldb.org/pvldb/vol17/p1528-zou.pdf | https://github.com/HIT-DB-Group/RIBE | ml-for-systems | learned benefit estimation that skips what-if calls during index tuning |
| 31 | Is Your Learned Query Optimizer Behaving As You Expect? A Machine Learning Perspective | https://doi.org/10.14778/3654621.3654625 | https://www.vldb.org/pvldb/vol17/p1565-lehmann.pdf | https://github.com/edualc/lqo_ml_perspective | ml-for-systems | critical re-evaluation of learned query optimizers; released harness makes a careful reproduction straightforward |
| 32 | Leveraging Dynamic and Heterogeneous Workload Knowledge to Boost the Performance of Index Advisors | https://doi.org/10.14778/3654621.3654631 | https://www.vldb.org/pvldb/vol17/p1642-lin.pdf | https://github.com/XMUDM/BALANCE | ml-for-systems | learning-based index advisor for dynamic and heterogeneous workloads |
| 33 | FlowWalker: A Memory-efficient and High-performance GPU-based Dynamic Graph Random Walk Framework | https://doi.org/10.14778/3659437.3659438 | https://www.vldb.org/pvldb/vol17/p1788-mei.pdf | https://github.com/junyimei/flowwalker-artifact | other-userspace | GPU dynamic-graph random-walk engine with sampler-centric scheduling; one GPU |
| 34 | InferDB: In-Database Machine Learning Inference Using Indexes | https://doi.org/10.14778/3659437.3659441 | https://www.vldb.org/pvldb/vol17/p1830-salazar-diaz.pdf | https://github.com/hpides/inferdb | ml-systems | index-based approximation of end-to-end ML inference pipelines inside PostgreSQL |
| 35 | Oasis: An Optimal Disjoint Segmented Learned Range Filter | https://doi.org/10.14778/3659437.3659447 | https://www.vldb.org/pvldb/vol17/p1911-luo.pdf | https://github.com/Woooooow-Pro/Oasis-RangeFilter | storage | learned range filter integrated into RocksDB; a clean single-machine storage project |
| 36 | GPTuner: A Manual-Reading Database Tuning System via GPT-Guided Bayesian Optimization | https://doi.org/10.14778/3659437.3659449 | https://www.vldb.org/pvldb/vol17/p1939-tang.pdf | https://github.com/SolidLao/GPTuner | ml-for-systems | LLM-guided Bayesian optimization of DBMS knobs. Concern: needs an LLM endpoint or a local 7B model |
| 37 | NeutronOrch: Rethinking Sample-based GNN Training under CPU-GPU Heterogeneous Environments | https://doi.org/10.14778/3659437.3659453 | https://www.vldb.org/pvldb/vol17/p1995-ai.pdf | https://github.com/AiX-im/Sample-based-GNN | ml-systems | CPU-GPU task orchestration for sample-based GNN training |
| 38 | Everything You Always Wanted to Know About Storage Compressibility of Pre-Trained ML Models but Were Afraid to Ask | https://doi.org/10.14778/3659437.3659456 | https://www.vldb.org/pvldb/vol17/p2036-su.pdf | https://github.com/ds2-lab/ELF | storage | deduplication and compression study of pre-trained model files; needs tens of GB of downloads but 257 GB free is enough |
| 39 | SeLeP: Learning Based Semantic Prefetching for Exploratory Database Workloads | https://doi.org/10.14778/3659437.3659458 | https://www.vldb.org/pvldb/vol17/p2064-zirak.pdf | https://github.com/fzirak/SeLeP | ml-for-systems | learned semantic prefetcher for exploratory database workloads |
| 40 | Visualization-aware Time Series Min-Max Caching with Error Bound Guarantees | https://doi.org/10.14778/3659437.3659460 | https://www.vldb.org/pvldb/vol17/p2091-maroulis.pdf | https://github.com/athenarc/MinMaxCache | caching | adaptive in-memory min-max cache with error bounds for time-series visualization |
| 41 | SplitDF: Splitting Dataframes for Memory-Efficient Data Analysis | https://doi.org/10.14778/3665844.3665849 | https://www.vldb.org/pvldb/vol17/p2175-kakaraparthy.pdf | https://github.com/UWQuickstep/splitting | memory | memory-footprint reduction for dataframes on DuckDB/Ibis; user-space Python |
| 42 | Improving Graph Compression for Efficient Resource-Constrained Graph Analytics | https://doi.org/10.14778/3665844.3665852 | https://www.vldb.org/pvldb/vol17/p2212-xu.pdf | https://github.com/xuqianmamba/Laconic | memory | rule-based graph compression that cuts peak memory during both compression and computation; CPU only |
| 43 | GENTI: GPU-powered Walk-based Subgraph Extraction for Scalable Representation Learning on Dynamic Graphs | https://doi.org/10.14778/3665844.3665856 | https://www.vldb.org/pvldb/vol17/p2269-yu.pdf | https://github.com/gdmnl/GENTI | ml-systems | GPU subgraph-extraction pipeline for representation learning on dynamic graphs |
| 44 | Breaking It Down: An In-depth Study of Index Advisors | https://doi.org/10.14778/3675034.3675035 | https://www.vldb.org/pvldb/vol17/p2405-li.pdf | https://github.com/XMUDM/Index_EAB | ml-for-systems | open testbed implementing 17 index advisors; excellent reproduction or improvement base |
| 45 | D-Bot: Database Diagnosis System using Large Language Models | https://doi.org/10.14778/3675034.3675043 | https://www.vldb.org/pvldb/vol17/p2514-li.pdf | https://github.com/TsinghuaDatabaseGroup/DB-GPT | ml-for-systems | LLM-based DBMS diagnosis agent; can run against a local PostgreSQL. Concern: needs an LLM endpoint |
| 46 | Blitzcrank: Fast Semantic Compression for In-memory Online Transaction Processing | https://doi.org/10.14778/3675034.3675044 | https://www.vldb.org/pvldb/vol17/p2528-zhang.pdf | https://github.com/YimingQiao/Blitzcrank | storage | semantic compression for in-memory OLTP row stores; user-space C++ with TPC-C evaluation |
| 47 | Biathlon: Harnessing Model Resilience for Accelerating ML Inference Pipelines | https://doi.org/10.14778/3675034.3675052 | https://www.vldb.org/pvldb/vol17/p2631-lo.pdf | https://github.com/ChaokunChang/Biathlon | ml-systems | ML serving system that trades feature approximation for latency under accuracy bounds |
| 48 | Towards Optimal Transaction Scheduling | https://doi.org/10.14778/3681954.3681956 | https://www.vldb.org/pvldb/vol17/p2694-cheng.pdf | https://github.com/audreyccheng/transaction-scheduling | scheduling | schedule-first concurrency control and greedy schedule search implemented in RocksDB; single machine |
| 49 | RoarGraph: A Projected Bipartite Graph for Efficient Cross-Modal Approximate Nearest Neighbor Search | https://doi.org/10.14778/3681954.3681959 | https://www.vldb.org/pvldb/vol17/p2735-chen.pdf | https://github.com/matchyc/RoarGraph | storage | cross-modal ANN graph index; single-machine memory-bound C++. Concern: ANN indexing is a borderline fit for the topic table |
| 50 | Eliminating Data Processing Bottlenecks in GNN Training over Large Graphs via Two-level Feature Compression | https://doi.org/10.14778/3681954.3681968 | https://www.vldb.org/pvldb/vol17/p2854-gong.pdf | https://github.com/gpzlx1/F2CGT | ml-systems | two-level feature compression plus GPU cache co-design for GNN training; single-GPU config available |
| 51 | Towards Systematic Index Dynamization | https://doi.org/10.14778/3681954.3681969 | https://www.vldb.org/pvldb/vol17/p2867-rumbaugh.pdf | https://github.com/psu-db/dynamic-extension | storage | framework that turns static indexes into updatable ones; user-space C++ library |
| 52 | OUTRE: An OUT-of-core De-REdundancy GNN Training Framework for Massive Graphs within A Single Machine | https://doi.org/10.14778/3681954.3681976 | https://www.vldb.org/pvldb/vol17/p2960-sheng.pdf | https://github.com/PKU-DAIR/OUTRE | ml-systems | out-of-core GNN training explicitly designed for a single machine |
| 53 | On Reducing Space Amplification with Multi-Column Compaction in Apache IoTDB | https://doi.org/10.14778/3681954.3681977 | https://www.vldb.org/pvldb/vol17/p2974-song.pdf | https://github.com/column-compaction/column-compaction | storage | multi-column LSM-tree compaction policy in Apache IoTDB; JVM, single node, classic storage project |
| 54 | When Amnesia Strikes: Understanding and Reproducing Data Loss Bugs with Fault Injection | https://doi.org/10.14778/3681954.3681980 | https://www.vldb.org/pvldb/vol17/p3017-ramos.pdf | https://github.com/dsrhaslab/lazyfs | storage | FUSE-based fault-injection file system; /dev/fuse is world-writable and fusermount3 is setuid so it runs unprivileged |
| 55 | Two Birds With One Stone: Designing a Hybrid Cloud Storage Engine for HTAP | https://doi.org/10.14778/3681954.3682001 | https://www.vldb.org/pvldb/vol17/p3290-schmidt.pdf | https://github.com/umbra-db/colibri-vldb2024 | storage | hybrid column-row cloud storage engine for HTAP. Concern: object-store experiments need a user-space substitute such as MinIO |
| 56 | The Holon Approach for Simultaneously Tuning Multiple Components in a Self-Driving Database Management System with Machine Learning via Synthesized Proto-Actions | https://doi.org/10.14778/3681954.3682007 | https://www.vldb.org/pvldb/vol17/p3373-zhang.pdf | https://github.com/17zhangw/protox | ml-for-systems | holistic RL tuning across knobs, indexes and query hints on PostgreSQL. Concern: tuning runs are long |
| 57 | LITS: An Optimized Learned Index for Strings | https://doi.org/10.14778/3681954.3682010 | https://www.vldb.org/pvldb/vol17/p3415-chen.pdf | https://github.com/schencoding/lits | ml-for-systems | learned index for variable-length string keys; user-space C++ benchmark against ART and HOT |
| 58 | OLAP on Modern Chiplet-Based Processors | https://doi.org/10.14778/3681954.3682011 | https://www.vldb.org/pvldb/vol17/p3428-fogli.pdf | https://github.com/Alessandro727/OLAP-on-Modern-Chiplet-Based-CPUs | scheduling | chiplet-aware task placement for query engines; the target machine is a multi-CCD Threadripper PRO so the effect is present. Concern: part of the analysis relies on hardware counters that are blocked |
| 59 | Partition, Don't Sort! Compression Boosters for Cloud Data Ingestion Pipelines | https://doi.org/10.14778/3681954.3682013 | https://www.vldb.org/pvldb/vol17/p3456-hansert.pdf | https://github.com/dbislab/Partition-Dont-Sort | storage | clustering-based compression booster for nested-data ingestion; CPU only |
| 60 | Hardware-Efficient Data Imputation through DBMS Extensibility | https://doi.org/10.14778/3681954.3682016 | https://www.vldb.org/pvldb/vol17/p3497-mohr-daurat.pdf | https://github.com/lsds/ImputationBOSS | other-userspace | shape-wise microbatching execution model inside the BOSS DBMS kernel; user-space C++ |
| 61 | Optimizing Collections of Bloom Filters within a Space Budget | https://doi.org/10.14778/3681954.3682020 | https://www.vldb.org/pvldb/vol17/p3551-mersy.pdf | https://github.com/gmersy/truncated-bloom-filter | storage | joint space allocation across a collection of Bloom filters; small self-contained user-space artifact |
| 62 | A Spark Optimizer for Adaptive, Fine-Grained Parameter Tuning | https://doi.org/10.14778/3681954.3682021 | https://www.vldb.org/pvldb/vol17/p3565-lyu.pdf | https://github.com/udao-moo/udao-spark-optimizer | ml-for-systems | multi-objective ML tuning of Spark adaptive-query-execution parameters; Spark runs local or pseudo-distributed |
| 63 | Aleph Filter: To Infinity in Constant Time | https://doi.org/10.14778/3681954.3682027 | https://www.vldb.org/pvldb/vol17/p3644-dayan.pdf | https://github.com/nivdayan/AlephFilter | storage | expandable filter with constant-time operations under growth; user-space C++ |
| 64 | Hit the Gym: Accelerating Query Execution to Efficiently Bootstrap Behavior Models for Self-Driving Database Management Systems | https://doi.org/10.14778/3681954.3682030 | https://www.vldb.org/pvldb/vol17/p3680-lim.pdf | https://github.com/lmwnshn/boot | ml-for-systems | accelerated training-data collection for self-driving DBMS behaviour models on PostgreSQL |
| 65 | The Case for DBMS Live Patching | https://doi.org/10.14778/3704965.3704966 | https://www.vldb.org/pvldb/vol17/p4557-fruth.pdf | https://github.com/sdbs-uni-p/vldb25-dbms-live-patching | other-userspace | user-space live patching of DBMS binaries via libpulp; no kernel module needed. Concern: confirm that the patching path works without extra privileges |
| 66 | CausalMesh: A Causal Cache for Stateful Serverless Computing | https://doi.org/10.14778/3704965.3704969 | https://www.vldb.org/pvldb/vol17/p4599-zhang.pdf | https://github.com/eniac/causalmesh | caching | causally consistent cache for stateful serverless workflows; the multi-server topology can be emulated with several processes on one host |
| 67 | Scalable Model-Based Management of Massive High Frequency Wind Turbine Data with ModelarDB | https://doi.org/10.14778/3704965.3704978 | https://www.vldb.org/pvldb/vol17/p4723-abduvakhobov.pdf | https://github.com/aabduvakhobov/ModelarDB-Analyzer | storage | model-based time-series compression evaluation in Rust. Concern: the edge-to-cloud pipeline must be collapsed onto one host |
| 68 | Powering In-Database Dynamic Model Slicing for Structured Data Analytics | https://doi.org/10.14778/3704965.3704985 | https://www.vldb.org/pvldb/vol17/p4813-zeng.pdf | https://github.com/NLGithubWP/indices | ml-systems | in-database dynamic model slicing shipped as a PostgreSQL extension in Rust |
| 69 | GastCoCo: Graph Storage and Coroutine-Based Prefetch Co-Design for Dynamic Graph Processing | https://doi.org/10.14778/3704965.3704986 | https://www.vldb.org/pvldb/vol17/p4827-li.pdf | https://github.com/GorgeouszzZ/GastCoCo | other-userspace | coroutine-based prefetching and graph storage co-design that targets cache misses; CPU only |

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | DecLog: Decentralized Logging in Non-Volatile Memory for Time Series Database Systems | out-machine | core contribution is logging on byte-addressable NVM - no persistent memory on this machine |
| 2 | Efficient Dynamic Weighted Set Sampling and Its Extension | out-topic | sampling algorithm |
| 3 | ZIP: Lazy Imputation during Query Processing | out-topic | query-time data imputation |
| 4 | FedGTA: Topology-aware Averaging for Federated Graph Learning | out-topic | federated graph learning method |
| 5 | Host Profit Maximization: Leveraging Performance Incentives and User Flexibility | out-topic | influence/incentive optimization problem |
| 6 | DP-PQD: Privately Detecting Per-Query Gaps In Synthetic Data Generated By Black-Box Mechanisms | out-topic | differential privacy |
| 7 | Cryptographically Secure Private Record Linkage Using Locality-Sensitive Hashing | out-topic | privacy-preserving record linkage |
| 8 | Language Models Enable Simple Systems for Generating Structured Views of Heterogeneous Data Lakes | out-topic | LLM-based data extraction application, not an inference system |
| 9 | Query Refinement for Diversity Constraint Satisfaction | out-topic | query refinement semantics |
| 10 | ElasticNotebook: Enabling Live Migration for Computational Notebooks | included | user-space checkpoint-restore of Python notebook sessions; pure Python, one machine, no root |
| 11 | Breathing New Life into An Old Tree: Resolving Logging Dilemma of $B^{+}$-tree on Modern Computational Storage Drives | out-machine | requires computational storage drives with in-drive compute |
| 12 | An Empirical Evaluation of Columnar Storage Formats | included | Parquet-ORC storage-format deep dive with a released benchmark harness; C++/Arrow builds in user space, GPU-decode part optional |
| 13 | Everest: GPU-Accelerated System For Mining Temporal Motifs | out-topic | temporal motif mining algorithm |
| 14 | Billion-Scale Bipartite Graph Embedding: A Global-Local Induced Approach | out-topic | graph embedding method |
| 15 | Utility-aware Payment Channel Network Rebalance | out-topic | blockchain payment channels |
| 16 | ALECE: An Attention-based Learned Cardinality Estimator for SPJ Queries on Dynamic Workloads | included | learned cardinality estimator wired into PostgreSQL; single node, fits 24 GB GPU |
| 17 | Flash-LLM: Enabling Low-Cost and Highly-Efficient Large Generative Model Inference With Unstructured Sparsity | included | unstructured-sparsity SpMM kernels for generative inference; A5000 is Ampere so FP16 tensor cores work and no FP8 is needed |
| 18 | Confidential Consortium Framework: Secure Multiparty Applications with Confidentiality, Integrity, and High Availability | out-machine | requires hardware trusted execution environments plus a multi-node replicated deployment |
| 19 | VeLP: Vehicle Loading Plan Learning from Human Behavior in Nationwide Logistics System | out-topic | logistics prediction application |
| 20 | Relational Query Synthesis ⋈ Decision Tree Learning | out-topic | program synthesis for SQL |
| 21 | RAGraph: A Region-Aware Framework for Geo-Distributed Graph Processing | out-machine | geo-distributed multi-datacenter graph processing |
| 22 | SmartLite: A DBMS-based Serving System for DNN Inference in Resource-constrained Environments | included | DNN serving inside a lightweight DBMS for resource-constrained devices; CPU-only and scales down naturally |
| 23 | Blocker and Matcher Can Mutually Benefit: A Co-Learning Framework for Low-Resource Entity Resolution | out-topic | entity resolution method |
| 24 | TSGBench: Time Series Generation Benchmark | out-topic | time-series generation benchmark |
| 25 | OmniSketch: Efficient Multi-Dimensional High-Velocity Stream Analytics with Arbitrary Predicates | out-topic | streaming sketch algorithm |
| 26 | Maximum Balanced (k, ε)-Bitruss Detection in Signed Bipartite Graph | out-topic | graph mining algorithm |
| 27 | Missing Value Imputation for Multi-attribute Sensor Data Streams via Message Propagation | out-topic | stream imputation method |
| 28 | ImDiffusion: Imputed Diffusion Models for Multivariate Time Series Anomaly Detection | out-topic | time-series anomaly detection model |
| 29 | Confidence Intervals for Private Query Processing | out-topic | differential privacy |
| 30 | A Shapelet-based Framework for Unsupervised Multivariate Time Series Representation Learning | out-topic | time-series representation learning |
| 31 | Fast and Space-Efficient Parallel Algorithms for Influence Maximization | out-topic | influence maximization algorithm |
| 32 | TERI: An Effective Framework for Trajectory Recovery with Irregular Time Intervals | out-topic | trajectory recovery model |
| 33 | Demystifying Graph Sparsification Algorithms in Graph Properties Preservation | out-topic | graph sparsification algorithm study |
| 34 | GPU Database Systems Characterization and Optimization | out-machine | characterization relies on Multi-Instance GPU partitioning and micro-architectural hardware counters - MIG is unsupported on an A5000 and perf counters are blocked |
| 35 | NeutronStream: A Dynamic GNN Training Framework with Sliding Window for Graph Streams | included | dynamic GNN training framework; single machine CPU + one GPU |
| 36 | Caerus: Low-Latency Distributed Transactions for Geo-Replicated Systems | out-machine | geo-replicated multi-node transaction protocol |
| 37 | An Experimental Evaluation of Anomaly Detection in Time Series | out-topic | time-series anomaly detection evaluation |
| 38 | FormaT5: Abstention and Examples for Conditional Table Formatting with Natural Language | out-topic | LLM table-formatting application |
| 39 | Quantum-Inspired Digital Annealing for Join Ordering | out-machine | evaluation runs on Fujitsu quantum-inspired digital annealing hardware |
| 40 | KAMEL: A Scalable BERT-based System for Trajectory Imputation | out-topic | trajectory imputation model |
| 41 | An Efficient Transfer Learning Based Configuration Adviser for Database Tuning | included | transfer-learning knob adviser for DBMS tuning; PostgreSQL/MySQL run in user space |
| 42 | ADF & TransApp: A Transformer-Based Framework for Appliance Detection Using Smart Meter Consumption Series | out-topic | appliance detection model |
| 43 | RALF: Accuracy-Aware Scheduling for Feature Store Maintenance | included | accuracy-aware scheduling policy for feature-store maintenance |
| 44 | The Art of Latency Hiding in Modern Database Engines | included | stackless coroutines plus scheduling to hide I/O and synchronization latency in an OLTP engine; user-space C++, no root |
| 45 | MOSER: Scalable Network Motif Discovery using Serial Test | out-topic | network motif discovery algorithm |
| 46 | Co-movement Pattern Mining from Videos | out-topic | video pattern mining semantics |
| 47 | Efficient and Accurate SimRank-based Similarity Joins: Experiments, Analysis, and Improvement | out-topic | similarity join algorithm |
| 48 | Expanding Reverse Nearest Neighbors | out-topic | nearest-neighbour query semantics |
| 49 | Errata for "SpaceSaving±: An Optimal Algorithm for Frequency Estimation and Frequent Items in the Bounded-Deletion Model" | out-topic | errata note on a sketching algorithm |
| 50 | Cache-Efficient Top-k Aggregation over High Cardinality Large Datasets | out-no-code | checked the PDF (no PVLDB artifact-availability statement), the PVLDB volume-17 artifact flag (no) and GitHub search for Zippy - no released implementation found |
| 51 | Efficient Temporal Butterfly Counting and Enumeration on Temporal Bipartite Graphs | out-topic | graph counting algorithm |
| 52 | TVM: A Tile-based Video Management Framework | included | tile-based video storage and semantic index that cuts decoded data volume; single machine, GPU used for the DNN oracle |
| 53 | ScienceBenchmark: A Complex Real-World Benchmark for Evaluating Natural Language to SQL Systems | out-topic | NL2SQL benchmark |
| 54 | Densest Multipartite Subgraph Search in Heterogeneous Information Networks | out-topic | subgraph search algorithm |
| 55 | Saturn: An Optimized Data System for Multi-Large-Model Deep Learning Workloads | out-machine | the whole point is choosing model-parallelism strategies across many GPUs - no meaningful single-GPU scale-down |
| 56 | BonsaiKV: Towards Fast, Scalable, and Persistent Key-Value Stores with Tiered, Heterogeneous Memory System | out-machine | requires NVMM plus CXL tiered heterogeneous memory hardware |
| 57 | Sample-Efficient Cardinality Estimation Using Geometric Deep Learning | included | geometric deep learning cardinality estimator with an end-to-end PostgreSQL benchmark |
| 58 | Multiple Time Series Forecasting with Dynamic Graph Modeling | out-topic | time-series forecasting model |
| 59 | Weakly Guided Adaptation for Robust Time Series Forecasting | out-topic | time-series forecasting model |
| 60 | Algorithmic Complexity Attacks on Dynamic Learned Indexes | included | complexity attacks on the ALEX dynamic learned index; pure user-space C++ experiments |
| 61 | METER: A Dynamic Concept Adaptation Framework for Online Anomaly Detection | out-topic | online anomaly detection model |
| 62 | Experimental Analysis of Large-scale Learnable Vector Storage Compression | included | modular benchmark of 14 embedding-compression methods |
| 63 | A Comparative Study and Component Analysis of Query Plan Representation Techniques in ML4DB Studies | included | component analysis of query-plan representation models used in ML-for-DB work; released evaluation testbed |
| 64 | Testing Graph Database Systems via Graph-Aware Metamorphic Relations | out-topic | metamorphic testing of graph DBMSs |
| 65 | Observatory: Characterizing Embeddings of Relational Tables | out-topic | table embedding characterization |
| 66 | FusionFlow: Accelerating Data Preprocessing for Machine Learning with CPU-GPU Cooperation | included | CPU-GPU cooperative data-preprocessing scheduler for DL training |
| 67 | BOSS - An Architecture for Database Kernel Composition | included | composable DBMS kernel architecture gluing Arrow, Velox and ArrayFire; builds in user space, one GPU |
| 68 | CoroGraph: Bridging Cache Efficiency and Work Efficiency for Graph Algorithm Execution | included | coroutine-based software prefetching and cache-efficient in-memory graph engine; CPU only |
| 69 | Mammoths Are Slow: The Overlooked Transactions of Graph Data | out-topic | graph transaction benchmark study |
| 70 | VeriDKG: A Verifiable SPARQL Query Engine for Decentralized Knowledge Graphs | out-topic | verifiable decentralized knowledge graphs |
| 71 | Eraser: Eliminating Performance Regression on Learned Query Optimizer | included | eliminating performance regressions of learned query optimizers on PostgreSQL |
| 72 | HyBench: A New Benchmark for HTAP Databases | out-topic | HTAP workload benchmark specification |
| 73 | Falcon: Fair Active Learning using Multi-armed Bandits | out-topic | fair active learning |
| 74 | A Blockchain System for Clustered Federated Learning with Peer-to-Peer Knowledge Transfer | out-topic | blockchain federated learning |
| 75 | PilotScope: Steering Databases with Machine Learning Drivers | included | platform for plugging ML drivers into PostgreSQL/openGauss; strong base for an improvement project |
| 76 | Timestamp as a Service, not an Oracle | out-topic | distributed timestamp oracle design |
| 77 | Data-Driven Insight Synthesis for Multi-Dimensional Data | out-topic | insight synthesis over multi-dimensional data |
| 78 | Database Native Model Selection: Harnessing Deep Neural Networks in Database Systems | included | in-database neural model selection; single GPU is enough |
| 79 | Querying Structural Diversity in Streaming Graphs | out-topic | streaming graph query algorithm |
| 80 | LM-SRPQ: Efficiently Answering Regular Path Query in Streaming Graphs | out-topic | streaming regular path queries |
| 81 | ETC: Efficient Training of Temporal Graph Neural Networks over Large-scale Dynamic Graphs | included | temporal GNN training system for large dynamic graphs; single machine GPU |
| 82 | Towards Full Stack Adaptivity in Permissioned Blockchains | out-topic | permissioned blockchain adaptivity |
| 83 | BigST: Linear Complexity Spatio-Temporal Graph Neural Network for Traffic Forecasting on Large-Scale Road Networks | out-topic | traffic forecasting model |
| 84 | SepHash: A Write-Optimized Hash Index On Disaggregated Memory via Separate Segment Structure | out-machine | disaggregated memory over RDMA |
| 85 | XGNN: Boosting Multi-GPU GNN Training via Global GNN Memory Store | out-machine | multi-GPU server with NVLink/NVSwitch |
| 86 | Communication Efficient and Provable Federated Unlearning | out-topic | federated unlearning |
| 87 | Text-to-SQL Empowered by Large Language Models: A Benchmark Evaluation | out-topic | text-to-SQL benchmark |
| 88 | Scaling Package Queries to a Billion Tuples via Hierarchical Partitioning and Customized Optimization | out-topic | package query optimization |
| 89 | MisDetect: Iterative Mislabel Detection using Early Loss | out-topic | mislabel detection method |
| 90 | Capturing More Associations by Referencing External Graphs | out-topic | graph association rules |
| 91 | QTCS: Efficient Query-Centered Temporal Community Search | out-topic | temporal community search |
| 92 | DPSUR: Accelerating Differentially Private Stochastic Gradient Descent Using Selective Update and Release | out-topic | differentially private SGD |
| 93 | How Can We Train Deep Learning Models Across Clouds and Continents? An Experimental Study | out-machine | trains across many spot VMs in multiple clouds and continents |
| 94 | Accelerating Sampling and Aggregation Operations in GNN Frameworks with GPU Initiated Direct Storage Accesses | out-machine | GPU-initiated direct NVMe access needs GPUDirect Storage and privileged kernel-level drivers |
| 95 | Comprehensive Evaluation of GNN Training Systems: A Data Management Perspective | included | systematic evaluation of GNN training systems from a data-management perspective |
| 96 | LION: Fast and High-Resolution Network Kernel Density Visualization | out-topic | kernel density visualization |
| 97 | Performance-Based Pricing of Federated Learning via Auction | out-topic | federated learning pricing/auction |
| 98 | OEBench: Investigating Open Environment Challenges in Real-World Relational Data Streams | out-topic | data-stream ML benchmark |
| 99 | Influence Maximization via Vertex Countering | out-topic | influence countering algorithm |
| 100 | Optimizing Data Acquisition to Enhance Machine Learning Performance | out-topic | data acquisition for ML |
| 101 | Minimum Strongly Connected Subgraph Collection in Dynamic Graphs | out-topic | dynamic graph algorithm |
| 102 | FusionQuery: On-demand Fusion Queries over Multi-source Heterogeneous Data | out-topic | multi-source query fusion |
| 103 | POLAR: Adaptive and Non-invasive Join Order Selection via Plans of Least Resistance | out-topic | adaptive join order selection |
| 104 | DAHA: Accelerating GNN Training with Data and Hardware Aware Execution Planning | included | cost-model-driven execution planning and pipelining for GNN training on CPU-GPU |
| 105 | FluidKV: Seamlessly Bridging the Gap between Indexing Performance and Memory-Footprint on Ultra-Fast Storage | out-machine | targets byte-addressable persistent memory |
| 106 | How do Categorical Duplicates Affect ML? A New Benchmark and Empirical Analyses | out-topic | data quality benchmark for ML |
| 107 | CGgraph: An Ultra-fast Graph Processing System on Modern Commodity CPU-GPU Co-processor | included | CPU-GPU cooperative graph engine that handles GPU memory oversubscription; one GPU is the target setting |
| 108 | FCBench: Cross-Domain Benchmarking of Lossless Compression for Floating-point Data | included | cross-domain lossless floating-point compression benchmark with CPU and GPU codecs |
| 109 | PairwiseHist: Fast, Accurate, and Space-Efficient Approximate Query Processing with Data Compression | out-no-code | checked the PDF (no artifact-availability statement), the PVLDB artifact flag (no) and a web search - only baseline repositories are cited, no PairwiseHist code |
| 110 | MetaStore: Analyzing Deep Learning Meta-Data at Scale | included | system for storing and analyzing deep-learning gradient metadata at scale; single machine with one GPU |
| 111 | RTScan:  Efficient Scan with Ray Tracing Cores | included | index scan offloaded to GPU ray-tracing cores; the A5000 is Ampere and has RT cores, OptiX works on driver 535 |
| 112 | FreshGNN: Reducing Memory Access via Stable Historical Embeddings for Graph Neural Network Training | included | historical-embedding cache policy that cuts feature loading in GNN mini-batch training; single-GPU configuration exists |
| 113 | Sorting on Byte-Addressable Storage: The Resurgence of Tree Structure | out-machine | targets byte-addressable persistent storage hardware |
| 114 | Efficient Placement of Decomposable Aggregation Functions for Stream Processing over Large Geo-Distributed Topologies | out-machine | operator placement across a large geo-distributed multi-node topology |
| 115 | AeonG: An Efficient Built-in Temporal Support in Graph Databases | included | built-in temporal storage support in a graph database; JVM installable through conda |
| 116 | Refactoring Index Tuning Process with Benefit Estimation | included | learned benefit estimation that skips what-if calls during index tuning |
| 117 | LightDiC: A Simple yet Effective Approach for Large-scale Digraph Representation Learning | out-topic | digraph representation learning |
| 118 | Efficient Differential Dependency Discovery | out-topic | dependency discovery algorithm |
| 119 | Is Your Learned Query Optimizer Behaving As You Expect? A Machine Learning Perspective | included | critical re-evaluation of learned query optimizers; released harness makes a careful reproduction straightforward |
| 120 | Mixed Covers of Keys and Functional Dependencies for Maintaining the Integrity of Data under Updates | out-topic | integrity constraint maintenance |
| 121 | Outlier Summarization via Human Interpretable Rules | out-topic | outlier summarization rules |
| 122 | Nuhuo: An Effective Estimation Model for Traffic Speed Histogram Imputation on A Road Network | out-topic | traffic histogram imputation |
| 123 | Intelligent Pooling: Proactive Resource Provisioning in Large-scale Cloud Service | out-no-code | checked the PDF (no artifact-availability statement) and the PVLDB artifact flag (no) - the system is a Microsoft production service with no released code or traces |
| 124 | Efficient Exact Subgraph Matching via GNN-based Path Dominance Embedding | out-topic | subgraph matching algorithm |
| 125 | Leveraging Dynamic and Heterogeneous Workload Knowledge to Boost the Performance of Index Advisors | included | learning-based index advisor for dynamic and heterogeneous workloads |
| 126 | UltraLogLog: A Practical and More Space-Efficient Alternative to HyperLogLog for Approximate Distinct Counting | out-topic | distinct-counting sketch algorithm |
| 127 | Real-time Insertion Operator for Shared Mobility on Time-Dependent Road Networks | out-topic | shared mobility insertion algorithm |
| 128 | X-TED: Massive Parallelization of Tree Edit Distance | out-topic | tree edit distance parallelization |
| 129 | Cardinality Estimation of Subgraph Matching: A Filtering-Sampling Approach | out-topic | subgraph cardinality estimation algorithm |
| 130 | Efficient Regular Simple Path Queries under Transitive Restricted Expressions | out-topic | regular path query algorithm |
| 131 | A Multi-Scale Decomposition MLP-Mixer for Time Series Analysis | out-topic | time-series model architecture |
| 132 | P-Shapley: Shapley Values on Probabilistic Classifiers | out-topic | Shapley value computation |
| 133 | Optimizing Video Selection LIMIT Queries With Commonsense Knowledge | out-topic | video query semantics |
| 134 | ZeroEA: A Zero-Training Entity Alignment Framework via Pre-Trained Language Model | out-topic | entity alignment method |
| 135 | Extending Graph Rules with Oracles | out-topic | graph rule semantics |
| 136 | FlowWalker: A Memory-efficient and High-performance GPU-based Dynamic Graph Random Walk Framework | included | GPU dynamic-graph random-walk engine with sampler-centric scheduling; one GPU |
| 137 | Accelerating String-key Learned Index Structures via Memoization-based Incremental Training | out-machine | SIA is an algorithm-hardware co-design whose accelerator is implemented on an FPGA |
| 138 | Truss-based Community Search over Streaming Directed Graphs | out-topic | community search over streaming graphs |
| 139 | InferDB: In-Database Machine Learning Inference Using Indexes | included | index-based approximation of end-to-end ML inference pipelines inside PostgreSQL |
| 140 | AAA: an Adaptive Mechanism for Locally Differential Private Mean Estimation | out-topic | local differential privacy |
| 141 | Accelerating Merkle Patricia Trie with GPU | out-topic | blockchain state trie acceleration |
| 142 | Privacy Amplification via Shuffling: Unified, Simplified, and Tightened | out-topic | differential privacy theory |
| 143 | Detecting Metadata-Related Logic Bugs in Database Systems via Raw Database Construction | out-topic | DBMS logic bug detection |
| 144 | From Zero to Hero: Detecting Leaked Data through Synthetic Data Injection and Model Querying | out-topic | data leakage detection |
| 145 | Oasis: An Optimal Disjoint Segmented Learned Range Filter | included | learned range filter integrated into RocksDB; a clean single-machine storage project |
| 146 | LakeBench: A Benchmark for Discovering Joinable and Unionable Tables in Data Lakes | out-topic | data lake table discovery benchmark |
| 147 | GPTuner: A Manual-Reading Database Tuning System via GPT-Guided Bayesian Optimization | included | LLM-guided Bayesian optimization of DBMS knobs |
| 148 | Raising the ClaSS of Streaming Time Series Segmentation | out-topic | time-series segmentation |
| 149 | Fast Local Subgraph Counting | out-topic | subgraph counting algorithm |
| 150 | ReAcTable: Enhancing ReAct for Table Question Answering | out-topic | table question answering with LLMs |
| 151 | NeutronOrch: Rethinking Sample-based GNN Training under CPU-GPU Heterogeneous Environments | included | CPU-GPU task orchestration for sample-based GNN training |
| 152 | Rapidash: Efficient Detection of Constraint Violations | out-topic | constraint violation detection |
| 153 | Differentially Private Data Generation with Missing Data | out-topic | differentially private data generation |
| 154 | Everything You Always Wanted to Know About Storage Compressibility of Pre-Trained ML Models but Were Afraid to Ask | included | deduplication and compression study of pre-trained model files; needs tens of GB of downloads but 257 GB free is enough |
| 155 | Fight Fire with Fire: Towards Robust Graph Neural Networks on Dynamic Graphs via Actively Defense | out-topic | adversarial robustness of GNNs |
| 156 | SeLeP: Learning Based Semantic Prefetching for Exploratory Database Workloads | included | learned semantic prefetcher for exploratory database workloads |
| 157 | Contributions Estimation in Federated Learning: A Comprehensive Experimental Evaluation | out-topic | federated learning contribution estimation |
| 158 | Visualization-aware Time Series Min-Max Caching with Error Bound Guarantees | included | adaptive in-memory min-max cache with error bounds for time-series visualization |
| 159 | CHORUS: Foundation Models for Unified Data Discovery and Exploration | out-topic | foundation models for data discovery |
| 160 | Cloud-Native Database Systems and Unikernels: Reimagining OS Abstractions for Modern Hardware | out-machine | requires booting a specialized unikernel OS kernel |
| 161 | CIVET: Exploring Compact Index for Variable-Length Subsequence Matching on Time Series | out-topic | subsequence matching index |
| 162 | Spatialyze: A Geospatial Video Analytics System with Spatial-Aware Optimizations | out-topic | geospatial video query optimization |
| 163 | Optimal Matrix Sketching over Sliding Windows | out-topic | matrix sketching algorithm |
| 164 | Window Function Expression: Let the Self-join Enter | out-topic | window function query rewriting |
| 165 | SplitDF: Splitting Dataframes for Memory-Efficient Data Analysis | included | memory-footprint reduction for dataframes on DuckDB/Ibis; user-space Python |
| 166 | Sampling Methods for Inner Product Sketching | out-topic | inner product sketching |
| 167 | DIDS: Double Indices and Double Summarizations for Fast Similarity Search | out-topic | similarity search index algorithm |
| 168 | Improving Graph Compression for Efficient Resource-Constrained Graph Analytics | included | rule-based graph compression that cuts peak memory during both compression and computation; CPU only |
| 169 | Efficient Unsupervised Community Search with Pre-trained Graph Transformer | out-topic | community search model |
| 170 | DET-LSH: A Locality-Sensitive Hashing Scheme with Dynamic Encoding Tree for Approximate Nearest Neighbor Search | out-topic | LSH algorithm for nearest-neighbour search |
| 171 | BIRD: Efficient Approximation of Bidirectional Hidden Personalized PageRank | out-topic | personalized PageRank algorithm |
| 172 | GENTI: GPU-powered Walk-based Subgraph Extraction for Scalable Representation Learning on Dynamic Graphs | included | GPU subgraph-extraction pipeline for representation learning on dynamic graphs |
| 173 | ArcheType: A Novel Framework for Open-Source Column Type Annotation using Large Language Models | out-topic | column type annotation with LLMs |
| 174 | Trajectory Similarity Measurement: An Efficiency Perspective | out-topic | trajectory similarity measures |
| 175 | BYO: A Unified Framework for Benchmarking Large-Scale Graph Containers | out-topic | graph container benchmark |
| 176 | Secure and Verifiable Data Collaboration with Low-Cost Zero-Knowledge Proofs | out-topic | zero-knowledge proof protocols |
| 177 | Rashnu: Data-Dependent Order-Fairness | out-topic | order fairness in transaction ordering |
| 178 | Sparcle: Boosting the Accuracy of Data Cleaning Systems through Spatial Awareness | out-topic | spatial data cleaning |
| 179 | TFB: Towards Comprehensive and Fair Benchmarking of Time Series Forecasting Methods | out-topic | forecasting benchmark |
| 180 | FSM: A Fine-grained Splitting and Merging Framework for Dual-balanced Graph Partition | out-topic | graph partitioning algorithm |
| 181 | Efficient and Reliable Estimation of Knowledge Graph Accuracy | out-topic | knowledge graph accuracy estimation |
| 182 | Breaking It Down: An In-depth Study of Index Advisors | included | open testbed implementing 17 index advisors; excellent reproduction or improvement base |
| 183 | Accelerating Maximal Clique Enumeration via Graph Reduction | out-topic | clique enumeration algorithm |
| 184 | POLIGRAS: Policy-based Graph Summarization | out-topic | graph summarization |
| 185 | SWAT: A System-Wide Approach to Tunable Leakage Mitigation in Encrypted Data Stores | out-topic | encrypted data store leakage mitigation |
| 186 | TIGER: Training Inductive Graph Neural Network for Large-scale Knowledge Graph Reasoning | out-topic | knowledge graph reasoning model |
| 187 | Incremental Sliding Window Connectivity over Streaming Graphs | out-topic | streaming graph connectivity |
| 188 | CohortNet: Empowering Cohort Discovery for Interpretable Healthcare Analytics | out-topic | healthcare analytics model |
| 189 | Efficient Influence Minimization via Node Blocking | out-topic | influence minimization algorithm |
| 190 | D-Bot: Database Diagnosis System using Large Language Models | included | LLM-based DBMS diagnosis agent; can run against a local PostgreSQL |
| 191 | Blitzcrank: Fast Semantic Compression for In-memory Online Transaction Processing | included | semantic compression for in-memory OLTP row stores; user-space C++ with TPC-C evaluation |
| 192 | Spectrum: Speedy and Strictly-Deterministic Smart Contract Transactions for Blockchain Ledgers | out-topic | blockchain smart contract execution |
| 193 | Fast Commitment for Geo-Distributed Transactions via Decentralized Co-coordinators | out-machine | geo-distributed multi-node commit protocol |
| 194 | CXL and the Return of Scale-Up Database Engines | out-machine | argues from CXL hardware that is not available here and ships no artifact |
| 195 | Inductive Attributed Community Search: to Learn Communities across Graphs | out-topic | community search model |
| 196 | I/O Efficient Label-Constrained Reachability Queries in Large Graphs | out-topic | reachability query algorithm |
| 197 | DEX: Scalable Range Indexing on Disaggregated Memory | out-machine | disaggregated memory over RDMA |
| 198 | Automatic Data Repair: Are We Ready to Deploy? | out-topic | data repair evaluation |
| 199 | Biathlon: Harnessing Model Resilience for Accelerating ML Inference Pipelines | included | ML serving system that trades feature approximation for latency under accuracy bounds |
| 200 | Distributed Shortest Distance Labeling on Large-Scale Graphs | out-topic | graph labeling algorithm |
| 201 | Efficient Parallel D-core Decomposition at Scale | out-topic | graph decomposition algorithm |
| 202 | Efficient Discovery of Significant Patterns with Few-Shot Resampling | out-topic | pattern mining statistics |
| 203 | Robust Best Point Selection under Unreliable User Feedback | out-topic | preference elicitation |
| 204 | Towards Optimal Transaction Scheduling | included | schedule-first concurrency control and greedy schedule search implemented in RocksDB; single machine |
| 205 | QCore: Data-Efficient, On-Device Continual Calibration for Quantized Models | out-topic | quantized model calibration method |
| 206 | Efficient Algorithms for Pseudoarboricity Computation in Large Static and Dynamic Graphs | out-topic | graph density algorithm |
| 207 | RoarGraph: A Projected Bipartite Graph for Efficient Cross-Modal Approximate Nearest Neighbor Search | included | cross-modal ANN graph index; single-machine memory-bound C++ |
| 208 | Combining Small Language Models and Large Language Models for Zero-Shot NL2SQL | out-topic | NL2SQL with language models |
| 209 | D3-GNN: Dynamic Distributed Dataflow for Streaming Graph Neural Networks | out-machine | distributed streaming dataflow across a multi-node cluster |
| 210 | Distance-based Outlier Query Optimization in Apache IoTDB | out-topic | outlier query algorithm |
| 211 | TC-Match: Fast Time-constrained Continuous Subgraph Matching | out-topic | continuous subgraph matching |
| 212 | Automating the Enterprise with Foundation Models | out-topic | vision paper on foundation models for enterprise data |
| 213 | Efficient Index for Temporal Core Queries over Bipartite Graphs | out-topic | temporal graph index |
| 214 | Uldp-FL: Federated Learning with Across Silo User-Level Differential Privacy | out-topic | federated learning with differential privacy |
| 215 | Evolution Forest Index: Towards Optimal Temporal $k$-Core Component Search via Time-Topology Isomorphic Computation | out-topic | temporal k-core index |
| 216 | Eliminating Data Processing Bottlenecks in GNN Training over Large Graphs via Two-level Feature Compression | included | two-level feature compression plus GPU cache co-design for GNN training; single-GPU config available |
| 217 | Towards Systematic Index Dynamization | included | framework that turns static indexes into updatable ones; user-space C++ library |
| 218 | Ensemble Clustering based on Meta-Learning and Hyperparameter Optimization | out-topic | clustering method |
| 219 | Efficient Stochastic Routing in Path-Centric Uncertain Road Networks | out-topic | stochastic routing algorithm |
| 220 | Transforming Property Graphs | out-topic | property graph transformation language |
| 221 | Are Large Language Models a Good Replacement of Taxonomies? | out-topic | LLM evaluation study |
| 222 | Efficient Algorithms for Density Decomposition on Large Static and Dynamic Graphs | out-topic | graph decomposition algorithm |
| 223 | Efficient Maximal Motif-Clique Enumeration over Large Heterogeneous Information Networks | out-topic | motif clique enumeration |
| 224 | OUTRE: An OUT-of-core De-REdundancy GNN Training Framework for Massive Graphs within A Single Machine | included | out-of-core GNN training explicitly designed for a single machine |
| 225 | On Reducing Space Amplification with Multi-Column Compaction in Apache IoTDB | included | multi-column LSM-tree compaction policy in Apache IoTDB; JVM, single node, classic storage project |
| 226 | AutoTSAD: Unsupervised Holistic Anomaly Detection for Time Series Data | out-topic | anomaly detection ensemble |
| 227 | Enabling Window-Based Monotonic Graph Analytics with Reusable Transitional Results for Pattern-Consistent Queries | out-topic | graph analytics query reuse |
| 228 | When Amnesia Strikes: Understanding and Reproducing Data Loss Bugs with Fault Injection | included | FUSE-based fault-injection file system; /dev/fuse is world-writable and fusermount3 is setuid so it runs unprivileged |
| 229 | PriPL-Tree: Accurate Range Query for Arbitrary Distribution under Local Differential Privacy | out-topic | local differential privacy |
| 230 | Win-Win: On Simultaneous Clustering and Imputing over Incomplete Data | out-topic | clustering and imputation method |
| 231 | HRNet: Differentially Private Hierarchical and Multi-Resolution Network for Human Mobility Data Synthesization | out-topic | differentially private mobility synthesis |
| 232 | Efficiently Mitigating the Impact of Data Drift on Machine Learning Pipelines | out-topic | data drift handling for ML pipelines |
| 233 | PCSP: Efficiently Answering Label-Constrained Shortest Path Queries in Road Networks | out-topic | shortest path query algorithm |
| 234 | Efficient Enumeration of Recursive Plans in Transformation-based Query Optimizers | out-topic | query optimizer plan enumeration |
| 235 | Enriching Relations with Additional Attributes for ER | out-topic | entity resolution |
| 236 | Enhancing Accuracy for Super Spreader Identification in High-Speed Data Streams | out-topic | stream sketch for heavy hitters |
| 237 | Privately Answering Queries on Skewed Data via Per-Record Differential Privacy | out-topic | differential privacy |
| 238 | Agile-Ant: Self-managing Distributed Cache Management for Cost Optimization of Big Data Applications | out-machine | needs an elastic multi-node cloud cluster that it scales out and is billed for |
| 239 | Complex Event Recognition with Symbolic Register Transducers | out-topic | complex event recognition automata |
| 240 | HAIChart: Human and AI Paired Visualization System | out-topic | visualization recommendation |
| 241 | A Sampling-based Framework for Hypothesis Testing on Large Attributed Graphs | out-topic | graph hypothesis testing |
| 242 | LLM-PBE: Assessing Data Privacy in Large Language Models | out-topic | LLM privacy benchmark |
| 243 | Robust Join Processing with Diamond Hardened Joins | out-topic | join operator and query optimization |
| 244 | DARKER: Efficient Transformer with Data-driven Attention Mechanism for Time Series | out-topic | time-series transformer model |
| 245 | Efficient Maximal Frequent Group Enumeration in Temporal Bipartite Graphs | out-topic | temporal graph enumeration |
| 246 | Optimizing Video Queries with Declarative Clues | out-topic | video query optimization semantics |
| 247 | Fainder: A Fast and Accurate Index for Distribution-Aware Dataset Search | out-topic | dataset search index |
| 248 | nsDB: Architecting the Next Generation Database by Integrating Neural and Symbolic Systems (Vision) | out-topic | vision paper on neuro-symbolic databases |
| 249 | Two Birds With One Stone: Designing a Hybrid Cloud Storage Engine for HTAP | included | hybrid column-row cloud storage engine for HTAP |
| 250 | DDS: DPU-optimized Disaggregated Storage | out-machine | requires DPU networking hardware |
| 251 | The Dawn of Natural Language to SQL: Are We Fully Ready? [Experiment, Analysis & Benchmark ] | out-topic | NL2SQL benchmark |
| 252 | Counterfactual Explanation of the Shapley Value in Data Coalitions | out-topic | Shapley value explanations |
| 253 | Searching Data Lakes for Nested and Joined Data | out-topic | data lake search |
| 254 | Efficient Betweenness Centrality Computation over Large Heterogeneous Information Networks | out-topic | centrality computation algorithm |
| 255 | The Holon Approach for Simultaneously Tuning Multiple Components in a Self-Driving Database Management System with Machine Learning via Synthesized Proto-Actions | included | holistic RL tuning across knobs, indexes and query hints on PostgreSQL |
| 256 | DynaHB: A Communication-Avoiding Asynchronous Distributed Framework with Hybrid Batches for Dynamic GNN Training | out-machine | distributed multi-node asynchronous GNN training |
| 257 | Efficient kNN Search in Public Transportation Networks | out-topic | kNN query algorithm on transport networks |
| 258 | LITS: An Optimized Learned Index for Strings | included | learned index for variable-length string keys; user-space C++ benchmark against ART and HOT |
| 259 | OLAP on Modern Chiplet-Based Processors | included | chiplet-aware task placement for query engines; the target machine is a multi-CCD Threadripper PRO so the effect is present |
| 260 | Bf-Tree: A Modern Read-Write-Optimized Concurrent Larger-Than-Memory Range Index | out-no-code | the only repository (XiangpengHao/bf-tree-docs) contains slides and the paper; its README states the implementation is internal to Microsoft |
| 261 | Partition, Don't Sort! Compression Boosters for Cloud Data Ingestion Pipelines | included | clustering-based compression booster for nested-data ingestion; CPU only |
| 262 | Chameleon: Foundation Models for Fairness-aware Multi-modal Data Augmentation to Enhance Coverage of Minorities | out-topic | data augmentation for fairness |
| 263 | DAFDiscover: Robust Mining Algorithm for Dynamic Approximate Functional Dependencies on Dirty Data | out-topic | functional dependency mining |
| 264 | Hardware-Efficient Data Imputation through DBMS Extensibility | included | shape-wise microbatching execution model inside the BOSS DBMS kernel; user-space C++ |
| 265 | Generating Succinct Descriptions of Database Schemata for Cost-Efficient Prompting of Large Language Models | out-topic | prompt compression for schema descriptions |
| 266 | Saving Money for Analytical Workloads in the Cloud | out-machine | optimizes monetary cost across commercial cloud pricing models and services |
| 267 | ReCG: Bottom-Up JSON Schema Discovery Using a Repetitive Cluster-and-Generalize Framework | out-topic | JSON schema discovery |
| 268 | Optimizing Collections of Bloom Filters within a Space Budget | included | joint space allocation across a collection of Bloom filters; small self-contained user-space artifact |
| 269 | A Spark Optimizer for Adaptive, Fine-Grained Parameter Tuning | included | multi-objective ML tuning of Spark adaptive-query-execution parameters; Spark runs local or pseudo-distributed |
| 270 | Texera: A System for Collaborative and Interactive Data Analytics Using Workflows | out-topic | collaborative workflow analytics platform for clusters |
| 271 | Efficient Validation of SHACL Shapes with Reasoning | out-topic | SHACL constraint validation |
| 272 | QED: A Powerful Query Equivalence Decider for SQL | out-topic | SQL equivalence checking |
| 273 | Index Advisors on Quantum Platforms | out-machine | requires gate-based quantum platforms or quantum simulators at scale |
| 274 | Blueprinting the Cloud: Unifying and Automatically Optimizing Cloud Data Infrastructures with BRAD | out-machine | plans and manages real AWS engines such as Aurora, Redshift and Athena |
| 275 | Aleph Filter: To Infinity in Constant Time | included | expandable filter with constant-time operations under growth; user-space C++ |
| 276 | RUSH: Real-time Burst Subgraph Discovery in Dynamic Graphs | out-topic | burst subgraph discovery |
| 277 | A Benchmark Study of Deep-RL Methods for Maximum Coverage Problems over Graphs | out-topic | reinforcement learning for graph coverage |
| 278 | Hit the Gym: Accelerating Query Execution to Efficiently Bootstrap Behavior Models for Self-Driving Database Management Systems | included | accelerated training-data collection for self-driving DBMS behaviour models on PostgreSQL |
| 279 | Why TPC Is Not Enough: An Analysis of the Amazon Redshift Fleet | out-topic | production cloud fleet measurement study |
| 280 | Efficient k-Clique Count Estimation with Accuracy Guarantee | out-topic | clique count estimation |
| 281 | The Case for DBMS Live Patching | included | user-space live patching of DBMS binaries via libpulp; no kernel module needed |
| 282 | TenGraph: A Tensor-Based Graph Query Engine | out-topic | tensor-based graph query engine |
| 283 | LARGE: A Length-Aggregation-based Grid Structure for Line Density Visualization | out-topic | line density visualization |
| 284 | CausalMesh: A Causal Cache for Stateful Serverless Computing | included | causally consistent cache for stateful serverless workflows; the multi-server topology can be emulated with several processes on one host |
| 285 | The Vadalog Parallel System: Distributed Reasoning with Datalog+/- | out-topic | distributed Datalog reasoning |
| 286 | PARQO: Penalty-Aware Robust Plan Selection in Query Optimization | out-topic | robust plan selection in query optimization |
| 287 | InBox: Recommendation with Knowledge Graph using Interest Box Embedding | out-topic | knowledge graph recommendation |
| 288 | A Branch-&-Bound Algorithm for Fractional Hypertree Decomposition | out-topic | hypertree decomposition algorithm |
| 289 | Steiner-Hardness: A Query Hardness Measure for Graph-Based ANN Indexes | out-topic | ANN query hardness measure |
| 290 | Simpler is More: Efficient Top-K Nearest Neighbors Search on Large Road Networks | out-topic | road network nearest-neighbour queries |
| 291 | SQL Engines Excel at the Execution of Imperative Programs | out-topic | SQL code generation for imperative programs |
| 292 | Scaling your Hybrid CPU-GPU DBMS to Multiple GPUs | out-machine | the contribution is scaling a DBMS across multiple GPUs |
| 293 | Scalable Model-Based Management of Massive High Frequency Wind Turbine Data with ModelarDB | included | model-based time-series compression evaluation in Rust |
| 294 | Eventual Durability | out-topic | transaction durability semantics |
| 295 | TUCKET: A Tensor Time Series Data Structure for Efficient and Accurate Factor Analysis over Time Ranges | out-topic | tensor decomposition data structure |
| 296 | Topology-preserving Graph Coarsening: An Elementary Collapse-based Approach | out-topic | graph coarsening algorithm |
| 297 | Efficient Cost Modeling of Space-filling Curves | out-topic | space-filling curve cost model |
| 298 | Generalizable Data Cleaning of Tabular Data in Latent Space | out-topic | tabular data cleaning method |
| 299 | Dynamic Graph Databases with Out-of-order Updates | out-topic | dynamic graph query semantics |
| 300 | Powering In-Database Dynamic Model Slicing for Structured Data Analytics | included | in-database dynamic model slicing shipped as a PostgreSQL extension in Rust |
| 301 | GastCoCo: Graph Storage and Coroutine-Based Prefetch Co-Design for Dynamic Graph Processing | included | coroutine-based prefetching and graph storage co-design that targets cache misses; CPU only |
| 302 | MTSClean: Efficient Constraint-based Cleaning for Multi-Dimensional Time Series Data | out-topic | time-series constraint cleaning |
| 303 | Neighborhood-Preserving Graph Sparsification | out-topic | graph sparsification algorithm |
| 304 | ELEET: Efficient Learned Query Execution over Text and Tables | out-topic | learned query execution over text and tables |
