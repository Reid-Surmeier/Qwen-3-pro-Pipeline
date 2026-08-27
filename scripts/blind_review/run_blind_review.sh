#!/usr/bin/env bash
# Spawn the blind reviewer: Hermes on the host, sandbox in Docker.
#
# The Hermes process runs from the owner's install with the configured
# OpenRouter key, pinned to a vision model, with user config and rules
# stripped so nothing Hermes remembers about this project reaches the
# reviewer. Its terminal backend is Docker: every command, file read, and
# screenshot happens inside a --network none container whose /workspace is
# the packet-derived blind workspace, read-only. The verdict is validated
# fail-closed on the host; posting labels or comments stays with the host
# operator, never the agent.
#
# Paid use: one spawn makes model calls through OpenRouter under ADR 0003
# and the active milestone allowance. Do not wire this into ordinary CI.
#
# Usage:
#   scripts/blind_review/run_blind_review.sh \
#     --packet artifacts/reviews/issue-86/packet.json \
#     [--repo .] [--include godot] [--model google/gemini-3.7-flash] \
#     [--image qwen-pipeline/blind-review-sandbox] [--skip-build] \
#     [--max-turns 120] [--run-budget 2700] [--workdir DIR] [--dry-run]

set -euo pipefail

PACKET=""
REPO="."
INCLUDES=()
MODEL="google/gemini-3.7-flash"
IMAGE="qwen-pipeline/blind-review-sandbox"
SKIP_BUILD="false"
MAX_TURNS="120"
RUN_BUDGET="2700"
WORKDIR=""
DRY_RUN="false"

while [ $# -gt 0 ]; do
  case "$1" in
    --packet) PACKET="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --include) INCLUDES+=("$2"); shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --image) IMAGE="$2"; shift 2 ;;
    --skip-build) SKIP_BUILD="true"; shift ;;
    --max-turns) MAX_TURNS="$2"; shift 2 ;;
    --run-budget) RUN_BUDGET="$2"; shift 2 ;;
    --workdir) WORKDIR="$2"; shift 2 ;;
    --dry-run) DRY_RUN="true"; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

[ -n "$PACKET" ] || { echo "--packet is required" >&2; exit 2; }
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$REPO" && pwd)"

echo "==> Validating packet"
EXPECT_SHA="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['candidate_commit'])" "$PACKET")"
python3 "$SCRIPT_DIR/../validate_blind_review_packet.py" \
  --packet "$PACKET" --repo "$REPO" --expect-sha "$EXPECT_SHA"

if [ -z "$WORKDIR" ]; then
  WORKDIR="$(mktemp -d -t blind-review-XXXXXX)"
fi
WORKSPACE="$WORKDIR/workspace"
OUT="$WORKDIR/out"
mkdir -p "$OUT"

echo "==> Building blind workspace at $WORKSPACE"
INCLUDE_ARGS=()
for path in ${INCLUDES[@]+"${INCLUDES[@]}"}; do
  INCLUDE_ARGS+=(--include "$path")
done
python3 "$SCRIPT_DIR/build_workspace.py" \
  --packet "$PACKET" --repo "$REPO" --out "$WORKSPACE" \
  ${INCLUDE_ARGS[@]+"${INCLUDE_ARGS[@]}"}

echo "==> Rendering reviewer prompt"
python3 "$SCRIPT_DIR/render_prompt.py" --workspace "$WORKSPACE" > "$WORKDIR/prompt.md"

if [ "$SKIP_BUILD" != "true" ]; then
  echo "==> Building sandbox image $IMAGE"
  docker build -f "$SCRIPT_DIR/sandbox.Dockerfile" -t "$IMAGE" "$SCRIPT_DIR"
fi

HERMES_CMD=(
  hermes chat
  --query-file "$WORKDIR/prompt.md"
  -m "$MODEL" --provider openrouter
  -t terminal,file,vision,todo
  --ignore-user-config --ignore-rules
  --cli -Q --yolo
  --max-turns "$MAX_TURNS" --run-budget "$RUN_BUDGET"
)

SANDBOX_ENV=(
  "TERMINAL_ENV=docker"
  "TERMINAL_DOCKER_IMAGE=$IMAGE"
  "TERMINAL_DOCKER_VOLUMES=[\"$WORKSPACE:/workspace:ro\",\"$OUT:/out:rw\"]"
  "TERMINAL_DOCKER_EXTRA_ARGS=[\"--network\",\"none\"]"
  "TERMINAL_CWD=/workspace"
  "TERMINAL_TIMEOUT=300"
  "TERMINAL_LIFETIME_SECONDS=3600"
)

if [ "$DRY_RUN" = "true" ]; then
  echo "==> Dry run; would spawn:"
  printf '  %s \\\n' "${SANDBOX_ENV[@]}"
  printf '  %q ' "${HERMES_CMD[@]}"
  echo
  echo "workdir: $WORKDIR"
  exit 0
fi

echo "==> Spawning blind reviewer ($MODEL)"
env "${SANDBOX_ENV[@]}" "${HERMES_CMD[@]}"

echo "==> Validating verdict (fail-closed)"
if python3 "$SCRIPT_DIR/validate_verdict.py" \
  --verdict "$OUT/review.json" \
  --packet "$WORKSPACE/packet.json" \
  --out-dir "$OUT"; then
  CONTRACT="$(python3 -c "import json,sys;print(json.load(open(sys.argv[1]))['acceptance_contract'])" "$WORKSPACE/packet.json")"
  python3 "$SCRIPT_DIR/render_comment.py" \
    --verdict "$OUT/review.json" --contract "$CONTRACT" > "$WORKDIR/comment.md"
  echo "==> Review complete"
  echo "verdict:  $OUT/review.json"
  echo "comment:  $WORKDIR/comment.md"
  echo "evidence: $OUT/"
  echo "Post the comment and apply the verdict label from the host (never the agent)."
else
  echo "==> Verdict failed validation: treat this round as blind-review-blocked." >&2
  echo "workdir: $WORKDIR" >&2
  exit 1
fi
