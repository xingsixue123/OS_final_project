# SCOPE v2 amendment 1.2d (proposed by 3_autoresearch, 2026-10-20): union of two admission models

**Status:** proposed and used only inside `changes/3_autoresearch/work/union/`. It builds on:
- 1.2b (`2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md`);
- 1.2c (`work/cls_table/SCOPE_AMENDMENT.md`, G1_v4 PASS).

No reviewed patch file is modified. This work runs its own overlay copy (`work/union/overlay/`) = `work/cls_table/PATCH_v4.diff` + `PATCH_v5_delta.diff` (2 files: `cachesim/admission_policies.py`, `cachesim/simulate_ap.py`). A result that uses the union counts only after `G1_v5.md` reports PASS.

## Why
The published deployed failures of Ising peak labels (WP3 Region7 s0.5, WP9 Region5 s0.5) came from an F1-label model that does not admit a big-offset scan peak that Baleen's model does admit. The Region6 dev gains of the same labels came from admitting scans that Baleen's model does not admit (WP2 §7).

A union keeps Baleen's admissions as a floor and adds the peak-label model's admissions.

## The exact amendment (adds item 1.2d to SCOPE_v2 §1)
1.2d **Optionally admit with a second admission model.**
- **Flags (all off by default):** `--ap-union-model <GBM file>`, `--ap-union-feat-subset`, `--ap-main-feat-subset`, `--ap-union-kappa κ` (default 1), `--ap-union-gate-load G` (default none).
- **Decision:** admit iff s_main(x) > θ·g OR s_2(x) > κ·θ·g [AND load_10m ≥ G].
  - g is the 1.2 / 1.2b / 1.2c multiplier (1 if none).
  - Each model scores its own canonical-order prefix of the access's admission feature vector. The collected vector (`--ap-feat-subset`) is the longer of the two subsets, and the column-order guards of 1.1 apply to both models.
- **Training:** both models are trained by the unmodified overlay trainer on the training day.
  - The main model has Baleen's labels (arm A).
  - The second model's labels come from the swap boundary of SCOPE v1 (the selection `Policy`; here the phase-1/WP2 F1 min–max day-1 selection, `PolicyPeakBaleen4`).
- **κ and G** are computed from the training day only:
  - κ = θ_2*/θ_main*, the two models' own day-1 emulated thresholds at the same day-1 write budget;
  - G = the day-1 access-level 0.75 quantile of load_10m.
- **Causality:** as 1.2 (both models score the same causal features; load_t uses requests strictly before t).
- **Base θ** is converged to 35.599 MB/s ± 1% by full simulation, range (0, 4].
- **Fairness gates (`G1_v5.md`):**
  - G1 default equivalence vs the frozen artifact;
  - v5 == v4 on the α and class-table paths;
  - a union whose second model can never admit (κ = 1e9), and a union of a model with itself (κ = 1), must both reproduce the single-model run bit-for-bit.

## What does not change
SCOPE_v2 §2:
- the simulator datapath, eviction, prefetch (the main arm's prefetch models), disk-time accounting;
- the episode model; GBM training;
- data, operating point, metric, matched write rate.

Only the admission comparison changes.
