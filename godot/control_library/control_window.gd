class_name ControlWindow
extends Control
## Production Window adapter for schema-v3 manifests. The Window owns chrome,
## move/minimize/close state and delegates each Control to the shared library.

signal state_changed(window_id: String)

const BitmapControlScript = preload("res://control_library/bitmap_control.gd")
const RangeControlScript = preload("res://control_library/range_control.gd")
const DropdownControlScript = preload("res://control_library/dropdown_control.gd")
const ChoiceGroupControlScript = preload("res://control_library/choice_group.gd")
const SelectionViewControlScript = preload("res://control_library/selection_view_control.gd")
const StepperControlScript = preload("res://control_library/stepper_control.gd")

var spec: Dictionary
var runtime: ControlRuntime
var plate: TextureRect
var control_nodes := {}
var minimized := false
var view_mode := "tree"
var detail_item := ""
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
			"ChoiceGroup":
				node = ChoiceGroupControlScript.new()
			"SelectionView":
				node = SelectionViewControlScript.new()
			"Stepper":
				node = StepperControlScript.new()
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
	for control_id in control_nodes:
		var node: Control = control_nodes[control_id]
		var rect := node.get_global_rect()
		state.controls[control_id].geometry = {
			"x": rect.position.x, "y": rect.position.y,
			"width": rect.size.x, "height": rect.size.y,
		}
		state.controls[control_id].visible = node.is_visible_in_tree()
		state.controls[control_id].z_index = node.z_index
		state.controls[control_id].rendered = true
		if node.has_method("rendered_facts"):
			state.controls[control_id].merge(node.rendered_facts(), true)
	state.window = {
		"id": str(spec.id),
		"position": [position.x, position.y],
		"size": [size.x, size.y],
		"visible": visible,
		"minimized": minimized,
		"view_mode": view_mode,
		"detail_item": detail_item,
		"pending": state.get("window_pending", false),
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
	var geometry: Dictionary = spec.get("drag_geometry",
		{"x": 0, "y": 0, "width": 373, "height": 28})
	hit.position = Vector2(float(geometry.x), float(geometry.y))
	hit.size = Vector2(float(geometry.width), float(geometry.height))
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
		for control_id in control_nodes:
			var node: Control = control_nodes[control_id]
			if node is DropdownControl and runtime.qa_state().controls[control_id].semantic_state == "open":
				node.dismiss()
				get_viewport().set_input_as_handled()
				return


func _control_changed(control_id: String, result: Dictionary) -> void:
	if result.get("ok", false) and result.has("action"):
		match str(result.action):
			"ToggleMinimized":
				_toggle_minimized()
			"CloseWindow":
				dismiss_dropdowns()
				visible = false
			"ToggleSkillView":
				_toggle_skill_view()
			"OpenSkillDetail":
				_show_skill_detail(str(result.get("value", "")))
			"SelectSkill", "StepSkill", "CommitSkillChanges", "CancelSkillChanges":
				pass
			_:
				runtime.reject_action(control_id, str(result.action))
	_refresh_all_controls()
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
	var keep_visible: Array = spec.get("minimized_controls", [])
	if keep_visible.is_empty():
		keep_visible = control_nodes.keys().filter(func(control_id):
			return str(control_id).ends_with(".minimize") \
				or str(control_id).ends_with(".close"))
	for control_id in control_nodes:
		var node: Control = control_nodes[control_id]
		node.visible = not minimized or control_id in keep_visible
	if not minimized:
		_apply_view_mode()


func _toggle_skill_view() -> void:
	view_mode = "list" if view_mode == "tree" else "tree"
	detail_item = ""
	_apply_view_mode()


func _apply_view_mode() -> void:
	if minimized:
		return
	if view_mode == "list" and spec.plates.has("list"):
		plate.texture = load(str(spec.plates.list))
	else:
		plate.texture = load(str(spec.plates.expanded))
	for control_id in control_nodes:
		var node: Control = control_nodes[control_id]
		if node.has_method("set_list_mode"):
			node.set_list_mode(view_mode == "list")
		elif str(runtime.controls[control_id].spec.type) == "Stepper":
			node.visible = view_mode == "tree"


func _show_skill_detail(item: String) -> void:
	detail_item = item
	for control_id in control_nodes:
		var node: Control = control_nodes[control_id]
		if node.has_method("show_detail"):
			node.show_detail(item)


func _refresh_all_controls() -> void:
	for control_id in control_nodes:
		var node: Control = control_nodes[control_id]
		if node.has_method("refresh"):
			node.refresh()
