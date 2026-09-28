#!/bin/bash
# Fails if the frozen artifact differs from the checksums recorded at freeze time.
set -euo pipefail
R="$(cd "$(dirname "$0")" && pwd)"
cd "$R/baleen_code"
sha256sum --quiet -c "$R/baleen_code.sha256"
extra=$(find . -path ./.git -prune -o -path ./BCacheSim/.git -prune -o -type f -print | sort \
        | comm -23 - <(awk '{print $2}' "$R/baleen_code.sha256" | sort) || true)
[ -z "$extra" ] || { echo "FROZEN VIOLATION: new files: $extra"; exit 1; }
echo "frozen OK ($(wc -l < "$R/baleen_code.sha256") files)"
