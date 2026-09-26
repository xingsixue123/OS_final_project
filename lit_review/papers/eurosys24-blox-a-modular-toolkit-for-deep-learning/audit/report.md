# Blox: A Modular Toolkit for Deep Learning Schedulers

Desk review only. Nothing was built or run; every claim below cites a paper section/figure
or a repository path.

## 1. Paper summary

**Problem.** Every recent DL cluster scheduler (Tiresias, Optimus, Gavel, Themis, Pollux,
Synergy) ships its own full stack, so their contributions cannot be compared, composed, or
re-evaluated on a common footing (§1, §2.3). The paper asks: how do these policies compare
on newer traces and at higher load, and what happens when you compose pieces of them?

**Key idea.** Decompose a DL scheduler into seven abstractions — job admission, cluster
management, job scheduling, job placement, job launch, job preemption/restart, metric
collection (Figure 1, Table 1) — with fixed input/output contracts (Table 6, page 12) and
two shared data structures, `ClusterState` (a per-GPU dataframe) and `JobState` (a
per-job dict) (§6.4). A scheduler is then a ~40-line main loop chaining these modules
(Figure 2, page 3). The *same* loop runs in simulation or on a real cluster; only a CLI
flag changes (§3, lines 498–509 of the text).

**Implementation.** ~8000 lines of Python, gRPC between a `CentralScheduler`, a
per-node `WorkerManager`, and a `BloxClientLibrary` linked into training jobs
(§6.3, Figure 17). Preemption uses *optimistic lease renewal*: leases auto-renew unless
revoked, with a two-phase exit-iteration handshake for distributed jobs (§7).

**Evaluation setup.** Simulated cluster of 128 GPUs = 32 servers × 4 × V100 (p3.8xlarge),
round duration 300 s. Three traces: **Philly-Trace** (public Microsoft Philly trace, jobs
3000–4000 tracked, Poisson arrivals with rate λ swept 1→9 jobs/hour), **Pollux-Trace**
(160 jobs, 64 GPUs, load swept to 40 jobs/hour), **Tiresias-Trace** (csv-60). Jobs are
assigned one of 7 DNNs from Table 2 (ResNet-18/50, CycleGAN, LSTM, Recoder, Transformer,
A3C) with per-iteration profiles (§4 "Workloads").

**Headline numbers.**
- Fidelity of re-implementations: Pollux within 2.4% of the authors' implementation
  (Figure 3), Tiresias JCT CDF matches the open-source simulator (Figure 4), Synergy
  matches Figure 9(b) of the Synergy paper (Figure 5).
- Implementation cost: 12–1157 LOC per scheduler over a FIFO baseline (Table 3, Table 7).
- **Figure 6 / Figure 7 (page 6):** FIFO vs Tiresias vs Optimus on Philly-Trace, 1→9
  jobs/hour. At low load Optimus wins JCT; above ~7 jobs/hour Tiresias has *higher* JCT
  than FIFO ("causes long running jobs to suffer a large number of preemptions"), while
  keeping the best responsiveness. FIFO has the worst responsiveness.
- **Figures 8/9:** Pollux beats FIFO/LAS under 15 jobs/hour but degrades to FIFO-like
  behaviour above 20 jobs/hour.
- **Figures 10/11 (§4.3):** on a V100/10 Gbps cluster, blanket consolidation beats the
  Tiresias skew heuristic above 4 jobs/hour; an oracle profile-based policy (Tiresias+)
  widens its lead as more workloads become placement-sensitive.
- **Figures 12/13 (§5.1, page 9):** composing FIFO admission control with LAS trades
  responsiveness for JCT — 15% JCT improvement at Accept-1.2×, 27.3% under a bursty trace.
- **Figures 14/15 (§5.2):** an Automatic Scheduler Synthesizer that re-simulates all
  policy combinations and switches at runtime matches the best static policy on both traces.
- **§5.3:** loss-based termination cuts avg JCT ~44% (Figure 16); bandwidth-aware
  intra-node placement raises observed bandwidth 1.47× (Table 4).
- **§7:** simulator vs 32-GPU AWS cluster: per-job JCT differs by 6.1% on average
  (Figure 18, page 12); optimistic lease renewal is >50% faster and flat in cluster size
  where centralized renewal grows (Figure 19).

**Stated limitations** (§8): simulation ignores hardware variability, disk loading, and
resource contention; Blox only supports round-based centralized scheduling (churn-based
and distributed/hybrid designs are "left to the future"); decomposition can be suboptimal
when scheduling and placement must be decided jointly; the synthesizer should eventually
use "a learning based approach" instead of brute-force simulation (§5.2 last paragraph).

## 2. Artifact audit

**Repo.** `https://github.com/msr-fiddle/blox`, MIT, 429 files / 47 MB / ~47.9k lines of
Python. Head commit `c8851b2` dated **2024-04-04**; GitHub `pushed_at` 2024-07-04; 47
stars, 6 open issues, not archived. `repo/Readme.md:2` states verbatim that it "contains
the source code implementation of the Eurosys 2024 paper 'Blox: …'" and that it is part of
Microsoft Research's Project Fiddle; the paper's abstract and §1 link the same URL.

### Structure and paper → code map

| Paper component | Code path |
|---|---|
| Scheduling loop (Figure 2) | `las_scheduler.py:90-160`, `blox_examples/blox_new_flow_multi_run.py:15-121` |
| `BloxManager` / CentralScheduler (§6.3) | `blox/blox_manager.py` |
| `ClusterState` (§6.4) | `blox/cluster_state.py` |
| `JobState` (§6.4) | `blox/job_state.py` |
| Job Admission abstraction | `admission_control/admission_policy.py`, `accept_all.py`, `load_based_accept.py` (the Accept-1.2×/1.4× policy of Figures 12–14) |
| Job Scheduling abstraction | `schedulers/scheduler_policy.py` + `fifo.py`, `las.py`, `srtf.py`, `optimus.py`, `tiresias.py`, `gavel.py`, `proportional.py` (Synergy-Proportional), `policy.py` |
| Job Placement abstraction | `placement/placement_policy.py`, `placement/placement.py` (the live one), `consolidated_placement.py`, `synergy_placement.py`, `bebop.py`, `first-gpu.py`, `placement_inference.py` |
| Metric collection / simulated job progress | `blox/deployment/grpc_client_rm.py:168-297` |
| Simulator driver (Figures 6/7, 12/13, 14/15) | `simulator_runner/simulator.py`, `simulator_simple.py`, `simulator_acceptance_policy.py`, `simulator_dual_load.py`, `simulator_dual_load_small_large.py` |
| Automatic Scheduler Synthesizer (§5.2) | `blox_examples/blox_new_flow_dynamic_policy.py` + `simulator_runner/predict_simulation.py` |
| Workload generation / Philly parsing / model zoo | `workload/workload.py`, `workload/parse_philly_jobs.py`, `workload/model_zoo.py`, `workload/model.py`, `workload/models/*.py` |
| WorkerManager (§6.3) | `node_manager.py`, `blox/deployment/grpc_server_nm.py`, `blox/deployment/node_data_relay.py` |
| `BloxClientLibrary` / lease-based preemption (§7) | `blox_enumerator.py`, `applications/blox_enumerator.py`, `blox/deployment/grpc_client_blox_iterator.py` |
| gRPC contracts | `blox/deployment/grpc_proto/{rm,nm,simulator,frontend,backend}.proto`, `blox/deployment/Makefile` |

