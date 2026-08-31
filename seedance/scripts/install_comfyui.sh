#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /absolute/path/to/new-comfyui-directory" >&2
  exit 2
fi

target_dir="$1"
if [[ "$target_dir" != /* ]] || [[ -e "$target_dir" ]]; then
  echo "Target must be an absolute path that does not already exist." >&2
  exit 2
fi

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
git clone --branch v0.31.0 --depth 1 https://github.com/comfyanonymous/ComfyUI.git "$target_dir"
python3 -m venv "$target_dir/.venv"
"$target_dir/.venv/bin/pip" install -r "$target_dir/requirements.txt"
"$target_dir/.venv/bin/pip" install -e "$repo_dir"
ln -s "$repo_dir/comfyui_custom_nodes/seedance_icon_animation" \
  "$target_dir/custom_nodes/seedance_icon_animation"

echo "Installed an isolated ComfyUI v0.31.0 checkout at $target_dir"
echo "No server was started or restarted. Add an MCP adapter only after reviewing its permissions."
