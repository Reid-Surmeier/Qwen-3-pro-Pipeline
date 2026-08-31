class_name DesktopActionRouter
extends RefCounted
## Frozen transaction and source-attested detail routing interface.

const Errors = preload("res://control_library/control_errors.gd")


static func transfer(source: Dictionary, target: Dictionary, item: String,
		expected_source_version: int, expected_target_version: int,
		modifiers: Array) -> Dictionary:
	if modifiers != ["ctrl"]:
		return _error(Errors.INVALID_MODIFIER,
			"cross-Window transfer requires exactly the Control modifier")
	if int(source.get("version", -1)) != expected_source_version \
			or int(target.get("version", -1)) != expected_target_version:
		return _error(Errors.GESTURE_CONFLICT,
			"source or target collection changed during transfer")
	var source_items: Variant = source.get("items")
	var target_items: Variant = target.get("items")
	if not source_items is Array or not target_items is Array or item not in source_items:
		return _error(Errors.TRANSACTION_REJECTED,
			"source does not contain the selected item")
	if item in target_items:
		return _error(Errors.TRANSACTION_REJECTED,
			"target already contains the selected item")
	if target_items.size() >= int(target.get("capacity", 0)):
		return _error(Errors.TRANSACTION_REJECTED,
			"target collection is full")
	var next_source := source.duplicate(true)
	var next_target := target.duplicate(true)
	next_source.items.erase(item)
	next_target.items.append(item)
	next_source.version = expected_source_version + 1
	next_target.version = expected_target_version + 1
	return {"ok": true, "source": next_source, "target": next_target,
		"item": item, "source_window": str(source.get("window_id", "")),
		"target_window": str(target.get("window_id", ""))}


static func equipment_transaction(inventory: Dictionary, equipment: Dictionary,
		operation: String, inventory_slot: String, equipment_slot: String,
		expected_inventory_version: int,
		expected_equipment_version: int) -> Dictionary:
	if operation not in ["equip", "unequip"]:
		return _error(Errors.ACTION_ROUTING,
			"equipment operation must be equip or unequip")
	if int(inventory.get("version", -1)) != expected_inventory_version \
			or int(equipment.get("version", -1)) != expected_equipment_version:
		return _error(Errors.GESTURE_CONFLICT,
			"Inventory or Equipment changed during the transaction")
	var inventory_slots: Variant = inventory.get("slots")
	var equipment_slots: Variant = equipment.get("slots")
	if not inventory_slots is Dictionary or not equipment_slots is Dictionary \
			or not inventory_slots.has(inventory_slot) \
			or not equipment_slots.has(equipment_slot):
		return _error(Errors.TRANSACTION_REJECTED,
			"source and destination slots must exist")
	var inventory_item := str(inventory_slots[inventory_slot])
	var equipment_item := str(equipment_slots[equipment_slot])
	if operation == "equip" and inventory_item.is_empty():
		return _error(Errors.TRANSACTION_REJECTED,
			"Inventory source slot is empty")
	if operation == "unequip" and equipment_item.is_empty():
		return _error(Errors.TRANSACTION_REJECTED,
			"Equipment source slot is empty")
	var next_inventory := inventory.duplicate(true)
	var next_equipment := equipment.duplicate(true)
	if operation == "equip":
		next_inventory.slots[inventory_slot] = equipment_item
		next_equipment.slots[equipment_slot] = inventory_item
	else:
		next_inventory.slots[inventory_slot] = equipment_item
		next_equipment.slots[equipment_slot] = inventory_item
	next_inventory.version = expected_inventory_version + 1
	next_equipment.version = expected_equipment_version + 1
	return {"ok": true, "action": "EquipItem" if operation == "equip" else "UnequipItem",
		"operation": operation, "inventory": next_inventory,
		"equipment": next_equipment, "inventory_slot": inventory_slot,
		"equipment_slot": equipment_slot, "displaced_item": equipment_item \
			if operation == "equip" else inventory_item}


static func open_detail(window_id: String, detail: Dictionary) -> Dictionary:
	var detail_id := str(detail.get("id", ""))
	if window_id.is_empty() or detail_id.is_empty():
		return _error(Errors.ACTION_ROUTING,
			"detail routing requires a Window and detail id")
	if detail.get("source_attested", false) != true:
		return _error(Errors.VISUAL_AUTHORITY,
			"detail pixels are not source-attested")
	return {"ok": true, "action": "OpenDetail", "window_id": window_id,
		"detail_item": detail_id, "visible": true,
		"continuation_available": bool(detail.get("continuation_available", false))}


static func close_detail(window_id: String, detail_id: String) -> Dictionary:
	if window_id.is_empty() or detail_id.is_empty():
		return _error(Errors.ACTION_ROUTING,
			"detail routing requires a Window and detail id")
	return {"ok": true, "action": "CloseDetail", "window_id": window_id,
		"detail_item": detail_id, "visible": false}


static func open_window(available_window_ids: Array, target_window: String) -> Dictionary:
	if target_window.is_empty() or target_window not in available_window_ids:
		return _error(Errors.ACTION_ROUTING,
			"destination Window is not declared: %s" % target_window)
	return {"ok": true, "action": "OpenWindow",
		"target_window": target_window, "visible": true, "raised": true}


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
