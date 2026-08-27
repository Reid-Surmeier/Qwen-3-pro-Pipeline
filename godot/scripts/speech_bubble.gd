class_name SpeechBubble
extends Control
## The in-scene chat bubble (集合したらいくよー) with live text.

var text := "集合したら\nいくよー"
var label: Label
var panel: Panel


func _ready() -> void:
	panel = Panel.new()
	panel.name = "BubblePanel"
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(255, 255, 255)
	sb.border_color = Color8(180, 188, 200)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(16)
	panel.add_theme_stylebox_override("panel", sb)
	panel.size = Vector2(200, 96)
	add_child(panel)
	label = Label.new()
	label.name = "BubbleText"
	label.text = text
	label.position = Vector2(18, 8)
	label.add_theme_font_size_override("font_size", 26)
	label.add_theme_color_override("font_color", Color8(30, 34, 44))
	panel.add_child(label)


func set_text(value: String) -> void:
	text = value
	label.text = value
	var line_count := value.split("\n").size()
	panel.size = Vector2(maxf(120, 40 + 26 * value.length() / line_count * 0.9), 32 + line_count * 32)
