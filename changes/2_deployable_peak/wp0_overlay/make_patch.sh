#!/bin/bash
# Regenerate PATCH.diff = overlay/BCacheSim vs the frozen BCacheSim (0_reproduce/baleen_code, ddeb2d8).
# The frozen tree's gitfile `.git` (a submodule pointer) is not copied into the overlay and is excluded here.
set -euo pipefail
A="$(cd "$(dirname "$0")" && pwd)"
cd "$A"
diff -ruN --exclude=.git --exclude=__pycache__ ../../0_reproduce/baleen_code/BCacheSim overlay/BCacheSim > PATCH.diff || [ $? -eq 1 ]
echo "PATCH.diff: $(grep -c '^diff ' PATCH.diff) files, +$(grep -c '^+[^+]' PATCH.diff) / -$(grep -c '^-[^-]' PATCH.diff) lines"
