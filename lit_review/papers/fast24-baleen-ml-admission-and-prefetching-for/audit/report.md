# Baleen: ML Admission & Prefetching for Flash Caches

*Desk review only — nothing was built or run. Every claim below is traceable to a paper
section/figure or a repository path.*

## 1. Paper summary

**Problem.** Bulk storage (Meta's Tectonic) is backed by HDDs whose scarce resource is
*disk-head time* (seek + transfer), and fronted by a flash cache whose scarce resource is
*write endurance*. An admission policy must spend a fixed flash write budget (e.g. 3
DWPD) on the insertions that remove the most backend load. Admitting everything would
need up to 492 MB/s / 43 DWPD on these traces, wearing out a 3-DWPD SSD in 4 months
(§2.3).

**Key idea.** Three coupled contributions (§1, §3):

1. **Disk-head Time (DT)** as the optimization target instead of IO/byte miss rate:
   `DT_i = t_seek + n·t_read` (§3.1, Fig 2). Validated against production disk-utilisation
   counters — peaks line up within 1% (Fig 3). `Peak DT` = P100 of 10-minute-window
   utilisation, which is what provisioning (and therefore TCO, §3.2, Eq 4) is driven by.
2. **Episodes** (§3.4, Figs 4–5): assuming an LRU cache evicts at a roughly constant
   eviction age, a block's access stream is cut into *episodes* — groups of accesses that
   would all be hits if the block were admitted at the first of them. An episode has a
   size (segments needed) and a DT-saved value, so admission becomes "pick the best
   episodes subject to a write budget". This yields **OPT** (§3.5), an offline
   near-optimal admission policy that ranks episodes by `DT_saved / size`, and it yields
   clean supervised labels.
3. **Baleen** (§4): a LightGBM binary classifier imitating OPT's admission labels (9
   features: namespace/user/temporary metadata + 1–6 h access counts, §4.1), plus two
   regression models **ML-Range** (which segments to prefetch = imitate `OPT-Range`) and a
   classifier **ML-When** (whether the expected prefetch benefit exceeds ε = 5 ms, Eq 3a–e,
   §4.2). Assumed eviction age and admission threshold are found by an outer/inner
   convergence loop around a Python cache simulator (§4.1). **Baleen-TCO** additionally
   sweeps the flash write rate and picks the TCO-optimal point (§4.3).

**Evaluation setup** (§5.1, App A.8–A.9). Seven Meta Tectonic traces (Region1–7, 2019 /
2021 / 2023; Table 1, Table 2), sampled on the block key space to 0.1–5 % with cache size
scaled proportionally; train on day 1, test on the remaining days. Metrics: Peak/Median
backend load normalised to no-cache, estimated TCO, IO/byte miss rate (Fig 16). Baselines:
CoinFlip, RejectX, CacheLib-ML, Flashield (failed to train on half the samples, App A.5),
and OPT as the ceiling. Results come from the Python simulator, validated against a
CacheLib testbed and against production counters (Fig 11, Figs 21–22).

**Headline numbers.** Baleen cuts Peak DT by 12 % on average vs RejectX at a fixed write
rate, ranging 5–29 % per trace (Fig 9, §5.2); Baleen-TCO cuts estimated TCO by 17 % and
peak load by 16 % (Fig 1, Fig 8). ML-Range saves 16 % of Peak DT over no prefetching and
4 % over "All on Partial Hit" (Fig 13); prefetching on *every* miss is *worse* than not
prefetching, which is what ML-When guards against (Fig 14). Baleen gets the same Peak DT
as RejectX with 55 % less cache (Fig 10).

**Stated limitations / future work** (§3.1, §5.6, §6) — the raw material for add-ons:
explicit Peak-DT optimisation is left for future work and a naive "admit only at high
load" attempt failed; a 16 % gap to OPT remains, 9 % of it from late admissions;
segment-aware admission/prefetch was measured at 11 % potential but "we were unable to
realize this"; early eviction was measured at 11 % potential but "our current ML models
are not accurate enough"; models regress over time in production.

## 2. Artifact audit

### Repo structure

The cloned repo (`repo/`, head `4e3a920`, 2024-02-28) is a thin **wrapper**: README,
`getting-started.sh`, example configs, trace-download scripts, and all the Jupyter
notebooks. **The actual system lives in a git submodule** declared in
`repo/.gitmodules` → `https://github.com/wonglkd/BCacheSim.git`, which this shallow clone
did **not** fetch. Everything under `BCacheSim/` referenced below was read from GitHub
(`wonglkd/BCacheSim`, default branch `main`, Apache-2.0, last push 2024-01-16) and is
**not present on disk** in `repo/`.

```
repo/
  README.md                       badges, install, 2-command example  (repo/README.md:10-12, :84-92)
  getting-started.sh              same commands as a script           (repo/getting-started.sh:27-33)
  .gitmodules                     BCacheSim submodule pointer
  data/get-tectonic.sh            wget of traces + released results   (repo/data/get-tectonic.sh:1-16)
  runs/example/rejectx/config.json           baseline sim config
  runs/example/baleen/prefetch_ml-on-partial-hit/config.json   Baleen sim config
  notebooks/example/example.ipynb            read/plot your own run
  notebooks/paper-figs/fig-*.ipynb           8 notebooks, one per paper figure group
  notebooks/reproduce/reproduce_commands.sh, reproduce_commands_all.sh   full experiment grid
  notebooks/includes/includes-202312.ipynb   imports BCacheSim.* (:24-26, :75-79)
  chameleon/1-getting-started.ipynb, 2-start-dedicated-server.ipynb
```