**Components described in the paper but NOT in the repo.** Grepping the whole tree for
`pollux|themis` finds exactly one hit — a comment in `schedulers/optimus.py:31`. There is
no Pollux scheduler, no Themis finish-time-fairness scheduler, and no Synergy-Tune
scheduling policy, despite Table 3/Table 7 listing 1157 / 745 / 1137 LOC for them and
Figures 3, 5, 8 and 9 depending on them. `schedulers/__init__.py` exports only
`fifo, las, srtf, optimus, tiresias` — `gavel.py` and `proportional.py` are present but
not exported and not selectable from any driver. Likewise there is no Tiresias *placement*
policy (§4.3, Figures 10/11) anywhere in `placement/`.

### Build route on this machine

Simulation mode is pure Python and needs no root. Concretely:

1. `conda create -n blox python=3.10` — Python 3.12 will not work: `blox/cluster_state.py:89`
   calls `self.gpu_df.append(...)`, removed in pandas 2.0, so pandas must be < 2.0, and the
   README pin is `pandas==1.3.0` (`Readme.md:96`, a 2021 release with no 3.11/3.12 wheels).
2. `pip install grpcio grpcio-tools "protobuf<5" "pandas<2" numpy matplotlib`.
   protobuf must stay < 5 because `blox/deployment/grpc_server_rm.py:42` passes
   `including_default_value_fields=True` to `MessageToDict`, a kwarg removed in protobuf 5.
3. `mkdir blox/deployment/grpc_stubs && touch blox/deployment/grpc_stubs/__init__.py`
   then `make -C blox/deployment grpc`. The stubs are deliberately not committed
   (`.gitignore:7` = `*pb2*.py`) and the Makefile writes into a directory that does not
   exist in the clone.
4. Fix the stub import path. The code uses two incompatible styles:
   `simulator_simple.py:20` does `from blox.deployment.grpc_stubs import rm_pb2` while
   `blox/deployment/grpc_server_rm.py:18` does a bare `import rm_pb2` after
   `sys.path.append(.../grpc_stubs)`; `blox/deployment/grpc_client_rm.py:10` appends
   `os.path.join((__file__), "./grpc_stubs")`, which is not a directory at all. Easiest fix
   is `PYTHONPATH=$PWD:$PWD/blox/deployment/grpc_stubs`.
5. Run the two processes from the repo root (the README's commands assume a flat layout that
   no longer exists — `simulator.py` lives in `simulator_runner/`, `blox_new_flow_multi_run.py`
   in `blox_examples/`, and `blox_examples/blox_new_flow_dynamic_policy.py:12` imports
   `predict_simulation` as a top-level module although it sits in `simulator_runner/`).

No Docker is needed. The 42 `docker` grep hits and all 3 `sudo` hits in `repo_facts.json`
are inside `workload_synergy/models/**` — vendored NVIDIA DeepLearningExamples READMEs for
BERT/GNMT/DeepSpeech that are only used if you run real training jobs on a real cluster.
`redis` (`blox/deployment/node_data_relay.py:3`) and `numa`
(`blox/deployment/grpc_client_nm.py:5`) are imported only by the WorkerManager path
(`node_manager.py`); `blox/deployment/__init__.py` is empty, so `import blox` does not pull
them in and simulation never touches them.

### Data, traces, models

- **Philly-Trace**: not bundled. `workload/parse_philly_jobs.py:14,33` names the source —
  `https://github.com/msr-fiddle/philly-traces` — which is public and ships
  `cluster_job_log` inside a ~1 GB `trace-data.tar.gz` (6.6 GB uncompressed). Fits in the
  ~257 GB free. `workload/workload.py:102-150` parses it once and caches to
  `philly_jobs_*.pickle` (also gitignored).
- **Model profiles**: hardcoded in the repo, no download needed.
  `workload/model_zoo.py:190-196` defines the zoo (alexnet, res18, res50, mobilenet,
  shufflenet / gnmt, transformer, lstm / deepspeech) and each profile is a Python class,
  e.g. `workload/models/res18_1.py:11-29` gives `iter_time=0.64`, `speedup=2.4`,
  `placement_penalty=1` and a 9×4 throughput matrix.
- **Pollux-Trace and Tiresias-Trace**: not in the repo and no loader for them
  (`Workload.populate_from_trace` at `workload/workload.py:90` references `self.trace`,
  which is never assigned in `__init__`). Both upstream traces are public, but the parser
  work is on you.

### Evaluation scripts present / absent

- Present and matching the paper: `simulator_runner/simulator.py:430-445` hardcodes exactly
  the Figure 6/7 sweep — schedulers `["Tiresias","Optimus","Fifo"]`, loads
  `np.arange(1,10,1.0)`, 32 machines × 4 GPUs, tracking jobs 3000–4000 — and
  `blox_examples/blox_new_flow_multi_run.py:63-78` dispatches those three plus Las/Srtf.
  `simulator_runner/simulator_acceptance_policy.py` and `simulator_dual_load.py` cover
  Figures 12/13; `blox_new_flow_dynamic_policy.py` covers Figures 14/15.
  `Readme_figure.md` gives per-figure commands.
