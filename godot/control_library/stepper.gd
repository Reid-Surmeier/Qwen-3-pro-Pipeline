class_name Stepper
extends RefCounted
## Pure current/target Stepper semantics. A Window transaction owns commit,
## cancel, and the all-Steppers arrow-visibility invariant.

const Errors = preload("res://control_library/control_errors.gd")


static func step(spec: Dictionary, state: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if gesture != "Activate":
		return _error(Errors.CONTROL_BINDING, "Stepper accepts Activate")
	var direction := int(payload.get("direction", 0))
	if direction not in [-1, 1]:
		return _error(Errors.CONTROL_BINDING,
			"Stepper Activate requires direction -1 or 1")
	var next := clampf(float(state.target) + direction * float(spec.value.step),
		float(spec.value.minimum), float(spec.value.maximum))
	var changed := not is_equal_approx(float(state.target), next)
	state.target = next
	if changed:
		state.pending = true
	state.text = format_value(state.current, state.target)
	state.semantic_state = "pending" if bool(state.get("pending", false)) else "ready"
	state.interaction_phase = "idle"
	state.last_action = "StepSkill"
	state.last_gesture = gesture
	return {"ok": true, "action": "StepSkill", "current": state.current,
		"target": state.target, "text": state.text,
		"semantic_state": state.semantic_state}


static func format_value(current: Variant, target: Variant) -> String:
	return "%d / %d" % [int(current), int(target)]


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
