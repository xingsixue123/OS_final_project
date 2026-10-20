#!/bin/bash
# 3_autoresearch UNION test chain for pool T1 (work/t1u_region2/PROTOCOL.md §6). Idempotent: relaunching resumes.
#   cd changes/3_autoresearch/work/union && setsid nohup bash src/chain_test_t1u.sh >> logs/chain_test_t1u.out 2>&1 < /dev/null &
set -uo pipefail
H="$(cd "$(dirname "$0")/.." && pwd)"
cd "$H"
source ./env.sh
REPO="$(cd "$H/../../../.." && pwd)"
export AR_TEST_DIR="$(cd "$H/../t1u_region2" && pwd)"
PROTO_REL="changes/3_autoresearch/work/t1u_region2/PROTOCOL.md"
log() { echo "[chain_t1u $(date +%F' '%T)] $*"; }
[ -f "$AR_TEST_DIR/CHAIN_DONE" ] && { log "CHAIN_DONE exists"; exit 0; }
log "start (pid $$)"

# 1. dev finalist (mechanical, chain_dev2.py)
while [ ! -f results/dev_finalist.json ]; do sleep 60; done
FIN=$(python3 -c "import json;print(json.load(open('results/dev_finalist.json'))['FINALIST'] or '')")
CTL=$(python3 -c "import json;print(json.load(open('results/dev_finalist.json')).get('CONTROL') or '')")
log "finalist '$FIN' control '$CTL'"
if [ -z "$FIN" ]; then
  echo "NO FINALIST by DEV_RULES R3 (R0 gate + finalist rule) (results/dev_finalist.json); T1 not spent; no TEST_GO. $(date +%F' '%T)" > "$AR_TEST_DIR/CHAIN_DONE"
  log "no finalist -> stop"; exit 0
fi
case "$FIN" in XA-F1PT|XG-F1PT) ;; *) log "unexpected finalist $FIN"; exit 1;; esac

# 2. G1_v4 gate
while [ ! -f results/g1v5_summary.json ]; do sleep 60; done
python3 -c "import json,sys;v=json.load(open('results/g1v5_summary.json'))['verdict'];sys.exit(0 if v['G1_v5_pass'] and v['v5_paths_pass'] else 1)" \
  || { log "G1_v5 not passed -> no TEST_GO"; exit 1; }

# 3. protocol committed and unchanged -> TEST_GO
HASH=$(git -C "$REPO" log -1 --format=%H -- "$PROTO_REL")
[ -n "$HASH" ] || { log "PROTOCOL.md not committed -> refuse"; exit 1; }
git -C "$REPO" diff --quiet "$HASH" -- "$PROTO_REL" || { log "PROTOCOL.md changed after its commit -> refuse"; exit 1; }
[ -f "$H/../t1_region2/TEST_GO" ] && { log "T1 already spent by work/t1_region2 -> refuse"; exit 1; }
[ -f "$AR_TEST_DIR/TEST_GO" ] || { printf '%s\nPOOL=T1\nFINALIST=%s\nCONTROL=%s\ncreated %s\n' "$HASH" "$FIN" "$CTL" "$(date -Is)" > "$AR_TEST_DIR/TEST_GO"; log "TEST_GO written ($HASH)"; }
mkdir -p "$AR_TEST_DIR/results_test"

# 4. static replays (frozen code) in parallel with the test
[ -f "$AR_TEST_DIR/results_test/static_baselines.csv" ] || src/sbx.sh src/prep.py static >> logs/prep_static_t1u.out 2>&1 &
SPID=$!

# 5. test
log "TEST: arms A B Aa Ba ${FIN/-/:} ${CTL/-/:} reps 1-3 (+ extra seeds)"
src/sbx.sh src/union.py --mode test --arms A B Aa Ba "${FIN/-/:}" "${CTL/-/:}" --reps 1 2 3 -j 14 >> logs/test_t1u.out 2>&1 || log "test driver rc=$?"
wait $SPID 2>/dev/null
[ -f "$AR_TEST_DIR/results_test/static_baselines.csv" ] || { log "static baselines missing"; exit 1; }

# 6. evaluation + integrity
python3 src/eval_test.py --test-dir "$AR_TEST_DIR" --pool T1 --Y "$FIN" --control "$CTL" >> logs/eval_t1u.out 2>&1 || log "eval rc=$?"
{ date -Is; bash "$REPO/changes/0_reproduce/check_frozen.sh" 2>&1 | tail -1
  echo "PATCH_v5.diff sha256: $(sha256sum PATCH_v5.diff | cut -c1-12)"; } > "$AR_TEST_DIR/results_test/integrity.txt"
echo "done $(date +%F' '%T); finalist $FIN" > "$AR_TEST_DIR/CHAIN_DONE"
log "CHAIN_DONE"
