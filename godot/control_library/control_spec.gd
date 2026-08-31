class_name ControlSpec
extends RefCounted
## Validator for the frozen manifest seam defined by issues #124 and #125.
## Validation is pure: it returns factual errors and never constructs a
## partially interactive Window.

const Errors = preload("res://control_library/control_errors.gd")

const SCHEMA_VERSION := 3
const CONTROL_TYPES := [
	"Window", "Button", "Toggle", "ChoiceGroup", "Tabs", "Range",
	"ScrollView", "Dropdown", "SelectionView", "Stepper", "TextField", "Meter",
]
const INTERACTION_PHASES := ["idle", "hover", "pressed"]
const GESTURES := [
	"Activate", "ContextActivate", "DoubleActivate", "ModifierActivate",
	"ModifierDoubleActivate", "Drag", "DragDrop", "Resize", "Wheel", "KeyCommand",
]
const ACTIONS_BY_TYPE := {
	"Window": ["MoveWindow", "ResizeWindow", "CloseWindow"],
	"Button": ["ToggleMinimized", "CloseWindow", "ToggleSkillView",
		"CommitSkillChanges", "CancelSkillChanges", "ToggleStorageView",
		"SortStorage", "FocusStorageSearch"],
	"Toggle": ["ToggleValue"],
	"Range": ["StepRange", "SetRange"],
	"Dropdown": ["ToggleDropdown", "SelectChoice", "DismissDropdown"],
	"ChoiceGroup": ["SelectChoice"],
	"Tabs": ["SelectInventoryTab", "SelectStorageCategory"],
	"SelectionView": ["SelectSkill", "OpenSkillDetail", "SelectInventoryItem",
		"OpenInventoryItem", "ToggleInventorySelection", "MoveInventoryItem",
		"SelectStorageItem", "ToggleStorageSelection", "TransferStorageItem",
		"TransferInventoryItem"],
	"Stepper": ["StepSkill"],
	"ScrollView": ["ScrollStorage", "StepStorageScroll", "SetStorageScrollOffset",
		"ScrollEquipmentCard", "StepEquipmentCardScroll",
		"SetEquipmentCardScrollOffset"],
	"TextField": ["FilterStorage"],
}


static func load_and_validate(path: String, asset_exists: Callable = Callable()) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {"manifest": {}, "errors": [_error(Errors.INVALID_CONTROL_SPEC, path,
			"manifest file does not exist")]}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if not parsed is Dictionary:
		return {"manifest": {}, "errors": [_error(Errors.INVALID_CONTROL_SPEC, path,
			"manifest root must be an object")]}
	return {"manifest": parsed, "errors": validate(parsed, asset_exists)}


static func validate(manifest: Variant, asset_exists: Callable = Callable()) -> Array[Dictionary]:
	var errors: Array[Dictionary] = []
	if not manifest is Dictionary:
		return [_error(Errors.INVALID_CONTROL_SPEC, "$", "manifest root must be an object")]
	if manifest.get("schema_version") != SCHEMA_VERSION:
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, "$.schema_version",
			"expected schema version %d" % SCHEMA_VERSION))
	_validate_reference(manifest.get("reference"), errors, asset_exists)
	var windows: Variant = manifest.get("windows")
	if not windows is Array or windows.is_empty():
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, "$.windows",
			"at least one Window is required"))
		return errors
	var window_ids := {}
	var control_ids := {}
	for window_index in windows.size():
		_validate_window(windows[window_index], window_index, window_ids, control_ids,
			errors, asset_exists)
	return errors


static func _validate_reference(reference: Variant, errors: Array[Dictionary],
		asset_exists: Callable) -> void:
	if not reference is Dictionary:
		errors.append(_error(Errors.VISUAL_AUTHORITY, "$.reference",
			"hash-locked Reference Screen is required"))
		return
	var sha := str(reference.get("sha256", ""))
	if not _is_sha256(sha):
		errors.append(_error(Errors.VISUAL_AUTHORITY, "$.reference.sha256",
			"expected 64 lowercase hexadecimal characters"))
	var size: Variant = reference.get("size")
	if not size is Array or size.size() != 2 or not _positive_number(size[0]) \
			or not _positive_number(size[1]):
		errors.append(_error(Errors.INVALID_GEOMETRY, "$.reference.size",
			"Reference Screen size must contain two positive numbers"))
	_validate_asset(str(reference.get("path", "")), "$.reference.path", errors, asset_exists)


