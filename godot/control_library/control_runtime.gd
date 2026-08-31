class_name ControlRuntime
extends RefCounted
## Factual semantic runtime behind the ControlSpec seam. Input arrives as a
## shared Gesture Capability; the runtime applies the declared Window Action
## and exposes observations through qa_state(). Rendering is a separate adapter.

const Errors = preload("res://control_library/control_errors.gd")
const ChoiceGroup = preload("res://control_library/choice_group.gd")
const TabsModule = preload("res://control_library/tabs.gd")
const SelectionViewModule = preload("res://control_library/selection_view.gd")
const StepperModule = preload("res://control_library/stepper.gd")
const StatusWindowState = preload("res://window_state/status_window_state.gd")
const PartyWindowState = preload("res://window_state/party_window_state.gd")
const ScrollViewModule = preload("res://control_library/scroll_view.gd")
const TextFieldModule = preload("res://control_library/text_field.gd")
const MeterModule = preload("res://control_library/meter.gd")

var window_spec: Dictionary = {}
var controls: Dictionary = {}
var interaction_log: Array[Dictionary] = []
var window_state_adapter: Dictionary = {}
var window_state: Dictionary = {}


func configure(spec: Dictionary) -> Dictionary:
	window_spec = spec.duplicate(true)
	controls.clear()
	interaction_log.clear()
	window_state_adapter = window_spec.get("state_adapter", {}).duplicate(true)
	window_state.clear()
	if str(window_state_adapter.get("type", "")) == "status":
		var initialized: Dictionary = StatusWindowState.initialize(window_state_adapter)
		if not initialized.get("ok", false):
			return initialized
		window_state = initialized.state
	elif str(window_state_adapter.get("type", "")) == "party":
		var initialized: Dictionary = PartyWindowState.initialize(window_state_adapter)
		if not initialized.get("ok", false):
			return initialized
		window_state = initialized.state
	for control_spec in window_spec.get("controls", []):
		var control_id := str(control_spec.id)
		var state := {
			"id": control_id,
			"type": str(control_spec.type),
			"interaction_phase": "idle",
			"active_surface": "",
			"semantic_state": str(control_spec.initial_semantic_state),
			"last_action": "",
			"last_gesture": "",
			"last_error": null,
			"geometry": control_spec.get("geometry", {}).duplicate(true),
			"visible": true,
			"z_index": 0,
			"rendered": false,
			"text": "",
			"last_result": {"accepted": false, "action": "", "error": null},
		}
		if str(control_spec.type) == "Stepper":
			var status_attribute: Variant = window_state.get("attributes", {}).get(control_id)
			state.current = status_attribute.base if status_attribute is Dictionary \
				else control_spec.value.current
			state.target = state.current if status_attribute is Dictionary \
				else control_spec.value.target
			state.minimum = control_spec.value.minimum
			state.maximum = control_spec.value.maximum
			state.step = control_spec.value.step
			state.pending = false
			state.arrows_visible = bool(window_state.get("availability", {}).get(
				control_id, true))
			state.semantic_state = ("available" if state.arrows_visible else "disabled") \
				if status_attribute is Dictionary else state.semantic_state
			state.text = str(state.current) if status_attribute is Dictionary \
				else StepperModule.format_value(state.current, state.target)
		elif str(control_spec.type) == "SelectionView":
			state.value = control_spec.value.get("initial")
			state.text = str(state.value)
			state.selected_items = []
			state.opened_item = ""
			state.item_values = control_spec.value.get("item_values", {}).duplicate(true)
			state.item_version = int(control_spec.value.get("initial_version", 0))
			state.drag_state = {"active": false, "source": "", "target": "",
				"motion_samples": 0}
			state.transfer_state = {"active": false, "item": ""}
			state.collection_items = control_spec.value.get("collection_items",
				state.item_values.values()).duplicate()
			state.filtered_items = state.collection_items.duplicate()
			state.filter_text = ""
			state.sort_ascending = true
			state.scroll_offset = 0
			state.capacity = int(control_spec.value.get("capacity",
				state.collection_items.size()))
		elif str(control_spec.type) == "ScrollView":
			state.offset = int(control_spec.value.initial)
			state.value = state.offset
			state.minimum = int(control_spec.value.minimum)
			state.maximum = int(control_spec.value.maximum)
			state.available = bool(control_spec.value.get("available", true))
			state.unavailable_reason = str(control_spec.value.get(
				"unavailable_reason", ""))
		elif str(control_spec.type) == "TextField":
			state.value = str(control_spec.value.initial)
			state.text = state.value
		elif str(control_spec.type) == "Meter":
			var projected: Dictionary = MeterModule.project(control_spec.value)
			if not projected.get("ok", false):
				return projected
			state.minimum = projected.minimum
			state.maximum = projected.maximum
			state.current = projected.current
			state.value = projected.current
			state.ratio = projected.ratio
			state.projected_fill_pixels = projected.projected_fill_pixels
		elif control_spec.has("value"):
			state.value = control_spec.value.get("initial")
			if state.value is String:
				state.text = state.value
		controls[control_id] = {"spec": control_spec.duplicate(true), "state": state}
	if str(window_state_adapter.get("type", "")) == "party":
		_sync_party_controls()
	return {"ok": true, "window_id": str(window_spec.get("id", "")),
		"control_count": controls.size()}


