extends SceneTree
## Real InputEvent contracts for the issue #125 production Options Window.

var results: Array[Dictionary] = []
var desktop: Control
var window: ControlWindow
var state_change_count := 0


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	# Headless defaults to a 64×64 host surface; match the project's viewport so
	# parsed InputEvents address the same coordinates as the browser/native run.
	get_root().size = Vector2i(1973, 1319)
	change_scene_to_file("res://image79_options.tscn")
	await process_frame
	await process_frame
	desktop = current_scene
	window = desktop.options
	window.state_changed.connect(func(_window_id: String): state_change_count += 1)
	_check("scene-valid", window != null and desktop.validation_errors.is_empty(),
		str(desktop.validation_errors))
	await _pressed_phase_publication()
	await _toggle_reversal()
	await _range_drag()
	await _dropdown_lifecycle()
	await _escape_without_open_dropdown_is_inert()
	await _minimize_restore()
	await _window_drag()
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _pressed_phase_publication() -> void:
	var fixtures := [
		{"id": "options.attack", "point": window.global_position + Vector2(36, 178)},
		{"id": "options.bgm", "point": window.global_position + Vector2(123, 60)},
		{"id": "options.skin", "point": window.global_position + Vector2(220, 134)},
	]
	var published := true
	for fixture in fixtures:
		await _move(fixture.point, false)
		var before := state_change_count
		var event := InputEventMouseButton.new()
		event.position = fixture.point
		event.global_position = fixture.point
		event.button_index = MOUSE_BUTTON_LEFT
		event.pressed = true
		Input.parse_input_event(event)
		await process_frame
		var state: Dictionary = window.qa_state().controls[fixture.id]
		published = published and state.interaction_phase == "pressed" \
			and state_change_count > before
		await _release(fixture.point)
		if fixture.id == "options.attack":
			await _click(fixture.point)
	if window.qa_state().controls["options.skin"].semantic_state == "open":
		await _key(KEY_ESCAPE)
	_check("pressed-phase-publication", published,
		"state changes=%d" % state_change_count)


func _toggle_reversal() -> void:
	var point := window.global_position + Vector2(36, 178)
	var before: String = str(window.qa_state().controls["options.attack"].semantic_state)
	await _click(point)
	var during: String = str(window.qa_state().controls["options.attack"].semantic_state)
	await _click(point)
	var after: String = str(window.qa_state().controls["options.attack"].semantic_state)
	_check("real-toggle-reversal", before == "off" and during == "on" and after == before,
		str([before, during, after]))


func _range_drag() -> void:
	var start := window.global_position + Vector2(131, 60)
	var finish := window.global_position + Vector2(355, 60)
	await _press(start)
	var values: Array[float] = []
	for index in 31:
		var point := start.lerp(finish, float(index) / 30.0)
		await _move(point, true)
		values.append(float(window.qa_state().controls["options.bgm"].value))
	await _release(finish)
	var monotonic := true
	for index in range(1, values.size()):
		monotonic = monotonic and values[index] >= values[index - 1]
	_check("real-range-31-frames", values.size() == 31 and monotonic
		and values[-1] >= 99.0, str(values))


func _dropdown_lifecycle() -> void:
	var field_point := window.global_position + Vector2(220, 134)
	await _click(field_point)
	var opened: String = str(window.qa_state().controls["options.skin"].semantic_state)
	var row_point := window.global_position + Vector2(220, 217)
	await _click(row_point)
	var selected: Dictionary = window.qa_state().controls["options.skin"]
	var dropdown: DropdownControl = window.control_nodes["options.skin"]
	var selected_field_path := dropdown.field.texture.resource_path
	await _click(field_point)
	await _key(KEY_ESCAPE)
	var dismissed: String = str(window.qa_state().controls["options.skin"].semantic_state)
	_check("real-dropdown-lifecycle", opened == "open" and selected.value == "tanublue"
		and selected.semantic_state == "closed" and dismissed == "closed", str(selected))
	_check("selected-dropdown-uses-unlabelled-field",
		selected_field_path.contains("dropdown-field-blank-")
		and dropdown.label.visible and dropdown.label.text == "tanublue",
		str({"field": selected_field_path, "label": dropdown.label.text}))


func _escape_without_open_dropdown_is_inert() -> void:
	await _key(KEY_ESCAPE)
	_check("closed-dropdown-escape-is-inert", window.qa_state().window.visible,
		str(window.qa_state().window))


func _minimize_restore() -> void:
	var point := window.global_position + Vector2(382, 17)
	await _click(point)
	var minimized_state: Dictionary = window.qa_state().window
	await _click(point)
	var restored_state: Dictionary = window.qa_state().window
	var minimized: bool = bool(minimized_state.minimized) \
		and minimized_state.size == [424.0, 28.0]
	var restored: bool = not bool(restored_state.minimized) \
		and restored_state.size == [424.0, 202.0]
	_check("real-distinct-minimize-restore", minimized and restored,
		str(window.qa_state().window))


func _window_drag() -> void:
	var start := window.global_position + Vector2(100, 14)
	var target := start + Vector2(-80, 90)
	var before: Array = window.qa_state().window.position
	await _press(start)
	await _move(target, true)
	await _release(target)
	var after: Array = window.qa_state().window.position
	_check("real-window-drag", is_equal_approx(after[0], before[0] - 80.0)
		and is_equal_approx(after[1], before[1] + 90.0), str([before, after]))


func _click(point: Vector2) -> void:
	await _press(point)
	await _release(point)


func _press(point: Vector2) -> void:
	await _move(point, false)
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


func _key(keycode: Key) -> void:
	var down := InputEventKey.new()
	down.keycode = keycode
	down.pressed = true
	Input.parse_input_event(down)
	await process_frame
	var up := InputEventKey.new()
	up.keycode = keycode
	up.pressed = false
	Input.parse_input_event(up)
	await process_frame


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "options-real-input", "total": results.size(),
		"failed": failed.size(), "results": results}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/options-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("OPTIONS REAL INPUT %d/%d passed" % [results.size() - failed.size(), results.size()])