static func _validate_window(window: Variant, window_index: int, window_ids: Dictionary,
		control_ids: Dictionary, errors: Array[Dictionary], asset_exists: Callable) -> void:
	var path := "$.windows[%d]" % window_index
	if not window is Dictionary:
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path, "Window must be an object"))
		return
	var window_id := str(window.get("id", ""))
	if window_id.is_empty() or window_ids.has(window_id):
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path + ".id",
			"Window id must be non-empty and unique"))
	else:
		window_ids[window_id] = true
	_validate_geometry(window.get("geometry"), path + ".geometry", errors)
	var gestures: Variant = window.get("gestures")
	_validate_gestures(gestures, path + ".gestures", errors)
	_validate_actions(window.get("actions"), gestures, "Window",
		path + ".actions", errors)
	var plates: Variant = window.get("plates")
	if not plates is Dictionary:
		errors.append(_error(Errors.ASSET_INTEGRITY, path + ".plates",
			"expanded and minimized plates are required"))
	else:
		_validate_asset(str(plates.get("expanded", "")), path + ".plates.expanded",
			errors, asset_exists)
		_validate_asset(str(plates.get("minimized", "")), path + ".plates.minimized",
			errors, asset_exists)
		if plates.has("list"):
			_validate_asset(str(plates.get("list", "")), path + ".plates.list",
				errors, asset_exists)
	if window.has("drag_geometry"):
		_validate_geometry(window.drag_geometry, path + ".drag_geometry", errors)
	if "Resize" in (gestures if gestures is Array else []):
		_validate_resize_contract(window.get("resize"), window.get("geometry"),
			window.get("controls"),
			path + ".resize", errors, asset_exists)
	elif window.has("resize"):
		errors.append(_error(Errors.CONTROL_BINDING, path + ".resize",
			"resize geometry requires the shared Resize Gesture Capability"))
	var controls: Variant = window.get("controls")
	if not controls is Array or controls.is_empty():
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path + ".controls",
			"Window must contain at least one Control"))
		return
	var requires_list_plate: bool = controls.any(func(control):
		if not control is Dictionary:
			return false
		var actions: Variant = control.get("actions", [])
		return actions is Array and actions.any(func(binding):
			return binding is Dictionary and binding.get("action") in [
				"ToggleSkillView", "ToggleStorageView"]))
	if requires_list_plate and (not plates is Dictionary or not plates.has("list")):
		errors.append(_error(Errors.ASSET_INTEGRITY, path + ".plates.list",
			"a list plate is required when ToggleSkillView is bound"))
	for control_index in controls.size():
		_validate_control(controls[control_index], window_id, control_index,
			control_ids, errors, asset_exists)
	_validate_selection_value_controls(controls, window_id, path, errors)
	_validate_linked_selection_controls(controls, path, errors)
	if window.has("minimized_controls"):
		_validate_minimized_controls(window.minimized_controls, controls,
			path + ".minimized_controls", errors)


static func _validate_minimized_controls(value: Variant, controls: Array,
		path: String, errors: Array[Dictionary]) -> void:
	if not value is Array or value.is_empty():
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path,
			"minimized Controls must be a non-empty array"))
		return
	var declared := {}
	for control in controls:
		if control is Dictionary:
			declared[str(control.get("id", ""))] = control
	var seen := {}
	var has_restore := false
	for index in value.size():
		var control_id := str(value[index])
		if control_id.is_empty() or seen.has(control_id) or not declared.has(control_id):
			errors.append(_error(Errors.INVALID_CONTROL_SPEC,
				"%s[%d]" % [path, index],
				"minimized Control must be unique and belong to this Window"))
		else:
			seen[control_id] = true
			var actions: Variant = declared[control_id].get("actions", [])
			has_restore = has_restore or (actions is Array and actions.any(func(binding):
				return binding is Dictionary and binding.get("action") == "ToggleMinimized"))
	if not has_restore:
		errors.append(_error(Errors.CONTROL_BINDING, path,
			"minimized Controls must retain a ToggleMinimized restore action"))


static func _validate_linked_selection_controls(controls: Array, path: String,
		errors: Array[Dictionary]) -> void:
	var declared := {}
	for control in controls:
		if control is Dictionary:
			declared[str(control.get("id", ""))] = control
	for index in controls.size():
		var control: Variant = controls[index]
		if not control is Dictionary or str(control.get("type", "")) not in [
				"ScrollView", "TextField"]:
			continue
		var value: Variant = control.get("value", {})
		if str(control.get("type", "")) == "ScrollView" and value is Dictionary \
				and value.get("available", true) == false:
			continue
		var linked_id := str(value.get("selection_control_id", "")) \
			if value is Dictionary else ""
		if linked_id.is_empty() or not declared.has(linked_id) \
				or str(declared[linked_id].get("type", "")) != "SelectionView":
			errors.append(_error(Errors.CONTROL_BINDING,
				"%s.controls[%d].value.selection_control_id" % [path, index],
				"linked Control must be a SelectionView declared in the same Window"))