- Absent or broken: no plotting script produces Figure 6 as published. The in-repo plotter
  `simulator_simple.py:182-287` reads filenames of the form
  `{prefix}_{lo}_{hi}_{sched}_load_{load}_job_stats.json`, but `blox/blox_manager.py:253`
  writes `..._{sched}_{acceptance_policy}_load_{load}_job_stats.json` — the names do not
  match — and line 281 references an undefined `free_gpu`. Avg JCT is, however, printed to
  stdout (`blox/blox_manager.py:258-260`), so re-plotting from the JSON is easy.

### Code-quality findings that matter for reproduction

- `blox/deployment/grpc_client_rm.py:265-272` reads `self.optimus_scale_by_gpus`, but that
  dict is commented out at lines 232-243 — running the **Optimus** scheduler in simulation
  will raise `AttributeError` as released. The values are recoverable from the comment.
- `blox/deployment/grpc_client_rm.py:105` = `# TODO: Add time for checkpoint and restore`.
  The simulated progress function (lines 251-295) advances a job by
  `round_duration / job_iteration_time` and charges **no** launch, checkpoint or restore
  cost, despite §7 claiming "We ensure that the simulator can capture the job launch and
  preemption overheads".
- The same function ignores placement: `placement_penalty` is loaded into the model
  (`workload/model.py:178`) and copied onto the job (`workload/workload.py:190`) but never
  divides iteration time on the simulator path. Symmetrically, `placement_preference` is
  only ever *read* (`placement/placement.py:70,162`), never written by `workload/`, so
  `job.get("placement_preference") == "consolidated"` is always False and every job is
  placed scattered.
- `placement/placement.py:242` assigns to `node_with_min_moRE_gpUs` (typo) instead of
  `node_with_min_more_GPUs`, so the "node with more GPUs than needed" fallback in
  `_consolidated_placement` is dead code.
- `schedulers/tiresias.py:42-52` builds the multi-queue discretized-LAS order into
  `combine_across_all_list` and then discards it; `schedule_info["job_order"]` is the plain
  LAS sort, and the class defaults to `num_queus=1`. As released, Tiresias ≡ LAS.
- `placement/placement.py:137,142` (the Gavel branch) reference undefined names `jid` and
  `jobs_to_launch`; `placement/consolidated.py` uses `pd` and `find_free_GPUs` without
  importing them. Neither is on the default path.
- Three near-duplicate workload trees exist (`workload/`, `jobs/`, `helpers/`); only
  `workload/` is imported by the simulators (`simulator_simple.py:7`).
- `blox/utils.py` defines `prune_jobs_based_on_runtime` and `remove_post_termination`
  twice each (lines 20/85 and 12/194).
- `simulator_runner/predict_simulation.py` ignores its `rounds_to_simulate` argument and
  instead drains **all** active jobs to completion (lines 112-218) for every policy
  combination, and `blox_examples/blox_new_flow_dynamic_policy.py:107` calls it every round
  (`if round_number % 1 == 0`), not every ten rounds as §5.2 states.

None of these is a blocker; together they are the reason reproduction is rated M, not H.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | `https://github.com/msr-fiddle/blox`, linked from the paper abstract and §1 and from `repo/Readme.md:2` ("source code implementation of the Eurosys 2024 paper… Microsoft Research's Project Fiddle"); `msr-fiddle` is the authors' org (Amar Phanishayee, MSR). Contains the real system, not a stub: `blox/blox_manager.py`, `blox/cluster_state.py`, `blox/job_state.py`, `schedulers/`, `placement/`, `admission_control/`, `workload/`, `simulator_runner/` — ~47.9k lines of Python. Caveat noted in §2: the Pollux/Themis/Synergy-Tune scheduling policies of Table 3 are not in the release. |
| `H2_no_root` | **pass** | Simulation is two Python processes talking over localhost gRPC (`simulator_runner/simulator.py:446`, `blox/blox_manager.py:44-47`); no kernel module, eBPF, perf counter, KVM, `/proc/sys` write or hugepage anywhere on that path. `blox/deployment/__init__.py` is empty so `import blox` does not pull in `numa`/`redis`. The `sudo`/`docker` red flags are confined to vendored NVIDIA example READMEs under `workload_synergy/models/**` (e.g. `workload_synergy/models/deepspeech.pytorch/README.md:12`) and are not needed. `node_manager.py` reads `/proc/meminfo` and `/proc/driver/nvidia` read-only (`blox/deployment/grpc_client_nm.py:68,95`) — and is only used in cluster mode. |
| `H3_hardware_fit` | **pass** | The headline results (Figures 6, 7, 10–16) are *all* simulations (§4: "all our experiments in this section are simulations"). The 128-GPU cluster exists only as rows in a pandas dataframe (`simulator_simple.py:357-378` registers `number_of_machines=32, gpus_per_machine=4` over gRPC). Cost is CPU + RAM only; 16 cores / 125 GB is ample, and `--simulator-rpc-port` (`Readme.md:141-159`) lets many configs run concurrently. Concern to note: the real-cluster results — Figure 18 (32 GPUs on 8× p3.8xlarge, §7) and Figure 19 (lease renewal swept to 256 GPUs) — cannot be reproduced on one A5000 and have no meaningful single-GPU scale-down; they are not the paper's headline, but any add-on that needs them is out of scope. |
| `H4_obtainable_deps_data` | **pass** | Deps are 5 pip packages, all user-space (`Readme.md:93-98`): grpcio, grpcio-tools, matplotlib, pandas, numpy — with the pins discussed in §2 (pandas < 2, protobuf < 5, Python ≤ 3.10 via conda). The only external data is the Philly `cluster_job_log`, publicly downloadable from `https://github.com/msr-fiddle/philly-traces` as named in `workload/parse_philly_jobs.py:14,33` (~1 GB compressed, 6.6 GB extracted; fits the ~257 GB free). Model/iteration-time profiles are committed as Python (`workload/models/res18_1.py`). No proprietary trace is required for the target figure. Pollux-Trace and Tiresias-Trace are public but have no loader in the repo. |

No `fail`, no `unclear`.

## 4. Reproduction plan

**Target.** **Figure 6** (page 6): average JCT of FIFO vs Tiresias vs Optimus on
Philly-Trace at 1→9 jobs/hour, 128 GPUs. It supports the paper's central "revisiting"
claim — that at high load Tiresias's responsiveness advantage costs it JCT relative to
FIFO. **Figure 7** (responsiveness) falls out of the same run, since
`blox/blox_manager.py:277-288` writes the responsiveness JSON alongside the JCT JSON.