func set_interaction_phase(control_id: String, phase: String, surface: String = "") -> Dictionary:
	if not controls.has(control_id):
		return _reject(control_id, "", Errors.INVALID_CONTROL_SPEC,
			"unknown control id")
	var spec: Dictionary = controls[control_id].spec
	if phase not in spec.interaction_phases:
		return _reject(control_id, "", Errors.INVALID_STATE_SET,
			"undeclared interaction phase: %s" % phase)
	controls[control_id].state.interaction_phase = phase
	controls[control_id].state.active_surface = surface
	return {"ok": true, "interaction_phase": phase, "active_surface": surface}


func dispatch(control_id: String, gesture: String, payload: Dictionary) -> Dictionary:
	if not controls.has(control_id):
		return _reject(control_id, gesture, Errors.INVALID_CONTROL_SPEC,
			"unknown control id")
	var entry: Dictionary = controls[control_id]
	var spec: Dictionary = entry.spec
	if gesture not in spec.gestures:
		return _reject(control_id, gesture, Errors.UNSUPPORTED_GESTURE,
			"gesture is not declared by the control")
	var result: Dictionary
	match str(spec.type):
		"Toggle":
			result = _dispatch_toggle(entry, gesture)
		"Range":
			result = _dispatch_range(entry, gesture, payload)
		"Dropdown":
			result = _dispatch_dropdown(entry, gesture, payload)
		"ChoiceGroup":
			result = _dispatch_choice_group(entry, gesture, payload)
		"Tabs":
			result = _dispatch_tabs(entry, gesture, payload)
		"SelectionView":
			result = _dispatch_selection_view(entry, gesture, payload)
		"Stepper":
			result = _dispatch_stepper(entry, gesture, payload)
		"ScrollView":
			result = _dispatch_scroll_view(entry, gesture, payload)
		"TextField":
			result = _dispatch_text_field(entry, gesture, payload)
		"Button":
			result = _dispatch_button(entry, gesture)
		_:
			result = _reject(control_id, gesture, Errors.CONTROL_BINDING,
				"control type has no runtime action adapter")
	if result.get("ok", false):
		entry.state.last_error = null
		entry.state.last_gesture = gesture
		entry.state.last_result = {"accepted": true,
			"action": str(entry.state.last_action), "error": null}
		if entry.state.get("value") is String:
			entry.state.text = str(entry.state.value)
		interaction_log.append({"control_id": control_id, "gesture": gesture,
			"accepted": true, "semantic_state": entry.state.semantic_state,
			"value": entry.state.get("value")})
	return result


func qa_state() -> Dictionary:
	var factual_controls := {}
	for control_id in controls:
		factual_controls[control_id] = controls[control_id].state.duplicate(true)
	return {
		"window_id": str(window_spec.get("id", "")),
		"controls": factual_controls,
		"interaction_log": interaction_log.duplicate(true),
		"window_pending": _has_pending_stepper(),
		"window_state": window_state.duplicate(true),
	}


