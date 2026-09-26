# Latency-Aware Caching with Delayed Hits: From Bursty Traffic to Pipeline Architectures

NSDI '26 — Nadav Keren, Gil Einziger, Gabriel Scalosub (Ben Gurion University).
Desk review only: nothing was built, installed, or run.

## 1. Paper summary

**Problem.** In heterogeneous storage / cloud settings, miss latencies differ per item, and
misses are not instantaneous. A request arriving for an item that is *already being fetched*
is a **delayed hit**: it costs `f_t(i) + L_i − t`, i.e. between 0 and a full miss
(paper §1.1, p. 4, case 3). Bursty items generate many delayed hits per fetch, so the metric
the paper optimizes is **average request latency (ARL)**, Eq. (1)/(3) on p. 4, not hit ratio.

**Key ideas (five contributions, §1 p. 3).**

1. **LBU (Least Bursty Used)**, §2.3 p. 7 + Appendix A p. 16–17. Each item gets a burstiness
   score `β_i` = max over a sliding window of ℓ *accumulated request latencies* `s(i,t)`
   (Eq. 2, p. 4), i.e. the total latency all requests in `[t, t+L_i]` would pay if `i` were
   missing. Scores decay (`β_i(1−α)` after `A·L_i` idle time). Implementation is a lazily
   maintained min-heap: O(1) admission test against the root, O(log M) on actual eviction,
   heap rebuilt every `δ·M` requests (Appendix A, p. 17).
2. **Pipeline cache architecture** (§3, p. 8–9, Algorithm 1 and Fig. 2): the cache of M items
   is split into m blocks `B_1..B_m` with quota fractions summing to 1. A retrieved item is
   offered to `B_1`; each block's victim is offered to the next block; the last block's victim
   is dropped. Buffers `F_t`/`P_t` (in-flight fetches and pending requests) live in the
   pipeline, not in the blocks.
3. **Adaptive sizing** (§3.1, p. 9–10, Algorithm 2): a fixed-step hill climber. Every
   `10·M` requests it compares `m(m−1)` **ghost caches**, each differing from the live cache
   by moving one quantum (of `κ = 16` quanta, Table 3 p. 11) from one block to another,
   and adopts the best ghost's configuration if its ARL beats the live cache's. Resizing moves
   metadata between blocks rather than evicting. Ghosts can be **sampled** (hash-based, all
   requests of a sampled sub-universe kept) à la MiniSim, so a ghost of size `R·M` sees an `R`
   fraction of requests; with `m=3, R=1/4` the claimed metadata overhead is +75 % and the
   compute overhead 15 % of full ghosts (p. 11).
4. **RFB** = pipeline of `LRU* (CRA)` → `LFU* (access-time-aware TinyLFU)` → `LBU`
   (§4, p. 11–12). `RFB_1` = full ghosts, `RFB_{1/4}` = sampled ghosts, `RF_1` = no LBU block.
5. **Evaluation** (§4, p. 11–13).

**Eval setup.** 13 traces — IBM Object Storage 010/012/024/029/031/034/045 (SNIA), Meta KV
2 and 4, Twitter memcached clusters 1/3/9/28 (Table 3, p. 11; 0.5 M–200 M requests, cache
sizes 512–65 536 entries) — plus a concatenated trace (IBM24, IBM10, IBM12×10, IBM24;
85.3 M requests, size 512). Traces carry no latency, so per-key latency is **synthesised**
from three AWS-site normal distributions (means ≈120/340/675 ms, p. 11), assigned to keys
uniformly at random. Baselines: GDWheel, LAC (Yan-Li), LRU*, LFU*, LHD, Adaptive
CA-W-TinyLFU, ARC, FRD, SIEVE, Hyperbolic, S3-FIFO, LRB (12 policies, Table 4 p. 12).
Everything is a **trace-driven simulation** inside a fork of Caffeine's simulator.

**Headline numbers.**
- Table 4 (p. 12), ARL relative to the best *static* RFB: `RFB_1` is +4.8 % ± 8.5 %,
  `RFB_{1/4}` +5.8 % ± 8.3 %, `RF_1` +7.4 % ± 10.9 %; the best prior art is LRB at
  +14.6 % ± 16.5 %, S3-FIFO +15.6 %, Hyperbolic +19.3 %. That gap is the claimed
  "≈10 % lower ARL than the best state-of-the-art alternative" plus a much smaller STD.
- `RF_1` (+7.4 %) vs Adaptive CA-W-TinyLFU (+29.0 %) — the paper attributes ≈25 % of the
  improvement to the *new hill climber alone* (p. 12, §4.1).
- Table 1 (p. 7): on a synthetic 3-bias workload LRU\*/LFU\*/LBU each win exactly one bias
  (65.6 / 79.3 / 6.6 ms respectively on their own bias, ≥390 ms on the others) — the
  motivation for LBU.
- Table 3 (p. 11): LBU helps a lot on IBM12 (19 % better than RF) and Twi28 (4.4 %), and
  ~0 % on 7 of 13 traces.
- Fig. 3 (p. 13): on the concatenated trace the adaptive pipeline re-allocates quanta within
  a segment boundary and beats the best static pipeline by 4–5.5 points, ≈10 % better than LRB.

**Stated limitations / future work (§5, p. 13).** (i) Integrating RFB into Caffeine proper
and evaluating it on real applications is not done; (ii) "the main technical hurdle is
efficient parallelization, which is not currently addressed in our simulation-based
implementation"; (iii) uniform item size is assumed (§1.2 p. 5–6: slabbing is assumed,
size-aware policies are explicitly out of scope); (iv) fetch latency is estimated by the most
recent observed latency (footnote 1, p. 3) and is drawn i.i.d. per key, independent of load.

## 2. Artifact audit

### Repo structure (`repo/`, 27 files, ~2.5 kLOC Python, head commit 2026-02-18)

