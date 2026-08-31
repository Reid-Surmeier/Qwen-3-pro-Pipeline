class_name SystemMenuWindowState
extends RefCounted
## Pure System Menu destination policy. It publishes route availability and
## emits normalized OpenWindow requests without fabricating unavailable UI.

const Errors = preload("res://control_library/control_errors.gd")


static func initialize(adapter_spec: Dictionary) -> Dictionary:
	var problem := _validate_spec(adapter_spec)
	if not problem.is_empty():
		return _error(Errors.INVALID_CONTROL_SPEC, problem)
	var destinations := {}
	for control_id in adapter_spec.actions:
		var route: Dictionary = adapter_spec.actions[control_id]
		destinations[str(control_id)] = {
			"target": str(route.target),
			"available": str(route.disposition) == "route",
			"reason": str(route.get("reason", "")),
		}
	return {"ok": true, "state": {
		"version": 0,
		"destinations": destinations,
		"last_action": "",
		"last_target": "",
	}}


static func activate(adapter_spec: Dictionary, state: Dictionary,
		control_id: String, expected_version: int) -> Dictionary:
	var initialized := initialize(adapter_spec)
	if not initialized.get("ok", false):
		return _rejected(state, initialized.error.code, initialized.error.detail)
	var state_problem := _state_problem(adapter_spec, state)
	if not state_problem.is_empty():
		return _rejected(state, Errors.INVALID_CONTROL_SPEC, state_problem)
	if int(state.version) != expected_version:
		return _rejected(state, Errors.GESTURE_CONFLICT,
			"System Menu version changed before the action")
	if control_id not in adapter_spec.actions:
		return _rejected(state, Errors.ACTION_ROUTING,
			"System Menu action is not declared: %s" % control_id)
	var route: Dictionary = adapter_spec.actions[control_id]
	var target := str(route.target)
	if str(route.disposition) == "reject":
		return {"ok": true, "action": "OpenWindow", "target_window": target,
			"expected_rejection": true, "state": state.duplicate(true)}
	var next := state.duplicate(true)
	next.version = int(state.version) + 1
	next.last_action = "OpenWindow"
	next.last_target = target
	return {"ok": true, "action": "OpenWindow", "target_window": target,
		"expected_rejection": false, "state": next}


static func _validate_spec(adapter_spec: Dictionary) -> String:
	if str(adapter_spec.get("type", "")) != "system_menu":
		return "System Menu adapter type is required"
	var actions: Variant = adapter_spec.get("actions")
	if not actions is Dictionary or actions.size() != 6:
		return "System Menu requires exactly six destination actions"
	var route_count := 0
	for control_id in actions:
		var route: Variant = actions[control_id]
		if not route is Dictionary or str(control_id).is_empty() \
				or str(route.get("target", "")).is_empty() \
				or str(route.get("disposition", "")) not in ["route", "reject"]:
			return "Every System Menu destination requires target and disposition"
		if str(route.disposition) == "route":
			route_count += 1
		elif str(route.get("reason", "")).is_empty():
			return "Rejected System Menu destinations require a factual reason"
	if route_count != 1:
		return "Exactly one System Menu destination is available in this release"
	return ""


static func _state_problem(adapter_spec: Dictionary, state: Dictionary) -> String:
	if not state.get("version") is int or int(state.get("version", -1)) < 0 \
			or not state.get("destinations") is Dictionary \
			or not state.get("last_action") is String \
			or not state.get("last_target") is String:
		return "System Menu state has malformed fields"
	var initialized: Dictionary = initialize(adapter_spec)
	if not initialized.get("ok", false) \
			or state.destinations != initialized.state.destinations:
		return "System Menu destination availability changed outside its adapter"
	return ""


static func _rejected(state: Dictionary, code: String, detail: String) -> Dictionary:
	return {"ok": false, "state": state.duplicate(true),
		"error": {"code": code, "detail": detail}}


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
