class_name ChoiceGroupControl
extends RefCounted
## Pure single-selection policy for the shared ChoiceGroup Control type.

const Errors = preload("res://control_library/control_errors.gd")


static func select(spec: Dictionary, state: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if gesture != "Activate":
		return _error(Errors.CONTROL_BINDING, "ChoiceGroup accepts Activate")
	if not payload.has("choice"):
		return _error(Errors.CONTROL_BINDING, "ChoiceGroup requires a choice")
	var value_spec: Variant = spec.get("value")
	if not value_spec is Dictionary or not value_spec.get("choices") is Array:
		return _error(Errors.INVALID_STATE_SET, "ChoiceGroup requires declared choices")
	var choice := str(payload.choice)
	if choice not in value_spec.choices:
		return _error(Errors.CONTROL_BINDING,
			"choice is not declared: %s" % choice)
	return {"ok": true, "value": choice,
		"previous": state.get("value")}


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
