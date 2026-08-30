extends SceneTree
## Action/QA-state contracts at the public runtime seam from issues #124/#125.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlRuntime = preload("res://control_library/control_runtime.gd")

var results: Array[Dictionary] = []
var runtime


func _init() -> void:
	var loaded: Dictionary = ControlSpec.load_and_validate(
		"res://data/image-79-control-spec.json")
	_check("fixture-valid", loaded.errors.is_empty(), str(loaded.errors))
	runtime = ControlRuntime.new()
	var configured: Dictionary = runtime.configure(loaded.manifest.windows[0])
	_check("runtime-configures", configured.ok, str(configured))
	_contract_toggle_reverses()
	_contract_range_drag_is_monotonic_and_clamped()
	_contract_dropdown_opens_selects_and_dismisses()
	_contract_choice_group_selects_one_declared_choice()
	_contract_unsupported_gesture_fails_closed()
	_contract_qa_state_is_factual()
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _contract_toggle_reverses() -> void:
	var before: String = runtime.qa_state().controls["options.attack"].semantic_state
	var first: Dictionary = runtime.dispatch("options.attack", "Activate", {})
	var during: String = runtime.qa_state().controls["options.attack"].semantic_state
	var second: Dictionary = runtime.dispatch("options.attack", "Activate", {})
	var after: String = runtime.qa_state().controls["options.attack"].semantic_state
	_check("toggle-reversal", first.ok and second.ok and before == "off"
		and during == "on" and after == before, str([first, second]))


func _contract_range_drag_is_monotonic_and_clamped() -> void:
	var values: Array[float] = []
	for index in 31:
		var result: Dictionary = runtime.dispatch("options.bgm", "Drag",
			{"normalized": float(index) / 30.0})
		values.append(float(result.value))
	var monotonic := true
	for index in range(1, values.size()):
		monotonic = monotonic and values[index] >= values[index - 1]
	var low: Dictionary = runtime.dispatch("options.bgm", "Drag", {"normalized": -2.0})
	var high: Dictionary = runtime.dispatch("options.bgm", "Drag", {"normalized": 3.0})
	_check("range-monotonic-clamped", monotonic and values.size() == 31
		and values[0] == 0.0 and values[-1] == 100.0
		and low.value == 0.0 and high.value == 100.0, str(values))


func _contract_dropdown_opens_selects_and_dismisses() -> void:
	var opened: Dictionary = runtime.dispatch("options.skin", "Activate", {})
	var selected: Dictionary = runtime.dispatch("options.skin", "Activate",
		{"choice": "tanublue"})
	runtime.dispatch("options.skin", "Activate", {})
	var dismissed: Dictionary = runtime.dispatch("options.skin", "KeyCommand",
		{"key": "Escape"})
	var state: Dictionary = runtime.qa_state().controls["options.skin"]
	_check("dropdown-lifecycle", opened.ok and selected.ok and dismissed.ok
		and selected.value == "tanublue" and state.value == "tanublue"
		and state.semantic_state == "closed", str(state))


func _contract_choice_group_selects_one_declared_choice() -> void:
	var choice_spec := {
		"id": "fixture", "controls": [{
			"id": "fixture.mode", "type": "ChoiceGroup",
			"interaction_phases": ["idle", "hover", "pressed"],
			"semantic_states": ["ready"], "initial_semantic_state": "ready",
			"state_set": {"ready": {"idle": "fixture", "hover": "fixture",
				"pressed": "fixture"}},
			"gestures": ["Activate"],
			"actions": [{"gesture": "Activate", "action": "SelectChoice"}],
			"value": {"choices": ["one", "two", "three"], "initial": "one"},
		}],
	}
	var choice_runtime = ControlRuntime.new()
	choice_runtime.configure(choice_spec)
	var selected: Dictionary = choice_runtime.dispatch("fixture.mode", "Activate",
		{"choice": "three"})
	var rejected: Dictionary = choice_runtime.dispatch("fixture.mode", "Activate",
		{"choice": "missing"})
	var state: Dictionary = choice_runtime.qa_state().controls["fixture.mode"]
	_check("choice-group-single-selection", selected.ok and selected.value == "three"
		and not rejected.ok and state.value == "three", str([selected, rejected, state]))


func _contract_unsupported_gesture_fails_closed() -> void:
	var before: Dictionary = runtime.qa_state().controls["options.attack"].duplicate(true)
	var result: Dictionary = runtime.dispatch("options.attack", "Drag", {"normalized": 1.0})
	var after: Dictionary = runtime.qa_state().controls["options.attack"]
	_check("unsupported-gesture-fails-closed", not result.ok
		and result.error.code == "UnsupportedGesture"
		and before.semantic_state == after.semantic_state, str(result))


func _contract_qa_state_is_factual() -> void:
	var state: Dictionary = runtime.qa_state()
	_check("qa-state", state.window_id == "options" and state.controls.size() == 11
		and state.controls["options.bgm"].value == 100.0
		and state.controls["options.attack"].interaction_phase == "idle"
		and state.interaction_log.size() >= 38, str(state))


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "control-runtime", "total": results.size(),
		"failed": failed.size(), "results": results}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/control-runtime-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("CONTROL RUNTIME %d/%d passed" % [results.size() - failed.size(), results.size()])
