extends SceneTree
## Issue #132 manifest and destination-routing contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")
const Router = preload("res://desktop_router/desktop_action_router.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	var loaded: Dictionary = ControlSpec.load_and_validate(
		"res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(
		func(window): return window.get("id") == "basic_info")
	_check("basic-info-manifest-is-complete", loaded.errors.is_empty()
		and matches.size() == 1 and matches[0].controls.filter(func(control):
			return control.get("type") == "Meter").size() == 4
		and int(matches[0].geometry.width) == 484
		and int(matches[0].geometry.height) == 205
		and int(matches[0].get("minimized_height")) == 28
		and matches[0].get("backing_color") == "#00000000"
		and matches[0].get("display_facts", []).size() == 10,
		str([loaded.errors, matches]))
	if not matches.is_empty():
		var window: Dictionary = matches[0]
		var destinations: Array = []
		for control in window.controls:
			if control.get("initial_semantic_state") == "ready" \
					and control.get("actions", []).any(func(binding):
						return binding.get("action") == "OpenWindow"):
				destinations.append(control)
		_check("six-live-destinations-are-declared", destinations.size() == 6
			and destinations.all(func(control):
				return not str(control.get("value", {}).get("target_window", "")).is_empty()),
			str(destinations))
	var opened := Router.open_window(["basic_info", "status"], "status")
	var missing := Router.open_window(["basic_info", "status", "chat_room"], "friends")
	_check("router-opens-declared-target", opened.get("ok", false)
		and opened.action == "OpenWindow" and opened.target_window == "status",
		str(opened))
	_check("router-rejects-missing-target-atomically", not missing.get("ok", true)
		and missing.error.code == "ActionRoutingError", str(missing))
	_finish()


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "basic-info-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/basic-info-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("BASIC INFO %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
