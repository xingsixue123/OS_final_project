#!/bin/bash
source /home/sxing/project/OS_final_project/changes/1_literature_review/explore/q2/env.sh; cd $Q2
while kill -0 192500 2>/dev/null; do sleep 5; done
$SOLVER_PY -c "import optuna; optuna.delete_study(study_name='F2b_tau_rel0.6__lp__b10', storage='sqlite:///optuna.db')" >> logs/chain2.log 2>&1
$SOLVER_PY src/q2tune.py --form '{"name":"F2b","tau_rel":0.6}' --solvers lp --budget 10 --trials 10 > logs/tune_F2b_b10_lp_rerun.log 2>&1
$SOLVER_PY src/q2tune.py --form '{"name":"F1"}' --solvers ls,pt,eim,milp,cpsat,hlns,lp,sb,mq --budget 10 --trials 10 > logs/tune_F1_b10.log 2>&1
