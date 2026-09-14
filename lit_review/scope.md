# Scope

## The course project

Graduate Operating Systems, Fall 2026 (Notre Dame). The team (2–4 students) takes a
recent paper from a top-tier systems venue and **improves its design or performance**
("Improvement paper" track). If the improvement does not pan out, a careful
reproduction showing the results are correct or more nuanced is an accepted fallback
("Contemporary paper" track). The final deliverable is a paper "within striking
distance" of a conference submission, and the proposal must state a **testable
research hypothesis**. Budget: roughly 10 weeks of part-time work by the team, on the
single machine described in `env.md`.

## Years

2023, 2024, 2025, 2026 — all weighted equally. No age penalty inside this window.

## Venues

Tier A (core systems): OSDI, SOSP, EuroSys, USENIX ATC, NSDI, FAST, ASPLOS.
Tier B (systems-adjacent): MLSys, VLDB, SIGMOD, SIGMETRICS, SoCC, Middleware.
Main research/technical track only — no workshops, posters, demos, or industry-track
abstracts without a full paper.

## Topics — in scope

Tag each paper with exactly one of these topic keys:

| key | covers |
|---|---|
| `llm-inference` | LLM / model serving and inference systems: KV-cache management, request scheduling, batching, speculative decoding systems, offloading |
| `ml-systems` | Other ML systems: training systems that fit one node, ML compilers, runtimes, data loading/preprocessing pipelines |
| `caching` | Cache eviction / admission / tiering policies, CDN and key-value caches, trace-driven cache studies |
| `storage` | LSM-trees, key-value stores, storage engines, user-space / FUSE file systems, compression, dedup, SSD-aware software |
| `scheduling` | CPU/GPU/job schedulers and resource managers that can be studied in user space or by simulation; serverless/cluster policies evaluated with simulators or traces |
| `memory` | User-space memory management: allocators, garbage collection, memory tiering/far-memory studied in user space or by simulation |
| `ml-for-systems` | Learned components inside systems: learned indexes, learned cache/scheduling policies, ML-based tuning |
| `other-userspace` | Any other systems paper whose core artifact is user-space and fits the machine (e.g. runtimes, concurrency libraries, observability tooling that needs no root) |

## Topics — out of scope

Exclude papers whose core contribution *requires* any of these (see `env.md` for why):

- modifying or rebooting into a custom kernel, kernel modules, eBPF programs
- hardware performance counters (`perf`), KVM/hypervisors, Docker as the only way to run
- multi-node clusters, RDMA, SmartNICs/DPUs, FPGAs, CXL, persistent memory, custom hardware
- multi-GPU or >24 GB GPU memory **with no meaningful single-GPU scale-down**
- architecture simulation papers whose evaluation needs gem5-scale compute or hardware
- pure theory / measurement studies with no reusable artifact

When a paper is borderline (e.g. evaluated on 8 GPUs but the mechanism works on one),
keep it and note the concern — the audit stage decides.

## Hard requirement

The paper must have an **openly released official implementation** (GitHub, GitLab,
Zenodo artifact, etc.). A paper whose code is not released cannot be built upon.
