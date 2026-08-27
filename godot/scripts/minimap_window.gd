class_name MinimapWindow
extends ReplicaWindow
## ミニマップ — extracted map plate with live +/- zoom and player dot.

var zoom := 1.0
var plate: TextureRect
var zoom_in_button: Button
var zoom_out_button: Button


func _init() -> void:
	title_text = "ミニマップ"
	window_size = Vector2(460, 208)


func _build_body() -> void:
	var inset := Panel.new()
	inset.name = "MapInset"
	inset.position = Vector2(4, 2)
	inset.size = body.size - Vector2(8, 6)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(206, 208, 210)
	sb.border_color = Color8(120, 140, 170)
	sb.set_border_width_all(2)
	inset.clip_contents = true
	inset.add_theme_stylebox_override("panel", sb)
	body.add_child(inset)

	plate = TextureRect.new()
	plate.name = "MapPlate"
	plate.texture = load("res://textures/minimap-plate.png")
	plate.position = Vector2(2, 2)
	plate.stretch_mode = TextureRect.STRETCH_SCALE
	plate.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_apply_zoom()
	inset.add_child(plate)

	zoom_in_button = _zoom_button("+", Vector2(inset.size.x - 40, 8))
	zoom_in_button.name = "ZoomIn"
	zoom_in_button.pressed.connect(func(): set_zoom(zoom * 1.25))
	inset.add_child(zoom_in_button)
	zoom_out_button = _zoom_button("-", Vector2(inset.size.x - 40, 52))
	zoom_out_button.name = "ZoomOut"
	zoom_out_button.pressed.connect(func(): set_zoom(zoom / 1.25))
	inset.add_child(zoom_out_button)


func set_zoom(value: float) -> void:
	zoom = clampf(value, 0.5, 4.0)
	_apply_zoom()


func _apply_zoom() -> void:
	if plate.texture:
		plate.size = plate.texture.get_size() * zoom


func _zoom_button(glyph: String, pos: Vector2) -> Button:
	var button := make_side_button(glyph, pos, Vector2(32, 32))
	button.add_theme_font_size_override("font_size", 26)
	return button
