import json
import unittest

from qwen_ui_pipeline.comfyui_node import QwenImage3Render, ReferenceRegionComposite
from qwen_ui_pipeline import WorkflowContractError


class QwenImage3RenderTests(unittest.TestCase):
    def test_node_accepts_an_edit_brief_but_never_an_api_key_widget(self):
        inputs = QwenImage3Render.INPUT_TYPES()
        exposed_names = set(inputs["required"]) | set(inputs["optional"])

        self.assertIn("edit_brief_json", exposed_names)
        self.assertIn("reference_images", exposed_names)
        self.assertNotIn("api_key", exposed_names)
        self.assertEqual(QwenImage3Render.CATEGORY, "Qwen UI Pipeline")

    def test_node_rejects_non_contract_provider_before_loading_credentials(self):
        with self.assertRaisesRegex(WorkflowContractError, "provider must be 'alibaba'"):
            QwenImage3Render().render(
                json.dumps({"provider": "OpenAI built-in image_gen"})
            )

    def test_region_composite_exposes_only_images_and_explicit_coordinates(self):
        inputs = ReferenceRegionComposite.INPUT_TYPES()
        exposed_names = set(inputs["required"])

        self.assertEqual(
            exposed_names,
            {
                "reference_images",
                "generated_images",
                "region",
                "approval_manifest_json",
            },
        )
        self.assertEqual(ReferenceRegionComposite.RETURN_TYPES, ("IMAGE",))


if __name__ == "__main__":
    unittest.main()
