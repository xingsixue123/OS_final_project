#!/bin/bash
# Rebuild the two algorithm images used on slide 5 (LaTeX algorithm/algpseudocode, Times via TeX Gyre Termes).
# Needs tectonic (two passes run automatically for the tikzmark highlight bands) and poppler + Pillow.
set -euo pipefail
cd "$(dirname "$0")"
tectonic alg.tex
pdftoppm -png -r 300 alg.pdf p
python3 - <<'PY'
from PIL import Image, ImageChops
for i in (1, 2):
    im = Image.open(f"p-{i}.png").convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
    pad = 30
    bb = (max(bb[0] - pad, 0), max(bb[1] - pad, 0), min(bb[2] + pad, im.size[0]), min(bb[3] + pad, im.size[1]))
    im.crop(bb).save(f"alg{i}.png")
PY
rm -f p-1.png p-2.png alg.pdf
