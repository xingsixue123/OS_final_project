#!/bin/bash
source /home/sxing/project/OS_final_project/changes/1_literature_review/explore/q2/env.sh; cd $Q2
while pgrep -f "q2tune.py --form {\"name\":\"F2b\"" >/dev/null; do sleep 10; done
$SOLVER_PY src/q2tune.py --form '{"name":"F1"}' --solvers ls,pt,eim,milp,cpsat,hlns,lp,sb,mq --budget 10 --trials 10 > logs/tune_F1_b10.log 2>&1
