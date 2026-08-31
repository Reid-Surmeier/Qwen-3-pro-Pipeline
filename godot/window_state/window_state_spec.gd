class_name WindowStateSpec
extends RefCounted
## Domain validation host called through the ControlSpec construction seam.

const Errors = preload("res://control_library/control_errors.gd")
const StatusWindowState = preload("res://window_state/status_window_state.gd")
const PartyWindowState = preload("res://window_state/party_window_state.gd")
const SystemMenuWindowState = preload("res://window_state/system_menu_window_state.gd")
const ChatRoomWindowState = preload("res://window_state/chat_room_window_state.gd")


static func validate(adapter: Variant, controls: Array, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	if not adapter is Dictionary or str(adapter.get("type", "")) not in ["status", "party", "system_menu", "chat_room"]:
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path,
			"Window state adapter must declare a supported type"))
		return
	if str(adapter.type) == "party":
		_validate_party(adapter, controls, path, errors, asset_exists)
	elif str(adapter.type) == "system_menu":
		_validate_system_menu(adapter, controls, path, errors)
	elif str(adapter.type) == "chat_room":
		_validate_chat_room(adapter, controls, path, errors)
	else:
		_validate_status(adapter, controls, path, errors, asset_exists)


static func _validate_status(adapter: Dictionary, controls: Array, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	var initialized: Dictionary = StatusWindowState.initialize(adapter)
	if not initialized.get("ok", false):
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path,
			str(initialized.get("error", {}).get("detail", "invalid Status adapter"))))
	var declared := _declared_controls(controls)
	var attributes: Variant = adapter.get("attributes", {})
	if attributes is Dictionary:
		for control_id in attributes:
			var control: Variant = declared.get(str(control_id))
			if not control is Dictionary or str(control.get("type", "")) != "Stepper" \
					or not _has_action(control, "StepStatusAttribute"):
				errors.append(_error(Errors.CONTROL_BINDING,
					path + ".attributes." + str(control_id),
					"Status attribute must reference a same-Window Stepper bound to StepStatusAttribute"))
		for control_id in declared:
			var control: Dictionary = declared[control_id]
			if str(control.get("type", "")) == "Stepper" \
					and _has_action(control, "StepStatusAttribute") \
					and not attributes.has(control_id):
				errors.append(_error(Errors.CONTROL_BINDING, path + ".attributes",
					"Every Status Stepper must belong to the adapter"))
	_validate_status_presentation(adapter.get("presentation"), attributes,
		adapter.get("derived", {}), path + ".presentation", errors, asset_exists)


