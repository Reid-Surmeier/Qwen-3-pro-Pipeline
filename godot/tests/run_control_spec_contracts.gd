extends SceneTree
## Public seam contracts for the image-79 ControlSpec manifest.
## These literals come from issue #124/#125, not from the implementation.

const ControlSpec = preload("res://control_library/control_spec.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	_contract_valid_manifest_is_accepted()
	_contract_options_manifest_is_complete()
	_contract_skill_tree_control_types_are_frozen()
	_contract_selection_foreign_identity_fields_fail_closed()
	_contract_window_adapter_fields_fail_closed()
	_contract_party_adapter_fields_fail_closed()
	_contract_basic_info_fields_fail_closed()
	_contract_failures_are_named_and_fail_closed()
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _valid_manifest() -> Dictionary:
	return {
		"schema_version": 3,
		"reference": {
			"path": "res://reference.png",
			"sha256": "f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f",
			"size": [1536, 1024],
		},
		"windows": [{
			"id": "options",
			"geometry": {"x": 1108, "y": 297, "width": 424, "height": 202},
			"gestures": ["Drag", "KeyCommand"],
			"actions": [
				{"gesture": "Drag", "action": "MoveWindow"},
				{"gesture": "KeyCommand", "key": "Escape", "action": "CloseWindow"},
			],
			"plates": {
				"expanded": "res://options/window.png",
				"minimized": "res://options/minimized.png",
			},
			"controls": [{
				"id": "options.close",
				"type": "Button",
				"geometry": {"x": 397, "y": 4, "width": 22, "height": 25},
				"interaction_phases": ["idle", "hover", "pressed"],
				"semantic_states": ["ready"],
				"initial_semantic_state": "ready",
				"state_set": {"ready": {
					"idle": "res://options/close-idle.png",
					"hover": "res://options/close-hover.png",
					"pressed": "res://options/close-pressed.png",
				}},
				"gestures": ["Activate"],
				"actions": [{"gesture": "Activate", "action": "CloseWindow"}],
			}],
		}],
	}


func _all_assets_exist(_path: String) -> bool:
	return true


func _contract_valid_manifest_is_accepted() -> void:
	var errors: Array = ControlSpec.validate(_valid_manifest(), _all_assets_exist)
	_check("valid-manifest", errors.is_empty(), str(errors))


func _contract_options_manifest_is_complete() -> void:
	var loaded: Dictionary = ControlSpec.load_and_validate(
		"res://data/image-79-control-spec.json")
	var manifest: Dictionary = loaded.manifest
	var options: Dictionary = manifest.get("windows", [{}])[0]
	var ids: Array = options.get("controls", []).map(func(control): return control.id)
	_check("options-production-manifest", loaded.errors.is_empty()
		and options.id == "options" and ids.size() == 11
		and "options.bgm" in ids and "options.effect" in ids
		and "options.skin" in ids, str(loaded.errors))


func _contract_skill_tree_control_types_are_frozen() -> void:
	var fixture := _valid_manifest()
	var variants := {"idle": "res://fixture.png", "hover": "res://fixture.png",
		"pressed": "res://fixture.png"}
	fixture.windows[0].id = "skill_tree"
	fixture.windows[0].controls = [
		{
			"id": "skill_tree.skills", "type": "SelectionView",
			"geometry": {"x": 30, "y": 60, "width": 550, "height": 470},
			"interaction_phases": ["idle", "hover", "pressed"],
			"semantic_states": ["unselected", "selected"],
			"initial_semantic_state": "unselected",
			"state_set": {"unselected": variants, "selected": variants},
			"value": {"items": ["heal", "holy-light"], "initial": "heal",
				"details": {"heal": "heal\n7 / 7", "holy-light": "holy-light\n5 / 5"},
				"value_control_ids": {"heal": "skill_tree.stepper.heal"}},
			"surfaces": {
				"heal": {"geometry": {"x": 0, "y": 0, "width": 42, "height": 42},
					"state_set": {"unselected": variants, "selected": variants}},
				"holy-light": {"geometry": {"x": 100, "y": 0, "width": 42, "height": 42},
					"state_set": {"unselected": variants, "selected": variants}},
			},
			"gestures": ["Activate", "ContextActivate"],
			"actions": [
				{"gesture": "Activate", "action": "SelectSkill"},
				{"gesture": "ContextActivate", "action": "OpenSkillDetail"},
			],
		},
		{
			"id": "skill_tree.stepper.heal", "type": "Stepper",
			"geometry": {"x": 126, "y": 111, "width": 72, "height": 16},
			"interaction_phases": ["idle", "hover", "pressed"],
			"semantic_states": ["ready", "pending", "disabled"],
			"initial_semantic_state": "ready",
			"state_set": {"ready": variants, "pending": variants,
				"disabled": {"idle": "res://fixture.png"}},
			"value": {"minimum": 0, "maximum": 10, "current": 7,
				"target": 7, "step": 1},
			"surfaces": {
				"decrement": {"geometry": {"x": 0, "y": 0, "width": 18, "height": 16},
					"state_set": {"visible": variants, "hidden": variants}},
				"increment": {"geometry": {"x": 54, "y": 0, "width": 18, "height": 16},
					"state_set": {"visible": variants, "hidden": variants}},
			},
			"gestures": ["Activate"],
			"actions": [{"gesture": "Activate", "action": "StepSkill"}],
		},
	]
	var errors: Array = ControlSpec.validate(fixture, _all_assets_exist)
	_check("skill-tree-control-contracts", errors.is_empty(), str(errors))

	var bad_stepper := fixture.duplicate(true)
	bad_stepper.windows[0].controls[1].value.target = 11
	var stepper_errors: Array = ControlSpec.validate(bad_stepper, _all_assets_exist)
	_check("stepper-bounds-fail-closed",
		"InvalidStateSet" in stepper_errors.map(func(error): return error.code),
		str(stepper_errors))

	var bad_context := fixture.duplicate(true)
	bad_context.windows[0].controls[0].actions = [
		{"gesture": "Activate", "action": "SelectSkill"}]
	var context_errors: Array = ControlSpec.validate(bad_context, _all_assets_exist)
	_check("selection-context-binding-fails-closed",
		"ControlBindingError" in context_errors.map(func(error): return error.code),
		str(context_errors))

	var missing_details := fixture.duplicate(true)
	missing_details.windows[0].controls[0].value.details.erase("holy-light")
	var detail_errors: Array = ControlSpec.validate(missing_details, _all_assets_exist)
	_check("selection-details-fail-closed",
		"InvalidStateSet" in detail_errors.map(func(error): return error.code),
		str(detail_errors))

	var foreign_value_control := fixture.duplicate(true)
	foreign_value_control.windows[0].controls[0].value.value_control_ids.heal = \
		"other.stepper.heal"
	var foreign_value_errors: Array = ControlSpec.validate(foreign_value_control,
		_all_assets_exist)
	_check("selection-value-control-fails-closed",
		"ControlBindingError" in foreign_value_errors.map(func(error): return error.code),
		str(foreign_value_errors))


func _contract_selection_foreign_identity_fields_fail_closed() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(
		"res://data/image-79-control-spec.json"))
	var equipment_index: int = fixture.windows.find_custom(func(window):
		return window.get("id") == "equipment_items")
	var selection_index: int = fixture.windows[equipment_index].controls.find_custom(func(control):
		return control.get("id") == "equipment_items.slots")

	var missing_foreign := fixture.duplicate(true)
	missing_foreign.windows[equipment_index].controls[selection_index].value\
		.foreign_identity_assets.r0c0 = "res://missing-foreign-identity.png"
	var missing_errors: Array = ControlSpec.validate(missing_foreign,
		func(path: String) -> bool: return path != "res://missing-foreign-identity.png")
	_check("selection-foreign-asset-fails-closed", missing_errors.any(func(error):
		return error.code == "AssetIntegrityError" \
			and "foreign_identity_assets.r0c0" in str(error.path)), str(missing_errors))

	var bad_identity_surface := fixture.duplicate(true)
	bad_identity_surface.windows[equipment_index].controls[selection_index].value\
		.identity_surfaces.head = "missing-slot"
	var identity_errors: Array = ControlSpec.validate(bad_identity_surface,
		_all_assets_exist)
	_check("selection-identity-surface-fails-closed", identity_errors.any(func(error):
		return error.code == "ControlBindingError" \
			and "identity_surfaces.head" in str(error.path)), str(identity_errors))

	var bad_empty_flag := fixture.duplicate(true)
	bad_empty_flag.windows[equipment_index].controls[selection_index].value\
		.show_empty_slots = "yes"
	var empty_flag_errors: Array = ControlSpec.validate(bad_empty_flag,
		_all_assets_exist)
	_check("selection-empty-flag-fails-closed", empty_flag_errors.any(func(error):
		return error.code == "InvalidStateSet" \
			and "show_empty_slots" in str(error.path)), str(empty_flag_errors))

	var missing_available := fixture.duplicate(true)
	missing_available.windows[equipment_index].controls[selection_index].surfaces\
		.head.state_set.erase("available")
	var available_errors: Array = ControlSpec.validate(missing_available,
		_all_assets_exist)
	_check("selection-empty-slot-state-fails-closed", available_errors.any(func(error):
		return error.code == "InvalidStateSet" and "surfaces.head.state_set.available" \
			in str(error.path)), str(available_errors))


