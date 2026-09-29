# Swappable QUBO/Ising selectors: concrete formulations for Baleen episode selection (cache-capacity coupling, multiple-choice admission+prefetch, same-block logic, peak balancing)

Scope note: this file avoids repeating material already in `lit_review_qubo/REPORT.md` (knapsack slack / unbalanced / Lagrangian budget handling; epigraph and sum-of-squares min-max; low-rank matrix-free SB) and `ising_followup/survey.md` §5 (min-max / NPP / load-balancing Ising table). Those are cross-referenced, not re-cited. Notation used below for our instance: episodes e = 1..n (n = 10^4–10^5), ten-minute windows w = 1..144, s_e = flash bytes written by e, d_{e,w} = DT saved by e in window w, o_{e,t} = bytes e occupies in cache during slot t (s_e if e is resident in t, else 0), cache capacity Cap = 366 GB, write budget W.

Search coverage: roughly 20 tool calls across arXiv, IEEE, SciTePress, IEEE Access (via INSPIRE mirror), Springer, and the GitHub API. Primary texts that I extracted and read: arXiv 2312.14448 (HTML), Güney–Ehrenthal–Hanne ICAART/QAIO 2025 (PDF), Güney–Ehrenthal IEEE Access 2026 (PDF), Borrajo et al. QKP transformations (PDF), and Awasthi et al. arXiv 2301.05750 (PDF). For everything else I saw only the abstract, which is marked where it matters.

## Q1. Cache-capacity coupling: QUBO models where time-overlapping items compete for per-slot/per-node capacity

### Takeaway
The only published QUBO for cache placement with a per-node capacity that I could verify is the ISTN caching paper (arXiv 2312.14448). It uses one slack-encoded squared penalty per cache node and was solved at toy scale: 5 contents and 2 caches. No published QUBO models *time-slotted* cache occupancy, meaning items with lifetimes competing per time slot. The closest published algebra is the multidimensional knapsack (MDKP) QUBO, with one squared slack penalty per dimension. It maps directly to "occupancy per slot ≤ Cap" if each of the 144 slots is treated as a knapsack dimension. It captures nothing an LP cannot also express linearly.

