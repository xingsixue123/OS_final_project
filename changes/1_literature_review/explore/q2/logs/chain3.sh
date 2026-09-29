#!/bin/bash
source /home/sxing/project/OS_final_project/changes/1_literature_review/explore/q2/env.sh; cd $Q2
while kill -0 203323 2>/dev/null; do sleep 5; done
$SOLVER_PY src/q2tune.py --form '{"name":"F1"}' --solvers ls,pt,eim,milp,cpsat,hlns,lp,sb,mq --budget 60 --trials 3 --seed-from 10 --topk 3 --with-default > logs/tune_F1_b60.log 2>&1