static func _validate_party(adapter: Dictionary, controls: Array, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	var initialized: Dictionary = PartyWindowState.initialize(adapter)
	if not initialized.get("ok", false):
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path,
			str(initialized.get("error", {}).get("detail", "invalid Party adapter"))))
	var declared := _declared_controls(controls)
	var mappings: Variant = adapter.get("controls")
	if not mappings is Dictionary:
		errors.append(_error(Errors.CONTROL_BINDING, path + ".controls",
			"Party adapter requires manifest-owned Control mappings"))
		return
	var mode_id := str(mappings.get("mode", ""))
	var member_id := str(mappings.get("members", ""))
	if not declared.get(mode_id) is Dictionary \
			or str(declared[mode_id].get("type", "")) != "ChoiceGroup" \
			or not _has_action(declared[mode_id], "SelectPartyMode"):
		errors.append(_error(Errors.CONTROL_BINDING, path + ".controls.mode",
			"Party mode must map a ChoiceGroup bound to SelectPartyMode"))
	if not declared.get(member_id) is Dictionary \
			or str(declared[member_id].get("type", "")) != "SelectionView" \
			or not _has_action(declared[member_id], "SelectPartyMember"):
		errors.append(_error(Errors.CONTROL_BINDING, path + ".controls.members",
			"Party members must map a SelectionView bound to SelectPartyMember"))
	else:
		var members: Dictionary = declared[member_id]
		if members.get("semantic_states", []) != ["unselected", "selected", "unavailable"] \
				or not members.get("state_set", {}).has("unavailable") \
				or not members.get("surfaces", {}).values().all(func(surface):
					return surface is Dictionary \
						and surface.get("state_set", {}).has("unavailable")):
			errors.append(_error(Errors.INVALID_STATE_SET,
				path + ".controls.members",
				"Party members require unselected, selected, and unavailable State Sets"))
	var action_ids: Variant = mappings.get("actions")
	var expected_actions: Array = adapter.get("actions", {}).keys().map(func(value):
		return str(value))
	var mapped_actions: Array = action_ids.map(func(value): return str(value)) \
		if action_ids is Array else []
	var unique := {}
	for action_id in mapped_actions:
		unique[action_id] = true
	var mapping_valid := action_ids is Array and mapped_actions.size() == 5 \
		and unique.size() == mapped_actions.size() \
		and mapped_actions.all(func(action_id): return action_id in expected_actions) \
		and expected_actions.all(func(action_id): return action_id in mapped_actions) \
		and mode_id not in mapped_actions and member_id not in mapped_actions
	if mapping_valid:
		for action_id in mapped_actions:
			var control: Variant = declared.get(action_id)
			if not control is Dictionary or str(control.get("type", "")) != "Button" \
					or not _has_action(control, "ActivatePartyAction") \
					or str(control.get("value", {}).get("action_id", "")) != action_id:
				mapping_valid = false
				break
	if not mapping_valid:
		errors.append(_error(Errors.CONTROL_BINDING, path + ".controls.actions",
			"Party actions must uniquely map every declared source Button and action identity"))
	var presentation: Variant = adapter.get("presentation")
	if not presentation is Dictionary:
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path + ".presentation",
			"Party presentation must be manifest-owned"))
		return
	_validate_asset(str(presentation.get("blank_list", "")),
		path + ".presentation.blank_list", errors, asset_exists)
	_validate_geometry(presentation.get("geometry"),
		path + ".presentation.geometry", errors)


static func _validate_system_menu(adapter: Dictionary, controls: Array,
		path: String, errors: Array[Dictionary]) -> void:
	var initialized: Dictionary = SystemMenuWindowState.initialize(adapter)
	if not initialized.get("ok", false):
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path,
			str(initialized.get("error", {}).get("detail", "invalid System Menu adapter"))))
	var declared := _declared_controls(controls)
	var policy_ids: Array = adapter.get("actions", {}).keys().map(func(value):
		return str(value))
	var open_window_ids: Array = []
	for control_id in declared:
		var declared_control: Dictionary = declared[control_id]
		if _has_action(declared_control, "OpenWindow"):
			open_window_ids.append(str(control_id))
	if policy_ids.size() != open_window_ids.size() \
			or not policy_ids.all(func(control_id): return control_id in open_window_ids) \
			or not open_window_ids.all(func(control_id): return control_id in policy_ids):
		errors.append(_error(Errors.CONTROL_BINDING, path + ".actions",
			"System Menu policy must own every same-Window OpenWindow Control exactly once"))
	for control_id in adapter.get("actions", {}):
		var control: Variant = declared.get(str(control_id))
		var route: Dictionary = adapter.actions[control_id]
		if not control is Dictionary or str(control.get("type", "")) != "Button" \
				or not _has_action(control, "OpenWindow") \
				or str(control.get("value", {}).get("target_window", "")) != str(route.target):
			errors.append(_error(Errors.CONTROL_BINDING,
				path + ".actions." + str(control_id),
				"System Menu policy must map a same-Window OpenWindow Button and exact target"))


