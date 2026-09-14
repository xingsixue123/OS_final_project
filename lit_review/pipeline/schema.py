"""Output validators, the verdict rule, and the markdown renderers.

Every agent output passes through a check here before the driver accepts it; a check
returns a list of human-readable errors that is sent back to the agent verbatim.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

TOPICS = ["llm-inference", "ml-systems", "caching", "storage", "scheduling", "memory",
          "ml-for-systems", "other-userspace"]
DECISIONS = {"included", "out-topic", "out-machine", "out-no-code"}
LEVEL = {"H": 3, "M": 2, "L": 1}
FILTERS = ["H1_open_repo", "H2_no_root", "H3_hardware_fit", "H4_obtainable_deps_data"]


def _load_json(path: Path, errors: list[str]):
    if not path.is_file():
        errors.append(f"{path} does not exist")
        return None
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        errors.append(f"{path} is not valid JSON: {e}")
        return None


# ---------------------------------------------------------------- research shard

def _table_rows(text: str, heading: str) -> list[list[str]]:
    """Data rows of the first markdown table under `## heading`."""
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return []
    rows = [l.strip() for l in m.group(1).splitlines() if l.strip().startswith("|")]
    rows = [r for r in rows if not re.fullmatch(r"\|[\s:|-]+\|", r)]
    return [[c.strip() for c in r.strip("|").split("|")] for r in rows[1:]]  # drop header


def shard_markers(path: Path) -> dict:
    head = path.read_text(errors="replace").splitlines()[:3] if path.is_file() else []
    out = {}
    for line in head:
        m = re.match(r"^(STATUS|TOTAL_PAPERS|INCLUDED):\s*(\S+)\s*$", line.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


def check_shard(path: Path) -> list[str]:
    if not path.is_file():
        return [f"{path} does not exist"]
    mk = shard_markers(path)
    status = mk.get("STATUS")
    if status not in {"complete", "not_yet_published", "not_held"}:
        return ["first line must be `STATUS: complete | not_yet_published | not_held`"]
    if status != "complete":
        return []
    errors = []
    try:
        total, included = int(mk["TOTAL_PAPERS"]), int(mk["INCLUDED"])
    except (KeyError, ValueError):
        return ["lines 2-3 must be `TOTAL_PAPERS: <int>` and `INCLUDED: <int>`"]
    text = path.read_text(errors="replace")
    inc = _table_rows(text, "Included")
    allp = _table_rows(text, "All papers")
    if total <= 0:
        errors.append("TOTAL_PAPERS is 0 but STATUS is complete")
    if len(inc) != included:
        errors.append(f"INCLUDED says {included} but the `## Included` table has {len(inc)} rows")
    if len(allp) != total:
        errors.append(f"TOTAL_PAPERS says {total} but the `## All papers` table has {len(allp)} rows")
    bad_topic = [r[1] for r in inc if len(r) < 7 or r[5] not in TOPICS]
    if bad_topic:
        errors.append(f"Included rows with a wrong column count or a topic not in {TOPICS}: {bad_topic[:5]}")
    bad_dec = [r[1] for r in allp if len(r) < 4 or r[2] not in DECISIONS]
    if bad_dec:
        errors.append(f"All-papers rows with a wrong column count or a decision not in {sorted(DECISIONS)}: {bad_dec[:5]}")
    n_inc = sum(1 for r in allp if len(r) >= 3 and r[2] == "included")
    if not bad_dec and n_inc != included:
        errors.append(f"`## All papers` marks {n_inc} papers as included but INCLUDED is {included}")
    return errors


# ---------------------------------------------------------------- collector

def check_candidates(collect_dir: Path, expected: int, shard_names: set[str]) -> list[str]:
    errors: list[str] = []
    cands = _load_json(collect_dir / "candidates.json", errors)
    rep = collect_dir / "report.md"
    if not rep.is_file():
        errors.append(f"{rep} does not exist")
    if cands is None or errors:
        return errors
    if not isinstance(cands, list):
        return ["candidates.json must be a JSON array"]
    m = re.match(r"^MERGED_DUPLICATES:\s*(\d+)\s*$", rep.read_text().splitlines()[0] if rep.read_text() else "")
    if not m:
        return ["report.md first line must be `MERGED_DUPLICATES: <int>`"]
    merged = int(m.group(1))
    for i, c in enumerate(cands):
        if not isinstance(c, dict):
            errors.append(f"candidate {i} is not an object")
            continue
        for k in ("shard", "title", "paper_url", "pdf_url", "repo_url", "topic", "note"):
            if k not in c:
                errors.append(f"candidate {i} ({c.get('title')!r}) is missing `{k}`")
        if c.get("shard") not in shard_names:
            errors.append(f"candidate {i} ({c.get('title')!r}) has shard {c.get('shard')!r}, not one of the reports")
        if c.get("topic") not in TOPICS:
            errors.append(f"candidate {i} ({c.get('title')!r}) has topic {c.get('topic')!r}, not in {TOPICS}")
        if not str(c.get("title", "")).strip():
            errors.append(f"candidate {i} has an empty title")
    if len(cands) + merged != expected:
        errors.append(f"{len(cands)} candidates + {merged} merged duplicates = {len(cands) + merged}, "
                      f"but the shard reports have {expected} Included rows in total")
    return errors


# ---------------------------------------------------------------- pre-ranker

PRERANK_AXES = ["os_fit", "feasibility", "buildability", "headroom"]


def check_prerank(out_dir: Path, ids: list[str]) -> list[str]:
    errors: list[str] = []
    scores = _load_json(out_dir / "scores.json", errors)
    if scores is None:
        return errors
    if not isinstance(scores, list):
        return ["scores.json must be a JSON array"]
    seen = [s.get("id") for s in scores if isinstance(s, dict)]
    missing, extra = set(ids) - set(seen), set(seen) - set(ids)
    dup = {i for i in seen if seen.count(i) > 1}
    if missing:
        errors.append(f"{len(missing)} input ids have no score, e.g. {sorted(missing)[:5]}")
    if extra:
        errors.append(f"{len(extra)} ids are not in the input, e.g. {sorted(extra)[:5]}")
    if dup:
        errors.append(f"ids scored more than once: {sorted(dup)[:5]}")
    for s in scores:
        if not isinstance(s, dict):
            errors.append("every entry must be an object")
            continue
        for ax in PRERANK_AXES:
            if not isinstance(s.get(ax), int) or not 1 <= s[ax] <= 5:
                errors.append(f"{s.get('id')}: `{ax}` must be an integer 1-5, got {s.get(ax)!r}")
        if not str(s.get("reason", "")).strip():
            errors.append(f"{s.get('id')}: `reason` is empty")
    return errors[:60]


def prerank_key(s: dict) -> tuple:
    """Sort key, best first. A paper weak on feasibility or buildability (<= 2) sinks
    below every paper that is not, whatever its other scores: an ungated favourite
    that cannot be rebuilt here is not worth an audit."""
    total = sum(s[ax] for ax in PRERANK_AXES)
    return (min(s["feasibility"], s["buildability"]) >= 3, total, s["os_fit"], s["headroom"])


def render_prerank(rows: list[dict]) -> str:
    out = ["# Pre-rank", "",
           "Cheap desk scores from title + scout note only (no PDF, no repo) — an ordering for "
           "the audit queue, **not** a gate. Axes 1–5: fit = OS-course fit, feas = fits the machine, "
           "build = artifact completeness, room = incremental-add-on headroom. Papers with feas or "
           "build ≤ 2 are ranked below all others.", "",
           "| # | total | fit | feas | build | room | paper | venue | topic | reason |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        out.append(f"| {i} | {sum(r[a] for a in PRERANK_AXES)} | {r['os_fit']} | {r['feasibility']} | "
                   f"{r['buildability']} | {r['headroom']} | {_cell(r['title'])} (`{r['id']}`) | "
                   f"{r['venue'].upper()} {r['year']} | {r['topic']} | {_cell(r['reason'])} |")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- fetcher

def check_fetch(paper_dir: Path, valid_pdf, valid_repo) -> list[str]:
    errors: list[str] = []
    fr = _load_json(paper_dir / "fetch_result.json", errors)
    if fr is None:
        return errors
    pdf, repo = fr.get("pdf") or {}, fr.get("repo") or {}
    if pdf.get("status") not in {"ok", "not_found"}:
        errors.append("pdf.status must be `ok` or `not_found`")
    if repo.get("status") not in {"ok", "not_found", "not_released"}:
        errors.append("repo.status must be `ok`, `not_found`, or `not_released`")
    if repo.get("status") == "ok" and repo.get("official") not in {"yes", "no", "unclear"}:
        errors.append("repo.official must be `yes`, `no`, or `unclear`")
    if pdf.get("status") == "ok":
        ok, why = valid_pdf(paper_dir / "paper.pdf")
        if not ok:
            errors.append(f"pdf.status is ok but paper.pdf is not a valid paper PDF: {why}")
    if repo.get("status") == "ok":
        ok, why = valid_repo(paper_dir / "repo")
        if not ok:
            errors.append(f"repo.status is ok but repo/ is not usable: {why}")
    return errors


# ---------------------------------------------------------------- auditor

REPORT_HEADINGS = ["## 1. Paper summary", "## 2. Artifact audit", "## 3. Hard filters",
                   "## 4. Reproduction plan", "## 5. Add-on ideas",
                   "## 6. Risks and open questions", "## 7. Evidence index"]


def _enum(errors, where, value, allowed):
    if value not in allowed:
        errors.append(f"{where} is {value!r}; must be one of {sorted(allowed)}")


def check_audit(paper_dir: Path) -> list[str]:
    audit, repo = paper_dir / "audit", paper_dir / "repo"
    errors: list[str] = []
    rep = audit / "report.md"
    if not rep.is_file():
        errors.append(f"{rep} does not exist")
    else:
        text = rep.read_text(errors="replace")
        errors += [f"report.md is missing the heading `{h}`" for h in REPORT_HEADINGS if h not in text]
    s = _load_json(audit / "summary.json", errors)
    if not isinstance(s, dict):
        return errors + ([] if s is None else ["summary.json must be a JSON object"])

    for k in ("title", "one_line", "topic", "repo", "hard_filters", "reproduce", "addons", "risks"):
        if k not in s:
            errors.append(f"summary.json is missing `{k}`")
    if errors:
        return errors
    try:
        return _check_summary_fields(s, repo, errors)
    except (AttributeError, TypeError, KeyError) as e:
        return errors + [f"summary.json does not have the documented shape ({e!r})"]


def _check_summary_fields(s: dict, repo: Path, errors: list[str]) -> list[str]:
    _enum(errors, "topic", s["topic"], set(TOPICS))
    _enum(errors, "repo.official", s["repo"].get("official"), {"yes", "no", "unclear"})
    badges = s["repo"].get("artifact_badges")
    if not isinstance(badges, list) or not set(badges) <= {"available", "functional", "reproduced"}:
        errors.append("repo.artifact_badges must be a list drawn from available/functional/reproduced")
    for f in FILTERS:
        hf = s["hard_filters"].get(f)
        if not isinstance(hf, dict):
            errors.append(f"hard_filters.{f} is missing")
            continue
        _enum(errors, f"hard_filters.{f}.result", hf.get("result"), {"pass", "fail", "unclear"})
        if not str(hf.get("evidence", "")).strip():
            errors.append(f"hard_filters.{f}.evidence is empty")
    rp = s["reproduce"]
    _enum(errors, "reproduce.level", rp.get("level"), set(LEVEL))
    for k in ("target", "scale_down", "effort", "rationale"):
        if not str(rp.get(k, "")).strip():
            errors.append(f"reproduce.{k} is empty")
    addons = s["addons"]
    if not isinstance(addons, list) or not 2 <= len(addons) <= 5:
        errors.append("addons must be a list of 2-5 add-ons")
        addons = addons if isinstance(addons, list) else []
    for i, a in enumerate(addons):
        w = f"addons[{i}]"
        for k in ("name", "hypothesis", "mechanism", "motivating_evidence",
                  "feasibility_rationale", "research_value_rationale"):
            if not str(a.get(k, "")).strip():
                errors.append(f"{w}.{k} is empty")
        _enum(errors, f"{w}.feasibility", a.get("feasibility"), set(LEVEL))
        _enum(errors, f"{w}.research_value", a.get("research_value"), set(LEVEL))
        sc = a.get("scoop_check") or {}
        _enum(errors, f"{w}.scoop_check.result", sc.get("result"), {"clear", "partial", "scooped", "not_checked"})
        locs = a.get("code_locations")
        if not isinstance(locs, list) or not locs:
            errors.append(f"{w}.code_locations must be a non-empty list of repo paths")
            continue
        for loc in locs:
            rel = re.sub(r":\d+(-\d+)?$", "", str(loc).strip()).lstrip("/")
            target = (repo / rel).resolve()
            if not rel or not target.is_relative_to(repo.resolve()) or not target.exists():
                errors.append(f"{w}.code_locations entry {loc!r} does not exist under repo/")
    return errors


def verdict(s: dict) -> tuple[str, str, int]:
    """(verdict, reason, best add-on score). The single place the rubric's rule lives."""
    failed = [f for f in FILTERS if s["hard_filters"][f]["result"] == "fail"]
    unclear = [f for f in FILTERS if s["hard_filters"][f]["result"] == "unclear"]
    repro = LEVEL[s["reproduce"]["level"]]
    best = max((LEVEL[a["feasibility"]] * LEVEL[a["research_value"]] for a in s["addons"]
                if a["scoop_check"]["result"] != "scooped"), default=0)
    if failed:
        return "reject", "failed " + ", ".join(failed), best
    if not unclear and repro >= 2 and best >= 6:
        return "shortlist", "", best
    if repro >= 2 and best >= 4:
        return "maybe", ("unclear " + ", ".join(unclear)) if unclear else "", best
    return "reject", f"reproduce={s['reproduce']['level']}, best add-on score={best}", best


