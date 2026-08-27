class_name TradeWindow
extends ReplicaWindow
## アイテム交換 — two offer columns with extracted item icons, zeny rows,
## and the OK/trade/cancel flow: trade stays disabled until both sides OK.

var partner := "Sebas'"
var partner_desc := "(Lv.58 Knight)"
var my_items := [{"icon": "res://textures/item-muffler.png", "name": "イミュンマフラー", "count": 1}]
var their_items := [{"icon": "res://textures/item-ori.png", "name": "オリデオコン", "count": 2}]
var my_zeny := 0
var their_zeny := 0
var my_ok := false
var their_ok := false
var ok_button: Button
var trade_button: Button
var cancel_button: Button
var my_zeny_label: Label
var their_zeny_label: Label


func _init() -> void:
	title_text = "アイテム交換 : Sebas' (Lv.58 Knight)"
	window_size = Vector2(577, 408)


func _build_body() -> void:
	var col_w := (body.size.x - 24) / 2.0
	_build_column("SakumaRiri の提供アイテム", Vector2(8, 4), col_w, my_items, true)
	_build_column("%s の提供アイテム" % partner, Vector2(16 + col_w, 4), col_w, their_items, false)

	ok_button = make_side_button("OK", Vector2(10, body.size.y - 52), Vector2(96, 44))
	ok_button.name = "OkButton"
	ok_button.pressed.connect(_on_ok)
	body.add_child(ok_button)

	trade_button = make_side_button("trade", Vector2(body.size.x / 2 - 48, body.size.y - 52), Vector2(96, 44))
	trade_button.name = "TradeButton"
	trade_button.disabled = true
	body.add_child(trade_button)

	cancel_button = make_side_button("cancel", Vector2(body.size.x - 106, body.size.y - 52), Vector2(96, 44))
	cancel_button.name = "CancelButton"
	cancel_button.pressed.connect(func(): visible = false)
	body.add_child(cancel_button)


func _build_column(header: String, pos: Vector2, width: float, items: Array, mine: bool) -> void:
	var head_color := Color8(70, 110, 220) if mine else Color8(60, 160, 90)
	body.add_child(make_label(header, pos + Vector2(4, 2), 19, head_color))
	var panel := Panel.new()
	panel.name = ("My" if mine else "Their") + "Column"
	panel.position = pos + Vector2(0, 32)
	panel.size = Vector2(width, body.size.y - 140)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(255, 255, 255)
	sb.border_color = Color8(130, 145, 170)
	sb.set_border_width_all(2)
	panel.add_theme_stylebox_override("panel", sb)
	body.add_child(panel)

	for i in items.size():
		var item: Dictionary = items[i]
		var icon := TextureRect.new()
		icon.texture = load(item["icon"])
		icon.position = Vector2(10, 8 + i * 64)
		icon.size = Vector2(52, 58)
		icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		panel.add_child(icon)
		panel.add_child(make_label(item["name"], Vector2(72, 8 + i * 64), 22))
		panel.add_child(make_label("[%d] 個" % item["count"], Vector2(72, 36 + i * 64), 22))

	for slot in range(items.size(), items.size() + 4):
		var ellipse := Panel.new()
		var esb := StyleBoxFlat.new()
		esb.bg_color = Color8(214, 222, 234)
		esb.set_corner_radius_all(12)
		ellipse.add_theme_stylebox_override("panel", esb)
		ellipse.position = Vector2(14, 16 + slot * 64)
		ellipse.size = Vector2(44, 24)
		panel.add_child(ellipse)

	var zeny_label := make_label("Zeny", pos + Vector2(6, body.size.y - 100), 24)
	body.add_child(zeny_label)
	var value := make_label("0", pos + Vector2(width - 40, body.size.y - 100), 24)
	value.name = ("My" if mine else "Their") + "Zeny"
	body.add_child(value)
	if mine:
		my_zeny_label = value
	else:
		their_zeny_label = value


func set_my_zeny(value: int) -> void:
	my_zeny = maxi(0, value)
	my_zeny_label.text = _format_zeny(my_zeny)


func _on_ok() -> void:
	my_ok = true
	ok_button.disabled = true
	_refresh_trade()


func partner_ok() -> void:
	their_ok = true
	_refresh_trade()


func _refresh_trade() -> void:
	trade_button.disabled = not (my_ok and their_ok)


static func _format_zeny(n: int) -> String:
	var s := str(n)
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return s + out
