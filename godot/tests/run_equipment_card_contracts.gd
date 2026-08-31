extends SceneTree
## Issue #129 manifest, visual-authority, and unavailable-scroll contracts.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ScrollViewModule = preload("res://control_library/scroll_view.gd")
const DesktopActionRouter = preload("res://desktop_router/desktop_action_router.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	var loaded: Dictionary = ControlSpec.load_and_validate(
		"res://data/image-79-control-spec.json")
	_check("manifest-valid", loaded.errors.is_empty(), str(loaded.errors))
	var matches: Array = loaded.manifest.get("windows", []).filter(func(window):
		return window.id == "equipment_card")
	_check("equipment-card-declared", matches.size() == 1, str(matches.size()))
	if matches.size() == 1:
		var card: Dictionary = matches.front()
		var controls := {}
		for control in card.controls:
			controls[str(control.id)] = control
		_check("source-geometry", int(card.geometry.x) == 1108
			and int(card.geometry.y) == 0 and int(card.geometry.width) == 424
			and int(card.geometry.height) == 290, str(card.geometry))
		_check("source-attested-detail", card.detail.id == "mistress-card"
			and card.detail.source_attested == true
			and card.detail.continuation_available == false, str(card.detail))
		_check("shared-controls", controls.size() == 3
			and controls["equipment_card.scroll"].type == "ScrollView",
			str(controls.keys()))
		var scroll: Dictionary = controls["equipment_card.scroll"]
		_check("unattested-continuation-fails-closed",
			scroll.value.available == false and not str(scroll.value.unavailable_reason).is_empty(),
			str(scroll.value))
		var state := {"minimum": 0, "maximum": 0, "offset": 0, "value": 0,
			"semantic_state": "at_start", "interaction_phase": "idle"}
		var before := state.duplicate(true)
		var rejected: Dictionary = ScrollViewModule.interact(scroll, state, "Wheel",
			{"direction": 1})
		_check("wheel-rejected-with-visual-authority-error",
			rejected.get("ok") == false
			and rejected.error.code == "VisualAuthorityError" and state == before,
			str(rejected))
		var opened: Dictionary = DesktopActionRouter.open_detail(card.id, card.detail)
		_check("source-detail-routes-open", opened.get("ok") == true
			and opened.detail_item == "mistress-card" and opened.visible == true
			and opened.continuation_available == false, str(opened))
		var unavailable: Dictionary = card.detail.duplicate(true)
		unavailable.source_attested = false
		var refused: Dictionary = DesktopActionRouter.open_detail(card.id, unavailable)
		_check("unattested-detail-fails-closed", refused.get("ok") == false
			and refused.error.code == "VisualAuthorityError", str(refused))
		var closed: Dictionary = DesktopActionRouter.close_detail(card.id, card.detail.id)
		_check("source-detail-routes-close", closed.get("ok") == true
			and closed.visible == false, str(closed))
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/equipment-card-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"suite": "equipment-card", "total": results.size(),
		"failed": failed.size(), "results": results}, "  "))
	file.close()
	print("EQUIPMENT CARD %d/%d passed" % [results.size() - failed.size(), results.size()])
