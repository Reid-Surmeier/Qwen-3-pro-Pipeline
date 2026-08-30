class_name ControlRuntime
extends RefCounted
## Factual semantic runtime behind the ControlSpec seam. Input arrives as a
## shared Gesture Capability; the runtime applies the declared Window Action
## and exposes observations through qa_state(). Rendering is a separate adapter.

const Errors = preload("res://control_library/control_errors.gd")
const ChoiceGroup = preload("res://control_library/choice_group.gd")
const SelectionViewModule = preload("res://control_library/selection_view.gd")
const StepperModule = preload("res://control_library/stepper.gd")

var window_spec: Dictionary = {}
var controls: Dictionary = {}
var interaction_log: Array[Dictionary] = []


func configure(spec: Dictionary) -> Dictionary:
	window_spec = spec.duplicate(true)
	controls.clear()
	interaction_log.clear()
	for control_spec in window_spec.get("controls", []):
		var control_id := str(control_spec.id)
		var state := {
			"id": control_id,
			"type": str(control_spec.type),
			"interaction_phase": "idle",
			"active_surface": "",
			"semantic_state": str(control_spec.initial_semantic_state),
			"last_action": "",
			"last_gesture": "",
			"last_error": null,
			"geometry": control_spec.get("geometry", {}).duplicate(true),
			"visible": true,
			"z_index": 0,
			"rendered": false,
			"text": "",
			"last_result": {"accepted": false, "action": "", "error": null},
		}
		if str(control_spec.type) == "Stepper":
			state.current = control_spec.value.current
			state.target = control_spec.value.target
			state.minimum = control_spec.value.minimum
			state.maximum = control_spec.value.maximum
			state.step = control_spec.value.step
			state.pending = false
			state.arrows_visible = true
			state.text = StepperModule.format_value(state.current, state.target)
		elif control_spec.has("value"):
			state.value = control_spec.value.get("initial")
			if state.value is String:
				state.text = state.value
		controls[control_id] = {"spec": control_spec.duplicate(true), "state": state}
	return {"ok": true, "window_id": str(window_spec.get("id", "")),
		"control_count": controls.size()}


func set_interaction_phase(control_id: String, phase: String, surface: String = "") -> Dictionary:
	if not controls.has(control_id):
		return _reject(control_id, "", Errors.INVALID_CONTROL_SPEC,
			"unknown control id")
	var spec: Dictionary = controls[control_id].spec
	if phase not in spec.interaction_phases:
		return _reject(control_id, "", Errors.INVALID_STATE_SET,
			"undeclared interaction phase: %s" % phase)
	controls[control_id].state.interaction_phase = phase
	controls[control_id].state.active_surface = surface
	return {"ok": true, "interaction_phase": phase, "active_surface": surface}


func dispatch(control_id: String, gesture: String, payload: Dictionary) -> Dictionary:
	if not controls.has(control_id):
		return _reject(control_id, gesture, Errors.INVALID_CONTROL_SPEC,
			"unknown control id")
	var entry: Dictionary = controls[control_id]
	var spec: Dictionary = entry.spec
	if gesture not in spec.gestures:
		return _reject(control_id, gesture, Errors.UNSUPPORTED_GESTURE,
			"gesture is not declared by the control")
	var result: Dictionary
	match str(spec.type):
		"Toggle":
			result = _dispatch_toggle(entry, gesture)
		"Range":
			result = _dispatch_range(entry, gesture, payload)
		"Dropdown":
			result = _dispatch_dropdown(entry, gesture, payload)
		"ChoiceGroup":
			result = _dispatch_choice_group(entry, gesture, payload)
		"SelectionView":
			result = _dispatch_selection_view(entry, gesture, payload)
		"Stepper":
			result = _dispatch_stepper(entry, gesture, payload)
		"Button":
			result = _dispatch_button(entry, gesture)
		_:
			result = _reject(control_id, gesture, Errors.CONTROL_BINDING,
				"control type has no runtime action adapter")
	if result.get("ok", false):
		entry.state.last_error = null
		entry.state.last_gesture = gesture
		entry.state.last_result = {"accepted": true,
			"action": str(entry.state.last_action), "error": null}
		if entry.state.get("value") is String:
			entry.state.text = str(entry.state.value)
		interaction_log.append({"control_id": control_id, "gesture": gesture,
			"accepted": true, "semantic_state": entry.state.semantic_state,
			"value": entry.state.get("value")})
	return result


