extends SceneTree
## Issue #135 pure Chat Room semantic contracts.

const ChatRoomWindowState = preload("res://window_state/chat_room_window_state.gd")

var results: Array[Dictionary] = []


func _init() -> void:
	call_deferred("_run")


func _run() -> void:
	var spec := {
		"controls": {"input": "chat_room.input", "scroll": "chat_room.scroll"},
		"initial_lines": [
			{"kind": "chat", "text": "Sebas*：レイドリック終わったー"},
			{"kind": "chat", "text": "SakumaRiri：おつかれさま〜"},
			{"kind": "chat", "text": "ANRI：もう1周いきますか？"},
			{"kind": "chat", "text": "Show_A：いきましょう！"},
			{"kind": "system", "text": "経験値が 10800 上がりました。"},
		],
		"row_count_cycle": [5, 7, 3],
	}
	var initialized := ChatRoomWindowState.initialize(spec)
	_check("source-state", initialized.ok and initialized.state.version == 0
		and initialized.state.draft == "" and initialized.state.lines.size() == 5
		and initialized.state.visible_row_count == 5
		and initialized.state.pending_delivery == null, str(initialized))

	var edited := ChatRoomWindowState.edit_draft(spec, initialized.state,
		"テスト送信", 0)
	_check("draft-is-atomic", edited.ok and edited.state.version == 1
		and edited.state.draft == "テスト送信" and edited.state.lines.size() == 5,
		str(edited))
	var accepted := ChatRoomWindowState.submit(spec, edited.state, "party", 1)
	_check("submit-clears-before-echo", accepted.ok and accepted.state.version == 2
		and accepted.state.draft == "" and accepted.state.lines.size() == 5
		and accepted.state.pending_delivery.frames_remaining == 3
		and accepted.state.pending_delivery.scope == "party"
		and accepted.state.pending_delivery.text == "テスト送信", str(accepted))

	var frame_one := ChatRoomWindowState.advance_frame(spec, accepted.state)
	var frame_two := ChatRoomWindowState.advance_frame(spec, frame_one.state)
	var frame_three := ChatRoomWindowState.advance_frame(spec, frame_two.state)
	_check("echo-is-exactly-third-frame", frame_one.state.lines.size() == 5
		and frame_one.state.pending_delivery.frames_remaining == 2
		and frame_two.state.lines.size() == 5
		and frame_two.state.pending_delivery.frames_remaining == 1
		and frame_three.state.lines.size() == 6
		and frame_three.state.lines[-1].text == "テスト送信"
		and frame_three.state.lines[-1].scope == "party"
		and frame_three.state.pending_delivery == null
		and frame_three.scroll_to_end_control_id == "chat_room.scroll", str(frame_three))
	var settled := ChatRoomWindowState.advance_frame(spec, frame_three.state)
	_check("echo-auto-scroll-request-is-one-shot", settled.ok and not settled.changed
		and not settled.has("scroll_to_end_control_id"), str(settled))

	var resized := ChatRoomWindowState.change_rows(spec, frame_three.state,
		frame_three.state.version)
	_check("f10-cycles-declared-row-count", resized.ok
		and resized.state.visible_row_count == 7, str(resized))
	var stale_before := JSON.stringify(resized.state)
	var stale := ChatRoomWindowState.submit(spec, resized.state, "screen", 0)
	_check("stale-submit-preserves-state", not stale.ok
		and stale.error.code == "GestureConflictError"
		and JSON.stringify(resized.state) == stale_before, str(stale))

	var empty := ChatRoomWindowState.submit(spec, initialized.state, "screen", 0)
	_check("empty-submit-rejected", not empty.ok
		and empty.error.code == "TransactionRejectedError", str(empty))
	_finish()


func _check(name: String, passed: bool, detail: String) -> void:
	results.append({"name": name, "passed": passed, "detail": detail})


func _finish() -> void:
	var failed := results.filter(func(result): return not result.passed)
	DirAccess.make_dir_recursive_absolute("res://qa/out")
	var report := {"suite": "chat-room-state-contracts", "total": results.size(),
		"failed": failed.size(), "results": results}
	var file := FileAccess.open("res://qa/out/chat-room-state-contracts.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	file.close()
	print("CHAT ROOM STATE %d/%d passed" % [results.size() - failed.size(), results.size()])
	quit(1 if not failed.is_empty() else 0)
