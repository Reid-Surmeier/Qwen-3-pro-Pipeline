import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark_comfyui_routing.py"
SPEC = importlib.util.spec_from_file_location("benchmark_comfyui_routing", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not load routing benchmark")
BENCHMARK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BENCHMARK
SPEC.loader.exec_module(BENCHMARK)


def _pinned_git_objects_available():
    try:
        for commit in (BENCHMARK.BASELINE_COMMIT, BENCHMARK.CANDIDATE_COMMIT):
            BENCHMARK._git(ROOT, "cat-file", "-e", f"{commit}^{{commit}}")
        for branch in (BENCHMARK.BASELINE_BRANCH, BENCHMARK.CANDIDATE_BRANCH):
            BENCHMARK._git(
                ROOT,
                "show-ref",
                "--verify",
                f"refs/remotes/origin/{branch}",
            )
    except subprocess.CalledProcessError:
        return False
    return True


PINNED_GIT_OBJECTS_AVAILABLE = _pinned_git_objects_available()


class ComfyUIRoutingBenchmarkTests(unittest.TestCase):
    def test_defines_exact_archived_refs_and_six_equivalent_jobs(self):
        self.assertEqual(
            BENCHMARK.BASELINE_COMMIT,
            "e8079a3d311f0402afa179080905b2e431c6c972",
        )
        self.assertEqual(
            BENCHMARK.CANDIDATE_COMMIT,
            "b8e226cb12f7cea8a201da73a852542938fdad9f",
        )
        jobs = BENCHMARK._build_jobs(1.0)
        self.assertEqual(len(jobs), 6)
        self.assertEqual(len({job.payload for job in jobs}), 6)
        for job in jobs:
            payload = json.loads(job.payload)
            self.assertEqual(
                payload["prompt"]["1"]["class_type"], "SyntheticNoProviderNode"
            )

    @unittest.skipUnless(
        PINNED_GIT_OBJECTS_AVAILABLE,
        "archive refs are unavailable in this checkout",
    )
    def test_verifies_exact_archived_refs(self):
        pins = BENCHMARK._verify_pins(ROOT)

        self.assertEqual(
            pins["resolved_branches"][BENCHMARK.BASELINE_BRANCH],
            BENCHMARK.BASELINE_COMMIT,
        )
        self.assertEqual(
            pins["resolved_branches"][BENCHMARK.CANDIDATE_BRANCH],
            BENCHMARK.CANDIDATE_COMMIT,
        )
    @unittest.skipUnless(
        PINNED_GIT_OBJECTS_AVAILABLE,
        "archive refs are unavailable in this checkout",
    )
    def test_records_complete_comparable_runs_without_retries(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "benchmark"
            manifest = BENCHMARK.run_benchmark(
                ROOT,
                output,
                repeat_count=2,
                duration_scale=0.2,
            )

            self.assertEqual(len(manifest["runs"]), 4)
            self.assertTrue(manifest["summary"]["output_digest_parity"])
            self.assertEqual(manifest["summary"]["baseline"]["retry_count"], 0)
            self.assertEqual(manifest["summary"]["candidate"]["retry_count"], 0)
            self.assertEqual(
                manifest["summary"]["candidate"]["routing_failures"], 0
            )
            self.assertEqual(
                manifest["summary"]["candidate"]["history_failures"], 0
            )
            self.assertEqual(manifest["summary"]["candidate"]["dropped_jobs"], 0)
            self.assertEqual(manifest["summary"]["candidate"]["timeout_count"], 0)
            self.assertEqual(
                manifest["summary"]["candidate"]["missing_observations"], 0
            )
            self.assertEqual(
                len(manifest["summary"]["candidate"]["workers_observed"]), 5
            )
            self.assertEqual(manifest["summary"]["conclusion"], "promising")
            self.assertTrue((output / "results.json").is_file())
            self.assertTrue((output / "report.md").is_file())

            for run in manifest["runs"]:
                self.assertEqual(len(run["jobs"]), 6)
                for job in run["jobs"]:
                    self.assertEqual(job["status"], "completed")
                    self.assertIsNone(job["error"])
                    self.assertEqual(job["enqueue_attempts"], 1)
                    self.assertTrue(job["history_verified"])
                    self.assertEqual(
                        job["payload_sha256"], job["expected_payload_sha256"]
                    )


if __name__ == "__main__":
    unittest.main()
