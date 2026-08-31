class_name MeterControl
extends Control
## Source-owned Meter visual with factual manifest projection.

signal changed(control_id: String, result: Dictionary)

var spec: Dictionary
var runtime: ControlRuntime
var visual: TextureRect


func configure(control_spec: Dictionary, control_runtime: ControlRuntime) -> void:
	spec = control_spec
	runtime = control_runtime
	name = str(spec.id).replace(".", "-")
	position = Vector2(float(spec.geometry.x), float(spec.geometry.y))
	size = Vector2(float(spec.geometry.width), float(spec.geometry.height))
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	visual = TextureRect.new()
	visual.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	visual.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	visual.stretch_mode = TextureRect.STRETCH_KEEP
	visual.mouse_filter = Control.MOUSE_FILTER_IGNORE
	visual.texture = load(runtime.visual_asset(spec.id))
	add_child(visual)


func rendered_facts() -> Dictionary:
	return {"rendered_asset": str(visual.texture.resource_path),
		"rendered_texture_size": [visual.texture.get_width(), visual.texture.get_height()]}
