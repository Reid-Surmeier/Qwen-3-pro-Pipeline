extends SceneTree
## Issue #128 semantic Storage contracts through the public runtime seam.

const ControlSpec = preload("res://control_library/control_spec.gd")
const ControlRuntime = preload("res://control_library/control_runtime.gd")

var results: Array[Dictionary] = []
var runtime: ControlRuntime


func _init() -> void:
	var loaded: Dictionary = ControlSpec.load_and_validate(
		"res://data/image-79-control-spec.json")
	var storage: Dictionary = loaded.manifest.windows.filter(func(window):
		return window.id == "storage").front()
	runtime = ControlRuntime.new()
	runtime.configure(storage)
	var category := runtime.dispatch("storage.categories", "Activate",
		{"choice": "equipment"})
	_check("category-selects", category.ok and category.value == "equipment", str(category))
	var selected := runtime.dispatch("storage.items", "Activate", {"item": "r0c2"})
	var modifier := runtime.dispatch("storage.items", "ModifierActivate",
		{"item": "r0c2", "modifiers": ["ctrl"]})
	_check("selection-and-modifier", selected.ok and modifier.ok
		and runtime.qa_state().controls["storage.items"].selected_items == ["r0c2"],
		str(runtime.qa_state().controls["storage.items"]))
	var wheel := runtime.dispatch("storage.scroll", "Wheel", {"direction": 120})
	runtime.set_selection_scroll("storage.items", wheel.offset)
	_check("wheel-pages-three-rows", wheel.ok and wheel.offset == 3
		and runtime.qa_state().controls["storage.items"].scroll_offset == 3,
		str([wheel, runtime.qa_state().controls["storage.items"]]))
	var search := runtime.dispatch("storage.search", "KeyCommand", {"text": "Potion 70"})
	var filtered := runtime.filter_selection("storage.items", search.value)
	runtime.sync_scroll_bounds("storage.scroll", "storage.items")
	_check("text-drives-filter-and-reset", search.ok and filtered.result_count == 1
		and runtime.qa_state().controls["storage.search"].text == "Potion 70"
		and runtime.qa_state().controls["storage.scroll"].offset == 0
		and runtime.qa_state().controls["storage.scroll"].maximum == 0,
		str([search, filtered, runtime.qa_state()]))
	var sorted := runtime.sort_selection("storage.items")
	_check("sort-reverses-order", sorted.ok and not sorted.ascending, str(sorted))
	_write_report()
	quit(1 if results.any(func(result): return not result.passed) else 0)


func _check(name: String, passed: bool, detail: String = "") -> void:
	results.append({"test": name, "passed": passed, "detail": detail})


func _write_report() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var file := FileAccess.open("res://qa/out/storage-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify({"suite": "storage", "total": results.size(),
		"failed": failed.size(), "results": results}, "  "))
	file.close()
	print("STORAGE %d/%d passed" % [results.size() - failed.size(), results.size()])
