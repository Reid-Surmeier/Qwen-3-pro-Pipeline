extends Panel
## Prototype B (#137): the same window as engine-native controls under a source-pixel
## Theme, with live text everywhere. Artwork: replica-b/assets/theme (all cut from
## image 79). Behaviour: docs/research/ro-behaviour-cards.md. No tweens anywhere.

const T := "res://assets/theme/"
const SKINS := ["Classic Blue", "<Basic Skin>", "scribbling kid", "tanublue"]
const EXPANDED := Vector2(424, 202)
const MINI := Vector2(424, 28)
const VIEWPORT := Vector2(1536, 1024)

var bgm := 87.0
var effect := 52.0
var bgm_on := false
var effect_on := false
var footer := {"attack": false, "skill": true, "item": true, "option": false}
var skin := "Classic Blue"
var minimized := false
var dragging_window := false
var drag_offset := Vector2.ZERO
var hovered := ""
var pressed := ""
var interaction_log: Array = []

var font: FontFile
var ink: Color
var title_ink: Color
var sliders := {}
var body: Control
var mini_rect: TextureRect
var opt_btn: OptionButton

func _tex(p: String) -> Texture2D: return load(T + p)

func _sbtex(p: String, m: int) -> StyleBoxTexture:
	var sb := StyleBoxTexture.new(); sb.texture = _tex(p)
	sb.texture_margin_left = m; sb.texture_margin_right = m
	sb.texture_margin_top = m; sb.texture_margin_bottom = m
	return sb

func _log(control: String, event: String, detail := {}) -> void:
	interaction_log.append({"control": control, "event": event, "detail": detail,
		"ms": Time.get_ticks_msec()})
	get_parent()._publish_qa()

func _ready() -> void:
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(T + "theme-manifest.json"))
	var tk: Dictionary = manifest["tokens"]
	ink = Color8(tk["label_ink"][0], tk["label_ink"][1], tk["label_ink"][2])
	title_ink = Color8(tk["title_ink"][0], tk["title_ink"][1], tk["title_ink"][2])
	font = load("res://fonts/DotGothic16-Regular.ttf")
	font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	font.hinting = TextServer.HINTING_NONE
	font.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	size = EXPANDED
	add_theme_stylebox_override("panel", _sbtex("chrome-plate.png", 8))
	clip_contents = false
	body = Control.new(); body.name = "Body"; body.mouse_filter = Control.MOUSE_FILTER_PASS
	body.set_anchors_preset(Control.PRESET_FULL_RECT); add_child(body)
	_build_title(); _build_sliders(); _build_checks(); _build_dropdown(); _build_mini()
	_log("window", "ready")

func _label(text: String, pos: Vector2, px: int, colr: Color, parent: Control = null) -> Label:
	var l := Label.new(); l.text = text; l.position = pos
	l.add_theme_font_override("font", font); l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", colr); l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	(parent if parent else body).add_child(l); return l

func _texbtn(id: String, base: String, pos: Vector2, cb: Callable) -> TextureButton:
	var b := TextureButton.new(); b.name = id; b.position = pos
	b.texture_normal = _tex(base + ".png"); b.texture_hover = _tex(base + "-hover.png")
	b.texture_pressed = _tex(base + "-pressed.png")
	b.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	b.pressed.connect(cb)
	b.button_down.connect(func(): pressed = id; _log(id, "down"))
	b.button_up.connect(func(): pressed = ""; _log(id, "up"))
	b.mouse_entered.connect(func(): hovered = id; get_parent()._publish_qa())
	b.mouse_exited.connect(func(): if hovered == id: hovered = ""; get_parent()._publish_qa())
	body.add_child(b); return b

func _build_title() -> void:
	var strip := Control.new(); strip.name = "TitleDrag"
	strip.position = Vector2.ZERO; strip.size = Vector2(370, 24)
	strip.mouse_filter = Control.MOUSE_FILTER_STOP
	strip.mouse_default_cursor_shape = Control.CURSOR_MOVE
	strip.gui_input.connect(_on_title_input)
	add_child(strip)
	var icon := TextureRect.new(); icon.texture = _tex("title-icon.png")
	icon.position = Vector2(5, 3); icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(icon)
	_label("オプション", Vector2(32, 2), 17, title_ink, self)
	var m := _texbtn("minimize", "btn-minimize", Vector2(373, 8), _toggle_minimized)
	m.reparent(self)   # must stay clickable while the body is hidden (restore!)
	var c := _texbtn("close", "btn-close", Vector2(397, 4), func(): _close("close-button"))
	c.reparent(self)

