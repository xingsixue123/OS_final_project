"""Renumber findings F01..Fnn in document order and rewrite every cross-reference (STORY.md + WRITER_NOTES.md).

  python3 changes/4_story/code/renumber.py

Finding ids are two-digit (F01, F02, ...), so formulation names such as F1, F2b, F1PT are never touched.
Use only before validators have referenced the ids (round 1); later rounds keep ids stable.
"""
import os
import re

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = [os.path.join(HERE, "STORY.md"), os.path.join(HERE, "result", "WRITER_NOTES.md")]
HEAD = re.compile(r"^### (F\d{2}) \[", re.M)
TOKEN = re.compile(r"\bF(\d{2})\b")


def main():
    story = open(FILES[0], encoding="utf-8").read()
    old = HEAD.findall(story)
    mapping = {o: f"F{i:02d}" for i, o in enumerate(old, 1)}
    assert len(set(old)) == len(old), "duplicate ids"
    for path in FILES:
        if not os.path.exists(path):
            continue
        txt = open(path, encoding="utf-8").read()
        txt = TOKEN.sub(lambda m: mapping.get(m.group(0), m.group(0)), txt)
        open(path, "w", encoding="utf-8").write(txt)
    changed = {o: n for o, n in mapping.items() if o != n}
    print(f"{len(old)} findings; {len(changed)} ids changed: {changed}")


if __name__ == "__main__":
    main()
