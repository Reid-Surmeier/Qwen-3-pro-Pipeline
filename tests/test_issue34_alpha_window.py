import unittest
from pathlib import Path

from scripts.build_issue34_alpha_window_evidence import (
    SOURCE_SHA256,
    SOURCE_SIZE,
    TARGET_SIZE,
    analyze_rgba,
    build_alpha_resize_workflow,
    build_failed_split_after_load_workflow,
    build_qwen_brief,
    build_qwen_exact_alpha_workflow,
    build_qwen_workflow,
    compare_to_authoritative_2x,
)


SOURCE = Path(
    "artifacts/issue-34/alpha-window-2x/source/options-window-source.png"
)


class Issue34AlphaWindowTests(unittest.TestCase):
    def test_native_workflow_resizes_image_and_alpha_together(self):
        workflow = build_alpha_resize_workflow(
            reference_filename="issue-34/options-window-source.png",
            filename_prefix="issue-34/nearest-exact-2x",
            image_method="nearest-exact",
        )

        self.assertEqual(workflow["2"]["class_type"], "ResizeImageMaskNode")
        self.assertEqual(workflow["2"]["inputs"]["input"], ["1", 0])
        self.assertEqual(workflow["2"]["inputs"]["resize_type.multiplier"], 2.0)
        self.assertEqual(workflow["2"]["inputs"]["scale_method"], "nearest-exact")
        self.assertEqual(workflow["3"]["class_type"], "ResizeImageMaskNode")
        self.assertEqual(workflow["3"]["inputs"]["input"], ["1", 1])
        self.assertEqual(workflow["3"]["inputs"]["resize_type.multiplier"], 2.0)
        self.assertEqual(workflow["3"]["inputs"]["scale_method"], "nearest-exact")
        self.assertEqual(workflow["4"]["class_type"], "JoinImageWithAlpha")
        self.assertEqual(workflow["4"]["inputs"]["image"], ["2", 0])
        self.assertEqual(workflow["4"]["inputs"]["alpha"], ["3", 0])

    def test_source_identity_and_alpha_are_measured(self):
        analysis = analyze_rgba(SOURCE)

        self.assertEqual(SOURCE_SIZE, (1572, 718))
        self.assertEqual(TARGET_SIZE, (3144, 1436))
        self.assertEqual(analysis["sha256"], SOURCE_SHA256)
        self.assertEqual(analysis["size"], [1572, 718])
        self.assertEqual(analysis["mode"], "RGBA")
        self.assertEqual(analysis["alpha"]["min"], 0)
        self.assertEqual(analysis["alpha"]["max"], 255)
        self.assertGreater(analysis["alpha"]["transparent_pixels"], 0)
        self.assertGreater(analysis["alpha"]["opaque_pixels"], 0)

    def test_qwen_plan_is_source_only_openrouter_and_two_outputs(self):
        brief = build_qwen_brief()
        workflow = build_qwen_workflow(
            brief,
            reference_filename="issue-34-options-window-source.png",
        )

        self.assertEqual(brief["provider"], "openrouter")
        self.assertEqual(brief["model"], "qwen/qwen-image-3-pro")
        self.assertEqual(brief["output"]["count"], 2)
        self.assertEqual(workflow["1"]["class_type"], "LoadImage")
        self.assertEqual(workflow["2"]["class_type"], "QwenImage3Render")
        self.assertEqual(workflow["2"]["inputs"]["reference_images"], ["1", 0])
        self.assertNotIn("guide", workflow["2"]["inputs"])
        self.assertEqual(workflow["3"]["class_type"], "SaveImage")

    def test_live_native_mask_result_preserves_opaque_membership(self):
        comparison = compare_to_authoritative_2x(
            SOURCE,
            Path(
                "artifacts/issue-34/alpha-window-2x/deterministic/"
                "nearest-exact-alpha-2x_00001_.png"
            ),
        )

        self.assertEqual(comparison["opaque_membership_errors"], 0)
        self.assertGreater(comparison["transparent_membership_errors"], 0)

    def test_qwen_postprocess_fits_target_and_reuses_source_mask(self):
        workflow = build_qwen_exact_alpha_workflow(
            candidate_filename="issue-34-qwen-raw-01.png",
            reference_filename="issue-34-options-window-source.png",
            candidate_number=1,
        )

        self.assertEqual(workflow["2"]["inputs"]["resize_type.width"], 3144)
        self.assertEqual(workflow["2"]["inputs"]["resize_type.height"], 1436)
        self.assertEqual(workflow["2"]["inputs"]["scale_method"], "lanczos")
        self.assertEqual(workflow["4"]["inputs"]["input"], ["3", 1])
        self.assertEqual(workflow["4"]["inputs"]["scale_method"], "nearest-exact")
        self.assertEqual(workflow["5"]["inputs"]["alpha"], ["4", 0])

    def test_rejected_split_workflow_is_reproducible(self):
        workflow = build_failed_split_after_load_workflow(
            reference_filename="issue-34-options-window-source.png",
            filename_prefix="issue-34/nearest-exact-2x",
            image_method="nearest-exact",
        )

        self.assertEqual(workflow["2"]["class_type"], "SplitImageWithAlpha")
        self.assertEqual(workflow["2"]["inputs"]["image"], ["1", 0])
        self.assertEqual(workflow["4"]["inputs"]["input"], ["2", 1])


if __name__ == "__main__":
    unittest.main()
