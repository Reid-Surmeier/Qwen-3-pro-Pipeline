from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
