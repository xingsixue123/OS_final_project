# Constraint-handling Ising/QUBO solvers with runnable code (CPU, 24 threads, 123 GB, no GPU)

Scope and conventions. This note extends `../../../ising_followup/survey.md` and `../../../ising_followup/audit/AUDIT.md` and does not repeat them. Those files already cover `simulated-bifurcation`, dwave-samplers, OpenJij (QUBO), `cim-optimizer`, MindQuantum QAIA, FEM, `qqa`, PySA/tamc/APT (briefly), and the headline claims of EIM, Awai and Delacour. The new material here is: algorithm details precise enough to implement, code-existence checks, and constrained-problem evidence.

- **Metadata source.** Repository and package metadata (license, last push, last release) was pulled on 2026-09-28 from the GitHub REST API (`api.github.com/repos/...`) and the PyPI JSON API (`pypi.org/pypi/<pkg>/json`).
- **Labels.** `[UNVERIFIED]` means I could not confirm the claim from a primary source. `[inference]` marks my own reasoning.
- **Notation.** The problem is E(x) = xᵀQx + cᵀx, subject to sᵀx ≤ W, plus possibly one-hot groups and per-slot capacities Σ_e d_{e,w} x_e ≤ K_w.
  - Q = D diag(α) Dᵀ, with D an n×m sparse matrix (1–3 nnz per row) and m ≈ 144.
  - The brief writes DᵀΛD; which form is correct depends on D's orientation. Either way Q is n×n with rank ≤ m.

---

## Q1. Lagrangian / augmented-Lagrangian / subgradient / ADMM Ising methods: implementable details and code

### Takeaway
All the Lagrangian-on-Ising methods share one outer loop: an Ising or SA inner solve at fixed multipliers, then a (sub)gradient step on the multipliers. They differ in three things: whether a small quadratic penalty is kept (SAIM, ALF), whether multipliers are updated from single samples or from ensemble averages (SAIM uses single samples; Ohzeki-HS and ALF use averages), and how inequalities are handled (binary slack in SAIM, ALF and LagONN; slack-free via μ ≥ 0 in Takabayashi/Ohzeki).
- **Code.** Runnable code exists only for Delacour's SAIM (MATLAB, GPL-3.0, dense), Delacour's 2D-PT (MATLAB, MIT) and Qiskit's ADMMOptimizer (Python, Apache-2.0, repo now archived). Awai, Takabayashi/Ohzeki and Hagiwara released none.
- **Cost of rewriting.** Every one of these is roughly 30–80 lines on top of an existing SA or SB kernel. Our audit's "μ-bisection outside the solver" is already a member of this family.

### Cited Findings

