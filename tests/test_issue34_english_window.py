import unittest
from pathlib import Path

from qwen_ui_pipeline.prompt_manifest import compile_edit_brief
from scripts.build_issue34_english_window_evidence import (
    SOURCE_SHA256,
    SOURCE_SIZE,
    TARGET_SIZE,
    analyze_image,
    build_direct_baseline_workflow,
    build_english_edit_brief,
    build_node_assisted_workflow,
    compare_alpha_to_source,
)


class Issue34EnglishWindowTests(unittest.TestCase):
    def test_revised_brief_requires_translation_removal_and_uniform_reflow(self):
        brief = build_english_edit_brief()
        prompt = compile_edit_brief(brief).prompt

        self.assertEqual(SOURCE_SIZE, (1572, 718))
        self.assertEqual(TARGET_SIZE, (3144, 1436))
        self.assertEqual(
            SOURCE_SHA256,
            "7132ec99366fe2c33a1db5cadd92448257e35795764f4010b808e06723a40b16",
        )
        self.assertIn('title bar: "Options"', prompt)
        self.assertIn('bottom option: "Snap"', prompt)
        self.assertIn("Remove the complete Effect row", prompt)
        self.assertIn("even vertical spacing", prompt)
        self.assertEqual(brief["output"]["count"], 2)
        self.assertEqual(brief["provider"], "openrouter")
        self.assertEqual(brief["model"], "qwen/qwen-image-3-pro")

    def test_direct_baseline_has_no_visual_preprocessing_or_helper_nodes(self):
        workflow = build_direct_baseline_workflow(
            build_english_edit_brief(),
            reference_filename="issue-34-options-window-source.png",
        )

        self.assertEqual(
            [node["class_type"] for node in workflow.values()],
            ["LoadImage", "QwenImage3Render", "SaveImage", "SaveText"],
        )
        self.assertEqual(workflow["2"]["inputs"]["reference_images"], ["1", 0])
        self.assertNotIn("guide", workflow["2"]["inputs"])

    def test_node_assisted_arm_only_changes_size_and_exterior_alpha(self):
        workflow = build_node_assisted_workflow(
            candidate_filename="issue-34-english-raw-01.png",
            source_filename="issue-34-options-window-source.png",
            candidate_number=1,
        )

        self.assertEqual(workflow["2"]["class_type"], "ResizeImageMaskNode")
        self.assertEqual(workflow["2"]["inputs"]["resize_type.width"], 3144)
        self.assertEqual(workflow["2"]["inputs"]["resize_type.height"], 1436)
        self.assertEqual(workflow["4"]["inputs"]["input"], ["3", 1])
        self.assertEqual(workflow["4"]["inputs"]["scale_method"], "nearest-exact")
        self.assertEqual(workflow["5"]["class_type"], "JoinImageWithAlpha")
        self.assertEqual(workflow["5"]["inputs"]["image"], ["2", 0])
        self.assertEqual(workflow["5"]["inputs"]["alpha"], ["4", 0])
        self.assertNotIn(
            "ReferenceRegionComposite",
            [node["class_type"] for node in workflow.values()],
        )

    def test_live_node_outputs_have_exact_size_and_source_derived_alpha(self):
        root = Path("artifacts/issue-34/english-structural-edit-v002")
        source = Path(
            "artifacts/issue-34/alpha-window-2x/source/options-window-source.png"
        )

        for candidate_number in (1, 2):
            raw = analyze_image(root / f"raw/candidate-{candidate_number:02d}.png")
            assisted_path = (
                root / f"node-assisted/candidate-{candidate_number:02d}.png"
            )
            assisted = analyze_image(assisted_path)
            alpha = compare_alpha_to_source(source, assisted_path)

            self.assertEqual(raw["size"], [2048, 1024])
            self.assertEqual(raw["mode"], "RGB")
            self.assertEqual(assisted["size"], [3144, 1436])
            self.assertEqual(assisted["mode"], "RGBA")
            self.assertEqual(alpha["opaque_membership_errors"], 0)
            self.assertGreater(alpha["transparent_membership_errors"], 0)


if __name__ == "__main__":
    unittest.main()