**Why this target.** It is the only headline figure whose full driver is committed and
hardcoded: `simulator_runner/simulator.py:430-445` already encodes the exact scheduler list,
load sweep, cluster shape and tracked job range, and `Readme_figure.md:4-16` gives the
command pair.

**Scale-down.**
- Loads `{1,3,5,7,9}` instead of `{1..9}` — 15 configs instead of 27; the crossover the
  paper claims lives between 4 and 8 jobs/hour, so add 6 and 8 if the curves look close.
- Track jobs 3000–3200 (`--start-job-track/--end-job-track`) instead of 3000–4000 for a
  first pass; the simulation terminates when all tracked jobs finish
  (`blox/blox_manager.py:251`), so this is the main runtime knob. Widen to 3000–4000 for
  the final numbers.
- Run 8–12 configs concurrently on distinct ports (`--simulator-rpc-port`,
  `Readme.md:141-159`); each config is a single-threaded Python pair, and 16 cores are free.
- Cluster size stays at 32×4 = 128 GPUs — there is no reason to shrink it, and shrinking it
  would change the claim.

**Step list.**
1. conda env with Python 3.10; pip install grpcio, grpcio-tools, `protobuf<5`, `pandas<2`,
   numpy, matplotlib.
2. `mkdir blox/deployment/grpc_stubs`, add `__init__.py`, `make -C blox/deployment grpc`,
   set `PYTHONPATH=$PWD:$PWD/blox/deployment/grpc_stubs`.
3. Download and extract `trace-data.tar.gz` from `msr-fiddle/philly-traces`; point
   `--cluster-job-log` at `cluster_job_log`.
4. Restore `self.optimus_scale_by_gpus` in `blox/deployment/grpc_client_rm.py` from the
   commented block at lines 232-243, otherwise the Optimus sweep dies at line 268.
5. Smoke test with `simulator_simple.py` + `las_scheduler.py` at load 1 and a 20-job
   tracking window; confirm a `*_job_stats.json` is written and an "Avg JCT" line is printed.
6. Run `simulator_runner/simulator.py` + `blox_examples/blox_new_flow_multi_run.py` for the
   reduced sweep, from the repo root.
7. Re-plot from the emitted `*_job_stats.json` / `*_responsivness.json` with a ~30-line
   script (the bundled plotter's filename convention does not match what the manager writes,
   see §2).
8. Compare shape and crossover point against Figure 6/7. Expect the Tiresias curve to look
   like LAS, because `schedulers/tiresias.py` discards its queue logic — record this as a
   finding rather than a failure.

**Effort estimate.** ~6–9 person-days of porting and debugging (dominated by steps 2, 4, 7
and by chasing the duplicate-module / import-path layout), plus ~60–120 CPU-hours of
simulation — the README itself budgets "around 8hrs" for one full Figure-6 sweep
(`Readme.md:110`), and we would run several. **0 GPU-hours.**

**Level: M.** The exact driver, sweep and commands exist, which argues for H; but the gRPC
stubs are not generated, the README's paths no longer match the tree, three dependency pins
(Python/pandas/protobuf) are stale, one of the three target schedulers crashes as released,
the plotting path is broken, and the trace must be fetched and parsed separately. That is
"reproducible with real porting work" — M, not H. No artifact badge was found to raise
confidence.

## 5. Add-on ideas

### A1. Preemption-cost-aware simulation, and whether the paper's high-load conclusions survive

- **Hypothesis.** We hypothesize that charging a per-job checkpoint/restore cost on every
  preemption in Blox's simulated progress model changes the FIFO / LAS / Tiresias / Optimus
  ranking on average JCT — and specifically narrows or reverses the paper's reported
  Tiresias-worse-than-FIFO crossover — at loads ≥ 6 jobs/hour on Philly-Trace, with the
  effect scaling in checkpoint size and shrinking in round duration.
- **Mechanism.** Replace the simulated metric path so that a job that was suspended in the
  previous round loses `c(model, num_GPUs)` seconds of the next round before making
  progress. `blox/blox_manager.py:354` already sets `active_jobs[jid]["suspended"] = 1` on
  preemption and `:386` clears it on relaunch, so the signal is there; the progress update
  in `blox/deployment/grpc_client_rm.py:251-264` just has to consume it. Add
  `ckpt_save_s` / `ckpt_restore_s` fields to the profile classes under `workload/models/`
  and thread them through `workload/workload.py`. Measure real values for the zoo's models
  on the local A5000 (torch.save/load of the state dict + dataloader warm-up) to anchor the
  sweep, then sweep 0–120 s. Report avg JCT, responsiveness, *and* the preemption count
  already logged via `utils.collect_custom_metrics(..., {"num_preemptions": ...})`
  (`blox_examples/blox_new_flow_multi_run.py:112-114`). Mirror the change into
  `simulator_runner/predict_simulation.py:136-177` so the synthesizer's lookahead stays
  consistent.
- **Code locations.** `blox/deployment/grpc_client_rm.py`, `blox/blox_manager.py`,
  `blox/job_state.py`, `workload/models/model_stats.py`, `workload/workload.py`,
  `simulator_runner/predict_simulation.py`
- **Motivating evidence.** `blox/deployment/grpc_client_rm.py:105` is literally
  `# TODO: Add time for checkpoint and restore`, and the simulation branch (lines 251-295)
  charges nothing — yet §7 claims "We ensure that the simulator can capture the job launch
  and preemption overheads and profile these overheads for the models we use (Table 2)" and
  reports 6.1% mean JCT error against a real cluster (Figure 18). Crucially, §4.2's
  explanation of the Figure 6 crossover is *entirely about preemption cost*: Tiresias
  "causes long running jobs to suffer a large number of preemptions thus having longer
  average JCT at high load". If preemption is free in the model, that mechanism cannot be
  what produces the curve, and the stated causal story is untested. §8 ("Limitations of
  Simulation in Scheduling Research") concedes the gap.
- **Feasibility: H.** Localized — a few hundred LOC across two files plus profile fields.
  Reuses the existing sweep driver and the existing metrics JSON. Pure CPU for the sweep;
  the checkpoint profiling is minutes of single-GPU work on the A5000. Comfortably inside
  10 weeks for 2–4 students.
- **Research value: H.** Blox's entire pitch is that it puts prior schedulers on a common,
  faithful footing; showing that the released simulator omits the exact cost that the
  paper's main comparative claim is attributed to is a result a EuroSys reviewer would care
  about. Both outcomes teach something: if the crossover survives, the paper's conclusion is
  strengthened and now rests on a modelled mechanism; if it moves, several of §4.2, §5.1 and
  §5.2's takeaways (including the 15%/27.3% admission-control gains, which are gains from
  *reducing preemptions*) need restating. The round-duration × checkpoint-cost plane is also
  a regime the paper never explores.