static func _validate_control(control: Variant, window_id: String, control_index: int,
		control_ids: Dictionary, errors: Array[Dictionary], asset_exists: Callable) -> void:
	var path := "$.windows[%s].controls[%d]" % [window_id, control_index]
	if not control is Dictionary:
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path, "Control must be an object"))
		return
	var control_id := str(control.get("id", ""))
	if control_id.is_empty() or not control_id.begins_with(window_id + ".") \
			or control_ids.has(control_id):
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path + ".id",
			"Control id must be globally unique and prefixed by its Window id"))
	else:
		control_ids[control_id] = true
	var control_type := str(control.get("type", ""))
	if control_type not in CONTROL_TYPES:
		errors.append(_error(Errors.UNKNOWN_CONTROL_TYPE, path + ".type",
			"unknown Control Library type: %s" % control_type))
	_validate_geometry(control.get("geometry"), path + ".geometry", errors)
	var phases: Variant = control.get("interaction_phases")
	if not phases is Array or not _contains_all(phases, INTERACTION_PHASES):
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".interaction_phases",
			"idle, hover, and pressed phases are required"))
	var semantic_states: Variant = control.get("semantic_states")
	var initial := str(control.get("initial_semantic_state", ""))
	if not semantic_states is Array or semantic_states.is_empty() or initial not in semantic_states:
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".semantic_states",
			"semantic states must be non-empty and contain the initial state"))
	else:
		_validate_state_set(control.get("state_set"), semantic_states, phases,
			path + ".state_set", errors, asset_exists)
	if control.has("surfaces"):
		_validate_surfaces(control.surfaces, path + ".surfaces", errors, asset_exists)
	_validate_type_contract(control, control_type, path, errors, asset_exists)
	var gestures: Variant = control.get("gestures")
	_validate_gestures(gestures, path + ".gestures", errors)
	_validate_actions(control.get("actions"), gestures, control_type,
		path + ".actions", errors)


static func _validate_type_contract(control: Dictionary, control_type: String,
		path: String, errors: Array[Dictionary], asset_exists: Callable) -> void:
	if control_type == "Toggle":
		var states: Variant = control.get("semantic_states")
		if not states is Array or states.size() != 2 or states[0] == states[1]:
			errors.append(_error(Errors.INVALID_STATE_SET, path + ".semantic_states",
				"Toggle requires exactly two distinct semantic states"))
	elif control_type == "Range":
		_validate_range_contract(control, path, errors)
	elif control_type == "Dropdown" or control_type == "ChoiceGroup":
		_validate_choice_contract(control, control_type, path, errors)
	elif control_type == "Tabs":
		_validate_choice_contract(control, control_type, path, errors)
	elif control_type == "SelectionView":
		_validate_selection_view_contract(control, path, errors, asset_exists)
	elif control_type == "Stepper":
		_validate_stepper_contract(control, path, errors)
	elif control_type == "ScrollView":
		_validate_scroll_view_contract(control, path, errors)
	elif control_type == "TextField":
		_validate_text_field_contract(control, path, errors, asset_exists)


static func _validate_range_contract(control: Dictionary, path: String,
		errors: Array[Dictionary]) -> void:
	var value: Variant = control.get("value")
	var valid := value is Dictionary
	if valid:
		for field in ["minimum", "maximum", "initial", "arrow_step", "wheel_step"]:
			valid = valid and _number(value.get(field))
	if valid:
		valid = float(value.minimum) < float(value.maximum) \
			and float(value.initial) >= float(value.minimum) \
			and float(value.initial) <= float(value.maximum) \
			and float(value.arrow_step) > 0.0 and float(value.wheel_step) > 0.0
	if not valid:
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".value",
			"Range requires ordered bounds, an in-range initial value, and positive steps"))
	var surfaces: Variant = control.get("surfaces")
	if not surfaces is Dictionary or not ["track", "thumb", "decrement", "increment"].all(
			func(surface): return surfaces.has(surface)):
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path + ".surfaces",
			"Range requires track, thumb, decrement, and increment surfaces"))


