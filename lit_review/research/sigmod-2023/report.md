STATUS: complete
TOTAL_PAPERS: 186
INCLUDED: 37

## Sources

- **Primary list**: the official conference page `https://2023.sigmod.org/sigmod_research_list.shtml`
  ("SIGMOD 2023: Accepted Research Papers"), fetched raw with `curl` and parsed with a regex over
  the `<li><strong>...</strong>` entries. The page contains a single flat `<ul>` with **190 `<li>`
  entries**, but four titles appear twice verbatim (Efficient and Portable Einstein Summation in SQL;
  FEC: Efficient Deep Recommendation Model Training with Flexible Embedding Communication;
  SSIN: Self-Supervised Learning for Rainfall Spatial Interpolation; Near-Duplicate Sequence Search
  at Scale for Neural Language Model Memorization Evaluation). After removing those duplicates the
  venue-year has **186 distinct main-track research papers**, which is the number reported as
  `TOTAL_PAPERS`. Demo, industrial, tutorial, PODS and workshop papers are on separate pages and
  were not included.
- **Cross-check**: SIGMOD 2023 research papers are published in PACMMOD volume 1. DBLP and the ACM
  Digital Library both refuse plain `curl` (DBLP serves an Anubis bot challenge on `dblp.org`,
  `dblp.uni-trier.de` and `dblp.dagstuhl.de`; `dl.acm.org` returns a Cloudflare interstitial and
  403s on PDF URLs), so the count was cross-checked against the **OpenAlex** API
  (`source S4387289859`, "Proceedings of the ACM on Management of Data", `publication_year:2023`),
  which returns 271 works for PACMMOD in 2023 - i.e. SIGMOD 2023 plus PODS 2023 plus the
  December 2023 issue that belongs to SIGMOD 2024. 184 of the 186 official titles matched an
  OpenAlex record exactly or after normalisation/fuzzy matching; the remaining discrepancies are
  camera-ready title changes, which were resolved one by one (for example
  "Caerus: A Caching-based Framework for Scalable Temporal Graph Neural Networks" was published as
  "Orca: Scalable Temporal Graph Neural Network Training with Theoretical Guarantees",
  "TowerSensing" as "TreeSensing", "HybridPipe" as "HAIPipe"). Only
  "DARQ Matter Binds Everything" has no OpenAlex PACMMOD-2023 record; its DOI (10.1145/3589262)
  was confirmed independently.
- **Abstracts** for the topic screen came from the OpenAlex `abstract_inverted_index` field for all
  185 matched papers.
- **Code check**: GitHub repository search API, targeted web searches, direct HTTP checks of
  candidate repository URLs, and arXiv preprints (downloaded and grepped for repository links) for
  the eight candidates that have one. ACM DL PDFs could not be fetched (403), so first-page
  availability footnotes could not be read directly; papers whose artifact could not be confirmed
  are listed with repo `unknown` rather than excluded.

