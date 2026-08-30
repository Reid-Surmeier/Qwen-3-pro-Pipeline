extends Control
## Issue #125 production tracer desktop. The old release scene remains intact
## while image 79 expands Window-by-Window behind the schema-v3 seam.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlWindowScript = preload("res://control_library/control_window.gd")

var options: ControlWindow
var validation_errors: Array = []
var _last_json := ""


func _ready() -> void:
	if OS.has_feature("web"):
		get_window().content_scale_size = Vector2i(1536, 1024)
		get_window().size = Vector2i(1536, 1024)
	var background := ColorRect.new()
	background.name = "Image79Magenta"
	background.color = Color8(255, 0, 254)
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)
	var loaded: Dictionary = ControlSpec.load_and_validate(
		"res://data/image-79-control-spec.json")
	validation_errors = loaded.errors
	if not validation_errors.is_empty():
		push_error("Image 79 ControlSpec rejected: %s" % str(validation_errors))
		_publish()
		return
	options = ControlWindowScript.new()
	options.configure(loaded.manifest.windows[0])
	options.state_changed.connect(_publish)
	add_child(options)
	_publish()


func qa_state() -> Dictionary:
	return {
		"schema_version": 3,
		"reference_sha256": "f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f",
		"viewport": [1536, 1024],
		"validation_errors": validation_errors,
		"windows": {} if options == null else {"options": options.qa_state()},
	}


func _publish(_window_id: String = "") -> void:
	var json := JSON.stringify(qa_state())
	if json == _last_json:
		return
	_last_json = json
	print(json)
	if OS.has_feature("web"):
		JavaScriptBridge.eval("window.godotQaState = " + json + ";", true)


func _process(_delta: float) -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture-image79=") and not has_meta("capturing"):
			set_meta("capturing", true)
			_capture(argument.trim_prefix("--capture-image79="))


func _capture(path: String) -> void:
	await get_tree().process_frame
	await get_tree().process_frame
	await get_tree().process_frame
	var image := get_viewport().get_texture().get_image()
	image.save_png(path)
	print("CAPTURED IMAGE79 ", path, " ", image.get_width(), "x", image.get_height())
	get_tree().quit()
