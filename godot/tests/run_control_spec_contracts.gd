extends SceneTree
## Public seam contracts for the image-79 ControlSpec manifest.
## These literals come from issue #124/#125, not from the implementation.

const ControlSpec = preload("res://control_library/control_spec.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	_contract_valid_manifest_is_accepted()
	_contract_options_manifest_is_complete()
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