func reject_action(control_id: String, action: String,
		code: String = Errors.ACTION_ROUTING, detail: String = "") -> Dictionary:
	var message := detail if not detail.is_empty() \
		else "Window cannot route action: %s" % action
	return _reject(control_id, "", code, message)


func visual_asset(control_id: String) -> String:
	if not controls.has(control_id):
		return ""
	var entry: Dictionary = controls[control_id]
	var state: Dictionary = entry.state
	return str(entry.spec.state_set.get(state.semantic_state, {}).get(
		state.interaction_phase, ""))


func visual_surface_asset(control_id: String, surface_id: String) -> String:
	if not controls.has(control_id):
		return ""
	var entry: Dictionary = controls[control_id]
	if not entry.spec.get("surfaces", {}).has(surface_id):
		return ""
	var state: Dictionary = entry.state
	var asset_surface_id := surface_id
	if str(entry.spec.type) == "SelectionView":
		var mapped := str(state.get("item_values", {}).get(surface_id, surface_id))
		var home_values: Dictionary = entry.spec.value.get("item_values", {})
		var identity_surfaces: Dictionary = entry.spec.value.get("identity_surfaces", {})
		var mapped_surface := str(identity_surfaces.get(mapped, ""))
		if str(home_values.get(surface_id, "")) == mapped:
			asset_surface_id = surface_id
		elif not mapped_surface.is_empty() and entry.spec.surfaces.has(mapped_surface):
			asset_surface_id = mapped_surface
		elif entry.spec.surfaces.has(mapped):
			asset_surface_id = mapped
	var surface: Dictionary = entry.spec.surfaces[asset_surface_id]
	var semantic := str(state.semantic_state)
	if str(entry.spec.type) == "SelectionView":
		var drag: Dictionary = state.get("drag_state", {})
		var transfer: Dictionary = state.get("transfer_state", {})
		var mapped_identity := str(state.get("item_values", {}).get(surface_id, surface_id))
		if mapped_identity.is_empty() and surface.state_set.has("available"):
			semantic = "available"
		elif surface.state_set.has("transferring") \
				and bool(transfer.get("active", false)) \
				and str(transfer.get("item", "")) == surface_id:
			semantic = "transferring"
		elif bool(drag.get("active", false)) and str(drag.get("source", "")) == surface_id:
			semantic = "dragging"
		elif bool(drag.get("active", false)) and str(drag.get("target", "")) == surface_id:
			semantic = "drop_target"
		elif surface_id in state.get("selected_items", []):
			semantic = "modifier_selected"
		else:
			semantic = "selected" if state.get("semantic_state") == "selected" \
				and str(state.get("value", "")) == surface_id else "unselected"
	elif str(entry.spec.type) == "Stepper":
		semantic = str(state.semantic_state) if _is_status_stepper(entry) \
			else ("visible" if bool(state.get("arrows_visible", true)) else "hidden")
	var phase := str(state.interaction_phase) \
		if str(state.get("active_surface", "")) == surface_id else "idle"
	return str(surface.state_set.get(semantic, {}).get(phase, ""))


func _dispatch_toggle(entry: Dictionary, gesture: String) -> Dictionary:
	if gesture != "Activate":
		return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
			"Toggle accepts Activate")
	var states: Array = entry.spec.semantic_states
	if states.size() != 2:
		return _reject(entry.state.id, gesture, Errors.INVALID_STATE_SET,
			"Toggle requires exactly two semantic states")
	entry.state.semantic_state = states[1] if entry.state.semantic_state == states[0] else states[0]
	entry.state.interaction_phase = "idle"
	entry.state.last_action = "ToggleValue"
	return {"ok": true, "semantic_state": entry.state.semantic_state}


