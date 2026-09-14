# Scoring rubric

The audit is **desk review only**: read the paper and the repository. Nothing is built,
installed, or run. Every judgement is therefore a prediction, and must be backed by
evidence you can point at — a paper section/figure/table, or a repository path.
"unclear" is always an allowed answer; a confident guess is not.

## 1. Hard filters

Each is `pass`, `fail`, or `unclear`, with evidence. Any `fail` ⇒ the paper is rejected.
Any `unclear` caps the paper at "maybe".

| id | passes when |
|---|---|
| `H1_open_repo` | The repository is the **official** implementation (linked from the paper, artifact page, or authors' org/account), and it contains the actual system — not a placeholder, "code coming soon", a binary-only release, or only plotting scripts. |
| `H2_no_root` | The core system and its evaluation run without root: no custom kernel, kernel module, eBPF, perf counters, KVM, `/proc/sys` or hugepage setup that cannot be skipped or substituted. A Dockerfile is **not** a fail if its steps can be replayed with conda/pip (say so). |
| `H3_hardware_fit` | The headline mechanism can be exercised on 1 × 24 GB Ampere GPU / 16 cores / 125 GB RAM / ~250 GB free disk / one machine — at the paper's scale, or at a scale-down that still tests the paper's claim. Multi-node or multi-GPU evaluations pass only if a meaningful single-node scale-down exists. |
| `H4_obtainable_deps_data` | Dependencies are installable in user space, and the datasets / traces / model weights used in the evaluation are publicly downloadable (or a public substitute is named in the repo/paper). Proprietary production traces with no public substitute ⇒ fail. |

## 2. Reproduction feasibility — `H` / `M` / `L`

How confident are we that the team can reproduce **one headline result** (name the
specific figure or table) in the first ~2 weeks?

- **H** — build instructions and evaluation scripts exist for that result; dependencies
  are current; it fits the machine at paper scale or a documented scale-down; artifact
  badge "Results Reproduced" or equivalent evidence helps.
- **M** — reproducible with real porting work: Docker→conda, older CUDA/PyTorch pins,
  missing plotting scripts, scaling the workload down, re-deriving a config from the
  paper.
- **L** — major pieces missing (eval harness, baselines, data), dependencies abandoned
  or unbuildable, or the result only makes sense at a scale this machine cannot approach.

Also give: the scale-down you would use, and an effort estimate (person-days +
compute hours).

## 3. Incremental add-ons

Propose **2–5** add-ons. Each is a research hypothesis, not a feature request:

> We hypothesize that **X** improves **Y** (a measurable metric) under **Z** (a workload
> or regime), compared with the paper's system.

For each add-on give:

- `mechanism` — what changes in the design, concretely.
- `code_locations` — the repository files (and optionally `:line`) where it plugs in.
  Paths are relative to the repository root and **are checked to exist**.
- `motivating_evidence` — the paper's own stated limitation, an unexplored workload, a
  figure where the system degrades, a simplifying assumption, etc.
- `feasibility` — `H` / `M` / `L`:
  - **H** — localized change (roughly ≤ ~1–2k LOC touching a few modules), evaluable with
    the existing harness on this machine, clearly doable by 2–4 students in ~10 weeks.
  - **M** — cross-cutting change, or needs a new evaluation harness / workload
    generator, or eval compute is heavy but still fits.
  - **L** — needs a redesign, root, hardware we lack, or eval we cannot afford.
- `research_value` — `H` / `M` / `L`:
  - **H** — a reviewer at the original venue would care: addresses a real limitation or
    an important regime the paper ignores, and either outcome (works / fails) teaches
    something.
  - **M** — a solid but expected improvement, or a regime of moderate interest.
  - **L** — parameter tuning, engineering polish, porting, or a result nobody would be
    surprised by.
- `scoop_check` — search for follow-up work that already does this (papers citing the
  original; Semantic Scholar / Google Scholar / arXiv). `result` is `clear` (nothing
  found), `partial` (related but not the same), `scooped` (already done — give the link),
  or `not_checked`. A scooped add-on does not count toward the verdict.

Calibrate honestly. An H/H add-on should be rare; most real ideas are M on at least one
axis. Inflated scores make the ranking useless.

## 4. Verdict (computed by the driver, not by you)

With H=3, M=2, L=1 and `best` = the highest feasibility × research_value over
non-scooped add-ons:

- **reject** — any hard filter `fail`
- **shortlist** — no hard filter `unclear`, reproduction ≥ M, and `best` ≥ 6 (i.e. an
  add-on rated H/M, M/H, or H/H)
- **maybe** — reproduction ≥ M and `best` ≥ 4
- **reject** — otherwise
