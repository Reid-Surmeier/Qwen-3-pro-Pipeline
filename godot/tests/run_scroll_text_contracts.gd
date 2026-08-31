extends SceneTree
## Issue #128 frozen ScrollView and TextField semantic contracts.

const ScrollView = preload("res://control_library/scroll_view.gd")
const TextField = preload("res://control_library/text_field.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	var scroll_spec := {"actions": [
		{"gesture": "Wheel", "action": "ScrollStorage"},
		{"gesture": "Activate", "action": "StepStorageScroll"},
		{"gesture": "Drag", "action": "SetStorageScrollOffset"}],
		"value": {"minimum": 0, "maximum": 8, "initial": 0,
			"wheel_rows": 3, "arrow_rows": 1}}
	var scroll_state := {"offset": 0, "semantic_state": "at_start",
		"interaction_phase": "idle", "last_action": ""}
	var one := ScrollView.interact(scroll_spec, scroll_state, "Wheel", {"direction": 99})
	_check("wheel-normalizes-to-three-rows", one.ok and one.offset == 3,
		str([one, scroll_state]))
	var end := ScrollView.interact(scroll_spec, scroll_state, "Wheel", {"direction": 1})
	end = ScrollView.interact(scroll_spec, scroll_state, "Wheel", {"direction": 1})
	end = ScrollView.interact(scroll_spec, scroll_state, "Wheel", {"direction": 1})
	_check("wheel-clamps-exact-end", end.ok and end.offset == 8
		and scroll_state.semantic_state == "at_end", str([end, scroll_state]))
	var arrow := ScrollView.interact(scroll_spec, scroll_state, "Activate",
		{"direction": -1})
	_check("arrow-is-one-row", arrow.ok and arrow.offset == 7, str(arrow))
	var middle := ScrollView.interact(scroll_spec, scroll_state, "Drag",
		{"normalized": 0.375})
	var start := ScrollView.interact(scroll_spec, scroll_state, "Drag",
		{"normalized": -8.0})
	_check("thumb-continuous-and-clamped", middle.ok and middle.offset == 3
		and start.ok and start.offset == 0 and scroll_state.semantic_state == "at_start",
		str([middle, start, scroll_state]))

	var text_spec := {"actions": [{"gesture": "KeyCommand",
		"action": "FilterStorage"}], "value": {"initial": "", "maximum_length": 24,
		"accepted_pattern": "^[A-Za-z0-9 ]*$"}}
	var text_state := {"value": "", "text": "", "semantic_state": "empty",
		"interaction_phase": "idle", "last_action": ""}
	var accepted := TextField.edit(text_spec, text_state, "KeyCommand",
		{"text": "Potion 2"})
	_check("accepted-text-renders", accepted.ok and text_state.text == "Potion 2"
		and text_state.semantic_state == "filtered", str([accepted, text_state]))
	var before := text_state.duplicate(true)
	var rejected := TextField.edit(text_spec, text_state, "KeyCommand",
		{"text": "Potion!"})
	_check("rejected-text-preserves-value", not rejected.ok and text_state == before,
		str([rejected, text_state]))
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "scroll-text", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/scroll-text-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("SCROLL TEXT %d/%d passed" % [results.size() - failed.size(), results.size()])
