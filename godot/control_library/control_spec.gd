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
	"Drag", "DragDrop", "Resize", "Wheel", "KeyCommand",
]


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
	var plates: Variant = window.get("plates")
	if not plates is Dictionary:
		errors.append(_error(Errors.ASSET_INTEGRITY, path + ".plates",
			"expanded and minimized plates are required"))
	else:
		_validate_asset(str(plates.get("expanded", "")), path + ".plates.expanded",
			errors, asset_exists)
		_validate_asset(str(plates.get("minimized", "")), path + ".plates.minimized",
			errors, asset_exists)
	var controls: Variant = window.get("controls")
	if not controls is Array or controls.is_empty():
		errors.append(_error(Errors.INVALID_CONTROL_SPEC, path + ".controls",
			"Window must contain at least one Control"))
		return
	for control_index in controls.size():
		_validate_control(controls[control_index], window_id, control_index,
			control_ids, errors, asset_exists)


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
	var gestures: Variant = control.get("gestures")
	if not gestures is Array or gestures.is_empty():
		errors.append(_error(Errors.UNSUPPORTED_GESTURE, path + ".gestures",
			"at least one shared Gesture Capability is required"))
	else:
		for gesture in gestures:
			if gesture not in GESTURES:
				errors.append(_error(Errors.UNSUPPORTED_GESTURE, path + ".gestures",
					"unsupported gesture: %s" % str(gesture)))
	_validate_actions(control.get("actions"), gestures, path + ".actions", errors)


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


static func _validate_actions(actions: Variant, gestures: Variant, path: String,
		errors: Array[Dictionary]) -> void:
	if not actions is Array or actions.is_empty():
		errors.append(_error(Errors.CONTROL_BINDING, path,
			"at least one gesture-to-action binding is required"))
		return
	var declared: Array = gestures if gestures is Array else []
	for action_index in actions.size():
		var action: Variant = actions[action_index]
		if not action is Dictionary or str(action.get("action", "")).is_empty() \
				or action.get("gesture") not in declared:
			errors.append(_error(Errors.CONTROL_BINDING, "%s[%d]" % [path, action_index],
				"binding must name a declared gesture and non-empty Window Action"))


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
