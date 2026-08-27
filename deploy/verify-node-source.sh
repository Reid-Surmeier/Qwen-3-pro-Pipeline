#!/usr/bin/env bash
# Assert that the running ComfyUI serves node code from the intended checkout.
#
# On 2026-08-26 the live pool was found serving a stale worktree whose pull
# request had been closed unmerged, so every change merged to main was
# invisible to the server. Two host-side links can drift independently: the
# editable install of qwen_ui_pipeline inside the ComfyUI virtual environment,
# and the custom_nodes symlink. This checks both.
#
# It reports and stops. It never repairs, because silently reinstalling could
# discard work an operator deliberately placed on the host.

set -euo pipefail

readonly PIPELINE_ROOT="${QWEN_PIPELINE_ROOT:-$HOME/.local/share/qwen-image-pipeline}"
readonly COMFYUI_ROOT="${QWEN_COMFYUI_ROOT:-$PIPELINE_ROOT/ComfyUI}"
readonly PYTHON="${QWEN_COMFYUI_PYTHON:-$COMFYUI_ROOT/.venv/bin/python}"
readonly CUSTOM_NODE_LINK="${QWEN_CUSTOM_NODE_LINK:-$COMFYUI_ROOT/custom_nodes/qwen_image_3_openrouter}"

script_directory=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly EXPECTED_REPO="${QWEN_PIPELINE_REPO:-$(cd -- "$script_directory/.." && pwd)}"

fail() {
  printf 'deploy drift: %s\n' "$*" >&2
  exit 1
}

[[ -x "$PYTHON" ]] || fail "ComfyUI interpreter is not executable: $PYTHON"
[[ -d "$EXPECTED_REPO/qwen_ui_pipeline" ]] ||
  fail "expected repository has no qwen_ui_pipeline package: $EXPECTED_REPO"

# Resolve the package from a neutral directory: running inside the repository
# would let the current working directory shadow the installed mapping and
# report a pass on a drifted host.
installed_package=$(cd / && "$PYTHON" - <<'PYTHON'
import importlib.util
import sys

spec = importlib.util.find_spec("qwen_ui_pipeline")
if spec is None or not spec.origin:
    sys.exit("qwen_ui_pipeline is not importable by the ComfyUI interpreter")
print(spec.origin)
PYTHON
) || fail "could not resolve qwen_ui_pipeline in $PYTHON"

installed_root=$(cd -- "$(dirname -- "$(dirname -- "$installed_package")")" && pwd)
expected_root=$(cd -- "$EXPECTED_REPO" && pwd)

if [[ "$installed_root" != "$expected_root" ]]; then
  fail "$(printf 'qwen_ui_pipeline resolves to the wrong checkout\n  expected: %s\n  actual:   %s\n  repair:   uv pip install --python %s -e %s --no-deps' \
    "$expected_root" "$installed_root" "$PYTHON" "$expected_root")"
fi

[[ -e "$CUSTOM_NODE_LINK" ]] || fail "custom node is missing: $CUSTOM_NODE_LINK"

linked_target=$(cd -- "$(readlink -f -- "$CUSTOM_NODE_LINK")" && pwd)
expected_target=$(cd -- "$expected_root/comfyui_custom_nodes/qwen_image_3_openrouter" && pwd)

if [[ "$linked_target" != "$expected_target" ]]; then
  fail "$(printf 'custom node points at the wrong checkout\n  expected: %s\n  actual:   %s\n  repair:   ln -sfn %s %s' \
    "$expected_target" "$linked_target" "$expected_target" "$CUSTOM_NODE_LINK")"
fi

printf 'node source verified: %s\n' "$expected_root"
