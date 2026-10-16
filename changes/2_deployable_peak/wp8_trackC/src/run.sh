#!/bin/bash
# Track C sandboxed runner: taskset (8-11,20-23) + bwrap private /tmp, cwd = wp8_trackC/work.
#   src/run.sh baleen|solver <script.py> [args...]      (env.sh is sourced here)
set -e
D="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$D/env.sh"
which=$1; shift
case $which in baleen) PY=$BALEEN_PY;; solver) PY=$SOLVER_PY;; *) echo "baleen|solver"; exit 2;; esac
JT="$D/work/systmp/job_$$_$(date +%s%N)"
mkdir -p "$JT"
export PYTHONPATH="$D/src:$D/src/q3lib:$D/src/q2lib:$D/work"
cd "$D/work"
set +e
taskset -c "$WP8_CPUS" bwrap --dev-bind / / --bind "$JT" /tmp -- "$PY" -B "$@"
rc=$?
rm -rf "$JT"
exit $rc
