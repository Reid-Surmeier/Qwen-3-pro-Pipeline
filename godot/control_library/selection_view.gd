class_name SelectionView
extends RefCounted
## Pure semantic module for selecting an item or opening its contextual detail.
## Pointer grammar belongs to SelectionViewControl; this module receives only
## normalized Activate or ContextActivate facts.

const Errors = preload("res://control_library/control_errors.gd")


static func activate(spec: Dictionary, state: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if gesture not in ["Activate", "ContextActivate"]:
		return _error(Errors.CONTROL_BINDING,
			"SelectionView accepts Activate or ContextActivate")
	var item := str(payload.get("item", ""))
	if item not in spec.value.items:
		return _error(Errors.CONTROL_BINDING,
			"SelectionView item is not declared: %s" % item)
	var action := "SelectSkill" if gesture == "Activate" else "OpenSkillDetail"
	state.value = item
	state.text = item
	state.semantic_state = "selected"
	state.interaction_phase = "idle"
	state.active_surface = item
	state.last_action = action
	state.last_gesture = gesture
	return {"ok": true, "action": action, "value": item,
		"semantic_state": state.semantic_state, "gesture": gesture}


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
