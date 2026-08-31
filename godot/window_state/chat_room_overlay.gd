class_name ChatRoomOverlay
extends Control
## Dynamic conversation presentation. Idle remains the exact source plate;
## this overlay appears only after semantic chat state changes.

var spec: Dictionary
var runtime: ControlRuntime
var background: TextureRect
var labels: Array[Label] = []


func configure(adapter_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = adapter_spec
	runtime = control_runtime
	var geometry: Dictionary = spec.presentation.geometry
	position = Vector2(float(geometry.x), float(geometry.y))
	size = Vector2(float(geometry.width), float(geometry.height))
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	background = TextureRect.new()
	background.texture = load(str(spec.presentation.background))
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	background.stretch_mode = TextureRect.STRETCH_SCALE
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)
	refresh()


func refresh() -> void:
	if background == null:
		return
	for label in labels:
		label.queue_free()
	labels.clear()
	var state: Dictionary = runtime.qa_state().window_state
	visible = state.get("lines", []).size() > 5 \
		or int(state.get("visible_row_count", 5)) != 5
	if not visible:
		return
	var scroll_id := str(spec.controls.scroll)
	var offset := int(runtime.qa_state().controls.get(scroll_id, {}).get("offset", 0))
	var count := int(state.get("visible_row_count", 5))
	var lines: Array = state.get("lines", [])
	var shown := lines.slice(offset, mini(offset + count, lines.size()))
	var row_height := floorf(size.y / float(maxi(count, 1)))
	for index in shown.size():
		var entry: Dictionary = shown[index]
		var label := Label.new()
		label.position = Vector2(4, index * row_height)
		label.size = Vector2(size.x - 8, row_height)
		label.add_theme_font_override("font", load(str(spec.presentation.font)))
		label.add_theme_font_size_override("font_size", int(spec.presentation.font_size))
		var kind := str(entry.get("scope", entry.get("kind", "chat")))
		label.add_theme_color_override("font_color", Color.from_string(
			str(spec.presentation.colors.get(kind, "#202020")), Color8(32, 32, 32)))
		label.text = ("SakumaRiri : " if entry.has("speaker") else "") + str(entry.text)
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(label)
		labels.append(label)


func rendered_facts() -> Dictionary:
	var state: Dictionary = runtime.qa_state().window_state
	return {"visible": visible,
		"rendered_lines": labels.map(func(label): return label.text),
		"visible_row_count": int(state.get("visible_row_count", 5)),
		"pending_delivery": state.get("pending_delivery"),
		"version": int(state.get("version", 0))}
