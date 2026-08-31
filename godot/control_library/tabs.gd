class_name Tabs
extends RefCounted
## Pure semantic module for choosing one manifest-declared tab. Pointer input
## belongs to TabsControl; this module receives normalized Activate facts.

const Errors = preload("res://control_library/control_errors.gd")


static func select(spec: Dictionary, state: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if gesture != "Activate":
		return _error(Errors.CONTROL_BINDING, "Tabs accepts Activate")
	var choice := str(payload.get("choice", ""))
	if choice not in spec.value.get("choices", []):
		return _error(Errors.CONTROL_BINDING, "tab is not declared: %s" % choice)
	var action := _action_for_gesture(spec, gesture)
	if action.is_empty():
		return _error(Errors.CONTROL_BINDING,
			"Tabs gesture has no declared Window Action: %s" % gesture)
	state.value = choice
	state.text = choice
	state.semantic_state = "ready"
	state.interaction_phase = "idle"
	state.active_surface = choice
	state.last_action = action
	state.last_gesture = gesture
	return {"ok": true, "action": action, "value": choice,
		"semantic_state": state.semantic_state, "gesture": gesture}


static func _action_for_gesture(spec: Dictionary, gesture: String) -> String:
	for binding in spec.get("actions", []):
		if binding is Dictionary and str(binding.get("gesture", "")) == gesture:
			return str(binding.get("action", ""))
	return ""


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