### Paper component → code path

| Paper component | Code path |
|---|---|
| Episodes model (§3.4) | `BCacheSim/episodic_analysis/episodes.py` *(submodule)* |
| OPT + episode scoring (§3.5) | `BCacheSim/episodic_analysis/policies.py` — `PolicyUtilityServiceTimeSize2` (~L259) is Baleen's `DT_saved/size` score; `PolicyUtilityHits` (~L274) is the hit-rate score used for the non-Baleen baselines; `PolicyUtilityPeakServiceTimeSize` (~L289) is an unused peak-oriented stub |
| Admission training loop (§4.1) | `BCacheSim/episodic_analysis/train.py`, `train_ap.py`; entry point in `repo/getting-started.sh:30` (`--policy PolicyUtilityServiceTimeSize2 --train-models admit prefetch`) |
| Prefetcher training (§4.2) | `BCacheSim/episodic_analysis/train_prefetcher.py` |
| Online admission policies (§2.3, §4.1) | `BCacheSim/cachesim/admission_policies.py` — `RejectXAP` (~L42), `CoinFlipAP` (~L87), `FlashieldAP` (~L148), `LearnedAP` (~L209), `NewMLAP` (~L250, the `"ap": "mlnew"` of `runs/example/baleen/.../config.json:11`), `LocalMLAP` (~L372, online-retrained), `OfflineAP` (~L477 = OPT) |
| ML-Range / ML-When (§4.2, §3.6) | `BCacheSim/cachesim/prefetchers.py` — `Prefetcher` (L14-156), `LearnedRangePrefetcherModel` (L164-207), `LearnedRangeConfPrefetcherModel` (L210-243); the `prefetch_when` / `prefetch_range` keys in `runs/example/baleen/prefetch_ml-on-partial-hit/config.json:27-28` |
| Cache + eviction (§3.3) | `BCacheSim/cachesim/sim_cache.py` (`QueueCache`), `BCacheSim/cachesim/eviction_policies.py` (`LRUPolicy`, `TTLPolicy`, `LIRSCache`) |
| Simulator entry point / DT accounting (§4.1) | `BCacheSim/cachesim/simulate_ap.py` |
| Features (§4.1) | `BCacheSim/cachesim/dynamic_features.py`, `sim_features.py`; `ap_feat_subset: "meta+block+chunk"` (`runs/example/baleen/.../config.json:19`) |
| Testbed CacheBench (§5.1) | `BCacheSim/cachesim/testbed/*.cpp` — harness only; the modified CacheLib itself is **not released** (`repo/README.md:14`) |
| Figures (§5) | `repo/notebooks/paper-figs/` (8 notebooks, matching the Artifact Appendix list on paper p. 18) |

### Build route on this machine

Pure CPU Python. `conda env create -f BCacheSim/install/env_cachelib-py-3.11.yaml`
(Python 3.11 + ~300 conda-forge packages) or, more robustly,
`pip install -r BCacheSim/install/requirements.txt`
(`lightgbm==3.3.5, numpy==1.24.2, pandas==1.5.3, scikit-learn==1.2.2, scipy==1.10.1,
matplotlib==3.7.1, seaborn==0.12.1` + unpinned `spookyhash, jsonargparse, compress_json,
compress_pickle, commentjson, retry, psutil, tqdm, redis, pqdict, jupyterlab`).
No CUDA, no C++ build, no container, no privileged step: `BCacheSim/run_py.sh` is a
`stdbuf`+`python -m` wrapper. `repo_facts.json` reports `red_flags: {}` for the wrapper
repo (note: the submodule was not scanned by the driver; reading its file list shows no
kernel/eBPF/perf/root usage — only the optional `cachesim/testbed/` C++ CacheBench
harness, which is not needed for the simulator results). Pins are ~Q1-2023 vintage:
installable in a dedicated env, but they are old enough that a fresh `numpy`/`pandas` env
would break — pin exactly as given. `redis`/`brooce` are only for the authors' cluster
job queue (`BCacheSim/episodic_analysis/local_cluster.py`, called out in the paper's
Artifact Appendix); GNU parallel/xargs over 16 cores substitutes.

### Data

`repo/data/get-tectonic.sh:1-16` wgets from `https://ftp.pdl.cmu.edu/pub/datasets/Baleen24/`:
`storage_0.1.tar.gz` (15 MB → 76 MB, the 0.1 % traces used for the paper's simulator
results), `results_release.csv.gz` (the authors' intermediate results, which the paper-fig
notebooks plot), and `breakdowns.tar.gz`. The same directory also offers `storage.tar.gz`
/ `storage_0.1_10.tar.gz` (0.15 GB → 0.8 GB, 10 samples each), `storage_10.tar.gz`
(1.6 GB → 8.1 GB) and full traces (150 GB). Everything is public, anonymous HTTP, and the
useful subsets are well under the ~257 GB free. No model weights needed — models are
trained in ~25 s from the trace (`repo/getting-started.sh:29-30`).

### Eval scripts

