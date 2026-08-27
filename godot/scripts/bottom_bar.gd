class_name BottomBar
extends Control
## The full-width bottom strip: chat entry box, live location text, and the
## extracted icon tray.

var location_map := "ETダンジョン 02F"
var location_pos := Vector2i(158, 94)
var location_label: Label
var chat_input: LineEdit


func _ready() -> void:
	custom_minimum_size = Vector2(1973, 61)
	size = custom_minimum_size

	var strip := Panel.new()
	strip.name = "Strip"
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(236, 240, 246)
	sb.border_color = Color8(96, 121, 160)
	sb.set_border_width_all(2)
	strip.add_theme_stylebox_override("panel", sb)
	strip.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(strip)

	chat_input = LineEdit.new()
	chat_input.name = "ChatInput"
	chat_input.position = Vector2(10, 8)
	chat_input.size = Vector2(420, 44)
	chat_input.add_theme_font_size_override("font_size", 22)
	var isb := StyleBoxFlat.new()
	isb.bg_color = Color8(255, 255, 255)
	isb.border_color = Color8(130, 145, 170)
	isb.set_border_width_all(2)
	chat_input.add_theme_stylebox_override("normal", isb)
	chat_input.add_theme_stylebox_override("focus", isb)
	chat_input.add_theme_color_override("font_color", Color8(30, 34, 44))
	chat_input.add_theme_color_override("caret_color", Color8(30, 34, 44))
	add_child(chat_input)

	location_label = Label.new()
	location_label.name = "Location"
	location_label.add_theme_font_size_override("font_size", 26)
	location_label.add_theme_color_override("font_color", Color8(120, 128, 140))
	location_label.position = Vector2(560, 14)
	add_child(location_label)
	_refresh_location()

	var tray := TextureRect.new()
	tray.name = "IconTray"
	tray.texture = load("res://textures/icon-tray-strip.png")
	tray.position = Vector2(size.x - 300, 4)
	tray.size = Vector2(278, 52)
	tray.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tray.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(tray)


func set_location(map_name: String, pos: Vector2i) -> void:
	location_map = map_name
	location_pos = pos
	_refresh_location()


func _refresh_location() -> void:
	location_label.text = "%s [座標 %d, %d]" % [location_map, location_pos.x, location_pos.y]
