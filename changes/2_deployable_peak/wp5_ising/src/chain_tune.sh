#!/bin/bash
# WP5 step 1: tuning chain (dev only), budgets 1 -> 3 -> 10 s, 12 trials per solver per budget.
source /home/sxing/project/OS_final_project/changes/2_deployable_peak/wp5_ising/env.sh
cd $A
for b in 1 3 10; do
  $SOLVER_PY src/p2tune.py --budget $b --solvers pt,lp,eim,milp,sb,cpsat,mq,ls --trials 12 >> logs/tune_b$b.log 2>&1
done
echo "TUNE DONE $(date)" >> logs/tune_b10.log