func _slider_row(id: String, y_arrow: float, y_track: float, start: float) -> void:
	var track := TextureRect.new(); track.texture = _tex("slider-track.png")
	track.position = Vector2(131, y_track); track.mouse_filter = Control.MOUSE_FILTER_IGNORE
	body.add_child(track)
	var s := HSlider.new(); s.name = id; s.min_value = 0; s.max_value = 100; s.step = 1
	s.value = start; s.position = Vector2(130, y_track - 1); s.size = Vector2(227, 17)
	s.focus_mode = Control.FOCUS_ALL; s.scrollable = true
	s.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	s.add_theme_icon_override("grabber", _tex("slider-thumb.png"))
	s.add_theme_icon_override("grabber_highlight", _tex("slider-thumb-hover.png"))
	s.add_theme_stylebox_override("slider", StyleBoxEmpty.new())
	s.add_theme_stylebox_override("grabber_area", StyleBoxEmpty.new())
	s.add_theme_stylebox_override("grabber_area_highlight", StyleBoxEmpty.new())
	s.drag_started.connect(func():
		pressed = id; s.add_theme_icon_override("grabber", _tex("slider-thumb-pressed.png"))
		s.add_theme_icon_override("grabber_highlight", _tex("slider-thumb-pressed.png"))
		_log(id, "drag-start"))
	s.drag_ended.connect(func(changed: bool):
		pressed = ""; s.add_theme_icon_override("grabber", _tex("slider-thumb.png"))
		s.add_theme_icon_override("grabber_highlight", _tex("slider-thumb-hover.png"))
		_log(id, "drag-end", {"value": s.value, "changed": changed}))
	s.value_changed.connect(func(v: float):
		if id == "bgm": bgm = v
		else: effect = v
		_log(id, "value", {"value": v}))
	s.mouse_entered.connect(func(): hovered = id + "_slider"; get_parent()._publish_qa())
	s.mouse_exited.connect(func(): if hovered == id + "_slider": hovered = ""; get_parent()._publish_qa())
	body.add_child(s); sliders[id] = s
	_texbtn(id + "_arrow_left", "slider-left", Vector2(115, y_arrow), func(): s.value -= 2)
	_texbtn(id + "_arrow_right", "slider-right", Vector2(355, y_arrow), func(): s.value += 2)

func _build_sliders() -> void:
	_label("BGM", Vector2(30, 49), 16, ink)
	_label("Effect", Vector2(22, 81), 16, ink)
	_slider_row("bgm", 48.0, 53.0, bgm)
	_slider_row("effect", 80.0, 85.0, effect)

func _check(id: String, pos: Vector2, small: bool, start: bool, cb: Callable) -> CheckBox:
	var c := CheckBox.new(); c.name = id; c.position = pos; c.button_pressed = start
	var suffix := "-small" if small else ""
	c.add_theme_icon_override("checked", _tex("check-on%s.png" % suffix))
	c.add_theme_icon_override("unchecked", _tex("check-off%s.png" % suffix))
	for st in ["normal", "pressed", "hover_pressed", "focus"]:
		c.add_theme_stylebox_override(st, StyleBoxEmpty.new())
	var hov := StyleBoxFlat.new(); hov.draw_center = false
	hov.border_color = Color(title_ink, 0.55); hov.set_border_width_all(1)
	c.add_theme_stylebox_override("hover", hov)
	c.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	c.toggled.connect(func(v: bool): cb.call(v); _log(id, "toggle", {"on": v}))
	c.mouse_entered.connect(func(): hovered = id; get_parent()._publish_qa())
	c.mouse_exited.connect(func(): if hovered == id: hovered = ""; get_parent()._publish_qa())
	body.add_child(c); return c

func _build_checks() -> void:
	_check("bgm_on", Vector2(377, 53), true, bgm_on, func(v): bgm_on = v)
	_label("on", Vector2(396, 52), 14, ink)
	_check("effect_on", Vector2(377, 84), true, effect_on, func(v): effect_on = v)
	_label("on", Vector2(396, 83), 14, ink)
	var xs := {"attack": 26.0, "skill": 116.0, "item": 188.0, "option": 283.0}
	var lx := {"attack": 49.0, "skill": 139.0, "item": 210.0, "option": 306.0}
	for key in xs.keys():
		_check("cb_" + key, Vector2(xs[key], 169), false, footer[key],
			func(v): footer[key] = v)
		_label(key, Vector2(lx[key], 168), 14, ink)

