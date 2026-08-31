extends SceneTree
## Issue #130 red-first contract: Equipment Items owns stable slots and the
## Desktop Action Router commits Inventory <-> Equipment swaps atomically.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlRuntime = preload("res://control_library/control_runtime.gd")
const Router = preload("res://desktop_router/desktop_action_router.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	_manifest_contract()
	_router_contracts()
	_runtime_contract()
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "equipment-items-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/equipment-items-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("EQUIPMENT ITEMS %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)


func _manifest_contract() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var windows: Array = loaded.get("manifest", {}).get("windows", [])
	var matches := windows.filter(func(window): return window.get("id") == "equipment_items")
	_check("manifest-source-geometry", loaded.errors.is_empty() and matches.size() == 1
		and int(matches[0].geometry.x) == 0
		and int(matches[0].geometry.y) == 423
		and int(matches[0].geometry.width) == 484
		and int(matches[0].geometry.height) == 271,
		str([loaded.errors, matches]))
	if matches.is_empty():
		return
	var slots: Dictionary = matches[0].controls.filter(func(control):
		return control.get("id") == "equipment_items.slots")[0]
	_check("nine-manifest-owned-slots", slots.surfaces.size() == 9
		and slots.value.items.size() == 9
		and slots.gestures == ["Activate", "DoubleActivate", "DragDrop"], str(slots))


func _router_contracts() -> void:
	var inventory := {"window_id": "inventory", "version": 3,
		"slots": {"r0c0": "inventory-a", "r0c1": ""}, "capacity": 100}
	var equipment := {"window_id": "equipment_items", "version": 7,
		"slots": {"head": "crown", "robe": ""}, "capacity": 9}
	var before_inventory := inventory.duplicate(true)
	var before_equipment := equipment.duplicate(true)
	var equip := Router.equipment_transaction(inventory, equipment, "equip",
		"r0c0", "robe", 3, 7)
	_check("equip-two-sided-commit", equip.get("ok", false)
		and equip.inventory.slots.r0c0 == ""
		and equip.equipment.slots.robe == "inventory-a"
		and equip.inventory.version == 4 and equip.equipment.version == 8
		and inventory == before_inventory and equipment == before_equipment, str(equip))
	var displaced := Router.equipment_transaction(inventory, equipment, "equip",
		"r0c0", "head", 3, 7)
	_check("equip-displacement-is-atomic", displaced.get("ok", false)
		and displaced.inventory.slots.r0c0 == "crown"
		and displaced.equipment.slots.head == "inventory-a", str(displaced))
	var unequip := Router.equipment_transaction(inventory, equipment, "unequip",
		"r0c1", "head", 3, 7)
	_check("unequip-two-sided-commit", unequip.get("ok", false)
		and unequip.inventory.slots.r0c1 == "crown"
		and unequip.equipment.slots.head == "", str(unequip))
	for invalid in [
		Router.equipment_transaction(inventory, equipment, "equip", "missing", "head", 3, 7),
		Router.equipment_transaction(inventory, equipment, "unequip", "r0c0", "missing", 3, 7),
		Router.equipment_transaction(inventory, equipment, "equip", "r0c0", "head", 2, 7),
	]:
		_check("rejection-is-named-and-preserves-input", not invalid.get("ok", false)
			and invalid.error.code in ["TransactionRejectedError", "GestureConflictError"]
			and inventory == before_inventory and equipment == before_equipment, str(invalid))


func _runtime_contract() -> void:
	var loaded := ControlSpec.load_and_validate("res://data/image-79-control-spec.json")
	var matches: Array = loaded.get("manifest", {}).get("windows", []).filter(func(window):
		return window.get("id") == "equipment_items")
	if matches.is_empty():
		_check("runtime-slot-actions", false, "equipment_items manifest absent")
		return
	var runtime := ControlRuntime.new()
	runtime.configure(matches[0])
	var selected := runtime.dispatch("equipment_items.slots", "Activate", {"item": "head"})
	var opened := runtime.dispatch("equipment_items.slots", "DoubleActivate", {"item": "head"})
	_check("runtime-slot-actions", selected.get("action") == "SelectEquipmentSlot"
		and opened.get("action") == "UnequipEquipmentItem"
		and runtime.qa_state().controls["equipment_items.slots"].value == "head",
		str([selected, opened]))


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})
