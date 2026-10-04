# Q3 formulation (Track A -> Track B)

**Status: FINAL. Finalists P0, T2, C2 (selected 21:50-22:00 by the pre-registered dev rule, q3/PROGRESS.md).
Held-out Q3 outcome (q3/RESULTS.md): NO for all three (2/6 wins each; mean change vs Baleen -0.41 / -1.07 / -0.57).**

The Q3 labels are produced on the **day-1 instance** (`common/inst/day1_<Region>_s<start>.npz`, deployed mode) by an
Ising-family solver (parallel tempering) on the extended-Ising energy below; the selected episodes are the training
labels of Baleen's unchanged GBMs (label rule `threshold < 35.599`), the tail after the selected set stays in Baleen
order (SCOPE §1).

## Energy (binary units u; all terms in utilisation-% points)

```
E(x) = A * F_peak(L(x))                                   soft peak of the day-1 per-window loads
     + sum_u lin_u x_u                                    DT blend + trust region (+ optional peak-weighted DT)
     + lam_c * sum_{(u,v) in G} |x_u - x_v|               feature-consistency couplings (optional)
     + const
s.t. sum_u s_u x_u <= Bc = f * B                          native hard write budget (B = harness label budget)
     x_u = 1 for forced units (optional saturated-row coverage)

L_w(x)  = C_w - sum_u D_uw x_u,        w = the 145 day-1 windows (optionally aggregated)
F_peak  = LSE_gamma(L) = max L + log(sum_w exp(gamma (L_w - max L))) / gamma      ("lse", default gamma = 2 /util-pt)
        | mean of the top-k windows                                                ("topk")
lin_u   = -beta * sts_u * US / m                       (DT blend: -beta x mean-util reduction)
          + mu / |S_B| * (n_u - 2 b_u)                 (trust region: mu util-pts per 100% of Baleen's labels flipped)
          - beta_pw * sum_w D_uw phi_w / m             (optional; phi_w = normalized (C_w / mean C)^pw)
G       = symmetric kNN graph (k=5) over episodes inside each (op, namespace, user) group, in the standardized space
          of the first training row's numeric GBM features (log size, log offset, log1p block/chunk counts, log #rows);
          lam_c = lam / |G|
units   = episodes (cells = "ep") or feature cells of the first training row ("meta+sz+h+nacc": op/ns/user, log2 IO
          size, block-count bins, #rows bin); an episode is labeled iff its unit is selected.
```
`D_uw`, `C_w` are the harness_eval d(e,w) / C_w (util %), `s_u` = `rl.chunks_written`, `sts_u` = DT saved, `b_u` =
number of Baleen-selected episodes in u, `n_u` = number of episodes in u. MILP form for classical solvers: use
`peak = "max"` (epigraph `z >= L_w`) and `t_e >= |x_u - x_v|` for the couplings; LSE / top-k have standard convex
reformulations (top-k: CVaR epigraph; LSE: SOCP/exp-cone or piecewise-linear tangents).

## Builder / evaluator (exactly the solver's energy)
`common/src/q3form.py`:
```
python common/src/q3form.py <instance.npz> '<cfg json>' <out.npz>     # writes D, C, s, Bc, lin, edges, lam_c, ...
from q3form import build, energy;  F = build(inst, cfg);  E, parts = energy(F, x_units)
```
Checked: `energy()` reproduces the PT solver's reported energies exactly (Baleen start 24.5180 and solution 22.4457
on dev Region7 day 1, cfg `{"mu":2,"beta":0.5,"lam":5}`).
Solver used by Track A: `q3/src/q3solve.py --cand PT` (numba parallel tempering, 16 replicas, geometric temperatures
1e-3..0.3 util-pts, Metropolis flips/swaps biased to units touching the current argmax window, replica exchange each
round; 100% of accepted moves from PT). Labels = selection + harness strict-prefix fill in Baleen order.

## Final configurations (the exact solver args; `secs` = PT wall budget inside the train, not part of the energy)

| name | cfg (q3solve/q3form args) | energy | dev (3 retrains each) |
|---|---|---|---|
| **P0** | `{"mu":0,"beta":0,"secs":15}` | pure soft peak: E = LSE_2(L(x)) s.t. s.x <= B (episodes as units) | R7 39.16 +- 0.40, R6 42.93 +- 0.18 (Baleen 40.10 / 43.25) |
| **T2** | `{"mu":2,"beta":0.5,"secs":15}` | LSE_2(L) + 0.5 x DT blend + trust region mu=2 (episodes) | R7 39.36 +- 0.17, R6 42.78 +- 0.40 |
| **C2** | `{"mu":2,"beta":0.5,"cells":"meta+sz+h+nacc","secs":15}` | same energy as T2 over feature CELLS of the first training row (op, ns, user, log2 IO size, block-count bins, any-older-history, #rows bin); ~1.6k cells | R7 38.93 +- 0.56, R6 43.21 +- 0.13 |

Defaults not listed: A=1, peak="lse", gamma=2 (per util-pt), f=1 (Bc = B), cells="ep", lam=0, all 145 day-1 windows.
Instances: `common/inst/day1_<Region>_s<start>.npz` (the day-1 instance each deployed train builds is identical up to
episode order). Example:
```
X/env/bin/python common/src/q3form.py common/inst/day1_Region7_s0.1.npz '{"mu":0,"beta":0}' <tmp file>
```
For MILP-based classical solvers use `peak="max"` (exact epigraph) or report LSE via a convex solver; the top-k
variant is not a finalist.

**Caveat for Q2 (mechanism, see q3/RESULTS.md):** on dev the deployed gain of these labels comes mostly from
zero-value one-hit-wonder episodes that the stochastic PT leaves selected (they do not change the day-1 loads, so the
energy is indifferent to them under P0 and nearly so under T2); they shift Baleen's GBM toward first-access admission.
A solver that minimizes the same energy more exactly (or repairs/cleans such units) need not reproduce the deployed
effect, so Q2's energy comparison and Q3's deployed outcome measure different things here.
