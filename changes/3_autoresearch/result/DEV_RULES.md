# Dev rules (3_autoresearch): written before the dev simulations they govern

Every rule below is dated. A rule applies only to simulations launched after it was written. Rules are never edited after the fact; a change is a new dated entry.

## R0 — 2026-10-20 00:56 (file time 00:56:42, before any simulation of this run; the probe was launched at 00:56:58, the screen at 01:00:42)

**Scope.** Dev data only:
- the 8 instances Region7/Region6 × samples 0, 0.1, 0.2, 0.3 (`DEV8`);
- plus Region5_s0 and Region1_s0 (`DEV_EXTRA`) once their reference arms exist.

No test-pool or past-test sample is simulated or read for any choice.

**Reference arms on dev:**
- **DEV8:** WP2's matched dev trials, reused unchanged (`2_deployable_peak/wp2_deployed/trials.csv`):
  - A, B;
  - A+α = `Aa-1.0` ∪ `Ax-1.0`;
  - B+α = `Ba-1.0` ∪ `Bx-1.0`.
- **DEV_EXTRA:** A, B, A+α (`Aa-1.0`), B+α (`Ba-1.0`), run here through the same pipeline (overlay v3 training = WP2/WP9 training; retrains 1–3).

**Probe arms (`PB<c>`) are mechanism checks only.** They are never candidates, and their results cannot select a finalist directly. They only decide whether the class-table family is worth fitting at all; the finalist comes from the fitted Ising arms below.

**Candidates.** Only Ising-solver configurations are candidates:
- `CA:pt` and `CB:pt`: a load × access-class threshold table fitted by parallel tempering on the training day;
- any later Ising configuration, added to this file before its first simulation.

The classical-solver controls (`:cd`) are reported. They are never candidates.

**Screen (retrain 1).**
- For a candidate X on each available dev instance i (paired by retrain 1): d_i = min((A+α)_i, (B+α)_i) − X_i.
- **Gate:** mean_i d_i > 0, and no instance with d_i < −2.0.
- At most 2 candidates (the largest mean d) go to confirmation, which runs retrains 2 and 3 of the same configuration.

**Finalist rule (≥ 3 matched retrains per instance, on every dev instance that has complete reference data).** The contract's §4 pass rule is applied on dev:
- n = number of such dev instances;
- R ∈ {A, B, best α}, where best α is the one of A+α / B+α with the lower mean over the same instances;
- per-instance means over matched retrains.

X qualifies iff, for each R:
- (a) wins ≥ ⌈2n/3⌉;
- (b) mean(R − X) > 2.5 × SE_retrain, with SE_retrain = sqrt(Σ_i s²_X,i/n_X,i + s²_R,i/n_R,i)/n;
- (c) min_i (R_i − X_i) ≥ −2.0.

**Tie-break** among qualifiers: the larger min over R of mean(R − X), then name order.

**If nothing qualifies, there is no finalist and no test is spent on this family.** Every dev evaluation, matched or not, is a row of the cls_table ledger `work/cls_table/trials_dev.csv`.

## R1 — 2026-10-20 01:04 (file time; before any screen or probe result was read; no dev P100 of this run existed yet; the m-screen was launched at 01:04:54)
**New candidates** (same family, same fit, one added constraint): `CA:ptm`, `CB:ptm`.
- They are the class-monotone versions of `CA:pt` / `CB:pt`: PT on the same energy plus PMONO · Σ_b [m_big,b > m_small,b], so the big-offset class is never less admissive than the small class at the same load.
- Classical controls: `CA:cdm`, `CB:cdm`.
- **Reason:** the retrain-1 *tables* (not results) show that on Region7 the unconstrained fits often make big-offset accesses less admissive at high load. That is X1's catastrophic failure mode (an unadmitted scan peak on a later day).

The R0 screen gate and finalist rule apply unchanged. The candidate set for the screen is {CA:pt, CB:pt, CA:ptm, CB:ptm}; at most 2 (largest mean d) go to confirmation.

## R2 — 2026-10-20 01:42 (file time 01:42:38; UB launched 01:43:38; the screen results read so far: 15 retrain-1 evaluations of CA/CB/PB, none of UB, which had no simulation)
**New candidate `UB:ptm`** (plan B, the pooled universal class table):
- One load × class multiplier table, fitted by PT (class-monotone energy of `cls_fit.py`, 180 s) on the mean over the pooled training-day packs of base B, retrains 1–3 (`src/cls_pool.py`).
- **Deployment:** Baleen's B models + that table on the instance's own day-1 quantile load edges.
- **Dev evaluation is leave-one-instance-out.** On a DEV8 instance the table was fitted on the other 7 instances' packs only (21 packs). On Region5_s0 / Region1_s0 and on any test pool, the table is the fit on all 24 DEV8 packs (`pool_loo_all_B_ptm`), fixed now.
- **Control:** `UB:cdm` (coordinate descent on the same pooled energy).

**Procedure:**
- The R0 screen gate and finalist rule apply unchanged. The screen candidate set becomes {CA:pt, CB:pt, CA:ptm, CB:ptm, UB:ptm}; at most 2 (largest mean d) are confirmed.
- To save wall-clock, retrains 2 and 3 of UB:ptm / UB:cdm run together with retrain 1. They count toward the finalist rule only if UB:ptm passes the screen gate and is among the 2 confirmed candidates; otherwise they are reported only.

## R3 — 2026-10-20 03:56 (file time 03:56:47; union screen launched 03:56:50; before any simulation of the union family; G1_v5 is running)
**New family "union"** (`work/union/`, overlay v5, `work/union/SCOPE_AMENDMENT.md` item 1.2d). Admit iff Baleen's model A admits OR the F1 peak-label model X admits, both under α = −1:
- s_A > θ·g OR s_X > κ·θ·g [AND load_10m ≥ G];
- κ = θ_X*/θ_A* (day-1 emulated thresholds at the same day-1 budget);
- G = the day-1 q75 of load_10m.

**Arms:**
- **Candidates (Ising labels: phase-1/WP2 F1 min–max day-1 selection solved by parallel tempering):** `XA:F1PT` (no gate) and `XG:F1PT` (X gated to load ≥ G).
- **Classical controls (same formulation solved by CP-SAT):** `XA:F1CPSAT`, `XG:F1CPSAT`. Reported, never candidates.
- **Dev models:** WP2's retrains, read-only. Model A = `A_baleen_<inst>_r<k>`; model X = `D_<labels>_<inst>_r<k>` (`meta+block+chunk+load`).

**Rules:**
- **Screen:** the R0 gate on DEV8, retrain 1. At most 2 candidates (largest mean d) go to confirmation.
- **Confirmation:** retrains 2–3 on DEV8, plus retrains 1–3 on Region5_s0 and Region1_s0 if the F1-label pipeline (day-1 dump, label solve, X training, as WP9) is built for them. Otherwise the finalist rule runs on DEV8 only (n = 8, wins ≥ 6).
- **Finalist rule:** R0's, unchanged.
- The test protocol for a union finalist will be a new conditional pre-registration (pool by the 01:08 rule), committed before any of its test runs.
