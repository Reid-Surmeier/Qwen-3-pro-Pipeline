class_name ControlWindow
extends Control
## Production Window adapter for schema-v3 manifests. The Window owns chrome,
## move/minimize/close state and delegates each Control to the shared library.

signal state_changed(window_id: String)

const BitmapControlScript = preload("res://control_library/bitmap_control.gd")
const RangeControlScript = preload("res://control_library/range_control.gd")
const DropdownControlScript = preload("res://control_library/dropdown_control.gd")

var spec: Dictionary
var runtime: ControlRuntime
var plate: TextureRect
var control_nodes := {}
var minimized := false
var _expanded_size := Vector2.ZERO
var _dragging := false
var _drag_offset := Vector2.ZERO
var _home := Vector2.ZERO


func configure(window_spec: Dictionary) -> void:
	spec = window_spec
	runtime = ControlRuntime.new()
	runtime.configure(spec)
	name = str(spec.id).replace("-", "_").to_pascal_case()
	position = Vector2(float(spec.geometry.x), float(spec.geometry.y))
	_home = position
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	_expanded_size = size
	mouse_filter = Control.MOUSE_FILTER_PASS


func _ready() -> void:
	plate = TextureRect.new()
	plate.name = "Plate"
	plate.texture = load(str(spec.plates.expanded))
	plate.size = size
	plate.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	plate.stretch_mode = TextureRect.STRETCH_KEEP
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(plate)
	for control_spec in spec.controls:
		var node: Control
		match str(control_spec.type):
			"Button", "Toggle":
				node = BitmapControlScript.new()
			"Range":
				node = RangeControlScript.new()
			"Dropdown":
				node = DropdownControlScript.new()
			_:
				continue
		node.configure(control_spec, runtime)
		node.changed.connect(_control_changed)
		add_child(node)
		control_nodes[str(control_spec.id)] = node
	_add_title_drag()
	gui_input.connect(_window_input)
	state_changed.emit(str(spec.id))


func qa_state() -> Dictionary:
	var state := runtime.qa_state()
	state.window = {
		"id": str(spec.id),
		"position": [position.x, position.y],
		"size": [size.x, size.y],
		"visible": visible,
		"minimized": minimized,
		"z_index": z_index,
	}
	return state


func reset() -> void:
	position = _home
	visible = true
	if minimized:
		_toggle_minimized()
	state_changed.emit(str(spec.id))


func dismiss_dropdowns() -> void:
	for control_id in control_nodes:
		var node: Control = control_nodes[control_id]
		if node is DropdownControl:
			var state: Dictionary = runtime.qa_state().controls[control_id]
			if state.semantic_state == "open":
				node.dismiss()


func _add_title_drag() -> void:
	var hit := Control.new()
	hit.name = "TitleDrag"
	hit.position = Vector2.ZERO
	hit.size = Vector2(373, 28)
	hit.mouse_filter = Control.MOUSE_FILTER_STOP
	hit.mouse_default_cursor_shape = Control.CURSOR_MOVE
	hit.gui_input.connect(_title_input)
	add_child(hit)
	move_child(hit, 1)


func _title_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			move_to_front()
			_dragging = true
			_drag_offset = event.global_position - global_position
			accept_event()
		else:
			_dragging = false
			state_changed.emit(str(spec.id))
			accept_event()
	if event is InputEventMouseMotion and _dragging:
		var viewport_size := get_viewport_rect().size
		var max_position := Vector2(maxf(0.0, viewport_size.x - size.x),
			maxf(0.0, viewport_size.y - size.y))
		position = (event.global_position - _drag_offset).clamp(Vector2.ZERO, max_position)
		state_changed.emit(str(spec.id))
		accept_event()


func _window_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		move_to_front()
		if event.button_index == MOUSE_BUTTON_LEFT:
			dismiss_dropdowns()


func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE:
		var skin: Dictionary = runtime.qa_state().controls.get("options.skin", {})
		if skin.get("semantic_state") == "open":
			dismiss_dropdowns()
		else:
			dismiss_dropdowns()
			visible = false
			state_changed.emit(str(spec.id))
		get_viewport().set_input_as_handled()


func _control_changed(control_id: String, result: Dictionary) -> void:
	if result.get("ok", false) and result.has("action"):
		match str(result.action):
			"ToggleMinimized":
				_toggle_minimized()
			"CloseWindow":
				dismiss_dropdowns()
				visible = false
	state_changed.emit(str(spec.id))


func _toggle_minimized() -> void:
	dismiss_dropdowns()
	minimized = not minimized
	if minimized:
		plate.texture = load(str(spec.plates.minimized))
		size = Vector2(_expanded_size.x, 28)
		plate.size = size
	else:
		plate.texture = load(str(spec.plates.expanded))
		size = _expanded_size
		plate.size = size
	for control_id in control_nodes:
		var node: Control = control_nodes[control_id]
		node.visible = not minimized or control_id in ["options.minimize", "options.close"]
