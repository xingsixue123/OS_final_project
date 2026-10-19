# SCOPE v2 amendment 1b (proposed by Track E / WP10, 2026-10-19): a piecewise-constant threshold table

**Status:** proposed, used only inside `wp10_schedule/`. The coordinator records it in `SCOPE_v2.md` §1a. Until then it governs no other work package. The reviewed `wp0_overlay/PATCH.diff` (sha256 `2a914eb589bb`) is unchanged; WP10 runs a separate overlay copy built from `PATCH_v3.diff`.

## Why an amendment is needed
SCOPE_v2 §1 item 2 allows a load-adaptive admission threshold θ_t = θ · g(load_t) **with a fixed shape parameter** (the power law g(x) = clip((x/20)^α, 0.25, 4), α fixed). WP10 replaces the one-parameter power law by a **table**: a piecewise-constant multiplier m_b over K load buckets (optionally K × J cells with J time-of-day buckets). A table is a shape change, not a parameter change, so it needs this amendment.

## The exact amendment (adds item 1.2b to SCOPE_v2 §1)
1.2b **Optionally replace g by a piecewise-constant table** loaded from a JSON file:
- **Flag:** a new `simulate_ap` option `--ap-load-adapt-table <file.json>`. **Off by default** (unset → no new code path runs). It is exclusive with `--ap-load-adapt-alpha` (asserted).
- **Form:** θ_t = θ · g(load_t[, hour_t]) with g(x) = m_b for e_b ≤ x < e_{b+1} (`bisect_right` on the increasing edge list), load_t = the same causal trailing 10-minute GET demand (`DemandLoad.load`, utilisation %) as item 1.2; optional time-of-day rows by UTC hour of the access. JSON: `{"window_min": 10, "edges": [...], "mult": [...]}` (+ `"tod_edges_h"` and a 2-D `"mult"`). Multipliers must be positive.
- **Causality:** unchanged from item 1.2. g is evaluated at each item's own access time with demand strictly before it. It never sees admission decisions or anything later.
- **Fitting rule:** a table is fitted **only on training-window data**: the same day-1 window (`--train-split-secs-start 0 --train-split-secs-end 86400`) on which the artifact trains its GBM, using the trained model's scores on day-1 accesses. No data after day 1 and no simulation outcome of any evaluated period may enter the fit.
- **Base θ** is still converged to 35.599 MB/s ± 1% by full simulation, as for every arm (SCOPE_v2 §2).
- **Fairness gates:** G1 (default equivalence of the new overlay vs the frozen artifact) is re-run. A table that reproduces the power law must give results bit-identical to `--ap-load-adapt-alpha -1` (`G1_v3.md`).

## What does not change
Everything in SCOPE_v2 §2 (simulator datapath, episode model and labels, GBM training, data, operating point, `PeakServiceTimeUtil1`, matched write rate). The table touches only the admission comparison `score > θ · g`. The prefetch models are untouched.

## Implementation
`PATCH_v3.diff` = `PATCH.diff` + 4 files, +43/−1 lines (`PATCH_v3_delta.diff`): `load_features.LoadTableThreshold`, the `--ap-load-adapt-table` flag (`simulate_ap.py`), its construction in `admission_policies.construct('mlnew')`, and the demand-series condition in `sim_cache.py`. Built by `rebuild_overlay.sh` into `wp10_schedule/overlay/`.