func _dispatch_range(entry: Dictionary, gesture: String, payload: Dictionary) -> Dictionary:
	var value_spec: Dictionary = entry.spec.value
	var minimum := float(value_spec.minimum)
	var maximum := float(value_spec.maximum)
	var next := float(entry.state.value)
	match gesture:
		"Drag":
			if not payload.has("normalized"):
				return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
					"Range Drag requires normalized pointer position")
			next = lerpf(minimum, maximum, clampf(float(payload.normalized), 0.0, 1.0))
		"Activate":
			var direction := float(payload.get("direction", 0.0))
			next += direction * float(value_spec.arrow_step)
		"Wheel":
			var wheel_direction := float(payload.get("direction", 0.0))
			next += wheel_direction * float(value_spec.wheel_step)
		_:
			return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
				"gesture is not bound to Range")
	entry.state.value = clampf(next, minimum, maximum)
	entry.state.last_action = "SetRange" if gesture == "Drag" else "StepRange"
	return {"ok": true, "value": entry.state.value}


func _dispatch_dropdown(entry: Dictionary, gesture: String, payload: Dictionary) -> Dictionary:
	if gesture == "KeyCommand":
		if str(payload.get("key", "")) != "Escape":
			return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
				"Dropdown KeyCommand must be Escape")
		entry.state.semantic_state = "closed"
		entry.state.interaction_phase = "idle"
		entry.state.last_action = "DismissDropdown"
		return {"ok": true, "value": entry.state.value,
			"semantic_state": entry.state.semantic_state}
	if gesture != "Activate":
		return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
			"Dropdown accepts Activate or KeyCommand")
	if payload.has("choice"):
		var choice: String = str(payload.choice)
		if choice not in entry.spec.value.choices:
			return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
				"choice is not declared: %s" % choice)
		entry.state.value = choice
		entry.state.semantic_state = "closed"
		entry.state.last_action = "SelectChoice"
	else:
		entry.state.semantic_state = "open" \
			if entry.state.semantic_state == "closed" else "closed"
		entry.state.last_action = "ToggleDropdown"
	entry.state.interaction_phase = "idle"
	return {"ok": true, "value": entry.state.value,
		"semantic_state": entry.state.semantic_state}


func _dispatch_choice_group(entry: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if str(window_state_adapter.get("type", "")) == "party" \
			and str(entry.state.id) == str(window_state_adapter.get("controls", {}).get("mode", "")):
		if gesture != "Activate" or not payload.has("choice"):
			return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
				"Party mode requires an activated choice")
		var party_result: Dictionary = PartyWindowState.select_mode(
			window_state_adapter, window_state, str(payload.choice),
			int(payload.get("expected_version", window_state.get("version", -1))))
		if not party_result.get("ok", false):
			return _reject(entry.state.id, gesture, party_result.error.code,
				party_result.error.detail)
		window_state = party_result.state
		_sync_party_controls()
		entry.state.interaction_phase = "idle"
		entry.state.last_action = "SelectPartyMode"
		return {"ok": true, "action": "SelectPartyMode", "value": entry.state.value,
			"window_state": window_state.duplicate(true)}
	var result: Dictionary = ChoiceGroup.select(entry.spec, entry.state, gesture, payload)
	if not result.ok:
		return _reject(entry.state.id, gesture, result.error.code, result.error.detail)
	entry.state.value = result.value
	entry.state.interaction_phase = "idle"
	entry.state.last_action = "SelectChoice"
	return {"ok": true, "value": entry.state.value,
		"semantic_state": entry.state.semantic_state}


