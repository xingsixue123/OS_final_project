STATUS: complete
TOTAL_PAPERS: 52
INCLUDED: 7

## Sources

- **Primary list:** the official conference site's accepted-papers page,
  <https://www.sigmetrics.org/sigmetrics2024/accepted_papers.html> (fetched with `curl`
  and parsed from raw HTML, not summarized). It groups the papers presented at ACM
  SIGMETRICS / IFIP Performance 2024 (Venice, 10–14 June 2024) by review round:
  Summer deadline 21, Fall deadline 18, Winter deadline 13 = **52**.
- **Cross-check 1 — official program:** <https://www.sigmetrics.org/sigmetrics2024/program.html>.
  The 16 technical sessions (1.A–8.B) contain exactly 52 talks, and the titles match the
  accepted-papers page one-for-one. No extra poster-only main-track papers appear.
- **Cross-check 2 — POMACS editorials (authoritative per-issue counts):** the SIGMETRICS
  "open TOC" pages carry the issue editorials, which state that every paper in the issue
  is presented at SIGMETRICS/Performance 2024.
  - POMACS V7 N3 (Dec 2023, summer round): "publishing **20** papers out of 91 submissions"
    — <https://www.sigmetrics.org/opentoc/acm23_vol7_issue3_toc.html>
  - POMACS V8 N1 (Mar 2024, fall round): "publishing **18** papers out of 118 submissions"
    — <https://www.sigmetrics.org/opentoc/acm24_vol8_issue1_toc.html>
  - POMACS V8 N2 (Jun 2024, winter round): open-TOC page is missing from the site; the
    issue's DOI block 10.1145/3656005–3656018 contains 14 items of which one is the
    editorial (10.1145/3656013), i.e. **13** papers — consistent with the site's Winter list.
  - So 20 + 18 + 13 = 51 POMACS papers. The 52nd title on the conference list,
    "When should prices stay fixed? ...", is presented in the main program (session 6.A)
    but is not in POMACS V7 N3 — it is the joint IFIP Performance contribution. It is
    counted here because it is a main-track talk; it is out of topic scope anyway.
- **Cross-check 3 — Crossref** (`api.crossref.org/journals/2476-1249`) was used to attach
  DOIs to titles and to confirm per-issue DOI ranges. DBLP and the ACM DL were both
  unreachable from this host (bot challenge / HTTP 403), so they could not be used.
- **Abstracts** came from the Semantic Scholar Graph API (by DOI) and arXiv; code checks
  used the GitHub search/repos API, author and lab pages (e.g. Goodwill Computing Lab),
  and the arXiv PDFs where available.

