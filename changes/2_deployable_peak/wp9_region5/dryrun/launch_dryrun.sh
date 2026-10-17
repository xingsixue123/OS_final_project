#!/bin/bash
# Waits for the Region5 s0 fullml dump, then runs the WP9 pipeline dry run (Region5 s0, arm A, 1 retrain).
cd "$(dirname "$0")/.." && source env.sh
until grep -q "fullml_Region5_s0.npz" logs/prep_dumps.out; do sleep 15; done
exec taskset -c 0-23 $BALEEN_PY -B src/wp9.py --mode dryrun --arms A --insts Region5_s0 --reps 1 -j 1
