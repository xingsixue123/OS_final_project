#!/bin/bash
# B0: build the shared solver env at X/env (sandboxed; nothing registered or written outside X).
source /home/sxing/project/OS_final_project/changes/1_literature_review/explore/q2/env.sh
LOG=$Q2/logs/b0_install.log
REC=$Q2/logs/b0_install_outcomes.tsv
echo -e "package\tresult\tseconds" > $REC
echo "=== conda create $(date -Is)" >> $LOG
t0=$(date +%s)
/home/sxing/miniconda3/bin/conda create -y -p $X/env --override-channels -c conda-forge python=3.11 >> $LOG 2>&1
rc=$?; echo -e "conda python=3.11\trc=$rc\t$(( $(date +%s)-t0 ))" >> $REC
[ $rc -ne 0 ] && { echo "conda create failed" >> $LOG; exit 1; }
PY=$X/env/bin/python
$PY -m pip install --upgrade pip >> $LOG 2>&1
inst() {  # name, pip args...
  local name=$1; shift
  local t0=$(date +%s)
  echo "=== pip $name $(date -Is)" >> $LOG
  timeout 900 $PY -m pip install "$@" >> $LOG 2>&1
  local rc=$?
  echo -e "$name\trc=$rc\t$(( $(date +%s)-t0 ))" >> $REC
}
inst torch torch --index-url https://download.pytorch.org/whl/cpu
inst numpy-scipy-numba numpy scipy numba
inst highspy highspy
inst pyscipopt pyscipopt
inst ortools ortools
inst optuna optuna
inst simulated-bifurcation simulated-bifurcation
inst dwave-samplers-dimod dwave-samplers dimod
inst openjij openjij
inst mindquantum mindquantum==0.12.0
inst pandas pandas
echo "=== done $(date -Is)" >> $LOG
