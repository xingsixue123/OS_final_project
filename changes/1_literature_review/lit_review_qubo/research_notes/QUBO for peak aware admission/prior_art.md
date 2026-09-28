# Prior-art scoop check: PeakBaleen (QUBO/Ising, peak-aware, budget-constrained flash-cache admission)

Research date: 2026-09-27. About 20 searches and fetches (web search, arXiv, USENIX PDF, CMU tech-report PDF). Semantic Scholar's citation API returned HTTP 429, and ACM DL pages returned 403, so **the citing-papers list for Baleen could not be enumerated directly**. Anything marked [UNVERIFIED] comes from background knowledge and was not re-checked in this session.

## Q1: Has anyone applied QUBO, Ising machines, quantum annealing or similar combinatorial solvers to caching, storage, data placement or prefetching?

### Takeaway
Yes, but only in neighbouring problems: joint cache placement plus power allocation in wireless or satellite networks, distributed-database data or replica allocation, and database index selection and join ordering. I found **no** work that applies QUBO or Ising methods to flash-cache admission, cache replacement, storage-tier admission under a write budget, prefetching, or any min-max (peak) load objective. The closest hit is a wireless edge-caching placement problem. It is static, maximizes throughput, and has no time dimension or write budget.

### Cited Findings
- **Zhang, Gong, Fan, Wang, Han, Guo, "Quantum-Assisted Joint Caching and Power Allocation for Integrated Satellite-Terrestrial Networks"**. arXiv Dec 2023, reported as IEEE Trans. Network Science & Engineering 2024 (the TNSE venue comes from a search snippet [partly UNVERIFIED]).
  - The joint problem (content delivery policy, cache placement, transmit power) is a MINLP that maximizes network throughput.
  - Generalized Benders decomposition splits it into a binary master problem (cache placement and delivery) and a continuous subproblem. The master problem is converted to QUBO and solved on a D-Wave annealer.
  - It has no temporal or peak dimension. — [arXiv 2312.14448](https://arxiv.org/abs/2312.14448), [HTML](https://arxiv.org/html/2312.14448v1)
  - **Closeness to PeakBaleen:** it is the most direct "QUBO for caching" precedent. However, the problem is static content placement in a wireless network: no admission over time, no write-rate budget, no min-max objective, no ML distillation.
- **Same group, "Quantum-Assisted Online Task Offloading and Resource Allocation in MEC-Enabled Satellite-Aerial-Terrestrial Integrated Networks"**. arXiv 2312.15808. This is QA for MEC offloading, not caching. — [arXiv 2312.15808](https://arxiv.org/pdf/2312.15808)
- **"Leveraging Quantum Computing for Optimal Data Allocation in Distributed Systems"**. Q-Data '25 (2nd Workshop on Quantum Computing and Quantum-Inspired Technology for Data-Intensive Systems and Applications, ACM).
  - It turns data-partition allocation, with node storage capacity, k-safety replication and remote-access network cost, into QUBO for quantum annealers, and analyses how many qubits are needed.
  - It is static placement with no time windows and no peak objective. Authors could not be retrieved (ACM 403). — [ACM DL](https://dl.acm.org/doi/10.1145/3736393.3736692)
- **"Leveraging Quantum Computing for Database Index Selection"**. Q-Data '24 (1st workshop, ACM). Index selection is a knapsack-like "what to materialize under a budget" problem. Details not fetched. — [ACM DL](https://dl.acm.org/doi/10.1145/3665225.3665445)
- **Database query optimization on annealers:**
  - Trummer & Koch, "Multiple Query Optimization on the D-Wave 2X", VLDB 2016.
  - Schönberger, Trummer, Mauerer, "Quantum-Inspired Digital Annealing for Join Ordering", PVLDB 17 (2023/24), using the Fujitsu Digital Annealer, which is an Ising-machine class.
  - These show QUBO and Ising methods are accepted in data-systems venues, but none of them concern caching. — [PVLDB vol17 p511](https://www.vldb.org/pvldb/vol17/p511-schonberger.pdf), [ACM](https://dl.acm.org/doi/abs/10.14778/3632093.3632112)
- **QCE'24 Tutorial, "Quantum Annealing – Emerging Exploration for Database Optimization"**. A survey of QA for database optimization. It shows the area exists but is database-centric. — [arXiv 2411.04638](https://arxiv.org/html/2411.04638v1)
- **Other placement problems on annealers:**
  - FPGA placement via quantum annealing — [arXiv 2312.15467](https://arxiv.org/pdf/2312.15467)
  - Quantum-based edge-node placement and workload allocation — [arXiv 2306.01159](https://arxiv.org/pdf/2306.01159)
  - Neither involves caching.
- **"Edge Caching in Fog-Based Sensor Networks through Deep Learning-Associated Quantum Computing Framework"**. PMC / Sensors-style journal, 2022. It is described as a DL agent with a "quantum memory module". It does not appear to be a QUBO or annealing formulation of admission [UNVERIFIED, not fetched]. — [PMC8759837](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8759837/)
- **Simulated bifurcation (Toshiba SBM) applications:** the published ones I found are finance, TSP, MAXCUT and 5G wireless resource allocation. None are in storage or caching. — [Goto et al., Science Advances 2019](https://www.science.org/doi/10.1126/sciadv.aav2372), [Toshiba](https://www.global.toshiba/ww/company/digitalsolution/articles/tsoul/tech/t0501.html)
- **Keyword searches came back empty.** Searches for "Ising machine" + cache replacement or admission, QUBO + storage tiering, and simulated bifurcation + storage or caching or disk scheduling returned no relevant papers. — [search: Ising/QUBO cache admission](https://sdm.lbl.gov/~arie/papers/Cache.replacement.CCjournal.pdf) (irrelevant top hit, which shows the gap)

### Inferences
- "First QUBO/Ising formulation of **budget-constrained flash-cache admission**" appears to hold. This is **moderately high confidence (~80%)**. The residual risk is:
  - an obscure IEEE Access, MDPI or Chinese-journal paper doing QA for "edge caching" under a capacity knapsack;
  - patents (e.g., Fujitsu, Toshiba or IBM filings on "Ising machine for cache/storage allocation"), which I did not search systematically.
- "First QUBO formulation of *any* caching problem" does **not** hold. Wireless content-placement QUBO exists (Zhang et al. 2023/24), and so do data-allocation QUBOs (Q-Data '25). The novelty claim must be scoped to *flash admission / time-indexed episodes / write budget / min-max peak*.
- No QUBO work I found encodes a **min-max over time windows**. Min-max needs auxiliary slack variables or penalty or epigraph tricks in QUBO. This encoding itself is a defensible technical contribution.

### Gaps
- Could not enumerate IEEE Xplore results (INFOCOM, ICC, Globecom, TCOM, IoT-J) for "quantum annealing" + "caching" beyond what web search surfaced. A manual IEEE Xplore query is recommended: ("quantum annealing" OR QUBO OR "Ising") AND (caching OR "cache placement").
- Patent search was not done.
- There is a likely-relevant body of work on quantum materialized-view selection (e.g., Trummer et al.). It was not verified in this session.

## Q2: Offline-optimal and combinatorial flash-cache admission. Does any of it optimize peak load explicitly?

### Takeaway
All the major flash-admission works optimize **aggregate or average** quantities: hit ratio, disk reads, TCO, or mean disk-head time (DT) under a write budget.
- CacheSack uses a knapsack.
- Cheng et al. and Lyons et al. use min-cost or network flow.
- Baleen's OPT is a greedy episode knapsack.

Baleen itself explicitly defers peak optimization. The strongest prior art is **Daniel Wong's PhD thesis (CMU-CS-24-152, 2024), Chapter 7**. It *attempted* explicit Peak-DT admission and reported partial failure. PeakBaleen must cite it and differentiate from it.

### Cited Findings
- **Baleen (Wong et al., FAST 2024)**, §3.1.
  - It defines Peak DT as the P100 backend DT utilization over 10-minute intervals.
  - It states: "This introduces the need for scheduling (i.e., when to spend the flash write rate budget) to prioritize the admission of items that contribute to the Peak DT. As explicitly optimizing admission for the peak introduces significant complexity, we leave that for future work. For this paper, we design our admission and prefetching policies to minimize average DT…"
  - §5.6 reports that a simple "admit only during high load" extension saved flash writes but did **not** reduce Peak DT. It concludes that "more fundamental changes (e.g., scoring episodes by their usefulness in reducing Peak DT) will be required."
  - §2 says: "only one other system evaluates load at peak [42]", and [42] is HALP. — [USENIX PDF](https://www.usenix.org/system/files/fast24-wong.pdf), [USENIX page](https://www.usenix.org/conference/fast24/presentation/wong)
- **Daniel Lin-Kit Wong, "Machine learning for flash caching in bulk storage systems", CMU PhD thesis, CMU-CS-24-152 (2024), Chapter 7 "Optimizing for peak load".** This is the **key scoop risk**.
  - **§7.4.1, varying selectivity by load level:**
    - Method: a load-dependent admission threshold, which moves the write budget from off-peak to peak. It was applied to OPT, admitting only when load was above 30% of the last peak.
    - Result on Region3: flash writes fell 8.0% and Peak DT fell only 1.4%.
  - **§7.4.2, prioritizing episodes by contribution to peak:** there were two approaches:
    - reweighting episodes that overlap a fixed peak period;
    - changing the episode score to count DT saved during the peak period.
  - **Result of §7.4.2:**
    - In the analytical model, "PeakOPT" cut Peak DT by **29%** over vanilla OPT, "However, we could not translate these savings over to simulation."
    - OPT-PeakDT "had a regression with a new, much higher peak appearing in a different part of the trace".
    - The modified Baleen was no better than vanilla.
  - **§7.4.3 future work:** "Extend analytical model to peak… divide trace time into smaller intervals (e.g., 10 minutes) and calculating the Disk-head Time saved per interval from each admitted episode…"
  - **§7.5:** "we were unsuccessful in directly optimizing the peak by modifying the scoring function… a more complex solution would be required." — [CMU-CS-24-152 PDF](http://reports-archive.adm.cs.cmu.edu/anon/2024/CMU-CS-24-152.pdf)
- **CacheSack (Yang et al., USENIX ATC 2022; ACM TOS 2023, "Theory and Experience of Google's Admission Optimization for Datacenter Flash Caches").**
  - It partitions traffic into categories and solves a knapsack (fractional, per the Wong thesis §2 summary) to pick one of 4 admission policies per category.
  - The objective is TCO from disk IO plus flash footprint.
  - Production results: 7.7% TCO, 9.5% fewer disk reads, 17.8% less flash wearout. Deployed in Colossus Flash Cache in May 2021.
  - Its objective is aggregate cost, not min-max over time windows. I did not verify whether the TOS version discusses peak provisioning. — [ATC'22](https://www.usenix.org/conference/atc22/presentation/yang-tzu-wei), [TOS'23](https://dl.acm.org/doi/full/10.1145/3582014), [thesis summary](http://reports-archive.adm.cs.cmu.edu/anon/2024/CMU-CS-24-152.pdf)
- **Lyons, Rangaswami, Xie, "Finding optimal non-datapath caching strategies via network flow"**, Theoretical Computer Science 945 (Feb 2023).
  - It gives an offline optimal admission ("whether to write") policy that trades hit rate against write-erase cycles, solved as network flow.
  - The objective is additive utility, with no peak term. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304397522007678)
- **Cheng et al., "Erasing Belady's Limitations: In Search of Flash Cache Offline Optimality", USENIX ATC 2016** [UNVERIFIED this session]. It covers offline-optimal flash caching with write constraints via min-cost-flow-like formulations, with a hit-ratio and write objective and no peak.
- **Other admission and eviction works** [UNVERIFIED this session, background knowledge]:
  - Flashield (Eisenman et al., NSDI 2019): ML/SVM admission for write endurance.
  - RIPQ (Tang et al., FAST 2015): flash-friendly priority queues.
  - Kangaroo (McAllister et al., SOSP 2021): tiny-object flash cache with probabilistic admission.
  - LRB (Song et al., NSDI 2020): Belady-boundary ML eviction.
  - Raven (Hu et al., CoNEXT 2022): learned eviction.
  - None of these optimizes a min-max-over-time objective. They target hit or byte-miss ratio or write amplification.
- **HALP (Song et al., NSDI 2023, YouTube CDN).** Baleen credits HALP as the only other system that *evaluates* load at peak. By Baleen's classification, it optimizes bandwidth and not peak explicitly. — [Baleen §2 via PDF](https://www.usenix.org/system/files/fast24-wong.pdf)
- **Wong thesis §7.2: indirect peak optimization.** The thesis achieves Peak DT reductions only indirectly, by choosing static parameters (prefetch method, write rate) for policies that optimize mean DT. Baleen-TCO similarly chooses the write rate. — [thesis](http://reports-archive.adm.cs.cmu.edu/anon/2024/CMU-CS-24-152.pdf)

### Inferences
- "First admission policy that explicitly optimizes peak (min-max) load" is **risky as stated**. The Wong thesis already *attempted* explicit peak-aware episode scoring and load-dependent thresholds, and it is public.
- A defensible claim is: "first to **successfully** formulate and solve peak-DT admission as a **global min-max selection over episodes with per-window DT accounting** (the exact approach the thesis lists as future work in §7.4.3), and to show gains survive full simulation."
- The thesis failure mode is directly relevant to PeakBaleen's evaluation. A new peak appeared elsewhere when only a fixed peak window was targeted. A min-max objective over *all* 10-min windows is the natural fix, and it is the argument for QUBO/min-max over reweighting.
- Confidence that **no published paper (non-thesis) optimizes flash-cache admission for min-max peak backend load**: moderately high (~75%). It is lower for "no prior attempt at all" (~0%, because the thesis exists).

### Gaps
- Did not verify whether the CacheSack TOS'23 or MLSys'22 versions contain an explicit peak discussion.
- Did not re-verify the details of Cheng ATC'16 / Flashield / Kangaroo / RIPQ / LRB / Raven this session.

## Q3: Peak-aware and peak-shaving caching, admission or provisioning in CDNs and storage

### Takeaway
Peak reduction via caching is a well-established *motivation* in networking:
- Coded caching minimizes the peak delivery rate.
- CDNs prefetch off-peak.

In those settings, though, "peak" means the worst-case delivery-phase rate or time-of-day shifting of *fills*. It is not a min-max over time windows of backend load with a cumulative write budget. In storage caching, only Baleen and HALP evaluate at peak (per Baleen), and only the Wong thesis attempts to optimize it.

### Cited Findings
- **Maddah-Ali & Niesen, "Fundamental Limits of Caching"**. IEEE Trans. IT 2014; arXiv 1209.5807. The coded-caching framework explicitly minimizes the **peak** delivery rate by placing content in caches during off-peak hours. It is an information-theoretic setting, not admission under a write budget. — [arXiv 1209.5807](https://arxiv.org/pdf/1209.5807)
- **Off-peak prefetching as a CDN and ISP practice.** Content is prefetched in low-load periods so that peaks are served from cache. Examples include vendor docs such as Alibaba Cloud CDN "run prefetch tasks during off-peak hours". — [Alibaba Cloud docs](https://www.alibabacloud.com/help/en/cdn/user-guide/refresh-and-prefetch-resources), [arXiv 1409.1148](https://arxiv.org/pdf/1409.1148)
- **"Prefetching and Caching for Minimizing Service Costs"** (NSF PAR). This work notes that off-peak prefetching lowers cost. It was not examined in detail. — [NSF PAR](https://par.nsf.gov/servlets/purl/10229901)
- **Baleen:** "Almost all systems report averages … bad performance at peak can be covered up by good (but ultimately unhelpful) off-peak performance. To our knowledge, only one other system evaluates load at peak [HALP]." — [Baleen PDF](https://www.usenix.org/system/files/fast24-wong.pdf)
- **Wong thesis:** DT has a peak-to-mean ratio of about 2, and eviction ages are about 2 hours. These imply that admissions pay off within the peak period, which is why write-budget shifting is plausible. — [thesis](http://reports-archive.adm.cs.cmu.edu/anon/2024/CMU-CS-24-152.pdf)
- **"Performance and Cost-Aware Cache Provisioning"**, arXiv 2608.09820 (2026). It covers SLO-driven minimum cache sizing, not peak-window admission. — [arXiv 2608.09820](https://arxiv.org/abs/2608.09820)

### Inferences
- PeakBaleen can frame itself as bringing the coded-caching "peak rate" and CDN "off-peak shifting" intuitions into *storage flash admission*. There, the constrained resource is a cumulative **write budget**, and the objective is the **max over 10-min windows** of HDD DT.
- It should cite:
  - Maddah-Ali & Niesen, for the concept that caching reduces peak rate;
  - HALP, for peak evaluation;
  - Baleen and the Wong thesis, for the peak-DT metric and the prior failed attempts.

### Gaps
- Did not find storage-specific works on time-of-day-aware admission (e.g., Tectonic or Colossus peak discussions). The Tectonic (FAST'21) paper was not checked.
- Queuing-theoretic "tail at scale"-style work concerns latency tails, not provisioning peaks, and was not pursued.

## Q4: Follow-up work citing Baleen (2024-2026) that addresses its peak gap

### Takeaway
I found no published 2024-2026 paper that claims to close Baleen's peak-optimization gap. Enumeration was incomplete because the Semantic Scholar API was rate-limited. The only peak-focused follow-on I found is Wong's own 2024 thesis, Chapter 7 (see Q2).

### Cited Findings
- Search hits that cite or neighbour Baleen are not peak-focused:
  - "Towards Efficient Flash Caches with Emerging NVMe Flexible Data Placement SSDs" (arXiv 2503.11665, 2025), which is about FDP write amplification — [arXiv 2503.11665](https://arxiv.org/pdf/2503.11665)
  - Nemo, a low-write-amplification tiny-object cache (arXiv 2603.09605, 2026) — [arXiv 2603.09605](https://arxiv.org/pdf/2603.09605)
  - "Learning-Augmented Heuristics … Cache Eviction" (arXiv 2608.27975, 2026) — [arXiv 2608.27975](https://arxiv.org/pdf/2608.27975)
  - "Cache is King: Smart Page Eviction with eBPF" (arXiv 2502.02750) — [arXiv 2502.02750](https://arxiv.org/pdf/2502.02750)
  - None of these are peak-aware admission, judging from titles and abstracts.
- The Wong thesis (2024) Ch. 7 is the explicit peak follow-on and reports failure to translate PeakOPT gains into simulation. — [thesis](http://reports-archive.adm.cs.cmu.edu/anon/2024/CMU-CS-24-152.pdf)

### Inferences
- The field appears open for a working peak-aware admission policy. PeakBaleen's positioning should be: "Baleen §3.1 and Wong thesis §7.4 identify peak-optimal admission as open and report failed heuristics. We give the first global min-max formulation (QUBO), solve it with Ising/SB solvers, and distill it into an online model."

### Gaps
- **Action item:** run a manual Google Scholar "Cited by" pass on Baleen (FAST'24) and on the CMU thesis. Filter for "peak", "disk-head time" and "write budget", with particular attention to FAST'25/'26, ATC'25, OSDI'25, EuroSys'26 and HotStorage'25/'26. I could not complete this because of the API rate limit.

## Verdict summary (for the report writer)

| Claim | Holds? | Confidence | Must-cite / caveat |
|---|---|---|---|
| First QUBO/Ising formulation of **budget-constrained flash-cache admission** | Likely yes | ~80% | Must acknowledge QUBO for wireless cache placement (Zhang et al. arXiv 2312.14448 / TNSE 2024), QUBO data allocation (Q-Data'25), and QUBO index selection (Q-Data'24). Do NOT claim "first QUBO for caching". |
| First **min-max peak-optimizing** admission | Only with careful wording | ~75% for "first published successful", ~0% for "first attempt" | Wong CMU thesis 2024 Ch.7 attempted PeakOPT (29% in analytical model, failed in simulation) and load-dependent thresholds (−1.4% peak). Baleen §3.1/§5.6 explicitly defer it. Frame PeakBaleen as realizing the thesis §7.4.3 per-10-min-interval future work with a true min-max objective. |
| First Ising-solver-derived labels distilled into an online ML admission model | Likely yes | ~80% | No hit found for "annealing-derived labels → online cache policy". The closest analogues are OPT-imitation learners (Baleen, LRB, Flashield), which imitate greedy or Belady-style OPT and not a QUBO solution. |
