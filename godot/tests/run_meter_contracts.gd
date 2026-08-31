extends SceneTree
## Issue #132 frozen Meter interface. Meter is intentionally read-only: it
## projects a bounded value into source-owned fill geometry and accepts no
## Gesture Capability.

const Meter = preload("res://control_library/meter.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	var hp := {"minimum": 0, "maximum": 1109, "current": 1092,
		"fill_axis": "horizontal", "fill_pixels": 100}
	var projected: Dictionary = Meter.project(hp)
	_check("meter-projects-bounded-value", projected.get("ok", false)
		and is_equal_approx(float(projected.ratio), 1092.0 / 1109.0)
		and int(projected.projected_fill_pixels) == 98, str(projected))
	for invalid in [
		{"minimum": 10, "maximum": 10, "current": 10, "fill_axis": "horizontal", "fill_pixels": 10},
		{"minimum": 0, "maximum": 10, "current": 11, "fill_axis": "horizontal", "fill_pixels": 10},
		{"minimum": 0, "maximum": 10, "current": 5, "fill_axis": "diagonal", "fill_pixels": 10},
	]:
		var rejected: Dictionary = Meter.project(invalid)
		_check("meter-rejects-malformed-value", not rejected.get("ok", true)
			and rejected.error.code == "InvalidStateSet", str(rejected))
	_finish()


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "meter-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/meter-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("METER %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
