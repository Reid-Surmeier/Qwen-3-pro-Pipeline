class_name ChatRoomWindow
extends ReplicaWindow
## チャットルーム — room chat: colored log, member roster with scrollbar,
## live input and send, member count in the title.

const NAME_COLORS := {
	"AyanaIshizuka": Color8(60, 160, 90),
	"SakumaRiri": Color8(70, 110, 220),
	"Sebas'": Color8(60, 160, 90),
	"Ragna-X": Color8(60, 160, 90),
	"Meltina": Color8(60, 160, 90),
	"Choco-L": Color8(200, 90, 60),
	"Aero": Color8(70, 110, 220),
	"Show_A": Color8(60, 160, 90),
}

var room_name := "ET登頂作戦部屋"
var capacity := 20
var members := ["AyanaIshizuka", "SakumaRiri", "Sebas'", "Ragna-X", "Show_A",
	"Meltina", "Choco-L", "Aero", "Yuu-ya", "Lily_M", "HaneKaze", "Papiyon", "Lumiere"]
var self_name := "SakumaRiri"
var log_label: RichTextLabel
var member_list: ItemList
var input: LineEdit
var send_button: Button
var lines: Array = []


func _init() -> void:
	title_text = "チャットルーム : ET登頂作戦部屋 (13/20)"
	window_size = Vector2(683, 430)


func _refresh_title() -> void:
	title_text = "チャットルーム : %s (%d/%d)" % [room_name, members.size(), capacity]
	var label: Label = title_bar.get_node("Title")
	label.text = title_text


func _build_body() -> void:
	log_label = RichTextLabel.new()
	log_label.name = "Log"
	log_label.bbcode_enabled = true
	log_label.scroll_following = true
	log_label.position = Vector2(8, 6)
	log_label.size = Vector2(body.size.x - 190, body.size.y - 64)
	log_label.add_theme_font_size_override("normal_font_size", 22)
	log_label.add_theme_color_override("default_color", Color8(30, 34, 44))
	body.add_child(log_label)

	member_list = ItemList.new()
	member_list.name = "Members"
	member_list.position = Vector2(body.size.x - 174, 6)
	member_list.size = Vector2(168, body.size.y - 64)
	member_list.add_theme_font_size_override("font_size", 22)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(255, 255, 255)
	sb.border_color = Color8(130, 145, 170)
	sb.set_border_width_all(2)
	member_list.add_theme_stylebox_override("panel", sb)
	for m in members:
		member_list.add_item(m)
		var color: Color = NAME_COLORS.get(m, Color8(60, 160, 90))
		member_list.set_item_custom_fg_color(member_list.item_count - 1, color)
	body.add_child(member_list)

	for entry in [
		["AyanaIshizuka", "ども〜"],
		["SakumaRiri", "支援いきます〜"],
		["Sebas'", "盾まかせてっ"],
		["Ragna-X", "火力おっけー"],
		["Meltina", "ヒール全開で！"],
		["Choco-L", "SWありますー"],
		["Aero", "材料いける？"],
		["AyanaIshizuka", "いけます〜"],
		["Show_A", "ではいくよー"],
		["SakumaRiri", "集合したらいくよー"],
	]:
		append_line(entry[0], entry[1])

	input = LineEdit.new()
	input.name = "Input"
	input.position = Vector2(8, body.size.y - 52)
	input.size = Vector2(body.size.x - 106, 42)
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

	send_button = make_side_button("send", Vector2(body.size.x - 90, body.size.y - 52), Vector2(82, 42))
	send_button.name = "SendButton"
	send_button.pressed.connect(send)
	body.add_child(send_button)

	_refresh_title()


func append_line(speaker: String, text: String) -> void:
	lines.append({"speaker": speaker, "text": text})
	var color: Color = NAME_COLORS.get(speaker, Color8(60, 160, 90))
	log_label.append_text("[color=#%s]%s[/color] : %s\n" % [color.to_html(false), speaker, text])


func send() -> void:
	var text := input.text.strip_edges()
	if text.is_empty():
		return
	append_line(self_name, text)
	input.clear()


func join(member: String) -> bool:
	if members.size() >= capacity or member in members:
		return false
	members.append(member)
	member_list.add_item(member)
	_refresh_title()
	return true
