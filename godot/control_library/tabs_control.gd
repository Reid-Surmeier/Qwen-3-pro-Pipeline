class_name TabsControl
extends Control
## Render/input adapter for Tabs. It owns pointer phases and emits only the
## normalized Activate Gesture Capability with a stable tab ID.

signal changed(control_id: String, result: Dictionary)

var spec: Dictionary
var runtime: ControlRuntime
var surfaces := {}


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
		var surface := TextureRect.new()
		surface.name = str(choice).to_pascal_case()
		surface.position = Vector2(float(surface_spec.geometry.x),
			float(surface_spec.geometry.y))
		surface.size = Vector2(float(surface_spec.geometry.width),
			float(surface_spec.geometry.height))
		surface.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		surface.stretch_mode = TextureRect.STRETCH_KEEP
		surface.mouse_filter = Control.MOUSE_FILTER_STOP
		surface.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		surface.mouse_entered.connect(_phase.bind(str(choice), "hover"))
		surface.mouse_exited.connect(_phase.bind(str(choice), "idle"))
		surface.gui_input.connect(_tab_input.bind(str(choice)))
		add_child(surface)
		surfaces[str(choice)] = surface
	_refresh()


func _phase(choice: String, phase: String) -> void:
	runtime.set_interaction_phase(spec.id, phase, choice)
	_refresh()
	changed.emit(spec.id, {"ok": true, "phase": phase, "surface": choice})


func _tab_input(event: InputEvent, choice: String) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			runtime.set_interaction_phase(spec.id, "pressed", choice)
			_refresh()
			changed.emit(spec.id, {"ok": true, "phase": "pressed", "surface": choice})
		else:
			var result: Dictionary = runtime.dispatch(spec.id, "Activate", {
				"choice": choice,
				"position": [event.position.x, event.position.y],
				"global_position": [event.global_position.x, event.global_position.y],
			})
			runtime.set_interaction_phase(spec.id, "hover", choice)
			_refresh()
			changed.emit(spec.id, result)
		accept_event()


func rendered_facts() -> Dictionary:
	return {"selected_tab": str(runtime.qa_state().controls[spec.id].get("value", ""))}


func refresh() -> void:
	_refresh()


func _refresh() -> void:
	if surfaces.is_empty():
		return
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	for choice in surfaces:
		var semantic := "selected" if choice == str(state.value) else "unselected"
		var phase := str(state.interaction_phase) if state.active_surface == choice else "idle"
		surfaces[choice].texture = load(str(
			spec.surfaces[choice].state_set[semantic][phase]))
