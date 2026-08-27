class_name PlateWindow
extends Control
## Manifest-driven source-pixel window (architecture adopted from the
## figma-ui-ux-qwen-pipeline Codex prototype): the visible chrome IS the
## extracted reference plate; interaction comes from invisible hit regions;
## live behavior draws overlays on demand so the untouched render stays
## pixel-identical to the Reference Screen.

signal hit_activated(window_id: String, hit_id: String)
signal state_changed(window_id: String)

const MINIMIZED_H := 47.0
const SHADOW_ALPHA := 0.4
const SHADOW_W := 3.0

var definition: Dictionary = {}
var window_id := ""
var plate: TextureRect
var hit_nodes := {}
var toggle_state := {}
var dynamic_regions := {}
var overlays := {}
var minimized := false
var state_patches := {}
var last_scroll_dir := 0
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


var _shadow_b: ColorRect
var _shadow_r: ColorRect
var _flash: ColorRect
var _mini_texture: Texture2D
var _full_texture: Texture2D


func _ready() -> void:
	# The window owns its drop shadow (the desktop plate is scrubbed of the
	# reference's baked shadows), so shadows move and fold with the window.
	_shadow_b = ColorRect.new()
	_shadow_b.name = "ShadowB"
	_shadow_b.color = Color(0, 0, 0, SHADOW_ALPHA)
	_shadow_b.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_shadow_b)
	_shadow_r = ColorRect.new()
	_shadow_r.name = "ShadowR"
	_shadow_r.color = Color(0, 0, 0, SHADOW_ALPHA)
	_shadow_r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_shadow_r)
	_update_shadow()

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
			var patch: Dictionary = state_patches.get(hit_id, {})
			toggle_state[hit_id] = bool(patch.get("source_state", false))


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
			_refresh_state_visuals()
		"radio", "tab":
			for other in toggle_state:
				var other_role := str(hit_nodes[other].get_meta("hit").get("role", ""))
				if other_role == role:
					toggle_state[other] = false
			toggle_state[hit_id] = true
			_refresh_state_visuals()
	hit_activated.emit(window_id, hit_id)
	state_changed.emit(window_id)


func _toggle_minimized() -> void:
	## Snap between the full plate and the composited collapsed plate
	## (title bar + closing border) — a real minimized asset, not a clipped
	## frame. Era-accurate: 2004 clients snap, they do not tween.
	minimized = not minimized
	if _full_texture == null:
		_full_texture = plate.texture
		var mini_path := "res://plates/%s-minimized.png" % window_id
		if ResourceLoader.exists(mini_path):
			_mini_texture = load(mini_path)
	if minimized and _mini_texture != null:
		plate.texture = _mini_texture
		size = Vector2(_expanded_size.x, MINIMIZED_H)
		plate.size = size
	else:
		minimized = false
		plate.texture = _full_texture
		size = _expanded_size
		plate.size = size
	for hit_id in hit_nodes:
		var node: Control = hit_nodes[hit_id]
		if node.position.y + node.size.y > MINIMIZED_H:
			node.visible = not minimized
	for key in overlays:
		var overlay_node: Control = overlays[key]
		if overlay_node.position.y + overlay_node.size.y > MINIMIZED_H:
			overlay_node.visible = not minimized
	_update_shadow()


func _update_shadow() -> void:
	## The reference frame is the authority: at the home position the desktop
	## is pixel-exact and windows cast no synthesized shadow. A displaced or
	## minimized window is a new surface, so it owns a shadow that moves with it.
	var displaced := minimized or position != Vector2(
		float(definition.geometry.x), float(definition.geometry.y))
	_shadow_b.visible = displaced
	_shadow_r.visible = displaced
	var h := MINIMIZED_H if minimized else size.y
	var w := _expanded_size.x if _expanded_size != Vector2.ZERO else size.x
	_shadow_b.position = Vector2(SHADOW_W, h)
	_shadow_b.size = Vector2(w, SHADOW_W)
	_shadow_r.position = Vector2(w, SHADOW_W)
	_shadow_r.size = Vector2(SHADOW_W, h)


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
			# ADR 0009 item 13: pointer-down shows visible feedback and must
			# not trigger the action before release.
			move_to_front()
			if role == "drag":
				_dragging = true
				_drag_offset = event.global_position - global_position
			elif not hit.get("disabled", false):
				if role == "scroll":
					# upper half scrolls up, lower half scrolls down
					last_scroll_dir = -1 if event.position.y < node.size.y / 2.0 else 1
				_show_press_flash(node)
		else:
			_clear_press_flash()
			if _dragging:
				_dragging = false
			elif role != "drag":
				activate(str(hit.id))


func _refresh_state_visuals() -> void:
	## Stateful bitmap controls show their toggled state via derived patches
	## (data/state-patches.json). When state matches the source, the patch is
	## removed so the untouched plate pixels show through.
	for hit_id in state_patches:
		var patch: Dictionary = state_patches[hit_id]
		var node_name := "state-" + str(hit_id)
		var current: TextureRect = overlays.get(node_name)
		var state: bool = toggle_state.get(hit_id, false)
		var asset = patch.get("on_asset") if state else patch.get("off_asset")
		if state == bool(patch.get("source_state", false)) or asset == null:
			if current != null:
				current.queue_free()
				overlays.erase(node_name)
			continue
		if current == null:
			current = TextureRect.new()
			current.name = node_name
			current.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			current.mouse_filter = Control.MOUSE_FILTER_IGNORE
			current.position = Vector2(patch.pos[0], patch.pos[1])
			current.size = Vector2(patch.size[0], patch.size[1])
			add_child(current)
			overlays[node_name] = current
		current.texture = load(str(asset))


func _show_press_flash(node: Control) -> void:
	_clear_press_flash()
	_flash = ColorRect.new()
	_flash.name = "PressFlash"
	_flash.color = Color(0, 0, 0, 0.16)
	_flash.position = node.position
	_flash.size = node.size
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_flash)


func _clear_press_flash() -> void:
	if _flash != null and is_instance_valid(_flash):
		_flash.queue_free()
	_flash = null


func _input(event: InputEvent) -> void:
	if not _dragging:
		return
	if event is InputEventMouseMotion:
		global_position = event.global_position - _drag_offset
		_update_shadow()
	elif event is InputEventMouseButton \
			and event.button_index == MOUSE_BUTTON_LEFT and not event.pressed:
		_dragging = false


static func _rect(values: Array) -> Rect2:
	return Rect2(float(values[0]), float(values[1]), float(values[2]), float(values[3]))
