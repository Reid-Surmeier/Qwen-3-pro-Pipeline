extends Control
## Desktop root: magenta ground, game-scene backdrop placeholder, windows at
## their Reference Screen positions, and the project-wide pixel font.

const DESKTOP_MAGENTA := Color8(239, 7, 239)
const WINDOW_LAYOUT := {
	"StatusWindow": Vector2(10, 8),
	"GuildWindow": Vector2(15, 295),
	"MinimapWindow": Vector2(1403, 4),
	"CreateRoomWindow": Vector2(1378, 232),
	"PartyWindow": Vector2(720, 318),
	"TradeWindow": Vector2(663, 850),
	"ChatRoomWindow": Vector2(1262, 690),
	"PmWindow": Vector2(88, 1018),
}


func _ready() -> void:
	var font := FontFile.new()
	font.load_dynamic_font("res://fonts/PixelMplus12-Regular.ttf")
	font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	font.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	get_theme_default_font()
	theme = Theme.new()
	theme.default_font = font
	theme.default_font_size = 24

	var desktop := ColorRect.new()
	desktop.name = "Desktop"
	desktop.color = DESKTOP_MAGENTA
	desktop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(desktop)

	for entry in [[StatusWindow, "StatusWindow"], [GuildWindow, "GuildWindow"],
			[MinimapWindow, "MinimapWindow"], [CreateRoomWindow, "CreateRoomWindow"],
			[PartyWindow, "PartyWindow"], [TradeWindow, "TradeWindow"],
			[ChatRoomWindow, "ChatRoomWindow"], [PmWindow, "PmWindow"]]:
		var win: ReplicaWindow = entry[0].new()
		win.name = entry[1]
		win.position = WINDOW_LAYOUT[entry[1]]
		add_child(win)

	var bubble := SpeechBubble.new()
	bubble.name = "SpeechBubble"
	bubble.position = Vector2(862, 50)
	add_child(bubble)

	var bar := BottomBar.new()
	bar.name = "BottomBar"
	bar.position = Vector2(0, 1258)
	add_child(bar)

func _process(_delta: float) -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture=") and not has_meta("capturing"):
			set_meta("capturing", true)
			_capture(arg.trim_prefix("--capture="))


func _capture(path: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	img.save_png(path)
	print("CAPTURED ", path, " ", img.get_width(), "x", img.get_height())
	get_tree().quit()
