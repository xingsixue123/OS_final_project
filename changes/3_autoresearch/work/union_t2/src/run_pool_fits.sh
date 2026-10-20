#!/bin/bash
# plan B pooled fits (solver only, nice 19): leave-one-instance-out over DEV8 + one fit on all DEV8, base $1
set -uo pipefail
cd "$(dirname "$0")/.." && source ./env.sh
BASE=${1:-B}
D8="Region7_s0 Region7_s0.1 Region7_s0.2 Region7_s0.3 Region6_s0 Region6_s0.1 Region6_s0.2 Region6_s0.3"
for h in $D8 all; do
  echo "$h"
done | xargs -P 5 -I{} env PY="$SOLVER_PY" NUMBA_NUM_THREADS=1 OMP_NUM_THREADS=1 nice -n 19 src/sbx.sh src/cls_pool.py --mode dev --base "$BASE" --insts $D8 --reps 1 2 3 --holdout {} --solvers ptm cdm --budget 180 --tag loo
