STATUS: not_yet_published
TOTAL_PAPERS: 0
INCLUDED: 0

## Sources

- Official conference site: https://acmsocc.org/2026/ (home page, fetched 2026-09-14 with `curl`).
  It states: "SoCC'26 will take place in person in Singapore. November 18-20, 2026" — i.e. the
  conference has **not happened yet** as of today (2026-09-14).
- Important dates block on the same page (verbatim):
  - `nov 18` — Conference starts
  - `sep 26` — **Notification to authors (second round)**
  - `sep 12` — Authors' response period ends (second round)
  - `sep 10` — Authors' response period begins (second round)
  - `jul 14` — Paper submission deadline (second round)
  - `jul 07` — Paper registration deadline (second round)
  - `apr 29` — Notification to authors (first round)
  - `feb 13` — Paper submission deadline (first round)
- Accepted-papers page: https://acmsocc.org/2026/accepted-papers.html (fetched and parsed raw HTML).
  It is explicitly headed: *"The following papers have been accepted to SoCC 2026 (**Round 1**).
  Titles and author lists may change during the shepherding process."* It lists **19** titles.
  Round-2 notifications are not due until **2026-09-26**, twelve days from today, so this list is
  a partial (round-1-only) list, not the full main-track program.
- Call for papers: https://acmsocc.org/2026/papers.html — confirms the two-round review model and
  the four submission categories (Full Research, Short Research, Industry, Vision).
- https://acmsocc.org/2026/schedule.html exists but is **stale template content carried over from
  SoCC 2025** (it is dated "Wednesday, November 19, 2025", links to "Proceedings of SoCC 2024", and
  the corresponding nav entry is HTML-commented-out on every 2026 page). It is not the 2026 program
  and was not used.

Cross-checks attempted:
- DBLP (`https://dblp.org/db/conf/cloud/index.html`): blocked by an Anubis anti-bot challenge for
  both plain and browser user-agents; no data retrievable. In any case DBLP indexes SoCC only once
  the ACM proceedings are published.
- ACM DL (`https://dl.acm.org/conference/socc/proceedings`): HTTP 403 behind Cloudflare. A SoCC '26
  proceedings volume cannot exist yet — proceedings appear at/near the November conference date.
- Web search for a second-round or full SoCC 2026 accepted list returned only the official site and
  CFP aggregators (wikicfp, myhuiban); no full paper list is published anywhere.

Conclusion: the complete main-track paper list for ACM SoCC 2026 is **not public as of 2026-09-14**.
Per the task rules this run stops with `STATUS: not_yet_published`.

### Recommended re-run date

**On or shortly after 2026-09-26** (round-2 notification), and ideally again in late October 2026
once the program/proceedings are posted, since round-1 titles are still subject to shepherding
changes and camera-ready artifact/code URLs are usually not available until then.

### Partial information observed (round 1 only — NOT screened, recorded for the next run)

These 19 round-1 titles were on the accepted-papers page. They are listed here as a lead for the
follow-up run; none of them were topic-screened, machine-screened, or code-checked, and they are
deliberately **not** counted in `TOTAL_PAPERS`:

1. Spanner-RSS+: Diagnosing and Reducing Safe-Time Waiting of Read-only Transactions in Spanner-RSS
2. FCP: Fast User-space RDMA Control Plane Setup for Elastic Computing
3. FlowWise: Fast-Slow Model Orchestration for Line-Rate Network Traffic Intelligence
4. FedRD: Towards Memory-efficient Federated Learning via Adaptive Recomputation and Defragmentation
5. PEACE: Power and Performance Aware Colocation for Efficient GPU Spatial Partitioning
6. Spandana: Reconciling Strict SLOs with Low Cost under Fine-Grained Load Fluctuations
7. TRAM: Tree-based atomic multicast on RDMA
8. Tessera: Contract-Driven Cost-SLO Optimization for Multi-tenant GPU Clouds
9. ExclaveFL: Verifiable Claims for Federated Learning using Exclaves
10. Cadence: Taming Coupled Contention in Disaggregated Agent Clouds
11. The Kernel Always Knows: Understanding Isolation via Kernel Objects
12. Memory-Decoupled Layer-Wise Fine-Tuning for Efficient On-Device LLM Adaptation
13. BoxD: Managing GPU Managed Memory
14. Robust and efficient replication with CAV data structures
15. SlimeMold: Scaling Distributed Hardware Load Balancers via a Unified Giant Connection Table
16. MosaicKV: SLO-Aware KV-Cache Virtualization for Multi-Tenant LLM Serving in the Cloud
17. Evaluating Agentic Systems Across the Lifecycle: A Taxonomy of Drifts and Success Criteria
18. No Request Left Behind: Tackling Heterogeneity in Long-Context LLM Inference with Medha
19. On Evaluating Performance of LLM Inference Serving Systems

First-glance notes for the follow-up run (not decisions):
- Likely promising on the target machine: #5 PEACE (single-GPU spatial partitioning via MPS/MIG-like
  colocation), #13 BoxD (GPU managed memory, single GPU), #16 MosaicKV (KV-cache, `llm-inference`),
  #18 Medha (long-context LLM inference — may need multi-GPU scale-down), #19 the LLM-serving
  evaluation study (`llm-inference`, but may be a measurement study with no reusable artifact),
  #12 on-device LLM fine-tuning (`ml-systems`, memory-decoupled, plausibly fits 24 GB).
- Likely out on machine grounds: #2 FCP and #7 TRAM (RDMA), #15 SlimeMold (hardware load balancers /
  Broadcom silicon), #9 ExclaveFL (TEE/exclaves hardware), #11 kernel-object isolation (kernel access).

Data-quality anomaly worth re-verifying on the next fetch: three of the nineteen entries (#8 Tessera,
#10 Cadence, #16 MosaicKV) are attributed to the identical two-author list "Rui Li (Hill Research);
Shuang Cao (Hill Research)", an affiliation with no visible research footprint. Entry #17 is likewise
attributed to an independent researcher plus a startup and reads more like a taxonomy/position piece.
These may be placeholder or erroneous rows on the page rather than genuine acceptances; treat them
with suspicion and re-check against the final program before investing screening effort in them.

## Included

| # | Title | Paper link | PDF link | Repo link | Topic | Why in scope / concerns |
|---|---|---|---|---|---|---|

## All papers

| # | Title | Decision | Reason |
|---|---|---|---|
