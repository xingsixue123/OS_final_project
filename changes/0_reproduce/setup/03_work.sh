#!/bin/bash
# Lay out work/ so that the artifact's relative paths (BCacheSim/, data/tectonic, runs/, tmp/,
# notebooks/../../data) all resolve inside work/. The code is a symlink to the frozen tree.
set -euo pipefail
source "$(dirname "$0")/../env.sh"
mkdir -p "$REPRO_WORK"/{runs,tmp,logs,jobs,results,systmp}
cd "$REPRO_WORK"
[ -L BCacheSim ] || ln -s ../baleen_code/BCacheSim BCacheSim
# Notebooks are copied (not linked): executing a notebook writes outputs next to it.
if [ ! -d notebooks ]; then
    cp -r "$REPRO_CODE/notebooks" notebooks && chmod -R u+w notebooks
fi
bash "$REPRO_ROOT/check_frozen.sh"
echo "work/ ready: $REPRO_WORK"