```
README.md                      # artifact instructions (748 lines, detailed)
aliases.sh, containers/        # Containerfiles for the two published images
  test-container/Containerfile # Fedora 43 + caffeine fork + this repo
  lhd-lrb/Containerfile        # Ubuntu 18.04 + LRB + LHD (legacy baselines)
trace_processing/              # parse_IBM|twitter|meta.py, latency_appender.py,
                               # latency_generators.py, trace_merger.py,
                               # convert_to_LRB_LHD.py, mark_existing_trace.py,
                               # common_data.py (per-trace RNG seeds),
                               # latency_distributions.json (the paper's latencies)
experiments/                   # run_experiments.py, run_mock_experiments.py,
                               # run_synthetic_experiments.py, synthetic_trace_gen.py,
                               # split_synthetic_results.py, simulatools.py, policies.py,
                               # synthetic_trace_config.json
graph_generators/              # adaptation_graph_gen.py (Figure 3)
```

**Important:** the audited repository is an *orchestration hub*, not the system. The cache
policies themselves live in a second, author-owned repository — a fork of Caffeine —
pinned by tag: `containers/test-container/Containerfile:4-7` clones
`https://github.com/NadavKeren/caffeine.git` and checks out `adaptive-pipeline-v1`;
`README.md:49-53` names all three code repositories (caffeine fork, LHD fork, LRB fork).
I verified by browsing the fork at that tag that
`simulator/src/main/java/.../policy/latency_aware/` exists and that its `pipeline/`
subdirectory contains `PipelinePolicy.java`, `PipelineBlock.java`, `LbuBlock.java`,
`LALruBlock.java`, `LALfuBlock.java`, `SampledHillClimber.java`, `RandomHillClimber.java`,
`MovingAverageBurstEstimator.java`, `FetchStage.java`, and the samplers — i.e. the real
implementation is present and public, just not in this clone.

### Paper component → code path

