extends Control
##
## The magenta desktop the オプション window sits on, plus the QA bridge.
##
## Prototype for wayfinder ticket #111 (map #103).  The desktop is flat
## #FF00FF so that anything the window fails to cover is impossible to miss.
##

const OPTIONS_SCRIPT := preload("res://scripts/options_window.gd")
const VIEWPORT := Vector2(1536, 1024)

var window: Control
var reopen_button: Button
var _last_json := ""


func _ready() -> void:
	var bg := ColorRect.new()
	bg.name = "MagentaDesktop"
	bg.color = Color(1, 0, 1)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	window = Control.new()
	window.name = "OptionsWindow"
	window.set_script(OPTIONS_SCRIPT)
	add_child(window)
	window.state_changed.connect(_publish)

	# PROTOTYPE AFFORDANCE, not a Source Game control: ⊗ and Esc both hide the
	# window, and the owner needs a way back in mid-session.  Visible only
	# while the window is hidden, and recorded as such in the manifest notes.
	reopen_button = Button.new()
	reopen_button.name = "ReopenAffordance"
	reopen_button.text = "reopen"
	reopen_button.position = Vector2(8, 6)
	reopen_button.size = Vector2(64, 22)
	reopen_button.flat = true
	reopen_button.focus_mode = Control.FOCUS_NONE
	reopen_button.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	reopen_button.add_theme_color_override("font_color", Color(1, 1, 1))
	reopen_button.add_theme_color_override("font_hover_color", Color(1, 1, 0.6))
	reopen_button.visible = false
	reopen_button.pressed.connect(func() -> void: window.reopen())
	add_child(reopen_button)

	_publish()


func _publish() -> void:
	if window == null:
		return
	reopen_button.visible = not window.visible
	var state: Dictionary = window.qa_state()
	state["desktop"] = {
		"viewport": [int(VIEWPORT.x), int(VIEWPORT.y)],
		"reopen_affordance_visible": reopen_button.visible,
	}
	var json := JSON.stringify(state)
	if json == _last_json:
		return
	_last_json = json
	print(json)
	if OS.has_feature("web"):
		JavaScriptBridge.eval("window.godotQaState = " + json + ";", true)