- **Scoop check.** Queries: *"papers citing Blox EuroSys 2024 deep learning scheduler
  simulator preemption overhead fidelity 2025"*; *"GPU cluster scheduling simulator fidelity
  checkpoint preemption overhead modeling job completion time 2025 2026"*.
  Result: **partial.** Injecting a restart penalty is standard practice in *other*
  simulators — [Pollux](https://arxiv.org/pdf/2008.12260) injects a fixed 30 s
  checkpoint-restart delay per reallocation, and
  [Lucid/WiseShare](https://arxiv.org/pdf/2407.13088) validate simulators to within ~5% of
  testbeds. Citing work found ([PAL](https://arxiv.org/pdf/2408.11919), WiseShare) cites
  Blox but does not audit its progress model. No work found that re-derives Blox's own
  conclusions under a preemption-cost model.

### A2. Make placement actually matter: placement-sensitive progress + the missing Tiresias placement policy

- **Hypothesis.** We hypothesize that (i) applying the per-model `placement_penalty` already
  present in Blox's model zoo to simulated iteration time and (ii) implementing the Tiresias
  skew-based placement policy plus an oracle "Tiresias+" policy reproduces the qualitative
  conclusion of Figures 10 and 11 — consolidation wins at high load on fast-GPU/slow-network
  clusters, and the oracle's lead grows with the fraction of placement-sensitive jobs — and
  we hypothesize the magnitude of the gap is materially smaller than published once
  fragmentation feedback is modelled.
- **Mechanism.** Set `job["placement_preference"]` in the workload generator from
  `Model.placement_penalty`; divide simulated iteration time by the penalty when a job's
  assigned GPUs span more than one node (the node mapping is available from
  `cluster_state.gpu_df`); add `TiresiasPlacement` (skew heuristic over the profile) and
  `OraclePlacement` classes next to `JobPlacement`; wire a `--placement-name` switch in the
  drivers, which currently hard-fail on anything but `"Place"`
  (`blox_examples/blox_new_flow_multi_run.py:46-51`). Fix the dead consolidation fallback at
  `placement/placement.py:242` as part of the change. Sweep the placement-sensitive
  workload fraction 5/8 → 8/8 as in Figure 11.
- **Code locations.** `placement/placement.py`, `placement/placement_policy.py`,
  `workload/workload.py`, `workload/model.py`,
  `blox/deployment/grpc_client_rm.py`, `blox_examples/blox_new_flow_multi_run.py`
- **Motivating evidence.** `placement_preference` is read at `placement/placement.py:70,162`
  (and in `first-gpu.py:81,173`, `bebop.py:63`) but a grep of `workload/` shows it is never
  written, so `place_consolidated` is always False and every job takes the scattered path.
  `placement_penalty` is loaded (`workload/model.py:178`) and attached to the job
  (`workload/workload.py:190`) but never reaches the simulated progress computation
  (`blox/deployment/grpc_client_rm.py:251-264`). And `placement/placement.py:242` assigns to
  a misspelled variable, disabling the only non-exact-match consolidation path. Net effect:
  §4.3's entire case study — "placement policies need to be guided by profiles on specific
  hardware rather than fixed heuristics" — has no reproducible code behind it.
- **Feasibility: H.** Self-contained, well under 1k LOC, evaluated with the existing sweep on
  CPU only. The hardest part is deciding a defensible slowdown model for a >1-node job, and
  the profiles already supply the constant.
- **Research value: M.** It repairs and re-tests a published figure rather than opening new
  ground, and "consolidation helps when the network is the bottleneck" is not a surprising
  headline. It is valuable as a correctness contribution and as necessary scaffolding for
  any placement-related follow-up, but a reviewer would call it expected.
- **Scoop check.** Queries: *"GPU cluster scheduling network-sensitive placement consolidation
  Tiresias skew heuristic re-evaluation"*; *"Blox scheduler toolkit extension new policy 2025"*.
  Result: **partial.** Placement/network sensitivity is a well-worked area
  ([GPU Cluster Scheduling for Network-Sensitive Deep Learning](https://arxiv.org/html/2401.16492v1),
  [WiseShare](https://arxiv.org/html/2407.13088v1)), so the *idea* is not novel; but no
  follow-up was found that supplies the missing placement machinery in the Blox artifact or
  re-derives Figures 10/11.

### A3. Replace the brute-force Automatic Scheduler Synthesizer with cheap online policy selection

- **Hypothesis.** We hypothesize that a contextual-bandit selector driven by cheap
  cluster-state features gets within a few percent of the average JCT achieved by Blox's
  exhaustive simulate-every-combination synthesizer while reducing per-round selection cost
  by more than an order of magnitude, and that the advantage grows as the policy portfolio
  is scaled beyond the paper's 9 combinations.
- **Mechanism.** Keep the outer loop of `blox_new_flow_dynamic_policy.py` and swap the
  oracle. Featurize the round (queue length, GPU demand / supply ratio, arrival rate over a
  sliding window, short-job fraction, preemptions last round — all already in
  `cluster_state.cluster_stats` and `job_state.custom_metrics`). Implement (a) a
  Thompson-sampling / UCB bandit over policy combinations with delayed JCT-based reward,
  (b) an ε-greedy baseline, (c) the paper's exhaustive lookahead as the upper-bound baseline,
  and (d) a "best static policy" lower bound. Instrument wall-clock per selection. Scale the
  portfolio from 9 to 25+ combinations by adding Srtf/Optimus/Tiresias × more admission
  thresholds. Also report the paper's intended every-ten-rounds cadence, which the code does
  not implement.
- **Code locations.** `simulator_runner/predict_simulation.py`,
  `blox_examples/blox_new_flow_dynamic_policy.py`, `schedulers/__init__.py`,
  `admission_control/load_based_accept.py`, `blox/job_state.py`
- **Motivating evidence.** §5.2 ends with the authors' own future work: "rather than using
  simulation use a learning based approach to determine the policies to choose." The
  released oracle is far more expensive than §5.2 describes: it takes
  `rounds_to_simulate` as an argument and ignores it, instead looping
  `while True: … if len(job_state.active_jobs) == 0: break`
  (`simulator_runner/predict_simulation.py:112-218`) — i.e. it drains *all* active jobs to
  completion for each of the `itertools.product` combinations (lines 31-48), deep-copying
  `ClusterState` and `JobState` each time (lines 38-48) — and
  `blox_examples/blox_new_flow_dynamic_policy.py:107` fires it every round
  (`if round_number % 1 == 0`), not every ten. The paper reports the synthesizer's *quality*
  (Figures 14, 15, 20, 21) but never its cost, which is precisely the axis that decides
  whether the idea is deployable.
- **Feasibility: M.** The selector itself is small, but honest evaluation needs a new harness:
  portfolio-scaling experiments, per-round cost instrumentation, multiple traces (including
  the bursty derivative of §5.2), and repeated seeds because bandits are stochastic. All CPU,
  but a lot of runs.
- **Research value: H.** It is the paper's own named next step, it attacks a cost the paper
  never measured, and the portfolio-scaling regime is where a modular toolkit's
  "just compose more policies" promise either holds or breaks. A negative result — that the
  bandit cannot track a fast-changing trace and exhaustive lookahead is irreplaceable — would
  be just as publishable a finding about the synthesizer's premise.
- **Scoop check.** Queries: *"automatic scheduler policy selection bandit reinforcement
  learning switching scheduling policies GPU cluster online 2025"*; *"Blox scheduler toolkit
  extension new policy 2025"*. Result: **partial.** There is a lot of 2025 RL-for-GPU-scheduling
  work — [RLTune / hybrid learning-optimization dynamic scheduling (SoCC '25)](https://dl.acm.org/doi/10.1145/3772052.3772257),
  [defragmentation scheduling with DRL (SoCC '25)](https://doi.org/10.1145/3772052.3772242),
  [network-contention-aware RL scheduling](https://arxiv.org/pdf/2310.20209) — but these
  *learn a scheduling policy*, not *select among existing policy compositions* at runtime,
  and none builds on or replaces Blox's synthesizer. Closest in spirit but not the same.

### A4. Re-evaluate the schedulers under a transformer / LLM-fine-tuning workload mix

- **Hypothesis.** We hypothesize that replacing Blox's CNN/RNN-era model zoo with profiles
  measured from transformer fine-tuning jobs — which have longer and more uniform iteration
  times and far larger checkpoints — changes the JCT-vs-responsiveness ordering of
  FIFO / LAS / Tiresias / Optimus at a fixed load on Philly-Trace, and in particular erodes
  the benefit of preemption-heavy policies relative to Figure 6.
- **Mechanism.** Profile 3–4 transformer fine-tuning workloads that fit 24 GB (e.g. BERT-base,
  GPT-2 small/medium, a 7B LoRA run, ViT) on the A5000: per-iteration time at the batch sizes
  the zoo uses, GPU memory, checkpoint save/load time and size. Add them as `ModelStats`
  subclasses in `workload/models/` following the `res18_1.py` template, extend
  `create_default_models` / the task split in `workload/model_zoo.py`, and sweep the
  transformer fraction from 0% to 100% via the existing `model_class_split` knob
  (`simulator_simple.py:40`, `workload/workload.py:70-75`). Re-run the Figure 6/7 sweep. Pairs
  naturally with A1, which supplies the checkpoint-cost channel.
- **Code locations.** `workload/models/model_stats.py`, `workload/model_zoo.py`,
  `workload/model.py`, `workload/workload.py`, `simulator_runner/simulator.py`
- **Motivating evidence.** §1 and §2.2 make workload evolution the paper's own motivation —
  "popular DNN architectures evolve from CNNs to RNNs to Transformer-based models… it becomes
  necessary to re-evaluate scheduler efficacy" — yet Table 2's zoo stops at
  ResNet/LSTM/CycleGAN/A3C and the released zoo is the same
  (`workload/model_zoo.py:190-196`). The multi-GPU scaling numbers are hardcoded constants
  (`workload/models/res18_1.py:19-29`), i.e. the toolkit never actually exercised the
  transformer regime it argues for.
- **Feasibility: M.** Profiling is cheap in GPU-hours and fits one A5000 for 1-GPU jobs, and
  the simulation is CPU-only. The honest difficulty is that the zoo's throughput matrices are
  indexed by GPU count up to 16 (`workload/model_zoo.py:181`) and this machine has one GPU,
  so multi-GPU entries must be extrapolated (or restricted to single-GPU jobs via the
  `multigpu=False` path) and that limitation stated plainly in the write-up.
- **Research value: M.** A well-motivated re-evaluation that the paper invites, and the
  outcome is not fully predictable. But it produces new numbers for an existing system rather
  than a new mechanism, and a reviewer may read "modern models change the ranking" as the
  expected answer.
- **Scoop check.** Query: *"re-evaluating DL cluster schedulers Tiresias Optimus on LLM
  fine-tuning workloads trace 2025 2026 GPU scheduling"*. Result: **partial.** Plenty of
  2025–26 LLM-serving and LLM-training scheduling work exists, and
  [Saturn](https://arxiv.org/pdf/2309.01226) targets large-model training workloads, but no
  paper was found that re-runs the classic FIFO/LAS/Tiresias/Optimus comparison under a
  transformer-era workload mix on a common trace.

### A5. An in-process, event-driven simulator core for Blox

- **Hypothesis.** We hypothesize that replacing Blox's two-process gRPC round loop with an
  in-process, event-driven core — one that advances simulated time to the next arrival,
  completion or lease expiry instead of ticking every 300 s — reduces wall-clock per
  simulated experiment by more than 10× while keeping per-job JCT within 1% of the current
  simulator, without changing any scheduling/placement/admission module.
- **Mechanism.** Add a `--simulate` shim that substitutes direct method calls for
  `BloxManager.rmserver` and `comm_node_manager` so no socket is touched; replace the fixed
  `simulator_time += args.round_duration` advance with an event queue; keep
  `schedule()`/`place()`/`accept()` signatures byte-identical so the existing policy modules
  are unmodified (this is the real test of whether Blox's abstraction boundary is as clean as
  §6.2 claims). Also remove the per-round `copy.deepcopy` of `ClusterState`/`JobState` in the
  placement wrapper behind a flag. Validate by running the Figure 6 sweep on both cores and
  comparing JCT CDFs.
- **Code locations.** `blox/blox_manager.py`, `blox/deployment/grpc_client_rm.py`,
  `blox/deployment/grpc_server_rm.py`, `simulator_runner/simulator.py`,
  `blox_examples/blox_new_flow_multi_run.py`, `placement/placement.py`
- **Motivating evidence.** `Readme.md:110`: "The above experiment will take around 8hrs to
  run" — for one figure. Every round crosses two gRPC hops
  (`blox/blox_manager.py:87,125`, `simulator_simple.py:125-167`) and deep-copies the whole
  cluster and schedule (`placement/placement.py:14-22`). §8 explicitly leaves churn-based
  scheduling to future work: "While our optimistic lease renewal can be used to support
  scheduling policies where the scheduling loop only kicks in on churn, we leave such
  investigation to the future." An event-driven core is the prerequisite for studying that.
- **Feasibility: M.** Cross-cutting: it touches the manager/RPC boundary that every driver
  goes through, and equivalence between the two cores must be demonstrated, not assumed. No
  new hardware, no GPU. Achievable but riskier than A1/A2.
- **Research value: M.** Partly engineering — "make the simulator faster" is not a finding.
  It earns an M because the toolkit is *sold* as a research accelerator, so 8 hours per figure
  is a first-class limitation, and because the event-driven core opens the churn-based
  scheduling question the paper defers. A reviewer would want the churn-based policy study,
  not just the speedup number, so plan to deliver both.
- **Scoop check.** Query: *"event-driven churn-based scheduling versus round-based DL cluster
  scheduler simulator speedup"*. Result: **partial.** Event-driven cluster simulators are
  standard practice and round-based-vs-event-driven trade-offs are discussed in the
  literature (e.g. [ACM Queue on internet-scale cluster schedulers](https://queue.acm.org/detail.cfm?id=3199609),
  [round-based mechanisms for DL training](https://doi.org/10.3390/app14062349)), but nothing
  was found that does this inside Blox or that quantifies the round-based/churn-based JCT
  difference with Blox's abstractions held fixed.

## 6. Risks and open questions

- **The released artifact is a subset of the paper.** Pollux, Themis and Synergy-Tune
  scheduling policies are absent (only comment-level mentions exist; see §2), so Figures 3, 5,
  8 and 9 are not reproducible from this repo. Anyone whose plan depends on Pollux's goodput
  model must budget for reimplementation (the paper itself charges 1157 LOC for it).
- **The released Tiresias is not the paper's Tiresias.** `schedulers/tiresias.py:42-52`
  discards its queue assignment and defaults to one queue, so it behaves as LAS. The Figure 6
  Tiresias curve may therefore not reproduce, and a "faithful discretized 2D-LAS" would have
  to be written first. This is a reproduction risk *and* a possible sixth add-on.
- **Optimus crashes as released** (`blox/deployment/grpc_client_rm.py:268` reads a dict
  commented out at lines 232-243). The fix is mechanical but the commented values are an
  authorial guess we cannot validate.
- **No artifact badge found.** Searches of the ACM DL page and EuroSys '24 materials turned up
  no Artifacts Available / Functional / Reproduced badge; the ACM page returns 403 to
  automated fetch, so this is "not found", not "confirmed absent".
- **Dead and duplicated code.** Three near-copies of the workload tree (`workload/`, `jobs/`,
  `helpers/`), duplicate function definitions in `blox/utils.py`, broken modules in
  `placement/` (`consolidated.py` has missing imports; the Gavel branch of `placement.py`
  references undefined `jid`/`jobs_to_launch`). Expect to spend time deciding which copy is live.
- **Stale pins.** pandas < 2 is forced by `cluster_state.py:89`; protobuf < 5 by
  `grpc_server_rm.py:42`; together they force Python ≤ 3.10 in a conda env, not the system 3.12.
- **Runtime.** ~8 hours per full Figure-6 sweep per the README, 27 configs in the published
  version. Parallelism across ports is the mitigation; the scale-down in §4 is the fallback.
- **Real-cluster claims are out of reach.** Figure 18 (32 GPUs, AWS) and Figure 19 (up to 256
  GPUs) cannot be reproduced on one A5000, and no honest single-GPU scale-down exists for
  them. Any hypothesis about lease-renewal scalability or simulator-vs-cluster fidelity is
  therefore unavailable to this team — which is exactly why A1 targets *internal consistency*
  of the simulator rather than validation against hardware.
- **Multi-GPU profiling gap for A4.** The zoo's throughput matrices span 1–16 GPUs; this
  machine has one. Any new profile's multi-GPU entries are extrapolation and must be labelled
  as such.
- **Determinism.** `simulator_simple.py:90,320` fixes `random.seed(1)` per workload, so runs
  should be repeatable, but the model-assignment path (`workload/model_zoo.py:97-130`) has
  seed-order-sensitive branches — worth verifying early with two identical runs.

## 7. Evidence index

**Paper.** Abstract; §1 (contributions, repo link); §2.1–2.3 (why DL schedulers differ, need
for modularity); §3 + Figure 1 + Figure 2 + Table 1 (abstractions and the scheduling loop);
§4 "Workloads" (Philly/Pollux/Tiresias traces, 128 GPUs = 32 × 4 V100, jobs 3000–4000);
Table 2 (model zoo); Table 3 (LOC per scheduler); §4.1 + Figures 3, 4, 5 (fidelity of
re-implementations); §4.2 + Figures 6, 7 (JCT and responsiveness vs load — **the reproduction
target**, page 6) + Figures 8, 9 (Pollux); §4.3 + Figures 10, 11 (placement policies);
§5.1 + Figures 12, 13 (admission × LAS, page 9); §5.2 + Figures 14, 15 (Automatic Scheduler
Synthesizer, page 9); §5.3 + Figure 16 + Table 4 (loss-based termination, intra-node
placement); §6.1–6.4 + Figure 17 + Tables 5, 6, 7 (design, API, per-scheduler changes,
page 12); §7 + Figures 18, 19 (simulator fidelity 6.1%, lease renewal, page 12);
§8 (experience, simulation limitations, round-based vs churn-based, joint scheduling);
Appendix A + Figures 20, 21; Appendix C (Nexus).
Pages rendered and read: `pages/page-06.png`, `pages/page-09.png`, `pages/page-12.png`.

**Repository (paths relative to `repo/`).**
`Readme.md` (:2 provenance, :66 single-instance/gRPC-ports note, :93-98 dependency pins,
:104-110 artifact run + 8 h estimate, :141-159 parallel runs via `--simulator-rpc-port`,
:160-196 cluster mode / redis / env vars); `Readme_figure.md` (:4-16 Figure 6/7, :18-29
Figures 12/13, :32-57 Figures 14/15); `.gitignore` (:7 `*pb2*.py`); `LICENSE.txt`.
`blox/__init__.py`; `blox/blox_manager.py` (:19-21 imports, :44-47 server launch,
:87 update_cluster, :104-297 update_metrics, :251-296 termination + stats filenames,
:313-418 exec_jobs, :354/:386 suspended flag); `blox/cluster_state.py` (:36-46 gpu_df schema,
:89 `gpu_df.append`); `blox/job_state.py` (:61-100 update_metrics, :102-130 add_new_jobs);
`blox/utils.py` (:20/:85 duplicate defs, :202-264 prune_jobs, :267-300 custom/cluster metrics,
:324-358 write_log_files); `blox/deployment/__init__.py` (empty);
`blox/deployment/grpc_client_rm.py` (:10 broken stub path, :48/:104 sim branches,
:105 checkpoint TODO, :168-297 get_metrics, :232-243 commented `optimus_scale_by_gpus`,
:251-295 simulated progress); `blox/deployment/grpc_server_rm.py` (:15-21 stub imports,
:42 `including_default_value_fields`); `blox/deployment/grpc_client_nm.py` (:5 `import numa`,
:68/:95 `/proc` reads); `blox/deployment/node_data_relay.py` (:3 `import redis`);
`blox/deployment/grpc_server_nm.py` (:120-121 checkpoint TODOs);
`blox/deployment/Makefile` (:1-16 stub generation); `blox/deployment/grpc_proto/*.proto`.
`las_scheduler.py` (:90-160 the Figure-2 loop in real code); `simulator_simple.py`
(:7 workload import, :19-23 stub imports, :40 model_class_split, :90/:320 random seed,
:182-287 plotter incl. :281 undefined `free_gpu`, :315-339 workload construction,
:357-378 cluster registration); `simulator_runner/simulator.py` (:387-421 args,
:430-445 the hardcoded Figure 6/7 sweep); `simulator_runner/simulator_acceptance_policy.py`;
`simulator_runner/simulator_dual_load.py`; `simulator_runner/simulator_dual_load_small_large.py`;
`simulator_runner/predict_simulation.py` (:10-23 signature, :31-48 policy product + deepcopies,
:112-218 drain-to-completion lookahead, :136-177 inner progress model);
`blox_examples/blox_new_flow_multi_run.py` (:15-121 driver, :46-51 placement switch,
:53-78 policy dispatch, :112-114 preemption metric);
`blox_examples/blox_new_flow_dynamic_policy.py` (:12 `predict_simulation` import,
:20-38 policy portfolio, :107 every-round lookahead);
`blox_examples/blox_new_flow_acceptance_policy.py`; `blox_examples/las_scheduler_cluster.py`.
`schedulers/__init__.py` (exports 5 of 7 policies); `schedulers/las.py` (:29-40);
`schedulers/tiresias.py` (:13-53, queues discarded at :42-52); `schedulers/optimus.py` (:31 comment);
`schedulers/gavel.py`; `schedulers/proportional.py`; `schedulers/policy.py`;
`schedulers/scheduler_policy.py`.
`admission_control/__init__.py`; `admission_control/admission_policy.py`;
`admission_control/accept_all.py`; `admission_control/load_based_accept.py` (:32-52 accept,
:55-66 GPU accounting).
`placement/__init__.py`; `placement/placement.py` (:10-24 deepcopy wrapper, :48-142 Gavel branch
incl. undefined `jid`/`jobs_to_launch` at :137/:142, :147-213 default branch, :70/:162
`placement_preference` reads, :215-247 consolidated incl. :242 typo, :249-272 scattered);
`placement/consolidated.py` (missing imports); `placement/consolidated_placement.py`;
`placement/synergy_placement.py`; `placement/bebop.py` (:63); `placement/first-gpu.py` (:81,:173);
`placement/placement_policy.py`; `placement/placement_inference.py`.
`workload/workload.py` (:49-94 workload types, :102-150 Philly parsing + pickle cache,
:182-268 model/profile attachment incl. :190 placement_penalty and :260 iteration time,
:314-451 synthetic fallbacks); `workload/parse_philly_jobs.py` (:14,:33 trace URL and schema,
:45-120 parser); `workload/model_zoo.py` (:97-130 class assignment, :179-187 multi-GPU models,
:189-228 the zoo); `workload/model.py` (:60-70 json profiles, :76-180 score tables,
:167-179 `use_scores_from_tput`); `workload/models/res18_1.py` (:11-29 a profile);
`workload/models/model_stats.py`; `workload/job.py` (:26-62 fields, :164-186 penalty-aware
progress on the *unused* path); `workload/utils.py`; `workload/stats.py`; `workload/task.py`.
`blox_enumerator.py` (:5-15 lease-checking iterator); `applications/blox_enumerator.py`;
`applications/testing_application.py`; `node_manager.py`; `jobs/`, `helpers/` (duplicate trees);
`combined_plots/*.pdf` (committed result plots); `workload_synergy/models/**` (vendored NVIDIA
examples — source of the sudo/docker/infiniband red flags, e.g.
`workload_synergy/models/deepspeech.pytorch/README.md:12`, `models/BERT/README.md:405-408`).

**External.** `https://github.com/msr-fiddle/philly-traces` (public Philly trace,
`cluster_job_log` in `trace-data.tar.gz`, ~1 GB compressed / 6.6 GB extracted — verified by
fetch); GitHub API metadata in `repo_facts.json` (head `c8851b2`, 2024-04-04; 47 stars;
6 open issues; MIT); `fetch_result.json` (PDF from arXiv 2312.12621, repo official "unclear"
before this audit — now resolved to "yes"). Scoop-check sources are linked inline in §5.
