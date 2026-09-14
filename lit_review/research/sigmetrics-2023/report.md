STATUS: complete
TOTAL_PAPERS: 54
INCLUDED: 3

## Sources

Primary enumeration: the official conference site, ACM SIGMETRICS 2023 (Orlando, FL, June 19–22, 2023, co-located with FCRC).

- Accepted-papers page: https://www.sigmetrics.org/sigmetrics2023/accepted_papers.html — lists all main-track POMACS papers grouped by review round: Summer deadline 17, Fall deadline 26, Winter deadline 11 = **54**.
- Conference program page: https://www.sigmetrics.org/sigmetrics2023/program.html — the 16 technical sessions (1A/1B … 8A/8B) list 4+3+3+3+3+3+4+4+4+4+3+3+3+3+3+4 = **54** talks. Workshops, tutorials, keynotes and the two SRC poster sessions were excluded.

Cross-check: the two pages were parsed independently (raw HTML via `curl`, then tag-stripped in Python) and give the same 54 titles, so TOTAL_PAPERS = 54.

Secondary cross-checks used for DOIs / issue assignment (both are partial, so they were not used for the count):

- SIGMETRICS OpenTOC pages, which carry the free ACM DL links: http://www.sigmetrics.org/opentoc/acm22_vol6_issue3_toc.html (POMACS 6(3), Dec 2022 = Summer round), http://www.sigmetrics.org/opentoc/acm23_vol7_issue1_toc.html (POMACS 7(1), Mar 2023 = Fall round), http://www.sigmetrics.org/opentoc/acm23_vol7_issue2_toc.html (POMACS 7(2), Jun 2023 = Winter round). These list 17 + 23 + 8 = 48 papers plus 3 editorials; the 6 missing entries are all queueing/online-optimization theory papers and are present on the conference pages.
- OpenAlex (`primary_location.source.issn:2476-1249`) returns exactly the same 48 papers + 3 editorials for those three issues, i.e. it reproduces the OpenTOC gap.
- DBLP (dblp.org and dblp.uni-trier.de) and the ACM DL TOCs were both unreachable from this host (anti-bot challenge / HTTP 403), so they could not be used.

