class_name WindowStateOverlay
extends Control
## Domain presentation host. ControlWindow owns only this neutral seam; each
## Window adapter remains responsible for its optional rendered facts.

const StatusWindowOverlayScript = preload("res://window_state/status_window_overlay.gd")
const PartyWindowOverlayScript = preload("res://window_state/party_window_overlay.gd")
const ChatRoomOverlayScript = preload("res://window_state/chat_room_overlay.gd")

var status_overlay: StatusWindowOverlay
var party_overlay: PartyWindowOverlay
var chat_room_overlay: ChatRoomOverlay


static func empty_facts() -> Dictionary:
	return {
		"status_overlay": {"visible": false, "version": 0, "text": {}},
		"party_overlay": {"visible": false, "asset": ""},
		"chat_room_overlay": {"visible": false, "rendered_lines": [],
			"visible_row_count": 5, "pending_delivery": null, "version": 0},
	}


func configure(adapter_spec: Dictionary, runtime: ControlRuntime,
		window_size: Vector2) -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	match str(adapter_spec.get("type", "")):
		"status":
			status_overlay = StatusWindowOverlayScript.new()
			status_overlay.configure(adapter_spec, runtime, window_size)
			add_child(status_overlay)
		"party":
			party_overlay = PartyWindowOverlayScript.new()
			party_overlay.configure(adapter_spec, runtime)
			add_child(party_overlay)
		"chat_room":
			chat_room_overlay = ChatRoomOverlayScript.new()
			chat_room_overlay.configure(adapter_spec, runtime)
			add_child(chat_room_overlay)


func rendered_facts() -> Dictionary:
	var facts := empty_facts()
	facts.merge({
		"status_overlay": status_overlay.rendered_facts() \
			if status_overlay != null else {"visible": false, "version": 0, "text": {}},
		"party_overlay": party_overlay.rendered_facts() \
			if party_overlay != null else {"visible": false, "asset": ""},
		"chat_room_overlay": chat_room_overlay.rendered_facts() \
			if chat_room_overlay != null else {"visible": false,
				"rendered_lines": [], "visible_row_count": 5,
				"pending_delivery": null, "version": 0},
	}, true)
	return facts


func set_minimized(minimized: bool) -> void:
	if status_overlay != null:
		status_overlay.set_minimized(minimized)


func refresh() -> void:
	if status_overlay != null:
		status_overlay.refresh()
	if party_overlay != null:
		party_overlay.refresh()
	if chat_room_overlay != null:
		chat_room_overlay.refresh()
