import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from qwen_ui_pipeline.play_log import evaluate_play_log


class PlayLogVerdictTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.before = self._frame("before.png", b"before")
        self.mid = self._frame("mid.png", b"mid")
        self.after = self._frame("after.png", b"after")
        self.invariant_before = self._frame("invariant-before.png", b"stable")
        self.invariant_after = self._frame("invariant-after.png", b"stable")

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _frame(self, name: str, content: bytes) -> dict[str, str]:
        path = self.root / name
        path.write_bytes(content)
        return {"path": name, "sha256": hashlib.sha256(content).hexdigest()}

    def _valid_log(self) -> dict:
        return {
            "schema_version": "image79-play-log-v1",
            "candidate": {
                "issue": 125,
                "commit_sha": "a" * 40,
                "window_id": "options",
            },
            "source_reference_sha256": "b" * 64,
            "required_controls": ["options.bgm", "options.skin"],
            "required_actions": [
                {"control_id": "options.bgm", "gesture": "Drag", "window_action": "SetRange"},
                {"control_id": "options.skin", "gesture": "Activate", "window_action": "ToggleDropdown"},
            ],
            "console_errors": [],
            "invariant_frames": {
                "before": self.invariant_before,
                "after": self.invariant_after,
            },
            "actions": [
                {
                    "control_id": "options.bgm",
                    "gesture": "Drag",
                    "window_action": "SetRange",
                    "expected": "continuous and clamped",
                    "observed": "31 monotonic samples reached both endpoints",
                    "responsive": True,
                    "matches_expected": True,
                    "assertions": {
                        "continuous": True,
                        "monotonic": True,
                        "endpoint_clamped": True,
                        "reversible": True,
                    },
                    "motion_samples": list(range(31)),
                    "frames": {
                        "before": self.before,
                        "mid": self.mid,
                        "after": self.after,
                    },
                },
                {
                    "control_id": "options.skin",
                    "gesture": "Activate",
                    "window_action": "ToggleDropdown",
                    "expected": "open themed list",
                    "observed": "list opened",
                    "responsive": True,
                    "matches_expected": True,
                    "assertions": {"opened": True},
                    "frames": {"before": self.before, "after": self.after},
                },
            ],
        }

    def _manifest(self) -> dict:
        log = self._valid_log()
        controls = []
        for control_id in log["required_controls"]:
            controls.append({
                "id": control_id,
                "actions": [
                    {"gesture": action["gesture"], "action": action["window_action"]}
                    for action in log["required_actions"]
                    if action["control_id"] == control_id
                ],
            })
        return {"reference": {"sha256": "b" * 64},
                "windows": [{"id": "options", "controls": controls}]}

    def test_complete_hash_locked_log_passes(self) -> None:
        verdict = evaluate_play_log(self._valid_log(), self.root, self._manifest())
        self.assertEqual("PASS", verdict["verdict"])
        self.assertEqual(5, verdict["frames_verified"])

    def test_unexercised_control_is_incomplete(self) -> None:
        log = self._valid_log()
        log["actions"] = log["actions"][:1]
        verdict = evaluate_play_log(log, self.root, self._manifest())
        self.assertEqual("INCOMPLETE", verdict["verdict"])
        self.assertEqual(["options.skin"], verdict["unexercised"])

    def test_unexercised_manifest_action_is_incomplete(self) -> None:
        log = self._valid_log()
        log["required_actions"].append(
            {"control_id": "options.bgm", "gesture": "Wheel", "window_action": "StepRange"}
        )
        manifest = self._manifest()
        manifest["windows"][0]["controls"][0]["actions"].append(
            {"gesture": "Wheel", "action": "StepRange"}
        )
        verdict = evaluate_play_log(log, self.root, manifest)
        self.assertEqual("INCOMPLETE", verdict["verdict"])
        self.assertEqual(
            ["options.bgm:Wheel:StepRange"], verdict["unexercised_actions"]
        )

    def test_false_action_claim_fails(self) -> None:
        log = self._valid_log()
        log["actions"][1]["matches_expected"] = False
        verdict = evaluate_play_log(log, self.root, self._manifest())
        self.assertEqual("FAIL", verdict["verdict"])

    def test_console_error_fails(self) -> None:
        log = self._valid_log()
        log["console_errors"] = ["Invalid call"]
        verdict = evaluate_play_log(log, self.root, self._manifest())
        self.assertEqual("FAIL", verdict["verdict"])

    def test_missing_or_changed_frame_is_invalid(self) -> None:
        missing = self._valid_log()
        missing["actions"][1]["frames"]["after"]["path"] = "absent.png"
        self.assertEqual("INVALID", evaluate_play_log(missing, self.root, self._manifest())["verdict"])

        changed = self._valid_log()
        (self.root / "after.png").write_bytes(b"changed")
        self.assertEqual("INVALID", evaluate_play_log(changed, self.root, self._manifest())["verdict"])

    def test_drag_requires_mid_frame_and_thirty_motion_samples(self) -> None:
        log = self._valid_log()
        del log["actions"][0]["frames"]["mid"]
        log["actions"][0]["motion_samples"] = list(range(29))
        verdict = evaluate_play_log(log, self.root, self._manifest())
        self.assertEqual("INVALID", verdict["verdict"])
        self.assertTrue(any("30 motion samples" in problem for problem in verdict["problems"]))

    def test_malformed_root_is_invalid_without_throwing(self) -> None:
        verdict = evaluate_play_log({"schema_version": "wrong"}, self.root, self._manifest())
        self.assertEqual("INVALID", verdict["verdict"])
        self.assertTrue(verdict["problems"])

    def test_required_actions_cannot_omit_a_manifest_binding(self) -> None:
        log = self._valid_log()
        log["required_actions"] = log["required_actions"][:1]
        log["required_controls"] = ["options.bgm"]
        log["actions"] = log["actions"][:1]
        verdict = evaluate_play_log(log, self.root, self._manifest())
        self.assertEqual("INVALID", verdict["verdict"])
        self.assertTrue(any("frozen manifest" in problem for problem in verdict["problems"]))


if __name__ == "__main__":
    unittest.main()
