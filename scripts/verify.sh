#!/usr/bin/env bash
# Canonical deterministic repository baseline (Issue #19).
#
# Humans, agents, and GitHub Actions all run this same entry point. It must
# stay free of provider credentials, model APIs, ComfyUI generation, and any
# paid or external effect.

set -uo pipefail

PYTHON_BIN="${VERIFY_PYTHON:-python3.12}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN=python3
fi

cd "$(dirname "$0")/.."

failures=0

run_check() {
  local name="$1"
  shift
  echo "==> ${name}"
  if "$@"; then
    echo "==> ${name}: ok"
  else
    echo "==> ${name}: FAILED" >&2
    failures=$((failures + 1))
  fi
}

run_check "python unit tests" "$PYTHON_BIN" -m unittest discover -s tests
run_check "seedance tests" env \
  "PYTHONPATH=${PWD}/seedance/src${PYTHONPATH:+:${PYTHONPATH}}" \
  "$PYTHON_BIN" -m pytest seedance/tests
run_check "node tests" node --test tests/figma-mcp-client.test.mjs tests/figma-oauth-bootstrap.test.mjs

GODOT_CACHE_BIN="${HOME}/.cache/qwen-ui-pipeline/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64"
GODOT_EXECUTABLE="${GODOT_BIN:-}"
if [ -z "$GODOT_EXECUTABLE" ]; then
  GODOT_EXECUTABLE="$(command -v godot4 || command -v godot || true)"
fi
if [ -z "$GODOT_EXECUTABLE" ] && [ -x "$GODOT_CACHE_BIN" ]; then
  GODOT_EXECUTABLE="$GODOT_CACHE_BIN"
fi
if [ -n "$GODOT_EXECUTABLE" ] && [ -x "$GODOT_EXECUTABLE" ]; then
  run_check "godot headless QA" env GODOT_BIN="$GODOT_EXECUTABLE" \
    bash godot/qa/qa.sh --headless
else
  echo "==> godot headless QA: SKIP (Godot binary not found; set GODOT_BIN or populate ${GODOT_CACHE_BIN})"
fi

if command -v pre-commit >/dev/null 2>&1; then
  run_check "pre-commit" pre-commit run --all-files
else
  echo "==> pre-commit: SKIPPED (not installed; pip install pre-commit)"
fi
run_check "python compilation" "$PYTHON_BIN" -m compileall -q \
  qwen_ui_pipeline tests scripts seedance/src seedance/tests godot/qa
run_check "git diff --check" git diff --check

if [ "$failures" -ne 0 ]; then
  echo "verification failed: ${failures} check(s) reported errors" >&2
  exit 1
fi
echo "verification passed"
