STATUS: complete
TOTAL_PAPERS: 66
INCLUDED: 7

## Sources

- Official conference program (session-by-session, with ACM DL links per paper):
  https://www.sigmetrics.org/sigmetrics2025/program.html — parsed with `curl` + regex; yielded
  exactly 66 papers across sessions 1A–6C (15 sessions of 4 papers, 3 sessions of 2 papers).
- Official accepted-papers page (grouped by submission deadline):
  https://www.sigmetrics.org/sigmetrics2025/accepted_papers.html — parsed independently; yielded
  20 (Summer) + 15 (Fall) + 31 (Winter) = **66** papers. Titles match the program one-for-one.
- Cross-check: the program page contains exactly 66 `[abstract]` links into the SIGMETRICS '25
  abstract proceedings (ACM DL 10.1145/3726854.*), and 60 `[paper]` links into POMACS Vol. 8 No. 3 /
  Vol. 9 No. 1 / Vol. 9 No. 2 (6 papers had no full-paper link posted at scrape time).
- ACM OpenTOC (https://www.sigmetrics.org/opentoc/sigmetrics25toc.html) also lists 66 DL entries
  plus the proceedings front matter, confirming the count.
- DBLP (dblp.org/db/journals/pomacs) was unreachable — the site is behind an Anubis bot challenge
  that blocks `curl`. dl.acm.org is behind Cloudflare and returned 403 for both HTML and PDF, so
  abstracts were obtained from the Semantic Scholar Graph API (55/60 DOIs) and Crossref (remainder),
  and PDF availability was checked via Unpaywall.
- Code search: GitHub REST search API (by system name, paper title keywords and author handles),
  plus targeted web search and author homepages. No repositories were cloned.

Note on scope: SIGMETRICS 2025 is overwhelmingly a queueing-theory / online-algorithms /
network-and-blockchain-measurement venue. 45 of 66 papers are pure theory or measurement studies
with no reusable systems artifact, and most of the remaining systems papers depend on hardware this
machine does not have (persistent memory, CXL, UPMEM PIM, Intel UINTR, SEV-SNP/TDX, Kubernetes
clusters, testbeds). That is why the included set is small.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | Using Lock-Free Design for Throughput-Optimized Cache Eviction (Mobius) | https://dl.acm.org/doi/10.1145/3727136 | https://dl.acm.org/doi/pdf/10.1145/3727136 | https://github.com/Anonymous-chaos/Cachelib-with-Mobius | caching | Lock-free FIFO-queue cache eviction policy (SIEVE-like) evaluated for concurrent throughput and hit ratio; pure user-space C++ integrated into CacheLib and RocksDB. Ideal fit for a 16-core/32-thread box. Second official repo is RocksDB-with-Mobius under the same account. Concern: the artifact account is an anonymized handle with no README-level build docs visible; scaling claims were made on a higher-core-count cluster so absolute numbers will differ. |
| 2 | ScaleOPT: A Scalable Optimal Page Replacement Policy Simulator | https://dl.acm.org/doi/10.1145/3700426 | unknown | https://github.com/syslab-CAU/ScaleOPT | caching | Parallel trace-driven simulator for Belady/OPT page replacement; plain C, CPU-only, compares directly against libCacheSim and webcachesim. Runs entirely in user space on cache traces. Concerns: evaluated on a 72-core machine, so our 16-core/32-thread CPU is a meaningful scale-down (speedup ceiling will be lower); repo has had no pushes since Oct 2024 and the ACM paper is closed-access so the trace list must be recovered from the repo. |
| 3 | Improving Multiresource Job Scheduling with Markovian Service Rate Policies | https://dl.acm.org/doi/10.1145/3727117 | https://arxiv.org/pdf/2412.08915 | https://github.com/jcpwfloi/msr-borg | scheduling | Multiresource job scheduling policy class evaluated by trace-driven simulation on the Google Borg trace; C++ simulator, user space, no cluster needed. Concern: the paper's core contribution is queueing-theoretic (throughput optimality, response-time bounds) and the simulator is a supporting artifact, so an "improvement" project would be partly analytical; the Borg trace download is large and must be budgeted against ~257 GB free. |
| 4 | Learning-Augmented Competitive Algorithms for Spatiotemporal Online Allocation with Deadline Constraints (ST-CLIP) | https://dl.acm.org/doi/10.1145/3711701 | https://dspace.mit.edu/bitstream/1721.1/159050/1/3711701.pdf | https://github.com/umassos/soad-experiments | scheduling | Carbon-aware spatiotemporal scheduling of delay-tolerant batch jobs across datacenters, evaluated as a trace-driven simulation (carbon-intensity traces) in Python/Jupyter — no cluster or root needed. Concern: primarily an online-algorithms paper (competitive ratio, consistency-robustness trade-off); the artifact is a notebook-based simulation harness, so the project would be a policy/prediction improvement rather than a systems build. |
| 5 | A Case Study for Ray Tracing Cores: Performance Insights with BFS and Triangle Counting in Graphs | https://dl.acm.org/doi/10.1145/3727108 | https://dl.acm.org/doi/pdf/10.1145/3727108 | https://github.com/xiaozxiong/RT-Graph | other-userspace | Repurposes GPU RT cores (OptiX BVH + ray casting) for graph BFS, triangle counting and set intersection, compared against CUDA baselines. Single GPU, user space, CUDA code in the repo. Our RTX A5000 is Ampere (CC 8.6) and does have 2nd-gen RT cores plus OptiX support, so the mechanism reproduces. Concerns: the paper's result is largely negative (RT cores lose to CUDA except at high skew), which suits the "reproduction with nuance" fallback; OptiX version may want a newer driver than 535, and large graphs must fit in 24 GB. |
| 6 | Diffusion-Based Generative System Surrogates for Scalable Learning-Driven Optimization in Virtual Playgrounds (DiffNEST) | https://dl.acm.org/doi/10.1145/3727112 | https://dl.acm.org/doi/pdf/10.1145/3727112 | https://github.com/leejunyoung8631/DiffNest | ml-for-systems | Diffusion model that generates synthetic system traces so that RL-based system optimizers can be trained without physical hardware; Python/PyTorch, single-GPU training fits 24 GB. Repo URL is stated in the abstract, so it is unambiguously official. Concerns: the two case studies (task-aware adaptive DVFS, multi-core cache partitioning) actuate hardware knobs that need root here — DVFS via cpupower and CAT/pqos are both blocked — so only the surrogate-training and offline-evaluation half is reproducible; repo is small and was pushed only once (Mar 2025). |
| 7 | CertainSync: Rateless Set Reconciliation with Certainty | https://dl.acm.org/doi/10.1145/3727110 | https://dl.acm.org/doi/pdf/10.1145/3727110 | https://github.com/toto9820/Rateless-Set-Reconciliation-with-Listing-Guarantees | other-userspace | Rateless IBLT-based set reconciliation library with guaranteed (not probabilistic) success; evaluation is a single-machine simulation of communication overhead, no network or root required. Repo title matches the paper exactly. Concerns: contribution is closer to coding theory / distributed protocols than to the topic table's systems categories, and the motivating deployment is blockchain mempool sync — an audit may judge it out of topic. |

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | Steady-State Convergence of the Continuous-Time Routing System with General Distributions in Heavy Traffic | out-topic | Pure queueing theory, no artifact |
| 2 | Finite-Time behavior of Erlang-C Model: Mixing Time, Mean Queue Length and Tail Bounds | out-topic | Pure queueing theory, no artifact |
| 3 | Improving Multiresource Job Scheduling with Markovian Service Rate Policies | included | Trace-driven multiresource scheduling simulator on Google Borg traces; code at github.com/jcpwfloi/msr-borg |
| 4 | On the Distribution of Sojourn Times in Tandem Queues | out-topic | Pure queueing theory, tail bounds only |
| 5 | Online Allocation with Multi-Class Arrivals: Group Fairness vs Individual Welfare | out-topic | Online-algorithms theory, fairness guarantees |
| 6 | Game Theoretic Liquidity Provisioning in Concentrated Liquidity Market Makers | out-topic | DeFi / AMM game theory |
| 7 | Two Choice Behavioral Game Dynamics with Myopic-Rational and Herding Players | out-topic | Behavioral game theory |
| 8 | Allocating Public Goods via Dynamic Max-Min Fairness: Long-Run Behavior and Competitive Equilibria | out-topic | Mechanism design theory |
| 9 | MUDGUARD: Taming Malicious Majorities in Federated Learning using Privacy-preserving Byzantine-robust Clustering | out-topic | Federated-learning security and crypto protocol, not a systems topic in the table |
| 10 | Application-driven Reexamination of Datacenter Microbursts | out-topic | Datacenter network measurement study |
| 11 | VESTA: A Secure and Efficient FHE-based Three-Party Vectorized Evaluation System for Tree Aggregation Models | out-topic | Homomorphic-encryption cryptosystem |
| 12 | Confidential VMs Explained: An Empirical Analysis of AMD SEV-SNP and Intel TDX | out-machine | Core contribution measures AMD SEV-SNP and Intel TDX confidential VMs; needs that CPU hardware, a hypervisor and root. env.md has no KVM access and no root |
| 13 | DiskAdapt: Hard Disk Failure Prediction based on Pre-training and Fine-tuning | out-no-code | In topic (ml-for-systems) and runs fine on one GPU, but no artifact found: GitHub repo search on DiskAdapt and AdaptFormer disk-failure terms returns 0 hits, no URL in the abstract, no artifact link on the ACM/SIGMETRICS pages, and web search surfaced no repository |
| 14 | PROPHET: PRediction Of 5G bandwidtH using Event-driven causal Transformer | out-topic | Cellular bandwidth prediction for vehicular RTC; networking ML, not a systems topic in the table |
| 15 | Diffusion-Based Generative System Surrogates for Scalable Learning-Driven Optimization in Virtual Playgrounds | included | Diffusion surrogate for system-level optimization; code at github.com/leejunyoung8631/DiffNest |
| 16 | FastFlow: Early Yet Robust Network Flow Classification using the Minimal Number of Time-Series Packets | out-topic | Network traffic classification |
| 17 | Using Lock-Free Design for Throughput-Optimized Cache Eviction | included | Lock-free cache eviction policy in CacheLib and RocksDB; code at github.com/Anonymous-chaos |
| 18 | Optimal SSD Management with Predictions | out-no-code | In topic (storage, learning-augmented garbage collection) and trace-simulatable, but no released artifact: GitHub search on Gladiator SSD and related terms returns 0 hits, author GitHub profiles (Lange, Naor, Yadgar) carry no such repo, Unpaywall lists only the ACM PDF, and web search found no code |
| 19 | Adversarial Network Optimization under Bandit Feedback: Maximizing Utility in Non-Stationary Multi-Hop Networks | out-topic | Bandit / stochastic network optimization theory |
| 20 | Reducing Sensor Requirements by Relaxing the Network Metric Dimension | out-topic | Graph theory, source localization |
| 21 | The Tale of Errors in Microservices | out-topic | Measurement study of 11B RPCs on Uber's proprietary production fleet; no reusable artifact and the data cannot be released |
| 22 | Quantum Computing in the RAN: Closing Gaps Towards Quantum-based FEC processors | out-topic | Quantum computing for wireless baseband |
| 23 | Design and Modeling of a New File Transfer Architecture to Reduce Undetected Errors Evaluated in the FABRIC Testbed | out-machine | Recursive in-network error detection whose evaluation requires the FABRIC multi-node testbed with programmable in-network resources; env.md allows only this single host |
| 24 | Beaver: A High-Performance and Crash-Consistent File System Cache via PM-DRAM Collaborative Memory Tiering | out-machine | Design depends on real persistent memory (PM-DRAM tiering) and an in-kernel kprefetcher; env.md rules out persistent memory and kernel modules |
| 25 | Tiered Cloud Routing: Methodology, Latency, and Improvement | out-topic | Internet/cloud WAN routing measurement |
| 26 | Exploring Function Granularity for Serverless Machine Learning Application with GPU Sharing | out-no-code | Topically close (ml-systems, single-GPU sharing) but no artifact: GitHub search by title keywords returns 0 hits, the author's GitHub account has only personal pages, and web search found no repository. Would additionally need a container-based serverless platform, which env.md rules out (no Docker, no root) |
| 27 | UniContainer: Unlocking the Potential of Unikernel for Secure and Efficient Containerization | out-machine | Partitions containers into Unikraft unikernels, which are booted as VMs; env.md gives no /dev/kvm access and no root, and no public artifact was found |
| 28 | Microns: Connection Subsetting for Microservices in Shared Clusters | out-machine | Requires a shared multi-node microservice cluster with persistent inter-container connections; env.md provides one machine, no Kubernetes and no root. No public artifact found |
| 29 | A Piecewise Lyapunov Analysis of Sub-quadratic SGD: Applications to Robust and Quantile Regression | out-topic | Stochastic-approximation theory |
| 30 | Optimal Aggregation via Overlay Trees: Delay-MSE Tradeoffs under Failures | out-topic | Distributed aggregation theory |
| 31 | The Power of Migrations in Dynamic Bin Packing | out-topic | Online-algorithms theory |
| 32 | Tight bounds for Dynamic Bin Packing with Predictions | out-topic | Online-algorithms theory |
| 33 | Uncovering BGP Action Communities and Community Squatters in the Wild | out-topic | Internet routing measurement |
| 34 | Beyond App Markets: Demystifying Underground Mobile App Distribution Via Telegram | out-topic | Mobile app ecosystem measurement |
| 35 | INT-MC: Low-Overhead In-Band Network-Wide Telemetry Based on Matrix Completion | out-topic | In-band network telemetry |
| 36 | Beyond Data Points: Regionalizing Crowdsourced Latency Measurements | out-topic | Broadband measurement methodology |
| 37 | Asynchronous Multi-Agent Bandits: Fully Distributed vs. Leader-Coordinated Algorithms | out-topic | Multi-armed bandit theory |
| 38 | Combinatorial Logistic Bandits | out-topic | Multi-armed bandit theory |
| 39 | Online Fair Allocation of Reusable Resources | out-topic | Online-algorithms theory |
| 40 | Universal and Tight Bounds on Counting Errors of Count-Min Sketch with Conservative Updates | out-topic | Analytical bounds on sketch error, Markov-chain analysis only |
| 41 | Internet Service Usage and Delivery As Seen From a Residential Network | out-topic | Residential network traffic measurement |
| 42 | The Last Survivor of PoS Pools: Staker's Dilemma | out-topic | Blockchain staking game theory |
| 43 | Understanding Intel User Interrupts | out-machine | Studies the UINTR instruction set extension on recent Intel Xeon CPUs, with KVM guest measurements; our CPU is an AMD Threadripper and env.md gives no KVM and no root |
| 44 | A Case Study for Ray Tracing Cores: Performance Insights with Breadth-First Search and Triangle Counting in Graphs | included | Single-GPU CUDA/OptiX study of RT cores for graph workloads; code at github.com/xiaozxiong/RT-Graph |
| 45 | Peer-to-Peer Distribution of Graph States Across Spacetime Quantum Networks of Arbitrary Topology | out-topic | Quantum networking |
| 46 | Modeling and Simulating Rydberg Atom Quantum Computers for Hardware-Software Co-design with PachinQo | out-topic | Quantum computer architecture simulation |
| 47 | Optimal Scheduling in a Quantum Switch: Capacity and Throughput Optimality | out-topic | Quantum switch queueing theory |
| 48 | Quantum Network Optimization: From Optimal Routing to Fair Resource Allocation | out-topic | Quantum network routing theory |
| 49 | NetJIT: Bridging the Gap from Traffic Prediction to Preknowledge for Distributed Machine Learning | out-machine | Predicts and exploits inter-node traffic of distributed ML jobs, validated on a self-built multi-node network testbed with traffic/topology engineering; env.md has a single machine and no cluster network |
| 50 | ScaleOPT: A Scalable Optimal Page Replacement Policy Simulator | included | Parallel OPT cache simulator in C; code at github.com/syslab-CAU/ScaleOPT |
| 51 | PipeCo: Pipelining Cold Start of Deep Learning Inference Services on Serverless Platforms | out-machine | Prototype is built on the OpenFaaS serverless platform and evaluated on CPU and GPU clusters; env.md has no Docker/Podman, no Kubernetes, no root and a single node. No public artifact found either |
| 52 | PyGim: An Efficient Graph Neural Network Library for Real Processing-In-Memory Architectures | out-machine | Targets a real UPMEM PIM system with 16 PIM DIMMs and 1992 PIM cores; that hardware does not exist on this machine |
| 53 | CertainSync: Rateless Set Reconciliation with Certainty | included | User-space rateless IBLT set-reconciliation library with simulation harness; code at github.com/toto9820 |
| 54 | CHash: A High Cost-Performance Hash Design for CXL-based Disaggregated Memory System | out-machine | Requires real CXL 1.0 memory devices on 4th-gen Intel Xeon; env.md rules out CXL and persistent-memory-class hardware |
| 55 | Learning-Augmented Decentralized Online Convex Optimization in Networks | out-topic | Online convex optimization theory |
| 56 | Robust Gittins for Stochastic Scheduling | out-topic | Stochastic scheduling theory, no artifact |
| 57 | Learning-Augmented Competitive Algorithms for Spatiotemporal Online Allocation with Deadline Constraints | included | Carbon-aware workload allocation evaluated by trace-driven simulation; code at github.com/umassos/soad-experiments |
| 58 | A Gittins Policy for Optimizing Tail Latency | out-topic | M/G/1 scheduling theory, asymptotic tail optimality, no artifact |
| 59 | Revisiting Traffic Splitting for Software Switch in Datacenter | out-machine | VALO is implemented inside Open vSwitch and measured on a multi-machine datacenter topology; the OVS datapath needs root/kernel privileges and env.md gives neither, plus no second machine |
| 60 | Exploiting Kubernetes Autoscaling for Economic Denial of Sustainability | out-machine | Experiments require a realistic Kubernetes cluster with autoscaling and cloud billing; env.md has no Kubernetes, no container runtime, no root and one node |
| 61 | A Global Perspective on the Past, Present, and Future of Video Streaming over Starlink | out-topic | LEO satellite video-streaming measurement on proprietary Netflix data |
| 62 | ForgetMeNot: Understanding and Modeling the Impact of Forever Chemicals Toward Sustainable Large-Scale Computing | out-topic | Semiconductor-fabrication emissions modeling; sustainability accounting, not a systems topic in the table |
| 63 | Phishing Tactics Are Evolving: An Empirical Study of Phishing Contracts on Ethereum | out-topic | Blockchain security measurement |
| 64 | Blockchain Amplification Attack | out-topic | Ethereum P2P network attack analysis |
| 65 | Piecing Together the Jigsaw Puzzle of Transactions on Heterogeneous Blockchain Networks | out-topic | Cross-chain bridge measurement |
| 66 | Towards Understanding and Analyzing Instant Cryptocurrency Exchanges | out-topic | Blockchain service measurement |
