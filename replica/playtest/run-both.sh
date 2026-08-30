#!/usr/bin/env bash
# Blind Playtesters for the Options-window prototype. Packets at neutral paths; nothing from the host loads.
set -u
P=/tmp/claude-1000/-home-reidsurmeier-Qwen-3-pro-Pipeline/ad61c962-aeb7-4583-bb02-12f0c19476ff/scratchpad/play
O=/tmp/playtest/out
rm -rf /tmp/playtest/opt-claude /tmp/playtest/opt-codex; mkdir -p /tmp/playtest/opt-claude /tmp/playtest/opt-codex
cp $P/PLAYTEST-options.md /tmp/playtest/opt-claude/PLAYTEST.md; cp $P/PLAYTEST-options.md /tmp/playtest/opt-codex/PLAYTEST.md
sed 's#/tmp/playtest/claude#/tmp/playtest/opt-claude#' $P/pw-mcp-claude-v2.json > $O/pw-mcp-opt-claude.json
sed 's#/tmp/playtest/codex#/tmp/playtest/opt-codex#g' $P/codex-config-v2.toml > $O/codex-config-opt.toml
( cd /tmp/playtest/opt-claude && export CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 && timeout 1500 claude -p \
  --model "${CLAUDE_MODEL:-opus}" --setting-sources "" \
  --strict-mcp-config --mcp-config "$O/pw-mcp-opt-claude.json" \
  --tools "Read,Write" --allowedTools "Read,Write,mcp__browser" \
  --disallowedTools "mcp__browser__browser_evaluate,mcp__browser__browser_run_code_unsafe,mcp__browser__browser_snapshot,mcp__browser__browser_find,mcp__browser__browser_console_messages,mcp__browser__browser_network_requests,mcp__browser__browser_network_request" \
  --max-turns 120 --no-session-persistence --output-format json \
  "$(cat PLAYTEST.md)" > $O/run-opt-claude.json 2> $O/run-opt-claude.err; echo "claude exit=$?" ) &
( export CODEX_HOME="$O/codex-home" HOME="$O/fakehome"; cp $O/codex-config-opt.toml $CODEX_HOME/config.toml
  cd /tmp/playtest/opt-codex && timeout 1500 codex exec -C /tmp/playtest/opt-codex --skip-git-repo-check --ephemeral --ignore-rules \
  -s workspace-write --json -o $O/run-opt-codex.last.md "$(cat PLAYTEST.md)" > $O/run-opt-codex.jsonl 2> $O/run-opt-codex.err; echo "codex exit=$?" ) &
wait
echo "--- logs ---"; ls -la /tmp/playtest/opt-claude/play-log.json /tmp/playtest/opt-codex/play-log.json 2>&1
