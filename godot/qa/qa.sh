#!/usr/bin/env bash
# Self-verifying QA loop for the RO-HUD replica (milestone #86).
# Produces qa/out/report.json that an agent consumes and course-corrects from.
set -uo pipefail
GODOT="${GODOT_BIN:-$HOME/.cache/qwen-ui-pipeline/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64}"
cd "$(dirname "$0")/.."
mkdir -p qa/out
: > qa/out/import.log

echo "==> import"
"$GODOT" --headless --path . --import >> qa/out/import.log 2>&1
import_rc=$?
grep -iE 'error|script error|parse error|failed' qa/out/import.log > qa/out/import-errors.log || true

echo "==> engine contracts"
"$GODOT" --headless --path . --script res://tests/run_contracts.gd > qa/out/contracts.log 2>&1
contracts_rc=$?

echo "==> image-79 registered contracts"
GODOT_BIN="$GODOT" bash qa/image79.sh > qa/out/image79.log 2>&1
image79_rc=$?

capture_rc=-1
fidelity_rc=-1
interact_rc=-1
if [ "${QA_CAPTURE:-1}" = "1" ]; then
  echo "==> frame capture (DISPLAY=${DISPLAY:-:99})"
  timeout 120 "$GODOT" --path . -- --capture=qa/out/capture.png > qa/out/capture.log 2>&1
  capture_rc=$?
  if [ -f qa/out/capture.png ]; then
    echo "==> fidelity"
    python3.12 qa/fidelity.py > qa/out/fidelity.log 2>&1
    fidelity_rc=$?
  fi
  echo "==> real-input interaction"
  timeout 120 "$GODOT" --path . -- --interact=qa/out/interact.json > qa/out/interact.log 2>&1
  interact_rc=$?
fi

python3.12 - "$import_rc" "$contracts_rc" "$image79_rc" "$capture_rc" "$fidelity_rc" "$interact_rc" <<'PY'
import json, sys, pathlib
import_rc, contracts_rc, image79_rc, capture_rc, fidelity_rc, interact_rc = map(int, sys.argv[1:7])
out = pathlib.Path("qa/out")
report = {
    "import": {"exit": import_rc,
               "errors": out.joinpath("import-errors.log").read_text().splitlines()
               if out.joinpath("import-errors.log").exists() else []},
    "contracts": json.loads(out.joinpath("contracts.json").read_text())
                 if out.joinpath("contracts.json").exists() else {"error": "no contracts.json", "exit": contracts_rc},
    "image79": json.loads(out.joinpath("image79-contracts.json").read_text())
                 if out.joinpath("image79-contracts.json").exists()
                 else {"error": "no image79-contracts.json", "exit": image79_rc},
    "capture": {"exit": capture_rc, "file": "qa/out/capture.png" if out.joinpath("capture.png").exists() else None},
    "fidelity": json.loads(out.joinpath("fidelity.json").read_text())
                if out.joinpath("fidelity.json").exists() else {"exit": fidelity_rc},
    "interact": json.loads(out.joinpath("interact.json").read_text())
                if out.joinpath("interact.json").exists() else {"exit": interact_rc},
}
hard_fail = bool(report["import"]["errors"]) \
    or report["contracts"].get("failed", 1) != 0 \
    or report["image79"].get("failed", 1) != 0 \
    or report["interact"].get("failed", 1) != 0
report["pass"] = not hard_fail
out.joinpath("report.json").write_text(json.dumps(report, indent=2))
print(json.dumps({"pass": report["pass"],
                  "import_errors": len(report["import"]["errors"]),
                  "contracts_failed": report["contracts"].get("failed"),
                  "image79_failed": report["image79"].get("failed"),
                  "capture": report["capture"]["file"],
                  "fidelity_pass": report["fidelity"].get("pass"),
                  "interact_failed": report["interact"].get("failed")}))
PY
