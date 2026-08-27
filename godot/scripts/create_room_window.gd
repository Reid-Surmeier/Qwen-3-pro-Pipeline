class_name CreateRoomWindow
extends ReplicaWindow
## チャットルーム作成 — the room-creation form: room name, level condition,
## public/private radio, member limit, message body, OK/cancel. Submitting
## with 公開 creates a room via a signal the desktop can route.

signal room_created(config: Dictionary)

var room_name_edit: LineEdit
var level_edit: LineEdit
var public_radio: CheckBox
var private_radio: CheckBox
var limit_edit: LineEdit
var message_edit: TextEdit
var ok_button: Button
var cancel_button: Button


func _init() -> void:
	title_text = "チャットルーム作成"
	window_size = Vector2(517, 440)


func _build_body() -> void:
	body.add_child(make_label("ルーム名 :", Vector2(12, 14), 24))
	room_name_edit = _edit(Vector2(140, 8), Vector2(352, 40), "ET登頂作戦部屋")
	room_name_edit.name = "RoomName"
	body.add_child(room_name_edit)

	body.add_child(make_label("入室条件 :", Vector2(12, 66), 24))
	body.add_child(make_label("Lv", Vector2(148, 66), 24, Color8(70, 110, 220)))
	level_edit = _edit(Vector2(184, 60), Vector2(90, 40), "40")
	level_edit.name = "LevelEdit"
	body.add_child(level_edit)
	body.add_child(make_label("以上", Vector2(292, 66), 24))

	body.add_child(make_label("公開設定 :", Vector2(12, 118), 24))
	var group := ButtonGroup.new()
	public_radio = _radio("公開", Vector2(140, 112), group, true)
	public_radio.name = "PublicRadio"
	body.add_child(public_radio)
	private_radio = _radio("非公開", Vector2(280, 112), group, false)
	private_radio.name = "PrivateRadio"
	body.add_child(private_radio)

	body.add_child(make_label("参加制限 :", Vector2(12, 170), 24))
	limit_edit = _edit(Vector2(140, 164), Vector2(90, 40), "20")
	limit_edit.name = "LimitEdit"
	body.add_child(limit_edit)
	body.add_child(make_label("名", Vector2(248, 170), 24))

	body.add_child(make_label("メッセージ :", Vector2(12, 222), 24))
	message_edit = TextEdit.new()
	message_edit.name = "MessageEdit"
	message_edit.position = Vector2(12, 256)
	message_edit.size = Vector2(480, 84)
	message_edit.text = "ETペア狩り＆登頂チャレンジ！\n職不問、支援歓迎です〜"
	message_edit.add_theme_font_size_override("font_size", 22)
	var tsb := StyleBoxFlat.new()
	tsb.bg_color = Color8(255, 255, 255)
	tsb.border_color = Color8(130, 145, 170)
	tsb.set_border_width_all(2)
	message_edit.add_theme_stylebox_override("normal", tsb)
	message_edit.add_theme_stylebox_override("focus", tsb)
	message_edit.add_theme_color_override("font_color", Color8(30, 34, 44))
	body.add_child(message_edit)

	ok_button = make_side_button("OK", Vector2(body.size.x - 200, 352), Vector2(88, 44))
	ok_button.name = "OkButton"
	ok_button.pressed.connect(_on_ok)
	body.add_child(ok_button)
	cancel_button = make_side_button("cancel", Vector2(body.size.x - 100, 352), Vector2(92, 44))
	cancel_button.name = "CancelButton"
	cancel_button.pressed.connect(func(): visible = false)
	body.add_child(cancel_button)


func _on_ok() -> void:
	var config := {
		"name": room_name_edit.text.strip_edges(),
		"min_level": int(level_edit.text) if level_edit.text.is_valid_int() else 0,
		"public": public_radio.button_pressed,
		"limit": int(limit_edit.text) if limit_edit.text.is_valid_int() else 0,
		"message": message_edit.text,
	}
	if config["name"].is_empty() or config["limit"] <= 0:
		return
	room_created.emit(config)


func _edit(pos: Vector2, size_: Vector2, text: String) -> LineEdit:
	var edit := LineEdit.new()
	edit.position = pos
	edit.size = size_
	edit.text = text
	edit.add_theme_font_size_override("font_size", 22)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(255, 255, 255)
	sb.border_color = Color8(130, 145, 170)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(4)
	edit.add_theme_stylebox_override("normal", sb)
	edit.add_theme_stylebox_override("focus", sb)
	edit.add_theme_color_override("font_color", Color8(30, 34, 44))
	edit.add_theme_color_override("caret_color", Color8(30, 34, 44))
	return edit


func _radio(text: String, pos: Vector2, group: ButtonGroup, pressed: bool) -> CheckBox:
	var radio := CheckBox.new()
	radio.text = text
	radio.position = pos
	radio.button_group = group
	radio.button_pressed = pressed
	radio.add_theme_font_size_override("font_size", 24)
	for state in ["font_color", "font_pressed_color", "font_hover_color",
			"font_hover_pressed_color", "font_focus_color"]:
		radio.add_theme_color_override(state, Color8(30, 34, 44))
	return radio
