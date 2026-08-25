#!/usr/bin/env bash
set -euo pipefail

readonly PIPELINE_ROOT="${QWEN_PIPELINE_ROOT:-$HOME/.local/share/qwen-image-pipeline}"
readonly SECRET_RUNNER="${CODEX_HOME:-$HOME/.codex}/skills/access-bitwarden-secrets/scripts/stored_bws.sh"
readonly OPENROUTER_SECRET_NAME="${QWEN_OPENROUTER_SECRET_NAME:-OpenRouter}"
readonly ALIBABA_SECRET_NAME="${QWEN_ALIBABA_SECRET_NAME:-Alibaba Singapour}"
readonly POOL_RUNNER="${QWEN_COMFYUI_POOL_RUNNER:-$PIPELINE_ROOT/run-comfyui-pool.sh}"

exec "$SECRET_RUNNER" run "$OPENROUTER_SECRET_NAME" OPENROUTER_API_KEY -- \
  "$SECRET_RUNNER" run "$ALIBABA_SECRET_NAME" DASHSCOPE_API_KEY -- \
    "$POOL_RUNNER"
