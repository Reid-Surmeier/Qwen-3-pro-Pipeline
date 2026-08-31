extends SceneTree
## Issue #128 Storage manifest and source-lock contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	var loaded: Dictionary = ControlSpec.load_and_validate(
		"res://data/image-79-control-spec.json")
	_check("manifest-valid", loaded.errors.is_empty(), str(loaded.errors))
	var storage: Dictionary = loaded.manifest.windows.filter(func(window):
		return window.id == "storage").front()
	var controls := {}
	for control in storage.controls:
		controls[str(control.id)] = control
	_check("source-geometry", float(storage.geometry.x) == 492.0
		and float(storage.geometry.y) == 609.0 and float(storage.geometry.width) == 539.0
		and float(storage.geometry.height) == 393.0, str(storage.geometry))
	_check("shared-types-declared", controls["storage.scroll"].type == "ScrollView"
		and controls["storage.search"].type == "TextField", str(controls.keys()))
	_check("scroll-contract", controls["storage.scroll"].value.wheel_rows == 3
		and controls["storage.scroll"].value.arrow_rows == 1
		and controls["storage.scroll"].value.selection_control_id == "storage.items",
		str(controls["storage.scroll"].value))
	_check("learned-state-sets-declared",
		"dragging" in controls["storage.scroll"].interaction_phases
		and "focused" in controls["storage.search"].interaction_phases
		and controls["storage.items"].surfaces.r0c0.state_set.has("transferring"),
		str([controls["storage.scroll"].interaction_phases,
			controls["storage.search"].interaction_phases,
			controls["storage.items"].surfaces.r0c0.state_set.keys()]))
	_check("scroll-endpoint-arrows-are-distinct",
		controls["storage.scroll"].surfaces.decrement.state_set.at_start.idle \
			!= controls["storage.scroll"].surfaces.decrement.state_set.between.idle
		and controls["storage.scroll"].surfaces.increment.state_set.at_end.idle \
			!= controls["storage.scroll"].surfaces.increment.state_set.between.idle,
		str(controls["storage.scroll"].surfaces))
	var has_transfer := false
	for binding in controls["storage.items"].actions:
		has_transfer = has_transfer or (binding.gesture == "ModifierDoubleActivate" \
			and binding.action == "TransferStorageItem")
	_check("transfer-gesture-distinct",
		"ModifierDoubleActivate" in controls["storage.items"].gestures and has_transfer,
		str(controls["storage.items"].actions))
	_check("complete-window-controls", controls.size() == 9
		and controls["storage.categories"].value.choices.size() == 6
		and controls["storage.items"].value.items.size() == 35, str(controls.keys()))
	var wrong_link: Dictionary = loaded.manifest.duplicate(true)
	var wrong_storage: Dictionary = wrong_link.windows.filter(func(window):
		return window.id == "storage").front()
	for control in wrong_storage.controls:
		if control.id == "storage.scroll":
			control.value.selection_control_id = "storage.search"
	var wrong_link_errors: Array = ControlSpec.validate(wrong_link,
		func(_path: String) -> bool: return true)
	_check("linked-selection-type-fails-closed",
		"ControlBindingError" in wrong_link_errors.map(func(error): return error.code),
		str(wrong_link_errors))
	var missing_font: Dictionary = loaded.manifest.duplicate(true)
	var missing_font_storage: Dictionary = missing_font.windows.filter(func(window):
		return window.id == "storage").front()
	for control in missing_font_storage.controls:
		if control.id == "storage.search":
			control.tokens.font = "res://fonts/missing-storage-font.ttf"
	var font_errors: Array = ControlSpec.validate(missing_font,
		func(path: String) -> bool: return not path.ends_with("missing-storage-font.ttf"))
	_check("text-field-font-fails-closed",
		"AssetIntegrityError" in font_errors.map(func(error): return error.code),
		str(font_errors))
	var missing_list: Dictionary = loaded.manifest.duplicate(true)
	var missing_list_storage: Dictionary = missing_list.windows.filter(func(window):
		return window.id == "storage").front()
	missing_list_storage.plates.erase("list")
	var list_errors: Array = ControlSpec.validate(missing_list,
		func(_path: String) -> bool: return true)
	_check("storage-view-list-plate-fails-closed",
		"AssetIntegrityError" in list_errors.map(func(error): return error.code),
		str(list_errors))
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/storage-spec-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"suite": "storage-spec", "total": results.size(),
		"failed": failed.size(), "results": results}, "  "))
	file.close()
	print("STORAGE SPEC %d/%d passed" % [results.size() - failed.size(), results.size()])
