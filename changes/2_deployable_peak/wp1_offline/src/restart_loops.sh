#!/bin/bash
# wait for orphaned WP1 sims (old CPU pinning) to finish, then restart the r0 and sim loops (resumable)
source /home/sxing/project/OS_final_project/changes/2_deployable_peak/wp1_offline/env.sh
cd $A
while ps aux | grep "[s]imulate_ap" | grep -q "runs/off/wp1_"; do sleep 5; done
nohup $BALEEN_PY src/wp1.py r0 --workers 6 >> logs/r0.log 2>&1 &
echo $! > logs/r0.pid
nohup $BALEEN_PY src/wp1.py sim --wait --workers 6 >> logs/sim.log 2>&1 &
echo $! > logs/sim.pid
echo "restarted $(date)"