Present and unusually complete: `repo/notebooks/reproduce/reproduce_commands_all.sh`
contains the literal `train` + `simulate_ap` command pairs for **CoinFlip, RejectX,
Baleen (No Prefetch), Baleen** across all 7 regions × up to 10 samples (≈330 runs), with
the converged eviction ages and thresholds baked in. `reproduce_commands.sh` is a smaller
subset. Gaps: (a) the **CacheLib-ML** and **Flashield** baselines of Fig 9 / Fig 1 are
*not* in these scripts — the policies exist in `admission_policies.py` but their configs
must be re-derived; (b) the paper-fig notebooks read the authors' released
`results_release.csv.gz` and hard-coded run directories (`../runs/exp_reproduce_spring23/...`,
job-ids containing `/users/dlwong/...`), so plotting *your own* runs needs path surgery;
(c) `repo/notebooks/example/example.ipynb` does read your own run output and is the clean
starting point.

### Provenance and badges

`repo/README.md:5` links the paper, the live code repo, the data, a walkthrough video and
a Chameleon Trovi artifact; the paper's Artifact Appendix (p. 18) names the identical
GitHub URL and Trovi share id. `repo/README.md:10-12` embeds the three USENIX badge
images: **Artifacts Available, Artifacts Functional, Results Reproduced**.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | `github.com/wonglkd/Baleen-FAST24` is named in the paper's Artifact Appendix (paper.txt p. 18, "You may view our artifact and its README at https://github.com/wonglkd/Baleen-FAST24") and is the first author's account. It is a real artifact, not a placeholder: `repo/notebooks/reproduce/reproduce_commands_all.sh` (≈330 concrete experiment commands), 8 figure notebooks, runnable configs (`repo/runs/example/*/config.json`). Caveat: the simulator itself is in the `BCacheSim` submodule (`repo/.gitmodules`), which the shallow clone did not fetch — it is public and Apache-2.0, so this is a `git submodule update --init` away, not a blocker. |
| `H2_no_root` | **pass** | Everything needed for the paper's simulator results is user-space Python: `repo/getting-started.sh:27-33` runs `python -m BCacheSim.cachesim.simulate_ap` / `BCacheSim.episodic_analysis.train`; deps come from conda/pip (`BCacheSim/install/requirements.txt`). No Docker, kernel module, eBPF, perf counter, or `/proc/sys` write anywhere in the wrapper repo (`repo_facts.json` `red_flags: {}`). The only privileged-ish artefacts are the optional Chameleon provisioning notebook (`repo/chameleon/2-start-dedicated-server.ipynb`, a cloud convenience we skip) and the unused `BCacheSim/cachesim/testbed/` CacheBench harness. |
| `H3_hardware_fit` | **pass** | The paper's own key results are simulation (paper §5.1 "Our key results use simulation runs"); the released artifact is simulator-only (`repo/README.md:14`). Single-threaded CPU Python, 0.1 % traces of 76 MB, 366 GB *simulated* cache size (`repo/runs/example/rejectx/config.json:28`) — no GPU, no flash, no HDD needed. 16 cores/125 GB RAM runs the ≈330-command grid embarrassingly in parallel. The A5000 is unused (LightGBM trains on CPU in ~25 s, `repo/getting-started.sh:29`). Only the *testbed* validation (Fig 11) needs real HDDs and the unreleased CacheLib fork — out of scope and not required for any headline claim. |
| `H4_obtainable_deps_data` | **pass** | Traces are public and anonymous: `repo/data/get-tectonic.sh:2` wgets `https://ftp.pdl.cmu.edu/pub/datasets/Baleen24/storage_0.1.tar.gz`; the same index publishes 0.1 %/1 %/10 %/full variants (15 MB – 30 GB compressed). Deps are pinned pip/conda packages (`BCacheSim/install/requirements.txt`, `install/env_cachelib-py-3.11.yaml`), all pure-Python/CPU wheels available for Python 3.11. The one non-public element — Meta's exact seek/bandwidth constants — is explicitly substituted by the authors' measured university-testbed constants (`repo/README.md:14`; paper Artifact Appendix "Caveats"), so absolute DT differs slightly but the policy comparison is intact. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** **Figure 9** (paper p. 11): Peak backend load per trace for CoinFlip / RejectX /
CacheLib-ML / Baleen (No Prefetch) / Baleen, supporting the headline claim "Baleen reduces
Peak DT by 12 % on average over RejectX at a fixed flash write rate" (§5.2). Secondary,
cheaper target: **Figure 13/14** (prefetching ablation) via
`repo/notebooks/paper-figs/fig-13,14-prefetching-20230424.ipynb`.

**Scale-down.** Use the 0.1 % traces (`storage_0.1.tar.gz`, the same sample rate the paper
used for the simulator results in Fig 11a) at the default 366.475 GB-equivalent cache and
35.599 MB/s write rate (`repo/runs/example/rejectx/config.json:28`,
`repo/getting-started.sh:30`). Run **7 regions × 4 policies × 3 samples** (the paper uses
10 samples; 3 keeps the Peak-DT variance visible while cutting compute ~3×) ≈ 84 runs
instead of ≈330. Reproduce 4 of Fig 9's 5 bars from scratch and overlay the
CacheLib-ML bar from the released `data/results_release.csv.gz` (its config is not in the
reproduce scripts).

