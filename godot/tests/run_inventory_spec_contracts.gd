extends SceneTree
## Issue #127 construction-seam contracts. These freeze Inventory Tabs,
## multi-gesture SelectionView policy, resize bounds, and typed rejection
## before production adapters are implemented.

const ControlSpec = preload("res://control_library/control_spec.gd")
const Errors = preload("res://control_library/control_errors.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	_contract_inventory_production_manifest()
	_contract_valid_inventory_fixture()
	_contract_modifier_policy_fails_closed()
	_contract_drop_targets_fail_closed()
	_contract_item_identity_fails_closed()
	_contract_detail_view_fails_closed()
	_contract_resize_bounds_fail_closed()
	_contract_resize_frame_fails_closed()
	_contract_resize_relationships_fail_closed()
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _contract_inventory_production_manifest() -> void:
	var loaded: Dictionary = ControlSpec.load_and_validate(
		"res://data/image-79-control-spec.json")
	var windows: Array = loaded.manifest.get("windows", [])
	var inventory: Variant = windows.filter(func(window):
		return window is Dictionary and window.get("id") == "inventory").front() \
		if windows.any(func(window): return window is Dictionary \
			and window.get("id") == "inventory") else null
	var tabs: Array = inventory.get("controls", []).filter(func(control):
		return control is Dictionary and control.get("type") == "Tabs") \
		if inventory is Dictionary else []
	var selections: Array = inventory.get("controls", []).filter(func(control):
		return control is Dictionary and control.get("type") == "SelectionView") \
		if inventory is Dictionary else []
	_check("inventory-production-manifest", loaded.errors.is_empty()
		and inventory is Dictionary and tabs.size() == 1 and selections.size() == 1
		and tabs[0].value.choices.size() == 5
		and selections[0].value.items.size() == 28,
		str({"errors": loaded.errors, "inventory": inventory}))


func _contract_valid_inventory_fixture() -> void:
	var errors: Array[Dictionary] = ControlSpec.validate(_fixture(), func(_path): return true)
	_check("valid-inventory-gesture-contract", errors.is_empty(), str(errors))


func _contract_modifier_policy_fails_closed() -> void:
	var fixture := _fixture()
	fixture.windows[0].controls[1].value.allowed_modifiers = ["ctrl", "alt"]
	var errors: Array[Dictionary] = ControlSpec.validate(fixture, func(_path): return true)
	_check("invalid-modifier-policy-fails-closed", _has_code(errors, Errors.INVALID_MODIFIER),
		str(errors))


func _contract_drop_targets_fail_closed() -> void:
	var fixture := _fixture()
	fixture.windows[0].controls[1].value.drop_targets = ["r0c0", "missing"]
	var errors: Array[Dictionary] = ControlSpec.validate(fixture, func(_path): return true)
	_check("invalid-drop-target-fails-closed", _has_code(errors, Errors.INVALID_DROP_TARGET),
		str(errors))


func _contract_item_identity_fails_closed() -> void:
	var fixture := _fixture()
	fixture.windows[0].controls[1].value.item_values.r0c1 = "missing"
	var errors: Array[Dictionary] = ControlSpec.validate(fixture, func(_path): return true)
	_check("invalid-item-identity-fails-closed", _has_code(errors, Errors.INVALID_STATE_SET),
		str(errors))


func _contract_detail_view_fails_closed() -> void:
	var fixture := _fixture()
	fixture.windows[0].controls[1].value.detail_view.erase("padding")
	var errors: Array[Dictionary] = ControlSpec.validate(fixture, func(_path): return true)
	var oversized := _fixture()
	oversized.windows[0].controls[1].value.detail_view.padding = [1000, 1000]
	var oversized_errors: Array[Dictionary] = ControlSpec.validate(
		oversized, func(_path): return true)
	_check("missing-detail-padding-fails-closed",
		_has_code(errors, Errors.INVALID_STATE_SET)
		and _has_code(oversized_errors, Errors.INVALID_STATE_SET),
		str({"missing": errors, "oversized": oversized_errors}))


func _contract_resize_bounds_fail_closed() -> void:
	var fixture := _fixture()
	fixture.windows[0].resize.minimum = [735, 513]
	var errors: Array[Dictionary] = ControlSpec.validate(fixture, func(_path): return true)
	_check("invalid-resize-bounds-fail-closed", _has_code(errors, Errors.INVALID_GEOMETRY),
		str(errors))


func _contract_resize_frame_fails_closed() -> void:
	var missing_geometry := _fixture()
	missing_geometry.windows[0].resize.frame.erase("home_size")
	var geometry_errors: Array[Dictionary] = ControlSpec.validate(
		missing_geometry, func(_path): return true)
	var foreign_control := _fixture()
	foreign_control.windows[0].resize.frame.anchored_right_controls = ["inventory.missing"]
	var control_errors: Array[Dictionary] = ControlSpec.validate(
		foreign_control, func(_path): return true)
	_check("invalid-resize-frame-fails-closed",
		_has_code(geometry_errors, Errors.INVALID_GEOMETRY)
		and _has_code(control_errors, Errors.CONTROL_BINDING),
		str({"geometry": geometry_errors, "control": control_errors}))


func _contract_resize_relationships_fail_closed() -> void:
	var wrong_home := _fixture()
	wrong_home.windows[0].resize.frame.home_size = [1, 1]
	var home_errors: Array[Dictionary] = ControlSpec.validate(
		wrong_home, func(_path): return true)
	var wrong_grip := _fixture()
	wrong_grip.windows[0].resize.grip_geometry.x = 0
	wrong_grip.windows[0].resize.grip_geometry.y = 0
	var grip_errors: Array[Dictionary] = ControlSpec.validate(
		wrong_grip, func(_path): return true)
	var missing_state := _fixture()
	missing_state.windows[0].resize.erase("state_set")
	var state_errors: Array[Dictionary] = ControlSpec.validate(
		missing_state, func(_path): return true)
	var old_footer := _fixture()
	old_footer.windows[0].resize.frame.stale_footer_geometry = {
		"x": 0, "y": 279, "width": 484, "height": 24,
	}
	var footer_errors: Array[Dictionary] = ControlSpec.validate(
		old_footer, func(_path): return true)
	_check("resize-relationships-fail-closed",
		_has_code(home_errors, Errors.INVALID_GEOMETRY)
		and _has_code(grip_errors, Errors.INVALID_GEOMETRY)
		and _has_code(state_errors, Errors.INVALID_STATE_SET)
		and _has_code(footer_errors, Errors.INVALID_GEOMETRY),
		str({"home": home_errors, "grip": grip_errors, "state": state_errors,
			"footer": footer_errors}))


func _fixture() -> Dictionary:
	var variants := {"idle": "fixture", "hover": "fixture", "pressed": "fixture"}
	var item_states := {
		"unselected": variants, "selected": variants, "modifier_selected": variants,
		"dragging": variants, "drop_target": variants,
	}
	var surfaces := {}
	for index in 3:
		var item := "r0c%d" % index
		surfaces[item] = {
			"geometry": {"x": index * 54, "y": 0, "width": 54, "height": 61},
			"state_set": item_states,
		}
	var tab_surfaces := {}
	for index in 5:
		var tab: String = str(["item", "equip", "etc-1", "etc-2", "cash"][index])
		tab_surfaces[tab] = {
			"geometry": {"x": 0, "y": index * 39, "width": 26, "height": 36},
			"state_set": {"selected": variants, "unselected": variants},
		}
	return {
		"schema_version": 3,
		"reference": {"path": "fixture", "sha256":
			"f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f",
			"size": [1536, 1024]},
		"windows": [{
			"id": "inventory", "geometry": {"x": 0, "y": 701, "width": 484, "height": 303},
			"drag_geometry": {"x": 24, "y": 0, "width": 390, "height": 24},
			"resize": {"grip_geometry": {"x": 460, "y": 279, "width": 24, "height": 24},
				"minimum": [332, 220], "maximum": [734, 512],
				"state_set": {"ready": variants},
				"frame": {"home_size": [484, 303], "title_height": 24,
					"footer_height": 24, "right_edge_width": 4,
					"anchored_right_controls": ["inventory.tabs"],
					"stale_title_controls_geometry": {"x": 436, "y": 0,
						"width": 48, "height": 24},
					"stale_footer_grip_geometry": {"x": 460, "y": 279,
						"width": 24, "height": 24},
					"stale_footer_geometry": {"x": 0, "y": 278,
						"width": 484, "height": 25},
					"stale_right_edge_geometry": {"x": 480, "y": 24,
						"width": 4, "height": 255},
					"title_fill": "fixture", "footer": "fixture",
					"footer_fill": "fixture", "right_edge": "fixture"}},
			"plates": {"expanded": "fixture", "minimized": "fixture"},
			"gestures": ["Drag", "Resize", "KeyCommand"],
			"actions": [
				{"gesture": "Drag", "action": "MoveWindow"},
				{"gesture": "Resize", "action": "ResizeWindow"},
				{"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"},
			],
			"controls": [
				{
					"id": "inventory.tabs", "type": "Tabs",
					"geometry": {"x": 10, "y": 30, "width": 26, "height": 192},
					"interaction_phases": ["idle", "hover", "pressed"],
					"semantic_states": ["ready"], "initial_semantic_state": "ready",
					"state_set": {"ready": variants}, "gestures": ["Activate"],
					"actions": [{"gesture": "Activate", "action": "SelectInventoryTab"}],
					"value": {"choices": ["item", "equip", "etc-1", "etc-2", "cash"],
						"initial": "item"}, "surfaces": tab_surfaces,
				},
				{
					"id": "inventory.items", "type": "SelectionView",
					"geometry": {"x": 42, "y": 30, "width": 378, "height": 244},
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
						"item_values": {"r0c0": "r0c0", "r0c1": "r0c1", "r0c2": "r0c2"},
						"allowed_modifiers": ["ctrl"],
						"drop_targets": ["r0c0", "r0c1", "r0c2"], "initial_version": 0,
						"detail_view": {"size": [156, 50], "offset": [8, 0],
							"padding": [8, 5], "font": "fixture", "font_size": 12,
							"font_color": "#2a252a",
							"state_set": {"ready": variants}}},
					"surfaces": surfaces,
				},
			],
		}],
	}


func _has_code(errors: Array[Dictionary], code: String) -> bool:
	return errors.any(func(error): return error.get("code") == code)


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "inventory-spec", "total": results.size(),
		"failed": failed.size(), "results": results}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/inventory-spec-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("INVENTORY SPEC %d/%d passed" % [results.size() - failed.size(), results.size()])