func qa_state() -> Dictionary:
	var factual_controls := {}
	for control_id in controls:
		factual_controls[control_id] = controls[control_id].state.duplicate(true)
	return {
		"window_id": str(window_spec.get("id", "")),
		"controls": factual_controls,
		"interaction_log": interaction_log.duplicate(true),
		"window_pending": _has_pending_stepper(),
	}


func reject_action(control_id: String, action: String) -> Dictionary:
	return _reject(control_id, "", Errors.ACTION_ROUTING,
		"Window cannot route action: %s" % action)


func visual_asset(control_id: String) -> String:
	if not controls.has(control_id):
		return ""
	var entry: Dictionary = controls[control_id]
	var state: Dictionary = entry.state
	return str(entry.spec.state_set.get(state.semantic_state, {}).get(
		state.interaction_phase, ""))


func visual_surface_asset(control_id: String, surface_id: String) -> String:
	if not controls.has(control_id):
		return ""
	var entry: Dictionary = controls[control_id]
	if not entry.spec.get("surfaces", {}).has(surface_id):
		return ""
	var state: Dictionary = entry.state
	var surface: Dictionary = entry.spec.surfaces[surface_id]
	var semantic := str(state.semantic_state)
	if str(entry.spec.type) == "SelectionView":
		semantic = "selected" if str(state.get("value", "")) == surface_id else "unselected"
	elif str(entry.spec.type) == "Stepper":
		semantic = "visible" if bool(state.get("arrows_visible", true)) else "hidden"
	var phase := str(state.interaction_phase) \
		if str(state.get("active_surface", "")) == surface_id else "idle"
	return str(surface.state_set.get(semantic, {}).get(phase, ""))


func _dispatch_toggle(entry: Dictionary, gesture: String) -> Dictionary:
	if gesture != "Activate":
		return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
			"Toggle accepts Activate")
	var states: Array = entry.spec.semantic_states
	if states.size() != 2:
		return _reject(entry.state.id, gesture, Errors.INVALID_STATE_SET,
			"Toggle requires exactly two semantic states")
	entry.state.semantic_state = states[1] if entry.state.semantic_state == states[0] else states[0]
	entry.state.interaction_phase = "idle"
	entry.state.last_action = "ToggleValue"
	return {"ok": true, "semantic_state": entry.state.semantic_state}


func _dispatch_range(entry: Dictionary, gesture: String, payload: Dictionary) -> Dictionary:
	var value_spec: Dictionary = entry.spec.value
	var minimum := float(value_spec.minimum)
	var maximum := float(value_spec.maximum)
	var next := float(entry.state.value)
	match gesture:
		"Drag":
			if not payload.has("normalized"):
				return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
					"Range Drag requires normalized pointer position")
			next = lerpf(minimum, maximum, clampf(float(payload.normalized), 0.0, 1.0))
		"Activate":
			var direction := float(payload.get("direction", 0.0))
			next += direction * float(value_spec.arrow_step)
		"Wheel":
			var wheel_direction := float(payload.get("direction", 0.0))
			next += wheel_direction * float(value_spec.wheel_step)
		_:
			return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
				"gesture is not bound to Range")
	entry.state.value = clampf(next, minimum, maximum)
	entry.state.last_action = "SetRange" if gesture == "Drag" else "StepRange"
	return {"ok": true, "value": entry.state.value}


func _dispatch_dropdown(entry: Dictionary, gesture: String, payload: Dictionary) -> Dictionary:
	if gesture == "KeyCommand":
		if str(payload.get("key", "")) != "Escape":
			return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
				"Dropdown KeyCommand must be Escape")
		entry.state.semantic_state = "closed"
		entry.state.interaction_phase = "idle"
		entry.state.last_action = "DismissDropdown"
		return {"ok": true, "value": entry.state.value,
			"semantic_state": entry.state.semantic_state}
	if gesture != "Activate":
		return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
			"Dropdown accepts Activate or KeyCommand")
	if payload.has("choice"):
		var choice: String = str(payload.choice)
		if choice not in entry.spec.value.choices:
			return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
				"choice is not declared: %s" % choice)
		entry.state.value = choice
		entry.state.semantic_state = "closed"
		entry.state.last_action = "SelectChoice"
	else:
		entry.state.semantic_state = "open" \
			if entry.state.semantic_state == "closed" else "closed"
		entry.state.last_action = "ToggleDropdown"
	entry.state.interaction_phase = "idle"
	return {"ok": true, "value": entry.state.value,
		"semantic_state": entry.state.semantic_state}