static func _validate_choice_contract(control: Dictionary, control_type: String,
		path: String, errors: Array[Dictionary]) -> void:
	var value: Variant = control.get("value")
	var choices: Array = value.get("choices", []) if value is Dictionary else []
	var initial: Variant = value.get("initial") if value is Dictionary else null
	var unique := {}
	var valid := not choices.is_empty()
	for choice in choices:
		valid = valid and choice is String and not str(choice).is_empty() and not unique.has(choice)
		unique[choice] = true
	valid = valid and initial in choices
	if not valid:
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".value",
			"%s requires unique non-empty choices and a declared initial choice" % control_type))
	var surfaces: Variant = control.get("surfaces")
	if control_type == "Dropdown":
		if not surfaces is Dictionary or not surfaces.has("field") or not surfaces.has("arrow"):
			errors.append(_error(Errors.INVALID_CONTROL_SPEC, path + ".surfaces",
				"Dropdown requires field and arrow surfaces"))
		var tokens: Variant = control.get("tokens")
		if not tokens is Dictionary or not ["fill", "border", "highlight", "text"].all(
				func(token): return tokens.has(token) and not str(tokens[token]).is_empty()):
			errors.append(_error(Errors.INVALID_STATE_SET, path + ".tokens",
				"Dropdown requires fill, border, highlight, and text tokens"))
	else:
		if not surfaces is Dictionary or not choices.all(func(choice):
				return surfaces.has(str(choice)) and surfaces[str(choice)] is Dictionary \
				and surfaces[str(choice)].has("geometry") \
				and surfaces[str(choice)].has("state_set") \
				and surfaces[str(choice)].state_set.has("selected") \
				and surfaces[str(choice)].state_set.has("unselected")):
			errors.append(_error(Errors.INVALID_STATE_SET, path + ".surfaces",
				"%s requires selected/unselected State Sets for every choice" % control_type))


static func _validate_selection_view_contract(control: Dictionary, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	var value: Variant = control.get("value")
	var items: Array = value.get("items", []) if value is Dictionary else []
	var initial: Variant = value.get("initial") if value is Dictionary else null
	var unique := {}
	var valid := not items.is_empty()
	for item in items:
		valid = valid and item is String and not str(item).is_empty() and not unique.has(item)
		unique[item] = true
	valid = valid and initial in items
	var details: Variant = value.get("details") if value is Dictionary else null
	valid = valid and details is Dictionary and items.all(func(item):
		return details.has(str(item)) and details[item] is String \
			and not str(details[item]).is_empty())
	if not valid:
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".value",
			"SelectionView requires unique items, an initial item, and detail text for every item"))
	var gestures: Array = control.get("gestures", []) \
		if control.get("gestures", []) is Array else []
	if "DoubleActivate" in gestures:
		var detail_view: Variant = value.get("detail_view") if value is Dictionary else null
		var detail_size: Variant = detail_view.get("size") \
			if detail_view is Dictionary else null
		var detail_offset: Variant = detail_view.get("offset") \
			if detail_view is Dictionary else null
		var detail_padding: Variant = detail_view.get("padding") \
			if detail_view is Dictionary else null
		var detail_valid: bool = detail_view is Dictionary \
			and detail_size is Array and detail_size.size() == 2 \
			and _positive_number(detail_size[0]) and _positive_number(detail_size[1]) \
			and detail_offset is Array and detail_offset.size() == 2 \
			and _number(detail_offset[0]) and _number(detail_offset[1]) \
			and detail_padding is Array and detail_padding.size() == 2 \
			and _number(detail_padding[0]) and float(detail_padding[0]) >= 0.0 \
			and _number(detail_padding[1]) and float(detail_padding[1]) >= 0.0 \
			and float(detail_padding[0]) * 2.0 < float(detail_size[0]) \
			and float(detail_padding[1]) * 2.0 < float(detail_size[1]) \
			and _positive_number(detail_view.get("font_size")) \
			and not str(detail_view.get("font_color", "")).is_empty()
		if not detail_valid:
			errors.append(_error(Errors.INVALID_STATE_SET, path + ".value.detail_view",
				"DoubleActivate requires a complete manifest-owned detail view"))
		else:
			_validate_state_set(detail_view.get("state_set"), ["ready"],
				INTERACTION_PHASES, path + ".value.detail_view.state_set",
				errors, asset_exists)
			_validate_asset(str(detail_view.get("font", "")),
				path + ".value.detail_view.font", errors, asset_exists)
	if "ModifierActivate" in gestures or "ModifierDoubleActivate" in gestures:
		var allowed: Variant = value.get("allowed_modifiers") if value is Dictionary else null
		if not allowed is Array or allowed != ["ctrl"]:
			errors.append(_error(Errors.INVALID_MODIFIER,
				path + ".value.allowed_modifiers",
				"ModifierActivate requires exactly the Control modifier"))
	if "DragDrop" in gestures:
		var item_values: Variant = value.get("item_values") if value is Dictionary else null
		var item_identities: Array = item_values.values() if item_values is Dictionary else []
		var unique_identities := {}
		for identity in item_identities:
			unique_identities[str(identity)] = true
		if not item_values is Dictionary or item_values.keys().size() != items.size() \
				or not items.all(func(item): return item_values.has(str(item)) \
					and item_values[item] is String and str(item_values[item]) in items) \
				or unique_identities.size() != items.size():
			errors.append(_error(Errors.INVALID_STATE_SET, path + ".value.item_values",
				"DragDrop item values must be a permutation of declared item identities"))
		var targets: Variant = value.get("drop_targets") if value is Dictionary else null
		if not targets is Array or targets.is_empty() or not targets.all(func(target):
			return target in items):
			errors.append(_error(Errors.INVALID_DROP_TARGET, path + ".value.drop_targets",
				"every DragDrop target must be a declared SelectionView item"))
		var version: Variant = value.get("initial_version") if value is Dictionary else null
		if not _number(version) or float(version) < 0.0 or float(version) != floorf(float(version)):
			errors.append(_error(Errors.GESTURE_CONFLICT, path + ".value.initial_version",
				"DragDrop requires a non-negative transaction version"))
	var surfaces: Variant = control.get("surfaces")
	var required_surface_states := ["selected", "unselected"]
	if "ModifierActivate" in gestures or "ModifierDoubleActivate" in gestures:
		required_surface_states.append("modifier_selected")
	if "DragDrop" in gestures:
		required_surface_states.append_array(["dragging", "drop_target"])
	if not surfaces is Dictionary or not items.all(func(item):
		return surfaces.has(str(item)) and surfaces[str(item)] is Dictionary \
			and surfaces[str(item)].has("geometry") \
			and surfaces[str(item)].has("state_set") \
			and required_surface_states.all(func(state):
				return surfaces[str(item)].state_set.has(state))):
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".surfaces",
			"SelectionView requires every declared item visual State Set"))
	var value_control_ids: Variant = value.get("value_control_ids", {}) \
		if value is Dictionary else null
	if not value_control_ids is Dictionary or not value_control_ids.keys().all(func(item):
		return item in items and value_control_ids[item] is String \
			and not str(value_control_ids[item]).is_empty()):
		errors.append(_error(Errors.CONTROL_BINDING, path + ".value.value_control_ids",
			"SelectionView value Control ids must map declared items to non-empty ids"))


