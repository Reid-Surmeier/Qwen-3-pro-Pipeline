extends SceneTree
## Real InputEvent contracts for the Issue #127 production Inventory Window.

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
	window = desktop.inventory
	_check("scene-valid", window != null and desktop.validation_errors.is_empty()
		and desktop.windows.size() == 3, str(desktop.validation_errors))
	await _tabs_reverse()
	await _single_and_double_activate()
	await _modifier_reverse_and_reject()
	await _drag_drop_and_rejections()
	await _resize_and_alignment()
	await _minimize_restore_resized()
	window.reset()
	await process_frame
	await _window_drag()
	await _escape_close()
	await _close()
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _tabs_reverse() -> void:
	await _click(Vector2(23, 788))
	var selected: Dictionary = window.qa_state().controls["inventory.tabs"]
	await _click(Vector2(23, 749))
	var restored: Dictionary = window.qa_state().controls["inventory.tabs"]
	_check("real-tabs-reverse", selected.value == "equip"
		and selected.last_action == "SelectInventoryTab"
		and restored.value == "item", str([selected, restored]))


func _single_and_double_activate() -> void:
	var first := Vector2(69, 761)
	var second := Vector2(123, 761)
	await _click(first)
	await create_timer(0.25).timeout
	var selected: Dictionary = window.qa_state().controls["inventory.items"]
	var log_before := window.runtime.interaction_log.size()
	await _click(second)
	await _double_click(second)
	await create_timer(0.25).timeout
	var opened: Dictionary = window.qa_state().controls["inventory.items"]
	var slice: Array = window.runtime.interaction_log.slice(log_before)
	var semantic := slice.filter(func(entry):
		return entry.get("control_id") == "inventory.items" \
			and entry.get("gesture") in ["Activate", "DoubleActivate"])
	_check("real-single-activate", selected.value == "r0c0"
		and selected.last_gesture == "Activate", str(selected))
	_check("real-double-exclusive", opened.opened_item == "r0c1"
		and opened.last_gesture == "DoubleActivate"
		and semantic.filter(func(entry): return entry.get("gesture") == "DoubleActivate").size() == 1
		and semantic.filter(func(entry): return entry.get("gesture") == "Activate").is_empty(),
		str([opened, semantic]))


func _modifier_reverse_and_reject() -> void:
	var point := Vector2(177, 761)
	await _click(point, true)
	var during: Array = window.qa_state().controls["inventory.items"].selected_items
	await _click(point, true)
	var after: Array = window.qa_state().controls["inventory.items"].selected_items
	var before_values: Dictionary = window.qa_state().controls["inventory.items"].item_values.duplicate(true)
	await _click(point, false, true)
	var rejected: Dictionary = window.qa_state().controls["inventory.items"]
	_check("real-modifier-reverse", "r0c2" in during and "r0c2" not in after,
		str([during, after]))
	_check("real-invalid-modifier", not rejected.last_result.accepted
		and rejected.last_result.error.code == "InvalidModifierError"
		and rejected.item_values == before_values, str(rejected))


func _drag_drop_and_rejections() -> void:
	var source := Vector2(69, 761)
	var target := Vector2(123, 761)
	var activate_before := _gesture_count("Activate")
	await _press(source)
	for index in 31:
		await _move(source.lerp(target, float(index + 1) / 31.0), true)
	await _release(target)
	var moved: Dictionary = window.qa_state().controls["inventory.items"]
	_check("real-drag-drop-once", moved.item_version == 1
		and moved.item_values.r0c0 == "r0c1" and moved.item_values.r0c1 == "r0c0"
		and moved.last_gesture == "DragDrop" and _gesture_count("Activate") == activate_before,
		str(moved))
	var values_before: Dictionary = moved.item_values.duplicate(true)
	await _press(source)
	for index in 31:
		await _move(source.lerp(Vector2(500, 900), float(index + 1) / 31.0), true)
	await _release(Vector2(500, 900))
	var invalid: Dictionary = window.qa_state().controls["inventory.items"]
	_check("real-invalid-drop-preserves", not invalid.last_result.accepted
		and invalid.last_result.error.code == "InvalidDropTargetError"
		and invalid.item_values == values_before and invalid.item_version == 1,
		str(invalid))
	var conflict := window.runtime.dispatch("inventory.items", "DragDrop",
		{"source": "r0c0", "target": "r0c1", "version": 0})
	var conflicted: Dictionary = window.qa_state().controls["inventory.items"]
	_check("stale-drag-conflict-preserves", not conflict.ok
		and conflict.error.code == "GestureConflictError"
		and conflicted.item_values == values_before and conflicted.item_version == 1,
		str([conflict, conflicted]))


