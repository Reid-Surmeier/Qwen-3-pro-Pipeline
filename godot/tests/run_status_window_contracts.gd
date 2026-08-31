extends SceneTree
## Issue #131 real-input Window contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlWindow = preload("res://control_library/control_window.gd")
const Desktop = preload("res://scripts/image79_desktop.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(
		func(window): return window.get("id") == "status")
	if matches.is_empty():
		_check("status-window-constructs", false, "manifest absent")
		_finish()
		return
	var window = ControlWindow.new()
	window.configure(matches[0])
	get_root().add_child(window)
	await process_frame
	var idle := window.qa_state()
	_check("status-window-constructs", idle.window.size == [484.0, 208.0]
		and idle.window_state.version == 0
		and idle.controls["status.attribute.str"].rendered
		and idle.controls["status.attribute.int"].semantic_state == "disabled",
		str(idle))
	var int_controls: Array = matches[0].controls.filter(
		func(control): return control.get("id") == "status.attribute.int")
	var int_disabled: Dictionary = int_controls[0].surfaces.increment.state_set.disabled
	_check("disabled-stepper-has-transient-feedback", str(int_disabled.idle).ends_with(
		"transparent.png") and not str(int_disabled.hover).ends_with("transparent.png")
		and not str(int_disabled.pressed).ends_with("transparent.png"), str(int_disabled))
	var minimized: Dictionary = window.runtime.dispatch("status.minimize", "Activate", {})
	window._control_changed("status.minimize", minimized)
	var mini: Dictionary = window.qa_state().window
	window._control_changed("status.minimize",
		window.runtime.dispatch("status.minimize", "Activate", {}))
	_check("purpose-built-minimize-restores", mini.minimized
		and mini.size == [484.0, 28.0]
		and window.qa_state().window.size == [484.0, 208.0], str(mini))
	window.queue_free()
	await process_frame
	get_root().size = Vector2i(1973, 1319)
	var desktop := Desktop.new()
	desktop.set_meta("suppress_publish", true)
	get_root().add_child(desktop)
	await process_frame
	var initial := desktop.qa_state()
	_check("assembled-seven-window-state", initial.windows.has("status")
		and initial.windows.size() == 7 and desktop.status != null, str(initial.keys()))
	if desktop.status == null:
		desktop.queue_free()
		_finish()
		return
	var arrow: Dictionary = initial.windows.status.controls[
		"status.attribute.str"].surface_geometry.increment
	var center := Vector2(float(arrow.x) + float(arrow.width) / 2.0,
		float(arrow.y) + float(arrow.height) / 2.0)
	await _click(center, MOUSE_BUTTON_LEFT)
	await _click(center, MOUSE_BUTTON_LEFT)
	var exhausted: Dictionary = desktop.status.qa_state()
	await _click(center, MOUSE_BUTTON_LEFT)
	var rejected: Dictionary = desktop.status.qa_state()
	_check("real-rapid-clicks-exhaust-and-preserve", exhausted.window_state.points == 0
		and exhausted.window_state.version == 2
		and rejected.window_state == exhausted.window_state
		and rejected.controls["status.attribute.str"].last_error.code \
			== "TransactionRejectedError", str([exhausted, rejected]))
	await _click(center, MOUSE_BUTTON_RIGHT)
	var reversed: Dictionary = desktop.status.qa_state()
	_check("real-right-click-reverses-in-one-frame", reversed.window_state.version == 3
		and reversed.window_state.points == 2
		and reversed.window_state.attributes["status.attribute.str"].base == 2
		and reversed.window_state.derived.Atk == 64
		and reversed.controls["status.attribute.str"].semantic_state == "available"
		and reversed.status_overlay.visible, str(reversed))
	desktop.queue_free()
	_finish()


func _click(point: Vector2, button: MouseButton) -> void:
	var move := InputEventMouseMotion.new()
	move.position = point
	move.global_position = point
	Input.parse_input_event(move)
	await process_frame
	var press := InputEventMouseButton.new()
	press.position = point
	press.global_position = point
	press.button_index = button
	press.pressed = true
	Input.parse_input_event(press)
	await process_frame
	var release := InputEventMouseButton.new()
	release.position = point
	release.global_position = point
	release.button_index = button
	release.pressed = false
	Input.parse_input_event(release)
	await process_frame


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "status-window-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/status-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("STATUS WINDOW %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
