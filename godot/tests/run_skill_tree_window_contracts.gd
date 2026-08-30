extends SceneTree
## Real InputEvent contracts for the Issue #126 production Skill Tree Window.

var results: Array[Dictionary] = []
var desktop: Control
var window: ControlWindow
const STEPPER_IDS := [
	"skill_tree.stepper.r1c1", "skill_tree.stepper.r1c3", "skill_tree.stepper.r1c4",
	"skill_tree.stepper.r1c5", "skill_tree.stepper.r1c6", "skill_tree.stepper.r2c1",
	"skill_tree.stepper.r2c2", "skill_tree.stepper.r2c3", "skill_tree.stepper.r2c4",
	"skill_tree.stepper.r2c5", "skill_tree.stepper.r3c1", "skill_tree.stepper.r3c2",
	"skill_tree.stepper.r3c3", "skill_tree.stepper.r3c4", "skill_tree.stepper.r3c5",
	"skill_tree.stepper.r3c6", "skill_tree.stepper.r4c1", "skill_tree.stepper.r4c2",
	"skill_tree.stepper.r4c3", "skill_tree.stepper.r4c4", "skill_tree.stepper.r4c5",
	"skill_tree.stepper.r4c6", "skill_tree.stepper.r5c1", "skill_tree.stepper.r5c3",
	"skill_tree.stepper.r5c4", "skill_tree.stepper.r5c5",
]


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	# Match the project viewport so injected global pointer coordinates resolve
	# through the same stretch transform as the production scene.
	get_root().size = Vector2i(1973, 1319)
	change_scene_to_file("res://image79_options.tscn")
	await process_frame
	await process_frame
	desktop = current_scene
	window = desktop.skill_tree
	_check("scene-valid", window != null and desktop.validation_errors.is_empty()
		and desktop.windows.size() == 2, str(desktop.validation_errors))
	await _selection_and_context_activate()
	await _step_commit_cancel()
	await _view_reversal()
	await _description_toggle_reversal()
	await _minimize_restore()
	await _window_drag()
	await _close()
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _selection_and_context_activate() -> void:
	var point := Vector2(757, 87)
	await _click(point, MOUSE_BUTTON_LEFT)
	var selected: Dictionary = window.qa_state().controls["skill_tree.skills"]
	await _click(point, MOUSE_BUTTON_RIGHT)
	var detailed: Dictionary = window.qa_state().controls["skill_tree.skills"]
	var window_state: Dictionary = window.qa_state().window
	_check("real-selection", selected.value == "r1c3"
		and selected.last_gesture == "Activate" and selected.last_action == "SelectSkill",
		str(selected))
	_check("real-context-activate", detailed.last_gesture == "ContextActivate"
		and detailed.last_action == "OpenSkillDetail"
		and window_state.detail_item == "r1c3" and detailed.detail_visible
		and detailed.detail_text == "ヒール\n10 / 10",
		str([detailed, window_state]))


func _step_commit_cancel() -> void:
	# Reversing the view dismisses the context panel before rendered-pixel checks.
	await _click(Vector2(1048, 15), MOUSE_BUTTON_LEFT)
	await _click(Vector2(1048, 15), MOUSE_BUTTON_LEFT)
	var stepper_id := "skill_tree.stepper.r2c4"
	var increment := Vector2(887, 220)
	await _click(increment, MOUSE_BUTTON_LEFT)
	var pending: Dictionary = window.qa_state()
	var all_hidden := true
	for control_id in STEPPER_IDS:
		all_hidden = all_hidden and not bool(pending.controls[control_id].arrows_visible) \
			and pending.controls[control_id].rendered_arrow_visibility.values().all(
				func(visible): return not visible)
	_check("real-stepper-pending", pending.window.pending and all_hidden
		and pending.controls[stepper_id].text == "0 / 6", str(pending.controls[stepper_id]))
	_check("real-stepper-pending-has-no-rendered-arrows",
		all_hidden, str(pending.controls[stepper_id].rendered_arrow_visibility))

	await _click(Vector2(957, 569), MOUSE_BUTTON_LEFT)
	var committed: Dictionary = window.qa_state()
	_check("real-stepper-commit", not committed.window.pending
		and committed.controls[stepper_id].current == 6
		and committed.controls[stepper_id].target == 6
		and committed.controls[stepper_id].arrows_visible,
		str(committed.controls[stepper_id]))
	var restored_arrow_pixels: Array[int] = []
	for control_id in STEPPER_IDS:
		restored_arrow_pixels.append_array(
			Array(committed.controls[control_id].rendered_arrow_pixels.values()))
	_check("real-stepper-restores-complete-arrows",
		not restored_arrow_pixels.is_empty() and restored_arrow_pixels.min() >= 12,
		str(restored_arrow_pixels))

	var max_id := "skill_tree.stepper.r1c3"
	var max_before: Dictionary = window.qa_state().controls[max_id].duplicate(true)
	await _click(Vector2(793, 120), MOUSE_BUTTON_LEFT)
	var max_after: Dictionary = window.qa_state().controls[max_id]
	_check("real-stepper-bound-rejected", not max_after.last_result.accepted
		and max_after.last_result.error.code == "TransactionRejectedError"
		and max_after.target == max_before.target and not window.qa_state().window.pending,
		str(max_after))

	await _click(increment, MOUSE_BUTTON_LEFT)
	await _click(Vector2(1046, 569), MOUSE_BUTTON_LEFT)
	var cancelled: Dictionary = window.qa_state()
	_check("real-stepper-cancel", not cancelled.window.pending
		and cancelled.controls[stepper_id].current == 6
		and cancelled.controls[stepper_id].target == 6,
		str(cancelled.controls[stepper_id]))