func _contract_window_adapter_fields_fail_closed() -> void:
	var fixture := _valid_manifest()
	var minimize: Dictionary = fixture.windows[0].controls[0].duplicate(true)
	minimize.id = "options.minimize"
	minimize.actions[0].action = "ToggleMinimized"
	fixture.windows[0].controls.append(minimize)
	var list_toggle: Dictionary = fixture.windows[0].controls[0].duplicate(true)
	list_toggle.id = "options.list-toggle"
	list_toggle.actions[0].action = "ToggleSkillView"
	fixture.windows[0].controls.append(list_toggle)
	fixture.windows[0].drag_geometry = {"x": 0, "y": 0, "width": 200, "height": 24}
	fixture.windows[0].minimized_controls = ["options.minimize", "options.close"]
	fixture.windows[0].plates.list = "res://options/list.png"
	_check("valid-window-adapter-fields",
		ControlSpec.validate(fixture, _all_assets_exist).is_empty())

	var bad_drag := fixture.duplicate(true)
	bad_drag.windows[0].drag_geometry.width = 0
	var drag_errors: Array = ControlSpec.validate(bad_drag, _all_assets_exist)
	_check("invalid-drag-geometry-fails-closed",
		"InvalidGeometry" in drag_errors.map(func(error): return error.code), str(drag_errors))

	var bad_minimized := fixture.duplicate(true)
	bad_minimized.windows[0].minimized_controls = ["options.missing"]
	var minimized_errors: Array = ControlSpec.validate(bad_minimized, _all_assets_exist)
	_check("unknown-minimized-control-fails-closed",
		"InvalidControlSpec" in minimized_errors.map(func(error): return error.code),
		str(minimized_errors))

	var bad_list := fixture.duplicate(true)
	var list_errors: Array = ControlSpec.validate(bad_list,
		func(path: String) -> bool: return not path.ends_with("list.png"))
	_check("missing-list-plate-fails-closed",
		"AssetIntegrityError" in list_errors.map(func(error): return error.code),
		str(list_errors))

	var omitted_list := fixture.duplicate(true)
	omitted_list.windows[0].plates.erase("list")
	var omitted_list_errors: Array = ControlSpec.validate(omitted_list, _all_assets_exist)
	_check("omitted-required-list-plate-fails-closed",
		"AssetIntegrityError" in omitted_list_errors.map(func(error): return error.code),
		str(omitted_list_errors))

	var missing_window_action := fixture.duplicate(true)
	missing_window_action.windows[0].actions = [
		{"gesture": "Drag", "action": "MoveWindow"}]
	var missing_window_action_errors: Array = ControlSpec.validate(
		missing_window_action, _all_assets_exist)
	_check("window-gesture-binding-fails-closed",
		"ControlBindingError" in missing_window_action_errors.map(func(error): return error.code),
		str(missing_window_action_errors))

	var unknown_window_action := fixture.duplicate(true)
	unknown_window_action.windows[0].actions[0].action = "TeleportWindow"
	var unknown_window_action_errors: Array = ControlSpec.validate(
		unknown_window_action, _all_assets_exist)
	_check("window-action-routing-fails-closed",
		"ActionRoutingError" in unknown_window_action_errors.map(func(error): return error.code),
		str(unknown_window_action_errors))

	var missing_key := fixture.duplicate(true)
	missing_key.windows[0].actions[1].erase("key")
	var missing_key_errors: Array = ControlSpec.validate(missing_key, _all_assets_exist)
	_check("window-key-command-fails-closed",
		"ControlBindingError" in missing_key_errors.map(func(error): return error.code),
		str(missing_key_errors))


