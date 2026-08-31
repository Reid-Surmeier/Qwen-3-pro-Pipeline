#!/usr/bin/env bash
# Headless image-79 regression registry. Append each Window contract suite here;
# shared Control Library changes always rerun the complete registered set.
set -uo pipefail
GODOT="${GODOT_BIN:-$HOME/.cache/qwen-ui-pipeline/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64}"
cd "$(dirname "$0")/.."
mkdir -p qa/out

suites=(
  "run_control_spec_contracts.gd:control-spec-contracts.json"
  "run_control_runtime_contracts.gd:control-runtime-contracts.json"
  "run_scroll_text_contracts.gd:scroll-text-contracts.json"
  "run_desktop_router_contracts.gd:desktop-router-contracts.json"
  "run_inventory_spec_contracts.gd:inventory-spec-contracts.json"
  "run_inventory_contracts.gd:inventory-contracts.json"
  "run_inventory_window_contracts.gd:inventory-window-contracts.json"
  "run_storage_spec_contracts.gd:storage-spec-contracts.json"
  "run_storage_contracts.gd:storage-contracts.json"
  "run_storage_window_contracts.gd:storage-window-contracts.json"
  "run_equipment_card_contracts.gd:equipment-card-contracts.json"
  "run_equipment_card_window_contracts.gd:equipment-card-window-contracts.json"
  "run_equipment_items_contracts.gd:equipment-items-contracts.json"
  "run_equipment_items_window_contracts.gd:equipment-items-window-contracts.json"
  "run_status_window_state_contracts.gd:status-window-state-contracts.json"
  "run_status_contracts.gd:status-contracts.json"
  "run_status_window_contracts.gd:status-window-contracts.json"
  "run_meter_contracts.gd:meter-contracts.json"
  "run_basic_info_contracts.gd:basic-info-contracts.json"
  "run_basic_info_window_contracts.gd:basic-info-window-contracts.json"
  "run_party_window_state_contracts.gd:party-window-state-contracts.json"
  "run_party_contracts.gd:party-contracts.json"
  "run_party_window_contracts.gd:party-window-contracts.json"
  "run_system_menu_contracts.gd:system-menu-contracts.json"
  "run_system_menu_window_contracts.gd:system-menu-window-contracts.json"
  "run_system_menu_desktop_contracts.gd:system-menu-desktop-contracts.json"
  "run_chat_room_state_contracts.gd:chat-room-state-contracts.json"
  "run_chat_room_window_contracts.gd:chat-room-window-contracts.json"
  "run_image79_assembly_contracts.gd:image79-assembly-contracts.json"
  "run_options_window_contracts.gd:options-window-contracts.json"
  "run_skill_tree_contracts.gd:skill-tree-contracts.json"
  "run_skill_tree_window_contracts.gd:skill-tree-window-contracts.json"
)
exit_code=0
reports=()
for suite in "${suites[@]}"; do
  script="${suite%%:*}"
  report="${suite#*:}"
  echo "==> image-79 $script"
  "$GODOT" --headless --path . --script "res://tests/$script" \
    > "qa/out/${script%.gd}.log" 2>&1
  rc=$?
  if [ "$rc" -ne 0 ]; then exit_code=1; fi
  reports+=("$report")
done

python3.12 - "$exit_code" "${reports[@]}" <<'PY'
import json
import pathlib
import sys

out = pathlib.Path("qa/out")
exit_code = int(sys.argv[1])
suites = []
for name in sys.argv[2:]:
    path = out / name
    if path.exists():
        suites.append(json.loads(path.read_text()))
    else:
        suites.append({"suite": name, "failed": 1, "error": "report missing"})
report = {
    "suites": suites,
    "total": sum(suite.get("total", 0) for suite in suites),
    "failed": sum(suite.get("failed", 1) for suite in suites),
}
report["pass"] = exit_code == 0 and report["failed"] == 0
(out / "image79-contracts.json").write_text(json.dumps(report, indent=2))
print(json.dumps({"pass": report["pass"], "total": report["total"],
                  "failed": report["failed"]}))
PY
exit "$exit_code"