| paper component | code |
|---|---|
| LBU policy (§2.3, App. A) | fork: `.../latency_aware/pipeline/LbuBlock.java`, `MovingAverageBurstEstimator.java`; configured via `pipeline.burst.*` in `experiments/run_experiments.py:46-50,89-98` |
| LRU\* (CRA) / LFU\* blocks (§1.3) | fork: `LALruBlock.java`, `LALfuBlock.java`; config `pipeline.blocks.N.type = "LA-LRU"/"LA-LFU"`, `decay-factor`, `max-lists` (`run_experiments.py:39-50`) |
| Pipeline + F/P buffers (Alg. 1) | fork: `PipelinePolicy.java`, `PipelineBlock.java`, `FetchStage.java`; policy id `latency-aware.Pipeline` (`experiments/policies.py:14`) |
| Adaptive/sampled hill climber (Alg. 2, Table 2) | fork: `SampledHillClimber.java` + `XXH3Sampler/FarmHashSampler/LongSampler.java`; policy id `latency-aware.SampledHillClimber` (`policies.py:15`); knobs `sampled-hill-climber.sample-order-factor`, `adaption-multiplier` (`run_experiments.py:100-101,239-240`) |
| RFB / RF / single-block configs (§4) | `experiments/run_experiments.py:39-98` (`PIPELINE_CA_SETTINGS_WITHOUT_QUOTA`, `PIPELINE_SETTINGS_WITHOUT_BURST`, `PIPELINE_CA_LRU_ONLY/LFU_ONLY/LBU_ONLY`) |
| Table 4 rows | `run_experiments.py:216` (`run_full_ghost`), `:272` (`run_all_simple`), `:316` (`run_adaptive_CA`), `:322` (`run_other` → Hyperbolic, GDWheel, ARC, FRD, LA-Cache, S3-FIFO, SIEVE) |
| Table 3 "best static RFB/RF" | `run_experiments.py:289` (`run_grid_search`, 153 configs over 16 quanta) |
| LHD / LRB rows of Table 4 | `trace_processing/convert_to_LRB_LHD.py` → `containers/lhd-lrb/run_lhd_lrb.py` → `trace_processing/mark_existing_trace.py` → `experiments/run_mock_experiments.py` (mock policy replays the dump so delayed hits can be scored) |
| Table 1 (synthetic 3×3) | `experiments/synthetic_trace_gen.py` + `synthetic_trace_config.json` + `run_synthetic_experiments.py` + `split_synthetic_results.py` |
| Fig. 3 (adaptation under the hood) | `trace_processing/trace_merger.py` (concat trace) → `run_experiments.py` `should_keep_dump=True` → `graph_generators/adaptation_graph_gen.py` |
| Latency synthesis (§4 "The datasets") | `trace_processing/latency_appender.py`, `latency_generators.py`, `latency_distributions.json` (means 120/340/675, σ 12.16/14/15.2, weights 34/33/33 — matches the paper's three AWS sites), per-trace seeds in `common_data.py` |

### Build route on this machine (no Docker, no root)

The published images cannot be pulled (Docker/Podman are not installed), but the general
container is a 4-step recipe that replays natively — `containers/test-container/Containerfile`:

1. `git clone https://github.com/NadavKeren/caffeine.git && git checkout adaptive-pipeline-v1`
2. `./gradlew compileJava` — the Gradle wrapper downloads Gradle and dependencies into
   `$HOME/.gradle`; JDK 17 and 21 are already on `PATH` (README:61 asks for Java ≥ 11).
3. `pip install xxhash rich pandas pyhocon polars matplotlib numpy` in a conda env
   (README:62). The code needs Python ≥ 3.12 — `latency_appender.py:222-223` uses same-quote
   nesting inside f-strings (PEP 701); README:60 asks for 3.14, which conda-forge can provide.
4. Write `experiments/conf.json` (`{caffeine_root, resources, output, results}`) — it is not
   in the repo, but the exact content is in `Containerfile:15` and `README.md:714-722`.

Runs are launched by `experiments/simulatools.py:41`:
`./gradlew simulator:run -x caffeine:compileJava -x caffeine:compileCodeGenJava -PjvmArgs=-Xmx8g`,
with the HOCON `application.conf` rewritten per run (`simulatools.py:35-74`). Pure
CPU + heap; 8 GB per JVM, README:36 says "2 cores and ~8 GB of RAM will suffice".

The **LHD/LRB container is the exception**: `containers/lhd-lrb/Containerfile` is Ubuntu 18.04
with `apt-get install git sudo libconfig++-dev python3` and `bash ./scripts/install.sh` from
the LRB fork. Without Docker or root this must be rebuilt from source in `$HOME`
(libconfig++ is a small autotools project; LRB pulls a heavier C++ stack). These two
baselines are *comparison rows only* — the paper's own system does not depend on them.

### Dependency pins and age

There are **no build files in this repo** (`repo_facts.json: build_files: []`) and no
`requirements.txt`/lockfile — dependencies are a prose list (README:62) with no version pins.
That is loose, but all of them are actively maintained (`rich`, `pandas`, `polars`, `pyhocon`,
`xxhash`, `numpy`, `matplotlib`). The Java side is pinned properly by the
`adaptive-pipeline-v1` tag. Head commit 2026-02-18, 19 commits, MIT/`LICENSE` present.

### Data sources

- IBM Object Storage 010/012/024/029/031/034/045 and Twitter clusters 1/3/9/28: SNIA IOTTA
  `https://iotta.snia.org/traces/key-value` (README:133-141, paper ref [29][55]). Manual
  download; README warns the full Twitter set is ~2.8 TB compressed / 14 TB raw.
- Meta KV: public S3, no credentials — `containers/test-container/aliases.sh:1-2` gives the
  two exact `wget` URLs (`cache-datasets.s3.amazonaws.com/.../202210_kv_traces_all_sort.csv.zst`
  and `202401_...`).
- Synthetic trace: generated locally, no download (`experiments/synthetic_trace_gen.py`).
- Latency synthesis is **deterministic**: `trace_processing/common_data.py:1-4` commits the
  per-trace RNG seed and `latency_distributions.json` the exact distributions, so a
  re-generated trace should be bit-identical to the authors'. This is a strong repro signal.

### Eval scripts present / absent

Present: every Table 4 row (except the LHD/LRB legacy pair), the Table 3 grid search, the
Table 1 synthetic pipeline, the Fig. 3 concat trace and its plotter. Absent: any script that
assembles Table 4 itself from the per-run CSVs (the runners emit one CSV per policy/trace
into `RESULTS_DIR`; the normalisation "% relative to best static RFB" must be redone by hand),
and any throughput/memory measurement whatsoever.

## 3. Hard filters

| id | result | evidence |
|---|---|---|
| `H1_open_repo` | **pass** | `README.md:1-3` declares itself the NSDI '26 artifact; paper p. 13 "Availability: Our full artifact is available at GitHub [35]" and ref [35] is exactly `github.com/NadavKeren/Adaptive-Pipeline-Cache`; Artifact Appendix p. 18 describes these modules. The policy code is not in this clone but in the author's pinned Caffeine fork (`containers/test-container/Containerfile:4-7`, `README.md:49-53`); I browsed tag `adaptive-pipeline-v1` and confirmed `simulator/.../policy/latency_aware/pipeline/{PipelinePolicy,PipelineBlock,LbuBlock,LALruBlock,LALfuBlock,SampledHillClimber}.java` exist. Not a placeholder, not binary-only. |
| `H2_no_root` | **pass** | Core path is Java + Python in user space: `experiments/simulatools.py:41` runs `./gradlew simulator:run`; `containers/test-container/Containerfile` has no privileged step (only `git clone`, `gradlew compileJava`, `pip install`). No kernel/eBPF/perf/KVM anywhere. The one `sudo` grep hit is `containers/lhd-lrb/Containerfile:7`, inside the *legacy baselines* image (Ubuntu 18.04 + apt); those two rows (LHD, LRB of Table 4) would have to be rebuilt from source in `$HOME` or dropped — they are baselines, not the paper's system. |
| `H3_hardware_fit` | **pass** | Trace-driven simulation, CPU + RAM only, single process per run; `README.md:36` "2 cores and ~8 GB of RAM will suffice" (LRB wants 4); `simulatools.py:41` caps the JVM at `-Xmx8g`. Machine has 16 c / 32 t, 125 GiB RAM, ~257 GB free — comfortably above. No GPU needed. Largest working set is disk, not compute (see risks). |
| `H4_obtainable_deps_data` | **pass** | Deps are pip/conda-installable (README:60-62) and JDK 17/21 are present. Data: SNIA IOTTA key-value traces (public, README:133-141) and Meta KV via unauthenticated S3 (`containers/test-container/aliases.sh:1-2`). No proprietary trace. Latency values are generated locally from committed seeds/distributions (`trace_processing/common_data.py`, `latency_distributions.json`). |

## 4. Reproduction plan

**Target.** Table 4 (p. 12), the IBM012 and IBM010 columns: `RFB_1` = +11.7 % / 0.0 %,
`RFB_{1/4}` = +16.8 % / +0.1 %, `RF_1` = +35.3 % / +0.1 %, LBU alone = 24.0 % / 44.0 %,
ARC = 25.4 % / 0.3 %, SIEVE = 25.1 % / 21.1 %, S3-FIFO = 22.7 % / 16.2 %, ACA-TLFU =
55.7 % / 37.8 %. Reproducing IBM012 alone already tests the paper's central claim, because
IBM012 is the trace where LBU carries the result (Table 3, p. 11: best static RFB = (1,1,14)
vs RF = (1,15), a 19 % gap) — if RFB_1 does not beat RF_1 by roughly that margin on IBM012,
the burstiness claim does not hold. Secondary target: Table 1 (p. 7), the LRU\*/LFU\*/LBU 3×3
synthetic matrix, which needs *no downloads at all*
(`experiments/run_synthetic_experiments.py --cache-size 1024 --seed 42`).

**Scale-down.** Drop Twitter and Meta entirely for the first pass (they are 200 M-request
traces and hundreds of GB of raw download). Use IBM012 (533 K requests, cache 1 024) first, as
the README itself recommends (`README.md:32`), then IBM010 (13.2 M, cache 512) and IBM024
(33.4 M, cache 512). Skip the LHD and LRB rows (legacy container). Run the grid search
(`--run-grid-search`, 153 configs) only on IBM012 — it is what defines the "best static RFB"
denominator of Table 4; for IBM010 reuse the paper's (14,2,0) from Table 3. Use
`--rounds 3` instead of the paper's 10 for the sampled-ghost variance.

**Steps.**
1. conda env (python ≥ 3.12) + `pip install rich pandas polars pyhocon xxhash numpy matplotlib`.
2. `git clone` the Caffeine fork, `git checkout adaptive-pipeline-v1`, `./gradlew compileJava`
   with `JAVA_HOME` pointing at the user-installed JDK 21 (fall back to 17 if the toolchain
   complains). This is the main risk step.
3. Write `experiments/conf.json` per `containers/test-container/Containerfile:15`.
4. Download `IBMObjectStoreTrace012Part0` (and 010) from SNIA; run
   `trace_processing/parse_IBM.py` then `latency_appender.py -d latency_distributions.json -c`.
   Seeds are committed, so latencies should match the paper's exactly.
5. `python experiments/run_experiments.py --input <...ibm012...trace.xz> --run-base --run-aca
   --run-other --run-single-shc --rounds 3` , then `--run-grid-search`.
6. Normalise every policy's `Average Penalty` against the best static RFB CSV by hand
   (no script ships for this) and compare against Table 4.
7. Independently: `run_synthetic_experiments.py` for Table 1 and `trace_merger.py` +
   `adaptation_graph_gen.py` for Fig. 3 if time allows.

**Effort.** ≈4 person-days of setup/porting + ≈40–80 CPU-hours (0 GPU-hours). IBM012 runs are
minutes; IBM010 at 13 M requests × ~20 policy configs plus a 153-point grid search is the bulk.
Twitter/Meta at 200 M requests are "up to a day" each per the README and are out of scope for
the first two weeks.

**Level: H.** Every ingredient for the target result is present and pinned: the policy code is
tagged, the runner script has the paper's exact hyper-parameters hard-coded
(`run_experiments.py:39-113`), the default cache sizes match Table 3
(`run_experiments.py:33-37`), the latency distributions and per-trace seeds are committed, and
the README documents a native (non-container) route. The machine exceeds the stated
requirements by ~8×. It is not an "A" because there is no lockfile, no badge evidence, no
table-assembly script, and the Gradle/JDK step is unverified from a desk review — but none of
those is a porting *project*, so M would understate it.

## 5. Add-on ideas

### A. Load-coupled fetch latency (congestion feedback)

- **Hypothesis.** We hypothesize that making fetch latency a function of the number of
  concurrently outstanding fetches (an M/M/c-style origin queue) *increases* the ARL advantage
  of burstiness-aware admission (LBU) and shifts the adaptive pipeline's steady-state quota
  toward the LBU block, under bursty traces (IBM012, Twi28) and high miss-rate regimes
  (small caches), compared with the paper's load-independent i.i.d. latency model.
- **Mechanism.** Today `L_i` is sampled per key at trace-generation time from a fixed normal
  chosen by `hash(key) mod Σweights` (`trace_processing/latency_appender.py:63-72,140-154`)
  and is then a constant column in the trace. Replace this with a latency that is resolved at
  simulation time as `L_i = L_base(i) + q(|F_t|)`, where `|F_t|` is the current size of the
  fetch buffer and `q` is a queueing term (linear, then knee-shaped past a service-capacity
  parameter `c`). Two tiers of implementation: (i) a cheap offline approximation entirely
  inside this repo — compute an instantaneous request-density signal per timestamp in
  `latency_appender.py` and modulate the drawn latency by it, giving a *correlated* but
  open-loop model; (ii) the real closed-loop version in the fork's `FetchStage.java`, where
  `F_t` is already maintained, plus a new `LatencyModel` config key threaded through
  `pipeline.*`. Then re-run Table 4 under both models and compare rankings and the Fig. 3
  quota traces.
- **Code locations.** `trace_processing/latency_appender.py`,
  `trace_processing/latency_generators.py`, `trace_processing/latency_distributions.json`,
  `experiments/run_experiments.py` (new settings + a second sweep),
  `graph_generators/adaptation_graph_gen.py` (quota traces under the new model).
  Fork-side: `simulator/.../latency_aware/pipeline/FetchStage.java`.
- **Motivating evidence.** §4 "The datasets" (p. 11): latencies are drawn from static
  per-site normals and "items are distributed uniformly at random across sites" — latency is
  independent of load, of the trace, and of the cache's own behaviour. Footnote 1 (p. 3)
  admits the system only estimates `L_i` by the last observed value. But delayed hits are
  *by definition* a congestion phenomenon: a burst produces `s(i,t)` simultaneous pending
  requests (Eq. 2, p. 4), which in any real origin would lengthen the very fetch they are
  waiting on. The paper's model therefore cannot exhibit the feedback loop that makes its own
  motivating scenario worse — this both under- and over-states LBU's value in ways that are
  not predictable a priori.
- **Feasibility: M.** The offline tier is a ~200-line change to files in this repo; the
  closed-loop tier needs a contained edit to one Java class plus a config knob, and the
  existing harness re-runs everything unchanged. But: all 11 usable baselines must be re-run
  under the new model to make the comparison fair (≈2× the reproduction compute), and the
  queueing parameters need a defensible calibration. Cross-cutting but not a redesign.
- **Research value: H.** It attacks a simplifying assumption shared by the *entire*
  delayed-hits line (Atre et al. SIGCOMM'20 onward), and either outcome is publishable-grade
  for a class project: if LBU's edge grows, the paper under-sells itself and the congestion
  regime is the right one to target; if it shrinks or the ranking reorders, the reported 10 %
  is an artifact of a benign latency model.
- **Scoop check: partial.** Queries: "caching with delayed hits load-dependent fetch latency
  queueing congestion 2025"; "'delayed hits' stochastic miss latency". Closest work:
  [Modeling and Optimizing Latency for Delayed Hit Caching with Stochastic Miss Latency,
  arXiv:2505.15531](https://arxiv.org/abs/2505.15531) and [VA-CDH, arXiv:2504.20335](https://arxiv.org/pdf/2504.20335)
  — both replace deterministic latency with an *i.i.d. random* (exponential) latency and
  derive variance-aware ranking functions; also [Optimizing latency for caching with delayed
  hits in non-stationary environments (PEVA 2025)](https://jhc.sjtu.edu.cn/~bjiang/papers/Jiang_PEVA2025_Cache.pdf).
  None of them makes latency depend on the *instantaneous outstanding-fetch count* (closed
  loop), and none evaluates a multi-block adaptive pipeline under it. The variance-aware
  ranking functions are in fact a natural extra baseline for this add-on.

### B. Does the pipeline actually compose? A fourth block and block order

- **Hypothesis.** We hypothesize that (i) adding a fourth, reuse-distance-oriented block
  (LIRS/FRD-style) to the RFB pipeline lowers ARL on the traces where RFB is farthest from
  the best static configuration (IBM031 +27.1 %, Meta2 +16.0 % for `RFB_1`, Table 4), and
  (ii) ARL is significantly sensitive to block *order*, i.e. the pipeline is not the
  order-free "plug-and-play" abstraction the paper claims.
- **Mechanism.** The pipeline is already config-driven: `pipeline.num-of-blocks` and
  `pipeline.blocks.N.type` (`experiments/run_experiments.py:39-50`). Implement one new
  `PipelineBlock` subclass in the fork (FRD or LIRS over the latency-aware score) and register
  its type string; then (a) run the m=4 adaptive pipeline, whose ghost count rises from
  `m(m−1)=6` to 12, directly testing the scalability argument on p. 11, and (b) run the 6
  permutations of the R/F/B blocks at the best static quotas from Table 3 to quantify order
  sensitivity. Extend `run_grid_search` to 4 blocks (the current double loop at
  `run_experiments.py:296-313` enumerates 153 configurations for m=3; for m=4 it becomes 969,
  so sample it or fix the new block's quota).
- **Code locations.** `experiments/run_experiments.py:39` (block config dict),
  `experiments/run_experiments.py:289` (`run_grid_search`), `experiments/policies.py`,
  `experiments/run_experiments.py:216` (`run_full_ghost`).
  Fork-side: `.../pipeline/PipelineBlock.java`, `PipelinePolicy.java`.
- **Motivating evidence.** §3 p. 9: "The order of the blocks in the pipeline may well, and
  indeed often does, affect the behavior and performance of the overall pipeline cache
  architecture" — asserted, never measured. §5 p. 13 sells the design as: "to address a new
  access pattern, one merely adds a simple policy (akin to LBU) to the pipeline and allows the
  adaptive mechanism to self-tune allocations" — also never tested beyond m=3, and the ghost
  cost is quadratic in m (p. 11), so the claim has a built-in tension. Table 4 shows RFB is
  still 16–27 % off the static optimum on IBM031/Meta2/Meta4, leaving headroom.
- **Feasibility: H.** One new Java class against an existing interface, everything else is
  configuration and existing scripts; evaluable on IBM traces on this machine within the
  compute budget; clearly sized for 2–4 students.
- **Research value: M.** It directly tests the paper's central architectural claim (good), but
  the expected outcome — "a 4th block helps a bit, order matters somewhat, ghosts get
  expensive" — is what most reviewers would predict. It becomes H only if m=4 *hurts*, which
  would be a real finding about the hill climber's ability to search a larger simplex.
- **Scoop check: partial.** Queries: "modular pipeline cache architecture multiple eviction
  policies adaptive partitioning 2025"; "policy orchestration cache 2026". Closest:
  [SCION: Size-aware Policy Orchestration for Nonstationary Object Caches, arXiv:2605.01055](https://arxiv.org/pdf/2605.01055)
  (May 2026) — orchestrates six *whole* policies by a workload fingerprint and picks one; it
  is miss-ratio/byte-miss-ratio oriented and explicitly not latency- or delayed-hit-aware, and
  it does not compose policies in a victim-chaining pipeline or size blocks. Different
  mechanism, overlapping motivation.

### C. A better allocator than fixed-step greedy hill climbing

- **Hypothesis.** We hypothesize that replacing the fixed-one-quantum greedy hill climber with
  (a) an adaptive step size and (b) a regret-based bandit over ghost configurations reduces
  ARL and, more importantly, shortens the re-convergence time after a workload shift, measured
  on the concatenated trace of Fig. 3, at equal or lower ghost overhead.
- **Mechanism.** Today: every `10·M` requests (`adaption-multiplier` = 10,
  `run_experiments.py:101,240`), evaluate `m(m−1)` ghosts each one quantum away and take the
  argmin (Algorithm 2, p. 10); 16 quanta total. Changes: (1) accelerate the step when the same
  direction wins k intervals in a row and decelerate on oscillation; (2) keep per-direction
  regret estimates so ghosts that have been losing are evaluated at a lower sampling rate,
  cutting metadata overhead below the current +75 % at `R=1/4`; (3) make the adaptation
  interval itself adaptive (short after a detected distribution shift, long when stable).
  Metrics: final ARL per trace (Table 4), plus a new *re-convergence* metric = requests needed
  to reach within 5 % of the post-shift best static quota, read off the `.quota_dump` the
  runner already preserves (`run_experiments.py:183-196`) and plotted by the existing
  `adaptation_graph_gen.py`.
- **Code locations.** `experiments/run_experiments.py:100` (`FGHC_SETTINGS`),
  `experiments/run_experiments.py:233` (`run_sampled_all`),
  `experiments/run_experiments.py:216` (`run_full_ghost`),
  `graph_generators/adaptation_graph_gen.py`, `trace_processing/trace_merger.py`.
  Fork-side: `.../pipeline/SampledHillClimber.java`, `RandomHillClimber.java`.
- **Motivating evidence.** The paper itself credits the hill climber, not LBU, with most of
  the win: "RF_1 exhibits an improvement of almost 25 % when compared with
  Adaptive-CA-WTinyLFU, which can be mostly attributed to our novel hill-climbing approach"
  (§4.1, p. 12). And it explicitly settles for less than optimal: "our goal is not to find a
  local minimum, but rather to avoid allocations that result in unnecessary performance
  degradation … merely being near a good allocation is sufficient" (§3.1, p. 9). Fig. 3a
  (p. 13) shows visibly slow ramps at segment boundaries, and `RFB_1` is still +27.1 % off the
  static optimum on IBM031 (Table 4) — an adaptivity failure, not an LBU failure.
- **Feasibility: M.** Confined to one or two Java classes plus new config keys, and the
  evaluation harness and the concat-trace plotting already exist — but the re-convergence
  metric needs new analysis code, the concat trace is 85 M requests per run, and a bandit
  formulation needs care to not destabilise the live cache.
- **Research value: M.** Squarely on the paper's own critical path and the "near-optimal is
  enough" claim is falsifiable. Marked down because bandit/regret-based policy adaptation is
  well-trodden (LeCaR, CACHEUS) even if not for multi-block latency-aware quotas, and a
  moderate ARL gain would surprise nobody.
- **Scoop check: partial.** Queries: "adaptive cache partitioning ghost cache multi-armed
  bandit reinforcement learning eviction policy 2024 2025"; "hill climbing cache resizing
  2025". Closest: LeCaR / CACHEUS (regret-based weighting of LRU vs LFU, pre-2023, discussed
  as prior art in the paper's §1.2 via [2,13,51]) and
  [DynamicAdaptiveClimb, arXiv:2511.21235](https://arxiv.org/abs/2511.21235) (Nov 2025), which
  adapts promotion distance and total cache size — hit-ratio oriented, single policy, no
  ghosts, not delayed-hit aware. Nothing found that does bandit-style allocation across
  pipeline blocks under an ARL objective.

### D. What does the pipeline cost? Throughput and memory of RFB in a real cache

- **Hypothesis.** We hypothesize that the pipeline + sampled-ghost machinery costs
  significantly more than the paper's analytical estimate (0.875 extra metadata operations per
  request, +75 % ghost entries) once implemented in a concurrent cache, and that a sharded
  pipeline recovers throughput within X % of Caffeine's W-TinyLFU while preserving most of the
  ARL gain, measured on this 16-core machine under multi-threaded replay of IBM010.
- **Mechanism.** Two parts. (1) *Measurement*: instrument the simulator path to report
  wall-clock requests/second and resident metadata bytes per policy — the harness already
  parses whatever the simulator emits into a DataFrame (`experiments/simulatools.py:80-87`),
  so adding two columns and a sweep is mechanical, and it immediately yields the
  overhead table the paper never presents. (2) *Prototype*: implement the pipeline over
  Caffeine's real (non-simulator) cache with per-shard pipelines and a single background
  thread owning the ghosts and the adaptation event, then drive it with a JMH-style
  multi-threaded replay harness and measure throughput vs thread count and ARL vs the
  single-threaded simulator result.
- **Code locations.** `experiments/simulatools.py` (run/parse path and JVM flags),
  `experiments/policies.py` (policy registry for the new variant),
  `experiments/run_experiments.py` (sweep over thread counts / policies),
  `containers/test-container/Containerfile` (build recipe to replay).
  Fork-side: `.../pipeline/PipelinePolicy.java` and the `caffeine/` library module.
- **Motivating evidence.** §5, p. 13, verbatim: "From a systems perspective, the main
  technical hurdle is efficient parallelization, which is not currently addressed in our
  simulation-based implementation", and "we aim to integrate RFB into existing open-source
  projects … The primary challenge is to develop a Caffeine branch that replaces its internal
  caching policy with RFB". The overhead argument on p. 11 is purely analytical (ghost-entry
  counts compared with ARC/LIRS/FOMO); Table 4 reports ARL only. A policy that wins 10 % ARL
  but halves throughput is not deployable, and nothing in the paper rules that out.
- **Feasibility: M.** Part (1) is a few days. Part (2) is a substantial Java engineering
  effort inside an unfamiliar, large codebase and needs a new concurrent benchmark harness —
  but it needs no special hardware (16 cores / 32 threads is a legitimate concurrency
  testbed), no root, and can be descoped to "sharded prototype + JMH" if the full integration
  stalls. Risky for a 10-week project but not out of reach; part (1) is a guaranteed fallback
  deliverable.
- **Research value: H.** It answers the paper's own declared open question, and the answer
  matters to anyone considering deployment. Both outcomes teach something: cheap-and-parallel
  validates the modularity pitch, expensive-and-serial says the pipeline is a simulator
  artifact.
- **Scoop check: clear.** Queries: "Caffeine W-TinyLFU throughput concurrent adaptive policy
  overhead 2026 latency-aware integration"; "Keren Einziger Scalosub pipeline cache LBU
  follow-up 2026". No follow-up to this NSDI '26 paper was found (it was presented May 2026);
  no RFB branch of Caffeine exists upstream. The closest relevant art is
  [Limited Associativity Makes Concurrent Software Caches a Breeze, arXiv:2109.03021](https://arxiv.org/pdf/2109.03021)
  (a concurrency technique for software caches, not this policy) — usable as a design input,
  not a scoop.

### E. Variable object sizes and size-proportional latency

- **Hypothesis.** We hypothesize that when fetch latency is modelled as
  `L_i = RTT + size_i / bandwidth` and the cache is byte-capacity-bounded, the ARL ranking in
  Table 4 changes materially and RFB's advantage over size-aware baselines shrinks, on IBM and
  Meta traces whose native size fields the artifact currently discards.
- **Mechanism.** `trace_processing/parse_IBM.py:8-18` keeps only `time` and `object_id` and
  `parse_meta.py:9-22` keeps only `timestamp,key` — the size column present in both trace
  formats is thrown away. Restore it, extend the trace format to carry size, make
  `latency_appender.py` compute a size-dependent latency instead of a per-key i.i.d. draw, and
  switch the simulator's capacity accounting to weighted entries (Caffeine's simulator already
  supports weighted traces). Add one size-aware baseline (GDSF or AdaptSize) and optionally a
  size-aware pipeline block.
- **Code locations.** `trace_processing/parse_IBM.py`, `trace_processing/parse_meta.py`,
  `trace_processing/parse_twitter.py`, `trace_processing/latency_appender.py`,
  `experiments/run_experiments.py`.
- **Motivating evidence.** §1.2, p. 5–6 explicitly assumes unit-sized items and defers size to
  "slabbing" — "cluster items of similar size … and then apply a unit-sized cache policy (as in
  this work)". In object storage (the IBM traces' own domain) object sizes span orders of
  magnitude and fetch time is dominated by transfer, not RTT, so the assumption and the latency
  model interact.
- **Feasibility: M.** Trace-side changes are easy and in this repo, but weighted capacity plus
  a size-aware block touches the simulator's accounting and every baseline must be re-run;
  defining a fair size-aware ARL metric is itself a design decision.
- **Research value: M.** A real and acknowledged gap, but size-aware caching is a mature area
  and one of the paper's own authors has published on it (ref [19], *Lightweight Robust Size
  Aware Cache Management*), so a reviewer would see this as filling in a known box rather
  than opening a new one.
- **Scoop check: partial.** Query: "variable object size delayed hits latency proportional to
  object size". The latency model "constant delay plus a component proportional to object
  size" already appears in the delayed-hit literature surfaced above (arXiv:2505.15531's
  related work), and [SCION](https://arxiv.org/pdf/2605.01055) plus AdaptSize/[Lightweight
  Robust Size Aware Cache Management](https://arxiv.org/pdf/2105.08770) cover size-aware
  policy selection — but not size-aware *pipeline block composition* under an ARL objective.

## 6. Risks and open questions

1. **The system is in a second repository.** Everything that implements the paper
   (`PipelinePolicy`, `LbuBlock`, `SampledHillClimber`, `FetchStage`) lives in
   `github.com/NadavKeren/caffeine` @ `adaptive-pipeline-v1`, not in the audited clone. It is
   public, author-owned, tagged and linked from both the README and the Containerfile, so this
   is not an availability problem — but *all four add-ons do their real work there*, and the
   team must be comfortable modifying a large Java codebase they did not write. A desk review
   cannot tell how readable those classes are.
2. **Gradle/JDK build is unverified.** `./gradlew compileJava` on a Caffeine fork pulls a
   large plugin stack and may pin a JDK toolchain. JDK 17 and 21 are installed; if the fork
   wants a different major version, a user-space JDK install is needed (doable, but it is the
   single most likely two-day sink in week 1).
3. **Likely bug in the synthetic trace generator.** `experiments/synthetic_trace_gen.py:70`
   appends 4-tuples `(curr_time, item_num, 0, latency)` inside the recency loop but 3-tuples
   everywhere else (`:73,83,102,201`), while `gen_trace` writes only three fields
   (`:212`: `{row[0]} {row[1]} {row[2]}`). Recency requests therefore appear to be written with
   miss penalty `0` instead of the configured `latency` of 1000 ms. If that reading is right,
   Table 1's recency column (LRU\* 65.61 vs LBU 606.73) will not reproduce as printed from this
   script. Worth verifying first — it is cheap (no downloads) and is either a quick fix or the
   first real finding.
4. **Disk and time for the large traces.** Twitter is ~2.8 TB compressed for the full set
   (`README.md:141`); the four needed clusters plus the two 200 M-request Meta traces could
   approach or exceed the ~257 GB free. Meta/Twitter runs are "up to a day to process"
   (`README.md:32`). Any plan that needs Table 4's Twitter/Meta columns must budget storage
   explicitly; the IBM subset does not have this problem.
5. **Two baselines are effectively unavailable.** LHD and LRB require the Ubuntu 18.04 image
   (`containers/lhd-lrb/Containerfile`, apt + `sudo`). With no Docker and no root they must be
   built from source in `$HOME` (libconfig++ plus LRB's C++/ML stack) or dropped. LRB is the
   *best* prior-art row in Table 4 (+14.6 %), so dropping it weakens any "we beat the best
   baseline" claim; ARC/SIEVE/S3-FIFO/ACA remain available as strong baselines.
6. **No dependency pins and no table-assembly script.** README:62 lists library names without
   versions and there is no `requirements.txt`; the "% relative to best static RFB"
   normalisation of Table 4 is not scripted. Neither is fatal; both add friction and both are
   worth fixing (and contributing back) early.
7. **No artifact badge evidence.** The PDF contains an Artifact Appendix (p. 18) and an
   availability statement (p. 13), but I could not retrieve the USENIX presentation page
   (HTTP 403) and found no "Artifacts Available/Functional/Reproduced" badge in the PDF or the
   repository. Treat "artifact evaluated" as unconfirmed.
8. **Add-on A changes the metric.** Any result produced under a load-coupled latency model is
   not numerically comparable to Table 4; the project must re-run the baselines under the new
   model and report both, which roughly doubles the compute and must be planned from week 1.

## 7. Evidence index

**Paper** (`paper.txt` page markers; PDF pages read as images where noted)
- p. 2 — abstract: 13 traces, 10 % ARL improvement, low STD.
- p. 3 — §1 contributions (i)–(v); §1.1 system model, fetch/pending buffers; footnote 1
  (latency estimated by last observed fetch).
- p. 4 — hit / miss / delayed-hit request latency cases; Eq. (1)–(3) ARL and accumulated
  request latency `s(i,t)`.
- p. 5–6 — §1.2 related work; adaptive caches limited to two heuristics; unit-size assumption
  and slabbing; §1.3 CRA = LRU\*, access-time-aware TinyLFU = LFU\*.
- p. 6–7 — §2.1 why burstiness ≠ recency/frequency; **Table 1** (synthetic 3-bias results).
- p. 7–8 — §2.2 burstiness score; §2.3 LBU, ℓ-window max, aging, lazy heap.
- p. 8–9 — §3 pipeline architecture, Algorithm 1, Fig. 2; block-order caveat.
- p. 9–10 — §3.1 adaptive pipeline, Algorithm 2, quanta, ghost caches, MiniSim-style sampling.
- p. 11 — **Table 2** (6 ghosts for m=3); overhead arithmetic (+75 % entries, 15 % compute);
  §4 datasets, AWS latency distributions, cache-size selection; **Table 3** (best static
  RFB/RF per trace, request counts, cache sizes).
- p. 12 (read as image, `pages/page-12.png`) — **Table 4**, full policy × trace ARL matrix;
  §4.1 competitive evaluation, RF_1 vs ACA-TLFU 25 % claim, sampled vs full ghosts.
- p. 13 (read as image, `pages/page-13.png`) — **Fig. 3a/3b** adaptation over the concat trace;
  §4.2; §5 discussion, Caffeine integration and parallelization as future work; availability.
- p. 16–17 — Appendix A, LBU implementation (virtual fetch requests, decay, lazy heap, Fig. 4).
- p. 18 — Appendix B, Artifact Appendix: contents, container split, traces not included.

**Repository** (`repo/`)
- `README.md` — :27-36 container/resource requirements; :49-53 the three code repositories;
  :55-62 native requirements (Python 3.14, Java 11+, library list); :133-148 trace sources and
  the 2.8 TB Twitter warning; :317-449 experiment runners and per-trace cache sizes;
  :450-521 LHD/LRB mock workflow; :523-634 synthetic experiments; :650-689 Fig. 3 plotting;
  :691-743 end-to-end workflow and `conf.json`.
- `containers/test-container/Containerfile` — :4-7 caffeine fork + tag `adaptive-pipeline-v1`;
  :12 `./gradlew compileJava`; :15 exact `conf.json`.
- `containers/test-container/aliases.sh` — :1-2 unauthenticated S3 URLs for metakv2/metakv4.
- `containers/lhd-lrb/Containerfile` — :1,7,13,23 Ubuntu 18.04 + apt/sudo + LRB install script
  + LHD `make`.
- `experiments/policies.py` — :14-17 `latency-aware.Pipeline`, `SampledHillClimber`, `Mockup`,
  `RHC`; :18-26 baseline policy class names.
- `experiments/simulatools.py` — :14-19 `conf.json` loading; :35-74 HOCON generation;
  :41 gradle run command and `-Xmx8g`; :80-87 CSV → DataFrame.
- `experiments/run_experiments.py` — :31-37 quanta and per-trace cache sizes (match Table 3);
  :39-98 RFB/RF/single-block configurations and LBU hyper-parameters; :100-113 hill-climber
  settings; :183-196 `.quota_dump` handling; :216-231 `run_full_ghost`; :233-269 sampled
  runs; :272-287 single-policy runs; :289-313 grid search; :322-342 baseline sweep.
- `experiments/run_synthetic_experiments.py` — :36-65 LRU/LFU/LBU-only pipelines;
  :140-179 the 3×3 table (Table 1).
- `experiments/synthetic_trace_gen.py` — :55-107 the three traffic generators; :70,73 the
  tuple-arity inconsistency; :168-212 `gen_trace` and the 3-field writer.
- `experiments/synthetic_trace_config.json` — item counts 250 000/100/100/150 000 and
  latency 1000 ms (matches §2.1 p. 6–7).
- `trace_processing/latency_appender.py` — :63-72 hash-based site assignment; :117-169 trace
  rewriting; :214 per-trace seed lookup; :222-223 PEP-701 f-strings (Python ≥ 3.12).
- `trace_processing/latency_generators.py` — :17-40 the normal generator used for the paper's
  three sites.
- `trace_processing/latency_distributions.json` — the exact 120/340/675 ms configuration.
- `trace_processing/common_data.py` — :1-4 committed per-trace RNG seeds.
- `trace_processing/parse_IBM.py` — :8-18 GET filtering, size column dropped.
- `trace_processing/parse_meta.py` — :9-22 GET filtering, size column dropped.
- `graph_generators/adaptation_graph_gen.py` — Fig. 3 generator.
- `repo_facts.json` — head commit `e7413d1` dated 2026-02-18; 27 files; no build files;
  red flags = 1 `sudo` (lhd-lrb Containerfile) and 17 Docker mentions.
- `fetch_result.json` — PDF from `usenix.org/system/files/nsdi26-keren.pdf`; repo provenance
  "unclear" from the list, resolved to official by README/paper ref [35].

**External** (scoop check / provenance)
- <https://github.com/NadavKeren/caffeine/tree/adaptive-pipeline-v1/simulator/src/main/java/com/github/benmanes/caffeine/cache/simulator/policy/latency_aware/pipeline> — 14 Java files incl. `PipelinePolicy.java`, `LbuBlock.java`, `SampledHillClimber.java`, `FetchStage.java`.
- <https://arxiv.org/abs/2505.15531> — delayed hits with stochastic (exponential) miss latency.
- <https://arxiv.org/pdf/2504.20335> — VA-CDH, variance-aware delayed-hit ranking.
- <https://jhc.sjtu.edu.cn/~bjiang/papers/Jiang_PEVA2025_Cache.pdf> — delayed hits in
  non-stationary environments (PEVA 2025).
- <https://arxiv.org/pdf/2605.01055> — SCION, size-aware policy orchestration (May 2026).
- <https://arxiv.org/abs/2511.21235> — DynamicAdaptiveClimb (Nov 2025).
- <https://arxiv.org/pdf/2109.03021> — limited associativity for concurrent software caches.
- <https://dl.acm.org/doi/10.5555/3833220.3833349> — NSDI '26 proceedings entry for this paper.
