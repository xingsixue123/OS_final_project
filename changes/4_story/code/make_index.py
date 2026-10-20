"""Regenerate the findings index table in changes/4_story/STORY.md from the finding headers.

  python3 changes/4_story/code/make_index.py

Replaces everything between <!-- INDEX:BEGIN --> and <!-- INDEX:END -->. Titles are copied verbatim, so the index
can never disagree with the findings.
"""
import collections
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY = os.path.join(HERE, "STORY.md")
HEAD = re.compile(r"^### (F[\w.-]+) \[(P[0-3])\] \[([A-Z-]+)\] (.+)$")


def main():
    text = open(STORY, encoding="utf-8").read()
    rows, section = [], ""
    for ln in text.split("\n"):
        if ln.startswith("## "):
            section = ln[3:].split(":")[0].strip()
        m = HEAD.match(ln)
        if m:
            rows.append((m.group(1), m.group(2), m.group(3), m.group(4), section))
    count = collections.Counter(r[1] for r in rows)
    ev = collections.Counter(r[2] for r in rows)
    out = [f"{len(rows)} findings: " + ", ".join(f"{p} {count[p]}" for p in ("P0", "P1", "P2", "P3"))
           + ". Evidence: " + ", ".join(f"{k} {v}" for k, v in sorted(ev.items())) + ".", "",
           "**P0 findings (headline results and decisive negatives):** "
           + ", ".join(r[0] for r in rows if r[1] == "P0") + ".", "",
           "| ID | Priority | Evidence | Claim | Section |", "|---|---|---|---|---|"]
    for fid, p, e, title, sec in rows:
        out.append(f"| {fid} | {p} | {e} | {title.replace('|', '/')} | {sec} |")
    new = "<!-- INDEX:BEGIN -->\n" + "\n".join(out) + "\n<!-- INDEX:END -->"
    text = re.sub(r"<!-- INDEX:BEGIN -->.*?<!-- INDEX:END -->", lambda _: new, text, flags=re.S)
    open(STORY, "w", encoding="utf-8").write(text)
    print(out[0])


if __name__ == "__main__":
    main()
