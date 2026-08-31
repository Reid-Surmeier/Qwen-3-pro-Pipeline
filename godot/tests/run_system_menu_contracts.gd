extends SceneTree
## Issue #134 frozen System Menu manifest and semantic contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlRuntime = preload("res://control_library/control_runtime.gd")

const BUTTONS := [
	"system_menu.save_point",
	"system_menu.character_select",
	"system_menu.sound_settings",
	"system_menu.environment_settings",
	"system_menu.shortcuts",
	"system_menu.game_exit",
	"system_menu.return_to_game",
]
const TARGETS := {
	"system_menu.save_point": "save_point",
	"system_menu.character_select": "character_select",
	"system_menu.sound_settings": "options",
	"system_menu.environment_settings": "environment_settings",
	"system_menu.shortcuts": "shortcut_settings",
	"system_menu.game_exit": "game_exit",
}

var results: Array[Dictionary] = []


func _init() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(
		func(window): return window.get("id") == "system_menu")
	_check("system-menu-manifest-is-complete", loaded.errors.is_empty()
		and matches.size() == 1 and matches[0].controls.size() == 8
		and int(matches[0].geometry.width) == 204
		and int(matches[0].geometry.height) == 273
		and int(matches[0].minimized_height) == 27
		and str(matches[0].plates.expanded) != str(matches[0].plates.minimized),
		str([loaded.errors, matches]))
	if matches.is_empty():
		_finish()
		return
	var spec: Dictionary = matches[0]
	var ids: Array = spec.controls.map(func(control): return str(control.id))
	_check("seven-source-buttons-and-minimize-are-declared",
		ids == ["system_menu.minimize"] + BUTTONS
		and spec.controls.all(func(control):
			return control.interaction_phases == ["idle", "hover", "pressed"] \
			and control.state_set.has("ready")), str(ids))
	for control_id in TARGETS:
		var entry: Dictionary = spec.controls.filter(func(control):
			return control.id == control_id)[0]
		_check("%s-routes-to-declared-destination" % control_id,
			entry.actions == [{"gesture": "Activate", "action": "OpenWindow"}]
			and str(entry.value.target_window) == TARGETS[control_id], str(entry))
	var return_control: Dictionary = spec.controls.filter(func(control):
		return control.id == "system_menu.return_to_game")[0]
	_check("return-to-game-is-real-close-action",
		return_control.actions == [{"gesture": "Activate", "action": "CloseWindow"}],
		str(return_control))
	var runtime := ControlRuntime.new()
	var configured: Dictionary = runtime.configure(spec)
	var initial := runtime.qa_state()
	var action := runtime.dispatch("system_menu.sound_settings", "Activate", {})
	_check("sound-settings-publishes-options-route", configured.get("ok", false)
		and initial.window_state.version == 0
		and action.get("ok", false) and action.action == "OpenWindow"
		and action.target_window == "options"
		and runtime.qa_state().window_state.version == 1
		and runtime.qa_state().window_state.last_action == "OpenWindow"
		and runtime.qa_state().window_state.last_target == "options",
		str([configured, initial, action, runtime.qa_state()]))
	var before_rejection := JSON.stringify(runtime.qa_state().window_state)
	var rejected := runtime.dispatch("system_menu.game_exit", "Activate", {})
	_check("external-actions-defer-named-router-rejection-immutably",
		rejected.get("ok", false) and rejected.action == "OpenWindow"
		and rejected.target_window == "game_exit"
		and rejected.expected_rejection
		and JSON.stringify(runtime.qa_state().window_state) == before_rejection,
		str([rejected, runtime.qa_state()]))
	_finish()


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "system-menu-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/system-menu-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("SYSTEM MENU %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
