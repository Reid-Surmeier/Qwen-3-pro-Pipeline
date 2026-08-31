extends Control
## Incremental image-79 production desktop. Every integrated Window is built
## from the same validated schema-v3 manifest and publishes factual QA state.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlWindowScript = preload("res://control_library/control_window.gd")
const DesktopActionRouter = preload("res://desktop_router/desktop_action_router.gd")

var options: ControlWindow
var skill_tree: ControlWindow
var inventory: ControlWindow
var storage: ControlWindow
var equipment_card: ControlWindow
var equipment_items: ControlWindow
var status: ControlWindow
var basic_info: ControlWindow
var system_menu: ControlWindow
var windows := {}
var validation_errors: Array = []
var last_transaction: Dictionary = {}
var _last_json := ""
var _cross_window_drag := {}

func _ready() -> void:
	var background := ColorRect.new()
	background.name = "Image79Magenta"
	background.color = Color8(255, 0, 254)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)
	var loaded: Dictionary = ControlSpec.load_and_validate(
		"res://data/image-79-control-spec.json")
	validation_errors = loaded.errors
	if not validation_errors.is_empty():
		push_error("Image 79 ControlSpec rejected: %s" % str(validation_errors))
		_publish()
		return
	for window_spec in loaded.manifest.windows:
		var window: ControlWindow = ControlWindowScript.new()
		window.configure(window_spec)
		window.state_changed.connect(_publish)
		window.action_emitted.connect(_route_desktop_action)
		add_child(window)
		windows[str(window_spec.id)] = window
	options = windows.get("options")
	skill_tree = windows.get("skill_tree")
	inventory = windows.get("inventory")
	storage = windows.get("storage")
	equipment_card = windows.get("equipment_card")
	equipment_items = windows.get("equipment_items")
	status = windows.get("status")
	basic_info = windows.get("basic_info")
	system_menu = windows.get("system_menu")
	# Manifest order remains the stable ControlSpec interface (Options first),
	# while source reset stacking places Basic Info behind overlapping Windows.
	if basic_info != null:
		move_child(basic_info, 1)
	if equipment_card != null:
		var detail_route: Dictionary = DesktopActionRouter.open_detail(
			"equipment_card", equipment_card.spec.get("detail", {}))
		if detail_route.get("ok", false):
			equipment_card.detail_item = str(detail_route.detail_item)
	_publish()


func _unhandled_key_input(event: InputEvent) -> void:
	if not (event is InputEventKey) or not event.pressed or event.echo \
			or event.keycode != KEY_ESCAPE or system_menu == null:
		return
	var semantic_before: Dictionary = system_menu.runtime.qa_state()
	var position_before: Array = system_menu.qa_state().window.position
	last_transaction = DesktopActionRouter.open_window(windows.keys(), "system_menu")
	last_transaction.source_window = "desktop"
	last_transaction.control_id = "desktop.escape"
	last_transaction.context = "no_frontmost_closeable_window"
	if last_transaction.get("ok", false):
		system_menu.visible = true
		system_menu.move_to_front()
		last_transaction.position_before = position_before
		last_transaction.position_after = system_menu.qa_state().window.position
		last_transaction.semantic_state_preserved = \
			system_menu.runtime.qa_state() == semantic_before
		get_viewport().set_input_as_handled()
	_publish()


func qa_state() -> Dictionary:
	var window_states := {}
	for window_id in windows:
		window_states[window_id] = windows[window_id].qa_state()
	return {
		"schema_version": 3,
		"reference_sha256": "f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f",
		"viewport": [1536, 1024],
		"validation_errors": validation_errors,
		"windows": window_states,
		"last_transaction": last_transaction.duplicate(true),
	}


