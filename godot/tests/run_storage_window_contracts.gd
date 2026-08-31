extends SceneTree
## Real InputEvent contracts for the Issue #128 production Storage Window.

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
	window = desktop.storage
	_check("scene-valid", window != null and desktop.validation_errors.is_empty()
		and desktop.windows.size() == 4, str(desktop.validation_errors))
	await _adapter_click(window.control_nodes["storage.categories"], "_tab_input",
		"equipment", Vector2(537, 704))
	_check("real-category", window.qa_state().controls["storage.categories"].value == "equipment",
		str(window.qa_state().controls["storage.categories"]))
	await _adapter_wheel(window.control_nodes["storage.scroll"], "track", 1,
		Vector2(1007, 800))
	_check("real-wheel-three", window.qa_state().controls["storage.scroll"].offset == 3,
		str(window.qa_state().controls["storage.scroll"]))
	await _adapter_click(window.control_nodes["storage.scroll"], "_surface_input",
		"increment", Vector2(1007, 946))
	_check("real-arrow-one", window.qa_state().controls["storage.scroll"].offset == 4,
		str(window.qa_state().controls["storage.scroll"]))
	await _scroll_drag(Vector2(1007, 850), Vector2(1007, 700), 17)
	var dragged: Dictionary = window.qa_state().controls["storage.scroll"]
	_check("real-thumb-continuous", dragged.offset < 4 and dragged.offset >= 0,
		str(dragged))
	window.control_nodes["storage.search"].focus_field()
	await process_frame
	await _type_text("Potion 70")
	var searched: Dictionary = window.qa_state()
	_check("real-text-filter", searched.controls["storage.search"].rendered_text == "Potion 70"
		and searched.controls["storage.items"].filtered_items.size() == 1
		and searched.controls["storage.scroll"].offset == 0, str(searched.controls))
	await _adapter_click(window.control_nodes["storage.list"], "_on_gui_input", "",
		Vector2(632, 977))
	_check("real-list-mode", window.qa_state().window.view_mode == "list"
		and window.qa_state().controls["storage.items"].list_mode,
		str(window.qa_state().window))
	await _adapter_click(window.control_nodes["storage.sort"], "_on_gui_input", "",
		Vector2(878, 977))
	_check("real-sort", not window.qa_state().controls["storage.items"].sort_ascending,
		str(window.qa_state().controls["storage.items"]))
	await _adapter_click(window.control_nodes["storage.list"], "_on_gui_input", "",
		Vector2(632, 977))
	_check("real-list-mode-reverses", window.qa_state().window.view_mode == "tree",
		str(window.qa_state().window))
	window.control_nodes["storage.search"].field.text = ""
	await process_frame
	var storage_before: Dictionary = window.runtime.selection_collection("storage.items")
	var inventory_before: Dictionary = desktop.inventory.runtime.selection_collection("inventory.items")
	await _selection_modifier_double(window.control_nodes["storage.items"], "r0c0",
		Vector2(610, 670))
	_check("real-full-target-rejects-atomically", not desktop.last_transaction.get("ok", true)
		and desktop.last_transaction.get("error", {}).get("code") == "TransactionRejectedError"
		and window.runtime.selection_collection("storage.items") == storage_before
		and desktop.inventory.runtime.selection_collection("inventory.items") == inventory_before,
		str(desktop.last_transaction))
	await _selection_modifier_double(desktop.inventory.control_nodes["inventory.items"],
		"r0c0", Vector2(69, 761))
	var outbound: Dictionary = desktop.last_transaction
	_check("real-inventory-to-storage-commits", outbound.get("ok", false)
		and outbound.source_window == "inventory" and outbound.target_window == "storage"
		and outbound.source_version_after == outbound.source_version_before + 1
		and outbound.target_version_after == outbound.target_version_before + 1,
		str(outbound))
	window.control_nodes["storage.search"].field.text = "r0c0"
	await process_frame
	await _selection_modifier_double(window.control_nodes["storage.items"], "r0c0",
		Vector2(610, 670))
	var returned: Dictionary = desktop.last_transaction
	_check("real-storage-to-inventory-commits", returned.get("ok", false)
		and returned.source_window == "storage" and returned.target_window == "inventory",
		str(returned))
	await _window_drag(Vector2(700, 620), Vector2(760, 580), 12)
	_check("real-window-drag", window.qa_state().window.position == [552.0, 569.0],
		str(window.qa_state().window))
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _selection_modifier_double(node: Control, item: String, point: Vector2) -> void:
	for click_index in 2:
		var press := InputEventMouseButton.new()
		press.button_index = MOUSE_BUTTON_LEFT
		press.pressed = true
		press.double_click = click_index == 1
		press.ctrl_pressed = true
		press.position = point
		press.global_position = point
		node._item_input(press, item)
		await process_frame
		var release := press.duplicate()
		release.pressed = false
		node._item_input(release, item)
		await process_frame


func _adapter_click(node: Control, method: String, surface: String, point: Vector2) -> void:
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = point
	press.global_position = point
	if surface.is_empty():
		node.call(method, press)
	else:
		node.call(method, press, surface)
	await process_frame
	var release := press.duplicate()
	release.pressed = false
	if surface.is_empty():
		node.call(method, release)
	else:
		node.call(method, release, surface)
	await process_frame


func _adapter_wheel(node: Control, surface: String, direction: int,
		point: Vector2) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = MOUSE_BUTTON_WHEEL_DOWN if direction > 0 else MOUSE_BUTTON_WHEEL_UP
	event.pressed = true
	event.position = point
	event.global_position = point
	node._surface_input(event, surface)
	await process_frame


func _scroll_drag(start: Vector2, finish: Vector2, samples: int) -> void:
	var node: Control = window.control_nodes["storage.scroll"]
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = start
	press.global_position = start
	node._surface_input(press, "thumb")
	await process_frame
	for index in samples:
		var point := start.lerp(finish, float(index + 1) / float(samples))
		var motion := InputEventMouseMotion.new()
		motion.button_mask = MOUSE_BUTTON_MASK_LEFT
		motion.position = point
		motion.global_position = point
		node._input(motion)
		await process_frame
	var release := press.duplicate()
	release.pressed = false
	release.position = finish
	release.global_position = finish
	node._input(release)
	await process_frame


func _window_drag(start: Vector2, finish: Vector2, samples: int) -> void:
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = start - window.position
	press.global_position = start
	window._title_input(press)
	await process_frame
	for index in samples:
		var point := start.lerp(finish, float(index + 1) / float(samples))
		var motion := InputEventMouseMotion.new()
		motion.button_mask = MOUSE_BUTTON_MASK_LEFT
		motion.position = point - window.position
		motion.global_position = point
		window._title_input(motion)
		await process_frame
	var release := press.duplicate()
	release.pressed = false
	release.position = finish - window.position
	release.global_position = finish
	window._title_input(release)
	await process_frame


func _type_text(value: String) -> void:
	for character in value:
		var event := InputEventKey.new()
		event.pressed = true
		event.unicode = character.unicode_at(0)
		Input.parse_input_event(event)
		await process_frame


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/storage-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"suite": "storage-window", "total": results.size(),
		"failed": failed.size(), "results": results}, "  "))
	file.close()
	print("STORAGE REAL INPUT %d/%d passed" % [results.size() - failed.size(), results.size()])
