extends SceneTree
## Real adapter/desktop contract for Issue #130.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlWindow = preload("res://control_library/control_window.gd")
const Desktop = preload("res://scripts/image79_desktop.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(func(window):
		return window.get("id") == "equipment_items")
	if matches.is_empty():
		_check("equipment-window-constructs", false, "manifest absent")
		_finish()
		return
	var window: ControlWindow = ControlWindow.new()
	window.configure(matches[0])
	get_root().add_child(window)
	await process_frame
	var idle := window.qa_state()
	_check("equipment-window-constructs", idle.window.size == [484.0, 271.0]
		and idle.controls["equipment_items.slots"].surface_geometry.size() == 9,
		str(idle))
	var minimized := window.runtime.dispatch("equipment_items.minimize", "Activate", {})
	window._control_changed("equipment_items.minimize", minimized)
	var mini: Dictionary = window.qa_state().window
	window._control_changed("equipment_items.minimize",
		window.runtime.dispatch("equipment_items.minimize", "Activate", {}))
	_check("purpose-built-minimize-restores", mini.minimized and mini.size == [484.0, 28.0]
		and window.qa_state().window.size == [484.0, 271.0], str(mini))
	window.queue_free()
	await process_frame
	get_root().size = Vector2i(1973, 1319)
	var desktop := Desktop.new()
	desktop.set_meta("suppress_publish", true)
	get_root().add_child(desktop)
	await process_frame
	var initial := desktop.qa_state()
	_check("assembled-six-window-state", initial.windows.has("equipment_items")
		and initial.windows.has("inventory") and initial.windows.has("equipment_card"), str(initial.keys()))
	var before_inventory: Dictionary = initial.windows.inventory.controls["inventory.items"]
	var before_equipment: Dictionary = initial.windows.equipment_items.controls["equipment_items.slots"]
	var inventory_point := _center(before_inventory.surface_geometry.r0c0)
	var equipment_point := _center(before_equipment.surface_geometry.head)
	var drag_feedback: Dictionary = await _drag_between(inventory_point, equipment_point, desktop)
	var after_inventory: Dictionary = desktop.inventory.runtime.qa_state().controls["inventory.items"]
	var after_equipment: Dictionary = desktop.equipment_items.runtime.qa_state().controls["equipment_items.slots"]
	var rendered_after_equip: Dictionary = desktop.qa_state()
	_check("real-cross-window-equip-displacement", desktop.last_transaction.get("ok", false)
		and drag_feedback.source.motion_samples >= 31
		and drag_feedback.source.source == "r0c0"
		and drag_feedback.target.target == "head"
		and after_inventory.item_version == before_inventory.item_version + 1
		and after_equipment.item_version == before_equipment.item_version + 1
		and after_inventory.item_values.r0c0 == before_equipment.item_values.head
		and after_equipment.item_values.head == before_inventory.item_values.r0c0
		and str(rendered_after_equip.windows.inventory.controls["inventory.items"]
			.rendered_foreign_identity_assets.r0c0).contains("slot-head-unselected-idle")
		and str(rendered_after_equip.windows.equipment_items.controls["equipment_items.slots"]
			.rendered_foreign_identity_assets.head).contains("cell-r0c0-unselected-idle")
		and rendered_after_equip.windows.inventory.controls["inventory.items"]
			.rendered_foreign_identity_visibility.r0c0
		and rendered_after_equip.windows.equipment_items.controls["equipment_items.slots"]
			.rendered_foreign_identity_visibility.head,
		str([desktop.last_transaction, drag_feedback]))
	var reverse_feedback: Dictionary = await _drag_between(equipment_point, inventory_point, desktop)
	var restored_inventory: Dictionary = desktop.inventory.runtime.qa_state().controls["inventory.items"]
	var restored_equipment: Dictionary = desktop.equipment_items.runtime.qa_state().controls["equipment_items.slots"]
	_check("real-cross-window-unequip-reverses", desktop.last_transaction.get("ok", false)
		and desktop.last_transaction.operation == "unequip"
		and reverse_feedback.source.motion_samples >= 31
		and restored_inventory.item_values == before_inventory.item_values
		and restored_equipment.item_values == before_equipment.item_values
		and restored_inventory.item_version == before_inventory.item_version + 2
		and restored_equipment.item_version == before_equipment.item_version + 2,
		str([desktop.last_transaction, reverse_feedback]))
	var rejection_inventory: Dictionary = restored_inventory.item_values.duplicate(true)
	var rejection_equipment: Dictionary = restored_equipment.item_values.duplicate(true)
	await _drag_between(inventory_point, Vector2(200.0, 435.0), desktop)
	_check("real-invalid-drop-rejects-and-preserves-both",
		not desktop.last_transaction.get("ok", false)
		and desktop.last_transaction.error.code == "TransactionRejectedError"
		and desktop.inventory.runtime.qa_state().controls[
			"inventory.items"].item_values == rejection_inventory
		and desktop.equipment_items.runtime.qa_state().controls[
			"equipment_items.slots"].item_values == rejection_equipment
		and desktop.inventory.runtime.qa_state().controls[
			"inventory.items"].interaction_phase == "idle"
		and desktop.inventory.runtime.qa_state().controls[
			"inventory.items"].active_surface == "",
		str(desktop.last_transaction))
	var tab_result := desktop.inventory.runtime.dispatch("inventory.tabs", "Activate",
		{"choice": "equip"})
	desktop.inventory._control_changed("inventory.tabs", tab_result)
	var double_before_inventory: Dictionary = desktop.inventory.runtime.qa_state().controls[
		"inventory.items"]
	var double_before_equipment: Dictionary = desktop.equipment_items.runtime.qa_state().controls[
		"equipment_items.slots"]
	var double_result := desktop.inventory.runtime.dispatch("inventory.items",
		"DoubleActivate", {"item": "r0c0"})
	desktop.inventory._control_changed("inventory.items", double_result)
	var double_state: Dictionary = desktop.qa_state()
	_check("equip-tab-double-activate-owns-explicit-action",
		double_result.get("action") == "EquipInventoryItem"
		and desktop.last_transaction.get("ok", false)
		and double_state.windows.inventory.controls["inventory.items"].opened_item == ""
		and not double_state.windows.inventory.controls["inventory.items"].detail_visible
		and double_state.windows.inventory.controls["inventory.items"].item_version \
			== double_before_inventory.item_version + 1
		and double_state.windows.equipment_items.controls["equipment_items.slots"].item_version \
			== double_before_equipment.item_version + 1,
		str([double_result, desktop.last_transaction]))
	desktop._equipment_transaction("equip", "r0c0", "head")
	var displaced_inventory: Dictionary = desktop.inventory.runtime.qa_state().controls["inventory.items"]
	var displaced_equipment: Dictionary = desktop.equipment_items.runtime.qa_state().controls["equipment_items.slots"]
	var stale_inventory := int(displaced_inventory.item_version)
	var stale_equipment := int(displaced_equipment.item_version)
	desktop._equipment_transaction("unequip", "r0c1", "face")
	var preserved := [desktop.inventory.runtime.qa_state().controls["inventory.items"].item_values.duplicate(true),
		desktop.equipment_items.runtime.qa_state().controls["equipment_items.slots"].item_values.duplicate(true)]
	desktop._equipment_transaction("equip", "r0c2", "armor", stale_inventory, stale_equipment)
	_check("desktop-stale-gesture-preserves-both", not desktop.last_transaction.get("ok", false)
		and desktop.last_transaction.error.code == "GestureConflictError"
		and desktop.inventory.runtime.qa_state().controls["inventory.items"].item_values == preserved[0]
		and desktop.equipment_items.runtime.qa_state().controls["equipment_items.slots"].item_values == preserved[1],
		str(desktop.last_transaction))
	desktop.queue_free()
	_finish()


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "equipment-items-window-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/equipment-items-window-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("EQUIPMENT ITEMS WINDOW %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _center(geometry: Dictionary) -> Vector2:
	return Vector2(float(geometry.x) + float(geometry.width) / 2.0,
		float(geometry.y) + float(geometry.height) / 2.0)


