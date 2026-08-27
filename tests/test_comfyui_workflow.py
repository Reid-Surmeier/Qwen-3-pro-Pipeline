import unittest

from qwen_ui_pipeline import (
    build_comfyui_api_workflow,
    build_comfyui_assembly_workflow,
    build_comfyui_component_extraction_workflow,
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

    def test_extracts_reference_components_without_regenerating_their_pixels(self):
        workflow = build_comfyui_component_extraction_workflow(
            reference_filename="golfstudio-approved-baseline.png",
            components={
                "toolbar": (10, 44, 101, 25),
                "animate": (393, 350, 77, 26),
            },
            filename_prefix="golf-ui/reference-components/v001",
        )

        self.assertEqual(workflow["1"]["class_type"], "LoadImage")
        crop_nodes = [node for node in workflow.values() if node["class_type"] == "ImageCrop"]
        self.assertEqual(len(crop_nodes), 2)
        self.assertEqual(
            crop_nodes[0]["inputs"],
            {"image": ["1", 0], "x": 10, "y": 44, "width": 101, "height": 25},
        )
        save_nodes = [node for node in workflow.values() if node["class_type"] == "SaveImage"]
        self.assertEqual(
            save_nodes[0]["inputs"]["filename_prefix"],
            "golf-ui/reference-components/v001/toolbar",
        )

    def test_rejects_invalid_component_rectangles(self):
        for bad in ({"toolbar": (-1, 0, 10, 10)}, {"toolbar": (0, 0, 0, 10)}):
            with self.assertRaises(ValueError):
                build_comfyui_component_extraction_workflow(
                    reference_filename="golfstudio-approved-baseline.png",
                    components=bad,
                    filename_prefix="golf-ui/reference-components/v001",
                )


if __name__ == "__main__":
    unittest.main()
