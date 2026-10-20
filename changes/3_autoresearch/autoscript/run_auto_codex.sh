#!/bin/bash
# PeakBaleen auto-research loop (pattern of autoresearch/neural_bench run_step10_new_flip_codex.sh):
# worker round -> deterministic validation -> independent validators -> feedback -> next round,
# until a GOOD RESULT passes every gate, the worker declares the budget exhausted, or the deadline is reached.
#   autoscript/run_auto_codex.sh --detach        # setsid nohup, survives session loss
#   RESUME_FROM_RUN_ID=<id> autoscript/run_auto_codex.sh --detach
set -Eeuo pipefail

CHANGE_ROOT="${CHANGE_ROOT:-/home/sxing/project/OS_final_project/changes/3_autoresearch}"
REPO="$(cd "$CHANGE_ROOT/../.." && pwd)"
AUTOSCRIPT_DIR="$CHANGE_ROOT/autoscript"
RUNS_DIR="$CHANGE_ROOT/output/codex_auto_runs"
RESULT_DIR="$CHANGE_ROOT/result"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
RUN_DIR="$RUNS_DIR/$RUN_ID"
DEADLINE_HOURS="${DEADLINE_HOURS:-24}"
ROUND_HOURS="${ROUND_HOURS:-6}"
SLEEP_SECONDS="${SLEEP_SECONDS:-60}"
CODEX_MODEL="${CODEX_MODEL:-gpt-5.5}"
CODEX_REASONING_EFFORT="${CODEX_REASONING_EFFORT:-xhigh}"
RESUME_FROM_RUN_ID="${RESUME_FROM_RUN_ID:-}"
PUSH_URL="${PUSH_URL:-git@github.com:xingsixue123/OS_final_project.git}"
BRANCH="${BRANCH:-phase2-deployable-peak}"
VALIDATORS=(red_team integrity_stats)