func _contract_party_adapter_fields_fail_closed() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(
		"res://data/image-79-control-spec.json"))
	var window_index: int = fixture.windows.find_custom(func(window):
		return window.get("id") == "party")
	var party: Dictionary = fixture.windows[window_index]

	var duplicate_actions := fixture.duplicate(true)
	var first_action := str(party.state_adapter.controls.actions[0])
	duplicate_actions.windows[window_index].state_adapter.controls.actions = [
		first_action, first_action, first_action, first_action, first_action]
	var duplicate_errors: Array = ControlSpec.validate(duplicate_actions, _all_assets_exist)
	_check("party-action-mapping-permutation-fails-closed", duplicate_errors.any(func(error):
		return error.code == "ControlBindingError" \
			and "controls.actions" in str(error.path)), str(duplicate_errors))

	var mismatched_action := fixture.duplicate(true)
	var action_index: int = party.controls.find_custom(func(control):
		return control.get("id") == first_action)
	mismatched_action.windows[window_index].controls[action_index].value.action_id = \
		"party.action.leave"
	var mismatch_errors: Array = ControlSpec.validate(mismatched_action, _all_assets_exist)
	_check("party-action-identity-fails-closed", mismatch_errors.any(func(error):
		return error.code == "ControlBindingError" \
			and "controls.actions" in str(error.path)), str(mismatch_errors))


