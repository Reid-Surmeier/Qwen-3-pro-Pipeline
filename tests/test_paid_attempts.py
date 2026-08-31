import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from qwen_ui_pipeline.paid_attempts import PaidAttemptLedger


class PaidAttemptLedgerTests(unittest.TestCase):
    def test_attempt_sentinel_blocks_resubmission_even_before_a_response(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = PaidAttemptLedger(Path(temporary))
            record = ledger.begin("legacy", request_sha256="abc123", requested_outputs=1)

            self.assertEqual(record["status"], "submitting")
            with self.assertRaisesRegex(RuntimeError, "refusing to submit"):
                ledger.assert_unexecuted(("legacy", "partner"))
            with self.assertRaisesRegex(RuntimeError, "refusing to resubmit"):
                ledger.begin("legacy", request_sha256="abc123", requested_outputs=1)

    def test_attempt_updates_preserve_identity_and_request_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = PaidAttemptLedger(Path(temporary))
            started = ledger.begin("partner", request_sha256="request-hash", requested_outputs=1)
            completed = ledger.update("partner", status="completed", completed_outputs=1)
            stored = json.loads(
                (Path(temporary) / "partner/attempt.json").read_text(encoding="utf-8")
            )

            self.assertEqual(completed["attempt_id"], started["attempt_id"])
            self.assertEqual(stored["request_sha256"], "request-hash")
            self.assertEqual(stored["status"], "completed")
            self.assertFalse(stored["retry_allowed"])

    def test_reviewed_plan_blocks_prepare_but_remains_executable_once(self):
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary)
            (run / "plan.json").write_text("{}\n", encoding="utf-8")
            ledger = PaidAttemptLedger(run)

            with self.assertRaisesRegex(RuntimeError, "overwrite preparation"):
                ledger.assert_unprepared(("legacy", "partner"))
            ledger.assert_unexecuted(("legacy", "partner"))

    def test_attempt_creation_and_updates_sync_files_and_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            ledger = PaidAttemptLedger(Path(temporary))
            with patch("qwen_ui_pipeline.paid_attempts.os.fsync", wraps=os.fsync) as fsync:
                ledger.begin("legacy", request_sha256="request-hash", requested_outputs=1)
                begin_syncs = fsync.call_count
                ledger.update("legacy", status="completed")

            self.assertGreaterEqual(begin_syncs, 3)
            self.assertGreaterEqual(fsync.call_count - begin_syncs, 2)


if __name__ == "__main__":
    unittest.main()
