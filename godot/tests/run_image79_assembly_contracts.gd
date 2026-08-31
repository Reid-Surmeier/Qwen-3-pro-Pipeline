extends SceneTree
## Issue #136 complete Assembly, reset, stack, and idle-work contracts.

const Desktop = preload("res://scripts/image79_desktop.gd")

var results: Array[Dictionary] = []
var desktop: Control


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	get_root().size = Vector2i(1536, 1024)
	desktop = Desktop.new()
	get_root().add_child(desktop)
	await process_frame
	await process_frame
	var initial: Dictionary = desktop.qa_state()
	_check("complete-eleven-window-reset",
		initial.windows.size() == 11
		and initial.windows.values().all(func(state):
			return state.window.visible and not state.window.minimized), str(initial))
	_check("idle-windows-do-no-frame-work",
		initial.windows.values().all(func(state):
			return not state.window.process_active), str(initial.windows))
	_check("stack-facts-are-unique-and-ordered",
		_unique_stack(initial) and initial.windows.basic_info.window.stack_index
		< initial.windows.status.window.stack_index, str(_stack(initial)))

	var original_stack := _stack(initial)
	desktop.options.move_to_front()
	await process_frame
	var raised: Dictionary = desktop.qa_state()
	_check("pointer-raise-stack-is-factual",
		raised.windows.options.window.stack_index == _max_stack(raised)
		and _stack(raised) != original_stack, str(_stack(raised)))

	desktop.options.position = Vector2(600, 500)
	desktop.options.visible = false
	desktop.status.position = Vector2(700, 600)
	desktop.reset()
	await process_frame
	var reset_state: Dictionary = desktop.qa_state()
	_check("desktop-reset-restores-position-visibility-and-stack",
		reset_state.windows.options.window.position == [1108.0, 297.0]
		and reset_state.windows.options.window.visible
		and reset_state.windows.status.window.position == [0.0, 211.0]
		and _stack(reset_state) == original_stack, str(reset_state))

	desktop.queue_free()
	_finish()


func _stack(state: Dictionary) -> Dictionary:
	var result := {}
	for window_id in state.windows:
		result[window_id] = state.windows[window_id].window.get("stack_index", -1)
	return result


func _unique_stack(state: Dictionary) -> bool:
	var values: Array = _stack(state).values()
	var unique := {}
	for value in values:
		unique[value] = true
	return values.size() == unique.size()


func _max_stack(state: Dictionary) -> int:
	var maximum := -1
	for value in _stack(state).values():
		maximum = maxi(maximum, int(value))
	return maximum


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "image79-assembly-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/image79-assembly-contracts.json",
		FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("IMAGE79 ASSEMBLY %d/%d passed" % [
		results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