func _contract_basic_info_fields_fail_closed() -> void:
	var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(
		"res://data/image-79-control-spec.json"))
	var window_index: int = fixture.windows.find_custom(func(window):
		return window.get("id") == "basic_info")
	var destination_index: int = fixture.windows[window_index].controls.find_custom(
		func(control): return control.get("id") == "basic_info.destination.status")

	var bad_backing := fixture.duplicate(true)
	bad_backing.windows[window_index].backing_color = "transparent-ish"
	var backing_errors: Array = ControlSpec.validate(bad_backing, _all_assets_exist)
	_check("invalid-backing-color-fails-closed", backing_errors.any(func(error):
		return error.code == "InvalidControlSpec" and "backing_color" in str(error.path)),
		str(backing_errors))

	var bad_facts := fixture.duplicate(true)
	bad_facts.windows[window_index].display_facts[0].geometry[2] = 0
	var fact_errors: Array = ControlSpec.validate(bad_facts, _all_assets_exist)
	_check("invalid-display-fact-fails-closed", fact_errors.any(func(error):
		return error.code == "InvalidGeometry" and "display_facts" in str(error.path)),
		str(fact_errors))

	var bad_minimized := fixture.duplicate(true)
	bad_minimized.windows[window_index].minimized_height = 206
	var minimized_errors: Array = ControlSpec.validate(bad_minimized, _all_assets_exist)
	_check("invalid-minimized-height-fails-closed", minimized_errors.any(func(error):
		return error.code == "InvalidGeometry" and "minimized_height" in str(error.path)),
		str(minimized_errors))

	var missing_target := fixture.duplicate(true)
	missing_target.windows[window_index].controls[destination_index].value.erase(
		"target_window")
	var target_errors: Array = ControlSpec.validate(missing_target, _all_assets_exist)
	_check("missing-open-window-target-fails-closed", target_errors.any(func(error):
		return error.code == "ControlBindingError" and "target_window" in str(error.path)),
		str(target_errors))