### Cited Findings
- **ISTN joint caching + power (Zhang, Gong, Fan, Wang, Han, Guo; arXiv 2312.14448; IEEE TNSE, DOI 10.1109/TNSE.2024.3435444).**
  - Variables: binary cache placement x_{f,m} ∈ {0,1}^{F×M} (content f cached at BS or satellite m), binary association z_{n,m}, and continuous power p_{n,m}.
  - Capacity: Σ_f x_{f,m} d_f ≤ F_m for every m. In the QUBO it becomes f_Q^{(C1)} = Σ_m ξ_{1,m} (Σ_f x_{f,m} d_f − F_m + Σ_{l=0}^{l̄_{1,m}} 2^l s_{1,m})², i.e. binary-expanded slack, one block per node.
  - Decomposition: the problem is split by a hybrid quantum-classical generalized Benders decomposition (HQCGBD). The binary master problem goes to D-Wave. The continuous Benders variable φ is binarized with U bits over positive and negative powers of 2, and each Benders cut becomes a squared slack penalty ξ_4(ℒ(·) − φ̄(w) + Σ 2^l s_4)².
  - Instance: F = 5 contents, 1 LEO satellite + 1 terrestrial BS, N = 10 users (a "small-scale" proof of concept). Solver: the D-Wave hybrid solver. Reported gains are fewer Benders iterations (237 for 5-cut vs 828 for classical Benders) and up to 98.31% less "solver accessing time". No solution-quality gap vs Gurobi is reported for a larger instance.
  - Code: none linked (Python 3.7 + Mosek/Gurobi/D-Wave SDK mentioned). — [arXiv 2312.14448 HTML](https://arxiv.org/html/2312.14448); [abs](https://arxiv.org/abs/2312.14448)
- **Edge node placement + workload allocation (Do, Trieu, Nguyen; arXiv 2306.01159).**
  - The MILP is decomposed into a QUBO (binary placement) and an LP subproblem (continuous workload), with QAOA as the quantum solver.
  - The exact energy terms, capacity handling and sizes were not extracted (abstract only). **[UNVERIFIED details]** — [arXiv 2306.01159](https://arxiv.org/abs/2306.01159)
- **6G edge service placement with "quantum-centric optimisation"** on real hardware (IEEE Commun. Lett. 2025). The placement is turned into a QUBO with penalty parameters. Terms and sizes were not extracted. **[UNVERIFIED details]** — [PDF (CERC)](https://cerc-ngct.ca/wp-content/uploads/2025/03/J-2025-IEEE-COML-Optimal-Service-Placement-for-6G-Edge-Computing-with-Quantum-Centric-Optimisation-in-Real-Quantum-Hardware.pdf)
- **BALANCE (Rajpurohit, Kelley, Wang, Ramamoorthy; IEEE WCNC 2025; arXiv 2509.19616).**
  - A QUBO for per-segment bitrate allocation under a data cap. The cap is a single knapsack-type budget, which is structurally the same as our write budget W.
  - It compares slack variables with a "Dynamic Penalization Approach" (DPA) and reports that DPA "consistently outperforms the Slack Variable Method, delivering more valid and optimal solutions as data limits increase". Exact terms, sizes and code were not in the abstract. **[UNVERIFIED details]** — [arXiv 2509.19616](https://arxiv.org/abs/2509.19616)
- **MDKP QUBO (Güney & Ehrenthal, IEEE Access 14:66699–66710, 2026, DOI 10.1109/ACCESS.2026.3682459).**
  - Each capacity row Σ_i w_{id} x_i ≤ W_d gets binary slack y_{td} with a binary expansion of the residual capacity and a squared penalty λ_K P_K(x,y).
  - The resulting couplings are of type x_i x_j, x_i y_{td} and y_{td} y_{t'd'}.
  - Sufficient bound: λ_K ≥ R* = max revenue.
  - Instances are tiny: 12 logical qubits (N = 4, D = 2) and 23 logical qubits (N = 7, D = 4). They were run on D-Wave, QAOA (Qiskit/IonQ) and Gurobi.
  - The authors say the QUBO size is dominated by the capacity slack. — [IEEE Access PDF via INSPIRE](https://inspirehep.net/files/6dc97dfdba01eae229daa641fac62284)
- **Multiple-knapsack QUBO (Awasthi et al., "Quantum Computing Techniques for Multi-Knapsack Problems", SAI 2023, LNNS 739, arXiv 2301.05750).**
  - Energy: H = A·H_single + B·H_capacity + C·H_obj, where
    - H_capacity = Σ_i (Σ_j w_j x_{i,j} + Σ_{b=0}^{⌊log2 c_i⌋} 2^b y_{i,b} − c_i)²
    - H_obj = −Σ v_{i,j} x_{i,j}
  - Penalty rule: A/C, B/C > max v. They chose C = 1 and A = B = 2·max v.
  - Largest instance: 19 qubits (2 knapsacks × 6 items + slack).
  - Results: SA and iterative heuristic solvers found the optimum on every instance. D-Wave Advantage 6.1 reached 95.4 ± 7.4% of optimum on the largest instance.
  - Code: [github.com/QutacQuantum/Knapsack](https://github.com/QutacQuantum/Knapsack). The GitHub API reports **no license**, 5 stars, last push 2025-11. — [arXiv 2301.05750](https://arxiv.org/abs/2301.05750)
- **QAL-BP bin packing (Cellini, Macaluso, Lombardi; arXiv 2309.12678).**
  - Uses x_{ij} (item → bin) and y_j (bin used). The capacity constraints are folded in with augmented-Lagrangian terms, with **no slack variables**, and the multipliers are estimated analytically.
  - Tested on a real annealer vs SA and Gurobi.
  - Code: [github.com/Lorenz92/QAL-BP](https://github.com/Lorenz92/QAL-BP), no license per the GitHub API. The exact energy terms and the largest instance were not extracted. **[UNVERIFIED details]** — [arXiv 2309.12678](https://arxiv.org/abs/2309.12678)
- **QKP constraint transformations (Borrajo, Ramírez, Nosrati, Aguilar, Mancuso, Fernández Anta; GECCO'25 companion, DOI 10.1145/3712255.3726615; extended SciTePress 2026).**
  - Nine capacity encodings were evaluated under SA: unary slack (W bits), log slack (⌈log2(W+1)⌉ bits), "each w max" (slack only over [W − w_max + 1, W]), "log w max" (⌈log2(w_max+1)⌉ bits: P6 = (W − Σ w_i x_i + Σ_k 2^{k−1} s_k)²), and **equality** P5 = ((W − λ) − Σ w_i x_i)² with **no slack**, with λ iterated over 0..w_max−1 or fixed at w_max/2 or √w_max.
  - Result: the "equality approaches generally outperform inequality formulations across all evaluated metrics". Unary-slack SA found almost no feasible solutions (1% at 20 items, 0 above).
  - Instances had 20/35/50/65 items. On D-Wave, feasible outputs were 1.5% at 50 items and 0.1% at 65. Code: a [Zenodo record 18542280](https://zenodo.org/records/18542280) exists, but its contents and license were not verified. — [SciTePress PDF](https://www.scitepress.org/Papers/2026/146074/146074.pdf); [ACM](https://dl.acm.org/doi/10.1145/3712255.3726615)

### Inferences
- **Time-slotted occupancy QUBO for Baleen (our construction, not published):**
  - Treat each ten-minute slot t as one MDKP dimension: E_cap = Σ_t λ_t (Σ_e o_{e,t} x_e + Σ_{b=0}^{K−1} 2^b Δ y_{t,b} − Cap)².
  - Slack count: with Cap quantized to Δ = 1 GB, K = ⌈log2 367⌉ = 9 bits per slot, so 144 × 9 = 1,296 slack spins.
  - Couplings: x_e x_{e'} gets 2 Σ_t λ_t o_{e,t} o_{e',t}, which is non-zero exactly for time-overlapping episodes. If a_t episodes are live in slot t, the slot contributes a clique of ~a_t²/2 couplers, and every episode couples to the 9 slack spins of each slot it spans.
  - This has the same rank-≤144 structure as the peak objective, so the matrix-free J·x trick in REPORT.md applies unchanged: J·x = Oᵀ(λ ⊙ (O x)).
- **This constraint is probably redundant for Baleen as currently defined.** Baleen episodes are already built with an assumed eviction age derived from the cache size, so occupancy ≤ Cap is enforced implicitly by the episode model. An explicit per-slot capacity term only adds value if the selector is allowed to change that assumption, for example by admitting fewer episodes so that others live longer.
- **What an LP or MIP cannot express but a QUBO can:** the per-slot constraints above are linear, so LP and MILP handle them exactly and better. The genuinely quadratic interaction worth encoding is the capacity-induced *eviction-age feedback*: admitting e shortens the residency of the overlapping episodes e', which lowers their realized DT savings. The simplest quadratic surrogate is a QKP-style negative pair value −γ_{ee'} x_e x_{e'}, with γ_{ee'} ∝ the DT that e' loses from the hits beyond its shortened residency when e is also admitted. That turns the objective into a Quadratic Knapsack Problem, the setting where Borrajo et al. and Bontekoe et al. evaluated encodings. No published cache paper does this, so it is an open design point.
- **Encoding choice for our write budget W:** the evidence from Borrajo et al. (equality-with-offset or tight-range slack beats full slack under SA) and from BALANCE (dynamic penalty beats slack) is consistent with REPORT.md's recommendation to keep W outside the QUBO as a Lagrangian diagonal term.

### Gaps
- I found no published QUBO or Ising model of cache admission or placement that has a time dimension (items with lifetimes competing per slot, CDN or storage-cache admission, or eviction-age feedback).
- I found no multiple-knapsack-per-time-slot or "temporal knapsack" QUBO; a targeted search returned only VRP-with-time-windows and generic knapsack papers.
- No published cache QUBO exceeds toy scale: 5 contents in the ISTN paper, ≤ 65 items with D-Wave feasibility collapsing in the QKP paper, and ≤ 23 logical qubits in the MDKP paper.
- I could not extract the exact energy terms or sizes for 2306.01159, the 6G service-placement letter, or QAL-BP.

## Q2. Joint admission + prefetch: one-hot / multiple-choice among {reject, admit, admit+prefetch-k}

### Takeaway
The published MKP/GAP QUBOs give a slack-free "at-most-one" term that fits the {reject, admit, admit+prefetch-k} choice exactly. Reject is the all-zero state, so no slack or reject variable is needed. The penalty weight must exceed the largest single-option value (A > max v, proven sufficient in two papers). Budget-penalty couplings between options of the same episode have the same sign as the one-hot couplings and reinforce them. However, the budget's linear pull can make choosing two options look attractive when the budget is slack, which is one more reason to handle W with a Lagrangian term.

### Cited Findings
- **At-most-one without slack (Awasthi et al., arXiv 2301.05750):** H_single = Σ_j (Σ_i x_{i,j})(Σ_i x_{i,j} − 1). This is 0 when item j is assigned to 0 or 1 knapsacks and positive otherwise. It needs A > max v_{i,j}, and they used A = 2·max v. Code: [QutacQuantum/Knapsack](https://github.com/QutacQuantum/Knapsack), no license. — [arXiv 2301.05750](https://arxiv.org/pdf/2301.05750)
- **At-most-one with one slack per item (Güney, Ehrenthal, Hanne; ICAART 2025 / QAIO workshop, DOI 10.5220/0013387700003890, CC BY-NC-ND).**
  - Energy: P = λ1 Σ_k (Σ_i d_i x_{ik} − Σ_{t=0}^{M_k−1} 2^t u_{tk} − α_k u_{M_k k})² + λ2 Σ_i (Σ_k x_{ik} + v_i − 1)², with M_k = ⌊log2 E_k⌋ and α_k = E_k + 1 − 2^{M_k}.
  - Theorem 1: λ1, λ2 ≥ C* = max c_{ik} is a valid reformulation. When both constraints are violated the weaker condition d*λ1 + λ2 ≥ C* suffices.
  - The instances were tiny (up to (N,K) = (6,2) and (5,3)). The D-Wave optimal rate fell from 99.4% at (6,2) to 68.6% at (5,3). — [SciTePress PDF](https://www.scitepress.org/Papers/2025/133877/133877.pdf)
- **Standard penalty table (Glover, Kochenberger, Du tutorial):** x_i + x_j ≤ 1 → P·x_i x_j. For larger groups, Σ x ≤ 1 → P Σ_{i<j} x_i x_j, which is algebraically ½·(Σx)(Σx−1). — [arXiv 1811.11538](https://arxiv.org/abs/1811.11538)

### Inferences
- **Proposed multiple-choice selector (our construction):**
  - Variables x_{e,k}, k ∈ {1..K_e}, one per option (admit, admit+prefetch-range-1, …). "Reject" means all zeros.
  - E = −Σ_{e,k} v_{e,k} x_{e,k} + A Σ_e Σ_{k<k'} x_{e,k} x_{e,k'} + μ Σ_{e,k} s_{e,k} x_{e,k} + [peak or capacity terms over d_{e,k,w}, o_{e,k,t}].
  - Counts: n·K spins plus n·K(K−1)/2 intra-episode couplers. With K = 3 and n = 10^5 that is 3×10^5 spins and 3×10^5 one-hot couplers, which is sparse and local. The peak and capacity terms keep the rank-144 structure over the (e,k) columns.
- **One-hot vs budget interaction:**
  - If W is a squared penalty B(Σ s x + slack − W)², each same-episode option pair gains +2B s_{e,k} s_{e,k'}. That has the same sign as A, so it helps exclusivity.
  - The linear term −2BW s_{e,k} rewards large options, though, so A must exceed max_k(v_{e,k} + 2BW s_{e,k} − B s_{e,k}²) rather than just max v. This is an algebraic consequence of expanding the square, not a published result.
  - With a Lagrangian μ Σ s x there is no such interaction and A > max_k(v_{e,k} − μ s_{e,k}) suffices.
- **Why a greedy or LP ranking cannot do this:** because prefetch options are nested (a larger prefetch range writes more bytes and saves more DT), a per-byte greedy picks an option per episode by ratio and ignores which windows the extra DT lands in. The joint choice is a multiple-choice knapsack. Its LP relaxation is still tractable, so the QUBO's advantage again rests only on the non-separable peak objective.

### Gaps
- I found no published QUBO for the multiple-choice knapsack (MCKP) or the generalized assignment problem at scale with code and a license. Every one-hot knapsack QUBO I found tops out at ≤ 23 logical qubits.
- I found no study of how one-hot penalties interact with a knapsack budget under simulated bifurcation (SB) or simulated annealing (SA) at large n.

## Q3. Same-block episodes: mutual exclusivity, dependence and precedence in QUBO

### Takeaway
Conflict, forcing and precedence each map to one quadratic term with no auxiliary variables. Güney & Ehrenthal (IEEE Access 2026) give sufficient penalty bounds: λ_C ≥ R*, and λ_F, λ_P ≥ the sum of all other revenues in the worst case, which is loose and inflates the dynamic range.

### Cited Findings
- **Constraints (Güney & Ehrenthal, IEEE Access 2026):**
  - Conflict: x_j + x_k ≤ 1 for (j,k) ∈ C.
  - Forcing: x_j + x_k ≥ 1.
  - Precedence: x_j ≤ x_k ("j only if k").
  - They are "incorporated through quadratic penalty terms that modify existing QUBO coefficients without introducing additional binary variables", and the property "preserves the size of the QUBO formulation".
- **Penalty bounds, same paper:** λ_K = λ_P; λ_C ≥ R* (a conflict violation changes the objective by −r_j + λ_C); λ_F ≥ Σ_{i∈N∖{j,k}} r_i; λ_P ≥ max{R*, Σ_{i∈N∖{j,k}} r_i}. Instances had N ≤ 7 and 23 logical qubits, with conflict density CD ∈ {0, 0.1, 0.2, 0.3}. — [IEEE Access PDF via INSPIRE](https://inspirehep.net/files/6dc97dfdba01eae229daa641fac62284)
- **Standard quadratic forms (Glover–Kochenberger–Du tutorial):** conflict → P x_j x_k; x_j ≤ x_k → P(x_j − x_j x_k); forcing x_j + x_k ≥ 1 → P(1 − x_j − x_k + x_j x_k). — [arXiv 1811.11538](https://arxiv.org/abs/1811.11538)

### Inferences
- **In Baleen, same-block episodes are disjoint in time**, so they do not conflict for space with each other. The realistic couplings are these:
  - (a) Dependence: if admitting episode e_1 changes the boundary or eviction assumptions of e_2 (for example, when merged episodes are split), encode it as precedence x_{e2} ≤ x_{e1} or as a soft pair reward.
  - (b) Alternative episode segmentations of the same block at different assumed eviction ages: these are mutually exclusive, so use the one-hot (Q2) or conflict terms.
- **Counts:** one coupler per same-block pair. That is O(#episodes per block) and negligible next to the time-overlap cliques.
- **Precision:** the forcing and precedence bounds scale with Σ r_i, which could be ~10^5 × the typical r at our n. Hard-penalty precedence would therefore blow up the dynamic range that REPORT.md already flags. Enforcing precedence in repair or post-processing, or using a local λ tuned by violation, is more practical. This is an inference; no source tests these bounds at scale.

### Gaps
- I found no published cache or storage QUBO that uses precedence or consistency constraints.
- No scaling study of the conflict/forcing/precedence (CFP) penalty bounds beyond N = 7.

## Q4. Peak / load balancing: multiway partitioning, makespan, time-window structure

### Takeaway
Nothing new beyond ising_followup/survey.md §5 turned up. Published peak or load QUBOs use either a sum-of-squares balance, (Σ_i a_i x_{ik} − T/K)², or Lucas's epigraph or bisection. None has time-window structure like our 144 windows. The only new item is a 2025 J. Heuristics hybrid decomposition for number partitioning, whose details are not verified.

### Cited Findings
- **Number partitioning with hybrid decomposition:** "Efficient solution of the number partitioning problem on a quantum annealer: a hybrid quantum-classical decomposition approach" (J. Heuristics 2025, DOI 10.1007/s10732-025-09556-3). Per the search snippet, it splits the problem into sub-problems solved by quantum annealing and recombines them with SA on an auxiliary problem. The full text was paywalled. Two-way vs multiway, the sizes and the baselines are **[UNVERIFIED]**. — [Springer](https://link.springer.com/article/10.1007/s10732-025-09556-3)
- **Constraint-preserving mixer vs penalty QUBO:** a GitHub repo compares a constraint-preserving XY-mixer QAOA with a penalty-based "soft-QUBO" for HPC load balancing. It has no license, and its scale and results are not verified. — [GitHub moadex2005/High-Performance-Computing-HPC-Load-Balancing](https://github.com/moadex2005/High-Performance-Computing-HPC-Load-Balancing)
- The makespan epigraph, the Venturelli bisection, the Rathore HPC load balancing on D-Wave (arXiv 2403.05278) and the weakness of SA vs Karmarkar–Karp on number partitioning (NPP) are all covered in `ising_followup/survey.md` §5 and REPORT.md. See [Lucas 2014, arXiv 1302.5843](https://arxiv.org/abs/1302.5843).

### Inferences
- For our time-window peak, the natural QUBO is the multidimensional analogue of the number-partitioning energy: Σ_w α_w (C_w − Σ_e d_{e,w} x_e − τ)², which REPORT.md already recommends.
- The one formulation the literature adds is to put **per-window occupancy (Q1) and per-window disk-time (DT) load into the same rank-(2×144) quadratic form**. Both are sums over the same windows, so a combined E = Σ_w α_w (L_w − τ)² + Σ_t λ_t (occ_t + slack − Cap)² + μ Σ s x + one-hot + conflict terms stays matrix-free.
- **Scale warning:** every published QUBO in Q1–Q3 stops at ≤ 65 items (SA) or ≤ 23 qubits (hardware). That is 3–4 orders of magnitude below our n. At our size, any quality claim will have to come from our own SA/SB runs against Gurobi.

### Gaps
- I found no min-max or load-balancing QUBO with a time-window (per-slot) structure and published quality at n ≥ 10^3.
- No head-to-head of sum-of-squares vs epigraph beyond what the prior notes already cite.

## Code / license summary (verified via the GitHub API on 2026-09-28 unless noted)

| Formulation | Code | License | Largest solved |
|---|---|---|---|
| Multiple-knapsack, H_single + log-slack (Awasthi et al. 2023) | [QutacQuantum/Knapsack](https://github.com/QutacQuantum/Knapsack) | none declared | 19 qubits (2 knapsacks, 6 items) |
| QAL-BP bin packing, augmented Lagrangian, no slack | [Lorenz92/QAL-BP](https://github.com/Lorenz92/QAL-BP) | none declared | not extracted [UNVERIFIED] |
| Bin packing via QAOA/Qiskit (repo owner is likely Montañez-Barrera; not confirmed to be the unbalanced-penalization paper's code, [UNVERIFIED]) | [alejomonbar/Bin-Packing-Problem](https://github.com/alejomonbar/Bin-Packing-Problem) | Apache-2.0 | the paper reports 29 items on D-Wave Hybrid (see REPORT.md) |
| QKP 9 transformations (Borrajo et al.) | [Zenodo 18542280](https://zenodo.org/records/18542280) [contents UNVERIFIED] | unknown | 65 items (SA); D-Wave ≤ 1.5% feasible at 50 items |
| MKP penalty bounds (Güney et al. 2025), MDKP-CFP (Güney & Ehrenthal 2026) | none found | paper CC BY-NC-ND (2025) | (6,2)/(5,3) MKP; 23 qubits MDKP |
| ISTN caching + power, Benders + QUBO (Zhang et al.) | none | — | 5 contents, 2 caches, 10 users |
| BALANCE bitrate / data-cap (WCNC 2025) | none found | — | [UNVERIFIED] |

GitHub searches for "qubo cache placement" and "quantum annealing caching" returned **zero repositories**.
