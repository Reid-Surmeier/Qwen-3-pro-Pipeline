extends SceneTree
## Public seam contracts for the image-79 ControlSpec manifest.
## These literals come from issue #124/#125, not from the implementation.

const ControlSpec = preload("res://control_library/control_spec.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	_contract_valid_manifest_is_accepted()
	_contract_options_manifest_is_complete()
	_contract_skill_tree_control_types_are_frozen()
	_contract_window_adapter_fields_fail_closed()
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
				"details": {"heal": "heal\n7 / 7", "holy-light": "holy-light\n5 / 5"}},
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
