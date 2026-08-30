class_name ChoiceGroupControl
extends Control
## Renderable single-selection adapter for the shared ChoiceGroup Control type.

signal changed(control_id: String, result: Dictionary)

const Errors = preload("res://control_library/control_errors.gd")

var spec: Dictionary
var runtime: ControlRuntime
var surfaces: Dictionary = {}


func configure(control_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = control_spec
	runtime = control_runtime
	name = str(spec.id).replace(".", "-")
	position = Vector2(float(spec.geometry.x), float(spec.geometry.y))
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	mouse_filter = Control.MOUSE_FILTER_PASS


func _ready() -> void:
	for choice in spec.value.choices:
		var surface_spec: Dictionary = spec.surfaces[str(choice)]
		var hit := TextureRect.new()
		hit.name = str(choice).to_pascal_case()
		hit.position = Vector2(float(surface_spec.geometry.x), float(surface_spec.geometry.y))
		hit.size = Vector2(float(surface_spec.geometry.width), float(surface_spec.geometry.height))
		hit.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		hit.stretch_mode = TextureRect.STRETCH_KEEP
		hit.mouse_filter = Control.MOUSE_FILTER_STOP
		hit.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		hit.mouse_entered.connect(_phase.bind(str(choice), "hover"))
		hit.mouse_exited.connect(_phase.bind(str(choice), "idle"))
		hit.gui_input.connect(_choice_input.bind(str(choice)))
		add_child(hit)
		surfaces[str(choice)] = hit
	_refresh()


func _phase(choice: String, phase: String) -> void:
	var result: Dictionary = runtime.set_interaction_phase(spec.id, phase, choice)
	_refresh()
	changed.emit(spec.id, result)


func _choice_input(event: InputEvent, choice: String) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			runtime.set_interaction_phase(spec.id, "pressed", choice)
			_refresh()
		else:
			var result: Dictionary = runtime.dispatch(spec.id, "Activate", {"choice": choice})
			runtime.set_interaction_phase(spec.id, "hover", choice)
			_refresh()
			changed.emit(spec.id, result)
		accept_event()


func _refresh() -> void:
	if surfaces.is_empty():
		return
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	for choice in surfaces:
		var semantic := "selected" if choice == str(state.value) else "unselected"
		var phase := str(state.interaction_phase) if state.active_surface == choice else "idle"
		surfaces[choice].texture = load(str(spec.surfaces[choice].state_set[semantic][phase]))


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
