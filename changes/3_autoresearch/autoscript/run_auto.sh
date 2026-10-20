#!/bin/bash
# PeakBaleen auto-research loop: headless Claude Code worker + validators (captain's instruction 2026-10-20:
# Opus 5.5 1M, effort xhigh, permissions skipped, background, killed after 24 h).
# worker round -> deterministic validation (code/validate.py) -> 2 independent validators -> git sync -> next round,
# until a GOOD RESULT passes every gate, the worker declares the test budget exhausted, or the deadline is reached.
#   autoscript/run_auto.sh --detach                       # new run (setsid nohup; survives session loss)
#   RUN_ID=<same id> autoscript/run_auto.sh --detach      # continue a dead run with the same deadline
set -Eeuo pipefail

CHANGE_ROOT="${CHANGE_ROOT:-/home/sxing/project/OS_final_project/changes/3_autoresearch}"
REPO="$(cd "$CHANGE_ROOT/../.." && pwd)"
AUTOSCRIPT_DIR="$CHANGE_ROOT/autoscript"
RUNS_DIR="$CHANGE_ROOT/output/auto_runs"
RESULT_DIR="$CHANGE_ROOT/result"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
RUN_DIR="$RUNS_DIR/$RUN_ID"
DEADLINE_HOURS="${DEADLINE_HOURS:-24}"
ROUND_HOURS="${ROUND_HOURS:-6}"
SLEEP_SECONDS="${SLEEP_SECONDS:-60}"
CLAUDE_MODEL="${CLAUDE_MODEL:-claude-opus-5-5[1m]}"
CLAUDE_EFFORT="${CLAUDE_EFFORT:-xhigh}"
PUSH_URL="${PUSH_URL:-git@github.com:xingsixue123/OS_final_project.git}"
BRANCH="${BRANCH:-phase2-deployable-peak}"
VALIDATORS=(red_team integrity_stats)

