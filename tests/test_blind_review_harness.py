"""Calibration tests for the blind-reviewer harness.

Three properties keep the harness honest, and each is tested directly:
the workspace shows the reviewer nothing beyond what the packet names
(blindness), the prompt is built from the packet and contract alone, and
a verdict that is malformed or self-contradictory can never validate
(fail-closed). No test here touches Docker, Hermes, or the network.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.blind_review.build_workspace import WorkspaceError, build_workspace
from scripts.blind_review.render_comment import render as render_comment
from scripts.blind_review.render_prompt import render as render_prompt
from scripts.blind_review.validate_verdict import validate_verdict


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


class HarnessFixture(unittest.TestCase):
    """A scratch candidate repository with a committed packet's worth of files."""

    IMPLEMENTER_SECRET = "the implementer struggled with checkbox hitboxes"

    def setUp(self) -> None:
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        root = Path(self._directory.name)
        self.repo = root / "repo"
        self.workdir = root / "work"
        (self.repo / "docs/reviews").mkdir(parents=True)
        (self.repo / "artifacts/references").mkdir(parents=True)
        (self.repo / "qa/out").mkdir(parents=True)
        (self.repo / "godot").mkdir()
        self.workdir.mkdir()

        run_git(self.repo, "init", "--quiet")
        run_git(self.repo, "config", "user.name", "Calibration")
        run_git(self.repo, "config", "user.email", "calibration@example.invalid")

        (self.repo / "docs/reviews/issue-86-contract.md").write_text(
            "# Contract\n\nV1 — the party window matches the reference.\n",
            encoding="utf-8",
        )
        (self.repo / "artifacts/references/reference.png").write_bytes(b"reference-pixels")
        (self.repo / "qa/out/capture.png").write_bytes(b"candidate-pixels")
        (self.repo / "godot/project.godot").write_text("[application]\n", encoding="utf-8")
        (self.repo / "IMPLEMENTATION-NOTES.md").write_text(
            self.IMPLEMENTER_SECRET + "\n", encoding="utf-8"
        )

        run_git(self.repo, "add", "-A")
        run_git(self.repo, "commit", "--quiet", "-m", "candidate")
        self.head = run_git(self.repo, "rev-parse", "HEAD")

        self.packet = {
            "schema_version": 1,
            "issue": 86,
            "candidate_commit": self.head,
            "acceptance_contract": "docs/reviews/issue-86-contract.md",
            "references": [
                {
                    "path": "artifacts/references/reference.png",
                    "sha256": hashlib.sha256(b"reference-pixels").hexdigest(),
                }
            ],
            "candidate": {"evidence": ["qa/out/capture.png"]},
            "launch": {"command": "godot --path godot"},
        }
        self.packet_path = self.repo / "packet.json"
        self.packet_path.write_text(json.dumps(self.packet), encoding="utf-8")

    def build(self, include: list[str] | None = None) -> Path:
        workspace = self.workdir / "workspace"
        build_workspace(self.packet_path, self.repo, workspace, include or [])
        return workspace

    def good_verdict(self) -> dict:
        return {
            "schema_version": 1,
            "candidate_commit": self.head,
            "verdict": "fail",
            "findings": [
                {
                    "id": "BR-01",
                    "title": "party window typography drifts",
                    "contract_clause": "V1",
                    "state": "idle",
                    "steps": ["launch", "observe party window"],
                    "expected": "source-matched glyphs",
                    "actual": "wider glyphs",
                    "evidence": "/out/BR-01.png",
                    "severity": "blocking",
                }
            ],
            "unverified": [],
            "positive": ["window dragging preserved plates"],
            "followups": [],
        }


