from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "validate_blind_review_packet", ROOT / "scripts" / "validate_blind_review_packet.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BlindReviewPacketTests(unittest.TestCase):
    def test_current_issue_125_packet_is_hash_locked(self) -> None:
        candidate = "e395a3413a4d6bfc05582eaf17340662cc6420c2"
        packet = ROOT / "artifacts" / "reviews" / "issue-125" / "packet.json"
        self.assertEqual([], MODULE.validate_packet(packet, ROOT, candidate))

    def test_candidate_mismatch_fails_closed(self) -> None:
        packet = ROOT / "artifacts" / "reviews" / "issue-125" / "packet.json"
        problems = MODULE.validate_packet(packet, ROOT, "0" * 40)
        self.assertIn("packet candidate_commit does not match requested candidate", problems)

    def test_issue_126_packet_declares_each_evidence_manifest(self) -> None:
        packet_path = ROOT / "artifacts" / "reviews" / "issue-126" / "packet.json"
        packet = json.loads(packet_path.read_text())
        self.assertEqual(
            [
                "artifacts/reviews/issue-126/builder/evidence-manifest.json",
                "artifacts/reviews/issue-126/options-regression/evidence-manifest.json",
            ],
            packet["candidate"]["evidence_manifests"],
        )
        self.assertEqual(
            [],
            MODULE.validate_packet(packet_path, ROOT, "82ae10483fd41d365f1ca54fe691e894c9727303"),
        )

    def test_play_log_commit_must_match_trusted_packet_candidate(self) -> None:
        candidate = "7e2ff9ee5b8d55ef9d7cfe077de46975a53f9daf"
        source = ROOT / "artifacts" / "reviews" / "issue-127" / "builder-7e2ff9e" / "play-log.json"
        with tempfile.TemporaryDirectory() as directory:
            evidence_root = Path(directory)
            locked = evidence_root / "locked.txt"
            locked.write_text("locked")
            manifest = evidence_root / "evidence-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "candidate_commit": candidate,
                        "files": [
                            {
                                "path": locked.name,
                                "sha256": hashlib.sha256(locked.read_bytes()).hexdigest(),
                            }
                        ],
                    }
                )
            )
            play_log = json.loads(source.read_text())
            play_log["candidate"]["commit_sha"] = "0" * 40
            (evidence_root / "play-log.json").write_text(json.dumps(play_log))
            problems: list[str] = []
            MODULE._validate_evidence_manifest(manifest, ROOT, candidate, 127, problems)
            self.assertTrue(
                any(
                    "Play Log candidate commit does not match packet candidate" in problem
                    for problem in problems
                ),
                problems,
            )

    def test_issue_127_packet_bootstraps_a_complete_godot_import(self) -> None:
        packet = json.loads(
            (ROOT / "artifacts" / "reviews" / "issue-127" / "packet.json").read_text()
        )
        launch = packet["launch"]
        for command in (launch["command"], launch["clean_state_command"]):
            self.assertIn("--headless --path godot --import", command)
            self.assertNotIn("--quit-after", command)

    def test_issue_127_clean_state_records_the_godot_process(self) -> None:
        packet = json.loads(
            (ROOT / "artifacts" / "reviews" / "issue-127" / "packet.json").read_text()
        )
        command = packet["launch"]["clean_state_command"]
        self.assertIn("&& { nohup env", command)
        self.assertIn("& echo $! >/tmp/issue127-blind-review.pid; }", command)


if __name__ == "__main__":
    unittest.main()
