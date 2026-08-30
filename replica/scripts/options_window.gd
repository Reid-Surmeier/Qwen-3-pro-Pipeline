extends Control
##
## The オプション (Options) window of Reference Screen image 79, rebuilt from
## the parts that replica/tools/extract_options.py cuts out of
## artifacts/references/ro-desktop-b/reference-native.png.
##
## Every geometry number below is read from assets/options/manifest.json.  The
## structure and the slider maths are ported from the predecessor repo's
## godot/scripts/options_window.gd, which ADR 0006 names as the canonical
## control quality floor -- with one deliberate change: THERE ARE NO TWEENS.
## Behaviour Card cross-cutting finding 0 measured about forty transitions in
## the Source Game and every one completes inside a single frame at 60 fps, so
## the predecessor's 0.208 s minimize animation is wrong for this game.  Every
## transition here is an instant swap on the frame the input arrives.
##

const ASSETS := "res://assets/options/"
const VIEWPORT := Vector2(1536, 1024)

## Behaviour Card `dropdown` evidence; only `Classic Blue` is legible in this
## Reference Screen, the other three come from the dropdown crops.
const SKINS := ["Classic Blue", "<Basic Skin>", "scribbling kid", "tanublue"]
const LIST_ROW_H := 19
const LIST_FONT_SIZE := 15   # the reference is ~1.5x client scale

const ARROW_STEP := 2.0      # INTENT-SPECIFIED (Behaviour Card `slider`: Unverified)
const WHEEL_STEP := 1.0      # INTENT-SPECIFIED

signal state_changed

var man: Dictionary = {}
var win_org := Vector2.ZERO
var expanded_size := Vector2(424, 202)
var minimized_size := Vector2(424, 28)

# ---- state ---------------------------------------------------------------
var bgm := 0.0
var effect := 0.0
var bgm_on := false
var effect_on := false
var footer := {"attack": false, "skill": true, "item": true, "option": false}
var skin := "Classic Blue"
var skin_open := false
var skin_pointed := -1            # -1 while the pointer is outside the list
var minimized := false
var hovered := ""
var pressed := ""
var dragging_slider := ""
var dragging_window := false
var drag_offset := Vector2.ZERO
var interaction_log: Array = []

# ---- scene ---------------------------------------------------------------
var parts := {}                   # id -> {node, variants, variant, base}
var hits := {}                    # id -> Control
var body_nodes: Array = []
var plate: TextureRect
var min_plate: TextureRect
var skin_menu: Control
var skin_rows: Array = []
var skin_value: Label
var slider_geom := {}
var _tex_cache := {}


# --------------------------------------------------------------------------
func _ready() -> void:
	man = JSON.parse_string(FileAccess.get_file_as_string(ASSETS + "manifest.json"))
	assert(man != null, "assets/options/manifest.json failed to parse")
	var wr: Dictionary = man["window_rect"]
	win_org = Vector2(wr["x"], wr["y"])
	expanded_size = Vector2(wr["w"], wr["h"])

	var mp: Dictionary = man["assets"]["minimized-plate.png"]
	minimized_size = Vector2(mp["size"][0], mp["size"][1])

	var vm: Dictionary = man["measurements"]["slider_value_mapping"]
	bgm = float(vm["bgm_default"])
	effect = float(vm["effect_default"])

	position = win_org
	size = expanded_size
	clip_contents = false          # the open list is NOT clipped by its window
	mouse_filter = Control.MOUSE_FILTER_PASS
	focus_mode = Control.FOCUS_NONE

	_build_visuals()
	_build_skin_menu()
	_build_hits()
	_refresh_all()
	_log("ready", "window", {})
	_publish()


# --------------------------------------------------------------------------
# build

func _tex(file: String) -> Texture2D:
	if not _tex_cache.has(file):
		_tex_cache[file] = load(ASSETS + file)
	return _tex_cache[file]


func _rel(rect: Array) -> Vector2:
	return Vector2(rect[0], rect[1]) - win_org


