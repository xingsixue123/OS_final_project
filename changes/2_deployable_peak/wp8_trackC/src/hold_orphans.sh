#!/bin/bash
# Hold one SimSlot per running simulate_ap python process (after a driver restart), released as each one exits.
D="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; source "$D/env.sh"; cd "$D"
SP=$(pgrep -f "^/home.*python -B -m BCacheSim.cachesim.simulate_ap" | tr '\n' ' ')
echo "orphans: $SP"
exec taskset -c 0-23 bwrap --dev-bind / / --bind "$D/work/systmp" /tmp -- "$BALEEN_PY" -B src/hold_slots.py $SP
