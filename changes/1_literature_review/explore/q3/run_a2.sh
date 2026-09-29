#!/bin/bash
# A2: held-out confirmation of ONE final configuration: 6 held-out instances x 3 retrains, deployed pipeline, stage=heldout.
#   run_a2.sh <name> <cand> '<args json>'      (args must be identical to the dev runs of that config)
Q3="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source $Q3/env.sh
cd $Q3
nohup taskset -c 8-23 $BALEEN_PY -B src/deployed3.py --inst Region7_s0.1 Region7_s0.2 Region7_s0.3 Region6_s0.1 Region6_s0.2 Region6_s0.3 \
  --name "$1" --cand "$2" --args "$3" --reps 1 2 3 --stage heldout > work/logs/drv/A2_$1.log 2>&1 &
echo "A2 $1 started: pid $!"
