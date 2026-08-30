from __future__ import annotations

import importlib.util
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
        candidate = "7dcc651993319b5cfbb1aee1049bc7b9c82d0caf"
        packet = ROOT / "artifacts" / "reviews" / "issue-125" / "packet.json"
        self.assertEqual([], MODULE.validate_packet(packet, ROOT, candidate))

    def test_candidate_mismatch_fails_closed(self) -> None:
        packet = ROOT / "artifacts" / "reviews" / "issue-125" / "packet.json"
        problems = MODULE.validate_packet(packet, ROOT, "0" * 40)
        self.assertIn("packet candidate_commit does not match requested candidate", problems)


if __name__ == "__main__":
    unittest.main()
