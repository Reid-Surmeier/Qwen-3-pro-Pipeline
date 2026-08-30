class_name ControlWindow
extends Control
## Production Window adapter for schema-v3 manifests. The Window owns chrome,
## move/minimize/close state and delegates each Control to the shared library.

signal state_changed(window_id: String)

const BitmapControlScript = preload("res://control_library/bitmap_control.gd")
const RangeControlScript = preload("res://control_library/range_control.gd")
const DropdownControlScript = preload("res://control_library/dropdown_control.gd")
const ChoiceGroupControlScript = preload("res://control_library/choice_group.gd")
const TabsControlScript = preload("res://control_library/tabs_control.gd")
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
var _home_size := Vector2.ZERO
var _dragging := false
var _drag_offset := Vector2.ZERO
var _home := Vector2.ZERO
var _last_window_gesture := ""
var _last_window_action := ""
var _last_window_error: Variant = null
var _resize_hit: Control
var _resize_visual: TextureRect
var _resize_frame_nodes: Array[CanvasItem] = []
var _resize_old_footer_cover: ColorRect
var _resize_title_fill: TextureRect
var _resize_footer: TextureRect
var _resize_footer_fill: TextureRect
var _resize_right_edge: TextureRect
var _resizing := false
var _resize_start_pointer := Vector2.ZERO
var _resize_start_size := Vector2.ZERO
var _resize_requested := Vector2.ZERO
var _resize_clamped := Vector2.ZERO
var _resize_motion_samples := 0
var _geometry_version := 0


func configure(window_spec: Dictionary) -> void:
	spec = window_spec
	runtime = ControlRuntime.new()
	runtime.configure(spec)
	name = str(spec.id).replace("-", "_").to_pascal_case()
	position = Vector2(float(spec.geometry.x), float(spec.geometry.y))
	_home = position
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	_expanded_size = size
	_home_size = size
	mouse_filter = Control.MOUSE_FILTER_PASS
	clip_contents = true


func _ready() -> void:
	var backing := ColorRect.new()
	backing.name = "Backing"
	backing.color = Color8(247, 247, 247)
	backing.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backing.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(backing)
	plate = TextureRect.new()
	plate.name = "Plate"
	plate.texture = load(str(spec.plates.expanded))
	plate.size = size
	plate.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	plate.stretch_mode = TextureRect.STRETCH_KEEP
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(plate)
	_add_resize_frame()
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
			"Tabs":
				node = TabsControlScript.new()
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
	_add_resize_grip()
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
		"last_gesture": _last_window_gesture,
		"last_action": _last_window_action,
		"last_error": _last_window_error,
		"geometry_version": _geometry_version,
		"resize": {"active": _resizing,
			"requested": [_resize_requested.x, _resize_requested.y],
			"clamped": [_resize_clamped.x, _resize_clamped.y],
			"motion_samples": _resize_motion_samples},
	}
	return state


func reset() -> void:
	position = _home
	visible = true
	_last_window_gesture = ""
	_last_window_action = ""
	_last_window_error = null
	if minimized:
		_toggle_minimized()
	size = _home_size
	_expanded_size = _home_size
	plate.size = size
	_layout_resize_frame()
	_layout_responsive_controls()
	_geometry_version = 0
	_resize_requested = size
	_resize_clamped = size
	_resize_motion_samples = 0
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


func _add_resize_grip() -> void:
	if not spec.get("resize") is Dictionary:
		return
	var geometry: Dictionary = spec.resize.get("grip_geometry", {})
	_resize_hit = Control.new()
	_resize_hit.name = "ResizeGrip"
	_resize_hit.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT)
	_resize_hit.offset_left = -float(geometry.get("width", 24))
	_resize_hit.offset_top = -float(geometry.get("height", 24))
	_resize_hit.offset_right = 0
	_resize_hit.offset_bottom = 0
	_resize_hit.mouse_filter = Control.MOUSE_FILTER_STOP
	_resize_hit.mouse_default_cursor_shape = Control.CURSOR_FDIAGSIZE
	_resize_visual = TextureRect.new()
	_resize_visual.name = "Visual"
	_resize_visual.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_resize_visual.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_resize_visual.stretch_mode = TextureRect.STRETCH_KEEP
	_resize_visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_resize_hit.add_child(_resize_visual)
	_set_resize_phase("idle")
	_resize_hit.mouse_entered.connect(func(): _set_resize_phase("hover"))
	_resize_hit.mouse_exited.connect(func(): _set_resize_phase("idle" if not _resizing else "pressed"))
	_resize_hit.gui_input.connect(_resize_input)
	add_child(_resize_hit)


