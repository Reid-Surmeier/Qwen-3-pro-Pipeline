from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class VerifyWorkflowTests(unittest.TestCase):
    def test_checkout_includes_history_required_by_review_packets(self) -> None:
        workflow = (ROOT / ".github/workflows/verify.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "fetch-depth: 0",
            workflow,
            "review-packet validation reads pinned ancestor commits",
        )


if __name__ == "__main__":
    unittest.main()
