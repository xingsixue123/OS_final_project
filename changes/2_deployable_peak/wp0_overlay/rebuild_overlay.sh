#!/bin/bash
# Rebuild the phase-2 overlay package from the frozen artifact + PATCH.diff (SCOPE_v2 section 1).
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"
FROZEN="$H/../../0_reproduce/baleen_code/BCacheSim"
OUT="${1:-$H/overlay}"
[ -e "$OUT/BCacheSim" ] && { echo "refusing to overwrite $OUT/BCacheSim"; exit 1; }
mkdir -p "$OUT" && cp -r "$FROZEN" "$OUT/BCacheSim" && chmod -R u+w "$OUT/BCacheSim" && rm -rf "$OUT/BCacheSim/.git"
# PATCH.diff paths are "overlay/BCacheSim/<file>"; apply inside the copy, stripping the 2-component prefix.
cd "$OUT/BCacheSim" && patch -p2 --quiet --forward < "$H/PATCH.diff"
echo "overlay rebuilt at $OUT/BCacheSim"
