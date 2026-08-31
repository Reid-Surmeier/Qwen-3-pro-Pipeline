class_name Meter
extends RefCounted
## Pure, read-only Meter projection. Rendering is owned by MeterControl.

const Errors = preload("res://control_library/control_errors.gd")


static func project(value: Variant) -> Dictionary:
	if not value is Dictionary:
		return _error("Meter value must be an object")
	for field in ["minimum", "maximum", "current", "fill_pixels"]:
		if not _number(value.get(field)):
			return _error("Meter requires numeric %s" % field)
	var minimum := float(value.minimum)
	var maximum := float(value.maximum)
	var current := float(value.current)
	var fill_pixels := int(value.fill_pixels)
	if minimum >= maximum or current < minimum or current > maximum or fill_pixels <= 0:
		return _error("Meter bounds, current value, or fill pixels are invalid")
	if str(value.get("fill_axis", "")) not in ["horizontal", "vertical"]:
		return _error("Meter fill axis must be horizontal or vertical")
	var ratio := (current - minimum) / (maximum - minimum)
	return {"ok": true, "minimum": minimum, "maximum": maximum,
		"current": current, "ratio": ratio,
		"projected_fill_pixels": int(round(ratio * fill_pixels))}


static func _number(value: Variant) -> bool:
	return (value is int or value is float) and not value is bool \
		and is_finite(float(value))


static func _error(detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": Errors.INVALID_STATE_SET,
		"detail": detail}}
