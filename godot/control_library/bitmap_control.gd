class_name BitmapControl
extends Control
## Shared Button/Toggle visual adapter. It renders the runtime's declared
## two-axis State Set and forwards only normalized Gesture Capabilities.

signal changed(control_id: String, result: Dictionary)

var spec: Dictionary
var runtime: ControlRuntime
var visual: TextureRect
var _held := false


func configure(control_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = control_spec
	runtime = control_runtime
	name = str(spec.id).replace(".", "-")
	position = _point(spec.geometry)
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	mouse_filter = Control.MOUSE_FILTER_STOP
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	focus_mode = Control.FOCUS_ALL


func _ready() -> void:
	visual = TextureRect.new()
	visual.name = "Visual"
	visual.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	visual.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	visual.stretch_mode = TextureRect.STRETCH_KEEP
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(visual)
	mouse_entered.connect(_entered)
	mouse_exited.connect(_exited)
	gui_input.connect(_on_gui_input)
	_refresh()


func _entered() -> void:
	if not _held:
		runtime.set_interaction_phase(spec.id, "hover", "body")
		_refresh()
		changed.emit(spec.id, {"ok": true, "phase": "hover"})


func _exited() -> void:
	if not _held:
		runtime.set_interaction_phase(spec.id, "idle")
		_refresh()
		changed.emit(spec.id, {"ok": true, "phase": "idle"})


func _on_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_held = true
			runtime.set_interaction_phase(spec.id, "pressed", "body")
			_refresh()
			changed.emit(spec.id, {"ok": true, "phase": "pressed", "surface": "body"})
			accept_event()
		else:
			var was_held := _held
			_held = false
			if was_held:
				var result: Dictionary = runtime.dispatch(spec.id, "Activate", {})
				runtime.set_interaction_phase(spec.id,
					"hover" if get_global_rect().has_point(event.global_position) else "idle",
					"body" if get_global_rect().has_point(event.global_position) else "")
				_refresh()
				changed.emit(spec.id, result)
				accept_event()


func _refresh() -> void:
	if visual == null:
		return
	var path := runtime.visual_asset(spec.id)
	if not path.is_empty():
		visual.texture = load(path)


func _point(geometry: Dictionary) -> Vector2:
	return Vector2(float(geometry.x), float(geometry.y))