func _drag_between(start: Vector2, finish: Vector2, desktop: Control) -> Dictionary:
	var move := InputEventMouseMotion.new()
	move.position = start
	move.global_position = start
	Input.parse_input_event(move)
	await process_frame
	var press := InputEventMouseButton.new()
	press.position = start
	press.global_position = start
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	Input.parse_input_event(press)
	await process_frame
	for index in range(1, 32):
		var point := start.lerp(finish, float(index) / 31.0)
		var motion := InputEventMouseMotion.new()
		motion.position = point
		motion.global_position = point
		motion.button_mask = MOUSE_BUTTON_MASK_LEFT
		Input.parse_input_event(motion)
		await process_frame
	var state: Dictionary = desktop.qa_state()
	var feedback := {
		"source": state.windows.inventory.controls["inventory.items"].drag_state.duplicate(true),
		"target": state.windows.equipment_items.controls["equipment_items.slots"].drag_state.duplicate(true),
	}
	if not str(feedback.target.get("source", "")).is_empty():
		feedback = {
			"source": state.windows.equipment_items.controls["equipment_items.slots"].drag_state.duplicate(true),
			"target": state.windows.inventory.controls["inventory.items"].drag_state.duplicate(true),
		}
	var release := InputEventMouseButton.new()
	release.position = finish
	release.global_position = finish
	release.button_index = MOUSE_BUTTON_LEFT
	release.pressed = false
	Input.parse_input_event(release)
	await process_frame
	await process_frame
	return feedback
