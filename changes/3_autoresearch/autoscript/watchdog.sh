#!/bin/bash
# Hard 24 h stop for an auto-research run: kills the launcher's process group and every worker/validator
# `timeout ... claude -p` group it started. Detached simulation jobs (own sessions) are left to finish and log.
RUN_DIR="$1"; SECS="$2"
sleep "$SECS"
L=$(cat "$RUN_DIR/launcher.pid")
for g in $(ps -eo pgid,args | awk '/timeout --signal=TERM .*claude -p/ && !/awk/ {print $1}' | sort -u); do kill -TERM -- -"$g" 2>/dev/null; done
kill -TERM -- -"$L" 2>/dev/null; sleep 30; kill -KILL -- -"$L" 2>/dev/null
printf 'STATUS=KILLED_24H\nTIME=%s\n' "$(date -Is)" > "$RUN_DIR/status"
echo "[$(date -Is)] watchdog: killed at 24 h" >> "$RUN_DIR/launcher.log"