**Steps.**
1. `git clone --recurse-submodules https://github.com/wonglkd/Baleen-FAST24` (the audited
   clone lacks `BCacheSim/`).
2. `pip install -r BCacheSim/install/requirements.txt` into a fresh Python 3.11 conda env
   (prefer pip over the 300-package conda yaml, which is unlikely to solve cleanly today).
3. `cd data && bash get-tectonic.sh` (≈20 MB download for the 0.1 % set + released results).
4. Smoke test exactly `repo/getting-started.sh:27-33` on Region1: RejectX sim (~4 min),
   Baleen train (~25 s), Baleen sim (~30 min); check
   `repo/notebooks/example/example.ipynb` renders Write Rate / Service-Time-Saved / Peak.
5. Extract the matching lines from `repo/notebooks/reproduce/reproduce_commands_all.sh`
   for the chosen (region, policy, sample) subset and drive them with `xargs -P16`.
   Substitute the authors' `../runs/exp_reproduce_spring23/...` output paths for local ones.
6. Aggregate with the loaders in `repo/notebooks/includes/includes-202312.ipynb` and
   re-point `repo/notebooks/paper-figs/fig-09-202309.ipynb` at the local run directory.

**Effort.** ≈4 person-days (most of it path/plumbing surgery in step 5–6, not science) +
≈80 CPU-core-hours ≈ 6–8 wall-clock hours on 16 cores. 0 GPU-hours.

**Level: H.** Build instructions, pinned deps, public data, per-result commands with
converged hyper-parameters, and an artifact with "Results Reproduced" all exist; the
machine is over-provisioned for a CPU-only Python simulation. It is not "H with zero
work" only because the plotting notebooks are wired to the authors' directory layout and
the CacheLib-ML baseline is unscripted.

## 5. Add-on ideas

> Path note: the driver validates `code_locations` against the *checked-out* tree, and the
> simulator lives in the un-fetched `BCacheSim` submodule. The JSON therefore cites the
> configs/scripts in `repo/` that each add-on is driven from; the precise submodule files
> and line numbers are given below in prose.

### A1 — Peak-aware episode scoring and load-adaptive gating ("PeakBaleen")

**Hypothesis.** We hypothesize that scoring episodes by their contribution to the *peak*
10-minute DT windows — and modulating the admission threshold and the ML-When prefetch gate
by the current load level — reduces **Peak DT** by ≥5 % over stock Baleen at the same flash
write rate, on the 7 Meta traces.

**Mechanism.** (i) Add a scoring function alongside
`PolicyUtilityServiceTimeSize2` in `BCacheSim/episodic_analysis/policies.py` (~L259; the
unused `PolicyUtilityPeakServiceTimeSize` at ~L289 is a stub to build on) that weights each
episode's `DT_saved` by the *load percentile* of the 10-minute windows its hits fall into,
so writes are spent on episodes whose hits land in peak windows. Episode timestamps and the
10-min window bucketing already exist (`log_interval: 600.0`,
`repo/runs/example/rejectx/config.json:36`). (ii) Add a load-aware gate in
`BCacheSim/cachesim/prefetchers.py` (the `pf_when` dispatch, ~L103-115): raise the
ML-When confidence threshold off-peak and lower it near peak, using a short trailing-load
estimate rather than an oracle. (iii) Re-run the existing eviction-age / threshold
convergence loop (`BCacheSim/episodic_analysis/train.py`) so the write-rate constraint is
still met. Evaluate with the unchanged harness, which already reports Peak DT.

**Motivating evidence.** §3.1: "As explicitly optimizing admission for the peak introduces
significant complexity, we leave that for future work." §5.6 "Explicitly optimizing Peak
DT": the authors admitted only during high-load periods, "found that while this saved flash
writes, it did not reduce Peak DT", and concluded "more fundamental changes (e.g., scoring
episodes by their usefulness in reducing Peak DT) will be required" — i.e. they name this
exact mechanism as the missing piece. App A.3 / Fig 18 shows Baleen's peak window *moves*
relative to RejectX's and that Baleen's worst windows are those where prefetching does not
pay, so a load-aware prefetch gate has a concrete target.

**Feasibility: H.** Two localized additions (a scoring function and a gate predicate,
order 300–600 LOC) plus re-running the existing convergence loop; no new harness, since
Peak DT is the metric the simulator already emits. Compute is CPU-only and parallel
(~30 min per ML simulation; 7 traces × 3 samples × {Baleen, PeakBaleen} ≈ 21 core-hours
per design iteration).

**Research value: H.** Peak DT is the paper's *own* headline metric and the thing that
sets the HDD count; the authors flag peak-explicit optimisation as unsolved and report a
failed attempt. A positive result is a direct improvement to the paper's main claim; a
negative result with the episode-attribution analysis explains *why* peak is hard (peaks
shift between policies — the "whack-a-mole" effect of App A.3), which is publishable
insight either way.

