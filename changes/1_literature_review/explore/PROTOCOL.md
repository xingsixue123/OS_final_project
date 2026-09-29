# Deep-explore protocol: can QUBO/Ising answer "yes" three times?

**Frozen:** 2026-09-28, before any tuning. Every trial follows these rules. Changing a rule needs the user's approval and a new dated version of this file.

## The three questions and their pass criteria
The final answers are judged **only on held-out instances**, never on the development instances used for tuning.

| # | Question | Pass criterion (held-out, matched flash write rate 35.599 MB/s ±1%) |
|---|---|---|
| Q1 | Does QUBO/Ising find good peak-aware selections? | Offline mode (`--ap opt`): the simulated P100 of the chosen Ising configuration is below Baleen's peak-blind OPT on at least 5 of 6 held-out instances, and lower on average. |
| Q2 | Is it better than classical solvers? | Same formulation, at equal wall-clock budgets of 10, 60 and 300 s, on the same pinned cores. It must meet all three conditions below. |
| Q3 | Does it beat Baleen in the real deployed system? | Deployed mode (labels from an **Ising-family** solver, then Baleen's unchanged GBMs, then `--ap mlnew`), with at least 3 retrains per instance. It must meet all three conditions below. |

**Q2 conditions:**
- **Objective:** the Ising objective is at most the best classical objective on at least 5 of 6 held-out instances, at 2 or more of the 3 budgets.
- **Average:** it is strictly better on average.
- **Simulation:** the simulated offline P100 of the Ising solution is at most the classical one's, on average.
- **Which formulation:** Q2 must be shown on a formulation actually used by the final Q1 or Q3 configuration, not on a toy problem.

**Q3 conditions:**
- **Against Baleen:** the mean P100 is below Baleen online's mean on at least 4 of 6 held-out instances.
- **Average margin:** the average improvement over Baleen online exceeds 2 SE of the difference.
- **Against the baselines:** it is below RejectX and CoinFlip on average.

## Instances
- **Development set (tuning allowed):** Region7 and Region6, sample 0 (20230325, 0.1%). These are already used by `harness_eval/`.
- **Held-out set (evaluation only, never used to pick configurations):** Region7 and Region6, samples 0.1, 0.2 and 0.3. That is 6 instances.
- **Baselines on every held-out instance:**
  - Baleen online (Fig 9 prefetch variant: Region7 ML-Range on ML-When, Region6 All on Partial Hit), with at least 3 retrains;
  - RejectX;
  - CoinFlip;
  - Baleen peak-blind OPT (offline).

  All are run from the authors' per-sample commands in `results_release.csv.gz`, with their knobs converged to the matched write rate.

## Families
- **Ising/QUBO family:** simulated bifurcation (any variant, matrix-free or not); CIM-style amplitude dynamics (CAC, AHC, CFC); Extended-Ising-Machine or SAIM-style samplers with native or Lagrangian constraints; parallel tempering, simulated annealing, Gibbs sampling or p-bit sampling on a QUBO/Ising energy; any hybrid whose accepted moves come mainly from one of these. Report the share of moves each sub-solver contributes.
- **Classical family:**
  - greedy;
  - LP relaxation plus round and repair;
  - HiGHS MILP;
  - SCIP (MIQP or MINLP) where the formulation is quadratic;
  - OR-Tools CP-SAT;
  - true-objective local search that works directly on the problem, with no QUBO.

  Classical solvers get the **same number of hyperparameter-tuning trials** as the Ising solvers.

## Rules
1. **Scope stays as agreed.** `changes/SCOPE.md` is unchanged: only the offline selection `Policy` (and the solver behind it) may change. No changes to features, GBM, simulator, episode model or training driver. Nothing under `0_reproduce/` or `harness_eval/` may be modified; copy or import instead.
2. **Tune on dev only.** Tuning and selection use dev instances only. At most 3 final configurations may go to the held-out set, and each is reported however it turns out.
3. **Log every trial.** Record the configuration, instance, seed, wall time, objective, simulated P100 and matched write rate in a `trials.csv`. Report failures too. No cherry-picking seeds or retrains: report the mean ± SD over all of them.
4. **Matched write rate always.** A result counts only if its simulated write rate is within ±1% of 35.599 MB/s.
5. **Sandbox.** All work stays inside `explore/`. Every Baleen process runs under `bwrap` with a private `/tmp`. Only one `train` runs at a time (shared lock `explore/.train.lock`). There is no GPU. Core pinning: Q2 timing uses cores 0–7; everything else uses cores 8–23.
6. **Report the answer we get.** If a criterion is not met, the answer is "no", with the evidence and the reason.
