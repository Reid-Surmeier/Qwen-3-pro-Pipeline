class_name GuildWindow
extends ReplicaWindow
## ギルド情報 [LunaBrigade] — emblem, guild stat block, five side buttons,
## and the scrollable member table with the source's columns and rows.

const ROSTER := [
	["AyanaIshizuka", "マスター", 62, "High Priest", "フェイヨン…"],
	["SakumaRiri", "副マスター", 60, "Acolyte", "ダンジョン…"],
	["Sebas'", "副マスター", 58, "Knight", "ダンジョン…"],
	["Show_A", "長老", 57, "Hunter", "ブロンテラ…"],
	["Ragna-X", "長老", 56, "Wizard", "ダンジョン…"],
	["Yuu-ya", "一般", 53, "Assassin", "ダンジョン…"],
	["Meltina", "一般", 52, "Priest", "フェイヨン…"],
	["Aero", "一般", 51, "Alchemist", "ブロンテラ…"],
	["Lily_M", "一般", 49, "Blacksmith", "ブロンテラ…"],
	["HaneKaze", "一般", 48, "Archer", "ダンジョン…"],
	["Papiyon", "一般", 47, "Merchant", "ブロンテラ…"],
	["Lumiere", "一般", 45, "Dancer", "ゲフェン…"],
	["Choco-L", "一般", 44, "Thief", "ブロンテラ…"],
]
const BUTTONS := ["guildskill", "member", "position", "guildsmn", "notice"]

var guild_name := "LunaBrigade"
var guild_level := 13
var master := "AyanaIshizuka"
var member_count := 24
var member_cap := 28
var allied := 3
var guild_exp := 1345678
var avg_level := 56
var side_buttons := {}
var members_label: Label
var table: Tree


func _init() -> void:
	title_text = "ギルド情報 [LunaBrigade]"
	window_size = Vector2(685, 718)


func _build_body() -> void:
	var emblem := TextureRect.new()
	emblem.name = "Emblem"
	emblem.texture = load("res://textures/guild-emblem.png")
	emblem.position = Vector2(22, 16)
	emblem.size = Vector2(96, 150)
	emblem.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	emblem.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	body.add_child(emblem)

	body.add_child(make_label(guild_name, Vector2(140, 10), 26, Color8(70, 110, 220)))
	body.add_child(make_label("ギルドレベル : %d" % guild_level, Vector2(140, 44), 24))
	var master_line := make_label("ギルドマスター : ", Vector2(140, 76), 24)
	body.add_child(master_line)
	body.add_child(make_label(master, Vector2(348, 76), 24, Color8(60, 160, 90)))
	members_label = make_label("ギルドメンバー : %d / %d  ⟳" % [member_count, member_cap],
		Vector2(140, 108), 24)
	members_label.name = "MembersLabel"
	body.add_child(members_label)
	body.add_child(make_label("同盟ギルド : %d" % allied, Vector2(140, 140), 24))
	body.add_child(make_label("ギルド経験値 : %d" % guild_exp, Vector2(140, 172), 24))
	body.add_child(make_label("ギルド平均レベル : %d" % avg_level, Vector2(140, 204), 24))

	for i in BUTTONS.size():
		var button := make_side_button(BUTTONS[i], Vector2(body.size.x - 122, 12 + i * 52),
			Vector2(112, 44))
		button.name = BUTTONS[i].capitalize() + "Button"
		body.add_child(button)
		side_buttons[BUTTONS[i]] = button

	table = Tree.new()
	table.name = "Roster"
	table.position = Vector2(8, 276)
	table.size = Vector2(body.size.x - 16, body.size.y - 286)
	table.columns = 5
	table.column_titles_visible = true
	table.hide_root = true
	table.select_mode = Tree.SELECT_ROW
	var titles := ["名前", "職位", "Lv", "職業", "現在位置"]
	var widths := [170, 110, 60, 150, 140]
	for c in 5:
		table.set_column_title(c, titles[c])
		table.set_column_custom_minimum_width(c, widths[c])
		table.set_column_expand(c, c == 4)
	var panel_sb := StyleBoxFlat.new()
	panel_sb.bg_color = Color8(255, 255, 255)
	panel_sb.border_color = Color8(130, 145, 170)
	panel_sb.set_border_width_all(2)
	table.add_theme_stylebox_override("panel", panel_sb)
	table.add_theme_color_override("font_color", Color8(30, 34, 44))
	table.add_theme_color_override("title_button_color", Color8(30, 34, 44))
	table.add_theme_font_size_override("font_size", 22)
	table.add_theme_font_size_override("title_button_font_size", 22)
	var root := table.create_item()
	for row in ROSTER:
		var item := table.create_item(root)
		for c in 5:
			item.set_text(c, str(row[c]))
			item.set_custom_color(c, Color8(30, 34, 44))
		item.set_custom_color(0, Color8(70, 110, 220))
	body.add_child(table)


func roster_size() -> int:
	var count := 0
	var child := table.get_root().get_first_child()
	while child:
		count += 1
		child = child.get_next()
	return count