func _add_resize_frame() -> void:
	var frame: Variant = spec.get("resize", {}).get("frame", {})
	if not frame is Dictionary or frame.is_empty():
		return
	_resize_old_footer_cover = ColorRect.new()
	_resize_old_footer_cover.name = "OldFooterCover"
	_resize_old_footer_cover.color = Color8(247, 247, 247)
	_resize_old_footer_cover.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_resize_old_footer_cover)
	_resize_frame_nodes.append(_resize_old_footer_cover)
	_resize_title_fill = _frame_texture("TitleFill", str(frame.title_fill))
	_resize_footer = _frame_texture("Footer", str(frame.footer))
	_resize_footer_fill = _frame_texture("FooterFill", str(frame.footer_fill))
	_resize_right_edge = _frame_texture("RightEdge", str(frame.right_edge))
	_layout_resize_frame()


func _frame_texture(node_name: String, path: String) -> TextureRect:
	var texture_rect := TextureRect.new()
	texture_rect.name = node_name
	texture_rect.texture = load(path)
	texture_rect.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	texture_rect.stretch_mode = TextureRect.STRETCH_SCALE
	texture_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(texture_rect)
	_resize_frame_nodes.append(texture_rect)
	return texture_rect


func _layout_resize_frame() -> void:
	if _resize_frame_nodes.is_empty():
		return
	var frame: Dictionary = spec.resize.frame
	var home := Vector2(float(frame.home_size[0]), float(frame.home_size[1]))
	var title_height := float(frame.title_height)
	var footer_height := float(frame.footer_height)
	var edge_width := float(frame.right_edge_width)
	var resized := not size.is_equal_approx(home) and not minimized
	for node in _resize_frame_nodes:
		node.visible = resized
	if not resized:
		return
	_resize_old_footer_cover.position = Vector2(0, home.y - footer_height)
	_resize_old_footer_cover.size = Vector2(minf(size.x, home.x), footer_height)
	_resize_old_footer_cover.visible = size.y > home.y
	_resize_title_fill.position = Vector2(home.x, 0)
	_resize_title_fill.size = Vector2(maxf(0.0, size.x - home.x), title_height)
	_resize_title_fill.visible = size.x > home.x
	_resize_footer.position = Vector2(0, size.y - footer_height)
	_resize_footer.size = Vector2(minf(size.x, home.x), footer_height)
	_resize_footer_fill.position = Vector2(home.x, size.y - footer_height)
	_resize_footer_fill.size = Vector2(maxf(0.0, size.x - home.x - edge_width), footer_height)
	_resize_footer_fill.visible = size.x > home.x
	_resize_right_edge.position = Vector2(size.x - edge_width, title_height)
	_resize_right_edge.size = Vector2(edge_width,
		maxf(0.0, size.y - title_height - footer_height))


func _layout_responsive_controls() -> void:
	var frame: Variant = spec.get("resize", {}).get("frame", {})
	if not frame is Dictionary:
		return
	var home_width := float(frame.get("home_size", [size.x, size.y])[0])
	for control_id in frame.get("anchored_right_controls", []):
		if not control_nodes.has(control_id):
			continue
		var control_spec: Dictionary = runtime.controls[control_id].spec
		control_nodes[control_id].position.x = float(control_spec.geometry.x) \
			+ size.x - home_width


func _set_resize_phase(phase: String) -> void:
	if _resize_visual == null:
		return
	var state_set: Variant = spec.get("resize", {}).get("state_set", {})
	var path := str(state_set.get("ready", {}).get(phase, "")) \
		if state_set is Dictionary else ""
	_resize_visual.texture = load(path) if not path.is_empty() else null


func _resize_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT \
			and event.pressed:
		move_to_front()
		_resizing = true
		_resize_start_pointer = event.global_position
		_resize_start_size = size
		_resize_requested = size
		_resize_clamped = size
		_resize_motion_samples = 0
		_set_resize_phase("pressed")
		accept_event()


