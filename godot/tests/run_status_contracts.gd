extends SceneTree
## Issue #131 manifest and shared-runtime contracts. These freeze the Status
## adapter seam while leaving the generic Stepper transaction unchanged.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlRuntime = preload("res://control_library/control_runtime.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	_manifest_contract()
	_adversarial_manifest_contracts()
	_runtime_contract()
	_finish()


func _manifest_contract() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(
		func(window): return window.get("id") == "status")
	_check("manifest-status-window", loaded.errors.is_empty() and matches.size() == 1
		and int(matches[0].geometry.x) == 0 and int(matches[0].geometry.y) == 211
		and int(matches[0].geometry.width) == 484
		and int(matches[0].geometry.height) == 208,
		str([loaded.errors, matches]))
	if matches.is_empty():
		return
	var window: Dictionary = matches[0]
	var adapter: Dictionary = window.get("state_adapter", {})
	var step_ids: Array = window.controls.filter(func(control):
		return control.get("type") == "Stepper").map(func(control):
			return str(control.id))
	_check("manifest-six-adapter-owned-steppers", adapter.get("type") == "status"
		and adapter.get("initial_points") == 4 and adapter.attributes.size() == 6
		and adapter.attributes.keys().all(func(control_id): return control_id in step_ids)
		and adapter.presentation.attribute_values.size() == 6
		and adapter.presentation.attribute_costs.size() == 6
		and adapter.presentation.derived_values.size() == 9,
		str([adapter, step_ids]))


func _adversarial_manifest_contracts() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var manifest: Dictionary = loaded.manifest
	var status_index := -1
	for index in manifest.windows.size():
		if manifest.windows[index].get("id") == "status":
			status_index = index
			break
	if status_index < 0:
		_check("malformed-adapters-fail-closed", false, "status manifest absent")
		return
	var mutations: Array[Callable] = [
		func(candidate): candidate.windows[status_index].state_adapter.initial_points = -1,
		func(candidate): candidate.windows[status_index].state_adapter.attributes[
			"status.attribute.str"].key = "Int",
		func(candidate): candidate.windows[status_index].state_adapter.attributes[
			"status.attribute.ghost"] = {"key": "Ghost", "base": 1, "bonus": 0},
		func(candidate): candidate.windows[status_index].state_adapter.derived.Atk.coefficients = {
			"Ghost": 1},
		func(candidate): candidate.windows[status_index].state_adapter.presentation.points.width = 0,
	]
	var rejected := true
	var details := []
	for mutate in mutations:
		var candidate := manifest.duplicate(true)
		mutate.call(candidate)
		var errors := ControlSpec.validate(candidate, func(_path): return true)
		rejected = rejected and errors.any(func(error):
			return error.code in ["InvalidControlSpec", "InvalidGeometry", "ControlBindingError"])
		details.append(errors)
	_check("malformed-adapters-fail-closed", rejected, str(details))


func _runtime_contract() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(
		func(window): return window.get("id") == "status")
	if matches.is_empty():
		_check("runtime-publishes-complete-status-state", false, "status manifest absent")
		return
	var runtime := ControlRuntime.new()
	var configured: Dictionary = runtime.configure(matches[0])
	var initial: Dictionary = runtime.qa_state()
	var first := runtime.dispatch("status.attribute.str", "Activate", {})
	var second := runtime.dispatch("status.attribute.str", "Activate", {})
	var exhausted := runtime.qa_state()
	var rejected := runtime.dispatch("status.attribute.str", "Activate", {})
	var after_rejection := runtime.qa_state()
	var reversed := runtime.dispatch("status.attribute.str", "ContextActivate", {})
	var final := runtime.qa_state()
	_check("runtime-publishes-complete-status-state", configured.get("ok", false)
		and initial.window_state.version == 0 and initial.window_state.points == 4
		and first.get("action") == "StepStatusAttribute"
		and second.get("action") == "StepStatusAttribute"
		and exhausted.window_state.version == 2 and exhausted.window_state.points == 0
		and exhausted.controls["status.attribute.str"].current == 3
		and exhausted.controls["status.attribute.str"].semantic_state == "disabled"
		and exhausted.window_state.derived.Atk == 65,
		str([initial, first, second, exhausted]))
	_check("runtime-rejects-then-right-click-reverses", not rejected.get("ok", true)
		and rejected.error.code == "TransactionRejectedError"
		and after_rejection.window_state == exhausted.window_state
		and reversed.get("action") == "StepStatusAttribute"
		and final.window_state.version == 3 and final.window_state.points == 2
		and final.controls["status.attribute.str"].current == 2
		and final.controls["status.attribute.str"].semantic_state == "available"
		and final.window_state.derived.Atk == 64,
		str([rejected, after_rejection, reversed, final]))
	var int_before: Dictionary = final.window_state.duplicate(true)
	var int_rejected := runtime.dispatch("status.attribute.int", "Activate", {})
	_check("disabled-int-is-atomic", not int_rejected.get("ok", true)
		and int_rejected.error.code == "TransactionRejectedError"
		and runtime.qa_state().window_state == int_before,
		str(int_rejected))


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "status-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/status-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("STATUS %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
