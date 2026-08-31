class_name PartyWindowState
extends RefCounted
## Pure Party transaction interface. Shared Controls forward normalized input;
## this adapter owns mode, membership, selection, permission, and rejection.

const Errors = preload("res://control_library/control_errors.gd")

const MODES := ["friends", "party"]
const MEMBERSHIPS := ["member", "none"]
const LEAVE_ACTION := "party.action.leave"


static func initialize(adapter_spec: Dictionary) -> Dictionary:
	var problem := _validate_spec(adapter_spec)
	if not problem.is_empty():
		return _error(Errors.INVALID_CONTROL_SPEC, problem)
	var state := {
		"version": 0,
		"mode": str(adapter_spec.initial_mode),
		"membership": str(adapter_spec.initial_membership),
		"selected_member": "",
		"visible_members": [],
		"availability": {},
	}
	_refresh(adapter_spec, state)
	return {"ok": true, "state": state}


static func select_mode(adapter_spec: Dictionary, state: Dictionary,
		mode: String, expected_version: int) -> Dictionary:
	var rejected := _preflight(adapter_spec, state, expected_version)
	if not rejected.is_empty():
		return rejected
	if mode not in MODES:
		return _rejected(state, Errors.ACTION_ROUTING,
			"Party mode is not declared: %s" % mode)
	var next := state.duplicate(true)
	next.version = int(state.version) + 1
	next.mode = mode
	_refresh(adapter_spec, next)
	return {"ok": true, "action": "SelectPartyMode", "mode": mode,
		"state": next}


static func select_member(adapter_spec: Dictionary, state: Dictionary,
		member_id: String, expected_version: int) -> Dictionary:
	var rejected := _preflight(adapter_spec, state, expected_version)
	if not rejected.is_empty():
		return rejected
	if str(state.mode) != "party" or str(state.membership) != "member":
		return _rejected(state, Errors.TRANSACTION_REJECTED,
			"Party member selection is unavailable in the current state")
	if member_id not in _member_ids(adapter_spec):
		return _rejected(state, Errors.ACTION_ROUTING,
			"Party member is not declared: %s" % member_id)
	var next := state.duplicate(true)
	next.version = int(state.version) + 1
	next.selected_member = member_id
	return {"ok": true, "action": "SelectPartyMember",
		"member_id": member_id, "state": next}


static func activate_action(adapter_spec: Dictionary, state: Dictionary,
		action_id: String, expected_version: int) -> Dictionary:
	var rejected := _preflight(adapter_spec, state, expected_version)
	if not rejected.is_empty():
		return rejected
	if action_id not in adapter_spec.actions:
		return _rejected(state, Errors.ACTION_ROUTING,
			"Party action is not declared: %s" % action_id)
	if action_id != LEAVE_ACTION:
		return _rejected(state, Errors.TRANSACTION_REJECTED,
			str(adapter_spec.actions[action_id].reason))
	if not bool(state.availability.get(LEAVE_ACTION, false)):
		return _rejected(state, Errors.TRANSACTION_REJECTED,
			"Leave Party is unavailable without active Party membership")
	var next := state.duplicate(true)
	next.version = int(state.version) + 1
	next.membership = "none"
	_refresh(adapter_spec, next)
	return {"ok": true, "action": "LeaveParty", "state": next}


static func _preflight(adapter_spec: Dictionary, state: Dictionary,
		expected_version: int) -> Dictionary:
	var initialized := initialize(adapter_spec)
	if not initialized.get("ok", false):
		return _rejected(state, initialized.error.code, initialized.error.detail)
	var state_problem := _state_problem(adapter_spec, state)
	if not state_problem.is_empty():
		return _rejected(state, Errors.INVALID_CONTROL_SPEC,
			state_problem)
	if int(state.version) != expected_version:
		return _rejected(state, Errors.GESTURE_CONFLICT,
			"Party version changed before the action")
	return {}