**Delacour, Self-Adaptive Ising Machine (SAIM), DATE 2025, [arXiv:2501.04971](https://arxiv.org/abs/2501.04971)**
- **Algorithm 1 (verbatim structure).**
  - Start with (λ₀, P) ← (0, α·d·N), where d is the density of J and N is the number of spins including slack spins.
  - Repeat K times:
    1. x_k = argmin_x L_k(x), where L(x) = f(x) + P‖g(x)‖² + λᵀg(x) (solved on the Ising machine);
    2. store x_k if it is feasible;
    3. update λ_{k+1} ← λ_k + η·g(x_k) (on the CPU).
  - Return the best feasible x. — [arXiv PDF](https://arxiv.org/pdf/2501.04971)
- **Interpretation.** The λ step is a subgradient or "surrogate-gradient" ascent on the dual lower bound LB_L = min_x L. It is valid even when the inner solve is only a pseudo-minimum. — [arXiv PDF](https://arxiv.org/pdf/2501.04971)
- **Inequality handling.** Inequalities are turned into equalities with binary-expanded slack: Aᵀx + x_S = b, x_S = Σ_q 2^q x_S^q, Q = floor(log₂ b + 1). A and b are normalized by max(|A|, |b|), and W and h by max(|W|, |h|). — [arXiv PDF](https://arxiv.org/pdf/2501.04971)
- **Inner solver.** A software p-bit machine: I_i = Σ_j J_ij m_j + h_i and m_i = sign(tanh(βI_i) + U(−1, 1)). This is sequential Gibbs sampling with a linear β ramp from 0 to β_max. One λ update is made per SA run, from the last sample only. — [arXiv PDF](https://arxiv.org/pdf/2501.04971)
- **Exact settings in the released code** (`SAIM_QKP.m`):
  - P = 2·Nt·density;
  - 1,000 MCS per SA run;
  - β_max = 10 (on normalized coefficients);
  - η = 20;
  - 2,000 λ updates;
  - dense `W_new = W + P·AᵀA`, with the diagonal removed;
  - the p-bit update loop is `I(i) = -2*W_new(i,:)*S - h_new(i); S(i) = sign(tanh(beta*I(i)) - 2*rand + 1)`.
  - Source: [GitHub corentindelacour/self-adaptive-IM](https://github.com/corentindelacour/self-adaptive-IM) (read via raw.githubusercontent).
- **MKP settings.** P = 5dN, with density approximated as 2/(N+1). — [arXiv PDF](https://arxiv.org/pdf/2501.04971)
- **QKP results (Billionnet–Soutif instances, N = 100–300).**
  - Median accuracy is above 99.2% at every size.
  - At N = 300 the medians are 94.5% for the best penalty-SA (ref [16]) and 84.8% for parallel tempering on Fujitsu DA (PT-DA).
  - SAIM uses 200 M MCS, against 19.5 G for the best SA and 15 G for PT-DA, so the claim is "7,500× fewer" sweeps than PT-DA.
  - At N = 100, SAIM's best accuracy averages 99.8% against 88.8% for a hand-tuned penalty (tuned P = 40–500·dN) at an equal 2 M MCS.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2501.04971)
- **MKP results (Chu–Beasley instances, N = 100/250, M = 5/10 constraints).**
  - Average best accuracy is 99.7%, "comparable" to a specialised GA (≥ 99.1%).
  - Only **5.1% of samples are feasible**, against about 50% on QKP. The paper attributes this to multiple constraints being "harder to satisfy simultaneously".
  - Optima come from MATLAB `intlinprog`, used only as a reference. There is no timing race against MILP.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2501.04971)
- **Code.**
  - GitHub `corentindelacour/self-adaptive-IM`, **GPL-3.0**, last push 2025-01-10.
  - MATLAB scripts `SAIM_QKP.m` and `SAIM_MKP.m`, with MKP `.mps` instances included.
  - Metadata: GitHub API. Code: [GitHub](https://github.com/corentindelacour/self-adaptive-IM).

**Delacour, Sajeeb, Hespanha, Camsari, "Two-dimensional parallel tempering for constrained optimization" (2D-PT), *Phys. Rev. E* 112, L023301 (2025), [arXiv:2506.14781](https://arxiv.org/abs/2506.14781)**
- **Replica grid.** Replicas sit on an I×J grid of (β_i, P_j). Temperature swaps are accepted with min(1, exp(Δβ·ΔE)). Penalty swaps are accepted with min(1, exp(β·ΔP·Δg)), where Δg is the difference in constraint violation. The target sample is read from the (β_max, P_max) corner. — [arXiv HTML](https://arxiv.org/html/2506.14781)
- **Adaptive ladders.**
  - β is incremented by α_β/σ_E until σ_E < σ_min.
  - P is incremented by α_P/(β σ_g) until the mean violation is below 0.5.
  - The grid is capped at 20×20, with 50–500 MCS between swaps.
  - Reported result: "orders of magnitude" speedup over the same number of 1-D PT replicas on sparsified Wishart instances (≈ O(N⁵) speedup scaling in the fetched summary).
  - Source: [arXiv HTML](https://arxiv.org/html/2506.14781); [arXiv abs](https://arxiv.org/abs/2506.14781)
- **Code.** GitHub `OPUSLab/2DPT`, **MIT**, MATLAB, last push 2025-08-04. It contains only the sparsified-graph (copy-constraint) application and Wishart instances; there is no knapsack driver. — [GitHub](https://github.com/OPUSLab/2DPT)
- **No Gurobi comparison is reported** (fetched summary of the HTML). — [arXiv HTML](https://arxiv.org/html/2506.14781)

**Awai, Itoh, Takahashi, Tanahashi, Tanaka, "Evaluating the solution performance of the augmented Lagrangian function on Ising machines," *JPSJ* 95, 094004 (2026), [arXiv:2606.24241](https://arxiv.org/abs/2606.24241)**
- **Formulation.** The knapsack inequality becomes an equality through log-encoded slack y_d with D = ⌈log₂(W+1)⌉. The augmented Lagrangian is H_AL = H_obj + (μ/2)·H_const² − λ·H_const. — [arXiv HTML](https://arxiv.org/html/2606.24241)
- **ALM update.** λ^(k+1) = λ^(k) − μ^(k)⟨g(x^(k)) − c⟩, with the average taken over the samples, and μ^(k+1) = a·μ^(k) with a > 1. — [arXiv HTML](https://arxiv.org/html/2606.24241)
- **Inner solver.** Fixstars Amplify AE (cloud), with a 1 s anneal and 50 runs per setting. Instances are QKP with N = 100/200/300.
- **Metric and result.** TTε = τ·ln(1 − 0.99)/ln(1 − p_ε) with ε = 5%. The augmented Lagrangian cuts TTε by about 10× against a pure penalty (μ = 40). The best setting was (μ, λ) = (5, 100) on r_100_50_5.
- **Code.** No code link. — [arXiv HTML](https://arxiv.org/html/2606.24241); [JPSJ](https://journals.jps.jp/doi/10.7566/JPSJ.95.094004)

**Ohzeki, Hubbard–Stratonovich (HS) constraint linearization, [arXiv:2002.05298](https://arxiv.org/abs/2002.05298)** (published in *Sci. Rep.* 10, 3126, 2020 `[venue from memory, UNVERIFIED]`)
- **Idea.** An HS transform of the partition function turns the quadratic penalty (Σ a_i x_i − b)² into a linear field ν(Σ a_i x_i − b) with an auxiliary ν. ν is then updated by gradient steps from sample averages, so no dense constraint couplers are needed.
- **Applications.** Partition, linear equations, and traffic flow in Sendai and Kyoto. — [arXiv abs](https://arxiv.org/abs/2002.05298)

**Takabayashi, Goto, Ohzeki, subgradient + quantum annealing for inequalities, [arXiv:2411.06901](https://arxiv.org/abs/2411.06901)**
- **Slack-free formulation.** Z = Σ_x exp(−βf₀)Π_k Θ(C_k − F_k(x)) gives the sampling Hamiltonian H(x; μ) = f₀(x) + Σ_k μ_k F_k(x) with μ ≥ 0.
- **Update.** μ_k ← μ_k + max{0, η(⟨F_k⟩ − C_k)}.
- **Polyak-type step.** η = τ[f₀^UB − (⟨f₀⟩ + Σ_k(⟨F_k⟩ − C_k))] / Σ_k(⟨F_k⟩ − C_k)², with τ₀ = 0.5 halved after 10 non-improving iterations.
- **Setup.** QKP with N ≤ 64, run with OpenJij SA/SQA.
- **Negative result.** "**greedy methods achieved superior accuracy**" to all the sampling variants.
- **Code.** None. — [arXiv HTML](https://arxiv.org/html/2411.06901v1)

**Follow-ups from the same group (no code)**
- Takabayashi & Ohzeki, mixed-binary QP via QUBO sampling, [arXiv:2607.21286](https://arxiv.org/abs/2607.21286). Continuous variables are integrated out analytically at fixed Lagrange multipliers. Solutions are more reliably feasible than with penalties, and the abstract claims "faster time-to-target … than the commercial solver in the upper range of tested problem sizes" (sizes not given in the abstract).
- Hagiwara, Arai, Takabe, slack-free deep-unfolded "UPOM"/"DU-UPOM", [arXiv:2607.20042](https://arxiv.org/abs/2607.20042). The two static unbalanced-penalization coefficients are replaced by an auxiliary-variable update. Tested on random knapsack under QA.

**Gambella & Simonetto, multi-block ADMM for mixed-binary problems, [arXiv:2001.02069](https://arxiv.org/abs/2001.02069)** (IEEE TQE 2020)
- **Decomposition.** ADMM splits the problem into a QUBO block (binaries) and convex continuous blocks, with 2-block or 3-block variants. — [arXiv abs](https://arxiv.org/abs/2001.02069)
- **Implementation.** Qiskit Optimization `ADMMOptimizer(qubo_optimizer=…, continuous_optimizer=…, params=ADMMParameters(rho_initial, beta, factor_c, maxiter, three_block, tol))`.
  - It supports linear equality and inequality constraints.
  - Any `OptimizationAlgorithm` can be plugged in as the QUBO solver.
  - The tutorial example has only 3 binary variables. — [Qiskit docs 0.7.0](https://qiskit-community.github.io/qiskit-optimization/tutorials/05_admm_optimizer.html)
- **Package status.** PyPI `qiskit-optimization` 0.7.0 (2025-08-20), Apache-2.0. The GitHub repo `qiskit-community/qiskit-optimization` is **archived** (API `archived: true`, last push 2026-07-12). — [GitHub](https://github.com/qiskit-community/qiskit-optimization)

**Sharma & Lau, "Cutting Slack", [arXiv:2507.12159](https://arxiv.org/abs/2507.12159)**
- Compares dual ascent, bundle, cutting-plane and augmented-Lagrangian slack-free reformulations on TSP, MDKP and MIS.
- Finding: MDKP and TSP gain qubit savings "without compromising performance", while MIS gains little. Code not stated.

**Delacour, LagONN (Lagrange oscillatory neural network), [arXiv:2505.07179](https://arxiv.org/abs/2505.07179)**
- Oscillator phases plus Lagrange-multiplier oscillators, with inequalities handled through slack.
- Code: `corentindelacour/Lagrange-oscillatory-neural-network`, **GPL-3.0**, MATLAB, last push 2025-05-13. It targets Max-3-SAT only. — [GitHub API/repo](https://github.com/corentindelacour/Lagrange-oscillatory-neural-network)

### Inferences
- **Our single budget row.** For one budget row sᵀx ≤ W, Takabayashi/Ohzeki's slack-free μ ≥ 0 update is exactly the "price" update the audit already runs, but with a Polyak step instead of bisection. It keeps Q untouched: no sAsᵀ rank-1 term and no slack spins. SAIM's P‖g‖² term would add a dense rank-1 P·ssᵀ, which is cheap to apply matrix-free but densifies an explicit Q. That is consistent with the audit's finding that a large P "over-shrinks" the selection.
- **Per-slot capacities.** With up to m = 144 capacity rows (Σ_e d_{e,w}x_e ≤ K_w), SAIM-style λ updates are 144 scalars, each costing O(nnz(D)) per update. The MKP evidence (5.1% feasibility with only 5–10 constraints) suggests that the Lagrangian alone will return mostly infeasible samples, so a repair step, or EIM-style max(0, ·) terms (Q2), would still be needed.
- **Dual reuse.** The per-window capacity multipliers λ_w are structurally the same object as our α_w reweighting. A Lagrangian on "L_w ≤ τ" is the minimax dual, so SAIM/ALM gives a principled α-update rule (λ_w ← [λ_w + η(L_w(x) − τ)]₊).
- **ALM vs. plain Lagrangian.** Awai's ALM (small μ plus λ from averages) is the most robust choice when the inner solver is noisy, because averaging reduces the variance of the step. Our audit found a small fixed penalty was cheaper than bisection; ALM combines both.

### Gaps
- Awai, Takabayashi/Ohzeki (both papers) and Hagiwara released no code. Amplify AE is proprietary cloud.
- The exact 2D-PT knapsack results could not be extracted. The repository only contains the copy-constraint application, and whether the paper benchmarks QKP/MKP is `[UNVERIFIED]` (one search summary said so; the fetched HTML summary did not).
- None of these methods has been run above N ≈ 300 with constraints, and none against MILP time-to-solution.

---

## Q2. Native inequality handling: Fujitsu DA, Extended Ising Machine, Toshiba SQBM+, "constrained SB"

### Takeaway
- **The only published native inequality mechanism with precise semantics is the Extended Ising Machine (EIM).** It adds λ_k·max(0, r_k) to the energy, with r_k = Z_k·x + c_k. It runs on a Digital-Annealer-style rejection-free MCMC with replica exchange, and the simulator came privately from Fujitsu.
- **Everything is reimplementable in about 100 lines of numba.** The r_k are affine in x, so a single flip updates each r_k in O(1) and ΔE is exact. In our case every flip touches 1–3 windows.
- **Vendor features stay closed.** Fujitsu DA's inequality and one-hot features are cloud or SDK only (`dadk` is proprietary; `ommx-da4-adapter` needs an API token). Toshiba SQBM+ advertises a "QPLIB solver" for linearly constrained binary QPs with no penalty tuning, but its algorithm is undisclosed.
- **No open-source "constrained SB" was found.**

### Cited Findings

**Extended Ising Machine (EIM), Akishima, Tamura, Kudo, *JPSJ* 94, 095002 (2025), [arXiv:2508.06909](https://arxiv.org/abs/2508.06909)**
- **Energy.**
  - H(x) = −½ΣΣW_ij x_i x_j − Σ b_i x_i + Σ_k λ_k G_k(r_k), where r_k = Σ_i Z_{k,i}x_i + c_k and **G_k(r_k) = max(0, r_k)** for inequality constraints.
  - The dependent variables "are uniquely determined by the decision variables" and add no problem size.
  - For QKP: H = H_cost + λ_extend·max(0, Σw_i x_i − c), against the QUBO form λ_qubo(Σw_i x_i + Σ_j 2^j y_j − c)².
  - Source: [arXiv PDF](https://arxiv.org/pdf/2508.06909)
- **Engine and tuning.**
  - "MCMC with the rejection-free selection rule [Bortz–Kalos–Lebowitz; Rosenthal et al. 2021] and replica-exchange MC".
  - λ is chosen by grid search. The temperature ladder targets about 20% swap acceptance, with swaps every 10 MCMC runs.
  - At most 10⁶ iterations and 10 seeds, run on an Intel i7-13700 CPU (16 cores).
  - Source: [arXiv PDF](https://arxiv.org/pdf/2508.06909)
- **Results (100 QKP instances, n = 100–300).**
  - EIM solved every instance (all seeds except on one instance). The QUBO+slack formulation solved only 35 of the 60 instances at n = 200/300.
  - Average time-to-optimum is about 0.0097–2.94 s for EIM and about 0.50–40.4 s for QUBO. Taken from the reference: IHEA 1.18–3.59 s, **Gurobi 0.45–91.5 s**.
  - Gurobi's time is "the time required to guarantee optimality", while EIM stops when it hits the known optimum.
  - Source: [arXiv PDF](https://arxiv.org/pdf/2508.06909)
- **Why it works, per the authors.** In the QUBO form, "flipping any variable from a feasible solution results in an immediate constraint violation", whereas EIM "enables search without constraint violation". — [arXiv PDF](https://arxiv.org/pdf/2508.06909)
- **Code.** Not public ("We thank Fujitsu Limited for providing us with the extended Ising machine simulator"). The primary EIM algorithm papers are Yin et al., *JPSJ* 92, 034002 (2023) and Watanabe et al., *IEEE Access* 12, 14636 (2024), both cited as refs 7–8 in [arXiv PDF](https://arxiv.org/pdf/2508.06909) `[not read]`.

**Fujitsu Digital Annealer**
- **Constraint features.** Inequality-constraint separation (a λ per inequality) and one-way/two-way one-hot constraints are used in Kao et al. [arXiv:2311.05196](https://arxiv.org/abs/2311.05196), as already documented in `survey.md`.
- **Documentation.** The user guide at [portal.aispf.global.fujitsu.com](https://portal.aispf.global.fujitsu.com/apidoc/da/jp/da-guide-en.html) returned **HTTP 403**, so the internal mechanism is `[UNVERIFIED]`.
- **SDK.** `dadk` is "Fujitsu's proprietary software development kit", with a `BinPol` class that can reduce higher degree to QUBO. It is not on PyPI (404). — [Sci. Rep. power-flow paper via search](https://www.nature.com/articles/s41598-024-73512-7.pdf); PyPI check
- **Adapter.** `ommx-da4-adapter` (Jij, Apache-2.0, 0.1.1 on PyPI 2025-07-30, repo push 2026-09-14) sends OMMX instances to DA4 and needs `token` and `url`. The open PR #6 adds "One Hot Special Constraints". — [GitHub README](https://github.com/Jij-Inc/ommx-da4-adapter); [PR #6](https://github.com/Jij-Inc/ommx-da4-adapter/pull/6)
- **Public algorithm description.** The DA algorithm (parallel trial, i.e. evaluating all single flips at once; dynamic offset) is in Aramon et al., *Front. Phys.* 7:48 (2019) ([Frontiers](https://www.frontiersin.org/journals/physics/articles/10.3389/fphy.2019.00048/xml)). Its mathematics is analysed in [arXiv:2303.08392](https://arxiv.org/pdf/2303.08392).
- **Open "DA-like" codes (all small or toy).**
  - `simulated-annealing-variants` (PyPI 1.1.8, 2024-05-16): quasi-rejection-free and rejection-free SA for QUBO.
  - `LinoBugia/annealing-cop-approximator` (MSc thesis, MIT).
  - `AlexanderNenninger/QUBOBrute` (MIT, numba multi-threaded SA, last push 2023-03).
  - Sources: [PyPI](https://pypi.org/project/simulated-annealing-variants); [GitHub](https://github.com/LinoBugia/annealing-cop-approximator); GitHub API.
  - **None implements inequality or one-hot constraints** `[inference from descriptions]`.

**Toshiba SQBM+**
- **Product page claims.**
  - "QPLIB Solver: for linearly constrained quadratic binary programming problems. It supports QPLIB as input data format."
  - "A solver that can directly solve quadratic binary optimization problems with linear constraints … there is no need to incorporate linear constraints into QUBO and adjust penalty parameters."
  - A "PUBO solver" for cubic and quartic terms, and a Bayesian-optimization "parameter automatic adjustment function".
  - Deployment: AWS AMI and cloud images, plus on-prem FPGA (test marketing) and GPU (under development).
  - Scale: up to 1 B variables and 10 B non-zeros.
  - Sources: [Toshiba intro](https://www.global.toshiba/ww/products-solutions/ai-iot/sbm/intro.html); [Toshiba technologies](https://www.global.toshiba/ww/products-solutions/ai-iot/sbm/sbm-technologies.html)
- **Algorithm not disclosed.** Toshiba's 2025 public SB slides show constrained applications (portfolio basket selection with a cardinality and a delta-neutral constraint, N = 128; multi-object tracking) handled as **H = H_cost + c·H_penalty**. For tracking, SB is "execut[ed] twice while changing the penalty weight". — [Toshiba slides 2025-05-21](https://www.global.toshiba/content/dam/toshiba/jp/products-solutions/ai-iot/sbm/pdf/20250521_WSonRQC_PittU_SB_Toshiba.pdf) (pdftotext)
- **Open-source "constrained SB".** None found. Kanao & Goto extended SB to higher-order costs, *APEX* 16, 014501 ([arXiv:2211.09296](https://arxiv.org/abs/2211.09296)), not to constraints. The FPGA dSB with knapsack (Orlando et al., [arXiv:2510.12407](https://arxiv.org/abs/2510.12407)) remains repo-not-located (as in `survey.md`).

### Inferences
- **EIM is the best mechanism for our constraints.**
  - Budget: r_0 = sᵀx − W.
  - Per-slot capacity: r_w = (Dᵀx)_w − K_w, which the incremental L_w bookkeeping already tracks.
  - One-hot upper bound (at most one per group): r_g = Σ_{e∈g} x_e − 1.
  - Each flip changes 1–3 r_w, one r_0 and one r_g, so ΔE is O(deg) and exact. The audit's numba local search (`ls_*`) already holds these quantities, so adding λ_k·max(0, r_k) terms plus replica exchange and rejection-free selection turns it into an "open EIM" `[inference]`.
- **Exact one-hot.** Exact one-hot (exactly one) is better enforced by a swap move inside the group (a Kawasaki-style move that preserves feasibility) than by any penalty `[inference]`. DA's "one-way/two-way one-hot" features are the vendor version of this `[mechanism UNVERIFIED]`.
- **max(0, ·) cannot be used by SB/CIM directly.** It has no quadratic form, and the SB gradient would need a subgradient of max(0, r), i.e. a ReLU-gated field, which no public SB package supports `[inference]`. A matrix-free SB with a hinge-gated field λ·1[r_k > 0]·Z_k is easy to write but unpublished.

### Gaps
- Fujitsu's DA inequality semantics (hard vs. soft, how λ is used) are unverified because the documentation is 403. No legitimate open DA or EIM emulator exists.
- The algorithm inside SQBM+'s QPLIB solver is undisclosed.
- The EIM primary algorithm papers (Yin 2023; Watanabe 2024) were not read.

---

## Q3. p-bit / probabilistic-computing simulators with code; CPU versions; constraint support

### Takeaway
- **Camsari's OPUS Lab publishes MATLAB, Python and C++ research code on GitHub (`OPUSLab`).** The constraint-relevant repos are **2DPT** (MIT) and Delacour's **self-adaptive-IM** (GPL-3.0).
- **The Aadit et al. 2022 sparse Ising machine is FPGA hardware** with graph-colored parallel updates. Its companion code is MATLAB 3R3X/XORSAT work (GPL-3.0).
- **No maintained general-purpose CPU p-bit QUBO solver package exists.** A p-bit machine emulated in software is sequential Gibbs sampling, which is heat-bath SA, so dwave-samplers or OpenJij SA are functionally equivalent CPU substitutes `[inference]`.
- **The Camsari group's constraint results** (SAIM, 2D-PT, Potts "mean-field constraints") are all ≤ a few hundred to a few thousand variables.

### Cited Findings
- **Aadit et al., "Massively parallel probabilistic computing with sparse Ising machines,"** *Nat. Electron.* 5, 460–468 (2022), [arXiv:2110.02481](https://arxiv.org/abs/2110.02481).
  - Sparsification plus graph coloring gives flips/s that scale linearly with the number of p-bits, on about 5,000–10,000 p-bits (FPGA).
  - Sampling is 5–18× faster than optimized GPU/TPU and "up to 6 orders of magnitude" faster than CPU Gibbs.
  - It factors 32-bit semiprimes and beats competition SAT solvers by 4–700× on 3SAT.
  - Source: [arXiv abs](https://arxiv.org/abs/2110.02481) (summary); [Nat. Electron.](https://www.nature.com/articles/s41928-022-00774-2)
- **OPUSLab GitHub repos (GitHub API, 2026-09-28).**
  - `2DPT`: MIT, MATLAB, push 2025-08-04.
  - `XORSATwithpbits`: GPL-3.0, MATLAB, push 2024-09-25, "Codes and data for the 3R3X (XORSAT) problem with probabilistic bits".
  - `3DSpinGlassWithPbits`: MIT, Python, push 2025-11-06, companion to arXiv:2503.10302.
  - `PAOAwithPbits`: no license, C++, push 2026-03-29.
  - `SparseDeepBoltzmannMachines`: GPL-3.0, MATLAB.
  - `SparsifyDenseGraph`: no license, push 2025-06-04.
  - Source: [OPUSLab GitHub](https://github.com/OPUSLab); [OPUS publications](https://opus.ece.ucsb.edu/publications)
- **Callahan-Coray, Lee, Jiang, Camsari, "Restoring Sparsity in Potts Machines via Mean-Field Constraints,"** *npj Unconv. Comput.* 3, 50 (2026), [arXiv:2602.04200](https://arxiv.org/html/2602.04200).
  - "Mean-field constraints" replace dense pairwise constraint couplings with **dynamically updated single-node biases**, with native Potts/p-dit variables for one-hot groups.
  - On balanced partitioning (4elt, k = 32) the edge count drops about 10⁵× with quality comparable to all-to-all constraints.
  - Code not located.
  - Source: [OPUS publications](https://opus.ece.ucsb.edu/publications); [arXiv](https://arxiv.org/html/2602.04200)
- **Nikhar et al., "All-to-all reconfigurability with sparse and higher-order Ising machines"** (XORSAT with p-bits), [arXiv:2312.08748](https://arxiv.org/html/2312.08748v1). Companion code is presumably `OPUSLab/XORSATwithpbits` `[link inferred from repo description]`.
- **`nonizawa/GPU-pSAv`** (Onizawa et al., *Sci. Rep.* 2025; [arXiv:2601.14476](https://arxiv.org/html/2601.14476)).
  - p-bit SA with device-variability models (pSA, TApSA, SpSA) on Gset MAX-CUT with 800–20,000 nodes.
  - CUDA via PyCUDA, plus a single-threaded Python CPU baseline. About 100× GPU speedup over CPU. No constraints.
  - Repo push 2024-10-07, license NOASSERTION. — [arXiv HTML](https://arxiv.org/html/2601.14476); GitHub API
- **`IBM/p-kit`.** BSD-3-Clause, Python, push 2026-09-23. It simulates "probabilistic circuits" (invertible p-bit logic via Gibbs sampling) and has no official release. — [GitHub](https://github.com/IBM/p-kit); GitHub API
- **Other recent p-bit work (no code checked).** "Programmable probabilistic computer with 1,000,000 p-bits" [arXiv:2606.25313](https://arxiv.org/pdf/2606.25313); "Unified performance-cost landscape of parallel p-bit Ising machines" [arXiv:2604.01564](https://arxiv.org/pdf/2604.01564); p-bits for MIMO detection with 2D-PT [arXiv:2601.09037](https://arxiv.org/html/2601.09037v1).

### Inferences
- **The p-bit update is heat-bath Gibbs.** m_i = sign(tanh βI_i + U) is heat-bath Gibbs with local field I_i. On a CPU the p-bit "machine" is therefore just SA or PT, and the only hardware-specific trick (graph-colored parallel updates) needs a sparse coupling graph.
- **Our Q is not sparse in that sense.** Our Q = D diag(α) Dᵀ is a union of window cliques, so chromatic parallelism is poor. The equivalent CPU trick is our O(1)-per-flip window bookkeeping `[inference]`.
- **Mean-field constraints are what we should borrow.** The dynamically updated per-node bias from "mean-field constraints" (Potts MFC) is essentially a per-constraint Lagrange price applied as a linear field. That is the same structure as the audit's μ·s term, which supports keeping capacity constraints as linear fields rather than dense penalties `[inference]`.

### Gaps
- There is no CPU-optimized, multi-threaded, general QUBO p-bit package with constraints. The GPU-pSAv license is unclear, and the Aadit 2022 FPGA design has no public CPU port.

---

## Q4. CIM (CAC/AHC/CFC) and SB variants on constrained problems (new beyond survey.md)

### Takeaway
- **Nothing new and runnable exists.** Constrained results for CIM-family and SB-family solvers are still penalty-based and small; `survey.md` already covers Zeng 2024 (unconstrained) and Ichikawa 2026 (SQBM+ with composition penalty).
- **The newest relevant items are:**
  - Toshiba's commercial "QPLIB solver" (Q2);
  - "Tabu-Enhanced SB" (*Commun. Phys.* 2026, not fetched);
  - 2025 benchmarks in which CIM and SB rank below other solvers on assignment-type QUBOs.
- **Our own audit is the most relevant constrained CPU data point:** the audit's SB/CAC arms trailed SA and LP+repair.

### Cited Findings
- **Tabu-Enhanced Simulated Bifurcation**, *Commun. Phys.* (2026), [nature.com/articles/s42005-026-02538-2](https://www.nature.com/articles/s42005-026-02538-2). Page behind the Nature auth redirect, so method, constraints and code are `[UNVERIFIED]`.
- **2025 QUBO solver benchmark, [arXiv:2506.04596](https://arxiv.org/pdf/2506.04596).** Per the search-snippet summary, on an assignment-type QUBO the proposed "QIS3" solver reaches −5644 against −5640 for SA (D-Wave Neal) at 1,000 variables, while SB reaches −5624 and CIM −5504. `[numbers from search snippet; paper not read; vendor-authored]`
- **Toshiba SB constrained use-cases** are penalty-weight runs (portfolio N = 128; tracking run "twice while changing the penalty weight"). — [Toshiba slides](https://www.global.toshiba/content/dam/toshiba/jp/products-solutions/ai-iot/sbm/pdf/20250521_WSonRQC_PittU_SB_Toshiba.pdf)
- **Higher-order SB** (Kanao & Goto, *APEX* 16, 014501): higher-order SB beats second-order SB with auxiliary spins, and SA applied directly to third-order costs. — [search summary of IOPscience](https://iopscience.iop.org/article/10.35848/1882-0786/acaba9); [arXiv:2211.09296](https://arxiv.org/abs/2211.09296)
- **Our own audit (from AUDIT.md, not new research).**
  - At n = 1k, MQ dSB and bSB reach 11.9–15.2% of headroom and CAC 21%. The `simulated-bifurcation` package gets 58%, and cim-optimizer extAHC collapses to x = 0.
  - A small fixed penalty (k = 0.1) beat the bisected Lagrangian with mfsb, while k = 10 was worse than repair-only.
  - Source: `ising_followup/audit/AUDIT.md` §4–5.

### Inferences
- The CIM and SB families have no native constraint mechanism in any public code. The Lagrangian wrappers from Q1 apply to them unchanged, since they only need a new h each outer iteration. Their weakness on our instance (outputs that are nearly empty or far over budget) is a scaling problem with h and ξ, not a constraint-mechanism problem `[inference from audit]`.

### Gaps
- Tabu-Enhanced SB details and code were not verified (paywall).
- No constrained CAC/CFC result above toy size was found in 2024–2026.

---

## Q5. Parallel tempering, population annealing, MQLib, tabu / path relinking: CPU scale on 10⁴–10⁵ sparse QUBOs

### Takeaway
- **The mature CPU codes run on unconstrained QUBO or Max-Cut:**
  - MQLib (37+ heuristics including Burer2002, Glover2010 tabu, Festa GRASP + path relinking; sparse edge list; C++; MIT);
  - dwave-samplers / dwave-tabu (MST2 multistart tabu);
  - PySA (numba PT on a **dense** matrix);
  - `libtsqubo` (sparse tabu, header-only C).
- **Population annealing** has only spin-glass research code (`jcallaham/population-annealing`, GPL-3.0, 2017, OpenMP).
- **None handles constraints except by penalty**, and all need an explicit Q. At n = 10⁵ with all 144 windows the explicit Q has about 3×10⁸ nnz (from `survey.md` §4); the audit's own instance had about 1.1×10⁹ nnz at 200k. That fits in RAM, but at 10⁵ nodes MQLib's default time budget per run is clamped to 1,200 s.

### Cited Findings
- **MQLib** (Dunning, Gupta, Silberholz, *INFORMS J. Comput.* 30(3), 2018). GitHub `MQLib/MQLib`, MIT, push 2025-11-12.
  - CLI: `bin/MQLib -fQ file -h <HEUR> -r <seconds> -ps -s <seed>`, or `-hh` for the ML hyper-heuristic.
  - The default runtime limit is 0.59·n s, clamped to [120, 1200] s.
  - File format: `n m` followed by `a b w` lines (a sparse list).
  - QUBO instances are reduced to Max-Cut when a Max-Cut heuristic is chosen.
  - The fitted-model directory lists ALKHAMIS1998, BEASLEY1998SA/TS, BURER2002, DUARTE2005, FESTA2002G/GPR/GVNS/GVNSPR/VNS/VNSPR (the "PR" variants are **path relinking**), GLOVER1998a, GLOVER2010, HASAN2000GA/TS, KATAYAMA2000/2001, LAGUNA2009HCE, LODI1999, LU2010, MERZ1999GLS, MERZ2002 variants, and more.
  - No multithreading is mentioned. Build is `make` with g++.
  - Sources: [README](https://github.com/MQLib/MQLib), [bin/README](https://github.com/MQLib/MQLib/blob/master/bin/README.md) (raw fetch), GitHub tree API
- **PySA** (NASA QuAIL). GitHub `nasa/pysa`, Apache-2.0, push 2025-05-16. **Install with `pip install git+https://github.com/nasa/pysa`.** PyPI `pysa` 0.3b5 (2013) is an unrelated "Reverse your Servers Configuration" package.
  - `Solver.metropolis_update(num_sweeps, num_reads, num_replicas, temps, parallel=True, use_pt=True, …)` runs PT with geometric temperatures; the default is 4 replicas.
  - It checks `problem.shape == (n_vars, n_vars)`, so the input is a **dense** matrix. Parallelism comes from numba.
  - Modules also include annealed importance sampling (`ais.py`), branching, WalkSAT and DPLL.
  - Sources: [README](https://github.com/nasa/pysa); `pysa/sa.py` (raw fetch); PyPI API
- **dwave-tabu.** PyPI 0.5.0 (2022-11-25), Apache-2.0, a "C/C++ implementation of the MST2 multistart tabu search algorithm". The algorithm is now shipped inside `dwave-samplers` 1.8.0 (2026-06-18). — [GitHub](https://github.com/dwavesystems/dwave-tabu); PyPI API
- **qbsolv** (tabu plus decomposition, with a path-relinking option) is **archived** (GitHub API `archived: true`, push 2022-04-14). — [GitHub](https://github.com/dwavesystems/qbsolv)
- **`rliang/libtsqubo`.** MIT, header-only C, push 2025-02-26: "Tabu Search with optimized iteration time using sparse matrix formats". It accompanies Liang et al., "Data structures for speeding up Tabu Search when solving sparse QUBO problems," *J. Heuristics* (2022). — [GitHub](https://github.com/rliang/libtsqubo); [Springer](https://link.springer.com/article/10.1007/s10732-022-09498-0)
- **SATPR** (scatter search + adaptive-tenure tabu + path relinking, multi-threaded, "open-source"), *Comput. Oper. Res.* (2025), [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0305054825001650). A GitHub search for "SATPR QUBO" found **no repo** `[code UNVERIFIED]`.
- **Population annealing.**
  - `jcallaham/population-annealing`: GPL-3.0, C++/OpenMP, last push 2017-09, spin glasses. — [GitHub](https://github.com/jcallaham/population-annealing)
  - Population annealing vs. SA hardness study on diluted Ising models: [arXiv:2501.07638](https://arxiv.org/pdf/2501.07638) `[code not checked]`.
  - GPU PA: [arXiv:1703.03676](https://arxiv.org/pdf/1703.03676).
- **tamc** (Rust PT plus isoenergetic cluster moves). No license, push 2023-08. — GitHub API (as in survey.md)

### Inferences
- **Sizing on our machine.**
  - MQLib and dwave-samplers can load the explicit Q at n ≈ 10⁵ (about 3×10⁸ nnz ≈ 2.5–5 GB in CSR, per the `survey.md` sizing).
  - The audit measured dwave SA at about 108 s per call for 16 reads × 1000 sweeps at n = 10⁴, and 1–12 calls in 40 min at 5×10⁴. The explicit-Q per-flip cost (O(degree) ≈ thousands) is the bottleneck, not the algorithm.
  - PySA's dense input rules it out beyond about 5×10⁴ (a 10 GB float32 matrix).
- **The fair classical control is our custom sampler.** It is a numba SA/PT/tabu on the *true* objective with O(1) window-local updates and hard budget and capacity constraints (the audit's `ls_*` extended with replica exchange). MQLib's value is as an "off-the-shelf QUBO heuristic ceiling" on the pegged sub-problem (n ≲ 10⁴–10⁵), not as the production solver.

### Gaps
- No published MQLib or PySA timings on 10⁵-variable *constrained-penalty* QUBOs were found.
- SATPR code location is unknown.
- Whether MQLib is thread-safe for parallel instances (24 independent seeds) was not checked; running separate processes is the safe route.

---

## Q6. HUBO solvers (if one-hot or capacity terms need higher order)

### Takeaway
- **None of our constraints needs higher order.** Budget, capacity and one-hot penalties are quadratic, and EIM-style max(0, r) is handled natively by an MCMC sampler rather than by a polynomial. HUBO would only enter if the min-max objective were written as a high-order polynomial.
- **Open CPU HUBO options exist if needed:** OpenJij (native HUBO SA, Apache-2.0, 0.12.2) and pyqbpp/QUBO++ (HUBO modelling plus the EasySolver and ABS3 solvers). pyqbpp is **limited to 100 variables without a license key**.

### Cited Findings
- **OpenJij** "can solve HUBO directly using simulated annealing without converting HUBO to QUBO". — [OpenJij HUBO tutorial](https://tutorial.openjij.org/en/tutorial/002-HuboSolver.html)
  - Repo: `OpenJij/OpenJij`, Apache-2.0, push 2026-08-25. PyPI 0.12.2 (2026-08-19), Python ≥ 3.10, < 3.15. — GitHub/PyPI API
  - Suzuki (2025), [arXiv:2511.17245](https://arxiv.org/abs/2511.17245), adds SA for quadratic and higher-order unconstrained **integer** problems (an "optimal-transition Metropolis" method), implemented in OpenJij.
- **OMMX / JijModeling pathway.** `ommx` 2.8.0 and `ommx-openjij-adapter` 2.8.0 (2026-09-11) convert constrained models (Indicator, OneHot and SOS1 are "lowered") into penalty form with a uniform or per-constraint penalty magnitude. Adapters exist for HiGHS, SCIP, Gurobi, Python-MIP, D-Wave, Fixstars Amplify and DA4. — [PyPI ommx-openjij-adapter](https://pypi.org/project/ommx-openjij-adapter/3.0.0b6/); [Jij-Inc GitHub](https://github.com/Jij-Inc); PyPI API
- **pyqbpp (QUBO++, Koji Nakano).** PyPI 2026.9.25. It offers "Symbolic construction of QUBO/HUBO expressions" and "Easy Solver, Exhaustive Solver, ABS3", on Linux x86_64/arm64 plus CUDA. "Without a license key, the number of binary variables is limited to 100." — [PyPI JSON description](https://pypi.org/project/pyqbpp/)
  - ABS3 (GPU) and EasySolver were the classical baselines against which an IBM-Heron HUBO pipeline was benchmarked ("competitive with strong classical solvers running on 128 vCPUs or 8 NVIDIA A100 GPUs"). — [arXiv:2603.13607](https://arxiv.org/abs/2603.13607)
- **Toshiba SQBM+** has a PUBO solver for cubic and quartic terms (cloud or proprietary). — [Toshiba intro](https://www.global.toshiba/ww/products-solutions/ai-iot/sbm/intro.html)
- **dimod** 0.12.22 (Apache-2.0) provides `make_quadratic` HUBO→QUBO reduction. `dadk`'s `BinPol.reduce_higher_degree_to_qubo` is proprietary. — PyPI API; [Sci. Rep. power-flow](https://www.nature.com/articles/s41598-024-73512-7.pdf) `[make_quadratic name from memory, UNVERIFIED]`
- **Walsh–Fourier slack-free penalty projection.** Lee, Nagarajan, Gerlach, Mücke, Krishnamoorthy, Piatkowski (QCE 2026), [arXiv:2607.26349](https://arxiv.org/abs/2607.26349). It projects the constraint penalty onto hardware-native quadratic Walsh characters with "no per-constraint penalty coefficients to tune". Code: `lklee9/topology-aware-walsh-fourier-penalization`, MIT, push 2026-05-04.

### Inferences
- **HUBO is unnecessary for our formulation** `[inference]`. It would only matter for a cubic "min-max via products" encoding, and the epigraph plus Lagrangian route is strictly cheaper.
- **pyqbpp's 100-variable free limit** makes it unusable at our scale without a trial license.

### Gaps
- OpenJij's HUBO SA performance at 10⁵ variables was not checked.

---

## Q7. Evidence: which methods won on constrained knapsack / assignment / scheduling QUBOs vs. Gurobi

### Takeaway
- **The only "Ising ≥ Gurobi" claims on constrained binary problems come from native or Lagrangian constraint handling on small dense QKPs (n ≤ 300).** Examples are EIM (time-to-known-optimum against Gurobi's time-to-proof) and Amplify AE plus post-processing (Ohno 2024, "comparable").
- **On realistic scheduling instances** (transport robots, 2k–23k variables), penalty-QUBO on DA or D-Wave found "no general advantage" over Gurobi. Only the DA hybrid was competitive on some of the largest instances, where Gurobi could not prove optimality in 3,600 s.
- **Takabayashi et al. found greedy beats Lagrangian-QA on QKP.** Our audit found LP + repair beats all Ising arms at n ≥ 10⁴.

### Cited Findings
- **EIM on QKP** (i7-13700 CPU): all 100 instances solved, EIM 0.0097–2.94 s against Gurobi 0.45–91.5 s. The Gurobi number is time to guarantee optimality, and EIM stops at the known optimum. — [arXiv:2508.06909](https://arxiv.org/pdf/2508.06909)
- **SAIM beats PT-DA and penalty-SA on QKP** (accuracy and sweep counts). MKP accuracy is comparable to a GA. There is no MILP timing race. — [arXiv:2501.04971](https://arxiv.org/pdf/2501.04971)
- **Ohno, Shirai, Togawa**, "Toward practical benchmarks of Ising machines: QKP" (*IEEE Access* 12, 97678, 2024): on large QKP instances, "the Amplify Annealing Engine with proposed post-processing achieved comparable performance against Gurobi or other heuristic methods tailored for the QKP" (search-result summary). — [arXiv:2403.19175](https://arxiv.org/html/2403.19175v1)
- **Transport robot scheduling** (Leib et al.; PMC10618446).
  - Solvers: Fujitsu DA (≤ 8,192 variables), DA hybrid, D-Wave Leap BQM and Gurobi, on 161 "minor" instances (2,071–8,080 variables) and 99 "major" instances (10,822–22,692 variables).
  - Constraints were penalty terms in the QUBO.
  - "No general advantage of the quantum and quantum-inspired solvers was found", but "QU-FDAh shows an advantage on some bigger instances when compared to [Gurobi] on a similar time scale".
  - Source: [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10618446/)
- **Takabayashi/Ohzeki MBQP (2026):** faster time-to-target than "the commercial solver" at the upper end of tested sizes (abstract only, sizes unknown). — [arXiv:2607.21286](https://arxiv.org/abs/2607.21286)
- **Takabayashi/Goto/Ohzeki QKP (N ≤ 64):** greedy was more accurate than the Lagrangian or Ohzeki sampling methods. — [arXiv:2411.06901](https://arxiv.org/html/2411.06901v1)
- **Awai 2026** compares only augmented Lagrangian against penalty (about 10× better TTε). There is no MILP. — [arXiv:2606.24241](https://arxiv.org/html/2606.24241)
- **QOBLIB** (Koch et al., *Nat. Comput. Sci.* 2026).
  - Baselines: Gurobi 12.0.1 on 128 threads with a 7,200 s limit for the MIP formulations, and ABS2 on 4× A40 GPUs with a 7,200 s limit for the QUBO formulations.
  - 1,260+ instances with 20 to 3 M+ variables, including assignment and scheduling-type classes.
  - Sources: [search summary](https://thequantuminsider.com/2025/04/10/a-decathalon-of-difficulty-working-group-benchmarks-the-limits-of-quantum-optimization/); [Nat. Comput. Sci.](https://www.nature.com/articles/s43588-026-00991-1); [GitHub ZIB-AOPT/QOBLIB](https://github.com/ZIB-AOPT/QOBLIB)
  - Per-class winners were not extracted `[gap]`.
- **Fujimoto, Yamashita, Tanaka, Ising-machine-assisted LNS (LNS-VT)**, [arXiv:2607.05169](https://arxiv.org/abs/2607.05169). Solving large constrained problems "directly" degrades solution quality, so the Ising machine is used only on feasibility-preserving LNS sub-problems (VRP with 300 sites; quadratic multiple knapsack). About 10% better than the prior LNS. No Gurobi comparison.

### Inferences
- **The pattern across sources** `[inference]`:
  1. Native or Lagrangian constraint handling beats penalty QUBO by 1–4 orders of magnitude in samples or time on knapsack-type problems (EIM, SAIM, ALF).
  2. The winning regime is dense quadratic objectives with 1–10 linear constraints and n ≤ 300.
  3. At realistic n with many constraints, MILP or LP-based pipelines win or tie, and Ising machines are best used inside decomposition or LNS.
- **Our problem sits outside the winning regime:** low-rank, with a linear-ish min-max, about 145 rows and n = 10⁴–10⁵. This agrees with AUDIT.md, where LP round + repair (+ LS) dominated.

### Gaps
- No head-to-head exists of any Lagrangian or native-inequality Ising method against Gurobi at n ≥ 10⁴ with more than 10 constraints.
- QOBLIB per-class results (e.g., whether ABS2 ever beats Gurobi on constrained classes) were not extracted.

---

## Inventory table (new items only; see survey.md for SB/MQ/FEM/qqa/cim/dwave/OpenJij basics)

| Solver / method | Code URL | License | Last release / push | Lang / deps | Install | Input | Linear h | Constraint handling | Largest published + time | CPU @ 10⁴–10⁵ | Fit for our E(x) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SAIM (Delacour DATE'25) | [github](https://github.com/corentindelacour/self-adaptive-IM) | GPL-3.0 | push 2025-01-10 | MATLAB | clone | dense W, h, A, b (QKP/MPS files) | yes | Lagrange λ ← λ+ηg(x), plus penalty P=2dN; binary slack | QKP n=300 (+slack), 200 M MCS; MKP n=250, M=10 | No: dense O(N²)/sweep; reimplement | High as an **outer-loop recipe** (port to numba/our mfSB) |
| 2D-PT (Delacour+ PRE'25) | [github](https://github.com/OPUSLab/2DPT) | MIT | push 2025-08-04 | MATLAB | clone | sparse J, h (copy-constraint graphs) | yes | penalty ladder as 2nd PT axis; P-swap min(1, e^{βΔPΔg}) | sparsified Wishart N≤100 logical (~300 spins) | Algorithm yes (if we write it); repo is app-specific | Medium-high: removes penalty tuning for budget/capacity |
| ALF / ALM (Awai+ JPSJ'26) | none | — | — | (Amplify AE cloud) | — | — | — | ALM: λ←λ−μ⟨g⟩, μ←aμ; log slack | QKP n=300, 1 s/run ×50 | trivially reimplementable | High (robust variant of our μ loop) |
| Ohzeki HS / subgradient (Takabayashi+ '24) | none | — | — | (OpenJij SA/SQA) | — | — | — | slack-free μ≥0, Polyak step | QKP N≤64; greedy won | reimplementable | High for budget row; weak evidence |
| EIM (Akishima+ JPSJ'25; Fujitsu) | **not public** | — | — | Fujitsu simulator | — | dense W, b + Z, c | yes | **native λ·max(0, Zx+c)**, rejection-free MCMC + RE | QKP n=300, ≤2.94 s (i7) | reimplementable in numba, O(1)/flip for us | **Highest**: exact budget + slot capacity without slack |
| Fujitsu DA ineq/one-hot | cloud; `dadk` proprietary; [ommx-da4-adapter](https://github.com/Jij-Inc/ommx-da4-adapter) | proprietary / Apache adapter | adapter 0.1.1 (2025-07-30) | Python client | `pip install ommx-da4-adapter` + token | OMMX | yes | inequality λ-separated; one-way/two-way one-hot `[mechanism UNVERIFIED]` | 8,192 (DA) / hybrid larger | cloud only | Out of scope (off-prem) |
| Toshiba SQBM+ QPLIB solver | vendor | proprietary | — | cloud / AMI | — | QPLIB | yes | "no need to … adjust penalty parameters" `[algorithm undisclosed]` | "up to 1B variables" (QUBO) | cloud/AMI | Out of scope |
| Qiskit ADMMOptimizer (Gambella–Simonetto) | [github (archived)](https://github.com/qiskit-community/qiskit-optimization) | Apache-2.0 | 0.7.0 (2025-08-20) | Python, qiskit | `pip install qiskit-optimization` | QuadraticProgram (LP-like) | yes | ADMM split: QUBO block + convex block; eq/ineq | toy (3 binaries) | Python overhead; wrap own QUBO solver | Low-medium (conceptual template only) |
| MQLib | [github](https://github.com/MQLib/MQLib) | MIT | push 2025-11-12 | C++ | `git clone … && make` | sparse `a b w` list | yes (diag) | none | 3,296 instances (paper) `[count UNVERIFIED]`; runtime cap 1200 s | yes with explicit Q ≤ ~3e8 nnz | Baseline ceiling on pegged sub-problem |
| PySA (NASA) | [github](https://github.com/nasa/pysa) | Apache-2.0 | push 2025-05-16 | Python + numba | `pip install git+https://github.com/nasa/pysa` | **dense** n×n | diag | none | — | ≤ ~5×10⁴ (dense) | PT baseline on sub-problem only |
| libtsqubo | [github](https://github.com/rliang/libtsqubo) | MIT | push 2025-02-26 | C header | copy `tsqubo.h` | sparse | yes | none | — | yes (sparse) | Tabu baseline |
| dwave-tabu (in dwave-samplers) | [github](https://github.com/dwavesystems/dwave-tabu) | Apache-2.0 | 0.5.0 (2022); samplers 1.8.0 (2026-06-18) | C++/Python | `pip install dwave-samplers` | BQM | yes | none | — | audit: 305 s at n=1k (4×2 s timeouts ×40 calls) | Baseline |
| Population annealing | [github](https://github.com/jcallaham/population-annealing) | GPL-3.0 | push 2017-09 | C++/OpenMP | make | spin-glass lattices | — | none | — | not general QUBO | Not recommended |
| OpenJij HUBO / integer SA | [github](https://github.com/OpenJij/OpenJij) | Apache-2.0 | 0.12.2 (2026-08-19) | C++/Python | `pip install openjij` | dict / BQM / HUBO | yes | none (penalty via OMMX adapter) | — | yes | Only if HUBO needed (it isn't) |
| pyqbpp (QUBO++) | [qubo-plus.github.io](https://qubo-plus.github.io/python/) | proprietary (license key) | 2026.9.25 | C++/Python (+CUDA) | `pip install pyqbpp` | symbolic | yes | modelling helpers | — | **≤100 vars w/o key** | No |
| p-bit sims (GPU-pSAv, IBM p-kit, OPUSLab repos) | [GPU-pSAv](https://github.com/nonizawa/GPU-pSAv), [p-kit](https://github.com/IBM/p-kit), [OPUSLab](https://github.com/OPUSLab) | NOASSERTION / BSD-3 / mixed | 2024-10 / 2026-09 / 2024–2026 | CUDA+Python / Python / MATLAB | clone | Gset MaxCut / circuits | yes | none (except 2DPT, SAIM) | MaxCut 20k (GPU) | CPU = plain Gibbs SA | No added value over our SA |
| Walsh–Fourier slack-free penalty | [github](https://github.com/lklee9/topology-aware-walsh-fourier-penalization) | MIT | push 2026-05-04 | Python | clone | constrained binary | yes | projected quadratic penalty, no per-constraint weights | QA-scale | untested | Low (QA embedding focus) |

## Overall fit judgement for E(x) = xᵀD diag(α)Dᵀx + cᵀx, subject to sᵀx ≤ W, one-hot, and slot capacities `[inference, grounded in the findings above]`
1. **Best mechanism: an open reimplementation of the EIM energy inside our numba sampler.**
   - Energy: E(x) + λ₀·max(0, sᵀx − W) + Σ_w λ_w·max(0, (Dᵀx)_w − K_w), with one-hot groups kept exact by in-group swap moves.
   - Engine: rejection-free selection plus replica exchange.
   - Update cost is O(1) per flip because each episode touches 1–3 windows.
   - This matches the only published evidence of large gains over penalty-QUBO (EIM on QKP) and needs no Q.
2. **Wrap it with 2D-PT or ALM to remove the λ tuning.** Either use a penalty axis in PT (2D-PT's P-swap rule) or an augmented-Lagrangian outer update (Awai). Per-window λ_w then doubles as the minimax dual, i.e. a principled replacement for the audit's heuristic α-reweighting.
3. **Keep SAIM/Ohzeki-style linear-price updates as a plug-in for matrix-free SB** (mfSB, MQ-dSB). These only change h per outer iteration. Evidence says the Lagrangian alone gives low feasibility with many constraints (MKP: 5.1%), so the shared repair stays.
4. **Baselines:** MQLib, libtsqubo and dwave-samplers on the explicit penalty-QUBO of a pegged sub-problem; LP round + repair and HiGHS MILP as the reference that, per AUDIT.md and the transport-robot study, is expected to win at n ≥ 10⁴.
