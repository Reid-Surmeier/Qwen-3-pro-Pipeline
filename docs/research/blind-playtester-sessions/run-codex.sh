#!/usr/bin/env bash
# Blind Playtester — Codex (GPT-5.6 Sol, xhigh) on the owner's Codex subscription.
# No shell tool: the packet text is the prompt, the browser MCP is the only way to act,
# and apply_patch is the only way to write. Nothing from the host loads.
set -u
O=/tmp/playtest/out
PACKET=/tmp/playtest/codex
export CODEX_HOME="$O/codex-home"      # isolated: only auth.json + this config.toml
export HOME="$O/fakehome"              # isolated: hides ~/.agents/skills
cp "$O/codex-config.toml" "$CODEX_HOME/config.toml"
timeout 900 codex exec \
  -C "$PACKET" --skip-git-repo-check --ephemeral \
  --ignore-rules \
  -s workspace-write \
  --json -o "$O/run-codex.last.md" \
  "$(cat "$PACKET/PLAYTEST.md")" \
  > "$O/run-codex.jsonl" 2> "$O/run-codex.err"
echo "exit=$?"
