extends SceneTree
## Headless engine contracts v2 for the manifest-driven source-pixel replica.
## Emits qa/out/contracts.json; non-zero exit on any failure.

var results: Array = []


func check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"contract": name, "passed": passed, "detail": detail})


func _initialize() -> void:
	var manifest: Dictionary = JSON.parse_string(
		FileAccess.get_file_as_string("res://data/runtime-manifest.json"))
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
	check("desktop-plate-loaded", desktop != null and desktop is TextureRect \
		and desktop.texture != null)

	# Exact inventory: every manifest window exists with its plate and hits.
	var expected_hits := 0
	for value in manifest.windows:
		expected_hits += value.hits.size()
		var window = main.windows.get(str(value.id))
		if window == null:
			check("window-" + str(value.id), false, "missing")
			continue
		var plate_ok: bool = window.plate.texture != null
		var geometry_ok: bool = window.position == Vector2(
			float(value.geometry.x), float(value.geometry.y)) \
			and window.size == Vector2(
			float(value.geometry.width), float(value.geometry.height))
		var hits_ok: bool = window.hit_nodes.size() == value.hits.size()
		check("window-" + str(value.id), plate_ok and geometry_ok and hits_ok,
			"plate=%s geom=%s hits=%d/%d" % [plate_ok, geometry_ok,
			window.hit_nodes.size(), value.hits.size()])
	var state: Dictionary = main.qa_state()
	check("inventory-window-count", state.window_count == manifest.windows.size(),
		str(state.window_count))
	check("inventory-hit-count", state.hit_count == expected_hits,
		"%d/%d" % [state.hit_count, expected_hits])

	# Behavior contracts through activate(). Source state: check-exp starts
	# checked, so the first toggle unchecks and must show the derived patch.
	var party = main.windows["party"]
	check("checkbox-source-state", party.toggle_state["check-exp"] == true)
	party.activate("check-exp")
	check("checkbox-toggles", party.toggle_state["check-exp"] == false)
	check("checkbox-visible-off", party.overlays.has("state-check-exp"))
	party.activate("check-exp")
	check("checkbox-restores", party.toggle_state["check-exp"] == true)
	party.activate("tab-guild")
	check("tab-exclusive", party.toggle_state["tab-guild"] \
		and not party.toggle_state["tab-party"])
	check("tab-visible-active", party.overlays.has("state-tab-guild"))
	party.activate("tab-party")
	check("tab-visible-moves", party.overlays.has("state-tab-party") \
		and not party.overlays.has("state-tab-guild"))

	var form = main.windows["create-room"]
	form.activate("radio-private")
	check("radio-exclusive", form.toggle_state["radio-private"] \
		and not form.toggle_state["radio-public"])
	check("radio-visible-swap", form.overlays.has("state-radio-private") \
		and form.overlays.has("state-radio-public"))
	form.activate("radio-public")

	var basic = main.windows["basic-info"]
	var full: Vector2 = basic.size
	var full_texture: Texture2D = basic.plate.texture
	basic.activate("minimize")
	await create_timer(0.2).timeout
	check("minimize-folds", basic.minimized and basic.size.y <= 47.0, str(basic.size))
	check("minimize-real-asset", basic.plate.texture != full_texture,
		"collapsed state must be the composited plate, not a clipped frame")
	basic.activate("minimize")
	await create_timer(0.2).timeout
	check("minimize-restores", not basic.minimized and basic.size == full \
		and basic.plate.texture == full_texture)

	basic.activate("close")
	check("close-hides", not basic.visible)
	var reopen := InputEventKey.new()
	reopen.keycode = KEY_V
	reopen.alt_pressed = true
	reopen.pressed = true
	Input.parse_input_event(reopen)
	await process_frame
	await process_frame
	check("close-reopens-by-key", basic.visible, "Alt+V must restore the window")

	var trade = main.windows["trade"]
	var before: int = main.interaction_log.size()
	trade.activate("btn-trade")
	check("disabled-hit-inert", main.interaction_log.size() == before)

	check("live-inputs-mounted", main.windows["pm"].overlays.has("input") \
		and main.windows["chat-room"].overlays.has("input") \
		and main.windows["bottom-bar"].overlays.has("chat-entry"))
	var pm_edit: LineEdit = main.windows["pm"].overlays["input"]
	check("live-input-transparent-initially", pm_edit.text == "")

	main._send_chat("pm", "テスト")
	check("live-send-appends", main.windows["pm"].overlays.has("live-log"))
	check("clean-plate-patch", main.windows["pm"].overlays.has("clean-log-patch"))

	var info = main.windows["basic-info"]
	info.set_dynamic_text("hp-value", "999 / 1109")
	check("dynamic-text-live", info.overlays.has("patch-hp-value") \
		and info.overlays.has("text-hp-value") \
		and info.overlays["text-hp-value"].text == "999 / 1109")
	info.set_dynamic_text("hp-value", "1092 / 1109")
	check("dynamic-text-updates", info.overlays["text-hp-value"].text == "1092 / 1109")

	_finish()


func _finish() -> void:
	var failed := results.filter(func(r): return not r["passed"])
	var report := {"suite": "engine-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var f := FileAccess.open("res://qa/out/contracts.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	f.close()
	print("CONTRACTS %d/%d passed" % [results.size() - failed.size(), results.size()])
	for r in failed:
		printerr("FAIL %s: %s" % [r["contract"], r["detail"]])
	quit(1 if failed.size() > 0 else 0)