func _ctrl(id: String) -> Dictionary:
	return man["controls"][id]


func _place_of(id: String) -> Vector2:
	var p: Array = _ctrl(id)["place_in_window"]
	return Vector2(p[0], p[1])


func _add_part(id: String, variants: Dictionary, place: Vector2, in_body := true) -> TextureRect:
	var node := TextureRect.new()
	node.name = "V_" + id
	node.texture = _tex(variants[variants.keys()[0]]["idle"])
	node.position = place
	node.size = node.texture.get_size()
	node.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	node.stretch_mode = TextureRect.STRETCH_KEEP
	node.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(node)
	parts[id] = {"node": node, "variants": variants, "variant": variants.keys()[0], "base": place}
	if in_body:
		body_nodes.append(node)
	return node


func _states(control_id: String) -> Dictionary:
	var s: Dictionary = _ctrl(control_id)["states"]
	return {"idle": s["idle"], "hover": s["hover"], "pressed": s["pressed"]}


func _build_visuals() -> void:
	plate = TextureRect.new()
	plate.name = "CleanPlate"
	plate.texture = _tex("clean-plate.png")
	plate.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	plate.stretch_mode = TextureRect.STRETCH_KEEP
	add_child(plate)
	body_nodes.append(plate)

	min_plate = TextureRect.new()
	min_plate.name = "MinimizedPlate"
	min_plate.texture = _tex("minimized-plate.png")
	min_plate.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	min_plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	min_plate.stretch_mode = TextureRect.STRETCH_KEEP
	min_plate.visible = false
	add_child(min_plate)

	# sliders: track, both arrows, thumb
	for row in ["bgm", "effect"]:
		var meas: Dictionary = man["measurements"][row + "_slider"]
		var track: Array = meas["track"]
		var thumb: Array = meas["thumb"]
		slider_geom[row] = {
			"track": Rect2(Vector2(track[0], track[1]) - win_org, Vector2(track[2], track[3])),
			"thumb_y": thumb[1] - win_org.y,
			"thumb_w": float(thumb[2]),
			"travel": float(track[2] - thumb[2]),
		}
		_add_part(row + "_track", {"only": {"idle": row + "-track.png"}},
			_rel([track[0], track[1]]))
		for side in ["left", "right"]:
			_add_part(row + "_arrow_" + side, {"only": _states(row + "_arrow_" + side)},
				_place_of(row + "_arrow_" + side))
		_add_part(row + "_thumb", {"only": _states(row + "_thumb")}, Vector2.ZERO)

	# the two `on` boxes and the four footer checkboxes: each carries its own
	# square in both states, so the idle frame is exact and a toggle round-trip
	# restores byte-identical pixels (ADR 0006 gate 5)
	for key in ["bgm_on", "effect_on", "cb_attack", "cb_skill", "cb_item", "cb_option"]:
		var cs: Dictionary = _ctrl(key)["states"]
		_add_part(key, {"off": cs["off"], "on": cs["on"]}, _place_of(key))

	# the dropdown
	var fs: Dictionary = _ctrl("dropdown_field")["states"]
	_add_part("dropdown_field", {
		"classic": {"idle": fs["idle"], "hover": fs["hover"], "pressed": fs["pressed"]},
		"blank": {"idle": fs["blank_idle"], "hover": fs["blank_hover"], "pressed": fs["blank_pressed"]},
	}, _place_of("dropdown_field"))
	var as_: Dictionary = _ctrl("dropdown_arrow")["states"]
	_add_part("dropdown_arrow", {
		"closed": {"idle": as_["idle"], "hover": as_["hover"], "pressed": as_["pressed"]},
		"open": {"idle": as_["open"], "hover": as_["open"], "pressed": as_["open"]},
	}, _place_of("dropdown_arrow"))

	# the value Label, used only once a skin other than Classic Blue is chosen
	var fr: Array = man["measurements"]["dropdown"]["field_ink_rect"]
	skin_value = Label.new()
	skin_value.name = "SkinValue"
	skin_value.position = Vector2(fr[0], fr[1]) - win_org
	skin_value.size = Vector2(fr[2], fr[3])
	skin_value.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	skin_value.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	skin_value.mouse_filter = Control.MOUSE_FILTER_IGNORE
	skin_value.visible = false
	_style_label(skin_value, _colour("field_text"))
	add_child(skin_value)
	body_nodes.append(skin_value)

	# the title-bar buttons last, so they sit above the plate
	_add_part("minimize", {"only": _states("minimize")}, _place_of("minimize"), false)
	_add_part("close", {"only": _states("close")}, _place_of("close"), false)


