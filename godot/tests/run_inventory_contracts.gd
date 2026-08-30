extends SceneTree
## Issue #127 semantic contracts for shared Tabs and the multi-gesture
## SelectionView. Real input recognition is frozen separately at the Window seam.

const ControlRuntime = preload("res://control_library/control_runtime.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	_contract_tabs_route_declared_action()
	_contract_selection_and_double_open()
	_contract_modifier_selection_reverses()
	_contract_invalid_modifier_preserves_state()
	_contract_drag_drop_swaps_once()
	_contract_invalid_drop_preserves_state()
	_contract_conflict_preserves_state()
	_contract_qa_state_is_factual()
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _runtime():
	var runtime = ControlRuntime.new()
	runtime.configure(_fixture())
	return runtime


func _contract_tabs_route_declared_action() -> void:
	var runtime = _runtime()
	var result: Dictionary = runtime.dispatch("inventory.tabs", "Activate", {"choice": "equip"})
	var state: Dictionary = runtime.qa_state().controls["inventory.tabs"]
	_check("tabs-route-declared-action", result.get("ok", false)
		and result.get("action") == "SelectInventoryTab" and state.get("value") == "equip",
		str([result, state]))


func _contract_selection_and_double_open() -> void:
	var runtime = _runtime()
	var selected: Dictionary = runtime.dispatch("inventory.items", "Activate", {"item": "r0c1"})
	var opened: Dictionary = runtime.dispatch("inventory.items", "DoubleActivate", {"item": "r0c2"})
	var state: Dictionary = runtime.qa_state().controls["inventory.items"]
	_check("selection-and-double-open", selected.get("action") == "SelectInventoryItem"
		and opened.get("action") == "OpenInventoryItem"
		and state.get("value") == "r0c2" and state.get("opened_item") == "r0c2",
		str([selected, opened, state]))


func _contract_modifier_selection_reverses() -> void:
	var runtime = _runtime()
	var first: Dictionary = runtime.dispatch("inventory.items", "ModifierActivate",
		{"item": "r0c1", "modifiers": ["ctrl"]})
	var during: Array = runtime.qa_state().controls["inventory.items"].get("selected_items", [])
	var second: Dictionary = runtime.dispatch("inventory.items", "ModifierActivate",
		{"item": "r0c1", "modifiers": ["ctrl"]})
	var after: Array = runtime.qa_state().controls["inventory.items"].get("selected_items", [])
	_check("modifier-selection-reverses", first.get("ok", false) and second.get("ok", false)
		and "r0c1" in during and "r0c1" not in after,
		str([first, during, second, after]))


func _contract_invalid_modifier_preserves_state() -> void:
	var runtime = _runtime()
	var before: Dictionary = runtime.qa_state().controls["inventory.items"]
	var result: Dictionary = runtime.dispatch("inventory.items", "ModifierActivate",
		{"item": "r0c1", "modifiers": ["alt"]})
	var after: Dictionary = runtime.qa_state().controls["inventory.items"]
	_check("invalid-modifier-preserves-state", not result.get("ok", false)
		and result.get("error", {}).get("code") == "InvalidModifierError"
		and before.get("value") == after.get("value")
		and before.get("selected_items", []) == after.get("selected_items", [])
		and before.get("item_values", {}) == after.get("item_values", {}), str(result))


func _contract_drag_drop_swaps_once() -> void:
	var runtime = _runtime()
	var result: Dictionary = runtime.dispatch("inventory.items", "DragDrop",
		{"source": "r0c0", "target": "r0c1", "version": 0})
	var state: Dictionary = runtime.qa_state().controls["inventory.items"]
	_check("drag-drop-swaps-once", result.get("ok", false)
		and result.get("action") == "MoveInventoryItem"
		and state.get("item_values", {}).get("r0c0") == "item-02"
		and state.get("item_values", {}).get("r0c1") == "item-01"
		and state.get("item_version") == 1, str([result, state]))


func _contract_invalid_drop_preserves_state() -> void:
	var runtime = _runtime()
	var before: Dictionary = runtime.qa_state().controls["inventory.items"]
	var result: Dictionary = runtime.dispatch("inventory.items", "DragDrop",
		{"source": "r0c0", "target": "missing", "version": 0})
	var after: Dictionary = runtime.qa_state().controls["inventory.items"]
	_check("invalid-drop-preserves-state", not result.get("ok", false)
		and result.get("error", {}).get("code") == "InvalidDropTargetError"
		and before.get("item_values", {}) == after.get("item_values", {})
		and before.get("item_version") == after.get("item_version"), str(result))


func _contract_conflict_preserves_state() -> void:
	var runtime = _runtime()
	runtime.dispatch("inventory.items", "DragDrop",
		{"source": "r0c0", "target": "r0c1", "version": 0})
	var before: Dictionary = runtime.qa_state().controls["inventory.items"]
	var result: Dictionary = runtime.dispatch("inventory.items", "DragDrop",
		{"source": "r0c1", "target": "r0c2", "version": 0})
	var after: Dictionary = runtime.qa_state().controls["inventory.items"]
	_check("gesture-conflict-preserves-state", not result.get("ok", false)
		and result.get("error", {}).get("code") == "GestureConflictError"
		and before.get("item_values", {}) == after.get("item_values", {})
		and before.get("item_version") == after.get("item_version"), str(result))


func _contract_qa_state_is_factual() -> void:
	var runtime = _runtime()
	runtime.dispatch("inventory.items", "Activate", {"item": "r0c2"})
	runtime.dispatch("inventory.items", "ModifierActivate",
		{"item": "r0c1", "modifiers": ["ctrl"]})
	var state: Dictionary = runtime.qa_state().controls["inventory.items"]
	_check("inventory-qa-state", state.get("value") == "r0c2"
		and state.get("selected_items", []) == ["r0c1"]
		and state.get("opened_item", "").is_empty()
		and state.get("item_values", {}).size() == 3
		and state.get("item_version") == 0
		and state.has("drag_state"), str(state))


func _fixture() -> Dictionary:
	var variants := {"idle": "fixture", "hover": "fixture", "pressed": "fixture"}
	var item_states := {"unselected": variants, "selected": variants,
		"modifier_selected": variants, "dragging": variants, "drop_target": variants}
	var surfaces := {}
	for index in 3:
		var item := "r0c%d" % index
		surfaces[item] = {"geometry": {"x": index * 54, "y": 0,
			"width": 54, "height": 61}, "state_set": item_states}
	var tab_surfaces := {}
	for index in 5:
		var tab: String = str(["item", "equip", "etc-1", "etc-2", "cash"][index])
		tab_surfaces[tab] = {"geometry": {"x": 0, "y": index * 39,
			"width": 26, "height": 36}, "state_set": {
				"selected": variants, "unselected": variants}}
	return {"id": "inventory", "controls": [
		{
			"id": "inventory.tabs", "type": "Tabs",
			"interaction_phases": ["idle", "hover", "pressed"],
			"semantic_states": ["ready"], "initial_semantic_state": "ready",
			"state_set": {"ready": variants}, "gestures": ["Activate"],
			"actions": [{"gesture": "Activate", "action": "SelectInventoryTab"}],
			"value": {"choices": ["item", "equip", "etc-1", "etc-2", "cash"],
				"initial": "item"}, "surfaces": tab_surfaces,
		},
		{
			"id": "inventory.items", "type": "SelectionView",
			"interaction_phases": ["idle", "hover", "pressed"],
			"semantic_states": ["unselected", "selected"],
			"initial_semantic_state": "unselected",
			"state_set": {"unselected": variants, "selected": variants},
			"gestures": ["Activate", "DoubleActivate", "ModifierActivate", "DragDrop"],
			"actions": [
				{"gesture": "Activate", "action": "SelectInventoryItem"},
				{"gesture": "DoubleActivate", "action": "OpenInventoryItem"},
				{"gesture": "ModifierActivate", "action": "ToggleInventorySelection"},
				{"gesture": "DragDrop", "action": "MoveInventoryItem"},
			],
			"value": {"items": ["r0c0", "r0c1", "r0c2"], "initial": "r0c0",
				"details": {"r0c0": "item 1", "r0c1": "item 2", "r0c2": "item 3"},
				"value_control_ids": {},
				"item_values": {"r0c0": "item-01", "r0c1": "item-02", "r0c2": "item-03"},
				"allowed_modifiers": ["ctrl"],
				"drop_targets": ["r0c0", "r0c1", "r0c2"], "initial_version": 0},
			"surfaces": surfaces,
		},
	]}


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "inventory-runtime", "total": results.size(),
		"failed": failed.size(), "results": results}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/inventory-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("INVENTORY %d/%d passed" % [results.size() - failed.size(), results.size()])
