extends Control
## Desktop root v2 — manifest-driven source-pixel assembly. Every window is
## an extracted reference plate; the untouched frame is pixel-identical to
## the Reference Screen inside window rects by construction.

const DESKTOP_MAGENTA := Color8(239, 7, 239)

var windows := {}
var interaction_log: Array = []


func _ready() -> void:
	var font := FontFile.new()
	font.load_dynamic_font("res://fonts/PixelMplus12-Regular.ttf")
	font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	font.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
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
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(backdrop)

	var bubble := TextureRect.new()
	bubble.name = "SpeechBubble"
	bubble.texture = load("res://plates/speech-bubble.png")
	bubble.position = Vector2(852, 42)
	bubble.size = bubble.texture.get_size()
	bubble.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	bubble.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bubble)

	var manifest: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/runtime-manifest.json"))
	var holder := Control.new()
	holder.name = "Windows"
	holder.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	holder.mouse_filter = Control.MOUSE_FILTER_PASS
	add_child(holder)
	for value in manifest.windows:
		var window := PlateWindow.new()
		window.configure(value)
		window.hit_activated.connect(_on_hit)
		holder.add_child(window)
		windows[window.window_id] = window

	_mount_live_inputs()


func _mount_live_inputs() -> void:
	## Transparent inputs over source-empty input boxes: invisible until used,
	## so the untouched frame stays exact.
	for pair in [["pm", "input"], ["chat-room", "input"], ["bottom-bar", "chat-entry"]]:
		var window: PlateWindow = windows[pair[0]]
		var region_id: String = pair[1]
		if not window.dynamic_regions.has(region_id):
			continue
		var edit := LineEdit.new()
		edit.name = "live-" + region_id
		edit.flat = true
		edit.add_theme_color_override("font_color", Color8(30, 34, 44))
		edit.add_theme_color_override("caret_color", Color8(30, 34, 44))
		edit.add_theme_font_size_override("font_size", 24)
		var window_name := String(window.window_id)
		edit.text_submitted.connect(func(text): _send_chat(window_name, text))
		window.overlay(region_id, edit)


func _send_chat(window_id: String, text: String) -> void:
	if text.strip_edges().is_empty():
		return
	var window: PlateWindow = windows[window_id]
	if window.dynamic_regions.has("log"):
		var label: RichTextLabel = window.overlays.get("live-log")
		if label == null:
			label = RichTextLabel.new()
			label.name = "live-log"
			label.bbcode_enabled = true
			label.scroll_active = false
			label.add_theme_color_override("default_color", Color8(30, 34, 44))
			label.add_theme_font_size_override("normal_font_size", 22)
			var rect: Rect2 = window.dynamic_regions["log"]
			label.position = Vector2(rect.position.x, rect.position.y + rect.size.y - 66)
			label.size = Vector2(rect.size.x, 62)
			window.add_child(label)
			window.overlays["live-log"] = label
		label.append_text("[color=#4a6edc]SakumaRiri[/color] : %s\n" % text)
	var edit: Control = window.overlays.get("input")
	if edit == null:
		edit = window.overlays.get("chat-entry")
	if edit is LineEdit:
		edit.clear()
	interaction_log.append({"window": window_id, "sent": text})


func _on_hit(window_id: String, hit_id: String) -> void:
	interaction_log.append({"window": window_id, "hit": hit_id})


func qa_state() -> Dictionary:
	var hit_count := 0
	for id in windows:
		hit_count += windows[id].hit_nodes.size()
	return {"window_count": windows.size(), "hit_count": hit_count}


func _process(_delta: float) -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture=") and not has_meta("capturing"):
			set_meta("capturing", true)
			_capture(arg.trim_prefix("--capture="))
		if arg.begins_with("--interact=") and not has_meta("interacting"):
			set_meta("interacting", true)
			_interact(arg.trim_prefix("--interact="))


func _capture(path: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	var img := get_viewport().get_texture().get_image()
	img.save_png(path)
	print("CAPTURED ", path, " ", img.get_width(), "x", img.get_height())
	get_tree().quit()


func _interact(path: String) -> void:
	var results: Array = []
	await get_tree().process_frame
	await get_tree().process_frame

	# Real-input hit matrix: click every hit center; activatable hits must
	# emit, drag hits must move the window, disabled hits must stay inert.
	var matrix_total := 0
	var unreached: Array = []
	for window_id in windows:
		var window: PlateWindow = windows[window_id]
		for hit_id in window.hit_nodes:
			matrix_total += 1
			var node: Control = window.hit_nodes[hit_id]
			var hit: Dictionary = node.get_meta("hit")
			var role := str(hit.get("role", "button"))
			var was_visible := window.visible
			var was_min := window.minimized
			var center := node.get_global_rect().get_center()
			if role == "drag":
				var before := window.global_position
				await _press(center)
				await _move(center + Vector2(24, 18))
				await _release(center + Vector2(24, 18))
				if not (window.global_position - before).is_equal_approx(Vector2(24, 18)):
					unreached.append("%s/%s (drag)" % [window_id, hit_id])
				window.global_position = before
				continue
			var count_before := interaction_log.size()
			await _click(center)
			var reacted := interaction_log.size() > count_before
			var is_disabled: bool = hit.get("disabled", false)
			if is_disabled and reacted:
				unreached.append("%s/%s (disabled but reacted)" % [window_id, hit_id])
			elif not is_disabled and not reacted:
				unreached.append("%s/%s" % [window_id, hit_id])
			if window.minimized != was_min:
				window._toggle_minimized()
				await get_tree().create_timer(0.15).timeout
			if was_visible and not window.visible:
				window.visible = true
	results.append({"test": "hit-matrix", "passed": unreached.is_empty(),
		"hits": matrix_total, "unreached": unreached})

	# Live chat: type into the PM transparent input and press Enter.
	var pm: PlateWindow = windows["pm"]
	var edit: LineEdit = pm.overlays["input"]
	await _click(edit.get_global_rect().get_center())
	edit.text = "gg"
	edit.text_submitted.emit("gg")
	await get_tree().process_frame
	var sent := interaction_log.filter(func(e): return e.get("sent", "") == "gg")
	results.append({"test": "pm-live-send", "passed": sent.size() == 1 \
		and pm.overlays.has("live-log")})

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
