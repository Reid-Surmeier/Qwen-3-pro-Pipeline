import hashlib
import tempfile
import unittest
from pathlib import Path

from qwen_ui_pipeline import (
    WorkflowContractError,
    validate_assembly_gate,
    validate_workflow_contract,
    verify_approved_output_hash,
    verify_reference_hash,
)


def strict_brief() -> dict:
    return {
        "workflow_profile": "qwen-source-locked-single-decision-v1",
        "runtime": "comfyui",
        "provider": "alibaba",
        "model": "qwen/qwen-image-3-pro",
        "stage": {
            "id": "01-typography",
            "decision": "Replace only the title lettering.",
            "status": "planned",
        },
        "reference": {
            "path": "reference.png",
            "sha256": hashlib.sha256(b"source").hexdigest(),
        },
        "objective": "Replace only the title lettering.",
        "reference_role": "The source is immutable outside the approved title band.",
        "preservation_invariants": ["Keep every pixel outside the title band."],
        "canvas": ["Preserve the source geometry."],
        "regions": [
            {
                "name": "title band",
                "bounds": [10, 20, 300, 80],
                "change": "Replace only the title.",
                "preserve": ["surrounding label"],
            }
        ],
        "style": ["Derive lettering character from the source."],
        "negative_constraints": ["No global redraw."],
        "quality_checks": ["Outside-region pixels remain identical after assembly."],
        "output": {
            "resolution": "2K",
            "aspect_ratio": "source",
            "size": "1048*1501",
            "count": 4,
            "seed": 1786,
        },
    }


class WorkflowContractTests(unittest.TestCase):
    def test_accepts_complete_qwen_comfyui_contract(self):
        validate_workflow_contract(strict_brief())

    def test_rejects_openai_provider_before_generation(self):
        brief = strict_brief()
        brief["provider"] = "OpenAI built-in image_gen"

        with self.assertRaisesRegex(WorkflowContractError, "provider must be 'alibaba'"):
            validate_workflow_contract(brief)

    def test_rejects_more_than_one_visual_decision(self):
        brief = strict_brief()
        brief["regions"].append(
            {"name": "sculpture", "bounds": [20, 40, 80, 120], "change": "Restyle it."}
        )

        with self.assertRaisesRegex(WorkflowContractError, "exactly one visual decision"):
            validate_workflow_contract(brief)

    def test_rejects_single_output_or_missing_fixed_seed(self):
        brief = strict_brief()
        brief["output"] = {"resolution": "2K", "aspect_ratio": "source", "count": 1}

        with self.assertRaises(WorkflowContractError) as raised:
            validate_workflow_contract(brief)

        self.assertIn("output.count must be 4", str(raised.exception))
        self.assertIn("output.seed must be a fixed", str(raised.exception))

    def test_verifies_immutable_reference_hash(self):
        brief = strict_brief()
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "reference.png"
            reference.write_bytes(b"source")
            self.assertEqual(verify_reference_hash(brief, reference), brief["reference"]["sha256"])

            reference.write_bytes(b"changed")
            with self.assertRaisesRegex(WorkflowContractError, "SHA-256 mismatch"):
                verify_reference_hash(brief, reference)

    def test_blocks_assembly_until_approved_donor_is_frozen(self):
        brief = strict_brief()
        with self.assertRaisesRegex(WorkflowContractError, "stage.status='approved'"):
            validate_assembly_gate(brief)

        brief["stage"]["status"] = "approved"
        brief["stage"]["approved_output_sha256"] = hashlib.sha256(b"donor").hexdigest()
        validate_assembly_gate(brief)

        with tempfile.TemporaryDirectory() as directory:
            donor = Path(directory) / "donor.png"
            donor.write_bytes(b"donor")
            self.assertEqual(
                verify_approved_output_hash(brief, donor),
                brief["stage"]["approved_output_sha256"],
            )

            donor.write_bytes(b"wrong")
            with self.assertRaisesRegex(WorkflowContractError, "donor SHA-256 mismatch"):
                verify_approved_output_hash(brief, donor)


if __name__ == "__main__":
    unittest.main()
