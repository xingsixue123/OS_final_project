#!/bin/bash
source /home/sxing/project/OS_final_project/changes/1_literature_review/explore/q2/env.sh; cd $Q2
while kill -0 235150 2>/dev/null; do sleep 5; done
$SOLVER_PY src/q2confirm.py --form '{"name":"F1"}' --solvers pt,cpsat --budgets 10,60 --seeds 0,1,2 --phase sens_default > logs/sens_default.log 2>&1
$SOLVER_PY src/q2confirm.py --form '{"name":"F1"}' --solvers pt,cpsat --budgets 10,60 --seeds 0,1,2 --extra-cfg '{"level_weights":[6,1,1,1,1,1,1,1]}' --phase sens_w6 > logs/sens_w6.log 2>&1
