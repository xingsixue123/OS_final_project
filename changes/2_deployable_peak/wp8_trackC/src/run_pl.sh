#!/bin/bash
# PL validation then PM (resumable; skips ledger keys already present)
D="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$D"
src/run.sh baleen ../src/pl_eval.py --what wp2 > logs/pl_wp2.out 2>&1
src/run.sh baleen ../src/pl_eval.py --what pm > logs/pm_eval.out 2>&1
