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
