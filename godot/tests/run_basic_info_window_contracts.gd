extends SceneTree
## Issue #132 real-input Window and destination contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlWindow = preload("res://control_library/control_window.gd")
const Desktop = preload("res://scripts/image79_desktop.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(
		func(window): return window.get("id") == "basic_info")
	if matches.is_empty():
		_check("basic-info-window-constructs", false, "manifest absent")
		_finish()
		return
	var window = ControlWindow.new()
	window.configure(matches[0])
	get_root().add_child(window)
	await process_frame
	var idle := window.qa_state()
	_check("basic-info-window-constructs", idle.window.size == [484.0, 205.0]
		and idle.display_facts.size() == 10
		and idle.controls["basic_info.meter.hp"].rendered
		and str(idle.controls["basic_info.meter.hp"].rendered_asset).ends_with(
			"meter-hp-idle.png")
		and int(idle.controls["basic_info.meter.hp"].rendered_texture_size[0]) == 151
		and int(idle.controls["basic_info.meter.hp"].rendered_texture_size[1]) == 15
		and is_equal_approx(float(idle.controls["basic_info.meter.hp"].ratio),
			1.0), str(idle))
	window._control_changed("basic_info.minimize",
		window.runtime.dispatch("basic_info.minimize", "Activate", {}))
	var mini := window.qa_state()
	window._control_changed("basic_info.minimize",
		window.runtime.dispatch("basic_info.minimize", "Activate", {}))
	var restored := window.qa_state()
	_check("purpose-built-minimize-restores", mini.window.minimized
		and mini.window.size == [484.0, 28.0]
		and not restored.window.minimized and restored.window.size == [484.0, 205.0]
		and restored.controls["basic_info.meter.hp"].current == 1109.0,
		str([mini.window, restored.window]))
	window.queue_free()
	await process_frame

	get_root().size = Vector2i(1536, 1024)
	var desktop := Desktop.new()
	desktop.set_meta("suppress_publish", true)
	get_root().add_child(desktop)
	await process_frame
	var initial := desktop.qa_state()
	_check("assembled-eleven-window-state", initial.windows.size() == 11
		and desktop.basic_info != null and initial.windows.has("basic_info"),
		str(initial.windows.keys()))
	if desktop.basic_info == null:
		desktop.queue_free()
		_finish()
		return
	desktop.basic_info.move_to_front()
	desktop.status.visible = false
	var target_semantic_before: Dictionary = desktop.status.runtime.qa_state()
	var destination_result: Dictionary = desktop.basic_info.runtime.dispatch(
		"basic_info.destination.status", "Activate", {})
	desktop.basic_info._control_changed("basic_info.destination.status", destination_result)
	_check("real-destination-opens-and-raises", desktop.status.visible
		and desktop.get_children().back() == desktop.status
		and desktop.last_transaction.get("ok", false)
		and desktop.last_transaction.target_window == "status"
		and desktop.last_transaction.position_before \
			== desktop.last_transaction.position_after
		and desktop.status.runtime.qa_state() == target_semantic_before,
		str(desktop.last_transaction))
	var before: Dictionary = desktop.qa_state().windows.duplicate(true)
	var unavailable_result: Dictionary = desktop.basic_info.runtime.dispatch(
		"basic_info.destination.map", "Activate", {})
	desktop.basic_info._control_changed("basic_info.destination.map", unavailable_result)
	var after := desktop.qa_state()
	_check("unavailable-destination-rejects-atomically",
		after.windows.basic_info.controls["basic_info.destination.map"].last_error.code \
			== "ActionRoutingError"
		and desktop.last_transaction.error.code == "ActionRoutingError"
		and after.windows.status.window.position == before.status.window.position,
		str(after.windows.basic_info.controls["basic_info.destination.map"]))
	desktop.queue_free()
	_finish()


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


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "basic-info-window-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/basic-info-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("BASIC INFO WINDOW %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