func _dispatch_choice_group(entry: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	var result: Dictionary = ChoiceGroup.select(entry.spec, entry.state, gesture, payload)
	if not result.ok:
		return _reject(entry.state.id, gesture, result.error.code, result.error.detail)
	entry.state.value = result.value
	entry.state.interaction_phase = "idle"
	entry.state.last_action = "SelectChoice"
	return {"ok": true, "value": entry.state.value,
		"semantic_state": entry.state.semantic_state}


func _dispatch_selection_view(entry: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	var result: Dictionary = SelectionViewModule.activate(entry.spec, entry.state,
		gesture, payload)
	if not result.ok:
		return _reject(entry.state.id, gesture, result.error.code, result.error.detail)
	return result


func _dispatch_stepper(entry: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	var result: Dictionary = StepperModule.step(entry.spec, entry.state, gesture, payload)
	if not result.ok:
		return _reject(entry.state.id, gesture, result.error.code, result.error.detail)
	_set_all_stepper_arrows(not _has_pending_stepper())
	return result


func _dispatch_button(entry: Dictionary, gesture: String) -> Dictionary:
	if gesture != "Activate":
		return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
			"Button accepts Activate")
	var action := ""
	for binding in entry.spec.actions:
		if binding.gesture == gesture:
			action = str(binding.action)
			break
	if action.is_empty():
		return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
			"Button has no Activate Window Action")
	if action not in ["ToggleMinimized", "CloseWindow", "ToggleSkillView",
			"CommitSkillChanges", "CancelSkillChanges"]:
		return _reject(entry.state.id, gesture, Errors.ACTION_ROUTING,
			"Button action is not routed: %s" % action)
	if action == "CommitSkillChanges":
		_commit_steppers()
	elif action == "CancelSkillChanges":
		_cancel_steppers()
	entry.state.interaction_phase = "idle"
	entry.state.last_action = action
	return {"ok": true, "action": action,
		"semantic_state": entry.state.semantic_state}


func _has_pending_stepper() -> bool:
	for control_id in controls:
		var entry: Dictionary = controls[control_id]
		if str(entry.spec.type) == "Stepper" and bool(
				entry.state.get("pending", false)):
			return true
	return false


func _set_all_stepper_arrows(visible: bool) -> void:
	for control_id in controls:
		var entry: Dictionary = controls[control_id]
		if str(entry.spec.type) == "Stepper":
			entry.state.arrows_visible = visible


func _commit_steppers() -> void:
	for control_id in controls:
		var entry: Dictionary = controls[control_id]
		if str(entry.spec.type) == "Stepper":
			entry.state.current = entry.state.target
			entry.state.pending = false
			entry.state.semantic_state = "ready"
			entry.state.text = StepperModule.format_value(
				entry.state.current, entry.state.target)
	_set_all_stepper_arrows(true)


func _cancel_steppers() -> void:
	for control_id in controls:
		var entry: Dictionary = controls[control_id]
		if str(entry.spec.type) == "Stepper":
			entry.state.target = entry.state.current
			entry.state.pending = false
			entry.state.semantic_state = "ready"
			entry.state.text = StepperModule.format_value(
				entry.state.current, entry.state.target)
	_set_all_stepper_arrows(true)


func _reject(control_id: String, gesture: String, code: String, detail: String) -> Dictionary:
	var error := {"code": code, "detail": detail}
	if controls.has(control_id):
		controls[control_id].state.last_error = error
		controls[control_id].state.last_result = {
			"accepted": false, "action": "", "error": error}
	interaction_log.append({"control_id": control_id, "gesture": gesture,
		"accepted": false, "error": error})
	return {"ok": false, "error": error}
