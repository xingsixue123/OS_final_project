# QUBO/Ising encodings for budget-constrained min-max (bottleneck) episode selection

Problem recap (for the report writer): choose x_e in {0,1} over 10^4-10^6 cache episodes; write cost s_e; per-window savings d_{e,w} over ~144-1000 windows. Goal: min_x max_w L_w(x), L_w(x) = C_w - sum_e d_{e,w} x_e, s.t. sum_e s_e x_e <= W. Planned approach: weighted sum-of-squares surrogate sum_w alpha_w L_w(x)^2 with iterative reweighting of alpha_w toward the argmax window, budget as a quadratic penalty, then QUBO -> Ising, solved with simulated bifurcation (SB) or an annealer.

Verification status: I read the full text of Lucas 2014, Glover et al. 2019 tutorial, Montañez-Barrera et al. (unbalanced penalization) and Mücke et al. (parameter compression) as PDFs. For the other sources I read only the abstract or landing page, and the citations say so. Claims marked **[UNVERIFIED]** come from memory or from secondary snippets only.

## Q1. Inequality / knapsack constraints in QUBO: slack, equality penalty, unbalanced penalization, Lagrangian; penalty-weight choice and failure modes

### Takeaway
There are four families. (a) Slack variables with a binary (log) expansion are exact but add about ⌊1+log2(range)⌋ spins per constraint and make the constraint term fully dense over the problem variables plus the slack. (b) A plain λ(Σ s_e x_e − W)^2 with no slack is an *equality* constraint, so it biases the solution toward using exactly W. (c) Unbalanced penalization −λ1·h + λ2·h^2 with h = W − Σ s_e x_e needs no slack and did better than slack in published knapsack and bin-packing tests. Its λs are tuned empirically, and it is a soft, approximate encoding. (d) Lagrangian or dual methods (Hubbard–Stratonovich, subgradient) move the constraint outside the QUBO as a *linear* term μ·s_e, which removes the dense coupling. Penalty weights have a "Goldilocks" range. If they are too small, solutions are infeasible. If they are too large, the objective landscape is swamped: convergence slows and returned solutions are feasible but poor.

