#!/usr/bin/env bash
# AFK Ralph loop for milestone #86: runs one fixed-prompt Claude iteration
# at a time until godot/qa/RALPH_DONE exists or RALPH_MAX iterations pass.
# Launch:  nohup bash godot/qa/ralph.sh >> godot/qa/out/ralph.log 2>&1 &
set -uo pipefail
cd "$(dirname "$0")/../.."
MAX="${RALPH_MAX:-10}"
for i in $(seq 1 "$MAX"); do
  if [ -f godot/qa/RALPH_DONE ]; then
    echo "[ralph] done marker present — stopping after $((i - 1)) iterations"
    break
  fi
  echo "[ralph] === iteration $i/$MAX $(date -Is) ==="
  claude -p "$(cat godot/qa/RALPH_PROMPT.md)" \
    --permission-mode acceptEdits \
    --max-turns 120 || echo "[ralph] iteration $i exited non-zero; continuing"
  echo "[ralph] === iteration $i finished $(date -Is) ==="
done
echo "[ralph] loop ended $(date -Is)"
