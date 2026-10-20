"""Deterministic, fail-closed checks for changes/4_story/STORY.md.

  python3 changes/4_story/code/check_story.py      # exit 0 iff no problems; writes result/check_story.json

Required finding format (one block per finding):
  ### F<id> [P0|P1|P2|P3] [EVIDENCE] <title>
  ... claim text with numbers ...
  Refs: `repo/relative/path` (`path#Lnn` or `path` §section allowed), ...
EVIDENCE is one of TEST-PREREG, TEST-POSTHOC, DEV, OFFLINE, REPRO, INFRA, NEGATIVE-TEST.
Every backticked repo path anywhere in the file must exist; every finding needs >= 1 existing ref.
Every number (e.g. 37.20, -13.7%, 5/6) in a finding's text must also appear in at least one of its referenced
files (normalised), otherwise it is flagged as an UNSOURCED number.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(HERE))
STORY = os.path.join(HERE, "STORY.md")
EVID = {"TEST-PREREG", "TEST-POSTHOC", "DEV", "OFFLINE", "REPRO", "INFRA", "NEGATIVE-TEST"}
HEAD = re.compile(r"^### (F[\w.-]+) \[(P[0-3])\] \[([A-Z-]+)\] (.+)$")
PATH = re.compile(r"`([A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+)(?:#L\d+(?:-L?\d+)?)?`")
NUM = re.compile(r"(?<![\w.])[-−+]?\d+(?:\.\d+)?(?:/\d+)?%?")
TRIVIAL = {str(i) for i in range(0, 13)} | {"0.1", "0.2", "0.3", "0.4", "0.5", "0.6", "0.7", "0.8", "0.9", "100", "24", "2026"}


def norm(x):
    return x.replace("−", "-").lstrip("+").rstrip("%")


def file_numbers(paths, cache={}):
    out = set()
    for p in paths:
        full = os.path.join(REPO, p)
        if full in cache:
            out |= cache[full]
            continue
        s = set()
        try:
            if os.path.isfile(full) and os.path.getsize(full) < 30_000_000:
                txt = open(full, errors="ignore").read()
                s = {norm(m) for m in NUM.findall(txt)}
                # also allow rounded forms of long decimals in the source (e.g. 37.2029 -> 37.20, 37.2)
                for m in re.findall(r"-?\d+\.\d{3,}", txt):
                    v = float(m)
                    for k in (0, 1, 2, 3):
                        s.add(norm(f"{v:.{k}f}"))
        except OSError:
            pass
        cache[full] = s
        out |= s
    return out


def link_problems(text):
    """Stricter checks added in story round 2: line anchors within the file, link targets exist."""
    probs = []
    nlines = {}
    for m in re.finditer(r"`([A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+)#L(\d+)(?:-L?(\d+))?`", text):
        p, a, b = m.group(1), int(m.group(2)), int(m.group(3) or m.group(2))
        full = os.path.join(REPO, p)
        if not os.path.isfile(full) or p.endswith((".pdf", ".npz", ".gz")):
            continue
        if p not in nlines:
            nlines[p] = sum(1 for _ in open(full, errors="ignore"))
        if a > b or b > nlines[p]:
            probs.append(f"line anchor out of range: {p}#L{a}-L{b} (file has {nlines[p]} lines)")
    anchors = set(re.findall(r'<a id="(F[\w.-]+)"></a>', text))
    for m in re.finditer(r"\]\(([^)\s]+)\)", text):
        t = m.group(1)
        if t.startswith("#"):
            if t[1:] not in anchors:
                probs.append(f"link to missing anchor: {t}")
        elif not t.startswith("http"):
            path = t.split("#")[0]
            if not os.path.exists(os.path.normpath(os.path.join(HERE, path))):
                probs.append(f"link target does not exist: {t}")
    return sorted(set(probs))


def main():
    problems, warnings, findings = [], [], []
    if not os.path.exists(STORY):
        print(json.dumps({"problems": ["STORY.md missing"]}))
        sys.exit(1)
    lines = open(STORY, encoding="utf-8").read().split("\n")
    for m in PATH.finditer("\n".join(lines)):
        p = m.group(1)
        if "/" in p and not os.path.exists(os.path.join(REPO, p)):
            problems.append(f"referenced path does not exist: {p}")
    problems.extend(link_problems("\n".join(lines)))
    cur = None
    blocks = []
    for ln in lines:
        h = HEAD.match(ln)
        if h:
            cur = dict(id=h.group(1), prio=h.group(2), evid=h.group(3), title=h.group(4), body=[])
            blocks.append(cur)
        elif ln.startswith("## ") or ln.startswith("# "):
            cur = None
        elif cur is not None:
            cur["body"].append(ln)
    ids = [b["id"] for b in blocks]
    if len(ids) != len(set(ids)):
        problems.append("duplicate finding ids")
    for b in blocks:
        body = "\n".join(b["body"])
        if b["evid"] not in EVID:
            problems.append(f"{b['id']}: unknown evidence tag {b['evid']}")
        refs = [m.group(1) for m in PATH.finditer(body) if os.path.exists(os.path.join(REPO, m.group(1)))]
        if "Refs:" not in body or not refs:
            problems.append(f"{b['id']}: no existing Refs")
        nums = {norm(n) for n in NUM.findall(body.split("Refs:")[0] + " " + b["title"])} - TRIVIAL
        src = file_numbers(refs)
        unsourced = sorted(n for n in nums if n not in src and n.split("/")[0] not in src)
        if unsourced:
            problems.append(f"{b['id']}: numbers not found in its refs: {unsourced[:12]}")
        findings.append(dict(id=b["id"], prio=b["prio"], evid=b["evid"], refs=len(refs), unsourced=unsourced))
    if len(blocks) < 25:
        warnings.append(f"only {len(blocks)} findings; the story should be comprehensive")
    for p in ("P0", "P1", "P2", "P3"):
        if not any(b["prio"] == p for b in blocks):
            warnings.append(f"no {p} finding")
    out = dict(problems=problems, warnings=warnings, n_findings=len(blocks), findings=findings)
    json.dump(out, open(os.path.join(HERE, "result", "check_story.json"), "w"), indent=1)
    print(json.dumps(dict(problems=problems[:60], n_problems=len(problems), warnings=warnings, n_findings=len(blocks)), indent=1))
    sys.exit(0 if not problems else 1)


if __name__ == "__main__":
    main()
