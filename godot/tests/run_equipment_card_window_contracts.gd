extends SceneTree
## Public-input contracts for the Issue #129 Equipment Card Window.

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
	window = desktop.windows.get("equipment_card")
	_check("scene-valid", window != null and desktop.validation_errors.is_empty()
		and desktop.windows.size() == 5, str(desktop.validation_errors))
	if window != null:
		var state: Dictionary = window.qa_state()
		_check("attested-detail-is-public", state.window.detail_item == "mistress-card",
			str(state.window))
		await _click(Vector2(1122, 14))
		_check("purpose-built-minimize", window.qa_state().window.minimized
			and window.size.y == 28.0, str(window.qa_state()))
		await _click(Vector2(1122, 14))
		_check("restore", not window.qa_state().window.minimized
			and window.size.y == 290.0, str(window.qa_state().window))
		await _wheel(Vector2(1510, 160), 1)
		state = window.qa_state()
		_check("unattested-scroll-rejected", state.controls["equipment_card.scroll"].offset == 0
			and state.controls["equipment_card.scroll"].last_error.code == "VisualAuthorityError",
			str(state.controls["equipment_card.scroll"]))
		window.move_to_front()
		await _escape()
		_check("escape-routes-detail", window.qa_state().window.visible == false
			and window.qa_state().window.detail_item.is_empty()
			and desktop.last_transaction.get("action") == "CloseDetail"
			and desktop.last_transaction.get("detail_item") == "mistress-card",
			str(desktop.last_transaction))
		window.visible = true
		window.detail_item = "mistress-card"
		window.move_to_front()
		await _click(Vector2(1517, 16))
		_check("close-routes-detail", window.qa_state().window.visible == false
			and window.qa_state().window.detail_item.is_empty()
			and desktop.last_transaction.get("action") == "CloseDetail"
			and desktop.last_transaction.get("detail_item") == "mistress-card",
			str(desktop.last_transaction))
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
	var release := event.duplicate()
	release.pressed = false
	Input.parse_input_event(release)
	await process_frame


func _escape() -> void:
	var event := InputEventKey.new()
	event.keycode = KEY_ESCAPE
	event.pressed = true
	Input.parse_input_event(event)
	await process_frame
	var release := event.duplicate()
	release.pressed = false
	Input.parse_input_event(release)
	await process_frame


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/equipment-card-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"suite": "equipment-card-window", "total": results.size(),
		"failed": failed.size(), "results": results}, "  "))
	file.close()
	print("EQUIPMENT CARD WINDOW %d/%d passed" % [results.size() - failed.size(), results.size()])
