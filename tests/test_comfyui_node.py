import importlib.util
import unittest

from qwen_ui_pipeline.comfyui_node import QwenImage3Render, ReferenceRegionComposite


class QwenImage3RenderTests(unittest.TestCase):
    def test_node_accepts_an_edit_brief_but_never_an_api_key_widget(self):
        inputs = QwenImage3Render.INPUT_TYPES()
        exposed_names = set(inputs["required"]) | set(inputs["optional"])

        self.assertIn("edit_brief_json", exposed_names)
        self.assertIn("reference_images", exposed_names)
        self.assertNotIn("api_key", exposed_names)
        self.assertEqual(QwenImage3Render.CATEGORY, "Qwen UI Pipeline")

    def test_region_composite_exposes_only_images_and_explicit_coordinates(self):
        inputs = ReferenceRegionComposite.INPUT_TYPES()
        exposed_names = set(inputs["required"])

        self.assertEqual(
            exposed_names,
            {"reference_images", "generated_images", "region"},
        )
        self.assertEqual(set(inputs["optional"]), {"reference_masks"})
        self.assertEqual(ReferenceRegionComposite.RETURN_TYPES, ("IMAGE",))

    @unittest.skipUnless(importlib.util.find_spec("torch"), "torch is optional")
    def test_region_composite_can_round_trip_source_alpha(self):
        import torch

        reference = torch.tensor(
            [
                [
                    [[10 / 255, 20 / 255, 30 / 255], [0.2, 0.3, 0.4]],
                    [[0.5, 0.6, 0.7], [0.8, 0.9, 1.0]],
                ]
            ],
            dtype=torch.float32,
        )
        generated = torch.ones((1, 2, 2, 3), dtype=torch.float32)
        source_alpha = torch.tensor(
            [[[0 / 255, 64 / 255], [128 / 255, 255 / 255]]],
            dtype=torch.float32,
        )

        output = ReferenceRegionComposite().composite(
            reference,
            generated,
            "1,1,1,1",
            reference_masks=1.0 - source_alpha,
        )[0]

        saved_bytes = torch.floor(output * 255).to(torch.uint8)
        self.assertEqual(tuple(saved_bytes.shape), (1, 2, 2, 4))
        self.assertTrue(
            torch.equal(
                saved_bytes[0, ..., 3],
                (source_alpha[0] * 255).round().to(torch.uint8),
            )
        )
        self.assertEqual(saved_bytes[0, 0, 0].tolist(), [10, 20, 30, 0])
        self.assertEqual(saved_bytes[0, 1, 1].tolist(), [255, 255, 255, 255])


if __name__ == "__main__":
    unittest.main()
