extends SceneTree
## Public-input smoke contracts for the Issue #128 production Storage Window.
## The exhaustive gesture drive is the browser Play Log; this native suite only
## proves that OS-style input reaches the production scene without private-node
## or adapter-method access.

var results: Array[Dictionary] = []
var desktop: Control
var window: ControlWindow


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	get_root().size = Vector2i(1973, 1319)
	change_scene_to_file("res://image79_options.tscn")
	await process_frame
	await process_frame
	desktop = current_scene
	window = desktop.storage
	_check("scene-valid", window != null and desktop.validation_errors.is_empty()
		and desktop.windows.size() == 11, str(desktop.validation_errors))
	await _click(Vector2(537, 704))
	_check("public-input-category",
		window.qa_state().controls["storage.categories"].value == "equipment",
		str(window.qa_state().controls["storage.categories"]))
	await _click(Vector2(632, 977))
	var state: Dictionary = window.qa_state()
	_check("list-layout-uses-declared-two-columns", state.window.view_mode == "list"
		and state.controls["storage.items"].list_labels.size() == 24,
		str(state.controls["storage.items"]))
	await _click(Vector2(632, 977))
	await _wheel(Vector2(1007, 800), 1)
	state = window.qa_state()
	_check("public-input-wheel-three", state.controls["storage.scroll"].offset == 3,
		str(state.controls["storage.scroll"]))
	_check("wheel-redraws-logical-items",
		state.controls["storage.items"].item_values["r0c0"] == "stock-021"
		and state.controls["storage.items"].rendered_item_values["r0c0"] == "stock-021"
		and str(state.controls["storage.items"].rendered_asset_paths["r0c0"])
			.ends_with("cell-r3c0-unselected-idle.png"),
		str(state.controls["storage.items"]))
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _click(point: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = point
	motion.global_position = point
	Input.parse_input_event(motion)
	await process_frame
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = point
	press.global_position = point
	Input.parse_input_event(press)
	await process_frame
	var release := press.duplicate()
	release.pressed = false
	Input.parse_input_event(release)
	await process_frame


func _wheel(point: Vector2, direction: int) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_WHEEL_DOWN if direction > 0 else MOUSE_BUTTON_WHEEL_UP
	event.pressed = true
	event.position = point
	event.global_position = point
	Input.parse_input_event(event)
	await process_frame


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/storage-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"suite": "storage-window", "total": results.size(),
		"failed": failed.size(), "results": results}, "  "))
	file.close()
	print("STORAGE PUBLIC INPUT %d/%d passed" % [results.size() - failed.size(), results.size()])