func _route_desktop_action(window_id: String, control_id: String,
		result: Dictionary) -> void:
	if str(result.get("action", "")) == "OpenWindow":
		var target_id := str(result.get("target_window", ""))
		var target: ControlWindow = windows.get(target_id)
		var target_semantic_before: Dictionary = target.runtime.qa_state() \
			if target != null else {}
		last_transaction = DesktopActionRouter.open_window(windows.keys(), target_id)
		last_transaction.source_window = window_id
		last_transaction.control_id = control_id
		if last_transaction.get("ok", false):
			last_transaction.position_before = target.qa_state().window.position
			target.visible = true
			target.move_to_front()
			last_transaction.position_after = target.qa_state().window.position
			last_transaction.semantic_state_preserved = \
				target.runtime.qa_state() == target_semantic_before
		else:
			var source: ControlWindow = windows.get(window_id)
			if source != null:
				var error: Dictionary = last_transaction.get("error", {})
				source.runtime.reject_action(control_id, "OpenWindow",
					str(error.get("code", "ActionRoutingError")),
					str(error.get("detail", "destination Window rejected")))
				source._refresh_all_controls()
		_publish()
		return
	if result.get("cross_window_drag", false) \
			or result.get("cross_window_drag_end", false):
		_route_cross_window_drag(window_id, control_id, result)
		return
	if window_id == "equipment_card" \
			and str(result.get("action", "")) == "CloseWindow":
		var card_window: ControlWindow = windows.get(window_id)
		var detail_id := str(card_window.detail_item) if card_window != null else ""
		last_transaction = DesktopActionRouter.close_detail(window_id,
			detail_id)
		if last_transaction.get("ok", false) and card_window != null:
			card_window.detail_item = ""
		_publish()
		return
	if window_id == "equipment_items" \
			and str(result.get("gesture", "")) == "DoubleActivate" \
			and str(result.get("action", "")) == "UnequipEquipmentItem":
		var inventory_slot := str(inventory.runtime.qa_state().controls[
			"inventory.items"].get("value", "")) if inventory != null else ""
		_equipment_transaction("unequip", inventory_slot,
			str(result.get("value", "")))
		return
	if window_id == "inventory" \
			and str(result.get("action", "")) == "EquipInventoryItem" \
			and inventory != null and equipment_items != null \
			and str(inventory.runtime.qa_state().controls["inventory.tabs"].get(
				"value", "")) == "equip":
		var equipment_slot := str(equipment_items.runtime.qa_state().controls[
			"equipment_items.slots"].get("value", ""))
		_equipment_transaction("equip", str(result.get("value", "")), equipment_slot)
		return
	if str(result.get("gesture", "")) != "ModifierDoubleActivate" \
			or window_id not in ["inventory", "storage"]:
		return
	var target_id := "storage" if window_id == "inventory" else "inventory"
	var source_window: ControlWindow = windows.get(window_id)
	var target_window: ControlWindow = windows.get(target_id)
	if source_window == null or target_window == null:
		return
	var source_control := window_id + ".items"
	var target_control := target_id + ".items"
	var slot := str(result.get("value", ""))
	var item := source_window.runtime.selected_logical_item(source_control, slot)
	var source := source_window.runtime.selection_collection(source_control)
	var target := target_window.runtime.selection_collection(target_control)
	var transaction: Dictionary = DesktopActionRouter.transfer(source, target, item,
		int(source.get("version", -1)), int(target.get("version", -1)), ["ctrl"])
	last_transaction = {"ok": bool(transaction.get("ok", false)),
		"source_window": window_id, "target_window": target_id, "item": item,
		"source_version_before": source.get("version"),
		"target_version_before": target.get("version"),
		"error": transaction.get("error")}
	if transaction.get("ok", false):
		source_window.runtime.apply_selection_collection(source_control, transaction.source)
		target_window.runtime.apply_selection_collection(target_control, transaction.target)
		if source_window.runtime.controls.has(window_id + ".scroll"):
			source_window.runtime.sync_scroll_bounds(window_id + ".scroll", source_control)
		if target_window.runtime.controls.has(target_id + ".scroll"):
			target_window.runtime.sync_scroll_bounds(target_id + ".scroll", target_control)
		source_window._refresh_all_controls()
		target_window._refresh_all_controls()
		last_transaction.source_version_after = transaction.source.version
		last_transaction.target_version_after = transaction.target.version
	_publish()


func _equipment_transaction(operation: String, inventory_slot: String,
		equipment_slot: String, expected_inventory_version: int = -1,
		expected_equipment_version: int = -1) -> Dictionary:
	if inventory == null or equipment_items == null:
		last_transaction = {"ok": false, "error": {"code": "ActionRoutingError",
			"detail": "Inventory and Equipment Items must both exist"}}
		_publish()
		return last_transaction
	var inventory_control := "inventory.items"
	var equipment_control := "equipment_items.slots"
	var inventory_snapshot := inventory.runtime.selection_slots(inventory_control)
	var equipment_snapshot := equipment_items.runtime.selection_slots(equipment_control)
	if expected_inventory_version < 0:
		expected_inventory_version = int(inventory_snapshot.get("version", -1))
	if expected_equipment_version < 0:
		expected_equipment_version = int(equipment_snapshot.get("version", -1))
	var transaction: Dictionary = DesktopActionRouter.equipment_transaction(
		inventory_snapshot, equipment_snapshot, operation, inventory_slot,
		equipment_slot, expected_inventory_version, expected_equipment_version)
	last_transaction = {"ok": bool(transaction.get("ok", false)),
		"action": transaction.get("action"), "operation": operation,
		"inventory_slot": inventory_slot, "equipment_slot": equipment_slot,
		"inventory_version_before": inventory_snapshot.get("version"),
		"equipment_version_before": equipment_snapshot.get("version"),
		"error": transaction.get("error")}
	if transaction.get("ok", false):
		inventory.runtime.apply_selection_slots(inventory_control, transaction.inventory)
		equipment_items.runtime.apply_selection_slots(equipment_control, transaction.equipment)
		inventory.runtime.set_selection_drag_state(inventory_control, false)
		equipment_items.runtime.set_selection_drag_state(equipment_control, false)
		inventory._refresh_all_controls()
		equipment_items._refresh_all_controls()
		last_transaction.inventory_version_after = transaction.inventory.version
		last_transaction.equipment_version_after = transaction.equipment.version
		last_transaction.displaced_item = transaction.displaced_item
	_publish()
	return last_transaction


