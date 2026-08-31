extends SceneTree
## Issue #134 frozen System Menu manifest and semantic contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlRuntime = preload("res://control_library/control_runtime.gd")
const SystemMenuWindowState = preload("res://window_state/system_menu_window_state.gd")

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
	_contract_adapter_owns_every_open_window(spec)
	_contract_impossible_history_fails_closed(spec)
	_finish()


func _contract_adapter_owns_every_open_window(spec: Dictionary) -> void:
	var manifest := {
		"schema_version": 3,
		"reference": {
			"path": "res://assets/image-79/system-menu/source-plate.png",
			"sha256": "f4844fa9030b31b233f43244290f729db105f7256e0c0a6e889f0889bb88366f",
			"size": [1536, 1024],
		},
		"windows": [spec.duplicate(true)],
	}
	var unowned: Dictionary = spec.controls.filter(func(control):
		return control.id == "system_menu.sound_settings")[0].duplicate(true)
	unowned.id = "system_menu.extra"
	unowned.value.target_window = "inventory"
	manifest.windows[0].controls.append(unowned)
	var errors := ControlSpec.validate(manifest, func(_path: String) -> bool: return true)
	_check("every-open-window-control-is-adapter-owned",
		errors.any(func(error):
			return error.code == "ControlBindingError" \
			and str(error.path).ends_with(".state_adapter.actions")), str(errors))


func _contract_impossible_history_fails_closed(spec: Dictionary) -> void:
	var adapter: Dictionary = spec.state_adapter
	var zero_version: Dictionary = SystemMenuWindowState.initialize(adapter).state
	zero_version.last_action = "OpenWindow"
	zero_version.last_target = "game_exit"
	var zero_before := JSON.stringify(zero_version)
	var zero_rejected := SystemMenuWindowState.activate(
		adapter, zero_version, "system_menu.sound_settings", 0)
	var forged_commit: Dictionary = SystemMenuWindowState.initialize(adapter).state
	forged_commit.version = 1
	forged_commit.last_action = "OpenWindow"
	forged_commit.last_target = "game_exit"
	var forged_before := JSON.stringify(forged_commit)
	var forged_rejected := SystemMenuWindowState.activate(
		adapter, forged_commit, "system_menu.sound_settings", 1)
	_check("impossible-public-history-fails-closed",
		not zero_rejected.get("ok", true)
		and zero_rejected.error.code == "InvalidControlSpec"
		and JSON.stringify(zero_rejected.state) == zero_before
		and not forged_rejected.get("ok", true)
		and forged_rejected.error.code == "InvalidControlSpec"
		and JSON.stringify(forged_rejected.state) == forged_before,
		str([zero_rejected, forged_rejected]))


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