log() { mkdir -p "$RUN_DIR"; printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$RUN_DIR/launcher.log" >> "$CHANGE_ROOT/output/launcher_all.log"; }

preflight() {
  command -v claude >/dev/null || { echo "claude not found"; exit 1; }
  [[ -s "$AUTOSCRIPT_DIR/agent_prompt.md" && -s "$AUTOSCRIPT_DIR/GOOD_RESULT.sha256" ]] || { echo "missing prompt/contract hash"; exit 1; }
  mkdir -p "$RUN_DIR" "$RESULT_DIR"
}

remaining() { echo $(( $(cat "$RUN_DIR/deadline.epoch") - $(date +%s) )); }

claude_run() {  # claude_run <prompt file> <events file> <stderr file> <timeout s> [extra args...]
  local prompt="$1" ev="$2" er="$3" tmo="$4"; shift 4
  ( cd "$REPO" && timeout --signal=TERM "$tmo" claude -p --model "$CLAUDE_MODEL" --effort "$CLAUDE_EFFORT" \
      --dangerously-skip-permissions --output-format stream-json --verbose "$@" < "$prompt" ) > "$ev" 2> "$er"
}

feedback() {
  local v f
  for v in "${VALIDATORS[@]}"; do
    f="$(find "$RESULT_DIR" -maxdepth 1 -name "validator_${v}_round_*.md" | sort -V | tail -n1)"
    if [[ -n "$f" ]]; then printf '\n### Latest %s validator feedback (`%s`)\n```text\n' "$v" "${f#$REPO/}"; tail -n 200 "$f"; printf '\n```\n'; fi
  done
  if [[ -f "$RESULT_DIR/deterministic_validation.json" ]]; then
    printf '\n### Deterministic validation (latest)\n```json\n'; head -c 6000 "$RESULT_DIR/deterministic_validation.json"; printf '\n```\n'
  fi
  return 0
}

worker_prompt() {
  local round="$1" tmo="$2" p="$RUN_DIR/worker_prompt_round_$1.md"
  {
    cat "$AUTOSCRIPT_DIR/agent_prompt.md"
    printf '\n## Runtime context\n- Run ID `%s`, round %s, time now %s\n' "$RUN_ID" "$round" "$(date -Is)"
    printf -- '- Hard deadline %s (%s s left). This round is cut off after %s s.\n' "$(date -d @"$(cat "$RUN_DIR/deadline.epoch")" -Is)" "$(remaining)" "$tmo"
    printf -- '- Before the cut-off, leave detached jobs running with RESUME notes in result/STATUS.md.\n'
    printf -- '- When the test budget is spent and no claim passes, write result/FINAL_REPORT.md and result/STOP_EXHAUSTED.\n'
    if (( round > 1 )); then printf '\n## Feedback to resolve (validators are fail-closed)\n'; feedback; fi
  } > "$p"
  echo "$p"
}

run_worker() {
  local round="$1" tmo="$2" prompt res=() t0 s sid
  prompt="$(worker_prompt "$round" "$tmo")"
  [[ -s "$RUN_DIR/worker_session_id" ]] && res=(--resume "$(cat "$RUN_DIR/worker_session_id")")
  log "worker round $round (timeout ${tmo}s) ${res[*]:-new session}"
  t0=$(date +%s)
  set +e
  claude_run "$prompt" "$RUN_DIR/worker_events_round_$round.jsonl" "$RUN_DIR/worker_stderr_round_$round.log" "$tmo" "${res[@]}"
  s=$?
  set -e
  sid="$(grep -o '"session_id":"[^"]*"' "$RUN_DIR/worker_events_round_$round.jsonl" | tail -n1 | cut -d'"' -f4 || true)"
  [[ -n "$sid" ]] && echo "$sid" > "$RUN_DIR/worker_session_id"
  WORKER_SECS=$(( $(date +%s) - t0 )); WORKER_STATUS=$s
  log "worker round $round status=$s secs=$WORKER_SECS"
}

run_validator() {
  local v="$1" round="$2" out="$RESULT_DIR/validator_${1}_round_${2}.md" p="$RUN_DIR/${1}_validator_prompt_round_${2}.md"
  {
    cat "$AUTOSCRIPT_DIR/validator_prompts/${v}_prompt.md"
    printf '\n## Runtime context\n- Run %s, round %s\n- Required output path: `%s`\n- Do not edit worker code or results; no git writes.\n' "$RUN_ID" "$round" "$out"
  } > "$p"
  log "validator $v round $round"
  set +e
  claude_run "$p" "$RUN_DIR/${v}_events_round_$round.jsonl" "$RUN_DIR/${v}_stderr_round_$round.log" 7200
  set -e
  if [[ ! -s "$out" ]]; then
    grep '"type":"result"' "$RUN_DIR/${v}_events_round_$round.jsonl" | tail -n1 \
      | python3 -c 'import json,sys; t=sys.stdin.read(); print(json.loads(t).get("result","") if t.strip() else "")' > "$out" 2>/dev/null || true
  fi
}

validators_pass() {
  local ok=0 f v
  for v in "${VALIDATORS[@]}"; do
    f="$(find "$RESULT_DIR" -maxdepth 1 -name "validator_${v}_round_*.md" | sort -V | tail -n1)"
    if [[ -z "$f" ]] || ! grep -q 'VALIDATOR_STATUS=PASS' "$f" || ! grep -q 'OPEN_FINDINGS=0' "$f"; then ok=1; fi
  done
  return $ok
}

sync_git() {
  cd "$REPO"
  if python3 tools/privacy_scrub.py --check > "$RUN_DIR/privacy_round_$1.log" 2>&1; then
    git add changes/3_autoresearch > /dev/null 2>&1 || true
    if ! git diff --cached --quiet; then
      git commit -q -m "3_autoresearch: round $1 ($RUN_ID) [auto]" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" || true
    fi
    if git push -q "$PUSH_URL" "$BRANCH" >> "$RUN_DIR/push.log" 2>&1; then log "pushed round $1"; else log "push failed round $1"; fi
  else
    log "privacy check failed; not committing round $1 (see privacy_round_$1.log)"
  fi
  cd "$CHANGE_ROOT"
}

status() { printf 'STATUS=%s\nROUND=%s\nRUN_ID=%s\nTIME=%s\n' "$1" "$2" "$RUN_ID" "$(date -Is)" | tee "$RUN_DIR/status" > "$RESULT_DIR/LOOP_STATUS.txt"; }

run_loop() {
  preflight
  [[ -s "$RUN_DIR/deadline.epoch" ]] || echo $(( $(date +%s) + DEADLINE_HOURS * 3600 )) > "$RUN_DIR/deadline.epoch"
  local round rem tmo det fails=0
  round=$(( $(find "$RUN_DIR" -maxdepth 1 -name "worker_prompt_round_*.md" | wc -l) + 1 ))
  while true; do
    rem="$(remaining)"
    if (( rem <= 600 )); then status DEADLINE "$round"; log "deadline reached"; sync_git "$round"; exit 3; fi
    tmo=$(( ROUND_HOURS * 3600 < rem ? ROUND_HOURS * 3600 : rem ))
    status RUNNING "$round"
    run_worker "$round" "$tmo"
    if (( WORKER_STATUS != 0 && WORKER_SECS < 300 )); then
      fails=$(( fails + 1 )); log "worker failed fast ($fails in a row)"
      if (( fails >= 3 )); then status ERROR "$round"; log "3 fast worker failures; stopping (see worker_stderr)"; exit 5; fi
      round=$(( round + 1 )); sleep 300; continue
    fi
    fails=0
    set +e; python3 "$CHANGE_ROOT/code/validate.py" > "$RUN_DIR/validation_round_$round.log" 2>&1; det=$?; set -e
    log "deterministic validation round $round exit=$det"
    for v in "${VALIDATORS[@]}"; do run_validator "$v" "$round"; done
    sync_git "$round"
    if [[ "$det" == 0 ]] && validators_pass; then status PASS "$round"; log "GOOD RESULT: all gates passed"; exit 0; fi
    if [[ -f "$RESULT_DIR/STOP_EXHAUSTED" ]]; then status EXHAUSTED "$round"; log "worker declared budget exhausted"; exit 4; fi
    round=$(( round + 1 )); sleep "$SLEEP_SECONDS"
  done
}

case "${1:-}" in
  --foreground) run_loop ;;
  --detach)
    preflight
    setsid nohup env RUN_ID="$RUN_ID" DEADLINE_HOURS="$DEADLINE_HOURS" ROUND_HOURS="$ROUND_HOURS" \
      CLAUDE_MODEL="$CLAUDE_MODEL" CLAUDE_EFFORT="$CLAUDE_EFFORT" \
      "$AUTOSCRIPT_DIR/run_auto.sh" --foreground > "$RUN_DIR/nohup.out" 2>&1 < /dev/null &
    echo "$!" > "$RUN_DIR/launcher.pid"; echo "$RUN_ID" > "$CHANGE_ROOT/output/latest_run_id"
    echo "detached: run $RUN_ID pid $(cat "$RUN_DIR/launcher.pid")" ;;
  *) echo "usage: $0 --detach | --foreground"; exit 1 ;;
esac
