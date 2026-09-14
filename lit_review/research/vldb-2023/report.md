STATUS: complete
TOTAL_PAPERS: 287
INCLUDED: 53

## Sources

Venue definition. PVLDB research-track papers presented at VLDB 2023 (49th VLDB, Vancouver,
28 Aug - 1 Sep 2023) span two PVLDB volumes: **Vol. 15 no. 13** (published after VLDB 2022,
presented at VLDB 2023) and **Vol. 16 no. 1-11**. Vol. 16 no. 12 is the industrial /
demonstration / tutorial / panel / keynote issue and is excluded. Vol. 16 no. 13 was
published in September 2023, after the conference, and none of its 14 papers appear in the
VLDB 2023 accepted-papers list - those were presented at VLDB 2024, so they are excluded too.

Primary enumeration.
- https://www.vldb.org/pvldb/volumes/16/ - parsed the embedded `__NEXT_DATA__` JSON with
  `curl` + Python rather than WebFetch. 393 entries, 13 of which are Front Matter, so 380
  papers. Page numbers run contiguously from 1 to 4352 with **no gaps**, which confirms the
  listing is complete. Removing issue 12 (100 industrial/demo/tutorial/panel entries) and
  issue 13 (14 post-conference papers) leaves **266** research-track papers.
- https://www.vldb.org/pvldb/volumes/15/ - same parse; issue 13 contributes **21** papers
  (22 entries minus Front Matter).
- 266 + 21 = **287**.

Cross-check.
- https://vldb.org/2023/?papers-research - the official VLDB 2023 accepted-papers table,
  parsed to 295 rows with category labels: Research 234, EAB 23, SDS 20, Vision 10,
  VLDBJ 8. The 8 `VLDBJ` rows are VLDB Journal papers given a presentation slot, not PVLDB
  main-track papers, so they are excluded. 295 - 8 = **287**, matching exactly.
- A title-level join between the two sources matched all 287 papers (6 of them through
  small title edits between the accepted list and the final PVLDB version); the 21 papers
  present in the accepted list but absent from Vol. 16 are precisely the Vol. 15 no. 13 set.
- DBLP (`dblp.org/db/journals/pvldb/pvldb16`) was attempted but is behind an Anubis
  bot-challenge and returned no data over `curl`; the two sources above were sufficient.

Topic and machine screen. Titles plus abstracts/first pages. For every surviving paper the
PDF was downloaded and searched for the PVLDB "Artifact Availability" statement and for
repository URLs; all 53 included papers carry an explicit official artifact URL, and every
URL was verified to return HTTP 200. Four candidates were dropped as `out-no-code` after
checking the PDF, arXiv and GitHub/web search, and one (FastFlow) because the repository
named in the paper now returns 404.

Paper links are DOI links (`doi.org/10.14778/...`) extracted from each PDF, which resolve to
the ACM DL page; PDF links are the official vldb.org copies.

