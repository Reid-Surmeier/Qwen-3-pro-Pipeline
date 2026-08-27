class_name StatusWindow
extends ReplicaWindow
## 基本情報 — the basic-info window: name/class, HP/SP bars, Base/Job level
## bars, weight/zeny line, and the eight side buttons. All values are live.

var character_name := "SakumaRiri"
var character_class := "Acolyte"
var hp := 1092
var hp_max := 1109
var sp := 601
var sp_max := 613
var base_lv := 60
var base_pct := 0.55
var job_lv := 47
var job_pct := 0.45
var weight := 987
var weight_max := 2430
var zeny := 318430

var hp_bar: ProgressBar
var sp_bar: ProgressBar
var hp_value_label: Label
var sp_value_label: Label
var weight_label: Label
var side_buttons := {}

const BUTTON_NAMES := ["status", "option", "items", "equip", "skill", "map", "chat", "friend"]


func _init() -> void:
	title_text = "基本情報"
	window_size = Vector2(645, 277)


func _build_body() -> void:
	body.add_child(make_label(character_name, Vector2(14, 10), 30))
	body.add_child(make_label(character_class, Vector2(14, 52), 24, Color8(60, 66, 80)))

	body.add_child(make_label("HP", Vector2(216, 32), 24))
	hp_bar = _make_stat_bar(Vector2(258, 26), Color8(90, 140, 230))
	hp_bar.max_value = hp_max
	hp_bar.value = hp
	body.add_child(hp_bar)
	hp_value_label = make_label("%d / %d" % [hp, hp_max], Vector2(300, 52), 26)
	body.add_child(hp_value_label)

	body.add_child(make_label("SP", Vector2(216, 96), 24))
	sp_bar = _make_stat_bar(Vector2(258, 90), Color8(226, 110, 110))
	sp_bar.max_value = sp_max
	sp_bar.value = sp
	body.add_child(sp_bar)
	sp_value_label = make_label("%d / %d" % [sp, sp_max], Vector2(300, 114), 24)
	body.add_child(sp_value_label)

	var lv_panel := Panel.new()
	lv_panel.name = "LevelPanel"
	lv_panel.position = Vector2(24, 150)
	lv_panel.size = Vector2(420, 74)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(232, 238, 246)
	sb.border_color = Color8(150, 165, 190)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(6)
	lv_panel.add_theme_stylebox_override("panel", sb)
	body.add_child(lv_panel)
	lv_panel.add_child(make_label("Base Lv. %d" % base_lv, Vector2(10, 4), 24))
	lv_panel.add_child(_make_level_bar(Vector2(190, 10), base_pct))
	lv_panel.add_child(make_label("Job Lv. %d" % job_lv, Vector2(10, 38), 24))
	lv_panel.add_child(_make_level_bar(Vector2(190, 44), job_pct))

	weight_label = make_label(
		"Weight : %d / %d    Zeny : %s" % [weight, weight_max, _fmt(zeny)],
		Vector2(16, 218), 24)
	body.add_child(weight_label)

	for i in BUTTON_NAMES.size():
		var col := i % 2
		var row := i / 2
		var button := make_side_button(BUTTON_NAMES[i],
			Vector2(468 + col * 92, 8 + row * 55))
		button.name = BUTTON_NAMES[i].capitalize() + "Button"
		body.add_child(button)
		side_buttons[BUTTON_NAMES[i]] = button


func set_hp(value: int) -> void:
	hp = clampi(value, 0, hp_max)
	hp_bar.value = hp
	hp_value_label.text = "%d / %d" % [hp, hp_max]


func set_sp(value: int) -> void:
	sp = clampi(value, 0, sp_max)
	sp_bar.value = sp
	sp_value_label.text = "%d / %d" % [sp, sp_max]


func _make_stat_bar(pos: Vector2, fill: Color) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.position = pos
	bar.size = Vector2(196, 22)
	bar.show_percentage = false
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color8(252, 252, 252)
	bg.border_color = Color8(120, 130, 150)
	bg.set_border_width_all(1)
	bg.set_corner_radius_all(10)
	var fg := StyleBoxFlat.new()
	fg.bg_color = fill
	fg.set_corner_radius_all(10)
	bar.add_theme_stylebox_override("background", bg)
	bar.add_theme_stylebox_override("fill", fg)
	return bar


func _make_level_bar(pos: Vector2, fraction: float) -> ProgressBar:
	var bar := _make_stat_bar(pos, Color8(90, 120, 210))
	bar.size = Vector2(214, 20)
	bar.max_value = 1.0
	bar.value = fraction
	var bg: StyleBoxFlat = bar.get_theme_stylebox("background")
	bg.set_corner_radius_all(3)
	var fg: StyleBoxFlat = bar.get_theme_stylebox("fill")
	fg.set_corner_radius_all(3)
	return bar


static func _fmt(n: int) -> String:
	var s := str(n)
	var out := ""
	while s.length() > 3:
		out = "," + s.substr(s.length() - 3) + out
		s = s.substr(0, s.length() - 3)
	return s + out