static func _refresh(adapter_spec: Dictionary, state: Dictionary) -> void:
	var party_visible := str(state.mode) == "party" \
		and str(state.membership) == "member"
	state.visible_members = _member_ids(adapter_spec) if party_visible else []
	if party_visible:
		if not str(state.selected_member).is_empty() \
				and str(state.selected_member) not in state.visible_members:
			state.selected_member = ""
	else:
		state.selected_member = ""
	var availability := {}
	for action_id in adapter_spec.actions:
		availability[str(action_id)] = action_id == LEAVE_ACTION and party_visible
	state.availability = availability


static func _validate_spec(adapter_spec: Dictionary) -> String:
	if str(adapter_spec.get("type", "")) != "party":
		return "Party adapter type is required"
	if str(adapter_spec.get("initial_mode", "")) not in MODES:
		return "Party initial_mode must be friends or party"
	if str(adapter_spec.get("initial_membership", "")) not in MEMBERSHIPS:
		return "Party initial_membership must be member or none"
	var members: Variant = adapter_spec.get("members")
	if not members is Array or members.size() != 5:
		return "Party source state requires exactly five members"
	var ids := {}
	for member in members:
		if not member is Dictionary or str(member.get("id", "")).is_empty() \
				or str(member.get("name", "")).is_empty() \
				or str(member.get("location", "")).is_empty() \
				or not _positive_integer(member.get("current_hp")) \
				or not _positive_integer(member.get("maximum_hp")) \
				or int(member.current_hp) > int(member.maximum_hp) \
				or ids.has(str(member.id)):
			return "Every Party member requires unique identity, display facts, and valid HP"
		ids[str(member.id)] = true
	var actions: Variant = adapter_spec.get("actions")
	if not actions is Dictionary or actions.size() != 5 or not actions.has(LEAVE_ACTION):
		return "Party requires the five source icon actions including Leave Party"
	for action_id in actions:
		var action: Variant = actions[action_id]
		if not action is Dictionary or str(action_id).is_empty() \
				or str(action.get("permission", "")) not in ["unavailable", "party_member"]:
			return "Every Party action requires a supported permission"
		if action_id == LEAVE_ACTION and str(action.permission) != "party_member":
			return "Leave Party requires party_member permission"
		if action_id != LEAVE_ACTION and (str(action.permission) != "unavailable" \
				or str(action.get("reason", "")).is_empty()):
			return "Unattested Party icons require an unavailable reason"
	return ""


static func _member_ids(adapter_spec: Dictionary) -> Array:
	return adapter_spec.members.map(func(member): return str(member.id))


static func _state_problem(adapter_spec: Dictionary, state: Dictionary) -> String:
	if not state.get("version") is int or int(state.get("version", -1)) < 0 \
			or str(state.get("mode", "")) not in MODES \
			or str(state.get("membership", "")) not in MEMBERSHIPS \
			or not state.get("selected_member") is String \
			or not state.get("visible_members") is Array \
			or not state.get("availability") is Dictionary:
		return "Party state has malformed fields"
	var party_visible := str(state.mode) == "party" and str(state.membership) == "member"
	var expected_visible := _member_ids(adapter_spec) if party_visible else []
	if state.visible_members != expected_visible:
		return "Party visible members contradict mode or membership"
	if not str(state.selected_member).is_empty() \
			and str(state.selected_member) not in expected_visible:
		return "Party selection is not a visible declared member"
	var availability: Dictionary = state.availability
	if availability.size() != adapter_spec.actions.size():
		return "Party availability keys do not match declared actions"
	for action_id in adapter_spec.actions:
		if not availability.has(action_id) or not availability[action_id] is bool:
			return "Party availability must contain Boolean action entries"
		var expected: bool = action_id == LEAVE_ACTION and party_visible
		if bool(availability[action_id]) != expected:
			return "Party action availability contradicts current state"
	return ""


static func _positive_integer(value: Variant) -> bool:
	return (value is int or value is float) and not value is bool \
		and is_finite(float(value)) and float(value) == floor(float(value)) \
		and int(value) > 0


static func _rejected(state: Dictionary, code: String, detail: String) -> Dictionary:
	return {"ok": false, "state": state.duplicate(true),
		"error": {"code": code, "detail": detail}}


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
