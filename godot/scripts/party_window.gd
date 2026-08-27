class_name PartyWindow
extends ReplicaWindow
## パーティー (ETペア狩り) — member rows with ON badges and HP bars, the
## 友達/パーティー/ギルド tab strip, and the two stateful checkboxes.

var party_name := "ETペア狩り"
var members := [
	{"name": "SakumaRiri", "map": "ダンジョン02F", "hp": 1092, "hp_max": 1109},
	{"name": "Sebas'", "map": "ダンジョン02F", "hp": 2643, "hp_max": 2643},
	{"name": "Ragna-X", "map": "ダンジョン02F", "hp": 1821, "hp_max": 1821},
	{"name": "Show_A", "map": "ダンジョン02F", "hp": 1656, "hp_max": 1656},
	{"name": "Meltina", "map": "ダンジョン02F", "hp": 1320, "hp_max": 1320},
]
var rows := []
var exp_share_check: CheckBox
var item_share_check: CheckBox
var tabs := {}


func _init() -> void:
	title_text = "パーティー (ETペア狩り)"
	window_size = Vector2(525, 482)


func _build_body() -> void:
	var list := Panel.new()
	list.name = "MemberList"
	list.position = Vector2(6, 4)
	list.size = Vector2(body.size.x - 12, 300)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(255, 255, 255)
	sb.border_color = Color8(130, 145, 170)
	sb.set_border_width_all(2)
	list.add_theme_stylebox_override("panel", sb)
	body.add_child(list)

	for i in members.size():
		var m: Dictionary = members[i]
		var row := Control.new()
		row.name = "Row%d" % i
		row.position = Vector2(8, 6 + i * 58)
		row.size = Vector2(list.size.x - 40, 56)
		var badge := Label.new()
		badge.text = "ON"
		badge.position = Vector2(0, 6)
		badge.add_theme_font_size_override("font_size", 18)
		badge.add_theme_color_override("font_color", Color8(255, 255, 255))
		var bsb := StyleBoxFlat.new()
		bsb.bg_color = Color8(90, 170, 90)
		bsb.set_corner_radius_all(10)
		bsb.content_margin_left = 6.0
		bsb.content_margin_right = 6.0
		var badge_panel := PanelContainer.new()
		badge_panel.position = Vector2(0, 2)
		badge_panel.add_theme_stylebox_override("panel", bsb)
		badge_panel.add_child(badge)
		row.add_child(badge_panel)
		var name_label := make_label("%s(%s)" % [m["name"], m["map"]], Vector2(52, 0), 24,
			Color8(70, 110, 220))
		row.add_child(name_label)
		var bar := ProgressBar.new()
		bar.name = "HpBar"
		bar.position = Vector2(52, 32)
		bar.size = Vector2(220, 14)
		bar.max_value = m["hp_max"]
		bar.value = m["hp"]
		bar.show_percentage = false
		var bg := StyleBoxFlat.new()
		bg.bg_color = Color8(240, 242, 246)
		bg.border_color = Color8(150, 160, 180)
		bg.set_border_width_all(1)
		var fg := StyleBoxFlat.new()
		fg.bg_color = Color8(90, 110, 200)
		bar.add_theme_stylebox_override("background", bg)
		bar.add_theme_stylebox_override("fill", fg)
		row.add_child(bar)
		var hp_label := make_label("%d/%d" % [m["hp"], m["hp_max"]], Vector2(292, 22), 22)
		hp_label.name = "HpLabel"
		row.add_child(hp_label)
		list.add_child(row)
		rows.append(row)

	var tab_strip := Control.new()
	tab_strip.name = "TabStrip"
	tab_strip.position = Vector2(6, 312)
	tab_strip.size = Vector2(body.size.x - 12, 46)
	body.add_child(tab_strip)
	var tab_names := ["友達", "パーティー", "ギルド"]
	for i in tab_names.size():
		var tab := make_side_button(tab_names[i], Vector2(i * 168, 0), Vector2(162, 44))
		tab.name = "Tab" + str(i)
		tab.toggle_mode = true
		tab.button_pressed = tab_names[i] == "パーティー"
		tab.pressed.connect(_on_tab.bind(tab_names[i]))
		tab_strip.add_child(tab)
		tabs[tab_names[i]] = tab

	exp_share_check = _check("パーティー経験値配分", Vector2(14, 366), true)
	exp_share_check.name = "ExpShare"
	body.add_child(exp_share_check)
	item_share_check = _check("アイテム分配 : 各自取得", Vector2(14, 404), true)
	item_share_check.name = "ItemShare"
	body.add_child(item_share_check)


func set_member_hp(index: int, hp: int) -> void:
	var m: Dictionary = members[index]
	m["hp"] = clampi(hp, 0, m["hp_max"])
	var row: Control = rows[index]
	row.get_node("HpBar").value = m["hp"]
	row.get_node("HpLabel").text = "%d/%d" % [m["hp"], m["hp_max"]]


func _on_tab(tab_name: String) -> void:
	for key in tabs:
		tabs[key].button_pressed = key == tab_name


func _check(text: String, pos: Vector2, pressed: bool) -> CheckBox:
	var box := CheckBox.new()
	box.text = text
	box.position = pos
	box.button_pressed = pressed
	box.add_theme_font_size_override("font_size", 24)
	for state in ["font_color", "font_pressed_color", "font_hover_color",
			"font_hover_pressed_color", "font_focus_color"]:
		box.add_theme_color_override(state, Color8(30, 34, 44))
	return box
