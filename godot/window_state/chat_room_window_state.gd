class_name ChatRoomWindowState
extends RefCounted
## Issue #135 pure conversation-log state. Delivery timing is semantic state:
## accepted send clears now, then advances through exactly three engine frames.

const Errors = preload("res://control_library/control_errors.gd")
const SCOPES := ["screen", "party", "guild", "allied_guild"]


static func initialize(spec: Dictionary) -> Dictionary:
	var lines: Variant = spec.get("initial_lines")
	var cycle: Variant = spec.get("row_count_cycle")
	if not lines is Array or lines.size() != 5 or not lines.all(func(line):
		return line is Dictionary and line.get("text") is String \
			and str(line.get("kind", "")) in ["chat", "system"]):
		return _error(Errors.INVALID_CONTROL_SPEC,
			"Chat Room requires five exact initial chat/system lines")
	if not cycle is Array or cycle.is_empty() or not cycle.all(func(value):
		return (value is int or value is float) and not value is bool \
			and is_finite(float(value)) and int(value) == float(value) \
			and int(value) > 0) or int(cycle[0]) != 5:
		return _error(Errors.INVALID_CONTROL_SPEC,
			"Chat Room row cycle must start at the five source rows")
	return {"ok": true, "state": {
		"version": 0,
		"draft": "",
		"lines": lines.duplicate(true),
		"visible_row_count": int(cycle[0]),
		"pending_delivery": null,
		"last_scope": "screen",
		"last_action": "",
	}}


static func edit_draft(spec: Dictionary, state: Dictionary, text: String,
		expected_version: int) -> Dictionary:
	var guarded := _guard(spec, state, expected_version)
	if not guarded.ok:
		return guarded
	var next := state.duplicate(true)
	next.version += 1
	next.draft = text
	next.last_action = "SetChatDraft"
	return {"ok": true, "action": "SetChatDraft", "state": next}


static func submit(spec: Dictionary, state: Dictionary, scope: String,
		expected_version: int) -> Dictionary:
	var guarded := _guard(spec, state, expected_version)
	if not guarded.ok:
		return guarded
	if scope not in SCOPES:
		return _error(Errors.CONTROL_BINDING, "Chat scope is not declared")
	if str(state.get("draft", "")).is_empty():
		return _error(Errors.TRANSACTION_REJECTED, "Empty chat messages are not sent")
	if state.get("pending_delivery") != null:
		return _error(Errors.TRANSACTION_REJECTED,
			"One server echo must settle before another is submitted")
	var next := state.duplicate(true)
	next.version += 1
	next.pending_delivery = {"text": str(state.draft), "scope": scope,
		"frames_remaining": 3}
	next.draft = ""
	next.last_scope = scope
	next.last_action = "SubmitChat"
	return {"ok": true, "action": "SubmitChat", "state": next}


static func advance_frame(spec: Dictionary, state: Dictionary) -> Dictionary:
	var guarded := _guard(spec, state, int(state.get("version", -1)))
	if not guarded.ok:
		return guarded
	if state.get("pending_delivery") == null:
		return {"ok": true, "action": "AdvanceChatFrame", "state": state.duplicate(true),
			"changed": false}
	var next := state.duplicate(true)
	next.pending_delivery.frames_remaining = int(next.pending_delivery.frames_remaining) - 1
	if int(next.pending_delivery.frames_remaining) == 0:
		next.lines.append({"kind": "chat", "speaker": "SakumaRiri",
			"text": str(next.pending_delivery.text),
			"scope": str(next.pending_delivery.scope)})
		next.pending_delivery = null
		next.version += 1
		next.last_action = "AppendChatEcho"
	return {"ok": true, "action": "AdvanceChatFrame", "state": next,
		"changed": true}


static func change_rows(spec: Dictionary, state: Dictionary,
		expected_version: int) -> Dictionary:
	var guarded := _guard(spec, state, expected_version)
	if not guarded.ok:
		return guarded
	var cycle: Array = spec.row_count_cycle
	var current := -1
	for index in cycle.size():
		if int(cycle[index]) == int(state.visible_row_count):
			current = index
			break
	if current < 0:
		return _error(Errors.INVALID_CONTROL_SPEC,
			"Chat visible row count left its declared cycle")
	var next := state.duplicate(true)
	next.version += 1
	next.visible_row_count = int(cycle[(current + 1) % cycle.size()])
	next.last_action = "ChangeChatRows"
	return {"ok": true, "action": "ChangeChatRows", "state": next}


static func _guard(spec: Dictionary, state: Dictionary,
		expected_version: int) -> Dictionary:
	if not state is Dictionary or not state.has("version") \
			or not state.get("lines") is Array or not state.has("draft"):
		return _error(Errors.INVALID_CONTROL_SPEC, "Chat Room state is incomplete")
	if expected_version != int(state.version):
		return _error(Errors.GESTURE_CONFLICT, "Chat Room state version is stale")
	if not spec.get("row_count_cycle") is Array:
		return _error(Errors.INVALID_CONTROL_SPEC, "Chat Room adapter is incomplete")
	return {"ok": true}


static func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
