#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
QWEN_DATA_ROOT="${QWEN_PIPELINE_ROOT:-${XDG_DATA_HOME:-${HOME}/.local/share}/qwen-image-pipeline}"
COMFYUI_ROOT="${QWEN_COMFYUI_ROOT:-${QWEN_DATA_ROOT}/ComfyUI}"
TARGET_DIR="${COMFYUI_ROOT}/custom_nodes/qwen_sticker_tooling"

install -d -m 0755 "${TARGET_DIR}"
install -m 0644 \
  "${REPOSITORY_ROOT}/comfyui_custom_nodes/qwen_sticker_tooling/__init__.py" \
  "${TARGET_DIR}/__init__.py"
install -m 0644 \
  "${REPOSITORY_ROOT}/comfyui_custom_nodes/qwen_sticker_tooling/nodes.py" \
  "${TARGET_DIR}/nodes.py"

sha256sum "${TARGET_DIR}/__init__.py" "${TARGET_DIR}/nodes.py"
echo "Installed qwen_sticker_tooling at ${TARGET_DIR}"
echo "ComfyUI was not restarted. Confirm the aggregate queue is empty before restart."
