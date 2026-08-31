class_name StatusWindowState
extends RefCounted
## Pure Status attribute transaction. The shared Stepper forwards a normalized
## direction; this adapter owns cost, points, availability, and derived values.

const Errors = preload("res://control_library/control_errors.gd")


static func initialize(adapter_spec: Dictionary) -> Dictionary:
	var problem := _validate_spec(adapter_spec)
	if not problem.is_empty():
		return _error(Errors.INVALID_CONTROL_SPEC, problem)
	var attributes := {}
	for control_id in adapter_spec.attributes:
		var source: Dictionary = adapter_spec.attributes[control_id]
		attributes[control_id] = {
			"key": str(source.key),
			"base": int(source.base),
			"initial_base": int(source.base),
			"bonus": int(source.bonus),
			"cost": cost_for(int(source.base)),
		}
	var state := {
		"version": 0,
		"points": int(adapter_spec.initial_points),
		"attributes": attributes,
		"derived": _derive(adapter_spec, attributes),
	}
	_refresh_availability(state)
	return {"ok": true, "state": state}


static func step(adapter_spec: Dictionary, state: Dictionary,
		control_id: String, direction: int, expected_version: int) -> Dictionary:
	var validated := initialize(adapter_spec)
	if not validated.get("ok", false):
		return _rejected(state, validated.error.code, validated.error.detail)
	if not _valid_state(state, adapter_spec):
		return _rejected(state, Errors.INVALID_CONTROL_SPEC,
			"Status state does not match the adapter spec")
	if int(state.version) != expected_version:
		return _rejected(state, Errors.GESTURE_CONFLICT,
			"Status version changed before the action")
	if control_id not in state.attributes:
		return _rejected(state, Errors.ACTION_ROUTING,
			"Status attribute is not declared: %s" % control_id)
	if direction not in [-1, 1]:
		return _rejected(state, Errors.ACTION_ROUTING,
			"Status direction must be -1 or 1")
	var current: Dictionary = state.attributes[control_id]
	var next := state.duplicate(true)
	if direction == 1:
		var cost := cost_for(int(current.base))
		var maximum := int(adapter_spec.attributes[control_id].get("maximum", 99))
		if int(current.base) >= maximum:
			return _rejected(state, Errors.TRANSACTION_REJECTED,
				"Status attribute is already at its maximum")
		if cost > int(state.points):
			return _rejected(state, Errors.TRANSACTION_REJECTED,
				"Status step costs %d; %d points available" % [cost, int(state.points)])
		next.attributes[control_id].base = int(current.base) + 1
		next.points = int(state.points) - cost
	else:
		if int(current.base) <= int(current.initial_base):
			return _rejected(state, Errors.TRANSACTION_REJECTED,
				"Status attribute is already at its source value")
		next.attributes[control_id].base = int(current.base) - 1
		next.points = int(state.points) + cost_for(int(current.base) - 1)
	next.attributes[control_id].cost = cost_for(
		int(next.attributes[control_id].base))
	next.version = int(state.version) + 1
	next.derived = _derive(adapter_spec, next.attributes)
	_refresh_availability(next)
	return {"ok": true, "action": "StepStatusAttribute",
		"control_id": control_id, "direction": direction, "state": next}


static func cost_for(value: int) -> int:
	return int(floor(float(value - 1) / 10.0)) + 2


static func _derive(adapter_spec: Dictionary, attributes: Dictionary) -> Dictionary:
	var values := {}
	var by_key := {}
	for control_id in attributes:
		var attribute: Dictionary = attributes[control_id]
		by_key[str(attribute.key)] = int(attribute.base) - int(attribute.initial_base)
	for derived_id in adapter_spec.derived:
		var rule: Dictionary = adapter_spec.derived[derived_id]
		var value := float(rule.base)
		for key in rule.coefficients:
			value += float(rule.coefficients[key]) * float(by_key.get(str(key), 0))
		values[derived_id] = int(value) if is_equal_approx(value, round(value)) else value
	return values


static func _refresh_availability(state: Dictionary) -> void:
	var availability := {}
	var reverse_availability := {}
	for control_id in state.attributes:
		var attribute: Dictionary = state.attributes[control_id]
		attribute.cost = cost_for(int(attribute.base))
		availability[control_id] = attribute.cost <= int(state.points)
		reverse_availability[control_id] = int(attribute.base) > int(attribute.initial_base)
	state.availability = availability
	state.reverse_availability = reverse_availability


static func _validate_spec(adapter_spec: Dictionary) -> String:
	if str(adapter_spec.get("type", "")) != "status":
		return "Status adapter type is required"
	if not adapter_spec.get("initial_points") is int \
			or int(adapter_spec.get("initial_points", -1)) < 0:
		return "Status initial_points must be a non-negative integer"
	var attributes: Variant = adapter_spec.get("attributes")
	if not attributes is Dictionary or attributes.is_empty():
		return "Status attributes must be a non-empty object"
	var keys := {}
	for control_id in attributes:
		var value: Variant = attributes[control_id]
		if str(control_id).is_empty() or not value is Dictionary \
				or str(value.get("key", "")).is_empty() \
				or not value.get("base") is int or int(value.get("base", 0)) < 1 \
				or not value.get("bonus") is int or int(value.get("bonus", -1)) < 0:
			return "Every Status attribute requires a control id, key, positive base, and non-negative bonus"
		if value.has("maximum") and (not value.maximum is int \
				or int(value.maximum) < int(value.base)):
			return "Status attribute maximum must be an integer at or above base"
		if keys.has(str(value.key)):
			return "Status attribute keys must be unique"
		keys[str(value.key)] = true
	var derived: Variant = adapter_spec.get("derived")
	if not derived is Dictionary or derived.is_empty():
		return "Status derived rules must be a non-empty object"
	for derived_id in derived:
		var rule: Variant = derived[derived_id]
		if str(derived_id).is_empty() or not rule is Dictionary \
				or not _number(rule.get("base")) \
				or not rule.get("coefficients") is Dictionary:
			return "Every Status derived rule requires a numeric base and coefficients"
		for key in rule.coefficients:
			if str(key) not in keys or not _number(rule.coefficients[key]):
				return "Status derived coefficients must reference declared attribute keys"
	return ""


static func _valid_state(state: Dictionary, adapter_spec: Dictionary) -> bool:
	return state.get("version") is int and int(state.get("version", -1)) >= 0 \
		and state.get("points") is int and int(state.get("points", -1)) >= 0 \
		and state.get("attributes") is Dictionary \
		and state.attributes.keys().all(func(control_id):
			return adapter_spec.attributes.has(control_id)) \
		and state.attributes.size() == adapter_spec.attributes.size()


static func _number(value: Variant) -> bool:
	return (value is int or value is float) and not value is bool \
		and is_finite(float(value))


static func _rejected(state: Dictionary, code: String, detail: String) -> Dictionary:
	return {"ok": false, "state": state.duplicate(true),
		"error": {"code": code, "detail": detail}}


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
