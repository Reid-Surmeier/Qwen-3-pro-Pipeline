#!/usr/bin/env bash
set -euo pipefail

readonly PIPELINE_ROOT="${QWEN_PIPELINE_ROOT:-$HOME/.local/share/qwen-image-pipeline}"
readonly COMFYUI_ROOT="$PIPELINE_ROOT/ComfyUI"
readonly SECRET_RUNNER="${CODEX_HOME:-$HOME/.codex}/skills/access-bitwarden-secrets/scripts/stored_bws.sh"
readonly OPENROUTER_SECRET_NAME="${QWEN_OPENROUTER_SECRET_NAME:-OpenRouter}"
readonly ALIBABA_SECRET_NAME="${QWEN_ALIBABA_SECRET_NAME:-Alibaba Singapour}"
readonly COMFYUI_LISTEN_ADDRESS="${QWEN_COMFYUI_LISTEN_ADDRESS:-10.255.255.254}"
readonly COMFYUI_PORT="${QWEN_COMFYUI_PORT:-8188}"
readonly SOURCE_GUARD="${QWEN_NODE_SOURCE_GUARD:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/verify-node-source.sh}"

# Refuse to start on a drifted host. Serving nodes from a stale checkout is
# silent: the service looks healthy while every merged change is invisible.
if [[ -x "$SOURCE_GUARD" ]]; then
  "$SOURCE_GUARD"
fi

exec "$SECRET_RUNNER" run "$OPENROUTER_SECRET_NAME" OPENROUTER_API_KEY -- \
  "$SECRET_RUNNER" run "$ALIBABA_SECRET_NAME" DASHSCOPE_API_KEY -- \
    "$COMFYUI_ROOT/.venv/bin/python" "$COMFYUI_ROOT/main.py" \
    --listen "$COMFYUI_LISTEN_ADDRESS" \
    --port "$COMFYUI_PORT" \
    --disable-auto-launch
