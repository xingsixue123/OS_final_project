#!/bin/bash
# Stop the running `lr run` driver as soon as the collect stage finishes, so the
# (expensive) papers/audit stage never starts without a human go-ahead.
cd "$(dirname "$0")/.."
PID=$(cat .lr.lock)
until grep -qE "collect: [0-9]+ papers ->|collect: FAILED|run: finished" lr.log; do
  kill -0 "$PID" 2>/dev/null || { echo "driver $PID already exited"; exit 0; }
  sleep 2
done
pkill -TERM -P "$PID"; kill -TERM "$PID"; sleep 3
rm -f .lr.lock
echo "stopped driver $PID after: $(grep -E 'collect:' lr.log | tail -1)"