log() { mkdir -p "$RUN_DIR"; printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$RUN_DIR/launcher.log" >> "$CHANGE_ROOT/output/launcher_all.log"; }

preflight() {
  command -v codex >/dev/null || { echo "codex not found"; exit 1; }
  [[ -s "$AUTOSCRIPT_DIR/agent_prompt.md" && -s "$AUTOSCRIPT_DIR/GOOD_RESULT.sha256" ]] || { echo "missing prompt/contract hash"; exit 1; }
  mkdir -p "$RUN_DIR" "$RESULT_DIR"
}

margs() { printf '%s\n' -m "$CODEX_MODEL" -c "model_reasoning_effort=\"$CODEX_REASONING_EFFORT\"" -c 'approval_policy="never"'; }

remaining() { echo $(( $(cat "$RUN_DIR/deadline.epoch") - $(date +%s) )); }

feedback() {
  for v in "${VALIDATORS[@]}"; do
    local f; f="$(ls "$RESULT_DIR"/validator_${v}_round_*.md 2>/dev/null | sort -V | tail -n1 || true)"
    [[ -n "$f" ]] && { printf '\n### Latest %s validator feedback (`%s`)\n```text\n' "$v" "${f#$REPO/}"; tail -n 200 "$f"; printf '\n```\n'; }
  done
  [[ -f "$RESULT_DIR/deterministic_validation.json" ]] && { printf '\n### Deterministic validation (latest)\n```json\n'; head -c 6000 "$RESULT_DIR/deterministic_validation.json"; printf '\n```\n'; }
  return 0
}

worker_prompt() {
  local round="$1" p="$RUN_DIR/worker_prompt_round_$1.md"
  { cat "$AUTOSCRIPT_DIR/agent_prompt.md"
    printf '\n## Runtime context\n- Run ID `%s`, round %s, time now %s\n' "$RUN_ID" "$round" "$(date -Is)"
    printf -- '- Hard deadline %s (%s s left). This round is cut off after %s s.\n' "$(date -d @"$(cat "$RUN_DIR/deadline.epoch")" -Is)" "$(remaining)" "$2"
    printf -- '- Before the cut-off, leave detached jobs running with RESUME notes in result/STATUS.md.\n'
    printf -- '- When the test budget is spent and no claim passes, write result/FINAL_REPORT.md and result/STOP_EXHAUSTED.\n'
    (( round > 1 )) && { printf '\n## Feedback to resolve (validators are fail-closed)\n'; feedback; }
  } > "$p"
  echo "$p"
}

run_worker() {
  local round="$1" tmo="$2" prompt; prompt="$(worker_prompt "$round" "$tmo")"
  local ev="$RUN_DIR/worker_events_round_$round.jsonl" er="$RUN_DIR/worker_stderr_round_$round.log" fin="$RUN_DIR/worker_final_round_$round.md"
  local a; mapfile -t a < <(margs)
  [[ "$round" == 1 && -n "$RESUME_FROM_RUN_ID" && -s "$RUNS_DIR/$RESUME_FROM_RUN_ID/worker_thread_id" ]] && cp "$RUNS_DIR/$RESUME_FROM_RUN_ID/worker_thread_id" "$RUN_DIR/"
  log "worker round $round (timeout ${tmo}s)"
  set +e
  if [[ -s "$RUN_DIR/worker_thread_id" ]]; then
    timeout --signal=TERM "$tmo" codex exec resume --ignore-user-config --json -o "$fin" "${a[@]}" -c 'sandbox_mode="danger-full-access"' "$(cat "$RUN_DIR/worker_thread_id")" - < "$prompt" > "$ev" 2> "$er"
  else
    timeout --signal=TERM "$tmo" codex exec --ignore-user-config -C "$REPO" --sandbox danger-full-access --json -o "$fin" "${a[@]}" - < "$prompt" > "$ev" 2> "$er"
    local tid; tid="$(sed -n 's/.*"thread_id":"\([^"]*\)".*/\1/p' "$ev" | head -n1)"
    [[ -n "$tid" ]] && echo "$tid" > "$RUN_DIR/worker_thread_id"
  fi
  local s=$?; set -e; log "worker round $round status=$s"
}

run_validator() {
  local v="$1" round="$2" out="$RESULT_DIR/validator_${1}_round_${2}.md" p="$RUN_DIR/${1}_validator_prompt_round_${2}.md"
  local a; mapfile -t a < <(margs)
  { cat "$AUTOSCRIPT_DIR/validator_prompts/${v}_prompt.md"
    printf '\n## Runtime context\n- Run %s, round %s\n- Required output path: `%s`\n- Do not edit worker code or results.\n' "$RUN_ID" "$round" "$out"
  } > "$p"
  log "validator $v round $round"
  set +e
  timeout 7200 codex exec --ignore-user-config -C "$REPO" --sandbox workspace-write --json -o "$RUN_DIR/${v}_final_round_$round.md" "${a[@]}" - < "$p" > "$RUN_DIR/${v}_events_round_$round.jsonl" 2> "$RUN_DIR/${v}_stderr_round_$round.log"
  set -e
  [[ -s "$out" ]] || cp "$RUN_DIR/${v}_final_round_$round.md" "$out" 2>/dev/null || true
}

validators_pass() {
  local ok=0 f
  for v in "${VALIDATORS[@]}"; do
    f="$(ls "$RESULT_DIR"/validator_${v}_round_*.md 2>/dev/null | sort -V | tail -n1 || true)"
    [[ -n "$f" ]] && grep -q 'VALIDATOR_STATUS=PASS' "$f" && grep -q 'OPEN_FINDINGS=0' "$f" || ok=1
  done
  return $ok
}

sync_git() {
  cd "$REPO"
  if python3 tools/privacy_scrub.py --check > "$RUN_DIR/privacy_round_$1.log" 2>&1; then
    git add changes/3_autoresearch >/dev/null 2>&1 || true
    if ! git diff --cached --quiet; then
      git commit -q -m "3_autoresearch: round $1 ($RUN_ID) [auto]" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" || true
    fi
    git push -q "$PUSH_URL" "$BRANCH" >> "$RUN_DIR/push.log" 2>&1 && log "pushed round $1" || log "push failed round $1"
  else
    log "privacy check failed; not committing round $1 (see privacy_round_$1.log)"
  fi
  cd "$CHANGE_ROOT"
}

status() { printf 'STATUS=%s\nROUND=%s\nRUN_ID=%s\nTIME=%s\n' "$1" "$2" "$RUN_ID" "$(date -Is)" | tee "$RUN_DIR/status" > "$RESULT_DIR/LOOP_STATUS.txt"; }

run_loop() {
  preflight
  [[ -s "$RUN_DIR/deadline.epoch" ]] || echo $(( $(date +%s) + DEADLINE_HOURS * 3600 )) > "$RUN_DIR/deadline.epoch"
  local round; round=$(( $(find "$RUN_DIR" -maxdepth 1 -name "worker_prompt_round_*.md" | wc -l) + 1 ))
  while true; do
    local rem; rem="$(remaining)"
    (( rem > 600 )) || { status DEADLINE "$round"; log "deadline reached"; sync_git "$round"; exit 3; }
    local tmo=$(( ROUND_HOURS * 3600 < rem ? ROUND_HOURS * 3600 : rem ))
    status RUNNING "$round"
    run_worker "$round" "$tmo"
    set +e; python3 "$CHANGE_ROOT/code/validate.py" > "$RUN_DIR/validation_round_$round.log" 2>&1; local det=$?; set -e
    log "deterministic validation round $round exit=$det"
    for v in "${VALIDATORS[@]}"; do run_validator "$v" "$round"; done
    sync_git "$round"
    if [[ "$det" == 0 ]] && validators_pass; then status PASS "$round"; log "GOOD RESULT: all gates passed"; exit 0; fi
    if [[ -f "$RESULT_DIR/STOP_EXHAUSTED" ]]; then status EXHAUSTED "$round"; log "worker declared budget exhausted"; exit 4; fi
    round=$((round + 1)); sleep "$SLEEP_SECONDS"
  done
}

case "${1:-}" in
  --foreground) run_loop ;;
  --detach)
    preflight
    RUN_ID="$RUN_ID" setsid nohup env RUN_ID="$RUN_ID" DEADLINE_HOURS="$DEADLINE_HOURS" ROUND_HOURS="$ROUND_HOURS" \
      CODEX_MODEL="$CODEX_MODEL" CODEX_REASONING_EFFORT="$CODEX_REASONING_EFFORT" RESUME_FROM_RUN_ID="$RESUME_FROM_RUN_ID" \
      "$AUTOSCRIPT_DIR/run_auto_codex.sh" --foreground > "$RUN_DIR/nohup.out" 2>&1 < /dev/null &
    echo "$!" > "$RUN_DIR/launcher.pid"; echo "$RUN_ID" > "$CHANGE_ROOT/output/latest_run_id"
    echo "detached: run $RUN_ID pid $(cat "$RUN_DIR/launcher.pid")" ;;
  *) echo "usage: $0 --detach | --foreground"; exit 1 ;;
esac