Note on venue character: SIGMETRICS 2024 is dominated by queueing/online-algorithms
theory and Internet/blockchain measurement. Only a small minority of the 52 papers have a
buildable user-space systems artifact, which is why the included list is short.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|
| 1 | Agents of Autonomy: A Systematic Study of Robotics on Modern Hardware | https://dl.acm.org/doi/10.1145/3626774 | https://dl.acm.org/doi/pdf/10.1145/3626774 | https://github.com/cmu-roboarch/rowild | other-userspace | RoWild is an open-source cross-platform user-space robotics benchmark suite (C++/Python, CPU and CUDA) that the paper profiles end-to-end on everything from embedded CPUs to server GPUs; one 16-core CPU plus one A5000 covers the high-end configuration. Concern: the paper is a characterization study and its own conclusions argue for hardware changes, so an improvement project would have to target the software side (kernel fusion, batching, data structures in the motion-planning and SLAM workloads). Second concern: the published characterization leans on architectural counters that perf_event_paranoid=3 blocks, so a reproduction would be limited to wall-clock timing. |
| 2 | The Online Pause and Resume Problem: Optimal Algorithms and An Application to Carbon-Aware Load Shifting | https://dl.acm.org/doi/10.1145/3626776 | https://arxiv.org/pdf/2303.17551 | https://github.com/umassos/pause-resume | scheduling | A suspend/resume scheduling policy for batch compute workloads, evaluated trace-driven on real grid carbon-intensity traces that ship with the repo — squarely the "policies evaluated with simulators or traces" case, and it runs on CPU in pure Python in minutes. Concern: the core contribution is a competitive-ratio proof for double-threshold algorithms, so the artifact is a numerical simulator rather than a system; an "improvement" here would be algorithmic or an empirical extension (e.g. driving it with real checkpoint/restore costs measured on this machine) rather than a systems build. |
| 3 | CarbonScaler: Leveraging Cloud Workload Elasticity for Optimizing Carbon-Efficiency | https://dl.acm.org/doi/10.1145/3626788 | https://arxiv.org/pdf/2302.08681 | https://github.com/umassos/CarbonScaler | scheduling | Elastic resource-allocation policy for batch jobs driven by carbon intensity, with a greedy marginal-allocation scheduler, released code, carbon traces and job scaling profiles; the analytic/trace-driven half is fully reproducible on one machine, and ML-training and MPI scaling profiles can be re-measured locally on 16 cores plus one GPU. Concern: the reference prototype is a Kubernetes autoscaler evaluated on a commercial cloud, and this machine has no root, no Docker and no second node, so the k8s prototype path is closed and the project would have to live in the simulator or in a local process-level re-implementation. |
| 4 | Machine Learning Systems are Bloated and Vulnerable | https://dl.acm.org/doi/10.1145/3639032 | https://arxiv.org/pdf/2212.09437 | https://github.com/reSecureIt/MMLB | other-userspace | MMLB is a user-space measurement and debloating-analysis framework for ML software stacks that quantifies package-level bloat and links it to CVEs; the repo is actively maintained and the analysis itself is plain Python plus vulnerability scanners, which fit the machine easily. Concern: the objects of study are Docker images (TensorFlow/PyTorch/NVIDIA containers) and Docker is not installed and needs root here, so reproduction would require daemonless user-space image tooling (skopeo/umoci/bwrap) to pull and unpack the layers — a real porting risk that the audit stage should weigh. |
| 5 | NetDiffusion: Network Data Augmentation Through Protocol-Constrained Traffic Generation | https://dl.acm.org/doi/10.1145/3639037 | https://arxiv.org/pdf/2310.08543 | https://github.com/noise-lab/NetDiffusion | ml-systems | A user-space generative data pipeline: a fine-tuned Stable Diffusion plus ControlNet model with protocol-constraint post-processing, sized for a single consumer GPU, so a 24 GB A5000 is sufficient for both fine-tuning (LoRA) and inference; the repo is popular and maintained, and generation cost per trace is the paper's acknowledged weak point, which makes a performance-improvement hypothesis natural. Concern: topic fit is the weakest in this list — it is generative ML applied to networking data rather than a core systems artifact, so the audit may prefer to drop it. Second concern: FlashAttention-2 works on Ampere but FP8 kernels do not, which caps some inference-speedup options. |
| 6 | Shrinking VOD Traffic via Renyi-Entropic Optimal Transport | https://dl.acm.org/doi/10.1145/3639033 | https://dl.acm.org/doi/pdf/10.1145/3639033 | unknown | caching | Cache-efficiency work: it proposes Renyi entropy as a proxy for the cache footprint of a video catalogue, proves that minimizing it maximizes soft cache hit ratio, and evaluates on a real VOD request trace. Entirely CPU-side optimal-transport computation over a request trace, so the machine is not a constraint. Concern: no official implementation found — I searched the GitHub repository API for the system name and for "optimal transport / soft cache hit ratio" phrasings, checked the ACM DL landing page and the Edinburgh and Surrey institutional repository records, and found no code or Zenodo artifact link; the Edinburgh open-access PDF is behind a Cloudflare challenge from this host, so I could not read the first-page footnote and cannot rule out a link there. Listed as repo unknown per the code-check rule rather than out-no-code. |
| 7 | BONES: Near-Optimal Neural-Enhanced Video Streaming | https://dl.acm.org/doi/10.1145/3656014 | https://arxiv.org/pdf/2310.09920 | https://github.com/UMass-LIDS/bones | scheduling | A Lyapunov-based controller that jointly schedules a GPU super-resolution enhancement queue against network downloads — a GPU resource manager studied in simulation with real network traces, with code explicitly released in the abstract. Runs on one GPU and CPU-side trace replay. Concern: topic fit is partly video streaming/ABR rather than classic OS scheduling, and the strongest results come from a trace-driven simulator, so a systems improvement would mean strengthening the GPU-side scheduling model (batching, multi-tenant enhancement) rather than the streaming control law. |

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
| 1 | Agents of Autonomy: A Systematic Study of Robotics on Modern Hardware | included | Open user-space RoWild benchmark suite, runs on this CPU+GPU |
| 2 | Invertible Bloom Lookup Tables with Listing Guarantees | out-topic | Coding-theory construction and listing-guarantee proofs, not a systems artifact |
| 3 | Change point detection with adaptive measurement schedules for network performance verification | out-topic | Network performance monitoring statistics, no scope topic applies |
| 4 | Lightweight Acquisition and Ranging of Flows in the Data Plane | out-topic | Programmable-switch flow telemetry sketch, networking data plane is not a scope topic |
| 5 | HEAL: Performance Troubleshooting Deep inside Data Center Hosts | out-no-code | Would fit other-userspace as observability tooling, but no implementation released - searched the GitHub repository API for HEAL and host-metric causality tooling, checked ByteDance and Peking University org repos and the paper abstract, which advertises only an internal production deployment |
| 6 | The Online Pause and Resume Problem: Optimal Algorithms and An Application to Carbon-Aware Load Shifting | included | Carbon-aware suspend/resume scheduling policy with released trace-driven code |
| 7 | MetaVRadar: Measuring Metaverse Virtual Reality Network Activity | out-topic | Network traffic measurement and classification study |
| 8 | Nautilus: A Framework for Cross-Layer Cartography of Submarine Cables and IP Links | out-topic | Internet topology cartography, no scope topic applies |
| 9 | A hop away from everywhere: A view of the intercontinental long-haul infrastructure | out-topic | Internet infrastructure measurement study |
| 10 | GuaNary: Efficient Buffer Overflow Detection In Virtualized Clouds Using Intel EPT-based Sub-Page Write Protection Support | out-machine | Core mechanism is Intel EPT Sub-Page write Permission exposed from a hypervisor to the guest - requires an Intel CPU, KVM and a modified guest kernel; this machine is AMD, has no /dev/kvm access and no root for kernel changes |
| 11 | Near-Optimal Stochastic Bin-Packing in Large Service Systems with Time-Varying Item Sizes | out-topic | Queueing/stochastic bin-packing theory with asymptotic optimality proofs |
| 12 | Kernel vs. User-Level Networking: Don't Throw Out the Stack with the Interrupts | out-machine | Contribution is a modification to the vanilla Linux network stack plus IRQ handling, measured against kernel-bypass stacks on a multi-machine client/server testbed - no root, no kernel builds, and only one host available |
| 13 | Automated Backend Allocation for Multi-Model, On-Device AI Inference | out-no-code | Samsung industrial paper with no released implementation - searched the GitHub repository API for the backend-allocation and on-device pareto-front system, checked Samsung org repos, and the paper carries no artifact link; it also targets memory-constrained embedded SoCs rather than this workstation |
| 14 | When should prices stay fixed? On the chances and limitations of spot pricing in larger markets | out-topic | Market-design and spot-pricing economics |
| 15 | CarbonScaler: Leveraging Cloud Workload Elasticity for Optimizing Carbon-Efficiency | included | Carbon-driven elastic job scheduling with released code and traces |
| 16 | Optimized Cross-Path Attacks via Adversarial Reconnaissance | out-topic | Network security attack modelling |
| 17 | A Large Scale Study and Classification of VirusTotal Reports on Phishing and Malware URLs | out-topic | Security measurement study of URL reports |
| 18 | Sampling for Remote Estimation of the Wiener Process over an Unreliable Channel | out-topic | Remote estimation and age-of-information theory |
| 19 | Near-Optimal Packet Scheduling in Multihop Networks with End-to-End Deadline Constraints | out-topic | Network packet scheduling theory with competitive analysis, no systems artifact |
| 20 | Miracle or Mirage? A Measurement Study of NFT Rug Pulls | out-topic | Blockchain fraud measurement study |
| 21 | Towards Understanding and Characterizing the Arbitrage Bot Scam In the Wild | out-topic | Blockchain scam measurement study |
| 22 | Strategyproof Decision-Making in Panel Data Settings and Beyond | out-topic | Mechanism design and causal-inference theory |
| 23 | Online Conversion with Switching Costs: Robust and Learning-Augmented Algorithms | out-topic | Competitive-analysis theory whose case study is carbon-aware EV charging, an energy-market application rather than a computing system; released code is a Cython numerical simulation |
| 24 | Thorough Characterization and Analysis of Large Transformer Model Training At-Scale | out-machine | The entire question is how training throughput splits into compute and communication as data and model parallelism scale to 512 GPUs across a multi-node interconnect - there is no meaningful single-GPU scale-down, and this machine has one 24 GB A5000 and no second node |
| 25 | Online Allocation with Replenishable Budgets: Worst Case and Beyond | out-topic | Online resource-allocation theory motivated by a solar-powered edge device's energy budget, not a computing-systems artifact |
| 26 | Heavy-Traffic Optimal Size- and State-Aware Dispatching | out-topic | Heavy-traffic queueing theory |
| 27 | SCADA World: An Exploration of the Diversity in Power Grid Networks | out-topic | Industrial control network measurement study |
| 28 | Scalability Limitations of Processing-in-Memory using Real System Evaluations | out-machine | Evaluation is on real UPMEM PIM DIMMs with thousands of PIM cores - custom memory hardware that this machine does not have and that cannot be emulated at the scale the paper studies |
| 29 | NetDiffusion: Network Data Augmentation Through Protocol-Constrained Traffic Generation | included | Single-GPU user-space generative data pipeline with an active released repo; weak topic fit noted |
| 30 | Machine Learning systems are Bloated and Vulnerable | included | MMLB user-space bloat-analysis framework released; Docker dependency flagged as a concern |
| 31 | H3DM: A High-bandwidth High-capacity Hybrid 3D Memory Design for GPUs | out-machine | Proposes true-3D PCM stacking on GPU memory and evaluates it in a cycle-level GPU architecture simulator - hardware design plus simulator-scale compute, both ruled out |
| 32 | Democratizing LEO Satellite Network Measurement | out-topic | Satellite network measurement methodology |
| 33 | StarShip: Mitigating I/O Bottlenecks in Serverless Computing for Scientific Workflows | out-machine | Artifact exists at https://zenodo.org/records/11480216, but the contribution is choosing among commercial serverless storage tiers and multi-tier function configurations on a FaaS platform, optimizing service time against cloud service cost - it needs a real serverless provider, and no local substitute is possible here since Docker and Kubernetes are unavailable without root and only one machine exists |
| 34 | Approximations to Study the Impact of the Service Discipline in Systems with Redundancy | out-topic | Mean-field queueing approximations for redundancy systems |
| 35 | Deep Dive into NTP Pool Popularity and Mapping | out-topic | Internet measurement study of the NTP Pool |
| 36 | Xaminer: An Internet Cross-Layer Resilience Analysis Tool | out-topic | Internet cross-layer resilience analysis, no scope topic applies |
| 37 | Shrinking VOD Traffic via Rényi-Entropic Optimal Transport | included | Cache-footprint and soft-cache-hit-ratio optimization on a real VOD trace; repo unknown |
| 38 | Fair Resource Allocation in Virtualized O-RAN Platforms | out-topic | Radio access network resource allocation, telecom rather than a scope topic |
| 39 | Who's Got My Back? Measuring the Adoption of an Internet-wide BGP RTBH Service | out-topic | BGP blackholing adoption measurement study |
| 40 | BONES: Near-Optimal Neural-Enhanced Video Streaming | included | Joint GPU-enhancement and download scheduling, code released, single-GPU trace-driven |
| 41 | TAO: Re-Thinking DL-based Microarchitecture Simulation | out-no-code | Good ml-for-systems fit and single-GPU trainable, but no official implementation - I read the arXiv PDF (2404.10921) end to end for a release statement and found none, the only repository it points to is the SimNet baseline at https://github.com/lingda-li/simnet, and GitHub repository and author-account searches for the TAO artifact returned nothing |
| 42 | FedQV: Leveraging Quadratic Voting in Federated Learning | out-topic | Federated-learning aggregation rule and poisoning robustness, an ML security algorithm rather than a systems artifact |
| 43 | Strongly Tail-Optimal Scheduling in the Light-Tailed M/G/1 | out-topic | M/G/1 tail-optimality queueing theory |
| 44 | Server Saturation in Skewed Networks | out-topic | Load-balancing limit theory on skewed graphs |
| 45 | Prelimit Coupling and Steady-State Convergence of Constant-stepsize Nonsmooth Contractive SA | out-topic | Stochastic approximation convergence theory |
| 46 | Network Fairness Ambivalence: When Does Diffusion Mitigate or Amplify Unfairness? | out-topic | Social network diffusion and fairness analysis |
| 47 | Analysis of False Negative Rates for Recycling Bloom Filters (Yes, They Happen!) | out-topic | Analytic bounds on Bloom filter false negatives, a probabilistic data-structure analysis with no system to improve |
| 48 | A Closer Look into IPFS: Accessibility, Content, and Performance | out-topic | Measurement study of IPFS content and availability, no reusable system artifact |
| 49 | Continuous Query-based Data Trading | out-topic | Data-market pricing and mechanism design |
| 50 | Multi-dimensional state space collapse in non-complete resource pooling scenarios | out-topic | Heavy-traffic state space collapse theory |
| 51 | Distributed Speed Scaling in Large-Scale Service Systems | out-topic | Mean-field speed scaling theory for large service systems |
| 52 | Learning the Optimal Control for Evolving Systems with Converging Dynamics | out-topic | Online learning and bandit control theory |
