extends SceneTree
## Issue #134 assembled-desktop routing and contextual Escape contracts.

const Desktop = preload("res://scripts/image79_desktop.gd")

var results: Array[Dictionary] = []
var desktop: Control


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	get_root().size = Vector2i(1973, 1319)
	desktop = Desktop.new()
	get_root().add_child(desktop)
	await process_frame
	await process_frame
	_check("assembled-desktop-has-system-menu",
		desktop.validation_errors.is_empty() and desktop.windows.size() == 10
		and desktop.system_menu != null and desktop.system_menu.visible,
		str(desktop.qa_state()))

	var system_before_options_escape := _window_fact("system_menu")
	var unrelated_before_options_escape := _facts_except(["options", "system_menu"])
	desktop.options.visible = true
	desktop.options.move_to_front()
	await process_frame
	await _escape()
	var after_options_escape: Dictionary = desktop.qa_state()
	_check("frontmost-options-consumes-escape-without-system-menu-side-effect",
		not after_options_escape.windows.options.window.visible
		and after_options_escape.windows.options.window.last_action == "CloseWindow"
		and _window_fact("system_menu") == system_before_options_escape
		and _facts_except(["options", "system_menu"]) == unrelated_before_options_escape,
		str(after_options_escape))
	desktop.options.reset()
	desktop.system_menu.move_to_front()
	await process_frame

	var unrelated_before := _unrelated_facts()
	await _escape()
	var after_return: Dictionary = desktop.qa_state()
	_check("frontmost-system-escape-only-closes-system-menu",
		not after_return.windows.system_menu.window.visible
		and after_return.windows.system_menu.window.last_action == "CloseWindow"
		and _unrelated_facts() == unrelated_before, str(after_return))

	for window_id in desktop.windows:
		desktop.windows[window_id].visible = false
	await process_frame
	var hidden_facts := _unrelated_facts()
	await _escape()
	var opened: Dictionary = desktop.qa_state()
	_check("unhandled-escape-opens-system-menu-only",
		opened.windows.system_menu.window.visible
		and opened.last_transaction.get("ok", false)
		and opened.last_transaction.get("source_window") == "desktop"
		and opened.last_transaction.get("control_id") == "desktop.escape"
		and opened.last_transaction.get("semantic_state_preserved")
		and _unrelated_facts() == hidden_facts, str(opened.last_transaction))

	desktop.options.position = Vector2(900, 300)
	desktop.options.visible = false
	var options_semantic: Dictionary = desktop.options.runtime.qa_state()
	await _click(Vector2(1430, 617))
	var routed: Dictionary = desktop.qa_state()
	_check("sound-settings-opens-options-without-reset",
		routed.windows.options.window.visible
		and routed.windows.options.window.position == [900.0, 300.0]
		and desktop.options.runtime.qa_state() == options_semantic
		and routed.last_transaction.get("ok", false)
		and routed.last_transaction.get("target_window") == "options"
		and routed.last_transaction.get("semantic_state_preserved"),
		str(routed.last_transaction))

	desktop.system_menu.visible = true
	desktop.system_menu.move_to_front()
	var window_facts_before := _all_window_facts()
	var state_before := JSON.stringify(
		desktop.system_menu.runtime.qa_state().window_state)
	await _click(Vector2(1430, 549))
	var rejected: Dictionary = desktop.qa_state()
	var control_error: Variant = rejected.windows.system_menu.controls[
		"system_menu.save_point"].last_error
	_check("unsupported-destination-rejects-without-window-mutation",
		not rejected.last_transaction.get("ok", true)
		and rejected.last_transaction.get("error", {}).get("code") == "ActionRoutingError"
		and control_error is Dictionary \
		and control_error.get("code") == "ActionRoutingError"
		and JSON.stringify(desktop.system_menu.runtime.qa_state().window_state) == state_before
		and _all_window_facts() == window_facts_before,
		str([rejected.last_transaction, control_error]))

	desktop.queue_free()
	_finish()


func _escape() -> void:
	var event := InputEventKey.new()
	event.keycode = KEY_ESCAPE
	event.pressed = true
	Input.parse_input_event(event)
	await process_frame


func _click(point: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.position = point
	event.global_position = point
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	Input.parse_input_event(event)
	await process_frame
	event = InputEventMouseButton.new()
	event.position = point
	event.global_position = point
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = false
	Input.parse_input_event(event)
	await process_frame


func _unrelated_facts() -> Dictionary:
	var facts := {}
	for window_id in desktop.windows:
		if window_id != "system_menu":
			var state: Dictionary = desktop.windows[window_id].qa_state()
			facts[window_id] = {"window": state.window,
				"semantic": state.window_state, "controls": state.controls}
	return facts


func _all_window_facts() -> Dictionary:
	var facts := {}
	for window_id in desktop.windows:
		var state: Dictionary = desktop.windows[window_id].qa_state()
		facts[window_id] = {"position": state.window.position,
			"size": state.window.size, "visible": state.window.visible,
			"minimized": state.window.minimized,
			"window_state": state.window_state}
	return facts


func _window_fact(window_id: String) -> Dictionary:
	var state: Dictionary = desktop.windows[window_id].qa_state()
	return {"position": state.window.position,
		"size": state.window.size, "visible": state.window.visible,
		"minimized": state.window.minimized,
		"window_state": state.window_state}


func _facts_except(excluded: Array[String]) -> Dictionary:
	var facts := {}
	for window_id in desktop.windows:
		if window_id not in excluded:
			facts[window_id] = _window_fact(window_id)
	return facts


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "system-menu-desktop-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/system-menu-desktop-contracts.json",
		FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("SYSTEM MENU DESKTOP %d/%d passed" % [
		results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