func _build_dropdown() -> void:
	_label("Skin", Vector2(28, 121), 16, ink)
	opt_btn = OptionButton.new(); opt_btn.name = "skin"
	opt_btn.position = Vector2(114, 118); opt_btn.size = Vector2(300, 32)
	for s_name in SKINS: opt_btn.add_item(s_name)
	opt_btn.selected = 0
	opt_btn.alignment = HORIZONTAL_ALIGNMENT_CENTER
	opt_btn.add_theme_font_override("font", font)
	opt_btn.add_theme_font_size_override("font_size", 16)
	opt_btn.add_theme_color_override("font_color", Color8(30, 30, 30))
	opt_btn.add_theme_color_override("font_hover_color", Color8(30, 30, 30))
	opt_btn.add_theme_color_override("font_pressed_color", Color8(30, 30, 30))
	opt_btn.add_theme_color_override("font_focus_color", Color8(30, 30, 30))
	opt_btn.add_theme_icon_override("arrow", _tex("dropdown-arrow.png"))
	opt_btn.add_theme_stylebox_override("normal", _sbtex("dropdown-field.png", 4))
	var hov := _sbtex("dropdown-field.png", 4); hov.modulate_color = Color(0.93, 0.95, 1.0)
	opt_btn.add_theme_stylebox_override("hover", hov)
	opt_btn.add_theme_stylebox_override("pressed", _sbtex("dropdown-field.png", 4))
	opt_btn.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	opt_btn.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	var pm := opt_btn.get_popup()
	pm.add_theme_stylebox_override("panel", _sbtex("list-panel.png", 4))
	var hbar := StyleBoxTexture.new(); hbar.texture = _tex("list-hover-bar.png")
	pm.add_theme_stylebox_override("hover", hbar)
	pm.add_theme_font_override("font", font)
	pm.add_theme_font_size_override("font_size", 15)
	pm.add_theme_color_override("font_color", ink)
	pm.add_theme_color_override("font_hover_color", Color.WHITE)
	pm.add_theme_icon_override("radio_checked", ImageTexture.new())
	pm.add_theme_icon_override("radio_unchecked", ImageTexture.new())
	pm.add_theme_constant_override("icon_max_width", 1)
	opt_btn.item_selected.connect(func(i: int):
		skin = SKINS[i]; _log("skin", "commit", {"value": skin}))
	pm.about_to_popup.connect(func(): _log("skin", "open"))
	pm.popup_hide.connect(func(): _log("skin", "dismiss"))
	opt_btn.mouse_entered.connect(func(): hovered = "skin"; get_parent()._publish_qa())
	opt_btn.mouse_exited.connect(func(): if hovered == "skin": hovered = ""; get_parent()._publish_qa())
	body.add_child(opt_btn)

func _build_mini() -> void:
	mini_rect = TextureRect.new(); mini_rect.texture = _tex("minimized-window.png")
	mini_rect.position = Vector2.ZERO; mini_rect.visible = false
	mini_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(mini_rect)
	move_child(mini_rect, 0)   # behind the live title icon, label and buttons

func _toggle_minimized() -> void:
	minimized = not minimized
	body.visible = not minimized
	mini_rect.visible = minimized
	add_theme_stylebox_override("panel",
		StyleBoxEmpty.new() if minimized else _sbtex("chrome-plate.png", 8))
	size = MINI if minimized else EXPANDED   # instant — the Source Game has no animation
	_log("minimize", "toggle", {"minimized": minimized})

func _close(how: String) -> void:
	visible = false; _log("window", "close", {"how": how})

func reopen() -> void:
	visible = true; _log("window", "reopen")

func _on_title_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		dragging_window = event.pressed
		if event.pressed: drag_offset = get_global_mouse_position() - position
		_log("title", "drag-start" if event.pressed else "drag-end", {"position": [position.x, position.y]})
	elif event is InputEventMouseMotion and dragging_window and event.button_mask & MOUSE_BUTTON_MASK_LEFT:
		var want := get_global_mouse_position() - drag_offset
		position = Vector2(clampf(round(want.x), 0.0, VIEWPORT.x - size.x),
			clampf(round(want.y), 0.0, VIEWPORT.y - size.y))
		get_parent()._publish_qa()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE and visible:
		_close("escape")   # manual-attested: Esc closes the window

func qa_state() -> Dictionary:
	return {"ready": true, "approach": "B-native-theme", "bgm": bgm, "effect": effect,
		"bgm_on": bgm_on, "effect_on": effect_on, "footer": footer, "skin": skin,
		"skin_open": opt_btn != null and opt_btn.get_popup().visible,
		"minimized": minimized, "visible": visible,
		"position": [roundi(position.x), roundi(position.y)],
		"size": [roundi(size.x), roundi(size.y)],
		"hovered": hovered, "pressed": pressed,
		"bgm_thumb_x": roundi(position.x + 130 + sliders["bgm"].ratio * 227) if sliders.has("bgm") else 0,
		"effect_thumb_x": roundi(position.x + 130 + sliders["effect"].ratio * 227) if sliders.has("effect") else 0,
		"controls": 15, "live_text_labels": 12,
		"interaction_log": interaction_log.slice(max(0, interaction_log.size() - 40))}
