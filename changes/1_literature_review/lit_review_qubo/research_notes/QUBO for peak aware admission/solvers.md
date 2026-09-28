# Ising/QUBO Solvers on a Single Workstation (16-core CPU, 1x 24 GB GPU): Scale, Quality, Competitiveness

Scope note: researched 2026-09-27. Several primary Science Advances pages returned HTTP 403 to the fetcher, so some SB numbers come from Toshiba press material or secondary summaries and are flagged. Items marked **[UNVERIFIED]** come from background knowledge and were not confirmed by a source fetched this session.

## Q1. Simulated bifurcation (SB): variants, reported scale, time-to-solution; the open-source `simulated-bifurcation` package

### Takeaway
SB (Goto/Tatsumura/Dixon 2019; ballistic and discrete SB in Goto et al. 2021) is the strongest *published* GPU-parallel Ising heuristic for large all-to-all (dense) unconstrained problems. The reported scale runs up to about 10^6 spins on a 16-GPU machine. The open-source `simulated-bifurcation` PyTorch package (v2.0.0, April 2025, MIT) is the practical way to run it on one 24 GB GPU. It handles spin, binary (QUBO) and integer domains but has **no native constraint support**, so constraints must go in as penalties.

### Cited Findings
- Goto, Tatsumura & Dixon, "Combinatorial optimization by simulating adiabatic bifurcations in nonlinear Hamiltonian systems," *Science Advances* 2019 (DOI 10.1126/sciadv.aav2372). The paper built an all-to-all 2000-spin SB machine on a single FPGA, reported as about 10x faster than a state-of-the-art coherent Ising machine. It also solved an all-to-all **100,000-node MAX-CUT with continuous weights** on a GPU cluster, about 10x faster than the authors' fastest simulated annealing. — [ResearchGate record of the paper](https://www.researchgate.net/publication/332535366_Combinatorial_optimization_by_simulating_adiabatic_bifurcations_in_nonlinear_Hamiltonian_systems) (via search summary; the science.org page returned 403)
- Goto, Endo, Suzuki, Sakai, Kanao, Hamakawa, … Tatsumura, "High-performance combinatorial optimization based on classical mechanics," *Science Advances* 7(6) eabe7953 (2021). This paper introduced **ballistic SB (bSB)** and **discrete SB (dSB)** and claims high speed and accuracy "for problems with up to one million binary variables." — [Science Advances](https://www.science.org/doi/10.1126/sciadv.abe7953); [Semantic Scholar](https://www.semanticscholar.org/paper/High-performance-combinatorial-optimization-based-Goto-Endo/bfe8e49dff8fd46b56678c0c531e9cb406af8ab5)
- On a **16-GPU machine**, dSB solved a **1,000,000-bit problem** to a "nearly optimal" solution in **30 minutes**. Toshiba says this is 20,000x faster than CPU simulated annealing, which it projects would take 14 months. Toshiba recommends bSB for immediate-response use and dSB for accuracy. — [Toshiba press release](https://asia.toshiba.com/press-release/english/toshibas-new-algorithms-quickly-deliver-highly-accurate-solutions-to-complex-problems/) (vendor source; the 14-month SA figure is an extrapolation, not a measurement)
- Variant semantics: bSB uses particle *positions* in the matrix-vector product (usually faster, less accurate). dSB uses the *sign* of positions (usually slower, more accurate). — [bqth29 GitHub README](https://github.com/bqth29/simulated-bifurcation-algorithm)
- Kanao & Goto, "Simulated bifurcation assisted by thermal fluctuation" (heated SB, HbSB/HdSB), arXiv:2203.08361. — [arXiv](https://arxiv.org/pdf/2203.08361)
- Kanao & Goto also extended SB to higher-order (PUBO) cost functions in "Simulated bifurcation for higher-order cost functions." — [arXiv:2211.09296](https://arxiv.org/pdf/2211.09296)
- **Package `simulated-bifurcation` (PyPI):**
  - Current version **2.0.0**, released **2025-04-10**, MIT license, Python ≥3.8, depends on PyTorch.
  - Domains: Ising/spin, binary (QUBO), integer (X-bit encoded, e.g. `domain='int3'`), plus helper models (Markowitz, number partitioning, graph cuts).
  - API: `sb.minimize` / `sb.maximize` / `sb.build_model` (tensors or SymPy polynomials) and `set_env` / `reset_env` for hyperparameters.
  - Options: multi-agent search (`agents`; the docs say one run with N agents beats N separate runs), `device='cuda'`, `dtype`, `max_steps`, `best_only`, `mode='ballistic'|'discrete'`, `heated=True`, and early stopping (`early_stopping`, `sampling_period`, `convergence_threshold`).
  - Source: [PyPI](https://pypi.org/project/simulated-bifurcation/); [GitHub](https://github.com/bqth29/simulated-bifurcation-algorithm); [docs v2.0.0](https://simulated-bifurcation-algorithm.readthedocs.io/en/v2.0.0/)
- Maintenance: the GitHub repo has about 168 stars, 35 forks and 598 commits on main. It mentions no constraint handling and documents no memory or size limits. The README claims a "median optimality gap of less than 1%" on its test instances; the instance set is not specified in what we fetched. — [GitHub](https://github.com/bqth29/simulated-bifurcation-algorithm)
- Toshiba's commercial SB product, **SQBM+ v2** (Nov 2023), supports **up to 10 million variables** on AWS GPU instances (p4d/p3/g4dn). Toshiba says it found best-known values on **60 of 71** G-set MAX-CUT instances, up from 50 in v1. It adds a PUBO solver and problem-specific TSP, shift-scheduling and QAP solvers. — [Toshiba news 2023-11-27](https://www.global.toshiba/ww/news/digitalsolution/2023/11/news-20231127-01.html)
- Applied result: on modularity (community detection) QUBOs, SB on a single GPU achieved the highest modularity among the tested methods. It matched Fujitsu's Digital Annealer and beat D-Wave, IBM hardware and **Gurobi**. — [SSRN, Li et al.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5496392) (search-snippet level; Gurobi's time limit not checked)

### Inferences
- **Memory is the binding limit on a 24 GB GPU for dense QUBOs.** SB keeps the full coupling matrix J (n×n) in memory, and each step is a dense GEMM of J with the agents' state (arithmetic, not from a source):
  - n=10^4 in fp32 needs 0.4 GB (trivial).
  - n=5×10^4 in fp32 needs about 10 GB (fits).
  - n=10^5 in fp32 needs about 40 GB (**does not fit**). In fp16/bf16 it needs about 20 GB, which fits only barely, leaves little room for agents, and loses precision on penalty-scaled coefficients.
  - The package API takes dense tensors; we found no sparse-matrix path. **[UNVERIFIED]**: we did not confirm whether torch sparse tensors are accepted.
  - So dense 10^5 on one 24 GB card needs either sparsity or decomposition.
- Published SB scale claims (10^5–10^6 spins) used GPU clusters or 16-GPU nodes, mostly on **unconstrained** MAX-CUT/SK instances. They do not carry over directly to constrained QUBOs with penalty terms.

### Gaps
- Exact published time-to-solution numbers for the 2019 FPGA (2000 spins) and GPU-cluster (100k) runs could not be fetched (science.org 403). From memory, the 2019 paper reports about 0.5 ms for the 2000-spin FPGA run. **[UNVERIFIED]**
- We found no independent benchmark of the bqth29 package at 10^4–10^5 variables on a single GPU.

## Q2. Simulated annealing / parallel tempering on CPU: dwave-samplers (ex-neal), dimod, PyQUBO, OpenJij

### Takeaway
For CPU-only baselines, use **dwave-samplers 1.8.0** (SA, Tabu, steepest descent, SQA; C++ core) with dimod BQMs, or **OpenJij 0.12.2** (SA/SQA). Both are maintained in 2026. OpenJij **dropped GPU support in Aug 2023**, so the only well-maintained open-source GPU QUBO heuristic is the SB package.

### Cited Findings
- **dwave-samplers 1.8.0** was released **2026-06-18**, Apache-2.0, Python ≥3.10 (wheels for 3.10–3.14, free-threaded 3.14), x86-64 and ARM64. — [PyPI](https://pypi.org/project/dwave-samplers/)
  - Exact samplers: Planar (Ising on planar graphs) and TreeDecomposition (low treewidth).
  - Heuristic samplers: SimulatedAnnealing, SimulatedQuantumAnnealing, SteepestDescent, Tabu.
  - Baseline: Random.
- **OpenJij 0.12.2** was released **2026-08-19**, Apache-2.0, Python 3.10–3.14, by Jij Inc. It provides SASampler, SQASampler and CSQASampler. **"GPGPU algorithm support was discontinued as of August 2023."** — [PyPI](https://pypi.org/project/openjij/)
- On randomly generated inputs, D-Wave's QPU as a heuristic "can be outperformed by simulated thermal annealing." The authors (Jünger et al., ACM JEA 26, 2021) used tailored branch-and-cut/SDP with Gurobi 9.0 to prove optimality on Chimera Ising instances. — [ACM JEA](https://dl.acm.org/doi/abs/10.1145/3459606)
- In Ohno et al. on the quadratic knapsack problem (QKP), **raw** Ising-machine outputs were "completely inferior to the greedy method" without post-processing. — [arXiv:2403.19175](https://arxiv.org/html/2403.19175v1)

### Inferences
- The following are **[UNVERIFIED]** background knowledge:
  - `dwave-neal` has been superseded: `neal` is now a thin wrapper around `dwave-samplers`.
  - `dimod` is the BQM/CQM data layer, and `dimod.ConstrainedQuadraticModel` plus `cqm_to_bqm` handles automatic penalty and slack conversion.
  - PyQUBO (Recruit) compiles symbolic expressions and constraints with `Placeholder` penalty weights into BQMs. Its release activity has slowed; latest is 1.4.x, roughly 2023.
- Single-flip SA on a **dense** QUBO costs O(n) per flip to update local fields, so one sweep is O(n^2). At n=10^5 that is about 10^10 operations per sweep, which means seconds to tens of seconds per sweep per core even in C++. Sparse QUBOs with degree d cost O(n·d) per sweep. So CPU SA/Tabu is realistic for dense n ≲ 10^4 or for sparse n up to 10^5–10^6. Dense 10^5 is the regime where GPU SB is actually needed.
- The 16 cores are best used for independent restarts (`num_reads`) or parallel tempering replicas.

### Gaps
- We did not verify current PyPI versions for dimod or PyQUBO, or whether PyQUBO is still maintained.
- We found no rigorous published single-workstation benchmark of dwave-samplers SA vs SB at 10^4–10^5 dense variables.

## Q3. Commercial/hardware Ising machines: reported scales (context only)

### Takeaway
Vendors report 10^4 to 10^7 variables, but only on their own hardware or cloud. Independent benchmarks show that **no single machine dominates**: the winner depends on problem structure.

### Cited Findings
- **Toshiba SQBM+** v2 (SB on GPUs) handles up to **10M variables**. — [Toshiba](https://www.global.toshiba/ww/news/digitalsolution/2023/11/news-20231127-01.html)
- **Fujitsu Digital Annealer**: the ASIC hardware is reported as limited to **8,192** variables. A research paper cites DA supporting "beyond an equivalent of 10,000 logical variables," presumably via software decomposition. — Search summary citing [Medium benchmark post](https://medium.com/@jy_farhani/benchmarking-quantum-digital-annealers-3ecd5e7816a5) (secondary/blog; low confidence)
- Oshiyama & Ohzeki (*Sci. Rep.* 2022) compared D-Wave Hybrid Solver Service, Toshiba SBM, Fujitsu DA and SA:
  - D-Wave HSS ranked first on MQLib real-world instances.
  - DA ranked first on NAE-3SAT at the phase transition.
  - SBM ranked first on the SK spin glass.
  - Conclusion: no single solver dominates. — [arXiv:2104.14096](https://arxiv.org/abs/2104.14096)
- Huang et al. (2022) benchmarked the D-Wave QA and the Fujitsu DA on three combinatorial problems. "Both annealers are effective on problems with small size and simple settings, but lose their utility when facing problems in practical size and settings." Decomposition extends scale but is "still far away from practical use." — [arXiv:2203.02325](https://arxiv.org/abs/2203.02325)
- Safi et al. (2026, industrial job-shop scheduling) compared IBM QC, D-Wave, Fujitsu DA and exact/MILP. They frame quantum and quantum-inspired methods as aids for solver selection and proof-of-concept work, not replacements, and stress that hardware-software co-design is essential. — [arXiv:2607.13325](https://arxiv.org/abs/2607.13325) (abstract only; no numbers extracted)
- Mohseni, McMahon & Byrnes, "Ising machines as hardware solvers of combinatorial optimization problems," *Nat. Rev. Phys.* 2022. It reviews metrics (ground-state probability, time-to-solution) and notes that the open question is whether Ising machines keep an advantage over digital computers as problems scale. — [arXiv:2204.00276](https://arxiv.org/abs/2204.00276)
- Hitachi CMOS annealer: no source was found in this session. **[UNVERIFIED]**: around 100k spins on King's-graph (sparse, nearest-neighbour) connectivity.

### Inferences
- The reported 10^6–10^7 figures are mostly for unconstrained, and often sparse or MAX-CUT, instances. None of these vendor numbers applies to a constrained QUBO on one 24 GB GPU.

### Gaps
- There are no primary Fujitsu or Hitachi spec sheets in these notes. D-Wave hybrid (Leap) CQM/BQM size limits (**[UNVERIFIED]**: around 1M variables for BQM, about 500k for CQM) were not confirmed. None of these are usable on-prem without a cloud account anyway.

## Q4. Weaknesses on constrained problems: penalties, feasibility, knapsack-type constraints

### Takeaway
This is the central weakness. A single penalty weight λ must be large enough to make solutions feasible but small enough not to flatten the objective landscape. Inequality (knapsack) constraints also need slack variables that enlarge the problem. From a feasible QUBO state, single flips immediately violate an equality or tight inequality, which blocks local search. On QKP, raw penalty QUBO outputs lose to plain greedy. Getting competitive results requires **post-processing (repair plus local improvement)** or native constraint handling.

### Cited Findings
- Ohno, Shirai & Togawa (Waseda/NTT, 2024), QKP with n = 100–300 and n = 1000–2000, using the Fixstars Amplify Annealing Engine on an A100 and a time budget of 0.01·n s:
  - The key difficulty is the penalty trade-off: a large λ is needed for feasibility, but "large λ typically degrades the objective value."
  - Raw outputs were "completely inferior to the greedy method."
  - With their repair + improvement post-processing (AE-RI), they obtained about 82% optimal solutions on medium instances.
  - On 80 large instances, AE-RI reached 62 best-known solutions (77.5%) at a mean gap of 0.172%. Gurobi (60 s limit) reached 57 best-known at a mean gap of **0.075%**, and GRASP+Tabu reached **75** best-known at 0.121%.
  - So even post-processed, the Ising approach found more best-known solutions than Gurobi but had a worse average gap than both Gurobi and the specialised heuristic.
  - [arXiv:2403.19175](https://arxiv.org/html/2403.19175v1)
- Akishima, Tamura & Kudo (2025), QKP with 100–300 items and 25–100% density, using Fujitsu's Extended Ising Machine (EIM) simulator on an i7-13700:
  - The **penalty QUBO formulation solved only 35 of 60** larger (200–300 item) instances.
  - EIM, which handles inequality constraints natively through real-valued dependent variables and no slack bits, reached optimum on all 100, with times comparable to or faster than Gurobi.
  - They attribute the QUBO failure to the fact that "flipping any variable from a feasible solution results in an immediate constraint violation."
  - [arXiv:2508.06909](https://arxiv.org/html/2508.06909)
- Studies of constraint encodings (slack binary/unary/log encodings) for annealers and digital solvers compare how encoding choice affects solver performance. — [Sci. Rep. 2023, "On good encodings for quantum annealer and digital optimization solvers"](https://www.nature.com/articles/s41598-023-32232-0) (paywall redirect; content not verified)
- Cardinality-constrained QKP (one inequality plus one equality) has been benchmarked with D-Wave, SA and Gurobi 9.5. — [InspireHEP PDF](https://inspirehep.net/files/6dc97dfdba01eae229daa641fac62284) (search snippet only)

### Inferences
- For a constrained admission-type QUBO (knapsack-like capacity/peak constraints), expect the following:
  1. Tuning λ per instance family.
  2. Slack variables adding about log2(capacity) bits per inequality.
  3. Low raw feasibility at objective-friendly λ.
  4. A mandatory greedy repair step (drop the worst-ratio items until feasible, then greedy fill).
- With many constraints (multidimensional knapsack, makespan, max-min objectives with auxiliary variables), each extra constraint adds a penalty term with its own scale. The literature above covers one constraint and already shows the difficulty, so multi-constraint cases are presumably worse (inference, not directly measured).
- Squaring penalty terms makes the QUBO **dense** even when the objective is sparse: (Σ w_i x_i − C)^2 couples all items in the constraint. This interacts badly with the Q1 memory limit.

### Gaps
- We found no peer-reviewed study specifically measuring feasibility rates of the bqth29 SB package on penalty QUBOs.
- We found no study for multidimensional knapsack at 10^4+ variables comparing Ising heuristics with Gurobi or CP-SAT.

## Q5. Head-to-head: Ising heuristics vs Gurobi / CP-SAT / HiGHS / greedy

### Takeaway
On **unconstrained, dense, MAX-CUT/SK-like** problems at 10^4–10^6 variables, GPU SB is genuinely competitive with or better than MIP solvers within a fixed time. MIP solvers cannot prove optimality there and SB scales well. On **constrained knapsack/scheduling-type** problems, the evidence says Ising heuristics are **not** competitive out of the box. Raw outputs lose to greedy. They become roughly comparable to Gurobi only with problem-specific repair post-processing (QKP, n ≤ 2000) or native constraint support (Fujitsu EIM), and Gurobi still had the best average gap in Ohno et al.

### Cited Findings
- QKP n=1000–2000: Gurobi 60 s gave a mean gap of 0.075%, versus 0.172% for the Ising machine with repair and 0.121% for GRASP+Tabu. Raw Ising outputs were worse than greedy. — [arXiv:2403.19175](https://arxiv.org/html/2403.19175v1)
- QKP n=100–300: the penalty QUBO solved only 35/60 of the larger instances, while native-constraint EIM matched Gurobi's optima with comparable time. — [arXiv:2508.06909](https://arxiv.org/html/2508.06909)
- On Chimera Ising, tailored branch-and-cut (Gurobi 9.0 based) proved optimality, and simulated annealing beat the D-Wave QPU. — [Jünger et al., ACM JEA 2021](https://dl.acm.org/doi/abs/10.1145/3459606)
- On modularity QUBOs, single-GPU SB outperformed Gurobi (time limits not verified). — [SSRN Li et al.](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5496392)
- Classical solvers such as Gurobi, CPLEX and CP-SAT "routinely solve problems with thousands of variables to provable optimality" in the QKP/MKP setting, which is the competition quantum methods face. — [arXiv:2503.22325](https://arxiv.org/html/2503.22325v1) (a quantum-methods paper making this concession)
- Industrial job-shop scheduling: the quantum/quantum-inspired approaches (including DA) were positioned as complements to exact/MILP, not replacements. — [arXiv:2607.13325](https://arxiv.org/abs/2607.13325)
- Practical-size problems: annealers "lose their utility when facing problems in practical size and settings." — [Huang et al. arXiv:2203.02325](https://arxiv.org/abs/2203.02325)

### Inferences
- Recommended stack for a 10^3–10^5 variable constrained admission QUBO on this workstation:
  1. **Baseline first:** LP relaxation plus rounding/greedy, and CP-SAT (OR-Tools; uses the 16 cores) or HiGHS/Gurobi MILP on the *native* linear-constrained formulation, which avoids penalties entirely. A knapsack-structured admission problem with linear constraints is exactly what MILP/CP-SAT do well; at 10^4–10^5 binaries with few constraints, they typically give near-optimal answers with certified gaps in seconds to minutes (inference, based on the Gurobi QKP results above, which are on a harder *quadratic* objective).
  2. **Ising heuristic as a secondary arm:** `simulated-bifurcation` (bSB for speed, dSB/heated for quality, many agents on the GPU) for n ≤ ~5×10^4 dense in fp32. Add λ sweeps, a greedy repair plus 1-flip/swap local search post-processor, and always report feasibility rate and gap vs the MILP/CP-SAT result.
  3. **CPU SA/Tabu** (dwave-samplers) as a cheap reference heuristic on the same QUBO, to show whether SB adds anything over SA.
- Ising heuristics have their best chance when the objective is genuinely **quadratic and dense** (pairwise interactions such as co-peak or interference terms) *and* constraints are few or soft. That is where MILP linearisation blows up (O(n^2) auxiliary variables). With a linear objective and hard knapsack constraints, expect MILP/CP-SAT or greedy to win.
- Max-min and makespan objectives require auxiliary integer variables plus several penalty inequalities in QUBO form. No evidence was found that Ising heuristics are competitive there, and the structural arguments in Q4 predict they are not.

### Gaps
- We found no head-to-head study of SB (bqth29 or Toshiba) vs CP-SAT/HiGHS on multidimensional knapsack, makespan or max-min problems at 10^4–10^5 variables.
- Time-normalised comparisons on identical hardware (one GPU vs 16 CPU cores) are essentially absent in the literature. Most studies compare cloud hardware against a time-limited Gurobi run on different machines.