static func _validate_selection_value_controls(controls: Array, window_id: String,
		path: String, errors: Array[Dictionary]) -> void:
	var declared := {}
	for control in controls:
		if control is Dictionary:
			declared[str(control.get("id", ""))] = control
	for index in controls.size():
		var control: Variant = controls[index]
		if not control is Dictionary or control.get("type") != "SelectionView":
			continue
		var value: Variant = control.get("value")
		var mappings: Variant = value.get("value_control_ids", {}) \
			if value is Dictionary else {}
		if not mappings is Dictionary:
			continue
		for item in mappings:
			var related_id := str(mappings[item])
			if not related_id.begins_with(window_id + ".") or not declared.has(related_id):
				errors.append(_error(Errors.CONTROL_BINDING,
					"%s.controls[%d].value.value_control_ids.%s" % [path, index, str(item)],
					"related value Control must belong to this Window and be declared"))


static func _validate_gestures(gestures: Variant, path: String,
		errors: Array[Dictionary]) -> void:
	if not gestures is Array or gestures.is_empty():
		errors.append(_error(Errors.UNSUPPORTED_GESTURE, path,
			"at least one shared Gesture Capability is required"))
		return
	for gesture in gestures:
		if gesture not in GESTURES:
			errors.append(_error(Errors.UNSUPPORTED_GESTURE, path,
				"unsupported gesture: %s" % str(gesture)))


