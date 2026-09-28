# 0_reproduce: Baleen (FAST '24) reproduction wrapper

This wrapper reproduces **Figure 9** of the Baleen paper (peak backend load per trace) on Region7 and Region6, sample 0, using the unmodified authors' artifact. Targets and pass criteria are in [REPRODUCE_PLAN.md](REPRODUCE_PLAN.md).

## Rules this wrapper enforces
- **`baleen_code/` is frozen.** It is a read-only clone (commits in `FROZEN_baleen_code.txt`). `check_frozen.sh` runs before and after every batch and fails on any changed or new file.
- **Every runtime write stays inside this directory.** `env.sh` points HOME, the XDG dirs, pip, conda, matplotlib, jupyter and TMPDIR here.
  - The artifact hard-codes a cache at `/tmp/cache-sim-accesses-*` (`BCacheSim/cachesim/utils.py:29`). Every job therefore runs under `bwrap` with `/tmp` bound to `work/systmp`.
  - `check_no_leak.sh` verifies nothing was written outside this directory.
- **We follow the artifact's harness.** Jobs run `python -B -m BCacheSim.episodic_analysis.train …` and then `python -B -m BCacheSim.cachesim.simulate_ap …`, from `work/`, the same way `BCacheSim/run_py.sh` does. The arguments are the authors' own `TrainCommand` and `ReproduceCommand` from `results_release.csv.gz`, one job per authors' run. Only paths and the experiment name are rewritten.
- **Three runtime adaptations were needed.** None of them touches algorithm parameters. `analyze.py` lists them in every report.
  1. The simulator is given `--eviction-policy LRU`. The authors' commands predate this flag, and the frozen simulator's default of `None` crashes. `EvictionPolicy` is `LRU` for every row used here.
  2. `--offline-ap-decisions` is dropped. The authors' file came from a separate analysis over the full trace. The one `train.py` produces covers only day 1, so the per-access lookup raises `KeyError`. For our policies the loaded episodes only feed diagnostic counters, and the README example configs omit the flag as well.
  3. Training steps run one at a time behind a file lock. `train_ap.py` and `train_prefetcher.py` hard-code LightGBM `num_threads=20`, so running them in parallel stalls the CPU. Simulations run in parallel with `OMP_NUM_THREADS` capped per job.
- **Metrics use the artifact's own loader**, `episodic_analysis.exps.results`, which is the same code path the paper notebooks use.

## Layout
```
env.sh              source first; sandboxes all caches/temp dirs
setup/01_env.sh     conda env from the artifact's pinned YAML -> env/ (+ env.lock.txt)
setup/02_data.sh    traces + results_release.csv.gz -> work/data (sha1-checked); --samples10 for samples 0-9
setup/03_work.sh    work/ layout: BCacheSim symlink, notebook copies, runs/ tmp/ logs/ systmp/
repro/make_jobs.py  authors' CSV rows -> work/jobs/{fig9,smoke}.jsonl (self-checks Fig 9 bar values)
repro/run.py        run jobs (parallel, resumable; hard-fails on missing inputs / soft-fail messages)
repro/analyze.py    ours vs authors per job, per Fig 9 bar, pass/fail -> work/results/
repro/stage_a.py    execute the authors' fig-09 / example notebooks (copies) in the sandbox
check_frozen.sh     frozen-tree checksum check
check_no_leak.sh    lists files modified outside this directory since .cache/leak_marker
```

## Run
```bash
cd changes/0_reproduce
bash setup/01_env.sh && bash setup/02_data.sh && bash setup/03_work.sh   # once
source env.sh
touch .cache/leak_marker

$REPRO_PY repro/stage_a.py              # A: authors' Fig 9 notebook on their CSV -> 28.11/31.95/34.63
$REPRO_PY repro/make_jobs.py            # builds 10 fig9 jobs + 2 README smoke jobs
$REPRO_PY repro/run.py smoke -j 2       # 0: README example, Region1 (~35 min)
$REPRO_PY repro/analyze.py smoke        #    expect Baleen saving over RejectX ~16.1%
$REPRO_PY repro/stage_a.py --example    #    the same check through the authors' example.ipynb
$REPRO_PY repro/run.py fig9 -j 10       # B: 10 authors' runs, Region7 + Region6 sample 0
$REPRO_PY repro/analyze.py fig9         #    -> work/results/fig9_summary.md

bash check_no_leak.sh && bash check_frozen.sh
```
- Multi-sample option: `bash setup/02_data.sh --samples10`, then `$REPRO_PY repro/make_jobs.py --set fig9x10 --samples 0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8 0.9`, then `run.py fig9x10`. The results then compare directly against the Fig 9 bars.
- Logs are in `work/logs/<set>/<job>/{train,sim}.log`.
- Job status is in `work/jobs/<set>/<job>.json`. Pass `--force` to rerun a job.
