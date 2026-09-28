# PeakBaleen: the fixed swap boundary

**Status: FROZEN (2026-09-27).** This file defines the only part of the Baleen harness PeakBaleen may replace. Changing it needs the whole team's agreement and a new dated version of this file.

## 1. The one replaceable block: offline episode selection

In the harness, every method, Baleen's OPT included, is a subclass of `Policy` (`BCacheSim/episodic_analysis/policies.py`), chosen with `train --policy <Name>`. A policy's single job is:

```
sort_residencies(residency_lists) -> residency_lists
    for each rl: rl.init(**rl_init_kwargs); rl.recompute()
                 order, scores = <OUR ALGORITHM>
                 rl.apply_policy(order, scores=scores, policy=<name>)
```

What the harness already does with that output:
- `apply_policy` sets each episode's `threshold` to its cumulative write rate in `order`.
- The episodes admitted at budget W are the prefix of `order` with `threshold ≤ W`.
- In the harness's existing methods, the rule "Baleen = greedy by DT-saved / chunks-written" is exactly `order = argsort(score)` (`PolicyUtilityServiceTimeSize2`).

**PeakBaleen = one new `Policy` subclass.**

Input:
- The `ResidencyList`s the harness builds: episodes at the harness's eviction age. Each episode carries its `accesses` (timestamps), `service_time_saved`, `chunks_written`, `key`, and so on.
- `rl_init_kwargs` and the target write rate.

Algorithm: anything, including QUBO or an Ising solver.

Output: an ordering and scores. **The selected set for the training budget W = 35.599 MB/s must come first**, so that the harness's prefix rule reproduces the selection exactly. The remaining episodes follow in Baleen's own order.

Everything is computed inside the new module, including the per-window savings d(e,w), from episode data the harness provides. The class must not modify episodes, residency lists or any global state beyond what `apply_policy` does.

**How it plugs in, without editing frozen code.** Our own entry module registers the class into `policies.__dict__` and then calls the unmodified `BCacheSim.episodic_analysis.train.main()` with the usual arguments plus `--policy PeakBaleen…`. The simulator needs no plug-in.

## 2. How both methods are evaluated (fixed; the same for Baleen and PeakBaleen)

| Mode | Harness path (unchanged) | Paper analogue | Measures |
|---|---|---|---|
| **Offline (OPT)** | policy → decisions file → `simulate_ap --ap opt` (existing `OfflineAP`) | "OPT AP" rows | quality of the selection itself (upper bound) |
| **Deployed (ML)** | policy labels → existing `train_ap` / `train_prefetcher` GBMs → `simulate_ap --ap mlnew` | "Baleen" rows | what survives distillation into the online model |

Settings that are the same for both methods:
- Trace samples: 0.1%, sample start 0 first, then samples 0–9.
- Cache size 366.475 GB; target write rate 35.599 MB/s.
- The authors' converged eviction age for each trace.
- Admission threshold re-converged to the target write rate (±1%) with `0_reproduce/repro/converge.py`.
- Metric: `PeakServiceTimeUtil1` (peak load, 10-minute windows, after day 1).
- Train on day 1; test on the remaining days.
- The same sandbox (`bwrap`) and `check_frozen.sh`.

## 3. Frozen: never touched, overridden or monkey-patched
- **Simulator:** everything in `cachesim/`: datapath, admission policies (`mlnew`, `opt`, `rejectx`, `coinflip`), prefetchers (ML-Range, ML-When), eviction, the DT/utilisation accounting, and the output fields.
- **Episode model:** `episodes.py`, i.e. episode generation, the residency model and `apply_policy`/threshold semantics.
- **Online ML:** features (`dynamic_features.py`, the `meta+block+chunk` subset), GBM code and hyperparameters (`train_ap.py`, `train_prefetcher.py`), and the label rule `threshold < target_wr`.
- **Training driver:** `train.py`, eviction-age handling, train/test split.
- **Data:** traces, sampling, operating point.
- **Evaluation:** our evaluation code in `0_reproduce/` (runner, `converge.py`, `analyze.py`). New code may import it but must not edit it.

## 4. Consequences for the proposal (agreed trade-offs)
- **Out of scope:** the proposal's "causal load features" for the admission model and the "load-adaptive ML-When gate" (§4.1/§4.3, and H3's feature part). Both would change features, prefetchers and the simulator's datapath.
- **H3 therefore becomes:** "how much of the offline (OPT-mode) peak gain survives distillation into the *unchanged* Baleen GBM". Its features are metadata plus access counts over the last 1–6 hours, with no time-of-day or load signal. Losing most of the gain is an expected, reportable outcome.
- **Unchanged:** H1 (offline peak gain at a matched write rate) and H2 (solver comparison on a fixed formulation). Both are measured entirely through the swap block.
- **Ablation (a), the artifact's own peak policy** (`PolicyUtilityPeakServiceTimeSize`, which needs an oracle `peak_ts1_*` window through `rl_init_kwargs`), is another `Policy` in the same slot. It is compared on equal terms.