func _colour(token: String) -> Color:
	return Color(man["tokens"][token]["hex"])


func _list_font() -> FontFile:
	var f: FontFile = load("res://fonts/DotGothic16-Regular.ttf")
	f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	f.hinting = TextServer.HINTING_NONE
	f.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	f.force_autohinter = false
	return f


func _style_label(label: Label, colour: Color) -> void:
	label.add_theme_font_override("font", _list_font())
	label.add_theme_font_size_override("font_size", LIST_FONT_SIZE)
	label.add_theme_color_override("font_color", colour)


func _build_skin_menu() -> void:
	# Behaviour Card `dropdown`: the list opens downward, its width matches the
	# field, it is drawn over whatever is beneath it, and one highlight bar
	# serves both "current value" and "pointed row".
	var dd: Array = man["measurements"]["dropdown"]["ink_rect"]
	skin_menu = Control.new()
	skin_menu.name = "SkinMenu"
	skin_menu.position = Vector2(dd[0], dd[1] + dd[3]) - win_org
	skin_menu.size = Vector2(dd[2], SKINS.size() * LIST_ROW_H + 2)
	skin_menu.visible = false
	skin_menu.z_index = 40
	skin_menu.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(skin_menu)

	var panel := Panel.new()
	panel.name = "Panel"
	panel.size = skin_menu.size
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var box := StyleBoxFlat.new()
	box.bg_color = _colour("field_fill")
	box.border_color = _colour("field_border")
	box.set_border_width_all(1)
	box.set_corner_radius_all(0)
	panel.add_theme_stylebox_override("panel", box)
	skin_menu.add_child(panel)

	for i in SKINS.size():
		var row := Control.new()
		row.name = "Row%d" % i
		row.position = Vector2(1, 1 + i * LIST_ROW_H)
		row.size = Vector2(skin_menu.size.x - 2, LIST_ROW_H)
		row.mouse_filter = Control.MOUSE_FILTER_STOP
		row.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		skin_menu.add_child(row)

		var bar := ColorRect.new()
		bar.name = "Bar"
		bar.color = _colour("title_ink_blue")
		bar.size = row.size
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		bar.visible = false
		row.add_child(bar)

		var label := Label.new()
		label.name = "Label"
		label.text = SKINS[i]
		label.position = Vector2(6, 0)
		label.size = Vector2(row.size.x - 12, LIST_ROW_H)
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_style_label(label, _colour("field_text"))
		row.add_child(label)

		var index := i
		row.mouse_entered.connect(func() -> void: _point_row(index))
		row.gui_input.connect(func(e: InputEvent) -> void: _row_input(index, e))
		skin_rows.append({"row": row, "bar": bar, "label": label})

	skin_menu.mouse_exited.connect(func() -> void: _point_row(-1))


func _add_hit(id: String, rect: Rect2, cursor: int, in_body := true) -> Control:
	var c := Control.new()
	c.name = "H_" + id
	c.position = rect.position
	c.size = rect.size
	c.mouse_filter = Control.MOUSE_FILTER_STOP
	c.mouse_default_cursor_shape = cursor
	c.focus_mode = Control.FOCUS_ALL
	c.mouse_entered.connect(func() -> void: _set_hovered(id))
	c.mouse_exited.connect(func() -> void: _clear_hovered(id))
	c.gui_input.connect(func(e: InputEvent) -> void: _hit_input(id, e))
	add_child(c)
	hits[id] = c
	if in_body:
		body_nodes.append(c)
	return c


