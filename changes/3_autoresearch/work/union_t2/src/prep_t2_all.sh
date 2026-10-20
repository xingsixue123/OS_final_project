#!/bin/bash
# T2 prerequisites (no outcome read): frozen fullml + day-1 dumps, then F1PT/F1CPSAT label sets seeds 1-6.
set -uo pipefail
cd "$(dirname "$0")/.." && source ./env.sh
K="Region4_s0.2 Region4_s0.3 Region4_s0.4 Region4_s0.5 Region4_s0.6"
src/sbx.sh src/prep.py dumps --keys $K
src/sbx.sh src/prep_day1.py --mode test --keys $K
mkdir -p logs/test/labels
for s in 1 2 3 4 5 6; do for d in F1PT F1CPSAT; do for i in $K; do echo "$i $d $s"; done; done; done | xargs -P 3 -L 1 bash -c '[ -f labels/$0_$1_s$2.npz ] || PY=$SOLVER_PY NUMBA_NUM_THREADS=8 OMP_NUM_THREADS=8 src/sbx.sh src/labels.py --inst $0 --design $1 --seed $2 --inst-dir inst_test > logs/test/labels/$0_$1_s$2.log 2>&1; echo "$0 $1 s$2 rc=$?"'
echo "T2 prerequisites done $(date -Is)"
