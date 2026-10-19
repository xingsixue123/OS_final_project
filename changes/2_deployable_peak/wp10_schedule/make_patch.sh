#!/bin/bash
# Regenerate PATCH_v3.diff = overlay/BCacheSim vs the frozen BCacheSim, and PATCH_v3_delta.diff = the v3 additions
# relative to wp0_overlay/overlay (the reviewed PATCH.diff). Both are reports; rebuild_overlay.sh applies PATCH_v3.diff.
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"
cd "$H"
diff -ruN --exclude=.git --exclude=__pycache__ ../../0_reproduce/baleen_code/BCacheSim overlay/BCacheSim > PATCH_v3.diff || [ $? -eq 1 ]
diff -ruN --exclude=.git --exclude=__pycache__ ../wp0_overlay/overlay/BCacheSim overlay/BCacheSim > PATCH_v3_delta.diff || [ $? -eq 1 ]
echo "PATCH_v3.diff: $(grep -c '^diff ' PATCH_v3.diff) files, +$(grep -c '^+[^+]' PATCH_v3.diff) / -$(grep -c '^-[^-]' PATCH_v3.diff) lines"
echo "PATCH_v3_delta.diff: $(grep -c '^diff ' PATCH_v3_delta.diff) files, +$(grep -c '^+[^+]' PATCH_v3_delta.diff) / -$(grep -c '^-[^-]' PATCH_v3_delta.diff) lines"
