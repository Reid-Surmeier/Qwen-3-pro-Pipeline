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
		check("desktop-magenta", desktop.color.is_equal_approx(Color8(239, 7, 239)),
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

	# Chat room contracts.
	var room = main.get_node_or_null("ChatRoomWindow")
	check("chatroom-exists", room != null)
	if room:
		check("chatroom-seed", room.lines.size() == 10 and room.members.size() == 13,
			"%d lines %d members" % [room.lines.size(), room.members.size()])
		room.input.text = "移動します"
		room.send()
		check("chatroom-send", room.lines[-1]["text"] == "移動します")
		var joined: bool = room.join("Newcomer")
		check("chatroom-join", joined and room.members.size() == 14 \
			and room.title_text.contains("(14/20)"), room.title_text)
		check("chatroom-join-dup-rejected", not room.join("Newcomer"))

	# Create-room contracts.
	var form = main.get_node_or_null("CreateRoomWindow")
	check("createroom-exists", form != null)
	if form:
		var got: Array = []
		form.room_created.connect(func(cfg): got.append(cfg))
		form._on_ok()
		check("createroom-ok-emits", got.size() == 1 \
			and got[0]["name"] == "ET登頂作戦部屋" and got[0]["min_level"] == 40 \
			and got[0]["public"] and got[0]["limit"] == 20, str(got))
		form.room_name_edit.text = ""
		form._on_ok()
		check("createroom-empty-name-rejected", got.size() == 1)
		form.room_name_edit.text = "ET登頂作戦部屋"
		form.private_radio.button_pressed = true
		check("createroom-radio-exclusive", not form.public_radio.button_pressed)
		form.public_radio.button_pressed = true
		form.cancel_button.emit_signal("pressed")
		check("createroom-cancel-hides", not form.visible)
		form.visible = true

	# Party contracts.
	var party = main.get_node_or_null("PartyWindow")
	check("party-exists", party != null)
	if party:
		check("party-five-rows", party.rows.size() == 5, str(party.rows.size()))
		party.set_member_hp(0, 500)
		check("party-hp-live", int(party.rows[0].get_node("HpBar").value) == 500 \
			and party.rows[0].get_node("HpLabel").text == "500/1109")
		party.set_member_hp(0, 1092)
		var was: bool = party.exp_share_check.button_pressed
		party.exp_share_check.button_pressed = not was
		check("party-checkbox-toggles", party.exp_share_check.button_pressed != was)
		party.exp_share_check.button_pressed = was
		party._on_tab("ギルド")
		check("party-tab-exclusive", party.tabs["ギルド"].button_pressed \
			and not party.tabs["パーティー"].button_pressed)
		party._on_tab("パーティー")

	# Trade contracts.
	var trade = main.get_node_or_null("TradeWindow")
	check("trade-exists", trade != null)
	if trade:
		check("trade-initially-disabled", trade.trade_button.disabled)
		trade._on_ok()
		check("trade-still-disabled-after-one-ok", trade.trade_button.disabled)
		trade.partner_ok()
		check("trade-enabled-after-both-ok", not trade.trade_button.disabled)

	# Guild contracts.
	var guild = main.get_node_or_null("GuildWindow")
	check("guild-exists", guild != null)
	if guild:
		check("guild-roster-13", guild.roster_size() == 13, str(guild.roster_size()))
		check("guild-emblem-texture", guild.get_node("Body/Emblem").texture != null)

	# Bottom bar contracts.
	var bar = main.get_node_or_null("BottomBar")
	check("bottombar-exists", bar != null)
	if bar:
		bar.set_location("プロンテラ", Vector2i(45, 200))
		check("bottombar-location-live",
			bar.location_label.text == "プロンテラ [座標 45, 200]", bar.location_label.text)
		bar.set_location("ETダンジョン 02F", Vector2i(158, 94))

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
