"""Make STORY.md clickable (idempotent): anchors before findings, repo paths as relative links, finding ids as links.

  python3 changes/4_story/code/linkify.py

- `### F18 ...` gets a preceding `<a id="F18"></a>` line.
- A backticked existing repo path (optionally `#Lx-Ly`) becomes [`path#Lx-Ly`](../../path#Lx-Ly), relative to
  changes/4_story/ (GitHub and most IDEs resolve it; GitHub highlights the line range).
- A bare finding id (F01..F999 that exists as a finding) becomes [F18](#F18). Header lines, anchor lines and fenced
  code blocks are left alone; already-linked ids and paths are not re-linked.
"""
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(HERE))
STORY = os.path.join(HERE, "STORY.md")
HEAD = re.compile(r"^### (F\d{2,3}) \[")
PATH = re.compile(r"(?<!\[)`(\.?/?[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)+)((?:#L\d+(?:-L?\d+)?)?)`(?!\]\()")
FID = re.compile(r"(?<![\[#\w/])(F\d{2,3})(?![\w\]])")


def main():
    text = open(STORY, encoding="utf-8").read()
    ids = set(m.group(1) for m in re.finditer(r"^### (F\d{2,3}) \[", text, flags=re.M))
    out, in_code = [], False
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.startswith("```"):
            in_code = not in_code
            out.append(ln)
            continue
        if in_code:
            out.append(ln)
            continue
        h = HEAD.match(ln)
        if h:
            anchor = f'<a id="{h.group(1)}"></a>'
            if not (out and out[-1] == anchor):
                out.append(anchor)
            out.append(ln)
            continue
        if ln.startswith('<a id="'):
            out.append(ln)
            continue

        def path_link(m):
            p, anc = m.group(1), m.group(2)
            if not os.path.exists(os.path.join(REPO, p)):
                return m.group(0)
            target = "../../" + p[2:] if p.startswith("./") else "../../" + p
            return f"[`{p}{anc}`]({target}{anc})"

        ln = PATH.sub(path_link, ln)
        # link finding ids outside existing link texts/targets
        parts = re.split(r"(\[[^\]]*\]\([^)]*\))", ln)
        for k in range(0, len(parts), 2):
            parts[k] = FID.sub(lambda m: f"[{m.group(1)}](#{m.group(1)})" if m.group(1) in ids else m.group(1), parts[k])
        out.append("".join(parts))
    open(STORY, "w", encoding="utf-8").write("\n".join(out))
    print(f"linkified: {len(ids)} finding anchors")


if __name__ == "__main__":
    main()
