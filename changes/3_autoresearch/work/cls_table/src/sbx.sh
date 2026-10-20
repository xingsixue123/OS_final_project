#!/bin/bash
# Run one Baleen-env (or solver-env, PY=...) python command inside the WP10 sandbox:
# taskset -c 0-23 bwrap --dev-bind / / --bind <private job tmp> /tmp -- <env python> -B ...
# Usage: src/sbx.sh [args to python...]   (env.sh must be sourced; cwd is kept)
set -euo pipefail
: "${AR_ROOT:?source wp10_schedule/env.sh first}"
PYBIN="${PY:-$BALEEN_PY}"
JT="$AR_ROOT/.cache/jobtmp/sbx_$$_$(date +%s%N)"
mkdir -p "$JT"
trap 'rm -rf "$JT"' EXIT
taskset -c "${CPUS:-0-23}" bwrap --dev-bind / / --bind "$JT" /tmp -- "$PYBIN" -B "$@"
