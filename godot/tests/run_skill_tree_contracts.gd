extends SceneTree
## Issue #126 public runtime contracts. These tests freeze SelectionView,
## Stepper, ContextActivate, and the Window-level pending transaction before
## their production adapters exist.

const ControlRuntime = preload("res://control_library/control_runtime.gd")

var results: Array[Dictionary] = []
var runtime


func _init() -> void:
	runtime = ControlRuntime.new()
	runtime.configure(_fixture())
	_contract_context_activate_is_distinct()
	_contract_declared_actions_drive_runtime()
	_contract_stepper_bounds_reject_without_mutation()
	_contract_step_hides_every_arrow_in_one_frame()
	_contract_commit_and_cancel_are_window_transactions()
	_contract_qa_state_covers_every_stable_id()
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _fixture() -> Dictionary:
	var variants := {"idle": "fixture", "hover": "fixture", "pressed": "fixture"}
	return {
		"id": "skill_tree",
		"controls": [
			{
				"id": "skill_tree.skills", "type": "SelectionView",
				"interaction_phases": ["idle", "hover", "pressed"],
				"semantic_states": ["unselected", "selected"],
				"initial_semantic_state": "unselected", "state_set": {
					"unselected": variants, "selected": variants},
				"value": {"items": ["heal", "holy-light"], "initial": "heal",
					"details": {"heal": "heal\n7 / 7", "holy-light": "holy-light\n5 / 5"}},
				"gestures": ["Activate", "ContextActivate"],
				"actions": [
					{"gesture": "Activate", "action": "SelectSkill"},
					{"gesture": "ContextActivate", "action": "OpenSkillDetail"},
				],
			},
			_stepper("skill_tree.stepper.heal", 7, 7, 10),
			_stepper("skill_tree.stepper.holy-light", 5, 5, 10),
			_button("skill_tree.use", "CommitSkillChanges"),
			_button("skill_tree.cancel", "CancelSkillChanges"),
		],
	}


func _stepper(id: String, current: int, target: int, maximum: int) -> Dictionary:
	var variants := {"idle": "fixture", "hover": "fixture", "pressed": "fixture"}
	return {
		"id": id, "type": "Stepper", "interaction_phases": ["idle", "hover", "pressed"],
		"semantic_states": ["ready", "pending", "disabled"],
		"initial_semantic_state": "ready", "state_set": {
			"ready": variants, "pending": variants, "disabled": {"idle": "fixture"}},
		"value": {"minimum": 0, "maximum": maximum, "current": current,
			"target": target, "step": 1},
		"gestures": ["Activate"],
		"actions": [{"gesture": "Activate", "action": "StepSkill"}],
	}


func _button(id: String, action: String) -> Dictionary:
	var variants := {"idle": "fixture", "hover": "fixture", "pressed": "fixture"}
	return {
		"id": id, "type": "Button", "interaction_phases": ["idle", "hover", "pressed"],
		"semantic_states": ["ready"], "initial_semantic_state": "ready",
		"state_set": {"ready": variants}, "gestures": ["Activate"],
		"actions": [{"gesture": "Activate", "action": action}],
	}


func _contract_context_activate_is_distinct() -> void:
	var selected: Dictionary = runtime.dispatch("skill_tree.skills", "Activate",
		{"item": "holy-light", "button": "left"})
	var detailed: Dictionary = runtime.dispatch("skill_tree.skills", "ContextActivate",
		{"item": "heal", "button": "right"})
	var state: Dictionary = runtime.qa_state().controls["skill_tree.skills"]
	_check("context-activate-distinct", selected.ok and detailed.ok
		and selected.action == "SelectSkill" and detailed.action == "OpenSkillDetail"
		and state.value == "heal" and state.last_gesture == "ContextActivate",
		str([selected, detailed, state]))


