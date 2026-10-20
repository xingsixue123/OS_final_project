#!/bin/bash
# 3_autoresearch UNION test chain for pool T2 (work/t2u_region4/PROTOCOL.md §6): the second spend, only if the union
# finalist was tested on T1 and did not pass. Idempotent.
#   cd changes/3_autoresearch/work/union_t2 && setsid nohup bash src/chain_test_t2u.sh >> logs/chain_test_t2u.out 2>&1 < /dev/null &
set -uo pipefail
H="$(cd "$(dirname "$0")/.." && pwd)"
cd "$H"
source ./env.sh
REPO="$(cd "$H/../../../.." && pwd)"
U="$H/../union"
T1="$H/../t1u_region2"
export AR_TEST_DIR="$(cd "$H/../t2u_region4" && pwd)"
PROTO_REL="changes/3_autoresearch/work/t2u_region4/PROTOCOL.md"
log() { echo "[chain_t2u $(date +%F' '%T)] $*"; }
[ -f "$AR_TEST_DIR/CHAIN_DONE" ] && { log "CHAIN_DONE exists"; exit 0; }
log "start (pid $$)"

# 1. the union dev finalist (fixed before any test; the same Y as T1)
while [ ! -f "$U/results/dev_finalist.json" ]; do sleep 120; done
FIN=$(python3 -c "import json;print(json.load(open('$U/results/dev_finalist.json'))['FINALIST'] or '')")
CTL=$(python3 -c "import json;print(json.load(open('$U/results/dev_finalist.json')).get('CONTROL') or '')")
log "finalist '$FIN' control '$CTL'"
if [ -z "$FIN" ]; then echo "NO union finalist; T2 not spent. $(date +%F' '%T)" > "$AR_TEST_DIR/CHAIN_DONE"; exit 0; fi
case "$FIN" in XA-F1PT|XG-F1PT) ;; *) log "unexpected finalist $FIN"; exit 1;; esac

# 2. T1 must have been spent on this finalist and must not have passed
while [ ! -f "$T1/CHAIN_DONE" ]; do sleep 120; done
if [ ! -f "$T1/TEST_GO" ]; then echo "T1 not spent; T2 not spent. $(date +%F' '%T)" > "$AR_TEST_DIR/CHAIN_DONE"; log "T1 not spent -> stop"; exit 0; fi
GOOD=$(python3 -c "import json;print(json.load(open('$T1/results_test/evaluation.json')).get('good_result'))")
log "T1 good_result=$GOOD"
if [ "$GOOD" = "True" ]; then echo "T1 passed; T2 not needed. $(date +%F' '%T)" > "$AR_TEST_DIR/CHAIN_DONE"; exit 0; fi
# ADDENDUM_T1_UNEVALUABLE.md (2026-10-20): a missing/None good_result (T1 TEST_GO + CHAIN_DONE present) = T1 not passed
if [ "$GOOD" != "False" ]; then log "T1 evaluation has no good_result ($GOOD): T1 closed as spent and failed (unevaluable) -> T2 proceeds as pre-registered"; fi

# 3. G1_v5, protocol committed and unchanged -> TEST_GO
python3 -c "import json,sys;v=json.load(open('$U/results/g1v5_summary.json'))['verdict'];sys.exit(0 if v['G1_v5_pass'] and v['v5_paths_pass'] else 1)" \
  || { log "G1_v5 not passed -> no TEST_GO"; exit 1; }
HASH=$(git -C "$REPO" log -1 --format=%H -- "$PROTO_REL")
[ -n "$HASH" ] || { log "PROTOCOL.md not committed -> refuse"; exit 1; }
git -C "$REPO" diff --quiet "$HASH" -- "$PROTO_REL" || { log "PROTOCOL.md changed after its commit -> refuse"; exit 1; }
[ -f "$AR_TEST_DIR/TEST_GO" ] || { printf '%s\nPOOL=T2\nFINALIST=%s\nCONTROL=%s\ncreated %s\n' "$HASH" "$FIN" "$CTL" "$(date -Is)" > "$AR_TEST_DIR/TEST_GO"; log "TEST_GO written ($HASH)"; }
mkdir -p "$AR_TEST_DIR/results_test"

# 4. static replays + test
[ -f "$AR_TEST_DIR/results_test/static_baselines.csv" ] || src/sbx.sh src/prep.py static >> logs/prep_static_t2u.out 2>&1 &
SPID=$!
log "TEST: arms A B Aa Ba ${FIN/-/:} ${CTL/-/:} reps 1-3 (+ extra seeds)"
src/sbx.sh src/union.py --mode test --arms A B Aa Ba "${FIN/-/:}" "${CTL/-/:}" --reps 1 2 3 -j 14 >> logs/test_t2u.out 2>&1 || log "test driver rc=$?"
wait $SPID 2>/dev/null
[ -f "$AR_TEST_DIR/results_test/static_baselines.csv" ] || { log "static baselines missing"; exit 1; }

# 5. evaluation + integrity
python3 src/eval_test.py --test-dir "$AR_TEST_DIR" --pool T2 --Y "$FIN" --control "$CTL" >> logs/eval_t2u.out 2>&1 || log "eval rc=$?"
{ date -Is; bash "$REPO/changes/0_reproduce/check_frozen.sh" 2>&1 | tail -1
  echo "PATCH_v5.diff sha256: $(sha256sum PATCH_v5.diff | cut -c1-12)"; } > "$AR_TEST_DIR/results_test/integrity.txt"
echo "done $(date +%F' '%T); finalist $FIN" > "$AR_TEST_DIR/CHAIN_DONE"
log "CHAIN_DONE"
