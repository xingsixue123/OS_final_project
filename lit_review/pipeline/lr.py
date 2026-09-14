#!/usr/bin/env python3
"""lit_review driver. See ../README.md.

    lr research   one scout agent per venue-year      -> research/<venue>-<year>/report.md
    lr collect    one collector agent                 -> paper_list.json, paper_list.md
    lr papers     per paper, one at a time:
                    0 mkdir papers/<id>/
                    1 paper.pdf   (driver curl; fetch agent if that fails)
                    2 repo/       (driver git clone; fetch agent if that fails)
                    3 audit agent, no shell           -> papers/<id>/audit/{report.md,summary.json}
    lr rank       deterministic                        -> ranking.md
    lr run        all of the above, resumable
    lr status     progress counts
    lr add        put a paper into the list by hand

Every stage is resumable: finished, validated outputs are skipped on re-run.
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import shutil
import sys
import threading
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import fetch  # noqa: E402
import sandbox  # noqa: E402
import schema  # noqa: E402

TOOLS = {  # the security property of each role lives here, not in config
    "research": ["Bash", "Read", "Write", "Edit", "Grep", "Glob", "WebSearch", "WebFetch"],
    "collect": ["Read", "Write", "Edit", "Grep", "Glob"],
    "prerank": ["Read", "Write", "Edit"],
    "fetch": ["Bash", "Read", "Write", "Grep", "Glob", "WebSearch", "WebFetch"],
    "audit": ["Read", "Write", "Edit", "Grep", "Glob", "WebSearch", "WebFetch"],
}
TERMINAL = {"audited", "no_repo", "no_pdf"}

FIX_PROMPT = """The driver checked your outputs and they are not acceptable yet:

{errors}

