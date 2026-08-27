class_name PlateWindow
extends Control
## Manifest-driven source-pixel window (architecture adopted from the
## figma-ui-ux-qwen-pipeline Codex prototype): the visible chrome IS the
## extracted reference plate; interaction comes from invisible hit regions;
## live behavior draws overlays on demand so the untouched render stays
## pixel-identical to the Reference Screen.

signal hit_activated(window_id: String, hit_id: String)
signal state_changed(window_id: String)

const TITLE_FOLD_H := 46.0

var definition: Dictionary = {}
var window_id := ""
var plate: TextureRect
var hit_nodes := {}
var toggle_state := {}
var dynamic_regions := {}
var overlays := {}
var minimized := false
var _dragging := false
var _drag_offset := Vector2.ZERO
var _expanded_size := Vector2.ZERO


func configure(value: Dictionary) -> void:
	definition = value
	window_id = str(value.id)
	name = window_id
	var g: Dictionary = value.geometry
	position = Vector2(float(g.x), float(g.y))
	size = Vector2(float(g.width), float(g.height))
	_expanded_size = size


func _ready() -> void:
	clip_contents = true
	plate = TextureRect.new()
	plate.name = "Plate"
	plate.texture = load(str(definition.plate))
	plate.position = Vector2.ZERO
	plate.size = _expanded_size
	plate.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	plate.stretch_mode = TextureRect.STRETCH_SCALE
	plate.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(plate)

	for entry in definition.get("dynamic", []):
		dynamic_regions[str(entry.id)] = _rect(entry.r)

	for hit in definition.hits:
		var node := Control.new()
		var hit_id := str(hit.id)
		node.name = "hit-" + hit_id
		var rect := _rect(hit.r)
		node.position = rect.position
		node.size = rect.size
		node.mouse_filter = Control.MOUSE_FILTER_STOP
		node.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		node.set_meta("hit", hit)
		node.gui_input.connect(_on_hit_input.bind(node))
		add_child(node)
		hit_nodes[hit_id] = node
		if str(hit.get("role", "")) in ["checkbox", "radio", "tab"]:
			toggle_state[hit_id] = false


func activate(hit_id: String) -> void:
	var hit: Dictionary = hit_nodes[hit_id].get_meta("hit")
	if hit.get("disabled", false):
		return
	var role := str(hit.get("role", "button"))
	match role:
		"minimize":
			_toggle_minimized()
		"close":
			visible = false
		"checkbox":
			toggle_state[hit_id] = not toggle_state[hit_id]
		"radio", "tab":
			for other in toggle_state:
				var other_role := str(hit_nodes[other].get_meta("hit").get("role", ""))
				if other_role == role:
					toggle_state[other] = false
			toggle_state[hit_id] = true
	hit_activated.emit(window_id, hit_id)
	state_changed.emit(window_id)


func _toggle_minimized() -> void:
	minimized = not minimized
	var tween := create_tween()
	if minimized:
		tween.tween_property(self, "size", Vector2(_expanded_size.x, TITLE_FOLD_H), 0.12)
	else:
		tween.tween_property(self, "size", _expanded_size, 0.12)


func set_dynamic_text(region_id: String, text: String, font_size: int = 24,
		color: Color = Color8(30, 34, 44)) -> void:
	## Swap a dynamic region to its clean-plate patch and mount live text.
	var rect: Rect2 = dynamic_regions[region_id]
	if not overlays.has("patch-" + region_id):
		var clean_path := "res://plates/%s-clean.png" % window_id
		if ResourceLoader.exists(clean_path):
			var atlas := AtlasTexture.new()
			atlas.atlas = load(clean_path)
			atlas.region = rect
			var patch := TextureRect.new()
			patch.name = "patch-" + region_id
			patch.texture = atlas
			patch.position = rect.position
			patch.size = rect.size
			patch.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			patch.mouse_filter = Control.MOUSE_FILTER_IGNORE
			add_child(patch)
			overlays["patch-" + region_id] = patch
	var label: Label = overlays.get("text-" + region_id)
	if label == null:
		label = Label.new()
		label.name = "text-" + region_id
		label.position = rect.position
		label.size = rect.size
		label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(label)
		overlays["text-" + region_id] = label
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	label.text = text
	state_changed.emit(window_id)


func overlay(region_id: String, node: Control) -> void:
	## Place a live node over a dynamic region; source pixels stay everywhere else.
	if overlays.has(region_id):
		overlays[region_id].queue_free()
	var rect: Rect2 = dynamic_regions[region_id]
	node.position = rect.position
	node.size = rect.size
	add_child(node)
	overlays[region_id] = node


func _on_hit_input(event: InputEvent, node: Control) -> void:
	var hit: Dictionary = node.get_meta("hit")
	var role := str(hit.get("role", "button"))
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			move_to_front()
			if role == "drag":
				_dragging = true
				_drag_offset = event.global_position - global_position
			else:
				activate(str(hit.id))
		else:
			_dragging = false


func _input(event: InputEvent) -> void:
	if not _dragging:
		return
	if event is InputEventMouseMotion:
		global_position = event.global_position - _drag_offset
	elif event is InputEventMouseButton \
			and event.button_index == MOUSE_BUTTON_LEFT and not event.pressed:
		_dragging = false


static func _rect(values: Array) -> Rect2:
	return Rect2(float(values[0]), float(values[1]), float(values[2]), float(values[3]))
