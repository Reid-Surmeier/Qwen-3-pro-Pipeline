extends Control
## Incremental image-79 production desktop. Every integrated Window is built
## from the same validated schema-v3 manifest and publishes factual QA state.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlWindowScript = preload("res://control_library/control_window.gd")
const DesktopActionRouter = preload("res://desktop_router/desktop_action_router.gd")

var options: ControlWindow
var skill_tree: ControlWindow
var inventory: ControlWindow
var storage: ControlWindow
var windows := {}
var validation_errors: Array = []
var last_transaction: Dictionary = {}
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
	for window_spec in loaded.manifest.windows:
		var window: ControlWindow = ControlWindowScript.new()
		window.configure(window_spec)
		window.state_changed.connect(_publish)
		window.action_emitted.connect(_route_desktop_action)
		add_child(window)
		windows[str(window_spec.id)] = window
	options = windows.get("options")
	skill_tree = windows.get("skill_tree")
	inventory = windows.get("inventory")
	storage = windows.get("storage")
	_publish()


func qa_state() -> Dictionary:
	var window_states := {}
	for window_id in windows:
		window_states[window_id] = windows[window_id].qa_state()
	return {
		"schema_version": 3,
		"reference_sha256": "f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f",
		"viewport": [1536, 1024],
		"validation_errors": validation_errors,
		"windows": window_states,
		"last_transaction": last_transaction.duplicate(true),
	}


func _route_desktop_action(window_id: String, control_id: String,
		result: Dictionary) -> void:
	if str(result.get("gesture", "")) != "ModifierDoubleActivate" \
			or window_id not in ["inventory", "storage"]:
		return
	var target_id := "storage" if window_id == "inventory" else "inventory"
	var source_window: ControlWindow = windows.get(window_id)
	var target_window: ControlWindow = windows.get(target_id)
	if source_window == null or target_window == null:
		return
	var source_control := window_id + ".items"
	var target_control := target_id + ".items"
	var slot := str(result.get("value", ""))
	var item := source_window.runtime.selected_logical_item(source_control, slot)
	var source := source_window.runtime.selection_collection(source_control)
	var target := target_window.runtime.selection_collection(target_control)
	var transaction: Dictionary = DesktopActionRouter.transfer(source, target, item,
		int(source.get("version", -1)), int(target.get("version", -1)), ["ctrl"])
	last_transaction = {"ok": bool(transaction.get("ok", false)),
		"source_window": window_id, "target_window": target_id, "item": item,
		"source_version_before": source.get("version"),
		"target_version_before": target.get("version"),
		"error": transaction.get("error")}
	if transaction.get("ok", false):
		source_window.runtime.apply_selection_collection(source_control, transaction.source)
		target_window.runtime.apply_selection_collection(target_control, transaction.target)
		if source_window.runtime.controls.has(window_id + ".scroll"):
			source_window.runtime.sync_scroll_bounds(window_id + ".scroll", source_control)
		if target_window.runtime.controls.has(target_id + ".scroll"):
			target_window.runtime.sync_scroll_bounds(target_id + ".scroll", target_control)
		source_window._refresh_all_controls()
		target_window._refresh_all_controls()
		last_transaction.source_version_after = transaction.source.version
		last_transaction.target_version_after = transaction.target.version
	_publish()


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
