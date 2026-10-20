#!/bin/bash
# Rebuild the 3_autoresearch overlay v4 from the frozen artifact + PATCH_v4.diff (= wp10 PATCH_v3.diff + PATCH_v4_delta.diff,
# SCOPE_AMENDMENT.md item 1.2c). Never touches wp0_overlay/, wp10_schedule/ or 0_reproduce/.
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"
FROZEN="$H/../../../0_reproduce/baleen_code/BCacheSim"
OUT="${1:-$H/overlay}"
[ -e "$OUT/BCacheSim" ] && { echo "refusing to overwrite $OUT/BCacheSim"; exit 1; }
mkdir -p "$OUT" && cp -r "$FROZEN" "$OUT/BCacheSim" && chmod -R u+w "$OUT/BCacheSim" && rm -rf "$OUT/BCacheSim/.git"
# PATCH_v4.diff paths are "overlay/BCacheSim/<file>"; apply inside the copy, stripping the 2-component prefix.
cd "$OUT/BCacheSim" && patch -p2 --quiet --forward < "$H/PATCH_v4.diff"
echo "overlay v4 rebuilt at $OUT/BCacheSim"