func _resize_and_alignment() -> void:
	var start := Vector2(472, 992)
	await _press(start)
	for index in 31:
		await _move(start.lerp(start + Vector2(400, 400), float(index + 1) / 31.0), true)
	await _release(start + Vector2(400, 400))
	var maximum := window.qa_state()
	var aligned := _surfaces_aligned(maximum)
	_check("real-resize-max-clamp", maximum.window.size == [734.0, 512.0]
		and maximum.window.resize.motion_samples >= 30 and maximum.window.geometry_version == 1,
		str(maximum.window))
	_check("resized-grid-alignment", aligned, str(maximum.controls["inventory.items"].surface_geometry))
	var grip := window.get_node("ResizeGrip")
	var grip_rect: Rect2 = grip.get_global_rect()
	var grip_point := grip_rect.get_center()
	await _press(grip_point)
	for index in 31:
		await _move(grip_point.lerp(grip_point - Vector2(800, 800), float(index + 1) / 31.0), true)
	await _release(grip_point - Vector2(800, 800))
	var minimum: Dictionary = window.qa_state().window
	_check("real-resize-min-clamp", minimum.size == [332.0, 220.0]
		and minimum.resize.motion_samples >= 30 and minimum.geometry_version == 2,
		str(minimum))


func _minimize_restore_resized() -> void:
	var before: Dictionary = window.qa_state().window
	var minimize_geometry: Dictionary = window.qa_state().controls["inventory.minimize"].geometry
	await _click(Vector2(minimize_geometry.x + minimize_geometry.width / 2.0,
		minimize_geometry.y + minimize_geometry.height / 2.0))
	var minimized: Dictionary = window.qa_state().window
	minimize_geometry = window.qa_state().controls["inventory.minimize"].geometry
	await _click(Vector2(minimize_geometry.x + minimize_geometry.width / 2.0,
		minimize_geometry.y + minimize_geometry.height / 2.0))
	var restored: Dictionary = window.qa_state().window
	var restored_items: Dictionary = window.qa_state().controls["inventory.items"]
	_check("real-resized-minimize-restore", minimized.minimized
		and minimized.size == [484.0, 28.0] and not restored.minimized
		and restored.size == before.size and restored.position == before.position
		and restored.detail_item == before.detail_item and restored_items.detail_visible,
		str([before, minimized, restored, restored_items]))


func _window_drag() -> void:
	var start := Vector2(200, 710)
	var before: Array = window.qa_state().window.position
	await _press(start)
	await _move(start + Vector2(70, -80), true)
	await _release(start + Vector2(70, -80))
	var after: Array = window.qa_state().window.position
	_check("real-window-drag", after == [before[0] + 70.0, before[1] - 80.0],
		str([before, after]))


func _escape_close() -> void:
	var event := InputEventKey.new()
	event.keycode = KEY_ESCAPE
	event.pressed = true
	Input.parse_input_event(event)
	await process_frame
	var closed: Dictionary = window.qa_state().window
	_check("real-window-key-command", not closed.visible
		and closed.last_gesture == "KeyCommand" and closed.last_action == "CloseWindow",
		str(closed))
	window.reset()
	await process_frame


func _close() -> void:
	var state: Dictionary = window.qa_state().window
	await _click(Vector2(state.position[0] + 469, state.position[1] + 16))
	_check("real-close", not window.qa_state().window.visible, str(window.qa_state().window))


func _surfaces_aligned(state: Dictionary) -> bool:
	var origin := Vector2(state.window.position[0] + 42, state.window.position[1] + 30)
	for item in window.runtime.controls["inventory.items"].spec.surfaces:
		var local: Dictionary = window.runtime.controls["inventory.items"].spec.surfaces[item].geometry
		var actual: Dictionary = state.controls["inventory.items"].surface_geometry[item]
		if Vector2(actual.x, actual.y) != origin + Vector2(local.x, local.y):
			return false
	return true


func _gesture_count(gesture: String) -> int:
	return window.runtime.interaction_log.filter(func(entry):
		return entry.get("control_id") == "inventory.items" \
			and entry.get("gesture") == gesture).size()


func _double_click(point: Vector2) -> void:
	await _move(point, false)
	var event := InputEventMouseButton.new()
	event.position = point
	event.global_position = point
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.double_click = true
	Input.parse_input_event(event)
	await process_frame
	await _release(point)


func _click(point: Vector2, ctrl := false, alt := false) -> void:
	await _press(point, ctrl, alt)
	await _release(point, ctrl, alt)


func _press(point: Vector2, ctrl := false, alt := false) -> void:
	await _move(point, false)
	var event := InputEventMouseButton.new()
	event.position = point
	event.global_position = point
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = true
	event.ctrl_pressed = ctrl
	event.alt_pressed = alt
	Input.parse_input_event(event)
	await process_frame


func _release(point: Vector2, ctrl := false, alt := false) -> void:
	var event := InputEventMouseButton.new()
	event.position = point
	event.global_position = point
	event.button_index = MOUSE_BUTTON_LEFT
	event.pressed = false
	event.ctrl_pressed = ctrl
	event.alt_pressed = alt
	Input.parse_input_event(event)
	await process_frame


func _move(point: Vector2, held: bool) -> void:
	var event := InputEventMouseMotion.new()
	event.position = point
	event.global_position = point
	event.button_mask = MOUSE_BUTTON_MASK_LEFT if held else 0
	Input.parse_input_event(event)
	await process_frame


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "inventory-real-input", "total": results.size(),
		"failed": failed.size(), "results": results}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/inventory-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("INVENTORY REAL INPUT %d/%d passed" % [results.size() - failed.size(), results.size()])
