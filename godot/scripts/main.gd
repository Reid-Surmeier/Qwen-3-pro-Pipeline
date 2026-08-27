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

	var backdrop := TextureRect.new()
	backdrop.name = "GameBackdrop"
	backdrop.texture = load("res://textures/game-backdrop.png")
	backdrop.position = Vector2(655, 0)
	backdrop.size = Vector2(753, 845)
	backdrop.stretch_mode = TextureRect.STRETCH_SCALE
	backdrop.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(backdrop)

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
	_maybe_interact()


func _capture(path: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	img.save_png(path)
	print("CAPTURED ", path, " ", img.get_width(), "x", img.get_height())
	get_tree().quit()


func _maybe_interact() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--interact=") and not has_meta("interacting"):
			set_meta("interacting", true)
			_interact(arg.trim_prefix("--interact="))


func _interact(path: String) -> void:
	var results: Array = []
	await get_tree().process_frame
	await get_tree().process_frame

	# 1. Real click on the status window's items button.
	var status = get_node("StatusWindow")
	var items_button: Button = status.side_buttons["items"]
	var fired := [false]
	items_button.pressed.connect(func(): fired[0] = true)
	await _click(items_button.get_global_rect().get_center())
	results.append({"test": "click-items-button", "passed": fired[0]})

	# 2. Real drag of the PM window by its title bar.
	var pm = get_node("PmWindow")
	var before: Vector2 = pm.global_position
	var grab: Vector2 = pm.title_bar.get_global_rect().get_center() + Vector2(60, 0)
	await _press(grab)
	await _move(grab + Vector2(80, -40))
	await _release(grab + Vector2(80, -40))
	var moved: Vector2 = pm.global_position - before
	results.append({"test": "drag-pm-window",
		"passed": moved.distance_to(Vector2(80, -40)) < 2.0, "moved": str(moved)})
	pm.global_position = before

	# 3. Real click toggling the party exp-share checkbox.
	var party = get_node("PartyWindow")
	var box: CheckBox = party.exp_share_check
	var was: bool = box.button_pressed
	await _click(box.get_global_rect().position + Vector2(16, box.size.y / 2))
	results.append({"test": "click-party-checkbox", "passed": box.button_pressed != was})
	box.button_pressed = was

	# 4. Real typing into the chat room and pressing Enter.
	var room = get_node("ChatRoomWindow")
	var line_count: int = room.lines.size()
	await _click(room.input.get_global_rect().get_center())
	for ch in "gg":
		var key := InputEventKey.new()
		key.pressed = true
		key.unicode = ch.unicode_at(0)
		key.keycode = KEY_G
		Input.parse_input_event(key)
		await get_tree().process_frame
	var enter := InputEventKey.new()
	enter.pressed = true
	enter.keycode = KEY_ENTER
	Input.parse_input_event(enter)
	await get_tree().process_frame
	await get_tree().process_frame
	results.append({"test": "type-and-enter-chat",
		"passed": room.lines.size() == line_count + 1 \
			and room.lines[-1]["text"] == "gg", "lines": room.lines.size()})

	# 5. Full-control matrix: raise each window with a real title-bar click,
	# then really click every Button / CheckBox in it and assert a reaction.
	var matrix_total := 0
	var matrix_failed: Array = []
	for child in get_children():
		var window := child as ReplicaWindow
		if window == null:
			continue
		await _click(window.title_bar.get_global_rect().get_center() + Vector2(90, 0))
		var controls: Array = []
		_collect_controls(window.body, controls)
		controls.append(window.title_bar.get_node("MinimizeButton"))
		controls.append(window.title_bar.get_node("CloseButton"))
		for control in controls:
			matrix_total += 1
			var reacted := [false]
			var was_visible: bool = window.visible
			var was_pressed: bool = control.button_pressed if control is BaseButton else false
			var was_disabled: bool = control is BaseButton and control.disabled
			var handler := func(): reacted[0] = true
			control.pressed.connect(handler)
			await _click(control.get_global_rect().get_center())
			control.pressed.disconnect(handler)
			var name_path := "%s/%s" % [window.name, control.name]
			var is_disabled: bool = was_disabled
			if is_disabled and reacted[0]:
				matrix_failed.append(name_path + " (disabled but reacted)")
			elif not is_disabled and not reacted[0]:
				matrix_failed.append(name_path)
			# restore any state the click changed
			if control is CheckBox:
				control.button_pressed = was_pressed
			if window.is_collapsed():
				window._on_minimize()
			if not window.visible and was_visible:
				window.visible = true
		await get_tree().process_frame
	results.append({"test": "control-matrix", "passed": matrix_failed.is_empty(),
		"controls": matrix_total, "unreached": matrix_failed})

	var failed := results.filter(func(r): return not r["passed"])
	var report := {"suite": "real-input", "total": results.size(),
		"failed": failed.size(), "results": results}
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	f.close()
	print("INTERACT %d/%d passed" % [results.size() - failed.size(), results.size()])
	get_tree().quit(1 if failed.size() > 0 else 0)


func _click(pos: Vector2) -> void:
	await _press(pos)
	await _release(pos)


func _press(pos: Vector2) -> void:
	await _mouse_button(pos, true)


func _release(pos: Vector2) -> void:
	await _mouse_button(pos, false)


func _mouse_button(pos: Vector2, pressed: bool) -> void:
	var move := InputEventMouseMotion.new()
	move.position = pos
	move.global_position = pos
	Input.parse_input_event(move)
	await get_tree().process_frame
	var ev := InputEventMouseButton.new()
	ev.position = pos
	ev.global_position = pos
	ev.button_index = MOUSE_BUTTON_LEFT
	ev.pressed = pressed
	Input.parse_input_event(ev)
	await get_tree().process_frame


func _move(pos: Vector2) -> void:
	var ev := InputEventMouseMotion.new()
	ev.position = pos
	ev.global_position = pos
	ev.button_mask = MOUSE_BUTTON_MASK_LEFT
	Input.parse_input_event(ev)
	await get_tree().process_frame
	await get_tree().process_frame


func _collect_controls(node: Node, out: Array) -> void:
	for child in node.get_children():
		if child is Button or child is CheckBox:
			out.append(child)
		if not (child is Button):
			_collect_controls(child, out)
