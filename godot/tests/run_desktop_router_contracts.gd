extends SceneTree
## Issue #128 frozen cross-Window transaction contracts.

const Router = preload("res://desktop_router/desktop_action_router.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	var inventory := {"window_id": "inventory", "items": ["apple", "sword"],
		"version": 4, "capacity": 3}
	var storage := {"window_id": "storage", "items": ["potion"],
		"version": 9, "capacity": 300}
	var committed := Router.transfer(inventory, storage, "apple", 4, 9, ["ctrl"])
	_check("commit-updates-both-sides", committed.ok
		and committed.source.items == ["sword"]
		and committed.target.items == ["potion", "apple"]
		and committed.source.version == 5 and committed.target.version == 10,
		str(committed))
	var source_before := inventory.duplicate(true)
	var target_before := storage.duplicate(true)
	var conflict := Router.transfer(inventory, storage, "apple", 3, 9, ["ctrl"])
	_check("version-rejection-is-atomic", not conflict.ok
		and conflict.error.code == "GestureConflictError"
		and inventory == source_before and storage == target_before,
		str([conflict, inventory, storage]))
	var modifier := Router.transfer(inventory, storage, "apple", 4, 9, ["shift"])
	_check("modifier-rejection-is-atomic", not modifier.ok
		and modifier.error.code == "InvalidModifierError"
		and inventory == source_before and storage == target_before, str(modifier))
	var full := {"window_id": "storage", "items": ["potion"],
		"version": 9, "capacity": 1}
	var full_before := full.duplicate(true)
	var rejected := Router.transfer(inventory, full, "apple", 4, 9, ["ctrl"])
	_check("capacity-rejection-is-atomic", not rejected.ok
		and rejected.error.code == "TransactionRejectedError"
		and inventory == source_before and full == full_before, str(rejected))
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "desktop-router", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/desktop-router-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("DESKTOP ROUTER %d/%d passed" % [results.size() - failed.size(), results.size()])
