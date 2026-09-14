# Top-8 papers: can we rebuild and extend them on this machine?

*Prepared 2026-09-14 for the Graduate OS course project (Improvement-paper track).*

These are the 8 highest-ranked papers of the 1,254-paper pre-rank ([`../prerank.md`](../prerank.md)). For each one:
- **the repository was cloned** into [`repos/<name>/`](repos/), along with its simulator or library dependencies where the build needs them;
- its README, artifact docs and every dependency file were read;
- its data and model sources were sized with HTTP HEAD requests and bucket listings;
- the paper's evaluation setup was read, and one result was picked as the reproduction target.

**Desk check only.** Nothing was built, installed, run or downloaded beyond the repositories. Each paper was explored by a separate agent. I then **re-checked the key claims myself** (dependency pins, `sudo` steps, broken paths, data sizes, model gating); those claims are marked *verified* in the sections. One agent error was caught and corrected: the size of Lazy Promotion's throughput archive.

## This machine (the yardstick)

| | |
|---|---|
| Access | **no root/sudo**, no Docker, no KVM, eBPF off, perf counters blocked; user-space installs only (conda, pip, rustup) |
| CPU / RAM | Threadripper PRO 5955WX (Zen 3) 16 cores / 32 threads, **AVX2, no AVX-512**; 125 GiB |
| GPU | 1 × RTX A5000 24 GB (Ampere sm_86), driver 535 → **CUDA ≤ 12.2** |
| Disk | **~253 GB free** |
| Toolchain | Debian 12, glibc 2.36, gcc 12.2 (+ g++-11), cmake 3.25 (4.x via pip), nvcc 11.8, Java 17/21, Python via conda; **no Rust, no GLib headers** |

## How to read the scores

| score | from | scale |
|---|---|---|
| **Pre-rank** fit / feas / build / room | title + scout note only (no repo, no PDF) | 1–5 each, /20 |
| **Repo exploration** build complexity · dependency fit · data fit · hardware fit · repro scripts · extensibility | reading the actual repo, dependency files and data sources against this machine | 1–5 each, **/30** |
| **Hard filters** H1 official open repo · H2 no root · H3 hardware fits · H4 dependencies + data obtainable | same | pass / fail / unclear |
| **Verdict** | same | ✅ DOABLE · 🟡 DOABLE-WITH-WORK · ❌ NOT-DOABLE |
| **Gate** (full audit) | a separate no-shell auditor that read the whole PDF + repo and scored add-on hypotheses by the rubric in [`../pipeline/rubric.md`](../pipeline/rubric.md) | shortlist / maybe / reject; reproduction H/M/L |

## Summary

