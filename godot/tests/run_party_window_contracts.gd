extends SceneTree
## Issue #133 rendered Party Window and real-input contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlWindow = preload("res://control_library/control_window.gd")

var results: Array[Dictionary] = []
var window: ControlWindow


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	# Match the project viewport so source-native global pointer coordinates
	# resolve through the production stretch transform.
	get_root().size = Vector2i(1973, 1319)
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(
		func(candidate): return candidate.get("id") == "party")
	if matches.is_empty():
		_check("party-window-constructs", false, "manifest absent")
		_finish()
		return
	window = ControlWindow.new()
	window.configure(matches[0])
	get_root().add_child(window)
	await process_frame
	var idle := window.qa_state()
	_check("party-window-constructs", idle.window.position == [1107.0, 505.0]
		and idle.window.size == [215.0, 269.0]
		and idle.controls.size() == 13 and idle.display_facts.size() == 10
		and not idle.party_overlay.visible
		and idle.controls["party.members"].visible_item_count == 5
		and idle.controls["party.meter.sakumariri"].rendered_texture_size == [88, 5],
		str(idle))

	await _click(Vector2(1120, 758))
	var friends := window.qa_state()
	_check("real-friends-mode-one-frame", friends.window_state.mode == "friends"
		and friends.window_state.version == 1 and friends.party_overlay.visible
		and friends.controls["party.members"].visible_item_count == 0
		and friends.controls["party.action.leave"].semantic_state == "disabled",
		str(friends))
	await _click(Vector2(1210, 758))
	var party := window.qa_state()
	_check("real-party-mode-restores-one-frame", party.window_state.mode == "party"
		and party.window_state.version == 2 and not party.party_overlay.visible
		and party.controls["party.members"].visible_item_count == 5,
		str(party))

	await _click(Vector2(1200, 655))
	var selected := window.qa_state()
	_check("real-member-selection", selected.window_state.version == 3
		and selected.window_state.selected_member == "show_a"
		and selected.controls["party.members"].selected_item == "show_a",
		str(selected.controls["party.members"]))

	var before_unavailable := JSON.stringify(selected.window_state)
	await _click(Vector2(1237, 729))
	var unavailable := window.qa_state()
	var unavailable_error: Variant = unavailable.controls[
		"party.action.search"].last_error
	_check("real-unavailable-icon-rejection", not unavailable.controls[
		"party.action.search"].last_result.accepted
		and unavailable_error is Dictionary \
		and unavailable_error.get("code") == "ActionRoutingError"
		and JSON.stringify(unavailable.window_state) == before_unavailable,
		str([unavailable.controls["party.action.search"], unavailable.interaction_log]))

	await _click(Vector2(1272, 729))
	var left := window.qa_state()
	var repeat_before := JSON.stringify(left.window_state)
	await _click(Vector2(1272, 729))
	var repeated := window.qa_state()
	var repeated_error: Variant = repeated.controls["party.action.leave"].last_error
	_check("real-leave-and-repeat", left.window_state.version == 4
		and left.window_state.membership == "none" and left.party_overlay.visible
		and left.controls["party.members"].visible_item_count == 0
		and left.controls["party.action.leave"].semantic_state == "disabled"
		and repeated_error is Dictionary \
		and repeated_error.get("code") == "TransactionRejectedError"
		and JSON.stringify(repeated.window_state) == repeat_before,
		str([left, repeated.controls["party.action.leave"]]))

	window.reset()
	await process_frame
	var before_drag: Array = window.qa_state().window.position
	await _press(Vector2(1160, 515))
	await _move(Vector2(1080, 435), true)
	await _release(Vector2(1080, 435))
	var after_drag: Array = window.qa_state().window.position
	_check("real-window-drag", after_drag == [before_drag[0] - 80.0,
		before_drag[1] - 80.0], str([before_drag, after_drag]))

	var escape := InputEventKey.new()
	escape.keycode = KEY_ESCAPE
	escape.pressed = true
	Input.parse_input_event(escape)
	await process_frame
	var closed: Dictionary = window.qa_state().window
	_check("real-window-key-command", not closed.visible
		and closed.last_gesture == "KeyCommand" and closed.last_action == "CloseWindow",
		str(closed))
	window.reset()
	await process_frame
	var position: Array = window.qa_state().window.position
	await _click(Vector2(position[0] + 200, position[1] + 11))
	_check("real-close", not window.qa_state().window.visible,
		str(window.qa_state().window))
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
	var report := {"suite": "party-window-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/party-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("PARTY WINDOW %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