## Included
| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | Efficient and Portable Einstein Summation in SQL | https://dl.acm.org/doi/10.1145/3589266 | https://dl.acm.org/doi/pdf/10.1145/3589266 | unknown | ml-systems | Compiles Einstein-summation tensor expressions into portable SQL and runs them in a relational engine - a CPU-only single-node tensor runtime. Concern: contribution is a query-compilation technique rather than an ML runtime; no official repo found in GitHub or web search |
| 2 | AWARE: Workload-aware, Redundancy-exploiting Linear Algebra | https://dl.acm.org/doi/10.1145/3588682 | https://dl.acm.org/doi/pdf/10.1145/3588682 | https://github.com/apache/systemds | ml-systems | Workload-aware lossless compression for linear algebra inside Apache SystemDS; single-node CPU ML runtime with clear performance hypotheses. Concern: code lives in the large SystemDS codebase rather than a standalone artifact |
| 3 | CompressGraph: Efficient Parallel Graph Analytics with Rule-Based Compression | https://dl.acm.org/doi/10.1145/3588684 | https://dl.acm.org/doi/pdf/10.1145/3588684 | https://github.com/ZhengChenCS/CompressGraph | other-userspace | Rule-based graph compression with direct computation on the compressed form; user-space C++ engine on multicore CPU. Concern: graph-analytics flavour rather than OS-level systems |
| 4 | Virtual-Memory Assisted Buffer Management | https://dl.acm.org/doi/10.1145/3588687 | https://dl.acm.org/doi/pdf/10.1145/3588687 | https://github.com/viktorleis/vmcache | memory | Buffer pool built on hardware virtual memory - directly a user-space memory-management design and an excellent improvement target. Concern: the second half of the paper (exmap) is a Linux kernel module and cannot be built or loaded without root; only vmcache itself is reproducible here |
| 5 | One-shot garbage collection for in-memory OLTP through temporality-aware version storage | https://dl.acm.org/doi/10.1145/3588699 | https://dl.acm.org/doi/pdf/10.1145/3588699 | unknown | memory | One-shot GC and temporality-aware version storage for in-memory MVCC OLTP - user-space memory reclamation on one multicore machine. Concern: no public repo located via GitHub search or web search; marked unknown rather than excluded |
| 6 | Grouping Time Series for Efficient Columnar Storage | https://dl.acm.org/doi/10.1145/3588703 | https://dl.acm.org/doi/pdf/10.1145/3588703 | unknown | storage | Groups time series to cut columnar timestamp storage overhead - a storage-engine/compression contribution evaluated on a single node. Concern: implementation is reported inside Apache IoTDB but no dedicated artifact repo was confirmed |
| 7 | Transaction Scheduling: From Conflicts to Runtime Conflicts | https://dl.acm.org/doi/10.1145/3588706 | https://dl.acm.org/doi/pdf/10.1145/3588706 | unknown | scheduling | Runtime-conflict-aware scheduling of transactions across cores of a single multicore machine; fits the scheduling topic and the hardware. Concern: no public artifact found |
| 8 | Speeding Up End-to-end Query Execution via Learning-based Progressive Cardinality Estimation | https://dl.acm.org/doi/10.1145/3588708 | https://dl.acm.org/doi/pdf/10.1145/3588708 | unknown | ml-for-systems | Learned progressive cardinality estimator - a learned component inside a query engine with an explicit inference-latency vs accuracy tradeoff to improve. Concern: no public repo found |
| 9 | dbET: Execution Time Distribution-based Plan Selection | https://dl.acm.org/doi/10.1145/3588711 | https://dl.acm.org/doi/pdf/10.1145/3588711 | unknown | ml-for-systems | Conformal-prediction-based execution-time distributions for plan selection - an ML component inside the optimizer. Concern: no public repo found; industrial co-authors (Huawei) |
| 10 | Detect, Distill and Update: Learned DB Systems Facing Out of Distribution Data | https://dl.acm.org/doi/10.1145/3588713 | https://dl.acm.org/doi/pdf/10.1145/3588713 | unknown | ml-for-systems | Detect/distill/update pipeline for keeping learned DB components correct under distribution shift; single-node CPU or one GPU. Concern: no repo link found in the arXiv preprint (2210.05508) or via search |
| 11 | Optimizing Tensor Programs on Flexible Storage | https://dl.acm.org/doi/10.1145/3588717 | https://dl.acm.org/doi/pdf/10.1145/3588717 | unknown | ml-systems | Compiler-style optimization of tensor programs jointly with storage/layout formats - ML-compiler territory, CPU-only. Concern: arXiv preprint (2210.06267) contains no artifact link |
| 12 | FactorJoin: A New Cardinality Estimation Framework for Join Queries | https://dl.acm.org/doi/10.1145/3588721 | https://dl.acm.org/doi/pdf/10.1145/3588721 | https://github.com/wuziniu/FactorJoin | ml-for-systems | Factor-graph cardinality estimator for joins - learned/statistical component inside the optimizer; runs on CPU with public benchmarks |
| 13 | MRV: Enforcing Numeric Invariants in Parallel Updates to Hotspots with Randomized Splitting | https://dl.acm.org/doi/10.1145/3588723 | https://dl.acm.org/doi/pdf/10.1145/3588723 | unknown | other-userspace | Randomized splitting of hot numeric records to remove update hotspots while preserving invariants; the mechanism itself is a user-space concurrency technique. Concern: motivation and evaluation lean on large-scale or geo-distributed deployments; no repo confirmed |
| 14 | Polaris: Enabling Transaction Priority in Optimistic Concurrency Control | https://dl.acm.org/doi/10.1145/3588724 | https://dl.acm.org/doi/pdf/10.1145/3588724 | https://github.com/chenhao-ye/polaris | scheduling | Transaction prioritization inside optimistic concurrency control on one multicore machine - a scheduling policy with a released artifact |
| 15 | SplinterDB and Maplets: Improving the Tradeoffs in Key-Value Store Compaction Policy | https://dl.acm.org/doi/10.1145/3588726 | https://dl.acm.org/doi/pdf/10.1145/3588726 | https://github.com/vmware/splinterdb | storage | LSM compaction policy plus maplets (mergeable resizable lossy maps) in a real embedded key-value store - a prime storage improvement target on NVMe. Concern: verify that the maplet variant is in the public SplinterDB tree and not only an internal branch |
| 16 | IcebergHT: High Performance PMEM Hash Tables Through Stability and Low Associativity | https://dl.acm.org/doi/10.1145/3588727 | https://dl.acm.org/doi/pdf/10.1145/3588727 | https://github.com/splatlab/iceberghashtable | storage | Stability plus low-associativity hash table design; artifact released. Concern: headline results target Optane PMEM which this machine lacks, and the build links libpmem - only the DRAM configuration is reproducible |
| 17 | Caerus: A Caching-based Framework for Scalable Temporal Graph Neural Networks | https://dl.acm.org/doi/10.1145/3588737 | https://dl.acm.org/doi/pdf/10.1145/3588737 | https://github.com/LuckyLYM/Orca | caching | Published as Orca: staleness-aware caching of node embeddings to cut temporal-GNN training cost - a cache policy question on one GPU. Concern: title differs between the program page and the final paper |
| 18 | MorphStream: Adaptive Scheduling for Scalable Transactional Stream Processing on Multicores | https://dl.acm.org/doi/10.1145/3588913 | https://dl.acm.org/doi/pdf/10.1145/3588913 | https://github.com/DataSysResearch/MorphStream | scheduling | Adaptive decomposition and scheduling of state transactions across cores - explicitly a multicore scheduling paper with a maintained Java artifact; fits 16C/32T perfectly |
| 19 | The RLR-Tree: A Reinforcement Learning Based R-Tree for Spatial Data | https://dl.acm.org/doi/10.1145/3588917 | https://dl.acm.org/doi/pdf/10.1145/3588917 | https://github.com/Liuguanli/RLRtree | ml-for-systems | Reinforcement learning drives R-tree ChooseSubtree and Split without changing the index structure - a learned policy inside a system, CPU only |
| 20 | Toward Efficient Homomorphic Encryption for Outsourced Databases through Parallel Caching | https://dl.acm.org/doi/10.1145/3588920 | https://dl.acm.org/doi/pdf/10.1145/3588920 | unknown | caching | Parallel caching of ciphertext computations to speed up homomorphic encryption over outsourced data - a caching policy question, CPU only. Concern: no artifact found; HE library dependencies need user-space builds |
| 21 | ST4ML: Machine Learning Oriented Spatio-Temporal Data Processing at Scale | https://dl.acm.org/doi/10.1145/3588941 | https://dl.acm.org/doi/pdf/10.1145/3588941 | https://github.com/Panrong/st4ml | ml-systems | Spatio-temporal feature extraction pipeline for ML - a data preprocessing/loading system. Concern: built on Spark; would need single-node local mode |
| 22 | Grep: A Graph Learning Based Database Partitioning System | https://dl.acm.org/doi/10.1145/3588948 | https://dl.acm.org/doi/pdf/10.1145/3588948 | unknown | ml-for-systems | Graph-learning model that picks partitioning keys - a learned component replacing a DBA heuristic. Concern: target is a distributed DBMS so end-to-end gains need multiple nodes; the learning part alone is single-node. No repo found |
| 23 | Hierarchical Residual Encoding for Multiresolution Compression | https://dl.acm.org/doi/10.1145/3588953 | https://dl.acm.org/doi/pdf/10.1145/3588953 | unknown | storage | Hierarchical residual encoding gives one compressed representation serving many accuracy levels - a compression/storage contribution, CPU only. Concern: no artifact found |
| 24 | NeuroSketch: Fast and Approximate Evaluation of Range Aggregate Queries with Neural Networks | https://dl.acm.org/doi/10.1145/3588954 | https://dl.acm.org/doi/pdf/10.1145/3588954 | https://github.com/szeighami/NeuroSketch | ml-for-systems | Neural network replacing range-aggregate query evaluation, with theory on when it works - a learned system component; small models fit the A5000 easily |
| 25 | Pea Hash: A Performant Extendible Adaptive Hashing Index | https://dl.acm.org/doi/10.1145/3588962 | https://dl.acm.org/doi/pdf/10.1145/3588962 | https://github.com/schencoding/peahash | memory | Extendible adaptive hash index trading latency against memory utilization; repo ships a DRAM-only variant. Concern: best results assume Optane PMEM and AVX-512 - the Zen3 Threadripper has neither, so expect a scaled-down baseline |
| 26 | Kepler: Robust Learning for Parametric Query Optimization | https://dl.acm.org/doi/10.1145/3588963 | https://dl.acm.org/doi/pdf/10.1145/3588963 | https://github.com/google/kepler | ml-for-systems | Learned parametric query optimization with row-count evolution and SNGP confidence - ML-based tuning with a released artifact and Postgres integration |
| 27 | ForestTI: A Scalable Inverted-Index-Oriented Timeseries Management System with Flexible Memory Efficiency | https://dl.acm.org/doi/10.1145/3589260 | https://dl.acm.org/doi/pdf/10.1145/3589260 | unknown | storage | In-memory inverted-index structures for time-series ingestion with a tunable memory/throughput knob - storage engine work on one node. Concern: no artifact found |
| 28 | DARQ Matter Binds Everything: Performant and Composable Cloud Programming via Resilient Steps | https://dl.acm.org/doi/10.1145/3589262 | https://dl.acm.org/doi/pdf/10.1145/3589262 | unknown | other-userspace | Resilient-step abstraction and speculative durability for composable cloud programs - a user-space runtime idea. Concern: evaluated as a distributed cloud service, so a single-host multi-process scale-down is needed; no artifact confirmed (possibly inside microsoft/FASTER) |
| 29 | BtrBlocks: Efficient Columnar Compression for Data Lakes | https://dl.acm.org/doi/10.1145/3589263 | https://dl.acm.org/doi/pdf/10.1145/3589263 | https://github.com/maxi-k/btrblocks | storage | Columnar compression scheme for data-lake formats with a well-maintained C++ artifact; pure CPU, easy to benchmark and improve on this machine |
| 30 | GIO: Generating Efficient Matrix and Frame Readers for Custom Data Formats by Example | https://dl.acm.org/doi/10.1145/3589265 | https://dl.acm.org/doi/pdf/10.1145/3589265 | https://github.com/apache/systemds | ml-systems | Generates efficient matrix/frame readers for custom data formats - an ML data-loading/ingestion contribution in Apache SystemDS. Concern: code embedded in the SystemDS tree |
| 31 | Automating and Optimizing Data-Centric What-If Analyses on Native Machine Learning Pipelines | https://dl.acm.org/doi/10.1145/3589273 | https://dl.acm.org/doi/pdf/10.1145/3589273 | https://github.com/stefan-grafberger/mlwhatif | ml-systems | Automatic multi-query optimization and reuse across what-if re-executions of native ML pipelines - an ML pipeline runtime, CPU only, clean Python artifact |
| 32 | Updatable Learned Indexes Meet Disk-Resident DBMS - From Evaluations to Design Choices | https://dl.acm.org/doi/10.1145/3589284 | https://dl.acm.org/doi/pdf/10.1145/3589284 | https://github.com/rmitbggroup/LearnedIndexDiskExp | ml-for-systems | Systematic disk-resident evaluation of updatable learned indexes vs B+-tree with released code - ideal reproduction-or-improvement target on NVMe |
| 33 | InfiniFilter: Expanding Filters to Infinity and Beyond | https://dl.acm.org/doi/10.1145/3589285 | https://dl.acm.org/doi/pdf/10.1145/3589285 | https://github.com/nivdayan/FilterLibrary | storage | Filter that expands capacity while keeping a false-positive bound - the filter component of LSM key-value stores; Java artifact, CPU only |
| 34 | Exploiting Structure in Regular Expression Queries | https://dl.acm.org/doi/10.1145/3589297 | https://dl.acm.org/doi/pdf/10.1145/3589297 | https://github.com/mush-zhang/Blare | other-userspace | BLARE: multi-armed-bandit runtime strategy layered on existing regex libraries (RE2, PCRE2, Boost, ICU) - a user-space runtime/adaptive-execution artifact that builds and runs without root |
| 35 | DUCATI: A Dual-Cache Training System for Graph Neural Networks on Giant Graphs with GPU | https://dl.acm.org/doi/10.1145/3589311 | https://dl.acm.org/doi/pdf/10.1145/3589311 | https://github.com/initzhang/DUCATI_SIGMOD | caching | Dual GPU cache (adjacency plus features) with budget allocation for mini-batch GNN training on one GPU - a cache-policy improvement target that fits 24 GB |
| 36 | A Unified and Efficient Coordinating Framework for Autonomous DBMS Tuning | https://dl.acm.org/doi/10.1145/3589331 | https://dl.acm.org/doi/pdf/10.1145/3589331 | unknown | ml-for-systems | Coordinating framework for multiple ML-based DBMS tuning agents (knobs, index, view) - ML-based tuning. Concern: no artifact link found in the arXiv preprint (2303.05710) or via search |
| 37 | WISK: A Workload-aware Learned Index for Spatial Keyword Queries | https://dl.acm.org/doi/10.1145/3589332 | https://dl.acm.org/doi/pdf/10.1145/3589332 | unknown | ml-for-systems | Workload-aware learned index for spatial keyword queries - a learned index, CPU only, arXiv preprint available. Concern: no official code repository found via GitHub or web search |

