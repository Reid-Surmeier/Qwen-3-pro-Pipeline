class_name WindowStateRuntime
extends RefCounted
## Domain adapter host behind the ControlRuntime seam. Shared Controls know only
## whether an adapter owns a control and consume complete factual state patches.

const Errors = preload("res://control_library/control_errors.gd")
const StatusWindowState = preload("res://window_state/status_window_state.gd")
const PartyWindowState = preload("res://window_state/party_window_state.gd")
const SystemMenuWindowState = preload("res://window_state/system_menu_window_state.gd")
const ChatRoomWindowState = preload("res://window_state/chat_room_window_state.gd")

var adapter_spec: Dictionary = {}
var state: Dictionary = {}


func configure(spec: Dictionary) -> Dictionary:
	adapter_spec = spec.duplicate(true)
	var initialized: Dictionary
	match str(adapter_spec.get("type", "")):
		"status":
			initialized = StatusWindowState.initialize(adapter_spec)
		"party":
			initialized = PartyWindowState.initialize(adapter_spec)
		"system_menu":
			initialized = SystemMenuWindowState.initialize(adapter_spec)
		"chat_room":
			initialized = ChatRoomWindowState.initialize(adapter_spec)
		_:
			return _error(Errors.INVALID_CONTROL_SPEC,
				"Window state adapter type is unsupported")
	if not initialized.get("ok", false):
		return initialized
	state = initialized.state
	return {"ok": true, "state": state.duplicate(true)}


func owns(control_id: String) -> bool:
	match str(adapter_spec.get("type", "")):
		"status":
			return adapter_spec.get("attributes", {}).has(control_id)
		"party":
			var mappings: Dictionary = adapter_spec.get("controls", {})
			return control_id == str(mappings.get("mode", "")) \
				or control_id == str(mappings.get("members", "")) \
				or control_id in mappings.get("actions", [])
		"system_menu":
			return adapter_spec.get("actions", {}).has(control_id)
		"chat_room":
			return control_id == str(adapter_spec.get("controls", {}).get("input", ""))
	return false