| # | paper | pre-rank | **repo /30** | build · dep · data · hw · scripts · ext | verdict | min data | setup | gate |
|---|---|---|---|---|---|---|---|---|
| 1 | **Baleen** (FAST'24) — ML admission + prefetching for flash caches | 20 | **26** | 4 · 5 · 5 · 4 · 4 · 4 | ✅ DOABLE | **17 MB** | ~0.5 d (+2 d full Figure 9) | **shortlist**, repro H |
| 6 | **S3-FIFO** (SOSP'23) — 3-queue FIFO eviction | 20 | **24** | 4 · 4 · 3 · 4 · 4 · 5 | ✅ DOABLE | 11.5 GB | ~2 d | **shortlist**, repro H, best add-on H/H |
| 3 | **Lazy Promotion** (VLDB'26) — D-FR / AGE eviction | 20 | **24** | 4 · 4 · 3 · 4 · 4 · 5 | ✅ DOABLE | 14 GB | ~1–1.5 d | **shortlist**, repro H |
| 4 | **SIEVE** (NSDI'24) — visited-bit FIFO eviction | 20 | **22** | 4 · 4 · 3 · 4 · 2 · 5 | ✅ DOABLE | 6 GB | ~1–2 d | **shortlist**, repro M |
| 2 | **Kosmo** (FAST'24) — online miss-ratio curves | 20 | **21** | 4 · 4 · 3 · 4 · 2 · 4 | 🟡 WITH WORK | ~16 GB | ~2–3 d | **shortlist**, repro M |
| 5 | **3L-Cache** (FAST'25) — learned eviction, low overhead | 20 | **21** | **2** · 4 · 4 · 4 · 3 · 4 | 🟡 WITH WORK | 9 GB | ~2–3 d (gate: ~7 d for the Figure 10 overhead target) | **shortlist**, repro M |
| 7 | **PowerInfer** (SOSP'24) — GPU/CPU hot-cold neuron LLM inference | 20 | **21** | 4 · 4 · 3 · 4 · **2** · 4 | 🟡 WITH WORK | 54 GB models | ~2–3 d (gate: 4–6 d + 15–25 GPU-h) | **shortlist**, repro M |
| 8 | **S4-FIFO** (OSDI'26) — learned parameters for S3-FIFO | 20 | **20** | 4 · 4 · 3 · **3** · **2** · 4 | 🟡 WITH WORK | 12.6–35 GB | **~4–6 d** (gate: **~12 d**) | **shortlist**, repro M, best add-on H/H |

- **All 8 pass every hard filter at subset scale; none needs root.** The only root-bound pieces are optional throughput experiments: CacheLib builds for SIEVE, S3-FIFO and S4-FIFO, turbo/SMT control for Lazy Promotion and S3-FIFO, and a full paper-scale Twitter/CDN corpus.
- **The full gate marked all 8 shortlist.** It gave reproduction feasibility **H** to Baleen, S3-FIFO and Lazy Promotion, and **M** to the other five. Three papers have an add-on rated high feasibility / high research value: Baleen, S3-FIFO and S4-FIFO. The gate's effort estimates are consistently higher than the repo exploration's for the harder papers (3L-Cache ~7 d, S4-FIFO ~12 d, PowerInfer 4–6 d).
- **The two independent checks agree on the key problems.** The gate and the repo exploration each found 3L-Cache's broken CMake path and S4-FIFO's hand-curated split on their own.
- **The pre-rank couldn't tell these apart** (all scored 20/20). Reading the repos spreads them from 20 to 26, and the difference is almost entirely **build friction and reproduction scripts**, not feasibility.

## Recommendation

1. **Baleen:** most turnkey. Pure Python, 17 MB of data, notebooks regenerate every figure from the authors' results, and the gate found an **H/H add-on** (PeakBaleen: peak-aware episode scoring, no prior work found).
2. **Lazy Promotion:** cleanest reproduction. It ships per-trace reference results for every trace, so a 14 GB public-subset run can be **diffed row by row**, and new policies appear in the figure pipeline automatically.
3. **S3-FIFO / SIEVE:** the most extensible code (one `.c` file per policy in libCacheSim) and the richest space of eviction add-ons. S3-FIFO ships precomputed per-trace results to diff against; SIEVE needs its Figure 4 aggregation written by hand.

**Treat with care**
- **3L-Cache:** the current commit doesn't configure (bad CMake path, *verified*), and it needs a modified LightGBM 2.2.2 fork that prebuilt packages can't replace.
- **S4-FIFO:** the simulator never actually runs the model (*verified*: the prediction callback has no callers), and the trained model, labels and features are unreleased.
  - **Project angle:** the training script **forces worst-case traces into training and showcase traces into test** (*verified*), contradicting the paper's "randomly split". Re-evaluating the robustness claim under a truly random split is a ready-made "Contemporary paper" (reproduce-and-scrutinize) project.
- **PowerInfer:** the only GPU/LLM candidate. It fits this machine, and the 13B target needs no gated models. But there is **no benchmark harness**, the predictor-training code is unreleased, and this CPU's high memory bandwidth may shrink the headline 3.47× speedup.
- **Kosmo:** Rust nightly with no toolchain pin, and no trace converter. The paper-scale Twitter/SEC data far exceeds disk.

**Shared infrastructure:** 6 of the 8 (S3-FIFO, SIEVE, Lazy Promotion, 3L-Cache, S4-FIFO, and Kosmo via the same MSR traces) use libCacheSim-style simulators and the same public trace bucket. One conda env (`glib zstd pkg-config gperftools`) plus one ~12–15 GB trace subset (MSR + FIU + CloudPhysics + Meta CDN) covers most of them. That makes it cheap to prototype on one and compare against the others.

## Add-on ideas from the full gate (all 8 audited — all **shortlist**)

F = feasibility, RV = research value (rubric in `../pipeline/rubric.md`); scoop = whether follow-up work already exists.

| paper | add-on hypothesis | F / RV | scoop |
|---|---|---|---|
| Baleen | **PeakBaleen**: score episodes by their contribution to peak 10-min disk-head-time windows, and modulate the admission threshold / prefetch gate with load | **H / H** | clear |
| Baleen | Segment-level (vs block-level) admission and prefetching | M / H | clear |
| Baleen | "Is the ML necessary?": DT-objective vs model-class ablation | H / M | clear |
| Baleen | Learned early eviction (episode-end TTL); drift + online retraining | H / M | partial |
| Kosmo | Incremental stack reconstruction to cut CPU per access ≥ 2× | M / H | partial |
| Kosmo | Violation-aware pruning for FIFO/2Q MRC accuracy | M / H | clear |
| Kosmo | ARC eviction map: does the abstraction cover self-tuning policies? | M / H | clear |
| Kosmo | Sub-linear cost of multi-policy MRC generation; adaptive granularity | H / M | clear / partial |
| Lazy Promotion | Trace-driven concurrency: does real-trace throughput change the ranking? (the missing AGE throughput) | M / H | partial |
| Lazy Promotion | Learned Belady-early-eviction classifier replacing AGE's age heuristic | M / H | partial |
| Lazy Promotion | Object-size-aware lazy promotion; lazy promotion on S3-FIFO/SIEVE; self-tuning under a promotion budget | H / M | clear / partial |
| SIEVE | Closing the SIEVE–Belady gap with O(1) per-object state | M / H | partial |
| SIEVE | SIEVE-Ghost (scan resistance); adaptive hand floor for small caches | H / M | partial / clear |
| SIEVE | Reproducing the scalability claim without CacheLib | M / M | partial |
| 3L-Cache | Skew-aware sampling guard: detect when sampling precision drops and fall back to a wider candidate pool to improve the worst case | M / H | partial |
| 3L-Cache | Adaptive eviction-ratio controller instead of the fixed 1/2 | H / M | partial |
| 3L-Cache | Warm-start / incremental GBM training plus reuse of still-valid predictions | H / M | partial |
| 3L-Cache | Metadata-charged evaluation: does the byte-miss-ratio advantage survive when per-object learning metadata counts against the cache budget? | H / M | clear |

| S3-FIFO | **S3FIFO-mini**: choose the small-queue ratio online from a bank of spatially-sampled 1/100-scale shadow simulations | **H / H** | partial (overlaps with S4-FIFO's learned parameters and S3-FIFO-d; must be positioned against both) |
| S3-FIFO | Write-amplification-aware main queue for DRAM+flash (in-place frequency tracking instead of physical reinsertion) | M / H | clear |
| S3-FIFO | Size-aware promotion (benefit-per-byte instead of freq ≥ 2) | H / M | partial |
| S3-FIFO | Metadata charged against capacity: fair re-evaluation of the baselines | H / M | clear |

| PowerInfer | Co-allocate VRAM between hot neurons and the KV cache as a function of context length (instead of all VRAM to neurons) | M / H | partial |
| PowerInfer | Activation-affinity request batching to preserve union sparsity at batch > 1 | M / H | partial |
| PowerInfer | Calibrated placement solver: measured communication constraint + impact-weighted (not frequency) objective | H / M | clear |
| PowerInfer | Sparsity-preserving chunked prefill instead of the dense-GPU fallback | M / M | partial |

| S4-FIFO | **Leakage-free split + calibrated abstention**: replace the hand-curated train/test split with a grouped / leave-one-source-out split, and fall back to S3-FIFO defaults when the model is unsure | **H / H** | clear |
| S4-FIFO | Periodic re-prediction under workload drift (windowed features + hysteresis) | M / H | partial |
| S4-FIFO | Generality: apply learned-parameter tuning to a different heuristic (2Q or SIEVE) | M / H | clear |
| S4-FIFO | Honest-overhead model: distil the released 20-model ensemble into the single 20-tree, depth-9 model the paper claims | H / M | clear |
| S4-FIFO | Shrink the warmup window to close the v1/v2 gap | M / M | clear |

The S4-FIFO gate independently found the hand-curated split as well (27 worst-case traces forced into training, 6 showcase traces forced into test, `analysis/train_xgb_18class.py:296-312`), and turned it into its top add-on.
The PowerInfer gate chose the same reproduction target as the repo exploration (Table 4, 13B FP16, 3.47×).
The 3L-Cache gate independently found the same broken `3LCache+` CMake path as the repo exploration (`../papers/fast25-3l-cache-…/audit/report.md` §2).

Full audit reports: `../papers/<id>/audit/report.md`. Ranking across the top 30: [`../ranking.md`](../ranking.md), when the gate finishes.

---

# Per-paper details

### 1. Baleen: ML Admission and Prefetching for Flash Caches (FAST'24)

- **Repo:** https://github.com/wonglkd/Baleen-FAST24 — artifact wrapper; last commit 2024-02-29 (`4e3a920`); no LICENSE file.
  - **Simulator:** https://github.com/wonglkd/BCacheSim, a submodule pinned at `ddeb2d8` (2024-01-16), Apache-2.0.
  - **Size:** wrapper 11 MB of notebooks; simulator 1.3 MB, about 13.6k lines of Python.
  - **Artifact badges:** USENIX Available, Functional and Reproduced.
- **What it is:** an ML admission and prefetching policy for flash caches in front of HDD storage (Meta Tectonic/CacheLib). LightGBM models imitate an episode-based optimal policy that minimizes **peak disk-head time (DT)** rather than maximizing hit rate. The artifact is the Python simulator plus the training code, trace download scripts, plotting notebooks and the authors' intermediate results. The CacheLib testbed is not released.
- **Paper eval setup:**
  - **Traces:** 7 Meta Tectonic regions (2019/2021/2023), 3–7 days each; day 1 trains the models, the rest is test.
  - **Cache:** 400 GB-equivalent flash at 3 drive-writes per day (DWPD).
  - **Sampling:** 0.1–5% sampled traces, 10 samples per trace.
  - **Hardware:** a 24-node CPU cluster (16-core Xeon, 64 GB, one node per run). The full paper took 624 machine-days, and each ML simulation takes at least 30 min.
- **Reproduction target:** **Figure 9, peak backend load per trace.** It rolls up into the headline claim that Baleen cuts peak DT by **12.0%** versus RejectX (range 4.8–29.2%). The authors' output: Baleen 28.11%, RejectX 31.95%, CoinFlip 34.63%.
  - **Stage A:** re-plot from `results_release.csv.gz`.
  - **Stage B:** re-simulate sample 0 of all 7 traces at 0.1%.
  - **Stage C:** paper scale.
  - **Smoke test:** `notebooks/example/example.ipynb`, which expects 16.1% peak saving on Region1.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| Python 3.11 with pins numpy 1.24.2, pandas 1.5.3, scipy 1.10.1, sklearn 1.2.2, lightgbm 3.3.5 | `BCacheSim/install/requirements.txt:1-19` | user install | The pins have no py3.12 wheels, so use a new env: `conda create -n baleen -c conda-forge python=3.11`, then `pip install -r BCacheSim/install/requirements.txt` |
| spookyhash, compress_json, compress_pickle, pqdict, jsonargparse, commentjson, retry, redis (client only) | `requirements.txt` | user install | pip. The recommended conda YAML is **missing 4 of these**, so pip on top of it; pin `jsonargparse==4.20.0` |
| libgomp for LightGBM | wheel | ✅ available | `/usr/lib/x86_64-linux-gnu/libgomp.so.1` |
| Jupyter (plots) | `requirements.txt:19` | user install | pip `jupyterlab`, or headless `jupyter nbconvert --execute` |
| PyPy 3.8 env (optional speed-up) | `env_cachelib-pypy-3.8.yaml` | optional | conda |
| brooce + redis job queue | README | not needed | Use GNU `parallel` / `xargs -P` |
| `sudo apt install`, systemd | `chameleon/2-start-dedicated-server.ipynb` only | not applicable | Chameleon-cloud notebook only; no `.sh`/`.py` uses sudo (verified) |
| Hard-coded paths in bulk reproduce scripts (`../data/.../processed/`, `../tmp/2023xxxx_*`) | `notebooks/reproduce/reproduce_commands.sh` | ⚠️ needs editing | Rewrite paths to the download layout and to the train-output dirs |
| Region3 5% samples | `reproduce_commands_all.sh` | ⚠️ needs sampling | Download the full Region3 trace and run `scripts/common/sample.py` (hard-codes `~/fb/ws`) |

**Data** (Apache-2.0, public, not gated; sizes verified by HTTP HEAD)

| dataset | size | needed for |
|---|---|---|
| `storage_0.1.tar.gz` (0.1%, sample 0, all 7 regions) | **17 MB** (76 MB unpacked) | smoke test, stages A/B |
| `results_release.csv.gz` (authors' results) | 71 MB | stage A, plus the converged parameters the reproduce commands need |
| `storage_0.1_10.tar.gz` / `storage_10.tar.gz` | 163 MB / 1.72 GB | stage C |
| `storage_all_Region3.tar.gz` | 640 MB | stage C (5% sampling) |
| all full traces | ~30 GB compressed / 150 GB unpacked | **not needed** |

**Hard filters** — H1 ✅ official artifact in the paper's Artifact Appendix, with AE badges · H2 ✅ conda/pip only; sudo appears only in the cloud-VM notebook · H3 ✅ CPU-only, single-process Python simulator · H4 ✅ every dependency has py3.11 wheels; data is 17 MB–4 GB against 253 GB free.

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | Pure Python with nothing to compile. −1 because the conda YAML misses 4 imports and `getting-started.sh:11` has a stray `cd` |
| dependency fit | 5 | All user-space on py3.11; no CUDA, system libraries or root |
| data fit | 5 | 17 MB for the smoke test and sample-0 runs; ~3–4 GB at paper scale |
| hardware fit | 4 | CPU single-core jobs parallelize across 32 threads; paper-scale Figure 9 is days of wall time; all figures (624 machine-days) are out of reach |
| repro scripts | 4 | Notebooks regenerate every figure from the released CSV; the bulk reproduce scripts need path rewrites |
| extensibility | 4 | Clean `AP` / prefetcher / eviction / cost-model seams; −1 because `sim_cache.py` is 1,583 lines driven by CLI flags |
| **total** | **26 / 30** | |

**Verdict: ✅ DOABLE** · confidence high · setup ≈0.5 person-day (env, smoke test, stage A), +1.5–2 days for stage B, +1–2 days for stage C · compute: smoke test ≈35 min on one core; stage B ≈40–80 core-hours (<1 day at 16–24 parallel jobs); stage C several hundred to ~1,500 core-hours; no GPU needed.

**Key risks**
- **Bulk reproduce scripts point at paths that don't match the download layout.** A missing model file fails softly ("Failed to load … continues") and can silently produce wrong numbers.
- **The "Baleen" bar is the best of several prefetch variants per region**, so reproducing it means running every variant.
- **Converged eviction-age and threshold parameters come from the authors' CSV.** Converging them from scratch is a costly simulation loop.
- **Absolute DT differs from the paper by design** (the public release uses different hardware constants), so compare relative savings.
- **Unpinned pip packages may have drifted**, and memory per job on 1%/5% traces isn't documented.

**Where an add-on plugs in**
- **Admission policy:** subclass `AP` in `BCacheSim/cachesim/admission_policies.py` and add it to `construct()` (line 916, verified); select with `--ap`.
- **Prefetching:** `Prefetcher` and `LearnedRangePrefetcherModel` in `cachesim/prefetchers.py`.
- **Eviction:** `EvictionImpl` subclasses in `cachesim/eviction_policies.py`.
- **Training labels, OPT and objective:** `Policy*` classes in `episodic_analysis/policies.py`, `episodes.py`, `train_ap.py`.
- **Cost model:** `service_time()` in `episodic_analysis/constants_public.py:3`.

**Build route (not executed)**
1. `git submodule update --init` (or symlink the already-cloned `BCacheSim` at `ddeb2d8`)
2. `conda create -y -n baleen -c conda-forge python=3.11 && conda activate baleen`
3. `pip install -r BCacheSim/install/requirements.txt "jsonargparse==4.20.0"`
4. `cd data && bash get-tectonic.sh` (≈90 MB)
5. Stage A: `jupyter nbconvert --to notebook --execute notebooks/paper-figs/fig-09-202309.ipynb`, then compare 28.11 vs 31.95
6. Smoke test: `./BCacheSim/run_py.sh py -B -m BCacheSim.cachesim.simulate_ap --config runs/example/rejectx/config.json`, then train and simulate Baleen and check the ~16.1% saving
7. Stage B: rewrite the paths in `reproduce_commands.sh`, then run the train+sim pairs with `parallel -j 24`

---

### 6. FIFO Queues are All You Need for Cache Eviction — S3-FIFO (SOSP'23)

- **Repo:** https://github.com/Thesys-lab/sosp23-s3fifo — last commit 2024-06-12 (`6bc49d9`); 1.0 GB checked out, of which `result/` is 760 MB.
  - **License:** Apache-2.0 per the README; the bundled libCacheSim is GPL-3.0.
  - **Throughput prototype:** a separate repo, `Thesys-lab/cachelib-sosp23`.
- **What it is:** eviction with three FIFO queues: a small queue S (10% of the cache), a main queue M, and a ghost queue G. Quick demotion through S keeps one-hit wonders out of M. The artifact is a libCacheSim snapshot with `cache/eviction/S3FIFO.c` and about 20 baselines, plotting scripts, **precomputed per-trace results for all 14 datasets (verified)**, and a Redis-based multi-node job runner.
- **Paper eval setup:**
  - **Simulation:** 6,594 traces from 14 datasets, of which 3 are proprietary (CDN1, CDN2, SocialNetwork1): 856 B requests, cache sizes of 10% and 0.1%, reported as miss-ratio reduction versus FIFO.
  - **Compute:** about 1 M core-hours on CloudLab.
  - **Figure 8 throughput:** CacheLib on Intel nodes with turbo off, 1–16 threads.
- **Reproduction target:** **Figures 6a/7a (large cache, 10%)**, recomputed on the public, unsampled block datasets MSR (14 traces), FIU (10) and CloudPhysics (106), 130 traces in total. The claim: S3-FIFO has the largest miss-ratio reduction versus FIFO across percentiles and the lowest mean miss ratio per dataset. **Our outputs can be diffed per trace against the shipped `result/cachesim/{MSR,FIU,Cloudphysics}/*.txt`.** Stretch goal: Table 2 (small-queue size sweep on `msr_hm_0`).

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| cmake ≥ 3.2; C11/C++17 | `libCacheSim/CMakeLists.txt:1,121` | ✅ cmake 3.25, gcc 12.2 | as-is (gcc 12 untested, low risk) |
| glib-2.0 dev headers (required) | `CMakeLists.txt:140` | ❌ not on system (verified) | `conda install -c conda-forge glib pkg-config` |
| zstd (fatal if missing) | `CMakeLists.txt:150-156` | only in miniconda base | conda-forge `zstd` in the env |
| tcmalloc | `CMakeLists.txt:167-175` | missing, optional | conda `gperftools` or skip |
| xgboost / LightGBM | `install_dependency.sh` (`sudo make install`) | not needed (GLCache/LRB are off) | skip |
| One-line dependency installer | `README.md:28` → `install_dependency.sh` | ❌ on Debian it falls into the `sudo yum` branch | use the conda route instead |
| artifact-evaluation `apt` line (glib, boost, zstd) | `doc/AE.md:8` | needs sudo; boost is unused | conda glib + zstd |
| numpy + matplotlib | `requirements.txt` | trivial | pip/conda |
| Plot script requires all 14 dataset dirs | `scripts/libCacheSim/plot_miss_ratio.py:48-75` | ⚠️ small edit | edit its `datasets` list |
| Exact flags for all 14 algorithms in Figure 6 | `AE.md:200` lists only 8 | ⚠️ undocumented | reconstruct from `cache_init.h`, `cli_parser.c` |
| distComp multi-node runner (Redis, parallel-ssh) | `distributedComputation/` | not needed | loop traces locally; `cachesim` already uses all cores |
| Figure 8: CacheLib with folly/fbthrift and ~30 apt packages; turbo/MSR control | `cachelib-sosp23/contrib/*`, `mybench/turboboost.sh` | ❌ brittle on Debian 12 without apt; turbo toggle needs root | skip; at best qualitative |

**Data** (CMU PDL public FTP, `.zst`, read directly)

| dataset | size | subset needed |
|---|---|---|
| MSR (14 files, verified) | 1.6 GB | ✅ target |
| FIU (10) | 1.3 GB | ✅ target |
| CloudPhysics (106) | 8.6 GB | ✅ target |
| Meta CDN / wiki_2019t | 2.2 GB / 1.9 GB | optional |
| Twitter (54) | 1.6 TB full; 141 GB sample10; 14 GB sample100 | skip. **The artifact docs' Twitter URL now returns 404 (verified)**; files moved to `twitter/sample10/` |
| Alibaba / Tencent block, Meta KV, TencentPhoto, SYSTOR | 35–230 GB each | skip |
| CDN1, CDN2, SocialNetwork1 | proprietary | ❌ precomputed results only |
| Precomputed results | 760 MB, in repo | ground truth for the diff |

Target total ≈ **11.5 GB**; the full corpus is ≈ 2.5 TB.

**Hard filters** — H1 ✅ official repo named in the paper · H2 ✅ simulator (sudo only in the dependency script and the throughput tooling); ❌ exact Figure 8 conditions · H3 ✅ single-threaded C simulations; the 130-trace target fits in a day (paper scale is a budget limit, not a hardware mismatch) · H4 ✅ for the 11.5 GB subset; the full corpus is ~2.5 TB and 3 datasets are proprietary.

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | Simulator is `cmake .. && make -j` with 3 small libraries; only the dependency script is broken off Ubuntu; CacheLib is heavy |
| dependency fit | 4 | glib, zstd and gperftools from conda-forge; the Figure 8 folly stack is the weak spot |
| data fit | 3 | Block datasets are small (11.5 GB target), but the full corpus is 2.5 TB and 3 datasets are proprietary |
| hardware fit | 4 | Single-core sims fit easily; paper-scale sweeps and Intel/turbo-off throughput can't be matched |
| repro scripts | 4 | `AE.md` gives per-figure commands, plot scripts and precomputed results; missing are the full Figure 6 command line, a subset-friendly plot script, and one stale URL |
| extensibility | 5 | Pluggable per-algorithm interface with a written recipe (`libCacheSim/doc/advanced_lib_extend.md`), separate admission modules, and `-e key=value` parameter parsing |
| **total** | **24 / 30** | |

**Verdict: ✅ DOABLE (simulator); Figure 8 CacheLib throughput is DOABLE-WITH-WORK and not recommended** · confidence high · setup ≈2 person-days (0.5 build, 1 reconstructing flags, names and subset plots, 0.5 data) · compute: MSR+FIU+CloudPhysics ≈ 3 B requests × 14 algorithms × 8 sizes ≈ 50–150 core-hours ≈ 2–6 h on 32 threads, 12 GB disk.

**Key risks**
- **Undocumented algorithm flags.** Figure 6 needs 14 algorithms (window-size variants of W-TinyLFU, 4-segment SLRU, B-LRU, FIFO-Merge), and a wrong flag gives mismatched numbers.
- **Algorithm output names may differ** from those in the shipped results, and the loader silently skips traces with missing algorithms, which could quietly shrink the sample.
- **130 traces give different percentile shapes than 6,594**, even when the per-trace numbers match.
- **Conda glib/zstd may conflict with system libraries**, so set an rpath.
- **Twitter can't be matched per trace** without the full 1.6 TB traces.
- **Shared machine:** the largest CloudPhysics runs may need fewer threads.

**Where an add-on plugs in**
- **S3-FIFO variant:** `libCacheSim/cache/eviction/S3FIFO.c`. Key functions: `S3FIFO_evict_fifo()` (promotion test `freq >= move_to_main_threshold`), `S3FIFO_evict_main()` (reinsertion), `S3FIFO_find()` / `S3FIFO_insert()` (ghost hit → admit to M), and `S3FIFO_parse_params()` (`-e fifo-size-ratio=…,ghost-size-ratio=…,move-to-main-threshold=…`).
- **Registration:** `cache/eviction/CMakeLists.txt`, `include/libCacheSim/evictionAlgo.h`, `bin/cachesim/cache_init.h`.
- **Per-object metadata:** the union in `include/libCacheSim/cacheObj.h` (next to `S3FIFO_obj_metadata_t`).
- **Admission filters:** `cache/admission/{bloomfilter,prob,size}.c`, run with `cachesim --admission`.
- **Instrumentation:** `TRACK_EVICTION_V_AGE` / `TRACK_DEMOTION` in `include/config.h`. The flash-tier simulator is in `bin/SOSP23/flash`.

**Build route (not executed)**
1. `conda create -y -n s3fifo -c conda-forge python=3.11 glib zstd gperftools pkg-config numpy matplotlib && conda activate s3fifo`
2. `cd repo/libCacheSim && mkdir -p _build && cd _build && PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig cmake .. -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DCMAKE_BUILD_RPATH=$CONDA_PREFIX/lib && make -j32`
3. Smoke test: `./bin/cachesim ../data/trace.oracleGeneral.bin oracleGeneral fifo,lru,s3fifo 0.1 --ignore-obj-size 1`
4. `wget -r -np -nd -A '*.zst'` MSR, FIU and CloudPhysics from `ftp.pdl.cmu.edu/pub/datasets/twemcacheWorkload/cacheDatasets/` (~11.5 GB)
5. Sanity check: run `cachesim` on `msr_hm_0` and diff against `result/cachesim/MSR/hm_0.IQI.bin.txt`
6. Run all 14 algorithms × 8 sizes per trace; normalize names; restrict `plot_miss_ratio.py` to `["FIU","MSR","Cloudphysics"]`; compare against the same script on the shipped results for the same 130 traces

---

### 3. Demystifying and Improving Lazy Promotion in Cache Eviction (VLDB'26)

- **Repo:** https://github.com/cacheMon/Lazy-Promotions — last commit 2025-12-08 (`7e50398`), 231 MB cloned.
  - **License:** no top-level LICENSE; the vendored simulator is GPL-3.0.
  - **Official:** the paper's "PVLDB Artifact Availability" section names this repo.
- **What it is:** a libCacheSim fork that adds lazy-promotion eviction policies (Prob-LRU, Batch-LRU, Delay-LRU, FIFO-reinsertion/CLOCK, Random-LRU, lazy ARC/2Q, and offline oracles) plus the paper's two new algorithms **D-FR** (`DelayFR.c`, 330 lines) and **AGE** (`AGE.c`, 382 lines). It also includes a separate concurrent simulator for throughput tests and Python scripts that turn per-trace outputs into every paper figure.
- **Paper eval setup:**
  - **Miss ratio and promotions:** 6,357 production traces (346 B requests; MSR, FIU, CloudPhysics, Tencent, Alibaba, Twitter, Wiki, Meta, plus 2 private CDNs), replayed in libCacheSim on CloudLab. Cache size is 1% of working-set size, results relative to LRU.
  - **Throughput:** a Zipf trace at 16 threads on a 36-core Xeon with SMT and turbo off.
- **Reproduction target:** **Figure 11a/b/c.** The claim: D-FR (delay ratio 0.05) and AGE (factor 0.5) cut promotions relative to FR and LRU without hurting miss ratio. D-FR removes about 60% of FR's promotions on the median trace, and promotion efficiency is about 48% versus about 24% for FR.
  - **Cost:** 8 `cachesim` configs per trace.
  - **Determinism:** the metrics are hardware-independent.
  - **Checkable:** the repo ships **per-trace results for all traces** (`scripts/data/lazy_promotions_data.tar.gz`, 18.8 MB, 159k files, verified), so a public-subset run can be diffed row by row.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| cmake ≥ 3.12; C11/C++17 | `simulator/CMakeLists.txt:1,12-17` | ✅ cmake 3.25, gcc 12.2 | as-is (the README's extra flags are for gcc ≥ 13) |
| glib-2.0 dev (pkg-config) | `CMakeLists.txt:143` | ❌ runtime `.so` only | `conda install -c conda-forge glib pkg-config` |
| zstd dev (required) | `CMakeLists.txt:152-163` | ❌ runtime only | conda-forge `zstd` |
| argp | `CMakeLists.txt:148` | ✅ glibc | — |
| tcmalloc | `FindTcmalloc.cmake` (hard-coded system paths) | missing, optional | conda `gperftools` + `-DHT_DEPENDENCY_LIB_DIR`, or skip |
| `install_dependency.sh` (sudo apt, `sudo make install`) | `simulator/scripts/install_dependency.sh` | ❌ | don't run; use conda |
| Dockerfile | `simulator/dockerfile` | not applicable | leftover upstream file |
| libCacheSim | vendored (diverged fork, no pinned base; ~mid-2024 upstream) | n/a | nothing to fetch; **upstream cannot be substituted** |
| Python pandas 2.3.1, numpy 2.3.2, seaborn, matplotlib | `scripts/requirements.txt` | user install | py3.12 env + pip |
| Undeclared Python deps: pyarrow, scipy, `textual_pandas` | `process_data.py:2` (verified) | missing | `pip install pyarrow scipy textual-pandas`, or drop the unused import |
| `process_data.py:101` always reads `scalability.feather` | verified | ⚠️ crashes without it | run `parse_scalability.py` on the shipped `lazy_throughput.tar.gz` first (19 KB; the explorer's 64.8 MB figure was wrong) |
| distComp + Redis orchestration | README | not needed | `xargs -P 28` over the generated task commands |
| Hard-coded `/ltdata`, `/mnt/nfs`, `~/Lazy-Promotions` | `scripts/generate_task.sh:4-9` | ⚠️ | edit variables |
| "≥ 256 GB RAM for larger traces" | README | 125 GiB | only matters for the biggest Twitter/Meta KV traces; not the target |
| Throughput runs: `sudo wrmsr` turbo off, SMT off | `scripts/disable_turbo.sh` | ❌ no root, AMD CPU | Figures 1b/2b–5b/6a are only approximate; not the target |

**Data** (CMU PDL public FTP, zstd oracleGeneral)

| dataset | size | subset needed |
|---|---|---|
| MSR (14) + FIU (9) + CloudPhysics (106) + MetaCDN (3) + MetaStorage (5) | **≈ 14 GB**, ~3.3 B requests | ✅ minimum for Figure 11 (137 traces) |
| Tencent CBS (4,048) | ≈ 154 GB | optional second tier |
| Alibaba block (609) | ≈ 94 GB | optional; not together with Tencent (248 GB is too tight) |
| Tencent Photo / Wiki / Meta KV | 67 / 50 / 61 GB | optional |
| Twitter (51) | ≈ 1.5 TB | skip |
| CDN 1 / CDN 2 (1,506 traces, ~24% of the paper) | private | ❌ figures only via the shipped results |
| Shipped per-trace results | 18.8 MB (verified) | reference for the diff, and regenerates every miss-ratio figure without simulating |

**Hard filters** — H1 ✅ named in the paper's artifact section · H2 ✅ cmake + conda glib/zstd; sudo only in the replaceable installer and the throughput scripts · H3 ✅ single-threaded CPU simulations; throughput not faithfully reproducible · H4 ✅ at subset scale (14 GB + shipped per-trace references); ❌ at full scale (private CDNs, 1.5 TB Twitter).

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | Documented plain `cmake .. && make`; only friction is pointing CMake at conda glib/zstd |
| dependency fit | 4 | All on conda-forge; minus for the sudo installer, tcmalloc's hard-coded paths and 3 undeclared Python deps |
| data fit | 3 | 14 GB public subset plus shipped references, but 1,506 traces are private and Twitter is 1.5 TB |
| hardware fit | 4 | Deterministic, hardware-independent metrics; throughput needs a root-tuned Xeon |
| repro scripts | 4 | `generate_task.sh` (exact sweeps) → `parse_data.py` → `process_data.py` → `generate_figures.py figure11a` (verified); minus for distComp/Redis, hard-coded paths and the unconditional feather read |
| extensibility | 5 | One file per policy (DelayFR/AGE as templates), registered in 3 places; the shared `n_promotion` counter plus a parser dict make new policies appear in the figures automatically |
| **total** | **24 / 30** | |

**Verdict: ✅ DOABLE** · confidence high for Figure 11 (miss ratio / promotions), medium for throughput · setup ≈1–1.5 person-days · compute: 137 traces × 8 configs ≈ 26 B simulated requests ≈ 2–4 CPU-hours (< 30 min wall at 28 workers), 14 GB disk.

**Key risks**
- **Subset versus paper distribution:** without the private CDNs and Twitter, Figure 11 medians will differ. Diff against the shipped rows for the same traces (exact match expected).
- **Prob-LRU uses unseeded `rand()`** (`lpLRU_prob.c:154`), so results are reproducible only while the RNG path stays the same.
- **Parser coupling:** a new policy must print a name that `parse_data.py`'s regex and dict accept, or its rows are **silently dropped**. Traces with fewer than 1 M requests are also filtered out.
- **The build may silently pick up system runtime libraries** instead of conda's, so set an rpath.
- **Diverged vendored fork:** upstream fixes won't carry over; stale `priv/` and `customized/` code may break on stricter compilers.

**Where an add-on plugs in**
- **New policy:** `simulator/libCacheSim/cache/eviction/<X>.c`, templated on `DelayFR.c` / `AGE.c`. Increment `cache->n_promotion` wherever a promotion happens (`include/libCacheSim/cache.h:104`).
- **Registration:** `cache/eviction/CMakeLists.txt`, `include/libCacheSim/evictionAlgo.h` (see `DelayFR_params_t` :65), `include/libCacheSim/cacheObj.h` (`DelayFR_obj_metadata_t` :47), `bin/cachesim/cache_init.h`.
- **Evaluation pipeline:** a sweep loop in `scripts/generate_task.sh`, a name + parameter parser in `scripts/parse_data.py`, and a `figureXX` in `scripts/generate_figures.py` modeled on `figure11a` (:573).
- **Throughput version:** port the policy into the diverged `simulator-concurrent/`.

**Build route (not executed)**
1. `conda create -n lazyp -c conda-forge python=3.12 glib pkg-config zstd gperftools -y && conda activate lazyp`
2. `cd repo/simulator && mkdir -p _build && cd _build && PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig cmake -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DCMAKE_BUILD_RPATH=$CONDA_PREFIX/lib .. && make -j32 cachesim`
3. Smoke test: `./bin/cachesim ../data/cloudPhysicsIO.oracleGeneral.bin oracleGeneral delayfr -e delay-ratio=0.05 0.01 --ignore-obj-size 1`
4. `wget -r -np` MSR, FIU, CloudPhysics, MetaCDN and MetaStorage (~14 GB); symlink `cphy/` → `cloudphysics/` for `datasets.txt`
5. Edit `generate_task.sh:4-9`, keep only the 8 Figure 11 configs, and run them with `xargs -P 28`
6. `pip install -r scripts/requirements.txt pyarrow scipy textual-pandas`
7. Reference figure: untar both shipped archives → `parse_scalability.py` → `parse_data.py ref` → `process_data.py` → `generate_figures.py figure11a figure11b figure11c`
8. Own figure: `parse_data.py ~/lp_results` → same steps; diff miss-ratio and promotion columns against the reference rows for the 137 traces

---

### 4. SIEVE is Simpler than LRU: an Efficient Turn-Key Eviction Algorithm for Web Caches (NSDI'24)

- **Repo:** https://github.com/cacheMon/NSDI24-SIEVE — last commit 2024-08-01 (`0861f82`), 204 MB, C/C++/Python.
  - **License:** Apache-2.0 at the top level; the bundled libCacheSim copy is GPL-3.0.
  - **Official:** the paper points to this repo.
- **What it is:** a FIFO queue with a "visited" bit and a moving hand that either clears the bit or evicts. It is simpler than LRU yet has a lower miss ratio. The repo contains a libCacheSim snapshot with SIEVE (`cache/eviction/Sieve.c`, 286 lines, verified) and all the baselines, plus links to 5 production libraries patched with SIEVE: groupcache, mnemonist, lru-rs, lru-dict and CacheLib.
- **Paper eval setup:**
  - **Traces:** 1,559 traces from 7 datasets. CDN1 (1,273 traces) and CDN2 (219) are **proprietary**. The public ones are Twitter KV, Meta KV, Meta CDN, Wiki CDN and Tencent Photo.
  - **Miss ratio:** libCacheSim on CloudLab nodes; cache sizes of 0.1% and 10% of unique objects; reported as miss-ratio reduction versus FIFO.
  - **Throughput:** a CacheLib prototype on a 2-socket Xeon at 1–16 threads, with turbo off and threads pinned to one NUMA node.
- **Reproduction target:** **Figure 4(a)/(b), miss-ratio reduction versus FIFO on the public Meta KV, Meta CDN, Wiki and Tencent datasets.** The claim: at the large cache size (10%), SIEVE beats all 10 other algorithms on all four datasets. All 11 algorithms exist in the snapshot. Figures 3 and 5 depend on the proprietary CDNs, and Figure 6 (throughput) needs the full CacheLib/folly build.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| cmake ≥ 3.12, C/C++17 | `libCacheSim/CMakeLists.txt:1,12` | ✅ cmake 3.25.1, gcc 12.2 | as-is |
| GLib 2 dev headers, required | `CMakeLists.txt:141` | ❌ not on system (no `/usr/include/glib-2.0`, no `.pc`; verified) | `conda install -c conda-forge glib pkg-config` (glib 2.88 available, verified) |
| zstd (on by default; reads `.zst` traces) | `CMakeLists.txt:150` | headers only in conda | conda-forge `zstd` |
| argp | `CMakeLists.txt:146` | ✅ in glibc | as-is |
| tcmalloc (optional, speed only) | `FindTcmalloc.cmake` | missing | conda `gperftools`, or skip |
| `install_dependency.sh` | 6 × `sudo` (verified) | ❌ unusable as written | **don't run it**; the conda route above replaces it |
| README build path | `README.md:22` (wrong dir) | doc bug | build in `libCacheSim/_build` |
| numpy/matplotlib for plots | `requirements.txt` | user install | conda |
| Hard-coded plot paths (`/disk/data`, `/disk/cphy/result/`) | `scripts/plot_mrc_size.py:182` | ⚠️ | edit or write own driver |
| Figure 6: CacheLib fork (folly/fbthrift pinned) with ~20 apt `-dev` packages; turbo-boost toggle | `cachelib-sosp23/contrib/*`, `mybench/turboboost.sh` | ❌ heavy / needs root | skip Figure 6; absolute throughput isn't comparable anyway |

**Data** (public oracleGeneral `.zst` from the `cache-datasets` S3 bucket / CMU FTP; read directly without decompressing)

| dataset | size | subset needed |
|---|---|---|
| Meta CDN (3 traces) | **2.2 GB** (verified by HEAD) | all 3 |
| Meta KV | 67 GB in the bucket today, but 2 files are dated 2023-12/2024-01, **later than the paper**; which 5 files the paper used is unclear | minimum: `meta_kvcache_traces_1` (1.7 GB) |
| Wiki CDN (3) | 53.6 GB | minimum: `wiki_2019t` (2.0 GB) |
| Tencent Photo (2) | 72 GB | optional |
| Twitter KV (54) | 1.6 TB full; S3 has only 10% samples (152 GB) | not needed for Figure 4 |
| CDN1 / CDN2 | proprietary | ❌ unobtainable |
| Zipf smoke-test trace | 2.8 MB, in the repo | smoke test |

Minimum partial Figure 4 ≈ **6 GB**; full Figure 4 ≈ 150–195 GB of the 253 GB free.

**Hard filters** — H1 ✅ official repo named in the paper · H2 ✅ for the simulator (the only sudo is the dependency script, replaced by conda); ❌ for faithful Figure 6 (turbo toggle, apt prerequisites) · H3 ✅ CPU-only, single node · H4 ✅ with caveats: the Meta KV file set has drifted since publication, and CDN1/CDN2 are unobtainable.

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | One plain CMake build; the documented dependency step is sudo-based and the README path is wrong |
| dependency fit | 4 | Only GLib dev and zstd are missing, both on conda-forge; the Figure 6 CacheLib stack is heavy |
| data fit | 3 | Public; minimum 6 GB, but full Figure 4 is 150–195 GB, the Meta KV set is ambiguous, and 2 datasets are proprietary |
| hardware fit | 4 | Simulator runs at paper scale per trace; Figure 6 needs a 2-socket node with turbo off |
| repro scripts | 2 | Only generic `cachesim` + `plot_mrc_size.py`; the Figure 4 plot script is left over from S3-FIFO (SIEVE missing, hard-coded paths), so the aggregation must be written by hand |
| extensibility | 5 | Function-pointer cache interface (`include/libCacheSim/cache.h:74-106`): a new policy is one `.c` file plus 3 registration lines |
| **total** | **22 / 30** | |

**Verdict: ✅ DOABLE (simulator, Figure 4); Figure 6 throughput is not realistically reproducible** · confidence high for build and run, medium for matching Figure 4 exactly · setup ≈1–2 person-days (0.5 day build + smoke test, 0.5–1 day Figure 4 driver) · compute: 6 GB subset < 1 h on 16 threads; full Figure 4 ≈ 0.5–1 day, tens of GB of RAM on Tencent.

**Key risks**
- **Meta KV file set drifted:** those points in Figure 4 may not match the paper.
- **The libCacheSim snapshot isn't pinned to an upstream commit.** Upstream has since changed algorithms and defaults, so use the snapshot for fidelity. gcc 12 with conda GLib is untested.
- **The FIFO-baseline formula and the Figure 4 aggregation must be re-implemented.**
- **Large traces at 10% cache size may need fewer threads** to bound memory.
- **GPL-3.0 applies to the libCacheSim code**, which matters only if modified code is redistributed.

**Where an add-on plugs in**
- **New eviction policy:** copy `libCacheSim/cache/eviction/Sieve.c` (implement `init/get/find/insert/to_evict/evict/remove`), declare it in `include/libCacheSim/evictionAlgo.h`, add a name branch in `bin/cachesim/cache_init.h`, and add it to `cache/eviction/CMakeLists.txt`.
- **Per-object metadata** (for example a multi-bit counter instead of the visited bit): `include/libCacheSim/cacheObj.h:126`. A frequency-aware variant already exists at `Sieve.c:165`.
- **Admission add-on** (like B-LRU): `cache/admission/*.c`, registered in `admissionAlgo.h`, run with `cachesim -a <name>`.
- **Tests:** `test/test_evictionAlgo.c` (`test_Sieve`).

**Build route (not executed)**
1. `conda create -y -n sieve -c conda-forge python=3.11 glib zstd pkg-config gperftools numpy matplotlib && conda activate sieve`
2. `cd repo/libCacheSim && mkdir -p _build && cd _build`
3. `PKG_CONFIG_PATH=$CONDA_PREFIX/lib/pkgconfig cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DENABLE_TESTS=OFF -DCMAKE_INSTALL_RPATH=$CONDA_PREFIX/lib -DCMAKE_BUILD_WITH_INSTALL_RPATH=ON && make -j32`
4. Smoke test: `./bin/cachesim ../data/trace.oracleGeneral.bin oracleGeneral fifo,lru,clock,sieve 0 --ignore-obj-size 1`
5. Download Meta CDN ×3 + `wiki_2019t` + `meta_kvcache_traces_1` (~6 GB)
6. For each trace: `cachesim $t oracleGeneral fifo,sieve,arc,wtinylfu,twoq,lirs,lhd,cacheus,hyperbolic,clock,lru 0.001,0.1 --ignore-obj-size 1 --num-thread 16`; B-LRU is `lru -a bloomfilter`
7. Write a ~50-line parser + plot that computes the reduction versus FIFO for Figure 4a/b

---

### 2. Kosmo: Efficient Online Miss Ratio Curve Generation for Eviction Policy Evaluation (FAST'24)

- **Repo:** https://github.com/Stumm-Lab/kosmo-fast24 — MIT, ~5.1k lines of Rust; 40 MB checkout, of which 33 MB is the bundled trace `traces/wdev.bin`.
  - **Last commit:** 2025-05-11, "Upgrade dependencies + modernize outdated code". The paper version is tag `v1.0.0-fast24`, identical to Zenodo 10569925.
- **What it is:** approximate miss-ratio curves (MRCs) for eviction policies that break the inclusion property (LFU, FIFO, 2Q, LRFU, plus LRU). Kosmo keeps one global object table with per-policy "eviction maps" and rebuilds cache stacks only when needed, where MiniSim keeps 100 separate caches.
  - **Three CLI tools:** `wss` (working-set size), `accurate` (100 full simulations as ground truth) and `mrc` (Kosmo or MiniSim with SHARDS sampling; reports MAE, memory or throughput).
- **Paper eval setup:**
  - **Hardware:** Threadripper 3990X, 64 cores, 256 GB.
  - **Traces:** 52 public traces, ~126 B accesses: MSR 13, Twitter 24, SEC 15.
  - **Sampling:** 3 SHARDS configs, granularity G = 10, 100 MiniSim caches.
  - **Scale:** the README estimates ~6 months of compute over ~4 TiB for the full campaign.
- **Reproduction target:** **Figures 6 (memory) + 8 (MAE), on the 13 MSR traces, for LFU and FIFO, all 3 SHARDS configs.** The claim: about **3.6× less memory** than MiniSim on average (up to 36×), with similar MAE (average within 0.25%). Memory is the least hardware-dependent claim; the 1.3× throughput claim (Figure 7) depends on core count.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| **Rust nightly** (`#![feature(btree_cursors)]`) | `src/mrc.rs:8`, `src/wss.rs:8`, `src/accurate.rs:8` (verified) | ❌ not installed | user `rustup`; there is **no `rust-toolchain` pin** |
| Edition 2024 → rustc ≥ 1.85 (the README's "1.77-nightly" is stale) | `Cargo.toml:4` (verified) | ❌ | pin a nightly near the last commit, e.g. `nightly-2025-05-10` |
| Crates (rayon, clap, serde, …); no `Cargo.lock` | `Cargo.toml`, `.gitignore:8` (verified) | fetched by cargo | small version-drift risk |
| `kwik` git dependency at tag v1.16.5 | `Cargo.toml:11` | pure Rust | cargo clones it |
| `fasthash 0.4.0` → 2018-era C++ built with `-msse4.2 -maes -mavx -mavx2` | `Cargo.toml:9` | gcc 12 present; CPU has AES and AVX2 | should build; fallback is a pure-Rust murmur3 in `src/shards.rs:54-56` |
| gnuplot 5.4 with pdfcairo (only for the final PDF) | README | not installed | `conda install -c conda-forge gnuplot=5.4.10` |
| Memory measured via `/proc/self/status` VmHWM | `kwik/src/sys/mem.rs` | ✅ user-readable | no root needed |
| No Docker, apt or sudo anywhere | README | ✅ | — |
| Trace format: 25-byte records (u64 timestamp, u8 command, u64 key, u32 size, u32 ttl) | `src/access.rs:39-63` | ⚠️ **no converter in the repo** | write one; validate against `traces/wdev.bin` (1,326,264 records, verified) |

**Data**

| dataset | size | how obtained | subset needed |
|---|---|---|---|
| MSR wdev (bundled) | 33 MB | in repo | smoke test |
| MSR Cambridge, 13 servers (434 M records) | 3.06 + 1.88 GB compressed → ~10.9 GB converted | SNIA IOTTA (click-through license) | ✅ **all 13 (target), ~16 GB disk** |
| Twitter, 24 clusters | ~749 GB zstd (~2.5 TB converted) | CMU FTP, no login | optional, small clusters only; **full set exceeds disk** |
| SEC EDGAR logs, 15 years | hundreds of GB zipped (~660 GB converted) | sec.gov | optional small years; **full set exceeds disk** |
| Authors' precomputed accurate curves | — | only on the artifact reviewers' VM | ❌ run `accurate` yourself |

> Easier route (my note, not from the explorer): the same MSR traces are published as `oracleGeneral .zst` on the CMU FTP (1.6 GB, no login; see the S3-FIFO section), so converting from that format avoids the SNIA click-through. Keys would then be hashed differently from the authors' `wdev.bin`, so validate on record and GET counts rather than exact keys.

**Hard filters** — H1 ✅ authors' lab repo, MIT, matches Zenodo · H2 ✅ no sudo, apt or Docker; rustup and conda install into `$HOME` · H3 ✅ CPU-only Rust; MSR-scale runs fit · H4 ✅ for the MSR subset (~16 GB); ❌ for full paper scale (Twitter + SEC far exceed 253 GB)

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | One `cargo build -r`, but on an unpinned nightly, with no lock file and 2018-era C++ in fasthash |
| dependency fit | 4 | All user-space (rustup, conda gnuplot); the risk is guessing the right nightly |
| data fit | 3 | The MSR subset is small, but there are no trace converters and the full Twitter/SEC data far exceeds disk |
| hardware fit | 4 | MSR runs at paper scale here; core count only affects the throughput claim |
| repro scripts | 2 | Tools print MAE, memory and throughput per trace, but there are no batch scripts, converters or plots for Figures 3–10 |
| extensibility | 4 | Clean per-policy trait modules (EvictionMap, LocalObject, ReconstructedStack, Cache); a new policy needs dispatch boilerplate in ~5 files |
| **total** | **21 / 30** | |

**Verdict: 🟡 DOABLE-WITH-WORK** · confidence medium · setup ≈2–3 person-days (0.5 toolchain, ~1 converter, ~1 run/plot scripts) · compute: 312 `mrc` runs + 26 `accurate` runs on MSR ≈ 1–3 days wall-clock (`accurate` dominates); < 20 GB disk.

**Key risks**
- **Toolchain drift:** nightly-only feature, edition 2024, no toolchain pin, no lock file.
- **fasthash-sys is unmaintained C/C++.** A pure-Rust murmur3 fallback may sample a different key set.
- **No trace converters and undocumented key hashing.** Whether writes are kept changes the throughput metric.
- **Current `main` is a May-2025 modernized version, not the Jan-2024 paper snapshot.** The README's numbers (5×/9×/1.2×) also disagree with the paper's (3.6×/36×/1.3×).
- **Throughput depends on hardware** (32 vs 64 threads, shared machine).
- **Minor code issues:** batching drops one access per 10 M records; a divide-by-zero on runs under 1 ms.

**Where an add-on plugs in**
- **New Kosmo policy** (e.g. S3-FIFO, mentioned in a paper footnote but not shipped; ARC/LIRS, listed as future work):
  - `src/kosmo/policy.rs`
  - `src/kosmo/eviction_map/<p>_eviction_map.rs`
  - `src/kosmo/local_object/<p>_local_object.rs`
  - `src/kosmo/reconstructed_stack/<p>_reconstructed_stack.rs`
- **Ground truth / MiniSim for that policy:** the `Cache` trait (`src/cache.rs`), plus `src/cache/<p>_cache.rs` and `src/cache/policy.rs`.
- **Algorithm changes** (adaptive granularity, faster stack rebuild): `Kosmo::perform_evictions` / `reconstruct_policy_stacks` in `src/kosmo.rs` (`GRANULARITY` at :35). Multi-policy runs are already supported by `Kosmo::new(&[KosmoPolicy])`, but `init_kosmo` in `src/mrc.rs:197-202` passes only one policy.
- **Sampling:** the `Shards` trait in `src/shards.rs`.

**Build route (not executed)**
1. `curl -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain none --no-modify-path && source ~/.cargo/env`
2. `rustup toolchain install nightly-2025-05-10 --profile minimal && rustup override set nightly-2025-05-10` (in the repo)
3. `conda create -y -n kosmo -c conda-forge gnuplot=5.4.10 zstd python=3.11`
4. `cargo build -r`
5. Smoke test: `./target/release/wss -p traces/wdev.bin` should print 313344512, then run `accurate` and `mrc -k lfu` / `-m lfu` on wdev
6. Get the MSR traces and write `msr_to_kosmo.py` (25-byte records); validate by rebuilding `wdev.bin`
7. Driver: `wss` → `accurate` (lfu, fifo) → `mrc` {Kosmo, MiniSim} × 3 SHARDS configs × {memory, throughput}; parse the `MAE:`, `Memory usage:` and `Throughput:` lines and box-plot against Figures 6–8

---

### 5. 3L-Cache: Low Overhead and Precise Learning-based Eviction Policy for Caches (FAST'25)

- **Repo:** https://github.com/optiq-lab/3L-Cache — GPL-3.0; last commit 2025-08-09 (`134cd15`, "update 3LCache+"); 925 MB checkout, of which `data/` sample traces are 722 MB. It contains a vendored libCacheSim and a **modified LightGBM 2.2.2**.
- **What it is:** a learned per-object eviction policy, about 870 lines of C++ in `3LCache/`. It predicts each object's next arrival with a LightGBM model, and keeps overhead low with bidirectional sampling, batched eviction and automatic parameter tuning.
- **Paper eval setup:**
  - **Traces:** 4,855 traces from 8 public datasets (CloudPhysics 106, Tencent CBS 4,030, Alibaba 652, Twitter 54, …), 267 B requests.
  - **Baselines:** 12 policies, including LRB, GL-Cache and HALP.
  - **Sizes and metrics:** cache sizes 0.1% and 10%; byte and object miss-ratio reduction versus LRU; CPU overhead measured as a simulator-throughput ratio.
  - **Hardware:** a dual-Xeon server with 192 GB.
- **Reproduction target:** **Figure 6(a)+(e), CloudPhysics byte miss-ratio reduction versus LRU at small and large sizes.** The same runs also give Figure 8(a)/(e) and a CloudPhysics-only Figure 10 (CPU overhead). The claim: the largest reduction at nearly every percentile, at about 6.4× LRU's CPU, 94.9% less than LRB. CloudPhysics fits well: the public copy has exactly the paper's 106 traces in 9 GB.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| "Ubuntu 18.04, cmake 3.28.6" | README | Debian 12, cmake 3.25.1 | top-level CMake only needs ≥ 3.12, so fine |
| **Current version doesn't configure:** `cache/eviction/CMakeLists.txt:97-99` references `../../../../3LCache+`, one level above the repo | verified: that path doesn't exist; `../../../3LCache+` does | ❌ as shipped | one-line `sed` fix, or check out `fa5caa6` (the commit before 3LCache+ was added) |
| glib-2.0 dev | `CMakeLists.txt:142` | ❌ runtime only | conda-forge `glib` |
| zstd dev (required) | `CMakeLists.txt:150-159` | ❌ runtime only | conda-forge `zstd` |
| argp, OpenMP (libgomp) | — | ✅ | — |
| tcmalloc | `CMakeLists.txt:171-179` | missing, optional | conda `gperftools` or skip |
| `install_dependency.sh` (sudo apt; 3× `sudo make install`) | `scripts/install_dependency.sh:4-5,29,44,55` | ❌ | replace with user-prefix installs |
| **Modified LightGBM 2.2.2** (required for 3L-Cache and LRB) | non-standard C API: `LGBM_BoosterPredictForCSR` takes a `std::unordered_map` (`c_api.h`, verified) | ⚠️ must build the vendored copy | prebuilt conda/pip LightGBM **won't link**. Build `scripts/LightGBM` into `$HOME/local`; gcc 12 likely needs `#include <limits>` in ~5 files (`common.h` lacks it, verified), or use a conda gcc 9/10 |
| xgboost 2.0.0 (GL-Cache; on by default and required) | `CMakeLists.txt:26,187-190` | missing | `-DENABLE_GLCACHE=OFF` (GL-Cache isn't in the repo's scripts anyway), or build it into a prefix |
| HALP baseline | only a plot label | ❌ **not in the repo** (verified) | drop HALP from the figures |
| Python numpy, matplotlib + undeclared pandas, openpyxl, psutil | `requirements.txt`; scripts | user install | pip |
| Dockerfile | builds *upstream* libCacheSim, not this fork | not applicable | ignore |

**Data**

| dataset | size | subset needed |
|---|---|---|
| In-repo `data/` samples (57 CSVs truncated to 1 M / 100 K requests, plus a Tencent zip) | 722 MB | smoke test only; not comparable with the paper's cache sizes |
| CloudPhysics (oracleGeneral `.zst`, public S3 `2015_cloudphysics/`) | **106 traces, 9.0 GB** | ✅ target (Figures 6a/e, 8a/e) |
| Tencent CBS | 163 GB (378 large traces: 79 GB) | stretch: the only dataset with explicit numbers in the paper (Figure 6b: mean 11.6% vs LRB 8.6%) |
| Alibaba / Twitter (S3 copies are 10% samples) / Wiki / Tencent Photo / Meta | 2–152 GB each | not needed |
| Full 8-dataset corpus | ≈ 620 GB | exceeds disk |

**Hard filters** — H1 ✅ named in the paper and its Artifact Appendix · H2 ✅ with work: sudo appears only in the dependency script, and every dependency installs to a user prefix · H3 ✅ CPU-only; CPU overhead comes from simulator throughput, not perf counters · H4 ✅ for CloudPhysics (9 GB); ❌ full corpus (620 GB).

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | **2** | sudo-based one-liner; **current version doesn't configure** (bad `3LCache+` path); modified LightGBM 2.2.2 fork likely hits gcc-12 `<limits>` errors |
| dependency fit | 4 | glib/zstd headers via conda; LightGBM from the vendored copy; xgboost optional; the modified API rules out prebuilt packages |
| data fit | 4 | CloudPhysics has exactly the paper's 106 traces in 9 GB; the authors' preprocessed CSVs aren't published and the Twitter copies are 10% samples |
| hardware fit | 4 | Single-threaded sims; CloudPhysics and even Tencent fit in hours to a day or two; only disk limits the full corpus |
| repro scripts | 3 | `run_scripts.sh` (executor → collect → draw → Figures 6/8/10), but it reads only `.csv` from a hard-coded `../../data/`, looks up sizes by CSV name, omits LRB/GL-Cache/HALP, and has no download scripts |
| extensibility | 4 | Policy cleanly split into `lookup/admit/evict/sample/rank/train/prediction` in `3LCache/TLCache.cpp`; `3LCache+/` already shows how to add a variant (~5 lines of registration) |
| **total** | **21 / 30** | |

**Verdict: 🟡 DOABLE-WITH-WORK** · confidence medium (build issues checked by path resolution and headers; nothing compiled) · setup ≈2–3 person-days (1 dependencies + patches, 0.5–1 script adaptation to `.zst` and fractional sizes, 0.5 plots) · compute: CloudPhysics × 10 policies × 2 sizes ≈ 10–20 core-hours (2–4 h wall); +40–80 core-hours if LRB is included; Tencent stretch 79–163 GB disk, 100–300 core-hours.

**Key risks**
- **Broken CMake path at the current commit;** 3LCache+ also changed `TLCache.cpp`, so pick a version deliberately.
- **LightGBM fork:** non-standard API; gcc-12 compile fixes needed.
- **Preprocessing mismatch:** the S3 oracleGeneral traces may differ from the authors' unpublished CSVs, so compare rankings and relative reductions, using fractional sizes `0.001,0.1`.
- **Incomplete baselines:** HALP isn't implemented, GL-Cache needs xgboost, and LRB (~20× the CPU) dominates compute.
- **Machine contention skews Figure 10:** the executor launches 32 concurrent jobs, so run throughput passes with ≤ 16 jobs.
- **Garbled hardware in the paper:** "Xeon Gold 5128R" isn't a real part number; only the ratios matter.

**Where an add-on plugs in**
- **Policy hooks** in `3LCache/TLCache.cpp`: `train()` :12, `sample()` :63, `lookup()` :75, `admit()` :159, `rank()` :192, `evict()` :301/308, `evict_predobj()` :343, `prediction()` :383. These cover sampling, features, eviction ratio and retraining triggers.
- **Features and tunables** in `3LCache/TLCache.h`: `Meta` :57; `sample_rate`, `eviction_rate`, `reserved_space` ~:250-268; LightGBM `training_params` ~:297; `batch_size` :27.
- **New variant:** copy `3LCache/TLCache_Interface.cpp`, as `3LCache+/TLCacheN_Interface.cpp` does, and register it in `bin/cachesim/cache_init.h:141-149`, `evictionAlgo.h:131-133` and `cache/eviction/CMakeLists.txt:92-99`.
- **Experiment lists:** `3LCache/scripts/executor_libcachesim.py:66` and `libcachesim_result_collect.py`.

**Build route (not executed)**
1. `conda create -y -n 3lc -c conda-forge python=3.11 glib zstd gperftools pkg-config numpy matplotlib pandas openpyxl psutil awscli`
2. Fix the path: `sed -i 's#\.\./\.\./\.\./\.\./3LCache+#../../../3LCache+#' libCacheSim/cache/eviction/CMakeLists.txt`
3. Add `#include <limits>` to the ~5 LightGBM files; `cmake -S scripts/LightGBM -B scripts/LightGBM/build -DCMAKE_INSTALL_PREFIX=$HOME/local/3lc && cmake --build … -j32 && cmake --install …`
4. `cmake -S . -B _build -DCMAKE_BUILD_TYPE=Release -DENABLE_GLCACHE=OFF -DENABLE_LRB=ON -DENABLE_TESTS=OFF -DCMAKE_PREFIX_PATH="$HOME/local/3lc;$CONDA_PREFIX" && cmake --build _build -j32`
5. Smoke test on the bundled Tencent sample; expect miss ratio ≈ 0.3380 (README.md:75)
6. `aws s3 sync --no-sign-request s3://cache-datasets/cache_dataset_oracleGeneral/2015_cloudphysics/ ~/traces/cloudphysics/` (9 GB)
7. Run 10 policies × `0.001,0.1` per trace; patch the executor to glob `*.zst` and the collector to key by trace name; plot the CloudPhysics panels; re-run throughput with ≤ 16 jobs for Figure 10

---

### 7. PowerInfer: Fast Large Language Model Serving with a Consumer-grade GPU (SOSP'24)

- **Repo:** https://github.com/SJTU-IPADS/PowerInfer (now redirects to `Tiiny-AI/PowerInfer`) — MIT; 77 MB checkout; C++/C/CUDA/Python.
  - **History:** last commit 2026-05-11 (a README edit). The core engine was last really changed in 2024-09.
  - **Artifact:** no tags or separate AE repo; the SOSP artifact is `main`.
  - **Not released:** **the offline profiler and predictor training** (`README.md:298` "[ ] Release predictor training code", verified). Activation statistics and trained predictors come ready-made inside the GGUF files on Hugging Face.
- **What it is:** a llama.cpp/ggml fork for ReLU-sparse LLMs split across GPU and CPU. An offline ILP puts frequently activated ("hot") FFN neurons on the GPU and leaves "cold" ones on the CPU. Small MLP predictors choose which neurons to compute per token, using sparse operators on both sides. `--vram-budget` replaces llama.cpp's `-ngl`.
- **Paper eval setup:**
  - **Machines:** PC-High = i9-13900K + 192 GB + RTX 4090 24 GB; PC-Low = i7-12700K + 64 GB + RTX 2080Ti 11 GB.
  - **Models:** OPT 7B–175B, Falcon-40B, LLaMA2(ReGLU) 7B/13B/70B, Bamboo-7B; FP16 and INT4.
  - **Baselines:** llama.cpp, SpecInfer, vLLM.
  - **Headline:** up to 11.69× (Falcon-40B FP16).
- **Reproduction target:** **Table 4, LLaMA(ReGLU)-13B-FP16 on a 24 GB GPU, 1.5K-token input / 256-token output: llama.cpp 49.91 ms/token vs PowerInfer 14.38 ms/token (3.47×).** Why this row:
  - The released files (28.3 GB) are just larger than 24 GB of VRAM, the case the engine is built for. With a model that fits entirely on the GPU there is no speedup (issue #128).
  - No gated models are needed.
  - Cheap follow-up: emulate PC-Low with `--vram-budget 11`; Bamboo-7B needs no conversion at all.

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| CMake ≥ 3.17 (CUDA); C11/C++11 | `CMakeLists.txt:1,252` | ✅ 3.25.1, gcc 12.2 | as-is (gcc 14 breaks it, #267; gcc 12 is fine) |
| CUDA toolkit + cuBLAS | `CMakeLists.txt:254-288` | ✅ system nvcc 11.8 + `libcublas.so.11` + `g++-11` host compiler (verified) | pass `-DCMAKE_CUDA_COMPILER=/usr/bin/nvcc -DCMAKE_CUDA_HOST_COMPILER=g++-11`. **Don't use conda CUDA ≥ 12.3**: driver 535 gives PTX errors (#229) |
| CUDA arch default `52;61;70` / `60;61;70` (no 86) | `CMakeLists.txt:290-299` (verified) | ⚠️ JIT fallback is slow | `-DCMAKE_CUDA_ARCHITECTURES=86` |
| CPU SIMD: AVX2/F16C/FMA; AVX-512 **off** by default | `CMakeLists.txt:69-71`; the paper's 13900K has no AVX-512 either | ✅ Zen 3 has AVX2/F16C/FMA (verified) | no AVX-512 assumption |
| Python ≥ 3.8: numpy, sentencepiece, transformers, local `gguf-py`, `powerinfer-py` | `requirements.txt` | user install | `conda create -n powerinfer python=3.10` + pip |
| torch ≥ 2, cvxopt 1.3.2 (GLPK ILP solver) | `powerinfer-py/pyproject.toml:18-19` | user install | CPU torch wheel is enough |
| Runtime calls `python3 -m powerinfer` on first load | `llama.cpp:3120-3134` | ⚠️ | keep the conda env active |
| Docker images | `.devops/full-cuda.Dockerfile` (stale: calls `make`, no Makefile) | not applicable | native CMake build |
| 24 GB GPU (paper: RTX 4090) | paper | A5000 24 GB, Ampere sm_86 | same VRAM; lower GPU memory bandwidth (768 vs 1,008 GB/s); #184 says a 3090 (sm_86) behaved correctly |
| Host RAM for spill-over (paper: 192 GB) | paper | 125 GiB | fine for 7B/13B FP16 and 40B/70B INT4; **70B FP16 (~140 GB) doesn't fit** |

**Models** (Hugging Face; sizes and gating verified via API)

| artifact | size | gated? | needed |
|---|---|---|---|
| `Tiiny/ReluLLaMA-13B-PowerInfer-GGUF` | **28.3 GB** | no | ✅ PowerInfer side of the target |
| `SparseLLM/ReluLLaMA-13B` (safetensors) | **26.0 GB** | no | ✅ only to `convert-dense.py` into a ~26 GB f16 baseline GGUF, then delete |
| `Tiiny/Bamboo-base-v0.1-gguf` | 39.4 GB total | no | optional cheap check (Figure 11 / Table 5) |
| `Tiiny/ReluLLaMA-70B-PowerInfer-GGUF` (Q4) | 42.2 GB | no | stretch; dense Q4 baseline source is 276 GB → over disk |
| `Tiiny/ReluFalcon-40B-PowerInfer-GGUF` (Q4) | 25.5 GB | **yes (auto)** | stretch only, needs an HF token |
| `SparseLLM/ReluFalcon-40B` (FP32) + predictor | 167 + 14 GB | no | ❌ the 11.69× FP16 headline needs ≈ 264 GB > 253 GB free |
| OPT-13B/30B/66B/175B predictors | — | **not released** | ❌ OPT results can't be reproduced |
| Prompts (ChatGPT-prompts, Alpaca) | small | public | no sampling script, so write a ~1.5K-token prompt file |

Minimum for the target: ~54 GB download, ~81 GB peak disk, ~55 GB after cleanup.

**Hard filters** — H1 ✅ official repo, MIT (the profiler and predictor trainer are unreleased) · H2 ✅ user-space CMake + pip; no kernel, driver or Docker · H3 ✅ one 24 GB GPU, AVX2 only; absolute speeds differ from a 4090 · H4 ✅ for the 7B/13B targets; ❌ for Falcon-40B FP16 (disk), 70B FP16 (RAM) and OPT-30B+ (predictors unreleased).

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | One documented cmake command; needs extra flags for the Debian nvcc path and arch 86, plus an active Python env at runtime |
| dependency fit | 4 | System CUDA 11.8 + gcc-11 works with driver 535; torch/cvxopt have wheels |
| data fit | 3 | 7B/13B GGUFs are public at 15–28 GB; the flagship Falcon-40B FP16 and 70B FP16 don't fit; Falcon Q4 is gated; OPT predictors are missing |
| hardware fit | 4 | Same 24 GB VRAM and AVX2-only CPU assumption; `--vram-budget` emulates the 11 GB PC-Low; slower GPU, less RAM, and different CPU memory bandwidth |
| repro scripts | **2** | No figure or benchmark scripts; `llama-bench` lacks `--vram-budget`; only README one-liners |
| extensibility | 4 | Neuron placement is a clean Python plug-in (`powerinfer-py/powerinfer/solver.py`, `export_split.py`); the runtime is huge single files (`llama.cpp` 423 KB, `ggml.c` 680 KB, `ggml-cuda.cu` 367 KB); predictor changes are hard without the trainer |
| **total** | **21 / 30** | |

**Verdict: 🟡 DOABLE-WITH-WORK** · confidence medium-high · setup ≈2–3 person-days (½ build, ½ downloads + dense conversion, 1–2 benchmark harness) · compute: ~54 GB download (1–2 h), ~15 min build, ~15 min conversion, < 2 GPU-hours for Table 4 with 5 repeats + PC-Low emulation.

**Key risks**
- **Baseline fidelity.** The "llama.cpp" baseline must be this repo's dense mode on a `convert-dense.py` GGUF with `-ngl`; upstream llama.cpp can't run ReLU LLaMA correctly, and the paper's exact baseline build isn't documented.
- **This CPU may shrink the ratio.** The Threadripper's 8-channel DDR4 likely has more memory bandwidth than the 13900K, which speeds up llama.cpp's CPU layers and could reduce the 3.47×.
- **Small spill-over.** 13B FP16 is only ~5 GB over 24 GB, so the result is sensitive to `--vram-budget` accounting, which is known to be inaccurate. Report the actual offloaded MiB from the logs.
- **Ampere correctness** (A100 anomalies reported in #184): sanity-check outputs first.
- **Headline gap.** The 11.69× Falcon result and the OPT results can't be reproduced here; a 13B result confirms the mechanism, not the biggest number.
- **ILP caching.** The solver has a 30 s GLPK limit and caches `*.generated.gpuidx`, so pass `--reset-gpu-index` whenever the budget changes.
- **Unmaintained core.** No CUDA CI.

**Where an add-on plugs in**
- **Hot/cold placement policy:** `powerinfer-py/powerinfer/solver.py::solve_gpu_split` (ILP) and `export_split.py::export_split`, called from `llama.cpp:3088 llm_load_gpu_split_with_budget`. Communication-aware, budget-adaptive or workload-specific placements can be swapped in **without touching C++**.
- **Online / dynamic re-placement:** `llama.cpp:2781 llama_gpu_split_loader`, `:10130 llama_model_offload_ffn_split`, `:3000 buffered_tensor_allocator`.
- **VRAM budgeting:** `llama.cpp:188 llama_set_vram_budget`; flags in `common/common.cpp:474-566`.
- **Predictor threshold / adaptive sparsity:** `llama.cpp:4652 llm_build_ffn_sparse`; env `LLAMA_SPARSE_PRED_THRESHOLD` (`llama.cpp:1269`).
- **Sparse operators:** CPU `ggml.c:14030 ggml_compute_forward_mul_mat_sparse` (AVX2 axpy :14285-14330); GPU `ggml-cuda.cu:8787 ggml_cuda_mul_mat_sparse`.

**Build route (not executed)**
1. `conda create -n powerinfer python=3.10 -y && conda activate powerinfer && pip install torch --index-url https://download.pytorch.org/whl/cpu && pip install -r requirements.txt "huggingface_hub[cli]"`
2. `cmake -S . -B build -DLLAMA_CUBLAS=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/bin/nvcc -DCMAKE_CUDA_HOST_COMPILER=g++-11 -DCMAKE_CUDA_ARCHITECTURES=86 && cmake --build build -j 32`
3. `huggingface-cli download Tiiny/ReluLLaMA-13B-PowerInfer-GGUF` and `SparseLLM/ReluLLaMA-13B` (safetensors)
4. `python convert-dense.py --outtype f16 --outfile …/llama-13b-relu.f16.gguf …/ReluLLaMA-13B`, then delete the safetensors
5. Sanity run: `./build/bin/main -m …powerinfer.gguf -n 32 -t 16 -p "Once upon a time"`; the log should show `offloaded … MiB of FFN weights to GPU`
6. Table 4 PowerInfer: `-c 2048 -f prompt_1500tok.txt -n 256 --ignore-eos -t 16`; read ms/token from `llama_print_timings`, ×5
7. Table 4 baseline: dense f16 GGUF with the largest `-ngl` that fits (~34–36 of 40), ×5; compare to 49.91 vs 14.38
8. Optional PC-Low: `--vram-budget 11 --reset-gpu-index` vs an `-ngl` that fits in 11 GB

---

### 8. Learning-Augmented Heuristics: Simple Yet Smart, Robust and Interpretable Cache Eviction — S4-FIFO (OSDI'26)

- **Repo:** https://github.com/cacheMon/osdi26-s4-fifo — Apache-2.0; last commit 2026-05-12 (`000095f`); 672 KB checkout, no LFS.
  - **Submodules:** libCacheSim fork `haochengxia/libCacheSim@1f62efc` (GPL-3.0, 128 MB) and CacheLib fork `williamnixon20/CacheLib@72bb810`.
- **What it is:** S3-FIFO with 5 cache-level settings: small-queue ratio, ghost ratio, two promotion thresholds, and a skip ratio. After a warmup it collects 73 cache-level features, and an offline-trained LightGBM classifier makes **one** prediction that picks 1 of 18 settings bundles. The data path stays O(1) FIFO queues; inference is exported to C/C++ with m2cgen.
- **Paper eval setup:**
  - **Traces:** 5,175 production traces from 14 sources, split 4,140 train / 1,035 test ("randomly"); cache sizes 0.1/1/10%.
  - **Labels:** grid search over 168 settings combinations.
  - **Test protocol:** run defaults for 20% of the trace, predict once, then either switch for the remaining 80% ("v1 online") or apply the prediction to the whole trace ("v2 retrospective").
  - **Baselines:** S3-FIFO, LIRS, ARC, LRB, 3L-Cache, LHD, GL-Cache, LeCaR.
  - **Throughput:** CacheBench at 48 threads.
  - **Hardware:** a 20-node × 32-core cluster.
- **Reproduction target:** **Figure 6(a), mean miss-ratio reduction versus FIFO at the large (10%) cache.** The claim: +26% over S3-FIFO, +8% over 3L-Cache, and v2 within 0.2% of the offline grid-search best. Figure 7a/c (worst case / 10th percentile) comes from the same runs. This has to be **scaled to a public-trace subset with a retrained model** (see Data and Key risks).

**Requirements vs this machine**

| requirement | source | status here | route / blocker |
|---|---|---|---|
| gcc ≥ 11, cmake ≥ 3.12 | README; `libCacheSim/CMakeLists.txt:1` | ✅ | builds with **`-Werror`** (`CMakeLists.txt:92`); add `-Wno-error` if gcc 12 complains |
| glib-2.0 dev, zstd dev | `CMakeLists.txt:123-150` | ❌ runtime only | conda-forge `glib zstd pkg-config` |
| argp; tcmalloc optional | `CMakeLists.txt:135,156` | ✅ / skip | — |
| `sudo apt install …`; Docker image | README; `install_dependency.sh`; Dockerfile | ❌ | replay the steps via conda |
| LightGBM / XGBoost C libraries (only for 3L-Cache/LRB/GL-Cache baselines) | `CMakeLists.txt:171-194` | missing | conda-forge `liblightgbm libxgboost` |
| Python: numpy, pandas, sklearn, xgboost, lightgbm, joblib, m2cgen, torch (unpinned) | `requirements.txt` | user install | py3.11 env; CPU torch is enough |
| Cluster task runner: hard-coded `/mnt/cfs/…`, distComp format, scp to node1..19 | `grid_search/yield_tasks.py:7-9`, `apply.sh` | ⚠️ unusable as-is | rewrite paths; `parallel -j30` |
| **Intermediate CSVs** (`features_20pct.csv`, `cleaned/*/grid_full.csv`, `baselines.csv`) | `analysis/.gitignore` (verified) | ❌ **not released** | regenerate by simulation and write the missing glue (log dumps → CSV) |
| **The paper's trained model** (20 trees, depth 9) | paper §4.4.3 | ❌ **not released** | only a "lite" 5 × 50-tree, depth-4 model exists in the CacheLib fork (47% top-1). Retrain |
| **Online inference inside the simulator** | `REPRODUCTION.md:106,154` suggests `s4fifo -e collect-features` predicts | ❌ **absent**: `S4FIFO.c` only snapshots features at PREDICTION and calls an optional callback, and `S4FIFO_set_phase_callback` has **no callers** (verified) | v2 can be scored by table lookup; v1 needs ~100 lines of C (model header + queue resize) |
| CacheLib throughput (Figure 8) | README (`sudo … install-system-deps`) | ❌ sudo step; 48 vs 32 threads | optional; getdeps from source is fragile |
| Label-generation compute (paper: 20 × 32 cores) | paper | 1 × 32 threads | fits CPU-wise at ~1/20 throughput, so use a trace subset |

**Data** (public `cache-datasets` S3 bucket, oracleGeneral)

| dataset | size | subset needed |
|---|---|---|
| CloudPhysics (104) + MSR (14) + Meta Storage (5) + Meta CDN (3) | **≈ 12.6 GiB**, ~2.8 B requests | ✅ core subset (126 traces) |
| Tencent CBS (3,370) | ≈ 142 GiB | add ~500 random traces (≈ 21 GiB) so the 18-class model has enough training data; the name mapping `tencentBlock.nsN` ↔ `tencentBlock_N` is unverified |
| Alibaba (552) | ≈ 93 GiB | optional |
| Twitter sample10, Meta KV, Tencent Photo, Wiki | 50–134 GiB each | skip |
| CDN1 (Akamai, 163), CDN2 (890), FIU, Systor | ~22% of the corpus | ❌ **private / on request** |
| Sample traces in repo | 3–62 MB | smoke test (miss ratio ≈ 0.48) |
| All public traces at paper scale | ≈ 560 GiB, ≈ 11 days on this box | ❌ doesn't fit |

**Hard filters** — H1 ✅ official repo, Apache-2.0, public pinned submodules · H2 ✅ user-space cmake + conda; sudo only for optional CacheLib · H3 ✅ CPU-only trace simulation; paper scale is only a time problem · H4 ✅ at subset scale; ❌ for exact numbers (private CDN traces, and the model, labels and feature CSVs are unreleased).

**Repo-exploration scores (1–5)**

| axis | score | justification |
|---|---|---|
| build complexity | 4 | One documented cmake/make with common libraries; `-Werror` + conda glib add friction; CacheLib optional |
| dependency fit | 4 | glib/zstd headers trivial via conda; apt lines skipped |
| data fit | 3 | 12–35 GiB public subset is enough for a scaled target, but ~22% of paper traces are private and no labels, features or model are released |
| hardware fit | 3 | Runs, but label generation used 20 × 32 cores; paper scale ≈ 2 weeks here |
| repro scripts | **2** | Training and plot scripts exist but read unreleased CSVs; task generators hard-code `/mnt/cfs`; the log→CSV glue is missing; the grid JSONs (54/72/72 combos) don't match the paper's 168; docs reference missing scripts; **the simulator has no inference path** |
| extensibility | 4 | Clean phase state machine in `S4FIFO.c`, separate feature header, table-driven registration, single training script with explicit config/cost-matrix/split functions |
| **total** | **20 / 30** | |

**Verdict: 🟡 DOABLE-WITH-WORK** · confidence medium · setup ≈**4–6 person-days** (0.5 build, 0.5 data, 1.5–2 rebuilding the 168-combo grid + CSV glue, 1 training/eval/plots, +1–1.5 for true v1 online switching in C) · compute: 126 traces × 168 combos × 2 sizes ≈ 9.4e11 simulated requests ≈ 6 h on 30 jobs; +500 Tencent ≈ +11 h; 0.5–1.5 machine-days, CPU only, 15–40 GB disk.

**Key risks**
- **`s4fifo` in the simulator never runs a model** (verified), so v1 "online" numbers need new code.
- **Three inconsistent models:**
  - Paper: 20 trees, depth 9.
  - Training script: an ensemble of 20 LightGBM classifiers with 200–580 trees, depth 6–9, ~75 features.
  - Released: only the lite 5 × 50-tree model.
- **The split contradicts "randomly split"** (verified). `train_xgb_18class.py:295-329` forces ~30 worst-case traces (where S4-FIFO/ARC/LeCaR did worst) into **training** and hand-picked "showcase" traces into **test**, so the Figure 7 robustness claim may not survive a truly random split. **This is itself a strong course-project angle.**
- **Private traces are ~22% of the corpus,** and accuracy depends on thousands of training traces, so a subset-trained model will likely fall short of +26%. Compare against the grid-search offline best to separate data effects from method effects.
- **Doc drift:** the 168 grid must be rebuilt (7 small ratios × ghost {0.9, 3, 6} × 2 × 2 × 2), and the trace filters differ (100K vs 1M objects).
- **`-Werror` build risk;** CacheLib throughput is the riskiest part.

**Where an add-on plugs in**
- **`S4FIFO.c`:**
  - `S4FIFO_transition_phase` (:153), PREDICTION branch: call an m2cgen C model and resize the queues. **This is the missing online step.**
  - `S4FIFO_update_phase` (:187) with `prediction-interval`: periodic or drift-triggered re-prediction.
  - `S4FIFO_parse_params` (:451): new settings.
- **`S4FIFO.h`:** `S4FIFO_base_params_t` (:40), `S4FIFO_shared_init_queues` (:109) for runtime queue resizing. **`S4FIFO_features.h`:** new or sampled features.
- **Learning side:** `analysis/train_xgb_18class.py` (`SELECTED_CONFIGS` :15-34, `engineer_features` :82, `split_by_trace` :167, `build_empirical_cost_matrix` :402), `create_grid_optimal.py`, `export_models_multilang.py`.
- **Real cache:** CacheLib fork `cachelib/allocator/MMS4FIFO.h`, `S4FIFOLightGBMPredictor.h`.

**Build route (not executed)**
1. `git submodule update --init libCacheSim` (the pinned checkout already exists at `../libCacheSim`)
2. `conda create -y -n s4fifo -c conda-forge python=3.11 glib zstd gperftools pkg-config ninja liblightgbm libxgboost lightgbm xgboost pandas numpy scikit-learn matplotlib seaborn joblib parallel awscli && pip install m2cgen`
3. `cmake -S libCacheSim -B libCacheSim/_build -G Ninja -DCMAKE_BUILD_TYPE=Release -DENABLE_TESTS=OFF -DCMAKE_PREFIX_PATH=$CONDA_PREFIX -DCMAKE_BUILD_RPATH=$CONDA_PREFIX/lib -DENABLE_3L_CACHE=ON -DENABLE_LRB=ON` (+ `-Wno-error` if needed); `ninja -C libCacheSim/_build`
4. Smoke test: `cachesim libCacheSim/data/cloudPhysicsIO.vscsi vscsi s4fifo 1GB -n 100000` (≈ 0.48), then `s4fifo-base`, `s3fifo`
5. `aws s3 cp --no-sign-request --recursive` CloudPhysics, MSR, metaStorage and metaCDN (+ ~500 Tencent)
6. Patch `grid_search/yield_tasks.py`: local paths, the 168-combo grid, sizes {0.001, 0.1}; pipe to `parallel -j30`
7. Patch `feature/yield_feature_tasks.py` (20%, local paths); run the baselines with `parallel -j30 cachesim …`
8. Write the glue (aggregate → `cleaned/*/grid_full.csv`, `baselines.csv`, `features_20pct.csv`); `create_grid_optimal.py`
9. `train_xgb_18class.py` twice: as shipped, and with the forced train/test lists emptied (true random split); `plot_cleaned_data.py` → Figures 6/7
10. Optional v1 online: m2cgen export → wire into `S4FIFO_transition_phase`, rebuild, rerun test traces

---