func _ink_rect(control_id: String) -> Rect2:
	var r: Array = _ctrl(control_id)["ink_rect"]
	return Rect2(Vector2(r[0], r[1]) - win_org, Vector2(r[2], r[3]))


func _build_hits() -> void:
	# The title-bar drag surface stops where ⊖ begins.
	var min_x: float = _ink_rect("minimize").position.x
	_add_hit("title", Rect2(Vector2.ZERO, Vector2(min_x - 1, 28)), Control.CURSOR_MOVE, false)
	_add_hit("minimize", _ink_rect("minimize"), Control.CURSOR_POINTING_HAND, false)
	_add_hit("close", _ink_rect("close"), Control.CURSOR_POINTING_HAND, false)

	for row in ["bgm", "effect"]:
		_add_hit(row + "_left", _ink_rect(row + "_arrow_left"), Control.CURSOR_POINTING_HAND)
		_add_hit(row + "_right", _ink_rect(row + "_arrow_right"), Control.CURSOR_POINTING_HAND)
		_add_hit(row + "_slider", slider_geom[row]["track"], Control.CURSOR_POINTING_HAND)

	var pad: int = int(man["texture_margin_px"])
	for key in ["bgm_on", "effect_on", "cb_attack", "cb_skill", "cb_item", "cb_option"]:
		var r: Array = man["measurements"][key]["ink_rect"]
		_add_hit(key, Rect2(Vector2(r[0], r[1]) - win_org, Vector2(r[2], r[3])),
			Control.CURSOR_POINTING_HAND)
		hits[key].position -= Vector2(pad, pad)
		hits[key].size += Vector2(pad * 2, pad * 2)

	_add_hit("skin_field", _ink_rect("dropdown_field"), Control.CURSOR_POINTING_HAND)
	_add_hit("skin_arrow", _ink_rect("dropdown_arrow"), Control.CURSOR_POINTING_HAND)


# --------------------------------------------------------------------------
# visual state

func _part_for(hit_id: String) -> String:
	match hit_id:
		"bgm_left": return "bgm_arrow_left"
		"bgm_right": return "bgm_arrow_right"
		"effect_left": return "effect_arrow_left"
		"effect_right": return "effect_arrow_right"
		"bgm_slider": return "bgm_thumb"
		"effect_slider": return "effect_thumb"
		"skin_field": return "dropdown_field"
		"skin_arrow": return "dropdown_arrow"
		_: return hit_id


func _refresh_part(id: String) -> void:
	if not parts.has(id):
		return
	var p: Dictionary = parts[id]
	var variant: String = p["variant"]
	var state_set: Dictionary = p["variants"][variant]
	var key := "idle"
	var owner_hit := ""
	for h in hits.keys():
		if _part_for(h) == id:
			owner_hit = h
			break
	if owner_hit != "":
		if pressed == owner_hit and state_set.has("pressed"):
			key = "pressed"
		elif hovered == owner_hit and state_set.has("hover"):
			key = "hover"
	# the slider's thumb only lights when the pointer is actually on the thumb
	if id.ends_with("_thumb") and key == "hover":
		var row := id.split("_")[0]
		if not _pointer_on_thumb(row):
			key = "idle"
	p["node"].texture = _tex(state_set.get(key, state_set["idle"]))


func _pointer_on_thumb(row: String) -> bool:
	var g: Dictionary = slider_geom[row]
	var local: Vector2 = get_local_mouse_position()
	var x: float = _thumb_x(row)
	return local.x >= x - 2.0 and local.x <= x + g["thumb_w"] + 2.0


func _thumb_x(row: String) -> float:
	var g: Dictionary = slider_geom[row]
	var value: float = bgm if row == "bgm" else effect
	return g["track"].position.x + round(value / 100.0 * g["travel"])


func _refresh_sliders() -> void:
	var pad: int = int(man["texture_margin_px"])
	for row in ["bgm", "effect"]:
		var g: Dictionary = slider_geom[row]
		parts[row + "_thumb"]["node"].position = Vector2(_thumb_x(row) - pad, g["thumb_y"] - pad)


