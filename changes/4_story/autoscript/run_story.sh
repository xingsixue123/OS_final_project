#!/bin/bash
# Build changes/4_story/STORY.md with a 5-round write -> check -> self-grill loop (headless Claude Opus 5.5 1M,
# effort xhigh, permissions skipped by the captain's instruction). Runs all ROUNDS (default 5).
#   changes/4_story/autoscript/run_story.sh --detach
#   RUN_ID=<same id> changes/4_story/autoscript/run_story.sh --detach   # resume
set -Eeuo pipefail

ROOT="${ROOT:-/home/sxing/project/OS_final_project/changes/4_story}"
REPO="$(cd "$ROOT/../.." && pwd)"
AS="$ROOT/autoscript"
RESULT="$ROOT/result"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
RUN_DIR="$ROOT/output/runs/$RUN_ID"
ROUNDS="${ROUNDS:-5}"
ROUND_HOURS="${ROUND_HOURS:-4}"
PB_MODEL="${PB_MODEL:-claude-opus-5-5[1m]}"
PB_EFFORT="${PB_EFFORT:-xhigh}"
PUSH_URL="${PUSH_URL:-git@github.com:xingsixue123/OS_final_project.git}"
BRANCH="${BRANCH:-phase2-deployable-peak}"
VALIDATORS=(citation grill)

log() { mkdir -p "$RUN_DIR"; printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$RUN_DIR/launcher.log" >> "$ROOT/output/launcher_all.log"; }

claude_run() {  # <prompt> <events> <stderr> <timeout> [extra args]
  local prompt="$1" ev="$2" er="$3" tmo="$4"; shift 4
  ( cd "$REPO" && timeout --signal=TERM "$tmo" claude -p --model "$PB_MODEL" --effort "$PB_EFFORT" \
      --dangerously-skip-permissions --output-format stream-json --verbose "$@" < "$prompt" ) > "$ev" 2> "$er"
}

feedback() {
  local v f
  for v in "${VALIDATORS[@]}"; do
    f="$(find "$RESULT" -maxdepth 1 -name "validator_${v}_round_*.md" | sort -V | tail -n1)"
    if [[ -n "$f" ]]; then printf '\n### Latest %s validator feedback (`%s`)\n```text\n' "$v" "${f#$REPO/}"; tail -n 300 "$f"; printf '\n```\n'; fi
  done
  if [[ -f "$RESULT/check_story.json" ]]; then printf '\n### check_story.py (latest)\n```json\n'; head -c 8000 "$RESULT/check_story.json"; printf '\n```\n'; fi
  return 0
}

run_round() {
  local r="$1" p="$RUN_DIR/worker_prompt_round_$1.md" res=() sid s
  {
    cat "$AS/agent_prompt.md"
    printf '\n## Runtime context\n- Run %s, round %s of %s, time %s. This round is cut off after %s h.\n' "$RUN_ID" "$r" "$ROUNDS" "$(date -Is)" "$ROUND_HOURS"
    if (( r == ROUNDS )); then printf -- '- FINAL round: leave STORY.md complete, consistent and passing check_story.py.\n'; fi
    if (( r > 1 )); then printf '\n## Feedback to resolve\n'; feedback; fi
  } > "$p"
  [[ -s "$RUN_DIR/worker_session_id" ]] && res=(--resume "$(cat "$RUN_DIR/worker_session_id")")
  log "writer round $r ${res[*]:-new session}"
  set +e; claude_run "$p" "$RUN_DIR/worker_events_round_$r.jsonl" "$RUN_DIR/worker_stderr_round_$r.log" $(( ROUND_HOURS * 3600 )) "${res[@]}"; s=$?; set -e
  sid="$(grep -o '"session_id":"[^"]*"' "$RUN_DIR/worker_events_round_$r.jsonl" | tail -n1 | cut -d'"' -f4 || true)"
  [[ -n "$sid" ]] && echo "$sid" > "$RUN_DIR/worker_session_id"
  log "writer round $r status=$s"
  set +e; python3 "$ROOT/code/check_story.py" > "$RUN_DIR/check_round_$r.log" 2>&1; s=$?; set -e
  log "check_story round $r exit=$s"
  local v out vp
  for v in "${VALIDATORS[@]}"; do
    out="$RESULT/validator_${v}_round_$r.md"; vp="$RUN_DIR/${v}_prompt_round_$r.md"
    { cat "$AS/validator_prompts/${v}_prompt.md"; printf '\n## Runtime context\n- Round %s of %s\n- Required output path: `%s`\n' "$r" "$ROUNDS" "$out"; } > "$vp"
    log "validator $v round $r"
    set +e; claude_run "$vp" "$RUN_DIR/${v}_events_round_$r.jsonl" "$RUN_DIR/${v}_stderr_round_$r.log" 7200; set -e
    if [[ ! -s "$out" ]]; then
      grep '"type":"result"' "$RUN_DIR/${v}_events_round_$r.jsonl" | tail -n1 \
        | python3 -c 'import json,sys; t=sys.stdin.read(); print(json.loads(t).get("result","") if t.strip() else "")' > "$out" 2>/dev/null || true
    fi
    log "validator $v round $r: $(grep -h 'VALIDATOR_STATUS=' "$out" | tail -n1) $(grep -h 'OPEN_FINDINGS=' "$out" | tail -n1)"
  done
  cd "$REPO"
  if python3 tools/privacy_scrub.py --check > "$RUN_DIR/privacy_round_$r.log" 2>&1; then
    git add changes/4_story > /dev/null 2>&1 || true
    git diff --cached --quiet || git commit -q -m "4_story: round $r ($RUN_ID) [auto]" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>" || true
    if git push -q "$PUSH_URL" "$BRANCH" >> "$RUN_DIR/push.log" 2>&1; then log "pushed round $r"; else log "push failed round $r"; fi
  else
    log "privacy check failed; round $r not committed"
  fi
  cd "$ROOT"
}

run_loop() {
  mkdir -p "$RUN_DIR" "$RESULT"
  local r; r=$(( $(find "$RUN_DIR" -maxdepth 1 -name "worker_prompt_round_*.md" | wc -l) + 1 ))
  while (( r <= ROUNDS )); do
    printf 'STATUS=RUNNING\nROUND=%s/%s\nRUN_ID=%s\nTIME=%s\n' "$r" "$ROUNDS" "$RUN_ID" "$(date -Is)" > "$RESULT/LOOP_STATUS.txt"
    run_round "$r"; r=$(( r + 1 ))
  done
  printf 'STATUS=DONE\nROUNDS=%s\nRUN_ID=%s\nTIME=%s\n' "$ROUNDS" "$RUN_ID" "$(date -Is)" > "$RESULT/LOOP_STATUS.txt"
  log "all $ROUNDS rounds done"
}

case "${1:-}" in
  --foreground) run_loop ;;
  --detach)
    mkdir -p "$RUN_DIR"
    setsid nohup env RUN_ID="$RUN_ID" ROUNDS="$ROUNDS" ROUND_HOURS="$ROUND_HOURS" PB_MODEL="$PB_MODEL" PB_EFFORT="$PB_EFFORT" \
      "$AS/run_story.sh" --foreground > "$RUN_DIR/nohup.out" 2>&1 < /dev/null &
    echo "$!" > "$RUN_DIR/launcher.pid"; echo "$RUN_ID" > "$ROOT/output/latest_run_id"
    echo "detached: run $RUN_ID pid $(cat "$RUN_DIR/launcher.pid")" ;;
  *) echo "usage: $0 --detach | --foreground"; exit 1 ;;
esac