static func _validate_resize_contract(resize: Variant, window_geometry: Variant,
		controls: Variant, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	if not resize is Dictionary:
		errors.append(_error(Errors.INVALID_GEOMETRY, path,
			"Resize requires grip geometry and minimum/maximum sizes"))
		return
	_validate_geometry(resize.get("grip_geometry"), path + ".grip_geometry", errors)
	var minimum: Variant = resize.get("minimum")
	var maximum: Variant = resize.get("maximum")
	var valid: bool = minimum is Array and maximum is Array \
		and minimum.size() == 2 and maximum.size() == 2 \
		and _positive_number(minimum[0]) and _positive_number(minimum[1]) \
		and _positive_number(maximum[0]) and _positive_number(maximum[1])
	if valid:
		valid = float(minimum[0]) <= float(maximum[0]) \
			and float(minimum[1]) <= float(maximum[1])
	if not valid:
		errors.append(_error(Errors.INVALID_GEOMETRY, path,
			"Resize minimum must be positive and no larger than maximum"))
	_validate_state_set(resize.get("state_set"), ["ready"], INTERACTION_PHASES,
		path + ".state_set", errors, asset_exists)
	var frame: Variant = resize.get("frame") if resize is Dictionary else null
	if not frame is Dictionary:
		errors.append(_error(Errors.INVALID_GEOMETRY, path + ".frame",
			"Resize requires a complete manifest-owned frame Assembly"))
		return
	for field in ["title_fill", "footer", "footer_fill", "right_edge"]:
		_validate_asset(str(frame.get(field, "")), path + ".frame." + field,
			errors, asset_exists)
	var home_size: Variant = frame.get("home_size")
	var dimensions_valid: bool = home_size is Array and home_size.size() == 2 \
		and _positive_number(home_size[0]) and _positive_number(home_size[1]) \
		and _positive_number(frame.get("title_height")) \
		and _positive_number(frame.get("footer_height")) \
		and _positive_number(frame.get("right_edge_width"))
	if not dimensions_valid:
		errors.append(_error(Errors.INVALID_GEOMETRY, path + ".frame",
			"Resize frame sizes must be present and positive"))
	for field in ["stale_title_controls_geometry", "stale_footer_geometry",
			"stale_footer_grip_geometry", "stale_right_edge_geometry"]:
		_validate_geometry(frame.get(field), path + ".frame." + field, errors)
	var grip: Variant = resize.get("grip_geometry")
	var title_cover: Variant = frame.get("stale_title_controls_geometry")
	var footer_cover: Variant = frame.get("stale_footer_geometry")
	var grip_cover: Variant = frame.get("stale_footer_grip_geometry")
	var right_cover: Variant = frame.get("stale_right_edge_geometry")
	var relationships_valid: bool = valid and dimensions_valid \
		and window_geometry is Dictionary and grip is Dictionary \
		and title_cover is Dictionary and footer_cover is Dictionary \
		and grip_cover is Dictionary and right_cover is Dictionary
	if relationships_valid:
		var home_width := float(home_size[0])
		var home_height := float(home_size[1])
		var title_height := float(frame.title_height)
		var footer_height := float(frame.footer_height)
		var edge_width := float(frame.right_edge_width)
		relationships_valid = float(window_geometry.get("width", -1)) == home_width \
			and float(window_geometry.get("height", -1)) == home_height \
			and float(minimum[0]) <= home_width and home_width <= float(maximum[0]) \
			and float(minimum[1]) <= home_height and home_height <= float(maximum[1]) \
			and float(grip.get("x", -1)) + float(grip.get("width", -1)) == home_width \
			and float(grip.get("y", -1)) + float(grip.get("height", -1)) == home_height \
			and grip == grip_cover \
			and float(title_cover.get("y", -1)) == 0.0 \
			and float(title_cover.get("height", -1)) == title_height \
			and float(title_cover.get("x", -1)) + float(title_cover.get("width", -1)) == home_width \
			and float(footer_cover.get("x", -1)) == 0.0 \
			and float(footer_cover.get("width", -1)) == home_width \
			and float(footer_cover.get("y", -1)) == home_height - footer_height - 1.0 \
			and float(footer_cover.get("height", -1)) == footer_height + 1.0 \
			and float(right_cover.get("x", -1)) + float(right_cover.get("width", -1)) == home_width \
			and float(right_cover.get("width", -1)) == edge_width \
			and float(right_cover.get("y", -1)) == title_height \
			and float(right_cover.get("y", -1)) + float(right_cover.get("height", -1)) \
				== home_height - footer_height
	if not relationships_valid:
		errors.append(_error(Errors.INVALID_GEOMETRY, path + ".frame",
			"Resize frame, home Window, grip, and stale-cover geometry must agree"))
	var anchored: Variant = frame.get("anchored_right_controls")
	var declared := {}
	if controls is Array:
		for control in controls:
			if control is Dictionary:
				declared[str(control.get("id", ""))] = true
	var anchored_valid: bool = anchored is Array and not anchored.is_empty()
	var seen := {}
	if anchored_valid:
		for control_id in anchored:
			var normalized := str(control_id)
			anchored_valid = anchored_valid and not normalized.is_empty() \
				and declared.has(normalized) and not seen.has(normalized)
			seen[normalized] = true
	if not anchored_valid:
		errors.append(_error(Errors.CONTROL_BINDING,
			path + ".frame.anchored_right_controls",
			"anchored right Controls must be unique declared Controls"))


static func _validate_stepper_contract(control: Dictionary, path: String,
		errors: Array[Dictionary]) -> void:
	var value: Variant = control.get("value")
	var valid := value is Dictionary
	if valid:
		for field in ["minimum", "maximum", "current", "target", "step"]:
			valid = valid and _number(value.get(field))
	if valid:
		valid = float(value.minimum) <= float(value.current) \
			and float(value.current) <= float(value.maximum) \
			and float(value.minimum) <= float(value.target) \
			and float(value.target) <= float(value.maximum) \
			and float(value.step) > 0.0
	if not valid:
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".value",
			"Stepper requires in-range current/target values and a positive step"))
	var surfaces: Variant = control.get("surfaces")
	if not surfaces is Dictionary or not ["decrement", "increment"].all(func(surface):
		return surfaces.has(surface) and surfaces[surface] is Dictionary \
			and surfaces[surface].has("geometry") \
			and surfaces[surface].has("state_set") \
			and surfaces[surface].state_set.has("visible") \
			and surfaces[surface].state_set.has("hidden")):
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".surfaces",
			"Stepper requires visible/hidden State Sets for both arrows"))


