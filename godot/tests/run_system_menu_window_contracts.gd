extends SceneTree
## Issue #134 rendered System Menu and real-input contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlWindow = preload("res://control_library/control_window.gd")

var results: Array[Dictionary] = []
var window: ControlWindow


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	# Match the project's stretch transform so source-native pointer positions
	# resolve through the same real input path as the production scene.
	get_root().size = Vector2i(1973, 1319)
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(
		func(candidate): return candidate.get("id") == "system_menu")
	if matches.is_empty():
		_check("system-menu-window-constructs", false, "manifest absent")
		_finish()
		return
	window = ControlWindow.new()
	window.configure(matches[0])
	get_root().add_child(window)
	await process_frame
	var idle := window.qa_state()
	_check("system-menu-window-constructs", idle.window.position == [1328.0, 505.0]
		and idle.window.size == [204.0, 273.0] and idle.controls.size() == 8,
		str(idle))
	var original_position: Array = idle.window.position
	await _click(Vector2(1511, 517))
	var minimized := window.qa_state()
	_check("purpose-built-minimize", minimized.window.minimized
		and minimized.window.size == [204.0, 27.0]
		and minimized.window.position == original_position
		and minimized.window.plate_asset == matches[0].plates.minimized,
		str(minimized.window))
	await _click(Vector2(1511, 517))
	var restored := window.qa_state()
	_check("restore-preserves-geometry", not restored.window.minimized
		and restored.window.size == [204.0, 273.0]
		and restored.window.position == original_position, str(restored.window))
	await _press(Vector2(1400, 517))
	await _move(Vector2(1300, 417), true)
	await _release(Vector2(1300, 417))
	var dragged := window.qa_state()
	_check("title-drag-is-continuous-and-clamped", dragged.window.position == [1228.0, 405.0],
		str(dragged.window))
	window.reset()
	await process_frame
	await _click(Vector2(1430, 754))
	_check("return-to-game-closes", not window.qa_state().window.visible,
		str(window.qa_state().window))
	window.reset()
	await process_frame
	var escape := InputEventKey.new()
	escape.keycode = KEY_ESCAPE
	escape.pressed = true
	Input.parse_input_event(escape)
	await process_frame
	var escaped: Dictionary = window.qa_state().window
	_check("frontmost-escape-is-return-to-game", not escaped.visible
		and escaped.last_gesture == "KeyCommand" and escaped.last_action == "CloseWindow",
		str(escaped))
	window.queue_free()
	_finish()


func _click(point: Vector2) -> void:
	await _press(point)
	await _release(point)


func _press(point: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.position = point
	event.global_position = point
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	Input.parse_input_event(event)
	await process_frame


func _release(point: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.position = point
	event.global_position = point
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = false
	Input.parse_input_event(event)
	await process_frame


func _move(point: Vector2, held: bool) -> void:
	var event := InputEventMouseMotion.new()
	event.position = point
	event.global_position = point
	event.button_mask = MOUSE_BUTTON_MASK_LEFT if held else 0
	Input.parse_input_event(event)
	await process_frame


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "system-menu-window-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/system-menu-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("SYSTEM MENU WINDOW %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
