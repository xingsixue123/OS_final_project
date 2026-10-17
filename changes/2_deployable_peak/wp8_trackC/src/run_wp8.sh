#!/bin/bash
# Stage-2 driver launcher: the driver itself also runs under taskset + bwrap (private /tmp); it spawns its own
# bwrap'd train/sim jobs (nested bwrap verified). Usage: src/run_wp8.sh '<queue json>' <logname>
D="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$D/env.sh"
JT="$D/work/systmp/driver_$$_$(date +%s%N)"; mkdir -p "$JT"
cd "$D"
taskset -c 0-23 bwrap --dev-bind / / --bind "$JT" /tmp -- "$BALEEN_PY" -B src/wp8.py --queue "$1" -j 16 >> "logs/$2" 2>&1
rm -rf "$JT"
