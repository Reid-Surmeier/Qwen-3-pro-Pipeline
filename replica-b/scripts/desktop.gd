extends Control
## Magenta desktop + QA bridge for prototype B. The reopen button is a test affordance.

var reopen_btn: Button

func _ready() -> void:
	var bg := ColorRect.new(); bg.color = Color8(255, 0, 255)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT); bg.z_index = -10
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg); move_child(bg, 0)
	reopen_btn = Button.new(); reopen_btn.text = "reopen"; reopen_btn.flat = true
	reopen_btn.position = Vector2(8, 8); reopen_btn.visible = false
	reopen_btn.add_theme_color_override("font_color", Color.WHITE)
	reopen_btn.pressed.connect(func():
		$Options.reopen(); reopen_btn.visible = false; _publish_qa())
	add_child(reopen_btn)
	_publish_qa()

func _process(_d: float) -> void:
	var want: bool = not $Options.visible
	if reopen_btn.visible != want:
		reopen_btn.visible = want; _publish_qa()

func _publish_qa() -> void:
	var state: Dictionary = $Options.qa_state()
	state["desktop"] = {"viewport": [1536, 1024], "reopen_affordance_visible": reopen_btn.visible if reopen_btn else false}
	if OS.has_feature("web"):
		JavaScriptBridge.eval("window.godotQaState = " + JSON.stringify(state) + ";")
	else:
		print("QA ", JSON.stringify({"bgm": state["bgm"], "skin": state["skin"], "minimized": state["minimized"]}))
