class_name PmWindow
extends ReplicaWindow
## 個人メッセージ — private message window: colored chat log, live input,
## working send (Enter or button) appending to the log.

const PEER_COLOR := Color8(60, 160, 90)
const SELF_COLOR := Color8(70, 110, 220)

var peer_name := "Sebas'"
var self_name := "SakumaRiri"
var log_label: RichTextLabel
var input: LineEdit
var send_button: Button
var lines: Array = []


func _init() -> void:
	title_text = "個人メッセージ : Sebas'"
	window_size = Vector2(490, 254)


func _build_body() -> void:
	log_label = RichTextLabel.new()
	log_label.name = "Log"
	log_label.bbcode_enabled = true
	log_label.scroll_following = true
	log_label.position = Vector2(8, 4)
	log_label.size = Vector2(body.size.x - 16, body.size.y - 56)
	log_label.add_theme_font_size_override("normal_font_size", 22)
	log_label.add_theme_color_override("default_color", Color8(30, 34, 44))
	body.add_child(log_label)

	for entry in [
		[peer_name, "さっきの宝箱 あけた？"],
		[self_name, "あけたよ〜"],
		[peer_name, "お、何でた？"],
		[self_name, "イミュンマフラー！"],
		[peer_name, "うまｗ"],
		[self_name, "今回ついてるかもｗ"],
	]:
		append_line(entry[0], entry[1])

	input = LineEdit.new()
	input.name = "Input"
	input.position = Vector2(8, body.size.y - 46)
	input.size = Vector2(body.size.x - 100, 40)
	input.add_theme_font_size_override("font_size", 22)
	var isb := StyleBoxFlat.new()
	isb.bg_color = Color8(255, 255, 255)
	isb.border_color = Color8(130, 145, 170)
	isb.set_border_width_all(2)
	isb.set_corner_radius_all(4)
	input.add_theme_stylebox_override("normal", isb)
	input.add_theme_stylebox_override("focus", isb)
	input.add_theme_color_override("font_color", Color8(30, 34, 44))
	input.add_theme_color_override("caret_color", Color8(30, 34, 44))
	input.text_submitted.connect(func(_t): send())
	body.add_child(input)

	send_button = make_side_button("send", Vector2(body.size.x - 86, body.size.y - 46), Vector2(78, 40))
	send_button.name = "SendButton"
	send_button.pressed.connect(send)
	body.add_child(send_button)


func append_line(speaker: String, text: String) -> void:
	lines.append({"speaker": speaker, "text": text})
	var color := SELF_COLOR if speaker == self_name else PEER_COLOR
	log_label.append_text("[color=#%s]%s[/color] : %s\n" % [color.to_html(false), speaker, text])


func send() -> void:
	var text := input.text.strip_edges()
	if text.is_empty():
		return
	append_line(self_name, text)
	input.clear()