# ---------------------------------------------------------------- renderers

def _cell(x) -> str:
    return str(x if x is not None else "").replace("|", "/").replace("\n", " ")


def _link(url, label) -> str:
    return f"[{label}]({url})" if isinstance(url, str) and url.startswith("http") else "—"


def render_list(papers: list[dict]) -> str:
    out = [f"# Candidate papers ({len(papers)})", ""]
    for topic in TOPICS:
        group = [p for p in papers if p["topic"] == topic]
        if not group:
            continue
        out += [f"## {topic} ({len(group)})", "",
                "| id | title | venue | paper | pdf | repo | note |", "|---|---|---|---|---|---|---|"]
        for p in sorted(group, key=lambda p: (p["venue"], p["year"], p["title"])):
            out.append(f"| `{p['id']}` | {_cell(p['title'])} | {p['venue'].upper()} {p['year']} | "
                       f"{_link(p['paper_url'], 'page')} | {_link(p['pdf_url'], 'pdf')} | "
                       f"{_link(p['repo_url'], 'repo')} | {_cell(p['note'])} |")
        out.append("")
    return "\n".join(out)


def render_ranking(rows: list[dict], others: list[dict]) -> str:
    order = {"shortlist": 0, "maybe": 1, "reject": 2}
    rows = sorted(rows, key=lambda r: (order[r["verdict"]], -r["best"],
                                       -LEVEL[r["s"]["reproduce"]["level"]], r["id"]))
    out = ["# Ranking", "",
           "Verdict and ordering are computed from each `audit/summary.json` by the rule in "
           "`pipeline/rubric.md` §4. Levels: reproduction H/M/L; add-on F = feasibility, "
           "RV = research value.", "",
           f"Audited: {len(rows)} — shortlist {sum(r['verdict'] == 'shortlist' for r in rows)}, "
           f"maybe {sum(r['verdict'] == 'maybe' for r in rows)}, "
           f"reject {sum(r['verdict'] == 'reject' for r in rows)}.", "",
           "| # | verdict | paper | venue | topic | repro | best add-on (F/RV, scoop) | note |",
           "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        s = r["s"]
        live = [a for a in s["addons"] if a["scoop_check"]["result"] != "scooped"] or s["addons"]
        top = max(live, key=lambda a: LEVEL[a["feasibility"]] * LEVEL[a["research_value"]])
        out.append(
            f"| {i} | **{r['verdict']}** | [{_cell(s['title'])}](papers/{r['id']}/audit/report.md) | "
            f"{r['venue'].upper()} {r['year']} | {s['topic']} | {s['reproduce']['level']} | "
            f"{_cell(top['name'])} ({top['feasibility']}/{top['research_value']}, {top['scoop_check']['result']}) | "
            f"{_cell(r['reason'])} |")
    pending = [o for o in others if o["status"] == "pending"]
    others = [o for o in others if o["status"] != "pending"]
    if pending:
        out += ["", f"{len(pending)} papers in the list have not been processed yet (see `prerank.md` for their order)."]
    if others:
        out += ["", "## Processed but not audited", "", "| paper | venue | status | detail |", "|---|---|---|---|"]
        for o in sorted(others, key=lambda o: (o["status"], o["id"])):
            out.append(f"| {_cell(o['title'])} (`{o['id']}`) | {o['venue'].upper()} {o['year']} | "
                       f"{o['status']} | {_cell(o['detail'])} |")
    return "\n".join(out) + "\n"
