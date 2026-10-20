#!/bin/bash
# Rebuild the overlay v3 package (3_autoresearch copy of wp10_schedule/rebuild_overlay.sh) from the frozen artifact + PATCH_v3.diff (= wp0_overlay/PATCH.diff + the
# SCOPE_v2_1b table threshold). Never touches wp0_overlay/ or 0_reproduce/.
set -euo pipefail
H="$(cd "$(dirname "$0")" && pwd)"
FROZEN="$H/../../../0_reproduce/baleen_code/BCacheSim"
OUT="${1:-$H/overlay}"
[ -e "$OUT/BCacheSim" ] && { echo "refusing to overwrite $OUT/BCacheSim"; exit 1; }
mkdir -p "$OUT" && cp -r "$FROZEN" "$OUT/BCacheSim" && chmod -R u+w "$OUT/BCacheSim" && rm -rf "$OUT/BCacheSim/.git"
# PATCH_v3.diff paths are "overlay/BCacheSim/<file>"; apply inside the copy, stripping the 2-component prefix.
cd "$OUT/BCacheSim" && patch -p2 --quiet --forward < "$H/PATCH_v3.diff"
echo "overlay v3 rebuilt at $OUT/BCacheSim"
