class_name TextField
extends RefCounted
## Frozen Issue #128 semantic interface. The adapter owns platform text input;
## this module accepts or rejects a complete candidate value atomically.

const Errors = preload("res://control_library/control_errors.gd")


static func edit(spec: Dictionary, state: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if gesture != "KeyCommand":
		return _error(Errors.CONTROL_BINDING, "TextField accepts KeyCommand")
	var action := ""
	for binding in spec.get("actions", []):
		if binding is Dictionary and binding.get("gesture") == gesture:
			action = str(binding.get("action", ""))
			break
	if action.is_empty():
		return _error(Errors.CONTROL_BINDING,
			"TextField KeyCommand has no declared Window Action")
	if not payload.has("text") or not payload.text is String:
		return _error(Errors.CONTROL_BINDING,
			"TextField KeyCommand requires complete text")
	var candidate := str(payload.text)
	var value: Dictionary = spec.get("value", {})
	if candidate.length() > int(value.get("maximum_length", 0)):
		return _error(Errors.CONTROL_BINDING,
			"TextField candidate exceeds maximum length")
	var pattern := str(value.get("accepted_pattern", ""))
	if not pattern.is_empty():
		var regex := RegEx.new()
		if regex.compile(pattern) != OK or regex.search(candidate) == null:
			return _error(Errors.CONTROL_BINDING,
				"TextField candidate contains unsupported characters")
	state.value = candidate
	state.text = candidate
	state.semantic_state = "empty" if candidate.is_empty() else "filtered"
	state.interaction_phase = "idle"
	state.last_action = action
	state.last_gesture = gesture
	return {"ok": true, "action": action, "value": candidate,
		"text": candidate, "semantic_state": state.semantic_state,
		"gesture": gesture}


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
