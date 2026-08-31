extends SceneTree
## Issue #133 production manifest and runtime contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlRuntime = preload("res://control_library/control_runtime.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(
		func(window): return window.get("id") == "party")
	_check("party-manifest-is-complete", loaded.errors.is_empty()
		and matches.size() == 1 and matches[0].controls.size() == 13
		and matches[0].controls.filter(func(control):
			return control.get("type") == "Meter").size() == 5
		and matches[0].controls.filter(func(control):
			return control.get("type") == "SelectionView").size() == 1
		and matches[0].controls.filter(func(control):
			return control.get("type") == "ChoiceGroup").size() == 1
		and int(matches[0].geometry.width) == 215
		and int(matches[0].geometry.height) == 269
		and not matches[0].controls.any(func(control):
			return str(control.id).contains("minimize")), str([loaded.errors, matches]))
	if matches.is_empty():
		_finish()
		return
	var member_control: Dictionary = matches[0].controls.filter(func(control):
		return control.get("id") == "party.members")[0]
	_check("member-state-sets-are-complete",
		member_control.semantic_states == ["unselected", "selected", "unavailable"]
		and member_control.state_set.has("unavailable")
		and member_control.surfaces.values().all(func(surface):
			return surface.state_set.has("unavailable")), str(member_control))
	var runtime := ControlRuntime.new()
	var configured: Dictionary = runtime.configure(matches[0])
	var initial := runtime.qa_state()
	_check("source-state-renders-through-runtime", configured.get("ok", false)
		and initial.window_state.version == 0
		and initial.window_state.mode == "party"
		and initial.controls["party.mode"].value == "party"
		and initial.controls["party.members"].value == ""
		and initial.controls["party.action.leave"].semantic_state == "available"
		and initial.controls["party.action.search"].semantic_state == "disabled",
		str(initial))
	var selected: Dictionary = runtime.dispatch(
		"party.members", "Activate", {"item": "show_a"})
	var after_selected := runtime.qa_state()
	_check("member-selection-is-one-runtime-version", selected.get("ok", false)
		and selected.action == "SelectPartyMember"
		and after_selected.window_state.version == 1
		and after_selected.window_state.selected_member == "show_a"
		and after_selected.controls["party.members"].value == "show_a", str(after_selected))
	var unavailable_before := JSON.stringify(after_selected.window_state)
	var unavailable: Dictionary = runtime.dispatch("party.action.search", "Activate", {})
	_check("unattested-icon-rejects-without-state-change", not unavailable.get("ok", true)
		and unavailable.error.code == "TransactionRejectedError"
		and JSON.stringify(runtime.qa_state().window_state) == unavailable_before,
		str(unavailable))
	var friends: Dictionary = runtime.dispatch(
		"party.mode", "Activate", {"choice": "friends"})
	var after_friends := runtime.qa_state()
	_check("friends-mode-clears-party-surfaces-atomically", friends.get("ok", false)
		and after_friends.window_state.version == 2
		and after_friends.controls["party.mode"].value == "friends"
		and after_friends.window_state.membership == "none"
		and after_friends.window_state.party_membership == "member"
		and after_friends.controls["party.members"].item_values.values().all(
			func(value): return str(value).is_empty())
		and after_friends.controls["party.members"].semantic_state == "unavailable"
		and after_friends.controls["party.action.leave"].semantic_state == "disabled",
		str(after_friends))
	var party: Dictionary = runtime.dispatch(
		"party.mode", "Activate", {"choice": "party"})
	var left: Dictionary = runtime.dispatch("party.action.leave", "Activate", {})
	var after_left := runtime.qa_state()
	var repeated_before := JSON.stringify(after_left.window_state)
	var repeated: Dictionary = runtime.dispatch("party.action.leave", "Activate", {})
	_check("leave-and-repeat-runtime-contract", party.get("ok", false)
		and left.get("ok", false) and left.action == "LeaveParty"
		and after_left.window_state.version == 4
		and after_left.window_state.membership == "none"
		and after_left.window_state.party_membership == "none"
		and after_left.controls["party.members"].item_values.values().all(
			func(value): return str(value).is_empty())
		and after_left.controls["party.action.leave"].semantic_state == "disabled"
		and not repeated.get("ok", true)
		and repeated.error.code == "TransactionRejectedError"
		and JSON.stringify(runtime.qa_state().window_state) == repeated_before,
		str([party, left, repeated]))
	_finish()


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "party-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/party-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("PARTY %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