func _refresh_checks() -> void:
	parts["bgm_on"]["variant"] = "on" if bgm_on else "off"
	parts["effect_on"]["variant"] = "on" if effect_on else "off"
	for key in footer.keys():
		parts["cb_" + key]["variant"] = "on" if footer[key] else "off"
	for id in ["bgm_on", "effect_on", "cb_attack", "cb_skill", "cb_item", "cb_option"]:
		_refresh_part(id)


func _refresh_dropdown() -> void:
	parts["dropdown_field"]["variant"] = "classic" if skin == SKINS[0] else "blank"
	parts["dropdown_arrow"]["variant"] = "open" if skin_open else "closed"
	skin_value.visible = skin != SKINS[0]
	skin_value.text = skin
	skin_menu.visible = skin_open
	if skin_open:
		skin_menu.move_to_front()
	for i in skin_rows.size():
		var marked: bool = (skin_pointed == i) if skin_pointed >= 0 else (SKINS[i] == skin)
		skin_rows[i]["bar"].visible = marked
		skin_rows[i]["label"].add_theme_color_override(
			"font_color", Color(1, 1, 1) if marked else _colour("field_text"))
	_refresh_part("dropdown_field")
	_refresh_part("dropdown_arrow")


func _refresh_all() -> void:
	_refresh_sliders()
	_refresh_checks()
	_refresh_dropdown()
	for id in parts.keys():
		_refresh_part(id)


# --------------------------------------------------------------------------
# input

func _set_hovered(id: String) -> void:
	if hovered == id:
		return
	var prev := hovered
	hovered = id
	if prev != "":
		_refresh_part(_part_for(prev))
	_refresh_part(_part_for(id))
	_log("hover_enter", id, {})
	_publish()


func _clear_hovered(id: String) -> void:
	if hovered != id:
		return
	hovered = ""
	_refresh_part(_part_for(id))
	_log("hover_exit", id, {})
	_publish()


func _set_pressed(id: String) -> void:
	pressed = id
	_refresh_part(_part_for(id))


func _release_pressed() -> void:
	if pressed == "":
		return
	var id := pressed
	pressed = ""
	_refresh_part(_part_for(id))


