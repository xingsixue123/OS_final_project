#!/bin/bash
# A0 driver: dumps, then OPT / Baleen online / RejectX+CoinFlip baselines in parallel (all resumable).
X="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source $X/q3/env.sh
cd $X/common
PY="taskset -c 8-23 $BALEEN_PY -B"
$PY src/a0.py dumps > logs/a0_dumps.log 2>&1
$PY src/a0.py dumps_dev --keys Region7_s0 Region6_s0 > logs/a0_dumps_dev.log 2>&1
touch $X/common/.dumps_done
A0_SIM_WORKERS=6 $PY src/a0.py opt > logs/a0_opt.log 2>&1 &
A0_SIM_WORKERS=8 $PY src/a0.py baleen --reps 1 2 3 > logs/a0_baleen.log 2>&1 &
A0_SIM_WORKERS=6 $PY src/a0.py static > logs/a0_static.log 2>&1 &
wait
touch $X/common/.a0_runs_done
