import unittest

from qwen_ui_pipeline import (
    build_comfyui_api_workflow,
    build_comfyui_assembly_workflow,
    build_comfyui_component_assembly_workflow,
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

    def test_builds_source_locked_component_reflow_graph(self):
        workflow = build_comfyui_component_assembly_workflow(
            reference_filename="options-window-source.png",
            generated_filename="qwen-donor.png",
            layout={
                "donor_normalization": {
                    "width": 1572,
                    "height": 718,
                    "upscale_method": "nearest-exact",
                    "crop": "disabled",
                },
                "cleanplate": {
                    "source_region": [185, 235, 1245, 65],
                    "target_region": [185, 130, 1245, 350],
                },
                "components": [
                    {
                        "source_region": [185, 130, 1245, 115],
                        "target": [185, 130],
                    },
                    {
                        "source_region": [185, 355, 1245, 130],
                        "target": [185, 280],
                    },
                ],
                "final_edit_region": [160, 130, 1350, 350],
            },
            filename_prefix="issue-34/component-assembly",
            preserve_reference_alpha=True,
        )

        self.assertEqual(workflow["3"]["class_type"], "ImageScale")
        self.assertEqual(workflow["3"]["inputs"]["width"], 1572)
        self.assertEqual(workflow["4"]["class_type"], "ImageCropV2")
        self.assertEqual(
            workflow["4"]["inputs"]["crop_region"],
            {"x": 185, "y": 235, "width": 1245, "height": 65},
        )
        self.assertEqual(workflow["5"]["class_type"], "ImageScale")
        self.assertEqual(workflow["5"]["inputs"]["upscale_method"], "nearest-exact")
        self.assertEqual(workflow["6"]["class_type"], "ImageCompositeMasked")
        self.assertFalse(workflow["6"]["inputs"]["resize_source"])
        self.assertEqual(workflow["8"]["inputs"]["x"], 185)
        self.assertEqual(workflow["10"]["inputs"]["y"], 280)
        self.assertEqual(workflow["11"]["class_type"], "ReferenceRegionComposite")
        self.assertEqual(workflow["11"]["inputs"]["region"], "160,130,1350,350")
        self.assertEqual(workflow["11"]["inputs"]["reference_masks"], ["1", 1])
        self.assertEqual(workflow["12"]["inputs"]["images"], ["11", 0])

    def test_component_reflow_rejects_invalid_layout_coordinates(self):
        with self.assertRaisesRegex(ValueError, "cleanplate.source_region"):
            build_comfyui_component_assembly_workflow(
                reference_filename="reference.png",
                generated_filename="donor.png",
                layout={
                    "donor_normalization": {"width": 4, "height": 4},
                    "cleanplate": {
                        "source_region": [1, 2, 0, 4],
                        "target_region": [1, 2, 3, 4],
                    },
                    "components": [],
                    "final_edit_region": [1, 2, 3, 4],
                },
                filename_prefix="invalid",
            )

    def test_component_reflow_rejects_patches_outside_final_edit_region(self):
        layout = {
            "donor_normalization": {"width": 30, "height": 30},
            "cleanplate": {
                "source_region": [0, 0, 20, 20],
                "target_region": [10, 10, 20, 20],
            },
            "components": [
                {"source_region": [0, 0, 10, 10], "target": [25, 25]},
            ],
            "final_edit_region": [10, 10, 20, 20],
        }

        with self.assertRaisesRegex(ValueError, r"components\[0\] target extent"):
            build_comfyui_component_assembly_workflow(
                reference_filename="reference.png",
                generated_filename="donor.png",
                layout=layout,
                filename_prefix="invalid",
            )

    def test_component_reflow_rejects_cleanplate_outside_normalized_donor(self):
        with self.assertRaisesRegex(ValueError, "cleanplate.source_region must fit"):
            build_comfyui_component_assembly_workflow(
                reference_filename="reference.png",
                generated_filename="donor.png",
                layout={
                    "donor_normalization": {"width": 30, "height": 30},
                    "cleanplate": {
                        "source_region": [20, 20, 20, 20],
                        "target_region": [0, 0, 20, 20],
                    },
                    "components": [
                        {"source_region": [0, 0, 10, 10], "target": [0, 0]},
                    ],
                    "final_edit_region": [0, 0, 30, 30],
                },
                filename_prefix="invalid",
            )


if __name__ == "__main__":
    unittest.main()
