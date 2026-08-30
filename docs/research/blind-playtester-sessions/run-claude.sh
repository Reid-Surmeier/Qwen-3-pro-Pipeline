#!/usr/bin/env bash
# Blind Playtester — Claude Code. Runs inside the packet dir; nothing from the host loads.
set -u
O=/tmp/playtest/out
PACKET=/tmp/playtest/claude
cd "$PACKET" || exit 1
export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1
timeout 900 claude -p \
  --model opus \
  --setting-sources "" \
  --strict-mcp-config --mcp-config "$O/pw-mcp-claude.json" \
  --tools "Read,Write" \
  --allowedTools "Read,Write,mcp__browser" \
  --disallowedTools "mcp__browser__browser_evaluate,mcp__browser__browser_run_code_unsafe,mcp__browser__browser_snapshot,mcp__browser__browser_find,mcp__browser__browser_console_messages,mcp__browser__browser_network_requests,mcp__browser__browser_network_request" \
  --max-turns 45 \
  --no-session-persistence \
  --output-format json \
  "$(cat "$PACKET/PLAYTEST.md")" \
  > "$O/run-claude.json" 2> "$O/run-claude.err"
echo "exit=$?"
