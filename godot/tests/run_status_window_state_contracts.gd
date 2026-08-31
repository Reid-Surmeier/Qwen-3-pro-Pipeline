extends SceneTree
## Issue #131 frozen Window State Adapter contracts.

const StatusWindowState = preload("res://window_state/status_window_state.gd")

var results: Array[Dictionary] = []
var spec := {
	"type": "status",
	"initial_points": 4,
	"attributes": {
		"status.attribute.str": {"key": "Str", "base": 1, "bonus": 2},
		"status.attribute.agi": {"key": "Agi", "base": 1, "bonus": 2},
		"status.attribute.vit": {"key": "Vit", "base": 1, "bonus": 3},
		"status.attribute.int": {"key": "Int", "base": 92, "bonus": 10},
		"status.attribute.dex": {"key": "Dex", "base": 1, "bonus": 3},
		"status.attribute.luk": {"key": "Luk", "base": 1, "bonus": 5},
	},
	"derived": {
		"Atk": {"base": 63, "coefficients": {"Str": 1, "Dex": 1}},
		"Def": {"base": 20, "coefficients": {"Vit": 1}},
		"MatkMin": {"base": 298, "coefficients": {"Int": 2}},
		"MatkMax": {"base": 502, "coefficients": {"Int": 3}},
		"Mdef": {"base": 107, "coefficients": {"Int": 1}},
		"Hit": {"base": 64, "coefficients": {"Dex": 1}},
		"Flee": {"base": 64, "coefficients": {"Agi": 1}},
		"Critical": {"base": 3, "coefficients": {"Luk": 1}},
		"Aspd": {"base": 140, "coefficients": {"Agi": 1}},
	},
}


func _init() -> void:
	_contract_source_state_and_availability()
	_contract_accept_updates_every_fact_in_one_version()
	_contract_rapid_exhaustion_rejects_without_mutation()
	_contract_unaffordable_int_rejects_without_mutation()
	_contract_reverse_refunds_and_restores_derived()
	_contract_source_floor_rejects_without_mutation()
	_contract_stale_version_rejects_without_mutation()
	_contract_malformed_spec_fails_closed()
	_finish()


func _contract_source_state_and_availability() -> void:
	var result: Dictionary = StatusWindowState.initialize(spec)
	var state: Dictionary = result.get("state", {})
	_check("source-state-and-availability", result.get("ok", false)
		and state.version == 0 and state.points == 4
		and state.attributes["status.attribute.int"].base == 92
		and state.attributes["status.attribute.int"].cost == 11
		and not state.availability["status.attribute.int"]
		and state.availability["status.attribute.str"]
		and state.derived.Atk == 63 and state.derived.MatkMin == 298,
		str(result))


func _contract_accept_updates_every_fact_in_one_version() -> void:
	var initial: Dictionary = StatusWindowState.initialize(spec).state
	var result: Dictionary = StatusWindowState.step(spec, initial,
		"status.attribute.str", 1, 0)
	var state: Dictionary = result.get("state", {})
	_check("accepted-step-is-one-complete-state", result.get("ok", false)
		and result.action == "StepStatusAttribute" and state.version == 1
		and state.points == 2 and state.attributes["status.attribute.str"].base == 2
		and state.attributes["status.attribute.str"].cost == 2
		and state.derived.Atk == 64 and state.availability["status.attribute.str"]
		and initial.version == 0 and initial.points == 4
		and initial.attributes["status.attribute.str"].base == 1,
		str([initial, result]))


func _contract_rapid_exhaustion_rejects_without_mutation() -> void:
	var state: Dictionary = StatusWindowState.initialize(spec).state
	state = StatusWindowState.step(spec, state, "status.attribute.str", 1, 0).state
	state = StatusWindowState.step(spec, state, "status.attribute.str", 1, 1).state
	var before := JSON.stringify(state)
	var rejected: Dictionary = StatusWindowState.step(spec, state,
		"status.attribute.str", 1, 2)
	_check("rapid-exhaustion-rejects-atomically", not rejected.get("ok", true)
		and rejected.error.code == "TransactionRejectedError"
		and JSON.stringify(rejected.state) == before and JSON.stringify(state) == before
		and state.points == 0 and state.version == 2
		and state.availability.values().all(func(value): return not value), str(rejected))


func _contract_unaffordable_int_rejects_without_mutation() -> void:
	var state: Dictionary = StatusWindowState.initialize(spec).state
	var before := JSON.stringify(state)
	var rejected: Dictionary = StatusWindowState.step(spec, state,
		"status.attribute.int", 1, 0)
	_check("unaffordable-int-rejects-atomically", not rejected.get("ok", true)
		and rejected.error.code == "TransactionRejectedError"
		and JSON.stringify(rejected.state) == before and JSON.stringify(state) == before,
		str(rejected))


func _contract_reverse_refunds_and_restores_derived() -> void:
	var source: Dictionary = StatusWindowState.initialize(spec).state
	var stepped: Dictionary = StatusWindowState.step(spec, source,
		"status.attribute.agi", 1, 0).state
	var reversed: Dictionary = StatusWindowState.step(spec, stepped,
		"status.attribute.agi", -1, 1)
	_check("reverse-refunds-and-restores-derived", reversed.get("ok", false)
		and reversed.state.version == 2 and reversed.state.points == 4
		and reversed.state.attributes["status.attribute.agi"].base == 1
		and reversed.state.derived.Flee == 64 and reversed.state.derived.Aspd == 140
		and stepped.derived.Flee == 65 and stepped.derived.Aspd == 141,
		str([stepped, reversed]))


func _contract_source_floor_rejects_without_mutation() -> void:
	var state: Dictionary = StatusWindowState.initialize(spec).state
	var before := JSON.stringify(state)
	var rejected: Dictionary = StatusWindowState.step(spec, state,
		"status.attribute.agi", -1, 0)
	_check("source-floor-rejects-atomically", not rejected.get("ok", true)
		and rejected.error.code == "TransactionRejectedError"
		and JSON.stringify(rejected.state) == before, str(rejected))


func _contract_stale_version_rejects_without_mutation() -> void:
	var state: Dictionary = StatusWindowState.initialize(spec).state
	var before := JSON.stringify(state)
	var rejected: Dictionary = StatusWindowState.step(spec, state,
		"status.attribute.str", 1, 9)
	_check("stale-version-rejects-atomically", not rejected.get("ok", true)
		and rejected.error.code == "GestureConflictError"
		and JSON.stringify(rejected.state) == before, str(rejected))


func _contract_malformed_spec_fails_closed() -> void:
	var malformed := spec.duplicate(true)
	malformed.initial_points = -1
	malformed.attributes["status.attribute.int"].base = 0
	var result: Dictionary = StatusWindowState.initialize(malformed)
	_check("malformed-adapter-fails-closed", not result.get("ok", true)
		and result.error.code == "InvalidControlSpec", str(result))


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "status-window-state-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/status-window-state-contracts.json",
		FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("STATUS WINDOW STATE %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
