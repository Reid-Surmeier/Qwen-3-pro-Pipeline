class_name PartyWindowOverlay
extends Control
## Source-style empty list surface for Friends and no-membership Party states.

var spec: Dictionary
var runtime: ControlRuntime
var blank: TextureRect


func configure(adapter_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = adapter_spec
	runtime = control_runtime
	var geometry: Dictionary = spec.presentation.geometry
	position = Vector2(float(geometry.x), float(geometry.y))
	size = Vector2(float(geometry.width), float(geometry.height))
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	blank = TextureRect.new()
	blank.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	blank.texture = load(str(spec.presentation.blank_list))
	blank.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	blank.stretch_mode = TextureRect.STRETCH_KEEP
	blank.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(blank)
	refresh()


func refresh() -> void:
	if blank != null:
		blank.visible = runtime.qa_state().window_state.get("visible_members", []).is_empty()


func rendered_facts() -> Dictionary:
	return {"visible": blank != null and blank.visible,
		"asset": str(blank.texture.resource_path) if blank != null else ""}
