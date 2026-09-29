# Real-system "wins" for QUBO / Ising / annealing, and what they imply for the PeakBaleen selector slot

Scope note: this complements `REPORT.md`, whose sections already cover the QKP/MILP-vs-Ising benchmarks (Ohno 2024, Akishima 2025, Oshiyama & Ohzeki 2022, Huang et al.), QBSolv/decomposition, the Wong thesis Ch. 7 PeakOPT failure, and CacheSack/HALP/Lyons prior art. Those are not repeated here except as one-line cross-references. Session budget: about 15 web calls. Several abstracts only were read, and they are marked as such.

## Q1. Which published QUBO/Ising applications in systems, networking, scheduling or energy report beating a strong baseline, and on what metric?

### Takeaway
No paper found reports a QUBO/Ising method beating a strong baseline on a *caching or storage* system metric. The credible "wins" fall into three groups. (a) Quadratic-objective, penalty-light problems where D-Wave's hybrid solver beat Gurobi at an equal, short wall-clock budget: production scheduling and BQP. (b) Large time-indexed scheduling QUBOs where Gurobi hit its time limit and Fujitsu's Digital Annealer did not. (c) Wireless physical-layer ML detection, which is natively Ising. Unit commitment, which is closest to peak shaving, is a documented loss to Gurobi at realistic size.

### Cited Findings

**Win table (primary sources read this session unless marked).**

| # | Paper (venue, year) | Problem | Formulation | Solver | Baseline "beaten" | Metric | Size | Code |
|---|---|---|---|---|---|---|---|---|
| W1 | Awasthi, Kraus, Krellner, Zambrano, arXiv:2408.01641 (2024) | Production assignment + scheduling (setup time, load balance, job value) | Pure binary quadratic program (classical side: MI convex program with a few quadratic terms) | D-Wave Leap Hybrid (BQM) | Gurobi, 3 h limit, 8-core Xeon 8124M | Objective value at equal runtime; time to quality | 2,012–151,556 binaries; 27–160 jobs; 8–20 machines | None given |
| W2 | Leib et al., *Sci. Rep.* 13 (2023), doi:10.1038/s41598-023-45668-1 | Lab transport-robot scheduling (sum of completion times) | Time-indexed x_{j,m,t} with **7 penalty terms**, weights tuned on smaller instances | Fujitsu Digital Annealer (FDA; FDAh hybrid for >8,192 vars); D-Wave LBQM | Gurobi 3,600 s, both a sequence MIP and a time-indexed MIP | Objective; end-to-end runtime incl. network latency | 260 instances; 2,071–22,692 vars | "Upon reasonable request" |
| W3 | Quinton et al. (NTNU), arXiv:2409.05542v2 (2024) | Generic BQP (a win) **and** unit commitment (a loss; see Q2) | Hybrid CQM | D-Wave LeapHybridCQM | CPLEX, IPOPT | Objective | BQP up to 500 vars with quadratic constraints | "Upon request" |
| W4 | Kim, Venturelli, Jamieson, "QuAMax", ACM SIGCOMM 2019 (arXiv:2001.04014) | Large-MIMO ML detection in C-RAN | ML detection is natively Ising (BPSK/QPSK map to spins) | D-Wave 2000Q (2,031 qubits) | [UNVERIFIED which baseline; the thesis compares against linear detectors and sphere decoding] | BER / frame error rate on real and synthetic channel traces | 48 users × 48 AP antennas, BPSK | None verified |
| W5 | Liu & Sabek (USC), arXiv:2601.12123 (2026); Q2O demo, PVLDB 18 | Join ordering (a DB systems problem) | QUBO/nonlinear model | D-Wave NL-Solver (hybrid) | PostgreSQL 16.4 default optimizer (**not** a strong offline baseline) | Query execution time | JOB, 113 queries | Not provided |
| W6 | Nikmehr, Zhang, Bragin, IEEE TPWRS 37(5) 2022, doi:10.1109/TPWRS.2022.3141794 (abstract only) | Microgrid unit commitment | Quantum UC subproblems coordinated by ADMM | Quantum (QAOA/annealing; [UNVERIFIED which]) | "Classical counterpart" ADMM | Validates efficacy; no win margin read | Microgrid scale [UNVERIFIED] | — |
| W7 | Hong, Xu, Teng, arXiv:2502.15917 (2025/26, "submitted to IEEE"; abstract only) | Stochastic UC | Benders; master problem as QUBO; PHR augmented Lagrangian removes slack qubits; quantum ADMM blocks by generator | D-Wave QPU | "Classical and baseline quantum approaches" [margins UNVERIFIED] | Qubit count, runtime, feasibility | 4-gen and IEEE 118-bus | Not given |

