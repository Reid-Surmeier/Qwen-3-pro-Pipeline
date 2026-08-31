class_name SelectionViewControl
extends Control
## Render/input adapter for SelectionView. It is the shared recognition seam
## for left Activate and right ContextActivate; semantic meaning remains in
## SelectionView and the owning Window adapter.

signal changed(control_id: String, result: Dictionary)

var spec: Dictionary
var runtime: ControlRuntime
var visuals := {}
var hits := {}
var list_labels := {}
var list_overlay: Control
var detail_panel: Control
var detail_label: Label
var _held_item := ""
var _held_button := 0
var _list_mode := false
var _press_global := Vector2.ZERO
var _press_local := Vector2.ZERO
var _press_modifiers: Array[String] = []
var _dragging := false
var _drag_target := ""
var _drag_version := 0
var _motion_samples := 0
var _double_pending := false
var _modifier_double_pending := false
var _single_generation := 0
var _last_click_item := ""
var _last_click_modifiers: Array[String] = []
var _last_click_msec := -1

const DRAG_THRESHOLD := 4.0
const DOUBLE_INTERVAL_SECONDS := 0.22


func configure(control_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = control_spec
	runtime = control_runtime
	name = str(spec.id).replace(".", "-")
	position = _point(spec.geometry)
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	for item in spec.value.items:
		_add_item(str(item), spec.surfaces[str(item)])
	_add_list_overlay()
	_add_detail_panel()
	_refresh()


func set_list_mode(enabled: bool) -> void:
	_list_mode = enabled
	for item in hits:
		hits[item].visible = not enabled
		visuals[item].visible = not enabled
	list_overlay.visible = enabled
	if detail_panel != null:
		detail_panel.visible = false


func show_detail(item: String) -> void:
	if item not in spec.value.items or detail_panel == null:
		return
	var surface: Dictionary = spec.surfaces[item]
	var geometry: Dictionary = surface.geometry
	detail_label.text = str(spec.value.details[_item_identity(item)])
	var detail_view: Variant = spec.value.get("detail_view", {})
	var offset: Array = detail_view.get("offset", [8, 0]) \
		if detail_view is Dictionary else [8, 0]
	detail_panel.position = Vector2(
		minf(float(geometry.x) + float(geometry.width) + float(offset[0]),
			size.x - detail_panel.size.x),
		minf(float(geometry.y) + float(offset[1]), size.y - detail_panel.size.y))
	detail_panel.visible = true


func rendered_facts() -> Dictionary:
	var opened_item := str(runtime.qa_state().controls[spec.id].get("opened_item", ""))
	var rendered_values := {}
	var rendered_assets := {}
	var visible_count := 0
	for item in hits:
		var identity := _item_identity(item)
		rendered_values[str(item)] = identity
		rendered_assets[str(item)] = runtime.visual_surface_asset(spec.id, str(item)) \
			if not identity.is_empty() else ""
		if not identity.is_empty():
			visible_count += 1
	return {
		"selected_item": str(runtime.qa_state().controls[spec.id].get("value", "")),
		"list_mode": _list_mode,
		"detail_visible": detail_panel != null and detail_panel.visible,
		"detail_text": "" if detail_label == null else detail_label.text,
		"opened_item_value": "" if opened_item.is_empty() else _item_identity(opened_item),
		"list_values": _list_values(),
		"list_labels": _rendered_list_labels(),
		"gesture_drag": runtime.qa_state().controls[spec.id].get("drag_state", {}),
		"surface_geometry": _surface_geometry(),
		"rendered_item_values": rendered_values,
		"rendered_asset_paths": rendered_assets,
		"visible_item_count": visible_count,
	}


func _surface_geometry() -> Dictionary:
	var geometry := {}
	for item in hits:
		var rect: Rect2 = hits[item].get_global_rect()
		geometry[str(item)] = {"x": rect.position.x, "y": rect.position.y,
			"width": rect.size.x, "height": rect.size.y}
	return geometry


func refresh() -> void:
	_refresh()


func _add_item(item: String, surface: Dictionary) -> void:
	var visual := TextureRect.new()
	visual.name = item + "-visual"
	visual.position = _point(surface.geometry)
	visual.size = Vector2(float(surface.geometry.width), float(surface.geometry.height))
	visual.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	visual.stretch_mode = TextureRect.STRETCH_KEEP
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(visual)
	visuals[item] = visual

	var hit := Control.new()
	hit.name = item + "-hit"
	hit.position = visual.position
	hit.size = visual.size
	hit.mouse_filter = Control.MOUSE_FILTER_STOP
	hit.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	hit.mouse_entered.connect(_entered.bind(item))
	hit.mouse_exited.connect(_exited.bind(item))
	hit.gui_input.connect(_item_input.bind(item))
	add_child(hit)
	hits[item] = hit


func _add_list_overlay() -> void:
	list_overlay = Control.new()
	list_overlay.name = "ListView"
	list_overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	list_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var labels: Dictionary = spec.value.get("labels", {})
	var layout: Dictionary = spec.value.get("list_layout", {})
	var rows := maxi(int(layout.get("rows", 14)), 1)
	var columns := maxi(int(layout.get("columns", 1)), 1)
	var origin: Array = layout.get("origin", [12, 8])
	var row_height := float(layout.get("row_height", 30))
	var column_width := float(layout.get("column_width", 270))
	var visible_items := mini(spec.value.items.size(), rows * columns)
	for index in visible_items:
		var item := str(spec.value.items[index])
		var label := Label.new()
		label.text = "%s   %s" % [str(labels.get(item, item)), _related_value_text(item)]
		label.position = Vector2(float(origin[0]) + column_width * int(index / rows),
			float(origin[1]) + row_height * (index % rows))
		label.size = Vector2(column_width - 8, row_height - 2)
		label.add_theme_font_override("font", load("res://fonts/PixelMplus10-Regular.ttf"))
		label.add_theme_font_size_override("font_size", 14)
		label.add_theme_color_override("font_color", Color8(42, 37, 42))
		list_overlay.add_child(label)
		list_labels[item] = label
	add_child(list_overlay)
	list_overlay.visible = false


func _add_detail_panel() -> void:
	var detail_view: Variant = spec.value.get("detail_view")
	if not detail_view is Dictionary:
		var legacy := PanelContainer.new()
		detail_panel = legacy
		detail_panel.name = "ContextDetail"
		detail_panel.size = Vector2(156, 50)
		detail_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var style := StyleBoxFlat.new()
		style.bg_color = Color8(246, 242, 245)
		style.border_color = Color8(70, 89, 159)
		style.set_border_width_all(1)
		legacy.add_theme_stylebox_override("panel", style)
		detail_label = Label.new()
		detail_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		detail_label.add_theme_font_override("font",
			load("res://fonts/PixelMplus10-Regular.ttf"))
		detail_label.add_theme_font_size_override("font_size", 12)
		detail_label.add_theme_color_override("font_color", Color8(42, 37, 42))
		detail_panel.add_child(detail_label)
		add_child(detail_panel)
		detail_panel.visible = false
		return
	detail_panel = Control.new()
	detail_panel.name = "ContextDetail"
	detail_panel.size = Vector2(float(detail_view.size[0]), float(detail_view.size[1]))
	detail_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var background := TextureRect.new()
	background.name = "Background"
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.texture = load(str(detail_view.state_set.ready.idle))
	background.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	background.stretch_mode = TextureRect.STRETCH_KEEP
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	detail_panel.add_child(background)
	detail_label = Label.new()
	detail_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	detail_label.position = Vector2(float(detail_view.padding[0]),
		float(detail_view.padding[1]))
	detail_label.size = detail_panel.size - detail_label.position * 2.0
	detail_label.add_theme_font_override("font", load(str(detail_view.font)))
	detail_label.add_theme_font_size_override("font_size", int(detail_view.font_size))
	detail_label.add_theme_color_override("font_color", Color.from_string(
		str(detail_view.font_color), Color8(42, 37, 42)))
	detail_panel.add_child(detail_label)
	add_child(detail_panel)
	detail_panel.visible = false


func _related_value_text(item: String) -> String:
	var control_id := str(spec.value.get("value_control_ids", {}).get(item, ""))
	if control_id.is_empty():
		return ""
	var state: Dictionary = runtime.qa_state().controls.get(control_id, {})
	return str(state.get("text", ""))


func _list_values() -> Dictionary:
	var values := {}
	var labels: Dictionary = spec.value.get("labels", {})
	for item in list_labels:
		var prefix := str(labels.get(item, item)) + "   "
		var rendered := str(list_labels[item].text)
		values[str(item)] = rendered.trim_prefix(prefix)
	return values


func _rendered_list_labels() -> Dictionary:
	var rendered := {}
	for item in list_labels:
		rendered[str(item)] = str(list_labels[item].text)
	return rendered


func _entered(item: String) -> void:
	if _held_item.is_empty():
		runtime.set_interaction_phase(spec.id, "hover", item)
		_refresh()
		changed.emit(spec.id, {"ok": true, "phase": "hover", "surface": item})


func _exited(item: String) -> void:
	if _held_item.is_empty() and str(runtime.qa_state().controls[spec.id].active_surface) == item:
		runtime.set_interaction_phase(spec.id, "idle")
		_refresh()
		changed.emit(spec.id, {"ok": true, "phase": "idle"})


func _item_input(event: InputEvent, item: String) -> void:
	if event is InputEventMouseButton and event.button_index in [MOUSE_BUTTON_LEFT, MOUSE_BUTTON_RIGHT]:
		if event.pressed:
			var press_modifiers := _modifiers(event)
			var matching_double := _matches_declared_double(event, item, press_modifiers)
			_held_item = item
			_held_button = event.button_index
			_press_global = event.global_position
			_press_local = event.position
			_press_modifiers = press_modifiers
			_dragging = false
			_drag_target = ""
			_motion_samples = 0
			_drag_version = int(runtime.qa_state().controls[spec.id].get("item_version", 0))
			_modifier_double_pending = event.button_index == MOUSE_BUTTON_LEFT \
				and matching_double and not _press_modifiers.is_empty() \
				and "ModifierDoubleActivate" in spec.gestures
			_double_pending = event.button_index == MOUSE_BUTTON_LEFT \
				and matching_double and _press_modifiers.is_empty() \
				and "DoubleActivate" in spec.gestures
			_single_generation += 1
			runtime.set_interaction_phase(spec.id, "pressed", item)
			_refresh()
			changed.emit(spec.id, {"ok": true, "phase": "pressed", "surface": item})
			accept_event()
		elif _held_item == item and _held_button == event.button_index:
			_finish_pointer(event)


func _input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		var keycodes := [event.keycode, event.physical_keycode]
		if keycodes.any(func(keycode):
			return keycode in [KEY_CTRL, KEY_ALT, KEY_SHIFT, KEY_META]):
			_single_generation += 1
		return
	if _held_item.is_empty():
		return
	if event is InputEventMouseMotion and _held_button == MOUSE_BUTTON_LEFT \
			and "DragDrop" in spec.gestures:
		var distance: float = event.global_position.distance_to(_press_global)
		if distance > DRAG_THRESHOLD:
			_dragging = true
			_single_generation += 1
			_drag_target = _item_at_global(event.global_position)
			_motion_samples += 1
			runtime.set_selection_drag_state(spec.id, true, _held_item,
				_drag_target, _motion_samples)
			_refresh()
			changed.emit(spec.id, {"ok": true, "phase": "dragging",
				"source": _held_item, "target": _drag_target,
				"motion_samples": _motion_samples})
	if event is InputEventMouseButton and not event.pressed \
			and event.button_index == _held_button:
		_finish_pointer(event)


func _finish_pointer(event: InputEventMouseButton) -> void:
	if _held_item.is_empty():
		return
	var item := _held_item
	var button := _held_button
	var was_dragging := _dragging
	var was_double := _double_pending
	var was_modifier_double := _modifier_double_pending
	var modifiers := _press_modifiers.duplicate()
	var payload := {
		"item": item,
		"button": "right" if button == MOUSE_BUTTON_RIGHT else "left",
		"position": [event.position.x, event.position.y],
		"global_position": [event.global_position.x, event.global_position.y],
		"modifiers": modifiers,
	}
	_held_item = ""
	_held_button = 0
	_double_pending = false
	_modifier_double_pending = false
	var schedules_single: bool = not was_dragging and button == MOUSE_BUTTON_LEFT \
		and modifiers.is_empty() and not was_double \
		and "DoubleActivate" in spec.gestures
	if not schedules_single:
		_single_generation += 1
	if was_dragging:
		_forget_click()
	elif button == MOUSE_BUTTON_LEFT:
		_remember_click(item, modifiers)
	else:
		_forget_click()
	var result: Dictionary
	if was_dragging:
		var target := _item_at_global(event.global_position)
		result = runtime.dispatch(spec.id, "DragDrop", {
			"source": item, "target": target, "version": _drag_version,
			"start_position": [_press_global.x, _press_global.y],
			"end_position": [event.global_position.x, event.global_position.y],
			"motion_samples": _motion_samples, "modifiers": modifiers,
		})
		runtime.set_selection_drag_state(spec.id, false)
		_dragging = false
		_drag_target = ""
	elif button == MOUSE_BUTTON_RIGHT:
		result = runtime.dispatch(spec.id, "ContextActivate", payload)
	elif was_modifier_double:
		runtime.set_selection_transfer_state(spec.id, true, item)
		result = runtime.dispatch(spec.id, "ModifierDoubleActivate", payload)
		call_deferred("_clear_transfer_state")
	elif not modifiers.is_empty() and "ModifierActivate" in spec.gestures:
		result = runtime.dispatch(spec.id, "ModifierActivate", payload)
	elif was_double:
		result = runtime.dispatch(spec.id, "DoubleActivate", payload)
	elif "DoubleActivate" in spec.gestures:
		_schedule_single(payload)
		runtime.set_interaction_phase(spec.id, "hover", item)
		_refresh()
		accept_event()
		return
	else:
		result = runtime.dispatch(spec.id, "Activate", payload)
	runtime.set_interaction_phase(spec.id, "hover", item)
	_refresh()
	changed.emit(spec.id, result)
	accept_event()


func _clear_transfer_state() -> void:
	runtime.set_selection_transfer_state(spec.id, false)
	_refresh()
	changed.emit(spec.id, {"ok": true, "phase": "transfer-complete"})


func _matches_declared_double(event: InputEventMouseButton, item: String,
		modifiers: Array[String]) -> bool:
	if not event.double_click or _last_click_msec < 0:
		return false
	var elapsed_msec := Time.get_ticks_msec() - _last_click_msec
	return item == _last_click_item and modifiers == _last_click_modifiers \
		and elapsed_msec <= int(DOUBLE_INTERVAL_SECONDS * 1000.0)


func _remember_click(item: String, modifiers: Array[String]) -> void:
	_last_click_item = item
	_last_click_modifiers = modifiers.duplicate()
	_last_click_msec = Time.get_ticks_msec()


func _forget_click() -> void:
	_last_click_item = ""
	_last_click_modifiers = []
	_last_click_msec = -1


func _schedule_single(payload: Dictionary) -> void:
	_single_generation += 1
	var generation := _single_generation
	get_tree().create_timer(DOUBLE_INTERVAL_SECONDS).timeout.connect(
		_commit_single.bind(generation, payload.duplicate(true)))


func _commit_single(generation: int, payload: Dictionary) -> void:
	if generation != _single_generation:
		return
	var result: Dictionary = runtime.dispatch(spec.id, "Activate", payload)
	runtime.set_interaction_phase(spec.id, "hover", str(payload.item))
	_refresh()
	changed.emit(spec.id, result)


func _item_at_global(point: Vector2) -> String:
	for item in hits:
		if hits[item].get_global_rect().has_point(point):
			return str(item)
	return ""


func _modifiers(event: InputEventWithModifiers) -> Array[String]:
	var modifiers: Array[String] = []
	if event.ctrl_pressed:
		modifiers.append("ctrl")
	if event.alt_pressed:
		modifiers.append("alt")
	if event.shift_pressed:
		modifiers.append("shift")
	if event.meta_pressed:
		modifiers.append("meta")
	return modifiers


func _refresh() -> void:
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	var current_values: Dictionary = state.get("item_values", {})
	var declared_values: Dictionary = spec.value.get("item_values", {})
	var identity_backed: bool = not declared_values.is_empty() \
		or not current_values.is_empty()
	for item in visuals:
		var identity := str(current_values.get(item, item if not identity_backed else ""))
		visuals[item].visible = not identity.is_empty() and not _list_mode
		hits[item].visible = (not identity_backed or not identity.is_empty()) \
			and not _list_mode
		var path := runtime.visual_surface_asset(spec.id, item)
		if not path.is_empty():
			visuals[item].texture = load(path)
	var labels: Dictionary = spec.value.get("labels", {})
	var collection_labels: Dictionary = spec.value.get("collection_labels", {})
	for item in list_labels:
		var identity := _item_identity(item)
		list_labels[item].visible = not identity.is_empty()
		list_labels[item].text = "%s   %s" % [
			str(collection_labels.get(identity, labels.get(item, identity))),
			_related_value_text(item)]
	var opened_item := str(runtime.qa_state().controls[spec.id].get("opened_item", ""))
	if detail_panel != null and detail_panel.visible and not opened_item.is_empty():
		show_detail(opened_item)


func _item_identity(item: String) -> String:
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	return str(state.get("item_values", {}).get(item, item))


func _point(geometry: Dictionary) -> Vector2:
	return Vector2(float(geometry.x), float(geometry.y))
