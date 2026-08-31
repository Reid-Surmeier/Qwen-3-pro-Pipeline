#!/usr/bin/env bash
# Reproducible Image-79 Web export from a clean worktree.
set -euo pipefail

GODOT="${GODOT_BIN:-$HOME/.cache/qwen-ui-pipeline/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64}"
cd "$(dirname "$0")/.."
mkdir -p web
"$GODOT" --headless --path . --import
"$GODOT" --headless --path . --export-release Web web/index.html
test -s web/index.html
test -s web/index.pck
test -s web/index.wasm
printf '{"pass":true,"output":"godot/web/index.html"}\n'