## Included
| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | TreeLine: An Update-In-Place Key-Value Store for Modern Storage | https://doi.org/10.14778/3561261.3561270 | https://www.vldb.org/pvldb/vol16/p99-yu.pdf | https://github.com/mitdbg/treeline | storage | Single-node update-in-place KV store on NVMe as a RocksDB alternative; C++ user-space build, io_uring/O_DIRECT only, dataset fits the 257 GB free space |
| 2 | Frequency Domain Data Encoding in Apache IoTDB | https://doi.org/10.14778/3565816.3565829 | https://www.vldb.org/pvldb/vol16/p282-song.pdf | https://github.com/543202718/iotdb/tree/research/descend | storage | Frequency-domain lossy encoding for time-series storage; pure Java single node. Concern: artifact is a personal Apache IoTDB fork branch not upstream |
| 3 | SHiFT: An Efficient, Flexible Search Engine for Transfer Learning | https://doi.org/10.14778/3565816.3565831 | https://www.vldb.org/pvldb/vol16/p304-renggli.pdf | https://github.com/DS3Lab/shift | ml-systems | Search engine over a pretrained-model zoo with cost models and caching; one A5000 suffices for the small models. Concern: full model zoo plus datasets is a large download |
| 4 | Serving and Optimizing Machine Learning Workflows on Heterogeneous Infrastructures | https://doi.org/10.14778/3570690.3570692 | https://www.vldb.org/pvldb/vol16/p406-wu.pdf | https://github.com/libertyeagle/JellyBean | ml-systems | ML-workflow serving and placement optimizer. Concern: original evaluation spans an edge-cloud heterogeneous cluster - on one host it must run as co-located processes or the placement optimizer studied offline from profiles |
| 5 | Optimizing Video Analytics with Declarative Model Relationships | https://doi.org/10.14778/3570690.3570695 | https://www.vldb.org/pvldb/vol16/p447-romero.pdf | https://github.com/stanford-mast/viva-vldb23-artifact | ml-systems | Declarative video analytics that exploits model-relationship hints to trade accuracy for speed; single-GPU inference, AE-reviewed artifact repo |
| 6 | Dalton: Learned Partitioning for Distributed Data Streams | https://doi.org/10.14778/3570690.3570699 | https://www.vldb.org/pvldb/vol16/p491-zapridou.pdf | https://github.com/ezapridou/Dalton | ml-for-systems | RL-learned partitioning for stream operators. Concern: built on Apache Flink - the distributed setup must be emulated with local task managers on the 32 threads |
| 7 | Can Learned Models Replace Hash Functions? | https://doi.org/10.14778/3570690.3570702 | https://www.vldb.org/pvldb/vol16/p532-sabek.pdf | https://github.com/DominikHorn/hashing-benchmark | ml-for-systems | CPU-only study of learned models as hash functions in hash tables and joins; strong reproduce-then-improve target, no GPU or special hardware |
| 8 | TOD: GPU-accelerated Outlier Detection via Tensor Operations | https://doi.org/10.14778/3570690.3570703 | https://www.vldb.org/pvldb/vol16/p546-zhao.pdf | https://github.com/yzhao062/pytod | ml-systems | GPU outlier detection with provable memory-aware batching; explicitly designed for one GPU, PyTorch, fits 24 GB |
| 9 | FILM: a Fully Learned Index for Larger-than-Memory Databases | https://doi.org/10.14778/3570690.3570704 | https://www.vldb.org/pvldb/vol16/p561-ma.pdf | https://github.com/chaohcc/film | ml-for-systems | Learned index for larger-than-memory data; single node, only RAM plus local disk needed |
| 10 | Toward Quantity-of-Interest Preserving Lossy Compression for Scientific Data | https://doi.org/10.14778/3574245.3574255 | https://www.vldb.org/pvldb/vol16/p697-liang.pdf | https://github.com/szcompressor/SZ3/tree/qoi_error_control | storage | Quantity-of-interest preserving error-bounded lossy compression on top of SZ3; CPU-only C++. Concern: reference scientific datasets are tens of GB to download |
| 11 | SubStrat: A Subset-Based Optimization Strategy for Faster AutoML | https://doi.org/10.14778/3574245.3574261 | https://www.vldb.org/pvldb/vol16/p772-somech.pdf | https://github.com/teddy4445/SubStrat | ml-systems | Data-subset strategy that accelerates AutoML search; pure Python CPU workload, small footprint |
| 12 | Excalibur: A Virtual Machine for Adaptive Fine-grained JIT-Compiled Query Execution based on VOILA | https://doi.org/10.14778/3574245.3574266 | https://www.vldb.org/pvldb/vol16/p829-boncz.pdf | https://github.com/t1mm3/db_excalibur | other-userspace | Adaptive fine-grained JIT-compiled query execution VM; C++ single node, LLVM is conda-installable. Concern: research-grade build with heavy dependencies |
| 13 | Making Cache Monotonic and Consistent | https://doi.org/10.14778/3574245.3574271 | https://www.vldb.org/pvldb/vol16/p891-cao.pdf | https://github.com/jiayouanan/mccache | caching | Cache admission and eviction policy that keeps cached query results monotonic and consistent; trace-driven single-node evaluation |
| 14 | SkinnerMT: Parallelizing for Efficiency and Robustness in Adaptive Query Processing on Multicore Platforms | https://doi.org/10.14778/3574245.3574272 | https://www.vldb.org/pvldb/vol16/p905-wei.pdf | https://github.com/cornelldbgroup/skinnerdb/tree/skinnermt | ml-for-systems | Parallel RL-based adaptive query processing on multicore; Java, 16 cores/32 threads is a sensible scale-down of the paper's machine |
| 15 | On Efficient Approximate Queries over Machine Learning Models | https://doi.org/10.14778/3574245.3574273 | https://www.vldb.org/pvldb/vol16/p918-ding.pdf | https://github.com/DujianDing/AQUAPRO | ml-systems | Approximate query processing that minimises expensive ML model invocations using cheap proxy models; one GPU is enough |
| 16 | FederatedScope: A Flexible Federated Learning Platform for Heterogeneity | https://doi.org/10.14778/3579075.3579081 | https://www.vldb.org/pvldb/vol16/p1059-li.pdf | https://github.com/alibaba/FederatedScope | ml-systems | Event-driven federated learning framework; the standard mode simulates many clients as processes on one node with one GPU |
| 17 | Blink-hash: An Adaptive Hybrid Index for In-Memory Time-Series Databases | https://doi.org/10.14778/3583140.3583143 | https://www.vldb.org/pvldb/vol16/p1235-cha.pdf | https://github.com/chahk0129/Blink-hash | storage | In-memory hybrid hash/tree index for time-series ingestion on multicore; C++ DRAM-only. Concern: paper's best numbers use a 4-socket server, we have 1 socket and 16 cores |
| 18 | Scalable and Robust Snapshot Isolation for High-Performance Storage Engines | https://doi.org/10.14778/3583140.3583157 | https://www.vldb.org/pvldb/vol16/p1426-alhomssi.pdf | https://github.com/leanstore/leanstore/tree/mvcc | storage | MVCC/snapshot-isolation redesign inside the LeanStore storage engine; single-node NVMe C++, benchmarks via BenchBase |
| 19 | Lero: A Learning-to-Rank Query Optimizer | https://doi.org/10.14778/3583140.35831601 | https://www.vldb.org/pvldb/vol16/p1466-zhu.pdf | https://github.com/Blondig/Lero-on-PostgreSQL | ml-for-systems | Learning-to-rank query optimizer for PostgreSQL; PostgreSQL builds from source into $HOME, model training is small enough for one GPU or CPU |
| 20 | Robust Query Driven Cardinality Estimation under Changing Workloads | https://doi.org/10.14778/3583140.3583164 | https://www.vldb.org/pvldb/vol16/p1520-negi.pdf | https://github.com/learnedsystems/CEB | ml-for-systems | Robust learned cardinality estimation evaluated on the CEB benchmark; PostgreSQL user-space build plus PyTorch on one GPU |
| 21 | The Case for Learned In-Memory Joins | https://doi.org/10.14778/3587136.3587148 | https://www.vldb.org/pvldb/vol16/p1749-sabek.pdf | https://github.com/ibrahimsabek/learned-joins | ml-for-systems | Learned in-memory sort/hash joins; CPU-only C++ with SOSD-style datasets. Concern: paper uses AVX-512 in places, our Zen3 has only AVX2 |
| 22 | Elf: Erasing-based Lossless Floating-Point Compression | https://doi.org/10.14778/3587136.3587149 | https://www.vldb.org/pvldb/vol16/p1763-li.pdf | https://github.com/Spatio-Temporal-Lab/elf | storage | Erasing-based lossless floating-point compression for time-series storage; Java, single node, modest datasets |
| 23 | LOGER: A Learned Optimizer towards Generating Efficient and Robust Query Execution Plans | https://doi.org/10.14778/3587136.3587150 | https://www.vldb.org/pvldb/vol16/p1777-gao.pdf | https://github.com/TianyiChen0316/LOGER | ml-for-systems | Learned query optimizer generating robust plans on PostgreSQL; GPU-optional training, single node |
| 24 | Sim-Piece: Highly Accurate Piecewise Linear Approximation through Similar Segment Merging | https://doi.org/10.14778/3594512.3594521 | https://www.vldb.org/pvldb/vol16/p1910-liakos.pdf | https://github.com/xkitsios/sim-piece | storage | Piecewise-linear lossy compression for time series; Java, CPU-only, small datasets - easy to reproduce and extend |
| 25 | BASE: Bridging the Gap between Cost and Latency for Query Optimization | https://doi.org/10.14778/3594512.3594525 | https://www.vldb.org/pvldb/vol16/p1958-chen.pdf | https://github.com/Thisislegit/BASE | ml-for-systems | RL query optimizer bridging cost and latency on PostgreSQL; same footprint as Bao/Lero, single node |
| 26 | Learned Index: A Comprehensive Experimental Evaluation | https://doi.org/10.14778/3594512.3594528 | https://www.vldb.org/pvldb/vol16/p1992-li.pdf | https://github.com/curtis-sun/TLI | ml-for-systems | Comprehensive experimental evaluation of learned indexes; CPU-only benchmark harness, a natural reproduction or extension target |
| 27 | What Modern NVMe Storage Can Do, And How To Exploit It: High-Performance I/O for High-Performance Storage Engines | https://doi.org/10.14778/3598581.3598584 | https://www.vldb.org/pvldb/vol16/p2090-haas.pdf | https://github.com/leanstore/leanstore/tree/io | storage | User-space high-IOPS NVMe I/O engine (io_uring, many threads) for storage engines; no root needed. Concern: paper uses 8 enterprise SSDs, we have 2 PM9A3 in software RAID so absolute IOPS will be lower |
| 28 | The FastLanes Compression Layout: Decoding >100 Billion Integers per Second with Scalar Code | https://doi.org/10.14778/3598581.3598587 | https://www.vldb.org/pvldb/vol16/p2132-afroozeh.pdf | https://github.com/cwida/FastLanes | storage | Bit-packing/compression layout decoded with auto-vectorizable scalar code; CPU-only C++. Concern: headline numbers are from AVX-512 and SVE machines, Zen3 gives AVX2 only |
| 29 | Towards Designing and Learning Piecewise Space-Filling Curves | https://doi.org/10.14778/3598581.3598589 | https://www.vldb.org/pvldb/vol16/p2158-li.pdf | https://github.com/gravesprite/Learned-BMTree | ml-for-systems | Learned piecewise space-filling curve for multidimensional indexing; Python plus C++, single node |
| 30 | MiniGraph: Querying Big Graphs with a Single Machine | https://doi.org/10.14778/3598581.3598590 | https://www.vldb.org/pvldb/vol16/p2172-liu.pdf | https://github.com/SICS-Fundamental-Research-Center/MiniGraph | other-userspace | Out-of-core graph processing engine explicitly designed for a single machine; C++ user space, disk-resident graphs fit 257 GB |
| 31 | DILI: A Distribution-Driven Learned Index | https://doi.org/10.14778/3598581.3598593 | https://www.vldb.org/pvldb/vol16/p2212-li.pdf | https://github.com/pfl-cs/DILI | ml-for-systems | Distribution-driven learned index; C++ single node, SOSD-style datasets |
| 32 | LEON: A New Framework for ML-Aided Query Optimization | https://doi.org/10.14778/3598581.3598597 | https://www.vldb.org/pvldb/vol16/p2261-chen.pdf | https://github.com/haitianchen/LEON | ml-for-systems | ML-aided query optimization framework on PostgreSQL; single node, small models |
| 33 | SEIDEN: Revisiting Query Processing in Video Database Systems | https://doi.org/10.14778/3598581.3598599 | https://www.vldb.org/pvldb/vol16/p2289-kakkar.pdf | https://github.com/georgia-tech-db/seiden_submission | ml-systems | Video database query processing that re-plans around expensive model inference; single GPU, part of the EVA ecosystem |
| 34 | Extract-Transform-Load for Video Streams | https://doi.org/10.14778/3598581.3598600 | https://www.vldb.org/pvldb/vol16/p2302-kossmann.pdf | https://github.com/ferdiko/vetl | ml-systems | ETL pipeline for video streams that schedules model inference under resource limits; single GPU sufficient for a scaled-down stream count |
| 35 | LRU-C: Parallelizing Database I/Os for Flash SSDs | https://doi.org/10.14778/3598581.3598605 | https://www.vldb.org/pvldb/vol16/p2364-lee.pdf | https://github.com/LeeBohyun/LRU-C | caching | Buffer-pool replacement and I/O parallelisation for flash SSDs; user-space DBMS buffer manager on NVMe, no kernel changes needed |
| 36 | Scaling a Declarative Cluster Manager Architecture with Query Optimization Techniques | https://doi.org/10.14778/3603581.3603599 | https://www.vldb.org/pvldb/vol16/p2618-rong.pdf | https://github.com/vmware/declarative-cluster-management/releases/tag/vldb23 | scheduling | Declarative cluster manager (Kubernetes scheduler) reduced to constrained optimization; evaluated with trace-driven simulation and an emulated cluster. Concern: real Kubernetes needs root or containers, so only the simulated/emulated path is usable |
| 37 | REmatch: a novel regex engine for finding all matches | https://doi.org/10.14778/3611479.3611488 | https://www.vldb.org/pvldb/vol16/p2792-vrgoc.pdf | https://github.com/REmatchChile/REmatch-paper | other-userspace | User-space regular-expression engine enumerating all matches with output-linear delay; C++ library, CPU-only |
| 38 | ADOPT: Adaptively Optimizing Attribute Orders for Worst-Case Optimal Join Algorithms via Reinforcement Learning | https://doi.org/10.14778/3611479.3611489 | https://www.vldb.org/pvldb/vol16/p2805-wang.pdf | https://github.com/jxiw/ADOPT | ml-for-systems | RL-based adaptive attribute ordering for worst-case optimal joins; Java/C++ single node |
| 39 | Accelerating Aggregation Queries on Unstructured Streams of Data | https://doi.org/10.14778/3611479.3611496 | https://www.vldb.org/pvldb/vol16/p2897-russo.pdf | https://github.com/stanford-futuredata/InQuest | ml-systems | Approximate aggregation over streams processed by expensive ML models, with a sampling/scheduling policy; one GPU is enough |
| 40 | Simple Adaptive Query Processing vs. Learned Query Optimizers: Observations and Analysis | https://doi.org/10.14778/3611479.3611501 | https://www.vldb.org/pvldb/vol16/p2962-zhang.pdf | https://github.com/yunjiazhang/adaptiveness_vs_learning | ml-for-systems | Head-to-head study of adaptive query processing versus learned query optimizers; already a reproduction-style paper, easy hypothesis to extend on PostgreSQL |
| 41 | BP-tree: Overcoming the Point-Range Operation Tradeoff for In-Memory B-trees | https://doi.org/10.14778/3611479.3611502 | https://www.vldb.org/pvldb/vol16/p2976-xu.pdf | https://github.com/wheatman/concurrent-btrees | storage | Concurrent in-memory B-tree balancing point and range performance; C++ multicore, 32 threads is a fair scale-down |
| 42 | A Deep Dive into Common Open Formats for Analytical DBMSs | https://doi.org/10.14778/3611479.3611507 | https://www.vldb.org/pvldb/vol16/p3044-liu.pdf | https://github.com/Tranway1/ColumnarFormatsEval | storage | Deep evaluation of Parquet/ORC/Arrow open columnar formats; CPU and disk only, ideal reproduce-and-improve target |
| 43 | JoinBoost: Grow Trees Over Normalized Data Using Only SQL | https://doi.org/10.14778/3611479.3611509 | https://www.vldb.org/pvldb/vol16/p3071-huang.pdf | https://github.com/JoinBoost/JoinBoost | ml-systems | In-database gradient-boosted tree training expressed in SQL over normalized data; DuckDB-based, CPU-only single node |
| 44 | R^3: Record-Replay-Retroaction for Database-Backed Applications | https://doi.org/10.14778/3611479.3611510 | https://www.vldb.org/pvldb/vol16/p3085-li.pdf | https://github.com/DBOS-project/apiary/tree/r3-exp | other-userspace | Record-replay-retroaction runtime for database-backed applications; Java services plus PostgreSQL/VoltDB, all runnable in user space on one host |
| 45 | Sieve: A Learned Data-Skipping Index for Data Analytics | https://doi.org/10.14778/3611479.3611520 | https://www.vldb.org/pvldb/vol16/p3214-tong.pdf | https://github.com/UmasouTTT/Sieve | ml-for-systems | Learned data-skipping index for analytics; single-node build, compares against Cuckoo-Index style baselines |
| 46 | Out-of-Order Sliding-Window Aggregation with Efficient Bulk Evictions and Insertions | https://doi.org/10.14778/3611479.3611521 | https://www.vldb.org/pvldb/vol16/p3227-hirzel.pdf | https://github.com/IBM/sliding-window-aggregators | other-userspace | Out-of-order sliding-window aggregation data structures with bulk eviction/insertion; C++/Rust library, CPU-only microbenchmarks |
| 47 | FASTgres: Making Learned Query Optimizer Hinting Effective | https://doi.org/10.14778/3611479.3611528 | https://www.vldb.org/pvldb/vol16/p3310-habich.pdf | https://github.com/db-tu-dresden/FASTgres-PVLDBv16 | ml-for-systems | Classifier-based query hint selection for PostgreSQL; lightweight models, single node |
| 48 | Write-Aware Timestamp Tracking: Effective and Efficient Page Replacement for Modern Hardware | https://doi.org/10.14778/3611479.3611529 | https://www.vldb.org/pvldb/vol16/p3323-vohringer.pdf | https://github.com/leanstore/leanstore/tree/WATT | caching | Write-aware timestamp tracking page-replacement policy in a buffer manager; single-node NVMe, pure user-space C++ |
| 49 | Similarity search in the blink of an eye with compressed indices | https://doi.org/10.14778/3611479.3611537 | https://www.vldb.org/pvldb/vol16/p3433-aguerrebere.pdf | https://github.com/IntelLabs/ScalableVectorSearch | other-userspace | Graph vector index with compressed vectors and SIMD kernels; single node, datasets fit in 125 GiB RAM. Concern: heavily tuned for Intel AVX-512, our Zen3 has AVX2 so absolute numbers will differ |
| 50 | Declarative Sub-Operators for Universal Data Processing | https://doi.org/10.14778/3611479.3611539 | https://www.vldb.org/pvldb/vol16/p3461-jungmair.pdf | https://github.com/lingo-db/subop-vldb-2023-reproducibility | other-userspace | MLIR-based sub-operator IR and compiler in LingoDB; C++/LLVM builds in user space, CPU-only |
| 51 | Enabling Transparent Acceleration of Big Data Frameworks using Heterogeneous Hardware | https://doi.org/10.14778/3565838.3565842 | https://www.vldb.org/pvldb/vol15/p3869-xekalaki.pdf | https://github.com/mairooni/Flink-TornadoVM-Artifact | other-userspace | Transparent JIT offload of JVM big-data operators to accelerators via TornadoVM; the GPU path works on one A5000 with the NVIDIA OpenCL/PTX backend. Concern: paper also evaluates FPGA, and the Flink part must be run in local mode |
| 52 | Cost-based or Learning-based? A Hybrid Query Optimizer for Query Plan Selection | https://doi.org/10.14778/3565838.3565846 | https://www.vldb.org/pvldb/vol15/p3924-li.pdf | https://github.com/yxfish13/HyperQO | ml-for-systems | Hybrid cost-based plus learned query optimizer for plan selection on PostgreSQL; single node, small models |
| 53 | Learned Index Benefits: Machine Learning Based Index Performance Estimation | https://doi.org/10.14778/3565838.3565848 | https://www.vldb.org/pvldb/vol15/p3950-shi.pdf | https://github.com/JC-Shi/Learned-Index-Benefits | ml-for-systems | ML-based index performance/benefit estimation for index tuning; PostgreSQL plus lightweight models, CPU-only |

