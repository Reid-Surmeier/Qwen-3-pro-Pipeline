from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.audit_project_skills import compute_skill_folder_hash


REPO_ROOT = Path(__file__).resolve().parents[1]


class ProjectSkillsAuditTests(unittest.TestCase):
    def test_project_skill_installation_matches_recorded_inventory(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "audit_project_skills.py")],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("OK: 37 project-local skills", result.stdout)

    def test_folder_hash_detects_a_vendored_skill_mutation(self) -> None:
        source = REPO_ROOT / ".agents" / "skills" / "ask-matt"
        expected = "0cd14026efa0330083cbc7adf590976c162b60e02f696a8dcce96f0b4dab8a72"
        self.assertEqual(compute_skill_folder_hash(source), expected)

        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "ask-matt"
            shutil.copytree(source, candidate)
            skill_file = candidate / "SKILL.md"
            skill_file.write_text(
                skill_file.read_text(encoding="utf-8") + "\nmutation\n",
                encoding="utf-8",
            )

            self.assertNotEqual(compute_skill_folder_hash(candidate), expected)


if __name__ == "__main__":
    unittest.main()
