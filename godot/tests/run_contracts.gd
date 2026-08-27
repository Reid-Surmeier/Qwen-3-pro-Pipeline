extends SceneTree
## Headless engine contracts for the replica. Emits machine-readable JSON to
## qa/out/contracts.json and exits non-zero on any failure — the agent-facing
## half of the self-verifying loop.

var results: Array = []


func check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"contract": name, "passed": passed, "detail": detail})


func _initialize() -> void:
	var scene: PackedScene = load("res://main.tscn")
	if scene == null:
		check("main-scene-loads", false, "load returned null")
		_finish()
		return
	var main = scene.instantiate()
	root.add_child(main)
	await process_frame
	check("main-scene-loads", true)

	var desktop = main.get_node_or_null("Desktop")
	check("desktop-exists", desktop != null)
	if desktop:
		check("desktop-magenta", desktop.color.is_equal_approx(Color8(255, 0, 230)),
			str(desktop.color))

	var win = main.get_node_or_null("StatusWindow")
	check("status-window-exists", win != null)
	if win == null:
		_finish()
		return

	check("status-window-position",
		win.position.is_equal_approx(Vector2(10, 8)), str(win.position))
	check("status-window-size",
		win.size.is_equal_approx(Vector2(645, 277)), str(win.size))
	check("status-title", win.title_text == "基本情報", win.title_text)

	# Drag contract: synthetic press-move-release through the title bar handler.
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	win._on_title_input(press)
	var before: Vector2 = win.global_position
	win._dragging = true
	win._drag_offset = Vector2.ZERO
	win.global_position = before + Vector2(40, 25)
	var release := InputEventMouseButton.new()
	release.button_index = MOUSE_BUTTON_LEFT
	release.pressed = false
	win._on_title_input(release)
	check("window-draggable",
		win.global_position.is_equal_approx(before + Vector2(40, 25)),
		str(win.global_position))
	win.position = Vector2(10, 8)

	# Live-value contracts.
	win.set_hp(500)
	check("hp-bar-live", int(win.hp_bar.value) == 500 \
		and win.hp_value_label.text == "500 / 1109", win.hp_value_label.text)
	win.set_hp(1092)
	win.set_sp(100)
	check("sp-bar-live", int(win.sp_bar.value) == 100 \
		and win.sp_value_label.text == "100 / 613", win.sp_value_label.text)
	win.set_sp(601)

	# All eight side buttons exist and are pressable.
	var pressed_count := 0
	for button_name in win.BUTTON_NAMES:
		var button = win.side_buttons.get(button_name)
		if button == null:
			continue
		var got := [false]
		button.pressed.connect(func(): got[0] = true)
		button.emit_signal("pressed")
		if got[0]:
			pressed_count += 1
	check("side-buttons-pressable", pressed_count == 8, str(pressed_count) + "/8")

	# Minimize collapses to the title bar and restores.
	var full: Vector2 = win.size
	win._on_minimize()
	check("minimize-collapses", win.is_collapsed() and not win.body.visible)
	win._on_minimize()
	check("minimize-restores", not win.is_collapsed() and win.body.visible)
	win.size = full

	# Minimap contracts.
	var mini = main.get_node_or_null("MinimapWindow")
	check("minimap-exists", mini != null)
	if mini:
		var z0: float = mini.zoom
		mini.zoom_in_button.emit_signal("pressed")
		check("minimap-zoom-in", mini.zoom > z0, str(mini.zoom))
		mini.zoom_out_button.emit_signal("pressed")
		check("minimap-zoom-back", is_equal_approx(mini.zoom, z0), str(mini.zoom))
		check("minimap-plate-texture", mini.plate.texture != null)

	# PM window contracts.
	var pm = main.get_node_or_null("PmWindow")
	check("pm-exists", pm != null)
	if pm:
		var before_lines: int = pm.lines.size()
		pm.input.text = "テスト送信"
		pm.send()
		check("pm-send-appends", pm.lines.size() == before_lines + 1 \
			and pm.lines[-1]["text"] == "テスト送信", str(pm.lines.size()))
		check("pm-input-cleared", pm.input.text == "", pm.input.text)
		check("pm-seed-log", before_lines == 6, str(before_lines))

	_finish()


func _finish() -> void:
	var failed := results.filter(func(r): return not r["passed"])
	var report := {
		"suite": "engine-contracts",
		"total": results.size(),
		"failed": failed.size(),
		"results": results,
	}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var f := FileAccess.open("res://qa/out/contracts.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	f.close()
	print("CONTRACTS %d/%d passed" % [results.size() - failed.size(), results.size()])
	for r in failed:
		printerr("FAIL %s: %s" % [r["contract"], r["detail"]])
	quit(1 if failed.size() > 0 else 0)