func _view_reversal() -> void:
	var point := Vector2(1048, 15)
	await _click(point, MOUSE_BUTTON_LEFT)
	var list_state: Dictionary = window.qa_state()
	await _click(point, MOUSE_BUTTON_LEFT)
	var tree_state: Dictionary = window.qa_state()
	_check("real-view-reversal", list_state.window.view_mode == "list"
		and list_state.controls["skill_tree.skills"].list_mode
		and list_state.controls["skill_tree.skills"].list_values["r2c4"] == "6 / 6"
		and str(list_state.controls["skill_tree.skills"].list_labels["r2c4"]).ends_with("6 / 6")
		and tree_state.window.view_mode == "tree"
		and not tree_state.controls["skill_tree.skills"].list_mode,
		str([list_state.window, tree_state.window]))


func _description_toggle_reversal() -> void:
	var point := Vector2(758, 19)
	var before := str(window.qa_state().controls["skill_tree.descriptions"].semantic_state)
	await _click(point, MOUSE_BUTTON_LEFT)
	var during := str(window.qa_state().controls["skill_tree.descriptions"].semantic_state)
	await _click(point, MOUSE_BUTTON_LEFT)
	var after := str(window.qa_state().controls["skill_tree.descriptions"].semantic_state)
	_check("real-description-reversal", before == "off" and during == "on" and after == before,
		str([before, during, after]))


func _minimize_restore() -> void:
	var point := Vector2(503, 12)
	var before: Dictionary = window.qa_state().window
	await _click(point, MOUSE_BUTTON_LEFT)
	var minimized: Dictionary = window.qa_state().window
	await _click(point, MOUSE_BUTTON_LEFT)
	var restored: Dictionary = window.qa_state().window
	_check("real-distinct-minimize-restore", minimized.minimized
		and minimized.size == [611.0, 28.0] and not restored.minimized
		and restored.size == [611.0, 595.0] and restored.position == before.position,
		str([before, minimized, restored]))


func _window_drag() -> void:
	var start := Vector2(620, 14)
	var target := start + Vector2(-60, 70)
	var before: Array = window.qa_state().window.position
	await _press(start, MOUSE_BUTTON_LEFT)
	await _move(target, true)
	await _release(target, MOUSE_BUTTON_LEFT)
	var after: Array = window.qa_state().window.position
	_check("real-window-drag", is_equal_approx(after[0], before[0] - 60.0)
		and is_equal_approx(after[1], before[1] + 70.0), str([before, after]))


func _close() -> void:
	var state: Dictionary = window.qa_state().window
	await _click(Vector2(state.position[0] + 598, state.position[1] + 15), MOUSE_BUTTON_LEFT)
	_check("real-close", not window.qa_state().window.visible, str(window.qa_state().window))


func _click(point: Vector2, button: MouseButton) -> void:
	await _press(point, button)
	await _release(point, button)


func _press(point: Vector2, button: MouseButton) -> void:
	await _move(point, false)
	var event := InputEventMouseButton.new()
	event.position = point
	event.global_position = point
	event.button_index = button
	event.pressed = true
	Input.parse_input_event(event)
	await process_frame


func _release(point: Vector2, button: MouseButton) -> void:
	var event := InputEventMouseButton.new()
	event.position = point
	event.global_position = point
	event.button_index = button
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


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "skill-tree-real-input", "total": results.size(),
		"failed": failed.size(), "results": results}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/skill-tree-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("SKILL TREE REAL INPUT %d/%d passed" % [results.size() - failed.size(), results.size()])