func dispatch(control_spec: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	var control_id := str(control_spec.get("id", ""))
	if not owns(control_id):
		return _error(Errors.ACTION_ROUTING,
			"Window state adapter does not own Control: %s" % control_id)
	var result: Dictionary
	match str(adapter_spec.type):
		"status":
			result = _dispatch_status(control_id, gesture, payload)
		"party":
			result = _dispatch_party(control_spec, gesture, payload)
		"system_menu":
			result = _dispatch_system_menu(control_spec, gesture, payload)
		"chat_room":
			result = _dispatch_chat_room(control_spec, gesture, payload)
		_:
			return _error(Errors.INVALID_CONTROL_SPEC,
				"Window state adapter type is unsupported")
	if result.get("ok", false):
		state = result.state
		result.window_state = state.duplicate(true)
	return result


func control_patches() -> Dictionary:
	match str(adapter_spec.get("type", "")):
		"status":
			return _status_patches()
		"party":
			return _party_patches()
		"system_menu":
			return {}
		"chat_room":
			return _chat_room_patches()
	return {}


func advance_frame() -> Dictionary:
	if str(adapter_spec.get("type", "")) != "chat_room":
		return {"ok": true, "changed": false, "state": state.duplicate(true)}
	var result := ChatRoomWindowState.advance_frame(adapter_spec, state)
	if result.get("ok", false):
		state = result.state
		result.window_state = state.duplicate(true)
	return result


func dispatch_window_action(action: String) -> Dictionary:
	if str(adapter_spec.get("type", "")) != "chat_room" \
			or action != "ChangeChatRows":
		return _error(Errors.ACTION_ROUTING,
			"Window state adapter cannot route action: %s" % action)
	var result := ChatRoomWindowState.change_rows(adapter_spec, state,
		int(state.get("version", -1)))
	if result.get("ok", false):
		state = result.state
		result.window_state = state.duplicate(true)
	return result


func _dispatch_status(control_id: String, gesture: String,
		payload: Dictionary) -> Dictionary:
	var direction := 1 if gesture == "Activate" else -1 \
		if gesture == "ContextActivate" else 0
	if direction == 0:
		return _error(Errors.CONTROL_BINDING,
			"Status Stepper accepts Activate or ContextActivate")
	return StatusWindowState.step(adapter_spec, state, control_id, direction,
		int(payload.get("expected_version", state.get("version", -1))))


func _dispatch_party(control_spec: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	var control_id := str(control_spec.id)
	var mappings: Dictionary = adapter_spec.controls
	if control_id == str(mappings.mode):
		if gesture != "Activate" or not payload.has("choice"):
			return _error(Errors.CONTROL_BINDING,
				"Party mode requires an activated choice")
		return PartyWindowState.select_mode(adapter_spec, state,
			str(payload.choice), int(payload.get("expected_version",
			state.get("version", -1))))
	if control_id == str(mappings.members):
		if gesture != "Activate":
			return _error(Errors.CONTROL_BINDING,
				"Party members accept Activate")
		return PartyWindowState.select_member(adapter_spec, state,
			str(payload.get("item", "")), int(payload.get("expected_version",
			state.get("version", -1))))
	if gesture != "Activate":
		return _error(Errors.CONTROL_BINDING,
			"Party action Buttons accept Activate")
	return PartyWindowState.activate_action(adapter_spec, state,
		str(control_spec.get("value", {}).get("action_id", control_id)),
		int(payload.get("expected_version", state.get("version", -1))))


func _dispatch_system_menu(control_spec: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if gesture != "Activate":
		return _error(Errors.CONTROL_BINDING,
			"System Menu destination Buttons accept Activate")
	return SystemMenuWindowState.activate(adapter_spec, state,
		str(control_spec.get("id", "")), int(payload.get("expected_version",
		state.get("version", -1))))


func _dispatch_chat_room(control_spec: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if gesture != "KeyCommand":
		return _error(Errors.CONTROL_BINDING,
			"Chat input accepts KeyCommand")
	var expected := int(payload.get("expected_version", state.get("version", -1)))
	if bool(payload.get("submit", false)):
		return ChatRoomWindowState.submit(adapter_spec, state,
			str(payload.get("scope", "screen")), expected)
	if not payload.has("text") or not payload.text is String:
		return _error(Errors.CONTROL_BINDING,
			"Chat input editing requires complete text")
	return ChatRoomWindowState.edit_draft(adapter_spec, state,
		str(payload.text), expected)


func _status_patches() -> Dictionary:
	var patches := {}
	for control_id in state.get("attributes", {}):
		var attribute: Dictionary = state.attributes[control_id]
		var available := bool(state.availability[control_id])
		patches[str(control_id)] = {
			"current": attribute.base,
			"target": attribute.base,
			"text": str(attribute.base),
			"pending": false,
			"arrows_visible": available,
			"semantic_state": "available" if available else "disabled",
		}
	return patches


func _party_patches() -> Dictionary:
	var mappings: Dictionary = adapter_spec.controls
	var patches := {
		str(mappings.mode): {
			"value": str(state.mode), "text": str(state.mode),
		},
	}
	var values := {}
	for member in adapter_spec.members:
		var member_id := str(member.id)
		values[member_id] = member_id if member_id in state.visible_members else ""
	var members_available: bool = not state.visible_members.is_empty()
	patches[str(mappings.members)] = {
		"item_values": values,
		"value": str(state.selected_member),
		"text": str(state.selected_member),
		"semantic_state": ("unavailable" if not members_available else
			"selected" if not str(state.selected_member).is_empty() else "unselected"),
		"active_surface": str(state.selected_member),
	}
	for action_id in mappings.actions:
		patches[str(action_id)] = {
			"semantic_state": "available" \
				if bool(state.availability.get(str(action_id), false)) else "disabled",
		}
	return patches


func _chat_room_patches() -> Dictionary:
	var controls: Dictionary = adapter_spec.get("controls", {})
	var input_id := str(controls.get("input", ""))
	var scroll_id := str(controls.get("scroll", ""))
	var maximum := maxi(0, state.get("lines", []).size()
		- int(state.get("visible_row_count", 5)))
	var scroll_patch := {"maximum": maximum}
	if str(state.get("last_action", "")) == "AppendChatEcho":
		scroll_patch.merge({"offset": maximum, "value": maximum,
			"semantic_state": "at_start" if maximum == 0 else "at_end"})
	return {
		input_id: {"value": str(state.get("draft", "")),
			"text": str(state.get("draft", "")),
			"semantic_state": "empty" if str(state.get("draft", "")).is_empty() else "editing"},
		scroll_id: scroll_patch,
	}


func _error(code: String, detail: String) -> Dictionary:
	return {"ok": false, "error": {"code": code, "detail": detail}}
