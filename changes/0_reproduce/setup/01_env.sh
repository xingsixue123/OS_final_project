#!/bin/bash
# Create the conda env from the artifact's own pinned spec, into changes/0_reproduce/env.
set -euo pipefail
source "$(dirname "$0")/../env.sh"
YAML="$REPRO_CODE/BCacheSim/install/env_cachelib-py-3.11.yaml"
if [ ! -x "$REPRO_PY" ]; then
    conda env create -p "$REPRO_ENV" -f "$YAML"
fi
# The artifact's conda YAML misses these imports; its requirements.txt lists them (unpinned).
"$REPRO_PY" -m pip install spookyhash compress_json compress_pickle pqdict
"$REPRO_PY" -m pip freeze > "$REPRO_ROOT/env.lock.txt"
"$REPRO_PY" - <<'PY'
import sys, numpy, pandas, lightgbm, sklearn, scipy, jsonargparse
print("python", sys.version.split()[0], "| numpy", numpy.__version__, "| pandas", pandas.__version__,
      "| lightgbm", lightgbm.__version__, "| sklearn", sklearn.__version__, "| scipy", scipy.__version__,
      "| jsonargparse", jsonargparse.__version__)
PY
