class_name TextFieldControl
extends Control
## TextField adapter. Godot owns text/IME editing; the semantic module accepts
## each complete candidate before it becomes public QA state.

signal changed(control_id: String, result: Dictionary)

var spec: Dictionary
var runtime: ControlRuntime
var visual: TextureRect
var field: LineEdit
var _reverting := false


func configure(control_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = control_spec
	runtime = control_runtime
	name = str(spec.id).replace(".", "-")
	position = Vector2(float(spec.geometry.x), float(spec.geometry.y))
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	mouse_filter = Control.MOUSE_FILTER_PASS


func _ready() -> void:
	visual = TextureRect.new()
	visual.name = "Visual"
	visual.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	visual.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	visual.stretch_mode = TextureRect.STRETCH_KEEP
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(visual)
	field = LineEdit.new()
	field.name = "Field"
	field.position = Vector2(5, 1)
	field.size = size - Vector2(10, 2)
	field.max_length = int(spec.value.maximum_length)
	field.text = str(runtime.qa_state().controls[spec.id].text)
	field.add_theme_font_override("font", load(str(spec.tokens.font)))
	field.add_theme_font_size_override("font_size", int(spec.tokens.font_size))
	field.add_theme_color_override("font_color", Color.from_string(
		str(spec.tokens.font_color), Color8(42, 37, 42)))
	field.add_theme_stylebox_override("normal", StyleBoxEmpty.new())
	field.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	field.text_changed.connect(_text_changed)
	field.focus_entered.connect(_focus.bind(true))
	field.focus_exited.connect(_focus.bind(false))
	add_child(field)
	_refresh()


func focus_field() -> void:
	field.grab_focus()
	field.caret_column = field.text.length()


func _focus(focused: bool) -> void:
	runtime.set_interaction_phase(spec.id, "hover" if focused else "idle",
		"field" if focused else "")
	_refresh()
	changed.emit(spec.id, {"ok": true, "focused": focused})


func _text_changed(candidate: String) -> void:
	if _reverting:
		return
	var result: Dictionary = runtime.dispatch(spec.id, "KeyCommand", {"text": candidate})
	if not result.ok:
		_reverting = true
		field.text = str(runtime.qa_state().controls[spec.id].text)
		field.caret_column = field.text.length()
		_reverting = false
	_refresh()
	changed.emit(spec.id, result)


func refresh() -> void:
	_refresh()


func rendered_facts() -> Dictionary:
	return {"rendered_text": field.text, "focused": field.has_focus(),
		"caret_column": field.caret_column}


func _refresh() -> void:
	if visual == null:
		return
	var path := runtime.visual_asset(spec.id)
	if not path.is_empty():
		visual.texture = load(path)
