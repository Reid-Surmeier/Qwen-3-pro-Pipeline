import hashlib
import unittest

from qwen_ui_pipeline import build_comfyui_api_workflow, build_comfyui_assembly_workflow


def strict_brief(*, approved: bool = False) -> dict:
    stage = {
        "id": "01-object",
        "decision": "Replace only the selected flower.",
        "status": "approved" if approved else "planned",
    }
    if approved:
        stage["approved_output_sha256"] = hashlib.sha256(b"donor").hexdigest()
    return {
        "workflow_profile": "qwen-source-locked-single-decision-v1",
        "runtime": "comfyui",
        "provider": "alibaba",
        "model": "qwen/qwen-image-3-pro",
        "stage": stage,
        "reference": {
            "path": "plantstudio-main-window.gif",
            "sha256": hashlib.sha256(b"source").hexdigest(),
        },
        "objective": "Replace only the selected flower.",
        "reference_role": "The source is immutable outside the region.",
        "preservation_invariants": ["Keep all surrounding pixels."],
        "canvas": ["Preserve source geometry."],
        "regions": [
            {
                "name": "selected flower",
                "bounds": [182, 78, 37, 165],
                "change": "Replace it with one golf club.",
            }
        ],
        "style": ["Match the source raster style."],
        "negative_constraints": ["No global redraw."],
        "quality_checks": ["Outside-region pixels remain unchanged."],
        "output": {
            "resolution": "1K",
            "aspect_ratio": "source",
            "size": "948*806",
            "count": 4,
            "seed": 1786,
        },
    }


class ComfyUiWorkflowTests(unittest.TestCase):
    def test_builds_reference_edit_graph_with_save_node(self):
        brief = strict_brief()

        workflow = build_comfyui_api_workflow(
            brief,
            reference_filename="plantstudio-main-window.gif",
            filename_prefix="golf-ui/club-preview/v001",
        )

        self.assertEqual(workflow["1"]["class_type"], "LoadImage")
        self.assertEqual(workflow["2"]["class_type"], "QwenImage3Render")
        self.assertEqual(workflow["2"]["inputs"]["reference_images"], ["1", 0])
        self.assertEqual(workflow["3"]["inputs"]["images"], ["2", 0])
        self.assertEqual(
            workflow["3"]["inputs"]["filename_prefix"],
            "golf-ui/club-preview/v001",
        )

    def test_builds_deterministic_region_assembly_graph(self):
        workflow = build_comfyui_assembly_workflow(
            strict_brief(approved=True),
            reference_filename="plantstudio-main-window.gif",
            generated_filename="golf-club-v002-2.png",
            region="182,78,37,165",
            filename_prefix="golf-ui/club-assembly/v003",
        )

        self.assertEqual(workflow["1"]["class_type"], "LoadImage")
        self.assertEqual(workflow["2"]["class_type"], "LoadImage")
        self.assertEqual(workflow["3"]["class_type"], "ReferenceRegionComposite")
        self.assertEqual(workflow["3"]["inputs"]["reference_images"], ["1", 0])
        self.assertEqual(workflow["3"]["inputs"]["generated_images"], ["2", 0])
        self.assertEqual(workflow["3"]["inputs"]["region"], "182,78,37,165")
        self.assertIn(
            '"status": "approved"',
            workflow["3"]["inputs"]["approval_manifest_json"],
        )
        self.assertEqual(workflow["4"]["inputs"]["images"], ["3", 0])


if __name__ == "__main__":
    unittest.main()