## All papers
| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | C5: Cloned Concurrency Control That Always Keeps Up | out-topic | replicated DBMS concurrency-control protocol |
| 2 | The Case for Distributed Shared-Memory Databases with RDMA-Enabled Memory Disaggregation | out-machine | vision paper whose premise is RDMA-enabled memory disaggregation hardware |
| 3 | FlexChain: An Elastic Disaggregated Blockchain | out-topic | blockchain system |
| 4 | MiCS: Near-linear Scaling for Training Gigantic Model on Public Cloud | out-machine | gigantic-model training needs multi-node multi-GPU cloud clusters |
| 5 | Privacy-preserving Cooperative Online Matching over Spatial Crowdsourcing Platforms | out-topic | privacy-preserving spatial crowdsourcing |
| 6 | Coresets over Multiple Tables for Feature-rich and Data-efficient Machine Learning | out-topic | coreset theory for ML over tables |
| 7 | STARRY: Multi-master Transaction Processing on Semi-leader Architecture | out-topic | multi-master transaction protocol |
| 8 | SIFTER: Space-Efficient Value Iteration for Finite-Horizon MDPs | out-topic | MDP value-iteration algorithm |
| 9 | TreeLine: An Update-In-Place Key-Value Store for Modern Storage | included | storage - Single-node update-in-place KV store on NVMe as a RocksDB alternative; C++ user-space build, io_uring/O_DIRECT only, dataset fits the 257 GB free space |
| 10 | DPXPlain: Privately Explaining Aggregate Query Answers | out-topic | differentially private query explanation |
| 11 | Efficient Maximum k-Plex Computation over Large Sparse Graphs | out-topic | graph mining algorithm |
| 12 | Online Schema Evolution is (almost) Free for Snapshot Databases | out-topic | DBMS schema evolution |
| 13 | LIDER: An Efficient High-dimensional Learned Index for Large-scale Dense Passage Retrieval | out-no-code | checked the PVLDB PDF, the arXiv version and GitHub/web search - no official implementation released |
| 14 | Models and Mechanisms for Spatial Data Fairness | out-topic | spatial data fairness |
| 15 | Influence Maximization in Real-World Closed Social Networks | out-topic | influence maximization in graphs |
| 16 | Time2Feat: Learning Interpretable Representations for Multivariate Time Series Clustering | out-topic | interpretable time-series clustering |
| 17 | OpBoost: A Vertical Federated Tree Boosting Framework Based on Order-Preserving Desensitization | out-topic | privacy-preserving federated boosting |
| 18 | HMAB: Self-Driving Hierarchy of Bandits for Integrated Physical Database Design Tuning | out-machine | the tuner drives Microsoft SQL Server which cannot be installed without root or Docker on this host |
| 19 | Erebus: Explaining the Outputs of Data Streaming Queries | out-topic | explaining streaming query outputs |
| 20 | PLIN: A Persistent Learned Index for Non-Volatile Memory with High Performance and Instant Recovery | out-machine | learned index for non-volatile memory (Optane) hardware |
| 21 | Fries: Fast and Consistent Runtime Reconfiguration in Dataflow Systems with Transactional Guarantees | out-topic | dataflow reconfiguration semantics for a distributed engine |
| 22 | Fast Approximate Denial Constraint Discovery | out-topic | denial-constraint discovery |
| 23 | Frequency Domain Data Encoding in Apache IoTDB | included | storage - Frequency-domain lossy encoding for time-series storage; pure Java single node |
| 24 | Happiness Maximizing Sets under Group Fairness Constraints | out-topic | fairness-constrained set selection |
| 25 | SHiFT: An Efficient, Flexible Search Engine for Transfer Learning | included | ml-systems - Search engine over a pretrained-model zoo with cost models and caching; one A5000 suffices for the small models |
| 26 | Satisfying Complex Top-k Fairness Constraints by Preference Substitutions | out-topic | top-k fairness constraints |
| 27 | SyncSignature: A Simple, Efficient, Parallelizable Framework for Tree Similarity Joins | out-topic | tree similarity join algorithm |
| 28 | Approximating Probabilistic Group Steiner Trees in Graphs | out-topic | probabilistic Steiner tree approximation |
| 29 | Space-Efficient Random Walks on Streaming Graphs | out-topic | streaming graph random-walk algorithm |
| 30 | PromptEM: Prompt-tuning for Low-resource Generalized Entity Matching | out-topic | entity matching via prompt tuning |
| 31 | Cornus: Atomic Commit for a Cloud DBMS with Storage Disaggregation | out-machine | atomic commit for a multi-node cloud DBMS with storage disaggregation |
| 32 | Route Travel Time Estimation on A Road Network Revisited: Heterogeneity, Proximity, Periodicity and Dynamicity | out-topic | travel-time estimation model |
| 33 | Serving and Optimizing Machine Learning Workflows on Heterogeneous Infrastructures | included | ml-systems - ML-workflow serving and placement optimizer |
| 34 | Computing Rule-Based Explanations by Leveraging Counterfactuals | out-topic | counterfactual explanation computation |
| 35 | Self-supervised and Interpretable Data Cleaning with Sequence Generative Adversarial Networks | out-topic | data cleaning with GANs |
| 36 | Optimizing Video Analytics with Declarative Model Relationships | included | ml-systems - Declarative video analytics that exploits model-relationship hints to trade accuracy for speed; single-GPU inference, AE-reviewed artifact repo |
| 37 | Spade: A Real-Time Fraud Detection Framework on Evolving Graphs | out-topic | fraud detection on evolving graphs |
| 38 | Galvatron: Efficient Transformer Training over Multiple GPUs Using Automatic Parallelism | out-machine | automatic parallelism search is meaningless with a single GPU |
| 39 | iEDeaL: A Deep Learning Framework for Detecting Highly Imbalanced Interictal Epileptiform Discharges | out-topic | deep learning for EEG signal detection |
| 40 | Dalton: Learned Partitioning for Distributed Data Streams | included | ml-for-systems - RL-learned partitioning for stream operators |
| 41 | FirmTruss Community Search in Multilayer Networks | out-topic | community search in multilayer graphs |
| 42 | Efficient Triangle-Connected Truss Community Search In Dynamic Graphs | out-topic | truss community search |
| 43 | Can Learned Models Replace Hash Functions? | included | ml-for-systems - CPU-only study of learned models as hash functions in hash tables and joins; strong reproduce-then-improve target, no GPU or special hardware |
| 44 | TOD: GPU-accelerated Outlier Detection via Tensor Operations | included | ml-systems - GPU outlier detection with provable memory-aware batching; explicitly designed for one GPU, PyTorch, fits 24 GB |
| 45 | FILM: a Fully Learned Index for Larger-than-Memory Databases | included | ml-for-systems - Learned index for larger-than-memory data; single node, only RAM plus local disk needed |
| 46 | Cache Me If You Can: Accuracy-Aware Inference Engine for Differentially Private Data Exploration | out-topic | differentially private data exploration semantics |
| 47 | Range Search over Encrypted Multi-Attribute Data | out-topic | searchable encryption |
| 48 | HEDA: Multi-Attribute Unbounded Aggregation over Homomorphically Encrypted Database | out-topic | homomorphic encryption aggregation |
| 49 | Density Personalized Group Query | out-topic | group query over graphs |
| 50 | Nezha: Deployable and High-Performance Consensus Using Synchronized Clocks | out-machine | consensus protocol needing multiple nodes and synchronized clocks |
| 51 | Pantheon: Private Retrieval from Public Key-Value Store | out-topic | private information retrieval |
| 52 | Bayesian Sketches for Volume Estimation in Data Streams | out-topic | streaming sketch algorithm |
| 53 | Waffle: A Workload-Aware and Query-Sensitive Framework for Disk-Based Spatial Indexing | out-topic | disk-based spatial index |
| 54 | Fast Algorithms for Denial Constraint Discovery | out-topic | denial-constraint discovery algorithms |
| 55 | Toward Quantity-of-Interest Preserving Lossy Compression for Scientific Data | included | storage - Quantity-of-interest preserving error-bounded lossy compression on top of SZ3; CPU-only C++ |
| 56 | Scalable Graph Convolutional Network Training on Distributed-Memory Systems | out-machine | GCN training on distributed-memory MPI clusters |
| 57 | Motiflets - Simple and Accurate Detection of Motifs in Time Series | out-topic | time-series motif discovery algorithm |
| 58 | Can Foundation Models Wrangle Your Data? | out-topic | vision paper on foundation models for data wrangling |
| 59 | M2Bench: A Database Benchmark for Multi-Model Analytic Workloads | out-topic | multi-model database benchmark |
| 60 | Parallelism-Optimizing Data Placement for Faster Data-Parallel Computations | out-machine | data placement for distributed data-parallel jobs on a cluster |
| 61 | SubStrat: A Subset-Based Optimization Strategy for Faster AutoML | included | ml-systems - Data-subset strategy that accelerates AutoML search; pure Python CPU workload, small footprint |
| 62 | MultiBiSage: A Web-Scale Recommendation System Using Multiple Bipartite Graphs at Pinterest | out-topic | web-scale recommender embedding system |
| 63 | TokenJoin: Efficient Filtering for Set Similarity Join with Maximum Weighted Bipartite Matching | out-topic | set similarity join filtering |
| 64 | Quasi-stable Coloring for Graph Compression: Approximating Max-Flow, Linear Programs, and Centrality | out-topic | graph coloring and compression theory |
| 65 | Multi-Analyst Differential Privacy for Online Query Answering | out-topic | differential privacy for multi-analyst query answering |
| 66 | Excalibur: A Virtual Machine for Adaptive Fine-grained JIT-Compiled Query Execution based on VOILA | included | other-userspace - Adaptive fine-grained JIT-compiled query execution VM; C++ single node, LLVM is conda-installable |
| 67 | Differentially Oblivious Relational Database Operators | out-topic | oblivious relational operators |
| 68 | Keep CALM and CRDT On | out-topic | vision paper on CRDTs with no artifact |
| 69 | MQH: Locality Sensitive Hashing on Multi-level Quantization Errors for Point-to-Hyperplane Distances | out-topic | locality-sensitive hashing algorithm |
| 70 | The LDBC Social Network Benchmark: Business Intelligence Workload | out-topic | graph benchmark specification |
| 71 | Making Cache Monotonic and Consistent | included | caching - Cache admission and eviction policy that keeps cached query results monotonic and consistent; trace-driven single-node evaluation |
| 72 | SkinnerMT: Parallelizing for Efficiency and Robustness in Adaptive Query Processing on Multicore Platforms | included | ml-for-systems - Parallel RL-based adaptive query processing on multicore; Java, 16 cores/32 threads is a sensible scale-down of the paper's machine |
| 73 | On Efficient Approximate Queries over Machine Learning Models | included | ml-systems - Approximate query processing that minimises expensive ML model invocations using cheap proxy models; one GPU is enough |
| 74 | Integrating Data Lake Tables | out-topic | data lake table integration |
| 75 | PIM-tree: A Skew-resistant Index for Processing-in-Memory | out-machine | index designed for UPMEM processing-in-memory hardware |
| 76 | Web Record Extraction with Invariants | out-topic | web record extraction |
| 77 | A Deep Generative Model for Trajectory Modeling and Utilization | out-topic | trajectory generative model |
| 78 | L2chain: Towards High-performance, Confidential and Secure Layer-2 Blockchain Solution for Decentralized Applications | out-topic | layer-2 blockchain |
| 79 | Auto-Tuning with Reinforcement Learning for Permissioned Blockchain Systems | out-topic | permissioned blockchain tuning |
| 80 | PetPS: Supporting Huge Embedding Models with Persistent Memory | out-machine | parameter server built on persistent memory (Optane) hardware |
| 81 | Extraction of Validating Shapes from very large Knowledge Graphs | out-topic | knowledge graph shape extraction |
| 82 | Async-fork: Mitigating Query Latency Spikes Incurred by the Fork-based Snapshot Mechanism from the OS Level | out-machine | the contribution is a Linux kernel modification to the fork snapshot path - needs kernel build and root |
| 83 | Change Propagation Without Joins | out-topic | incremental view maintenance theory |
| 84 | FederatedScope: A Flexible Federated Learning Platform for Heterogeneity | included | ml-systems - Event-driven federated learning framework; the standard mode simulates many clients as processes on one node with one GPU |
| 85 | ACTA: Autonomy and Coordination Task Assignment in Spatial Crowdsourcing Platforms | out-topic | spatial crowdsourcing task assignment |
| 86 | FastFlow: Accelerating Deep Learning Model Training with Smart Offloading of Input Data Pipeline | out-no-code | paper points to github.com/SamsungLabs/FastFlow which now returns HTTP 404; no mirror or artifact found elsewhere |
| 87 | FARGO: Fast Maximum Inner Product Search via Global Multi-Probing | out-topic | maximum inner product search algorithm |
| 88 | Optimistic Data Parallelism for FPGA-Accelerated Sketching | out-machine | FPGA-accelerated sketching |
| 89 | On the Risks of Collecting Multidimensional Data Under Local Differential Privacy | out-topic | local differential privacy analysis |
| 90 | Odyssey: A Journey in the Land of Distributed Data Series Similarity Search | out-machine | distributed data-series similarity search on a cluster |
| 91 | Anonymous Edge Representation for Inductive Anomaly Detection in Dynamic Bipartite Graphs | out-topic | anomaly detection in dynamic graphs |
| 92 | Scalable Time-Range k-Core Query on Temporal Graphs | out-topic | temporal graph k-core query |
| 93 | High-Performance Row Pattern Recognition Using Joins | out-topic | row pattern recognition query processing |
| 94 | A Hierarchical Grouping Algorithm for the Multi-Vehicle Dial-a-Ride Problem | out-topic | vehicle routing optimization |
| 95 | Leveraging Application Data Constraints to Optimize Database-Backed Web Applications | out-topic | program analysis for database-backed web apps |
| 96 | Bringing Compiling Databases to RISC Architectures | out-machine | the contribution is code generation for ARM and RISC-V hardware we do not have |
| 97 | Blink-hash: An Adaptive Hybrid Index for In-Memory Time-Series Databases | included | storage - In-memory hybrid hash/tree index for time-series ingestion on multicore; C++ DRAM-only |
| 98 | A Design Space Exploration and Evaluation for Main-Memory Hash Joins in Storage Class Memory | out-machine | hash joins on storage class memory (Optane DIMMs) |
| 99 | Efficient Black-box Checking of Snapshot Isolation in Databases | out-topic | black-box isolation-level checking |
| 100 | Differentially Private Vertical Federated Clustering | out-topic | private federated clustering |
| 101 | Panakos: Chasing the Tails for Multidimensional Data Streams | out-topic | multidimensional stream sketch |
| 102 | VersaMatch: Ontology Matching with Weak Supervision | out-topic | ontology matching |
| 103 | RECA: Related Tables Enhanced Column Semantic Type Annotation Framework | out-topic | column semantic type annotation |
| 104 | Zebra: When Temporal Graph Neural Networks Meet Temporal Personalized PageRank | out-topic | temporal GNN algorithm |
| 105 | Efficient Approximation of Certain and Possible Answers for Ranking and Window Queries over Uncertain Data | out-topic | uncertain data query semantics |
| 106 | GlassDB: An Efficient Verifiable Ledger Database System Through Transparency | out-topic | verifiable ledger database |
| 107 | Efficient Distributed Transaction Processing in Heterogeneous Networks | out-machine | distributed transactions over RDMA and heterogeneous networks |
| 108 | Auxo: A Scalable and Efficient Graph Stream Summarization Structure | out-topic | graph stream summarization sketch |
| 109 | OneShotSTL: One-Shot Seasonal-Trend Decomposition For Online Time Series Anomaly Detection And Forecasting | out-topic | time-series decomposition algorithm |
| 110 | Cloud Analytics Benchmark | out-topic | cloud analytics benchmark specification |
| 111 | Scalable and Robust Snapshot Isolation for High-Performance Storage Engines | included | storage - MVCC/snapshot-isolation redesign inside the LeanStore storage engine; single-node NVMe C++, benchmarks via BenchBase |
| 112 | FLARE: A Fast, Secure, and Memory-Efficient Distributed Analytics Framework (Flavor: Systems) | out-machine | secure distributed analytics across multiple parties and machines |
| 113 | NV-SQL: Boosting OLTP Performance with Non-Volatile DIMMs | out-machine | OLTP engine built for NVDIMM hardware |
| 114 | Lero: A Learning-to-Rank Query Optimizer | included | ml-for-systems - Learning-to-rank query optimizer for PostgreSQL; PostgreSQL builds from source into $HOME, model training is small enough for one GPU or CPU |
| 115 | Deploying Computational Storage for HTAP DBMSs Takes More Than Just Computation Offloading | out-machine | requires computational storage devices |
| 116 | Transactional Panorama: A Conceptual Framework for User Perception in Analytical Visual Interfaces | out-topic | user-perception framework for visual interfaces |
| 117 | Sparkly: A Simple yet Surprisingly Strong TF/IDF Blocker for Entity Matching | out-topic | entity matching blocker |
| 118 | Robust Query Driven Cardinality Estimation under Changing Workloads | included | ml-for-systems - Robust learned cardinality estimation evaluated on the CEB benchmark; PostgreSQL user-space build plus PyTorch on one GPU |
| 119 | CatSQL: Towards Real World Natural Language to SQL Applications | out-topic | natural language to SQL |
| 120 | Elpis: Graph-Based Similarity Search for Scalable Data Science | out-topic | graph-based similarity search algorithm |
| 121 | Dotori: A Key-Value SSD Based KV Store | out-machine | built on Key-Value SSD (Samsung KV-SSD) hardware |
| 122 | PreFair: Privately Generating Justifiably Fair Synthetic Data | out-topic | private fair synthetic data generation |
| 123 | Explaining Dataset Changes for Semantic Data Versioning with Explain-Da-V | out-topic | dataset change explanation |
| 124 | DBSP: Automatic Incremental View Maintenance for Rich Query Languages | out-topic | incremental view maintenance theory |
| 125 | SPG: Structure-Private Graph Database via SqueezePIR | out-topic | private graph database via PIR |
| 126 | InfiniStore: Elastic Serverless Cloud Storage | out-machine | elastic serverless storage needs a cloud FaaS platform |
| 127 | Distributed Graph Embedding with Information-Oriented Random Walks | out-machine | distributed graph embedding on a cluster |
| 128 | Secure Shapley Value for Cross-Silo Federated Learning | out-topic | secure federated Shapley value computation |
| 129 | SODA: A Set of Fast Oblivious Algorithms in Distributed Secure Data Analytics | out-topic | oblivious distributed analytics algorithms |
| 130 | GriDB: Scaling Blockchain Database via Sharding and Off-Chain Cross-Shard Mechanism | out-topic | blockchain sharding |
| 131 | SUFF: Accelerating Subgraph Matching with Historical Data | out-topic | subgraph matching acceleration |
| 132 | When Database Meets New Storage Devices: Understanding and Exposing Performance Mismatches via Configurations | out-machine | study requires a fleet of new storage devices (ZNS, Optane, KV-SSD) |
| 133 | Semantics-aware Dataset Discovery from Data Lakes with Contextualized Column-based Representation Learning | out-topic | dataset discovery from data lakes |
| 134 | Marigold: Efficient k-means Clustering in High Dimensions | out-topic | k-means clustering algorithm |
| 135 | The Case for Learned In-Memory Joins | included | ml-for-systems - Learned in-memory sort/hash joins; CPU-only C++ with SOSD-style datasets |
| 136 | Elf: Erasing-based Lossless Floating-Point Compression | included | storage - Erasing-based lossless floating-point compression for time-series storage; Java, single node, modest datasets |
| 137 | LOGER: A Learned Optimizer towards Generating Efficient and Robust Query Execution Plans | included | ml-for-systems - Learned query optimizer generating robust plans on PostgreSQL; GPU-optional training, single node |
| 138 | Representing Paths in Graph Database Pattern Matching | out-topic | graph query language path semantics |
| 139 | ZKSQL: Verifiable and Efficient Query Evaluation with Zero-Knowledge Proofs | out-topic | zero-knowledge proof query evaluation |
| 140 | Computing Graph Edit Distance via Neural Graph Matching | out-topic | neural graph edit distance |
| 141 | Benchmarking the Utility of 𝑤-event Differential Privacy Mechanisms - When Baselines Become Mighty Competitors | out-topic | differential privacy benchmarking |
| 142 | Collective Grounding: Applying Database Techniques to Grounding Templated Models | out-topic | grounding for templated statistical models |
| 143 | An Experimental Evaluation of Process Concept Drift Detection | out-topic | process concept drift detection |
| 144 | Pollock: A Data Loading Benchmark | out-topic | CSV data loading robustness benchmark |
| 145 | Answering Private Linear Queries Adaptively using the Common Mechanism | out-topic | private linear query answering |
| 146 | LDPTrace: Locally Differentially Private Trajectory Synthesis | out-topic | locally private trajectory synthesis |
| 147 | Sim-Piece: Highly Accurate Piecewise Linear Approximation through Similar Segment Merging | included | storage - Piecewise-linear lossy compression for time series; Java, CPU-only, small datasets - easy to reproduce and extend |
| 148 | Towards Migration-Free Just-In-Case Data Archival for Future Cloud Data Lakes | out-machine | vision paper about DNA-storage archival, no runnable artifact |
| 149 | Fine-Grained Re-Execution for Efficient Batched Commit of Distributed Transactions | out-machine | batched commit for distributed transactions across nodes |
| 150 | Learning and Deducing Temporal Orders | out-topic | temporal order deduction |
| 151 | BASE: Bridging the Gap between Cost and Latency for Query Optimization | included | ml-for-systems - RL query optimizer bridging cost and latency on PostgreSQL; same footprint as Bao/Lero, single node |
| 152 | Efficient framework for operating on data sketches | out-topic | sketch framework theory |
| 153 | Towards Efficient Index Construction and Approximate Nearest Neighbor Search in High-Dimensional Spaces | out-topic | approximate nearest neighbour index algorithm |
| 154 | Learned Index: A Comprehensive Experimental Evaluation | included | ml-for-systems - Comprehensive experimental evaluation of learned indexes; CPU-only benchmark harness, a natural reproduction or extension target |
| 155 | Longshot: Indexing Growing Databases using MPC and Differential Privacy | out-topic | secure multi-party computation index |
| 156 | Accelerating Similarity Search for Elastic Measures: A Study and New Generalization of Lower Bounding Distances | out-topic | lower bounds for elastic similarity measures |
| 157 | AdaChain: A Learned Adaptive Blockchain | out-topic | learned blockchain |
| 158 | Influential Community Search over Large Heterogeneous Information Networks | out-topic | community search over heterogeneous networks |
| 159 | Neighborhood-based Hypergraph Core Decomposition | out-topic | hypergraph core decomposition |
| 160 | Temporal SIR-GN: Efficient and Effective Structural Representation Learning for Temporal Graphs | out-topic | temporal graph representation learning |
| 161 | What Modern NVMe Storage Can Do, And How To Exploit It: High-Performance I/O for High-Performance Storage Engines | included | storage - User-space high-IOPS NVMe I/O engine (io_uring, many threads) for storage engines; no root needed |
| 162 | WiscSort: External Sorting For Byte-Addressable Storage | out-machine | external sort designed for byte-addressable persistent memory (Optane) |
| 163 | Text Indexing for Long Patterns: Anchors are All you Need | out-topic | text indexing theory |
| 164 | The FastLanes Compression Layout: Decoding >100 Billion Integers per Second with Scalar Code | included | storage - Bit-packing/compression layout decoded with auto-vectorizable scalar code; CPU-only C++ |
| 165 | VeriBench: Analyzing the Performance of Database Systems with Verifiability | out-topic | benchmark for verifiable databases |
| 166 | Towards Designing and Learning Piecewise Space-Filling Curves | included | ml-for-systems - Learned piecewise space-filling curve for multidimensional indexing; Python plus C++, single node |
| 167 | MiniGraph: Querying Big Graphs with a Single Machine | included | other-userspace - Out-of-core graph processing engine explicitly designed for a single machine; C++ user space, disk-resident graphs fit 257 GB |
| 168 | BICE: Exploring Compact Search Space by Using Bipartite Matching and Cell-Wide Verification | out-topic | subgraph matching search space |
| 169 | Maximal D-truss Search in Dynamic Directed Graphs | out-topic | directed truss search |
| 170 | DILI: A Distribution-Driven Learned Index | included | ml-for-systems - Distribution-driven learned index; C++ single node, SOSD-style datasets |
| 171 | Pre-trained Embeddings for Entity Resolution: An Experimental Analysis | out-topic | entity resolution embedding study |
| 172 | Decoupled Graph Neural Networks for Large Dynamic Graphs | out-topic | GNN algorithm for dynamic graphs |
| 173 | Adaptive Indexing of Objects with Spatial Extent | out-topic | spatial adaptive indexing |
| 174 | LEON: A New Framework for ML-Aided Query Optimization | included | ml-for-systems - ML-aided query optimization framework on PostgreSQL; single node, small models |
| 175 | TiQuE: Improving the Transactional Performance of Analytical Systems for True Hybrid Workloads | out-topic | HTAP transactional performance |
| 176 | SEIDEN: Revisiting Query Processing in Video Database Systems | included | ml-systems - Video database query processing that re-plans around expensive model inference; single GPU, part of the EVA ecosystem |
| 177 | Extract-Transform-Load for Video Streams | included | ml-systems - ETL pipeline for video streams that schedules model inference under resource limits; single GPU sufficient for a scaled-down stream count |
| 178 | Pando: Enhanced Data Skipping with Logical Data Partitioning | out-no-code | no code URL in the paper and no repository found via GitHub/web search for the Pando artifact |
| 179 | Cracking-Like Join for Trusted Execution Environments | out-machine | joins inside Intel SGX trusted execution environments |
| 180 | Opportunities for Quantum Acceleration of Databases: Optimization of Queries and Transaction Schedules | out-machine | vision paper requiring quantum hardware |
| 181 | SDPipe: A Semi-Decentralized Framework for Heterogeneity-aware Pipeline-parallel Training | out-machine | pipeline-parallel training across many GPUs and nodes |
| 182 | LRU-C: Parallelizing Database I/Os for Flash SSDs | included | caching - Buffer-pool replacement and I/O parallelisation for flash SSDs; user-space DBMS buffer manager on NVMe, no kernel changes needed |
| 183 | Why Not Yet: Fixing a Top-k Ranking that Is Not Fair to Individuals | out-topic | fair ranking repair |
| 184 | Information-Theoretically Secure and Highly Efficient Search and Row Retrieval | out-topic | information-theoretically secure search |
| 185 | Olive: Oblivious Federated Learning on Trusted Execution Environment Against the Risk of Sparsification | out-machine | federated learning inside SGX enclaves |
| 186 | TASK: An Efficient Framework for Instant Error-tolerant Spatial Keyword Queries on Road Networks | out-topic | spatial keyword query on road networks |
| 187 | Autonomously Computable Information Extraction | out-topic | information extraction |
| 188 | NVM: Is it Not Very Meaningful for Databases? | out-machine | evaluation study of Optane NVM hardware for databases |
| 189 | DeepJoin: Joinable Table Discovery with Pre-trained Language Models | out-topic | joinable table discovery with language models |
| 190 | Falcon: A Privacy-Preserving and Interpretable Vertical Federated Learning System | out-topic | vertical federated learning privacy |
| 191 | Enabling Secure and Efficient Data Analytics Pipeline Evolution with Trusted Execution Environment | out-machine | analytics pipeline evolution inside SGX enclaves |
| 192 | A Case for Graphics-driven Query Processing | out-no-code | Microsoft Research Garuda prototype; the paper gives no repository and GitHub/web search found no public release |
| 193 | Effective and Efficient Route Planning Using Historical Trajectories on Road Networks | out-topic | route planning over trajectories |
| 194 | Adaptive Indexing in High-Dimensional Metric Spaces | out-topic | metric space adaptive indexing |
| 195 | Parallel Colorful h-star Core Maintenance in Dynamic Graphs | out-topic | graph core maintenance |
| 196 | MITra: A Framework for Multi-Instance Graph Traversal | out-topic | multi-instance graph traversal |
| 197 | CommunityAF: An Example-based Community Search Method via  Autoregressive Flow | out-topic | community search via autoregressive flow |
| 198 | Auto-BI: Automatically Build BI-Models Leveraging Local Join Prediction and Global Schema Graph | out-topic | BI model construction from schemas |
| 199 | Trajectory Data Collection with Local Differential Privacy | out-topic | locally private trajectory collection |
| 200 | LMSFC: A Novel Multidimensional Index based on Learned Monotonic Space Filling Curves | out-no-code | no repository in the paper, the arXiv version or GitHub/web search |
| 201 | Scaling a Declarative Cluster Manager Architecture with Query Optimization Techniques | included | scheduling - Declarative cluster manager (Kubernetes scheduler) reduced to constrained optimization; evaluated with trace-driven simulation and an emulated cluster |
| 202 | CORNET: Learning Table Formatting Rules By Example | out-topic | learning spreadsheet formatting rules |
| 203 | ARKGraph: All-Range Approximate K-Nearest-Neighbor Graph | out-topic | approximate k-NN graph construction algorithm |
| 204 | Causal Data Integration | out-topic | vision paper on causal data integration |
| 205 | Mining Frequent Infix Patterns from Concurrency-Aware Process Execution Variants | out-topic | process mining pattern discovery |
| 206 | The Composable Data Management System Manifesto | out-topic | manifesto/vision paper with no artifact |
| 207 | A Two-Level Signature Scheme for Stable Set Similarity Joins | out-topic | set similarity join signatures |
| 208 | Scalable Reasoning on Document Stores via Instance-Aware Query Rewriting | out-topic | ontology-mediated query rewriting |
| 209 | EQUI-VOCAL: Synthesizing Queries for Compositional Video Events from Limited User Interactions | out-topic | video event query synthesis from user interaction |
| 210 | Lotan: Bridging the Gap between GNNs and Scalable Graph Analytics Engines | out-machine | GNN training driven by a Spark cluster plus multiple GPUs |
| 211 | Epoxy: ACID Transactions Across Diverse Data Stores | out-topic | cross-datastore transaction protocol |
| 212 | Analyzing Vectorized Hash Tables Across CPU Architectures | out-machine | the contribution is a comparison across x86, ARM Graviton and Apple M1 including AVX-512 paths |
| 213 | Exploiting Cloud Object Storage for High-Performance Analytics | out-machine | needs cloud object storage and cloud VM network bandwidth |
| 214 | A Randomized Blocking Structure for Streaming Record Linkage | out-topic | streaming record linkage blocking |
| 215 | REmatch: a novel regex engine for finding all matches | included | other-userspace - User-space regular-expression engine enumerating all matches with output-linear delay; C++ library, CPU-only |
| 216 | ADOPT: Adaptively Optimizing Attribute Orders for Worst-Case Optimal Join Algorithms via Reinforcement Learning | included | ml-for-systems - RL-based adaptive attribute ordering for worst-case optimal joins; Java/C++ single node |
| 217 | Triangular Stability Maximization by Influence Spread over Social Networks | out-topic | social network influence maximization |
| 218 | CORE-Sketch: On Exact Computation of Median Absolute Deviation with Limited Space | out-topic | streaming sketch for median absolute deviation |
| 219 | Fast Search-By-Classification for Large-Scale Databases Using Index-Aware Decision Trees and Random Forests | out-topic | classifier-driven database search algorithm |
| 220 | Semi-Oblivious Chase Termination for Linear Existential Rules: An Experimental Study | out-topic | chase termination experimental study |
| 221 | Analyzing the Impact of Cardinality Estimation on Execution Plans in Microsoft SQL Server | out-machine | study of the closed-source Microsoft SQL Server optimizer, not installable or instrumentable here |
| 222 | WALTZ: Leveraging Zone Append to Tighten the Tail Latency of LSM Tree on ZNS SSD | out-machine | LSM design that depends on ZNS SSD zone-append hardware |
| 223 | Accelerating Aggregation Queries on Unstructured Streams of Data | included | ml-systems - Approximate aggregation over streams processed by expensive ML models, with a sampling/scheduling policy; one GPU is enough |
| 224 | QueryBooster: Improving SQL Performance Using Middleware Services for Human-Centered Query Rewriting | out-topic | SQL query rewriting middleware |
| 225 | Consistent Range Approximation for Fair Predictive Modeling | out-topic | fairness in predictive modeling |
| 226 | SUREL+: Moving from Walks to Sets for Scalable Subgraph-based Graph Representation Learning | out-topic | subgraph representation learning |
| 227 | Estimating Single-Node PageRank in O(min{d_t, sqrt(m)}) Time | out-topic | PageRank estimation algorithm |
| 228 | Simple Adaptive Query Processing vs. Learned Query Optimizers: Observations and Analysis | included | ml-for-systems - Head-to-head study of adaptive query processing versus learned query optimizers; already a reproduction-style paper, easy hypothesis to extend on PostgreSQL |
| 229 | BP-tree: Overcoming the Point-Range Operation Tradeoff for In-Memory B-trees | included | storage - Concurrent in-memory B-tree balancing point and range performance; C++ multicore, 32 threads is a fair scale-down |
| 230 | HENCE-X: Toward Heterogeneity-agnostic Multi-level Explainability for Deep Graph Networks | out-topic | GNN explainability |
| 231 | Automatic Road Extraction with Multi-Source Data Revisited: Completeness, Smoothness and Discrimination | out-topic | road extraction from multi-source data |
| 232 | Asymptotically Better Query Optimization Using Indexed Algebra | out-topic | query optimizer algebra and complexity |
| 233 | Normalizing Property Graphs | out-topic | property graph normalization theory |
| 234 | A Deep Dive into Common Open Formats for Analytical DBMSs | included | storage - Deep evaluation of Parquet/ORC/Arrow open columnar formats; CPU and disk only, ideal reproduce-and-improve target |
| 235 | Saibot: A Differentially Private Data Search Platform | out-topic | differentially private data search platform |
| 236 | JoinBoost: Grow Trees Over Normalized Data Using Only SQL | included | ml-systems - In-database gradient-boosted tree training expressed in SQL over normalized data; DuckDB-based, CPU-only single node |
| 237 | R^3: Record-Replay-Retroaction for Database-Backed Applications | included | other-userspace - Record-replay-retroaction runtime for database-backed applications; Java services plus PostgreSQL/VoltDB, all runnable in user space on one host |
| 238 | Self-Training for Label-Efficient Information Extraction from Semi-Structured Web-Pages | out-topic | self-training for web information extraction |
| 239 | Efficient Non-Learning Similar Subtrajectory Search | out-topic | subtrajectory similarity search |
| 240 | Frequency-revealing attacks against Frequency-hiding Order-preserving Encryption | out-topic | attacks on order-preserving encryption |
| 241 | Efficient Fault Tolerance for Recommendation Model Training via Erasure Coding | out-machine | erasure-coded fault tolerance for distributed parameter-server training clusters |
| 242 | SlabCity: Whole-Query Optimization using Program Synthesis | out-topic | SQL query optimization via program synthesis |
| 243 | Scaling Up Structural Clustering to Large Probabilistic Graphs Using Lyapunov Central Limit Theorem | out-topic | probabilistic graph clustering |
| 244 | Epistemic Parity: Reproducibility as an Evaluation Metric for Differential Privacy | out-topic | differential privacy reproducibility study |
| 245 | POEM: Pattern-Oriented Explanations of Convolutional Neural Networks | out-topic | CNN explanation method |
| 246 | gCore: Exploring Cross-layer Cohesiveness in Multi-layer Graphs | out-topic | multi-layer graph cohesive subgraph search |
| 247 | Sieve: A Learned Data-Skipping Index for Data Analytics | included | ml-for-systems - Learned data-skipping index for analytics; single-node build, compares against Cuckoo-Index style baselines |
| 248 | Out-of-Order Sliding-Window Aggregation with Efficient Bulk Evictions and Insertions | included | other-userspace - Out-of-order sliding-window aggregation data structures with bulk eviction/insertion; C++/Rust library, CPU-only microbenchmarks |
| 249 | k-Best Egalitarian Stable Marriages for Task Assignment | out-topic | stable marriage task assignment |
| 250 | Federated Calibration and Evaluation of Binary Classifiers | out-topic | federated classifier calibration |
| 251 | FlashAlloc: Dedicating Flash Blocks By Objects | out-machine | requires SSD firmware support for dedicating flash blocks (multi-stream/open-channel) |
| 252 | Through the Fairness Lens: Experimental Analysis and Evaluation of Entity Matching | out-topic | fairness study of entity matching |
| 253 | Check Out the Big Brain on BRAD: Simplifying Cloud Data Processing with Learned Automated Data Meshes | out-topic | vision paper with no released artifact |
| 254 | How Large Language Models Will Disrupt Data Management | out-topic | vision paper with no released artifact |
| 255 | FASTgres: Making Learned Query Optimizer Hinting Effective | included | ml-for-systems - Classifier-based query hint selection for PostgreSQL; lightweight models, single node |
| 256 | Write-Aware Timestamp Tracking: Effective and Efficient Page Replacement for Modern Hardware | included | caching - Write-aware timestamp tracking page-replacement policy in a buffer manager; single-node NVMe, pure user-space C++ |
| 257 | Tigger: A Database Proxy That Bounces With User-Bypass | out-machine | the user-bypass mechanism is eBPF, which is disabled for unprivileged users here |
| 258 | Equitable Data Valuation Meets the Right to Be Forgotten in Model Markets | out-topic | data valuation and machine unlearning markets |
| 259 | TSM-Bench: Benchmarking Time Series Database Systems for Monitoring Applications | out-topic | time-series DBMS benchmark requiring several server systems deployed via containers |
| 260 | Cross Modal Data Discovery over Structured and Unstructured Data Lakes | out-topic | cross-modal data discovery |
| 261 | Auto-Tables: Synthesizing Multi-Step Transformations to Relationalize Tables without Using Examples | out-topic | table transformation synthesis |
| 262 | Effective Entity Augmentation By Querying External Data Sources | out-topic | entity augmentation from external sources |
| 263 | Choose Wisely: An Extensive Evaluation of Model Selection for Anomaly Detection in Time Series | out-topic | model selection for time-series anomaly detection |
| 264 | Similarity search in the blink of an eye with compressed indices | included | other-userspace - Graph vector index with compressed vectors and SIMD kernels; single node, datasets fit in 125 GiB RAM |
| 265 | On Data-Aware Global Explainability of Graph Neural Networks | out-topic | global explainability of GNNs |
| 266 | Declarative Sub-Operators for Universal Data Processing | included | other-userspace - MLIR-based sub-operator IR and compiler in LingoDB; C++/LLVM builds in user space, CPU-only |
| 267 | High-dimensional Data Cubes | out-topic | data cube algorithms |
| 268 | Fast and Scalable Mining of Time Series Motifs with Probabilistic Guarantees | out-topic | time-series motif mining |
| 269 | FEDEX: An Explainability Framework for Data Exploration Steps | out-topic | data exploration explanations |
| 270 | Enabling Transparent Acceleration of Big Data Frameworks using Heterogeneous Hardware | included | other-userspace - Transparent JIT offload of JVM big-data operators to accelerators via TornadoVM; the GPU path works on one A5000 with the NVIDIA OpenCL/PTX backend |
| 271 | Discovering Polarization Niches via Dense Subgraphs with Attractors and Repulsers | out-topic | dense subgraph mining |
| 272 | Sage: A System for Uncertain Network Analysis | out-topic | uncertain network analysis |
| 273 | Mining Bursting Core in Large Temporal Graph | out-topic | temporal graph bursting core mining |
| 274 | Cost-based or Learning-based? A Hybrid Query Optimizer for Query Plan Selection | included | ml-for-systems - Hybrid cost-based plus learned query optimizer for plan selection on PostgreSQL; single node, small models |
| 275 | ONe Index for All  Kernels (ONIAK): A Zero Re-Indexing  LSH Solution to ANNS-ALT | out-topic | LSH for kernel similarity search |
| 276 | Learned Index Benefits: Machine Learning Based Index Performance Estimation | included | ml-for-systems - ML-based index performance/benefit estimation for index tuning; PostgreSQL plus lightweight models, CPU-only |
| 277 | Online Ridesharing with Meeting Points | out-topic | ridesharing optimization |
| 278 | Exploiting the Power of Equality-generating Dependencies in Ontological Reasoning | out-topic | ontological reasoning with EGDs |
| 279 | No Repetition: Fast and Reliable Sampling with Highly Concentrated Hashing | out-topic | hashing and sampling theory |
| 280 | Witness Generation for JSON Schema | out-topic | JSON schema witness generation theory |
| 281 | Towards Observability for Production Machine Learning Pipelines [Vision] | out-topic | vision paper with no released artifact |
| 282 | DINOMO: An Elastic, Scalable, High-Performance Key-Value Store for Disaggregated Persistent Memory | out-machine | key-value store for disaggregated persistent memory over RDMA |
| 283 | Bolt-on, Compact, and Rapid Program Slicing for Notebooks [Scalable Data Science] | out-topic | program slicing tool for notebooks |
| 284 | Fairness Matters: A Tit-For-Tat Strategy Against Selfish Mining | out-topic | blockchain mining game theory |
| 285 | SageDB: An Instance-Optimized Data Analytics System | out-no-code | the SageDB system is not released; the paper links only to a technical report, and no repository exists |
| 286 | Budget-Conscious Fine-Grained Configuration Optimization for Spatio-Temporal Applications | out-topic | configuration tuning for spatio-temporal applications |
| 287 | Nemo: Guiding and Contextualizing Weak Supervision for Interactive Data Programming | out-topic | weak supervision for interactive data programming |
