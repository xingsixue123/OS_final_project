#!/bin/bash
# WP5 remaining dev pipeline (dev instances only). Priorities on the cores lock: 1 = deval / label timing, 3 = rolling,
# scaling (fill-in work that no simulation waits for).
source /home/sxing/project/OS_final_project/changes/2_deployable_peak/wp5_ising/env.sh
cd $A
PY=$SOLVER_PY
until [ -f logs/tune_b10.log ]; do sleep 20; done                      # 3-s tuning finished
$PY src/p2deval.py plan > logs/plan_b3.log 2>&1
$PY src/p2deval.py run --split default --budgets 3 >> logs/deval_default.log 2>&1
$PY src/p2deval.py run --split hl --budgets 3 >> logs/deval_hl.log 2>&1
until grep -q "TUNE DONE" logs/tune_b10.log; do sleep 20; done          # 10-s tuning finished
$PY src/p2deval.py plan > logs/plan_b10.log 2>&1
$PY src/p2deval.py run --split default --budgets 10 >> logs/deval_default.log 2>&1
$PY src/p2analyze.py finalists > logs/finalists.log 2>&1
FIN=$($PY -c "import json; print(','.join(json.load(open('results/finalists.json'))['finalists']))")
BC10=$($PY src/best_classical.py 10)
BC3=$($PY src/best_classical.py 3)
BC1=$($PY src/best_classical.py 1)
echo "finalists=$FIN best_classical b1=$BC1 b3=$BC3 b10=$BC10 $(date)" >> logs/chain_rest.log
# label evidence: OPT-mode sims of the dev selections (Baleen env, sims on 8-11,20-23) -- background
F1=$(echo $FIN | cut -d, -f1)
nohup $BALEEN_PY src/p2labsim.py --phase deval --solvers $(echo $FIN | tr , ' ') $BC10 --budgets 10 --seed 101 >> logs/labsim.log 2>&1 &
# day-1 (label-size) timing for the finalists + classical references
for sv in $(echo "$FIN,$BC1,$BC3,$BC10,cpsat,ls" | tr , '\n' | sort -u); do
  for b in 1 3 10; do
    CFG=$($PY -c "import json; print(json.dumps(json.load(open('results/plan_dev.json'))['solvers']['$sv']['$b']['cfg']))")
    OMP_NUM_THREADS=8 NUMBA_NUM_THREADS=8 taskset -c 0-7 $PY src/p2run.py --insts inst_day1/*.npz --solver $sv --budget $b \
      --seed 101 --cfg "$CFG" --phase label_day1 --tag label_day1_${sv}_b$b --sols $A/sols >> logs/label_day1.log 2>&1
  done
done
$PY src/p2deval.py run --split hl --budgets 10 >> logs/deval_hl.log 2>&1
nohup $BALEEN_PY src/p2labsim.py --phase deval --solvers $F1 $BC1 --budgets 1 --seed 101 >> logs/labsim.log 2>&1 &
# fill-in work (priority 3)
export P2_PRIO=3
$PY src/p2rollrun.py --budget 1 --solvers greedy,pgreedy,lp,milp,cpsat,ls,pt,eim,sb,mq >> logs/roll_b1.log 2>&1
$PY src/p2rollrun.py --budget 3 --solvers $(echo "$FIN,$BC3,$BC1,pgreedy" | tr , '\n' | awk '!s[$0]++' | paste -sd,) >> logs/roll_b3.log 2>&1
$PY src/make_scale_plan.py >> logs/scale.log 2>&1
$PY src/p2scale.py all --plan scale_plan.json >> logs/scale.log 2>&1
echo "CHAIN REST DONE $(date)" >> logs/chain_rest.log
