"""Calibration tests for the blind-review packet validator.

The gate is only trustworthy if a known-good packet passes and every
known-bad packet blocks with the specific failure that made it bad. These
tests are that calibration.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.validate_blind_review_packet import validate_packet


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class BlindReviewPacketValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.repo = Path(self._directory.name)

        run_git(self.repo, "init", "--quiet")
        run_git(self.repo, "config", "user.name", "Calibration")
        run_git(self.repo, "config", "user.email", "calibration@example.invalid")

        (self.repo / "docs" / "reviews").mkdir(parents=True)
        (self.repo / "artifacts" / "references").mkdir(parents=True)
        (self.repo / "qa" / "out").mkdir(parents=True)

        self.contract = Path("docs/reviews/issue-86-contract.md")
        (self.repo / self.contract).write_text("# Contract\n", encoding="utf-8")

        self.reference = Path("artifacts/references/reference-native.png")
        (self.repo / self.reference).write_bytes(b"reference-pixels")
        self.reference_sha = hashlib.sha256(b"reference-pixels").hexdigest()

        self.evidence = Path("qa/out/capture.png")
        (self.repo / self.evidence).write_bytes(b"candidate-pixels")

        run_git(self.repo, "add", "-A")
        run_git(self.repo, "commit", "--quiet", "-m", "candidate")
        self.head = run_git(self.repo, "rev-parse", "HEAD")

    def good_packet(self) -> dict:
        return {
            "schema_version": 1,
            "issue": 86,
            "pull_request": 90,
            "candidate_commit": self.head,
            "acceptance_contract": str(self.contract),
            "references": [
                {"path": str(self.reference), "sha256": self.reference_sha}
            ],
            "candidate": {"evidence": [str(self.evidence)]},
            "launch": {
                "command": "godot --path godot",
                "clean_state_command": "bash godot/qa/reset-state.sh",
            },
        }

    def write_packet(self, packet: dict) -> Path:
        path = self.repo / "packet.json"
        path.write_text(json.dumps(packet), encoding="utf-8")
        return path

    def failure_codes(self, packet: dict, expect_sha: str | None = None) -> list[str]:
        failures = validate_packet(self.write_packet(packet), self.repo, expect_sha)
        return [failure["code"] for failure in failures]

    def test_known_good_packet_is_valid(self) -> None:
        self.assertEqual(self.failure_codes(self.good_packet()), [])

    def test_known_good_packet_passes_expected_sha_check(self) -> None:
        self.assertEqual(self.failure_codes(self.good_packet(), expect_sha=self.head), [])

    def test_tampered_reference_hash_blocks(self) -> None:
        packet = self.good_packet()
        (self.repo / self.reference).write_bytes(b"tampered-pixels")
        self.assertIn("reference-hash-mismatch", self.failure_codes(packet))

    def test_unknown_candidate_commit_blocks(self) -> None:
        packet = self.good_packet()
        packet["candidate_commit"] = "0" * 40
        self.assertIn("candidate-commit-unknown", self.failure_codes(packet))

    def test_candidate_commit_must_match_expected_sha(self) -> None:
        codes = self.failure_codes(self.good_packet(), expect_sha="f" * 40)
        self.assertIn("candidate-commit-mismatch", codes)

    def test_missing_evidence_file_blocks(self) -> None:
        packet = self.good_packet()
        packet["candidate"]["evidence"] = ["qa/out/does-not-exist.png"]
        self.assertIn("evidence-not-found", self.failure_codes(packet))

    def test_missing_launch_instructions_block(self) -> None:
        packet = self.good_packet()
        del packet["launch"]
        self.assertIn("launch-missing", self.failure_codes(packet))

    def test_missing_acceptance_contract_blocks(self) -> None:
        packet = self.good_packet()
        packet["acceptance_contract"] = "docs/reviews/missing-contract.md"
        self.assertIn("acceptance-contract-not-found", self.failure_codes(packet))

    def test_unparseable_packet_blocks(self) -> None:
        path = self.repo / "packet.json"
        path.write_text("{not json", encoding="utf-8")
        failures = validate_packet(path, self.repo, None)
        self.assertEqual([failure["code"] for failure in failures], ["packet-unparseable"])

    def test_cli_reports_verdict_and_exit_code(self) -> None:
        import sys

        packet_path = self.write_packet(self.good_packet())
        script = Path(__file__).resolve().parents[1] / "scripts" / "validate_blind_review_packet.py"
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--packet",
                str(packet_path),
                "--repo",
                str(self.repo),
                "--expect-sha",
                self.head,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "valid")


if __name__ == "__main__":
    unittest.main()