Supporting detail for each row:
- W1: D-Wave gave a "1.5 to 2x speedup". At identical runtime, Gurobi's solution was up to ">17.5%" worse. D-Wave's worst solution was within "2.6%" of Gurobi's final (3 h) value after 45 min. The authors state it "is not known if [the advantage] is due to utilizing quantum computing", because the hybrid solver is a black box — [arXiv:2408.01641](https://arxiv.org/html/2408.01641v1)
- W2: On the 161 "minor" instances, Gurobi was statistically significantly better (p<0.01) than FDA and LBQM, although FDA "finds a comparable solution almost always faster". On the 99 "major" instances, FDAh "shows an advantage on some bigger instances … on a similar time scale". Its runtime stayed about 120–300 s while Gurobi's grew exponentially and hit the limit. D-Wave LBQM underperformed throughout and returned infeasible solutions. The comparison excludes tailor-made metaheuristics — [Leib et al., Sci. Rep. 2023 (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10618446/)
- W3: On pure BQP, the D-Wave hybrid "outperforms CPLEX by ~25% solution quality" in less time. The authors conclude the hybrid solver "is currently most advantageous for integer quadratic objective functions" — [arXiv:2409.05542v2](https://arxiv.org/html/2409.05542v2)
- W4: About tens of µs of 2000Q compute supported 48×48 BPSK at 20 dB SNR, with BER 10^-6 and a 1,500-byte frame error rate of 10^-4 — [QuAMax arXiv:2001.04014](https://arxiv.org/pdf/2001.04014); [Princeton PAWS QA-for-wireless page](https://paws.princeton.edu/qa-wireless)
- W5: 31 of 113 queries sped up, with a maximum execution-time reduction of 92.7% and a mean of 42.09% on the improved queries. The E2E gain was only 1.25–1.42×, because NL-Solver latency is 2.5–2.9 s per query — [arXiv:2601.12123](https://arxiv.org/html/2601.12123)
- W6: The paper proposes a quantum UC model plus quantum ADMM, and compares against the classical counterpart "validating the efficacy" — [IEEE Xplore 9677977](https://ieeexplore.ieee.org/document/9677977/); [OSTI 1890216](https://www.osti.gov/pages/biblio/1890216)
- W7: The paper claims "superior qubit and runtime efficiency" on the 118-bus system, but no numbers were visible in the abstract — [arXiv:2502.15917](https://arxiv.org/abs/2502.15917)

**Caching, storage and data placement (closest to our slot): no wins on a real system metric found.**
- Zhang et al. use a hybrid quantum-classical generalized Benders decomposition, in which a quantum annealer solves the master problem, for joint cache placement and power allocation in satellite-terrestrial networks. The metric is network throughput, and the evaluation is model-based, not trace-driven. The abstract gives no baselines or margins — [arXiv:2312.14448](https://arxiv.org/abs/2312.14448)
- Do, Trieu & Nguyen decompose edge-server placement and workload allocation (a MILP) into a QUBO (binary placement) plus an LP (continuous allocation). The abstract gives no baselines or margins — [arXiv:2306.01159](https://arxiv.org/abs/2306.01159)
- Q-Data@SIGMOD'25 has a talk on "Leveraging Quantum Computing for Optimal Data Allocation in Distributed Systems" (storage and k-safety constraints) and a paper on QUBO transaction scheduling. We found no quantitative wins against a strong baseline — [dblp Q-Data 2025](https://dblp.org/db/conf/q-data/q-data2025.html); [ACM 10.1145/3736393.3736692](https://dl.acm.org/doi/10.1145/3736393.3736692)
- VM placement: a search for QUBO/annealing VM placement returned only survey or tutorial mentions (e.g., the QCE'24 database QA tutorial). We found no primary paper with a win over First-Fit-Decreasing or MILP — [QCE'24 tutorial arXiv:2411.04638](https://arxiv.org/html/2411.04638)
- Household demand response and peak-to-average scheduling: QUBO/QA papers exist, e.g., hierarchical QA-MPC for household energy scheduling with hydrogen storage, [arXiv:2603.07823](https://arxiv.org/pdf/2603.07823), and a QUBO microgrid scheduling chapter validated on qbsolv, [Springer 2024](https://link.springer.com/chapter/10.1007/978-981-96-0897-3_48). Neither was read in full, so baseline strength and margins are [UNVERIFIED].

### Inferences
- Every "win" above is either (i) wall-clock-bounded quality against Gurobi, where Gurobi eventually matches or beats it (W1, W2), (ii) a natively Ising problem (W4), or (iii) against a weak online default rather than an offline optimum (W5). None is "better final objective than a well-tuned MILP/LP given comparable time on a linear, few-constraint problem", which is our case.
- In W1 and W2 the black-box hybrid solvers do most of the work classically, so a "win" cannot be credited to annealing per se. That argues for our H2 using transparent solvers (SB/SA on identical Q) rather than a cloud hybrid.

### Gaps
- We found no primary source applying QUBO to CDN/edge caching or flash admission with trace-driven simulation. We found none for VM placement with a quantitative comparison against a strong heuristic.
- W4's exact baseline set and margins, W6/W7 margins and the demand-response papers' baselines were not read in full.
- No public code repository was found for any of W1–W7. Every paper that states availability says "upon request".

## Q2. Common success factors versus failure modes

### Takeaway
Wins come from quadratic, dense objectives with few or soft constraints, from large time-indexed models where the MIP baseline is time-limited, and from comparing at a short fixed budget. Losses come from linear/MILP structure with many hard constraints, from penalty-encoded feasibility, and from the realistic-size unit commitment problem, the closest analogue to peak shaving.

### Cited Findings
- **Unit commitment is a loss at scale.** On the full RTS-GMLC UC (44,544 vars, 42,899 constraints), the D-Wave hybrid's best feasible objective was 5.7×10^6, against Gurobi's 1.23×10^6 (optimal to a 0.05% gap in 180 s). It needed 400 s+ of manual tuning. On Reduced-1 (11,136 vars) it was about 10× off optimal. On Reduced-2 (1,418 vars) it was 2.4% off in 5 s, against Gurobi's <1 s. With more than 5 linear constraints, BLP quality diverged, and runtimes exceeded 600 s — [Quinton et al., arXiv:2409.05542v2](https://arxiv.org/html/2409.05542v2)
- **Quadratic-objective structure is the success factor.** The same study finds its only clear win on BQP (~25% better than CPLEX) — [arXiv:2409.05542v2](https://arxiv.org/html/2409.05542v2)
- **Penalty tuning and feasibility.** Leib et al. needed 7 penalty terms with weights from pre-studies. D-Wave LBQM returned infeasible solutions — [Leib et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10618446/). REPORT.md already covers the Akishima 2025 finding that the penalty QUBO solved only 35 of 60 QKP instances.
- **Instance size and timing asymmetry.** The FDA advantage appeared only on the "major" instances, where Gurobi hit its 3,600 s cap. On small instances Gurobi won significantly — [Leib et al. 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10618446/). W1 compares at equal runtime, but the gap nearly closes given Gurobi's full 3 h — [arXiv:2408.01641](https://arxiv.org/html/2408.01641v1)
- **Uncounted overheads.** Q2O's 2.5–2.9 s solver latency cut a 13.15× execution speedup to 1.25–1.42× E2E — [arXiv:2601.12123](https://arxiv.org/html/2601.12123). Leib et al. is one of the few studies that explicitly counts network latency — [Leib et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC10618446/)
- **Decomposition as the enabling trick in power-systems QUBOs.** Benders or ADMM keeps the continuous and linear parts classical and sends only small binary masters to the annealer — [Nikmehr et al. TPWRS 2022](https://ieeexplore.ieee.org/document/9677977/); [Hong et al. arXiv:2502.15917](https://arxiv.org/abs/2502.15917); [Do et al. arXiv:2306.01159](https://arxiv.org/abs/2306.01159)
- **Weak or opaque baselines.** Q2O's baseline is PostgreSQL's default optimizer — [arXiv:2601.12123](https://arxiv.org/html/2601.12123). W1's authors cannot attribute the gain to quantum resources — [arXiv:2408.01641](https://arxiv.org/html/2408.01641v1)

### Inferences
- Our problem is a min-max (epigraph) over about 1,000–1,500 windows plus one budget knapsack row, with a linear objective. It resembles UC (the documented loss) far more than BQP (the documented win). Expect Ising to be competitive only if (a) we make the objective genuinely quadratic, e.g. a smooth surrogate Σ_w L_w² or a top-k/CVaR proxy over window loads, which is dense quadratic in x through co-windowed episodes, and (b) the budget is handled by a Lagrange multiplier or repair, not a slack-bit penalty.
- A fair "win" claim for a QUBO selector in H2 must fix the wall-clock budget and hardware, and must report the Gurobi/HiGHS value at both the same budget and convergence. The W1/W2 pattern suggests that the only defensible positive result is "comparable quality at a lower or fixed time".

### Gaps
- No source quantifies how much classical preprocessing (embedding, decomposition, repair) contributes to reported hybrid wins.
- No source reports QUBO results on a min-max, peak-load objective with realistic window counts.

## Q3. How to wire an Ising/QUBO selector into the Baleen slot, and what evaluation gives it a fair chance to beat Baleen in simulation

### Takeaway
The QUBO is not the hard part. The analytic-to-simulation gap is: Baleen's own paper says episode-model numbers "will differ from simulated ones", and Wong's PeakOPT died on exactly that gap. A QUBO selector has a fair chance only if (1) its objective is robust to peak migration (all windows or top-k/CVaR, not one fixed window), (2) its ordering stays sensible *beyond* the selected prefix, because the frozen `converge.py` re-moves the cutoff, and (3) its analytic per-window loads are validated against simulator per-window DT before any claim is made.

### Cited Findings (from Baleen's own text; the harness facts come from SCOPE.md)
- The episode model enforces cache size "only as a long-term average". Offline numbers "will differ from simulated ones as the cache size constraint is not enforced all the time" — [Baleen FAST'24 §3](https://www.usenix.org/system/files/fast24-wong.pdf) (local copy `documents/Baleen_FAST24_Wong.pdf`)
- Decisions are independent only under a *constant* eviction age. "In reality, the eviction age is not constant and varies with cache usage over time". Baleen is "not sensitive to the assumed eviction age (typically 2+ hours)" end to end — [Baleen FAST'24](https://www.usenix.org/system/files/fast24-wong.pdf)
- Baleen converges the eviction age and the admission threshold in nested loops against the online simulator. The inner loop "aims to offset the small differences between offline analysis and a higher-fidelity online simulation". Peak DT is one of the metrics that "cannot be obtained from offline episode analysis" — [Baleen FAST'24](https://www.usenix.org/system/files/fast24-wong.pdf)
- LRB's relaxed Belady and Baleen's OPT both prune the decision space. Baleen's OPT is scored by DT/size and "decides at a higher granularity" of disjoint episodes (Suppl. A.7) — [Baleen FAST'24](https://www.usenix.org/system/files/fast24-wong.pdf)
- Wong thesis §7.4.2: the fixed-window PeakOPT cut peak by 29% analytically, and a new, higher peak then appeared elsewhere in simulation (details in REPORT.md) — [CMU-CS-24-152](http://reports-archive.adm.cs.cmu.edu/anon/2024/CMU-CS-24-152.pdf)

### Inferences (design recommendations; not from a source)
1. **Formulation inside the slot.** Compute d(e,w), the DT saved by episode e in window w, from each episode's access timestamps × per-access DT saved, excluding the first (miss) access. Compute the baseline per-window load L0_w from the episode data, taken as the no-admission DT. Load L_w(x) = L0_w − Σ_e d(e,w)x_e. The objective should be all-window: min t subject to L_w(x) ≤ t for all w, or a quadratic surrogate. The QUBO-native candidate is Σ_w (L_w(x))² or a softmax/CVaR over windows. The squared form is quadratic in x through co-windowed pairs, which is the structure where Ising solvers win (Q2). The budget Σ c_e x_e ≤ W goes in via a Lagrange multiplier λ, bisected until the prefix hits W, followed by a greedy repair. Avoid slack-bit penalties.
2. **Scale.** Pre-fix variables. Episodes with d(e,·) = 0 in every top-K candidate window, or with a very high DT/byte ratio, go to Baleen's greedy order, fixed in or out by LP reduced cost. This keeps the QUBO to about 10^4 free variables, the dense-SB envelope in REPORT.md.
3. **Ordering beyond the prefix matters.** `converge.py` re-converges the threshold to 35.599 MB/s ±1% in simulation, so the simulated cutoff will not land exactly at the analytic W. Emit a *nested* ordering by solving at W·(1−δ), W, W·(1+δ) (e.g., δ = 5–10%) and concatenating the differences, rather than appending Baleen's order immediately after the W-set. Otherwise the re-converged cutoff admits peak-blind episodes.
4. **Capacity coupling.** Admitting a different set changes occupancy, and so changes the eviction age and whether an episode's later accesses actually hit. Two mitigations are possible in-slot: (a) add a soft per-window occupancy constraint Σ_e size_e·[e resident in w]·x_e ≤ C (a Little's-law window version of Baleen's average constraint), and (b) prefer selections whose occupancy profile matches Baleen's, to keep the converged eviction age valid.
5. **Prefetch interaction.** In `--ap opt` mode the frozen ML prefetchers still run. The chunks they fetch count toward writes and DT, so the selector's d(e,w) omits prefetch-induced DT. Measure the per-window residual between analytic and simulated L_w as a diagnostic.
6. **Evaluation protocol for a fair chance.**
   - **Gate 0 (analytic-to-sim fidelity):** for Baleen's own selection, correlate analytic L_w with the simulator's per-window DT on sample 0. Report the rank correlation and the top-10-window overlap. If fidelity is poor for Baleen itself, no selector can be expected to transfer its peak gain.
   - **Gate 1 (offline, `--ap opt`):** P100 and also P99 and top-5-window mean of 10-min windows after day 1, at the matched, re-converged write rate. Report the argmax window's location for both methods; the Wong failure mode is argmax migration. Report mean DT too, so any peak gain is weighed against total DT.
   - **Iterative re-weighting (the peak-migration fix):** after simulating selection k, take the simulator's worst windows. Up-weight them in the objective (multiplicative weights over windows, i.e. an online min-max / Lagrangian dual update) and re-solve. This uses the simulator only as an evaluator inside the training day, the same way Baleen's own convergence loop already does for EA and threshold. It stays within the frozen boundary if the loop lives in our entry module. **[Needs team check that this counts as "policy" rather than "modifying training"].**
   - **Splits:** tune any λ, δ, K or re-weight schedule on day 1 of sample 0 only, and report samples 0–9, per the SCOPE.md airblock on held-out data.
   - **H2 solver fairness:** same Q, same repair, same wall-clock budget. Report LP/MILP at equal time and at convergence (Q2 inference).
   - **Gate 2 (`--ap mlnew`):** expect most of the gain to be lost (REPORT.md H3 section).

### Gaps
- No published caching work reports per-window validation of an offline selection against a simulator for a *peak* metric. Baleen validates aggregate metrics and says outright that Peak DT is simulation-only. Wong's thesis is the only such attempt, and it failed.
- Whether the iterative simulator-in-the-loop re-weighting is admissible under SCOPE.md §3 ("Training driver: frozen") needs a team decision.

## Q4. Caching papers that validated offline-optimal selections in a simulator and discussed the analytic-to-simulation gap

### Takeaway
Baleen is the clearest primary source. It names the gap (cache size enforced only on average; eviction age varies) and closes it for aggregate metrics with a nested convergence loop against the simulator, not in the optimizer. Wong's thesis shows that the loop does not close the gap for a peak objective. LRB and CacheSack were not re-read this session.

### Cited Findings
- Baleen: OPT is an "online simulation that approximates the optimal AP using offline information from the entire trace". Admitted episodes are marked offline and replayed. The threshold loop compensates for offline/online differences. Baleen also calls itself "the only online policy that approximates the optimal flash admission policy, and which can easily optimize an arbitrary metric like DT" — [Baleen FAST'24](https://www.usenix.org/system/files/fast24-wong.pdf)
- Baleen, related work: Relaxed Belady (LRB) prunes by the Belady boundary. Container-optimized MIN [11] extended Belady to admission for erasures "but did not provide an online algorithm" — [Baleen FAST'24](https://www.usenix.org/system/files/fast24-wong.pdf)

### Inferences
- The gap is structural. The episode model decouples decisions via a constant eviction age, and a peak-aware selector deliberately concentrates admissions in time, which is precisely what breaks that assumption locally. Temporally concentrated admission raises local occupancy, shortens the local eviction age and cancels planned hits. This is a plausible mechanism for Wong's peak migration. It should be tested with Gate 0 plus a per-window "planned hit vs realized hit" audit.

### Gaps
- We did not verify whether LRB (NSDI'20), CacheSack (ATC'22), Flashield (NSDI'19) or Kangaroo discuss offline-versus-simulated discrepancies for their oracle labels (not fetched this session; [UNVERIFIED]).
