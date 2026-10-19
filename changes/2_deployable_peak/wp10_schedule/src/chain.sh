#!/bin/bash
# WP10 detached chain (PROTOCOL_v2_H5 §8). Idempotent: relaunching resumes (every driver skips finished work).
#   cd changes/2_deployable_peak/wp10_schedule && setsid nohup bash src/chain.sh >> logs/chain.out 2>&1 < /dev/null &
# Every Python step runs through src/sbx.sh (taskset -c 0-23 bwrap ... private /tmp); trains/sims are sandboxed by the
# drivers as before (train lock, SimSlot cap 14).
set -uo pipefail
H="$(cd "$(dirname "$0")/.." && pwd)"
cd "$H"
source ./env.sh
log() { echo "[chain $(date +%F' '%T)] $*"; }
[ -f results/CHAIN_DONE ] && { log "CHAIN_DONE exists; nothing to do"; exit 0; }
log "start (pid $$)"

# (a) wait for the E3 confirmation driver to exit
while pgrep -f "src/wp10.py --mode dev" > /dev/null; do sleep 60; done
log "E3 confirmation driver not running; trials_dev rows: $(($(wc -l < trials_dev.csv) - 1))"

# (b) finalist rule (unchanged) -> results/finalist.json
src/sbx.sh src/e3_eval.py || { log "e3_eval failed"; exit 1; }
FIN=$("$BALEEN_PY" -B -c "import json;print(json.load(open('results/finalist.json'))['FINALIST'] or '')")
log "finalist: '${FIN}'"

# (c) no finalist -> stop
if [ -z "$FIN" ]; then
  echo "NO FINALIST by the PROGRESS.md finalist rule (results/e3_finalist.json); no E4 test run. $(date +%F' '%T)" > results/CHAIN_DONE
  log "no finalist -> CHAIN_DONE"; exit 0
fi
case "$FIN" in TA-pt) ARMS="A B Aa Ba TA:pt TA:cd";; TB-pt) ARMS="A B Aa Ba TB:pt TB:cd";; *) log "unexpected finalist $FIN"; exit 1;; esac

# (d) TEST_GO (the protocol was committed before this chain was launched), statics, dry run, test
git -C "$H" log --oneline -1 -- PROTOCOL_v2_H5.md | grep -q . || { log "PROTOCOL_v2_H5.md not committed -> refuse"; exit 1; }
[ -f TEST_GO ] || { date +%F' '%T > TEST_GO; log "TEST_GO created"; }
log "static replays (frozen code)"
[ -f results_test/static_baselines.csv ] || src/sbx.sh src/prep.py static --keys Region1_s0.1 Region1_s0.2 Region1_s0.3 Region1_s0.4 Region1_s0.5 Region1_s0.6 >> logs/prep_static.out 2>&1 &
SPID=$!
log "dry run Region1 s0 (resume)"
src/sbx.sh src/wp10.py --mode dryrun --arms A ${FIN/-/:} ${FIN/-pt/:cd} --reps 1 -j 6 >> logs/dryrun.out 2>&1 || log "dry run driver rc=$?"
log "TEST: arms $ARMS reps 1-3 (+ extra seeds)"
src/sbx.sh src/wp10.py --mode test --arms $ARMS --reps 1 2 3 -j 16 >> logs/test.out 2>&1 || log "test driver rc=$?"
wait $SPID 2>/dev/null
[ -f results_test/static_baselines.csv ] || { log "static baselines missing"; exit 1; }

# (e) evaluation
src/sbx.sh src/evaluate_test.py --finalist "$FIN" >> logs/evaluate_test.out 2>&1 || { log "evaluate_test failed"; exit 1; }
log "evaluation -> results_test/evaluation.json"

# (f) integrity
{ date +%F' '%T; bash ../../0_reproduce/check_frozen.sh 2>&1 | tail -1
  echo "files under 0_reproduce/1_literature_review newer than .leak_marker:"
  find ../../0_reproduce ../../1_literature_review -newer .leak_marker -type f 2>/dev/null | wc -l
  echo "known foreign cpython-312/313 pyc (dated):"; find ../../0_reproduce ../../1_literature_review -name '*.cpython-31[23]*.pyc' -printf '%TY-%Tm-%Td\n' 2>/dev/null | sort | uniq -c
  echo "PATCH_v3.diff sha256: $(sha256sum PATCH_v3.diff | cut -c1-12); wp0 PATCH.diff: $(sha256sum ../wp0_overlay/PATCH.diff | cut -c1-12)"
} > results_test/integrity.txt
log "integrity -> results_test/integrity.txt"

# (g)
echo "done $(date +%F' '%T); finalist $FIN" > results/CHAIN_DONE
log "CHAIN_DONE"
