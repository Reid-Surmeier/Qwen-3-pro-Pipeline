class_name StatusWindowOverlay
extends Control
## Manifest-driven visual projection of the complete Status semantic state.
## The source plate remains untouched at version zero; after a transaction,
## only declared numeric regions are repainted in the source visual language.

var adapter_spec: Dictionary
var runtime: ControlRuntime
var labels := {}
var _minimized := false


func configure(spec: Dictionary, control_runtime: ControlRuntime,
		window_size: Vector2) -> void:
	adapter_spec = spec
	runtime = control_runtime
	name = "StatusOverlay"
	position = Vector2.ZERO
	size = window_size
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	var presentation: Dictionary = adapter_spec.presentation
	_add_label("points", presentation.points)
	for control_id in presentation.attribute_values:
		_add_label("attribute_value:" + str(control_id),
			presentation.attribute_values[control_id])
	for control_id in presentation.attribute_costs:
		_add_label("attribute_cost:" + str(control_id),
			presentation.attribute_costs[control_id])
	for derived_id in presentation.derived_values:
		_add_label("derived:" + str(derived_id),
			presentation.derived_values[derived_id])
	refresh()


func refresh() -> void:
	if runtime == null or labels.is_empty():
		return
	var state: Dictionary = runtime.qa_state().get("window_state", {})
	var differs_from_source: bool = state.get("attributes", {}).values().any(
		func(attribute): return int(attribute.base) != int(attribute.initial_base))
	visible = not _minimized and differs_from_source
	if state.is_empty():
		return
	labels.points.text = str(int(state.points))
	for control_id in state.attributes:
		var attribute: Dictionary = state.attributes[control_id]
		labels["attribute_value:" + str(control_id)].text = "%d + %d" % [
			int(attribute.base), int(attribute.bonus)]
		labels["attribute_cost:" + str(control_id)].text = str(int(attribute.cost))
	for derived_id in state.derived:
		var geometry: Dictionary = adapter_spec.presentation.derived_values[derived_id]
		labels["derived:" + str(derived_id)].text = _format_derived(
			int(state.derived[derived_id]), str(geometry.get("format", "integer")))


func set_minimized(value: bool) -> void:
	_minimized = value
	refresh()


func rendered_facts() -> Dictionary:
	var rendered_text := {}
	for fact_id in labels:
		rendered_text[fact_id] = labels[fact_id].text
	return {"visible": visible, "version": int(runtime.qa_state().get(
		"window_state", {}).get("version", 0)), "text": rendered_text}


func _add_label(fact_id: String, geometry: Dictionary) -> void:
	var background := ColorRect.new()
	background.position = _point(geometry)
	background.size = Vector2(float(geometry.width), float(geometry.height))
	background.color = Color.from_string(str(adapter_spec.presentation.background),
		Color8(247, 247, 247))
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)
	var label := Label.new()
	label.position = background.position
	label.size = background.size
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.add_theme_font_override("font", load(str(adapter_spec.presentation.font)))
	label.add_theme_font_size_override("font_size", int(adapter_spec.presentation.font_size))
	label.add_theme_color_override("font_color", Color.from_string(
		str(adapter_spec.presentation.font_color), Color8(23, 23, 23)))
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(label)
	labels[fact_id] = label


func _format_derived(value: int, format_id: String) -> String:
	match format_id:
		"plus_zero":
			return "%d + 0" % value
		"def_split":
			return "%d + 4" % (value - 4)
		"mdef_split":
			return "5 + %d" % (value - 5)
		"flee_split":
			return "%d + 1" % (value - 1)
		_:
			return str(value)


func _point(geometry: Dictionary) -> Vector2:
	return Vector2(float(geometry.x), float(geometry.y))
