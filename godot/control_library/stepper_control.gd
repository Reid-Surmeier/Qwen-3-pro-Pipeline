class_name StepperControl
extends Control
## Real-input/render adapter for a current/target Stepper. The semantic module
## owns one step; ControlRuntime owns the complete-Window pending transaction.

signal changed(control_id: String, result: Dictionary)

var spec: Dictionary
var runtime: ControlRuntime
var visuals := {}
var hits := {}
var text_background: ColorRect
var value_label: Label
var _held_surface := ""


func configure(control_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = control_spec
	runtime = control_runtime
	name = str(spec.id).replace(".", "-")
	position = _point(spec.geometry)
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	_add_text()
	for surface_name in ["decrement", "increment"]:
		_add_surface(surface_name, spec.surfaces[surface_name])
	_refresh()


func rendered_facts() -> Dictionary:
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	return {
		"current": state.current,
		"target": state.target,
		"arrows_visible": state.arrows_visible,
		"text_visible": value_label.visible,
	}


func refresh() -> void:
	_refresh()


func _add_text() -> void:
	var left_width := float(spec.surfaces.decrement.geometry.width)
	var right_width := float(spec.surfaces.increment.geometry.width)
	text_background = ColorRect.new()
	text_background.position = Vector2(left_width, 0)
	text_background.size = Vector2(size.x - left_width - right_width, size.y)
	text_background.color = Color8(252, 252, 252)
	text_background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(text_background)
	value_label = Label.new()
	value_label.position = text_background.position
	value_label.size = text_background.size
	value_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	value_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	value_label.add_theme_font_override("font", load("res://fonts/PixelMplus10-Regular.ttf"))
	value_label.add_theme_font_size_override("font_size", 13)
	value_label.add_theme_color_override("font_color", Color8(24, 24, 24))
	value_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(value_label)


func _add_surface(surface_name: String, surface: Dictionary) -> void:
	var visual := TextureRect.new()
	visual.name = surface_name + "-visual"
	visual.position = _point(surface.geometry)
	visual.size = Vector2(float(surface.geometry.width), float(surface.geometry.height))
	visual.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	visual.stretch_mode = TextureRect.STRETCH_KEEP
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(visual)
	visuals[surface_name] = visual
	var hit := Control.new()
	hit.name = surface_name + "-hit"
	hit.position = visual.position
	hit.size = visual.size
	hit.mouse_filter = Control.MOUSE_FILTER_STOP
	hit.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	hit.mouse_entered.connect(_entered.bind(surface_name))
	hit.mouse_exited.connect(_exited.bind(surface_name))
	hit.gui_input.connect(_surface_input.bind(surface_name))
	add_child(hit)
	hits[surface_name] = hit


func _entered(surface_name: String) -> void:
	if _held_surface.is_empty():
		runtime.set_interaction_phase(spec.id, "hover", surface_name)
		_refresh()
		changed.emit(spec.id, {"ok": true, "phase": "hover", "surface": surface_name})


func _exited(surface_name: String) -> void:
	if _held_surface.is_empty() and str(runtime.qa_state().controls[spec.id].active_surface) == surface_name:
		runtime.set_interaction_phase(spec.id, "idle")
		_refresh()
		changed.emit(spec.id, {"ok": true, "phase": "idle"})


func _surface_input(event: InputEvent, surface_name: String) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_held_surface = surface_name
			runtime.set_interaction_phase(spec.id, "pressed", surface_name)
			_refresh()
			changed.emit(spec.id, {"ok": true, "phase": "pressed", "surface": surface_name})
			accept_event()
		elif _held_surface == surface_name:
			_held_surface = ""
			var result: Dictionary = runtime.dispatch(spec.id, "Activate",
				{"direction": -1 if surface_name == "decrement" else 1,
				 "surface": surface_name,
				 "position": [event.position.x, event.position.y],
				 "global_position": [event.global_position.x, event.global_position.y]})
			runtime.set_interaction_phase(spec.id, "idle")
			_refresh()
			changed.emit(spec.id, result)
			accept_event()


func _refresh() -> void:
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	value_label.text = str(state.text)
	for surface_name in visuals:
		var path := runtime.visual_surface_asset(spec.id, surface_name)
		if not path.is_empty():
			visuals[surface_name].texture = load(path)
		visuals[surface_name].visible = bool(state.arrows_visible)
		hits[surface_name].visible = bool(state.arrows_visible)


func _point(geometry: Dictionary) -> Vector2:
	return Vector2(float(geometry.x), float(geometry.y))
