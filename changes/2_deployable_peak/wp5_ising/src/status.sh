#!/bin/bash
P2=/home/sxing/project/OS_final_project/changes/2_deployable_peak
date
echo "--- tuning BEST:"; grep -h "BEST" $P2/wp5_ising/logs/tune_b*.log 2>/dev/null | cut -c1-90
for b in 1 3 10; do f=$P2/wp5_ising/logs/tune_b$b.log; [ -f $f ] && echo "b$b last: $(grep '\] trial' $f | tail -1 | cut -c1-60)"; done
echo "--- wp1 solve:"; grep "^\[solve\]" $P2/wp1_offline/logs/solve.log | tail -3 | cut -c1-110
echo "--- wp1 R0 done: $(grep -c '^== ' $P2/wp1_offline/logs/r0.log)  sims done: $(grep -c '^== ' $P2/wp1_offline/logs/sim.log)  FAILED: $(grep -c FAIL $P2/wp1_offline/logs/r0.log $P2/wp1_offline/logs/sim.log | paste -sd' ')"
echo "--- running sims: $(ps -eo args | grep -c '[B]CacheSim.cachesim.simulate_ap')  trains: $(ps -eo args | grep -c '[q]2launch_train')"
echo "--- audit DIRECT lines: $(grep -c DIRECT $P2/wp5_ising/logs/core_audit.log)  SIBLING lines: $(grep -c SIBLING $P2/wp5_ising/logs/core_audit.log)"
free -g | sed -n 2p