func _hit_input(id: String, event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT:
			if mb.pressed:
				hits[id].grab_focus()
				_set_pressed(id)
				_press(id, mb)
			else:
				var was := pressed
				_release_pressed()
				if was == id:
					_release(id)
		elif id.ends_with("_slider") and mb.pressed:
			var row := id.split("_")[0]
			if mb.button_index == MOUSE_BUTTON_WHEEL_UP:
				_step(row, WHEEL_STEP, "wheel")
			elif mb.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_step(row, -WHEEL_STEP, "wheel")
	elif event is InputEventMouseMotion:
		if dragging_slider != "" and id == dragging_slider + "_slider":
			_set_from_pointer(dragging_slider, (event as InputEventMouseMotion).position.x, "drag")
		elif dragging_window and id == "title":
			_drag_window()
		elif id.ends_with("_thumb") or id.ends_with("_slider"):
			_refresh_part(_part_for(id))
	elif event is InputEventKey and (event as InputEventKey).pressed:
		var k := (event as InputEventKey).keycode
		if id.ends_with("_slider"):
			var row2 := id.split("_")[0]
			var handled := true
			if k == KEY_LEFT or k == KEY_DOWN:
				_step(row2, -ARROW_STEP, "key")
			elif k == KEY_RIGHT or k == KEY_UP:
				_step(row2, ARROW_STEP, "key")
			elif k == KEY_HOME:
				_set_value(row2, 0.0, "key")
			elif k == KEY_END:
				_set_value(row2, 100.0, "key")
			else:
				handled = false
			# without this the arrow key ALSO drives Godot's focus-neighbour
			# navigation, focus leaves the slider and only the first press works
			if handled:
				hits[id].accept_event()


func _press(id: String, mb: InputEventMouseButton) -> void:
	match id:
		"title":
			dragging_window = true
			drag_offset = get_global_mouse_position() - position
			_log("press", "title", {})
		"bgm_slider", "effect_slider":
			var row := id.split("_")[0]
			dragging_slider = row
			_set_from_pointer(row, mb.position.x, "press")
		_:
			_log("press", id, {})
	_publish()


func _release(id: String) -> void:
	match id:
		"title":
			dragging_window = false
			_log("release", "title", {"position": [int(position.x), int(position.y)]})
		"minimize":
			_toggle_minimized()
		"close":
			_hide_window("close_button")
		"bgm_left":
			_step("bgm", -ARROW_STEP, "arrow")
		"bgm_right":
			_step("bgm", ARROW_STEP, "arrow")
		"effect_left":
			_step("effect", -ARROW_STEP, "arrow")
		"effect_right":
			_step("effect", ARROW_STEP, "arrow")
		"bgm_slider", "effect_slider":
			dragging_slider = ""
			_log("release", id, {"value": _value_of(id.split("_")[0])})
		"bgm_on":
			bgm_on = not bgm_on
			_refresh_checks()
			_log("toggle", "bgm_on", {"value": bgm_on})
		"effect_on":
			effect_on = not effect_on
			_refresh_checks()
			_log("toggle", "effect_on", {"value": effect_on})
		"cb_attack", "cb_skill", "cb_item", "cb_option":
			var key := id.substr(3)
			footer[key] = not footer[key]
			_refresh_checks()
			_log("toggle", id, {"value": footer[key]})
		"skin_field", "skin_arrow":
			_toggle_skin_list()
	_publish()


func _row_input(index: int, event: InputEvent) -> void:
	if event is InputEventMouseButton:
		var mb := event as InputEventMouseButton
		if mb.button_index == MOUSE_BUTTON_LEFT and not mb.pressed:
			_commit_skin(index)


func _point_row(index: int) -> void:
	if skin_pointed == index:
		return
	skin_pointed = index
	_refresh_dropdown()
	_log("dropdown_point", "skin_list", {"row": index, "name": SKINS[index] if index >= 0 else ""})
	_publish()


func _input(event: InputEvent) -> void:
	# click-outside dismisses the list WITHOUT committing (Behaviour Card
	# `dropdown` records the dismiss gesture as Unverified -- INTENT-SPECIFIED).
	if not skin_open:
		return
	if event is InputEventMouseButton and (event as InputEventMouseButton).pressed:
		var g: Vector2 = (event as InputEventMouseButton).global_position
		var inside := Rect2(skin_menu.global_position, skin_menu.size).has_point(g)
		var on_field := Rect2(hits["skin_field"].global_position, hits["skin_field"].size).has_point(g)
		var on_arrow := Rect2(hits["skin_arrow"].global_position, hits["skin_arrow"].size).has_point(g)
		if not inside and not on_field and not on_arrow:
			_close_skin_list("click_outside")


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and (event as InputEventKey).pressed \
			and (event as InputEventKey).keycode == KEY_ESCAPE:
		if skin_open:
			_close_skin_list("escape")
		elif visible:
			_hide_window("escape")
		get_viewport().set_input_as_handled()


# --------------------------------------------------------------------------
# behaviour

func _value_of(row: String) -> float:
	return bgm if row == "bgm" else effect


func _set_value(row: String, value: float, how: String) -> void:
	var clamped: float = clampf(value, 0.0, 100.0)
	if row == "bgm":
		bgm = clamped
	else:
		effect = clamped
	_refresh_sliders()
	_log("value", row, {"value": snappedf(clamped, 0.01), "how": how,
		"thumb_x": int(position.x + _thumb_x(row))})
	_publish()


func _step(row: String, delta: float, how: String) -> void:
	_set_value(row, _value_of(row) + delta, how)


func _set_from_pointer(row: String, local_x: float, how: String) -> void:
	# The thumb follows the pointer: its centre sits under the cursor and it
	# clamps flush at both track ends (Behaviour Card `slider`, End clamping).
	var g: Dictionary = slider_geom[row]
	var desired_left: float = local_x - g["thumb_w"] * 0.5
	_set_value(row, clampf(desired_left / g["travel"], 0.0, 1.0) * 100.0, how)


func _drag_window() -> void:
	var desired: Vector2 = get_global_mouse_position() - drag_offset
	position = Vector2(
		clampf(round(desired.x), 0.0, VIEWPORT.x - size.x),
		clampf(round(desired.y), 0.0, VIEWPORT.y - size.y))
	_publish()


func _toggle_minimized() -> void:
	# INSTANT. No tween: Behaviour Card cross-cutting finding 0.
	minimized = not minimized
	if skin_open:
		_close_skin_list("minimize")
	size = minimized_size if minimized else expanded_size
	for node in body_nodes:
		node.visible = not minimized
	min_plate.visible = minimized
	if not minimized:
		# the blanket body-visibility sweep above overrides visibility that is
		# derived from state (the Skin value Label is only shown once a skin
		# other than Classic Blue is committed), so reassert it
		_refresh_all()
	position = Vector2(
		clampf(position.x, 0.0, VIEWPORT.x - size.x),
		clampf(position.y, 0.0, VIEWPORT.y - size.y))
	_log("minimize", "minimize", {"minimized": minimized,
		"size": [int(size.x), int(size.y)]})
	_publish()


func _hide_window(how: String) -> void:
	if skin_open:
		_close_skin_list(how)
	visible = false
	hovered = ""
	pressed = ""
	_refresh_all()
	_log("close", "window", {"how": how})
	_publish()


func reopen() -> void:
	visible = true
	_log("reopen", "window", {"how": "prototype_affordance"})
	_publish()


func _toggle_skin_list() -> void:
	skin_open = not skin_open
	skin_pointed = -1
	_refresh_dropdown()
	_log("dropdown", "skin", {"open": skin_open})
	_publish()


func _close_skin_list(how: String) -> void:
	if not skin_open:
		return
	skin_open = false
	skin_pointed = -1
	_refresh_dropdown()
	_log("dropdown", "skin", {"open": false, "how": how, "committed": false})
	_publish()


func _commit_skin(index: int) -> void:
	skin = SKINS[index]
	skin_open = false
	skin_pointed = -1
	_refresh_dropdown()
	_log("dropdown_commit", "skin", {"value": skin})
	_publish()


# --------------------------------------------------------------------------
# QA

func _log(event: String, control: String, detail: Dictionary) -> void:
	interaction_log.append({
		"n": interaction_log.size(),
		"ms": Time.get_ticks_msec(),
		"event": event,
		"control": control,
		"detail": detail,
	})
	if interaction_log.size() > 600:
		interaction_log = interaction_log.slice(interaction_log.size() - 600)


func qa_state() -> Dictionary:
	return {
		"ready": true,
		"bgm": snappedf(bgm, 0.01),
		"effect": snappedf(effect, 0.01),
		"bgm_rounded": int(round(bgm)),
		"effect_rounded": int(round(effect)),
		"bgm_on": bgm_on,
		"effect_on": effect_on,
		"footer": footer,
		"skin": skin,
		"skin_open": skin_open,
		"skin_pointed_row": skin_pointed,
		"skin_pointed_name": SKINS[skin_pointed] if skin_pointed >= 0 else "",
		"minimized": minimized,
		"visible": visible,
		"position": [int(position.x), int(position.y)],
		"size": [int(size.x), int(size.y)],
		"bgm_thumb_x": int(position.x + _thumb_x("bgm")),
		"effect_thumb_x": int(position.x + _thumb_x("effect")),
		"hovered": hovered,
		"pressed": pressed,
		"dragging_slider": dragging_slider,
		"dragging_window": dragging_window,
		"controls": hits.size(),
		"visual_authorities": parts.size() + 2,
		"interaction_log": interaction_log,
	}


func _publish() -> void:
	state_changed.emit()
