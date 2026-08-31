class_name SelectionView
extends RefCounted
## Pure semantic module for single/context/double/modifier selection and an
## atomic same-View DragDrop. Pointer grammar belongs to SelectionViewControl.

const Errors = preload("res://control_library/control_errors.gd")


static func activate(spec: Dictionary, state: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if gesture not in ["Activate", "ContextActivate", "DoubleActivate",
			"ModifierActivate", "ModifierDoubleActivate", "DragDrop"]:
		return _error(Errors.CONTROL_BINDING, "SelectionView gesture is not supported")
	var action := _action_for_gesture(spec, gesture)
	if action.is_empty():
		return _error(Errors.CONTROL_BINDING,
			"SelectionView gesture has no declared Window Action: %s" % gesture)
	if gesture == "DragDrop":
		return _drag_drop(spec, state, action, payload)
	var item := str(payload.get("item", ""))
	if item not in spec.value.items:
		return _error(Errors.CONTROL_BINDING,
			"SelectionView item is not declared: %s" % item)
	if gesture in ["ModifierActivate", "ModifierDoubleActivate"]:
		if payload.has("modifiers") and not payload.modifiers is Array:
			return _error(Errors.INVALID_MODIFIER,
				"modifiers must be an array")
		var modifiers: Array = payload.get("modifiers", [])
		var allowed: Array = spec.value.get("allowed_modifiers", [])
		if modifiers != allowed:
			return _error(Errors.INVALID_MODIFIER,
				"expected modifiers %s, received %s" % [str(allowed), str(modifiers)])
		if gesture == "ModifierActivate":
			var selected: Array = state.get("selected_items", []).duplicate()
			if item in selected:
				selected.erase(item)
			else:
				selected.append(item)
			state.selected_items = selected
		else:
			state.value = item
			state.text = item
	elif gesture == "DoubleActivate":
		state.opened_item = item
		state.value = item
	elif gesture in ["Activate", "ContextActivate"]:
		state.value = item
		if gesture == "Activate" and state.has("selected_items"):
			state.selected_items = []
	if gesture not in ["ModifierActivate", "ModifierDoubleActivate"]:
		state.value = item
		state.text = item
	state.semantic_state = "selected"
	state.interaction_phase = "idle"
	state.active_surface = item
	state.last_action = action
	state.last_gesture = gesture
	return {"ok": true, "action": action, "value": item,
		"semantic_state": state.semantic_state, "gesture": gesture}


static func _drag_drop(spec: Dictionary, state: Dictionary, action: String,
		payload: Dictionary) -> Dictionary:
	if payload.has("modifiers") and not payload.modifiers is Array:
		return _error(Errors.INVALID_MODIFIER,
			"DragDrop modifiers must be an array")
	var modifiers: Array = payload.get("modifiers", [])
	if not modifiers.is_empty():
		return _error(Errors.INVALID_MODIFIER,
			"DragDrop does not accept modifiers: %s" % str(modifiers))
	var source := str(payload.get("source", ""))
	var target := str(payload.get("target", ""))
	var items: Array = spec.value.items
	var targets: Array = spec.value.get("drop_targets", items)
	if source not in items or target not in targets:
		return _error(Errors.INVALID_DROP_TARGET,
			"source and target must be declared SelectionView items")
	if source == target:
		return _error(Errors.INVALID_DROP_TARGET,
			"source and target must be distinct SelectionView items")
	var version := int(payload.get("version", -1))
	if version != int(state.get("item_version", 0)):
		return _error(Errors.GESTURE_CONFLICT,
			"item version changed during DragDrop")
	var values: Dictionary = state.get("item_values", {}).duplicate(true)
	if not values.has(source) or not values.has(target):
		return _error(Errors.INVALID_DROP_TARGET,
			"source and target must own declared item values")
	var source_value: Variant = values[source]
	values[source] = values[target]
	values[target] = source_value
	state.item_values = values
	state.item_version = version + 1
	state.value = target
	state.text = target
	state.selected_items = []
	state.semantic_state = "selected"
	state.interaction_phase = "idle"
	state.active_surface = target
	state.last_action = action
	state.last_gesture = "DragDrop"
	return {"ok": true, "action": action, "value": target,
		"source": source, "target": target, "item_version": state.item_version,
		"semantic_state": state.semantic_state, "gesture": "DragDrop"}


static func _action_for_gesture(spec: Dictionary, gesture: String) -> String:
	for binding in spec.get("actions", []):
		if binding is Dictionary and str(binding.get("gesture", "")) == gesture:
			return str(binding.get("action", ""))
	return ""


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
