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