func _dispatch_tabs(entry: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	var result: Dictionary = TabsModule.select(entry.spec, entry.state, gesture, payload)
	if not result.ok:
		return _reject(entry.state.id, gesture, result.error.code, result.error.detail)
	return result


func _dispatch_selection_view(entry: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if str(window_state_adapter.get("type", "")) == "party" \
			and str(entry.state.id) == str(window_state_adapter.get("controls", {}).get("members", "")):
		if gesture != "Activate":
			return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
				"Party members accept Activate")
		var party_result: Dictionary = PartyWindowState.select_member(
			window_state_adapter, window_state, str(payload.get("item", "")),
			int(payload.get("expected_version", window_state.get("version", -1))))
		if not party_result.get("ok", false):
			return _reject(entry.state.id, gesture, party_result.error.code,
				party_result.error.detail)
		window_state = party_result.state
		_sync_party_controls()
		entry.state.interaction_phase = "idle"
		entry.state.last_action = "SelectPartyMember"
		return {"ok": true, "action": "SelectPartyMember", "value": entry.state.value,
			"window_state": window_state.duplicate(true)}
	var result: Dictionary = SelectionViewModule.activate(entry.spec, entry.state,
		gesture, payload)
	if not result.ok:
		return _reject(entry.state.id, gesture, result.error.code, result.error.detail)
	var context_action := _selection_context_action(entry, gesture)
	if not context_action.is_empty():
		entry.state.last_action = context_action
		if context_action not in ["OpenSkillDetail", "OpenInventoryItem"]:
			entry.state.opened_item = ""
		result.action = context_action
	return result


func _selection_context_action(entry: Dictionary, gesture: String) -> String:
	for route in entry.spec.value.get("context_actions", []):
		if not route is Dictionary or str(route.get("gesture", "")) != gesture:
			continue
		var condition: Variant = route.get("when")
		if not condition is Dictionary:
			continue
		var context_id := str(condition.get("control_id", ""))
		if not controls.has(context_id):
			continue
		if controls[context_id].state.get("value") == condition.get("value"):
			return str(route.get("action", ""))
	return ""


func set_selection_drag_state(control_id: String, active: bool, source: String = "",
		target: String = "", motion_samples: int = 0) -> Dictionary:
	if not controls.has(control_id) or str(controls[control_id].spec.type) != "SelectionView":
		return _reject(control_id, "DragDrop", Errors.INVALID_CONTROL_SPEC,
			"drag state requires a SelectionView")
	var state: Dictionary = controls[control_id].state
	state.drag_state = {"active": active, "source": source, "target": target,
		"motion_samples": motion_samples}
	return {"ok": true, "drag_state": state.drag_state.duplicate(true)}


func set_selection_transfer_state(control_id: String, active: bool,
		item: String = "") -> Dictionary:
	if not controls.has(control_id) or str(controls[control_id].spec.type) != "SelectionView":
		return _reject(control_id, "ModifierDoubleActivate", Errors.INVALID_CONTROL_SPEC,
			"transfer state requires a SelectionView")
	var state: Dictionary = controls[control_id].state
	state.transfer_state = {"active": active, "item": item if active else ""}
	return {"ok": true, "transfer_state": state.transfer_state.duplicate(true)}


func filter_selection(control_id: String, query: String) -> Dictionary:
	if not controls.has(control_id) or str(controls[control_id].spec.type) != "SelectionView":
		return _reject(control_id, "KeyCommand", Errors.CONTROL_BINDING,
			"filter target must be a SelectionView")
	var entry: Dictionary = controls[control_id]
	var labels: Dictionary = entry.spec.value.get("collection_labels", {})
	var normalized := query.strip_edges().to_lower()
	entry.state.filter_text = query
	entry.state.filtered_items = entry.state.collection_items.filter(func(item):
		return normalized.is_empty() or normalized in str(labels.get(item, item)).to_lower())
	entry.state.scroll_offset = 0
	_refresh_selection_page(entry)
	return {"ok": true, "query": query, "result_count": entry.state.filtered_items.size()}


func sort_selection(control_id: String) -> Dictionary:
	if not controls.has(control_id) or str(controls[control_id].spec.type) != "SelectionView":
		return _reject(control_id, "Activate", Errors.CONTROL_BINDING,
			"sort target must be a SelectionView")
	var entry: Dictionary = controls[control_id]
	entry.state.sort_ascending = not bool(entry.state.sort_ascending)
	entry.state.collection_items.sort()
	if not entry.state.sort_ascending:
		entry.state.collection_items.reverse()
	filter_selection(control_id, str(entry.state.filter_text))
	return {"ok": true, "ascending": entry.state.sort_ascending}


func set_selection_scroll(control_id: String, offset: int) -> Dictionary:
	if not controls.has(control_id) or str(controls[control_id].spec.type) != "SelectionView":
		return _reject(control_id, "Wheel", Errors.CONTROL_BINDING,
			"scroll target must be a SelectionView")
	var entry: Dictionary = controls[control_id]
	entry.state.scroll_offset = maxi(offset, 0)
	_refresh_selection_page(entry)
	return {"ok": true, "offset": entry.state.scroll_offset}


func sync_scroll_bounds(scroll_control_id: String, selection_control_id: String) -> Dictionary:
	if not controls.has(scroll_control_id) or str(controls[scroll_control_id].spec.type) != "ScrollView" \
			or not controls.has(selection_control_id) \
			or str(controls[selection_control_id].spec.type) != "SelectionView":
		return _reject(scroll_control_id, "", Errors.CONTROL_BINDING,
			"scroll bounds require linked ScrollView and SelectionView controls")
	var scroll: Dictionary = controls[scroll_control_id]
	var selection: Dictionary = controls[selection_control_id]
	var columns := maxi(int(selection.spec.value.get("columns", 1)), 1)
	var visible_rows := maxi(int(selection.spec.value.get("visible_rows", 1)), 1)
	var result_count: int = selection.state.filtered_items.size()
	var total_rows: int = ceili(float(result_count) / float(columns))
	scroll.state.maximum = maxi(total_rows - visible_rows, 0)
	scroll.state.offset = clampi(int(scroll.state.offset), 0, int(scroll.state.maximum))
	scroll.state.value = scroll.state.offset
	scroll.state.semantic_state = "at_start" if scroll.state.offset == 0 else (
		"at_end" if scroll.state.offset == scroll.state.maximum else "between")
	selection.state.scroll_offset = scroll.state.offset
	_refresh_selection_page(selection)
	return {"ok": true, "maximum": scroll.state.maximum, "offset": scroll.state.offset}


func selection_collection(control_id: String) -> Dictionary:
	if not controls.has(control_id) or str(controls[control_id].spec.type) != "SelectionView":
		return {}
	var state: Dictionary = controls[control_id].state
	return {"window_id": str(window_spec.get("id", "")),
		"items": state.collection_items.duplicate(),
		"version": int(state.item_version), "capacity": int(state.capacity)}


func apply_selection_collection(control_id: String, collection: Dictionary) -> Dictionary:
	if not controls.has(control_id) or str(controls[control_id].spec.type) != "SelectionView":
		return _reject(control_id, "ModifierActivate", Errors.CONTROL_BINDING,
			"transaction target must be a SelectionView")
	var entry: Dictionary = controls[control_id]
	entry.state.collection_items = collection.get("items", []).duplicate()
	entry.state.item_version = int(collection.get("version", entry.state.item_version))
	filter_selection(control_id, str(entry.state.filter_text))
	return {"ok": true, "version": entry.state.item_version,
		"items": entry.state.collection_items.duplicate()}


func selection_slots(control_id: String) -> Dictionary:
	if not controls.has(control_id) or str(controls[control_id].spec.type) != "SelectionView":
		return {}
	var state: Dictionary = controls[control_id].state
	return {"window_id": str(window_spec.get("id", "")),
		"slots": state.item_values.duplicate(true),
		"version": int(state.item_version), "capacity": int(state.capacity)}


func apply_selection_slots(control_id: String, snapshot: Dictionary) -> Dictionary:
	if not controls.has(control_id) or str(controls[control_id].spec.type) != "SelectionView":
		return _reject(control_id, "DragDrop", Errors.CONTROL_BINDING,
			"equipment transaction target must be a SelectionView")
	var entry: Dictionary = controls[control_id]
	var slots: Variant = snapshot.get("slots")
	if not slots is Dictionary or slots.keys().any(func(slot):
		return slot not in entry.spec.value.items):
		return _reject(control_id, "DragDrop", Errors.TRANSACTION_REJECTED,
			"equipment transaction contains an undeclared slot")
	entry.state.item_values = slots.duplicate(true)
	entry.state.collection_items = entry.spec.value.items.map(func(slot):
		return str(slots.get(slot, ""))).filter(func(item): return not item.is_empty())
	entry.state.filtered_items = entry.state.collection_items.duplicate()
	entry.state.item_version = int(snapshot.get("version", entry.state.item_version))
	entry.state.selected_items = []
	return {"ok": true, "version": entry.state.item_version,
		"slots": entry.state.item_values.duplicate(true)}


func selected_logical_item(control_id: String, slot: String) -> String:
	if not controls.has(control_id):
		return ""
	return str(controls[control_id].state.get("item_values", {}).get(slot, ""))


func _refresh_selection_page(entry: Dictionary) -> void:
	var slots: Array = entry.spec.value.items
	var columns := maxi(int(entry.spec.value.get("columns", slots.size())), 1)
	var start := int(entry.state.scroll_offset) * columns
	var values := {}
	for index in slots.size():
		var source_index := start + index
		values[str(slots[index])] = str(entry.state.filtered_items[source_index]) \
			if source_index < entry.state.filtered_items.size() else ""
	entry.state.item_values = values


func _dispatch_stepper(entry: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	if _is_status_stepper(entry):
		var direction := 1 if gesture == "Activate" else -1 \
			if gesture == "ContextActivate" else 0
		if direction == 0:
			return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
				"Status Stepper accepts Activate or ContextActivate")
		var expected_version := int(payload.get("expected_version",
			window_state.get("version", -1)))
		var status_result: Dictionary = StatusWindowState.step(window_state_adapter,
			window_state, str(entry.state.id), direction, expected_version)
		if not status_result.get("ok", false):
			return _reject(entry.state.id, gesture, status_result.error.code,
				status_result.error.detail)
		window_state = status_result.state
		_sync_status_controls()
		entry.state.interaction_phase = "idle"
		entry.state.last_action = "StepStatusAttribute"
		return {"ok": true, "action": "StepStatusAttribute",
			"control_id": str(entry.state.id), "direction": direction,
			"window_state": window_state.duplicate(true)}
	var result: Dictionary = StepperModule.step(entry.spec, entry.state, gesture, payload)
	if not result.ok:
		return _reject(entry.state.id, gesture, result.error.code, result.error.detail)
	_set_all_stepper_arrows(not _has_pending_stepper())
	return result


func _dispatch_scroll_view(entry: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	var result: Dictionary = ScrollViewModule.interact(entry.spec, entry.state,
		gesture, payload)
	if not result.ok:
		return _reject(entry.state.id, gesture, result.error.code, result.error.detail)
	return result


func _dispatch_text_field(entry: Dictionary, gesture: String,
		payload: Dictionary) -> Dictionary:
	var result: Dictionary = TextFieldModule.edit(entry.spec, entry.state,
		gesture, payload)
	if not result.ok:
		return _reject(entry.state.id, gesture, result.error.code, result.error.detail)
	return result


func _dispatch_button(entry: Dictionary, gesture: String) -> Dictionary:
	if gesture != "Activate":
		return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
			"Button accepts Activate")
	if _is_party_action(entry):
		var action_id := str(entry.spec.get("value", {}).get("action_id", entry.state.id))
		var party_result: Dictionary = PartyWindowState.activate_action(
			window_state_adapter, window_state, action_id,
			int(window_state.get("version", -1)))
		if not party_result.get("ok", false):
			return _reject(entry.state.id, gesture, party_result.error.code,
				party_result.error.detail)
		window_state = party_result.state
		_sync_party_controls()
		entry.state.interaction_phase = "idle"
		entry.state.last_action = str(party_result.action)
		return {"ok": true, "action": str(party_result.action),
			"window_state": window_state.duplicate(true)}
	var action := ""
	for binding in entry.spec.actions:
		if binding.gesture == gesture:
			action = str(binding.action)
			break
	if action.is_empty():
		return _reject(entry.state.id, gesture, Errors.CONTROL_BINDING,
			"Button has no Activate Window Action")
	if action not in ["ToggleMinimized", "CloseWindow", "ToggleSkillView",
			"CommitSkillChanges", "CancelSkillChanges", "ToggleStorageView",
			"SortStorage", "FocusStorageSearch", "OpenWindow",
			]:
		return _reject(entry.state.id, gesture, Errors.ACTION_ROUTING,
			"Button action is not routed: %s" % action)
	if action == "CommitSkillChanges":
		_commit_steppers()
	elif action == "CancelSkillChanges":
		_cancel_steppers()
	entry.state.interaction_phase = "idle"
	entry.state.last_action = action
	return {"ok": true, "action": action,
		"target_window": str(entry.spec.get("value", {}).get("target_window", "")),
		"semantic_state": entry.state.semantic_state}


func _has_pending_stepper() -> bool:
	for control_id in controls:
		var entry: Dictionary = controls[control_id]
		if str(entry.spec.type) == "Stepper" and bool(
				entry.state.get("pending", false)):
			return true
	return false


func _set_all_stepper_arrows(visible: bool) -> void:
	for control_id in controls:
		var entry: Dictionary = controls[control_id]
		if str(entry.spec.type) == "Stepper" and not _is_status_stepper(entry):
			entry.state.arrows_visible = visible


func _commit_steppers() -> void:
	for control_id in controls:
		var entry: Dictionary = controls[control_id]
		if str(entry.spec.type) == "Stepper" and not _is_status_stepper(entry):
			entry.state.current = entry.state.target
			entry.state.pending = false
			entry.state.semantic_state = "ready"
			entry.state.text = StepperModule.format_value(
				entry.state.current, entry.state.target)
	_set_all_stepper_arrows(true)


func _cancel_steppers() -> void:
	for control_id in controls:
		var entry: Dictionary = controls[control_id]
		if str(entry.spec.type) == "Stepper" and not _is_status_stepper(entry):
			entry.state.target = entry.state.current
			entry.state.pending = false
			entry.state.semantic_state = "ready"
			entry.state.text = StepperModule.format_value(
				entry.state.current, entry.state.target)
	_set_all_stepper_arrows(true)


func _is_status_stepper(entry: Dictionary) -> bool:
	return str(window_state_adapter.get("type", "")) == "status" \
		and window_state_adapter.get("attributes", {}).has(str(entry.state.id))


func _is_party_action(entry: Dictionary) -> bool:
	return str(window_state_adapter.get("type", "")) == "party" \
		and str(entry.state.id) in window_state_adapter.get("controls", {}).get("actions", [])


func _sync_party_controls() -> void:
	var mappings: Dictionary = window_state_adapter.get("controls", {})
	var mode_id := str(mappings.get("mode", ""))
	if controls.has(mode_id):
		controls[mode_id].state.value = str(window_state.get("mode", "party"))
		controls[mode_id].state.text = controls[mode_id].state.value
	var members_id := str(mappings.get("members", ""))
	if controls.has(members_id):
		var member_state: Dictionary = controls[members_id].state
		var values := {}
		for item in controls[members_id].spec.value.items:
			values[str(item)] = str(item) \
				if str(item) in window_state.get("visible_members", []) else ""
		member_state.item_values = values
		member_state.value = str(window_state.get("selected_member", ""))
		member_state.text = member_state.value
		member_state.semantic_state = "selected" \
			if not member_state.value.is_empty() else "unselected"
		member_state.active_surface = member_state.value
	for action_id in mappings.get("actions", []):
		if not controls.has(str(action_id)):
			continue
		var available := bool(window_state.get("availability", {}).get(str(action_id), false))
		controls[str(action_id)].state.semantic_state = "available" if available else "disabled"


func _sync_status_controls() -> void:
	for control_id in window_state.get("attributes", {}):
		if not controls.has(control_id):
			continue
		var state: Dictionary = controls[control_id].state
		var attribute: Dictionary = window_state.attributes[control_id]
		state.current = attribute.base
		state.target = attribute.base
		state.text = str(attribute.base)
		state.pending = false
		state.arrows_visible = bool(window_state.availability[control_id])
		state.semantic_state = "available" if state.arrows_visible else "disabled"


func _reject(control_id: String, gesture: String, code: String, detail: String) -> Dictionary:
	var error := {"code": code, "detail": detail}
	if controls.has(control_id):
		controls[control_id].state.last_error = error
		controls[control_id].state.last_result = {
			"accepted": false, "action": "", "error": error}
	interaction_log.append({"control_id": control_id, "gesture": gesture,
		"accepted": false, "error": error})
	return {"ok": false, "error": error}