func _contract_declared_actions_drive_runtime() -> void:
	var remapped := ControlRuntime.new()
	var fixture := _fixture()
	fixture.controls[0].actions = [
		{"gesture": "Activate", "action": "OpenSkillDetail"},
		{"gesture": "ContextActivate", "action": "SelectSkill"},
	]
	remapped.configure(fixture)
	var activated: Dictionary = remapped.dispatch("skill_tree.skills", "Activate",
		{"item": "holy-light"})
	var contextual: Dictionary = remapped.dispatch("skill_tree.skills", "ContextActivate",
		{"item": "heal"})
	_check("declared-selection-actions-drive-runtime", activated.ok and contextual.ok
		and activated.action == "OpenSkillDetail" and contextual.action == "SelectSkill",
		str([activated, contextual]))


func _contract_stepper_bounds_reject_without_mutation() -> void:
	var bounded := ControlRuntime.new()
	var bounded_fixture := _fixture()
	bounded_fixture.controls[2].value.current = 10
	bounded_fixture.controls[2].value.target = 10
	bounded_fixture.controls[1].value.current = 0
	bounded_fixture.controls[1].value.target = 0
	bounded.configure(bounded_fixture)
	var before_max: Dictionary = bounded.qa_state().controls["skill_tree.stepper.holy-light"]
	var rejected_max: Dictionary = bounded.dispatch("skill_tree.stepper.holy-light", "Activate",
		{"direction": 1})
	var after_max: Dictionary = bounded.qa_state().controls["skill_tree.stepper.holy-light"]
	var rejected_min: Dictionary = bounded.dispatch("skill_tree.stepper.heal", "Activate",
		{"direction": -1})
	var after_min: Dictionary = bounded.qa_state().controls["skill_tree.stepper.heal"]
	_check("stepper-bounds-reject-without-mutation", not rejected_max.ok and not rejected_min.ok
		and rejected_max.error.code == "TransactionRejectedError"
		and rejected_min.error.code == "TransactionRejectedError"
		and after_max.target == 10 and not after_max.pending
		and after_min.target == 0 and not after_min.pending
		and before_max.last_action == after_max.last_action,
		str([rejected_max, rejected_min, after_max, after_min]))


func _contract_step_hides_every_arrow_in_one_frame() -> void:
	var stepped: Dictionary = runtime.dispatch("skill_tree.stepper.heal", "Activate",
		{"direction": 1})
	var state: Dictionary = runtime.qa_state()
	_check("stepper-current-target-format", stepped.ok and stepped.current == 7
		and stepped.target == 8 and state.controls["skill_tree.stepper.heal"].text == "7 / 8",
		str(stepped))
	_check("stepper-window-wide-arrow-hide", state.window_pending
		and not state.controls["skill_tree.stepper.heal"].arrows_visible
		and not state.controls["skill_tree.stepper.holy-light"].arrows_visible,
		str(state))


func _contract_commit_and_cancel_are_window_transactions() -> void:
	var committed: Dictionary = runtime.dispatch("skill_tree.use", "Activate", {})
	var after_commit: Dictionary = runtime.qa_state()
	runtime.dispatch("skill_tree.stepper.heal", "Activate", {"direction": 1})
	var cancelled: Dictionary = runtime.dispatch("skill_tree.cancel", "Activate", {})
	var after_cancel: Dictionary = runtime.qa_state()
	_check("stepper-commit", committed.ok and not after_commit.window_pending
		and after_commit.controls["skill_tree.stepper.heal"].current == 8
		and after_commit.controls["skill_tree.stepper.heal"].target == 8
		and after_commit.controls["skill_tree.stepper.holy-light"].arrows_visible,
		str(after_commit))
	_check("stepper-cancel", cancelled.ok and not after_cancel.window_pending
		and after_cancel.controls["skill_tree.stepper.heal"].current == 8
		and after_cancel.controls["skill_tree.stepper.heal"].target == 8,
		str(after_cancel))


func _contract_qa_state_covers_every_stable_id() -> void:
	var state: Dictionary = runtime.qa_state()
	_check("skill-tree-qa-coverage", state.controls.size() == 5
		and state.controls.keys().all(func(id): return str(id).begins_with("skill_tree.")),
		str(state.controls.keys()))


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	var report := {"suite": "skill-tree-runtime", "total": results.size(),
		"failed": failed.size(), "results": results}
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/skill-tree-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("SKILL TREE %d/%d passed" % [results.size() - failed.size(), results.size()])
