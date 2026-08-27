class_name ReplicaWindow
extends Control
## Base window for the RO-HUD replica: source-styled chrome, draggable by the
## title bar, raises on click, minimize button with the source's collapse
## behavior (window folds to its title bar).

const BODY_COLOR := Color8(243, 246, 250)
const BORDER_COLOR := Color8(96, 121, 160)
const TITLE_TEXT_COLOR := Color8(40, 60, 90)
const TITLE_GRAD_TOP := Color8(252, 253, 255)
const TITLE_GRAD_BOTTOM := Color8(196, 216, 240)

var title_text := ""
var window_size := Vector2(400, 300)
var title_bar: Control
var body: Control
var _dragging := false
var _drag_offset := Vector2.ZERO
var _collapsed := false
var _expanded_size := Vector2.ZERO
var resizable := true
var _resizing := false
var _resize_start_size := Vector2.ZERO
var _resize_start_mouse := Vector2.ZERO
var min_size := Vector2(180, 80)

const TITLE_H := 34.0


func _ready() -> void:
	custom_minimum_size = min_size
	size = window_size
	_expanded_size = window_size
	_build_chrome()
	body = Control.new()
	body.name = "Body"
	body.position = Vector2(4, TITLE_H)
	body.size = window_size - Vector2(8, TITLE_H + 4)
	add_child(body)
	_build_body()


func _build_chrome() -> void:
	var frame := Panel.new()
	frame.name = "Frame"
	var sb := StyleBoxFlat.new()
	sb.bg_color = BODY_COLOR
	sb.border_color = BORDER_COLOR
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(6)
	frame.add_theme_stylebox_override("panel", sb)
	frame.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(frame)

	title_bar = Control.new()
	title_bar.name = "TitleBar"
	title_bar.position = Vector2(2, 2)
	title_bar.size = Vector2(window_size.x - 4, TITLE_H - 4)
	add_child(title_bar)

	var grad := Gradient.new()
	grad.colors = PackedColorArray([TITLE_GRAD_TOP, TITLE_GRAD_BOTTOM])
	var grad_tex := GradientTexture2D.new()
	grad_tex.gradient = grad
	grad_tex.fill_from = Vector2(0, 0)
	grad_tex.fill_to = Vector2(0, 1)
	var bar_bg := TextureRect.new()
	bar_bg.name = "BarBg"
	bar_bg.texture = grad_tex
	bar_bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bar_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_bar.add_child(bar_bg)

	var minimize := Button.new()
	minimize.name = "MinimizeButton"
	minimize.text = "⊖"
	minimize.flat = true
	minimize.position = Vector2(4, 1)
	minimize.size = Vector2(28, 28)
	minimize.add_theme_color_override("font_color", Color8(40, 90, 200))
	minimize.add_theme_font_size_override("font_size", 24)
	minimize.pressed.connect(_on_minimize)
	title_bar.add_child(minimize)

	var title := Label.new()
	title.name = "Title"
	title.text = title_text
	title.position = Vector2(38, 2)
	title.size = Vector2(window_size.x - 80, TITLE_H - 8)
	title.add_theme_color_override("font_color", TITLE_TEXT_COLOR)
	title.add_theme_font_size_override("font_size", 24)
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_bar.add_child(title)

	title_bar.gui_input.connect(_on_title_input)

	if resizable:
		var grip := Control.new()
		grip.name = "ResizeGrip"
		grip.size = Vector2(20, 20)
		grip.anchor_left = 1.0
		grip.anchor_top = 1.0
		grip.anchor_right = 1.0
		grip.anchor_bottom = 1.0
		grip.offset_left = -20
		grip.offset_top = -20
		grip.mouse_default_cursor_shape = Control.CURSOR_FDIAGSIZE
		grip.gui_input.connect(_on_grip_input)
		add_child(grip)


func _build_body() -> void:
	pass  # subclasses populate body


func _on_title_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_dragging = true
			_drag_offset = get_global_mouse_position() - global_position
			move_to_front()
		else:
			_dragging = false
	elif event is InputEventMouseMotion and _dragging:
		global_position = get_global_mouse_position() - _drag_offset


func _gui_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed:
		move_to_front()


func _on_grip_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		_resizing = event.pressed
		_resize_start_size = size
		_resize_start_mouse = get_global_mouse_position()
	elif event is InputEventMouseMotion and _resizing and not _collapsed:
		var new_size: Vector2 = _resize_start_size + get_global_mouse_position() - _resize_start_mouse
		resize_to(new_size)


func resize_to(new_size: Vector2) -> void:
	size = new_size.max(min_size)
	_expanded_size = size
	title_bar.size.x = size.x - 4
	body.size = size - Vector2(8, TITLE_H + 4)


func _on_minimize() -> void:
	_collapsed = not _collapsed
	body.visible = not _collapsed
	if _collapsed:
		_expanded_size = size
		var tween := create_tween()
		tween.tween_property(self, "size", Vector2(size.x, TITLE_H), 0.12)
	else:
		var tween := create_tween()
		tween.tween_property(self, "size", _expanded_size, 0.12)


func is_collapsed() -> bool:
	return _collapsed


static func make_label(text: String, pos: Vector2, font_size: int = 24,
		color: Color = Color8(20, 24, 32)) -> Label:
	var label := Label.new()
	label.text = text
	label.position = pos
	label.add_theme_color_override("font_color", color)
	label.add_theme_font_size_override("font_size", font_size)
	return label


static func make_side_button(text: String, pos: Vector2,
		btn_size: Vector2 = Vector2(88, 44)) -> Button:
	var button := Button.new()
	button.text = text
	button.position = pos
	button.size = btn_size
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color8(238, 244, 250)
	sb.border_color = Color8(120, 140, 170)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(8)
	var sb_pressed := sb.duplicate()
	sb_pressed.bg_color = Color8(198, 216, 240)
	var sb_hover := sb.duplicate()
	sb_hover.bg_color = Color8(226, 236, 248)
	button.add_theme_stylebox_override("normal", sb)
	button.add_theme_stylebox_override("pressed", sb_pressed)
	button.add_theme_stylebox_override("hover", sb_hover)
	for state in ["font_color", "font_pressed_color", "font_hover_color",
			"font_hover_pressed_color", "font_focus_color"]:
		button.add_theme_color_override(state, Color8(30, 40, 60))
	button.add_theme_font_size_override("font_size", 22)
	return button