Fix exactly these problems in place (same output paths), then finish."""

_lock = threading.Lock()


class WS:
    def __init__(self, root: Path):
        self.root = root
        self.research = root / "research"
        self.collect = root / "collect"
        self.papers = root / "papers"
        self.agents = root / ".agents"
        self.list_json = root / "paper_list.json"
        self.list_md = root / "paper_list.md"
        self.manual = root / "manual_papers.json"
        self.ranking = root / "ranking.md"
        self.logfile = root / "lr.log"


def log(ws: WS, msg: str):
    line = f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    with _lock:
        print(line, flush=True)
        ws.root.mkdir(parents=True, exist_ok=True)
        with open(ws.logfile, "a") as f:
            f.write(line + "\n")


def fill(template: str, **kw) -> str:
    for k, v in kw.items():
        template = template.replace("{{" + k + "}}", str(v))
    left = re.findall(r"\{\{[A-Z_]+\}\}", template)
    if left:
        raise ValueError(f"unfilled placeholders: {left}")
    return template


def system_prompt(role: str, **kw) -> str:
    parts = [(ROOT / "scope.md").read_text(), (HERE / "env.md").read_text()]
    if role == "audit":
        parts.append((HERE / "rubric.md").read_text())
    parts.append(fill((HERE / "prompts" / f"{role}.md").read_text(), **kw))
    return "\n\n---\n\n".join(parts)


def tool_violations(cfg_dir: Path, session_id: str, allowed: list[str]) -> list[str]:
    """Tool calls outside the role's list that the harness actually executed.

    Belt-and-braces for the kernel no-shell sandbox: --tools alone has been observed to
    let a deferred tool (Monitor) run. A refused call (is_error) is harmless.
    """
    path = sandbox.transcript_path(cfg_dir, session_id)
    if not path:
        return []
    calls, errored = {}, set()
    for line in path.read_text(errors="replace").splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = (ev.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use" and c.get("name") not in allowed:
                calls[c.get("id")] = f"{c.get('name')} {json.dumps(c.get('input'))[:200]}"
            elif c.get("type") == "tool_result" and c.get("is_error"):
                errored.add(c.get("tool_use_id"))
    return [desc for tid, desc in calls.items() if tid not in errored]


def call_agent(ws: WS, cfg: dict, *, name: str, role: str, rw: list[Path], chdir: Path,
               validate, **kw) -> list[str]:
    """Run one sandboxed agent until `validate()` returns no errors.

    Invalid output -> resume the same session with the errors (max_fix_rounds).
    A crash or timeout is not a verdict: it is retried from a fresh session
    (max_crash_retries) and never fed back as if it were a defect list.
    A non-allowed tool that executed fails the agent outright, with no retry.
    Returns the remaining errors ([] on success).
    """
    stage = cfg["stages"][role]
    adir = ws.agents / name
    cfg_dir = sandbox.make_config_dir(adir)
    sysp = system_prompt(role, **kw)
    first = "Do the task described at the end of your system prompt. Start now."
    sid, resume, msg = sandbox.new_session_id(), False, first
    crashes = fixes = 0
    n = len(list(adir.glob("log-*.json")))
    while True:
        n += 1
        log(ws, f"{name}: agent start ({'fix round ' + str(fixes) if resume else 'fresh session'})")
        rc, _, data = sandbox.run_agent(
            prompt=msg, system_prompt=sysp, tools=TOOLS[role], rw_paths=rw, ro_paths=[ws.root],
            cfg_dir=cfg_dir, chdir=chdir, model=stage.get("model", cfg["model"]),
            effort=stage.get("effort", cfg["effort"]), log_path=adir / f"log-{n}.json",
            session_id=sid, resume=resume, timeout=stage["timeout_seconds"])
        cost = (data or {}).get("total_cost_usd")
        crashed = rc != 0 or data is None or data.get("is_error")
        # a role that has Bash may also use the other shell tools (Monitor etc.): same power
        allowed = TOOLS[role] + (sandbox.SHELL_TOOLS if "Bash" in TOOLS[role] else [])
        bad = tool_violations(cfg_dir, sid, allowed)
        if bad:
            (adir / "tool_violations.json").write_text(json.dumps(bad, indent=2) + "\n")
            log(ws, f"{name}: executed tools outside its role: {bad}")
            return [f"agent executed tools outside its role ({len(bad)}); see {adir}/tool_violations.json"]
        if crashed:
            crashes += 1
            reason = str((data or {}).get("result", ""))[:160].replace("\n", " ")
            log(ws, f"{name}: agent crashed/timed out (rc={rc}) {reason!r}, log {adir}/log-{n}.json")
            if crashes > cfg["max_crash_retries"]:
                return [f"agent crashed {crashes} times; logs in {adir}"]
            sid, resume, msg = sandbox.new_session_id(), False, first
            continue
        errors = validate()
        log(ws, f"{name}: agent done (cost ${cost}), {len(errors)} validation errors")
        if not errors:
            return []
        if fixes >= cfg["max_fix_rounds"]:
            return errors
        fixes += 1
        resume, msg = True, FIX_PROMPT.format(errors="\n".join(f"- {e}" for e in errors[:40]))


# ================================================================ research

def shards(cfg: dict) -> list[tuple[str, dict, int]]:
    return [(f"{v['key']}-{y}", v, y) for v in cfg["venues"] for y in v.get("years", cfg["years"])]


def stage_research(ws: WS, cfg: dict, only=None, force=False) -> bool:
    todo = []
    for name, venue, year in shards(cfg):
        if only and name not in only:
            continue
        rep = ws.research / name / "report.md"
        if force:
            rep.unlink(missing_ok=True)
        if schema.check_shard(rep):
            todo.append((name, venue, year))
    log(ws, f"research: {len(todo)} venue-years to screen")

    def one(item):
        name, venue, year = item
        out = ws.research / name
        errs = call_agent(ws, cfg, name=f"research-{name}", role="research", rw=[out], chdir=out,
                          validate=lambda: schema.check_shard(out / "report.md"),
                          VENUE_NAME=venue["name"], YEAR=year, NOTE=venue.get("note", ""),
                          OUT_DIR=out, TODAY=dt.date.today().isoformat())
        log(ws, f"research-{name}: {'OK ' + str(schema.shard_markers(out / 'report.md')) if not errs else 'FAILED: ' + '; '.join(errs)}")
        return not errs

    with cf.ThreadPoolExecutor(cfg["stages"]["research"]["concurrency"]) as pool:
        results = list(pool.map(one, todo))
    return all(results)


# ================================================================ collect

def slug(text: str, n: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:n].rstrip("-") or "paper"


def build_list(ws: WS, cfg: dict) -> list[dict]:
    """candidates.json (+ manual additions) -> paper_list.json with stable ids."""
    cands = json.loads((ws.collect / "candidates.json").read_text()) if (ws.collect / "candidates.json").is_file() else []
    manual = json.loads(ws.manual.read_text()) if ws.manual.is_file() else []
    papers, seen = [], set()
    for c in cands + manual:
        venue, year = (c["venue"], int(c["year"])) if "venue" in c else (c["shard"].rsplit("-", 1)[0], int(c["shard"].rsplit("-", 1)[1]))
        base = f"{slug(venue, 12)}{year % 100:02d}-{slug(c['title'])}"
        pid, k = base, 2
        while pid in seen:
            pid, k = f"{base}-{k}", k + 1
        seen.add(pid)
        papers.append({"id": pid, "title": c["title"].strip(), "venue": venue, "year": year,
                       "paper_url": c.get("paper_url"), "pdf_url": c.get("pdf_url"),
                       "repo_url": c.get("repo_url"), "topic": c.get("topic", "other-userspace"),
                       "note": c.get("note", "")})
    ws.list_json.write_text(json.dumps(papers, indent=2) + "\n")
    ws.list_md.write_text(schema.render_list(papers))
    return papers


def stage_collect(ws: WS, cfg: dict, force=False) -> bool:
    names = [n for n, _, _ in shards(cfg)]
    bad = [n for n in names if schema.check_shard(ws.research / n / "report.md")]
    if bad:
        log(ws, f"collect: {len(bad)} research shards are missing or invalid ({', '.join(bad[:8])}...); run `lr research` first")
        return False
    complete = [n for n in names if schema.shard_markers(ws.research / n / "report.md")["STATUS"] == "complete"]
    expected = sum(int(schema.shard_markers(ws.research / n / "report.md")["INCLUDED"]) for n in complete)
    validate = lambda: schema.check_candidates(ws.collect, expected, set(complete))  # noqa: E731
    if force:
        shutil.rmtree(ws.collect, ignore_errors=True)
    if validate():
        shard_list = "\n".join(f"- `{ws.research / n / 'report.md'}`" for n in complete)
        errs = call_agent(ws, cfg, name="collect", role="collect", rw=[ws.collect], chdir=ws.collect,
                          validate=validate, SHARD_LIST=shard_list, EXPECTED=expected, OUT_DIR=ws.collect)
        if errs:
            log(ws, "collect: FAILED: " + "; ".join(errs))
            return False
    papers = build_list(ws, cfg)
    log(ws, f"collect: {len(papers)} papers -> {ws.list_md}")
    return True


# ================================================================ prerank

def stage_prerank(ws: WS, cfg: dict, force=False) -> bool:
    """Cheap scores for every listed paper (title + scout note only), to order the audit queue.

    Papers are shuffled with a fixed seed before batching, so every batch mixes venues and
    topics and one batch's calibration drift cannot sink a whole venue.
    """
    import random
    if not ws.list_json.is_file():
        log(ws, "prerank: no paper_list.json; run `lr collect` first")
        return False
    papers = json.loads(ws.list_json.read_text())
    stage = cfg["stages"]["prerank"]
    order = sorted(papers, key=lambda p: p["id"])
    random.Random(20260914).shuffle(order)
    size = stage["batch_size"]
    batches = [order[i:i + size] for i in range(0, len(order), size)]
    pdir = ws.root / "prerank"
    if force:
        shutil.rmtree(pdir, ignore_errors=True)
    keys = ("id", "title", "venue", "year", "topic", "paper_url", "pdf_url", "repo_url", "note")

    def one(item):
        k, batch = item
        out = pdir / f"batch-{k:02d}"
        out.mkdir(parents=True, exist_ok=True)
        inp = out / "input.json"
        want = [{key: p.get(key) for key in keys} for p in batch]
        if not inp.is_file() or json.loads(inp.read_text()) != want:  # list changed -> rescore
            inp.write_text(json.dumps(want, indent=2) + "\n")
            (out / "scores.json").unlink(missing_ok=True)
        ids = [p["id"] for p in batch]
        validate = lambda: schema.check_prerank(out, ids)  # noqa: E731
        if not validate():
            return True
        errs = call_agent(ws, cfg, name=f"prerank-{k:02d}", role="prerank", rw=[out], chdir=out,
                          validate=validate, BATCH=k, INPUT=inp, N=len(batch), OUT_DIR=out)
        if errs:
            log(ws, f"prerank-{k:02d}: FAILED: " + "; ".join(errs[:5]))
        return not errs

    log(ws, f"prerank: {len(papers)} papers in {len(batches)} batches")
    with cf.ThreadPoolExecutor(stage["concurrency"]) as pool:
        ok = all(pool.map(one, enumerate(batches, 1)))
    if not ok:
        return False
    by_id = {p["id"]: p for p in papers}
    rows = []
    for k in range(1, len(batches) + 1):
        for s in json.loads((pdir / f"batch-{k:02d}" / "scores.json").read_text()):
            rows.append({**by_id[s["id"]], **{a: s[a] for a in schema.PRERANK_AXES}, "reason": s["reason"]})
    rows.sort(key=schema.prerank_key, reverse=True)
    (ws.root / "prerank.json").write_text(json.dumps(rows, indent=2) + "\n")
    (ws.root / "prerank.md").write_text(schema.render_prerank(rows))
    log(ws, f"prerank: {len(rows)} papers scored -> {ws.root / 'prerank.md'}")
    return True


# ================================================================ papers

def read_status(d: Path) -> dict:
    try:
        return json.loads((d / "status.json").read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def write_status(d: Path, status: str, detail: str = ""):
    (d / "status.json").write_text(json.dumps(
        {"status": status, "detail": detail, "updated": dt.datetime.now().isoformat(timespec="seconds")}, indent=2) + "\n")


def process_paper(ws: WS, cfg: dict, p: dict, force=False):
    d = ws.papers / p["id"]
    if force:
        shutil.rmtree(d / "audit", ignore_errors=True)
        (d / "status.json").unlink(missing_ok=True)
    # step 0
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(json.dumps(p, indent=2) + "\n")
    tag = f"paper {p['id']}"

    # steps 1-2: deterministic first
    tried = []
    pdf_ok, _ = fetch.valid_pdf(d / "paper.pdf")
    if not pdf_ok:
        pdf_ok, t = fetch.try_pdf(p, d / "paper.pdf")
        tried += t
    repo_ok, _ = fetch.valid_repo(d / "repo")
    if not repo_ok:
        repo_ok, t = fetch.try_clone(p.get("repo_url"), d / "repo")
        tried += t
    fr_path = d / "fetch_result.json"
    if pdf_ok and repo_ok and not fr_path.is_file():
        fr_path.write_text(json.dumps({
            "pdf": {"status": "ok", "source_url": p.get("pdf_url") or p.get("paper_url"), "version": "from list", "notes": ""},
            "repo": {"status": "ok", "url": p.get("repo_url"), "official": "unclear",
                     "evidence": "link taken from the research list; not independently verified"}}, indent=2) + "\n")
    elif not (pdf_ok and repo_ok):
        log(ws, f"{tag}: driver fetch incomplete ({'; '.join(tried)}); spawning fetch agent")
        fr_path.unlink(missing_ok=True)
        missing = " and ".join(x for x, ok in (("the PDF", pdf_ok), ("the repository", repo_ok)) if not ok)
        errs = call_agent(ws, cfg, name=f"fetch-{p['id']}", role="fetch", rw=[d], chdir=d,
                          validate=lambda: schema.check_fetch(d, fetch.valid_pdf, fetch.valid_repo),
                          TITLE=p["title"], VENUE=p["venue"].upper(), YEAR=p["year"],
                          PAPER_URL=p.get("paper_url"), PDF_URL=p.get("pdf_url"), REPO_URL=p.get("repo_url"),
                          TRIED="\n".join(f"- {t}" for t in tried) or "- nothing", PAPER_DIR=d, MISSING=missing)
        if errs:
            write_status(d, "fetch_failed", "; ".join(errs))
            log(ws, f"{tag}: fetch FAILED")
            return
        fr = json.loads(fr_path.read_text())
        if not fetch.valid_pdf(d / "paper.pdf")[0]:
            write_status(d, "no_pdf", fr["pdf"].get("notes", ""))
            log(ws, f"{tag}: no PDF obtainable")
            return
        if not fetch.valid_repo(d / "repo")[0]:
            write_status(d, "no_repo", f"{fr['repo'].get('status')}: {fr['repo'].get('evidence', '')}")
            log(ws, f"{tag}: no official repo ({fr['repo'].get('status')})")
            return

    if not (d / "paper.txt").is_file():
        fetch.extract_text(d / "paper.pdf", d / "paper.txt")
    if not (d / "pages").is_dir():
        fetch.render_pages(d / "paper.pdf", d / "pages")
    if not (d / "repo_facts.json").is_file():
        url = json.loads(fr_path.read_text())["repo"].get("url") or p.get("repo_url")
        (d / "repo_facts.json").write_text(json.dumps(fetch.repo_facts(d / "repo", url), indent=2) + "\n")

    # step 3
    audit = d / "audit"
    if schema.check_audit(d):
        errs = call_agent(ws, cfg, name=f"audit-{p['id']}", role="audit", rw=[audit], chdir=audit,
                          validate=lambda: schema.check_audit(d),
                          TITLE=p["title"], PAPER_DIR=d, AUDIT_DIR=audit)
        if errs:
            write_status(d, "audit_failed", "; ".join(errs[:10]))
            log(ws, f"{tag}: audit FAILED")
            return
    v, reason, best = schema.verdict(json.loads((audit / "summary.json").read_text()))
    write_status(d, "audited", f"{v} {reason}".strip())
    log(ws, f"{tag}: audited -> {v} {reason}")


def stage_papers(ws: WS, cfg: dict, only=None, limit=None, force=False, top=None) -> bool:
    if not ws.list_json.is_file():
        log(ws, "papers: no paper_list.json; run `lr collect` (or `lr add`) first")
        return False
    papers = json.loads(ws.list_json.read_text())
    if top:
        pr = ws.root / "prerank.json"
        if not pr.is_file():
            log(ws, "papers: --top needs prerank.json; run `lr prerank` first")
            return False
        only = (only or []) + [r["id"] for r in json.loads(pr.read_text())[:top]]
        rank = {pid: i for i, pid in enumerate(only)}
        papers = sorted(papers, key=lambda p: rank.get(p["id"], len(rank)))
    if only:
        unknown = set(only) - {p["id"] for p in papers}
        if unknown:
            log(ws, f"papers: unknown ids {sorted(unknown)}")
            return False
        papers = [p for p in papers if p["id"] in only]
    todo = [p for p in papers if force or read_status(ws.papers / p["id"]).get("status") not in TERMINAL]
    if limit:
        todo = todo[:limit]
    log(ws, f"papers: {len(todo)} to process ({len(papers) - len(todo)} already done or not selected)")
    with cf.ThreadPoolExecutor(cfg["stages"]["audit"]["concurrency"]) as pool:
        for fut in [pool.submit(process_paper, ws, cfg, p, force) for p in todo]:
            try:
                fut.result()
            except Exception as e:  # noqa: BLE001 -- one broken paper must not stop the list
                log(ws, f"papers: driver error: {e!r}")
    stage_rank(ws, cfg)
    return True


# ================================================================ rank / status / add

def stage_rank(ws: WS, cfg: dict):
    papers = json.loads(ws.list_json.read_text()) if ws.list_json.is_file() else []
    rows, others = [], []
    for p in papers:
        d = ws.papers / p["id"]
        st = read_status(d)
        if st.get("status") == "audited" and not schema.check_audit(d):
            s = json.loads((d / "audit" / "summary.json").read_text())
            v, reason, best = schema.verdict(s)
            rows.append({**p, "s": s, "verdict": v, "reason": reason, "best": best})
        else:
            others.append({**p, "status": st.get("status", "pending"), "detail": st.get("detail", "")})
    ws.ranking.write_text(schema.render_ranking(rows, others))
    log(ws, f"rank: {len(rows)} audited, {len(others)} not audited -> {ws.ranking}")


def stage_status(ws: WS, cfg: dict):
    counts: dict[str, int] = {}
    for name, _, _ in shards(cfg):
        rep = ws.research / name / "report.md"
        key = "missing/invalid" if schema.check_shard(rep) else schema.shard_markers(rep)["STATUS"]
        counts[key] = counts.get(key, 0) + 1
    print(f"research shards ({len(shards(cfg))}): {counts}")
    if not ws.list_json.is_file():
        print("paper list: not built")
        return
    papers = json.loads(ws.list_json.read_text())
    st: dict[str, int] = {}
    for p in papers:
        s = read_status(ws.papers / p["id"]).get("status", "pending")
        st[s] = st.get(s, 0) + 1
    print(f"papers ({len(papers)}): {st}")


def stage_add(ws: WS, cfg: dict, a):
    manual = json.loads(ws.manual.read_text()) if ws.manual.is_file() else []
    if a.topic not in schema.TOPICS:
        sys.exit(f"--topic must be one of {schema.TOPICS}")
    manual.append({"venue": a.venue.lower(), "year": a.year, "title": a.title, "paper_url": a.paper_url,
                   "pdf_url": a.pdf_url, "repo_url": a.repo_url, "topic": a.topic, "note": "added by hand"})
    ws.root.mkdir(parents=True, exist_ok=True)
    ws.manual.write_text(json.dumps(manual, indent=2) + "\n")
    papers = build_list(ws, cfg)
    log(ws, f"add: {papers[-1]['id']} ({len(papers)} papers in list)")


# ================================================================ main

def main():
    ap = argparse.ArgumentParser(prog="lr", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workdir", type=Path, default=ROOT, help="where outputs go (default: lit_review/)")
    ap.add_argument("--config", type=Path, default=ROOT / "config.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("research"); r.add_argument("--only", nargs="+"); r.add_argument("--force", action="store_true")
    c = sub.add_parser("collect"); c.add_argument("--force", action="store_true")
    pr = sub.add_parser("prerank"); pr.add_argument("--force", action="store_true")
    p = sub.add_parser("papers"); p.add_argument("--only", nargs="+"); p.add_argument("--limit", type=int)
    p.add_argument("--top", type=int, help="the N best papers of prerank.json")
    p.add_argument("--concurrency", type=int, help="override stages.audit.concurrency")
    p.add_argument("--force", action="store_true")
    sub.add_parser("rank"); sub.add_parser("status"); sub.add_parser("run")
    a = sub.add_parser("add")
    for k in ("--title", "--venue", "--topic"):
        a.add_argument(k, required=True)
    a.add_argument("--year", type=int, required=True)
    for k in ("--paper-url", "--pdf-url", "--repo-url"):
        a.add_argument(k)
    args = ap.parse_args()

    cfg = json.loads(args.config.read_text())
    ws = WS(args.workdir.resolve())
    ws.root.mkdir(parents=True, exist_ok=True)

    if args.cmd in ("status", "rank"):
        return stage_status(ws, cfg) if args.cmd == "status" else stage_rank(ws, cfg)

    lock = ws.root / ".lr.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        pid = lock.read_text().strip()
        if pid.isdigit() and Path(f"/proc/{pid}").exists():
            sys.exit(f"another lr (pid {pid}) is running in {ws.root}")
        lock.write_text(str(os.getpid()))
    stop = threading.Event()

    def keepalive():  # agents cannot refresh the OAuth token themselves; see sandbox.py
        while not stop.wait(600):
            try:
                msg = sandbox.refresh_token_if_needed()
                if not msg.startswith("token ok"):
                    log(ws, f"keepalive: {msg}")
            except Exception as e:  # noqa: BLE001
                log(ws, f"keepalive: error {e!r}")

    threading.Thread(target=keepalive, daemon=True).start()
    try:
        if args.cmd == "research":
            ok = stage_research(ws, cfg, args.only, args.force)
        elif args.cmd == "collect":
            ok = stage_collect(ws, cfg, args.force)
        elif args.cmd == "prerank":
            ok = stage_prerank(ws, cfg, args.force)
        elif args.cmd == "papers":
            if args.concurrency:
                cfg["stages"]["audit"]["concurrency"] = args.concurrency
            ok = stage_papers(ws, cfg, args.only, args.limit, args.force, args.top)
        elif args.cmd == "add":
            ok = stage_add(ws, cfg, args) or True
        else:  # run -- unattended: give failed shards more passes before giving up
            ok = any(stage_research(ws, cfg) for _ in range(3))
            ok = ok and stage_collect(ws, cfg) and stage_prerank(ws, cfg)
            # audits cost ~$9 each: choose how many explicitly with `lr papers --top N`
            log(ws, f"run: finished research/collect/prerank, ok={ok}; next: lr papers --top N")
        sys.exit(0 if ok else 1)
    finally:
        stop.set()
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
