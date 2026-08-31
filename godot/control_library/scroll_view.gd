class_name ScrollView
extends RefCounted
## Frozen Issue #128 semantic interface. Pointer recognition stays in the
## adapter; callers provide only normalized shared Gesture payloads.

const Errors = preload("res://control_library/control_errors.gd")


static func interact(spec: Dictionary, state: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	var action := _action_for_gesture(spec, gesture)
	if action.is_empty():
		return _error(Errors.CONTROL_BINDING,
			"ScrollView gesture has no declared Window Action: %s" % gesture)
	var value: Dictionary = spec.get("value", {})
	var minimum := int(value.get("minimum", 0))
	var maximum := int(value.get("maximum", 0))
	var next := int(state.get("offset", value.get("initial", minimum)))
	match gesture:
		"Wheel":
			var direction := signf(float(payload.get("direction", 0.0)))
			if direction == 0.0:
				return _error(Errors.CONTROL_BINDING,
					"ScrollView Wheel requires a non-zero direction")
			next += int(direction) * int(value.get("wheel_rows", 3))
		"Activate":
			var direction := signf(float(payload.get("direction", 0.0)))
			if direction == 0.0:
				return _error(Errors.CONTROL_BINDING,
					"ScrollView arrow requires a non-zero direction")
			next += int(direction) * int(value.get("arrow_rows", 1))
		"Drag":
			if not payload.has("normalized"):
				return _error(Errors.CONTROL_BINDING,
					"ScrollView Drag requires normalized track travel")
			next = roundi(lerpf(float(minimum), float(maximum),
				clampf(float(payload.normalized), 0.0, 1.0)))
		_:
			return _error(Errors.CONTROL_BINDING,
				"ScrollView gesture is not supported")
	state.offset = clampi(next, minimum, maximum)
	state.value = state.offset
	state.semantic_state = "at_start" if state.offset == minimum else (
		"at_end" if state.offset == maximum else "between")
	state.interaction_phase = "idle"
	state.last_action = action
	state.last_gesture = gesture
	return {"ok": true, "action": action, "offset": state.offset,
		"semantic_state": state.semantic_state, "gesture": gesture}


static func _action_for_gesture(spec: Dictionary, gesture: String) -> String:
	for binding in spec.get("actions", []):
		if binding is Dictionary and str(binding.get("gesture", "")) == gesture:
			return str(binding.get("action", ""))
	return ""


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