func _contract_failures_are_named_and_fail_closed() -> void:
	var cases: Array[Dictionary] = []

	var bad_reference := _valid_manifest()
	bad_reference.reference.sha256 = "not-a-sha"
	cases.append({"name": "visual-authority", "manifest": bad_reference,
		"expected": "VisualAuthorityError", "assets": _all_assets_exist})

	var bad_type := _valid_manifest()
	bad_type.windows[0].controls[0].type = "Mystery"
	cases.append({"name": "unknown-control", "manifest": bad_type,
		"expected": "UnknownControlType", "assets": _all_assets_exist})

	var bad_geometry := _valid_manifest()
	bad_geometry.windows[0].controls[0].geometry.width = 0
	cases.append({"name": "invalid-geometry", "manifest": bad_geometry,
		"expected": "InvalidGeometry", "assets": _all_assets_exist})

	var bad_states := _valid_manifest()
	bad_states.windows[0].controls[0].state_set.ready.erase("hover")
	cases.append({"name": "invalid-state-set", "manifest": bad_states,
		"expected": "InvalidStateSet", "assets": _all_assets_exist})

	var bad_gesture := _valid_manifest()
	bad_gesture.windows[0].controls[0].gestures = ["Teleport"]
	cases.append({"name": "unsupported-gesture", "manifest": bad_gesture,
		"expected": "UnsupportedGesture", "assets": _all_assets_exist})

	var bad_binding := _valid_manifest()
	bad_binding.windows[0].controls[0].actions = []
	cases.append({"name": "missing-binding", "manifest": bad_binding,
		"expected": "ControlBindingError", "assets": _all_assets_exist})

	var unknown_action := _valid_manifest()
	unknown_action.windows[0].controls[0].actions[0].action = "InventedAction"
	cases.append({"name": "unknown-action", "manifest": unknown_action,
		"expected": "ActionRoutingError", "assets": _all_assets_exist})

	var malformed_toggle := _valid_manifest()
	malformed_toggle.windows[0].controls[0].type = "Toggle"
	malformed_toggle.windows[0].controls[0].semantic_states = ["only"]
	malformed_toggle.windows[0].controls[0].initial_semantic_state = "only"
	malformed_toggle.windows[0].controls[0].state_set = {
		"only": {"idle": "res://options/close-idle.png",
			"hover": "res://options/close-hover.png",
			"pressed": "res://options/close-pressed.png"}}
	malformed_toggle.windows[0].controls[0].actions[0].action = "ToggleValue"
	cases.append({"name": "malformed-toggle", "manifest": malformed_toggle,
		"expected": "InvalidStateSet", "assets": _all_assets_exist})

	var bad_surface_geometry := _valid_manifest()
	bad_surface_geometry.windows[0].controls[0].surfaces = {
		"icon": {"geometry": {"x": 0, "y": 0, "width": 0, "height": 8},
			"asset": "res://options/icon.png"},
	}
	cases.append({"name": "invalid-surface-geometry", "manifest": bad_surface_geometry,
		"expected": "InvalidGeometry", "assets": _all_assets_exist})

	var missing_surface_asset := _valid_manifest()
	missing_surface_asset.windows[0].controls[0].surfaces = {
		"icon": {"geometry": {"x": 0, "y": 0, "width": 8, "height": 8},
			"asset": "res://options/missing-surface.png"},
	}
	cases.append({"name": "missing-surface-asset", "manifest": missing_surface_asset,
		"expected": "AssetIntegrityError",
		"assets": func(path: String) -> bool: return not path.ends_with("missing-surface.png")})

	var malformed_range := _valid_manifest()
	malformed_range.windows[0].controls[0].type = "Range"
	malformed_range.windows[0].controls[0].value = {"minimum": 100, "maximum": 0}
	cases.append({"name": "malformed-range", "manifest": malformed_range,
		"expected": "InvalidStateSet", "assets": _all_assets_exist})

	var malformed_dropdown := _valid_manifest()
	malformed_dropdown.windows[0].controls[0].type = "Dropdown"
	malformed_dropdown.windows[0].controls[0].value = {
		"choices": ["one", "one"], "initial": "missing"}
	cases.append({"name": "malformed-dropdown", "manifest": malformed_dropdown,
		"expected": "InvalidStateSet", "assets": _all_assets_exist})

	var duplicate := _valid_manifest()
	duplicate.windows[0].controls.append(duplicate.windows[0].controls[0].duplicate(true))
	cases.append({"name": "duplicate-control", "manifest": duplicate,
		"expected": "InvalidControlSpec", "assets": _all_assets_exist})

	cases.append({"name": "missing-asset", "manifest": _valid_manifest(),
		"expected": "AssetIntegrityError",
		"assets": func(path: String) -> bool: return not path.ends_with("close-hover.png")})

	for case in cases:
		var errors: Array = ControlSpec.validate(case.manifest, case.assets)
		var codes := errors.map(func(error): return error.code)
		_check(case.name, case.expected in codes, str(errors))


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "control-spec", "total": results.size(),
		"failed": failed.size(), "results": results}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/control-spec-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("CONTROL SPEC %d/%d passed" % [results.size() - failed.size(), results.size()])