static func _validate_chat_room(adapter: Dictionary, controls: Array,
		path: String, errors: Array[Dictionary]) -> void:
	var initialized := ChatRoomWindowState.initialize(adapter)
	if not initialized.get("ok", false):
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path,
			str(initialized.get("error", {}).get("detail", "invalid Chat Room adapter"))))
	var declared := _declared_controls(controls)
	var mappings: Variant = adapter.get("controls")
	if not mappings is Dictionary:
		errors.append(_error(Errors.CONTROL_BINDING, path + ".controls",
			"Chat Room adapter requires Control mappings"))
		return
	var input_id := str(mappings.get("input", ""))
	var scroll_id := str(mappings.get("scroll", ""))
	if not declared.get(input_id) is Dictionary \
			or str(declared[input_id].get("type", "")) != "TextField" \
			or not _has_action(declared[input_id], "SetChatDraft"):
		errors.append(_error(Errors.CONTROL_BINDING, path + ".controls.input",
			"Chat input must map a TextField bound to SetChatDraft"))
	if not declared.get(scroll_id) is Dictionary \
			or str(declared[scroll_id].get("type", "")) != "ScrollView" \
			or not _has_action(declared[scroll_id], "ScrollChatLog"):
		errors.append(_error(Errors.CONTROL_BINDING, path + ".controls.scroll",
			"Chat log must map a ScrollView bound to ScrollChatLog"))


static func _validate_status_presentation(presentation: Variant,
		attributes: Variant, derived: Variant, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	if not presentation is Dictionary:
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path,
			"Status presentation must be a manifest-owned object"))
		return
	_validate_asset(str(presentation.get("font", "")), path + ".font",
		errors, asset_exists)
	if not _positive_number(presentation.get("font_size")) \
			or str(presentation.get("font_color", "")).is_empty() \
			or str(presentation.get("background", "")).is_empty():
		errors.append(_error(Errors.INVALID_STATE_SET, path,
			"Status presentation requires font size, font color, and background"))
	_validate_geometry(presentation.get("points"), path + ".points", errors)
	for field in ["attribute_values", "attribute_costs"]:
		var geometries: Variant = presentation.get(field)
		if not geometries is Dictionary or not attributes is Dictionary \
				or geometries.keys().size() != attributes.keys().size() \
				or not attributes.keys().all(func(control_id):
					return geometries.has(control_id)):
			errors.append(_error(Errors.CONTROL_BINDING, path + "." + field,
				"Status attribute presentation must map every adapter Control"))
			continue
		for control_id in geometries:
			_validate_geometry(geometries[control_id],
				path + "." + field + "." + str(control_id), errors)
	var derived_values: Variant = presentation.get("derived_values")
	if not derived_values is Dictionary or not derived is Dictionary \
			or derived_values.keys().size() != derived.keys().size() \
			or not derived.keys().all(func(derived_id):
				return derived_values.has(derived_id)):
		errors.append(_error(Errors.CONTROL_BINDING, path + ".derived_values",
			"Status derived presentation must map every derived rule"))
		return
	for derived_id in derived_values:
		_validate_geometry(derived_values[derived_id],
			path + ".derived_values." + str(derived_id), errors)


static func _declared_controls(controls: Array) -> Dictionary:
	var declared := {}
	for control in controls:
		if control is Dictionary:
			declared[str(control.get("id", ""))] = control
	return declared


static func _has_action(control: Dictionary, action: String) -> bool:
	return control.get("actions", []).any(func(binding):
		return binding is Dictionary and str(binding.get("action", "")) == action)


static func _validate_asset(resource: String, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	var exists := ResourceLoader.exists(resource) \
		if asset_exists.is_null() else bool(asset_exists.call(resource))
	if resource.is_empty() or not exists:
		errors.append(_error(Errors.ASSET_INTEGRITY, path,
			"declared adapter asset does not exist: %s" % resource))


static func _validate_geometry(value: Variant, path: String,
		errors: Array[Dictionary]) -> void:
	if not value is Dictionary or not ["x", "y", "width", "height"].all(
			func(field): return _number(value.get(field))) \
			or float(value.get("width", 0)) <= 0.0 \
			or float(value.get("height", 0)) <= 0.0:
		errors.append(_error(Errors.INVALID_GEOMETRY, path,
			"geometry requires numeric x/y and positive width/height"))


static func _number(value: Variant) -> bool:
	return (value is int or value is float) and not value is bool \
		and is_finite(float(value))


static func _positive_number(value: Variant) -> bool:
	return _number(value) and float(value) > 0.0


static func _error(code: String, path: String, detail: String) -> Dictionary:
	return {"code": code, "path": path, "detail": detail}