class WorkspaceBlindnessTests(HarnessFixture):
    def test_workspace_contains_exactly_the_packet_paths(self) -> None:
        workspace = self.build()
        delivered = {
            str(path.relative_to(workspace))
            for path in workspace.rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            delivered,
            {
                "docs/reviews/issue-86-contract.md",
                "artifacts/references/reference.png",
                "qa/out/capture.png",
                "packet.json",
                "workspace-manifest.json",
            },
        )

    def test_workspace_excludes_git_history_and_implementer_notes(self) -> None:
        workspace = self.build(include=["godot"])
        self.assertFalse((workspace / ".git").exists())
        self.assertFalse((workspace / "IMPLEMENTATION-NOTES.md").exists())
        self.assertTrue((workspace / "godot/project.godot").is_file())

    def test_workspace_is_cut_at_the_candidate_sha_not_the_working_tree(self) -> None:
        (self.repo / "qa/out/capture.png").write_bytes(b"drifted-uncommitted-pixels")
        workspace = self.build()
        self.assertEqual(
            (workspace / "qa/out/capture.png").read_bytes(), b"candidate-pixels"
        )

    def test_reference_tampered_at_the_sha_refuses_to_build(self) -> None:
        (self.repo / "artifacts/references/reference.png").write_bytes(b"tampered")
        run_git(self.repo, "add", "-A")
        run_git(self.repo, "commit", "--quiet", "-m", "tamper")
        self.packet["candidate_commit"] = run_git(self.repo, "rev-parse", "HEAD")
        self.packet_path.write_text(json.dumps(self.packet), encoding="utf-8")
        with self.assertRaises(WorkspaceError):
            self.build()

    def test_manifest_records_every_delivered_file_hash(self) -> None:
        workspace = self.build()
        manifest = json.loads(
            (workspace / "workspace-manifest.json").read_text(encoding="utf-8")
        )
        recorded = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
        self.assertEqual(
            recorded["artifacts/references/reference.png"],
            hashlib.sha256(b"reference-pixels").hexdigest(),
        )
        self.assertEqual(manifest["candidate_commit"], self.head)


class PromptTests(HarnessFixture):
    def test_prompt_carries_contract_sha_and_launch_only(self) -> None:
        prompt = render_prompt(self.build())
        self.assertIn(self.head, prompt)
        self.assertIn("the party window matches the reference", prompt)
        self.assertIn("godot --path godot", prompt)
        self.assertNotIn(self.IMPLEMENTER_SECRET, prompt)

    def test_prompt_demands_a_disposition_for_every_clause(self) -> None:
        prompt = render_prompt(self.build())
        self.assertIn("pass, fail, or", prompt)
        self.assertIn("/out/review.json", prompt)


class VerdictFailClosedTests(HarnessFixture):
    def check(self, verdict: dict) -> list[str]:
        out_dir = self.workdir / "out"
        out_dir.mkdir(exist_ok=True)
        (out_dir / "BR-01.png").write_bytes(b"evidence")
        verdict_path = self.workdir / "review.json"
        verdict_path.write_text(json.dumps(verdict), encoding="utf-8")
        workspace = self.workdir / "workspace"
        if not workspace.exists():
            self.build()
        failures = validate_verdict(verdict_path, workspace / "packet.json", out_dir)
        return [failure["code"] for failure in failures]

    def test_known_good_verdict_validates(self) -> None:
        self.assertEqual(self.check(self.good_verdict()), [])

    def test_pass_with_blocking_finding_is_contradictory(self) -> None:
        verdict = self.good_verdict()
        verdict["verdict"] = "pass"
        self.assertIn("pass-with-blocking-finding", self.check(verdict))

    def test_fail_without_blocking_finding_is_contradictory(self) -> None:
        verdict = self.good_verdict()
        verdict["findings"][0]["severity"] = "minor"
        self.assertIn("fail-without-blocking-finding", self.check(verdict))

    def test_wrong_candidate_sha_is_rejected(self) -> None:
        verdict = self.good_verdict()
        verdict["candidate_commit"] = "f" * 40
        self.assertIn("candidate-commit-mismatch", self.check(verdict))

    def test_missing_evidence_file_is_rejected(self) -> None:
        verdict = self.good_verdict()
        verdict["findings"][0]["evidence"] = "/out/never-captured.png"
        self.assertIn("finding-evidence-not-found", self.check(verdict))

    def test_blocked_verdict_must_name_a_reason(self) -> None:
        verdict = self.good_verdict()
        verdict["verdict"] = "blocked"
        verdict["findings"] = []
        self.assertIn("blocked-without-reason", self.check(verdict))

    def test_extra_keys_are_rejected_not_ignored(self) -> None:
        verdict = self.good_verdict()
        verdict["implementer_notes"] = "trust me"
        self.assertIn("verdict-unknown-keys", self.check(verdict))

    def test_unparseable_verdict_fails_closed(self) -> None:
        verdict_path = self.workdir / "review.json"
        verdict_path.write_text("{not json", encoding="utf-8")
        workspace = self.build()
        failures = validate_verdict(
            verdict_path, workspace / "packet.json", self.workdir
        )
        self.assertEqual([f["code"] for f in failures], ["verdict-unparseable"])


class CommentTests(HarnessFixture):
    def test_comment_renders_the_documented_sections(self) -> None:
        comment = render_comment(self.good_verdict(), "docs/reviews/issue-86-contract.md")
        self.assertIn("## Blind artifact review", comment)
        self.assertIn("Verdict: **FAIL**", comment)
        self.assertIn("BR-01", comment)
        self.assertIn("### Positive observations", comment)
        self.assertIn("### Required disposition", comment)


if __name__ == "__main__":
    unittest.main()
