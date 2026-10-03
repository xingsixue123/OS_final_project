#!/bin/bash
# every 20 s: processes (other than q2run.py timing runs) that last ran on cores 0-7 with >5% CPU over the interval
LOG=$1
while true; do
  ts=$(date +%H:%M:%S)
  ps -eo pid,psr,pcpu,etimes,args --no-headers | awk -v ts="$ts" '$2<=7 && $3>5.0 && $0 !~ /q2run.py/ && $0 !~ /ps -eo/ {print ts, $0}' | cut -c1-200 >> $LOG
  sleep 20
done
