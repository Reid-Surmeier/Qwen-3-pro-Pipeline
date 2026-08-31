extends SceneTree
## Issue #135 rendered Chat Room and real keyboard/scroll contracts.

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
	window = desktop.chat_room
	var idle := window.qa_state()
	_check("source-window-constructs", window != null
		and desktop.validation_errors.is_empty() and desktop.windows.size() == 11
		and idle.window.position == [1037.0, 782.0]
		and idle.window.size == [495.0, 226.0]
		and idle.window_state.lines.size() == 5
		and not idle.chat_room_overlay.visible, str(idle))

	await _click(Vector2(1120, 988))
	await _type_text("hello")
	await process_frame
	var typed := window.qa_state()
	_check("real-text-visible", typed.controls["chat_room.input"].rendered_text == "hello"
		and typed.window_state.draft == "hello", str(typed.controls["chat_room.input"]))
	await _send(false, false, false)
	var accepted := window.qa_state()
	_check("accepted-frame-clears-only", accepted.controls["chat_room.input"].rendered_text == ""
		and accepted.window_state.lines.size() == 5
		and accepted.window_state.pending_delivery.frames_remaining == 3
		and accepted.window_state.pending_delivery.scope == "screen", str(accepted.window_state))
	# The process-frame signal precedes Node._process. The first signal is the
	# accepted frame's tail; the next three completed process passes are N+1..3.
	await process_frame
	await process_frame
	var one := window.qa_state()
	await process_frame
	var two := window.qa_state()
	await process_frame
	var three := window.qa_state()
	_check("third-frame-exact-echo", one.window_state.lines.size() == 5
		and two.window_state.lines.size() == 5 and three.window_state.lines.size() == 6
		and three.window_state.lines[-1].text == "hello"
		and three.chat_room_overlay.rendered_lines[-1].ends_with("hello"), str(three))

	for scope_case in [["p", true, false, false, "party"],
			["g", false, true, false, "guild"],
			["a", false, false, true, "allied_guild"]]:
		await _type_text(scope_case[0])
		await process_frame
		await _send(scope_case[1], scope_case[2], scope_case[3])
		var submitted := window.qa_state()
		_check("modifier-scope-" + scope_case[4],
			submitted.window_state.pending_delivery != null \
				and submitted.window_state.pending_delivery.scope == scope_case[4],
			str(submitted.window_state.pending_delivery))
		await process_frame
		await process_frame
		await process_frame

	await _key(KEY_F10)
	_check("f10-changes-row-count", window.qa_state().window_state.visible_row_count == 7,
		str(window.qa_state().window_state))
	await _wheel(Vector2(1517, 865), 1)
	_check("wheel-moves-three-and-clamps", window.qa_state().controls["chat_room.scroll"].offset == 2,
		str(window.qa_state().controls["chat_room.scroll"]))

	await _key(KEY_F10, false, true)
	_check("alt-f10-hides", not window.visible, str(desktop.last_transaction))
	await _key(KEY_F10, false, true)
	_check("alt-f10-restores", window.visible, str(desktop.last_transaction))
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _type_text(text: String) -> void:
	for character in text:
		var event := InputEventKey.new()
		event.pressed = true
		event.unicode = character.unicode_at(0)
		Input.parse_input_event(event)
		await process_frame


func _send(ctrl: bool, alt: bool, shift: bool) -> void:
	await _key(KEY_ENTER, ctrl, alt, shift)


func _key(code: Key, ctrl := false, alt := false, shift := false) -> void:
	_emit_key(code, ctrl, alt, shift)
	await process_frame


func _emit_key(code: Key, ctrl := false, alt := false, shift := false) -> void:
	var event := InputEventKey.new()
	event.keycode = code
	event.pressed = true
	event.ctrl_pressed = ctrl
	event.alt_pressed = alt
	event.shift_pressed = shift
	Input.parse_input_event(event)


func _click(point: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = point
	motion.global_position = point
	Input.parse_input_event(motion)
	await process_frame
	var press := InputEventMouseButton.new()
	press.position = point
	press.global_position = point
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
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


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/chat-room-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"suite": "chat-room-window-contracts",
		"total": results.size(), "failed": failed.size(), "results": results}, "  "))
	file.close()
	print("CHAT ROOM WINDOW %d/%d passed" % [results.size() - failed.size(), results.size()])
