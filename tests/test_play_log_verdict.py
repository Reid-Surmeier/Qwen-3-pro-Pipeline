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
            "required_controls": ["options.bgm", "options.skin"],
            "required_actions": [
                {"control_id": "options.bgm", "gesture": "Drag", "window_action": "SetRange"},
                {"control_id": "options.skin", "gesture": "Activate", "window_action": "ToggleDropdown"},
            ],
            "console_errors": [],
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

    def test_complete_hash_locked_log_passes(self) -> None:
        verdict = evaluate_play_log(self._valid_log(), self.root)
        self.assertEqual("PASS", verdict["verdict"])
        self.assertEqual(3, verdict["frames_verified"])

    def test_unexercised_control_is_incomplete(self) -> None:
        log = self._valid_log()
        log["actions"] = log["actions"][:1]
        verdict = evaluate_play_log(log, self.root)
        self.assertEqual("INCOMPLETE", verdict["verdict"])
        self.assertEqual(["options.skin"], verdict["unexercised"])

    def test_unexercised_manifest_action_is_incomplete(self) -> None:
        log = self._valid_log()
        log["required_actions"].append(
            {"control_id": "options.bgm", "gesture": "Wheel", "window_action": "StepRange"}
        )
        verdict = evaluate_play_log(log, self.root)
        self.assertEqual("INCOMPLETE", verdict["verdict"])
        self.assertEqual(
            ["options.bgm:Wheel:StepRange"], verdict["unexercised_actions"]
        )

    def test_false_action_claim_fails(self) -> None:
        log = self._valid_log()
        log["actions"][1]["matches_expected"] = False
        verdict = evaluate_play_log(log, self.root)
        self.assertEqual("FAIL", verdict["verdict"])

    def test_console_error_fails(self) -> None:
        log = self._valid_log()
        log["console_errors"] = ["Invalid call"]
        verdict = evaluate_play_log(log, self.root)
        self.assertEqual("FAIL", verdict["verdict"])

    def test_missing_or_changed_frame_is_invalid(self) -> None:
        missing = self._valid_log()
        missing["actions"][1]["frames"]["after"]["path"] = "absent.png"
        self.assertEqual("INVALID", evaluate_play_log(missing, self.root)["verdict"])

        changed = self._valid_log()
        (self.root / "after.png").write_bytes(b"changed")
        self.assertEqual("INVALID", evaluate_play_log(changed, self.root)["verdict"])

    def test_drag_requires_mid_frame_and_thirty_motion_samples(self) -> None:
        log = self._valid_log()
        del log["actions"][0]["frames"]["mid"]
        log["actions"][0]["motion_samples"] = list(range(29))
        verdict = evaluate_play_log(log, self.root)
        self.assertEqual("INVALID", verdict["verdict"])
        self.assertTrue(any("30 motion samples" in problem for problem in verdict["problems"]))

    def test_malformed_root_is_invalid_without_throwing(self) -> None:
        verdict = evaluate_play_log({"schema_version": "wrong"}, self.root)
        self.assertEqual("INVALID", verdict["verdict"])
        self.assertTrue(verdict["problems"])


if __name__ == "__main__":
    unittest.main()
