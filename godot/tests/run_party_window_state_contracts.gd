extends SceneTree
## Issue #133 frozen Party Window State Adapter contracts.

const PartyWindowState = preload("res://window_state/party_window_state.gd")

var results: Array[Dictionary] = []
var spec := {
	"type": "party",
	"initial_mode": "party",
	"initial_membership": "member",
	"members": [
		{"id": "sakumariri", "name": "SakumaRiri", "location": "フェイヨン..", "current_hp": 1109, "maximum_hp": 1109},
		{"id": "sebas", "name": "Sebas*", "location": "フェイヨン...", "current_hp": 1340, "maximum_hp": 1340},
		{"id": "anri", "name": "ANRI", "location": "フェイヨン森）", "current_hp": 1762, "maximum_hp": 1762},
		{"id": "show_a", "name": "Show_A", "location": "フェイヨン森..", "current_hp": 1235, "maximum_hp": 1235},
		{"id": "ayana_ishizuka", "name": "AyanaIshizuka", "location": "フェイヨン...", "current_hp": 1028, "maximum_hp": 1028},
	],
	"actions": {
		"party.action.memo": {"permission": "unavailable", "reason": "Source icon behavior is unattested"},
		"party.action.info": {"permission": "unavailable", "reason": "Source icon behavior is unattested"},
		"party.action.target": {"permission": "unavailable", "reason": "Source icon behavior is unattested"},
		"party.action.search": {"permission": "unavailable", "reason": "Source icon behavior is unattested"},
		"party.action.leave": {"permission": "party_member"},
	},
}


func _init() -> void:
	_contract_source_state()
	_contract_mode_switch_is_atomic()
	_contract_member_selection_is_atomic()
	_contract_unavailable_action_rejects_immutably()
	_contract_leave_is_atomic_and_repeat_rejects()
	_contract_stale_version_rejects_immutably()
	_contract_inconsistent_state_rejects_immutably()
	_contract_malformed_spec_fails_closed()
	_finish()


func _contract_source_state() -> void:
	var result: Dictionary = PartyWindowState.initialize(spec)
	var state: Dictionary = result.get("state", {})
	_check("source-state", result.get("ok", false) and state.version == 0
		and state.mode == "party" and state.membership == "member"
		and state.party_membership == "member"
		and state.selected_member == ""
		and state.visible_members.size() == 5
		and state.availability["party.action.leave"]
		and not state.availability["party.action.memo"], str(result))


func _contract_mode_switch_is_atomic() -> void:
	var source: Dictionary = PartyWindowState.initialize(spec).state
	var result: Dictionary = PartyWindowState.select_mode(spec, source, "friends", 0)
	_check("mode-switch-one-complete-state", result.get("ok", false)
		and result.action == "SelectPartyMode" and result.state.version == 1
		and result.state.mode == "friends" and result.state.visible_members.is_empty()
		and result.state.membership == "none"
		and result.state.party_membership == "member"
		and result.state.selected_member == ""
		and result.state.availability.values().all(func(value): return not value)
		and source.version == 0 and source.mode == "party"
		and source.visible_members.size() == 5, str([source, result]))


func _contract_member_selection_is_atomic() -> void:
	var source: Dictionary = PartyWindowState.initialize(spec).state
	var result: Dictionary = PartyWindowState.select_member(spec, source, "show_a", 0)
	_check("member-selection-one-complete-state", result.get("ok", false)
		and result.action == "SelectPartyMember" and result.state.version == 1
		and result.state.selected_member == "show_a"
		and source.selected_member == "" and source.version == 0,
		str([source, result]))


func _contract_unavailable_action_rejects_immutably() -> void:
	var state: Dictionary = PartyWindowState.initialize(spec).state
	var before := JSON.stringify(state)
	var rejected: Dictionary = PartyWindowState.activate_action(
		spec, state, "party.action.search", 0)
	_check("unavailable-action-rejects-immutably", not rejected.get("ok", true)
		and rejected.error.code == "TransactionRejectedError"
		and JSON.stringify(rejected.state) == before and JSON.stringify(state) == before,
		str(rejected))


func _contract_leave_is_atomic_and_repeat_rejects() -> void:
	var source: Dictionary = PartyWindowState.initialize(spec).state
	var left: Dictionary = PartyWindowState.activate_action(
		spec, source, "party.action.leave", 0)
	var before_repeat := JSON.stringify(left.state)
	var repeated: Dictionary = PartyWindowState.activate_action(
		spec, left.state, "party.action.leave", 1)
	_check("leave-and-repeat-contract", left.get("ok", false)
		and left.action == "LeaveParty" and left.state.version == 1
		and left.state.membership == "none" and left.state.party_membership == "none"
		and left.state.selected_member == ""
		and left.state.visible_members.is_empty()
		and left.state.availability.values().all(func(value): return not value)
		and source.membership == "member" and source.visible_members.size() == 5
		and not repeated.get("ok", true)
		and repeated.error.code == "TransactionRejectedError"
		and JSON.stringify(repeated.state) == before_repeat,
		str([source, left, repeated]))


func _contract_stale_version_rejects_immutably() -> void:
	var state: Dictionary = PartyWindowState.initialize(spec).state
	var before := JSON.stringify(state)
	var rejected: Dictionary = PartyWindowState.select_member(
		spec, state, "sebas", 7)
	_check("stale-version-rejects-immutably", not rejected.get("ok", true)
		and rejected.error.code == "GestureConflictError"
		and JSON.stringify(rejected.state) == before, str(rejected))


func _contract_inconsistent_state_rejects_immutably() -> void:
	var inconsistent: Dictionary = PartyWindowState.initialize(spec).state
	inconsistent.mode = "friends"
	var before := JSON.stringify(inconsistent)
	var rejected: Dictionary = PartyWindowState.activate_action(
		spec, inconsistent, "party.action.leave", 0)
	_check("inconsistent-state-fails-closed", not rejected.get("ok", true)
		and rejected.error.code == "InvalidControlSpec"
		and JSON.stringify(rejected.state) == before
		and JSON.stringify(inconsistent) == before, str(rejected))


func _contract_malformed_spec_fails_closed() -> void:
	var malformed := spec.duplicate(true)
	malformed.members[2].maximum_hp = 0
	malformed.actions.erase("party.action.leave")
	var result: Dictionary = PartyWindowState.initialize(malformed)
	_check("malformed-adapter-fails-closed", not result.get("ok", true)
		and result.error.code == "InvalidControlSpec", str(result))


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "party-window-state-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/party-window-state-contracts.json",
		FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("PARTY WINDOW STATE %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
