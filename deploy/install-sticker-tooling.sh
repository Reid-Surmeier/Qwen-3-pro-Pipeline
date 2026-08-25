#!/usr/bin/env bash
set -euo pipefail

readonly SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
readonly PIPELINE_ROOT="${QWEN_PIPELINE_ROOT:-$HOME/.local/share/qwen-image-pipeline}"
readonly TARGET="$PIPELINE_ROOT/ComfyUI/custom_nodes/qwen_sticker_tooling"

install -d -m 0755 "$TARGET"
install -m 0644 \
  "$SOURCE_ROOT/comfyui_custom_nodes/qwen_sticker_tooling/__init__.py" \
  "$TARGET/__init__.py"
install -m 0644 \
  "$SOURCE_ROOT/comfyui_custom_nodes/qwen_sticker_tooling/nodes.py" \
  "$TARGET/nodes.py"

printf 'Installed additive sticker tooling at %s\n' "$TARGET"
printf 'Restart ComfyUI only after verifying the aggregate queue is empty.\n'