static func _validate_scroll_view_contract(control: Dictionary, path: String,
		errors: Array[Dictionary]) -> void:
	var value: Variant = control.get("value")
	var valid := value is Dictionary
	if valid:
		for field in ["minimum", "maximum", "initial", "wheel_rows", "arrow_rows"]:
			valid = valid and _number(value.get(field))
	if valid:
		valid = int(value.minimum) == 0 and int(value.maximum) >= int(value.minimum) \
			and int(value.initial) >= int(value.minimum) \
			and int(value.initial) <= int(value.maximum) \
			and int(value.wheel_rows) == 3 and int(value.arrow_rows) == 1
	var available := true
	if valid and value.has("available"):
		valid = value.available is bool
		available = bool(value.available)
	if valid:
		if available:
			valid = not str(value.get("selection_control_id", "")).is_empty()
		else:
			valid = int(value.minimum) == 0 and int(value.maximum) == 0 \
				and int(value.initial) == 0 \
				and not str(value.get("unavailable_reason", "")).is_empty()
	if not valid:
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".value",
			"ScrollView requires zero-based bounds, an in-range initial offset, three-row wheel and one-row arrow steps, plus a linked SelectionView or explicit zero-range unavailable authority"))
	var surfaces: Variant = control.get("surfaces")
	if not surfaces is Dictionary or not ["track", "thumb", "decrement", "increment"].all(
		func(surface): return surfaces.has(surface) and surfaces[surface] is Dictionary \
			and surfaces[surface].has("geometry")):
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path + ".surfaces",
			"ScrollView requires track, thumb, decrement, and increment surfaces"))


static func _validate_text_field_contract(control: Dictionary, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	var value: Variant = control.get("value")
	var valid := value is Dictionary and value.get("initial") is String \
		and _positive_number(value.get("maximum_length")) \
		and not str(value.get("accepted_pattern", "")).is_empty() \
		and not str(value.get("selection_control_id", "")).is_empty()
	if valid:
		var regex := RegEx.new()
		valid = regex.compile(str(value.accepted_pattern)) == OK
	if not valid:
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".value",
			"TextField requires initial text, a positive maximum length, a valid accepted pattern, and a linked SelectionView"))
	var tokens: Variant = control.get("tokens")
	if not tokens is Dictionary or not ["font", "font_size", "font_color"].all(
		func(token): return tokens.has(token) and not str(tokens[token]).is_empty()):
		errors.append(_error(Errors.INVALID_STATE_SET, path + ".tokens",
			"TextField requires font, font_size, and font_color tokens"))
	elif tokens is Dictionary:
		_validate_asset(str(tokens.font), path + ".tokens.font", errors, asset_exists)


static func _validate_surfaces(surfaces: Variant, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	if not surfaces is Dictionary or surfaces.is_empty():
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path,
			"nested surfaces must be a non-empty object"))
		return
	for surface_name in surfaces:
		var surface_path := path + "." + str(surface_name)
		var surface: Variant = surfaces[surface_name]
		if not surface is Dictionary:
			errors.append(_error(Errors.INVALID_CONTROL_SPEC, surface_path,
				"nested surface must be an object"))
			continue
		_validate_geometry(surface.get("geometry"), surface_path + ".geometry", errors)
		if surface.has("asset"):
			_validate_asset(str(surface.asset), surface_path + ".asset", errors, asset_exists)
		if surface.has("state_set"):
			_validate_surface_state_set(surface.state_set, surface_path + ".state_set",
				errors, asset_exists)


