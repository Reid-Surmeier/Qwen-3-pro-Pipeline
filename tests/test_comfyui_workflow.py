import unittest

from qwen_ui_pipeline import (
    build_comfyui_api_workflow,
    build_comfyui_assembly_workflow,
    build_comfyui_mask_assembly_workflow,
    build_comfyui_mask_reference_workflow,
)


class ComfyUiWorkflowTests(unittest.TestCase):
    def test_builds_reference_edit_graph_with_save_node(self):
        brief = {"objective": "Replace the flower with a golf club."}

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
        self.assertEqual(workflow["4"]["inputs"]["images"], ["3", 0])

    def test_builds_opt_in_mask_owned_assembly_graph(self):
        workflow = build_comfyui_mask_assembly_workflow(
            reference_filename="reference.png",
            generated_filename="approved-donor.png",
            mask_filename="approved-mask.png",
            filename_prefix="issue-2/mask-assembly/v001",
            mask_threshold=0.6,
            cutline_width=3,
            contact_width=2,
        )

        self.assertEqual(workflow["1"]["class_type"], "LoadImage")
        self.assertEqual(workflow["2"]["inputs"]["image"], "approved-donor.png")
        self.assertEqual(workflow["3"]["inputs"]["image"], "approved-mask.png")
        self.assertEqual(workflow["4"]["class_type"], "ImageToMask")
        self.assertEqual(workflow["4"]["inputs"]["channel"], "red")
        self.assertEqual(workflow["5"]["class_type"], "StickerMaskBands")
        self.assertEqual(workflow["5"]["inputs"]["threshold"], 0.6)
        self.assertEqual(workflow["6"]["class_type"], "ImageCompositeMasked")
        self.assertEqual(workflow["6"]["inputs"]["mask"], ["5", 0])
        self.assertEqual(
            workflow["7"]["class_type"], "MaskedReferenceFidelityGate"
        )
        self.assertTrue(workflow["7"]["inputs"]["exact_outside_mask"])
        self.assertEqual(workflow["7"]["inputs"]["allowed_masks"], ["5", 3])
        self.assertEqual(workflow["8"]["class_type"], "ArtworkFidelityGate")
        self.assertEqual(workflow["8"]["inputs"]["min_silhouette_iou"], 0.0)
        self.assertEqual(
            workflow["8"]["inputs"]["max_centroid_drift_px"], 16384.0
        )
        self.assertEqual(workflow["8"]["inputs"]["max_scale_drift"], 1.0)
        self.assertEqual(workflow["9"]["inputs"]["images"], ["8", 0])

    def test_builds_mask_as_visual_reference_graph_without_replacing_qwen(self):
        brief = {
            "provider": "openrouter",
            "objective": "Preserve the sticker while cleaning its boundary.",
            "output": {"count": 2, "seed": 17},
        }

        workflow = build_comfyui_mask_reference_workflow(
            brief,
            reference_filename="reference.png",
            mask_guide_filename="mask-guide.png",
            filename_prefix="issue-2/mask-guide/v001",
        )

        self.assertEqual(workflow["1"]["class_type"], "LoadImage")
        self.assertEqual(workflow["2"]["class_type"], "LoadImage")
        self.assertEqual(workflow["3"]["class_type"], "BatchImagesNode")
        self.assertEqual(workflow["3"]["inputs"]["images.image0"], ["1", 0])
        self.assertEqual(workflow["3"]["inputs"]["images.image1"], ["2", 0])
        self.assertEqual(workflow["4"]["class_type"], "QwenImage3Render")
        self.assertEqual(workflow["4"]["inputs"]["reference_images"], ["3", 0])
        self.assertIn(
            '"provider": "openrouter"',
            workflow["4"]["inputs"]["edit_brief_json"],
        )
        self.assertEqual(workflow["5"]["inputs"]["images"], ["4", 0])
        self.assertEqual(workflow["6"]["class_type"], "SaveText")
        self.assertEqual(workflow["6"]["inputs"]["text"], ["4", 1])
        self.assertEqual(
            workflow["6"]["inputs"]["filename_prefix"],
            "issue-2/mask-guide/v001-metadata",
        )


if __name__ == "__main__":
    unittest.main()
