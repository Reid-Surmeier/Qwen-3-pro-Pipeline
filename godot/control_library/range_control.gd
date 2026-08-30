class_name RangeControl
extends Control
## Shared Range adapter: arrow step, wheel step, track jump, and continuous
## thumb drag all dispatch through the same factual runtime seam.

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
	_add_fixed_surface("track")
	_add_state_surface("decrement")
	_add_state_surface("increment")
	_add_state_surface("thumb", spec.state_set)
	for surface in ["decrement", "increment", "track", "thumb"]:
		_add_hit(surface)
	_refresh()


func _add_fixed_surface(surface: String) -> void:
	var definition: Dictionary = spec.surfaces[surface]
	var node := _texture_node(surface, definition.geometry)
	node.texture = load(str(definition.asset))


func _add_state_surface(surface: String, state_set: Dictionary = {}) -> void:
	var definition: Dictionary = spec.surfaces[surface]
	var node := _texture_node(surface, definition.geometry)
	node.set_meta("state_set", state_set if not state_set.is_empty() else definition.state_set)


func _texture_node(surface: String, geometry: Dictionary) -> TextureRect:
	var node := TextureRect.new()
	node.name = "Visual-" + surface
	node.position = Vector2(float(geometry.x), float(geometry.y))
	node.size = Vector2(float(geometry.width), float(geometry.height))
	node.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	node.stretch_mode = TextureRect.STRETCH_KEEP
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(node)
	visuals[surface] = node
	return node


func _add_hit(surface: String) -> void:
	var visual: TextureRect = visuals[surface]
	var hit := Control.new()
	hit.name = "Hit-" + surface
	hit.position = visual.position
	hit.size = visual.size
	hit.mouse_filter = Control.MOUSE_FILTER_STOP
	hit.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	hit.gui_input.connect(_surface_input.bind(surface))
	hit.mouse_entered.connect(_surface_entered.bind(surface))
	hit.mouse_exited.connect(_surface_exited.bind(surface))
	add_child(hit)
	hits[surface] = hit


func _surface_entered(surface: String) -> void:
	if not _dragging:
		runtime.set_interaction_phase(spec.id, "hover", surface)
		_refresh()
		changed.emit(spec.id, {"ok": true, "phase": "hover", "surface": surface})


func _surface_exited(surface: String) -> void:
	if not _dragging and runtime.qa_state().controls[spec.id].active_surface == surface:
		runtime.set_interaction_phase(spec.id, "idle")
		_refresh()
		changed.emit(spec.id, {"ok": true, "phase": "idle"})


func _surface_input(event: InputEvent, surface: String) -> void:
	if event is InputEventMouseButton and event.button_index in [
			MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN] and event.pressed:
		var direction := 1.0 if event.button_index == MOUSE_BUTTON_WHEEL_UP else -1.0
		var result: Dictionary = runtime.dispatch(spec.id, "Wheel", {"direction": direction})
		_refresh()
		changed.emit(spec.id, result)
		accept_event()
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			runtime.set_interaction_phase(spec.id, "pressed", surface)
			_dragging = surface in ["track", "thumb"]
			if _dragging:
				_set_from_global_x(event.global_position.x)
			_refresh()
			if not _dragging:
				changed.emit(spec.id, {"ok": true, "phase": "pressed", "surface": surface})
			accept_event()
		else:
			var result := {"ok": true}
			if _dragging:
				_set_from_global_x(event.global_position.x)
			elif surface in ["decrement", "increment"]:
				result = runtime.dispatch(spec.id, "Activate",
					{"direction": -1.0 if surface == "decrement" else 1.0})
			_dragging = false
			runtime.set_interaction_phase(spec.id, "hover", surface)
			_refresh()
			changed.emit(spec.id, result)
			accept_event()
	if event is InputEventMouseMotion and _dragging:
		_set_from_global_x(event.global_position.x)
		accept_event()


func _set_from_global_x(global_x: float) -> void:
	var track: TextureRect = visuals.track
	var thumb: TextureRect = visuals.thumb
	var local_x := global_x - global_position.x
	var travel := track.size.x - thumb.size.x
	var normalized := (local_x - track.position.x - thumb.size.x / 2.0) / travel
	var result: Dictionary = runtime.dispatch(spec.id, "Drag", {"normalized": normalized})
	_refresh()
	changed.emit(spec.id, result)


func _refresh() -> void:
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	var value_spec: Dictionary = spec.value
	var normalized: float = (float(state.value) - float(value_spec.minimum)) \
		/ (float(value_spec.maximum) - float(value_spec.minimum))
	var track: TextureRect = visuals.track
	var thumb: TextureRect = visuals.thumb
	thumb.position.x = track.position.x + round(normalized * (track.size.x - thumb.size.x))
	for surface in ["thumb", "decrement", "increment"]:
		var node: TextureRect = visuals[surface]
		var state_set: Dictionary = node.get_meta("state_set")
		var phase: String = str(state.interaction_phase) \
			if state.active_surface == surface else "idle"
		var path := str(state_set.get(state.semantic_state, {}).get(phase, ""))
		if not path.is_empty():
			node.texture = load(path)
