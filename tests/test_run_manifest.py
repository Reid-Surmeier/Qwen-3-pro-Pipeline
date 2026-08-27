"""Behavioral tests for the run-manifest validator (Issue #20)."""

import copy
import unittest

from qwen_ui_pipeline.run_manifest import validate_manifest

SHA = "a" * 64
SHA_B = "b" * 64
COMMIT = "c" * 40

VALID_RENDER = {
    "manifest_version": "run-manifest-v1",
    "run_id": "plantstudio-club-v009",
    "kind": "render",
    "repository_commit": COMMIT,
    "created_at": "2026-08-26T21:00:00-04:00",
    "status": "complete",
    "provider": {
        "name": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "prompt_id": "0f0e0d0c-1111-2222-3333-444455556666",
        "requested_outputs": 2,
        "completed_outputs": 2,
        "estimated_cost_usd": 0.083,
        "actual_cost_usd": 0.083,
    },
    "generation": {"seed": 2026082601},
    "sources": [
        {
            "role": "reference_screen",
            "path": "artifacts/references/plantstudio-main-window.png",
            "sha256": SHA,
        }
    ],
    "outputs": [
        {"path": "artifacts/runs/x/image-01.png", "sha256": SHA_B, "width": 948, "height": 806, "bytes": 1000},
        {"path": "artifacts/runs/x/image-02.png", "sha256": SHA, "width": 948, "height": 806, "bytes": 1000},
    ],
    "approvals": [
        {
            "decision": "approved",
            "actor": "repository-owner",
            "timestamp": "2026-08-26T22:00:00-04:00",
            "approved_sha256": SHA_B,
        }
    ],
}

VALID_ASSEMBLY = {
    "manifest_version": "run-manifest-v1",
    "run_id": "plantstudio-club-assembly-v004",
    "kind": "assembly",
    "repository_commit": COMMIT,
    "created_at": "2026-08-26T21:30:00-04:00",
    "status": "complete",
    "sources": [
        {"role": "reference_screen", "path": "artifacts/references/plantstudio-main-window.png", "sha256": SHA},
        {"role": "approved_donor", "path": "artifacts/runs/x/image-02.png", "sha256": SHA_B},
    ],
    "outputs": [
        {"path": "artifacts/runs/y/image-01.png", "sha256": SHA_B, "width": 474, "height": 403, "bytes": 500},
    ],
    "region": {"x": 182, "y": 78, "width": 37, "height": 165},
    "fidelity": {"outside_region_changed_pixels": 0},
    "approvals": [
        {"decision": "pending", "actor": "repository-owner", "timestamp": "2026-08-26T22:00:00-04:00"}
    ],
}


def invalid(mutate):
    manifest = copy.deepcopy(VALID_RENDER)
    mutate(manifest)
    return manifest


class RunManifestValidatorTests(unittest.TestCase):
    def assert_error(self, manifest, fragment):
        errors = validate_manifest(manifest)
        self.assertTrue(
            any(fragment in error for error in errors),
            f"expected an error containing {fragment!r}, got {errors}",
        )

    def test_valid_render_passes(self):
        self.assertEqual(validate_manifest(VALID_RENDER), [])

    def test_valid_assembly_passes(self):
        self.assertEqual(validate_manifest(VALID_ASSEMBLY), [])

    def test_missing_source_hash(self):
        self.assert_error(invalid(lambda m: m["sources"][0].pop("sha256")), "$.sources[0].sha256")

    def test_malformed_sha(self):
        self.assert_error(
            invalid(lambda m: m["outputs"][0].update(sha256="XYZ")),
            "$.outputs[0].sha256",
        )

    def test_completed_count_mismatch(self):
        self.assert_error(
            invalid(lambda m: m["provider"].update(completed_outputs=1)),
            "must equal len(outputs)",
        )

    def test_completed_cannot_exceed_requested(self):
        self.assert_error(
            invalid(lambda m: m["provider"].update(requested_outputs=1)),
            "cannot exceed requested_outputs",
        )

    def test_requested_over_adr_cap(self):
        self.assert_error(
            invalid(lambda m: m["provider"].update(requested_outputs=11, completed_outputs=2)),
            "ADR 0003",
        )

    def test_approval_without_matching_output_hash(self):
        self.assert_error(
            invalid(lambda m: m["approvals"][0].update(approved_sha256="d" * 64)),
            "does not match any output",
        )

    def test_approval_without_hash(self):
        self.assert_error(
            invalid(lambda m: m["approvals"][0].pop("approved_sha256")),
            "$.approvals[0].approved_sha256",
        )

    def test_render_may_not_claim_fidelity(self):
        self.assert_error(
            invalid(lambda m: m.update(fidelity={"outside_region_changed_pixels": 0})),
            "$.fidelity",
        )

    def test_assembly_may_not_carry_provider(self):
        manifest = copy.deepcopy(VALID_ASSEMBLY)
        manifest["provider"] = {"name": "openrouter"}
        self.assert_error(manifest, "$.provider")

    def test_contradictory_complete_status(self):
        self.assert_error(
            invalid(lambda m: (m.update(outputs=[]), m["provider"].update(completed_outputs=0))),
            "at least one output",
        )

    def test_credential_like_value_rejected(self):
        self.assert_error(
            invalid(lambda m: m["sources"][0].update(role="sk-or-abcdefghijklmnop")),
            "credential-like value",
        )

    def test_credential_like_key_rejected(self):
        self.assert_error(
            invalid(lambda m: m.setdefault("extensions", {}).update(api_key="redacted")),
            "credential-like key",
        )

    def test_absolute_path_rejected(self):
        self.assert_error(
            invalid(lambda m: m["outputs"][0].update(path="/home/user/private/image.png")),
            "absolute or escaping paths",
        )

    def test_undeclared_field_rejected(self):
        self.assert_error(invalid(lambda m: m.update(surprise=1)), "$.surprise")

    def test_unknown_version_rejected(self):
        self.assert_error(
            invalid(lambda m: m.update(manifest_version="run-manifest-v0")),
            "$.manifest_version",
        )

    def test_incomplete_run_may_have_zero_outputs(self):
        manifest = invalid(
            lambda m: (
                m.update(status="incomplete", outputs=[], approvals=[]),
                m["provider"].update(completed_outputs=0),
            )
        )
        self.assertEqual(validate_manifest(manifest), [])


if __name__ == "__main__":
    unittest.main()