func _continue_resize(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT \
			and not event.pressed:
		_resizing = false
		_geometry_version += 1
		_set_resize_phase("hover" if _resize_hit.get_global_rect().has_point(event.global_position) else "idle")
		state_changed.emit(str(spec.id))
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseMotion:
		var routed := _route_window_gesture("Resize")
		if not routed.get("ok", false) or routed.get("action") != "ResizeWindow":
			return
		_resize_requested = _resize_start_size + event.global_position - _resize_start_pointer
		var minimum := Vector2(float(spec.resize.minimum[0]), float(spec.resize.minimum[1]))
		var maximum := Vector2(float(spec.resize.maximum[0]), float(spec.resize.maximum[1]))
		_resize_clamped = _resize_requested.clamp(minimum, maximum)
		size = _resize_clamped
		_expanded_size = size
		plate.size = size
		_layout_resize_frame()
		_layout_responsive_controls()
		_resize_motion_samples += 1
		state_changed.emit(str(spec.id))
		get_viewport().set_input_as_handled()


func _input(event: InputEvent) -> void:
	if _resizing and (event is InputEventMouseMotion \
			or event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT):
		_continue_resize(event)


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
		var routed := _route_window_gesture("Drag")
		if not routed.get("ok", false) or routed.get("action") != "MoveWindow":
			return
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
	if event is InputEventKey and event.pressed and not event.echo \
			and event.keycode == KEY_ESCAPE and _is_frontmost_window():
		for control_id in control_nodes:
			var node: Control = control_nodes[control_id]
			if node is DropdownControl and runtime.qa_state().controls[control_id].semantic_state == "open":
				node.dismiss()
				get_viewport().set_input_as_handled()
				return
		var result := _route_window_gesture("KeyCommand", "Escape")
		if result.get("ok", false):
			get_viewport().set_input_as_handled()
			state_changed.emit(str(spec.id))


func _is_frontmost_window() -> bool:
	if not visible or get_parent() == null:
		return false
	var siblings := get_parent().get_children().filter(func(node):
		return node is ControlWindow and node.visible)
	return not siblings.is_empty() and siblings.back() == self


func _route_window_gesture(gesture: String, key: String = "") -> Dictionary:
	if gesture not in spec.get("gestures", []):
		_last_window_error = {"code": "UnsupportedGesture",
			"message": "Window gesture is not declared: %s" % gesture}
		return {"ok": false, "error": _last_window_error}
	for binding in spec.get("actions", []):
		if not binding is Dictionary or binding.get("gesture") != gesture:
			continue
		if gesture == "KeyCommand" and str(binding.get("key", "")) != key:
			continue
		_last_window_gesture = gesture
		_last_window_action = str(binding.get("action", ""))
		_last_window_error = null
		match _last_window_action:
			"MoveWindow":
				pass
			"ResizeWindow":
				pass
			"CloseWindow":
				dismiss_dropdowns()
				visible = false
			_:
				_last_window_error = {"code": "ActionRoutingError",
					"message": "Window cannot route action: %s" % _last_window_action}
				return {"ok": false, "error": _last_window_error}
		return {"ok": true, "gesture": gesture, "action": _last_window_action}
	_last_window_error = {"code": "ControlBindingError",
		"message": "Window gesture has no matching action: %s" % gesture}
	return {"ok": false, "error": _last_window_error}


func _control_changed(control_id: String, result: Dictionary) -> void:
	move_to_front()
	if result.get("ok", false) and result.has("action"):
		match str(result.action):
			"ToggleMinimized":
				_toggle_minimized()
			"CloseWindow":
				dismiss_dropdowns()
				visible = false
			"ToggleSkillView":
				_toggle_skill_view()
			"OpenSkillDetail", "OpenInventoryItem":
				_show_selection_detail(str(result.get("value", "")))
			"SelectSkill", "StepSkill", "CommitSkillChanges", "CancelSkillChanges", \
					"SelectInventoryTab", "SelectInventoryItem", \
					"ToggleInventorySelection", "MoveInventoryItem":
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
		size = Vector2(float(spec.geometry.width), 28)
		plate.size = size
	else:
		plate.texture = load(str(spec.plates.expanded))
		size = _expanded_size
		plate.size = size
	_layout_resize_frame()
	_layout_responsive_controls()
	if _resize_hit != null:
		_resize_hit.visible = not minimized
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
		if not detail_item.is_empty():
			_show_selection_detail(detail_item)


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


func _show_selection_detail(item: String) -> void:
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