func _route_cross_window_drag(window_id: String, control_id: String,
		result: Dictionary) -> void:
	if window_id not in ["inventory", "equipment_items"] \
			or control_id not in ["inventory.items", "equipment_items.slots"]:
		return
	if inventory == null or equipment_items == null:
		return
	var global_coordinates: Array = result.get("global_position", [])
	if global_coordinates.size() != 2:
		return
	var point := Vector2(float(global_coordinates[0]), float(global_coordinates[1]))
	if _cross_window_drag.is_empty() or str(_cross_window_drag.get(
			"source_window", "")) != window_id:
		var inventory_state: Dictionary = inventory.runtime.qa_state().controls["inventory.items"]
		var equipment_state: Dictionary = equipment_items.runtime.qa_state().controls["equipment_items.slots"]
		_cross_window_drag = {
			"source_window": window_id,
			"source_control": control_id,
			"source_slot": str(result.get("source", "")),
			"target_slot": "",
			"motion_samples": int(result.get("motion_samples", 0)),
			"inventory_version": int(result.get("version", -1)) if window_id == "inventory" \
				else int(inventory_state.get("item_version", -1)),
			"equipment_version": int(result.get("version", -1)) if window_id == "equipment_items" \
				else int(equipment_state.get("item_version", -1)),
		}
	var source_is_inventory := window_id == "inventory"
	var target_window := "equipment_items" if source_is_inventory else "inventory"
	var target_control := "equipment_items.slots" if source_is_inventory else "inventory.items"
	var target_slot := _slot_at_global(target_window, target_control, point)
	_cross_window_drag.target_slot = target_slot
	_cross_window_drag.motion_samples = int(result.get("motion_samples", 0))
	windows[target_window].runtime.set_selection_drag_state(target_control, true, "",
		target_slot, int(_cross_window_drag.motion_samples))
	windows[target_window]._refresh_all_controls()
	if not result.get("cross_window_drag_end", false):
		_publish()
		return
	var finished := _cross_window_drag.duplicate(true)
	finished.target_slot = _slot_at_global(target_window, target_control, point)
	_cross_window_drag = {}
	call_deferred("_commit_cross_window_drag", finished)


func _commit_cross_window_drag(finished: Dictionary) -> void:
	inventory.runtime.set_selection_drag_state("inventory.items", false)
	equipment_items.runtime.set_selection_drag_state("equipment_items.slots", false)
	inventory._refresh_all_controls()
	equipment_items._refresh_all_controls()
	var target_slot := str(finished.get("target_slot", ""))
	var source_is_inventory := str(finished.source_window) == "inventory"
	var inventory_slot := str(finished.source_slot) if source_is_inventory else target_slot
	var equipment_slot := target_slot if source_is_inventory else str(finished.source_slot)
	_equipment_transaction("equip" if source_is_inventory else "unequip",
		inventory_slot, equipment_slot, int(finished.inventory_version),
		int(finished.equipment_version))


func _slot_at_global(window_id: String, control_id: String, point: Vector2) -> String:
	var target_window: ControlWindow = windows.get(window_id)
	if target_window == null:
		return ""
	var window_state: Dictionary = target_window.qa_state()
	if not bool(window_state.window.get("visible", false)) \
			or bool(window_state.window.get("minimized", false)):
		return ""
	var surface_geometry: Dictionary = window_state.controls.get(control_id, {}).get(
		"surface_geometry", {})
	for slot in surface_geometry:
		var geometry: Dictionary = surface_geometry[slot]
		var rect := Rect2(float(geometry.x), float(geometry.y),
			float(geometry.width), float(geometry.height))
		if rect.has_point(point):
			return str(slot)
	return ""


func _publish(_window_id: String = "") -> void:
	if has_meta("suppress_publish"):
		return
	var json := JSON.stringify(qa_state())
	if json == _last_json:
		return
	_last_json = json
	print(json)
	if OS.has_feature("web"):
		JavaScriptBridge.eval("window.godotQaState = " + json + ";", true)


func _process(_delta: float) -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-image79=") and not has_meta("capturing"):
			set_meta("capturing", true)
			_capture(argument.trim_prefix("--capture-image79="))
func _capture(path: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	image.save_png(path)
	print("CAPTURED IMAGE79 ", path, " ", image.get_width(), "x", image.get_height())
	get_tree().quit()