### Cited Findings
- **Slack with a log/binary expansion (Lucas).** A variable taking values 1..N needs only M+1 bits, M = ⌊log2 N⌋, using Σ_{n=0}^{M−1} 2^n y_n + (N+1−2^M) y_M. The ground state may become degenerate when N ≠ 2^{M+1}−1. Knapsack with integer weights needs N + ⌊1+log W⌋ spins, with H_A = A(W_slack − Σ w_α x_α)^2-type terms and H_B = −B Σ c_α x_α. Correctness requires **0 < B·max(c_α) < A**. — [Lucas 2014, Front. Phys. 2:5, arXiv:1302.5843, §2.4 and §5.2](https://arxiv.org/abs/1302.5843)
- **Glover–Kochenberger–Du tutorial.** Inequality constraints become equalities by adding slack variables "via a binary expansion", with upper bounds on each slack "estimated" by inspection (e.g., s ≤ 3 → x6 + 2x7). The quadratic penalty is P(Ax−b)^T(Ax−b) ("Transformation #1"). — [Glover, Kochenberger & Du, arXiv:1811.11538 (4OR 17:335–371, 2019)](https://arxiv.org/abs/1811.11538)
- **Glover et al. on penalty-weight guidance.** "A penalty value that is too large can impede the solution process as the penalty terms overwhelm the original objective function information … too small jeopardizes the search for feasible solutions." There is a "'Goldilocks region' of considerable size". A suggested start is P = **75%–150% of an estimate of the original objective value**, followed by feasibility checks and re-solves. — [arXiv:1811.11538 §"Comment on the Scalar Penalty P"](https://arxiv.org/abs/1811.11538)
- **Unbalanced penalization.** Formulation: ζ(x) = −λ1·h(x) + λ2·h(x)^2 with h(x) = B − Σ l_i x_i ≥ 0. It is motivated as a 2nd-order Taylor expansion of e^{−h}, and it needs no slack variables. The λ0,1,2 values were tuned with Nelder–Mead on one small instance (a 13-item KP) and reused on larger instances. KP values were λ1 = 0.9603 and λ2 = 0.0371 (TSP and BPP values are also in Table I). For a 21-item KP, the true optimum was at worst eigenvalue position 49 of 2^21. For bin packing on the D-Wave Hybrid solver, the method found optima up to 29 items versus 11 with slack, and the slack version "fails to find optimal solutions after 7 nodes". It also gave more valid solutions on D-Wave Advantage, with an exception at 7 nodes that was inconclusive. — [Montañez-Barrera, Willsch, Maldonado-Romo, Michielsen, arXiv:2211.13914; Quantum Sci. Technol. 9:025022 (2024), DOI 10.1088/2058-9565/ad35e4](https://arxiv.org/abs/2211.13914)
- **Same paper, slack cost.** In KP the number of slack variables is constant and depends on the knapsack capacity. In TSP it grows exponentially with cities, and in BPP it grows substantially with items. — [arXiv:2211.13914 Fig. 2](https://arxiv.org/abs/2211.13914)
- **Bontekoe, Phillipson & van der Schoot (ICCS 2023).** Six QUBO translations of the quadratic knapsack constraint were compared with simulated annealing. The best one used **no auxiliary variables** for the inequality. — [Springer LNCS, DOI 10.1007/978-3-031-36030-5_8](https://link.springer.com/chapter/10.1007/978-3-031-36030-5_8) (abstract only)
- **Dual / Lagrangian approaches outside the QUBO.**
  - Ohzeki uses the Hubbard–Stratonovich transformation to turn quadratic (fully connected) constraint penalties into *linear* terms plus an auxiliary continuous variable that is updated classically. The goal was to avoid dense embeddings on sparse hardware. — [Ohzeki, Sci. Rep. 10:3126 (2020), arXiv:2002.05298](https://arxiv.org/abs/2002.05298)
  - This was extended to inequality constraints, tested on the quadratic knapsack problem. — [Takabayashi, Goto & Ohzeki, arXiv:2411.06901 (J. Phys. Soc. Jpn., 2025)](https://arxiv.org/abs/2411.06901) (abstract only)
  - An application to EV-bus charging scheduling used multipliers updated by ADAM. A case needing **2,499 physical qubits with slack+penalty needed only 320 with the dual approach.** — [Yu & Nabil, Front. Phys. 9:730685 (2021)](https://www.frontiersin.org/journals/physics/articles/10.3389/fphy.2021.730685/full)
- **Other penalty-weight work.**
  - Verma & Lewis (Discrete Optimization, 2020) bound the penalty M using the largest gain available from violating a constraint. — [Semantic Scholar entry](https://www.semanticscholar.org/paper/Penalty-and-partitioning-techniques-to-improve-of-Verma-Lewis/46de092b2e81c405f80af30cb7f90d979407483d) (snippet only)
  - Ayodele (EvoCOP 2022) found that too-small weights give infeasible solutions and too-large weights slow convergence, and proposed new static weight rules. — [arXiv:2206.11040](https://arxiv.org/abs/2206.11040)
- **The "big-M problem" (Alessandroni et al., 2026).** A too-large M makes the solver return "feasible states that may be far from optimal", and mean objective energy rises as M grows. The trivial bound M ≤ ‖Q‖_ℓ1 + δ "overshoots". Their Algorithm 1 pre-computes M with guarantees for Gibbs-like samplers and is claimed to be an order of magnitude faster than binary search. — [arXiv:2604.02416](https://arxiv.org/html/2604.02416)

### Inferences
- **The bias of a plain λ(Σ s_e x_e − W)^2 in our problem.** With no slack, energy is lowest at total write = W exactly. Any budget under-use costs λ·(W−Σs x)^2, and over-use costs the same, so budget violation is symmetric. With savings pulling usage upward, the minimizer usually lands slightly *over* W. The overshoot is roughly where the marginal L^2 reduction equals 2λ·(overshoot)·s_e. In practice this means repair or pruning is needed after decoding.
- **Unbalanced penalization acts as a target margin.** −λ1 h + λ2 h^2 is minimized at h* = λ1/(2λ2). That is a soft "aim for W − λ1/(2λ2)" rather than an exact ≤. With the paper's KP values, h* ≈ 12.9 in the instance's weight units. So λ1/λ2 must be rescaled to our s_e units, e.g. bytes normalized by W. The coupling term is still λ2·s_e·s_e' for all pairs, so it removes the slack spins but **not the density**.
- **Slack cost is negligible here.** A single knapsack needs only ⌈log2(W/Δs)⌉ slack spins, where Δs is the size quantum. That is about 20–40 spins, tiny against 10^4–10^6 episodes. The real cost of slack is dynamic range: the MSB slack coefficient is about W/2 while small s_e are about 1, and the A ≫ B·max(c) requirement from Lucas adds more range.
- **The best fit for our scale is probably the Lagrangian with μ outside the QUBO.** Replace the budget term with μ·Σ s_e x_e, which only changes the diagonal. Update μ by bisection or subgradient on the observed Σ s x − W, and do a final greedy repair. This removes the only globally dense term, and it pairs naturally with the outer alpha-reweighting loop: both are outer dual-style loops.

### Gaps
- I could not read the full text of the IEEE multi-knapsack penalty paper (ieeexplore document 10924197, "QUBO Formulations and Characterization of Penalty Parameters for the Multi-Knapsack Problem", 2025). The page returned empty, so I have no specific bounds from it.
- Quintero & Zuluaga (knapsack/QUBO penalty bounds) was not located in this session. **[UNVERIFIED]**
- Glover et al.'s 75–150% rule targets objective *values*. I found no source that calibrates it for squared (sum-of-squares) objectives.

## Q2. Min-max / bottleneck objectives in QUBO: epigraph, L_p / sum-of-squares, log-sum-exp, IRLS reweighting

### Takeaway
The only exact QUBO route is the epigraph or reference-bin construction, which needs auxiliary bits and a per-window slack. Lucas's job-sequencing Hamiltonian is the canonical example. Scheduling practitioners otherwise (i) solve the *decision* version with a fixed horizon and bisect, or (ii) replace max with a balancing (sum-of-squares) proxy. Log-sum-exp is not quadratic, so it cannot be used directly. IRLS toward min-max (Lawson's algorithm) has a known linear-convergence theory only for *continuous linear* Chebyshev approximation. I found no guarantee for binary variables.

### Cited Findings
- **Lucas, job sequencing (min makespan).** The Hamiltonian assumes WLOG that machine 1 is the max. For each machine α≠1 it adds slack y_{n,α} encoding M1 − Mα = n: H_A = A Σ_i(1−Σ_α x_{i,α})^2 + A Σ_{α≠1}(Σ_n n·y_{n,α} + Σ_i L_i(x_{i,α} − x_{i,1}))^2, and it minimizes H_B = B Σ_i L_i x_{i,1}. This needs 0 < B·max(L_i) < A and uses mN + (m−1)⌊1+log M⌋ spins, where M ≤ N·max L_i in the worst case. — [Lucas 2014, arXiv:1302.5843 §6.3](https://arxiv.org/abs/1302.5843)
- **Decision version plus bisection (Venturelli et al.).** Job-shop was formulated as a time-indexed QUBO with a *fixed timespan*, and "tailored binary searches" over the horizon were used instead of encoding the makespan objective. Variable pruning was also used. Instances went up to 6 jobs × 6 machines on D-Wave. — [Venturelli, Marchand & Rojo, arXiv:1506.08479 (2015/2016)](https://arxiv.org/abs/1506.08479)
- **Balancing proxy in the scheduling literature.** A 2026 industrial case study says "the maximum function cannot be directly encoded in a QUBO". Makespan minimisation is therefore "approximated by balancing total production times across machines", and full time-indexed scheduling needs on the order of N^2·M variables. — [arXiv:2607.13325](https://arxiv.org/pdf/2607.13325) (search snippet only, **[not full-text verified]**)
- **Decoupled makespan.** HPC workflow-mapping QUBOs (2026) optimize only the assignment in the QUBO and compute makespan with a classical scheduler afterward. This avoids time-indexed variables. — [Sharma, Boehme & Kunkel, arXiv:2605.25350](https://arxiv.org/html/2605.25350v1)
- **Exact epigraph with surplus variables.** Search snippets describe an "exact epigraph reformulation … followed by equality conversion via surplus variables with a quadratic penalty whose exactness on the finite binary domain is formally established". — [search result, source paper not identified] **[UNVERIFIED — could not attribute]**
- **Lawson / IRLS for minimax.** Lawson's 1961 thesis computes discrete linear minimax (Chebyshev) approximations as limits of weighted least-squares solutions. The method is an IRLS iteration with in-principle **linear** convergence, and a convergence analysis appears in arXiv:2401.00778. — [Authors not verified, "A convergence analysis of Lawson's iteration…", arXiv:2401.00778](https://arxiv.org/html/2401.00778); also [Nakatsukasa & Trefethen, AAA-Lawson, SIAM J. Sci. Comput. 2020, arXiv:1908.06001](https://arxiv.org/abs/1908.06001)
- IRLS for ℓ∞ regression with improved convergence rates exists for convex continuous problems. — [Authors not verified (likely Ene & Vladu), "Improved convergence for ℓ∞ and ℓ1 regression via IRLS", ICML 2019 (NSF PAR copy)](https://par.nsf.gov/servlets/purl/10104982) (title only)

### Inferences
- **The exact epigraph for our problem.** Introduce a peak variable t encoded in K bits, plus, for each window, slack σ_w encoded in K bits with C_w − Σ d_{e,w} x_e + σ_w = t. The terms are A Σ_w (C_w − Σ_e d_{e,w} x_e + σ_w − t)^2 + B·t. This adds about (|W|+1)·K spins; with |W| = 144–1000 and K ≈ 10–16, that is about 1.5k–16k spins, which is small relative to the episodes. However, each window's square couples **all episodes active in w with each other, with σ_w, and with t**. Since t is in every window's square, the t bits connect to every episode. The A ≫ B·max requirement (Lucas) also widens the coefficient range. I expect this to be hard for annealers or SB unless A is tuned carefully. There is no published scaling evidence for this exact form at 10^5+ variables. **[inference]**
- **Lucas's "reference machine" trick does not transfer directly.** It works because the bin that holds the max is a symmetry-broken label. Our windows are not interchangeable, so a true epigraph variable t is needed.
- **The sum-of-squares surrogate.** Σ_w α_w L_w^2 is exactly the "balancing" proxy used in scheduling QUBOs. Two caveats:
  - (i) It also penalizes windows with L_w < 0, i.e. over-saving. Unless C_w is large enough that L_w stays positive, the surrogate rewards *not* saving in low windows. A shift L_w − τ, or a one-sided hinge (which needs slack), may be needed.
  - (ii) Lawson-style updates α_w ← α_w·|L_w(x^k)|, normalized, converge for the continuous linear Chebyshev problem, but binary x breaks convexity. Treat the loop as a heuristic: track the best true max_w L_w seen and use it, not the surrogate, as the stopping criterion.
- **A bisection alternative (Venturelli-style).** Fix a target peak T. Solve the feasibility QUBO Σ_w (hinge of L_w − T)^2 + μ·s·x, or maximize savings in windows above T. Then bisect on T. This replaces the min-max with a sequence of decision problems.
- **Log-sum-exp.** (1/β) log Σ_w exp(β L_w) is not a polynomial of degree ≤ 2, so it cannot be a QUBO. Its gradient-weighting interpretation (softmax weights on windows) can still be used as the α-update rule: α_w ∝ exp(β L_w). That is a softer alternative to Lawson's multiplicative rule. **[inference, no QUBO source]**

### Gaps
- I found no paper that compares an L2-surrogate + reweighting QUBO against the true min-max (bottleneck) optimum on binary selection problems.
- I found no QUBO paper that uses log-sum-exp or softmax reweighting for min-max.

## Q3. Closest published QUBO formulations: variable counts and coupling densities

### Takeaway
Number partitioning, and its m-way form as job sequencing, is the nearest structural analogue. Its objective (Σ n_i s_i)^2 is a fully dense all-to-all Ising glass. Knapsack adds ⌊1+log W⌋ slack spins and a dense rank-1 penalty. Time-indexed scheduling (job-shop) scales as N^2·M variables but gives sparser, structured couplings.

### Cited Findings
- **Number partitioning.** H = A(Σ_i n_i s_i)^2 on N spins, a complete graph. Lucas flags complete graphs and "separations of energy scales" as the main hardware problems: "these devices may only encode couplings constants of 1,…,16" (2014 D-Wave). — [Lucas 2014 §2.1 and hardware discussion, arXiv:1302.5843](https://arxiv.org/abs/1302.5843)
- **Knapsack.** N + ⌊1+log W⌋ spins; **job sequencing**: mN + (m−1)⌊1+log M⌋ spins. — [Lucas 2014 §5.2, §6.3](https://arxiv.org/abs/1302.5843)
- **Job-shop time-indexed QUBO.** Time-indexed; up to 6×6 on D-Wave Vesuvius, with variable pruning and embedding required. — [arXiv:1506.08479](https://arxiv.org/abs/1506.08479). A full time-indexed schedule needs about N^2·M variables. — [arXiv:2607.13325](https://arxiv.org/pdf/2607.13325) (snippet)
- **Multiple and multidimensional knapsack.** A 2025 IEEE paper gives QUBO formulations with an algebraic characterization of penalty parameters and compares QAOA, QA and classical solvers. — [IEEE Xplore 10924197](https://ieeexplore.ieee.org/document/10924197/) (abstract snippet only)
- **Bin packing with unbalanced penalization.** Solved up to 29 items with D-Wave Hybrid, versus 11 items with slack. — [arXiv:2211.13914](https://arxiv.org/abs/2211.13914)

### Inferences
- **Our Q matrix.** Q_{ee'} = Σ_w α_w d_{e,w} d_{e',w} + λ s_e s_{e'}. This is a rank-≤|W| matrix plus a rank-1 matrix, i.e. a generalized multi-way number partitioning with a knapsack. The number of nonzeros is n^2 because of the λ s s^T term. Even with μ-outside-QUBO, the window term couples every pair of episodes that share a window. Long-lived episodes spanning many windows make it effectively dense.
- **Scale.** At n = 10^5–10^6, an explicit dense Q (10^10–10^12 entries) cannot be stored. Published QUBO scheduling and knapsack demos are all at ≤ 10^2–10^3 variables, so our instance size is **2–4 orders of magnitude beyond the published QUBO formulations I found**.

### Gaps
- I did not locate the "parallel machine scheduling" QUBO papers (e.g., the FGCS 2023 unrelated-parallel-machine QA paper, ScienceDirect S0167739X23002583) in full. Their exact variable counts are unverified.
- Stollenwerk et al. (flight-gate / ATM QUBOs) were not fetched. **[UNVERIFIED]**

## Q4. Handling globally dense penalty terms (sparsification, low-rank, Lagrangian outside the QUBO)

### Takeaway
Two established routes exist. (1) Dualize: Hubbard–Stratonovich or Lagrangian methods turn the quadratic penalty into a linear term plus an outer multiplier loop, removing the dense coupling. (2) Keep the dense term but exploit its low rank. Spatial-photonic Ising machines are built around J = Σ_k λ_k ξ^(k) ξ^(k)T. The same factorization makes matrix-free SB feasible in O(nnz(D)) per step.

### Cited Findings
- Hubbard–Stratonovich turns fully connected quadratic constraint terms into linear terms, which mitigates low embeddable size on sparse (Chimera) hardware. — [Ohzeki 2020, arXiv:2002.05298](https://arxiv.org/abs/2002.05298)
- In a scheduling instance this reduced physical qubits from 2,499 to 320, with multipliers updated classically (ADAM) between annealer calls. — [Yu & Nabil 2021, Front. Phys. 9:730685](https://www.frontiersin.org/journals/physics/articles/10.3389/fphy.2021.730685/full)
- The extension to inequality constraints uses a subgradient method with QA, avoiding slack. — [Takabayashi, Goto & Ohzeki, arXiv:2411.06901](https://arxiv.org/abs/2411.06901)
- Low-rank Ising: SPIMs natively handle rank-1 couplings and have been extended to low-rank J = Σ_{k≤K} λ_k ξ^(k) ξ^(k)T. The model is "particularly efficient for Ising problems with low-rank interaction matrices". — [PRL 131:063801 (2023), arXiv:2303.14993 (authors not verified)](https://arxiv.org/pdf/2303.14993); [Commun. Phys. 2025, arXiv:2406.01400](https://arxiv.org/pdf/2406.01400)
- Simulated bifurcation (SB) targets all-to-all Ising problems. — [Goto, Tatsumura & Dixon, Sci. Adv. 5:eaav2372 (2019)](https://www.science.org/doi/10.1126/sciadv.aav2372); ballistic/discrete SB: [Goto et al., Sci. Adv. 7:eabe7953 (2021)](https://www.science.org/doi/10.1126/sciadv.abe7953). The specific result "a 100,000-node fully connected MAX-CUT solved in about 0.5 s on FPGA/GPUs" is from memory and was not verified here (the page returned 403). **[UNVERIFIED]**

### Inferences
- **SB is matrix-free for our Q.** Each SB step needs only J·x. With J = −(D^T diag(α) D + λ s s^T) (up to sign and diagonal), compute y = D x (|W|-vector), then D^T(α ⊙ y), then λ s (s^T x). The cost is O(nnz(D) + n) per step, with no n×n matrix. The dense budget term becomes one dot product. This is the "low-rank Ising" structure the SPIM papers exploit. **This is the key practical enabler at 10^5–10^6 episodes.** It holds for SB/GPU solvers but *not* for D-Wave-style hardware, which needs explicit sparse embedding. **[inference]**
- **For hardware annealers**, move the budget outside as μ·s_e (diagonal) and optionally split windows or episodes into blocks. The window-sharing couplings are still dense within each window.

### Gaps
- I found no published SB implementation that uses a factorized low-rank J with a knapsack term at this scale. It is feasible in principle, but I found no citation.
- Sparsifying the window term (e.g., dropping small d_{e,w} d_{e',w}) has no QUBO-specific literature that I found.

## Q5. Precision / dynamic range of coefficients (SB and annealers)

### Takeaway
Dynamic range (DR), in bits, controls how robust a QUBO is to parameter rounding or noise. Large penalty weights, log-encoded slack MSBs, and heterogeneous s_e and d_{e,w} all raise DR. Early D-Wave hardware reliably resolved only about 16 coupling levels. There are optimum-preserving methods that shrink DR.

### Cited Findings
- Mücke, Gerlach & Piatkowski define the DR of Q as log2 of (largest minus smallest distinct value) over the minimal gap between distinct values. The larger the DR, the more bits are needed and the less robust the instance is against distortion. They give optimum-preserving parameter modifications that reduce DR, and report drastic improvement on quantum annealing hardware for BinClustering and SubsetSum. — [arXiv:2307.02195; Quantum Mach. Intell. 7 (2025)](https://arxiv.org/abs/2307.02195)
- Lucas warns about formulations needing "large separations of energy scales", such as coupling ratios ∝ N, and notes that devices "may only encode couplings constants of 1, …, 16". — [arXiv:1302.5843](https://arxiv.org/abs/1302.5843)
- Hard-constraint weights must dominate the objective scale (0 < B·max c < A), which directly sets a minimum DR. — [Lucas 2014](https://arxiv.org/abs/1302.5843)

### Inferences
- **Sources of large DR in our problem:**
  - (i) s_e s_{e'} products when object sizes span KB–MB, which is about 20 bits of range in the product;
  - (ii) α_w after many multiplicative reweighting steps, since weights can collapse onto a few windows;
  - (iii) d_{e,w} d_{e',w} squared products;
  - (iv) slack-bit coefficients up to about W/2 if slack is used.
- **Mitigations:** normalize s by W and d by max C_w; quantize s_e and d_{e,w} to a few bits; floor and clip α_w, e.g. α_w ∈ [ε, 1] after normalization, or use softmax with bounded β; keep the budget as a linear μ term; and apply Mücke-style DR reduction if targeting annealers.
- SB in float32 on GPU tolerates more DR than annealers. However, the SB dynamics are driven by the *largest* couplings, so a dominant λ s s^T term will still swamp the window structure, which is the landscape-flattening failure mode. **[inference]**

### Gaps
- I found no quantitative DR tolerance for SB (bSB/dSB).
- I found no study of how DR grows under IRLS-style reweighting in QUBO loops.
