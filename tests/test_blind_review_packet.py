from __future__ import annotations

import importlib.util
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
            MODULE.validate_packet(packet_path, ROOT,
                                   "82ae10483fd41d365f1ca54fe691e894c9727303"),
        )


if __name__ == "__main__":
    unittest.main()
