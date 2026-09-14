# lit_review

Finds candidate papers for the OS course project (see `scope.md`) and audits each one
for "can we rebuild it on this machine, and what could we add on top?".

```bash
./lr run          # everything, resumable — safe to Ctrl+C and re-run
./lr status       # progress
```

Final outputs: `paper_list.md` (the rough list) and `ranking.md` (audited, ranked, each
row linking to `papers/<id>/audit/report.md`).

## Pipeline

| stage | command | agents | writes | tools |
|---|---|---|---|---|
| deep research | `./lr research` | 1 scout per venue-year (13 venues × 4 years = 52), `concurrency` in parallel | `research/<venue>-<year>/report.md` | web + shell (curl for full program pages) |
| collect | `./lr collect` | 1 collector | `collect/candidates.json` → driver writes `paper_list.json` / `paper_list.md` | files only |
| per paper, one at a time | `./lr papers` | fresh agents per paper | `papers/<id>/` | see below |
| rank | `./lr rank` (also runs after `papers`) | none | `ranking.md` | — |

Per paper (`papers/<id>/`):

0. `mkdir`, `meta.json` = the list entry.
1. `paper.pdf` — the driver tries the list's PDF/arXiv link with curl.
2. `repo/` — the driver tries `git clone --depth 1` of the list's repo link.
   If 1 or 2 fails, a **fetch agent** (shell + web, writes only this dir, told not to
   build anything) finds the official PDF / repo and writes `fetch_result.json`. The
   driver verifies its claims (real PDF, non-empty repo). No PDF ⇒ `no_pdf`; no official
   code ⇒ `no_repo`; neither is audited.
   The driver then writes `paper.txt` (page-marked text), `pages/` (page images) and `repo_facts.json` (head
   commit date, size, languages, build files, GitHub stars/license, and grep **red
   flags** for everything `pipeline/env.md` rules out).
3. **Audit agent** — reads paper + repo, scores with `pipeline/rubric.md`, writes
   `audit/report.md` and `audit/summary.json`.

## What is enforced in code, not in prompts

- **Audit only, no experiments** — three layers, because one was measured to leak:
  1. the auditor (and collector) get `--tools Read,Write,Edit,Grep,Glob,WebSearch,WebFetch`
     plus a `--disallowedTools` list of every shell/agent-spawning tool;
  2. **kernel:** their sandbox overlays every shell binary (`sh`, `bash`, `dash`, `zsh`,
     `busybox`, …) with `/dev/null`, so nothing can spawn a shell — this matters because
     in testing, `--tools` alone did not stop the deferred `Monitor` tool from running
     `find` over `$HOME`;
  3. **transcript audit:** after every run the driver scans the session transcript; any
     tool outside the role's list that actually executed fails that agent outright
     (`.agents/<agent>/tool_violations.json`).

  Web access is for the scoop check (has someone already done this add-on?). Since
  page-wise PDF reading needs a shell, the driver renders `papers/<id>/pages/page-NN.png`
  for the auditor to look at figures.
- **Write confinement.** Every agent runs in `bwrap` with the whole filesystem
  read-only except its own output directory (the auditor: only `papers/<id>/audit/`; it
  cannot even modify the repo it reads).
- **Nothing declares itself finished.** Every output is validated by
  `pipeline/schema.py`; errors are sent back into the same session (`max_fix_rounds`):
  - scout: `TOTAL_PAPERS`/`INCLUDED` must equal the table row counts, and every
    enumerated paper needs a decision row — coverage of the whole program is checked;
  - collector: `candidates + merged duplicates == sum of Included rows`;
  - fetcher: `status: ok` must correspond to a real PDF / non-empty repo;
  - auditor: full schema, enum values, required report sections, and **every
    `code_locations` path must exist in the repo**.
- **Verdict is computed, not chosen.** `shortlist / maybe / reject` comes from
  `summary.json` by the rule in `rubric.md` §4 (`schema.verdict`), identically for
  every paper.
- **Credentials.** Each agent's config dir holds a *symlink* to `~/.claude/.credentials.json`
  (read-only in the sandbox), not a bind mount of the file: an OAuth refresh replaces the file,
  and a file bind mount keeps the old revoked token (every agent running across a refresh died
  with 401). Agents cannot refresh the ~8 h token themselves, so the driver runs a keepalive
  thread that makes one tiny unsandboxed `claude -p` call when < 1 h remains.
- **Crash ≠ verdict.** A crashed/timed-out agent is retried from a fresh session
  (`max_crash_retries`), never shown its harness error as if it were feedback.

## Useful commands

```bash
./lr research --only osdi-2024 fast-2025     # some venue-years
./lr research --only osdi-2024 --force       # redo one
./lr papers --limit 5                        # next 5 papers
./lr papers --only <id> --force              # re-audit one (keeps pdf/repo)
./lr add --title "..." --venue osdi --year 2024 --topic storage \
         --repo-url https://github.com/x/y --pdf-url https://...   # add a paper by hand
./lr --workdir /some/scratch --config mini.json research          # try things without touching the real outputs
```

Only one `lr` may run per workdir at a time (`.lr.lock`). Each agent's final result
and cost is in `.agents/<agent>/log-*.json`, its full transcript in
`.agents/<agent>/cfg/projects/*/<session>.jsonl`; the driver log is `lr.log`.

## Tuning

`config.json`: model and effort (global, or per stage by adding `"model"` /
`"effort"` inside a stage), years, venues, per-stage `concurrency` and timeouts.
`stages.audit.concurrency` is 1 ("one by one"); papers are independent, so raising it
is safe if throughput matters. `scope.md` (topics, venues, hard requirement) and
`pipeline/rubric.md` are given verbatim to the agents — edit them to change judgement.

## Layout

```
lr, config.json, scope.md      entry point and the two files you are expected to edit
pipeline/
  lr.py        driver (stages, retry/fix loop, per-paper steps)
  sandbox.py   bwrap + `claude -p` wrapper (prompt on stdin, per-role tool list)
  fetch.py     deterministic PDF / clone / text extraction / repo facts
  schema.py    validators, verdict rule, markdown renderers
  env.md       measured machine capability sheet (given to every agent)
  rubric.md    scoring rules (given to the auditor)
  prompts/     research.md, collect.md, fetch.md, audit.md
research/  collect/  papers/  paper_list.{json,md}  ranking.md  lr.log  .agents/   (generated)
```