## All papers
| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | Sequence-Based Target Coin Prediction for Cryptocurrency Pump-and-Dump | out-topic | cryptocurrency pump-and-dump prediction - data mining |
| 2 | LadderFilter: Filtering Infrequent Items with Small Memory and Time Overhead | out-topic | stream sketch/filter algorithm for frequency estimation |
| 3 | Time2State: An Unsupervised Framework for Inferring the Latent States in Time Series Data | out-topic | unsupervised time-series state inference |
| 4 | Incremental Tabular Learning on Heterogeneous Feature Space | out-topic | incremental learning on tabular data |
| 5 | GitTables: A Large-Scale Corpus of Relational Tables | out-topic | relational table corpus/dataset |
| 6 | Raster Intervals: An Approximation Technique for Polygon Intersection Joins | out-topic | spatial polygon join approximation algorithm |
| 7 | Runtime Variation in Big Data Analytics | out-topic | measurement study of cloud job runtime variability |
| 8 | Efficient and Effective Cardinality Estimation for Skyline Family | out-topic | skyline cardinality estimation algorithm |
| 9 | FlexMoE: Scaling Large-scale Sparse Pre-trained Model Training via Dynamic Device Placement | out-machine | MoE training whose contribution is dynamic expert placement across many GPUs and nodes - no meaningful single-GPU scale-down |
| 10 | Efficient and Portable Einstein Summation in SQL | included | Compiles Einstein-summation tensor expressions into portable SQL and runs them in a relational engine - a CPU-only single-node tensor runtime. Concern: contribution is a query-compilation technique rather than an ML runtime; no official repo found in GitHub or web search |
| 11 | Spatio-Temporal Denoising Graph Autoencoders with Data Augmentation for Photovoltaic Data Imputation | out-topic | photovoltaic time-series imputation model |
| 12 | FEC: Efficient Deep Recommendation Model Training with Flexible Embedding Communication | out-machine | core contribution is embedding communication (AllReduce/prefetch) in multi-node distributed recommender training |
| 13 | SSIN: Self-Supervised Learning for Rainfall Spatial Interpolation | out-topic | rainfall spatial interpolation model |
| 14 | Near-Duplicate Sequence Search at Scale for Neural Language Model Memorization Evaluation | out-topic | near-duplicate text sequence search for an LLM memorization study - text search, not an inference system |
| 15 | AWARE: Workload-aware, Redundancy-exploiting Linear Algebra | included | Workload-aware lossless compression for linear algebra inside Apache SystemDS; single-node CPU ML runtime with clear performance hypotheses. Concern: code lives in the large SystemDS codebase rather than a standalone artifact |
| 16 | Unsupervised Hashing with Semantic Concept Mining | out-topic | unsupervised hashing for image retrieval |
| 17 | CompressGraph: Efficient Parallel Graph Analytics with Rule-Based Compression | included | Rule-based graph compression with direct computation on the compressed form; user-space C++ engine on multicore CPU. Concern: graph-analytics flavour rather than OS-level systems |
| 18 | A New Sparse Data Clustering Method Based on Frequent Items | out-topic | sparse categorical clustering algorithm |
| 19 | Virtual-Memory Assisted Buffer Management | included | Buffer pool built on hardware virtual memory - directly a user-space memory-management design and an excellent improvement target. Concern: the second half of the paper (exmap) is a Linux kernel module and cannot be built or loaded without root; only vmcache itself is reproducible here |
| 20 | iFlipper: Label Flipping for Individual Fairness | out-topic | label flipping for individual fairness |
| 21 | SANTOS: Relationship-based Semantic Table Union Search | out-topic | semantic table union search |
| 22 | Effectiveness Perspectives and a Deep Relevance Model for Spatial Keyword Queries | out-topic | relevance model for spatial keyword queries |
| 23 | Circinus: Fast Redundancy-Reduced Subgraph Matching | out-topic | subgraph matching algorithm |
| 24 | Composite Object Normal Forms | out-topic | normal form theory for schema design |
| 25 | EAR-Oracle: On Efficient Indexing for Distance Queries between Arbitrary Points on Terrain Surface | out-topic | terrain-surface distance index |
| 26 | Fast Continuous Subgraph Matching over Streaming Graphs via Backtracking Reduction | out-topic | continuous subgraph matching over streaming graphs |
| 27 | Efficient Estimation of Pairwise Effective Resistance | out-topic | effective resistance estimation algorithm |
| 28 | One-shot garbage collection for in-memory OLTP through temporality-aware version storage | included | One-shot GC and temporality-aware version storage for in-memory MVCC OLTP - user-space memory reclamation on one multicore machine. Concern: no public repo located via GitHub search or web search; marked unknown rather than excluded |
| 29 | AutoOD: Automatic Outlier Detection | out-topic | automatic outlier detection / AutoML |
| 30 | A Neural Approach to Spatio-Temporal Data Release with User-Level Differential Privacy | out-topic | differentially private spatio-temporal data release |
| 31 | Most Expected Winner: An Interpretation of Winners over Uncertain Voter Preferences | out-topic | social choice / winner determination theory |
| 32 | Grouping Time Series for Efficient Columnar Storage | included | Groups time series to cut columnar timestamp storage overhead - a storage-engine/compression contribution evaluated on a single node. Concern: implementation is reported inside Apache IoTDB but no dedicated artifact repo was confirmed |
| 33 | How To Optimize My Blockchain? A Multi-Level Recommendation Approach | out-topic | blockchain configuration recommendation |
| 34 | Personalized PageRank on Evolving Graphs with an Incremental Index-Update Scheme | out-topic | Personalized PageRank graph algorithm |
| 35 | Transaction Scheduling: From Conflicts to Runtime Conflicts | included | Runtime-conflict-aware scheduling of transactions across cores of a single multicore machine; fits the scheduling topic and the hardware. Concern: no public artifact found |
| 36 | ClipSim: A GPU-friendly Parallel Framework for Single-Source SimRank with Accuracy Guarantee | out-topic | SimRank graph algorithm; GPU used only as an accelerator for a graph kernel |
| 37 | Speeding Up End-to-end Query Execution via Learning-based Progressive Cardinality Estimation | included | Learned progressive cardinality estimator - a learned component inside a query engine with an explicit inference-latency vs accuracy tradeoff to improve. Concern: no public repo found |
| 38 | Distributed GPU Joins on Fast RDMA-capable Networks | out-machine | distributed GPU joins whose design depends on fast RDMA networks and multiple GPU nodes |
| 39 | dbET: Execution Time Distribution-based Plan Selection | included | Conformal-prediction-based execution-time distributions for plan selection - an ML component inside the optimizer. Concern: no public repo found; industrial co-authors (Huawei) |
| 40 | Ground Truth Inference for Weakly Supervised Entity Matching | out-topic | weakly supervised entity matching |
| 41 | Detect, Distill and Update: Learned DB Systems Facing Out of Distribution Data | included | Detect/distill/update pipeline for keeping learned DB components correct under distribution shift; single-node CPU or one GPU. Concern: no repo link found in the arXiv preprint (2210.05508) or via search |
| 42 | I/O-Efficient Butterfly Counting at Scale | out-topic | butterfly counting graph algorithm |
| 43 | LiteHST: A Tree Embedding based Method for Similarity Search | out-topic | metric-space similarity search index |
| 44 | Optimizing Tensor Programs on Flexible Storage | included | Compiler-style optimization of tensor programs jointly with storage/layout formats - ML-compiler territory, CPU-only. Concern: arXiv preprint (2210.06267) contains no artifact link |
| 45 | LinCQA: Faster Consistent Query Answering with Linear Time Guarantees | out-topic | consistent query answering theory |
| 46 | Probabilistic Reasoning at Scale: Trigger Graphs to the Rescue | out-topic | probabilistic rule reasoning |
| 47 | Foreign Keys Open the Door for Faster Incremental View Maintenance | out-topic | incremental view maintenance in a query engine |
| 48 | FactorJoin: A New Cardinality Estimation Framework for Join Queries | included | Factor-graph cardinality estimator for joins - learned/statistical component inside the optimizer; runs on CPU with public benchmarks |
| 49 | FlexER: Flexible Entity Resolution for Multiple Intents | out-topic | entity resolution with multiple intents |
| 50 | MRV: Enforcing Numeric Invariants in Parallel Updates to Hotspots with Randomized Splitting | included | Randomized splitting of hot numeric records to remove update hotspots while preserving invariants; the mechanism itself is a user-space concurrency technique. Concern: motivation and evaluation lean on large-scale or geo-distributed deployments; no repo confirmed |
| 51 | Polaris: Enabling Transaction Priority in Optimistic Concurrency Control | included | Transaction prioritization inside optimistic concurrency control on one multicore machine - a scheduling policy with a released artifact |
| 52 | An Efficient Algorithm for Distance-based Structural Graph Clustering | out-topic | structural graph clustering algorithm |
| 53 | SplinterDB and Maplets: Improving the Tradeoffs in Key-Value Store Compaction Policy | included | LSM compaction policy plus maplets (mergeable resizable lossy maps) in a real embedded key-value store - a prime storage improvement target on NVMe. Concern: verify that the maplet variant is in the public SplinterDB tree and not only an internal branch |
| 54 | IcebergHT: High Performance PMEM Hash Tables Through Stability and Low Associativity | included | Stability plus low-associativity hash table design; artifact released. Concern: headline results target Optane PMEM which this machine lacks, and the build links libpmem - only the DRAM configuration is reproducible |
| 55 | Efficient Sampling Approaches to Shapley Value Approximation | out-topic | Shapley value approximation algorithms |
| 56 | Maximum k-Biplex Search on Bipartite Graphs: A Symmetric-BK Branching Approach | out-topic | maximal k-biplex enumeration |
| 57 | TED: Towards Discovering Top-𝑘 Edge-Diversified Patterns in a Graph Database | out-topic | edge-diversified graph pattern mining |
| 58 | Caerus: A Caching-based Framework for Scalable Temporal Graph Neural Networks | included | Published as Orca: staleness-aware caching of node embeddings to cut temporal-GNN training cost - a cache policy question on one GPU. Concern: title differs between the program page and the final paper |
| 59 | SafeBound: A Practical System for Generating Cardinality Bounds | out-topic | non-learned cardinality bounding for query optimization |
| 60 | Efficient Approximate Nearest Neighbor Search in Multi-dimensional Databases | out-topic | proximity-graph ANN search algorithm |
| 61 | Detecting Logic Bugs of Join Optimizations in DBMS | out-topic | logic-bug testing of DBMS join optimizers |
| 62 | TowerSensing: Linearly Compressing Sketches with Flexibility | out-topic | sketch compression algorithm for data streams |
| 63 | A Universal Question-Answering Platform for Knowledge Graphs | out-topic | knowledge graph question answering platform |
| 64 | Fast Density-Based Clustering: Geometric Approach | out-topic | DBSCAN clustering algorithm |
| 65 | MorphStream: Adaptive Scheduling for Scalable Transactional Stream Processing on Multicores | included | Adaptive decomposition and scheduling of state transactions across cores - explicitly a multicore scheduling paper with a maintained Java artifact; fits 16C/32T perfectly |
| 66 | An Effective and Differentially Private Protocol for Secure Distributed Cardinality Estimation | out-topic | differentially private distributed cardinality sketch |
| 67 | Towards Generating Hop-constrained s-t Simple Path Graphs | out-topic | hop-constrained path enumeration |
| 68 | GeoGauss: Strongly Consistent Coordinator-Free OLTP for Geo-Replicated SQL Database | out-machine | geo-replicated OLTP requiring multiple geographically separated sites |
| 69 | The RLR-Tree: A Reinforcement Learning Based R-Tree for Spatial Data | included | Reinforcement learning drives R-tree ChooseSubtree and Split without changing the index structure - a learned policy inside a system, CPU only |
| 70 | Robust and Transferable Log-based Anomaly Detection | out-topic | ML model for log anomaly detection |
| 71 | Matching Roles from Temporal Data | out-topic | integrity constraints over temporal fact data |
| 72 | Toward Efficient Homomorphic Encryption for Outsourced Databases through Parallel Caching | included | Parallel caching of ciphertext computations to speed up homomorphic encryption over outsourced data - a caching policy question, CPU only. Concern: no artifact found; HE library dependencies need user-space builds |
| 73 | Efficient Resistance Distance Computation: the Power of Landmark-based Approaches | out-topic | resistance distance computation algorithm |
| 74 | Scaling Up k-Clique Densest Subgraph Detection | out-topic | k-clique densest subgraph algorithm |
| 75 | Discovering Top-k Rules using Subjective and Objective Criteria | out-topic | rule discovery with subjective/objective criteria |
| 76 | FINEX: A Fast Index for Exact & Flexible Density-Based Clustering | out-topic | density-based clustering index |
| 77 | DBPA: A Benchmark for Transactional Database Performance Anomalies | out-topic | benchmark/dataset for transactional performance anomalies |
| 78 | Efficiently Computing Join Orders with Heuristic Search | out-topic | join order enumeration algorithm |
| 79 | T-FSM: A Task-Based System for Massively Parallel Frequent Subgraph Pattern Mining from a Big Graph | out-topic | frequent subgraph pattern mining |
| 80 | Discovering Similarity Inclusion Dependencies | out-topic | similarity inclusion dependency discovery |
| 81 | Effective and Efficient PageRank-based Positioning for Graph Visualization | out-topic | graph visualization layout |
| 82 | Maximal Defective Clique Enumeration | out-topic | maximal defective clique enumeration |
| 83 | Efficient Biclique Counting in Large Bipartite Graphs | out-topic | biclique counting in bipartite graphs |
| 84 | Double-Anonymous Sketch: Achieving Fairness for Finding Global Top-K Frequent Items | out-topic | stream sketch for global top-K |
| 85 | Managing Conflicting Interests of Stakeholders in Influencer Marketing | out-topic | influencer marketing optimization |
| 86 | JoinSketch: A Sketch Algorithm for Accurate and Unbiased Inner-Product Estimation | out-topic | sketch for inner-product estimation |
| 87 | Regularized Pairwise Relationship based Analytics for Structured Data | out-topic | deep model for structured data analytics |
| 88 | Together is Better: Heavy Hitters Latency Quantile Estimation | out-topic | stream quantile sketch |
| 89 | Unicorn: A Unified Multi-tasking Model for Supporting Matching Tasks in Data Integration | out-topic | multi-task model for data integration matching |
| 90 | Time Series Data Validity | out-topic | data quality/validity measure |
| 91 | Making It Tractable to Catch Duplicates and Conflicts in Graphs | out-topic | graph cleaning rules for entity and conflict resolution |
| 92 | ST4ML: Machine Learning Oriented Spatio-Temporal Data Processing at Scale | included | Spatio-temporal feature extraction pipeline for ML - a data preprocessing/loading system. Concern: built on Spark; would need single-node local mode |
| 93 | Learned Data-aware Image Representations of Line Charts for Similarity Search | out-topic | line-chart image similarity search |
| 94 | RLS Side Channels: Investigating Leakage of Row-Level Security Protected Data Through Query Execution Time | out-topic | security side-channel measurement study of row-level security |
| 95 | LightRW: FPGA Accelerated Graph Dynamic Random Walks | out-machine | FPGA accelerator - no FPGA available |
| 96 | HybridPipe: Combining Human-generated and Machine-generated Pipelines for Data Preparation | out-topic | AutoML data preparation pipeline synthesis |
| 97 | Ready to Leap (by Co-Design)? Join Order Optimisation on Quantum Hardware | out-machine | requires quantum processing units |
| 98 | Mining Geospatial Relationships from Text | out-topic | geospatial knowledge graph construction from text |
| 99 | Grep: A Graph Learning Based Database Partitioning System | included | Graph-learning model that picks partitioning keys - a learned component replacing a DBA heuristic. Concern: target is a distributed DBMS so end-to-end gains need multiple nodes; the learning part alone is single-node. No repo found |
| 100 | BALANCE: Bayesian Linear Attribution for Root Cause Localization | out-topic | root cause localization method for operations |
| 101 | Efficient Tree-SVD for Subset Node Embedding over Large Dynamic Graphs | out-topic | dynamic graph embedding algorithm |
| 102 | AutoCTS+: Joint Neural Architecture and Hyperparameter Search for Correlated Time Series Forecasting | out-topic | neural architecture search for time series forecasting |
| 103 | When Private Blockchain Meets Deterministic Database | out-machine | private blockchain versus deterministic database - replication across multiple nodes is the object of study |
| 104 | Hierarchical Residual Encoding for Multiresolution Compression | included | Hierarchical residual encoding gives one compressed representation serving many accuracy levels - a compression/storage contribution, CPU only. Concern: no artifact found |
| 105 | NeuroSketch: Fast and Approximate Evaluation of Range Aggregate Queries with Neural Networks | included | Neural network replacing range-aggregate query evaluation, with theory on when it works - a learned system component; small models fit the A5000 easily |
| 106 | INEv: In-Network Evaluation for Event Stream Processing | out-machine | in-network evaluation distributes sub-queries across network nodes; the contribution is the multi-node placement |
| 107 | Graph Learning for Interaction Analysis in Smart Home Rule Data | out-topic | threat detection in smart home rule data |
| 108 | dsJSON: A Distributed SQL JSON Processor | out-machine | distributed Spark JSON processor; contribution is cluster-scale parsing and partitioning |
| 109 | When Tree Meets Hash: Reducing Random Reads for Index Structures on Persistent Memories | out-machine | index design specific to Optane persistent memory - no PM on this machine |
| 110 | Pontus: Finding Waves in Data Streams | out-topic | stream sketch for wave/burst detection |
| 111 | FEAST: A Communication-efficient Federated Feature Selection Framework for Relational Data | out-topic | federated feature selection algorithm for vertical federated learning |
| 112 | Pea Hash: A Performant Extendible Adaptive Hashing Index | included | Extendible adaptive hash index trading latency against memory utilization; repo ships a DRAM-only variant. Concern: best results assume Optane PMEM and AVX-512 - the Zen3 Threadripper has neither, so expect a scaled-down baseline |
| 113 | Kepler: Robust Learning for Parametric Query Optimization | included | Learned parametric query optimization with row-count evolution and SNGP confidence - ML-based tuning with a released artifact and Postgres integration |
| 114 | Dumpy: A Compact and Adaptive Index for Large Data Series Collections | out-topic | data series similarity search index |
| 115 | Design and Analysis of a Processing-in-DIMM Join Algorithm: A Case Study with UPMEM DIMMs | out-machine | processing-in-DIMM join on UPMEM hardware |
| 116 | Parallel Strong Connectivity Based on Faster Reachability | out-topic | parallel strongly connected components algorithm |
| 117 | ForestTI: A Scalable Inverted-Index-Oriented Timeseries Management System with Flexible Memory Efficiency | included | In-memory inverted-index structures for time-series ingestion with a tunable memory/throughput knob - storage engine work on one node. Concern: no artifact found |
| 118 | Efficient and Effective Attributed Hypergraph Clustering via K-Nearest Neighbor Augmentation | out-topic | attributed hypergraph clustering |
| 119 | DARQ Matter Binds Everything: Performant and Composable Cloud Programming via Resilient Steps | included | Resilient-step abstraction and speculative durability for composable cloud programs - a user-space runtime idea. Concern: evaluated as a distributed cloud service, so a single-host multi-process scale-down is needed; no artifact confirmed (possibly inside microsoft/FASTER) |
| 120 | BtrBlocks: Efficient Columnar Compression for Data Lakes | included | Columnar compression scheme for data-lake formats with a well-maintained C++ artifact; pure CPU, easy to benchmark and improve on this machine |
| 121 | Practical Differentially Private and Byzantine-resilient Federated Learning | out-topic | differentially private Byzantine-resilient federated learning algorithm |
| 122 | GIO: Generating Efficient Matrix and Frame Readers for Custom Data Formats by Example | included | Generates efficient matrix/frame readers for custom data formats - an ML data-loading/ingestion contribution in Apache SystemDS. Concern: code embedded in the SystemDS tree |
| 123 | Prerequisite-driven Fair Clustering on Heterogeneous Information Networks | out-topic | fair clustering on heterogeneous information networks |
| 124 | Better than Composition: How to Answer Multiple Relational Queries under Differential Privacy | out-topic | differentially private query answering |
| 125 | A Step Toward Deep Online Aggregation | out-topic | online aggregation for query processing |
| 126 | LightCTS: A Lightweight Framework for Correlated Time Series Forecasting | out-topic | lightweight time-series forecasting model |
| 127 | rkHit: Representative Query with Uncertain Preference | out-topic | representative top-k query semantics |
| 128 | HR-Index: An Effectiveness Index Method for Historical Reachability Queries over Evolving Graphs | out-topic | historical reachability index for evolving graphs |
| 129 | Automating and Optimizing Data-Centric What-If Analyses on Native Machine Learning Pipelines | included | Automatic multi-query optimization and reuse across what-if re-executions of native ML pipelines - an ML pipeline runtime, CPU only, clean Python artifact |
| 130 | A Framework for Privacy Preserving Localized Graph Pattern Query Processing | out-topic | privacy-preserving graph pattern query processing |
| 131 | T-Rex: Optimizing Pattern Search on Time Series | out-topic | time-series pattern search operator |
| 132 | Design Guidelines for Correct, Efficient, and Scalable Synchronization using One-Sided RDMA | out-machine | one-sided RDMA synchronization design - no RDMA hardware |
| 133 | Theories and Principles Matter: Towards Visually Appealing and Effective Abstraction of Property Graph Queries | out-topic | visual abstraction of property graph queries |
| 134 | Efficient Star-based Truss Maintenance on Dynamic Graphs | out-topic | k-truss maintenance on dynamic graphs |
| 135 | QaaD (Query-as-a-Data): Scalable Execution of Massive Number of Small Queries in Spark | out-topic | Spark query-execution technique for batching many small queries |
| 136 | Exploratory Training: When Annonators Learn About Data | out-topic | active learning with imperfect annotators |
| 137 | Predicate Pushdown for Data Science Pipelines | out-topic | predicate pushdown rules for data science pipelines - query optimization |
| 138 | High-Dimensional Approximate Nearest Neighbor Search: with Reliable and Efficient Distance Comparison Operations | out-topic | high-dimensional ANN search algorithm |
| 139 | Hereditary Cohesive Subgraphs Enumeration on Bipartite Graphs: The Power of Pivot-based Approaches | out-topic | hereditary cohesive subgraph enumeration |
| 140 | Updatable Learned Indexes Meet Disk-Resident DBMS - From Evaluations to Design Choices | included | Systematic disk-resident evaluation of updatable learned indexes vs B+-tree with released code - ideal reproduction-or-improvement target on NVMe |
| 141 | InfiniFilter: Expanding Filters to Infinity and Beyond | included | Filter that expands capacity while keeping a false-positive bound - the filter component of LSM key-value stores; Java artifact, CPU only |
| 142 | Shortest Paths Discovery in Uncertain Networks via Transfer Learning | out-topic | shortest path in uncertain networks |
| 143 | PrivLava: Synthesizing Relational Data with Foreign Keys under Differential Privacy | out-topic | differentially private relational data synthesis |
| 144 | Scalable and Efficient Full-Graph GNN Training for Large Graphs | out-machine | G3 is a distributed full-graph GNN trainer for billion-edge graphs across many GPUs and nodes; also no public artifact was found |
| 145 | ML2DAC: Meta-Learning to Democratize AutoML for Clustering Analysis | out-topic | meta-learning AutoML for clustering |
| 146 | OM^3: An Ordered Multi-level Min-Max Representation for Interactive Progressive Visualization of Time Series | out-topic | time-series visualization representation |
| 147 | Scapin: Scalable Graph Structure Perturbation by Augmented Influence Maximization | out-topic | graph structure perturbation for GNN robustness |
| 148 | Few-shot Text-to-SQL Translation using Structure and Content Prompt Learning | out-topic | few-shot text-to-SQL translation |
| 149 | Detock: High Performance Multi-region Transactions at Scale | out-machine | multi-region geo-distributed transaction protocol |
| 150 | Measuring Re-identification Risk | out-topic | theoretical re-identification risk measurement |
| 151 | Free Join: Unifying Worst-Cast Optimal and Traditional Joins | out-topic | worst-case optimal join algorithm |
| 152 | Generalizing Bulk-Synchronous Parallel Processing for Data Science: from data to threads and agent-based simulations | out-machine | generalizes bulk-synchronous parallel processing for cluster-scale agent-based simulation |
| 153 | Exploiting Structure in Regular Expression Queries | included | BLARE: multi-armed-bandit runtime strategy layered on existing regex libraries (RE2, PCRE2, Boost, ICU) - a user-space runtime/adaptive-execution artifact that builds and runs without root |
| 154 | Computing the Difference of Conjunctive Queries Efficiently | out-topic | algorithm for the difference of conjunctive queries |
| 155 | Global and Local Differentially Private Release of Count-Weighted Graphs | out-topic | differentially private graph release |
| 156 | QHL: A Fast Algorithm for Exact Constrained Shortest Path Search on Road Networks | out-topic | constrained shortest path on road networks |
| 157 | XInsight: eXplainable Data Analysis Through The Lens of Causality | out-topic | causal explanation framework for exploratory data analysis |
| 158 | GoodCore: Coreset Selection over Incomplete Data for Data-effective and Data-efficient Machine Learning | out-topic | coreset selection over incomplete data |
| 159 | Incentive-Aware Decentralized Data Collaboration | out-topic | incentive design for decentralized data collaboration |
| 160 | Deep Active Alignment of Knowledge Graph Entities and Schemata | out-topic | knowledge graph entity and schema alignment |
| 161 | Efficient Personalized PageRank Computation: The Power of Variance-Reduced Monte Carlo Approaches | out-topic | Personalized PageRank Monte Carlo algorithm |
| 162 | Using Cloud Functions as Accelerator for Elastic Data Analytics | out-machine | requires AWS Lambda cloud function infrastructure |
| 163 | Data Stream Clustering: An In-depth Empirical Study | out-topic | empirical study of data stream clustering algorithms |
| 164 | EARLY: Efficient and Reliable Graph Neural Network for Dynamic Graphs | out-topic | GNN method for dynamic graphs |
| 165 | Popularity Ratio Maximization: Surpassing Competitors through Influence Propagation | out-topic | influence propagation and popularity maximization |
| 166 | DUCATI: A Dual-Cache Training System for Graph Neural Networks on Giant Graphs with GPU | included | Dual GPU cache (adjacency plus features) with budget allocation for mini-batch GNN training on one GPU - a cache-policy improvement target that fits 24 GB |
| 167 | GuP: Fast Subgraph Matching by Guard-based Pruning | out-topic | subgraph matching with guard-based pruning |
| 168 | DeltaBoost: Gradient Boosting Decision Trees with Efficient Machine Unlearning | out-topic | machine unlearning algorithm for gradient boosted trees |
| 169 | Efficient and Effective Algorithms for Generalized Densest Subgraph Discovery | out-topic | generalized densest subgraph algorithms |
| 170 | On Querying Connected Components in Large Temporal Graphs | out-topic | connected components in temporal graphs |
| 171 | LightTS: Lightweight Time Series Classification with Adaptive Ensemble Distillation | out-topic | time series classification model |
| 172 | Data-Sharing Markets: Model, Protocol, and Algorithms to Incentivize the Formation of Data-Sharing Consortia | out-topic | data-sharing market protocols and incentives |
| 173 | Ghost: A General Framework for High-Performance Online Similarity Queries over Distributed Trajectory Streams | out-machine | online similarity queries over distributed trajectory streams; the contribution is the distributed streaming framework |
| 174 | LAQy: Efficient and Reusable Query Approximations via Lazy Sampling | out-topic | approximate query processing via lazy sampling |
| 175 | Mitigating Filter Bubbles Under a Competitive Diffusion Model | out-topic | filter bubble mitigation in diffusion models |
| 176 | Maestro: Automatic Generation of Comprehensive Benchmarks for Question Answering Over Knowledge Graphs | out-topic | benchmark generation for knowledge graph question answering |
| 177 | Selection Pushdown in Column Stores using Bit Manipulation Instructions | out-no-code | in scope on topic (BMI-based decoding and selection pushdown for Parquet) but no official implementation - GitHub repository search and a targeted web search found only the Microsoft Research page plus an apache/arrow feature request citing the paper |
| 178 | Query-Guided Resolution of Uncertain Databases | out-topic | oracle-guided cleaning of uncertain databases |
| 179 | Efficient GPU-Accelerated Subgraph Matching | out-topic | GPU-accelerated subgraph matching algorithm |
| 180 | Hamming Tree: The case for Energy-Aware Indexing for NVMs | out-machine | energy-aware NVM indexing requires NVM hardware and energy/bit-flip measurement |
| 181 | DiffPrep: Differentiable Data Preprocessing Pipeline Search for Learning over Tabular Data | out-topic | differentiable AutoML search over preprocessing pipelines |
| 182 | GraphINC: Graph Pattern Mining at Network Speed | out-machine | graph pattern mining offloaded to programmable network hardware |
| 183 | Efficient Query Re-optimization with Judicious Subquery Selections | out-topic | query re-optimization with subquery selection |
| 184 | A Unified and Efficient Coordinating Framework for Autonomous DBMS Tuning | included | Coordinating framework for multiple ML-based DBMS tuning agents (knobs, index, view) - ML-based tuning. Concern: no artifact link found in the arXiv preprint (2303.05710) or via search |
| 185 | WISK: A Workload-aware Learned Index for Spatial Keyword Queries | included | Workload-aware learned index for spatial keyword queries - a learned index, CPU only, arXiv preprint available. Concern: no official code repository found via GitHub or web search |
| 186 | DAMR: Dynamic Adjacency Matrix Representation Learning for Multivariate Time Series Imputation | out-topic | multivariate time series imputation model |
