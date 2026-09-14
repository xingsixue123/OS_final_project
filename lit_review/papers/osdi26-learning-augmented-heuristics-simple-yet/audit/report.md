# Learning-Augmented Heuristics: Simple Yet Smart, Robust and Interpretable Cache Eviction

OSDI '26 · Xia, Nixon, Marthen, Bhandari, Yang (Harvard / UIUC / U Chicago / ITB / Meta)
Repo audited: `https://github.com/cacheMon/osdi26-s4-fifo` @ `000095f` (2026-05-12)
arXiv preprint: 2608.27975 · authors' blog: systems.seas.harvard.edu/blog/learning-augmented-heuristics/

---

## 1. Paper summary

**Problem.** Production caches use static heuristics (LRU, 2Q, S3-FIFO, SIEVE) because they are
simple and fast; "smart" caches (ARC, LeCaR, LRB, LHD, GL-Cache, 3L-Cache) rarely get deployed.
The paper argues (§2.3–2.4, Table 1) that existing smart caches sit in three of four quadrants of a
(learning granularity × prediction frequency) design space, and each quadrant has a characteristic
failure: object-level learning suffers *objective mismatch* (Fig. 2) and per-object metadata
overhead; per-miss adaptation suffers instability and delayed reward (Fig. 3).

**Key idea.** Occupy the empty quadrant: *periodic, cache-level* learning. Don't learn a new
eviction policy — learn to **configure** a simple one. The framework is called **Learning-Augmented
Heuristics (LAH)** (§3, Fig. 4): a deterministic parameterised heuristic on the data plane, and an
asynchronous control plane that reads cache-level features and picks a parameter set from a
pre-trained "foundation model for caches" (zero-shot, no per-deployment retraining).

**Design (S4-FIFO, §4).** S3-FIFO's three FIFO queues (small / main / ghost) with five exposed knobs
(Table 2): small-queue ratio ρS ∈ [0.05, 0.90], ghost ratio ρG ∈ [0.90, 6.00], skip ratio κ ∈ {0, 0.25},
small→main threshold τS ∈ {1, 2}, ghost→main threshold τG ∈ {0, 1}. The skip ratio creates a virtual
probationary region (Fig. 5) without a fourth physical queue. The space is discretised to 168
configurations and reduced to **18 representative classes** by greedy set cover (§4.3.3). Features are
73-dimensional (Table 3): 3 × 20-bin hit-position histograms, 3 queue hit ratios, log cache size and
10 composite features. Inference minimises expected regret under a **FIFO-anchored asymmetric cost
matrix** `L[k][j] = E[(MR(c_k) − MR(c_j)) / MR_FIFO]` (§4.3.1) — this is the stated source of the
robustness result. The paper states the model is a GBDT with **20 trees of max depth 9**, exported
with m2cgen to dependency-free C/C++/Go/Rust/Java/JS, inference < 2 ms, total learning storage
overhead "on the order of tens of kilobytes" (§4.4.1, §4.4.3).

**Evaluation setup (§5.1, Table 4).** 5,175 production traces from 14 sources (traces with < 100 K
objects excluded), randomly split 4,140 train / 1,035 test. Three cache sizes: 0.1 %, 1 %, 10 % of each
trace's working-set size. Miss ratios from libCacheSim; throughput from CacheBench on CacheLib
(48 threads, 20-node cluster with 32 cores / 192 GB each — the *cluster* is for parallelism, each run
is single-node). Baselines: S3-FIFO, LIRS, ARC, 2Q, LRB, 3L-Cache, LHD, GL-Cache, LeCaR.
Protocol: run the first 20 % of each trace with default parameters to collect features, make **one**
prediction, run the remaining 80 % with the predicted parameters (v1 = online); v2 = the retrospective
variant that applies the predicted parameters to the whole trace.

**Headline numbers.**
- Efficiency (Fig. 6a, large cache = 10 % WSS): S4-FIFO gives **+26 %** higher mean miss-ratio reduction
  over FIFO than S3-FIFO, **+8 %** over 3L-Cache. At 0.1 % (Fig. 6b) it is slightly behind 3L-Cache.
- Offline S4-FIFO (grid-search optimum) is at most 0.2 pp above learned v2 (§5.2).
- Robustness (Fig. 7a/7b): worst-trace miss-ratio increase over FIFO is **0.8 %** (large) / 0.2 % (small)
  vs 8.8 % for 3L-Cache, 20–72 % for LIRS/LRB, 4.3 % for 2Q. 10th-percentile trace (Fig. 7c/d): S4-FIFO
  still *reduces* FIFO's miss ratio by 4.2 % / 3.6 %.
- Throughput (Fig. 8): parity with S3-FIFO/LRU/2Q, beats TinyLFU.
- Why it works (§5.5): histogram features = 75 % of importance (Fig. 9); top-1 ≈ 60 %, top-2 ≈ 70 %,
  top-3 ≈ 80 % with several thousand training traces (Fig. 10); a model trained on CDN2 transfers to
  Twitter (Fig. 11); predicted-parameter rank distribution is tight vs the default (Fig. 13).
- Interpretability (§5.6, Fig. 14): an LLM picks the better of two configurations with 83 % / 86 %
  accuracy given the feature vector.

**Stated limitations / future work.** §4.2: "For simplicity, our evaluation makes a single prediction per
trace… We leave the choice of refresh policy and interval outside the scope of this work." §5.4: periodic
or sampled feature collection "left to future work". §5.5: extending LAH to LRU/2Q/ARC/LeCaR
"requires policy-specific feature engineering… beyond the scope of this work."

---

## 2. Artifact audit

### 2.1 Repository shape

The audited repo is a thin wrapper (42 files, 0.5 MB, 7,871 lines of Python) around two git submodules:

