class_name ScrollViewControl
extends Control
## Vertical ScrollView adapter for wheel, one-row arrows, and continuous thumb Drag.

signal changed(control_id: String, result: Dictionary)

var spec: Dictionary
var runtime: ControlRuntime
var visuals := {}
var hits := {}
var _dragging := false


func configure(control_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = control_spec
	runtime = control_runtime
	name = str(spec.id).replace(".", "-")
	position = Vector2(float(spec.geometry.x), float(spec.geometry.y))
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	mouse_filter = Control.MOUSE_FILTER_PASS


func _ready() -> void:
	for surface in ["track", "decrement", "increment", "thumb"]:
		var definition: Dictionary = spec.surfaces[surface]
		var visual := TextureRect.new()
		visual.name = "Visual-" + surface
		visual.position = _point(definition.geometry)
		visual.size = Vector2(float(definition.geometry.width),
			float(definition.geometry.height))
		visual.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		visual.stretch_mode = TextureRect.STRETCH_KEEP
		visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
		visuals[surface] = visual
		add_child(visual)
		var hit := Control.new()
		hit.name = "Hit-" + surface
		hit.position = visual.position
		hit.size = visual.size
		hit.mouse_filter = Control.MOUSE_FILTER_STOP
		hit.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		hit.gui_input.connect(_surface_input.bind(surface))
		hit.mouse_entered.connect(_phase.bind(surface, "hover"))
		hit.mouse_exited.connect(_phase.bind(surface, "idle"))
		hits[surface] = hit
		add_child(hit)
	_refresh()


func _phase(surface: String, phase: String) -> void:
	if _dragging:
		return
	runtime.set_interaction_phase(spec.id, phase, surface if phase != "idle" else "")
	_refresh()
	changed.emit(spec.id, {"ok": true, "phase": phase, "surface": surface})


func _surface_input(event: InputEvent, surface: String) -> void:
	if event is InputEventMouseButton and event.button_index in [
			MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN] and event.pressed:
		var direction := -1 if event.button_index == MOUSE_BUTTON_WHEEL_UP else 1
		var result: Dictionary = runtime.dispatch(spec.id, "Wheel", {"direction": direction})
		_refresh()
		changed.emit(spec.id, result)
		accept_event()
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			runtime.set_interaction_phase(spec.id, "pressed", surface)
			_dragging = surface == "thumb" or surface == "track"
			if _dragging:
				_set_from_global_y(event.global_position.y)
			else:
				_refresh()
				changed.emit(spec.id, {"ok": true, "phase": "pressed", "surface": surface})
		else:
			var result := {"ok": true}
			if _dragging:
				_set_from_global_y(event.global_position.y)
			elif surface in ["decrement", "increment"]:
				result = runtime.dispatch(spec.id, "Activate",
					{"direction": -1 if surface == "decrement" else 1})
			_dragging = false
			runtime.set_interaction_phase(spec.id, "hover", surface)
			_refresh()
			changed.emit(spec.id, result)
		accept_event()
	if event is InputEventMouseMotion and _dragging:
		_set_from_global_y(event.global_position.y)
		accept_event()


func _input(event: InputEvent) -> void:
	if not _dragging:
		return
	if event is InputEventMouseMotion:
		_set_from_global_y(event.global_position.y)
	elif event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT \
			and not event.pressed:
		_set_from_global_y(event.global_position.y)
		_dragging = false
		runtime.set_interaction_phase(spec.id, "idle")
		_refresh()
		accept_event()


func _set_from_global_y(global_y: float) -> void:
	runtime.set_interaction_phase(spec.id, "dragging", "thumb")
	var track: TextureRect = visuals.track
	var thumb: TextureRect = visuals.thumb
	var local_y := global_y - global_position.y
	var thumb_start := float(spec.surfaces.thumb.geometry.y)
	var travel := track.position.y + track.size.y - thumb.size.y - thumb_start
	var normalized := (local_y - thumb_start - thumb.size.y / 2.0) / travel
	var result: Dictionary = runtime.dispatch(spec.id, "Drag", {"normalized": normalized})
	_refresh()
	changed.emit(spec.id, result)


func refresh() -> void:
	_refresh()


func rendered_facts() -> Dictionary:
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	return {"offset": int(state.offset), "thumb_y": visuals.thumb.position.y,
		"at_start": state.semantic_state == "at_start",
		"at_end": state.semantic_state == "at_end"}


func _refresh() -> void:
	if visuals.is_empty():
		return
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	var minimum := int(state.minimum)
	var maximum := int(state.maximum)
	var normalized := 0.0 if maximum == minimum else \
		float(int(state.offset) - minimum) / float(maximum - minimum)
	var track: TextureRect = visuals.track
	var thumb: TextureRect = visuals.thumb
	var thumb_start := float(spec.surfaces.thumb.geometry.y)
	var travel := track.position.y + track.size.y - thumb.size.y - thumb_start
	thumb.position.y = thumb_start + round(normalized * travel)
	if hits.has("thumb"):
		hits.thumb.position = thumb.position
	for surface in visuals:
		var definition: Dictionary = spec.surfaces[surface]
		var phase := str(state.interaction_phase) if state.active_surface == surface else "idle"
		var semantic := str(state.semantic_state)
		var path := str(definition.get("asset", ""))
		if definition.has("state_set"):
			path = str(definition.state_set.get(semantic,
				definition.state_set.get("ready", {})).get(phase, ""))
		if not path.is_empty():
			visuals[surface].texture = load(path)


func _point(geometry: Dictionary) -> Vector2:
	return Vector2(float(geometry.x), float(geometry.y))
