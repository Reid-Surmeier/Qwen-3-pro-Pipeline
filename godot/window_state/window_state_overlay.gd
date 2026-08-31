class_name WindowStateOverlay
extends Control
## Domain presentation host. ControlWindow owns only this neutral seam; each
## Window adapter remains responsible for its optional rendered facts.

const StatusWindowOverlayScript = preload("res://window_state/status_window_overlay.gd")
const PartyWindowOverlayScript = preload("res://window_state/party_window_overlay.gd")

var status_overlay: StatusWindowOverlay
var party_overlay: PartyWindowOverlay


static func empty_facts() -> Dictionary:
	return {
		"status_overlay": {"visible": false, "version": 0, "text": {}},
		"party_overlay": {"visible": false, "asset": ""},
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


func rendered_facts() -> Dictionary:
	var facts := empty_facts()
	facts.merge({
		"status_overlay": status_overlay.rendered_facts() \
			if status_overlay != null else {"visible": false, "version": 0, "text": {}},
		"party_overlay": party_overlay.rendered_facts() \
			if party_overlay != null else {"visible": false, "asset": ""},
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
