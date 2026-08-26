import io
import json
import tempfile
import unittest
from pathlib import Path

from qwen_ui_pipeline import (
    CapacityPlanningError,
    CapacityPolicy,
    MemorySnapshot,
    plan_capacity_scenarios,
    plan_worker_capacity,
)
from qwen_ui_pipeline.capacity import main as capacity_main


GIB = 1024**3


class WorkerCapacityTests(unittest.TestCase):
    def test_twelve_job_burst_queues_work_above_the_safe_worker_cap(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        plan = plan_worker_capacity(
            snapshot,
            policy,
            requested_workers=5,
            submitted_jobs=12,
        )

        self.assertEqual(plan.recommended_workers, 5)
        self.assertEqual(plan.maximum_simultaneous_jobs, 5)
        self.assertEqual(plan.accepted_jobs, 12)
        self.assertEqual(plan.queued_jobs, 7)
        self.assertEqual(plan.rejected_jobs, 0)

    def test_maximum_simultaneous_jobs_is_capacity_not_current_demand(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        plan = plan_worker_capacity(
            snapshot,
            policy,
            requested_workers=5,
            submitted_jobs=2,
        )

        self.assertEqual(plan.maximum_simultaneous_jobs, 5)
        self.assertEqual(plan.accepted_jobs, 2)
        self.assertEqual(plan.queued_jobs, 0)

    def test_memory_ceiling_and_host_reserve_clamp_requested_workers(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        plan = plan_worker_capacity(
            snapshot,
            policy,
            requested_workers=12,
            submitted_jobs=24,
        )

        self.assertEqual(plan.memory_limited_worker_count, 5)
        self.assertEqual(plan.recommended_workers, 5)
        self.assertLessEqual(
            plan.projected_total_used_bytes + policy.host_reserve_bytes,
            policy.memory_ceiling_bytes,
        )
        self.assertGreaterEqual(
            plan.remaining_host_headroom_bytes,
            policy.host_reserve_bytes,
        )
        self.assertIn("memory_limit", plan.reasons)

    def test_stale_memory_measurement_fails_closed(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=301,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        with self.assertRaisesRegex(CapacityPlanningError, "stale"):
            plan_worker_capacity(
                snapshot,
                policy,
                requested_workers=6,
                submitted_jobs=12,
            )

    def test_zero_worker_reserve_fails_closed(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=0,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        with self.assertRaisesRegex(CapacityPlanningError, "worker reserve"):
            plan_worker_capacity(
                snapshot,
                policy,
                requested_workers=6,
                submitted_jobs=12,
            )

    def test_zero_worker_safety_factor_fails_closed(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=0,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        with self.assertRaisesRegex(CapacityPlanningError, "safety factor"):
            plan_worker_capacity(
                snapshot,
                policy,
                requested_workers=6,
                submitted_jobs=12,
            )

    def test_negative_job_count_fails_closed(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        with self.assertRaisesRegex(CapacityPlanningError, "submitted jobs"):
            plan_worker_capacity(
                snapshot,
                policy,
                requested_workers=6,
                submitted_jobs=-1,
            )

    def test_contradictory_memory_snapshot_fails_closed(self):
        snapshot = MemorySnapshot(
            total_bytes=40 * GIB,
            available_bytes=41 * GIB,
            service_current_bytes=3 * GIB,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        with self.assertRaisesRegex(CapacityPlanningError, "available memory"):
            plan_worker_capacity(
                snapshot,
                policy,
                requested_workers=6,
                submitted_jobs=12,
            )

    def test_service_memory_above_host_used_memory_fails_closed(self):
        snapshot = MemorySnapshot(
            total_bytes=50 * GIB,
            available_bytes=49 * GIB,
            service_current_bytes=3 * GIB,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        with self.assertRaisesRegex(CapacityPlanningError, "service memory"):
            plan_worker_capacity(
                snapshot,
                policy,
                requested_workers=6,
                submitted_jobs=12,
            )

    def test_unvalidated_active_peak_blocks_worker_increase(self):
        snapshot = MemorySnapshot(
            total_bytes=50 * GIB,
            available_bytes=30 * GIB,
            service_current_bytes=3 * GIB,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=False,
        )

        plan = plan_worker_capacity(
            snapshot,
            policy,
            requested_workers=8,
            submitted_jobs=12,
        )

        self.assertGreaterEqual(plan.memory_limited_worker_count, 8)
        self.assertEqual(plan.recommended_workers, 5)
        self.assertIn("active_worker_peak_unvalidated", plan.reasons)

    def test_sensitivity_matrix_exposes_worker_and_burst_assumptions(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=False,
        )

        scenarios = plan_capacity_scenarios(
            snapshot,
            policy,
            requested_worker_counts=(5, 6, 8, 10, 12),
            submitted_job_counts=(6, 12, 24),
        )

        self.assertEqual(len(scenarios), 15)
        self.assertEqual(
            {(item.requested_workers, item.submitted_jobs) for item in scenarios},
            {
                (workers, jobs)
                for workers in (5, 6, 8, 10, 12)
                for jobs in (6, 12, 24)
            },
        )
        self.assertTrue(
            all(item.recommendation.recommended_workers <= 5 for item in scenarios)
        )
        self.assertTrue(
            all(
                "active_worker_peak_unvalidated" in item.recommendation.reasons
                for item in scenarios
                if item.requested_workers > 5
            )
        )

    def test_cli_emits_machine_readable_plan_and_sensitivity_matrix(self):
        request = {
            "snapshot": {
                "total_bytes": 50_510_004_224,
                "available_bytes": 21_926_240_256,
                "service_current_bytes": 3_546_509_312,
                "configured_workers": 5,
                "measurement_age_seconds": 0,
            },
            "policy": {
                "memory_ceiling_bytes": 45 * GIB,
                "host_reserve_bytes": 8 * GIB,
                "worker_reserved_bytes": 2 * GIB,
                "worker_safety_factor": 1.25,
                "queue_limit": 64,
                "max_measurement_age_seconds": 300,
                "worker_peak_validated": False,
            },
            "requested_workers": 12,
            "submitted_jobs": 24,
            "sensitivity": {
                "requested_worker_counts": [5, 6, 8, 10, 12],
                "submitted_job_counts": [6, 12, 24],
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            request_path = Path(directory) / "request.json"
            result_path = Path(directory) / "result.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            output = io.StringIO()

            status = capacity_main(
                [
                    "--input",
                    str(request_path),
                    "--output",
                    str(result_path),
                ],
                stdout=output,
            )
            result = json.loads(result_path.read_text(encoding="utf-8"))

        self.assertEqual(status, 0)
        self.assertEqual(output.getvalue(), "")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["decision"], "keep-current-workers")
        self.assertEqual(result["plan"]["recommended_workers"], 5)
        self.assertEqual(result["plan"]["queued_jobs"], 19)
        self.assertEqual(len(result["scenarios"]), 15)

    def test_provider_concurrency_is_separate_from_local_worker_capacity(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
            provider_concurrency_limit=3,
        )

        plan = plan_worker_capacity(
            snapshot,
            policy,
            requested_workers=5,
            submitted_jobs=12,
        )

        self.assertEqual(plan.recommended_workers, 5)
        self.assertEqual(plan.maximum_simultaneous_jobs, 3)
        self.assertEqual(plan.queued_jobs, 9)
        self.assertIn("provider_concurrency_limit", plan.reasons)

    def test_queue_limit_rejects_burst_over_bounded_capacity(self):
        snapshot = MemorySnapshot(
            total_bytes=50_510_004_224,
            available_bytes=21_926_240_256,
            service_current_bytes=3_546_509_312,
            configured_workers=5,
            measurement_age_seconds=0,
        )
        policy = CapacityPolicy(
            memory_ceiling_bytes=45 * GIB,
            host_reserve_bytes=8 * GIB,
            worker_reserved_bytes=2 * GIB,
            worker_safety_factor=1.25,
            queue_limit=64,
            max_measurement_age_seconds=300,
            worker_peak_validated=True,
        )

        plan = plan_worker_capacity(
            snapshot,
            policy,
            requested_workers=5,
            submitted_jobs=100,
        )

        self.assertEqual(plan.maximum_simultaneous_jobs, 5)
        self.assertEqual(plan.queued_jobs, 64)
        self.assertEqual(plan.accepted_jobs, 69)
        self.assertEqual(plan.rejected_jobs, 31)

    def test_cli_reports_unsafe_input_as_machine_readable_error(self):
        request = {
            "snapshot": {
                "total_bytes": 50_510_004_224,
                "available_bytes": 21_926_240_256,
                "service_current_bytes": 3_546_509_312,
                "configured_workers": 5,
                "measurement_age_seconds": 0,
            },
            "policy": {
                "memory_ceiling_bytes": 45 * GIB,
                "host_reserve_bytes": 8 * GIB,
                "worker_reserved_bytes": 0,
                "worker_safety_factor": 1.25,
                "queue_limit": 64,
                "max_measurement_age_seconds": 300,
                "worker_peak_validated": False,
            },
            "requested_workers": 12,
            "submitted_jobs": 24,
            "sensitivity": {
                "requested_worker_counts": [5, 6, 8, 10, 12],
                "submitted_job_counts": [6, 12, 24],
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            request_path = Path(directory) / "request.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            output = io.StringIO()

            status = capacity_main(
                ["--input", str(request_path)],
                stdout=output,
            )

        result = json.loads(output.getvalue())
        self.assertEqual(status, 2)
        self.assertEqual(result["status"], "error")
        self.assertIn("worker reserve", result["error"])

    def test_cli_reports_missing_measurement_as_machine_readable_error(self):
        request = {
            "snapshot": {
                "total_bytes": 50_510_004_224,
                "service_current_bytes": 3_546_509_312,
                "configured_workers": 5,
                "measurement_age_seconds": 0,
            },
            "policy": {
                "memory_ceiling_bytes": 45 * GIB,
                "host_reserve_bytes": 8 * GIB,
                "worker_reserved_bytes": 2 * GIB,
                "worker_safety_factor": 1.25,
                "queue_limit": 64,
                "max_measurement_age_seconds": 300,
                "worker_peak_validated": False,
            },
            "requested_workers": 12,
            "submitted_jobs": 24,
            "sensitivity": {
                "requested_worker_counts": [5, 6, 8, 10, 12],
                "submitted_job_counts": [6, 12, 24],
            },
        }

        with tempfile.TemporaryDirectory() as directory:
            request_path = Path(directory) / "request.json"
            request_path.write_text(json.dumps(request), encoding="utf-8")
            output = io.StringIO()

            status = capacity_main(
                ["--input", str(request_path)],
                stdout=output,
            )

        result = json.loads(output.getvalue())
        self.assertEqual(status, 2)
        self.assertEqual(result["status"], "error")
        self.assertIn("available_bytes", result["error"])


if __name__ == "__main__":
    unittest.main()
