class_name DropdownControl
extends Control
## Source-themed Dropdown adapter. ChoiceGroup semantics remain local to the
## declared choices; the Window receives only the selected value.

signal changed(control_id: String, result: Dictionary)

const ROW_HEIGHT := 19
const FONT_SIZE := 15

var spec: Dictionary
var runtime: ControlRuntime
var field: TextureRect
var arrow: TextureRect
var label: Label
var menu: Control
var rows: Array[Dictionary] = []
var _held := false


func configure(control_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = control_spec
	runtime = control_runtime
	name = str(spec.id).replace(".", "-")
	position = Vector2(float(spec.geometry.x), float(spec.geometry.y))
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	mouse_filter = Control.MOUSE_FILTER_STOP
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	focus_mode = Control.FOCUS_ALL
	z_index = 50


func _ready() -> void:
	field = TextureRect.new()
	field.name = "Field"
	field.position = Vector2.ZERO
	field.size = Vector2(270, 32)
	field.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	field.stretch_mode = TextureRect.STRETCH_KEEP
	field.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(field)
	arrow = TextureRect.new()
	arrow.name = "Arrow"
	arrow.position = Vector2(268, 0)
	arrow.size = Vector2(32, 32)
	arrow.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	arrow.stretch_mode = TextureRect.STRETCH_KEEP
	arrow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(arrow)
	label = Label.new()
	label.name = "Value"
	label.position = Vector2(1, 1)
	label.size = Vector2(268, 30)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_style_label(label, Color(spec.tokens.text))
	add_child(label)
	_build_menu()
	mouse_entered.connect(_entered)
	mouse_exited.connect(_exited)
	gui_input.connect(_on_gui_input)
	_refresh()


func dismiss() -> Dictionary:
	var result: Dictionary = runtime.dispatch(spec.id, "KeyCommand", {"key": "Escape"})
	_refresh()
	changed.emit(spec.id, result)
	return result


func _build_menu() -> void:
	menu = Control.new()
	menu.name = "Menu"
	menu.position = get_parent().position + position + Vector2(0, 32)
	menu.size = Vector2(300, spec.value.choices.size() * ROW_HEIGHT + 2)
	menu.mouse_filter = Control.MOUSE_FILTER_STOP
	menu.visible = false
	get_parent().get_parent().add_child(menu)
	var panel := Panel.new()
	panel.name = "Panel"
	panel.size = menu.size
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var box := StyleBoxFlat.new()
	box.bg_color = Color(spec.tokens.fill)
	box.border_color = Color(spec.tokens.border)
	box.set_border_width_all(1)
	panel.add_theme_stylebox_override("panel", box)
	menu.add_child(panel)
	for index in spec.value.choices.size():
		var row := Control.new()
		row.name = "Row%d" % index
		row.position = Vector2(1, 1 + index * ROW_HEIGHT)
		row.size = Vector2(298, ROW_HEIGHT)
		row.mouse_filter = Control.MOUSE_FILTER_STOP
		row.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		menu.add_child(row)
		var bar := ColorRect.new()
		bar.color = Color(spec.tokens.highlight)
		bar.size = row.size
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		bar.visible = false
		row.add_child(bar)
		var text := Label.new()
		text.text = str(spec.value.choices[index])
		text.position = Vector2(6, 0)
		text.size = Vector2(286, ROW_HEIGHT)
		text.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		text.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_style_label(text, Color(spec.tokens.text))
		row.add_child(text)
		row.mouse_entered.connect(_row_entered.bind(index))
		row.mouse_exited.connect(_row_exited.bind(index))
		row.gui_input.connect(_row_input.bind(index))
		rows.append({"row": row, "bar": bar, "label": text})


func _style_label(node: Label, color: Color) -> void:
	var font: FontFile = load("res://fonts/DotGothic16-Regular.ttf")
	font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	font.hinting = TextServer.HINTING_NONE
	font.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	node.add_theme_font_override("font", font)
	node.add_theme_font_size_override("font_size", FONT_SIZE)
	node.add_theme_color_override("font_color", color)


func _entered() -> void:
	if not _held:
		runtime.set_interaction_phase(spec.id, "hover", "field")
		_refresh()
		changed.emit(spec.id, {"ok": true, "phase": "hover"})


func _exited() -> void:
	if not _held and not menu.get_global_rect().has_point(get_global_mouse_position()):
		runtime.set_interaction_phase(spec.id, "idle")
		_refresh()


func _on_gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_held = true
			runtime.set_interaction_phase(spec.id, "pressed", "field")
			_refresh()
			changed.emit(spec.id, {"ok": true, "phase": "pressed", "surface": "field"})
			accept_event()
		else:
			_held = false
			var result: Dictionary = runtime.dispatch(spec.id, "Activate", {})
			runtime.set_interaction_phase(spec.id, "hover", "field")
			_refresh()
			changed.emit(spec.id, result)
			accept_event()


func _row_entered(index: int) -> void:
	for row_index in rows.size():
		rows[row_index].bar.visible = row_index == index
		rows[row_index].label.add_theme_color_override("font_color",
			Color.WHITE if row_index == index else Color(spec.tokens.text))


func _row_exited(index: int) -> void:
	rows[index].bar.visible = false
	rows[index].label.add_theme_color_override("font_color", Color(spec.tokens.text))


func _row_input(event: InputEvent, index: int) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT \
			and not event.pressed:
		var result: Dictionary = runtime.dispatch(spec.id, "Activate",
			{"choice": spec.value.choices[index]})
		runtime.set_interaction_phase(spec.id, "idle")
		_refresh()
		changed.emit(spec.id, result)
		accept_event()


func _refresh() -> void:
	if field == null:
		return
	var state: Dictionary = runtime.qa_state().controls[spec.id]
	menu.position = get_parent().position + position + Vector2(0, 32)
	field.texture = load(runtime.visual_asset(spec.id))
	var arrow_set: Dictionary = spec.surfaces.arrow.state_set
	var phase: String = str(state.interaction_phase) \
		if state.active_surface == "field" else "idle"
	arrow.texture = load(str(arrow_set[state.semantic_state][phase]))
	menu.visible = state.semantic_state == "open"
	label.text = str(state.value)
	label.visible = state.value != "Classic Blue"
