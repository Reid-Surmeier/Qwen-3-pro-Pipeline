#!/usr/bin/env bash
set -euo pipefail

readonly PIPELINE_ROOT="${QWEN_PIPELINE_ROOT:-$HOME/.local/share/qwen-image-pipeline}"
readonly COMFYUI_ROOT="$PIPELINE_ROOT/ComfyUI"
readonly PYTHON="$COMFYUI_ROOT/.venv/bin/python"
readonly PUBLIC_LISTEN_ADDRESS="${QWEN_COMFYUI_LISTEN_ADDRESS:-10.255.255.254}"
readonly PUBLIC_PORT="${QWEN_COMFYUI_PORT:-8188}"
readonly WORKER_LISTEN_ADDRESS="${QWEN_COMFYUI_WORKER_LISTEN_ADDRESS:-$PUBLIC_LISTEN_ADDRESS}"
readonly WORKER_BASE_PORT="${QWEN_COMFYUI_WORKER_BASE_PORT:-8191}"
readonly WORKER_COUNT="${QWEN_COMFYUI_WORKERS:-5}"
readonly WORKER_STATE_ROOT="${QWEN_COMFYUI_WORKER_STATE_ROOT:-$PIPELINE_ROOT/workers}"

if [[ ! "$WORKER_COUNT" =~ ^[1-9][0-9]*$ ]]; then
  echo "QWEN_COMFYUI_WORKERS must be a positive integer" >&2
  exit 2
fi
if [[ ! "$WORKER_BASE_PORT" =~ ^[0-9]+$ ]] || (( WORKER_BASE_PORT < 1 )); then
  echo "QWEN_COMFYUI_WORKER_BASE_PORT must be a positive integer" >&2
  exit 2
fi

declare -a child_pids=()

cleanup() {
  trap - EXIT INT TERM
  if (( ${#child_pids[@]} )); then
    kill "${child_pids[@]}" 2>/dev/null || true
    wait "${child_pids[@]}" 2>/dev/null || true
  fi
}

trap cleanup EXIT
trap 'exit 0' INT TERM

declare -a router_args=(
  --listen "$PUBLIC_LISTEN_ADDRESS"
  --port "$PUBLIC_PORT"
)

for (( worker_index = 0; worker_index < WORKER_COUNT; worker_index++ )); do
  worker_port=$(( WORKER_BASE_PORT + worker_index ))
  worker_state_directory="$WORKER_STATE_ROOT/worker-$(( worker_index + 1 ))"
  mkdir -p "$worker_state_directory"
  "$PYTHON" "$COMFYUI_ROOT/main.py" \
    --listen "$WORKER_LISTEN_ADDRESS" \
    --port "$worker_port" \
    --database-url "sqlite:///$worker_state_directory/comfyui.db" \
    --disable-auto-launch &
  child_pids+=("$!")
  router_args+=(--backend "http://$WORKER_LISTEN_ADDRESS:$worker_port")
done

"$PYTHON" -m qwen_ui_pipeline.comfyui_router "${router_args[@]}" &
child_pids+=("$!")

# Any unexpected child exit restarts the complete, consistent pool through
# systemd.  The EXIT trap terminates the remaining children first.
set +e
wait -n "${child_pids[@]}"
status=$?
set -e
if (( status == 0 )); then
  status=1
fi
exit "$status"