static func _validate_surface_state_set(state_set: Variant, path: String,
		errors: Array[Dictionary], asset_exists: Callable) -> void:
	if not state_set is Dictionary or state_set.is_empty():
		errors.append(_error(Errors.INVALID_STATE_SET, path,
			"nested surface State Set must be a non-empty object"))
		return
	for semantic_state in state_set:
		var variants: Variant = state_set[semantic_state]
		var state_path := path + "." + str(semantic_state)
		if not variants is Dictionary:
			errors.append(_error(Errors.INVALID_STATE_SET, state_path,
				"nested surface state must be an object"))
			continue
		for phase in INTERACTION_PHASES:
			if not variants.has(phase):
				errors.append(_error(Errors.INVALID_STATE_SET, state_path + "." + phase,
					"required nested visual state is missing"))
			else:
				_validate_asset(str(variants[phase]), state_path + "." + phase,
					errors, asset_exists)


static func _validate_state_set(state_set: Variant, semantic_states: Array,
		phases: Variant, path: String, errors: Array[Dictionary], asset_exists: Callable) -> void:
	if not state_set is Dictionary:
		errors.append(_error(Errors.INVALID_STATE_SET, path, "State Set must be an object"))
		return
	var required_phases: Array = phases if phases is Array else INTERACTION_PHASES
	for semantic_state in semantic_states:
		var state_path := path + "." + str(semantic_state)
		var variants: Variant = state_set.get(semantic_state)
		if not variants is Dictionary:
			errors.append(_error(Errors.INVALID_STATE_SET, state_path,
				"semantic state is missing its visual variants"))
			continue
		var required := ["idle"] if semantic_state == "disabled" else required_phases
		for phase in required:
			if not variants.has(phase):
				errors.append(_error(Errors.INVALID_STATE_SET, state_path + "." + str(phase),
					"required visual state is missing"))
			else:
				_validate_asset(str(variants[phase]), state_path + "." + str(phase),
					errors, asset_exists)


static func _validate_actions(actions: Variant, gestures: Variant, control_type: String,
		path: String,
		errors: Array[Dictionary]) -> void:
	if not actions is Array or actions.is_empty():
		errors.append(_error(Errors.CONTROL_BINDING, path,
			"at least one gesture-to-action binding is required"))
		return
	var declared: Array = gestures if gestures is Array else []
	var allowed: Array = ACTIONS_BY_TYPE.get(control_type, [])
	for action_index in actions.size():
		var action: Variant = actions[action_index]
		if not action is Dictionary or str(action.get("action", "")).is_empty() \
				or action.get("gesture") not in declared:
			errors.append(_error(Errors.CONTROL_BINDING, "%s[%d]" % [path, action_index],
				"binding must name a declared gesture and non-empty Window Action"))
		elif not allowed.is_empty() and str(action.action) not in allowed:
			errors.append(_error(Errors.ACTION_ROUTING, "%s[%d].action" % [path, action_index],
				"Window Action is not supported by %s: %s" % [control_type, str(action.action)]))
		elif control_type == "Window" and action.get("gesture") == "KeyCommand" \
				and str(action.get("key", "")).is_empty():
			errors.append(_error(Errors.CONTROL_BINDING, "%s[%d].key" % [path, action_index],
				"KeyCommand binding must name a key"))
	for gesture in declared:
		if not actions.any(func(action): return action is Dictionary \
			and action.get("gesture") == gesture):
			errors.append(_error(Errors.CONTROL_BINDING, path,
				"declared gesture has no Window Action: %s" % str(gesture)))


static func _validate_geometry(geometry: Variant, path: String,
		errors: Array[Dictionary]) -> void:
	if not geometry is Dictionary or not _number(geometry.get("x")) \
			or not _number(geometry.get("y")) or not _positive_number(geometry.get("width")) \
			or not _positive_number(geometry.get("height")):
		errors.append(_error(Errors.INVALID_GEOMETRY, path,
			"geometry requires numeric x/y and positive width/height"))


static func _validate_asset(path: String, field_path: String, errors: Array[Dictionary],
		asset_exists: Callable) -> void:
	if path.is_empty():
		errors.append(_error(Errors.ASSET_INTEGRITY, field_path, "asset path is required"))
		return
	var exists := ResourceLoader.exists(path) if asset_exists.is_null() else bool(asset_exists.call(path))
	if not exists:
		errors.append(_error(Errors.ASSET_INTEGRITY, field_path,
			"asset does not exist: %s" % path))


static func _contains_all(values: Array, required: Array) -> bool:
	return required.all(func(value): return value in values)


static func _is_sha256(value: String) -> bool:
	if value.length() != 64:
		return false
	for character in value:
		if character not in "0123456789abcdef":
			return false
	return true


static func _number(value: Variant) -> bool:
	return value is int or value is float


static func _positive_number(value: Variant) -> bool:
	return _number(value) and float(value) > 0.0


static func _error(code: String, path: String, detail: String) -> Dictionary:
	return {"code": code, "path": path, "detail": detail}
