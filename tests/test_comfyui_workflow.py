import unittest

from qwen_ui_pipeline import build_comfyui_api_workflow, build_comfyui_assembly_workflow


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


if __name__ == "__main__":
    unittest.main()
