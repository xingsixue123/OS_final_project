"""Check changes/5_midterm/SOURCES.md: every cited file exists and every value appears in its cited lines.

  python3 changes/5_midterm/code/check_sources.py      # exit 0 iff every row checks out

A value matches a cited line if it occurs there verbatim, or (for a plain number, ignoring a leading sign and a
trailing %) if some number in the line rounds half-up to it at the value's precision (42.455 -> 42.46).
PDF sources are checked for existence only.
"""
import os
import re
import sys
from decimal import ROUND_HALF_UP, Decimal

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(os.path.dirname(HERE))
ROW = re.compile(r"^\| *(\d+) *\| *(.+?) *\| *`([^`#]+)(?:#L(\d+)(?:-L(\d+))?)?` *\|")
NUM = re.compile(r"\d+(?:\.\d+)?")


def num_match(value, text):
    v = value.replace("−", "-").strip().lstrip("+-").rstrip("%")
    if not re.fullmatch(r"\d+(?:\.\d+)?", v):
        return False
    q = Decimal(1).scaleb(-len(v.split(".")[1])) if "." in v else Decimal(1)
    return any(Decimal(n).quantize(q, rounding=ROUND_HALF_UP) == Decimal(v) for n in NUM.findall(text))


def main():
    bad, n = [], 0
    for line in open(os.path.join(HERE, "SOURCES.md"), encoding="utf-8"):
        m = ROW.match(line)
        if not m:
            continue
        n += 1
        slide, value, path, a, b = m.groups()
        full = os.path.join(REPO, path)
        if not os.path.exists(full):
            bad.append(f"slide {slide}: missing file {path}")
            continue
        if path.endswith(".pdf"):
            continue
        lines = open(full, encoding="utf-8", errors="ignore").read().split("\n")
        lo, hi = (int(a), int(b or a)) if a else (1, len(lines))
        text = "\n".join(lines[lo - 1:hi])
        if value not in text and value.replace("−", "-") not in text and not num_match(value, text):
            bad.append(f"slide {slide}: '{value}' not found in {path}#L{lo}-L{hi}")
    print(f"{n} rows checked, {len(bad)} problems")
    for x in bad:
        print("  " + x)
    sys.exit(1 if bad or n == 0 else 0)


if __name__ == "__main__":
    main()