| path | what | present in clone? |
|---|---|---|
| `libCacheSim/` | submodule → `haochengxia/libCacheSim` branch `s4-fifo` (first author's fork) | **no** (not fetched) |
| `CacheLib/` | submodule → `williamnixon20/CacheLib` branch `fork-w-s4fifo` (second author's fork) | **no** |
| `analysis/` | 22 Python scripts: training, evaluation, plotting | yes |
| `doc/` | `GUIDE.md`, `REPRODUCTION.md`, one SVG | yes |
| `Dockerfile`, `Makefile`, `requirements.txt`, `README.md`, `BLOG.md` | build + docs | yes |

`.gitmodules` names both forks. I verified the libCacheSim fork out-of-band: branch `s4-fifo`,
head `b6d292e` (2026-05-12, message "update"), and it contains a real implementation —
`libCacheSim/cache/eviction/S4FIFO.c` (22,554 B), `S4FIFO.h` (7,923 B), `S4FIFO_base.c` (9,769 B),
`S4FIFO_features.h` (14,009 B), `S4FIFO_verify.c` (19,083 B), plus a `grid_search/` directory
(`conf.py`, `conf_1..3.json`, `yield_tasks.py`, `apply.sh`, `trace_lists.txt`) that is the Phase-2
grid-search harness. So the artifact is real, not a placeholder.

### 2.2 Paper component → code path

| paper component | code path | status |
|---|---|---|
| S4-FIFO data path, 5 knobs (§4.2, Table 2, Fig. 5) | `libCacheSim/libCacheSim/cache/eviction/S4FIFO.c`, `S4FIFO.h` (submodule) | present; `S4FIFO_base_params_t` carries `small_size_ratio`, `ghost_size_ratio`, `move_to_main_threshold`, `small_skip_ratio`, `ghost_to_main_threshold` — exactly the paper's five knobs, defaults `0.10/0.90/2/0/0` matching Table 2 |
| Feature collection, 73 dims (§4.4.2, Table 3) | `libCacheSim/libCacheSim/cache/eviction/S4FIFO_features.h` (submodule) | present: `bucketed_hit_pos_tracker_t` (with the ghost deletion-count correction of §4.4.2), `S4FIFO_feature_collector_t`, `S4FIFO_feature_vector_t`, `feature_collector_get_features()`, `feature_vector_print()`. **Statistics + dump only — no scoring code.** |
| Oracle / grid variant (`s4fifo-verify`) | `S4FIFO_verify.c` (submodule) | present |
| 168-config grid search (§4.2, Phase 2) | `libCacheSim/grid_search/` (submodule) | present |
| Greedy set cover → 18 classes (§4.3.3) | — | **absent.** `analysis/create_grid_optimal.py` only takes an argmin over `grid_full.csv`; the 18 classes appear only as a hard-coded literal (`analysis/train_xgb_18class.py:15-34` and five other scripts). The set-cover algorithm itself is not released. |
| Cost-sensitive objective / risk-minimising inference (§4.3.1) | `analysis/train_xgb_18class.py:402-514` (`build_empirical_cost_matrix`, `expected_risk = probs @ C.T`, `argmin`) | present and faithful to the formula |
| GBDT model (§4.4.1) | `analysis/train_xgb_18class.py:342-372`, `analysis/train_xgb_18class_lite_logc.py:351-382` | present as *training code* |
| **Pre-trained model** ("foundation model", the paper's central artifact) | — | **absent.** `analysis/.gitignore:2-5` excludes `xgb_18class_results/`, `xgb_results/`, …; a recursive tree listing of the libCacheSim fork at `b6d292e` contains **no** file whose path matches `model`, `ensemble`, or `m2cgen`, and `S4FIFO.h` contains none of the words `model`, `config`, `predict`-as-inference. |
| m2cgen export to C/Go/Rust/Java/JS (§4.4.1) | `analysis/export_models_multilang.py` | present, but loads `xgb_18class_results_lite/ensemble_models.pkl` (line 420) which is gitignored |
| CacheLib prototype + CacheBench (Fig. 8) | `CacheLib/` submodule | present upstream, not fetched |
| Fig. 9 feature importance | `analysis/export_feature_importance.py`, `plot_feature_importance.py` | present |
| Fig. 10 training-data scaling | `analysis/learning_curve_experiment.py` | present |
| Fig. 11 cross-dataset | `analysis/cross_dataset_simple.py`, `cross_dataset_optimized.py` | present but trains on `tencentBlock` and tests on all others, not CDN2 → Twitter as §5.5 describes; also needs `trace.txt`, gitignored as "internal cluster trace lists" (`analysis/.gitignore:21`) |
| Fig. 7 robustness tables | `analysis/check_tail_performance.py` | present (reads `cleaned/tail_stats_ratio_*_vs_fifo.csv`, gitignored) |
| Fig. 14 LLM interpretability | — | **absent**; no prompt, harness or transcript in the repo |

### 2.3 What is missing and why it matters

Everything in `analysis/` reads three families of CSV that are **gitignored** (`analysis/.gitignore:8-12`):
`features_20pct.csv`, `cleaned/{0.001,0.01,0.1}/{grid_full,grid_optimal,baselines}.csv`, and
`aggregated_results.csv`. The README calls them "regenerated from simulation" — true, but that means
*regenerating the entire 168-config × 5,175-trace × 3-ratio grid* before a single training script will run.
The column schema (`hits_small`, `hits_main`, `hits_ghost`, `total_hits`, `total_misses`, `total_reqs`,
`H_s/H_m/H_g`, `rho_unique`, `rho_onehit`, `log_C`, `hist_{small,main,ghost}_0..19`, and
`s_param/m_param/t_param/g_param/miss_ratio`) is recoverable by reading the scripts, but the glue between
the C `feature_vector_print()` dump and the CSV is not released.

Documentation drift to be aware of: `doc/GUIDE.md:178` points at `scripts/quick_eval.py` and
`doc/GUIDE.md:200` at `analysis/evaluate.py`; neither exists. `doc/REPRODUCTION.md:77` lists ρG ∈ {3×, 6×}
(that would give 112 configurations, not 168; the scripts use {0.9, 3.0, 6.0}, which gives 7×3×2×2×2 = 168).
`doc/REPRODUCTION.md:45` says traces under **1 M** objects were filtered, the paper (§5.1) says **100 K**.

### 2.4 Three discrepancies between the released code and the paper's claims

These are the most consequential findings of this audit and they drive both the reproduction plan and
the add-on ideas.

**(a) The train/test split in the released training code is hand-curated, not random.**
The paper (§5.1) says "We randomly split the traces into two sets: 4140 for training and 1035 for
evaluation." `analysis/train_xgb_18class.py:296-329` (and identically
`train_xgb_18class_lite_logc.py:306-339`) instead calls
`split_by_trace(..., force_train_traces=worst_traces_for_train, force_test_traces=showcase_test_traces)`
where `worst_traces_for_train` is a list of **27 named traces** annotated with the regression they
previously caused ("`io_traces.ns738` — Was -1.52 % at ratio=0.1", "`cf_allcolo.ns180` — Was -0.22 % at
ratio=0.001"), and `showcase_test_traces` is a list of 6 traces annotated
"Best18 >> ARC/LeCaR (clear advantage) … `tencentBlock.ns9193` — Best18: +28.8 %, ARC: -9.7 %".
In other words, every trace on which the method previously regressed against FIFO was moved into the
*training* set, and traces on which it beats the adaptive baselines were pinned into the *test* set.
Figure 7's 0.8 % worst-case number and Figure 6's comparison with ARC/LeCaR are computed on that split.

**(b) The model is far larger than the paper's overhead analysis states.**
§4.4.3 bounds inference at O(T·D) with "T is the number of trees (20 in our model) and D is the maximum
depth (9 in our model)", and §4.4.3/`BLOG.md:151` claim total learning overhead "on the order of tens of
kilobytes". The released trainer (`analysis/train_xgb_18class.py:343-361`) fits **20 separate LightGBM
models** with `n_estimators = 200 + 20·i` (200…580), `max_depth = 6..9`, `num_leaves = 31..126`, over 18
classes — i.e. on the order of 10⁵ trees, not 20. The "lite" variant
(`train_xgb_18class_lite_logc.py:353-368`) is 5 models × 50 estimators × 18 classes ≈ 4,500 trees.
`analysis/export_models_multilang.py:456-457` prints each exported model's size in **MB** and the
per-language total in MB. Nothing in the repo produces a 20-tree model.

**(c) Reported top-k accuracy uses an undisclosed tolerance, and the reported miss ratios are table
lookups, not simulations.** `analysis/learning_curve_experiment.py:178-211` (Fig. 10) and
`cross_dataset_simple.py:127-151` (Fig. 11) count a prediction as top-1 *correct* whenever the predicted
configuration's miss ratio rounds (4 dp) to the optimum's, not only when the class matches — the paper
(§5.5) defines top-1 as "the fraction of traces in which the predicted parameters are ranked top-1".
Separately, `train_xgb_18class.py:518-551` computes the "S4-FIFO" miss ratio by looking the predicted
configuration up in `grid_full.csv`, i.e. it evaluates the **v2 retrospective** variant only; the online
v1 variant (20 % warmup with defaults) requires the simulator and is not produced by any released script.

**(d) The pre-trained model is not embedded in the simulator.** `S4FIFO.c`'s default parameter string is
`"small-size-ratio=0.10,…,feature-collect-reqs=10000,feature-num-buckets=16,prediction-interval=0"` —
knobs for feature collection and a re-prediction interval exist, but no inference code and no table of
18 configurations was found in `S4FIFO.c`, `S4FIFO.h` or `S4FIFO_features.h`, and no model file exists
anywhere in the fork's tree. How `s4fifo` obtains predicted parameters at run time is **unclear** from
desk review and must be settled by fetching the submodule.

### 2.5 Build route on *this* machine (desk prediction)

`Dockerfile:9-17` installs `build-essential cmake pkg-config libglib2.0-dev libgoogle-perftools-dev
libzstd-dev python3-pip` — all replayable without root:

```
conda create -n s4fifo python=3.11
conda install -c conda-forge glib pkg-config zstd gperftools cmake
cmake .. -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DUSE_HUGEPAGE=OFF
```

The upstream `CMakeLists.txt` requires Threads, GLib-2.0 (via `pkg_check_modules`), `argp` (in glibc 2.36)
and, optionally, ZSTD (`OPT_SUPPORT_ZSTD_TRACE`, default ON — needed, the public traces are `.zst`).
`USE_HUGEPAGE` defaults **ON**; `Dockerfile:31` already passes `-DUSE_HUGEPAGE=OFF`, so the escape hatch
is documented. gcc 12.2 and cmake 3.25.1 on the machine satisfy the README's "gcc ≥ 11, cmake ≥ 3.12".
3L-Cache / LRB / GL-Cache baselines are behind `ENABLE_3L_CACHE` / `ENABLE_LRB` / `ENABLE_GLCACHE`
(all default OFF) and need LightGBM/XGBoost **C libraries** — available on conda-forge, but this is real
porting work and is the main H4-adjacent risk.

Python side: `requirements.txt` has **no upper pins** (`numpy>=1.21`, `lightgbm>=3.3`, `xgboost>=1.5`,
`m2cgen>=0.9`, `torch>=1.10`, `jupyter`). Two version hazards visible from reading:
`learning_curve_experiment.py:125` uses `groupby().apply(..., include_groups=False)` (pandas ≥ 2.2) while
`train_xgb_18class.py:253` uses the deprecated form — the scripts disagree with each other about the
pandas version. `torch` is only needed by `analysis/gpu/train_deep_classifier.py`, which is gitignored.

### 2.6 Data sources

`doc/REPRODUCTION.md:41`: "Because many of these traces contain proprietary data, they are available upon
request." The proprietary part is CDN 1 (163, `akamai_*` in the scripts), CDN 2 (890, `cf_*`), Meta
Storage/CDN (8) and Tencent Photo (2) — roughly 1,060 of 5,175. The remainder is public **in the same
`oracleGeneral` format from the same group**: `cacheMon/cache_dataset` publishes Tencent CBS (4,030),
Alibaba block (1,000), CloudPhysics (106), Twitter Twemcache (54), MSR (13), Wikimedia CDN (3), Meta KV (5),
all zstd-compressed on `s3.amazonaws.com/cache-datasets/`. `analysis/train_traces.txt` (5,171 lines) gives
the exact per-trace names used, so the public subset can be matched name-for-name.
`libCacheSim/data/cloudPhysicsIO.vscsi` (3.6 MB) ships with the fork for the smoke test.

---

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | `cacheMon/osdi26-s4-fifo` is under the libCacheSim org; `.gitmodules` points at forks owned by the first two authors (`haochengxia/libCacheSim#s4-fifo`, `williamnixon20/CacheLib#fork-w-s4fifo`); the paper's footnote 1 (p. 2242) points to libcachesim.com. The submodule contains the real system: `libCacheSim/cache/eviction/S4FIFO.c` (22.5 KB), `S4FIFO.h`, `S4FIFO_base.c`, `S4FIFO_features.h`, `S4FIFO_verify.c` and a `grid_search/` harness; `analysis/` holds the training pipeline. **Caveat (does not flip the verdict, but is the top risk):** the *pre-trained model* — the paper's headline artifact — is not in either repo (`analysis/.gitignore:2-5`; no model/ensemble/m2cgen path in the fork's recursive tree at `b6d292e`), nor are the feature/label CSVs every training script reads. |
| `H2_no_root` | **pass** | Everything that produces a miss-ratio number is user-space trace-driven simulation. `Dockerfile:9-17` lists only build-time libs (glib, gperftools, zstd) that conda-forge provides; `Dockerfile:31` already passes `-DUSE_HUGEPAGE=OFF`, so the one root-adjacent option is optional. No kernel module, eBPF, perf counter, KVM or `/proc/sys` write appears anywhere. The two `sudo` grep hits are `README.md:55` (apt for the same libs — replaceable by conda) and `README.md:84` (`getdeps.py install-system-deps` for CacheLib), which is needed only for the CacheBench throughput figure (Fig. 8) — explicitly not needed for any miss-ratio result (§5.1: "All miss ratio results are from libCacheSim"). Fig. 8 is therefore out of reach and should be dropped. |
| `H3_hardware_fit` | **pass** | CPU-only, single-node, embarrassingly parallel across traces/configs (§4.4.3: "the grid search is embarrassingly parallel across traces, cache sizes, and configurations"). `doc/REPRODUCTION.md:227` gives a minimum of "4 cores, 16 GB RAM" — the machine has 16 cores / 32 threads and 125 GB. Cache sizes are 0.1–10 % of each trace's working set, so per-run RSS is well under a GB. No GPU needed (`analysis/gpu/train_deep_classifier.py` is an optional, gitignored side experiment). The only binding constraint is disk: `doc/REPRODUCTION.md:229` recommends 500 GB for the full grid and only ~257 GB is free, so the trace corpus must be subsetted — a scale-down that still tests the claim (see §4). |
| `H4_obtainable_deps_data` | **pass** | Deps: all conda/pip-installable in user space (§2.5). Data: the paper's exact corpus is partly proprietary (`doc/REPRODUCTION.md:41`), but a public substitute covering the same sources and the same binary format is published by the same group at `cacheMon/cache_dataset` (Tencent CBS 4,030 / Alibaba 1,000 / CloudPhysics 106 / Twitter 54 / MSR 13 / Wikimedia 3 / Meta KV 5, on `s3.amazonaws.com/cache-datasets/`), and `analysis/train_traces.txt` names the exact traces so the public subset can be matched. Model weights are not downloadable, but they are re-derivable from the released training code on those public traces — no external/gated asset is required. |

No `fail`, no `unclear` ⇒ not rejected on hard filters.

---

## 4. Reproduction plan

**Target: Figure 6(a)** — mean and median miss-ratio reduction over FIFO at the large cache size
(10 % of working set), specifically the three bars that carry the paper's central claim:
`FIFO → S3-FIFO → S4-FIFO (v2) → Offline S4-FIFO`, i.e. the assertion that S4-FIFO gives **+26 %** higher
mean miss-ratio reduction than S3-FIFO and lands within 0.2 pp of the grid-search optimum (§5.2).
Secondary target, essentially free once Fig. 6a exists: the **Fig. 7a worst-trace** bar for S4-FIFO,
S3-FIFO, 2Q, ARC and LeCaR.

**Scale-down.** ~300–400 public `oracleGeneral` traces instead of 5,175: all 106 CloudPhysics, all 54
Twitter, all 13 MSR, plus a stratified ~200 from Tencent CBS and Alibaba block, chosen from the names in
`analysis/train_traces.txt` (this keeps the block/KV/object mix of Table 4 minus the proprietary CDN
sources, and fits the 257 GB disk budget). Grid reduced from 168 configurations to the **18 released
classes** (`analysis/train_xgb_18class.py:15-34`) plus the S3-FIFO default; this is exactly what the
trained model can choose among, so it reproduces the claim rather than approximating it. Cache sizes
0.1 % / 1 % / 10 % of WSS as in §5.1. Drop the CacheBench throughput figure entirely (needs root).
Drop 3L-Cache / LRB / LHD / GL-Cache from the first pass (they need LightGBM/XGBoost C libraries linked
into libCacheSim); keep FIFO, LRU, 2Q, ARC, LeCaR, LIRS, SIEVE, S3-FIFO, which need no extra deps.

**Steps.**
1. Build the fork in a conda env with `-DUSE_HUGEPAGE=OFF -DENABLE_TESTS=OFF`; validate with
   `make test` (`Makefile:18-26`), which should report miss ratio ≈ 0.48 on `cloudPhysicsIO.vscsi`
   for all three of `s4fifo`, `s4fifo-base`, `s4fifo-verify` (`doc/REPRODUCTION.md:32-37`).
2. Download the trace subset from `s3.amazonaws.com/cache-datasets/`; compute each trace's WSS to
   derive the three absolute cache sizes.
3. Regenerate `cleaned/{0.001,0.01,0.1}/grid_full.csv` by running the 18 configs per trace per size via
   `-e "small-size-ratio=…,ghost-size-ratio=…,move-to-main-threshold=…,ghost-to-main-threshold=…"`
   (`README.md:130-147`), and `baselines.csv` by running FIFO/LRU/2Q/ARC/LeCaR/LIRS/SIEVE/S3-FIFO.
   `analysis/create_grid_optimal.py` then produces `grid_optimal.csv` unchanged.
4. Regenerate `features_20pct.csv` with `-e "collect-features=true,feature-collect-reqs=<20 % of trace>,
   dump-file=…"` (`doc/REPRODUCTION.md:104-107`) and write the ~25-line adapter from
   `feature_vector_print()` output to the CSV schema the scripts expect (§2.3).
5. Run `analysis/train_xgb_18class.py` unmodified to get the paper's numbers under the paper's own
   (hand-curated) split; then run it again with `force_train_traces=None, force_test_traces=None` to get
   the honest-split numbers. Compare against Fig. 6a / Fig. 7a.
6. For the online **v1** variant, re-run the simulator with the predicted per-trace configuration applied
   only after the 20 % mark (`prediction-interval` / a two-phase driver script) — this is the piece with
   no released harness.

**Effort.** ≈ 12 person-days + ≈ 150 CPU-core-hours (≈ 5–6 wall-clock hours on 30 threads) for the
simulation grid, plus ~40 GB–150 GB of trace download. No GPU hours. Breakdown: 2 d build + trace
plumbing, 2 d WSS/harness scripting, 1 d grid runs (mostly waiting), 4 d feature-CSV adapter and getting
the training scripts to run end-to-end, 3 d analysis and plotting (Fig. 6/7 plotting scripts read
`cleaned/`, which the team now has).

**Level: M.** Not **H**, because (i) the pre-trained model, all feature CSVs and all grid CSVs are absent,
so *every* number must be regenerated before any released script executes; (ii) the exact corpus is ~20 %
proprietary, so the absolute 26 % / 0.8 % figures cannot be matched, only the qualitative claim; (iii) the
adapter between the C feature dump and the Python training pipeline is not released; (iv) `doc/GUIDE.md`
points at scripts that do not exist, and there is no artifact badge. Not **L**, because the simulator, the
five knobs, the feature collector, the grid-search harness, the 18 classes, the cost matrix and the full
training pipeline *are* released and readable; the traces are public in the exact format; and the whole
thing is CPU-only and fits comfortably on this machine.

---

## 5. Add-on ideas

### AO1 — Leakage-free re-evaluation plus a calibrated abstention fallback

> **Hypothesis.** We hypothesize that replacing the hand-curated train/test split and bare
> expected-risk-argmin inference with (a) a leakage-free grouped/leave-one-source-out split and (b) a
> calibrated **abstention rule** that falls back to the S3-FIFO default configuration when the model's
> regret margin is small, restores S4-FIFO's ≤ 1 % worst-case miss-ratio regression versus FIFO under an
> honest split, at ≤ 1 percentage point of mean miss-ratio reduction.

- **Mechanism.** (1) Drop `force_train_traces` / `force_test_traces`; evaluate under grouped 5-fold CV and
  leave-one-source-out, reporting worst-trace and P10 exactly as Fig. 7 does. (2) After the expected-risk
  computation, instead of `argmin`, emit the default configuration `(ρS=0.10, τS=2, τG=0, ρG=0.90)`
  whenever `risk(default) − min_k risk(k) < τ`; calibrate τ on a held-out fold to a target worst-case
  regression (e.g. ≤ 0.5 %) and report the mean cost of that guarantee. This makes the paper's stated
  robustness mechanism ("selects parameters from a validated set of safe configurations", §3) an explicit,
  tunable knob with a measurable efficiency/robustness frontier rather than an emergent property.
- **Code locations.** `analysis/train_xgb_18class.py` (split at :296-329, risk-minimising inference at
  :488-514), `analysis/train_xgb_18class_lite_logc.py`, `analysis/check_tail_performance.py`,
  `analysis/create_improvement_report.py`.
- **Motivating evidence.** Paper §5.1 claims a random split; `analysis/train_xgb_18class.py:296-312`
  force-feeds 27 named previously-regressing traces into training with comments recording the exact
  regression each caused, and `:316-325` pins 6 favourable traces into the test set. Figure 7a's 0.8 %
  worst-case and Figure 7c's 10th-percentile numbers are the paper's most distinctive claims and are
  computed on that split.
- **Feasibility: H.** A < 300-line change to Python that already exists, evaluated on the grid CSVs the
  team regenerates for the reproduction target — no simulator work, no new compute beyond §4.
  (Dependency: it presupposes step 3 of §4 succeeded.)
- **Research value: H.** It tests the paper's flagship claim with the paper's own code, and *both*
  outcomes are informative: if robustness survives the honest split, the curation was cosmetic and the
  result is stronger than the artifact suggests; if it does not, the abstention rule is a principled fix
  that restores the guarantee and quantifies its price. A reviewer at OSDI would care about either.
- **Scoop check: clear.** Queries: "S4-FIFO learning-augmented heuristics cache eviction follow-up 2026";
  "cache policy selection model abstention fallback conformal prediction robustness worst-case miss ratio".
  Only the paper itself (arXiv 2608.27975), the USENIX page and the authors' Harvard blog post came back;
  the conformal-abstention literature that surfaced is all LLM/vision, none applied to cache
  configuration selection.

### AO2 — An honest-overhead model: distilling to the paper's stated 20-tree budget

> **Hypothesis.** We hypothesize that distilling the released 20-model LightGBM ensemble into the single
> 20-tree, depth-9 GBDT that §4.4.3 claims S4-FIFO uses costs < 1 percentage point of mean miss-ratio
> reduction while shrinking the m2cgen-exported C model by > 100× and cutting inference latency below
> 100 µs, thereby making the paper's own overhead claim ("tens of kilobytes", "< 2 ms") true.

- **Mechanism.** Train the existing ensemble as a teacher; fit one `LGBMClassifier(n_estimators=20,
  max_depth=9)` on the teacher's soft probabilities, weighted by the empirical regret matrix
  `build_empirical_cost_matrix` already computes, so the student is optimised for regret rather than
  log-loss. Export with `export_models_multilang.py`, then measure (i) exported byte size per language,
  (ii) per-call latency with the compiled-C harness, and (iii) end-to-end miss ratio versus the teacher
  on the honest split from AO1. Sweep the tree budget (5/10/20/50/200) to produce an
  accuracy-versus-footprint curve.
- **Code locations.** `analysis/train_xgb_18class.py`, `analysis/train_xgb_18class_lite_logc.py`,
  `analysis/export_models_multilang.py`, `analysis/test_c_consistency.py`.
- **Motivating evidence.** §4.4.3 bounds inference as O(T·D) with T = 20, D = 9 and claims "tens of
  kilobytes" total; `analysis/train_xgb_18class.py:347-358` trains 20 models of 200–580 estimators over
  18 classes (≈ 10⁵ trees), the "lite" variant is still ≈ 4,500 trees
  (`train_xgb_18class_lite_logc.py:360-367`), and `export_models_multilang.py:456-457,472` reports the
  exported code size in **MB** per model and per language. No released script produces a 20-tree model.
- **Feasibility: H.** All four scripts exist and already do the export and the Python↔C consistency test;
  the change is localized; training is minutes of CPU once the CSVs from §4 exist.
- **Research value: M.** It repairs and quantifies a stated deployability claim — genuinely useful for a
  system whose entire pitch is "cheap enough to deploy" — but the direction of the result (small trees are
  nearly as good on 73 tabular features) is what most reviewers would expect.
- **Scoop check: clear.** Queries: "S4-FIFO learning-augmented heuristics cache eviction follow-up 2026";
  "learning to configure cache eviction parameters SIEVE 2Q TinyLFU generality learned configuration
  selector 2026". Nothing distils or re-budgets this model; GBDT distillation is generic ML, not applied
  here.

### AO3 — Actually periodic prediction: re-configuration under workload drift

> **Hypothesis.** We hypothesize that periodic re-prediction over a windowed feature collector, gated by
> hysteresis on the expected-regret improvement, reduces mean miss ratio by > 3 % relative to one-shot
> S4-FIFO on drifting workloads (multi-day Tencent/Twitter traces and cross-source concatenations) without
> increasing the worst-trace regression versus FIFO.

- **Mechanism.** (1) Make the feature collector windowed — the current `bucketed_hit_pos_tracker_t`
  accumulates from t = 0, so a second prediction at t = 0.6 is dominated by the first 20 %; replace with an
  exponentially-decayed or tumbling-window histogram. (2) Drive re-prediction from the already-present
  `prediction-interval` knob, but only commit a switch when
  `risk(current) − risk(candidate) > θ`, so the cache does not oscillate. (3) Build a drift workload
  generator: concatenate traces from different sources and different phases of the same source, plus use
  the natural multi-day structure of the Tencent CBS and Twitter traces. (4) Report mean, P10 and worst
  against one-shot S4-FIFO, S3-FIFO, ARC and LeCaR — ARC/LeCaR are the per-miss adaptive baselines that
  *should* win on drift if periodicity is the wrong granularity.
- **Code locations.** `doc/REPRODUCTION.md` (the `prediction-interval` knob is documented at :210 and
  defaults to one-shot), `analysis/train_xgb_18class.py` (the risk-minimising inference at :488-514 is what
  gets invoked per window), `analysis/create_improvement_report.py`, `Makefile`.
  The C-side edit lands in the submodule at `libCacheSim/libCacheSim/cache/eviction/S4FIFO_features.h`
  (14,009 B — the tracker and collector structs) and `S4FIFO.c` (22,554 B — the phase machine and the
  `prediction-interval` handling), both verified to exist upstream on branch `s4-fifo` @ `b6d292e` but not
  present in this shallow clone.
- **Motivating evidence.** §4.2: "For simplicity, our evaluation makes a single prediction per trace. We
  found that substantial shifts requiring a new prediction are uncommon… We leave the choice of refresh
  policy and interval outside the scope of this work." §5.1: "we restrict ourselves to one prediction per
  trace". Yet the paper's *framing* contribution (Table 1, Fig. 1, §2.4.2) is that it occupies the
  **periodic** cache-level quadrant — periodicity is asserted as the design's defining property and never
  exercised. The claim that drift is rare is also tested on traces that were filtered and cut to a single
  window; on multi-day traces it is exactly the assumption most likely to break.
- **Feasibility: M.** Cross-cutting: it needs C work in the submodule (windowed collector + an inference
  path that does not currently exist, since no model is embedded — see §2.4d), a new drift workload
  generator, and a full re-run of the evaluation. All the compute is CPU-only and within the §4 budget, and
  3–4 students can do it in 10 weeks, but it is not a localized change.
- **Research value: H.** It closes the gap between the paper's taxonomy claim and its evaluation. A null
  result ("one-shot is enough even on multi-day drifting traces") validates a load-bearing assumption the
  paper only asserts; a positive result is a direct improvement in the regime the authors named as future
  work.
- **Scoop check: partial.** Queries: "learned cache eviction policy configuration tuning periodic
  re-prediction workload drift 2026"; "S4-FIFO … follow-up 2026". Closest work is
  *DynamicAdaptiveClimb: Adaptive Cache Replacement with Dynamic Resizing* (arXiv 2511.21235), which
  resizes cache regions adaptively — but per-access and without a pre-trained cache-level configuration
  selector, i.e. it is in the per-miss quadrant the paper argues against. No work re-predicts LAH-style
  configurations periodically.

### AO4 — Shrinking the observation window: closing the v1/v2 gap

> **Hypothesis.** We hypothesize that triggering the prediction as soon as the histogram feature vector
> stabilises (L1 drift between consecutive windows below a threshold) — typically far earlier than 20 % of
> the trace — recovers at least half of the online-versus-retrospective gap in Figure 6 at no loss in
> configuration-selection accuracy.

- **Mechanism.** Collect features at 1 %, 2 %, 5 %, 10 % and 20 % of each trace; train one model per window
  length and measure both top-k accuracy and the end-to-end **v1** miss ratio (default parameters before
  the switch, predicted after). Then replace the fixed window with a stability trigger on the L1 distance
  between successive feature snapshots, and report the induced distribution of trigger points and the
  resulting v1 miss ratio versus the fixed-20 % baseline.
- **Code locations.** `analysis/train_xgb_18class.py`, `analysis/train_xgb_18class_lite_logc.py`,
  `analysis/plot_feature_distribution.py`, `analysis/train_per_ratio.py`, `analysis/README.md`.
- **Motivating evidence.** §5.2: "Across both cache sizes, v2 consistently outperforms v1… the observation
  window accounts for the gap between the two variants" — the paper identifies the cost but never tries to
  reduce it. The authors evidently already collected a shorter-window variant and did not report it:
  `analysis/README.md:81-82` lists both `features_10pct.csv` and `features_20pct.csv`, and every training
  script loads only the 20 % file. The C default is smaller still
  (`feature-collect-reqs=10000` in `S4FIFO.c`'s default parameter string) and `doc/REPRODUCTION.md:154`
  uses 50,000 — three different window definitions across paper, code and docs.
- **Feasibility: M.** Needs feature collection re-run at ~5 window lengths over the trace subset
  (≈ 4× the §4 simulation budget, still only ~1 CPU-day on 30 threads) plus a v1 driver script that the
  repo does not provide; training itself is cheap.
- **Research value: M.** A concrete, measurable improvement to the variant the paper actually deploys
  (v1 is the online one), and it probes how much history the "foundation model" really needs — but the
  direction is unsurprising and the magnitude is bounded by the v1/v2 gap in Fig. 6.
- **Scoop check: clear.** Queries: "S4-FIFO … follow-up 2026"; "learned cache eviction policy
  configuration tuning periodic re-prediction workload drift 2026". Nothing addresses the warmup-window
  length for cache-level configuration prediction.

### AO5 — Generality of LAH: learning to configure a second heuristic

> **Hypothesis.** We hypothesize that applying LAH to a second, structurally different heuristic — 2Q (hot/cold
> queue ratio + ghost size) or SIEVE (hand ratio / admission) — recovers at least half of S4-FIFO's mean
> miss-ratio reduction over its own static default on the same traces, showing that the gain comes from
> learning-to-configure rather than from S3-FIFO's specific queue structure.

- **Mechanism.** Expose the target heuristic's knobs in libCacheSim, define an analogous cache-level
  feature set (queue-position histograms + the same composite ratios), grid-search a discretised
  configuration space, reduce to ~10–18 classes, and reuse the existing regret-matrix training and
  risk-minimising inference verbatim. Compare (a) learned-vs-default for the new heuristic, (b)
  learned-2Q/SIEVE vs learned-S4-FIFO, and (c) whether a model trained on S4-FIFO features transfers.
- **Code locations.** `analysis/train_xgb_18class.py`, `analysis/train_xgb_18class_lite_logc.py`,
  `analysis/create_grid_optimal.py`, `analysis/analyze_class_distribution.py`.
  The new policy would sit alongside `libCacheSim/libCacheSim/cache/eviction/TwoQ.c` / `Sieve.c` in the
  submodule (both verified present upstream in the eviction directory listing at `b6d292e`).
- **Motivating evidence.** §5.5 "Generality across eviction algorithms": the paper lists CacheLib's LRU
  knobs, 2Q's hot/cold ratio, ARC's balance and LeCaR's weights as candidates and then says "Extending LAH
  to these policies requires policy-specific feature engineering… These extensions are beyond the scope of
  this work." LAH is presented as a *framework* (§3, the paper's first-listed contribution) but is
  instantiated exactly once, so its central generality claim is currently unsupported.
- **Feasibility: M.** A new parameterised policy plus a feature collector in C, a fresh grid search, and a
  fresh training run — cross-cutting and the largest of the five, but all CPU-only and reusing the existing
  training/evaluation code unchanged. Realistic for 3–4 students over 10 weeks only if the reproduction in
  §4 lands early.
- **Research value: H.** It is the direct test of the paper's framework-level claim, and a negative result
  (gains do not transfer, i.e. S3-FIFO's three-queue structure is what makes configuration learnable) would
  be at least as interesting as a positive one.
- **Scoop check: clear.** Queries: "learning to configure cache eviction parameters SIEVE 2Q TinyLFU
  generality learned configuration selector 2026"; "S4-FIFO … follow-up 2026". Search returned only the
  paper, its arXiv version and its blog post, plus unrelated learned-eviction work (SL-Cache, Cold-RL,
  MUSTACHE, LearnedCache) that all replace the policy rather than configure it.

---

## 6. Risks and open questions

1. **The pre-trained model is not released.** No model/ensemble/m2cgen file exists anywhere in the
   libCacheSim fork's tree at `b6d292e`, `S4FIFO.h`/`S4FIFO_features.h` contain no inference code, and
   `analysis/.gitignore:2-5` excludes the pickles. `README.md:204` and `BLOG.md:169` both advertise a
   released pre-trained model. **First action on day 1: fetch both submodules and grep for the model.**
   If it truly is absent, every S4-FIFO number must be re-trained from scratch, which is what the effort
   estimate in §4 assumes.
2. **How does `s4fifo` obtain its parameters at run time?** `S4FIFO.c` exposes
   `feature-collect-reqs`, `feature-num-buckets` and `prediction-interval` but I found no inference path.
   It may read a config file, or call a stub. Unresolved by desk review; blocks AO3 until answered.
3. **No intermediate data at all.** `features_*.csv`, `cleaned/`, `aggregated_results.csv`,
   `xgb_*_results/` and `trace.txt` are all gitignored. Every plotting and analysis script fails on a
   fresh clone. The dependency chain is: traces → grid search → `grid_full.csv` → everything else.
4. **The train/test split in the released trainer is hand-curated** (§2.4a). Any reproduction that runs
   `train_xgb_18class.py` unmodified inherits it; any reproduction that removes it is no longer comparing
   like with like against Fig. 6/7. Report both (this is AO1).
5. **Model size contradicts the paper's overhead analysis** (§2.4b). Consequently Figure 8's throughput
   parity claim rests on a model that may be orders of magnitude larger than described — and Figure 8 is
   also the one figure this machine cannot reproduce (CacheLib needs root for `install-system-deps`).
6. **Top-k accuracy uses an undisclosed miss-ratio tolerance** (§2.4c); Figure 10's ~60 % top-1 is not the
   quantity the paper's text defines. Recompute both ways.
7. **~20 % of the corpus is proprietary** (CDN 1, CDN 2, Meta, Tencent Photo; "available upon request").
   Absolute numbers will not match the paper. The public substitute is block/KV-heavy, so results will be
   biased toward block workloads — state this explicitly rather than claiming a failed reproduction.
8. **Disk.** ~257 GB free versus a recommended 500 GB (`doc/REPRODUCTION.md:229`). Trace subsetting is
   mandatory; budget download and decompression time, and keep traces zstd-compressed
   (`OPT_SUPPORT_ZSTD_TRACE` is ON by default).
9. **Learned baselines need extra C libraries.** 3L-Cache, LRB and GL-Cache are behind CMake options that
   are OFF by default and require LightGBM/XGBoost C libs. Without them the "+8 % over 3L-Cache" claim
   cannot be checked at all. Conda-forge provides both, but this is an unvalidated build path.
10. **No artifact badge found.** The USENIX presentation page returned HTTP 403 to automated fetch, so
    badge status could not be confirmed either way; the repo has 2 stars, 0 forks, 0 issues and was last
    pushed 2026-05-12. `BLOG.md:170` claims a "Docker-based artifact evaluation package", and the
    Dockerfile exists, but it builds only the simulator — it ships no traces, no model and no results.
11. **Unpinned Python dependencies**, and the scripts disagree with each other about the pandas API
    (`learning_curve_experiment.py:125` needs pandas ≥ 2.2, `train_xgb_18class.py:253` uses the form
    deprecated in 2.2). Expect to pin manually.
12. **Doc drift.** `doc/GUIDE.md:178,200` reference `scripts/quick_eval.py` and `analysis/evaluate.py`,
    neither of which exists; `doc/REPRODUCTION.md:77` and `:45` contradict the paper on the ghost-ratio
    grid and the trace-length filter. Trust the code over the docs.

---

## 7. Evidence index

**Paper** (`paper.txt`, page-marked; figures read from `pages/page-NN.png`)
- Abstract (p. 2241) — 26 % / 8 % / 0.8 % headline numbers
- Fig. 1 (p. 2241) — quadrant classification, efficiency/robustness summary
- §2.2, Table 1 (p. 2243) — granularity × frequency taxonomy, "S4-FIFO (this work): periodic, cache-level"
- Fig. 2 (p. 2243) — objective-mismatch example
- §2.3–2.4, Fig. 3 (p. 2244) — per-miss instability, delayed reward
- §3, Fig. 4 (p. 2245) — LAH framework, offline pretrain / online control path
- §4.1–4.2, Table 2, Fig. 5 (pp. 2245–2246) — five knobs, defaults, learning ranges, lazy resize, "single prediction per trace", "refresh policy … outside the scope of this work"
- §4.3, Table 3 (p. 2247) — 73 features; §4.3.1 cost matrix and FIFO anchor; §4.3.3 GBDT, 18 classes from 168 via greedy set cover
- §4.4.1–4.4.3 (pp. 2247–2248) — LightGBM + m2cgen export; ghost-histogram bin correction; "20 trees, max depth 9", "< 2 ms", "tens of kilobytes"
- §5.1, Table 4 (p. 2249) — 14 sources, 5,175 traces, 100 K-object filter, random 4,140/1,035 split, 20 % warmup, cache sizes 0.1/1/10 % WSS, "All miss ratio results are from libCacheSim"
- §5.2, Fig. 6a/6b (p. 2250) — efficiency; v1 vs v2; offline S4-FIFO within 0.2 pp
- §5.3, Fig. 7a–7d (p. 2251) — worst-trace and 10th-percentile robustness
- §5.4, Fig. 8 (p. 2251) — CacheBench throughput, 48 threads
- §5.5, Figs. 9–13 (p. 2252) — feature importance; training-data scaling; cross-dataset CDN2 → Twitter; rank distribution; "Generality across eviction algorithms … beyond the scope of this work"
- §5.6, Fig. 14 (p. 2253) — LLM interpretability, 83 % / 86 %

**Repository** (`repo/`)
- `README.md` — :22-29 quick start; :44-56 prerequisites (`sudo apt`); :78-100 CacheLib build (`sudo getdeps.py`); :130-147 `-e` parameter table; :177-194 algorithm list; :204 "Pre-trained model"
- `doc/REPRODUCTION.md` — :11 component→path table; :20-37 smoke test; :41 "available upon request"; :45 1 M-object filter; :72-80 grid table (ghost ∈ {3×,6×}); :101-107 feature dump command; :128-136 training commands; :140-160 evaluation protocol; :192-213 full knob table incl. `prediction-interval`; :225-231 system requirements
- `doc/GUIDE.md` — :44 "Contact for access"; :105-114 knob table; :176-185 non-existent `scripts/quick_eval.py`; :190-202 key-files tree naming `analysis/evaluate.py`
- `BLOG.md` — :66-76 knob table; :88 "20 trees of depth 9"; :151 "tens of kilobytes"; :163-170 "Pre-trained model exported to C/C++…", "Docker-based artifact evaluation package"
- `Dockerfile` — :9-17 apt deps; :28-32 cmake flags incl. `-DUSE_HUGEPAGE=OFF`; :46-61 pip deps
- `Makefile` — :12-13 build; :18-26 `make test` smoke test; :45-46 `submodules`
- `requirements.txt` — unpinned deps
- `.gitmodules` (via `repo_facts.json`) — both author-owned submodule forks
- `analysis/README.md` — :7-22 directory layout incl. gitignored `cleaned/`, `gpu/`; :81-86 `features_10pct.csv` / `features_20pct.csv`; :111 pointer to `S4FIFO_features.h`
- `analysis/.gitignore` — :2-5, :8-12, :21 the excluded model/feature/grid/trace-list artifacts
- `analysis/train_xgb_18class.py` — :15-34 the 18 classes; :167-213 `split_by_trace`; :296-312 `worst_traces_for_train`; :316-325 `showcase_test_traces`; :343-361 20-model ensemble hyper-parameters; :402-486 `build_empirical_cost_matrix`; :494-514 expected-risk argmin; :518-551 miss-ratio lookup from `grid_full.csv`
- `analysis/train_xgb_18class_lite_logc.py` — :306-339 identical curated split; :353-368 "lite" 5×50 ensemble; :140-153 log_C-normalised composite features
- `analysis/export_models_multilang.py` — :22-41 CONFIGS with κ fixed at 0.25 for all 18 classes; :420 loads gitignored `xgb_18class_results_lite/ensemble_models.pkl`; :456-457,:466-472 per-model and total sizes reported in MB
- `analysis/test_c_consistency.py` — :18-28 loads gitignored artifacts; :55-107 compiles and runs the exported C ensemble (the latency/size harness AO2 reuses)
- `analysis/learning_curve_experiment.py` — :98 reads gitignored `tune.csv`; :125 `include_groups=False`; :178-211 top-k with undisclosed miss-ratio tolerance; :234-242 10×200-estimator ensemble
- `analysis/cross_dataset_simple.py` — :45-56 needs gitignored `trace.txt`; :182-186 trains on `tencentBlock` (not CDN2); :127-151 tolerance-based top-1
- `analysis/create_grid_optimal.py` — :24-31 argmin over `grid_full.csv` (no set cover)
- `analysis/evaluate_model.py` — :309 loads gitignored `xgb_config_results/xgboost_config_model.json`; :154-171 an *uncurated* `split_by_trace`
- `analysis/check_tail_performance.py` — :22 reads gitignored `cleaned/tail_stats_ratio_*_vs_fifo.csv` (Fig. 7 inputs)
- `analysis/train_traces.txt` — 5,171 trace names (`akamai_*`, `cf_*`, `tencentBlock.*`, `io_traces.*`, `cluster*`, `wiki_*`, `2016_LUN*`)

**Out-of-band verification** (web, for provenance and the missing-model finding)
- `haochengxia/libCacheSim` branch `s4-fifo` @ `b6d292e` (2026-05-12): eviction directory listing incl. `S4FIFO.c` 22,554 B, `S4FIFO.h` 7,923 B, `S4FIFO_base.c` 9,769 B, `S4FIFO_features.h` 14,009 B, `S4FIFO_verify.c` 19,083 B; `grid_search/{conf.py,conf_1..3.json,yield_tasks.py,apply.sh,trace_lists.txt}`; recursive tree contains no `model`/`ensemble`/`m2cgen` path; root `CMakeLists.txt` requires GLib-2.0 + argp, `USE_HUGEPAGE` default ON, `ENABLE_GLCACHE`/`ENABLE_LRB`/`ENABLE_3L_CACHE` default OFF
- `cacheMon/cache_dataset` — public `oracleGeneral` traces on `s3.amazonaws.com/cache-datasets/`: Tencent CBS 4,030 · Alibaba 1,000 · CloudPhysics 106 · Twitter 54 · MSR 13 · Wikimedia 3 · Meta KV 5
- arXiv 2608.27975 (preprint of this paper); Harvard Systems Group blog post
- `https://www.usenix.org/conference/osdi26/presentation/xia` — HTTP 403 to automated fetch; artifact badges not confirmed
- Scoop-check searches (2026-09-14) returned no follow-up work implementing any of AO1–AO5; closest neighbour is arXiv 2511.21235 (*DynamicAdaptiveClimb*), a per-access adaptive resizing policy
