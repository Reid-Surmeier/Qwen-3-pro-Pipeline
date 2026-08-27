import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from qwen_ui_pipeline.prompt_manifest import compile_edit_brief
from scripts.build_issue34_japanese_node_evidence import (
    ASSEMBLY_RECT,
    BASELINE_COMMIT,
    CANDIDATE_COMMIT,
    CONTEXT_RECT,
    DONOR_RECT,
    EDIT_RECT,
    SEED,
    SOURCE_SHA256,
    SOURCE_SIZE,
    build_baseline_assembly_workflow,
    build_direct_baseline_workflow,
    build_focused_crop_workflow,
    build_japanese_edit_brief,
    compare_declared_region,
    prepare_experiment,
)


class Issue34JapaneseNodeExperimentTests(unittest.TestCase):
    def test_brief_preserves_japanese_and_requests_one_structural_edit(self):
        brief = build_japanese_edit_brief()
        prompt = compile_edit_brief(brief).prompt

        self.assertEqual(SOURCE_SIZE, (1572, 718))
        self.assertEqual(
            BASELINE_COMMIT,
            "37c87b8a071c1ab8bd15f0d0c55dfd8a59b3de43",
        )
        self.assertEqual(
            CANDIDATE_COMMIT,
            "d25cf4f27e81ab8b8a61d4869a07da3683cc3ff1",
        )
        self.assertEqual(
            SOURCE_SHA256,
            "7132ec99366fe2c33a1db5cadd92448257e35795764f4010b808e06723a40b16",
        )
        self.assertEqual(SEED, 2026082603)
        self.assertEqual(brief["provider"], "openrouter")
        self.assertEqual(brief["model"], "qwen/qwen-image-3-pro")
        self.assertEqual(brief["output"]["count"], 2)
        self.assertIn('title bar: "オプション"', prompt)
        self.assertIn('bottom option: "スナップ"', prompt)
        self.assertIn("Remove the complete Effect row", prompt)
        self.assertNotIn("translate", prompt.lower())
        self.assertNotIn("English", prompt)

    def test_direct_baseline_uses_only_the_immutable_full_source(self):
        workflow = build_direct_baseline_workflow(
            build_japanese_edit_brief(),
            reference_filename="issue-34-options-window-source.png",
        )

        self.assertEqual(
            [node["class_type"] for node in workflow.values()],
            ["LoadImage", "QwenImage3Render", "SaveImage", "SaveText"],
        )
        self.assertEqual(workflow["2"]["inputs"]["reference_images"], ["1", 0])
        brief = json.loads(workflow["2"]["inputs"]["edit_brief_json"])
        self.assertEqual(brief["output"]["seed"], SEED)

    def test_focused_graph_crops_before_qwen_and_reuses_the_same_donors(self):
        workflow = build_focused_crop_workflow(
            build_japanese_edit_brief(),
            reference_filename="issue-34-options-window-source.png",
        )

        self.assertEqual(CONTEXT_RECT, (160, 64, 1250, 625))
        self.assertEqual(EDIT_RECT, (160, 130, 1250, 395))
        self.assertEqual(DONOR_RECT, (0, 66, 1250, 395))
        self.assertEqual(workflow["2"]["class_type"], "ImageCropV2")
        self.assertEqual(
            workflow["2"]["inputs"]["crop_region"],
            {"x": 160, "y": 64, "width": 1250, "height": 625},
        )
        self.assertEqual(workflow["3"]["class_type"], "QwenImage3Render")
        self.assertEqual(workflow["3"]["inputs"]["reference_images"], ["2", 0])
        self.assertEqual(workflow["5"]["class_type"], "ResizeImageMaskNode")
        self.assertEqual(workflow["6"]["class_type"], "ImageCropV2")
        self.assertEqual(workflow["8"]["class_type"], "FeatherMask")
        self.assertEqual(workflow["9"]["class_type"], "ImageCompositeMasked")
        self.assertEqual(workflow["10"]["class_type"], "ImageCompositeMasked")
        self.assertEqual(workflow["9"]["inputs"]["source"], ["6", 0])
        self.assertEqual(workflow["10"]["inputs"]["source"], ["6", 0])
        self.assertEqual(workflow["9"]["inputs"]["mask"], ["7", 0])
        self.assertEqual(workflow["10"]["inputs"]["mask"], ["8", 0])
        self.assertEqual(workflow["9"]["inputs"]["x"], EDIT_RECT[0])
        self.assertEqual(workflow["9"]["inputs"]["y"], EDIT_RECT[1])
        self.assertEqual(workflow["10"]["inputs"]["x"], EDIT_RECT[0])
        self.assertEqual(workflow["10"]["inputs"]["y"], EDIT_RECT[1])
        self.assertEqual(workflow["11"]["class_type"], "MaskToImage")

    def test_baseline_assembly_reuses_one_raw_donor_and_source_owned_exterior(self):
        workflow = build_baseline_assembly_workflow(
            candidate_filename="issue-34-japanese-v003-baseline-01.png",
            reference_filename="issue-34-options-window-source.png",
            candidate_number=1,
        )

        self.assertEqual(workflow["1"]["class_type"], "LoadImage")
        self.assertEqual(workflow["2"]["class_type"], "LoadImage")
        self.assertEqual(workflow["3"]["class_type"], "ResizeImageMaskNode")
        self.assertEqual(workflow["3"]["inputs"]["resize_type.width"], 1572)
        self.assertEqual(workflow["3"]["inputs"]["resize_type.height"], 718)
        self.assertEqual(workflow["4"]["class_type"], "ImageCropV2")
        self.assertEqual(ASSEMBLY_RECT, (160, 130, 1350, 350))
        self.assertEqual(
            workflow["4"]["inputs"]["crop_region"],
            {"x": 160, "y": 130, "width": 1350, "height": 350},
        )
        self.assertEqual(workflow["7"]["class_type"], "ImageCompositeMasked")
        self.assertEqual(workflow["8"]["class_type"], "ImageCompositeMasked")
        self.assertEqual(workflow["7"]["inputs"]["destination"], ["1", 0])
        self.assertEqual(workflow["7"]["inputs"]["source"], ["4", 0])
        self.assertEqual(workflow["7"]["inputs"]["mask"], ["5", 0])
        self.assertEqual(workflow["8"]["inputs"]["mask"], ["6", 0])
        self.assertEqual(workflow["9"]["class_type"], "JoinImageWithAlpha")
        self.assertEqual(workflow["9"]["inputs"]["image"], ["7", 0])
        self.assertEqual(workflow["9"]["inputs"]["alpha"], ["1", 1])
        self.assertEqual(workflow["10"]["class_type"], "JoinImageWithAlpha")
        self.assertEqual(workflow["10"]["inputs"]["image"], ["8", 0])
        self.assertEqual(workflow["10"]["inputs"]["alpha"], ["1", 1])

    def test_rejected_pre_alpha_graph_is_retained_with_its_exact_geometry(self):
        workflow = build_baseline_assembly_workflow(
            candidate_filename="issue-34-japanese-v003-baseline-01.png",
            reference_filename="issue-34-options-window-source.png",
            candidate_number=1,
            rectangle=(160, 130, 1250, 395),
            output_version="assembly",
            rejoin_reference_alpha=False,
        )

        self.assertEqual(
            workflow["4"]["inputs"]["crop_region"],
            {"x": 160, "y": 130, "width": 1250, "height": 395},
        )
        self.assertNotIn("9", workflow)
        self.assertNotIn("10", workflow)
        self.assertEqual(workflow["13"]["inputs"]["images"], ["7", 0])
        self.assertEqual(workflow["14"]["inputs"]["images"], ["8", 0])

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is optional")
    def test_region_comparison_proves_rgba_exterior_is_unchanged(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = Image.new("RGBA", (4, 4), (10, 20, 30, 40))
            candidate = source.copy()
            candidate.putpixel((1, 1), (200, 201, 202, 203))
            source_path = root / "source.png"
            candidate_path = root / "candidate.png"
            source.save(source_path)
            candidate.save(candidate_path)

            comparison = compare_declared_region(
                source_path,
                candidate_path,
                (1, 1, 2, 2),
            )

        self.assertEqual(comparison["outside_rgba_changed_pixels"], 0)
        self.assertEqual(comparison["outside_rgb_changed_pixels"], 0)
        self.assertEqual(comparison["outside_alpha_changed_pixels"], 0)
        self.assertEqual(comparison["inside_rgba_changed_pixels"], 1)
        self.assertEqual(comparison["max_outside_channel_delta"], 0)

    def test_preparation_retains_a_full_canvas_matched_donor_control(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            prepare_experiment(root)
            workflow = json.loads(
                (root / "matched-donor-candidate-01.api.json").read_text()
            )

        self.assertEqual(workflow["3"]["inputs"]["region"], "0,0,1572,718")
        self.assertNotIn("reference_masks", workflow["3"]["inputs"])


if __name__ == "__main__":
    unittest.main()
