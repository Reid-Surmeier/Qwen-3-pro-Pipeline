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
var detail_panel: PanelContainer
var detail_label: Label
var _held_item := ""
var _held_button := 0
var _list_mode := false


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
	if item not in spec.value.items:
		return
	var surface: Dictionary = spec.surfaces[item]
	var geometry: Dictionary = surface.geometry
	detail_label.text = str(spec.value.details[item])
	detail_panel.position = Vector2(
		minf(float(geometry.x) + float(geometry.width) + 8.0, size.x - 156.0),
		minf(float(geometry.y), size.y - 50.0))
	detail_panel.visible = true


func rendered_facts() -> Dictionary:
	return {
		"selected_item": str(runtime.qa_state().controls[spec.id].get("value", "")),
		"list_mode": _list_mode,
		"detail_visible": detail_panel != null and detail_panel.visible,
		"detail_text": "" if detail_label == null else detail_label.text,
		"list_values": _list_values(),
	}


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
	for index in spec.value.items.size():
		var item := str(spec.value.items[index])
		var label := Label.new()
		label.text = "%s   %s" % [str(labels.get(item, item)), _stepper_text(item)]
		label.position = Vector2(12 + 270 * int(index / 14), 8 + 30 * (index % 14))
		label.size = Vector2(255, 26)
		label.add_theme_font_override("font", load("res://fonts/PixelMplus10-Regular.ttf"))
		label.add_theme_font_size_override("font_size", 14)
		label.add_theme_color_override("font_color", Color8(42, 37, 42))
		list_overlay.add_child(label)
		list_labels[item] = label
	add_child(list_overlay)
	list_overlay.visible = false


func _add_detail_panel() -> void:
	detail_panel = PanelContainer.new()
	detail_panel.name = "ContextDetail"
	detail_panel.size = Vector2(156, 50)
	var style := StyleBoxFlat.new()
	style.bg_color = Color8(246, 242, 245)
	style.border_color = Color8(70, 89, 159)
	style.set_border_width_all(1)
	detail_panel.add_theme_stylebox_override("panel", style)
	detail_label = Label.new()
	detail_label.add_theme_font_override("font", load("res://fonts/PixelMplus10-Regular.ttf"))
	detail_label.add_theme_font_size_override("font_size", 12)
	detail_label.add_theme_color_override("font_color", Color8(42, 37, 42))
	detail_panel.add_child(detail_label)
	add_child(detail_panel)
	detail_panel.visible = false


func _stepper_text(item: String) -> String:
	var control_id := "skill_tree.stepper.%s" % item
	var state: Dictionary = runtime.qa_state().controls.get(control_id, {})
	return str(state.get("text", ""))


func _list_values() -> Dictionary:
	var values := {}
	for item in spec.value.items:
		values[str(item)] = _stepper_text(str(item))
	return values


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
			_held_item = item
			_held_button = event.button_index
			runtime.set_interaction_phase(spec.id, "pressed", item)
			_refresh()
			changed.emit(spec.id, {"ok": true, "phase": "pressed", "surface": item})
			accept_event()
		elif _held_item == item and _held_button == event.button_index:
			var gesture := "ContextActivate" \
				if event.button_index == MOUSE_BUTTON_RIGHT else "Activate"
			_held_item = ""
			_held_button = 0
			var result: Dictionary = runtime.dispatch(spec.id, gesture,
				{"item": item, "button": "right" if gesture == "ContextActivate" else "left",
				 "position": [event.position.x, event.position.y],
				 "global_position": [event.global_position.x, event.global_position.y]})
			runtime.set_interaction_phase(spec.id, "hover", item)
			_refresh()
			changed.emit(spec.id, result)
			accept_event()


func _refresh() -> void:
	for item in visuals:
		var path := runtime.visual_surface_asset(spec.id, item)
		if not path.is_empty():
			visuals[item].texture = load(path)
	var labels: Dictionary = spec.value.get("labels", {})
	for item in list_labels:
		list_labels[item].text = "%s   %s" % [str(labels.get(item, item)), _stepper_text(item)]


func _point(geometry: Dictionary) -> Vector2:
	return Vector2(float(geometry.x), float(geometry.y))