**Scoop check: clear.** Queries: "peak-aware cache admission policy disk-head time flash
cache load-adaptive 2025"; "'Baleen' flash cache Tectonic traces 2026 admission policy
improve peak disk-head time". Closest prior work is
[CacheSack (ATC'22 / ToS'23)](https://www.usenix.org/conference/atc22/presentation/yang-tzu-wei),
which solves a knapsack over admission policies for *average* cost, not peak, and
[HALP (NSDI'23)](https://dl.acm.org/doi/10.1145/3582014) for eviction. No follow-up to
Baleen found on peak-explicit scoring.

### A2 — Segment-level (chunk-granular) admission and prefetching

**Hypothesis.** We hypothesize that extending episodes, labels and the admission/prefetch
models from block granularity to per-segment granularity reduces **Peak DT** by up to the
11 % that the authors' own offline analysis predicts, under the default 3-DWPD /
400 GB-equivalent regime on all 7 traces.

**Mechanism.** Generate per-segment (or per-contiguous-run) episodes in
`BCacheSim/episodic_analysis/episodes.py`; score and label at that granularity in
`policies.py`; emit per-segment admission decisions from the GBM instead of one decision
for the whole access range. The plumbing partly exists: the simulator already carries
`learned_ap_granularity` (`repo/runs/example/baleen/prefetch_ml-on-partial-hit/config.json:21`,
value `"both"`), `block_level` (:24) and `one_chunk` (:35) switches, and
`NewMLAP` in `BCacheSim/cachesim/admission_policies.py` (~L250) already consumes the
`meta+block+chunk` feature subset. The work is in making the *episode* model and the
write-budget accounting segment-aware, and in letting `sim_cache.py` admit a strict subset
of the fetched range.

**Motivating evidence.** §5.6, "Segment-aware admission & prefetching": "Baleen operates at
the block level and can only choose to admit or reject the entire access range, rather than
individual segments (unlike RejectX). Episode-based analysis showed a potential reduction of
DT by 11 %. However, we were unable to realize this." App A.8 Fig 19d: the median access is
<2 MB of a 5–7 MB block, so block-granular admission systematically over-writes flash.

**Feasibility: M.** Cross-cutting: the episode abstraction (the paper's core contribution)
is block-defined, so segment episodes need new construction and a new size/benefit
accounting, and the OPT ranking must be redone. All Python, all in the existing harness,
but ~1–2k LOC across `episodes.py`, `policies.py`, `sim_cache.py` and the trainers — and
the authors tried and failed, which is a real risk for a 10-week project.

**Research value: H.** It is the single largest quantified gap the paper leaves on the
table (11 % of DT), and the authors explicitly could not realize it. Either outcome is
informative: a win is a large improvement over a FAST'24 system, a principled failure
explains why finer granularity defeats the episode abstraction (e.g. write amplification at
142 kB regions, App B.1).

**Scoop check: clear.** Queries: "'segment-level' OR 'chunk-level' flash cache admission
policy learned granularity 2025 storage cache episodes". Closest work is container-oriented
flash caching — [Kangaroo (SOSP'21)](https://dl.acm.org/doi/full/10.1145/3542928) and
[Pannier](https://dl.acm.org/doi/10.1145/3094785) — which changes the *write* granularity
for tiny objects rather than making learned admission sub-block. Nothing found that does
segment-granular episode-based admission.

### A3 — Learned early eviction (episode-end TTL) instead of LRU

**Hypothesis.** We hypothesize that a third GBM predicting the *end of an episode*, used to
drive TTL-based eviction, reduces mean and Peak DT at a fixed flash write rate by
reclaiming the "dead time" between an item's last hit and its LRU eviction, compared with
Baleen's LRU.

**Mechanism.** Train a regression head (same features as the admission model, labels from
the episode's last access time) in a new module next to
`BCacheSim/episodic_analysis/train_prefetcher.py`; at admission time, stamp the predicted
expiry and evict via the existing `TTLPolicy` (`BCacheSim/cachesim/eviction_policies.py`,
~L119-145) instead of `LRUPolicy` (~L127-139). The hooks are already exposed in the run
config: `evict_by_episode` and `eviction_policy`
(`repo/runs/example/baleen/prefetch_ml-on-partial-hit/config.json:26,42`), and
`QueueCache` in `sim_cache.py` already supports a TTL backend. Sweep a
conservatism margin so that under-prediction (evicting a live item) is penalised
asymmetrically, and report the write-rate/DT frontier.

**Motivating evidence.** §5.6, "Early eviction": "If items could be evicted immediately
after their last access in an episode ... this would eliminate dead time and result in a
greater effective cache size. Episode-based analysis showed mean DT could potentially be
reduced by 11 %. However, our current ML models are not accurate enough to realize this."
§3.3 also lists eviction as the sub-problem Baleen deliberately leaves to LRU.

**Feasibility: H.** One new model + one config switch; both the TTL eviction path and the
`evict_by_episode` flag already exist, and the training pipeline is a copy of the existing
prefetch-range regressor. Evaluated by the unchanged harness on the same traces.

**Research value: M.** The 11 % offline ceiling is attractive and the flash-specific framing
(reclaiming dead space rather than ranking victims) is less explored than generic learned
eviction — but ML eviction is a crowded field (LRB, HALP, MAT, Raven, all cited in §7), so a
moderate win would read as expected rather than surprising.

**Scoop check: partial.** Queries: "learned early eviction flash cache predict end of
residency episode eviction 2025". [MAT (arXiv 2301.11886)](https://arxiv.org/abs/2301.11886)
and [LRB (NSDI'20)](https://www.usenix.org/conference/nsdi20/presentation/song) learn *which*
object to evict next; neither predicts an episode-end TTL under a flash write-rate
constraint, and the paper itself (§7, App A.7) argues the episode formulation is stronger
than Relaxed Bélády for this setting. Related but not the same.

### A4 — Workload drift and cross-region transfer, with online retraining

**Hypothesis.** We hypothesize that Baleen's day-1-trained, per-workload models degrade
monotonically over the 7-day test window and transfer poorly across clusters/years, and
that periodic retraining (the already-implemented online-trained AP) recovers most of the
loss at negligible flash-write cost — quantified as Peak DT per test day and per
(train-region, test-region) pair.

**Mechanism.** No new policy: (i) a driver script that trains on Region *i* / year *y* and
simulates on Region *j* / year *y'* (`--region`, `--trace-group` in
`repo/getting-started.sh:30` and in every line of
`repo/notebooks/reproduce/reproduce_commands.sh`), producing a 7×7 transfer matrix across
2019/2021/2023 traces; (ii) per-day Peak DT instead of whole-window P100, by post-processing
the 10-minute `cache_perf` log the simulator already writes
(`repo/notebooks/example/example.ipynb`); (iii) enable the existing `LocalMLAP` /
`"ap": "mlonline"` path (`BCacheSim/cachesim/admission_policies.py` ~L372, with `GBTrainer`
~L342) which retrains during the run, and sweep the retraining interval.

**Motivating evidence.** §5.1: "the first day of each workload is used as training data,
with the remaining days used for testing" — but no result in the paper decomposes accuracy
or Peak DT *by test day*. §6: "Models often performed the best when they were first deployed
and slowly regressed over time even with retraining using the same set of features"; the
paper answers this only with the weak claim that Baleen "was designed primarily using traces
from 2019 but also demonstrates improvements on traces from 2021 and 2023" (different models
per trace, not transferred models). Table 2 gives traces from 3 years — the transfer
experiment is sitting there unused.

**Feasibility: H.** Scripting plus config sweeps over an existing, already-implemented
policy; no algorithmic change. Compute is the binding cost (49 transfer pairs × ~30 min,
≈25 core-hours, trivially parallel).

**Research value: M.** A real deployment question that the paper raises and does not answer,
and a natural robustness section for an improvement paper; but the qualitative outcome
(offline models decay, retraining helps) is largely expected, and CacheSack already argues
for online training, so the contribution is measurement rather than mechanism.

**Scoop check: partial.** Queries: "flash cache admission policy transfer learning
cross-workload generalization retraining drift storage cache 2025 2026".
[CacheSack (ATC'22)](https://www.usenix.org/system/files/atc22-yang-tzu-wei.pdf) argues
online-trained models are needed because "workloads change much more rapidly than software
updates", but does not measure drift for an episode-trained GBM on these traces. No direct
scoop.

### A5 — Is the ML necessary? A DT-objective heuristic ablation

**Hypothesis.** We hypothesize that most of Baleen's Peak-DT advantage over RejectX comes
from *optimising DT under a write budget with episode-derived labels* rather than from the
GBM itself, and that a size-and-frequency-aware non-ML scorer (a "RejectX+DT" threshold on
`DT_saved/size` estimated from the same 9 features' counts) recovers ≥70 % of Baleen's gain
at a fraction of the complexity.

**Mechanism.** Add a closed-form scorer next to `PolicyHeuristic`
(`BCacheSim/episodic_analysis/policies.py`, ~L330) and a matching online AP next to
`RejectXAP` (`BCacheSim/cachesim/admission_policies.py`, ~L42) that thresholds
`estimated_DT_saved / bytes_written` from the count-min-sketch history features already
tracked in `BCacheSim/cachesim/dynamic_features.py`, with the threshold tuned by the same
write-rate convergence loop. Run it through the unchanged Fig 9 pipeline; the comparison
points (CoinFlip, RejectX, Baleen ±prefetch) are already scripted in
`repo/notebooks/reproduce/reproduce_commands_all.sh`.

**Motivating evidence.** §5.6 reports GBM beats a Transformer by only 0.2 % (App C, Table 3)
and that "Baleen learns [size-awareness] implicitly if size-related features are supplied" —
suggesting the model is doing something simple. §5.6 also observes Baleen "learning to reject
almost all items on the first access (a behavior similar to RejectX)". The paper never
ablates the *objective* (DT vs hits) against the *model class*: `PolicyUtilityHits` vs
`PolicyUtilityServiceTimeSize2` exist side by side in the code but the paper reports only the
combined Baleen-vs-RejectX delta.

**Feasibility: H.** A few hundred LOC, no new data, no new harness; reuses the existing
threshold-convergence loop and figure pipeline.

**Research value: M.** This is the "FIFO queues are all you need"-style question a FAST
reviewer asks about any ML-for-systems paper (and the paper cites [53] itself), and it is a
safe fallback for the course's "careful reproduction / more nuanced result" track. It scores
M rather than H because the likely outcome — ML gives a real but modest edge — refines rather
than overturns the paper.

**Scoop check: clear.** Queries: "flash cache admission ML vs heuristic ablation is ML
necessary caching 2025"; nothing found that ablates Baleen's objective against its model
class. Related in spirit: [S3-FIFO / "FIFO queues are all you need" (SOSP'23)](https://dl.acm.org/doi/10.1145/3600006.3613147),
which the Baleen authors reused for their Flashield baseline (App A.5), but it targets
eviction in DRAM caches, not flash admission under a write budget.

## 6. Risks and open questions

1. **The audited clone is missing the system.** `repo/` contains no simulator; the ~7.5 MB
   are notebooks, configs and shell scripts. `repo/.gitmodules` points at
   `wonglkd/BCacheSim` (public, Apache-2.0, last pushed 2024-01-16). Everything in §2/§5
   about `BCacheSim/*` was read on GitHub, not on disk — confirm with
   `git submodule update --init` before committing to this paper.
2. **Simulator-only artifact.** The CacheLib testbed fork and Meta's real seek/bandwidth
   constants are not released (`repo/README.md:14`; Artifact Appendix "Caveats"), so absolute
   DT will differ from the paper and *no* add-on can be validated on real flash/HDD. All
   claims would be simulator-relative — acceptable for the course, but must be stated.
3. **Peak DT is a P100 statistic on a downsampled trace.** With 0.1 % samples and 1–3 seeds
   instead of the paper's 10, run-to-run variance may be comparable to a 5 % improvement.
   Any add-on claim needs multiple samples and a reported spread; the paper's per-trace range
   (5–29 %, Fig 9) shows how heterogeneous this is.
4. **Plotting is wired to the authors' environment.** Notebook paths embed
   `../runs/exp_reproduce_spring23/...` and job-ids containing `/users/dlwong/...`;
   `data/results_release.csv.gz` is the default data source. Budget real time for
   re-pointing them (or build a thin loader on top of `notebooks/example/example.ipynb`).
5. **Two Fig-9 baselines are unscripted.** CacheLib-ML and Flashield have code
   (`admission_policies.py`) but no reproduce commands; Flashield is additionally reported
   as failing to train on half the samples (App A.5). A fair add-on comparison should use
   RejectX + Baleen and take CacheLib-ML from the released results.
6. **Old pins.** `lightgbm==3.3.5`, `numpy==1.24.2`, `pandas==1.5.3` (Q1 2023) on Python
   3.11 — fine in a dedicated conda env, but the 300-package `env_cachelib-py-3.11.yaml`
   may not solve today; prefer `requirements.txt`. Unverified whether the code is
   pandas-2.x clean.
7. **Compute honesty.** The authors used 624 machine-days for the full grid; ≥30 min per
   ML simulation. Any add-on that requires re-running the eviction-age convergence loop
   across 7 traces × N samples × M configurations must be budgeted in core-hours up front
   — this machine can afford a few hundred core-hours, not thousands.
8. **A1/A2 risk.** Both target things the authors tried and failed at (peak-explicit
   admission; segment granularity). That is exactly why they are valuable, but the project
   must be framed so a negative-but-explained result is a publishable outcome.
9. **Unverified by desk review.** Per-run peak RAM; whether `--fast` mode (seen in
   `reproduce_commands.sh:25`) changes fidelity; whether PyPy (`env_cachelib-pypy-3.8.yaml`)
   is usable for the non-ML baselines to cut wall-clock; the exact line numbers quoted for
   submodule files (obtained from a summarizing fetch, not a direct read).

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; `pages/page-NN.png` for figures)
- §1 Introduction + Fig 1 (TCO/peak/median summary) — p. 2
- §2.2–2.4 DT motivation, write endurance (43 DWPD / 4-month wearout), ML challenges — pp. 3–4
- §3.1 DT and Peak DT definitions; "leave [peak optimization] for future work" — p. 5
- §3.2 + App A.4 TCO function (Eq 2, Eq 4a–e) — pp. 5, 20–21
- §3.3 decomposition (admission / prefetching / eviction; LRU chosen) — pp. 5–6
- §3.4 episodes, Figs 4–5 — p. 6
- §3.5 OPT scoring `DT_saved/size` — p. 7
- §3.6 OPT-Range, when/what to prefetch — p. 7
- §4.1 features, labels, convergence loop, Python simulator, GBM choice — pp. 7–8
- §4.2 ML-Range / ML-When, Eq 3a–e — p. 8
- §4.3 Baleen-TCO, per-workload prefetch choice — p. 9
- §5.1 setup: LightGBM 500 rounds/63 leaves, 0.1–5 % samples, day-1 train split — p. 9
- Table 1 / App A.8 Table 2, Figs 19–20 trace statistics — pp. 9, 21–22
- §5.2 + **Fig 9** (Peak DT per trace, 12 % avg) — pp. 10, 11 (`pages/page-11.png`)
- §5.3 + Fig 8, Fig 12 (TCO, optimal write rate) — pp. 10–12
- §5.4 + **Fig 13, Fig 14** (ML-Range, ML-When; prefetch-every-miss hurts) — pp. 10, 12 (`pages/page-12.png`)
- §5.5 Peak-DT metric discussion — p. 10
- §5.6 negative results: failed peak extension, 16 % OPT gap, segment-awareness 11 %, early eviction 11 %, prefetch-on-PUT — pp. 10–11
- §6 production lessons: model regression over time, DRAM rethink — pp. 11–12
- §7 related work (CacheSack, Kangaroo, LRB, HALP, MAT, S3-FIFO) — p. 12
- Artifact Appendix: GitHub URL, Trovi share, notebook↔figure map, 624 machine-days, caveats — p. 18
- App A.3 Fig 18 peak-window breakdown; A.5 Flashield failure; A.9 testbed hardware; A.11 Figs 24–25 — pp. 20–24
- App C Cache Transformer, Table 3 (GBM 0.2 % better) — pp. 24–26

**Repository** (paths relative to `repo/`)
- `README.md` — badges (:10-12), simulator-only scope + nomenclature (:14), install (:55-75), 2-command example (:84-92), 624 machine-days (:128-129)
- `.gitmodules` / `repo_facts.json` — `BCacheSim` submodule → `github.com/wonglkd/BCacheSim`; `red_flags: {}`; head commit 2024-02-28
- `getting-started.sh` — :13 conda env, :22-23 trace download, :27-33 RejectX/train/Baleen commands
- `data/get-tectonic.sh` — :2 `storage_0.1.tar.gz`, :9 `results_release.csv.gz`, :11 `breakdowns.tar.gz`
- `runs/example/rejectx/config.json` — `ap: rejectx` (:7), `size_gb: 366.475` (:28), `log_interval: 600.0` (:36)
- `runs/example/baleen/prefetch_ml-on-partial-hit/config.json` — `ap: mlnew` (:11), `ap_threshold` (:18), `ap_feat_subset` (:19), `learned_ap_granularity` (:21), `block_level` (:24), `evict_by_episode` (:26), `prefetch_when/range` (:27-28), `one_chunk` (:35), `eviction_policy: LRU` (:42)
- `notebooks/reproduce/reproduce_commands.sh` — :3-58, exact train+simulate pairs with converged eviction ages/thresholds
- `notebooks/reproduce/reproduce_commands_all.sh` — ≈330 commands: CoinFlip/RejectX/Baleen(±prefetch) × 7 regions × up to 10 samples; **no** CacheLib-ML or Flashield
- `notebooks/example/example.ipynb` — :53-54 reads local run outputs; :72 metric columns
- `notebooks/includes/includes-202312.ipynb` — :24-26, :75-79 imports of `BCacheSim.cachesim` / `BCacheSim.episodic_analysis`
- `notebooks/paper-figs/fig-09-202309.ipynb`, `fig-13,14-prefetching-20230424.ipynb`, `fig-18-peak-hrs-20230424.ipynb`, `fig-01a,08,12-202309-tco.ipynb`, `fig-10a,24-wr-20230414.ipynb`, `fig-10b,25-csize-20230424.ipynb`, `fig-07,19,20-tracestats-20230504.ipynb`, `fig-01bc,16-202309.ipynb`
- `notebooks/reproduce/exps-cluster-sample.ipynb` — :114 reads `data/results_release.csv.gz`
- `chameleon/1-getting-started.ipynb`, `chameleon/2-start-dedicated-server.ipynb`

**Submodule, read on GitHub (not on disk)** — `wonglkd/BCacheSim@main`, Apache-2.0, pushed 2024-01-16
- `cachesim/admission_policies.py` (RejectXAP ~L42, CoinFlipAP ~L87, FlashieldAP ~L148, LearnedAP ~L209, NewMLAP ~L250, GBTrainer ~L342, LocalMLAP ~L372, OfflineAP ~L477, construct ~L567)
- `cachesim/prefetchers.py` (Prefetcher L14-156, pf_when dispatch ~L103-115, LearnedRangePrefetcherModel L164-207, LearnedRangeConfPrefetcherModel L210-243)
- `cachesim/eviction_policies.py` (EvictionImpl ~L102, TTLPolicy ~L119-145, LRUPolicy ~L127-139, QueueCache ~L564-850, `evict_by='episode'` ~L407)
- `cachesim/sim_cache.py`, `cachesim/simulate_ap.py`, `cachesim/dynamic_features.py`, `cachesim/sim_features.py`
- `episodic_analysis/episodes.py`, `policies.py` (PolicyUtilityServiceTimeSize2 ~L259, PolicyUtilityHits ~L274, PolicyUtilityPeakServiceTimeSize ~L289, PolicyHeuristic ~L330), `train.py`, `train_ap.py`, `train_prefetcher.py`, `local_cluster.py`
- `install/requirements.txt` (lightgbm 3.3.5, numpy 1.24.2, pandas 1.5.3, scikit-learn 1.2.2, scipy 1.10.1, matplotlib 3.7.1, seaborn 0.12.1 + unpinned utils), `install/env_cachelib-py-3.11.yaml`, `run_py.sh`
- `cachesim/testbed/*.cpp`, `run_cachebench.sh` (unused for simulator results)

**External**
- Trace/data index: `https://ftp.pdl.cmu.edu/pub/datasets/Baleen24/` — `storage_0.1.tar.gz` 15 MB→76 MB; `storage_0.1_10.tar.gz` 0.15 GB→0.8 GB; `storage_10.tar.gz` 1.6 GB→8.1 GB; full 30 GB→150 GB
- Artifact page: `https://www.usenix.org/conference/fast24/presentation/wong`; Chameleon Trovi share `aa6fb454-6452-4fc8-994a-b028bfc3c82d`
- Scoop-check sources: CacheSack ATC'22 / ToS'23, Kangaroo ToS/SOSP'21, Pannier ToS'17, LRB NSDI'20, HALP NSDI'23, MAT arXiv:2301.11886, S3-FIFO SOSP'23