Code checks used: GitHub repository search API, authors' and lab homepages (liuhongyuan.com, adwaitjog.github.io/software.html, chenavin.github.io/publications, haibo.pro), Semantic Scholar and Unpaywall for abstracts / open-access PDFs, and repository READMEs for dependency requirements.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | Optimistic No-regret Algorithms for Discrete Caching | https://dl.acm.org/doi/10.1145/3570608 | https://arxiv.org/pdf/2208.06414 | https://github.com/Naram-m/discrete-online-learning | caching | Prediction-assisted (oracle/NN-guided) discrete caching policies with a new optimistic Follow-the-Perturbed-Leader family; evaluated trace-driven on MovieLens and similar request traces. Pure CPU Python, no root, no GPU needed — a natural fit for the machine. Improvement angle - the policies are O(N) per request in the number of files and the paper itself trades performance against complexity; a faster implementation or a real cache integration is a testable hypothesis. Concern - the paper is theory-heavy and the released code is a numerical-experiment harness rather than a cache system so a reproduction may feel thin without extending it to a real workload trace |
| 2 | Smash: Flexible, Fast, and Resource-efficient Placement and Lookup of Distributed Storage | https://dl.acm.org/doi/10.1145/3589977 | https://dl.acm.org/doi/pdf/10.1145/3589977 | https://github.com/yliu634/smash | storage | Object placement and lookup for distributed object stores using a space-efficient lookup structure instead of hashing; claims full placement flexibility with under 60 percent of the DRAM of Ceph/MapX. Core artifact is a self-contained user-space C++ library built with cmake and gcc 12 which the machine has. Concern - the paper's headline evaluation was run in a public cloud with multiple storage nodes, so a single-machine study would have to fall back to multi-process emulation plus data-structure microbenchmarks (memory cost, lookup latency, recovery time); the repo has no CI and was last pushed in 2021, so build friction is a real risk |
| 3 | DiffForward: On Balancing Forwarding Traffic for Modern Cloud Block Services via Differentiated Forwarding | https://dl.acm.org/doi/10.1145/3579444 | unknown | https://github.com/wzhzhu/DiffForward | storage | Separates burst from stable write traffic at the client of a cloud block service and routes burst traffic round-robin into a decentralized log store to remove the proxy-layer imbalance. Official code released by the first author (Python, client/server/manager/utils). In-topic as a storage-engine/IO-path policy that is trace-driven. Concerns - the system is inherently multi-role (client, proxy servers, distributed log store) so on one host it can only be run as co-located processes; no README or build instructions in the repo and no open-access PDF found, so the burst-detection mechanism would have to be reconstructed from the ACM DL version |

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | Joint Learning and Control in Stochastic Queueing Networks with Unknown Utilities | out-topic | Queueing-network control theory |
| 2 | Characterizing Cryptocurrency-themed Malicious Browser Extensions | out-topic | Security measurement study |
| 3 | Optimal Scheduling in the Multiserver-job Model under Heavy Traffic | out-topic | Pure queueing theory heavy-traffic analysis, no systems artifact |
| 4 | Robust Multi-Agent Bandits Over Undirected Graphs | out-topic | Bandit learning theory |
| 5 | The Online Knapsack Problem with Departures | out-topic | Online algorithms theory |
| 6 | Characterizing the Performance of Accelerated Jetson Edge Devices for Training Deep Learning Models | out-machine | The whole contribution is a characterization of NVIDIA Jetson AGX Xavier, Xavier NX and Nano boards - varying power modes, shared-memory behaviour and storage media on that specific edge hardware. None of those devices exist on this machine and the results do not transfer to a desktop RTX A5000 |
| 7 | On the stochastic and asymptotic improvement of First-Come First-Served and Nudge scheduling | out-topic | Queueing theory analysis of Nudge scheduling |
| 8 | Leveraging the properties of mmWave Signals for 3D Finger Motion Tracking for Interactive IoT Applications | out-topic | mmWave wireless sensing |
| 9 | Malcolm: Multi-agent Learning for Cooperative Load Management at Rack Scale | out-machine | Code is released at github.com/uwaterloo-mast/malcolm but its README requires eRPC, which needs InfiniBand or DPDK-enabled NICs and hugepages allocated per NUMA node, plus a cluster of machines driven by scripts/runCluster.py. Hugepage setup and DPDK need root, and there is no second machine |
| 10 | Dynamic Bin Packing with Predictions | out-topic | Online algorithms with predictions, theory |
| 11 | Optimistic No-regret Algorithms for Discrete Caching | included | Trace-driven prediction-assisted caching policies with official CPU-only code |
| 12 | Streaming Algorithms for Constrained Submodular Maximization | out-topic | Submodular optimization theory |
| 13 | FuncPipe: A Pipelined Serverless Framework for Fast and Cost-efficient Training of Deep Learning Models | out-machine | The framework partitions DL models across many concurrent serverless functions on a commercial FaaS platform (AWS Lambda class) with object storage, and its cost model is built on that platform's pricing. There is no way to reproduce the memory/bandwidth limits and per-function pricing that the whole design targets on one local node |
| 14 | Enabling Long-term Fairness in Dynamic Resource Allocation | out-topic | Online convex optimization theory |
| 15 | Noise in the Clouds: Influence of Network Performance Variability on Application Scalability | out-machine | A measurement study of network-noise effects across HPC and cloud clusters (multi-node MPI runs over InfiniBand/EFA). Requires many interconnected nodes; single-machine only here |
| 16 | Switching in the Rain: Predictive Wireless x-haul Network Reconfiguration | out-topic | Wireless x-haul networking |
| 17 | The M/M/k with deterministic setup times | out-topic | Queueing theory |
| 18 | DareShark - Detecting and Measuring Security Risks of Hosting-Based Dangling Domains | out-topic | DNS/security measurement study |
| 19 | Asynchronous Automata Processing on GPUs | out-no-code | Topically a good fit - a single-GPU user-space automata engine. But no official release found. Checked the first author's homepage liuhongyuan.com which explicitly links an Artifact for the ASPLOS 24 ngAP paper but nothing for AsyncAP, Adwait Jog's publication page which lists only a PDF, Jog's software/artifacts page which lists the ASPLOS 20 gpunfa-artifact and MAFIA but not AsyncAP, and GitHub repository search for AsyncAP and for automata processing GPU. getianao/ngAP is a different ASPLOS 24 paper, not the AsyncAP release |
| 20 | DaeMon: Architectural Support for Efficient Data Movement in Fully Disaggregated Systems | out-machine | The contribution is hardware support - DaeMon hardware units added to compute and memory blades - evaluated in an architectural simulator for a disaggregated machine. Needs custom hardware/simulation infrastructure ruled out by env.md |
| 21 | Bias and Extrapolation in Markovian Linear Stochastic Approximation with Constant Stepsizes | out-topic | Stochastic approximation theory |
| 22 | Network Monitoring on Multi-Pipe Switches | out-topic | Programmable switch ASIC dataplane monitoring, networking |
| 23 | Power-of-d Choices Load Balancing in the Sub-Halfin Whitt Regime | out-topic | Queueing theory asymptotics |
| 24 | Detecting and Measuring Aggressive Location Harvesting in Mobile Apps via Data-flow Path Embedding | out-topic | Mobile app security measurement |
| 25 | Gacha Game Analysis and Design | out-topic | Game theory and mechanism design |
| 26 | A Comparative Analysis of Ookla Speedtest and Measurement Labs Network Diagnostic Test (NDT7) | out-topic | Network measurement study |
| 27 | Duo: A High-Throughput Reconfigurable Datacenter Network Using Local Routing and Control | out-topic | Reconfigurable optical datacenter networking |
| 28 | (Private) Kernelized Bandits with Distributed Biased Feedback | out-topic | Bandit and privacy theory |
| 29 | Fiat Lux: Illuminating IPv6 Apportionment with Different Datasets | out-topic | Internet measurement study |
| 30 | Batching of Tasks by Users of Pseudonymous Forums: Anonymity Compromise and Protection | out-topic | Anonymity and privacy analysis |
| 31 | Bias and Refinement of Multiscale Mean Field Models | out-topic | Mean-field model theory |
| 32 | PEACH: Proactive and Environment Aware Channel State Information Prediction with Depth Images | out-topic | Wireless CSI prediction |
| 33 | A First Look at Wi-Fi 6 in Action: Throughput, Latency, Energy Efficiency, and Security | out-topic | Wi-Fi 6 measurement study |
| 34 | Online Adversarial Stabilization of Unknown Networked Systems | out-topic | Control theory |
| 35 | Each at its own pace: Third-party Dependency and Centralization Around the World | out-topic | Web dependency measurement study |
| 36 | SLITS: Sparsity-Lightened Intelligent Thread Scheduling | out-machine | The scheduler builds a Thread-Interaction Matrix from hardware performance counters through perf_events, which is blocked here by perf_event_paranoid=3, and the design adds a hardware TIS-Cache whose chip-area and power overheads are part of the evaluation. Separately, the paper PDF contains no artifact URL - its only GitHub link is the third-party xlearn factorization-machine library - and no repository was found |
| 37 | Go-to-Controller is Better: Efficient and Optimal LPM Caching with Splicing | out-no-code | In-topic as an LPM rule-caching policy with dependency constraints that could be studied trace-driven. But no implementation found - checked GitHub repository search for LPM caching and for splicing cache SDN, GitHub user search for Gozlan and Einziger, Chen Avin's publication page at chenavin.github.io/publications which lists no artifact link for this paper, and the BGU research portal entry. The ACM DL page carries no artifact badge |
| 38 | Mean-field Analysis for Load Balancing on Spatial Graphs | out-topic | Mean-field queueing theory |
| 39 | Smoothed Online Optimization with Unreliable Predictions | out-topic | Online optimization theory |
| 40 | Global Convergence of Localized Policy Iteration in Networked Multi-Agent Reinforcement Learning | out-topic | Reinforcement learning theory |
| 41 | JS Capsules: A Framework for Capturing Fine-grained JavaScript Memory Measurements for the Mobile Web | out-machine | The framework instruments browser internals and was run on a testbed of Android mobile phones crawling the Alexa top 1K. It needs physical Android handsets and instrumented browser builds; neither is available and the results are about mobile browser memory, not desktop |
| 42 | DiffForward: On Balancing Forwarding Traffic for Modern Cloud Block Services via Differentiated Forwarding | included | Storage IO-path forwarding policy with official code released by the first author |
| 43 | Mars: Near-Optimal Throughput with Shallow Buffers in Reconfigurable Datacenter Networks | out-topic | Reconfigurable datacenter network theory |
| 44 | SMASH: Flexible, Fast, and Resource-efficient Placement and Lookup of Distributed Storage | included | User-space C++ object placement and lookup library with official code |
| 45 | Towards Accelerating Data Intensive Application's Shuffle Process Using SmartNICs | out-machine | The contribution offloads the shuffle stage onto SmartNICs (BlueField-class DPUs). SmartNICs/DPUs are explicitly out of scope and none are present |
| 46 | Constant Regret Primal-Dual Policy for Multi-way Dynamic Matching | out-topic | Dynamic matching theory |
| 47 | Online Fair Allocation with Perishable Resources | out-topic | Online fair allocation theory |
| 48 | Overcoming the Long Horizon Barrier for Sample-Efficient Reinforcement Learning with Latent Low-Rank Structure | out-topic | Reinforcement learning theory |
| 49 | SplitRPC: A Control plus Data Path Splitting RPC Stack for ML Inference Serving | out-machine | Code exists at github.com/minus-one/splitrpc but the stack is built on DPDK, RDMA/libibverbs, GPUDirect and a BlueField SmartNIC data path - the README has separate directories for the SmartNIC-side and host-side servers. DPDK and RDMA need root and hardware this machine does not have |
| 50 | Online Resource Allocation under Horizon Uncertainty | out-topic | Online resource allocation theory |
| 51 | CoBF: Coordinated Beamforming in Dense mmWave Networks | out-topic | mmWave wireless networking |
| 52 | Real-time Spread Burst Detection in Data Streaming | out-topic | Network-traffic sketch/streaming estimator, outside the scope topic table; no code found on the authors' pages either |
| 53 | Strategic Latency Reduction in Blockchain Peer-to-Peer Networks | out-topic | Blockchain peer-to-peer networking |
| 54 | Memtrade: Marketplace for Disaggregated Memory on Clouds | out-machine | Code exists at github.com/SymbioticLab/Memtrade but the repo ships an Infiniswap RDMA block device and a tswap swap module plus a balloon driver - these are kernel modules over InfiniBand, and the marketplace needs separate producer and consumer VMs. No root, no kernel modules, no RDMA and no second machine here |
