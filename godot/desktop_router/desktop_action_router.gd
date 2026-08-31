class_name DesktopActionRouter
extends RefCounted
## Frozen Issue #128 transaction interface.

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


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
