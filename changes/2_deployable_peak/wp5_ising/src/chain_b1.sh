#!/bin/bash
# deval at 1 s (phase-1 split, then hard-level split) and rolling at 1 s for every tuned solver + greedy/pgreedy
source /home/sxing/project/OS_final_project/changes/2_deployable_peak/wp5_ising/env.sh
cd $A
$SOLVER_PY src/p2deval.py plan > logs/plan_b1.log 2>&1
$SOLVER_PY src/p2deval.py run --split default --budgets 1 >> logs/deval_default.log 2>&1
$SOLVER_PY src/p2deval.py run --split hl --budgets 1 >> logs/deval_hl.log 2>&1
$SOLVER_PY src/p2rollrun.py --budget 1 --solvers greedy,pgreedy,lp,milp,cpsat,ls,pt,eim,sb,mq >> logs/roll_b1.log 2>&1
echo "CHAIN B1 DONE $(date)" >> logs/roll_b1.log
