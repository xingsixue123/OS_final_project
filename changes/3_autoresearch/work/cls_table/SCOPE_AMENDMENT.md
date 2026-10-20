# SCOPE v2 amendment 1.2c (proposed by 3_autoresearch, 2026-10-20): a load × access-class threshold table

**Status:** proposed and used only inside `changes/3_autoresearch/work/`. It extends amendment 1.2b (`2_deployable_peak/wp10_schedule/SCOPE_v2_1b.md`, recorded in `SCOPE_v2.md` §1a). None of these files is modified:
- `wp0_overlay/PATCH.diff` (sha256 `2a914eb589bb`);
- `wp10_schedule/PATCH_v3.diff` (sha256 `03f1523e688d`).

This work runs its own overlay copy (`work/cls_table/overlay/`):
- built by `rebuild_overlay.sh` from `PATCH_v3.diff`;
- plus `PATCH_v4_delta.diff` (2 files: `cachesim/load_features.py` and `cachesim/admission_policies.py`).

A result that uses the class table counts only after `G1_v4.md` reports PASS.

## Why an amendment is needed
Amendment 1.2b allows θ_t = θ · g(load_t[, hour_t]), a piecewise-constant table over load buckets (optionally × time-of-day). The class table lets g also depend on a **class of the access itself**, computed from the access's own admission feature vector. That is a new argument of g, so it needs this amendment.

The motivation comes from the published mechanism (WP2 §7, WP3 §2):
- deployed peaks are often big-offset sequential scans;
- Baleen's models admit almost none of their accesses in the peak window.

## The exact amendment (adds item 1.2c to SCOPE_v2 §1)
1.2c **Optionally let the table of 1.2b depend on an access class.**
- **Flag:** the same `--ap-load-adapt-table <file.json>` (off by default; exclusive with `--ap-load-adapt-alpha`). A JSON file with a `class_dims` key selects the class table; a file without it is read exactly as in 1.2b.
- **Form:** θ_t = θ · m[j(x), b(load_t)].
  - b is the load bucket of 1.2b (`bisect_right` on the increasing load edges; load_t = the same causal trailing 10-minute GET demand).
  - j(x) is the mixed-radix index of `bisect_right(dim edges, f(x))` over the class dimensions.
  - f is one of `load_features.CLASS_FEATURES`, computed from the access's own admission feature vector x (the values the GBM scores):
    - `endoff` = x[4] = offset + size;
    - `size` = x[5];
    - `blkcount` = Σ x[6:12] = block accesses in the 6 trailing hourly buckets.
  - Multipliers must be positive.
- **Causality:** x is computed by the simulator before the admission decision, from the access and earlier accesses only (`sim_features.collect_features`). load_t is causal as in 1.2. The class therefore never sees admission outcomes or anything later.
- **Fitting rule:** as 1.2b. A table is fitted only on the training window (day 1, `--train-split-secs-start 0 --train-split-secs-end 86400`), using the trained model's scores on day-1 accesses. No data after day 1 and no simulation outcome of an evaluated period enters the fit.
- **Base θ:** still converged to 35.599 MB/s ± 1% by full simulation, with search range (0, 4] as for every adaptive arm.
- **Fairness gates (`G1_v4.md`):**
  - G1 default equivalence of overlay v4 vs the frozen artifact.
  - v4 == v3 on the α path and the 1.2b table path.
  - A class table whose class rows are all equal must give results bit-identical to the same 1.2b table.

## What does not change
Everything in SCOPE_v2 §2:
- the simulator datapath, eviction, prefetch, disk-time accounting and output fields;
- the episode model and labels; GBM training;
- data, operating point, `PeakServiceTimeUtil1`, matched write rate.

The class table touches only the admission comparison `score > θ · g`. Training code is not modified: the v4 delta touches no file under `episodic_analysis/`.
