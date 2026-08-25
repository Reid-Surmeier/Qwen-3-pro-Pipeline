import unittest

from qwen_ui_pipeline import (
    build_comfyui_api_workflow,
    build_comfyui_assembly_workflow,
    build_sticker_mask_assembly_workflow,
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

    def test_builds_mask_owned_sticker_assembly_without_changing_region_flow(self):
        workflow = build_sticker_mask_assembly_workflow(
            reference_filename="device.png",
            artwork_filename="approved-sticker.png",
            mask_filename="approved-sticker-mask.png",
            integration_filename="qwen-contact-donor.png",
            canvas_width=1024,
            canvas_height=768,
            target_quad="120,90,430,72,448,350,105,366",
            cutline_width=3,
            contact_width=2,
            filename_prefix="stickers/mask-owned/v001",
        )

        self.assertEqual(workflow["4"]["class_type"], "StickerPerspectiveWarp")
        self.assertEqual(workflow["5"]["class_type"], "StickerMaskBands")
        self.assertEqual(workflow["7"]["class_type"], "ImageCompositeMasked")
        self.assertEqual(workflow["8"]["class_type"], "ImageCompositeMasked")
        self.assertEqual(workflow["9"]["class_type"], "ColorTransfer")
        self.assertEqual(workflow["10"]["class_type"], "ImageCompositeMasked")
        self.assertEqual(workflow["11"]["class_type"], "MaskedReferenceFidelityGate")
        self.assertEqual(workflow["12"]["class_type"], "ArtworkFidelityGate")
        self.assertEqual(workflow["13"]["class_type"], "SaveImage")
        self.assertEqual(workflow["7"]["inputs"]["mask"], ["5", 1])
        self.assertEqual(workflow["8"]["inputs"]["mask"], ["5", 0])
        self.assertEqual(workflow["10"]["inputs"]["mask"], ["5", 2])
        self.assertEqual(workflow["11"]["inputs"]["allowed_masks"], ["5", 3])
        self.assertEqual(workflow["12"]["inputs"]["candidate_images"], ["11", 0])
        self.assertEqual(workflow["13"]["inputs"]["images"], ["12", 0])


if __name__ == "__main__":
    unittest.main()
